#!/usr/bin/env python3
"""Issue #124 -- spike_v0: the exact error law of a decision over N repeated runs.

The construct.  A stochastic evaluation is repeated N times.  Each repeat produces a verdict, and the
verdict disagrees with the truth with probability p -- the *repeat instability*, the one input a
practitioner can measure.  A decision RULE aggregates the N verdicts into one claim.  This script
computes, EXACTLY, the probability that the claim is wrong:

    majority-strict   a verdict requires a strict majority; an even N that ties yields NO verdict
                      (reported separately as `unresolved` -- an absence, not an error)
    majority-opt      the same rule with the tie resolved to one side (the optimistic reading)
    unanimity         a verdict requires all N to agree (one dissenter withholds the claim)
    any-of            a verdict requires at least one run to assert it
    mean              a continuous score X_r ~ Normal(+delta/2, sigma^2) under the truth and the
                      claim sign(mean(X)): the resolution-limited rule

Why the exact forms matter.  The strict-majority error is a binomial tail whose rate is the
Bernoulli divergence D(q || 1/2) -- steep at small p, flat (-> 0) as p -> 1/2.  "How many runs" is
therefore not a constant but the reciprocal of a divergence, and it diverges at the top of the range.
And withholding a tie is not cosmetic: at the same budget an even N beats the odd N above it, because
the tie is the one outcome that carries no claim.

The law's input is not sufficient on its own.  Real repeats are not exchangeable -- a run that flipped
makes the next flip likelier.  The script solves the SAME decision exactly when the verdict sequence
is a two-state Markov chain with the SAME stationary p and lag-1 correlation rho, and reports the
EFFECTIVE repeat count: how many independent runs the correlated N is worth.

TWO EXACT ROUTES.  Every tail is computed twice -- by `scipy.stats.binom.sf` (route A) and by an
independent log-space summation of the pmf (route B) -- because a single route that fails silently is
indistinguishable from a discovery.  The first version of this instrument summed a recursion anchored
at P(X = 0); for p near 1/2 and n > ~1100 that anchor underflows, and once the accumulated sum passed
1 the clamp `max(0, 1 - s)` returned an error of exactly ZERO -- a perfect result manufactured by a
sum that exceeded its own bound.  Routes A/B, the monotonicity invariants, and the large-n
certificate are what caught it.

Usage:  python3 spike_v0.py
Out:    spike_v0_results.json
"""
import json
import math
import os
import random
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))

from scipy.stats import binom

SEED0 = 20261003
P_GRID = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.45, 0.49, 0.50]
N_SHOW = [1, 2, 3, 4, 5, 10]
RHO_GRID = [0.0, 0.1, 0.25, 0.4, 0.6, 0.8]
EPS_GRID = [0.10, 0.05, 0.01, 0.001]
REL_P = 0.25            # the relative precision at which "the error can be STATED"
MC_TRIALS = 200000
MC_N = [1, 3, 5, 10, 30]


def cell_seed(*parts):
    """A seed that is a function of the REQUEST and nothing else: `hash()` of a str is randomized per
    process, so it would make the run unreproducible (Class 159(b))."""
    return SEED0 + zlib.crc32("|".join(str(x) for x in parts).encode("utf-8")) % 1000000


# ---------------------------------------------------------------- two exact routes
def _logpmf(n, i, p):
    return (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + i * math.log(p) + (n - i) * math.log1p(-p))


def tail_B(n, k, p):
    """P(Bin(n,p) >= k) by log-space summation of the pmf -- independent of `binom.sf`, and stable
    where a recursion anchored at P(X = 0) is not."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    logs = [_logpmf(n, i, p) for i in range(k, n + 1)]
    m = max(logs)
    return math.exp(m) * sum(math.exp(x - m) for x in logs)


def tail(n, k, p, route="A"):
    if route == "A":
        return float(binom.sf(k - 1, n, p))
    return tail_B(n, k, p)


def pmf(n, k, p, route="A"):
    if k < 0 or k > n:
        return 0.0
    if route == "A":
        return float(binom.pmf(k, n, p))
    return math.exp(_logpmf(n, k, p))


def divergence(p, q=0.5):
    """Bernoulli KL divergence D(p || q) -- the majority rule's error exponent."""
    if p <= 0.0 or p >= 1.0:
        return float("inf")
    return p * math.log(p / q) + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))


