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

from .base import AppTemplate


class BalancedDocs(AppTemplate):
    """Balanced docs"""

    ENV = 'misc'
    CHEF_RECIPE = 'balanced-docs'
    STACK_TAG = 'docs'
    PUBLIC = True

    def elb(self):
        """Load balancer for BalancedDocs."""
        elb = super(BalancedDocs, self).elb()
        elb['HealthUrl'] = '/'
        elb['SSLCertificateId'] = 'balancedpayments-2014'
        return elb


if __name__ == '__main__':
    print(BalancedDocs().to_json())
