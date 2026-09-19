#!/usr/bin/env python3
"""refs_select_v50 -- the AUTHORED selection for issue #50's bibliography.

Each row is (key, title anchor, section, stated difference).  The anchor is a
substring of the record's own title in the controlled pool, so the resolver
binds key -> record and reports every anchor that does not resolve: no entry is
typed into the bibliography, each is bound to a record the controlled scan
returned.  The fourth field is the one-line stated difference and is also the
claim the entry is cited for.
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

SEL = []
SEL += [
 ("uht1995", "Disjoint eager execution", "S2.1",
  "shows eager execution outside program order is optimal when the extra work is free; we price that work, since a discarded tool call is charged to a shared pool."),
 ("oancea2007", "A Lightweight Model for Software Thread-Level Speculation", "S2.1",
  "models speculation across loop iterations in one address space; our speculation crosses a tool boundary and can have external effects."),
 ("oancea2008", "Software thread-level speculation", "S2.1",
  "measures speculation speedups for parallel loops; we locate the contention at which one in-flight call costs more than it hides."),
 ("steffan2000", "A scalable approach to thread-level speculation", "S2.1",
  "supplies the memory-dependence machinery that makes speculative threads legal; we speculate on an agent's own tool calls, not on addresses."),
 ("raghavan2003", "Dynamic schemes for speculative execution of code", "S2.1",
  "adapts when to speculate from observed outcomes inside a processor; we index the boundary by measured contention, not by predictor accuracy."),
 ("pajuelo2004", "Speculative execution for hiding memory latency", "S2.1",
  "hides memory latency by executing past a miss; we hide tool latency in an agent loop and report where hiding stops paying."),
 ("zhao2012", "Hiding I/O Latency with Parallel Pre-Execution Prefetching", "S2.1",
  "overlaps I/O with computation into a private buffer; our harm concentrates in a shared worker pool rather than in a local cache."),
 ("chen2008", "Hiding I/O latency with pre-execution prefetching for parallel applications", "S2.1",
  "hides I/O in HPC kernels where loss is bounded by wasted bandwidth; we show a large share of individual speculative steps lose time outright."),
 ("nylander2020", "Towards Performance Modeling of Speculative Execution for Cloud Applications", "S2.1",
  "models speculative execution for cloud applications in the mean; we report that the mean is the wrong statistic and the tail pair moves the boundary."),
 ("marcuello2000", "A quantitative assessment of thread-level speculation", "S2.1",
  "quantifies speculation benefit across benchmark loops; our quantity is a boundary in a contention coordinate with a per-seed interval."),
 ("martinez2004", "Speculative Locks", "S2.1",
  "speculates past a critical section to raise concurrency; we speculate past a remote call whose compensation cost we vary explicitly."),
 ("redkha2017", "Optimized Speculative Execution", "S2.1",
  "uses speculative task replicates to shorten big-data job tails; we measure the boundary of one such mechanism in a controlled model."),
 ("chen2014", "Smart Speculative Execution Strategy", "S2.1",
  "launches speculative MapReduce tasks past a progress threshold; our boundary is indexed by measured contention instead."),
 ("ibrahim2017", "Progress and Feedback Based Speculative Execution", "S2.1",
  "tunes when to launch a speculative task from progress feedback; we show where that threshold sits and how it moves with the pool size."),
 ("oleksenko2023", "Hide and Seek with Spectres", "S2.1",
  "searches for speculative information leaks; we study the performance side of speculation, which those defences did not price."),
 ("cauligi2021", "Practical Foundations for Software Spectre Defenses", "S2.1",
  "taxonomises software defences against speculative leakage; those defences pay a cost our instrument would book as congestion."),
 ("oleksenko2019", "SpecFuzz", "S2.1",
  "surfaces Spectre-type vulnerabilities by fuzzing; our instrument excludes the security channel entirely and measures time."),
 ("bhattacharyya2019", "SMoTherSpectre", "S2.1",
  "leaks through port contention between speculative and victim threads; the same contention is what our instrument charges as harm."),
 ("ye2020", "Speculative Data-Oblivious", "S2.1",
  "makes speculative execution safe by making it data-oblivious; the leakage question is out of scope here and we price the contention that remains."),
 ("auclair2020", "Speculative Execution in High Performance Computer Architectures", "S2.1",
  "collects the architecture literature on speculation; it predates the agent setting, where a speculative call has an external side effect."),
 ("spork2026", "SPORK", "S2.2",
  "self-speculates a fork of the agent's own trajectory, reporting a 16-37% tool-wait share and an 18% P95 reduction; we reproduce that sign inside its own reported share and locate where it stops paying."),
 ("smc2026", "Speculative Macro Commit", "S2.2",
  "commits predicted macro-actions for tool-using agents and reports up to 44.9% over sequential execution; we show that cell sits above the ceiling our model admits and say why rather than smoothing it."),
 ("specbox2026", "SpecBox", "S2.2",
  "warms sandboxes ahead of use to cut agent setup latency; it measures one interval, while we derive the contention at which warming hurts."),
 ("bpaste2026", "B-PASTE", "S2.2",
  "selects speculative executions under a co-run interference budget; we measure the boundary it budgets against, with compensation priced explicitly."),
 ("costaware2026", "Cost-Aware Speculative Execution for LLM-Agent Workflows", "S2.2",
  "states an admissibility precondition that excludes side-effecting edges; we test that rule and find adverse states inside its permitted region."),
 ("speculativecalls2025", "Speculative Tool Calls", "S2.2",
  "speculates tool calls for agentic inference and reports an isolated speedup; we add the serial baseline and the parallelism it already had."),
 ("spechop2025", "SpecHop", "S2.2",
  "speculates continuously across multi-hop retrieval steps; our mechanism is a single tool call priced by contention."),
 ("specagents2025", "Speculative Interaction Agents", "S2.2",
  "builds real-time agents with asynchronous I/O and speculation; we quantify the share of that gain any parallel schedule would have bought."),
 ("agentboundary2026", "When Tool Calls Succeed but Workflows Fail", "S2.2",
  "catalogues anomalies at the agent-tool boundary; we take that side-effect risk as given and price compensation instead."),
 ("ghosttools2026", "Ghost Tool Calls", "S2.2",
  "protects the privacy of speculative tool calls by not issuing them; we issue them and charge the pool, which is the cost counterpart."),
 ("grotov2026", "How to Speculate about Uncertainty in Agentic Coding", "S2.2",
  "gates speculation on a draft model's uncertainty; we show the gate is not the binding constraint when the pool is the constraint."),
 ("agentspec2026", "AgentSpec", "S2.2",
  "applies token-level speculative decoding inside a batch of agent requests; our speculation is at the tool-call granularity where effects are external."),
 ("asymspec2026", "AsymSpec", "S2.2",
  "makes drafting context-asymmetric for agentic decoding; it accelerates the model, not the tool round trip our instrument isolates."),
 ("tailaware2026", "Decoupling Readiness from Release", "S2.2",
  "decouples readiness from release to cut tail latency of agentic inference; we locate the crossover of the same trade under a fixed pool."),
 ("alossurvey2026", "Is Multimodal Speculative Decoding Ready", "S2.2",
  "surveys speculative drafting methods and their readiness; none of the surveyed methods prices contention in a shared pool."),
 ("specgen2026", "SpecGen", "S2.2",
  "speculatively generates kernel-optimisation candidates; its speculative artefacts are compute-only, so its harm channel is not compensation."),
 ("fleet2026", "FleetSieve", "S2.2",
  "profiles decision-critical requests for SLO-aware fleet configuration; our instrument holds the fleet fixed and moves contention."),
 ("chronos2026", "Chronos", "S2.2",
  "adds bolt-on branching across data stores for stateful applications; that branching is exactly the side-effect case our model charges."),
 ("hidelatency2026", "Hiding Service Latency", "S2.2",
  "hides service latency with deterministic asynchronous execution; we measure the regime where that determinism is what removes the boundary."),
]
io.open(os.path.join(HERE, "refs_select_part1.py"), "w", encoding="utf-8").write(
    "PART1 = " + repr(SEL) + "\n")
print("part1 entries:", len(SEL))
