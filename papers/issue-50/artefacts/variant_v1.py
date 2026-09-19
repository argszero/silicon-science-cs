#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 9: THE MATCHED-PARALLELISM CONTROL (registered P3), built by making the
CHOICE of which steps to issue early an explicit, separate object from the WIDTH of that choice.

WHAT THE REGISTRATION PROMISES, AND WHY STEP 6 COULD NOT DELIVER IT.  `heilmeier.md` section 4 registers

  P3 -- "part of the reported gain is PARALLELISM, not prediction: the prediction-attributable fraction F of
  the serial-baseline gain is below 0.7, and decreasing in rho.  Justification: the systems baselines are
  serial, so a speculative call also buys concurrency any parallel schedule buys."

and section 2.3 promises "a matched-parallelism control (the same capacity spent on unpredicted useful work)
that separates the prediction's contribution from the parallelism a serial baseline never had".  Step 6
measured a PROXY for F (the hiding channel's share of the decomposition: >= 0.9866) and recorded that the
promised arm "cannot be built" in v0, because in v0 "issuing early IS the hit": `agent_run` draws a RANDOM
mask and issues early exactly on it, so the flagged set carries no information and the width is the whole
story.

THE DISTINCTION STEP 6 CONFLATED, AND WHAT THIS FILE SEPARATES.  "A wrong prediction costs nothing" and "the
prediction's information is worth nothing" are different statements.  In v0 the prediction has no COST --
but the SET of steps it flags still determines the schedule, and steps differ in how much early issue helps
them.  So the control exists as soon as WIDTH and CHOICE are separate objects:

    width  h  -- the FRACTION of steps whose call is issued early (= the capacity spent, unchanged)
    choice    -- WHICH h-fraction: a blind draw with no information, or a selection that ranks the steps

The control arm holds h fixed and chooses blindly; the arm under test holds h fixed and chooses by
information.  Both spend the same capacity by construction (exactly k = round(h * steps) flags per agent),
so the difference between them is the information and nothing else:

    F := (G_selected - G_blind) / G_selected,     G_x := (L_serial - L_x) / L_serial

MEASURED FIRST, BECAUSE THE SELECTOR'S EXISTENCE RESTS ON IT (the probe this file formalises as check V1):
the engine's own per-step effect of issuing a call early is, with no queueing,

    d(a,k) := latency_serial(a,k) - latency_eager(a,k) = min(T, S)      (max |d - min(T,S)| = 2.3e-13)

so the ordering a selector needs is available and EXACT, and -- the round's first surprise -- the steps most
worth hiding are the SHORT calls (a call shorter than the think phase is hidden ENTIRELY, saving all of S;
a longer one is only partly hidden, saving T).  The naive rule "hide the long calls" is backwards.

WHAT THIS FILE DOES NOT CLAIM.  There is no cost for a misprediction here: the charge channel is step 7's
(q = 0 throughout, so this variant isolates P3 and nothing else).  F therefore measures what INFORMATION buys
at a fixed width, NOT what an accurate-but-costly predictor is worth in a real system -- that second question
is P4's and step 7 answered it separately.  The two are not interchangeable and the report says so.

`instrument_v0.py` is imported UNMODIFIED; this file re-implements the scheduling loop because the loop is
what carries the mask, and the re-implementation is anchored: with v0's own random mask it must reproduce
`agent_run` per-step, BITWISE (check V2).
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

# Two arithmetic paths over the same draws must agree to the resolution of the coarser one (step 4 measured
# the pair at 7.0e-15; this is six orders above it).  Used for V1 and V3.
AGREE_TOL = 1e-09
# V2 is a BITWISE claim about two runs of the same arithmetic, so its tolerance is the arithmetic's own.
BITWISE_TOL = 1e-12

# The mask modes.  `v0` reproduces the instrument's own draw (Bernoulli(h) per step, from the same rng
# position) and exists ONLY for the anchor; the deciding comparison uses the two EXACT modes, which flag
# exactly k = round(h*steps) steps per agent so that both arms spend identical capacity.
MASK_V0 = "v0"
MASK_BLIND = "blind"
MASK_SELECTED = "selected"

# (h, c) grid for the deciding sweep.  c is the worker pool; rho is MEASURED, never set.
H_GRID = (0.25, 0.50, 0.75)
C_GRID = (2, 4, 8, 16)


# --------------------------------------------------------------------------- the scheduler (mask explicit)
def build_mask(mode, cfg, h, seed, order=None):
    """The flag set, one list of 0/1 per agent.

    `v0`      -- Bernoulli(h) per step, drawn from the model's OWN stream at the model's OWN position: the
                 draws must be consumed exactly as `agent_run` consumes them (T, then S, THEN the hit mask),
                 or the mask is a different random object and the reproduction anchor cannot hold.  That
                 position is the whole reason this function takes the config.
    `blind`   -- exactly k = round(h*steps) flags per agent, chosen uniformly at random.
    `selected`-- exactly k flags per agent: the k steps ranked highest by `order` (the selector's information).

    Returns the mask plus the flag count, because "both arms spend the same capacity" is a CLAIM the caller
    checks (`V3`) rather than a property of the code that a reader is asked to believe.
    """
    agents, steps = cfg["agents"], cfg["steps"]
    k = int(round(h * steps))
    if mode == MASK_V0:
        rng = random.Random(seed)
        for _ in range(agents):                          # T, exactly as the model draws it
            for _ in range(steps):
                rng.expovariate(1.0 / cfg["mT"])
        for _ in range(agents):                          # then S
            for _ in range(steps):
                I.draw_service(rng, cfg["mS"], cfg["tail"])
        return ([[1 if rng.random() < h else 0 for _ in range(steps)] for _ in range(agents)],
                {"k": None, "per_agent": None})
    if mode == MASK_BLIND:
        rng = random.Random(seed * 1000003 + 17)
        mask = []
        for _ in range(agents):
            idx = list(range(steps))
            rng.shuffle(idx)
            row = [0] * steps
            for j in idx[:k]:
                row[j] = 1
            mask.append(row)
        return mask, {"k": k, "per_agent": [sum(r) for r in mask]}
    if mode == MASK_SELECTED:
        if order is None:
            raise ValueError("the selected mask needs the selector's `order`")
        mask = []
        for a in range(agents):
            idx = sorted(range(steps), key=lambda j: -order[a][j])
            row = [0] * steps
            for j in idx[:k]:
                row[j] = 1
            mask.append(row)
        return mask, {"k": k, "per_agent": [sum(r) for r in mask]}
    raise ValueError("unknown mask mode %r" % (mode,))


def run_mask(cfg, c, mask):
    """One run with an EXPLICIT flag set: the same scheduler as `instrument_v0.agent_run(speculate=True)`,
    with `HIT[a][k]` replaced by `mask[a][k]`.  Returns the same fields, so the two can be compared
    directly.  The draws are taken in the model's own order (T, then S) and nothing else is drawn.
    """
    n_agents, mT, mS, steps, seed = cfg["agents"], cfg["mT"], cfg["mS"], cfg["steps"], cfg["seed"]
    tail = cfg["tail"]
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / mT) for _ in range(steps)] for _ in range(n_agents)]
    S = [[I.draw_service(rng, mS, tail) for _ in range(steps)] for _ in range(n_agents)]

    import heapq
    events, seq = [], 0
    free = [0.0] * c
    heapq.heapify(free)
    busy = 0.0
    lat = [[] for _ in range(n_agents)]
    step_start = [0.0] * n_agents
    done = [0] * n_agents
    now = [0.0]
    think_end_at, call_done_at = {}, {}

    def push(t, kind, payload):
        nonlocal seq
        seq += 1
        heapq.heappush(events, (t, seq, kind, payload))

    def submit(job):
        nonlocal busy
        f = heapq.heappop(free)
        start = max(f, job.arrival)
        finish = start + job.service
        busy += job.service
        heapq.heappush(free, finish)
        push(finish, "job_done", job)

    def start_step(a):
        k = done[a]
        step_start[a] = now[0]
        if mask[a][k]:
            submit(I.Job(now[0], S[a][k], a, k, "real"))
        push(now[0] + T[a][k], "think_end", (a, k))

    def on_think_end(payload):
        a, k = payload
        think_end_at[(a, k)] = now[0]
        if not mask[a][k]:
            submit(I.Job(now[0], S[a][k], a, k, "real"))
        else:
            finish_if_both(a, k)

    def finish_if_both(a, k):
        if (a, k) not in think_end_at or (a, k) not in call_done_at:
            return
        end = max(think_end_at[(a, k)], call_done_at[(a, k)])
        lat[a].append(end - step_start[a])
        done[a] += 1
        if done[a] < steps:
            now[0] = end
            start_step(a)

    def on_job_done(j):
        if j.kind == "real":
            call_done_at[(j.agent, j.step)] = now[0]
            finish_if_both(j.agent, j.step)

    for a in range(n_agents):
        start_step(a)
    while events:
        t, _s, kind, payload = heapq.heappop(events)
        now[0] = t
        if kind == "job_done":
            on_job_done(payload)
        else:
            on_think_end(payload)

    makespan = max(step_start[a] + lat[a][-1] for a in range(n_agents)) if all(lat) else 0.0
    warm = min(20, steps // 5)
    samples = [x for a in range(n_agents) for x in lat[a][warm:]]
    return {"mean_latency": statistics.fmean(samples), "n_samples": len(samples),
            "rho": busy / (c * makespan) if makespan else 0.0, "busy": busy, "makespan": makespan,
            "ci": I.batch_ci(samples),
            "latencies": [x for a in range(n_agents) for x in lat[a]],
            "trace": [(a, k, round(lat[a][k], 12)) for a in range(n_agents)
                      for k in range(len(lat[a]))]}


# --------------------------------------------------------------------------- the selector's information
def per_step_value(cfg, c=None):
    """The engine's own value of issuing step (a,k) early, re-derived from the draws: `min(T, S)`.

    Declared as an ANCHOR-BACKED definition, not an assumption: with no queueing the engine's measured
    per-step effect equals it to 2.3e-13 (check V1), and it ranks the steps exactly (top-quartile overlap
    1.000 on the same runs).  The draws are taken in the model's own order, so this is the same object the
    engine schedules.
    """
    n_agents, mT, mS, steps, seed = cfg["agents"], cfg["mT"], cfg["mS"], cfg["steps"], cfg["seed"]
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / mT) for _ in range(steps)] for _ in range(n_agents)]
    S = [[I.draw_service(rng, mS, cfg["tail"]) for _ in range(steps)] for _ in range(n_agents)]
    return {"T": T, "S": S, "value": [[min(T[a][k], S[a][k]) for k in range(steps)]
                                      for a in range(n_agents)]}


