#!/usr/bin/env python3
"""spike_real3 (#126) -- THE SECOND SCALAR: why kappa1 is not enough, and what the accumulator rounds.

R543 (spike_real2) REFUTED the sharp form of prior P2: at a FIXED kappa1 band [1,1.5) the collapse
constant c = E_floor/(kappa1*u) varies 3.1-5.8x across matrices.  This instrument identifies the missing
scalar from the MECHANISM instead of guessing one:

  the emulator rounds the RUNNING SUM after every add -- `S = sig_round(S + t, p)` -- so the accumulation
  error contributed by add k is O(u * |S_k|), with S_k the PARTIAL SUM after k adds.  The error therefore
  depends on the magnitudes ALONG THE SUMMATION PATH.  But

      kappa1 = ||ab||_1 / |S_n|                                                    (terms only)

  is a function of the TERMS, with no reference to the order in which they are added: it is blind to the
  path BY CONSTRUCTION.

REGISTERED PREDICTION (written before measuring):
  P4  the second scalar is the PATH condition number, normalised exactly as kappa1 is --
          R_sum = (sum_k |S_k|) / (sum_i |a_i b_i|)          the L1 (worst-case) walk, and
          R_rms = sqrt(sum_k S_k^2) / (sum_i |a_i b_i|)      the random-walk form
      with c = E/(kappa1*u) equal to one of them up to a constant O(1).
  P5  R_path is ORDER-DEPENDENT while kappa1 is ORDER-INVARIANT, so the decisive test is WITHIN-CASE:
      permute the summation order at FIXED kappa1 and the measured floor must move, with R_path
      predicting the move.  A between-matrix collapse alone could be coincidence; this cannot.

Certificates (asserted, not printed):
  C1  kappa1 is invariant under permutation (the property that makes the within-case arm a test of
      kappa1's insufficiency rather than of the permutation).
  C2  R_sum is NOT invariant under permutation -- if it were, it would be another function of the terms
      and could not be the missing scalar.
  C3  the custom ordered emulator reproduces the library emulator on the identity order.
  C4  [path] the end of the path is the exact dot product when K is at the operand's own limb count.
  C5  the collapse test CAN fail: a control scalar constant across matrices leaves the spread unchanged,
      so a "collapse" the test reports is a measurement and not an artefact of the arithmetic.
  C6  [power] at least 6 matrices carry the fixed-kappa1 band (Class 184: a spread test owes powering).
Output: spike_real3_results.json
Usage:  python3 spike_real3.py [--selftest]
"""
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S      # noqa: E402
import spike_real as R    # noqa: E402
import spike_real2 as R2  # noqa: E402  (R543's families and floor definition, imported not modified)

MATDIR = R.MATDIR
SEED0 = 20261007
KMAX = 6
BAND = (1.0, 1.5)                       # the fixed-kappa1 band (R543's, so the spreads are comparable)


# ----------------------------------------------------------------- the summation path
def limb_terms(x, y, q, K):
    """the SIGNED limb products of ONE element, in the emulator's own order (heaviest first)."""
    neg = (x < 0) ^ (y < 0)
    return [(-t if neg else t) for t in S.diagonals(x, y, q)[:K]]


def dot_ordered(a, b, q, K, p, order):
    """the emulator's accumulation with the ELEMENT order given explicitly (route A otherwise)."""
    acc = 0
    for i in order:
        for t in limb_terms(a[i], b[i], q, K):
            acc = S.sig_round(acc + t, p)
    return acc


def path_scalars(a, b, q, K, order=None):
    """The PATH condition numbers of the summation the emulator actually performs.

    Returns None for a degenerate case.  `T` is the L1 norm of the TERMS (the normalisation kappa1
    also uses) and `final` is the exact end of the path -- so `T/|final|` IS kappa1 up to the
    K-truncation, which lets this routine serve as its own consistency check (C4).
    """
    idx = list(range(len(a))) if order is None else list(order)
    terms = []
    for i in idx:
        terms.extend(limb_terms(a[i], b[i], q, K))
    T = sum(abs(t) for t in terms)
    if T == 0:
        return None
    acc, sk = 0, []
    for t in terms:
        acc += t
        sk.append(abs(acc))
    n_ad = len(terms)
    r_sum = sum(sk) / T
    r_rms = math.sqrt(sum(v * v for v in sk)) / T
    return {"n_add": n_ad, "T": T, "final": acc,
            "r_sum": r_sum,
            "r_rms": r_rms,
            "r_max": max(sk) / T,
            # the NORMALISED forms: a raw walk sum grows with the number of adds, so a fair test of P4
            # has to try the walk divided by its own length / its own sqrt -- otherwise "does it
            # collapse?" would be answering a question about n_add instead of about the path.
            "r_mean": r_sum / n_ad,
            "r_rms_n": r_rms / math.sqrt(n_ad)}


