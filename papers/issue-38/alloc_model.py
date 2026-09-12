#!/usr/bin/env python3
"""
Issue #38 - the allocation model (bounded-attention planner vs bidding market).

This module is part of the submission package: it is the whole model, and
``canonical_runner.py`` drives it to produce every number the manuscript reports.
The development history (including the tie-break defect this module carries a fix
for) is recorded in the research notes, not here.


Question (registered): where is the boundary, in (N, sigma, beta), between a
bounded-attention central planner and a bid-based market?

Conventions
-----------
* Costs are written task-major: ``C[j, i]`` is the TRUE cost of assigning agent ``i``
  to task ``j`` (N tasks, N agents).  All assignment solves are
  ``scipy.optimize.linear_sum_assignment`` on a square matrix; the returned
  ``assign[j] = i`` is the agent chosen for task ``j``.
* Total cost of an assignment is always evaluated on the TRUE matrix, so a
  decision rule's regret is a real loss, not a proxy.

Instance
--------
``C = 1 + gamma * u + beta * 1[block(task) != block(agent)]``, ``u ~ U(0,1)`` per pair.
* ``gamma``  - within-block heterogeneity (skill / requirement spread).
* ``beta``   - specialization-mismatch premium (how much matching matters).
Blocks are balanced: agent ``i`` and task ``j`` share a block iff ``i % K == j % K``.

Decision rules
--------------
* ``oracle`` / ``full-information planner`` - solve on ``C`` itself.  This is the
  lower bracket (nothing can beat it) and the target both reductions must hit.
* ``bounded-attention planner`` - observes the true cost of only ``m`` agents per task
  (an *attention budget*, fixed in m, NOT a fraction of N); every unattended agent is
  indistinguishable to it and is priced at its prior, the global mean cost ``cbar``.
  ``m = N``  =>  it observes everything  =>  the solve is on ``C`` exactly (reduction A).
  No arbitrary fallback constant is needed and every instance stays feasible.
* ``market`` - every agent bids for every task, ``B = C + sigma * z``, ``z ~ N(0,1)``
  (misestimation of one's own cost, absolute in cost units).  The market clears by
  solving the assignment on the bids; ``sigma = 0`` => bids are true costs (reduction B).
  The market has no attention limit: the whole pool bids.
* ``greedy`` - centralised but noisy allocation rule: fixed task order, each task takes
  its cheapest still-free agent.  Upper bracket alongside ``random``.

Changelog
---------
v0.0  first cut; reductions exact; anchors exposed two defects (below).
v0.1  (a) DEFECT FIXED - filler tie-break bias.  With every unattended cell set to the
      same prior ``cbar``, ``linear_sum_assignment`` breaks ties by lowest index, and
      because blocks are ``index % K`` that bias silently favours the specialised
      diagonal.  It made the no-attention planner (m = 0) look BETTER than m = 1 (12.75
      vs 29.96 at N=64) - an artefact, not a property.  Filler cells now carry a
      ``JIT``-scale jitter drawn from the instance stream, so ties are broken
      arbitrarily instead of index-first.  m = N still overwrites every cell, so
      reduction A stays exact.
      (b) ATTENTION MODE ADDED.  The registration is internally ambiguous on what
      "attention" is: the construct line says "attention = fraction of pool observable"
      while P1's justification assumes a budget ("a falling fraction of the pool can be
      conditioned on" as N grows).  Both readings are implemented:
        ``mode='budget'``   m is a fixed number of agents per task (context-window reading)
        ``mode='fraction'`` m = round(alpha * N) (constant fraction reading)
      They predict OPPOSITE signs for sigma*(N), so the instrument must report both.

The two structural reductions the registration demands be run BEFORE any reported
number:   A: attention unbounded (m = N)  ==  full-information optimum.
           B: sigma = 0 market            ==  the same optimum.
"""

from __future__ import annotations

import json
import numpy as np
from scipy.optimize import linear_sum_assignment


# --------------------------------------------------------------------------- #
# instance
# --------------------------------------------------------------------------- #
def make_instance(N, K, beta, gamma, seed):
    """Return (C, task_block, agent_block).  C[j, i] = true cost, task-major."""
    if N % K != 0:
        raise ValueError("N must be divisible by K")
    rng = np.random.default_rng(seed)
    tb = np.arange(N) % K
    ab = np.arange(N) % K
    u = rng.random((N, N))
    mismatch = (tb[:, None] != ab[None, :]).astype(float)
    C = 1.0 + gamma * u + beta * mismatch
    return C, tb, ab


# --------------------------------------------------------------------------- #
# solvers / brackets
# --------------------------------------------------------------------------- #
def solve(M):
    """Min-cost assignment on M (task-major) -> assign[j] = agent index."""
    row, col = linear_sum_assignment(M)
    assign = np.empty(M.shape[0], dtype=int)
    assign[row] = col
    return assign


def true_cost(C, assign):
    return float(C[np.arange(len(assign)), assign].sum())


def oracle_assign(C):
    return solve(C)


JIT = 1e-6   # filler tie-break jitter; negligible against a cost scale of ~1


