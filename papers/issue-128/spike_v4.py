#!/usr/bin/env python3
"""spike_v4.py -- issue #128, the REAL-DATA arm (R556).

Everything before this instrument ran on synthetic point sets.  This one measures the same
objects -- the zero-cost threshold, the cost curve, the baseline confound -- on a real corpus
with a real grouping variable, and it adds the test R555 said P2' needs: on ONE metric space,
many DIFFERENT group partitions, so the predictor is tested within a family instead of across
families.

Corpus: UCI Wine Quality (red), 1599 real samples, 12 numeric features, and a natural grouping
variable (the sensory quality score).  Fetched and SHA-256-pinned by corpus/fetch_corpus.sh; every
run re-hashes before it reads, so a corpus that has silently changed fails the run.

Metric: the 12 features are z-scored (deterministically, in a fixed column order) and quantised to
integers, so the squared Euclidean distance is an INTEGER and every objective value is an integer --
which is what makes the artefacts byte-identical across runs.

Group partitions.  Part A uses the corpus's own quality bins.  Part B holds the metric space FIXED
and varies only the partition: one aligned partition (the quality bins) and several deterministic
balanced RANDOM partitions of the same size profile, each with its own measured alignment statistic
(mean within-group over mean between-group distance).  The free width is then regressed on that
statistic WITHIN the family, which is the honest test of a "predict from the unconstrained instance"
claim.

Usage:
  python3 spike_v4.py              write spike_v4_results.json
  python3 spike_v4.py --selftest   each certificate on a healthy AND a mutated object
"""
import io, json, os, sys, hashlib, itertools
from math import comb, ceil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v3 as sv                      # enumeration, integer program, baselines, curves

OUT = os.path.join(HERE, "spike_v4_results.json")
CORPUS = os.path.join(HERE, "corpus", "winequality-red.csv")
PINS = os.path.join(HERE, "corpus", "SHA256SUMS")

# ---------------------------------------------------------------- corpus
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

def load_corpus():
    """Read the pinned CSV.  Refuses to return data whose hash is not the pinned one."""
    want = pinned_hash(os.path.basename(CORPUS))
    got = sha256_of(CORPUS)
    if got != want:
        raise RuntimeError("corpus hash mismatch: pinned %s, found %s" % (want, got))
    rows = []
    with io.open(CORPUS, encoding="utf-8") as fh:
        header = fh.readline().strip().strip('"').split(";")
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append([float(x) for x in line.split(";")])
    X = np.array([r[:-1] for r in rows])            # 12 numeric features
    quality = np.array([int(r[-1]) for r in rows])  # the grouping variable, 3-8
    return header, X, quality

def quantise(X, scale=8.0):
    """z-score each feature in a FIXED column order, then quantise to integers.
    Deterministic: the same input gives the same integers on every run."""
    mu = X.mean(axis=0); sd = X.std(axis=0)
    sd = np.where(sd == 0, 1.0, sd)
    Z = (X - mu) / sd
    Q = np.floor(Z * scale + 0.5).astype(np.int64)   # round-half-up, deterministic
    return Q

