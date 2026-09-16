# Issue #47 — What Does a Prediction Buy? A Signed-Error Decomposition

Reproduction package for the manuscript in this directory. Every number the paper cites is
**recomputed** from the stage artefacts' primitives by `canonical_runner.py`, and each recomputed
value is cross-checked against the value the stage recorded about itself. No number is typed into
the prose.

## Reproduce

```bash
bash reproduce.sh
```

Runtime is about five minutes on one CPU core, and **no wall-clock tolerance is claimed**: the runtime
is a coordinate of the machine that ran it — and of what else that machine was doing — not a result the
package asserts, so the check is on the printed verdicts of the eleven-step run below and on every
*measurement* the run reports, never on how long it took.
**Dependencies: the Python standard library only** — no
numpy, no scipy, no network, no `matplotlib`. Python 3.8+.

The verdict of every step, and the exit status:

```
criteria: a=MET, b=MET, c=MET, d=MET
facts recomputed: 113 | disagreeing with the artefact's own value: 0
coordinate census: 0 violation(s)
  stages and aggregate: OK
  aggregate liveness: OK
  external-cell check liveness: OK
  design freeze: OK
  manuscript assembly: OK
  support limb: OK
  journal reference gate: OK
  flip bound: OK
  flip bound liveness: OK
  README figures: OK
  README figure liveness: OK
  manuscript typed counts: OK
  manuscript typed counts liveness: OK
verdict: OK
REPRODUCE: ALL GREEN
```

Criterion (c) was **UNMET by design of the record, not by failure of the run** in the first
submission of this package: the registered measurement needed a certificate-chosen λ, and no stage
computed that formula — the package reported the state rather than substitute a proxy whose own
direction contradicted the registered one. The stage `lambda_cert_v1.py` (added by the **F0b
amendment** to the design freeze) now computes it, and the runner recomputes every number quoted
from the per-profile primitives, so (c) is **MEASURED**: a factor per problem — median 1.7006
(ski), 1.2851 (sched), 1.4934 (paging), worst profile 1.8252 with a 95% between-stream interval
[1.8109, 1.8404] — with the same factor under an out-of-sample λ* agreeing to 0.01–0.04.

The registered prior **P2 is half confirmed**, and the criterion's detail says so: the tail profiles
carry the higher mean factor in all three problems, but the correlations are weak (0.17 / 0.30 /
0.39) and the relation is non-monotone in spread — in `ski` the extreme-spread profiles carry the
*lowest* factor. `canonical_results.json → criteria` carries the same statement, per problem.

Step 10 prints the sha256 of every artefact the package ships, as a block to copy: **a digest quoted
in a report is read off that output, never typed.** Step 7 runs the journal's own reference gate
(`.github/tools/refgate.py`) on the assembled manuscript from the repository root — expected output
at this head: `156` entries in one `## References` section, `coverage=100.0%`, `GATE: PASS`, the
same block `reference-check.md` reproduces from running that tool. If the package is read outside the
repository the step is **skipped with that reason printed**, never silently omitted: the gate lives in
the journal, and a package that pretended to run it would be claiming a reading it did not take.

## The two citation relations, and which limb is checked here

A citation owes **two** relations, and only one of them can be read in the list:

| relation | what it asks | read where |
|---|---|---|
| **identity** | is the record the work the entry names? | `refs_resolve_v1.py` (research workspace): the returned year / venue / authors against the entry's own line. Needs the network, so it is *reported* in `reference-check.md`, not re-run by `reproduce.sh`. |
| **support** | can that work carry the claim at its in-text key? | `support_read_v1.py --check` (this directory, offline, step 6 above): the sentence each key sits in, against a recorded read. |

The support limb is read **per occurrence, not per key**: 156 keys appear as 237 occurrences, and 58
keys are cited in more than one sentence, so a per-key read would hide the occurrence that fails. A
row is identified by the text (part, key, digest of the sentence) and never by a line number: an
earlier version keyed rows by `part:line:key`, and inserting one sentence then re-keyed every row
below it -- 41 bound rows went stale, which is an instrument defect and not a finding.

`support-read.md` is the report, including the four occurrences where the read found that the work
**could not** carry its sentence (an exactness claim resting on three competitive analyses; a
structural-equation sample-size app cited for cluster-level MDEs; five asymmetric-loss papers cited
for a claim about guarantees; a theory bound listed among systems measurements). Each was corrected
in the manuscript, and the record of the finding is kept: a corrected finding that leaves no trace is
indistinguishable from one that was never made.

## The entry style: a resolvable link and a one-line stated difference

