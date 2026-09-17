#!/usr/bin/env python3
"""Issue #47 -- figures, generated from the committed artefacts by the standard library alone.

    python3 figures/make_figures_v1.py                 # (re)write every figure
    python3 figures/make_figures_v1.py --check         # fail if a committed figure is not what this produces
    python3 figures/make_figures_v1.py --selftest      # mutation battery: each planted defect must fail

WHY THIS FILE EXISTS.  The journal's presentation bar requires >= 1 figure visualizing the core outcome,
committed under `papers/issue-<N>/figures/` AND embedded in the manuscript as `![caption](figures/<file>)`
with a caption stating what it shows.  This package shipped none, and -- the part worth recording -- no
check noticed: the manuscript's own checker bound typed counts, section references and the roadmap, and
the README checker bound the README's numbers, so a carrier with *no* figure satisfied every read
vacuously.  A bar item whose object is absent is not satisfied by the absence; it is unread.  So the
figure is generated from the artefacts (never hand-drawn), its bytes are reproduced by this script, and
`manuscript_check_v1.py` now reads the embed side of the same requirement.

WHY SVG, AND WHY HERE.  The package's reproduction spec promises one CPU-only command on the standard
library with no network and no `matplotlib`.  A figure that needed a plotting library would either
falsify that promise or sit outside the reproducible path.  Scalable Vector Graphics is text, so this
script writes it with string formatting alone: deterministic (no timestamps, no ids, no locale-dependent
formatting), byte-comparable, and rendered by every viewer that renders an image at all.

TEXT THAT FITS IS A PROPERTY, SO IT IS MEASURED.  A figure is drawn in a box, and a string that leaves
the box is silently clipped by the renderer rather than reported by anything -- the first version of this
file overflowed the canvas on two lines and looked correct in its own source.  Every string is therefore
measured against the canvas as it is emitted (an advance-width estimate per character, monospace spans
counted at their own width) and a string whose box leaves the drawing area raises instead of drawing.
The estimate is approximate; the assertion is not decoration, it is the difference between a figure that
fits and a figure that was *going* to fit.

WHAT FIGURE 1 CARRIES, AND WHY THAT RESULT.  The review's Q4 asked which of the four results the figure
would carry; it carries **result 1**, the witness, because the witness is the paper's sharpest claim and
the one the other three are measured against: two arms with the *same multiset of |error|* by
construction, whose realized losses differ.  A figure of an identity is not a picture of a curve, so the
figure states the two halves the witness is made of, in the two panels the claim has:

  * **top panel** -- the *identity*: the largest scalar-feature gap between the arms, over every one of
    the 39 blocks.  It is `0.0e+00` in every block, by construction, and the panel is drawn so that a
    reader sees that this is not a small number but an exact zero.
  * **bottom panel** -- the *gap*: each block's realized loss difference between the arms, in units of
    **that block's own** cluster-unit minimum detectable effect.  The dashed line is 1 -- a block's own
    resolution -- so a mark above it is a difference the block can resolve.  The blocks that are not
    above it are the 8 where the two arms did not separate at all (the error-free profile and the
    coincident-arm cases), drawn as hollow marks on the zero line rather than dropped: a control belongs
    in the picture, not in a footnote.
"""
import copy
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

PROBLEMS = ("ski", "paging", "sched")
PROBLEM_LABEL = {"ski": "ski rental", "paging": "paging", "sched": "scheduling"}
# One colour per problem, chosen to differ in lightness as well as hue, so the figure survives greyscale.
PROBLEM_FILL = {"ski": "#3b6ea5", "paging": "#b3702a", "sched": "#4a7c59"}

W, H = 980, 540
LEFT, RIGHT = 160, 26
MARGIN = 2.0
ADV = 0.530          # average advance width per character, in em, for the sans face used here
ADV_MONO = 0.600     # ditto for the monospace spans


def load():
    with io.open(os.path.join(PKG, "sufficiency_v1_results.json"), encoding="utf-8") as fh:
        suf = json.load(fh)
    with io.open(os.path.join(PKG, "canonical_results.json"), encoding="utf-8") as fh:
        can = json.load(fh)
    return suf, can


