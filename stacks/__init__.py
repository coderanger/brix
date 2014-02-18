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
  balanced-stacks [options] validate
  balanced-stacks [options] list
  balanced-stacks [options] show <name>
  balanced-stacks [options] sync
  balanced-stacks [options] update [--no-sync] [--ip=NUMBER] [--key=KEY]
  balanced-stacks [options] events [--no-recurse] <stack>

-h --help                    show this help message and exit
--version                    show program's version number and exit
-q, --quiet                  minimal output
--region=REGION              AWS region [default: us-west-1]
--no-sync                    do not auto-sync before update
--ip=NUMBER                  second octet to use for the VPC [default: 5]
--key=KEY                    EC2 SSH key name [default: cloudformation]
--no-recurse                 do not process sub-stacks

Example:
balanced-stacks sync

"""

from __future__ import print_function

import importlib
import os
import sys

import boto
import boto.cloudformation
import docopt
import troposphere


class BalancedStacks(object):
    TEMPLATES = [
        'balanced_region',
        'balanced_az',
        'balanced_gateway',
        'balanced_docs',
    ]

    REGIONS = [
        'us-east-1',
        'us-west-1',
        'us-west-2',
    ]

    def __init__(self):
        self.access_key_id = os.environ.get('BALANCED_AWS_ACCESS_KEY_ID', os.environ.get('AWS_ACCESS_KEY_ID'))
        self.secret_access_key = os.environ.get('BALANCED_AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY'))
        self.cfn = boto.connect_cloudformation(self.access_key_id, self.secret_access_key)

    def validate(self, quiet=False):
        error = False
        for name in self.TEMPLATES:
            try:
                self._load_template(name)().to_json()
                if not quiet:
                    print("{0} ok".format(name))
            except Exception, e:
                error = True
                print("{0} error: {1}".format(name, e))
        if error:
            raise ValueError('Errors detected')

    def show(self, name):
        if name in self.TEMPLATES:
            cls = self._load_template(name)
        elif 'balanced_{0}'.format(name) in self.TEMPLATES:
            cls = self._load_template('balanced_{0}'.format(name))
        else:
            raise ValueError('Unknown template {0}'.format(name))
        print(cls().to_json())

    def sync(self):
        self.validate(quiet=True)
        s3 = boto.connect_s3(self.access_key_id, self.secret_access_key)
        for name, cls in self.templates.iteritems():
            print('Uploading {0}'.format(name))
            self._upload_template(s3, name, self._load_template(name))

    def list(self, region):
        cfn = self._cfn(region)
        for stack in self._cfn_iterate(lambda t: cfn.list_stacks(next_token=t)):
            if stack.stack_status == 'DELETE_COMPLETE':
                continue
            print('{0.stack_name}: {0.template_description}'.format(stack))

    def update(self, region):
        cfn = self._cfn(region)
        try:
            cfn.describe_stacks('BalancedRegion')
            operation = 'update_stack'
            kwargs = {}
            print('Updating stack in {0}'.format(region))
        except boto.exception.BotoServerError:
            operation = 'create_stack'
            kwargs = {'disable_rollback': True}
            print('Creating stack in {0}'.format(region))
        getattr(cfn, operation)(
            stack_name='BalancedRegion',
            template_url='https://balanced-cfn-{0}.s3.amazonaws.com/templates/balanced_region.json'.format(region),
            capabilities=['CAPABILITY_IAM'],
            **kwargs)

    def events(self, region, stack, recurse=True):
        cfn = self._cfn(region)
        stacks = []
        if recurse:
            # Find all sub-stacks
            pending = [stack]
            while pending:
                s = pending.pop()
                stacks.append(s)
                for res in cfn.describe_stack_resources(s):
                    if res.resource_type == 'AWS::CloudFormation::Stack':
                        pending.append(res.stack_name)

        else:
            stacks.append(stack)
        events = []
        for stack in stacks:
            for event in self._cfn_iterate(lambda t: cfn.describe_stack_events(stack, next_token=t)):
                events.append(event)
        for event in sorted(events, key=lambda event: event.timestamp):
            fmt = '{2} '
            if len(stacks) > 1:
                fmt += '[{0.stack_name}]\t'
            fmt += '{0.logical_resource_id}: {0.resource_status} {1}'
            print(fmt.format(event, event.resource_status_reason or '', event.timestamp.replace(microsecond=0)))


    def _load_template(self, name):
        """Given a module name, return the template class."""
        # Mahmoud, be mad ;-)
        mod = importlib.import_module('.{0}'.format(name), __package__)
        for key, value in mod.__dict__.iteritems():
            if isinstance(value, type) and issubclass(value, troposphere.Template) and not key[0] == '_' and key != 'Template':
                return value

    def _upload_template(self, conn, name, cls):
        """Upload a template for all regions."""
        json = cls().to_json()
        for region in self.REGIONS:
            bucket = conn.get_bucket('balanced-cfn-{0}'.format(region))
            key = bucket.get_key('templates/{0}.json'.format(name), validate=False)
            key.set_contents_from_string(json)

    def _cfn(self, region):
        for r in boto.cloudformation.regions():
            if r.name == region:
                break
        else:
            raise ValueError('Unknown region {0}'.format(region))
        return boto.connect_cloudformation(self.access_key_id, self.secret_access_key, region=r)

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
    args = docopt.docopt(__doc__, version='balanced-stacks')
    app = BalancedStacks()
    try:
        if args['validate']:
            app.validate(quiet=args['--quiet'])
        elif args['show']:
            app.show(args['<name>'])
        elif args['sync']:
            app.sync()
        elif args['list']:
            app.list(args['--region'])
        elif args['update']:
            if not args['--no-sync']:
                app.sync()
            app.update(args['--region'])
        elif args['events']:
            app.events(args['--region'], args['<stack>'] or 'BalancedRegion', not args['--no-recurse'])
    except ValueError, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)



if __name__ == '__main__':
    main()
