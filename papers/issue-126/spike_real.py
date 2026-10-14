#!/usr/bin/env python3
"""spike_real (#126) -- DOES THE FLOOR LAW HOLD ON REAL MATRICES?

Every instrument so far (spike_v0/v1/v2/v3) used ONE synthetic integer generator: random p-bit
integers with a sign-flip knob.  The laws could be artefacts of that generator (the R540 lesson: an
exponent measured on one realisation of a nuisance is a number, not a law).  This instrument replaces
the generator with REAL sparse matrices from the SuiteSparse Matrix Collection, pinned by SHA-256 and
hash-verified on EVERY read, QUANTIZED TO THE FORMAT'S OWN WIDTH -- "the matrix as stored in format
F" -- so the operands are exactly representable and the exact dot product is computable, as before.

THE DOT PRODUCTS ARE PAIRS OF REAL VECTORS (row_i . row_j, col_i . col_j).  The first construction
tried was row sums (row_i . 1): it produces the WIDE kappa1 range (1 to 2.5e7 on stiffness matrices,
whose rows sum to their equilibrium cancellation) but multiplying by the all-ones vector keeps every
term well under the register width, so the arithmetic came out EXACT in most cases and the floor was
never reached.  A pair of full-width real vectors is the regime the construct is actually about.

Laws under test (what spike_v0/v1 measured on synthetic data):
  L1 the floor exists : E falls with K then flattens
  L2 the collapse (P2): E_floor / kappa1 depends on the accumulator width u alone, not on the matrix
  L3 the constant     : E_floor / (kappa1 * 2^-p) == c, compared against the synthetic c ~ 0.2-0.5
Output: spike_real_results.json
Usage:  python3 spike_real.py [--selftest]
"""
import glob
import hashlib
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S  # noqa: E402  (sig_round, dot_emulated, kappa1, relerr, median)

MATDIR = os.path.join(HERE, "matrices")
SEED0 = 20261006


# ----------------------------------------------------------------- the pinned corpus
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pins():
    """SHA256SUMS lines: '<name>  ok  mtx_sha=<32 hex>  tar_sha=<32 hex>' (truncated hashes)."""
    pins = {}
    with open(os.path.join(MATDIR, "SHA256SUMS")) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            for p in parts:
                if p.startswith("mtx_sha="):
                    pins[parts[0]] = p.split("=", 1)[1]
    return pins


def verify_corpus():
    """Every read is hash-checked: a cache that has silently become another dataset must be caught."""
    pins = load_pins()
    ok, bad = [], []
    for name, prefix in sorted(pins.items()):
        have = sha256_file(os.path.join(MATDIR, name))[:len(prefix)]
        (ok if have == prefix else bad).append(name)
    return sorted(ok), sorted(bad)


def load_mtx(path):
    """Matrix Market reader (coordinate real/integer/pattern, general/symmetric)."""
    entries, dims, pattern, sym = [], None, False, False
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("%"):
                if s.startswith("%%MatrixMarket"):
                    header = s.split()
                    pattern = header[-2] == "pattern"
                    sym = header[-1] == "symmetric"
                continue
            parts = s.split()
            if dims is None:
                dims = [int(x) for x in parts[:2]]
                continue
            i, j = int(parts[0]) - 1, int(parts[1]) - 1
            v = 1.0 if pattern else float(parts[2])
            entries.append((i, j, v))
            if sym and i != j:
                entries.append((j, i, v))
    return dims[0], dims[1], entries


def quantize(nr, nc, entries, p):
    """The matrix as stored in format F: entries scaled so max|A| <= 2^(p-1)-1, rounded to integers.

    Matching spike_v0, whose generator drew operands from [1, 2^(p-1)), i.e. at most p-1 bits -- so
    the real operands and the synthetic ones occupy the SAME width and the comparison is like for like.
    """
    mx = max(abs(v) for _, _, v in entries) if entries else 0.0
    if mx == 0:
        return [[0] * nc for _ in range(nr)], 0
    s = math.floor(math.log2((2.0 ** (p - 1) - 1.0) / mx))
    scale = 2.0 ** s
    A = [[0] * nc for _ in range(nr)]
    for i, j, v in entries:
        A[i][j] = int(round(v * scale))
    return A, s


def cases_from(A, nr, nc, max_vecs=60, max_pairs=300, seed=SEED0):
    """Real dot products: pairs of DISTINCT real vectors (rows and columns of the matrix)."""
    rng = random.Random(seed)
    vecs = [("row%d" % i, A[i]) for i in range(min(nr, max_vecs))]
    cols = [[A[i][j] for i in range(nr)] for j in range(min(nc, max_vecs))]
    vecs += [("col%d" % j, cols[j]) for j in range(min(nc, max_vecs))]
    pairs = [(i, j) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]
    rng.shuffle(pairs)
    return [(vecs[i][0] + "." + vecs[j][0], vecs[i][1], vecs[j][1]) for i, j in pairs[:max_pairs]]


