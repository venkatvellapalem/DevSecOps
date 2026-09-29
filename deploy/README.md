# Deploying on-prem

The pipeline builds and scans in CI; the on-prem host only ever **pulls the
artifact CI approved**. It never builds the image it runs — otherwise you would
be scanning one thing and running another, and the gates would be theatre.

## Why pull, and not a self-hosted runner

The obvious alternative is a GitHub Actions self-hosted runner on this box. For
**this repository that is unsafe**: it is public, and a self-hosted runner
executes workflow code from any fork's pull request. Someone could open a PR and
land arbitrary code on your host with your runner's privileges.

Polling the registry has no inbound port, exposes nothing to the internet, and
accepts no code from outside.

## Quick start

```bash
# public package — no docker login needed
./deploy/update.sh <git-sha>        # e.g. the sha of a green pipeline run
docker compose -f deploy/docker-compose.yml ps
curl http://localhost:5000/         # {"service":"bcssl-devsecops-demo","status":"ok"}
```

## Why it deploys by digest, not by tag

`latest` is mutable. Pulling it an hour later can hand you different bytes than
the ones Trivy cleared, and the whole "the scanned artifact is the deployed
artifact" claim quietly stops being true.

`update.sh` resolves the tag to a digest once, records it in
`/var/lib/devsecops/deployed`, and pins the container to that digest. Compare it
against the `docker push` output in the CI job to prove the link:

```
CI   latest: digest: sha256:de04549f1f8ecd794acff2cc9dabf23edefe8fccbdd432f55a2a4a2acb186f0b
host deploying ghcr.io/venkatvellapalem/devsecops@sha256:de04549f1f8ecd…
```

## Rollback

```bash
./deploy/update.sh --rollback      # back to the previously deployed digest
```

The previous digest is kept in `/var/lib/devsecops/previous`. Roll back **on the
digest**, not by rebuilding an older commit — a rebuild produces different bytes
that no gate has seen.

## Re-running is safe

`update.sh` compares the resolved digest against the deployed one and exits
without touching the container if they match. Safe to put on a timer.

## Optional: poll for new releases

```bash
sudo tee /etc/systemd/system/devsecops-update.service <<'EOF'
[Unit]
Description=Deploy the latest approved DevSecOps image
After=docker.service network-online.target
[Service]
Type=oneshot
WorkingDirectory=/opt/devsecops
ExecStart=/opt/devsecops/deploy/update.sh <git-sha>
EOF

sudo tee /etc/systemd/system/devsecops-update.timer <<'EOF'
[Unit]
Description=Poll for a new approved image
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF

sudo systemctl enable --now devsecops-update.timer
```

For real push-to-deploy without a public-repo runner, point the timer at a
*specific, immutable* tag and have CI write that tag after the gates pass — do
not have the host resolve `latest`.

## Container hardening applied

Defined in `docker-compose.yml`:

| Setting | Why |
|---|---|
| `no-new-privileges:true` | no setuid escalation after start |
| `cap_drop: ALL` | the app binds 5000, which needs no capabilities |
| non-root `uid 10001` | from the image; a container RCE is not host root |
| `restart: unless-stopped` | survives reboot |
| `HEALTHCHECK` | from the image, on `/healthz` |
