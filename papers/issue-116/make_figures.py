#!/usr/bin/env python3
"""Issue #116 -- the first two figures, drawn from canonical_results.json.

Figure 1 (frontier.png): L*(lam_c) for the well-damped plant at several tau, with
  the FEASIBLE WINDOW shaded, the floor and ceiling drawn as boundaries, and the
  LATENCY WALL annotated. The point of the figure: the optimum is pinned at the
  floor when inference is cheap and at the ceiling when it is expensive, and the
  priced region in between is where the law lives.

Figure 2 (exponent.png): the measured exponent of L* in lam_c, by plant and tau,
  with its 95% regression interval. The point of the figure: sqrt (0.5) is inside
  the range but is NOT the centre -- the exponent is plant- and tau-dependent.

Everything is stdlib: plotlib.py (a raster canvas + 3x5 font + zlib PNG writer,
reused from issue #114) -- no matplotlib, and the bytes are a function of the
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

FIG_W, FIG_H = 900, 620


def dashed_h(c, y, x0, x1, color, dash=6, gap=5):
    """A dashed horizontal reference line (plotlib has no dashes)."""
    x = x0
    while x < x1:
        c.line(x, y, min(x + dash, x1), y, color, 1)
        x += dash + gap


def dashed_v(c, x, y0, y1, color, dash=6, gap=5):
    y = y0
    while y < y1:
        c.line(x, y, x, min(y + dash, y1), color, 1)
        y += dash + gap


def write(c, path):
    """Save and report the file, its size and its digest -- never the bytes."""
    png = c.save(path)
    h = hashlib.sha256(png).hexdigest()
    print(f"wrote {path}  {len(png)} B  sha256 {h}")
    return h


def load():
    with open("canonical_results.json") as fh:
        return json.load(fh)


def fig_frontier(res, plant, taus, path):
    c = Canvas(FIG_W, FIG_H, WHITE)
    rec = res["plants"][plant]
    dmax = rec["dmax"]
    lams = [float(k) for k in res["lam_grid"]]
    lo, hi = math.log10(lams[0]) - 0.1, math.log10(lams[-1]) + 0.1
    ax = Axes(c, (110, 70, 850, 500), (lo, hi), (0.0, dmax + 1.0),
              xlabel="LOG10 LAMBDA_C   (INFERENCE PRICE PER QUERY)",
              ylabel="L* (EXECUTION HORIZON, STEPS)",
              xticks=[-2, -1, 0, 1, 2, 3, 4, 5],
              yticks=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
              xfmt="{:.0f}", yfmt="{:.0f}", scale=2,
              title="FRONTIER: OPTIMAL HORIZON VS INFERENCE PRICE")
    # NOTE: the latency wall is a TAU coordinate, not a horizon value, so it is
    # stated in the caption rather than drawn as a horizontal line (drawing it at
    # y = d_max/2 put a tau-axis fact on the L* axis).
    colors = {0: BLUE, 1: GREEN, 2: GREY, 4: (120, 120, 190), 6: (190, 120, 60),
              8: (60, 160, 160)}
    for tau in taus:
        d = rec["tau"].get(str(tau))
        if not d:
            continue
        xs, ys = [], []
        for lam, L in zip(lams, d["Lstar"]):
            if L is None:
                continue
            xs.append(math.log10(lam))
            ys.append(L)
        col = colors.get(tau, BLACK)
        ax.plot(xs, ys, col, width=2)
        ax.points(xs, ys, col, r=3)
        # label each curve at its right end with the ceiling it is pinned to
        c.text(int(ax.X(xs[-1])) - 46, int(ax.Y(ys[-1])) - 16,
               f"T{tau} C{int(dmax - tau)}", col, 1)
    ax.frame()
    c.text(110, 528, "CURVES: TAU = 0 (BLUE), 1 (GREEN), 2 (GREY), 4 (MAUVE),"
                     " 6 (ORANGE), 8 (TEAL); LABELS READ T<TAU> C<CEILING = D_MAX-TAU>",
           BLACK, 1)
    c.text(110, 546, "EACH CURVE IS FLAT WHERE THE FLOOR (L = TAU) OR THE CEILING"
                     " BINDS; L* RISES WITH THE PRICE ONLY IN BETWEEN", BLACK, 1)
    c.text(110, 564, f"THE FEASIBLE WINDOW IS [TAU, D_MAX - TAU] = [TAU,"
                     f" {dmax} - TAU]: IT IS EMPTY FOR TAU >= D_MAX/2 = {dmax // 2}"
                     " (THE LATENCY WALL)", RED, 1)
    return write(c, path)


def fig_exponent(res, path):
    c = Canvas(FIG_W, FIG_H, WHITE)
    rows = []
    for plant, rec in res["plants"].items():
        for tau_s, d in rec["tau"].items():
            e = d.get("exponent")
            if e:
                rows.append((plant, int(tau_s), e["value"], e["ci95"]))
    rows.sort(key=lambda r: (r[0], r[1]))
    ylo, yhi = 0.0, 0.75
    ax = Axes(c, (300, 70, 850, 520), (0, len(rows)), (ylo, yhi),
              xlabel="CONFIGURATION (PLANT, TAU), SORTED",
              ylabel="EXPONENT OF L* IN LAMBDA_C",
              xticks=[], yticks=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
              yfmt="{:.1f}", scale=1,
              title="THE EXPONENT IS PLANT- AND TAU-DEPENDENT")
    # the sqrt reference line
    dashed_h(c, ax.Y(0.5), ax.x0, ax.x1, RED)
    for i, (plant, tau, e, ci) in enumerate(rows):
        x = ax.x0 + (i + 0.5) * (ax.x1 - ax.x0) / max(1, len(rows))
        c.line(x, int(ax.Y(ci[0])), x, int(ax.Y(ci[1])), GREY, 1)
        c.rect(int(x - 3), int(ax.Y(e)) - 3, int(x + 3), int(ax.Y(e)) + 3, BLUE)
    ax.frame()
    # legend by hand (three short lines of text)
    c.text(120, 560, "RED DASH = SQRT(2*LAM/S) = 0.500", RED, 1)
    c.text(120, 578, "BARS = 95 PCT REGRESSION INTERVAL", BLACK, 1)
    c.text(120, 596, f"N = {len(rows)} FITS OVER 4 PLANTS", BLACK, 1)
    return write(c, path)


def fig_regime(res, path):
    """The regime map: which cell of (tau, price) is floor-pinned, interior,
    ceiling-pinned, or infeasible -- one panel per plant. This is the paper's core
    construct in one picture, and it is the ONE place a tau-coordinate line
    (the latency wall) is correct, because tau is now an axis."""
    plants = ["scalar-stable a=0.9", "double-int R=1 (near-margin)",
              "double-int R=10", "double-int R=100 (well damped)"]
    rows = [int(t) for t in res["tau_grid"]]
    lams = [float(k) for k in res["lam_grid"]]
    lo, hi = math.log10(lams[0]) - 0.05, math.log10(lams[-1]) + 0.05
    c = Canvas(1120, 880, WHITE)
    c.text(40, 30, "THE REGIME MAP: WHERE THE OPTIMUM IS PRICED, FLOOR-PINNED,"
                   " CEILING-PINNED, OR INFEASIBLE", BLACK, 2)
    boxes = [(120, 110, 560, 370), (640, 110, 1080, 370),
             (120, 450, 560, 710), (640, 450, 1080, 710)]
    fill = {"floor": BLUE, "interior": WHITE, "ceiling": ORANGE,
            "infeasible": LIGHT, "none": WHITE}
    for bi, plant in enumerate(plants):
        rec = res["plants"][plant]
        dmax = rec["dmax"]
        bx0, by0, bx1, by1 = boxes[bi]
        ax = Axes(c, (bx0, by0, bx1, by1), (lo, hi), (0, len(rows)),
                  xticks=[-2, -1, 0, 1, 2, 3, 4, 5], yticks=[],
                  xfmt="{:.0f}", scale=1)
        colw = (bx1 - bx0) / len(lams)
        rowh = (by1 - by0) / len(rows)
        for j, tau in enumerate(rows):
            d = rec["tau"].get(str(tau))
            for i, lam in enumerate(lams):
                cls = "infeasible" if d is None else d["class"][i]
                x0 = int(round(bx0 + i * colw))
                y0 = int(round(by0 + j * rowh))
                x1 = int(round(bx0 + (i + 1) * colw)) - 1
                y1 = int(round(by0 + (j + 1) * rowh)) - 1
                c.rect(x0, y0, x1, y1, fill[cls], fill=True)
                c.rect(x0, y0, x1, y1, GREY, fill=False)
        # The latency wall, tau = d_max/2, drawn on the TAU axis (correct here).
        # It is ANCHORED TO THE DATA: the first row the plot itself calls
        # infeasible, so the line can never contradict the cells beneath it.
        j_inf = next((j for j, tau in enumerate(rows)
                      if rec["tau"].get(str(tau)) is None), None)
        if j_inf is not None:
            dashed_h(c, int(round(by0 + j_inf * rowh)), bx0, bx1, RED)
        ax.frame()
        wall_note = f"WALL TAU={dmax/2:g}" if j_inf is not None else \
            f"WALL TAU={dmax/2:g} BEYOND GRID"
        c.text(bx0, by0 - 20, f"{plant.upper()}  (D_MAX={dmax}, {wall_note})", BLACK, 1)
        for j, tau in enumerate(rows):
            y = int(round(by0 + (j + 0.5) * rowh))
            c.text(bx0 - 26, y - 5, f"{tau:>2}", BLACK, 1)
        c.text(bx0 - 26, by0 - 20, "TAU", BLACK, 1)
    c.text(120, 750, "X AXIS: LOG10 LAMBDA_C (0.01 ... 100000).  Y AXIS: TAU."
                     "  RED LINE = LATENCY WALL (THE FIRST TAU THE WINDOW IS EMPTY).",
           BLACK, 1)
    en = [("FLOOR-PINNED (L*=TAU)", BLUE), ("INTERIOR (PRICED)", WHITE),
          ("CEILING-PINNED (L*=D_MAX-TAU)", ORANGE), ("INFEASIBLE / NOT SWEPT", LIGHT)]
    lx, ly = 120, 788
    for name, col in en:
        c.rect(lx, ly, lx + 12, ly + 10, col, fill=True)
        c.rect(lx, ly, lx + 12, ly + 10, GREY, fill=False)
        c.text(lx + 18, ly + 2, name, BLACK, 1)
        lx += 18 + len(name) * 5 + 22
    return write(c, path)


def fig_channels(res, path):
    """The two channels, side by side. LEFT: the mean channel adds a delay-INVARIANT
    term ||xbar||^2 to the cost, far above the covariance part. RIGHT: the shape
    channel's signature -- the sparse/gauss cost ratio RISES with the delay."""
    ch = res["channels"]
    dmax = 7
    ds = list(range(0, dmax + 1))
    trP = [ch["trP_centered_by_d"][str(d)] for d in ds]
    mt = [ch["mean_term_by_d"][str(d)]["mean_term"] for d in ds]
    sd = sorted(int(k) for k in ch["shape_ratio_by_d"])
    ratio = [ch["shape_ratio_by_d"][str(d)] for d in sd]

    c = Canvas(1060, 640, WHITE)
    c.text(40, 30, "THE TWO CHANNELS: A MEAN RAISES THE LEVEL, A SHAPE MOVES THE"
                   " OPTIMUM", BLACK, 2)
    ax1 = Axes(c, (110, 110, 520, 430), (0, dmax), (0, max(mt) * 1.15),
               xlabel="DELAY D (STEPS)", ylabel="COST CONTRIBUTION",
               xticks=list(range(0, dmax + 1)), yticks=[0, 5, 10, 15, 20, 25],
               xfmt="{:.0f}", yfmt="{:.0f}", scale=1,
               title="MEAN CHANNEL: ||XBAR_D||^2 IS FLAT IN D")
    ax1.plot(ds, mt, ORANGE, width=2)
    ax1.points(ds, mt, ORANGE, r=3)
    ax1.plot(ds, trP, BLUE, width=2)
    ax1.points(ds, trP, BLUE, r=3)
    ax1.frame()
    inv_txt = "EXACTLY INVARIANT IN D" if ch["mean_delay_invariance_spread"] == 0 \
        else f"SPREAD {ch['mean_delay_invariance_spread']:.1e} OVER D"
    c.text(120, 470, f"ORANGE = MEAN TERM ||XBAR||^2 = {mt[0]:.6f} ({inv_txt})",
           ORANGE, 1)
    c.text(120, 488, f"BLUE = CENTERED COVARIANCE Tr(P_D); RATIO AT D={ch['d_ref']}"
                     f" = {ch['mean_over_trP_pct']/100:.3f}", BLUE, 1)
    c.text(120, 506, "THE DC GAIN OF A STABLE LOOP IS DELAY-INVARIANT: A CONSTANT"
                     " CANNOT MOVE THE ARGMIN", BLACK, 1)

    ax2 = Axes(c, (650, 110, 1020, 430), (sd[0], sd[-1]), (1.0, 1.12),
               xlabel="DELAY D (STEPS)", ylabel="COST RATIO SPARSE / GAUSS",
               xticks=[0, 2, 4, 6, 8, 10], yticks=[1.00, 1.03, 1.06, 1.09, 1.12],
               xfmt="{:.0f}", yfmt="{:.2f}", scale=1,
               title="SHAPE CHANNEL: THE RATIO RISES WITH D")
    dashed_h(c, ax2.Y(1.0), ax2.x0, ax2.x1, GREY)
    ax2.plot(sd, ratio, GREEN, width=2)
    ax2.points(sd, ratio, GREEN, r=3)
    ax2.frame()
    c.text(660, 470, f"SPARSE/GAUSS = {ratio[0]:.4f} AT D=0 -> {ratio[-1]:.4f} AT"
                     f" D={sd[-1]}  (MATCHED IN 2ND MOMENT)", GREEN, 1)
    c.text(660, 488, "SAME 2ND MOMENT, DIFFERENT HIGHER MOMENTS: THE COST"
                     " SEPARATES AND GROWS WITH STALENESS", BLACK, 1)
    c.text(120, 560, "LEFT PANEL: LINEAR ARM (U UNBOUNDED) AT DELAY D="
                     + str(ch["d_ref"]) + ".  RIGHT PANEL: THE SATURATING PLANT.", BLACK, 1)
    mc = ch["mc"]
    sig = " / ".join(f"{(m['cost']-ch['prediction'])/m['se']:+.2f}" for m in mc)
    costs = " / ".join(f"{m['cost']:.5f}" for m in mc)
    c.text(120, 578, f"PREDICTION Tr(P)+||XBAR||^2 = {ch['prediction']:.10f} vs MC"
                     f" {costs} ({sig} SIGMA)", BLACK, 1)
    return write(c, path)


