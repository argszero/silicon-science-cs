#!/usr/bin/env python3
"""build_fixture.py -- cut the shipped fixture out of the 1M corpus, once, for the maintainer.

Why a fixture exists at all
---------------------------
A clean machine must be able to reproduce every number this package states. The 1M corpus is
525 MB and cannot be committed, so the package ships:

  * `fixture/sift_subset.npz` -- a committed, numpy-ONLY subsample (no h5py, no network), which
    every number in the paper's mechanism table is reproduced from; and
  * `fetch_corpus.sh` -- a pinned fetch with a sha256 for the 1M corpus, which the scale tier
    needs and which reports NOT RUN (not a failure) when the corpus is absent.

The two tiers are declared separately in `reproduce.sh`, and the paper names which tier each
number comes from.

This script is the maintainer's path: it needs h5py and the 1M corpus. A reader never runs it.
The fixture it writes is committed, and `reproduce.sh` verifies the fixture's sha256 before using
it, so the committed bytes -- not this script -- are what a reader depends on.

    python3 build_fixture.py <path-to-sift1m.hdf5>

Deterministic: the subsample is the first N rows of one fixed permutation, drawn from a seeded
generator, so re-running on the same corpus reproduces the same fixture byte for byte.
"""
import hashlib
import sys

import numpy as np

N_TRAIN = 20000
N_TRAIN_MEDIUM = 200000
N_QUERY = 200
SEED = 20261030
OUT = "fixture/sift_subset.npz"
OUT_MEDIUM = "fixture/sift_medium.npz"


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def main(argv):
    medium = len(argv) > 1 and argv[1] == "--medium"
    if medium:
        argv = argv[:1] + argv[2:]
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1])
        print("       python3 build_fixture.py --medium <path-to-sift1m.hdf5>")
        return 2
    src = argv[1]
    import h5py                                     # maintainer-only dependency

    digest = sha256(src)
    print("source: %s" % src)
    print("sha256: %s" % digest)
    with h5py.File(src, "r") as f:
        train = f["train"][:]
        test = f["test"][:]
    assert train.shape[1] == 128 and test.shape[1] == 128
    assert np.all(train == np.round(train)) and train.min() >= 0, "expected integer-valued SIFT"

    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(train))
    if medium:
        # Same permutation as the 20k fixture, read further along it: the first N_TRAIN rows of
        # this train block ARE `fixture/sift_subset.npz`'s train block, so the three scales the
        # paper reports (20k, 200k, 1M) sit on one inclusion chain rather than on three unrelated
        # draws. `reproduce.sh` asserts that nesting; it is the property that lets a reader read
        # the axis across scales instead of comparing three samples of different populations.
        #
        # The whole 10,000-row query set ships because the measurement draws its queries from it
        # BY SEED. Shipping only the rows one seed happens to pick would bake one design's choice
        # into the fixture's bytes and make every later seed a re-use of that choice.
        X = train[perm[:N_TRAIN_MEDIUM]].astype(np.uint8)
        Q = test.astype(np.uint8)
        out, n_train = OUT_MEDIUM, N_TRAIN_MEDIUM
    else:
        qidx = rng.permutation(len(test))
        X = train[perm[:N_TRAIN]].astype(np.uint8)
        Q = test[qidx[:N_QUERY]].astype(np.uint8)
        out, n_train = OUT, N_TRAIN

    import os
    os.makedirs("fixture", exist_ok=True)
    np.savez_compressed(out, train=X, queries=Q,
                        source_sha256=digest.encode(),
                        seed=np.array([SEED]), n_train=np.array([n_train]))
    new = sha256(out)
    print("wrote %s (%d x %d train, %d x %d queries)" % (out, *X.shape, *Q.shape))
    print("fixture sha256: %s" % new)
    print("   -> record this in fixture/SHA256SUMS; reproduce.sh verifies it")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
