#!/usr/bin/env python3
"""spike_v1.py -- issue #139 (R615): the scaled exact frontier grid.

Model (unchanged from spike_v0.py; ground truth by construction)
----------------------------------------------------------------
An obligation set is a DAG (V,E), |V| = n.  Obligation j carries a standalone
difficulty p_j: the probability that ONE attempt discharges it while none of its
parents is discharged.  One attempt costs one budget unit.  Coupling: if at
least one parent of j is discharged, p_j -> min(1, p_j + c); c = 0 is the
uncoupled control.  A schedule is a deterministic map pol : S -> j; the frontier
is F(B) = E[# discharged after B attempts], computed by backward induction over
the 2^n discharged sets -- an exact expectation.

What v1 adds over v0
--------------------
1. THE GRID: the declared DAG families x difficulty vectors x coupling levels,
   at n = 8.
2. THE CERTIFICATE AT c = 0: at c = 0 every schedule used here reduces to a
   FIXED ORDER (its choice criterion -- max p, max (descendants, p), or a fixed
   permutation -- does not depend on which obligations are already discharged),
   and a fixed order's frontier has a closed form: an uncoupled set attempted in
   a fixed order is a sum of independent geometric searches, so
   F(B) = sum_{k>=1} P(sum_{i<=k} G_i <= B).  The DP is therefore checked against
   the closed form AT EVERY GRID POINT, on the order each schedule actually
   induces -- not on one hand-picked fixture.
3. THE CORRECT CONTROL FOR A SCHEDULE CLAIM: the registration's placebo was a
   permuted schedule, which spike_v0 showed is NOT null (ordering has value with
   no graph at all).  The control used here is the SAME schedule on the SAME
   difficulty vector with the EDGES REMOVED: at c = 0 the edges carry no value,
   so a difference there is an ordering effect, not a coupling effect.
4. P1 (concavity + target-budget) and P3' (the schedule effect as an INTERACTION,
   not a universal quantifier) are measured over the grid rather than asserted.

5. A ROBUSTNESS LEG (`--robust`): the same instrument at several sizes and seeds,
   asserting the qualitative findings rather than reporting them once -- a result
   read off a single grid is an n and a seed, not a law.
"""
import argparse
import json
import os
import random
import sys

N = 8
BMAX = 120
CHECKPOINTS = (4, 8, 16, 24, 32, 48, 64, 96, 120)

# ------------------------------------------------------------------ the graphs

