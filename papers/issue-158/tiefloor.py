"""tiefloor.py -- the instrument this package is about, and the three quantisers it is run on.

Everything here is a pure function of its arguments: no I/O, no globals, no hidden state. The
programs that produce results import this module; nothing in it writes a file.

WHY EVERY DISTANCE IS AN EXACT INTEGER
--------------------------------------
The subject of this package is *which distances are equal*. Measuring that in floating point
would measure rounding noise and call it a tie structure -- and the registration names this as a
known hazard ("the hamming-via-BLAS path can make two equal Hamming distances unequal in the last
bits"). SIFT descriptors are integer-valued (asserted by the loader), so:

  * product quantisation uses centroids rounded onto the data's own integer grid, and
  * scalar quantisation uses integer reconstruction levels,

which makes every reconstruction integer-valued and every squared distance an exact integer. The
distances are computed through one float32 GEMM, which is exact here because every intermediate
stays below 2**24 (max ||q-x||^2 = 128 * 255^2 = 8,323,200, and the largest intermediate,
2*|q.x|, is 16,646,400, both under 16,777,216). That bound is not assumed: `assert_exact`
recomputes a sample in int64 and refuses to return if any distance disagrees.

THE IDENTIFIED SET
------------------
recall@k against an exhaustive ground truth takes the k smallest distances. When several points
share the k-th distance, the procedure picks some of them arbitrarily. For a provably correct
index, the value the metric can take therefore lies in [floor, 1], where

    r     = k - #{points strictly nearer than the k-th distance}
    t     = #{points at the k-th distance}
    floor = ((k - r) + max(0, 2r - t)) / k

The floor is computable exactly, with no sampling. `floor` is the number this package reports.
"""

import numpy as np

K_DEFAULT = 10


def identified_set(k, dist_row):
    """(r, t, floor) for one query's distance row. `dist_row` must be exact integers or compare
    unreliably; callers pass values produced by `exact_sq_distances` or by Hamming on codes."""
    dk = np.partition(dist_row, k - 1)[k - 1]
    less = int(np.count_nonzero(dist_row < dk))
    t = int(np.count_nonzero(dist_row == dk))
    r = k - less
    return r, t, ((k - r) + max(0, 2 * r - t)) / k


def resolution(dist_row, knn=1000):
    """The metric's LOCAL resolution: how many distinct distance values the `knn` nearest occupy.

    This is the quantity the package's claim is about. A metric with few attainable values
    concentrates probability mass on each one, so n * P(D = d_k) -- the tie group -- is large; a
    metric with many atoms spreads the same mass thin and contracts it.
    """
    knn = min(knn, dist_row.size)
    thr = np.partition(dist_row, knn - 1)[knn - 1]
    return int(np.unique(dist_row[dist_row <= thr]).size)


def exact_sq_distances(Q, R, Rsq=None, block=32, check_pairs=64):
    """|q-x|^2 for every (query, reconstruction) pair, as exact integers in a float32 array.

    Raises if the float path disagrees with int64 on a sample, so no caller can score a tie on a
    path that was never verified. That check is the whole reason this function exists.
    """
    Q = np.ascontiguousarray(Q, dtype=np.int32)
    R = np.ascontiguousarray(R, dtype=np.int32)
    if Rsq is None:
        Rsq = (R.astype(np.int64) ** 2).sum(1)
    Rsq_f = Rsq.astype(np.float32)
    checked = False
    for lo in range(0, len(Q), block):
        qb = Q[lo:lo + block]
        qsq = (qb.astype(np.int64) ** 2).sum(1).astype(np.float32)
        D = qsq[:, None] - 2.0 * (qb.astype(np.float32) @ R.T.astype(np.float32)) + Rsq_f[None, :]
        D = np.rint(D)
        if not checked:
            idx = np.linspace(0, R.shape[0] - 1, check_pairs).astype(int)
            exact = ((R[idx].astype(np.int64) - qb[0].astype(np.int64)[None, :]) ** 2).sum(1)
            bad = int((exact != D[0, idx].astype(np.int64)).sum())
            if bad:
                raise AssertionError(
                    "float32 distance path disagrees with int64 on %d/%d sampled pairs; "
                    "refusing to score ties on an unverified path" % (bad, check_pairs))
            checked = True
        yield D


