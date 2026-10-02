#!/usr/bin/env python3
"""Issue #118 -- the four figures, drawn from canonical_results.json.

Figure 1 (frontier): the critical-capacity frontier C_min(mu) for a UNIFORM router,
  each point one (E, T) cell, the vertical bar through it the move of C_min when the
  DECLARED tolerance moves 1e-3 -> 1e-9. The point of the figure: the two folk
  constants are horizontal lines, and they sit BELOW the frontier over most of the
  load range -- the constant is a point on this curve that was never read off it.

Figure 2 (ceiling): the ceiling from both sides. Left: the uniform floor against 20
  Dirichlet-skew cells (skew only adds). Right: a MEASURED router's C_min against the
  strength of its balancing loss, with the same floor drawn in -- balancing converges
  to the floor from above and never crosses it.

Figure 3 (inversion): what C = 1.25 actually accepts, D(C=1.25) against mu on a log
  axis. The point of the figure: one constant, four orders of magnitude of behaviour.

Figure 4 (composition): the dispatch arm. Left: where the drops are (arrival decile,
  against the uniform null). Right: the displacement exchange rate -- exactly 1:1 and
  saturating at ONE expert's capacity.

Everything is stdlib: plotlib.py (a raster canvas + 3x5 font + zlib PNG writer,
reused from issues #114 / #116) -- no matplotlib, and the bytes are a function of the
series alone.
"""
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, ".")
from plotlib import (Canvas, Axes, BLACK, BLUE, RED, GREEN, GREY, WHITE,  # noqa: E402
                     ORANGE, LIGHT)

FIG_W, FIG_H = 1120, 700
SC = 1                      # text scale for the axis annotations
GW, GG, GH = 3, 1, 5        # plotlib's glyph metrics

L10 = math.log10


def tw(s, scale=SC):
    """Pixel width of a string in plotlib's 3x5 font."""
    return len(s) * (GW + GG) * scale - GG * scale


def dashed_h(c, y, x0, x1, color, dash=6, gap=5):
    x = x0
    while x < x1:
        c.line(x, y, min(x + dash, x1), y, color, 1)
        x += dash + gap


def dashed_v(c, x, y0, y1, color, dash=6, gap=5):
    y = y0
    while y < y1:
        c.line(x, y, x, min(y + dash, y1), color, 1)
        y += dash + gap


def ticks_x(c, ax, vals, labels, scale=SC):
    for v, lab in zip(vals, labels):
        x = int(round(ax.X(v)))
        c.line(x, ax.y1, x, ax.y1 + 3 * scale, BLACK)
        c.text(int(x - tw(lab, scale) / 2), ax.y1 + 6 * scale, lab, BLACK, scale)


def ticks_y(c, ax, vals, labels, scale=SC):
    for v, lab in zip(vals, labels):
        y = int(round(ax.Y(v)))
        c.line(ax.x0 - 3 * scale, y, ax.x0, y, BLACK)
        c.text(int(ax.x0 - 6 * scale - tw(lab, scale)), int(y - GH * scale / 2), lab,
               BLACK, scale)


def xlabel(c, ax, s, scale=SC):
    c.text(int((ax.x0 + ax.x1) / 2 - tw(s, scale) / 2), ax.y1 + 20 * scale, s, BLACK, scale)


def ylabel(c, ax, s, scale=SC):
    ax._vtext(int(ax.x0 - 40 * scale), int((ax.y0 + ax.y1) / 2), s, scale)


def write(c, path):
    """Save and report the file, its size and its digest -- never the bytes."""
    png = c.save(path)
    h = hashlib.sha256(png).hexdigest()
    print("wrote %s  %d B  sha256 %s" % (path, len(png), h))
    return h


def load():
    with open("canonical_results.json") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
