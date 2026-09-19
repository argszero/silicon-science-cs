#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 7: THE SIDE-EFFECT CHANNEL (registered P4), and what a rule about tool
semantics can and cannot bound.

WHAT THIS FILE IS.  Steps 1-6 built the model, located the boundary (rho* ~ 0.985, indexed by the pool size
A), decomposed the A-effect, refuted P2, and split the reported gain into channels (P3 refuted: the gain is
the hiding channel).  The registration (`heilmeier.md` section 4, frozen before any deciding run) also says:

  P4 -- "the admissibility rule guards the wrong channel": with a non-idempotent fraction q and compensating
  cost, the safe region shrinks by a measurable amount, while the field's admissibility precondition
  (2606.07846: speculate only on side-effect-free / idempotent / stageable edges) leaves a NON-EMPTY set of
  states with negative benefit inside the region it permits.  Justification: that precondition is keyed to
  the EFFECT channel; the load channel acts on the same edges, so a rule about tool semantics cannot bound
  harm that is caused by contention.  Expected direction: shrinkage >= 0.05 in rho* at q = 0.05, and the
  permitted-but-harmful set non-empty.

THE CHANNEL AS THIS MODEL ACTUALLY IMPLEMENTS IT (found in step 6, relied on here).  A charge exists only on
a step that MISSES: `need_real = not (speculate and HIT)`, and the compensation job is submitted inside that
branch.  A miss is scheduled exactly as the serial call -- nothing is issued early, nothing is discarded.  So
the charge is levied on steps where NOTHING WAS SPECULATED: in this model the effect channel is a tax on the
miss rate, not a cost of damaged state.  Two consequences, measured here rather than inferred:

  (i)  at h = 1.0 the channel is INERT: no step misses, so q has no route into the schedule at all;
  (ii) when it does fire (h < 1, q > 0) the compensation job goes to the POOL and its completion is not
       awaited by the step that caused it (`on_job_done` registers only kind == "real"), so the charge lands
       as WORKER-BUSY TIME -- the load channel -- and not on the charging step.

