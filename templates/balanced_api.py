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

from ._base import AppTemplate


class BalancedApi(AppTemplate):
    """Balanced API service"""

    CHEF_RECIPE = 'role-balanced-api'
    STACK_TAG = 'bapi'
    INSTANCE_TYPE = 'm3.large'
    PORT = 5000
    CITADEL_FOLDERS = ['omnibus']


if __name__ == '__main__':
    print(BalancedApi().to_json())
