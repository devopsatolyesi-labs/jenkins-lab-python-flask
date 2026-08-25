# Jenkins Lab: Python Flask

A small Flask service and a standalone Jenkins pipeline lab. It is useful on
its own: it does not need access to any private training platform, catalog, or
instructor material.

## Local development

```bash
docker build --target test -t jenkins-lab-python-flask-test .
docker build --target runtime -t jenkins-lab-python-flask:local .
docker run --rm -p 8080:8080 jenkins-lab-python-flask:local
curl http://localhost:8080/health
```

## Jenkins pipelines

Start with `Jenkinsfile.basic`. The default `Jenkinsfile` and
`Jenkinsfile.ci` test and build one immutable image tag
`BUILD_NUMBER-GIT_SHA`. With defaults, they stop after the local build.

Set these job parameters to use your own infrastructure:

| Parameter | Purpose |
|---|---|
| `REGISTRY_URL` | Docker registry hostname; empty means no push |
| `REGISTRY_CREDENTIALS_ID` | Jenkins username/password credential ID for that registry |
| `IMAGE_NAME`, `IMAGE_TAG` | Target name and optional immutable tag |
| `DEPLOY_TARGET` | `none` or `kubernetes` |
| `K8S_NAMESPACE` | Namespace for Kubernetes deployment |
| `KUBE_CONFIG_CREDENTIAL_ID` | Jenkins secret-file credential ID containing kubeconfig |

For a registry push, configure a Jenkins credential by ID; never commit its
password. For Kubernetes, use a least-privileged kubeconfig stored as a
secret-file credential. Set `TRIVY_ENABLED=true` only on an agent that has
Trivy available.

`jenkins/pipelines/Jenkinsfile.cd` is an optional deploy-only pipeline: it
accepts an existing `IMAGE_TAG`, pulls the exact registry artifact, applies
the included Kubernetes manifests, waits for rollout, smoke-tests it, and
attempts rollback on failure. It deliberately never rebuilds the image.
An administrator may set the optional `CD_JOB_NAME`, `REGISTRY_URL`, and
`TRIVY_ENABLED` controller environment variables to connect a platform job;
the repository itself remains usable without them.

The default pipeline already contains the optional Kubernetes deploy stage.
Adapt registry and deployment values to your own environment.