# ---------------------------------------------------------------- the rules
def majority_strict(n, p, route="A"):
    """(error, unresolved): strict majority, a tie yields no verdict."""
    if n % 2 == 1:
        return tail(n, (n + 1) // 2, p, route), 0.0
    return tail(n, n // 2 + 1, p, route), pmf(n, n // 2, p, route)


def majority_opt(n, p, route="A"):
    """Strict majority with the tie resolved to one side (an optimistic rule)."""
    if n % 2 == 1:
        return tail(n, (n + 1) // 2, p, route), 0.0
    return tail(n, n // 2, p, route), 0.0


def unanimity(n, p, route="A"):
    return 1.0 - (1.0 - p) ** n, 0.0


def anyof(n, p, route="A"):
    return p ** n, 0.0


def mean_rule(n, delta, sigma):
    """sign(mean) wrong: the exact normal tail, no simulation."""
    if sigma <= 0:
        return 0.0 if delta > 0 else (1.0 if delta < 0 else 0.5)
    return 0.5 * math.erfc(delta * math.sqrt(n) / (2.0 * sigma) / math.sqrt(2.0))


RULES = {"majority-strict": majority_strict, "majority-opt": majority_opt}


def n_star(p, eps, rule="majority-strict", nmax=5001):
    """Smallest n whose rule error is <= eps, or None if none up to nmax reaches it."""
    f = RULES[rule]
    for n in range(1, nmax):
        if f(n, p)[0] <= eps:
            return n
    return None


def n_for_p_precision(p, rel=REL_P):
    """Runs needed for the relative sd of the instability estimate to reach `rel`:
    sqrt((1-p)/(n p)) <= rel  =>  n >= ceil((1-p)/(p rel^2)).  Normal approximation, stated."""
    if p <= 0.0:
        return None
    return int(math.ceil((1.0 - p) / (p * rel * rel)))


# ---------------------------------------------------------------- correlated repeats
def markov_majority(n, p, rho, route="A"):
    """Exact (error, unresolved) for a strict majority when the verdict sequence is a two-state Markov
    chain with stationary P(wrong) = p and lag-1 correlation rho.

    Parametrisation: alpha = (1-p)(1-rho) = P(right -> wrong), beta = p(1-rho) = P(wrong -> right);
    the stationary law is p and the lag-1 correlation of the indicator is exactly rho, so rho = 0 must
    reproduce the independent tail to machine precision.  Solved by dynamic programming over
    (position, running count of wrong verdicts): exact, O(n^2)."""
    alpha = (1.0 - p) * (1.0 - rho)
    beta = p * (1.0 - rho)
    dist = {(1, 1): p, (0, 0): 1.0 - p}          # (wrong count, current state; 1 = wrong)
    dist = {k: v for k, v in dist.items() if v > 0.0}
    for _ in range(n - 1):
        nd = {}
        for (k, s), pr in dist.items():
            if s == 1:
                nd[(k + 1, 1)] = nd.get((k + 1, 1), 0.0) + pr * (1.0 - alpha)
                nd[(k, 0)] = nd.get((k, 0), 0.0) + pr * alpha
            else:
                nd[(k, 0)] = nd.get((k, 0), 0.0) + pr * (1.0 - beta)
                nd[(k + 1, 1)] = nd.get((k + 1, 1), 0.0) + pr * beta
        dist = nd
    tot = {}
    for (k, _), pr in dist.items():
        tot[k] = tot.get(k, 0.0) + pr
    s = sum(tot.values())
    if abs(s - 1.0) > 1e-9:
        raise AssertionError("the Markov DP lost probability: %.12f" % s)
    if n % 2 == 1:
        return sum(v for k, v in tot.items() if k >= (n + 1) // 2), 0.0
    return (sum(v for k, v in tot.items() if k > n // 2), tot.get(n // 2, 0.0))


def n_effective(n, p, rho):
    """The independent repeat count whose strict-majority error matches the correlated one."""
    target, _ = markov_majority(n, p, rho)
    if target <= 0.0 or target >= 0.5:
        return None
    best, best_d = None, float("inf")
    for m in range(1, 2001):
        e, _ = majority_strict(m, p)
        d = abs(e - target)
        if d < best_d:
            best, best_d = m, d
        if e < target:
            break
    return best


# ---------------------------------------------------------------- Monte-Carlo
def mc_majority(n, p, trials, seed, tie="withhold"):
    rng = random.Random(seed)
    wrong = unres = 0
    for _ in range(trials):
        c = 0
        for _ in range(n):
            if rng.random() < p:
                c += 1
        if n % 2 == 1:
            if c >= (n + 1) // 2:
                wrong += 1
        elif tie == "withhold":
            if c > n // 2:
                wrong += 1
            elif c == n // 2:
                unres += 1
        else:
            if c >= n // 2:
                wrong += 1
    return wrong / trials, unres / trials


def mc_markov(n, p, rho, trials, seed):
    rng = random.Random(seed)
    alpha = (1.0 - p) * (1.0 - rho)
    beta = p * (1.0 - rho)
    wrong = unres = 0
    for _ in range(trials):
        state = 1 if rng.random() < p else 0
        c = state
        for _ in range(n - 1):
            if state == 1:
                state = 0 if rng.random() < alpha else 1
            else:
                state = 1 if rng.random() < beta else 0
            c += state
        if n % 2 == 1:
            if c >= (n + 1) // 2:
                wrong += 1
        else:
            if c > n // 2:
                wrong += 1
            elif c == n // 2:
                unres += 1
    return wrong / trials, unres / trials


def main():
    out = {"seed0": SEED0, "p_grid": P_GRID, "n_show": N_SHOW, "rho_grid": RHO_GRID,
           "eps_grid": EPS_GRID, "rel_p": REL_P, "mc_trials": MC_TRIALS, "mc_n": MC_N,
           "law": [], "even_odd": [], "n_star": [], "divergence": [], "requirements": [],
           "correlated": [], "resolve": [], "certificates": {}, "controls": {}}

    print("=" * 112)
    print("spike_v0 -- the exact error of a decision over N repeated runs (the repeat axis)")
    print()
    print("1. the exact law: P(claim is WRONG)                            [unresolved shown for even N]")
    print("   %-6s %-4s | %-10s %-10s | %-11s | %-10s | %-9s | %-9s" %
          ("p", "N", "maj-strict", "unres", "maj-opt", "unanimity", "any-of", "mean d/s=1"))
    for p in P_GRID:
        for n in N_SHOW:
            es, un = majority_strict(n, p)
            eo, _ = majority_opt(n, p)
            ue, ao = unanimity(n, p)[0], anyof(n, p)[0]
            out["law"].append({"p": p, "n": n, "majority_strict": es, "unresolved": un,
                               "majority_opt": eo, "unanimity": ue, "any_of": ao,
                               "mean_ds1": mean_rule(n, 1.0, 1.0)})
            print("   %-6.2f %-4d | %-10.4g %-10.4g | %-11.4g | %-10.4g | %-9.4g | %-9.4g" %
                  (p, n, es, un, eo, ue, ao, mean_rule(n, 1.0, 1.0)))

    print()
    print("1b. withholding the tie is not cosmetic: at the same budget an even N beats the odd N above")
    print("   %-6s | %-13s %-13s | %-13s %-13s" % ("p", "N=3 strict", "N=4 strict", "N=5 strict", "N=6 strict"))
    for p in (0.05, 0.10, 0.20, 0.30, 0.40, 0.45):
        r = [majority_strict(n, p)[0] for n in (3, 4, 5, 6)]
        out["even_odd"].append({"p": p, "n3": r[0], "n4": r[1], "n5": r[2], "n6": r[3]})
        print("   %-6.2f | %-13.4g %-13.4g | %-13.4g %-13.4g" % (p, r[0], r[1], r[2], r[3]))

    print()
    print("2. the rate is a divergence, not a constant: runs needed for a target error")
    print("   %-6s %-11s | %-8s %-8s %-8s %-8s | %-12s" %
          ("p", "D(p||1/2)", "eps=.10", "eps=.05", "eps=.01", "eps=.001", "n for p +-25%"))
    for p in (0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.45, 0.49):
        row = {"p": p, "divergence": divergence(p), "n_for_p_25pct": n_for_p_precision(p)}
        cells = []
        for eps in EPS_GRID:
            k = n_star(p, eps)
            row["n_for_%s" % eps] = k
            cells.append("none" if k is None else str(k))
        out["divergence"].append(row)
        print("   %-6.2f %-11.5f | %-8s %-8s %-8s %-8s | %-12s" %
              (p, row["divergence"], cells[0], cells[1], cells[2], cells[3], row["n_for_p_25pct"]))

    print()
    print("3. the two requirements, and where they cross (P3)")
    print("   %-6s | %-14s %-18s | %-12s" % ("p", "N: decide@5%", "N: state p to +-25%", "which binds"))
    cross = None
    for p in (0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
        nd = n_star(p, 0.05)
        ne = n_for_p_precision(p)
        if nd is None:
            which = "decision (unreachable)"
        elif ne is None:
            which = "decision"
        else:
            which = "estimation" if ne > nd else "decision"
            if cross is None and ne <= nd:
                cross = p
        out["requirements"].append({"p": p, "n_decide_5pct": nd, "n_state_p_25pct": ne, "binding": which})
        print("   %-6.2f | %-14s %-18s | %-12s" % (p, "none" if nd is None else nd, ne, which))
    out["cross_p"] = cross
    print("   -> the binding requirement switches at p ~ %s" % (cross,))

    print()
    print("4. the law's input is not sufficient: the SAME p with correlated repeats (N = 7)")
    print("   %-6s %-6s | %-11s %-11s | %-11s | %-7s" %
          ("p", "rho", "iid error", "markov err", "unresolved", "N_eff"))
    for p in (0.05, 0.10, 0.20, 0.30):
        e_i, _ = majority_strict(7, p)
        for rho in RHO_GRID:
            e_m, un_m = markov_majority(7, p, rho)
            ne = n_effective(7, p, rho)
            out["correlated"].append({"p": p, "n": 7, "rho": rho, "err_iid": e_i, "err_markov": e_m,
                                      "unresolved": un_m, "n_effective": ne})
            print("   %-6.2f %-6.2f | %-11.4g %-11.4g | %-11.4g | %-7s" %
                  (p, rho, e_i, e_m, un_m, "n/a" if ne is None else ne))

    print()
    print("5. the resolution limit: the gap a fixed repeat count can resolve (mean rule, sigma = 1)")
    print("   %-6s | %-12s %-12s %-12s %-12s" % ("N", "delta=1.0", "delta=0.5", "delta=0.2", "delta=0.1"))
    for n in (1, 2, 3, 5, 10, 30, 100):
        vals = [mean_rule(n, d, 1.0) for d in (1.0, 0.5, 0.2, 0.1)]
        out["resolve"].append({"n": n, "d1.0": vals[0], "d0.5": vals[1], "d0.2": vals[2], "d0.1": vals[3]})
        print("   %-6d | %-12.4g %-12.4g %-12.4g %-12.4g" % (n, vals[0], vals[1], vals[2], vals[3]))

    # ---------------------------------------------------------------- certificates
    print()
    print("CERTIFICATE -- route A (scipy.sf) vs route B (log-space summation)")
    worst = 0.0
    cells = 0
    for p in (0.01, 0.05, 0.10, 0.30, 0.49, 0.5, 0.8):
        for n in (1, 2, 5, 9, 40, 137, 400):
            for frac in (0.25, 0.5, 0.75):
                k = max(0, min(n, int(round(n * frac))))
                a, b = tail(n, k, p, "A"), tail(n, k, p, "B")
                worst = max(worst, abs(a - b))
                cells += 1
    out["certificates"]["route_A_vs_B_max_abs_diff"] = worst
    out["certificates"]["route_cells"] = cells
    print("   worst |A - B| over %d cells: %.3e" % (cells, worst))
    assert worst < 1e-10, "the two exact routes disagree"

    print()
    print("CERTIFICATE -- the large-n region where the FIRST version of this instrument failed")
    big = []
    for p in (0.49, 0.5):
        for n in (1000, 1100, 1106, 1107, 2000, 4000):
            k = n // 2 + 1
            a, b = tail(n, k, p, "A"), tail(n, k, p, "B")
            big.append((p, n, float(a), float(b)))
    out["certificates"]["large_n"] = [{"p": p, "n": n, "route_A": a, "route_B": b} for p, n, a, b in big]
    for p, n, a, b in big:
        print("   p=%.2f n=%-5d  A=%.6f  B=%.6f  diff=%.2e" % (p, n, a, b, abs(a - b)))
    assert all(abs(a - b) < 1e-9 for _, _, a, b in big), "the two routes disagree at large n"
    assert all(0.05 < a < 0.95 for _, _, a, _ in big), \
        "a large-n tail sits at 0 or 1 -- the underflow defect has returned"

    print()
    print("CERTIFICATE -- the exact law against a Monte-Carlo of the same rule")
    zs = []
    for p in (0.05, 0.10, 0.20, 0.30):
        for n in MC_N:
            e, _ = majority_strict(n, p)
            mc, _ = mc_majority(n, p, MC_TRIALS, cell_seed("mc", n, p))
            sd = math.sqrt(max(e * (1 - e), 1e-12) / MC_TRIALS)
            z = (mc - e) / sd
            zs.append(abs(z))
            print("   p=%.2f N=%-3d  exact=%.6f  mc=%.6f  |z|=%.2f" % (p, n, e, mc, abs(z)))
    out["certificates"]["mc_max_abs_z"] = max(zs)
    out["certificates"]["mc_cells"] = len(zs)
    assert max(zs) < 4.0, "the exact law and its Monte-Carlo disagree beyond the sampling band"

    print()
    print("CERTIFICATE -- the Markov solver at rho = 0 must BE the independent tail")
    worst0 = 0.0
    for p in (0.05, 0.10, 0.20, 0.30):
        for n in (1, 3, 4, 7, 10):
            e_m, u_m = markov_majority(n, p, 0.0)
            e_i, u_i = majority_strict(n, p)
            worst0 = max(worst0, abs(e_m - e_i), abs(u_m - u_i))
    out["certificates"]["rho0_identity_max_abs_diff"] = worst0
    print("   worst |markov(rho=0) - iid| over 20 cells: %.3e" % worst0)
    assert worst0 < 1e-12, "the correlated solver does not reduce to the independent law at rho = 0"

    print()
    print("CERTIFICATE -- the correlated solver against its own Monte-Carlo")
    zc = []
    for p in (0.10, 0.30):
        for rho in (0.25, 0.6):
            e, _ = markov_majority(9, p, rho)
            mc, _ = mc_markov(9, p, rho, MC_TRIALS, cell_seed("mcmarkov", 9, p, rho))
            sd = math.sqrt(max(e * (1 - e), 1e-12) / MC_TRIALS)
            z = (mc - e) / sd
            zc.append(abs(z))
            print("   p=%.2f rho=%.2f N=9  exact=%.6f  mc=%.6f  |z|=%.2f" % (p, rho, e, mc, abs(z)))
    out["certificates"]["markov_mc_max_abs_z"] = max(zc)
    assert max(zc) < 4.0, "the correlated solver and its Monte-Carlo disagree"

    # ---------------------------------------------------------------- invariants + controls
    print()
    print("INVARIANT -- the tail must fall in k and rise in p (the overshoot defect broke both)")
    bad = []
    for p in (0.02, 0.10, 0.30, 0.49, 0.50):
        prev = 1.0
        for k in range(0, 201):
            t = tail(200, k, p)
            if t > prev + 1e-12:
                bad.append(("k", p, k))
            prev = t
    prev = -1.0
    for p in (0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.49, 0.5, 0.6):
        t = tail(200, 100, p)
        if t < prev - 1e-12:
            bad.append(("p", p, 100))
        prev = t
    out["certificates"]["monotonicity_violations"] = bad
    print("   violations over 5 x 201 k-cells and 9 p-cells: %d" % len(bad))
    assert not bad, "the exact tail violates its own monotonicity: %s" % bad[:4]

    print()
    print("CONTROL -- planted truth (two-sided)")
    e0, _ = majority_strict(7, 0.0)
    e1, _ = majority_strict(1, 0.31)
    ehalf_odd, _ = majority_strict(1001, 0.5)
    ehalf_even, ueven = majority_strict(1000, 0.5)
    e_frozen, _ = markov_majority(101, 0.20, 1.0 - 1e-9)
    out["controls"] = {"p0_err": e0, "n1_err": e1, "p_half_N1001": ehalf_odd,
                       "p_half_N1000": ehalf_even, "p_half_N1000_unres": ueven,
                       "frozen_err_p020": e_frozen}
    print("   p=0        majority error      = %.3e   (exactly 0)" % e0)
    print("   N=1        majority error      = %.6f  (equals p = 0.31)" % e1)
    print("   p=1/2 N=1001 (odd)  error      = %.6f  (must stay ~1/2: no run count helps)" % ehalf_odd)
    print("   p=1/2 N=1000 (even) error      = %.6f  (the tie is withheld, so it is far below)" % ehalf_even)
    print("   p=1/2 N=1000        unresolved = %.6f" % ueven)
    print("   rho->1, p=0.20      error      = %.6f  (must approach p: the chain freezes)" % e_frozen)
    assert e0 == 0.0, "the no-instability control reports a non-zero error"
    assert abs(e1 - 0.31) < 1e-12, "the single-run control does not equal p"
    assert ehalf_odd > 0.45, "the no-information control must not fall below ~1/2"
    assert abs(e_frozen - 0.20) < 0.02, "the frozen-chain control must approach p"
    assert ehalf_even + ueven > 0.45, "the even-N tie mass has gone missing"

    with open(os.path.join(HERE, "spike_v0_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v0_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