# ---------------------------------------------------------------------------- quantisers

def simhash_codes(X, P, b):
    """Random-hyperplane bits: sign(X @ P[:, :b]). Hamming distance attains b+1 values."""
    return (X.astype(np.float64) @ P[:, :b]) > 0


def hamming_blocks(codes, qcodes, b, block=32):
    """Exact integer Hamming distances, yielded in query-major blocks.

    The shape convention is the one `exact_sq_distances` uses -- each yielded matrix is
    (queries in this block) x (every corpus point) -- so a caller can measure any family with one
    loop. Hamming is computed from +-1 codes as (b - <S,Q>)/2, which is an exact integer; the
    matrix is built per query block rather than whole because 1e6 x 512 float32 is 2 GB.
    """
    S = np.where(codes, np.float32(1.0), np.float32(-1.0))
    Qs = np.where(qcodes, np.float32(1.0), np.float32(-1.0))
    for lo in range(0, Qs.shape[0], block):
        blk = Qs[lo:lo + block]
        # (n_corpus x b) @ (b x blk) -> (n_corpus x blk); transposed to query-major
        yield np.rint((b - (S @ blk.T)) / 2.0).T


def _kmeans_int(Xf, ncent, iters, rng):
    """k-means++ init then Lloyd iterations, on float64, returning integer centroids.

    Rounding to the integer grid is what makes the downstream distance exact; it also keeps the
    quantiser honest, since the data are integers and a non-integer reconstruction would be
    measuring the centroid's own rounding error rather than the code.
    """
    n, d = Xf.shape
    ncent = min(ncent, n)
    cent = np.empty((ncent, d), dtype=np.float64)
    cent[0] = Xf[rng.integers(0, n)]
    closest = ((Xf - cent[0]) ** 2).sum(1)
    for c in range(1, ncent):
        s = closest.sum()
        if s <= 0:
            cent[c] = Xf[rng.integers(0, n)]
        else:
            cent[c] = Xf[rng.choice(n, p=closest / s)]
        closest = np.minimum(closest, ((Xf - cent[c]) ** 2).sum(1))
    for _ in range(iters):
        D = (Xf ** 2).sum(1)[:, None] - 2.0 * Xf @ cent.T + (cent ** 2).sum(1)[None, :]
        lab = np.argmin(D, axis=1)
        for c in range(ncent):
            m = lab == c
            if m.any():
                cent[c] = Xf[m].mean(0)
    return np.rint(cent).astype(np.int32)


def pq_train_encode(X, m, rng, iters=12, sample=50000):
    """Product quantisation: m subspaces, 256 integer centroids each, codes as uint8."""
    n, d = X.shape
    sub = d // m
    cent, codes = [], np.empty((n, m), dtype=np.uint8)
    samp = rng.choice(n, min(sample, n), replace=False)
    for j in range(m):
        lo, hi = j * sub, (j + 1) * sub
        C = _kmeans_int(X[samp, lo:hi].astype(np.float64), 256, iters, rng)
        cent.append(C)
        for s in range(0, n, 100000):
            B = X[s:s + 100000, lo:hi].astype(np.int32)
            D = (B ** 2).sum(1)[:, None] - 2 * B @ C.T + (C ** 2).sum(1)[None, :]
            codes[s:s + 100000, j] = np.argmin(D, axis=1).astype(np.uint8)
    return cent, codes


def pq_reconstruct(X, cent, codes):
    n, d = X.shape
    m = len(cent)
    sub = d // m
    R = np.empty((n, d), dtype=np.int32)
    for j in range(m):
        R[:, j * sub:(j + 1) * sub] = cent[j][codes[:, j]]
    return R


def sq_levels(bits, qmax=255.0):
    """Uniform integer scalar quantisation: reconstruction levels are integers."""
    levels = 2 ** bits
    return np.rint(np.arange(levels) * qmax / (levels - 1)).astype(np.int32)


def sq_encode(X, bits, qmax=255.0):
    levels = 2 ** bits
    step = qmax / (levels - 1)
    code = np.rint(X.astype(np.float64) / step).astype(np.int32)
    return np.clip(code, 0, levels - 1).astype(np.uint8)


def sq_reconstruct(rec, code):
    return rec[code.astype(np.int32)]
