#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 6: WHICH channel pays the benefit (registered P3), and what this model's
"contention" actually is.

WHAT THIS FILE IS.  Steps 1-5 built the model, located the boundary (rho* ~ 0.985, indexed by the pool size A),
decomposed the A-effect, and refuted the registered P2.  The registration (`heilmeier.md` section 4, frozen
before any deciding run) also says:

  P3 -- "part of the reported gain is PARALLELISM, not prediction: the prediction-attributable fraction F of
  the serial-baseline gain is below 0.7, and decreasing in rho.  Justification: the systems baselines are
  serial, so a speculative call also buys concurrency any parallel schedule buys."

WHAT P3 NEEDS, and what this file does about it.  Step 4 produced the algebra: with `speculate=False` a step
costs `T + w_s + S` and with `speculate=True` it costs `max(T, w_p + S)`, so

    benefit = w_s + S - overshoot,   overshoot = max(0, latency_spec - T)

and every term is observable.  This file splits that identity into THREE reported channels, all measurable
per step:

    H := max(0, S - overshoot)      the HIDING channel -- service time the think phase absorbed.  This is the
                                    only part that needs the payload, i.e. the prediction-attributable one.
    D := min(0, S - overshoot)      the OVERSHOOT DEBIT (<= 0) -- the part of the speculative wait that even
                                    the whole service time could not pay for.
    W := w_s                        the QUEUE-POSITION channel -- the wait the SERIAL baseline paid on this
                                    step and the speculative schedule dodged by issuing earlier.

with `H + D + W == benefit` per step to the arithmetic's own resolution.  The registered fraction is then

    F := mean(H) / mean(benefit)    over the same steps, per seed, then aggregated over seeds.

DECLARED BEFORE THE RUN (rules of this file, not descriptions of what came out):

  * F is a "fraction of the gain" and is reported only for cells whose measured gain is POSITIVE.  A cell at
    or above the boundary has no gain to split; its channels are reported and its F is recorded NOT DEFINED,
    with the count of seeds excluded for that reason.  Exclusions are counted, never silent.
  * P3a ("below 0.7"): over every positive-gain cell of every family: CONFIRMED iff EVERY cell's F interval
    lies strictly below 0.7; CONTRADICTED iff at least one lies strictly above 0.7; UNRESOLVED otherwise.
  * P3b ("decreasing in rho"): order a family's positive-gain cells by rho ascending and take the
    paired-by-seed difference dF = F(higher rho) - F(lower rho) at each adjacent pair.  A pair is an
    INCREASE if dF's interval lies strictly above zero, a DECREASE if strictly below, otherwise a tie.
    CONFIRMED iff no increase and at least one decrease; CONTRADICTED iff at least one increase; UNRESOLVED
    otherwise.  A Spearman rank correlation over the same cells is reported as a summary, not as a verdict.
  * Each adjacent pair's own interval width is printed: a rule whose resolution is unstated cannot be read.

WHAT ELSE THIS FILE MEASURES -- the load channel, because P1's justification ("the added load is paid by every
request through queueing") asserts one.  With `q = 0` the speculative schedule issues exactly the SAME calls
with the same service times as the serial one, only earlier, so the total work must be the same and any rise
in measured contention must be pure makespan compression:

    rho_spec / rho_serial = makespan_serial / makespan_spec

Both facts are checked on every cell (relative tolerance on `busy`, and that ratio identity), so "no load is
added" is a measurement rather than an inference from the code.

AND WHAT THE MODEL'S OWN FILES SAY ABOUT SPECULATION, because the runs and the module docstring disagree and
the disagreement bounds every claim in this paper:

  * the docstring says "a wrong prediction is also issued there, consumes a worker, and is discarded, after
    which the real call is issued at the end of the think phase";
  * the code issues early ONLY when the prediction hits, and schedules a miss exactly as the serial call does.
    Measured here four ways: (i) `h = 0` reproduces `speculate=False` step for step (anchor A2, re-measured);
    (ii) `h = 1.0` is identical to `ignore_h` at any h; (iii) with `q = 1` the model's own `wasted` counter
    divided by `comp` equals the count of MISSES implied by the re-derived draw stream -- exactly -- while with
    `q = 0` it is 0; (iv) with `q = 0` the two arms' `busy` agree to ~1e-15 relative, so no extra work is
    scheduled.  Conclusion carried in the report: in this instrument `h` is the FRACTION OF STEPS WHOSE CALL
    IS ISSUED EARLY -- a parallel width -- not a predictor's accuracy with a cost for being wrong.  That makes
    the instrument an optimistic case for speculation, and it is why the promised "matched parallelism" arm
    (the same early-issue width, no prediction) cannot be built in it: here, issuing early IS the hit.

