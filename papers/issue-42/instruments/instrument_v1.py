#!/usr/bin/env python3
"""Issue #42 v1 -- the marginal-value surface and the inversion's dominance region.

ANALYTIC CORE (exact by construction, then verified by simulation).
A layer L2 with standalone catch rate C2 and redundancy dial beta, added after a primary
layer with catch rate f, removes exactly

    marginal_catch = p0 * (1 - beta) * C2          (per covered item)

because the residual pool left by the primary is p0*(1-f) and the layer's catch rate on
that pool is q_res = (1-beta)*C2/(1-f), so the product cancels f. Two consequences are
tested here rather than assumed:

  (i)  a layer's marginal value is a ONE-SCALAR product of its own accuracy and its
       decorrelation: neither the task error rate p0 nor the primary strength f enters it;
  (ii) the decision "add the layer" compares that product against what the SAME BUDGET
       buys elsewhere: a stronger primary, or wider coverage.

THE COST MODEL (stated, not hidden)
    h(x) = -log(1-x)                 cost of reaching catch rate x per item, convex
    primary: catch f, covers cov, costs kappa1*h(f)*cov
    layer:   catch C2, costs kappa2*h(C2)*cov        (this is the budget B1)
    A: add the layer         value_A = p0*(1-beta)*C2*cov
    B: same budget raises f  h(f2) = h(f) + r*h(C2)  where r = kappa2/kappa1
                             value_B = p0*cov*(f2 - f)
    C: same budget widens cov  d_cov = r*h(C2)*cov/h(f), capped at the uncovered share
                             value_C = p0*(1-f)*d_cov
    N: nothing               value_N = 0
Only r matters, and neither p0 nor cov enters the A-versus-B boundary; that is what makes
a one-scalar law possible. Whether ONE scalar suffices against BOTH alternatives is the
empirical question this file answers.

OPERATIONAL POINT: q_res is directly observable in a log (both layers' outcomes on the
same items), so the decision needs q_res and (1-f), not beta. The last section measures
the regret of deciding from a finite log instead of the true parameters.
"""
import io
import json

import numpy as np

SEED0 = 20260914
def h(x):
    return -np.log(1.0 - np.asarray(x, dtype=float))


def marginal_catch(p0, C2, beta):
    """Per covered item. Exact: p0*(1-f)*q_res with q_res=(1-beta)*C2/(1-f)."""
    return p0 * (1.0 - beta) * C2


def f_after_primary_investment(f, r, C2):
    """Catch rate the primary reaches if the layer's budget is spent on the primary."""
    return 1.0 - np.exp(-(h(f) + r * h(C2)))


def d_cov_from_budget(f, r, C2, cov):
    return min(1.0 - cov, r * h(C2) * cov / h(f))


def values(p0, f, cov, C2, beta, r):
    vA = p0 * (1.0 - beta) * C2 * cov
    f2 = f_after_primary_investment(f, r, C2)
    vB = p0 * cov * (f2 - f)
    vC = p0 * (1.0 - f) * d_cov_from_budget(f, r, C2, cov)
    return {"A": float(vA), "B": float(vB), "C": float(vC), "N": 0.0}


def best_action(v):
    return max(v, key=lambda k: (v[k], k == "A"))


# ------------------------------------------------------------------ simulation
def simulate(n, p0, f, C2, beta, seed):
    rng = np.random.default_rng(seed)
    bad = rng.random(n) < p0
    caught1 = bad & (rng.random(n) < f)
    q_red = beta * C2 / f
    q_res = (1.0 - beta) * C2 / (1.0 - f)
    u = rng.random(n)
    caught2 = bad & (u < np.where(caught1, q_red, q_res))
    return {"bad": bad, "caught1": caught1, "caught2": caught2}


