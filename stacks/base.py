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

import troposphere.elasticloadbalancing
from troposphere import Ref, Join, Base64

import stratosphere


class SecurityGroup(stratosphere.ec2.SecurityGroup):
    def __init__(self, *args, **kwargs):
        self._allow = kwargs.pop('Allow', [])
        self._allow_self = kwargs.pop('AllowSelf', True)
        self._gateway_security_group_a = kwargs.pop('GatewaySecurityGroupA', None)
        self._gateway_security_group_b = kwargs.pop('GatewaySecurityGroupB', None)
        self._gateway_security_group_c = kwargs.pop('GatewaySecurityGroupC', None)
        super(SecurityGroup, self).__init__(*args, **kwargs)

    def VpcId(self):
        return Ref(self.template.param_VpcId())

    def SecurityGroupIngress(self):
        rules = []
        rules.append(stratosphere.ec2.SecurityGroupRule(
            'ICMP',
            IpProtocol='icmp',
            FromPort='-1',
            ToPort='-1',
            CidrIp='0.0.0.0/0',
        ))
        if not (self._gateway_security_group_a or self._gateway_security_group_b or self._gateway_security_group_c):
            rules.append(stratosphere.ec2.SecurityGroupRule(
                'SSH',
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp='0.0.0.0/0',
            ))
        else:
            if self._gateway_security_group_a:
                rules.append(stratosphere.ec2.SecurityGroupRule(
                    'SSHA',
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    SourceSecurityGroupId=self._gateway_security_group_a,
                ))
            if self._gateway_security_group_b:
                rules.append(stratosphere.ec2.SecurityGroupRule(
                    'SSHB',
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    SourceSecurityGroupId=self._gateway_security_group_b,
                ))
            if self._gateway_security_group_c:
                rules.append(stratosphere.ec2.SecurityGroupRule(
                    'SSHC',
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    SourceSecurityGroupId=self._gateway_security_group_c,
                ))
        for port in self._allow:
            rules.append(stratosphere.ec2.SecurityGroupRule(
                'Port{0}'.format(port),
                IpProtocol='tcp',
                FromPort=str(port),
                ToPort=str(port),
                CidrIp='0.0.0.0/0',
            ))
        return rules

    def post_add(self, template):
        if self._allow_self:
            template.add_resource(stratosphere.ec2.SecurityGroupIngress(
                self.name + 'SelfTCPIngress',
                IpProtocol='tcp',
                FromPort='0',
                ToPort='65535',
                GroupId=Ref(self),
                SourceSecurityGroupId=Ref(self),
            ))
            template.add_resource(stratosphere.ec2.SecurityGroupIngress(
                self.name + 'SelfUDPIngress',
                IpProtocol='udp',
                FromPort='0',
                ToPort='65535',
                GroupId=Ref(self),
                SourceSecurityGroupId=Ref(self),
            ))
            template.add_resource(stratosphere.ec2.SecurityGroupIngress(
                self.name + 'SelfICMPIngress',
                IpProtocol='icmp',
                FromPort='-1',
                ToPort='-1',
                GroupId=Ref(self),
                SourceSecurityGroupId=Ref(self),
            ))


class LoadBalancer(stratosphere.elasticloadbalancing.LoadBalancer):
    def __init__(self, *args, **kwargs):
        self._port = kwargs.pop('Port', '80')
        self._ssl_certificate_id = kwargs.pop('SSLCertificateId', 'balancedpayments-2014')
        self._security_group = kwargs.pop('SecurityGroup', None)
        self._health_url = kwargs.pop('HealthUrl', '/health')
        super(LoadBalancer, self).__init__(*args, **kwargs)

    def CrossZone(self):
        # Why the bloody hell is this false by default?
        return True

    def SecurityGroups(self):
        if self._security_group:
            return [self._security_group]

    def Listeners(self):
        listeners = [self._http_listener()]
        if self._ssl_certificate_id:
            listeners.append(self._https_listener())
        return listeners

    def _http_listener(self):
        return troposphere.elasticloadbalancing.Listener(
            LoadBalancerPort='80',
            InstancePort=self._port,
            Protocol='HTTP',
            InstanceProtocol='HTTP',
        )

    def _https_listener(self):
        return troposphere.elasticloadbalancing.Listener(
            LoadBalancerPort='443',
            InstancePort=self._port,
            Protocol='HTTPS',
            InstanceProtocol='HTTP',
            SSLCertificateId=Join('', [
                'arn:aws:iam::',
                Ref('AWS::AccountId'),
                ':server-certificate/',
                self._ssl_certificate_id,
            ]),
        )

    def HealthCheck(self):
        if self._health_url:
            return troposphere.elasticloadbalancing.HealthCheck(
                Target=Join('', ['HTTP:', '80', self._health_url]),
                HealthyThreshold='3',
                UnhealthyThreshold='5',
                Interval='30',
                Timeout='5',
            )

    def Subnets(self):
        return [
            Ref(self.template.param_SubnetA()),
            Ref(self.template.param_SubnetB()),
            Ref(self.template.param_SubnetC()),
        ]