def attention_budget(N, mode, param):
    """Translate an attention specification into agents-per-task m."""
    if mode == "budget":
        return int(min(param, N))
    if mode == "fraction":
        return int(min(max(1, round(param * N)), N))
    raise ValueError("mode must be 'budget' or 'fraction'")


def planner_estimate(C, m, rng, nested=False):
    """What the bounded-attention planner believes the cost matrix is.

    m == N  -> the estimate IS C (reduction A, exact).
    nested  -> the attended set of size m is a prefix of one random permutation per
               task, so attention sets are nested in m (used only for a clean
               monotonicity probe; the default draws a fresh subset per m).
    Filler cells are cbar + JIT*jitter: equal to the prior up to a tie-break, so the
    solver cannot exploit the index/block alignment (see v0.1 defect (a)).
    """
    N = C.shape[0]
    cbar = float(C.mean())                       # the planner's prior over the pool
    E = cbar + JIT * rng.random((N, N))
    if m > 0:
        for j in range(N):
            if nested:
                perm = rng.permutation(N)
                idx = perm[:min(m, N)]
            else:
                idx = rng.choice(N, size=min(m, N), replace=False)
            E[j, idx] = C[j, idx]
    return E, cbar


def planner_assign(C, m, rng, nested=False):
    E, _ = planner_estimate(C, m, rng, nested=nested)
    return solve(E)


def market_bids(C, sigma, rng):
    if sigma == 0.0:
        return C.copy()                          # reduction B (exact, no RNG draw)
    return C + sigma * rng.standard_normal(C.shape)


def market_assign(C, sigma, rng):
    return solve(market_bids(C, sigma, rng))


def greedy_assign(C):
    N = C.shape[0]
    free = np.ones(N, dtype=bool)
    assign = np.empty(N, dtype=int)
    for j in range(N):
        cand = np.where(free)[0]
        i = int(cand[np.argmin(C[j, cand])])
        assign[j] = i
        free[i] = False
    return assign


def random_assign(N, rng):
    return rng.permutation(N)


# --------------------------------------------------------------------------- #
# regret of each rule, in one call
# --------------------------------------------------------------------------- #
def regrets(C, m, sigma, seed, nested=False):
    """Regret (true excess cost over the oracle) of every rule on one instance."""
    rng = np.random.default_rng(seed)
    m = int(min(m, C.shape[0]))
    a_opt = oracle_assign(C)
    opt = true_cost(C, a_opt)
    out = {
        "opt": opt,
        "planner": true_cost(C, planner_assign(C, m, rng, nested=nested)) - opt,
        "market": true_cost(C, market_assign(C, sigma, rng)) - opt,
        "greedy": true_cost(C, greedy_assign(C)) - opt,
        "random": true_cost(C, random_assign(C.shape[0], rng)) - opt,
    }
    out["m"] = int(m)
    out["sigma"] = float(sigma)
    out["N"] = int(C.shape[0])
    out["attended_fraction"] = min(m, C.shape[0]) / C.shape[0]
    return out


def mean_regrets(N, K, beta, gamma, m, sigma, seeds=20, nested=False):
    acc = {}
    for s in range(seeds):
        C, _, _ = make_instance(N, K, beta, gamma, seed=1000 * s + N)
        r = regrets(C, m, sigma, seed=7 * s + 3, nested=nested)
        for k, v in r.items():
            acc.setdefault(k, []).append(v)
    out = {k: float(np.mean(v)) for k, v in acc.items()}
    out.update({"N": N, "K": K, "beta": beta, "gamma": gamma,
                "m": m, "sigma": sigma, "seeds": seeds})
    return out


# --------------------------------------------------------------------------- #
# the two structural reductions (must be exact)
# --------------------------------------------------------------------------- #
def reductions(Ns=(8, 12, 16, 24, 32, 64), K=4, betas=(0.0, 0.5, 2.0),
               gammas=(0.0, 0.25, 1.0), seeds=5):
    rows = []
    for N in Ns:
        for beta in betas:
            for gamma in gammas:
                for s in range(seeds):
                    C, _, _ = make_instance(N, K, beta, gamma, seed=1000 * s + N)
                    opt = true_cost(C, oracle_assign(C))
                    a = true_cost(C, planner_assign(C, N, np.random.default_rng(s)))
                    b = true_cost(C, market_assign(C, 0.0, np.random.default_rng(s)))
                    rows.append({
                        "N": N, "K": K, "beta": beta, "gamma": gamma, "seed": s,
                        "opt": opt, "attention_unbounded": a, "zero_noise_market": b,
                        "A_exact": abs(a - opt) < 1e-9,
                        "B_exact": abs(b - opt) < 1e-9,
                    })
    return rows


if __name__ == "__main__":
    rows = reductions()
    bad = [r for r in rows if not (r["A_exact"] and r["B_exact"])]
    print(json.dumps({
        "cells": len(rows),
        "A_exact_all": all(r["A_exact"] for r in rows),
        "B_exact_all": all(r["B_exact"] for r in rows),
        "failures": len(bad),
    }, indent=2))
