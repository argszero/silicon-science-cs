#!/usr/bin/env python3
"""Issue #122 -- spike_v2: multi-seed statistics for the hysteresis (registered criterion iii),
and the first test of P2 (is the fresh-data FRACTION the control variable?).

Two pieces of work in one instrument, sharing one trajectory function.

------------------------------------------------------------------------------
PART 1 -- criterion (iii): >=3 seeds per cell, mean +/- CI, censored-correct.
------------------------------------------------------------------------------
spike_v1 reported the first-passage pair as a mean of T over the replicates that finished inside
the horizon.  A mean over survivors is not a mean: at n=50, lam=0.005, 96 % of the collapsed
replicates never healed inside H=2000, so what was reported was the median of the lucky 4 %.
Here each cell is run with S=5 independent seeds and reports, per seed,
    p_finished = P(the first passage happened within H)      <- uncensored, exact
    med_T      = median T among the finished, with the censoring fraction printed
aggregated over seeds as mean +/- 95 % t-interval.  Criterion (iii) is evaluated on the aggregate.

------------------------------------------------------------------------------
PART 2 -- P2: "the prevention boundary is NOT a function of the fresh-data fraction alone".
------------------------------------------------------------------------------
Registered P2: two pool policies matched on per-generation fresh fraction but differing in pool
history have different boundaries.  The pool protocol family, parameterised by a window w in
batches:
    batch_t ~ Multinomial(n, lam*p* + (1-lam)*q_t)      (fresh fraction lam BY CONSTRUCTION)
    pool    = the union of the last w batches
    q_{t+1} = pool frequency
w = 1 is EXACTLY the replacement protocol of spike_v1 (the pool is the newest batch alone) -- and
that is checked against spike_v1's own simulator, not asserted (control C1).  At matched lam the
protocols differ ONLY in pool history, so P2 holds iff the located boundary moves with w.  The
boundary is located the same way everywhere: the largest lam whose stationary per-symbol absence
fraction stays <= 1 %, by bisection.

Controls, run BEFORE the readings:
  (C1) w = 1 must reproduce spike_v1's replacement trajectory EXACTLY (identity on the same rng
       path, not a tolerance).
  (C2) at lam = 1 the batch is pure real data, so the pool is w*n iid draws from p* and the
       absence fraction is EXACTLY (1-p_i)^(w*n) -- an exact statement that scales with w.

Usage: python3 spike_v2.py  ->  spike_v2_results.json
"""
import json
import math
import sys
import zlib

import numpy as np

import spike_v1

SEED0 = 20261003
K = 8


def cell_rng(*parts):
    """A seed that is a function of the request and NOTHING else (no per-process str hash)."""
    key = "|".join(str(x) for x in parts).encode("utf-8")
    return np.random.default_rng(SEED0 + zlib.crc32(key) % 1_000_000)


def sources():
    uni = np.full(K, 1.0 / K)
    zf = np.array([1.0 / (i + 1) ** 1.2 for i in range(K)])
    zf = zf / zf.sum()
    two = np.array([0.35, 0.35] + [0.30 / (K - 2)] * (K - 2))
    return {"uniform": uni, "zipf": zf, "twohot": two}


def trajectory(p, n, lam, w, reps, steps, rng, q0=None):
    """Post-draw states q_1..q_steps for the pool protocol with window w, shape (steps, reps, K).

    w = 1 reduces to the replacement loop of spike_v1: one multinomial draw per step, pool = that
    draw alone.  The rng is consumed with exactly one multinomial call per step, which is what
    makes the C1 identity check possible against spike_v1.simulate on the same seed.
    """
    Q = np.tile(p if q0 is None else q0, (reps, 1)).astype(float).copy()
    out = np.empty((steps, reps, K))
    batches = [np.zeros((reps, K), dtype=np.int64) for _ in range(w)]
    pool = np.zeros((reps, K), dtype=np.int64)
    idx = 0
    for t in range(steps):
        r = lam * p[None, :] + (1.0 - lam) * Q
        r = np.clip(r, 0.0, None)
        r = r / r.sum(axis=1, keepdims=True)
        B = rng.multinomial(n, r)
        if w == 1:
            Q = B / float(n)
        else:
            pool += B - batches[idx]
            batches[idx] = B
            idx = (idx + 1) % w
            # Normalise by the pool's ACTUAL size, not by the nominal window w*n: while the pool is
            # still filling, the nominal divisor leaves Q a sub-probability distribution, i.e. a
            # "model" that is simply wrong -- and the error is confined to the first w generations,
            # which is exactly where a short window takes its readings.
            tot = pool.sum(axis=1, keepdims=True).astype(float)
            Q = np.divide(pool, tot, out=np.full_like(pool, 1.0 / K, dtype=float),
                          where=tot > 0)
        out[t] = Q
    return out


