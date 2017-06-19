#!groovy

// The list of applications which can be deployed.
def deployApplications = ['bouncer', 'h-periodic', 'metabase', 'via'].join('\n')
// The list of deployment types.
def deployTypes = ['promote', 'exact-version', 'sync-env'].join('\n')
// The list of environments. It is assumed that each application has one of each
// of these environments.
def deployEnvironments = ['qa', 'prod'].join('\n')

def postSlack(state, params) {
    def messages = [
        'start': ['promote': "Starting to promote ${params.APP} to ${params.ENV}",
                  'exact-version': "Starting to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                  'sync-env': "Starting to synchronize the ${params.APP}-${params.ENV} environment"],
        'success': ['promote': "Successfully promoted ${params.APP} to ${params.ENV}",
                  'exact-version': "Successfully deployed ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                  'sync-env': "Successfully synchronized the ${params.APP}-${params.ENV} environment"],
        'error': ['promote': "Failed to promote ${params.APP} to ${params.ENV}",
                  'exact-version': "Failed to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                  'sync-env': "Failed to synchronize the ${params.APP}-${params.ENV} environment"]
    ]
    def colors = ['start': 'good', 'success': 'good', 'error': 'danger']
    slackSend color: colors[state], message: messages[state][params.TYPE]
}

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
                            '`sync-env` synchronizes the environment definition.')
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
        stage('setup') {
            steps {
                script {
                    def label = "#${currentBuild.number} ${params.APP} " +
                                "${params.ENV} ${params.TYPE}"
                    currentBuild.displayName = label
                }
                postSlack('start', params)
            }
        }

        stage('main') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-elasticbeanstalk-jenkins']]) {
                    sh 'bin/jenkins'
                }
            }
        }
    }

    post {
        failure { postSlack('error', params) }
        success { postSlack('success', params) }
    }
}
