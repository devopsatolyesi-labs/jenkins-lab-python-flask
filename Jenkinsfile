// Default standalone pipeline. See Jenkinsfile.basic for the first exercise.
// Jenkinsfile.ci is intentionally self-contained so this file remains usable
// when pasted into a normal Pipeline job.
pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  parameters {
    string(name: 'REGISTRY_URL', defaultValue: '', description: 'Optional Docker registry host')
    string(name: 'REGISTRY_CREDENTIALS_ID', defaultValue: '', description: 'Jenkins credential ID for REGISTRY_URL')
    string(name: 'IMAGE_NAME', defaultValue: 'jenkins-lab-python-flask', description: 'Image repository/name')
    string(name: 'IMAGE_TAG', defaultValue: '', description: 'Optional immutable image tag')
    choice(name: 'DEPLOY_TARGET', choices: ['none', 'kubernetes'], description: 'Deployment target')
    string(name: 'K8S_NAMESPACE', defaultValue: 'default', description: 'Kubernetes namespace')
    string(name: 'KUBE_CONFIG_CREDENTIAL_ID', defaultValue: '', description: 'Secret-file credential ID containing kubeconfig')
    booleanParam(name: 'TRIVY_ENABLED', defaultValue: false, description: 'Run Trivy when available')
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Metadata') {
      steps {
        script {
          def gitSha = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
          env.RESOLVED_IMAGE_TAG = params.IMAGE_TAG?.trim() ? params.IMAGE_TAG.trim() : "${env.BUILD_NUMBER}-${gitSha}"
          env.EFFECTIVE_REGISTRY_URL = params.REGISTRY_URL?.trim() ?: (env.REGISTRY_URL ?: '').trim()
          env.EFFECTIVE_REGISTRY_CREDENTIALS_ID = params.REGISTRY_CREDENTIALS_ID?.trim() ?: (env.REGISTRY_CREDENTIALS_ID ?: '').trim()
          env.IMAGE_REF = env.EFFECTIVE_REGISTRY_URL ? "${env.EFFECTIVE_REGISTRY_URL}/${params.IMAGE_NAME}:${env.RESOLVED_IMAGE_TAG}" : "${params.IMAGE_NAME}:${env.RESOLVED_IMAGE_TAG}"
        }
      }
    }
    stage('Unit Tests') { steps { sh 'docker build --target test -t jenkins-lab-python-flask-test:${RESOLVED_IMAGE_TAG} .' } }
    stage('Docker Build') { steps { sh 'docker build --target runtime -t "$IMAGE_REF" .' } }
    stage('Trivy Scan') {
      when { expression { return params.TRIVY_ENABLED || env.TRIVY_ENABLED == 'true' } }
      steps {
        sh '''#!/bin/sh
          set -eu
          docker run --rm --network "${TRIVY_DOCKER_NETWORK:-bridge}" -v /certs/client:/certs/client:ro \
            -e DOCKER_HOST -e DOCKER_TLS_VERIFY -e DOCKER_CERT_PATH \
            "${TRIVY_IMAGE:-ghcr.io/aquasecurity/trivy:0.68.2}" image --exit-code 0 "$IMAGE_REF"
        '''
      }
    }
    stage('Registry Push') {
      when { expression { return env.EFFECTIVE_REGISTRY_URL } }
      steps {
        script { if (!env.EFFECTIVE_REGISTRY_CREDENTIALS_ID) { error('REGISTRY_CREDENTIALS_ID is required when REGISTRY_URL is set.') } }
        withCredentials([usernamePassword(credentialsId: "${env.EFFECTIVE_REGISTRY_CREDENTIALS_ID}", usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASSWORD')]) {
          sh 'printf %s "$REGISTRY_PASSWORD" | docker login "$EFFECTIVE_REGISTRY_URL" --username "$REGISTRY_USER" --password-stdin && docker push "$IMAGE_REF"'
        }
      }
    }
    stage('Kubernetes Deploy') {
      when { expression { return params.DEPLOY_TARGET == 'kubernetes' } }
      steps {
        script {
          if (!env.EFFECTIVE_REGISTRY_URL) { error('REGISTRY_URL is required for Kubernetes deployment.') }
          if (!params.KUBE_CONFIG_CREDENTIAL_ID?.trim()) { error('KUBE_CONFIG_CREDENTIAL_ID is required for Kubernetes deployment.') }
        }
        withCredentials([file(credentialsId: "${params.KUBE_CONFIG_CREDENTIAL_ID}", variable: 'KUBECONFIG')]) {
          sh 'kubectl -n "$K8S_NAMESPACE" create deployment "$IMAGE_NAME" --image="$IMAGE_REF" --dry-run=client -o yaml | kubectl apply -f - && kubectl -n "$K8S_NAMESPACE" rollout status deployment/"$IMAGE_NAME" --timeout=120s'
        }
      }
    }
    stage('Trigger External CD') {
      when { expression { return env.CD_JOB_NAME?.trim() && env.EFFECTIVE_REGISTRY_URL } }
      steps { build job: env.CD_JOB_NAME, parameters: [string(name: 'IMAGE_TAG', value: "${env.RESOLVED_IMAGE_TAG}")], wait: false }
    }
  }
}
