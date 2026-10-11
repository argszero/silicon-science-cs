#!/usr/bin/env python3
"""make_figures (#126, R551) -- the manuscript's figures, drawn from the committed result artefacts.

Every figure reads a *_results.json written by an instrument and plots a value that appears in the text
of the manuscript, so a figure cannot disagree with the prose without one of them being regenerated.
Deterministic: no randomness, fixed size and DPI, so re-running is byte-identical (asserted by the
reproduction script against the committed PNG digests).

Needs matplotlib (measured 3.9.4 under /usr/bin/python3 3.9.6).  Set MPLCONFIGDIR to a writable
directory if the default config path is not writable.  Usage: python3 make_figures.py [--outdir DIR]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")

import matplotlib                                    # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def fig_floor(path):
    """Fig. 1 -- the floor, in two panels.

    (a) the two terms against the limb count at one width: the truncation term falls geometrically and
        the total error floors where the accumulation term takes over (sweepA);
    (b) the crossover `K*` against the accumulator width: a wider accumulator needs MORE limbs, never
        fewer (sweepB).
    """
    d = load("spike_v2_results.json")
    a = d["sweepA"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.2))
    ks = sorted(int(k) for k in a["E_total"])
    a1.plot(ks, [a["E_total"][str(k)] for k in ks], "o-", ms=3, lw=1.3, label="total $E$")
    a1.plot(ks, [a["E_trunc"][str(k)] for k in ks], "s--", ms=3, lw=1.1, label="truncation term")
    a1.axhline(a["E_acc_floor"], color="crimson", lw=1.1, ls=":", label="accumulation floor")
    a1.set_yscale("log")
    a1.set_xlabel("limb count $K$")
    a1.set_ylabel("relative error")
    a1.set_title("(a) the floor (p=%d, q=%d)" % (a["p"], a["q"]))
    a1.grid(alpha=0.25, which="both")
    a1.legend(fontsize=7)
    ps = sorted(int(k) for k in d["sweepB"])
    a2.plot(ps, [d["sweepB"][str(p)]["K_star_cross"] for p in ps], "o-", ms=4, lw=1.2)
    a2.set_xlabel("accumulator width $p$ (bits)")
    a2.set_ylabel("$K^*$ (crossover)")
    a2.set_title("(b) a wider register needs more limbs")
    a2.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_width_law(path):
    """Fig. 2 -- the accumulator-width law: p* measured against p* predicted, and the n-flatness."""
    d = load("spike_v1_results.json")
    ps = d["sweep_pstar"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.2))
    xs = [p["p_star_predicted"] for p in ps]
    ys = [p["p_star_measured"] for p in ps]
    a1.plot(xs, ys, "o", ms=4, label="measured")
    lo, hi = min(xs + ys) - 1, max(xs + ys) + 1
    a1.plot([lo, hi], [lo, hi], "--", lw=1, color="grey", label="y = x")
    a1.set_xlabel("predicted $p^*$")
    a1.set_ylabel("measured $p^*$")
    a1.set_title("width law: within 1 bit")
    a1.grid(alpha=0.25)
    a1.legend(fontsize=7)
    sn = d["sweep_n"]
    a2.semilogx(sn["ns"], sn["E_over_kappa1"], "s-", ms=3, lw=1.2)
    a2.set_xlabel("dot-product length $n$")
    a2.set_ylabel("floor $E/\\kappa_1$")
    a2.set_title("floor is flat in $n$ (slope %.3f)" % sn["slope_vs_n"])
    a2.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_order_axis(path):
    """Fig. 3 -- the order axis: the constant's spread over element permutations at fixed kappa1."""
    d = load("spike_real3_results.json")
    pooled = d["order_arm_pooled"]
    names = [k for k in ("fp16", "fp32") if k in pooled]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    x = range(len(names))
    med = [pooled[n]["c_spread_median"] for n in names]
    mx = [pooled[n]["c_spread_max"] for n in names]
    ax.bar(x, med, 0.45, label="median over orders")
    ax.plot(x, mx, "r_", ms=22, label="max over orders")
    for i, n in enumerate(names):
        ax.text(i, max(med[i], mx[i]) * 1.06, "%.1fx / %.1fx" % (med[i], mx[i]),
                ha="center", fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylim(0, max(mx) * 1.20)          # headroom for the min/max annotation
    ax.set_ylabel("within-case spread of $c$")
    ax.set_title("Order alone moves the floor (fixed $\\kappa_1$)")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_lanes(path):
    """Fig. 4 -- register lanes: median constant by configuration, and the per-case three-way split."""
    d = load("spike_mm_results.json")
    fmts = ["bf16", "fp16", "fp32"]
    cfgs = ["L1_rr", "L2_rr", "L4_rr", "L8_rr", "L8_blk"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.2))
    for f in fmts:
        md = d["formats"][f]["median_c"]
        a1.plot(range(len(cfgs)), [md[c] for c in cfgs], "o-", ms=3, lw=1.2, label=f)
    a1.set_xticks(range(len(cfgs)))
    a1.set_xticklabels([c.replace("_", "\n") for c in cfgs], fontsize=7)
    a1.set_ylabel("median $c$")
    a1.set_title("lanes reduce the median")
    a1.grid(alpha=0.25)
    a1.legend(fontsize=7)
    w = 0.26
    for i, f in enumerate(fmts):
        pc = d["formats"][f]["per_case_ratio"]["L4_rr"]
        a2.bar([j + (i - 1) * w for j in range(3)],
               [pc["frac_better"], pc["frac_equal"], pc["frac_worse"]], w, label=f)
    a2.set_xticks(range(3))
    a2.set_xticklabels(["improve", "unchanged", "worse"])
    a2.set_ylabel("fraction of cases")
    a2.set_title("...but redistribute, not remove (L=4 rr)")
    a2.grid(alpha=0.25, axis="y")
    a2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_library(path):
    """Fig. 5 -- the library's reduction: which structure reproduces its per-case error."""
    d = load("spike_struct_results.json")
    fmts = ["fp16", "fp32", "fp64"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    names = ["chain", "pairwise", "lanes4", "lanes8", "lanes16"]
    w = 0.15
    for i, f in enumerate(fmts):
        dd = d["formats"][f]
        q1 = {r["name"]: r for r in dd["q1"]}
        n = dd["n_library_rounds"]
        ax.bar([j + (i - 1) * w for j in range(len(names))],
               [q1[k]["exact"] / n if k in q1 else 0.0 for k in names], w, label=f)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel("fraction of rounding cases reproduced")
    ax.set_title("which structure reproduces the real library")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main(argv):
    out = OUT
    if "--outdir" in argv:
        out = argv[argv.index("--outdir") + 1]
    if not os.path.isdir(out):
        os.makedirs(out)
    jobs = [("fig1_floor.png", fig_floor), ("fig2_width_law.png", fig_width_law),
            ("fig3_order_axis.png", fig_order_axis), ("fig4_lanes.png", fig_lanes),
            ("fig5_library_structure.png", fig_library)]
    for name, fn in jobs:
        p = os.path.join(out, name)
        fn(p)
        print("wrote %s (%d bytes)" % (name, os.path.getsize(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
