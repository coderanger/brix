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


class LegacyRegionTemplate(BalancedRegionBase):
    """Template our legacy VPC region."""

    def vpc(self):
        return 'vpc-d6832dbf'

    def stack_BalancedDocs(self):
        """Balanced documentation stack."""
        return {
            'TemplateName': 'balanced_docs',
            'Parameters': {
                'Env': 'misc',
                'AmiId': FindInRegionMap(self.map_RegionMap(), 'AmiId'),
                'SubnetA': '',
                'SubnetB': '',
                'GatewaySecurityGroupA': '',
                'GatewaySecurityGroupB': '',
            },
        }
