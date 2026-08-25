import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        application="jenkins-lab-python-flask",
        message="GitHub -> Jenkins -> Nexus -> Kubernetes deployment is live",
    )


@app.get("/health")
def health():
    return jsonify(status="healthy")


@app.get("/version")
def version():
    return jsonify(version=os.getenv("APP_VERSION", "development"), environment="training")
