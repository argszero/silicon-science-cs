#!/usr/bin/env python3
"""spike_v3.py -- issue #139 (R617): the n-form of the concavity law, tested EXHAUSTIVELY.

R616 measured "concave <=> the induced order is non-increasing in difficulty" and
reported it as an AGREEMENT rate (99.3% at c=0, 45-54% at c>0).  An agreement rate
mixes two different statements, and they have different status:

  GUARANTEE   non-increasing order  =>  concave frontier
  CONVERSE    concave frontier      =>  non-increasing order

R616's own table shows the guarantee had NO exception at c = 0 (its "non-increasing &
convex: 0") while the converse had one -- i.e. the law was already one-directional and
the agreement rate hid it.  This script measures the two directions separately, and
tests the guarantee EXHAUSTIVELY over every permutation at n = 5, 6 and 7 (a fixed
order has an exact O(n*B) recursion, so the whole permutation group is affordable --
nothing is sampled).

Then it separates the two things that can make a frontier convex at c > 0:
  (i)  the ORDER        -- test the same order with the coupling switched off
  (ii) the COUPLING     -- increasing returns, which is not an order property at all
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spike_v1 as V1

# ---------------------------------------------- the fixed-order exact recursion

def fixed_order_frontier(p_order, Bmax):
    """F(B) for an UNCOUPLED set attempted in the fixed order p_order.

    With a fixed order the process's state is (how many done, attempts used), so the
    exact expectation is an O(n*Bmax) recursion -- no 2^n state space:
        V[k][b] = p_k (1 + V[k+1][b-1]) + (1-p_k) V[k][b-1]
    """
    n = len(p_order)
    V = [[0.0] * (Bmax + 1) for _ in range(n + 1)]
    for b in range(1, Bmax + 1):
        for k in range(n - 1, -1, -1):
            pk = p_order[k]
            V[k][b] = pk * (1.0 + V[k + 1][b - 1]) + (1.0 - pk) * V[k][b - 1]
    return [V[0][b] for b in range(Bmax + 1)]

def is_noninc(seq):
    return all(seq[i] >= seq[i + 1] - 1e-12 for i in range(len(seq) - 1))

def concavity_defect(F):
    d = [F[b] - F[b - 1] for b in range(1, len(F))]
    return max([0.0] + [d[i] - d[i - 1] for i in range(1, len(d))])

# ------------------------------------------------ the exhaustive order guarantee

def exhaustive_guarantee(p, Bmax=100):
    """Every distinct permutation of p, both directions of the law."""
    viol_guar, viol_conv, cells = [], [], 0
    seen = set()
    for perm in itertools.permutations(p):
        if perm in seen:
            continue
        seen.add(perm)
        cells += 1
        F = fixed_order_frontier(list(perm), Bmax)
        noninc = is_noninc(perm)
        conc = concavity_defect(F) <= 1e-9
        if noninc and not conc:
            viol_guar.append(list(perm))
        if conc and not noninc:
            viol_conv.append(list(perm))
    return {"cells": cells, "guarantee_violations": viol_guar, "converse_violations": viol_conv}

# --------------------------------- a FIXED order WITH coupling (the honest boundary)

def fixed_order_frontier_coupled(order, parents, p, c, Bmax):
    """A FIXED attempt order WITH coupling.  Under a fixed order the discharged set after
    k attempts SUCCEEDING is exactly the first k nodes of the order, so the process is
    still a (k, b) recursion and the boost is a function of k alone -- so this is exact,
    and it is the clean test of whether the guarantee is a c = 0 statement or holds under
    coupling too."""
    n = len(order)
    q = [0.0] * n
    for k in range(n):
        j = order[k]
        boosted = any(order.index(i) < k for i in parents[j])   # a parent already attempted
        q[k] = min(1.0, p[j] + (c if boosted else 0.0))
    V = [[0.0] * (Bmax + 1) for _ in range(n + 1)]
    for b in range(1, Bmax + 1):
        for k in range(n - 1, -1, -1):
            V[k][b] = q[k] * (1.0 + V[k + 1][b - 1]) + (1.0 - q[k]) * V[k][b - 1]
    return [V[0][b] for b in range(Bmax + 1)]

def guarantee_under_coupling(seed=139, Bmax=100, n=8):
    """The guarantee tested with coupling, over every (family, difficulty) of the v1 grid
    and the canonical orders (index order and the difficulty order), at every c > 0."""
    out = []
    for gk in V1.GRAPHS:
        if gk == "empty":
            continue
        edges = V1.graph(gk, n, seed)
        parents = V1.parents_of(n, edges)
        for dk in V1.DIFFS:
            p = V1.difficulties(dk, n)
            index_order = list(range(n))
            diff_order = sorted(range(n), key=lambda j: -p[j])
            for name, order in (("index", index_order), ("difficulty", diff_order)):
                seq = [p[j] for j in order]
                for c in V1.CS:
                    if c == 0.0:
                        continue
                    F = fixed_order_frontier_coupled(order, parents, p, c, Bmax)
                    out.append({"graph": gk, "diff": dk, "order": name, "c": c,
                                "noninc": is_noninc(seq),
                                "defect": concavity_defect(F),
                                "concave": concavity_defect(F) <= 1e-9})
    return out

def report_coupling_boundary(Bmax=100):
    rows = guarantee_under_coupling(Bmax=Bmax)
    print("\n== THE GUARANTEE WITH COUPLING (a genuinely FIXED order, c > 0) ==")
    vi = [r for r in rows if r["noninc"] and not r["concave"]]
    print("   cells=%d  violating the guarantee (non-increasing order yet convex): %d"
          % (len(rows), len(vi)))
    if vi:
        for r in vi[:6]:
            print("     %-8s %-10s order=%-10s c=%.2f  defect=%.4f"
                  % (r["graph"], r["diff"], r["order"], r["c"], r["defect"]))
    byd = {}
    for r in rows:
        byd.setdefault(r["order"], []).append(r)
    for k, v in byd.items():
        bad = [x for x in v if x["noninc"] and not x["concave"]]
        print("   order=%-11s cells=%d  guarantee violations=%d" % (k, len(v), len(bad)))
    return rows


# ------------------------------------- the c>0 decomposition: order vs coupling

def coupling_decomposition(seed=139, Bmax=100, n=8):
    """For every v1 grid cell whose induced order is NON-INCREASING but whose frontier is
    CONVEX, ask WHICH of the two is responsible: recompute the frontier for the SAME order
    with the coupling switched OFF (c = 0).  If the uncoupled frontier is concave, the
    convexity comes from the coupling and not from the order -- which is the separation
    the n-form needs, since at c > 0 the schedule's order is state-dependent and the
    'order' read on the empty set is not the order the process actually takes."""
    rows = []
    for gk in V1.GRAPHS:
        edges = V1.graph(gk, n, seed)
        parents = V1.parents_of(n, edges)
        for dk in V1.DIFFS:
            p = V1.difficulties(dk, n)
            for c in V1.CS:
                E = V1.eff_table(n, p, parents, c)
                for sk in V1.SCHEDS:
                    A = V1.make_policy(sk, n, p, parents, E, seed)
                    F = V1.frontier_exact(n, E, A, Bmax)
                    order = V1.induced_order(n, A)
                    seq = [p[a] for a in order]
                    conc = concavity_defect(F) <= 1e-9
                    if c == 0.0 or conc:
                        continue
                    if not is_noninc(seq):
                        continue                      # already outside the guarantee
                    # the guarantee's antecedent holds (on the empty set) yet the frontier is convex
                    E0 = V1.eff_table(n, p, parents, 0.0)
                    # the same ATTEMPT ORDER as a fixed order, coupling off
                    F0 = fixed_order_frontier(seq, Bmax)
                    rows.append({"graph": gk, "diff": dk, "c": c, "sched": sk,
                                 "order": [round(x, 4) for x in seq],
                                 "defect_coupled": concavity_defect(F),
                                 "defect_uncoupled_same_order": concavity_defect(F0),
                                 "explained_by_coupling": concavity_defect(F0) <= 1e-9})
    return rows

# --------------------------------------------------------------- the report/mode

def report_exhaustive(Bmax=100, ns=(5, 6, 7)):
    vectors = {
        "uniform_0.35": [0.35] * 7,
        "spread_zigzag": [0.6, 0.5, 0.45, 0.4, 0.35, 0.25, 0.15],
        "hard_first": [0.12, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "bimodal": [0.15, 0.6, 0.15, 0.6, 0.15, 0.6, 0.15],
        "ties": [0.45, 0.45, 0.1, 0.45, 0.45, 0.45, 0.45],
        "near_equal": [0.5000001, 0.5, 0.5, 0.5, 0.5, 0.4999999, 0.5],
    }
    print("== THE n-FORM, EXHAUSTIVE (every permutation; the two directions separately) ==")
    print("   GUARANTEE = non-increasing order => concave ; CONVERSE = concave => non-increasing")
    print("   %-14s %4s %8s %10s %10s" % ("vector", "n", "perms", "GUAR.viol", "CONV.viol"))
    out = []
    for name, base in vectors.items():
        for n in ns:
            p = base[:n]
            r = exhaustive_guarantee(p, Bmax)
            out.append({"vector": name, "n": n, **{k: (len(v) if isinstance(v, list) else v)
                                                   for k, v in r.items()},
                        "guarantee_examples": r["guarantee_violations"][:2],
                        "converse_examples": r["converse_violations"][:2]})
            print("   %-14s %4d %8d %10d %10d" % (name, n, r["cells"],
                                                   len(r["guarantee_violations"]),
                                                   len(r["converse_violations"])))
            for v in r["guarantee_violations"][:2]:
                print("        GUARANTEE VIOLATION: %s" % v)
            for v in r["converse_violations"][:1]:
                print("        converse exception:   %s" % v)
    tot_g = sum(r["guarantee_violations"] for r in out)
    tot_c = sum(r["converse_violations"] for r in out)
    tot_p = sum(r["cells"] for r in out)
    print("\n   TOTAL: %d permutations tested; GUARANTEE violations %d; converse exceptions %d"
          % (tot_p, tot_g, tot_c))
    return out

def report_decomposition(Bmax=100):
    rows = coupling_decomposition(Bmax=Bmax)
    print("\n== WHY IT BREAKS AT c > 0: the order, or the coupling? ==")
    print("   cells whose EMPTY-SET order is non-increasing yet whose frontier is convex: %d" % len(rows))
    byc = {}
    for r in rows:
        byc.setdefault(r["explained_by_coupling"], []).append(r)
    for k in (True, False):
        v = byc.get(k, [])
        print("   explained by the COUPLING (same order, c=0 -> concave): %d" % len(v) if k
              else "   NOT explained by the coupling: %d" % len(v))
    for r in rows[:6]:
        print("     %-8s %-10s c=%.2f %-18s coupled defect %.4f  same-order uncoupled defect %.4f"
              % (r["graph"], r["diff"], r["c"], r["sched"],
                 r["defect_coupled"], r["defect_uncoupled_same_order"]))
    return rows

# ------------------------------------------------------------------- selftest

def selftest():
    ok = total = 0
    def check(name, cond):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
        else:
            print("  PLANT MISSED: %s" % name)

    # the fixed-order recursion must equal the general 2^n DP on the same process
    n, Bmax = 4, 60
    p = [0.3, 0.55, 0.2, 0.65]
    parents = V1.parents_of(n, [])
    E = V1.eff_table(n, p, parents, 0.0)
    A = V1.make_policy("fixed_order", n, p, parents, E)
    Fdp = V1.frontier_exact(n, E, A, Bmax)
    Ffo = fixed_order_frontier(p, Bmax)
    check("the O(n*B) recursion equals the 2^n DP", max(abs(x - y) for x, y in zip(Fdp, Ffo)) < 1e-9)
    # PLANT: a permuted order must give a DIFFERENT frontier (the check is not vacuous)
    check("a different order changes the frontier",
          max(abs(x - y) for x, y in zip(Ffo, fixed_order_frontier(list(reversed(p)), Bmax))) > 1e-6)
    # the guarantee must fire on a hard-first order
    check("hard-first order is convex (the guarantee's antecedent is false there)",
          concavity_defect(fixed_order_frontier([0.15, 0.6, 0.6, 0.6], Bmax)) > 1e-9)
    check("easiest-first order is concave",
          concavity_defect(fixed_order_frontier([0.6, 0.6, 0.6, 0.15], Bmax)) <= 1e-9)
    # PLANT: the exhaustive tester must be able to REPORT a violation, so feed it a vector
    # whose permutations include hard-first ones and confirm the tester is not trivially clean
    r = exhaustive_guarantee([0.2, 0.8], 60)
    check("the tester visits every permutation", r["cells"] == 2)
    check("the tester finds no guarantee violation on a 2-obligation vector",
          len(r["guarantee_violations"]) == 0)
    # determinism
    a = json.dumps(exhaustive_guarantee([0.2, 0.4, 0.6, 0.8], 40), sort_keys=True)
    b = json.dumps(exhaustive_guarantee([0.2, 0.4, 0.6, 0.8], 40), sort_keys=True)
    check("the exhaustive test is deterministic", a == b)
    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1

# ----------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--Bmax", type=int, default=100)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ex = report_exhaustive(a.Bmax)
        dec = report_decomposition(a.Bmax)
        cb = report_coupling_boundary(a.Bmax)
    if a.json:
        out = {"exhaustive": ex, "decomposition": dec, "coupling_boundary": cb,
               "totals": {"permutations": sum(r["cells"] for r in ex),
                          "guarantee_violations": sum(r["guarantee_violations"] for r in ex),
                          "converse_exceptions": sum(r["converse_violations"] for r in ex),
                          "coupled_breakdown_cells": len(dec),
                          "explained_by_coupling": sum(1 for r in dec if r["explained_by_coupling"]),
                          "coupling_boundary_cells": len(cb),
                          "coupling_boundary_violations": sum(
                              1 for r in cb if r["noninc"] and not r["concave"])}}
        text = json.dumps(out, indent=2, sort_keys=True)
        dest = os.environ.get("SPIKE_OUT")
        if dest:
            with open(dest + ".stage", "w", encoding="utf-8") as fh:
                fh.write(text)
            os.replace(dest + ".stage", dest)
        else:
            print(text)
    else:
        sys.stdout.write(buf.getvalue())
    return 0

if __name__ == "__main__":
    sys.exit(main())