The journal's presentation requirement (Ops R334) asks every entry in the reference list to carry a
**one-line stated difference**, read as a `Difference` marker following the entry's last link token.
It is a requirement nothing in the journal's tooling can see -- `refgate.py` reads the count and the
in-text coverage, never the entry's style -- so this package reads it itself, in three places:

* **authored per work** in `research/refs_differences_v1.json` (156 lines). Each names what that work
  does and what it does not do relative to this paper; a work with no line makes the resolver
  **refuse to render the entry** rather than emit one without the element;
* **rendered** into `references.md` after a resolvable link (`https://doi.org/...` or
  `https://arxiv.org/abs/...`, built from the locator the entry names);
* **measured** in `reference-check.md` (`rendered entries carrying the stated difference: 156 of
  156`, read by that instrument), and **checked again at the manuscript** by `assemble.py`, which
  fails if any cited entry does not carry it -- the report is not the artefact a reviewer opens, and
  a green report over a manuscript that dropped the element is exactly the mismatch this package was
  bitten by twice.

## The flip bound: the sensitivity the registration promises per headline number

The registration's fourth success criterion asks a *flip count* per headline number — how many of the
observations a number rests on would have to change for its **verdict** to reverse — and through R346
no stage computed it (the manuscript said so in as many words). `flip_bound_v1.py` (step 8, offline)
computes it from the committed stage artefacts, into `flip_bound_v1_results.json`:

| rule | what it fixes | where it is read |
|---|---|---|
| the **unit** is the smallest observation the producing stage records | a bound in blocks, clusters, profiles or pairs is in units OF that number, never in a convenient unit | `unit` per headline |
| a unit is **inverted** by giving its contribution the mirror value, strongest-support-first | the number reported is the **fewest** changes that could reverse the verdict, so the verdict survives any change to fewer units | `k_inversions` |
| a verdict that asserts an **absence** gets no inversion count | only *more* support moves an absence across, so its margin is the distance to the decision boundary — an inversion count for it would be a made-up number | `distance_to_boundary` |
| an aggregate keeps no units | where the stage stored only a cluster mean and its interval, the bound is an ESTIMATE under a stated assumption and says so; the one headline whose per-unit rows were never recorded is reported as **not derivable** rather than estimated | `kind` |

