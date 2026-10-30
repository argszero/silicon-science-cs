#!/usr/bin/env python3
"""run_scale.py -- TIER B: the same axis at the harness's own scale (1,000,000 descriptors).

Tier A runs on a committed 20k subsample, so a clean machine reproduces it with numpy alone.
This tier needs the 1M corpus, which cannot be committed: `fetch_corpus.sh` retrieves it and
checks its sha256, and when the corpus is absent this program prints `NOT RUN` and exits 0. Not
run is not a failure, and it is never reported as one.

What it adds to tier A: whether the ordering the axis predicts survives an increase in n by
50x, and what the family spread looks like at the scale a benchmark actually reports.

Reads  : the corpus given by $SIFT_HDF5 (default: corpus/sift-128-euclidean.hdf5)
Writes : results/scale.json
"""
import json
import os
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiefloor as T                                   # noqa: E402

warnings.filterwarnings("ignore", message=".*encountered in matmul")

K = 10
NQ = 512
SEEDS = [7, 11, 13]
KNN = 1000
CORPUS = os.environ.get("SIFT_HDF5", "corpus/sift-128-euclidean.hdf5")
EXPECT_SHA = "dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984"


def main():
    if not os.path.exists(CORPUS):
        print("NOT RUN: the 1M corpus is not present at %s" % CORPUS)
        print("         run ./fetch_corpus.sh (it verifies sha256 %s...)" % EXPECT_SHA[:16])
        print("         Tier A (run_mechanism.py) needs no corpus and is unaffected.")
        return 0
    try:
        import h5py
    except ImportError:
        print("NOT RUN: h5py is not importable by %s, and the corpus is stored as HDF5." % sys.executable)
        print("         Tier A (run_mechanism.py) needs no h5py and is unaffected.")
        return 0

    t0 = time.time()
    with h5py.File(CORPUS, "r") as f:
        X = f["train"][:]
        test = f["test"][:]
    n, d = X.shape
    assert (n, d) == (1000000, 128), (n, d)
    X = X.astype(np.int32)
    assert np.all(X == np.round(X)) and X.min() >= 0
    print("corpus %d x %d, %d seeds, %d queries/seed, k=%d" % (n, d, len(SEEDS), NQ, K))

    def query_set(seed):
        r = np.random.default_rng(seed)
        r.permutation(n)                         # same draw order as the round-4/5 runs
        qidx = r.choice(len(test), NQ, replace=False)
        return test[qidx].astype(np.int32)

    cells = []

    def record(tag, D_fn, qs, knn=KNN):
        # SHAPE CONTRACT: every distance generator yields query-MAJOR matrices, (queries x corpus).
        # The first version of this function indexed columns while the generators had been made
        # query-major, so each "query" was really one corpus point's distances across a 32-query
        # block -- a 32-long vector. It produced a full, plausible-looking table whose `atoms` was
        # 32 in every cell (the block size) and whose tie groups were the block's, not the
        # corpus's, and nothing raised, because both axes were 32. The assertion below is the guard
        # this defect earned.
        import statistics
        ts, fs, ats = [], [], []
        for D in D_fn():
            if D.shape[1] != n or D.shape[0] > 64:
                raise AssertionError(
                    "distance block must be (queries-in-block x corpus) = (<=64 x %d), got %s -- "
                    "an axis swap here measures a block instead of the corpus and raises nothing"
                    % (n, (D.shape,)))
            for j in range(D.shape[0]):
                r_, t, fl = T.identified_set(K, D[j])
                ts.append(t); fs.append(fl); ats.append(T.resolution(D[j], knn))
        cells.append(dict(tag=tag, n_queries=len(ts),
                          median_t=round(float(statistics.median(ts)), 3),
                          mean_t=round(float(statistics.mean(ts)), 3),
                          max_t=int(max(ts)),
                          median_atoms=int(statistics.median(ats)),
                          mean_floor=round(float(statistics.mean(fs)), 4),
                          frac_floor_lt1=round(sum(1 for f in fs if f < 1 - 1e-12) / len(fs), 4),
                          frac_whole_topk=round(sum(1 for t in ts if t >= K) / len(ts), 4)))

    # float endpoint control at scale
    qs = query_set(SEEDS[0])
    record("float/raw descriptors", lambda: T.exact_sq_distances(qs, X), qs)

    # SimHash / Hamming
    bmax = 256
    rng = np.random.default_rng(SEEDS[0])
    P = rng.standard_normal((d, bmax))
    codes_full = T.simhash_codes(X, P, bmax)
    for b in [256, 64, 32]:
        for seed in SEEDS:
            q = query_set(seed)
            qc = T.simhash_codes(q, P, b)
            record("Hamming/%dbit" % b,
                   lambda c=codes_full, qc=qc, b=b: T.hamming_blocks(c[:, :b], qc, b), q)
        del q

    # product quantisation
    for bits in [32, 64]:
        m = bits // 8
        cent, pcodes = T.pq_train_encode(X, m, np.random.default_rng(20261030 + bits))
        R = T.pq_reconstruct(X, cent, pcodes)
        for seed in SEEDS:
            q = query_set(seed)
            record("PQ/%dbit" % bits,
                   lambda q=q: T.exact_sq_distances(q, R), q)
        del R, pcodes

    # scalar quantisation
    for qbits in [2, 4]:
        rec = T.sq_levels(qbits)
        code = T.sq_encode(X, qbits)
        R = T.sq_reconstruct(rec, code)
        for seed in SEEDS:
            q = query_set(seed)
            record("SQ/%dbit-per-component" % qbits,
                   lambda q=q: T.exact_sq_distances(q, R), q)
        del R, code

    print("\n%-30s %8s %8s %8s" % ("cell", "atoms", "med t", "floor"))
    for c in sorted(cells, key=lambda c: c["median_atoms"]):
        print("%-30s %8d %8.1f %8.4f" % (c["tag"], c["median_atoms"], c["median_t"], c["mean_floor"]))

    # The artefact records the corpus by NAME, never by absolute path: a committed result that
    # embeds one machine's directory layout is not reproducible by anyone else, and a reader
    # would have no way to tell the difference from the numbers being local too.
    out = dict(corpus=dict(name=os.path.basename(CORPUS), expected_sha256=EXPECT_SHA,
                           n=int(n), d=int(d),
                           k=K, n_queries=NQ, seeds=SEEDS, knn=KNN),
               cells=cells)
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/scale.json", "w"), indent=1, sort_keys=True)
    print("\nelapsed %.1fs -> results/scale.json" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