def graph(kind, n, seed=139):
    """The declared DAG families.  Edges are (parent, child): child depends on parent."""
    if kind == "empty":
        return []
    if kind == "chain":
        return [(i, i + 1) for i in range(n - 1)]
    if kind == "tree":                        # binary tree, parents before children
        return [((i - 1) // 2, i) for i in range(1, n)]
    if kind == "layered":                     # two layers, complete bipartite
        h = n // 2
        return [(i, j) for i in range(h) for j in range(h, n)]
    if kind == "hub":                         # one root feeding every other
        return [(0, j) for j in range(1, n)]
    if kind.startswith("er"):
        p = float(kind[2:]) / 10.0            # "er03" -> p = 0.3
        rng = random.Random(seed)
        return [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    raise ValueError("unknown graph family: %s" % kind)

def difficulties(kind, n):
    """The declared difficulty vectors.  A vector is FIXED per (kind), so two graphs
    built on the same (kind) share the multiset -- which is what P2' needs."""
    if kind == "uniform":
        return [0.35] * n
    if kind == "easy":
        return [0.60] * n
    if kind == "hard_root":
        return [0.10] + [0.45] * (n - 1)
    if kind == "bimodal":
        return [0.15 if i % 2 == 0 else 0.60 for i in range(n)]
    if kind == "zipf":
        return [round(0.50 / (1.0 + 0.55 * i), 4) for i in range(n)]
    raise ValueError("unknown difficulty vector: %s" % kind)

# ------------------------------------------------------------------- the model

def parents_of(n, edges):
    parents = [[] for _ in range(n)]
    for (i, j) in edges:
        assert 0 <= i < n and 0 <= j < n and i != j, "bad edge %r" % ((i, j),)
        parents[j].append(i)
    return parents

def topo_check(n, parents):
    indeg = [len(parents[j]) for j in range(n)]
    ch = [[] for _ in range(n)]
    for j in range(n):
        for i in parents[j]:
            ch[i].append(j)
    q = [j for j in range(n) if indeg[j] == 0]
    seen = 0
    while q:
        x = q.pop()
        seen += 1
        for y in ch[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    assert seen == n, "edges must form a DAG"

def descendants(n, parents):
    ch = [[] for _ in range(n)]
    for j in range(n):
        for i in parents[j]:
            ch[i].append(j)
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

def eff_table(n, p, parents, c):
    """E[S][j] = the effective success probability of j when S is discharged."""
    full = 1 << n
    E = [[0.0] * n for _ in range(full)]
    for S in range(full):
        row = E[S]
        for j in range(n):
            boosted = parents[j] and any((S >> i) & 1 for i in parents[j])
            row[j] = min(1.0, p[j] + (c if boosted else 0.0))
    return E

def make_policy(kind, n, p, parents, E, seed=139):
    """A schedule as a function of the discharged set S.  Returns A[S] = the choice."""
    full = 1 << n
    if kind == "greedy":                       # max current effective probability
        def crit(S, j):
            return (E[S][j],)
    elif kind == "assumptions_first":          # max descendant cone, then max probability
        d = descendants(n, parents)
        def crit(S, j):
            return (d[j], E[S][j])
    elif kind == "fixed_order":
        def crit(S, j):
            return (-j,)                       # lowest index first
    elif kind == "placebo":
        order = list(range(n))
        random.Random(seed).shuffle(order)
        rank = {j: -order.index(j) for j in range(n)}
        def crit(S, j):
            return (rank[j],)
    else:
        raise ValueError("unknown policy: %s" % kind)
    A = [0] * full
    for S in range(full):
        best = None
        for j in range(n):
            if (S >> j) & 1:
                continue
            k = crit(S, j)
            if best is None or k > best[0]:
                best = (k, j)
        A[S] = best[1] if best else -1
    return A

def frontier_exact(n, E, A, Bmax):
    """F(B) = E[# discharged after B attempts], by backward induction on (S, b)."""
    full = 1 << n
    V = [[0.0] * (Bmax + 1) for _ in range(full)]
    last = full - 1
    for b in range(1, Bmax + 1):
        for S in range(full):
            if S == last:
                continue
            a = A[S]
            q = E[S][a]
            V[S][b] = q * (1.0 + V[S | (1 << a)][b - 1]) + (1.0 - q) * V[S][b - 1]
    return [V[0][b] for b in range(Bmax + 1)]

# ------------------------------------------- the closed-form anchor (uncoupled)

def anchor_geometric(p_order, Bmax):
    """E[count(B)] for an UNCOUPLED set attempted in a FIXED order p_order.

    The attempts needed for obligation k are geometric(p_k), independent, so the
    number completed within B attempts is max{k : sum_{i<=k} G_i <= B} and
    E[count(B)] = sum_{k>=1} P(sum_{i<=k} G_i <= B), by convolution.
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

def induced_order(n, A):
    """The fixed order a schedule induces WHEN ITS CRITERION IS STATE-INDEPENDENT
    (true at c = 0 for every schedule here): follow the choices assuming each
    pick discharges, which is what the criterion's independence makes well defined."""
    S, order = 0, []
    full = 1 << n
    while S != full - 1:
        a = A[S]
        order.append(a)
        S |= 1 << a
    return order

# ---------------------------------------------------------------- P1 utilities

def concavity_defect(F):
    """max_b [ (F[b+1]-F[b]) - (F[b]-F[b-1]) ] clamped at 0.  F is concave iff 0."""
    d = [F[b] - F[b - 1] for b in range(1, len(F))]
    return max([0.0] + [d[i] - d[i - 1] for i in range(1, len(d))])

def first_budget(F, target, n):
    """The smallest B reaching target*n discharged, or None if the grid does not reach it."""
    want = target * n
    for b in range(len(F)):
        if F[b] >= want - 1e-12:
            return b
    return None

# ------------------------------------------------------------------ the grid

GRAPHS = ("empty", "chain", "tree", "layered", "hub", "er03", "er06")
DIFFS = ("uniform", "easy", "hard_root", "bimodal", "zipf")
CS = (0.0, 0.15, 0.35, 0.60)
SCHEDS = ("greedy", "assumptions_first", "fixed_order", "placebo")

def run(seed=139, Bmax=BMAX, n=N):
    cps = [b for b in CHECKPOINTS if b <= Bmax]
    out = {"config": {"n": n, "Bmax": Bmax, "graphs": list(GRAPHS), "difficulties": list(DIFFS),
                      "c": list(CS), "schedules": list(SCHEDS), "seed": seed},
           "certificate": {}, "P1": [], "P2": [], "P3": [], "findings": {}}
    cert_max = 0.0
    cert_cells = 0
    for gk in GRAPHS:
        edges = graph(gk, n, seed)
        parents = parents_of(n, edges)
        topo_check(n, parents)
        for dk in DIFFS:
            p = difficulties(dk, n)
            parents_e = parents_of(n, [])          # the SAME nodes, edges removed
            for c in CS:
                Eg = eff_table(n, p, parents, c)
                Ee = eff_table(n, p, parents_e, c)
                Fg, Fe, Ag = {}, {}, {}
                for sk in SCHEDS:
                    Ag[sk] = make_policy(sk, n, p, parents, Eg, seed)
                    Ae = make_policy(sk, n, p, parents_e, Ee, seed)
                    Fg[sk] = frontier_exact(n, Eg, Ag[sk], Bmax)
                    Fe[sk] = frontier_exact(n, Ee, Ae, Bmax)
                # --- the certificate: at c = 0 the DP must equal the closed form
                #     on the order the schedule itself induces
                if c == 0.0:
                    for sk in SCHEDS:
                        order = induced_order(n, Ag[sk])
                        ref = anchor_geometric([p[a] for a in order], Bmax)
                        cert_max = max(cert_max, max(abs(x - y) for x, y in zip(Fg[sk], ref)))
                        cert_cells += 1
                # --- P1: concavity and the target-budget
                for sk in SCHEDS:
                    F = Fg[sk]
                    B50 = first_budget(F, 0.5, n)
                    B90 = first_budget(F, 0.9, n)
                    out["P1"].append({
                        "graph": gk, "diff": dk, "c": c, "sched": sk,
                        "concavity_defect": concavity_defect(F),
                        "B50": B50, "B90": B90,
                        "ratio_B90_B50": (None if not B50 or B90 is None else round(B90 / B50, 4)),
                        "F_at_Bmax": round(F[Bmax], 6),
                    })
                # --- P2': the coupling gain at a FIXED schedule (coupled vs edges removed)
                for sk in SCHEDS:
                    gains = [Fg[sk][b] - Fe[sk][b] for b in range(Bmax + 1)]
                    mb = max(range(Bmax + 1), key=lambda b: gains[b])
                    out["P2"].append({
                        "graph": gk, "diff": dk, "c": c, "sched": sk,
                        "max_gain": round(gains[mb], 6), "at_B": mb,
                        "gain_at_checkpoints": {str(b): round(gains[b], 6) for b in cps},
                    })
                # --- P3': the schedule effect as an INTERACTION, with its control
                d_af = [Fg["assumptions_first"][b] - Fg["greedy"][b] for b in range(Bmax + 1)]
                d_ctl = [Fe["assumptions_first"][b] - Fe["greedy"][b] for b in range(Bmax + 1)]
                signs = [1 if x > 1e-12 else (-1 if x < -1e-12 else 0) for x in d_af]
                nz = [s for s in signs if s != 0]
                out["P3"].append({
                    "graph": gk, "diff": dk, "c": c,
                    "delta_at_checkpoints": {str(b): round(d_af[b], 6) for b in cps},
                    "delta_min": round(min(d_af), 6), "delta_max": round(max(d_af), 6),
                    "sign_changes": sum(1 for i in range(1, len(nz)) if nz[i] != nz[i - 1]),
                    "control_maxabs": round(max(abs(x) for x in d_ctl), 12),
                })
    out["certificate"] = {"c0_cells": cert_cells, "max_abs_vs_closed_form": cert_max}
    out["findings"] = summarize(out, n)
    return out

def summarize(out, n):
    # `empty` is the CONTROL, not a treatment: the coupling gain there is 0 trivially
    # (the same configuration with the edges removed) and the schedule effect there is
    # the by-construction zero.  Counting it as a treatment cell is what makes a summary
    # report the control's own arithmetic as a finding, so the two are separated here.
    P1 = [r for r in out["P1"] if r["graph"] != "empty"]
    P2 = [r for r in out["P2"] if r["graph"] != "empty"]
    P3 = [r for r in out["P3"] if r["graph"] != "empty"]
    f = {"control_cells_excluded": len(out["P1"]) - len(P1)}
    f["P1_cells"] = len(P1)
    f["P1_concave_cells"] = sum(1 for r in P1 if r["concavity_defect"] <= 1e-9)
    f["P1_max_concavity_defect"] = round(max(r["concavity_defect"] for r in P1), 6)
    ratios = [r["ratio_B90_B50"] for r in P1 if r["ratio_B90_B50"] is not None]
    f["P1_ratio_cells"] = len(ratios)
    f["P1_ratio_min"] = min(ratios) if ratios else None
    f["P1_ratio_max"] = max(ratios) if ratios else None
    f["P1_ratio_ge_1.5"] = sum(1 for x in ratios if x >= 1.5)
    coupled = [r for r in P2 if r["c"] > 0]
    f["P2_coupled_cells"] = len(coupled)
    f["P2_positive_gain_cells"] = sum(1 for r in coupled if r["max_gain"] > 1e-9)
    f["P2_max_gain"] = max((r["max_gain"] for r in coupled), default=None)
    f["P2_gain_at_c0_maxabs"] = max((abs(r["max_gain"])
                                     for r in out["P2"] if r["c"] == 0.0), default=None)
    f["control_empty_max_gain"] = max((abs(r["max_gain"])
                                       for r in out["P2"] if r["graph"] == "empty"), default=None)
    f["P3_control_maxabs"] = max((r["control_maxabs"] for r in P3), default=None)
    inter = [r for r in P3 if r["delta_min"] < -1e-9 and r["delta_max"] > 1e-9]
    pos = [r for r in P3 if r["delta_min"] > 1e-9]
    neg = [r for r in P3 if r["delta_max"] < -1e-9]
    f["P3_cells"] = len(P3)
    f["P3_always_positive"] = len(pos)
    f["P3_always_negative"] = len(neg)
    f["P3_sign_changing"] = len(inter)
    f["P3_identical"] = len(P3) - len(pos) - len(neg) - len(inter)
    return f

# ------------------------------------------------------------------ reporting

def report(out):
    cfg = out["config"]
    print("issue #139 spike_v1 -- the scaled exact frontier grid")
    print("n=%d  Bmax=%d  seed=%d" % (cfg["n"], cfg["Bmax"], cfg["seed"]))
    print("graphs=%s" % ",".join(cfg["graphs"]))
    print("difficulties=%s   c=%s   schedules=%s"
          % (",".join(cfg["difficulties"]), cfg["c"], ",".join(cfg["schedules"])))
    cert = out["certificate"]
    print("\n-- CERTIFICATE at c=0: the DP against the closed form, on the order each"
          " schedule induces --")
    print("   cells=%d   max |DP - closed form| = %.3e" % (cert["c0_cells"], cert["max_abs_vs_closed_form"]))
    f = out["findings"]
    print("\n-- P1: concavity and the target-budget --")
    print("   cells=%d  concave=%d  (max concavity defect %.6f)"
          % (f["P1_cells"], f["P1_concave_cells"], f["P1_max_concavity_defect"]))
    print("   B(0.9)/B(0.5) over %d cells: min=%.3f max=%.3f ; >=1.5 in %d"
          % (f["P1_ratio_cells"], f["P1_ratio_min"], f["P1_ratio_max"], f["P1_ratio_ge_1.5"]))
    print("\n-- P2': the coupling gain at a FIXED schedule (coupled vs edges removed) --")
    print("   coupled cells=%d  positive=%d  max gain=%.4f   |gain| at c=0 (must be 0): %.3e"
          % (f["P2_coupled_cells"], f["P2_positive_gain_cells"], f["P2_max_gain"],
             f["P2_gain_at_c0_maxabs"]))
    print("   the largest gains:")
    for r in sorted([r for r in out["P2"] if r["c"] > 0], key=lambda r: -r["max_gain"])[:6]:
        print("     %-8s %-10s c=%.2f %-18s gain=%+.4f at B=%d"
              % (r["graph"], r["diff"], r["c"], r["sched"], r["max_gain"], r["at_B"]))
    print("\n-- P3': the schedule effect (assumptions-first - greedy) as an interaction --")
    print("   cells=%d  always>0: %d  always<0: %d  SIGN-CHANGING: %d  identical: %d"
          % (f["P3_cells"], f["P3_always_positive"], f["P3_always_negative"],
             f["P3_sign_changing"], f["P3_identical"]))
    print("   control (edges removed) max |delta| over all cells: %.3e" % f["P3_control_maxabs"])
    print("   the cells where the schedule effect changes sign (the crossover):")
    for r in [r for r in out["P3"] if r["delta_min"] < -1e-9 and r["delta_max"] > 1e-9][:8]:
        print("     %-8s %-10s c=%.2f  min=%+.4f  max=%+.4f at %s"
              % (r["graph"], r["diff"], r["c"], r["delta_min"], r["delta_max"],
                 r["delta_at_checkpoints"]))

# ------------------------------------------------------------------- selftest

def selftest():
    """Plant battery: every check must be shown able to FAIL, and the certificate
    must hold on the real grid."""
    ok = 0
    total = 0
    def check(name, cond):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
        else:
            print("  PLANT MISSED: %s" % name)

    n, Bmax = 5, 60
    p = [0.3, 0.5, 0.2, 0.45, 0.6]
    parents = parents_of(n, graph("chain", n))
    E = eff_table(n, p, parents, 0.0)
    A = make_policy("greedy", n, p, parents, E)
    F = frontier_exact(n, E, A, Bmax)
    order = induced_order(n, A)
    ref = anchor_geometric([p[a] for a in order], Bmax)
    check("the certificate holds on a real (graph, schedule) cell",
          max(abs(x - y) for x, y in zip(F, ref)) < 1e-9)
    # PLANT: the same anchor against a WRONG order must disagree -> the check can fail
    wrong = anchor_geometric([p[a] for a in reversed(order)], Bmax)
    check("the certificate FAILS on a deliberately wrong order",
          max(abs(x - y) for x, y in zip(F, wrong)) > 1e-3)
    # PLANT: concavity_defect must be positive on a convex sequence
    check("concavity_defect reports a convex sequence as non-concave",
          concavity_defect([0.0, 1.0, 3.0, 6.0, 10.0]) > 0.9)
    check("concavity_defect reports a concave sequence as concave",
          concavity_defect([0.0, 1.0, 1.5, 1.75, 1.875]) < 1e-12)
    # PLANT: greedy and assumptions-first must coincide when there are no edges
    pe = parents_of(n, [])
    Ee = eff_table(n, p, pe, 0.2)
    Fg = frontier_exact(n, Ee, make_policy("greedy", n, p, pe, Ee), Bmax)
    Fa = frontier_exact(n, Ee, make_policy("assumptions_first", n, p, pe, Ee), Bmax)
    check("with the edges removed the schedule effect is 0 by construction",
          max(abs(x - y) for x, y in zip(Fg, Fa)) < 1e-12)
    # PLANT: on a hub with a hard root the two schedules must NOT coincide
    ph = [0.1] + [0.5] * (n - 1)
    ph_par = parents_of(n, graph("hub", n))
    Eh = eff_table(n, ph, ph_par, 0.4)
    Fg = frontier_exact(n, Eh, make_policy("greedy", n, ph, ph_par, Eh), Bmax)
    Fa = frontier_exact(n, Eh, make_policy("assumptions_first", n, ph, ph_par, Eh), Bmax)
    check("on a hub with a hard root the two schedules DIFFER",
          max(abs(x - y) for x, y in zip(Fg, Fa)) > 1e-3)
    # PLANT: the grid is deterministic
    a = run(seed=7, Bmax=40)
    b = run(seed=7, Bmax=40)
    check("the grid is deterministic across two runs", json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True))
    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1

# ----------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--robust", action="store_true")
    ap.add_argument("--seed", type=int, default=139)
    ap.add_argument("--Bmax", type=int, default=BMAX)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.robust:
        return robustness()
    out = run(a.seed, a.Bmax)
    if a.json:
        text = json.dumps(out, indent=2, sort_keys=True)
        dest = os.environ.get("SPIKE_OUT")
        if dest:
            tmp = dest + ".stage"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(text)
            os.replace(tmp, dest)
        else:
            print(text)
    else:
        report(out)
    return 0


# ----------------------------------------------------------------- robustness

def robustness(sizes=(6, 8, 10), seeds=(139, 271, 511), Bmax=120):
    """Run the whole grid at several (size, seed) and report the invariants the
    findings rest on.  The point is not to add cells to the same grid but to show
    the SHAPE survives a change of size and of seed -- an ER graph is drawn from a
    seed, and a placebo order is too."""
    rows = []
    for n in sizes:
        for sd in seeds:
            out = run(sd, Bmax, n)
            P1 = [r for r in out["P1"] if r["graph"] != "empty"]
            P2 = [r for r in out["P2"] if r["graph"] != "empty"]
            P3 = [r for r in out["P3"] if r["graph"] != "empty"]
            ratios = [r["ratio_B90_B50"] for r in P1 if r["ratio_B90_B50"] is not None]
            rows.append({
                "n": n, "seed": sd,
                "cert_max_abs": out["certificate"]["max_abs_vs_closed_form"],
                "P1_cells": len(P1),
                "P1_concave_pct": round(100.0 * sum(1 for r in P1 if r["concavity_defect"] <= 1e-9) / len(P1), 1),
                "P1_ratio_min": min(ratios) if ratios else None,
                "P1_ratio_ge_1.5": sum(1 for x in ratios if x >= 1.5),
                "P1_ratio_cells": len(ratios),
                "P2_coupled_positive": sum(1 for r in P2 if r["c"] > 0 and r["max_gain"] > 1e-9),
                "P2_coupled_cells": sum(1 for r in P2 if r["c"] > 0),
                "P2_max_gain": max((r["max_gain"] for r in P2 if r["c"] > 0), default=None),
                "P2_gain_at_c0": max((abs(r["max_gain"]) for r in out["P2"] if r["c"] == 0.0), default=None),
                "P3_always_positive": sum(1 for r in P3 if r["delta_min"] > 1e-9),
                "P3_sign_changing": sum(1 for r in P3 if r["delta_min"] < -1e-9 and r["delta_max"] > 1e-9),
                "P3_identical": sum(1 for r in P3 if abs(r["delta_max"]) <= 1e-9 and abs(r["delta_min"]) <= 1e-9),
                "P3_cells": len(P3),
                "P3_control_maxabs": max(r["control_maxabs"] for r in out["P3"]),
            })
    print("-- ROBUSTNESS: the same instrument at several sizes and seeds --")
    print("   n  seed |      cert  concave%  ratio>=1.5 |   P2 max    P2|c0 |  P3>0  P3 sgn  P3 id")
    for r in rows:
        print("  %2d %5d | %9.2e %6.1f%% | %4d/%-4d %9.4f | %6.1e %4d/%-4d | %7d %7d %7d" % (
            r["n"], r["seed"], r["cert_max_abs"], r["P1_concave_pct"],
            r["P1_ratio_ge_1.5"], r["P1_ratio_cells"], r["P2_max_gain"], r["P2_gain_at_c0"],
            r["P2_coupled_positive"], r["P2_coupled_cells"],
            r["P3_always_positive"], r["P3_sign_changing"], r["P3_identical"]))
    bad = [r for r in rows if r["cert_max_abs"] > 1e-9 or r["P2_gain_at_c0"] > 1e-12
           or r["P3_always_positive"] > 0 or r["P3_control_maxabs"] > 1e-12]
    print("\n  INVARIANTS: certificate ~0, coupling gain at c=0 exactly 0, no always-positive"
          " schedule cell, control 0 -- violations: %d" % len(bad))
    return 0 if not bad else 1
if __name__ == "__main__":
    sys.exit(main())
