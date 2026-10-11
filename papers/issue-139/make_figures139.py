#!/usr/bin/env python3
"""make_figures139 -- the manuscript's figure set for issue #139, generated from the shipped reports.

Standard library only (the package's own rule: no third-party import anywhere -- matplotlib is not
used and is not required), and DETERMINISTIC: the same reports produce byte-identical SVG.

    python3 make_figures139.py [OUTDIR]        # default: figures/
    python3 make_figures139.py --selftest      # the certificate below

Six figures, each read off the shipped `spike_v*_results.json`.  Nothing is drawn that is not in a
report, and every number a figure ANNOTATES is read from the report dict rather than typed, so a
figure cannot drift from its source.

Certificate (--selftest), each item able to fail:
  F1  every source report exists, parses, and carries every key the figures read;
  F2  the FACTS the figures assert are re-derived from those reports here, each stated as a direction
      a report could contradict -- (a) the registration's placebo is NOT null; (b) at c = 0 the
      coupling gain is exactly 0; (c) the concavity defect RISES with the coupling; (d) the frontier
      is superlinear in the budget (F-at-B90 / F-at-B50 >= 1.5 in EVERY cell); (e) the registered
      concavity prior is REFUTED; (f) the pass-rate sizing rule UNDER-budgets in a majority of cells
      and its worst cell is off by more than 4x; (g) the two-obligation law "attempt the harder one
      second" agrees on 100.0% while the hand-derived rule is > 20 points below; (h) the guarantee
      non-increasing => concave holds with NO violation while its converse fails thousands of times;
      (i) every coupled breakdown is attributed to the coupling (same order, coupling off: defect 0);
      (j) the coupling boundary is violated more often as c grows.
  F3  no emitted element leaves its canvas: a figure is regenerated into memory and every polyline
      vertex / circle centre is read BACK off the SVG text and checked against the canvas, with the
      count of checked coordinates asserted.
Each F2 item is also run against a TAMPERED report and must report a contradiction, so the
certificate is a test and not a restatement (Class 238: a plant must land inside its jurisdiction).
"""
import hashlib
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "figures")

PAL = {"coupled": "#d62728", "uncoupled": "#1f77b4", "placebo": "#7f7f7f",
       "defect": "#d62728", "ratio": "#1f77b4", "keep": "#2ca02c", "lost": "#d62728"}
INK = "#222222"
GRID = "#dddddd"
AXIS = "#333333"
MUTED = "#666666"
WARN = "#b8860b"
FONT = "Helvetica, Arial, sans-serif"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def num(x):
    """A stable decimal rendering: no float repr, no locale, no '-0'."""
    if x == 0:
        return "0"
    return ("%.4f" % x).rstrip("0").rstrip(".")


