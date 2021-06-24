"""
iamsync.py
Generates and maintains local Linux user accounts using AWS IAM as a source of
truth. Users added and removed from eligible IAM usergroups will be able to
login using SSH once a public ssh key has been added to their AWS account.
"""

import argparse
import grp
import logging
import logging.handlers
import os
import pwd
import subprocess
import sys
from pathlib import Path

import boto3
import yaml

parser = argparse.ArgumentParser(
    description="Sync IAM group users and SSH keys to local Linux accounts"
)
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default="iam.yml",
    required=False,
    help="Path to configuration file",
)
parser.add_argument(
    "-l",
    "--log",
    type=str,
    default="/var/log/iamsync.log",
    required=False,
    help="Path to log file",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase output level",
)
args = parser.parse_args()

log_lev = logging.INFO
log_fmt = "%(asctime)s : %(levelname)s - %(message)s"
log_hdl = [logging.FileHandler(args.log)]
if args.verbose > 0:
    log_hdl = [logging.FileHandler(args.log), logging.StreamHandler()]
logging.basicConfig(level=log_lev, format=log_fmt, handlers=log_hdl)

DEV_NULL = open(os.devnull, "w")
authorized_iam_accounts = []


def read_config():
    config = args.config
    local_config = None
    try:
        with open(config) as config_file:
            local_config = yaml.safe_load(config_file)
            if args.verbose > 0:
                logging.info(f"loaded configuration ({config})")
            return local_config["iamsync"]
    except Exception as e:
        raise Exception("read_config failed") from e


def iam_test():
    try:
        client = boto3.client("iam")
        response = client.list_groups()
        return True
    except Exception as e:
        logging.error(f"iam_test failed {e}")
        orphan_account_cleanup()
        raise SystemExit(99)


def iam_user_query(group):
    try:
        iam_info_list = []
        remote_users = []
        client = boto3.client("iam")
        response = client.get_group(GroupName=group)
        for i in range(len(response["Users"])):
            username = response["Users"][i]["UserName"]
            remote_users.append(username)
        if args.verbose > 0:
            logging.info(f"iam group available ({group})")
            logging.info(f"iam group users ({remote_users})")
        if remote_users is not None:
            for username in remote_users:
                sshpublickeyid = iam_ssh_key_id_query(client, username)
                if sshpublickeyid is not None:
                    sshpublickeybody = iam_ssh_public_key_query(
                        client, username, sshpublickeyid
                    )
                    iam_info_list.append(
                        {
                            "username": username,
                            "sshpublickeyid": sshpublickeyid,
                            "sshpublickeybody": sshpublickeybody,
                        }
                    )
        return iam_info_list
    except client.exceptions.NoSuchEntityException:
        logging.error(f"iam group '{group}' defined in {args.config} is not available")
    except Exception as e:
        raise Exception("iam_user_query failed") from e


def iam_ssh_key_id_query(client, username):
    try:
        response = client.list_ssh_public_keys(UserName=username)
        sshpublickeyid = response["SSHPublicKeys"][0]["SSHPublicKeyId"]
        return sshpublickeyid
    except IndexError:
        if args.verbose > 0:
            logging.info(f"iam group user without a valid public ssh key ({username})")
    except Exception as e:
        raise Exception("iam_ssh_key_id_query failed") from e


def iam_ssh_public_key_query(client, username, sshpublickeyid):
    try:
        response = client.get_ssh_public_key(
            UserName=username, SSHPublicKeyId=sshpublickeyid, Encoding="SSH"
        )
        sshpublickeybody = response["SSHPublicKey"]["SSHPublicKeyBody"]
        return sshpublickeybody
    except Exception as e:
        raise Exception("iam_ssh_public_key_query failed") from e


