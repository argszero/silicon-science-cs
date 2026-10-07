#!/usr/bin/env python3
"""analyse_v3.py -- read spike_v3_results.json and report the registered priors (R555).

Adds the structural predictor R554 lacked: the alignment between the group partition and the
metric, computed from the instance ALONE (no solve), as mean within-group distance over mean
between-group distance.  Every statistic is derived from the artefact; nothing is typed in.

Usage: python3 analyse_v3.py [--selftest]
"""
import io, json, os, sys, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spike_v3 as sv

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "spike_v3_results.json")

def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    def rank(a):
        o = np.argsort(a, kind="mergesort"); r = np.empty(len(a), float); r[o] = np.arange(len(a))
        return r
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    den = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else float("nan")

def within_between(pts, groups, m):
    """Mean within-group pairwise distance / mean between-group pairwise distance. No solve."""
    D = sv.d2_matrix(pts)
    n = len(groups)
    same = groups[:, None] == groups[None, :]
    iu = np.triu_indices(n, 1)
    s = same[iu]; d = D[iu].astype(float)
    w = d[s].mean() if s.any() else 0.0
    b = d[~s].mean() if (~s).any() else 0.0
    return float(w / b) if b else float("nan")

def usable(c):
    return (c["M_star"] is not None
            and all(r["status"] != "UNSOLVED" for r in c["floors_curve"] + c["caps_curve"])
            and all(r["cross_agrees"] is not False for r in c["floors_curve"] + c["caps_curve"])
            and all(r.get("identity_agrees") is not False for r in c["floors_curve"] + c["caps_curve"]))

def features(c):
    n, m, k = c["n"], c["m"], c["k"]
    pts, groups = sv.make_instance(c["family"], c["seed"], n, m)
    D = sv.d2_matrix(pts)
    base_set = c["base_set"] or []
    opt_prof = np.bincount(groups[np.array(base_set)], minlength=m).astype(float) if base_set else np.zeros(m)
    g_set = c["floors_curve"][0]["greedy_set"] or []
    g_prof = np.bincount(groups[np.array(g_set)], minlength=m).astype(float)
    cnt = np.array(c["group_counts"], float)
    return {
        "group_metric_alignment": within_between(pts, groups, m),          # cheap, no solve
        "instance_imbalance": float(cnt.max() / cnt.sum()),                # the naive predictor
        "n_optima": float(c["base_n_optima"]),
        "log_n_optima": float(np.log1p(c["base_n_optima"])),
        "opt_imbalance": float(opt_prof.max() / k),
        "greedy_imbalance": float(g_prof.max() / k),
        "greedy_gap": float(c["unconstrained"] - c["floors_curve"][0]["greedy_value"]) / float(max(1, c["unconstrained"])),
    }

def p1_prime(res):
    out = {}
    for st in ("A", "B"):
        cs = [c for c in res["cases"] if usable(c) and c["setting"] == st]
        fr = np.array([c["M_star"] / float(c["k"]) for c in cs])
        strict = [c for c in cs if c["M_star"] > c["M_first"]]
        out[st] = {"n": len(cs), "strict": len(strict), "median": float(np.median(fr)),
                   "min": float(fr.min()), "max": float(fr.max()),
                   "full": int((fr == 1.0).sum())}
    return out

def by_family(res):
    rows = []
    for fam in sorted(set(c["family"] for c in res["cases"])):
        cs = [c for c in res["cases"] if usable(c) and c["family"] == fam]
        fr = np.array([c["M_star"] / float(c["k"]) for c in cs])
        rows.append((fam, len(cs), float(np.median(fr)), float(fr.min()), float(fr.max())))
    return rows

