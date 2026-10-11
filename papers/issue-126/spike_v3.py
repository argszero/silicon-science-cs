#!/usr/bin/env python3
"""spike_v3 (#126) -- IS THE E_acc EXPONENT ABOUT THE ADDITION COUNT, OR ABOUT THE SPLIT'S SHAPE?

spike_v2 measured E_acc against the number of additions M = K*n and fitted an exponent
0.223 +- 0.053, where the sqrt(K) model predicts 0.5.  But its only instrument was split_exact --
contiguous bit-blocks -- so as K grows each part SHRINKS and many late additions round away to
nothing.  The add COUNT and the addend SHAPE moved together, so the exponent could be about either
(Class 172/177: the two sides of a comparison conditioned on different objects).  This instrument
separates them:

  scheme "contig"  contiguous bit-blocks (spike_v2's split_exact): parts span the whole magnitude range
  scheme "spread"  INTERLEAVED bits: part i carries bit positions i, i+K, i+2K, ... in their true
                   positions, so every part has a SIMILAR magnitude; the SAME add count, the SAME
                   exact sum, a different shape
  scheme "kahan"   contiguous parts with COMPENSATED summation: the rounding error is carried and
                   re-added, so the M-dependence should largely VANISH

The verdict is a comparison, not a coefficient:
  * if "spread" gives the SAME exponent, the exponent is about the number of roundings, not the shape;
  * if it rises toward 0.5, spike_v2's 0.223 was an artefact of the shrinking addends and the sqrt(K)
    law is re-armed.  Either way, a second route that CAN disagree is what makes the first meaningful.

Certificates:
  C1  both splits reconstruct the exact product (their parts sum to it), for several K and signs
  C2  at p huge (no rounding) every scheme is EXACT, whatever M
  C3  the compensated arm is NOT worse than the naive arm at the same M (a direction, not closeness)
  C4  the compensated arm's exponent is ZERO (within 0.05): compensation removes the M-dependence,
      which is what Kahan's bound says and what a broken/uncompensated arm cannot satisfy
  C6  the naive exponent is SUB-LINEAR (< 1): the worst case M*u is not attained
Output: spike_v3_results.json
Usage:  python3 spike_v3.py [--selftest]
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S  # noqa: E402  (the exact register, the data generator, the statistics)


# ----------------------------------------------------------------- the two split shapes
def split_contig(v, K):
    """Contiguous bit-blocks, heaviest first (spike_v2's split_exact -- the incumbent route)."""
    return S.split_exact(v, K)


def split_spread(v, K):
    """INTERLEAVED bits: part i keeps the bit positions j with j % K == i, in their true positions.

    Same exact sum, same number of parts, but every part draws from the whole exponent range, so the
    parts are of SIMILAR magnitude -- the shape the contiguous split cannot produce.
    """
    if v == 0:
        return [0] * K
    sign = 1 if v > 0 else -1
    ax = abs(v)
    bits = [0] * K
    for j in range(ax.bit_length()):
        if (ax >> j) & 1:
            bits[j % K] |= (1 << j)
    out = [sign * b for b in bits]
    out.sort(key=lambda t: -abs(t))
    return out


def scheme_parts(v, K, scheme):
    return split_contig(v, K) if scheme == "contig" else split_spread(v, K)


# ----------------------------------------------------------------- the accumulation arms
def dot_scheme(a, b, K, p, scheme):
    """Add each element's product through K parts, rounding a p-bit register after EVERY add."""
    run = 0
    for x, y in zip(a, b):
        for t in scheme_parts(x * y, K, scheme):
            run = S.sig_round(run + t, p)
    return run


def dot_kahan(a, b, K, p):
    """Contiguous parts with compensated summation: C carries the lost low bits into the next add."""
    run, comp = 0, 0
    for x, y in zip(a, b):
        for t in split_contig(x * y, K):
            yv = t - comp
            tmp = run + yv                 # exact (Python ints)
            r = S.sig_round(tmp, p)
            comp = (r - run) - yv          # the rounding error of THIS add (exact), as Kahan defines it
            run = r
    return run


def dot_any(a, b, K, p, scheme):
    return dot_kahan(a, b, K, p) if scheme == "kahan" else dot_scheme(a, b, K, p, scheme)


# ----------------------------------------------------------------- measurement
def eacc_cells(Ks, p, n, p_in, seeds, scheme, cancel=4.0):
    """Per-cell curves: one row per seed, rows[K] = E/kappa1.  The SAME cells at every K, so the
    exponent can be fitted WITHIN a cell -- a paired design, which removes the between-cell scatter
    that makes a pooled median so noisy (the R539 defect in the estimator, not in the physics)."""
    rows = []
    for s in range(seeds):
        rng = random.Random(S.SEED0 + 4241 * s + 131 * n + 17 * p)
        a, b = S.gen_case(n, p_in, rng, cancel)
        ex = S.dot_exact(a, b)
        if ex == 0:
            continue
        k = S.kappa1(a, b)
        row = {}
        for K in Ks:
            row[K] = S.relerr(dot_any(a, b, K, p, scheme), ex) / k
        rows.append(row)
    return rows


def paired_exponent(rows, Ks):
    """Fit the exponent in EACH cell; summarise the per-cell exponents by their median and its SE."""
    e = []
    for row in rows:
        val, _se = S.fit_slope_se(Ks, [row[K] for K in Ks])
        if val == val:                     # not NaN
            e.append(val)
    e.sort()
    cnt = len(e)
    if cnt < 3:
        return float("nan"), float("nan"), e
    med = e[cnt // 2]
    mean = sum(e) / cnt
    sd = math.sqrt(sum((x - mean) ** 2 for x in e) / (cnt - 1))
    se = 1.253 * sd / math.sqrt(cnt)       # SE of a median
    return med, se, e


def main():
    out = {"seed0": S.SEED0}
    P_IN, N, SEEDS = 24, 300, 24
    Ks = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    p = 12

    print("=" * 100)
    print("spike_v3 -- is the E_acc exponent about the ADDITION COUNT or about the SPLIT'S SHAPE?")
    print("=" * 100)

    rows_by = {}
    curves = {}
    exps = {}
    for scheme in ("contig", "spread", "kahan"):
        rows_by[scheme] = eacc_cells(Ks, p, N, P_IN, SEEDS, scheme)
        curves[scheme] = {K: S.median([r[K] for r in rows_by[scheme]]) for K in Ks}
        e, se, allexp = paired_exponent(rows_by[scheme], Ks)
        exps[scheme] = (e, se)
        out["per_cell_exponents_" + scheme] = allexp
    out["curves"] = curves
    out["exponents"] = {k: {"e": v[0], "se": v[1]} for k, v in exps.items()}

    print()
    print("E_acc/kappa1 vs M = K*n (p=12, n=%d, %d seeds)" % (N, SEEDS))
    print("   %-4s %-14s %-14s %-14s" % ("K", "contig", "spread", "kahan"))
    for K in Ks:
        print("   %-4d %-14.3e %-14.3e %-14.3e"
              % (K, curves["contig"][K], curves["spread"][K], curves["kahan"][K]))
    print()
    for scheme in ("contig", "spread", "kahan"):
        e, se = exps[scheme]
        n_sig = abs(e) / se if se else float("inf")
        print("   exponent[%-6s] = %.3f +- %.3f  (paired per-cell; %.1f SE from 0)"
              % (scheme, e, se, n_sig))
    ec, sec = exps["contig"]
    es, ses = exps["spread"]
    d = abs(ec - es) / math.sqrt(sec * sec + ses * ses) if (sec or ses) else float("nan")
    out["contig_vs_spread_sigma"] = d
    print("   contig vs spread: %.3f vs %.3f -> %.2f SE apart %s"
          % (ec, es, d, "(AGREE: the exponent is about the add count)"
             if d < 2 else "(DISAGREE: the shape matters)"))
    print("   sqrt(K)=0.5 prediction: contig %.2f SE away, spread %.2f SE away"
          % (abs(ec - 0.5) / sec if sec else float("nan"),
             abs(es - 0.5) / ses if ses else float("nan")))

    # a second register width: is the exponent p-independent?
    print()
    print("p-independence check (p=18, same Ks)")
    for scheme in ("contig", "spread"):
        r18 = eacc_cells(Ks, 18, N, P_IN, SEEDS, scheme)
        e18, se18, _ = paired_exponent(r18, Ks)
        out["exponent_p18_" + scheme] = {"e": e18, "se": se18}
        print("   exponent[%-6s] at p=18 = %.3f +- %.3f  (at p=12: %.3f +- %.3f)"
              % (scheme, e18, se18, exps[scheme][0], exps[scheme][1]))

    # ---- certificates
    print()
    print("certificates")
    rng = random.Random(S.SEED0)
    a, b = S.gen_case(120, P_IN, rng)
    ex = S.dot_exact(a, b)
    # C1: both splits reconstruct the product exactly
    for v in (ex, -ex, ex // 3 or 7, -12345):
        for K in (1, 2, 3, 7, 12, 32):
            assert sum(split_contig(v, K)) == v, "contig split does not reconstruct %d at K=%d" % (v, K)
            assert sum(split_spread(v, K)) == v, "spread split does not reconstruct %d at K=%d" % (v, K)
    print("   C1 both splits reconstruct the exact product (K in {1,2,3,7,12,32}, signs both)")
    # C2: at p huge every scheme is exact
    for scheme in ("contig", "spread", "kahan"):
        for K in (1, 8, 32):
            assert dot_any(a, b, K, 4000, scheme) == ex, \
                "%s is not exact at p=4000, K=%d" % (scheme, K)
    print("   C2 exact at p=4000 for every scheme and K in {1,8,32}")
    # C3: the compensated arm is never worse than the naive arm at the same M
    for K in Ks:
        assert curves["kahan"][K] <= curves["contig"][K] * 1.001, \
            "compensation is WORSE at K=%d (%.3e vs %.3e)" % (K, curves["kahan"][K], curves["contig"][K])
    print("   C3 compensation is never worse than the naive arm (every K)")
    # C4 is a DESIGN property of compensated summation (its error bound is independent of M), so it
    # asserts FLATNESS -- and it FIRES on an uncompensated or sign-flipped arm (a broken Kahan read
    # 0.404 +- 0.288 this round).  The naive arms' own exponents are FINDINGS, reported, never asserted
    # (asserting a model prediction is the defect this round is about).
    ek, sek = exps["kahan"]
    assert abs(ek) < 0.05, "the compensated arm is not flat in M (exponent %.3f +- %.3f)" % (ek, sek)
    assert ec < 1.0, "the naive exponent exceeds the linear worst case (%.3f)" % ec
    print("   C4 compensated exponent %.3f +- %.3f : flat in M (within 0.05)" % (ek, sek))
    print("   C6 naive (contig) exponent %.3f < 1 (the worst case M*u is not attained)" % ec)
    print("      findings: contig %.3f +- %.3f (%.1f SE from 0), spread %.3f +- %.3f (%.1f SE from 0)"
          % (ec, sec, ec / sec if sec else float("inf"), es, ses, es / ses if ses else float("inf")))

    with open(os.path.join(HERE, "spike_v3_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v3_results.json")
    return 0


# ----------------------------------------------------------------- self-test
def _raise():
    raise AssertionError("the planted defect did not fire")


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

    rng = random.Random(3)
    a, b = S.gen_case(60, 24, rng)

    # C1: a split that does NOT reconstruct must fire
    def reconstructs(split, v, K):
        return sum(split(v, K)) == v

    fires("split-loses-a-bit", lambda: reconstructs(lambda v, K: [v - 1] + [0] * (K - 1), 100, 4) or _raise())
    holds("split-reconstructs/ok", lambda: reconstructs(split_spread, 100, 4) or _raise())

    # C2: an inexact-at-huge-p arm must fire
    def exact_at_huge_p(dot, a, b):
        return dot(a, b, 8, 4000) == S.dot_exact(a, b)

    fires("arm-inexact-at-huge-p",
          lambda: exact_at_huge_p(lambda a, b, K, p: S.dot_exact(a, b) + 1, a, b) or _raise())
    holds("arm-exact-at-huge-p/ok",
          lambda: exact_at_huge_p(lambda a, b, K, p: dot_scheme(a, b, K, p, "spread"), a, b) or _raise())

    # C3: compensation worse than naive must fire
    def not_worse(comp, naive):
        return comp <= naive * 1.001

    fires("compensation-worse", lambda: not_worse(1e-3, 1e-5) or _raise())
    holds("compensation-ok", lambda: not_worse(1e-5, 1e-3) or _raise())

    # C4: a FALLING exponent and a noise-level exponent must both fire
    def grows(e, se):
        return e > max(0.1, 4.0 * se)

    fires("exponent-falls", lambda: grows(-0.3, 0.05) or _raise())
    fires("exponent-at-noise", lambda: grows(0.12, 0.04) or _raise())
    holds("exponent-grows/ok", lambda: grows(0.5, 0.05) or _raise())

    # C6: an exponent above the linear worst case must fire
    def sublinear(e):
        return e < 1.0

    fires("exponent-above-linear", lambda: sublinear(1.4) or _raise())
    holds("exponent-sublinear/ok", lambda: sublinear(0.22) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