def draw_stream(cfg, seed):
    """The model's own draw stream for one seed, re-derived (T then S), for the checks that compare a
    re-derivation against what a run scheduled."""
    n_agents, mT, mS, steps = cfg["agents"], cfg["mT"], cfg["mS"], cfg["steps"]
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / mT) for _ in range(steps)] for _ in range(n_agents)]
    S = [[I.draw_service(rng, mS, cfg["tail"]) for _ in range(steps)] for _ in range(n_agents)]
    return T, S


# --------------------------------------------------------------------------- the measurement
def arm_gains(cfg, c, h, seeds):
    """Per seed: serial latency, the two arms' latencies, their relative gains, and F.

    The two arms are built from the SAME draws and the SAME seed, and flag the same number of steps, so a
    difference between them is a difference in CHOICE.  A seed whose selected-arm gain is not positive has
    no gain to split: F is NOT DEFINED there, and the seed is counted, never silently dropped.
    """
    out = []
    for seed in seeds:
        c1 = dict(cfg, seed=seed)
        ser = I.agent_run(cfg["agents"], cfg["mT"], cfg["mS"], 0.0, cfg["steps"], seed,
                          tail=cfg["tail"], q=0.0, comp=0.0, speculate=False, c=c)
        val = per_step_value(c1)["value"]
        m_blind, info_blind = build_mask(MASK_BLIND, cfg, h, seed)
        m_sel, info_sel = build_mask(MASK_SELECTED, cfg, h, seed, order=val)
        r_blind = run_mask(c1, c, m_blind)
        r_sel = run_mask(c1, c, m_sel)
        ls, lb, lg = ser["mean_latency"], r_blind["mean_latency"], r_sel["mean_latency"]
        gb = (ls - lb) / ls
        gg = (ls - lg) / ls
        out.append({"seed": seed, "latency_serial": ls, "latency_blind": lb, "latency_selected": lg,
                    "gain_blind": gb, "gain_selected": gg,
                    "rho_serial": ser["rho"], "rho_blind": r_blind["rho"], "rho_selected": r_sel["rho"],
                    "F": (gg - gb) / gg if gg > 0 else None,
                    "flag_count_blind": sum(info_blind["per_agent"]),
                    "flag_count_selected": sum(info_sel["per_agent"]),
                    "k": info_blind["k"]})
    return out


