#!/usr/bin/env python3
"""Issue #44 -- figure verification: content, render, canvas.

    python3 verify_figures.py

Three questions, in the order they can go wrong:

1. CONTENT -- is the committed `figures/manifest.json` the manifest a fresh run produces?
   Each entry records the digest of the exact arrays the figure plotted and of every
   artefact it read, so a changed number changes the digest.  PNG *bytes* depend on the
   matplotlib build; when the local build equals the recorded one they are required to
   match, and when it differs that is reported, not failed -- the DATA is what is pinned.

2. RENDER -- does every label the caption promises actually appear in the drawing?  Each
   figure is re-rendered to SVG with the text kept as text (`svg.fonttype='none'`) and the
   required strings are searched for there.  This is the check that a caption cannot
   outlive the artist it describes.

3. CANVAS -- is every positioned element inside the rendered viewBox?  A label placed
   outside the canvas is not drawn at all -- a defect that has shipped in this repository
   before, and one that reading the source does not reveal.

ONE DOCUMENTED BLIND SPOT, because it changes what the check can promise: matplotlib
renders any string containing mathtext as glyph OUTLINES, so those labels (and the plain
text sharing their string) are invisible to a text search.  `MATHTEXT_LABELS` below lists
them; for those the check falls back to the canvas test, which covers them because they
are drawn as positioned groups.  The blind spot is stated rather than left implicit.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIGD = os.path.join(HERE, "figures")

# labels that a text search cannot find, because their string contains mathtext and
# matplotlib emits the whole string as outlines.  Kept here so the blind spot is visible.
MATHTEXT_LABELS = {
    "fig2_band.png": ["$\\sigma$ tick labels (panel a, both legends) and the budget axis label"],
    "fig3_rule.png": ["the lambda legend of panel (a) and the title of panel (b)"],
    "fig4_lattice.png": ["the usable-boundary legend entry, both x labels, the node legend"],
    "fig5_ceiling.png": ["the bound legend entry, the saturated legend entries"],
    "fig6_decidability.png": ["the N_min axis label"],
}

# strings each figure must actually draw.  Only plain text is listed.
REQUIRED = {
    "fig1_prediction.png": ["perfect prediction", "measured detection rate",
                            "detection rate", "contaminate", "shift"],
    "fig2_band.png": ["predicted band", "measured band", "spread "],
    "fig3_rule.png": ["informative cell (ordered by the factor)",
                      "factor   derived rule / constant rule"],
    "fig4_lattice.png": ["tolerance, 1 pp", "Gaussian control (ratio = 0)",
                         "signed error"],
    "fig5_ceiling.png": ["unsaturated", "measured difference (95 % CI)",
                         "predicted difference"],
    "fig6_decidability.png": ["decidable at that budget", "not decidable",
                              "the budget the study ran: ",
                              "informative cell (ordered by the streams it needs)"],
}

TEXT_RE = re.compile(
    r"<text[^>]*?x=\"([-0-9.eE+]+)\"[^>]*?y=\"([-0-9.eE+]+)\"[^>]*?>(.*?)</text>", re.S)
POS_RE = re.compile(
    r"transform=\"translate\(([-0-9.eE+]+)[ ,]+([-0-9.eE+]+)\)\"")
VIEWBOX_RE = re.compile(r'viewBox="([-0-9. ]+)"')

MIN_DRAWN = 25          # a live figure draws many paths; this only catches a blank one
MIN_POSITIONED = 5      # text elements plus positioned groups


class Audit(object):
    def __init__(self):
        self.rows = []
        self.failed = 0

    def ok(self, name, cond, detail=""):
        self.rows.append((bool(cond), name, detail))
        if not cond:
            self.failed += 1
        return bool(cond)


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


INK_MIN = 0.01          # a figure with less ink than this did not draw
INK_MAX = 0.45          # more ink than this is a flood, usually a misfilled axis
HALF_MIN = 0.01         # each half of a two-panel figure must have drawn something


def pixel_audit(png, au, label):
    """Read the committed PNG back and check that ink is present, and on both halves.

    The element counts in the SVG audit cannot see a panel whose series came out empty
    (the axes are still drawn); pixels can.  Both halves of every figure in this package
    carry a panel, so both must carry ink.
    """
    import matplotlib.image as mpimg
    import numpy as np
    arr = mpimg.imread(png)
    if arr.dtype != np.uint8:
        arr = (arr * 255).astype(np.uint8)
    ink = arr[..., :3].min(axis=2) < 245
    h, w = ink.shape
    frac = float(ink.mean())
    left = float(ink[:, :w // 2].mean())
    right = float(ink[:, w // 2:].mean())
    au.ok("%s/has ink (%.2f%%)" % (label, 100 * frac), INK_MIN <= frac <= INK_MAX,
          "ink fraction %.4f outside [%g, %g]" % (frac, INK_MIN, INK_MAX))
    au.ok("%s/both halves drew (left %.2f%%, right %.2f%%)" % (label, 100 * left,
                                                              100 * right),
          left >= HALF_MIN and right >= HALF_MIN,
          "left %.4f right %.4f" % (left, right))
    return {"ink": frac, "left": left, "right": right}


def read_svg_texts(path):
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        svg = fh.read()
    m = VIEWBOX_RE.search(svg)
    box = tuple(float(v) for v in m.group(1).split()) if m else None
    texts = [(float(x), float(y), re.sub(r"<[^>]+>", "", body))
             for x, y, body in TEXT_RE.findall(svg)]
    pos = [(float(a), float(b)) for a, b in POS_RE.findall(svg)]
    drawn = svg.count("<use ") + svg.count("<path ")
    return svg, box, texts, pos, drawn


def audit_svg(path, required, au, label):
    svg, box, texts, pos, drawn = read_svg_texts(path)
    if not au.ok(label + "/svg has a viewBox", box is not None):
        return None
    x0, y0, w, h = box
    au.ok("%s/is not blank" % label, drawn > MIN_DRAWN,
          "only %d drawn elements" % drawn)
    au.ok("%s/has positioned elements" % label, len(texts) + len(pos) >= MIN_POSITIONED,
          "%d text + %d groups" % (len(texts), len(pos)))
    flat = " ".join(t[2] for t in texts)
    for token in required:
        au.ok("%s/draws %r" % (label, token), token in flat,
              "not found among %d text runs" % len(texts))
    outside = [p for p in ([t[:2] for t in texts] + pos)
               if not (x0 - 1 <= p[0] <= x0 + w + 1 and y0 - 1 <= p[1] <= y0 + h + 1)]
    au.ok("%s/every positioned element is inside the canvas" % label, not outside,
          "outside: %r (viewBox %r)" % (outside[:6], box))
    return flat


def main():
    mpath = os.path.join(FIGD, "manifest.json")
    if not os.path.isfile(mpath):
        sys.stdout.write("FAIL: figures/manifest.json is missing -- run make_figures.py\n")
        return 1
    committed = json.load(io.open(mpath, encoding="utf-8"))

    tmp = tempfile.mkdtemp(prefix="issue44-figcheck-")
    try:
        figs = os.path.join(tmp, "figs")
        svgs = os.path.join(tmp, "svg")
        proc = subprocess.run([sys.executable, "make_figures.py", figs, "--audit-svg", svgs],
                              cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True)
        if proc.returncode != 0:
            sys.stdout.write("FAIL: make_figures.py exited %d\n%s\n"
                             % (proc.returncode, proc.stdout))
            return 1
        fresh = json.load(io.open(os.path.join(figs, "manifest.json"), encoding="utf-8"))

        au = Audit()
        same_build = fresh["matplotlib"] == committed["matplotlib"]
        names = [f["figure"] for f in committed["figures"]]
        au.ok("figure list unchanged", names == [f["figure"] for f in fresh["figures"]],
              "%r vs %r" % (names, [f["figure"] for f in fresh["figures"]]))
        au.ok("every figure has a caption",
              all(f.get("caption") for f in committed["figures"]))

        flats = {}
        for c, f in zip(committed["figures"], fresh["figures"]):
            label = os.path.basename(c["figure"])[:-4]
            au.ok("%s/series digest is reproducible" % label,
                  c["series_sha256"] == f["series_sha256"],
                  "committed %s vs recomputed %s" % (c["series_sha256"][:16],
                                                     f["series_sha256"][:16]))
            au.ok("%s/source artefact digests unchanged" % label,
                  c["sources"] == f["sources"],
                  "committed %r vs recomputed %r" % (c["sources"], f["sources"]))
            png = os.path.join(HERE, c["figure"])
            au.ok("%s/is committed" % label, os.path.isfile(png))
            if os.path.isfile(png):
                au.ok("%s/committed PNG matches its manifest entry" % label,
                      sha256_file(png) == c["png_sha256"])
                pixel_audit(png, au, label)
            if same_build:
                au.ok("%s/PNG bytes reproduce on this matplotlib build" % label,
                      c["png_sha256"] == f["png_sha256"],
                      "recorded build %s" % committed["matplotlib"])
            flats[label] = audit_svg(os.path.join(svgs, label + ".svg"),
                                     REQUIRED.get(label + ".png", []), au, label)

        # CONTROL: the search must be able to tell one figure's document from another.
        # If a figure's required set is satisfied by every other figure as well, the
        # check is not reading the document it claims to read.
        for i, (label, flat) in enumerate(sorted(flats.items())):
            if flat is None:
                continue
            own = [t for t in REQUIRED.get(label + ".png", []) if t in flat]
            others = [f for l2, f in flats.items() if l2 != label and f]
            unique = [t for t in own if not any(t in f for f in others)]
            au.ok("%s/has a token no other figure draws" % label, bool(unique),
                  "none of %r is unique to this figure" % own)

        for f in fresh["figures"]:
            label = os.path.basename(f["figure"])[:-4]
            pixel_audit(os.path.join(figs, os.path.basename(f["figure"])), au,
                        label + "/fresh")

        sys.stdout.write("figures: %d, matplotlib %s%s\n"
                         % (len(committed["figures"]), committed["matplotlib"],
                            "" if same_build else " (local %s: PNG bytes reported only)"
                            % fresh["matplotlib"]))
        sys.stdout.write("mathtext-drawn labels (invisible to a text search, covered by "
                         "the canvas check): %d figures\n" % len(MATHTEXT_LABELS))
        sys.stdout.write("figure checks: %d run, %d failed\n"
                         % (len(au.rows), au.failed))
        for ok, name, detail in au.rows:
            if not ok:
                sys.stdout.write("FAIL %s: %s\n" % (name, detail))
        return 1 if au.failed else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
