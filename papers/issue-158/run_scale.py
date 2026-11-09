#!/usr/bin/env python3
"""run_scale.py -- TIERS M and B: the same axis above the committed 20k subsample.

Tier A runs on a 20,000-descriptor fixture. These two tiers ask whether the ordering the axis
predicts survives larger n, and they answer it at two reachable scales:

  TIER M  (medium; `run_scale.py --medium`) reads `fixture/sift_medium.npz`: 200,000 descriptors
          cut from the same 1M corpus along the same seeded permutation as the 20k fixture, plus
          the corpus's whole 10,000-row query set. Numpy alone -- no corpus, no h5py, no network.
          This is the path by which a reader re-derives the axis at scale from committed bytes,
          and it is the 1M number's second, independent instrument.

  TIER B  (full; the default) reads the 1M corpus, which cannot be committed: `fetch_corpus.sh`
          retrieves it and checks its sha256, and when it is absent this program prints `NOT RUN`
          and exits 3. Not run is not a failure, and it is never reported as one.

Both tiers run THE SAME `measure()` over the same descriptor semantics and the same seeded query
draws: what differs between them is the array that goes in, never the statistics that come out. A
second implementation written for the medium scale would make the two readings incomparable in
exactly the way this file exists to avoid.

Reads  : fixture/sift_medium.npz (tier M) or $SIFT_HDF5 / corpus/sift-128-euclidean.hdf5 (tier B)
Writes : results/medium.json (tier M) or results/scale.json (tier B)
"""
import axis
import json
import os
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiefloor as T                                   # noqa: E402
import verify_fixture as V                             # noqa: E402

warnings.filterwarnings("ignore", message=".*encountered in matmul")

K = 10
NQ = 512
SEEDS = [7, 11, 13]
KNN = 1000
DATASET = "sift-128-euclidean"
CORPUS = os.environ.get("SIFT_HDF5", "corpus/sift-128-euclidean.hdf5")
EXPECT_SHA = "dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984"
MEDIUM = "fixture/sift_medium.npz"
MEDIUM_OUT = "results/medium.json"
SCALE_OUT = "results/scale.json"


def measure(X, test, label):
    """The measurement both scales run.

    X arrives as integer-valued descriptors in whatever dtype its store used (uint8 from the
    fixture, float32 from HDF5). The cast to int32 happens here, once, before anything is
    measured, so the two tiers cannot differ in the arithmetic they do.
    """
    n, d = X.shape
    X = X.astype(np.int32)
    assert np.all(X == np.round(X)) and X.min() >= 0
    print("%s %d x %d, %d seeds, %d queries/seed, k=%d" % (label, n, d, len(SEEDS), NQ, K))

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
    return cells, n, d


def run_medium():
    """Tier M: the committed 200k fixture, numpy alone.

    The digest is not restated here. It lives in `fixture/SHA256SUMS`, which step 1 of every
    reproduction verifies, and this program reads it from there: one pin, one place, so the
    program and the gate cannot disagree about which bytes were measured.
    """
    if not os.path.exists(MEDIUM):
        print("NOT RUN: the medium fixture is not present at %s" % MEDIUM)
        print("         it is committed; a checkout without it is incomplete (see %s)" % V.SUMS)
        return 3
    pin = V.recorded().get(MEDIUM)
    if not pin:
        print("NOT RUN: %s records no digest for %s, so the bytes below would be unnamed" % (V.SUMS, MEDIUM))
        return 3
    got = V.sha256(MEDIUM)
    if got != pin:
        print("FAILED: %s on disk is %s..., the package pins %s..." % (MEDIUM, got[:16], pin[:16]))
        print("        every number below would be about some other descriptors")
        return 1

    t0 = time.time()
    with np.load(MEDIUM) as z:
        X = z["train"]
        test = z["queries"]
        src = bytes(z["source_sha256"]).decode()
        seed = int(z["seed"][0])
        n_train = int(z["n_train"][0])
    if src != EXPECT_SHA:
        print("FAILED: the fixture says it was cut from corpus %s..., the package pins %s..."
              % (src[:16], EXPECT_SHA[:16]))
        return 1
    if (len(X), X.shape[1]) != (n_train, 128):
        print("FAILED: the fixture's own n_train is %d but its train block is %s" % (n_train, (X.shape,)))
        return 1

    # The nesting: this package reports three scales of one corpus, and they must be three views of
    # ONE inclusion chain, not three independent draws that happen to come from the same source. The
    # 20k fixture is the head of this fixture's permutation, so tier A's descriptors are literally
    # the first 20,000 rows measured below. That is a property of two committed files, checkable
    # offline, and it is checked here rather than asserted in prose: if a future rebuild cuts either
    # fixture from a different draw, the scales silently stop being comparable and every across-
    # scale sentence in the paper becomes a comparison of different populations.
    subset = "fixture/sift_subset.npz"
    if not os.path.exists(subset):
        print("FAILED: %s is absent, so the nesting with tier A cannot be checked" % subset)
        print("        both fixtures are committed; a checkout holding one is incomplete")
        return 1
    with np.load(subset) as zs:
        small = zs["train"]
    nested_rows = int(len(small))
    if not np.array_equal(small, X[:nested_rows]):
        print("FAILED: %s's %d descriptors are not the first %d rows of %s"
              % (subset, nested_rows, nested_rows, MEDIUM))
        print("        the two fixtures were cut from different draws, so the scales are not")
        print("        nested and no across-scale sentence in the paper is a comparison")
        return 1
    print("nested: %s's %d descriptors == %s' first %d rows"
          % (subset, nested_rows, MEDIUM, nested_rows))

    cells, n, d = measure(X, test, MEDIUM)
    out = dict(fixture=dict(path=MEDIUM, sha256=pin, source=DATASET, source_sha256=src,
                            seed=seed, n=int(n), d=int(d), k=K, n_queries=NQ,
                            seeds=SEEDS, knn=KNN, n_queries_available=int(len(test)),
                            nested_with=subset, nested_rows=nested_rows),
               cells=cells,
               **axis.at_evidence_count(cells))
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(MEDIUM_OUT, "w"), indent=1, sort_keys=True)
    print("\nelapsed %.1fs -> %s" % (time.time() - t0, MEDIUM_OUT))
    return 0


