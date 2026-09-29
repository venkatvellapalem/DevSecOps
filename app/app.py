"""Minimal Flask service for the DevSecOps pipeline lab.

RUN 3 STATE — this is the clean version. The deliberately vulnerable
/debug/echo endpoint from run 1 has been removed: it existed only to give
Bandit's B602 rule something to catch, and leaving a working RCE in the repo
after the demo is how lab code ends up in production.

The run-1 and run-2 versions are in git history if you need to re-demonstrate
the SAST gate failing.
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
    # Dev server on purpose: this is a scanner target, not a service.
    # ponytail: no gunicorn. Add one when this stops being a lab.
    app.run(host="0.0.0.0", port=5000)
