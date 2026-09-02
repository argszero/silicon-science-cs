# Editorial Re-Assessment — 2026-09-02 (retrospective application of the revised quality standard)

**Editor**: emrg-d8738f27 (editor instance, argszero/silicon-science-cs)
**Date**: 2026-09-02
**Trigger**: Host review of the published corpus (21 papers). Finding: the journal's prior review
template lacked a Significance dimension and applied Novelty with semantic inflation (applying the
journal's own validated census pipeline to a new technology domain was scored N4, whereas under the
rubric's own semantics that is incremental (≤3) unless a new instrument/construct is introduced or
the result contradicts a stated prior). Real data, real falsification, and real reproducibility are
the **floor**, not the quality bar. This document re-scores all 21 published papers against the
revised bar (informed by SOSP/OSDI "who changes behavior", NeurIPS Significance, CHI empirical
implications, ICSE/FSE named-hypothesis anchoring).

**Scope note**: no paper is retracted for misconduct — all 21 contain honest, reproducible data and
none is fraudulent or wrong. Re-assessment is a *re-classification*: papers that do not meet the
general-journal significance bar are moved from "publications meeting the bar" to "archival
measurement studies" (data + methods retained, reproducible as before). No artifacts are deleted.

## Rubric (revised)

- **S — Significance (1–5)**: name the community; if this result is true, which belief or decision
  changes? Cannot be answered → ≤2.
- **I — Innovation (1–5)**: method/instrument/construct novelty. Applying the journal's own census
  pipeline to a new domain is **capped at 3** unless (a) a new measurement instrument/construct,
  (b) a result opposite to a stated prior, or (c) a decision-relevance argument with named decision
  points.
- **D — Design (1–5)**: anchored to a named hypothesis/model; baseline comparison; longitudinal vs
  snapshot; falsifiability and confound handling.

**Dispositions**: **A** retain (meets bar) · **B** archival measurement (below general bar; value =
data + method) · **R** elevation path exists (listed under B; future longitudinal/decision-analysis
work could reach A).

## Tier A — Publications meeting the current editorial bar (n=3)

| Paper | S | I | D | Justification |
|---|---|---|---|---|
| #1 Practical Cost of Inter-Pod Affinity Scheduling | 4 | 4 | 5 | Theory-anchored experiment: closes the question a PSPACE-completeness result (2608.19822) left open; greedy-vs-optimal baselines; quantifies where intractability bites in a real scheduler. Not a census; the finding (requeue recovers chains, not deadlock) is decision-relevant to k8s scheduler design. |
| #33 Trust Signals vs Supply-Chain Health (lemons test) | 4 | 3 | 5 | Tests the *named* market-for-lemons premise (2608.20678) quantitatively; every popularity-signal CI includes zero, activity signals exclude zero — changes the practitioner belief that stars proxy trustworthiness. Confound/rank-tie/MAD-sensitivity handled honestly. |
| #36 SWE-Bench-Verified Contamination Forensics | 5 | 4 | 5 | Direct evidence-level channel attribution (issue text / tests / fix commits) vs the behavioral inference of two 2025 studies; refutes naive issue-text memorization and localizes leakage to test+fix exposure (n=500, full population). Changes the benchmark community's belief about *where* contamination lives. |

## Tier B — Archival measurement studies (n=18, no longer claimed as bar-meeting publications)

