#!/usr/bin/env python3
"""analyse_v5.py -- issue #128, R558: is the free width M*/k predicted by ANYTHING cheap?

R557 refuted the geometric proxy (group-metric alignment).  The remaining hope was a statistic of the
UNCONSTRAINED instance -- cheap, because the unconstrained problem is far easier than the whole quota
curve.  On the 320-cell wide sweep the best-looking candidate is the number of unconstrained optima,
`n_optima`, whose log correlates +0.435 with M*/k.

This reader tests that claim the only way it can be tested: it SPLITS BY THE STRATIFICATION the
correlation could be riding on.  The sweep pools two objectives (max-min, max-sum) whose optima have
different multiplicity structure; a statistic that separates the STRATA rather than predicting WITHIN
them is not a predictor, it is a proxy for the stratum label.  The certificate builds exactly such a
pooled object, and a genuine within-stratum object, and requires the detector to tell them apart.

Usage:
  python3 analyse_v5.py              read spike_v5_results.json and report
  python3 analyse_v5.py --selftest   certificates on a healthy AND a mutated object
"""
import io, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "spike_v5_results.json")

STRATUM_KEYS = ("corpus", "obj")          # the split the correlation could be riding on


def load(path=RES):
    d = json.load(io.open(path, encoding="utf-8"))
    return [c for blk in d["corpora"].values() for c in blk["cells"]]


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or len(set(x.tolist())) < 2 or len(set(y.tolist())) < 2:
        return None
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return None if den == 0 else float((rx * ry).sum() / den)


def mae_gain(feat, target):
    """MAE of an affine predictor on `feat` against a constant predictor -- the gain, in MAE units."""
    feat = np.asarray(feat, float); target = np.asarray(target, float)
    const = float(np.abs(np.median(target) - target).mean())
    if len(set(feat.tolist())) < 2:
        return 0.0, const
    lin = float(np.abs(np.polyval(np.polyfit(feat, target, 1), feat) - target).mean())
    return const - lin, const


def features(cell):
    """The cheap candidate predictors a caller could compute without the constrained solve."""
    u = cell["unconstrained"]; g0 = cell["curve"][0]["greedy_value"]
    return {
        "alignment (solve-free)": cell["alignment"],
        "log n_optima": float(np.log1p(cell["base_n_optima"])),
        "greedy gap @M=0": (0.0 if g0 is None else (u - g0) / float(u) if u else 0.0),
        "unconstrained value": float(u),
    }


def assess(cells, name, f):
    """Pooled power vs per-stratum power, plus the degeneracy check.

    A candidate is RELIABLE only if it is non-degenerate in every stratum AND its MAE gain is positive
    in every stratum.  A predictor that is CONSTANT inside one stratum cannot predict there at all;
    such a stratum still contributes points at one corner and can inflate the pooled number.
    """
    ok = [c for c in cells if c["free_width"] is not None]
    X = np.array([f(c) for c in ok]); W = np.array([c["free_width"] for c in ok])
    pooled = spearman(X, W)
    pg, _ = mae_gain(X, W)
    strata = {}
    for key in sorted(set(tuple(c[k] for k in STRATUM_KEYS) for c in ok)):
        sub = [c for c in ok if tuple(c[k] for k in STRATUM_KEYS) == key]
        sx = np.array([f(c) for c in sub]); sw = np.array([c["free_width"] for c in sub])
        g, _ = mae_gain(sx, sw)
        strata["/".join(key)] = {"n": len(sub), "rho": spearman(sx, sw), "mae_gain": g,
                                 "degenerate": spearman(sx, sw) is None}
    best = max((s["rho"] for s in strata.values() if s["rho"] is not None), default=None)
    best_gain = max((s["mae_gain"] for s in strata.values()), default=0.0)
    min_gain = min((s["mae_gain"] for s in strata.values()), default=0.0)
    degenerate = [k for k, s in strata.items() if s["degenerate"]]
    reliable = (not degenerate) and min_gain > 0.005 and pg > 0.005
    return {"name": name, "n": len(ok), "pooled_rho": pooled, "pooled_mae_gain": pg,
            "best_stratum_rho": best, "best_stratum_mae_gain": best_gain,
            "min_stratum_mae_gain": min_gain, "degenerate_strata": degenerate,
            "strata": strata, "reliable": reliable}


