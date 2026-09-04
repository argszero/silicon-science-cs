#!/usr/bin/env python3
"""Generate all data figures for issue #79 manuscript (post-publication enhancement).

Every series below is transcribed VERBATIM from the published manuscript tables
(papers/issue-79/manuscript.md, v1, merged via PR #81) and README_repro.md; no new
measurements. Source anchors are noted per figure. Regenerate with:

    ./.venv/bin/python make_figures.py        # from figures/ (venv: python3 -m venv .venv + pip install matplotlib numpy)

Outputs fig1..fig6 PNGs into this directory. See README_repro.md for the per-run
variance table that panels (b) of Fig 5 draw on.
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

C_BASE = "#8da0cb"; C_RL = "#e08214"; C_SEARCH = "#66c2a5"; C_DEST = "#d62728"; C_OK = "#2ca02c"

def save(fig, name):
    path = os.path.join(HERE, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)

# ----------------------------------------------------------------------------
# Fig 1 (manuscript §5.2, Table RACE): seed-lottery bars, search baseline, R179 re-draw
# ----------------------------------------------------------------------------
def fig1_race():
    seeds = ["seed 0", "seed 1", "seed 2"]
    rl = [0.172, 0.076, 0.000]              # held-out eval 777, R169 (manuscript §5.2)
    r179 = [0.172, 0.174, 0.003]            # clean-clone re-draw (README_repro.md)
    x = np.arange(3); w = 0.38
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    ax.bar(x, rl, w, color=C_RL, label="RL greedy (eval 777, R169)")
    ax.scatter(x + w/2 + 0.04, r179, marker="+", s=60, color="#1f77b4", zorder=5,
               label="R179 clean re-run draw")
    ax.axhline(0.083, color=C_SEARCH, ls="--", lw=1.2)
    ax.text(2.42, 0.097, "base+search pass@64 = 0.083", color=C_SEARCH, fontsize=7.5, ha="right")
    ax.set_xticks(x); ax.set_xticklabels(seeds)
    ax.set_ylabel("greedy accuracy (carry class)")
    ax.set_ylim(0, 0.30); ax.set_title("RACE (count L20, p0≈3e-3): bootstrap seed-lottery")
    ax.legend(fontsize=6.5, loc="upper left")
    save(fig, "fig1_race_lottery.png")

# ----------------------------------------------------------------------------
# Fig 2 (manuscript §5.3, CREATE): base vs RL greedy per seed
# ----------------------------------------------------------------------------
def fig2_create():
    seeds = ["seed 0", "seed 1", "seed 2"]
    base = [0.130, 0.034, 0.034]
    rl = [0.378, 0.505, 0.565]
    x = np.arange(3); w = 0.34
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    ax.bar(x - w/2, base, w, color=C_BASE, label="SFT base greedy")
    ax.bar(x + w/2, rl, w, color=C_RL, label="RL greedy (eval 777)")
    for i, (b, r) in enumerate(zip(base, rl)):
        ax.annotate("%.0fx" % (r / b), (i + w/2 + 0.05, r + 0.02), fontsize=7, color=C_RL)
    ax.set_xticks(x); ax.set_xticklabels(seeds)
    ax.set_ylabel("greedy accuracy")
    ax.set_ylim(0, 0.75); ax.set_title("CREATE (count L12, p0≥0.03): RL lifts every seed")
    ax.text(0.02, 0.02, "R179 clean re-run: 0.305–0.432 (same mechanism, lower base draw)",
            fontsize=6.5, transform=ax.transAxes, color="0.3")
    ax.legend(fontsize=7, loc="upper left")
    save(fig, "fig2_create_lift.png")

# ----------------------------------------------------------------------------
# Fig 3 (manuscript §5.4): add-family coverage sweep — WALL → DESTROY → mild degrade
# ----------------------------------------------------------------------------
def fig3_add_cov():
    cov = [0.0, 0.003, 0.01, 0.03, 0.10]
    bg = [0.000, 0.000, 0.156, 0.143, 0.948]
    bp = [0.000, 0.000, 0.792, 0.958, 1.000]
    rg = [0.000, 0.000, 0.083, 0.128, 0.742]
    rp = [0.000, 0.000, 0.333, 0.812, 1.000]
    fig, ax = plt.subplots(figsize=(4.2, 2.7))
    xs = np.arange(len(cov))
    ax.plot(xs, bg, "o-", color=C_BASE, lw=1.4, label="base greedy")
    ax.plot(xs, bp, "s--", color=C_SEARCH, lw=1.2, label="base pass@64 (search)")
    ax.plot(xs, rg, "o-", color=C_RL, lw=1.4, label="RL greedy")
    ax.plot(xs, rp, "s-", color=C_DEST, lw=1.4, label="RL pass@64")
    ax.axvspan(-0.4, 1.4, color="0.85", alpha=0.5)
    ax.text(0.5, 0.92, "WALL", ha="center", fontsize=8, color="0.25")
    ax.axvspan(1.6, 3.4, color="#fde0dd", alpha=0.7)
    ax.text(2.5, 0.92, "DESTROY", ha="center", fontsize=8, color=C_DEST)
    ax.set_xticks(xs); ax.set_xticklabels(["0", "0.003", "0.01", "0.03", "0.10"])
    ax.set_xlabel("carry coverage c in SFT base")
    ax.set_ylabel("accuracy (carry class)")
    ax.set_ylim(-0.03, 1.1); ax.set_title("Add family: RL contracts what search used")
    ax.legend(fontsize=6.8, ncol=2, loc="lower right")
    save(fig, "fig3_add_coverage.png")

# ----------------------------------------------------------------------------
# Fig 4 (manuscript §5.4, R171): budget trajectory — greedy recovers, pass@64 collapses
# ----------------------------------------------------------------------------
def fig4_budget():
    budget = ["base", "500", "1000", "1500"]
    rg = [0.156, 0.083, 0.120, 0.161]
    rp = [0.833, 0.333, 0.167, 0.188]
    nc = [1.000, np.nan, 0.935, 0.828]   # no-carry drift (RL greedy, §5.4)
    xs = np.arange(4)
    fig, ax = plt.subplots(figsize=(4.2, 2.7))
    ax.plot(xs, rg, "o-", color=C_OK, lw=1.6, label="RL greedy (carry): dip, then recovers to base")
    ax.plot(xs, rp, "s-", color=C_DEST, lw=1.8, label="RL pass@64 (carry): collapses, never recovers")
    ax.plot(xs[0], 0.156, "o", color=C_BASE, zorder=5, label="base greedy = 0.156")
    ax.plot(xs, nc, "^:", color="0.5", lw=1.1, label="RL greedy (no-carry class)")
    ax.fill_between(xs[1:], np.array(rp[1:]) - 0.0, np.array(rp[1:]) + 0.12, color=C_DEST, alpha=0.08)
    ax.annotate("greedy-only eval would say\n'recovered to base by 1500'",
                xy=(3, 0.161), xytext=(1.05, 0.62), fontsize=7,
                arrowprops=dict(arrowstyle="->", color="0.4"), color=C_OK)
    ax.annotate("sampling channel destroyed\n(pass@64 0.833 → 0.188)",
                xy=(2.7, 0.19), xytext=(1.0, 0.05), fontsize=7,
                arrowprops=dict(arrowstyle="->", color="0.4"), color=C_DEST)
    ax.set_xticks(xs); ax.set_xticklabels(budget)
    ax.set_xlabel("GRPO budget (steps; base = no RL)")
    ax.set_ylabel("accuracy (add c=0.01, seed 0)")
    ax.set_ylim(-0.02, 1.12); ax.set_title("DESTROY: greedy and pass@k decouple with budget")
    ax.legend(fontsize=6.5, loc="upper right")
    save(fig, "fig4_budget_decouple.png")

# ----------------------------------------------------------------------------
# Fig 5 (manuscript §5.5): parity — (a) coverage sweep; (b) rl_p64 bimodality across runs
# ----------------------------------------------------------------------------
def fig5_parity():
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    cov = [0.0, 0.003, 0.01, 0.03, 0.10, 0.50]
    bog = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    bp = [0.000, 0.021, 0.208, 0.604, 1.000, 1.000]
    rg = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    rp = [0.000, 0.021, 0.583, 1.000, 1.000, 1.000]
    xs = np.arange(len(cov))
    ax.plot(xs, bp, "s--", color=C_SEARCH, lw=1.2, label="base pass@64")
    ax.plot(xs, rp, "s-", color=C_RL, lw=1.4, label="RL pass@64")
    ax.plot(xs, bog, "o-", color=C_BASE, lw=1.4, label="base odd greedy")
    ax.plot(xs, rg, "o-", color=C_DEST, lw=1.4, ls=":", label="RL odd greedy")
    ax.annotate("balanced SFT (c=0.5)\nlearns parity → imbalance, not unlearnability",
                xy=(5, 1.0), xytext=(2.6, 0.55), fontsize=6.5,
                arrowprops=dict(arrowstyle="->", color="0.4"))
    ax.set_xticks(xs); ax.set_xticklabels(["0", ".003", ".01", ".03", ".10", ".50"])
    ax.set_xlabel("odd coverage c in SFT base")
    ax.set_ylabel("accuracy (odd class)")
    ax.set_ylim(-0.03, 1.12); ax.set_title("(a) GREEDY-BLIND: argmax pinned at 0,\nsampling mass grows")
    ax.legend(fontsize=6.3, loc="upper left")
    ax = axes[1]
    runs = ["R177\n(author)", "editor\nindependent", "R179\nclean re-run"]
    base = [1.0, 1.0, 1.0]
    rlp = [1.000, 0.90, 0.021]   # editor run measured ">=0.9" (not published exactly)
    x2 = np.arange(3); w = 0.34
    ax.bar(x2 - w/2, base, w, color=C_SEARCH, label="base pass@64")
    b1 = ax.bar(x2 + w/2, rlp, w, color=C_RL, label="post-RL pass@64")
    b1[1].set_alpha(0.45); b1[1].set_hatch("//")
    ax.text(1 + w/2, 0.93, "≥0.9", ha="center", fontsize=7, color=C_RL)
    ax.annotate("bimodal:\nRL destroys a perfect\n2-value sampling\nchannel in 1/3 runs",
                xy=(2 + w/2, 0.06), xytext=(0.05, 0.55), fontsize=6.8,
                arrowprops=dict(arrowstyle="->", color="0.4"), color=C_DEST)
    ax.set_xticks(x2); ax.set_xticklabels(runs, fontsize=7)
    ax.set_ylabel("pass@64 (odd class, c=0.10)")
    ax.set_ylim(0, 1.15); ax.set_title("(b) post-RL search channel is\nnot reliably preserved")
    ax.legend(fontsize=6.3, loc="upper right")
    save(fig, "fig5_parity_sweep_bimodal.png")

# ----------------------------------------------------------------------------
# Fig 6 (manuscript §5.7, R173 + R174): entropy mechanism (incl. no-KL ablation)
# ----------------------------------------------------------------------------
def fig6_entropy():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    fams = ["count L12\n(CREATE)", "add band\n(DESTROY)"]
    ent_base = [0.81, 2.19]; ent_rl = [1.22, 0.55]; ent_nokl = [1.42, 0.63]
    cp_base = [0.125, 0.075]; cp_rl = [0.397, 0.231]; cp_nokl = [0.384, 0.325]
    x = np.arange(2); w = 0.26
    ax = axes[0]
    ax.bar(x - w, ent_base, w, color=C_BASE, label="SFT base")
    ax.bar(x, ent_rl, w, color=C_RL, label="RL (KL-anchored)")
    ax.bar(x + w, ent_nokl, w, color="#9467bd", label="RL (no-KL)")
    ax.set_xticks(x); ax.set_xticklabels(fams)
    ax.set_ylabel("per-prompt answer entropy (bits)")
    ax.set_title("(a) sampling support: expands in CREATE,\ncontracts 4x in DESTROY")
    ax.legend(fontsize=6.3)
    ax = axes[1]
    ax.bar(x - w, cp_base, w, color=C_BASE)
    ax.bar(x, cp_rl, w, color=C_RL)
    ax.bar(x + w, cp_nokl, w, color="#9467bd")
    for i in range(2):
        ax.annotate("%.0fx" % (cp_rl[i] / cp_base[i]), (x[i], cp_rl[i] + 0.012),
                    ha="center", fontsize=7.5, color=C_RL)
    ax.set_xticks(x); ax.set_xticklabels(fams)
    ax.set_ylabel("per-sample correct probability")
    ax.set_title("(b) correct-p rises ~3x in both\n(the KL anchor is not the mechanism)")
    ax.set_ylim(0, 0.5)
    save(fig, "fig6_entropy_mechanism.png")

if __name__ == "__main__":
    fig1_race(); fig2_create(); fig3_add_cov(); fig4_budget(); fig5_parity(); fig6_entropy()
    print("all figures generated in", HERE)
