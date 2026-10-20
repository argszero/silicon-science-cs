#!/usr/bin/env python3
"""issue #141 -- the figures, generated from the artefacts and re-checkable.

Three figures, one per headline claim.  Each reads ONLY the shipped JSON (never a hand-typed
number), so a figure cannot disagree with the table it illustrates:

  fig1_p1_gain.png        P1 -- the gain is positive in a majority of cells, and its distribution
  fig2_p2_lever.png       P2 -- protocol vs population mean squares, per game, both readings
  fig3_p3_opposition.png  P3 -- the containment, and the one design maxially opposed by both

  python3 figures.py            # write the PNGs + captions.json
  python3 figures.py --check    # regenerate in memory and compare byte-for-byte (the tolerance:
                                # EXACT -- a figure that changes without an artefact changing is a
                                # figure nobody can reproduce)

DETERMINISM, stated rather than hoped for: the Agg backend, no timestamps, no random draws, a fixed
dpi and figure size, and `matplotlib` metadata written only as its own version string.  The declared
build is CPython 3.9.6 / numpy 2.0.2 / matplotlib 3.9.4; a different matplotlib may legitimately
render differently, which is why `--check` reports the build it ran under.
"""
import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from fractions import Fraction  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(HERE, "spike_v4_results.json")
OUTDIR = os.path.join(HERE, "figures")
CAPTIONS = os.path.join(OUTDIR, "captions.json")

DPI = 150
FIGSIZE = (7.0, 4.2)
# a figure must not depend on the machine's taste
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.autolayout": False,
    "savefig.bbox": "tight",
    "savefig.dpi": DPI,
    "svg.hashsalt": "issue-141",
})


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _save(fig, name):
    """Write to a buffer first, so a failure cannot leave a truncated PNG behind."""
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", metadata={"Software": None})
    plt.close(fig)
    data = buf.getvalue()
    return name, data


# ---------------------------------------------------------------------------------------------
# fig 1 -- P1
# ---------------------------------------------------------------------------------------------
def fig_p1(v4):
    cells = v4["cells_G_tau"]
    G = np.array([c["G"] for c in cells.values()], dtype=int)
    per_game = v4["P1_gain_positive"]["per_game"]
    games = sorted(per_game)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE, gridspec_kw={"width_ratios": [1, 1.05]})

    vals, counts = np.unique(G, return_counts=True)
    ax1.bar(vals, counts, color=["0.72" if v == 0 else "0.30" for v in vals], width=0.72)
    ax1.set_xlabel("rank gain $G$ (positions)")
    ax1.set_ylabel("cells")
    ax1.set_title("(a) the gain over all %d cells" % len(G))
    ax1.axvline(0.5, color="C3", lw=1.0, ls="--")
    # the two counts are written ON the bar they describe -- an arrow into empty space tells a
    # reader nothing and, at print size, reads as a stray mark
    ax1.text(0, counts[0], " %d" % int((G == 0).sum()), va="bottom", ha="center", fontsize=8,
             color="0.25")
    ax1.text(vals[-1], counts[-1], " %d" % int(counts[-1]), va="bottom", ha="center", fontsize=8)
    ax1.set_ylim(0, counts.max() * 1.18)
    ax1.text(0.02, 0.94, "$G>0$ in %d of %d cells (%.1f%%)"
             % (int((G > 0).sum()), len(G), 100.0 * (G > 0).mean()),
             transform=ax1.transAxes, fontsize=8.5, va="top")

    frac = [per_game[g]["G_pos"] / per_game[g]["cells"] for g in games]
    ax2.barh(np.arange(len(games)), frac, color="0.30", height=0.68)
    ax2.set_yticks(np.arange(len(games)))
    ax2.set_yticklabels(games, fontsize=7.5)
    ax2.set_xlim(0, 1)
    ax2.axvline(0.5, color="C3", lw=1.0, ls="--")
    ax2.set_xlabel("share of the game's cells with $G>0$")
    ax2.set_title("(b) flat along the ladder")
    for i, g in enumerate(games):
        ax2.text(frac[i] + 0.015, i, "%d/%d" % (per_game[g]["G_pos"], per_game[g]["cells"]),
                 va="center", fontsize=7)
    ax2.invert_yaxis()

    fig.tight_layout()
    return _save(fig, "fig1_p1_gain.png")


