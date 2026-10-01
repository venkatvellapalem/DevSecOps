# Use this on your repo

## The one command

From inside any repository:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/venkatvellapalem/DevSecOps/main/bin/devsecops) init
```

That is the entire integration. It detects your Dockerfile, dependency manifest and
language, and writes a ~12-line workflow that runs the shared gates on your code.
Then push, and watch the gates run at **github.com/&lt;you&gt;/&lt;repo&gt;/actions**.

To run the same gates *before* you push:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/venkatvellapalem/DevSecOps/main/bin/devsecops) scan
```

`scan` needs Docker and nothing else. Both commands are read-only except for
writing that one workflow file, and they never install anything into your repo —
you reference our gates, you do not copy them.

---

## What the one command does, step by step

1. Finds the repository root (walks up to `.git`).
2. Detects the Dockerfile (root, `docker/`, `app/`, `build/`), the dependency
   manifest (searches root first, then subdirectories, skipping `.git` and
   `node_modules`), and the language.
3. Writes `.github/workflows/security-gates.yml` — a caller of the shared reusable
   workflow, with the inputs already filled in for your layout.
4. Tells you what to do next, and warns you if it found a problem (no Dockerfile,
   or a non-Python language, where SAST and SCA are Python-specific).

It refuses to overwrite an existing workflow unless you pass `--force`.

```bash
bash <(curl -fsSL .../bin/devsecops) init --dockerfile docker/Dockerfile \
                                           --source src \
                                           --requirements requirements.txt
```

If you would rather not pipe a script into bash — reasonable, for a security
project — download and read it first:

```bash
curl -fsSL https://raw.githubusercontent.com/venkatvellapalem/DevSecOps/main/bin/devsecops -o devsecops
less devsecops            # ~120 readable lines, no surprises
chmod +x devsecops && ./devsecops init
```

---

## Option A — write the caller by hand (same result, no script)

Prefer to see exactly what lands in your repo? The one command writes this file.
You can create it yourself:

```yaml
# .github/workflows/security.yml
name: Security gates
on: [push, pull_request]
permissions:
  contents: read

jobs:
  gates:
    uses: venkatvellapalem/DevSecOps/.github/workflows/security-gates.yml@v1
    with:
      dockerfile: Dockerfile
      context: .
      source-path: .
      requirements: requirements.txt
      image-name: my-app
```

That is the whole integration. Push, and six gates run on your code.

### Inputs

| input | default | what it does |
|---|---|---|
| `dockerfile` | `Dockerfile` | path to your Dockerfile |
| `context` | `.` | Docker build context |
| `source-path` | `.` | directory Bandit and Gitleaks scan |
| `requirements` | *(empty)* | Python manifest for pip-audit. **Empty means the dependency gate is skipped** — and it says so loudly in the run summary rather than quietly passing |
| `image-name` | `scan-target` | local tag; nothing is pushed unless you add a deploy job |
| `severity` | `CRITICAL,HIGH` | Trivy severities that fail |
| `ignore-unfixed` | `true` | only fail on findings that have a fix. Leave this on |

### Optional secret

| secret | effect |
|---|---|
| `SLACK_WEBHOOK_URL` | posts a one-line summary on failure. Absent = no-op, not an error. |

### Check the result

Actions tab → your run → jobs appear as `gates / hadolint`, `gates / sast`, etc.
Any of them failing means your build did not pass. Add a deploy job with
`needs: gates` to actually block a release.

---

## Option B — copy the files (no dependency on this repo)

```bash
mkdir -p .github/workflows bin
cp <this-repo>/.github/workflows/security-gates.yml .github/workflows/
cp <this-repo>/.github/workflows/devsecops.yml      .github/workflows/   # then edit
cp <this-repo>/bin/devsecops-scan                   bin/
```

Use this if you want to change the gates themselves, or you cannot depend on
someone else's repository.

---

## Option C — run the same gates locally, before you push

```bash
./bin/devsecops-scan
# or
./bin/devsecops-scan --dockerfile docker/Dockerfile --source src --requirements requirements.txt
./bin/devsecops-scan --no-image        # skip the build + image scan
./bin/devsecops-scan --skip sca        # iterate on one gate
```

Exit code is 0 or 1, so it works as a pre-push hook:

```bash
# .git/hooks/pre-push
#!/usr/bin/env bash
exec ./bin/devsecops-scan
```

Requires Docker and nothing else — every tool runs in the **same pinned container
versions CI uses**, so "it passed locally" means something.

---

## Which gates work for which language

| gate | language-agnostic? | if not |
|---|---|---|
| hadolint | ✅ | — |
| gitleaks | ✅ | — |
| image-scan (Trivy) | ✅ | — |
| sast (Bandit) | Python only | swap for `semgrep` (multi-language) or CodeQL |
| sca (pip-audit) | Python only | `npm audit`, `osv-scanner`, `go list -m`, `cargo audit` |

Only the SAST and SCA `run:` lines are language-specific. Everything else works
unchanged on any repo with a Dockerfile.

---

## Expect the first run to be red

This is the tool working, not the tool being broken. A typical first run on a
real codebase finds dozens of dependency CVEs and several high-severity findings
that have been there for years.

Work in this order:

1. **Gitleaks first.** A committed secret is the only finding where the clock is
   actually ticking — rotate it before you do anything else.
2. **Fix what is cheap.** Dependency bumps are usually a one-line change.
3. **Then check `ignore-unfixed` is on.** Without it, unfixable base-image CVEs
   make `image-scan` permanently red, and a gate that is always red gets ignored.
4. **Then decide on Bandit.** `-lll` (High only) is what ships here. Lowering it
   to `-ll` catches more but produces noise you will learn to skip.

**A gate people route around is worse than no gate.** That is the single most
important thing in this document.

---

## Two things that will bite you

**`GITHUB_TOKEN` permissions are not inherited.** A reusable workflow gets the
*contents* permission, but if your deploy job needs `packages: write`, your
**caller** must grant it:

```yaml
jobs:
  gates:
    uses: .../security-gates.yml@v1
  deploy:
    needs: gates
    permissions:
      contents: read
      packages: write      # must be here, in the caller
```

**Pin the ref.** `@v1` is a tag this project moves for fixes, so you get security
updates automatically. That is a deliberate trust decision — this workflow runs in
your repository with your token. If you would rather not take updates, pin a
commit SHA: `@45e8bd1`. Third-party actions *inside* the shared workflow are
pinned to versions, not branches.

---

## Verified

Tested from a separate repository
([`devsecops-target-test`](https://github.com/venkatvellapalem/devsecops-target-test))
containing an unrelated Flask app. With a 12-line caller it found:

- `sast` — `B602`, a request parameter reaching a shell
- `sca` — 40 vulnerabilities across 4 packages
- `image-scan` — fixable CVEs in the built image
- `gitleaks`, `hadolint` — passed
- `notify` — fired, because gates failed

`actions/checkout` inside the shared workflow checked out **the caller's** code.
That is what makes this portable.
