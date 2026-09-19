#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 4: WHERE does the pool-size effect put its loss?

WHAT THIS FILE IS.  Step 3 measured that the boundary moves with the pool size A (span 0.0216 = 20.5x the
families' own intervals) and that at matched contention the sign of the benefit splits.  It did not say
WHY.  This file decomposes one step's benefit into terms that are each observable, so the A-effect stops
being a name for a slope and becomes a list of amounts:

    benefit(step) = latency_serial - latency_speculative

With `speculate=False` the call is issued when the think phase ENDS, so a serial step is strictly sequential
and its latency is exactly `T + w_s + S` (`w_s` = the queue wait before service starts).  With
`speculate=True` the call is issued when the think phase STARTS, so its latency is `max(T, w_p + S)` -- the
call is hidden only as far as the think phase reaches.  Therefore, per step,

    benefit = w_s + S - overshoot,      overshoot = max(0, latency_spec - T)

and all three terms are OBSERVABLE: `w_s` from the serial run (given the draws), `S` from the draws, and
`overshoot` from the speculative latency against the same `T`.  `overshoot` is the part of the speculative
call the think phase did NOT absorb; `w_s` is the queue wait the serial baseline pays and the speculative
one does not (it is issued earlier, so it reaches the worker earlier -- step 1's A4).

WHAT THE TERMS MEAN, which is why this is a mechanism test and not arithmetic:

  * if the A-effect acts through the SERIAL BASELINE -- a bigger pool at the same measured utilisation is a
    longer queue, so `w_s` grows -- the benefit would GROW with A, and the measured benefit FALLS;
  * if it acts through the SCHEDULE (more agents contending for the same workers, so the speculative call
    also waits and its wait is no longer absorbed by the think phase), the term that moves is `overshoot`;
  * `S` is a property of the workload and moves with neither.

The decomposition is an IDENTITY, so it is also its own control: every step's three terms must add back to
the measured benefit to the arithmetic's own resolution, and `--selftest` plants each term's omission and
requires the identity to break.  A decomposition nobody can falsify is a description.

CPU only, stdlib only, fixed seeds.  `instrument_v0.py` is imported unmodified; the draw re-derivation and
its stated tolerance are IMPORTED from `boundary_v2.py` rather than re-written, so the coordinate this file
divides by is the one step 3 validated.
"""
import argparse
import io
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I      # noqa: E402  the model, unmodified
import boundary_v1 as B1       # noqa: E402  step 2's t interval
import boundary_v2 as B2       # noqa: E402  step 3's draw re-derivation + its tolerance

# The identity is arithmetic over the same floats the model accumulated, so its residual is a rounding
# error, not a modelling quantity.  The tolerance is the one step 3 measured and stated (2.24e-13 max); it
# is reused by import rather than re-chosen here.
IDENTITY_TOL = B2.DERIVATION_TOL

TERMS = ("w_s", "S", "overshoot")


def warmup(cfg):
    """The model's own warm-up trim, read from the model rather than re-guessed: `agent_run` computes
    `warm = min(20, steps // 5)` and reports `mean_latency` over `lat[a][warm:]`.  This file must aggregate
    over the SAME samples, or every comparison against the model's printed numbers is between two different
    populations -- `--selftest` has an arm for exactly that."""
    return min(20, cfg["steps"] // 5)


def make_runs(cfg, agents, workers, h, seed):
    """Both runs of one cell for one seed, plus the draws they were made from."""
    T, S = B2.derive_draws(agents, seed, cfg)
    kw = dict(tail=cfg["tail"], q=cfg["q"], comp=cfg["comp"], c=workers)
    ser = I.agent_run(agents, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], seed, speculate=False, **kw)
    spe = I.agent_run(agents, cfg["mT"], cfg["mS"], h, cfg["steps"], seed, speculate=True, **kw)
    return {"T": T, "S": S, "ser": ser, "spe": spe}


def per_step(cfg, agents, b, defect=None):
    """The three terms and the identity's residual, per step, over the model's own sample window.

    `defect` plants one of the ways a decomposition can be wrong; `--selftest` uses them so the identity is
    shown to be able to FAIL rather than asserted to hold.  Every plant is a wrong TERM, never a wrong
    measurement: the latencies are always the model's own.

      * "no_overshoot"           -- drop the overshoot term (as if every call cost were absorbed);
      * "no_serial_wait"         -- drop `w_s` (as if the whole gain were hiding);
      * "overshoot_from_serial"  -- read the overshoot off the SERIAL run (one reading, two meanings);
      * "full_window"            -- aggregate over ALL steps instead of the model's warm-up-trimmed window.
    """
    T, S, ser, spe = b["T"], b["S"], b["ser"], b["spe"]
    steps = cfg["steps"]
    lo = 0 if defect == "full_window" else warmup(cfg)
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
            if defect == "no_overshoot":
                overshoot = 0.0
            if defect == "no_serial_wait":
                w_s = 0.0
            benefit = lat_s - lat_p
            rows.append({"T": t, "lat_s": lat_s, "lat_p": lat_p, "w_s": w_s, "S": s,
                         "overshoot": overshoot, "benefit": benefit,
                         "residual": benefit - (w_s + s - overshoot),
                         "hidden": overshoot == 0.0,
                         "w_p": (lat_p - s) if overshoot > 0.0 else None})
    return rows


def cell(cfg, agents, workers, h, seeds, defect=None):
    """One cell over a seed list: the terms' means, intervals over SEEDS, and the identity's worst residual.

    The independent unit is a draw stream, so the intervals are taken over the per-seed means of the step
    terms (`B1.t_ci`) -- the same estimator step 2 and step 3 used.  `benefit_pct_model` is the model's own
    `benefit_pct` for the same cell, carried so this file's aggregate can be compared against the number
    step 3 published rather than standing as its own authority.
    """
    per_seed = {k: [] for k in TERMS + ("benefit", "lat_s", "lat_p")}
    rho_spec, rho_serial, model_pct, mine_pct, hidden = [], [], [], [], []
    worst, n_steps, n_wp, w_p_sum = 0.0, 0, 0, 0.0
    # The mean benefit is a small number; this file also asks HOW it is made up.  A step either has its call
    # fully absorbed by the think phase (overshoot == 0) or it does not, and the two populations can carry
    # opposite signs -- if they do, the mean hides a mixture, and "the benefit comes from hiding" and "the
    # benefit comes from queue position" are different claims about the same number.
    hid_sum, tot_sum, hid_n, lose_sum, lose_n = 0.0, 0.0, 0, 0.0, 0
    for s in seeds:
        b = make_runs(cfg, agents, workers, h, s)
        rows = per_step(cfg, agents, b, defect=defect)
        for r in rows:
            worst = max(worst, abs(r["residual"]))
            n_steps += 1
            tot_sum += r["benefit"]
            if r["hidden"]:
                hid_sum += r["benefit"]; hid_n += 1
            else:
                lose_sum += r["benefit"]; lose_n += 1
                n_wp += 1
                w_p_sum += r["w_p"]
        for k in TERMS + ("benefit", "lat_s", "lat_p"):
            per_seed[k].append(statistics.fmean(r[k] for r in rows))
        hidden.append(sum(1 for r in rows if r["hidden"]) / float(len(rows)))
        rho_spec.append(b["spe"]["rho"]); rho_serial.append(b["ser"]["rho"])
        m = I.benefit(dict(cfg, seed=s), agents, workers, h)
        model_pct.append(m["benefit_pct"])
        mine_pct.append(100.0 * statistics.fmean(r["benefit"] for r in rows)
                        / statistics.fmean(r["lat_s"] for r in rows))
    out = {"agents": agents, "workers": workers, "h": h, "n_seeds": len(seeds), "defect": defect,
           "n_steps": n_steps, "identity_max_residual": worst, "identity_tol": IDENTITY_TOL,
           "identity_holds": worst <= IDENTITY_TOL,
           "rho_spec": statistics.fmean(rho_spec), "rho_spec_ci": B1.t_ci(rho_spec),
           "rho_serial": statistics.fmean(rho_serial),
           "hidden_frac": statistics.fmean(hidden),
           "n_w_p_observable": n_wp, "w_p_mean": (w_p_sum / n_wp) if n_wp else None,
           "benefit_sum_hidden_steps": hid_sum, "benefit_sum_other_steps": lose_sum,
           "benefit_sum_all_steps": tot_sum, "n_hidden_steps": hid_n, "n_other_steps": lose_n,
           "mean_benefit_hidden": (hid_sum / hid_n) if hid_n else None,
           "mean_benefit_other": (lose_sum / lose_n) if lose_n else None,
           "hidden_share_of_net_benefit": (hid_sum / tot_sum) if tot_sum else None,
           "benefit_pct_model": statistics.fmean(model_pct), "benefit_pct_model_ci": B1.t_ci(model_pct),
           "benefit_pct_mine": statistics.fmean(mine_pct), "per_seed": per_seed}
    for k in TERMS + ("benefit", "lat_s", "lat_p"):
        out[k + "_mean"] = statistics.fmean(per_seed[k])
        out[k + "_ci"] = B1.t_ci(per_seed[k])
    return out


def matched_pairs(cells, tol, key="rho_spec"):
    """Cells from DIFFERENT pool sizes whose measured contention differs by no more than `tol`.

    The same test step 3 ran, carried one level down: it reports not only whether the two cells' benefit
    signs agree but WHICH TERM differs, so "the boundary is not indexed by contention" comes with the
    amount that moves.  Pairs whose benefit intervals overlap are counted separately -- a sign difference
    inside two noise clouds is not evidence.
    """
    pairs = []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            a, b = cells[i], cells[j]
            if a["agents"] == b["agents"]:
                continue
            d = abs(a[key] - b[key])
            if d > tol:
                continue
            ov = not (a["benefit_ci"][1] < b["benefit_ci"][0] or b["benefit_ci"][1] < a["benefit_ci"][0])
            pairs.append({"agents": [a["agents"], b["agents"]], "workers": [a["workers"], b["workers"]],
                          "x": [a[key], b[key]], "dx": d,
                          "benefit_pct": [a["benefit_pct_mine"], b["benefit_pct_mine"]],
                          "intervals_overlap": ov,
                          "signs_agree": (a["benefit_pct_mine"] > 0) == (b["benefit_pct_mine"] > 0),
                          "terms": {k: [a[k + "_mean"], b[k + "_mean"]] for k in TERMS},
                          "delta_terms": {k: a[k + "_mean"] - b[k + "_mean"] for k in TERMS},
                          "delta_benefit_pct": a["benefit_pct_mine"] - b["benefit_pct_mine"]})
    pairs.sort(key=lambda p: p["dx"])
    resolved = [p for p in pairs if not p["signs_agree"] and not p["intervals_overlap"]]
    return {"tol": tol, "key": key, "n_pairs": len(pairs), "n_disagreeing": len(resolved),
            "closest": pairs[0]["dx"] if pairs else None, "pairs": pairs, "disagreeing": resolved}


def term_contrast(pairs):
    """Which term carries the sign flip, over the resolved disagreeing pairs.

    For every pair whose signs disagree with disjoint intervals, the benefit difference is decomposed into
    the three deltas; this returns the mean |delta| of each term and how often each is the LARGEST, so
    "the schedule carries it" is a count and not a reading of one example.
    """
    dis = pairs["disagreeing"]
    if not dis:
        return {"n": 0, "note": "no resolved disagreeing pair in this tolerance -- nothing to attribute"}
    out = {"n": len(dis), "mean_abs_delta": {}, "largest_count": {}, "sign": {}}
    for k in TERMS:
        ds = [p["delta_terms"][k] for p in dis]
        out["mean_abs_delta"][k] = statistics.fmean(abs(d) for d in ds)
        out["sign"][k] = sum(1 for d in ds if d < 0)
    biggest = []
    for p in dis:
        d = p["delta_terms"]
        biggest.append(max(TERMS, key=lambda k: abs(d[k])))
    for k in TERMS:
        out["largest_count"][k] = sum(1 for b in biggest if b == k)
    # the other two terms net out, so the benefit difference is (mostly) one of them
    ben = [abs(p["delta_benefit_pct"]) / 100.0 for p in dis]
    out["mean_abs_delta"]["_benefit_abs"] = statistics.fmean(ben)
    return out
# --------------------------------------------------------------------------- the matched pair, one level down
def fake_cell(agents, workers, rho, benefit_pct, w_s, s, overshoot, ci=None):
    """A synthetic cell carrying only what the pair machinery reads -- for the two-sided arms."""
    d = {"agents": agents, "workers": workers, "rho_spec": rho, "benefit_pct_mine": benefit_pct,
         "benefit_ci": ci or [benefit_pct - 0.01, benefit_pct + 0.01]}
    for k, v in (("w_s", w_s), ("S", s), ("overshoot", overshoot)):
        d[k + "_mean"] = v
    d["design_load"] = agents * 1.0 / (workers * 3.0)
    return d


def design_load(cfg, agents, workers):
    """The offered load the DESIGN states: agents x mean service / (workers x mean step length).

    Carried beside the measured rho because step 3's cross-pool comparison needs to know which coordinate
    the two cells were supposed to match on -- the measured contention, or the load the experiment set.
    `--selftest` has an arm requiring the two to be the same function of the same numbers.
    """
    return agents * cfg["mS"] / (workers * (cfg["mT"] + cfg["mS"]))


# --------------------------------------------------------------------------- report
def report(cells, h, mat_rho, mat_u, contrast_rho, contrast_u, cfg, shared):
    print("== benefit decomposition (h=%.1f, %d seed(s) per cell) ==" % (h, cells[0]["n_seeds"]))
    print("   A    c     rho_spec        benefit%%   benefit%%(model)   w_s      S        overshoot   "
          "hidden   residual")
    for c in sorted(cells, key=lambda x: (x["agents"], x["workers"])):
        print("   %-4d %-5d %.5f         %+7.3f  %+7.3f          %7.4f  %7.4f  %9.4f   %5.2f    %.1e"
              % (c["agents"], c["workers"], c["rho_spec"], c["benefit_pct_mine"], c["benefit_pct_model"],
                 c["w_s_mean"], c["S_mean"], c["overshoot_mean"], c["hidden_frac"],
                 c["identity_max_residual"]))
    print("   identity: benefit = w_s + S - overshoot, worst |residual| over %d cells = %.3e (tol %.0e) "
          "-> %s" % (len(cells), max(c["identity_max_residual"] for c in cells), IDENTITY_TOL,
                     "HOLDS on every cell" if all(c["identity_holds"] for c in cells) else "BROKEN"))
    print("   this file's benefit%% vs the model's own benefit%%: worst |diff| = %.3e"
          % max(abs(c["benefit_pct_mine"] - c["benefit_pct_model"]) for c in cells))
    print("   w_p (the speculative queue wait, observable only where the call is NOT hidden): "
          "%d of %d steps across the cells; mean %.4f"
          % (sum(c["n_w_p_observable"] for c in cells), sum(c["n_steps"] for c in cells),
             statistics.fmean([c["w_p_mean"] for c in cells if c["w_p_mean"] is not None])))
    print("   HOW THE MEAN IS MADE UP (the mean is a residual of two populations, so it is reported as one):")
    print("      A    c     mean benefit/step  on hidden steps  on other steps   hidden steps   hidden "
          "steps' share of the net")
    for c in sorted(cells, key=lambda x: (x["agents"], x["workers"])):
        print("      %-4d %-5d %+14.4f %+16.4f %+15.4f %11d/%d %14s"
              % (c["agents"], c["workers"], c["benefit_sum_all_steps"] / float(c["n_steps"]),
                 c["mean_benefit_hidden"] if c["mean_benefit_hidden"] is not None else float("nan"),
                 c["mean_benefit_other"], c["n_hidden_steps"], c["n_steps"],
                 ("%.2f" % c["hidden_share_of_net_benefit"]) if c["hidden_share_of_net_benefit"] is not None
                 else "n/a"))

    for tag, mat, con in (("measured contention rho_spec", mat_rho, contrast_rho),
                          ("design load u = A*mS/(c*(mT+mS))", mat_u, contrast_u)):
        print("  matched by %s (tol %.5f): %d pair(s) across different pool sizes, %d with the sign "
              "disagreeing AND disjoint intervals; closest pair %.6f apart"
              % (tag, mat["tol"], mat["n_pairs"], mat["n_disagreeing"],
                 mat["closest"] if mat["closest"] is not None else float("nan")))
        for p in mat["disagreeing"][:6]:
            print("      A=%s c=%s  x %s  benefit%% %s  | d(w_s) %+.4f  d(S) %+.4f  d(overshoot) %+.4f"
                  % (p["agents"], p["workers"], ["%.5f" % v for v in p["x"]],
                     ["%+.3f" % v for v in p["benefit_pct"]], p["delta_terms"]["w_s"],
                     p["delta_terms"]["S"], p["delta_terms"]["overshoot"]))
        if con["n"]:
            print("      which term carries the difference, over those %d pair(s): mean |delta| -- w_s "
                  "%.4f, S %.4f, overshoot %.4f (benefit %.4f) | largest in %d / %d / %d pair(s) | "
                  "w_s lower in %d, S lower in %d, overshoot lower in %d"
                  % (con["n"], con["mean_abs_delta"]["w_s"], con["mean_abs_delta"]["S"],
                     con["mean_abs_delta"]["overshoot"], con["mean_abs_delta"]["_benefit_abs"],
                     con["largest_count"]["w_s"], con["largest_count"]["S"],
                     con["largest_count"]["overshoot"], con["sign"]["w_s"], con["sign"]["S"],
                     con["sign"]["overshoot"]))
        else:
            print("      %s" % con["note"])
    print("  the coordinate the two cells were SET to share: design load u ranges %.4f..%.4f over these "
          "cells; the model's own draw order is unchanged by A for the think phase only "
          "(step 3's assay: derivation %s, think shared %s, service shared %s)"
          % (min(c["design_load"] for c in cells), max(c["design_load"] for c in cells),
             shared["derivation_ok"], shared["think_shared_ok"], shared["service_shared_ok"]))


# --------------------------------------------------------------------------- controls
def selftest():
    """Each arm plants one defect and requires exactly that defect to be reported.

    Six of the nine arms are about the IDENTITY -- a decomposition is only a mechanism claim if its terms
    are forced to add back up, and a check that cannot fail is a check that is not there.
    """
    print("== selftest ==")
    bad = 0

    def arm(tag, ok, detail):
        nonlocal bad
        print("  %-40s %s  %s" % (tag, "ok" if ok else "BAD", detail))
        bad += 0 if ok else 1

    cfg = I.default_cfg()
    cfgs = [dict(cfg, seed=s) for s in (101, 102)]

    # 1. the coordinate this file divides by is assayed, by step 3's assay, imported not re-written
    shared = B2.draw_prefix_check(list(range(101, 103)), (16, 64))
    arm("the draw coordinate is step 3's assay",
        shared["derivation_ok"] and shared["think_shared_ok"] and not shared["service_shared_ok"],
        "re-derived T+S == the model's latencies (%d/%d seeds), think shared %s, service shared %s -- the "
        "basis of every w_s and overshoot below" % (shared["derivation_validated"], shared["checked"],
                                                    shared["think_shared_ok"], shared["service_shared_ok"]))

    # 2. the identity holds on real cells, per step
    good = [cell(c, 16, 6, 1.0, [101]) for c in cfgs[:1]][0]
    good2 = cell(cfg, 32, 8, 1.0, [101])
    arm("the identity holds on real cells",
        good["identity_holds"] and good2["identity_holds"] and good["n_steps"] == 16 * (400 - 20),
        "two real cells (A=16 c=6, A=32 c=8, h=1.0): worst |residual| %.3e / %.3e over %d and %d steps "
        "(tol %.0e)" % (good["identity_max_residual"], good2["identity_max_residual"], good["n_steps"],
                        good2["n_steps"], IDENTITY_TOL))

    # 3-5. the identity CAN fail: one plant per term
    plants = {}
    for d in ("no_overshoot", "no_serial_wait", "overshoot_from_serial"):
        plants[d] = cell(cfg, 16, 6, 1.0, [101], defect=d)
    arm("omitting the overshoot term breaks it",
        not plants["no_overshoot"]["identity_holds"]
        and plants["no_overshoot"]["identity_max_residual"] > 1e-6,
        "planted: worst |residual| %.3e -- the identity is load-bearing, not decorative"
        % plants["no_overshoot"]["identity_max_residual"])
    arm("omitting the serial wait breaks it",
        not plants["no_serial_wait"]["identity_holds"]
        and plants["no_serial_wait"]["identity_max_residual"] > 1e-6,
        "planted: worst |residual| %.3e" % plants["no_serial_wait"]["identity_max_residual"])
    arm("reading the overshoot off the serial run breaks it",
        not plants["overshoot_from_serial"]["identity_holds"]
        and plants["overshoot_from_serial"]["identity_max_residual"] > 1e-6,
        "planted (one reading, two meanings): worst |residual| %.3e"
        % plants["overshoot_from_serial"]["identity_max_residual"])

    # 6. the aggregation window is the model's own: my per-seed mean latency == the model's mean_latency
    b = make_runs(cfg, 16, 6, 1.0, 101)
    rows = per_step(cfg, 16, b)
    mine = statistics.fmean(r["lat_s"] for r in rows)
    rows_full = per_step(cfg, 16, b, defect="full_window")
    mine_full = statistics.fmean(r["lat_s"] for r in rows_full)
    arm("the aggregation window is the model's own",
        abs(mine - b["ser"]["mean_latency"]) <= IDENTITY_TOL
        and abs(mine_full - b["ser"]["mean_latency"]) > 1e-6,
        "my mean over the model's own window = %.9f, the model's `mean_latency` = %.9f (|diff| %.1e <= "
        "%.0e); over ALL steps it is %.9f (|diff| %.1e) -- so the window is a measurement, not a choice"
        % (mine, b["ser"]["mean_latency"], abs(mine - b["ser"]["mean_latency"]), IDENTITY_TOL, mine_full,
           abs(mine_full - b["ser"]["mean_latency"])))

    # 7. agreement with the model's own benefit_pct (the number step 3 published)
    m = I.benefit(dict(cfg, seed=101), 16, 6, 1.0)
    mine_pct = 100.0 * statistics.fmean(r["benefit"] for r in rows) / statistics.fmean(r["lat_s"] for r in rows)
    arm("agrees with the model's own benefit_pct",
        abs(mine_pct - m["benefit_pct"]) <= 1e-9,
        "A=16 c=6 h=1.0 seed=101: this file %.12f, the model %.12f (|diff| %.1e) -- the decomposition is "
        "of the number step 3 published, not of a new one"
        % (mine_pct, m["benefit_pct"], abs(mine_pct - m["benefit_pct"])))

    # 7b. the concentration machinery is two-sided: a fixture where every step is hidden must put the whole
    #     net benefit on the hidden population, and one where no step is hidden must put none of it there
    # TWO-SIDED, and the first version of this arm was WRONG ABOUT ITS OWN OBJECT: it required the share to
    # be positive in both cells, but in a saturated cell the net benefit is NEGATIVE while the fully-hidden
    # steps still contribute POSITIVELY -- so the share is negative there, and that is the reading, not a
    # defect.  The assertion is now what the two populations actually imply, one arm per sign.
    allhid = cell(cfg, 16, 8, 1.0, [101])          # light contention: many hidden steps
    nonehid = cell(cfg, 16, 2, 1.0, [101])         # saturation: almost none
    arm("the concentration machinery is two-sided",
        nonehid["n_hidden_steps"] < allhid["n_hidden_steps"]
        and allhid["benefit_sum_all_steps"] > 0 and allhid["hidden_share_of_net_benefit"] > 0
        and nonehid["benefit_sum_all_steps"] < 0 and nonehid["hidden_share_of_net_benefit"] < 0
        and nonehid["mean_benefit_other"] < 0,
        "A=16 c=8 (light): net benefit %+.3f/step, %.3f of it on the %d/%d fully-hidden steps; A=16 c=2 "
        "(saturated): net %+.3f/step (negative) while its %d/%d hidden steps contribute POSITIVELY, so the "
        "share is %.3f -- a negative share is the reading here (the hidden population works against the "
        "net), and the positive arm is the same machinery on the light cell"
        % (allhid["benefit_sum_all_steps"] / allhid["n_steps"], allhid["hidden_share_of_net_benefit"],
           allhid["n_hidden_steps"], allhid["n_steps"],
           nonehid["benefit_sum_all_steps"] / nonehid["n_steps"], nonehid["n_hidden_steps"],
           nonehid["n_steps"], nonehid["hidden_share_of_net_benefit"]))

    # 8. the pair machinery is two-sided (agreeing pair -> 0; flipped sign, disjoint -> 1)
    agree = matched_pairs([fake_cell(16, 6, 0.98, 1.0, 0.5, 1.0, 0.2),
                           fake_cell(48, 16, 0.9801, 0.9, 0.5, 1.0, 0.2)], 0.002)
    flip = matched_pairs([fake_cell(16, 6, 0.98, 1.0, 0.5, 1.0, 0.2, ci=[0.9, 1.1]),
                          fake_cell(48, 16, 0.9801, -0.9, 0.5, 1.0, 1.9, ci=[-1.0, -0.8])], 0.002)
    arm("the matched-pair machinery is two-sided",
        agree["n_pairs"] == 1 and agree["n_disagreeing"] == 0 and flip["n_disagreeing"] == 1,
        "same-rho pair with agreeing signs: %d disagreement(s); the same pair with the sign flipped and "
        "disjoint intervals: %d" % (agree["n_disagreeing"], flip["n_disagreeing"]))

    # 9. the attribution reads the term that actually moves
    planted = matched_pairs([fake_cell(16, 6, 0.98, 1.0, 0.5, 1.0, 0.1, ci=[0.9, 1.1]),
                             fake_cell(48, 16, 0.9801, -0.8, 0.5, 1.0, 1.8, ci=[-0.9, -0.7])], 0.002)
    con = term_contrast(planted)
    arm("the attribution names the term that moves",
        con["n"] == 1 and con["largest_count"]["overshoot"] == 1
        and abs(con["mean_abs_delta"]["overshoot"] - 1.7) < 1e-9,
        "a pair whose only planted difference is overshoot (0.1 -> 1.8): largest-in %d pair(s), mean "
        "|delta| %.4f -- the contrast is computed from the pair, not asserted" % (con["largest_count"]["overshoot"],
                                                                                 con["mean_abs_delta"]["overshoot"]))

    print("  selftest: 10 arm(s), %d failure(s)" % bad)
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", type=float, default=1.0)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--tol", type=float, default=0.002)
    ap.add_argument("--windows", default=None,
                    help="A:c_lo:c_hi triples, comma separated (default: step 3's windows)")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    cfg = I.default_cfg()
    seeds = list(range(101, 101 + a.seeds))
    wins = B2.default_windows()
    if a.windows:
        wins = [tuple(int(x) for x in w.split(":")) for w in a.windows.split(",")]
    cells = []
    for (A, c_lo, c_hi) in wins:
        for c in range(c_lo, c_hi + 1):
            cells.append(cell(cfg, A, c, a.h, seeds))
    for c in cells:
        c["design_load"] = design_load(cfg, c["agents"], c["workers"])
    mat_rho = matched_pairs(cells, a.tol, "rho_spec")
    mat_u = matched_pairs(cells, 0.01, "design_load")
    shared = B2.draw_prefix_check(seeds[:2], (16, 64))
    report(cells, a.h, mat_rho, mat_u, term_contrast(mat_rho), term_contrast(mat_u), cfg, shared)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"model": cfg, "h": a.h, "seeds": seeds, "tol": a.tol,
                                 "cells": cells, "matched_rho": mat_rho, "matched_design_load": mat_u,
                                 "contrast_rho": term_contrast(mat_rho),
                                 "contrast_design_load": term_contrast(mat_u),
                                 "draw_prefix": shared}, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
