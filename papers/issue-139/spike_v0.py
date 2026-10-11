#!/usr/bin/env python3
"""spike_v0.py -- issue #139 (R613): the exact obligation-search frontier and its
zero-coupling closed-form anchor.

Model (declared; ground truth by construction)
----------------------------------------------
An obligation set is a DAG G = (V, E) over n obligations.  Obligation j carries a
standalone difficulty p_j in (0,1]: the probability that ONE attempt discharges
it while none of its parents is discharged.  One attempt costs one budget unit.
An attempt either discharges the obligation or fails; failures are independent
and leave the obligation open.

Coupling: if at least one parent of j has been discharged, j's success
probability is boosted: p_j -> min(1, p_j + c).  c = 0 is the uncoupled control.

A schedule is any deterministic map pol : S -> j (S = the discharged set, j not
in S).  The frontier is F(B) = E[number discharged after B attempts] under pol.

Everything here is an EXACT expectation: V(S,b) is backward induction over the
2^n discharged sets and the budget, so each reported number is computed, not
estimated.  Two independent readings check it: a geometric-convolution closed
form (the ground-truth anchor on an uncoupled set, where the process is a sum of
independent geometric searches) and a seeded Monte-Carlo simulation.
"""
import argparse
import json
import random
import sys

# ---------------------------------------------------------------- model helpers

def children_of(n, parents):
    ch = [[] for _ in range(n)]
    for j in range(n):
        for i in parents[j]:
            ch[i].append(j)
    return ch

def descendants(n, parents):
    """Number of distinct descendants of each node (the dependent cone)."""
    ch = children_of(n, parents)
    out = [0] * n
    for j in range(n):
        seen, stack = set(), list(ch[j])
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(ch[x])
        out[j] = len(seen)
    return out

