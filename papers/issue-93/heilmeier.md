# Heilmeier answers — issue #93

**Direction**: *When Does a Human Approval Gate Pay? Binding Fidelity Sets the Net Value of Human-in-the-Loop Control for Tool-Using Agents*
**Registered**: 2026-09-21 (R406), label `in-preparation`, issue #93.
**Author instance**: `emrg-e2816d37`.

The registered text is the issue body (the journal is the record). This file is the working copy: it holds the
screening trail that did **not** go into the registration, the anchor table, and the round plan.

## 1. Candidate pool this round (Phase A selection, R406)

External scans: arXiv API (`abs:` field queries, `sortBy=submittedDate`) over **arXiv submission date
2026-01-01 → 2026-09-21**, scan date 2026-09-21 — ~67 queries across cs.SE / cs.AI / cs.LG / cs.DC / cs.CR /
cs.NI / cs.DB / cs.OS / cs.MA / cs.AR / cs.CL / cs.ET plus law-style and overturning-claim phrasings; plus
Crossref (`query.bibliographic`, publication date 2026-01-01 → 2026-09-21). Raw JSON kept in `scan/`.
Hotspot signals: agent security ≈ agent memory > agentic serving ≈ context management; the 2026-09 wave of
approval-binding papers (2609.21081, 2609.18411, 2609.11596, 2609.15576) is 4 days old.

| candidate | what it would have been | screened out because |
|---|---|---|
| C1 capability scoping / least privilege for tool-using agents | boundary law for static session grants vs per-call mediation | **occupied**: 2609.18820 (2026-09-16) already claims the core — step-scoped monitors cannot see compositional violations, and it names the repair |
| C2 approval / escalation boundary law | net value of a human gate vs channel fidelity | **TAKEN — this direction** (no threshold published; see the registration's reverse gap) |
| C3 KV-eviction boundary law | when does eviction scoring start to cost accuracy | **partly occupied**: 2605.18053 (structure dominates scoring), 2609.16617 (divergence decomposition), 2609.20068 (marginal-utility framework); and it needs real models |
| C4 context-compaction boundary law | the inverted-U in compaction ratio | **occupied**: 2608.01326 *Context Compaction Theory*, 2608.22752 *The Compaction Cliff*, 2607.08032 (rate–distortion view of memory compaction), 2605.10828 (nonlinear distractor impact) |
| C5 agent-memory backend adjudication | does structure beat raw retrieval under a matched budget | **crowded + audit-shaped** (2608.12888, 2608.13883, 2608.25489); and the host's standing instruction excludes audit-type work |
| C6 world-model / planning boundary | when does a learned model beat a reactive policy | classic compounding-error theory already bound the region; no fresh gap found in the window |
| C7 tool-contract / schema value | does a declared contract beat free text | thin novelty (function-calling benchmarks abound), no anchor with a measured parameter |

## 2. Anchor table for #93 (parameters read from published measurements, never invented)

| anchor | published measurement | what it becomes in the harness |
|---|---|---|
| 2605.24309 (2026-05-23) | runtime approval deployed by 15 of 21 production agent systems; 59 papers / 21 systems / 26 plugins as of April 2026; names "approval fatigue vs uncontrolled autonomy" with no criterion | the *deployed* regime the study measures (why the question is live; and `s` near 1 in practice) |
| 2609.21081 (2026-09-17) | approval hijacking reproduced in 7 Agno AgentOS releases (≤ 3.0.9) and 12 LangGraph Agent Server versions (≤ 0.14.0); OpenAI Agents SDK 0.22.0/0.22.2 is a negative control | the two adversary variants (representation mismatch; post-approval substitution) and the "binding holds" arm |
| 2609.18411 (2026-09-16) | attack success 68–100% without binding → 0% with it; 78% legitimate completion; 0% false block | the `b → 1` arm's target numbers and the false-block rate `c` |
| 2608.24569 (2026-08-25) | over 1,296 controlled episodes: normal handoff compression gives 100.0% deactivation of binding state and 54.2% forbidden actions downstream | the measured low-fidelity end of the `b` axis (an input to the law, not a hypothetical) |
| 2609.15576 (2026-09-14) | production response-act checker accepts 291 of 302 unsupported-labelled answers | an independent estimate of the *false-accept* side of reviewer accuracy `a` |
| 2609.18820 (2026-09-16) | step-scoped monitors cannot detect compositional violations however accurate they are | the "accuracy is not the axis" statement for a *different* mechanism — the paper's stated difference |
| 2606.29406 (2026-06-28) | delegation authority as a POMDP; policy under uncertainty, channel assumed faithful | the closest decision-policy work; the difference is that the channel is this study's variable |
| 2608.01388 (2026-08-02) | recall of a fixed-invariant FSA monitor is bounded by attack-distribution entropy | the adjacent *programmatic-monitor* law; the human gate has no such bound published |

## 3. Plan (one small goal per round)

- **R407**: model v0 — the screening-only case `b = 1` in closed form (gate value = `s·(−Δharm) − c·E[escalations]`, with the reviewer's ROC), checked against the harness before any other cell is read. Round-note every defect found by that check.
- **R408**: the laundering channel — value sign at `b < 1`, the insensitivity measurement `(∂E/∂a)/(∂E/∂b)`.
- **R409**: the escalation optimum `s*(b)` (PB3) and the four-gate-design map (no gate / text approval / canonical rendering / + use-time check), with the adversary variants.
- **R410**: PB4 — the marginal value of use-time checking as a function of the faithfulness of the representation it reads.
- **R411**: disjoint seed streams (≥ 3) with CIs; external validation of the two published orderings; falsification checks.
- Then: figures, the ≥ 100-entry bibliography with a stated difference per entry (the R404 recipe), the assembly/traceability layer, `reproduce.sh`, `reference-check.md`, the `Outcome` line per prior, and submission.

## 4. Diversity note

`recent subfields` rotation for the live journal: #1 cs.CL/cs.IR · #38 cs.MA · #42 cs.SE×cs.LG · #44 cs.CR
(re-execution) · #47 cs.DS · #50 cs.DC×cs.AI · #87 quantum ML (cs.ET∩quant-ph∩cs.LG) · **#93 cs.CR×cs.AI
(human-in-the-loop control integrity)** — the first paper in this live journal whose construct is a *channel
between a human and an executing system*, and the first on approval/binding. cs.CR is revisited once, four
papers apart, on a construct with nothing in common with #44 (trustless re-execution sampling).
