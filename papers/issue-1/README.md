# Issue #1 - reproduction package

**When Should an Agent Retrieve Instead of Read? A Controlled Phase Map of
Evidence Access under Semantic Interference**

This directory is the committed artefact set for issue #1: the sweep runner, the
derivation and analysis scripts, the figures, the result table, a frozen snapshot of the
reader-fidelity corpus, a 38-check validation suite, and a 37-check manuscript-consistency
gate. Every number that appears in
`manuscript.md` is read out of `canonical_results.json`, which this package
regenerates from scratch and validates. Seven independent full runs of this pipeline produced a byte-identical artefact, the four most
recent through the entry point documented below after a metadata correction (see *Reproduction status*).

## One-command reproduction

    working directory:  papers/issue-1        (the package root - run it from there)
    environment:        see "Environment" below - it decides which tier runs
    command:            bash reproduce.sh

Expected output (light tier, default environment):

    canonical payload sha256: e801274596d9b662
    VALIDATE 38/38
    CONSISTENCY 37/37
    RESULT: PASS | wall-clock <seconds> s

Full artefact payload sha256:

    e801274596d9b6621ccfd074ddd768ea76ddca426c4d253832efb0a08b1df5eb

The first three lines are the values a verifier compares; `wall-clock` is machine-dependent
and is stated separately under *Measured wall-clock* below.

**The command is re-entrant: it prints `RESULT: PASS` on the first run and on every run after it, over the
same copy.** It rewrites the figures, `figures/manifest.json` and `run.log`, and no check compares those files to
a static record, so a second invocation sees the same verdict as the first.

**Tolerance: exact, not statistical.** `validate.py` must print `VALIDATE 38/38`;
it asserts 38 individual conditions (16 structural, 22 mechanism), each attached to a
specific headline claim in the manuscript. `consistency_check.py` must print
`CONSISTENCY 37/37`, which it does by re-deriving from the artefact every number the
manuscript quotes (see *Traceability* below). The three figures and the result table must
match the sha256 values recorded in `figures/manifest.json` byte for byte. A single
mismatched byte, or a single failed assertion, fails the run.

**Measured wall-clock** (Apple silicon, no GPU, both measured by the script itself):

| tier | total | breakdown |
|---|---|---|
| **heavy** (recomputes the experiment) | **830 s** | fidelity gate 15 s, 84-cell sweep and derivation 814 s, figures 1 s, validation 0 s |
| **light** (validates the committed artefact) | **0.8 s** | figures 0 s, validation 0 s |

The script prints its own wall-clock and writes `run.log` next to itself, naming the tier,
the interpreters it selected, and the timings it observed.

### Environment

**The environment is not a detail: it decides which tier runs.** Read this before you run the command,
because in a default environment you get the light (validating) path and a green message even when the
recompute path was never attempted.

| tier | interpreter | what it selects |
|---|---|---|
| light (validate + redraw figures) | any Python 3 with matplotlib; this package was verified on `/usr/bin/python3` | the default path, taken whenever no torch interpreter is supplied |
| heavy (**the recompute**) | a Python with torch and numpy, supplied through the `EMRG_PYTHON` variable | the path that re-runs the experiment |

**The exact command that produced the committed artefact**, run from `papers/issue-1/`:

```
EMRG_PYTHON=/path/to/python-with-torch bash reproduce.sh
```

**Versions this package was verified against** (the environment the reproduction status below refers to):

| component | version | used by |
|---|---|---|
| Python | 3.12.12 | heavy tier |
| torch | 2.9.1 | heavy tier |
| numpy | 2.5.2 | heavy tier |
| Python | 3.9.6 | light tier |
| matplotlib | 3.9.4 (Agg backend) | figures, both tiers |

`reproduce.sh` probes each candidate interpreter for the module it needs (`import torch`, `import
matplotlib`) and reports which ones it selected as its first output lines, so the tier actually taken is
visible in the run rather than inferred. If the heavy interpreter is not supplied, the script prints the
line `PyTorch was not found, so the sweep is NOT recomputed` and the command you just ran was a package
integrity check, not a reproduction.

**Check an interpreter before you rely on it:**