class LaunchConfiguration(stratosphere.autoscaling.LaunchConfiguration):
    def __init__(self, *args, **kwargs):
        self._security_group = kwargs.pop('SecurityGroup', None)
        self._chef_role = kwargs.pop('ChefRole')
        self._chef_env = kwargs.pop('ChefEnv')
        self._name_tag = kwargs.pop('NameTag', self._chef_role)
        super(LaunchConfiguration, self).__init__(*args, **kwargs)

    def IamInstanceProfile(self):
        return Ref(self.template.insp())

    def ImageId(self):
        return Ref(self.template.param_AmiId())

    def KeyName(self):
        return Ref(self.template.param_KeyName())

    def SecurityGroups(self):
        if self._security_group:
            return [self._security_group]

    def UserData(self):
        return Base64(Join('', [
            '#!/bin/bash -vxe\n',
            'apt-get --yes update\n'
            'apt-get --yes install python-pip\n'
            'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n'
            'cfn-init',
                ' --stack ', Ref('AWS::StackName'),
                ' --resource ', self.name,
                ' --region ', Ref('AWS::Region'),
            '\n',
        ]))

    def Metadata(self):
        return {
            'AWS::CloudFormation::Authentication': {
                'S3AccessCreds' : {
                    'type': 'S3',
                    'buckets': ['balanced.confucius'],
                    'roleName': 'balanced-api',
                }
            },
            'AWS::CloudFormation::Init': {
                'configSets': {
                    'default': ['dependencies', 'bootstrap']
                },
                'dependencies': {
                    'packages': {
                        'python': {
                            'awscli': []
                        }
                    },
                    'sources' : {
                        '/opt/confucius': Join('', [
                            'https://balanced-cfn-',
                            Ref('AWS::Region'),
                            '.s3.amazonaws.com/chef-v1.tar.gz',
                        ])
                    },
                },
                'bootstrap': {
                    'commands': {
                        'chef': {
                            'command': Join('', [
                                '/opt/confucius/bootstrap.sh',
                                ' --role ', self._chef_role,
                                ' --env ', self._chef_env,
                                ' --tag ', self._name_tag,
                            ]),
                        }
                    }
                }
            }
        }


class AutoScalingGroup(stratosphere.autoscaling.AutoScalingGroup):
    def __init__(self, *args, **kwargs):
        self._subnet_a = kwargs.pop('SubnetA', None)
        self._subnet_b = kwargs.pop('SubnetB', None)
        self._subnet_c = kwargs.pop('SubnetC', None)
        if not (self._subnet_a or self._subnet_b or self._subnet_c):
            raise ValueError('At least one subnet must be provided')
        super(AutoScalingGroup, self).__init__(*args, **kwargs)

    def AvailabilityZones(self):
        azs = []
        if self._subnet_a:
            azs.append(Join('', [Ref('AWS::Region'), 'a']))
        if self._subnet_b:
            azs.append(Join('', [Ref('AWS::Region'), 'b']))
        if self._subnet_c:
            azs.append(Join('', [Ref('AWS::Region'), 'c']))
        return azs

    def LaunchConfigurationName(self):
        return Ref(self.template.lc())

    def LoadBalancerNames(self):
        return [Ref(self.template.elb())]

    def MaxSize(self):
        return '1'

    def MinSize(self):
        return '1'

    def VPCZoneIdentifier(self):
        subnets = []
        if self._subnet_a:
            subnets.append(self._subnet_a)
        if self._subnet_b:
            subnets.append(self._subnet_b)
        if self._subnet_c:
            subnets.append(self._subnet_c)
        return subnets


