pipeline {
    agent any

    environment {
        DEPLOY_SHIELD_URL = 'http://127.0.0.1:5000/v1/deploy/watch'
        DEPLOYMENT_NAME   = 'demo-app'
        NAMESPACE         = 'default'
        SMOKE_TEST_URL    = 'http://localhost:8080/'
        ALERT_PHONE       = '+923328848628'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Apply K8s Manifest') {
            steps {
                echo "Applying manifest layout to cluster..."
                // Validation bypass aur direct minikube port address map kiya
                bat 'kubectl apply -f demo/app_good.yaml --server=https://127.0.0.1:53217 --validate=false --insecure-skip-tls-verify=true'
            }
        }

        stage('DeployShield Guard') {
            steps {
                echo "Pinging DeployShield gateway on port 5000..."
                script {
                    def jsonPayload = """{
                        "namespace": "${env.NAMESPACE}",
                        "deployment_name": "${env.DEPLOYMENT_NAME}",
                        "image_tag": "latest",
                        "smoke_test_url": "${env.SMOKE_TEST_URL}",
                        "phone_number": "${env.ALERT_PHONE}"
                    }"""

                    bat "curl -s -X POST ${env.DEPLOY_SHIELD_URL} -H \"Content-Type: application/json\" -d \"${jsonPayload.replaceAll('\n', '').replaceAll('"', '\\\"')}\""
                }
            }
        }
    }
}