def p2_prime(res):
    cs = [c for c in res["cases"] if usable(c)]
    y = np.array([c["M_star"] / float(c["k"]) for c in cs])
    F = [features(c) for c in cs]
    fams = np.array([c["family"] for c in cs])
    out = {}
    for nm in sorted(F[0].keys()):
        x = np.array([f[nm] for f in F])
        if not np.all(np.isfinite(x)):
            continue
        err = []
        for fam in sorted(set(fams)):
            tr = fams != fam; te = ~tr
            if tr.sum() < 3 or te.sum() < 1:
                continue
            X = np.vstack([x[tr], np.ones(int(tr.sum()))]).T
            coef, *_ = np.linalg.lstsq(X, y[tr], rcond=None)
            pred = np.vstack([x[te], np.ones(int(te.sum()))]).T @ coef
            err.extend(list(pred - y[te]))
        err = np.array(err)
        out[nm] = {"loo_family_mae": float(np.abs(err).mean()), "n": len(err),
                   "in_sample_spearman": spearman(x, y)}
    return out

def p3(res):
    fits = []
    for c in res["cases"]:
        if not usable(c):
            continue
        base = float(c["unconstrained"]); Ms = c["M_star"]
        pts = [(r["M"] - Ms, (base - r["value"]) / base) for r in c["floors_curve"]
               if r["M"] > Ms and r["value"] is not None and r["value"] < base]
        if len(pts) >= 3:
            X = np.log([p[0] for p in pts]); Y = np.log([p[1] for p in pts])
            fits.append({"setting": c["setting"], "family": c["family"], "obj": c["obj"],
                         "n_points": len(pts), "beta": float(np.polyfit(X, Y, 1)[0])})
    out = {"n_fits": len(fits), "fits": fits}
    for obj in ("maxmin", "maxsum"):
        b = [f["beta"] for f in fits if f["obj"] == obj]
        out[obj] = {"n": len(b), "median_beta": float(np.median(b)) if b else None}
    return out

def p4(res):
    """Does the heuristic pay at a tightness where the exact optimum pays nothing?"""
    rows = []
    for c in res["cases"]:
        if not usable(c):
            continue
        base = c["unconstrained"]
        heur0 = c["floors_curve"][0]["greedy_value"]
        if heur0 is None:
            continue
        pays_first = [r["M"] for r in c["floors_curve"]
                      if r["value"] == base and r["greedy_value"] is not None and r["greedy_value"] < heur0]
        rows.append({"setting": c["setting"], "family": c["family"], "obj": c["obj"],
                     "exact_open": c["M_star"], "heur_open": (min(pays_first) - 1) if pays_first else c["k"],
                     "n_free_for_exact_but_not_heuristic": len(pays_first),
                     "greedy_gap_unconstrained": float(base - heur0) / float(max(1, base))})
    n_any = len([r for r in rows if r["n_free_for_exact_but_not_heuristic"] > 0])
    return {"n": len(rows), "n_cases_heuristic_pays_first": n_any,
            "median_greedy_gap_unconstrained": float(np.median([r["greedy_gap_unconstrained"] for r in rows])) if rows else None,
            "rows": rows}

def main():
    res = json.load(io.open(ART, encoding="utf-8"))
    print("== %s : %d cases, %d cells ==" % (res["instrument"], len(res["cases"]),
          sum(c["n_cells"] for c in res["cases"])))
    print("cross-checked cells:", sum(c["cross_checked_cells"] for c in res["cases"]), "of",
          sum(c["n_cells"] for c in res["cases"]), " declared:", res["settings"]["cross_set"])
    a = p1_prime(res)
    print("\nP1' (M* > M_first; free width M*/k):")
    for st in ("A", "B"):
        v = a[st]
        print("  setting %s: strict %d/%d  median %.3f (%.2f-%.2f)  whole quota free %d/%d"
              % (st, v["strict"], v["n"], v["median"], v["min"], v["max"], v["full"], v["n"]))
    print("\n  by family (median free width):")
    for fam, n, med, lo, hi in by_family(res):
        print("    %-12s n=%2d  median %.3f  (%.2f-%.2f)" % (fam, n, med, lo, hi))
    p2 = p2_prime(res)
    print("\nP2' predictors of M*/k, leave-one-FAMILY-out MAE (lower is better):")
    for nm, v in sorted(p2.items(), key=lambda kv: kv[1]["loo_family_mae"]):
        print("  %-24s loo_mae=%.3f  in_sample_spearman=%+.3f" % (nm, v["loo_family_mae"], v["in_sample_spearman"]))
    t = p3(res)
    print("\nP3 cost law: %d case(s) yield a fit with >=3 points above M*" % t["n_fits"])
    for obj in ("maxmin", "maxsum"):
        print("  %-6s median beta = %s (n=%d)" % (obj, t[obj]["median_beta"], t[obj]["n"]))
    f4 = p4(res)
    print("\nP4 baseline confound: the heuristic pays a quota cost before the optimum does in %d of %d cases"
          % (f4["n_cases_heuristic_pays_first"], f4["n"]))
    print("  median greedy gap on the UNCONSTRAINED instance: %.4f" % f4["median_greedy_gap_unconstrained"])
    return 0

