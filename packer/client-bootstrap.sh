#!/bin/bash -xe
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

# Config options
TAG="$1"
ENV="$2"
ROLE="$3"

# Set the hostname
LOCAL_IPV4="$(curl http://169.254.169.254/latest/meta-data/local-ipv4)"
HOSTNAME="${TAG}-${ENV}-$(echo $LOCAL_IPV4 | sed s/\\./-/g)"
echo "$HOSTNAME" > /etc/hostname
hostname "$HOSTNAME"

# Write Chef first-boot JSON
cat > /etc/chef/first-boot.json <<EOP
{"run_list":["recipe[role-base]", "recipe[$ROLE]"]}
EOP

# Lock the chef node name
echo "node_name '$HOSTNAME'" >> /etc/chef/client.rb

# Run Chef
chef-client --environment "$ENV" --json-attributes /etc/chef/first-boot.json --logfile /var/log/chef-bootstrap.log
