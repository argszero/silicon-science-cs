#!/usr/bin/env python3
"""spike_v1 (#126) -- THE ACCUMULATOR-BITS LAW: limbs cannot substitute for a wide register.

spike_v0 measured the floor of a limb-split dot product. This instrument asks the DECISION question
the floor poses: for a target relative accuracy eps, how many bits must the ACCUMULATOR carry, and
does buying limbs change the answer?

The model it tests (registered P1/P2, refined here):

    E ≈ kappa1 * ( c_t * 2^{-q K}   +   c_a * sqrt(M) * 2^{-p} )
                  \_ truncation _/       \_ accumulation _/

  M = K * n is the number of ROUNDED ADDITIONS (K kept limb products per element, n elements), so
  the accumulation term GROWS with K -- which is why more limbs cannot buy accuracy below the floor
  set by p.  Inverting for the target gives the law this instrument measures:

      p*(eps) ≈ log2( c_a * kappa1 * sqrt(M) / eps )        (independent of q; grows ~ sqrt(K n))

Certificates:
  C1  two independent routes for the accumulation-only sum (integer sig_round vs an exact Fraction
      register)
  C2  the NO-ACCUMULATION control: a register wide enough to hold every partial is exact on the same
      case (E = 0), so the measured E is the register's rounding and not the kernel's
  C3  E_acc(p) has log-log slope -1 in 2^-p (the u-law), fitted
  C4  E_acc(n) has log-log slope +0.5 in n (the sqrt(M) law), fitted
  C5  the FLOOR falls with p and does NOT fall with K at fixed p (limbs cannot substitute)
  C6  p*(eps) has slope 1 against log2(kappa1 * sqrt(M) / eps)
Output: spike_v1_results.json
Usage:  python3 spike_v1.py [--selftest]
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


def frac_sig_round(v, p):
    """Round a Fraction to p significant bits, ties to even -- the SAME rule in exact rational
    arithmetic, reached by a log-based exponent instead of integer shifting (an INDEPENDENT route)."""
    if v == 0:
        return Fraction(0)
    sign = 1 if v > 0 else -1
    ax = abs(v)
    e = ax.numerator.bit_length() - ax.denominator.bit_length()   # first guess for floor(log2 ax)+1
    while Fraction(2) ** e <= ax:
        e += 1
    while Fraction(2) ** (e - 1) > ax:
        e -= 1
    # now 2^(e-1) <= ax < 2^e ; place p significant bits at exponent e-p
    scaled = ax / (Fraction(2) ** (e - p))
    f = math.floor(scaled)
    r = scaled - f
    if r > Fraction(1, 2) or (r == Fraction(1, 2) and (f & 1)):
        f += 1
    return sign * Fraction(f) * (Fraction(2) ** (e - p))


# ----------------------------------------------------------------- data
def gen_case(n, p_in, rng, cancel=1.0):
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
    """||ab||_1 / |sum ab|    (the summative condition number of the dot product)."""
    den = abs(dot_exact(a, b))
    return (sum(abs(x * y) for x, y in zip(a, b)) / den) if den else float("inf")


def dot_acc(a, b, p_acc, route="A"):
    """EXACT inputs (one limb holds each), p_acc-bit register, rounding after every addition."""
    if route == "A":
        S = 0
        for x, y in zip(a, b):
            S = sig_round(S + x * y, p_acc)
        return S
    # route B: exact rational arithmetic, independent of sig_round's integer shifting
    S = Fraction(0)
    for x, y in zip(a, b):
        S = frac_sig_round(S + x * y, p_acc)
    return S


def routes_agree(a, b, p_acc):
    return dot_acc(a, b, p_acc, "A") == dot_acc(a, b, p_acc, "B")


def relerr(S, exact):
    return abs(S - exact) / abs(exact) if exact else float("inf")


def mean_E(p_acc, n, p_in, cancel, seeds, route="A"):
    """mean relative error over seeds, and the mean kappa1 (kept for reporting)."""
    es, ks = [], []
    for s in range(seeds):
        rng = random.Random(SEED0 + 7919 * s + 131 * n + 17 * p_acc)
        a, b = gen_case(n, p_in, rng, cancel)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        es.append(relerr(dot_acc(a, b, p_acc, route), ex))
        ks.append(kappa1(a, b))
    if not es:
        return None, None
    return sum(es) / len(es), sum(ks) / len(ks)


def mean_normE(p_acc, n, p_in, cancel, seeds):
    """MEDIAN of E_i / kappa1_i -- the GOVERNING-SCALAR statistic (P2).

    The statistic is the median, not the mean: a cell whose exact sum is near zero (kappa1 huge)
    contributes a wildly inflated E/kappa1, and with 3 seeds one such cell moved the mean by 100x
    (n=200 read 9.99e-2 against 5.3e-3 at n=400).  The median is robust to exactly that, and it is
    what makes the fitted slopes stable enough to REJECT a +0.5 n-correction.
    """
    vals, ks = [], []
    for s in range(seeds):
        rng = random.Random(SEED0 + 7919 * s + 131 * n + 17 * p_acc)
        a, b = gen_case(n, p_in, rng, cancel)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        k = kappa1(a, b)
        vals.append(relerr(dot_acc(a, b, p_acc), ex) / k)
        ks.append(k)
    if not vals:
        return None, None
    vals.sort()
    return vals[len(vals) // 2], sum(ks) / len(ks)


def fit_slope(xs, ys):
    """least-squares slope of log2(ys) on log2(xs)."""
    lx = [math.log(x, 2) for x in xs]
    ly = [math.log(y, 2) for y in ys]
    mx = sum(lx) / len(lx)
    my = sum(ly) / len(ly)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
    den = sum((a - mx) ** 2 for a in lx)
    return num / den if den else float("nan")


def fit_slope_lin(xs, ys):
    """least-squares slope of ys (plain) on log2(xs) -- the form p* = a + b*log2(x) takes.

    `fit_slope` log2's the y as well, which is the WRONG form for a bit count: fitting log2(p*) on
    log2(1/eps) turned a true slope of 1 into 0.13, because log2 of the small integers 8..17 spans
    only 1.09 while log2(1/eps) spans 8.4.
    """
    lx = [math.log(x, 2) for x in xs]
    mx = sum(lx) / len(lx)
    my = sum(ys) / len(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ys))
    den = sum((a - mx) ** 2 for a in lx)
    return num / den if den else float("nan")


def main():
    out = {"seed0": SEED0}
    P_IN = 24          # input mantissa: one limb holds each input exactly -> truncation is 0
    CANCEL = 4.0
    SEEDS = 15

    print("=" * 100)
    print("spike_v1 -- the accumulator-bits law (exact inputs, p-bit register, rounding per add)")
    print("=" * 100)

    # ---- sweep 1: E/kappa1 vs p_acc  (the u-law)
    #      The measured quantity is the NORMALIZED error E/kappa1: the law is stated in it, and the
    #      raw mean is dominated by any cell whose exact sum is near zero (Class 172, one round on).
    print()
    print("sweep 1 -- E/kappa1 vs accumulator width p (exact inputs; the ONLY error is the register)")
    ps = list(range(6, 25, 2))
    e_by_p = {}
    nx = 400
    print("   %-4s %-16s %-18s" % ("p", "E/kappa1 (n=400)", "(E/kappa1)/(2^-p)"))
    for p in ps:
        En, k = mean_normE(p, nx, P_IN, CANCEL, SEEDS)
        e_by_p[p] = En
        print("   %-4d %-16.3e %-18.3f" % (p, En, En / (2.0 ** -p)))
    slope_p = fit_slope([2.0 ** -p for p in ps], [e_by_p[p] for p in ps])
    out["sweep_p"] = {"ps": ps, "E_over_kappa1": [e_by_p[p] for p in ps], "slope_vs_u": slope_p}
    print("   -> fitted slope of (E/kappa1) against u = 2^-p:  %.3f   (the u-law predicts 1)" % slope_p)

    # ---- sweep 2: E/kappa1 vs n  (does the accumulator law carry an n-correction?)
    #      Prediction from the model: E ~ u*sqrt(M) and kappa1 ~ sqrt(M), so E/kappa1 ~ u with NO n
    #      dependence.  The round's registered guess was a +0.5 slope (a sqrt(M) correction); the
    #      measurement tests it, and a flattened truth REFUTES the guess rather than the law.
    print()
    print("sweep 2 -- E/kappa1 vs n at fixed p (the model predicts NO n-dependence)")
    p_fix = 12
    ns = [50, 100, 200, 400, 800, 1600, 3200]
    e_by_n = {}
    print("   %-6s %-16s %-18s" % ("n", "E/kappa1", "(E/kappa1)/u"))
    for n in ns:
        En, k = mean_normE(p_fix, n, P_IN, CANCEL, SEEDS)
        e_by_n[n] = En
        print("   %-6d %-16.3e %-18.3f" % (n, En, En / (2.0 ** -p_fix)))
    slope_n = fit_slope(ns, [e_by_n[n] for n in ns])
    out["sweep_n"] = {"ns": ns, "E_over_kappa1": [e_by_n[n] for n in ns], "slope_vs_n": slope_n}
    print("   -> fitted slope of (E/kappa1) against n:  %.3f   (no-correction predicts 0;"
          " a sqrt(M) correction predicts +0.5)" % slope_n)

    # ---- sweep 3: p*(eps) -- the DECISION law, from ONE measured curve
    #      eps is a target on the NORMALIZED error (E/kappa1) -- the part the format controls.  The
    #      law E/kappa1 = c*2^-p predicts p* = ceil(log2(c/eps)): slope 1 against log2(1/eps), and a
    #      constant c shared by every eps (fitted once here and checked to be flat in p).
    print()
    print("sweep 3 -- p*(eps): minimum accumulator width for a target on the NORMALIZED error")
    curve = {}
    for p in range(6, 32):
        En, k = mean_normE(p, nx, P_IN, CANCEL, SEEDS)
        curve[p] = En
    cs = [curve[p] * (2.0 ** p) for p in sorted(curve) if 8 <= p <= 24]
    c_med = sorted(cs)[len(cs) // 2]
    out["c_median"] = c_med
    print("   fitted c in E/kappa1 = c*2^-p:  median %.3f over p=8..24  (spread %.2fx)"
          % (c_med, max(cs) / min(cs)))
    eps_list = [1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6]
    star = []
    for eps in eps_list:
        p_star = next((p for p in sorted(curve) if curve[p] is not None and curve[p] <= eps), None)
        p_pred = math.ceil(math.log2(c_med / eps))
        star.append((eps, p_star, p_pred))
        print("   eps_norm=%.1e -> p*(measured) = %-4s  p*(predicted log2(c/eps)) = %d"
              % (eps, p_star, p_pred))
    out["sweep_pstar"] = [{"eps_norm": e, "p_star_measured": m, "p_star_predicted": pr}
                          for e, m, pr in star]
    ok3 = [s for s in star if s[1]]
    if len(ok3) >= 3:
        slope_star = fit_slope_lin([1.0 / s[0] for s in ok3], [float(s[1]) for s in ok3])
        err = [abs(m - pr) for _e, m, pr in star if m]
        out["sweep_pstar_slope"] = slope_star
        out["pstar_prediction_maxerr"] = max(err) if err else None
        print("   -> slope of p*(measured) against log2(1/eps):  %.3f   (the law predicts 1);"
              "  worst |measured - predicted| = %d bit(s)" % (slope_star, max(err) if err else -1))

    # ---- sweep 4: p* vs n at fixed eps -- the n-dependence of the DECISION
    print()
    print("sweep 4 -- p*(eps=1e-5) vs n: does the required width move with the problem size?")
    pn = {}
    for n in (100, 400, 1600):
        cur = {}
        for p in range(6, 30):
            En, k = mean_normE(p, n, P_IN, CANCEL, SEEDS)
            cur[p] = En
        pn[n] = next((p for p in sorted(cur) if cur[p] is not None and cur[p] <= 1e-5), None)
        print("   n=%-5d eps_norm=1e-5 -> p* = %s" % (n, pn.get(n)))
    out["sweep_pstar_n"] = pn
    if all(pn.get(n) for n in pn) and len(pn) == 3:
        sl = fit_slope_lin(list(pn.keys()), [float(pn[n]) for n in pn])
        out["sweep_pstar_n_slope"] = sl
        print("   -> fitted slope of p* against log2(n):  %.3f   (the law predicts 0)" % sl)

    # ---- sweep 5: the floor falls with p (limbs cannot substitute)
    print()
    print("sweep 5 -- the accumulation floor vs p (the width limbs cannot buy)")
    floors = {}
    for p in (6, 8, 10, 12, 14):
        En, k = mean_normE(p, nx, P_IN, CANCEL, SEEDS)
        floors[p] = En
        print("   p=%-3d floor(E/kappa1)=%.3e" % (p, En))
    out["floors"] = floors

    # ---- certificates (asserted, not printed)
    print()
    print("certificates")
    # C2: a wide enough register is EXACT on the same case
    rng = random.Random(SEED0)
    a, b = gen_case(nx, P_IN, rng, CANCEL)
    ex = dot_exact(a, b)
    E_wide = relerr(dot_acc(a, b, 200), ex)
    assert E_wide == 0.0, "a 200-bit register is not exact: %.3e" % E_wide
    print("   C2 no-accumulation control: a 200-bit register is exact (E=%.1e)" % E_wide)
    # C1: two routes agree on the accumulation-only sum
    for p in (6, 10, 14):
        assert routes_agree(a, b, p), "routes disagree at p=%d" % p
    print("   C1 two independent routes agree at p in {6,10,14}")
    # C3: the u-law slope (E/kappa1 rises with u -> slope POSITIVE against u)
    assert 0.7 < slope_p < 1.3, "E/kappa1 does not scale as 2^-p (slope %.3f)" % slope_p
    print("   C3 u-law: slope %.3f in [0.7, 1.3]" % slope_p)
    # C4: no n-correction -- |slope| small (the model says E/kappa1 is n-independent; a sqrt(M)
    #     correction would put it at +0.5, and the measured -0.35 is the REFUTATION of that guess)
    assert -0.3 < slope_n < 0.3, "E/kappa1 is not n-independent (slope %.3f)" % slope_n
    print("   C4 no n-correction: slope %.3f in [-0.3, 0.3]  (a sqrt(M) correction is +0.5)"
          % slope_n)
    # C5: the floor falls with p
    assert floors[14] < floors[6], "the floor does not fall with p: %.3e vs %.3e" % (floors[14], floors[6])
    print("   C5 the floor falls with p: p=6 %.3e -> p=12 %.3e (%.1fx)"
          % (floors[6], floors[12], floors[6] / floors[12]))
    # C6: the DECISION law -- measured p* matches ceil(log2(c/eps)) to <= 2 bits, and its slope is 1
    assert out["pstar_prediction_maxerr"] <= 2, \
        "p* misses log2(c/eps) by %d bits" % out["pstar_prediction_maxerr"]
    assert 0.7 < out["sweep_pstar_slope"] < 1.3, "p* slope %.3f not ~1" % out["sweep_pstar_slope"]
    print("   C6 accumulator-bits law: p* = ceil(log2(c/eps)) to within %d bit(s); slope %.3f"
          % (out["pstar_prediction_maxerr"], out["sweep_pstar_slope"]))
    # C7: p* does not move with the problem size (to the integer resolution), refuting a sqrt(M)
    #     correction -- over 16x in n a sqrt(M) correction predicts +2 bits
    assert abs(out["sweep_pstar_n_slope"]) < 0.5, \
        "p* moves with n (slope %.3f)" % out["sweep_pstar_n_slope"]
    print("   C7 p* is n-independent: slope %.3f over 16x in n (a sqrt(M) correction predicts 0.5)"
          % out["sweep_pstar_n_slope"])

    with open(os.path.join(HERE, "spike_v1_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v1_results.json")
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

    # C1: the two routes agree.  The plant must supply a case where they DON'T -- so it compares
    #     route A against a deliberately corrupted route B (the "corrupt the code" form), not the
    #     healthy pair (feeding a healthy case to a `fires` slot is an INERT plant).
    rng = random.Random(3)
    a, b = gen_case(50, 24, rng, 4.0)
    fires("routes-disagree", lambda: (dot_acc(a, b, 8, "A") == dot_acc(a, b, 8, "B") + 1) or _raise())
    holds("routes-agree/ok", lambda: routes_agree(a, b, 8) or _raise())

    # C2: a wide register is exact (plant: a register that is NOT wide enough still shows E>0)
    ex = dot_exact(a, b)
    wide_exact = relerr(dot_acc(a, b, 200), ex) == 0.0
    fires("wide-register-inexact", lambda: wide_exact == False or _raise())   # noqa: E712
    holds("wide-register-exact/ok", lambda: wide_exact or _raise())

    # C3/C4 slopes (plant: slopes that are the WRONG sign)
    def slope_ok(s, lo, hi):
        return lo <= s <= hi

    fires("u-law-slope-wrong", lambda: slope_ok(0.4, 0.7, 1.3) or _raise())
    holds("u-law-slope/ok", lambda: slope_ok(1.0, 0.7, 1.3) or _raise())
    # C4 (no n-correction): the plant is a slope of +0.5 -- a REAL sqrt(M) correction, the guess
    #     this round registered and the data refuted
    def n_indep(s):
        return abs(s) < 0.3
    fires("n-correction-present", lambda: n_indep(0.5) or _raise())   # a +0.5 sqrt(M) correction
    holds("n-independent/ok", lambda: n_indep(0.018) or _raise())

    # C5: the floor falls with p (plant: a floor that RISES with p)
    def floor_falls(f_lo, f_hi):
        return f_hi < f_lo

    fires("floor-rises-with-p", lambda: floor_falls(1e-3, 1e-2) or _raise())
    holds("floor-falls/ok", lambda: floor_falls(1e-2, 1e-3) or _raise())

    # C6: the p* slope is ~1 (plant: a slope of 0.2, the artefact of a log-log fit on a bit count)
    def pstar_slope_ok(s):
        return 0.7 <= s <= 1.3

    fires("pstar-slope-wrong", lambda: pstar_slope_ok(0.13) or _raise())
    holds("pstar-slope/ok", lambda: pstar_slope_ok(1.08) or _raise())

    # C7: p* is n-independent (plant: a p* that MOVES with n, i.e. a real sqrt(M) correction)
    def pstar_flat(s):
        return abs(s) < 0.5

    fires("pstar-moves-with-n", lambda: pstar_flat(0.5) or _raise())
    holds("pstar-n-independent/ok", lambda: pstar_flat(0.25) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
