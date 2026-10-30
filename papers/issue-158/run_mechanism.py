#!/usr/bin/env python3
"""run_mechanism.py -- TIER A: the package's central table, from the committed fixture.

Question: what governs the size of the boundary tie group -- the quantiser family, or the
resolution of the distance the family induces?

Three families at equal budgets, all measured on the same corpus and the same queries:
random-hyperplane (SimHash/Hamming), product quantisation, and scalar quantisation. For each cell
the program records the boundary tie group `t`, the identified-set floor, and `atoms` -- the
number of distinct distance values occupied by the 1000 nearest points. If `atoms` orders `t`
across families, the family label is not the variable and the claim is the axis.

Two endpoint controls are run in the same program, and they are not decoration: an instrument
that cannot be made to return "fully identified" and cannot be made to return "maximally
unidentified" has not been shown to measure either.

  * float endpoint -- distances on the raw descriptors. The boundary tie group is 1 for
    essentially every query, so the identified set has width 0. Any instrument reporting otherwise
    here is measuring itself.
  * constructed endpoint -- every point replaced by one repeated reconstruction, so the entire
    corpus is one tie group and the floor is pinned at the value the arithmetic forces.

Reads  : fixture/sift_subset.npz   (committed; numpy only -- no h5py, no network)
Writes : results/mechanism.json, results/mechanism.txt
"""
import json
import os
import statistics
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiefloor as T                                   # noqa: E402

warnings.filterwarnings("ignore", message=".*encountered in matmul")

K = 10
SEEDS = [7, 11, 13]
KNN = 1000
FIXTURE = "fixture/sift_subset.npz"


def cells_for(dist_fn, nq, k=K):
    """Per-query (t, floor, atoms) over every query, for one distance field."""
    out = []
    for D in dist_fn():
        for j in range(D.shape[0]):
            r, t, fl = T.identified_set(k, D[j])
            out.append((t, fl, T.resolution(D[j], KNN)))
    return out


def summarise(tag, rows):
    ts = [r[0] for r in rows]
    fs = [r[1] for r in rows]
    ats = [r[2] for r in rows]
    return dict(tag=tag, n_queries=len(rows),
                median_t=round(float(statistics.median(ts)), 3),
                mean_t=round(float(statistics.mean(ts)), 3),
                max_t=int(max(ts)),
                median_atoms=int(statistics.median(ats)),
                mean_atoms=int(statistics.mean(ats)),
                mean_floor=round(float(statistics.mean(fs)), 4),
                frac_floor_lt1=round(sum(1 for f in fs if f < 1 - 1e-12) / len(fs), 4),
                frac_whole_topk=round(sum(1 for t in ts if t >= K) / len(ts), 4))