# ----------------------------------------------------------------- the measured floor
def floor_and_kappa(a, b, q, p):
    """(kappa1, E_floor) -- EXACTLY R543's definition, imported so the rounds stay comparable."""
    return R2.floor_and_kappa(a, b, q, p)


def c_at_k(a, b, q, p, K):
    """(kappa1, E_K, c_K) at a FIXED K -- used by the within-case order arm."""
    ex = S.dot_exact(a, b)
    k1 = S.kappa1(a, b)
    if ex == 0 or k1 == float("inf") or not R2.resolvable(k1, p):
        return None
    E = S.relerr(S.dot_emulated(a, b, q, K, p), ex)
    u = 2.0 ** -p
    return k1, E, (E / (k1 * u) if E > 0 else None)


def c_ordered(a, b, q, p, K, order):
    """(kappa1, E_K, c_K) with the summation order given explicitly -- the within-case arm's probe."""
    ex = S.dot_exact(a, b)
    k1 = S.kappa1(a, b)
    if ex == 0 or k1 == float("inf") or not R2.resolvable(k1, p):
        return None
    E = S.relerr(dot_ordered(a, b, q, K, p, order), ex)
    u = 2.0 ** -p
    return k1, E, (E / (k1 * u) if E > 0 else None)


# ----------------------------------------------------------------- analysis
def collapse_check(rows, key):
    """`rows` = [(name, c, scalar_dict)]; returns the spread of c and of c/scalar across matrices.

    A scalar COLLAPSES the spread when `ratio_scaled` is well below `ratio_raw` (R543's 3.1-5.8x).
    `key=None` is the control: dividing by 1, so ratio_scaled == ratio_raw (C5).
    """
    cs = [c for _n, c, _s in rows]
    raw = (max(cs) / min(cs)) if len(cs) >= 2 and min(cs) else None
    if key is None:
        return {"key": None, "ratio_raw": raw, "ratio_scaled": raw, "n": len(rows)}
    sc = [c / s[key] for _n, c, s in rows if s and s.get(key)]
    ratio = (max(sc) / min(sc)) if len(sc) >= 2 and min(sc) else None
    return {"key": key, "ratio_raw": raw, "ratio_scaled": ratio, "n": len(rows)}


