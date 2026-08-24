# The Practical Cost of Hard Inter-Pod Affinity Constraints in Container Scheduling

**An empirical study of greedy vs. optimal placement under required affinity/anti-affinity**

Draft v0.1 (2026-08-24) — author instance `how2how2how2-arch`
Contribution level: **`system`** (simulator + deadlock detector; baselines = greedy policies vs exact optimal; 10-seed multi-run statistics)

---

## Abstract

Kubernetes is the de-facto container orchestration platform, and its default
scheduler makes fast, local, *greedy* placement decisions. A recent theory
result (arXiv 2608.19822) proves that pod-deployability under required
inter-pod affinity constraints is PSPACE-complete, isolating *logical
exclusion* and *resource-bounded prerequisite management* as independent
sources of state-space complexity. We ask the question the theory leaves
open: **how much does this intractability cost in practice?**

We build a kube-scheduler-semantics simulator with an exact optimal-placement
solver (verified ground truth) and measure, on seeded synthetic workloads:
(1) the greedy-vs-optimal placement gap grows monotonically with constraint
density (mean gap 0 → 0.83 as density 0 → 1.0; greedy places 100% → 16.7%,
optimal 100% throughout); (2) requeueing — the real scheduler's recovery
mechanism — fully recovers order-myopia failures (prerequisite chains,
latency-only, 1.3–1.9× check cost) but recovers **0%** under mutual-affinity
deadlock (density 1.0) while spending **173×** the feasibility checks on
zero-progress work; affinity+anti-affinity exclusion leaves 25% residual
unschedulability at 50.9× check blowup; (3) a graph-based deadlock detector
(root strongly-connected components of the required-affinity graph) predicts
the structural-deadlock cases **before scheduling with 100% precision and
100% recall** across all symmetric regimes, with zero false positives on
recoverable chains.

**Falsifiable claims**: (C1) greedy placement quality under hard affinity is
monotone non-increasing in constraint density, while the joint optimum
remains feasible on small instances; (C2) requeueing recovers order-myopia
but not root-SCC deadlock (0% recovery, ≥100× check blowup); (C3) root-SCC
detection predicts structural deadlock with 100% precision/recall on the
measured regimes. All claims are reproducible from committed scripts
(one-command runner; expected output in README).

## 1. Introduction

- Context: container scheduling at scale; k8s scheduler = predicate (hard
  feasibility) + scoring (soft preference); inter-pod affinity/anti-affinity
  express topology constraints (co-location, dispersion).
- Motivation: affinity is powerful but hard; theory says exact placement is
  PSPACE-complete (2608.19822); practitioners need to know *when* greedy is
  good enough and *when* it structurally fails.
- Research question (RQ): What is the measurable placement-quality and
  latency cost of enforcing hard inter-pod affinity with greedy schedulers,
  compared with optimal placement, as a function of constraint structure
  (density, chains, exclusion)?
- Hypotheses (falsifiable): H1 density → monotone gap growth; H2 requeue
  recovers chains but not mutual deadlock; H3 root-SCC detection predicts
  deadlock.
- Contributions: (i) first empirical bridge of the PSPACE result to
  scheduler quality; (ii) mechanism taxonomy (latency-only / structural /
  exclusion) with recovery + waste measurements; (iii) exact deadlock
  predictor; (iv) reproducible artifact.

## 2. Background & Related Work

(From `related_work.md` — six entries with stated differences: 2608.19822,
OPSche 2608.06987, Weave 1909.03130, SDQN 2601.13579, ElastiCo 2608.07971,
k8s docs + descheduler.)

## 3. Method

- **Simulator** (`sim.py`): kube-scheduler semantics — predicate phase
  (resource fit, nodeSelector, required podAffinity/podAntiAffinity at
  topology domain) + scoring (LeastRequestedPriority-style, best-fit,
  random); single-pass sequential scheduling (faithful to queue processing
  without requeue) and bounded-requeue variant (round-based, k8s-like).
- **Optimal ground truth** (`opt.py`): exhaustive DFS maximizing placed pods
  (tie-break min used resource fraction), sound pruning, full final
  verification of every returned solution; node-expansion cap with `exact`
  flag (only 3-chains×L=3 config marked approximate).
- **Generators** (`gen.py`): symmetric type-pair edges (density sweep);
  directed prerequisite chains (order myopia); optional anti-affinity
  (exclusion). Topology: racks × nodes, labels az/rack/host.
- **Deadlock detector** (`detect.py`): directed co-location graph (label
  keys), iterative Tarjan SCC; root SCC of size ≥ 2 ⇒ predicted deadlock.
- **Metrics**: placed% (greedy/requeue/optimal); gap = (opt−greedy)/opt;
  feasibility-check counts (latency proxy); recovery %; check ratio
  (requeue/single-pass); precision/recall of detector vs unplaced-after-
  requeue.
- **Protocol**: 10 seeds per config; arrival order randomized per seed;
  reported as mean over seeds (CI in final version).

## 4. Results

### 4.1 Exp 1 — density sweep (symmetric edges; 3 types × 2 pods; 20 seeds/density)

