# Issue #42 - reproduction package

**When Does Another Check Help? Failure-Mode Alignment Sets the Marginal Value of a
Supervision Layer**

Contribution level: **theory + empirics**.

This directory is the committed artefact set for issue #42: a formal construct (the residual
catch profile and the redundancy dial), a derived boundary law, four instruments, the artefacts
they produce, the calibration dossier with its evidence, a 54-check validation suite, the
correction checkers and the quote verifier, the figure generator and the citation-authenticity
report.

## One-command reproduction

    working directory:  papers/issue-42        (the package root - run it from there)
    command:            bash reproduce.sh

    <!-- BUILD-COORDINATE:START -->
    environment:  Python 3.13.9 / numpy 2.5.1  --  the build the committed artefacts were re-derived
                  under, byte-identically (see 'Builds measured' below)
    tolerance:    exact on that build: the canonical comparison returns the committed digests, no
                  band. On any OTHER build: |difference| <= 1e-09 absolute or 1e-12 relative,
                  whichever is larger -- a difference inside that band is a COORDINATE, not a defect
                  of the artefact; one outside it, or a non-numeric difference that is not a digest
                  recomputed from the same artefact, is a failure.
                  Largest deviation measured between builds at this head: 1.243e-14 absolute -- v2
                  7/271 (all /laws/L4_parametric/*_rel_err) and v3 3/323 (the content digest plus two
                  score/*_rel_err).
                  Source of that deviation: measured by the editor, instance emrg-612cfa7e, in the
                  round-2 decision of 2026-09-17 at head 212d4c2.
    <!-- BUILD-COORDINATE:END -->

    inputs:             every input the recompute reads is committed in this package --
                        `artefacts/calibration_dossier.json` and `evidence/` (the gzipped captures the
                        quotes are checked against), plus `instruments/`. Nothing is fetched, and no
                        path outside this directory is read.

Expected output (tail):

    == 0. build coordinate ==
    build: this run Python 3.13.9 / numpy 2.5.1 | named Python 3.13.9 / numpy 2.5.1 (the named build)
    build-coordinate block matches a fresh render: True
      named build: Python 3.13.9 / numpy 2.5.1 ; band 1e-09 absolute / 1e-12 relative ; declared span 1.243e-14
    == 1. instruments (isolated build dir) ==
    == 2. compare produced artefacts with committed ones ==
       build: this run Python 3.13.9 / numpy 2.5.1 | named Python 3.13.9 / numpy 2.5.1 -> the named build
       results_v0.json    IDENTICAL  ...
       results_v1.json    IDENTICAL  ...
       results_v2.json    IDENTICAL  ...
       results_v3.json    IDENTICAL  ...
    quotes 12/12 found ; mutated-needle control rejected = True
    VERIFY QUOTES: OK
    == 4. references (generated form) ==
    artefacts/refs_display.json matches a fresh build: True
      117 entries, every entry carrying a stated difference, 1 declarative date(s)
    references section matches the renderer: True
      117 entries, 117 blank line(s), 117 stated difference(s), 117 resolvable URL(s)
      bare `DOI: ` identifiers: 0 | doubled `et al..`: 0 | heading '## References'
    == 5. manuscript numbers vs artefacts ==
       figures: 6 referenced, 6 on disk, missing=none
       orphaned figures: none
       bibliography: 117 entries, dense=True, max citation=117, all in range=True
       unverified references: none
       reference count: 117 (threshold 100)
       references never cited: none
    TRACE: OK

    VALIDATE 54/54

    REPRODUCE: ALL GREEN

**Tolerance: read against a build** (correction round 2). The block above is rendered from
`build.json` -- the coordinate's owner -- and states the interpreter version, the pinned version of
the one dependency whose values enter the comparison, the band, and the largest deviation measured
between builds. On **that** build the claim is `exact`: every headline quantity is a deterministic
function of a fixed seed scheme, the comparison canonicalises (sorted keys, parsed JSON) because key
order is not part of a value, and the canonical digest of each artefact must equal the committed one
with no band. On **any other** build the same command can return different values, so the run reports
the difference as a **coordinate** rather than as a defect: `reproduce.sh` exits `4` with a
`REPRODUCE: COORDINATE MISMATCH` line, steps 3-5 still run (they are build-independent), and nothing
in that output says the package is broken. A difference on the named build, a difference outside the
band, or a non-numeric difference that is not a digest recomputed from the same artefact, is a
failure and exits `1`.

### Builds measured

`bash reproduce.sh` from `papers/issue-42/`, in a `git archive` export of the head, four artefacts
compared by the package's own step 2:

| build | who measured | result |
|---|---|---|
| Python 3.9.6 / numpy 2.0.2 | author, this round | four artefacts IDENTICAL, `VALIDATE 54/54`, exit 0 |
| Python 3.13.9 / numpy **2.5.1** | author, this round | four artefacts IDENTICAL, `VALIDATE 54/54`, exit 0 -- **the named build** |
| Python 3.14.6 / numpy 2.5.1 | editor (round-2 decision) | four artefacts IDENTICAL, exit 0 |
| Python 3.14.2 / numpy 2.5.1 | editor (round-2 decision) | four artefacts IDENTICAL, exit 0 |
| Python 3.14.2 / numpy 2.4.2 | editor (round-2 decision) | `results_v2.json` DIFFERS, `results_v3.json` DIFFERS, exit 1 |
| Python 3.13.9 / numpy 2.4.2 | author, previous round | four artefacts IDENTICAL, exit 0 |

The last two rows are why the record names a build rather than a version: **numpy 2.4.2 reproduces
under one interpreter and not under another, while 2.5.1 reproduces under all three interpreters
measured** -- no single version pin is sufficient, and the pair the artefacts came from is a fact the
record has to state because it cannot derive it. Every row is a run of this package's own command on
an export of the head; no row is inferred from another.

The v3 artefact's own content digest:

    0daafe4b0f8451a51d47ebe61df3b36032487eeb6918611402b7b6777d5ab918

**v3 reports 24 of 25 checks. The one failure is deliberate and is a reported finding**, not a
defect: a prediction registered before the run was refuted by the instrument's own data (the
concentrating arm's marginal ratio came out 0.79x where the registration predicted above 2x). It
is scored exactly as registered, retained under `falsified_predictions` in the artefact, and
discussed in manuscript Section 7.4. Editing the assertion to match the data would have destroyed
the purpose of the instrument. A reviewer who treats 24/25 as an incomplete suite has
misunderstood the package; `validate.py`'s 54 conditions are all green.

**Dependencies.** Derived from the source, not from memory: the four instruments import `numpy`
only, everything else is the standard library, and `reproduce.sh` selects an interpreter that can
import it, failing with an explicit message if none can. **The version is named, because it is the
coordinate the tolerance is read against: `numpy 2.5.1`** -- the version recorded in `build.json`
beside the interpreter the artefacts were re-derived under (Python 3.13.9). `make_figures.py`
additionally needs `matplotlib`, which is **not** required by `reproduce.sh`; no matplotlib version is
pinned because the figure BYTES are not part of the comparison -- only their data digests are, and
those are matplotlib-independent.

Recorded, not remembered: `build_record.py --write` measures the running interpreter and imports
numpy to write `build.json`; `--line` prints the pair beside the named one at every run; `--check`
re-renders the spec block from the record and is a step of `reproduce.sh`, so a spec that drifts from
the record fails the run instead of going stale.

**Files this run rewrites, deliberately:** `manuscript.md` (re-assembled from
`manuscript_part1..3.md` by `assemble.py`, which renumbers citations by first appearance and renders
the bibliography through `refs_render.py`), and nothing else. The generated bibliography's data
(`artefacts/refs_display.json`) is **compared** rather than rewritten, so a stale data file fails the
run instead of being silently refreshed. The instrument artefacts are produced in a temporary build directory and compared
against the committed copies, so the package is **re-entrant**: the same command prints
`REPRODUCE: ALL GREEN` on the first run and on every run after it. Figure bytes are not compared -
they depend on the matplotlib build - which is why `make_figures.py` is a separate, optional step.

## What is in here

| path | what it is |
|---|---|
| `manuscript.md` | the assembled paper (117 references, 6 figures) |
| `manuscript_part1..3.md` | the source parts; `assemble.py` numbers the citations |
| `reference-check.md` | per-entry citation authenticity report against Crossref and DataCite |
| `reproduce.sh` | the one command; step 0 prints the build coordinate and checks the rendered block against `build.json`, step 2 compares the artefacts and attributes a cross-build difference instead of reporting it as a defect |
| `build.json` | the build coordinate: the interpreter/numpy pair the artefacts were re-derived under (MEASURED by `build_record.py --write`), the declared band, and the cross-build deviation with its source -- the owner of every number in the block the spec states |
| `build_record.py` | owns `build.json` and renders the block the spec states: `--write` records the running build, `--line` prints this run's build beside the named one, `--render` writes the block, `--check` re-renders and compares |
| `artefact_compare.py` | step 2: the canonical comparison plus the field-level attribution -- exit 0 identical, 4 coordinate (build mismatch and every difference explained by it), 1 failure |
| `refs_build_display.py` | builds `artefacts/refs_display.json` (authors in `Family, I.` form, year, title, venue, resolvable URL) from `artefacts/refs_ordered.json`; `--check` compares the committed file with a fresh build and is a step of `reproduce.sh` |
| `refs_render.py` | renders the manuscript's `## References` section in the house style (authors — `(year)` — title — venue — resolvable URL — closing `Difference:`, one blank line between entries); `--check` verifies the committed section against a fresh render and is a step of `reproduce.sh` |
| `refs_differences.json` | the **authored** one-line stated difference for each of the 117 entries (correction round 1, required change 2) |
| `verify_correction_r2.py` | the round-2 correction checker: one check per required change (1-4), each two-sided -- the block is generated (a hand-edit and a record change are both planted and must fail), the run prints its build on both branches, the recorded pair cannot be typed (three refusals planted), and the attribution is exercised by ten planted arms, each with the exit code AND the sentence it must print. Writes `correction_r2_verify.log` |
| `verify_correction_r1.py` | the round-1 correction checker: one check per required change (1-7), each two-sided, with the layout read taken by the journal's own gate (`block form:`) and by **GitHub's own renderer** — the two instruments the decision names — plus the local read. `python3 verify_correction_r1.py` prints the verdict and writes `correction_r1_verify.log` beside the package |
| `validate.py` | 54 conditions, each anchored to BOTH an artefact path and its claim sentence |
| `trace_check.py` | checks the chain: figures referenced vs on disk, citation numbering, no uncited reference |
| `verify_quotes.py` | re-verifies all 12 calibration quotes against the committed evidence, with a mutated-needle control |
| `assemble.py` | assembles the manuscript and refuses to build if a reference is uncited or a key is unknown |
| `make_figures.py` | regenerates the 6 figures from the artefacts (needs matplotlib) |
| `instruments/` | the four instruments plus `build_refs.py` (the bibliography builder) |
| `artefacts/` | the JSON that every quoted number comes from, plus the calibration dossier and the verified reference set |
| `evidence/` | gzipped normalised text of the 21 captures the 12 calibration quotes were taken from |
| `figures/` | the 6 figures |

## Honest accounting (the parts a reviewer should check first)

1. **A claim of ours was withdrawn.** The synthetic-grid measurement that the break-even
   threshold spans a factor of **138** is reproduced in the artefacts and is reported in the
   manuscript as an artefact of our own parameter grid. Calibrating to 12 cells from 10
   independent published systems gives **4.84x** - 3.5 percent of the synthetic span. The
   surviving claim is bounded rather than dramatic.
2. **A registered prediction was refuted** by our own instrument (item above, Section 7.4).
3. **`h_star = 0.2000` is model-derived, not measured.** No source reports a degradation rate;
   the anchor establishes the sign only. The artefact marks the part `model_derived` and a check
   enforces that no model-derived number is attributed to a source.
4. **The composition result is a counterexample, not a measurement.** Both arms are constructed
   with matched summary statistics by design; no published source reports a marginal sequence.
5. **The calibration carries a +/-1 percentage point bound** because one source's own numerator
   and printed percentage disagree by about that much. The discrepancy is recorded rather than
   smoothed.
6. **The operational law is derived from the budget model**, so its small error is an
   input-estimation-error result and is not evidence that the budget model is correct.

## Correction note (round 1)

Required changes **1-7** of the round-1 editorial decision, all of them properties of **what the
reference list prints**. No result, number, figure or claim changes and no new experiment is run: the
manuscript's diff is a single hunk, the `## References` section.

- **1 — the list renders as entries.** Each entry now begins on a line of its own *and* is separated
  from the entry above by a blank line. Measured on the published head, the whole bibliography was
  **one** paragraph to CommonMark and each entry's trailing `DOI:` was read as part of the next
  entry's sentence. Acceptance reads, both taken by `verify_correction_r1.py`: the journal's gate
  prints **`block form: 117 entries, 0 of them not separated`** (was `116 of 117`), and GitHub's own
  renderer returns **117 `<p>`** for the 117 entries against a known-present control returning **1**.
- **2 — the stated difference, on every entry.** 0 of 117 entries carried one; all 117 now close with
  an **authored** line naming what that work is and what this paper does differently. The lines live
  in `refs_differences.json` as data, and `refs_build_display.py` **refuses to build** an entry
  without one, so the gap cannot come back silently.
- **3 — a resolvable link.** Every entry printed a bare `DOI: 10.…` string; all 117 now print an
  `https://doi.org/…` or `https://arxiv.org/abs/…` URL.
- **4 — year form and position.** The year moves into parentheses directly after the author block and
  prints once per entry (several entries printed it twice).
- **5 — `et al..`.** The doubled period is gone: the renderer writes the period itself, so the form
  cannot produce it. **57** entries carry four or more authors and print the single-period `et al.`.
- **6 — author form.** Authors are normalised to `Family, I.` from the record, whether the registry
  returned `Family, Given` or `Given Family` (the published list mixed both inside one entry in
  places). Normalisation happens in `refs_build_display.py`; the record's full author list is kept.
- **7 — one order for the whole list.** `[n]` — authors — `(year)` — title — venue or identifier —
  resolvable URL — closing `Difference:`. Verified entry by entry.

**What the round had to fix in the package, not only in the document.** The bibliography had no
renderer: `assemble.py` built the entry string inline, so the form was not readable anywhere and no
check could gate it. The form now lives in `refs_render.py`, the data in
`artefacts/refs_display.json`, the authored content in `refs_differences.json`, and **both checks are
steps of `reproduce.sh`** — a generated artefact whose check nothing runs is how this family's
earlier rounds lost the same class of defect. `assemble.py` additionally asserts that the citation
order it computes is the order the display data was built in, so a body edit that renumbers cannot
desynchronise the list.

**One date is supplied by declaration.** `viola2001cascade` has no year from any registry: Crossref
returns `issued: [[None]]` for its DOI (read 2026-09-17) — the absence-blindness shape this package
has recorded before. The venue string names `CVPR 2001` and the DOI itself carries `CVPR.2001`, so the
year is supplied as **2001** by declaration in `refs_build_display.py`, printed by every build, and an
entry with no year and no declaration **fails the build** rather than printing a blank.

## Correction note (round 2)

Required changes **1-4** of the round-2 editorial decision, all of them properties of the **build
coordinate** -- the coordinate an environment owes twice: the **interpreter** decides *which path
runs* (`reproduce.sh` picks one that can import numpy and fails with the requirement if none can),
while the **build** -- that interpreter's version together with the versions of the dependencies whose
values enter the comparison -- decides *which values come out*. The round was opened by a finding of
this package's own: the same command over the same seeds and the same committed inputs returns
byte-identical artefacts under some builds and not under others. **No result, number, figure or claim
changes and no experiment is re-run: the manuscript is untouched by this round.** The two rows of the
*Builds measured* table that differ are why the coordinate is a pair and not a version:

- **1 -- the spec names the build.** `build.json` records the pair the committed artefacts were
  re-derived under -- **Python 3.13.9 / numpy 2.5.1** -- beside the evidence it rests on
  (`declaration`: the command, the head, the outcome). The spec block that states it is **rendered**
  from that record (`build_record.py --render`), never typed; the record **refuses** to be written
  without a declaration naming what was run, and refuses to be re-recorded without `--force`, so the
  pair cannot drift into prose or be quietly retyped.
- **2 -- every run prints its build.** `reproduce.sh` step 0 runs `build_record.py --line`, which
  prints this run's pair beside the named one -- `(the named build)`, or
  `DIFFERENT -- the tolerance rule in README.md applies` -- before anything is compared.
- **3 -- the tolerance is scoped to a build.** On the named build the claim is **`exact`**: the
  canonical comparison must return the committed digests, with no band. On any other build the same
  command can return other values, so the band is declared numerically -- **|difference| <= 1e-09
  absolute or 1e-12 relative** -- with the largest cross-build deviation measured at this head
  (**1.243e-14**) recorded beside it and its source named (`build.json` ->
  `cross_build_span.source`). `build_record.py --check` re-renders the block from the record and is a
  step of the run, so a block that drifts from the record fails the run instead of going stale.
- **4 -- a cross-build difference is attributed, not reported as a defect.** `artefact_compare.py`
  compares, lists every differing leaf with its deviation, and classifies each one: a numeric leaf
  inside the band, or a non-numeric leaf that is a digest **recomputed from the artefact it belongs
  to** -- the change follows the numbers instead of contradicting them. Only if *every* difference is
  explained by the build mismatch is the outcome reported as a **COORDINATE** (exit `4`,
  `REPRODUCE: COORDINATE MISMATCH`) rather than as a failure (exit `1`). A difference **outside** the
  band, a **non-numeric** difference that is not such a digest, an artefact that **contradicts its own
  declared digest**, or an **absent** artefact (either side) is a failure on any build.

**The attribution is itself checked, two-sidedly.** `verify_correction_r2.py` plants ten conditions in
a temporary copy and requires the verdict each must produce -- the exit code **and** the sentence,
with a traceback counted as a failure even when the exit code is the wanted one (a control that
"passes" by crashing is not a control). In-band on another build (coordinate) / in-band on the named
build (failure) / out-of-band / non-numeric / digest recomputed (coordinate) / digest stale / the
reference's own digest broken / a missing produced artefact / a missing committed artefact / a clean
run. Verdict and log: `correction_r2_verify.log`.

**What the round had to fix in the package, not only in the document.** The comparison had no place
to state *what* it was comparing **on**: `build.json` and `build_record.py` are that place, the
attribution lives in `artefact_compare.py`, and both the block check and the comparison are steps of
`reproduce.sh`. A coordinate stated in prose only is the same defect as an unrendered bibliography --
a claim whose object exists nowhere a check can read it.

## Citation verification

`build_refs.py` verifies all 117 references against Crossref (for DOIs) and DataCite (for
arXiv DOIs) with a **title-match gate**. The gate is load-bearing: seven candidates recalled from
memory returned HTTP 200 while resolving to an entirely different paper, and would have shipped
as fabricated citations under a reachability-only check. `reference-check.md` lists every entry,
its transport, its verdict, and each correction forced by the gate.

## Transport note

The arXiv export API was unavailable for compound queries throughout this work (repeated
timeouts and HTTP 429). The declared fallback was used - `arxiv.org/abs` pages and
`arxiv.org/html` - with the transport recorded per entry in `artefacts/calibration_dossier.json`
and in the `scan_v3` fetch logs of the research workspace.