def absence_fraction(p, n, lam, w, reps, T0, T, rng, q0=None):
    """Time-averaged per-symbol absence fraction over the window after burn-in T0, WITH its own
    resolution.

    The absence indicator is strongly autocorrelated: a symbol stays absent while the pool holds no
    draw of it, i.e. for runs of order w*n generations.  So the number of observations is NOT the
    sample size -- the honest standard error comes from the spread ACROSS REPLICATES, each replicate
    being one independent run of the loop.  Returns (mean_per_symbol, se_per_symbol).
    """
    tr = trajectory(p, n, lam, w, reps, T0 + T, rng, q0=q0)
    win = tr[T0:]
    per_rep = (win == 0.0).mean(axis=0)                 # (reps, K)
    mean = per_rep.mean(axis=0)
    se = per_rep.std(axis=0, ddof=1) / math.sqrt(reps) if reps > 1 else np.zeros(K)
    return mean, se


# --------------------------------------------------------------------------------------
# PART 1 -- first passage with seeds and CIs
# --------------------------------------------------------------------------------------

def first_passage(p, n, lam, mode, reps, H, rng, q0=None):
    """Right-censored first passage; taus = inf where censored."""
    Q = np.tile(p if q0 is None else q0, (reps, 1)).astype(float).copy()
    done = np.zeros(reps, dtype=bool)
    taus = np.full(reps, np.inf)
    for t in range(1, H + 1):
        r = lam * p[None, :] + (1.0 - lam) * Q
        r = np.clip(r, 0.0, None)
        r = r / r.sum(axis=1, keepdims=True)
        Q = rng.multinomial(n, r) / float(n)
        pres = Q > 0
        hit = (~pres).any(axis=1) if mode == "loss" else pres.all(axis=1)
        newly = hit & ~done
        taus[newly] = t
        done |= hit
        if done.all():
            break
    return taus, ~done


def mean_ci(xs):
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    if not xs:
        return {"mean": None, "lo": None, "hi": None, "sd": 0.0, "n_seeds": 0}
    m = float(np.mean(xs))
    if len(xs) < 2:
        return {"mean": m, "lo": m, "hi": m, "sd": 0.0, "n_seeds": 1}
    sd = float(np.std(xs, ddof=1))
    tval = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365}.get(
        len(xs), 1.96)
    h = tval * sd / math.sqrt(len(xs))
    return {"mean": m, "lo": m - h, "hi": m + h, "sd": sd, "n_seeds": len(xs)}