def linux_group_validate(group, gid):
    try:
        linux_group_details = grp.getgrnam(group)
        linux_gid = linux_group_details[2]
        if not linux_gid == gid:
            raise ValueError("gid incorrect")
        if args.verbose > 0:
            logging.info(f"linux group validated ({group}:{gid})")
        return True
    except KeyError:
        linux_group_create(group, gid)
    except ValueError as v:
        logging.error(f"linux group validation failed ({v})")
        linux_group_delete(group)
        linux_group_create(group, gid)
    except Exception as e:
        raise Exception("linux_group_validate failed") from e


def linux_group_create(group, gid):
    try:
        subprocess.check_call(["groupadd", "--gid", str(gid), group])
        logging.info(f"linux group created ({group}:{gid})")
    except Exception as e:
        raise Exception("linux_group_create failed") from e


def linux_group_delete(group):
    try:
        subprocess.check_call(["groupdel", group])
        logging.info(f"linux group deleted ({group})")
        return True
    except Exception as e:
        logging.error(
            f"linux group configuration is invalid. "
            f"tip: check users outside of iamsync are not using ("
            f"{group}) as their primary group"
        )
        raise Exception("linux_group_delete failed") from e


def sudo_rule_validate(sudo_rule, group):
    try:
        sudo_file = "/etc/sudoers.d/" + group
        on_disk = open(sudo_file, "r").read().split()
        if len(on_disk) == 0:
            raise IndexError("empty file")
        if not on_disk[0] == "%" + group:
            raise ValueError("group error")
        if not len(on_disk) == len(sudo_rule.split()) + 1:
            raise ValueError("parameter error")
        if args.verbose > 0:
            logging.info(f"sudo rule validated ({sudo_file})")
        return True
    except (IndexError, IOError, ValueError) as e:
        logging.error(f"sudo rule validation failed ({e}:{sudo_file})")
        sudo_rule_create(group, sudo_rule, sudo_file)
    except Exception as e:
        raise Exception("sudo_rule_validate failed") from e


def sudo_rule_create(group, sudo_rule, sudo_file):
    newline = "\n"
    try:
        with open(sudo_file, "w+") as file:
            file.write(f"%{group} {sudo_rule}{newline}")
            logging.info(f"sudo rule create ({sudo_file}:{sudo_rule})")
    except Exception as e:
        raise Exception(f"sudo_rule_validate {e}")


def linux_user_validate(user_info_list, group):
    for user in user_info_list:
        username = user["username"]
        sshpublickeyid = user["sshpublickeyid"]
        sshpublickeybody = user["sshpublickeybody"]
        homedir = f"/home/{username}"
        authorized_iam_accounts.append(username)
        try:
            check = pwd.getpwnam(username)
            linux_user_primary_gid = check[3]
            linux_user_homedir = check[5]
            if not linux_user_homedir == homedir:
                raise ValueError("incorrect homedir")
            linux_user_primary_gid_validate(linux_user_primary_gid, group)
            if args.verbose > 0:
                logging.info(
                    f"linux user validated "
                    f"({username}:{group}:{linux_user_primary_gid}:{homedir})"
                )
        except KeyError:
            linux_user_create(username, group, homedir)
        except ValueError as v:
            logging.error(f"linux user validation failed ({v}:{username})")
            linux_user_delete(username)
            linux_user_create(username, group, homedir)
        except Exception as e:
            raise Exception("linux_user_validate failed") from e
        auth_ssh_key_validate(username, sshpublickeybody, sshpublickeyid)


def linux_user_primary_gid_validate(linux_user_primary_gid, group):
    try:
        linux_group_gid = grp.getgrnam(group)[2]
        if not linux_user_primary_gid == linux_group_gid:
            raise Exception()
    except Exception:
        raise ValueError("incorrect primary group")


def linux_user_create(username, group, homedir):
    try:
        subprocess.check_call(
            [
                "useradd",
                "-s",
                "/bin/bash",
                "-c",
                "iamsync",
                "-md",
                homedir,
                "-g",
                group,
                username,
            ],
            stdout=DEV_NULL,
            stderr=subprocess.STDOUT,
        )
        logging.info(f"linux user created ({username}':{group}:{homedir})")
        return True
    except Exception as e:
        raise Exception("linux_user_create failed") from e


