#!/usr/bin/env bash
# infra/host-bootstrap.sh — generic host preparation for Ubuntu / Debian Linux
# (Works on any on-prem server, local Linux/WSL2 VM, or optional cloud instance)
#
# What this script configures:
#   1. 2 GB swapfile (prevents OOM during heavy Docker builds / Trivy scans)
#   2. Docker Engine + Docker Compose v2 (from official Ubuntu repositories)
#   3. Aqua Security Trivy (pinned version with sha256 checksum verification)
#
# Usage:
#   sudo bash infra/host-bootstrap.sh
#
# Note: This project has ZERO mandatory dependency on EC2 or AWS.
# The pipeline runs in GitHub Actions, and images can run anywhere Docker is installed.
set -euo pipefail

# Fail early and clearly. Running this without root otherwise produces a
# confusing stream of apt permission errors halfway through.
if [ "$(id -u)" -ne 0 ]; then
  echo "This script needs root. Run it as: sudo bash $0" >&2
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script targets Ubuntu/Debian. No apt-get found on this system." >&2
  exit 1
fi

TRIVY_VERSION=0.74.0

echo "==> 1. Configuring 2 GB swap"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
swapon --show

echo "==> 2. Installing Docker Engine"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# Use Ubuntu's distribution packages: verified by distro keys, no unauthenticated curl|sh
apt-get install -y -qq docker.io docker-compose-v2 curl ca-certificates
systemctl enable --now docker

# Add the current user to docker group if running under sudo with SUDO_USER
if [ -n "${SUDO_USER:-}" ]; then
  usermod -aG docker "$SUDO_USER" || true
fi

echo "==> 3. Installing Trivy ${TRIVY_VERSION} (checksum-verified)"
# Pinned release deb + sha256 verification against upstream release checksums
cd /tmp
BASE="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}"
DEB="trivy_${TRIVY_VERSION}_Linux-64bit.deb"
curl -fsSLO "${BASE}/${DEB}"
curl -fsSLO "${BASE}/trivy_${TRIVY_VERSION}_checksums.txt"
grep " ${DEB}\$" "trivy_${TRIVY_VERSION}_checksums.txt" | sha256sum -c -
dpkg -i "${DEB}"
rm -f "${DEB}" "trivy_${TRIVY_VERSION}_checksums.txt"

echo "==> 4. Verification"
docker --version
docker compose version
trivy --version
free -h
df -h /

echo "==> Host bootstrap complete. Machine is ready to pull and run containers."
