#!/usr/bin/env python3
"""spike_real2 (#126) -- THE WIDE-kappa1 REAL REGIME: a second real case family and the kappa1 exponent.

spike_real (#126, R541) measured the floor on real matrices with ONE case family -- pairs of distinct
real vectors (row.row, col.col) -- and found that family CANNOT reach the regime the law is about: at
fp32 its cases have median kappa1 ~ 1.0, so the fitted exponent beta in E_floor ~ kappa1^beta came out
[0.65, 0.83] over a range that barely leaves 1.  This instrument adds a SECOND real family that does
reach it, and fits beta on both:

  family "pair"   (a, b) = (col_i, col_j)                       -- spike_real's family
  family "cancel" (a, b) = (col_i + col_j, col_i - col_j)       -- a real change of basis; the dot
                  product is |col_i|^2 - |col_j|^2, which cancels when the two columns have similar
                  NORMS while every addend is full width.  This is a property of the real matrix (how
                  many of its column pairs have comparable norm), not a synthetic knob.

Both families are real integer vectors after quantization, so the exact dot product is computable and
the error is measured, not modelled.  The exponent is reported as a RANGE over subsets for EACH family
and for the pooled set (an exponent read off one subset is a number, not a law -- R540/Class 181), and
a REACH certificate asserts the cancel family actually arrives (Class 182: an arm must be shown to
reach the regime before its result means anything).
Output: spike_real2_results.json
Usage:  python3 spike_real2.py [--selftest]
"""
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S     # noqa: E402
import spike_real as R   # noqa: E402  (the pinned corpus, the loader, the quantizer)

MATDIR = R.MATDIR
SEED0 = 20261006
KMAX = 6


# ----------------------------------------------------------------- the two real case families
def pair_cases(A, nr, nc, max_vecs=60, max_pairs=250, seed=SEED0):
    """pairs of distinct real vectors (spike_real's family)."""
    return R.cases_from(A, nr, nc, max_vecs, max_pairs, seed)


def cancel_cases(A, nr, nc, max_vecs=60, max_pairs=250, seed=SEED0 + 991):
    """(col_i + col_j, col_i - col_j): a real cancelling basis, full-width addends."""
    rng = random.Random(seed)
    cols = [[A[i][j] for i in range(nr)] for j in range(min(nc, max_vecs))]
    pairs = [(i, j) for i in range(len(cols)) for j in range(i + 1, len(cols))]
    rng.shuffle(pairs)
    out = []
    for i, j in pairs[:max_pairs]:
        a, b = cols[i], cols[j]
        u = [x + y for x, y in zip(a, b)]
        v = [x - y for x, y in zip(a, b)]
        out.append(("cancel%d.%d" % (i, j), u, v))
    return out


def resolvable(k1, p):
    """Is the RELATIVE error a meaningful accuracy metric for this case?

    kappa1 = ||ab||_1 / |sum ab|.  When kappa1 exceeds 1/u = 2^p the exact sum is SMALLER than the
    rounding unit of the terms, i.e. it cancels below the representable precision of the operands --
    and then |S - exact|/|exact| is not an accuracy, it is an amplification of the operands'
    representation error (measured here at 2.7e6 for one matrix).  Those cases lie OUTSIDE the regime
    the law is about and must be excluded, not fitted: they pinned beta to 1.0 with SE 0.005 before
    this bound existed.
    """
    return k1 <= float(2 ** p)


def floor_and_kappa(a, b, q, p):
    """(kappa1, E_floor) for one real dot product; None if degenerate or unresolvable."""
    ex = S.dot_exact(a, b)
    k1 = S.kappa1(a, b)
    if ex == 0 or k1 == float("inf") or not resolvable(k1, p):
        return None
    E = {K: S.relerr(S.dot_emulated(a, b, q, K, p), ex) for K in range(1, KMAX + 1)}
    ef = min(E[K] for K in range(max(3, KMAX - 3), KMAX + 1))
    return k1, ef


