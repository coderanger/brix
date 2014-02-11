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
  balanced-stacks [options] show <name>
  balanced-stacks [options] sync
  balanced-stacks [options] update [<region>]

-h --help                    show this help message and exit
--version                    show program's version number and exit
-q, --quiet                  minimal output
--no-sync                    do not auto-sync before update

Example:
balanced-stacks sync

"""

from __future__ import print_function

import collections
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
        self.region = os.environ.get('BALANCED_AWS_REGION', 'us-west-2')
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

    def update(self, region):
        region = region or self.region
        for r in boto.cloudformation.regions():
            if r.name == region:
                break
        else:
            raise ValueError('Unknown region {0}'.format(region))
        cfn = boto.connect_cloudformation(self.access_key_id, self.secret_access_key, region=r)
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
        elif args['update']:
            if not args['--no-sync']:
                app.sync()
            app.update(args['<region>'])
    except ValueError, e:
        print(e.message, file=sys.stderr)
        sys.exit(1)



if __name__ == '__main__':
    main()
