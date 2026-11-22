#!/usr/bin/env python3
"""issue-165 -- figures. A figure is an ASSERTION IN A SECOND LANGUAGE, so each one here carries a
numeric invariant that is checked in this program before the pixels are drawn, and printed so that a
reader can compare the printed claim with the drawn one:

  fig1_decay.png        claim: mean d < 0 with the whole 95% interval below zero, in BOTH fields.
                        invariant: for each field, ci95_mean_d[1] < 0; points drawn == n_seeds.
  fig2_price_bound.png  claim: w* with its whole 95% interval below the floor of 1.0, in BOTH fields.
                        invariant: for each field, w_star.ci95[1] < floor; the floor line is drawn at
                        the value the artefact holds, not at a literal typed here.

A figure that cannot fail is not a check: if a field's interval crossed its line, this program exits
non-zero and writes no image, rather than drawing a picture whose prose would then be false.

Usage:  python3 make_figures.py           -> writes figures/*.png
        python3 make_figures.py --check   -> redraw into a temp dir and compare bytes with the committed PNGs
"""
import json
import os
import shutil
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="mplcfg-"))
try:
    import matplotlib                             # noqa: E402
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt               # noqa: E402
except ImportError as exc:                        # declared NOT RUN, never a silent pass
    print("make_figures: NOT RUN -- %s\n"
          "  figures are the only artefact that needs matplotlib; every number in the paper is "
          "reproduced without it" % exc, file=sys.stderr)
    sys.exit(3)

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.json")
FIGDIR = os.path.join(HERE, "figures")
FIELDS = [("cs", "Computer Science"), ("social_sciences", "Social Sciences")]
# Pinned so that a re-render is byte-identical on any machine that has this matplotlib.
for _k, _v in [("svg.hashsalt", "issue-165"), ("font.size", 10), ("figure.dpi", 100),
               ("savefig.dpi", 100), ("axes.grid", True), ("grid.alpha", 0.25)]:
    matplotlib.rcParams[_k] = _v


def save(fig, path):
    fig.savefig(path, format="png", bbox_inches="tight",
                metadata={"Software": None, "Creation Time": None})
    plt.close(fig)


def fig_decay(results, outdir):
    """Per-seed decay d = excess(hop2) - excess(hop1), both fields, with the field means and intervals."""
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    printed, ticks = [], []
    for i, (key, label) in enumerate(FIELDS):
        a = results["arms"][key]
        ds = [row["d"] for row in a["per_seed"] if row.get("d") is not None]
        assert len(ds) == a["decay"]["n_seeds_with_d"], (
            "seed count mismatch: %d points drawn but the artefact holds n_seeds_with_d=%d"
            % (len(ds), a["decay"]["n_seeds_with_d"]))
        ys = [i + 0.16 * ((j % 5) - 2) / 2.0 for j in range(len(ds))]   # deterministic jitter, no rng
        ax.scatter(ds, ys, s=14, alpha=0.75, label=None)
        mean, (lo, hi) = a["decay"]["mean_d"], a["decay"]["ci95_mean_d"]
        ax.plot([lo, hi], [i, i], color="black", lw=2, solid_capstyle="butt", zorder=5)
        ax.plot([mean], [i], marker="D", color="black", ms=6, zorder=6)
        neg = sum(1 for x in ds if x < 0)
        assert neg == a["decay"]["seeds_d_lt_0"], (
            "counted %d negative seeds but the artefact holds %d" % (neg, a["decay"]["seeds_d_lt_0"]))
        ticks.append("%s\n%d of %d seeds negative" % (label, neg, len(ds)))
        printed.append("%s: mean %.4f CI [%.4f, %.4f], %d/%d seeds negative"
                       % (label, mean, lo, hi, neg, len(ds)))
        assert hi < 0, ("the figure claims the decay interval lies below zero, but %s has upper "
                        "bound %.4f -- refusing to draw a picture that contradicts the paper" % (label, hi))
    ax.axvline(0, color="crimson", lw=1.2, ls="--")
    ax.set_yticks(range(len(FIELDS)))
    ax.set_yticklabels(ticks)
    ax.set_xlabel("per-seed decay  d = excess(hop 2) − excess(hop 1)")
    # The title may not say "every seed": the per-row counts above are the exact statement, and a
    # reader is entitled to read them off the axis instead of trusting a summary word.
    ax.set_title("The per-seed excess falls with depth; dashed line marks no decay")
    ax.set_ylim(-0.6, len(FIELDS) - 0.4)
    save(fig, os.path.join(outdir, "fig1_decay.png"))
    return printed


def fig_price_bound(results, outdir):
    """w* (a depth batch's price, in breadth pages) with its interval, against the floor of 1.0."""
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    printed = []
    floors = {results["arms"][k]["w_star"]["floor"] for k, _ in FIELDS}
    assert len(floors) == 1, "the fields disagree on the floor: %r" % (floors,)
    floor = floors.pop()
    ax.axvspan(floor, floor + 1.6, color="tab:green", alpha=0.09)
    ax.axvline(floor, color="black", lw=1.2)
    ax.text(floor + 0.03, -0.62, "admissible prices: w ≥ %g" % floor, fontsize=8, va="bottom")
    for i, (key, label) in enumerate(FIELDS):
        w = results["arms"][key]["w_star"]
        point, (lo, hi) = w["point"], w["ci95"]
        ax.plot([lo, hi], [i, i], color="tab:blue", lw=2, solid_capstyle="butt")
        ax.plot([point], [i], marker="o", color="tab:blue", ms=7)
        printed.append("%s: w* = %.3f CI [%.3f, %.3f]%s" % (label, point, lo, hi,
                       "" if lo <= point <= hi else "  <-- POINT OUTSIDE ITS OWN INTERVAL"))
        assert lo <= point <= hi, "the point estimate %r is outside its own interval %r" % (point, (lo, hi))
        assert hi < floor, ("the figure claims depth cannot win, but %s has w* interval reaching "
                            "%.3f >= floor %g" % (label, hi, floor))
    ax.set_yticks(range(len(FIELDS)))
    ax.set_yticklabels([label for _, label in FIELDS])
    ax.set_xlim(0, 1.35)
    ax.set_ylim(-0.7, len(FIELDS) - 0.35)
    ax.set_xlabel("w*  =  largest depth-batch price (in breadth pages) at which depth wins")
    ax.set_title("Depth cannot win at this API's price: every interval ends left of the floor")
    save(fig, os.path.join(outdir, "fig2_price_bound.png"))
    return printed


def main():
    results = json.load(open(RESULTS))
    check = "--check" in sys.argv
    if check:
        assert os.path.isdir(FIGDIR), "no committed figures/ to compare against"
        outdir = tempfile.mkdtemp(prefix="figs-")
    else:
        outdir = FIGDIR
        os.makedirs(FIGDIR, exist_ok=True)
    for fn in (fig_decay, fig_price_bound):
        for line in fn(results, outdir):
            print("  [fig] %s" % line)
    names = ["fig1_decay.png", "fig2_price_bound.png"]
    if not check:
        print("make_figures: %d figures written to figures/" % len(names))
        return 0
    bad = 0
    for n in names:
        a = open(os.path.join(FIGDIR, n), "rb").read()
        b = open(os.path.join(outdir, n), "rb").read()
        if a != b:
            print("CHECK FAILED: %s differs from a fresh render (%d vs %d bytes)"
                  % (n, len(a), len(b)), file=sys.stderr)
            bad += 1
    shutil.rmtree(outdir, ignore_errors=True)
    if bad:
        return 1
    print("CHECK OK: %d figures match a fresh render byte for byte" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