def fig_frontier(res, path):
    curve = res["steps"]["spike_v1"]["curve"]
    ti = res["steps"]["probe_uniform"]["tolerance_indexed"]
    c = Canvas(FIG_W, FIG_H, WHITE)
    ax = Axes(c, (150, 110, 900, 480), (L10(0.85), L10(150.0)), (1.0, 9.2),
              xticks=[], yticks=[])
    ax.frame()
    # ONE cell carries its exact tolerance-indexed readings. They are drawn as a labelled
    # bar from the exact route -- NOT from spike_v1's c_tol1e3/c_tol1e9 columns, which are
    # the closed form's own readings and are not valid below mu ~ 8 (section 5.4).
    vals = [r["c_min"] for r in ti["readings"]]
    assert vals[0] < vals[1] < vals[2], "the tolerance-indexed readings are not ordered"
    x_ti = L10(ti["T"] / ti["E"])
    c.line(ax.X(x_ti), ax.Y(vals[0]), ax.X(x_ti), ax.Y(vals[2]), GREY, 3)
    ax.points([x_ti] * 3, vals, GREY, r=3)
    for tol, v in zip([r["tol"] for r in ti["readings"]], vals):
        lab = "TOL %.0E -> %.3F" % (tol, v)
        c.text(int(ax.X(x_ti) - 8 - tw(lab)), int(ax.Y(v)) - 6, lab, GREY, SC)
    ticks_x(c, ax, [L10(v) for v in (1, 2, 4, 8, 16, 32, 64, 128)],
            ["1", "2", "4", "8", "16", "32", "64", "128"])
    ticks_y(c, ax, [1, 2, 3, 4, 5, 6, 7, 8, 9], ["1", "2", "3", "4", "5", "6", "7", "8", "9"])
    xlabel(c, ax, "PER-EXPERT LOAD MU = TOPK * T / E   (LOG SCALE)")
    ylabel(c, ax, "CRITICAL CAPACITY FACTOR C_MIN")

    dashed_h(c, ax.Y(1.25), ax.x0, ax.x1, RED)
    dashed_h(c, ax.Y(2.00), ax.x0, ax.x1, GREEN)
    ax.points([L10(r["mu"]) for r in curve], [r["c_min"] for r in curve], BLUE, r=4)
    dashed_v(c, ax.X(L10(8.3)), ax.y0, ax.y1, GREY)
    c.text(ax.X(L10(8.3)) + 5, ax.y0 + 18, "MU = 2 LN E = 8.3 (E = 64)", GREY, SC)
    c.text(ax.x0 + 8, int(ax.Y(1.25)) - 14, "C = 1.25  (Switch Transformer)", RED, SC)
    c.text(ax.x0 + 8, int(ax.Y(2.00)) - 14, "C = 2.00  (GShard)", GREEN, SC)

    c.text(150, 545, "EACH BLUE POINT IS ONE (E, T) CELL OF A PERFECTLY UNIFORM ROUTER -- THE BALANCING IDEAL,", BLACK, SC)
    c.text(150, 563, "THE STRONGEST POSSIBLE CASE FOR THE FOLK CONSTANT. THE GREY BAR AT MU = 16 IS THE SAME", BLACK, SC)
    c.text(150, 581, "CELL READ AT THREE DECLARED TOLERANCES BY THE EXACT ROUTE: A C_MIN IS A READING *AT* A", BLACK, SC)
    c.text(150, 599, "TOLERANCE, NEVER A PROPERTY OF THE ROUTER ALONE. C = 1.25 IS INSIDE THE FRONTIER ONLY", BLACK, SC)
    c.text(150, 617, "ABOVE MU ~ 64.", BLACK, SC)
    c.text(150, 648, "THE DASHED RULE AT MU = 8.3 IS THE REGISTERED BOUNDARY: BELOW IT THE CONSTANT'S RELATIVE", RED, SC)
    c.text(150, 666, "HEADROOM 0.25*MU IS SMALLER THAN THE FLUCTUATION OF THE BUSIEST OF E EXPERTS.", RED, SC)
    return write(c, path)


