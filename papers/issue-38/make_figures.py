#!/usr/bin/env python3
"""Issue #38 - figures, drawn only from canonical_results.json.

    figures/fig1_collapse.png      measured sigma* against the law's prediction
    figures/fig2_scrambling.png    the scrambling signature (Hamming) and the mismatch rate
    figures/fig3_amplification.png the specialisation channel as an amplifier
    figures/manifest.json          the artefact digest each figure was drawn from

Declared rewritten by a run (README): the PNGs are build-dependent, so they are pinned by
agreement with the artefact (a manifest entry carrying the artefact digest), never by a
static byte hash.
"""
from __future__ import annotations

import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "canonical_results.json")
FIGDIR = os.path.join(HERE, "figures")

DPI = 150


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fig1(d):
    """The collapse: sigma* is a single scalar function of the planner's own error."""
    lg = d["law_grid"]
    cl = d["closure"]
    cells = [(c["planner_per_task"], c["sigma_star"], c["gamma"]) for c in lg["cells"]
             if c["sigma_star"] and c["planner_per_task"] > 0]
    p_law = np.array([c[0] for c in cells], float)
    s_law = np.array([c[1] for c in cells], float)
    g_law = np.array([c[2] for c in cells], float)
    const = cl["one_constant"]["c"]

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    sc = ax.scatter(p_law, s_law, c=g_law, cmap="viridis", s=26, alpha=0.85,
                    edgecolors="none", label="grid cells (%d)" % len(cells))
    xs = np.array([min(p_law) * 0.85, max(p_law) * 1.15])
    ax.plot(xs, const * xs, "k--", lw=1.2,
            label=r"$\sigma^\ast = %.2f\,p$" % const)
    ax.plot(xs, xs, color="0.6", lw=0.8, ls=":", label=r"$\sigma^\ast = p$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("planner per-task allocation error  $p$")
    ax.set_ylabel(r"measured crossover scale  $\sigma^\ast$")
    ax.set_title("The boundary is one scalar: $\\sigma^\\ast$ vs the planner's own error")
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label(r"cost scale  $\gamma$")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.grid(alpha=0.25, which="both", lw=0.4)
    fig.tight_layout()
    out = os.path.join(FIGDIR, "fig1_collapse.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def fig2(d):
    """Scrambling: a fixed noise scale reshuffles a growing share of the whole assignment."""
    me = d["mechanism"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.9))
    colours = {0.05: "tab:blue", 0.2: "tab:orange", 0.5: "tab:green"}
    for row in me["hamming"]:
        if row["gamma"] != 1.0 or row["beta"] != 0.5:
            continue
        Ns = [s["N"] for s in row["series"]]
        r = [s["rate"] for s in row["series"]]
        ax.plot(Ns, r, marker="o", ms=4, lw=1.4, color=colours.get(row["sigma"], None),
                label=r"$\sigma=%.2f$" % row["sigma"])
    ax.set_xscale("log", base=2)
    ax.set_ylim(0, 1)
    ax.set_xlabel("pool size  $N$")
    ax.set_ylabel("share of tasks assigned differently from the oracle")
    ax.set_title("Scrambling grows with the pool")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25, lw=0.4)

    for row in me["wrong_block_rate"]:
        if row["gamma"] != 1.0 or row["beta"] != 0.5:
            continue
        Ns = [s["N"] for s in row["series"]]
        r = [s["rate"] for s in row["series"]]
        ax2.plot(Ns, r, marker="s", ms=4, lw=1.4, color=colours.get(row["sigma"], None),
                 label=r"$\sigma=%.2f$" % row["sigma"])
    ax2.set_xscale("log", base=2)
    ax2.set_ylim(-0.02, 1)
    ax2.set_xlabel("pool size  $N$")
    ax2.set_ylabel("share assigned to a wrong-specialisation agent")
    ax2.set_title("Noise does not break specialisation")
    ax2.legend(fontsize=8, frameon=False)
    ax2.grid(alpha=0.25, lw=0.4)
    fig.tight_layout()
    out = os.path.join(FIGDIR, "fig2_scrambling.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def fig3(d):
    """The specialisation channel is an amplifier, not the source of the advantage."""
    rows = d["p3_ablation"]["rows"]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    for N in sorted({r["N"] for r in rows}):
        pts = sorted([(r["beta"], r["sigma_star"]) for r in rows
                      if r["N"] == N and r["sigma_star"]], key=lambda t: t[0])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=4, lw=1.5,
                label="$N=%d$" % N)
    amp = d["p3_ablation"]["amplification_beta_max_over_beta_0"]
    ax.axvline(0.0, color="0.6", lw=0.9, ls=":")
    ax.annotate("specialisation channel OFF\n(boundary still exists)",
                xy=(0.02, min(r["sigma_star"] for r in rows if r["sigma_star"]) * 1.02),
                fontsize=8, color="0.25")
    ax.set_xlabel(r"specialisation premium  $\beta$")
    ax.set_ylabel(r"crossover scale  $\sigma^\ast$")
    ax.set_title("Specialisation amplifies the advantage by a constant "
                 r"($\times$%s)" % ("%.1f" % np.mean(list(amp.values()))))
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25, lw=0.4)
    fig.tight_layout()
    out = os.path.join(FIGDIR, "fig3_amplification.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    with open(ART, encoding="utf-8") as f:
        d = json.load(f)
    art_digest = sha(ART)
    figs = [fig1(d), fig2(d), fig3(d)]
    manifest = {
        "artefact": os.path.basename(ART),
        "artefact_sha256": art_digest,
        "note": ("figures are regenerated by the run and are build-dependent; each entry "
                 "records the artefact digest it was drawn from, so agreement is checked "
                 "against the data, not against a static byte hash"),
        "figures": [{"file": os.path.basename(p), "sha256": sha(p)} for p in figs],
        "claims": {
            "fig1_collapse.png": "law_grid.cells + closure.one_constant.c",
            "fig2_scrambling.png": "mechanism.hamming + mechanism.wrong_block_rate",
            "fig3_amplification.png": "p3_ablation.rows + p3_ablation.amplification",
        },
    }
    with open(os.path.join(FIGDIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
        f.write("\n")
    for p in figs:
        print("wrote", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
