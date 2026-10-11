#!/usr/bin/env python3
"""spike_struct (#126, R549) -- the second scalar, re-posed as a STRUCTURE question.

R544 refuted the path-statistic family (prior P4) as the second scalar, and R548 found a real library
BETTER than both the naive chain and the issue's 4-lane model, on a three-term cancellation where both
models returned 0.0 and numpy returned 1.0.  Together those imply a question this issue has not asked:
is the missing quantity a MATRIX STATISTIC at all, or is it the REDUCTION STRUCTURE?

R549's own pre-run probe answers a piece of that, and it CORRECTS R548's reading of its own headline.
On [1e8, 1, -1e8] at fp32:

    np.dot             = 1.0   (exact)
    np.sum(a*b)        = 0.0
    naive chain        = 0.0
    recursive pairwise = 0.0
    n = 2      -> 0.0
    n = 3      -> 1.0      <-- the ONLY n that is exact
    n = 4..11  -> 0.0
    mid = 0.1  -> 0.1f, i.e. the result equals the EXACT fp64 sum rounded to fp32

so the library is exact there not because it accumulates in higher precision (n=4, same magnitudes,
comes out 0.0 -- which extended precision could not do) but because its lane geometry pairs the two
huge terms with EACH OTHER before the small one.  With accumulators (s0,s1,s2,s3) and a stride-halving
horizontal reduce the combination is (s0+s2)+(s1+s3) = (1e8-1e8)+(1+0) = 1.0, while a serial chain and a
recursive halving both add 1 to 1e8 first and lose it.  At n=4 the vector is full, the 1 is absorbed
inside a lane, and the exactness disappears.  So "the library has better structure" stands; R548's
sentence naming it "blocked/pairwise" names the wrong mechanism, and this instrument tests the right one.

READINGS
  Q1  structure identification -- emulate the named structures IN FORMAT, all on the SAME product list in
      the SAME order (the encoding matters, Class 172), and ask which reproduces the library's own
      per-case accumulation error: chain, recursive pairwise, lanes(L) for L in {2,4,8,16}, numpy's own
      block-128/8-lane pairwise-sum, and Kahan as a near-exact control.
  Q2  the between-matrix spread at fixed kappa1 (R543: 3.1-5.8x) was measured on the CHAIN.  Does it
      survive under the structure that fits the library?  If it collapses, the "second scalar" was a
      chain artefact; if it survives, the second scalar is real and the structure is not its name.
  Q3  the order axis (R544: 77.9x/209.6x fp32 over 24 element orders) was also a chain measurement.
      Does a lane structure remove the order sensitivity?  The mechanism claim ("a serial chain is a
      recurrence, so order matters") predicts a large reduction; a refutation is the STRONGER statement.

CERTIFICATES (asserted, not printed -- each one can fail)
  C1  the corpus hashes verify before any number is produced.
  C2  the exact reference agrees with an independent route (math.fsum) read on the SAME list.
  C3  every structure consumes the SAME product list (the comparison is of structures, not of terms).
  C4  the EXACT control: a power-of-two case cannot round, so E == 0 for every structure.
  C5  the LANE-GEOMETRY control -- the instrument's positive control: on the measured triple,
      chain == pairwise == 0.0 and lanes(2) == lanes(4) == 1.0 == the library.  An instrument that
      cannot see the difference it exists to measure is decoration.
  C6  REACH: the structure family must differ from the chain on the corpus, or Q1 has no object.
  C7  kappa1 <= 2^p (Class 184/189: the bound comes from the metric's meaning and applies wherever the
      metric is computed -- including the struct and order arms below).
  C8  implementation sanity, two-sided: a correct Kahan/reduction structure is never much WORSE than the
      chain.  Failing C8 indicts the EMULATION, not the library (Class 181).
Output: spike_struct_results.json
Usage:  python3 spike_struct.py [--quick] [--selftest]
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
SEED0 = 20261012
FORMATS = [("fp16", 11, np.float16), ("fp32", 24, np.float32), ("fp64", 53, np.float64)]
LANE_SET = (2, 4, 8, 16)
MAX_CASES = 150                 # per format, the same shape as spike_lib
ORDER_MATS = 3                  # matrices in the order arm
ORDER_PERMS = 16                # permutations per case
BAND_LO, BAND_HI = 1.0, 1.5     # R543's fixed-kappa1 band for the between-matrix spread
MIN_LIVE = 8                    # a case with fewer live products has no accumulation to study (measured)


# ----------------------------------------------------------------- the structures
def _acc(dt, s, v):
    """One add, rounded to the format.  Every structure below accumulates only through this."""
    return dt(dt(s) + dt(v))


def sum_chain(vals, dt):
    """One accumulator, left to right -- the serial recurrence of the naive model."""
    s = dt(0)
    for v in vals:
        s = _acc(dt, s, v)
    return s


def sum_pairwise(vals, dt):
    """Recursive halving: (v0+v1)+(v2+v3) ... at every level."""
    cur = [dt(v) for v in vals]
    while len(cur) > 1:
        nxt = [_acc(dt, cur[i], cur[i + 1]) for i in range(0, len(cur) - 1, 2)]
        if len(cur) % 2:
            nxt.append(cur[-1])
        cur = nxt
    return cur[0] if cur else dt(0)


def sum_lanes(vals, dt, L):
    """L accumulators filled round-robin (the shape of a SIMD loop), then a STRIDE-HALVING horizontal
    reduce: s[i] += s[i+h] for h = L/2, L/4, ..., 1.  For L=4 that combines (s0+s2) before (s1+s3),
    which is the pairing the R549 probe measured on the library."""
    s = [dt(0)] * L
    for i, v in enumerate(vals):
        j = i % L
        s[j] = _acc(dt, s[j], v)
    h = L
    while h > 1:
        h //= 2
        for i in range(h):
            s[i] = _acc(dt, s[i], s[i + h])
    return s[0]


def sum_numpy_pairwise(vals, dt, blk=128, u=8):
    """numpy's npy_pairwise_sum: recursive halving down to blocks of `blk`, and inside a block a u-way
    unrolled loop over u accumulators combined by the same stride-halving tree."""
    def rec(lo, hi):
        n = hi - lo
        if n <= blk:
            r = [dt(0)] * u
            i = lo
            while i + u <= hi:
                for j in range(u):
                    r[j] = _acc(dt, r[j], vals[i + j])
                i += u
            while i < hi:
                r[0] = _acc(dt, r[0], vals[i])
                i += 1
            h = u
            while h > 1:
                h //= 2
                for j in range(h):
                    r[j] = _acc(dt, r[j], r[j + h])
            return r[0]
        half = lo + (hi - lo) // 2
        return _acc(dt, rec(lo, half), rec(half, hi))

    return rec(0, len(vals)) if vals else dt(0)


def sum_kahan(vals, dt):
    """Compensated summation -- near-exact, the control that shows what a good algorithm looks like when
    the format is the only limit."""
    s = dt(0)
    c = dt(0)
    for v in vals:
        y = dt(dt(v) - c)
        t = _acc(dt, s, y)
        c = dt(dt(dt(t - s)) - y)
        s = t
    return s


STRUCTS = [("chain", sum_chain), ("pairwise", sum_pairwise), ("kahan", sum_kahan)]
STRUCTS += [("lanes%d" % L, (lambda v, dt, L=L: sum_lanes(v, dt, L))) for L in LANE_SET]
STRUCTS += [("numpy_pairwise", sum_numpy_pairwise)]
STRUCT_NAMES = [n for n, _ in STRUCTS]
PERM = dict(STRUCTS)
# the family that may FIX the library's per-case behaviour (kahan is a control, not a candidate fit)
CANDIDATES = ["chain", "pairwise"] + ["lanes%d" % L for L in LANE_SET] + ["numpy_pairwise"]


# ----------------------------------------------------------------- the measurement
def relerr(got, ex):
    return float(abs(Fraction(float(got)) - ex) / abs(ex))


def exact_sum(floats):
    acc = Fraction(0)
    for v in floats:
        acc += Fraction(float(v))
    return acc


def kappa1_of(prods):
    ab = Fraction(0)
    for v in prods:
        ab += abs(Fraction(float(v)))
    return ab


def measure(a, b, dt, p, stats=None):
    """One case.  Returns (n, kappa1, n_live, {structure: E}, E_numpy) or None if degenerate.

    The operands are scaled by 2^-(p-1) -- exact in binary FP, significand untouched -- so full-width
    operands fit the format's range (the fp16 overflow R548 measured).

    MIN_LIVE is the case filter this round had to add, and the reason is measured, not assumed: the
    corpus is INTEGER-valued after quantize(), and a SuiteSparse column pair shares only 2-3 nonzero
    entries, so 128 of a 130-term dot product are zeros.  With 2 live terms there is no accumulation,
    every structure is trivially exact, and a "which structure matches the library" table built on such
    cases is a table about nothing (measured: all 7 structures identical, med|lr| = 0.000).  A case
    below MIN_LIVE is dropped and COUNTED, so the report carries its own exclusion rate (Class 184).
    """
    scale = dt(2.0) ** (p - 1)
    fa = np.asarray(a, dtype=dt) / scale
    fb = np.asarray(b, dtype=dt) / scale
    if fa.size == 0 or fa.size != fb.size:
        return None
    prods = (fa * fb).tolist()               # the products, rounded by the library, ONE list
    live = sum(1 for v in prods if v != 0)
    if live < MIN_LIVE:
        if stats is not None:
            stats["few_live"] = stats.get("few_live", 0) + 1
        return None
    ex = exact_sum(prods)
    if ex == 0:
        if stats is not None:
            stats["exact_zero"] = stats.get("exact_zero", 0) + 1
        return None
    ab = kappa1_of(prods)
    k1 = float(ab / abs(ex))
    if not math.isfinite(k1) or k1 <= 0 or k1 > float(2 ** p):
        if stats is not None:
            stats["past_bound"] = stats.get("past_bound", 0) + 1
        return None                          # C7 -- past 1/u a relative error is not an accuracy
    got = np.dot(fa, fb)
    errs = {name: relerr(fn(prods, dt), ex) for name, fn in STRUCTS}
    return fa.size, k1, live, errs, relerr(got, ex)


# ----------------------------------------------------------------- the lane-geometry control
CTRL_M = {11: 8192.0, 24: 1e8, 53: 1e17}   # smallest magnitude whose ulp exceeds 1, per format


def lane_control(dt, p, M, mid=1.0, extra_zero=False):
    """The instrument's positive control, on a SYNTHETIC case -- deliberately outside C7's regime (its
    kappa1 is ~2M/mid >> 2^p, so the exact sum lies below the operands' own ulp and a relative-accuracy
    statement about it is not meaningful; that is itself a reading, returned as kappa1).  It exists to
    show that the instrument SEES a geometry difference at all.

    Returns (kappa1, n, {structure: E}, E_library).
    """
    a = np.array([M, mid, -M], dtype=dt) if not extra_zero else np.array([M, 0.0, mid, -M], dtype=dt)
    b = np.ones(a.size, dtype=dt)
    prods = (a * b).tolist()
    ex = exact_sum(prods)
    k1 = float(kappa1_of(prods) / abs(ex))
    errs = {name: relerr(fn(prods, dt), ex) for name, fn in STRUCTS}
    return k1, a.size, errs, relerr(np.dot(a, b), ex)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


# ----------------------------------------------------------------- the order arm
def order_arm(mats, p, dt, rng, max_cases=5):
    """Permute only the element ORDER of one case and re-measure every structure AND the library.

    kappa1 is a function of the terms alone, so it is invariant under the permutation; the exact sum is
    invariant too.  What moves is the accumulated error -- and by how much is the reading.

    The case selection is MEASURED, and this is the second thing this round had to fix: most corpus
    cases are exactly accumulated by every structure in every order, so max/min is undefined on them
    (the first run printed nan for fp16 AND fp32).  A case is used only if the CHAIN has >= 2 positive
    errors over the permutations -- i.e. only if there is an order effect to measure -- and the cases
    dropped for that reason are counted (Class 184: report the exclusion rate).
    """
    structs = ("chain", "pairwise", "lanes4", "library")
    spread = {nm: [] for nm in structs}
    worst = {nm: [] for nm in structs}
    used = skipped = 0
    for _name, path in mats:
        if used >= max_cases:
            break
        nr, nc, ent = R.load_mtx(path)
        A, _sc = R.quantize(nr, nc, ent, p)
        for _tag, a, b in R2.pair_cases(A, nr, nc, max_vecs=40, max_pairs=60):
            if used >= max_cases:
                break
            if len(a) != len(b) or not a:
                continue                      # the corpus generator emits pairs of unequal length
            scale = dt(2.0) ** (p - 1)
            fa = np.asarray(a, dtype=dt) / scale
            fb = np.asarray(b, dtype=dt) / scale
            prods = (fa * fb).tolist()
            if sum(1 for v in prods if v != 0) < MIN_LIVE:
                continue                      # the same live-term filter
            ex = exact_sum(prods)
            if ex == 0:
                continue
            k1 = float(kappa1_of(prods) / abs(ex))
            if not math.isfinite(k1) or k1 <= 0 or k1 > float(2 ** p):
                continue                      # C7 on this arm too
            cs = {nm: [] for nm in structs}
            idx = list(range(fa.size))
            for _ in range(ORDER_PERMS):
                rng.shuffle(idx)
                pp = [prods[i] for i in idx]
                cs["chain"].append(relerr(sum_chain(pp, dt), ex))
                cs["pairwise"].append(relerr(sum_pairwise(pp, dt), ex))
                cs["lanes4"].append(relerr(sum_lanes(pp, dt, 4), ex))
                cs["library"].append(relerr(np.dot(fa[idx], fb[idx]), ex))
            pos = [v for v in cs["chain"] if v > 0]
            if len(pos) < 2:
                skipped += 1                  # every order exact (or a single positive): no object
                continue
            for nm in structs:
                vals = [v for v in cs[nm] if v > 0]
                if len(vals) >= 2:
                    spread[nm].append(max(vals) / min(vals))
                worst[nm].append(max(cs[nm]))
            used += 1
    med = {nm: (S.median(v) if v else float("nan")) for nm, v in spread.items()}
    med.update({("worst_" + nm): (S.median(v) if v else float("nan")) for nm, v in worst.items()})
    med["_used"] = used
    med["_skipped_no_order_effect"] = skipped
    return med


# ----------------------------------------------------------------- main
def main(argv):
    quick = "--quick" in argv
    rng = random.Random(SEED0)
    out = {"seed0": SEED0, "numpy": np.__version__, "lane_set": list(LANE_SET), "formats": {},
           "lane_control": {}}
    print("=" * 104)
    print("spike_struct -- is the missing second scalar a MATRIX STATISTIC or a REDUCTION STRUCTURE?")
    print("=" * 104)
    ok, bad = R.verify_corpus()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "C1: corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok

    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    if quick:
        mats = mats[:3]
    out["matrices"] = [n for n, _ in mats]

    # ---- C5: the lane-geometry control, before anything it licenses
    print()
    print("C5 lane-geometry control (synthetic; its kappa1 is reported because it is outside C7)")
    for fname, p, dt in FORMATS:
        M = CTRL_M[p]
        k1, n, errs, E_lib = lane_control(dt, p, M)
        k1b, nb, errsb, E_libb = lane_control(dt, p, M, extra_zero=True)
        print("   %-5s M=%-9g n=%d kappa1=%.3g | relerr: chain=%.3f pairwise=%.3f lanes2=%.3f "
              "lanes4=%.3f LIBRARY=%.3f" % (fname, M, n, k1, errs["chain"], errs["pairwise"],
                                             errs["lanes2"], errs["lanes4"], E_lib))
        assert errs["chain"] == 1.0, ("C5: the chain is maximally wrong here (relerr 1.0, the small "
                                      "term is lost) -- if not, the rounding discipline is broken")
        assert errs["pairwise"] == 1.0, "C5: recursive halving loses it too (relerr 1.0)"
        assert errs["lanes2"] == 0.0, "C5: lanes2 did not recover it -- the emulation, not the library"
        assert errs["lanes4"] == 0.0, "C5: lanes4 did not recover it"
        out["lane_control"][fname] = {
            "M": M, "kappa1": k1, "n": n, "E_library": E_lib,
            "n4": {"kappa1": k1b, "n": nb, "E_library": E_libb, "lanes4": errsb["lanes4"],
                   "chain": errsb["chain"]},
            "struct": {nm: errs[nm] for nm in STRUCT_NAMES},
        }
        print("          the library is EXACT here: %s   (n=4 leg: library relerr %s, lanes4 %s)"
              % ("YES" if E_lib == 0.0 else "NO -- measured, and it is the fp64 finding",
                 E_libb, errsb["lanes4"]))

    for fname, p, dt in FORMATS:
        u = 2.0 ** -p
        stats = {}
        recs = []
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            cases = R2.pair_cases(A, nr, nc, max_vecs=40, max_pairs=60) + \
                R2.cancel_cases(A, nr, nc, max_vecs=40, max_pairs=60)
            n_here = 0
            for _tag, a, b in cases:
                r = measure(a, b, dt, p, stats)
                if r is None:
                    continue                     # the filters (live terms, C7) are applied inside
                n, k1, live, errs, E_lib = r
                recs.append({"matrix": name, "n": n, "kappa1": k1, "live": live, "errs": errs,
                             "E_lib": E_lib})
                n_here += 1
                if n_here >= max(1, MAX_CASES // max(1, len(mats))) + (6 if quick else 12):
                    break
        assert recs, "no resolvable cases at %s" % fname
        kmax = max(r["kappa1"] for r in recs)
        # the reach bar is a declared parameter of the RUN (a 3-matrix smoke run cannot carry the same
        # kappa1 range as the 14-matrix corpus, and pretending otherwise would be a bar with no power)
        reach_min = 10.0 if quick else 100.0
        assert kmax >= reach_min, \
            "reach: %s only reaches kappa1 %.3g (bar %.1f, %s run)" % (fname, kmax, reach_min,
                                                                      "quick" if quick else "full")
        nz_lib = sum(1 for r in recs if r["E_lib"] == 0)
        distinct = len({round(r["E_lib"], 12) for r in recs})
        assert distinct >= 3, ("C9: the library's measured error takes only %d distinct values -- a "
                               "constant instrument" % distinct)
        print()
        lv = sorted(r["live"] for r in recs)
        print("--- %s (p=%d, %s) -- %d cases, kappa1 up to %.3g, live products %d..%d (median %d), "
              "library exactly right on %d ---"
              % (fname, p, dt.__name__, len(recs), kmax, lv[0], lv[-1], S.median(lv), nz_lib))
        print("      case filters: dropped %d few-live (<%d), %d exact-zero, %d past the kappa1 bound"
              % (stats.get("few_live", 0), MIN_LIVE, stats.get("exact_zero", 0),
                 stats.get("past_bound", 0)))

        # ---- Q1: which structure reproduces the library's per-case error?
        # THE OBJECT IS THE SUBSET WHERE THE LIBRARY ROUNDS.  Most corpus cases accumulate exactly in
        # every structure (measured below), so a comparison over all of them reports "every structure
        # matches, med|lr| = 0.000" -- a table about nothing (a statistic identical in most cells is
        # resolving nothing).  c_struct / c_library == E_struct / E_library case by case (same kappa1,
        # same u), so a log-ratio in E is a log-ratio in c: the encoding is shared by design.
        lib_rounds = [r for r in recs if r["E_lib"] > 0]
        lib_exact = [r for r in recs if r["E_lib"] == 0]
        print("   the library ROUNDS on %d of %d cases (exact on %d) -- Q1 runs on the first set"
              % (len(lib_rounds), len(recs), len(lib_exact)))
        assert len(lib_rounds) >= (1 if quick else 5), \
            "Q1 has no object: the library rounds on only %d cases" % len(lib_rounds)
        rows = []
        for nm in CANDIDATES:
            lr, exact_s, zero_s, fewer, ex_when_lib_exact = [], 0, 0, 0, 0
            for r in lib_rounds:
                e_s, e_l = r["errs"][nm], r["E_lib"]
                if e_s == 0:
                    zero_s += 1
                else:
                    lr.append(abs(math.log2(e_s / e_l)))
                    if e_s < e_l:
                        fewer += 1
                if abs(e_s - e_l) <= 1e-12 * max(e_s, e_l):
                    exact_s += 1
            for r in lib_exact:
                if r["errs"][nm] == 0:
                    ex_when_lib_exact += 1
            nearest = 0
            for r in lib_rounds:
                e_l = r["E_lib"]
                live = [(m, r["errs"][m]) for m in CANDIDATES if r["errs"][m] > 0]
                if live and min(live, key=lambda t: abs(math.log2(t[1] / e_l)))[0] == nm:
                    nearest += 1
            rows.append({"name": nm, "median_abs_log2": (S.median(lr) if lr else float("nan")),
                         "exact": exact_s, "nearest": nearest, "struct_zero": zero_s, "fewer": fewer,
                         "n_live": len(lr), "exact_when_lib_exact": ex_when_lib_exact})
        rows.sort(key=lambda d: (math.isnan(d["median_abs_log2"]), d["median_abs_log2"]))
        print("   Q1 which structure matches the LIBRARY, per case (lower = closer):")
        print("      %-16s %9s %7s %8s %9s %7s %10s" % ("structure", "med|lr|", "reprod", "nearest",
                                                        "struct=0", "fewer", "exact-libE=0"))
        for d in rows:
            print("      %-16s %9.3f %7d %8d %9d %7d %10d"
                  % (d["name"], d["median_abs_log2"], d["exact"], d["nearest"], d["struct_zero"],
                     d["fewer"], d["exact_when_lib_exact"]))
        best = rows[0]
        # the median |log2| TIES at 0.000 whenever a structure and the library agree exactly on most
        # cases, so naming rows[0] as "the fit" would report the sort's tie-break as a finding.  The
        # decisive column is the COUNT of exact reproductions, and both are named for what they are.
        best_rep = max(rows, key=lambda d: (d["exact"], -d["median_abs_log2"]))
        print("      -> by exact reproduction: %s (%d/%d, med|lr| %.3f)   |   by median |log2|: %s "
              "(%.3f, reproduces %d)"
              % (best_rep["name"], best_rep["exact"], len(lib_rounds), best_rep["median_abs_log2"],
                 best["name"], best["median_abs_log2"], best["exact"]))

        # ---- C8: implementation sanity, two-sided (failing it indicts the EMULATION)
        sanity = {}
        for nm in ("pairwise", "lanes4", "kahan"):
            worse = sum(1 for r in recs if r["errs"][nm] > r["errs"]["chain"] * (1 + 1e-12))
            sanity[nm] = worse / len(recs)
            print("      [C8 %s vs chain] worse on %.1f%% of cases" % (nm, 100 * sanity[nm]))
        assert sanity["kahan"] <= 0.10, ("C8: Kahan is worse than the chain on %.1f%% of cases -- the "
                                         "EMULATION is at fault" % (100 * sanity["kahan"]))

        # ---- C6: reach -- the family must differ from the chain where the comparison lives
        diff = sum(1 for r in lib_rounds
                   if any(abs(r["errs"][nm] - r["errs"]["chain"]) > 1e-9 * max(r["errs"]["chain"], 1e-300)
                          for nm in ("lanes4", "pairwise")))
        fr = diff / len(lib_rounds)
        print("      [C6 reach] lanes4 or pairwise differs from the chain on %.1f%% of the cases where "
              "the library rounds" % (100 * fr))
        assert fr >= 0.25, ("C6: the structure family differs from the chain on only %.1f%% of the "
                            "rounding cases -- the comparison has no object" % (100 * fr))
        out_reach = len(lib_rounds)

        # ---- Q2: does the between-matrix spread at FIXED kappa1 survive a change of structure?
        fit = best_rep["name"]
        band = [r for r in recs if BAND_LO <= r["kappa1"] < BAND_HI]
        print("   Q2 fixed-kappa1 band [%.1f,%.1f): %d cases" % (BAND_LO, BAND_HI, len(band)))
        q2 = {}
        for nm in ("chain", fit, "library"):
            key = "E_lib" if nm == "library" else None
            cs = [((r["E_lib"] if key else r["errs"][nm]) / (r["kappa1"] * u)) for r in band]
            cs = [c for c in cs if c > 0]
            if len(cs) >= 3:
                q2[nm] = {"n": len(cs), "median": S.median(cs), "min": min(cs), "max": max(cs),
                          "spread": max(cs) / min(cs)}
                print("      %-9s c median %.4g  range [%.4g, %.4g]  SPREAD %.2fx"
                      % (nm, q2[nm]["median"], q2[nm]["min"], q2[nm]["max"], q2[nm]["spread"]))
            else:
                q2[nm] = {"n": len(cs)}
                print("      %-9s too few positive cases in the band (%d)" % (nm, len(cs)))

        # ---- the second-scalar test, structure-conditioned: does kappa1 explain c at all?
        print("   Q2b does log c track log kappa1 under each structure?  (r^2; R543 found 0.11-0.16)")
        q2b = {}
        for nm in ("chain", fit, "library"):
            key = "E_lib" if nm == "library" else None
            pts = [((r["E_lib"] if key else r["errs"][nm]) / (r["kappa1"] * u), r["kappa1"])
                   for r in recs]
            pts = [(c, k) for c, k in pts if c > 0]
            r_ = pearson([math.log(k) for _c, k in pts], [math.log(c) for c, _k in pts])
            q2b[nm] = r_ * r_
            print("      %-9s r^2 = %.3f  (%d cases)" % (nm, q2b[nm], len(pts)))

        # ---- Q3: the order axis under a fixed structure
        sp = order_arm(mats[:max(6, ORDER_MATS)], p, dt, rng)
        print("   Q3 order axis, %d cases x %d permutations (kappa1 invariant, exact sum invariant); "
              "%d cases skipped with no order effect"
              % (sp["_used"], ORDER_PERMS, sp["_skipped_no_order_effect"]))
        print("      median within-case max/min of the error --  chain %.2fx | pairwise %.2fx | "
              "lanes4 %.2fx | LIBRARY %.2fx"
              % (sp["chain"], sp["pairwise"], sp["lanes4"], sp["library"]))
        print("      median WORST error over the orders -- chain %.3g | pairwise %.3g | lanes4 %.3g | "
              "LIBRARY %.3g" % (sp["worst_chain"], sp["worst_pairwise"], sp["worst_lanes4"],
                                sp["worst_library"]))
        print("      R544 measured 77.9x/209.6x on the chain at fp32 over 24 orders")
        used = sp["_used"]

        out["formats"][fname] = {
            "p": p, "dtype": dt.__name__, "n_cases": len(recs), "kappa1_max": kmax,
            "library_exact_cases": nz_lib, "q1": rows,
            "best_by_exact_reproduction": best_rep["name"],
            "best_by_median_abs_log2": best["name"], "fit_used": fit,
            "c8_worse_frac": sanity, "reach_frac": fr, "n_library_rounds": out_reach,
            "case_filters": stats, "live_min": lv[0], "live_max": lv[-1],
            "q2": q2, "q2b_r2": q2b,
            "q3_order_spread": sp, "q3_cases": used,
        }

    with open(os.path.join(HERE, "spike_struct_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_struct_results.json")
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
            print("[%-38s] FIRED" % name)
            return
        print("[%-38s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-38s] holds" % name)
        except AssertionError as e:
            print("[%-38s] *** FIRED ON HEALTHY *** %s" % (name, str(e)[:40]))
            ok = False

    okc, badc = R.verify_corpus()
    assert not badc, "selftest needs the corpus"

    # C2 -- the exact reference against an independent route, read on the SAME list.  math.fsum is
    # correctly rounded and exact_sum is exact, so no list can make them disagree; the only mutation
    # that breaks the certificate is feeding one route a DIFFERENT list, which is what the plant does.
    def ref_agrees(vals, other=None):
        ref = exact_sum(vals)
        f = math.fsum(float(v) for v in (vals if other is None else other))
        assert abs(float(ref) - f) <= abs(f) * 1e-15, "the exact accumulator disagrees with fsum"

    vals = [0.1, 1e-17, -0.1, 3.7e-16, 1e16, -1e16, 2.5]
    fires("C2 reference-reads-two-lists", lambda: ref_agrees(vals, other=vals[1:]))
    holds("C2 reference-agrees/ok", lambda: ref_agrees(vals))

    # C4 -- the EXACT control: products that are powers of two make every partial sum representable, so
    # E == 0 for every structure.  The plant believes the control rounds.
    POW2 = ([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0], [1.0] * 8)   # >= MIN_LIVE live terms

    def exact_control():
        _n, _k, _live, errs, e_lib = measure(POW2[0], POW2[1], np.float32, 24)
        assert all(errs[nm] == 0.0 for nm in STRUCT_NAMES), "the exact control rounds: %r" % errs
        assert e_lib == 0.0, "the library rounds the exact control: %r" % e_lib

    def rounding_case_called_exact():
        """The plant's case must GENUINELY round, and it was measured before being used (Class 189):
        a thousand 0.1s is a case no grouping saves -- E = 6.3e-7 at fp32, the same case spike_lib's
        plants had to find after two inert choices."""
        r = measure([0.1] * 1000, [1.0] * 1000, np.float32, 24)
        assert r is not None and all(v == 0.0 for v in r[3].values()), \
            "the 1000-term case rounds for every structure (measured)"

    fires("C4 rounding-case-called-exact", rounding_case_called_exact)
    holds("C4 exact-control/ok", exact_control)

    # C5 -- the lane-geometry control.  Both plants are on the MEASURED triple ([1e8,1,-1e8] at fp32:
    # chain 0.0, pairwise 0.0, lanes2 1.0, lanes4 1.0, library 1.0).  The fires-case asserts that the
    # CHAIN recovered the small term (false); the holds-case asserts that the lane structure did.
    def chain_recovers():
        _k, _n, errs, _e = lane_control(np.float32, 24, CTRL_M[24])
        assert errs["chain"] == 0.0, "the chain recovered the small term (it does not: relerr is 1.0)"

    def lanes_recover():
        _k, _n, errs, _e = lane_control(np.float32, 24, CTRL_M[24])
        assert errs["lanes4"] == 0.0 and errs["lanes2"] == 0.0, \
            "the lane structures did not recover it: %r" % errs

    fires("C5 chain-called-exact", chain_recovers)
    holds("C5 lane-recovery/ok", lanes_recover)

    # C7 -- the bound comes from the metric's meaning and applies wherever the metric is computed.
    # The control triple has kappa1 ~ 2e9 >> 2^24, so it is NOT measurable: the plant calls it so.
    def control_measurable():
        assert measure([1e8, 1.0, -1e8], [1.0, 1.0, 1.0], np.float32, 24) is not None, \
            "the control triple is outside C7 and must not be measurable"

    fires("C7 control-triple-called-measurable", control_measurable)
    holds("C7 in-regime-measurable/ok",
          lambda: (lambda r: (r is not None) or _raise())(
              measure([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0], [1.0] * 8, np.float32, 24)))

    # the live-term filter is itself a certificate: a case with too few live products has no
    # accumulation to study, and the plant calls such a case measurable (the corpus is full of them).
    fires("live-filter few-live-called-measurable",
          lambda: (lambda r: (r is not None) or _raise())(
              measure([1.0, 2.0, 4.0], [1.0, 1.0, 1.0], np.float32, 24)))
    holds("live-filter live-case/ok",
          lambda: (lambda r: (r is not None and r[2] >= MIN_LIVE) or _raise())(
              measure([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0], [1.0] * 8, np.float32, 24)))

    # C3 -- the comparison is of STRUCTURES, not of terms.  Every structure is handed the same list by
    # construction, and the plant is the mutation that breaks it: it claims a permuted copy of the same
    # terms is the same experiment.  The case is SEARCHED FOR in the corpus first (Class 189: measure the
    # candidate case, never assume one), so the plant has an object only if an order-sensitive case
    # exists -- and that search is itself a finding (kappa1 is invariant, the error is not).
    order_case = None
    tried = 0
    _rng = random.Random(SEED0 + 7)
    for _pn in sorted(glob.glob(os.path.join(MATDIR, "*.mtx"))):
        if order_case:
            break
        _nr, _nc, _ent = R.load_mtx(_pn)
        _A, _sc = R.quantize(_nr, _nc, _ent, 24)
        for _tag, _a, _b in R2.pair_cases(_A, _nr, _nc, max_vecs=40, max_pairs=60):
            if len(_a) != len(_b) or not _a:
                continue                      # the corpus generator emits pairs of unequal length
            _fa = np.asarray(_a, dtype=np.float32) / np.float32(2.0 ** 23)
            _fb = np.asarray(_b, dtype=np.float32) / np.float32(2.0 ** 23)
            _pp = (_fa * _fb).tolist()
            _ex = exact_sum(_pp)
            if _ex == 0:
                continue
            _k1 = float(kappa1_of(_pp) / abs(_ex))
            if not math.isfinite(_k1) or _k1 <= 0 or _k1 > float(2 ** 24):
                continue
            tried += 1
            _idx = list(range(len(_pp)))
            _rng.shuffle(_idx)
            _perm = [_pp[i] for i in _idx]
            if sum_lanes(_pp, np.float32, 4) != sum_lanes(_perm, np.float32, 4):
                order_case = (_pp, _ex, _perm)
                break
    assert order_case is not None, \
        "no order-sensitive case found in %d corpus cases -- the C3 plant has no object" % tried

    def permuted_copy_called_same():
        pp, ex, perm = order_case
        e_same = relerr(sum_lanes(pp, np.float32, 4), ex)
        e_perm = relerr(sum_lanes(perm, np.float32, 4), ex)
        assert e_same == e_perm, "a permuted copy is a different experiment (measured: %r vs %r)" \
            % (e_same, e_perm)

    print("   [C3 plant case] found after %d corpus cases: an order-sensitive case where lanes4 gives "
          "%r vs %r" % (tried, relerr(sum_lanes(order_case[0], np.float32, 4), order_case[1]),
                        relerr(sum_lanes(order_case[2], np.float32, 4), order_case[1])))

    fires("C3 permuted-copy-called-same", permuted_copy_called_same)
    holds("C3 exact-case-order-blind/ok",
          lambda: (lambda pp, ex: (relerr(sum_lanes(pp, np.float32, 4), ex) == 0.0) or _raise())(
              POW2[0], exact_sum(POW2[0])))

    # C6 -- reach.  A check that asks whether the family differs from the chain somewhere must FIRE on a
    # set where it does not: the exact case is such a set, and it is exact by construction.
    def reaches(cases):
        assert any(abs(c[1] - c[0]) > 1e-30 for c in cases), \
            "the structure family does not differ from the chain on any case in this set"

    fires("C6 no-difference-called-reach", lambda: reaches([(0.0, 0.0)] * 12))
    holds("C6 differing-set/ok",
          lambda: reaches([(relerr(sum_chain(order_case[0], np.float32), order_case[1]),
                            relerr(sum_lanes(order_case[0], np.float32, 4), order_case[1])),
                           (0.0, 0.0)]))

    # C8 -- Kahan is a near-exact structure: a chain beating it on most cases would indict the EMULATION,
    # not the library (Class 181).  The plant asserts the reverse on a set where it is false.
    def kahan_not_worse(cases):
        worse = [c for c in cases if c[0] > c[1] * (1 + 1e-12)]
        assert len(worse) <= max(1, len(cases) // 10), "%d of %d cases have Kahan worse" \
            % (len(worse), len(cases))

    # the tuple is (KAHAN, CHAIN): the harness counts c[0] > c[1] as "Kahan worse", so the two cases
    # must sit on OPPOSITE sides of that reading or the pair is a polarity error (Class 183)
    fires("C8 kahan-beaten-by-chain",
          lambda: kahan_not_worse([(1.0, 0.0)] * 20))     # kahan 1.0 > chain 0.0, everywhere
    holds("C8 kahan-slack/ok",
          lambda: kahan_not_worse([(0.5, 0.9), (0.4, 0.8), (0.2, 1.0), (0.6, 0.7)]))

    # C9 -- a constant instrument.  If the library's measured error takes the same value on every case,
    # the instrument is not resolving anything and the comparisons above are about nothing.
    def not_constant(vals):
        assert len({round(v, 12) for v in vals}) >= 3, \
            "the measured error takes fewer than 3 distinct values -- a constant instrument"

    fires("C9 constant-called-resolved", lambda: not_constant([1.0] * 40))
    holds("C9 varied/ok", lambda: not_constant([0.1, 0.2, 0.3, 0.1]))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv))
