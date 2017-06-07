#!groovy

// The list of applications which can be deployed.
def deployApplications = ['bouncer', 'via'].join('\n')
// The list of deployment types.
def deployTypes = ['promote', 'exact-version', 'sync-env'].join('\n')
// The list of environments. It is assumed that each application has one of each
// of these environments.
def deployEnvironments = ['qa', 'prod'].join('\n')

pipeline {
    agent { dockerfile true }

    parameters {
        choice(name: 'APP',
               choices: deployApplications,
               description: 'Choose the application to deploy.')
        choice(name: 'TYPE',
               choices: deployTypes,
               description: 'Choose the deployment type. ' +
                            '`promote` promotes the last successful QA deployment to prod. ' +
                            '`exact-version` pushes a specific docker tag. ' +
                            '`sync-env` synchronizes the environment definition.',
                defaultValue: 'promote')
        string(name: 'APP_DOCKER_VERSION',
               description: 'The tag of the application docker image to ' +
                            'deploy. This is required if the selected ' +
                            'deployment type is `exact-version`.',
               defaultValue: '')
        choice(name: 'ENV',
               choices: deployEnvironments,
               description: 'Choose the application to deploy.')
    }

    environment {
        AWS_DEFAULT_REGION = 'us-west-1'
    }

    stages {
        stage('main') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-elasticbeanstalk-jenkins']]) {
                    sh 'bin/jenkins'
                }
            }
        }
    }
}