def cell_summary(rows):
    """Aggregate one cell over seeds: gains with t intervals, F with its interval and its exclusions."""
    gb = [r["gain_blind"] for r in rows]
    gg = [r["gain_selected"] for r in rows]
    fs = [r["F"] for r in rows if r["F"] is not None]
    return {"n_seeds": len(rows), "n_F_defined": len(fs), "n_F_excluded": len(rows) - len(fs),
            "gain_blind": {"mean": statistics.fmean(gb), "ci": B1.t_ci(gb)},
            "gain_selected": {"mean": statistics.fmean(gg), "ci": B1.t_ci(gg)},
            "F": ({"mean": statistics.fmean(fs), "ci": B1.t_ci(fs)} if len(fs) > 1 else None),
            "rho_serial": statistics.fmean([r["rho_serial"] for r in rows]),
            "rho_blind": statistics.fmean([r["rho_blind"] for r in rows]),
            "rho_selected": statistics.fmean([r["rho_selected"] for r in rows]),
            "flags_equal": all(r["flag_count_blind"] == r["flag_count_selected"] for r in rows),
            "k": rows[0]["k"]}


def run_signature(rows):
    """The per-seed triple of latencies for one cell: two cells with the same signature are THE SAME RUN, so
    any difference in their MEASURED rho is a difference in the coordinate's denominator and not a load.

    This is a measurement, not a rule about `c`: the model stops queueing once the pool reaches the agent
    count (step 1's anchor A4 found that, and it is what the c >= A cells here are), and a verdict that read
    those cells as a load ladder would be reading rho's divisor.
    """
    return tuple((r["latency_serial"], r["latency_blind"], r["latency_selected"]) for r in rows)


def coordinate_only_pairs(cells, raw):
    """The adjacent (h, rho-ordered) pairs whose two cells are the same run, by signature."""
    sig = {k: run_signature(rows) for k, rows in raw.items()}
    out = set()
    for h in sorted({c["h"] for c in cells}):
        fam = sorted([c for c in cells if c["h"] == h and c["F"]], key=lambda c: c["rho_serial"])
        for lo_c, hi_c in zip(fam, fam[1:]):
            if sig.get(lo_c["key"]) == sig.get(hi_c["key"]):
                out.add((lo_c["key"], hi_c["key"]))
    return out


def p3_verdicts(cells, coord_only=None):
    """P3a ("F < 0.7 over every cell") and P3b ("F decreasing in rho"), from the declared rules.

    P3a: CONFIRMED iff every cell with a defined F has its whole interval strictly below 0.7; CONTRADICTED
    iff at least one cell's interval lies strictly above 0.7; UNRESOLVED otherwise (the rule's own
    resolution is the interval, and a cell whose interval straddles 0.7 cannot decide it).
    P3b: order each h-family's cells by MEASURED rho ascending and take the paired-by-seed difference
    dF = F(higher rho) - F(lower rho) at each adjacent pair; a pair is an INCREASE/DECREASE iff its interval
    excludes zero, else a tie.  CONFIRMED iff no increase and at least one decrease; CONTRADICTED iff any
    increase; UNRESOLVED otherwise.
    """
    defined = [c for c in cells if c["F"]]
    if not defined:
        return {"P3a": "UNRESOLVED (no cell has a defined F)", "P3b": "UNRESOLVED", "adjacent": []}
    below = [c for c in defined if c["F"]["ci"][1] < 0.7]
    above = [c for c in defined if c["F"]["ci"][0] > 0.7]
    if above:
        p3a = "CONTRADICTED (%d of %d cells strictly above 0.7)" % (len(above), len(defined))
    elif len(below) == len(defined):
        p3a = "CONFIRMED (every one of the %d cells strictly below 0.7)" % len(defined)
    else:
        p3a = "UNRESOLVED (%d below, none strictly above 0.7, %d straddling)" % (
            len(below), len(defined) - len(below))
    adjacent = []
    coord_only = coord_only or set()
    for h in sorted({c["h"] for c in cells}):
        fam = sorted([c for c in cells if c["h"] == h and c["F"]], key=lambda c: c["rho_serial"])
        for lo_c, hi_c in zip(fam, fam[1:]):
            if (lo_c["key"], hi_c["key"]) in coord_only:
                adjacent.append({"h": h, "rho_lo": lo_c["rho_serial"], "rho_hi": hi_c["rho_serial"],
                                 "n_pairs": len(lo_c["_per_seed_F"]), "mean": 0.0, "ci": [0.0, 0.0],
                                 "verdict": "COORDINATE-ONLY (the two cells are the same run: identical"
                                            " per-seed latencies, so this pair carries no load difference)",
                                 "informative": False})
                continue
            fl, fh = lo_c.get("_per_seed_F", {}), hi_c.get("_per_seed_F", {})
            common = sorted(set(fl) & set(fh))
            pairs = [fh[s] - fl[s] for s in common
                     if fl.get(s) is not None and fh.get(s) is not None]
            if len(pairs) > 1:
                ci = B1.t_ci(pairs)
                v = "INCREASE" if ci[0] > 0 else ("DECREASE" if ci[1] < 0 else "tie")
            else:
                ci, v = None, "n/a (fewer than two paired seeds)"
            adjacent.append({"h": h, "rho_lo": lo_c["rho_serial"], "rho_hi": hi_c["rho_serial"],
                             "n_pairs": len(pairs), "mean": (statistics.fmean(pairs) if pairs else None),
                             "ci": ci, "verdict": v, "informative": True})
    informative = [a for a in adjacent if a.get("informative")]
    inc = [a for a in informative if a["verdict"] == "INCREASE"]
    dec = [a for a in informative if a["verdict"] == "DECREASE"]
    n_coord = len(adjacent) - len(informative)
    if inc:
        p3b = "CONTRADICTED (%d of %d informative pairs increase significantly)" % (len(inc), len(informative))
    elif dec:
        p3b = "CONFIRMED (no increase, %d decreases, over %d informative pair(s); %d pair(s) are"\
              " coordinate-only and carry no load difference)" % (len(dec), len(informative), n_coord)
    elif informative:
        p3b = "UNRESOLVED (no significant change in either direction over %d pairs)" % len(informative)
    else:
        p3b = "UNRESOLVED (no informative adjacent pair to compare: all %d are coordinate-only)" % n_coord
    return {"P3a": p3a, "P3b": p3b, "adjacent": adjacent, "n_informative": len(informative),
            "n_coordinate_only": n_coord}


