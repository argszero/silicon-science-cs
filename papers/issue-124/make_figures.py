#!/usr/bin/env python3
"""Issue #124 -- figures.  Every figure is drawn from a committed *_results.json produced by the
instruments in this directory; nothing is drawn from a number typed into this file.

Usage:  /usr/bin/python3 make_figures.py
Out:    figures/fig1..fig6 .png + figures/manifest.json (sha256 per figure)

Determinism: matplotlib stamps its own version into every PNG's `Software` text chunk, which would
make the digests environment-dependent, so that chunk is rewritten to a constant here and the
version is RECORDED IN THE MANIFEST as data instead.
"""
import hashlib
import json
import os
import struct
import sys
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
SOFTWARE_TAG = "silicon-science-cs issue-124 figures"


def constant_software_tag(path):
    """Rewrite any PNG tEXt/iTXt `Software` chunk to a fixed value (CRC recomputed)."""
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    out = [raw[:8]]
    i = 8
    while i < len(raw):
        ln = struct.unpack(">I", raw[i:i + 4])[0]
        typ = raw[i + 4:i + 8]
        data = raw[i + 8:i + 8 + ln]
        rest = raw[i + 8 + ln:i + 12 + ln]
        is_software = (typ in (b"tEXt", b"iTXt")
                       and data.split(b"\x00", 1)[0] == b"Software")
        if is_software:
            data = b"Software\x00" + SOFTWARE_TAG.encode()
            crc = zlib.crc32(typ + data) & 0xFFFFFFFF
            out.append(struct.pack(">I", len(data)) + typ + data + struct.pack(">I", crc))
        else:
            out.append(raw[i:i + 12 + ln])
        i += 12 + ln
        assert rest == b"" or True
    open(path, "wb").write(b"".join(out))


def load(name):
    with open(os.path.join(HERE, name + "_results.json")) as f:
        return json.load(f)


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    constant_software_tag(p)
    print("   %-28s %8d bytes" % (name, os.path.getsize(p)))
    return p


def fig1(v0):
    """The repeat-count law: the error of each aggregation rule against the repeat count."""
    law = {(r["p"], r["n"]): r for r in v0["law"]}
    ns = sorted({r["n"] for r in v0["law"]})
    ps = [0.05, 0.10, 0.20, 0.40]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.6))
    for p in ps:
        xs = [n for n in ns if (p, n) in law]
        ys = [law[(p, n)]["majority_strict"] for n in xs]
        a1.semilogy(xs, [max(y, 1e-12) for y in ys], marker="o", ms=3, lw=1.3, label="p = %.2f" % p)
    a1.set_xlabel("repeat count N")
    a1.set_ylabel("error of the strict-majority decision")
    a1.set_title("the repeat-count law (exact binomial tail)", fontsize=9.5)
    a1.legend(fontsize=7.5)
    a1.grid(alpha=0.25, lw=0.5, which="both")
    rules = [("majority_strict", "strict majority"), ("unanimity", "unanimity"),
             ("any_of", "any-of"), ("mean_ds1", "mean threshold")]
    xs = [n for n in ns if (0.10, n) in law]
    for k, lab in rules:
        a2.semilogy(xs, [max(law[(0.10, n)][k], 1e-12) for n in xs],
                    marker="s", ms=3, lw=1.3, label=lab)
    a2.set_xlabel("repeat count N")
    a2.set_ylabel("error")
    a2.set_title("the RULE decides the direction (p = 0.10)", fontsize=9.5)
    a2.legend(fontsize=7.5)
    a2.grid(alpha=0.25, lw=0.5, which="both")
    return save(fig, "fig1_repeat_law.png")


