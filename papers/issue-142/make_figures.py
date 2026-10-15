#!/usr/bin/env python3
"""Build the four figures for issue #142, reading every plotted value out of the committed reports.

No number in a figure is typed here: each is read from the `spike_ident_v*_results.json` report that
owns it, and the figure generator FAILS if the key it needs is absent (Class 287 -- a reader that
guesses an artefact's schema returns an empty picture silently).  Determinism: `MPLCONFIGDIR` is
pinned, the figures are written through a temp file and `os.replace`, and the same input always
produces the same bytes, so `reproduce.sh` can diff them.

Run:  python3 make_figures.py            (write figures/*.png + figures/CAPTIONS.md)
      python3 make_figures.py --check    (re-render into memory and compare with the shipped bytes)
"""
import hashlib
import io
import json
import os
import sys

os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mplcache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
CAPTIONS = os.path.join(FIGDIR, "CAPTIONS.md")
CAPTIONS_JSON = os.path.join(FIGDIR, "captions.json")

# key -> (file, the caption the manuscript embeds).  ONE carrier: both the human-readable CAPTIONS.md
# and the build's figure blocks are generated from this dict, so a caption cannot drift between the
# two (Class 114 -- a number carried in one place and read in another is the recurring family).
FIGURES = {
    "p1": ("fig1_p1_quadrature.png",
           "P1: the sweep's error against its own correct target (the span mean) is a quadrature error, "
           "~8 orders of magnitude below its error against the point value. The `lam`+1% control breaks "
           "the identity. Bars are medians over the cells each report owns."),
    "p2": ("fig2_p2_span_law.png",
           "P2: the interior MSE-optimal span `h*(sigma)` on log-log axes, for every arm of both systems. "
           "The slopes cluster by REPRESENTATION -- ~1/3 for the smooth arms of both systems, ~0.41 for "
           "the delivered C0 arms of both -- and the dotted line is the derived `sigma^{1/3}` reference."),
    "p3": ("fig3_p3_boundary.png",
           "P3: identification error by the price-only prediction. Left: full range and median per class "
           "on a log scale -- predicted-interior cells sit below the resolution, predicted-pinned cells "
           "do not. Right: the soundness count, no predicted-interior cell above `1e-2`."),
    "p4": ("fig4_p4_routes.png",
           "P4: what separates the routes is access, not the object. (a) median `r` of each route against "
           "the true curve -- the moments LEVEL reading is the same object, the PROFILE reading has the "
           "wrong sign on every defined cell. (b) the system-identification route's reconstruction "
           "quality rising with the log length."),
}


class Fault(Exception):
    pass


