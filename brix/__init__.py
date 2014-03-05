#
# Author:: Noah Kantrowitz <noah@coderanger.net>
#
# Copyright 2014, Balanced, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Usage:
  brix [options] validate [--full] [<template>...]
  brix [options] show <name>
  brix [options] sync [<template>...]
  brix [options] update [--no-sync --param=KEY:VALUE...] <stack> [<template>]
  brix [options] diff <stack> [<template>]
  brix [options] stacks
  brix [options] events [--no-recurse] <stack>

-h --help                    show this help message and exit
--version                    show program's version number and exit
-q, --quiet                  minimal output
-r, --region=REGION          AWS region [default: us-west-1]
-f, --full                   run slower validations
--no-sync                    do not auto-sync before update
--param=KEY:VALUE            parameters to pass to the stack
--no-recurse                 do not process sub-stacks

Example:
brix sync

"""

from __future__ import print_function

import collections
import difflib
import hashlib
import importlib
import json
import os
import sys
import traceback

import boto
import boto.cloudformation
import boto.exception
import docopt
import troposphere

from templates import TemplateLibrary


class Brix(object):
    TEMPLATES = [
        'balanced_region',
        'legacy_region',
        'balanced_az',
        'balanced_gateway',
        'balanced_docs',
        'balanced_api',
    ]

    REGIONS = [
        'us-east-1',
        'us-west-1',
        'us-west-2',
    ]

    def __init__(self, region):
        self.region = region
        # TODO: Allow configuring these on the command line
        self.access_key_id = os.environ.get('BALANCED_AWS_ACCESS_KEY_ID', os.environ.get('AWS_ACCESS_KEY_ID'))
        self.secret_access_key = os.environ.get('BALANCED_AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY'))
        # Connect to the right CloudFormation region
        for r in boto.cloudformation.regions():
            if r.name == self.region:
                break
        else:
            raise ValueError('Unknown region {0}'.format(region))
        self.cfn = boto.connect_cloudformation(self.access_key_id, self.secret_access_key, region=r)
        self.s3 = boto.connect_s3(self.access_key_id, self.secret_access_key)
        # Load and render all templates
        self.templates = TemplateLibrary(os.path.abspath(os.path.join(__file__, '..', '..', 'templates')))

    def validate(self, names=None, quiet=False, full=False):
        error = False
        for tpl in self._get_templates(names):
            if tpl.error:
                print("{} error: {}".format(tpl.name, tpl.error[1]))
                error = True
                continue
            if full:
                # Run server-based validation
                # Trying to use template_body fails randomly, probably due to
                # length limits.
                bucket = self.s3.get_bucket('balanced-cfn-us-east-1')
                key = bucket.get_key('validation_tmp', validate=False)
                key.set_contents_from_string(tpl.json)
                try:
                    self.cfn.validate_template(template_url='https://balanced-cfn-us-east-1.s3.amazonaws.com/validation_tmp')
                except boto.exception.BotoServerError, e:
                    if e.status != 400:
                        raise
                    print("{} error: {}".format(tpl.name, e.message))
                    error = True
                    continue
                finally:
                    key.delete()
            if not quiet:
                print("{0} ok".format(tpl.name))
        if error:
            raise ValueError('Errors detected')

    def show(self, name):
        tpl = self._get_template(name)
        if tpl.error:
            print(''.join(traceback.format_exception(*tpl.error)), file=sys.stderr)
        else:
            print(tpl.json)

    def sync(self, names=None):
        self.validate(names, quiet=True) # Make sure the template(s) are good
        for tpl in self._get_templates(names):
            print('Uploading {}'.format(tpl.name), end='')
            for region in self.REGIONS:
                print(' {}'.format(region), end='')
                bucket = self.s3.get_bucket('balanced-cfn-{0}'.format(region))
                key = bucket.get_key(tpl.s3_key, validate=False)
                key.set_contents_from_string(tpl.json)
            print()

    def update(self, stack_name, template_name=None, params={}):
        try:
            stack = self.cfn.describe_stacks(stack_name)[0]
            operation = 'update_stack'
            kwargs = {}
            if stack.parameters:
                existing_params = {p.key: p.value for p in stack.parameters}
                existing_params.update(params)
                params = existing_params
            # if not template_name:
            #     template_name = stack.tags.get('TemplateName')
            print('Updating stack {} in {}'.format(stack_name, self.region))
        except boto.exception.BotoServerError:
            operation = 'create_stack'
            kwargs = {'disable_rollback': True}#, 'tags': {'TemplateName': template_name}}
            print('Creating stack {} in {}'.format(stack_name, self.region))
        if not template_name:
            raise ValueError('Template name for stack {} is required'.format(stack_name))
        print()
        tpl = self._get_template(template_name)
        getattr(self.cfn, operation)(
            stack_name=stack_name,
            template_url='https://balanced-cfn-{}.s3.amazonaws.com/{}'.format(self.region, tpl.s3_key),
            capabilities=['CAPABILITY_IAM'],
            parameters=params.items(),
            **kwargs)

    def stacks(self):
        """List all stacks in the region."""
        for stack in self._cfn_iterate(lambda t: self.cfn.list_stacks(next_token=t)):
            if stack.stack_status == 'DELETE_COMPLETE':
                continue
            print('{0.stack_name}: {0.template_description}'.format(stack))

    def events(self, stack, recurse=True):
        stacks = []
        if recurse:
            # Find all sub-stacks
            pending = [stack]
            while pending:
                s = pending.pop()
                stacks.append(s)
                for res in self.cfn.describe_stack_resources(s):
                    if res.resource_type == 'AWS::CloudFormation::Stack':
                        pending.append(res.stack_name)

        else:
            stacks.append(stack)
        events = []
        for stack in stacks:
            for event in self._cfn_iterate(lambda t: self.cfn.describe_stack_events(stack, next_token=t)):
                events.append(event)
        for event in sorted(events, key=lambda event: event.timestamp):
            fmt = '{2} '
            if len(stacks) > 1:
                fmt += '[{0.stack_name}]\t'
            fmt += '{0.logical_resource_id}: {0.resource_status} {1}'
            print(fmt.format(event, event.resource_status_reason or '', event.timestamp.replace(microsecond=0)))

    def diff(self, stack_name, template_name):
        if not template_name:
            stack = self.cfn.describe_stacks(stack_name)[0]
            template_name = stack.tags.get('TemplateName')
        if not template_name:
            raise ValueError('Template name for stack {} is required'.format(stack_name))
        # Who wants to bet this long string of __getitem__'s will break eventually?
        stack_template = self.cfn.get_template(stack_name)['GetTemplateResponse']['GetTemplateResult']['TemplateBody']
        # Reparse to normalize spacing
        stack_template = json.dumps(json.loads(stack_template, object_pairs_hook=collections.OrderedDict), indent=4)
        template = self._get_template(template_name)['json']
        for line in difflib.unified_diff(stack_template.splitlines(), template.splitlines(), fromfile=stack_name, tofile=template_name, lineterm=''):
            print(line)

    def _get_templates(self, names):
        if names:
            return [self._get_template(name) for name in names]
        else:
            return self.templates.itervalues()

    def _get_template(self, name):
        try:
            return self.templates[name]
        except KeyError:
            ValueError('Unknown template {}'.format(name))

    def _cfn_iterate(self, fn):
        first = True
        next_token = None
        while next_token or first:
            objs = fn(next_token)
            for obj in objs:
                yield obj # My kingdom for a yield from
            first = False
            next_token = objs.next_token


def main():
    args = docopt.docopt(__doc__, version='brix 1.0-dev')
    app = Brix(args['--region'])
    try:
        if args['validate']:
            app.validate(args['<template>'], quiet=args['--quiet'], full=args['--full'])
        elif args['show']:
            app.show(args['<name>'])
        elif args['sync']:
            app.sync(args['<template>'])
        elif args['stacks']:
            app.stacks()
        elif args['update']:
            if not args['--no-sync']:
                app.sync()
            def parse_param(s):
                if ':' in s:
                    return s.split(':', 1)
                else:
                    return (s, '1')
            params = dict(parse_param(s) for s in args['--param'])
            template = args['<template>'][0] if args['<template>'] else None
            app.update(args['<stack>'], template, params)
        elif args['events']:
            app.events(args['<stack>'], not args['--no-recurse'])
        elif args['diff']:
            template = args['<template>'][0] if args['<template>'] else None
            app.diff(args['<stack>'], template)
    except ValueError, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)



if __name__ == '__main__':
    main()
