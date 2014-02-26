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
from troposphere import If, Ref, Join, Base64

import stratosphere
from stratosphere.functions import And, Equals, Not


class ConditionalAZMixin(object):
    """A mixing to load some default parameters for multi-AZ objects."""

    def __init__(self, *args, **kwargs):
        template = kwargs.get('template')
        self._cond_a = kwargs.pop('CondA', None)
        self._cond_b = kwargs.pop('CondB', None)
        self._cond_c = kwargs.pop('CondC', None)
        self._subnet_a = kwargs.pop('SubnetA', None)
        self._subnet_b = kwargs.pop('SubnetB', None)
        self._subnet_c = kwargs.pop('SubnetC', None)
        self._gateway_security_group_a = kwargs.pop('GatewaySecurityGroupA', None)
        self._gateway_security_group_b = kwargs.pop('GatewaySecurityGroupB', None)
        self._gateway_security_group_c = kwargs.pop('GatewaySecurityGroupC', None)

        if template:
            if not self._cond_a and hasattr(template, 'cond_HasA'):
                self._cond_a = 'HasA'
            if not self._cond_b and hasattr(template, 'cond_HasB'):
                self._cond_b = 'HasB'
            if not self._cond_c and hasattr(template, 'cond_HasC'):
                self._cond_c = 'HasC'

            if not self._subnet_a and hasattr(template, 'param_SubnetA'):
                self._subnet_a = Ref(template.param_SubnetA())
            if not self._subnet_b and hasattr(template, 'param_SubnetB'):
                self._subnet_b = Ref(template.param_SubnetB())
            if not self._subnet_c and hasattr(template, 'param_SubnetC'):
                self._subnet_c = Ref(template.param_SubnetC())

            if not self._gateway_security_group_a and hasattr(template, 'param_GatewaySecurityGroupA'):
                self._gateway_security_group_a = Ref(template.param_GatewaySecurityGroupA())
            if not self._gateway_security_group_b and hasattr(template, 'param_GatewaySecurityGroupB'):
                self._gateway_security_group_b = Ref(template.param_GatewaySecurityGroupB())
            if not self._gateway_security_group_c and hasattr(template, 'param_GatewaySecurityGroupC'):
                self._gateway_security_group_c = Ref(template.param_GatewaySecurityGroupC())

        super(ConditionalAZMixin, self).__init__(*args, **kwargs)


class SecurityGroup(ConditionalAZMixin, stratosphere.ec2.SecurityGroup):
    def __init__(self, *args, **kwargs):
        self._allow = kwargs.pop('Allow', [])
        self._allow_self = kwargs.pop('AllowSelf', True)
        self._allow_ssh = kwargs.pop('AllowSSH', False)
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
        if self._allow_ssh:
            rules.append(stratosphere.ec2.SecurityGroupRule(
                'SSH',
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp='0.0.0.0/0',
            ))
        else:
            if self._cond_a:
                rules.append(If(
                    self._cond_a,
                    stratosphere.ec2.SecurityGroupRule(
                        'SSHA',
                        IpProtocol='tcp',
                        FromPort='22',
                        ToPort='22',
                        SourceSecurityGroupId=self._gateway_security_group_a,
                    ),
                    Ref('AWS::NoValue')
                ))
            if self._cond_b:
                rules.append(If(
                    self._cond_b,
                    stratosphere.ec2.SecurityGroupRule(
                        'SSHB',
                        IpProtocol='tcp',
                        FromPort='22',
                        ToPort='22',
                        SourceSecurityGroupId=self._gateway_security_group_b,
                    ),
                    Ref('AWS::NoValue')
                ))
            if self._cond_c:
                rules.append(If(
                    self._cond_c,
                    stratosphere.ec2.SecurityGroupRule(
                        'SSHC',
                        IpProtocol='tcp',
                        FromPort='22',
                        ToPort='22',
                        SourceSecurityGroupId=self._gateway_security_group_c,
                    ),
                    Ref('AWS::NoValue')
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


class LoadBalancer(ConditionalAZMixin, stratosphere.elasticloadbalancing.LoadBalancer):
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
        subnets = []
        if self._cond_a:
            subnets.append(If(self._cond_a, self._subnet_a, Ref('AWS::NoValue')))
        if self._cond_b:
            subnets.append(If(self._cond_b, self._subnet_b, Ref('AWS::NoValue')))
        if self._cond_c:
            subnets.append(If(self._cond_c, self._subnet_c, Ref('AWS::NoValue')))
        return subnets


class LaunchConfiguration(stratosphere.autoscaling.LaunchConfiguration):
    def __init__(self, *args, **kwargs):
        self._security_group = kwargs.pop('SecurityGroup', None)
        self._chef_recipe = kwargs.pop('ChefRecipe')
        self._chef_env = kwargs.pop('ChefEnv')
        self._name_tag = kwargs.pop('NameTag', 'ec2')
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
            '#!/bin/bash -xe\n',
            '/opt/bootstrap.sh "', self._name_tag, '" "', self._chef_env, '" "',  self._chef_recipe, '"\n',
        ]))


