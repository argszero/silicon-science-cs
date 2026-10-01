#!/usr/bin/env python3
"""#93 R428 -- the manuscript's figures, drawn from the instruments rather than typed.

Two panels, and they are the paper's spine:

  (a) the SIGN LAW at the defaults: the gate's net value against binding fidelity `b`, for a channel that merely
      misrepresents and one that launders, with the no-gate baseline at zero.  The negative region is the paper's
      claim -- a gate worth less than no gate -- and the two crossings are the thresholds the text reports.
  (b) the two bars against the COST RATIO R = L/c: the boundary's location is not a property of the fidelity axis
      alone, and the two channels' bars cross at R_c because at that ratio both sit at the axis edge.

Every curve is an instrument call (`gate_v1.value_closed`, `gate_v1.bstar_closed`, `gate_v6.bisect_boundary`), so a
change in the model moves the figure; the numbers the text reports are checked against the same instruments by
`verify_s5.py`.

Run:  python3 figures/make_figures.py            (write the PNGs and print their digests)
      python3 figures/make_figures.py --check    (refuse if the PNG on disk is not what this run produces)
"""
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import matplotlib                                                          # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                            # noqa: E402

import gate_v0 as V0                                                       # noqa: E402
import gate_v1 as V1                                                       # noqa: E402
import gate_v6 as V6                                                       # noqa: E402

FIG1 = os.path.join(HERE, "fig1_sign_law_and_cost_ratio.png")
# A PNG carries a Software tag by default; None keeps the file a function of the data alone, so byte-identity over
# two runs is a real property and not a coincidence of a stable timestamp.
META = {"Software": None, "Creation Time": None, "Source": None}


def save(fig, path):
    fig.savefig(path, dpi=130, metadata=META, bbox_inches="tight")
    plt.close(fig)
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def draw():
    p = dict(V0.DEFAULT)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.3))

    # (a) the sign law
    bs = [i / 200.0 for i in range(201)]
    for ch, colour, label in (("mismatch", "#b2182b", "misrepresents"),
                              ("substitution", "#2166ac", "launders")):
        vs = [V1.value_closed(p, ch, b, 1.0) for b in bs]
        ax1.plot(bs, vs, color=colour, lw=2.0, label="channel %s" % label)
        ax1.plot([1.0], [vs[-1]], "s", color=colour, ms=5)
        bstar = V1.bstar_closed(p, ch)
        if 0.0 <= bstar <= 1.0:
            ax1.plot([bstar], [0.0], "o", color=colour, ms=7)
    ax1.annotate("b* = 0.0800  (misrepresents)", xy=(0.08, 0.0), xytext=(0.115, -0.065),
                 color="#b2182b", fontsize=9, arrowprops=dict(arrowstyle="-", color="#b2182b", lw=0.8))
    ax1.annotate("b* = 0.8559  (launders)", xy=(0.8559, 0.0), xytext=(0.52, 0.105),
                 color="#2166ac", fontsize=9, arrowprops=dict(arrowstyle="-", color="#2166ac", lw=0.8))
    ax1.axhline(0.0, color="0.25", lw=1.2)
    ax1.text(0.015, 0.012, "no gate (baseline)", fontsize=8.5, color="0.25")
    ax1.fill_between(bs, -0.25, 0, color="0.92", zorder=0)
    ax1.text(0.015, -0.238, "gate worth less than no gate", fontsize=8.5, color="0.35")
    ax1.set_xlim(0, 1.02)
    ax1.set_ylim(-0.25, 0.17)
    ax1.set_xlabel("binding fidelity  b")
    ax1.set_ylabel("gate net value  V  (s = 1)")
    ax1.set_title("(a) the sign law at the defaults", fontsize=10.5)
    ax1.legend(fontsize=9, loc="lower right", frameon=False)
    ax1.grid(alpha=0.25, lw=0.5)

    # (b) the two bars against R
    Rs = [5.0 * (1.06 ** i) for i in range(45)]
    for ch, colour, label in (("mismatch", "#b2182b", "misrepresents"),
                              ("substitution", "#2166ac", "launders")):
        xs, ys = [], []
        for R in Rs:
            pr = V6.params_at_R(R)
            bar, _v_lo, _v_hi = V6.bisect_boundary(pr, ch)   # (value, v at 0, v at 1); None = no boundary there
            if bar is not None and 0.0 <= bar <= 1.0:
                xs.append(R)
                ys.append(bar)
        ax2.plot(xs, ys, color=colour, lw=2.0, label="channel %s" % label)
    ax2.axvline(6.875, color="0.4", lw=1.0, ls="--")
    ax2.text(7.1, 0.06, "R_c = 6.875\n(both bars at the axis edge)", fontsize=8.5, color="0.3")
    ax2.axvline(50.0, color="0.4", lw=1.0, ls=":")
    ax2.text(52.0, 0.62, "R = 50\n(the defaults)", fontsize=8.5, color="0.3")
    ax2.set_xscale("log")
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("cost ratio  R = L / c   (log scale)")
    ax2.set_ylabel("binding-fidelity threshold  b*(R)")
    ax2.set_title("(b) the boundary moves with the cost ratio", fontsize=10.5)
    ax2.legend(fontsize=9, loc="upper right", frameon=False)
    ax2.grid(alpha=0.25, lw=0.5)
    return save(fig, FIG1)


def main():
    digest = draw()
    if "--check" in sys.argv:
        if not os.path.exists(FIG1):
            print("NOT RUN -- no %s" % os.path.basename(FIG1))
            return 2
        on_disk = hashlib.sha256(io.open(FIG1, "rb").read()).hexdigest()
        if on_disk != digest:
            print("STALE -- %s differs from what this run draws" % os.path.basename(FIG1))
            print("  on disk %s, drawn %s" % (on_disk[:16], digest[:16]))
            return 1
        print("CURRENT -- %s is byte-identical to a fresh draw (sha256 %s)"
              % (os.path.basename(FIG1), digest[:16]))
        return 0
    print("wrote %s  sha256 %s" % (os.path.relpath(FIG1, ROOT), digest[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
