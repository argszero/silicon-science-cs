#!/usr/bin/env python3
"""Issue #122 -- spike_v1: the mean-field loss rate is a LOWER BOUND, and the rate that prevents
is not the rate that recovers (measured as a pair of first-passage times).

Model.  At generation t the runner holds a model q_t over K symbols; it draws a dataset
N_t ~ Multinomial(n, lam*p* + (1-lam)*q_t) and sets q_{t+1} = N_t/n.  lam is the fresh-data
fraction.  Three exact facts drive everything below:

  (F1) P(the draw from q loses symbol i) = ell_i(q) = (1 - lam*p*_i - (1-lam)*q_i)^n     EXACT.
  (F2) E[q_t] = p* + (1-lam)^t (q_0 - p*), and Var(q_t) satisfies an exact linear recursion.
  (F3) ell_i is CONVEX in q_i and E[q_i] -> p*_i, so by Jensen
           E[ell_i(q)]  >=  ell_i(p*_i)  =  (1 - p*_i)^n.
       So the practitioners' closed form (1-p*)^n is a LOWER BOUND on the loop's loss rate; the
       gap is a fluctuation penalty that grows with n.

Two routes to the same quantity, always on the SAME (state, draw) pairing:
  route A -- count the transitions in the simulation;
  route B -- integrate the exact kernel (F1) over the MEASURED marginal of q.
Route B is exact given the marginal, so A vs B checks the bookkeeping, not the physics.

Headline.  Two first-passage times, two initial conditions, one loop:
  T_loss(lam)  -- generations from a healthy start (q_0 = p*) until some symbol is absent;
  T_recov(lam) -- generations from a fully collapsed start (q_0 = a point mass) until every
                  symbol is present at the same generation.
If T_recov > T_loss the loop is hysteretic at that lam.  Both are right-censored at H.
Controls (planted truth): lam = 0 must give an absence fraction of exactly (K-1)/K; lam = 1 must
give a loss rate of exactly (1-p*)^n.

Usage: python3 spike_v1.py  ->  spike_v1_results.json
"""
import json
import sys
import zlib

import numpy as np

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


def draw(Q, p, n, lam, rng):
    r = lam * p[None, :] + (1.0 - lam) * Q
    r = np.clip(r, 0.0, None)
    r = r / r.sum(axis=1, keepdims=True)
    return rng.multinomial(n, r)


def simulate(p, n, lam, reps, T, T0, rng, q0=None):
    """Returns (Qrec, Nrec): Qrec[t] = q_t, Nrec[t] = the draw made FROM q_t."""
    Q = np.tile(p if q0 is None else q0, (reps, 1)).astype(float).copy()
    Qrec = np.empty((reps, T, K))
    Nrec = np.empty((reps, T, K), dtype=np.int64)
    for t in range(T0 + T + 1):
        C = draw(Q, p, n, lam, rng)
        if T0 <= t < T0 + T:
            Qrec[:, t - T0, :] = Q
            Nrec[:, t - T0, :] = C
        Q = C / float(n)
    return Qrec, Nrec


def exact_kernel(p, n, lam, q):
    """(F1): P(the draw from state q loses symbol i)."""
    return (1.0 - (lam * p[None, :] + (1.0 - lam) * q)) ** n


def mean_var_recursion(p_i, n, lam, steps):
    """(F2): exact m_t = E[q_i(t)], v_t = Var(q_i(t)) from the fixed point."""
    m, v = p_i, 0.0
    for _ in range(steps):
        m_r = lam * p_i + (1.0 - lam) * m
        v_r = (1.0 - lam) ** 2 * v
        v = (m_r - v_r - m_r * m_r) / n + v_r
        m = m_r
    return m, v


def stationary_cell(p, n, lam, reps=24, T=200, T0=100, q0=None):
    """Per-symbol loss / regain rates by the two routes, plus the stationary absence fraction."""
    rng = cell_rng("sweep", n, lam, tuple(np.round(p, 6)), "q0" if q0 is not None else "p")
    Q, N = simulate(p, n, lam, reps, T, T0, rng, q0=q0)
    qt = Q[:, :-1, :]                # the states q_t
    kept = N[:, :-1, :] > 0          # the draw from q_t kept symbol i
    pres = qt > 0
    loss_num = (pres & ~kept).sum(axis=(0, 1)).astype(float)
    loss_den = pres.sum(axis=(0, 1)).astype(float)
    reg_num = ((~pres) & kept).sum(axis=(0, 1)).astype(float)
    reg_den = (~pres).sum(axis=(0, 1)).astype(float)
    ell = exact_kernel(p, n, lam, qt)
    loss_B = np.array([ell[:, :, i][pres[:, :, i]].mean() if pres[:, :, i].any() else np.nan
                       for i in range(K)])
    with np.errstate(invalid="ignore", divide="ignore"):
        loss_A = np.where(loss_den > 0, loss_num / loss_den, np.nan)
        reg_A = np.where(reg_den > 0, reg_num / reg_den, np.nan)
    return {"loss_A": loss_A.tolist(), "loss_B": loss_B.tolist(),
            "loss_den": loss_den.tolist(), "reg_den": reg_den.tolist(),
            "regain_A": reg_A.tolist(), "regain_cf": (1.0 - (1.0 - lam * p) ** n).tolist(),
            "loss_cf": ((1.0 - p) ** n).tolist(),
            "abs_per_sym": ((~pres).sum(axis=(0, 1)) / float(pres.shape[0] * pres.shape[1])).tolist(),
            "abs_overall": float((~pres).mean()),
            "mean_mc": Q.reshape(-1, K).mean(axis=0).tolist(),
            "var_mc": Q.reshape(-1, K).var(axis=0).tolist()}