# --------------------------------------------------------------------------- the run's own checks
def check_per_step_identity(cfg, c, seed):
    """V1: with no queueing, the engine's per-step effect of early issue EQUALS min(T, S).

    Measured against the engine (serial vs eager on the same seed), not against a formula: the formula is
    what the check compares the engine to.  Also returns the ordering agreement, because the selector's
    existence rests on the ORDER, not only on the level.
    """
    ser = I.agent_run(cfg["agents"], cfg["mT"], cfg["mS"], 0.0, cfg["steps"], seed,
                      tail=cfg["tail"], q=0.0, comp=0.0, speculate=False, c=c)
    eag = I.agent_run(cfg["agents"], cfg["mT"], cfg["mS"], 1.0, cfg["steps"], seed,
                      tail=cfg["tail"], q=0.0, comp=0.0, speculate=True, c=c)
    T, S = draw_stream(cfg, seed)
    worst, order_num, order_den = 0.0, 0, 0
    for a in range(cfg["agents"]):
        d = [ser["latencies"][a * cfg["steps"] + k] - eag["latencies"][a * cfg["steps"] + k]
             for k in range(cfg["steps"])]
        v = [min(T[a][k], S[a][k]) for k in range(cfg["steps"])]
        for x, y in zip(d, v):
            worst = max(worst, abs(x - y))
        q = max(1, cfg["steps"] // 4)
        order_num += len(set(sorted(range(cfg["steps"]), key=lambda k: -d[k])[:q])
                         & set(sorted(range(cfg["steps"]), key=lambda k: -v[k])[:q]))
        order_den += q
    return {"worst_abs": worst, "order_agreement": order_num / order_den if order_den else None}


def check_reproduces_v0(cfg, c, h, seeds, planted=None):
    """V2: with v0's own mask, this scheduler reproduces `agent_run(speculate=True)` BITWISE, per step.

    The masks are built before the loop, outside the timed path, so the run's own draws are untouched and the
    two engines see the same T, S and the same flags.  `planted` (an arm's own defect) replaces the mask with
    its complement: the anchor must then FAIL, which is what makes it an anchor and not a tautology.
    """
    worst, n = 0.0, 0
    for seed in seeds:
        c1 = dict(cfg, seed=seed)
        m, _info = build_mask(MASK_V0, cfg, h, seed)
        if planted == "complement":
            m = [[1 - x for x in row] for row in m]
        mine = run_mask(c1, c, m)
        theirs = I.agent_run(cfg["agents"], cfg["mT"], cfg["mS"], h, cfg["steps"], seed,
                             tail=cfg["tail"], q=0.0, comp=0.0, speculate=True, c=c)
        for x, y in zip(mine["latencies"], theirs["latencies"]):
            worst = max(worst, abs(x - y))
            n += 1
    return {"worst_abs": worst, "n_compared": n}


def check_capacity_matched(rows):
    """V3: the two arms flagged the same number of steps, per seed -- the control's defining property."""
    bad = [r for r in rows if r["flag_count_blind"] != r["flag_count_selected"]]
    return {"ok": not bad, "n_seeds": len(rows), "bad": [r["seed"] for r in bad],
            "k": rows[0]["k"] if rows else None}


def check_selector_is_the_top_k(cfg, c, h, seeds, planted=None):
    """V4: the selected mask flags exactly the k steps the selector ranks highest -- and a BLIND mask does
    not.  The second half is the negative reading: without it, "the flags are the top k" could be true of
    any mask that happens to agree with the ranking.
    """
    agree_sel, agree_blind = 0, 0
    for seed in seeds:
        c1 = dict(cfg, seed=seed)
        val = per_step_value(c1)["value"]
        if planted == "wrong_order":
            val = [[-x for x in row] for row in val]
        k = int(round(h * cfg["steps"]))
        m_sel, _ = build_mask(MASK_SELECTED, cfg, h, seed, order=val)
        m_blind, _ = build_mask(MASK_BLIND, cfg, h, seed)
        top = [[1 if j in set(sorted(range(cfg["steps"]), key=lambda j: -val[a][j])[:k]) else 0
                for j in range(cfg["steps"])] for a in range(cfg["agents"])]
        agree_sel += sum(1 for a in range(cfg["agents"]) for j in range(cfg["steps"])
                         if m_sel[a][j] == top[a][j])
        agree_blind += sum(1 for a in range(cfg["agents"]) for j in range(cfg["steps"])
                           if m_blind[a][j] == top[a][j])
    total = cfg["agents"] * cfg["steps"] * len(seeds)
    return {"selected_agreement": agree_sel / total, "blind_agreement": agree_blind / total, "n": total}


def check_pool_beyond_the_agents_is_a_coordinate(cells, raw, agents):
    """V5: above the agent count the model stops queueing, so those cells are the SAME RUN measured in a
    different rho coordinate -- and at least one cell below the agent count must genuinely differ.

    Both halves are needed.  Without the first, the report would read a rho ladder that is a divisor; without
    the second, "everything is the same run" would pass this check trivially on a design that never
    contended.  A cell whose `pool` is not below `agents` for any h means the reading was not taken:
    NOT TAKEN, with the reason, and it is not registered as a check.
    """
    sig = {k: run_signature(rows) for k, rows in raw.items()}
    above = [k for k in sig if k.split("/c")[1].isdigit() and int(k.split("/c")[1]) >= agents]
    below = [k for k in sig if k.split("/c")[1].isdigit() and int(k.split("/c")[1]) < agents]
    if not below:
        return {"status": "NOT TAKEN", "reason": "no cell has a pool below the agent count (%d)" % agents}
    if not above:
        return {"status": "NOT TAKEN", "reason": "no cell has a pool at or above the agent count"}
    # every above-the-pool cell with the same h must share a signature, and must differ from the below one
    ok = True
    detail = []
    for h in sorted({k.split("/")[0] for k in sig}):
        up = sorted([k for k in above if k.startswith(h + "/")], key=lambda k: int(k.split("/c")[1]))
        dn = sorted([k for k in below if k.startswith(h + "/")], key=lambda k: int(k.split("/c")[1]))
        same_up = len({sig[k] for k in up}) == 1
        differ = all(sig[u] != sig[d] for u in up for d in dn)
        detail.append({"h": h, "above": up, "below": dn, "above_all_same_run": same_up,
                       "above_differs_from_below": differ})
        ok = ok and same_up and differ
    return {"status": "READ", "ok": ok, "agents": agents, "detail": detail}


def run_checks(v1, v2, v3, v4, cells):
    return {
        "the_per_step_effect_equals_min_T_S": v1["worst_abs"] <= AGREE_TOL,
        "the_selector_ranks_the_steps": (v1["order_agreement"] is not None and v1["order_agreement"] == 1.0),
        "the_scheduler_reproduces_v0_bitwise": v2["worst_abs"] <= BITWISE_TOL,
        "the_two_arms_flag_the_same_capacity": all(c["flags_equal"] for c in cells),
        "the_selected_mask_is_the_top_k": v4["selected_agreement"] == 1.0,
        "the_blind_mask_is_not_the_top_k": v4["blind_agreement"] < 1.0,
    }


# --------------------------------------------------------------------------- report
def fmt_ci(ci, spec="%+.5f"):
    return "-" if not ci else (spec + ".." + spec) % tuple(ci)


def fmt_pct(x):
    return "-" if x is None else "%+.3f%%" % (100.0 * x)


def report(cells, verdicts, checks, v1, v2, v3, v4, cfg0, seeds, v5=None):
    print("== step 9: the matched-parallelism control (registered P3) | %d seeds %d..%d | mT=%.1f mS=%.1f"
          " steps=%d ==" % (len(seeds), seeds[0], seeds[-1], cfg0["mT"], cfg0["mS"], cfg0["steps"]))
    print("   width h = the fraction of steps issued early (the capacity, IDENTICAL in both arms);")
    print("   choice  = which h-fraction: blind draw vs a selector ranking steps by min(T,S).")
    print()
    print("     %-6s %-4s %-8s %-11s %-11s %-11s %-20s %-9s"
          % ("h", "c", "k/agent", "rho", "G blind", "G selected", "F = (Gsel-Gb)/Gsel", "flags"))
    for c_ in sorted(cells, key=lambda x: (x["h"], x["pool"])):
        f = c_["F"]
        print("     %-6.2f %-4d %-8s %-11.4f %-11s %-11s %-20s %-9s"
              % (c_["h"], c_["pool"], c_["k"], c_["rho_serial"], fmt_pct(c_["gain_blind"]["mean"]),
                 fmt_pct(c_["gain_selected"]["mean"]),
                 ("%.4f [%s]" % (f["mean"], fmt_ci(f["ci"], "%+.4f"))) if f else "NOT DEFINED",
                 "=" if c_["flags_equal"] else "DIFFER"))
    print()
    print("   P3a (registered: F < 0.7 over every cell): %s" % verdicts["P3a"])
    print("   P3b (registered: F decreasing in rho):    %s" % verdicts["P3b"])
    for a in verdicts["adjacent"]:
        print("     h=%.2f  rho %.4f -> %.4f : n=%d mean %s  %s"
              % (a["h"], a["rho_lo"], a["rho_hi"], a["n_pairs"],
                 ("%+.5f" % a["mean"]) if a["mean"] is not None else "-", a["verdict"]))
    print("     (%d informative pair(s), %d coordinate-only)"
          % (verdicts.get("n_informative", 0), verdicts.get("n_coordinate_only", 0)))
    print()
    print("   checks: " + " | ".join("%s=%s" % (k, "OK" if v else "FAIL") for k, v in sorted(checks.items())))
    print("   V1 per-step effect vs min(T,S): worst |d - min| %.2e | selector's ranking agreement %.3f"
          % (v1["worst_abs"], v1["order_agreement"]))
    print("   V2 reproduction of the v0 instrument: worst per-step |delta| %.2e over %d steps"
          % (v2["worst_abs"], v2["n_compared"]))
    print("   V3 capacity: k = %s flags per agent, identical in both arms on %s"
          % (v3["k"], ("every seed" if v3["ok"] else "NOT every seed: %s" % v3["bad"])))
    print("   V4 selector: selected mask equals the top-k on %.3f of positions, blind on %.3f"
          % (v4["selected_agreement"], v4["blind_agreement"]))
    if v5 is not None:
        print("   V5 pool vs agent count: %s%s" % (v5["status"],
              "" if v5["status"] != "READ" else
              " -- at or above %d worker(s) the cells with the same h are one run, and each differs from"
              " the contended one: %s" % (v5["agents"], all(d["above_all_same_run"] and
                                                            d["above_differs_from_below"]
                                                            for d in v5["detail"]))))


# --------------------------------------------------------------------------- selftest
def case(name, ok, detail):
    return (name, bool(ok), detail)


def fake_trace(base, jitter, steps):
    return [{"latencies": [base + jitter * k for k in range(steps)]}]


def fake_rows(gains, rhos=None, k=4):
    """A fixture carrying EVERY field `cell_summary` reads -- a fixture missing one is a fixture that tests
    the reader's exception handling instead of its comparison (this arm set caught exactly that on its first
    run: the rows had no `rho_blind`)."""
    out = []
    for i, (gb, gg) in enumerate(gains):
        rho = (rhos[i] if rhos else 0.5 + 0.01 * i)
        out.append({"seed": 100 + i, "gain_blind": gb, "gain_selected": gg,
                    "F": (gg - gb) / gg if gg > 0 else None,
                    "rho_serial": rho, "rho_blind": rho, "rho_selected": rho,
                    "latency_serial": 1.0, "latency_blind": 1.0 - gb, "latency_selected": 1.0 - gg,
                    "flag_count_blind": k, "flag_count_selected": k, "k": k})
    return out


def cell(h, pool, rows):
    s = cell_summary(rows)
    s["h"], s["pool"] = h, pool
    s["key"] = "h%.2f/c%d" % (h, pool)
    s["_per_seed_F"] = {r["seed"]: r["F"] for r in rows}
    return s


def selftest():
    out = []
    cfg = I.default_cfg()

    # 1. the mask builders: v0's is Bernoulli(h) with the right expectation; the two exact modes flag
    #    EXACTLY k per agent (the capacity claim), and the selected one picks the top of its order.
    m_v0, _ = build_mask(MASK_V0, dict(cfg, agents=8, steps=400), 0.5, 101)
    rate = sum(sum(r) for r in m_v0) / float(8 * 400)
    c1 = dict(cfg, seed=101)
    val = per_step_value(c1)["value"]
    m_b, i_b = build_mask(MASK_BLIND, cfg, 0.375, 101)
    m_s, i_s = build_mask(MASK_SELECTED, cfg, 0.375, 101, order=val)
    k = int(round(0.375 * cfg["steps"]))
    # Both sides are the SAME SET, and the first version of this arm compared two ORDERINGS of it (the
    # selector's value-descending order against the mask's index order), so it was red while the selector was
    # right.  A comparison of an object with a re-ordering of itself is Class 61's defect, one level down.
    topk_ok = all(set(sorted(range(cfg["steps"]), key=lambda j: -val[a][j])[:k])
                  == set(j for j in range(cfg["steps"]) if m_s[a][j]) for a in range(cfg["agents"]))
    topk_order_ok = all(sorted(range(cfg["steps"]), key=lambda j: -val[a][j])[:k]
                        == sorted(j for j in range(cfg["steps"]) if m_s[a][j])
                        or True for a in range(cfg["agents"]))
    out.append(case("mask_builders_do_what_they_say",
                    abs(rate - 0.5) < 0.02 and i_b["per_agent"] == [k] * cfg["agents"]
                    and i_s["per_agent"] == [k] * cfg["agents"] and topk_ok,
                    "v0 rate %.4f (h=0.5); exact modes flag k=%d each; selected = top-k by the order" % (rate, k)))

    # 2. THE ANCHOR CAN FAIL: with the mask complemented, the reproduction of v0 must break loudly.
    ok_anchor = check_reproduces_v0(cfg, 8, 0.5, [101, 102])
    bad_anchor = check_reproduces_v0(cfg, 8, 0.5, [101, 102], planted="complement")
    out.append(case("the_v0_reproduction_anchor_can_fail",
                    ok_anchor["worst_abs"] <= BITWISE_TOL and bad_anchor["worst_abs"] > 1e-03,
                    "honest worst |delta| %.2e; complement-mask worst %.2e (n=%d)"
                    % (ok_anchor["worst_abs"], bad_anchor["worst_abs"], ok_anchor["n_compared"])))

    # 3. V1 is a measurement of the ENGINE, and it is two-sided: the identity holds, and the ordering
    #    agreement is exactly 1 (a selector that ranked wrongly would still pass a level-only check).
    v1 = check_per_step_identity(cfg, cfg["agents"], 101)      # c = agents => no queueing
    v1_bad = check_per_step_identity(cfg, 2, 101)              # c < agents => queueing, identity must fail
    out.append(case("the_per_step_identity_is_measured_and_can_fail",
                    v1["worst_abs"] <= AGREE_TOL and v1["order_agreement"] == 1.0
                    and v1_bad["worst_abs"] > 1e-03,
                    "unqueued worst %.2e / ranking %.3f; QUEUED cell worst %.2e (so the identity is a"
                    " no-queue statement, not a tautology)"
                    % (v1["worst_abs"], v1["order_agreement"], v1_bad["worst_abs"])))

    # 4. the capacity check fires on an unequal plant
    eq_rows = fake_rows([(0.10, 0.20), (0.11, 0.21)])
    un_rows = fake_rows([(0.10, 0.20), (0.11, 0.21)])
    un_rows[1]["flag_count_selected"] += 1
    out.append(case("the_capacity_check_fires",
                    check_capacity_matched(eq_rows)["ok"] and not check_capacity_matched(un_rows)["ok"],
                    "equal counts pass; one extra flag in one seed is caught and named"))

    # 5. F's arithmetic, both directions: a selected arm that is better gives F > 0; the same two arms
    #    SWAPPED must give F < 0, and an arm whose gain is not positive must have F NOT DEFINED.
    f_pos = cell(0.5, 8, fake_rows([(0.10, 0.20)] * 6))
    f_neg = cell(0.5, 8, fake_rows([(0.20, 0.10)] * 6))
    f_und = cell(0.5, 8, fake_rows([(0.10, 0.0)] * 6))
    out.append(case("F_arithmetic_is_two_sided",
                    f_pos["F"]["mean"] > 0 and f_neg["F"]["mean"] < 0 and f_und["F"] is None
                    and f_und["n_F_excluded"] == 6,
                    "(Gsel,Gb)=(0.20,0.10)->F=%+.3f; swapped->F=%+.3f; Gsel=0->NOT DEFINED with 6 seeds"
                    " counted" % (f_pos["F"]["mean"], f_neg["F"]["mean"])))

    # 6. P3a and P3b are each reachable in all three verdicts
    lo = cell(0.5, 8, fake_rows([(0.10, 0.20)] * 6))       # F = 0.5, well below 0.7
    hi = cell(0.5, 16, fake_rows([(0.01, 0.20)] * 6))      # F = 0.95, above 0.7
    mid = cell(0.5, 32, fake_rows([(0.09, 0.20)] * 6))     # F = 0.55 -> the interval may straddle 0.7
    a_conf = p3_verdicts([lo])
    a_contra = p3_verdicts([lo, hi])
    # P3b's three branches.  F falls with rho iff the HIGH-rho cell's F is smaller: F = (Gsel-Gb)/Gsel, so
    # (0.10,0.40) -> 0.75 and (0.20,0.40) -> 0.50, i.e. the falling pair is the FIRST of these two fixtures.
    # The first version of this arm had them the other way round and asserted a fall for a rise -- an arm is a
    # claim about its object, and this one was simply false about it.
    b_conf = p3_verdicts([cell(0.5, 8, fake_rows([(0.10, 0.40)] * 6, rhos=[0.5] * 6)),
                          cell(0.5, 16, fake_rows([(0.20, 0.40)] * 6, rhos=[0.9] * 6))])
    b_contra = p3_verdicts([cell(0.5, 8, fake_rows([(0.10, 0.40)] * 6, rhos=[0.5] * 6)),
                            cell(0.5, 16, fake_rows([(0.01, 0.40)] * 6, rhos=[0.9] * 6))])
    # the two UNRESOLVED branches, each reached for its OWN reason: P3a when no cell is strictly below and
    # none strictly above (an interval straddling 0.7 -- so the per-seed F must SPREAD, a degenerate interval
    # cannot straddle anything); P3b when the paired difference's interval contains zero.
    spread_lo = [{"seed": 100 + i, "gain_blind": gb, "gain_selected": gg,
                  "F": (gg - gb) / gg, "rho_serial": 0.5, "rho_blind": 0.5, "rho_selected": 0.5,
                  "latency_serial": 1.0, "latency_blind": 1.0 - gb, "latency_selected": 1.0 - gg,
                  "flag_count_blind": 4, "flag_count_selected": 4, "k": 4}
                 # F centres on 0.70 with enough SPREAD that the interval straddles it: with a
                 # degenerate interval no cell can be "not strictly below and not strictly above", so the
                 # UNRESOLVED branch would be unreachable BY CONSTRUCTION rather than by the data.
                 for i, (gb, gg) in enumerate([(0.16, 0.40), (0.14, 0.40), (0.12, 0.40),
                                               (0.10, 0.40), (0.088, 0.40), (0.112, 0.40)])]   # F .60-.78
    a_unres = p3_verdicts([cell(0.5, 8, spread_lo)])
    mix_lo = fake_rows([(0.10, 0.40), (0.20, 0.40), (0.10, 0.40), (0.20, 0.40), (0.10, 0.40), (0.20, 0.40)],
                       rhos=[0.5] * 6)
    mix_hi = fake_rows([(0.10, 0.40), (0.20, 0.40), (0.10, 0.40), (0.20, 0.40), (0.10, 0.40), (0.20, 0.40)],
                       rhos=[0.9] * 6)
    b_unres = p3_verdicts([cell(0.5, 8, mix_lo), cell(0.5, 16, mix_hi)])
    out.append(case("P3a_and_P3b_are_reachable_in_all_three_branches",
                    a_conf["P3a"].startswith("CONFIRMED") and a_contra["P3a"].startswith("CONTRADICTED")
                    and a_unres["P3a"].startswith("UNRESOLVED")
                    and b_conf["P3b"].startswith("CONFIRMED") and b_contra["P3b"].startswith("CONTRADICTED")
                    and b_unres["P3b"].startswith("UNRESOLVED"),
                    "P3a CONFIRMED/CONTRADICTED/UNRESOLVED and P3b CONFIRMED/CONTRADICTED/UNRESOLVED all"
                    " reachable (UNRESOLVED P3a at F=%.2f-%.2f, interval straddles 0.7; UNRESOLVED P3b on a"
                    " paired difference whose interval contains 0)"
                    % (min(r["F"] for r in spread_lo), max(r["F"] for r in spread_lo))))

    # 7. the selection is not the same object as the blind draw: two masks at the same h must differ, and
    #    the selector's advantage must vanish when the per-step values are all equal (no information).
    m1, _ = build_mask(MASK_BLIND, dict(cfg, agents=4, steps=200), 0.5, 101)
    m2, _ = build_mask(MASK_BLIND, dict(cfg, agents=4, steps=200), 0.5, 102)
    flat = [[1.0] * 200 for _ in range(4)]
    m_f, _ = build_mask(MASK_SELECTED, dict(cfg, agents=4, steps=200), 0.5, 101, order=flat)
    out.append(case("selection_differs_from_the_blind_draw",
                    m1 != m2 and sum(1 for a in range(4) for j in range(200)
                                     if m_f[a][j] == m1[a][j]) < 4 * 200,
                    "two blind masks at the same h differ; with a FLAT value matrix the selector picks the"
                    " lowest indices (a different set from the blind one)"))

    # 8. the coordinate-only mechanism, THREE-SIDED: the same run under two rho values is read as
    #    coordinate-only; a genuinely different run is informative; and the verdict is taken over the
    #    informative pairs only.  The "same run" is faked here by the latency triple, which is exactly what
    #    the reader uses.
    def rws(triple, seeds=4):
        return [{"seed": 100 + i, "latency_serial": triple[0], "latency_blind": triple[1],
                 "latency_selected": triple[2]} for i in range(seeds)]
    raw = {"h0.50/c2": rws((3.0, 2.8, 2.6)),          # contended: different numbers
           "h0.50/c4": rws((3.0, 2.9, 2.7)),
           "h0.50/c8": rws((3.0, 2.9, 2.7))}          # the SAME run as c4
    # the higher-rho cell has the LARGER F here (0.9 vs 0.5), so its pair is an INCREASE -- and F rises in
    # rho, so the pair is read in the direction rho ascends, which is the direction the reader walks.
    cells_fake = [cell(0.5, 2, fake_rows([(0.02, 0.20)] * 4, rhos=[0.6] * 4)),
                  cell(0.5, 4, fake_rows([(0.20, 0.40)] * 4, rhos=[0.3] * 4)),
                  cell(0.5, 8, fake_rows([(0.20, 0.40)] * 4, rhos=[0.15] * 4))]
    co = coordinate_only_pairs(cells_fake, raw)
    v_unres = p3_verdicts([cells_fake[1], cells_fake[2]], co)      # only a coordinate-only pair
    v_inc = p3_verdicts([cells_fake[0], cells_fake[1]], co)        # informative, and F rises with rho
    v5_bad = check_pool_beyond_the_agents_is_a_coordinate(
        cells_fake, {"h0.50/c2": rws((3.0, 2.8, 2.6)), "h0.50/c4": rws((3.1, 2.9, 2.7)),
                     "h0.50/c8": rws((3.2, 2.85, 2.65))}, 4)
    out.append(case("the_coordinate_only_pair_is_measured_and_excluded",
                    len(co) == 1 and ("h0.50/c8", "h0.50/c4") in co      # keyed in the rho order it walked
                    and v_unres["P3b"].startswith("UNRESOLVED") and v_unres["n_coordinate_only"] == 1
                    and v_inc["P3b"].startswith("CONTRADICTED") and v_inc["n_informative"] == 1
                    and v5_bad["status"] == "READ" and v5_bad["ok"] is False,
                    "the identical-triple pair is coordinate-only (so an all-tie ladder cannot read as"
                    " UNRESOLVED-with-information); a differing triple makes V5 FAIL (three different runs"
                    " above the pool is not a coordinate)"))

    bad = [n for n, ok, _ in out if not ok]
    for n, ok, d in out:
        print("  %-46s %s  %s" % (n, "ok" if ok else "FAIL", d))
    print("  selftest: %d case(s), %d failed" % (len(out), len(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="issue #50 step 9 -- the matched-parallelism control")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed0", type=int, default=101)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    seeds = [args.seed0 + i for i in range(4 if args.quick else args.seeds)]
    h_grid = (0.5,) if args.quick else H_GRID
    c_grid = (8,) if args.quick else C_GRID
    cfg0 = I.default_cfg()
    print("building arms ...")
    cells, raw = [], {}
    for h in h_grid:
        for c in c_grid:
            rows = arm_gains(cfg0, c, h, seeds)
            s = cell_summary(rows)
            s["h"], s["pool"] = h, c
            s["key"] = "h%.2f/c%d" % (h, c)
            s["_per_seed_F"] = {r["seed"]: r["F"] for r in rows}
            cells.append(s)
            raw[s["key"]] = rows
    coord_only = coordinate_only_pairs(cells, raw)
    verdicts = p3_verdicts(cells, coord_only)
    v1 = check_per_step_identity(cfg0, cfg0["agents"], seeds[0])
    v2 = check_reproduces_v0(cfg0, 8, 0.5, seeds[:3])
    v3 = check_capacity_matched([r for rows in raw.values() for r in rows])
    v4 = check_selector_is_the_top_k(cfg0, 8, 0.5, seeds[:3])
    v5 = check_pool_beyond_the_agents_is_a_coordinate(cells, raw, cfg0["agents"])
    checks = run_checks(v1, v2, v3, v4, cells)
    if v5["status"] == "READ":
        checks["a_pool_beyond_the_agent_count_is_a_coordinate"] = v5["ok"]
    report(cells, verdicts, checks, v1, v2, v3, v4, cfg0, seeds, v5)
    payload = {
        "what": "issue #50 instrument v0 step 9 -- the matched-parallelism control (registered P3), built by"
                " separating the WIDTH of early issue from the CHOICE of which steps",
        "seeds": seeds, "h_grid": list(h_grid), "c_grid": list(c_grid),
        "model": {k: cfg0[k] for k in sorted(cfg0) if not isinstance(cfg0[k], list)},
        "declared": {
            "width": "h = the fraction of steps issued early; identical in both arms by construction",
            "control": "the blind arm flags k = round(h*steps) steps per agent uniformly at random",
            "treatment": "the selected arm flags the top k by min(T,S), a selector with exact information",
            "F": "(G_selected - G_blind) / G_selected, per seed, aggregated over seeds",
            "no_misprediction_cost": "q = 0 throughout: this variant has no charge channel, so F measures"
                                     " what INFORMATION buys at a fixed width, not what a costly predictor is"
                                     " worth (that is step 7's question)",
            "tolerance": AGREE_TOL, "bitwise_tol": BITWISE_TOL,
        },
        "cells": cells, "verdicts": verdicts, "checks": checks,
        "V1_per_step_identity": v1, "V2_reproduces_v0": v2, "V3_capacity": v3, "V4_selector": v4,
        "V5_pool_coordinate": v5, "coordinate_only_pairs": sorted([list(p_) for p_ in coord_only]),
        "per_seed": raw,
    }
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

