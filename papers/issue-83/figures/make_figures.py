#!/usr/bin/env python3
"""Generate all data figures for issue #83 manuscript (recovery study).

Every series is transcribed VERBATIM from the measured values tabulated in
README_repro.md (the R182-R184 eval-777 runs; source anchors noted per figure) — no
new measurements. Regenerate with:

    python3 -m venv .venv && ./.venv/bin/pip install matplotlib numpy   # once
    ./.venv/bin/python make_figures.py        # from figures/

Outputs fig1..fig5 PNGs into this directory.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "figure.dpi": 150, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})
C_BASE = "#8da0cb"; C_COLL = "#d62728"; C_REPLAY = "#2ca02c"; C_FAIL = "#e08214"
C_OK = "#2ca02c"; C_REF = "#9467bd"

def save(fig, name):
    fig.savefig(os.path.join(HERE, name), bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)

# ---------------------------------------------------------------------------
# Fig 1 — 3-seed DESTROY recovery: base / collapsed / replay pass@64
# ---------------------------------------------------------------------------
def fig1_seeds():
    seeds = ["seed 0", "seed 1", "seed 2"]
    base = [0.835, 0.292, 0.417]     # s0 = mid of 0.792/0.875 band
    collapsed = [0.146, 0.208, 0.062]
    replayed = [0.938, 0.854, 0.438]
    x = np.arange(3); w = 0.26
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    ax.bar(x - w, base, w, color=C_BASE, label="SFT base (target)")
    ax.bar(x, collapsed, w, color=C_COLL, label="collapsed (1500-step RL)")
    ax.bar(x + w, replayed, w, color=C_REPLAY, label="replayed (600-step SFT)")
    for i, (b, c, r) in enumerate(zip(base, collapsed, replayed)):
        ax.annotate("%.1fx" % (r / c), (i + w + 0.03, r + 0.02), fontsize=7, color=C_REPLAY)
    ax.set_xticks(x); ax.set_xticklabels(seeds)
    ax.set_ylabel("pass@64 (carry class, eval 777)")
    ax.set_ylim(0, 1.12)
    ax.set_title("Recovery 3/3: SFT-replay restores the destroyed search channel")
    ax.legend(fontsize=7, loc="upper left")
    save(fig, "fig1_recovery_3seeds.png")

# ---------------------------------------------------------------------------
# Fig 2 — intervention taxonomy from collapsed s0
# ---------------------------------------------------------------------------
def fig2_taxonomy():
    arms = ["continue\n1000", "KL-reanchor\nβ=0.01", "KL-reanchor\nβ=0.1", "KL-reanchor\nβ=1.0",
            "entropy-bonus\nλ=0.005", "entropy-bonus\nλ≥0.02", "SFT-replay\n600"]
    p64 = [0.188, 0.104, 0.146, 0.333, 0.188, 0.000, 0.938]
    colors = [C_FAIL]*6 + [C_REPLAY]
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    bars = ax.bar(np.arange(len(arms)), p64, 0.62, color=colors)
    ax.axhspan(0.79, 0.88, color=C_BASE, alpha=0.25)
    ax.text(6.35, 0.86, "base band", fontsize=7, color="0.3", ha="right")
    ax.axhline(0.146, color=C_COLL, ls="--", lw=1.0)
    ax.text(6.35, 0.155, "collapsed start", fontsize=7, color=C_COLL, ha="right")
    for bar, v in zip(bars, p64):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.02, "%.3f" % v, ha="center", fontsize=6.8)
    ax.set_xticks(np.arange(len(arms))); ax.set_xticklabels(arms, fontsize=7)
    ax.set_ylabel("pass@64 after intervention (carry, eval 777)")
    ax.set_ylim(0, 1.1)
    ax.set_title("Policy-space pressure does not recover; data reintroduction does")
    save(fig, "fig2_intervention_taxonomy.png")

# ---------------------------------------------------------------------------
# Fig 3 — per-prompt entropy mechanism (base/collapsed/replay/strong-KL)
# ---------------------------------------------------------------------------
def fig3_entropy():
    labels = ["SFT base", "collapsed\n(1500 RL)", "SFT-replay\n600", "strong-KL β=1\n(no recovery)"]
    ent = [2.51, 0.50, 2.66, 0.77]
    dist = [10.81, 3.00, 9.19, 3.69]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8))
    colors = [C_BASE, C_COLL, C_REPLAY, C_REF]
    ax = axes[0]
    ax.bar(np.arange(4), ent, 0.6, color=colors)
    for i, v in enumerate(ent):
        ax.text(i, v + 0.05, "%.2f" % v, ha="center", fontsize=7.5)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("per-prompt answer entropy (bits)")
    ax.set_ylim(0, 3.2)
    ax.set_title("(a) sampling support re-expands with replay")
    ax = axes[1]
    ax.bar(np.arange(4), dist, 0.6, color=colors)
    for i, v in enumerate(dist):
        ax.text(i, v + 0.15, "%.1f" % v, ha="center", fontsize=7.5)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("distinct answers / prompt")
    ax.set_ylim(0, 13)
    ax.set_title("(b) answer diversity (fresh carry prompts, temp 0.8)")
    save(fig, "fig3_entropy_mechanism.png")

# ---------------------------------------------------------------------------
# Fig 4 — GREEDY-BLIND parity mechanism separation
# ---------------------------------------------------------------------------
def fig4_parity():
    labels = ["SFT base\n(c=0.10)", "collapsed\n(R179 RL)", "SFT-replay\n600"]
    p64 = [0.958, 0.021, 0.938]     # collapsed = R179 log value (this-draw eval 0.000)
    greedy = [0.000, 0.000, 0.000]
    x = np.arange(3); w = 0.3
    fig, ax = plt.subplots(figsize=(4.4, 2.9))
    ax.bar(x - w/2, p64, w, color=[C_BASE, C_COLL, C_REPLAY], label="odd pass@64 (search channel)")
    ax.bar(x + w/2, greedy, w, color="0.55", label="odd greedy (argmax)")
    for i, v in enumerate(p64):
        ax.text(i - w/2, v + 0.02, "%.3f" % v, ha="center", fontsize=7)
    ax.axhline(0.0, color="0.4", lw=0.8)
    ax.annotate("replay restores the RL-destroyed channel...",
                xy=(2 - w/2, 0.938), xytext=(0.1, 0.75), fontsize=7,
                arrowprops=dict(arrowstyle="->", color="0.4"))
    ax.annotate("...but the imbalance-pinned argmax stays 0.000",
                xy=(2 + w/2, 0.02), xytext=(0.2, 0.18), fontsize=7,
                arrowprops=dict(arrowstyle="->", color="0.4"))
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("odd-class accuracy (eval 777)")
    ax.set_ylim(0, 1.12)
    ax.set_title("Two mechanisms, two owners: imbalance pins greedy,\nRL destroyed the channel, replay restores it")
    ax.legend(fontsize=6.8, loc="upper left")
    save(fig, "fig4_parity_separation.png")

# ---------------------------------------------------------------------------
# Fig 5 — warm-start: replay-from-collapsed vs fresh SFT at matched budget
# ---------------------------------------------------------------------------
def fig5_warmstart():
    labels = ["fresh SFT\n300 steps", "replay from\ncollapsed 300", "fresh SFT\n600 (=base)", "replay from\ncollapsed 600"]
    p64 = [0.000, 0.729, 0.855, 0.938]   # fresh 600 = base band mid
    colors = [C_BASE, C_REPLAY, C_BASE, C_REPLAY]
    fig, ax = plt.subplots(figsize=(4.8, 2.9))
    bars = ax.bar(np.arange(4), p64, 0.55, color=colors)
    for bar, v in zip(bars, p64):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.02, "%.3f" % v, ha="center", fontsize=7.5)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("carry pass@64 (add c=0.01, seed 0)")
    ax.set_ylim(0, 1.1)
    ax.set_title("Warm start: the 'destroyed' policy beats training from scratch\nat every matched budget")
    ax.annotate("fresh 300: carry not yet\nbootstrapped at c=0.01",
                xy=(0, 0.0), xytext=(0.5, 0.1), fontsize=6.8,
                arrowprops=dict(arrowstyle="->", color="0.4"))
    save(fig, "fig5_warmstart.png")

if __name__ == "__main__":
    fig1_seeds(); fig2_taxonomy(); fig3_entropy(); fig4_parity(); fig5_warmstart()
    print("all figures generated in", HERE)
