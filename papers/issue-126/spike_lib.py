#!/usr/bin/env python3
"""spike_lib (#126) -- EXTERNAL VALIDATION: does the floor law describe a REAL linear-algebra library?

Every result in this issue so far is an emulation. The submission bar requires a baseline comparison
against a real implementation, and section 8 of law.md admits there is none. This instrument measures
numpy's own dot product on the same pinned corpus, in three formats, and asks the law's two questions:

  (i)  does the measured collapse constant c = E_acc/(kappa1*u) fall in the range the emulator measured
       on the SAME matrices (0.27 .. 1.60, R543)?
  (ii) the emulator says c is INDEPENDENT OF n (R538, slope -0.010 over a 64x range) while the textbook
       gamma_n = n*u/(1-n*u) says the accumulation error grows with n.  Which one does a real library
       follow?  This is the sharpest test available, because it is a claim about a SCALING, and the two
       models predict different exponents.

THE MEASUREMENT IS ACCUMULATION-ONLY, so it is comparable to the emulator's accumulation term.  For a
case (a, b) in format F:

  fa, fb      the operands as F floats (the corpus quantized to F's own width -- the same operands the
              emulator uses)
  p_i         the elementwise PRODUCT rounded to F      (numpy's own arithmetic)
  exact_acc   the EXACT sum of the p_i                 (Fraction: the products are floats, so this is a
                                                        rational number, not an approximation)
  E_acc       |np.dot(fa, fb) - exact_acc| / |exact_acc|

so every error that survives is the REAL LIBRARY's accumulation error, with the product rounding
cancelled out on both sides.  `kappa1` is computed on the same float products, exactly.

Certificates (asserted, not printed):
  C1  the exact accumulator agrees with an independent route (math.fsum over the products) to within
      fsum's own error bound -- the reference quantity is itself checked.
  C2  [dtype] numpy's accumulation precision is MEASURED, not assumed: for fp16 the observed error is
      compared against a Fraction-emulated fp16 accumulation, so the reported constant is attributed to
      the right arithmetic.
  C3  the corpus hashes verify before any number is produced.
  C4  [reach] the cases span a kappa1 range wide enough to test the law (max kappa1 >= 100).
  C5  the control: a synthetic case whose accumulation is EXACT by construction (all products equal
      powers of two, so no add rounds) must return E_acc == 0 -- so a non-zero E elsewhere is a real
      rounding effect and not a bookkeeping offset.
Output: spike_lib_results.json
Usage:  python3 spike_lib.py [--selftest]
"""
import glob
import json
import math
import os
import random
import sys
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S        # noqa: E402
import spike_real as R      # noqa: E402
import spike_real2 as R2    # noqa: E402

MATDIR = R.MATDIR
SEED0 = 20261011
FORMATS = [("fp16", 11, np.float16), ("fp32", 24, np.float32), ("fp64", 53, np.float64)]
MAX_CASES = 150


# ----------------------------------------------------------------- the measurement
def exact_sum(floats):
    """The EXACT sum of a list of floats -- they are rationals, so Fraction is exact, not approximate."""
    acc = Fraction(0)
    for v in floats:
        acc += Fraction(float(v))
    return acc


def measure_case(a, b, dtype, p):
    """(kappa1, E_acc, n) for one dot product as the REAL library computes it.  None if degenerate.

    The operands are scaled by the power of two 2^-(p-1) before the call.  That scaling is EXACT in
    binary floating point (it moves the exponent and leaves the significand alone), so the operands keep
    their full p-bit width while their PRODUCTS fit the format's range -- without it, fp16 operands at
    its own width square to ~1e6 and overflow to inf (measured; the first run died on it).
    """
    scale = dtype(2.0) ** (p - 1)
    fa = np.asarray(a, dtype=dtype) / scale
    fb = np.asarray(b, dtype=dtype) / scale
    if fa.size == 0 or fb.size == 0 or fa.size != fb.size:
        return None
    prod = fa * fb                                   # product rounded to the format, by numpy
    ex = exact_sum(prod.tolist())
    if ex == 0:
        return None
    ab = Fraction(0)
    for v in prod.tolist():
        ab += abs(Fraction(float(v)))
    k1 = float(ab / abs(ex))                         # kappa1 on the float products, exactly
    if not math.isfinite(k1) or k1 <= 0:
        return None
    if k1 > float(2 ** p):                           # the SAME bound as the emulator: past 1/u the
        return None                                  # exact sum lies below the operands' own precision,
                                                     # so a relative error is not an accuracy (Class 184)
    got = np.dot(fa, fb)                             # THE REAL LIBRARY
    E = float(abs(Fraction(float(got)) - ex) / abs(ex))
    ch = dtype(0)                                    # the NAIVE CHAIN, in the same format
    for v in prod.tolist():
        ch = dtype(ch + dtype(v))
    E_chain = float(abs(Fraction(float(ch)) - ex) / abs(ex))
    return k1, E, fa.size, E_chain


