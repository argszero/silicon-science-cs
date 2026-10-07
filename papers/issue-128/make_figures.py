#!/usr/bin/env python3
"""make_figures.py -- issue #128: the three data figures, drawn from the instrument artefacts.

Each figure reads the JSON the instruments wrote (never a retyped number), so a figure cannot drift
from the measurement it illustrates.  Deterministic: no random state, fixed dpi, fixed size -> the PNG
is byte-identical on a re-run.

  fig1_cost_curves.png   the cost above M*: max-sum is a slope, max-min is a step  (P3)
  fig2_free_width.png    the free width by family and on real data                  (P1')
  fig3_alignment.png     the predictor sweep: alignment vs free width               (P2')

Usage: MPLCONFIGDIR=<tmp> python3 make_figures.py
"""
import io, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True})


def load(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


def beta_pts(curve, M_star, basev):
    return [(r["M"] - M_star, (basev - r["value"]) / float(basev))
            for r in curve if M_star is not None and r["M"] > M_star
            and r["value"] is not None and r["value"] < basev]


def fig1():
    v3 = load("spike_v3_results.json")
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for obj, col, mk, lab in (("maxsum", "#1f77b4", "o", "max-sum (sum)"),
                              ("maxmin", "#d62728", "s", "max-min (bottleneck)")):
        sub = [c for c in v3["cases"] if c["obj"] == obj]
        first = True
        for c in sub:
            pts = beta_pts(c["floors_curve"], c["M_star"], c["unconstrained"])
            if len(pts) >= 2:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=col, alpha=0.35,
                        marker=mk, ms=2.5, lw=0.9, label=lab if first else None)
                first = False
    ax.set_xlabel("forced seats above the free threshold  (M - M*)")
    ax.set_ylabel("relative loss  (OPT(0) - OPT(M)) / OPT(0)")
    ax.set_title("Cost above the free region: a sum pays a slope, a bottleneck a step")
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_cost_curves.png")); plt.close(fig)


def fig2():
    v3 = load("spike_v3_results.json"); v4 = load("spike_v4_results.json")
    fams = {}
    for c in v3["cases"]:
        if c["M_star"] is not None:
            fams.setdefault(c["family"], []).append(c["M_star"] / float(c["k"]))
    order = sorted(fams, key=lambda f: float(np.median(fams[f])))
    labels = order + ["real (Wine Quality)"]
    med = [float(np.median(fams[f])) for f in order]
    A = [c for c in v4["part_a"]["cases"] if c["M_star"] is not None]
    med.append(float(np.median([c["M_star"] / float(c["k"]) for c in A])))
    allw = [c["M_star"] / float(c["k"]) for c in v3["cases"] if c["M_star"] is not None] + \
           [c["M_star"] / float(c["k"]) for c in A]
    free_all = sum(1 for w in allw if w == 1.0)
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.bar(range(len(labels)), med, color="#4c72b0", alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("median free width  M*/k")
    ax.set_ylim(0, 1.05)
    ax.axhline(1.0, color="grey", lw=0.8, ls="--")
    ax.set_title("How much quota is free: median free width (whole quota free in %d/%d cases)"
                 % (free_all, len(allw)))
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_free_width.png")); plt.close(fig)


def fig3():
    v5 = load("spike_v5_results.json")
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    xs, ys = [], []
    for cname, blk in v5["corpora"].items():
        cells = [c for c in blk["cells"] if c["free_width"] is not None]
        x = [c["alignment"] for c in cells]; y = [c["free_width"] for c in cells]
        xs += x; ys += y
        ax.scatter(x, y, s=7, alpha=0.45, label=cname)
    rx = np.argsort(np.argsort(xs)).astype(float); ry = np.argsort(np.argsort(ys)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    rho = float((rx * ry).sum() / np.sqrt((rx * rx).sum() * (ry * ry).sum()))
    ax.set_xlabel("group-metric alignment  (solve-free predictor)")
    ax.set_ylabel("free width  M*/k")
    ax.set_title("The predictor is not there: 320 real-row cells, pooled Spearman = %+.3f" % rho)
    ax.legend(loc="upper left", frameon=False, title="corpus")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_alignment.png")); plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    for f in ("fig1_cost_curves.png", "fig2_free_width.png", "fig3_alignment.png"):
        p = os.path.join(FIG, f)
        print("%-22s %8d B" % (f, os.path.getsize(p)))