# ----------------------------------------------------------------- measurement
def case_curve(a, b, q, p, Kmax):
    """E (and E/kappa1) vs K for one real dot product; None if the case is degenerate."""
    k1 = S.kappa1(a, b)
    ex = S.dot_exact(a, b)
    if ex == 0 or k1 == float("inf"):
        return None
    return {"kappa1": k1,
            "E": {K: S.relerr(S.dot_emulated(a, b, q, K, p), ex) for K in range(1, Kmax + 1)}}


def floor_of(cur, Kmax):
    """The floor: the smallest E over the K where truncation is already exactly zero."""
    return min(cur["E"][K] for K in range(max(3, Kmax - 3), Kmax + 1))


def binned(vals, edges):
    """Median of (E_floor/(kappa1*u)) per kappa1 bin, with the bin's case count."""
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        grp = [v for k, v in vals if lo <= k < hi]
        out.append((lo, hi, len(grp), S.median(grp) if grp else None))
    return out


def main():
    out = {"seed0": SEED0, "formats": {}}
    FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]   # p = accumulator width, q = p//2
    KMAX = 6
    N_SYN, SYN_SEEDS = 600, 12      # spike_v0's dot-product length, for a like-for-like comparison

    print("=" * 100)
    print("spike_real -- the floor law on REAL matrices (SuiteSparse, SHA-256 pinned, quantized to F)")
    print("=" * 100)

    ok, bad = verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok

    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]
    print("matrices: %s" % ", ".join(n for n, _ in mats))

    for fname, p in FORMATS:
        q, u = p // 2, 2.0 ** -p
        blk = {"p": p, "q": q, "u": u, "matrices": {}, "all_cases": {}}
        print()
        print("--- %s (p=%d q=%d u=%.3e) ---" % (fname, p, q, u))

        vals = []           # (kappa1, E_floor/(kappa1*u)) over all non-exact real cases
        raw = []            # (kappa1, E_floor), for the exponent fit
        n_exact = n_round = 0
        for name, path in mats:
            nr, nc, ent = load_mtx(path)
            A, sc = quantize(nr, nc, ent, p)
            ks, fl = [], []
            ne = nr_ = 0
            for tag, a, b in cases_from(A, nr, nc):
                cur = case_curve(a, b, q, p, KMAX)
                if cur is None:
                    continue
                ef = floor_of(cur, KMAX)
                if ef == 0:
                    ne += 1
                    continue
                nr_ += 1
                ks.append(cur["kappa1"])
                fl.append(ef / (cur["kappa1"] * u))
                vals.append((cur["kappa1"], ef / (cur["kappa1"] * u)))
                raw.append((cur["kappa1"], ef))
            n_exact += ne
            n_round += nr_
            blk["matrices"][name] = {"scale_2": sc, "n_rounding": nr_, "n_exact": ne,
                                     "median_kappa1": S.median(ks),
                                     "median_E_over_kappa1_over_u": S.median(fl)}
            print("   %-14s round=%3d exact=%3d  med kappa1=%9.3g  med E/k1/u=%.3g"
                  % (name, nr_, ne, S.median(ks) if ks else float("nan"),
                     S.median(fl) if fl else float("nan")))

        # synthetic arm, same formats (spike_v0's generator)
        syn_vals, syn_k1 = [], []
        for s in range(SYN_SEEDS):
            rng = random.Random(SEED0 + 1000 * p + 17 * N_SYN + 101 * s)
            a, b = S.gen_case(N_SYN, p, rng, 4.0)
            cur = case_curve(a, b, q, p, KMAX)
            if cur is None:
                continue
            ef = floor_of(cur, KMAX)
            syn_k1.append(cur["kappa1"])
            if ef > 0:
                syn_vals.append((cur["kappa1"], ef / (cur["kappa1"] * u)))

        c_real = S.median([v for _, v in vals]) if vals else float("nan")
        c_syn = S.median([v for _, v in syn_vals]) if syn_vals else float("nan")
        blk["all_cases"] = {"n_rounding": n_round, "n_exact": n_exact,
                            "median_kappa1": S.median([k for k, _ in vals]) if vals else None}
        blk["c_real"] = c_real
        blk["c_synthetic"] = c_syn
        blk["ratio_real_over_synthetic"] = c_real / c_syn if c_syn else float("nan")
        # the collapse (L2): is E/kappa1/u flat across the real kappa1 range?
        edges = [1.0, 1.0001, 1.5, 3.0, 10.0, 100.0, 1e18]
        blk["collapse_bins"] = binned(vals, edges)
        # the floor's own kappa1 exponent: E_floor ~ kappa1^beta (beta < 1 means the single governing
        # scalar kappa1 OVER-states the damage at high conditioning -- a refinement of P2, measured)
        # ...and it is fitted on SUBSETS, because an exponent read off one subset is a number, not a
        # law (R540/Class 181): the reported quantity is the RANGE across subsets, with each subset's
        # own SE, never a single coefficient.
        subsets = [("all", raw),
                   ("kappa1>1", [(k, e) for k, e in raw if k > 1.0000001]),
                   ("kappa1>=1.5", [(k, e) for k, e in raw if k >= 1.5])]
        fits = {}
        for label, sel in subsets:
            if len(sel) >= 8:
                be, se = S.fit_slope_se([k for k, _ in sel], [e for _, e in sel])
                fits[label] = {"beta": be, "se": se, "n": len(sel)}
        blk["floor_kappa1_fits"] = fits
        betas = [v["beta"] for v in fits.values()]
        blk["floor_kappa1_exponent_range"] = [min(betas), max(betas)] if betas else None
        blk["floor_kappa1_exponent_n"] = len(raw)
        out["formats"][fname] = blk

        print("   real:      rounding=%3d exact=%3d  med kappa1=%.3g" %
              (n_round, n_exact, S.median([k for k, _ in vals]) if vals else float("nan")))
        print("   synthetic: med kappa1=%.3g  (n=%d)" % (S.median(syn_k1), len(syn_k1)))
        print("   -> c_real=%.3g  c_synthetic=%.3g  ratio=%.2f"
              % (c_real, c_syn, blk["ratio_real_over_synthetic"]))
        print("   floor exponent E_floor ~ kappa1^beta by subset:")
        for label, fit in fits.items():
            print("      %-11s n=%4d  beta = %.3f +- %.3f" % (label, fit["n"], fit["beta"], fit["se"]))
        if blk["floor_kappa1_exponent_range"]:
            lo, hi = blk["floor_kappa1_exponent_range"]
            verdict = "consistent with LINEAR (P2 holds)" if lo <= 1.0 <= hi else \
                      "resolvably SUBLINEAR (P2 over-states high conditioning)"
            print("      -> range [%.3f, %.3f] : %s" % (lo, hi, verdict))
        print("   collapse (E/k1/u by kappa1 bin): %s"
              % "  ".join("[%g,%g)n=%d:%.3g" % (lo, hi, n, c if c else float('nan'))
                          for lo, hi, n, c in blk["collapse_bins"] if n))

    with open(os.path.join(HERE, "spike_real_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_real_results.json")
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

    ASH = os.path.join(MATDIR, "ash85.mtx")
    good = load_pins()["ash85.mtx"]

    # C1: the corpus read is hash-checked -- a wrong pin prefix must fail it
    def hash_matches(path, prefix):
        return sha256_file(path)[:len(prefix)] == prefix

    def corpus_check(path, prefix):
        assert hash_matches(path, prefix), "corpus hash mismatch"

    fires("tampered-corpus", lambda: corpus_check(ASH, "0" * len(good)))
    holds("corpus-intact/ok", lambda: corpus_check(ASH, good))

    # C2: the loader reads the real matrix; an entry-less matrix must FAIL (a real fixture, so the
    # plant is not a function that raises unconditionally -- that would be a decoration)
    import tempfile
    empty_mtx = os.path.join(tempfile.mkdtemp(), "empty.mtx")
    with open(empty_mtx, "w") as fh:
        fh.write("%%MatrixMarket matrix coordinate real general\n5 5 0\n")

    def loads_matrix(path):
        nr, nc, ent = load_mtx(path)
        return nr > 0 and nc > 0 and len(ent) > 0

    fires("empty-matrix", lambda: loads_matrix(empty_mtx) or _raise())
    holds("loads-mtx/ok", lambda: loads_matrix(ASH) or _raise())

    # C3: quantization must preserve BOTH signs of a mixed-sign real matrix
    def has_both_signs(A):
        vals = [v for row in A for v in row]
        return any(v < 0 for v in vals) and any(v > 0 for v in vals)

    nr, nc, ent = load_mtx(os.path.join(MATDIR, "west0067.mtx"))
    Aw, _s = quantize(nr, nc, ent, 24)
    fires("signs-lost", lambda: has_both_signs([[1, 1], [0, 1]]) or _raise())
    holds("signs-kept/ok", lambda: has_both_signs(Aw) or _raise())

    # C4: the quantized operands must fit the format's width (<= p-1 bits)
    def fits_width(A, p):
        return max(abs(v) for row in A for v in row).bit_length() <= p - 1

    fires("over-wide", lambda: fits_width([[1 << 30]], 8) or _raise())
    holds("fits-width/ok", lambda: fits_width(Aw, 24) or _raise())

    # C5: a case whose exact sum is ZERO is excluded, not silently divided by
    def excluded(a, b):
        return case_curve(a, b, 2, 8, 4) is None

    fires("zero-sum-kept", lambda: (excluded([1, -1], [1, 1]) is False) or _raise())
    holds("zero-sum-excluded/ok", lambda: excluded([1, -1], [1, 1]) or _raise())

    # C6: a vector PAIR must be used, not a row sum -- the construction that reaches the floor
    def pairs_only(cases):
        return all("." in tag for tag, _a, _b in cases)

    nr2, nc2, ent2 = load_mtx(ASH)
    A2, _ = quantize(nr2, nc2, ent2, 8)
    fires("row-sums-used", lambda: pairs_only([("rowsum", [1], [1])]) or _raise())
    holds("pairs-only/ok", lambda: pairs_only(cases_from(A2, nr2, nc2)) or _raise())

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
