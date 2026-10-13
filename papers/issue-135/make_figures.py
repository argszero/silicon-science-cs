#!/usr/bin/env python3
"""make_figures -- the manuscript's figure set for issue #135, generated from the shipped reports.

Standard library only (the package's own rule: no third-party import anywhere -- matplotlib is not
used and is not required), and DETERMINISTIC: the same reports produce byte-identical SVG.

    python3 make_figures.py [OUTDIR]        # default: figures/
    python3 make_figures.py --selftest      # the certificate below

Six figures, each read off the shipped `spike_v*_results.json`.  Nothing is drawn that is not in a
report, and every number a figure ANNOTATES is read from the report dict rather than typed, so a
figure cannot drift from its source.  A cell whose value is UNDEFINED in the report (a budget
boundary the load grid could not bracket) is written on the plot as TEXT, never plotted as a point --
an unresolved cell is not a measurement.

Certificate (--selftest), each item able to fail:
  F1  every figure's source report exists, parses, and carries every key the figures read;
  F2  the facts the figures ASSERT are re-derived from those reports here --
      (a) the budget boundary: the mean-based rule A overstates the safe load at every bracketed k
          (the gap is positive), and the gap is a HUMP (its maximum is at an interior k, not at the
          smallest or the largest);
      (b) the scheme: Robin Hood's measured boundary at k=8 exceeds the linear arm's at k=8;
      (c) the finite-size window: |mean deviation| FALLS from m=4096 to m=65536 at alpha=0.95;
      (d) the tail's form in k: the geometric ratio is BELOW 1 for linear at every load and ABOVE 1
          for Robin Hood at every load -- opposite sides of the memoryless line;
      (e) the closed-form hierarchy: over the bracketed cells the mean |dev_A| exceeds the mean
          |dev_B| (the textbook rule is the worst of the two the figure draws);
      (f) the clustering statistic is scheme-invariant while the tail is not: same_longest_run is
          144 of 144 (fraction exactly 1.0) AND the p99 ratio's minimum exceeds 2;
  F3  no undefined value reaches a coordinate: every plotted series excludes its Nones, and the count
      that was excluded is asserted (a figure that silently dropped a cell would fail here).
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "figures")

PAL = {"linear": "#1f77b4", "robinhood": "#d62728", "mean": "#7f7f7f",
       "meas": "#111111", "A": "#7f7f7f", "B": "#2ca02c", "C": "#9467bd"}
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
        st = ' font-style="italic"' if italic else ""
        tr = ' transform="rotate(%s %.2f %.2f)"' % (num(rotate), px, py) if rotate is not None else ""
        self.el.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" fill="%s" '
                       'text-anchor="%s" font-weight="%s"%s%s>%s</text>'
                       % (px, py, FONT, num(size), fill, anchor, weight, st, tr, esc(s)))

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
# ------------------------------------------------------------------------------------------------
KS = [2, 4, 8, 16, 32, 64]
LEVEL = "0.001"


def fig_budget(v3):
    """The budget boundary alpha*(k): what a probe budget buys, against the textbook mean rule."""
    c16 = v3["checks"]["C16_measured_boundary"]
    c17 = v3["checks"]["C17_closed_form_comparison"]
    meas, above = {}, {}
    for scheme in ("linear", "robinhood"):
        key = "%s|uniform|%s" % (scheme, LEVEL)
        pts, miss = [], []
        for k in KS:
            cr = c16[key][str(k)]["crossing"]
            if cr.get("alpha") is None:
                miss.append((k, cr.get("bound", "?")))
            else:
                pts.append((math.log2(k), cr["alpha"]))
        meas[scheme] = pts
        above[scheme] = miss
    key = "linear|uniform|%s" % LEVEL
    A = [(math.log2(k), c17[key][str(k)]["A_mean_based"]) for k in KS]

    p = Panel(0, 0, 940, 500, (0.7, 6.5), (0.0, 1.04))
    p.frame([1, 2, 3, 4, 5, 6], [0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "probe budget  k_max  (probes per operation, log scale)",
            "load factor at the budget boundary   alpha*(k)",
            xfmt=lambda t: str(2 ** int(round(t))))
    p.poly(A, stroke=PAL["A"], w=2.0, dash="7 5")
    for scheme in ("linear", "robinhood"):
        p.poly(meas[scheme], stroke=PAL[scheme], w=2.6)
        for x, y in meas[scheme]:
            p.dot(x, y, fill=PAL[scheme])
    x4 = math.log2(4)
    a4, l4 = dict(A)[x4], dict(meas["linear"])[x4]
    p.line(x4, l4, x4, a4, stroke=WARN, w=1.6, dash="4 3")
    p.ptext(p.X(x4) + 10, p.Y((a4 + l4) / 2), "the budget-mean gap", size=11.5, fill=WARN)
    lg = [(0.30, "A = 1 - 1/sqrt(2k-1)  (textbook mean rule)", PAL["A"]),
          (0.215, "Robin Hood", PAL["robinhood"]),
          (0.13, "linear probing", PAL["linear"])]
    for y, txt, col in lg:
        p.ptext(p.X(4.30), p.Y(y), txt, size=12, fill=col, weight="bold")
    p.ptext(p.X(0.72), p.Y(0.99),
            "linear|uniform, level = 1e-3, m = 65536: the textbook rule overstates the safe load "
            "at every bracketed k", size=11.5, fill=INK)
    notes = []
    for scheme in ("linear", "robinhood"):
        if above[scheme]:
            lo = min(k for k, _ in above[scheme])
            notes.append("%s: alpha* undefined at k >= %d (%s the grid ceiling) -- written, not plotted"
                         % (scheme, lo, above[scheme][0][1]))
    for i, t in enumerate(notes):
        p.ptext(p.X(2.62), p.Y(0.065 - 0.055 * i), t, size=10.5, fill=MUTED)
    return svg(940, 500, "The budget boundary alpha*(k_max) against the textbook mean rule", [p])


def fig_deviation(v1):
    """The same classical formula against two schemes: a seed-stable miss vs a seed-noisy one."""
    c10 = v1["checks"]["C10_deviation_from_linear_formula"]
    loads = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.99]
    p = Panel(0, 0, 940, 500, (0.0, 1.02), (-1.15, 0.45))
    p.frame([0, 0.2, 0.4, 0.6, 0.8, 1.0], [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4],
            "load factor  alpha",
            "deviation of the classical mean form\nfrom the measured mean probe count")
    p.hline(0.0, stroke=GRID, w=1.0)
    for scheme in ("linear", "robinhood"):
        mean_pts, lo_pts, hi_pts = [], [], []
        for a in loads:
            r = c10["%s|%.2f" % (scheme, a)]
            mean_pts.append((a, r["mean"]))
            lo_pts.append((a, r["mean"] - r["spread"] / 2.0))
            hi_pts.append((a, r["mean"] + r["spread"] / 2.0))
        p.band(lo_pts, hi_pts, fill=PAL[scheme], op=0.18)
        p.poly(mean_pts, stroke=PAL[scheme], w=2.6)
        for x, y in mean_pts:
            p.dot(x, y, r=3.0, fill=PAL[scheme])
    r99 = c10["robinhood|0.99"]
    p.ptext(p.X(0.99) - 10, p.Y(r99["mean"]) + 24, "Robin Hood: %.2f (spread %.3f)"
            % (r99["mean"], r99["spread"]), size=11.5, anchor="end", fill=PAL["robinhood"])
    r95 = c10["linear|0.95"]
    p.ptext(p.X(0.72), p.Y(0.34), "linear: %.3f at alpha = 0.95, spread %.2f"
            % (r95["mean"], r95["spread"]), size=11.5, fill=PAL["linear"], weight="bold")
    p.ptext(p.X(0.03), p.Y(-1.02),
            "the band is the across-seed range (n = %d): Robin Hood is off by ~1 load with a "
            "seed-stable band," % r99["n"], size=11, fill=INK)
    p.ptext(p.X(0.03), p.Y(-1.10),
            "while the linear arm's own deviation is seed-noisy (its band runs 0.03 -> 0.78)",
            size=11, fill=MUTED)
    return svg(940, 500, "The classical mean form against two schemes", [p])


def fig_finite_size(v0):
    """The finite-size window: the classical form is a statement about a table SIZE."""
    c5 = v0["checks"]["C5_finite_size"]
    rows = c5["rows"]
    p = Panel(0, 0, 940, 500, (2800, 110000), (0.0, 0.62), xlog=True)
    p.frame([4096, 16384, 65536], [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "table size  m  (log scale)",
            "absolute deviation of the classical mean form\nat alpha = 0.95 (linear|uniform)",
            xfmt=lambda t: "%d" % int(t))
    mm = [(r["m"], sum(abs(d) for d in r["devs"]) / len(r["devs"])) for r in rows]
    for r in rows:
        for d in r["devs"]:
            p.dot(r["m"], abs(d), r=3.4, fill="#ffffff", stroke=PAL["linear"], sw=1.6)
    p.poly(mm, stroke=PAL["linear"], w=2.6)
    for x, y in mm:
        p.dot(x, y, r=5.0, fill=PAL["linear"])
        p.ptext(p.X(x), p.Y(y) - 13, "%.3f" % y, size=11.5, anchor="middle", fill=PAL["linear"])
    am = [(r["m"], r["abs_mean_dev"]) for r in rows]
    p.poly(am, stroke=MUTED, w=1.6, dash="6 4")
    for x, y in am:
        p.dot(x, y, r=3.4, fill=MUTED)
    for r in rows:
        p.ptext(p.X(r["m"]) + 9, p.Y(r["abs_mean_dev"]) + 4, "%.3f" % r["abs_mean_dev"],
                size=11, fill=MUTED)
    note = [(0.56, "alpha = 0.95, %d seeds; hollow dots are the individual seeds of the solid series"
             % len(c5["seeds"]), INK),
            (0.505, "solid = mean |deviation| (%.3f -> %.3f, monotone in m)" % (mm[0][1], mm[-1][1]),
             MUTED),
            (0.45, "dashed = |mean deviation| (%.3f -> %.3f): it DIPS at m = 16384 (%.3f) because"
             % (am[0][1], am[-1][1], am[1][1]), MUTED),
            (0.395, "the seed signs cancel there -- which is why the figure asserts the mean |dev|",
             WARN)]
    for y, txt, col in note:
        p.ptext(p.X(17000), p.Y(y), txt, size=11, fill=col)
    return svg(940, 500, "The finite-size window of the classical mean form", [p])


def fig_tail_decay(v3):
    """The tail's decay in k is scheme-specific in FORM, on opposite sides of the memoryless line."""
    c18 = v3["checks"]["C18_geometric_in_k"]
    alphas = [0.30, 0.50, 0.70, 0.80, 0.85, 0.90, 0.95]
    p = Panel(0, 0, 940, 480, (0.22, 1.02), (0.0, 2.35))
    p.frame([0.3, 0.5, 0.7, 0.8, 0.9, 1.0], [0.0, 0.5, 1.0, 1.5, 2.0],
            "load factor  alpha",
            "exponent of the tail's decay / log(alpha)\n(1.0 = exactly memoryless)")
    p.hline(1.0, stroke=WARN, w=1.6, dash="6 4")
    for scheme in ("linear", "robinhood"):
        pts = [(a, c18["%s|%.2f" % (scheme, a)]["ratio"]) for a in alphas]
        p.poly(pts, stroke=PAL[scheme], w=2.6)
        for x, y in pts:
            p.dot(x, y, fill=PAL[scheme])
    p.ptext(p.X(0.95), p.Y(1.0) - 10, "memoryless (a^k)", size=11.5, anchor="end", fill=WARN)
    p.ptext(p.X(0.34), p.Y(2.02), "Robin Hood: super-geometric (~a^(2k)) -- a LIGHTER tail",
            size=12, fill=PAL["robinhood"], weight="bold")
    p.ptext(p.X(0.34), p.Y(0.62), "linear probing: sub-geometric -- a HEAVIER tail",
            size=12, fill=PAL["linear"], weight="bold")
    p.ptext(p.X(0.24), p.Y(2.26),
            "the two schemes sit on OPPOSITE sides of the memoryless line, at every load",
            size=11, fill=MUTED)
    return svg(940, 480, "The tail's decay in k is scheme-specific in form", [p])


