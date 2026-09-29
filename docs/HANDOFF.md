# Handoff

Everything you need to understand, run, and demo this project. Written assuming
no prior DevOps background.

---

## 1. What you built, in plain language

You built an **automatic quality-control gate for software**.

Picture a factory. A box moves down a conveyor belt. Before it's allowed to
leave the building, it passes four inspectors. Each inspector checks one
specific thing and either stamps it or hits a big red button.

Here's the important part: **the exit door is physically wired to the
inspectors' buttons.** It is not that someone is supposed to check the stamps
before opening the door. The door cannot open while any button is pressed. It
is a mechanism, not a policy.

That difference *is* DevSecOps. Most teams have a policy ("we review for
security before release"). You built a mechanism.

**The honest caveat:** the inspectors only check what they can see. A box can
leave the building perfectly stamped and still be a bad box. Section 9 covers
what this does not catch.

---

## 2. The 30-second version for a manager

> "Every time we push code, six automated checks run. If any one of them fails,
> the release is physically impossible — not discouraged, not flagged for
> review, impossible. We have before-and-after evidence: a run where three
> checks failed and nothing shipped, and a run where everything passed and it
> did. The whole pipeline is in version control and auditable."

Then open the dashboard.

---

## 3. How it works, step by step

Six things happen, in order, every time you push to `main`.

### Step 1 — build

Docker reads `app/Dockerfile` and assembles a **container image**: your code
plus a Python runtime, frozen into one file. This is what will eventually run.

`Dockerfile` is a multi-stage build. It uses a throwaway first stage to prepare
dependencies, then copies only the result into a clean second stage. Compilers
and build tools never end up in the thing you ship.

### Step 2 — hadolint

Lints the Dockerfile itself. Catches the container equivalent of leaving your
keys in the door: running as root (`DL3002`), using an unpinned base image
(`DL3007`).

Runs *in parallel* with the build, so a bad Dockerfile fails in seconds rather
than after a two-minute image build.

### Step 3 — sast (Bandit)

**S**tatic **A**pplication **S**ecurity **T**esting. Reads your source code and
flags dangerous patterns — `shell=True`, `eval`, unsafe deserialisation.

This catches flaws **you wrote**. A tool that checks your libraries cannot find
these, because the flaw is in a line you typed.

In run 1 it caught `B602`: a request parameter flowing into a shell. That is
remote code execution — someone could pass `?cmd=whatever` and run commands on
your server.

### Step 4 — sca (pip-audit)

**S**oftware **C**omposition **A**nalysis. Reads your dependency list and
compares every package against a database of known vulnerabilities.

This catches flaws **you consumed**. Your code can be perfect and this still
fires. In run 1 it found **74 vulnerabilities across 8 packages**, including a
`requests` version that leaks your password to any site you redirect to.

### Step 5 — gitleaks

Scans for secrets you accidentally committed — API keys, tokens, passwords.

**Nothing else here covers this.** Bandit reads code patterns. pip-audit reads
version numbers. Trivy reads packages. An AWS key sitting in a config file
passes all three silently. This was proven: a planted secret made this gate
fail and blocked the release.

### Step 6 — image-scan (Trivy)

Scans the finished image. This is the only gate that sees the actual object
you ship — operating system packages, language packages, and everything a
base image dragged in.

This one is subtle. In run 2, the dependency gate went green but this gate
stayed red on the same commit. Trivy found vulnerabilities in `wheel` and
`jaraco.context` **inside the base image** — packages that appear nowhere in
`requirements.txt`. The dependency scanner structurally could not see them.

That is why you have six gates and not one.

### And then — deploy

Publishes the image to a registry (GHCR), tagged with the commit.

Here is the whole trick:

```yaml
deploy:
  needs: [build, hadolint, sast, sca, gitleaks, image-scan]
```

`needs:` means "do not start this job unless every listed job succeeded."
GitHub enforces it. No script, no conditional logic, no review step. If any gate
fails, the deploy job shows "skipped" and never runs.

**That one line is the security control.**

---

## 4. The demo script

### Setup

Open the dashboard: **https://venkatvellapalem.github.io/DevSecOps/**

### What to show, in order

**1. The dashboard.** Point at the green status and the pipeline row.

> "Six checks. Every one has to pass."

**2. Open the failing run.**
https://github.com/venkatvellapalem/DevSecOps/actions/runs/36563555891

> "This is a real run from this repo. Three gates failed. Look at `deploy` —
> it says **skipped**. The image was never published. Nobody had to notice
> anything; it simply could not happen."

Click the red `sast` job, show `B602 - subprocess call with shell=True` at
`app/app.py:42`.

> "That's remote code execution, in code we wrote. Caught before it shipped."

**3. Open the passing run.**
https://github.com/venkatvellapalem/DevSecOps/actions/runs/36565013983

> "Same pipeline, after the fixes. All six green. And here —"

Point at the run summary line showing `Pushed ghcr.io/venkatvellapalem/devsecops:3c4ee7a4...`

> "— the image was published, at a specific fingerprint. The container we run
> is provably the container that was scanned."

**4. The part that shows you understand it.** Show run 2
(https://github.com/venkatvellapalem/DevSecOps/actions/runs/36564538965):

> "This is the run people find interesting. `sca` is green, `image-scan` is
> still red, same commit. Those two gates are not redundant — Trivy found
> vulnerabilities in the base image that the dependency scanner cannot see.
> That's why you can't just run one scanner and call it secure."

**5. The gates actually blocking, live.** Point at the notification job on the
gitleaks run:
https://github.com/venkatvellapalem/DevSecOps/actions/runs/36576497068

> "A secret-scanning gate caught a committed credential and blocked the
> release. On failure, a notification job runs and writes a per-gate summary —
> because the only time you need to be told is when something went wrong."

### Questions you should expect

**"Can't someone just merge anyway?"**
The deploy job only runs on `main`, and it depends on all six gates. A merge
that fails gates produces a green repo with no published image. To bypass it
you would have to edit the workflow — which is itself a commit, reviewed, in
version control.

**"What if a scanner gives a false alarm?"**
It will, eventually. The `image-scan` gate is deliberately set to
`ignore-unfixed: true` — it only fails on things that actually *have* a fix.
Without that, 44 unfixable operating-system findings make the gate permanently
red, and gates that are always red get ignored. **A gate people bypass is worse
than no gate.**

**"What about the vulnerabilities it can't see?"**
See section 9. Say so before they ask — it builds more trust than claiming the
pipeline is complete.

---

## 5. Why this is better than a textbook version

Four things worth saying out loud, because they show judgement rather than
tool-running.

**1. You found and fixed ten defects in the lab brief.** The original spec had
two gates that could *never* pass — one from 44 unfixable base-image CVEs, one
from a lint rule its own sample code always triggers. A gate that cannot pass
teaches people to bypass gates.

**2. You proved the gates are not redundant.** Run 2: `sca` green, `image-scan`
red, same commit. That single fact is the difference between "I wired up three
scanners" and "I understand why three."

**3. You fixed a real supply-chain flaw in the brief.** The original pipeline
rebuilt the image inside the deploy job — so it scanned artifact A and shipped
artifact B. Yours builds once, passes the image between jobs, and publishes
those exact bytes. Verifiable by digest.

**4. You hardened the pipeline itself.** The brief's workflow used
`trivy-action@master` — an unpinned third-party action with access to your
token. Yours is pinned to `v0.36.0`. In a project about supply-chain security,
that matters.

---

## 6. Where everything is

| what | where |
|---|---|
| **Dashboard (live)** | https://venkatvellapalem.github.io/DevSecOps/ |
| Repository | https://github.com/venkatvellapalem/DevSecOps |
| All pipeline runs | https://github.com/venkatvellapalem/DevSecOps/actions |
| The workflow | `.github/workflows/devsecops.yml` |
| The app | `app/app.py`, `app/Dockerfile`, `app/requirements.txt` |
| Design decisions | `ARCHITECTURE.md` |
| Shift-left write-up | `docs/WRITEUP.md` |
| Scanner logs, all runs | `evidence/` |
| Before/after screenshots | `evidence/run1-fail/`, `evidence/run3-pass/` |
| On-prem deployment | `deploy/` |
| EC2 host setup | `infra/ec2-bootstrap.sh` |
| The container image | `ghcr.io/venkatvellapalem/devsecops` |

---

## 7. Everyday commands

```bash
# Build and run locally
docker build -t demo ./app
docker run --rm -p 5000:5000 demo          # http://localhost:5000/

# Run the same gates CI runs
docker run --rm -i hadolint/hadolint:2.12.0 < app/Dockerfile
pip install bandit && bandit -r app -lll
pip install pip-audit && pip-audit -r app/requirements.txt
docker run --rm -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:v8.28.0 \
  detect --source=/repo --no-git --redact -v
trivy image --severity CRITICAL,HIGH --ignore-unfixed demo

# Re-demonstrate the failing pipeline (the vulnerable state is in git history)
git revert --no-commit 4f5b136 3c4ee7a
git commit -m "temporarily reintroduce the vulnerable state"
git push        # watch three gates go red and deploy skip
```

---

## 8. Glossary

| term | meaning |
|---|---|
| **CI/CD** | Continuous Integration / Continuous Delivery. Machines, not people, build and ship your code. |
| **SAST** | Scans *your source code* for insecure patterns. |
| **SCA** | Scans *your dependencies* for known CVEs. |
| **CVE** | A public catalogue number for a known vulnerability. |
| **gate** | A check that can stop a release. |
| **shift left** | Move security checks earlier, to where they're cheap. A bug caught at commit costs minutes; in production it costs an incident. |
| **image / container** | Your app plus everything it needs, frozen into one file. |
| **digest** | A fingerprint (`sha256:...`) of exact image bytes. Two images with the same digest are byte-identical. |
| **GHCR** | GitHub Container Registry — where the approved image is stored. |
| **fail-fast** | Stop at the first problem instead of carrying it forward. |
| **provenance** | Being able to prove an artifact is the one that was checked. |

---

## 9. What this does NOT catch

Say this before you're asked.

- **Runtime attacks.** A clean image can be exploited while running. This is a
  build-time check, not a firewall and not monitoring.
- **Logic flaws.** SQL injection through a legitimate-looking query, broken
  access control, business-logic abuse. Scanners see patterns, not intent.
- **Configuration drift.** Nothing enforces that production matches the repo.
- **Time.** The vulnerability database updates continuously. **The same commit
  can pass today and fail next month with no code change** — run 2 demonstrated
  exactly this. A green run is a statement about a moment, not forever.
- **Your judgement.** Nothing here tells you the design is right.

---

## 10. Going on-prem

`deploy/` is built and tested. Two rules worth defending:

**Deploy by digest, not `latest`.** `latest` is a moving target. Pulling it an
hour later can give you different bytes than the ones that were scanned, and
the whole provenance claim quietly becomes false.

```bash
./deploy/update.sh <git-sha>      # resolves tag -> digest, pins the container
./deploy/update.sh --rollback     # back to the previous digest
```

**Do not put a self-hosted GitHub runner on this repository.** It is public, and
a self-hosted runner executes workflow code from *any fork's pull request*.
Someone could open a PR and land arbitrary code on your host. Polling the
registry has no inbound port and accepts no code from outside.

Container hardening already applied: non-root (uid 10001), `cap_drop: ALL`,
`no-new-privileges`, healthcheck, `restart: unless-stopped`.

---

## 11. If you want to go further

- **Signed images** (cosign) — prove the image came from your pipeline, not just
  that it has the right digest.
- **SBOM generation** (`syft`) — a full ingredient list for each build.
- **Dependabot** — automated pull requests when a dependency has a CVE. Turns
  the red gate into a fix you can merge.
- **Branch protection** — make the gates required checks on `main`, so a PR
  cannot merge while they're red.
- **Pin actions by SHA, not tag** — a tag can be moved; a SHA cannot.
