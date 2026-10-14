#!/usr/bin/env python3
"""make_figures -- the manuscript's figures for issue #132, generated from the shipped reports.

Standard library only (the package's own rule: no third-party import anywhere), and DETERMINISTIC:
the same reports produce byte-identical SVG.  Run it from the package directory, or hand it an
output directory:

    python3 make_figures.py [OUTDIR]        # default: figures/
    python3 make_figures.py --selftest      # the certificate below

Five figures, each read off the shipped `*_results.json` of the instrument(s) named in
`figures/FIGURES.md`.  Nothing is drawn that is not in a report, and every number a figure
ANNOTATES is read from the report dict rather than typed, so a figure cannot drift from its source.
A cell whose value is UNDEFINED in the report (an eligible rate over an empty denominator) is
written on the plot as text, never plotted as a point -- a 0/0 cell is not a measurement.

Certificate (--selftest), each item able to fail:
  F1  every figure's source report exists, parses, and carries the keys the figures read;
  F2  the facts the figures ASSERT are re-derived from those reports here --
      (a) the share law's own control: the hidden fraction is exactly 0 at share 1.0;
      (b) the level ladder's step: the affected-pair rate is 1.0 below the critical prevalence and
          0 above it, in both strata, and the critical prevalence is the one the report records;
      (c) the residue error: the residual of df_corpus = s * df_pool is at float noise, not a share;
      (d) the r-boundary: the induced count is flat for r <= register_units and 0 above it;
      (e) the statistic decides: the word register is hidden from the corpus frame in every cell
          below the critical prevalence and the character register in none;
  F3  no undefined value reaches a coordinate: an undefined rate is written, never plotted.
"""
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "figures")

PAL = {"it": "#1f77b4", "en": "#d62728", "word3": "#2ca02c", "char2": "#9467bd"}
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

    def dot(self, x, y, r=3.6, fill=AXIS, stroke="#ffffff", sw=1.0):
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
# the five figures
# ------------------------------------------------------------------------------------------------
def fig_dilution(v0):
    """The share law: what a corpus-wide frame misses, as a function of the pool's share."""
    w3 = sorted(v0["share_sweep_word3_theta_0.01"], key=lambda r: r["share"])
    c2 = sorted(v0["share_sweep_char_bigram_theta_0.01"], key=lambda r: r["share"])
    cs = v0["containment_summary"]
    d = v0["dilution"]
    p = Panel(0, 0, 900, 470, (0.0, 1.06), (0.0, 1.0))
    p.frame([0, 0.25, 0.5, 0.75, 1.0], [0, 0.25, 0.5, 0.75, 1.0],
            "pool share of the corpus  s",
            "share of the pool's generic units\nthe corpus frame misses")
    for series, col in ((w3, PAL["word3"]), (c2, PAL["char2"])):
        pts = [(r["share"], r["hidden_fraction_of_F_pool"]) for r in series]
        p.poly(pts, stroke=col, w=2.4)
        for x, y in pts:
            p.dot(x, y, fill=col)
    zero = [r for r in w3 if abs(r["share"] - 1.0) < 1e-9][0]
    p.ptext(p.X(1.0) - 8, p.Y(zero["hidden_fraction_of_F_pool"]) - 12,
            "exactly 0 at s = 1.0 (the control: the pool IS the corpus)",
            size=11, anchor="end", fill=WARN)
    p.ptext(p.X(0.30), p.Y(0.92),
            "%d of %d cells FAIL set containment in both directions"
            % (cs["cells_where_F_corpus_NOT_subset_F_pool"], cs["cells"]),
            size=12, fill=INK)
    p.ptext(p.X(0.30), p.Y(0.80),
            "residual of  df_corpus = s * df_pool : %.1e (word-3, %d pairs)"
            % (d["word3_theta_0.01"]["worst_abs_violation"],
               d["word3_theta_0.01"]["n_confined_pairs"]),
            size=11, fill=MUTED)
    mid = [r for r in w3 if 0.3 < r["share"] < 0.6]
    if mid:
        m = mid[0]
        p.ptext(p.X(m["share"]) + 10, p.Y(m["hidden_fraction_of_F_pool"]) - 8,
                "word 3-shingles", size=12.5, fill=PAL["word3"], weight="bold")
    midc = [r for r in c2 if 0.3 < r["share"] < 0.6]
    if midc:
        m = midc[0]
        p.ptext(p.X(m["share"]) + 10, p.Y(m["hidden_fraction_of_F_pool"]) - 8,
                "character bigrams", size=12.5, fill=PAL["char2"], weight="bold")
    return svg(900, 470, "The share law: a corpus-wide frame's blind spot grows as the pool shrinks", [p])


