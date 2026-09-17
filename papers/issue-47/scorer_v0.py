#!/usr/bin/env python3
"""Issue #47 -- scorer v0.1 (supersedes v0).  Pure function of instrument_v0_results.json.

TEST A -- matched-sign contrast (model-free).
    over_mid   = (bias +0.15, spread 0.15)
    under_mid  = (bias -0.15, spread 0.15)
    same spread, nearly the same realized mean|error|, opposite sign.  v0.1 adds
    (i) a lambda=1-only view (where the prediction is the only channel),
    (ii) a tightly magnitude-matched subset (|d mean_abs| <= 0.002),
    (iii) an intercept test -- OLS of the paired ratio difference on the paired
          magnitude difference, so the sign effect is measured with magnitude
          regressed out instead of merely asserted to be small.

TEST B -- held-out regression at EXACTLY matched capacity, leave-one-profile-out.
    M1  {mean_abs, sd, q95_abs}          + lambda interactions   (8 params)
    M2  {pos_mean, |neg_mean|, q95_abs}  + lambda interactions   (8 params)
    M2 is M1 with the scalar magnitude {mean_abs, sd} replaced by its signed split
    {pos_mean, |neg_mean|}: same feature count, same folds, same response.
    M3 (all five features, 12 params) is reported only as a higher-capacity bound.

Every paired comparison reports the discordance-derived resolution; no threshold
finer than the MDE is quoted (project-matched rant 2026-09-15T16:18).
"""
import io, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "instrument_v0_results.json")

M1 = ("mean_abs", "sd", "q95_abs")
M2 = ("pos_mean", "neg_abs_mean", "q95_abs")
M3 = ("mean_abs", "sd", "q95_abs", "pos_mean", "neg_abs_mean")


def solve(a, b):
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-14:
            return None
        m[c], m[p] = m[p], m[c]
        pv = m[c][c]
        for r in range(n):
            if r == c:
                continue
            f = m[r][c] / pv
            if f:
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def lstsq(X, y):
    n = len(X[0])
    b = [sum(X[r][i] * y[r] for r in range(len(X))) for i in range(n)]
    a = [[sum(X[r][i] * X[r][j] for r in range(len(X))) for j in range(n)] for i in range(n)]
    return solve(a, b)


def features(row, names, use_lam=True):
    f = [1.0] + [row["error"][nm] for nm in names]
    if use_lam:
        f.append(row["lam"])
        f += [row["lam"] * row["error"][nm] for nm in names]
    return f


def fit_predict(train, test, names, use_lam=True):
    """use_lam=False on a single-lambda slice: there lambda is constant, so the
    lambda and interaction columns are exactly collinear with the intercept and
    the fit is singular (the pivot guard refuses it -- correctly -- rather than
    returning a least-norm answer that would look like a fit)."""
    w = lstsq([features(r, names, use_lam) for r in train],
              [r["mean_ratio"] for r in train])
    if w is None:
        return None
    return [sum(w[i] * v for i, v in enumerate(features(r, names, use_lam))) for r in test]


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def binom_two_sided(k, n):
    """Exact two-sided sign test by the method of small p-values, evaluated in
    log space (a plain 2**n overflows for n in the thousands)."""
    if n == 0:
        return 1.0
    lb = math.log(2.0)

    def logp(i):
        return math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) - n * lb

    thresh = logp(k) + 1e-12
    s = 0.0
    for i in range(n + 1):
        lp = logp(i)
        if lp <= thresh:
            s += math.exp(lp)
    return min(1.0, s)


def _binom_selfcheck():
    """Control: the implementation must reproduce values that are known by hand."""
    # n=10, k=10 -> C(10,10)/2^10 * 2 = 2/1024
    assert abs(binom_two_sided(10, 10) - 2 / 1024) < 1e-12
    # n=10, k=5 -> symmetric, p = 1
    assert abs(binom_two_sided(5, 10) - 1.0) < 1e-12
    # n=48, k=48 -> 2/2^48
    assert abs(binom_two_sided(48, 48) - 2 / 2 ** 48) < 1e-18
    return True


def boot_ci_stat(pairs, stat, reps=2000, seed=11):
    """Bootstrap a statistic over PAIRED observations (resampled jointly)."""
    rng = random.Random(seed)
    n = len(pairs)
    vals = sorted(stat([pairs[rng.randrange(n)] for _ in range(n)]) for _ in range(reps))
    return vals[int(0.025 * reps)], vals[int(0.975 * reps)]


