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

from troposphere import FindInMap, GetAtt, Join, Ref

from .balanced_region import BalancedRegionBase, FindInRegionMap
from .base import Stack


class AppStack(Stack):
    def __init__(self, *args, **kwargs):
        self._parameters = kwargs.pop('Parameters', {})
        super(AppStack, self).__init__(*args, **kwargs)

    def DependsOn(self):
        return [self.template.srta_RouteAssocA(), self.template.srta_RouteAssocB()]

    def Parameters(self):
        params = {
            'AmiId': FindInRegionMap(self.template.map_RegionMap(), 'AmiId'),
            'SubnetA': Ref(self.template.subnet_SubnetA()),
            'SubnetB': Ref(self.template.subnet_SubnetB()),
            'GatewaySecurityGroupA': 'sg-cdbdafa1',
            'GatewaySecurityGroupB': 'sg-cdbdafa1',
        }
        params.update(self._parameters)
        return params


class LegacyRegionTemplate(BalancedRegionBase):
    """Template our legacy VPC region."""

    @classmethod
    def STRATOSPHERE_TYPES(cls):
        return BalancedRegionBase.STRATOSPHERE_TYPES() + [
            ('app', 'apps', 'add_resource', AppStack),
        ]

    def vpc(self):
        return 'vpc-d6832dbf'

    def rtb_RouteTableA(self):
        return 'rtb-ac832dc5'

    def rtb_RouteTableB(self):
        return 'rtb-5c1c9b35'

    def subnet_SubnetA(self):
        """AZ A network subnet."""
        return {
            'VpcId': self.vpc(),
            'AvailabilityZone': 'us-west-1a',
            'CidrBlock': '10.3.200.0/20',
        }

    def srta_RouteAssocA(self):
        """Association between the AZ A subnet and the route table."""
        return {
            'RouteTableId': self.rtb_RouteTableA(),
            'SubnetId': Ref(self.subnet_SubnetA()),
        }

    def subnet_SubnetB(self):
        """AZ B network subnet."""
        return {
            'VpcId': self.vpc(),
            'AvailabilityZone': 'us-west-1b',
            'CidrBlock': '10.3.216.0/20',
        }

    def srta_RouteAssocB(self):
        """Association between the AZ B subnet and the route table."""
        return {
            'RouteTableId': self.rtb_RouteTableB(),
            'SubnetId': Ref(self.subnet_SubnetB()),
        }

    def app_BalancedDocs(self):
        """Balanced documentation stack."""
        return {'TemplateName': 'balanced_docs'}

    def app_BalancedApiProduction(self):
        """Balanced API production stack."""
        return {
            'TemplateName': 'balanced_api',
            'Parameters': {
                'Env': 'production',
                'ChefEnv': 'production',
                'Capacity': 4,
            },
        }

    def app_BalancedApiTest(self):
        """Balanced API test stack."""
        return {
            'TemplateName': 'balanced_api',
            'Parameters': {
                'Env': 'test',
                'ChefEnv': 'test',
                'Capacity': 2,
            },
        }
