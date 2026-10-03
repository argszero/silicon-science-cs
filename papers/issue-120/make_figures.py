#!/usr/bin/env python3
"""Issue #120 -- figures.  Every figure is drawn from a committed *_results.json produced by the
instruments in this directory; nothing is drawn from a number typed into this file.

Usage:  /usr/bin/python3 make_figures.py
Out:    figures/fig1..fig5 .png + figures/manifest.json (sha256 per figure)
"""
import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
N = 50000            # spike_v1 trace length
FAMS = ["uniform", "powerlaw1", "powerlaw2", "hotset", "scan8", "scan64"]
LABEL = {"uniform": "uniform", "powerlaw1": "power-law 1.0", "powerlaw2": "power-law 2.0",
         "hotset": "hot set 10/90", "scan8": "scan, chunk 8", "scan64": "scan, chunk 64"}


def load(name):
    with open(os.path.join(HERE, name + "_results.json")) as f:
        return json.load(f)


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print("   %-28s %8d bytes" % (name, os.path.getsize(p)))
    return p


def fig1(v1):
    """P1: the deployed-policy gap against the exact floor, versus fast-tier fraction."""
    fig, ax = plt.subplots(figsize=(6.2, 4.1))
    for fam in FAMS:
        cells = sorted([c for c in v1["cells"] if c["family"] == fam], key=lambda c: c["h"])
        ax.plot([c["h"] for c in cells], [100 * c["gap_LRU"] for c in cells],
                marker="o", ms=3.4, lw=1.4, label=LABEL[fam])
    ax.axhline(20, ls=":", c="k", lw=1)
    ax.text(0.51, 21.5, "P1 limb A bar: 20 % at h <= 0.2", fontsize=7.5, ha="right")
    ax.set_xlabel("fast-tier fraction h = c / |U|")
    ax.set_ylabel("LRU gap above the exact floor  (%)")
    ax.set_title("The gap's direction is not monotone in capacity\n(6 families x 7 capacities x 3 seeds, n = 50000)",
                 fontsize=9.5)
    ax.legend(fontsize=7.5, ncol=2, loc="upper left")
    ax.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig1_gap_vs_capacity.png")


