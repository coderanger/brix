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

# Install Chef
curl -L https://www.opscode.com/chef/install.sh | sudo bash

# Install ec2-ami-tools
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y unzip
curl -o /tmp/ec2-ami-tools.zip http://s3.amazonaws.com/ec2-downloads/ec2-ami-tools.zip
# The Amazon zip file has recoverable errors
(
set +e
unzip -d /tmp /tmp/ec2-ami-tools.zip
RV="$?"
if [[ "$RV" -gt 1 ]]; then
  exit "$RV"
fi
set -e
)
rm /tmp/ec2-ami-tools.zip
sudo mkdir /opt/ec2-ami-tools
sudo mv /tmp/ec2-ami-tools*/* /opt/ec2-ami-tools
rm -rf /tmp/ec2-ami-tools*
sudo chown -R root:root /opt/ec2-ami-tools

# Configure Chef
sudo mkdir /etc/chef
sudo chown -R root:root /etc/chef
sudo chmod 700 /etc/chef
if [ -f /tmp/cacert.pem ]; then
  sudo mv /tmp/cacert.pem /etc/chef
  sudo chmod 600 /etc/chef/cacert.pem
fi
if [ -f /tmp/validation.pem ]; then
  sudo mv /tmp/validation.pem /etc/chef
  sudo chmod 600 /etc/chef/validation.pem
fi
if [ -f /tmp/client.rb ]; then
  sudo mv /tmp/client.rb /etc/chef
  sudo chmod 600 /etc/chef/client.rb
fi
if [ -f /tmp/solo.rb ]; then
  sudo mv /tmp/solo.rb /etc/chef
  sudo chmod 600 /etc/chef/solo.rb
fi

# Ohai hints
sudo mkdir /etc/chef/ohai
sudo mkdir /etc/chef/ohai/hints
echo '{}' | sudo tee /etc/chef/ohai/hints/ec2.json
sudo chmod 700 /etc/chef/ohai /etc/chef/ohai/hints
sudo chmod 600 /etc/chef/ohai/hints/ec2.json

# Move the bootstrap script into place
sudo mv /tmp/bootstrap.sh /opt
sudo chown root:root /opt/bootstrap.sh
sudo chmod 744 /opt/bootstrap.sh

# more bootstrapping
sudo apt-get -y install python-pip xfs xfsprogs
sudo pip install /tmp/aws-cfn-bootstrap-20140311.tar.gz
sudo pip install awscli
sudo mv /tmp/jq /usr/bin/
sudo chmod 755 /usr/bin/jq

# this is really slow to build on instances, let's build it here such performance
sudo mv /tmp/gemrc /etc/gemrc
sudo chmod 444 /etc/gemrc
sudo apt-get -y install build-essential
sudo /opt/chef/embedded/bin/gem install fog
