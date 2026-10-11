#!/usr/bin/env python3
"""make_figures -- the manuscript's figures for issue #130, generated from the shipped reports.

Standard library only (the package's own rule: no third-party import anywhere), and DETERMINISTIC:
the same reports produce byte-identical SVG. Run it from the package directory, or hand it an
output directory:

    python3 make_figures.py [OUTDIR]        # default: figures/
    python3 make_figures.py --selftest      # the certificate below

Five figures, each read off the shipped `*_results.json` of the instrument(s) named in
`figures/FIGURES.md`. Nothing is drawn that is not in a report, and every number a figure ANNOTATES
is read from the report dict rather than typed, so a figure cannot drift from its source. A cell
whose value is censored in the report is written on the plot as text, never plotted as a point
(Class 203: an operating point can fail to exist).

Certificate (--selftest), each item able to fail:
  F1  every figure's source report exists, parses, and carries the keys the figures read;
  F2  the facts the figures ASSERT are re-derived from those reports here --
      (a) the character statistics' null p95 rises with L while the shingle statistics' stays low;
      (b) eps*(OR) >= max(members) and eps*(AND) <= min(members) in spike_v4;
      (c) the stratum mismatch inflates the FPR on the material cells and the repair restores it;
      (d) share(L) reaches alpha first at the L* the floor report records;
  F3  no censored value reaches a coordinate: a censored cell is written, never plotted.
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "figures")

# ---------------------------------------------------------------------------------------------------
# the canvas: a data->pixel mapping plus the SVG primitives the five figures need
# ---------------------------------------------------------------------------------------------------
PAL = {"dice2c": "#1f77b4", "cos": "#d62728", "jac3": "#2ca02c", "jac5": "#9467bd"}
INK = "#222222"
GRID = "#dddddd"
AXIS = "#333333"
MUTED = "#666666"
LABEL = {"dice2c": "char-bigram Dice", "cos": "char 3-gram cosine",
         "jac3": "word-3 Jaccard", "jac5": "word-5 Jaccard"}
ORDER = ["dice2c", "cos", "jac3", "jac5"]
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
    """One plotting area. Data coords in, SVG coords out; `ox/oy` place it on the canvas."""

    def __init__(self, ox, oy, w, h, xlim, ylim, xlog=False, ylog=False,
                 ml=80, mr=24, mt=36, mb=64):
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.xlim, self.ylim, self.xlog, self.ylog = xlim, ylim, xlog, ylog
        self.l = ox + ml
        self.r = ox + w - mr
        self.t = oy + mt
        self.b = oy + h - mb
        self.el = []

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

    # -- primitives ---------------------------------------------------------------------------------
    def line(self, x1, y1, x2, y2, stroke=AXIS, w=1.4, dash=None, op=1.0):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                       'stroke-width="%s"%s opacity="%s"/>'
                       % (self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), stroke, num(w), d, num(op)))

    def poly(self, pts, stroke=AXIS, w=2.0, dash=None, op=1.0):
        p = " ".join("%.2f,%.2f" % (self.X(x), self.Y(y)) for x, y in pts)
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.el.append('<polyline fill="none" points="%s" stroke="%s" stroke-width="%s"%s '
                       'opacity="%s" stroke-linejoin="round"/>' % (p, stroke, num(w), d, num(op)))

    def dot(self, x, y, r=3.6, fill=AXIS, stroke="#ffffff", sw=1.0):
        self.el.append('<circle cx="%.2f" cy="%.2f" r="%s" fill="%s" stroke="%s" '
                       'stroke-width="%s"/>'
                       % (self.X(x), self.Y(y), num(r), fill, stroke, num(sw)))

    def rect_px(self, px, py, pw, ph, fill, op=0.92):
        self.el.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" opacity="%s"/>'
                       % (px, py, pw, ph, fill, num(op)))

    def band(self, x1, x2, y1, y2, fill=GRID, op=0.55):
        px, py = self.X(x1), self.Y(y2)
        self.rect_px(px, py, self.X(x2) - px, self.Y(y1) - py, fill, op)

    def vbar(self, x, y0, y1, width_px, fill, op=0.92):
        top = min(self.Y(y0), self.Y(y1))
        self.rect_px(self.X(x) - width_px / 2.0, top, width_px,
                     abs(self.Y(y1) - self.Y(y0)), fill, op)

    def ptext(self, px, py, s, size=12, anchor="start", fill=INK, weight="normal",
              italic=False, rotate=None):
        st = ' font-style="italic"' if italic else ""
        tr = ' transform="rotate(%s %.2f %.2f)"' % (num(rotate), px, py) if rotate is not None else ""
        self.el.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" fill="%s" '
                       'text-anchor="%s" font-weight="%s"%s%s>%s</text>'
                       % (px, py, FONT, num(size), fill, anchor, weight, st, tr, esc(s)))

    def text(self, x, y, s, dx=0, dy=0, **kw):
        self.ptext(self.X(x) + dx, self.Y(y) + dy, s, **kw)

    # -- frame --------------------------------------------------------------------------------------
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
            self.ptext((self.l + self.r) / 2, self.b + 46, xlabel, size=label_size,
                       anchor="middle", fill=INK)
        if ylabel:
            self.ptext(self.ox + 20, (self.t + self.b) / 2, ylabel, size=label_size,
                       anchor="middle", fill=INK, rotate=-90)

    def legend(self, entries, px, py, dy=19, swatch=26, size=11.5):
        """entries: [(label, colour, dash)]"""
        for i, (lab, col, dash) in enumerate(entries):
            y = py + i * dy
            d = ' stroke-dasharray="%s"' % dash if dash else ""
            self.el.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                           'stroke-width="2.2"%s/>' % (px, y, px + swatch, y, col, d))
            self.ptext(px + swatch + 7, y + 4, lab, size=size, fill=INK)


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


def _slope(xs, ys):
    m = len(xs)
    mx = sum(xs) / m
    my = sum(ys) / m
    sl = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    b = my - sl * mx
    ss = sum((y - (sl * x + b)) ** 2 for x, y in zip(xs, ys))
    st = sum((y - my) ** 2 for y in ys)
    return sl, (1 - ss / st if st else 0.0), m


# ---------------------------------------------------------------------------------------------------
# the five figures
# ---------------------------------------------------------------------------------------------------
def fig1(outdir):
    """The null is a function of length, and its shape divides the four statistics into two classes."""
    d = report("spike_v2_results.json")
    Ls, ST = d["L_grid"], d["stats"]
    W, H = 1040, 440
    p1 = Panel(0, 54, W // 2, 350, (min(Ls), max(Ls)), (0.0, 1.0), xlog=True, mr=30)
    p2 = Panel(W // 2, 54, W // 2, 350, (min(Ls), max(Ls)), (0.0, 1.0), xlog=True, ml=64)
    for p, key, title in ((p1, "median", "null MEDIAN"), (p2, "p95", "null p95  (the threshold)")):
        p.frame([40, 100, 300, 1000, 3000], [0.0, 0.25, 0.5, 0.75, 1.0],
                "artefact length  L  (characters)", "unrelated-pair similarity",
                xfmt=lambda v: str(v), yfmt=lambda v: "%.2f" % v)
        p.ptext((p.l + p.r) / 2, p.oy + 22, title, size=15, anchor="middle", weight="bold")
        for s in ST:
            pts = [(L, d["null"]["%s|L=%d" % (s, L)][key]) for L in Ls]
            p.poly(pts, stroke=PAL[s], w=2.2)
            for x, y in pts:
                p.dot(x, y, r=3.2, fill=PAL[s])
    # the class split the figure is about, annotated from the report, not from the eye
    jac_max = max(d["null"]["%s|L=%d" % (s, L)][k]
                  for s in ("jac3", "jac5") for L in Ls for k in ("median", "p95"))
    p1.legend([(LABEL[s], PAL[s], None) for s in ORDER], p1.l + 14, p1.t + 26)
    p1.band(min(Ls), max(Ls), 0.0, 0.03, fill="#ececec", op=0.9)
    p1.text(min(Ls), 0.062, "shingle statistics never leave this band (max %.4f)" % jac_max,
            dx=6, size=10.5, fill=MUTED, italic=True)
    p2.text(min(Ls), 0.965, "the null RISES with L for the character-weighting statistics",
             dx=6, size=10.5, fill=MUTED, italic=True)
    p2.text(min(Ls), 0.90, "and stalls at the floor for the shingle statistics",
             dx=6, size=10.5, fill=MUTED, italic=True)
    return write("fig1_null_vs_length.svg",
                 svg(W, H, "The unrelated-pair similarity null as a function of artefact length",
                     [p1, p2]), outdir)


def _series_rate(d, s):
    pts = []
    for L in d["L_grid"]:
        c = d["recall"]["%s|L=%d|rate" % (s, L)]
        if d["fpr"]["%s|L=%d" % (s, L)]["degenerate_tau_zero"] or not c["eps_star"]:
            continue
        pts.append((L, c["eps_star"]))
    return pts


def _censored(d, s):
    return [L for L in d["L_grid"]
            if d["fpr"]["%s|L=%d" % (s, L)]["degenerate_tau_zero"]
            or not d["recall"]["%s|L=%d|rate" % (s, L)]["eps_star"]]


def fig2(outdir):
    """The boundary eps* falls as a power law for the character-weighting statistic and is flat for
    the shingle statistics."""
    d = report("spike_v2_results.json")
    Ls, ST = d["L_grid"], d["stats"]
    fits = {}
    for s in ST:
        pts = _series_rate(d, s)
        fits[s] = (_slope([math.log(x) for x, _ in pts], [math.log(y) for _, y in pts])
                   if len(pts) >= 3 else None)
    W, H = 960, 510
    p = Panel(0, 56, W, 400, (min(Ls), max(Ls)), (0.18, 1.0), xlog=True, ylog=True, mr=48)
    p.frame([40, 100, 300, 1000, 3000], [0.2, 0.3, 0.5, 0.7, 1.0],
            "artefact length  L  (characters)",
            "boundary  eps*  (perturbation rate at recall 0.5)",
            xfmt=lambda v: str(v), yfmt=lambda v: "%.1f" % v)
    p.ptext(p.l + 6, p.oy + 24,
            "at the FPR-matched operating point a character-bigram check gets EASIER to fool as L grows",
            size=13, weight="bold")
    # draw the steepest line last so it is never hidden; censored statistics first
    for s in sorted(ORDER, key=lambda k: (fits[k] is not None, fits[k][0] if fits[k] else 0.0)):
        pts = _series_rate(d, s)
        if pts:
            p.poly(pts, stroke=PAL[s], w=2.4, dash=None if s in ("dice2c", "jac3") else "7 4")
            for x, y in pts:
                p.dot(x, y, r=3.4, fill=PAL[s])
    for i, s in enumerate(ORDER):
        if fits[s]:
            p.ptext(p.r - 8, p.t + 24 + 20 * i,
                    "%s: slope %+.3f  (R2 %.3f, n=%d)"
                    % (LABEL[s], fits[s][0], fits[s][1], fits[s][2]),
                    size=11.5, anchor="end", fill=PAL[s])
    cen = [(s, L) for s in ST for L in _censored(d, s)]
    p.ptext(p.l - 76, p.b + 62,
            "%d of %d cells are censored (no alpha-level operating point): %s"
            % (len(cen), len(ST) * len(Ls),
               ", ".join("%s L=%d" % (s, L) for s, L in cen)),
            size=10, fill=MUTED, italic=True)
    return write("fig2_boundary_power_law.svg",
                 svg(W, H, "The boundary eps* versus artefact length at the FPR-matched operating point",
                     [p]), outdir)


def fig3(outdir):
    """The certification floor: below L*(alpha) the statistic's threshold is 0 and every pair passes."""
    d3 = report("floor_v3_results.json")
    d2 = report("floor_v2_results.json")
    Ls = d3["L_grid"]
    alphas = d3["alphas"]
    W, H = 960, 510
    p = Panel(0, 56, W, 400, (min(Ls), max(Ls)), (0.0, 1.0), xlog=True, mr=48)
    p.frame([40, 100, 300, 1000, 3500], [0.0, 0.25, 0.5, 0.75, 1.0],
            "artefact length  L  (characters)", "share(L): fraction of null pairs above 0",
            xfmt=lambda v: str(v), yfmt=lambda v: "%.2f" % v)
    p.ptext(p.l + 6, p.oy + 24,
            "below L*(alpha) the null's p95 is 0, so tau = 0 and the false-positive rate is 1.0",
            size=13, weight="bold")
    for a in alphas:
        p.line(min(Ls), a, max(Ls), a, stroke="#999999", w=1.3, dash="5 4")
        p.ptext(p.r - 6, p.Y(a) - 6, "alpha = %.2f" % a, size=11, anchor="end", fill=MUTED)
    for s in ("jac3", "jac5"):
        pts = [(L, d3["share"]["%s|L=%d" % (s, L)]) for L in Ls]
        p.poly(pts, stroke=PAL[s], w=2.4)
        for x, y in pts:
            p.dot(x, y, r=3.2, fill=PAL[s])
        for a in alphas:
            p.dot(d3["L_star"]["%s|alpha=%.2f" % (s, a)], a, r=5.4, fill="#ffffff",
                  stroke=PAL[s], sw=2.2)
    p.ptext(p.l + 8, p.t + 26, "word-3 Jaccard:  L*(0.05) = %d,  L*(0.01) = %d"
            % (d3["L_star"]["jac3|alpha=0.05"], d3["L_star"]["jac3|alpha=0.01"]),
            size=12, fill=PAL["jac3"])
    p.ptext(p.l + 8, p.t + 46, "word-5 Jaccard:  L*(0.05) = %d,  L*(0.01) = %d"
            % (d3["L_star"]["jac5|alpha=0.05"], d3["L_star"]["jac5|alpha=0.01"]),
            size=12, fill=PAL["jac5"])
    p.ptext(p.r - 8, p.t + 26, "floor_v2 (null p95 > 0): jac3 L = %d, jac5 L = %d"
            % (d2["floors"]["jac3"]["L_floor"], d2["floors"]["jac5"]["L_floor"]),
            size=10.5, anchor="end", fill=MUTED, italic=True)
    p.ptext(p.r - 8, p.b - 12,
            "open rings mark L*(alpha): the smallest L whose null reaches that level",
            size=10.5, anchor="end", fill=MUTED, italic=True)
    return write("fig3_certification_floor.svg",
                 svg(W, H, "The certification floor: share(L) and L*(alpha)", [p]), outdir)