def first_passage(p, n, lam, mode, reps=200, H=2000, q0=None):
    """First-passage time of the support event, right-censored at H.

    mode='loss'    -- healthy start: first generation with ANY symbol absent.
    mode='recover' -- collapsed start: first generation with EVERY symbol present.
    Returns (censored_fraction, mean_over_observed).
    """
    rng = cell_rng("fp", mode, n, round(lam, 9), tuple(np.round(p, 6)))
    Q = np.tile(p if q0 is None else q0, (reps, 1)).astype(float).copy()
    done = np.zeros(reps, dtype=bool)
    taus = np.full(reps, np.nan)
    for t in range(1, H + 1):
        Q = draw(Q, p, n, lam, rng) / float(n)
        pres = Q > 0
        hit = (~pres).any(axis=1) if mode == "loss" else pres.all(axis=1)
        newly = hit & ~done
        taus[newly] = t
        done |= hit
        if done.all():
            break
    cens = float((~done).mean())
    obs = taus[np.isfinite(taus)]
    return cens, (float(obs.mean()) if obs.size else float("nan")), int(obs.size)


def main():
    out = {"seed0": SEED0, "K": K, "cells": [], "certificates": {}, "controls": {},
           "first_passage": [], "crossing": {}}
    src = sources()
    n_grid = [25, 50, 100, 200]
    lam_grid = [0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]

    # ------------- main sweep: the Jensen gap, per symbol, WITH the observation counts ---------
    print("=" * 122)
    print("SWEEP -- the loop's loss rate vs the mean-field closed form (1-p*)^n, WORST symbol")
    print("  %-8s %4s %6s | %9s %9s %9s | %9s %7s %8s | %9s" %
          ("source", "n", "lam", "loss_A", "loss_B", "loss_cf", "cf/meas", "n_obs", "absfrac",
           "abs_worst"))
    rel_all, rel_ok, gap_ok, gap_abs = [], [], [], []
    for sname, p in src.items():
        for n in n_grid:
            for lam in lam_grid:
                c = stationary_cell(p, n, lam)
                A = np.array(c["loss_A"])
                B = np.array(c["loss_B"])
                D = np.array(c["loss_den"])
                cf = np.array(c["loss_cf"])
                # A vs B is only a check where the expected number of loss events is adequate:
                # a rate of 1e-3 observed 50 times carries ~0.05 events and no information.
                ev = D * np.where(np.isfinite(B), B, 0.0)
                fin = np.isfinite(A) & np.isfinite(B) & (ev >= 30.0)
                rel = np.abs(A[fin] - B[fin]) / B[fin]
                if rel.size:
                    rel_all.append(float(np.max(rel)))
                    rel_ok.append(float(np.max(rel)))
                # the Jensen gap, per symbol, on the same adequate-event gate
                gap_fin = fin & (cf > 0)
                gap_ok.extend((cf[gap_fin] / B[gap_fin]).tolist())
                # each reading carries the absence fraction of ITS symbol: route B is the kernel
                # averaged over the generations where the symbol is PRESENT, and presence selects
                # the high-q (low-kernel) states -- so this is the variable that decides which side
                # of the closed form a reading lands on.
                gap_abs.extend(np.asarray(c["abs_per_sym"])[gap_fin].tolist())
                iw = int(np.nanargmax(np.where(np.isfinite(B), B, -1.0)))
                out["cells"].append({"source": sname, "n": n, "lam": lam,
                                     "loss_A": c["loss_A"], "loss_B": c["loss_B"],
                                     "loss_cf": c["loss_cf"], "loss_den": c["loss_den"],
                                     "regain_A": c["regain_A"], "regain_cf": c["regain_cf"],
                                     "abs_per_sym": c["abs_per_sym"], "abs_overall": c["abs_overall"],
                                     "mean_mc": c["mean_mc"], "var_mc": c["var_mc"],
                                     "worst_symbol": iw})
                if np.isfinite(B[iw]) and cf[iw] > 0:
                    print("  %-8s %4d %6.3f | %9.5f %9.5f %9.3e | %9.2f %7d %8.4f | %9.4f" %
                          (sname, n, lam, A[iw], B[iw], cf[iw], cf[iw] / B[iw], int(D[iw]),
                           c["abs_overall"], c["abs_per_sym"][iw]))
                else:
                    print("  %-8s %4d %6.3f | %9s %9s %9.3e | %9s %7d %8.4f | %9.4f" %
                          (sname, n, lam, "n/a", "n/a", cf[iw], "n/a", int(D[iw]),
                           c["abs_overall"], c["abs_per_sym"][iw]))
    out["rel_A_vs_B_max_any"] = float(np.nanmax(rel_all))
    out["rel_A_vs_B_max_wellcounted"] = float(np.nanmax(rel_ok)) if rel_ok else None
    out["cf_over_meas_median"] = float(np.median(gap_ok)) if gap_ok else None
    out["cf_over_meas_min"] = float(np.min(gap_ok)) if gap_ok else None
    out["cf_over_meas_max"] = float(np.max(gap_ok)) if gap_ok else None
    out["n_gap_pairs"] = len(gap_ok)
    # The closed form is a bound on the UNCONDITIONAL loss probability (Jensen); the readings are
    # the CONDITIONAL rate, taken over present generations only.  Count the readings on each side
    # and bin them by the absence fraction, so the paper can state the scope of its own claim
    # instead of asserting it holds everywhere.
    out["n_gap_above1"] = int(sum(1 for g in gap_ok if g > 1.0))
    out["n_gap_below1"] = int(sum(1 for g in gap_ok if g <= 1.0))
    out["gap_by_absence"] = []
    for lo, hi in ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0000001)):
        sel = [g for g, a in zip(gap_ok, gap_abs) if lo <= a < hi]
        out["gap_by_absence"].append({
            "lo": lo, "hi": hi, "n": len(sel),
            "n_above1": int(sum(1 for g in sel if g > 1.0)),
            "median_ratio": float(np.median(sel)) if sel else None})

    # ------------- CERTIFICATE 1: the mean recursion, from a PERTURBED start -----------------
    print()
    print("CERTIFICATE 1 -- E[q_t] = p* + (1-lam)^t (q_0 - p*), from a perturbed start")
    p = src["twohot"]
    q0 = np.full(K, 1.0 / K)
    for n, lam in ((200, 0.05), (50, 0.5)):
        rng = cell_rng("cert-mean", n, lam)
        reps = 400
        Q = np.tile(q0, (reps, 1)).astype(float).copy()
        traj = []
        for _ in range(60):
            traj.append(Q.mean(axis=0))
            Q = draw(Q, p, n, lam, rng) / float(n)
        traj = np.array(traj)
        pred = np.array([p + (1.0 - lam) ** t * (q0 - p) for t in range(60)])
        err = float(np.abs(traj - pred).max())
        out["certificates"]["mean_n%d_lam%.3f" % (n, lam)] = {"max_abs_err": err,
                                                              "readings": int(traj.size)}
        print("   n=%-4d lam=%.3f : max |MC mean - exact recursion| = %.5f over %d readings"
              % (n, lam, err, traj.size))
        assert err < 0.02, "mean recursion certificate failed"

    # ------------- CERTIFICATE 2: the variance recursion = the fluctuation behind the gap -----
    print()
    print("CERTIFICATE 2 -- variance recursion vs measured Var(q_i)")
    for sname in ("uniform", "twohot"):
        p = src[sname]
        for n, lam in ((50, 0.01), (200, 0.05)):
            rng = cell_rng("cert-var", sname, n, lam)
            Q, _ = simulate(p, n, lam, 400, 1, 400, rng)
            var_mc = Q[:, 0, :].var(axis=0)
            vv = [mean_var_recursion(float(p[i]), n, lam, 401)[1] for i in range(K)]
            err = float(np.max(np.abs(var_mc - np.array(vv))))
            out["certificates"]["var_%s_n%d_lam%.3f" % (sname, n, lam)] = {
                "max_abs_err": err, "var_mc": var_mc.tolist(), "var_exact": vv}
            print("   %-8s n=%-4d lam=%.3f : max |Var_MC - Var_exact| = %.6f  (Var_exact up to %.5f)"
                  % (sname, n, lam, err, max(vv)))
            assert err < 0.25 * max(vv) + 1e-4, "variance recursion certificate failed"

    # ------------- CONTROLS: planted truth, two-sided ---------------------------------------
    print()
    print("CONTROL (planted truth, two-sided) -- lam=0: absence (K-1)/K exactly; lam=1: (1-p)^n")
    e0c = np.zeros(K)
    e0c[0] = 1.0
    c0 = stationary_cell(src["uniform"], 50, 0.0, q0=e0c)
    abs0 = c0["abs_overall"]
    exact0 = (K - 1) / K
    out["controls"]["lam0"] = {"abs_overall": abs0, "exact": exact0, "loss_B": c0["loss_B"]}
    print("   uniform n=50 lam=0.0, point-mass start : absence fraction=%.4f  (exact (K-1)/K=%.4f)"
          % (abs0, exact0))
    assert abs(abs0 - exact0) < 1e-12, "lam=0 collapse control failed"
    for sname, p_ in src.items():
        c1 = stationary_cell(p_, 50, 1.0)
        cf = (1.0 - p_) ** 50
        B = np.array(c1["loss_B"])
        ok = np.isfinite(B)
        rel = float(np.max(np.abs(B[ok] - cf[ok]) / cf[ok])) if ok.any() else float("nan")
        out["controls"]["lam1_" + sname] = {"loss_B": B.tolist(), "cf": cf.tolist(), "rel": rel}
        print("   %-8s lam=1.0      : max rel |loss_B - (1-p)^n| = %.2e (route B is exact here)"
              % (sname, rel))
        assert rel < 1e-9, "lam=1 identity control failed: %s" % sname

    # ------------- FIRST PASSAGE: T_loss vs T_recov ----------------------------------------
    print()
    print("FIRST PASSAGE -- T_loss (healthy -> any absence) vs T_recov (collapsed -> full support)")
    print("  %-8s %4s %7s | %12s %8s | %12s %8s | %8s" %
          ("source", "n", "lam", "T_loss", "cens_l", "T_recov", "cens_r", "T_r/T_l"))
    fp_lam = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    for sname in ("uniform", "twohot"):
        p = src[sname]
        for n in (50, 200):
            prev = None
            for lam in fp_lam:
                cens_l, tl, ncl = first_passage(p, n, lam, "loss")
                e0 = np.zeros(K)
                e0[0] = 1.0
                cens_r, tr, ncr = first_passage(p, n, lam, "recover", q0=e0)
                ratio = tr / tl if (tl and np.isfinite(tl) and np.isfinite(tr) and tl > 0) else float("nan")
                out["first_passage"].append({"source": sname, "n": n, "lam": lam,
                                             "T_loss": tl, "cens_loss": cens_l, "n_obs_loss": ncl,
                                             "T_recov": tr, "cens_recov": cens_r,
                                             "n_obs_recov": ncr, "ratio_recov_over_loss": ratio})
                if (np.isfinite(ratio) and prev is not None and np.isfinite(prev[1])
                        and (prev[1] - 1.0) * (ratio - 1.0) < 0.0):
                    out["crossing"]["%s/n%d" % (sname, n)] = {
                        "lam_lo": prev[0], "ratio_lo": prev[1], "lam_hi": lam, "ratio_hi": ratio}
                prev = (lam, ratio)
                print("  %-8s %4d %7.3f | %12s %8.2f | %12s %8.2f | %8s" %
                      (sname, n, lam, ("%.2f" % tl) if np.isfinite(tl) else "cens",
                       cens_l, ("%.2f" % tr) if np.isfinite(tr) else "cens", cens_r,
                       ("%.3f" % ratio) if np.isfinite(ratio) else "n/a"))

    with open("spike_v1_results.json", "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("route A vs B, worst rel (all symbols): %s ; (well-counted only): %s"
          % (out["rel_A_vs_B_max_any"], out["rel_A_vs_B_max_wellcounted"]))
    print("route A vs B, worst rel over cells with >=30 expected loss events: %s (n=%d)"
          % (out["rel_A_vs_B_max_wellcounted"], out["n_gap_pairs"]))
    print("Jensen gap (closed form / measured loss), per symbol, >=30 expected events: "
          "median %s  min %s  max %s" % (out["cf_over_meas_median"], out["cf_over_meas_min"],
                                         out["cf_over_meas_max"]))
    print("   above the closed form in %d of %d readings; by absence fraction:"
          % (out["n_gap_above1"], out["n_gap_pairs"]))
    for b in out["gap_by_absence"]:
        print("     absent %3.0f-%-3.0f%%: n=%-4d above1=%-3d median ratio %s"
              % (100 * b["lo"], 100 * b["hi"], b["n"], b["n_above1"],
                 ("%.4g" % b["median_ratio"]) if b["median_ratio"] is not None else "n/a"))
    print("wrote spike_v1_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