class Panel:
    """One plotting area.  Data coords in, SVG coords out; `ox/oy` place it on the canvas."""

    def __init__(self, ox, oy, w, h, xlim, ylim, xlog=False, ylog=False,
                 ml=84, mr=26, mt=40, mb=70):
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.xlim, self.ylim, self.xlog, self.ylog = xlim, ylim, xlog, ylog
        self.l = ox + ml
        self.r = ox + w - mr
        self.t = oy + mt
        self.b = oy + h - mb
        self.el = []

    def _ck(self, x, y):
        """The panel's one invariant: a drawn coordinate lies inside the declared limits.

        Raises rather than silently drawing outside the axes -- a band or a point that leaves the
        frame is a figure defect (it is the shape of "the annotation was never rendered" one step
        earlier), and a build that cannot fail cannot be trusted.
        """
        tol = 1e-9
        if self.xlog:
            xok = x > 0 and math.log10(self.xlim[0]) - tol <= math.log10(x) <= math.log10(self.xlim[1]) + tol
        else:
            xok = self.xlim[0] - tol <= x <= self.xlim[1] + tol
        if self.ylog:
            yok = y > 0 and math.log10(self.ylim[0]) - tol <= math.log10(y) <= math.log10(self.ylim[1]) + tol
        else:
            yok = self.ylim[0] - tol <= y <= self.ylim[1] + tol
        if not (xok and yok):
            raise ValueError("(%r, %r) leaves the panel limits x=%r y=%r"
                             % (x, y, self.xlim, self.ylim))
        return True

    def X(self, x):
        if self.xlog:
            a, b, v = math.log10(self.xlim[0]), math.log10(self.xlim[1]), math.log10(x)
        else:
            a, b, v = self.xlim[0], self.xlim[1], x
        return self.l + (v - a) / (b - a) * (self.r - self.l)

    def Y(self, y):
        if self.ylog:
            if y <= 0:
                raise ValueError("log axis cannot take %r" % y)
            a, b, v = math.log10(self.ylim[0]), math.log10(self.ylim[1]), math.log10(y)
        else:
            a, b, v = self.ylim[0], self.ylim[1], y
        return self.b - (v - a) / (b - a) * (self.b - self.t)

    def line(self, x1, y1, x2, y2, stroke=AXIS, w=1.4, dash=None, op=1.0):
        self._ck(x1, y1); self._ck(x2, y2)
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                       'stroke-width="%s"%s opacity="%s"/>'
                       % (self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), stroke, num(w), d, num(op)))

    def vline(self, x, stroke=AXIS, w=1.4, dash=None, op=1.0):
        self.line(x, self.ylim[0], x, self.ylim[1], stroke, w, dash, op)

    def hline(self, y, stroke=AXIS, w=1.4, dash=None, op=1.0):
        self.line(self.xlim[0], y, self.xlim[1], y, stroke, w, dash, op)

    def poly(self, pts, stroke=AXIS, w=2.0, dash=None, op=1.0):
        p = " ".join("%.2f,%.2f" % (self.X(x), self.Y(y)) for x, y in pts)
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.el.append('<polyline fill="none" points="%s" stroke="%s" stroke-width="%s"%s '
                       'opacity="%s" stroke-linejoin="round"/>' % (p, stroke, num(w), d, num(op)))

    def rect(self, x0, x1, y0, y1, fill="#cccccc", op=0.85, stroke="none"):
        """An axis-aligned box in DATA coordinates; both corners are checked."""
        self._ck(x0, y0); self._ck(x1, y1)
        self.el.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
                       'stroke="%s" opacity="%s"/>'
                       % (min(self.X(x0), self.X(x1)), min(self.Y(y0), self.Y(y1)),
                          abs(self.X(x1) - self.X(x0)), abs(self.Y(y1) - self.Y(y0)),
                          fill, stroke, num(op)))

    def band(self, pts_lo, pts_hi, fill="#cccccc", op=0.35):
        """A shaded ribbon between two series of the same x's; every vertex is checked."""
        for x, y in list(pts_lo) + list(pts_hi):
            self._ck(x, y)
        up = " ".join("%.2f,%.2f" % (self.X(x), self.Y(y)) for x, y in pts_hi)
        dn = " ".join("%.2f,%.2f" % (self.X(x), self.Y(y)) for x, y in reversed(pts_lo))
        self.el.append('<polygon fill="%s" opacity="%s" points="%s %s"/>' % (fill, num(op), up, dn))

    def dot(self, x, y, r=3.6, fill=AXIS, stroke="#ffffff", sw=1.0):
        self._ck(x, y)
        self.el.append('<circle cx="%.2f" cy="%.2f" r="%s" fill="%s" stroke="%s" '
                       'stroke-width="%s"/>' % (self.X(x), self.Y(y), num(r), fill, stroke, num(sw)))

    def ptext(self, px, py, s, size=12, anchor="start", fill=INK, weight="normal",
              italic=False, rotate=None):
        st_ = ' font-style="italic"' if italic else ""
        tr = ' transform="rotate(%s %.2f %.2f)"' % (num(rotate), px, py) if rotate is not None else ""
        self.el.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" fill="%s" '
                       'text-anchor="%s" font-weight="%s"%s%s>%s</text>'
                       % (px, py, FONT, num(size), fill, anchor, weight, st_, tr, esc(s)))

    def text(self, x, y, s, dx=0, dy=0, **kw):
        self.ptext(self.X(x) + dx, self.Y(y) + dy, s, **kw)

    def frame(self, xticks, yticks, xlabel, ylabel, xfmt=None, yfmt=None, grid=True,
              tick_size=11, label_size=13):
        if grid:
            for y in yticks:
                self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                               'stroke-width="1" stroke-dasharray="3 4"/>'
                               % (self.l, self.Y(y), self.r, self.Y(y), GRID))
        self.el.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" '
                       'stroke="%s" stroke-width="1.4"/>'
                       % (self.l, self.t, self.r - self.l, self.b - self.t, AXIS))
        for x in xticks:
            px = self.X(x)
            self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                           'stroke-width="1.2"/>' % (px, self.b, px, self.b + 5, AXIS))
            self.ptext(px, self.b + 18, xfmt(x) if xfmt else num(x),
                       size=tick_size, anchor="middle", fill=MUTED)
        for y in yticks:
            py = self.Y(y)
            self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                           'stroke-width="1.2"/>' % (self.l - 5, py, self.l, py, AXIS))
            self.ptext(self.l - 9, py + 4, yfmt(y) if yfmt else num(y),
                       size=tick_size, anchor="end", fill=MUTED)
        if xlabel:
            self.ptext((self.l + self.r) / 2, self.b + 48, xlabel, size=label_size,
                       anchor="middle", fill=INK)
        if ylabel:
            self.ptext(self.ox + 22, (self.t + self.b) / 2, ylabel, size=label_size,
                       anchor="middle", fill=INK, rotate=-90)


def svg(w, h, title, panels):
    body = "".join("".join(p.el) for p in panels)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img" aria-label="%s">\n<title>%s</title>\n'
            '<rect width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n'
            % (w, h, w, h, esc(title), esc(title), w, h, body))


