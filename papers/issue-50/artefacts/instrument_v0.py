#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 1: the classical anchors, BEFORE any boundary is measured.

WHAT THIS FILE IS.  A deterministic, standard-library-only discrete-event model of a shared tool
server pool serving agent loops, plus the closed forms the model must reproduce before it is used to
claim anything.  The registered priors (P1-P4) are about a *contention-indexed boundary*; a boundary
measured on an instrument that does not reproduce its own classical limits is a number about the
instrument.  So this step measures only what has a closed form:

  A1  M/M/1                    the queueing layer alone: mean sojourn time vs 1/(mu - lambda)
  A2  no-speculation limit     h = 0 must be the serial schedule, exactly (same event trace)
  A3  zero-contention hiding   no contention, h = 1: benefit = E[min(T, S)] = mT*mS/(mT+mS)
  A4  monotonicity in rho      benefit must not increase as contention grows

Each anchor is a claim about the instrument; `--selftest` plants one defect per anchor and requires
exactly that anchor to fail.  Every random quantity is drawn ONCE per (agent, step) before scheduling,
so that a policy change changes the SCHEDULE and never the draws -- that is what makes A2 an identity
rather than a statistical comparison.

The model (v0)
--------------
`n_agents` agent loops share a pool of `c` identical workers.  Step k of an agent: a think phase
(mean mT), then one tool call (mean mS, exponential or Pareto, mean-matched).  With speculation
enabled and a correct prediction (probability h) the call is ISSUED at the start of the think phase,
so its service overlaps the thinking; a wrong prediction is also issued then, consumes a worker, and is
discarded, after which the real call is issued at the end of the think phase -- and with probability q
the discard pays a compensating cost `comp` of worker time (the non-idempotent channel).  Latency is
per step, from the start of its think phase to the completion of that step's real call.

Contention is rho = (total worker-busy time) / (c * makespan), a measured quantity, not a setting; the
setting this file varies is the pool size c and the agent count.

