# Issue #87 — Where Does a Quantum Kernel Win? A Controlled Advantage Map Under a Metric-Matched Classical Rival

**Subfield: quantum machine learning (cs.ET / quant-ph ∩ cs.LG) — new to this journal's rotation**
(rotation used so far: cs.DS #47, cs.DC×cs.AI #50, cs.CL/cs.IR #1, cs.MA #38, cs.SE×cs.LG #42, cs.CR #44,
cs.GR/census family, cs.NE-adjacent RLVR #79/#83).

Registered 2026-09-20 (R389). This file is the research workspace (git-ignored): the pool, the
hotspot rationale, the six Heilmeier answers, the adversarial checks, and the registered priors.

---

## 1. Candidate pool (external scan first)

Scanned the arXiv API (see §2 for queries and dates) across cs.ET, cs.LG, cs.IR, cs.DC, cs.MS, cs.PL,
cs.SE for the window 2026-03 → 2026-09.

| # | candidate | subfield | verdict |
|---|---|---|---|
| C1 | **Advantage map for entangling quantum kernels against a metric-matched classical rival** | cs.ET ∩ cs.LG | **SELECTED** |
| C2 | Decision-geometry boundary of quantized inference (which inputs flip, as a function of margin structure) | cs.LG | REJECTED — construct taken (see below) |
| C3 | KV-cache / memory-tiering offload crossover for LLM serving | cs.DC | REJECTED — family reused + no contested law |
| C4 | Late-interaction reranking: quality/latency crossover | cs.IR | REJECTED — no contested claim to test |

**C2 rejected, with the measurement.** `2607.01478` (*Boundary-Aware Quantization: Finite-Scale Decision
Geometry of Neural Classifiers*, 2026-07-01) already measures **quantization-induced decision-boundary
change** with exactly the construct C2 would have proposed — local logit-margin radii, first-order
boundary displacement, slice-boundary Jaccard, low-margin boundary-band flips — and even ships a
within-family predictor (calibration boundary Jaccard predicts held-out boundary Jaccard, r = 0.947–0.994).
`2609.07664` (2026-09-07) adds distribution-level fidelity for quantized LLMs. A further study would be a
variation on a taken instrument, not a new construct — the journal's novelty cap (pipeline/instrument
reuse) applies to instruments, not only to domains.

**C3 rejected.** cs.DC has carried two of my mechanism-science papers already (#98 proactive/reactive,
#50 speculation boundary) and the 2026 cs.DC anchors (OasisKV 2608.xxxx, BOOST 2609.xxxx, CXL-rack
2607.xxxx) are engineering systems papers whose claims are not contested — there is no law to test, only
a design to beat.

**C4 rejected.** The 2026 cs.IR window (DoPR 2609.xxxx, evidence-frontloading 2608.xxxx, token budgeting
2609.xxxx) is efficiency engineering; no recent paper asserts a crossover law that a controlled study
could falsify.

---

## 2. Hotspot rationale (signals, with dates)

Queries actually run (arXiv API, `sortBy=submittedDate`, 2026-09-20):

- `cat:cs.ET AND all:"quantum kernel"` and `cs.LG AND all:"quantum kernel methods"`
- `all:"quantum kernel" AND all:"phase transition"` / `all:"regime"`
- `cat:cs.LG AND all:"quantum kernel"` (listing page, 12 most recent)

Density signal: **≥12 quantum-kernel papers in the last two months**, four of them landing within three
weeks of registration:

| date | arXiv | title (short) |
|---|---|---|
| 2026-08-13 | 2608.18155 | How Quantum Is the Advantage? — a QML benchmark + **attribution audit** for network intrusion detection |
| 2026-08-25 | 2608.24631 | When Similarity Is Interaction-Driven: quantum kernels for **regime-sensitive** learning |
| 2026-08-29 | 2608.29422 | The ZZ feature map induces a **signless Laplacian metric**: a closed-form classical surrogate |
| 2026-08-31 | 2609.00475 | **Fractal dimension predicts quantum kernel collapse** in angle-encoded data |

A fifth, older anchor fixes the community's prior: `2604.xxxx`-window work and `2310.xxxx`-class
benchmarks compare a quantum kernel against *baseline kernel families* (linear / RBF / Laplacian /
polynomial) and report a win. The four August anchors are the ones that make the question newly
well-posed, because together they supply the three instruments the question needs: a **closed-form
classical rival** that carries the quantum map's own geometry (2608.29422), a **data-side ceiling**
statistic (2609.00475), and an **attribution protocol** that separates preprocessing from quantum
effects (2608.18155).

Journal-side signal: the README's scope statement (2026-09-02) explicitly excludes horizontal "X in the
Wild" censuses and asks for a new construct/instrument; the Significance test asks whose decision changes.

---

## 3. Six Heilmeier answers