def blocks_by_problem(suf):
    """The witness's blocks, grouped by problem in a fixed order, each group sorted by profile name.

    The ORDER is part of the figure's identity: sorting by a set's iteration order would make the file
    depend on the interpreter, and a figure that differs between two runs of the same command is not a
    reproducible artefact.  Sorted by (problem, profile) here, explicitly.
    """
    out = {}
    for p in PROBLEMS:
        rows = [b for b in suf["part_B_matched_magnitude_witness"]["blocks"] if b["problem"] == p]
        out[p] = sorted(rows, key=lambda b: b["profile"])
    return out


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def plain(markup):
    """The string a reader sees: tags removed, monospace spans kept as text."""
    out, depth = [], 0
    i = 0
    while i < len(markup):
        if markup[i] == "<":
            if markup.startswith("<tspan", i):
                depth += 1
            elif markup.startswith("</tspan", i):
                depth -= 1
            i = markup.index(">", i) + 1
            continue
        out.append(markup[i])
        i += 1
    return "".join(out)


def est_width(markup, size):
    """Estimated advance width of a rendered string, in user units.

    Tags contribute nothing; a monospace span contributes its own advance and its own size only when the
    span sets one, which this figure never does.  The estimate is deliberately generous (a reader who
    measures the rendered text should find it narrower than this, never wider).
    """
    total = 0.0
    i = 0
    mono = 0
    while i < len(markup):
        if markup[i] == "<":
            if markup.startswith("<tspan", i):
                mono += 1
            elif markup.startswith("</tspan", i):
                mono -= 1
            i = markup.index(">", i) + 1
            continue
        total += (ADV_MONO if mono else ADV) * size
        i += 1
    return total


