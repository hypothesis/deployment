## iamsync.py

A script that generates and maintains local Linux user accounts using AWS IAM as a source of truth. Users added and removed from eligible IAM user groups will be able to login using SSH once a public ssh key has been added to their AWS account.

#### Parameters

**--config**

Path to configuration file.

**--log**

Path to log file.

**--verbose**

Increase output level.

#### Requirements

- Python3.6 or greater
- Boto3
- PyYaml

### Configuration

`iamsync.py` by default reads configuration from `iam.yml`. Here is an example entry:

```
iamsync:
  - iam_group: <group_name>
    sudo_rule: <sudo_rule>
    local_gid: <group_id>
```

A number of `iam_group` blocks with separate `sudo_rule` and `local_gid` entries can be defined to provide a granular access solution.

#### Configuration file format

**iamsync**

The key identifier for iamsync config in the iam.yml configuration file. Required. Do not change.

**iam_group**

The IAM user group you would like to sync with the local Linux server. A Linux user group with the same name as the IAM user group will be created.

**sudo_rule**

Sudo rule that defines the level of privilege give to `iam_group`.

**local_gid**

The Linux group identifier applied to the local Linux group to be created.

#### Configuration example

The example defines a solution were two groups `support` and `engineering` have been given access with slightly different privileges. Users in the `support` group have the ability to run `/bin/su - postgres` to inherit the `postgres` user account. Users in the `engineering` group have the ability to run `all` commands. Essentially providing `engineering` users will `root` level access.

```
iamsync:
  - iam_group: support
    sudo_rule: "ALL= NOPASSWD: /bin/su - postgres"
    local_gid: 1024
  - iam_group: engineering
    sudo_rule: "ALL=(ALL) NOPASSWD:ALL"
    local_gid: 1025
```
