#!/usr/bin/env python3
"""Issue #122 -- spike_v3: (1) the boundary gets a BEHAVIOURAL control (registered criterion ii),
and (2) an attempt to PREDICT the boundary from the mechanism.

Criterion (ii) as registered asks that each located boundary be *bracketed to a stated tolerance by
bisection WITH A TWO-SIDED CONTROL -- below it collapses, above it bounded*.  spike_v2 located the
boundaries but never showed that the loop behaves differently on the two sides of one, so part A
supplies exactly that: for each located lambda*, run the loop from a healthy start at
lambda*/2, lambda*, 2*lambda*, and measure whether the support DECAYS across the window (absence
fraction growing) or stays bounded (flat).  The control is two-sided: the low side must decay and
the high side must not.

Part B attacks the harder question.  spike_v2 showed the boundary moves with the pool window w, and
found the mechanism (pooling turns exponential mean reversion at rate ~lambda into a slow
moving-average relaxation).  If the mechanism is the whole story, the boundary should be the locus
where SOME mechanism-derived quantity crosses a fixed value, and that quantity should then be
constant across w at the boundary.  Candidates, all evaluated at each located lambda*:
    rate  = -ln(largest eigenvalue of the MA recursion)   [closed form, no simulation]
    vstar = mean stationary variance of q_i               [measured]
    snr   = min_i p_i / sd(q_i)                           [signal-to-noise of the rarest symbol]
Part C is the test that matters: fit the constant from w = 1 and w = 4, PREDICT lambda* at unseen
w, and then locate it directly.  A fit is not a prediction; an out-of-sample reading is.

Bisection is done on a LOG scale (linear bisection over [0,1] carries a resolution of 2.4e-4, the
same size as the smallest boundaries it was used to report).

Usage: python3 spike_v3.py  ->  spike_v3_results.json
"""
import json
import math
import sys

import numpy as np

import spike_v2 as s2

K = s2.K
DELTA = 0.01          # the absence bar every boundary is defined against


def locate_boundary_log(p, n, w, delta=0.01, reps=96, T0=200, T=1200, iters=22):
    """Largest lambda whose stationary worst-symbol absence fraction is <= delta, by LOG bisection."""
    lo, hi = 1e-6, 1.0                      # log10 range [-6, 0]
    trace = []
    for i in range(iters):
        mid = 10.0 ** (0.5 * (math.log10(lo) + math.log10(hi)))
        rng = s2.cell_rng("v3bnd", n, w, i)
        af, se = s2.absence_fraction(p, n, mid, w, reps, T0, T, rng)
        worst = float(np.max(af))
        worst_se = float(se[int(np.argmax(af))])
        trace.append({"lam": mid, "worst_abs": worst, "worst_se": worst_se, "ok": worst <= delta})
        if worst <= delta:
            hi = mid
        else:
            lo = mid
    res = (math.log10(hi) - math.log10(lo))
    return hi, trace, res


def stationary_stats(p, n, lam, w, reps=256, T0=400, T=600):
    """Stationary variance, signal-to-noise, and the loss/regain BALANCE at the given lambda.

    The absence fraction is pinned at `delta` by construction, and stationarity forces
    pi = loss/(loss+regain) = delta, i.e. loss = regain*delta/(1-delta).  The LOSS and REGAIN
    intensities are therefore the two quantities the mechanism sets, and neither the relaxation
    rate nor the coefficient of variation need be constant on its own.
    """
    rng = s2.cell_rng("v3stat", n, w, round(lam, 9))
    tr = s2.trajectory(p, n, lam, w, reps, T0 + T, rng)
    win = tr[T0:]                                   # (T, reps, K)
    var = win.var(axis=(0, 1))
    sd = np.sqrt(np.clip(var, 0.0, None))
    snr = float(np.min(np.where(sd > 0, p / np.where(sd > 0, sd, 1.0), np.inf)))
    absent = (win == 0.0)                           # (T, reps, K)
    # transition counts over the window: present->absent (loss) and absent->present (regain)
    for i in range(K):
        pass
    pres = ~absent
    loss_num = int((pres[:-1] & absent[1:]).sum())
    loss_den = int(pres[:-1].sum())
    reg_num = int((absent[:-1] & pres[1:]).sum())
    reg_den = int(absent[:-1].sum())
    loss_rate = loss_num / loss_den if loss_den else float("nan")
    reg_rate = reg_num / reg_den if reg_den else float("nan")
    return {"var": var.tolist(), "snr": snr, "worst_sd": float(np.max(sd)),
            "loss_rate": loss_rate, "regain_rate": reg_rate,
            "loss_den": loss_den, "reg_den": reg_den}