# --------------------------------------------------------------------------
def fig_ceiling(res, path):
    ceil = res["steps"]["spike_v1"]["ceiling"]
    ar = res["steps"]["model_v3"]["arm2_measured_router"]
    floor = res["steps"]["probe_uniform"]["floor"]["c_min"]
    c = Canvas(FIG_W, FIG_H, WHITE)

    ax = Axes(c, (140, 110, 540, 450), (-0.5, 3.5), (L10(1.8), L10(55.0)),
              xticks=[], yticks=[])
    ax.frame()
    ticks_x(c, ax, list(range(4)), ["%d/%g" % (r["E"], r["mu"]) for r in ceil])
    ticks_y(c, ax, [L10(v) for v in (2, 5, 10, 20, 50)], ["2", "5", "10", "20", "50"])
    xlabel(c, ax, "CELL   E / MU")
    ylabel(c, ax, "C_MIN  (LOG)")
    for i, r in enumerate(ceil):
        lo = min(r["uniform"], min(s["c_min"] for s in r["skew"]))
        assert r["uniform"] <= min(s["c_min"] for s in r["skew"]) + 1e-9, \
            "a skewed cell at E=%s is BELOW the uniform floor" % r["E"]
        assert lo > 1.0, "a ceiling cell read below C = 1"
        ax.points([i], [L10(r["uniform"])], BLUE, r=4)
        for j, s in enumerate(r["skew"]):
            ax.points([i + (j - 2) * 0.13], [L10(s["c_min"])], RED, r=2)
        c.text(int(ax.X(i)) - 10, int(ax.Y(L10(r["uniform"]))) + 10,
               "%.2f" % r["uniform"], BLUE, SC)
    c.text(150, 470, "BLUE = PERFECTLY UNIFORM ROUTER. RED = 5 DIRICHLET-SKEW CELLS (ALPHA 2 .. 0.05).", BLACK, SC)
    c.text(150, 488, "20 OF 20 SKEW CELLS SIT ABOVE THE UNIFORM FLOOR AND NONE BELOW: SKEW ONLY ADDS.", BLACK, SC)

    ax2 = Axes(c, (700, 110, 1080, 450), (-0.5, 5.5), (1.0, 4.6), xticks=[], yticks=[])
    ax2.frame()
    ticks_x(c, ax2, list(range(6)), ["%g" % r["aux_w"] for r in ar["sweep"]])
    ticks_y(c, ax2, [1, 2, 3, 4], ["1", "2", "3", "4"])
    xlabel(c, ax2, "AUXILIARY BALANCING WEIGHT")
    ylabel(c, ax2, "MEASURED C_MIN")
    means = [r["c_min"] for r in ar["sweep"]]
    ax2.plot(list(range(len(means))), means, GREEN, width=2)
    ax2.points(list(range(len(means))), means, GREEN, r=4)
    dashed_h(c, ax2.Y(floor), ax2.x0, ax2.x1, RED)
    c.text(ax2.x0 + 6, int(ax2.Y(floor)) - 14, "UNIFORM FLOOR C_MIN = %.4f" % floor, RED, SC)
    assert all(m > floor for m in means), "a measured-router cell read AT OR BELOW the floor"
    assert means[0] > means[-1], "the measured C_min does not fall as balancing is strengthened"
    c.text(710, 470, "A TOY MOE TRAINED ON CPU (E = 16 EXPERTS, 32 CLASSES, T = 8192, 3 SEEDS/CELL).", BLACK, SC)
    c.text(710, 488, "BALANCING DRIVES C_MIN %.2f -> %.2f AND STOPS: IT APPROACHES THE FLOOR FROM ABOVE."
           % (means[0], means[-1]), GREEN, SC)
    return write(c, path)


