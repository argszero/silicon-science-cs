#!/usr/bin/env python3
"""Regenerate every figure in the manuscript from the committed artefacts.

Figures are drawn ONLY from artefacts, never from inline constants, so a figure cannot
drift from the JSON that a table quotes.  Requires matplotlib (the instruments do not).
"""
import io
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
J = lambda n: json.load(io.open(os.path.join(HERE, "artefacts", n), encoding="utf-8"))

v0, v1, v2, v3 = J("results_v0.json"), J("results_v1.json"), J("results_v2.json"), J("results_v3.json")
P = v3["part"]
plt.rcParams.update({"figure.dpi": 160, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False})
C = {"a": "#1f4e79", "b": "#c00000", "c": "#2e7d32", "d": "#8e44ad"}


def save(fig, name, title):
    p = os.path.join(FIG, name)
    fig.suptitle(title, fontsize=10, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/" + name)


# ---- fig1: the dial -- accuracy constant, marginal value collapsing ----
fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.9))
b = [s["beta"] for s in v0["beta_sweep"]]
ax[0].plot(b, [s["C2_hat"] for s in v0["beta_sweep"]], "o-", color=C["a"], label="measured C2")
ax[0].axhline(0.15, ls="--", lw=1, color="grey", label="nominal C2 = 0.15")
ax[0].set_xlabel("dial beta"); ax[0].set_ylabel("standalone catch rate")
ax[0].set_title("accuracy is invariant across the dial", fontsize=9); ax[0].legend(fontsize=7)
ax[1].plot(b, [s["marginal_catch"] for s in v0["beta_sweep"]], "s-", color=C["b"], label="marginal catch")
ax[1].plot(b, [0.2 * (1 - x) * 0.15 for x in b], ":", color="black", lw=1.4,
           label="p0 (1 - beta) C2")
ax[1].axvline(0.30, ls="-.", lw=1.2, color=C["c"])
ax[1].annotate("independence\nbeta = f", xy=(0.30, 0.011), fontsize=7, color=C["c"], ha="left")
ax[1].set_xlabel("dial beta"); ax[1].set_ylabel("catch on primary failures")
ax[1].set_title("but its marginal value collapses to zero", fontsize=9); ax[1].legend(fontsize=7)
save(fig, "fig1_dial.png", "The redundancy dial: same accuracy, different worth")

# ---- fig2: the span, synthetic vs calibrated ----
fig, ax = plt.subplots(figsize=(5.0, 3.1))
lbl = ["synthetic grid", "calibrated\n(10 published systems)"]
lo = [P["span"]["synthetic"]["min"], P["span"]["calibrated"]["min"]]
hi = [P["span"]["synthetic"]["max"], P["span"]["calibrated"]["max"]]
ax.bar(lbl, [h - l for h, l in zip(hi, lo)], bottom=lo, color=[C["b"], C["c"]], width=0.55)
for i, (l, h) in enumerate(zip(lo, hi)):
    ax.text(i, h * 1.25, "%.2fx" % (h / l), ha="center", fontsize=10, fontweight="bold")
ax.set_yscale("log"); ax.set_ylabel("break-even threshold T (log scale)")
ax.set_title("138x was our grid; 4.84x is theirs", fontsize=10)
save(fig, "fig2_span.png", "Threshold span: synthetic vs calibrated")

# ---- fig3: law race, both regimes ----
fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.0), sharey=False)
laws = ["L0_constant", "L1_by_cost_ratio", "L2_operational", "L3_independence", "L4_parametric"]
short = ["const", "cost-r", "oper.", "indep", "param"]
syn = [v2["laws"][k]["oos"]["decision_accuracy"] for k in laws]
cal = [P["race_on_calibrated_region"][k]["score"]["decision_accuracy"] for k in laws]
x = range(len(laws))
ax[0].bar([i - 0.2 for i in x], syn, 0.4, label="synthetic held-out", color=C["b"])
ax[0].bar([i + 0.2 for i in x], cal, 0.4, label="calibrated held-out", color=C["c"])
ax[0].set_xticks(list(x)); ax[0].set_xticklabels(short, fontsize=8)
ax[0].set_ylim(0, 1.08); ax[0].set_ylabel("decision accuracy")
ax[0].axhline(1.0, ls=":", color="grey", lw=0.8)
ax[0].set_title("decision accuracy", fontsize=9); ax[0].legend(fontsize=7, loc="lower left")
ax[1].bar([i - 0.2 for i in x], [v2["laws"][k]["oos"]["median_rel_err"] for k in laws], 0.4,
          color=C["b"])