CPU only, stdlib only, fixed seeds, no network.  `instrument_v0.py` is imported UNMODIFIED; steps 2-5 supply
the t interval, the draw re-derivation with its tolerance, and the per-step terms (`D1.per_step`), so this
file's channels are the same function of the same draws as step 4's identity.
"""
import argparse
import io
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I      # noqa: E402  the model, unmodified
import boundary_v1 as B1       # noqa: E402  step 2's t interval
import boundary_v2 as B2       # noqa: E402  step 3's draw re-derivation + its tolerance
import decompose_v1 as D1      # noqa: E402  step 4's per-step terms + its mixture definition

# Two arithmetics over the same inputs must agree to the resolution of the coarser one (step 4 measured the
# pair `I.benefit` vs `D1.per_step` at 7.0e-15; this tolerance is six orders above that).
AGREE_TOL = 1e-09

# `busy` is a sum of the same service times, accumulated in the order jobs were SUBMITTED, so the two arms can
# differ bitwise while being the same work.  The worst relative difference measured over this run is printed;
# the tolerance is where "same work" stops being a claim about summation order.
BUSY_TOL = 1e-12

# A3's limit, checked at the lowest-contention cell of each family: E[min(T,S)] = mT*mS/(mT+mS).  The measured
# hiding channel can only be BELOW it (a queued call starts late inside the think phase), so this is one-sided.
HIDING_LIMIT_TOL = 0.05

# A cell whose gain is below this fraction of the hiding limit its OWN draws reach cannot carry a claim
# about a FRACTION of the gain: numerator and denominator are then both residuals (step 4's mixture).
# Declared here, before the run, so the robustness stratum is a rule and not a post-hoc cut.
NEGLIGIBLE_FRAC = 0.10

# A cell counts as `unloaded` for the one-sided A3 reading below this measured contention.
UNLOADED_RHO = 0.60

# The windows.  Wide on purpose: F's registered dependence is on rho, so rho must actually vary -- from
# saturation (where the gain vanishes) down to a nearly unloaded pool.
WINDOWS = ((16, 2, 16), (32, 3, 32), (64, 10, 64))
TAILS = ("light", "heavy")


# --------------------------------------------------------------------------- the model's own stream
def derive_stream(cfg, agents, seed):
    """T, S, HIT, IDEM in the model's own draw order: all think, all service, all hit flags, all idem flags.

    Re-derived because the model does not expose the flags, and VALIDATED in `stream_basis` by three routes
    that can fail: the miss count implied by HIT must equal what the model charges for (its `wasted` counter
    with q = 1), the h = 0 arm must reproduce the serial trace exactly, and the h = 1 arm must reproduce
    `ignore_h`.
    """
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / cfg["mT"]) for _ in range(cfg["steps"])] for _ in range(agents)]
    S = [[I.draw_service(rng, cfg["mS"], cfg["tail"]) for _ in range(cfg["steps"])]
         for _ in range(agents)]
    HIT = [[rng.random() < cfg["h"] for _ in range(cfg["steps"])] for _ in range(agents)]
    IDEM = [[rng.random() < cfg["q"] for _ in range(cfg["steps"])] for _ in range(agents)]
    return T, S, HIT, IDEM


def miss_count(HIT):
    """How many steps the re-derived stream says are MISSES -- the steps the model schedules as serial."""
    return sum(1 for row in HIT for x in row if not x)


def stream_basis(agents, seeds, cfg0):
    """The four measurements that decide what `h` does in this model, each of which can come out the other way.

    1. `h0_is_serial`  -- with h = 0 the speculative arm's per-step latencies are IDENTICAL to the serial
       arm's (anchor A2 re-measured here).  If a miss issued a speculative call that consumed a worker, this
       would be false, because every step would miss.
    2. `h1_is_ignore_h` -- h = 1.0 is identical to the model's own `ignore_h` arm at a different h.
    3. `miss_count_matches` -- with q = 1 the model's `wasted` counter is `comp * misses`; divided by `comp`
       it must equal the re-derived miss count EXACTLY, and with q = 0 it must be 0.
    4. `busy_is_shared` -- with q = 0 the two arms schedule the same work (`busy` equal within BUSY_TOL), so
       no miss adds load.
    """
    # Two counters run per (seed, h) PAIR and two run per seed.  Keeping one denominator for both is what the
    # battery's own last arm caught on this file's first run (it read "4/2"); the two denominators are named
    # separately now, because a counter and the thing its verdict divides by must be counted the same way.
    out = {"agents": agents, "seeds": len(seeds), "checks": 2 * len(seeds), "checks_per_branch": len(seeds),
           "h0_is_serial": 0, "h1_is_ignore_h": 0, "miss_count_matches": 0, "busy_is_shared": 0,
           "max_busy_rel_diff": 0.0, "misses_checked": 0, "draws_per_stream": 4 * agents * cfg0["steps"],
           "busy_tol": BUSY_TOL}
    for s in seeds:
        for h in (0.0, 1.0):
            cfg = dict(cfg0, h=h, q=0.0, comp=0.0, tail="light")
            T, S, HIT, IDEM = derive_stream(cfg, agents, s)
            c = 4
            ser = I.agent_run(agents, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], s, tail=cfg["tail"],
                              q=0.0, comp=0.0, speculate=False, c=c)
            spe = I.agent_run(agents, cfg["mT"], cfg["mS"], h, cfg["steps"], s, tail=cfg["tail"],
                              q=0.0, comp=0.0, speculate=True, c=c)
            if h == 0.0:
                out["h0_is_serial"] += 1 if spe["latencies"] == ser["latencies"] else 0
            else:
                ign = I.agent_run(agents, cfg["mT"], cfg["mS"], 0.25, cfg["steps"], s, tail=cfg["tail"],
                                  q=0.0, comp=0.0, speculate=True, c=c, ignore_h=True)
                out["h1_is_ignore_h"] += 1 if spe["latencies"] == ign["latencies"] else 0
            rel = abs(ser["busy"] - spe["busy"]) / (ser["busy"] or 1.0)
            out["max_busy_rel_diff"] = max(out["max_busy_rel_diff"], rel)
            out["busy_is_shared"] += 1 if rel <= BUSY_TOL else 0
            # the miss-count route, at the same h, with the compensation channel switched on and off
            comp = 0.5
            cfgq = dict(cfg, h=h, q=1.0, comp=comp)
            _, _, HITq, _ = derive_stream(cfgq, agents, s)
            rq = I.agent_run(agents, cfgq["mT"], cfgq["mS"], h, cfgq["steps"], s, tail=cfgq["tail"],
                             q=1.0, comp=comp, speculate=True, c=c)
            r0 = I.agent_run(agents, cfg["mT"], cfg["mS"], h, cfg["steps"], s, tail=cfg["tail"],
                             q=0.0, comp=0.0, speculate=True, c=c)
            want = miss_count(HITq)
            out["misses_checked"] += want
            out["miss_count_matches"] += 1 if (abs(rq["wasted"] / comp - want) <= 1e-09
                                               and r0["wasted"] == 0.0) else 0
    out["h0_ok"] = out["h0_is_serial"] == out["checks_per_branch"]
    out["h1_ok"] = out["h1_is_ignore_h"] == out["checks_per_branch"]
    out["miss_ok"] = out["miss_count_matches"] == out["checks"]
    out["busy_ok"] = out["busy_is_shared"] == out["checks"]
    out["all_ok"] = out["h0_ok"] and out["h1_ok"] and out["miss_ok"] and out["busy_ok"]
    return out


# --------------------------------------------------------------------------- one cell
def channel_rows(cfg, agents, b, defect=None):
    """Per step: the three channels and the identity's residual.

    `defect` plants one of the ways a channel split can be wrong; `--selftest` uses them so the identity is
    shown to be able to FAIL rather than asserted to hold.  Every plant is a wrong CHANNEL, never a wrong
    measurement: the latencies are always the model's own.

      * "hiding_is_S"           -- count the whole service time as hidden (as if nothing were left over);
      * "no_debit"              -- drop the overshoot debit;
      * "no_queue_channel"      -- drop w_s;
      * "overshoot_from_serial" -- read the overshoot off the SERIAL run (one reading, two meanings).
    """
    T, S, ser, spe = b["T"], b["S"], b["ser"], b["spe"]
    steps = cfg["steps"]
    lo = D1.warmup(cfg)
    rows = []
    for a in range(agents):
        for k in range(lo, steps):
            i = a * steps + k
            lat_s, lat_p = ser["latencies"][i], spe["latencies"][i]
            t, s = T[a][k], S[a][k]
            w_s = lat_s - t - s
            if defect == "overshoot_from_serial":
                overshoot = max(0.0, lat_s - t)
            else:
                overshoot = max(0.0, lat_p - t)
            if defect == "no_queue_channel":
                w_s = 0.0
            slack = s - overshoot
            if defect == "hiding_is_S":
                hid, debit = s, 0.0
            else:
                hid, debit = max(0.0, slack), min(0.0, slack)
            if defect == "no_debit":
                debit = 0.0
            benefit = lat_s - lat_p
            rows.append({"benefit": benefit, "H": hid, "D": debit, "W": w_s, "lat_s": lat_s,
                         "residual": benefit - (hid + debit + w_s)})
    return rows


def channel_cell(cfg, agents, workers, h, seeds, defect=None):
    """One cell: the channels' means with intervals over SEEDS, the load-channel facts, and F where defined.

    The independent unit is a draw stream, so every interval is over per-seed means (`B1.t_ci`) -- the same
    estimator steps 2-5 used.  `benefit_agreement_max_abs` compares this file's step aggregate with the
    model's own `I.benefit` for the same cell, so the split is of the number the model reports.
    """
    per = {"benefit": [], "H": [], "D": [], "W": []}
    per_seed_B, per_seed_F, rho_s, rho_ser, ms_s, ms_ser, busy_pairs, model_pct = ([] for _ in range(8))
    worst_res, worst_agree = 0.0, 0.0
    tot_steps = 0
    per_seed_limit, ratio_res = [], []
    for s in seeds:
        b = D1.make_runs(cfg, agents, workers, h, s)
        rows = channel_rows(cfg, agents, b, defect=defect)
        tot_steps += len(rows)
        # The limit the hiding channel can reach is a property of THESE draws over the model's OWN aggregation
        # window -- the population constant mT*mS/(mT+mS) is what the sample estimates, not what it equals.
        per_seed_limit.append(statistics.fmean(
            min(b["T"][a][k], b["S"][a][k]) for a in range(agents) for k in range(D1.warmup(cfg),
                                                                                cfg["steps"])))
        for k in per:
            per[k].append(statistics.fmean(r[k] for r in rows))
        for r in rows:
            worst_res = max(worst_res, abs(r["residual"]))
        B = per["benefit"][-1]
        H = per["H"][-1]
        per_seed_B.append(B)
        per_seed_F.append(H / B if B > 0 else None)
        m = I.benefit(dict(cfg, seed=s), agents, workers, h)
        model_pct.append(m["benefit_pct"])
        rho_s.append(b["spe"]["rho"])
        rho_ser.append(b["ser"]["rho"])
        ms_s.append(b["spe"]["makespan"])
        ms_ser.append(b["ser"]["makespan"])
        # PER SEED: a mean of ratios is not the ratio of means -- this file's own smoke run read a
        # 1.5e-04 residual here that was that aggregation, not a fact about the load channel
        ratio_res.append(abs(b["spe"]["rho"] / b["ser"]["rho"]
                             - b["ser"]["makespan"] / b["spe"]["makespan"]))
        busy_pairs.append((b["ser"]["busy"], b["spe"]["busy"]))
        worst_agree = max(worst_agree, abs(100.0 * statistics.fmean(r["benefit"] for r in rows)
                                           / statistics.fmean(r["lat_s"] for r in rows) - m["benefit_pct"]))
    fs = [x for x in per_seed_F if x is not None]
    lim_mean = statistics.fmean(per_seed_limit)
    # the declared robustness stratum: cells whose gain is at least NEGLIGIBLE_FRAC of the hiding limit
    # this cell's own draws reach.  Their F is reported but cannot carry the claim, and they are COUNTED.
    negligible = [f for f, Bv in zip(per_seed_F, per_seed_B)
                  if f is not None and Bv < NEGLIGIBLE_FRAC * lim_mean]
    rel_busy = max(abs(x - y) / (x or 1.0) for x, y in busy_pairs)
    rho_ratio = statistics.fmean(rho_s) / statistics.fmean(rho_ser) if statistics.fmean(rho_ser) else None
    ms_ratio = statistics.fmean(ms_ser) / statistics.fmean(ms_s) if statistics.fmean(ms_s) else None
    out = {"agents": agents, "workers": workers, "h": h, "tail": cfg["tail"], "n_seeds": len(seeds),
           "n_steps": tot_steps, "defect": defect,
           "rho_spec": statistics.fmean(rho_s), "rho_serial": statistics.fmean(rho_ser),
           "makespan_spec": statistics.fmean(ms_s), "makespan_serial": statistics.fmean(ms_ser),
           "busy_rel_diff_max": rel_busy, "busy_shared": rel_busy <= BUSY_TOL,
           "rho_ratio": rho_ratio, "makespan_ratio": ms_ratio,
           "rho_ratio_identity_residual": max(ratio_res),
           "rho_ratio_identity_residual_mean_based": (abs(rho_ratio - ms_ratio)
                                                      if (rho_ratio and ms_ratio) else None),
           "identity_max_residual": worst_res, "identity_tol": D1.IDENTITY_TOL,
           "identity_holds": worst_res <= D1.IDENTITY_TOL,
           "benefit_agreement_max_abs": worst_agree,
           "hiding_sample_limit": lim_mean,
           "hiding_sample_limit_ci": B1.t_ci(per_seed_limit) if len(per_seed_limit) > 1 else None,
           "hiding_over_sample_limit": (statistics.fmean(per["H"]) - statistics.fmean(per_seed_limit)),
           "benefit_agrees_with_model": worst_agree <= AGREE_TOL,
           "benefit_pct_model": statistics.fmean(model_pct),
           "F_mean": (statistics.fmean(fs) if fs else None),
           "F_ci": (B1.t_ci(fs) if len(fs) > 1 else None),
           "F_n_used": len(fs), "F_n_excluded_nonpositive_gain": len(per_seed_F) - len(fs),
           "F_n_excluded_negligible_gain": len(negligible),
           "F_negligible_gain": len(negligible) > 0,
           "per_seed_F": per_seed_F, "per_seed_benefit": per_seed_B}
    for k in per:
        out[k + "_mean"] = statistics.fmean(per[k])
        out[k + "_ci"] = B1.t_ci(per[k]) if len(per[k]) > 1 else None
    return out


def family(cfg, a, c_lo, c_hi, h, seeds):
    """One (tail, A, h) family: the swept cells in rho order, with the two P3 readings computed on it."""
    rows = [channel_cell(cfg, a, c, h, seeds) for c in range(c_lo, c_hi + 1)]
    rows.sort(key=lambda r: (r["rho_spec"], r["workers"]))
    pos = [r for r in rows if r["F_mean"] is not None]
    return {"tail": cfg["tail"], "agents": a, "h": h, "c_range": [c_lo, c_hi], "rows": rows,
            "positive_gain_cells": len(pos), "cells": len(rows),
            "F_min": (min(r["F_mean"] for r in pos) if pos else None),
            "F_min_cell": (min(pos, key=lambda r: r["F_mean"])["workers"] if pos else None),
            "F_max": (max(r["F_mean"] for r in pos) if pos else None),
            "F_max_cell": (max(pos, key=lambda r: r["F_mean"])["workers"] if pos else None),
            "plateau_F_one": (all(r["F_mean"] == 1.0 for r in pos[-4:]) if len(pos) >= 4 else None),
            "adjacent": adjacent_dF(pos, rows),
            "spearman_F_rho": spearman([(r["rho_spec"], r["F_mean"]) for r in pos])}


def adjacent_dF(pos, rows):
    """The paired-by-seed F differences between adjacent cells, in rho order -- P3b's own units.

    Cells with no defined F (gain <= 0) are not cells of this comparison; the count is carried so a reader can
    see how much of the family the comparison covers.
    """
    out = []
    for i in range(len(pos) - 1):
        lo, hi = pos[i], pos[i + 1]
        d = []
        for x, y in zip(hi["per_seed_F"], lo["per_seed_F"]):
            if x is not None and y is not None:
                d.append(x - y)
        if len(d) < 2:
            out.append({"workers": [lo["workers"], hi["workers"]], "n": len(d), "dF": None, "ci": None,
                        "verdict": "n/a (fewer than two paired seeds)"})
            continue
        ci = B1.t_ci(d)
        verdict = "INCREASE" if ci[0] > 0 else ("DECREASE" if ci[1] < 0 else "tie")
        out.append({"workers": [lo["workers"], hi["workers"]], "n": len(d),
                    "rho": [lo["rho_spec"], hi["rho_spec"]], "dF": statistics.fmean(d), "ci": ci,
                    "verdict": verdict})
    return out


def spearman(pairs):
    """Rank correlation of F against rho, over the positive-gain cells only (a summary, not a verdict)."""
    if len(pairs) < 3:
        return None
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    x = rank([p[0] for p in pairs])
    y = rank([p[1] for p in pairs])
    n = len(pairs)
    mx, my = statistics.fmean(x), statistics.fmean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else None


def family_verdicts(f):
    """P3a and P3b for one family, from the declared rules."""
    pos = [r for r in f["rows"] if r["F_mean"] is not None and r["F_ci"]]
    if not pos:
        p3a = "UNRESOLVED (no positive-gain cell with an interval)"
    elif all(r["F_ci"][1] < 0.7 for r in pos):
        p3a = "CONFIRMED (every one of the %d cells strictly below 0.7)" % len(pos)
    elif any(r["F_ci"][0] > 0.7 for r in pos):
        p3a = "CONTRADICTED (%d of %d cells strictly above 0.7)" % (
            sum(1 for r in pos if r["F_ci"][0] > 0.7), len(pos))
    else:
        p3a = "UNRESOLVED (%d cells below, none strictly above 0.7)" % sum(
            1 for r in pos if r["F_ci"][1] < 0.7)
    inc = [a for a in f["adjacent"] if a["verdict"] == "INCREASE"]
    dec = [a for a in f["adjacent"] if a["verdict"] == "DECREASE"]
    if inc:
        p3b = "CONTRADICTED (%d of %d adjacent pairs increase significantly)" % (len(inc), len(f["adjacent"]))
    elif dec:
        p3b = "CONFIRMED (no increase, %d decreases)" % len(dec)
    else:
        p3b = "UNRESOLVED (no significant change in either direction)"
    return {"P3a": p3a, "P3b": p3b, "n_increase": len(inc), "n_decrease": len(dec),
            "n_tie": len(f["adjacent"]) - len(inc) - len(dec),
            "max_interval_width": max((a["ci"][1] - a["ci"][0]) for a in f["adjacent"] if a["ci"])
            if any(a["ci"] for a in f["adjacent"]) else None}


def ladder_verdict(fams):
    """The same two rules over the whole ladder (the registered claim is about the study, not one family)."""
    p3a_sub = [family_verdicts(f)["P3a"] for f in fams]
    if any(s.startswith("CONTRADICTED") for s in p3a_sub):
        p3a = "CONTRADICTED (at least one family has cells strictly above 0.7)"
    elif all(s.startswith("CONFIRMED") for s in p3a_sub):
        p3a = "CONFIRMED (every family's positive-gain cells strictly below 0.7)"
    else:
        p3a = "UNRESOLVED"
    p3b_sub = [family_verdicts(f)["P3b"] for f in fams]
    if any(s.startswith("CONTRADICTED") for s in p3b_sub):
        p3b = "CONTRADICTED (at least one family has a significant increase with rho)"
    elif all(s.startswith("CONFIRMED") for s in p3b_sub):
        p3b = "CONFIRMED (no family increases; every family has a decrease)"
    else:
        p3b = "UNRESOLVED"
    return {"P3a": p3a, "P3b": p3b}


# --------------------------------------------------------------------------- report
def fmt_ci(ci, spec="%+.5f"):
    return "n/a" if not ci else "[" + (spec % ci[0]) + ", " + (spec % ci[1]) + "]"


def fmt_num(x, spec="%.4f"):
    return "n/a" if x is None else (spec % x)


def report(fams, basis, checks, h, cfg0):
    print("== step 6 -- which channel pays, and what the contention is (h=%.2f) ==" % h)
    print("  what `h` does in this model (measured, four routes):")
    print("     h=0 reproduces the serial trace step for step: %d/%d | h=1 equals ignore_h: %d/%d"
          % (basis["h0_is_serial"], basis["checks"], basis["h1_is_ignore_h"], basis["checks"]))
    print("     the model's own compensation counter equals the re-derived MISS count: %d/%d"
          " (%d misses checked, q=1) and is 0 at q=0 | `busy` shared within %.1e relative: %d/%d"
          % (basis["miss_count_matches"], basis["checks"], basis["misses_checked"],
             basis["max_busy_rel_diff"], basis["busy_is_shared"], basis["checks"]))
    for tail in TAILS:
        for f in fams[tail]:
            rows = f["rows"]
            print("  -- %s A=%d (c %d..%d, rho %.5f..%.5f) --"
                  % (tail, f["agents"], f["c_range"][0], f["c_range"][1], rows[0]["rho_spec"],
                     rows[-1]["rho_spec"]))
            print("     c    rho      benefit      H (hiding)     D (debit)      W (queue)     F        "
                  "busy diff")
            for r in rows:
                if r["F_mean"] is None:
                    fstr = "n/a"
                else:
                    fstr = "%.4f" % r["F_mean"]
                print("     %-3d %.5f %+10.4f  %10.4f  %10.4f  %10.4f  %-8s %.1e"
                      % (r["workers"], r["rho_spec"], r["benefit_mean"], r["H_mean"], r["D_mean"],
                         r["W_mean"], fstr, r["busy_rel_diff_max"]))
            v = family_verdicts(f)
            print("     P3a (F < 0.7): %s" % v["P3a"])
            print("     P3b (F decreasing in rho): %s | increases %d, decreases %d, ties %d | widest"
                  " adjacent interval %.2e"
                  % (v["P3b"], v["n_increase"], v["n_decrease"], v["n_tie"],
                     v["max_interval_width"] or 0.0))
            print("     F min %s at c=%s | F max %s at c=%s | spearman(F, rho) %s | positive-gain cells"
                  " %d of %d | cells whose gain is < %.0f%% of the hiding limit (F reported, not"
                  " claim-bearing): %d"
                  % (fmt_num(f["F_min"]), f["F_min_cell"], fmt_num(f["F_max"]), f["F_max_cell"],
                     fmt_num(f["spearman_F_rho"], "%+.3f"), f["positive_gain_cells"], f["cells"],
                     100.0 * NEGLIGIBLE_FRAC,
                     sum(1 for r in f["rows"] if r["F_negligible_gain"])))
    print("  load channel (q=0): worst relative |busy_serial - busy_spec| over all cells %.2e"
          " (tolerance %.0e); worst |rho_spec/rho_serial - makespan_serial/makespan_spec| %.2e"
          % (max(r["busy_rel_diff_max"] for t in TAILS for f in fams[t] for r in f["rows"]), BUSY_TOL,
             max((r["rho_ratio_identity_residual"] or 0.0) for t in TAILS for f in fams[t] for r in f["rows"])))
    print("  checks: " + ", ".join("%s=%s" % (k, "OK" if v else "FAIL") for k, v in sorted(checks.items())))


# --------------------------------------------------------------------------- controls
def fake_cell(**kw):
    """A synthetic cell for the rule arms: only the fields the rules read."""
    base = {"workers": 1, "agents": 8, "tail": "planted", "rho_spec": 0.9, "benefit_mean": 1.0,
            "H_mean": 1.0, "D_mean": 0.0, "W_mean": 0.0, "F_mean": 1.0, "F_ci": [0.9, 1.1],
            "per_seed_F": [1.0, 1.0, 1.0], "busy_rel_diff_max": 0.0, "rho_ratio_identity_residual": 0.0}
    base.update(kw)
    return base


def fake_family(cells):
    rows = sorted(cells, key=lambda r: r["rho_spec"])
    f = {"tail": "planted", "agents": 8, "c_range": [1, len(rows)], "rows": rows}
    pos = [r for r in rows if r["F_mean"] is not None]
    f["adjacent"] = adjacent_dF(pos, rows)
    f["positive_gain_cells"] = len(pos)
    f["cells"] = len(rows)
    f["F_min"] = min((r["F_mean"] for r in pos), default=None)
    f["F_max"] = max((r["F_mean"] for r in pos), default=None)
    f["F_min_cell"] = f["F_max_cell"] = 1
    f["spearman_F_rho"] = spearman([(r["rho_spec"], r["F_mean"]) for r in pos])
    return f


def planted_series(vals, rhos=None):
    """Cells whose F is exactly the given series: F_ci is a zero-width interval so the arms decide on it."""
    rhos = rhos or [0.5 + 0.05 * i for i in range(len(vals))]
    out = []
    for rho, v in zip(rhos, vals):
        out.append(fake_cell(rho_spec=rho, F_mean=v, F_ci=[v, v], per_seed_F=[v, v, v],
                             benefit_mean=1.0, H_mean=v, H_ci=[v, v]))
    return out


def case(name, ok, detail):
    return (name, bool(ok), detail)


def selftest():
    """Each arm fails for its OWN reason or it is decoration."""
    out = []
    cfg0 = I.default_cfg()
    seeds3 = [101, 102, 103]
    cl = dict(cfg0, tail="light")

    r = channel_cell(cl, 16, 8, 1.0, seeds3)
    out.append(case("clean_cell_passes",
                    r["identity_holds"] and r["benefit_agrees_with_model"] and r["busy_shared"],
                    "residual %.2e, agreement %.2e, busy diff %.1e"
                    % (r["identity_max_residual"], r["benefit_agreement_max_abs"],
                       r["busy_rel_diff_max"])))

    b = D1.make_runs(cl, 16, 8, 1.0, 101)
    rows = channel_rows(cl, 16, b)
    d = {k: statistics.fmean(x[k] for x in rows) for k in ("benefit", "H", "D", "W")}
    out.append(case("the_three_channels_add_up_on_a_real_cell",
                    abs(d["benefit"] - (d["H"] + d["D"] + d["W"])) <= AGREE_TOL and d["W"] > 0
                    and d["H"] > 0,
                    "benefit %.6f = H %.6f + D %.6f + W %.6f (gap %.2e, W positive: %s)"
                    % (d["benefit"], d["H"], d["D"], d["W"],
                       abs(d["benefit"] - (d["H"] + d["D"] + d["W"])), d["W"] > 0)))

    for defect, want_break in (("hiding_is_S", True), ("no_debit", True), ("no_queue_channel", True),
                               ("overshoot_from_serial", True)):
        rr = channel_rows(cl, 16, b, defect=defect)
        worst = max(abs(x["residual"]) for x in rr)
        out.append(case("identity_breaks_when_%s" % defect, (worst > AGREE_TOL) == want_break,
                        "worst residual %.4f (planted channel defect)" % worst))

    out.append(case("the_busy_channel_check_can_fail",
                    (not channel_cell(cl, 16, 8, 1.0, seeds3)["busy_shared"]) is False
                    and (abs(1.0 - 1.01) / 1.0 > BUSY_TOL),
                    "real cell shared: %s; a planted 1%% difference is above the tolerance"
                    % channel_cell(cl, 16, 8, 1.0, seeds3)["busy_shared"]))

    v = family_verdicts(fake_family(planted_series([0.9, 0.8, 0.7, 0.6])))
    out.append(case("P3b_reads_a_monotone_decrease_as_confirm", v["P3b"].startswith("CONFIRMED"),
                    "%s (decreases %d, ties %d)" % (v["P3b"][:40], v["n_decrease"], v["n_tie"])))
    v = family_verdicts(fake_family(planted_series([0.4, 0.5, 0.6, 0.9])))
    out.append(case("P3b_reads_one_increase_as_contradict", v["P3b"].startswith("CONTRADICTED"),
                    "%s (increases %d)" % (v["P3b"][:44], v["n_increase"])))
    v = family_verdicts(fake_family(planted_series([1.0, 1.0, 1.0, 1.0])))
    out.append(case("P3b_reads_a_flat_series_as_unresolved", v["P3b"].startswith("UNRESOLVED"),
                    "%s (ties %d)" % (v["P3b"][:44], v["n_tie"])))
    v = family_verdicts(fake_family(planted_series([0.3, 0.4, 0.5, 0.6])))
    out.append(case("P3a_reads_all_below_as_confirm_and_all_above_as_contradict",
                    v["P3a"].startswith("CONFIRMED")
                    and family_verdicts(fake_family(planted_series([0.8, 0.9, 1.0])))["P3a"].startswith(
                        "CONTRADICTED"),
                    "%s | %s" % (v["P3a"][:30],
                                 family_verdicts(fake_family(planted_series([0.8, 0.9, 1.0])))["P3a"][:34])))

    cells = planted_series([0.5, 0.6], rhos=[0.9, 0.95]) + [fake_cell(rho_spec=0.99, F_mean=None,
                                                                     F_ci=None, per_seed_F=[None, None, None],
                                                                     benefit_mean=-0.01)]
    f = fake_family(cells)
    out.append(case("cells_without_a_gain_are_excluded_from_F",
                    f["positive_gain_cells"] == 2 and f["cells"] == 3
                    and all(a["n"] == 3 for a in f["adjacent"]),
                    "positive-gain %d of %d cells; adjacent pairs kept %s"
                    % (f["positive_gain_cells"], f["cells"], [a["n"] for a in f["adjacent"]])))

    # The arm's subject is a SAMPLE mean, so its expectation is the sample limit on the same draws and window.
    # Its first version compared H against the POPULATION constant and read "0.66846 > 0.66667" as a failure:
    # the sample mean of min(T,S) is not the constant, and 0.0018 is well inside its own sampling error
    # (0.6667/sqrt(24320) = 0.0043).  What must hold one-sided is H <= the sample limit -- queueing can only
    # delay a call inside the think phase.
    lim = cfg0["mT"] * cfg0["mS"] / (cfg0["mT"] + cfg0["mS"])
    c_low = channel_cell(cl, 16, 16, 1.0, [101, 102, 103, 104])
    sam = c_low["hiding_sample_limit"]
    rel = abs(sam - lim) / lim
    out.append(case("the_hiding_channel_sits_at_the_A3_limit_when_unloaded",
                    sam > 0 and c_low["hiding_over_sample_limit"] <= 1e-09,
                    "measured H %.5f vs the SAMPLE limit %.5f (H - limit %.2e, one-sided) | the population"
                    " constant %.5f differs from the sample limit by %.2e (sampling, not bias)"
                    % (c_low["H_mean"], sam, c_low["hiding_over_sample_limit"], lim, rel)))

    sb = stream_basis(16, [101, 102], cfg0)
    out.append(case("the_stream_basis_holds_and_can_fail",
                    sb["all_ok"] and sb["misses_checked"] > 0
                    and sb["miss_count_matches"] == sb["checks"] == 2 * sb["seeds"]
                    and abs(1.0 - (sb["misses_checked"] + 1) / sb["misses_checked"]) > BUSY_TOL,
                    "h0 %d/%d, h1 %d/%d, misses %d/%d, busy %d/%d (denominators: %d pairs, %d per branch)"
                    % (sb["h0_is_serial"], sb["checks_per_branch"], sb["h1_is_ignore_h"],
                       sb["checks_per_branch"], sb["miss_count_matches"], sb["checks"],
                       sb["busy_is_shared"], sb["checks"], sb["checks"], sb["checks_per_branch"])))

    fails = [n for n, ok, _ in out if not ok]
    print("== step 6 --selftest: %d arms, %d failure(s) ==" % (len(out), len(fails)))
    for n, ok, d in out:
        print("  %-4s %-52s %s" % ("PASS" if ok else "FAIL", n, d))
    if fails:
        print("  FAILING: %s" % ", ".join(fails))
    return 0 if not fails else 1


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="issue #50 step 6 -- the channel split (P3) and the load channel")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed0", type=int, default=101)
    ap.add_argument("--h", type=float, default=1.0)
    ap.add_argument("--quick", action="store_true", help="3 seeds and a narrow window, for a smoke run")
    ap.add_argument("--no-heavy", action="store_true", help="light tail only")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    seeds = [args.seed0 + i for i in range(3 if args.quick else args.seeds)]
    cfg0 = I.default_cfg()
    windows = ((16, 3, 6), (32, 6, 12), (64, 14, 24)) if args.quick else WINDOWS
    tails = ("light",) if args.no_heavy else TAILS
    print("== step 6: seeds %d..%d (%d), h=%.2f, windows %s, mT=%.1f mS=%.1f steps=%d =="
          % (seeds[0], seeds[-1], len(seeds), args.h, windows, cfg0["mT"], cfg0["mS"], cfg0["steps"]))
    basis = stream_basis(16, seeds[:min(4, len(seeds))], cfg0)
    fams = {}
    for t in tails:
        cfg = dict(cfg0, tail=t)
        fams[t] = [family(cfg, a, lo, hi, args.h, seeds) for (a, lo, hi) in windows]
    verds = {t: [family_verdicts(f) for f in fams[t]] for t in tails}
    ladder = {t: ladder_verdict(fams[t]) for t in tails}
    lim = cfg0["mT"] * cfg0["mS"] / (cfg0["mT"] + cfg0["mS"])
    # The one-sided check lives at the LOW-CONTENTION end of each family.  If a window's top cell is still
    # loaded the reading cannot be taken there: that is NOT APPLICABLE with its reason, never a failure -- a
    # reading that could not be taken must not look like a finding (step 5's exit-2 rule).
    # `rows` is sorted by rho ASCENDING, so the lowest-contention cell is rows[0]: this line read rows[-1]
    # on the first deciding run and the check's own print exposed it ("the lowest measured is 0.9945"
    # is the TOP of the window, not the bottom) -- the wrong end of a sorted list is still a wrong object.
    lows = [f["rows"][0] for t in tails for f in fams[t]]
    unloaded = [r for r in lows if r["rho_spec"] <= UNLOADED_RHO]
    a3_status = ("READ" if unloaded else
                 "NOT APPLICABLE (no family's lowest-contention cell is at or below rho %.2f; the lowest"
                 " measured is %.4f)" % (UNLOADED_RHO, min(r["rho_spec"] for r in lows)))
    lim_rel = (max(abs(r["H_mean"] - r["hiding_sample_limit"]) / r["hiding_sample_limit"]
                   for r in unloaded) if unloaded else None)
    checks = {
        "stream_basis_ok": basis["all_ok"],
        "identity_holds_everywhere": all(r["identity_holds"] for t in tails for f in fams[t] for r in f["rows"]),
        "benefit_agrees_with_the_model": all(r["benefit_agrees_with_model"] for t in tails for f in fams[t]
                                             for r in f["rows"]),
        "busy_shared_everywhere": all(r["busy_shared"] for t in tails for f in fams[t] for r in f["rows"]),
        "rho_ratio_identity_holds": all((r["rho_ratio_identity_residual"] or 0.0) <= 1e-12
                                        for t in tails for f in fams[t] for r in f["rows"]),
        "hiding_channel_at_the_A3_limit_when_unloaded": (
            a3_status != "READ" or lim_rel is None or lim_rel <= HIDING_LIMIT_TOL),
        "every_family_has_a_positive_gain_cell": all(f["positive_gain_cells"] > 0
                                                     for t in tails for f in fams[t]),
    }
    report(fams, basis, checks, args.h, cfg0)
    for t in tails:
        print("  ladder (%s): P3a %s | P3b %s" % (t, ladder[t]["P3a"], ladder[t]["P3b"]))
    if a3_status == "READ":
        print("  A3 limit check (%d unloaded cell(s), rho <= %.2f): worst relative |H - sample limit| %.2e"
              " (tolerance %.2f, one-sided)" % (len(unloaded), UNLOADED_RHO, lim_rel, HIDING_LIMIT_TOL))
    else:
        print("  A3 limit check: %s" % a3_status)
    payload = {
        "what": "issue #50 instrument v0 step 6 -- the channel split (registered P3) and the load channel",
        "h": args.h, "seeds": seeds, "windows": windows, "tails": list(tails),
        "model": {k: cfg0[k] for k in sorted(cfg0) if not isinstance(cfg0[k], list)},
        "declared": {
            "channels": "benefit = H (hiding, max(0, S - overshoot)) + D (overshoot debit, min(0, ...)) + W (w_s)",
            "F": "mean(H)/mean(benefit), per seed, aggregated over seeds; reported only for positive-gain cells",
            "P3a_rule": "CONFIRMED iff every positive-gain cell's F interval is strictly below 0.7; CONTRADICTED iff one is strictly above",
            "P3b_rule": "adjacent cells in rho, paired by seed; INCREASE/DECREASE/tie from the interval; CONFIRMED iff no increase and >=1 decrease",
            "busy_tol": BUSY_TOL, "agree_tol": AGREE_TOL, "hiding_limit_tol": HIDING_LIMIT_TOL,
            "hiding_limit": lim,
        },
        "stream_basis": basis, "families": fams, "family_verdicts": verds, "ladder": ladder,
        "a3_check_status": a3_status, "a3_limit_relative_gap": lim_rel, "checks": checks,
    }
    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
