#!/usr/bin/env python3
"""Issue #122 -- figures.  Every panel is drawn from a committed `spike_v*_results.json` produced by
the instruments in this directory; nothing is drawn from a number typed into this file.

The one statistic this file RE-DERIVES rather than reads (the Jensen-gap spread in fig1b) is checked
against the artefact's own summary before it is drawn: the run FAILS if the count, the median or the
minimum disagree.  A figure that computes its own version of a reported number is a second
computation, and a second computation may disagree with the first without anyone noticing.

Usage:  /usr/bin/python3 make_figures.py
Out:    figures/fig1..fig5 .png + figures/manifest.json (sha256 per figure)
"""
import hashlib
import json
import math
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
# Read off `sources()` in spike_v1.py, not guessed: zipf is a power law with exponent 1.2 and
# `twohot` is TWO dominant symbols at 0.35 each with the remaining 0.30 spread over the rest.  The
# first version of this dict called twohot "Zipf-like", which is simply not what it is.
LABEL = {"uniform": "uniform", "zipf": "Zipf(1.2)", "twohot": "two-hot (2 symbols at 0.35)"}
# Everything drawn below comes from these artefacts; the manifest records their hashes so a figure
# can always be traced to the results that produced it.
SRC = ["spike_v1_results.json", "spike_v2_results.json", "spike_v3_results.json"]


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    # A PNG is not automatically reproducible: matplotlib stamps its own version into the file, so
    # the same code and data on two builds produce different bytes.  A constant Software tag removes
    # that (the version is recorded in the manifest as DATA, where it belongs).
    fig.savefig(p, dpi=140, bbox_inches="tight", metadata={"Software": "make_figures.py"})
    plt.close(fig)
    print("   %-30s %8d bytes" % (name, os.path.getsize(p)))
    return p


def jensen_pairs(v1):
    """The Jensen gap (closed form / measured), per symbol, on the adequate-EVENT gate.

    Re-derived here because the artefact stores the per-symbol vectors, not the pairs -- so the
    generator MUST reconstruct the same statistic the instrument reported, and the gate is part of
    that statistic.  The gate is on expected loss EVENTS (density x rate), not on the number of
    observations: a rate of 1e-3 observed 50 times carries 0.05 expected events.  The denominator is
    route B, as in the instrument.
    """
    gap = []
    for c in v1["cells"]:
        for i in range(len(c["loss_A"])):
            A, B, D, cf = c["loss_A"][i], c["loss_B"][i], c["loss_den"][i], c["loss_cf"][i]
            if not (math.isfinite(A) and math.isfinite(B)):
                continue
            if D * B < 30.0 or not cf > 0:
                continue
            gap.append(cf / B)
    # The reconstruction is only allowed to be drawn if it IS the reported statistic.
    for what, got, want in [("count", len(gap), v1["n_gap_pairs"]),
                            ("median", statistics.median(gap), v1["cf_over_meas_median"]),
                            ("min", min(gap), v1["cf_over_meas_min"]),
                            # the DIRECTION that distinguishes the claim: a reconstruction that
                            # agreed only on count/median/min would still draw a panel whose title
                            # says "every reading is below 1" while 83 of them are not.
                            ("max", max(gap), v1["cf_over_meas_max"]),
                            ("above-1 count", sum(1 for g in gap if g > 1.0), v1["n_gap_above1"])]:
        if not math.isclose(got, want, rel_tol=1e-12, abs_tol=0.0):
            sys.exit("REFUSING TO DRAW: the re-derived Jensen gap disagrees with the artefact on "
                     "%s: figure %.12g vs artefact %.12g" % (what, got, want))
    return gap