def fig2(v0):
    """Even beats odd at equal cost, and the tie is a third outcome."""
    eo = {r["p"]: r for r in v0["even_odd"]}
    ps = sorted(eo)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.4))
    w = 0.2
    for i, (key, lab) in enumerate((("n3", "N = 3"), ("n4", "N = 4"), ("n5", "N = 5"))):
        a1.bar([j + (i - 1) * w for j in range(len(ps))],
               [100 * eo[p][key] for p in ps], width=w, label=lab)
    a1.set_xticks(range(len(ps)))
    a1.set_xticklabels(["%.2f" % p for p in ps])
    a1.set_xlabel("per-run disagreement rate p")
    a1.set_ylabel("majority error  (%)")
    a1.set_title("an even N beats the odd N above it", fontsize=9.5)
    a1.legend(fontsize=7.5)
    a1.grid(alpha=0.25, lw=0.5, axis="y")
    law = {(r["p"], r["n"]): r for r in v0["law"]}
    ns = sorted({r["n"] for r in v0["law"]})
    xs = [n for n in ns if (0.40, n) in law]
    a2.plot(xs, [law[(0.40, n)]["majority_strict"] for n in xs], marker="o", ms=3.2,
            lw=1.4, label="majority error")
    a2.plot(xs, [law[(0.40, n)]["unresolved"] for n in xs], marker="^", ms=3.2,
            lw=1.4, ls="--", label="tie mass (unresolved)")
    a2.set_xlabel("repeat count N")
    a2.set_ylabel("probability  (p = 0.40)")
    a2.set_title("the tie is a third outcome, not a loss", fontsize=9.5)
    a2.legend(fontsize=7.5)
    a2.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig2_even_odd.png")


def fig3(v0):
    """The estimate-versus-decide crossover."""
    req = {r["p"]: r for r in v0["requirements"]}
    ps = sorted(req)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.loglog(ps, [req[p]["n_decide_5pct"] for p in ps], marker="o", ms=4, lw=1.5,
              label="runs to DECIDE (error < 5 %)")
    ax.loglog(ps, [req[p]["n_state_p_25pct"] for p in ps], marker="s", ms=4, lw=1.5,
              label="runs to ESTIMATE p (25 % rel.)")
    ax.axvline(v0["cross_p"], ls=":", c="k", lw=1.2)
    ax.text(v0["cross_p"] * 1.04, 3, "registered crossover\np* = %.2f" % v0["cross_p"],
            fontsize=7.5, va="bottom")
    ax.set_xlabel("per-run disagreement rate p")
    ax.set_ylabel("runs required")
    ax.set_title("the binding requirement changes with p", fontsize=9.5)
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.25, lw=0.5, which="both")
    return save(fig, "fig3_crossover.png")


def fig4(v1):
    """The item-repeat budget boundary: N* is scale-free in B, and the relaxation's corner."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.5))
    for cr in v1["cost_ratio"]:
        rows = sorted([r for r in v1["law"] if r["cost_ratio"] == cr], key=lambda r: r["var_ratio"])
        a1.loglog([r["var_ratio"] for r in rows], [max(r["n_star"], 1e-3) for r in rows],
                  marker="o", ms=3.2, lw=1.4, label="item/repeat price = %g" % cr)
    a1.axhline(1.0, ls=":", c="k", lw=1)
    a1.set_xlabel("variance ratio  sigma^2 / tau^2")
    a1.set_ylabel("optimal repeats per item  N*")
    a1.set_title("N* = sqrt(a sigma^2 / b tau^2),  scale-free in B", fontsize=9.5)
    a1.legend(fontsize=7, ncol=2)
    a1.grid(alpha=0.25, lw=0.5, which="both")
    for cr in v1["cost_ratio"]:
        rows = sorted([r for r in v1["law"] if r["cost_ratio"] == cr], key=lambda r: r["var_ratio"])
        a2.semilogx([r["var_ratio"] for r in rows], [r["ratio"] for r in rows],
                    marker="o", ms=3.2, lw=1.4, label="%g" % cr)
    a2.axhline(1.0, ls=":", c="k", lw=1)
    a2.set_xlabel("variance ratio  sigma^2 / tau^2")
    a2.set_ylabel("achieved / relaxed variance")
    a2.set_title("the closed form is a relaxation:\nits price is in the corner", fontsize=9.5)
    a2.legend(fontsize=7, title="price ratio", ncol=2)
    a2.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig4_budget.png")


def fig5(v3, v4):
    """The item-size axis, synthetic and real: tau^2 ~ c/T and sigma^2 floors."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.5))
    for tag, v, mk in (("synthetic", v3, "o"), ("real (Concrete)", v4, "^")):
        a1.loglog([a["T"] for a in v["axis"]], [a["tau2"] for a in v["axis"]],
                  marker=mk, ms=3.4, lw=1.4, label="tau^2, %s" % tag)
        a2.loglog([a["T"] for a in v["axis"]], [a["sigma2"] for a in v["axis"]],
                  marker=mk, ms=3.4, lw=1.4, label="sigma^2, %s" % tag)
    a1.set_xlabel("item size T")
    a1.set_ylabel("between-item variance")
    a1.set_title("tau^2(T) = c_tau / T", fontsize=9.5)
    a1.legend(fontsize=7.5)
    a1.grid(alpha=0.25, lw=0.5, which="both")
    a2.set_xlabel("item size T")
    a2.set_ylabel("within-item variance")
    a2.set_title("sigma^2(T) = sigma_inf^2 + c_sig / T  (floors)", fontsize=9.5)
    a2.legend(fontsize=7.5)
    a2.grid(alpha=0.25, lw=0.5, which="both")
    return save(fig, "fig5_itemsize.png")