def run_full():
    """Tier B: the 1M corpus."""
    if not os.path.exists(CORPUS):
        print("NOT RUN: the 1M corpus is not present at %s" % CORPUS)
        print("         run ./fetch_corpus.sh (it verifies sha256 %s...)" % EXPECT_SHA[:16])
        print("         Tier A (run_mechanism.py) needs no corpus and is unaffected.")
        print("         Tier M (run_scale.py --medium) needs only the committed 200k fixture.")
        # Exit 3 is NOT RUN, and it is deliberately not 0. When this returned 0 a caller could not
        # tell "the step ran and agreed" from "the step never ran", so `./reproduce.sh full` printed
        # REPRODUCE: ALL GREEN while this tier had measured nothing -- a verdict that claims the 1M
        # number was reproduced by a run that did not compute it. 3 is not a failure either: a
        # declared dependency that is absent is never a failed step.
        return 3
    try:
        import h5py
    except ImportError:
        print("NOT RUN: h5py is not importable by %s, and the corpus is stored as HDF5." % sys.executable)
        print("         Tier A (run_mechanism.py) and tier M (run_scale.py --medium) need no h5py.")
        return 3

    t0 = time.time()
    with h5py.File(CORPUS, "r") as f:
        X = f["train"][:]
        test = f["test"][:]
    if X.shape != (1000000, 128):
        raise AssertionError("expected the 1M corpus, got %s" % (X.shape,))

    cells, n, d = measure(X, test, "corpus")

    # The artefact records the corpus by DATASET, never by path and never by the operator's
    # filename. Using basename(CORPUS) was the same leak one step smaller: a reader who follows the
    # README runs ./fetch_corpus.sh, which names the file `sift-128-euclidean.hdf5`, while the
    # committed artefact had been produced from `research/sift1m.hdf5` -- so the documented path
    # regenerated every number identically and still failed a byte comparison, on a field whose
    # value is the operator's choice rather than the corpus's identity. The content is already
    # identified by expected_sha256; the name is now the dataset id both paths agree on.
    # The 1M number that carries the P1 refutation ships with its own sensitivity: the review's M4
    # and M2 both land on the same gap, that a headline number read from a committed artefact and
    # never re-derived must at least carry the design property that makes it readable as evidence.
    out = dict(corpus=dict(name=DATASET, expected_sha256=EXPECT_SHA,
                           n=int(n), d=int(d),
                           k=K, n_queries=NQ, seeds=SEEDS, knn=KNN),
               cells=cells,
               **axis.at_evidence_count(cells))
    os.makedirs("results", exist_ok=True)
    json.dump(out, open(SCALE_OUT, "w"), indent=1, sort_keys=True)
    print("\nelapsed %.1fs -> %s" % (time.time() - t0, SCALE_OUT))
    return 0


def main(argv):
    if len(argv) > 1 and argv[1] == "--medium":
        return run_medium()
    if len(argv) > 1 and argv[1] != "--full":
        print("usage: run_scale.py [--medium|--full]")
        return 2
    return run_full()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
