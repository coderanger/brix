#!/bin/bash -xe

# Install Chef
curl -L https://www.opscode.com/chef/install.sh | sudo bash

# Install ec2-ami-tools
sudo apt-get update -y
sudo apt-get install -y unzip
curl -o /tmp/ec2-ami-tools.zip http://s3.amazonaws.com/ec2-downloads/ec2-ami-tools.zip
# The Amazon zip file has recoverable errors
set +e
unzip -d /tmp /tmp/ec2-ami-tools.zip
RV="$?"
if [[ "$RV" -gt 1 ]]; then
  exit "$RV"
fi
set -e
rm /tmp/ec2-ami-tools.zip
sudo mkdir /opt/ec2-ami-tools
sudo mv /tmp/ec2-ami-tools*/* /opt/ec2-ami-tools
rm -rf /tmp/ec2-ami-tools*
sudo chown -R root:root /opt/ec2-ami-tools

# Configure Chef
sudo mkdir /etc/chef
sudo mv /tmp/validation.pem /tmp/client.rb /etc/chef
sudo chown -R root:root /etc/chef
sudo chmod 700 /etc/chef
sudo chmod 600 /etc/chef/validation.pem /etc/chef/client.rb