def selftest():
    res = json.load(io.open(ART, encoding="utf-8"))
    def nonincreasing(v):
        return all(v[i] >= v[i + 1] for i in range(len(v) - 1))
    checks = []
    checks.append(("C1 spearman sign", spearman([1, 2, 3, 4], [1, 4, 9, 16]) > 0.99,
                   spearman([1, 2, 3, 4], [16, 9, 4, 1]) > 0.99))
    ok = True
    for c in res["cases"]:
        rows = {r["M"]: r for r in c["floors_curve"]}
        if c["M_star"] is None:
            continue
        ok &= (rows[c["M_star"]]["value"] == c["unconstrained"])
        if c["M_star"] + 1 <= c["k"]:
            ok &= (rows[c["M_star"] + 1]["value"] < c["unconstrained"])
    # the mutation must be built on a case where the seat AFTER M* exists at all: if M* = k the
    # "next seat" is M* itself and the mutation is vacuous (this defect was caught by the test)
    cand = [c for c in res["cases"] if c["M_star"] is not None and c["M_star"] < c["k"]]
    assert cand, "no case with M* < k: the certificate cannot be exercised"
    c2 = cand[0]; r2 = {r["M"]: r for r in c2["floors_curve"]}
    mut = (r2[c2["M_star"] + 1]["value"] == c2["unconstrained"])
    checks.append(("C2 M* is the last free seat", ok, mut))
    fv = [[r["value"] for r in c["floors_curve"] if r["value"] is not None] for c in res["cases"]]
    checks.append(("C3 floors monotone in M", all(nonincreasing(v) for v in fv),
                   not all(nonincreasing(v) for v in fv)))
    # cap_levels() is ASCENDING in c, so the constraint LOOSENS along the curve and the optimum
    # is non-DEcreasing.  (In R554's instrument alpha descended, which flips the direction -- the
    # first version of this check inherited the old direction and failed on a healthy object.)
    def nondecreasing(v):
        return all(v[i] <= v[i + 1] for i in range(len(v) - 1))
    cv = [[r["value"] for r in c["caps_curve"] if r["value"] is not None] for c in res["cases"]]
    checks.append(("C4 caps monotone as c loosens", all(nondecreasing(v) for v in cv),
                   not all(nondecreasing(v) for v in cv)))
    # C5 the structural feature is a real ratio and moves with structure
    cl = [c for c in res["cases"] if c["family"] == "clustered2d"][0]
    un = [c for c in res["cases"] if c["family"] == "uniform2d"][0]
    pts_cl, g_cl = sv.make_instance(cl["family"], cl["seed"], cl["n"], cl["m"])
    pts_un, g_un = sv.make_instance(un["family"], un["seed"], un["n"], un["m"])
    vb_cl = within_between(pts_cl, g_cl, cl["m"]); vb_un = within_between(pts_un, g_un, un["m"])
    checks.append(("C5 structure feature separates families", vb_cl < vb_un, vb_cl >= vb_un))
    good = True
    for name, h, m in checks:
        row = h and not m
        print("  %-38s healthy=%-5s mutated=%-5s %s" % (name, h, m, "PASS" if row else "FAIL"))
        good = good and row
    print("selftest:", "ALL PASS" if good else "FAILED")
    return 0 if good else 1

if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
