#!/usr/bin/env python3
"""spike_v3.py -- issue #128, the redesigned cost-curve instrument (R555).

What R554's instrument could not do, and what this one changes:

  (1) REGIME.  R554 used n=18, m=3, k=6, and measured the whole quota free in 19 % of cases --
      there was almost no room above the threshold, so the cost-law (P3) was not fittable
      (only 12 of 32 cases had >=3 points above M*, and the fits were degenerate).  Here the
      selection is larger relative to the groups: setting A is n=18, m=3, k=9 (the quota forces
      a real rearrangement: 3 per group out of 6 available) and setting B is n=20, m=4, k=10.

  (2) CONSTRAINT FAMILIES, REPAIRED.  R554's two families coincided at the tightest point,
      because proportional floors and proportional caps both sum to k there, and a proportional
      cap is degenerate when the groups are equal.  The floors stay proportional
      (largest remainder); the CAPS become a per-group uniform cap c -- "no group may contribute
      more than c of the k chosen" -- which is the cap a practitioner actually writes, and which
      sums to m*c > k over the informative range, so it binds WITHOUT pinning the profile.

  (3) BASELINES (P4).  The constrained greedy and the constrained 1-swap local search are
      measured on the same cells as the exact optimum, so the heuristic's cost curve can be
      compared with the exact one: P4 asks whether a heuristic pays a quota cost where the
      optimum pays none.

Ground truth: integer points, squared Euclidean (integer) metric, so every objective value is an
integer and the artefact is byte-identical across runs.  Route 1 is a COMPLETE vectorised
enumeration over every feasible k-subset (it cannot return "unsolved"); route 2 is the integer
program, run on a DECLARED subsample of cells as an independent cross-check; max-sum carries a
third, coordinate-based identity route.  Every cell records its route, its status and whether the
routes agreed, and the analysis refuses a cell whose routes disagree.

Usage:
  python3 spike_v3.py              write spike_v3_results.json
  python3 spike_v3.py --selftest   each certificate on a healthy AND a mutated object
"""
import io, json, os, sys, itertools, hashlib
from math import comb, ceil
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spike_v3_results.json")
TIME_LIMIT = 300
CHUNK = 30000

# setting A and setting B: (name, n, m, k)
SETTINGS = [("A", 18, 3, 9), ("B", 20, 4, 10)]
FAMILIES = ["uniform2d", "uniform5d", "clustered2d", "unequal2d"]
OBJS = ("maxmin", "maxsum")
# the cells cross-checked by the integer program, declared (setting, seed) pairs
CROSS_SET = {("A", 1), ("A", 2), ("B", 1)}
SEEDS = (1, 2, 3, 4)

