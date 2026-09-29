# Architecture

## What this builds

A CI/CD pipeline that builds a container image, runs three independent security
gates against it, and **only publishes it if all three pass**. The gate is not a
report someone reads later — it is the job dependency graph.

```
git push  →  GitHub Actions
               ├─ build       docker build, save the image as an artifact
               ├─ sast        Bandit        → your own source
               ├─ sca         pip-audit     → your dependencies
               ├─ image-scan  Trivy         → the built artifact
               └─ deploy      needs: [build, sast, sca, image-scan]
                              GHCR push, only on main

GHCR  →  EC2 pulls the scanned digest and runs it
```

## The three planes

| Plane | Runs on | Job |
|---|---|---|
| Development | Windows workstation | author, commit, push. No Docker installed. |
| CI | GitHub-hosted runners | build, scan, gate, publish. Docker is preinstalled. |
| Runtime | EC2 `t3.small` | dev/test box **and** the target that pulls the approved image |

## Decisions and why

### CI builds the deployed image; EC2 never does

If EC2 built the image that got deployed, CI would scan build A and the box
would run build B. The scan would be theatre. So: build exactly once, pass the
image between jobs as an artifact, and publish only those bytes. Provenance is
checkable — the digest CI pushed (`sha256:0a8d320d…`) is the digest the box
runs.

### `--no-index` in the runtime stage

The runtime installs from wheels built in stage 1, with `--no-index`. The build
therefore cannot silently reach PyPI for a dependency `pip-audit` never saw.
Whatever the image contains is whatever `requirements.txt` said, and nothing else.

### Rationale for the three gate settings that differ from the lab write-up

Measured on the run-1 image, `severity: CRITICAL,HIGH`:

```
56 HIGH, 0 CRITICAL
  44 unfixed   ← all Debian 13 OS packages, no upstream fix exists
  12 fixable   ← all our app dependencies
```

`ignore-unfixed: true` makes the gate fail on what this repo can fix. Without it
the gate is red on every commit forever, which teaches people to bypass it.

`bandit -lll` rather than `-ll`, because `-ll` also reports B104
(`host="0.0.0.0"`), which this app always has.

`trivy-action` pinned to `v0.36.0` instead of `@master`, because an unpinned
third-party action executes with the workflow token.

### Build tooling removed from the runtime image

`python:3.11-slim` ships `wheel 0.45.1` and `jaraco.context 5.3.0`, both with
fixable HIGH CVEs. A running container never executes pip, setuptools or wheel.
Removing them beats upgrading them: no new downloads, smaller surface.

### EC2 sizing

`t3.small` (2 GB, x86_64) was the requirement. AMD64 not Graviton so CI's
`amd64` image runs without `docker buildx --platform`. Volume grew 8 → 20 GB:
Trivy's vulnerability DB alone unpacks to **1.4 GB**.

### Access: SSM, not port 22

The workstation is multi-homed and its egress IP flaps between two WAN paths.
Allowlisting a `/32` breaks without warning. SSM Session Manager needs no
inbound port and is immune to it. `infra/ssh-ec2.sh` keeps the security group
synchronised for interactive SSH and the browser-facing port, and it
deliberately **never prunes** — an IP that isn't visible this second is still
needed a second later.

## Verified results

| job | run 1 | run 2 | run 3 |
|---|---|---|---|
| build | success | success | success |
| sast | **failure** | **failure** | success |
| sca | **failure** | success | success |
| image-scan | **failure** | **failure** | success |
| deploy | **skipped** | **skipped** | success |

Run 2 is the interesting one: `sca` green while `image-scan` stayed red. The two
are not redundant — Trivy caught base-image packages that `pip-audit` cannot
see, because they are not in `requirements.txt`.

Full logs in `evidence/`.
