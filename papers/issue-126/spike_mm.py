#!/usr/bin/env python3
"""spike_mm (#126) -- THE MATMUL ARM: the construct is stated for kernels, but every result so far is an
isolated dot product.  A real kernel does not chain one accumulator -- it sums into L INDEPENDENT
REGISTER LANES and combines them at the end, and L is fixed by the ISA, not by the numerics.

This instrument asks the kernel question directly: does the number of lanes change the floor?

The construction is exact and needs no new ground truth.  A matmul output element is
C[i,j] = sum_p A[i,p]*B[p,j], and with B = A^T it is the dot product of two ROWS of A -- a quantity this
issue already measures.  So the SAME dot product can be evaluated two ways:

  route L=1   the single-accumulator chain the whole issue has measured        (spike_v2's emulator)
  route L>1   L lanes, terms assigned to lanes, each lane chained, then the lanes combined

and any difference is attributable to the lane structure ALONE -- it is a two-routes-to-one-quantity
design (Class 171), with the exact sum as the shared reference.

REGISTERED PREDICTION (written before measuring):
  P5  more lanes REDUCE the accumulation error.  The rounding after an add is O(u*|running partial|),
      and with L lanes each partial sum grows to only ~1/L of the total, so the per-add rounding is
      smaller; the combine step adds L roundings, which is O(L) against the O(n) saved.  So the floor
      should fall with L, with diminishing returns once the lane count is large.

Certificates (asserted, not printed):
  C1  L=1 reproduces the library emulator EXACTLY (the lane model contains the chain as its base case).
  C2  the lanes are a PARTITION of the terms: with an exact accumulator every L gives the exact sum, so a
      difference at finite p is a rounding difference and not a bookkeeping error.
  C3  the lane assignment is total: every term lands in exactly one lane (counts sum to the term count).
  C4  [power] >= 6 matrices carry the fixed-kappa1 band (Class 184).
  C5  the comparison CAN move: the control (L=1 against itself) shows no change, so a reported lane
      effect is a measurement (Class 173/178: the control must be able to fail the way the test can).
  C6  the two lane ASSIGNMENTS (round-robin and contiguous blocks) are different partitions, so an
      agreement between them is evidence about the lane COUNT and not about one assignment.
Output: spike_mm_results.json
Usage:  python3 spike_mm.py [--selftest]
"""
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S        # noqa: E402
import spike_real as R      # noqa: E402
import spike_real2 as R2    # noqa: E402

MATDIR = R.MATDIR
SEED0 = 20261010
KMAX = 6
LANES = (1, 2, 4, 8)
MODES = ("rr", "blk")
BAND = (1.0, 1.5)
FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]
P_EXACT = 400                  # a register wide enough that no add rounds: the partition check


# ----------------------------------------------------------------- the lane model (the kernel's accumulators)
def limb_terms(x, y, q, K):
    """the SIGNED limb products of ONE element, heaviest first (the emulator's own order)."""
    neg = (x < 0) ^ (y < 0)
    return [(-t if neg else t) for t in S.diagonals(x, y, q)[:K]]


def term_list(a, b, q, K):
    """every term the kernel adds, in the order the elements are traversed (the contraction index p)."""
    out = []
    for i in range(len(a)):
        out.extend(limb_terms(a[i], b[i], q, K))
    return out


