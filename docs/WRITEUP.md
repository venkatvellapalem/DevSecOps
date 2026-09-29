# Shift-Left Security: Three Gates, Three Failure Classes

The premise of DevSecOps is that security checks belong *in* the pipeline, as
automated steps that can stop a release, rather than in a review that happens
after the build exists. The mechanism here is deliberately boring: every gate
exits non-zero on failure, and the deploy job declares all of them in `needs`.
GitHub will not start a job whose dependencies failed. So a vulnerable build
cannot reach the registry — not because someone remembered to check, but
because the graph does not allow it.

The reason there are three gates rather than one is that they inspect three
disjoint things, and the evidence shows it. In **run 2**, the `sca` gate was
green while `image-scan` was still red — on the same commit. `pip-audit` cannot
see the vulnerable packages that Trivy found, because they are not listed in
`requirements.txt`; they arrive with the base image. One gate would have missed
them entirely.

## Gate 1 — SAST (Bandit): flaws in code we wrote

Static analysis reads the source and flags risky patterns: string-formatted SQL,
`eval`, unsafe deserialisation, `subprocess` with `shell=True`.

**What it caught:** `B602 subprocess_popen_with_shell_equals_true` at
`app/app.py:42:22`. A request parameter flowed into a shell, so
`?cmd=…` was remote code execution as the container user. A dependency scanner
cannot find this — the flaw is not in a library, it is in a line we typed.
CWE-78, OS Command Injection.

**Why it matters after the fix:** the same class covers SQL injection, XXE,
and `pickle.loads` on untrusted input. These are the vulnerabilities a SAST gate
exists to catch, and they only exist where you wrote code.

## Gate 2 — SCA (pip-audit): flaws in code we consume

Software composition analysis resolves the dependency tree and matches each
package against published CVEs. Your code can be flawless and this still fires.

**What it caught:** `Found 74 known vulnerabilities in 8 packages` from
`flask==2.0.1` and `requests==2.19.1` — including CVE-2018-18074, where
`requests` fails to strip the `Authorization` header on a redirect from HTTPS to
HTTP, leaking credentials to whatever host the redirect names. CWE-522,
Insufficiently Protected Credentials.

**Why the transitive pins matter:** the run-1 `requirements.txt` pins the whole
closure. Unpinned, pip resolves Werkzeug past Flask 2.0.1's compatible range and
the image dies at import with `cannot import name 'url_quote'`. A scan of a
dependency tree that cannot actually run is a scan of a tree that cannot
actually be exploited — the finding would be theoretical.

## Gate 3 — Image scan (Trivy): flaws in the artifact we ship

This is the only gate that sees the finished object: OS packages, language
packages, vendored tooling, and anything a base layer dragged in. Run 1 found
**12 fixable CVEs** here and **44 unfixable** ones.

**What it caught that nothing else could:** in run 2, with dependencies already
clean, Trivy flagged `wheel 0.45.1` (CVE-2026-24049 — arbitrary code execution
via a malicious wheel file) and `jaraco.context 5.3.0` (CVE-2026-23949 — path
traversal via a malicious tar). Neither appears in `requirements.txt`. Both ship
inside `python:3.11-slim`. The SAST and SCA gates were green and the image was
still vulnerable.

That run is also the honest illustration of what a supply-chain gate really
feels like: the pipeline went red on a commit that changed nothing except two
version numbers, because a CVE was disclosed in a base image underneath you.
This is why `ignore-unfixed` is in the config, and why the 44 unfixable Debian
findings are filtered rather than left to scream — a gate that is always red is
a gate people learn to skip.

## What the three gates still do not cover

Worth stating plainly, because a green pipeline is not a secure application:

- **Secrets** — nothing here scans for a committed key. Gitleaks would be the
  fourth gate.
- **Runtime** — a clean image at build time can be exploited at run time.
  Scanning is not WAF, and it is not monitoring.
- **Config** — the container runs as non-root and the base is stripped, but
  nothing enforces that. Hadolint would.
- **Freshness** — the vulnerability database updates continuously. A green run
  today is not a green run next month; the same commit can fail later with no
  code change, as run 2 demonstrated.
