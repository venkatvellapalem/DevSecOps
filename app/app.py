"""Minimal Flask service for the DevSecOps pipeline lab.

Deliberately tiny: the app is not the point, the gates are. It exists so the
pipeline has something real to build, scan, and ship.
"""
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return {"status": "ok", "service": "bcssl-devsecops-demo"}


@app.route("/healthz")
def healthz():
    # Container HEALTHCHECK hits this. Kept separate from / so a future
    # dependency-check on / doesn't break the liveness probe.
    return {"status": "healthy"}


if __name__ == "__main__":
    # Dev server on purpose: this is a lab artifact, not a production service.
    # ponytail: no gunicorn. Add one when this stops being a scanner target.
    app.run(host="0.0.0.0", port=5000)