class Stack(stratosphere.cloudformation.Stack):
    def __init__(self, *args, **kwargs):
        self._parameters = kwargs.pop('Parameters', {})
        self._template_name = kwargs.pop('TemplateName', None)
        super(Stack, self).__init__(*args, **kwargs)

    def TemplateURL(self):
        if self._template_name:
            return Join('', [
                'https://balanced-cfn-',
                Ref('AWS::Region'),
                '.s3.amazonaws.com/templates/{0}.json'.format(self._template_name),
            ])

    def Parameters(self):
        # Default stack parameters
        params = {
            'VpcId': Ref(self.template.param_VpcId() or self.template.vpc()),
            'KeyName': Ref(self.template.param_KeyName()),
        }
        params.update(self._parameters)
        return params


class Template(stratosphere.Template):
    """Defaults and mixins for Balanced templates."""

    AUTO_SCALING_GROUP_TYPE = AutoScalingGroup
    LOAD_BALANCER_TYPE = LoadBalancer
    LAUNCH_CONFIGURATION_TYPE = LaunchConfiguration
    SECURITY_GROUP_TYPE = SecurityGroup
    STACK_TYPE = Stack

    # def parameter_Env(self):
    #     """Stack environment."""
    #     return {'Type': 'String', 'AllowedValues': ['production', 'test', 'misc'], 'Default': 'misc'}

    def param_VpcId(self):
        """VPC ID."""
        return {'Type': 'String'}

    def param_KeyName(self):
        """SSH key name."""
        return {'Type': 'String', 'Default': 'cloudformation'}


class AppTemplate(Template):
    """A model for Cloud Formation stack for a Balanced application."""

    # Parameter defaults
    IAM_ROLE = None
    CHEF_ROLE = None
    STACK_TAG = None
    INSTANCE_TYPE = 'm1.small'
    CAPACITY = 1

    def parameter_KeyName(self):
        """Name of existing EC2 KeyPair to enable SSH access to instances."""
        return {'Type': 'String'}

    def parameter_Role(self):
        """IAM role name."""
        if not self.IAM_ROLE:
            raise ValueError('IAM_ROLE not set for %s'%self.__class__.__name__)
        return {'Type': 'String', 'Default': self.IAM_ROLE}

    def parameter_ChefRole(self):
        """Configuration role name."""
        if not self.CHEF_ROLE:
            raise ValueError('CHEF_ROLE not set for %s'%self.__class__.__name__)
        return {'Type': 'String', 'Default': self.CHEF_ROLE}

    def parameter_Tag(self):
        """Stack tag."""
        if not self.STACK_TAG:
            raise ValueError('STACK_TAG not set for %s'%self.__class__.__name__)
        return {'Type': 'String', 'Default': self.STACK_TAG}

    def parameter_ChefEnv(self):
        """Configuration environment."""
        return {'Type': 'String', 'AllowedValues': ['dev', 'production'], 'Default': 'production'}

    def parameter_InstanceType(self):
        """Instance type."""
        return {'Type': 'String', 'AllowedValues': ['t1.micro', 'm1.small', 'm1.medium', 'm1.large'], 'Default': self.INSTANCE_TYPE}

    def parameter_ConfuciusVer(self):
        """Instance configuration version."""
        return {'Type': 'String', 'Default': '1'}

    def parameter_DesiredCapacity(self):
        """Instance count."""
        return {'Type': 'Number', 'Default': str(self.CAPACITY)}

    def _mapping_us_west_1(self, env):
        return self.deep_merge(super(Template, self)._mapping_us_west_1(env), {
            'AMI': 'ami-e05260a5', # Ubuntu 12.04 daily
            'AvailabilityZones': ['us-west-1a', 'us-west-1b'],
        })

    def elb_LoadBalancer(self):
        return {}

    def lc_LaunchConfiguration(self):
        return {}