def linux_user_delete(username):
    try:
        subprocess.check_call(
            ["deluser", username], stdout=DEV_NULL, stderr=subprocess.STDOUT
        )
        logging.info(f"linux user deleted ({username})")
        return True
    except Exception as e:
        raise Exception("linux_user_delete failed") from e


def auth_ssh_key_validate(username, sshpublickeybody, sshpublickeyid):
    try:
        homedir = f"/home/{username}"
        key_file = homedir + "/.ssh/authorized_keys"
        on_disk = open(key_file, "r").read().split()
        if len(on_disk) == 0:
            raise ValueError("empty file")
        if not sshpublickeybody == on_disk[0] + " " + on_disk[1]:
            raise ValueError("incorrect sshpublickeybody")
        if not sshpublickeyid == on_disk[2]:
            raise ValueError("incorrect sshpublickeyid")
        if args.verbose > 0:
            logging.info(f"auth ssh key file validated ({key_file})")
        return True
    except IOError:
        auth_ssh_key_dir_create(homedir)
        auth_ssh_key_file_create(key_file, sshpublickeybody, sshpublickeyid)
        auth_ssh_key_perms_set(username, key_file)
    except ValueError as v:
        logging.error(f"auth ssh file validation failed ({v})")
        auth_ssh_key_file_create(key_file, sshpublickeybody, sshpublickeyid)
        auth_ssh_key_perms_set(username, key_file)
    except Exception as e:
        raise Exception("auth_ssh_key_validate failed") from e


def auth_ssh_key_dir_create(homedir):
    ssh_dir = homedir + "/.ssh"
    if Path(ssh_dir).exists():
        return True
    try:
        os.mkdir(ssh_dir)
        logging.info(f"auth ssh key dir created ({ssh_dir})")
    except Exception as e:
        raise Exception("auth_ssh_key_dir_create failed") from e


def auth_ssh_key_file_create(key_file, sshpublickeybody, sshpublickeyid):
    try:
        with open(key_file, "w+") as file:
            file.write(f"{sshpublickeybody} {sshpublickeyid}")
            logging.info(f"public ssh key created ({key_file})")
    except Exception as e:
        raise Exception("auth_ssh_key_file_create failed") from e


def auth_ssh_key_perms_set(username, key_file):
    try:
        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid
        os.chmod(key_file, 0o600)
        os.chown(key_file, uid, uid)
        logging.info(f"public ssh key perms ({key_file}:600)")
    except Exception as e:
        raise Exception("auth_ssh_key_perms_set failed") from e


def orphan_account_cleanup():
    local_iamsync_users = []
    try:
        local_users = pwd.getpwall()
        for i in local_users:
            if pwd.getpwnam(i.pw_name).pw_gecos == "iamsync":
                local_iamsync_users.append(i.pw_name)
        for username in local_iamsync_users:
            if username not in authorized_iam_accounts:
                logging.info(f"orphan account identified ({username})")
                linux_user_delete(username)
    except Exception as e:
        raise Exception("orphan_account_cleanup failed") from e


if __name__ == "__main__":
    try:
        logging.info("Starting iamsync")
        iam_test()
        config_list = read_config()
        for config in config_list:
            group = config["iam_group"]
            gid = config["local_gid"]
            sudo_rule = config["sudo_rule"]
            iam_user_info = iam_user_query(group)
            if iam_user_info is not None:
                linux_group_validate(group, gid)
                sudo_rule_validate(sudo_rule, group)
                linux_user_validate(iam_user_info, group)
        orphan_account_cleanup()
        logging.info("Completed iamsync")
    except Exception as e:
        logging.error(f"__main__  {e}")
        raise SystemExit(1)
