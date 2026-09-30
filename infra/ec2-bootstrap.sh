#!/usr/bin/env bash
# infra/ec2-bootstrap.sh — legacy wrapper for infra/host-bootstrap.sh
#
# NOTE: EC2 is NOT mandatory for this project.
# This project runs entirely on GitHub Actions, publishes to GHCR, and can run
# locally or on any server. This file is retained for backwards compatibility
# if testing on an optional AWS EC2 sandbox.
#
# Delegates directly to the generic host bootstrap script:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/host-bootstrap.sh" "$@"
