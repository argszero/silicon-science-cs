#!/usr/bin/env python3
"""
issue #44 -- instrument_v0.py
"What Does a Verification Budget Buy? Location, Dispersion, and the Sample-Size Ceiling"

Pure stdlib (no numpy/scipy). Deterministic: every cell has a fixed seed.

MODEL
  A verifier re-executes a nondeterministic pipeline k times and tests a statistic
  against a threshold calibrated so an HONEST node is rejected with probability alpha.
  Honest output standardised to N(0, 1)  (mu_H = 0, sigma_H = 1).

  Node mechanisms (the admissible set the node may choose from):
    honest       N(0, 1)                      -- the null
    shift(d)     N(d, 1)                      -- moves the LOCATION
    inflate(r)   N(0, r^2)                    -- LOCATION-PRESERVING, moves dispersion
    collapse(c)  N(c, eps)                    -- LOCATION-PRESERVING at c = 0;
                                                 collapses dispersion (replay style)
    contam(q,b)  with prob q ~ N(b,1) else N(0,1)   mean q*b, var 1+q(1-q)b^2

  Verifier statistics (each calibrated to alpha on the honest node):
    T_mean  reject if sample mean    > tau_m   (closed form available, known sigma)
    T_var   reject if 2nd moment     > tau_v   (chi-square null)
    T_both  reject if either fires, each at alpha/2

CONTROLS (all four must pass before any claim)
  C1 agreement      closed form vs Monte-Carlo on the same cells
  C2 discrimination the variance test MUST see an inflating node the mean test is
                    blind to -- otherwise "undetectable" would be a property of the
                    DATA rather than of the STATISTIC
  C3 null           honest rejection rate == alpha for every statistic
  C4 needle         a mechanism no statistic should detect must indeed not be detected
"""

import json
import math
import os
import random
import statistics


# ---------------------------------------------------------------- special funcs
def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def phi_inv(p):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _gser(a, x, itmax=500, eps=3.0e-16):
    ap = a
    s = 1.0 / a
    d = s
    for _ in range(itmax):
        ap += 1.0
        d *= x / ap
        s += d
        if abs(d) < abs(s) * eps:
            break
    return s * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gcf(a, x, itmax=500, eps=3.0e-16):
    b = x + 1.0 - a
    c = 1.0e300
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1.0e-300:
            d = 1.0e-300
        c = b + an / c
        if abs(c) < 1.0e-300:
            c = 1.0e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def gammq(a, x):
    if x <= 0.0:
        return 1.0
    if x < a + 1.0:
        return 1.0 - _gser(a, x)
    return _gcf(a, x)


def chi2_upper_quantile(k, alpha):
    lo, hi = 1.0e-12, 1.0
    while gammq(k / 2.0, hi / 2.0) > alpha:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if gammq(k / 2.0, mid / 2.0) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- node mechanisms
EPS_COLLAPSE = 1.0e-3


def node_sampler(kind, delta=0.0, rho=1.0, c=0.0, q=0.0, big=0.0):
    if kind == "honest":
        return lambda r: r.gauss(0.0, 1.0)
    if kind == "shift":
        return lambda r: r.gauss(delta, 1.0)
    if kind == "inflate":
        return lambda r: r.gauss(0.0, rho)
    if kind == "collapse":
        return lambda r: r.gauss(c, EPS_COLLAPSE)
    if kind == "shift_inflate":
        return lambda r: r.gauss(delta, rho)
    if kind == "contaminate":
        def f(r):
            if r.random() < q:
                return r.gauss(big, 1.0)
            return r.gauss(0.0, 1.0)
        return f
    raise ValueError("unknown mechanism: %s" % kind)


# ---------------------------------------------------------------- thresholds
def thresholds(k, alpha, split=False):
    a_m = alpha / 2.0 if split else alpha
    a_v = alpha / 2.0 if split else alpha
    tau_m = phi_inv(1.0 - a_m) / math.sqrt(k)
    tau_v = chi2_upper_quantile(k, a_v) / k
    return tau_m, tau_v


def closed_form_mean_power(k, delta, sigma_d, alpha):
    """power of T_mean for a node with mean delta and sd sigma_d (known variance)"""
    c_alpha = phi_inv(1.0 - alpha)
    return phi((math.sqrt(k) * delta - c_alpha) / sigma_d)