def linfit(xs, ys):
    """ordinary least squares with R2 -- reported so the additive reading carries its own quality."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return float("nan"), float("nan"), float("nan")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    ss, sst = sum(r * r for r in resid), sum((y - my) ** 2 for y in ys)
    return a, b, (1 - ss / sst if sst else float("nan"))


def c_trend(raw, u):
    """the collapse constant c = E_floor/(kappa1*u) binned by kappa1, and the fit c = a/kappa1 + b."""
    edges = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 1e18]
    bins = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        grp = [(k, e / (k * u)) for k, e in raw if lo <= k < hi]
        if len(grp) >= 10:
            bins.append([S.median([k for k, _ in grp]), S.median([c for _, c in grp]), len(grp)])
    fit = [float("nan")] * 3
    if len(bins) >= 4:
        a, b, r2 = linfit([1.0 / k for k, _c, _n in bins], [c for _k, c, _n in bins])
        fit = [a, b, r2]
    return {"bins": bins, "fit_a_over_k1_plus_b": fit}


def band_spread(bymat, lo, hi, u, min_cases=8):
    """Per-matrix medians of c = E_floor/(kappa1*u) inside a FIXED kappa1 band.

    This is the direct test of P2's sharp form: if kappa1 were the single governing scalar, then two
    problems with equal kappa1 would have equal accuracy, so c would be CONSTANT across matrices at
    fixed kappa1.  Whatever spread shows up is the contribution of a variable the scalar misses.
    """
    rows = []
    for name, cases in bymat.items():
        vals = [e / (k * u) for k, e in cases if lo <= k < hi]
        if len(vals) >= min_cases:
            rows.append((name, S.median(vals), len(vals)))
    rows.sort(key=lambda t: t[1])
    ratio = (rows[-1][1] / rows[0][1]) if len(rows) >= 2 and rows[0][1] else None
    return {"n_matrices": len(rows), "matrices": rows,
            "lo": rows[0][1] if rows else None, "hi": rows[-1][1] if rows else None, "ratio": ratio}


def subset_fits(raw):
    """beta of E_floor ~ kappa1^beta over subsets of (kappa1, E_floor) pairs."""
    subsets = [("all", raw),
               ("kappa1>1", [(k, e) for k, e in raw if k > 1.0000001]),
               ("kappa1>=1.5", [(k, e) for k, e in raw if k >= 1.5]),
               ("kappa1>=10", [(k, e) for k, e in raw if k >= 10.0])]
    fits = {}
    for label, sel in subsets:
        ks = [k for k, _ in sel]
        # a zero-variance subset has no slope to fit -- fit_slope_se divides by sum((x-mx)^2), so an
        # unguarded call CRASHES on it (found in this round's selftest, not in the data)
        if len(sel) >= 8 and len(set(ks)) > 1:
            be, se = S.fit_slope_se(ks, [e for _, e in sel])
            fits[label] = {"beta": be, "se": se, "n": len(sel)}
    return fits


def main():
    out = {"seed0": SEED0, "formats": {}}
    FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]

    print("=" * 100)
    print("spike_real2 -- the wide-kappa1 real regime: the cancelling family and the kappa1 exponent")
    print("=" * 100)

    ok, bad = R.verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok

    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]

    for fname, p in FORMATS:
        q, u = p // 2, 2.0 ** -p
        fams = {"pair": [], "cancel": []}          # (kappa1, E_floor)
        bymat = {}                                 # matrix -> [(kappa1, E_floor)]
        n_excluded = {"pair": 0, "cancel": 0}      # cases the resolvability bound removed
        nround, nexact, kmax = {"pair": 0, "cancel": 0}, {"pair": 0, "cancel": 0}, {"pair": 0.0, "cancel": 0.0}
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            for fam, cases in (("pair", pair_cases(A, nr, nc)), ("cancel", cancel_cases(A, nr, nc))):
                for _tag, a, b in cases:
                    r = floor_and_kappa(a, b, q, p)
                    if r is None:
                        ex = S.dot_exact(a, b)
                        k1 = S.kappa1(a, b)
                        if ex != 0 and k1 != float("inf") and not resolvable(k1, p):
                            n_excluded[fam] += 1
                        continue
                    k1, ef = r
                    if ef == 0:
                        nexact[fam] += 1
                        continue
                    nround[fam] += 1
                    fams[fam].append((k1, ef))
                    bymat.setdefault(name, []).append((k1, ef))
                    kmax[fam] = max(kmax[fam], k1)

        blk = {"p": p, "q": q, "u": u, "families": {}, "p_knob": {}}
        print()
        print("--- %s (p=%d q=%d) ---" % (fname, p, q))
        for fam in ("pair", "cancel"):
            raw = fams[fam]
            fits = subset_fits(raw)
            rng_ = [min(k for k, _ in raw), max(k for k, _ in raw)] if raw else None
            rngc = [min(e / (k * u) for k, e in raw), max(e / (k * u) for k, e in raw)] if raw else None
            blk["families"][fam] = {"n_rounding": nround[fam], "n_exact": nexact[fam],
                                    "n_excluded_unresolvable": n_excluded[fam],
                                    "kappa1_range": rng_, "c_range": rngc, "fits": fits}
            print("   %-7s round=%4d exact=%4d excluded(k1>2^p)=%4d  kappa1 range [%.2g, %.2g]"
                  "  c=E/k1/u range [%.2g, %.2g]"
                  % (fam, nround[fam], nexact[fam], n_excluded[fam],
                     rng_[0] if rng_ else float("nan"), rng_[1] if rng_ else float("nan"),
                     rngc[0] if rngc else float("nan"), rngc[1] if rngc else float("nan")))
            for label, fit in fits.items():
                print("        beta[%-11s] = %.3f +- %.3f (n=%d)" % (label, fit["beta"], fit["se"], fit["n"]))

        pooled = fams["pair"] + fams["cancel"]
        pfits = subset_fits(pooled)
        betas = [v["beta"] for v in pfits.values()]
        blk["p_knob"]["pooled_fits"] = pfits
        blk["p_knob"]["beta_range"] = [min(betas), max(betas)] if betas else None
        print("   POOLED (%d cases):" % len(pooled))
        for label, fit in pfits.items():
            print("        beta[%-11s] = %.3f +- %.3f (n=%d)" % (label, fit["beta"], fit["se"], fit["n"]))
        if blk["p_knob"]["beta_range"]:
            lo, hi = blk["p_knob"]["beta_range"]
            print("        -> range [%.3f, %.3f] : %s" % (
                lo, hi,
                "INSIDE linear (P2 holds)" if lo <= 1.0 <= hi else
                "resolvably SUBLINEAR (P2 over-states high conditioning)" if hi < 1.0 else
                "resolvably SUPERLINEAR"))
        trend = c_trend(pooled, u)
        blk["c_trend"] = trend
        print("   collapse constant c = E_floor/(kappa1*u) by kappa1 bin:")
        for k, c, n in trend["bins"]:
            print("        kappa1~%8.2f  c = %.4f  (n=%d)" % (k, c, n))
        a, b, r2 = trend["fit_a_over_k1_plus_b"]
        print("        additive reading  c = %.3f/kappa1 + %.4f   R2 = %.3f  (b = the high-kappa1 tail)"
              % (a, b, r2))
        spread = band_spread(bymat, 1.0, 1.5, u)
        # the spread is a FINDING (it is the refutation of P2's sharp form); what is asserted is that
        # the test is POWERED -- a handful of matrices cannot distinguish "constant" from "spread"
        assert spread["n_matrices"] >= 6, \
            "only %d matrices carry the [1,1.5) band -- too few to read a spread" % spread["n_matrices"]
        blk["band_spread_kappa1_1_1p5"] = spread
        print("   at a FIXED kappa1 band [1, 1.5): c per matrix")
        for name_, cm, nn in spread["matrices"]:
            print("        %-16s c = %.4f  (n=%d)" % (name_, cm, nn))
        print("        -> spread across matrices: %s  (= %.1fx)" % (
            "%.3g .. %.3g" % (spread["lo"], spread["hi"]) if spread["n_matrices"] else "n/a",
            spread["ratio"] if spread["ratio"] else float("nan")))
        out["formats"][fname] = blk

    with open(os.path.join(HERE, "spike_real2_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_real2_results.json")
    return 0


# ----------------------------------------------------------------- self-test
def _raise():
    raise AssertionError("the planted defect did not fire")


def assert_reach(pair):
    """REACH: the instrument must have arrived (rounds > 20) at a kappa1 well above 1 (worst > 100)."""
    rounds, worst = pair
    assert rounds > 20 and worst > 100, \
        "the family does not reach the regime (rounds=%d, max kappa1=%.3g)" % (rounds, worst)


def selftest():
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError:
            print("[%-30s] FIRED" % name)
            return
        print("[%-30s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-30s] holds" % name)
        except AssertionError as e:
            print("[%-30s] *** FIRED ON HEALTHY *** %s" % (name, str(e)[:30]))
            ok = False

    okc, badc = R.verify_corpus()
    assert not badc, "selftest needs the corpus"

    # C1: the cancelling construction really cancels -- (a+b).(a-b) == |a|^2 - |b|^2.  The plant is a
    # DIFFERENT construction (a+b, a+b) that genuinely violates the identity, so the ASSERT fires.
    def assert_identity(a, b, second=None):
        u = [x + y for x, y in zip(a, b)]
        v = [x + y for x, y in zip(a, b)] if second == "plus" else [x - y for x, y in zip(a, b)]
        assert S.dot_exact(u, v) == sum(x * x for x in a) - sum(y * y for y in b), \
            "the cancelling identity does not hold"

    nr, nc, ent = R.load_mtx(os.path.join(MATDIR, "west0067.mtx"))
    A, _ = R.quantize(nr, nc, ent, 11)
    cols = [[A[i][j] for i in range(nr)] for j in range(min(nc, 12))]
    fires("cancel-identity-broken", lambda: assert_identity([1, 2], [1, 3], "plus"))
    holds("cancel-identity/ok", lambda: all(assert_identity(cols[i], cols[j]) for i in range(len(cols))
                                            for j in range(i + 1, len(cols))))

    # C2 (REACH certificate, Class 182): the cancel family must arrive at a kappa1 well above 1 WITH
    # rounding.  The plant is a generator whose cases are ALL excluded -- one that cannot reach, which
    # is exactly the failure this certificate exists to catch.
    def reaches(cases_fn, A, nr, nc, p):
        q = p // 2
        worst, rounds = 0.0, 0
        for _tag, a, b in cases_fn(A, nr, nc):
            r = floor_and_kappa(a, b, q, p)
            if r is None:
                continue
            k1, ef = r
            if ef > 0:
                rounds += 1
                worst = max(worst, k1)
        return rounds, worst

    def degenerate_cases(A, nr, nc):
        return [("z", [1, -1], [1, 1])]          # exact sum zero -> excluded -> rounds stays 0

    A24, _ = R.quantize(nr, nc, ent, 24)
    rounds, worst = reaches(cancel_cases, A24, nr, nc, 24)
    print("   [reach probe] cancel fp32: %d rounding cases, max kappa1 = %.3g" % (rounds, worst))
    fires("regime-not-reached", lambda: assert_reach(reaches(degenerate_cases, A24, nr, nc, 24)))
    holds("regime-reached/ok", lambda: assert_reach((rounds, worst)))

    # C3: a reported beta RANGE needs at least two fits (a single fit is a number, not a range)
    def assert_range(fits):
        assert len(fits) >= 2, "a range needs at least two subset fits"

    fires("range-from-one-fit", lambda: assert_range({"all": {"beta": 0.5}}))
    holds("range-from-two/ok", lambda: assert_range({"a": {}, "b": {}}))

    # C3b: the zero-variance crash is REAL -- the unguarded routine raises (this is a MUTATION test:
    # the plant removes the guard by calling fit_slope_se directly), while subset_fits is guarded.
    def crashes_on_flat(ks, es):
        try:
            S.fit_slope_se(ks, es)
            return False
        except ZeroDivisionError:
            return True

    fires("unguarded-crashes", lambda: (crashes_on_flat([1.0] * 20, [1e-6] * 20) is False) or _raise())
    holds("guarded-ok", lambda: (subset_fits([(1.0, 1e-6)] * 20) == {}) or _raise())

    # C4: an exact-zero floor is excluded, not divided by
    def excluded(a, b):
        return floor_and_kappa(a, b, 2, 8) is None

    fires("zero-sum-kept", lambda: (excluded([1, -1], [1, 1]) is False) or _raise())
    holds("zero-sum-excluded/ok", lambda: excluded([1, -1], [1, 1]) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