class Canvas(object):
    """An SVG document that refuses to draw outside itself."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []
        self.problems = []

    def raw(self, s):
        self.parts.append(s)

    def text(self, x, y, size, fill, body, anchor="start", extra="", box=None):
        """Draw a string and check the box it occupies.

        `box` overrides the computed box for text whose rendered extent is not its horizontal extent --
        a rotated axis title, where the estimate below would measure the wrong axis and either pass a
        string that runs off the top or, as it did first, reject one that fits.  The override is a claim
        about the render, so it is written by the caller that knows the transform rather than guessed.
        """
        self.parts.append('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"%s>%s</text>'
                          % (x, y, size, fill, anchor, extra, body))
        w = est_width(body, float(size))
        x0 = x if anchor == "start" else (x - w if anchor == "end" else x - w / 2.0)
        bx0, bx1, by0, by1 = x0, x0 + w, float(y) - float(size), float(y) + 3.0
        if box is not None:
            bx0, bx1, by0, by1 = box
        self._fit("text %r" % plain(body)[:46], bx0, bx1, by0, by1)

    def rect(self, x, y, w, h):
        self.parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"/>' % (x, y, w, h))
        self._fit("rect", float(x), float(x) + float(w), float(y), float(y) + float(h))

    def mark(self, s, x0, x1, y0, y1, what):
        self.parts.append(s)
        self._fit(what, x0, x1, y0, y1)

    def _fit(self, what, x0, x1, y0, y1):
        if x0 < -MARGIN or x1 > self.w + MARGIN or y0 < -MARGIN or y1 > self.h + MARGIN:
            self.problems.append("%s: x [%.1f, %.1f], y [%.1f, %.1f]" % (what, x0, x1, y0, y1))

    def svg(self):
        if self.problems:
            raise ValueError("the figure draws outside its canvas (%d element(s)): %s"
                             % (len(self.problems), "; ".join(self.problems[:6])))
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
                'font-family="Helvetica,Arial,sans-serif">\n' % (self.w, self.h, self.w, self.h)
                + "\n".join(self.parts) + "\n</svg>\n")


def figure1(suf, can):
    """The witness: the identity (top panel) and the gap (bottom panel)."""
    groups = blocks_by_problem(suf)
    total = sum(len(v) for v in groups.values())
    mde_positive = [b for v in groups.values() for b in v if b["mde_cluster_unit"] > 0]
    ratios = [abs(b["median_ratio_diff_plus_minus"]) / b["mde_cluster_unit"] for b in mde_positive]
    ymax = max(ratios) * 1.08
    scalar_gap = max(b["max_scalar_feature_gap"] for v in groups.values() for b in v)
    fact = lambda k: can["facts"][k]["value"]
    blocks_total, blocks_above = fact("claim1.blocks_total"), fact("claim1.blocks_exceeding_own_mde")
    worst, worst_mde = fact("claim1.worst_loss_gap"), fact("claim1.worst_block_mde")
    span = W - LEFT - RIGHT
    panel_a_axis = 140.0
    panel_b_top, panel_b_h = 266.0, 168.0
    panel_b_bottom = panel_b_top + panel_b_h

    c = Canvas(W, H)
    c.rect(0, 0, W, H)
    c.text(LEFT, 28, "16", "#111", "The witness: an identity by construction, and a measured gap",
           extra=' font-weight="bold"')
    c.text(LEFT, 48, "12", "#444",
           "Two arms carry the same multiset of |error| in every block, differing only in its sign.")
    c.text(LEFT, 64, "12", "#444",
           "The two panels are the two halves of the claim that the scalar error is not sufficient.")

    # ---------------- Panel A: the identity ----------------
    c.text(LEFT, 92, "13", "#111",
           "(A) the identity &#8212; largest scalar-feature gap between the arms, over all %d blocks"
           % total, extra=' font-weight="bold"')
    for i in range(total):
        x = LEFT + span * (i + 0.5) / total
        c.mark('<circle cx="%.2f" cy="%.1f" r="3.1" fill="#3b6ea5"><title>block %d: scalar-feature gap '
               '= %.1e</title></circle>' % (x, panel_a_axis, i + 1, scalar_gap),
               x - 3.1, x + 3.1, panel_a_axis - 3.1, panel_a_axis + 3.1, "panel A mark")
    c.mark('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#888" stroke-width="1"/>'
           % (LEFT, panel_a_axis, LEFT + span, panel_a_axis),
           LEFT, LEFT + span, panel_a_axis - 0.5, panel_a_axis + 0.5, "panel A axis")
    c.text(LEFT, 166, "12", "#111",
           "every mark sits on the axis above, and the largest gap over all %d blocks is "
           "<tspan font-weight=\"bold\">%.1e</tspan>" % (total, scalar_gap), extra=' font-style="italic"')
    c.text(LEFT, 183, "11.5", "#666",
           "an exact zero, by construction: no scalar feature of |error| can separate the arms")

    # ---------------- Panel B: the gap ----------------
    c.text(LEFT, 212, "13", "#111",
           "(B) the gap &#8212; realized loss difference between the arms, in units of each "
           "block&#8217;s own resolution", extra=' font-weight="bold"')
    c.text(LEFT, 230, "11.5", "#444",
           "a mark above the dashed line is a difference its own block can resolve")
    c.text(LEFT + span, 230, "11.5", "#666",
           "%d of %d blocks" % (blocks_above, blocks_total), anchor="end")
    c.text(LEFT, 248, "11.5", "#444",
           "deepest gap %.4f competitive-ratio units against an MDE of %.4f &#8212; %.0f&#215; its own "
           "resolution" % (worst, worst_mde, abs(worst) / worst_mde))

    yticks = [ymax * f for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
    for v in yticks:
        y = panel_b_bottom - panel_b_h * (v / ymax)
        if 0 < v < ymax:
            c.mark('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#eeeeee" stroke-width="1"/>'
                   % (LEFT, y, LEFT + span, y), LEFT, LEFT + span, y - 0.5, y + 0.5, "gridline")
    yr = panel_b_bottom - panel_b_h * (1.0 / ymax)
    c.mark('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#c0392b" stroke-width="1.6" '
           'stroke-dasharray="6 4"/>' % (LEFT, yr, LEFT + span, yr),
           LEFT, LEFT + span, yr - 0.8, yr + 0.8, "resolution line")
    c.mark('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#333" stroke-width="1.2"/>'
           % (LEFT, panel_b_bottom, LEFT + span, panel_b_bottom),
           LEFT, LEFT + span, panel_b_bottom - 0.6, panel_b_bottom + 0.6, "x axis")
    c.mark('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#333" stroke-width="1.2"/>'
           % (LEFT, panel_b_top, LEFT, panel_b_bottom),
           LEFT - 0.6, LEFT + 0.6, panel_b_top, panel_b_bottom, "y axis")
    rot_x, rot_y = LEFT - 90, panel_b_top + panel_b_h / 2.0
    rot_w = est_width("|loss gap| / own cluster MDE", 11)
    c.text(rot_x, rot_y, "11", "#333", "|loss gap| / own cluster MDE", anchor="middle",
           extra=' transform="rotate(-90 %d %.1f)"' % (rot_x, rot_y),
           box=(rot_x - 6, rot_x + 6, rot_y - rot_w / 2.0, rot_y + rot_w / 2.0))
    for v in yticks:
        y = panel_b_bottom - panel_b_h * (v / ymax)
        if abs(v - 1.0) < 1e-9:
            continue
        c.text(LEFT - 6, y + 3.5, "10.5", "#555", "%.2f" % v, anchor="end")
    c.text(LEFT - 6, yr + 3.5, "10.5", "#c0392b", "1.00 = own resolution", anchor="end")

    idx = 0
    for p in PROBLEMS:
        rows = groups[p]
        xs = []
        for b in rows:
            x = LEFT + span * (idx + 0.5) / total
            xs.append(x)
            if b["mde_cluster_unit"] > 0:
                v = abs(b["median_ratio_diff_plus_minus"]) / b["mde_cluster_unit"]
                y = panel_b_bottom - panel_b_h * (min(v, ymax) / ymax)
                c.mark('<rect x="%.2f" y="%.1f" width="9.5" height="%.1f" fill="%s"><title>%s / %s: '
                       '|gap| = %.5f, own MDE = %.5f, ratio %.2f, %d pairs</title></rect>'
                       % (x - 4.75, y, panel_b_bottom - y, PROBLEM_FILL[p], esc(p), esc(b["profile"]),
                          abs(b["median_ratio_diff_plus_minus"]), b["mde_cluster_unit"], v, b["n_pairs"]),
                       x - 4.75, x + 4.75, y, panel_b_bottom, "bar %s/%s" % (p, b["profile"]))
            else:
                c.mark('<circle cx="%.2f" cy="%.1f" r="3.4" fill="none" stroke="%s" stroke-width="1.4">'
                       '<title>%s / %s: the arms did not separate (gap 0, own MDE 0) &#8212; a zero-error '
                       'control case</title></circle>' % (x, panel_b_bottom, PROBLEM_FILL[p], esc(p),
                                                          esc(b["profile"])),
                       x - 3.4, x + 3.4, panel_b_bottom - 3.4, panel_b_bottom + 3.4, "hollow mark")
            idx += 1
        cx = (xs[0] + xs[-1]) / 2.0
        c.text(cx, panel_b_bottom + 20, "12", PROBLEM_FILL[p],
               "%s (%d blocks)" % (PROBLEM_LABEL[p], len(rows)),
               anchor="middle", extra=' font-weight="bold"')
    for k in (1, 2):
        x = LEFT + span * (13 * k) / total
        c.mark('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#dddddd" stroke-width="1"/>'
               % (x, panel_b_top, x, panel_b_bottom), x - 0.5, x + 0.5, panel_b_top, panel_b_bottom,
               "group separator")

    c.text(LEFT, H - 48, "11.5", "#444",
           "Hollow marks: the blocks where the two arms did not separate at all (gap 0, own MDE 0)")
    c.text(LEFT, H - 32, "11.5", "#444",
           "&#8212; the zero-error and coincident-arm controls, kept in the picture.")
    c.text(LEFT + span, H - 32, "11.5", "#666",
           "The file is regenerated and byte-compared in <tspan>reproduce.sh</tspan>.", anchor="end")
    c.text(LEFT, H - 13, "11", "#666",
           "Every value is recomputed from the committed artefact "
           "(<tspan>sufficiency_v1_results.json</tspan>) by "
           "<tspan>figures/make_figures_v1.py</tspan>.")
    return c.svg()


FIGURES = {"fig1_witness.svg": figure1}


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--check" in argv:
        suf, can = load()
        bad = 0
        for name, fn in sorted(FIGURES.items()):
            path = os.path.join(HERE, name)
            if not os.path.exists(path):
                print("FAIL   %s: the committed figure is missing" % name)
                bad += 1
                continue
            with io.open(path, encoding="utf-8") as fh:
                have = fh.read()
            if have != fn(suf, can):
                print("FAIL   %s: the committed figure is not what this script produces from the "
                      "artefacts (regenerate with: python3 figures/make_figures_v1.py)" % name)
                bad += 1
                continue
            print("OK     %s: regenerated byte-identically (%d bytes)" % (name, len(have.encode())))
        print("figure check: %d figure(s), %d failed" % (len(FIGURES), bad))
        return 1 if bad else 0
    written = {}
    for name, fn in sorted(FIGURES.items()):
        suf, can = load()
        text = fn(suf, can)
        with io.open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        written[name] = text
    for name in sorted(written):
        print("wrote %s (%d bytes)" % (name, len(written[name].encode())))
    return 0


def selftest():
    """One planted defect per property the figure has to survive, each required to move the output.

    The battery is what makes `--check` more than decoration: without it, a figure nothing could ever
    disagree with would pass this script and every other step.  Each case breaks ONE property and prints
    which -- so a reader can see each check is reading the object it names rather than a neighbour of it.
    """
    suf, can = load()
    base = figure1(suf, can)

    def mutant_mde():
        """Scale one block's MDE in the artefact copy and require the figure to move.

        This is the case that binds the lower panel's UNIT: every bar is |gap| divided by THAT block's own
        MDE, so scaling one block's MDE must change that block's bar and leave the others where they are.
        An earlier version of this case searched the rendered text for a phrase the layout no longer
        carries, and reported "the planted defect changed nothing" -- a mutation anchored on a string
        rather than on the property, which is exactly the defect this file exists to avoid.
        """
        other = copy.deepcopy(suf)
        other["part_B_matched_magnitude_witness"]["blocks"][0]["mde_cluster_unit"] *= 10.0
        return figure1(other, can)

    def mutant_gap():
        """Widen one block's realized gap by a factor and require its bar to move."""
        other = copy.deepcopy(suf)
        other["part_B_matched_magnitude_witness"]["blocks"][3]["median_ratio_diff_plus_minus"] *= 1.5
        return figure1(other, can)

    def mutant_count():
        """A wrong count in the artefact the figure reads must change the printed count."""
        other = copy.deepcopy(can)
        other["facts"]["claim1.blocks_exceeding_own_mde"]["value"] = 7
        return figure1(suf, other)

    def mutant_overflow():
        """A string that leaves the canvas must be REPORTED, not clipped.

        This is the case for the property the first version of this file did not have: two of its lines
        drew past the right edge and the file looked correct in its own source.
        """
        wide = Canvas(100, 60)
        wide.text(50, 30, "12", "#000", "a line far wider than the canvas it is drawn in")
        try:
            wide.svg()
        except ValueError:
            return "raised"
        return "silently drawn"

    # Each case states what it EXPECTS.  A battery in which "nothing moved" is always a failure cannot
    # test determinism -- the one property whose evidence is that nothing moves -- and a battery whose
    # expectation is only in its author's head cannot be read by anyone else.
    cases = [
        ("the ratio is read from each block's own MDE", mutant_mde, True),
        ("the bar height is read from the block's gap", mutant_gap, True),
        ("the count above the line is read, not typed", mutant_count, True),
        ("a string that leaves the canvas is reported", mutant_overflow, True),
        ("determinism: two generations in one process agree", lambda: figure1(*load()), False),
    ]
    bad = 0
    for name, fn, expect_change in cases:
        try:
            other = fn()
        except Exception as exc:                                   # a case that cannot run is a failure
            print("FAIL   %-52s the case raised %s" % (name, exc))
            bad += 1
            continue
        moved = other != base
        if moved != expect_change:
            print("FAIL   %-52s expected %s, got %s"
                  % (name, "a change" if expect_change else "no change",
                     ("a change (%s)" % str(other)[:18]) if moved else "no change"))
            bad += 1
        else:
            print("PASS   %-52s %s" % (name, "moved" if moved else "byte-identical"))
    print("figure selftest: %d case(s), %d failure(s)" % (len(cases), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