# ---------------------------------------------------------------- Monte-Carlo
def mc_power(sampler, k, tau_m, tau_v, n_mc, seed, use_mean=True, use_var=False):
    r = random.Random(seed)
    rej = 0
    for _ in range(n_mc):
        s = 0.0
        ss = 0.0
        for _ in range(k):
            x = sampler(r)
            s += x
            ss += x * x
        hit = False
        if use_mean and (s / k) > tau_m:
            hit = True
        if use_var and (ss / k) > tau_v:
            hit = True
        if hit:
            rej += 1
    return rej / float(n_mc)


def mc_power_streams(sampler, k, tau_m, tau_v, n_mc, n_streams, base_seed,
                     use_mean=True, use_var=False):
    vals = [mc_power(sampler, k, tau_m, tau_v, n_mc, base_seed + 1000 * i,
                     use_mean=use_mean, use_var=use_var)
            for i in range(n_streams)]
    return {"mean": statistics.fmean(vals),
            "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
            "per_stream": vals}


# ---------------------------------------------------------------- experiment
ALPHA = 0.05
N_MC = 8000
N_STREAMS = 3


def seed_for(*parts):
    h = 17
    for p in parts:
        h = (h * 1000003 + int(round(float(p) * 1000))) & 0x7FFFFFFF
    return h


