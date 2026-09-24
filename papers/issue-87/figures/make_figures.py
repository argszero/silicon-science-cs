#!/usr/bin/env python3
"""#87 -- the manuscript's figures, drawn from `results_digest.json` alone.

Every plotted value is read out of the digest (which reads it out of a committed result JSON), so a figure
and a sentence in the manuscript cannot disagree: the two have one owner.  Nothing is recomputed here and no
number is typed in: the axis of a figure IS a digest quantity, named in the caption of the manuscript.

  fig1_advantage_map.png  the study's core outcome: the paired excess-risk difference (quantum - metric-matched
                          rival) over bandwidth, by convention and qubit count, averaged over the 5 disjoint
                          streams -- the mid-band block where the kernel loses, and the two flanks where it leads.
  fig2_power_arm.png      the registered power arm: the rival's own handicap effect dR(t) per axis (does
                          withholding geometry actually make the rival worse?), and the mid-band loss that
                          survives the strongest valid handicap.
  fig3_metric_structure.png  why the map has the shape it has: the map's metric is scale-uniform on
                          vertex-transitive graphs and not on a path (the statistic that locates the region),
                          on a log axis, at both qubit counts.

Run:  /usr/bin/python3 make_figures.py          (matplotlib 3.9.4 / numpy 2.0.2, on /usr/bin/python3)
Writes the three PNGs beside this file.
"""
import io
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DIGEST = os.path.join(os.path.dirname(HERE), "artefacts", "results_digest.json")


def main():
    with io.open(DIGEST, encoding="utf-8") as fh:
        q = json.load(fh)["quantities"]

    cells = q["panel.cells"]["value"]
    gammas = q["design.gammas"]["value"]
    convs = q["design.conventions"]["value"]
    structure = set(json.loads(json.dumps(
        [k for k in cells if k.split("|")[1] in ("0.5", "1", "2")])))

    # ------------------------------------------------------------------ fig 1
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4), sharex=True)
    xs = list(range(len(gammas)))
    for i, qubit in enumerate(("6", "8")):
        for j, conv in enumerate(convs):
            ax = axes[i][j]
            for a, style in ((1, dict(marker="o", ls="-")), (-1, dict(marker="s", ls="--"))):
                ys = [cells["%s|%s|a=%+d" % (conv, ("%g" % g), a)]["mean%s" % qubit] for g in gammas]
                es = [cells["%s|%s|a=%+d" % (conv, ("%g" % g), a)]["sd%s" % qubit] for g in gammas]
                ax.errorbar(xs, ys, yerr=es, capsize=3,
                            label="target alignment $\\alpha=%+d$" % a, **style)
            ax.axhline(0.0, color="k", lw=0.8)
            for g_i, g in enumerate(gammas):
                if ("%g" % g) in ("0.5", "1", "2"):
                    ax.axvspan(g_i - 0.35, g_i + 0.35, color="0.85", zorder=0)
            ax.set_title("%s convention, q = %s" % (conv, qubit), fontsize=10)
            ax.set_xticks(xs)
            ax.set_xticklabels([("%g" % g) for g in gammas])
            ax.set_ylabel("excess risk: quantum $-$ matched")
            ax.grid(alpha=0.25, lw=0.4)
            if i == 0 and j == 0:
                ax.legend(fontsize=8, loc="upper left")
    axes[1][0].set_xlabel("bandwidth $\\gamma$")
    axes[1][1].set_xlabel("bandwidth $\\gamma$")
    fig.suptitle("Fig. 1  The advantage map: paired difference in excess risk (quantum $-$ metric-matched\n"
                 "rival), mean $\\pm$ sd over 5 disjoint stream draws per cell (shaded: the mid-band block)",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(HERE, "fig1_advantage_map.png"), dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------------ fig 2
    ladder = q["power.ladder_by_axis"]["value"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes_order = sorted(ladder)
    names = [a.split("_", 1)[1].replace("_", " ") for a in axes_order]
    cyc = [ladder[a]["cycle_median"] for a in axes_order]
    pat = [ladder[a]["path_median"] for a in axes_order]
    xpos = range(len(axes_order))
    ax1.bar([p - 0.2 for p in xpos], cyc, width=0.38, label="cycle graph")
    ax1.bar([p + 0.2 for p in xpos], pat, width=0.38, label="path graph")
    ax1.axhline(0.0, color="k", lw=0.8)
    ax1.set_xticks(list(xpos))
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax1.set_ylabel("$dR(t{=}1)$: rival's excess risk change")
    ax1.set_title("(a) does the handicap handicap? (median over cells)", fontsize=10)
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.25, lw=0.4, axis="y")

    lvl = q["fallback.per_cell_delta_by_handicap_level"]["value"]
    levels = ["0.0", "0.3333333333333333", "0.6666666666666666", "1.0"]
    worst = sorted(lvl, key=lambda k: -lvl[k]["1.0"])[:4]
    for k in worst:
        ax2.plot(range(4), [lvl[k][t] for t in levels], marker="o",
                 label=k.split("|")[0] + " $\\gamma$=" + k.split("|")[1] + " " + k.split("|")[2])
    ax2.axhline(0.0, color="k", lw=0.8)
    ax2.set_xticks(range(4))
    ax2.set_xticklabels(["0", "1/3", "2/3", "1"])
    ax2.set_xlabel("handicap level $t$ (axis C: trace-matched random metric)")
    ax2.set_ylabel("quantum $-$ rival, excess risk")
    ax2.set_title("(b) the loss survives the strongest valid handicap", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.25, lw=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig2_power_arm.png"), dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------------ fig 3
    d6 = q["structure.diag_uniformity_rel_q6"]["value"]
    d8 = q["structure.diag_uniformity_rel_q8"]["value"]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    graphs = ["complete", "cycle", "path"]
    xpos = range(len(graphs))
    ax.bar([p - 0.2 for p in xpos], [max(d6[g], 1e-17) for g in graphs], width=0.38, label="q = 6")
    ax.bar([p + 0.2 for p in xpos], [max(d8[g], 1e-17) for g in graphs], width=0.38, label="q = 8")
    for p, g in zip(xpos, graphs):
        ax.annotate("%.1e" % d6[g], (p - 0.2, max(d6[g], 1e-17)), ha="center", va="bottom", fontsize=7)
        ax.annotate("%.1e" % d8[g], (p + 0.2, max(d8[g], 1e-17)), ha="center", va="bottom", fontsize=7)
    ax.set_yscale("log")
    ax.set_ylim(1e-17, 10)
    ax.set_xticks(list(xpos))
    ax.set_xticklabels(["complete", "cycle", "path"])
    ax.set_ylabel("max relative deviation of $\\mathrm{diag}(W)$")
    ax.set_title("Fig. 3  The map's metric is scale-uniform on vertex-transitive\n"
                 "graphs and not on a path: the statistic that locates the region", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, lw=0.4, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig3_metric_structure.png"), dpi=150)
    plt.close(fig)

    print("wrote fig1_advantage_map.png, fig2_power_arm.png, fig3_metric_structure.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