def _cells_ordered(d):
    """Cells in (statistic order, then numeric length) -- NOT the lexicographic key order, under
    which L=1500 would sort before L=350."""
    keys = sorted(d["cell"].keys(),
                  key=lambda k: (ORDER.index(k.split("|L=")[0]), int(k.split("|L=")[1])))
    return [(k, d["cell"][k]) for k in keys if not d["cell"][k]["degenerate_tau_zero"]]


def fig4(outdir):
    """The stratum-weights axis: a null calibrated on a uniform population applied to a scan whose
    shares are not uniform, the repair, and the diagnostic that does NOT rank the damage."""
    d = report("spike_v8_results.json")
    alpha = d["alpha"]
    cells = _cells_ordered(d)
    n = len(cells)
    mech = d["mechanism"]
    W, H = 1200, 560
    p1 = Panel(0, 58, 800, 450, (0.0, 0.55), (-0.7, n - 0.3), ml=124, mr=28, mb=76)
    p2 = Panel(800, 58, 400, 450, (-0.45, 1.0), (0.0, 1.0), ml=86, mr=44, mb=76)
    p1.frame([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], [], "false-positive rate on the scan", "",
             xfmt=lambda v: "%.2f" % v, yfmt=lambda v: "")
    p1.ptext(p1.l, p1.oy + 20,
             "a null calibrated uniformly, applied to a scan whose shares are skewed "
             "(book 0 = %.1f%%)" % (100 * d["skew_share"]), size=13, weight="bold")
    for i, (k, c) in enumerate(cells):
        p1.line(0.0, i, 0.55, i, stroke="#eeeeee", w=11)
        p1.ptext(p1.l - 10, p1.Y(i) + 4, k.replace("|L=", "  L="), size=11, anchor="end", fill=INK)
    # the three reads, drawn in an order that keeps the mismatch on top
    for key, col, r in (("fpr_matched_mean", "#7f7f7f", 4.0),
                        ("fpr_reweighted_mean", "#2ca02c", 4.0),
                        ("fpr_mismatched_mean", "#d62728", 4.8)):
        for i, (k, c) in enumerate(cells):
            p1.dot(c[key], i, r=r, fill=col, sw=1.2)
    p1.line(alpha, -0.7, alpha, n - 0.3, stroke="#111111", w=1.6, dash="6 3")
    p1.ptext(p1.X(alpha) + 5, p1.t + 14, "alpha = %.2f" % alpha, size=11, fill="#111111")
    worst = max(range(n), key=lambda i: cells[i][1]["fpr_mismatched_mean"]
                / cells[i][1]["fpr_matched_mean"])
    ratio = cells[worst][1]["fpr_mismatched_mean"] / cells[worst][1]["fpr_matched_mean"]
    p1.ptext(p1.X(cells[worst][1]["fpr_mismatched_mean"]) + 9, p1.Y(worst) + 4,
             "%.1fx" % ratio, size=11, fill="#d62728", weight="bold")
    p1.legend([("matched (null on its own measure)", "#7f7f7f", None),
               ("mismatched (skewed scan)", "#d62728", None),
               ("reweighted (the repair)", "#2ca02c", None)],
              p1.l + 200, p1.oy + 12, dy=16, swatch=20, size=10.5)
    # right panel: which of the two candidate diagnostics ranks the damage
    p2.frame([-0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0], [0.0, 0.5, 1.0],
             "Spearman rho with the damage", "", xfmt=lambda v: "%+.1f" % v,
             yfmt=lambda v: "%.1f" % v, grid=False)
    p2.ptext((p2.l + p2.r) / 2, p2.oy + 20, "which diagnostic RANKS the damage?", size=13,
             weight="bold", anchor="middle")
    sd = mech["null_sd_of_rho_at_this_n"]
    p2.band(-2 * sd, 2 * sd, 0.0, 1.0, fill="#ececec", op=0.9)
    p2.ptext(p2.r - 4, p2.Y(0.0) + 4, "null band (2 sd)", size=9.5, anchor="end",
             fill=MUTED, italic=True)
    rows = [("per-stratum THRESHOLD spread",
             mech["spearman_inflation_vs_per_stratum_threshold_spread"], "#9467bd"),
            ("scan-median shift / null IQR",
             mech["spearman_inflation_vs_median_shift_in_iqr"], "#1f77b4")]
    for i, (lab, val, col) in enumerate(rows):
        yt, yb = 0.70 - 0.34 * i, 0.36 - 0.34 * i
        x0, x1 = p2.X(min(0.0, val)), p2.X(max(0.0, val))
        p2.rect_px(x0, p2.Y(yt), x1 - x0, p2.Y(yb) - p2.Y(yt), col)
        p2.ptext(p2.X(val) + (8 if val >= 0 else -8), p2.Y((yt + yb) / 2) + 4, "%+.3f" % val,
                 size=12, anchor="start" if val >= 0 else "end", fill=col, weight="bold")
        p2.ptext(p2.l + 4, p2.Y(yt) - 6, lab, size=10.5, fill=INK)
    p2.ptext(p2.l - 82, p2.b + 64,
             "the natural diagnostic (purple) does not rank the damage: rho < 0", size=10,
             fill=MUTED, italic=True)
    return write("fig4_stratum_weights.svg",
                 svg(W, H, "The stratum-weights axis: mismatch, repair, and the rank of the diagnostics",
                     [p1, p2]), outdir)


