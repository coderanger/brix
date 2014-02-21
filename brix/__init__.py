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

from __future__ import print_function

import collections
import importlib
import json
import os
import sys

import argparse
import boto
import boto.cloudformation
import pkg_resources
import troposphere

class BrixCommand(object):
    help = None
    arguments = []

    def __init__(self, app, parser):
        self.app = app
        self.parser = parser
        for argument in self.arguments:
            kwargs = {}
            if argument and isinstance(argument[-1], dict):
                kwargs = argument[-1]
                argument = argument[:-1]
            self.parser.add_argument(*argument, **kwargs)

    def __call__(self, args):
        raise NotImplementedError


class BrixList(BrixCommand):
    help = 'List all stacks.'

    def __call__(self, args):
        for stack in self.app._cfn_iterate(lambda t: self.app.cfn.list_stacks(next_token=t)):
            if stack.stack_status == 'DELETE_COMPLETE':
                continue
            print('{0.stack_name}: {0.template_description}'.format(stack))


class BrixRender(BrixCommand):
    help = 'Display the JSON for a template'
    arguments = [
        ('name', {'help': 'Template name'}),
    ]

    def __call__(self, args):
        print(self.app.load_template(args.name)().to_json())


class BrixApplication(object):
    def commands(self):
        cmds = collections.OrderedDict()
        cmds['list'] = BrixList
        cmds['render'] = BrixRender
        return cmds

    def parser(self):
        parser = argparse.ArgumentParser(description='CloudFormation management and workflow helpers.')
        parser.add_argument('-q', '--quiet', action='store_true', help='minimal output')
        parser.add_argument('--aws-access-key-id', metavar='KEY', help='AWS access key ID',
            default=(os.environ['BALANCED_AWS_ACCESS_KEY_ID'] or os.environ['AWS_ACCESS_KEY_ID']))
        parser.add_argument('--aws-secret-access-key', metavar='SECRET', help='AWS secret access key',
            default=(os.environ['BALANCED_AWS_SECRET_ACCESS_KEY'] or os.environ['AWS_SECRET_ACCESS_KEY']))
        parser.add_argument('--region', help='AWS region', default='us-west-1')
        subparsers = parser.add_subparsers(title='commands')
        for name, cmd_class in self.commands().iteritems():
            subparser = subparsers.add_parser(name, help=cmd_class.help)
            subparser.set_defaults(instance=cmd_class(self, subparser))
        return parser

    def __call__(self, args):
        parser = self.parser()
        self.args = parser.parse_args(args)
        self.cfn = self.connect_cfn(self.args.region)
        self.args.instance(self.args)

    def connect_cfn(self, region):
        for r in boto.cloudformation.regions():
            if r.name == region:
                break
        else:
            raise ValueError('Unknown region {0}'.format(region))
        return boto.connect_cloudformation(self.args.aws_access_key_id, self.args.aws_secret_access_key, region=r)

    def load_template(self, name):
        # Meh, want to get back to this later, leave commented for one commit
        # py = pkg_resources.resource_string(__name__, '../stacks/{}.py'.format(name))
        # code = compile(py, '{}.py'.format(name), 'exec')
        # mod = eval(code)
        # return mod

        # Mahmoud, be mad ;-)
        try:
            # Kind of gross that the stacks module needs to be global-ish
            mod = importlib.import_module('stacks.{0}'.format(name), __package__)
        except ImportError:
            mod = importlib.import_module('stacks.balanced_{0}'.format(name), __package__)
        for key, value in mod.__dict__.iteritems():
            if isinstance(value, type) and issubclass(value, troposphere.Template) and not key[0] == '_' and key != 'Template':
                return value


    def _cfn_iterate(self, fn):
        """Helper for CloudFormation API paging."""
        first = True
        next_token = None
        while next_token or first:
            objs = fn(next_token)
            for obj in objs:
                yield obj # My kingdom for a yield from
            first = False
            next_token = objs.next_token

def main():
    BrixApplication()(sys.argv[1:])