def main():
    import os
    os.makedirs("figures_draft", exist_ok=True)
    res = load()
    p1 = fig_frontier(res, "double-int R=100 (well damped)", [0, 1, 2, 4, 6, 8],
                      "figures_draft/frontier_R100.png")
    p2 = fig_exponent(res, "figures_draft/exponent_by_config.png")
    p3 = fig_regime(res, "figures_draft/regime_map.png")
    p4 = fig_channels(res, "figures_draft/channels.png")
    assert p1 and p2 and p3 and p4, "a figure failed to render"
    # determinism: render again into a scratch path and require the same digest
    p1b = fig_frontier(res, "double-int R=100 (well damped)", [0, 1, 2, 4, 6, 8],
                       "figures_draft/_rerun_frontier.png")
    p2b = fig_exponent(res, "figures_draft/_rerun_exponent.png")
    p3b = fig_regime(res, "figures_draft/_rerun_regime.png")
    p4b = fig_channels(res, "figures_draft/_rerun_channels.png")
    assert p1 == p1b, "frontier figure is NOT deterministic"
    assert p2 == p2b, "exponent figure is NOT deterministic"
    assert p3 == p3b, "regime figure is NOT deterministic"
    assert p4 == p4b, "channels figure is NOT deterministic"
    for p in ("_rerun_frontier", "_rerun_exponent", "_rerun_regime", "_rerun_channels"):
        os.remove(f"figures_draft/{p}.png")
    print("DETERMINISM: all four figures byte-identical across two renders")


if __name__ == "__main__":
    main()