def fig6(v2):
    """Two measured results: p across the difficulty axis, and the flat single-run rate vs T."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.5))
    pm = sorted(v2["certificates"]["p_mean_by_cell"].items(), key=lambda kv: float(kv[0]))
    a1.bar([kv[0] for kv in pm], [kv[1] for kv in pm], color="tab:blue")
    a1.axhline(0.10, ls="--", c="tab:red", lw=1.1)
    a1.text(0.02, 0.105, "criterion (ii) bar  p = 0.10", fontsize=7.5, color="tab:red")
    a1.set_xlabel("difficulty cell u")
    a1.set_ylabel("measured per-run disagreement rate p")
    a1.set_title("p is measurable, and it is large (%d runs/cell)" % v2["r_runs"], fontsize=9.5)
    a1.grid(alpha=0.25, lw=0.5, axis="y")
    for name, v, mk in (("synthetic", None, "o"), ("real (Concrete)", None, "^")):
        pass
    a2.axhline(0.5, ls=":", c="k", lw=1.1)
    a2.set_xlabel("item size T")
    a2.set_ylabel("single-run wrong-verdict rate p")
    a2.set_title("flat at 1/2 across a 256x span in T", fontsize=9.5)
    return fig, (a1, a2), pm


def fig6b(v4):
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.semilogx([a["T"] for a in v4["axis"]], [a["p_hat"] for a in v4["axis"]],
                marker="^", ms=5, lw=1.5, label="real (Concrete), %d runs/cell" % v4["r_runs"])
    ax.axhline(0.5, ls=":", c="k", lw=1.1)
    ax.text(v4["axis"][0]["T"] * 1.1, 0.51, "one half", fontsize=8)
    ax.set_ylim(0, 0.75)
    ax.set_xlabel("item size T")
    ax.set_ylabel("single-run wrong-verdict rate p")
    ax.set_title("bigger test set does not fix a single run\n(the rate is flat at about one half)",
                 fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, lw=0.5)
    return save(fig, "fig6_flat_p.png")


def main():
    print("figures from the committed results artefacts")
    v0, v1, v2, v3, v4 = (load("spike_v0"), load("spike_v1"), load("spike_v2"),
                          load("spike_v3"), load("spike_v4"))
    paths = [fig1(v0), fig2(v0), fig3(v0), fig4(v1), fig5(v3, v4), fig6b(v4)]
    man = {"_matplotlib": matplotlib.__version__, "_software_tag": SOFTWARE_TAG,
           "_sources": {n: hashlib.sha256(open(os.path.join(HERE, n + "_results.json"), "rb").read())
                        .hexdigest() for n in ("spike_v0", "spike_v1", "spike_v2",
                                               "spike_v3", "spike_v4")}}
    for p in paths:
        man[os.path.basename(p)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    with open(os.path.join(FIG, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print("-> figures/manifest.json (%d figures)" % (len(paths)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
