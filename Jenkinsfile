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

        stage('Sync Cluster Config') {
            steps {
                echo "Injecting valid Minikube authentication context..."
                // Local config directory create karke user config copy kar rahe hain
                bat '''
                if not exist ".kube" mkdir .kube
                copy "C:\\Users\\DELL\\.kube\\config" ".kube\\config"
                '''
            }
        }

        stage('Apply K8s Manifest') {
            environment {
                KUBECONFIG = "${WORKSPACE}\\.kube\\config"
            }
            steps {
                echo "Applying manifest layout to cluster using active context..."
                bat 'kubectl --context=minikube apply -f demo/app_good.yaml'
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