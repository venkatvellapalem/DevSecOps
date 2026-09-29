# Secure DevOps Pipeline

A CI/CD pipeline that builds a container image, runs six security gates against
it, and publishes it **only if all six pass**. Built as Project #15 of the BCSSL
Cybersecurity Lab Series.

**[Live dashboard](https://venkatvellapalem.github.io/DevSecOps/)** ·
[New here? Start with the handoff](docs/HANDOFF.md) ·
[All runs](https://github.com/venkatvellapalem/DevSecOps/actions)

```
git push → build → hadolint → sast → sca → gitleaks → image-scan → deploy
                                                                    └─ only on main, only if all six passed
```

## Results

| job | run 1 (vulnerable) | run 2 (deps patched) | run 3 (all fixed) |
|---|---|---|---|
| build | success | success | success |
| sast | **failure** — B602 shell=True | **failure** | success |
| sca | **failure** — 74 CVEs in 8 packages | success | success |
| image-scan | **failure** — 12 fixable CVEs | **failure** — 2 base-image CVEs | success |
| deploy | **skipped** | **skipped** | **success** → GHCR |

Run 2 is the one worth reading: `sca` went green while `image-scan` stayed red.
The gates are not redundant — Trivy saw packages `pip-audit` cannot, because
they ship in the base image and never appear in `requirements.txt`.

A fifth run proves the secret-scanning gate blocks a release:
`evidence/run5-gitleaks-blocks/` — gitleaks failed on two planted credentials,
deploy was skipped, and `notify` fired for the first time.

Raw scanner output for all three runs is in [`evidence/`](evidence/), along with the
pipeline screenshots the brief asks for:

| file | shows |
|---|---|
| `evidence/run1-fail/pipeline-failed.png` | run 1 — `sast`, `sca`, `image-scan` all red, `deploy` skipped |
| `evidence/run3-pass/pipeline-passed.png` | run 3 — all jobs green, `Pushed ghcr.io/…` in the run summary |
Design rationale: [`ARCHITECTURE.md`](ARCHITECTURE.md).
The shift-left write-up: [`docs/WRITEUP.md`](docs/WRITEUP.md).

## Layout

```
app/
  app.py              Flask service (~35 lines)
  requirements.txt    pinned dependency closure
  Dockerfile          multi-stage, non-root, no build tooling in the runtime
deploy/
  update.sh           pull-based deploy, pinned by digest, with rollback
  docker-compose.yml  on-prem runtime, hardened
.github/workflows/
  devsecops.yml       the pipeline
infra/
  ec2-bootstrap.sh    host prep: swap, Docker Engine, checksum-verified Trivy
  ssh-ec2.sh          keeps the security group in sync with a flapping egress IP
docs/
  index.html          live status dashboard (served by GitHub Pages)
  HANDOFF.md          start here: concepts, demo script, glossary
  WRITEUP.md          gates mapped to vulnerability classes
evidence/             scanner logs and screenshots, per run
```

## The six gates

| gate | tool | inspects | fails on |
|---|---|---|---|
| hadolint | Hadolint | the Dockerfile | DL3002 (root user), DL3007 (unpinned base), warning+ |
| sast | Bandit | source we wrote | High severity, e.g. B602 command injection |
| sca | pip-audit | dependencies we consume | any known CVE |
| gitleaks | Gitleaks | secrets we committed | any detected credential |
| image-scan | Trivy | the built artifact | fixable CRITICAL/HIGH |
| *(deploy)* | — | — | *not a gate: the thing being gated* |

`deploy` declares all five gates in `needs:`, so GitHub will not start it if any
of them failed. **That dependency graph is the security control** — not a report
anyone reads afterwards.

`notify` is the inverse of `deploy`: `if: failure()`, so it runs only when a
gate blocked a release. It writes a per-gate summary and posts to Slack only if
a `SLACK_WEBHOOK_URL` secret exists.

## Reproducing the run-1 failure

`requirements.txt` and `app.py` on `main` are the **fixed** versions. The
vulnerable state is in history:

```bash
git revert --no-commit 4f5b136 3c4ee7a   # restore run-1 app.py + requirements.txt
git commit -m "temporarily re-introduce the vulnerable state"
git push                                  # watch sast/sca/image-scan go red, deploy skip
```

## The runtime target

Two supported paths. CI pushes to `ghcr.io/venkatvellapalem/devsecops`; the host
only ever pulls that artifact.

**On-prem (pull-based) — see [`deploy/`](deploy/README.md):**

```bash
./deploy/update.sh <git-sha>     # resolves the tag to a digest and pins it
./deploy/update.sh --rollback    # back to the previous digest
```

Do **not** put a self-hosted Actions runner on this repo. It is public, and a
self-hosted runner executes workflow code from any fork PR.

**EC2 (the lab's build/test box):**

```bash
docker pull ghcr.io/venkatvellapalem/devsecops@sha256:<digest>
docker run -d --name devsecops -p 5000:5000 --restart unless-stopped \
  ghcr.io/venkatvellapalem/devsecops@sha256:<digest>
```

Deploy by digest, not `latest`. `latest` is mutable, so pinning it loses the
guarantee that the artifact you run is the artifact Trivy cleared.

## Host prep

```bash
ssh -i devsecops.pem ubuntu@<ip> 'sudo bash -s' < infra/ec2-bootstrap.sh
```

Pins a Trivy version and verifies its sha256 rather than piping a remote script
into `sh` — a supply-chain gate is not much use sitting behind an unverified
`curl | sh`.

## Access

Shell access is via **SSM Session Manager**; no inbound port is required and it
is immune to the workstation's flapping egress IP. `infra/ssh-ec2.sh` keeps the
security group synchronised for interactive SSH and the browser-facing port.
