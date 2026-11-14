#!/usr/bin/env python3
"""make_figure.py -- the paper's one figure, drawn from the committed artefacts.

Review item m3: section 9 named "the figures [123]" in a package that carried no figure at all and
imported no plotting library. The repair is to draw one, not to delete the sentence -- so this
program draws the paper's central claim, and two things keep the picture honest.

  * It plots the unit the paper quotes. One point is one (family, budget) configuration, composed by
    `axis.config_means` -- the same function the correlation and its threshold are computed on.
    Plotting the seed-level cells instead would put a finer view and the evidence count on one pair
    of axes and invite a reader to read the picture at a denominator the paper never claims.
  * It writes `figures/plot_data.json` beside the picture: every point as plotted, the r printed in
    each series' legend, and the digest of the image it just produced. `check_claims.py` compares
    that record against the artefacts and the image on disk, so the picture cannot drift from the
    numbers it illustrates, and a picture swapped for another one fails a claim rather than passing
    quietly. A two-run byte comparison cannot see either: it only knows the file is stable.

    python3 make_figure.py              # writes figures/resolution_axis.png + figures/plot_data.json
    python3 make_figure.py --selftest   # demonstrate that the guard refuses a drifted picture
"""
import hashlib
import json
import os
import sys

import axis

PNG = "figures/resolution_axis.png"
DATA = "figures/plot_data.json"

# Okabe-Ito, which stays separable under the common colour-vision deficiencies; three scales, so
# three colours and three marker shapes (shape carries the distinction if colour is lost entirely).
SCALES = [
    ("A", "results/mechanism.json", "20 000 descriptors", "#0072B2", "o"),
    ("M", "results/medium.json", "200 000 descriptors", "#D55E00", "s"),
    ("B", "results/scale.json", "1 000 000 descriptors", "#009E73", "^"),
]


def load(path):
    with open(path) as f:
        return json.load(f)


def plotted_from(art):
    """One record per configuration, in sorted key order -- the unit the paper quotes.

    Rounded only for storage; the guard recomposes from the artefact and compares the same rounding,
    so a rounding rule that changed on one side of the comparison is a difference, not a tolerance.
    """
    keys, xs, ys = axis.config_means(art["cells"])
    return {
        "n_configs": len(keys),
        "r_printed": art["log_log_pearson_configs"],
        "mde_printed": art["mde_pearson_configs"],
        "points": [{"config": "/".join(k), "mean_atoms": round(x, 6), "mean_t": round(y, 6)}
                   for k, x, y in zip(keys, xs, ys)],
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 16), b""):
            h.update(blk)
    return h.hexdigest()


def figure_claim_holds(plot_data, arts):
    """The picture's claim as numeric invariants. Returns [(name, ok, detail)] for the gate.

    Four invariants, each of which can be false on its own:

      1. every scale's plotted points equal the points the artefact's cells compose to;
      2. the r printed in each series' legend is the artefact's configuration-level correlation;
      3. the image on disk is the image this record was written beside (digest);
      4. every scale in the paper is in the figure, and nothing else is.
    """
    out = []
    recorded = plot_data.get("scales", {})
    for label in sorted(arts):
        if label not in recorded:
            out.append(("%s: the scale is in the figure" % label, False,
                        "no series for %s in %s" % (label, DATA)))
    for label in sorted(recorded):
        if label not in arts:
            out.append(("%s: the figure plots a scale the paper has" % label, False,
                        "%s is in %s and in no artefact" % (label, DATA)))
    for label in sorted(set(arts) & set(recorded)):
        want = plotted_from(arts[label])
        got = recorded[label]
        same_points = want["points"] == got.get("points")
        detail = "plotted %d configurations" % len(got.get("points") or [])
        if not same_points:
            w = {p["config"]: p for p in want["points"]}
            g = {p["config"]: p for p in (got.get("points") or [])}
            diff = [k for k in sorted(set(w) | set(g)) if w.get(k) != g.get(k)]
            detail = "%d configuration(s) differ: %s" % (len(diff), ", ".join(diff[:3]))
        out.append(("%s: the plotted points are the artefact's configuration means" % label,
                    same_points, detail))
        out.append(("%s: the r in the legend is the artefact's correlation" % label,
                    got.get("r_printed") == want["r_printed"],
                    "legend %s vs artefact %s" % (got.get("r_printed"), want["r_printed"])))
    img = plot_data.get("figure")
    if img and os.path.exists(img):
        out.append(("the image on disk is the one this record was written beside",
                    sha256(img) == plot_data.get("image_sha256"),
                    "%s %s..." % (img, sha256(img)[:16])))
    else:
        out.append(("the image on disk is the one this record was written beside", False,
                    "%s is absent" % img))
    return out


