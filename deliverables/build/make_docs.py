"""Build the four Word deliverables.

One script so the four documents share styling and cannot drift apart.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from docx_style import (AMBER, BLUE, DIM, FILL_AMBER, FILL_BLUE, FILL_GREEN,
                        FILL_RED, GREEN, INK, INK2, MUTED, RED, WHITE,
                        bullet, callout, code, cover, footer_pagenum, h1, h2, h3,
                        numbered, para, rich, setup, table, toc)

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DASH = "https://venkatvellapalem.github.io/DevSecOps/"
REPO = "https://github.com/venkatvellapalem/DevSecOps"
RUN1 = f"{REPO}/actions/runs/36563555891"
RUN2 = f"{REPO}/actions/runs/36564538965"
RUN3 = f"{REPO}/actions/runs/36565013983"
RUN5 = f"{REPO}/actions/runs/36576497068"


def new():
    d = Document()
    setup(d)
    return d


# ============================================================== BUILD GUIDE
def build_guide():
    d = new()
    cover(d, "Build guide", "Secure DevOps Pipeline",
          "Build a CI/CD pipeline where a security failure makes shipping impossible",
          [("Project", "BCSSL Cybersecurity Lab Series — Project 15"),
           ("Difficulty", "Intermediate to Advanced"),
           ("Duration", "8 to 10 hours across two sessions"),
           ("Prerequisite", "Basic Git. Docker is taught inline."),
           ("Result", "Six automated gates, one locked door, verifiable proof")])

    toc(d, [("1", "What you are building"), ("2", "Prerequisites"),
            ("3", "Phase 1 — the application"), ("4", "Phase 2 — the container"),
            ("5", "Phase 3 — the pipeline, one gate at a time"),
            ("6", "Phase 4 — the gate itself"), ("7", "Phase 5 — publish"),
            ("8", "Phase 6 — prove the gates actually work"),
            ("9", "Phase 7 — deploy on your own hardware"),
            ("10", "Ten defects in the original brief"), ("11", "Verification checklist"),
            ("12", "Where to go next")])

    # 1
    h1(d, "1", "What you are building")
    para(d, "You are building a conveyor belt with inspectors, and an iron gate that will not open "
            "unless every inspector approves. Concretely: a pipeline that runs every time you push "
            "code, checks six different things, and publishes the resulting container image only if "
            "all six pass.")
    para(d, "The single most important idea: the security control is not a policy document or a "
            "checklist. It is one line of YAML that GitHub enforces for you.")
    code(d, ["deploy:", "  needs: [build, hadolint, sast, sca, gitleaks, image-scan]"])
    callout(d, "Why this is the whole thing",
            "GitHub will not start a job whose dependencies failed. Nothing in the deploy job "
            "re-checks anything. The dependency graph IS the security control.", FILL_BLUE, "1D4ED8")

    h2(d, "What you will end up with")
    table(d, ["Piece", "What it is"],
          [["Six gates", "build · hadolint · sast · sca · gitleaks · image-scan"],
           ["A locked door", "deploy, which cannot run unless all six passed"],
           ["An alarm", "notify, which fires only when something is blocked"],
           ["Proof", "a failing run and a passing run, side by side"],
           ["A portable workflow", "callable from any other repository in about 12 lines"]])

    # 2
    h1(d, "2", "Prerequisites")
    bullet(d, "a free GitHub account (Actions is free for public repositories)", bold_lead="GitHub account — ")
    bullet(d, "none. You will write roughly 35 lines of Python.", bold_lead="Python locally — ")
    bullet(d, "optional. GitHub's runners have Docker preinstalled, which is where the pipeline actually runs.",
           bold_lead="Docker locally — ")
    bullet(d, "none, until Phase 7. The pipeline does not need one to prove itself.",
           bold_lead="A server — ")
    callout(d, "A note on local tools",
            "A very common mistake is installing every scanner locally before starting. You do not "
            "need to. Every gate in this guide runs on GitHub's runners. Install tools locally only "
            "when you want faster feedback, which is what the optional CLI in Phase 3 provides.",
            FILL_AMBER, "D97706", AMBER)

    # 3
    h1(d, "3", "Phase 1 — the application")
    para(d, "The application is deliberately tiny. It is not the point; it exists so the pipeline "
            "has something real to build, scan and ship. Create these three files in a new folder "
            "called app/.")
    h3(d, "app/app.py")
    code(d, ['from flask import Flask', '', 'app = Flask(__name__)', '',
             '@app.route("/")', 'def home():',
             '    return {"status": "ok", "service": "my-service"}', '',
             '@app.route("/healthz")', 'def healthz():',
             '    return {"status": "healthy"}', '',
             'if __name__ == "__main__":', '    app.run(host="0.0.0.0", port=5000)'])
    h3(d, "app/requirements.txt")
    code(d, ["flask==2.0.1", "requests==2.19.1", "urllib3==1.23",
             "", "# Pinned on purpose. These versions carry known CVEs and",
             "# exist here so the dependency gate has something real to catch."])
    callout(d, "Why deliberately old packages",
            "You cannot prove a gate works by showing it passing. You plant something for it to "
            "catch, watch it fail, then fix it and watch it pass. That before-and-after is the "
            "deliverable.", FILL_GREEN, "15803D", GREEN)
    para(d, "Push this to a new GitHub repository before continuing, with a .gitignore that excludes "
            "any .env or credential file from the very first commit.")

    # 4
    h1(d, "4", "Phase 2 — the container")
    para(d, "A container image is your application plus everything it needs, frozen into one file. "
            "Wherever you open it, the contents are identical. That property — immutable artifact — "
            "is what makes the later provenance claims possible.")
    h3(d, "app/Dockerfile")
    code(d, ["# syntax=docker/dockerfile:1", "",
             "FROM python:3.11-slim AS build          # stage 1: prepare dependencies",
             "WORKDIR /build",
             "COPY requirements.txt .",
             "RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt", "",
             "FROM python:3.11-slim AS runtime        # stage 2: ship only what runs",
             "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1",
             "WORKDIR /app",
             "COPY --from=build /wheels /wheels",
             "COPY requirements.txt .",
             "RUN pip install --no-index --find-links=/wheels -r requirements.txt \\",
             "    && rm -rf /wheels",
             "COPY app.py .",
             "RUN useradd --uid 10001 --create-home appuser",
             "USER appuser",
             "EXPOSE 5000",
             'CMD ["python", "app.py"]'])
    h3(d, "Why each unusual line is there")
    table(d, ["Line", "Why it matters"],
          [["multi-stage", "compilers and build tools never reach the shipped image"],
           ["--no-index", "the build cannot silently fetch a package the scanner never saw"],
           ["--uid 10001", "a container running as root means one escape is host root"],
           ["USER appuser", "the fix for hadolint's DL3002 rule in the next phase"]])

    # 5
    h1(d, "5", "Phase 3 — the pipeline, one gate at a time")
    callout(d, "Add one gate at a time",
            "Resist building all six at once. Add a gate, push, confirm it fails on your planted "
            "problem, fix it, confirm it passes. A gate you never saw fail is a gate you are "
            "trusting on faith.", FILL_AMBER, "D97706", AMBER)

    h3(d, "Step 1 — build only")
    para(d, "Create .github/workflows/security.yml and get a build running. Nothing else.")
    code(d, ["name: Security gates", "on: [push, pull_request]", "permissions:",
             "  contents: read", "jobs:", "  build:", "    runs-on: ubuntu-latest",
             "    steps:", "      - uses: actions/checkout@v4",
             "      - run: docker build --tag scan-target:${{ github.sha }} ./app"])

    h3(d, "Step 2 — hadolint (the Dockerfile)")
    para(d, "Add this job. It has no needs:, so it runs in parallel with the build and fails in "
            "seconds rather than after a two-minute image build.")
    code(d, ["  hadolint:", "    runs-on: ubuntu-latest", "    steps:",
             "      - uses: actions/checkout@v4",
             "      - uses: hadolint/hadolint-action@v3.1.0",
             "        with:", "          dockerfile: app/Dockerfile",
             "          failure-threshold: warning"])
    para(d, "Use warning, not the default info. At the default, style rules fail the build, which "
            "teaches people to route around the gate. At warning it still catches what matters: "
            "DL3002 (running as root) and DL3007 (an unpinned base image).")

    h3(d, "Step 3 — sast (Bandit)")
    code(d, ["  sast:", "    runs-on: ubuntu-latest", "    needs: build", "    steps:",
             "      - uses: actions/checkout@v4",
             "      - uses: actions/setup-python@v5",
             "        with: { python-version: '3.11' }",
             "      - run: pip install bandit",
             "      - run: bandit -r app -lll -f screen"])
    callout(d, "The gate needs something to catch",
            "Bandit finds nothing in a clean 35-line Flask app. Add a deliberately vulnerable "
            "endpoint so the gate can be shown failing, then remove it. Without this, 'prove the "
            "gate works' is impossible.", FILL_RED, "B91C1C", RED)
    code(d, ['@app.route("/debug/echo")', 'def debug_echo():',
             '    # Intentionally insecure: a request parameter reaches a shell.',
             '    cmd = request.args.get("cmd", "id")',
             '    return {"output": subprocess.check_output(cmd, shell=True, text=True)}'])
    para(d, "Bandit reports this as B602. That is remote code execution: ?cmd=... runs as your "
            "container user. Record the failure, then delete the endpoint.")

    h3(d, "Step 4 — sca (pip-audit)")
    code(d, ["  sca:", "    runs-on: ubuntu-latest", "    needs: build", "    steps:",
             "      - uses: actions/checkout@v4",
             "      - uses: actions/setup-python@v5",
             "        with: { python-version: '3.11' }",
             "      - run: pip install pip-audit",
             "      - run: pip-audit -r app/requirements.txt"])
    para(d, "This should fail immediately on the pinned-old requirements. Expect dozens of "
            "findings across several packages, not one.")

    h3(d, "Step 5 — gitleaks (secrets)")
    code(d, ["  gitleaks:", "    runs-on: ubuntu-latest", "    steps:",
             "      - uses: actions/checkout@v4",
             "      - run: |",
             "          docker run --rm -v \"$PWD:/repo\" ghcr.io/gitleaks/gitleaks:v8.28.0 \\",
             "            detect --source=/repo --no-git --redact --verbose"])
    callout(d, "Test this gate properly",
            "Gitleaks allowlists AWS's own documentation key (AKIAIOSFODNN7EXAMPLE), so testing "
            "with that will show you a pass and teach you the wrong lesson. Use a high-entropy "
            "string in a variable named like PASSWORD or API_SECRET.", FILL_AMBER, "D97706", AMBER)

    h3(d, "Step 6 — image-scan (Trivy)")
    code(d, ["  image-scan:", "    runs-on: ubuntu-latest", "    needs: build", "    steps:",
             "      - uses: actions/checkout@v4",
             "      - run: docker build --tag scan-target:${{ github.sha }} ./app",
             "      - uses: aquasecurity/trivy-action@v0.36.0",
             "        with:", "          image-ref: 'scan-target:${{ github.sha }}'",
             "          severity: 'CRITICAL,HIGH'",
             "          ignore-unfixed: true", "          exit-code: '1'"])
    para(d, "ignore-unfixed is not optional. Without it, unfixable operating-system CVEs in the "
            "base image make this gate red on every commit forever. Measured on the sample image: "
            "44 unfixable findings against 12 fixable ones. Fail on what you can actually fix.")

    # 6
    h1(d, "6", "Phase 4 — the gate itself")
    para(d, "Now wire it together. Add a deploy job that declares every gate, and give it the "
            "permission it needs.")
    code(d, ["  deploy:", "    runs-on: ubuntu-latest",
             "    needs: [build, hadolint, sast, sca, gitleaks, image-scan]",
             "    if: github.ref == 'refs/heads/main' && github.event_name == 'push'",
             "    permissions:",
             "      contents: read",
             "      packages: write      # required, and must be on the CALLER",
             "    steps:", "      - uses: actions/checkout@v4",
             "      - run: docker build --tag scan-target:${{ github.sha }} ./app",
             "      - run: echo \"${{ secrets.GITHUB_TOKEN }}\" | docker login ghcr.io -u \"${{ github.actor }}\" --password-stdin",
             "      - run: |",
             "          REGISTRY=\"ghcr.io/${GITHUB_REPOSITORY,,}\"",
             "          docker tag scan-target:${GITHUB_SHA} \"${REGISTRY}:${GITHUB_SHA}\"",
             "          docker push \"${REGISTRY}:${GITHUB_SHA}\""])
    callout(d, "Three details that cost people an afternoon",
            "permissions must be on the calling job, not inherited. GHCR paths must be lowercase, "
            "and github.repository preserves capitals, so ${GITHUB_REPOSITORY,,} is required. And "
            "the deploy job only runs on main, so a pull request will correctly show it as skipped.",
            FILL_BLUE, "1D4ED8")
    para(d, "Add the notify job now. It is the inverse of deploy and the only thing that tells a "
            "human something broke:")
    code(d, ["  notify:", "    runs-on: ubuntu-latest",
             "    needs: [build, hadolint, sast, sca, gitleaks, image-scan]",
             "    if: failure()",
             "    steps:", "      - run: echo \"Deployment blocked\" >> \"$GITHUB_STEP_SUMMARY\""])

    # 7
    h1(d, "7", "Phase 5 — publish")
    para(d, "Push to main with everything passing. The deploy job should run, push to GHCR, and "
            "write the image reference to the run summary. That reference, including its digest, "
            "is your provenance link.")
    callout(d, "Stop rebuilding in the deploy job",
            "This guide builds once and reuses the artifact elsewhere. Rebuilding inside deploy is a "
            "real defect: you scan artifact A and ship artifact B, and the scan becomes theatre. "
            "Prefer uploading the image as an artifact and loading it in each job.",
            FILL_RED, "B91C1C", RED)

    # 8
    h1(d, "8", "Phase 6 — prove the gates actually work")
    para(d, "This is the deliverable. Capture both halves.")
    table(d, ["Run", "State", "Expected result"],
          [["Run 1", "vulnerable dependency and code", "sast, sca and image-scan fail; deploy skipped"],
           ["Run 2", "dependencies patched only", "sca passes, sast and image-scan still fail; deploy skipped"],
           ["Run 3", "everything fixed", "all gates pass; deploy publishes"],
           ["Run 4", "a planted secret on a branch", "gitleaks fails; deploy skipped; notify fires"]])
    callout(d, "Run 2 is the one that matters",
            "sca green while image-scan is red, on the same commit. Trivy found CVEs in packages "
            "that appear nowhere in requirements.txt. This proves the gates catch disjoint classes "
            "of problem. Keep this evidence.", FILL_GREEN, "15803D", GREEN)
    para(d, "Do this on a throwaway branch, then delete it. Never push a real credential to test a "
            "secret scanner.")

    # 9
    h1(d, "9", "Phase 7 — deploy on your own hardware")
    para(d, "Deploy by digest, not by tag. A tag such as latest is mutable: pulling it an hour "
            "later can give you different bytes than the ones that were scanned, and your provenance "
            "claim quietly becomes false.")
    code(d, ["./deploy/update.sh <git-sha>      # resolves the tag to a digest and pins it",
             "./deploy/update.sh --rollback     # back to the previously deployed digest"])
    para(d, "Do not put a self-hosted GitHub runner on a public repository. A runner executes "
            "workflow code from any fork's pull request, so anyone could open a PR and land code "
            "on your machine. Polling the registry has no inbound port and accepts no outside code.")

    # 10
    h1(d, "10", "Ten defects in the original brief")
    para(d, "Found by running the pipeline rather than reading it. All are corrected in this guide.")
    table(d, ["#", "Defect", "Consequence"],
          [["1", "severity CRITICAL,HIGH with exit-code 1", "permanently red from unfixable base-image CVEs"],
           ["2", "claimed it fails on Critical findings", "there are zero Criticals, so the gate catches nothing"],
           ["3", "bandit -ll", "permanently red from the sample app's own host=\"0.0.0.0\""],
           ["4", "no SAST target planted", "the SAST rubric item is unwinnable"],
           ["5", "trivy-action@master", "unpinned third party running with your token"],
           ["6", "no permissions: packages: write", "the GHCR push is denied"],
           ["7", "ghcr.io/${{ github.repository }}", "docker rejects the uppercase repo name"],
           ["8", "deploy rebuilds the image", "scans artifact A, ships artifact B"],
           ["9", "flask==2.0.1 with unpinned transitives", "the image builds then dies at import"],
           ["10", "requests==2.19.1 with urllib3==1.26.5", "the file does not resolve at all"]],
          widths=[0.4, 2.9, 3.5])
    callout(d, "The lesson worth keeping",
            "Two of those made a gate impossible to pass. A gate that is always red teaches people "
            "to bypass gates, and a gate people route around is worse than no gate at all.",
            FILL_RED, "B91C1C", RED)

    # 11
    h1(d, "11", "Verification checklist")
    for item in [
        "The pipeline runs automatically on push.",
        "Every gate can be shown failing, not just passing.",
        "The deploy job is skipped when any gate fails.",
        "A passing run publishes an image to GHCR with a recorded digest.",
        "The digest you published is the digest your host runs.",
        "The notify job fires on failure and stays silent on success.",
        "No secrets, keys or certificates are committed anywhere in history.",
        "Every action is pinned to a version, not a branch.",
        "permissions: is declared and is the minimum needed.",
        "You can explain why run 2 matters.",
    ]:
        p = d.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Inches(0.15)
        r = p.add_run("☐   ")
        r.font.size = Pt(11)
        r.font.color.rgb = DIM
        r = p.add_run(item)
        r.font.size = Pt(10.5)
        r.font.color.rgb = INK2

    # 12
    h1(d, "12", "Where to go next")
    table(d, ["Idea", "Why"],
          [["Signed images (cosign)", "proves the image came from your pipeline, not merely that the digest matches"],
           ["SBOM generation (syft)", "a full ingredient list per build, for audits"],
           ["Dependabot", "turns a red dependency gate into a pull request you can merge"],
           ["Branch protection", "gates block the deploy; protection blocks the merge"],
           ["Pin actions by SHA", "a tag can be moved, a SHA cannot"]])

    footer_pagenum(d, "Build guide")
    p = os.path.join(OUT, "project_build_guide.docx")
    d.save(p)
    print(f"  {os.path.basename(p)}  {os.path.getsize(p):,} bytes")


# ============================================================ STUDENT GUIDE
def student_guide():
    d = new()
    cover(d, "Student guide", "Secure DevOps Pipeline",
          "Every concept, term and tool in plain language",
          [("Project", "BCSSL Cybersecurity Lab Series — Project 15"),
           ("For", "Students new to DevOps and CI/CD"),
           ("Companion", "project_build_guide.docx and project_student_worksheet.docx"),
           ("Live dashboard", DASH)])

    toc(d, [("1", "The big picture: the toy racecar factory"),
            ("2", "DevOps and DevSecOps"), ("3", "Every term, explained"),
            ("4", "The tools and technologies"), ("5", "Core DevOps concepts"),
            ("6", "The story of the runs"), ("7", "Reading the evidence"),
            ("8", "What this does not catch"), ("9", "Glossary"),
            ("10", "Where to find everything")])

    h1(d, "1", "The big picture: the toy racecar factory")
    para(d, "Imagine a factory that builds remote-controlled toy racecars.")
    para(d, "In the old way, you build the car, drop it in a cardboard box, and ship it straight to "
            "the store shelf. If the battery explodes or a wheel falls off while an eleven-year-old "
            "is driving it, you find out from an angry phone call. Too late.")
    para(d, "DevOps is building an automated conveyor belt. Every time an engineer designs a new "
            "car, robots assemble it, test-drive it, and package it without humans doing repetitive "
            "work by hand.")
    para(d, "DevSecOps adds inspector robots along that belt. Before the car can reach the delivery "
            "truck, every inspector must stamp it. If even one spots a cracked axle or an "
            "uninsulated wire, an iron gate slams shut and the car never leaves the building.")
    callout(d, "The one thing to take away",
            "The important part is not that the inspectors exist. It is that the exit door is "
            "physically wired to their buttons. Most teams have a policy that says the door should "
            "stay shut. You built a mechanism where it cannot open.", FILL_GREEN, "15803D", GREEN)
    para(d, "The honest caveat, which you should always volunteer: the inspectors can only check "
            "what they can see. A car can leave the factory perfectly stamped and still be a bad "
            "car. Section 8 covers exactly what this misses.")

    h1(d, "2", "DevOps and DevSecOps")
    table(d, ["Term", "Stands for", "In plain words"],
          [["DevOps", "Development + Operations",
            "In old companies, developers who write code and operators who run servers sat in separate rooms and blamed each other. DevOps made it one team that ships and runs its own work."],
           ["DevSecOps", "Development + Security + Operations",
            "The same, with security built into the process rather than inspected at the end."],
           ["CI", "Continuous Integration",
            "Every change is merged and tested immediately, instead of saving everything up for one painful integration day."],
           ["CD", "Continuous Delivery / Deployment",
            "Every change that passes the checks is automatically packaged and ready to ship. Deployment means it ships without a human step."]])
    callout(d, "The pizza analogy",
            "Old-style security inspects the pizza after it is baked and boxed, and throws the whole "
            "thing away because the cheese was bad. DevSecOps checks the cheese before it goes "
            "anywhere near the oven.", FILL_BLUE, "1D4ED8")

    h1(d, "3", "Every term, explained")
    terms = [
        ("Build", "Reads the recipe file (the Dockerfile) and packs your code, libraries and runtime "
                  "into one frozen box called a container image.",
         "Packing a school lunchbox: sandwich, apple and juice box sealed together. Wherever you "
         "open it, you get the identical lunch, regardless of whose kitchen packed it.",
         "Immutable artifact — build once, then never modify the contents."),
        ("Hadolint", "Checks the Dockerfile, the recipe, before anything is built.",
         "Checking a cake recipe before turning on the oven. If it says 'bake at 5000 degrees', you "
         "want to hear that now.",
         "Fail fast — catch bad configuration in seconds, not after a long build."),
        ("SAST (Bandit)", "Static Application Security Testing. Reads the source code you wrote, "
                          "without running it, looking for dangerous patterns.",
         "An English teacher marking your essay with a red pen, spotting forbidden constructions "
         "without reading it aloud.",
         "Shift left — catch developer mistakes at the keyboard, the earliest possible moment."),
        ("SCA (pip-audit)", "Software Composition Analysis. Checks the libraries you borrowed from "
                            "other people against a database of known vulnerabilities.",
         "You did not grow the lettuce; you bought it. This inspector checks the barcode against "
         "the national food recall list.",
         "Supply chain security — your code can be flawless and a library you imported can still "
         "be the problem."),
        ("Gitleaks", "Scans files and commit history for secrets: API keys, passwords, tokens.",
         "Checking your backpack before leaving the house, to be sure you did not tape your house "
         "keys to your diary.",
         "Secret governance — credentials belong in a vault, never in a repository."),
        ("Image scan (Trivy)", "Scans the finished container: operating system packages, language "
                               "packages, and everything the base image brought along.",
         "Airport baggage X-ray. The officer does not read your packing list; the suitcase goes "
         "through the machine.",
         "Defence in depth — it is the only gate that sees the object you actually ship."),
        ("Deploy", "Publishes the approved image to a registry. This is not a gate; it is the "
                   "treasure behind the gates.",
         "The delivery truck at the end of the conveyor belt, behind the locked door.",
         "The gate must be the dependency graph, not a review step."),
        ("Notify", "Runs only when something failed, and tells a human.",
         "An alarm that is silent while everything is fine and screams the moment a gate shuts.",
         "Observability — a red run nobody is told about is a red run nobody fixes."),
        ("Artifact", "The tangible thing produced by a build. Here, the container image.",
         "The lunchbox itself, not the recipe.",
         "Immutable artifact."),
        ("Digest", "A long fingerprint such as sha256:0a8d320d..., derived from the exact bytes.",
         "A fingerprint. Two people can both be called Alex (like a tag called latest), but only "
         "one has each fingerprint. Change a single character and the fingerprint changes completely.",
         "Provenance — proof that the thing you run is the thing that was checked."),
        ("Registry (GHCR)", "GitHub Container Registry. The warehouse where approved images live.",
         "The secure storeroom where the approved lunchboxes are kept until a truck collects them.",
         "Single source of truth for released artifacts."),
    ]
    for name, what, analogy, concept in terms:
        h2(d, name, before=12)
        rich(d, [("What it is.  ", {"bold": True, "color": INK}), (what, {})], after=3)
        rich(d, [("Think of it as.  ", {"bold": True, "color": INK}), (analogy, {})], after=3)
        rich(d, [("DevOps concept.  ", {"bold": True, "color": BLUE}), (concept, {})], after=6)

    h1(d, "4", "The tools and technologies")
    table(d, ["Category", "Tool", "What it does here"],
          [["Language", "Python 3.11", "the demo app is written in it"],
           ["Framework", "Flask", "serves web requests on port 5000"],
           ["Packaging", "Docker Engine", "assembles code into portable containers"],
           ["Build", "multi-stage Dockerfile", "stage 1 prepares dependencies; stage 2 ships only what runs"],
           ["CI/CD", "GitHub Actions", "the automation brain, running on every push"],
           ["Linting", "Hadolint", "scans the Dockerfile for unsafe practices"],
           ["SAST", "Bandit", "scans Python for injections and dangerous calls"],
           ["SCA", "pip-audit", "checks requirements against vulnerability databases"],
           ["Secrets", "Gitleaks", "hunts keys and tokens in files and history"],
           ["Image scan", "Trivy", "scans the finished image for CVEs"],
           ["Registry", "GHCR", "stores approved images"],
           ["Dashboard", "HTML, CSS, vanilla JS", "no framework, no build step, no server"],
           ["Hosting", "GitHub Pages", "serves the dashboard straight from the repository"]],
          widths=[1.1, 1.7, 4.0])

    h1(d, "5", "Core DevOps concepts")
    concepts = [
        ("Automation over discipline", "The security control is a dependency declaration, not a "
         "checklist. Nobody has to remember anything, and nobody can forget."),
        ("A gate must be able to fail", "Two gates in the original brief could never pass. A gate "
         "that is always red trains people to bypass gates, which is worse than having none."),
        ("Fail fast", "Cheap checks run first. A bad Dockerfile fails in five seconds rather than "
         "after a two-minute build."),
        ("One artifact, promoted", "Build once, pass those exact bytes between stages, and publish "
         "only them. Rebuilding later means you scanned one thing and shipped another."),
        ("Immutability", "Depend on a digest, not a tag. Tags move; digests cannot."),
        ("Provenance", "Always be able to answer: is the thing running the thing I checked?"),
        ("Least privilege", "The pipeline defaults to read-only, and only the deploy job asks for "
         "write, for itself alone. Every action is pinned to a version."),
        ("Non-root by default", "The container runs as an ordinary user with no capabilities, so "
         "breaking in does not mean owning the host."),
        ("Redundancy is not waste", "Six gates catch six disjoint classes of problem. Run 2 is the "
         "proof, not the assertion."),
        ("A green run is a moment", "The vulnerability database changes continuously. The same "
         "commit can pass today and fail next month with no code change at all."),
    ]
    for name, body in concepts:
        bullet(d, body, bold_lead=name + " — ")

    h1(d, "6", "The story of the runs")
    table(d, ["Run", "What changed", "Result"],
          [["1", "the vulnerable baseline", "sast, sca and image-scan failed; deploy skipped"],
           ["2", "dependencies patched only", "sca passed; sast and image-scan still failed"],
           ["3", "code and base image fixed", "all gates passed; the image was published"],
           ["4", "docs and dashboard work", "all gates passed"],
           ["5", "a planted secret on a branch", "gitleaks failed; deploy skipped; notify fired"]])
    h2(d, "Run 1 — the vulnerable baseline")
    bullet(d, "the app contained a deliberate remote code execution flaw")
    bullet(d, "requirements pinned ancient, vulnerable versions")
    bullet(d, "result: three gates failed and deploy was strictly blocked")
    h2(d, "Run 2 — the eye-opener")
    bullet(d, "dependencies updated, so pip-audit passed")
    bullet(d, "the code flaw was untouched, so SAST failed")
    bullet(d, "Trivy failed too, on wheel and jaraco.context inside the base image")
    bullet(d, "these appear nowhere in requirements.txt, so the dependency scanner cannot see them")
    callout(d, "This is the slide to remember",
            "sca green and image-scan red on the same commit. This is the difference between wiring "
            "up three scanners and understanding why three are needed.", FILL_GREEN, "15803D", GREEN)
    h2(d, "Run 3 — the clean release")
    bullet(d, "the dangerous endpoint was removed from the app")
    bullet(d, "the base image build tooling was stripped from the runtime stage")
    bullet(d, "all gates green; the image was tagged and published to GHCR with a digest")
    h2(d, "Run 5 — the secret leak test")
    bullet(d, "fabricated high-entropy strings were planted on a throwaway branch")
    bullet(d, "gitleaks caught them, deploy was blocked, and the notification fired")
    bullet(d, "the branch and the fake secret were deleted after capturing evidence")

    h1(d, "7", "Reading the evidence")
    para(d, "The repository keeps the raw scanner output for every run under evidence/. That matters: "
            "a claim you cannot show is not evidence.")
    code(d, ["evidence/run1-fail/           # three gates red, deploy skipped",
             "evidence/run2-scapass/        # sca green, everything else red",
             "evidence/run3-pass/           # all gates green, image published",
             "evidence/run5-gitleaks-blocks/  # a secret blocked the release",
             "evidence/run6-cross-repo/     # a different repository adopting the workflow"])
    para(d, f"Failing run: {RUN1}")
    para(d, f"The eye-opener: {RUN2}")
    para(d, f"Passing run: {RUN3}")
    para(d, f"Secret blocked: {RUN5}")

    h1(d, "8", "What this does not catch")
    para(d, "Say this before you are asked. Volunteering the limits reads as competence; being "
            "caught not knowing them reads as the opposite.")
    bullet(d, "A clean image can still be exploited at runtime. This is a build-time check, not a "
              "firewall and not monitoring.", bold_lead="Runtime attacks — ")
    bullet(d, "Broken access control and business-logic abuse look perfectly fine to a pattern "
              "matcher.", bold_lead="Logic flaws — ")
    bullet(d, "Nothing here enforces that production matches the repository.",
           bold_lead="Configuration drift — ")
    bullet(d, "The vulnerability database updates continuously, so the same commit can pass today "
              "and fail next month with no code change. Run 2 demonstrated exactly this.",
           bold_lead="Time — ")
    bullet(d, "Nothing here tells you the design is right.", bold_lead="Your judgement — ")

    h1(d, "9", "Glossary")
    table(d, ["Term", "Meaning"],
          [["artifact", "the thing a build produces; here, a container image"],
           ["CI/CD", "automatically build and ship on every change"],
           ["CVE", "a public catalogue number for a known vulnerability"],
           ["digest", "a fingerprint of exact bytes; identical digests mean identical images"],
           ["Dockerfile", "the recipe for building a container image"],
           ["fail fast", "stop at the first problem rather than carrying it forward"],
           ["gate", "a check that can stop a release"],
           ["GHCR", "GitHub Container Registry — the warehouse for images"],
           ["image", "an application plus everything it needs, frozen into one file"],
           ["immutable", "built once, never modified, only promoted"],
           ["least privilege", "grant only the access actually needed"],
           ["provenance", "proof that an artifact is the one that was checked"],
           ["registry", "where images are stored"],
           ["runner", "the machine that executes a workflow"],
           ["SAST", "Static Application Security Testing — scans your source"],
           ["SCA", "Software Composition Analysis — scans your dependencies"],
           ["shift left", "move a check earlier, to where it is cheap"],
           ["workflow", "the YAML file describing what runs and in what order"]],
          widths=[1.4, 5.4])

    h1(d, "10", "Where to find everything")
    table(d, ["What", "Where"],
          [["Live dashboard", DASH],
           ["Repository", REPO],
           ["All pipeline runs", REPO + "/actions"],
           ["The gate itself", REPO + "/blob/main/.github/workflows/security-gates.yml"],
           ["Design decisions", REPO + "/blob/main/ARCHITECTURE.md"],
           ["How to adopt it elsewhere", REPO + "/blob/main/docs/USE-IT-ON-YOUR-REPO.md"],
           ["Full handoff guide", REPO + "/blob/main/docs/HANDOFF.md"]],
          widths=[1.7, 5.1])

    footer_pagenum(d, "Student guide")
    p = os.path.join(OUT, "project_student_guide.docx")
    d.save(p)
    print(f"  {os.path.basename(p)}  {os.path.getsize(p):,} bytes")


if __name__ == "__main__":
    print("Building documents ->", OUT)
    build_guide()
    student_guide()
