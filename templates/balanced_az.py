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

from stratosphere import GetAtt, Ref

from ._base import Template


class BalancedAZTemplate(Template):
    """Network configuration for a single Availability Zone."""

    def param_AvailabilityZone(self):
        """Availability zone."""
        return {'Type': 'String'}

    def param_GatewayCidr(self):
        """CIDR block for gateway subnet."""
        return {'Type': 'String'}

    def param_ProductionCidr(self):
        """CIDR block for gateway subnet."""
        return {'Type': 'String'}

    def param_TestCidr(self):
        """CIDR block for gateway subnet."""
        return {'Type': 'String'}

    def param_MiscCidr(self):
        """CIDR block for gateway subnet."""
        return {'Type': 'String'}

    def param_AmiId(self):
        """AMI ID for gateway instances."""
        return {'Type': 'String'}

    def param_PublicRouteTableId(self):
        """Route table to use for public subnet."""
        return {'Type': 'String'}

    def stack_Gateway(self):
        return {
            'TemplateName': 'balanced_gateway',
            'Parameters': {
                'AmiId': Ref(self.param_AmiId()),
                'AvailabilityZone': Ref(self.param_AvailabilityZone()),
                'Cidr': Ref(self.param_GatewayCidr()),
                'PublicRouteTableId': Ref(self.param_PublicRouteTableId()),
            }
        }

    def rtb(self):
        """Route table."""
        return {
            'VpcId': Ref(self.param_VpcId()),
        }

    def route_GatewayRoute(self):
        """Route to the NAT gateway."""
        return {
            'RouteTableId': Ref(self.rtb()),
            'DestinationCidrBlock': '0.0.0.0/0',
            'InstanceId': GetAtt(self.stack_Gateway(), 'Outputs.Instance'),
        }

    def subnet_ProudctionSubnet(self):
        """Production network subnet."""
        return {
            'VpcId': Ref(self.param_VpcId()),
            'AvailabilityZone': Ref(self.param_AvailabilityZone()),
            'CidrBlock': Ref(self.param_ProductionCidr()),
        }

    def srta_ProductionRouteAssoc(self):
        """Association between the production subnet and the route table."""
        return {
            'RouteTableId': Ref(self.rtb()),
            'SubnetId': Ref(self.subnet_ProudctionSubnet()),
        }

    def subnet_TestSubnet(self):
        """Test network subnet."""
        return {
            'VpcId': Ref(self.param_VpcId()),
            'AvailabilityZone': Ref(self.param_AvailabilityZone()),
            'CidrBlock': Ref(self.param_TestCidr()),
        }

    def srta_TestRouteAssoc(self):
        """Association between the test subnet and the route table."""
        return {
            'RouteTableId': Ref(self.rtb()),
            'SubnetId': Ref(self.subnet_TestSubnet()),
        }

    def subnet_MiscSubnet(self):
        """Misc network subnet."""
        return {
            'VpcId': Ref(self.param_VpcId()),
            'AvailabilityZone': Ref(self.param_AvailabilityZone()),
            'CidrBlock': Ref(self.param_MiscCidr()),
        }

    def srta_MiscRouteAssoc(self):
        """Association between the misc subnet and the route table."""
        return {
            'RouteTableId': Ref(self.rtb()),
            'SubnetId': Ref(self.subnet_MiscSubnet()),
        }

    def out_GatewaySecurityGroup(self):
        """Security group ID for the gateway."""
        return {'Value': GetAtt(self.stack_Gateway(), 'Outputs.SecurityGroup')}

    def out_ProductionSubnet(self):
        """Subnet ID for the production network."""
        return {'Value': Ref(self.subnet_ProudctionSubnet())}

    def out_TestSubnet(self):
        """Subnet ID for the test network."""
        return {'Value': Ref(self.subnet_TestSubnet())}

    def out_MiscSubnet(self):
        """Subnet ID for the misc network."""
        return {'Value': Ref(self.subnet_MiscSubnet())}

if __name__ == '__main__':
    print(BalancedAZTemplate().to_json())