def part1(out, src, seeds=5, reps=200, H=2000):
    print("=" * 126)
    print("PART 1 -- criterion (iii): first passage, %d seeds/cell, mean +/- 95%% CI, censoring shown"
          % seeds)
    print("  %-8s %4s %7s | %-30s | %-30s" %
          ("source", "n", "lam", "T_loss over seeds", "T_recov over seeds"))
    lams = [0.005, 0.010, 0.020, 0.050, 0.100, 0.200, 0.500]
    for sname in ("uniform", "twohot"):
        p = src[sname]
        for n in (50, 200):
            for lam in lams:
                rows = []
                for s in range(seeds):
                    rng = cell_rng("v2fp", sname, n, round(lam, 9), s, "loss")
                    tl, cl = first_passage(p, n, lam, "loss", reps, H, rng)
                    rng = cell_rng("v2fp", sname, n, round(lam, 9), s, "rec")
                    e0 = np.zeros(K)
                    e0[0] = 1.0
                    tr, cr = first_passage(p, n, lam, "recover", reps, H, rng, q0=e0)
                    rows.append({"seed": s,
                                 "loss_med": float(np.median(tl[~cl])) if (~cl).any() else None,
                                 "loss_p": float((~cl).mean()), "loss_cens": float(cl.mean()),
                                 "rec_med": float(np.median(tr[~cr])) if (~cr).any() else None,
                                 "rec_p": float((~cr).mean()), "rec_cens": float(cr.mean())})
                agg = {"source": sname, "n": n, "lam": lam, "per_seed": rows,
                       "T_loss_median": mean_ci([r["loss_med"] for r in rows]),
                       "T_recov_median": mean_ci([r["rec_med"] for r in rows]),
                       "loss_censored": mean_ci([r["loss_cens"] for r in rows]),
                       "recov_censored": mean_ci([r["rec_cens"] for r in rows]),
                       "p_heal": mean_ci([r["rec_p"] for r in rows]),
                       "p_lost": mean_ci([r["loss_p"] for r in rows])}
                losm, recm = agg["T_loss_median"]["mean"], agg["T_recov_median"]["mean"]
                agg["ratio_of_medians"] = (recm / losm) if (losm and recm and losm > 0) else None
                out["part1"].append(agg)
                print("  %-8s %4d %7.3f | %-30s | %-30s" %
                      (sname, n, lam,
                       ("%.1f [%.1f,%.1f]" % (losm, agg["T_loss_median"]["lo"],
                                              agg["T_loss_median"]["hi"]))
                       if losm else "no seed finished",
                       ("%.1f [%.1f,%.1f] cens %.2f" % (recm, agg["T_recov_median"]["lo"],
                                                        agg["T_recov_median"]["hi"],
                                                        agg["recov_censored"]["mean"]))
                       if recm else "cens %.2f: none finished" % agg["recov_censored"]["mean"]))


# --------------------------------------------------------------------------------------
# PART 2 -- P2: does the boundary move with pool history at matched lam?
# --------------------------------------------------------------------------------------

def locate_boundary(p, n, w, delta=0.01, reps=128, T0=200, T=2000, iters=12):
    """Largest lam whose stationary worst-symbol absence fraction is <= delta (bisection)."""
    lo, hi = 0.0, 1.0
    trace = []
    for i in range(iters):
        mid = 0.5 * (lo + hi)
        rng = cell_rng("v2bnd", n, w, i)          # deterministic, and distinct per grid point
        af, se = absence_fraction(p, n, mid, w, reps, T0, T, rng)
        worst = float(np.max(af))
        worst_se = float(se[int(np.argmax(af))])
        trace.append({"lam": mid, "worst_abs": worst, "worst_se": worst_se,
                      "ok": worst <= delta})
        if worst <= delta:
            hi = mid
        else:
            lo = mid
    return hi, trace


def part2(out, src):
    print()
    print("=" * 126)
    print("PART 2 -- P2: at MATCHED per-generation lam, does the boundary move with pool history?")
    print("  %-8s %4s | %12s %12s %12s | %10s" %
          ("source", "n", "w=1 (repl)", "w=4", "w=64", "w64 / w1"))
    for sname in ("uniform", "zipf"):
        p = src[sname]
        for n in (50, 200):
            bnd, traces = {}, {}
            for w in (1, 4, 64):
                b, tr = locate_boundary(p, n, w)
                bnd[w] = b
                traces[w] = tr
            ratio = (bnd[64] / bnd[1]) if bnd[1] > 0 else None
            out["part2"].append({"source": sname, "n": n,
                                 "boundary": {str(k): v for k, v in bnd.items()},
                                 "ratio_w64_over_w1": ratio,
                                 "traces": {str(k): v for k, v in traces.items()}})
            print("  %-8s %4d | %12.6f %12.6f %12.6f | %10s" %
                  (sname, n, bnd[1], bnd[4], bnd[64],
                   ("%.3f" % ratio) if ratio else "n/a"))
    print("  (w is the pool window in batches; w=1 IS the replacement protocol.  A boundary that")
    print("   moves with w, at matched lam, is P2: the fraction is not the only control variable.)")



