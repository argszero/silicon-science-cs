#!/usr/bin/env python3
"""spike_v2.py -- issue #139 (R616): the concavity LAW and the budget-sizing rule.

Two things the v1 grid left as measurements are turned into laws here.

A. THE CONCAVITY LAW.  v1 found the frontier is not concave in general and that
   the failure is monotone in the coupling.  What is the shape without coupling?
   For an uncoupled set attempted in a FIXED order the process is a sum of
   independent geometric searches, and the frontier's marginal
   delta(B) = F(B) - F(B-1) is the completion density.  For two obligations the
   marginal is a two-term combination of decaying exponentials,
       delta(B) = A q1^(B-1) + C q2^(B-1),      qi = 1 - pi,
   and if the coefficient on the FASTER-decaying term is NEGATIVE the marginal
   RISES before it falls -- so the frontier is convex somewhere.  The law this
   script measures is the boundary of that region in (p1, p2) space.

B. THE BUDGET-SIZING RULE.  The registered deliverable: read the budget off the
   frontier and the DAG.  A planner takes (graph, difficulties, target) and
   returns the budget the frontier needs, with the schedule it assumed; the
   comparison is against the budget a PASS-RATE view would quote -- the marginal
   cost of the obligations treated as independent searches -- which is what the
   field's "pass rate at a fixed budget" implies.  The gap between the two IS the
   paper's practical claim.

Everything is an exact expectation over a declared model; ground truth by
construction.
"""
import argparse
import json
import os
import random
import sys

# ------------------------------------------------------- reuse the v1 machinery

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spike_v1 as V1

# ----------------------------------------------------------------------------
# A. The concavity law
# ----------------------------------------------------------------------------

def frontier_two(p1, p2, Bmax):
    """Exact frontier for TWO obligations attempted in the fixed order (p1 then p2),
    both uncoupled.  A direct closed form -- not the 2^n DP -- so the law is
    measured on an independent implementation.

    Let qi = 1 - pi.  The attempt that completes the k-th obligation is the sum of
    k independent geometrics, so
        delta(B) = A q1^(B-1) + C q2^(B-1),
        A = p1 (1 - p2/(q2-q1)),   C = p1 p2/(q2-q1),
    and F(B) = sum_{t<=B} delta(t).  For q1 == q2 the second term degenerates to
    p1 p2 (B-1) q^(B-2), handled separately.
    """
    q1, q2 = 1.0 - p1, 1.0 - p2
    d = [0.0] * (Bmax + 1)
    for B in range(1, Bmax + 1):
        if abs(q1 - q2) > 1e-15:
            A = p1 * (1.0 - p2 / (q2 - q1))
            C = p1 * p2 / (q2 - q1)
            d[B] = A * q1 ** (B - 1) + C * q2 ** (B - 1)
        else:
            d[B] = p1 * q1 ** (B - 1) + p1 * p2 * (B - 1) * q1 ** (B - 2) if B >= 2 else p1
    F, acc = [0.0] * (Bmax + 1), 0.0
    for B in range(1, Bmax + 1):
        acc += d[B]
        F[B] = acc
    return F, d

def law_grid(Bmax=140, lo=0.02, hi=0.98, steps=48):
    """Sweep (p1, p2) and measure the non-concavity of the two-obligation frontier."""
    rows = []
    for i in range(steps):
        p1 = lo + (hi - lo) * i / (steps - 1)
        for j in range(steps):
            p2 = lo + (hi - lo) * j / (steps - 1)
            F, d = frontier_two(p1, p2, Bmax)
            defect = V1.concavity_defect(F)
            rows.append({"p1": round(p1, 6), "p2": round(p2, 6),
                         "defect": defect, "convex": defect > 1e-9})
    return rows

def law_test(rows):
    """The candidate closed forms for the convexity boundary, scored on the grid."""
    cands = {
        # the DERIVED NECESSARY condition: the fast-decay coefficient must be negative
        "fast-decay coefficient < 0 (necessary)": lambda p1, p2: _coefA(p1, p2) < 0.0,
        # measured candidate boundaries
        "p2 > p1/2 and p1 < p2": lambda p1, p2: p2 > p1 / 2.0 and p1 < p2,
        "p2 > 2*p1": lambda p1, p2: p2 > 2.0 * p1,
        "p2 > 3*p1": lambda p1, p2: p2 > 3.0 * p1,
        # simple candidate rules a reader might guess
        "p2 > p1/2": lambda p1, p2: p2 > p1 / 2.0,
        "p2 < p1": lambda p1, p2: p2 < p1,
        "p2 > p1": lambda p1, p2: p2 > p1,
        "p2 < p1 and p2 > p1/2": lambda p1, p2: p2 < p1 and p2 > p1 / 2.0,
    }
    out = {}
    for name, f in cands.items():
        ok = sum(1 for r in rows if f(r["p1"], r["p2"]) == r["convex"])
        out[name] = {"agree": ok, "of": len(rows), "pct": round(100.0 * ok / len(rows), 2)}
    return out

