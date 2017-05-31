#!groovy

pipeline {
    agent { dockerfile true }
    stages {
        stage('run') {
            steps {
                sh 'echo hello world'
            }
        }
    }
}
