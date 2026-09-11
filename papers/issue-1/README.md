# Issue #1 - reproduction package

**When Should an Agent Retrieve Instead of Read? A Controlled Phase Map of
Evidence Access under Semantic Interference**

This directory is the committed artefact set for issue #1: the sweep runner, the
derivation and analysis scripts, the figures, the result table, a frozen snapshot of the
reader-fidelity corpus, a 37-check validation suite, and a 21-check manuscript-consistency
gate. Every number that appears in
`manuscript.md` is read out of `canonical_results.json`, which this package
regenerates from scratch and validates. Seven independent full runs of this pipeline produced a byte-identical artefact, the four most
recent through the entry point documented below after a metadata correction (see *Reproduction status*).

## One-command reproduction

    working directory:  papers/issue-1        (the package root - run it from there)
    environment:        see "Environment" below - it decides which tier runs
    command:            bash reproduce.sh

Expected output (light tier, default environment):

    canonical payload sha256: 8dc43a9cc1d0a981
    VALIDATE 37/37
    CONSISTENCY 21/21
    RESULT: PASS

Full artefact payload sha256:

    8dc43a9cc1d0a981a74de025e88046a3c31348928c4e7b83383ebf34582e71d7

**Tolerance: exact, not statistical.** `validate.py` must print `VALIDATE 37/37`;
it asserts 37 individual conditions (14 structural, 23 mechanism), each attached to a
specific headline claim in the manuscript. `consistency_check.py` must print
`CONSISTENCY 21/21`, which it does by re-deriving from the artefact every number the
manuscript quotes (see *Traceability* below). The three figures and the result table must
match the sha256 values recorded in `figures/manifest.json` byte for byte. A single
mismatched byte, or a single failed assertion, fails the run.

**Measured wall-clock** (Apple silicon, no GPU, both measured by the script itself):

| tier | total | breakdown |
|---|---|---|
| **heavy** (recomputes the experiment) | **605 s** | fidelity gate 15 s, 48-cell sweep and derivation 590 s, figures 0 s, validation 0 s |
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
| **heavy** | no - needs PyTorch + numpy and the two model snapshots | everything: the reader-fidelity gate, all 48 sweep cells from the corpus definitions, the whole derivation, then rewrites `canonical_results.json` | nothing |
| **light** | yes - needs only Python 3 + matplotlib | the three figures and the result table, from the committed artefact | everything else: checksums, structural consistency, all 37 mechanism assertions, and the 21-check manuscript-to-artefact consistency gate |

**The light tier is a package-integrity check, not a reproduction.** It confirms that the
committed artefact is internally consistent, that its embedded payload hash recomputes, and
that every headline number the manuscript quotes traces back to that artefact (`CONSISTENCY 21/21`) - but the
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
point: 605 s wall-clock, `VALIDATE 37/37`, and the rewritten `canonical_results.json`
byte-identical to the committed file (`cmp` reports no difference; file sha256
`de241d916e5885a82a6ecea8f258a2b47705b546f89c427e49dec9cc0d303a6e`, payload sha256
`8dc43a9cc1d0a981a74de025e88046a3...`). That makes seven independent full runs in total (three before a metadata correction, four after),
all producing a byte-identical artefact - the four post-correction runs are the committed artefact's.
The most recent one was run after the consistency gate was added, so it is also the run that
exercised `consistency_check.py` on the recompute path (`CONSISTENCY 21/21`, in `run.log`).
 `run.log` is the record of the most recent one - currently a
heavy-tier run, with its per-step timings.

## Traceability: every manuscript number back to the artefact

The chain a number travels from the experiment to the manuscript is

    canonical_results.json  ->  make_figures.py  ->  results_table.md  ->  manuscript.md

and it is checked rather than asserted. `consistency_check.py` walks that chain in both
directions - it reads the committed artefact, the generated table, the figure manifest, the
bibliography record store and the manuscript - and prints `CONSISTENCY 21/21`. It uses only
the standard library, so it runs in either tier; `reproduce.sh` runs it as its last step in
both. What the 21 checks cover:

- the manuscript's header carries the artefact's payload sha256, and that hash recomputes from the artefact body (C01-C02);
- the 18 data rows of the manuscript's main table equal `results_table.md` byte for byte, and that file matches `figures/manifest.json` (C03-C04);
- every headline number the manuscript quotes - the six interference gaps, the three context-length budgets, the filler control, the five position fractions, the distractor-type contrasts, the dense pooled-recall ladder, the BM25 recall, the cell count, the sign test, every Wilson interval in the table, and the fidelity block - is present **anchored to the sentence that makes the claim**, not merely as digits somewhere in the file (C05-C14). Anchoring matters here: the manuscript carries 115 arXiv identifiers, so a bare substring test is satisfied by unrelated digits, which is exactly the failure the audit below finds and eliminates;
- the bibliography has exactly one section, its entry count equals the verified record store, and every entry is cited in the body - citation clusters such as `[18,19,20,21,22,23]` are counted as citing each of their members, the same resolution the repository's `refgate.py` applies (C15-C17);
- the committed figures match the hashes in the manifest (C18).

The gate exits non-zero as soon as one number cannot be traced, so a manuscript edit that
outruns the artefact fails the same one-command reproduction that produces the artefact.

### Does every check earn its place? (`check_audit.py`)

