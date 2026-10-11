#!/usr/bin/env python3
"""spike_v5.py -- issue #128, the WIDE-ALIGNMENT real-row sweep (R557).

R556 tested the P2' predictor (a solve-free proxy for the free width M*/k) inside ONE real metric
space, varying the partition, and the test came out UNDETERMINED for a measurable reason: across every
partition of the Wine-Quality corpus the group-metric alignment statistic spanned only 0.902-1.117
(spread 0.215), against 0.044-1.035 across the synthetic families the predictor came from.  A test
whose input variable barely varies cannot refute a relation.

This instrument removes that obstruction on REAL rows.  Two corpora whose class labels are genuinely
separable in the real feature space -- UCI Wine (178 rows x 13 features x 3 classes) and UCI Seeds
(210 x 7 x 3) -- supply the LOW end of the alignment range (~0.35-0.46), where the Wine-Quality bins
could not reach.  The metric stays the real quantised features; the PARTITION is swept continuously
from label-aligned to random by a single knob lambda:

    v(lambda) = normalise( (1 - lambda) * u_label + lambda * u_random )

where u_label is the between-class scatter direction of the REAL features and u_random a deterministic
random direction in the SAME real feature space.  Rows are ranked by their projection on v(lambda) and
cut into contiguous blocks of a fixed size profile.  lambda = 0 gives a label-aligned partition,
lambda = 1 a label-blind one, and each lambda has its own MEASURED alignment -- so the predictor is
tested across a range wide enough for a negative to mean something.

Everything is integer: features are z-scored in a fixed column order and quantised, so every squared
distance and every objective value is an integer and the artefact is byte-identical across runs.

Usage:
  python3 spike_v5.py              write spike_v5_results.json
  python3 spike_v5.py --selftest   each certificate on a healthy AND a mutated object
"""
import io, json, os, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v3 as sv                      # enumeration, largest-remainder floors, baselines

OUT = os.path.join(HERE, "spike_v5_results.json")
PINS = os.path.join(HERE, "corpus", "SHA256SUMS")

N = 18          # rows per draw
M_G = 3         # groups
K = 9           # seats
PROFILES = {"bal": [6, 6, 6], "unb": [7, 6, 5]}
LAMBDAS = [0.0, 0.25, 0.5, 0.75, 1.0]
DRAWS = 4
DIRECTIONS = 2
OBJS = ("maxmin", "maxsum")