def run():
    out = {"experiment": "issue-44 instrument v0", "alpha": ALPHA,
           "n_mc": N_MC, "n_streams": N_STREAMS, "eps_collapse": EPS_COLLAPSE,
           "controls": {}, "budget_response": {}, "best_responder": {}}

    # C3 null calibration
    c3 = {}
    for k in (5, 32):
        tm, tv = thresholds(k, ALPHA)
        tmS, tvS = thresholds(k, ALPHA, split=True)
        hon = node_sampler("honest")
        c3["k=%d" % k] = {
            "mean_stat": mc_power_streams(hon, k, tm, tv, N_MC, N_STREAMS, seed_for(3, k), True, False),
            "var_stat": mc_power_streams(hon, k, tm, tv, N_MC, N_STREAMS, seed_for(4, k), False, True),
            "both_stat": mc_power_streams(hon, k, tmS, tvS, N_MC, N_STREAMS, seed_for(5, k), True, True),
            "alpha_target": ALPHA}
    out["controls"]["C3_null"] = c3

    # C1 closed form vs MC
    c1 = []
    for delta in (0.2, 0.4, 0.8):
        for k in (4, 16, 64):
            tm, tv = thresholds(k, ALPHA)
            cf = closed_form_mean_power(k, delta, 1.0, ALPHA)
            mc = mc_power_streams(node_sampler("shift", delta=delta), k, tm, tv,
                                  N_MC, N_STREAMS, seed_for(1, k, delta), True, False)
            se = math.sqrt(max(cf * (1 - cf), 1e-12) / N_MC)
            c1.append({"mechanism": "shift", "delta": delta, "k": k,
                       "closed_form": cf, "mc_mean": mc["mean"], "mc_sd": mc["sd"],
                       "abs_diff": abs(cf - mc["mean"]), "mc_1se": se,
                       "agree_4se": abs(cf - mc["mean"]) <= 4.0 * se})
    out["controls"]["C1_agreement"] = c1

    # C2 discrimination
    #   The control asks: does the instrument distinguish "this STATISTIC cannot buy
    #   power with budget" from "this DATA is undetectable"? Both are measured on the
    #   SAME node, at the same budgets, by two statistics:
    #     mean test  -- predicted flat in k, at 1 - Phi(c_alpha / rho)  (analytic)
    #     variance test -- predicted to grow with k
    #   Note (this corrected a working assumption of mine, not a registered prior):
    #   the mean test is NOT blind to an inflating node. Its rejection rate rises
    #   ABOVE alpha because its threshold is calibrated to the honest variance; but it
    #   never exceeds 0.5 and never improves with k.
    c2 = []
    for rho in (1.2, 1.5, 2.0):
        a_pred = 1.0 - phi(phi_inv(1.0 - ALPHA) / rho)
        row = {"mechanism": "inflate", "rho": rho, "analytic_mean_power": a_pred}
        for k in (4, 64):
            tm, tv = thresholds(k, ALPHA)
            mean_p = mc_power_streams(node_sampler("inflate", rho=rho), k, tm, tv,
                                      N_MC, N_STREAMS, seed_for(2, k, rho), True, False)
            var_p = mc_power_streams(node_sampler("inflate", rho=rho), k, tm, tv,
                                     N_MC, N_STREAMS, seed_for(2, k, rho) + 7, False, True)
            row["mean_k%d" % k] = mean_p["mean"]
            row["var_k%d" % k] = var_p["mean"]
        row["mean_delta_k4_to_k64"] = abs(row["mean_k64"] - row["mean_k4"])
        row["var_delta_k4_to_k64"] = abs(row["var_k64"] - row["var_k4"])
        row["mean_flat_in_k"] = row["mean_delta_k4_to_k64"] <= 0.02
        row["var_grows_with_k"] = row["var_delta_k4_to_k64"] >= 0.10
        row["analytic_matches_mc"] = (
            abs(a_pred - row["mean_k4"]) <= 0.03 and abs(a_pred - row["mean_k64"]) <= 0.03)
        c2.append(row)
    out["controls"]["C2_discrimination"] = c2

    # C4 needle
    c4 = []
    for c in (0.0, 0.5):
        for k in (16, 64):
            tm, tv = thresholds(k, ALPHA)
            mean_p = mc_power_streams(node_sampler("collapse", c=c), k, tm, tv,
                                      N_MC, N_STREAMS, seed_for(6, k, c), True, False)
            var_p = mc_power_streams(node_sampler("collapse", c=c), k, tm, tv,
                                     N_MC, N_STREAMS, seed_for(6, k, c) + 7, False, True)
            c4.append({"mechanism": "collapse", "c": c, "k": k,
                       "mean_stat_power": mean_p["mean"], "var_stat_power": var_p["mean"]})
    out["controls"]["C4_needle"] = c4

    # budget-margin law, location-shifting node
    #   The derived boundary is k*(delta) = (c_alpha / delta)^2, i.e. k* * delta^2 = c_alpha^2.
    #   The law is a boundary, so it must be evaluated AT k*, not read off a coarse grid
    #   (a power-of-two grid overshoots k* and inflated the first estimate by ~1.9x).
    budget = {}
    c_alpha = phi_inv(1.0 - ALPHA)
    for delta in (0.1, 0.2, 0.35, 0.5):
        k_pred = (c_alpha / delta) ** 2
        cf_at = closed_form_mean_power(k_pred, delta, 1.0, ALPHA)
        k_round = max(2, int(round(k_pred)))
        tm, tv = thresholds(k_round, ALPHA)
        mc = mc_power_streams(node_sampler("shift", delta=delta), k_round, tm, tv,
                              N_MC, N_STREAMS, seed_for(11, k_round), True, False)
        budget["delta=%.2f" % delta] = {
            "k_star": k_pred,
            "closed_form_power_at_k_star": cf_at,
            "k_round": k_round,
            "mc_power_at_k_round": mc["mean"],
            "mc_sd": mc["sd"],
            "k_star_times_delta_sq": k_pred * delta * delta,
            "boundary_holds_closed_form": abs(cf_at - 0.5) <= 1e-9,
            "boundary_holds_mc": abs(mc["mean"] - 0.5) <= 0.03,
        }
    out["budget_response"]["location_shift"] = budget
    out["budget_response"]["c_alpha_sq"] = c_alpha ** 2

    band = {}
    for k in (16, 64, 256):
        lo = (c_alpha - 1.2816) / math.sqrt(k)
        hi = (c_alpha + 1.2816) / math.sqrt(k)
        band["k=%d" % k] = {"delta_lo": lo, "delta_hi": hi, "width": hi - lo,
                            "width_times_sqrt_k": (hi - lo) * math.sqrt(k)}
    out["budget_response"]["band_width"] = band
    bw = [d["width_times_sqrt_k"] for d in band.values()]
    out["budget_response"]["band_width_constant"] = max(bw) - min(bw)

    # best-responding node
    br = {}
    for k in (16, 64, 256):
        tm, tv = thresholds(k, ALPHA, split=True)
        cands = {"shift_d0.5": node_sampler("shift", delta=0.5),
                 "shift_d0.2": node_sampler("shift", delta=0.2),
                 "inflate_r2": node_sampler("inflate", rho=2.0),
                 "collapse_c0": node_sampler("collapse", c=0.0),
                 "collapse_c0.2": node_sampler("collapse", c=0.2),
                 "contam_q0.1_b3": node_sampler("contaminate", q=0.1, big=3.0),
                 "contam_q0.01_b10": node_sampler("contaminate", q=0.01, big=10.0)}
        row = {}
        for i, (name, s) in enumerate(sorted(cands.items())):
            p = mc_power_streams(s, k, tm, tv, N_MC, N_STREAMS, seed_for(9, k, i), True, True)
            row[name] = {"power": p["mean"], "sd": p["sd"]}
        best = min(row.items(), key=lambda kv: kv[1]["power"])
        br["k=%d" % k] = {"by_mechanism": row, "node_best": best[0],
                          "node_best_power": best[1]["power"]}
    out["best_responder"] = br


    # verdicts
    v = {}
    v["C1_agreement_pass"] = all(r["agree_4se"] for r in c1)
    v["C2_discrimination_pass"] = all(
        r["mean_flat_in_k"] and r["var_grows_with_k"] and r["analytic_matches_mc"]
        for r in c2)
    v["C2_cells"] = len(c2)
    v["C3_null_pass"] = all(
        abs(d["mean_stat"]["mean"] - ALPHA) <= 0.02 and
        abs(d["var_stat"]["mean"] - ALPHA) <= 0.02 and
        abs(d["both_stat"]["mean"] - ALPHA) <= 0.03
        for d in c3.values())
    c4_c0 = [r for r in c4 if r["c"] == 0.0]
    v["C4_needle_pass"] = all(r["mean_stat_power"] <= ALPHA and r["var_stat_power"] <= ALPHA
                              for r in c4_c0)
    v["C5_margin_law_pass"] = all(
        d["boundary_holds_closed_form"] and d["boundary_holds_mc"] for d in budget.values())
    v["C6_band_law_pass"] = out["budget_response"]["band_width_constant"] <= 1e-9
    v["ALL_CONTROLS_PASS"] = all([v["C1_agreement_pass"], v["C2_discrimination_pass"],
                                  v["C3_null_pass"], v["C4_needle_pass"],
                                  v["C5_margin_law_pass"], v["C6_band_law_pass"]])
    out["verdicts"] = v
    return out


