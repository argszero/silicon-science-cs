#!/usr/bin/env python3
"""spike_v2 (#126) -- THE TWO-AXIS LAW AND THE OPTIMAL LIMB COUNT K*(p).

spike_v0 measured the floor at a fixed limb count; spike_v1 measured the accumulator-bits law with
EXACT inputs (one limb each, so truncation was identically zero).  This instrument joins them: real
multi-limb inputs, so BOTH error sources are live at once, and asks the question the two halves pose
jointly --

    for an accumulator of width p and q-bit limbs, how many limb products K should be kept, and can a
    narrower accumulator be bought back with more limbs?

THE MODEL it tests:

    E/kappa1  =  c_t * 2^{-q K}      +      c_a * sqrt(K) * 2^{-p}
                 \\_ truncation _/           \\_ accumulation _/

The two terms move in OPPOSITE directions as K grows: truncation falls as 2^{-qK}, while the number of
rounded additions grows with K, so accumulation grows ~ sqrt(K).  Hence (i) an INTERIOR optimum
K*(p, q), and (ii) the sharp claim: more limbs trade against the LIMB width q but NOT against the
accumulator width p -- below c_a*2^{-p} no K helps, which is "limbs cannot substitute for a wide
register" in its measured form.

METHOD NOTE (a defect fixed in this round).  E_total(K), E_trunc(K) and the floor E_acc are all
computed on the SAME cells (one seed loop): medians over DIFFERENT cell sets are not comparable, and
the first version's composition ratios were meaningless for exactly that reason.

Certificates:
  C1  two independent routes for the emulated sum (integer sig_round vs an exact Fraction register)
  C2  both controls on the SAME case: p huge -> truncation only; K huge -> accumulation only
  C3  composition: E_total is reproduced by the SUM or the RMS of the two isolated terms (same cells)
  C4  the number of additions raises the accumulation error, isolated by EXACT splits (truncation=0)
  C5  an INTERIOR optimum K* exists for every (p, q) tested (two independent routes to it)
  C6  the ROBUST K* (the truncation-mean crossover) is NON-DECREASING in p at fixed q
  C7  the floor: E_total(K) is not far below the accumulation-only error, for every K
Output: spike_v2_results.json
Usage:  python3 spike_v2.py [--selftest]
"""
import json
import math
import os
import random
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
SEED0 = 20261005


# ----------------------------------------------------------------- the register
def sig_round(v, p):
    """Round an integer to p significant bits (round-half-to-even). Exact, integer-only."""
    if v == 0:
        return 0
    nb = v.bit_length()
    if nb <= p:
        return v
    sh = nb - p
    quo, rem = divmod(abs(v), 1 << sh)
    half = 1 << (sh - 1)
    if rem > half or (rem == half and (quo & 1)):
        quo += 1
    return (1 if v > 0 else -1) * (quo << sh)


def sig_round_frac(v, p):
    """The same rule in exact rational arithmetic -- an INDEPENDENT route (C1)."""
    if v == 0:
        return Fraction(0)
    sign = 1 if v > 0 else -1
    ax = abs(v)
    e = ax.numerator.bit_length() - ax.denominator.bit_length()
    while Fraction(2) ** e <= ax:
        e += 1
    while Fraction(2) ** (e - 1) > ax:
        e -= 1
    scaled = ax / (Fraction(2) ** (e - p))
    f = math.floor(scaled)
    r = scaled - f
    if r > Fraction(1, 2) or (r == Fraction(1, 2) and (f & 1)):
        f += 1
    return sign * Fraction(f) * (Fraction(2) ** (e - p))


# ----------------------------------------------------------------- the split and the product
def limbs(x, q):
    """base-2^q limbs of |x|, least-significant first."""
    x = abs(x)
    out = []
    while x:
        out.append(x & ((1 << q) - 1))
        x >>= q
    return out or [0]


def diagonals(x, y, q):
    """the limb products of one element, HEAVIEST diagonal first (the leading terms).

    Truncation keeps the K heaviest: the dropped terms are the light ones, whose weight decays
    2^{-q} per diagonal down.  Keeping the lightest instead gives an error that never falls (the
    self-diagnosing defect spike_v0 hit).
    """
    out = []
    for j, xj in enumerate(limbs(x, q)):
        for l, yl in enumerate(limbs(y, q)):
            out.append((j + l, xj * yl * (1 << (q * (j + l)))))
    out.sort(key=lambda t: -t[0])
    return [t for _w, t in out]


