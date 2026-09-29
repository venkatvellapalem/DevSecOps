#!/usr/bin/env bash
# deploy/update.sh — deploy a CI-approved image, on-prem.
#
# Pull-based on purpose. The obvious alternative is a self-hosted GitHub Actions
# runner on the on-prem box, and for THIS repository that would be a serious
# mistake: the repo is public, and a self-hosted runner executes workflow code
# from any fork's pull request. Anyone could open a PR against a public repo and
# land arbitrary code as root on your box.
#
# Polling the registry instead means: no inbound port, nothing exposed to the
# internet, and no code execution originating from outside. A systemd timer or
# cron entry calling this script is the whole deploy mechanism.
#
#   usage:  update.sh <git-sha>
#           update.sh --rollback
#
# Then, to poll every 5 minutes (optional — a manual run is fine for the lab):
#   systemctl edit --force --full devsecops-update.service   # ExecStart=... update.sh <sha>
set -euo pipefail

IMAGE=${IMAGE:-ghcr.io/venkatvellapalem/devsecops}
STATE=${STATE:-/var/lib/devsecops}
HERE=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$STATE"
touch "$STATE/deployed" "$STATE/previous"

# ------------------------------------------------------------------ rollback
if [ "${1:-}" = "--rollback" ]; then
  PREV=$(cat "$STATE/previous")
  [ -n "$PREV" ] || { echo "no previous digest recorded" >&2; exit 1; }
  echo "rolling back to $PREV"
  DEVSECOPS_IMAGE="$PREV" docker compose -f "$HERE/docker-compose.yml" up -d --no-deps app
  echo "$PREV" > "$STATE/deployed"
  exit 0
fi

TAG=${1:?usage: update.sh <git-sha> | update.sh --rollback}

docker pull "${IMAGE}:${TAG}" >/dev/null              # public package: no login needed
NEW=$(docker image inspect "${IMAGE}:${TAG}" --format '{{index .RepoDigests 0}}')
CURRENT=$(cat "$STATE/deployed")

if [ "$NEW" = "$CURRENT" ]; then
  echo "already running ${NEW}"
  exit 0
fi

# The digest is the provenance link to what CI scanned. Print it in the run log
# so the CI job's `docker push` output and this line can be compared by eye.
echo "deploying ${NEW}"
[ -n "$CURRENT" ] && echo "$CURRENT" > "$STATE/previous"
echo "$NEW" > "$STATE/deployed"

DEVSECOPS_IMAGE="$NEW" docker compose -f "$HERE/docker-compose.yml" up -d --no-deps app

echo "$NEW" > "$STATE/deployed"