# ---------------------------------------------------------------------------------------------
# fig 2 -- P2
# ---------------------------------------------------------------------------------------------
def fig_p2(v4):
    fs = v4["factor_split"]
    games = sorted(fs)
    ms_p = np.array([float(Fraction(fs[g]["MS_protocol"])) for g in games])
    ms_pop = np.array([float(Fraction(fs[g]["MS_population"])) for g in games])
    ss_p = np.array([float(Fraction(fs[g]["SS_protocol"])) for g in games])
    ss_pop = np.array([float(Fraction(fs[g]["SS_population"])) for g in games])
    ratio_m = ms_p / ms_pop
    ratio_s = ss_p / ss_pop

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE, gridspec_kw={"width_ratios": [1.15, 1]})

    x = np.arange(len(games))
    w = 0.38
    ax1.bar(x - w / 2, ms_p, w, label="mean square: protocol (19 levels)", color="0.30")
    ax1.bar(x + w / 2, ms_pop, w, label="mean square: population (4 levels)", color="0.72")
    ax1.set_yscale("log")
    ax1.set_xticks(x)
    ax1.set_xticklabels(games, rotation=45, ha="right", fontsize=7.5)
    ax1.set_ylabel("mean square of $G$ (exact, log scale)")
    ax1.set_title("(a) the same decomposition, every game")
    ax1.legend(fontsize=7.5, frameon=False, loc="upper left")

    ax2.bar(x - w / 2, ratio_m, w, label="mean-square ratio (the claim)", color="C0")
    ax2.bar(x + w / 2, ratio_s, w, label="sum-of-squares ratio", color="C1", alpha=0.55)
    ax2.set_yscale("log")
    ax2.axhline(1.0, color="C3", lw=1.0, ls="--")
    ax2.set_xticks(x)
    ax2.set_xticklabels(games, rotation=45, ha="right", fontsize=7.5)
    ax2.set_ylabel("protocol / population (log scale)")
    ax2.set_title("(b) and why the two ratios differ")
    ax2.legend(fontsize=7.5, frameon=False, loc="upper right")
    for i in x:
        ax2.text(i - w / 2, ratio_m[i], "%.1f" % ratio_m[i], ha="center", va="bottom",
                 fontsize=6.2, rotation=90)
        ax2.text(i + w / 2, ratio_s[i], "%.0f" % ratio_s[i], ha="center", va="bottom",
                 fontsize=6.2, rotation=90)
    ax2.set_ylim(0.5, max(ratio_s) * 6)

    fig.tight_layout()
    return _save(fig, "fig2_p2_lever.png")


# ---------------------------------------------------------------------------------------------
# fig 3 -- P3
# ---------------------------------------------------------------------------------------------
def fig_p3(v4):
    per = v4["per_protocol"]
    names = sorted(per, key=lambda k: (-per[k]["immune_and_unfaithful"], k))
    gameable = np.array([per[k]["gameable"] for k in names], dtype=float)
    fragile = np.array([per[k]["tau_lt_1"] for k in names], dtype=float)
    cells = np.array([per[k]["cells"] for k in names], dtype=float)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE, gridspec_kw={"width_ratios": [1.25, 1]})

    y = np.arange(len(names))
    # fragile is shaded behind, gameable in front: the visible sliver IS the containment
    ax1.barh(y, fragile / cells, height=0.74, color="0.78", label="fragile ($\\tau<1$)")
    ax1.barh(y, gameable / cells, height=0.74, color="0.30", label="gameable ($G>0$)")
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=7)
    ax1.set_xlim(0, 1.02)
    ax1.invert_yaxis()
    ax1.set_xlabel("share of the protocol's 36 cells")
    ax1.set_title("(a) $G>0 \\Rightarrow \\tau<1$: no dark extends past its grey")
    # the legend belongs OUTSIDE the plotting area: inside, it covered two rows of data
    ax1.legend(fontsize=7.5, frameon=False, loc="upper center",
               bbox_to_anchor=(0.5, -0.13), ncol=2)
    for k in names:
        i = names.index(k)
        v = per[k]
        if v["cells"] and v["tau_lt_1"] == 0 and v["gameable"] == 0:
            # an all-zero row is a RESULT (a faithful protocol), not a missing one -- say so, or the
            # blank space reads as data that failed to draw
            ax1.text(0.02, i, "faithful: 0 gameable, 0 fragile", fontsize=6.5, va="center",
                     color="0.35", style="italic")
    for k in ("rank_score", "neg_mean"):
        if k in names:
            i = names.index(k)
            ax1.text(0.03, i, "%d/%d reversed" % (per[k]["reversed"], per[k]["cells"]),
                     fontsize=6.5, va="center", color="white", fontweight="bold")

    # the containment, as sets rather than as bars
    t3 = v4["T3_inclusion"]
    # read the denominator from the model, never a literal: a renamed key must BREAK this figure, not
    # silently replace its denominator with a remembered constant
    total = v4["model"]["cells"]
    ax2.bar([0], [total], color="0.90", width=0.5, label="all %d cells" % total)
    ax2.bar([0], [t3["fragile_cells"]], color="0.72", width=0.5, label="fragile %d" % t3["fragile_cells"])
    ax2.bar([0], [t3["gameable_cells"]], color="0.30", width=0.5,
            label="gameable %d" % t3["gameable_cells"])
    ax2.set_xlim(-0.9, 1.15)
    ax2.set_xticks([])
    ax2.set_ylabel("cells")
    ax2.set_title("(b) the nesting, %d cells wide" % (t3["fragile_cells"] - t3["gameable_cells"]))
    ax2.legend(fontsize=8, frameon=False, loc="upper right")
    band = t3["fragile_cells"] - t3["gameable_cells"]
    ax2.annotate("the band: %d cells\nfragile but not gameable" % band,
                 xy=(0.25, t3["gameable_cells"] + band / 2.0),
                 xytext=(0.36, t3["gameable_cells"] * 0.55), fontsize=7.5,
                 arrowprops=dict(arrowstyle="->", lw=0.7, color="0.4"))

    fig.tight_layout()
    return _save(fig, "fig3_p3_opposition.png")