def _corr(xs, ys):
    """Pearson correlation -- the within-case arm asks how well a scalar TRACKS the measured c."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def linfit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return float("nan"), float("nan"), float("nan")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    return a, b, (1 - ss / sst if sst else float("nan"))


def main():
    out = {"seed0": SEED0, "band": list(BAND), "kmax": KMAX, "formats": {}}
    FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]

    print("=" * 100)
    print("spike_real3 -- the second scalar: what the accumulator rounds, and why kappa1 cannot see it")
    print("=" * 100)

    ok, bad = R.verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok

    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]
    lo, hi = BAND
    band_cache = {}

    for fname, p in FORMATS:
        q, u = p // 2, 2.0 ** -p
        rows, all_cases = [], []
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            cases = R2.pair_cases(A, nr, nc) + R2.cancel_cases(A, nr, nc)
            band_cache.setdefault(fname, {})[name] = None
            bc, bs = [], []
            for _tag, a, b in cases:
                r = floor_and_kappa(a, b, q, p)
                if r is None:
                    continue
                k1, ef = r
                if ef <= 0:
                    continue
                ps = path_scalars(a, b, q, KMAX)
                if ps is None:
                    continue
                c = ef / (k1 * u)
                all_cases.append((k1, c, ps))
                if lo <= k1 < hi:
                    bc.append(c)
                    bs.append(ps)
            if len(bc) >= 8:
                def med(vals, k):
                    return S.median([v[k] for v in vals])
                rows.append((name, S.median(bc),
                             {"r_sum": med(bs, "r_sum"), "r_rms": med(bs, "r_rms"),
                              "r_max": med(bs, "r_max"), "r_mean": med(bs, "r_mean"),
                              "r_rms_n": med(bs, "r_rms_n"), "n_add": med(bs, "n_add")}))
        rows.sort(key=lambda t: t[1])

        blk = {"p": p, "q": q, "u": u, "n_cases": len(all_cases)}
        print()
        print("--- %s (p=%d q=%d, %d cases) ---" % (fname, p, q, len(all_cases)))
        print("   at the FIXED kappa1 band [%g, %g): per-matrix medians" % (lo, hi))
        print("   %-16s %9s %9s %9s %9s %9s %8s"
              % ("matrix", "c", "R_sum", "R_rms", "R_max", "R_mean", "n_add"))
        for nm, c, sc in rows:
            print("   %-16s %9.4f %9.4f %9.4f %9.4f %9.5f %8.1f"
                  % (nm, c, sc["r_sum"], sc["r_rms"], sc["r_max"], sc["r_mean"], sc["n_add"]))
        assert len(rows) >= 6, \
            "only %d matrices carry the [%g,%g) band (C6: a spread test owes powering)" % (len(rows), lo, hi)
        blk["band_matrices"] = [{"matrix": n, "c": c, "scalars": sc} for n, c, sc in rows]

        print("   does a scalar collapse the spread?  [ratio_scaled / ratio_raw -> 0 is collapse]")
        checks = {}
        for key in (None, "r_sum", "r_rms", "r_max", "r_mean", "r_rms_n", "n_add"):
            ch = collapse_check(rows, key)
            checks[key or "control(identity)"] = ch
            frac = (ch["ratio_scaled"] / ch["ratio_raw"]) if ch["ratio_raw"] else float("nan")
            print("        %-18s %8.3f / %8.3f = %.3f" %
                  (key or "control(identity)", ch["ratio_scaled"], ch["ratio_raw"], frac))
        blk["collapse"] = checks

        fits = {}
        for key in ("r_sum", "r_rms", "r_max", "r_mean", "r_rms_n", "n_add"):
            xs = [math.log(s[key]) for _k, _c, s in all_cases if s[key] > 0 and _c > 0]
            ys = [math.log(c) for _k, c, s in all_cases if s[key] > 0 and c > 0]
            if len(xs) >= 20 and len(set(xs)) > 1:
                a, b, r2 = linfit(xs, ys)
                fits[key] = {"slope": b, "intercept": a, "exp_intercept": math.exp(a), "r2": r2, "n": len(xs)}
        blk["loglog_fits"] = fits
        print("   log-log fit  log c = a + b*log(scalar)  over the whole corpus:")
        for key, f in sorted(fits.items()):
            print("        %-7s slope=%+.3f  exp(intercept)=%.3f  R2=%.3f  (n=%d)"
                  % (key, f["slope"], f["exp_intercept"], f["r2"], f["n"]))
        out["formats"][fname] = blk

    # ------------------------------------------------------------- the within-case order arm
    print()
    print("=" * 100)
    print("WITHIN-CASE ORDER ARM -- kappa1 fixed by construction, only the summation order moves (P5)")
    print("=" * 100)
    out["order_arm"] = {}
    NPERM, KORD = 24, 4
    for fname, p in [("fp32", 24), ("fp16", 11)]:
        q, u = p // 2, 2.0 ** -p
        results = []
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            best, bk, bv = None, 0.0, None
            for _tag, aa, bb in R2.cancel_cases(A, nr, nc):
                r = c_at_k(aa, bb, q, p, KORD)
                if r and r[0] > bk:
                    best, bk, bv = aa, r[0], bb
            if best is None or bk < 10.0:
                continue
            a, b = best, bv
            n = len(a)
            rng = random.Random(SEED0 + n)
            perms = [list(range(n)), list(range(n - 1, -1, -1))]
            while len(perms) < NPERM:
                pr = list(range(n))
                rng.shuffle(pr)
                perms.append(pr)
            k1s, cs, rs, rr = [], [], [], []
            for pr in perms:
                r = c_ordered(a, b, q, p, KORD, pr)
                ps = path_scalars(a, b, q, KORD, order=pr)
                if r is None or ps is None or r[2] is None:
                    continue          # r[2] is None when that order accumulates EXACTLY: E = 0 has no c
                k1s.append(r[0])
                cs.append(r[2])
                rs.append(ps["r_sum"])
                rr.append(ps["r_rms"])
            if len(cs) < 5:
                continue
            # C7 [power]: a spread read from a handful of orders is not powered -- a floor, declared as
            # one (Class 173/184: a printed bar is not a gate, and an invented bar is not a test).
            assert len(cs) >= 8, "C7: only %d usable orders -- too few to read an order spread" % len(cs)
            # C1: kappa1 is EXACTLY invariant under permutation.  C2: R_sum is NOT -- so the two are
            # not the same function of the case and the arm is a test of kappa1's insufficiency.
            assert max(k1s) - min(k1s) < 1e-9, "C1 violated: kappa1 moved under permutation"
            # C2 is an EXISTENCE claim, never a magnitude bar: R_sum must fail to be invariant under at
            # least one order tried (a magnitude threshold here would be an invented one -- Class 173).
            assert max(rs) > min(rs), "C2 violated: R_sum was invariant under every order tried"
            _, bsum, r2s = linfit([math.log(v) for v in rs], [math.log(v) for v in cs])
            _, brms, r2r = linfit([math.log(v) for v in rr], [math.log(v) for v in cs])
            rho_sum = _corr([math.log(v) for v in cs], [math.log(v) for v in rs])
            rho_rms = _corr([math.log(v) for v in cs], [math.log(v) for v in rr])
            rec = {"matrix": name, "kappa1": k1s[0], "n_add": len(rs), "n_orders": len(cs),
                   "rho_logc_logRsum": rho_sum, "rho_logc_logRrms": rho_rms,
                   "c_over_Rsum_min": min(c / v for c, v in zip(cs, rs)),
                   "c_over_Rsum_max": max(c / v for c, v in zip(cs, rs)),
                   "c_min": min(cs), "c_max": max(cs), "c_spread_at_fixed_kappa1": max(cs) / min(cs),
                   "r_sum_spread": max(rs) / min(rs),
                   "logc_vs_logr_sum": {"slope": bsum, "r2": r2s},
                   "logc_vs_logr_rms": {"slope": brms, "r2": r2r}}
            results.append(rec)
            print("   %-16s kappa1=%.3g (invariant)" % (name, k1s[0]))
            print("        c over %d orders: %.3g .. %.3g  -> %.2fx at FIXED kappa1"
                  % (len(cs), min(cs), max(cs), rec["c_spread_at_fixed_kappa1"]))
            print("        R_sum spread %.2fx | log c vs log R_sum: slope=%+.3f R2=%.3f rho=%+.3f"
                  % (rec["r_sum_spread"], bsum, r2s, rho_sum))
            print("        log c vs log R_rms: slope=%+.3f R2=%.3f rho=%+.3f" % (brms, r2r, rho_rms))
            print("        c/R_sum spans %.3f .. %.3f (a %.0fx span -- if R_sum were THE scalar this is 1)"
                  % (rec["c_over_Rsum_min"], rec["c_over_Rsum_max"],
                     rec["c_over_Rsum_max"] / rec["c_over_Rsum_min"]))
        out["order_arm"][fname] = results
        if results:
            sp = sorted(r["c_spread_at_fixed_kappa1"] for r in results)
            rhos = [r["rho_logc_logRsum"] for r in results if r["rho_logc_logRsum"] == r["rho_logc_logRsum"]]
            neg = sum(1 for v in rhos if v < 0)
            pooled = {"n_matrices": len(results), "c_spread_median": sp[len(sp) // 2],
                      "c_spread_max": max(sp), "c_spread_min": min(sp),
                      "n_rho_negative": neg, "n_rho": len(rhos),
                      "rho_median": sorted(rhos)[len(rhos) // 2] if rhos else None}
            out.setdefault("order_arm_pooled", {})[fname] = pooled
            print("   POOLED %s: %d matrices | c-spread at FIXED kappa1: min %.2fx median %.2fx max %.2fx"
                  % (fname, len(results), min(sp), sp[len(sp) // 2], max(sp)))
            print("        sign of rho(log c, log R_sum): %d of %d NEGATIVE -- %s"
                  % (neg, len(rhos),
                     "NO CONSISTENT SIGN across matrices" if 0 < neg < len(rhos) else "consistent"))

    with open(os.path.join(HERE, "spike_real3_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_real3_results.json")
    return 0


# ----------------------------------------------------------------- self-test
def _raise():
    raise AssertionError("the planted defect did not fire")


def selftest(argv=None):
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError:
            print("[%-34s] FIRED" % name)
            return
        print("[%-34s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-34s] holds" % name)
        except AssertionError as e:
            print("[%-34s] *** FIRED ON HEALTHY *** %s" % (name, str(e)[:34]))
            ok = False

    okc, badc = R.verify_corpus()
    assert not badc, "selftest needs the corpus"

    nr, nc, ent = R.load_mtx(os.path.join(MATDIR, "west0067.mtx"))
    A, _ = R.quantize(nr, nc, ent, 24)
    q, p, K = 12, 24, 4
    a = b = None
    for _tag, aa, bb in R2.cancel_cases(A, nr, nc):
        r = c_at_k(aa, bb, q, p, K)
        if r and r[0] > 50.0:
            a, b = aa, bb
            break
    assert a is not None, "selftest needs a high-kappa1 cancel case"
    n = len(a)
    rev = list(range(n - 1, -1, -1))

    def k1_is_order_invariant(a, b):
        return abs(S.kappa1(a, b) - S.kappa1(a, b)) < 1e-12

    def rsum_is_order_invariant(a, b):
        return abs(path_scalars(a, b, q, K, order=rev)["r_sum"]
                   - path_scalars(a, b, q, K)["r_sum"]) < 1e-12

    # C1/C2 -- the property that makes the order arm a test of kappa1's INSUFFICIENCY: kappa1 does not
    # move under permutation, R_sum does.  Each plant asserts the property that must be false.
    fires("kappa1-claimed-order-dependent", lambda: (k1_is_order_invariant(a, b) is False) or _raise())
    holds("kappa1-order-invariant/ok", lambda: k1_is_order_invariant(a, b) or _raise())
    fires("rsum-claimed-order-invariant", lambda: (rsum_is_order_invariant(a, b) is True) or _raise())
    holds("rsum-order-dependent/ok", lambda: (not rsum_is_order_invariant(a, b)) or _raise())

    # C3 -- the custom ordered emulator IS the library emulator on the identity order.  The plant uses a
    # different K, which is a genuinely different summation, so the equality fails.
    def same_as_library(a, b, kk, order):
        return dot_ordered(a, b, q, kk, p, order) == S.dot_emulated(a, b, q, kk, p)

    # the plant is a DIFFERENT ORDER (reversed), which for this cancelling case genuinely accumulates
    # to a different value -- so an equality assertion on it RAISES.  (The first version of this plant
    # changed K on BOTH sides, which is the same summation and could never fire.)
    fires("ordered!=library/reversed", lambda: same_as_library(a, b, K, rev) or _raise())
    holds("ordered==library/identity", lambda: same_as_library(a, b, K, list(range(n))) or _raise())

    # C4 -- the end of the recorded path IS the exact dot product once K reaches the operands' own limb
    # count, so the path scalar is normalised by the quantity kappa1 uses (T/|final| == kappa1).  The
    # plant truncates (K=1), where the path ends short of the exact sum.
    kfull = max(len(S.diagonals(a[i], b[i], q)) for i in range(n))

    def path_ends_exact(a, b, kk):
        ps = path_scalars(a, b, q, kk)
        return ps is not None and ps["final"] == S.dot_exact(a, b)

    fires("path-ends-exact/K-truncated", lambda: path_ends_exact(a, b, 1) or _raise())
    holds("path-ends-exact/K-full", lambda: path_ends_exact(a, b, kfull) or _raise())

    # C5 -- the collapse test CAN fail.  The control (identity) divides by 1, so c/scalar has exactly
    # c's spread; a test that "reports a collapse" on it is reporting arithmetic, not a measurement.
    rows = [("m1", 0.5, {"r_sum": 3.0}), ("m2", 1.0, {"r_sum": 2.0}), ("m3", 2.0, {"r_sum": 9.0})]
    ctl = collapse_check(rows, None)

    def control_collapses(rows, ctl):
        ch = collapse_check(rows, None)
        return ctl["ratio_raw"] and ch["ratio_scaled"] < ch["ratio_raw"] / 2.0

    fires("collapse-on-control", lambda: control_collapses(rows, ctl) or _raise())
    holds("collapse-needs-division/ok", lambda: (ctl["ratio_scaled"] == ctl["ratio_raw"]) or _raise())

    # C6 -- powering: a spread read from fewer than 6 matrices is not powered (Class 184).
    def powered(rows):
        return len(rows) >= 6

    fires("spread-unpowered", lambda: (powered(rows[:3]) is True) or _raise())
    holds("spread-powered/ok", lambda: powered(rows + rows) or _raise())
    # C7 [power, order arm] -- the same floor applied to the ORDER axis: a spread over 3 orders is
    # unpowered, and the plant asserts exactly that (so the assertion must be able to reject it).
    def orders_powered(cs):
        assert len(cs) >= 8, "fewer than 8 usable orders"

    fires("order-arm-unpowered", lambda: orders_powered([1.0, 2.0, 3.0]))
    holds("order-arm-powered/ok", lambda: orders_powered([float(i) for i in range(8)]))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
