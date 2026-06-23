pipeline {
    agent any

    environment {
        // Configured to point to your active DeployShield instance on port 5000
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
                // Switch this to demo/app_broken.yaml later to test the automated rollback path
                sh 'kubectl apply -f demo/app_good.yaml'
            }
        }

        stage('DeployShield Guard') {
            steps {
                echo "Registering deployment track with DeployShield gateway on port 5000..."
                script {
                    def jsonPayload = """{
                        "namespace": "${env.NAMESPACE}",
                        "deployment_name": "${env.DEPLOYMENT_NAME}",
                        "image_tag": "latest",
                        "smoke_test_url": "${env.SMOKE_TEST_URL}",
                        "phone_number": "${env.ALERT_PHONE}"
                    }"""

                    // Dispatches the background tracking worker thread asynchronously
                    def response = sh(
                        script: """
                            curl -s -X POST ${env.DEPLOY_SHIELD_URL} \
                            -H "Content-Type: application/json" \
                            -d '${jsonPayload}'
                        """,
                        returnStdout: true
                    ).trim()
                    
                    echo "DeployShield Gateway Response: ${response}"
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline passed successfully. DeployShield is auditing rollout stability asynchronously."
        }
    }
}