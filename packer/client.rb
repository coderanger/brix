log_level :auto
log_location STDOUT
chef_server_url 'https://confucius.balancedpayments.com'
validation_client_name 'chef-validator'
ssl_verify_mode :verify_peer
verify_api_cert true
ssl_ca_file '/etc/chef/cacert.pem'