FAMILIES = {
    "F1_easy_weak": (0.05, 0.25),
    "F2_easy_strong": (0.05, 0.60),
    "F3_hard_weak": (0.30, 0.25),
    "F4_hard_strong": (0.30, 0.60),
}
COV = 0.7
BETAS = (0.0, 0.25, 0.5, 0.75, 1.0)
C2S = (0.05, 0.10, 0.20, 0.35, 0.50)
RS = (0.25, 1.0, 4.0)
P2_MIN_FRACTION = 0.20
P2_MIN_FAMILIES = 3


def main():
    out = {"seed0": SEED0, "checks": [], "config": {"families": FAMILIES, "cov": COV,
           "betas": BETAS, "C2s": C2S, "rs": RS}}
    chk = []

    def check(name, cond, detail=""):
        chk.append({"name": name, "pass": bool(cond), "detail": detail})

    # C1 -- the analytic marginal catch is what the simulator does
    n = 200_000
    sim_rows = []
    for beta in (0.0, 0.25, 0.5, 0.75, 1.0):
        obs = []
        for k in range(20):
            r = simulate(n, 0.20, 0.30, 0.15, beta, SEED0 + 101 * k)
            obs.append(float(((r["bad"] & ~r["caught1"]) & r["caught2"]).sum() / n))
        pred = float(marginal_catch(0.20, 0.15, beta))
        mu, sd = float(np.mean(obs)), float(np.std(obs, ddof=1))
        sim_rows.append({"beta": beta, "predicted": pred, "observed_mean": mu,
                         "observed_sd": sd, "n_seeds": len(obs)})
        check("C1_marginal_catch_matches_sim_beta=%.2f" % beta, abs(mu - pred) < 4 * sd + 2e-4,
              "obs=%.5f pred=%.5f sd=%.5f" % (mu, pred, sd))
    out["marginal_catch_verification"] = sim_rows

    # C2 -- the product is scale-free in p0 and f (the claim that makes a law possible)
    grid_vals = []
    for p0 in (0.02, 0.05, 0.30, 0.60):
        for f in (0.10, 0.25, 0.60, 0.90):
            grid_vals.append(float(marginal_catch(p0, 0.20, 0.25) / (p0 * 0.75 * 0.20)))
    check("C2_product_is_scale_free_in_p0_and_f", all(abs(v - 1.0) < 1e-12 for v in grid_vals),
          "max deviation %.2g" % max(abs(v - 1.0) for v in grid_vals))

    # C3 -- the A-versus-B boundary does not depend on the task error rate p0 nor on how
    # many items are covered, HOLDING the primary strength f fixed. (The earlier form of
    # this check varied f across families and failed, which is correct: f does enter the
    # boundary. Only p0 and coverage must fall out, and that is what is tested here.)
    by_p0cov = {}
    for p0 in (0.02, 0.30, 0.60):
        for cov in (0.4, 0.7, 1.0):
            for r in RS:
                for C2 in C2S:
                    v = values(p0, 0.40, cov, C2, 0.5, r)
                    by_p0cov.setdefault((r, C2), set()).add(v["A"] > v["B"])
    bad_cells = [k for k, st in by_p0cov.items() if len(st) != 1]
    check("C3_AB_boundary_independent_of_p0_and_coverage", not bad_cells,
          "%d of %d cells vary with p0 or coverage" % (len(bad_cells), len(by_p0cov)))

    # ---- the surface over the parameter grid, per regime family
    surface = {}
    for fam, (p0, f) in FAMILIES.items():
        cells = []
        for beta in BETAS:
            for C2 in C2S:
                for r in RS:
                    v = values(p0, f, COV, C2, beta, r)
                    cells.append({"beta": beta, "C2": C2, "r": r, "values": v,
                                  "A_beats_B": v["A"] > v["B"], "A_beats_C": v["A"] > v["C"],
                                  "A_beats_both": v["A"] > v["B"] and v["A"] > v["C"],
                                  "A_beats_max": v["A"] > max(v["B"], v["C"])})
        ncell = len(cells)
        surface[fam] = {
            "p0": p0, "f": f, "cells": ncell,
            "frac_A_beats_B": float(np.mean([c["A_beats_B"] for c in cells])),
            "frac_A_beats_C": float(np.mean([c["A_beats_C"] for c in cells])),
            "frac_A_beats_both": float(np.mean([c["A_beats_both"] for c in cells])),
            "cells": cells,
        }
    out["surface"] = surface

    # C4 -- the LAYER-ADDITION dominance region is not uniform in the primary's strength:
    # a weak primary has more headroom, so the same budget buys more there and the layer
    # more rarely wins. This is a measurement, not a criterion: the registered P2 criterion
    # is about the INVERSION (C5), which is a different comparison.
    strong = {f: surface[f]["frac_A_beats_both"] for f in ("F2_easy_strong", "F4_hard_strong")}
    weak = {f: surface[f]["frac_A_beats_both"] for f in ("F1_easy_weak", "F3_hard_weak")}
    check("C4_layer_dominance_confined_to_strong_primaries",
          min(strong.values()) > max(weak.values()) and min(strong.values()) > 0.2,
          {"strong": {k: round(v, 3) for k, v in strong.items()},
           "weak": {k: round(v, 3) for k, v in weak.items()}})

    # ---- the inversion: a lower-accuracy decorrelated layer against a higher-accuracy
    # aligned one, at EQUAL COST. Cost is kappa*h(C), so equal cost fixes the accuracy gap:
    # only a layer that is CHEAPER PER UNIT OF HAZARD (rk < 1) reaches a lower accuracy for
    # the same money. A tolerance is mandatory here -- with rk = 1 the two accuracies are
    # equal to within 1e-16, and an exact comparison leaked 50 equal-accuracy pairs into the
    # "strictly lower accuracy" set on floating-point noise alone (150 live cells instead of
    # 100, and a reported inversion fraction of 0.78 instead of 0.32). The guard below is the
    # check that would have caught it, and it is kept.
    EQ_TOL = 1e-9
    inversion = {}
    for fam, (p0, f) in FAMILIES.items():
        cells = []
        for C_hi in (0.10, 0.20, 0.35, 0.50):
            for rk in (0.5, 1.0, 2.0, 4.0):
                C_lo = 1.0 - np.exp(-(rk * h(C_hi)))
                for b_hi in (0.0, 0.25, 0.5, 0.75, 1.0):
                    for b_lo in (0.0, 0.25, 0.5, 0.75, 1.0):
                        cells.append({"C_hi": C_hi, "C_lo": float(C_lo), "rk": rk,
                                      "beta_hi": b_hi, "beta_lo": b_lo,
                                      "strictly_lower": bool(C_lo < C_hi - EQ_TOL),
                                      "equal_accuracy": bool(abs(C_lo - C_hi) <= EQ_TOL),
                                      "inversion": bool((1.0 - b_lo) * C_lo >
                                                        (1.0 - b_hi) * C_hi)})
        live = [c for c in cells if c["strictly_lower"]]
        inversion[fam] = {
            "live_cells": len(live),
            "equal_accuracy_cells": sum(1 for c in cells if c["equal_accuracy"]),
            "equal_accuracy_in_live": sum(1 for c in live if c["equal_accuracy"]),
            "frac_inversion": float(np.mean([c["inversion"] for c in live])),
            "n_inversion": int(sum(c["inversion"] for c in live)),
            "rk_with_inversions": sorted({c["rk"] for c in live if c["inversion"]}),
            "rk_in_live": sorted({c["rk"] for c in live}),
        }
    out["inversion"] = inversion
    inv_fams = [f for f, s in inversion.items() if s["frac_inversion"] >= P2_MIN_FRACTION]
    check("C5_inversion_region_at_least_3_of_4_families", len(inv_fams) >= P2_MIN_FAMILIES,
          {k: round(v["frac_inversion"], 4) for k, v in inversion.items()})
    check("C5b_no_equal_accuracy_pair_leaks_into_the_region",
          all(s["equal_accuracy_in_live"] == 0 and s["equal_accuracy_cells"] > 0
              for s in inversion.values()),
          {k: (v["equal_accuracy_cells"], v["equal_accuracy_in_live"])
           for k, v in inversion.items()})
    check("C5c_the_inversion_requires_a_cheaper_per_hazard_layer",
          all(s["rk_with_inversions"] == [0.5] and s["rk_in_live"] == [0.5]
              for s in inversion.values()),
          {k: v["rk_with_inversions"] for k, v in inversion.items()})

    # C6 -- the inversion is NOT an artefact of the degenerate fully-aligned endpoint: the
    # comparison is restricted to pairs where BOTH alignments are interior and the
    # decorrelated one is genuinely more decorrelated
    inv_nondeg = {}
    for fam, (p0, f) in FAMILIES.items():
        cells = []
        for C_hi in (0.10, 0.20, 0.35, 0.50):
            for rk in (0.5, 1.0, 2.0, 4.0):
                C_lo = 1.0 - np.exp(-(rk * h(C_hi)))
                if not C_lo < C_hi - EQ_TOL:
                    continue
                for b_hi in (0.25, 0.5, 0.75):
                    for b_lo in (0.0, 0.25, 0.5, 0.75):
                        if b_lo < b_hi and b_lo > 0.0:
                            cells.append((1.0 - b_lo) * C_lo > (1.0 - b_hi) * C_hi)
        inv_nondeg[fam] = float(np.mean(cells)) if cells else 0.0
    out["inversion_non_degenerate_baseline"] = inv_nondeg
    check("C6_inversion_survives_non_degenerate_alignment",
          all(v >= P2_MIN_FRACTION for v in inv_nondeg.values()),
          {k: round(v, 4) for k, v in inv_nondeg.items()})

    # ---- decision rules: the analytic rule against four baselines
    rules = {"analytic": "A iff value_A beats B and C",
             "accuracy_ordered": "pick the candidate with the highest standalone C2",
             "primary_only": "always B",
             "coverage_first": "always C",
             "equal_split": "half the budget to the primary, half to a halved layer",
             "random": "uniform over A, B, C"}

    def rule_choice(rule, p0, f, cov, C2, beta, r, rng=None):
        v = values(p0, f, cov, C2, beta, r)
        if rule == "analytic":
            return best_action(v)
        if rule == "primary_only":
            return "B"
        if rule == "coverage_first":
            return "C"
        if rule == "accuracy_ordered":
            return "A" if C2 >= 0.10 else "B"
        if rule == "equal_split":
            return "B" if v["B"] > v["A"] * 0.5 else "A"
        if rule == "random":
            return ("A", "B", "C")[int(rng.integers(0, 3))]
        raise ValueError(rule)

    regret = {}
    rng = np.random.default_rng(SEED0)
    for rule in rules:
        vals, chosen_vals, opt_vals = [], [], []
        for fam, (p0, f) in FAMILIES.items():
            for beta in BETAS:
                for C2 in C2S:
                    for r in RS:
                        v = values(p0, f, COV, C2, beta, r)
                        opt = max(v.values())
                        ch = rule_choice(rule, p0, f, COV, C2, beta, r, rng)
                        vals.append((opt - v[ch]) / opt if opt > 0 else 0.0)
                        chosen_vals.append(v[ch])
                        opt_vals.append(opt)
        regret[rule] = {"mean_rel_regret": float(np.mean(vals)),
                        "max_rel_regret": float(np.max(vals)),
                        "n_cells": len(vals),
                        "mean_value_ratio": float(np.mean(np.array(chosen_vals) /
                                                          np.maximum(np.array(opt_vals), 1e-12)))}
    out["regret"] = regret
    check("C7_analytic_rule_is_zero_regret", regret["analytic"]["max_rel_regret"] < 1e-12,
          "max regret %.3g" % regret["analytic"]["max_rel_regret"])
    check("C8_single_scalar_rule_beats_every_baseline",
          regret["analytic"]["mean_value_ratio"] > max(
              regret[b]["mean_value_ratio"] for b in rules if b != "analytic"),
          {k: round(v["mean_value_ratio"], 4) for k, v in regret.items()})

    # C9 -- IS THE THRESHOLD ONE SCALAR? The driver can be one scalar (the residual-catch
    # product), but the boundary it must clear is f2-f, which depends on the cost ratio r
    # and on the primary's budget-response curve. Three laws are therefore raced out of
    # sample (fit on the easy families, scored on the hard ones):
    #   L1 scalar       one constant threshold on the product
    #   L2 by_r         a threshold per cost ratio r
    #   L3 operational  the product against the primary's own budget response f2-f
    law_rows = []
    for fam, (p0, f) in FAMILIES.items():
        for beta in BETAS:
            for C2 in C2S:
                for r in RS:
                    prod = (1.0 - beta) * C2
                    v = values(p0, f, COV, C2, beta, r)
                    law_rows.append({"fam": fam, "f": f, "r": r, "C2": C2, "beta": beta,
                                     "prod": prod, "boundary": f_after_primary_investment(f, r, C2) - f,
                                     "beats_B": v["A"] > v["B"], "beats_C": v["A"] > v["C"]})
    fit = [x for x in law_rows if x["fam"] in ("F1_easy_weak", "F2_easy_strong")]
    hold = [x for x in law_rows if x["fam"] not in ("F1_easy_weak", "F2_easy_strong")]

    def best_threshold(rows, key=lambda x: x["prod"]):
        bt, be = None, None
        for t in np.linspace(0.0, 0.60, 1201):
            err = np.mean([(key(x) > t) != (x["beats_B"] and x["beats_C"]) for x in rows])
            if be is None or err < be:
                bt, be = float(t), float(err)
        return bt, be

    t_scalar, fit_err_scalar = best_threshold(fit)
    err = {}
    err["L1_scalar_vs_both"] = float(np.mean(
        [(x["prod"] > t_scalar) != (x["beats_B"] and x["beats_C"]) for x in hold]))
    err["L1_scalar_vs_primary"] = float(np.mean(
        [(x["prod"] > t_scalar) != x["beats_B"] for x in hold]))
    t_by_r = {}
    for r in RS:
        t_by_r[str(r)] = best_threshold([x for x in fit if x["r"] == r])[0]
    err["L2_by_r_vs_both"] = float(np.mean(
        [(x["prod"] > t_by_r[str(x["r"])]) != (x["beats_B"] and x["beats_C"]) for x in hold]))
    err["L2_by_r_vs_primary"] = float(np.mean(
        [(x["prod"] > t_by_r[str(x["r"])]) != x["beats_B"] for x in hold]))
    err["L3_operational_vs_both"] = float(np.mean(
        [(x["prod"] > x["boundary"]) != (x["beats_B"] and x["beats_C"]) for x in hold]))
    err["L3_operational_vs_primary"] = float(np.mean(
        [(x["prod"] > x["boundary"]) != x["beats_B"] for x in hold]))
    out["law_races"] = {"threshold_scalar": t_scalar, "threshold_by_r": t_by_r,
                        "fit_error_scalar": fit_err_scalar, "oos_errors": err,
                        "n_fit": len(fit), "n_oos": len(hold)}
    check("C9_the_residual_product_is_the_driver_but_the_threshold_is_not_one_scalar",
          err["L1_scalar_vs_primary"] > 0.05 and err["L3_operational_vs_primary"] < 1e-12,
          {"scalar_oos_vs_primary": round(err["L1_scalar_vs_primary"], 4),
           "by_r_oos_vs_primary": round(err["L2_by_r_vs_primary"], 4),
           "operational_oos_vs_primary": round(err["L3_operational_vs_primary"], 4)})
    check("C9b_indexing_the_threshold_by_cost_ratio_improves_oos",
          err["L2_by_r_vs_both"] < err["L1_scalar_vs_both"],
          {"scalar_vs_both": round(err["L1_scalar_vs_both"], 4),
           "by_r_vs_both": round(err["L2_by_r_vs_both"], 4)})

    # C10 -- deciding from a FINITE LOG. q_res is directly observable in a log (both
    # layers' outcomes on the same items), so the rule needs q_res and f, not beta. The
    # cells are chosen to include two far from the boundary and one ON it, because a rule
    # that is right only where the answer is obvious would not evidence anything.
    cells = [("deep_A", 0.30, 0.0, 0.25), ("deep_B", 0.05, 1.0, 4.0), ("near_tie", 0.20, 0.5, 1.0)]
    log_rows = []
    for n_log in (2_000, 20_000):
        for name, C2, beta, r in cells:
            agree, regrets = [], []
            for fam, (p0, f) in FAMILIES.items():
                for k in range(20):
                    sim = simulate(n_log, p0, f, C2, beta, SEED0 + 7919 * k)
                    miss = sim["bad"] & ~sim["caught1"]
                    q_res_hat = float((sim["caught2"] & miss).sum() / max(1, int(miss.sum())))
                    if f <= 0.0 or f >= 1.0:
                        continue
                    f_hat = float(sim["caught1"].sum() / max(1, int(sim["bad"].sum())))
                    true = values(p0, f, COV, C2, beta, r)
                    est = {"A": p0 * COV * (1.0 - f_hat) * q_res_hat, "B": true["B"],
                           "C": true["C"], "N": 0.0}
                    opt = max(true.values())
                    ch_est = best_action(est)
                    agree.append(best_action(true) == ch_est)
                    regrets.append((opt - true[ch_est]) / opt if opt > 0 else 0.0)
            log_rows.append({"n_log": n_log, "cell": name, "C2": C2, "beta": beta, "r": r,
                             "n_seeds": len(agree),
                             "decision_agreement": float(np.mean(agree)),
                             "mean_rel_regret": float(np.mean(regrets))})
    out["finite_log_decision"] = log_rows
    far = [x["decision_agreement"] for x in log_rows
           if x["n_log"] == 20_000 and x["cell"] != "near_tie"]
    near = [x["decision_agreement"] for x in log_rows
            if x["n_log"] == 20_000 and x["cell"] == "near_tie"]
    check("C10_a_finite_log_decides_the_unambiguous_cells",
          min(far) >= 0.75, {"far_cells_at_20k": [round(v, 3) for v in far]})
    check("C10b_the_near_tie_is_not_claimed_decidable", max(near) < 1.0,
          {"near_tie_at_20k": [round(v, 3) for v in near]})

    out["checks"] = chk
    npass = sum(1 for c in chk if c["pass"])
    out["summary"] = {"n_checks": len(chk), "n_pass": npass, "all_pass": npass == len(chk),
                      # P2's registered criterion is about the INVERSION (C5/C6), not about
                      # the layer-addition surface (C4): they are different comparisons.
                      "P2_inversion_families_above_threshold": sorted(inv_fams),
                      "P2_inversion_criterion_met": len(inv_fams) >= P2_MIN_FAMILIES,
                      "P3_scalar_law_oos_error": out["law_races"]["oos_errors"]}
    with io.open("results_v1.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for c in chk:
        print("  [%s] %-52s %s" % ("ok" if c["pass"] else "FAIL", c["name"], c["detail"]))
    print("CHECKS %d/%d" % (npass, len(chk)))
    return 0 if npass == len(chk) else 1


if __name__ == "__main__":
    raise SystemExit(main())
