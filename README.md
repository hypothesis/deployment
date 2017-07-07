Deployment tools and configuration
==================================

This repository contains scripts and configuration templates for deployment of
Hypothesis applications to AWS Elastic Beanstalk (EB).

The repository is designed to act as the SCM source for a Jenkins job which is
responsible for:

- deploying our applications to a named environment (`qa` or `prod`)
- applying updates to the environment configuration

As such, the main entrypoint for the repository is the
[`Jenkinsfile`](Jenkinsfile), which defines how the Jenkins job runs.

The script which orchestrates the deployments is [`bin/jenkins`](bin/jenkins),
which in turn calls a number of other helper scripts which live in the `bin/`
directory:

| Name                                               | Description                                                                                                |
|----------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`eb-deploy`](bin/eb-deploy)                       | Triggers a deployment of a specific application version to a specific environment in EB.                   |
| [`eb-env-create`](bin/eb-env-create)               | Create an EB environment from scratch based on a YAML configuration file.                                  |
| [`eb-env-exists`](bin/eb-env-exists)               | Check if an EB environment exists.                                                                         |
| [`eb-env-sync`](bin/eb-env-sync)                   | Trigger an environment update to synchronise configuration with the YAML configuration file.               |
| [`eb-env-version`](bin/eb-env-version)             | Report the deployed application version label in a specific environment.                                   |
| [`eb-env-wait`](bin/eb-env-wait)                   | Wait for an EB environment to return to the `Ready` state while tailing the event log.                     |
| [`eb-manifest-platform`](bin/eb-manifest-platform) | Extract the the "Platform ARN" from a YAML environment configuration file.                                 |
| [`eb-manifest-settings`](bin/eb-manifest-settings) | Extract "option settings" from a YAML environment configuration file in a format suitable for the AWS CLI. |
| [`eb-release`](bin/eb-release)                     | Create a new application version in Elastic Beanstalk based on a specific Docker tag.                      |
| [`eb-task-run`](bin/eb-task-run)                   | Run a command inside the Docker container of a running EB instance and tail the output.                    |
| [`eb-task-wait`](bin/eb-task-wait)                 | Wait for an AWS SSM Run Command invocation to finish and print the log output.                             |

Some of these scripts rely on application-specific configuration files which
live in a directory with the same name as the application. For example, the EB
environments for the `bouncer` application are defined in
[`bouncer/env-qa.yml`](bouncer/env-qa.yml) and
[`bouncer/env-prod.yml`](bouncer/env-prod.yml)

License
-------

All code contained in this repository is released under the [2-Clause BSD
License](http://www.opensource.org/licenses/BSD-2-Clause), sometimes referred to
as the "Simplified BSD License" or the "FreeBSD License". A copy of the license
text can be found in the included [`LICENSE`](LICENSE) file.