THE FOUR READINGS, each with its own control:

  M1  inertness at h = 1.0: every cell of a q > 0 family must be BITWISE identical to the q = 0 family
      (per-step latency traces by hash, and the located crossing), and `wasted` must be exactly 0.
  M2  the shrinkage: for a config (q, comp) at a given h, the paired-by-seed difference
      shrink = rho*(q = 0) - rho*(q, comp) on the SAME window.  Pairing is legitimate because q and comp
      change no draw: the model draws IDEM on every run and uses q only in the comparison, so the T/S/HIT/IDEM
      streams are identical across configs -- and that premise is MEASURED here (`rederive()` re-derives all
      four streams and cross-checks them against the model's own `wasted` counter), never assumed.
  M3  where the charge lands: the speculative arm's extra worker-busy time must equal the charged
      compensation -- the same floats summed in a different order -- i.e. the effect channel arrives AS the
      load channel.  This is a per-seed quantity, so it is read per seed and never off a cell mean.
  M4  the permitted-but-harmful set, read two ways (the registered wording does not say what unit a "state"
      is, so both are reported): (a) cells whose MEAN benefit is negative inside the permitted region (the
      q = 0 families, where the rule permits every edge), and (b) individual STEPS whose benefit is negative
      inside that region, including cells whose MEAN benefit is POSITIVE.  Reading (a) is true by construction
      of a window that straddles the crossing and is reported as such; reading (b) is not.

DECLARED BEFORE THE RUN (rules of this file, not descriptions of what came out):

  * ADDED LOAD of a config: `load = (1 - h) * q * comp` worker-time units per step, against a per-step real
    work of `mS` = 1.0.  That is the expected charge -- (fraction of steps that miss) x (fraction
    non-idempotent) x (cost).  The MEASURED charge per step is reported beside it.
  * P4a (shrinkage > 0): CONFIRMED iff every (A, h, config) family with load > 0 has a paired shrinkage
    interval STRICTLY above 0; CONTRADICTED iff at least one lies strictly below 0; UNRESOLVED otherwise.
  * P4b (>= 0.05 at q = 0.05): read at the registered q = 0.05 with comp = 1.0 (the registration names no
    magnitude, so the magnitude is DECLARED here and the whole load axis is swept beside it).  CONFIRMED iff
    every such family's interval lies strictly above 0.05; CONTRADICTED iff at least one lies strictly below;
    UNRESOLVED otherwise.
  * P4c (permitted-but-harmful non-empty): CONFIRMED iff reading (a) or reading (b) is non-empty, with the
    reading that carries it named, and reading (a) flagged as by-construction.
  * THE LOAD LAW (this file's own claim, not a registered one): if the shrinkage is a function of the ADDED
    LOAD and not of how the load was manufactured, then two configs with the same load but different
    (h, q, comp) must give the same shrinkage within their intervals.  The plan contains such pairs on
    purpose (load 0.005 at h = 0.9 and at h = 0.5; load 0.025 at h = 0.9 and at h = 0.5).  CONSISTENT iff the
    two intervals overlap at every matched load; INCONSISTENT iff they are disjoint.
  * A family that locates no crossing, or an ambiguous one, is reported NOT LOCATED and dropped from the
    shrinkage table -- a reading that could not be taken must not look like a passing one.  Unpaired seeds
    (a seed that located a crossing in one config and not in the other) are COUNTED per family.
  * Resolution: `AGREE_TOL` for two arithmetics over the same inputs, `BUSY_REL_TOL` for the busy-time
    identity (the same floats summed in a different order), and every interval is `boundary_v1.t_ci` -- the
    estimator steps 2, 3, 5 and 6 reported with, so these numbers are comparable to theirs.

CPU only, stdlib only, fixed seeds, no network.  `instrument_v0.py` is imported UNMODIFIED; steps 2-4 supply
the t interval, the draw re-derivation with its tolerance, and the per-step terms; step 3's published
per-seed crossing reader is called on the same rows and must agree with the seed-labelled reader here.
"""
import argparse
import hashlib
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
import boundary_v2 as B2       # noqa: E402  step 3's draw re-derivation, crossing rules and reader
import decompose_v1 as D1      # noqa: E402  step 4's per-step terms

# Two arithmetics over the same inputs must agree to the resolution of the coarser one (step 4 measured the
# pair `I.benefit` vs `D1.per_step` at 7.0e-15; this tolerance is six orders above that measurement).
AGREE_TOL = 1e-09

# `busy` is a sum of the same service times accumulated in a DIFFERENT order across the two arms, so "the
# extra busy time equals the charge" is an identity about that arithmetic, not about the reals.
BUSY_REL_TOL = 1e-12

# The windows, per pool size, in worker counts.  Chosen from a pilot run (4 seeds) whose crossing cells were
# printed: at A = 16 the crossing sits between c = 3 and c = 4, at A = 64 between c = 17 and c = 18, and the
# whole load axis swept here moves it no further than c ~ 6 (A = 16) / c ~ 23 (A = 64) -- so both windows
# straddle every config in the plan with room to spare on both sides.
WINDOWS = ((16, 2, 12), (64, 12, 40))

# (h, q, comp).  The q = 0 rows are the reference of every family; the h = 1.0 row is M1; the pairs
# (0.9, 0.05, 5.0) with (0.5, 0.05, 1.0) share load 0.025 and (0.9, 0.05, 1.0) with (0.5, 0.01, 1.0) share
# load 0.005 -- the matched-load pairs the load law is read on.
PLAN = ((1.0, 0.0, 0.0), (1.0, 0.25, 4.0),
        (0.9, 0.0, 0.0), (0.9, 0.05, 1.0), (0.9, 0.05, 5.0), (0.9, 0.25, 4.0), (0.9, 0.5, 8.0),
        (0.5, 0.0, 0.0), (0.5, 0.01, 1.0), (0.5, 0.05, 1.0))

# The registered q for P4b, with the declared magnitude, at the hit rate the boundary is best resolved at.
REGISTERED_Q = 0.05
REGISTERED_COMP = 1.0
P4B_THRESHOLD = 0.05

# The declared load is an expectation over the miss and non-idempotence draws; the measured charge is one
# realisation.  Declared at 25% relative: loose enough for the sampling of a few hundred charges, tight enough
# that a family declared with load > 0 and measured at 0 fails.
CHARGE_REL_TOL = 0.25

# A declared load above this must be visible as a measured charge; below it the charge is expected to be
# exactly zero, and that reading is about the identity rather than about a rate.
MIN_VISIBLE_LOAD = 1e-09

# The per-step (M4b) reading is taken at the two cells bounding the crossing of these configs, per pool size.
MIXTURE_CONFIGS = ((1.0, 0.0, 0.0), (0.9, 0.25, 4.0))

# --------------------------------------------------------------------------- the charge, from the seed
def rederive(agents, seed, cfg, h, defect=None):
    """Re-derive the model's four draw streams in the model's own order, and the steps it charges.

    `agent_run` draws T (exponential), S (the service class), HIT (probability h) and IDEM (probability q), in
    that order, for EVERY run -- q is used only in the comparison, never to decide how many draws to make.
    That is why a config change cannot move a draw, and why the shrinkage below may be paired by seed.  The
    re-derivation is CONTROLLED against step 3's `derive_draws` (which covers T and S) and against the model's
    own `wasted` counter (which counts the charges).

    A miss is a step whose call is issued at the think phase's END, i.e. `not HIT`; the charge is levied when
    such a step's call is also non-idempotent (IDEM, drawn with probability q).  `defect` plants the two ways
    this reading can be wrong; `--selftest` requires each plant to be caught by the check that owns it.
    """
    rng = random.Random(seed)
    steps, mT, mS = cfg["steps"], cfg["mT"], cfg["mS"]
    T = [[rng.expovariate(1.0 / mT) for _ in range(steps)] for _ in range(agents)]
    S = [[I.draw_service(rng, mS, cfg["tail"]) for _ in range(steps)] for _ in range(agents)]
    if defect == "idem_first":                 # the streams are read in the wrong order
        IDEM = [[rng.random() < cfg["q"] for _ in range(steps)] for _ in range(agents)]
        HIT = [[rng.random() < h for _ in range(steps)] for _ in range(agents)]
    else:
        HIT = [[rng.random() < h for _ in range(steps)] for _ in range(agents)]
        IDEM = [[rng.random() < cfg["q"] for _ in range(steps)] for _ in range(agents)]
    miss = [[not HIT[a][k] for k in range(steps)] for a in range(agents)]
    if defect == "charge_on_hits":             # the charge is read off the hits
        charged = [[HIT[a][k] and IDEM[a][k] for k in range(steps)] for a in range(agents)]
    else:
        charged = [[miss[a][k] and IDEM[a][k] for k in range(steps)] for a in range(agents)]
    return {"T": T, "S": S, "HIT": HIT, "IDEM": IDEM, "miss": miss, "charged": charged,
            "n_miss": sum(1 for a in range(agents) for k in range(steps) if miss[a][k]),
            "n_charged": sum(1 for a in range(agents) for k in range(steps) if charged[a][k])}


def load_of(h, q, comp):
    """The declared added load: (fraction of steps that miss) x (fraction non-idempotent) x (cost)."""
    return (1.0 - h) * q * comp


def trace_hash(latencies):
    """A short digest of a run's per-step latencies: enough for the h = 1.0 bitwise identity, small enough to
    keep in the artefact (the traces themselves are 16 x 400 numbers per arm per seed)."""
    return hashlib.sha256(repr(latencies).encode("ascii")).hexdigest()[:16]


def cell3(cfg, agents, workers, h, seed, defect=None):
    """One cell, one seed: both arms made explicitly, plus the charge re-derived from the seed."""
    dry = dict(cfg, seed=seed)
    rd = rederive(agents, seed, dry, h, defect=defect)
    kw = dict(tail=cfg["tail"], q=cfg["q"], comp=cfg["comp"], c=workers)
    ser = I.agent_run(agents, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], seed, speculate=False, **kw)
    spe = I.agent_run(agents, cfg["mT"], cfg["mS"], h, cfg["steps"], seed, speculate=True, **kw)
    t3, s3 = B2.derive_draws(agents, seed, dry)
    charge = cfg["comp"] * rd["n_charged"]
    return {"seed": seed, "rho_spec": spe["rho"], "rho_serial": ser["rho"],
            "benefit_pct": 100.0 * (ser["mean_latency"] - spe["mean_latency"]) / ser["mean_latency"],
            "wasted": spe["wasted"], "busy_spec": spe["busy"], "busy_serial": ser["busy"],
            "extra_busy": spe["busy"] - ser["busy"], "n_miss": rd["n_miss"],
            "n_charged": rd["n_charged"], "charge_from_seed": charge,
            "charge_residual": abs(spe["wasted"] - charge),
            "draws_match_step3": (t3 == rd["T"] and s3 == rd["S"]),
            "spec_hash": trace_hash(spe["latencies"]), "ser_hash": trace_hash(ser["latencies"])}


def sweep3(cfg, agents, c_lo, c_hi, h, seeds):
    """All cells of one (A, h, config) family, keeping the per-seed rows so that crossings can be PAIRED."""
    rows = []
    for c in range(c_lo, c_hi + 1):
        per = [cell3(cfg, agents, c, h, s) for s in seeds]
        bs = [p["benefit_pct"] for p in per]
        rows.append({"agents": agents, "workers": c, "h": h, "q": cfg["q"], "comp": cfg["comp"],
                     "n_seeds": len(seeds), "seeds": list(seeds),
                     "rho_spec": statistics.fmean(p["rho_spec"] for p in per),
                     "rho_spec_sd": statistics.stdev([p["rho_spec"] for p in per]),
                     "rho_serial": statistics.fmean(p["rho_serial"] for p in per),
                     "benefit_pct": statistics.fmean(bs), "per_seed": bs,
                     "ci": B1.t_ci(bs), "per_seed_rho_spec": [p["rho_spec"] for p in per],
                     "per_seed_rho_serial": [p["rho_serial"] for p in per],
                     "wasted_total": sum(p["wasted"] for p in per),
                     "wasted_per_seed": [p["wasted"] for p in per],
                     "n_charged": sum(p["n_charged"] for p in per),
                     "n_miss": sum(p["n_miss"] for p in per),
                     "charge_residual_max": max(p["charge_residual"] for p in per),
                     "draws_match_all": all(p["draws_match_step3"] for p in per),
                     "extra_busy_per_seed": [p["extra_busy"] for p in per],
                     "busy_spec_per_seed": [p["busy_spec"] for p in per],
                     "spec_hash_per_seed": [p["spec_hash"] for p in per],
                     "ser_hash_per_seed": [p["ser_hash"] for p in per]})
    rows.sort(key=lambda r: r["rho_spec"])
    return rows


# --------------------------------------------------------------------------- the crossing, labelled by seed
def crossings_labelled(rows, key):
    """Each seed's own crossing inside the window, KEYED BY SEED so two configs can be paired.

    The same rule as step 3's `per_seed_crossings` (a seed that starts crossed, never crosses, or crosses
    twice is an exclusion, counted and never silently dropped) -- and the same numbers, which is checked by
    the caller against `B2.per_seed_crossings` on the same rows.  The label is the point: without it a paired
    difference cannot be formed, and two unlabelled lists compared position-by-position would pair a seed of
    one config with a DIFFERENT seed of the other.
    """
    by_seed, never, starts, amb = {}, 0, 0, 0
    for si, seed in enumerate(rows[0]["seeds"]):
        bs = [r["per_seed"][si] for r in rows]
        if bs[0] <= 0:                         # already crossed at the LOWEST-contention end of the window
            starts += 1
            continue
        idx = [i for i in range(len(bs) - 1) if bs[i] > 0 >= bs[i + 1]]
        if not idx:
            never += 1
            continue
        if len(idx) > 1:
            amb += 1
            continue
        i = idx[0]
        lo, hi = rows[i], rows[i + 1]
        by_seed[seed] = lo[key] + (bs[i] / (bs[i] - bs[i + 1])) * (hi[key] - lo[key])
    xs = sorted(by_seed.values())
    return {"by_seed": by_seed, "n_used": len(by_seed), "excluded_never_crossed": never,
            "excluded_starts_crossed": starts, "excluded_ambiguous": amb,
            "mean": statistics.fmean(xs) if xs else None,
            "sd": statistics.stdev(xs) if len(xs) > 1 else None,
            "ci": B1.t_ci(xs) if len(xs) > 1 else None}


def crossing_structure(rows, key):
    """Step 3's crossing reader, called for the curve and for the agreement check of the labelled reader."""
    cr = B2.crossing_of_curve(rows, key)
    ps = B2.per_seed_crossings(rows, key) if cr and not cr.get("ambiguous") else None
    return cr, ps


def not_located(cr):
    return cr is None or bool(cr.get("ambiguous"))


def family3(cfg, agents, c_lo, c_hi, h, seeds):
    """One (A, h, config) family: its cells, its curve crossing, and its seed-labelled crossings."""
    rows = sweep3(cfg, agents, c_lo, c_hi, h, seeds)
    cr, ps = crossing_structure(rows, "rho_spec")
    lab = crossings_labelled(rows, "rho_spec")
    agree = None
    if ps is not None:
        agree = (abs(lab["mean"] - ps["mean"]) <= AGREE_TOL and lab["n_used"] == ps["n_used"]
                 and lab["excluded_never_crossed"] == ps["excluded_never_crossed"]
                 and lab["excluded_starts_crossed"] == ps["excluded_starts_crossed"]
                 and lab["excluded_ambiguous"] == ps["excluded_ambiguous"])
    return {"agents": agents, "h": h, "q": cfg["q"], "comp": cfg["comp"], "c_range": [c_lo, c_hi],
            "rows": rows, "crossing": cr, "per_seed": ps, "labelled": lab,
            "labelled_agrees_with_step3": agree,
            "not_located": not_located(cr),
            "x_star": (None if not_located(cr) else cr["x_star"]),
            "load": load_of(h, cfg["q"], cfg["comp"]),
            "measured_charge_per_step": (sum(r["wasted_total"] for r in rows)
                                         / (agents * cfg["steps"] * len(seeds) * len(rows))),
            "kn": "%s/h%.2f/q%.2f/c%.1f" % (agents, h, cfg["q"], cfg["comp"])}


def paired_shrinkage(fam_ref, fam_cfg):
    """shrink = rho*(reference) - rho*(config), paired BY SEED, over the seeds both located a crossing.

    The two families must be the same design (same pool, same hit rate, same window, same seed list): a pair
    whose two members were not measured on the same seeds is not a paired difference, and the two families'
    seed lists are asserted equal here rather than trusted.
    """
    if fam_ref["agents"] != fam_cfg["agents"] or fam_ref["h"] != fam_cfg["h"]:
        return {"error": "not a pair", "family": fam_cfg["kn"]}
    if list(fam_ref["rows"][0]["seeds"]) != list(fam_cfg["rows"][0]["seeds"]):
        return {"error": "seed lists differ", "family": fam_cfg["kn"]}
    a, b = fam_ref["labelled"]["by_seed"], fam_cfg["labelled"]["by_seed"]
    common = sorted(set(a) & set(b))
    ds = [a[s] - b[s] for s in common]
    return {"family": fam_cfg["kn"], "h": fam_cfg["h"], "q": fam_cfg["q"], "comp": fam_cfg["comp"],
            "agents": fam_cfg["agents"], "load": fam_cfg["load"],
            "measured_charge_per_step": fam_cfg["measured_charge_per_step"],
            "n_pairs": len(ds), "n_unpaired": len(set(a) ^ set(b)),
            "mean": statistics.fmean(ds) if ds else None,
            "sd": statistics.stdev(ds) if len(ds) > 1 else None,
            "ci": B1.t_ci(ds) if len(ds) > 1 else None,
            "per_seed": ds, "shrink_known": bool(ds and len(ds) > 1),
            "ref_x": fam_ref["x_star"], "cfg_x": fam_cfg["x_star"],
            "not_located": fam_ref["not_located"] or fam_cfg["not_located"]}


# --------------------------------------------------------------------------- the per-step (M4b) reading
def mixture_cell(cfg, agents, workers, h, seeds):
    """How the cell's mean benefit is made up: the fraction of STEPS that lose, pooled over seeds, with the
    per-seed fraction's interval beside it.

    Aggregation unit: the STEP for the pooled counts (the registered wording says "states", and a step is the
    smallest state this model has), the SEED for the interval (`t_ci` over per-seed fractions, so the interval
    is over draw streams and not over steps -- steps inside a stream are not independent).
    """
    per_seed_frac, n_neg, n_tot, n_hidden = [], 0, 0, 0
    neg_sum = pos_sum = 0.0
    for s in seeds:
        rows = D1.per_step(cfg, agents, D1.make_runs(cfg, agents, workers, h, s))
        neg = [r["benefit"] for r in rows if r["benefit"] < 0]
        pos = [r["benefit"] for r in rows if r["benefit"] >= 0]
        per_seed_frac.append(len(neg) / len(rows))
        n_neg += len(neg)
        n_tot += len(rows)
        n_hidden += sum(1 for r in rows if r["hidden"])
        neg_sum += sum(neg)
        pos_sum += sum(pos)
    return {"cell": "%s/w%d/h%.2f/q%.2f/c%.1f" % (agents, workers, h, cfg["q"], cfg["comp"]),
            "agents": agents, "workers": workers, "h": h, "q": cfg["q"], "comp": cfg["comp"],
            "n_steps": n_tot, "n_negative": n_neg, "frac_negative": n_neg / n_tot,
            "frac_negative_per_seed_mean": statistics.fmean(per_seed_frac),
            "frac_negative_ci": B1.t_ci(per_seed_frac) if len(per_seed_frac) > 1 else None,
            "mean_negative": (neg_sum / n_neg) if n_neg else None,
            "mean_nonnegative": (pos_sum / (n_tot - n_neg)) if n_tot > n_neg else None,
            "mean_benefit": (neg_sum + pos_sum) / n_tot if n_tot else None,
            "hidden_fraction": n_hidden / n_tot}


def mixture_at_crossing(cfg, fam, seeds):
    """The two cells bounding this family's crossing, read per step.

    Reported even where the MEAN benefit is positive -- that is what reading (b) of M4 is about: a cell can
    make money on average while most of its steps lose.  A family with no crossing gets no cells: NOT LOCATED,
    with the reason, never an empty table that reads like a pass.
    """
    if fam["not_located"]:
        return {"family": fam["kn"], "cells": [], "status": "NOT LOCATED"}
    lo, hi = fam["crossing"]["cells"]
    return {"family": fam["kn"], "status": "LOCATED",
            "cells": [mixture_cell(cfg, fam["agents"], c, fam["h"], seeds) for c in (lo[1], hi[1])]}


# --------------------------------------------------------------------------- the load law
def load_law(shrinks, tol=1e-12):
    """Two configs with the SAME declared load but different (h, q, comp) must give the same shrinkage.

    Grouping is on the declared load (a design quantity, exact in binary for the values in the plan), and a
    group is only read when its members differ in h -- two rows of the same hit rate would be the same
    experiment, not a matched pair.
    """
    groups = {}
    for r in shrinks:
        if not r.get("shrink_known") or r["not_located"] or r["load"] <= 0:
            continue
        groups.setdefault(round(r["load"], 12), []).append(r)
    out = []
    for load, rs in sorted(groups.items()):
        hs = {r["h"] for r in rs}
        if len(rs) < 2 or len(hs) < 2:
            continue
        los = [r["ci"][0] for r in rs]
        his = [r["ci"][1] for r in rs]
        overlap = max(los) <= min(his)
        out.append({"load": load, "members": [r["family"] for r in rs],
                    "shrinkage": {r["family"]: (r["mean"], r["ci"]) for r in rs},
                    "disjoint": (not overlap), "consistent": bool(overlap)})
    verdict = ("NOT READ" if not out else ("INCONSISTENT" if any(p["disjoint"] for p in out)
                                          else "CONSISTENT"))
    return {"pairs": out, "any_disjoint": any(p["disjoint"] for p in out),
            "n_pairs": len(out), "verdict": verdict}


def load_to_reach(shrinks, threshold=P4B_THRESHOLD):
    """The load at which the REGISTERED threshold would be reached, per (A, h), as a through-origin fit.

    An ESTIMATE and labelled one: it is an extrapolation of a fit whose slope is measured only at the loads in
    the plan, and the two largest loads of the h = 0.9 groups show the shrink rising sub-linearly (A = 16:
    0.0182 at 0.10 and 0.0407 at 0.40 -- 2.2x for 4x the load).  Reported because "the claim is refuted" is
    only half an answer: the reader also needs to know what it would take for the claim to hold.
    """
    by_group = {}
    for r in shrinks:
        if not r.get("shrink_known") or r["not_located"] or r["load"] <= 0:
            continue
        by_group.setdefault((r["agents"], r["h"]), []).append(r)
    out = {}
    for (a, h), rs in sorted(by_group.items()):
        num = sum(r["load"] * r["mean"] for r in rs)
        den = sum(r["load"] ** 2 for r in rs)
        k = num / den if den else None
        out["A=%d/h%.2f" % (a, h)] = {"slope_per_unit_load": k, "loads": [r["load"] for r in rs],
                                      "shrinkages": [r["mean"] for r in rs],
                                      "load_for_threshold": (threshold / k) if k else None}
    return {"estimate": True, "threshold": threshold, "groups": out,
            "method": "through-origin least squares over the family's own measured (load, shrink) points"}


# --------------------------------------------------------------------------- verdicts
def verdicts(shrinks, m1, m4a, m4b):
    """The three registered halves, read off the numbers with the rules declared in the module docstring."""
    rows = [r for r in shrinks if r.get("shrink_known") and not r["not_located"] and r["load"] > 0]
    if not rows:
        p4a = {"verdict": "UNRESOLVED", "reason": "no load-bearing family located a crossing"}
    else:
        above = [r["family"] for r in rows if r["ci"][0] > 0]
        below = [r["family"] for r in rows if r["ci"][1] < 0]
        if len(above) == len(rows):
            p4a = {"verdict": "CONFIRMED", "n": len(rows),
                   "detail": "every load-bearing family's shrink interval is strictly above zero"}
        elif below:
            p4a = {"verdict": "CONTRADICTED", "n": len(rows), "below": below}
        else:
            p4a = {"verdict": "UNRESOLVED", "n": len(rows),
                   "straddling": [r["family"] for r in rows if not (r["ci"][0] > 0)]}
    reg = [r for r in rows if abs(r["q"] - REGISTERED_Q) < 1e-12 and abs(r["comp"] - REGISTERED_COMP) < 1e-12]
    if not reg:
        p4b = {"verdict": "UNRESOLVED", "reason": "the registered (q = %.2f, comp = %.1f) family was not run"
               % (REGISTERED_Q, REGISTERED_COMP)}
    else:
        above = [r["family"] for r in reg if r["ci"][0] > P4B_THRESHOLD]
        below = [r for r in reg if r["ci"][1] < P4B_THRESHOLD]
        if len(above) == len(reg):
            p4b = {"verdict": "CONFIRMED", "n": len(reg),
                   "detail": "every registered-point interval is strictly above %.2f" % P4B_THRESHOLD}
        elif below:
            p4b = {"verdict": "CONTRADICTED", "n": len(reg), "below": [r["family"] for r in below],
                   "measured": {r["family"]: (r["mean"], r["ci"]) for r in reg},
                   "shortfall_factor": min(P4B_THRESHOLD / r["ci"][1] for r in below)}
        else:
            p4b = {"verdict": "UNRESOLVED", "n": len(reg),
                   "detail": {r["family"]: (r["mean"], r["ci"]) for r in reg}}
    # The per-step reading lives one level down: `m4b` is a block PER FAMILY, each holding its cells.  Reading
    # the block level for a cell field finds nothing and reports the reading as absent while it is on the
    # page -- a false absence, and one that also changed which reading was said to carry the verdict.
    step_cells = [c for blk in m4b for c in blk.get("cells", [])]
    b_carry = [c for c in step_cells if c["frac_negative"] > 0]
    p4c = {"verdict": "CONFIRMED" if (m4a["n_cells_negative"] > 0 or b_carry) else "CONTRADICTED",
           "reading_a_cells_negative": m4a["n_cells_negative"],
           "reading_a_is_by_construction": True,
           "reading_b_cells_read": len(step_cells),
           "reading_b_cells_with_losing_steps": len(b_carry),
           "reading_b_losing_fraction": ([min(c["frac_negative"] for c in b_carry),
                                          max(c["frac_negative"] for c in b_carry)] if b_carry else None),
           "carried_by": ("individual steps (not by construction)" if b_carry
                          else ("cell means (by construction)" if m4a["n_cells_negative"] else "nothing"))}
    return {"P4a": p4a, "P4b": p4b, "P4c": p4c}


# --------------------------------------------------------------------------- the run's own controls
def agree_with_model(cfg, agents, workers, h, seeds):
    """This file's cell must agree with the MODEL's own `benefit` on the same cell and seeds.

    `cell3` computes the benefit from the two runs it makes itself; `I.benefit` makes its own two runs from
    the same config.  If they disagree, every number here is about a different system than the one steps 1-6
    published, and the comparison is a second opinion rather than a control.  Cost: two extra runs per cell,
    so it is read on a small declared cell set.
    """
    worst = 0.0
    for s in seeds:
        mine = cell3(cfg, agents, workers, h, s)
        theirs = I.benefit(dict(cfg, seed=s), agents, workers, h)
        worst = max(worst, abs(mine["benefit_pct"] - theirs["benefit_pct"]))
    return worst


def inertness(fams, ref_kn):
    """M1: a q > 0 family at h = 1.0 against the q = 0 family at the same h, cell by cell and seed by seed."""
    out = []
    for kn, fam in sorted(fams.items()):
        a, h, q, comp = fam["agents"], fam["h"], fam["q"], fam["comp"]
        if abs(h - 1.0) > 1e-12 or q <= 0.0:
            continue
        # The reference family is the q = 0 cell of the SAME h: its own comp is 0 by construction (a q = 0
        # family charges nothing, whatever comp it carries), and reading it off this family's comp was the
        # first bug of this file -- a key built from the wrong object's coordinate.
        ref = fams[ref_kn(a, 1.0, 0.0, 0.0)]
        hash_mismatch, wasted_total = 0, 0.0
        for r, rr in zip(fam["rows"], ref["rows"]):
            if r["workers"] != rr["workers"]:
                raise AssertionError("cell mismatch in the inertness reading")
            for x, y in zip(r["spec_hash_per_seed"], rr["spec_hash_per_seed"]):
                hash_mismatch += (x != y)
            wasted_total += r["wasted_total"]
        out.append({"family": kn, "hash_mismatches": hash_mismatch, "wasted_total": wasted_total,
                    "crossing_equal": (fam["x_star"] == ref["x_star"]),
                    "identical": hash_mismatch == 0 and wasted_total == 0.0
                                 and fam["x_star"] == ref["x_star"]})
    return out


def run_checks(fams, shrinks, m1, agree_worst, law):
    worst_charge = max((r["charge_residual_max"] for f in fams.values() for r in f["rows"]), default=0.0)
    worst_busy = 0.0
    for f in fams.values():
        for r in f["rows"]:
            for eb, w in zip(r["extra_busy_per_seed"], r["wasted_per_seed"]):
                if w > 0.0:
                    worst_busy = max(worst_busy, abs(eb - w) / w)
    # The declared load is an EXPECTATION over the miss and non-idempotence draws; the measured charge is one
    # realisation of it.  With A*steps*seeds steps per family the counts are large enough that the relative
    # gap is a few per cent (a hundred-ish charges), so the rule below is declared at 25% -- loose enough not
    # to fail on sampling, tight enough that a config declared with load > 0 and MEASURED at 0 cannot pass.
    gaps = {f["kn"]: (abs(f["measured_charge_per_step"] - f["load"]) / f["load"]
                      if f["load"] > MIN_VISIBLE_LOAD else 0.0) for f in fams.values()}
    charge_gap = (max(gaps.values()) if gaps else 0.0, gaps)
    return {
        "rederivation_matches_step3_draws": all(r["draws_match_all"] for f in fams.values() for r in f["rows"]),
        "charge_reproduced_from_the_seed": worst_charge <= AGREE_TOL,
        "zero_charge_when_q_is_zero": all(r["wasted_total"] == 0.0 for f in fams.values()
                                          if f["q"] == 0.0 for r in f["rows"]),
        "charge_arrives_as_busy_time": worst_busy <= BUSY_REL_TOL,
        "inert_at_h1": all(m["identical"] for m in m1),
        "labelled_crossings_agree_with_step3": all(f["labelled_agrees_with_step3"]
                                                   for f in fams.values() if not f["not_located"]),
        "every_family_located_a_crossing": all(not f["not_located"] for f in fams.values()),
        "measured_charge_tracks_the_declared_load": (charge_gap[0] <= CHARGE_REL_TOL),
        "every_declared_load_is_charged": all(
            (f["measured_charge_per_step"] > 0.0) for f in fams.values() if f["load"] > MIN_VISIBLE_LOAD),
        "cell_agrees_with_the_model": agree_worst <= AGREE_TOL,
    }


# --------------------------------------------------------------------------- report
def fmt_ci(ci, spec="%+.5f"):
    return "-" if not ci else (spec + ".." + spec) % tuple(ci)


def report(fams, shrinks, m1, m4a, m4b, cons, checks, verds, cfg0, seeds, law, windows, plan_printed):
    print("== step 7: the side-effect channel (P4) | %d seeds %d..%d | mT=%.1f mS=%.1f steps=%d =="
          % (len(seeds), seeds[0], seeds[-1], cfg0["mT"], cfg0["mS"], cfg0["steps"]))
    print("   windows %s | configs (h, q, comp) %s" % (list(windows), [p for p in plan_printed]))
    print()
    print("   M1 -- inertness at h = 1.0 (a q > 0 family vs the q = 0 family, same cells and seeds):")
    for m in m1:
        print("     %-22s hash mismatches %d | wasted total %.1f | crossing equal %s | identical %s"
              % (m["family"], m["hash_mismatches"], m["wasted_total"], m["crossing_equal"], m["identical"]))
    print()
    print("   M2/M3 -- the shrinkage, paired by seed, and the charge that produced it:")
    print("     %-24s %-8s %-14s %-9s %-22s %-6s" % ("family", "load", "charge/step", "shrink", "95% CI", "pairs"))
    for r in shrinks:
        if r.get("error"):
            print("     %-24s %s" % (r["family"], r["error"]))
            continue
        if r["not_located"]:
            print("     %-24s NOT LOCATED (a crossing was not resolved -- dropped from the verdicts)" % r["family"])
            continue
        print("     %-24s %-8.4f %-14.6f %-9s %-22s %-6d" % (r["family"], r["load"],
              r["measured_charge_per_step"], ("%+.5f" % r["mean"]), fmt_ci(r["ci"]), r["n_pairs"]))
    print("     (unpaired seeds, i.e. seeds that located a crossing in one config and not the other: %s)"
          % ", ".join("%s:%d" % (r["family"], r["n_unpaired"]) for r in shrinks if not r.get("error")))
    print("     the reference boundary at h = 1.0: %s"
          % ", ".join("A=%d %.5f" % (f["agents"], f["x_star"]) for k, f in sorted(fams.items())
                      if abs(f["h"] - 1.0) < 1e-12 and f["q"] == 0.0))
    print()
    print("   the load law (same declared load, different h, q, comp):")
    for p in law["pairs"]:
        print("     load %.4f | %s | %s" % (p["load"], " vs ".join(p["members"]),
              "CONSISTENT" if p["consistent"] else "INCONSISTENT (intervals disjoint)"))
    if not law["pairs"]:
        print("     no matched-load pair was read")
    print("     load-law verdict: %s" % law["verdict"])
    for k, v in sorted(law["load_to_reach"]["groups"].items()):
        print("       %-14s slope %.3f per unit load (measured at loads %s) -> the registered %.2f would"
              " need load %.2f (ESTIMATE, extrapolated)"
              % (k, v["slope_per_unit_load"], v["loads"], P4B_THRESHOLD, v["load_for_threshold"]))
    print()
    print("   M4a -- cells with a NEGATIVE mean benefit inside the permitted region (q = 0, all edges"
          " idempotent), i.e. the rule permits them:")
    for k, v in sorted(m4a["by_family"].items()):
        print("     %-20s %d of %d cells negative | rho range %.4f..%.4f"
              % (k, v["n_negative"], v["n_cells"], v["rho_min"], v["rho_max"]))
    print("     (reading (a) is true by construction of a window that straddles the crossing: %s)"
          % m4a["by_construction"])
    print()
    print("   M4b -- individual STEPS that lose, at the two cells bounding each crossing:")
    for blk in m4b:
        if blk["status"] != "LOCATED":
            print("     %-24s NOT LOCATED" % blk["family"])
            continue
        for c in blk["cells"]:
            print("     %-24s w=%-3d mean benefit %+8.4f units | losing steps %5.1f%% [%s] |"
                  " mean(losing) %+.4f | mean(winning) %+.4f | fully hidden %4.1f%%"
                  % (blk["family"], c["workers"], c["mean_benefit"],
                     100 * c["frac_negative"], fmt_ci([x * 100 for x in c["frac_negative_ci"]]),
                     c["mean_negative"], c["mean_nonnegative"], 100 * c["hidden_fraction"]))
    print()
    print("   verdicts: P4a %s | P4b %s | P4c %s (%s) | the load law %s (this file's own claim)"
          % (verds["P4a"]["verdict"], verds["P4b"]["verdict"], verds["P4c"]["verdict"],
             verds["P4c"]["carried_by"], law["verdict"]))
    print("   checks: " + " | ".join("%s=%s" % (k, "OK" if v else "FAIL") for k, v in sorted(checks.items())))
    print("   worst charge residual %.2e | cell-vs-model benefit agreement %.2e"
          % (max((r["charge_residual_max"] for f in fams.values() for r in f["rows"]), default=0.0),
             cons["agree_worst"]))


# --------------------------------------------------------------------------- selftest
def case(name, ok, detail):
    return (name, bool(ok), detail)


def selftest():
    """Each arm fails for its OWN reason or it is decoration; the three verdict rules are read on synthetic
    intervals so that CONFIRMED, CONTRADICTED and UNRESOLVED are each shown to be reachable."""
    cfg0 = I.default_cfg()
    seeds3 = [101, 102, 103]
    out = []
    cl = dict(cfg0, tail="light")

    # 1. the re-derivation is the model's own draw order: swap it and step 3's derives must stop matching
    good = cell3(dict(cl, q=0.25, comp=4.0), 16, 6, 0.9, seeds3[0])
    bad = cell3(dict(cl, q=0.25, comp=4.0), 16, 6, 0.9, seeds3[0], defect="idem_first")
    # Reading the last two streams in the wrong order CANNOT move T or S (they are drawn first), so the
    # plant's owner is the CHARGE check, not the draw check.  That is itself the reason the paired comparison
    # below is legitimate -- the streams that carry the workload are settled before h or q is consulted -- and
    # the arm asserts exactly that pair of facts.
    out.append(case("rederivation_order_is_the_models",
                    good["draws_match_step3"] and bad["draws_match_step3"]
                    and good["charge_residual"] <= AGREE_TOL and bad["charge_residual"] > 1.0,
                    "swapping the last two streams leaves T/S matching (%s, the reason pairing works) and"
                    " shows up as a charge mismatch instead: %.2e vs %.2f"
                    % (bad["draws_match_step3"], good["charge_residual"], bad["charge_residual"])))

    # 2. the charge is levied on MISSES, and the model's own counter says so
    planted = cell3(dict(cl, q=0.25, comp=4.0), 16, 6, 0.9, seeds3[0], defect="charge_on_hits")
    out.append(case("charge_is_levied_on_misses",
                    good["charge_residual"] <= AGREE_TOL and planted["charge_residual"] > 1.0,
                    "residual on the model's rule %.2e, on the hit-rule %.2f"
                    % (good["charge_residual"], planted["charge_residual"])))

    # 3. the inertness reading can fail: two h = 1.0 hash sets agree, two h = 0.9 ones do not
    a = cell3(cl, 16, 6, 1.0, seeds3[0])
    b = cell3(cl, 16, 6, 1.0, seeds3[1])
    c = cell3(cl, 16, 6, 0.9, seeds3[0])
    out.append(case("the_hash_reading_discriminates",
                    a["spec_hash"] != b["spec_hash"] and a["spec_hash"] != c["spec_hash"]
                    and a["spec_hash"] == a["spec_hash"],
                    "different seeds differ (%s/%s) and different h differs -- so an equality of hashes is a"
                    " statement about the schedule, not about the hash" % (a["spec_hash"][:6], b["spec_hash"][:6])))

    # 4. pairing refuses two families that were not measured on the same seeds
    def synth(seed_list, by_seed, kn):
        return {"agents": 16, "h": 0.9, "q": 0.05, "comp": 1.0, "load": 0.005,
                "measured_charge_per_step": 0.005, "rows": [{"seeds": seed_list, "per_seed": [1.0, -1.0]}],
                "labelled": {"by_seed": by_seed}, "not_located": False, "x_star": 0.98, "kn": kn}
    fam_a = synth([1, 2], {1: 0.9}, "a")
    fam_b = synth([3, 4], {3: 0.8}, "b")
    fam_c = synth([1, 2], {1: 0.85}, "c")   # same seed list, one shared seed
    r_bad = paired_shrinkage(fam_a, fam_b)
    r_ok = paired_shrinkage(fam_a, fam_c)
    out.append(case("pairing_refuses_foreign_seeds",
                    r_bad.get("error") == "seed lists differ" and r_ok.get("n_pairs") == 1,
                    "foreign seeds -> %s, a shared seed -> n_pairs %s" % (r_bad.get("error"), r_ok.get("n_pairs"))))

    # 5. the load law can be broken: two synthetic rows at the same load with disjoint intervals
    law = load_law([{"family": "x", "load": 0.05, "h": 0.9, "shrink_known": True, "not_located": False,
                     "ci": [0.001, 0.002], "mean": 0.0015},
                    {"family": "y", "load": 0.05, "h": 0.5, "shrink_known": True, "not_located": False,
                     "ci": [0.010, 0.020], "mean": 0.015}])
    law_same = load_law([{"family": "x", "load": 0.05, "h": 0.9, "shrink_known": True, "not_located": False,
                          "ci": [0.001, 0.004], "mean": 0.002},
                         {"family": "y", "load": 0.05, "h": 0.5, "shrink_known": True, "not_located": False,
                          "ci": [0.003, 0.006], "mean": 0.004}])
    out.append(case("load_law_can_fail",
                    law["any_disjoint"] and law["n_pairs"] == 1 and law_same["n_pairs"] == 1
                    and not law_same["any_disjoint"],
                    "disjoint intervals -> %s, overlapping -> %s"
                    % (law["any_disjoint"], law_same["any_disjoint"])))

    # 6. the three verdict rules are each reachable, read on synthetic shrinkage rows
    def row(kn, lo, hi, q=0.05, comp=1.0, h=0.9, load=0.005):
        return {"family": kn, "load": load, "q": q, "comp": comp, "h": h, "shrink_known": True,
                "not_located": False, "ci": [lo, hi], "mean": (lo + hi) / 2, "n_pairs": 12,
                "measured_charge_per_step": load, "n_unpaired": 0}
    v_pos = verdicts([row("p", 0.070, 0.075), row("p2", 0.080, 0.090, h=0.5, load=0.025)],
                     {}, {"n_cells_negative": 0}, [])
    v_straddle = verdicts([row("s", -0.001, 0.004)], {}, {"n_cells_negative": 0}, [])
    # P4b is a threshold rule, not a zero rule, so the interval that leaves P4a CONFIRMED (-0.001..0.004)
    # leaves P4b CONTRADICTED: the UNRESOLVED band of P4b is an interval crossing 0.05 itself.
    v_straddle50 = verdicts([row("s50", 0.040, 0.060)], {}, {"n_cells_negative": 0}, [])
    v_neg = verdicts([row("n", -0.004, -0.002)], {}, {"n_cells_negative": 0}, [])
    out.append(case("P4a_is_reachable_in_all_three_ways",
                    v_pos["P4a"]["verdict"] == "CONFIRMED" and v_straddle["P4a"]["verdict"] == "UNRESOLVED"
                    and v_neg["P4a"]["verdict"] == "CONTRADICTED",
                    "%s / %s / %s" % (v_pos["P4a"]["verdict"], v_straddle["P4a"]["verdict"],
                                      v_neg["P4a"]["verdict"])))
    out.append(case("P4b_is_reachable_in_all_three_ways",
                    v_pos["P4b"]["verdict"] == "CONFIRMED"
                    and v_straddle50["P4b"]["verdict"] == "UNRESOLVED"
                    and v_neg["P4b"]["verdict"] == "CONTRADICTED",
                    "%s / %s / %s (threshold %.2f; the band is an interval crossing %.2f, not zero)"
                    % (v_pos["P4b"]["verdict"], v_straddle50["P4b"]["verdict"], v_neg["P4b"]["verdict"],
                       P4B_THRESHOLD, P4B_THRESHOLD)))
    v_no = verdicts([row("z", 0.002, 0.004)], {}, {"n_cells_negative": 0}, [])
    v_a = verdicts([row("z", 0.002, 0.004)], {}, {"n_cells_negative": 1}, [{}])
    # A block with its own cells: the per-step reading is one level down, and an arm that plants it at the
    # block level would pass while testing nothing (this file's own P4c read that level first).
    v_b = verdicts([row("z", 0.002, 0.004)], {}, {"n_cells_negative": 0},
                   [{"family": "f", "cells": [{"frac_negative": 0.4}]}])
    out.append(case("P4c_needs_a_carrier",
                    v_no["P4c"]["verdict"] == "CONTRADICTED" and v_a["P4c"]["verdict"] == "CONFIRMED"
                    and v_b["P4c"]["verdict"] == "CONFIRMED"
                    and v_b["P4c"]["reading_b_cells_with_losing_steps"] == 1
                    and v_b["P4c"]["carried_by"].startswith("individual steps"),
                    "no carrier -> %s | a negative cell mean -> %s | a losing step (one level down) -> %s"
                    " carried by %s" % (v_no["P4c"]["verdict"], v_a["P4c"]["verdict"], v_b["P4c"]["verdict"],
                                        v_b["P4c"]["carried_by"])))

    # 7. a family that located nothing must be dropped from the verdicts, not counted as zero
    v_dropped = verdicts([dict(row("d", 0.0, 0.0), not_located=True)], {}, {"n_cells_negative": 0}, [])
    out.append(case("unlocated_families_are_dropped",
                    v_dropped["P4a"]["verdict"] == "UNRESOLVED"
                    and "no load-bearing family" in v_dropped["P4a"]["reason"],
                    "verdict %s (%s)" % (v_dropped["P4a"]["verdict"], v_dropped["P4a"]["reason"])))

    # 8. the mixture reading sees the two populations of step 4 rather than averaging them away
    m = mixture_cell(dict(cl, q=0.0, comp=0.0), 16, 4, 1.0, [101, 102])
    out.append(case("the_step_reading_separates_the_populations",
                    m["n_steps"] > 0 and m["frac_negative"] > 0 and m["mean_negative"] < 0
                    and m["mean_nonnegative"] > 0 and m["mean_benefit"] != m["mean_negative"],
                    "losing %.1f%% of %d steps, mean(losing) %+.4f vs mean(not) %+.4f"
                    % (100 * m["frac_negative"], m["n_steps"], m["mean_negative"], m["mean_nonnegative"])))

    # 9. a FALSIFIED auxiliary claim is a finding, not an instrument failure: the exit code answers "is this
    #    run trustworthy", and the load law does not answer that question.  Two-sided: the same synthetic run
    #    with a broken charge identity must fail the checks.
    def fake_fams(residual):
        return {"k": {"kn": "k", "q": 0.0, "comp": 0.0, "load": 0.0, "agents": 16, "h": 1.0,
                      "not_located": False, "labelled_agrees_with_step3": True,
                      "measured_charge_per_step": 0.0,
                      "rows": [{"charge_residual_max": residual, "extra_busy_per_seed": [0.0],
                                "wasted_per_seed": [0.0], "wasted_total": 0.0, "draws_match_all": True}]}}
    ok_law = run_checks(fake_fams(0.0), [], [], 0.0, {"any_disjoint": True})
    bad_law = run_checks(fake_fams(1.0), [], [], 0.0, {"any_disjoint": True})
    out.append(case("a_falsified_claim_does_not_fail_the_instrument",
                    all(ok_law.values()) and not all(bad_law.values())
                    and "matched_load_pairs_are_consistent" not in ok_law,
                    "%d checks, all OK with an inconsistent law; a broken charge identity -> %s"
                    % (len(ok_law), [k for k, v in bad_law.items() if not v])))

    bad = [n for n, ok, _ in out if not ok]
    for n, ok, d in out:
        print("  %-42s %s  %s" % (n, "ok" if ok else "FAIL", d))
    print("  selftest: %d case(s), %d failed" % (len(out), len(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="issue #50 step 7 -- the side-effect channel (registered P4)")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed0", type=int, default=101)
    ap.add_argument("--quick", action="store_true", help="3 seeds and a narrow window, for a smoke run")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    seeds = [args.seed0 + i for i in range(3 if args.quick else args.seeds)]
    cfg0 = I.default_cfg()
    windows = WINDOWS
    plan = ((1.0, 0.0, 0.0), (1.0, 0.25, 4.0), (0.9, 0.0, 0.0), (0.9, 0.05, 1.0),
            (0.9, 0.25, 4.0), (0.5, 0.0, 0.0), (0.5, 0.05, 1.0)) if args.quick else PLAN
    fams = {}
    for (h, q, comp) in plan:
        cfg = dict(cfg0, q=q, comp=comp)
        for (a, clo, chi) in windows:
            k = "%s/h%.2f/q%.2f/c%.1f" % (a, h, q, comp)
            fams[k] = family3(cfg, a, clo, chi, h, seeds)
    def ref_kn(agents, h, q, comp):
        return "%s/h%.2f/q%.2f/c%.1f" % (agents, h, q, comp)
    shrinks = []
    for (h, q, comp) in plan:
        if q == 0.0:
            continue
        for (a, _clo, _chi) in windows:
            shrinks.append(paired_shrinkage(fams[ref_kn(a, h, 0.0, 0.0)], fams[ref_kn(a, h, q, comp)]))
    m1 = inertness(fams, ref_kn)
    # M4a: the permitted region is the q = 0 families (every edge idempotent), so the rule permits them all.
    by_family = {}
    for k, f in sorted(fams.items()):
        if f["q"] != 0.0:
            continue
        neg = [r for r in f["rows"] if r["benefit_pct"] < 0]
        by_family[k] = {"n_negative": len(neg), "n_cells": len(f["rows"]),
                        "rho_min": f["rows"][0]["rho_spec"], "rho_max": f["rows"][-1]["rho_spec"],
                        "cells": [[r["agents"], r["workers"]] for r in neg]}
    m4a = {"by_family": by_family, "n_cells_negative": sum(v["n_negative"] for v in by_family.values()),
           "by_construction": ("the swept window is chosen to straddle each family's crossing, so the cells"
                               " above it are permitted-and-harmful whatever the crossing's location is")}
    m4b = []
    for (h, q, comp) in MIXTURE_CONFIGS:
        for (a, _clo, _chi) in windows:
            m4b.append(mixture_at_crossing(dict(cfg0, q=q, comp=comp), fams[ref_kn(a, h, q, comp)], seeds))
    law = load_law(shrinks)
    law["load_to_reach"] = load_to_reach(shrinks)
    cons = {"agree_worst": max(agree_with_model(dict(cfg0, q=0.25, comp=4.0), 16, 6, 0.9, [seeds[0]]),
                               agree_with_model(dict(cfg0, q=0.05, comp=1.0), 64, 18, 0.9, [seeds[0]]))}
    checks = run_checks(fams, shrinks, m1, cons["agree_worst"], law)
    verds = verdicts(shrinks, m1, m4a, m4b)
    report(fams, shrinks, m1, m4a, m4b, cons, checks, verds, cfg0, seeds, law, windows, plan)
    payload = {
        "what": "issue #50 instrument v0 step 7 -- the side-effect channel (registered P4)",
        "seeds": seeds, "windows": windows, "plan": plan,
        "model": {k: cfg0[k] for k in sorted(cfg0) if not isinstance(cfg0[k], list)},
        "declared": {
            "load": "load = (1-h)*q*comp worker-time units per step, against mS = 1.0 per step of real work",
            "P4a_rule": "CONFIRMED iff every load>0 family's paired shrink interval is strictly above 0",
            "P4b_rule": "at (q = 0.05, comp = 1.0): CONFIRMED iff every interval strictly above 0.05",
            "P4c_rule": "CONFIRMED iff reading (a) or (b) is non-empty; (a) is by construction",
            "load_law": "same declared load, different h -> intervals must overlap",
            "agree_tol": AGREE_TOL, "busy_rel_tol": BUSY_REL_TOL,
            "windows_basis": "pilot (4 seeds): A=16 crossing between c=3 and c=4, A=64 between c=17 and c=18",
        },
        "families": fams, "shrinkage": shrinks, "m1_inertness": m1, "m4a": m4a, "m4b": m4b,
        "load_law": law, "cons": cons, "checks": checks, "verdicts": verds,
    }
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