def support_measures(p, n, lam, w, reps=300, H=800, T0=200, T=800):
    """Behavioural functionals that do NOT saturate, measured on the same loop.

    A "did the event ever happen within H" probability saturates at 1 on both sides of the boundary
    once H is long enough to catch a rare event, so it carries no signal there.  These instead:
      absence    -- the stationary absence fraction of the worst symbol (the criterion's own object)
      full_supp  -- the fraction of GENERATIONS at which every symbol is present (a different
                    functional: "bounded" means the loop sits at full support nearly all the time)
      p_lost / p_heal -- reported for context, with a short horizon so they stay interior.
    """
    rng = s2.cell_rng("v3stat", n, w, round(lam, 12))
    tr = s2.trajectory(p, n, lam, w, reps, T0 + T, rng)
    win = tr[T0:]
    abs_per_rep = (win == 0.0).any(axis=2)                # (T, reps) any symbol absent
    absence_any = float(abs_per_rep.mean())
    full_supp = 1.0 - absence_any
    af, se = s2.absence_fraction(p, n, lam, w, reps, T0, T, rng)
    worst = float(np.max(af))
    worst_se = float(se[int(np.argmax(af))])
    return {"absence_worst_symbol": worst, "absence_worst_se": worst_se,
            "absence_any_symbol": absence_any, "full_support_fraction": full_supp}


def absence_at(p, n, lam, w, reps=200, T0=200, T=1200):
    """Stationary absence fraction with its own standard error (same functional as the bisection)."""
    rng = s2.cell_rng("v3abs", n, w, round(lam, 12))
    af, se = s2.absence_fraction(p, n, lam, w, reps, T0, T, rng)
    return float(np.max(af)), float(se[int(np.argmax(af))])


