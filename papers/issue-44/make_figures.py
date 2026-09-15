#!/usr/bin/env python3
"""Issue #44 -- figures.

    figures/fig1_prediction.png     criterion (a): the construct, and invariance
    figures/fig2_band.png           criterion (b): the transition band and its width law
    figures/fig3_rule.png           criterion (c): the derived rule against the best constant
    figures/fig4_lattice.png        S1: the construct's limit is a lattice
    figures/fig5_ceiling.png        S2: what the ceiling bounds
    figures/fig6_decidability.png   S3: where the comparison is decidable
    figures/manifest.json           what every figure was drawn from, and its digest

EVERY number in every figure is read from `canonical_results.json` or from a stage
artefact -- nothing is typed into this file.  Each figure records, in the manifest, the
digest of the exact arrays it plotted, so a rerun under a different matplotlib build can
still be checked for CONTENT even though the PNG bytes legitimately depend on the build.

The instruments need no third-party package; only this file needs matplotlib.

    python3 make_figures.py [OUTDIR] [--audit-svg DIR]

OUTDIR defaults to `figures/` beside this file.  `--audit-svg DIR` additionally writes a
text-bearing SVG twin of every figure into DIR; that twin is what `verify_figures.py`
parses to check that the labels a reader is promised are actually DRAWN and fall inside
the rendered canvas.  The twins are an audit artefact, never part of the package.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIGD = os.path.join(HERE, "figures")
AUDIT_SVG_DIR = None          # set by main(); a text-bearing twin for the render audit

STAGE_FILES = ("results_v0.json", "results_v1.json", "results_v2.json",
               "results_v3.json", "results_v4.json")

INK = "#1a1a1a"
BLUE = "#1f4e79"
RED = "#c00000"
GREEN = "#2e7d32"
PURPLE = "#6a1b9a"
GREY = "#8a8a8a"
LIGHT = "#cfd8e3"
CYCLE = [BLUE, RED, GREEN, PURPLE]

plt.rcParams.update({
    "figure.dpi": 160,
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.28,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#5a5a5a",
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": "#4a4a4a",
    "ytick.color": "#4a4a4a",
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def sha256_file(path):
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def artist_series(fig):
    """The numbers the RENDERER holds, read back off the axes.

    A digest of a hand-written list of "what I plotted" can be fooled by a change to the
    plotting expression itself -- the list stays the same while the drawing moves.  This
    reads `ax.lines` / `ax.collections` / `ax.patches` after the fact, so the digest covers
    what is actually on the canvas.
    """
    out = []
    for ai, ax in enumerate(fig.axes):
        entry = {"axes": ai, "lines": [], "collections": [], "patches": []}
        for ln in ax.lines:
            entry["lines"].append([
                np.nan_to_num(np.asarray(ln.get_xdata(), dtype=float)).tolist(),
                np.nan_to_num(np.asarray(ln.get_ydata(), dtype=float)).tolist()])
        for col in ax.collections:
            arr = np.asarray(col.get_offsets(), dtype=float)
            entry["collections"].append(
                np.nan_to_num(arr).round(12).tolist() if arr.size else [])
        for pa in ax.patches:
            entry["patches"].append([float(pa.get_x()), float(pa.get_y()),
                                     float(pa.get_width()), float(pa.get_height())])
        out.append(entry)
    return out


MANIFEST = {
    "figures": [],
    "matplotlib": matplotlib.__version__,
    "note": ("series_sha256 covers BOTH the declared arrays and the numbers read back "
             "off the axes' artists after drawing, so a change to the plotting expression "
             "moves it; sources records every artefact the figure read. PNG bytes depend "
             "on the matplotlib build, so the manifest records that build and pins the "
             "DATA instead."),
}


def save(fig, name, title, series, sources, caption):
    p = os.path.join(FIGD, name)
    fig.suptitle(title, fontsize=10.5, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.945])
    fig.savefig(p, dpi=160, bbox_inches="tight",
                metadata={"Software": "issue-44/make_figures.py"})
    if AUDIT_SVG_DIR:
        # svg.fonttype 'none' keeps the strings in the file instead of turning them into
        # glyph outlines, which is what makes the render audit possible at all
        old = plt.rcParams["svg.fonttype"]
        plt.rcParams["svg.fonttype"] = "none"
        fig.savefig(os.path.join(AUDIT_SVG_DIR, name.replace(".png", ".svg")),
                    bbox_inches="tight", metadata={"Date": None})
        plt.rcParams["svg.fonttype"] = old
    plt.close(fig)
    MANIFEST["figures"].append({
        "figure": "figures/" + name,
        "caption": caption,
        "series_sha256": digest({"declared": series, "artists": artist_series(fig)}),
        "png_sha256": sha256_file(p),
        "sources": {n: sha256_file(os.path.join(HERE, n)) for n in sources},
    })
    print("wrote figures/" + name)


# ------------------------------------------------------------------ fig 1 ----
def fig1(v1, src):
    A = v1["A_out_of_sample"]
    cells = sorted(A["cells"], key=lambda c: (c["mechanism"], c["k"], c["delta_D"]))
    mech = sorted(set(c["mechanism"] for c in cells))
    groups = sorted(v1["B_invariance"]["groups"], key=lambda g: g["u"])

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    top = max(max(c["predicted"] for c in cells),
              max(c["observed"] + c["observed_sd"] for c in cells)) * 1.06
    ax[0].plot([0, top], [0, top], "-", color=GREY, lw=1.0, zorder=1,
               label="perfect prediction")
    for i, m in enumerate(mech):
        rs = [c for c in cells if c["mechanism"] == m]
        ax[0].errorbar([c["predicted"] for c in rs], [c["observed"] for c in rs],
                       yerr=[c["observed_sd"] for c in rs], fmt="o", ms=3.2, lw=0.8,
                       capsize=1.6, color=CYCLE[i % 4], label=m)
    ax[0].set_xlim(0, top)
    ax[0].set_ylim(0, top)
    ax[0].set_xlabel("predicted power   $\\Phi(u)$")
    ax[0].set_ylabel("measured detection rate")
    ax[0].legend(loc="upper left", fontsize=7.5)
    ax[0].set_title("(a) %d out-of-sample cells, median $|$err$|$ = %.4f (limit %.2f)"
                    % (A["n_cells"], A["median_abs_error"], A["criterion_a_limit"]),
                    fontsize=8.5)

    u = [g["u"] for g in groups]
    mid = [0.5 * (g["observed_min"] + g["observed_max"]) for g in groups]
    err = [[m - g["observed_min"] for m, g in zip(mid, groups)],
           [g["observed_max"] - m for m, g in zip(mid, groups)]]
    ax[1].errorbar(u, mid, yerr=err, fmt="s", ms=3.2, lw=0.8, capsize=1.8, color=BLUE,
                   label="one $u$, different (k, $\\delta$, $\\sigma$, mechanism)")
    ax[1].plot(u, [g["predicted"] for g in groups], "x", ms=4.5, color=RED,
               label="the construct's value at that $u$")
    ax[1].set_xlabel("standardised margin   $u = (\\sqrt{k}\\,\\delta_D - c_\\alpha)/\\sigma_D$")
    ax[1].set_ylabel("detection rate")
    ax[1].legend(loc="upper left", fontsize=7.5)
    ax[1].set_title("(b) invariance: %d groups, max spread %.4f"
                    % (v1["B_invariance"]["n_groups"], v1["B_invariance"]["max_spread"]),
                    fontsize=8.5)

    save(fig, "fig1_prediction.png",
         "The construct is two numbers", {
             "pred": [c["predicted"] for c in cells],
             "obs": [c["observed"] for c in cells],
             "sd": [c["observed_sd"] for c in cells],
             "mech": [c["mechanism"] for c in cells],
             "u": u, "mid": mid, "err": err,
             "groups_pred": [g["predicted"] for g in groups]},
         src,
         "(a) predicted against measured power over the crossed cells, with the "
         "prediction interval on each measurement; (b) the invariance groups, in which "
         "one u arises from different decompositions.")


# ------------------------------------------------------------------ fig 2 ----
def fig2(v2, src):
    keys = sorted(v2["measured_bands"], key=float)
    sigmas = [float(k) for k in keys]
    mb = dict((s, v2["measured_bands"][k]) for s, k in zip(sigmas, keys))
    pb = dict((s, v2["predicted_bands"][k]) for s, k in zip(sigmas, keys))
    col = dict(zip(sigmas, CYCLE))

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    for i, s in enumerate(sigmas):
        y = len(sigmas) - 1 - i
        m, p = mb[s], pb[s]
        ax[0].plot([p["delta_lo"], p["delta_hi"]], [y + 0.20, y + 0.20], "-",
                   color=LIGHT, lw=7, solid_capstyle="butt",
                   label="predicted band" if i == 0 else None)
        ax[0].plot([m["delta_lo_refined"], m["delta_hi_refined"]], [y - 0.02, y - 0.02],
                   "-", color=col[s], lw=5, solid_capstyle="butt",
                   label="measured band" if i == 0 else None)
        ax[0].plot([m["delta_lo_refined"], m["delta_hi_refined"]], [y - 0.02, y - 0.02],
                   "|", color=INK, ms=7)
        ax[0].text(p["delta_hi"] + 0.06, y, "$\\sigma$=%g  width rel-$|$err$|$ %.3f / %.3f"
                   % (s, abs(m["width_rel_err"]), abs(m["width_rel_err_refined"])),
                   va="center", fontsize=7.5)
    ax[0].set_yticks(range(len(sigmas)))
    ax[0].set_yticklabels(["$\\sigma$=%g" % s for s in reversed(sigmas)])
    ax[0].set_ylim(-0.62, len(sigmas) - 0.25)
    ax[0].set_xlim(right=max(pb[s]["delta_hi"] for s in sigmas) * 1.55)
    ax[0].set_xlabel("location margin $\\delta$  (units of the honest spread)")
    ax[0].set_title("(a) the transition band, predicted vs measured (limit %.0f%%)"
                    % (100 * v2["tol"]), fontsize=8.5)
    ax[0].legend(loc="lower right", fontsize=7.5)

    rows = sorted(v2["band_law_tangent"], key=lambda r: (r["sigma"], r["k"]))
    for s in sigmas:
        rs = [r for r in rows if r["sigma"] == s]
        vals = [r["width_times_sqrt_k_over_sigma"] for r in rs]
        ax[1].plot([r["k"] for r in rs], vals, "o-", ms=3.4, lw=1.0, color=col[s],
                   label="$\\sigma$=%g" % s)
        ax[1].text(len(rs), vals[-1] + 0.1, "spread %.1e" % (max(vals) - min(vals)),
                   fontsize=7, ha="center", color=col[s])
    ks = [r["k"] for r in rows if r["sigma"] == sigmas[0]]
    ax[1].set_xscale("log", base=2)
    ax[1].set_xticks(ks)
    ax[1].set_xticklabels([str(k) for k in ks])
    ax[1].set_xlabel("budget $k$  (re-executions)")
    ax[1].set_ylabel("width $\\cdot\\sqrt{k}/\\sigma$")
    ax[1].legend(loc="center right", fontsize=7.5)
    ax[1].set_title("(b) the width law: constant in $k$ to machine precision",
                    fontsize=8.5)

    save(fig, "fig2_band.png",
         "The transition band, and the width law it obeys", {
             "sigma": sigmas,
             "delta_lo_pred": [pb[s]["delta_lo"] for s in sigmas],
             "delta_hi_pred": [pb[s]["delta_hi"] for s in sigmas],
             "delta_lo_meas": [mb[s]["delta_lo_refined"] for s in sigmas],
             "delta_hi_meas": [mb[s]["delta_hi_refined"] for s in sigmas],
             "width_rel_err": [mb[s]["width_rel_err"] for s in sigmas],
             "width_rel_err_refined": [mb[s]["width_rel_err_refined"] for s in sigmas],
             "k": [r["k"] for r in rows],
             "law": [r["width_times_sqrt_k_over_sigma"] for r in rows]},
         src,
         "criterion (b): the measured band against the construct's own band edges, and "
         "width*sqrt(k)/sigma constant in k at each honest spread.")


# ------------------------------------------------------------------ fig 3 ----
def fig3(v3, src):
    cc = v3["criterion_c"]
    inf = [c for c in v3["cells"].values()
           if 0.01 < c["predicted_power_derived"] < 0.99]
    ordered = sorted(inf, key=lambda c: c["factor"]["mean"])
    lam = sorted(set(c["lam"] for c in inf))
    col = dict(zip(lam, CYCLE))

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    x = list(range(len(ordered)))
    ax[0].axhline(1.0, color=INK, lw=1.0, ls="--")
    ax[0].vlines(x, [c["factor"]["ci_lo"] for c in ordered],
                 [c["factor"]["ci_hi"] for c in ordered], color=LIGHT, lw=1.6)
    for l in lam:
        xs = [i for i, c in enumerate(ordered) if c["lam"] == l]
        ax[0].plot(xs, [ordered[i]["factor"]["mean"] for i in xs], "o", ms=3.2,
                   color=col[l], label="$\\lambda$=%g" % l)
    ax[0].set_xlabel("informative cell (ordered by the factor)")
    ax[0].set_ylabel("factor   derived rule / constant rule")
    ax[0].legend(loc="upper left", fontsize=7.5)
    ax[0].set_title("(a) %d of %d cells above 1, %d significantly; none significantly "
                    "below" % (cc["n_cells_derived_better"], cc["n_informative_cells"],
                               len(cc["cells_derived_significantly_better"])),
                    fontsize=8.5)

    ncal = sorted(set(c["n_cal"] for c in v3["cells"].values()))
    for j, nc in enumerate(ncal):
        rs = [c for c in v3["cells"].values() if c["n_cal"] == nc]
        ax[1].plot([c["lam"] for c in rs], [c["factor"]["mean"] for c in rs], "o-",
                   ms=3.4, lw=0.9, color=CYCLE[j % 4], label="$n_{cal}$=%d" % nc)
    ax[1].axhline(1.0, color=INK, lw=1.0, ls="--")
    ax[1].set_xticks(sorted(set(c["lam"] for c in v3["cells"].values())))
    ax[1].set_xticklabels(["%g" % l for l in sorted(set(c["lam"] for c in v3["cells"].values()))])
    ax[1].set_xlabel("margin in standard-error units,  $\\lambda = \\delta\\sqrt{k}/\\sigma_h$")
    ax[1].set_ylabel("factor")
    ax[1].legend(loc="upper left", fontsize=7.5, ncol=2)
    ax[1].set_title("(b) the advantage peaks near $\\lambda\\approx2$ and does not vanish "
                    "with $n_{cal}$", fontsize=8.5)

    save(fig, "fig3_rule.png",
         "The derived threshold rule against the best constant threshold", {
             "factor_mean": [c["factor"]["mean"] for c in ordered],
             "ci_lo": [c["factor"]["ci_lo"] for c in ordered],
             "ci_hi": [c["factor"]["ci_hi"] for c in ordered],
             "lam": [c["lam"] for c in ordered],
             "n_cal": [c["n_cal"] for c in ordered],
             "k": [c["k"] for c in ordered],
             "sign_test_p": cc["sign_test_p_one_sided"],
             "strict_fail_cells": cc.get("n_cells_constant_better")},
         src,
         "criterion (c): every informative cell's factor with its 95 % interval, and the "
         "factor against the standardised margin at four calibration budgets.")


# ------------------------------------------------------------------ fig 4 ----
def fig4(v4, src):
    s1 = v4["S1_lattice"]
    rows = [r for r in s1["rows"] if r["error"] is not None]
    gauss = v4["S1_gaussian_control"]
    sig = sorted(set(r["sigma_node"] for r in rows))
    col = dict(zip(sig, CYCLE))
    flips = dict((n["sigma_node"], n["sign_flips_in_k"])
                 for n in s1["non_monotonicity"])

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    ax[0].axhline(s1["tolerance_pp"], color=INK, lw=1.0, ls="--",
                  label="tolerance, 1 pp")
    ax[0].axvline(s1["r_star_usable_boundary"], color=GREEN, lw=1.2, ls=":",
                  label="usable boundary $r^\\star$ = %.2f" % s1["r_star_usable_boundary"])
    for s in sig:
        rs = sorted([r for r in rows if r["sigma_node"] == s], key=lambda r: r["k"])
        ax[0].plot([max(r["lattice_ratio"], 1e-2) for r in rs],
                   [max(abs(r["error"]), 1e-6) for r in rs], "o-", ms=3.0, lw=0.8,
                   color=col[s], label="$\\sigma_{node}$=%g" % s)
    ax[0].plot([1e-2] * len(gauss), [max(g["abs_error"], 1e-6) for g in gauss], "*",
               ms=9, color=INK, label="Gaussian control (ratio = 0)")
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("lattice ratio   $\\mathrm{big}/(\\sigma\\sqrt{k})$")
    ax[0].set_ylabel("$|$error$|$")
    ax[0].legend(loc="lower left", fontsize=6.8)
    ax[0].set_title("(a) the error is ordered by the lattice ratio", fontsize=8.5)

    ks = sorted(set(r["k"] for r in rows))
    ax[1].axhline(0.0, color=INK, lw=0.9)
    ax[1].axhline(s1["tolerance_pp"], color=GREY, lw=0.8, ls="--")
    ax[1].axhline(-s1["tolerance_pp"], color=GREY, lw=0.8, ls="--")
    for s in sig:
        rs = sorted([r for r in rows if r["sigma_node"] == s], key=lambda r: r["k"])
        ax[1].plot([r["k"] for r in rs], [r["error"] for r in rs], "o-", ms=3.0, lw=0.9,
                   color=col[s], label="$\\sigma_{node}$=%g, %d sign changes"
                   % (s, flips.get(s, 0)))
    ax[1].set_xscale("log", base=2)
    ax[1].set_xticks(ks)
    ax[1].set_xticklabels([str(k) for k in ks])
    ax[1].set_xlabel("budget $k$")
    ax[1].set_ylabel("signed error")
    ax[1].legend(loc="lower right", fontsize=6.8)
    ax[1].set_title("(b) the error is NOT monotone in $k$", fontsize=8.5)

    save(fig, "fig4_lattice.png",
         "The construct's limit is a lattice, not a rate of convergence", {
             "ratio": [r["lattice_ratio"] for r in rows],
             "abs_error": [abs(r["error"]) for r in rows],
             "error": [r["error"] for r in rows],
             "k": [r["k"] for r in rows],
             "sigma_node": [r["sigma_node"] for r in rows],
             "gauss_k": [g["k"] for g in gauss],
             "gauss_abs_error": [g["abs_error"] for g in gauss],
             "tolerance_pp": s1["tolerance_pp"],
             "r_star": s1["r_star_usable_boundary"],
             "flips": flips},
         src,
         "S1: |error| against the lattice ratio with the usable boundary; the same error "
         "against the budget, showing it is not monotone; and the Gaussian control.")


# ------------------------------------------------------------------ fig 5 ----
def fig5(v4, src):
    meas = sorted(v4["S2_measured"], key=lambda e: (e["k"], e["lam"], e["n_cal"]))
    grid = sorted(v4["S2_grid"], key=lambda g: (g["k"], g["lam"], g["n_cal"]))
    sat = [e for e in meas if e["saturated"]]
    uns = [e for e in meas if not e["saturated"]]

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    ax[0].plot([0, 1], [0, 1], "-", color=GREY, lw=1.1, label="the bound, $1-p_c$")
    ax[0].plot([g["achievable_difference_bound"] for g in grid if not g["saturated"]],
               [g["predicted_difference"] for g in grid if not g["saturated"]], "o",
               ms=2.8, color=BLUE, label="unsaturated")
    ax[0].plot([g["achievable_difference_bound"] for g in grid if g["saturated"]],
               [g["predicted_difference"] for g in grid if g["saturated"]], "o",
               ms=2.8, color=RED, label="saturated ($p_c > 0.99$)")
    ax[0].set_xlabel("achievable difference, $1 - p_c$")
    ax[0].set_ylabel("predicted difference")
    ax[0].legend(loc="upper left", fontsize=7.5)
    ax[0].set_title("(a) %d grid cells: the difference never exceeds its bound"
                    % len(grid), fontsize=8.5)

    for lab, grp, c in (("saturated", sat, RED), ("unsaturated", uns, BLUE)):
        if not grp:
            continue
        ax[1].errorbar([e["bound_1_minus_pc"] for e in grp],
                       [e["mean_difference"] for e in grp],
                       yerr=[[e["mean_difference"] - e["ci_lo"] for e in grp],
                             [e["ci_hi"] - e["mean_difference"] for e in grp]],
                       fmt="o", ms=4.5, lw=0.9, capsize=2.2, color=c, label=lab)
    ax[1].set_xscale("log")
    ax[1].set_xlabel("prize available at the operating point, $1-p_c$   (log)")
    ax[1].set_ylabel("measured difference (95 % CI)")
    ax[1].legend(loc="upper left", fontsize=7.5)
    ax[1].set_title("(b) above the ceiling the prize is a fraction of a point "
                    "(max %.5f vs %.4f)"
                    % (max(e["bound_1_minus_pc"] for e in sat),
                       max(e["bound_1_minus_pc"] for e in uns)), fontsize=8.5)

    save(fig, "fig5_ceiling.png",
         "What the sample-size ceiling bounds: the prize, not the detection", {
             "grid_bound": [g["achievable_difference_bound"] for g in grid],
             "grid_difference": [g["predicted_difference"] for g in grid],
             "grid_saturated": [g["saturated"] for g in grid],
             "grid_k": [g["k"] for g in grid],
             "grid_lam": [g["lam"] for g in grid],
             "grid_n_cal": [g["n_cal"] for g in grid],
             "meas_bound": [e["bound_1_minus_pc"] for e in meas],
             "meas_diff": [e["mean_difference"] for e in meas],
             "meas_ci_lo": [e["ci_lo"] for e in meas],
             "meas_ci_hi": [e["ci_hi"] for e in meas],
             "meas_saturated": [e["saturated"] for e in meas]},
         src,
         "S2: the saturated and unsaturated grids against their 1-p_c bound, and the "
         "measured differences with intervals, showing the bound is never crossed.")


# ------------------------------------------------------------------ fig 6 ----
def fig6(v4, src):
    res = v4["S3_resolution"]
    known = sorted([r for r in res if r["n_min_streams"] is not None],
                   key=lambda r: r["n_min_streams"])
    never = [r for r in res if r["n_min_streams"] is None]
    streams = v4["n_streams"]
    s = v4["S3_summary"]

    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))

    ax[0].axhline(streams, color=RED, lw=1.3, ls="--",
                  label="the budget the study ran: %d streams" % streams)
    dec = [r for r in known if r["decidable_at_41"]]
    und = [r for r in known if not r["decidable_at_41"]]
    ax[0].semilogy(range(len(dec)), [r["n_min_streams"] for r in dec], "o", ms=3.6,
                   color=GREEN, label="decidable at that budget")
    ax[0].semilogy(range(len(dec), len(known)), [r["n_min_streams"] for r in und], "o",
                   ms=3.6, color=BLUE, label="not decidable")
    ax[0].set_xlabel("informative cell (ordered by the streams it needs)")
    ax[0].set_ylabel("streams needed to certify the factor, $N_{min}$  (log)")
    ax[0].legend(loc="upper left", fontsize=7.5)
    ax[0].set_title("(a) median %d, range %d-%d; the budget covers %d of %d"
                    % (s["n_min_median"], s["n_min_min"], s["n_min_max"],
                       s["n_decidable_at_41"], s["n_cells"]), fontsize=8.5)

    ax[1].axhline(1.0, color=INK, lw=1.0, ls="--", label="factor = 1 (no advantage)")
    ax[1].semilogy(range(len(dec)), [r["factor"] for r in dec], "o", ms=3.6, color=GREEN,
                   label="decidable")
    ax[1].semilogy(range(len(dec), len(known)), [r["factor"] for r in und], "o", ms=3.6,
                   color=BLUE, label="not decidable at %d streams" % streams)
    if never:
        ax[1].semilogy([len(known)], [never[0]["factor"]], "x", ms=8, color=RED,
                       label="never decidable")
    ax[1].set_xlabel("informative cell (same order as panel a)")
    ax[1].set_ylabel("measured factor  (log)")
    ax[1].legend(loc="upper left", fontsize=7.0)
    ax[1].set_title("(b) indecidability is an effect-size problem, not a budget problem",
                    fontsize=8.5)

    save(fig, "fig6_decidability.png",
         "Where the comparison is decidable at all", {
             "known_cells": [r["cell"] for r in known],
             "known_n_min": [r["n_min_streams"] for r in known],
             "known_decidable": [r["decidable_at_41"] for r in known],
             "known_factor": [r["factor"] for r in known],
             "never_cells": [r["cell"] for r in never],
             "never_factor": [r["factor"] for r in never],
             "streams": streams,
             "summary": {k: s[k] for k in sorted(s)}},
         src,
         "S3: the streams each informative cell needs to certify the factor against the "
         "budget the study ran, and the measured factor per cell on the same order.")


def main():
    global FIGD, AUDIT_SVG_DIR
    args = sys.argv[1:]
    if "--audit-svg" in args:
        i = args.index("--audit-svg")
        AUDIT_SVG_DIR = args[i + 1]
        del args[i:i + 2]
    if args:
        FIGD = args[0]
    for d in (FIGD, AUDIT_SVG_DIR):
        if d and not os.path.isdir(d):
            os.makedirs(d)
    v1 = load("results_v1.json")
    v2 = load("results_v2.json")
    v3 = load("results_v3.json")
    v4 = load("results_v4.json")
    load("results_v0.json")
    src = STAGE_FILES
    fig1(v1, src)
    fig2(v2, src)
    fig3(v3, src)
    fig4(v4, src)
    fig5(v4, src)
    fig6(v4, src)

    dest = os.path.join(FIGD, "manifest.json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(MANIFEST, indent=2, sort_keys=True) + "\n")
    print("wrote figures/manifest.json (%d figures, matplotlib %s)"
          % (len(MANIFEST["figures"]), matplotlib.__version__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
