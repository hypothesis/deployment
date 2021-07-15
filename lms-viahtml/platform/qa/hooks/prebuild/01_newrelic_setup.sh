#!/bin/bash
#
# 01_newrelic_setup.sh
#
# Script to setup and configure the newrelic infra agent for use with
# Elastic Beanstalk.
#
set -eu

key=$(/opt/elasticbeanstalk/bin/get-config environment -k NEW_RELIC_LICENSE_KEY)
display_name=$(/opt/elasticbeanstalk/bin/get-config environment -k NEW_RELIC_APP_NAME)

function create_config() {
cat << CONFIG > /etc/newrelic-infra.yml2
license_key: $key
display_name: $display_name
enable_process_metrics: false
CONFIG
}

if [ -z "$key" ] ; then
  echo "NEW_RELIC_LICENSE_KEY is empty"
  echo "Can not continue with NewRelic configuration - Set license key"
  exit 0
fi

if [ -z "$display_name" ] ; then
  echo "NEW_RELIC_APP_NAME is empty"
  echo "Can not continue with NewRelic configuration - Set app name"
  exit 0
else
  create_config
  curl -o /etc/yum.repos.d/newrelic-infra.repo https://download.newrelic.com/infrastructure_agent/linux/yum/el/7/x86_64/newrelic-infra.repo
  yum -q makecache -y --disablerepo='*' --enablerepo='newrelic-infra'
  yum install newrelic-infra -y 
fi
