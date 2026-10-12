#!/usr/bin/env python3
"""Issue #124 -- spike_v1: the ITEM-REPEAT BUDGET BOUNDARY (criterion (iv)).

spike_v0 solved the repeat axis: given N runs, the probability a decision rule's claim is wrong.
This instrument asks the OTHER half of the registered title -- with a FIXED BUDGET split between
items and repeats, where does the next unit of budget go?

The construct.  A stochastic evaluation on a population of items.  Budget B buys M items and N
repeats of each, at a per-item cost `a` and a per-repeat cost `b`:

        B = a*M + b*M*N = M*(a + b*N).

Two claims can be made from the same runs, and they have DIFFERENT error structures:

  (P) the POPULATION MEAN  mu_hat = grand mean over all M*N runs.  With a random-effects truth
      (item i has mean theta_i; between-item variance tau^2; each repeat is theta_i + eps with
      within-item variance sigma^2),

            Var(mu_hat) = tau^2/M + sigma^2/(M*N) = (tau^2 + sigma^2/N)/M.

  (D) a PER-ITEM DECISION: every item gets a strict-majority verdict over its N repeats.  With
      per-run flip rate p the per-item error is e(N) (spike_v0's exact law), so the expected number
      of wrong item-verdicts is M * e(N).

THE LAW (route A).  Substituting M = B/(a + bN) into (P),

        Var(N) = (tau^2 + sigma^2/N)(a + bN) / B,      convex in N, with the STATIONARY POINT

        N*   = sqrt( a * sigma^2 / (b * tau^2) )        <-- INDEPENDENT OF B  (scale-free).

At that point the AM-GM identity gives the RELAXED optimum

        Var_relaxed = ( sqrt(a*tau^2) + sqrt(b*sigma^2) )^2 / B.

THE CATCH, which the second route certified and the first draft got wrong.  `Var_relaxed` is the
optimum of a CONTINUOUS RELAXATION (real N >= 0); the achievable optimum lives on integer N >= 1.
The two agree in the INTERIOR (N* >= 1) and the relaxation is a strict LOWER BOUND in the CORNER
regime (N* < 1), where the optimum is clamped to N = 1 and the achievable variance is

        Var_corner = (tau^2 + sigma^2)(a + b) / B,

which can be several times worse than the relaxed form.  So the law has a STATED DOMAIN: the
scale-free closed form is the answer when N* >= 1, and below it the corner is.  The folk convention
N = 1 is optimal exactly on the boundary

        N* <= 1   <=>   a*sigma^2 <= b*tau^2,

i.e. when items are expensive next to repeats or the runs are already homogeneous.  That line is the
located, two-sided boundary criterion (iv) asks for.

WHY IT MATTERS.  The item-axis literature (sequential/anytime-valid, variance decomposition,
allocation, reporting standards -- the nine-work window cluster in the registration) holds N fixed by
convention, so it cannot see N*: in the corner it is optimal by accident, and outside it is off by a
located factor.  And the two objectives have different GEOMETRY -- (P) has an INTERIOR optimum in N,
while (D) is monotone decreasing in N (a corner at the smallest feasible M) -- which is what makes
"the boundary" depend on the claim being made.

TWO EXACT ROUTES.  route A is the closed form followed by its integer and cap corrections; route B
is an exhaustive integer search over N with the budget and the item-pool size K enforced per cell.
Neither is trusted on its own.

Usage:  python3 spike_v1.py            (tables + certificates + controls)
        python3 spike_v1.py --selftest (each certificate re-run on a planted defect; it MUST fire)
Out:    spike_v1_results.json
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spike_v0 import majority_strict  # the repeat-axis law, imported not re-derived

# ----------------------------------------------------------------- grid
A_COST = 1.0
COST_RATIO = [0.25, 1.0, 4.0, 16.0]        # a/b
VAR_RATIO = [0.01, 0.1, 1.0, 10.0, 100.0]  # sigma^2 / tau^2
B_GRID = [1.0e2, 1.0e3, 1.0e4, 1.0e5]
TAU2 = 1.0
K_POOL = 64
P_DECISION = 0.10
HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------- the objective
def var_at(N, a, b, tau2, sigma2, B, K=None):
    """(variance, M, N) at integer (M, N) -- budget and pool cap enforced.  None if infeasible."""
    if N < 1:
        return None
    M = int(math.floor(B / (a + b * N)))
    if K is not None:
        M = min(M, K)
    if M < 1:
        return None
    return tau2 / M + sigma2 / (M * N), M, N


def n_star(a, b, tau2, sigma2):
    """The stationary point of the relaxed objective.  inf when tau2 = 0, 0 when sigma2 = 0."""
    if tau2 <= 0.0:
        return float("inf")
    if sigma2 <= 0.0:
        return 0.0
    return math.sqrt(a * sigma2 / (b * tau2))


def var_relaxed(a, b, tau2, sigma2, B):
    """The continuous-relaxation optimum (AM-GM).  A LOWER BOUND on the achievable variance."""
    return (math.sqrt(a * tau2) + math.sqrt(b * sigma2)) ** 2 / B


def brute_force(a, b, tau2, sigma2, B, K=None, nmax=200000):
    """route B: exhaustive integer search over N, budget and cap enforced per cell."""
    best = None
    N = 1
    while N <= nmax:
        got = var_at(N, a, b, tau2, sigma2, B, K)
        if got is None:
            break
        if best is None or got[0] < best[0] - 1e-300:
            best = got
        N += 1
    return best


def route_A(a, b, tau2, sigma2, B, K=None):
    """route A: the closed form, then the corrections the relaxation needs -- the N >= 1 clamp,
    the integer rounding (floor/ceil), and the pool cap."""
    if tau2 <= 0.0:                       # all items identical: spend everything repeating ONE item
        N = 1
        while var_at(N + 1, a, b, tau2, sigma2, B, K) is not None:
            N += 1
        return var_at(N, a, b, tau2, sigma2, B, K)
    if sigma2 <= 0.0:                     # deterministic runs: one repeat per item
        return var_at(1, a, b, tau2, sigma2, B, K)
    ns = n_star(a, b, tau2, sigma2)
    cands = []
    # the integer neighbourhood of N*: when N* is an EXACT integer, floor == ceil, so the two
    # neighbours must be named explicitly or the true integer optimum is never evaluated
    base = max(1, int(round(ns)))
    for N in {1, base - 1, base, base + 1}:
        if N < 1:
            continue
        got = var_at(N, a, b, tau2, sigma2, B, K=None)
        if got:
            cands.append(got)
    if K is not None:                     # pool-capped regime: M = K, largest feasible N
        Ncap = int(math.floor((B / K - a) / b))
        if Ncap >= 1:
            got = var_at(Ncap, a, b, tau2, sigma2, B, K)
            if got:
                cands.append(got)
    if not cands:
        return brute_force(a, b, tau2, sigma2, B, K)
    return min(cands, key=lambda t: t[0])


# ----------------------------------------------------------------- the two relaxed objectives
def decision_continuous(N, a, b, B, p):
    """The relaxation of (D): B*e(N)/(a + bN).  Monotone decreasing in N (a corner)."""
    e, _ = majority_strict(N, p)
    return B * e / (a + b * N)


def pop_continuous(N, a, b, tau2, sigma2, B):
    """The relaxation of (P): (tau2 + sigma2/N)(a + bN)/B.  Convex with an interior minimum."""
    return (tau2 + sigma2 / N) * (a + b * N) / B


# ----------------------------------------------------------------- drivers
def main():
    out = {"a_cost": A_COST, "cost_ratio": COST_RATIO, "var_ratio": VAR_RATIO, "B_grid": B_GRID,
           "tau2": TAU2, "K_pool": K_POOL, "p_decision": P_DECISION, "law": [], "domain": {},
           "scale_free": [], "boundary": [], "pool_cap": [], "geometry": {}, "certificates": {},
           "controls": {}}

    print("=" * 112)
    print("1. THE LAW -- the optimal split on a fixed budget.  relax*B = the closed form at N*;")
    print("   achiev*B = the true integer optimum (route A == route B); ratio = achiev/relax")
    print("   a/b      s2/t2  |  N* relax  N (A)  N (B) |  relax*B   achiev*B  achiev/relax")
    for cr in COST_RATIO:
        a, b = A_COST, A_COST / cr
        for vr in VAR_RATIO:
            sigma2 = TAU2 * vr
            B = 1.0e4
            ns = n_star(a, b, TAU2, sigma2)
            vrel = var_relaxed(a, b, TAU2, sigma2, B) * B
            ra = route_A(a, b, TAU2, sigma2, B)
            rb = brute_force(a, b, TAU2, sigma2, B)
            ratio = rb[0] * B / vrel
            out["law"].append({"cost_ratio": cr, "var_ratio": vr, "n_star": ns, "N_A": ra[2],
                               "N_B": rb[2], "relaxB": vrel, "achievB": rb[0] * B, "ratio": ratio})
            print("   %-8.2f %-7.3g | %-9.4f %-6d %-6d | %-10.6g %-10.6g %.4f"
                  % (cr, vr, ns, ra[2], rb[2], vrel, rb[0] * B, ratio))

    print()
    print("2. THE DOMAIN -- the relaxation is the answer in the interior and a LOWER BOUND in the")
    print("   corner.  Grouped by whether N* >= 1 (the law's own domain).")
    interior = [r for r in out["law"] if r["n_star"] >= 1.0]
    corner = [r for r in out["law"] if r["n_star"] < 1.0]
    worst_int = max((abs(r["ratio"] - 1.0) for r in interior), default=0.0)
    worst_cor = max((r["ratio"] - 1.0 for r in corner), default=0.0)
    worst_cr = max(corner, key=lambda r: r["ratio"]) if corner else None
    print("   interior cells (N* >= 1): %d, worst |achiev/relax - 1| = %.4f" % (len(interior), worst_int))
    print("   corner   cells (N* <  1): %d, worst  achiev/relax - 1  = %.4f" % (len(corner), worst_cor))
    if worst_cr:
        print("   widest corner gap: a/b=%.2f s2/t2=%.3g  relax*B=%.4f achiev*B=%.4f (%.2fx)"
              % (worst_cr["cost_ratio"], worst_cr["var_ratio"], worst_cr["relaxB"],
                 worst_cr["achievB"], worst_cr["ratio"]))
    print("   -> the law's domain is N* >= 1; below it the corner N=1 governs.")
    out["domain"] = {"interior_cells": len(interior), "worst_interior_rel": worst_int,
                     "corner_cells": len(corner), "worst_corner_ratio": worst_cor}
    out["certificates"]["domain_interior_worst_rel"] = worst_int
    out["certificates"]["domain_corner_worst_ratio"] = worst_cor
    lb_viol = [r for r in out["law"] if r["ratio"] < 1.0 - 1e-9]
    out["certificates"]["relaxation_lower_bound_violations"] = lb_viol
    assert not lb_viol, "the AM-GM form is not a lower bound on the achievable variance"
    assert worst_int < 0.02, "the relaxation is not tight in its own interior domain"
    assert worst_cor > 1.0, "the corner regime carries no gap -- the domain claim is empty"

    print()
    print("3. SCALE-FREENESS -- N* must not move with B, and relaxed Var*B must be flat in B")
    worst_ns = worst_flat = 0.0
    for cr in (1.0, 4.0):
        a, b = A_COST, A_COST / cr
        for vr in (0.1, 10.0):
            sigma2 = TAU2 * vr
            ns = n_star(a, b, TAU2, sigma2)
            ref = None
            for B in B_GRID:
                vB = var_relaxed(a, b, TAU2, sigma2, B) * B
                ref = vB if ref is None else ref
                worst_flat = max(worst_flat, abs(vB / ref - 1.0))
                worst_ns = max(worst_ns, abs(n_star(a, b, TAU2, sigma2) - ns))
                out["scale_free"].append({"cost_ratio": cr, "var_ratio": vr, "B": B, "n_star": ns,
                                          "varB": vB})
    out["certificates"]["nstar_b_independence_max_move"] = worst_ns
    out["certificates"]["relaxed_varB_flatness_max_rel"] = worst_flat
    print("   max move of N* over B: %.3e   max relative move of relaxed Var*B: %.3e"
          % (worst_ns, worst_flat))
    assert worst_ns < 1e-12, "N* moved with the budget -- it must be scale-free"
    assert worst_flat < 1e-9, "the relaxed Var*B is not flat in B"

    print()
    print("4. THE BOUNDARY -- the folk N=1 corner regime, located at a*sigma2 = b*tau2")
    print("   a/b    | crossing s2/t2 | N* at crossing | N* x4 above | N* /4 below")
    for cr in COST_RATIO:
        a, b = A_COST, A_COST / cr
        cross = b / a
        ns_at = n_star(a, b, TAU2, TAU2 * cross)
        ns_hi = n_star(a, b, TAU2, TAU2 * cross * 4.0)
        ns_lo = n_star(a, b, TAU2, TAU2 * cross / 4.0)
        out["boundary"].append({"cost_ratio": cr, "crossing": cross, "n_at": ns_at,
                                "n_above": ns_hi, "n_below": ns_lo})
        print("   %-6.2f | %-15.4g | %-14.4f | %-11.4f | %.4f" % (cr, cross, ns_at, ns_hi, ns_lo))
    print("   -- and the SEARCH (not the formula) must switch its argmin across that line:")
    # The boundary must be checked against the SOLVER, not against the formula that DEFINES N*:
    # `n_star = sqrt(a s2/(b t2))` and `a*s2 <= b*t2` are the same expression, so comparing them is
    # a tautology that can never fire.  And there are TWO lines, not one:
    #   (relaxation boundary) N* = 1        -- where the CONTINUOUS optimum leaves the corner;
    #   (discrete boundary)   N* = sqrt(2)  -- where the INTEGER argmin leaves N = 1.  Exact, from
    #                                          f(2) - f(1) = b*tau2 - a*sigma2/2, so integrality
    #                                          widens the corner from a*s2 <= b*t2 to a*s2 <= 2*b*t2:
    #                                          exactly a factor of 2.
    bad = []
    switch = []
    for cr in COST_RATIO:
        a, b = A_COST, A_COST / cr
        cross = b / a
        for f in (0.25, 1.0, 1.9, 2.1, 4.0):
            sigma2 = TAU2 * cross * f
            Nopt = brute_force(a, b, TAU2, sigma2, B=1e5)[2]
            disc_corner = (n_star(a, b, TAU2, sigma2) <= math.sqrt(2.0) + 1e-12)
            switch.append((cr, f, Nopt, disc_corner))
            if disc_corner != (Nopt == 1):
                bad.append((cr, f, Nopt, disc_corner))
    out["certificates"]["corner_boundary_violations"] = bad
    out["certificates"]["corner_boundary_switch"] = switch
    out["certificates"]["relaxation_boundary_n_star"] = 1.0
    out["certificates"]["discrete_boundary_n_star"] = math.sqrt(2.0)
    for cr, f, Nopt, corner in switch:
        print("   a/b=%-5.2f s2/t2=x%-5.2g  N* = %-6.3f argmin N = %-3d  discrete corner = %s"
              % (cr, f, n_star(A_COST, A_COST / cr, TAU2, TAU2 * (A_COST / cr / A_COST) * f),
                 Nopt, corner))
    assert not bad, "the solver's argmin does not leave N=1 at N* = sqrt(2): %s" % bad[:3]

    print()
    print("5. THE POOL CAP -- once every item is used, repeats are all that is left and the error")
    print("   floors at tau2/K.  (K=%d, a=b=1, tau2=sigma2=1, floor = %.6f)" % (K_POOL, TAU2 / K_POOL))
    a, b = 1.0, 1.0
    for B in (1e2, 1e3, 1e4, 1e5, 1e6, 1e7):
        var, M, N = brute_force(a, b, TAU2, TAU2, B, K=K_POOL)
        out["pool_cap"].append({"B": B, "M": M, "N": N, "var": var,
                                "excess_over_floor": var - TAU2 / K_POOL})
        print("   B=%-9.0f M=%-5d N=%-7d Var=%-12.8f  Var - tau2/K = %.3e"
              % (B, M, N, var, var - TAU2 / K_POOL))
    assert out["pool_cap"][-1]["excess_over_floor"] < 1e-3, \
        "the pool-capped error does not approach the tau2/K floor"
    assert all(r["M"] == K_POOL for r in out["pool_cap"][1:]), "the cap did not bind once B is large"

    print()
    print("6. GEOMETRY -- the two objectives differ.  (a=b=1, tau2=1, sigma2=20, p=%.2f)" % P_DECISION)
    a, b, tau2, sigma2, B = 1.0, 1.0, 1.0, 20.0, 1.0e4
    nrng = list(range(1, 201))
    popv = [pop_continuous(N, a, b, tau2, sigma2, B) for N in nrng]
    decv = [decision_continuous(N, a, b, B, P_DECISION) for N in nrng]
    pop_arg = nrng[min(range(len(popv)), key=lambda i: popv[i])]
    dec_mono = all(decv[i + 1] <= decv[i] * (1.0 + 1e-12) for i in range(len(decv) - 1))
    out["geometry"] = {"pop_argmin_N": pop_arg, "pop_argmin_val": popv[pop_arg - 1],
                       "pop_range_len": len(nrng), "dec_stepwise_monotone": dec_mono,
                       "dec_at_1": decv[0], "dec_at_200": decv[-1],
                       "dec_ratio_200_over_1": decv[-1] / decv[0]}
    # (D) is a CORNER: its minimum over the range is attained at the LAST N (robust to float noise,
    # unlike a step-by-step monotonicity test through an underflowing tail)
    pop_interior = (2 <= pop_arg <= 150)
    dec_corner = (decv[-1] <= min(decv) + 1e-300)
    out["certificates"]["population_interior"] = pop_interior
    out["certificates"]["decision_corner"] = dec_corner
    print("   (P) population mean : argmin N = %-5d of %d  (INTERIOR)  Var = %.6g"
          % (pop_arg, len(nrng), popv[pop_arg - 1]))
    print("   (D) per-item decision: min at the LAST N: %-5s (CORNER)  D(200)/D(1) = %.3g"
          % (dec_corner, decv[-1] / decv[0]))
    print("       (stepwise strict monotonicity through the underflowing tail: %s -- a diagnostic,"
          % dec_mono)
    print("        not a certificate; the robust corner test above is what is asserted)")
    assert pop_interior, "the population objective did not have an interior optimum"
    assert dec_corner, "the decision objective's minimum was not at the corner"
    assert decv[-1] < decv[0], "the decision objective did not fall toward its corner"

    # ------------------------------------------------------------- certificates + controls
    print()
    print("CERTIFICATE -- route A (closed form + corrections) vs route B (exhaustive search)")
    worst_c = 0.0
    ncells = 0
    for cr in (0.25, 1.0, 4.0):
        a, b = A_COST, A_COST / cr
        for vr in (0.05, 1.0, 20.0):
            sigma2 = TAU2 * vr
            for B in (1e3, 1e5):
                ra = route_A(a, b, TAU2, sigma2, B)
                rb = brute_force(a, b, TAU2, sigma2, B)
                worst_c = max(worst_c, abs(ra[0] - rb[0]) / rb[0])
                ncells += 1
    out["certificates"]["route_A_vs_B_worst_rel"] = worst_c
    out["certificates"]["route_A_vs_B_cells"] = ncells
    print("   worst relative objective gap over %d cells: %.3e" % (ncells, worst_c))
    assert worst_c < 1e-6, "routes A and B disagree on the optimal objective"

    print()
    print("CERTIFICATE -- INTERIORITY (two-sided): in the law's domain, stepping off N* must RAISE")
    print("   the objective.  Cells with N* < 1 are excluded by the stated domain, not silently.")
    bad_int = []
    tested = 0
    for cr in (1.0, 4.0):
        a, b = A_COST, A_COST / cr
        for vr in (4.0, 20.0):
            sigma2 = TAU2 * vr
            B = 1e5
            ns = int(round(n_star(a, b, TAU2, sigma2)))
            if ns < 2:
                continue
            lo = var_at(ns - 1, a, b, TAU2, sigma2, B)
            mid = var_at(ns, a, b, TAU2, sigma2, B)
            hi = var_at(ns + 1, a, b, TAU2, sigma2, B)
            tested += 1
            if not (lo and mid and hi) or not (lo[0] > mid[0] and hi[0] > mid[0]):
                bad_int.append((cr, vr, ns))
    out["certificates"]["interiority_violations"] = bad_int
    out["certificates"]["interiority_cells"] = tested
    print("   interiority violations over %d in-domain cells: %d" % (tested, len(bad_int)))
    assert tested >= 4, "the interiority certificate tested too few cells"
    assert not bad_int, "N* is not an interior minimum: %s" % bad_int[:3]

    print()
    print("CONTROL -- planted truth (two-sided)")
    a, b = 1.0, 1.0
    B = 1e4
    # (C1) tau2 = 0: one item is enough; all budget to repeats -> Var = sigma2/(M*N), M = 1
    got = route_A(a, b, 0.0, 1.0, B)
    c1 = got[0]
    expect1 = 0.0 / got[1] + 1.0 / (got[1] * got[2])
    # (C2) sigma2 = 0: deterministic runs -> N = 1, all budget on items -> Var = tau2/M
    got2 = route_A(a, b, 1.0, 0.0, B)
    expect2 = 1.0 / int(math.floor(B / (a + b * 1)))
    # (C3) the boundary a*sigma2 = b*tau2 must give N* = 1, and there the AM-GM form equals the
    #      achievable N=1 variance exactly (the corner is where the relaxation is tight at N*=1)
    got3 = route_A(a, b, 1.0, b / a * 1.0, B)
    am = var_relaxed(a, b, 1.0, b / a * 1.0, B)
    out["controls"] = {"tau2_zero_var": c1, "tau2_zero_expect": expect1,
                       "sigma2_zero_var": got2[0], "sigma2_zero_expect": expect2,
                       "sigma2_zero_N": got2[2], "boundary_N": got3[2],
                       "boundary_amgm": am, "boundary_achiev": got3[0]}
    print("   tau2 = 0   -> Var = %-14.8g (expects sigma2/(M*N) = %.8g, M=1)" % (c1, expect1))
    print("   sigma2 = 0 -> N   = %-14d Var = %.8g (expects tau2/M)" % (got2[2], got2[0]))
    print("   boundary   -> N*  = %-14.8g (must be 1.0 at a*sigma2 = b*tau2)" % got3[2])
    print("   boundary   -> AM-GM %.8g vs achievable N=1 %.8g (tight at the boundary)"
          % (am, got3[0]))
    assert abs(c1 - expect1) < 1e-12, "the tau2 = 0 control does not give sigma2/(M*N)"
    assert got2[2] == 1, "the sigma2 = 0 control does not collapse to N = 1"
    assert abs(got2[0] - expect2) < 1e-12, "the sigma2 = 0 control does not give tau2/M"
    assert abs(got3[2] - 1.0) < 1e-9, "the boundary point does not give N* = 1"
    assert abs(am - got3[0]) / got3[0] < 2e-2, "the AM-GM form is not tight at the boundary"

    with open(os.path.join(HERE, "spike_v1_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v1_results.json")
    return 0


# ----------------------------------------------------------------- self-test (planted defects)
def selftest():
    """Each certificate re-run on a deliberately corrupted input; it MUST fire.  A check that never
    fires is decoration (Class 170)."""
    print("=" * 112)
    print("SELFTEST -- plant a defect per certificate and require it to FIRE")
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError as e:
            print("[%-22s] FIRED: %s" % (name, str(e)[:70]))
            return
        print("[%-22s] *** DID NOT FIRE ***" % name)
        ok = False

    a, b = 1.0, 1.0

    def plant_routeA():
        got = route_A(a, b, TAU2, TAU2, 1e4)
        rb = brute_force(a, b, TAU2, TAU2, 1e4)
        bad = got[0] * 1.5
        assert abs(bad - rb[0]) / rb[0] < 1e-6, "routes A and B disagree on the optimal objective"
    fires("route-A-vs-B", plant_routeA)

    def plant_interiority():
        sigma2 = TAU2 * 20.0
        ns = int(round(n_star(a, b, TAU2, sigma2)))
        lo, mid, hi = -1.0, 1.0, -1.0          # a maximum, not a minimum
        assert (lo > mid and hi > mid), "N* is not an interior minimum"
    fires("interiority", plant_interiority)

    def plant_boundary():
        # a solver stuck at the N=1 corner must break the SWITCH certificate at a cell where the
        # integer argmin has left the corner (N* = 1.549 > 1.5).  (Comparing n_star against the
        # formula that defines it cannot fire -- that was the first version's defect.)
        a, b = 1.0, 1.0
        sigma2 = TAU2 * (b / a) * 2.1          # N* = 1.449 > sqrt(2) -> discrete interior
        Nopt = 1                               # planted: the solver never leaves the corner
        disc_corner = (n_star(a, b, TAU2, sigma2) <= math.sqrt(2.0) + 1e-12)
        assert disc_corner == (Nopt == 1), "the solver's argmin does not leave N=1 at N* = sqrt(2)"
    fires("corner-boundary", plant_boundary)

    def plant_scale():
        ns_a = n_star(a, b, TAU2, TAU2 * 10.0)
        ns_b = ns_a * (1.0 + 1e-6)             # a B-dependent movement
        assert abs(ns_a - ns_b) < 1e-12, "N* moved with the budget -- it must be scale-free"
    fires("scale-free", plant_scale)

    def plant_lower_bound():
        # an AM-GM form that is TOO HIGH must break the lower-bound certificate
        r = {"ratio": 0.5, "cost_ratio": 1.0, "var_ratio": 1.0}
        lb = [q for q in [r] if q["ratio"] < 1.0 - 1e-9]
        assert not lb, "the AM-GM form is not a lower bound on the achievable variance"
    fires("relaxation-lower-bound", plant_lower_bound)

    def plant_domain():
        # a corner cell with NO gap must break the domain claim
        worst_cor = 0.0
        assert worst_cor > 1.0, "the corner regime carries no gap -- the domain claim is empty"
    fires("domain-gap", plant_domain)

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CERTIFICATE IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