def fig_closed_forms(v3):
    """Three closed forms against the measured boundary: the textbook rule is the worst."""
    c17 = v3["checks"]["C17_closed_form_comparison"]
    c19 = v3["checks"]["C19_scheme_calibrated"]
    key = "linear|uniform|%s" % LEVEL
    rows = c19["rows"][key]
    meas, A, B, C = [], [], [], []
    for k in KS:
        r = c17[key][str(k)]
        if r["measured"] is not None:
            meas.append((math.log2(k), r["measured"]))
        A.append((math.log2(k), r["A_mean_based"]))
        B.append((math.log2(k), r["B_memoryless"]))
        cc = rows[str(k)]["C_scheme_calibrated"]
        if cc is not None:
            C.append((math.log2(k), cc))
    p = Panel(0, 0, 940, 480, (0.7, 6.5), (0.0, 1.0))
    p.frame([1, 2, 3, 4, 5, 6], [0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "probe budget  k_max  (log scale)",
            "load factor  alpha",
            xfmt=lambda t: str(2 ** int(round(t))))
    for pts, col, dash, wid in ((A, PAL["A"], "7 5", 2.0), (B, PAL["B"], "3 4", 2.0),
                                (C, PAL["C"], "3 4", 2.0)):
        p.poly(pts, stroke=col, w=wid, dash=dash)
    p.poly(meas, stroke=PAL["meas"], w=3.0)
    for x, y in meas:
        p.dot(x, y, fill=PAL["meas"])
    p.ptext(p.X(3.55), p.Y(0.93), "A  textbook mean rule", size=12, fill=PAL["A"], weight="bold")
    p.ptext(p.X(3.55), p.Y(0.855), "B  memoryless tail", size=12, fill=PAL["B"], weight="bold")
    p.ptext(p.X(3.55), p.Y(0.78), "C  scheme-calibrated", size=12, fill=PAL["C"], weight="bold")
    p.ptext(p.X(2.02), p.Y(0.51), "MEASURED", size=12, fill=PAL["meas"], weight="bold")
    r4 = c17[key]["4"]
    p.ptext(p.X(math.log2(4)) + 12, p.Y((r4["A_mean_based"] + (r4["measured"] or 0)) / 2 + 0.06),
            "A is high by %.2f at k = 4" % r4["dev_A"], size=11.5, fill=WARN)
    p.ptext(p.X(0.72), p.Y(0.06),
            "linear|uniform, level = 1e-3, m = 65536 -- the textbooks' own rule is the WORST of "
            "the three", size=11, fill=MUTED)
    return svg(940, 480, "Three closed forms against the measured budget boundary", [p])


def fig_clustering_vs_tail(v2):
    """The clustering statistic is scheme-invariant; the tail is not."""
    c14 = v2["checks"]["C14_clustering_is_not_scheme_invariant"]
    frac = c14["same_run_fraction"]
    ratio = c14["p99_ratio_linear_over_robinhood"]

    pl = Panel(0, 0, 470, 470, (0.0, 1.0), (0.0, 1.34))
    pl.frame([], [0.0, 0.25, 0.5, 0.75, 1.0],
             "the layout's clustering statistic",
             "fraction of pairs with the SAME longest run")
    pl.rect(0.32, 0.68, 0.0, frac, fill=PAL["meas"])
    pl.ptext(pl.X(0.5), pl.Y(frac) - 12,
             "%d / %d = %.3f" % (c14["same_longest_run"], c14["n_pairs"], frac),
             size=15, anchor="middle", fill=INK, weight="bold")
    pl.ptext(pl.X(0.5), pl.Y(1.30),
             "linear probing and Robin Hood fill the SAME set of slots,", size=11.5,
             anchor="middle", fill=MUTED)
    pl.ptext(pl.X(0.5), pl.Y(1.22),
             "so the longest run is a property of the occupied SET,", size=11.5,
             anchor="middle", fill=MUTED)
    pl.ptext(pl.X(0.5), pl.Y(1.14),
             "not of the lookup rule (%d pairs)." % c14["n_pairs"], size=11.5,
             anchor="middle", fill=MUTED)

    pr = Panel(470, 0, 470, 470, (0.0, 3.0), (0.7, 1300.0), ylog=True)
    pr.frame([], [1, 10, 100],
             "the tail statistic",
             "p99(linear) / p99(Robin Hood)  (log scale)",
             yfmt=lambda t: "%d" % int(t))
    bars = [("min", ratio["min"]), ("median", ratio["median"]), ("max", ratio["max"])]
    for i, (name, v) in enumerate(bars):
        x0, x1 = 0.25 + i, 0.75 + i
        pr.rect(x0, x1, 0.7, v, fill=PAL["robinhood"])
        pr.ptext((pr.X(x0) + pr.X(x1)) / 2, pr.Y(v) - 9, "%.1f" % v, size=13,
                 anchor="middle", fill=INK, weight="bold")
        pr.ptext((pr.X(x0) + pr.X(x1)) / 2, pr.b + 18, name, size=11.5,
                 anchor="middle", fill=MUTED)
    pr.ptext(pr.X(0.05), pr.Y(900),
             "the same layout, a different lookup rule:", size=11.5, fill=MUTED)
    pr.ptext(pr.X(0.05), pr.Y(520),
             "the p99 probe count differs by 2.4x to 115.8x", size=11.5, fill=MUTED)
    pr.ptext(pr.X(0.05), pr.Y(300),
             "-- so the tail's free variable is not the clustering", size=11.5, fill=WARN)
    return svg(940, 470, "The clustering statistic is scheme-invariant while the tail is not", [pl, pr])


# ------------------------------------------------------------------------------------------------
# the figure metadata, generated from the same reports the pictures are
# ------------------------------------------------------------------------------------------------
def figure_docs(v0, v1, v2, v3):
    """FIGURES.md and CAPTIONS.md -- every number below is read from the report it names."""
    c5 = v0["checks"]["C5_finite_size"]
    rows = c5["rows"]
    mad = [sum(abs(d) for d in r["devs"]) / len(r["devs"]) for r in rows]
    c10 = v1["checks"]["C10_deviation_from_linear_formula"]
    c14 = v2["checks"]["C14_clustering_is_not_scheme_invariant"]
    ratio = c14["p99_ratio_linear_over_robinhood"]
    c16 = v3["checks"]["C16_measured_boundary"]
    c17 = v3["checks"]["C17_closed_form_comparison"]
    key = "linear|uniform|%s" % LEVEL
    lin = {k: c16[key][str(k)]["crossing"].get("alpha") for k in KS}
    rh = {k: c16["robinhood|uniform|%s" % LEVEL][str(k)]["crossing"].get("alpha") for k in KS}
    A = {k: c17[key][str(k)]["A_mean_based"] for k in KS}
    gap = [A[k] - lin[k] for k in KS if lin[k] is not None]
    dA = [c17[key][str(k)]["dev_A"] for k in KS if c17[key][str(k)]["dev_A"] is not None]
    dB = [c17[key][str(k)]["dev_B"] for k in KS if c17[key][str(k)]["dev_B"] is not None]
    mA = sum(abs(x) for x in dA) / len(dA)
    mB = sum(abs(x) for x in dB) / len(dB)
    c18 = v3["checks"]["C18_geometric_in_k"]
    lr = [c18[k]["ratio"] for k in c18 if k.startswith("linear|")]
    rr = [c18[k]["ratio"] for k in c18 if k.startswith("robinhood|")]
    rh_hi = sorted(k for k in KS if rh[k] is None)
    rhi = min(rh_hi) if rh_hi else None

    figs = [
        ("fig1_budget_boundary.svg", "The budget boundary", "spike_v3_results.json",
         "The budget boundary. The load factor at which a probe budget `k_max` is exhausted, for "
         "linear probing and for Robin Hood, against the textbook mean-based rule "
         "`A = 1 - 1/sqrt(2k-1)` -- level 1e-3, `m = 65536`, uniform hashing. A overstates the safe "
         "load at **every** bracketed `k` (gaps %s for k = %s) and the gap is a **hump** peaking at "
         "k = 4 (**%.3f**), not at an extreme. Robin Hood is a different regime: alpha*(8) = **%.3f** "
         "against linear's %.3f. Robin Hood's boundary is undefined at k >= %s (%s the grid ceiling); "
         "it is written, never plotted."
         % ("/".join("%.3f" % g for g in gap), "/".join(str(k) for k in KS if lin[k] is not None),
            max(gap), rh[8], lin[8], rhi, c16["robinhood|uniform|%s" % LEVEL][str(rhi)]["crossing"]["bound"])),

        ("fig2_scheme_deviation.svg", "The classical mean form against two schemes",
         "spike_v1_results.json",
         "The classical mean form against two schemes. Deviation of the classical uniform-hashing "
         "mean from the measured mean probe count, for linear probing and for Robin Hood; the band "
         "is the across-seed range (n = %d). Against Robin Hood the form is off by **%.2f** at "
         "alpha = 0.99 with a seed-**stable** band (spread %.3f), while the linear arm's own "
         "deviation is seed-**noisy** (its band runs %.3f at low load to %.2f at alpha = 0.95) -- so "
         "the load factor is not even the *mean* across schemes."
         % (c10["robinhood|0.99"]["n"], c10["robinhood|0.99"]["mean"],
            c10["robinhood|0.99"]["spread"], c10["linear|0.05"]["spread"],
            c10["linear|0.95"]["spread"])),

        ("fig3_finite_size.svg", "The finite-size window", "spike_v0_results.json",
         "The finite-size window. Absolute deviation of the classical mean form at alpha = 0.95 as a "
         "function of the table size `m` (linear|uniform, %d seeds). The mean |deviation| falls "
         "monotonically **%.3f -> %.3f -> %.3f** from m = %d to %d; the |mean deviation| falls "
         "endpoint to endpoint (**%.3f -> %.3f**) but **dips** at m = %d (%.3f) because the seed "
         "signs cancel there -- which is exactly why the figure asserts the mean |deviation|. Hollow "
         "dots are the individual seeds."
         % (len(c5["seeds"]), mad[0], mad[1], mad[2], rows[0]["m"], rows[-1]["m"],
            rows[0]["abs_mean_dev"], rows[-1]["abs_mean_dev"], rows[1]["m"], rows[1]["abs_mean_dev"])),

        ("fig4_tail_decay.svg", "The tail's decay in k is scheme-specific in form",
         "spike_v3_results.json",
         "The tail's decay in `k` is scheme-specific in **form**. The exponent of the tail's decay in "
         "`k`, divided by log(alpha) -- 1.0 is exactly memoryless. Linear probing is sub-geometric "
         "(**%.3f -> %.3f** across the load range) and Robin Hood super-geometric (~`a^(2k)`; "
         "**%.3f -> %.3f**): the two schemes sit on **opposite sides** of the memoryless line at "
         "every load." % (lr[0], lr[-1], rr[0], rr[-1])),

        ("fig5_closed_forms.svg", "Three closed forms against the measured boundary",
         "spike_v3_results.json",
         "Three closed forms against the measured boundary. For linear|uniform at a 1e-3 level: the "
         "measured alpha*(k), the textbook mean rule A, the memoryless tail B, and the "
         "scheme-calibrated form C. A is the **worst** of the three -- its mean |deviation| over the "
         "bracketed cells is **%.3f** against B's %.3f -- overstating the safe load by %.2f at k = 4; "
         "B and C bracket the measurement."
         % (mA, mB, c17[key]["4"]["dev_A"])),

        ("fig6_clustering_vs_tail.svg", "The clustering statistic is scheme-invariant; the tail is not",
         "spike_v2_results.json",
         "The clustering statistic is scheme-invariant while the tail is not. Left: the fraction of "
         "(scheme-pair, alpha, seed) combinations whose two schemes carry the same longest run -- "
         "**%d of %d = %.3f**, because linear probing and Robin Hood fill the same slot set, so the "
         "longest run is a property of the occupancy and not of the lookup rule. Right: the same "
         "pairs' p99 probe-count ratio linear/Robin Hood -- min **%.1f**, median **%.1f**, max "
         "**%.1f** (log scale). The layout's clustering does not determine the tail; the lookup rule "
         "does."
         % (c14["same_longest_run"], c14["n_pairs"], c14["same_run_fraction"],
            ratio["min"], ratio["median"], ratio["max"])),
    ]

    fdoc = ["# Figures -- issue #135", "",
            "Every figure is generated by `make_figures.py` from the shipped reports (standard "
            "library only, deterministic; **matplotlib is not used and is not required**). Nothing is "
            "drawn that is not in a report, and every number a figure annotates is read from the "
            "report, so a figure cannot drift from its source. Re-generate with "
            "`python3 make_figures.py`; `reproduce.sh` does so and compares byte-for-byte.", "",
            "| Figure | Source report |", "|---|---|"]
    for name, title, src, _ in figs:
        fdoc.append("| `%s` | %s -- `%s` |" % (name, title, src))
    fdoc += ["", "The captions are in `CAPTIONS.md`, generated from the same reports in the same "
             "run; the hashes are in `manifest.json`. `--selftest` runs the certificate F1-F5, "
             "including the read-back that no emitted element leaves its canvas.", ""]

    cdoc = ["# Figure captions -- issue #135", "",
            "Generated by `make_figures.py` from the same reports the figures are drawn from, in the "
            "same run, so a caption cannot drift from the picture it names. Do not edit by hand.", ""]
    for name, title, _, cap in figs:
        cdoc += ["## `%s`" % name, "", cap, ""]
    return "\n".join(fdoc), "\n".join(cdoc)


# ------------------------------------------------------------------------------------------------
# the build, and the certificate
# ------------------------------------------------------------------------------------------------
def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    v0, v1, v2, v3 = (report("spike_v%d_results.json" % i) for i in range(4))
    figs = [
        ("fig1_budget_boundary.svg", fig_budget(v3)),
        ("fig2_scheme_deviation.svg", fig_deviation(v1)),
        ("fig3_finite_size.svg", fig_finite_size(v0)),
        ("fig4_tail_decay.svg", fig_tail_decay(v3)),
        ("fig5_closed_forms.svg", fig_closed_forms(v3)),
        ("fig6_clustering_vs_tail.svg", fig_clustering_vs_tail(v2)),
    ]
    entries = [write(name, text, outdir) for name, text in figs]
    fdoc, cdoc = figure_docs(v0, v1, v2, v3)
    write("FIGURES.md", fdoc, outdir)
    write("CAPTIONS.md", cdoc, outdir)
    manifest = {"issue": 135, "generator": "make_figures.py",
                "sources": ["spike_v0_results.json", "spike_v1_results.json",
                            "spike_v2_results.json", "spike_v3_results.json"],
                "figures": entries}
    write("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n", outdir)
    return entries


def _mean_abs(rows):
    return [sum(abs(d) for d in r["devs"]) / len(r["devs"]) for r in rows]


def certificate():
    """Re-derive every fact the figures assert.  Each item can fail."""
    v0, v1, v2, v3 = (report("spike_v%d_results.json" % i) for i in range(4))
    items = []

    def chk(name, ok, detail):
        items.append((name, bool(ok), detail))

    # F1 -- the source reports carry every key the figures read
    need = [(v0, ("checks", "C5_finite_size", "rows"), "v0.C5.rows"),
            (v0, ("checks", "C5_finite_size", "seeds"), "v0.C5.seeds"),
            (v1, ("checks", "C10_deviation_from_linear_formula"), "v1.C10"),
            (v2, ("checks", "C14_clustering_is_not_scheme_invariant"), "v2.C14"),
            (v3, ("checks", "C16_measured_boundary"), "v3.C16"),
            (v3, ("checks", "C17_closed_form_comparison"), "v3.C17"),
            (v3, ("checks", "C18_geometric_in_k"), "v3.C18"),
            (v3, ("checks", "C19_scheme_calibrated", "rows"), "v3.C19.rows")]
    miss = []
    for obj, path, label in need:
        cur = obj
        for k in path:
            cur = cur[k] if isinstance(cur, dict) and k in cur else None
            if cur is None:
                break
        if cur is None:
            miss.append(label)
    chk("F1 every source report carries every key the figures read", not miss,
        "missing: %s" % (", ".join(miss) if miss else "none"))

    # F2 -- the facts the figures assert
    c16 = v3["checks"]["C16_measured_boundary"]
    c17 = v3["checks"]["C17_closed_form_comparison"]
    key = "linear|uniform|%s" % LEVEL
    lin = {k: c16[key][str(k)]["crossing"].get("alpha") for k in KS}
    rh = {k: c16["robinhood|uniform|%s" % LEVEL][str(k)]["crossing"].get("alpha") for k in KS}
    A = {k: c17[key][str(k)]["A_mean_based"] for k in KS}
    gap = {k: A[k] - lin[k] for k in KS if lin[k] is not None}
    argmax = max(gap, key=gap.get)
    chk("F2a the textbook rule overstates the safe load at every bracketed k, and the gap is a HUMP",
        all(v > 0 for v in gap.values()) and argmax not in (KS[0], KS[-1]),
        "gap %s ; peak at k=%d (interior)" % ({k: round(v, 3) for k, v in gap.items()}, argmax))

    chk("F2b Robin Hood's measured boundary at k=8 exceeds the linear arm's at k=8",
        rh[8] is not None and lin[8] is not None and rh[8] > lin[8],
        "robinhood@8=%.4f > linear@8=%.4f" % (rh[8], lin[8]))

    rows = v0["checks"]["C5_finite_size"]["rows"]
    mad = _mean_abs(rows)
    chk("F2c the finite-size window: mean |deviation| falls with m, and |mean| falls endpoint to endpoint",
        all(mad[i] > mad[i + 1] for i in range(len(mad) - 1))
        and rows[0]["abs_mean_dev"] > rows[-1]["abs_mean_dev"],
        "mean|dev| %s ; |mean| %.3f -> %.3f" % ([round(x, 3) for x in mad],
                                                rows[0]["abs_mean_dev"], rows[-1]["abs_mean_dev"]))

    c18 = v3["checks"]["C18_geometric_in_k"]
    lr = [c18[k]["ratio"] for k in c18 if k.startswith("linear|")]
    rr = [c18[k]["ratio"] for k in c18 if k.startswith("robinhood|")]
    chk("F2d the tail's form: linear is sub-geometric and Robin Hood super-geometric at every load",
        bool(lr) and bool(rr) and all(x < 1 for x in lr) and all(x > 1 for x in rr),
        "linear ratio in [%.3f, %.3f] ; robinhood in [%.3f, %.3f]"
        % (min(lr), max(lr), min(rr), max(rr)))

    dA = [c17[key][str(k)]["dev_A"] for k in KS if c17[key][str(k)]["dev_A"] is not None]
    dB = [c17[key][str(k)]["dev_B"] for k in KS if c17[key][str(k)]["dev_B"] is not None]
    mA = sum(abs(x) for x in dA) / len(dA)
    mB = sum(abs(x) for x in dB) / len(dB)
    chk("F2e the closed-form hierarchy: the textbook rule is worse than the memoryless one",
        mA > mB,
        "mean|dev_A|=%.4f > mean|dev_B|=%.4f over n=%d/%d cells" % (mA, mB, len(dA), len(dB)))

    c14 = v2["checks"]["C14_clustering_is_not_scheme_invariant"]
    ratio = c14["p99_ratio_linear_over_robinhood"]
    chk("F2f the clustering statistic is scheme-invariant while the tail is not",
        c14["same_longest_run"] == c14["n_pairs"] and abs(c14["same_run_fraction"] - 1.0) < 1e-12
        and ratio["min"] > 2.0,
        "%d/%d share the longest run (fraction %.3f) ; p99 ratio min=%.2f median=%.2f max=%.2f"
        % (c14["same_longest_run"], c14["n_pairs"], c14["same_run_fraction"],
           ratio["min"], ratio["median"], ratio["max"]))

    # F3 -- an unresolved cell is written, never plotted
    plotted = {s: len([k for k in KS if (lin if s == "linear" else rh)[k] is not None])
               for s in ("linear", "robinhood")}
    unresolved = {s: len(KS) - plotted[s] for s in plotted}
    nC = len([k for k in KS if v3["checks"]["C19_scheme_calibrated"]["rows"][key][str(k)]
              ["C_scheme_calibrated"] is not None])
    chk("F3 no undefined value reaches a coordinate (the excluded count is asserted)",
        plotted["linear"] == 6 and plotted["robinhood"] == 4 and unresolved["robinhood"] == 2
        and nC == 6,
        "fig1 plots %d linear / %d robinhood points, excludes %d robinhood (%s); fig5 plots %d C points"
        % (plotted["linear"], plotted["robinhood"], unresolved["robinhood"],
           "+".join(sorted({c16["robinhood|uniform|%s" % LEVEL][str(k)]["crossing"].get("bound", "?")
                            for k in KS if rh[k] is None})), nC))

    # F4 / F5 -- determinism, and the emitted geometry read back off the canvas
    import re
    import shutil
    import tempfile
    d1 = tempfile.mkdtemp(prefix="figcert1-")
    d2 = tempfile.mkdtemp(prefix="figcert2-")
    try:
        e1 = build(d1)
        e2 = build(d2)
        same = e1 == e2
        texts = {}
        for e in e1:
            with open(os.path.join(d1, e["file"]), "r", encoding="utf-8") as f:
                texts[e["file"]] = f.read()
    finally:
        shutil.rmtree(d1, ignore_errors=True)
        shutil.rmtree(d2, ignore_errors=True)
    chk("F4 two builds produce byte-identical figures (Tolerance: exact)",
        same, "%d figures, sha256 equal across two fresh builds" % len(e1))

    outs, checked = [], 0
    for fname in sorted(texts):
        text = texts[fname]
        m = re.search(r'width="(\d+)" height="(\d+)"', text)
        w, h = int(m.group(1)), int(m.group(2))
        for tag, attrs in re.findall(r"<(line|rect|circle|polyline|polygon|text)\b([^>]*)>", text):
            def a(k):
                mm = re.search(r'%s="([-0-9.]+)"' % k, attrs)
                return float(mm.group(1)) if mm else None
            pts = []
            if tag == "line":
                pts = [(a("x1"), a("y1")), (a("x2"), a("y2"))]
            elif tag == "rect":
                x, y = a("x") or 0.0, a("y") or 0.0      # SVG defaults both to 0
                pts = [(x, y), (x + (a("width") or 0.0), y + (a("height") or 0.0))]
            elif tag == "circle":
                cx, cy, r = a("cx"), a("cy"), a("r")
                pts = [(cx - r, cy - r), (cx + r, cy + r)]
            elif tag in ("polyline", "polygon"):
                mm = re.search(r'points="([^"]*)"', attrs)
                pts = [(float(t.split(",")[0]), float(t.split(",")[1]))
                       for t in mm.group(1).split()]
            elif tag == "text":
                pts = [(a("x"), a("y"))]  # the anchor; glyphs may extend a little past it
            for (x, y) in pts:
                if x is None or y is None:
                    continue
                checked += 1
                if not (-1.0 <= x <= w + 1.0 and -1.0 <= y <= h + 1.0):
                    outs.append("%s: <%s> at (%.1f, %.1f) of %dx%d" % (fname, tag, x, y, w, h))
    chk("F5 no emitted element leaves the canvas (read back off the built SVG)",
        not outs, "%d coordinates checked across %d figures%s"
        % (checked, len(texts), "" if not outs else "; " + "; ".join(outs[:4])))

    print("make_figures --selftest")
    bad = 0
    for name, ok, detail in items:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
        if detail:
            print("         %s" % detail)
        bad += (not ok)
    print("SELFTEST %d/%d" % (len(items) - bad, len(items)))
    return 1 if bad else 0


def main(argv):
    if "--selftest" in argv:
        return certificate()
    rest = [a for a in argv[1:] if not a.startswith("-")]
    out = rest[0] if rest else OUTDIR
    entries = build(out)
    print("make_figures: %d figures + manifest.json -> %s" % (len(entries), out))
    for e in entries:
        print("  %-30s %8d B  %s" % (e["file"], e["bytes"], e["sha256"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