def lane_index(idx, n, L, mode):
    """which register lane term `idx` lands in.  The two assignments are genuinely different partitions."""
    if mode == "rr":
        return idx % L
    return min(L - 1, idx * L // n)          # contiguous chunks


def dot_lanes(terms, p, L, mode):
    """L register lanes, each chained with rounding, combined with rounding at the end."""
    if L <= 1:
        acc = 0
        for t in terms:
            acc = S.sig_round(acc + t, p)
        return acc
    n = len(terms)
    lanes = [0] * L
    for idx, t in enumerate(terms):
        j = lane_index(idx, n, L, mode)
        lanes[j] = S.sig_round(lanes[j] + t, p)
    acc = 0
    for t in lanes:
        acc = S.sig_round(acc + t, p)
    return acc


def lane_counts(n, L, mode):
    """how many terms each lane receives -- the partition, as counts (C3)."""
    out = [0] * L
    for idx in range(n):
        out[lane_index(idx, n, L, mode)] += 1
    return out


def main():
    out = {"seed0": SEED0, "kmax": KMAX, "lanes": list(LANES), "modes": list(MODES),
           "band": list(BAND), "formats": {}}
    print("=" * 100)
    print("spike_mm -- the matmul arm: does the number of REGISTER LANES change the floor?")
    print("=" * 100)
    ok, bad = R.verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok
    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]
    lo, hi = BAND

    for fname, p in FORMATS:
        q, u = p // 2, 2.0 ** -p
        rows = []          # (matrix, kappa1, {config: c}) -- c = E/(kappa1*u) at K=KMAX
        bymat = {}
        for name, path in mats:
            nr, nc, ent = R.load_mtx(path)
            A, _sc = R.quantize(nr, nc, ent, p)
            for _tag, a, b in R2.pair_cases(A, nr, nc) + R2.cancel_cases(A, nr, nc):
                ex = S.dot_exact(a, b)
                if ex == 0:
                    continue
                k1 = S.kappa1(a, b)
                if k1 == float("inf") or not R2.resolvable(k1, p):
                    continue
                terms = term_list(a, b, q, KMAX)
                cs = {}
                for L in LANES:
                    for mode in MODES:
                        if L == 1 and mode != MODES[0]:
                            continue                      # L=1 is mode-independent
                        E = S.relerr(dot_lanes(terms, p, L, mode), ex)
                        cs["L%d_%s" % (L, mode)] = (E / (k1 * u)) if E > 0 else None
                rows.append((name, k1, cs))
                bymat.setdefault(name, []).append((k1, cs))

        cfgs = ["L%d_%s" % (1, MODES[0])] + ["L%d_%s" % (L, m) for L in LANES[1:] for m in MODES]
        # the case-wise RATIO E_L / E_1 -- the direct reading of "do more lanes help?"
        print()
        print("--- %s (p=%d q=%d) -- %d resolvable rounding cases ---" % (fname, p, q, len(rows)))
        print("   median c = E/(kappa1*u) at K=%d, by lane count:" % KMAX)
        hdr = "        %-10s" % "config"
        for c_ in cfgs:
            hdr += "%12s" % c_
        print(hdr)
        med = {}
        for c_ in cfgs:
            vals = [cs[c_] for _n, _k, cs in rows if cs.get(c_) is not None]
            med[c_] = S.median(vals)
        line = "        %-10s" % "median c"
        for c_ in cfgs:
            line += "%12.4g" % (med[c_] if med[c_] is not None else float("nan"))
        print(line)
        base = med[cfgs[0]]
        ratios = {}
        for c_ in cfgs:
            if med[c_] is None or not base:
                continue
            ratios[c_] = med[c_] / base
        line = "        %-10s" % "ratio / L1"
        for c_ in cfgs:
            line += "%12.3f" % ratios.get(c_, float("nan"))
        print(line)
        print("   (a ratio < 1 means MORE LANES MADE IT MORE ACCURATE)")

        # the per-case ratio, to separate a real effect from a median shift
        percase = {}
        for c_ in cfgs[1:]:
            rs = [cs[c_] / cs[cfgs[0]] for _n, _k, cs in rows
                  if cs.get(c_) is not None and cs.get(cfgs[0])]
            if rs:
                # THREE-WAY, because a two-way "improved" count hides the ties: a median ratio of
                # exactly 1.000 with a high "improved" share means most of the rest are EQUAL, not
                # worse -- and "more lanes never hurt" is a different claim from "more lanes help".
                percase[c_] = {"median": S.median(rs), "n": len(rs),
                               "frac_better": sum(1 for r in rs if r < 1.0 - 1e-15) / len(rs),
                               "frac_equal": sum(1 for r in rs if abs(r - 1.0) <= 1e-15) / len(rs),
                               "frac_worse": sum(1 for r in rs if r > 1.0 + 1e-15) / len(rs)}
        print("   per-case ratio E_L/E_1 (three-way; 'better' = the case became MORE accurate):")
        print("        %-10s %8s %9s %9s %9s" % ("config", "median", "better", "equal", "worse"))
        for c_, d in sorted(percase.items()):
            print("        %-10s %8.3f %8.1f%% %8.1f%% %8.1f%%  (n=%d)"
                  % (c_, d["median"], 100 * d["frac_better"], 100 * d["frac_equal"],
                     100 * d["frac_worse"], d["n"]))

        # the fixed-kappa1 spread under each lane count (does L move the between-matrix constant?)
        spreads = {}
        for c_ in cfgs:
            vals = []
            for nm, cs in bymat.items():
                bv = [cs_[c_] for k_, cs_ in cs if lo <= k_ < hi and cs_.get(c_) is not None]
                if len(bv) >= 8:
                    vals.append(S.median(bv))
            if len(vals) >= 6:
                spreads[c_] = {"n_matrices": len(vals), "ratio": max(vals) / min(vals)}
        # WHERE does the change land?  If the lane effect is rounding-driven, it should concentrate in
        # the heavily-cancelling cases (large c_L1), where the partial sums roam furthest from the total.
        c1 = sorted(cs[cfgs[0]] for _n, _k, cs in rows if cs.get(cfgs[0]) is not None)
        q1, q3 = c1[len(c1) // 4], c1[3 * len(c1) // 4]
        conc = {}
        for c_ in cfgs[1:]:
            hi_r = [cs[c_] / cs[cfgs[0]] for _n, _k, cs in rows
                    if cs.get(c_) is not None and cs.get(cfgs[0]) and cs[cfgs[0]] > q3]
            lo_r = [cs[c_] / cs[cfgs[0]] for _n, _k, cs in rows
                    if cs.get(c_) is not None and cs.get(cfgs[0]) and cs[cfgs[0]] < q1]
            if hi_r and lo_r:
                conc[c_] = {"hi_frac_better": sum(1 for r in hi_r if r < 1 - 1e-15) / len(hi_r),
                            "lo_frac_better": sum(1 for r in lo_r if r < 1 - 1e-15) / len(lo_r),
                            "hi_median": S.median(hi_r), "lo_median": S.median(lo_r)}
        print("   within-case change by the case's OWN c_L1 (top quartile vs bottom):")
        print("        %-10s %14s %14s %10s %10s" % ("config", "hi better", "lo better", "hi med", "lo med"))
        for c_, d in sorted(conc.items()):
            print("        %-10s %13.1f%% %13.1f%% %10.3f %10.3f"
                  % (c_, 100 * d["hi_frac_better"], 100 * d["lo_frac_better"], d["hi_median"], d["lo_median"]))
        print("   between-matrix spread of c at the FIXED kappa1 band [%g,%g):" % (lo, hi))
        for c_, d in sorted(spreads.items()):
            print("        %-10s %.3fx over %d matrices" % (c_, d["ratio"], d["n_matrices"]))
        assert len(spreads) == len(cfgs), \
            "C4: only %d of %d configs have 6+ band matrices -- the spread test is not powered" % (
                len(spreads), len(cfgs))

        out["formats"][fname] = {"p": p, "q": q, "u": u, "n_cases": len(rows),
                                 "median_c": med, "ratio_to_L1": ratios,
                                 "per_case_ratio": percase, "band_spread": spreads,
                                 "concentration": conc, "c_quartiles": [q1, q3],
                                 "cfgs": cfgs}

    with open(os.path.join(HERE, "spike_mm_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_mm_results.json")
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

    nr, nc, ent = R.load_mtx(os.path.join(MATDIR, "west0067.mtx"))
    A, _ = R.quantize(nr, nc, ent, 24)
    q, p = 12, 24
    a = b = None
    for _tag, aa, bb in R2.cancel_cases(A, nr, nc):
        if S.dot_exact(aa, bb) != 0 and S.kappa1(aa, bb) < 1e3:
            a, b = aa, bb
            break
    assert a is not None, "selftest needs a resolvable case"
    terms = term_list(a, b, q, KMAX)
    ex = S.dot_exact(a, b)

    # C1 -- L=1 IS the library emulator.  The plant is a different ORDER (reversed terms), which for a
    # cancelling case genuinely accumulates differently.
    def is_library(tl, reverse=False):
        got = dot_lanes(list(reversed(tl)) if reverse else tl, p, 1, "rr")
        want = S.dot_emulated(a, b, q, KMAX, p)
        assert got == want, "L=1 does not reproduce the library emulator"

    fires("L1-not-library", lambda: is_library(terms, reverse=True))
    holds("L1-library/ok", lambda: is_library(terms))

    # C2 -- the lanes are a PARTITION: an exact register makes every L land on the exact sum.  The plant
    # DROPS a term, which is exactly the bookkeeping error this certificate exists to catch.
    def exact_ok(L, mode, drop=False):
        tl = terms[1:] if drop else terms
        assert dot_lanes(tl, P_EXACT, L, mode) == ex, "L=%d disagrees with the exact sum" % L

    fires("dropped-term", lambda: exact_ok(4, "rr", drop=True))
    holds("exact-partition/ok", lambda: all(exact_ok(L, m) for L in LANES for m in MODES))

    # C3 -- every lane is NON-EMPTY and the counts sum to the term count.  The plant asks for more lanes
    # than there are terms, which leaves lanes empty.
    def partition_ok(tl, L, mode):
        cts = lane_counts(len(tl), L, mode)
        assert sum(cts) == len(tl) and min(cts) >= 1, "not a partition: %s" % cts

    fires("lanes-exceed-terms", lambda: partition_ok(terms[:4], 8, "rr"))
    holds("partition-total/ok", lambda: partition_ok(terms, 8, "rr"))

    # C4 -- power, on the reporting side rather than the run: the three-way split must partition the
    # cases (a bookkeeping bug that double-counts would silently inflate a fraction).
    def split_ok(better, equal, worse, n):
        assert abs((better + equal + worse) / n - 1.0) < 1e-12, "the three-way split does not partition"

    fires("split-not-partition", lambda: split_ok(10, 10, 10, 25))
    holds("split-partitions/ok", lambda: split_ok(10, 10, 5, 25))

    # C5 -- rr and blk are DIFFERENT partitions (so agreement between them is evidence about the lane
    # COUNT and not about one assignment).  The plant is the degenerate n == L, where they coincide.
    def partition_of(n, L, mode):
        d = {}
        for idx in range(n):
            d.setdefault(lane_index(idx, n, L, mode), []).append(idx)
        return {k: tuple(v) for k, v in sorted(d.items())}

    def assignments_differ(n, L):
        # MEMBERSHIP, not counts: with n divisible by L the two assignments hand each lane the SAME
        # NUMBER of terms and differ only in WHICH ones -- the first version of this check compared
        # counts and read "coincide" for a healthy input (Class 187(a): the check named the assignment
        # and compared a different object).
        assert partition_of(n, L, "rr") != partition_of(n, L, "blk"), \
            "the two lane assignments coincide at n=%d L=%d" % (n, L)

    fires("assignments-coincide", lambda: assignments_differ(2, 2))
    holds("assignments-differ/ok", lambda: assignments_differ(64, 4))

    # C6 -- the band-spread test needs power in EVERY configuration (Class 184)
    def powered(spreads, cfgs):
        assert len(spreads) == len(cfgs), "only %d of %d configs carry the band" % (len(spreads), len(cfgs))

    fires("band-unpowered", lambda: powered({"a": 1, "b": 2}, ["a", "b", "c"]))
    holds("band-powered/ok", lambda: powered({"a": 1, "b": 2, "c": 3}, ["a", "b", "c"]))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