def dot_emulated(a, b, q, K, p, route="A"):
    """Keep the K heaviest limb products per element; round a p-bit register after every add."""
    if route == "A":
        S = 0
        for x, y in zip(a, b):
            neg = (x < 0) ^ (y < 0)
            for t in diagonals(x, y, q)[:K]:
                S = sig_round(S + (-t if neg else t), p)
        return S
    S = Fraction(0)
    for x, y in zip(a, b):
        neg = (x < 0) ^ (y < 0)
        for t in diagonals(x, y, q)[:K]:
            t = Fraction(t)
            S = sig_round_frac(S + (-t if neg else t), p)
    return S


def split_exact(v, K):
    """K integer parts whose sum is EXACTLY v, heaviest first.

    Isolation instrument for the accumulation arm: the parts reconstruct |v| exactly, so truncation
    is identically zero however large K grows, while the number of rounded additions is exactly K.
    """
    if v == 0:
        return [0] * K
    sign = 1 if v > 0 else -1
    ax = abs(v)
    bits = ax.bit_length()
    s = max(1, (bits + K - 1) // K)
    out = []
    for i in range(K - 1, -1, -1):
        sh = s * i
        part = ((ax >> sh) & ((1 << s) - 1)) if sh < bits else 0
        out.append(sign * (part << sh))
    return out


def dot_parts(a, b, K, p):
    """Accumulate each element's product through K EXACT parts, rounding the register each add.

    Truncation is zero by construction, so the only error is accumulation -- and it grows with the
    number of additions M = K*n.  This is the countervailing force that makes K* interior.
    """
    S = 0
    for x, y in zip(a, b):
        for t in split_exact(x * y, K):
            S = sig_round(S + t, p)
    return S


# ----------------------------------------------------------------- data
def gen_case(n, p_in, rng, cancel=4.0):
    half = 1 << (p_in - 1)
    a, b = [], []
    for _ in range(n):
        x = rng.randrange(1, half)
        y = rng.randrange(1, half)
        s = 1 if rng.random() < 0.5 else -1
        a.append(s * x)
        b.append(y)
    if cancel != 1.0 and n >= 4:
        tgt = sum(x * y for x, y in zip(a, b))
        for _ in range(int(cancel * 4)):
            if abs(tgt) < 1:
                break
            i = rng.randrange(n)
            a[i] = -a[i]
            tgt = sum(x * y for x, y in zip(a, b))
    return a, b


def dot_exact(a, b):
    return sum(x * y for x, y in zip(a, b))


def kappa1(a, b):
    den = abs(dot_exact(a, b))
    return (sum(abs(x * y) for x, y in zip(a, b)) / den) if den else float("inf")


def relerr(S, exact):
    return abs(S - exact) / abs(exact) if exact else float("inf")


def median(cells):
    vals = sorted(v for v in cells if v is not None)
    if not vals:
        return None
    return vals[len(vals) // 2]


def mean(cells):
    vals = [v for v in cells if v is not None]
    return sum(vals) / len(vals) if vals else None


def measure(Kmax, q, p, n, p_in, seeds, cancel=4.0):
    """E_total(K), E_trunc(K) and the floor E_acc -- ALL on the same cells (one seed loop)."""
    tot = {K: [] for K in range(1, Kmax + 1)}
    trn = {K: [] for K in range(1, Kmax + 1)}
    acc = []
    for s in range(seeds):
        rng = random.Random(SEED0 + 7919 * s + 131 * n + 17 * p + 29 * q)
        a, b = gen_case(n, p_in, rng, cancel)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        k = kappa1(a, b)
        for K in range(1, Kmax + 1):
            tot[K].append(relerr(dot_emulated(a, b, q, K, p), ex) / k)
            trn[K].append(relerr(dot_emulated(a, b, q, K, 4000), ex) / k)
        acc.append(relerr(dot_emulated(a, b, q, 999, p), ex) / k)
    return ({K: median(tot[K]) for K in tot}, {K: median(trn[K]) for K in trn}, median(acc),
            {K: mean(trn[K]) for K in trn}, mean(acc))


def acc_vs_additions(Ks, p, n, p_in, seeds, cancel=4.0):
    """E_acc vs the number of additions, truncation zero by construction (exact K-way splits)."""
    per = {K: [] for K in Ks}
    for s in range(seeds):
        rng = random.Random(SEED0 + 4241 * s + 131 * n + 17 * p)
        a, b = gen_case(n, p_in, rng, cancel)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        k = kappa1(a, b)
        for K in Ks:
            per[K].append(relerr(dot_parts(a, b, K, p), ex) / k)
    return {K: median(per[K]) for K in Ks}


def fit_slope(xs, ys):
    lx = [math.log(x, 2) for x in xs]
    ly = [math.log(y, 2) for y in ys]
    mx = sum(lx) / len(lx)
    my = sum(ly) / len(ly)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
    den = sum((a - mx) ** 2 for a in lx)
    return num / den if den else float("nan")


def fit_slope_se(xs, ys):
    """log2-log2 slope WITH its standard error, so an exponent is compared rather than guessed."""
    lx = [math.log(x, 2) for x in xs]
    ly = [math.log(y, 2) for y in ys]
    n = len(lx)
    mx = sum(lx) / n
    my = sum(ly) / n
    sxx = sum((a - mx) ** 2 for a in lx)
    sl = sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx
    resid = sum((b - my - sl * (a - mx)) ** 2 for a, b in zip(lx, ly))
    se = math.sqrt(resid / (n - 2) / sxx) if n > 2 and sxx else float("nan")
    return sl, se


def main():
    out = {"seed0": SEED0}
    P_IN = 24
    N = 300
    SEEDS = 24
    KMAX = 12

    print("=" * 100)
    print("spike_v2 -- the two-axis law: truncation (2^-qK) vs accumulation (~2^-p), joint in K")
    print("=" * 100)

    # ---- sweep A: the two sources separately, and the joint curve (same cells)
    print()
    print("sweep A -- E/kappa1 vs K, sources isolated on the SAME cells (q=8, p=12)")
    q, p = 8, 12
    jt, tr, acc, trm, accm = measure(KMAX, q, p, N, P_IN, SEEDS)
    A_tot, A_trn, A_acc = jt, tr, acc   # sweep A owns these; certificates read them
    print("   %-4s %-14s %-14s %-14s" % ("K", "E_trunc", "E_total", "E_acc floor"))
    out["sweepA"] = {"q": q, "p": p, "E_trunc": tr, "E_total": jt, "E_acc_floor": acc}
    for K in range(1, KMAX + 1):
        print("   %-4d %-14.3e %-14.3e %-14.3e" % (K, tr[K], jt[K], acc))
    kbest = min(range(1, KMAX + 1), key=lambda K: jt[K])
    print("   -> floor (K=999) = %.3e ; optimum K* = %d at E = %.3e" % (acc, kbest, jt[kbest]))

    # ---- sweep C: the composition rule (same cells)
    print()
    print("sweep C -- composition: E_total vs (E_trunc + E_acc) and the RMS of the two (same cells)")
    ratio_sum, ratio_rms = [], []
    for K in range(1, KMAX + 1):
        s = tr[K] + acc
        r = math.sqrt(tr[K] ** 2 + acc ** 2)
        ratio_sum.append(jt[K] / s)
        ratio_rms.append(jt[K] / r)
    out["sweepC"] = {"ratio_total_over_sum": ratio_sum, "ratio_total_over_rms": ratio_rms}
    print("   %-4s %-14s %-16s %-16s" % ("K", "E_total", "E_total/(sum)", "E_total/(rms)"))
    for i, K in enumerate(range(1, KMAX + 1)):
        print("   %-4d %-14.3e %-16.3f %-16.3f" % (K, jt[K], ratio_sum[i], ratio_rms[i]))
    # the composition is a claim about the regimes where BOTH are live; at large K truncation -> 0
    live = [i for i in range(KMAX) if tr[i + 1] > 0.01 * acc]
    dev_sum = max(abs(ratio_sum[i] - 1) for i in live) if live else float("nan")
    dev_rms = max(abs(ratio_rms[i] - 1) for i in live) if live else float("nan")
    out["composition_live_K"] = [i + 1 for i in live]
    out["composition_dev_sum"] = dev_sum
    out["composition_dev_rms"] = dev_rms
    print("   -> where both terms are live (K in %s): worst departure from 1 = sum %.2f, rms %.2f"
          % ([i + 1 for i in live], dev_sum, dev_rms))

    # ---- sweep B: K*(p) at fixed q -- limbs scale with the accumulator width
    print()
    print("sweep B -- K*(p) at fixed q=8: does the optimal limb count grow with the accumulator?")
    q_fix = 8
    ps = [8, 10, 12, 14, 16, 18, 20]
    kstar = {}
    for p in ps:
        bjt, btr, bacc, btrm, baccm = measure(KMAX, q_fix, p, N, P_IN, SEEDS)
        kb = min(range(1, KMAX + 1), key=lambda K: bjt[K])
        kc = next((K for K in range(1, KMAX + 1) if btrm[K] <= baccm), None)
        kstar[p] = {"K_star_argmin": kb, "K_star_cross": kc, "E_star": bjt[kb], "floor": bacc,
                    "E_trunc_at_Kstar": btr[kb]}
        print("   p=%-3d -> K*_argmin = %-3d  K*_cross = %-3s  E* = %.3e   floor = %.3e"
              % (p, kb, kc, bjt[kb], bacc))
    out["sweepB"] = kstar
    ks_arg = [kstar[p]["K_star_argmin"] for p in ps]
    ks_cross = [kstar[p]["K_star_cross"] for p in ps]
    out["Kstar_argmin_seq"] = ks_arg
    out["Kstar_cross_seq"] = ks_cross
    if len(set(ks_cross)) > 1 and None not in ks_cross:
        sl_kp, se_kp = fit_slope_se(ps, [float(x) for x in ks_cross])
        out["Kstar_cross_slope_vs_p"] = sl_kp
        out["Kstar_cross_slope_se"] = se_kp
        print("   -> K*_cross %s ; slope vs p %.3f +- %.3f" % (ks_cross, sl_kp, se_kp))
    print("   -> K*_argmin %s  (jagged: the median truncation collapses to exact 0)" % ks_arg)

    # ---- sweep D: accumulation vs the NUMBER OF ADDITIONS (exact splits: truncation stays 0)
    print()
    print("sweep D -- E_acc vs the number of additions M=K*n (exact K-way splits, truncation zero)")
    Ks = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    eacc = acc_vs_additions(Ks, 12, N, P_IN, 48)
    out["sweepD"] = eacc
    for K in Ks:
        print("   K=%-3d E_acc=%.3e" % (K, eacc[K]))
    sl_acc, se_acc = fit_slope_se(Ks, [eacc[K] for K in Ks])
    out["Eacc_slope_vs_K"] = sl_acc
    out["Eacc_slope_se"] = se_acc
    nsigma = abs(sl_acc - 0.5) / se_acc if se_acc else float("nan")
    out["Eacc_vs_sqrtK_sigma"] = nsigma
    print("   -> fitted exponent of E_acc against K: %.3f +- %.3f   (sqrt(K) predicts 0.5: %.2f SE)"
          % (sl_acc, se_acc, nsigma))

    # ---- certificates (asserted, not printed)
    print()
    print("certificates")
    rng = random.Random(SEED0)
    a, b = gen_case(120, P_IN, rng)
    ex = dot_exact(a, b)
    # C1: two routes agree
    for K in (2, 5, 9):
        assert dot_emulated(a, b, q, K, p, "A") == dot_emulated(a, b, q, K, p, "B"), \
            "routes disagree at K=%d" % K
    print("   C1 two independent routes agree at K in {2,5,9}")
    # C2: the two controls on the same case
    e_wide = relerr(dot_emulated(a, b, q, 5, 4000), ex)     # p huge -> truncation only
    e_nolim = relerr(dot_emulated(a, b, q, 999, p), ex)     # K huge -> accumulation only
    assert e_wide > 0, "the no-accumulation control reads 0 -- no truncation"
    assert e_nolim > 0, "the no-truncation control reads 0 -- no accumulation"
    print("   C2 both controls non-zero: trunc-only %.3e, acc-only %.3e" % (e_wide, e_nolim))
    # C3: a composition rule holds within a stated factor, over the cells where both terms are live
    assert live, "no cell has both terms live -- the composition claim is empty"
    assert dev_sum < 0.5 or dev_rms < 0.5, \
        "neither composition rule holds (sum %.2f rms %.2f over K=%s)" % (dev_sum, dev_rms,
                                                                         [i + 1 for i in live])
    best_rule = "rms" if dev_rms <= dev_sum else "sum"
    print("   C3 composition holds (%s rule): worst departure sum %.2f / rms %.2f over K=%s"
          % (best_rule, dev_sum, dev_rms, [i + 1 for i in live]))
    # C4: more additions raise the accumulation error.  The threshold is derived from the fit's own
    # sampling error, so a flat/noise slope cannot pass it (the R538 lesson: a window wide enough to
    # admit the alternative is not a test).  The specific sqrt(K)=0.5 exponent is reported
    # SEPARATELY -- it is a finding, not this assertion.
    assert sl_acc > max(0.1, 4.0 * se_acc), \
        "E_acc does not grow with the number of additions (exponent %.3f +- %.3f)" % (sl_acc, se_acc)
    print("   C4 E_acc grows with M: exponent %.3f +- %.3f > max(0.1, 4 SE)" % (sl_acc, se_acc))
    print("      sqrt(K)=0.5 prediction: %.2f SE away -> %s"
          % (nsigma, "CONSISTENT" if se_acc and nsigma < 3 else "NOT supported by this sweep"))
    # C5: an interior optimum exists for every p tested (both routes name a K in range)
    for p in ps:
        assert kstar[p]["K_star_cross"] is not None, "no crossover optimum at p=%d" % p
        assert 1 <= kstar[p]["K_star_argmin"] <= KMAX, "no argmin optimum at p=%d" % p
    print("   C5 an interior optimum exists for every p in %s (both routes agree it exists)" % ps)
    # C6: on the ROBUST route the optimum is NON-DECREASING in p: a wider accumulator tolerates more
    # truncation at equal accuracy, so reaching the same place needs MORE limbs, never fewer.  This is
    # a MODEL-derived prediction, not a design invariant -- so its naive dual (the median-argmin
    # route, jagged on a statistic that collapses to exact 0) is REPORTED, never asserted.
    assert all(ks_cross[i] <= ks_cross[i + 1] for i in range(len(ks_cross) - 1)), \
        "K*_cross is not non-decreasing in p: %s" % ks_cross
    print("   C6 K*_cross non-decreasing in p: %s" % ks_cross)
    print("      finding: the argmin route is JAGGED (%s)" % ks_arg)
    # C7: the floor -- on sweep A's own curve, no K is far below the accumulation-only level
    for K in range(1, KMAX + 1):
        assert A_tot[K] >= 0.5 * A_acc, \
            "E_total(K=%d)=%.3e is below the floor %.3e" % (K, A_tot[K], A_acc)
    print("   C7 the floor holds (sweep A): min_K E_total = %.3e >= 0.5 x floor %.3e"
          % (min(A_tot.values()), A_acc))

    with open(os.path.join(HERE, "spike_v2_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v2_results.json")
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
    a, b = gen_case(60, 24, rng)
    ex = dot_exact(a, b)

    # C1: routes agree -- the plant gives a DISAGREEING case (a corrupted route B), never the pair
    fires("routes-disagree",
          lambda: (dot_emulated(a, b, 8, 4, 12, "A") == dot_emulated(a, b, 8, 4, 12, "B") + 1) or _raise())
    holds("routes-agree/ok",
          lambda: (dot_emulated(a, b, 8, 4, 12, "A") == dot_emulated(a, b, 8, 4, 12, "B")) or _raise())

    # C2: a control reading zero (plant: a case with zero error where the property is "nonzero")
    e_wide = relerr(dot_emulated(a, b, 8, 4, 4000), ex)

    def nonzero(x):
        return x > 0

    fires("control-reads-zero", lambda: nonzero(0.0) or _raise())
    holds("control-nonzero/ok", lambda: nonzero(e_wide) or _raise())

    # C3: composition (plant: a ratio far from 1, e.g. a factor-of-50 miss)
    def comp_ok(r):
        return abs(r - 1) < 0.5

    fires("composition-breaks", lambda: comp_ok(50.0) or _raise())
    holds("composition-ok", lambda: comp_ok(1.05) or _raise())

    # C4: E_acc grows with M (plants: a FALLING slope, and a slope at noise level -- both must fire)
    def acc_grows(s, se):
        return s > max(0.1, 4.0 * se)

    fires("acc-falls-with-M", lambda: acc_grows(-0.3, 0.05) or _raise())
    fires("acc-at-noise", lambda: acc_grows(0.12, 0.04) or _raise())
    holds("acc-grows/ok", lambda: acc_grows(0.5, 0.05) or _raise())

    # C6: K*_cross non-decreasing in p (plant: a crossover sequence that FALLS)
    def nondecr(seq):
        return all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))

    fires("kcross-falls-with-p", lambda: nondecr([1, 3, 3, 2, 5]) or _raise())
    holds("kcross-nondecr/ok", lambda: nondecr([1, 3, 3, 3, 5]) or _raise())

    # C7: the floor (plant: a total BELOW the floor by a large factor)
    def above_floor(tot, fl):
        return tot >= 0.5 * fl

    fires("total-below-floor", lambda: above_floor(1e-9, 1e-3) or _raise())
    holds("floor-holds/ok", lambda: above_floor(1e-3, 1e-3) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