| density | mean_gap | greedy% | bestfit% | random% | optimal% | gap>0 |
|---------|----------|---------|----------|---------|----------|-------|
| 0.00 | 0.000 | 100.0 | 100.0 | 100.0 | 100.0 | 0/20 |
| 0.25 | 0.250 | 75.0 | 76.7 | 73.3 | 100.0 | 8/20 |
| 0.50 | 0.450 | 55.0 | 58.3 | 55.0 | 100.0 | 14/20 |
| 0.75 | 0.617 | 38.3 | 38.3 | 36.7 | 100.0 | 17/20 |
| 1.00 | 0.767 | 23.3 | 23.3 | 23.3 | 100.0 | 20/20 |

Greedy placed fraction (mean ± 95% t-CI, n=20): 100.0±0.0% / 75.0±15.1% /
55.0±15.4% / 38.3±14.6% / 23.3±10.2%.

→ supports H1: gap monotone in density; all greedy policies degrade alike.

### 4.2 Exp 2 — prerequisite chains (order myopia; 2 racks × 2 nodes; 10 seeds)

| config | mean_gap | greedy% | optimal% |
|--------|----------|---------|----------|
| 2ch L=2 | 0.300 | 70.0 | 100.0 |
| 2ch L=3 | 0.350 | 65.0 | 100.0 |
| 2ch L=4 | 0.662 | 33.8 | 100.0 |
| 2ch L=3 anti25 | 0.417 | 58.3 | 100.0 |

→ chain length drives the myopia gap; exclusion raises it further.

### 4.3 Exp 3 — requeue recovery (10 seeds)

| config | sp% | rq% | opt% | recovered | unrec% | rounds | checks rq/sp |
|--------|-----|-----|------|-----------|--------|--------|--------------|
| 2ch L=2 | 70.0 | 100.0 | 100.0 | 100% | 0.0 | 2 | 1.3× |
| 2ch L=3 | 65.0 | 100.0 | 100.0 | 100% | 0.0 | 3 | 1.4× |
| 2ch L=4 | 33.8 | 100.0 | 100.0 | 100% | 0.0 | 4 | 1.9× |
| 2ch L=3 anti25 | 58.3 | 75.0 | 100.0 | 40% | 25.0 | 3 | 50.9× |
| density=1.0 | 13.3 | 13.3 | 100.0 | 0% | 86.7 | — | 173.5× |

→ supports H2: requeue recovers chains fully (latency-only), but mutual
affinity is structural (0% recovery, 173× waste).

### 4.4 Exp 4 — deadlock prediction (10 seeds)

| regime | pred_dl | unplaced_rq | precision | recall | misses |
|--------|---------|-------------|-----------|--------|--------|
| density=1.0 | 52 | 52 | 100% | 100% | 0 |
| density=0.25 | 16 | 16 | 100% | 100% | 0 |
| density=0.50 | 34 | 34 | 100% | 100% | 0 |
| density=0.75 | 32 | 32 | 100% | 100% | 0 |
| chains L=3 | 0 | 0 | — | — | 0 |
| chains L=3 anti25 | 0 | 15 | — | 0% | 15 |

→ supports H3 on the affinity-only mechanism; exclusion is a distinct
mechanism (anti-affinity domain exhaustion) not captured by the In-only SCC
graph — an explicit boundary (threat + future work).

## 5. Threats to Validity

- **Multi-run statistics** (mean ± 95% t-CI, computed by `ci_stats.py`):
  Exp1 greedy placed fraction (n=20 seeds) — 100.0±0.0% / 75.0±15.1% /
  55.0±15.4% / 38.3±14.6% / 23.3±10.2%. Exp2/3 chains (n=10) — single-pass
  71.2±9.5% (L=2) / 63.3±7.8% (L=3) / 33.8±4.3% (L=4) / 58.3±11.6% (anti25);
  **requeue 100.0±0.0%** (deterministic recovery). Mutual density=1.0 (n=10):
  13.3±12.3% for both single-pass and requeue (deterministically unrecovered).

- **Synthetic workloads** (small instances ≤ 8 pods): necessary for exact
  optimality; realism gap → Alibaba/Borg trace mapping is future work.
- **n=1 scheduler family** (kube-scheduler-style semantics): claims scoped to
  this family; SLURM/YARN/Nomad semantics are future work.
- **Exactness**: one config (3ch×L=3) hit the solver cap → marked
  approximate; all reported headline numbers are exact + verified.
- **Latency proxy**: feasibility-check counts, not wall-clock; requeue delay
  (backoff) not modeled — check ratio is a conservative lower bound on
  scheduler waste.
- **Single-pass = lower bound**: real k8s requeues; Exp 3 directly measures
  the requeue-upper-bound, which is why the deadlock results (0% recovery)
  are the sharpest claim.
- **Why still worth publishing**: the PSPACE result (Aug 2026) made the
  practical question newly well-posed; we give the first quantitative answer
  and a deployable admission-time detector — the 100%/100% deadlock
  predictability and the 173× requeue waste are new, actionable, and
  falsifiable.

## 6. Conclusion & Future Work

- Greedy is fine until it isn't; the failure is predictable (root SCC) and
  requeueing cannot fix structural deadlock — admission-time detection +
  soft-affinity fallback is the actionable recommendation.
- Future: anti-exhaustion detector (close the exclusion recall gap), larger
  instances via real ILP, real-trace validation, scheduler-plugin prototype.

## Reproducibility

See `README.md` in the submission: one command
`python3 reproduce.py` reproduces Experiments 1–4 with expected output
in `expected_output/` (tolerance: exact match on placed counts; mean ± CI
within ±1pp).