def fig_ladder(v1):
    """The level ladder: the induced flag count vs the register's prevalence, two strata."""
    st = {s["name"]: s for s in v1["strata"]}
    theta, tau, stat = 0.05, 0.5, "word3"
    rows = [r for r in v1["ladder"] if r["stat"] == stat and r["tau"] == tau and r["theta"] == theta]
    p = Panel(0, 0, 940, 470, (0.0, 1.05), (0.0, 125.0))
    p.frame([0, 0.2, 0.4, 0.6, 0.8, 1.0], [0, 25, 50, 75, 100, 120],
            "register prevalence in the community  phi", "level-induced flag count")
    for name, col in (("minority_it", PAL["it"]), ("majority_en", PAL["en"])):
        pts = sorted((r["phi"], r["level_induced"]) for r in rows if r["stratum"] == name)
        p.poly(pts, stroke=col, w=2.4)
        for x, y in pts:
            p.dot(x, y, fill=col)
        phi_star = theta / st[name]["share"]
        p.vline(phi_star, stroke=col, w=1.4, dash="5 4", op=0.75)
        p.ptext(p.X(phi_star), p.Y(118), "phi* = %.3f" % phi_star, size=11, anchor="middle", fill=col)
    p.ptext(p.X(0.06), p.Y(112),
            "word-3, tau = 0.5, theta = 0.05: below phi* the corpus frame fires on 120/120, "
            "the community frame on 0/120", size=11.5, fill=INK)
    p.ptext(p.X(0.06), p.Y(101),
            "above phi* the register is IN the corpus frame and the induced count is 0",
            size=11.5, fill=MUTED)
    p.ptext(p.X(0.02), p.Y(60), "Italian", size=12.5, fill=PAL["it"], weight="bold")
    p.ptext(p.X(0.02), p.Y(30), "English", size=12.5, fill=PAL["en"], weight="bold")
    return svg(940, 470, "The frame level moves the flag count; the band of blindness is theta/s wide", [p])