A suite that reports `21/21` is evidence about the suite only if each check can be shown to
reject something; a check that never fires inflates the denominator without constraining the
artefact. `check_audit.py` tests that directly. For each check it applies one targeted
corruption to a throwaway copy of the package, runs the gate there, and records which checks
fail. The corruptions are surgical and each mutator asserts that it changed something, so a
silently ineffective corruption cannot be mistaken for a check that failed to fire.

```
python3 check_audit.py
AUDIT CLEAN - every one of the 21 checks rejects something
```

Current result: **21/21 checks load-bearing, 22/22 corruptions caught, no decoration, and 17
checks have a corruption that only they catch.** Four corruptions trip two checks each, and
that overlap is expected rather than hidden: C02 recomputes the artefact's embedded payload
hash, so any edit to the artefact body necessarily trips it beside whichever check reads the
mutated field, and C16/C17 are two views of the same bibliography.

The audit is not decoration itself - it changed the gate. Its first run found that the four
per-rung recall tests (k=1,2,4,8) could not be made to fire independently: the exact
pooled-recall ladder phrase already pins all four values in one rendering, so the per-rung
tests were redundant. Three of them were removed and the stricter phrase test kept, which is
why this gate has 21 checks rather than 24. The same run showed that a value-presence test can
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
| `reproduce.sh` | `fc29253a003fef7d` | one-command entry point; picks interpreters, runs the tiers, writes `run.log` |
| `canonical_runner.py` | `6ae0667d242879ad` | single entry: fidelity gate, 48-cell sweep, derivation, artefact write |
| `eval_fidelity.py` | `8766fac036626e1e` | reader-fidelity gate over the frozen corpus; 12/12 checks plus a power check |
| `grid6.py` | `e2c5390959ce3f06` | the 48-cell grid definition and sweep driver |
| `analyze6.py` | `10a160fe8e27a565` | derivation: gaps, recall, Wilson intervals, position and type contrasts |
| `corpus5.py` | `bb6b3ec05fc59306` | builds the 12-document fidelity corpus and its train/eval split |
| `mini_port.py` | `1d8eee73ba250b60` | dependency-free transformer port (SmolLM2-135M) |
| `smollm_port.py` | `7309967e201e8acc` | reader wrapper: KV cache, greedy and sampled decoding |
| `validate.py` | `c9246f133fb0369f` | 37 assertions over the artefact; prints `VALIDATE 37/37` |
| `consistency_check.py` | `b6fd5605c27b4bfe` | 21 checks tracing every number in `manuscript.md` back to the artefact; prints `CONSISTENCY 21/21` |
| `check_audit.py` | `20f2b0a1c9e9b54d` | reversion audit of the gate: one targeted corruption per check, reporting which checks are load-bearing |
| `make_figures.py` | `cad4ec44b524f327` | regenerates the three figures and the result table from the artefact |
| `canonical_results.json` | `de241d916e5885a8` | the artefact: sweep, derivations, fidelity block, embedded payload sha256 |
| `fidelity_corpus.json` | `01e1d83b232acc68` | frozen text snapshot the fidelity gate reads (see below) |
| `results_table.md` | `cdf83e5e7730c522` | the result table embedded in the manuscript |
| `figures/manifest.json` | `2760403cfe629432` | figure/table sha256 values and every number plotted in them |
| `run.log` | `3e600142fe1713fd` | the log of the most recent run of this script (a heavy-tier run) |
| `manuscript.md` | - | the manuscript; every number in it is read from `canonical_results.json` |
| `reference-check.md` | - | citation authenticity and coverage report (115 entries) |
| `refs_tool.py` | `bd4eadc8ab5af4d0` | bibliography builder: `harvest` (arXiv + Crossref search) and `verify` (re-fetch by identifier) |
| `refs_selected.json` | `1629a255f263f98b` | the curated selection (115 entries) with a stated difference for each |
| `references.json` | `636f838ee3980af0` | the verified record store; `reference-check.md` is generated from it |

**Files the heavy tier writes but this package does not commit.** Running the heavy tier
leaves three further JSON files in this directory - `fidelity_results.json` (the gate's
output), `grid6_results.json` (the raw 48-cell sweep) and `grid6_analysis.json` (the
derivation's input); `canonical_runner.py` names them in that order. They are the pipeline's
intermediates, not part of the committed set: every number they carry is embedded in
`canonical_results.json`, which is what the manuscript, `validate.py` and `make_figures.py`
read. None of the three records wall-clock time, and none is needed to read any result here.

## Figures and the result table

All four are produced by `make_figures.py` from `canonical_results.json` only, so
they cannot drift from the numbers the validator checks.

| artifact | sha256 (16 hex) | what it shows |
|---|---|---|
| `figures/fig1_crossover.png` | `ca55c1097815ebbc` | the core outcome: dense-retrieval-minus-reader gap against interference, with the one point where retrieval leads (+0.062 at I=0.00) and the saturating deficit that follows |
| `figures/fig2_distractor_type.png` | `b03d53ccce7181f5` | the sign flip: same-entity confusables keep reading ahead, different-entity distractors reverse it at matched density |
| `figures/fig3_position.png` | `274cc7deb93251fd` | the U-shape of evidence position, with the middle of the context the worst point and the sampled exact-match rate beside it |
| `results_table.md` | `cdf83e5e7730c522` | the 18-row main grid: length x interference, both arms, gap, and the recall of both retrievers |

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