# --------------------------------------------------------------------------
def fig_inversion(res, path):
    cells = res["steps"]["probe_uniform"]["cells"]
    c = Canvas(FIG_W, FIG_H, WHITE)
    ax = Axes(c, (170, 110, 900, 480), (L10(0.85), L10(150.0)), (L10(5e-5), L10(0.6)),
              xticks=[], yticks=[])
    ax.frame()
    ticks_x(c, ax, [L10(v) for v in (1, 2, 4, 8, 16, 32, 64, 128)],
            ["1", "2", "4", "8", "16", "32", "64", "128"])
    ticks_y(c, ax, [L10(v) for v in (1e-1, 1e-2, 1e-3, 1e-4)],
            ["1E-1", "1E-2", "1E-3", "1E-4"])
    xlabel(c, ax, "PER-EXPERT LOAD MU = T / E   (LOG SCALE)")
    ylabel(c, ax, "DROPPED-TOKEN RATE AT C = 1.25  (LOG)")
    # D falls in mu at FIXED E. Across different E the ordering is not guaranteed (the family
    # offset IS the point of the figure), so the assertion is made inside each E group.
    for E in sorted({r["E"] for r in cells}):
        seq = [r["drop_at_folk"] for r in sorted((r for r in cells if r["E"] == E),
                                                 key=lambda r: r["mu"])]
        assert all(b < a for a, b in zip(seq, seq[1:])), \
            "D(C=1.25) does not fall in mu at E = %d" % E
    # the E = 64 sweep carries the line; the other two cells are points on the same curve
    line = sorted((r for r in cells if r["E"] == 64), key=lambda r: r["mu"])
    ax.plot([L10(r["mu"]) for r in line], [L10(r["drop_at_folk"]) for r in line], RED, width=2)
    for r in cells:
        col = RED if r["E"] == 64 else BLUE
        ax.points([L10(r["mu"])], [L10(r["drop_at_folk"])], col, r=4)
    for r in cells:
        if r["E"] != 64:
            c.text(int(ax.X(L10(r["mu"]))) + 8, int(ax.Y(L10(r["drop_at_folk"]))) - 6,
                   "E = %d" % r["E"], BLUE, SC)
    dashed_h(c, ax.Y(L10(1e-2)), ax.x0, ax.x1, GREY)
    c.text(ax.x0 + 8, int(ax.Y(L10(1e-2))) - 14, "1E-2  = THE TOLERANCE THE CONSTANT IMPLIES AT MU = 128", GREY, SC)
    lo = min(cells, key=lambda r: r["mu"])
    hi = max(cells, key=lambda r: r["mu"])
    c.text(int(ax.X(L10(lo["mu"]))) + 8, int(ax.Y(L10(lo["drop_at_folk"]))) - 14,
           "%.1f%% AT MU = 1" % (100 * lo["drop_at_folk"]), RED, SC)
    c.text(int(ax.X(L10(hi["mu"]))) - 96, int(ax.Y(L10(hi["drop_at_folk"]))) - 14,
           "%.1E AT MU = 128" % hi["drop_at_folk"], RED, SC)
    c.text(170, 545, "ONE CONSTANT, FOUR ORDERS OF MAGNITUDE OF BEHAVIOUR. C = 1.25 IS NOT WRONG -- IT IS", BLACK, SC)
    c.text(170, 563, "UNLABELLED: IT SILENTLY COMMITS A DEPLOYMENT TO WHATEVER DROP RATE ITS LOAD IMPLIES.", BLACK, SC)
    c.text(170, 590, "THE ACTIONABLE READING: READ THE TARGET DROP RATE OFF THIS CURVE, THEN THE CAPACITY.", BLUE, SC)
    c.text(170, 617, "A C_MIN IS A READING AT A DECLARED TOLERANCE (HERE 1E-6); WITHOUT THE TOLERANCE IT IS", BLACK, SC)
    c.text(170, 635, "NOT A MEASUREMENT.", BLACK, SC)
    return write(c, path)