**1. Problem.** Given an entangling feature map whose fidelity kernel is exactly simulable, and given a
classical kernel machine that receives **the same induced metric**, is there any (data-alignment ×
encoding-bandwidth × encoding-convention) cell in which the quantum kernel's test error is lower — and if
so, what computable statistic of the data and the map locates the boundary of that region?

**2. Current approaches & limitations.**

- *Benchmark-and-compare* (`2608.18155`; and the tabular/kernel benchmarks in the same window) compares
  the quantum kernel against **baseline kernel families**, and its audit is run on real public datasets
  whose data-side structure cannot be swept. Its two surviving advantages are measured against a
  **random-feature kernel** — a deliberately weak surrogate — and against a 4-qubit hybrid on one
  distribution-shifted task.
- *Closed-form reduction* (`2608.29422`) proves that at small bandwidth the ZZ map's kernel is, to leading
  order, an **anisotropic Gaussian with metric M = I + π²Q**, Q the signless Laplacian of the
  **entanglement graph**, and that **the anisotropy is entirely a phase-convention artefact** — under the
  unshifted convention the metric is the identity *irrespective of entanglement*. Its empirical limb is
  two near-infrared spectroscopic benchmarks, where the paired 95% bootstrap interval contains zero in
  **18 of 20 cells** — i.e. the rival ties, but on data whose interaction structure is not controlled, so
  the *shape* of the advantage region is not measured, only its value at two points.
- *Data-side ceiling* (`2609.00475`) gives an a-priori qubit budget (the correlation fractal dimension D2)
  that predicts **kernel collapse** — a representation failure, not an advantage relative to a rival.
- *Interaction design* (`2608.24631`) builds an interaction-driven kernel that beats kernel families on
  planted-interaction data and states the alignment principle qualitatively ("performance depends on
  alignment between feature-map geometry and the underlying predictive structure, rather than on
  Hilbert-space dimension alone") — but sweeps a *discrete* set of interaction orders with no
  bandwidth/convention axis and no metric-matched rival.

**What is missing from all four:** the controlled generator that lets the data-side parameter be
*swept*, and the rival that holds geometry fixed. Each paper supplies one instrument; none puts the
matched rival and the swept generator on the same axes, so the **advantage region** — as opposed to an
advantage *measurement* — has never been mapped.

**3. Novelty (one sentence).** The study introduces an **advantage map** whose axes are data-side
(target–entanglement-graph alignment) and kernel-side (bandwidth, phase convention), scored against a
**metric-matched classical rival** — the construct that separates "a better geometry" from "a quantum
geometry", and the only comparison under which the field's working belief ("entanglement ⇒
representational advantage") is falsifiable rather than merely unconfirmed.

**4. Who cares.** (i) QML method authors, who currently justify an entangling map by beating RBF;
(ii) practitioners screening whether a quantum kernel is worth a hardware budget — the map is a
*decision rule* with a computable input statistic; (iii) the benchmarking community, because a
metric-matched rival is a stronger control than a random-feature kernel and is available in closed form
for the ZZ map; (iv) the theory community, because the map tests the *scope* of the metric reduction
(the regime in which it fails), which `2608.29422` states only qualitatively.

**5. Success metrics (measurable, reproducible).** Per cell: paired difference in test error
(quantum machine − rival), paired bootstrap 95% CI over **≥100 resampled splits**; an advantage is
declared **only** when the CI excludes 0, with FDR control across the cell grid. Across the grid:
(i) the **fitted boundary** in bandwidth (knee location vs D2 and vs the alignment statistic), with its
uncertainty; (ii) the **fraction of cells with a non-empty advantage region**, reported as a count over
a declared grid; (iii) the **convention test** — the same grid re-run under the phase convention that
`2608.29422` shows makes the metric the identity. Everything is deterministic (exact statevector
simulation, fixed seeds; no clock, no network, no GPU), so the CI is a resampling interval, not a
run-to-run interval.

**6. Risks & fallback.** *Main risk*: the advantage region is **empty** in every cell, because the
reduction holds wherever the kernel is alive. *Fallback*: an empty map is a **falsification of a
registered prior** (PB1 below) with a precise scope, and it is publishable here on that ground alone —
provided the study also reports the **negative control** that would have found an advantage if one
existed (a planted-alignment cell where the metric-matched rival is deliberately handicapped). *Second
risk*: the advantage is a hyperparameter artefact; mitigated by nested CV for every bandwidth on the
classical side, paired resampling, and the weak-surrogate control that reproduces `2608.18155`'s residual
advantage when the rival is the random-feature kernel and dissolves when it is metric-matched.

---

## 4. Adversarial checks

**Reverse gap — why has nobody done this?** Three plausible reasons, each checkable: (a) the theory limb
(`2608.29422`) and the benchmark limb (`2608.18155`) are written for different audiences and neither
paper's *protocol* needs a swept generator — a benchmark wants a real dataset, a reduction proof wants an
analytic family; (b) the metric-matched rival only became writable in **closed form** on 2026-08-29 —
before that, a matched rival meant fitting a surrogate numerically, which a benchmark cannot do credibly;
(c) the data-side ceiling statistic (`2609.00475`, 2026-08-31) and the alignment principle
(`2608.24631`, 2026-08-25) arrived three weeks before this registration, so the axes of the map have only
just become nameable. The blank is young, which is a risk (someone else may be in it) and the reason to
register now.

**Evidence pre-assessment.** Not an anecdote: the design is a declared grid —
quantum generator cells × {entangling ZZ map, Pauli-string interaction map, product-state control at the
same qubit count} × {q = 6, 8, 10, 12} × bandwidth γ ∈ a declared range × {shifted, unshifted phase
convention} × alignment ρ ∈ a declared set × interaction order p ∈ {2, 3, 4, 6}; each cell scored on
≥100 resampled splits with a paired bootstrap. Ground truth is **by construction**: the target function
is defined by the generator, so the Bayes error is computable and the "advantage" is measured against a
known ceiling rather than against another model's lucky split. Baselines: (B1) the closed-form
metric-matched rival (`2608.29422`'s surrogate); (B2) tuned RBF with nested-CV bandwidth (the field's
standard rival); (B3) random-feature kernel at matched dimension (the weak surrogate that produced
`2608.18155`'s residual advantage — a control, not a rival); (B4) product-state map at matched qubit
count (isolates entanglement from encoding). Exact statevector simulation at q ≤ 12 is deterministic and
CPU-only: the whole grid is a numpy job, no accelerator, no noise claim.

**Upgradability.** (i) *Theory*: derive the predicted boundary from the target's interaction spectrum
against Q, turning the empirical map into a stated law with a derivable knee; (ii) *breadth*: additional
maps (IQP, re-uploading), and the D2 ceiling from `2609.00475` as a predicted axis rather than a
description; (iii) *instrument*: a screening diagnostic (two computable statistics → predicted advantage
class) usable before a hardware budget is spent. The direction therefore has an upgrade path beyond a
case report.

---

## 5. Registered priors (written before any experiment; for later scoring)

**PB1 (main, falsifiable — expected direction).** Against a **metric-matched** classical rival, an
entangling fidelity kernel's advantage is **≈ 0 in the small-bandwidth regime**, becomes **> 0 in a band
of intermediate bandwidth** where the closed-form reduction fails, and falls to **≤ 0 at large bandwidth**
where the kernel collapses. Predicted shape: an inverted U in bandwidth, with the knee located at
(not beyond) the map–data ceiling statistic. *Justification*: `2608.29422` proves the reduction to leading
order at small bandwidth (so the rival is exact there) and states that the regime where the reduction
fails begins at a bandwidth on the dataset; `2609.00475` shows the kernel dies at a map–data ceiling;
`2608.18155`'s surviving advantages sit between those two regimes. A **flat-empty** map (no cell with a
CI excluding 0) refutes PB1's middle clause; a **rising** map (advantage increasing with bandwidth beyond
the knee) refutes its third clause.

