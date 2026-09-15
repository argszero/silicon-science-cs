#!/usr/bin/env python3
"""Issue #42 v0 -- the model skeleton and its by-construction reductions.

Construct under study: the RESIDUAL CATCH PROFILE of a supervision layer. A layer L2
added after L1 is characterised not by its standalone catch rate C2 but by where its
catches fall: q_res = P(catch | L1 missed the error), q_red = P(catch | L1 already
caught it). Their split is the quantity a budget decision turns on.

Parameterisation (the redundancy dial beta, feasible everywhere and accuracy-invariant):
    f      = P(L1 catches a given error)                    (L1's catch rate)
    C2     = L2's standalone catch rate, held fixed
    q_red  = beta * C2 / f                                  (catches that re-catch)
    q_res  = (1 - beta) * C2 / (1 - f)                      (catches that are new)
Then for EVERY beta in [0, 1]:
    f*q_red + (1-f)*q_res = beta*C2 + (1-beta)*C2 = C2      [standalone accuracy fixed]
    beta = 1  ->  q_res = 0    : perfectly aligned, marginal catch exactly 0
    beta = 0  ->  q_red = 0    : perfectly complementary, all catches are new
    beta = f  ->  q_res = q_red = C2 : exact independence (the classical assumption)
so beta is a dial that moves WHERE the catches fall while holding HOW MANY fixed, and the
classical independence assumption is the single point beta = f, not a generic regime.

A first attempt used the symmetric pair q_red = C2 + alpha*s*(1-f), q_res = C2 - alpha*s*f.
It is infeasible at the extremes: with C2 = 0.15, f = 0.3 the "perfectly aligned" endpoint
needs q_res = -0.15, and the simulator silently clipped it at 0, which BROKE the
accuracy-invariance identity (measured C2_hat = 0.2556 against a target of 0.150). The
failure was caught by the reduction that asserts the identity -- which is why the identity
is asserted here rather than assumed. The dial above is feasible for all beta whenever
C2 <= min(f, 1-f).

Ground truth by construction: per-item catch outcomes are drawn from these known rates.
v0 asserts the reductions only; it makes no claim about the world.
"""
import json
import numpy as np

SEED0 = 20260913


def rates(C2, f, beta):
    return beta * C2 / f, (1.0 - beta) * C2 / (1.0 - f)


def simulate(n, p0, c1, C2, beta, seed):
    rng = np.random.default_rng(seed)
    bad = rng.random(n) < p0
    caught1 = bad & (rng.random(n) < c1)
    q_red, q_res = rates(C2, c1, beta)
    u = np.random.default_rng(seed + 977).random(n)
    caught2 = bad & (u < np.where(caught1, q_red, q_res))
    return {"bad": bad, "caught1": caught1, "caught2": caught2, "q_red": q_red, "q_res": q_res}


def stats(r):
    bad, c1, c2 = r["bad"], r["caught1"], r["caught2"]
    nbad = max(1, int(bad.sum()))
    miss1, red1 = bad & ~c1, c1 & bad
    q_res = (c2 & miss1).sum() / miss1.sum() if miss1.sum() else float("nan")
    q_red = (c2 & red1).sum() / red1.sum() if red1.sum() else float("nan")
    return {
        "n_bad": int(bad.sum()),
        "f_hat": float(c1.sum() / nbad),
        "C2_hat": float(c2.sum() / nbad),
        "q_res_hat": float(q_res), "q_red_hat": float(q_red),
        "alpha_hat": float(q_red - q_res),
        "err_after_L1": float((bad & ~c1).sum() / nbad),
        "err_after_both": float((bad & ~(c1 | c2)).sum() / nbad),
        "marginal_catch": float(((bad & ~c1) & c2).sum() / nbad),
    }