# --------------------------------------------------------------------------------------
# PART 3 -- the MECHANISM behind P2, stated as a prediction before it is measured
# --------------------------------------------------------------------------------------
# With a pool window w, the exact mean recursion is
#     E[q_{t+1}] = lam*p* + (1-lam) * (1/w) * sum_{j=0}^{w-1} E[q_{t-j}]
# i.e. the replacement loop's CONTEMPORANEOUS feedback (w=1: delta_{t+1} = (1-lam) delta_t,
# an exponential decay at rate -ln(1-lam) ~ lam) becomes a MOVING AVERAGE of past states.
# The linearised deviation therefore obeys a degree-w recursion, whose slowest mode is the
# eigenvalue nearest 1 of the companion matrix.  PREDICTION, stated before measuring:
#     w = 1  -> rate = -ln(1-lam)                       (the replacement law)
#     w > 1  -> rate = -ln(largest eigenvalue of the MA recursion) < lam, falling with w
# so pooling slows the loop's RETURN TO THE SOURCE, which is what lowers the boundary.

def ma_eigenvalue(w, lam):
    """Slowest decay rate of the exact mean recursion for a window of w batches.

    delta_{t+1} = (1-lam) * (1/w) * sum_{j=0}^{w-1} delta_{t-j}
    Companion matrix on the state (delta_t, ..., delta_{t-w+1}); returns -ln(largest |eig|).
    lam = 1 is a legitimate boundary reading (the fraction saturates), and there the deviation is
    zero at every step, i.e. the relaxation is instantaneous: return +inf rather than raising.
    """
    if w == 1:
        return -math.log(1.0 - lam) if lam < 1.0 else float("inf")
    if lam >= 1.0:
        return float("inf")
    M = np.zeros((w, w))
    M[0, :] = (1.0 - lam) / w
    for i in range(1, w):
        M[i, i - 1] = 1.0
    ev = np.abs(np.linalg.eigvals(M))
    top = float(np.max(ev))
    return -math.log(top) if top > 0.0 else float("inf")


