#!groovy

// The list of applications which can be deployed.
def deployApplications = ['analytics-dashboard', 'bouncer', 'checkmate', 'h', 'h-ca', 'h-periodic', 'h-periodic-ca', 'h-websocket', 'lms', 'lms-ca', 'lms-via', 'lms-viahtml', 'metabase', 'via', 'viahtml'].join('\n')
// The list of deployment types.
def deployTypes = ['deploy', 'redeploy', 'sync-env'].join('\n')
// The list of environments. It is assumed that each application has one of each
// of these environments.
def deployEnvironments = ['qa', 'prod'].join('\n')
// The list of supported regions. Defaults to us-west-1.
def deployRegions = ['us-west-1', 'ca-central-1'].join('\n')

def postSlack(state, params) {
    def messages = [
        'start': ['deploy': "Starting to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV} (${params.REGION})",
                  'redeploy': "Starting re-deployment of ${params.APP} in ${params.ENV} (${params.REGION})",
                  'sync-env': "Starting to synchronize the ${params.APP}-${params.ENV} environment (${params.REGION})"],
        'success': ['deploy': "Successfully deployed ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV} (${params.REGION})",
                    'redeploy': "Successfully re-deployed ${params.APP} in ${params.ENV} (${params.REGION})",
                    'sync-env': "Successfully synchronized the ${params.APP}-${params.ENV} environment (${params.REGION})"],
        'error': ['deploy': "Failed to deploy ${params.APP} ${params.APP_DOCKER_VERSION} to ${params.ENV} (${params.REGION})",
                  'redeploy': "Failed to re-deploy ${params.APP} in ${params.ENV} (${params.REGION})",
                  'sync-env': "Failed to synchronize the ${params.APP}-${params.ENV} environment (${params.REGION})"]
    ]
    def colors = ['start': 'good', 'success': 'good', 'error': 'danger']
    slackSend color: colors[state], message: messages[state][params.TYPE]

    // allow a single additional channel per repo as a target for the message
    def additionalChannels = ['lms': '#feat-canvas']
    if (additionalChannels.containsKey(params.APP)) {
        slackSend channel: "${additionalChannels[params.APP]}", color: colors[state], message: messages[state][params.TYPE]
    }
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
        choice(name: 'REGION',
               choices: deployRegions,
               description: 'Choose the region to deploy. Defaults to us-west-1')
        choice(name: 'ENV',
               choices: deployEnvironments,
               description: 'Choose the application to deploy.')
    }

    environment {
        AWS_DEFAULT_REGION = "${params.REGION}"
    }

    stages {
        stage('main') {
            steps {
                script {
                    def label = "#${currentBuild.number} ${params.APP} " +
                                "${params.ENV} ${params.TYPE}"
                    currentBuild.displayName = label
                }

                // Before we start the deployment proper, we grab a named lock
                // which ensures that only one deployment job can be acting on a
                // specific environment at one time.
                //
                // That is, deployments for different apps can proceed in
                // parallel, as can deployments to different environments for
                // the same app, but deployments to the same app and environment
                // must execute serially.
                lock(resource: "${params.APP}-${params.ENV}-deploy") {
                    postSlack('start', params)
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                      credentialsId: 'aws-elasticbeanstalk-jenkins']]) {
                        sh 'bin/jenkins'
                    }
                }
            }
        }
    }

    post {
        failure { postSlack('error', params) }
        success { postSlack('success', params) }
    }
}