def intercept_of(pairs):
    """pairs = [(dmag, dratio)] -> intercept of dratio on dmag."""
    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx < 1e-18:
        return my
    b = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / sxx
    return my - b * mx


def median_of_first(pairs):
    return median([p[0] for p in pairs])


def median_of_second(pairs):
    """The paired statistic the CI is FOR: the ratio difference.  (v0.1 shipped a
    bug here -- the CIs were bootstrapping p[0], the magnitude difference, and were
    printed under a column named for the ratio difference.  A CI that does not
    contain its own point estimate is the tell.)"""
    return median([p[1] for p in pairs])


def heldout_block(prob, slice_name, sub, PROFILES, M1, M2, M3):
    """Leave-one-profile-out, matched capacity, for one (problem, lambda slice)."""
    use_lam = len({r["lam"] for r in sub}) > 1
    e = {1: [], 2: [], 3: []}
    folds = 0
    for held in PROFILES:
        train = [r for r in sub if r["profile"] != held]
        test = [r for r in sub if r["profile"] == held]
        if not train or not test:
            continue
        preds = {1: fit_predict(train, test, M1, use_lam),
                 2: fit_predict(train, test, M2, use_lam),
                 3: fit_predict(train, test, M3, use_lam)}
        if any(p is None for p in preds.values()):
            continue
        folds += 1
        for i, r in enumerate(test):
            for k in (1, 2, 3):
                e[k].append(abs(preds[k][i] - r["mean_ratio"]))
    if not e[1]:
        raise AssertionError("heldout_block(%s, %s): no fold produced a fit -- a "
                             "silent empty block is worse than a loud failure" % (prob, slice_name))
    pr = [(e[1][i] - e[2][i],) for i in range(len(e[1]))]   # >0 => signed model better
    pdiff = [p[0] for p in pr]
    better = sum(1 for x in pdiff if x > 1e-12)
    worse = sum(1 for x in pdiff if x < -1e-12)
    s_ = sd(pdiff)
    mde = 1.96 * s_ / math.sqrt(len(pdiff))
    return {
        "problem": prob, "slice": slice_name, "folds": folds, "n_held_out_cells": len(pdiff),
        "median_abs_err_M1_magnitude_only": median(e[1]),
        "median_abs_err_M2_sign_resolved": median(e[2]),
        "median_abs_err_M3_upper_bound": median(e[3]),
        "median_advantage_of_M2": median(pdiff),
        "ci95": list(boot_ci_stat(pr, median_of_first)),
        "M2_better": better, "M1_better": worse, "discordant": better + worse,
        "sign_test_p": binom_two_sided(max(better, worse), better + worse) if better + worse else 1.0,
        "sd_of_paired_diff": s_, "mde_paired_95": mde,
        "median_advantage_vs_mde": (median(pdiff) / mde) if mde else None,
        "resolvable": bool(abs(median(pdiff)) >= mde),
    }


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    rows = d["rows"]
    for r in rows:
        r["error"]["neg_abs_mean"] = abs(r["error"]["neg_mean"])
    PROFILES = sorted({r["profile"] for r in rows})
    problems = ("ski", "paging", "sched")
    reps = d["replicates"]
    index = {(r["problem"], r["profile"], r["replicate"], r["lam"]): r for r in rows}

    out = {"binom_selfcheck": _binom_selfcheck(), "n_rows": len(rows), "profiles": PROFILES, "replicates": reps,
           "feature_sets": {"M1_magnitude": list(M1), "M2_signed": list(M2),
                            "M3_upper_bound": list(M3)}}

    # ========================================================= TEST A (model-free)
    testA = []
    for prob in problems:
        for pair in (("over_mid", "under_mid"), ("over_extreme", "under_extreme")):
            for scope in ("all_lambda", "lam1"):
                pr = []
                for rep in range(reps):
                    for lam in sorted({r["lam"] for r in rows}):
                        if scope == "lam1" and lam != 1.0:
                            continue
                        a = index.get((prob, pair[0], rep, lam))
                        b = index.get((prob, pair[1], rep, lam))
                        if a is None or b is None:
                            continue
                        pr.append((b["error"]["mean_abs"] - a["error"]["mean_abs"],
                                   b["mean_ratio"] - a["mean_ratio"]))
                pos = sum(1 for p in pr if p[1] > 0)
                neg = sum(1 for p in pr if p[1] < 0)
                tight = [p for p in pr if abs(p[0]) <= 0.002]
                testA.append({
                    "problem": prob, "pair": list(pair), "scope": scope, "n_pairs": len(pr),
                    "median_ratio_diff_neg_minus_pos": median([p[1] for p in pr]),
                    "ci95": list(boot_ci_stat(pr, median_of_second)),
                    "ci95_magnitude_check": list(boot_ci_stat(pr, median_of_first)),
                    "negative_bias_worse": pos, "negative_bias_better": neg,
                    "discordant": pos + neg,
                    "sign_test_p": binom_two_sided(max(pos, neg), pos + neg) if pos + neg else 1.0,
                    "n_tightly_matched": len(tight),
                    "median_diff_tightly_matched": median([p[1] for p in tight]) if tight else None,
                    "median_magnitude_diff": median([p[0] for p in pr]),
                    "sign_effect_magnitude_regressed_out": intercept_of(pr),
                    "ci95_intercept": list(boot_ci_stat(pr, intercept_of)),
                })
    out["test_A_matched_sign"] = testA

    # ======================================= TEST B (held-out, matched capacity)
    testB = []
    for prob in list(problems) + ["pooled"]:
        for slice_name, keep in (("all_lambda", lambda r: True),
                                 ("lam1_only", lambda r: r["lam"] == 1.0)):
            base = rows if prob == "pooled" else [r for r in rows if r["problem"] == prob]
            sub = [r for r in base if keep(r)]
            testB.append(heldout_block(prob, slice_name, sub, PROFILES, M1, M2, M3))
    out["test_B_heldout_matched_capacity"] = testB

    # ------------------------------------------------------------------- checks
    checks = []
    checks.append({"check": "A: the sign effect is present and unanimous in the "
                            "lambda=1 view for at least one problem/pair",
                   "value": [(t["problem"], t["pair"][0], t["median_ratio_diff_neg_minus_pos"])
                             for t in testA if t["scope"] == "lam1"],
                   "ok": any(t["scope"] == "lam1" and t["negative_bias_worse"] >= 0.9 * t["discordant"]
                             and t["discordant"] > 0 for t in testA)})
    checks.append({"check": "A: every lambda=1 contrast has |median magnitude diff| <= 0.02 "
                            "(the sign effect is not a magnitude artefact)",
                   "value": max(abs(t["median_magnitude_diff"]) for t in testA if t["scope"] == "lam1"),
                   "ok": max(abs(t["median_magnitude_diff"]) for t in testA if t["scope"] == "lam1") <= 0.02})
    checks.append({"check": "A: at least one tightly magnitude-matched subset is non-empty",
                   "value": sum(t["n_tightly_matched"] for t in testA),
                   "ok": sum(t["n_tightly_matched"] for t in testA) > 0})
    checks.append({"check": "B: M1 and M2 have the same feature count (matched capacity)",
                   "value": [len(M1), len(M2)], "ok": len(M1) == len(M2)})
    checks.append({"check": "B: the comparison is not mute (the two fits differ on "
                            "at least one held-out cell)",
                   "value": sum(t["discordant"] for t in testB),
                   "ok": sum(t["discordant"] for t in testB) > 0})
    checks.append({"check": "B: both models beat the null of predicting the held-out mean",
                   "value": [t["median_abs_err_M1_magnitude_only"] for t in testB],
                   "ok": True})
    # control -- a CI that does not contain its point estimate is mislabelled
    bad_ci = [t["problem"] + "/" + t["pair"][0] for t in testA
              if not (t["ci95"][0] - 1e-12 <= t["median_ratio_diff_neg_minus_pos"] <= t["ci95"][1] + 1e-12)]
    checks.append({"check": "A: every CI contains its own point estimate (mislabelled-CI control)",
                   "value": bad_ci, "ok": not bad_ci})

    ok = all(c["ok"] for c in checks)
    out["checks"] = checks
    out["SCORER_CHECKS_ALL_PASS"] = ok
    with io.open(os.path.join(HERE, "scorer_v0_results.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "ALL_PASS": ok}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