def fig5(outdir):
    """The fusion: OR recovers the robust member's boundary, AND inherits the brittle member's."""
    d = report("spike_v4_results.json")
    Ls = d["L_grid"]
    W, H = 960, 510
    p = Panel(0, 56, W, 400, (min(Ls), max(Ls)), (0.15, 0.85), xlog=True, mr=48)
    p.frame([40, 100, 300, 1000, 3000], [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            "artefact length  L  (characters)", "boundary  eps*  at the FPR-matched point",
            xfmt=lambda v: str(v), yfmt=lambda v: "%.1f" % v)
    p.ptext(p.l + 6, p.oy + 24,
            "OR recovers the ROBUST member's boundary; AND inherits the BRITTLE member's",
            size=13, weight="bold")
    rows = [("dice2c", PAL["dice2c"], None, 2.2), ("cos", PAL["cos"], None, 2.2),
            ("or", "#8c564b", "8 4", 2.2), ("and", "#e377c2", "2 4", 2.2)]
    for tag, col, dash, wid in rows:
        pts = []
        for L in Ls:
            key = ("L=%d|%s" % (L, tag)) if tag in ("dice2c", "cos") \
                else ("L=%d|dice2c+cos|%s" % (L, tag))
            pts.append((L, d["eps_star"][key]))
        p.poly(pts, stroke=col, w=wid, dash=dash)
        for x, y in pts:
            p.dot(x, y, r=3.4, fill=col)
    p.legend([("char-bigram Dice (member)", PAL["dice2c"], None),
              ("char 3-gram cosine (member)", PAL["cos"], None),
              ("OR (dice2c + cos)", "#8c564b", "8 4"),
              ("AND (dice2c + cos)", "#e377c2", "2 4")],
             p.l + 14, p.t + 26)
    v = d["certificates"]["recall_bounds"]
    p.ptext(p.r - 8, p.b - 12,
            "certificate: R_or >= max and R_and <= min at %d cells, %d violations"
            % (v["cells"], len(v["violations"])), size=10.5, anchor="end", fill=MUTED, italic=True)
    return write("fig5_fusion_recovery.svg",
                 svg(W, H, "The fusion's boundary transfer: OR recovers, AND inherits", [p]), outdir)


FIGURES = [("fig1_null_vs_length.svg", fig1),
           ("fig2_boundary_power_law.svg", fig2),
           ("fig3_certification_floor.svg", fig3),
           ("fig4_stratum_weights.svg", fig4),
           ("fig5_fusion_recovery.svg", fig5)]

SOURCE_OF = {
    "fig1_null_vs_length.svg": ["spike_v2_results.json"],
    "fig2_boundary_power_law.svg": ["spike_v2_results.json"],
    "fig3_certification_floor.svg": ["floor_v2_results.json", "floor_v3_results.json"],
    "fig4_stratum_weights.svg": ["spike_v8_results.json"],
    "fig5_fusion_recovery.svg": ["spike_v4_results.json"],
}


def _geom_check(outdir):
    """Every drawn element must lie inside its canvas -- the mechanical form of "the figure
    renders", and stricter than the eye for CLIPPING. Text extents are estimated (0.56 em per
    character, anchored as drawn); a rotated label is bounded by its own half-diagonal."""
    import xml.etree.ElementTree as ET
    bad = []
    for name, _fn in FIGURES:
        root = ET.parse(os.path.join(outdir, name)).getroot()
        W = float(root.get("width"))
        H = float(root.get("height"))
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            label = ""
            if tag == "text":
                x, y = float(el.get("x")), float(el.get("y"))
                size = float(el.get("font-size", 12))
                label = el.text or ""
                w = 0.56 * size * len(label)
                a = el.get("text-anchor", "start")
                x0 = -w / 2 if a == "middle" else (-w if a == "end" else 0.0)
                x1 = x0 + w
                # the glyph box in the text's own frame, then rotated into canvas coords
                corners = [(x0, -0.8 * size), (x1, -0.8 * size), (x1, 0.3 * size), (x0, 0.3 * size)]
                th = 0.0
                tr = el.get("transform")
                if tr:
                    th = math.radians(float(tr.split("(")[1].split()[0]))
                ct, st = math.cos(th), math.sin(th)
                pts = [(x + cx * ct - cy * st, y + cx * st + cy * ct) for cx, cy in corners]
                box = (min(q[0] for q in pts), min(q[1] for q in pts),
                       max(q[0] for q in pts), max(q[1] for q in pts))
            elif tag == "line":
                xs = [float(el.get("x1")), float(el.get("x2"))]
                ys = [float(el.get("y1")), float(el.get("y2"))]
                box = (min(xs), min(ys), max(xs), max(ys))
            elif tag == "rect":
                x, y = float(el.get("x", 0)), float(el.get("y", 0))
                box = (x, y, x + float(el.get("width", 0)), y + float(el.get("height", 0)))
            elif tag == "circle":
                cx, cy, r = float(el.get("cx")), float(el.get("cy")), float(el.get("r"))
                box = (cx - r, cy - r, cx + r, cy + r)
            elif tag == "polyline":
                pts = [tuple(map(float, q.split(","))) for q in el.get("points").split()]
                xs = [q[0] for q in pts]
                ys = [q[1] for q in pts]
                box = (min(xs), min(ys), max(xs), max(ys))
            else:
                continue
            if box[0] < -1 or box[1] < -1 or box[2] > W + 1 or box[3] > H + 1:
                bad.append((name, tag, tuple(round(v, 1) for v in box), (W, H), label[:30]))
    return bad


def captions():
    """The caption the manuscript embeds for each figure. Every number is read from the same report
    the figure is drawn from -- a caption is generated, never typed, so it cannot drift from its
    figure (and `figures/CAPTIONS.md` is what the manuscript copies)."""
    v2 = report("spike_v2_results.json")
    v4 = report("spike_v4_results.json")
    v8 = report("spike_v8_results.json")
    f3 = report("floor_v3_results.json")
    Ls = v2["L_grid"]

    def p95(s, L):
        return v2["null"]["%s|L=%d" % (s, L)]["p95"]

    jac3_max = max(p95("jac3", L) for L in Ls)
    jac5_max = max(p95("jac5", L) for L in Ls)

    fits = {}
    for s in v2["stats"]:
        pts = _series_rate(v2, s)
        fits[s] = (_slope([math.log(x) for x, _ in pts], [math.log(y) for _, y in pts])
                   if len(pts) >= 3 else None)
    censored = [(s, L) for s in v2["stats"] for L in _censored(v2, s)]

    live = [c for c in v8["cell"].values() if not c["degenerate_tau_zero"]]
    mat = [c for c in live if c["fpr_mismatched_mean"] > v8["alpha"] + 0.05]
    restored = [c for c in live if abs(c["fpr_reweighted_mean"] - v8["alpha"]) <= 0.05]
    worst = max(live, key=lambda c: c["fpr_mismatched_mean"] / c["fpr_matched_mean"])
    mech = v8["mechanism"]
    v4r = v4["certificates"]["recall_bounds"]

    return {
        "fig1_null_vs_length.svg":
            "**Figure 1. The unrelated-pair null is a function of artefact length, and its shape "
            "divides the statistics into two classes.** Similarity against length L for one "
            "corpus of real text: the null MEDIAN (left) and the null p95 (right, the "
            "false-positive-matched threshold). The character-weighting statistics rise steeply -- "
            "char-bigram Dice's p95 goes %.4f to %.4f and char 3-gram cosine's %.4f to %.4f over "
            "L = %d..%d -- while the shingle statistics never leave the floor (word-3 Jaccard's p95 "
            "peaks at %.4f, word-5's at %.4f). A fixed cut therefore over-flags short artefacts and "
            "under-flags long ones, and the two families cannot share one threshold."
            % (p95("dice2c", Ls[0]), p95("dice2c", Ls[-1]),
               p95("cos", Ls[0]), p95("cos", Ls[-1]), Ls[0], Ls[-1], jac3_max, jac5_max),
        "fig2_boundary_power_law.svg":
            "**Figure 2. At the FPR-matched operating point a character-bigram check gets easier to "
            "fool as the artefact grows.** The boundary eps*, the perturbation rate at which recall "
            "falls to 0.5, against L on log-log axes. Char-bigram Dice's boundary falls as a power "
            "law, slope %+.3f (R2 %.3f, n = %d); word-3 Jaccard's is flat (slope %+.3f). %d of %d "
            "cells are censored -- the statistic has no alpha-level operating point at that length -- "
            "and are named in the plot rather than drawn at zero."
            % (fits["dice2c"][0], fits["dice2c"][1], fits["dice2c"][2],
               fits["jac3"][0] if fits["jac3"] else float("nan"),
               len(censored), len(v2["stats"]) * len(Ls)),
        "fig3_certification_floor.svg":
            "**Figure 3. The certification floor: below L\\*(alpha) a check cannot certify "
            "anything.** share(L), the fraction of unrelated same-length null pairs whose "
            "similarity exceeds 0, against L. Where share(L) < alpha the null's p95 is 0, so the "
            "matched threshold is 0 and every pair passes -- the false-positive rate is 1.0, not "
            "alpha. Open rings mark L\\*(alpha); the two definitions of the floor (share reaching "
            "alpha, and the null's p95 becoming positive) are annotated in the plot. Below the "
            "floor a cell is a HOLE in the operating characteristic, not a reading of 0.0000.",
        "fig4_stratum_weights.svg":
            "**Figure 4. The operating point is stratified, and the natural diagnostic does not "
            "rank the damage.** Left: the false-positive rate read by a null calibrated on a "
            "uniform population over the corpus strata, when the scan's per-stratum shares are "
            "skewed (here one stratum supplies %.1f%% of the artefacts). The mismatched read is "
            "material (above alpha + 0.05) in %d of %d live cells and inflates the rate by up to "
            "%.1fx (annotated); reweighting the null to the scan's own shares restores alpha +- 0.05 "
            "in %d of %d. Right: two candidate diagnostics ranked against that inflation -- the "
            "per-stratum threshold spread (%+.3f), which does not rank it, and the scan-median "
            "shift expressed in the null's own interquartile range (%+.3f), which does (the grey "
            "band is +-2 standard deviations of rho under the null, %.3f)."
            % (100 * v8["skew_share"], len(mat), len(live),
               worst["fpr_mismatched_mean"] / worst["fpr_matched_mean"],
               len(restored), len(live),
               mech["spearman_inflation_vs_per_stratum_threshold_spread"],
               mech["spearman_inflation_vs_median_shift_in_iqr"],
               mech["null_sd_of_rho_at_this_n"]),
        "fig5_fusion_recovery.svg":
            "**Figure 5. A fusion of two statistics inherits one member's boundary at each "
            "composition.** The boundary eps* of the two member statistics and of their OR and AND "
            "at FPR-matched operating points. OR recovers the robust member's boundary and AND "
            "inherits the brittle member's -- eps\\*(OR) >= max(members) and eps\\*(AND) <= "
            "min(members), certified at all %d cells with %d violations, which is the whole price "
            "and the whole recovery of composing two checks rather than choosing one."
            % (v4r["cells"], len(v4r["violations"])),
    }


def write_captions(rows, outdir):
    caps = captions()
    lines = ["# Figure captions (generated by `make_figures.py`)",
             "",
             "The manuscript embeds these verbatim; every number in them is read from the same",
             "report the figure is drawn from, so a caption cannot drift from its figure.",
             ""]
    for name, _fn in FIGURES:
        lines += ["![%s](%s)" % (name, name), "", caps[name], ""]
    text = "\n".join(lines)
    write("CAPTIONS.md", text, outdir)
    return caps


def build(outdir):
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    rows = [fn(outdir) for _name, fn in FIGURES]
    manifest = {"generator": os.path.basename(__file__),
                "note": "generated by make_figures.py from the shipped reports; hashes are of the SVG bytes",
                "figures": [{"file": r["file"], "bytes": r["bytes"], "sha256": r["sha256"],
                             "sources": SOURCE_OF[r["file"]]} for r in rows]}
    write("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n", outdir)
    write_captions(rows, outdir)
    return rows


def selftest():
    v2 = report("spike_v2_results.json")
    v4 = report("spike_v4_results.json")
    v8 = report("spike_v8_results.json")
    f3 = report("floor_v3_results.json")
    f2 = report("floor_v2_results.json")
    Ls = v2["L_grid"]
    items = []

    def check(label, cond):
        items.append((label, bool(cond)))

    # F1 -- each figure's sources exist, parse, and carry the keys the figures read
    need = {"spike_v2_results.json": ("L_grid", "stats", "null", "fpr", "recall"),
            "spike_v4_results.json": ("L_grid", "eps_star", "certificates"),
            "spike_v8_results.json": ("alpha", "cell", "mechanism", "skew_share"),
            "floor_v3_results.json": ("L_grid", "alphas", "share", "L_star"),
            "floor_v2_results.json": ("floors",)}
    got = {"spike_v2_results.json": v2, "spike_v4_results.json": v4,
           "spike_v8_results.json": v8, "floor_v3_results.json": f3,
           "floor_v2_results.json": f2}
    missing = [(f, k) for f, ks in need.items() for k in ks if k not in got[f]]
    check("F1 every source report carries the keys the figures read", not missing)

    def p95(s, L):
        return v2["null"]["%s|L=%d" % (s, L)]["p95"]

    check("F2a the character statistics' null p95 rises monotonically in L",
          all(p95(s, Ls[i]) < p95(s, Ls[i + 1])
              for s in ("dice2c", "cos") for i in range(len(Ls) - 1)))
    check("F2a the shingle statistics' null p95 stays <= 0.01 at every L",
          all(p95(s, L) <= 0.01 for s in ("jac3", "jac5") for L in Ls))

    viol = []
    for L in v4["L_grid"]:
        a = v4["eps_star"]["L=%d|dice2c" % L]
        b = v4["eps_star"]["L=%d|cos" % L]
        o = v4["eps_star"]["L=%d|dice2c+cos|or" % L]
        n = v4["eps_star"]["L=%d|dice2c+cos|and" % L]
        if o < max(a, b) - 1e-9 or n > min(a, b) + 1e-9:
            viol.append(L)
    check("F2b eps*(OR) >= max(members) and eps*(AND) <= min(members)", not viol)

    live = {k: c for k, c in v8["cell"].items() if not c["degenerate_tau_zero"]}
    mat = [c for c in live.values() if c["fpr_mismatched_mean"] > v8["alpha"] + 0.05]
    restored = [c for c in live.values() if abs(c["fpr_reweighted_mean"] - v8["alpha"]) <= 0.05]
    check("F2c the mismatch is material somewhere and inflates every material cell",
          len(mat) >= 1 and all(c["fpr_mismatched_mean"] > c["fpr_matched_mean"] for c in mat))
    check("F2c the reweighting restores every live cell to alpha +- 0.05",
          len(restored) == len(live) and len(live) > 0)

    bad = []
    for s in ("jac3", "jac5"):
        for a in f3["alphas"]:
            Lstar = f3["L_star"]["%s|alpha=%.2f" % (s, a)]

            def sh(L):
                return f3["share"]["%s|L=%d" % (s, L)]
            if sh(Lstar) < a or any(sh(L) >= a for L in f3["L_grid"] if L < Lstar):
                bad.append((s, a, Lstar))
    check("F2d share(L) reaches alpha first at the recorded L*", not bad)

    plotted_none = [(s, L) for s in v2["stats"] for L, y in _series_rate(v2, s) if y is None]
    check("F3 no censored value reaches a coordinate (all plotted eps* are real)",
          not plotted_none)
    censored = [(s, L) for s in v2["stats"] for L in _censored(v2, s)]
    check("F3 the censored cells are counted and named, not plotted",
          len(censored) > 0)

    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="figcheck.")
    try:
        build(tmp)
        out_of_canvas = _geom_check(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("F4 every drawn element lies inside its canvas", not out_of_canvas)

    planted_dir = tempfile.mkdtemp(prefix="figplant.")
    try:
        planted = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                   '<text x="-500" y="10" font-size="12">outside</text></svg>')
        for name, _fn in FIGURES:      # every name the checker reads, so it cannot miss by absence
            with open(os.path.join(planted_dir, name), "w", encoding="utf-8") as f:
                f.write(planted)
        caught = _geom_check(planted_dir)
    finally:
        shutil.rmtree(planted_dir, ignore_errors=True)
    check("F4b the bounds check CATCHES a planted out-of-canvas element", bool(caught))

    ok = all(c for _l, c in items)
    print("make_figures --selftest")
    for label, c in items:
        print("  %-66s %s" % (label, "PASS" if c else "FAIL"))
    if censored:
        print("  censored cells: %s" % ", ".join("%s L=%d" % t for t in censored))
    print("SELFTEST %s" % ("ALL PASS" if ok else "FAILED"))
    return ok


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        return 0 if selftest() else 1
    outdir = args[0] if args else OUTDIR
    rows = build(outdir)
    print("make_figures: %d figure(s) + manifest.json -> %s" % (len(rows), outdir))
    for r in rows:
        print("  %-34s %7d B  %s" % (r["file"], r["bytes"], r["sha256"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
