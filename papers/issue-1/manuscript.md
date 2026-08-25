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
density (mean gap 0 → 0.767 as density 0 → 1.0; greedy places 100% → 23.3%,
optimal 100% throughout); (2) requeueing — the real scheduler's recovery
mechanism — fully recovers order-myopia failures (prerequisite chains,
latency-only, 1.3–1.8× check cost) but recovers **0%** under mutual-affinity
deadlock (density 1.0) while spending **173.5×** the feasibility checks on
zero-progress work; affinity+anti-affinity exclusion leaves 25% residual
unschedulability at 51.0× check blowup; (3) a graph-based deadlock detector
(root strongly-connected components of the required-affinity graph) predicts
the structural-deadlock cases **before scheduling with 100% precision and
94–100% recall** across the symmetric regimes, with zero false positives on
recoverable chains (the two recall misses at density 0.75 are exclusion-type
failures, not graph cycles — an explicit boundary).

**Falsifiable claims**: (C1) greedy placement quality under hard affinity is
monotone non-increasing in constraint density, while the joint optimum
remains feasible on small instances; (C2) requeueing recovers order-myopia
but not root-SCC deadlock (0% recovery, ≥100× check blowup); (C3) root-SCC
detection predicts structural deadlock with 100% precision and ≥94% recall on
the measured symmetric regimes. All claims are reproducible from committed
scripts (one-command runner; expected output in README).

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

Six concrete related works are compared with stated differences in
`related_work.md` (committed alongside this manuscript): arXiv 2608.19822
(the PSPACE-completeness anchor), OPSche (arXiv 2608.06987, cluster-wide
placement plugin), Weave (arXiv 1909.03130, declarative solver scheduling),
SDQN (arXiv 2601.13579, RL k8s scheduler), ElastiCo (arXiv 2608.07971, GPU
co-location), and the Kubernetes inter-pod affinity documentation +
descheduler (practice). In brief: none quantifies the greedy-vs-optimal
placement gap, the requeue recovery limits, or the predictability of
structural deadlock under hard inter-pod affinity — the theory result leaves
the practical question open, and the optimization/learning-based schedulers
optimize different objectives without an exact-optimality reference under
hard placement constraints.

## 3. Method

- **Simulator** (`sim.py`): kube-scheduler semantics — predicate phase
  (resource fit, nodeSelector, required podAffinity/podAntiAffinity at
  topology domain) + scoring (LeastRequestedPriority-style, best-fit,
  random); single-pass sequential scheduling (faithful to queue processing
  without requeue) and bounded-requeue variant (round-based, k8s-like).
- **Optimal ground truth** (`opt.py`): exhaustive DFS maximizing placed pods
  (tie-break min used resource fraction), sound pruning, full final
  verification of every returned solution; node-expansion cap with `exact`
  flag (none of the reported configurations hits the cap — all exact).
- **Generators** (`gen.py`): symmetric type-pair edges (density sweep);
  directed prerequisite chains (order myopia); optional anti-affinity
  (exclusion). Topology: racks × nodes, labels az/rack/host.
- **Deadlock detector** (`detect.py`): directed co-location graph (label
  keys), iterative Tarjan SCC; root SCC of size ≥ 2 ⇒ predicted deadlock.
- **Metrics**: placed% (greedy/requeue/optimal); gap = (opt−greedy)/opt;
  feasibility-check counts (latency proxy); recovery %; check ratio
  (requeue/single-pass); precision/recall of detector vs unplaced-after-
  requeue.
- **Protocol**: 10 seeds per config (20 for the density sweep); arrival order
  randomized per seed with a fixed rng pattern (mirrored by `ci_stats.py`);
  means reported in §4, mean ± 95% t-CI in §5.

## 4. Results

### 4.1 Exp 1 — density sweep (symmetric edges; 3 types × 2 pods; 20 seeds/density)

| density | mean_gap | greedy% | bestfit% | random% | optimal% | gap>0 |
|---------|----------|---------|----------|---------|----------|-------|
| 0.00 | 0.000 | 100.0 | 100.0 | 100.0 | 100.0 | 0/20 |
| 0.25 | 0.250 | 75.0 | 76.7 | 76.7 | 100.0 | 8/20 |
| 0.50 | 0.433 | 56.7 | 58.3 | 58.3 | 100.0 | 13/20 |
| 0.75 | 0.633 | 36.7 | 38.3 | 36.7 | 100.0 | 18/20 |
| 1.00 | 0.767 | 23.3 | 23.3 | 23.3 | 100.0 | 20/20 |

Greedy placed fraction (mean ± 95% t-CI, n=20, from `ci_stats.py`):
100.0±0.0% / 75.0±15.1% / 56.7±16.1% / 36.7±13.3% / 23.3±10.2%.

→ supports H1: gap monotone in density; all greedy policies degrade alike.

### 4.2 Exp 2 — prerequisite chains (order myopia; 2 racks × 2 nodes; 10 seeds)