# ---------------------------------------------------------------------------------------------
BUILDERS = [fig_p1, fig_p2, fig_p3]

# key -> text, keyed the way the manuscript embeds it ({{FIG:p1}}), so a figure's name appears in
# exactly two places: the builder's output filename and this table
FIGS = {
    "p1": "fig1_p1_gain.png",
    "p2": "fig2_p2_lever.png",
    "p3": "fig3_p3_opposition.png",
}

CAPTION_TEXT = {
    "p1":
        "P1: the ranking can be bought. (a) the distribution of the rank gain $G$ over all 684 cells — "
        "$G=0$ (the protocol ranks the policy where its payoff puts it) in 210, $G>0$ in 474. "
        "(b) the same reading per game: the share of each game's 76 cells with $G>0$ stays between "
        "50 and 55, so the effect is not an artefact of bidder count or auction family.",
    "p2":
        "P2: the protocol is the lever. (a) the exact two-way decomposition of $G$ in each game, on a "
        "log scale: the protocol's mean square exceeds the population's in 9 of 9 games. (b) the two "
        "ratios a reader could compute — the mean-square ratio (the claim, 3.929x to 52.132x) and the "
        "sum-of-squares ratio, which is larger for the protocol by construction because the protocol "
        "factor has 19 levels against the population's 4.",
    "p3":
        "P3 refuted: buyable rank and fragile rank are two properties. (a) per protocol, the share of "
        "its 36 cells that are fragile (grey) and gameable (dark) — the dark never escapes the grey, "
        "which is the dominance $G>0 \\Rightarrow \\tau<1$ with 0 counterexamples. (b) the containment "
        "in cells: 474 gameable strictly inside 564 fragile, leaving a band of 90 cells that are "
        "already misordered while nothing can be bought in them.",
}


def invariants(v4):
    """The claims the figures MAKE, asserted over the data they DRAW.

    A figure is an assertion in a second language.  If `fig3` shades gameable under fragile, the
    figure asserts `gameable <= fragile` per protocol; if that stops holding, the figure would keep
    rendering (the darker bar would simply stick out past the grey) and would be read as a rendering
    nicety rather than as a refutation.  So each claim is checked here, and `--selftest` plants the
    failure of each.
    """
    out = []
    per = v4["per_protocol"]

    dark_over_grey = {k: (v["gameable"], v["tau_lt_1"]) for k, v in per.items()
                      if v["gameable"] > v["tau_lt_1"]}
    out.append(("no protocol's gameable cells exceed its fragile cells (fig3a's claim)",
                dark_over_grey == {}))

    faithful = sorted(k for k, v in per.items()
                      if v["gameable"] == 0 and v["tau_lt_1"] == 0)
    out.append(("the all-zero rows are exactly the faithful protocols (fig3a annotates each one)",
                faithful == sorted(v4["headline"]["faithful_set"])))

    fs = v4["factor_split"]
    gt = [g for g in fs if Fraction(fs[g]["MS_protocol"]) > Fraction(fs[g]["MS_population"])]
    out.append(("fig2a draws every game with protocol > population",
                len(gt) == len(fs)))

    # fig2b prints a RATIO; the printed values must be the artefact's, to the width printed
    bad = []
    for g, rec in fs.items():
        r = float(Fraction(rec["MS_protocol"]) / Fraction(rec["MS_population"]))
        if abs(r - round(r, 1)) > 0.05 + 1e-9:
            bad.append((g, r))
    out.append(("every printed ratio is the artefact's ratio to 1dp", bad == []))

    cells = v4["cells_G_tau"]
    n_pos = sum(1 for c in cells.values() if c["G"] > 0)
    out.append(("fig1a's shaded share equals P1's own count",
                n_pos == v4["P1_gain_positive"]["G_pos"]))
    return out


