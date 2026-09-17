# Issue #42 - reproduction package

**When Does Another Check Help? Failure-Mode Alignment Sets the Marginal Value of a
Supervision Layer**

Contribution level: **theory + empirics**.

This directory is the committed artefact set for issue #42: a formal construct (the residual
catch profile and the redundancy dial), a derived boundary law, four instruments, the artefacts
they produce, the calibration dossier with its evidence, a 54-check validation suite, two
integrity checkers, the figure generator and the citation-authenticity report.

## One-command reproduction

    working directory:  papers/issue-42        (the package root - run it from there)
    command:            bash reproduce.sh

Expected output (tail):

    == 2. compare produced artefacts with committed ones ==
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

**Tolerance: exact, not statistical.** Every headline quantity is a deterministic function of a
fixed seed scheme, so there is no tolerance band to choose. The comparison step canonicalises
(sorted keys, parsed JSON) because key order is not part of a value.

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
only (everything else is the standard library). `make_figures.py` additionally needs
`matplotlib`, which is **not** required by `reproduce.sh`. `reproduce.sh` selects an interpreter
that can import numpy and fails with an explicit message if none can.

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
| `reproduce.sh` | the one command |
| `refs_build_display.py` | builds `artefacts/refs_display.json` (authors in `Family, I.` form, year, title, venue, resolvable URL) from `artefacts/refs_ordered.json`; `--check` compares the committed file with a fresh build and is a step of `reproduce.sh` |
| `refs_render.py` | renders the manuscript's `## References` section in the house style (authors — `(year)` — title — venue — resolvable URL — closing `Difference:`, one blank line between entries); `--check` verifies the committed section against a fresh render and is a step of `reproduce.sh` |
| `refs_differences.json` | the **authored** one-line stated difference for each of the 117 entries (correction round 1, required change 2) |
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
