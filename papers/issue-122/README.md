# Issue #122 — reproduction package

**Prevention Is Not Cure: What Fresh-Data Rate a Self-Consuming Training Loop Needs to Stay Stable,
and What It Needs to Recover**

This directory is the committed artefact set for issue #122: the three instruments, the artefacts they
produce, the reference layer (discovery, curation, verification and metadata), the figure generator, a
42-check validation suite tied to the manuscript's claims, and the citation report. Every number in
`manuscript.md` is read out of a committed `*_results.json` by `build_manuscript.py` — nothing is
typed into the prose — and `validate.py` re-reads those artefacts and asserts the claim each number
belongs to.

## One-command reproduction

    working directory:  papers/issue-122        (the package root — run it from there)
    command:            bash reproduce.sh

Expected output:

    VALIDATE 42/42
    RESULT: PASS
    SELFTEST 10/10 plants caught
    CHECKSUMS [HARD] 29/29 files match the committed record
    RESULT: PASS

and, on the full tier, one `wrote <name>_results.json` line per instrument plus a per-figure line.
`RESULT: PASS` is the verdict a verifier compares; the interpreter and the wall-clock are printed
above it and are machine-dependent.

### Tiers

| tier | command | what it does | measured wall-clock |
|---|---|---|---|
| **full** (default) | `bash reproduce.sh` | recomputes all three artefacts, regenerates the five figures and the reference layer, re-assembles the manuscript, validates, runs the suite's own plant control, checks the committed bytes | **78 s** |
| **quick** | `REPRODUCE_QUICK=1 bash reproduce.sh` | validates the artefacts **as committed** | 9 s |

The full tier is what the package stands behind: it shows the stored artefacts are what the code
produces, and that the committed bytes are the ones the run just wrote.

### Tolerance: exact, not statistical

`validate.py` prints `VALIDATE <passed>/<run>` and **all 42 checks must pass**; each is attached to a
named claim and its label names the section of the manuscript it belongs to (`4.1 …`, `4.5 …`,
`refs: …`). A single failed check fails the run, and so does an instrument that exits non-zero.

Two of the checks **re-derive** a statistic rather than reading the printed value back: the
Jensen-gap readings and their split around the bound are recomputed from the per-cell vectors on the
instrument's own gate, and the figure hashes are recomputed from the PNG bytes. A number is not
evidence for itself.

The suite also runs **a two-sided control on itself** (`validate.py --selftest`): each check is re-run
against a mutated copy of the artefact it reads, and every mutation must produce a failure.
`SELFTEST 10/10 plants caught` is that result. A check that cannot fire is decoration, so this is the
check on the checks.

### Determinism, and what the checksum step does and does not cover

Every instrument is deterministic: a seeded RNG derived from a fixed base and a hash of the cell's own
parameters (never from process state), no clocks, no environment reads. **Measured on the authoring
machine: the full tier reproduces all three artefacts and all five figures byte-identically**, and
`checksums.sha256` is the sha256 of the submitted bytes.

**The artefact bytes depend on the build, not only on the code and the seed.** `build.json` records
the interpreter, numpy and matplotlib versions that produced the submitted artefacts
(CPython 3.9.6, numpy 2.0.2, matplotlib 3.9.4). On a **different** interpreter the run is still
expected to pass every check, but floating-point sums can differ in the last one or two ULPs — CPython
3.12 changed `sum()` to compensated (Neumaier) summation — so the checksum step is a **hard** check
when the running build matches `build.json` and an **advisory** one when it does not, and it says
which of the two it is. A reproduction claim that does not name its build is a claim a verifier cannot
apply.

## The claims, and the artefact each one is read from

| # | claim | instrument | artefact |
|---|---|---|---|
| 1 | the folk closed form `(1−p*)ⁿ` bounds the **unconditional** loss probability, not the rate a loop experiences; the conditional rate falls on **both** sides of it, and the absence fraction of the symbol predicts which | `spike_v1.py` | `spike_v1_results.json` (`cf_over_meas_*`, `n_gap_above1`, `gap_by_absence`) |
| 2 | the stability boundary is set by the **pool window**, falling 2–3 orders at matched per-generation fresh rate | `spike_v2.py` | `spike_v2_results.json` (`part2`) |
| 3 | pooling replaces exponential mean reversion with a **moving-average** relaxation whose rate is the companion-matrix eigenvalue nearest 1 | `spike_v2.py` | `spike_v2_results.json` (`part3`) |
| 4 | "stable" is two different questions: keeping an intact support costs 13–45× more fresh data than healing a collapsed loop | `spike_v3.py` | `spike_v3_results.json` (`controls`) |
| 5 | no point of no return, but a finite-horizon one: the exit/entry first-passage times cross | `spike_v1.py` | `spike_v1_results.json` (`first_passage`, `crossing`) |
| 6 | no candidate mechanism quantity is invariant at the boundary (each fails a held-out test) | `spike_v3.py` | `spike_v3_results.json` (`predictions`) |

## The reference layer

102 references, every one cited in the body by its numbered key (0 uncited), each resolved **by its own
identifier** against the index that owns it (arXiv). `reference-check.md` is generated by
`make_reference_check.py` from `refs/curated.json`, `refs/meta.json`, `refs/verify.log` and
`manuscript.md` — including the counts, the section that precedes the bibliography, and the scan for
bracketed groups that are not citations.

A full re-verification re-fetches every identifier and needs the network:

    python3 refs_tool.py verify     # writes refs/verify.log (102 OK, 0 PROBLEM)
    python3 refs_tool.py plant      # two-sided control: corrupted title, invented id, invented DOI
    python3 refs_meta.py            # author metadata + its own plant control

`reproduce.sh` does **not** run these (a verifier's host may be offline); it reads the committed log.

## Files

| file | what it is |
|---|---|
| `manuscript.md` | the assembled manuscript (build output — 135 numbers, all sourced) |
| `manuscript.src.md` | the manuscript with `{{value}}` placeholders; the editable source |
| `build_manuscript.py` | the build: resolves every number from an artefact, refuses an ownerless number, an unused value, an unreadable placeholder, an uncited reference or a mis-filed citation |
| `values.json` | provenance for every printed number (value ← artefact ← field) |
| `spike_v1.py`, `spike_v2.py`, `spike_v3.py` | the instruments |
| `spike_v*_results.json` | their artefacts (the only source of the manuscript's numbers) |
| `make_figures.py`, `figures/` | the five figures and `manifest.json` (per-figure sha256 + source-artefact hashes) |
| `refs_discover.py`, `refs_curate.py`, `refs_meta.py`, `refs_tool.py`, `make_references.py` | the reference layer |
| `refs/` | `curated.json`, `meta.json`, `verify.log`, `numbering.json` |
| `reference-check.md` | the citation report, generated |
| `validate.py` | the 42-check claim suite + its plant control |
| `checksums.sha256`, `build.json` | the submitted bytes and the build that produced them |
| `reproduce.sh` | the one command |
| `run.log`, `gates.log` | the run log of the last reproduction, and the journal gates' output |

## What this package is not

The instruments simulate a **defined stochastic process** — the loop is ground truth by construction —
so the results are not measurements of a trained model. The manuscript states this in §3 and §7
(threats): the map from the process to a real training run is the paper's assumption, the loop is
memoryless across generations, and the reference layer's author metadata is fetched, not
independently re-verified. §7 argues why the results remain of interest despite each limitation.