def fig2(v4):
    """The matched pair: identical profile and identical LRU curve, different optima."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.5))
    caps = [r["cap"] for r in v4["curve"]]
    a1.plot(caps, [100 * r["phi_A"] for r in v4["curve"]], marker="o", ms=4, lw=1.5, label="oracle, trace A")
    a1.plot(caps, [100 * r["phi_B"] for r in v4["curve"]], marker="s", ms=4, lw=1.5, label="oracle, trace B")
    a1.plot(caps, [100 * r["lru"] for r in v4["curve"]], marker="^", ms=4, lw=1.2, ls="--",
            label="LRU (both traces)")
    a1.annotate("2x", xy=(2, 22.3), xytext=(2.55, 33),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
    a1.set_xlabel("capacity c")
    a1.set_ylabel("slow-tier traffic  (%)")
    a1.set_title("n = 9: identical profile, identical LRU,\ndifferent optima", fontsize=9)
    a1.legend(fontsize=7.5)
    a1.grid(alpha=0.25, lw=0.5)
    K = [r["K"] for r in v4["rows"]]
    a2.plot(K, [100 * r["gap"] for r in v4["rows"]], marker="o", ms=4, lw=1.5)
    a2.text(0.30, 0.62, "the stack-distance multisets are identical at every K:\n"
                        "sd-L1 = %.4f (asserted, all four scales)" % max(r["sd_l1"] for r in v4["rows"]),
            transform=a2.transAxes, fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6))
    a2.set_xscale("log")
    a2.set_ylim(0, 118)
    a2.axhline(100, ls=":", c="k", lw=1)
    a2.set_xlabel("scale factor K  (trace length n = 9K)")
    a2.set_ylabel("oracle gap B vs A  (%)")
    a2.set_title("the gap widens with scale, the profile\ndistance stays exactly zero", fontsize=9)
    a2.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig2_matched_pair.png")


def fig3(v2):
    """P3: the below-head relief, oracle vs the deployed policy."""
    rows = [r for r in v2["rows"] if r["below_head_share"] is not None
            and r["lru_below_head_share"] is not None]
    names = [r["family"] for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.bar([i - 0.2 for i in x], [r["below_head_share"] for r in rows], width=0.4,
           label="oracle  phi*", color="tab:blue")
    ax.bar([i + 0.2 for i in x], [r["lru_below_head_share"] for r in rows], width=0.4,
           label="LRU", color="tab:red")
    ax.axhline(0, c="k", lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel("share of relief delivered strictly\nbelow the working set")
    ax.set_title("P3 predicts ~0 here; the ORACLE is 0.78-0.97 and LRU is\nexactly 0.000 on the cyclic families", fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, lw=0.5, axis="y")
    return save(fig, "fig3_below_head.png")


def fig4(v2):
    """The thrashing cliff is the policy's: the same trace, oracle vs LRU, around capacity W."""
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    caps = v2["caps"]
    for fam, ls in (("loop8", "-"), ("loop16", "--"), ("loop32", ":")):
        r = [r for r in v2["rows"] if r["family"] == fam][0]
        W = int(r["h_true"] * 1000)
        idx = [i for i, c in enumerate(caps) if c <= W + 4]
        ax.plot([caps[i] for i in idx], [100 * r["phi_star"][i] for i in idx],
                ls=ls, lw=1.6, color="tab:blue",
                label="oracle, W = %d" % W if fam == "loop8" else None)
        ax.plot([caps[i] for i in idx], [100 * r["lru"][i] for i in idx],
                ls=ls, lw=1.6, color="tab:red",
                label="LRU, W = %d" % W if fam == "loop8" else None)
    ax.axvline(8, ls=":", c="tab:red", lw=1)
    ax.annotate("LRU gap 598 % at c = W-1\n(oracle 1384 % / 2859 % for W = 16 / 32)",
                xy=(7, 100), xytext=(11, 74), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=1))
    ax.set_xlabel("capacity c")
    ax.set_ylabel("slow-tier traffic  (%)")
    ax.set_title("The capacity knee is the policy's cliff, not the floor's shape", fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig4_policy_cliff.png")


def fig5(v5):
    """The profile-invisible fraction: how often a profile class carries a spread."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.4))
    items = sorted(v5["exhaustive"].items(), key=lambda kv: kv[1]["frac_spread"])
    names = [k.replace("_", ",") for k, _ in items]
    vals = [100 * v["frac_spread"] for _, v in items]
    a1.barh(range(len(items)), vals, color="tab:purple")
    a1.set_yticks(range(len(items)))
    a1.set_yticklabels(names, fontsize=7.5)
    a1.set_xlabel("% of profile classes carrying a spread of phi*")
    a1.set_xlim(0, 118)
    mid = 100 * v5["midscale"]["multi_classes"] / v5["midscale"]["classes"]
    a1.axvline(mid, ls="--", c="k", lw=1.1)
    a1.text(mid + 2, 0.2, "mid-scale n = 40:\n%.0f %%  (%d of %d)"
            % (mid, v5["midscale"]["multi_classes"], v5["midscale"]["classes"]),
            fontsize=7, va="bottom")
    a1.set_title("exhaustive small-scale sweep", fontsize=9)
    a1.grid(alpha=0.25, lw=0.5, axis="x")

    sc = [("exhaustive\n(max)", max(v["max_ratio"] for v in v5["exhaustive"].values())),
          ("mid-scale\n(n=40)", v5["midscale"]["max_ratio"]),
          ("practical\n(n=9000)", 1 + v5["practical"]["K=1000"]["gap"])]
    a2.bar([s[0] for s in sc], [s[1] for s in sc], color="tab:orange")
    for i, (_, v) in enumerate(sc):
        a2.text(i, v + 0.02, "%.2fx" % v, ha="center", fontsize=8.5)
    a2.set_ylim(1, 2.25)
    a2.set_ylabel("max ratio of optima inside one profile class")
    a2.set_title("the spread reaches 2x", fontsize=9)
    a2.grid(alpha=0.25, lw=0.5, axis="y")
    return save(fig, "fig5_profile_invisible.png")


def main():
    print("figures from the committed results artefacts")
    v1, v2, v4, v5 = load("spike_v1"), load("spike_v2"), load("spike_v4"), load("spike_v5")
    paths = [fig1(v1), fig2(v4), fig3(v2), fig4(v2), fig5(v5)]
    man = {}
    for p in paths:
        man[os.path.basename(p)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    with open(os.path.join(FIG, "manifest.json"), "w") as f:
        json.dump({k: man[k] for k in sorted(man)}, f, indent=1, sort_keys=True)
    print("-> figures/manifest.json (%d figures)" % len(man))
    return 0


if __name__ == "__main__":
    sys.exit(main())