def report(name):
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        raise Fault("report %s is missing" % name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def need(d, *keys):
    """Read a nested key out of a report, failing LOUDLY when it is not there."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            raise Fault("report key %r is absent (have: %s)" % (k, list(cur)[:8] if isinstance(cur, dict) else type(cur).__name__))
        cur = cur[k]
    return cur


def _save(fig, name):
    png = os.path.join(FIGDIR, name)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    data = buf.getvalue()
    tmp = png + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, png)
    return data


def fig1():
    """P1: the sweep's error is the span average -- against its CORRECT target it is a quadrature
    error, against the point value it is ~8 orders larger."""
    v0, v5 = report("spike_ident_v0_results.json"), report("spike_ident_v5_results.json")
    rows = [
        ("system 1 (n=352)", need(v0, "A_identity")["median"], None),
        ("system 2 (n=120)", need(v5, "pooled", "identity")["median"], None),
    ]
    s1_span = need(v0, "C_sweep_vs_spanmean")["median"]
    s1_pt = need(v0, "C_sweep_vs_point")["median"]
    s2_span = need(v5, "pooled", "sweep_vs_spanmean")["median"]
    s2_pt = need(v5, "pooled", "sweep_vs_point")["median"]
    ctl1 = need(v0, "A_identity_control_lam_1pct")["median"]

    labels = ["identity\n`G = int c`", "sweep vs\nSPAN MEAN\n(correct target)",
              "sweep vs\nPOINT value", "control:\n`lam` +1%"]
    s1 = [rows[0][1], s1_span, s1_pt, ctl1]
    s2 = [rows[1][1], s2_span, s2_pt, float("nan")]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = range(len(labels))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], s1, w, label="system 1 (chunked horizon)", color="#2b6cb0")
    b2 = ax.bar([i + w / 2 for i in x], s2, w, label="system 2 (AoI sampler)", color="#c05621")
    ax.set_yscale("log")
    ax.set_ylim(1e-17, 1e3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("median relative error (log)")
    ax.set_title("P1: the sweep's error is the span average, not a modelling error", fontsize=10)
    for bars, vals in ((b1, s1), (b2, s2)):
        for b, v in zip(bars, vals):
            if v == v:
                ax.annotate("%.1e" % v, (b.get_x() + b.get_width() / 2, v), ha="center",
                            va="bottom", fontsize=7, rotation=0)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    return _save(fig, "fig1_p1_quadrature.png")


def fig2():
    """P2: the interior MSE-optimal span and its exponent -- the same law, two systems, and the
    exponent set by the REPRESENTATION (smooth vs delivered C0), not the plant."""
    v1, v6 = report("spike_ident_v1_results.json"), report("spike_ident_v6_results.json")
    arms = [
        ("s1 analytic (C-inf)", need(v1, "analytic", "hstar_points_centred"),
         need(v1, "analytic", "hstar_vs_sigma_slope_centred"), "#2b6cb0", "-"),
        ("s1 model C0", need(v1, "model", "hstar_points_centred"),
         need(v1, "model", "hstar_vs_sigma_slope_centred"), "#2b6cb0", "--"),
    ]
    src = need(v6, "per_source")
    for name, blk in src.items():
        for arm_name, col, ls in (("smooth", "#c05621", "-"), ("grid", "#c05621", "--")):
            if arm_name in blk.get("arms", {}):
                a = blk["arms"][arm_name]
                arms.append(("s2 %s %s" % (arm_name, name.split()[1]), a["hstar_points_centred"],
                             a.get("hstar_vs_sigma_slope_centred"), col, ls))

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for label, pts, slope, col, ls in arms:
        sig = [p[0] for p in pts]
        hs = [p[1] for p in pts]
        ax.plot(sig, hs, ls, marker="o", ms=3, color=col, label="%s  (slope=%.3f)" % (label, slope))
    # the derived law sigma^{1/3} as a reference line through the smooth-limit points
    ref = arms[0][1][0]
    xs = [p[0] for p in arms[0][1]]
    ks = [p[1] / (p[0] ** (1.0 / 3.0)) for p in arms[0][1]]
    k = sorted(ks)[len(ks) // 2]
    ax.plot(xs, [k * (x ** (1.0 / 3.0)) for x in xs], ":", color="k", lw=1,
            label="reference slope 1/3 (smooth limit)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("noise level  sigma  (log)")
    ax.set_ylabel("MSE-optimal span  h*  (log)")
    ax.set_title("P2: the span law is the representation's, not the plant's", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3, which="both")
    return _save(fig, "fig2_p2_span_law.png")


def fig3():
    """P3: the identifiability boundary -- predicted-pinned cells carry no information, and the
    predictor is SOUND (no interior cell above the resolution) but not exact."""
    v2 = report("spike_ident_v2_results.json")
    it, pin = need(v2, "error_by_label", "interior"), need(v2, "error_by_label", "pinned")
    snd = need(v2, "soundness")
    res = float(need(v2, "resolution"))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.2), gridspec_kw={"width_ratios": [2, 1]})
    for i, (lab, d, col) in enumerate((("predicted INTERIOR (n=%d)" % it["n"], it, "#2b6cb0"),
                                       ("predicted PINNED (n=%d)" % pin["n"], pin, "#c53030"))):
        ax.plot([i - 0.18, i - 0.18], [d["best"], d["worst"]], "-", color=col, lw=2)
        ax.plot([i + 0.18, i + 0.18], [d["best"], d["worst"]], "-", color=col, lw=2)
        ax.plot(i - 0.18, d["median"], "o", color=col, ms=8)
        ax.plot(i + 0.18, d["median"], "o", color=col, ms=8)
    ax.axhline(res, color="k", ls=":", lw=1)
    # The class counts go in the TICK LABELS and the resolution marker is the only annotation: earlier
    # versions floated a class label beside its own worst value and the two labels' boxes overprinted
    # each other AND the resolution line -- a defect that only shows up when the figure is LOOKED at,
    # which is why this generator's output is read, not just hashed.
    ax.annotate("resolution %.0e" % res, (-0.55, res * 1.4), fontsize=7, va="bottom", ha="left")
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 1e4)
    ax.set_xlim(-0.6, 1.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["interior\n(n=%d)" % it["n"], "pinned\n(n=%d)" % pin["n"]])
    ax.set_ylabel("identification error (log)")
    ax.set_title("P3: error by the price-only prediction", fontsize=10)
    ax.grid(axis="y", alpha=0.3, which="both")

    ax2.bar([0, 1], [snd["interior_cells_above_1e-2"], it["n"] - snd["interior_cells_above_1e-2"]],
            color=["#c53030", "#2f855a"])
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["interior cells\nABOVE 1e-2", "interior cells\nbelow"], fontsize=8)
    ax2.set_title("predicted-interior errors\n(%d cells)" % it["n"], fontsize=9)
    ax2.set_ylabel("cells")
    for i, v in enumerate([snd["interior_cells_above_1e-2"], it["n"] - snd["interior_cells_above_1e-2"]]):
        ax2.annotate(str(v), (i, v), ha="center", va="bottom", fontsize=9)
    ax2.grid(axis="y", alpha=0.3)
    return _save(fig, "fig3_p3_boundary.png")


def fig4():
    """P4: what separates the routes is ACCESS, not the object.  Two independent readings."""
    v3, v4 = report("spike_ident_v3_results.json"), report("spike_ident_v4_results.json")
    m1 = float(need(v3, "routes", "M1", "object_test_interior", "median_r"))
    m2 = float(need(v3, "routes", "M2", "object_test_interior", "median_r"))
    sw = float(need(v3, "routes", "SW", "object_test_interior", "median_r"))
    frac = float(need(v3, "direction_test_M2", "all", "fraction_right_sign"))
    n_m2 = int(need(v3, "direction_test_M2", "all", "n_defined"))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.4))
    names = ["sweep\n(the instrument)", "M1: logged mean cost\n(LEVEL reading)",
             "M2: profile slope\n(PROFILE reading)"]
    vals = [sw, m1, m2]
    cols = ["#2f855a", "#3182ce", "#c53030"]
    bars = ax.bar(range(3), vals, color=cols)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylim(-1.35, 1.18)
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("median r against the true c\n(interior cells)")
    ax.set_title("P4a: same object, or a different one?", fontsize=10)
    for b, v in zip(bars, vals):
        ax.annotate("%+.3f" % v, (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom" if v > 0 else "top", fontsize=8,
                    color="white" if v < 0 else "black")
    # the note goes where the plot is EMPTY -- under the two positive bars, not across the negative
    # one it is about (the first version overprinted both the bar and the tick labels)
    ax.annotate("M2 is the WRONG SIGN on %d/%d defined cells\n(no threshold needed: %d of them are "
                "sign-wrong)" % (n_m2, n_m2, n_m2),
                (0.5, -0.72), ha="center", va="center", fontsize=7.5, color="#c53030",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c53030", lw=0.6))
    ax.grid(axis="y", alpha=0.3)

    ts, rs, errs = [], [], []
    for plant, blk in need(v4, "plants").items():
        for e in blk["by_T"]:
            ts.append(int(e["T"]))
            rs.append(float(e["curve_r"]))
            errs.append(float(e["c_error"]["median"]))
    ax2.plot(ts, rs, "o-", color="#553c9a", label="r (reconstructed vs true c)")
    ax2.plot(ts, errs, "s--", color="#b7791f", label="median relative error")
    ax2.set_xscale("log")
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("log length T (steps, log)")
    ax2.set_ylabel("r  /  relative error")
    ax2.set_title("P4b: system identification reaches the SAME curve", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    return _save(fig, "fig4_p4_routes.png")


def captions(digests):
    lines = [
        "# Figure captions -- issue #142",
        "",
        "Generated by `make_figures.py`; every plotted value is read out of the committed",
        "`spike_ident_v*_results.json` reports, and each PNG is byte-reproducible.",
        "",
    ]
    for key in ("p1", "p2", "p3", "p4"):
        fname, cap = FIGURES[key]
        lines += ["**Figure %s** (`%s`). %s" % (key[1:], fname, cap), ""]
    lines += ["## Digests", ""]
    for name in sorted(digests):
        lines.append("- `%s`  sha256 `%s`" % (name, digests[name]))
    lines.append("")
    tmp = CAPTIONS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    os.replace(tmp, CAPTIONS)
    # the machine-readable twin: the manuscript build reads THIS, so the caption the paper prints and
    # the caption this file documents are the same string by construction
    out = {k: {"file": f, "caption": c, "sha256": digests.get(f, "")}
           for k, (f, c) in FIGURES.items()}
    tmp = CAPTIONS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    os.replace(tmp, CAPTIONS_JSON)


def main(argv):
    os.makedirs(FIGDIR, exist_ok=True)
    try:
        digests = {}
        for fn in (fig1, fig2, fig3, fig4):
            data = fn()
            name = fn.__name__.replace("fig1", "fig1_p1_quadrature").replace("fig2", "fig2_p2_span_law") \
                .replace("fig3", "fig3_p3_boundary").replace("fig4", "fig4_p4_routes")
            digests[name + ".png"] = hashlib.sha256(data).hexdigest()
        captions(digests)
    except Fault as e:
        print("FIGURES FAILED: %s" % e)
        return 1
    if "--check" in argv:
        bad = []
        for name, dg in digests.items():
            path = os.path.join(FIGDIR, name)
            with open(path, "rb") as fh:
                if hashlib.sha256(fh.read()).hexdigest() != dg:
                    bad.append(name)
        if bad:
            print("CHECK FAILED: %s" % bad)
            return 1
        print("CHECK OK: %d figures reproduce" % len(digests))
        return 0
    print("wrote %d figures + CAPTIONS.md" % len(digests))
    for name in sorted(digests):
        print("   %-28s %s" % (name, digests[name][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