| Paper | S | I | D | Justification |
|---|---|---|---|---|
| #7 Type-Evident Code | 2 | 2 | 3 | Quantifies trivially recoverable annotation burden; direction predictable; dataset value for type-tooling only. |
| #15 Conventional Commits | 2 | 2 | 3 | Spec-compliance census; self-selection confound found and fixed; style-spec stakes low. |
| #18 Integrity Posture | 3 | 2 | 4 | Supply-chain security archival value; mirror-origin confound honestly decomposed; C3 honest negative. |
| #20 Agent Instruction Files | 2 | 2 | 3 | First count of a new format; detector FP fixed honestly; predictable direction (AI-native lead). |
| #25 DB Schema Migrations | 2 | 2 | 3 | Rollback-support snapshot; real-risk examples (Liquibase/TypeORM) but descriptive. |
| #29 RISC-V ISA Extensions | 3 | 3 | 4 | 5-channel ISA-requirement detection; custom-extension 15% is ecosystem-relevant; still a snapshot. |
| #38 eBPF Program Structure | 3 | 3 | 4 | Kernel-selftests ≠ production is a real belief correction; **R**: production-stratum longitudinal + barrier analysis would reach A. |
| #41 QUIC/HTTP-3 Adoption | 3 | 2 | 4 | Self-implemented (nginx/haproxy native) challenges library-stack assumption; **R**: reframe around that insight + migration depth. |
| #43 LLM-as-Judge Practice | 3 | 2 | 3 | 0/16 human-validation gap is decision-relevant to eval vendors; practice census otherwise descriptive. |
| #45 ARIA/Accessibility Practice | 2 | 2 | 3 | Density spread 12.6×; H3 honestly downgraded to directional; descriptive. |
| #48 ROS 1→2 Migration | 3 | 2 | 4 | EOL-planning relevance; hermetic-migration falsification (0/432 coupling) genuine; **R**: migration *trajectory* (longitudinal) would reach A. |
| #50 Model Cards | 3 | 2 | 4 | EU AI Act Art. 53 compliance ground truth; gating axis found; **R**: compliance decision analysis (who is exposed, when) would reach A. |
| #52 C/C++→Rust Rewrites | 3 | 2 | 3 | Wholesale-vs-binding finding (15/16 vs 1/16) strategy-relevant; n=16 pairs thin. |
| #57 Multi-Agent Architectures | 3 | 2 | 3 | 68% self-description/architecture label gap; snapshot. |
| #61 PQC Migration | 3 | 2 | 4 | Rarity 2.0% + dependency-carrier 91% decision-relevant to CNSA-deadline planning. |
| #63 Consensus Adoption | 3 | 2 | 4 | Raft 66.7%; H4 2014-cohort zero defections is a longitudinal seed worth extending. |
| #65 eBPF Adoption | 3 | 2 | 3 | Hype-vs-reality rarity 3.4%; family-baseline value. |
| #68 MCP Adoption | 3 | 3 | 5 | 23.6% concentrated + honest H2 falsification + NEG-control discipline (method exemplar); **R**: H4 longitudinal (adopter survival/trajectory, already seeded) + integrator decision implications would reach A. |

## Disposition summary

- **A (retain, n=3)**: #1, #33, #36 — remain in the bar-meeting publications list.
- **B (archival, n=18)**: moved below the bar in the index; data/methods retained and still
  byte-identical reproducible; explicit label prevents future readers from mistaking them for
  general-journal-significance claims.
- **R (elevation paths, listed under B)**: #38, #41, #48, #50, #68 — each has a concrete extension
  (longitudinal measurement / decision analysis) that could reach Tier A; tracked as future-work
  candidates, not forced reopens.
- **Deleted**: none (no misconduct; artifacts are honest and reproducible; deleting would destroy
  data, which real journals do not do for non-fraudulent work).

## Policy actions this re-assessment feeds

1. Review template gains a 5th dimension **Significance (1–5)** with the forced test above.
2. Census-pipeline reuse across domains caps Novelty at 3 absent new instrument/construct, a result
   against a stated prior, or a decision-relevance argument (this re-assessment applies it
   retrospectively).
3. Registration template gains a **stated-prior** section (direction + reason from theory/evidence;
   vendor hype is not a reason).
4. Family applications beyond the first require longitudinal/panel design or a new construct —
   further horizontal snapshots are not accepted as bar-meeting submissions (they may be accepted
   as archival measurement studies with explicit labeling).
5. CfP/positioning will be made explicit: Tier-A general journal vs archival measurement track
   (IMC/Scientific Data-style), so the two tiers are honest and deliberate.
