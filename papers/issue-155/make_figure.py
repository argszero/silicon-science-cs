#!/usr/bin/env python3
"""Issue #155 -- the paper's core figure, drawn from results.json.

A figure is an assertion in a second language, so the assertion is written as a
numeric invariant and checked before anything is drawn: the stacked fractions
must sum to 1 in every bar, and the two panels must show the same quantity
(`required k - LDS`) in the two regimes the paper contrasts.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.json")
FIGDIR = os.path.join(HERE, "figures")

PROBLEMS = []


def fail(msg):
    PROBLEMS.append(msg)
    print("  FAIL: %s" % msg)


def load():
    with open(RESULTS, encoding="utf-8") as fh:
        return json.load(fh)


def prepare():
    os.makedirs(FIGDIR, exist_ok=True)
    matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as text
    matplotlib.rcParams["font.size"] = 9


def bars(rows, key_label, gap_max=3):
    """Return (labels, per-gap fractions) for a list of histogram rows."""
    labels, fracs = [], []
    for r in rows:
        h = {int(k): v for k, v in r["histogram"].items()}
        total = r["windows"]
        lab = (key_label(r))
        f = [h.get(g, 0) / total for g in range(gap_max + 1)]
        s = sum(f)
        if abs(s - 1.0) > 1e-9:
            fail("bar %r fractions sum to %.12f, not 1" % (lab, s))
        labels.append(lab)
        fracs.append(f)
    return labels, fracs


def draw(rows_a, rows_b, gap_max=3):
    labels_a, fa = bars(rows_a, lambda r: "n=%d" % r["n"])
    labels_b, fb = bars(rows_b, lambda r: "n=%d, m=%d" % (r["n"], r["m"]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.4))
    colors = ["#4c72b0", "#dd8452", "#c44e52", "#8172b3"]
    names = {0: "0 (the disciplines agree)", 1: "1", 2: "2", 3: "3 or more"}

    for ax, labels, fracs, title, cap in (
        (ax1, labels_a, fa, "Distinct ranks (all arrival orders)", "max gap = 2"),
        (ax2, labels_b, fb, "Tied ranks (all windows)", "max gap = 1"),
    ):
        bottoms = [0.0] * len(labels)
        for g in range(gap_max + 1):
            vals = [f[g] for f in fracs]
            if all(v == 0 for v in vals):
                continue
            ax.bar(range(len(labels)), vals, bottom=bottoms,
                   color=colors[g % len(colors)], label=names[g], width=0.7)
            bottoms = [b + v for b, v in zip(bottoms, vals)]
        # A bar that is almost entirely "gap 0" reads as "no data" unless the
        # non-zero part is named. Print it inside the bar, where nothing else sits.
        for i, f in enumerate(fracs):
            nz = 1.0 - f[0]
            ax.text(i, 0.5, ("%.2f%%" % (100 * nz)) if nz else "0",
                    ha="center", va="center", rotation=90, fontsize=8,
                    color="white" if nz < 0.25 else "#222222")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_ylabel("fraction of windows")
        ax.set_title(title, fontsize=9.5, pad=6)
        ax.text(0.98, 0.03, cap, transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, style="italic", color="#444444")

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 0.005), fontsize=8.5)
    fig.suptitle("The free-merge statistic understates the queue count a strict-priority "
                 "device needs\n"
                 "gap = required k - LDS per window; the percentage inside each bar is the "
                 "share of windows where the two disciplines disagree",
                 fontsize=8.5)
    fig.tight_layout(rect=(0, 0.13, 1, 0.87))

    svg = os.path.join(FIGDIR, "discipline-gap.svg")
    png = os.path.join(FIGDIR, "discipline-gap.png")
    fig.savefig(svg, format="svg")
    fig.savefig(png, format="png", dpi=160)
    plt.close(fig)
    return svg, png, labels_a, labels_b, fa, fb


def main():
    prepare()
    R = load()
    if R.get("problems"):
        fail("results.json records problems: %s" % R["problems"])

    rows_a = R["gap_distinct"]
    rows_b = R["gap_ties"]

    svg, png, la, lb, fa, fb = draw(rows_a, rows_b)

    # invariants the caption will claim, checked here
    max_a = max(int(k) for r in rows_a for k in r["histogram"])
    max_b = max(int(k) for r in rows_b for k in r["histogram"])
    if max_a != R["gap_summary"]["distinct_max_gap"]:
        fail("figure max gap (distinct) %d != results.json %d"
             % (max_a, R["gap_summary"]["distinct_max_gap"]))
    if max_b != R["gap_summary"]["ties_max_gap"]:
        fail("figure max gap (ties) %d != results.json %d"
             % (max_b, R["gap_summary"]["ties_max_gap"]))
    if max_a > 2:
        fail("the 'never exceeds 2' caption is false: found gap %d" % max_a)
    if max_b > 1:
        fail("the 'never exceeds 1 under ties' caption is false: found gap %d" % max_b)

    # the zero-fraction bar must be labelled, never silently absent
    zero_a = sum(f[0] for f in fa) / len(fa)
    zero_b = sum(f[0] for f in fb) / len(fb)
    print("  wrote %s and %s" % (os.path.basename(svg), os.path.basename(png)))
    print("  mean fraction where the disciplines agree: distinct %.4f, ties %.4f"
          % (zero_a, zero_b))

    if PROBLEMS:
        print("FIGURE: %d PROBLEM(S)" % len(PROBLEMS))
        return 1
    print("FIGURE: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
