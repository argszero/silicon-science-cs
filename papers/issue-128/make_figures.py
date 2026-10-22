#!/usr/bin/env python3
"""make_figures.py -- issue #128: the three data figures, drawn from the instrument artefacts.

Each figure reads the JSON the instruments wrote (never a retyped number), so a figure cannot drift
from the measurement it illustrates.  Deterministic: no random state, fixed dpi, fixed size -> the PNG
is byte-identical on a re-run.

  fig1_cost_curves.png   the cost above M*: max-sum is a slope, max-min is a step  (P3)
  fig2_free_width.png    the free width by family and on real data                  (P1')
  fig3_alignment.png     the predictor sweep: alignment vs free width               (P2')

Usage: MPLCONFIGDIR=<tmp> python3 make_figures.py
"""
import io, json, os, shutil, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True})


# THE ONE RANK STATISTIC.  Imported, not re-implemented: this file carried the argsort-of-argsort
# variant, which is not a function of the data when M*/k is tied (9 distinct values over 320 cells),
# so the figure printed +0.079 for the statistic the manuscript states as +0.108 (issue #128,
# correction round).
from canonical import spearman


def load(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


# ---------------------------------------------------------------- the certificate
PRINTED = {}          # figure name -> the title text actually drawn


def assert_text_fits(fig, name, texts):
    """Assert every text artist the figure prints lies inside the canvas.

    Measured at the drawing path -- after tight_layout() and after canvas.draw(), at the
    savefig dpi -- because the axes box (not the canvas) is what a centred title is
    centred on, so an rcParams-only reading measures a figure nobody saves.

    This is the check the correction round owed: at the package's own configuration all
    three titles left the right edge of the canvas, and because the PNG is byte-stable a
    byte-identity step could not see it.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    fw = fig.get_size_inches()[0] * fig.dpi
    fh = fig.get_size_inches()[1] * fig.dpi
    for t in texts:
        if not t.get_text().strip():
            continue
        tb = t.get_window_extent(renderer=r)
        assert tb.x0 >= -0.5 and tb.x1 <= fw + 0.5 and tb.y0 >= -0.5 and tb.y1 <= fh + 0.5, (
            "%s: text leaves the canvas: %r  bbox x0=%.1f x1=%.1f on %.1f px (%.1f %% wide)"
            % (name, t.get_text()[:70], tb.x0, tb.x1, fw, 100.0 * tb.width / fw))
    PRINTED[name] = [t.get_text() for t in texts if t.get_text().strip()]


def save(fig, name):
    """tight_layout -> measure -> assert -> save.  Every figure goes through this."""
    fig.tight_layout()
    texts = list(fig.texts) + [ax.title for ax in fig.axes]
    assert_text_fits(fig, name, texts)
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)


def beta_pts(curve, M_star, basev):
    return [(r["M"] - M_star, (basev - r["value"]) / float(basev))
            for r in curve if M_star is not None and r["M"] > M_star
            and r["value"] is not None and r["value"] < basev]


def fig1():
    """P3: the cost above M* -- max-sum is a slope, max-min is a step."""
    v3 = load("spike_v3_results.json")
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for obj, col, mk, lab in (("maxsum", "#1f77b4", "o", "max-sum (sum)"),
                              ("maxmin", "#d62728", "s", "max-min (bottleneck)")):
        sub = [c for c in v3["cases"] if c["obj"] == obj]
        first = True
        for c in sub:
            pts = beta_pts(c["floors_curve"], c["M_star"], c["unconstrained"])
            if len(pts) >= 2:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=col, alpha=0.35,
                        marker=mk, ms=2.5, lw=0.9, label=lab if first else None)
                first = False
    ax.set_xlabel("forced seats above the free threshold  (M - M*)")
    ax.set_ylabel("relative loss  (OPT(0) - OPT(M)) / OPT(0)")
    ax.set_title("Cost above the free region: a sum slopes, a bottleneck steps")
    ax.legend(loc="lower right", frameon=False)
    save(fig, "fig1_cost_curves.png")


def fig2():
    """P1': the free width, by family and on real data."""
    v3 = load("spike_v3_results.json"); v4 = load("spike_v4_results.json")
    fams = {}
    for c in v3["cases"]:
        if c["M_star"] is not None:
            fams.setdefault(c["family"], []).append(c["M_star"] / float(c["k"]))
    order = sorted(fams, key=lambda f: float(np.median(fams[f])))
    labels = order + ["real (Wine Quality)"]
    med = [float(np.median(fams[f])) for f in order]
    A = [c for c in v4["part_a"]["cases"] if c["M_star"] is not None]
    med.append(float(np.median([c["M_star"] / float(c["k"]) for c in A])))
    allw = [c["M_star"] / float(c["k"]) for c in v3["cases"] if c["M_star"] is not None] + \
           [c["M_star"] / float(c["k"]) for c in A]
    free_all = sum(1 for w in allw if w == 1.0)
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.bar(range(len(labels)), med, color="#4c72b0", alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("median free width  M*/k")
    ax.set_ylim(0, 1.05)
    ax.axhline(1.0, color="grey", lw=0.8, ls="--")
    ax.set_title("How much quota is free: median M*/k (%d/%d fully free)" % (free_all, len(allw)))
    save(fig, "fig2_free_width.png")


def fig3():
    """P2': the predictor sweep -- alignment vs free width, with the pooled rank statistic."""
    v5 = load("spike_v5_results.json")
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    xs, ys = [], []
    for cname, blk in v5["corpora"].items():
        cells = [c for c in blk["cells"] if c["free_width"] is not None]
        x = [c["alignment"] for c in cells]; y = [c["free_width"] for c in cells]
        xs += x; ys += y
        ax.scatter(x, y, s=7, alpha=0.45, label=cname)
    # the canonical statistic, computed through the canonical implementation
    rho = spearman(xs, ys)
    ax.set_ylabel("free width  M*/k")
    # 320 cells is stated in §7's table; the title carries the statistic, and the title has to fit
    ax.set_title("The predictor is not there: pooled Spearman = %+.3f" % rho)
    ax.set_xlabel("group-metric alignment  (solve-free predictor, %d cells)" % len(xs))
    ax.legend(loc="upper left", frameon=False, title="corpus")
    save(fig, "fig3_alignment.png")
    return rho, len(xs)


def check_fig3_against_canonical():
    """CROSS-ARTEFACT check (required change 4): the number the FIGURE prints must equal the
    number the MANUSCRIPT states, read from the artefact that owns it.

    Byte-identity cannot see this defect: the PNG is regenerated byte-for-byte from a wrong
    convention, so `reproduce.sh` passes over a figure whose only quantitative claim disagrees
    with the text.  Two independent paths to one number is the only check that can.

    The check RUNS THE DRAWING PATH (so the title-fitting assertion is exercised on the real
    figure) but writes to a SCRATCH directory: `reproduce.sh` step [13] snapshots the three
    PNGs before rebuilding them, and a check that had already rewritten fig3 here would make
    that step compare a rebuilt file against a rebuilt file.  The committed PNG's size and
    mtime are read before and after, so the confinement is itself checked rather than assumed.
    """
    global FIG
    committed = os.path.join(FIG, "fig3_alignment.png")
    before = (os.path.getsize(committed), os.stat(committed).st_mtime_ns) \
        if os.path.exists(committed) else None
    keep = FIG
    scratch = tempfile.mkdtemp(prefix="fig3-check-")
    FIG = scratch
    try:
        rho, n = fig3()
        drew = os.path.getsize(os.path.join(scratch, "fig3_alignment.png"))
    finally:
        FIG = keep
        shutil.rmtree(scratch, ignore_errors=True)
    after = (os.path.getsize(committed), os.stat(committed).st_mtime_ns) \
        if os.path.exists(committed) else None
    if after != before:
        print("FAIL the check wrote into figures/: %r -> %r" % (before, after))
        return 1
    canon = json.load(io.open(os.path.join(HERE, "canonical_results.json"), encoding="utf-8"))
    want = canon["P2_wide"]["pooled_spearman"]
    want_n = canon["P2_wide"]["n_cells"]
    ok = True
    if drew <= 0:
        print("FAIL the check did not draw: the scratch PNG is empty, so nothing was verified")
        ok = False
    else:
        print("drawing path ran; wrote %d B to a scratch dir, figures/ untouched" % drew)
    if n != want_n:
        print("FAIL fig3 cells: figure used %d, canonical_results.json states %d" % (n, want_n))
        ok = False
    # the figure prints 3 decimals; compare at the precision it prints, and say so
    if "%+.3f" % rho != "%+.3f" % want:
        print("FAIL fig3 statistic: figure prints %+.3f, canonical_results.json states %+.3f"
              % (rho, want))
        ok = False
    if not ok:
        return 1
    print("fig3 printed statistic = canonical_results.json P2_wide.pooled_spearman = %+.3f"
          % want)
    return 0


def selftest_title():
    """The plant: a certificate nobody has seen fire is not a certificate.

    Build a figure whose title is deliberately too long and require assert_text_fits to
    raise on it.  A passing run of this selftest is the evidence that the check in `save()`
    can fail at all.
    """
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    ax.plot([0, 1], [0, 1])
    ax.set_title("A deliberately over-long title " + "x" * 160)
    fig.tight_layout()
    texts = list(fig.texts) + [a.title for a in fig.axes]
    fired = False
    try:
        assert_text_fits(fig, "PLANT", texts)
    except AssertionError as e:
        fired = True
        msg = str(e)
    plt.close(fig)
    # and the same check must PASS on a short title, so it is a check and not a constant
    fig2_, ax2 = plt.subplots(figsize=(5.4, 3.3))
    ax2.plot([0, 1], [1, 0])
    ax2.set_title("short enough")
    fig2_.tight_layout()
    passes = True
    try:
        assert_text_fits(fig2_, "CONTROL", list(fig2_.texts) + [a.title for a in fig2_.axes])
    except AssertionError:
        passes = False
    plt.close(fig2_)
    PRINTED.pop("PLANT", None); PRINTED.pop("CONTROL", None)
    good = fired and passes
    print("plant  over-long title -> %s" % ("ASSERTION FIRED" if fired else "NOT CAUGHT"))
    print("       %s" % (msg[:110] if fired else ""))
    print("control short title    -> %s" % ("passes" if passes else "falsely rejected"))
    print("TITLE-CERT: %s" % ("ALL PASS" if good else "FAILED"))
    return 0 if good else 1


if __name__ == "__main__":
    if "--selftest-title" in sys.argv:
        sys.exit(selftest_title())
    if "--check" in sys.argv:
        sys.exit(check_fig3_against_canonical())
    fig1(); fig2(); fig3()
    for f in ("fig1_cost_curves.png", "fig2_free_width.png", "fig3_alignment.png"):
        p = os.path.join(FIG, f)
        print("%-22s %8d B  title=%r" % (f, os.path.getsize(p), PRINTED.get(f, [""])[0][:56]))