class AutoScalingGroup(ConditionalAZMixin, stratosphere.autoscaling.AutoScalingGroup):
    def AvailabilityZones(self):
        zones = []
        if self._cond_a:
            zones.append(If(self._cond_a, Join('', [Ref('AWS::Region'), 'a']), Ref('AWS::NoValue')))
        if self._cond_b:
            zones.append(If(self._cond_b, Join('', [Ref('AWS::Region'), 'b']), Ref('AWS::NoValue')))
        if self._cond_c:
            zones.append(If(self._cond_c, Join('', [Ref('AWS::Region'), 'c']), Ref('AWS::NoValue')))
        return zones

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
        if self._cond_a:
            subnets.append(If(self._cond_a, self._subnet_a, Ref('AWS::NoValue')))
        if self._cond_b:
            subnets.append(If(self._cond_b, self._subnet_b, Ref('AWS::NoValue')))
        if self._cond_c:
            subnets.append(If(self._cond_c, self._subnet_c, Ref('AWS::NoValue')))
        return subnets


class Stack(stratosphere.cloudformation.Stack):
    # Find a better way to do this
    TEMPLATES = {}

    def __init__(self, *args, **kwargs):
        self._parameters = kwargs.pop('Parameters', {})
        self._template_name = kwargs.pop('TemplateName', None)
        super(Stack, self).__init__(*args, **kwargs)

    def TemplateURL(self):
        if self._template_name:
            if 'sha1' not in self.TEMPLATES.get(self._template_name, {}):
                raise ValueError('Unknown template {}'.format(self._template_name))
            return Join('', [
                'https://balanced-cfn-',
                Ref('AWS::Region'),
                '.s3.amazonaws.com/templates/{}-{}.json'.format(self._template_name, self.TEMPLATES[self._template_name]['sha1']),
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

    def param_VpcId(self):
        """VPC ID."""
        return {'Type': 'String'}

    def param_KeyName(self):
        """SSH key name."""
        return {'Type': 'String', 'Default': 'cloudformation'}


class AppTemplate(Template):
    """A model for Cloud Formation stack for a Balanced application."""

    # Parameter defaults
    ENV = 'production'
    CHEF_RECIPE = None
    STACK_TAG = None
    INSTANCE_TYPE = 'm1.small'
    CAPACITY = 1
    CITADEL_FOLDERS = []
    S3_BUCKETS = []
    IAM_STATEMENTS = []
    PORT = 80

    def param_ChefRecipe(self):
        """Chef recipe name."""
        if not self.CHEF_RECIPE:
            raise ValueError('CHEF_RECIPE not set for {}'.format(self.__class__.__name__))
        return {'Type': 'String', 'Default': self.CHEF_RECIPE}

    def param_Tag(self):
        """Stack tag."""
        if not self.STACK_TAG:
            raise ValueError('STACK_TAG not set for {}'.format(self.__class__.__name__))
        return {'Type': 'String', 'Default': self.STACK_TAG}

    def param_Env(self):
        """Logical environment."""
        return {'Type': 'String', 'AllowedValues': ['production', 'test', 'misc'], 'Default': 'production'}

    def param_ChefEnv(self):
        """Configuration environment."""
        return {'Type': 'String', 'Default': self.ENV}

    def param_InstanceType(self):
        """Instance type."""
        return {'Type': 'String', 'Default': self.INSTANCE_TYPE}

    def param_Capacity(self):
        """Instance count."""
        return {'Type': 'Number', 'Default': str(self.CAPACITY)}

    def param_AmiId(self):
        """Amazon machine image."""
        return {'Type': 'String'}

    def param_SubnetA(self):
        """Subnet ID for AZ A. Optional."""
        return {'Type': 'String', 'Default': ''}

    def param_SubnetB(self):
        """Subnet ID for AZ B. Optional."""
        return {'Type': 'String', 'Default': ''}

    def param_SubnetC(self):
        """Subnet ID for AZ C. Optional."""
        return {'Type': 'String', 'Default': ''}

    def param_GatewaySecurityGroupA(self):
        """Security group ID for AZ A Gateway instances. Optional."""
        return {'Type': 'String', 'Default': ''}

    def param_GatewaySecurityGroupB(self):
        """Security group ID for AZ B Gateway instances. Optional."""
        return {'Type': 'String', 'Default': ''}

    def param_GatewaySecurityGroupC(self):
        """Security group ID for AZ C Gateway instances. Optional."""
        return {'Type': 'String', 'Default': ''}

    def cond_HasA(self):
        """Condition checking if AZ A is usable."""
        return And(
            Not(Equals(Ref(self.param_SubnetA()), '')),
            Not(Equals(Ref(self.param_GatewaySecurityGroupA()), '')),
        )

    def cond_HasB(self):
        """Condition checking if AZ B is usable."""
        return And(
            Not(Equals(Ref(self.param_SubnetB()), '')),
            Not(Equals(Ref(self.param_GatewaySecurityGroupB()), '')),
        )

    def cond_HasC(self):
        """Condition checking if AZ C is usable."""
        return And(
            Not(Equals(Ref(self.param_SubnetC()), '')),
            Not(Equals(Ref(self.param_GatewaySecurityGroupC()), '')),
        )

    def sg(self):
        """Security group."""
        return {
            'Description': 'Security group for {}'.format(self.__class__.__name__),
            'Allow': [self.PORT],
        }

    def elb(self):
        """Load balancer."""
        return {
            'Description': 'Load balancer for {}'.format(self.__class__.__name__),
            'HealthUrl': '/health',
            'Port': self.PORT,
        }

    # TODO: this needs an overhaul
    def role(self):
        """IAM role for Balanced docs."""
        citadel_folders = ['newrelic', 'deploy_key'] + self.CITADEL_FOLDERS
        s3_buckets = ['balanced-citadel/{}'.format(s) for s in citadel_folders] + ['balanced.debs', 'apt.vandelay.io'] + self.S3_BUCKETS
        s3_objects = ['arn:aws:s3:::{}/*'.format(s) for s in s3_buckets]
        return {
            'Statements': [
                {
                    'Effect': 'Allow',
                    'Action': 's3:GetObject',
                    'Resource': s3_objects,
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
            ] + self.IAM_STATEMENTS,
        }

    def insp(self):
        """IAM instance profile."""
        return {
            'Description': 'IAM instance profile for {}'.format(self.__class__.__name__),
            'Roles': [Ref(self.role())],
        }

    def lc(self):
        """ASG launch configuration."""
        return {
            'Description': 'ASG launch configuration for {}'.format(self.__class__.__name__),
            'SecurityGroup': Ref(self.sg()),
            'ChefRecipe': Ref(self.param_ChefRecipe()),
            'ChefEnv': Ref(self.param_ChefEnv()),
            'NameTag': Ref(self.param_Tag()),
            'InstanceType': Ref(self.param_InstanceType()),
        }

    def asg(self):
        """Autoscaling group."""
        return {
            'Description': 'Autoscaling group for {}'.format(self.__class__.__name__),
            'MinSize': Ref(self.param_Capacity()),
            'MaxSize': Ref(self.param_Capacity()),
        }