CPU only, stdlib only, fixed seeds.  Nothing here is a result about the world.
"""
import argparse
import heapq
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MU = 1.0  # service rate of one worker (calls per unit time) => mean service 1.0


# --------------------------------------------------------------------------- service distributions
def draw_service(rng, mean, tail):
    """One tool-call service time with the requested mean.

    tail='light': exponential (cv = 1).  tail='heavy': Pareto with tail index 2.5, scaled to the same
    mean -- matched to the light class by construction, which is what P2's comparison needs.  The
    index is > 2 so the variance exists: a heavier index would make the measured mean a statement
    about the tail realisation rather than about the workload.
    """
    if tail == "light":
        return rng.expovariate(1.0 / mean)
    if tail == "heavy":
        alpha = 2.5
        xm = mean * (alpha - 1.0) / alpha
        return xm * (1.0 - rng.random()) ** (-1.0 / alpha)
    raise ValueError(tail)


# --------------------------------------------------------------------------- the queueing layer
def mm1(rho, n, seed, warmup=None, servers=1):
    """The queueing layer alone: Poisson arrivals at lambda = rho*mu per worker, exponential service.

    With servers=1 this is M/M/1 and the closed form is 1/(mu - lambda).  A batch-means interval is
    reported with it because the samples are autocorrelated -- an i.i.d. interval would be narrower
    than the truth and every later claim here is comparative.
    """
    lam = rho * MU * servers
    rng = random.Random(seed)
    warmup = warmup if warmup is not None else max(200, n // 10)
    free = [0.0] * servers
    heapq.heapify(free)
    t = 0.0
    sojourn = []
    for i in range(n):
        t += rng.expovariate(lam)
        f = heapq.heappop(free)
        start = max(f, t)
        finish = start + rng.expovariate(MU)
        heapq.heappush(free, finish)
        if i >= warmup:
            sojourn.append(finish - t)
    return {"mean": statistics.fmean(sojourn), "n": len(sojourn), "ci": batch_ci(sojourn),
            "warmup": warmup}


def batch_ci(xs, batches=20):
    if len(xs) < batches * 2:
        return None
    size = len(xs) // batches
    means = [statistics.fmean(xs[i * size:(i + 1) * size]) for i in range(batches)]
    se = statistics.stdev(means) / math.sqrt(batches)
    return [statistics.fmean(xs) - 1.96 * se, statistics.fmean(xs) + 1.96 * se]


# --------------------------------------------------------------------------- the agent loop
class Job(object):
    __slots__ = ("arrival", "service", "agent", "step", "kind")

    def __init__(self, arrival, service, agent, step, kind):
        self.arrival, self.service, self.agent, self.step, self.kind = (
            arrival, service, agent, step, kind)


def agent_run(n_agents, mT, mS, h, steps, seed, tail="light", q=0.0, comp=0.0,
              speculate=True, c=1, ignore_h=False):
    """One run of `n_agents` agent loops against a pool of `c` workers.  See the module docstring."""
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / mT) for _ in range(steps)] for _ in range(n_agents)]
    S = [[draw_service(rng, mS, tail) for _ in range(steps)] for _ in range(n_agents)]
    HIT = [[rng.random() < h for _ in range(steps)] for _ in range(n_agents)]
    IDEM = [[rng.random() < q for _ in range(steps)] for _ in range(n_agents)]
    if ignore_h:                       # the planted defect of anchor A2
        HIT = [[True] * steps for _ in range(n_agents)]

    events, seq = [], 0
    free = [0.0] * c
    heapq.heapify(free)
    busy = 0.0
    lat = [[] for _ in range(n_agents)]
    step_start = [0.0] * n_agents
    done = [0] * n_agents
    now = [0.0]
    wasted = [0.0]
    # A step ends when BOTH halves are done: the think phase has ended AND the real call has
    # completed.  Without this, a speculative hit landing inside the think phase lets the agent start
    # its next step then -- i.e. skip its own reasoning -- which is a different (and much better)
    # system than the one registered.  A3 caught exactly that on the first run: benefit 2.056 against
    # a hiding limit of 0.667 with measured utilisation pinned at 1.000.
    think_end_at = {}
    call_done_at = {}

    def push(t, kind, payload):
        nonlocal seq
        seq += 1
        heapq.heappush(events, (t, seq, kind, payload))

    def submit(job):
        """Hand a job to the earliest-free worker and schedule its completion."""
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
        if speculate and HIT[a][k]:
            submit(Job(now[0], S[a][k], a, k, "real"))
        push(now[0] + T[a][k], "think_end", (a, k))

    def on_think_end(payload):
        a, k = payload
        think_end_at[(a, k)] = now[0]
        need_real = not (speculate and HIT[a][k])
        if need_real:
            submit(Job(now[0], S[a][k], a, k, "real"))
            if speculate and q > 0.0 and IDEM[a][k]:
                wasted[0] += comp
                submit(Job(now[0], comp, a, k, "comp"))
        if not need_real:
            finish_if_both(a, k)

    def finish_if_both(a, k):
        """Complete step k at max(think end, call completion), then start the next step."""
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
            "ci": batch_ci(samples),
            "latencies": [x for a in range(n_agents) for x in lat[a]],
            "trace": [(a, k, round(lat[a][k], 12)) for a in range(n_agents)
                      for k in range(len(lat[a]))],
            "wasted": wasted[0]}


def benefit(cfg, n_agents, c, h, **kw):
    """Serial latency minus speculative latency, and the relative benefit, for one cell."""
    ser = agent_run(n_agents, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], cfg["seed"],
                    tail=cfg["tail"], q=cfg["q"], comp=cfg["comp"], speculate=False, c=c)
    spe = agent_run(n_agents, cfg["mT"], cfg["mS"], h, cfg["steps"], cfg["seed"],
                    tail=cfg["tail"], q=cfg["q"], comp=cfg["comp"], speculate=True, c=c, **kw)
    return {"rho": spe["rho"], "serial": ser["mean_latency"], "spec": spe["mean_latency"],
            "benefit": ser["mean_latency"] - spe["mean_latency"],
            "benefit_pct": 100.0 * (ser["mean_latency"] - spe["mean_latency"]) / ser["mean_latency"],
            "serial_n": ser["n_samples"], "spec_n": spe["n_samples"]}


# --------------------------------------------------------------------------- the anchors
def anchor_a1(cfg, closed_form=None):
    """A1 -- the queueing layer reproduces M/M/1's mean sojourn time 1/(mu - lambda).

    The criterion is the estimator's OWN resolution, not a fixed percentage, and the measurement that
    forced that: at rho = 0.9 the simulated mean deviates from the closed form by 7.9%, while the
    batch-means 95% interval is +/-16.4% of the mean wide (rho = 0.3: 1.1%; rho = 0.7: 4.1%; rho =
    0.95: 29.2%).  M/M/1 sojourn is exponential with cv = 1, so the deviation is sampling error whose
    size grows as rho -> 1 through the autocorrelation time (+/- 1/(1-rho)^2), and a point estimate
    cannot be required to resolve better than the interval it reports.  So: the closed form must lie
    INSIDE the interval, and the relative error must be within max(a1_tol, the interval's half-width
    as a fraction of the mean).  Both are reported, so the resolution is visible rather than implied.
    """
    rows, ok = [], True
    for rho in cfg["a1_levels"]:
        r = mm1(rho, cfg["a1_n"], cfg["seed"], servers=1)
        want = (closed_form or (lambda x: 1.0 / (MU - x * MU)))(rho)
        rel = abs(r["mean"] - want) / want
        inside = (r["ci"] is None) or (r["ci"][0] <= want <= r["ci"][1])
        hw = (r["ci"][1] - r["ci"][0]) / 2.0 if r["ci"] else 0.0
        resolution = hw / r["mean"] if r["mean"] else 0.0
        within = rel <= max(cfg["a1_tol"], resolution)
        rows.append({"rho": rho, "measured": r["mean"], "closed_form": want, "rel_error": rel,
                     "ci": r["ci"], "closed_form_in_ci": inside,
                     "resolution": resolution, "within_resolution": within})
        ok = ok and inside and within
    return ok, rows


def anchor_a2(cfg, ignore_h=False):
    """A2 -- with h = 0 the speculative run IS the serial run: identical per-step latencies."""
    serial = agent_run(cfg["agents"], cfg["mT"], cfg["mS"], 0.0, cfg["steps"], cfg["seed"],
                       tail=cfg["tail"], speculate=False, c=cfg["c"])
    nospec = agent_run(cfg["agents"], cfg["mT"], cfg["mS"], 0.0, cfg["steps"], cfg["seed"],
                       tail=cfg["tail"], speculate=True, c=cfg["c"], ignore_h=ignore_h)
    same = serial["trace"] == nospec["trace"]
    return same, {"serial_mean": serial["mean_latency"], "h0_mean": nospec["mean_latency"],
                  "identical_trace": same, "policy_switched": ignore_h,
                  "rule": "h = 0 must schedule nothing the serial run does not schedule"}


def anchor_a3(cfg, h=1.0, limit_factor=1.0):
    """A3 -- with no contention the benefit is exactly the hiding limit E[min(T, S)].

    One agent, one worker, and the worker never queues: serial latency is T + S; speculative latency is
    max(T, S) because the call is served while the agent thinks; so the per-step benefit is min(T, S)
    and for exponentials E[min] = mT*mS/(mT+mS).  The tolerance is sampling error over a finite number
    of steps, not a fit.
    """
    ser = agent_run(1, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], cfg["seed"], tail=cfg["tail"],
                    speculate=False, c=1)
    spe = agent_run(1, cfg["mT"], cfg["mS"], h, cfg["steps"], cfg["seed"], tail=cfg["tail"],
                    speculate=True, c=1)
    ben = ser["mean_latency"] - spe["mean_latency"]
    want = limit_factor * h * cfg["mT"] * cfg["mS"] / (cfg["mT"] + cfg["mS"])
    rel = abs(ben - want) / want
    return rel <= cfg["a3_tol"], {"benefit": ben, "hiding_limit": want, "rel_error": rel,
                                  "serial": ser["mean_latency"], "spec": spe["mean_latency"],
                                  "rho": spe["rho"], "n": spe["n_samples"]}


def anchor_a4(cfg, inject_increase=False):
    """A4 -- benefit must not increase as contention grows ... REFUTED as stated; the claim is narrowed.

    REFUTATION, recorded rather than smoothed: on the first non-degenerate sweep the benefit sequence
    over rho = 0.205 / 0.404 / 0.781 / 0.920 is 21.91% / 22.02% / 21.06% / 16.77% -- it RISES by 0.11
    percentage points and then falls.  The two runs share one seed and one draw stream, so the rise is
    a scheduling effect and not sampling noise: in the serial schedule a call is issued at the END of
    the think phase, while a correct speculation issues it at the START, so an early call can also
    reach a free worker sooner.  Speculation therefore buys SCHEDULE POSITION as well as hidden time,
    and the benefit curve is non-monotone before the boundary rather than monotone.

    What that changes: P1 is a claim about a CROSSING (benefit changes sign at rho*), not about
    monotonicity, so the registered prior does not need the stronger statement this anchor first made.
    The anchor now reads the one part the instrument supports and that P1 needs -- **the benefit must
    fall across the saturated half** (rho >= `saturated_rho`) -- and reports the low-contention rise as
    a measured fact beside it.  A4 as first written was my own over-claim, not the registration's.
    """
    rows = []
    for (c, A) in cfg["a4_cells"]:
        r = benefit(cfg, A, c, cfg["h"])
        rows.append({"c": c, "agents": A, "rho": r["rho"], "benefit_pct": r["benefit_pct"]})
    rows.sort(key=lambda r: r["rho"])
    vals = [r["benefit_pct"] for r in rows]
    if inject_increase:                      # a planted violation INSIDE the saturated half, so the
        vals[-1], vals[-2] = vals[-2], vals[-1]   # case targets the criterion the anchor now states
    sat = [v for r, v in zip(rows, vals) if r["rho"] >= cfg["saturated_rho"]]
    falling = all(sat[i] >= sat[i + 1] - cfg["a4_slack"] for i in range(len(sat) - 1)) and len(sat) >= 2
    rises = [i for i in range(len(vals) - 1) if vals[i + 1] > vals[i] + cfg["a4_slack"]]
    return falling, {"rows": rows, "saturated_half_falls": falling, "saturated_rho":
                     cfg["saturated_rho"], "n_saturated": len(sat),
                     "low_contention_rises_at": [rows[i]["rho"] for i in rises],
                     "refuted_as_first_stated": bool(rises)}


# --------------------------------------------------------------------------- driver + battery
def default_cfg():
    return {"a1_levels": [0.3, 0.5, 0.7, 0.9], "a1_n": 60000, "a1_tol": 0.05,
            "agents": 4, "mT": 2.0, "mS": 1.0, "steps": 400, "seed": 11, "tail": "light",
            "h": 1.0, "c": 4, "q": 0.0, "comp": 0.0, "a3_tol": 0.15, "a4_slack": 1e-9,
            "saturated_rho": 0.6,
            # Contention is varied by the agent-to-worker ratio A/c, not by the pool alone: a cell
            # with c >= A has a worker idle for every agent, so it cannot queue at all -- and the
            # first sweep showed exactly that, two cells reporting identical benefits to four
            # significant digits because neither ever waited.  Offered load = A*mS/(c*(mT+mS)).
            "a4_cells": [(8, 4), (8, 8), (8, 16), (8, 20)]}


def run_all(cfg, corrupt=None):
    rows = []
    rows.append(("A1/M-M-1-mean-sojourn",) +
                anchor_a1(cfg, closed_form=(lambda x: 0.5 / (MU - x * MU))
                          if corrupt == "closed_form" else None))
    rows.append(("A2/no-speculation-is-the-serial-schedule",) +
                anchor_a2(cfg, ignore_h=(corrupt == "ignore_h")))
    rows.append(("A3/zero-contention-hiding-limit",) +
                anchor_a3(cfg, limit_factor=1.5 if corrupt == "hiding_limit" else 1.0))
    rows.append(("A4/benefit-falls-across-the-saturated-half",) +
                anchor_a4(cfg, inject_increase=(corrupt == "increase")))
    return rows


def summarise(name, detail):
    if name.startswith("A1"):
        return " | ".join("rho=%.1f meas %.4f vs %.4f (rel %.3f, CI %s, res %.3f)" %
                          (r["rho"], r["measured"], r["closed_form"], r["rel_error"],
                           "ok" if r["closed_form_in_ci"] else "OUT",
                           r["resolution"]) for r in detail)
    if name.startswith("A2"):
        return "identical trace: %s (serial %.4f vs h=0 %.4f)" % (
            detail["identical_trace"], detail["serial_mean"], detail["h0_mean"])
    if name.startswith("A3"):
        return "benefit %.4f vs hiding limit %.4f (rel %.4f), rho %.3f over %d step(s)" % (
            detail["benefit"], detail["hiding_limit"], detail["rel_error"], detail["rho"],
            detail["n"])
    if name.startswith("A4"):
        if isinstance(detail, dict):
            return " / ".join("c=%d A=%d rho=%.3f B=%+.2f%%" % (r["c"], r["agents"], r["rho"],
                                                                r["benefit_pct"])
                              for r in detail["rows"]) + (
                " || saturated half falls: %s; rises at rho=%s (refutes the non-increasing form)"
                % (detail["saturated_half_falls"],
                   ["%.3f" % x for x in detail["low_contention_rises_at"]]))
        return " / ".join("..." for _ in detail)
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    cfg = default_cfg()
    if args.selftest:
        return selftest(cfg)
    rows = run_all(cfg)
    bad = 0
    payload = {}
    for name, ok, detail in rows:
        bad += 0 if ok else 1
        payload[name] = {"ok": bool(ok), "detail": detail}
        print("%-6s %-46s %s" % ("PASS" if ok else "FAIL", name, summarise(name, detail)))
    print("anchors: %d, failed: %d" % (len(rows), bad))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"config": cfg, "anchors": payload}, fh, indent=1, sort_keys=True)
    return 1 if bad else 0


def selftest(cfg):
    """One planted defect per anchor; each must fail its own anchor and no other."""
    base = [n for n, ok, _ in run_all(cfg) if not ok]
    if base:
        print("FAIL   the battery needs a clean base; already failing: %s" % base)
        return 1
    rows = run_all(cfg)
    print("%-6s %-46s %s" % ("PASS", "control/unmodified", summarise(rows[0][0], rows[0][2])[:60]))
    cases = [("A1/M-M-1-mean-sojourn", "closed_form"),
             ("A2/no-speculation-is-the-serial-schedule", "ignore_h"),
             ("A3/zero-contention-hiding-limit", "hiding_limit"),
             ("A4/benefit-falls-across-the-saturated-half", "increase")]
    bad = 0
    for name, corrupt in cases:
        failed = [n for n, ok, _ in run_all(cfg, corrupt=corrupt) if not ok]
        good = failed == [name]
        print("%-6s %-46s failed=%s expected=[%r]" % ("PASS" if good else "FAIL", name, failed, name))
        bad += 0 if good else 1
    print("selftest: %d case(s) + 1 control, %d failure(s) over 4 anchor(s)" % (len(cases), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
