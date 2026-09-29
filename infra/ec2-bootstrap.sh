#!/usr/bin/env bash
# infra/ec2-bootstrap.sh — host prep for Project #15 (Ubuntu 24.04 LTS, t3.small, x86_64)
#
# What this box is for:
#   1. the Docker build/run box (so nothing installs on the Windows machine)
#   2. the target that pulls the image CI already scanned and approved
#
# What this box is NOT for: building the image that gets deployed.
# CI builds -> CI scans -> GHCR -> this box pulls. One artifact, one identity.
#
# Run as:  ssh -i devsecops.pem ubuntu@<ip> 'sudo bash -s' < infra/ec2-bootstrap.sh
set -euo pipefail

TRIVY_VERSION=0.74.0

echo "==> 2 GB swap"
# t3.small ships with 1.9 GB RAM and no swap. pip install + a Trivy scan can peak
# near that, and the OOM killer is not a fun way to lose an afternoon.
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
swapon --show

echo "==> Docker Engine"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# Ubuntu's own packages on purpose: no third-party apt key to trust, no curl|sh.
apt-get install -y -qq docker.io docker-compose-v2 curl ca-certificates
systemctl enable --now docker
usermod -aG docker ubuntu

echo "==> Trivy ${TRIVY_VERSION} (checksum-verified)"
# Pinned version + sha256 check. `curl ... | sh` would be four characters shorter
# and would hand a third party arbitrary code execution on the build box.
cd /tmp
BASE="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}"
DEB="trivy_${TRIVY_VERSION}_Linux-64bit.deb"
curl -fsSLO "${BASE}/${DEB}"
curl -fsSLO "${BASE}/trivy_${TRIVY_VERSION}_checksums.txt"
grep " ${DEB}\$" "trivy_${TRIVY_VERSION}_checksums.txt" | sha256sum -c -
dpkg -i "${DEB}"
rm -f "${DEB}" "trivy_${TRIVY_VERSION}_checksums.txt"

echo "==> versions"
docker --version
docker compose version
trivy --version
free -h
df -h /