def main():
    out = {"seed0": SEED0, "checks": []}
    def check(name, cond, detail=""):
        out["checks"].append({"name": name, "pass": bool(cond), "detail": detail})

    n, p0, f, C2 = 400_000, 0.20, 0.30, 0.15     # C2 <= min(f, 1-f) holds

    # R1 -- accuracy invariance: the dial must not move L2's standalone catch rate
    sweep = []
    for beta in (0.0, 0.3, 0.6, 1.0):
        r = simulate(n, p0, f, C2, beta, SEED0)
        s = stats(r)
        sweep.append({"beta": beta, **{k: round(v, 6) for k, v in s.items()}})
        check("R1_accuracy_invariant_beta=%.1f" % beta, abs(s["C2_hat"] - C2) < 4e-3,
              "C2_hat=%.4f target=%.3f" % (s["C2_hat"], C2))
        check("R1_rates_match_parameterisation_beta=%.1f" % beta,
              abs(s["q_red_hat"] - r["q_red"]) < 8e-3 and abs(s["q_res_hat"] - r["q_res"]) < 8e-3,
              "q_red_hat=%.4f(%.4f) q_res_hat=%.4f(%.4f)"
              % (s["q_red_hat"], r["q_red"], s["q_res_hat"], r["q_res"]))
    out["beta_sweep"] = sweep

    # R2 -- the aligned endpoint has EXACTLY zero marginal catch
    r = simulate(n, p0, f, C2, 1.0, SEED0); s = stats(r)
    check("R2_aligned_q_res_exactly_zero", abs(r["q_res"]) < 1e-12, "q_res=%.3g" % r["q_res"])
    check("R2_aligned_marginal_catch_zero", s["marginal_catch"] == 0.0,
          "marginal_catch=%.3g" % s["marginal_catch"])

    # R3 -- the complementary endpoint re-catches nothing
    r = simulate(n, p0, f, C2, 0.0, SEED0); s = stats(r)
    check("R3_complementary_q_red_exactly_zero", abs(r["q_red"]) < 1e-12, "q_red=%.3g" % r["q_red"])
    check("R3_complementary_q_res", abs(s["q_res_hat"] - C2 / (1 - f)) < 6e-3,
          "q_res_hat=%.4f target=%.4f" % (s["q_res_hat"], C2 / (1 - f)))

    # R4 -- beta = f is exactly the classical independence assumption
    s = stats(simulate(n, p0, f, C2, f, SEED0))
    check("R4_beta_equals_f_is_independence",
          abs(s["q_res_hat"] - C2) < 6e-3 and abs(s["q_red_hat"] - C2) < 6e-3
          and abs(s["alpha_hat"]) < 0.02,
          "q_res=%.4f q_red=%.4f alpha=%.4f (C2=%.3f)" % (s["q_res_hat"], s["q_red_hat"],
                                                          s["alpha_hat"], C2))

    # R5 -- degenerate layers
    s0 = stats(simulate(n, p0, f, 0.0, 0.0, SEED0))
    check("R5_zero_catch_layer_inert", abs(s0["err_after_both"] - s0["err_after_L1"]) < 1e-9,
          "delta=%.3g" % (s0["err_after_both"] - s0["err_after_L1"]))
    check("R5_layer_never_increases_error", sweep[0]["err_after_both"] <= sweep[0]["err_after_L1"] + 1e-9,
          "after_L1=%.6f after_both=%.6f" % (sweep[0]["err_after_L1"], sweep[0]["err_after_both"]))
    # marginal catch must be monotone DECREASING in beta (more redundancy, less new catch)
    mc = [row["marginal_catch"] for row in sweep]
    check("R5_marginal_catch_decreasing_in_beta", all(mc[i] > mc[i + 1] for i in range(len(mc) - 1)), mc)

    # R6 -- the estimator recovers alpha from logs, incl. the independence control
    rec = []
    for beta in (0.0, f, 1.0):
        got = [stats(simulate(60_000, p0, f, C2, beta, SEED0 + 1000 * k))["alpha_hat"] for k in range(12)]
        true_alpha = rates(C2, f, beta)[0] - rates(C2, f, beta)[1]
        rec.append({"beta": beta, "alpha_true": round(true_alpha, 6),
                    "alpha_hat_mean": float(np.mean(got)), "alpha_hat_sd": float(np.std(got, ddof=1))})
        check("R6_estimator_recovers_alpha_beta=%.2f" % beta,
              abs(np.mean(got) - true_alpha) < 4 * np.std(got, ddof=1) / np.sqrt(len(got)) + 0.02,
              "mean=%.4f true=%.4f sd=%.4f" % (np.mean(got), true_alpha, np.std(got, ddof=1)))
    out["estimator_recovery"] = rec

    npass = sum(1 for c in out["checks"] if c["pass"])
    out["summary"] = {"n_checks": len(out["checks"]), "n_pass": npass,
                      "all_pass": npass == len(out["checks"])}
    with open("results_v0.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for c in out["checks"]:
        print("  [%s] %-46s %s" % ("ok" if c["pass"] else "FAIL", c["name"], c["detail"]))
    print("REDUCTIONS %d/%d" % (npass, len(out["checks"])))
    return 0 if npass == len(out["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