```
/path/to/python -c "import torch, numpy; print(torch.__version__, numpy.__version__)"
```

**If you have no such interpreter.** Construct one - `reproduce.sh` finds it without any
variable, because it probes `.venv/bin/python` at the package root by name:

```
python3 -m venv .venv
./.venv/bin/pip install "torch==2.9.1" "numpy==2.5.2"    # needs PyPI access
```

Two caveats, both stated below and both loud rather than silent. The install needs network
access to PyPI, which the authoring machine did not have - that is why the committed artefact
was produced through an existing local environment passed in `EMRG_PYTHON` instead of this
recipe. And the heavy tier additionally loads the two model snapshots listed under
*Dependencies and model snapshots* from the local HuggingFace cache, failing loudly if either
is absent. The probes accept any interpreter that can import the modules, and the
reader-fidelity gate re-verifies the port before any reported number is produced, so the pins
above describe the verified environment rather than gating a run.

## Two tiers: what each one recomputes

**What the command recomputes matters, so it is stated tier by tier.**

| tier | runs in a plain environment? | what it **recomputes** | what it only **validates** |
|---|---|---|---|
| **heavy** | no - needs PyTorch + numpy and the two model snapshots | everything: the reader-fidelity gate, all 84 sweep cells from the corpus definitions, the whole derivation, then rewrites `canonical_results.json` | nothing |
| **light** | yes - needs only Python 3 + matplotlib | the three figures and the result table, from the committed artefact | everything else: checksums, structural consistency, all 38 assertions (16 structural, 22 mechanism), and the 37-check manuscript-to-artefact consistency gate |

**The light tier is a package-integrity check, not a reproduction.** It confirms that the
committed artefact is internally consistent, that its embedded payload hash recomputes, and
that every headline number the manuscript quotes traces back to that artefact (`CONSISTENCY 37/37`) - but the
sweep cells it checks were produced by the heavy tier, so it cannot stand as the reproduction
by itself. The heavy tier is the reproduction. **Run the heavy tier to reproduce this work**;
run the light tier to check that the package you have is intact.

Run the heavy tier with:

    EMRG_PYTHON=/path/to/python-with-torch bash reproduce.sh

Any interpreter with `torch` and `numpy` works; check a candidate with
`/path/to/python -c "import torch, numpy"`. If neither tier can be run in your environment,
the light tier's output still tells you the committed artefact is self-consistent, but no
number in this package has then been recomputed on your machine - say so if you cite it.

**Metadata correction.** The artefact and the package scripts previously carried the retired-lineage
label `issue 100` in a provenance field and in docstrings, which mismatched this submission's number.
The label was corrected to `issue 1` before the manuscript was written, and the heavy tier was then run
three times more; all three runs are byte-identical to each other and to the committed file. The three earlier runs
refer to the same code with only that constant differing.

**Reproduction status.** The heavy tier **has** been run end to end through this exact entry
point: 820 s wall-clock, `VALIDATE 38/38`, `CONSISTENCY 37/37`, and the rewritten `canonical_results.json`
byte-identical to the committed file (`cmp` reports no difference; file sha256
`69960d951cfaa2231152932515feadbc984f0a9f3acf596d5387ddf305df712c`, payload sha256
`e801274596d9b6621ccfd074ddd768ea...`). The figures and `results_table.md` were rewritten by the same
run and are byte-identical too. **This artefact has been produced four times - once by
`canonical_runner.py` and three times through `reproduce.sh` - and all four are byte-identical**; the second was
the pre-revision package's, and the fourth is the heavy-tier run described above (the revision-round-2 runs are
light-tier: they validate the artefact rather than recomputing it). The earlier 48-cell artefact
that the first submission carried went through
seven full runs, likewise byte-identical, before the revision replaced it; its two hashes were
file `de241d916e5885a82a6ecea8f258a2b47705b546f89c427e49dec9cc0d303a6e`
(payload `8dc43a9cc1d0a981`), superseded on 2026-09-12 and recorded here as provenance only.
The most recent heavy-tier run was made after the consistency gate was added, so it is also the run that
exercised `consistency_check.py` on the recompute path (`CONSISTENCY 37/37`).
`run.log` is the record of the most recent run and names its own tier: after the revision-round-2 edits it is a
**light-tier** run (the authoring machine has no PyTorch, so the sweep was not recomputed), with its per-step
timings, and it prints `VALIDATE 38/38` and `CONSISTENCY 37/37`.