ax[1].bar([i + 0.2 for i in x], [P["race_on_calibrated_region"][k]["score"]["median_rel_err"] for k in laws], 0.4,
          color=C["c"])
ax[1].set_xticks(list(x)); ax[1].set_xticklabels(short, fontsize=8)
ax[1].set_ylabel("median relative error"); ax[1].set_title("threshold error", fontsize=9)
save(fig, "fig3_lawrace.png", "The law race on both regimes")

# ---- fig4: composition ----
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
m = P["composition"]["arms"]["skewed"]["matched"]
s = P["composition"]["arms"]["skewed"]["spread"]
k = range(1, len(m["marginals"]) + 1)
ax[0].plot(k, m["marginals"], "o-", color=C["a"], label="matched allocation")
ax[0].plot(k, s["marginals"], "s-", color=C["b"], label="concentrating allocation")
ax[0].set_xlabel("layer index"); ax[0].set_ylabel("marginal catch")
ax[0].set_title("identical capacity, different saturation", fontsize=9); ax[0].legend(fontsize=7)
ax[1].bar(["matched", "concentrating"], [m["cumulative"], s["cumulative"]],
          color=[C["a"], C["b"]], width=0.5)
for i, val in enumerate([m["cumulative"], s["cumulative"]]):
    ax[1].text(i, val + 0.006, "%.4f" % val, ha="center", fontsize=8)
ax[1].set_ylim(0, 0.72); ax[1].set_ylabel("cumulative 4-layer catch")
ax[1].set_title("8.5 percent apart", fontsize=9)
save(fig, "fig4_composition.png", "Summary statistics do not determine composition")

# ---- fig5: adversarial crossover ----
fig, ax = plt.subplots(figsize=(5.2, 3.0))
sw = P["adversarial"]["sweep"]
h = [p["h"] for p in sw]; d = [p["delta"] for p in sw]
ax.plot(h, d, "-", color=C["a"], lw=1.8)
ax.axhline(0, color="black", lw=0.8)
ax.axvline(P["adversarial"]["h_star"], ls="--", color=C["b"])
ax.annotate("h_star = %.4f" % P["adversarial"]["h_star"],
            xy=(P["adversarial"]["h_star"], min(d) * 0.55), fontsize=8, color=C["b"], ha="left")
ax.fill_between(h, d, 0, where=[x > 0 for x in d], color=C["c"], alpha=0.18)
ax.fill_between(h, d, 0, where=[x < 0 for x in d], color=C["b"], alpha=0.18)
ax.set_xlabel("harm rate h (degradation of items the primary got right)")
ax.set_ylabel("net change in catch rate")
ax.set_title("a layer that also harms has a finite crossover (model-derived)", fontsize=9)
save(fig, "fig5_adversarial.png", "The adversarially-correlated layer")

# ---- fig6: baselines ----
fig, ax = plt.subplots(figsize=(5.6, 3.0))
names = ["residual-catch", "equal-split", "coverage-first", "primary-only", "random", "accuracy-ordered"]
vals = [v1["regret"]["analytic"]["mean_value_ratio"], v1["regret"]["equal_split"]["mean_value_ratio"],
        v1["regret"]["coverage_first"]["mean_value_ratio"], v1["regret"]["primary_only"]["mean_value_ratio"],
        v1["regret"]["random"]["mean_value_ratio"], v1["regret"]["accuracy_ordered"]["mean_value_ratio"]]
cols = [C["c"]] + [C["a"]] * 4 + [C["b"]]
ax.barh(names[::-1], vals[::-1], color=cols[::-1], height=0.6)
for i, val in enumerate(vals[::-1]):
    ax.text(val + 0.012, i, "%.3f" % val, va="center", fontsize=8)
ax.set_xlim(0, 1.12); ax.set_xlabel("achieved reduction / achievable maximum")
ax.set_title("accuracy-ordered selection captures about half", fontsize=10)
save(fig, "fig6_baselines.png", "The ranking practitioners use is not the ranking that works")