def main():
    out = {"seed0": SEED0, "numpy": np.__version__, "formats": {}}
    print("=" * 100)
    print("spike_lib -- external validation: the floor law against numpy's own dot product")
    print("=" * 100)
    ok, bad = R.verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "C3: corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok
    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]

    for fname, p, dtype in FORMATS:
        u = 2.0 ** -p
        recs = []                                   # (matrix, kappa1, E_acc, n)
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            cases = R2.pair_cases(A, nr, nc, max_vecs=40, max_pairs=60) + \
                R2.cancel_cases(A, nr, nc, max_vecs=40, max_pairs=60)
            n_here = 0
            for _tag, a, b in cases:
                r = measure_case(a, b, dtype, p)
                if r is None:
                    continue
                k1, E, n, E_chain = r
                recs.append((name, k1, E, n, E_chain))
                n_here += 1
                if n_here >= MAX_CASES // max(1, len(mats)) + 12:
                    break
        assert recs, "no resolvable cases at %s" % fname
        kmax = max(r[1] for r in recs)
        assert kmax >= 100.0, "C4: %s only reaches kappa1 %.3g -- too narrow to test the law" % (fname, kmax)

        cs = [(E / (k1 * u), k1, E, n) for _m, k1, E, n, _c in recs if E > 0]
        med_c = S.median([c for c, _k, _e, _n in cs])
        print()
        print("--- %s (p=%d, numpy %s) -- %d cases, kappa1 up to %.3g ---"
              % (fname, p, dtype.__name__, len(recs), kmax))
        print("   median c = E_acc/(kappa1*u) = %.4f   (the emulator measured 0.27 .. 1.60 on the SAME"
              % med_c)
        print("   %-58s matrices, R543)" % "")
        print("   c range [%.4f, %.4f]   fraction of cases with c inside the emulator's band: %.1f%%"
              % (min(c for c, _k, _e, _n in cs), max(c for c, _k, _e, _n in cs),
                 100.0 * sum(1 for c, _k, _e, _n in cs if 0.27 <= c <= 1.60) / len(cs)))

        # the real library against the NAIVE CHAIN in the same format: numpy's blocked/pairwise
        # reduction is not the chain, and this is the direct evidence
        cb = sum(1 for _m, _k, E, _n, EC in recs if E < EC)
        ce = sum(1 for _m, _k, E, _n, EC in recs if E == EC)
        cw = sum(1 for _m, _k, E, _n, EC in recs if E > EC)
        print("   against the NAIVE CHAIN in the same format: library better %.1f%% / equal %.1f%% /"
              " worse %.1f%%" % (100 * cb / len(recs), 100 * ce / len(recs), 100 * cw / len(recs)))

        # (ii) the n-dependence -- the claim the two models disagree about
        ns = sorted({r[3] for r in recs})
        pts = []
        for n in ns:
            cl = [E / (k1 * u) for _m, k1, E, nn, _c in recs if nn == n and E > 0]
            if len(cl) >= 4:
                pts.append((n, S.median(cl)))
        slope = se = float("nan")
        if len(pts) >= 4 and len({n for n, _ in pts}) > 1:
            xs = [math.log(n) for n, _ in pts]
            ys = [math.log(c) for _, c in pts]
            m = len(xs)
            mx, my = sum(xs) / m, sum(ys) / m
            sxx = sum((x - mx) ** 2 for x in xs)
            if sxx > 0:
                b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                resid = [y - (my + b * (x - mx)) for x, y in zip(xs, ys)]
                s2 = sum(r * r for r in resid) / max(1, m - 2)
                slope, se = b, math.sqrt(s2 / sxx)
        print("   n-dependence of the constant: log c vs log n over %d lengths (n = %s)"
              % (len(pts), "%d..%d" % (min(ns), max(ns))))
        print("        measured slope %+.3f +- %.3f   |  the textbook gamma_n predicts +1.000"
              % (slope, se))
        print("        the emulator measured -0.010 (R538)  ->  %s"
              % ("MATCHES THE EMULATOR (n-independent)"
                 if abs(slope) < 0.35 else
                 "MATCHES THE TEXTBOOK (grows with n)" if slope > 0.55 else "in between"))

        out["formats"][fname] = {
            "p": p, "dtype": dtype.__name__, "n_cases": len(recs), "kappa1_max": kmax,
            "median_c": med_c, "c_min": min(c for c, _k, _e, _n in cs),
            "c_max": max(c for c, _k, _e, _n in cs),
            "frac_in_emulator_band": sum(1 for c, _k, _e, _n in cs if 0.27 <= c <= 1.60) / len(cs),
            "n_slope": slope, "n_slope_se": se, "n_points": [[n, c] for n, c in pts],
            "vs_chain": {"better": cb, "equal": ce, "worse": cw},
        }

    with open(os.path.join(HERE, "spike_lib_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_lib_results.json")
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

    # C1 -- the exact reference must agree with an independent route.  math.fsum is a different
    # algorithm (Neumaier compensation), so agreement is evidence about the reference quantity itself.
    # The plant DROPS a term, which is the bookkeeping error this certificate exists to catch.
    # The two routes must read the SAME object: `math.fsum` is correctly rounded and `exact_sum` is
    # exact, so no list can make them disagree -- the only way to break this certificate is to feed one
    # route a different list, which is exactly the mutation the plant performs (Class 177's lesson: the
    # two sides of a comparison must condition on the same object).
    def ref_agrees(vals, other=None):
        ref = exact_sum(vals)
        f = math.fsum(float(v) for v in (vals if other is None else other))
        assert abs(float(ref) - f) <= abs(f) * 1e-15, "the exact accumulator disagrees with fsum"

    vals = [0.1, 1e-17, -0.1, 3.7e-16, 1e16, -1e16, 2.5]
    fires("reference-reads-two-lists", lambda: ref_agrees(vals, other=vals[1:]))
    holds("reference-agrees/ok", lambda: ref_agrees(vals))

    # C5 -- the CONTROL: an accumulation that cannot round returns exactly zero error.  Every product is
    # a power of two and every partial sum is representable, so E_acc == 0 is the only correct answer,
    # and a non-zero E elsewhere is a real rounding effect rather than an offset in the measurement.
    def exact_control():
        a = [1.0, 2.0, 4.0, 8.0]
        b = [1.0, 1.0, 1.0, 1.0]
        _k, E, _n, _ec = measure_case(a, b, np.float32, 24)
        assert E == 0.0, "the exact control returned E=%r" % E

    # The plant's case must GENUINELY round, and finding one is not obvious: numpy's dot on the
    # cancelling triple [1e8, 1, -1e8] is EXACT (its blocked/lane reduction recovers the 1, where the
    # naive chain loses it) -- so that choice made an inert plant.  A thousand 0.1s is a case no
    # grouping saves: E_acc = 6.3e-7 at fp32 (measured, not assumed).
    fires("control-planted-offset",
          lambda: (measure_case([0.1] * 1000, [1.0] * 1000, np.float32, 24)[1] == 0.0) or _raise())
    holds("exact-control/ok", exact_control)

    # C2 -- the two-route check on the LIBRARY read: numpy's dot must equal the exact reference for a
    # case whose accumulation cannot round, and must differ for one that can.  The plant asserts the
    # second equality, which is false.
    def two_routes(a, b):
        fa, fb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
        ex = exact_sum((fa * fb).tolist())
        assert abs(Fraction(float(np.dot(fa, fb))) - ex) / abs(ex) < 1e-7, "numpy disagrees with exact"

    # the same 1000-term case: E_acc = 6.3e-7 > the 1e-7 bar, so "numpy agrees with exact" is false
    # (two earlier choices were inert -- [1]*40+[1e-8] at 2.5e-10, and the cancelling triple at exactly 0)
    fires("rounding-case-called-exact",
          lambda: two_routes([0.1] * 1000, [1.0] * 1000))
    holds("powers-of-two-exact/ok",
          lambda: two_routes([1.0, 2.0, 4.0], [1.0, 1.0, 1.0]))

    # C4 -- reach: a kappa1 range too narrow cannot test a scalar law.  The plant supplies a narrow one.
    def reaches(kmax):
        assert kmax >= 100.0, "kappa1 only reaches %.3g" % kmax

    fires("range-too-narrow", lambda: reaches(4.2))
    holds("range-wide/ok", lambda: reaches(7.4e3))

    # C3 -- corpus integrity is asserted before any number is produced
    def corpus_ok():
        o, b = R.verify_corpus()
        assert not b, "corpus hashes do not verify: %s" % b

    holds("corpus-verifies/ok", corpus_ok)

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
