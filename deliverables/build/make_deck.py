"""Build the presentation deck.

16:9, one idea per slide, speaker notes throughout (a deck nobody can present is
a document). Diagrams come from make_diagrams.py so they match this deck's palette.
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(HERE, "diagrams")
OUT = os.path.join(HERE, "DevSecOps_Secure_Pipeline.pptx")

INK = RGBColor(0x11, 0x18, 0x27)
INK2 = RGBColor(0x37, 0x41, 0x51)
MUTED = RGBColor(0x6B, 0x72, 0x80)
DIM = RGBColor(0x9C, 0xA3, 0xAF)
BLUE = RGBColor(0x25, 0x63, 0xEB)
GREEN = RGBColor(0x15, 0x80, 0x3D)
RED = RGBColor(0xDC, 0x26, 0x26)
AMBER = RGBColor(0xB4, 0x53, 0x09)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xE5, 0xE7, 0xEB)
BG = RGBColor(0xF9, 0xFA, 0xFB)
DARK = RGBColor(0x0F, 0x17, 0x2A)

SW, SH = Inches(13.333), Inches(7.5)
SANS = "Segoe UI"


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.25)
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, runs, size=18, color=INK2, bold=False, align=PP_ALIGN.LEFT,
         space_after=8, line_spacing=1.15):
    """runs: str, or list of (text, {opts}) tuples, or list of such lists (paragraphs)."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    if isinstance(runs, str):
        runs = [runs]
    if runs and isinstance(runs[0], str):
        runs = [runs]
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        if isinstance(para, str):
            para = [(para, {})]
        for t, o in para:
            r = p.add_run()
            r.text = t
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold)
            r.font.color.rgb = o.get("color", color)
            r.font.name = SANS
    return tb


def notes(slide, text_):
    slide.notes_slide.notes_text_frame.text = text_


def header(slide, title, kicker=None, accent=BLUE):
    rect(slide, Inches(0), Inches(0), Inches(0.16), SH, fill=accent)
    text(slide, Inches(0.62), Inches(0.42), Inches(11.8), Inches(0.7),
         [[(title, {"size": 33, "bold": True, "color": INK})]], space_after=0)
    if kicker:
        text(slide, Inches(0.62), Inches(1.12), Inches(11.8), Inches(0.5),
             [[(kicker, {"size": 16, "color": MUTED})]], space_after=0)


def footer(slide, n):
    text(slide, Inches(12.1), Inches(6.95), Inches(0.9), Inches(0.3),
         [[(str(n), {"size": 11, "color": DIM})]], align=PP_ALIGN.RIGHT, space_after=0)


def bullets(slide, items, x=Inches(0.75), y=Inches(1.85), w=Inches(11.8), size=17,
            gap=13):
    """items: list of (lead, body) or plain strings."""
    paras = []
    for it in items:
        if isinstance(it, tuple):
            lead, body = it
            paras.append([("▪  ", {"color": BLUE, "bold": True, "size": size}),
                          (lead, {"bold": True, "color": INK, "size": size}),
                          (body, {"color": INK2, "size": size})])
        else:
            paras.append([("▪  ", {"color": BLUE, "bold": True, "size": size}),
                          (it, {"color": INK2, "size": size})])
    text(slide, x, y, w, Inches(4.6), paras, size=size, space_after=gap)