# --------------------------------------------------------------------------
def fig_composition(res, path):
    p3 = res["steps"]["model_v2"]["p3"]
    c = Canvas(FIG_W, FIG_H, WHITE)

    ax = Axes(c, (140, 110, 560, 440), (-0.5, 2.5), (0.0, 0.62), xticks=[], yticks=[])
    ax.frame()
    ticks_x(c, ax, list(range(len(p3))), ["ALPHA=%g" % r["alpha"] for r in p3])
    ticks_y(c, ax, [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6"])
    xlabel(c, ax, "SKEW OF THE ROUTER (DIRICHLET ALPHA)")
    ylabel(c, ax, "SHARE OF ALL DROPS")
    for i, r in enumerate(p3):
        assert r["first_decile_share"] == 0.0, \
            "the positional asymmetry is not total: first decile = %.3f" % r["first_decile_share"]
        xs = [i - 0.26, i, i + 0.26]
        hs = [r["first_decile_share"], r["last_decile_share"], r["hot_expert_share"]]
        for x, h, col in zip(xs, hs, (GREY, RED, ORANGE)):
            c.rect(int(ax.X(x)) - 12, int(ax.Y(h)), int(ax.X(x)) + 12, int(ax.Y(0.0)), col, fill=True)
    dashed_h(c, ax.Y(0.10), ax.x0, ax.x1, GREY)
    c.text(ax.x0 + 6, int(ax.Y(0.10)) - 14, "UNIFORM NULL 10%", GREY, SC)
    c.text(140, 480, "GREY = FIRST DECILE OF ARRIVALS (NULL 10%)", GREY, SC)
    c.text(140, 498, "RED = LAST DECILE (NULL 10%)", RED, SC)
    c.text(140, 516, "ORANGE = THE SINGLE HOTTEST EXPERT (NULL 1.6%)", ORANGE, SC)
    c.text(140, 540, "NO DROP LANDS IN THE FIRST DECILE OF A DEPLETED EXPERT'S ARRIVALS.", BLACK, SC)

    ax2 = Axes(c, (720, 110, 1080, 440), (-8, 88), (0.0, 26.0), xticks=[], yticks=[])
    ax2.frame()
    ticks_x(c, ax2, [0, 20, 40, 60, 80], ["0", "20", "40", "60", "80"])
    ticks_y(c, ax2, [0, 5, 10, 15, 20, 25], ["0", "5", "10", "15", "20", "25"])
    xlabel(c, ax2, "ATTACKER LOAD L BEFORE THE VICTIM (TOKENS)")
    ylabel(c, ax2, "VICTIM TOKENS DISPLACED")
    for i, r in enumerate(p3):
        d = r["displacement"]
        base = d[0][1]
        caps = [r["cap"]]
        for L, v in d:
            assert v - base == min(L, r["cap"]), \
                "displacement at L=%d is %d, not min(L, cap=%d)=%d" % (L, v - base, r["cap"],
                                                                       min(L, r["cap"]))
        col = (BLUE, GREEN, ORANGE)[i]
        xs = [L for L, _ in d]
        ys = [v - base for _, v in d]
        ax2.plot(xs, ys, col, width=2)
        ax2.points(xs, ys, col, r=3)
        c.text(ax2.x1 - 210, int(ax2.Y(r["cap"])) - 12 - 13 * i,
               "CAP = %d TOKENS (ALPHA=%g)" % (r["cap"], r["alpha"]), col, SC)
    c.text(720, 480, "DISPLACEMENT IS EXACTLY MIN(L, CAP) IN EVERY CELL TESTED: ONE ATTACKER TOKEN", BLACK, SC)
    c.text(720, 498, "DISPLACES EXACTLY ONE VICTIM TOKEN UNTIL THE EXPERT'S CAPACITY IS SPENT.", BLACK, SC)
    c.text(720, 524, "PAST THE CAP THE ATTACKER'S OWN TOKENS ARE DROPPED AND DISPLACE NOBODY: THE 2026", RED, SC)
    c.text(720, 542, "CAPACITY-OVERFLOW CHANNEL HAS A HARD BUDGET OF ONE CAPACITY PER TARGETED EXPERT.", RED, SC)
    return write(c, path)


# --------------------------------------------------------------------------
def main():
    os.makedirs("figures_draft", exist_ok=True)
    res = load()
    jobs = [(fig_frontier, "figures_draft/fig1_frontier.png"),
            (fig_ceiling, "figures_draft/fig2_ceiling.png"),
            (fig_inversion, "figures_draft/fig3_inversion.png"),
            (fig_composition, "figures_draft/fig4_composition.png")]
    digests = {}
    for fn, p in jobs:
        digests[os.path.basename(p)] = fn(res, p)
    # determinism: render again into a scratch path and require the same digest
    for fn, p in jobs:
        q = p.replace(".png", "_rerun.png")
        assert fn(res, q) == digests[os.path.basename(p)], "%s is NOT deterministic" % p
        os.remove(q)
    print("DETERMINISM: all four figures byte-identical across two renders")
    art = hashlib.sha256(open("canonical_results.json", "rb").read()).hexdigest()
    man = {"artefact_sha256": art,
           "note": "every figure is a view of canonical_results.json; regenerate with "
                   "`python3 make_figures.py` and compare by sha256",
           "figures": {k: {"bytes": os.path.getsize("figures_draft/" + k), "sha256": v}
                       for k, v in sorted(digests.items())}}
    with open("figures_draft/manifest.json", "w") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
    print("wrote figures_draft/manifest.json  (artefact sha256 %s)" % art[:16])


if __name__ == "__main__":
    main()
