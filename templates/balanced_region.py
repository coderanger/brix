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

from stratosphere import FindInMap, GetAtt, Join, Ref

from ._base import Template


def FindInRegionMap(map, key):
    """Helper to do a lookup in a region-based mapping."""
    return FindInMap(map, Ref('AWS::Region'), key)


class BalancedRegionBase(Template):
    """Base template for regions."""

    def param_VpcId(self):
        # We don't have one of these, we are the alpha and the omega
        return None

    def map_RegionMap(self):
        return {
            'us-west-1': {
                'AmiId': 'ami-dac4f89f',
            },
            'us-west-2': {
                'AmiId': 'ami-3e167a0e',
            },
            'us-east-1': {
                'AmiId': 'ami-21898948', # For the future
            },
        }

    def vpc(self):
        raise NotImplementedError


class BalancedRegionTemplate(BalancedRegionBase):
    """Template for a whole AWS region."""

    def param_Ip(self):
        """Second octet to use for VPC subnets."""
        return {'Type': 'String', 'Default': '5'}

    SUBNETS = {
        'Vpc': '10.{0}.0.0/16',
        'GatewayA': '10.{0}.0.0/28',
        'GatewayB': '10.{0}.0.16/28',
        'GatewayC': '10.{0}.0.32/28',
        'ProductionA': '10.{0}.16.0/20',
        'ProductionB': '10.{0}.32.0/20',
        'ProductionC': '10.{0}.64.0/20',
        'TestA': '10.{0}.80.0/20',
        'TestB': '10.{0}.96.0/20',
        'TestC': '10.{0}.112.0/20',
        'MiscA': '10.{0}.128.0/20',
        'MiscB': '10.{0}.144.0/20',
        'MiscC': '10.{0}.160.0/20',
    }

    def FindSubnet(self, key):
        head, tail = self.SUBNETS[key].split('{0}')
        return Join('', [head, Ref(self.param_Ip()), tail])

    def vpc(self):
        """VPC for this region."""
        return {
            'CidrBlock': self.FindSubnet('Vpc'),
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

    def dhcp(self):
        """DHCP options for this VPC."""
        return {
            'DomainName': 'vandelay.io',
            'DomainNameServers': ['AmazonProvidedDNS'],
        }

    def vdoa(self):
        """DHCP options association for this VPC."""
        return {
            'VpcId': Ref(self.vpc()),
            'DhcpOptionsId': Ref(self.dhcp()),
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
                'GatewayCidr': self.FindSubnet('Gateway{0}'.format(zone_id)),
                'ProductionCidr': self.FindSubnet('Production{0}'.format(zone_id)),
                'TestCidr': self.FindSubnet('Test{0}'.format(zone_id)),
                'MiscCidr': self.FindSubnet('Misc{0}'.format(zone_id)),
                'AmiId': FindInRegionMap(self.map_RegionMap(), 'AmiId'),
            },
            'DependsOn': [self.vga(), self.vdoa()],
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
