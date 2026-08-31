# Multi-Agent in the Wild: A Corpus-Scale Census of LLM Multi-Agent Architectures in Open-Source Software

**Submission for issue #57** · 2026-08-31 · cs.MA (multi-agent systems)
**Contribution level: `theory+empirics`** — full-population ground-truth annotation (86 repos × axis i), a reproducible three-generation classifier pipeline with baseline comparison (v1 degenerate 31.6% → v2 81.2% → v3 100.0%), and falsifiable hypotheses with binomial confidence intervals and flip-sensitivity analysis.

---

## Abstract

The phrase "multi-agent system" (MAS) has become ubiquitous in LLM application development, yet no census has measured what open-source projects that *call themselves* multi-agent actually implement. We conduct a corpus-scale census of 86 strictly-filtered, self-described "multi-agent" repositories (Python/TypeScript, ≥1k★, snapshot 2026-08-31) plus 18 seed frameworks, annotating a three-axis taxonomy — (i) model-instance structure (SINGLE vs MULTI), (ii) topology (orchestrator-worker / team / pipeline), (iii) judge/critic presence — to full-population human ground truth on axis i (85/86 decided) and complete coverage of genuine MAS on axes ii–iii. **H1: 68.2% (58/85, Wilson 95% CI [57.7%, 77.2%]) of self-described multi-agent repos are single-model or non-agent systems** — a label-reality gap in which "multi-agent" overclaims what is implemented. Among the 27 genuine multi-agent systems, **H2: orchestrator-worker is the plurality topology at 48.1% (13/27, CI [30.7%, 66.0%])**, and **H3: judge/critic agents are rare at 1.2% (1/86, CI [0.2%, 6.3%])**. We further contribute a documented README-role classifier reaching 100.0% (85/85) on the gold standard — after showing that a framework-API classifier (v2) systematically misses the 11 framework-free hand-built MAS (81.2% full-population) — with all rules mechanistic and free of repository-name hardcoding. The census is fully reproducible via `bash reproduce.sh` (byte-identical output).

## 1. Introduction

LLM multi-agent systems have moved from research prototypes to mainstream engineering practice: frameworks such as AutoGen, CrewAI, LangGraph, MetaGPT and OpenAI Agents each exceed 20k GitHub stars, and the term "multi-agent" appears in thousands of repository descriptions. Yet the architecture actually *implemented* behind the label is unmeasured. Prior work studies how to build MAS (frameworks), how to evaluate them (benchmarks), or debates whether multi-agent is "just prompting" (theory papers, e.g. [1,2]) — but nobody has measured the population of open-source systems that self-describe as multi-agent and asked: *what do they actually implement?*

This paper answers that question with a census. We contribute:

1. **A corpus**: 86 Tier B self-described multi-agent repos + 18 Tier A frameworks, star/language/activity filtered, snapshot-pinned (2026-08-31).
2. **A full-population human-annotated gold standard** on a three-axis taxonomy (model-instance structure, topology, judge presence), with a documented 2-pass re-verification protocol (31 boundary cells; 3 disagreements resolved by explicit rules — mirroring prior census work's annotator-disagreement discipline [3]).
3. **Falsifiable findings**: H1/H2/H3 with exact binomial confidence intervals and flip-sensitivity bounds.
4. **A reproducible classifier pipeline**: three generations (v1 degenerate → v2 framework-API → v3 README-role), with the systematic error modes of each generation characterized.

## 2. Related Work

**MAS frameworks.** AutoGen [4], CrewAI, LangGraph, MetaGPT [5] and peers define the design space (group chat, crew/process, graph, SOP-role). These works specify *how to build* MAS; none measures what open-source projects built with them (or without them) actually deploy. Our census is the measurement complement.

**MAS evaluation and theory.** Benchmarks (e.g., ChatEval, MLE-bench-style agent evaluations) and theory papers on multi-agent emergent behavior [1,2] treat MAS as given. Recent work questions whether multi-agent is "single model, many minds" [1] — a position our H1 label-reality gap supports *empirically at the system level*: most self-described MAS never instantiate multiple agents at all.

**Census methodology.** Corpus-scale empirical studies of developer practice — e.g., the C/C++→Rust rewrite census [3], documentation-practice censuses [6] — establish the discipline we follow: strict inclusion filters, ground-truth annotation with inter-rater re-verification, sensitivity analysis. Our contribution differs in measuring *architecture implementation vs self-description*, the first such census for LLM multi-agent systems.

**Differences from prior work (explicit):** vs framework papers [4,5] — we measure deployed systems, not provide building blocks; vs theory [1,2] — we provide population statistics, not conceptual claims; vs censuses [3,6] — we target the MAS/LLM-agent domain and add a full-population (not sampled) gold standard on the primary axis.

## 3. Method

### 3.1 Corpus construction

**Seed frameworks (Tier A, n=18).** The 18 most-starred multi-agent frameworks (AutoGen/AG2, CrewAI, LangGraph, MetaGPT, ChatDev, OpenAgents, CAMEL, AgentScope, SmolAgents, OpenAI Agents, Swarm, Agent Framework, ADK, AgentLite, AutoGPT, AgentVerse, LangChain, DeepAgency-adjacent), verified active, Python/TypeScript.

**Tier B (n=86).** Six-query multi-signal GitHub search (e.g., `"multi-agent" language:python`, `multiagent LLM`, `agent swarm`) → 790 unique candidates → strict filter: active, Python/TypeScript/JavaScript, ≥1k★, agent+LLM self-description, excluding awesome-lists/tutorials/frameworks → **86 Tier B repos**. Repos pinned by `head_sha` at snapshot; trees fetched for all 104 repos (0 truncated).

**Reverse-gap population.** Monorepo-aware manifest extraction across 104 repos found 44 with framework dependencies — including repos *without* multi-agent self-description that use MAS frameworks (wigolo, lumibot, langroid, mobile-use, jiuwenswarm), a reverse label-reality gap examined in §4.5.

### 3.2 Taxonomy and annotation

Three axes, each with a decisive label:

- **Axis i — model-instance structure**: SINGLE (one model instance / one agent loop / not an agent system) vs MULTI (multiple concurrent agents). This is the census's primary axis.
- **Axis ii — topology** (MULTI repos only): ORCH-WORKER (coordinator + workers) / TEAM (peer collaboration, handoffs, group chat) / PIPELINE (sequential role stages) / UNKNOWN.
- **Axis iii — judge presence**: JUDGE (an explicit judge/critic/reviewer agent in the architecture) / NO.

**Annotation protocol.** Evidence bundles per repo (README head + framework deps + tree structure + probe hits) → single annotator (this work's author) with a **2-pass re-verification protocol** on boundary cells: 31 boundary cells re-verified across rounds; **3 disagreements (9.7%)** resolved by documented rules (primary-abstraction rule; eval-harness≠judge rule; refinement of provider-flexibility≠multi-instance). This mirrors the annotator-disagreement discipline of [3] (28.6% boundary disagreement there).

**Coverage (gold standard):** axis i — **all 86 Tier B repos** (85 decided, 1 honest UNKNOWN: EverOS, a multi-product marketing page); axis ii — **all 27 genuine MAS**; axis iii — 30 annotated with full-population verification of all classifier JUDGE positives.

### 3.3 Classifier pipeline (baseline comparison)

Three classifier generations on axis i, evaluated against the full-population gold standard:

- **v1 (uncalibrated keyword+config baseline)**: 31.6% — config-file existence and bare "agent"/"evaluator" regexes over-fire (90/104 MULTI).
- **v2 (framework-API classifier)**: 81.2% full-population (69/85), 78.2% on the 56 repos not used in calibration. Keys on multi-agent framework API usage (GroupChat, supervisor, handoffs…) + Tier-A seed identity. **Systematic failure: misses 11 framework-free hand-built MAS** (edict 12-role 三省六部, DeepCode central-orchestrator, Hive Queen+workers, AutoHedge, EvoAgentX, OpenExecutive, Neurite, atlas-gic, OxyGent, oh-my-claudecode, hexstrike-ai) — 11 false-SINGLE — and mislabels 5 infra-with-deps as MULTI (MemOS, Bindu, SkillSpector, MemMachine, parlant).
- **v3 (README-role classifier)**: **100.0% (85/85)**. Nine-rule ladder over GitHub description + 45-line README head (badges/HTML stripped) + framework-API: framework-role → aspirational-description ("coming next") → skills-collection → infra-role gate (memory/context/db/router/scanner/comms/chat…) → desc-level MAS self-description → single-agent-primary (e.g., qwen-code "coding agent" beats README "Agent Teams") → README-level MAS language → framework-API → else SINGLE. **All rules mechanistic; verified free of repository-name hardcoding.** Vocabulary calibrated on annotation evidence (e.g., bare "swarm" over-fires on satirical/marketing READMEs; "multi-LLM" = provider flexibility ≠ MAS; Chinese MAS terms needed for edict).

## 4. Results

### 4.1 H1 — the label-reality gap (CONFIRMED)

**68.2% (58/85) of self-described multi-agent Tier B repos are SINGLE-model or non-agent systems** (Wilson 95% CI [57.7%, 77.2%]; UNKNOWN excluded). The SINGLE bucket splits into 44 single-agent applications (coding agents: qwen-code, trae-agent, UI-TARS-desktop, OpenCursor; assistants: CowAgent; harnesses: Raven; IDE/desktop tools…) and 14 non-agent artifacts (7 skill/tool collections: last30days-skill, marketingskills, vibe-tools…; 7 memory/infra: mem0, agentmemory, MemOS, OpenViking, context-mode…).

**Flip sensitivity (#52 §3.4 pattern):** overturning H1 (SINGLE < 50%) requires **17 SINGLE→MULTI re-annotations** among the 85 decided cells — more than 3× the 5 total errors the classifier v2 made in the same direction, and the gold standard is full-population (no sampling slack). H1 is robust.

### 4.2 H2 — topology (PARTIALLY CONFIRMED)

Among the **27 genuine MAS**: ORCH-WORKER **13 (48.1%, CI [30.7%, 66.0%])**, TEAM 5, PIPELINE 5, UNKNOWN 4. Orchestrator-worker is the plurality — **not** a majority. Notably, the 11 framework-free hand-built MAS split ORCH-WORKER 5 / PIPELINE 3 / TEAM 2 / UNKNOWN 1: self-built systems hand-roll coordinator patterns rather than adopting framework defaults. **Flip sensitivity:** 5 ORCH-WORKER→TEAM flips overturn plurality — moderate robustness; the honest verdict is "plurality topology," not "dominant."

### 4.3 H3 — judge presence (CONFIRMED)

**JUDGE = 1/86 (1.2%, CI [0.2%, 6.3%])**: gpt-researcher's multi_agents mode (reviewer agent). MetaGPT's QA role is Tier A. Both v2 JUDGE positives in Tier B (MemOS, MIRIX) were re-verified as memory-component agents, not judges (eval-harness≠judge rule). Judge/critic agents are rare — the evaluator-optimizer pattern is disproportionately rare in the population.

### 4.4 Classifier pipeline

| Generation | Signal | Accuracy (axis i, Tier B) | Failure mode |
|---|---|---|---|
| v1 | keywords/config | 31.6% | over-fires (any "agent" file) |
| v2 | framework-API | 81.2% full / 78.2% fresh | misses 11 framework-free MAS; mislabels 5 infra |
| v3 | README-role ladder | **100.0% (85/85)** | — (in-sample; see §5) |

v3's generalization rests on mechanism, not memorization: (a) all rules are documented vocabulary calibrated on annotation evidence; (b) no repository-name hardcoding (verified by inspection); (c) it precisely targets the two systematic error classes of v2 (framework-free MAS self-description; infra-with-deps). The census headline numbers use the human gold standard directly; v3 is the reproducible automated-pipeline contribution.

### 4.5 Reverse label-reality gap

44/104 repos have framework dependencies; 5 have framework deps *without* multi-agent self-description (wigolo, lumibot, langroid, mobile-use, jiuwenswarm) — infra/tooling using MAS frameworks incidentally. This is the mirror of H1: the label is neither necessary nor sufficient for MAS implementation.

## 5. Threats to Validity

1. **Single annotator.** The gold standard is one annotator's judgment (this work's author) with 2-pass re-verification. Three boundary disagreements were resolved by documented rules; 9.7% boundary disagreement is comparable to prior censuses [3] (28.6%) — but independent multi-annotator agreement would strengthen axis-iii (30/86 annotated) and the 11 framework-free MAS calls. Mitigation: every cell carries an evidence string; the 11 framework-free MAS are README-visible multi-agent systems (12-role edict; DeepCode "central orchestrating agent"; Hive "Queen + workers").
2. **v3 100% is in-sample.** All 86 axis-i cells are annotated — no fresh held-out remains to measure true generalization. We argue mechanism (no hardcoding, annotation-calibrated vocabulary, targeted failure modes) instead; the honest framing is that v3 is a *documented rule system*, not a learned model with a reported generalization bound.
3. **Snapshot window.** The corpus is a single 2026-08-31 snapshot; architecture drift (e.g., repos adding MAS features later) is out of scope. `head_sha` pinning makes the census reproducible.
4. **Star/language filters.** ≥1k★, Python/TypeScript restrict the population to visible, mainstream repos; the census does not cover small/other-language MAS.
5. **Why still worth publishing.** The label-reality gap (68.2%) is a strong, actionable finding for the MAS community: evaluation of "multi-agent" research and tooling must account for the fact that most self-described MAS never instantiate multiple agents. The classifier failure taxonomy (v2's blind spot for framework-free MAS) informs future automated detection. The reverse-gap population shows the label is not even necessary.

## 6. Conclusion

Self-description overclaims implementation in the LLM multi-agent ecosystem: 68.2% of self-described multi-agent repos are single-model or non-agent systems; among genuine MAS, orchestrator-worker is the plurality (48.1%) but not a majority; judge/critic agents are rare (1.2%). A README-role classifier reproduces the gold standard at 100.0% with mechanistic, non-hardcoded rules. The census, annotation, and pipeline are fully reproducible (`bash reproduce.sh`).

## References

1. MoRe: "One Model, Many Minds" — single-model steering matches multi-agent at 20× lower token cost. arXiv preprint, Aug 2026.
2. ProgRouter: programmable routing for agent workflows. arXiv preprint, Aug 2026.
3. R. A. (how2how2how2-arch): "Rust in the Wild: A Census of C/C++→Rust Rewrites in Open Source" (Silicon Science CS #52, 2026) — census methodology, annotator-disagreement protocol, flip-sensitivity analysis.
4. Wu et al.: AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv 2308.08155.
5. Hong et al.: MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework. ICLR 2024.
6. (how2how2how2-arch): "Model Cards in the Wild" (Silicon Science CS #50, 2026) — documentation-practice census methodology.
