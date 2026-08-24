# Issue #1 — The Practical Cost of Hard Inter-Pod Affinity Constraints in Container Scheduling

**Manuscript**: `manuscript.md`
**Contribution level**: `system` (simulator + deadlock detector; baselines =
greedy policies vs exact optimal; 10–20 seed multi-run statistics with CIs)

## Reproduction (one command)

```bash
python3 reproduce.py
```

Requires Python ≥ 3.10 (stdlib only — no third-party packages). Runs
Experiments 1–3 (density sweep, chains + requeue recovery, deadlock
prediction) with the manuscript's fixed seeds and prints the headline tables.

**Expected output**: matches `expected_output/manuscript_results.txt`
(committed).
**Tolerance**: exact match on placed-pod counts for a given seed; mean ± CI
values within ±1 percentage point (deterministic — seeds are fixed, so a
successful run should match exactly).

Runtime: ~3 seconds.

## Files

- `manuscript.md` — the paper (abstract, method, results, threats, conclusion)
- `sim.py` — kube-scheduler-semantics simulator (predicate + scoring,
  single-pass and bounded-requeue variants)
- `opt.py` — exact optimal-placement solver (exhaustive DFS, final
  verification, `exact` flag)
- `gen.py` — seeded workload generators (symmetric density sweep, directed
  prerequisite chains, anti-affinity)
- `detect.py` — deadlock predictor (Tarjan SCC on the required-affinity graph)
- `reproduce.py` — one-command reproduction of all experiments
- `expected_output/manuscript_results.txt` — canonical output
- `figures/` — (to be populated with generated figures)

## Experiment protocol

- Fixed seeds: density sweep uses seeds 0–19; chains/requeue/deadlock use
  seeds 0–9; arrival order randomized per seed.
- Ground truth: exact optimal placement (verified) on all headline results;
  the only approximate config (3-chains × L=3, solver node cap) is marked
  `exact: false` in the scripts and is not a headline number.
- Metrics: placed% (greedy/requeue/optimal), gap = (opt−greedy)/opt,
  feasibility-check counts (latency proxy), recovery %, check ratio,
  deadlock-prediction precision/recall vs unplaced-after-requeue.

## Data availability

All data are generated synthetically by the committed scripts with fixed
seeds; no external datasets required. Public-trace validation (Alibaba 2022)
is listed as future work in the manuscript.
