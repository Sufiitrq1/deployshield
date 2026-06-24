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
                echo "Injecting Minikube context directly into Windows System Profile..."
                // Yeh seedha us path par directory banayega jahan kubectl dhoond raha hai
                bat '''
                if not exist "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube" mkdir "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube"
                copy "C:\\Users\\DELL\\.kube\\config" "C:\\WINDOWS\\system32\\config\\systemprofile\\.kube\\config"
                '''
            }
        }

        stage('Apply K8s Manifest') {
            steps {
                echo "Applying manifest layout to cluster..."
                // Ab haan bina kisi flags ke normal command chalegi kyunki config sahi jagah pahonch gayi hai
                bat 'kubectl apply -f demo/app_good.yaml'
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