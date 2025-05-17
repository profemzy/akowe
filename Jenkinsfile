pipeline {
    agent any
    
    tools {
        git 'Git'
    }
    
    environment {
        // Application Information
        APP_NAME = 'akowe'
        PROJECT_NAME = 'akowe'
        CI = 'true'
        
        // Container Registry Information
        STAGING_REGISTRY = 'stagingacr4yyprq.azurecr.io'
        PROD_REGISTRY = 'prodacrva1ng1.azurecr.io'
        
        // Azure Cluster Information
        STAGING_CLUSTER_NAME = 'staging-aks'
        STAGING_RESOURCE_GROUP = 'staging-aks-rg'
        PROD_CLUSTER_NAME = 'prod-aks'
        PROD_RESOURCE_GROUP = 'wackops-prod'
        
        // Namespace
        NAMESPACE = 'akowe'
        
        // App Version
        APP_VERSION = sh(script: 'git describe --tags --always || echo v1.0.0', returnStdout: true).trim()
    }
    
    options {
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    triggers {
        githubPush()
    }
    
    parameters {
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Skip running tests')
        booleanParam(name: 'DEPLOY_TO_PRODUCTION', defaultValue: false, description: 'Deploy to production (requires manual approval)')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Run Tests') {
            when {
                expression { return !params.SKIP_TESTS }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    export CI=true
                    pytest tests/ -v
                '''
            }
            post {
                always {
                    junit(testResults: '**/junit.xml', allowEmptyResults: true)
                }
            }
        }
        
        stage('Static Code Analysis') {
            steps {
                sh '''
                    . venv/bin/activate
                    flake8 .
                    mypy akowe
                '''
            }
        }
        
        stage('Build & Push Docker Image - Staging') {
            when {
                branch 'develop'
            }
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'acr-credentials',
                                     passwordVariable: 'ACR_PASSWORD',
                                     usernameVariable: 'ACR_USERNAME')
                ]) {
                    sh """
                        echo \${ACR_PASSWORD} | docker login ${STAGING_REGISTRY} -u \${ACR_USERNAME} --password-stdin
                        docker build -t ${STAGING_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER} -t ${STAGING_REGISTRY}/${APP_NAME}:latest .
                        docker push ${STAGING_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER}
                        docker push ${STAGING_REGISTRY}/${APP_NAME}:latest
                        docker logout ${STAGING_REGISTRY}
                    """
                }
                script {
                    env.STAGING_IMAGE_TAG = env.BUILD_NUMBER
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'azure-credentials',
                                     passwordVariable: 'AZURE_SP_PASSWORD',
                                     usernameVariable: 'AZURE_SP_ID'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID')
                ]) {
                    sh """
                        az login --service-principal \\
                            --username "\${AZURE_SP_ID}" \\
                            --password="\${AZURE_SP_PASSWORD}" \\
                            --tenant "\${AZURE_TENANT_ID}"

                        az aks get-credentials --resource-group ${STAGING_RESOURCE_GROUP} --name ${STAGING_CLUSTER_NAME} --overwrite-existing

                        kubectl get namespace ${NAMESPACE} || kubectl create namespace ${NAMESPACE}
                        
                        sed -i 's|image: stagingacr4yyprq.azurecr.io/akowe:latest|image: stagingacr4yyprq.azurecr.io/akowe:${env.STAGING_IMAGE_TAG}|g' k8s/overlays/staging/patch-deployment.yaml
                        
                        kubectl apply -k k8s/overlays/staging/
                        
                        kubectl rollout status deployment/akowe -n ${NAMESPACE} --timeout=300s
                    """
                }
            }
            post {
                success {
                    echo "Successfully deployed to staging environment"
                }
                failure {
                    echo "Failed to deploy to staging environment"
                }
            }
        }
        
        stage('Build & Push Docker Image - Production') {
            when {
                branch 'master'
            }
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'acr-credentials',
                                     passwordVariable: 'ACR_PASSWORD',
                                     usernameVariable: 'ACR_USERNAME')
                ]) {
                    sh """
                        echo \${ACR_PASSWORD} | docker login ${PROD_REGISTRY} -u \${ACR_USERNAME} --password-stdin
                        docker build -t ${PROD_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER} -t ${PROD_REGISTRY}/${APP_NAME}:latest .
                        docker push ${PROD_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER}
                        docker push ${PROD_REGISTRY}/${APP_NAME}:latest
                        docker logout ${PROD_REGISTRY}
                    """
                }
                script {
                    env.PROD_IMAGE_TAG = env.BUILD_NUMBER
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                allOf {
                    branch 'master'
                    expression { return params.DEPLOY_TO_PRODUCTION }
                }
            }
            steps {
                // Add a manual approval step before deploying to production
                timeout(time: 24, unit: 'HOURS') {
                    input message: 'Approve deployment to production?', ok: 'Deploy'
                }
                
                withCredentials([
                    usernamePassword(credentialsId: 'azure-credentials',
                                     passwordVariable: 'AZURE_SP_PASSWORD',
                                     usernameVariable: 'AZURE_SP_ID'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID')
                ]) {
                    sh """
                        az login --service-principal \\
                            --username "\${AZURE_SP_ID}" \\
                            --password="\${AZURE_SP_PASSWORD}" \\
                            --tenant "\${AZURE_TENANT_ID}"

                        az aks get-credentials --resource-group ${PROD_RESOURCE_GROUP} --name ${PROD_CLUSTER_NAME} --overwrite-existing

                        kubectl get namespace ${NAMESPACE} || kubectl create namespace ${NAMESPACE}
                        
                        sed -i 's|image: prodacrva1ng1.azurecr.io/akowe:latest|image: prodacrva1ng1.azurecr.io/akowe:${env.PROD_IMAGE_TAG}|g' k8s/overlays/production/patch-deployment.yaml
                        
                        kubectl apply -k k8s/overlays/production/
                        
                        kubectl rollout status deployment/akowe -n ${NAMESPACE} --timeout=300s
                    """
                }
            }
            post {
                success {
                    echo "Successfully deployed to production environment"
                }
                failure {
                    echo "Failed to deploy to production environment"
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'develop') {
                        sh """
                            echo "Verifying staging deployment..."
                            kubectl get ingress -n ${NAMESPACE}
                            kubectl get pods -n ${NAMESPACE} -l app=akowe
                            curl -k -I https://akowe-demo.infotitans.ca/ping || echo "Ping endpoint not accessible"
                        """
                    } else if (env.BRANCH_NAME == 'master' && params.DEPLOY_TO_PRODUCTION) {
                        sh """
                            echo "Verifying production deployment..."
                            kubectl get ingress -n ${NAMESPACE}
                            kubectl get pods -n ${NAMESPACE} -l app=akowe
                            curl -k -I https://akowe.infotitans.ca/ping || echo "Ping endpoint not accessible"
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up resources
            sh 'docker system prune -f || true'
            cleanWs()
        }
        success {
            echo 'Build and deployment successful!'
        }
        failure {
            echo 'Build or deployment failed!'
        }
    }
}