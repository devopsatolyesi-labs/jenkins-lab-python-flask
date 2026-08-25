from app import app


def test_index():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert response.json["application"] == "jenkins-lab-python-flask"
    assert response.json["message"] == "GitHub -> Jenkins -> Nexus -> Kubernetes deployment is live"


def test_health():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_version_defaults_to_development():
    response = app.test_client().get("/version")
    assert response.status_code == 200
    assert response.json == {"version": "development", "environment": "training"}