def main():
    out = run()
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "results_v0.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("wrote", dest)
    print("VERDICTS:", json.dumps(out["verdicts"], indent=2))
    print()
    print("C2 discrimination (same node, two statistics; alpha=%.2f):" % ALPHA)
    for r in out["controls"]["C2_discrimination"]:
        print("  rho=%.1f analytic_mean=%.4f | mean k4=%.4f k64=%.4f (d=%.4f flat=%s)"
              % (r["rho"], r["analytic_mean_power"], r["mean_k4"], r["mean_k64"],
                 r["mean_delta_k4_to_k64"], r["mean_flat_in_k"]))
        print("        var  k4=%.4f k64=%.4f (d=%.4f grows=%s)"
              % (r["var_k4"], r["var_k64"], r["var_delta_k4_to_k64"], r["var_grows_with_k"]))
    print()
    print("C4 needle (collapse / replay-style node):")
    for r in out["controls"]["C4_needle"]:
        print("  c=%.1f k=%-3d mean_stat=%.4f var_stat=%.4f" % (r["c"], r["k"],
              r["mean_stat_power"], r["var_stat_power"]))
    print()
    print("budget-margin boundary k* = (c_alpha/delta)^2, c_alpha^2=%.4f"
          % out["budget_response"]["c_alpha_sq"])
    for name, d in sorted(out["budget_response"]["location_shift"].items()):
        print("  %-10s k*=%7.2f  cf_power(k*)=%.6f  mc(k=%d)=%.4f  k**delta^2=%.4f"
              % (name, d["k_star"], d["closed_form_power_at_k_star"], d["k_round"],
                 d["mc_power_at_k_round"], d["k_star_times_delta_sq"]))
    print()
    print("band width ~ 1/sqrt(k):")
    for name, d in sorted(out["budget_response"]["band_width"].items(),
                          key=lambda kv: int(kv[0].split("=")[1])):
        print("  %-8s width=%.4f  width*sqrt(k)=%.4f"
              % (name, d["width"], d["width_times_sqrt_k"]))
    print()
    print("best-responding node (verifier tests both moments, alpha/2 each):")
    for name, d in sorted(out["best_responder"].items(), key=lambda kv: int(kv[0].split("=")[1])):
        print("  %-8s node_best=%-16s power=%.4f" % (name, d["node_best"], d["node_best_power"]))


if __name__ == "__main__":
    main()