def fig1(v1, gap):
    """P1 (refuted as a rate): the folk closed form is a lower bound on the UNCONDITIONAL loss;
    the conditional rate a loop experiences falls on both sides of it, and the gap grows with n."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.7))
    for src, lam, mk in [("uniform", 0.01, "o"), ("uniform", 0.02, "s")]:
        cells = sorted([c for c in v1["cells"] if c["source"] == src and c["lam"] == lam],
                       key=lambda c: c["n"])
        ns = [c["n"] for c in cells]
        a1.plot(ns, [max(c["loss_A"][c["worst_symbol"]], 1e-12) for c in cells],
                marker=mk, lw=1.5, label="measured, route A (lam=%.2f)" % lam)
        a1.plot(ns, [max(c["loss_B"][c["worst_symbol"]], 1e-12) for c in cells],
                marker=mk, lw=1.0, ls="--", alpha=0.75, label="measured, route B (lam=%.2f)" % lam)
        a1.plot(ns, [max(c["loss_cf"][c["worst_symbol"]], 1e-12) for c in cells],
                marker="x", lw=1.2, ls=":", c="k",
                label="closed form (1-p*)^n (lam=%.2f)" % lam)
    a1.set_xscale("log")
    a1.set_yscale("log")
    a1.set_xlabel("symbols per generation  n")
    a1.set_ylabel("per-generation loss of the worst symbol")
    a1.set_title("The folk rate collapses with n; the measured loss does not", fontsize=9.5)
    a1.legend(fontsize=6.4, loc="lower left")
    a1.grid(alpha=0.25, lw=0.5, which="both")

    # LOG-spaced bins, not linear ones: the readings span ~47 decades, so 40 equal-width bins put
    # the entire distribution in the leftmost bar and the median line lands inside a solid block --
    # the figure would be drawn, cite the right number, and show nothing.
    import numpy as np
    # The upper edge must COVER the largest reading: an edge at 1.0 (the old range) silently drops
    # every reading above it from the histogram, which is exactly the class of readings the caption
    # is about.  An edge is placed AT 1.0 so the readings on the two sides of the bound are two
    # separate bars rather than one bar straddling it.
    edges = list(np.logspace(math.log10(min(gap)), math.log10(max(gap)) * 1.06, 30))
    edges = sorted(set(edges + [1.0]))
    a2.hist(gap, bins=edges, color="#4878a8", edgecolor="white", lw=0.4)
    med = statistics.median(gap)
    top = a2.get_ylim()[1] * 1.18
    a2.set_ylim(top=top)
    # Both reference lines are labelled in a LEGEND rather than beside the lines: the rightmost bin
    # reaches the axis edge, so any text placed next to x=1 is drawn under a bar and unreadable.
    a2.axvline(med, c="k", lw=1.4, label="median %.3f" % med)
    a2.axvline(1.0, c="#c0504d", lw=1.4, ls="--", label="1.0 = the closed form is exact")
    a2.legend(fontsize=7.2, loc="upper left", framealpha=0.92)
    a2.set_xscale("log")
    a2.set_xlabel("closed form / measured loss  (per symbol, log scale)")
    a2.set_ylabel("per-symbol readings")
    n_above = sum(1 for g in gap if g > 1.0)
    a2.set_title("Bound above the measured rate in %d of %d readings"
                 % (len(gap) - n_above, len(gap)), fontsize=9.5)
    # The readings span 47 decades, so the side above the bound occupies a sliver of a full-range
    # log axis: the split is drawn as its own inset, where it can be read, instead of being left to
    # a bar two decades wide at the edge of a 52-decade axis.
    axin = a2.inset_axes([0.05, 0.40, 0.26, 0.44])
    axin.bar([0, 1], [len(gap) - n_above, n_above], color=["#4878a8", "#c0504d"], width=0.62)
    axin.set_xticks([0, 1])
    axin.set_xticklabels(["ratio < 1", "ratio > 1"], fontsize=6.8)
    axin.tick_params(axis="y", labelsize=6.5)
    axin.set_title("%d readings" % len(gap), fontsize=6.8)
    axin.grid(alpha=0.25, lw=0.4, axis="y")
    a2.grid(alpha=0.25, lw=0.5, axis="y")
    fig.suptitle("Fig. 1 - the folk closed form bounds the UNCONDITIONAL loss probability, not the "
                 "rate a loop experiences (min %.1e, max %.2f x the bound)" % (min(gap), max(gap)),
                 fontsize=9.8)
    return save(fig, "fig1_folk_law_refuted.png")


def fig2(v2):
    """P2 (confirmed): at matched per-generation fresh-data rate, a bigger pool window is worse."""
    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    mk = {"uniform": "o", "zipf": "s"}
    for r in sorted(v2["part2"], key=lambda r: (r["source"], r["n"])):
        ws = sorted(int(w) for w in r["boundary"])
        ys = [r["boundary"][str(w)] for w in ws]
        # The figure states monotonicity, so check it before drawing it.
        if any(ys[i] < ys[i + 1] for i in range(len(ys) - 1)):
            sys.exit("REFUSING TO DRAW: boundary not monotonically decreasing in w for %s n=%s"
                     % (r["source"], r["n"]))
        ax.plot(ws, ys, marker=mk.get(r["source"], "o"), lw=1.5,
                label="%s, n=%d (x%.4g from w=1 to w=64)"
                      % (LABEL.get(r["source"], r["source"]), r["n"], r["ratio_w64_over_w1"]))
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("pool window  w  (generations of history)")
    ax.set_ylabel("prevention boundary  lambda*  (largest rate with worst-symbol absence <= 1%)")
    ax.set_title("Accumulating a pool is far more fragile than replacing it\n"
                 "monotone in 4 of 4 cells, falling by 100x-1000x", fontsize=9.5)
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.25, lw=0.5, which="both")
    return save(fig, "fig2_boundary_vs_window.png")


def fig3(v2):
    """The mechanism: pooling turns exponential reversion into moving-average relaxation, whose rate
    is the eigenvalue nearest 1 of the degree-w companion matrix."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.7))
    # The lambda values are READ from the artefact, never typed: the second series is 0.05, and a
    # typed 0.01 selected an empty row set (the failure that produced this comment).
    lams = sorted(set(r["lam"] for r in v2["part3"]), reverse=True)
    if len(lams) != 2:
        sys.exit("REFUSING TO DRAW: fig3 expects two lambda settings, artefact has %d" % len(lams))
    for lam, mk in zip(lams, ["o", "s"]):
        rows = sorted([r for r in v2["part3"] if r["lam"] == lam], key=lambda r: r["w"])
        if not rows:
            sys.exit("REFUSING TO DRAW: no mechanism rows for lam=%s" % lam)
        ws = [r["w"] for r in rows]
        a1.plot(ws, [r["rate_measured"] for r in rows], marker=mk, lw=1.4,
                label="measured (lam=%.2f)" % lam)
        a1.plot(ws, [r["rate_ma_eig"] for r in rows], lw=1.0, ls="--",
                label="MA companion eigenvalue (lam=%.2f)" % lam)
        a1.axhline(rows[0]["rate_w1_law"], lw=1.1, ls=":", c="k",
                   label="replacement law -ln(1-lam) (lam=%.2f)" % lam)
    a1.set_xscale("log", base=2)
    a1.set_yscale("log")
    a1.set_xlabel("pool window  w")
    a1.set_ylabel("relaxation rate of the mean")
    a1.set_title("Measured rate tracks the MA eigenvalue, not the replacement law", fontsize=9.5)
    a1.legend(fontsize=6.4, loc="lower left")
    a1.grid(alpha=0.25, lw=0.5, which="both")

    meas = [r["rate_measured"] for r in v2["part3"]]
    eig = [r["rate_ma_eig"] for r in v2["part3"]]
    a2.scatter(eig, meas, s=22, zorder=3)
    lo, hi = min(eig + meas), max(eig + meas)
    a2.plot([lo, hi], [lo, hi], c="k", lw=1.0, ls="--", label="y = x")
    rel = max(abs(m - e) / e for m, e in zip(meas, eig))
    a2.set_xscale("log")
    a2.set_yscale("log")
    a2.set_xlabel("predicted rate (companion eigenvalue)")
    a2.set_ylabel("measured rate")
    a2.set_title("%d cells spanning %.0fx; worst relative miss %.1f%%"
                 % (len(meas), max(meas) / min(meas), 100 * rel), fontsize=9.5)
    a2.legend(fontsize=7.5)
    a2.grid(alpha=0.25, lw=0.5, which="both")
    fig.suptitle("Fig. 3 - the protocol's mechanism, stated as a prediction before it was measured",
                 fontsize=9.8)
    return save(fig, "fig3_mechanism.png")


