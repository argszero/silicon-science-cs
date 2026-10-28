#!/usr/bin/env python3
"""The core outcome, drawn and tabulated from the committed artifacts.

Two jobs, one source: `decay.json` gives the survival curve by range syntax, `rates.json` gives
the four rates with their intervals. Neither number is typed here -- both are read from the
artifact and the artifact is what the paper quotes, so the figure and the table cannot disagree
with the text without this script failing.

Design notes that are rules, not taste:

* **stdlib only.** This package declares zero third-party imports (envgate reads 0) and the
  editorial triage ran it as "standard library only, no venv, no network". A plotting library
  would buy nothing here and would cost that property plus a hash-salted, date-stamped output.
  The SVG is written by hand with fixed decimals, so two runs produce identical bytes.
* **A series that cannot be measured is labelled, not omitted.** PyPI has no declaration in the
  panel that is determined at k = 0, so its at-risk set is empty at every horizon and the curve
  is NOT RUN. Drawing nothing there would read as "PyPI is fine"; the figure says so in words.
* **The figure asserts.** Before writing, the script checks the ordering the paper's §7.3 claims
  (`exact` at 12 months is above `caret`), that every series starts at 1.000 by construction of
  the at-risk set, and that every plotted point is the artifact's own rate. A plot of numbers
  nobody re-read is a decoration.

Usage:
    python3 make_figures.py              # write figures/decay-curve.svg, print FIGURE: ...
    python3 make_figures.py --table      # print the rates table (markdown) to stdout
    python3 make_figures.py --check-table  # compare manuscript.md's table block to the render
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures", "decay-curve.svg")
MANUSCRIPT = os.path.join(HERE, "manuscript.md")

OPEN_MARK = "<!-- table:rates -->"
CLOSE_MARK = "<!-- /table:rates -->"

# The order the strata are drawn in: bounded pin, bounded range, unbounded range, and the
# declaration-level series the others decompose. Colours are fixed, not cycled.
SERIES = [
    ("declaration", "declaration (all edges)", "#111111", ""),
    ("exact", "exact pin", "#1f6f3f", ""),
    ("tilde", "tilde range", "#8a6d1f", "6,4"),
    ("caret", "caret range", "#9c2b2b", ""),
]


def load():
    decay = json.load(open(os.path.join(HERE, "decay.json"), encoding="utf-8"))
    rates = json.load(open(os.path.join(HERE, "rates.json"), encoding="utf-8"))
    return decay, rates


def pct(x):
    return "%.1f%%" % (100.0 * x)


def ci(pair):
    return "[%.1f, %.1f]" % (100.0 * pair[0], 100.0 * pair[1])


def count_from_share(share, denom, label):
    """An integer count the artifact stores only as a share.

    The artifact keeps the share; the table prints the count, because a rate beside no counts is
    a number a reader cannot check. The derivation is asserted rather than rounded silently.
    """
    n = int(round(share * denom))
    if abs(share - n / float(denom)) > 1e-6:
        raise SystemExit("%s: share %r over %d is not a whole count (%r)"
                         % (label, share, denom, share * denom))
    return n


# ---------------------------------------------------------------- the table

def render_table(rates):
    """The four rates, each with the counts it is a rate of and its Wilson interval."""
    out = [OPEN_MARK,
           "| measure | npm | PyPI |",
           "|---|---|---|"]
    rows = [
        ("edges whose range admits more than one version (depth 1)",
         ("ambiguous_edges", "edges", "ambiguous_share", "ambiguous_wilson")),
        ("…of those, whose alternative versions constrain further dependencies differently",
         ("ambiguous_with_closure_difference", "ambiguous_edges",
          "closure_difference_share", "closure_difference_wilson")),
        ("…of those, whose alternative versions add or remove a dependency",
         (None, "ambiguous_edges", "closure_shape_share", "closure_shape_wilson")),
        ("declarations at risk that lose determination within 12 months",
         ("declarations_under_determined", "declarations_with_edges",
          "declarations_share_under_determined_at_risk",
          "declarations_under_determined_wilson_at_risk")),
    ]
    for label, (num_key, den_key, share_key, wilson_key) in rows:
        cells = []
        for eco in ("npm", "pypi"):
            v = rates["ecosystems"][eco]
            den = v[den_key]
            num = v[num_key] if num_key else count_from_share(v[share_key], den, share_key)
            cells.append("%d/%d = %s %s" % (num, den, pct(v[share_key]), ci(v[wilson_key])))
        out.append("| %s | %s | %s |" % (label, cells[0], cells[1]))
    out.append(CLOSE_MARK)
    return "\n".join(out)


def check_table(rates):
    text = open(MANUSCRIPT, encoding="utf-8").read()
    if text.count(OPEN_MARK) != 1 or text.count(CLOSE_MARK) != 1:
        print("  [FAIL] manuscript.md carries %d open and %d close table markers, expected 1 and 1"
              % (text.count(OPEN_MARK), text.count(CLOSE_MARK)))
        return 1
    start = text.index(OPEN_MARK)
    end = text.index(CLOSE_MARK) + len(CLOSE_MARK)
    got = text[start:end]
    want = render_table(rates)
    if got != want:
        print("  [FAIL] the manuscript's table is not the one the artifacts render")
        for a, b in zip(got.split("\n"), want.split("\n")):
            if a != b:
                print("         manuscript: %s" % a)
                print("         rendered  : %s" % b)
        return 1
    print("  [ok]   TABLE: IN SYNC (%d rows, every cell a count, a share and an interval from rates.json)"
          % (len(want.split("\n")) - 4))
    return check_prose_rates(text, rates)


def check_prose_rates(text, rates):
    """Every `X% [a, b]` the results section prints must be a rate the artifacts hold.

    A table that is generated does not protect the sentence beside it: this package shipped
    `15.5% [11.3, 21.0]` while the artifact's lower bound was `0.1124951` -- 11.2495 %, which
    rounds to **11.2**. The editorial spot-check compared `0.1125` against `11.3` and passed it,
    which is what a bound read to four decimals and then to one can do. So the prose is read too:
    the triple (share, lower, upper) is taken from the sentence and matched against the pairs the
    artifact holds, at the precision the sentence prints.
    """
    held = set()
    for eco, v in rates["ecosystems"].items():
        for key, val in v.items():
            if key.endswith("_share") and isinstance(val, float):
                w = v.get(key.replace("_share", "_wilson"))
                if isinstance(w, list) and len(w) == 2:
                    held.add((round(100 * val, 1), round(100 * w[0], 1), round(100 * w[1], 1)))
    body = text[text.index("## 7. Results"):text.index("## 8. Related work")]
    body = body.replace(render_table(rates), "")        # the table is checked above
    pat = re.compile(r"(\d+\.\d)%\s*\[(\d+\.\d+),\s*(\d+\.\d+)\]")
    total = 0
    bad = 0
    for m in pat.finditer(body):
        total += 1
        triple = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        if triple not in held:
            bad += 1
            near = sorted(held, key=lambda h: abs(h[0] - triple[0]))[:1]
            print("  [FAIL] the results section prints %s%% [%s, %s], which no artifact holds "
                  "(nearest rate the artifacts hold: %.1f%% [%.1f, %.1f])"
                  % (m.group(1), m.group(2), m.group(3), near[0][0], near[0][1], near[0][2]))
    if bad:
        return 1
    print("  [ok]   PROSE: IN SYNC (%d rate-with-interval statements in §7, all of them the "
          "artifact's own numbers)" % total)
    return 0


# ---------------------------------------------------------------- the figure

W, H = 780, 470
X0, X1 = 78, 600          # plot area
Y0, Y1 = 40, 372
KMAX = 12
YLO, YHI = 0.70, 1.00


def sx(k):
    return X0 + (X1 - X0) * k / float(KMAX)


def sy(rate):
    return Y1 - (Y1 - Y0) * (rate - YLO) / (YHI - YLO)


def render_figure(decay):
    npm = decay["ecosystems"]["npm"]
    series = {}
    series["declaration"] = npm["declaration_survival"]
    for name in ("exact", "tilde", "caret"):
        series[name] = npm["strata"][name]
    pypi = decay["ecosystems"]["pypi"]

    # --- assertions, before a pixel is written ------------------------------------------------
    problems = []
    for name, rows in series.items():
        if [r["k"] for r in rows] != list(range(KMAX + 1)):
            problems.append("%s does not carry a rate at every horizon 0..%d" % (name, KMAX))
        if any(r["verdict"] != "measured" or r["rate"] is None for r in rows):
            problems.append("%s carries a horizon that is not measured" % name)
        if rows[0]["rate"] != 1.0:
            problems.append("%s does not start at 1.000, so its at-risk set is not a k = 0 "
                            "singleton cohort" % name)
        # the at-risk set is fixed at k = 0 by definition; a drifting denominator is a different
        # population at each k and the curve would not be a survival curve
        if len({r["at_risk"] for r in rows}) != 1:
            problems.append("%s: the at-risk set changes across horizons" % name)
    if series["exact"][-1]["rate"] <= series["caret"][-1]["rate"]:
        problems.append("the claimed ordering does not hold: exact %.3f <= caret %.3f at k = %d"
                        % (series["exact"][-1]["rate"], series["caret"][-1]["rate"], KMAX))
    if pypi["declaration_survival"][0]["verdict"] != "NOT RUN":
        problems.append("PyPI's series is not marked NOT RUN, so the 'no decay to measure' "
                        "reading in §7.3 has no carrier in the artifact")
    if problems:
        for p in problems:
            print("  [FAIL] %s" % p)
        return 1

    # --- the drawing -------------------------------------------------------------------------
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]

    # plot frame and gridlines
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#c8c8c8"/>'
             % (X0, Y0, X1 - X0, Y1 - Y0))
    for t in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00):
        y = sy(t)
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#eeeeee"/>' % (X0, y, X1, y))
        o.append('<text x="%d" y="%.1f" font-size="11" fill="#555555" text-anchor="end">%.2f</text>'
                 % (X0 - 8, y + 4, t))
    for k in range(0, KMAX + 1, 3):
        o.append('<text x="%.1f" y="%d" font-size="11" fill="#555555" text-anchor="middle">%d</text>'
                 % (sx(k), Y1 + 18, k))
    o.append('<text x="%.1f" y="%d" font-size="12" fill="#333333" text-anchor="middle">'
             'horizon k (publishes after the declaration)</text>' % ((X0 + X1) / 2.0, Y1 + 38))
    o.append('<text x="16" y="%.1f" font-size="12" fill="#333333" transform="rotate(-90 16 %.1f)" '
             'text-anchor="middle">share of edges still determined</text>'
             % ((Y0 + Y1) / 2.0, (Y0 + Y1) / 2.0))
    o.append('<text x="%d" y="22" font-size="13" fill="#111111">npm: survival of a declared edge, '
             'by range syntax (k = 0 cohort)</text>' % X0)

    for name, label, colour, dash in SERIES:
        rows = series[name]
        pts = " ".join("%.1f,%.1f" % (sx(r["k"]), sy(r["rate"])) for r in rows)
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"%s/>'
                 % (pts, colour, d))
        for r in rows:
            if r["k"] in (0, 6, KMAX):
                o.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s"/>'
                         % (sx(r["k"]), sy(r["rate"]), colour))

    # legend outside the plot area, with the 12-month value and its n on each line
    lx, ly = X1 + 24, Y0 + 6
    o.append('<text x="%d" y="%d" font-size="11" fill="#555555">at k = 12 (n at risk)</text>'
             % (lx, ly))
    for i, (name, label, colour, dash) in enumerate(SERIES):
        y = ly + 22 + i * 20
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"%s/>'
                 % (lx, y - 4, lx + 22, y - 4, colour, d))
        last = series[name][-1]
        o.append('<text x="%d" y="%d" font-size="11" fill="#333333">%s %.3f (n=%d)</text>'
                 % (lx + 28, y, label, last["rate"], last["at_risk"], ))

    # the absent series is named. "No points" and "flat at 1.000" are different facts and a
    # reader cannot tell them apart from an empty region.
    y = ly + 22 + len(SERIES) * 20 + 18
    o.append('<text x="%d" y="%d" font-size="11" fill="#9c2b2b">PyPI: NOT RUN</text>' % (lx, y))
    for j, line in enumerate([
            "no declaration in the panel",
            "is determined at k = 0, so the",
            "at-risk set is empty at every",
            "horizon. This is an absence of",
            "population, not a rate of zero."]):
        o.append('<text x="%d" y="%d" font-size="10" fill="#666666">%s</text>'
                 % (lx, y + 15 + j * 13, line))

    o.append('<text x="%d" y="%d" font-size="10" fill="#666666">'
             'exhaustive enumeration over the committed panel; no sampling, no seeds. '
             'Drawn from decay.json by make_figures.py.</text>' % (X0, H - 14))
    o.append("</svg>")

    os.makedirs(os.path.dirname(FIG), exist_ok=True)
    with open(FIG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o) + "\n")

    print("  [ok]   FIGURE: IN SYNC (%d series x %d horizons; caret %.3f vs exact %.3f at k=%d, "
          "declaration %.3f (n=%d); PyPI NOT RUN and labelled)"
          % (len(SERIES), KMAX + 1, series["caret"][-1]["rate"], series["exact"][-1]["rate"],
             KMAX, series["declaration"][-1]["rate"], series["declaration"][-1]["at_risk"]))
    return 0


def main(argv):
    decay, rates = load()
    if "--table" in argv:
        print(render_table(rates))
        return 0
    if "--check-table" in argv:
        return check_table(rates)
    return render_figure(decay)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