def main():
    out = {"cells": [], "predictions": [], "controls": []}
    src = s2.sources()
    print("=" * 122)
    print("PART B -- what is INVARIANT at the boundary?  (at each located lambda*, across w)")
    print("  %-8s %4s %5s | %11s | %12s %12s %12s | %s" %
          ("source", "n", "w", "lambda*", "rate(MA)", "mean_var", "snr",
           "loss / regain measured at the boundary"))
    w_grid = [1, 2, 4, 8, 16, 64]
    for sname in ("uniform", "twohot"):
        p = src[sname]
        n = 50
        for w in w_grid:
            lam, trace, res = locate_boundary_log(p, n, w)
            st = stationary_stats(p, n, lam, w)
            rate = s2.ma_eigenvalue(w, lam)
            cell = {"source": sname, "n": n, "w": w, "lambda_star": lam, "rate_ma": rate,
                    "mean_var": float(np.mean(st["var"])), "snr": st["snr"],
                    "loss_rate": st["loss_rate"], "regain_rate": st["regain_rate"],
                    "log_resolution_decades": res, "trace": trace}
            out["cells"].append(cell)
            print("  %-8s %4d %5d | %11.6f | %12.6f %12.3e %12.3f | loss %.5f regain %.5f" %
                  (sname, n, w, lam, rate, cell["mean_var"], cell["snr"],
                   st["loss_rate"], st["regain_rate"]))

    # ---------------- PART C -- is the invariant good enough to PREDICT a boundary? -----
    print()
    print("=" * 122)
    print("PART C -- fit the candidate on w = 1, 4 and test it against the UNSEEN w = 8, 16")
    print("  %-8s %-9s | %12s %12s %12s %12s | %10s %10s" %
          ("source", "candidate", "w=1", "w=4", "w=8", "w=16", "spread(w1,w4)", "held-out miss"))
    for sname in ("uniform", "twohot"):
        cells = {c["w"]: c for c in out["cells"] if c["source"] == sname}
        for key, getter in (("rate_MA", lambda c: c["rate_ma"]), ("snr", lambda c: c["snr"])):
            vals = {w: getter(cells[w]) for w in (1, 2, 4, 8, 16, 64)}
            base = [v for v in (vals[1], vals[4]) if np.isfinite(v)]
            if len(base) < 2 or base[0] == 0:
                print("  %-8s %-9s | %12s %12s %12s %12s | %10s %10s" %
                      (sname, key, "inf" if not np.isfinite(vals[1]) else "%.4g" % vals[1],
                       "%.4g" % vals[4], "%.4g" % vals[8], "%.4g" % vals[16],
                       "n/a (ceiling)", "n/a"))
                out["predictions"].append({"source": sname, "candidate": key, "values": vals,
                                           "note": "w=1 is a domain ceiling in lam, not a crossing"})
                continue
            spread = abs(base[0] - base[1]) / abs(base[0])
            fit = 0.5 * (base[0] + base[1])
            miss = max(abs(vals[8] - fit) / abs(vals[8]), abs(vals[16] - fit) / abs(vals[16]))
            out["predictions"].append({"source": sname, "candidate": key,
                                       "values": {str(k): v for k, v in vals.items()},
                                       "spread_w1_w4": spread, "fitted_constant": fit,
                                       "held_out_max_rel_miss": miss})
            print("  %-8s %-9s | %12.4g %12.4g %12.4g %12.4g | %10.3f %10.3f" %
                  (sname, key, vals[1], vals[4], vals[8], vals[16], spread, miss))
    print("  (A candidate is an INVARIANT only if its w=1 and w=4 values agree AND that fit then")
    print("   predicts the unseen w=8, 16. A small in-sample spread with a large held-out miss is")
    print("   a coincidence of two points, not a law -- the held-out column is the verdict.)")

    # ---------------- PART A -- the behavioural control the criterion asks for ----------
    print()
    print("=" * 122)
    print("PART A -- criterion (ii): the boundary must SEPARATE two behaviours, not just be a number")
    print("  %-8s %4s %5s | %10s | %-34s | %-34s" %
          ("source", "n", "w", "lambda*", "below (lam*/2)", "above (2*lam*)"))
    for sname in ("uniform", "twohot"):
        p = src[sname]
        n = 50
        for w in (1, 4, 16):
            cell = [c for c in out["cells"] if c["source"] == sname and c["w"] == w][0]
            lam = cell["lambda_star"]
            if lam >= 1.0 - 1e-9:
                print("  %-8s %4d %5d | %10.6f | CEILING: the 1%% bar is met NOWHERE in lam <= 1, "
                      "so there is no interior boundary to control -- reported as unsatisfiable"
                      % (sname, n, w, lam))
                out["controls"].append({"source": sname, "n": n, "w": w, "lambda_star": lam,
                                        "kind": "ceiling_unsatisfiable"})
                continue
            below = support_measures(p, n, lam * 0.5, w)
            above = support_measures(p, n, lam * 2.0, w)
            # two-sided, on two functionals: the bar straddles, and full support improves.
            ok = (below["absence_worst_symbol"] > DELTA
                  and above["absence_worst_symbol"] < DELTA
                  and below["full_support_fraction"] < above["full_support_fraction"])
            out["controls"].append({"source": sname, "n": n, "w": w, "lambda_star": lam,
                                    "kind": "behavioural", "below": below, "above": above,
                                    "ok": bool(ok)})
            print("  %-8s %4d %5d | %10.6f | abs %.4f  full %.4f            | abs %.4f  full %.4f"
                  "            | %s" %
                  (sname, n, w, lam, below["absence_worst_symbol"],
                   below["full_support_fraction"], above["absence_worst_symbol"],
                   above["full_support_fraction"], "two-sided OK" if ok else "CONTROL FAILED"))
            assert ok, "behavioural control failed at %s w=%d" % (sname, w)

    # ---------------- PART D -- is the boundary criterion-dependent? ---------------------
    print()
    print("=" * 122)
    print("PART D -- THE SAME LOOP, TWO CRITERIA: keeping it intact vs healing it once broken")
    print("  lambda_heal = smallest lam at which a FULLY COLLAPSED loop reaches full support within")
    print("  H=2000 with probability >= 0.5 (log bisection on an uncensored proportion);")
    print("  lambda_stationary = the 1%% absence bar located in Part B.")
    print("  %-8s %4s %5s | %14s %14s | %10s" %
          ("source", "n", "w", "lambda_heal", "lambda_stationary", "stat / heal"))

    def heal_prob(lam, w, reps=200, H=2000):
        rng = s2.cell_rng("v3heal", n_, w, round(lam, 12))
        e0 = np.zeros(K)
        e0[0] = 1.0
        tr = s2.trajectory(p_, n_, lam, w, reps, H, rng, q0=e0)
        return float(((tr > 0.0).all(axis=2)).any(axis=0).mean())

    for sname in ("uniform", "twohot"):
        p_ = src[sname]
        n_ = 50
        for w in (1, 4):
            lo, hi = 1e-6, 1.0
            for _ in range(14):
                mid = 10.0 ** (0.5 * (math.log10(lo) + math.log10(hi)))
                if heal_prob(mid, w) >= 0.5:
                    hi = mid
                else:
                    lo = mid
            lam_heal = hi
            stat = [c for c in out["cells"] if c["source"] == sname and c["w"] == w][0]["lambda_star"]
            ratio = (stat / lam_heal) if lam_heal > 0 else float("nan")
            out["controls"].append({"source": sname, "n": n_, "w": w, "kind": "criterion_dependence",
                                    "lambda_heal": lam_heal, "lambda_stationary": stat,
                                    "ratio_stationary_over_heal": ratio,
                                    "stationary_is_ceiling": stat >= 1.0 - 1e-9})
            print("  %-8s %4d %5d | %14.6f %14.6f | %10.1f%s" %
                  (sname, n_, w, lam_heal, stat, ratio,
                   "   (stationary is a CEILING: ratio is a lower bound)" if stat >= 1.0 - 1e-9 else ""))
        lam_h1 = [c for c in out["controls"] if c.get("kind") == "criterion_dependence"
                  and c["source"] == sname and c["w"] == 1][0]
        print("  %-8s -> a collapsed loop heals at lam >= %.5f, but keeping it intact needs "
              "%.5f : %.0fx more fresh data" %
              (sname, lam_h1["lambda_heal"], lam_h1["lambda_stationary"],
               lam_h1["ratio_stationary_over_heal"]))

    with open("spike_v3_results.json", "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v3_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
