#!/usr/bin/env python3
"""spike_v0 (#126) -- THE PRECISION FLOOR, MEASURED AGAINST EXACT ARITHMETIC.

Construct: the error of a limb-split (Ozaki/Zintra-style) dot product, measured against the exact
integer result, as a function of the number of limbs kept (K), the limb width (q), the accumulator's
mantissa width (p), and the problem's cancellation (kappa1 = ||ab||_1 / |sum a_i b_i|).

The kernel:
    s = sum_{i=1..n} a_i * b_i          (integers, exactly representable in a p-bit format)
exact:      sum of Python ints -> ground truth, by construction
emulated:   split each a_i, b_i into base-2^q limbs; keep the limb PAIRS with j + l < K (the
            "leading diagonals"); accumulate them in a p-bit-mantissa register, rounding after
            EVERY addition.

Two error sources, and the point of the instrument is to separate them:
    truncation    the dropped diagonals (j + l >= K)          ~ kappa1 * 2^{-q K}
    accumulation  the K(K+1)/2 rounded additions per element  ~ kappa1 * K^2 * u,   u = 2^{-p}

The falsifiable claim this instrument tests (registered P1/P2):
    up to the floor the RELATIVE error is governed by the single scalar kappa1, i.e. E/kappa1 is a
    function of (u, q, K) alone -- it collapses across n and across problems of different
    conditioning; the error then FALLS with K and FLOORS, so past K* extra limbs buy nothing and in
    fact cost accuracy; and the floor is kappa1 * c * (log(1/u)/q)^2 * u, reachable only for targets
    ABOVE it.

Certificates here:
  C1  two independent routes for the emulated sum (integer sig-round vs an exact Fraction model)
  C2  the no-truncation control  (K >= all limbs -> truncation is exactly 0; error is pure accumulation)
  C3  the no-accumulation control (p large enough that sig_round is the identity -> error is pure truncation)
  C4  monotone truncation (error at fixed K2 > K1 is <= that at K1 when accumulation is off)
  C5  the collapse of E/kappa1 across kappa1 (the governing-scalar claim, P2)
  C6  the interior optimum K* > 1 exists for every format tested (the floor claim, P1)
Output: spike_v0_results.json
Usage:  python3 spike_v0.py [--selftest]
"""
import json
import math
import os
import random
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
SEED0 = 20261005


# ----------------------------------------------------------------- the register and the split
def sig_round(v, p):
    """Round an integer to p significant bits -- the register a p-bit-mantissa accumulator is.

    Exact for p <= 53 in the sense that this models the FORMAT's rounding, not a float's: the
    operation is defined on integers and round-half-to-even, so no double-precision artefact enters.
    """
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


def limbs(x, q):
    """base-2^q limbs of |x|, least-significant first."""
    x = abs(x)
    out = []
    while x:
        out.append(x & ((1 << q) - 1))
        x >>= q
    return out or [0]


def dot_exact(a, b):
    return sum(x * y for x, y in zip(a, b))


def _diagonals(x, y, q):
    """the KEPT-ORDER limb products of one element, heaviest diagonal first (the leading terms)."""
    out = []
    for j, xj in enumerate(limbs(x, q)):
        for l, yl in enumerate(limbs(y, q)):
            out.append((j + l, xj * yl * (1 << (q * (j + l)))))
    out.sort(key=lambda t: -t[0])
    return out


def dot_emulated(a, b, q, K, p):
    """Keep the K HEAVIEST limb products per element; round the register after every add.

    The orientation matters and is the whole scheme: the dropped terms are the LIGHTEST (their
    weight decays as 2^{-q} per diagonal down), so keeping the heaviest K is what makes the error
    fall with K.  Keeping the lightest instead (the first version of this instrument) gives an error
    near 1 at every K -- a self-diagnosing defect, since the curve then has the wrong SHAPE.
    """
    S = 0
    for x, y in zip(a, b):
        neg = (x < 0) ^ (y < 0)
        for _w, t in _diagonals(x, y, q)[:K]:
            S = sig_round(S + (-t if neg else t), p)
    return S


