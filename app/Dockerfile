# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# stage 1 — build: resolve deps and produce wheels
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------------------------------------------------------------------------
# stage 2 — runtime: only the app and its wheels, no compiler, no pip cache
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install from the wheel dir only. --no-index means the build cannot silently
# reach out to PyPI for a dependency that pip-audit never saw. Whatever this
# image contains is whatever requirements.txt said, and nothing else.
COPY --from=build /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY app.py .

# Non-root. A container that runs as root is one RCE away from owning the host,
# and the lab's Hadolint stretch goal (DL3002) flags exactly this.
RUN useradd --uid 10001 --create-home appuser
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz').read()"

CMD ["python", "app.py"]
