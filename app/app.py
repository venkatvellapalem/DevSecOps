"""Minimal Flask service for the DevSecOps pipeline lab.

The app is not the point — the gates are. It exists so the pipeline has
something real to build, scan, and ship.

RUN 1 STATE: this file contains one deliberately vulnerable endpoint so the
SAST gate has something to actually catch. Without it, Bandit finds nothing on
20 lines of Flask and the "demonstrably functional SAST gate" rubric item is
impossible to satisfy. See /debug/echo.
"""
import subprocess

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def home():
    return {"status": "ok", "service": "bcssl-devsecops-demo"}


@app.route("/healthz")
def healthz():
    # Container HEALTHCHECK hits this. Kept separate from / so a future
    # dependency-check on / doesn't break the liveness probe.
    return {"status": "healthy"}


@app.route("/debug/echo")
def debug_echo():
    """DELIBERATELY VULNERABLE — the SAST gate's target.

    Bandit reports this as B602: a request parameter flows into a shell, so
    ?cmd=... is remote code execution as uid 10001. The fix commit replaces it
    with the argv form (shell=False) and the sast job goes green.

    Lab artifact. Do not copy this pattern, and do not run this image
    anywhere that is actually reachable.
    """
    cmd = request.args.get("cmd", "id")
    return {"output": subprocess.check_output(cmd, shell=True, text=True)}


if __name__ == "__main__":
    # Dev server on purpose: this is a scanner target, not a service.
    # ponytail: no gunicorn. Add one when this stops being a lab.
    app.run(host="0.0.0.0", port=5000)