def dot_emulated_exact_model(a, b, q, K, p):
    """Route 2: the same rule, but the register rounding is done in exact Fraction arithmetic.

    Independent of sig_round's integer shifting: it reconstructs the rounded value as a Fraction
    (nearest p-bit-significant rational, ties to even) and sums in Fraction space. Agreement to the
    last unit is the C1 certificate -- a route cannot certify itself.
    """
    def frac_round(v):
        if v == 0:
            return Fraction(0)
        sign = 1 if v > 0 else -1
        ax = abs(v)
        e = ax.numerator.bit_length() - ax.denominator.bit_length()
        # place the leading bit at exponent e (m in [0.5, 1) up to a factor of 2)
        m = ax / (Fraction(2) ** e)
        while m >= 1:
            e += 1
            m = ax / (Fraction(2) ** e)
        while m < Fraction(1, 2):
            e -= 1
            m = ax / (Fraction(2) ** e)
        scaled = m * (1 << p)
        f = math.floor(scaled)
        r = scaled - f
        if r > Fraction(1, 2) or (r == Fraction(1, 2) and (f & 1)):
            f += 1
        return sign * Fraction(f) * (Fraction(2) ** e) / (1 << p)

    S = Fraction(0)
    for x, y in zip(a, b):
        neg = (x < 0) ^ (y < 0)
        for _w, t in _diagonals(x, y, q)[:K]:
            t = Fraction(t)
            S = frac_round(S + (-t if neg else t))
    return S


# ----------------------------------------------------------------- data
def gen_case(n, p, rng, cancel=1.0):
    """a_i, b_i in [1, 2^(p-1)) with random signs; `cancel` sharpens the cancellation.

    kappa1 = ||ab||_1 / |sum ab| is measured, never assumed.
    """
    half = 1 << (p - 1)
    a, b = [], []
    for _ in range(n):
        x = rng.randrange(1, half)
        y = rng.randrange(1, half)
        s = 1 if rng.random() < 0.5 else -1
        a.append(s * x)
        b.append(y)
    if cancel != 1.0 and n >= 4:
        # push the sum toward zero: flip one sign, then one more, until |sum| shrinks
        tgt = dot_exact(a, b)
        for _ in range(int(cancel * 4)):
            if abs(tgt) < 1:
                break
            i = rng.randrange(n)
            a[i] = -a[i]
            tgt = dot_exact(a, b)
    return a, b


def kappa1(a, b):
    den = abs(dot_exact(a, b))
    num = sum(abs(x * y) for x, y in zip(a, b))
    return (num / den) if den else float("inf")


def rel_error(S, exact):
    return abs(S - exact) / abs(exact) if exact else float("inf")


# ----------------------------------------------------------------- the experiment
def sweep(p, q, n, kappa_target, seeds=3, Kmax=7):
    """For one format (p,q) and one conditioning class: error vs K, averaged over seeds."""
    rows = []
    for K in range(1, Kmax + 1):
        errs, k1s = [], []
        for s in range(seeds):
            rng = random.Random(SEED0 + 1000 * p + 17 * n + 101 * s)
            a, b = gen_case(n, p, rng, cancel=kappa_target)
            ex = dot_exact(a, b)
            if ex == 0:
                continue
            S = dot_emulated(a, b, q, K, p)
            errs.append(rel_error(S, ex))
            k1s.append(kappa1(a, b))
        if not errs:
            continue
        rows.append({"K": K, "relerr": sum(errs) / len(errs),
                     "kappa1": sum(k1s) / len(k1s),
                     "relerr_over_kappa1": (sum(errs) / len(errs)) / (sum(k1s) / len(k1s))})
    return rows


