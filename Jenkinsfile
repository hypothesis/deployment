#!groovy

// The list of applications which can be deployed.
def deployApplications = ['bouncer', 'h', 'h-periodic', 'metabase', 'via'].join('\n')
// The list of deployment types.
def deployTypes = ['deploy', 'redeploy', 'sync-env'].join('\n')
// The list of environments. It is assumed that each application has one of each
// of these environments.
def deployEnvironments = ['qa', 'prod'].join('\n')

def postSlack(state, params) {
    def messages = [
        'start': ['deploy': "Starting to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                  'redeploy': "Starting re-deployment of ${params.APP} in ${params.ENV}",
                  'sync-env': "Starting to synchronize the ${params.APP}-${params.ENV} environment"],
        'success': ['deploy': "Successfully deployed ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                    'redeploy': "Successfully re-deployed ${params.APP} in ${params.ENV}",
                    'sync-env': "Successfully synchronized the ${params.APP}-${params.ENV} environment"],
        'error': ['deploy': "Failed to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV}",
                  'redeploy': "Failed to re-deploy ${params.APP} in ${params.ENV}",
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
                            '`deploy` releases and deploys a specific application version. ' +
                            '`redeploy` triggers a redeployment of the currently-deployed version. ' +
                            '`sync-env` synchronizes the environment definition.')
        string(name: 'APP_DOCKER_VERSION',
               description: 'The tag of the application docker image to ' +
                            'deploy. This is required if the selected ' +
                            'deployment type is `deploy`.',
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