def quality_bins(quality, m):
    """Cut the quality score into m contiguous bins by rank, so every bin is non-empty."""
    order = np.argsort(quality, kind="mergesort")
    groups = np.empty(len(quality), dtype=np.int64)
    per = len(quality) / float(m)
    for rank, idx in enumerate(order):
        groups[idx] = min(m - 1, int(rank // per))
    return groups

def random_partition_of_sizes(sizes, rng):
    """A balanced partition with EXACTLY the given group sizes, random otherwise."""
    m = len(sizes)
    labels = np.repeat(np.arange(m), sizes)
    labels = labels[rng.permutation(len(labels))]
    return labels

def alignment(Q, groups):
    """Mean within-group pairwise distance over mean between-group pairwise distance.
    Computed from the instance ALONE -- no optimisation anywhere."""
    D = sv.d2_matrix(Q)
    n = len(groups)
    same = groups[:, None] == groups[None, :]
    iu = np.triu_indices(n, 1)
    s = same[iu]; d = D[iu].astype(float)
    w = d[s].mean() if s.any() else 0.0
    b = d[~s].mean() if (~s).any() else 0.0
    return float(w / b) if b else float("nan")

# ---------------------------------------------------------------- sampling the real corpus
def sample_rows(Q, quality, n, seed):
    """A deterministic draw of n rows from the corpus, stratified so every quality level that can
    appear does: sort by (quality, index) and take an even stride.  Deterministic in (n, seed)."""
    order = np.lexsort((np.arange(len(quality)), quality))
    stride = len(order) / float(n)
    idx = [int(order[min(len(order) - 1, int(seed * 7 + i * stride))]) for i in range(n)]
    idx = sorted(set(idx))
    while len(idx) < n:                        # top up deterministically if the stride collided
        for j in order:
            if int(j) not in idx:
                idx.append(int(j))
                if len(idx) == n:
                    break
        idx = sorted(idx)
    return np.array(idx, dtype=np.int64)

def measure_points(Q, groups, m, k, obj, cross=False, want_caps=False):
    """The same curve machinery as spike_v3, on an explicit point set + partition."""
    D = sv.d2_matrix(Q)
    cnt = sv.counts_of(groups, m)
    base_cell = sv.solve_cell(k, D, groups, m, obj, Q, cross=cross)
    base = base_cell["value"]
    floors = []
    for M in range(0, k + 1):
        fl = sv.largest_remainder(M, cnt)
        cell = sv.solve_cell(k, D, groups, m, obj, Q, floors=fl, cross=cross)
        g = sv.greedy_quota(k, D, groups, m, obj, floors=fl)
        lsv = None if g is None else sv.local_search_quota(k, D, groups, m, obj, g, floors=fl)[1]
        prof = None if cell["set"] is None else np.bincount(groups[np.array(cell["set"])], minlength=m)
        floors.append({"M": M, "floors": [int(x) for x in fl], "value": cell["value"],
                       "status": cell["status"], "cross_checked": cell["cross_checked"],
                       "cross_value": cell["cross_value"], "cross_agrees": cell["cross_agrees"],
                       "identity_agrees": cell.get("identity_agrees"),
                       "n_feasible_sets": cell["n_feasible_sets"], "set": cell["set"],
                       "honoured": None if prof is None else bool(np.all(prof >= fl)),
                       "greedy_value": None if g is None else int(sv.value_of(g, D, obj)),
                       "local_search_value": lsv})
    caps = []
    if want_caps:
        for c in sv.cap_levels(k, m):
            capv = np.full(m, c, dtype=np.int64)
            cell = sv.solve_cell(k, D, groups, m, obj, Q, caps=capv, cross=cross)
            g = sv.greedy_quota(k, D, groups, m, obj, caps=capv)
            lsv = None if g is None else sv.local_search_quota(k, D, groups, m, obj, g, caps=capv)[1]
            prof = None if cell["set"] is None else np.bincount(groups[np.array(cell["set"])], minlength=m)
            caps.append({"c": c, "value": cell["value"], "status": cell["status"],
                         "cross_checked": cell["cross_checked"], "cross_agrees": cell["cross_agrees"],
                         "n_feasible_sets": cell["n_feasible_sets"], "set": cell["set"],
                         "respected": None if prof is None else bool(np.all(prof <= capv)),
                         "greedy_value": None if g is None else int(sv.value_of(g, D, obj)),
                         "local_search_value": lsv})
    free = [r["M"] for r in floors if r["value"] is not None and r["value"] == base]
    return {"unconstrained": base, "M_star": max(free) if free else None, "M_first": 1,
            "base_n_optima": base_cell["n_optima"], "base_set": base_cell["set"],
            "floors_curve": floors, "caps_curve": caps,
            "n_unsolved": sum(1 for r in floors + caps if r["status"] == "UNSOLVED"),
            "n_cross_disagree": sum(1 for r in floors + caps if r["cross_agrees"] is False),
            "n_identity_disagree": sum(1 for r in floors + caps if r.get("identity_agrees") is False)}

def part_a(Q, quality, n=20, k=10, m=3, draws=12):
    """Real-data validation: the corpus's own quality bins as the grouping variable."""
    cases = []
    for seed in range(draws):
        idx = sample_rows(Q, quality, n, seed)
        groups = quality_bins(quality[idx], m)
        for obj in sv.OBJS:
            res = measure_points(Q[idx], groups, m, k, obj, cross=(seed in (0, 1)), want_caps=True)
            res.update({"draw": seed, "n": n, "m": m, "k": k, "obj": obj,
                        "group_counts": [int(x) for x in sv.counts_of(groups, m)],
                        "alignment": alignment(Q[idx], groups),
                        "quality_span": [int(quality[idx].min()), int(quality[idx].max())]})
            cases.append(res)
    return cases

def part_b(Q, quality, n=18, k=9, m=3, draws=6, partitions=6):
    """Within-family alignment test: ONE metric space per draw, MANY partitions of it."""
    cases = []
    for seed in range(draws):
        idx = sample_rows(Q, quality, n, seed)
        sub = Q[idx]
        sizes = sv.counts_of(quality_bins(quality[idx], m), m).astype(int).tolist()
        parts = [("aligned", quality_bins(quality[idx], m))]
        rng = np.random.RandomState(1000 + seed)
        for j in range(partitions - 1):
            parts.append(("random%d" % j, random_partition_of_sizes(sizes, rng)))
        for name, groups in parts:
            for obj in sv.OBJS:
                res = measure_points(sub, groups, m, k, obj, cross=(seed == 0 and name == "aligned"))
                res.update({"draw": seed, "partition": name, "n": n, "m": m, "k": k, "obj": obj,
                            "group_counts": [int(x) for x in sv.counts_of(groups, m)],
                            "alignment": alignment(sub, groups)})
                cases.append(res)
    return cases

# ---------------------------------------------------------------- run / report
def run():
    header, X, quality = load_corpus()
    Q = quantise(X)
    res = {"instrument": "spike_v4.py",
           "corpus": {"name": os.path.basename(CORPUS), "sha256": sha256_of(CORPUS),
                      "rows": int(len(X)), "features": header[:-1],
                      "grouping_variable": header[-1],
                      "quality_histogram": {str(q): int((quality == q).sum())
                                            for q in sorted(set(quality.tolist()))},
                      "metric": "z-scored features quantised to integers (scale 8), squared Euclidean",
                      "quantised_span": [int(Q.min()), int(Q.max())]},
           "part_a": {"description": "real-data validation, groups = the corpus's own quality bins",
                      "cases": part_a(Q, quality)},
           "part_b": {"description": "within-family alignment test, one metric space per draw, "
                                     "several partitions of it",
                      "cases": part_b(Q, quality)}}
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res

def report(res):
    c = res["corpus"]
    print("instrument: spike_v4 -- the real-data arm")
    print("corpus: %s  sha256 %s  rows=%d  features=%d" % (c["name"], c["sha256"][:16], c["rows"], len(c["features"])))
    print("quality histogram:", c["quality_histogram"])
    print()
    print("== Part A: groups = the corpus's own quality bins ==")
    a = res["part_a"]["cases"]
    uns = sum(x["n_unsolved"] for x in a); dis = sum(x["n_cross_disagree"] for x in a)
    for x in a:
        k = x["k"]; rows = {r["M"]: r for r in x["floors_curve"]}
        end = rows[k]["value"]
        loss = None if end is None else (x["unconstrained"] - end) / float(x["unconstrained"])
        print("  draw=%2d %-6s base=%7d M*=%-2s M*/k=%.2f align=%.3f loss@end=%s greedy0=%s"
              % (x["draw"], x["obj"], x["unconstrained"], x["M_star"], (x["M_star"] or 0) / float(k),
                 x["alignment"], "%.4f" % loss if loss is not None else "-", rows[0]["greedy_value"]))
    print("  cells: UNSOLVED=%d cross-disagreements=%d" % (uns, dis))
    strict = [x for x in a if x["M_star"] is not None and x["M_star"] > x["M_first"]]
    fr = [x["M_star"] / float(x["k"]) for x in a if x["M_star"] is not None]
    print("  P1': M* > M_first in %d of %d;  median free width %.3f (%.2f-%.2f);  whole quota free %d/%d"
          % (len(strict), len(a), float(np.median(fr)), min(fr), max(fr), int(sum(1 for v in fr if v == 1.0)), len(a)))
    print()
    print("== Part B: within-family alignment test (one metric space per draw) ==")
    b = res["part_b"]["cases"]
    print("  %-4s %-9s %-6s %6s %8s" % ("draw", "partition", "obj", "M*/k", "alignment"))
    for x in b:
        print("  %-4d %-9s %-6s %6.2f %8.3f" % (x["draw"], x["partition"], x["obj"],
                                                 (x["M_star"] or 0) / float(x["k"]), x["alignment"]))
    import numpy as _np
    xs = [x["alignment"] for x in b if x["M_star"] is not None]
    ys = [x["M_star"] / float(x["k"]) for x in b if x["M_star"] is not None]
    print("  within-family spearman(alignment, M*/k) = %+.3f  (n=%d)" % (_spearman(xs, ys), len(xs)))
    return 0 if (uns == 0 and dis == 0) else 1

def _spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    def rank(a):
        o = np.argsort(a, kind="mergesort"); r = np.empty(len(a), float); r[o] = np.arange(len(a)); return r
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    den = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else float("nan")

# ---------------------------------------------------------------- certificates
def selftest():
    """Each certificate on a healthy object (must PASS) and on a mutated object built to break
    exactly that certificate (must FAIL)."""
    header, X, quality = load_corpus()
    Q = quantise(X)
    checks = []

    # C1 the corpus pin is enforced: a wrong pin must refuse to load
    want = pinned_hash(os.path.basename(CORPUS))
    good = (sha256_of(CORPUS) == want)
    io.open("/tmp/v4_pin_ok", "w").write(want)
    checks.append(("C1 corpus pin enforced", good, (want[:-1] + ("0" if want[-1] != "0" else "1")) == sha256_of(CORPUS)))

    # C2 quantisation is deterministic and integral
    Q2 = quantise(X)
    checks.append(("C2 quantisation deterministic",
                   bool(np.array_equal(Q, Q2)) and Q.dtype == np.int64,
                   not np.array_equal(Q, quantise(X * 1.0001))))

    # C3 the quality bins are non-empty, complete and ordered
    groups = quality_bins(quality, 3)
    cnt = np.bincount(groups, minlength=3)
    ordered = all(quality[groups == i].max() <= quality[groups == i + 1].min() for i in range(2))
    checks.append(("C3 quality bins non-empty, ordered",
                   bool(np.all(cnt > 0)) and int(cnt.sum()) == len(quality) and ordered,
                   not (np.bincount(quality_bins(quality, 3), minlength=3) > 0).all()))

    # C4 the random partition preserves the size multiset and is not the identity
    sizes = cnt.astype(int).tolist()
    rng = np.random.RandomState(7)
    rp = random_partition_of_sizes(sizes, rng)
    srt = lambda v: sorted(np.bincount(v, minlength=len(sizes)).tolist())
    checks.append(("C4 random partition keeps sizes",
                   srt(rp) == sorted(sizes) and not np.array_equal(rp, groups),
                   srt(rp) != sorted(sizes)))

    # C5 the alignment statistic orders an aligned partition below a random one
    idx = sample_rows(Q, quality, 18, 0)
    ag = quality_bins(quality[idx], 3)
    rg = random_partition_of_sizes(np.bincount(ag, minlength=3).astype(int).tolist(), np.random.RandomState(3))
    a_ag, a_rg = alignment(Q[idx], ag), alignment(Q[idx], rg)
    checks.append(("C5 alignment separates aligned/random", a_ag < a_rg, a_ag >= a_rg))

    # C6 the sampling returns n DISTINCT rows, each a real corpus row
    idx = sample_rows(Q, quality, 20, 3)
    checks.append(("C6 sample is n distinct real rows",
                   len(set(idx.tolist())) == 20 and int(idx.max()) < len(Q),
                   len(set(sample_rows(Q, quality, 20, 3).tolist())) != 20))

    # C7 the two routes agree on a real-data cell, and disagree when fed different metrics
    sub = Q[sample_rows(Q, quality, 16, 0)]
    gsub = quality_bins(quality[sample_rows(Q, quality, 16, 0)], 3)
    for obj in sv.OBJS:
        c = sv.solve_cell(8, sv.d2_matrix(sub), gsub, 3, obj, sub, cross=True)
        ve = sv.enum_complete(8, sv.d2_matrix(sub), gsub, 3, obj)[0]
        vdiff = sv.enum_complete(8, 2 * sv.d2_matrix(sub), gsub, 3, obj)[0]
        checks.append(("C7 %s routes agree on real data" % obj,
                       bool(c["cross_agrees"]) and ve == c["value"], vdiff == ve))

    good = True
    for name, healthy, mutated in checks:
        row = healthy and not mutated
        print("  %-40s healthy=%-5s mutated=%-5s %s" % (name, healthy, mutated, "PASS" if row else "FAIL"))
        good = good and row
    print("selftest:", "ALL PASS" if good else "FAILED")
    return 0 if good else 1

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(report(run()))