def main():
    t0 = time.time()
    z = np.load(FIXTURE)
    X = z["train"]
    Q = z["queries"]
    n, d = X.shape
    print("fixture: %d x %d, %d queries, source sha256 %s..."
          % (n, d, len(Q), z["source_sha256"].tobytes().decode()[:16]))
    assert np.all(X == np.round(X)) and X.min() >= 0

    cells = []

    # ---------------------------------------------------------------- float endpoint control
    rows = []
    for D in T.exact_sq_distances(Q, X):
        for j in range(D.shape[0]):
            r, t, fl = T.identified_set(K, D[j])
            rows.append((t, fl, T.resolution(D[j], KNN)))
    cells.append(summarise("float/raw descriptors", rows))

    # ---------------------------------------------------------------- constructed endpoint
    R0 = np.repeat(X[:1], len(X), axis=0)               # every point is the same point
    rows = []
    for D in T.exact_sq_distances(Q[:20], R0):
        for j in range(D.shape[0]):
            r, t, fl = T.identified_set(K, D[j])
            rows.append((t, fl, T.resolution(D[j], KNN)))
    cells.append(summarise("constructed/all points identical", rows))

    # ---------------------------------------------------------------- family A: SimHash
    bmax = max(256, 128, 64, 32)
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        P = rng.standard_normal((d, bmax))
        codes = T.simhash_codes(X, P, bmax)
        qcodes = T.simhash_codes(Q, P, bmax)
        for b in [256, 128, 64, 32]:
            rows = []
            for D in T.hamming_blocks(codes[:, :b], qcodes[:, :b], b):
                for j in range(D.shape[0]):
                    r, t, fl = T.identified_set(K, D[j])
                    rows.append((t, fl, T.resolution(D[j], KNN)))
            cells.append(summarise("Hamming/%dbit/seed%d" % (b, seed), rows))

    # ---------------------------------------------------------------- family B: PQ
    for bits in [32, 64]:
        m = bits // 8
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            cent, codes = T.pq_train_encode(X, m, rng)
            R = T.pq_reconstruct(X, cent, codes)
            # iterate EVERY block: exact_sq_distances is a block generator, and taking only the
            # first one measures 32 queries while the cell reports a corpus-wide number.
            rows = []
            for D in T.exact_sq_distances(Q, R):
                for j in range(D.shape[0]):
                    r, t, fl = T.identified_set(K, D[j])
                    rows.append((t, fl, T.resolution(D[j], KNN)))
            cells.append(summarise("PQ/%dbit/seed%d" % (bits, seed), rows))
            del R

    # ---------------------------------------------------------------- family C: SQ
    for q in [2, 4]:
        rec = T.sq_levels(q)
        code = T.sq_encode(X, q)
        R = T.sq_reconstruct(rec, code)
        rows = []
        for D in T.exact_sq_distances(Q, R):
            for j in range(D.shape[0]):
                r, t, fl = T.identified_set(K, D[j])
                rows.append((t, fl, T.resolution(D[j], KNN)))
        cells.append(summarise("SQ/%dbit-per-component/seedless" % q, rows))
        del R, code

    # ---------------------------------------------------------------- the axis, tested
    fam = [c for c in cells if c["tag"].startswith(("Hamming", "PQ", "SQ"))]
    xs = np.array([c["median_atoms"] for c in fam], dtype=float)
    ys = np.array([c["median_t"] for c in fam], dtype=float)
    rho = float(np.corrcoef(np.log(xs), np.log(ys))[0, 1])
    print("\n=== cells (family x budget), ordered by the metric's local resolution ===")
    print("%-32s %8s %8s %8s %8s" % ("cell", "atoms", "med t", "mean t", "floor"))
    for c in sorted(fam, key=lambda c: c["median_atoms"]):
        print("%-32s %8d %8.1f %8.2f %8.4f"
              % (c["tag"], c["median_atoms"], c["median_t"], c["mean_t"], c["mean_floor"]))
    print("\ncontrols:")
    for c in cells:
        if not c["tag"].startswith(("Hamming", "PQ", "SQ")):
            print("%-32s %8d %8.1f %8.2f %8.4f"
                  % (c["tag"], c["median_atoms"], c["median_t"], c["mean_t"], c["mean_floor"]))
    print("\nPearson r on log(atoms) vs log(median t) = %.4f over %d cells" % (rho, len(fam)))

    out = dict(corpus=dict(source="ann-benchmarks sift-128-euclidean, committed subsample",
                           source_sha256=z["source_sha256"].tobytes().decode(),
                           n=n, d=int(d), n_queries=int(len(Q)), knn=KNN, k=K),
               fixture_sha256=os.environ.get("FIXTURE_SHA256", ""),
               cells=cells, log_log_pearson=round(rho, 4), n_cells=len(fam),
               exactness="all integer-valued reconstructions; float32 path asserted vs int64 "
                         "on every call (tiefloor.exact_sq_distances)")
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/mechanism.json", "w"), indent=1, sort_keys=True)
    print("\nelapsed %.1fs -> results/mechanism.json" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