def draw(arts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({
        "font.size": 8,
        "axes.linewidth": 0.6,
        "svg.hashsalt": "issue158",
        "figure.autolayout": False,
    })
    fig, ax = plt.subplots(figsize=(6.4, 3.9))

    for label, _, human, colour, marker in SCALES:
        keys, xs, ys = axis.config_means(arts[label]["cells"])
        r = arts[label]["log_log_pearson_configs"]
        lx, ly = np.log10(xs), np.log10(ys)
        # The fit is the claim: a straight line in log-log is what a Pearson r on the logs means.
        m, b = np.polyfit(lx, ly, 1)
        grid = np.linspace(lx.min() - 0.06, lx.max() + 0.06, 50)
        ax.plot(10 ** grid, 10 ** (m * grid + b), "-", color=colour, linewidth=0.9, alpha=0.75)
        ax.plot(xs, ys, marker, color=colour, markersize=5.2, markeredgewidth=0.5,
                markeredgecolor="white", linestyle="none",
                label="%s — %d configurations, $r = %s$" % (human, len(keys), ("%.4f" % r)))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("distinct distance values in the near neighbourhood (configuration mean)")
    ax.set_ylabel("boundary tie group\n(configuration mean)")
    ax.grid(True, which="major", linewidth=0.35, alpha=0.35)
    ax.grid(True, which="minor", linewidth=0.2, alpha=0.15)
    leg = ax.legend(frameon=False, loc="lower left", fontsize=7, handletextpad=0.4)
    for t in leg.get_texts():
        t.set_color("0.15")
    fig.tight_layout(pad=0.4)
    os.makedirs("figures", exist_ok=True)
    # `Software: None` because matplotlib otherwise stamps its own version into the PNG's metadata:
    # a version bump in a reader's environment would then rewrite a file whose content is unchanged,
    # and the byte comparison in reproduce.sh would report a drift that is not one.
    fig.savefig(PNG, dpi=220, metadata={"Software": None})
    plt.close(fig)


def main(argv):
    selftest = "--selftest" in argv

    arts = {label: load(path) for label, path, _, _, _ in SCALES}
    if selftest:
        return run_selftest(arts)

    draw(arts)
    data = {"figure": PNG, "image_sha256": sha256(PNG),
            "bytes": os.path.getsize(PNG),
            "axes": {"x": "median_atoms (distinct distance values, configuration mean)",
                     "y": "median_t (boundary tie group, configuration mean)",
                     "scale": "log-log"},
            "unit": "one point per (family, budget) configuration, composed by axis.config_means",
            "excluded": "the two endpoint controls: neither is a quantiser family, so neither is a "
                        "configuration in the correlation this figure draws",
            "scales": {label: dict(plotted_from(arts[label]), label=human)
                       for label, _, human, _, _ in SCALES}}
    with open(DATA, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)

    print("wrote %s (%d bytes, sha256 %s...)" % (PNG, data["bytes"], data["image_sha256"][:16]))
    for label, _, human, _, _ in SCALES:
        s = data["scales"][label]
        xs = [p["mean_atoms"] for p in s["points"]]
        ys = [p["mean_t"] for p in s["points"]]
        print("  %s %-22s %2d configurations, r=%s, atoms %.1f-%.1f, tie group %.1f-%.1f"
              % (label, human, s["n_configs"], s["r_printed"], min(xs), max(xs), min(ys), max(ys)))
    print("wrote %s" % DATA)
    return 0


def run_selftest(arts):
    """A guard nobody has seen refuse is not a guard.

    The plants are the three ways this picture can lie while the build stays green: a point that no
    longer matches its artefact, a legend claiming a correlation the artefact does not hold, and an
    image file that is not the one the record was written beside. Each is refused; the clean record
    passes. This runs the same predicate the real gate uses, not a copy of it.
    """
    import copy
    fails = 0

    good = {"figure": PNG, "image_sha256": sha256(PNG) if os.path.exists(PNG) else "x" * 64,
            "scales": {label: plotted_from(arts[label]) for label, _, _, _, _ in SCALES}}

    def expect(name, verdicts, want_ok, want_in):
        nonlocal fails
        ok_all = all(v[1] for v in verdicts)
        named = any(want_in in v[0] and v[1] == want_ok for v in verdicts)
        passed = (ok_all == want_ok) and named
        if want_ok is False:
            fired = [v for v in verdicts if not v[1]]
            passed = bool(fired) and named
        print("  [%s] %s%s" % ("ok" if passed else "FAIL", name,
                               "" if passed else "  -- got %s" % [(v[0], v[1]) for v in verdicts
                                                                  if v[1] != want_ok][:2]))
        if not passed:
            fails += 1

    # clean: every invariant holds
    expect("a record that matches its artefacts passes",
           figure_claim_holds(good, arts), True, "configuration means")
    if not os.path.exists(PNG):
        print("  note: %s is absent, so the digest invariant is exercised by the plants only" % PNG)

    # plant 1: one configuration's tie group moved
    bad = copy.deepcopy(good)
    first = sorted(bad["scales"])[0]
    bad["scales"][first]["points"][0]["mean_t"] += 0.5
    expect("a plotted point that moved is refused",
           figure_claim_holds(bad, arts), False, "%s: the plotted points" % first)

    # plant 2: the legend claims a correlation the artefact does not hold
    bad = copy.deepcopy(good)
    bad["scales"][first]["r_printed"] = -0.5
    expect("a legend r that no artefact holds is refused",
           figure_claim_holds(bad, arts), False, "%s: the r in the legend" % first)

    # plant 3: the image is not the one this record was written beside
    bad = copy.deepcopy(good)
    bad["image_sha256"] = "0" * 64
    expect("an image that is not the recorded one is refused",
           figure_claim_holds(bad, arts), False, "the image on disk")

    # plant 4: a scale the paper reports is missing from the picture
    bad = copy.deepcopy(good)
    dropped = sorted(bad["scales"])[0]
    del bad["scales"][dropped]
    expect("a scale missing from the figure is refused",
           figure_claim_holds(bad, arts), False, "%s: the scale is in the figure" % dropped)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