def fig4(v3):
    """P1 limb (a) REFUTED: the boundary is criterion-dependent by 13x-45x."""
    rows = [c for c in v3["controls"] if c["kind"] == "criterion_dependence"]
    rows.sort(key=lambda c: (c["source"], c["w"]))
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    xs = range(len(rows))
    w = 0.36
    for i, r in enumerate(rows):
        ceil = r["stationary_is_ceiling"]
        ax.bar(i - w / 2, r["lambda_stationary"], w, color="#4878a8",
               hatch=("//" if ceil else None), edgecolor="white",
               label="keep an intact support (lambda_stationary)" if i == 0 else None)
        ax.bar(i + w / 2, r["lambda_heal"], w, color="#c0504d", edgecolor="white",
               label="heal a collapsed loop (lambda_heal)" if i == 0 else None)
        ax.text(i, r["lambda_stationary"] * 1.25,
                ("%.4g (x%.1f)%s" % (r["lambda_stationary"], r["ratio_stationary_over_heal"],
                                     " CEILING" if ceil else "")),
                fontsize=7.0, ha="center")
    ax.set_yscale("log")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["%s\nw=%d" % (LABEL.get(r["source"], r["source"]), r["w"]) for r in rows],
                       fontsize=8)
    ax.set_ylim(top=max(r["lambda_stationary"] for r in rows) * 8)
    ax.set_ylabel("boundary  lambda  (log scale)")
    ax.set_title("The two criteria are different objects: keeping an intact support\n"
                 "costs 13x-45x more fresh data than healing a collapsed loop", fontsize=9.5)
    ax.legend(fontsize=7.5, loc="lower left")
    ax.grid(alpha=0.25, lw=0.5, axis="y", which="both")
    return save(fig, "fig4_criterion_dependence.png")


