# Related Work — Issue #1 (draft, for manuscript Introduction/Related Work)

Each entry: work → what it does → limitation → **our difference**.

## 1. Pod-Deployability complexity (anchor)
- **Giallorenzo, Mauro, Zavattaro. "Pod-Deployability in Kubernetes with Inter-Pod Affinity Constraints is PSPACE-Complete." arXiv 2608.19822 (2026-08-20).**
- What: proves pod-deployability is PSPACE-complete when required affinity (+ anti-affinity) is present; isolates two complexity sources — *logical exclusion* (affinity+anti-affinity interaction) and *resource-bounded prerequisite management* (affinity chains).
- Limitation: pure complexity theory — no statement of what the intractability means for real scheduler quality, requeueing, or admission control.
- **Our difference**: we translate the two complexity sources into measurable practice — greedy-vs-optimal placement gap (density monotonicity), requeue recovery limits (latency-only vs structural), and pre-scheduling deadlock predictability (root-SCC detection, 100% precision/recall on synthetic regimes).

## 2. Cluster-wide placement optimization for k8s
- **OPSche: "A Kubernetes Scheduler Plugin for Cluster-Wide Placement Optimisation." arXiv 2608.06987 (2026-08-07).**
- What: framework plugin letting external solvers drive cluster-wide placement; reports up to 3.0% resource-usage improvement and >1s latency reduction over default k8s scheduling.
- Limitation: (a) objective is resource usage/latency on their configurations, not an optimality gap vs exact optimum under hard placement constraints; (b) no analysis of affinity-driven unschedulability or deadlock; (c) the "up to 3.0%" is workload-specific, no mechanism taxonomy.
- **Our difference**: we provide exact-optimality ground truth (verified ILP-equivalent search on small instances) and a mechanism-level taxonomy of where greedy fails (order myopia / mutual deadlock / exclusion), including cases where requeueing cannot help at all (0% recovery, 173× wasted checks).

## 3. Declarative solver-driven cluster management
- **Weave (Krafzig et al.). "Automating Cluster Management with Weave." arXiv 1909.03130 (2019).**
- What: SQL-declared cluster-management policies encoded into solver models (incl. a k8s scheduler); improved placement quality and convergence times.
- Limitation: general optimization architecture (2019, pre-dates the PSPACE result); does not characterize the hard-inter-pod-affinity regime, greedy degradation, or structural deadlock; solver-encoded placement not compared against exact optimum under affinity constraints.
- **Our difference**: focus on the constraint regime that is provably hard (PSPACE-complete), with explicit measurements of greedy degradation and recovery limits rather than general architecture.

## 4. Learning-based k8s schedulers
- **SDQN / SDQN-n (RL custom k8s scheduler). arXiv 2601.13579 (2026-01).**
- What: Deep-Q-network schedulers reduce average CPU utilization by 10–20% for compute-intensive pods.
- Limitation: optimizes resource utilization on their workloads; no hard placement-constraint analysis, no optimality guarantee, no handling of affinity deadlock or exclusion.
- **Our difference**: constraint-first analysis with exact optimal reference; we show utilization-style objectives miss the structural failure modes of hard affinity (unplaceable pods, zero-progress requeueing).

## 5. (Domain context) GPU cluster co-location scheduling
- **ElastiCo. arXiv 2608.07971 (2026-08-08).**
- What: elastic interference-aware GPU co-location; JCT up to 2.94×, throughput 2.02×, utilization 25%→46%.
- Limitation: resource-sharing/interference axis, not hard inter-pod placement constraints; no greedy-vs-optimal placement analysis.
- **Our difference**: orthogonal axis — placement feasibility/quality under hard constraints, not resource sharing.

## 6. Primary sources (practice)
- **Kubernetes documentation, "Inter-pod affinity and anti-affinity"** (concept page): documents that anti-affinity rules can become unschedulable at scale; the known pod-affinity deadlock class (mutual required affinity) is a recognized operator problem.
- **descheduler** (Kubernetes SIG): best-effort rebalancing of already-placed pods.
- Limitation: best practice guidance and heuristics, no quantitative characterization of when hard affinity is unsafe.
- **Our difference**: we give the quantitative boundary — root-SCC detection predicts the deadlock class exactly, and the 173× requeue waste quantifies why best-effort retry is insufficient.

---

### Contribution-level declaration (target for this manuscript)
**`system`** — a working simulator + deadlock-detector system, evaluated with
baseline comparison (greedy policies vs exact optimal ground truth) and
multi-run statistics (10 seeds per configuration, CI reported). Claims are
scoped to the measured scheduler families (kube-scheduler-style single-pass
and bounded-requeue) and synthetic workload classes (chains, mutual affinity,
exclusion); no universal claims beyond the falsifiable mechanism taxonomy.