def report(cells):
    print("=== R558: is M*/k predicted by anything cheap? (n=%d cells) ===" % len(cells))
    ok = [c for c in cells if c["free_width"] is not None]
    print("cells: %d  unsolved: %d" % (len(cells), len(cells) - len(ok)))
    out = []
    for nm in list(features(ok[0]).keys()):
        f = (lambda nm: (lambda c: features(c)[nm]))(nm)
        r = assess(cells, nm, f)
        out.append(r)
        print("\n-- %s --" % nm)
        print("   pooled rho %s | pooled MAE gain %+.4f | best within-stratum rho %s | min within-stratum MAE gain %+.4f"
              % (("n/a" if r["pooled_rho"] is None else "%+.3f" % r["pooled_rho"]),
                 r["pooled_mae_gain"],
                 ("n/a" if r["best_stratum_rho"] is None else "%+.3f" % r["best_stratum_rho"]),
                 r["min_stratum_mae_gain"]))
        for k, s in r["strata"].items():
            print("     %-14s n=%3d rho %s  mae_gain %+.4f%s"
                  % (k, s["n"], ("n/a" if s["rho"] is None else "%+.3f" % s["rho"]), s["mae_gain"],
                     "  [DEGENERATE: constant within this stratum]" if s["degenerate"] else ""))
        if not r["reliable"]:
            print("   ** NOT RELIABLE: %s%s **" % (
                ("degenerate in " + ",".join(r["degenerate_strata"]) + "; ") if r["degenerate_strata"] else "",
                "or the gain is not positive in every stratum"))
        else:
            print("   RELIABLE: positive gain in every stratum and no degeneracy")
    print("\n== the stratification (why a pooled rho can be unusable) ==")
    for obj in ("maxmin", "maxsum"):
        sub = [c for c in ok if c["obj"] == obj]
        no = [c["base_n_optima"] for c in sub]; w = [c["free_width"] for c in sub]
        print("   %-6s n_optima %d..%d (distinct %d)  median M*/k %.3f"
              % (obj, min(no), max(no), len(set(no)), float(np.median(w))))
    rel = [r["name"] for r in out if r["reliable"]]
    print("\nVERDICT: reliable cheap predictors: %s"
          % (rel if rel else "NONE -- no candidate transports across every stratum"))
    return out


# ------------------------------------------------------------------ certificates
def _strata(specs, n=150, seed=1):
    """Build a pooled dataset from per-stratum specs (mean_feature, mean_target, within_slope, feat_sd)."""
    rng = np.random.RandomState(seed)
    cells = []
    for s, (mf, mt, slope, sd) in enumerate(specs):
        for _ in range(n):
            e = rng.normal()
            cells.append({"free_width": mt + slope * e + 0.15 * rng.normal(),
                          "_gf": mf + sd * e, "corpus": "x", "obj": "s%d" % s})
    return cells


def selftest():
    checks = []

    # C1 a POOLED object with a DEGENERATE stratum must be flagged NOT reliable: the feature is
    # constant inside stratum B, so it cannot predict there, yet the gap between the two strata makes
    # the pooled correlation look strong.
    planted = _strata([(0.0, 0.0, 0.9, 1.0), (5.0, 1.0, 0.0, 0.0)], seed=3)
    r = assess(planted, "planted", lambda c: c["_gf"])
    checks.append(("C1 degenerate stratum flagged not reliable",
                   (not r["reliable"]) and len(r["degenerate_strata"]) == 1 and (r["pooled_rho"] or 0) > 0.5,
                   r["reliable"]))

    # C2 a GENUINE transporting predictor must NOT be flagged: the same slope in both strata, no
    # degeneracy, positive gain everywhere.
    genuine = _strata([(0.0, 0.0, 0.9, 1.0), (0.0, 0.0, 0.9, 1.0)], seed=5)
    r2 = assess(genuine, "genuine", lambda c: c["_gf"])
    checks.append(("C2 transporting predictor is reliable", r2["reliable"], not r2["reliable"]))

    # C3 the real sweep's n_optima must be flagged NOT reliable (the round's finding, asserted)
    real = load()

    def nf(c):
        return float(np.log1p(c["base_n_optima"]))

    rn = assess(real, "log n_optima", nf)
    checks.append(("C3 real n_optima is not reliable",
                   (not rn["reliable"]) and len(rn["degenerate_strata"]) == 2, rn["reliable"]))

    # C4 max-sum optima are unique in every cell (the degeneracy the pooled number rides on)
    ms = [c["base_n_optima"] for c in real if c["obj"] == "maxsum"]
    mn = [c["base_n_optima"] for c in real if c["obj"] == "maxmin"]
    checks.append(("C4 maxsum n_optima==1, maxmin varies",
                   len(set(ms)) == 1 and ms[0] == 1 and len(set(mn)) > 1, len(set(mn)) == 1))

    good = True
    for name, healthy, mutated in checks:
        row = healthy and not mutated
        print("  %-44s healthy=%-5s mutated=%-5s %s" % (name, healthy, mutated, "PASS" if row else "FAIL"))
        good = good and row
    print("selftest:", "ALL PASS" if good else "FAILED")
    return 0 if good else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    report(load())