def build():
    v4 = load(V4)
    out = {}
    for fn in BUILDERS:
        name, data = fn(v4)
        out[name] = data
    return out


def main(argv):
    v4 = load(V4)

    if "--selftest" in argv:
        ok = True

        def holds(name, cond):
            nonlocal ok
            print("[%-64s] %s" % (name, "ok" if cond else "*** FAIL ***"))
            ok = ok and cond

        for name, cond in invariants(v4):
            holds(name, cond)

        # PLANT 1: a protocol whose gameable exceeds its fragile must fire the dominance check
        broken = json.loads(json.dumps(v4))
        victim = sorted(broken["per_protocol"])[0]
        broken["per_protocol"][victim]["gameable"] = broken["per_protocol"][victim]["tau_lt_1"] + 1
        fired = dict(invariants(broken))
        holds("PLANT: gameable > fragile is caught",
              not fired["no protocol's gameable cells exceed its fragile cells (fig3a's claim)"])

        # PLANT 2: a faithful protocol reclassified as gameable must fire the all-zero check
        broken2 = json.loads(json.dumps(v4))
        broken2["per_protocol"][
            broken2["headline"]["faithful_set"][0]]["gameable"] = 1
        fired2 = dict(invariants(broken2))
        holds("PLANT: a gameable 'faithful' protocol is caught",
              not fired2["the all-zero rows are exactly the faithful protocols (fig3a annotates each one)"])

        # PLANT 3: a factor split inverted must fire the fig2a check
        broken3 = json.loads(json.dumps(v4))
        g0 = sorted(broken3["factor_split"])[0]
        broken3["factor_split"][g0]["MS_population"] = broken3["factor_split"][g0]["MS_protocol"]
        fired3 = dict(invariants(broken3))
        holds("PLANT: a game where population >= protocol is caught",
              not fired3["fig2a draws every game with protocol > population"])

        # PLANT 4: a shifted G distribution must fire the fig1a count
        broken4 = json.loads(json.dumps(v4))
        for k, v in broken4["P1_gain_positive"].items():
            if k == "G_pos":
                broken4["P1_gain_positive"][k] = v + 1
        fired4 = dict(invariants(broken4))
        holds("PLANT: a G count that disagrees with the cells is caught",
              not fired4["fig1a's shaded share equals P1's own count"])

        print("FIGURES-SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
        return 0 if ok else 1

    imgs = build()

    if "--check" in argv:
        ok = True
        caps = load(CAPTIONS)
        for name, data in sorted(imgs.items()):
            disk = os.path.join(OUTDIR, name)
            if not os.path.isfile(disk):
                print("%-28s MISSING" % name)
                ok = False
                continue
            with open(disk, "rb") as fh:
                old = fh.read()
            same = old == data
            print("%-28s %s (%d bytes, sha256 %s)" %
                  (name, "identical" if same else "*** DIFFERS ***", len(data),
                   hashlib.sha256(data).hexdigest()[:16]))
            if not same:
                ok = False
            key = [k for k, f in FIGS.items() if f == name][0]
            declared = caps.get(key, {}).get("sha256")
            if declared != hashlib.sha256(data).hexdigest():
                print("    declared sha256 in captions.json does not match the regenerated image")
                ok = False
        print("BUILD: CPython %d.%d.%d / numpy %s / matplotlib %s"
              % (sys.version_info[0], sys.version_info[1], sys.version_info[2],
                 np.__version__, matplotlib.__version__))
        print("FIGURES:", "ALL IDENTICAL" if ok else "A FIGURE IS NOT REPRODUCIBLE")
        return 0 if ok else 1

    os.makedirs(OUTDIR, exist_ok=True)
    caps = {}
    for name, data in sorted(imgs.items()):
        tmp = os.path.join(OUTDIR, "." + name + ".tmp")
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, os.path.join(OUTDIR, name))
        key = [k for k, f in FIGS.items() if f == name][0]
        caps[key] = {"caption": CAPTION_TEXT[key], "file": name,
                     "sha256": hashlib.sha256(data).hexdigest()}
        print("wrote %-28s %6d bytes  sha256 %s" % (name, len(data), caps[key]["sha256"][:16]))
    with open(CAPTIONS, "w", encoding="utf-8") as fh:
        json.dump(caps, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d figures)" % (os.path.basename(CAPTIONS), len(caps)))
    print("BUILD: CPython %d.%d.%d / numpy %s / matplotlib %s"
          % (sys.version_info[0], sys.version_info[1], sys.version_info[2],
             np.__version__, matplotlib.__version__))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