def build(n, p, edges, c):
    """edges: (parent, child) pairs -> j depends on i."""
    assert len(p) == n and all(0.0 < x <= 1.0 for x in p), "p must be in (0,1]"
    parents = [[] for _ in range(n)]
    for (i, j) in edges:
        assert 0 <= i < n and 0 <= j < n and i != j
        parents[j].append(i)
    # acyclicity (needed: descendants() would loop forever otherwise)
    order, indeg = [], [len(parents[j]) for j in range(n)]
    ch = children_of(n, parents)
    q = [j for j in range(n) if indeg[j] == 0]
    while q:
        x = q.pop()
        order.append(x)
        for y in ch[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    assert len(order) == n, "edges must form a DAG"
    return parents, c

def eff_probs(n, p, parents, c):
    """Return a callable S -> list of effective success probabilities."""
    def f(S):
        out = [0.0] * n
        for j in range(n):
            boosted = parents[j] and any((S >> i) & 1 for i in parents[j])
            out[j] = min(1.0, p[j] + (c if boosted else 0.0))
        return out
    return f

# ------------------------------------------------------------------- schedules

def make_policy(kind, n, p, parents, c, rng=None):
    eff = eff_probs(n, p, parents, c)
    kind = {"greedy": "easiest_first"}.get(kind, kind)   # "greedy" = max current
    if kind == "easiest_first":
        def pol(S):
            e = eff(S)
            best = None
            for j in range(n):
                if (S >> j) & 1:
                    continue
                if best is None or e[j] > e[best]:
                    best = j
            return best
    elif kind == "assumptions_first":
        d = descendants(n, parents)
        def pol(S):
            e = eff(S)
            best = None
            for j in range(n):
                if (S >> j) & 1:
                    continue
                if best is None or (d[j], e[j]) > (d[best], e[best]):
                    best = j
            return best
    elif kind == "fixed_order":
        def pol(S):
            for j in range(n):
                if not ((S >> j) & 1):
                    return j
    elif kind == "placebo":
        order = list(range(n))
        rng.shuffle(order)
        def pol(S):
            for j in order:
                if not ((S >> j) & 1):
                    return j
    else:
        raise ValueError("unknown policy: %s" % kind)
    return pol, eff

# ----------------------------------------------------- exact frontier (the DP)

def frontier_exact(n, p, parents, c, pol, eff, Bmax):
    """Exact F(B) = E[discharged after B attempts], B = 0..Bmax.

    V[S][b] = expected ADDITIONAL discharges from discharged-set S with b
    attempts left, under the Markovian schedule pol.
    """
    full = 1 << n
    V = [[0.0] * (Bmax + 1) for _ in range(full)]
    for b in range(1, Bmax + 1):
        for S in range(full):
            if S == full - 1:
                V[S][b] = 0.0           # nothing left to discharge
                continue
            a = pol(S)
            q = eff(S)[a]
            V[S][b] = q * (1.0 + V[S | (1 << a)][b - 1]) + (1.0 - q) * V[S][b - 1]
    return [V[0][b] for b in range(Bmax + 1)]

# ------------------------------------------- closed-form anchor (uncoupled set)

def anchor_geometric(p_order, Bmax):
    """E[count(B)] for an UNCOUPLED set attempted in the fixed order p_order.

    The attempts needed for obligation k are geometric(p_k); the number of
    obligations completed within B attempts is max{k : sum_{i<=k} G_i <= B}.
    E[count(B)] = sum_{k>=1} P(sum_{i<=k} G_i <= B), computed by convolution.
    """
    n = len(p_order)
    D = [[0.0] * (Bmax + 1) for _ in range(n + 1)]
    D[0][0] = 1.0
    for k in range(1, n + 1):
        pk = p_order[k - 1]
        q = 1.0 - pk
        for s in range(Bmax + 1):
            ds = D[k - 1][s]
            if ds == 0.0:
                continue
            fail = 1.0
            for m in range(1, Bmax - s + 1):
                D[k][s + m] += ds * fail * pk
                fail *= q
    E = [0.0] * (Bmax + 1)
    for k in range(1, n + 1):
        acc = 0.0
        for t in range(Bmax + 1):
            acc += D[k][t]
            E[t] += acc
    return E

def mc_frontier(n, p, parents, c, pol, eff, Bmax, trials, seed):
    rng = random.Random(seed)
    full = 1 << n
    acc = [0.0] * (Bmax + 1)
    for _ in range(trials):
        S, cnt = 0, 0
        for b in range(1, Bmax + 1):
            if S == full - 1:
                acc[b] += cnt
                continue
            a = pol(S)
            if rng.random() < eff(S)[a]:
                S |= (1 << a)
                cnt += 1
            acc[b] += cnt
    return [x / trials for x in acc]


# ---------------------------------------------------------- Monte Carlo check

def mc_stats(n, p, parents, c, pol, eff, Bmax, trials, seed):
    rng = random.Random(seed)
    full = 1 << n
    sums = [0.0] * (Bmax + 1)
    sqs = [0.0] * (Bmax + 1)
    for _ in range(trials):
        S, cnt = 0, 0
        for b in range(1, Bmax + 1):
            if S != full - 1:
                a = pol(S)
                if rng.random() < eff(S)[a]:
                    S |= (1 << a)
                    cnt += 1
            sums[b] += cnt
            sqs[b] += cnt * cnt
    mean = [s / trials for s in sums]
    var = [max(0.0, sqs[b] / trials - mean[b] ** 2) for b in range(Bmax + 1)]
    return mean, [v ** 0.5 for v in var]

# ------------------------------------------------------------------- the cases

SCHEDULES = ("greedy", "assumptions_first", "fixed_order", "placebo")

CASES = [
    {"name": "chain_uniform", "n": 4, "p": [0.2, 0.2, 0.2, 0.2],
     "edges": [(0, 1), (1, 2), (2, 3)], "c": 0.35},
    {"name": "star_hard_root", "n": 4, "p": [0.15, 0.6, 0.6, 0.6],
     "edges": [(0, 1), (0, 2), (0, 3)], "c": 0.35},
]

BUDGETS = (4, 8, 12, 16, 20, 30, 60)

def run_case(case, Bmax, seed=139):
    """For every schedule: its frontier on the COUPLED DAG and on the UNCOUPLED
    control (same difficulties, no edges).  The coupling gain is the difference
    at a FIXED schedule; the ordering effect is the difference at a FIXED graph.
    Only the first can be attributed to the coupling."""
    n, p, edges, c = case["n"], list(case["p"]), case["edges"], case["c"]
    parC, cC = build(n, p, edges, c)
    parU, cU = build(n, p, [], c)

    def F(par, cc, kind):
        pol, eff = make_policy(kind, n, p, par, cc, rng=random.Random(seed))
        return frontier_exact(n, p, par, cc, pol, eff, Bmax)

    fc = {k: F(parC, cC, k) for k in SCHEDULES}
    fu = {k: F(parU, cU, k) for k in SCHEDULES}
    cells = []
    for B in BUDGETS:
        B = min(B, Bmax)
        cells.append({
            "B": B,
            "coupled": {k: fc[k][B] for k in SCHEDULES},
            "uncoupled": {k: fu[k][B] for k in SCHEDULES},
            "coupling_gain": {k: fc[k][B] - fu[k][B] for k in SCHEDULES},
            "ordering_effect_coupled": {k: fc[k][B] - fc["greedy"][B] for k in SCHEDULES},
            "ordering_effect_uncoupled": {k: fu[k][B] - fu["greedy"][B] for k in SCHEDULES},
        })
    return {"name": case["name"], "n": n, "p": p, "edges": edges, "c": c, "cells": cells}

# ------------------------------------------------------------------ the checks

def _maxdiff(a, b):
    return max(abs(x - y) for x, y in zip(a, b))

def run(Bmax=60, trials=20000, seed=1339):
    out = {"Bmax": Bmax, "trials": trials, "seed": seed,
           "exact_checks": {}, "stat_checks": {}, "cases": [], "findings": {}}

    # --- EXACT checks: the DP must reproduce the geometric law ---
    p1 = [0.1, 0.5, 0.9]
    par1, c1 = build(3, p1, [], 0.0)
    pol, eff = make_policy("fixed_order", 3, p1, par1, c1)
    out["exact_checks"]["anchor_fixed_order"] = _maxdiff(
        frontier_exact(3, p1, par1, c1, pol, eff, Bmax), anchor_geometric(p1, Bmax))
    pol, eff = make_policy("easiest_first", 3, p1, par1, c1)
    out["exact_checks"]["anchor_easiest_first"] = _maxdiff(
        frontier_exact(3, p1, par1, c1, pol, eff, Bmax),
        anchor_geometric(sorted(p1, reverse=True), Bmax))
    p3 = [0.2] * 4
    parC, cC = build(4, p3, [(0, 1), (1, 2), (2, 3)], 0.0)
    pol, eff = make_policy("fixed_order", 4, p3, parC, cC)
    out["exact_checks"]["zero_coupling_carries_no_value"] = _maxdiff(
        frontier_exact(4, p3, parC, cC, pol, eff, Bmax), anchor_geometric(p3, Bmax))
    parC, cC = build(4, p3, [(0, 1), (1, 2), (2, 3)], 0.35)
    pol, eff = make_policy("easiest_first", 4, p3, parC, cC)
    F = frontier_exact(4, p3, parC, cC, pol, eff, Bmax)
    out["exact_checks"]["determinism_rerun"] = _maxdiff(
        F, frontier_exact(4, p3, parC, cC, pol, eff, Bmax))

    # --- STATISTICAL check: the Monte Carlo must CONVERGE to the exact value ---
    eN, sN = mc_stats(4, p3, parC, cC, pol, eff, Bmax, trials, seed)
    e4, s4 = mc_stats(4, p3, parC, cC, pol, eff, Bmax, 4 * trials, seed + 1)
    out["stat_checks"]["mc_max_abs_error_at_N"] = _maxdiff(eN, F)
    out["stat_checks"]["mc_max_abs_error_at_4N"] = _maxdiff(e4, F)
    out["stat_checks"]["mc_max_abs_z_at_N"] = max(
        abs(eN[b] - F[b]) / (sN[b] / trials ** 0.5) for b in range(1, Bmax + 1) if sN[b] > 0)
    out["stat_checks"]["mc_max_abs_z_at_4N"] = max(
        abs(e4[b] - F[b]) / (s4[b] / (4 * trials) ** 0.5) for b in range(1, Bmax + 1) if s4[b] > 0)

    for case in CASES:
        out["cases"].append(run_case(case, Bmax, seed))

    # --- FINDINGS, computed from the cells ---
    f = out["findings"]
    f["P2_max_coupling_gain_greedy"] = max(
        ((c["B"], c["coupling_gain"]["greedy"]) for case in out["cases"] for c in case["cells"]),
        key=lambda t: t[1])
    f["P2_max_coupling_gain_assumptions_first"] = max(
        ((c["B"], c["coupling_gain"]["assumptions_first"]) for case in out["cases"] for c in case["cells"]),
        key=lambda t: t[1])
    f["placebo_coupling_gain_maxabs"] = max(
        abs(c["coupling_gain"]["placebo"]) for case in out["cases"] for c in case["cells"])
    f["ordering_effect_uncoupled_maxabs"] = max(
        abs(c["ordering_effect_uncoupled"]["placebo"]) for case in out["cases"] for c in case["cells"])
    f["P3_af_minus_greedy_coupled"] = [
        (case["name"], min(c["ordering_effect_coupled"]["assumptions_first"] for c in case["cells"]),
         max(c["ordering_effect_coupled"]["assumptions_first"] for c in case["cells"]))
        for case in out["cases"]]
    f["schedules_coincide_on"] = [
        case["name"] for case in out["cases"]
        if all(abs(c["ordering_effect_coupled"]["assumptions_first"]) == 0.0 for c in case["cells"])]
    return out

def report(out):
    print("issue #139 spike_v0 -- exact obligation-search frontier (Bmax=%d, MC trials=%d)"
          % (out["Bmax"], out["trials"]))
    print("\n-- EXACT instrument checks (must be ~0) --")
    for k, v in out["exact_checks"].items():
        print("  %s %-34s %.3e" % ("OK " if v < 1e-9 else "FAIL", k, v))
    print("-- Monte-Carlo convergence (statistical) --")
    for k, v in out["stat_checks"].items():
        print("     %-34s %.3e" % (k, v))
    for case in out["cases"]:
        print("\n== case %s  p=%s edges=%s c=%s ==" % (case["name"], case["p"], case["edges"], case["c"]))
        print("   frontiers      |   coupled                      |   uncoupled")
        print("  %3s %8s %8s %8s %8s | %8s %8s %8s %8s" % (
            "B", "greedy", "assum", "fixed", "plac", "greedy", "assum", "fixed", "plac"))
        for c in case["cells"]:
            print("  %3d %8.4f %8.4f %8.4f %8.4f | %8.4f %8.4f %8.4f %8.4f" % (
                c["B"], c["coupled"]["greedy"], c["coupled"]["assumptions_first"],
                c["coupled"]["fixed_order"], c["coupled"]["placebo"],
                c["uncoupled"]["greedy"], c["uncoupled"]["assumptions_first"],
                c["uncoupled"]["fixed_order"], c["uncoupled"]["placebo"]))
        print("   COUPLING gain  (coupled - uncoupled, schedule fixed)")
        print("  %3s %8s %8s %8s %8s | %8s" % ("B", "greedy", "assum", "fixed", "plac", "ord.eff.plac"))
        for c in case["cells"]:
            g = c["coupling_gain"]
            print("  %3d %+8.4f %+8.4f %+8.4f %+8.4f | %+8.4f" % (
                c["B"], g["greedy"], g["assumptions_first"], g["fixed_order"],
                g["placebo"], c["ordering_effect_uncoupled"]["placebo"]))
    print("\n-- findings --")
    f = out["findings"]
    print("  P2 max coupling gain, greedy schedule     :", f["P2_max_coupling_gain_greedy"])
    print("  P2 max coupling gain, assumptions-first   :", f["P2_max_coupling_gain_assumptions_first"])
    print("  placebo coupling gain (must be 0) maxabs  :", f["placebo_coupling_gain_maxabs"])
    print("  ordering effect with ZERO coupling maxabs :", f["ordering_effect_uncoupled_maxabs"])
    print("  P3 (assum-first - greedy) on coupled DAG  :", f["P3_af_minus_greedy_coupled"])
    print("  schedules coincide on                     :", f["schedules_coincide_on"])

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--Bmax", type=int, default=60)
    ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1339)
    a = ap.parse_args(argv)
    out = run(a.Bmax, a.trials, a.seed)
    print(json.dumps(out, indent=2, sort_keys=True)) if a.json else report(out)
    return out

if __name__ == "__main__":
    main()
