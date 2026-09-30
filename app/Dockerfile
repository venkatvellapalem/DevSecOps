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

# Apply Debian security updates before anything else.
#
# The python:3.11-slim tag lags the Debian security archive, so OS packages in
# the base image can be a patch release behind. That is not cosmetic: it shows up
# as a fixable HIGH finding, and because a fix EXISTS, `ignore-unfixed` correctly
# refuses to hide it -- so the image gate blocks the release until you upgrade.
#
# Seen for real: openssl 3.5.7-1~deb13u2 carried CVE-2026-75804 (QUIC DoS) and
# CVE-2026-84782 (information disclosure) once they were disclosed. The commit
# had not changed; the vulnerability database had. A pipeline that can go red
# with no code change is working, not broken.
#
# Placed before the COPYs so this layer caches and only rebuilds when the base
# image moves.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Install from the wheel dir only. --no-index means the build cannot silently
# reach out to PyPI for a dependency that pip-audit never saw. Whatever this
# image contains is whatever requirements.txt said, and nothing else.
#
# Then strip the build tooling. pip, setuptools and wheel are not executed by a
# running container, and two of them are the last HIGH findings in this image:
#   wheel 0.45.1          CVE-2026-24049  (fixed 0.46.2)
#   jaraco.context 5.3.0  CVE-2026-23949  (fixed 6.1.0)
# Both arrive with the python:3.11-slim base, neither is ours, and because both
# have upstream fixes `ignore-unfixed` rightly refuses to hide them. Removing
# them beats upgrading them: no new downloads, smaller image, less surface.
COPY --from=build /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python3.11/site-packages/jaraco* \
              /usr/local/lib/python3.11/site-packages/pkg_resources \
              /usr/local/lib/python3.11/site-packages/_distutils_hack \
    && rm -f /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.11

COPY app.py .

# Non-root. A container that runs as root is one RCE away from owning the host,
# and the lab's Hadolint stretch goal (DL3002) flags exactly this.
RUN useradd --uid 10001 --create-home appuser
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz').read()"

CMD ["python", "app.py"]
