#!/bin/bash
#
# 02_via_firewall.sh
#
# Script to set iptables firewall rules for via and viahtml applications
# running on elastic beanstalk.
#
# Firewall Rules
# --------------
# The purpose of this script is to block via proxy users from being 
# able to enumerate sensitive information about our environment.
#
# We are:
# - Rejecting requests that attempt to access to either RFC1918 private
#   address space, or the aws metadata service.
# - Accepting requests specifically to and from the Docker containers
#   running the service, and DNS queries.
set -eu

# Grab the environment_name value
ENV_NAME="$(/opt/elasticbeanstalk/bin/get-config container -k environment_name || true)"
# Spilt on '-' and extract the second to last record
APP="$(echo $ENV_NAME | awk -F- '{print $(NF-1)}')"

if [[ $APP = 'via' ]] || [[ $APP = 'viahtml' ]] ; then
  echo "Creating via firewall rules"

  container_ip_one='172.17.0.2'
  container_ip_two='172.17.0.3'

  iptables --flush DOCKER-USER
  iptables --insert DOCKER-USER --jump REJECT
  iptables --insert DOCKER-USER --destination 10.0.0.0/8 --jump REJECT
  iptables --insert DOCKER-USER --destination 172.16.0.0/12 --jump REJECT
  iptables --insert DOCKER-USER --destination 192.168.0.0/16 --jump REJECT
  iptables --insert DOCKER-USER --protocol tcp --destination $container_ip_one --jump ACCEPT
  iptables --insert DOCKER-USER --protocol tcp --source $container_ip_one --jump ACCEPT
  iptables --insert DOCKER-USER --protocol tcp --destination $container_ip_two --jump ACCEPT
  iptables --insert DOCKER-USER --protocol tcp --source $container_ip_two --jump ACCEPT
  iptables --insert DOCKER-USER --protocol udp --destination-port 53 --jump ACCEPT
  iptables --insert DOCKER-USER --protocol udp --source-port 53 --jump ACCEPT
  iptables --insert DOCKER-USER --destination 169.254.169.254 --jump REJECT

  iptables-save > /etc/sysconfig/iptables
fi
