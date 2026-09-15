# Issue #47 — What Does a Prediction Buy? A Signed-Error Decomposition

Reproduction package for the manuscript in this directory. Every number the paper cites is
**recomputed** from the stage artefacts' primitives by `canonical_runner.py`, and each recomputed
value is cross-checked against the value the stage recorded about itself. No number is typed into
the prose.

## Reproduce

```bash
bash reproduce.sh
```

Runtime is about 3 m 45 s on one CPU core. **Dependencies: the Python standard library only** — no
numpy, no scipy, no network, no `matplotlib`. Python 3.8+.

Expected final lines, and the lines that carry the verdict:

```
criteria: a=MET, b=MET, c=UNMET, d=MET
facts recomputed: 44 | disagreeing with the artefact's own value: 0
coordinate census: 0 violation(s)
  stages and aggregate: OK
  aggregate liveness: OK
  external-cell check liveness: OK
  design freeze: OK
verdict: OK
REPRODUCE: ALL GREEN
```

Criterion (c) is **UNMET by design of the record, not by failure of the run**: the registered
measurement is `ratio(λ_worst-case) − ratio(1)` with λ chosen by a certificate formula, and no stage
computes that formula. The package reports the state instead of substituting the fixed-grid proxy,
whose own direction contradicts the registered one. `canonical_results.json → criteria` carries the
same statement.

Step 5 prints the sha256 of every artefact the package ships, as a block to copy: **a digest quoted
in a report is read off that output, never typed.**

## What the checks are

The package's instruments are held to four disciplines, and so is `canonical_runner.py` itself:

* **the stage table** — every stage's own check list is reduced to `run / failed`, and the reduction
  is cross-checked against the flag that stage recorded about itself. The artefacts do **not** share
  one schema (four carry `checks[i].ok`, one `checks[i].pass`, one carries its checks under
  `verdict`, and one persists only the flag), so each stage **declares** its evidence schema and a
  missing field raises rather than defaulting: "no checks found" and "every check passed" must never
  look alike. The `external` row is `n/p` because that stage's artefact keeps only its flag — a
  residual, stated rather than papered over;

  ```
  stage        script                              run failed flag agrees
  anchor       anchor_smoke.py                       8      0 yes
  v0           instrument_v0.py                     14      0 yes
  scorer       scorer_v0.py                          7      0 yes
  mechanism    mechanism_v0.py                      10      0 yes
  paging       paging_v1.py                          9      0 yes
  sufficiency  sufficiency_v1.py                    15      0 yes
  external     external_cell_v1.py                 n/p    n/p yes
  ```

* **recomputation, not transcription** — 44 named facts are derived from primitives (the witness's
  exact-zero scalar identity, the argmin loss gap, the resolved contrasts, the ordering taus, the
  reach counts). Where the artefact records the same quantity, the two must agree; **0 of 44
  disagree**;
* **liveness** — `canonical_runner.py --selftest` corrupts each recomputation's input in a throwaway
  copy and requires the change to be noticed, comparing against a baseline rather than against the
  recorded field. It distinguishes the two mechanisms: a corrupted *primitive* must move the
  recomputed value, while a corrupted *recorded* field moves nothing and must be caught by the
  cross-check. 8 cases, 0 not noticed;
* **coordinates** — a census over all 11 source files enumerates the eight ways an input can enter
  from outside the package, and requires the three that would make the evidence machine-dependent
  (git object, network, clock/entropy) to be **empty**. It is empty here because the censused
  detector tables are a banner-delimited **declaration span** — data, not code — asserted
  structurally, with the control that a read planted *outside* that span is still caught. An
  exclusion wider than the thing it excludes is the defect this discipline exists for.

Two further controls live in their own files and are run by `reproduce.sh`:

* `external_cell_mutation_v1.py` — **13 mutations** of the external cell, one per named check, each
  of which must make exactly that check fail and no other. This is the control that shows the cell's
  gates can fail at all;