| config | mean_gap | greedy% | optimal% |
|--------|----------|---------|----------|
| 2ch L=2 | 0.300 | 70.0 | 100.0 |
| 2ch L=3 | 0.400 | 60.0 | 100.0 |
| 2ch L=4 | 0.538 | 46.2 | 100.0 |
| 2ch L=3 anti25 | 0.467 | 53.3 | 100.0 |

→ chain length drives the myopia gap; exclusion raises it further.

### 4.3 Exp 3 — requeue recovery (10 seeds)

| config | sp% | rq% | opt% | recovered | unrec% | rounds | checks rq/sp |
|--------|-----|-----|------|-----------|--------|--------|--------------|
| 2ch L=2 | 70.0 | 100.0 | 100.0 | 100% | 0.0 | 2 | 1.3× |
| 2ch L=3 | 60.0 | 100.0 | 100.0 | 100% | 0.0 | 3 | 1.4× |
| 2ch L=4 | 46.2 | 100.0 | 100.0 | 100% | 0.0 | 4 | 1.8× |
| 2ch L=3 anti25 | 53.3 | 75.0 | 100.0 | 46% | 25.0 | 3 | 51.0× |
| density=1.0 (mutual) | 13.3 | 13.3 | 100.0 | 0% | 86.7 | 1 | 173.5× |

(recovered = (rq − sp)/(opt − sp); unrec% = unplaced-after-requeue / total
pods, both derived from the canonical run.)

→ supports H2: requeue recovers chains fully (latency-only), but mutual
affinity is structural (0% recovery, 173.5× waste).

### 4.4 Exp 4 — deadlock prediction (10 seeds)

| regime | pred_dl | unplaced_rq | precision | recall | misses |
|--------|---------|-------------|-----------|--------|--------|
| density=1.0 | 52 | 52 | 100% | 100% | 0 |
| density=0.75 | 32 | 34 | 100% | 94% | 2 |
| density=0.50 | 34 | 34 | 100% | 100% | 0 |
| density=0.25 | 16 | 16 | 100% | 100% | 0 |
| chains L=3 | 0 | 0 | — | — | 0 |
| chains L=3 anti25 | 0 | 15 | — | 0% | 15 |

→ supports H3 on the affinity-only mechanism (100% precision; recall 94–100%);
the 2 misses at density 0.75 and the chains+anti25 misses are exclusion-type
failures (anti-affinity domain exhaustion), a distinct mechanism not captured
by the In-only SCC graph — an explicit boundary (threat + future work).

## 5. Threats to Validity

- **Multi-run statistics** (mean ± 95% t-CI, computed by `ci_stats.py` which
  mirrors `reproduce.py`'s exact rng pattern):
  Exp1 greedy placed fraction (n=20 seeds) — 100.0±0.0% / 75.0±15.1% /
  56.7±16.1% / 36.7±13.3% / 23.3±10.2%. Exp2 chains (n=10) — single-pass
  70.0±7.5% (L=2) / 60.0±16.1% (L=3) / 46.2±15.2% (L=4) / 53.3±15.7%
  (anti25); **requeue 100.0±0.0%** (deterministic recovery) for the chains,
  75.0±18.0% for anti25. Mutual density=1.0 (n=10): 13.3±12.3% for both
  single-pass and requeue (deterministically unrecovered).

- **Synthetic workloads** (small instances ≤ 8 pods): necessary for exact
  optimality; realism gap → Alibaba/Borg trace mapping is future work.
- **n=1 scheduler family** (kube-scheduler-style semantics): claims scoped to
  this family; SLURM/YARN/Nomad semantics are future work.
- **Exactness**: the optimal solver verifies every returned solution and
  reports `exact: false` when its node-expansion cap is hit; **none of the
  canonical runs in Exp 1–4 hit the cap** — all headline numbers are exact
  and verified.
- **Latency proxy**: feasibility-check counts, not wall-clock; requeue delay
  (backoff) not modeled — check ratio is a conservative lower bound on
  scheduler waste.
- **Single-pass = lower bound**: real k8s requeues; Exp 3 directly measures
  the requeue-upper-bound, which is why the deadlock results (0% recovery)
  are the sharpest claim.
- **Why still worth publishing**: the PSPACE result (Aug 2026) made the
  practical question newly well-posed; we give the first quantitative answer
  and a deployable admission-time detector — the 100% precision deadlock
  predictability and the 173.5× requeue waste are new, actionable, and
  falsifiable.

## 6. Conclusion & Future Work

- Greedy is fine until it isn't; the failure is predictable (root SCC) and
  requeueing cannot fix structural deadlock — admission-time detection +
  soft-affinity fallback is the actionable recommendation.
- Future: anti-exhaustion detector (close the exclusion recall gap), larger
  instances via real ILP, real-trace validation, scheduler-plugin prototype.

## Reproducibility

See `README.md` in the submission: one command
`python3 reproduce.py` reproduces Experiments 1–3 (density sweep → §4.1;
chains + requeue recovery → §4.2/§4.3; deadlock prediction → §4.4) with
expected output in `expected_output/manuscript_results.txt` (tolerance:
exact match on placed counts; mean ± CI within ±1pp). `ci_stats.py`
recomputes the §5 confidence intervals from the same rng pattern.