def relaxation_rate(p, n, lam, w, reps=4000, steps=400, skip=None, q0=None):
    """Measured decay rate of the mean deviation from p*, by linear regression on log ||.||_1.

    The fit window STOPS where the signal reaches its own Monte-Carlo noise floor.  A regression
    that runs past the floor fits the floor, not the decay -- and the error is largest exactly where
    the decay is fastest, which is what makes it look like a physical effect instead of a window
    defect.  The floor is computed from the across-replicate spread, so it is the statistic's own
    resolution and not a typed constant.
    """
    rng = cell_rng("v2rel", n, w, round(lam, 9))
    if q0 is None:
        q0 = np.zeros(K)
        q0[0] = 1.0
    tr = trajectory(p, n, lam, w, reps, steps, rng, q0=q0)      # (steps, reps, K)
    mean_t = tr.mean(axis=1)                                     # (steps, K)
    se_i = tr.std(axis=1, ddof=1) / math.sqrt(reps)              # (steps, K)
    dev = np.abs(mean_t - p[None, :]).sum(axis=1)
    se_dev = se_i.sum(axis=1)                                    # upper bound on the L1 noise floor
    if skip is None:
        skip = max(5 * w, 20)
    sig = dev > 10.0 * se_dev
    t_max = int(np.max(np.nonzero(sig)[0])) if sig.any() else skip
    if t_max <= skip + 5:
        return float("nan"), dev.tolist(), skip, t_max
    t = np.arange(skip, t_max, dtype=float)
    y = np.log(dev[skip:t_max])
    A = np.vstack([t, np.ones_like(t)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return -float(coef[0]), dev.tolist(), skip, t_max


def part3(out, src):
    print()
    print("=" * 126)
    print("PART 3 -- MECHANISM: pooling turns exponential mean reversion (rate ~lam) into a slow")
    print("          moving-average relaxation.  Measured rate vs the two candidate laws.")
    print("  %-8s %4s %6s %6s | %12s %12s %12s | %8s" %
          ("source", "n", "lam", "w", "rate(meas)", "rate(w=1 law)", "rate(MA eig)", "meas/eig"))
    for sname in ("uniform",):
        p = src[sname]
        for n in (50,):
            for lam in (0.02, 0.05):
                for w in (1, 2, 4, 8, 16, 64):
                    rate, dev, skip, tmax = relaxation_rate(p, n, lam, w)
                    law1 = -math.log(1.0 - lam)
                    eig = ma_eigenvalue(w, lam)
                    out["part3"].append({"source": sname, "n": n, "lam": lam, "w": w,
                                         "rate_measured": rate, "rate_w1_law": law1,
                                         "rate_ma_eig": eig, "ratio_measured_over_eig": rate / eig,
                                         "skip": skip, "fit_stop": tmax, "dev_tail": dev[-5:]})
                    print("  %-8s %4d %6.3f %6d | %12.5f %12.5f %12.5f | %8.3f  (fit %d..%d)" %
                          (sname, n, lam, w, rate, law1, eig, rate / eig, skip, tmax))
    print("  (If the measured rate tracks the MA eigenvalue and not the w=1 law, then pooling")
    print("   slows the return to the source -- that is the mechanism behind P2's boundary.)")


def main():
    out = {"seed0": SEED0, "K": K, "part1": [], "part2": [], "part3": [], "controls": {}}
    src = sources()

    print("=" * 126)
    print("CONTROLS -- run BEFORE the readings: a reading from an uncalibrated family is not a")
    print("            reading (C1: w=1 IS the replacement loop; C2: lam=1 is exact for every w)")
    p, n, lam, reps, T = src["twohot"], 50, 0.1, 16, 120
    my = trajectory(p, n, lam, 1, reps, T, cell_rng("ctl1", n, lam))
    _, Nrec = spike_v1.simulate(p, n, lam, reps, T, 0, cell_rng("ctl1", n, lam))
    ref = np.transpose(Nrec / float(n), (1, 0, 2))     # spike_v1 records (reps, T, K)
    assert my.shape == ref.shape, "C1 shape mismatch %s vs %s" % (my.shape, ref.shape)
    max_abs = float(np.max(np.abs(my - ref)))
    out["controls"]["C1_w1_is_replacement"] = {"max_abs_diff_vs_spike_v1": max_abs,
                                               "shape": list(my.shape)}
    print("   C1  w=1 vs spike_v1's replacement simulator: max |state difference| = %.3e "
          "over %d states" % (max_abs, my.size))
    assert max_abs == 0.0, "C1 failed: w=1 is not the replacement loop (diff %.3e)" % max_abs
    # C2a -- where the exact value is MEASURABLE (exact >= 1e-2), demand two-sided equality.
    # C2b -- where it is not (a big pool puts the exact value near 1e-186), the honest check is
    #        one-sided: the measured absence may not EXCEED the exact value by more than MC noise.
    #        An equality assertion on an unmeasurable quantity is not a stricter control, it is a
    #        broken one (Class 161(d): a premise must be attainable by its own instrument).
    p2 = src["uniform"]
    for w, n2 in ((1, 10), (2, 10), (4, 10)):
        t0 = max(100, 2 * w)
        af, se = absence_fraction(p2, n2, 1.0, w, 900, t0, 400, cell_rng("ctl2a", w, n2))
        exact = (1.0 - p2) ** (w * n2)
        z = float(np.max(np.abs(af - exact) / np.clip(se, 1e-300, None)))
        rel = float(np.max(np.abs(af - exact) / exact))
        out["controls"]["C2a_lam1_w%d_n%d" % (w, n2)] = {
            "measured": af.tolist(), "se": se.tolist(), "exact": exact.tolist(),
            "max_rel": rel, "max_z": z}
        print("   C2a lam=1, w=%d n=%-3d : measured %.5f vs exact %.5f  (rel %.3f, max z=%.2f)"
              % (w, n2, float(np.max(af)), float(np.max(exact)), rel, z))
        assert z < 5.0, "C2a failed at w=%d n=%d (z=%.2f)" % (w, n2, z)
    for w in (1, 4, 64):
        af, se = absence_fraction(p2, 50, 1.0, w, 400, max(100, 2 * w), 400, cell_rng("ctl2b", w))
        exact = (1.0 - p2) ** (w * 50)
        over = float(np.max(af - exact - 5.0 * se))
        out["controls"]["C2b_lam1_w%d" % w] = {"measured": af.tolist(), "exact": exact.tolist(),
                                               "max_over_exact_in_sigma": over}
        print("   C2b lam=1, w=%-3d : measured absence %.3e vs exact %.3e  (max overshoot %.2e, "
              "one-sided)" % (w, float(np.max(af)), float(np.max(exact)), over))
        assert over <= 0.0, "C2b failed at w=%d: measured absence EXCEEDS the exact value" % w
    print()

    part1(out, src)
    part2(out, src)
    part3(out, src)

    with open("spike_v2_results.json", "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v2_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
