pipeline {
  agent any

  options {
    disableConcurrentBuilds()
    timeout(time: 20, unit: 'MINUTES')
  }

  parameters {
    string(name: 'STUDENT_NO', defaultValue: '101', description: 'Öğrenci numaranız (Örn: 101, 1, 2 vb.)')
    string(name: 'DOCKERHUB_USERNAME', defaultValue: 'hbayraktar', description: 'Docker Hub kullanıcı adınız')
    string(name: 'DOCKERHUB_CREDENTIALS_ID', defaultValue: 'dockerhub-creds', description: 'Jenkins Username with password credential ID')
    string(name: 'KUBECONFIG_CREDENTIALS_ID', defaultValue: 'kubeconfig-student-kind', description: 'Jenkins Secret file credential ID')
  }

  environment {
    LOCAL_CONTAINER = 'student-python-flask'
    LOCAL_PORT = '19004'
    K8S_NAMESPACE = 'student-python-lab'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Parametreler ve İmaj Etiketi') {
      steps {
        script {
          def std = params.STUDENT_NO?.trim() ?: '101'
          if (std.startsWith('student')) {
            env.APP_HOST = "${std}-app1.devopsatolyesi.com"
          } else {
            env.APP_HOST = "student${std}-app1.devopsatolyesi.com"
          }
          env.DH_USER = params.DOCKERHUB_USERNAME?.trim() ?: 'hbayraktar'
          env.GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          env.IMAGE_REF = "${env.DH_USER}/jenkins-lab-python-flask:v${env.BUILD_NUMBER}-${env.GIT_SHA}"
          echo "Öğrenci Host Adı: ${env.APP_HOST}"
          echo "Hedef İmaj:       ${env.IMAGE_REF}"
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
        withCredentials([usernamePassword(credentialsId: params.DOCKERHUB_CREDENTIALS_ID, usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''
            set -eu
            test "$DOCKERHUB_USER" = "$DH_USER"
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
        withCredentials([file(credentialsId: params.KUBECONFIG_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
          sh '''
            set -eu
            kubectl --kubeconfig "$KUBECONFIG" apply -f k8s/namespace.yaml
            sed "s|__IMAGE_REF__|$IMAGE_REF|g" k8s/deployment.yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -
            kubectl --kubeconfig "$KUBECONFIG" apply -f k8s/service.yaml
            sed "s|__APP_HOST__|$APP_HOST|g" k8s/ingress.yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -
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
      echo "KinD:   https://${env.APP_HOST}/"
      echo "Health: https://${env.APP_HOST}/health"
    }
  }
}