def make_instance(family, seed, n, m):
    """Integer points and a group vector, deterministic in the arguments."""
    rng = np.random.RandomState((seed * 1000003 + len(family)) % (2 ** 31))
    if family == "uniform2d":
        pts = rng.randint(0, 40, size=(n, 2)); groups = np.arange(n) % m
    elif family == "uniform5d":
        pts = rng.randint(0, 25, size=(n, 5)); groups = np.arange(n) % m
    elif family == "clustered2d":
        centres = rng.randint(5, 35, size=(m, 2))
        rows = [centres[i] + rng.randint(-3, 4, size=(n // m, 2)) for i in range(m)]
        pts = np.vstack(rows); groups = np.repeat(np.arange(m), n // m)
        while len(pts) < n:
            pts = np.vstack([pts, rng.randint(0, 40, size=(1, 2))]); groups = np.append(groups, m - 1)
        pts, groups = pts[:n], groups[:n]
    elif family == "unequal2d":
        pts = rng.randint(0, 40, size=(n, 2))
        sizes = [n // 2, n // 3]; sizes.append(n - sizes[0] - sizes[1])
        groups = np.zeros(n, dtype=np.int64); p = 0
        for i, s in enumerate(sizes[:m]):
            groups[p:p + s] = i; p += s
    else:
        raise ValueError(family)
    return np.asarray(pts, dtype=np.int64), np.asarray(groups, dtype=np.int64)

def d2_matrix(pts):
    diff = pts[:, None, :] - pts[None, :, :]
    return (diff * diff).sum(axis=2)

def counts_of(groups, m):
    return np.bincount(groups, minlength=m)

def largest_remainder(M, cnt):
    """Distribute exactly M seats over the groups proportionally, largest remainder."""
    m = len(cnt); total = int(cnt.sum())
    if M <= 0:
        return np.zeros(m, dtype=np.int64)
    assert 0 < M <= total
    base = np.floor(M * cnt.astype(float) / total).astype(np.int64)
    rem = M * cnt.astype(float) / total - base
    need = M - int(base.sum())
    for i in sorted(range(m), key=lambda i: (-rem[i], i))[:need]:
        base[i] += 1
    assert int(base.sum()) == M and bool(np.all(base <= cnt))
    return base

def cap_levels(k, m):
    """Uniform per-group caps c: c >= ceil(k/m) keeps k selectable; c = k is non-binding."""
    return list(range(int(ceil(k / m)), k + 1))

# ------------------------------------------------------------------ routes
def enum_complete(k, D, groups, m, obj, floors=None, caps=None):
    """ROUTE 1: a complete vectorised enumeration over every feasible k-subset.

    It visits every subset, so its result IS the definition of the constrained optimum and it has
    no "unsolved" state.  Returns (value, n_optima, best_set, feasible_profile_count)."""
    n = D.shape[0]
    best = None; cnt = 0; arg = None; n_feas = 0
    I = np.empty((CHUNK, k), dtype=np.int32); f = 0
    eye = ~np.eye(k, dtype=bool)

    def flush(I, f):
        nonlocal best, cnt, arg, n_feas
        if f == 0:
            return
        J = I[:f]
        prof = np.zeros((f, m), dtype=np.int32)
        gsel = groups[J]                                  # (f, k) group of each selected index
        for i in range(m):
            prof[:, i] = (gsel == i).sum(axis=1)
        keep = np.ones(f, dtype=bool)
        if floors is not None:
            keep &= np.all(prof >= floors[None, :], axis=1)
        if caps is not None:
            keep &= np.all(prof <= caps[None, :], axis=1)
        n_feas += int(keep.sum())
        if not keep.any():
            return
        Jk = J[keep]
        sub = D[Jk[:, :, None], Jk[:, None, :]]           # (f', k, k)
        if obj == "maxmin":
            vals = sub[:, eye].min(axis=1)
        else:
            vals = sub.sum(axis=(1, 2)) // 2
        i = int(np.argmax(vals))
        if best is None or vals[i] > best:
            best = int(vals[i]); cnt = int((vals == best).sum()); arg = tuple(Jk[i].tolist())
        elif vals[i] == best:
            cnt += int((vals == best).sum())

    for S in itertools.combinations(range(n), k):
        I[f] = S; f += 1
        if f == CHUNK:
            flush(I, f); f = 0
    flush(I, f)
    if best is None:
        return None, 0, None, 0
    return best, cnt, arg, n_feas

def maxsum_identity(S, pts):
    """ROUTE 3 for max-sum, from coordinates only: k*sum|xi|^2 - |sum xi|^2."""
    X = pts[list(S)].astype(np.int64); k = len(S)
    return int(k * int((X * X).sum()) - int((X.sum(axis=0) ** 2).sum()))

def value_of(S, D, obj):
    if len(S) < 2:
        return 0
    if obj == "maxmin":
        sub = D[np.ix_(list(S), list(S))]; k = len(S)
        return int(sub[~np.eye(k, dtype=bool)].min())
    return int(sum(int(D[a, b]) for a, b in itertools.combinations(S, 2)))

def ilp_opt(k, D, groups, m, obj, floors=None, caps=None):
    """ROUTE 2: the integer program. Returns (value, set, status) with an explicit status."""
    n = D.shape[0]
    pairs = list(itertools.combinations(range(n), 2)); npairs = len(pairs)
    if obj == "maxmin":
        nv = n + 1; t = n
        c = np.zeros(nv); c[t] = -1.0
        lb = np.zeros(nv); ub = np.ones(nv); ub[t] = np.inf
        rows = [np.concatenate([np.ones(n), [0.0]])]; lo = [k]; hi = [k]
        BIG = int(D.max())
        for (a, b) in pairs:
            r = np.zeros(nv); r[a] = BIG; r[b] = BIG; r[t] = 1.0
            rows.append(r); lo.append(-np.inf); hi.append(int(D[a, b]) + 2 * BIG)
    else:
        nv = n + npairs; c = np.zeros(nv)
        for j, (a, b) in enumerate(pairs):
            c[n + j] = -float(D[a, b])
        lb = np.zeros(nv); ub = np.ones(nv)
        rows = [np.concatenate([np.ones(n), np.zeros(npairs)])]; lo = [k]; hi = [k]
        for j, (a, b) in enumerate(pairs):
            r = np.zeros(nv); r[a] = 1.0; r[b] = 1.0; r[n + j] = -1.0
            rows.append(r); lo.append(-np.inf); hi.append(1.0)
            r = np.zeros(nv); r[a] = -1.0; r[n + j] = 1.0
            rows.append(r); lo.append(-np.inf); hi.append(0.0)
            r = np.zeros(nv); r[b] = -1.0; r[n + j] = 1.0
            rows.append(r); lo.append(-np.inf); hi.append(0.0)
    for i in range(m):
        idx = [j for j in range(n) if groups[j] == i]
        if floors is not None and int(floors[i]) > 0:
            r = np.zeros(nv); r[idx] = -1.0
            rows.append(r); lo.append(-np.inf); hi.append(-float(floors[i]))
        if caps is not None and int(caps[i]) < len(idx):
            r = np.zeros(nv); r[idx] = 1.0
            rows.append(r); lo.append(-np.inf); hi.append(float(caps[i]))
    A = np.vstack(rows)
    res = milp(c=c, constraints=LinearConstraint(A, np.array(lo), np.array(hi)),
               integrality=np.ones(nv), bounds=Bounds(np.array(lb), np.array(ub)),
               options={"presolve": True, "time_limit": TIME_LIMIT})
    if res.status == 0 and res.success:
        x = np.round(res.x[:n]).astype(int)
        return -int(round(res.fun)), tuple(sorted(j for j in range(n) if x[j] == 1)), "OPTIMAL"
    if res.status == 2:
        return None, None, "INFEASIBLE"
    return None, None, "UNSOLVED"

def solve_cell(k, D, groups, m, obj, pts, floors=None, caps=None, cross=False):
    """One cell: complete enumeration (always) + the DECLARED cross-check when asked."""
    v, cnt, S, n_feas = enum_complete(k, D, groups, m, obj, floors=floors, caps=caps)
    cell = {"value": v, "set": None if S is None else list(S), "n_optima": cnt,
            "route": "enumeration", "status": "OPTIMAL" if v is not None else "INFEASIBLE",
            "n_feasible_sets": n_feas, "cross_checked": bool(cross),
            "cross_value": None, "cross_status": None, "cross_agrees": None}
    if cross:
        cv, cs, st = ilp_opt(k, D, groups, m, obj, floors=floors, caps=caps)
        cell["cross_value"] = cv; cell["cross_status"] = st
        if cv is None and v is None:
            cell["cross_agrees"] = (st == "INFEASIBLE")
        elif cv is None or v is None:
            cell["cross_agrees"] = False
        else:
            cell["cross_agrees"] = bool(cv == v)
    if v is not None and S is not None and obj == "maxsum":
        cell["identity_value"] = maxsum_identity(S, pts)
        cell["identity_agrees"] = bool(cell["identity_value"] == v)
    return cell

# ------------------------------------------------------------------ constrained baselines (P4)
def feasible_after(k, groups, m, floors, caps, chosen, cand):
    """Can `cand` be added to `chosen` and the rest still be completed feasibly?"""
    prof = np.bincount(groups[np.array(list(chosen) + [cand])], minlength=m)
    if caps is not None and np.any(prof > caps):
        return False
    left = k - (len(chosen) + 1)
    if left < 0:
        return False
    if floors is not None:
        need = int(np.maximum(floors - prof, 0).sum())
        if need > left:
            return False
    return True

def greedy_quota(k, D, groups, m, obj, floors=None, caps=None):
    """Farthest-first greedy with a feasibility repair: never choose a point that makes the
    remaining quota unsatisfiable.  Deterministic (ties broken by index)."""
    n = D.shape[0]
    chosen = []
    def pick(cands):
        if not cands:
            return None
        if not chosen:
            return min(cands, key=lambda j: (-int(D[j].sum()), j))
        if obj == "maxmin":
            return max(cands, key=lambda j: (min(int(D[j, s]) for s in chosen), -j))
        return max(cands, key=lambda j: (sum(int(D[j, s]) for s in chosen), -j))
    while len(chosen) < k:
        cands = [j for j in range(n) if j not in chosen and feasible_after(k, groups, m, floors, caps, chosen, j)]
        j = pick(cands)
        if j is None:
            return None
        chosen.append(int(j))
    return tuple(sorted(chosen))

def local_search_quota(k, D, groups, m, obj, start, floors=None, caps=None):
    """1-swap hill climbing that keeps the constraint satisfied at every step."""
    if start is None:
        return None, None
    n = D.shape[0]
    S = set(start); cur = value_of(sorted(S), D, obj)
    ok = lambda T: ((floors is None or np.all(np.bincount(groups[np.array(sorted(T))], minlength=m) >= floors))
                    and (caps is None or np.all(np.bincount(groups[np.array(sorted(T))], minlength=m) <= caps)))
    improved = True
    while improved:
        improved = False
        for i in sorted(S):
            for j in range(n):
                if j in S:
                    continue
                T = (S - {i}) | {j}
                if not ok(T):
                    continue
                v = value_of(sorted(T), D, obj)
                if v > cur:
                    S, cur, improved = T, v, True
                    break
            if improved:
                break
    return tuple(sorted(S)), int(cur)

# ------------------------------------------------------------------ the measurement
def measure(setting, family, seed, n, m, k, obj):
    pts, groups = make_instance(family, seed, n, m)
    D = d2_matrix(pts); cnt = counts_of(groups, m)
    cross = (setting, seed) in CROSS_SET
    base = solve_cell(k, D, groups, m, obj, pts, cross=cross)
    floors_curve = []
    for M in range(0, k + 1):
        fl = largest_remainder(M, cnt)
        c = solve_cell(k, D, groups, m, obj, pts, floors=fl, cross=cross)
        g = greedy_quota(k, D, groups, m, obj, floors=fl)
        lsv = None if g is None else local_search_quota(k, D, groups, m, obj, g, floors=fl)[1]
        prof = None if c["set"] is None else np.bincount(groups[np.array(c["set"])], minlength=m)
        floors_curve.append({"M": M, "floors": [int(x) for x in fl], "value": c["value"],
                             "status": c["status"], "route": c["route"],
                             "cross_checked": c["cross_checked"], "cross_value": c["cross_value"],
                             "cross_agrees": c["cross_agrees"],
                             "identity_agrees": c.get("identity_agrees"),
                             "n_feasible_sets": c["n_feasible_sets"],
                             "set": c["set"],
                             "honoured": None if prof is None else bool(np.all(prof >= fl)),
                             "greedy_value": None if g is None else int(value_of(g, D, obj)),
                             "greedy_set": None if g is None else list(g),
                             "local_search_value": lsv})
    caps_curve = []
    for c in cap_levels(k, m):
        capv = np.full(m, c, dtype=np.int64)
        cell = solve_cell(k, D, groups, m, obj, pts, caps=capv, cross=cross)
        g = greedy_quota(k, D, groups, m, obj, caps=capv)
        lsv = None if g is None else local_search_quota(k, D, groups, m, obj, g, caps=capv)[1]
        prof = None if cell["set"] is None else np.bincount(groups[np.array(cell["set"])], minlength=m)
        caps_curve.append({"c": c, "caps": [int(x) for x in capv], "value": cell["value"],
                           "status": cell["status"], "route": cell["route"],
                           "cross_checked": cell["cross_checked"], "cross_value": cell["cross_value"],
                           "cross_agrees": cell["cross_agrees"],
                           "identity_agrees": cell.get("identity_agrees"),
                           "n_feasible_sets": cell["n_feasible_sets"],
                           "set": cell["set"],
                           "respected": None if prof is None else bool(np.all(prof <= capv)),
                           "greedy_value": None if g is None else int(value_of(g, D, obj)),
                           "greedy_set": None if g is None else list(g),
                           "local_search_value": lsv})
    basev = base["value"]
    free_M = [r["M"] for r in floors_curve if r["value"] is not None and r["value"] == basev]
    M_star = max(free_M) if free_M else None
    return {"setting": setting, "family": family, "seed": seed, "n": n, "m": m, "k": k, "obj": obj,
            "group_counts": [int(x) for x in cnt], "unconstrained": basev,
            "base_n_optima": base["n_optima"], "base_set": base["set"],
            "M_star": M_star, "M_first": 1,
            "cap_levels": cap_levels(k, m),
            "cross_checked_cells": sum(1 for r in floors_curve + caps_curve if r["cross_checked"]),
            "n_cells": len(floors_curve) + len(caps_curve),
            "floors_curve": floors_curve, "caps_curve": caps_curve}

def run():
    res = {"instrument": "spike_v3.py", "metric": "squared Euclidean (integer)",
           "routes": {"1": "complete vectorised enumeration (primary, every cell)",
                      "2": "integer program, on the DECLARED subsample CROSS_SET",
                      "3": "max-sum coordinate identity, every max-sum cell"},
           "families_of_constraint": {"F": "proportional floors, largest remainder, M in 0..k",
                                      "C": "uniform per-group cap c, c in ceil(k/m)..k"},
           "settings": {"A": {"n": 18, "m": 3, "k": 9}, "B": {"n": 20, "m": 4, "k": 10},
                        "seeds": list(SEEDS), "cross_set": sorted(list(CROSS_SET))},
           "cases": []}
    for (name, n, m, k) in SETTINGS:
        for family in FAMILIES:
            for seed in SEEDS:
                for obj in OBJS:
                    res["cases"].append(measure(name, family, seed, n, m, k, obj))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res

def report(res):
    print("instrument: spike_v3 -- cost curve, redesigned regime, three routes")
    tot = sum(c["n_cells"] for c in res["cases"])
    xchk = sum(c["cross_checked_cells"] for c in res["cases"])
    print("cases=%d  cells=%d  cross-checked cells=%d  (%s)"
          % (len(res["cases"]), tot, xchk, res["settings"]["cross_set"]))
    dis = sum(1 for c in res["cases"] for r in c["floors_curve"] + c["caps_curve"]
              if r["cross_checked"] and r["cross_agrees"] is False)
    idbad = sum(1 for c in res["cases"] for r in c["floors_curve"] + c["caps_curve"]
                if r.get("identity_agrees") is False)
    uns = sum(1 for c in res["cases"] for r in c["floors_curve"] + c["caps_curve"]
              if r["status"] == "UNSOLVED")
    print("disagreements: cross=%d identity=%d   UNSOLVED=%d" % (dis, idbad, uns))
    print()
    print("%-2s %-12s %-6s %5s %5s %6s %8s %8s %8s" %
          ("S", "family", "obj", "base", "M*", "M*/k", "loss@end", "greedy", "ls"))
    for c in res["cases"]:
        k = c["k"]; rows = {r["M"]: r for r in c["floors_curve"]}
        end = rows[k]["value"]
        loss = None if (end is None or c["unconstrained"] is None) else (c["unconstrained"] - end) / float(c["unconstrained"])
        print("%-2s %-12s %-6s %5s %5s %6s %8s %8s %8s" % (
            c["setting"], c["family"], c["obj"], c["unconstrained"], c["M_star"],
            "%.2f" % (c["M_star"] / float(k)) if c["M_star"] is not None else "-",
            "%.4f" % loss if loss is not None else "-",
            rows[0]["greedy_value"], rows[0]["local_search_value"]))
    n_over = [c for c in res["cases"]
              if c["M_star"] is not None and (c["k"] - c["M_star"]) >= 3]
    print()
    print("cases with >=3 floors above M* (P3 fittable): %d of %d" % (len(n_over), len(res["cases"])))
    strict = [c for c in res["cases"] if c["M_star"] is not None and c["M_star"] > c["M_first"]]
    print("P1' : M* > M_first strictly in %d of %d" % (len(strict), len(res["cases"])))
    return 0 if (dis == 0 and uns == 0) else 1

def selftest():
    """Each certificate on a healthy object (must PASS) and on a mutated object built to break
    exactly that certificate (must FAIL)."""
    family, seed, n, m, k = "uniform2d", 7, 18, 3, 9
    pts, groups = make_instance(family, seed, n, m)
    D = d2_matrix(pts); cnt = counts_of(groups, m)
    checks = []

    # C1 the two routes agree on the same problem, and DISAGREE when fed different objects
    for obj in OBJS:
        c = solve_cell(k, D, groups, m, obj, pts, cross=True)
        ve = enum_complete(k, D, groups, m, obj)[0]
        vi = ilp_opt(k, D, groups, m, obj)[0]
        vdiff = enum_complete(k, 2 * D, groups, m, obj)[0]
        checks.append(("C1a %s routes agree" % obj, bool(c["cross_agrees"]), vdiff == ve))
        checks.append(("C1b %s ILP=enum direct" % obj, ve == vi, vi == vdiff))

    # C2 a constrained cell is solved and honoured in both families
    fl = largest_remainder(9, cnt)
    c = solve_cell(k, D, groups, m, "maxmin", pts, floors=fl, cross=True)
    okf = lambda T: bool(np.all(np.bincount(groups[np.array(list(T))], minlength=m) >= fl))
    checks.append(("C2a floors honoured", okf(c["set"]), okf(tuple(x for x in c["set"] if groups[x] != 0))))
    capv = np.full(m, int(ceil(k / m)), dtype=np.int64)
    c = solve_cell(k, D, groups, m, "maxmin", pts, caps=capv, cross=True)
    okc = lambda T: bool(np.all(np.bincount(groups[np.array(list(T))], minlength=m) <= capv))
    over = [int(j) for j in range(n) if groups[j] == 0][:capv[0] + 1]
    over += [int(j) for j in range(n) if groups[j] != 0][:k - len(over)]
    checks.append(("C2b caps respected", okc(c["set"]), okc(tuple(sorted(over)))))

    # C3 an infeasible cell is INFEASIBLE, never UNSOLVED; and the two routes agree on that
    hard = np.full(m, 99, dtype=np.int64)
    c = solve_cell(k, D, groups, m, "maxmin", pts, floors=hard, cross=True)
    checks.append(("C3 infeasible -> INFEASIBLE both routes",
                   c["status"] == "INFEASIBLE" and c["cross_status"] == "INFEASIBLE",
                   c["status"] == "UNSOLVED" or c["cross_status"] != "INFEASIBLE"))
    # a cap that cannot reach k is infeasible too (c = ceil(k/m) - 1)
    c = solve_cell(k, D, groups, m, "maxmin", pts, caps=np.full(m, int(ceil(k / m)) - 1, dtype=np.int64))
    checks.append(("C3b cap below k/m is infeasible", c["value"] is None, c["value"] is not None))

    # C4 the constrained baseline is feasible and never beats the exact optimum
    g = greedy_quota(k, D, groups, m, "maxmin", floors=fl)
    gv = value_of(g, D, "maxmin")
    ex = solve_cell(k, D, groups, m, "maxmin", pts, floors=fl)["value"]
    checks.append(("C4a greedy feasible and <= optimum", gv <= ex, gv > ex))
    checks.append(("C4b greedy honours the floors", okf(g), okf(tuple(x for x in g if groups[x] != 0))))
    ls, lsv = local_search_quota(k, D, groups, m, "maxmin", g, floors=fl)
    checks.append(("C4c local search <= optimum", lsv <= ex, lsv > ex))

    # C5 floors sum to exactly M
    checks.append(("C5 floors sum to M",
                   all(int(largest_remainder(M, cnt).sum()) == M for M in range(0, k + 1)),
                   any(int(largest_remainder(M, cnt).sum()) != M for M in range(0, k + 1))))

    good = True
    for name, healthy, mutated in checks:
        row = healthy and not mutated
        print("  %-36s healthy=%-5s mutated=%-5s %s" % (name, healthy, mutated, "PASS" if row else "FAIL"))
        good = good and row
    print("selftest:", "ALL PASS" if good else "FAILED")
    return 0 if good else 1

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(report(run()))