Expected output at this head (the instrument's own lines are in `run.log`): the witness's count form
needs **12** block inversions (≥ **108** paired observations) while its aggregate-interval form needs
**2**; scheduling's sign-channel contrast is reversed by **25** cluster inversions (an estimate) and
paging / ski rental carry **absence** verdicts at **1.03** and **0.52** cluster MDEs below the bar; the
external ordering needs **39 / 32 / 29** pair inversions; the external reach is the weakest headline —
no profile reaches the published scale, and one would. Its own `--selftest` plants each rule in both
directions (a count rule at, just below and just above its threshold; an interval that k inversions
reverse and k−1 leave standing; a verdict no inversion reverses; an absence verdict that must carry a
distance and no count; and the artefact on disk against a fresh computation).

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
  lambdacert   lambda_cert_v1.py                     6      0 yes
  ```

  The `lambdacert` row is the certificate stage added by the **F0b amendment**; on the `ski` profile
  `under_mid` its own control is what proves the stage's factor is not free — the runner mutates one
  profile's factor, one profile's λ, and the recorded median, and each mutation must be noticed
  (12 cases in all, 0 not noticed).

* **recomputation, not transcription** — 113 named facts are derived from primitives (the witness's
  exact-zero scalar identity, the argmin loss gap, the per-problem sign counts that carry the
  registered prior `P3`'s outcome, the resolved contrasts, the ordering taus **together with the pair
  counts and the bootstrap interval behind each**, the reach counts, and the calibration factor's
  medians, extremes, displaced counts and direction correlations). Where the artefact records the
  same quantity, the two must agree; **0 of 113 disagree**. Two conventions are named rather than assumed, because each is part of its rule: the
  factor is the mean of per-stream ratios (**not** the ratio of the two means, whose value is
  reported beside it so the difference is visible), and the median over an even profile count is the
  **upper** median the stage uses, not the average of the two central values;
* **liveness** — `canonical_runner.py --selftest` corrupts each recomputation's input in a throwaway
  copy and requires the change to be noticed, comparing against a baseline rather than against the
  recorded field. It distinguishes the two mechanisms: a corrupted *primitive* must move the
  recomputed value, while a corrupted *recorded* field moves nothing and must be caught by the
  cross-check. 12 cases, 0 not noticed;
* **the state word follows the evidence** — a criterion's `MEASURED`/`UNMET` state is checked
  against the stages that carry it: a criterion whose stages are present and green cannot be
  reported `unmet`, and one whose stages are absent cannot be reported `measured` (the mapping is
  declared in the runner, and criterion (d) is deliberately out of it — its evidence is the
  disjoint-stream design of the cells, not a stage). Without this rule the round-3 change to (c)
  would be a sentence rather than a consequence, and reverting the state while the certificate stage
  kept passing would be invisible; two mutations of a throwaway copy — state reverted, and stages
  replaced by a name that does not exist — each turn the run red naming the criterion;
* **coordinates** — a census over **every** `.py`/`.sh` file the package ships enumerates the eight ways an input can enter
  from outside the package, and requires the three that would make the evidence machine-dependent
  (git object, network, clock/entropy) to be **empty**. It is empty here because the censused
  detector tables are a banner-delimited **declaration span** — data, not code — asserted
  structurally, with the control that a read planted *outside* that span is still caught. An
  exclusion wider than the thing it excludes is the defect this discipline exists for.

Three further controls live in their own files and are run by `reproduce.sh`:

* `external_cell_mutation_v1.py` — **13 mutations** of the external cell, one per named check, each
  of which must make exactly that check fail and no other. This is the control that shows the cell's
  gates can fail at all;
* `freeze_check_v1.py` — **57 checks** re-deriving every number in `design_freeze_v1.md` from the
  artefacts, including its 8-row digest table;
* `manuscript_check_v1.py` — the **manuscript's** typed numbers, its section references and its
  roadmap, each against the artefact that owns it. This is the carrier the README check did not reach,
  and the one whose drift reached review twice: a step count of seven against the eleven the script
  prints, "46 checks" against the freeze check's 57, and a roadmap pointing one section past its
  object. Its claims are read out of the **part files**, not out of the rendered `manuscript.md`,
  because the parts are what the next assembly reads; every section reference must resolve to a
  heading that exists; and the roadmap's sentences are matched against the headings they name. Nine
  claims, nine mutations, one per claim, each required to fail its own check and no other.
* `readme_check_v1.py` — **this file's own numbers**, each against the artefact that owns it: the
  facts and criterion states against `canonical_results.json`, the stage table against the one
  `run.log` printed, the freeze and mutation counts against their result files, the support
  counts against the verdict rows, the stated-difference count against `reference-check.md` and
  `references.md`, the step count against `reproduce.sh` itself, and the census's source-file
  count against the directory. `--selftest` plants one wrong figure per check and requires that
  check -- and only that check -- to fail. A count in a README is a claim about an artefact; if
  nothing reads it against that artefact it drifts, and this file's did (three figures quoted a
  tree two rounds old).

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
| `lambda_cert_v1.py` | the certificate stage of the F0b amendment: the rule λ_wc(η) and the calibration factor (c) |
| `lambda_cert_v1_results.json` | its artefact: the per-profile factors, intervals, λs and direction statistics |
| `external_cell_mutation_v1.py` | the cell's check-liveness control (13 mutations) |
| `freeze_check_v1.py` | the design-freeze document against the artefacts (57 checks, the F0b amendment included) |
| `manuscript_check_v1.py` | the manuscript's typed numbers, section references and roadmap against the artefacts that own them (9 checks, 9 mutations) |
| `readme_check_v1.py` | the README's own numbers against the artefacts that own them (13 checks, 13 mutations) |
| `canonical_results.json` | the aggregate: stages, criteria, claims, limits, and every recomputed fact with its rule and source |
| `design_freeze_v1.md` | what the study claims, and the limits each claim carries |
| `run.log` | the transcript of the last `canonical_runner.py` run |
| `assemble.py` | assembles `manuscript.md` from the part files: every measurement is a `{{ns:path}}` placeholder resolved out of the artefacts, the design table is rendered from `instrument_v0_results.json` rather than typed, and a citation key with no entry in `references.md` fails the step |
| `manuscript_part1.md` | section 1 (introduction) and section 2 (related work) |
| `manuscript_part2.md` | section 3 (instrument and design) and section 4 (results) |
| `manuscript.md` | the assembled manuscript — generated by `assemble.py`, never edited by hand |
| `references.md` | the reference layer's output: one rendered entry per cited key, from the record the resolver returned |
| `reference-check.md` | the citation report (the **identity** limb): one row per entry, with the verification method and the record it resolved to |
| `support_read_v1.py` | the **support** limb: the sentence at every citation occurrence against a recorded read; `--check` (offline, step 6), `--bind`, `--build`, `--selftest` (11 cases) |
| `support_verdicts_v1.json` | the readings: one row per occurrence, each quoting the sentence it was made on |
| `support_read_v1.json` / `support-read.md` | the support report, generated from the readings |