* `freeze_check_v1.py` — **46 checks** re-deriving every number in `design_freeze_v1.md` from the
  artefacts, including its 8-row digest table.

## The claims, and where each one comes from

| claim (frozen) | recomputed value | source |
|---|---|---|
| a scalar error is not sufficient — identical scalar features, different loss | scalar gap **exactly 0**, worst loss gap **−0.5679**, **31 of 39** blocks above their own cluster MDE | `sufficiency_v1_results.json : part_B` |
| the sign channel carries information where the design resolves it | cluster-MDE advantage **+1.48** (ski), **+2.61** (sched), **+0.97** (paging, unresolved) | `… : part_C2.contrast_b_clean` (matched-form rows only) |
| the published ordering survives in **sign** | tau **0.744 / 0.889 / 1.000**; without the zero anchor **0.697 / 0.873 / 1.000** | `external_cell_v1_results.json : cells, tests.X1_order` |

The external cell is anchored to **arXiv:2608.27975** (LAH / S4-FIFO): +26% mean efficiency over
S3-FIFO, +8% over 3L-Cache, worst-trace degradation over FIFO 0.8% versus 8.8% — a *concordant*
published pair (larger mean gain, smaller worst tail). The harness reproduces the sign of that
concordance in all three problems and does **not** reach the published magnitude in two of them; that
limit is measured and reported per profile, not hidden.

## Limits the claim set carries (frozen in `design_freeze_v1.md`)

* **L1** the paging attachment is model-dependent: the step-common attachment is blind to positive
  errors where it does not clamp, the per-page attachment is the one used, and the trap is measured
  (a positive *bias* is not a non-negative *multiplier*).
* **L2** the object-level design's null is **shifted** — its specificity control penalises the odd
  parameter by ~13 cluster MDEs — so a *negative* verdict is uninterpretable. Only the positive
  resolutions are reported as evidence; the unmatched-form reading is retired, its sign not even
  stable across problems.
* **L3** unit reach is uneven and published per profile: the harness reaches the published
  robustness scale in **ski** (12 of 13 profiles at or above 0.8%) and in **neither** paging nor
  sched (0 of 13; the worst unit is *better* than FIFO everywhere). No magnitude claim is available
  in those two problems.
* **L4** concordance is a rank/sign agreement, not a magnitude match — no unit conversion is
  attempted; the anchor's +16.7% comparison mean is **derived** in the artefact, not asserted.
* **L5** the generalising unit is the **profile**, not the repeated measurement: every resolution
  verdict quotes the cluster unit, because the earlier figure was optimistic by 3.7–6.3×.
* **L6** synthetic harness, real anchor: the losses come from the generators, and the external cell
  anchors ordering and reach without reproducing the system's numbers.

## Files

| file | what it is |
|---|---|
| `reproduce.sh` | the one command above |
| `canonical_runner.py` | runs the stages, recomputes every cited number, cross-checks it, and prints the coordinate census |
| `anchor_smoke.py` | the classic competitive ratios and the consistency end, recovered exactly |
| `instrument_v0.py` | the harness: error generators, costs, the crossed grid |
| `scorer_v0.py` | the held-out fit of the scalar baseline against the signed decomposition |
| `mechanism_v0.py` | the mechanism: which decision each problem makes from the prediction |
| `paging_v1.py` | the per-page attachment, against the step-common one it replaces |
| `sufficiency_v1.py` | the scalar-insufficiency witness and the object-level contrast design |
| `external_cell_v1.py` | the committed external cell anchored to the published system result |
| `external_cell_mutation_v1.py` | the cell's check-liveness control (13 mutations) |
| `freeze_check_v1.py` | the design-freeze document against the artefacts (46 checks) |
| `canonical_results.json` | the aggregate: stages, criteria, claims, limits, and every recomputed fact with its rule and source |
| `design_freeze_v1.md` | what the study claims, and the limits each claim carries |
| `run.log` | the transcript of the last `canonical_runner.py` run |
