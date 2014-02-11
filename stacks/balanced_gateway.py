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

from troposphere import Join, Ref

import stratosphere

from .base import Template

class GatewayInstance(stratosphere.ec2.Instance):
    def AvailabilityZone(self):
        return self.template.subnet().AvailabilityZone

    def IamInstanceProfile(self):
        return Ref(self.template.insp())

    def ImageId(self):
        return Ref(self.template.param_AmiId())

    def InstanceType(self):
        return 'm1.small' # yolo

    def KeyName(self):
        return Ref(self.template.param_KeyName())

    def NetworkInterfaces(self):
        return [{
            'AssociatePublicIpAddress': True,
            'DeviceIndex': '0',
            'GroupSet': [Ref(self.template.sg())],
            'SubnetId': Ref(self.template.subnet()),
        }]

    def SourceDestCheck(self):
        return False


class BalancedGateway(Template):
    """NAT gateway configuration."""

    def param_AvailabilityZone(self):
        """Availability zone."""
        return {'Type': 'String'}

    def param_Cidr(self):
        """CIDR block for this network."""
        return {'Type': 'String'}

    def param_AmiId(self):
        """AMI ID."""
        return {'Type': 'String'}

    def param_PublicRouteTableId(self):
        """Route table to use for public subnet."""
        return {'Type': 'String'}

    def subnet(self):
        """Gateway network subnet."""
        return {
            'VpcId': Ref(self.param_VpcId()),
            'AvailabilityZone': Ref(self.param_AvailabilityZone()),
            'CidrBlock': Ref(self.param_Cidr()),
        }

    def srta(self):
        """Association between the subnet and the public subnet route table."""
        return {
            'RouteTableId': Ref(self.param_PublicRouteTableId()),
            'SubnetId': Ref(self.subnet()),
        }

    def sg(self):
        """Security group for gateway instance."""
        return {}

    def role(self):
        """IAM role for gateway instance."""
        return {
            'Statements': [
                {
                    'Effect': 'Allow',
                    'Action': 's3:GetObject',
                    'Resource': Join('', ['arn:aws:s3:::balanced-cfn-', Ref('AWS::Region'), '/*']),
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'route53:GetHostedZone',
                        'route53:ListResourceRecordSets',
                        'route53:ChangeResourceRecordSets',
                  ],
                  'Resource': 'arn:aws:route53:::hostedzone/Z2IP8RX9IARH86',
                },
            ],
        }

    def insp(self):
        """IAM instance profile for gateway instance."""
        return {'Roles': [Ref(self.role())]}

    def instance(self):
        """EC2 instance serving as a NAT gateway."""
        return GatewayInstance('GatewayInstance', template=self)

    def out_Instance(self):
        """Gateway instance ID."""
        return {'Value': Ref(self.instance())}

    def out_SecurityGroup(self):
        """Gateway security group."""
        return {'Value': Ref(self.sg())}


if __name__ == '__main__':
    print(BalancedGateway().to_json())