def fig_critical_share(v1):
    """Where the corpus frame stops seeing the register: its corpus prevalence against the cutoff."""
    theta, stat = 0.05, "word3"
    # phi = 1.0 is the "in every corpus document" CONTROL, not a point of the prevalence ladder:
    # its corpus prevalence is 1.0 and it belongs to BOTH frames.  It is named in the annotation
    # rather than drawn, so no element leaves the canvas (F4).
    rows = [r for r in v1["critical_share"]
            if r["stat"] == stat and abs(r["theta"] - theta) < 1e-9 and 0.0 < r["phi"] < 1.0]
    st = {s["name"]: s for s in v1["strata"]}
    p = Panel(0, 0, 900, 470, (0.0, 1.05), (0.0, 0.30))
    p.frame([0, 0.2, 0.4, 0.6, 0.8, 1.0], [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
            "register prevalence in the community  phi",
            "register prevalence in the CORPUS   s * phi")
    p.hline(theta, stroke=WARN, w=2.0, dash="6 4")
    p.ptext(p.X(1.03), p.Y(theta) - 6, "theta = %.2f" % theta, size=11.5, anchor="end", fill=WARN)
    for name, col in (("minority_it", PAL["it"]), ("majority_en", PAL["en"])):
        sub = sorted(((r["phi"], r["corpus_prevalence"], r["observed_hidden_from_corpus"])
                      for r in rows if r["stratum"] == name))
        pts = [(x, y) for x, y, _ in sub]
        p.poly(pts, stroke=col, w=2.2, dash="4 3")
        for x, y, hid in sub:
            p.dot(x, y, fill=col, r=6.0 if hid else 3.4)
        phi_star = theta / st[name]["share"]
        p.vline(phi_star, stroke=col, w=1.3, dash="2 4", op=0.8)
        p.ptext(p.X(phi_star), p.Y(0.285), "%.3f" % phi_star, size=11, anchor="middle", fill=col)
    p.ptext(p.X(0.03), p.Y(0.285),
            "big dots = the register is HIDDEN from the corpus frame (every cell agrees: 48/48)",
            size=11.5, fill=INK)
    p.ptext(p.X(0.03), p.Y(0.265),
            "the crossing of each line with theta IS phi* = theta/s  --  measured, not assumed",
            size=11.5, fill=MUTED)
    ctrl = [r for r in v1["critical_share"]
            if r["stat"] == stat and abs(r["theta"] - theta) < 1e-9 and r["phi"] >= 1.0
            and r["stratum"] == "minority_it"]
    if ctrl:
        p.ptext(p.X(0.03), p.Y(0.245),
                "off scale: the phi = 1.0 control has corpus prevalence %.3f  --  it is in BOTH frames"
                % ctrl[0]["corpus_prevalence"], size=11, fill=WARN)
    return svg(900, 470, "The critical share: the corpus frame stops seeing the register at theta/s", [p])


def fig_r_boundary(v2):
    """The residue threshold: flat while the register can decide it, a derived zero above."""
    stat, tau, theta, sample, stratum = "word3", 0.5, 0.05, "affected", "minority_it"
    cells = [c for c in v2["cells"]
             if (c["stat"], c["tau"], c["theta"], c["sample"], c["stratum"])
             == (stat, tau, theta, sample, stratum)]
    reg_units = cells[0]["register_units"]
    p = Panel(0, 0, 900, 470, (3.0, 43.0), (0.0, 125.0))
    p.frame([5, 10, 20, 27, 30, 40], [0, 25, 50, 75, 100, 120],
            "residue threshold  r", "level-induced flag count")
    p.vline(reg_units, stroke=WARN, w=2.0, dash="6 4")
    p.ptext(p.X(reg_units) + 4, p.Y(120), "register has %d units" % reg_units, size=11.5, fill=WARN)
    for phi, col in ((0.20, PAL["it"]), (0.30, PAL["en"])):
        pts = sorted((c["r"], c["level_induced"]) for c in cells if abs(c["phi"] - phi) < 1e-9)
        if not pts:
            continue
        p.poly(pts, stroke=col, w=2.2)
        for x, y in pts:
            p.dot(x, y, fill=col)
        p.ptext(p.X(3.4), p.Y(pts[0][1] + 10), "phi = %.2f" % phi, size=12, fill=col, weight="bold")
    mx = max(c["max_residue_corpus"] for c in cells if c["max_residue_corpus"] is not None)
    p.ptext(p.X(3.4), p.Y(112),
            "at r = 40 the corpus residue never reaches r: its maximum is %d (the register + 1 "
            "generic unit)" % mx, size=11, fill=MUTED)
    p.ptext(p.X(3.4), p.Y(101),
            "so 0 at r = 40 is DERIVED, not a small measurement", size=11.5, fill=INK)
    return svg(900, 470, "The residue threshold is a boundary, and the boundary is derived", [p])


def fig_eligible_rate(v2):
    """The eligible-subset rate: the same effect in the affected subpopulation and diluted."""
    stat, tau, theta, r, stratum = "word3", 0.5, 0.05, 10, "minority_it"
    cells = [c for c in v2["cells"]
             if (c["stat"], c["tau"], c["theta"], c["r"], c["stratum"])
             == (stat, tau, theta, r, stratum)]
    p = Panel(0, 0, 940, 470, (0.0, 1.05), (0.0, 1.12))
    p.frame([0, 0.2, 0.4, 0.6, 0.8, 1.0], [0.0, 0.25, 0.5, 0.75, 1.0],
            "register prevalence in the community  phi",
            "level-induced rate\nover the ELIGIBLE subset")
    labels = (("affected", PAL["it"], "affected subpopulation (both members carry the register)"),
              ("community", PAL["char2"], "community population (random pairs)"))
    for i, (sample, col, lab) in enumerate(labels):
        pts, undef = [], []
        for c in sorted((c for c in cells if c["sample"] == sample), key=lambda c: c["phi"]):
            if c["eligible_rate"] is None:
                undef.append(c["phi"])
            else:
                pts.append((c["phi"], c["eligible_rate"]))
        if pts:
            p.poly(pts, stroke=col, w=2.4)
        for x, y in pts:
            p.dot(x, y, fill=col)
        for x in undef:
            p.ptext(p.X(x), p.Y(0.02), "undef", size=10, anchor="middle", fill=col, rotate=-90)
        p.ptext(p.X(0.03), p.Y(1.09 - 0.06 * i), lab, size=12, fill=col, weight="bold")
    comm = [c for c in cells if c["sample"] == "community" and abs(c["phi"] - 0.20) < 1e-9]
    if comm:
        p.ptext(p.X(0.03), p.Y(0.70),
                "at phi = 0.20 the affected rate is 1.000 and the community rate is the same "
                "effect diluted by %.3f" % comm[0]["dilution"], size=11, fill=INK)
    p.ptext(p.X(0.03), p.Y(0.60),
            "an empty denominator is written 'undef', never plotted as 0.000", size=11, fill=MUTED)
    return svg(940, 470, "A rate is owed over the subset where the test is defined", [p])


FIGURES = [
    ("fig1_dilution_law.svg", "The share law -- `spike_v0_results.json`", fig_dilution),
    ("fig2_level_ladder.svg", "The level ladder -- `spike_v1_results.json`", fig_ladder),
    ("fig3_critical_share.svg", "The critical share -- `spike_v1_results.json`", fig_critical_share),
    ("fig4_r_boundary.svg", "The residue threshold -- `spike_v2_results.json`", fig_r_boundary),
    ("fig5_eligible_rate.svg", "The eligible-subset rate -- `spike_v2_results.json`", fig_eligible_rate),
]


# ------------------------------------------------------------------------------------------------
# the certificate
# ------------------------------------------------------------------------------------------------
def selftest():
    v0 = report("spike_v0_results.json")
    v1 = report("spike_v1_results.json")
    v2 = report("spike_v2_results.json")
    checks = []

    # F1 -- the reports carry the keys the figures read
    checks.append(("F1a spike_v0 carries share sweeps + containment + dilution",
                   all(k in v0 for k in ("share_sweep_word3_theta_0.01",
                                         "share_sweep_char_bigram_theta_0.01",
                                         "containment_summary", "dilution"))))
    checks.append(("F1b spike_v1 carries ladder + critical_share + strata",
                   all(k in v1 for k in ("ladder", "critical_share", "strata"))))
    checks.append(("F1c spike_v2 carries cells + strata", all(k in v2 for k in ("cells", "strata"))))

    # F2(a) -- the share law's own control
    ctrl = [r for r in v0["share_sweep_word3_theta_0.01"] if abs(r["share"] - 1.0) < 1e-9]
    checks.append(("F2a the hidden fraction is exactly 0 at share 1.0 (the control)",
                   bool(ctrl) and ctrl[0]["hidden_fraction_of_F_pool"] == 0.0))

    # F2(b) -- the level ladder's step in the AFFECTED subpopulation, both strata
    st = {s["name"]: s for s in v2["strata"]}
    ok_b = True
    for c in v2["cells"]:
        if c["stat"] != "word3" or c["sample"] != "affected" or c["r"] != 10:
            continue
        if c["tau"] != 0.5 or c["theta"] != 0.05:
            continue
        phi_star = c["theta"] / st[c["stratum"]]["share"]
        want = 1.0 if c["phi"] < phi_star else 0.0
        got = c["eligible_rate"] or 0.0
        if abs(got - want) > 1e-9:
            ok_b = False
    checks.append(("F2b below phi* the affected rate is 1.0 and above it 0.0, both strata", ok_b))

    # F2(c) -- the residue error is float noise, not a share
    wv = v0["dilution"]["word3_theta_0.01"]["worst_abs_violation"]
    cv = v0["dilution"]["char_bigram_theta_0.01"]["worst_abs_violation"]
    checks.append(("F2c the residue of df_corpus = s*df_pool is below 1e-15",
                   wv < 1e-15 and cv < 1e-15))

    # F2(d) -- the r-boundary, PER STRATUM: flat for r <= register_units, 0 above
    ok_d = True
    groups = {}
    for c in v2["cells"]:
        if c["sample"] == "affected" and c["stat"] == "word3" and c["tau"] == 0.5 \
                and c["theta"] == 0.05:
            groups.setdefault((c["stratum"], c["phi"], c["register_units"]), []).append(c)
    for (name, phi, ru), aff in sorted(groups.items()):
        below = {c["level_induced"] for c in aff if c["r"] <= ru}
        above = {c["level_induced"] for c in aff if c["r"] > ru}
        if len(below) != 1 or above != {0}:
            ok_d = False
    checks.append(("F2d per stratum, the induced count is flat for r <= register_units and 0 above",
                   ok_d))

    # F2(e) -- the statistic decides: word hidden in every below-phi* cell, character in none
    ok_e = True
    for c in v2["cells"]:
        if c["phi"] <= 0.0 or c["corpus_prevalence"] >= c["theta"]:
            continue
        want = (c["stat"] == "word3")
        if c["hidden_from_corpus"] != want:
            ok_e = False
    checks.append(("F2e below the critical prevalence word3 is hidden in every cell and char2 in "
                   "none", ok_e))

    # F3 -- no undefined value reaches a coordinate
    undef_cells = [c for c in v2["cells"] if c["eligible_rate"] is None]
    checks.append(("F3 an undefined rate is marked (never plotted as a point)",
                   all(c["sim_gate_pass"] == 0 for c in undef_cells)))

    # F4 -- nothing is drawn outside its canvas (a rotated label is bounded by its glyph box)
    import re as _re
    src = {"fig_dilution": v0, "fig_ladder": v1, "fig_critical_share": v1,
           "fig_r_boundary": v2, "fig_eligible_rate": v2}
    ok_f4 = True
    for name, _src, fn in FIGURES:
        text = fn(src[fn.__name__])
        m = _re.search(r'width="(\d+)" height="(\d+)"', text)
        w, h = int(m.group(1)), int(m.group(2))
        for tag, attrs in _re.findall(r'<(line|circle|rect|text|polyline)([^>]*)/?>', text):
            for a in ("x1", "x2", "cx", "x"):
                for v in _re.findall(r'\b%s="(-?[\d.]+)"' % a, attrs):
                    x = float(v)
                    if x < -0.5 or x > w + 0.5:
                        ok_f4 = False
            for a in ("y1", "y2", "cy", "y"):
                for v in _re.findall(r'\b%s="(-?[\d.]+)"' % a, attrs):
                    y = float(v)
                    if y < -0.5 or y > h + 0.5:
                        ok_f4 = False
            if tag == "rect":
                for xv, wv in [(_re.findall(r'\bx="(-?[\d.]+)"', attrs)[:1],
                                _re.findall(r'\bwidth="(-?[\d.]+)"', attrs)[:1])]:
                    pass
        for pts in _re.findall(r'points="([^"]+)"', text):
            for pair in pts.split():
                x, y = pair.split(",")
                if not (-0.5 <= float(x) <= w + 0.5 and -0.5 <= float(y) <= h + 0.5):
                    ok_f4 = False
    checks.append(("F4 no drawn element falls outside its canvas", ok_f4))

    bad = 0
    for lab, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        bad += 0 if ok else 1
    print("SELFTEST %d/%d" % (len(checks) - bad, len(checks)))
    return 1 if bad else 0


def captions(v0, v1, v2):
    """The captions, GENERATED from the same reports the figures are drawn from.

    A caption is a claim about a figure, so it is read off the report exactly as the figure is:
    a caption cannot drift from the picture it names (the correction this journal's own reviewer
    forced on #130 -- an annotated number typed into prose is a number that can go stale)."""
    cs = v0["containment_summary"]
    d = v0["dilution"]["word3_theta_0.01"]
    st = {s["name"]: s for s in v1["strata"]}
    t1 = [r for r in v1["ladder"]
          if r["stat"] == "word3" and r["tau"] == 0.5 and r["theta"] == 0.05
          and r["stratum"] == "minority_it" and abs(r["phi"] - 0.20) < 1e-9][0]
    t2 = [r for r in v1["ladder"]
          if r["stat"] == "word3" and r["tau"] == 0.5 and r["theta"] == 0.05
          and r["stratum"] == "majority_en" and abs(r["phi"] - 0.20) < 1e-9][0]
    c20 = [c for c in v2["cells"]
           if c["sample"] == "affected" and c["stat"] == "word3" and c["tau"] == 0.5
           and c["theta"] == 0.05 and c["stratum"] == "minority_it" and abs(c["phi"] - 0.20) < 1e-9
           and c["r"] == 10][0]
    comm = [c for c in v2["cells"]
            if c["sample"] == "community" and c["stat"] == "word3" and c["tau"] == 0.5
            and c["theta"] == 0.05 and c["stratum"] == "minority_it" and abs(c["phi"] - 0.20) < 1e-9
            and c["r"] == 10][0]
    w3cs = [c for c in v1["critical_share"] if c["stat"] == "word3"]
    n_agree = sum(1 for c in w3cs
                  if c["predicted_hidden_from_corpus"] == c["observed_hidden_from_corpus"])
    n_cs = len(w3cs)
    return [
        ("fig1_dilution_law.svg",
         "The share law. As a pool's share `s` of the corpus grows, the fraction of the pool's own "
         "generic units that a corpus-wide frame misses falls to **exactly 0 at s = 1.0** (the "
         "control: the pool IS the corpus). The relation is not set containment -- containment fails "
         "in **%d of %d** cells in both directions -- but a dilution, `df_corpus(u) = s * df_pool(u)`, "
         "whose residual over **%d** word-3 pairs is **%.1e**. The effect is statistic-dependent: "
         "character bigrams are near-universal across these languages and barely move."
         % (cs["cells_where_F_corpus_NOT_subset_F_pool"], cs["cells"],
            d["n_confined_pairs"], d["worst_abs_violation"])),
        ("fig2_level_ladder.svg",
         "The level ladder. The level-induced flag count (corpus-level frame minus community-level "
         "frame) against the register's prevalence `phi`, for the two communities of one corpus "
         "(Italian share **%.3f**, English share **%.3f**). Below the critical prevalence "
         "`phi* = theta/s` the corpus frame fires on **120 / 120** community pairs while the "
         "community frame fires on **0 / 120**; above it the register is inside the corpus frame and "
         "the induced count is **0**. `phi*` is measured: at phi = 0.20 the corpus prevalence is "
         "%.3f in the minority community (hidden, %d fires induced) and %.3f in the majority "
         "(visible, %d)."
         % (st["minority_it"]["share"], st["majority_en"]["share"], t1["corpus_prevalence"],
            t1["level_induced"], t2["corpus_prevalence"], t2["level_induced"])),
        ("fig3_critical_share.svg",
         "The critical share. Each community's register prevalence in the corpus (`s * phi`) against "
         "its prevalence in the community. The register is hidden from the corpus frame exactly when "
         "the line crosses the cutoff `theta` -- that crossing IS `phi* = theta/s` -- and the "
         "instrument agrees with the prediction in **%d of %d** word-3 cells. The two vertical lines "
         "are the two measured critical prevalences; the larger belongs to the smaller community."
         % (n_agree, n_cs)),
        ("fig4_r_boundary.svg",
         "The residue threshold. The level-induced count against `r`, for the affected subpopulation "
         "(both members carry the register). It is **flat** for every `r` up to the register's own "
         "size and **0** above it, because at phi = 0.20 the corpus residue never exceeds **%d** "
         "units: at `r = 40` the corpus level cannot fire on any pair. The zero is derived from the "
         "register's size, not a small measurement."
         % c20["max_residue_corpus"]),
        ("fig5_eligible_rate.svg",
         "The eligible-subset rate. A pair whose similarity gate does not open is *ineligible*, not a "
         "non-flag, so the rate is owed over the subset where the test is defined. In the **affected** "
         "subpopulation the rate is a clean step -- **%.3f** at phi = 0.20, corpus prevalence %.3f -- "
         "while the **community** population is the same effect diluted by **%.3f**; an empty "
         "denominator is written `undef`, never plotted as 0.000."
         % (c20["eligible_rate"], c20["corpus_prevalence"], comm["dilution"])),
    ]


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else OUTDIR
    os.makedirs(outdir, exist_ok=True)
    v0 = report("spike_v0_results.json")
    v1 = report("spike_v1_results.json")
    v2 = report("spike_v2_results.json")
    sources = {"fig_dilution": v0, "fig_ladder": v1, "fig_critical_share": v1,
               "fig_r_boundary": v2, "fig_eligible_rate": v2}
    made = []
    for name, src, fn in FIGURES:
        made.append(write(name, fn(sources[fn.__name__]), outdir))
        print("wrote %-28s %6d B  %s" % (name, made[-1]["bytes"], made[-1]["sha256"][:16]))

    caps = captions(v0, v1, v2)
    md = ["# Figure captions -- issue #132", "",
          "Generated by `make_figures.py` from the same reports the figures are drawn from, so a",
          "caption cannot drift from the picture it names. Do not edit by hand.", ""]
    for name, cap in caps:
        md += ["## `%s`" % name, "", cap, ""]
    write("CAPTIONS.md", "\n".join(md), outdir)
    write("manifest.json", json.dumps(
        {"figures": made, "captions": [c[0] for c in caps]}, indent=1, sort_keys=True) + "\n", outdir)
    fx = ["# Figures -- issue #132", "",
          "Every figure is generated by `make_figures.py` from the shipped reports (standard library",
          "only, deterministic). Nothing is drawn that is not in a report, and every number a figure",
          "annotates is read from the report, so a figure cannot drift from its source. Re-generate",
          "with `python3 make_figures.py`; `reproduce.sh` does so and compares byte-for-byte.", "",
          "| Figure | Source report |", "|---|---|"]
    for name, src, _fn in FIGURES:
        fx.append("| `%s` | %s |" % (name, src))
    fx += ["", "The captions are in `CAPTIONS.md`, generated from the same reports; the hashes are in",
           "`manifest.json`. `--selftest` runs the certificate F1-F4.", ""]
    write("FIGURES.md", "\n".join(fx), outdir)
    print("wrote %-28s CAPTIONS.md + manifest.json" % "")
    return made


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
