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

from .base import Template

def FindInRegionMap(map, key):
    """Helper to do a lookup in a region-based mapping."""
    return FindInMap(map, Ref('AWS::Region'), key)


class BalancedRegionTemplate(Template):
    """Template for a whole AWS region."""

    def param_VpcId(self):
        # We don't have one of these, we are the alpha and the omega
        return None

    def map_RegionMap(self):
        return {
            'us-west-1': {
                'VpcCidr': '10.5.0.0/16',
                'GatewayCidrA': '10.5.0.0/28',
                'GatewayCidrB': '10.5.0.16/28',
                'GatewayCidrC': '10.5.0.32/28',
                'GatewayAmiId': 'ami-d69aad93',
                'AmiId': 'ami-a8f5c8ed',
            },
            'us-west-2': {
                'VpcCidr': '10.6.0.0/16',
                'GatewayCidrA': '10.6.0.0/28',
                'GatewayCidrB': '10.6.0.16/28',
                'GatewayCidrC': '10.6.0.32/28',
                'GatewayAmiId': 'ami-f032acc0',
                'AmiId': 'ami-9a97f4aa',
            }
        }

    def map_ProductionMap(self):
        return {
            'us-west-1': {
                'CidrA': '10.5.16.0/20',
                'CidrB': '10.5.32.0/20',
                'CidrC': '10.5.64.0/20',
            },
            'us-west-2': {
                'CidrA': '10.6.16.0/20',
                'CidrB': '10.6.32.0/20',
                'CidrC': '10.6.64.0/20',
            },
        }

    def map_TestMap(self):
        return {
            'us-west-1': {
                'CidrA': '10.5.80.0/20',
                'CidrB': '10.5.96.0/20',
                'CidrC': '10.5.112.0/20',
            },
            'us-west-2': {
                'CidrA': '10.6.80.0/20',
                'CidrB': '10.6.96.0/20',
                'CidrC': '10.6.112.0/20',
            },
        }

    def map_MiscMap(self):
        return {
            'us-west-1': {
                'CidrA': '10.5.128.0/20',
                'CidrB': '10.5.144.0/20',
                'CidrC': '10.5.160.0/20',
            },
            'us-west-2': {
                'CidrA': '10.6.128.0/20',
                'CidrB': '10.6.144.0/20',
                'CidrC': '10.6.160.0/20',
            },
        }

    def vpc(self):
        """VPC for this region."""
        return {
            'CidrBlock': FindInRegionMap(self.map_RegionMap(), 'VpcCidr'),
        }

    def ig(self):
        """Internet gateway for this region."""
        return {}

    def vga(self):
        """VPC gateway attachement for the internet."""
        return {
            'VpcId': Ref(self.vpc()),
            'InternetGatewayId': Ref(self.ig()),
        }

    def rtb(self):
        """Route table for public subnets."""
        return {
            'VpcId': Ref(self.vpc()),
        }

    def route_GatewayRoute(self):
        """Route to the internet gateway."""
        return {
            'RouteTableId': Ref(self.rtb()),
            'DestinationCidrBlock': '0.0.0.0/0',
            'GatewayId': Ref(self.ig()),
        }

    def _stack_zone(self, zone_id):
        """Helper to create AZ stacks."""
        zone_id = zone_id.upper()
        return {
            'TemplateName': 'balanced_az',
            'Parameters': {
                'PublicRouteTableId': Ref(self.rtb()),
                'AvailabilityZone': Join('', [Ref('AWS::Region'), zone_id.lower()]),
                'GatewayCidr': FindInRegionMap(self.map_RegionMap(), 'GatewayCidr'+zone_id),
                'ProductionCidr': FindInRegionMap(self.map_ProductionMap(), 'Cidr'+zone_id),
                'TestCidr': FindInRegionMap(self.map_TestMap(), 'Cidr'+zone_id),
                'MiscCidr': FindInRegionMap(self.map_MiscMap(), 'Cidr'+zone_id),
                'GatewayAmiId': FindInRegionMap(self.map_RegionMap(), 'GatewayAmiId'),
            },
            'DependsOn': self.vga(),
        }

    def stack_ZoneA(self):
        """Availability Zone A."""
        return self._stack_zone('a')

    def stack_ZoneB(self):
        """Availability Zone B."""
        return self._stack_zone('b')

    def stack_ZoneC(self):
        """Availability Zone C."""
        return self._stack_zone('c')

    def stack_BalancedDocs(self):
        """Balanced documentation stack."""
        return {
            'TemplateName': 'balanced_docs',
            'Parameters': {
                'Env': 'misc',
                'AmiId': FindInRegionMap(self.map_RegionMap(), 'AmiId'),
                'SubnetA': GetAtt(self.stack_ZoneA(), 'Outputs.MiscSubnet'),
                'SubnetB': GetAtt(self.stack_ZoneB(), 'Outputs.MiscSubnet'),
                'SubnetC': GetAtt(self.stack_ZoneC(), 'Outputs.MiscSubnet'),
                'GatewaySecurityGroupA': GetAtt(self.stack_ZoneA(), 'Outputs.GatewaySecurityGroup'),
                'GatewaySecurityGroupB': GetAtt(self.stack_ZoneB(), 'Outputs.GatewaySecurityGroup'),
                'GatewaySecurityGroupC': GetAtt(self.stack_ZoneC(), 'Outputs.GatewaySecurityGroup'),
            },
        }

if __name__ == '__main__':
    print(BalancedRegionTemplate().to_json())