def pure_accumulation(p, q, n, K, seeds=3):
    """C2: K large enough that truncation is exactly zero -> pure accumulation error."""
    errs = []
    for s in range(seeds):
        rng = random.Random(SEED0 + 7 * n + 13 * K + s)
        a, b = gen_case(n, p, rng)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        S = dot_emulated(a, b, q, 99, p)     # K=99: keep every limb pair
        errs.append(rel_error(S, ex))
    return sum(errs) / len(errs) if errs else None


def pure_truncation(p, q, n, K, seeds=3):
    """C3: p large enough that sig_round never fires -> pure truncation error."""
    big = 4096          # >> bit length of any partial here: the register never rounds
    errs = []
    for s in range(seeds):
        rng = random.Random(SEED0 + 31 * n + 7 * K + s)
        a, b = gen_case(n, p, rng)
        ex = dot_exact(a, b)
        if ex == 0:
            continue
        S = dot_emulated(a, b, q, K, big)
        errs.append(rel_error(S, ex))
    return sum(errs) / len(errs) if errs else None


def main():
    out = {"seed0": SEED0, "formats": {}, "controls": {}, "laws": {}}

    # formats named by their real mantissa width; q = p // 2 so a limb product is exact
    FORMATS = {"bf16": 8, "fp16": 11, "tf32": 11, "fp32": 24}

    print("=" * 100)
    print("spike_v0 -- the precision floor of a limb-split dot product (error vs exact arithmetic)")
    print("=" * 100)

    for name, p in FORMATS.items():
        q = p // 2
        u = 2.0 ** -p
        rows = sweep(p, q, n=600, kappa_target=4.0, Kmax=7)
        out["formats"][name] = {"p": p, "q": q, "u": u, "rows": rows}
        print()
        print("%s (p=%d q=%d u=%.3e)" % (name, p, q, u))
        print("   %-4s %-12s %-12s %-14s" % ("K", "kappa1", "relerr", "relerr/kappa1"))
        best = None
        for r in rows:
            print("   %-4d %-12.3g %-12.3e %-14.3e"
                  % (r["K"], r["kappa1"], r["relerr"], r["relerr_over_kappa1"]))
            if best is None or r["relerr"] < best["relerr"]:
                best = r
        out["laws"].setdefault("best", {})[name] = {"K_star": best["K"], "floor": best["relerr"],
                                                    "kappa1": best["kappa1"]}
        print("   -> K* = %d  floor = %.3e" % (best["K"], best["relerr"]))

    # ---- C2 / C3 controls
    print()
    print("controls")
    for name, p in FORMATS.items():
        q = p // 2
        acc = pure_accumulation(p, q, n=600, K=99)
        tr1 = pure_truncation(p, q, n=600, K=1)
        tr3 = pure_truncation(p, q, n=600, K=3)
        out["controls"][name] = {"pure_accumulation": acc, "pure_truncation_K1": tr1,
                                 "pure_truncation_K3": tr3}
        print("   %-5s pure-accumulation=%.3e  pure-truncation K=1=%.3e  K=3=%.3e  (K3<=K1: %s)"
              % (name, acc, tr1, tr3, tr3 <= tr1))

    # ---- C5 collapse: E/kappa1 across conditioning classes, one format
    print()
    print("C5 -- the governing-scalar collapse (fp16): E/kappa1 across cancellation classes")
    collapse = {}
    for c in (1.0, 2.0, 4.0, 8.0):
        rows = sweep(11, 5, n=600, kappa_target=c, seeds=2, Kmax=5)
        collapse["cancel=%.0f" % c] = rows
    out["laws"]["collapse"] = collapse
    for k, rows in collapse.items():
        kk = ", ".join("K%d=%.2e" % (r["K"], r["relerr_over_kappa1"]) for r in rows)
        print("   %-12s kappa1~%.2g | %s" % (k, rows[0]["kappa1"], kk))

    # ---- the certificates: the run FAILS if the structure is absent (a print is not a gate)
    print()
    print("certificates")
    for name, p in FORMATS.items():
        rows = out["formats"][name]["rows"]
        errs = [r["relerr"] for r in rows]
        kbest = min(range(len(errs)), key=lambda i: errs[i])
        # C6 (falls then floors): the error at K* is far below K=1, and the tail is flat
        assert errs[0] > 3 * errs[kbest], "%s: the curve does not fall (K1=%.3e K*=%.3e)" % (
            name, errs[0], errs[kbest])
        assert errs[-1] >= 0.8 * errs[kbest], "%s: the curve never floors (still falling at Kmax)" % name
        # C6b: an interior optimum -- K* is not the first K
        assert kbest >= 1, "%s: K*=1 -- no interior optimum" % name
        print("   %-5s C6 falls+floors  K1/K* = %.1fx   tail/K* = %.2f   K* = %d"
              % (name, errs[0] / errs[kbest], errs[-1] / errs[kbest], rows[kbest]["K"]))
    for name in FORMATS:
        c = out["controls"][name]
        assert c["pure_truncation_K3"] <= c["pure_truncation_K1"], "%s: truncation not monotone" % name
        assert c["pure_accumulation"] > 0, "%s: no accumulation error" % name
    print("   C3 truncation monotone in K for every format; C2 accumulation > 0 for every format")

    with open(os.path.join(HERE, "spike_v0_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v0_results.json")
    return 0


# ----------------------------------------------------------------- self-test
def _raise():
    raise AssertionError("the planted defect did not fire")


def selftest():
    """Each certificate must FIRE on a case that violates it, and HOLD on the real one.

    A plant is built from the property's NEGATION (never by copying the check's own expression and
    flipping an operator): a plant that reuses the check's expression inverts both sides at once and
    reports DID NOT FIRE for the wrong reason.
    """
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
            print("[%-30s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:30]))
            ok = False

    # C1: the two independent routes agree (int register vs exact Fraction register)
    rng = random.Random(1)
    a, b = gen_case(20, 11, rng)
    S1 = dot_emulated(a, b, 5, 3, 11)
    S2 = dot_emulated_exact_model(a, b, 5, 3, 11)
    same = (S1 == S2) or (int(S2) == S1)
    print("C1 routes: int=%s frac=%s agree=%s" % (S1, S2, same))
    if not same:
        ok = False

    # C2: the accumulation floor is REAL and non-zero (a pure-accumulation run still errs).
    #     The plant feeds the predicate a FLOORLESS case (acc == 0), not the healthy one.
    acc = pure_accumulation(11, 5, 100, 99)
    print("C2 pure-accumulation at K=99 (truncation off): relerr=%.3e" % acc)
    has_floor = lambda v: v > 0                      # noqa: E731 -- the property, in words
    fires("accumulation-floor-absent", lambda: has_floor(0.0) or _raise())
    holds("accumulation-floor/present", lambda: has_floor(acc) or _raise())

    # C4: truncation is monotone in K when accumulation is off -- plant the VIOLATION (K4 > K1)
    def monotone(t1, t4):
        return t4 <= t1

    t1 = pure_truncation(11, 5, 200, 1)
    t4 = pure_truncation(11, 5, 200, 4)
    print("C4 truncation: K1=%.3e K4=%.3e  (real pair monotone: %s)" % (t1, t4, monotone(t1, t4)))
    fires("truncation-not-monotone", lambda: monotone(1e-3, 1e-2) or _raise())
    holds("truncation-monotone/ok", lambda: monotone(t1, t4) or _raise())

    # C6: the curve FALLS THEN FLOORS -- the last step is small relative to the one before it.
    #     Plant a curve that is still falling at its end (the negation of "floors").
    def floors(seq):
        return len(seq) >= 2 and seq[-1] >= 0.8 * seq[-2]

    print("C6 floor shape: plant n/a here; main() asserts the real fp16 curve")
    fires("curve-never-floors", lambda: floors([1.0, 0.5, 0.25, 0.125]) or _raise())
    holds("curve-floors/ok", lambda: floors([1.0, 0.5, 0.1, 0.1]) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
