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

from .base import Template


class BalancedDocs(Template):
    """Balanced docs"""

    CHEF_ROLE = 'balanced-docs'
    STACK_TAG = 'docs'

    def param_Env(self):
        return {'Type': 'String'}

    def param_AmiId(self):
        return {'Type': 'String'}

    def param_SubnetA(self):
        return {'Type': 'String'}

    def param_SubnetB(self):
        return {'Type': 'String'}

    def param_SubnetC(self):
        return {'Type': 'String'}

    def param_GatewaySecurityGroupA(self):
        return {'Type': 'String'}

    def param_GatewaySecurityGroupB(self):
        return {'Type': 'String'}

    def param_GatewaySecurityGroupC(self):
        return {'Type': 'String'}

    def sg(self):
        """Balanced docs security group."""
        return {
            'Allow': [80],
            'GatewaySecurityGroupA': Ref(self.param_GatewaySecurityGroupA()),
            'GatewaySecurityGroupB': Ref(self.param_GatewaySecurityGroupB()),
            'GatewaySecurityGroupC': Ref(self.param_GatewaySecurityGroupC()),
        }

    def elb(self):
        """Balanced docs load balancer."""
        return {'HealthUrl': '/'}

    def role(self):
        """IAM role for Balanced docs."""
        return {
            'Statements': [
                {
                    'Effect': 'Allow',
                    'Action': 's3:GetObject',
                    'Resource':[
                        Join('', ['arn:aws:s3:::balanced-cfn-', Ref('AWS::Region'), '/*']),
                        "arn:aws:s3:::balanced.citadel/newrelic/*",
                        "arn:aws:s3:::balanced.debs/*",
                        "arn:aws:s3:::apt.vandelay.io/*",
                    ],
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
        """IAM instance profile for Balanced docs."""
        return {'Roles': [Ref(self.role())]}

    def lc(self):
        """Balanced docs launch configuration."""
        return {
            'SecurityGroup': Ref(self.sg()),
            'ChefRole': self.CHEF_ROLE,
            'ChefEnv': 'production',
            'NameTag': self.STACK_TAG,
            'InstanceType': 'm1.small',
        }

    def asg(self):
        """Balanced docs autoscaling group."""
        return {
            'SubnetA': Ref(self.param_SubnetA()),
            'SubnetB': Ref(self.param_SubnetB()),
            'SubnetC': Ref(self.param_SubnetC()),
        }

if __name__ == '__main__':
    print(BalancedDocs().to_json())