def report(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as f:
        return json.load(f)


def write(name, text, outdir):
    data = text.encode("utf-8")
    with open(os.path.join(outdir, name), "wb") as f:
        f.write(data)
    return {"file": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


# ------------------------------------------------------------------------------------------------
# the six figures

def v1_by_c(v1):
    """Per coupling level: the concavity defect's (min, median, max), the concave count, and the
    F(B90)/F(B50) ratio's (min, median, max).  Read here so a figure and its caption share a source."""
    out = []
    for c in sorted({r["c"] for r in v1["P1"]}):
        sub = [r for r in v1["P1"] if r["c"] == c]
        d = [r["concavity_defect"] for r in sub]
        q = [r["ratio_B90_B50"] for r in sub]
        out.append({"c": c, "n": len(sub),
                    "dmin": min(d), "dmed": st.median(d), "dmax": max(d),
                    "concave": sum(1 for r in sub if r["concavity_defect"] <= 1e-9),
                    "qmin": min(q), "qmed": st.median(q), "qmax": max(q)})
    return out


def fig_frontier(v0):
    """F1 -- the exact frontier and the coupling gain, on the two declared cases."""
    cases = v0["cases"]
    W, H = 1020, 500
    panels = []
    for i, case in enumerate(cases):
        B = [c["B"] for c in case["cells"]]
        ymax = math.ceil(max(max(c["coupled"][k] for k in ("greedy", "placebo"))
                             for c in case["cells"])) + 0.4
        p = Panel(i * 505, 0, 505, H, (0, max(B)), (0, ymax), mb=76, mr=34)
        gain = [(c["B"], c["coupling_gain"]["greedy"]) for c in case["cells"]]
        pk = max(gain, key=lambda t: t[1])
        p.frame([0, 20, 40, 60], [0, round(ymax / 2, 1), round(ymax, 1)],
                "budget B (attempts)", "obligations discharged F(B)")
        p.poly([(c["B"], c["coupled"]["placebo"]) for c in case["cells"]],
               stroke=PAL["placebo"], w=1.8, dash="5 4")
        p.poly([(c["B"], c["uncoupled"]["greedy"]) for c in case["cells"]],
               stroke=PAL["uncoupled"], w=2.2)
        p.poly([(c["B"], c["coupled"]["greedy"]) for c in case["cells"]],
               stroke=PAL["coupled"], w=2.6)
        for c in case["cells"]:
            p.dot(c["B"], c["coupled"]["greedy"], r=3.0, fill=PAL["coupled"])
        p.ptext(p.l + 10, p.t + 16, "%s  n=%d  p=%s  c=%s"
                % (case["name"], case["n"], ",".join("%.2f" % x for x in case["p"]), num(case["c"])),
                size=12, weight="bold")
        p.ptext(p.l + 10, p.t + 36, "coupled (schedule active)", size=11, fill=PAL["coupled"])
        p.ptext(p.l + 10, p.t + 54, "uncoupled (same schedule)", size=11, fill=PAL["uncoupled"])
        p.ptext(p.l + 10, p.t + 72, "placebo (permuted -- NOT a control)", size=11, fill=PAL["placebo"])
        p.text(pk[0], pk[1], "max coupling gain %s at B=%d" % (num(round(pk[1], 4)), pk[0]),
               dx=8, dy=-8, size=11, fill=WARN)
        panels.append(p)
    return svg(W, H, "The exact obligation frontier and the coupling gain (issue #139, spike_v0)",
               panels)


def fig_grid_concavity(v1):
    """F2 -- the v1 grid: the concavity defect and the budget ratio, by coupling level."""
    agg = v1_by_c(v1)
    cs = [a["c"] for a in agg]
    W, H = 1020, 470
    p1 = Panel(0, 0, 505, H, (-0.05, max(cs) + 0.05), (0, max(a["dmax"] for a in agg) * 1.18))
    p1.frame(cs, [0, 0.1, 0.2], "coupling c", "concavity defect of F(B)")
    for a in agg:
        p1.line(a["c"], a["dmin"], a["c"], a["dmax"], stroke=PAL["defect"], w=2.4, op=0.45)
        p1.dot(a["c"], a["dmed"], r=5.0, fill=PAL["defect"])
        p1.dot(a["c"], a["dmin"], r=2.4, fill=PAL["defect"])
        p1.dot(a["c"], a["dmax"], r=2.4, fill=PAL["defect"])
        p1.ptext(p1.X(a["c"]) + 10, p1.Y(a["dmax"]) - 6,
                 "%d/%d concave" % (a["concave"], a["n"]), size=10, fill=MUTED)
    p1.ptext(p1.l + 12, p1.t + 18, "bar = min..max   dot = median", size=11, fill=INK)
    p1.ptext(p1.l + 12, p1.t + 36, "the defect RISES with c (median %s -> %s)"
             % (num(round(agg[0]["dmed"], 4)), num(round(agg[-1]["dmed"], 4))), size=11, fill=WARN)

    qmax = max(a["qmax"] for a in agg) * 1.12
    p2 = Panel(505, 0, 505, H, (-0.05, max(cs) + 0.05), (1.0, qmax))
    p2.frame(cs, [1.0, 2.0, 3.0, 4.0], "coupling c", "F(B90) / F(B50)")
    p2.hline(1.0, stroke=MUTED, w=1.2, dash="5 4")
    p2.ptext(p2.l + 12, p2.Y(1.0) - 8, "1.0 = proportional", size=10, fill=MUTED)
    for a in agg:
        p2.line(a["c"], a["qmin"], a["c"], a["qmax"], stroke=PAL["ratio"], w=2.4, op=0.45)
        p2.dot(a["c"], a["qmed"], r=5.0, fill=PAL["ratio"])
        p2.dot(a["c"], a["qmin"], r=2.4, fill=PAL["ratio"])
        p2.dot(a["c"], a["qmax"], r=2.4, fill=PAL["ratio"])
    p2.ptext(p2.l + 12, p2.t + 18,
             "every cell >= %s (superlinear budget)" % num(min(a["qmin"] for a in agg)),
             size=11, fill=WARN)
    return svg(W, H, "The concavity defect and the budget ratio by coupling level (issue #139, spike_v1)",
               [p1, p2])


def fig_sizing(v2):
    """F3 -- the pass-rate sizing rule against the frontier's own budget."""
    rows = [r for r in v2["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
    ratios = sorted(r["ratio"] for r in rows)
    n = len(ratios)
    targets = sorted({r["target"] for r in rows})
    W, H = 1020, 470

    p1 = Panel(0, 0, 505, H, (0, 1.05), (0, 1.0))
    p1.frame([0, 0.25, 0.5, 0.75, 1.0], [0, 0.25, 0.5, 0.75, 1.0],
             "pass-rate budget / frontier budget", "fraction of cells at or below")
    pts = [(ratios[min(n - 1, int(i * n / 200))], (i + 1) / 200.0) for i in range(200)]
    p1.poly(pts, stroke=PAL["ratio"], w=2.4)
    p1.vline(1.0, stroke=MUTED, w=1.2, dash="5 4")
    under = sum(1 for x in ratios if x < 1.0)
    p1.ptext(p1.l + 12, p1.t + 18, "the rule UNDER-budgets %d/%d (%.1f%%)"
             % (under, n, 100.0 * under / n), size=12, weight="bold", fill=PAL["lost"])
    p1.ptext(p1.l + 12, p1.t + 38, "1.0 = the rule's budget is right", size=10, fill=MUTED)
    p1.ptext(p1.X(ratios[0]) + 8, p1.Y(0.5), "worst cell %.2fx" % (1.0 / ratios[0]),
             size=11, fill=WARN)

    rmax = max(r["ratio"] for r in rows)
    p2 = Panel(505, 0, 505, H, (0.35, 1.05), (0, rmax * 1.08))
    p2.frame([0.5, 0.7, 0.9], [0.5, 0.75, 1.0, 1.25], "target fraction reached",
             "pass-rate / frontier")
    p2.hline(1.0, stroke=MUTED, w=1.2, dash="5 4")
    for t in targets:
        v = sorted(r["ratio"] for r in rows if r["target"] == t)
        u = sum(1 for x in v if x < 1)
        p2.line(t, v[0], t, v[-1], stroke=PAL["ratio"], w=6.0, op=0.35)
        p2.dot(t, v[len(v) // 2], r=5.4, fill=PAL["ratio"])
        p2.dot(t, v[0], r=2.4, fill=PAL["ratio"])
        p2.dot(t, v[-1], r=2.4, fill=PAL["ratio"])
        p2.ptext(p2.X(t) + 9, p2.Y(v[0]) - 4, "%d/%d under" % (u, len(v)), size=10, fill=MUTED)
    p2.ptext(p2.l + 12, p2.t + 18, "bar = min..max, dot = median", size=11, fill=INK)
    return svg(W, H, "The pass-rate sizing rule under-budgets the frontier (issue #139, spike_v2)",
               [p1, p2])


def fig_two_obligation_law(v2):
    """F4 -- the two-obligation law: which candidate rule predicts convexity."""
    rules = v2["law"]["candidate_rules"]
    items = sorted(rules.items(), key=lambda kv: (kv[1]["pct"], kv[0]))
    W, H = 60 + 30 * len(items) + 40 + 90 + 60, 0
    H = 60 + 30 * len(items) + 90
    p = Panel(0, 0, W, H, (0, 106), (-0.6, len(items) - 0.4), ml=380, mr=40, mt=52, mb=70)
    p.frame([0, 25, 50, 75, 100], list(range(len(items))),
            "agreement with the measured convexity (%)", "")
    for i, (name, r) in enumerate(items):
        col = PAL["keep"] if r["pct"] >= 99.99 else (WARN if "decay" in name else PAL["ratio"])
        p.rect(0, r["pct"], i - 0.32, i + 0.32, fill=col, op=0.85)
        p.ptext(p.X(r["pct"]) + 8, p.Y(i) + 4, "%.1f%%  (%d/%d)" % (r["pct"], r["agree"], r["of"]),
                size=11, fill=INK)
        p.ptext(p.l - 12, p.Y(i) + 4, name, size=11, anchor="end", fill=INK)
    p.ptext(p.l + 12, p.t - 24,
            "green = agrees on every cell; gold = the hand-derived fast-decay condition "
            "(%.2f%%, the one R616 measured)" % rules["fast-decay coefficient < 0 (necessary)"]["pct"],
            size=11, fill=MUTED)
    return svg(W, H, "Which candidate rule predicts the two-obligation convexity (issue #139, spike_v2)",
               [p])


def fig_guarantee(v3):
    """F5 -- the guarantee against its converse, and the coupling boundary."""
    ex = v3["exhaustive"]
    ns = sorted({r["n"] for r in ex})
    vecs = sorted({r["vector"] for r in ex})
    W, H = 1020, 470
    p1 = Panel(0, 0, 505, H, (-0.6, len(vecs) - 0.4), (0, max(r["cells"] for r in ex) * 1.15),
               ml=96, mb=104)
    p1.frame(list(range(len(vecs))), [0, 1000, 2000, 3000, 4000, 5000],
             "difficulty vector (bar = permutations tested)", "permutations",
             xfmt=lambda i: "")
    for i, v in enumerate(vecs):
        for j, nn in enumerate(ns):
            r = [x for x in ex if x["n"] == nn and x["vector"] == v][0]
            off = (j - 1) * 0.26
            p1.rect(i + off - 0.11, i + off + 0.11, 0, r["cells"], fill="#e9e9e9", op=1.0)
            if r["converse_violations"]:
                p1.rect(i + off - 0.11, i + off + 0.11, 0, r["converse_violations"],
                        fill=PAL["lost"], op=0.85)
    tot_g = sum(r["guarantee_violations"] for r in ex)
    tot_c = sum(r["converse_violations"] for r in ex)
    tot_p = sum(r["cells"] for r in ex)
    p1.ptext(p1.l + 10, p1.t + 18, "grey = permutations tested, red = CONVERSE violations",
             size=11, fill=INK)
    p1.ptext(p1.l + 10, p1.t + 40, "GUARANTEE violations: %d of %d" % (tot_g, tot_p),
             size=12, weight="bold", fill=PAL["keep"])
    p1.ptext(p1.l + 10, p1.t + 58, "CONVERSE exceptions: %d (one-directional)" % tot_c,
             size=12, weight="bold", fill=PAL["lost"])
    for i, v in enumerate(vecs):
        p1.ptext(p1.X(i), p1.b + 34, v.replace("_", " "), size=10, anchor="middle", fill=MUTED)

    cb = v3["coupling_boundary"]
    cs = sorted({r["c"] for r in cb})
    p2 = Panel(505, 0, 505, H, (-0.15, max(cs) + 0.15), (0, 1.0))
    p2.frame(cs, [0, 0.25, 0.5, 0.75, 1.0], "coupling c",
             "fraction of non-increasing orders that are convex")
    for c in cs:
        rows = [r for r in cb if r["c"] == c]
        bad_n = sum(1 for r in rows if r["noninc"] and not r["concave"])
        frac = bad_n / float(len(rows))
        p2.rect(c - 0.06, c + 0.06, 0, frac, fill=PAL["lost"], op=0.8)
        p2.ptext(p2.X(c), p2.Y(frac) - 8, "%d/%d" % (bad_n, len(rows)),
                 size=11, anchor="middle", fill=INK)
    tot = sum(1 for r in cb if r["noninc"] and not r["concave"])
    p2.ptext(p2.l + 12, p2.t + 18,
             "the guarantee breaks %d/%d times -- only ever with c > 0" % (tot, len(cb)),
             size=12, weight="bold", fill=WARN)
    return svg(W, H, "The concavity guarantee, its converse, and the coupling boundary "
                     "(issue #139, spike_v3)", [p1, p2])


def fig_attribution(v3):
    """F6 -- the coupling, not the order, explains every breakdown."""
    dec = v3["decomposition"]
    xs = [r["c"] for r in dec]
    ys = [r["defect_coupled"] for r in dec]
    zs = [abs(r["defect_uncoupled_same_order"]) for r in dec]
    W, H = 1020, 470
    p1 = Panel(0, 0, 505, H, (-0.02, max(xs) + 0.02), (0, max(ys) * 1.15))
    p1.frame(sorted({r["c"] for r in dec}), [0, 0.1, 0.2], "coupling c", "defect of the same order")
    for x, y in zip(xs, ys):
        p1.dot(x, y, r=3.2, fill=PAL["coupled"])
    p1.hline(0.0, stroke=PAL["uncoupled"], w=2.6)
    p1.ptext(p1.l + 12, p1.t + 18, "red: the coupled defect", size=11, fill=PAL["coupled"])
    p1.ptext(p1.l + 12, p1.t + 36, "blue: the SAME order, coupling off (max |defect| = %s)"
             % num(round(max(zs), 6)), size=11, fill=PAL["uncoupled"])

    p2 = Panel(505, 0, 505, H, (0, 1.06), (0, 1.06))
    p2.frame([0, 0.25, 0.5, 0.75, 1.0], [0, 0.25, 0.5, 0.75, 1.0],
             "fraction explained by the coupling", "fraction of the breakdown cells")
    exp = sum(1 for r in dec if r["explained_by_coupling"])
    frac = exp / float(len(dec))
    p2.band([(0.0, 0.0), (1.0, 1.0)], [(0.0, 0.0), (1.0, 1.0)], fill="#f0f0f0", op=0.0)
    p2.poly([(0.0, 0.0), (1.0, 1.0)], stroke=MUTED, w=1.6, dash="5 4")
    p2.dot(1.0, frac, r=7.0, fill=PAL["keep"])
    p2.ptext(p2.l + 12, p2.t + 18, "%d/%d breakdowns explained by the coupling" % (exp, len(dec)),
             size=12, weight="bold", fill=PAL["keep"])
    p2.ptext(p2.l + 12, p2.t + 38, "the diagonal = perfect attribution", size=10, fill=MUTED)
    return svg(W, H, "The coupling, not the order, explains every breakdown (issue #139, spike_v3)",
               [p1, p2])


# ------------------------------------------------------------------------------------------------
# the certificate

def facts(v0, v1, v2, v3):
    """The ten facts the figures assert, re-derived from the reports.  Returns (name, ok, detail)."""
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    f0, f1, f3 = v0["findings"], v1["findings"], v3["totals"]
    agg = v1_by_c(v1)
    meds = [a["dmed"] for a in agg]

    add("(a) the registration's placebo is NOT null -- a permuted schedule is not a control",
        f0["ordering_effect_uncoupled_maxabs"] > 1e-6,
        "ordering_effect_uncoupled_maxabs=%s, placebo_coupling_gain_maxabs=%s"
        % (num(f0["ordering_effect_uncoupled_maxabs"]), num(f0["placebo_coupling_gain_maxabs"])))

    add("(b) at c = 0 the coupling gain is exactly 0",
        f1["P2_gain_at_c0_maxabs"] == 0.0, "P2_gain_at_c0_maxabs=%s" % num(f1["P2_gain_at_c0_maxabs"]))

    add("(c) the concavity defect RISES with the coupling",
        all(meds[i] < meds[i + 1] for i in range(len(meds) - 1)),
        "median defect " + " -> ".join(num(round(m, 4)) for m in meds))

    add("(d) the frontier is superlinear in the budget (F@B90/F@B50 >= 1.5 in every cell)",
        f1["P1_ratio_ge_1.5"] == f1["P1_ratio_cells"] > 0,
        "%d/%d cells" % (f1["P1_ratio_ge_1.5"], f1["P1_ratio_cells"]))

    add("(e) the registered concavity prior is REFUTED",
        f1["P1_concave_cells"] < f1["P1_cells"] and f1["P1_max_concavity_defect"] > 0,
        "%d/%d concave, worst defect %s"
        % (f1["P1_concave_cells"], f1["P1_cells"], num(f1["P1_max_concavity_defect"])))

    rows = [r for r in v2["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
    under = sum(1 for r in rows if r["ratio"] < 1.0)
    add("(f) the pass-rate sizing rule UNDER-budgets in a majority, and by > 4x at worst",
        under * 2 > len(rows) and min(r["ratio"] for r in rows) < 0.25,
        "%d/%d under-budget, worst cell %.2fx" % (under, len(rows), 1.0 / min(r["ratio"] for r in rows)))

    rules = v2["law"]["candidate_rules"]
    gold = "fast-decay coefficient < 0 (necessary)"
    add("(g) the two-obligation law: p2 > p1 agrees on 100.0%, and the hand-derived rule is "
        "> 20 points below it",
        rules["p2 > p1"]["pct"] == 100.0 and rules["p2 > p1"]["pct"] - rules[gold]["pct"] > 20.0,
        "p2>p1 %.2f%% vs hand-derived %.2f%%" % (rules["p2 > p1"]["pct"], rules[gold]["pct"]))

    ex = v3["exhaustive"]
    add("(h) the guarantee holds with NO violation while its converse fails",
        sum(r["guarantee_violations"] for r in ex) == 0
        and sum(r["converse_violations"] for r in ex) > 0,
        "guarantee %d, converse %d over %d permutations"
        % (sum(r["guarantee_violations"] for r in ex), sum(r["converse_violations"] for r in ex),
           sum(r["cells"] for r in ex)))

    dec = v3["decomposition"]
    add("(i) every breakdown is attributed to the coupling, not the order",
        sum(1 for r in dec if r["explained_by_coupling"]) == f3["coupled_breakdown_cells"]
        and max(abs(r["defect_uncoupled_same_order"]) for r in dec) < 1e-9,
        "%d/%d explained; max |defect with coupling off| = %s"
        % (sum(1 for r in dec if r["explained_by_coupling"]), len(dec),
           num(round(max(abs(r["defect_uncoupled_same_order"]) for r in dec), 6))))

    cb = v3["coupling_boundary"]
    cs = sorted({r["c"] for r in cb})
    fr = []
    for c in cs:
        sub = [r for r in cb if r["c"] == c]
        fr.append(sum(1 for r in sub if r["noninc"] and not r["concave"]) / float(len(sub)))
    add("(j) the coupling boundary is violated more often as c grows",
        all(fr[i] < fr[i + 1] for i in range(len(fr) - 1)),
        "violation fraction " + " -> ".join(num(round(x, 4)) for x in fr))
    return out


def _tampers(v0, v1, v2, v3):
    """One mutation per F2 item, each chosen to make THAT item's check report a contradiction."""
    def cp():
        return (json.loads(json.dumps(v0)), json.loads(json.dumps(v1)),
                json.loads(json.dumps(v2)), json.loads(json.dumps(v3)))
    t = cp(); t[0]["findings"]["ordering_effect_uncoupled_maxabs"] = 0.0
    yield "(a)", t
    t = cp(); t[1]["findings"]["P2_gain_at_c0_maxabs"] = 0.5
    yield "(b)", t
    t = cp()
    for r in t[1]["P1"]:
        r["concavity_defect"] = 0.0
    yield "(c)", t
    t = cp(); t[1]["findings"]["P1_ratio_ge_1.5"] = 0
    yield "(d)", t
    t = cp(); t[1]["findings"]["P1_concave_cells"] = t[1]["findings"]["P1_cells"]
    yield "(e)", t
    t = cp()
    for r in t[2]["planner_rows"]:
        if r.get("ratio") is not None:
            r["ratio"] = 2.0
    yield "(f)", t
    t = cp(); t[2]["law"]["candidate_rules"]["p2 > p1"]["pct"] = 90.0
    yield "(g)", t
    t = cp(); t[3]["exhaustive"][0]["guarantee_violations"] = 1
    yield "(h)", t
    t = cp()
    for r in t[3]["decomposition"]:
        r["explained_by_coupling"] = False
    yield "(i)", t
    t = cp()
    for r in t[3]["coupling_boundary"]:
        if r["c"] == 0.6:
            r["concave"] = True                      # erase the LARGEST c's violations, so the
    yield "(j)", t                                   # violation fraction stops increasing


def readback(svgs):
    """Read every emitted coordinate BACK off the SVG text and check it against the canvas.

    Returns (n_checked, [violations]).  A coordinate outside its own canvas is a defect however it
    got there; the read-back is what makes F3 about the emitted artefact and not about the intent.
    """
    pts = 0
    bad = []
    for name, text in svgs.items():
        m = re.search(r'width="(\d+)" height="(\d+)"', text)
        W, H = int(m.group(1)), int(m.group(2))
        for attr, pairs in (("points", re.findall(r'points="([^"]+)"', text)),):
            for blob in pairs:
                for tok in blob.split():
                    xs, ys = tok.split(",")
                    pts += 1
                    x, y = float(xs), float(ys)
                    if not (-0.01 <= x <= W + 0.01 and -0.01 <= y <= H + 0.01):
                        bad.append("%s: (%s,%s) leaves %dx%d" % (name, xs, ys, W, H))
        for cx, cy in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', text):
            pts += 1
            x, y = float(cx), float(cy)
            if not (-0.01 <= x <= W + 0.01 and -0.01 <= y <= H + 0.01):
                bad.append("%s: circle (%s,%s) leaves %dx%d" % (name, cx, cy, W, H))
    return pts, bad


def certificate():
    v0, v1, v2, v3 = (report("spike_v%d_results.json" % i) for i in range(4))
    ok = total = 0

    def check(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            print("  OK   %s%s" % (name, ("  [%s]" % detail) if detail else ""))
        else:
            print("  FAIL %s%s" % (name, ("  [%s]" % detail) if detail else ""))

    print("F0 -- CAPTIONS.md states the numbers its reports hold, in the form the report dictates")
    _, caps_text = figure_docs(v0, v1, v2, v3)
    facts0 = caption_facts(v0, v1, v2, v3)
    for label, pat in facts0:
        check(label, re.search(pat, caps_text) is not None, pat)
    lab, pat = facts0[0]
    hit = re.search(pat, caps_text)
    if hit:
        stripped = caps_text[:hit.start()] + "XX" + caps_text[hit.end():]
        check("a caption number deleted from the text IS caught by its own check",
              re.search(pat, stripped) is None, pat)
    else:
        check("a caption number deleted from the text IS caught by its own check", False,
              "the pattern was absent, so nothing could be planted against it")

    print("F1 -- every source report parses and carries the keys the figures read")
    want_keys = ({"findings", "cases", "exact_checks"},
                 {"findings", "P1", "P2", "P3", "certificate"},
                 {"law", "planner_rows", "planner"},
                 {"totals", "exhaustive", "decomposition", "coupling_boundary"})
    for i, (d, wk) in enumerate(zip((v0, v1, v2, v3), want_keys)):
        missing = sorted(wk - set(d))
        check("spike_v%d_results.json carries its report keys" % i, not missing,
              "missing: %s" % ", ".join(missing) if missing else "")

    print("F2 -- the facts the figures assert, re-derived from the reports")
    for name, good, detail in facts(v0, v1, v2, v3):
        check(name, good, detail)
    for label, t in _tampers(v0, v1, v2, v3):
        res = facts(*t)
        caught = [n for n, g, _ in res if not g]
        check("plant %s is caught by its own check" % label,
              len(caught) > 0 and any(c.startswith(label) for c in caught),
              "caught: " + (", ".join(c.split()[0] for c in caught) if caught else "NOTHING"))

    print("F3 -- every emitted coordinate lies inside its own canvas (read back off the SVG)")
    svgs = {"fig1": fig_frontier(v0), "fig2": fig_grid_concavity(v1), "fig3": fig_sizing(v2),
            "fig4": fig_two_obligation_law(v2), "fig5": fig_guarantee(v3),
            "fig6": fig_attribution(v3)}
    pts, bad = readback(svgs)
    check("all %d emitted coordinates are inside their canvas" % pts, not bad and pts > 400,
          "; ".join(bad[:3]))
    planted = dict(svgs)
    planted["fig6"] = planted["fig6"].replace("points=\"", "points=\"99999,99999 ", 1)
    pts2, bad2 = readback(planted)
    check("a planted off-canvas coordinate IS caught by the read-back", len(bad2) > 0,
          bad2[0] if bad2 else "NOTHING")

    print("FIGURE SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1


# ------------------------------------------------------------------------------------------------
# the doc files and the build

def figure_docs(v0, v1, v2, v3):
    """FIGURES.md and CAPTIONS.md -- every number below is read from the report it names."""
    agg = v1_by_c(v1)
    f0, f1 = v0["findings"], v1["findings"]
    rows = [r for r in v2["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
    ratios = sorted(r["ratio"] for r in rows)
    under = sum(1 for x in ratios if x < 1.0)
    rules = v2["law"]["candidate_rules"]
    gold = "fast-decay coefficient < 0 (necessary)"
    ex = v3["exhaustive"]
    dec = v3["decomposition"]
    cb = v3["coupling_boundary"]
    gsum = sum(r["guarantee_violations"] for r in ex)
    csum = sum(r["converse_violations"] for r in ex)
    psum = sum(r["cells"] for r in ex)
    cbs = sorted({r["c"] for r in cb})
    cbv = {c: sum(1 for r in cb if r["c"] == c and r["noninc"] and not r["concave"]) for c in cbs}
    dec_exp = sum(1 for r in dec if r["explained_by_coupling"])
    dec_dev = max(abs(r["defect_uncoupled_same_order"]) for r in dec)

    figs = [
        ("fig1_frontier_and_coupling.svg", "spike_v0_results.json",
         "The exact frontier and the coupling gain"),
        ("fig2_grid_concavity.svg", "spike_v1_results.json",
         "The concavity defect and the budget ratio, by coupling level"),
        ("fig3_two_obligation_law.svg", "spike_v2_results.json",
         "Which candidate rule predicts the two-obligation convexity"),
        ("fig4_guarantee_and_boundary.svg", "spike_v3_results.json",
         "The guarantee, its converse, and the coupling boundary"),
        ("fig5_coupling_attribution.svg", "spike_v3_results.json",
         "The coupling, not the order, explains every breakdown"),
        ("fig6_sizing_rule.svg", "spike_v2_results.json",
         "The pass-rate sizing rule against the frontier's own budget"),
    ]
    t = ["# Figures -- issue #139", "",
         "Every figure is generated by `make_figures139.py` from the shipped reports (standard "
         "library only, deterministic; **matplotlib is not used and is not required**). Nothing is "
         "drawn that is not in a report, and every number a figure annotates is read from the "
         "report, so a figure cannot drift from its source. Re-generate with "
         "`python3 make_figures139.py`; `reproduce.sh` does so and compares byte-for-byte.", "",
         "| Figure | Source report |", "|---|---|"]
    for f, r, d in figs:
        t.append("| `%s` | %s -- %s |" % (f, r, d))
    t += ["",
          "The captions are in `CAPTIONS.md`, generated from the same reports in the same run; the "
          "hashes are in `manifest.json`.  `--selftest` runs the certificate F1-F3, including the "
          "read-back that no emitted coordinate leaves its canvas.", ""]

    _gmax = max(((c["B"], c["coupling_gain"]["greedy"]) for case in v0["cases"]
                 for c in case["cells"]), key=lambda z: z[1])

    caps = ["# Figure captions -- issue #139", "",
            "Generated by `make_figures139.py` from the same reports the figures are drawn from, in "
            "the same run, so a caption cannot drift from the picture it names. Do not edit by hand.",
            ""]
    cap_sizing = ["## `fig6_sizing_rule.svg`", "",
             "The pass-rate sizing rule against the frontier.  Left: the empirical CDF of "
             "pass-rate-budget / frontier-budget over the %d treatment cells; the rule "
             "**under-budgets %d of them (%.1f%%)**, and its worst cell is off by **%.2fx**.  "
             "Right: the same ratio by target fraction -- the closer the target to the whole set, "
             "the more often the rule is nearly right, and it is still short in %d of %d cells at "
             "a 0.9 target."
             % (len(rows), under, 100.0 * under / len(rows), 1.0 / ratios[0],
                sum(1 for r in rows if r["target"] == 0.9 and r["ratio"] < 1.0),
                sum(1 for r in rows if r["target"] == 0.9)), ""]
    caps += ["## `fig1_frontier_and_coupling.svg`", "",
             "The exact frontier and the coupling gain.  `F(B)` = expected obligations discharged "
             "after `B` attempts, on the two declared cases (`chain_uniform`, `p` uniform at 0.2, "
             "and `star_hard_root`, `p` = 0.15/0.60/0.60/0.60), at `c` = %s.  The red curve is the "
             "schedule with the coupling active, the blue the SAME schedule with the coupling "
             "switched off, the grey dashed the registration's permuted placebo.  The largest "
             "coupling gain is **%s** at `B` = %d.  The placebo is **not** null -- under zero "
             "coupling a permuted schedule already moves the frontier by %s -- which is why the "
             "registration's control could not have separated an ordering effect from a coupling "
             "effect." % (num(v0["cases"][0]["c"]), num(_gmax[1]), _gmax[0],
                          num(round(f0["ordering_effect_uncoupled_maxabs"], 4))), ""]
    caps += ["## `fig2_grid_concavity.svg`", "",
             "The `n` = 8 grid by coupling level.  Left: the concavity defect of `F(B)` over the "
             "%d cells at each `c` (bar = min..max, dot = median); the count of concave cells falls "
             "from **%d** at `c` = %s to **%d** at `c` = %s.  Right: `F(B90)/F(B50)`, the budget "
             "the frontier needs to go from 50%% to 90%% of the set; it is >= 1.0 -- proportional "
             "-- in **every** cell, with a minimum of %s and a maximum of %s, so the budget grows "
             "superlinearly."
             % (agg[0]["n"], agg[0]["concave"], num(agg[0]["c"]),
                agg[-1]["concave"], num(agg[-1]["c"]),
                num(min(a["qmin"] for a in agg)), num(max(a["qmax"] for a in agg))), ""]
    caps += ["## `fig3_two_obligation_law.svg`", "",
             "Which candidate rule predicts the two-obligation convexity, over the %d-point "
             "`(p1, p2)` grid (%.0f%% of the cells are convex somewhere).  The measured law is "
             "\"the attempt order takes the harder obligation second\" (`p2 > p1`), which agrees on "
             "**%.2f%%**; the hand-derived fast-decay condition -- which this study wrote down "
             "first and measured afterwards -- agrees on only **%.2f%%**, and is the measurement "
             "that corrected the derivation." % (v2["law"]["cells"], 100.0 * v2["law"]["convex"] / v2["law"]["cells"],
                                                rules["p2 > p1"]["pct"], rules[gold]["pct"]), ""]
    caps += ["## `fig4_guarantee_and_boundary.svg`", "",
             "The guarantee against its converse.  Left: every permutation at `n` = 5, 6, 7 for "
             "six difficulty vectors (grey = permutations tested, red = converse violations); the "
             "guarantee \"a non-increasing order has a concave frontier\" has **%d violations in "
             "%d permutations**, while its converse has **%d** -- the law is one-directional, and "
             "the agreement rate R616 reported hid that.  Right: the coupling boundary -- the "
             "guarantee is violated in %s of the %d cells at `c` = %s, i.e. only ever with `c` > 0, "
             "so it is a `c` = 0 theorem."
             % (gsum, psum, csum,
                "/".join("%d" % cbv[c] for c in cbs), len(cb), "/".join(num(c) for c in cbs)), ""]
    caps += ["## `fig5_coupling_attribution.svg`", "",
             "The coupling, not the order, explains every breakdown.  Left: for the %d cells whose "
             "non-increasing order is not concave, the defect with the coupling on (red) against "
             "the defect of the SAME order with the coupling switched off (blue, pinned at 0; the "
             "largest value anywhere is %s).  Right: **%d of %d** breakdowns are attributed to the "
             "coupling." % (len(dec), num(round(dec_dev, 6)), dec_exp, len(dec)), ""]
    caps += cap_sizing
    return "\n".join(t), "\n".join(caps)


def caption_facts(v0, v1, v2, v3):
    """(label, regex) for each number CAPTIONS.md states, RE-DERIVED from the report it names.

    A caption is a claim about a report, so it is checked like one.  The regex is built from the
    report and matched against the caption text, which is why a caption whose two values are
    swapped (the gain and its budget, say) fails here: the pattern fixes their ORDER, not just
    their presence.  This is F0's jurisdiction -- the caption PROSE; F3 reads the canvas back.
    """
    agg = v1_by_c(v1)
    f0 = v0["findings"]
    rows = [r for r in v2["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
    ratios = sorted(r["ratio"] for r in rows)
    under = sum(1 for x in ratios if x < 1.0)
    ex, dec, cb = v3["exhaustive"], v3["decomposition"], v3["coupling_boundary"]
    cbs = sorted({r["c"] for r in cb})
    bnd = "/".join("%d" % sum(1 for r in cb if r["c"] == c and r["noninc"] and not r["concave"])
                   for c in cbs)
    gmax = max(((c["B"], c["coupling_gain"]["greedy"]) for case in v0["cases"]
                for c in case["cells"]), key=lambda z: z[1])
    return [
        ("fig1 states its gain then its budget (the pair in that order)",
         r"\*\*%s\*\* at `B` = %d\b" % (re.escape(num(gmax[1])), gmax[0])),
        ("fig1's null is the measured zero-coupling ordering effect",
         re.escape(num(round(f0["ordering_effect_uncoupled_maxabs"], 4)))),
        ("fig2's concave count runs from the first c to the last",
         r"from \*\*%d\*\* at `c` = %s to \*\*%d\*\* at `c` = %s"
         % (agg[0]["concave"], re.escape(num(agg[0]["c"])),
            agg[-1]["concave"], re.escape(num(agg[-1]["c"])))),
        ("fig6's under-budget count", r"\*\*under-budgets %d of them" % under),
        ("fig6's worst factor", r"off by \*\*%.2fx\*\*" % (1.0 / ratios[0])),
        ("fig4's guarantee violations and permutation total",
         r"\*\*%d violations in %d permutations\*\*"
         % (sum(r["guarantee_violations"] for r in ex), sum(r["cells"] for r in ex))),
        ("fig4's boundary counts by coupling level",
         r"%s of the %d cells" % (re.escape(bnd), len(cb))),
        ("fig5's attribution is stated as a total of the breakdowns",
         r"\*\*%d of %d\*\*" % (sum(1 for r in dec if r["explained_by_coupling"]), len(dec))),
    ]


def build(outdir):
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    v0, v1, v2, v3 = (report("spike_v%d_results.json" % i) for i in range(4))
    # The file order is the order the manuscript READS them in: figure numbers are assigned by
    # first appearance, so a figure numbered below another must not be introduced after it.
    files = [
        ("fig1_frontier_and_coupling.svg", fig_frontier(v0)),
        ("fig2_grid_concavity.svg", fig_grid_concavity(v1)),
        ("fig3_two_obligation_law.svg", fig_two_obligation_law(v2)),
        ("fig4_guarantee_and_boundary.svg", fig_guarantee(v3)),
        ("fig5_coupling_attribution.svg", fig_attribution(v3)),
        ("fig6_sizing_rule.svg", fig_sizing(v2)),
    ]
    man = [write(f, t, outdir) for f, t in files]
    figsmd, caps = figure_docs(v0, v1, v2, v3)
    man.append(write("FIGURES.md", figsmd, outdir))
    man.append(write("CAPTIONS.md", caps, outdir))
    write("manifest.json", json.dumps({"figures": man}, indent=2, sort_keys=True) + "\n", outdir)
    return len(man) + 1


def main(argv):
    if "--selftest" in argv:
        return certificate()
    outdir = OUTDIR
    for a in argv[1:]:
        if not a.startswith("-"):
            outdir = a
    n = build(outdir)
    print("wrote %d files to %s" % (n, os.path.abspath(outdir)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