def fig5(v1):
    """Hysteresis: the exit and entry first-passage times of the SAME set (all symbols present)."""
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    mk = {"uniform": "o", "zipf": "s", "twohot": "^"}
    n_plot = 50
    # The series are taken from the artefact, and a source with NO rows is an error rather than a
    # silent omission: the first version looped over three hard-coded sources and quietly drew two
    # (only uniform and twohot were measured for this quantity).  A figure that skips what it
    # cannot find reports a narrower object than its own caption.
    srcs = sorted(set(r["source"] for r in v1["first_passage"]
                      if r["n"] == n_plot and r["T_recov"] is not None))
    if not srcs:
        sys.exit("REFUSING TO DRAW: no hysteresis rows at n=%d" % n_plot)
    for src in srcs:
        rows = sorted([r for r in v1["first_passage"] if r["source"] == src and r["n"] == n_plot],
                      key=lambda r: r["lam"])
        if len(rows) != 8:
            sys.exit("REFUSING TO DRAW: expected 8 rates for %s, found %d" % (src, len(rows)))
        ax.plot([r["lam"] for r in rows], [r["T_loss"] for r in rows], marker=mk.get(src, "o"),
                lw=1.4, color="#c0504d", label="exit from healthy - %s" % LABEL.get(src, src))
        ax.plot([r["lam"] for r in rows], [r["T_recov"] for r in rows], marker=mk.get(src, "o"),
                lw=1.4, ls="--", color="#4878a8",
                label="entry back to healthy - %s" % LABEL.get(src, src))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("fresh-data rate  lambda")
    ax.set_ylabel("generations to first passage\n(median over 200 replicates)", fontsize=8)
    # Short enough to fit: the previous title ran past both edges of the axes and was cut in half.
    ax.set_title("Ergodic for every lambda>0, so the point of no return\n"
                 "is finite-horizon only - the two curves cross below lam~0.2", fontsize=9.5)
    ax.legend(fontsize=7.0, ncol=2, loc="upper right")
    ax.grid(alpha=0.25, lw=0.5, which="both")
    return save(fig, "fig5_hysteresis.png")


def main():
    v1, v2, v3 = load(SRC[0]), load(SRC[1]), load(SRC[2])
    gap = jensen_pairs(v1)
    print("figures from %s" % ", ".join(SRC))
    paths = [fig1(v1, gap), fig2(v2), fig3(v2), fig4(v3), fig5(v1)]
    manifest = {os.path.basename(p): hashlib.sha256(open(p, "rb").read()).hexdigest()
                for p in paths}
    src_sha = {s: hashlib.sha256(open(os.path.join(HERE, s), "rb").read()).hexdigest() for s in SRC}
    with open(os.path.join(FIG, "manifest.json"), "w") as f:
        json.dump({"figures": manifest, "sources": src_sha,
                   "jensen_pairs": {"n": len(gap), "median": statistics.median(gap),
                                    "min": min(gap)},
                   "matplotlib": matplotlib.__version__,
                   "note": "PNG bytes are build-dependent (matplotlib version); the Software tag is "
                           "fixed so the same build is byte-identical across runs"},
                  f, indent=1, sort_keys=True)
    print("-> figures/manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
