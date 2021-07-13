#!/bin/bash
#
# 01_iamsync_setup.sh
#
# Setup and configure iamsync for use with Elastic Beanstalk.
set -eu

cat <<CRON > /etc/cron.d/iamsync
SHELL=/bin/bash
PATH="venv/bin:/usr/sbin:/bin"
5,35 * * * * root sleep \${RANDOM: -1} ; python bin/iamsync.py
CRON

cat <<CONFIG > /etc/iamsync.yml
iamsync:
  - iam_group: engineering
    sudo_rule: "ALL=(ALL) NOPASSWD:ALL"
    local_gid: 1025
CONFIG

mkdir -p /root/bin
curl https://raw.githubusercontent.com/hypothesis/iamsync/main/iamsync.py -o /root/bin/iamsync.py

python3 -m venv /root/venv
source /root/venv/bin/activate ; pip install wheel boto3 pyyaml

/root/venv/bin/python /root/bin/iamsync.py
