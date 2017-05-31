#!groovy

// The list of applications which can be deployed.
def deployApplications = ['bouncer'].join('\n')
// The list of environments. It is assumed that each application has one of each
// of these environments.
def deployEnvironments = ['qa', 'prod'].join('\n')

pipeline {
    agent { dockerfile true }

    parameters {
        choice(name: 'APP',
               choices: deployApplications,
               description: 'Choose the application to deploy.')
        string(name: 'APP_DOCKER_VERSION',
               description: 'The tag of the application docker image to ' +
                            'deploy. If you do not supply a tag, the ' +
                            'environment configuration will be synchronised ' +
                            'instead. (This can only happen if the ' +
                            'environment has already been created.)',
               defaultValue: '')
        choice(name: 'ENV',
               choices: deployEnvironments,
               description: 'Choose the application to deploy.')
    }

    stages {
        stage('run') {
            steps {
                sh 'echo hello world'
            }
        }
    }
}
