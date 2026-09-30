"""Generate the diagrams used by the deck and the guides.

Drawn with Pillow rather than sourced from anywhere, so they are reproducible,
editable, and carry no attribution requirement. Everything is rendered at 2x and
referenced at half size, which keeps it sharp when projected.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diagrams")
os.makedirs(OUT, exist_ok=True)

F = "C:/Windows/Fonts/"
INK = "#111827"
INK2 = "#374151"
MUTED = "#6B7280"
DIM = "#9CA3AF"
LINE = "#E5E7EB"
BLUE = "#2563EB"
BLUE_BG = "#EFF6FF"
GREEN = "#15803D"
GREEN_BG = "#ECFDF5"
RED = "#DC2626"
RED_BG = "#FEF2F2"
AMBER = "#B45309"
AMBER_BG = "#FFFBEB"
GREY_BG = "#F3F4F6"
WHITE = "#FFFFFF"


def f(size, bold=False):
    return ImageFont.truetype(F + ("SegoeUIB.ttf" if bold else "segoeui.ttf"), size)


def new(w, h, bg=WHITE):
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def rrect(d, box, r=16, fill=WHITE, outline=LINE, width=3):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def arrow(d, p1, p2, color=DIM, w=4, head=16, dashed=False):
    if dashed:
        x1, y1 = p1
        x2, y2 = p2
        total = math.hypot(x2 - x1, y2 - y1)
        if total == 0:
            return
        ux, uy = (x2 - x1) / total, (y2 - y1) / total
        pos = 0
        while pos < total - head - 6:
            seg = min(14, total - head - 6 - pos)
            d.line([(x1 + ux * pos, y1 + uy * pos),
                    (x1 + ux * (pos + seg), y1 + uy * (pos + seg))], fill=color, width=w)
            pos += 24
    else:
        d.line([p1, p2], fill=color, width=w)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    tip = p2
    left = (tip[0] - head * math.cos(ang - 0.42), tip[1] - head * math.sin(ang - 0.42))
    right = (tip[0] - head * math.cos(ang + 0.42), tip[1] - head * math.sin(ang + 0.42))
    d.polygon([tip, left, right], fill=color)


def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p)
    print(f"  {name:<26} {im.size[0]}x{im.size[1]}")


# ---------------------------------------------------------------- 1. pipeline
def pipeline():
    W, H = 2600, 560
    im, d = new(W, H)
    d.text((70, 60), "The pipeline", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 118), "six independent gates, then a door that will not open unless all six pass",
           font=f(28), fill=MUTED, anchor="lm")

    gates = ["build", "hadolint", "sast", "sca", "gitleaks", "image-scan"]
    bw, bh, gap = 300, 150, 46
    x = 70
    y = 210
    for i, g in enumerate(gates):
        rrect(d, (x, y, x + bw, y + bh), 20, GREY_BG, "#D1D5DB", 3)
        d.text((x + bw / 2, y + 56), g, font=f(34, True), fill=INK, anchor="mm")
        sub = {"build": "compile", "hadolint": "the recipe", "sast": "your code",
               "sca": "your deps", "gitleaks": "your secrets",
               "image-scan": "the artifact"}[g]
        d.text((x + bw / 2, y + 100), sub, font=f(23), fill=MUTED, anchor="mm")
        if i < len(gates) - 1:
            arrow(d, (x + bw + 8, y + bh / 2), (x + bw + gap - 8, y + bh / 2))
        x += bw + gap

    # barrier
    bx = x + 16
    d.line([(bx, y - 40), (bx, y + bh + 70)], fill=AMBER, width=6)
    d.line([(bx + 14, y - 40), (bx + 14, y + bh + 70)], fill=AMBER, width=6)
    d.text((bx + 7, y + bh + 104), "needs:", font=f(26, True), fill=AMBER, anchor="mm")
    d.text((bx + 7, y + bh + 140), "all six must pass", font=f(22), fill=AMBER, anchor="mm")

    # deploy
    dx = bx + 46
    rrect(d, (dx, y, dx + bw, y + bh), 20, BLUE_BG, BLUE, 4)
    d.text((dx + bw / 2, y + 56), "deploy", font=f(34, True), fill=BLUE, anchor="mm")
    d.text((dx + bw / 2, y + 100), "GHCR", font=f(23), fill=BLUE, anchor="mm")
    arrow(d, (bx + 24, y + bh / 2), (dx - 8, y + bh / 2), AMBER)

    d.text((70, 460), "A failure anywhere to the left means deploy is skipped. Not warned about -- skipped.",
           font=f(26), fill=INK2, anchor="lm")
    save(im, "pipeline.png")


# ----------------------------------------------------------------- 2. coverage
def coverage():
    W, H = 2600, 700
    im, d = new(W, H)
    d.text((70, 60), "Why six gates and not one", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 118), "each gate inspects something the others structurally cannot see",
           font=f(28), fill=MUTED, anchor="lm")

    cols = [
        ("hadolint", "the recipe", "how the container\nis built", BLUE),
        ("sast", "code you wrote", "bugs in lines\nyou typed", BLUE),
        ("sca", "code you borrowed", "known CVEs in\nlibraries", BLUE),
        ("gitleaks", "values", "committed keys,\ntokens, passwords", RED),
        ("image-scan", "the artifact", "OS + base image,\ninvisible to SCA", AMBER),
    ]
    cw, gap = 462, 40
    x = 70
    y = 190
    for name, cap, body, col in cols:
        rrect(d, (x, y, x + cw, y + 330), 18, WHITE, LINE, 3)
        d.rounded_rectangle((x, y, x + cw, y + 76), radius=18, fill=col)
        d.rectangle((x, y + 50, x + cw, y + 76), fill=col)
        d.text((x + cw / 2, y + 38), name, font=f(32, True), fill=WHITE, anchor="mm")
        d.text((x + cw / 2, y + 122), cap, font=f(26, True), fill=INK, anchor="mm")
        for i, ln in enumerate(body.split("\n")):
            d.text((x + cw / 2, y + 180 + i * 40), ln, font=f(24), fill=MUTED, anchor="mm")
        x += cw + gap

    # the punchline
    rrect(d, (70, 570, 2530, 665), 16, AMBER_BG, "#FDE68A", 3)
    d.text((100, 617),
           "Run 2:  sca passed and image-scan failed on the same commit.  "
           "Trivy found CVEs in wheel and jaraco.context -- packages that appear nowhere in requirements.txt.",
           font=f(26, True), fill=AMBER, anchor="lm")
    save(im, "coverage.png")


# --------------------------------------------------------------------- 3. runs
def runs():
    W, H = 2000, 780
    im, d = new(W, H)
    d.text((70, 58), "Four runs, one story", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 114), "the gate is only real if you can show it shutting", font=f(28),
           fill=MUTED, anchor="lm")

    gates = ["build", "hadolint", "sast", "sca", "gitleaks", "image-scan", "deploy"]
    rows = [
        ("Run 1", "vulnerable baseline", ["P", "-", "F", "F", "-", "F", "S"]),
        ("Run 2", "deps patched", ["P", "-", "F", "P", "-", "F", "S"]),
        ("Run 3", "fully fixed", ["P", "P", "P", "P", "P", "P", "OK"]),
        ("Run 5", "planted secret", ["P", "P", "P", "P", "F", "P", "S"]),
    ]

    x0 = 380
    cw = 205
    y0 = 230
    rh = 110
    d.text((70, y0 + rh / 2), "", font=f(24))
    for i, g in enumerate(gates):
        d.text((x0 + i * cw + cw / 2, y0 - 34), g, font=f(24, True), fill=MUTED, anchor="mm")

    for r, (name, sub, cells) in enumerate(rows):
        y = y0 + r * rh
        if r % 2 == 0:
            d.rectangle((60, y, 70 + x0 + len(gates) * cw, y + rh - 14), fill="#FAFAFA")
        d.text((90, y + 34), name, font=f(32, True), fill=INK, anchor="lm")
        d.text((90, y + 72), sub, font=f(23), fill=MUTED, anchor="lm")
        for i, c in enumerate(cells):
            cx = x0 + i * cw + cw / 2
            cy = y + (rh - 14) / 2
            if c == "P":
                d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=GREEN_BG, outline=GREEN, width=3)
                d.text((cx, cy), "✓", font=f(30, True), fill=GREEN, anchor="mm")
            elif c == "F":
                d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=RED_BG, outline=RED, width=3)
                d.text((cx, cy), "✕", font=f(30, True), fill=RED, anchor="mm")
            elif c == "S":
                d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=GREY_BG, outline=DIM, width=3)
                d.text((cx, cy), "skipped", font=f(16, True), fill=MUTED, anchor="mm")
            elif c == "OK":
                d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=BLUE_BG, outline=BLUE, width=3)
                d.text((cx, cy), "→", font=f(30, True), fill=BLUE, anchor="mm")
            else:
                d.text((cx, cy), "not yet added", font=f(15), fill=DIM, anchor="mm")

    rrect(d, (60, 700, 1870, 760), 14, BLUE_BG, "#BFDBFE", 3)
    d.text((90, 730), "Run 2 is the important one: sca green, image-scan red, same commit. "
                      "The gates are not redundant.", font=f(26, True), fill=BLUE, anchor="lm")
    save(im, "runs.png")


# --------------------------------------------------------------- 4. provenance
def provenance():
    W, H = 2600, 640
    im, d = new(W, H)
    d.text((70, 58), "One artifact, promoted", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 114), "the bytes that were scanned are the bytes that run",
           font=f(28), fill=MUTED, anchor="lm")

    steps = [
        ("git push", "your commit"),
        ("build once", "one image"),
        ("scan those bytes", "six gates"),
        ("digest", "sha256:0a8d320d…"),
        ("GHCR", "warehouse"),
        ("host runs it", "same digest"),
    ]
    bw, gap = 348, 58
    x = 70
    y = 210
    for i, (t, s) in enumerate(steps):
        col = BLUE if i in (1, 3, 4) else INK2
        bg = BLUE_BG if i in (1, 3, 4) else GREY_BG
        rrect(d, (x, y, x + bw, y + 190), 18, bg, col, 3)
        d.text((x + bw / 2, y + 66), t, font=f(31, True), fill=col, anchor="mm")
        d.text((x + bw / 2, y + 120), s, font=f(22, ), fill=MUTED, anchor="mm")
        if i < len(steps) - 1:
            arrow(d, (x + bw + 10, y + 95), (x + bw + gap - 10, y + 95))
        x += bw + gap

    rrect(d, (70, 470, 2530, 570), 16, RED_BG, "#FECACA", 3)
    d.text((100, 520),
           "The obvious mistake: rebuilding the image inside the deploy job.  "
           "That scans artifact A and ships artifact B -- the scan becomes theatre.",
           font=f(26, True), fill=RED, anchor="lm")

    rrect(d, (70, 585, 2530, 630), 12, GREY_BG, LINE, 2)
    d.text((100, 607),
           "Verified in this project: CI pushed sha256:0a8d320d…, and the host runs sha256:0a8d320d…",
           font=f(23), fill=INK2, anchor="lm")
    save(im, "provenance.png")


# ------------------------------------------------------------- 5. architecture
def architecture():
    W, H = 2600, 900
    im, d = new(W, H)
    d.text((70, 58), "What runs where", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 114), "GitHub's runners do all the work; the host only pulls and runs",
           font=f(28), fill=MUTED, anchor="lm")

    # plane 1
    rrect(d, (70, 190, 780, 720), 20, "#FAFAFA", LINE, 3)
    d.text((425, 240), "Your machine", font=f(32, True), fill=INK, anchor="mm")
    d.text((425, 282), "no Docker installed", font=f(22), fill=MUTED, anchor="mm")
    for i, (t, s) in enumerate([("write code", "edit files"),
                                ("git push", "commit to main")]):
        yy = 350 + i * 140
        rrect(d, (130, yy, 720, yy + 110), 14, WHITE, LINE, 2)
        d.text((425, yy + 40), t, font=f(26, True), fill=INK2, anchor="mm")
        d.text((425, yy + 76), s, font=f(20), fill=MUTED, anchor="mm")

    # plane 2
    rrect(d, (860, 190, 1950, 720), 20, BLUE_BG, "#BFDBFE", 3)
    d.text((1405, 240), "GitHub (cloud)", font=f(32, True), fill=BLUE, anchor="mm")
    d.text((1405, 282), "ephemeral runners, free for public repos", font=f(22), fill=BLUE, anchor="mm")
    for i, (t, s) in enumerate([("build + 6 gates", "Docker preinstalled"),
                                ("deploy job", "push to GHCR"),
                                ("GitHub Pages", "the dashboard")]):
        yy = 340 + i * 118
        rrect(d, (920, yy, 1890, yy + 96), 14, WHITE, "#BFDBFE", 2)
        d.text((1405, yy + 36), t, font=f(25, True), fill=BLUE, anchor="mm")
        d.text((1405, yy + 68), s, font=f(19), fill=MUTED, anchor="mm")

    arrow(d, (790, 455), (850, 455), BLUE)
    arrow(d, (1500, 730), (1500, 795), BLUE)
    d.text((1520, 762), "docker push", font=f(20), fill=BLUE, anchor="lm")

    # plane 3
    rrect(d, (860, 800, 1950, 880), 16, GREEN_BG, "#A7F3D0", 3)
    d.text((1405, 840), "GHCR  —  the warehouse for approved images", font=f(26, True),
           fill=GREEN, anchor="mm")

    # host
    rrect(d, (2030, 190, 2530, 720), 20, "#FAFAFA", LINE, 3)
    d.text((2280, 240), "Host", font=f(32, True), fill=INK, anchor="mm")
    d.text((2280, 282), "on-prem", font=f(22), fill=MUTED, anchor="mm")
    for i, (t, s) in enumerate([("docker pull", "by digest"),
                                ("docker run", "non-root"),
                                ("never builds", "never scans")]):
        yy = 340 + i * 118
        rrect(d, (2080, yy, 2480, yy + 96), 14, WHITE, LINE, 2)
        d.text((2280, yy + 36), t, font=f(25, True), fill=INK2, anchor="mm")
        d.text((2280, yy + 68), s, font=f(19), fill=MUTED, anchor="mm")

    arrow(d, (1950, 450), (2024, 450), GREEN)
    save(im, "architecture.png")


# ------------------------------------------------------------- 6. barrier zoom
def barrier():
    W, H = 2400, 700
    im, d = new(W, H)
    d.text((70, 58), "The gate is the dependency graph", font=f(46, True), fill=INK, anchor="lm")
    d.text((70, 114), "one line of YAML, enforced by GitHub, not by discipline",
           font=f(28), fill=MUTED, anchor="lm")

    rrect(d, (70, 200, 1300, 420), 18, "#0F172A", "#0F172A", 3)
    d.text((100, 240), "deploy:", font=f(28, True), fill="#7DD3FC", anchor="lm")
    d.text((160, 292), "needs: [build, hadolint, sast, sca, gitleaks, image-scan]",
           font=f(26, True), fill="#FCA5A5", anchor="lm")
    d.text((100, 356), "GitHub will not start this job unless every", font=f(23), fill="#94A3B8", anchor="lm")
    d.text((100, 390), "listed job succeeded. No script. No review.", font=f(23), fill="#94A3B8", anchor="lm")

    st = [("green", "the door opens", GREEN, GREEN_BG),
          ("red", "the door stays shut", RED, RED_BG)]
    for i, (cap, txt, col, bg) in enumerate(st):
        yy = 200 + i * 130
        rrect(d, (1400, yy, 2330, yy + 110), 16, bg, col, 3)
        d.text((1440, yy + 38), f"any gate {cap}", font=f(26, True), fill=col, anchor="lm")
        d.text((1440, yy + 78), txt, font=f(23), fill=INK2, anchor="lm")

    rrect(d, (70, 470, 2330, 640), 18, GREY_BG, LINE, 2)
    d.text((110, 520), "Most teams have a policy: \"we review for security before release.\"", font=f(27), fill=INK2, anchor="lm")
    d.text((110, 572), "This is a mechanism. Nobody has to remember anything.", font=f(30, True), fill=INK, anchor="lm")
    save(im, "barrier.png")


if __name__ == "__main__":
    print("Generating diagrams ->", OUT)
    pipeline()
    coverage()
    runs()
    provenance()
    architecture()
    barrier()
    print("done")
