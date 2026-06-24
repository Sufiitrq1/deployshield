pipeline {
    agent any

    environment {
        DEPLOY_SHIELD_URL = 'http://127.0.0.1:5001/v1/deploy/watch'
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
                echo "Pinging DeployShield gateway on port 5001 via Native HTTP..."
                script {
                    // Sahi JSON payload bina kisi escape ya formatting issue ke
                    def jsonPayload = """{
                        "namespace": "${env.NAMESPACE}",
                        "deployment_name": "${env.DEPLOYMENT_NAME}",
                        "image_tag": "latest",
                        "smoke_test_url": "${env.SMOKE_TEST_URL}",
                        "phone_number": "${env.ALERT_PHONE}"
                    }"""

                    // Groovy Native HTTP Request (Windows curl bypass)
                    def url = new URL(env.DEPLOY_SHIELD_URL)
                    def connection = (HttpURLConnection) url.openConnection()
                    connection.setRequestMethod("POST")
                    connection.setRequestProperty("Content-Type", "application/json; utf-8")
                    connection.setDoOutput(true)

                    connection.getOutputStream().withWriter("UTF-8") { writer ->
                        writer.write(jsonPayload)
                    }

                    def responseCode = connection.getResponseCode()
                    echo "DeployShield Response Code: ${responseCode}"
                    
                    if (responseCode >= 200 && responseCode < 300) {
                        echo "Success: Gateway accepted the tracking payload."
                    } else {
                        def responseText = connection.getErrorStream()?.text ?: connection.getInputStream().text
                        echo "Error Response: ${responseText}"
                        error("DeployShield rejected the request with status ${responseCode}")
                    }
                }
            }
        }