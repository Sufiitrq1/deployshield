pipeline {
    agent any

    environment {
        // Port 5000 ko badal kar 5001 kar diya hai
        DEPLOY_SHIELD_URL = 'http://127.0.0.1:5001/v1/deploy/watch'
        DEPLOYMENT_NAME   = 'demo-app'
        NAMESPACE         = 'default'
        SMOKE_TEST_URL    = 'https://claude.ai/upgrade3'
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
                echo "Injecting Minikube context directly into Windows System Profile..."
                bat '''
                if not exist "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube" mkdir "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube"
                copy "C:\\Users\\DELL\\.kube\\config" "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube\\config"
                '''
            }
        }

        stage('Apply K8s Manifest') {
            steps {
                echo "Applying manifest layout to cluster with strict network bypass..."
                bat 'kubectl apply -f demo/app_good.yaml --validate=false --insecure-skip-tls-verify=true'
            }
        }

        stage('DeployShield Guard') {
            steps {
                echo "Pinging DeployShield gateway on port 5001..."
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