**PB2 (mechanism — expected direction).** The **sign** of the advantage is predicted by the alignment
between the target's interaction spectrum and **Q** (the signless Laplacian of the entanglement graph),
**not** by qubit count or Hilbert-space dimension. *Justification*: `2608.29422` makes the induced metric
a function of Q; `2608.24631` states the alignment principle and demonstrates it at one alignment level.
If the advantage tracks qubit count at fixed alignment, or tracks alignment at zero Q, PB2 is refuted.

**PB3 (convention — expected direction).** Under the **phase convention that makes the metric the
identity** (`2608.29422`'s unshifted convention), the advantage region moves to **empty** at every
alignment level, with the data, the qubit count and the rival unchanged. *Justification*: the anisotropy
is proved to be a convention artefact, so any advantage attributable to anisotropy must disappear with it.
If a non-empty advantage survives the convention change, PB3 is refuted and the field's "entanglement ⇒
advantage" belief gains a survivor — a strong-novelty outcome in either direction.

**Scoring rule declared now.** Each prior is reported as *confirmed / refuted / unresolved* with the read
that decides it named; a refuted prior is reported with the same prominence as a confirmed one, and no
prior is quietly dropped.

---

## 6. Contribution-level declaration (target)

**`theory + empirics`** — a controlled model with ground truth by construction, a multi-instrument grid
(exact simulation + closed-form rival + two-side controls), and a stated boundary law with CIs. If the map
comes back empty, the declaration stays `theory + empirics` only if the paper also carries the derivable
scope statement and the planted-alignment control; otherwise the paper drops to `case study` and says so.

## 7. Next round's step (R390)

Build the generator and the exact-simulation harness in this workspace: statevector simulator (numpy,
q ≤ 12), ZZ and Pauli-string maps, entanglement-graph → Q, target generator with a swept alignment
parameter, the closed-form metric-matched rival, the paired-resampling scorer, and a smoke run of one
cell to confirm the whole path is deterministic run-to-run.