## Revision round 1: what changed in the package

This package was revised in response to the first review round (issue #1, `major-revision`). Four
changes, all of which moved the *evidence*, not just the prose:

1. **Per-rung 95% intervals** (`gap_ci_by_interference`): the interference ladder now carries an
   interval for every rung, computed over that rung's six cells. The zero-interference rung's interval
   contains zero, and the manuscript now states the two arms are indistinguishable there rather than
   that retrieval leads.
2. **The full budget ladder** (`budget_ladder`): k = 1, 2, 4 and 8 are all reported over the 30
   distractor cells. This corrected a claim - the deficit is *not* budget-invariant; it roughly halves
   from k = 1 to k = 8, and the manuscript now says so.
3. **A recall-matched control for the distractor-type contrast** (arms `TYPERM_status` / `TYPERM_entity`,
   derived as `type_contrast_recall_matched` and `type_contrast_matched_subset`): the original contrast
   compared a cell where the retriever returned the gold record against one where it did not. The
   control holds density, interference, instance and length fixed and changes only the distractor
   family, and the reported comparison is restricted to pairs where **both** families keep the gold
   record inside the k = 4 set (12 of 36 control cells). At that match the contrast collapses from
   about +2 nats to **-0.155 nats** (paired 95% interval [-0.217, -0.092]), and the manuscript
   withdraws the discrimination-margin reading in favour of a rank/recall statement. Figure 2 now shows
   both the unmatched and the matched contrast side by side.
4. **Two numeric corrections**: the worst single cell is -1.926, not -1.226 (which is the I = 0.30
   rung mean), and the one 0.003-nat inversion of the oracle >= reading bracket is stated as rounding
   tolerance.

The sweep therefore grew from 48 to **84 cells**, which is why the cell-count assertions in `validate.py`
and the corresponding checks in `consistency_check.py` were updated, and why the gate now reports 37
checks where the first submission reported 21: eight checks cover the four claims above, and eight
more (C27-C34) hold the package's own specification to the artefact and the scripts it describes -
the class of drift a file-hash table cannot see, because the values live in prose a reader executes.

**Second correction to the same apparatus (R286).** C27's first version compared the README's hash
rows against the working tree, which the run itself rewrites one step earlier: `make_figures.py`
redraws the three PNGs and `figures/manifest.json`, and `run.log` is written *after* the consistency
step. So the command passed on a first run and failed on a second over the same copy, and it failed
outright on a machine whose matplotlib is not the one this package was verified with. The corpus of
C27 is now the run-invariant files only, the five rewritten files state `*regenerated*`, C34 keeps
that set honest, and `check_audit.py` runs the documented command twice in its sandbox and fails
loudly if the two runs disagree. The property this restores is stated where a verifier will read it:
what the package promises is what a compliant run prints.

## Revision round 2: what changed in the package

The second review round asked for a consistency fix only - no new runs, no re-derived number -
because the package still carried two readings the paper had itself withdrawn: that retrieval leads
on the empty-distractor rung, and that the comparison is governed by a *discrimination margin*.

1. **The withdrawn sign is gone from every site.** The registered prediction - that retrieval
   overtakes reading above some interference threshold - does not appear, and the package now says
   so in one form everywhere: Section 1's headline summary, the Section 4.1 heading and opening,
   Figure 1's caption, the Section 4.2 table discussion, the P2 outcome in Section 5, and the
   Conclusion no longer attribute a lead to the zero-distractor rung. The rung is stated as what its
   interval supports: a **null** (+0.062 nats, 95% interval [-0.039, +0.163], cells split 3-3).
2. **One set of ahead-counts, each with its denominator.** The three counts are now stated once and
   identically - **3 of the 6** cells on the I = 0.00 rung, **2 of the 30** distractor cells (the
   five rungs from I = 0.15 upward), and **31 of 36** main-grid cells negative - and the table row
   names the denominator it divides by.
3. **The withdrawn reading is gone from the executed code and from the validator.** `make_figures.py`
   no longer annotates Figure 1 with "retrieval leads only here" and no longer reports the cell
   counts under that phrasing; `analyze6.py`'s printed conclusion no longer places a crossover at
   I = 0; and the two `validate.py` labels that named a lead and a crossover (B01, B04) now describe
   what they assert. Figure 1 and `figures/manifest.json` were regenerated together, since the
   manifest is the committed artefact that pins the pair.

   **One finding, reported rather than assumed away.** The review described that annotation as
   "baked into the committed PNG". It is not. The annotation's anchor point (I = 0.00 at +0.02 nats)
   lies outside the axes, whose y-range is [-2.058, -0.051], and `ax.annotate` with the default
   `annotation_clip=None` does not draw an annotation whose anchor is outside the axes. The control
   is exact: deleting the call entirely leaves Figure 1 **byte-identical** to the committed image,
   the same bytes it carried before this revision. So the visible figure never carried the withdrawn
   claim - the claim lived only in the source, where it is now corrected - and the regenerated
   Figure 1 and `figures/manifest.json` still agree (C18). Whether the corrected statement should now
   be made *visible* in the figure is a content change the review did not ask for, so it is left to
   the editor; the source states the corrected wording either way. The figure's other annotation
   ("reading wins (28 of 30 distractor cells)") does render and is correct.
4. **The sweep, counted.** Every statement resting on either withdrawn reading was enumerated and
   repaired: **twelve** edits in `manuscript.md`, **three** in the scripts the pipeline runs
   (`make_figures.py` twice, `analyze6.py` once), **two** check labels in `validate.py`, and **one**
   row in this README's figure table. The Section 6 threat paragraph that had already corrected the
   framing, and the sites that already stated the null, were left unchanged. **No number changed and
   no experiment was re-run.** Figure 1's two panel titles remain accurate under the corrected
   wording ("The comparison inverts at the interference boundary", "The deficit appears at once,
   then saturates"), so they were not retitled.

## Traceability: every manuscript number back to the artefact

The chain a number travels from the experiment to the manuscript is

    canonical_results.json  ->  make_figures.py  ->  results_table.md  ->  manuscript.md

and it is checked rather than asserted. `consistency_check.py` walks that chain in both
directions - it reads the committed artefact, the generated table, the figure manifest, the
bibliography record store and the manuscript - and prints `CONSISTENCY 37/37`. It uses only
the standard library, so it runs in either tier; `reproduce.sh` runs it as its last step in
both. What the 37 checks cover:

- the manuscript's header carries the artefact's payload sha256, and that hash recomputes from the artefact body (C01-C02);
- the 18 data rows of the manuscript's main table equal `results_table.md` byte for byte, and that file matches `figures/manifest.json` (C03-C04);
- every headline number the manuscript quotes - the six interference gaps, the three context-length budgets, the filler control, the five position fractions, the distractor-type contrasts, the dense pooled-recall ladder, the BM25 recall, the cell count, the sign test, every Wilson interval in the table, and the fidelity block - is present **anchored to the sentence that makes the claim**, not merely as digits somewhere in the file (C05-C14). Anchoring matters here: the manuscript carries 115 arXiv identifiers, so a bare substring test is satisfied by unrelated digits, which is exactly the failure the audit below finds and eliminates;
- the bibliography has exactly one section, its entry count equals the verified record store, and every entry is cited in the body - citation clusters such as `[18,19,20,21,22,23]` are counted as citing each of their members, the same resolution the repository's `refgate.py` applies (C15-C17);
- the committed figures match the hashes in the manifest (C18);
- **the package's own specification describes the package it ships (C27-C34)** - every file-hash
  row in the tables above matches the file on disk (C27, whose corpus is exactly the run-invariant
  files: the five files the run rewrites carry `*regenerated*` instead, and C34 requires that
  exclusion to name only files a package script really writes, so it cannot be used to retire a row
  that has drifted); no hash-like token appears in the
  specification that is not a current hash of a committed file or an explicitly labelled
  superseded one (C28, which is the check that sees prose, not tables); the expected-output block
  states the artefact's payload (C29); the reproduction-status paragraph quotes the committed
  file's own hash (C30); every sweep-cell count is the artefact's, unless the surrounding text
  marks it as historical (C31); the tally stated for `validate.py` is the tally `validate.py`
  actually asserts, measured by running it (C32); and every count stated for this gate is this
  gate's own check count, including the check that makes the comparison (C33). This family exists
  because the round-1 revision left seven stale values in exactly the documentation a reader
  executes, and the file-hash tables - the only thing being checked - could not see any of them.

The gate exits non-zero as soon as one number cannot be traced, so a manuscript edit that
outruns the artefact fails the same one-command reproduction that produces the artefact.

### Does every check earn its place? (`check_audit.py`)

A suite that reports `37/37` is evidence about the suite only if each check can be shown to
reject something; a check that never fires inflates the denominator without constraining the
artefact. `check_audit.py` tests that directly. For each check it applies one targeted
corruption to a throwaway copy of the package, runs the gate there, and records which checks
fail. The corruptions are surgical and each mutator asserts that it changed something, so a
silently ineffective corruption cannot be mistaken for a check that failed to fire.

```
python3 check_audit.py
AUDIT CLEAN - every one of the 37 checks rejects something
```

Current result: **37/37 checks load-bearing, 38/38 corruptions caught, no decoration, and 30
checks have a corruption that only they catch.** Seven corruptions trip more than one check, and
that overlap is expected rather than hidden, in three groups: C02 recomputes the artefact's
embedded payload hash, so any edit to the artefact body necessarily trips it beside whichever
check reads the mutated field (C02/C10/C12 share this); C27, C28 and C30 re-hash or re-read files
the documentation names, so they fire on any corruption that changes such a file (that is what
they are for - it is also why the audit had to be given a faithful copy of the package rather than
a partial one); and C03/C07 and C16/C17 are two views of one row and of one bibliography
respectively.

**Two properties the corruption matrix cannot express, run as separate cases.** A corruption is a
statement about one value in one file; the two failures this apparatus actually suffered were
statements about the *run*. Both are now cases in the same script, reported beside the matrix:

```
R1  ok  the documented command is re-entrant: same verdict on run 1 and run 2
        RESULT: PASS | wall-clock 0 s | RESULT: PASS | wall-clock 1 s
R2  ok  a consistent figure redraw (non-pinned matplotlib) still passes
        CONSISTENCY 37/37
```

**R1** executes `reproduce.sh` twice in the sandbox copy and requires the same verdict both times
- the command rewrites the figures, `figures/manifest.json` and `run.log`, and a documentation
check that reads the working tree would pass on a first run and fail on the second over the same
copy, which is exactly what the first revision of C27 did. **R2** emulates a machine whose
matplotlib is not the pinned build by changing a figure's bytes (inserting a real `tEXt` chunk, so
the file remains a valid image) and updating that figure's manifest entry exactly as
`make_figures.py` would: a consistent redraw must pass, because figure bytes are
interpreter-dependent by construction, while an *inconsistent* redraw must still fail C18 - which
is what the C18 corruption checks.

The audit is not decoration itself - it changed the gate. Its first run found that the four
per-rung recall tests (k=1,2,4,8) could not be made to fire independently: the exact
pooled-recall ladder phrase already pins all four values in one rendering, so the per-rung
tests were redundant. Three of them were removed and the stricter phrase test kept, which is
why this gate had 21 checks rather than 24 at the first submission. The same run showed that a value-presence test can
be satisfied by a colliding number elsewhere in the file, which is what motivated the anchored
form above. This is the standard the fidelity gate already met for the model port (three
corruptions that must degrade the metric, one that must improve it); `check_audit.py` applies
it to the manuscript-to-artefact chain.

## Dependencies and model snapshots

- **Light tier:** Python 3 with matplotlib (Agg backend). Nothing else.
- **Heavy tier:** additionally PyTorch and numpy, plus the two model snapshots the ports load:
  - reader: **SmolLM2-135M** (snapshot in the local HuggingFace cache of the authoring machine)
  - retriever: **all-MiniLM-L6-v2** embeddings (snapshot in the same cache)
  The ports load those snapshots from disk and **fail loudly** if either is absent; they
  never fall back silently to a random initialisation or to a network download, so a
  missing snapshot produces an error, not a plausible-looking wrong number. Both snapshots
  are already present in the machine's HuggingFace cache; a reader without that cache cannot
  run the heavy tier, and the failure is loud rather than silent.
- **Determinism:** sampled decoding uses four fixed seeds (101, 202, 303, 404) at
  temperature 0.7; no field of the artefact records wall-clock time, and `validate.py`
  asserts that no timing field is present anywhere in the JSON (check A02). Free-text
  generation is therefore reproducible byte for byte on the same model snapshot.

## What each file is

| file | sha256 (16 hex) | role |
|---|---|---|
| `reproduce.sh` | `0b8d09736139fcfa` | one-command entry point; picks interpreters, runs the tiers, writes `run.log` |
| `canonical_runner.py` | `6ae0667d242879ad` | single entry: fidelity gate, 84-cell sweep, derivation, artefact write |
| `eval_fidelity.py` | `8766fac036626e1e` | reader-fidelity gate over the frozen corpus; 12/12 checks plus a power check |
| `grid6.py` | `8e9106d588da2bc5` | the 84-cell grid definition and sweep driver, including the recall-matched control |
| `analyze6.py` | `c52b749c1b0bce12` | derivation: gaps, recall, Wilson intervals, position and type contrasts |
| `corpus5.py` | `bb6b3ec05fc59306` | builds the 12-document fidelity corpus and its train/eval split |
| `mini_port.py` | `1d8eee73ba250b60` | dependency-free transformer port (SmolLM2-135M) |
| `smollm_port.py` | `7309967e201e8acc` | reader wrapper: KV cache, greedy and sampled decoding |
| `validate.py` | `c5c21cec715316e0` | 38 assertions over the artefact; prints `VALIDATE 38/38` |
| `consistency_check.py` | `aa9e0b56ada63ca6` | 37 checks tracing every number in `manuscript.md` back to the artefact; prints `CONSISTENCY 37/37` |
| `check_audit.py` | `34cf4c1a41df5caf` | reversion audit of the gate: one targeted corruption per check, reporting which checks are load-bearing |
| `make_figures.py` | `5febdba1ea149c80` | regenerates the three figures and the result table from the artefact |
| `canonical_results.json` | `69960d951cfaa223` | the artefact: sweep, derivations, fidelity block, embedded payload sha256 |
| `fidelity_corpus.json` | `01e1d83b232acc68` | frozen text snapshot the fidelity gate reads (see below) |
| `results_table.md` | `3c3b21f35f40c6c5` | the result table embedded in the manuscript |
| `figures/manifest.json` | *regenerated* | figure/table sha256 values and every number plotted in them |
| `run.log` | *regenerated* | the log of the most recent run of this script, written by that run |
| `manuscript.md` | - | the manuscript; every number in it is read from `canonical_results.json` |
| `reference-check.md` | - | citation authenticity and coverage report (115 entries) |
| `refs_tool.py` | `bd4eadc8ab5af4d0` | bibliography builder: `harvest` (arXiv + Crossref search) and `verify` (re-fetch by identifier) |
| `refs_selected.json` | `1629a255f263f98b` | the curated selection (115 entries) with a stated difference for each |
| `references.json` | `636f838ee3980af0` | the verified record store; `reference-check.md` is generated from it |

**`*regenerated*` means the run rewrites the file, so a static hash row cannot hold.** Five files are in
that class: the three figures, `figures/manifest.json` and `run.log`. The figures are drawn by whichever
matplotlib the verifying machine has, and their PNG bytes differ between builds, so the package does not assert
what a run will print for them; `run.log` is by definition the log of the run that just happened, so a hash of it
is stale the moment the command it documents is executed. What replaces the hash row is a local, self-verifying
pair: the committed `figures/*.png` are pinned by the committed `figures/manifest.json`, and check C18 re-verifies
that pairing (figures against the manifest **as it stands in the tree you have**) on every run. The remaining rows
carry hashes and are asserted against the files on disk by **C27**, whose corpus is therefore exactly the set of
files a run does not rewrite; **C34** closes the loophole that would otherwise open here, by requiring every
hash-less row to name a file that a script in this package actually writes.

**Files the heavy tier writes but this package does not commit.** Running the heavy tier
leaves three further JSON files in this directory - `fidelity_results.json` (the gate's
output), `grid6_results.json` (the raw 84-cell sweep) and `grid6_analysis.json` (the
derivation's input); `canonical_runner.py` names them in that order. They are the pipeline's
intermediates, not part of the committed set: every number they carry is embedded in
`canonical_results.json`, which is what the manuscript, `validate.py` and `make_figures.py`
read. None of the three records wall-clock time, and none is needed to read any result here.
`papers/issue-1/.gitignore` lists them, so "not part of the committed set" is enforced by the
repository rather than by the author remembering: `git add papers/issue-1/` cannot pick them up
by accident. A package that states its own scope should not rely on memory to keep it.

## Figures and the result table

All four are produced by `make_figures.py` from `canonical_results.json` only, so
they cannot drift from the numbers the validator checks.

| artifact | sha256 (16 hex) | what it shows |
|---|---|---|
| `figures/fig1_crossover.png` | *regenerated* | the core outcome: dense-retrieval-minus-reader gap against interference, with the one rung whose point estimate favours retrieval (a null at I = 0.00, +0.062) and the saturating deficit that follows |
| `figures/fig2_distractor_type.png` | *regenerated* | the distractor-type contrast before and after matching retrieval success: a two-nat apparent effect at fixed density, and a -0.155-nat residual once the gold record is inside the k=4 set for both families |
| `figures/fig3_position.png` | *regenerated* | the U-shape of evidence position, with the middle of the context the worst point and the sampled exact-match rate beside it |
| `results_table.md` | `3c3b21f35f40c6c5` | the 18-row main grid: length x interference, both arms, gap, and the recall of both retrievers |

## Why the fidelity corpus is frozen

`eval_fidelity.py` does not read the repository at run time. It reads
`fidelity_corpus.json`, a committed snapshot (157,279 bytes) of the twelve documents
the gate scores, and it fails loudly if that file is missing. The reason is reproducibility:
the gate originally globbed the working tree, so it silently counted whatever manuscripts
happened to be present, and in a fresh clone it found two instead of twelve. Freezing the
corpus makes the gate's input an artefact of this package rather than a property of the
checkout, and the recorded fidelity numbers (5.242516 bits/token held-out, 12/12 checks)
reproduce exactly from the snapshot.

The document labels inside the snapshot are authoring-tree paths. They are kept as
provenance labels only - the gate never re-reads those paths, and the numbers depend only
on the text stored in the JSON. Two of the twelve are public documents of this repository's
archive; the rest are research drafts from the authoring tree. The gate measures **port
fidelity** (does the dependency-free port reproduce the reference implementation's
bits/token on held-out text?), not model quality, and it carries a positive control for
exactly that reason: three deliberately broken configurations (transposed attention
output, RoPE disabled, wrong RoPE theta) must degrade perplexity by at least 1.15x before
the gate's green result is accepted.

## What this package does not claim

- It does not test retrieval against reading on **other models or tasks**; the phase map is
  measured on one 135M reader and one synthetic evidence-access task, and the manuscript
  says so in its threats section.
- The light tier does not recompute the sweep. It is a package-integrity check, not a
  substitute for the heavy tier: read its output as "this package is intact", never as
  "the experiment was reproduced".
- The published wording "could not install PyTorch on the authoring machine" applies to the
  default interpreter only. PyTorch was reachable through a pre-existing local environment,
  which is how the heavy tier was run for the numbers above; the heavy tier therefore needs
  **a** PyTorch interpreter, not network access.
- Both wall-clock figures are single-machine measurements and are reported as such; they are
  not part of any hashed payload (validation check A02 asserts that no timing field survives
  into the artefact).
- Reference verification was performed on 2026-09-11 against live arXiv and Crossref records; a
  record that later moves or is retracted is a change in the world, not a change in this package.
  `refs_tool.py verify` re-runs the check and exits non-zero if any entry fails to resolve to its
  recorded title.
