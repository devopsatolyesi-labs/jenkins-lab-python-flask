pipeline {
  agent any

  options {
    disableConcurrentBuilds()
    timeout(time: 20, unit: 'MINUTES')
  }

  environment {
    DOCKERHUB_USERNAME = 'hbayraktar'
    DOCKERHUB_CREDENTIALS_ID = 'dockerhub-creds'
    KUBECONFIG_CREDENTIALS_ID = 'kubeconfig-student-kind'
    LOCAL_CONTAINER = 'student-python-flask'
    LOCAL_PORT = '19004'
    K8S_NAMESPACE = 'student-python-lab'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Image Etiketi') {
      steps {
        script {
          env.GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          env.IMAGE_REF = "${env.DOCKERHUB_USERNAME}/jenkins-lab-python-flask:v${env.BUILD_NUMBER}-${env.GIT_SHA}"
        }
      }
    }

    stage('Python Testleri') {
      steps { sh 'docker build --target test -t python-flask-test:${BUILD_NUMBER} .' }
    }

    stage('Docker Image Build') {
      steps { sh 'docker build --target runtime -t ${IMAGE_REF} .' }
    }

    stage('Docker Huba Public Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID, usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''
            set -eu
            test "$DOCKERHUB_USER" = "$DOCKERHUB_USERNAME"
            printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USER" --password-stdin
            docker push "$IMAGE_REF"
            docker logout
          '''
        }
      }
    }

    stage('Ayni Makinede Docker Deploy') {
      steps {
        sh '''
          set -eu
          docker rm -f "$LOCAL_CONTAINER" 2>/dev/null || true
          docker run -d --name "$LOCAL_CONTAINER" -p "127.0.0.1:${LOCAL_PORT}:8080" "$IMAGE_REF"
          for attempt in 1 2 3 4 5; do
            if docker exec "$LOCAL_CONTAINER" wget -qO- http://127.0.0.1:8080/health | grep -q healthy; then exit 0; fi
            sleep 1
          done
          docker logs "$LOCAL_CONTAINER"
          exit 1
        '''
      }
    }

    stage('KinD Kubernetes Deploy') {
      steps {
        withCredentials([file(credentialsId: env.KUBECONFIG_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
          sh '''
            set -eu
            kubectl --kubeconfig "$KUBECONFIG" apply -f k8s/namespace.yaml
            sed "s|__IMAGE_REF__|$IMAGE_REF|g" k8s/deployment.yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -
            kubectl --kubeconfig "$KUBECONFIG" apply -f k8s/service.yaml
            kubectl --kubeconfig "$KUBECONFIG" apply -f k8s/ingress.yaml
            kubectl --kubeconfig "$KUBECONFIG" -n "$K8S_NAMESPACE" rollout status deployment/python-flask --timeout=120s
            kubectl --kubeconfig "$KUBECONFIG" -n "$K8S_NAMESPACE" exec deployment/python-flask -- wget -qO- http://127.0.0.1:8080/health | grep -q healthy
          '''
        }
      }
    }
  }

  post {
    success {
      echo 'Docker: http://127.0.0.1:19004/health'
      echo 'KinD:   https://student101-app1.devopsatolyesi.com/health'
    }
  }
}
