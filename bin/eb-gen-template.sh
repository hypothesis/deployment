#!/bin/bash
#
# Generates valid Elastic Beanstalk environment definition YAML

set -eu

json_config="${1:-us-west-1_regional_values.json}"
env=${2:-prod}

if [ ! -f $json_config ] ; then
  echo "Can not find $json_config"
  exit 1
fi

missing_var_message="Could not find value for:"

if ! PlatformArn=$(jq -er .PlatformArn $json_config) ; then
  echo "$missing_var_message PlatformArn"
  exit 2
fi

if ! Subnets=$(jq -er .Subnets $json_config) ; then
  echo "$missing_var_message Subnets"
  exit 2
fi

if ! VPCId=$(jq -er .VPCId $json_config) ; then
  echo "$missing_var_message VPCId"
  exit 2
fi

if ! ELBSubnets=$(jq -er .ELBSubnets $json_config) ; then
  echo "$missing_var_message ELBSubnets"
  exit 2
fi

if ! SSLCertificateArns=$(jq -er .SSLCertificateArns $json_config) ; then
  echo "$missing_var_message SSLCertificateArns"
  exit 2
fi

if ! SecurityGroups=$(jq -er .SecurityGroups $json_config) ; then
  echo "$missing_var_message SecurityGroups"
  exit 2
fi

if ! InstanceType=$(jq -er .InstanceType $json_config) ; then
  echo "$missing_var_message InstanceType"
  exit 2
fi

if ! MaxSize=$(jq -er .MaxSize $json_config) ; then
  echo "$missing_var_message MaxSize"
  exit 2
fi

if ! MinSize=$(jq -er .MinSize $json_config) ; then
  echo "$missing_var_message MinSize"
  exit 2
fi

if [ $env = 'prod' ] ; then 
cat << PROD_CONFIG
AWSConfigurationTemplateVersion: 1.1.0.0
Platform:
  PlatformArn: $PlatformArn
EnvironmentTier:
  Type: Standard
  Name: WebServer
OptionSettings:
  aws:elasticbeanstalk:cloudwatch:logs:
    StreamLogs: true
    RetentionInDays: "7"
  aws:elasticbeanstalk:command:
    DeploymentPolicy: RollingWithAdditionalBatch
    BatchSizeType: Percentage
    BatchSize: '100'
  aws:elasticbeanstalk:environment:
    EnvironmentType: LoadBalanced
    LoadBalancerType: application
    ServiceRole: aws-elasticbeanstalk-service-role
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /_status
  aws:elasticbeanstalk:healthreporting:system:
    SystemType: enhanced
  aws:ec2:vpc:
    Subnets: $Subnets
    VPCId: $VPCId
    ELBSubnets: $ELBSubnets
    ELBScheme: public
    AssociatePublicIpAddress: true
  aws:autoscaling:updatepolicy:rollingupdate:
    RollingUpdateType: Immutable
    RollingUpdateEnabled: true
  aws:elbv2:listener:default:
    ListenerEnabled: false
  aws:elbv2:listener:443:
    ListenerEnabled: true
    SSLPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
    SSLCertificateArns: $SSLCertificateArns
    DefaultProcess: default
    Protocol: HTTPS
  aws:autoscaling:launchconfiguration:
    SecurityGroups: $SecurityGroups
    IamInstanceProfile: aws-elasticbeanstalk-ec2-role
    InstanceType: $InstanceType
    EC2KeyName: ops-20191105
  aws:autoscaling:asg:
    MaxSize: $MaxSize
    MinSize: $MinSize
  AWSEBCloudwatchAlarmHigh.aws:autoscaling:trigger:
    UpperThreshold: '15000000'
  AWSEBCloudwatchAlarmLow.aws:autoscaling:trigger:
    BreachDuration: '5'
    EvaluationPeriods: '2'
    Period: '5'
    LowerThreshold: '7000000'
    MeasureName: NetworkOut
    Statistic: Average
    Unit: Bytes
PROD_CONFIG



fi

if [ $env = 'qa' ] ; then
  echo qa_config
fi