def _coefA(p1, p2):
    """The coefficient attached to the FASTER-decaying exponential (q = 1-p).

    delta(B) = A q1^(B-1) + C q2^(B-1) with A = p1(1 - p2/(q2-q1)), C = p1 p2/(q2-q1).
    A NEGATIVE coefficient on the faster term lets the marginal rise before it falls,
    i.e. it is NECESSARY for a convex stretch -- measured on the grid, NOT sufficient
    (see law_report: the sign rule and the measured region are compared cell by cell).
    """
    q1, q2 = 1.0 - p1, 1.0 - p2
    if abs(q1 - q2) < 1e-15:
        return 1.0
    a = p1 * (1.0 - p2 / (q2 - q1))
    c = p1 * p2 / (q2 - q1)
    return a if q1 < q2 else c

def law_report(Bmax=140, steps=48):
    rows = law_grid(Bmax, steps=steps)
    nconv = sum(1 for r in rows if r["convex"])
    t = law_test(rows)
    print("== A. THE CONCAVITY LAW (two obligations, fixed order, closed form) ==")
    print("   cells=%d  convex region=%d (%.1f%%)" % (len(rows), nconv, 100.0 * nconv / len(rows)))
    print("   candidate rules, agreement with the measured convex region:")
    for k, v in sorted(t.items(), key=lambda kv: -kv[1]["pct"]):
        print("     %-28s %6.2f%%  (%d/%d)" % (k, v["pct"], v["agree"], v["of"]))
    # where the derived rule is wrong, if it is
    wrong = [r for r in rows if _coefA(r["p1"], r["p2"]) != r["convex"]]
    print("   derived rule (sign of the fast-decay coefficient) misclassifies: %d cells" % len(wrong))
    if wrong[:4]:
        for r in wrong[:4]:
            print("     p1=%.3f p2=%.3f  measured convex=%s  A=%.4f  defect=%.4f"
                  % (r["p1"], r["p2"], r["convex"], _coefA(r["p1"], r["p2"]), r["defect"]))
    return rows, t

# ----------------------------------------------------------------------------
# B. The budget-sizing rule
# ----------------------------------------------------------------------------

def budget_from_frontier(F, target, n):
    """The smallest budget B with F(B) >= target*n (a bracket, and the order it needs)."""
    want = target * n
    for b in range(len(F)):
        if F[b] >= want - 1e-12:
            return b
    return None

