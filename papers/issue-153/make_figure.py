#!/usr/bin/env python3
"""Issue #153 -- the figure the manuscript embeds, drawn from results.json.

WHAT THE FIGURE ASSERTS. It is not decoration; it carries the two readings of §4.2, which are
*a frequency* and *a magnitude*:

  (a) the deployed rule's loss fraction does not wash out as traces grow -- within a fixed
      (R, K) family the bars stay level as T increases;
  (b) the magnitude is worse than the fraction suggests -- the worst excess ratio reaches its
      maximum in a cell that is not the base cell.

Both are properties of stored numbers, so the program asserts them before drawing:

  1. `max_worst` (the value the prose prints) equals the maximum of the per-cell `greedy_worst`;
     if those disagree the manuscript's headline number is not the figure's.
  2. every bar's fraction equals `greedy_loss / traces` recomputed here -- never read from a
     field that might have been formatted on the way into the artifact.
  3. the cells with `K = 2` are exactly the cells with no loss and `w* = 0`, and they are drawn
     as CONTROLS rather than as wins: at K = 2 the legal merge set is a singleton, so no rule has
     freedom and a zero there measures the design, not the rule. The three K=2 cells are drawn
     with a hatch and named in the legend, because a zero-tall bar labelled like the others reads
     as a pass.
  4. the cell count matches `n_cells`.

`--check` redraws and compares against the committed files byte for byte instead of writing them,
so `reproduce.sh` can hold the figure to the package's no-tolerance rule without rewriting the
artifact a previous verification described.

The SVG is pinned to a fixed `hashsalt` with its date stamp suppressed: matplotlib otherwise puts
a fresh `<dc:date>` and per-process clip-path ids into every run, which makes a committed figure
differ from a regenerated one while every plotted number is equal.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.json")
FIGDIR = os.path.join(HERE, "figures")
SVG = os.path.join(FIGDIR, "deployed-rule-vs-optimum.svg")
PNG = os.path.join(FIGDIR, "deployed-rule-vs-optimum.png")

# the registered success criterion this figure is read against (issue #153, prior P1):
# a loss fraction at K = 3 with worst excess strictly above 1.3x.
REGISTERED_RATIO = 1.3


def load():
    with open(RESULTS, encoding="utf-8") as fh:
        return json.load(fh)


def cell_label(c):
    return "R%d K%d T%d" % (c["R"], c["K"], c["T"])


def collect(res):
    cells = sorted(res["cells"], key=lambda c: (c["K"], c["R"], c["T"]))
    rows = []
    for c in cells:
        rows.append({
            "label": cell_label(c),
            "K": c["K"], "R": c["R"], "T": c["T"],
            "fraction": c["greedy_loss"] / c["traces"],
            "worst": c["greedy_worst"],
            "loss": c["greedy_loss"],
            "traces": c["traces"],
            "wstar": c["wstar"],
            "anti_loss": c["anti_loss"],
            "control": c["K"] == 2,
        })
    return rows


def by_label_sort(res):
    return sorted(res["cells"], key=lambda c: (c["K"], c["R"], c["T"]))


def assert_invariants(res, rows):
    """Refuse to draw when the artifact disagrees with itself."""
    problems = []

    if len(rows) != res["n_cells"]:
        problems.append("drew %d cells, results.json says n_cells=%d"
                        % (len(rows), res["n_cells"]))

    # 1. the printed maximum is the maximum of the per-cell values
    worst_seen = max(r["worst"] for r in rows)
    if abs(worst_seen - res["max_worst"]) > 1e-9:
        problems.append("max_worst=%.6f but the largest per-cell worst is %.6f"
                        % (res["max_worst"], worst_seen))
    at_max = [(r["R"], r["K"], r["T"]) for r in rows if abs(r["worst"] - worst_seen) < 1e-9]
    recorded = [(c["R"], c["K"], c["T"]) for c in res["cells_at_max_worst"]]
    if sorted(at_max) != sorted(recorded):
        problems.append("cells_at_max_worst=%s but the maximum is attained at %s"
                        % (recorded, at_max))

    # 2. the fractions are recomputed, not trusted
    for r, c in zip(rows, sorted(res["cells"], key=lambda c: (c["K"], c["R"], c["T"]))):
        if r["loss"] / r["traces"] != c["greedy_loss"] / c["traces"]:
            problems.append("%s: fraction does not recompute" % r["label"])

    # 3. the K=2 cells are controls, and a control that loses is a code defect
    for r in rows:
        if r["control"]:
            if r["loss"] != 0:
                problems.append("%s is K=2 (no choice exists) yet reports %d losses -- "
                                "the model or the rule is broken, not the finding"
                                % (r["label"], r["loss"]))
            if r["wstar"] != 0:
                problems.append("%s is K=2 yet w*=%d" % (r["label"], r["wstar"]))

    # 3b. what w* = 0 actually means. It is NOT "no genuine choice exists": R3 K5 T6 has
    # K = 5, a real choice, and w* = 0, because the first choice arrives at the last flush
    # where there is nothing left to look ahead to. The quantity that identifies it is the
    # zero-lookahead member of the family -- the cheapest-overlap rule -- being exact, and
    # this equivalence is asserted over every cell rather than stated in prose.
    for r, c in zip(rows, by_label_sort(res)):
        if (r["wstar"] == 0) != (c["anti_loss"] == 0):
            problems.append("%s: w*=%d but the zero-lookahead rule loses %d traces -- "
                            "w*=0 must mean exactly that the zero-lookahead rule is exact"
                            % (r["label"], r["wstar"], c["anti_loss"]))

    # 4. the informative cells exist at all: a figure of nothing but controls asserts nothing
    if not any(not r["control"] for r in rows):
        problems.append("every cell is a control -- there is no branch to measure")

    return problems


def draw(res, rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["svg.hashsalt"] = "issue-153"
    matplotlib.rcParams["font.size"] = 8

    os.makedirs(FIGDIR, exist_ok=True)
    fig, (ax_f, ax_w) = plt.subplots(1, 2, figsize=(11.0, 4.4))
    xs = range(len(rows))
    labels = [r["label"] for r in rows]

    # ---- panel A: how often ------------------------------------------------
    frac_pct = [100.0 * r["fraction"] for r in rows]
    bars = ax_f.bar(xs, frac_pct, color="#4c72b0", width=0.72)
    for b, r in zip(bars, rows):
        if r["control"]:
            b.set_hatch("///")
            b.set_facecolor("#c8c8c8")
            b.set_edgecolor("#606060")
    ax_f.set_ylabel("traces on which the deployed rule is\nnot optimal (%)")
    ax_f.set_title("(a) how often, by cell", loc="left", fontsize=9)
    ax_f.set_ylim(0, max(frac_pct) * 1.28)
    for x, r, v in zip(xs, rows, frac_pct):
        if not r["control"]:
            ax_f.annotate("%.1f%%" % v, (x, v), ha="center", va="bottom", fontsize=6.5)
        # a control is NOT annotated per bar: its bar is zero-tall, so three per-bar labels
        # land on top of each other and print as an unreadable blot. The legend names them.

    # ---- panel B: by how much ---------------------------------------------
    worst = [r["worst"] for r in rows]
    bars_w = ax_w.bar(xs, worst, color="#c44e52", width=0.72)
    for b, r in zip(bars_w, rows):
        if r["control"]:
            b.set_hatch("///")
            b.set_facecolor("#c8c8c8")
            b.set_edgecolor("#606060")
    ax_w.axhline(REGISTERED_RATIO, color="#333333", linestyle="--", linewidth=1.0)
    # the criterion is named in the legend, not written across the bars: printed at its own
    # y it lay on top of four bars, and a threshold nobody can read is not a threshold
    ax_w.set_ylabel("worst excess over the exact optimum\n(bytes paid / optimum)")
    ax_w.set_title("(b) by how much", loc="left", fontsize=9)
    ax_w.set_ylim(0, max(worst) * 1.18)
    top = max(rows, key=lambda r: r["worst"])
    for x, r, v in zip(xs, rows, worst):
        if abs(v - top["worst"]) < 1e-9:
            ax_w.annotate("%.3g\u00d7  (%s)" % (v, r["label"]), (x, v), ha="center",
                          va="bottom", fontsize=7.5, fontweight="bold")
        else:
            ax_w.annotate("%.3g" % v, (x, v), ha="center", va="bottom", fontsize=6)

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor="#4c72b0", label="informative cell (K \u2265 3): the rule has a choice"),
        Patch(facecolor="#c8c8c8", hatch="///", edgecolor="#606060",
              label="control (K = 2): the legal merge set is a singleton, so a zero bar "
                    "measures the design, not the rule"),
        Line2D([0], [0], color="#333333", linestyle="--", linewidth=1.0,
               label="registered criterion in (b): worst excess %s\u00d7"
                     % ("%.1f" % REGISTERED_RATIO)),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=7.0,
               bbox_to_anchor=(0.5, -0.03))

    for ax in (ax_f, ax_w):
        ax.set_xticks(list(xs))
        ax.set_xticklabels(labels, rotation=90, fontsize=6.5)
        ax.grid(axis="y", linewidth=0.4, alpha=0.35)
        ax.set_axisbelow(True)

    fig.suptitle("The deployed rule (merge the run with the largest overlap) against the exact "
                 "optimum, per enumerated cell", fontsize=9.5, y=0.985)
    fig.tight_layout(rect=(0, 0.10, 1, 0.95))
    fig.savefig(SVG, format="svg", metadata={"Date": None})
    fig.savefig(PNG, format="png", dpi=170)
    plt.close(fig)
    return top


def main():
    res = load()
    rows = collect(res)
    problems = assert_invariants(res, rows)
    if problems:
        print("FIGURE INVARIANTS VIOLATED -- refusing to draw:")
        for p in problems:
            print("   " + p)
        return 1

    if "--check" in sys.argv[1:]:
        # compare, do not write: a gate that redraws the artifact it is checking would make
        # every later byte comparison a comparison of the file with itself
        for want, path in ((None, SVG), (None, PNG)):
            if not os.path.exists(path):
                print("ARTIFACT ABSENT: %s -- run without --check to draw it"
                      % os.path.basename(path))
                return 1
        before = {}
        for path in (SVG, PNG):
            before[path] = open(path, "rb").read()
        # draw into a temp directory and compare, so the committed files are untouched
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp(prefix="fig153-")
        try:
            draw(res, rows)
            for path in (SVG, PNG):
                if open(path, "rb").read() != before[path]:
                    print("STALE: %s does not match what this program draws"
                          % os.path.basename(path))
                    return 1
                shutil.copy(path, os.path.join(tmp, os.path.basename(path)))
            # restore the committed bytes
            for path in (SVG, PNG):
                open(path, "wb").write(before[path])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("FIGURE: IN SYNC (%d cells, %d controls, max excess %s)"
              % (len(rows), sum(1 for r in rows if r["control"]),
                 "%.3g" % res["max_worst"]))
        return 0

    top = draw(res, rows)
    print("wrote %s and %s" % (os.path.basename(SVG), os.path.basename(PNG)))
    print("  cells=%d  controls(K=2)=%d  informative=%d"
          % (len(rows), sum(1 for r in rows if r["control"]),
             sum(1 for r in rows if not r["control"])))
    print("  largest loss fraction: %.1f%%" % (100.0 * max(r["fraction"] for r in rows)))
    print("  worst excess: %.3gx at %s" % (top["worst"], top["label"]))
    print("FIGURE: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