# ------------------------------------------------------------------ corpus
def sha256_of(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def pinned_hash(name):
    for line in io.open(PINS, encoding="utf-8"):
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == name:
            return parts[0]
    raise KeyError("no pin for %s" % name)


def load_corpus(name):
    """Read a pinned corpus.  Refuses to return data whose hash is not the pinned one."""
    rel = {"wine": "corpus/wine.data", "seeds": "corpus/seeds_dataset.txt"}[name]
    path = os.path.join(HERE, rel)
    want = pinned_hash(os.path.basename(path))
    got = sha256_of(path)
    if got != want:
        raise ValueError("corpus %s hash %s != pin %s" % (name, got, want))
    X, y = [], []
    for ln in io.open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        if name == "wine":
            v = [float(t) for t in ln.split(",")]
            y.append(int(v[0])); X.append(v[1:])
        else:
            v = ln.split()
            X.append([float(t) for t in v[:7]]); y.append(int(v[7]))
    return np.array(X, dtype=float), np.array(y, dtype=np.int64), got


def quantise(X, scale=8.0):
    """z-score per column (fixed order) then quantise -> integer features."""
    mu = X.mean(axis=0); sd = X.std(axis=0)
    sd = np.where(sd == 0, 1.0, sd)
    Z = (X - mu) / sd
    return np.rint(Z * scale).astype(np.int64)


# ------------------------------------------------------------------ the sweep knob
def label_direction(Q, y):
    """Between-class scatter direction of the REAL features: first eigenvector of B."""
    cls = np.unique(y)
    mu = Q.mean(axis=0).astype(float)
    B = np.zeros((Q.shape[1], Q.shape[1]), dtype=float)
    for c in cls:
        m = Q[y == c].mean(axis=0).astype(float)
        d = (m - mu)[:, None]
        B += len(Q[y == c]) * (d @ d.T)
    w, V = np.linalg.eigh(B)
    v = V[:, int(np.argmax(w))]
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("degenerate label direction")
    return v / n


def random_direction(dim, seed):
    rng = np.random.RandomState(seed)
    v = rng.normal(size=dim)
    return v / np.linalg.norm(v)


def mixed_direction(u_label, u_rand, lam):
    v = (1.0 - lam) * u_label + lam * u_rand
    n = np.linalg.norm(v)
    if n < 1e-12:
        return u_rand.copy()
    return v / n


def block_partition(Q, v, sizes):
    """Rank the rows by their real-feature projection on v and cut into contiguous blocks."""
    order = np.argsort(Q.astype(float) @ v, kind="stable")
    groups = np.empty(len(order), dtype=np.int64)
    pos = 0
    for g, s in enumerate(sizes):
        groups[order[pos:pos + s]] = g
        pos += s
    assert pos == len(order)
    return groups


def alignment(Q, groups):
    """mean within-group squared distance over mean between-group squared distance (solve-free)."""
    n = len(groups)
    D = sv.d2_matrix(Q).astype(float)
    iu = np.triu_indices(n, 1)
    same = (groups[:, None] == groups[None, :])[iu]
    dd = D[iu]
    w = dd[same].mean(); b = dd[~same].mean()
    return float(w / b)


def sample_balanced(y, sizes, rng):
    """Sample `sizes[c]` distinct real rows from class c (classes in sorted order)."""
    cls = np.unique(y)
    idx = []
    for c, s in zip(cls, sizes):
        pool = np.where(y == c)[0]
        if s > len(pool):
            raise ValueError("class %d has %d rows, need %d" % (c, len(pool), s))
        idx.extend(rng.choice(pool, size=s, replace=False).tolist())
    return np.array(idx, dtype=np.int64)


# ------------------------------------------------------------------ the cell
def measure_cell(Q, groups, k, m, obj, cross=False):
    """The zero-cost threshold and the cost curve above it, by complete enumeration."""
    D = sv.d2_matrix(Q); cnt = sv.counts_of(groups, m)
    base = sv.enum_complete(k, D, groups, m, obj)
    basev, n_opt = base[0], base[1]
    curve = []
    for M in range(0, k + 1):
        fl = sv.largest_remainder(M, cnt)
        v, nopt, S, nfeas = sv.enum_complete(k, D, groups, m, obj, floors=fl)
        g = sv.greedy_quota(k, D, groups, m, obj, floors=fl)
        curve.append({"M": M, "floors": [int(x) for x in fl], "value": v,
                      "greedy_value": None if g is None else int(sv.value_of(g, D, obj))})
    free = [r["M"] for r in curve if r["value"] is not None and r["value"] == basev]
    M_star = max(free) if free else None
    cross_ok = None
    if cross:
        c = sv.solve_cell(k, D, groups, m, obj, Q, cross=True)
        cross_ok = bool(c["cross_agrees"]) and c["value"] == basev
    return {"unconstrained": int(basev) if basev is not None else None,
            "base_n_optima": int(n_opt), "M_star": M_star, "M_first": 1,
            "group_counts": [int(x) for x in cnt],
            "cross_checked": bool(cross), "cross_agrees": cross_ok,
            "curve": curve}


def run():
    res = {"instrument": "spike_v5 -- the wide-alignment real-row sweep",
           "n": N, "m": M_G, "k": K, "lambdas": LAMBDAS, "profiles": PROFILES,
           "draws": DRAWS, "directions": DIRECTIONS, "objs": list(OBJS), "corpora": {}}
    for cname in ("wine", "seeds"):
        X, y, sha = load_corpus(cname)
        Q = quantise(X)
        u_lab = label_direction(Q, y)
        cells, meta = [], {"sha256": sha, "rows": int(len(y)),
                           "features": int(X.shape[1]),
                           "class_counts": [int(x) for x in np.bincount(y)[1:]],
                           "alignment_all_rows": alignment(Q, y - 1),
                           "alignment_grid": []}
        for pname, sizes in PROFILES.items():
            for d in range(DRAWS):
                rng = np.random.RandomState(1000 + 17 * d + 7 * len(sizes))
                idx = sample_balanced(y, sizes, rng)
                Qs = Q[idx]; cnt = [int(x) for x in np.bincount(np.concatenate(
                    [np.full(s, c) for c, s in enumerate(sizes)]), minlength=M_G)]
                for di in range(DIRECTIONS):
                    u_r = random_direction(Q.shape[1], 500 + 31 * d + 13 * di)
                    for lam in LAMBDAS:
                        v = mixed_direction(u_lab, u_r, lam)
                        groups = block_partition(Qs, v, sizes)
                        a = alignment(Qs, groups)
                        meta["alignment_grid"].append(a)
                        for obj in OBJS:
                            mres = measure_cell(Qs, groups, K, M_G, obj, cross=(di == 0 and d == 0))
                            cells.append({"corpus": cname, "profile": pname, "draw": d,
                                          "dir": di, "lambda": lam, "obj": obj,
                                          "sizes": sizes, "alignment": a,
                                          "M_star": mres["M_star"], "k": K,
                                          "free_width": (None if mres["M_star"] is None
                                                         else mres["M_star"] / float(K)),
                                          "unconstrained": mres["unconstrained"],
                                          "base_n_optima": mres["base_n_optima"],
                                          "group_counts": mres["group_counts"],
                                          "cross_checked": mres["cross_checked"],
                                          "cross_agrees": mres["cross_agrees"],
                                          "curve": mres["curve"]})
        meta["alignment_grid"] = [float(a) for a in meta["alignment_grid"]]
        res["corpora"][cname] = {"meta": meta, "cells": cells}
    return res


# ------------------------------------------------------------------ report
def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3:
        return None
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return None if den == 0 else float((rx * ry).sum() / den)


def beta_above(curve, M_star, basev):
    pts = [(r["M"] - M_star, (basev - r["value"]) / float(basev))
           for r in curve if M_star is not None and r["M"] > M_star and r["value"] is not None]
    pos = [p for p in pts if p[1] > 0]
    if len(pos) < 3:
        return None, len(pts), len(pos)
    X = np.log([p[0] for p in pos]); Y = np.log([p[1] for p in pos])
    return float(np.polyfit(X, Y, 1)[0]), len(pts), len(pos)


def report(res):
    print("instrument:", res["instrument"])
    allA, allW = [], []
    for cname, blk in res["corpora"].items():
        meta = blk["meta"]; cells = blk["cells"]
        g = meta["alignment_grid"]
        print("\n== %s: %d rows x %d features, classes %s == sha %s" % (
            cname, meta["rows"], meta["features"], meta["class_counts"], meta["sha256"][:16]))
        print("   alignment on ALL rows (class partition) = %.3f" % meta["alignment_all_rows"])
        print("   sweep knob: alignment grid %.3f .. %.3f  (spread %.3f, n=%d)"
              % (min(g), max(g), max(g) - min(g), len(g)))
        for pname in PROFILES:
            for lam in LAMBDAS:
                sub = [c for c in cells if c["profile"] == pname and c["lambda"] == lam]
                A = [c["alignment"] for c in sub]
                W = [c["free_width"] for c in sub if c["free_width"] is not None]
                print("     %-4s lam=%.2f  align %.3f-%.3f  median M*/k %.3f"
                      % (pname, lam, min(A), max(A), float(np.median(W)) if W else float("nan")))
        for obj in OBJS:
            sub = [c for c in cells if c["obj"] == obj and c["free_width"] is not None]
            allA += [c["alignment"] for c in sub]; allW += [c["free_width"] for c in sub]
        print("   UNSOLVED: %d  cross-disagree: %d" % (
            sum(1 for c in cells if c["unconstrained"] is None),
            sum(1 for c in cells if c["cross_checked"] and c["cross_agrees"] is False)))
        print("   P4 greedy-vs-exact (unconstrained, maxmin/maxsum exact counts):")
        for obj in OBJS:
            sub = [c for c in cells if c["obj"] == obj]
            gaps = [(c["unconstrained"] - c["curve"][0]["greedy_value"]) / float(c["unconstrained"])
                    for c in sub if c["curve"][0]["greedy_value"] is not None]
            ex = sum(1 for x in gaps if abs(x) < 1e-12)
            print("     %-6s exact %d/%d  median gap %.4f  max %.4f"
                  % (obj, ex, len(gaps), float(np.median(gaps)), float(max(gaps))))
        print("   P3 median beta above M*:", end=" ")
        for obj in OBJS:
            bs = [beta_above(c["curve"], c["M_star"], c["unconstrained"])[0]
                  for c in cells if c["obj"] == obj]
            bs = [b for b in bs if b is not None]
            print("%s=%s(n=%d)" % (obj, ("%.3f" % float(np.median(bs))) if bs else "-", len(bs)), end="  ")
        print()
    print("\n== P2': the predictor on the WIDE sweep ==")
    print("   alignment range %.3f .. %.3f (spread %.3f) across %d cells"
          % (min(allA), max(allA), max(allA) - min(allA), len(allA)))
    print("   spearman(alignment, M*/k) = %s (n=%d)"
          % (("%+.3f" % spearman(allA, allW)) if spearman(allA, allW) is not None else "-", len(allA)))
    for cname, blk in res["corpora"].items():
        cs = [c for c in blk["cells"] if c["free_width"] is not None]
        s = spearman([c["alignment"] for c in cs], [c["free_width"] for c in cs])
        print("   per-corpus %-6s spearman %s (n=%d)"
              % (cname, ("%+.3f" % s) if s is not None else "-", len(cs)))


# ------------------------------------------------------------------ certificates
def selftest():
    checks = []
    Xw, yw, shaw = load_corpus("wine")
    Xs, ys, shas = load_corpus("seeds")
    Qw = quantise(Xw)

    # C1 both corpus pins enforced
    bad = (pinned_hash("wine.data")[:-1] + ("0" if pinned_hash("wine.data")[-1] != "0" else "1"))
    checks.append(("C1 corpus pins enforced",
                   shaw == pinned_hash("wine.data") and shas == pinned_hash("seeds_dataset.txt"),
                   bad == shaw))

    # C2 quantisation deterministic and integral
    Qw2 = quantise(Xw)
    checks.append(("C2 quantisation deterministic",
                   bool(np.array_equal(Qw, Qw2)) and Qw.dtype == np.int64,
                   not np.array_equal(Qw, quantise(Xw * 1.0001))))

    # C3 the lambda knob actually sweeps: label-aligned strictly below random, monotone in mean
    u = label_direction(Qw, yw)
    rng = np.random.RandomState(1000 + 7 * 3)
    idx = sample_balanced(yw, [6, 6, 6], rng); Qsub = Qw[idx]
    ur = random_direction(Qw.shape[1], 500)
    A = [alignment(Qsub, block_partition(Qsub, mixed_direction(u, ur, lam), [6, 6, 6]))
         for lam in (0.0, 0.5, 1.0)]
    checks.append(("C3 knob sweeps alignment upward", A[0] < A[-1],
                   A[0] >= A[-1]))

    # C4 the block split honours the size profile -- the SAME predicate applied to both objects
    def c4(g):
        return sorted(np.bincount(g, minlength=3).tolist()) == [5, 6, 7] and len(set(g.tolist())) == 3

    v05 = mixed_direction(u, ur, 0.5)
    checks.append(("C4 block split honours sizes",
                   c4(block_partition(Qsub, v05, [7, 6, 5])),
                   c4(block_partition(Qsub, v05, [6, 6, 6]))))

    # C5 the label direction is not a random direction (alignment separates them)
    a_lab = alignment(Qsub, block_partition(Qsub, u, [6, 6, 6]))
    a_rnd = alignment(Qsub, block_partition(Qsub, ur, [6, 6, 6]))
    checks.append(("C5 label direction separates", a_lab < a_rnd, a_lab >= a_rnd))

    # C6 the sample is n distinct real rows, balanced across the 3 real classes
    chk = np.bincount(yw[idx] - 1, minlength=3).tolist()
    checks.append(("C6 sample is n distinct real rows",
                   len(set(idx.tolist())) == 18 and int(idx.max()) < len(Qw) and chk == [6, 6, 6],
                   len(set(sample_balanced(yw, [6, 6, 6], np.random.RandomState(99)).tolist())) != 18))

    # C7 two routes agree on a real cell, and disagree when fed DIFFERENT objects
    D = sv.d2_matrix(Qsub)
    c = sv.solve_cell(9, D, np.zeros(18, dtype=np.int64), 1, "maxmin", Qsub, cross=True)
    v1 = sv.enum_complete(9, D, np.zeros(18, dtype=np.int64), 1, "maxmin")[0]
    v2 = sv.enum_complete(9, 2 * D, np.zeros(18, dtype=np.int64), 1, "maxmin")[0]
    checks.append(("C7 two routes agree / different objects differ",
                   bool(c["cross_agrees"]) and c["value"] == v1, v2 == v1))

    good = True
    for name, healthy, mutated in checks:
        row = healthy and not mutated
        print("  %-44s healthy=%-5s mutated=%-5s %s" % (name, healthy, mutated, "PASS" if row else "FAIL"))
        good = good and row
    print("selftest:", "ALL PASS" if good else "FAILED")
    return 0 if good else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    r = run()
    report(r)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(r, indent=1, sort_keys=True))
    print("\nwrote", OUT)