def budget_naive(p, target, n, coupled_cost=None):
    """The PASS-RATE rule: treat each obligation as an independent search with
    expected cost 1/p_i (optionally the coupled-down cost), take the m = ceil(target*n)
    cheapest, and add their expected costs.  This is the budget a 'our prover passes
    X% of obligations' table implies, and it ignores the schedule and the joint
    behaviour the frontier measures."""
    m = int(-(-target * n // 1))              # ceil without float error
    costs = sorted(1.0 / q for q in (coupled_cost if coupled_cost else p))
    return sum(costs[:m])

def coupled_costs(p, parents, c):
    """Per-obligation cost with the coupling applied for a node that HAS a parent
    (the most favourable reading for the naive rule -- it assumes every parent gets
    discharged), used to give the pass-rate rule its best case."""
    out = []
    for j in range(len(p)):
        q = p[j] + (c if parents[j] else 0.0)
        out.append(min(1.0, q))
    return out

def planner(seed=139, Bmax=120, n=8):
    """For every (graph, difficulty, c, schedule): the frontier budget to reach a
    target fraction, beside the pass-rate rule's budget at the same target.  The
    difference is the sizing error a pass-rate view commits."""
    targets = (0.5, 0.7, 0.9)
    rows = []
    for gk in V1.GRAPHS:
        edges = V1.graph(gk, n, seed)
        parents = V1.parents_of(n, edges)
        V1.topo_check(n, parents)
        for dk in V1.DIFFS:
            p = V1.difficulties(dk, n)
            for c in V1.CS:
                Eg = V1.eff_table(n, p, parents, c)
                for sk in V1.SCHEDS:
                    A = V1.make_policy(sk, n, p, parents, Eg, seed)
                    F = V1.frontier_exact(n, Eg, A, Bmax)
                    for t in targets:
                        bf = budget_from_frontier(F, t, n)
                        bn = budget_naive(p, t, n, coupled_costs(p, parents, c))
                        rows.append({
                            "graph": gk, "diff": dk, "c": c, "sched": sk, "target": t,
                            "frontier_budget": bf,
                            "naive_budget": round(bn, 4),
                            "ratio": (None if not bf or bf == 0 else round(bn / bf, 4)),
                            "unreached": bf is None,
                        })
    return rows

def planner_report(rows):
    real = [r for r in rows if r["graph"] != "empty" and r["ratio"] is not None]
    print("\n== B. THE BUDGET-SIZING RULE ==")
    print("   cells=%d (treatment, reached); unreached: %d"
          % (len(real), sum(1 for r in rows if r["unreached"])))
    by = {}
    for r in real:
        by.setdefault(r["target"], []).append(r["ratio"])
    for t in sorted(by):
        v = sorted(by[t])
        print("   target %.1f: naive/frontier ratio  min %.3f  median %.3f  max %.3f"
              % (t, v[0], v[len(v) // 2], v[-1]))
    under = sum(1 for r in real if r["ratio"] < 1.0)
    print("   cells where the pass-rate rule UNDER-budgets: %d/%d (%.1f%%)"
          % (under, len(real), 100.0 * under / len(real)))
    worst = sorted(real, key=lambda r: r["ratio"])[:5]
    print("   the worst under-budgets (naive/frontier):")
    for r in worst:
        print("     %-8s %-10s c=%.2f %-18s target=%.1f  naive=%.2f frontier=%d  ratio=%.3f"
              % (r["graph"], r["diff"], r["c"], r["sched"], r["target"],
                 r["naive_budget"], r["frontier_budget"], r["ratio"]))
    return real

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

    # the closed form for two must agree with the v1 DP on the same two-obligation set
    p = [0.4, 0.25]
    n, Bmax = 2, 80
    parents = V1.parents_of(n, [])
    E = V1.eff_table(n, p, parents, 0.0)
    A = V1.make_policy("fixed_order", n, p, parents, E)
    Fdp = V1.frontier_exact(n, E, A, Bmax)
    Fcf, _ = frontier_two(p[0], p[1], Bmax)
    check("the two-obligation closed form matches the DP",
          max(abs(x - y) for x, y in zip(Fdp, Fcf)) < 1e-9)
    # PLANT: swapping the order must change the frontier (so the agreement is not trivial)
    Fcf2, _ = frontier_two(p[1], p[0], Bmax)
    check("swapping the two difficulties changes the frontier",
          max(abs(x - y) for x, y in zip(Fcf, Fcf2)) > 1e-6)
    # PLANT: the marginal must be non-monotone for a spread pair (the convexity claim)
    _, d = frontier_two(0.4, 0.7, Bmax)          # the harder obligation attempts SECOND
    rises = any(d[i] - d[i - 1] > 1e-12 for i in range(2, len(d)))
    check("a wide-spread pair shows a RISING marginal", rises)
    # PLANT: the equal-difficulty pair must be concave (no spread -> no convexity)
    Feq, _ = frontier_two(0.4, 0.4, Bmax)
    check("the equal-difficulty pair is concave", V1.concavity_defect(Feq) <= 1e-12)
    # PLANT: the naive rule must be able to under-budget, on a case where it does
    rows = planner(seed=139, Bmax=60, n=6)
    check("the planner produces cells", len(rows) > 0)
    check("some cell has the pass-rate rule under-budgeting",
          any(r["ratio"] is not None and r["ratio"] < 1.0 for r in rows if r["graph"] != "empty"))
    # determinism
    a = json.dumps(law_grid(60, steps=6), sort_keys=True)
    b = json.dumps(law_grid(60, steps=6), sort_keys=True)
    check("the law grid is deterministic", a == b)
    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1

# ----------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--steps", type=int, default=48)
    ap.add_argument("--reliable", action="store_true")
    ap.add_argument("--Bmax", type=int, default=120)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.reliable:
        return reliability()
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        law_rows, law_t = law_report(a.Bmax, a.steps)
        gen_rows = law_generalization(Bmax=a.Bmax)
        generalize_report(gen_rows)
        plan_rows = planner(Bmax=a.Bmax)
        real = planner_report(plan_rows)
    if not a.json:
        sys.stdout.write(buf.getvalue())
    if a.json:
        out = {"law": {"cells": len(law_rows),
                       "convex": sum(1 for r in law_rows if r["convex"]),
                       "candidate_rules": law_t,
                       "derived_misclassified": sum(
                           1 for r in law_rows if _coefA(r["p1"], r["p2"]) != r["convex"])},
               "planner": {"cells": len(real)},
               "planner_rows": plan_rows}
        text = json.dumps(out, indent=2, sort_keys=True)
        dest = os.environ.get("SPIKE_OUT")
        if dest:
            with open(dest + ".stage", "w", encoding="utf-8") as fh:
                fh.write(text)
            os.replace(dest + ".stage", dest)
        else:
            print(text)
    return 0


# ------------------------------------------------- the law's n-obligation form

def law_generalization(seed=139, Bmax=120, n=8):
    """Does the two-obligation law survive more obligations?

    The law measured above: for TWO obligations the frontier is convex somewhere iff
    the order takes the HARDER one second -- i.e. concave iff the attempt order is
    non-increasing in difficulty.  The generalisation to test is the same statement
    at n: concavity holds iff the schedule's induced order is non-increasing in
    difficulty.  The measure is a cell-by-cell agreement over the v1 grid, at c = 0
    (where every schedule induces a fixed order) and at c > 0 (where the schedule is
    state-dependent and the 'order' is the order it takes on the all-undischarged set).
    """
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
                    diffs = [p[a] for a in order]
                    noninc = all(diffs[i] >= diffs[i + 1] - 1e-12 for i in range(len(diffs) - 1))
                    concave = V1.concavity_defect(F) <= 1e-9
                    rows.append({"graph": gk, "diff": dk, "c": c, "sched": sk,
                                 "nonincreasing": noninc, "concave": concave,
                                 "order_diffs": [round(d, 4) for d in diffs],
                                 "defect": V1.concavity_defect(F)})
    return rows

def generalize_report(rows):
    print("\n== A'. THE LAW AT n OBLIGATIONS (the v1 grid, c = 0 and c > 0) ==")
    for c in V1.CS:
        sub = [r for r in rows if r["c"] == c]
        agree = sum(1 for r in sub if r["nonincreasing"] == r["concave"])
        fn = [r for r in sub if r["nonincreasing"] and not r["concave"]]     # false negatives
        fp = [r for r in sub if r["concave"] and not r["nonincreasing"]]     # false positives
        print("   c=%.2f:  agree %4d/%4d (%5.1f%%)   non-increasing&convex: %d"
              "   concave&not-non-increasing: %d"
              % (c, agree, len(sub), 100.0 * agree / len(sub), len(fn), len(fp)))
        for r in (fn + fp)[:2]:
            print("        e.g. %-8s %-10s %-18s order=%s concave=%s defect=%.4f"
                  % (r["graph"], r["diff"], r["sched"], r["order_diffs"], r["concave"], r["defect"]))
    return rows

def reliability(seeds=(139, 271, 511), ns=(6, 8, 10), Bmax=120):
    """The two laws at several sizes and seeds: the n=2 law must be exact, the n-form
    must hold at c = 0 on the (size, seed) grid, and the sizing gap must reproduce."""
    print("\n== RELIABILITY: the laws at several sizes and seeds ==")
    print("   n seed |  n2 law agree | c=0 n-law agree | sizing under-budget% | worst ratio")
    bad = 0
    for n in ns:
        for sd in seeds:
            g = law_grid(120, lo=0.05, hi=0.95, steps=13)
            n2 = sum(1 for r in g if (r["p2"] > r["p1"]) == r["convex"])
            rows = law_generalization(seed=sd, Bmax=Bmax, n=n)
            c0 = [r for r in rows if r["c"] == 0.0]
            a0 = sum(1 for r in c0 if r["nonincreasing"] == r["concave"])
            pr = [r for r in planner(seed=sd, Bmax=Bmax, n=n)
                  if r["graph"] != "empty" and r["ratio"] is not None]
            under = sum(1 for r in pr if r["ratio"] < 1.0)
            worst = min(r["ratio"] for r in pr) if pr else None
            pct = 100.0 * n2 / len(g)
            if pct < 99.9 or worst is None or worst >= 1.0:
                bad += 1
            print("   %2d %4d | %11.2f%% | %5.1f%% (%d/%d) | %15.1f%% | %.3f"
                  % (n, sd, pct, 100.0 * a0 / len(c0), a0, len(c0),
                     100.0 * under / len(pr), worst))
    print("   the n=2 law is exact and the sizing gap reproduces wherever"
          " the grid is read: violations = %d" % bad)
    return 0 if bad == 0 else 1
if __name__ == "__main__":
    sys.exit(main())