def callout(slide, label, body, y=Inches(5.15), fill=BG, edge=LINE, label_color=BLUE):
    rect(slide, Inches(0.75), y, Inches(11.83), Inches(1.35), fill=fill, line=edge,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(slide, Inches(1.05), y + Inches(0.14), Inches(11.2), Inches(1.1),
         [[(label, {"size": 12, "bold": True, "color": label_color})],
          [(body, {"size": 16, "color": INK2})]], space_after=3)


def image_slide(prs, title, img, kicker=None, n=0, accent=BLUE, caption=None, note=None):
    s = blank(prs)
    header(s, title, kicker, accent)
    from PIL import Image
    iw, ih = Image.open(os.path.join(DIAG, img)).size
    max_w, max_h = Inches(12.0), Inches(4.5 if caption else 5.0)
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    s.shapes.add_picture(os.path.join(DIAG, img), int((SW - w) / 2), Inches(1.95), width=w, height=h)
    if caption:
        text(s, Inches(0.9), Inches(6.45), Inches(11.5), Inches(0.5),
             [[(caption, {"size": 13, "color": MUTED})]], align=PP_ALIGN.CENTER, space_after=0)
    footer(s, n)
    if note:
        notes(s, note)
    return s


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    n = 0

    def nxt():
        nonlocal n
        n += 1
        return n

    # ------------------------------------------------------------- 1. title
    s = blank(prs)
    rect(s, 0, 0, SW, SH, fill=DARK)
    rect(s, 0, 0, SW, Inches(0.09), fill=BLUE)
    text(s, Inches(1.0), Inches(2.15), Inches(11.3), Inches(1.2),
         [[("Secure DevOps Pipeline", {"size": 50, "bold": True, "color": WHITE})]], space_after=0)
    text(s, Inches(1.0), Inches(3.35), Inches(11.3), Inches(0.8),
         [[("Building a CI/CD pipeline where security failures are physically unable to ship",
            {"size": 20, "color": RGBColor(0x94, 0xA3, 0xB8)})]], space_after=0)
    rect(s, Inches(1.0), Inches(4.35), Inches(2.2), Inches(0.045), fill=BLUE)
    text(s, Inches(1.0), Inches(4.75), Inches(11.3), Inches(1.0),
         [[("Six automated gates  ·  one locked door  ·  verifiable proof",
            {"size": 17, "color": RGBColor(0xCB, 0xD5, 0xE1)})],
          [("BCSSL Cybersecurity Lab Series — Project 15", {"size": 14, "color": RGBColor(0x94, 0xA3, 0xB8)})]],
         space_after=6)
    notes(s, "Open with the outcome, not the technology. One sentence: every time we push code, "
             "six automated checks run, and if any one fails the release is physically impossible. "
             "Not discouraged, not flagged for review. Impossible. Then say you have before-and-after "
             "proof. Total time on this slide: 30 seconds.")

    # ---------------------------------------------------------- 2. the problem
    s = blank(prs)
    header(s, "The problem we are solving", "why security usually happens far too late", RED)
    bullets(s, [
        ("Old way:  ", "write code, build it, ship it. If it had a flaw, you found out from a customer."),
        ("The cost curve:  ", "a bug caught at your keyboard costs minutes. The same bug in production costs an incident call, a patch, and trust."),
        ("Why nobody fixes it:  ", "security reviews happen at the end, when the release is already built and everyone is tired."),
        ("The fix:  ", "move the checks to the cheapest possible moment — the moment you push."),
    ])
    callout(s, "THE ONE IDEA", "A gate is not a report someone reads later. It is a locked door wired to the checks. "
                               "Nobody has to remember anything.", label_color=RED)
    footer(s, nxt())
    notes(s, "The analogy to use: a toy racecar factory. In the old way you build the car, box it, and ship it "
             "straight to the shelf. If the battery explodes in an 11-year-old's hands, you find out from the "
             "angry phone call. DevSecOps builds a conveyor belt with inspector robots, and an iron gate that "
             "will not open unless every inspector gives a green stamp.")

    # -------------------------------------------------------------- 3. analogy
    s = blank(prs)
    header(s, "What we built, with one picture", "the conveyor belt and the iron gate", BLUE)
    from PIL import Image as _I
    iw, ih = _I.open(os.path.join(DIAG, "pipeline.png")).size
    w = Inches(12.2); h = int(w * ih / iw)
    s.shapes.add_picture(os.path.join(DIAG, "pipeline.png"), Inches(0.57), Inches(2.1), width=w, height=h)
    callout(s, "IN PLAIN WORDS",
            "Every push runs six inspectors. Each one either stamps the build or slams the gate. "
            "The gate is wired to all six — so a failure on the left makes the release impossible on the right.",
            y=Inches(4.9))
    footer(s, nxt())
    notes(s, "Walk left to right once, naming each stage in one breath. Do not explain any of them yet — "
             "the next slides do that. Land on the barrier: that dashed line is the whole security control. "
             "If asked 'what if someone ignores it', the answer is on the next slides: they cannot, it is the "
             "dependency graph.")

    # ----------------------------------------------------------- 4. the six gates
    image_slide(prs, "Why six gates and not one", "coverage.png",
                "each gate inspects something the others structurally cannot see", nxt(),
                note="Do not read this slide. Name each column in one sentence and move on. The point is the "
                     "amber bar at the bottom, which is the empirical version of the claim: in run 2, sca passed "
                     "and image-scan failed on the same commit. If the audience only remembers one slide, make it "
                     "that one.")

    # --------------------------------------------------------------- 5. hadolint
    s = blank(prs)
    header(s, "Gate 1 — hadolint", "lint the recipe before you turn on the oven", BLUE)
    bullets(s, [
        ("What it is:  ", "a linter for your Dockerfile — the recipe that builds the container."),
        ("Named:  ", "\"Hado\" from Docker's lineage + \"lint\", meaning to pick fluff off code."),
        ("Catches:  ", "DL3002 (the container runs as root), DL3007 (an unpinned base image)."),
        ("Why it earns its place:  ", "it runs in parallel with the build, so a bad recipe fails in five seconds instead of after a two-minute build."),
    ])
    callout(s, "ANALOGY", "Checking a cake recipe before turning the oven on. If it says \"bake at 5000 degrees\", "
                          "you want to know that now — not after the kitchen is on fire.", label_color=BLUE)
    footer(s, nxt())
    notes(s, "The security point: a container running as root means if someone gets in, they are already "
             "the superuser. That is a one-line fix in the Dockerfile that prevents a whole class of escalation. "
             "The engineering point is fail-fast: cheap checks run first and in parallel, so you are not waiting "
             "two minutes to learn about a typo.")

    # ------------------------------------------------------------------- 6. SAST
    s = blank(prs)
    header(s, "Gate 2 — sast (Bandit)", "flaws in the code you wrote", BLUE)
    bullets(s, [
        ("Stands for:  ", "Static Application Security Testing. \"Static\" means the code is not running — it is read like an essay."),
        ("Catches:  ", "dangerous patterns in your own source — shell=True, eval, unsafe deserialisation."),
        ("Found here:  ", "B602 in run 1. A URL parameter flowed straight into a system shell, so ?cmd=... was remote code execution."),
        ("The key limit:  ", "a library scanner cannot find these. The flaw is in a line you typed."),
    ])
    callout(s, "ANALOGY", "An English teacher marking your essay with a red pen — spotting forbidden constructions "
                          "without ever reading the essay aloud.", label_color=BLUE)
    footer(s, nxt())
    notes(s, "This is the gate that catches the bugs you personally wrote. Emphasise the concrete finding: "
             "a request parameter reaching a shell is not theoretical, it is remote code execution, and it takes "
             "one careless line. Then flag the limit honestly — this gate cannot see your libraries, which is "
             "exactly why the next gate exists.")

    # -------------------------------------------------------------------- 7. SCA
    s = blank(prs)
    header(s, "Gate 3 — sca (pip-audit)", "flaws in the code you borrowed", BLUE)
    bullets(s, [
        ("Stands for:  ", "Software Composition Analysis — what your software is composed of."),
        ("Catches:  ", "known CVEs in third-party packages, resolved from requirements.txt."),
        ("Found here:  ", "74 vulnerabilities across 8 packages, including a requests version that leaks your credentials on a redirect."),
        ("The point:  ", "your own code can be flawless and this still fires. You do not control the supply chain."),
    ])
    callout(s, "ANALOGY", "You did not grow the lettuce — you bought it. This inspector checks the barcode against "
                          "the national recall list before it goes in the salad.", label_color=BLUE)
    footer(s, nxt())
    notes(s, "The CVE to name: requests 2.19.1 fails to strip the Authorization header when a site redirects you "
             "from HTTPS to HTTP. That means your password goes to wherever the redirect points. It is a "
             "one-character fix in a requirements file that prevents a credential leak.")
    notes_extra = None

    # --------------------------------------------------------------- 8. gitleaks
    s = blank(prs)
    header(s, "Gate 4 — gitleaks", "the secrets you committed", RED)
    bullets(s, [
        ("Catches:  ", "API keys, tokens and passwords sitting in files or commit history."),
        ("Why it is essential:  ", "nothing else here reads values. SAST reads patterns, SCA reads version numbers, Trivy reads packages — an AWS key in a config file slides past all three."),
        ("Found here:  ", "a planted test secret failed the gate and blocked the release, and the notification fired."),
        ("Redaction matters:  ", "the scanner redacts the secret in its own output, so the CI log does not become the leak."),
    ])
    callout(s, "ANALOGY", "Checking your backpack before you leave the house, to be sure you did not tape your "
                          "house keys and door PIN to the front of your diary.", label_color=RED)
    footer(s, nxt())
    notes(s, "This is the gate people forget, and it is the one with the shortest fuse. A dependency CVE might "
             "take months to exploit; a leaked key is usable the second it is public. If you only add one gate "
             "beyond the basics, add this one. Also worth mentioning: a scanner that never fires is usually "
             "misconfigured, not proof you are clean.")

    # ------------------------------------------------------------ 9. image scan
    s = blank(prs)
    header(s, "Gate 5 — image-scan (Trivy)", "the finished artifact", AMBER)
    bullets(s, [
        ("Inspects:  ", "the assembled container — OS packages, language packages, and everything the base image dragged in."),
        ("Why it is different:  ", "it is the only gate that sees the object you actually ship, rather than the inputs to it."),
        ("Configured carefully:  ", "only fixable findings fail it (ignore-unfixed), because 44 unfixable operating-system CVEs would make the gate permanently red."),
        ("Found here:  ", "in run 2 it failed while sca passed — the CVEs were in the base image, invisible to the dependency scanner."),
    ])
    callout(s, "ANALOGY", "Airport baggage X-ray. The officer does not read your packing list — the suitcase goes "
                          "through the machine and they see what is physically inside.", label_color=AMBER)
    footer(s, nxt())
    notes(s, "Pause on the ignore-unfixed decision — it is the most opinionated choice in the project. Without it "
             "the gate is red on every commit forever, and a gate that is always red gets ignored. That is worse "
             "than no gate. The principle: fail on what the team can actually fix.")

    # -------------------------------------------------------------- 10. the gate
    image_slide(prs, "The gate itself", "barrier.png",
                "one line of YAML that GitHub enforces for you", nxt(), accent=AMBER,
                note="This is the one line of code worth showing. Read the needs: array aloud, then say the "
                     "sentence on the slide: GitHub will not start this job unless every listed job succeeded. "
                     "There is no script and no review step. If someone asks how it can be bypassed, the answer "
                     "is that you would have to edit this file, and that edit is itself a reviewed commit.")

    # ---------------------------------------------------------- 11. deploy + notify
    s = blank(prs)
    header(s, "Deploy is not a gate — it is the treasure", "plus the alarm that fires when a gate shuts", GREEN)
    bullets(s, [
        ("deploy:  ", "publishes the approved image to GHCR. It declares all six gates in needs:, so GitHub will not start it unless every one succeeded."),
        ("notify:  ", "the inverse — if: failure(). Silent when everything is green, fires the moment something is blocked."),
        ("Why notify matters:  ", "without it a red run just sits there until somebody happens to look. It writes a per-gate table and can post to Slack."),
        ("The separation:  ", "the reusable workflow produces a scanned image; only the repository knows where its own image belongs."),
    ])
    callout(s, "THE SECURITY CONTROL", "needs:  is not a comment, a convention, or a review step. "
                                       "It is the dependency graph, and GitHub enforces it.", label_color=GREEN)
    footer(s, nxt())
    notes(s, "Common question: 'what if someone merges anyway?' Answer: merging does not publish. The deploy job "
             "only runs on main, and only if all six gates pass. A bad merge leaves you with a green repository "
             "and no new published image — which is exactly the outcome you want. To bypass it you would have to "
             "edit the workflow, which is itself a reviewed commit.")

    # -------------------------------------------------------------- 12. provenance
    image_slide(prs, "One artifact, promoted", "provenance.png",
                "the bytes that were scanned are the bytes that run", nxt(), accent=GREEN,
                note="The red bar is the mistake the original brief made and it is worth dwelling on: rebuilding "
                     "inside the deploy job means you scan artifact A and ship artifact B, and the scan becomes "
                     "theatre. Then give the concrete proof from this project -- CI pushed a specific digest and "
                     "the host runs that same digest. Verifiable, not claimed.")

    # --------------------------------------------------------------- 13. evidence
    image_slide(prs, "The evidence", "runs.png",
                "the gate is only real if you can show it shutting", nxt(), accent=RED,
                note="Walk down the rows. Run 1: three gates red, deploy skipped. Run 2: the eye-opener. Run 3: "
                     "all green, image published. Run 5: a planted secret blocked the release and the notification "
                     "fired. Note the grey cells -- hadolint and gitleaks did not exist in runs 1 and 2, and the "
                     "dashboard reports those as 'not yet added' rather than pretending they passed.")

    # ------------------------------------------------------- 14. run 2 spotlight
    s = blank(prs)
    header(s, "Run 2 is the slide that matters", "sca green, image-scan red, same commit", AMBER)
    bullets(s, [
        ("What happened:  ", "we patched requirements.txt. The dependency gate went green and we expected everything to follow."),
        ("What actually happened:  ", "Trivy still failed — it found CVEs in wheel and jaraco.context, which ship inside the base image."),
        ("Why it could not be caught elsewhere:  ", "those packages appear nowhere in requirements.txt. The dependency scanner is structurally blind to them."),
        ("What it proves:  ", "the gates catch disjoint failure classes. One scanner would have shipped this."),
    ])
    callout(s, "THE SENTENCE TO REMEMBER", "This is the difference between wiring up three scanners and understanding "
                                           "why three are needed.", label_color=AMBER)
    footer(s, nxt())
    notes(s, "This is the strongest single argument in the whole project, and it is empirical rather than "
             "theoretical. If you memorise one thing, memorise this run. It also doubles as the honest answer to "
             "'isn't this redundant?' and to 'couldn't we just use one tool?'")

    # ----------------------------------------------------------- 15. what runs where
    image_slide(prs, "What runs where", "architecture.png",
                "GitHub's runners do the work; the host only pulls and runs", nxt(),
                note="The honest framing: the host does two things -- pull and run. Every build and every scan "
                     "happens on GitHub's ephemeral runners. This is worth saying plainly because it answers the "
                     "question 'do we need to maintain a build server?'. You do not. That machine never builds "
                     "the image it runs, which is exactly why the provenance claim holds.")

    # --------------------------------------------------------------- 16. dashboard
    s = blank(prs)
    header(s, "A live dashboard, for humans",
           "because a green pipeline nobody looks at is not reassurance", BLUE)
    from PIL import Image as _I2
    iw, ih = _I2.open(os.path.join(DIAG, "dashboard.png")).size
    w = Inches(8.2)
    h = int(w * ih / iw)
    s.shapes.add_picture(os.path.join(DIAG, "dashboard.png"), Inches(0.62), Inches(1.78),
                         width=w, height=h)
    text(s, Inches(0.62), Inches(6.72), Inches(8.2), Inches(0.4),
         [[("https://venkatvellapalem.github.io/DevSecOps/", {"size": 12, "color": BLUE})]],
         align=PP_ALIGN.CENTER, space_after=0)

    px, py, pw = Inches(9.15), Inches(1.78), Inches(3.56)
    rect(s, px, py, pw, Inches(4.82), fill=BG, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, px + Inches(0.22), py + Inches(0.22), pw - Inches(0.44), Inches(4.4), [
        [("What you are looking at", {"size": 11.5, "bold": True, "color": BLUE})],
        [("One self-contained HTML file. No framework, no build step, no server to run.",
          {"size": 11.5, "color": INK2})],
        [("Live", {"size": 11.5, "bold": True, "color": BLUE})],
        [("Reads the public GitHub API. The numbers are real, not a mockup.",
          {"size": 11.5, "color": INK2})],
        [("Interactive", {"size": 11.5, "bold": True, "color": BLUE})],
        [("Click any stage for what it checks. Click any run to expand every job.",
          {"size": 11.5, "color": INK2})],
        [("Why it exists", {"size": 11.5, "bold": True, "color": BLUE})],
        [("A manager should not need to read YAML to answer: are we safe to ship today?",
          {"size": 11.5, "color": INK2})],
    ], space_after=7)
    footer(s, nxt())
    notes(s, "Open this live rather than describing it -- network permitting. Click one gate and let the "
             "inspector panel appear: it shows what that gate checks, how many runs it has blocked, and the "
             "exact command to reproduce it locally. Then click a run row and let it expand to show every job "
             "with its duration and a link to its log. That interactivity is what makes this feel like a "
             "product rather than a status page. If the network fails, the bullets on the right still carry "
             "the message.")

    # ---------------------------------------------------------- 17. defects found
    s = blank(prs)
    header(s, "We did not just follow the brief — we audited it", "ten defects found by running it, not reading it", RED)
    bullets(s, [
        ("Two gates could never pass.  ", "The spec's Trivy config failed on 44 unfixable operating-system CVEs, and its Bandit config tripped on its own sample code."),
        ("One rubric item was unwinnable.  ", "The brief plants a vulnerable dependency for SCA but nothing for SAST, so \"demonstrably functional SAST gate\" could never be shown."),
        ("It scanned one artifact and shipped another.  ", "The deploy job rebuilt the image, so the scan was theatre."),
        ("It ran an unpinned third-party action.  ", "@master, with access to the workflow token, inside a project about supply-chain security."),
    ])
    callout(s, "WHY THIS MATTERS", "Two gates that are always red teach people to bypass gates. "
                                   "A gate people route around is worse than no gate at all.", label_color=RED)
    footer(s, nxt())
    notes(s, "This slide is about judgement, not tooling. Anyone can run a scanner; noticing that the supplied "
             "configuration can never pass is the actual skill. Frame it as 'we verified the controls work' rather "
             "than 'the brief was wrong' — you tested the gate by proving it can fail.")

    # ------------------------------------------------------------- 18. honesty
    s = blank(prs)
    header(s, "What this does not catch", "say this before you are asked", MUTED)
    bullets(s, [
        ("Runtime attacks.  ", "A clean image can still be exploited while running. This is a build-time check, not a firewall and not monitoring."),
        ("Logic flaws.  ", "Broken access control and business-logic abuse look perfectly fine to a pattern matcher."),
        ("Configuration drift.  ", "Nothing here enforces that production matches the repository."),
        ("Time.  ", "The vulnerability database changes continuously. The same commit can pass today and fail next month with no code change — run 2 proved it."),
    ])
    callout(s, "WHY VOLUNTEER THIS", "A green pipeline is a statement about a moment, not a guarantee. "
                                     "Being caught not knowing that reads far worse than saying it first.", label_color=MUTED)
    footer(s, nxt())
    notes(s, "Do not skip this slide, and do not bury it at the back. Volunteering the limitations is what "
             "separates a credible engineer from someone who read a tool's marketing page. The freshness point "
             "is the one people find most surprising: your pipeline can go red with no code change at all.")

    # --------------------------------------------------------------- 19. on-prem
    s = blank(prs)
    header(s, "Running it on our own hardware", "pull-based, pinned by digest", GREEN)
    bullets(s, [
        ("Deploy by digest, not by tag.  ", "latest is mutable — pulling it an hour later can hand you different bytes than the ones that were scanned."),
        ("Pull, do not push.  ", "The host polls the registry. No inbound port, and no self-hosted runner."),
        ("Why not a self-hosted runner:  ", "this repository is public, and a runner executes workflow code from any fork's pull request."),
        ("Rollback is a digest.  ", "./deploy/update.sh --rollback returns to the previous image in seconds, without rebuilding anything."),
    ])
    callout(s, "HARDENING ALREADY APPLIED", "non-root (uid 10001)  ·  cap_drop: ALL  ·  no-new-privileges  ·  healthcheck  ·  restart unless-stopped",
            label_color=GREEN)
    footer(s, nxt())
    notes(s, "The self-hosted runner point is a genuine trap and worth dwelling on. A public repository plus a "
             "self-hosted runner means anyone can open a pull request and land code on your machine. Poll-based "
             "deployment has none of that exposure. Also mention that rollback by digest is what makes deploys "
             "reversible without a rebuild.")

    # ---------------------------------------------------------------- 20. reuse
    s = blank(prs)
    header(s, "Any repository can adopt this in 12 lines", "no scanner installs, no configuration, no secrets", BLUE)
    rect(s, Inches(0.75), Inches(1.75), Inches(11.83), Inches(2.35), fill=DARK, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    code = ["jobs:", "  gates:",
            "    uses: venkatvellapalem/DevSecOps/.github/workflows/security-gates.yml@v1",
            "    with:", "      dockerfile: Dockerfile   ·   source-path: src",
            "      requirements: requirements.txt"]
    text(s, Inches(1.1), Inches(1.98), Inches(11.2), Inches(2.0),
         [[(l, {"size": 14, "color": RGBColor(0x7D, 0xD3, 0xFC) if i < 3 else RGBColor(0x94, 0xA3, 0xB8)})]
          for i, l in enumerate(code)], space_after=2)
    bullets(s, [
        ("Verified.  ", "Tested from a separate repository with an unrelated app — it found B602 in their code, 40 dependency CVEs, and fixable image CVEs."),
        ("Portable because  ", "the github context comes from the caller, so checkout pulls their code, not ours."),
    ], y=Inches(4.35), size=16)
    callout(s, "THE TRAP", "GITHUB_TOKEN permissions do not cross a workflow boundary — a caller wanting to push "
                           "must grant packages: write itself.", y=Inches(5.75), label_color=RED)
    footer(s, nxt())
    notes(s, "The 12-line claim is not aspirational, it is measured — see the target repository. The trap is the "
             "thing that costs people an afternoon: a reusable workflow gets the caller's token permissions, and "
             "those permissions are not inherited, so the caller has to opt in explicitly.")

    # ------------------------------------------------------------- 21. glossary
    s = blank(prs)
    header(s, "The vocabulary, in one place", "so nobody has to nod along at an acronym", INK2)
    terms = [
        ("CI / CD", "automatically build and ship on every push"),
        ("SAST", "scan the source you wrote"),
        ("SCA", "scan the dependencies you consumed"),
        ("artifact", "the built thing — here, a container image"),
        ("digest", "a fingerprint of exact bytes; two images sharing one are identical"),
        ("registry", "the warehouse images live in — GHCR"),
        ("immutable", "built once, then never modified, only promoted"),
        ("provenance", "proof an artifact is the one that was checked"),
        ("shift left", "move a check earlier, where it is cheap"),
        ("fail fast", "stop at the first problem instead of carrying it forward"),
        ("least privilege", "grant only the access actually needed"),
    ]
    paras = [[(f"{a}", {"bold": True, "color": INK, "size": 15}),
              (f"   —   {b}", {"color": MUTED, "size": 15})] for a, b in terms]
    text(s, Inches(0.85), Inches(1.8), Inches(11.6), Inches(4.9), paras, space_after=7)
    footer(s, nxt())
    notes(s, "Do not read this slide aloud. Say 'these are all defined in the handout' and move on. It exists so "
             "that the vocabulary is on the record and nobody has to feel behind on acronyms.")

    # ------------------------------------------------------------- 22. closing
    s = blank(prs)
    rect(s, 0, 0, SW, SH, fill=DARK)
    rect(s, 0, 0, SW, Inches(0.09), fill=GREEN)
    text(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.0),
         [[("A gate people route around", {"size": 34, "bold": True, "color": WHITE})],
          [("is worse than no gate at all.", {"size": 34, "bold": True, "color": WHITE})]], space_after=0)
    rect(s, Inches(1.0), Inches(3.6), Inches(2.2), Inches(0.045), fill=GREEN)
    text(s, Inches(1.0), Inches(3.95), Inches(11.3), Inches(1.6),
         [[("Six gates that can each be shown failing.", {"size": 19, "color": RGBColor(0xCB, 0xD5, 0xE1)})],
          [("Before-and-after evidence from real runs.", {"size": 19, "color": RGBColor(0xCB, 0xD5, 0xE1)})],
          [("Provable provenance from commit to running container.", {"size": 19, "color": RGBColor(0xCB, 0xD5, 0xE1)})]],
         space_after=8)
    text(s, Inches(1.0), Inches(6.1), Inches(11.3), Inches(0.6),
         [[("Questions?", {"size": 22, "bold": True, "color": BLUE})]], space_after=0)
    notes(s, "Close on the sentence, not the technology: a gate people route around is worse than no gate. "
             "Then offer the three things a sceptical audience will want — the failing run, the passing run, and "
             "the dashboard. Have those URLs ready to paste into chat.")

    prs.save(OUT)
    print(f"  {os.path.basename(OUT)}  {len(prs.slides.__iter__.__self__._sldIdLst)} slides")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    build()
