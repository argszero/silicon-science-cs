# Issue #120 - reproduction package

**What Limits Memory Tiering? An Exact Oracle and the Workload-Intrinsic Floor on Slow-Tier
Traffic**

This directory is the committed artefact set for issue #120: the six instruments, the artefacts they
produce, the reference layer (discovery, curation, verification and metadata), the figure generator,
a 40-check validation suite tied to the manuscript's claims, and the citation report. Every number in
`manuscript.md` is read out of a committed `*_results.json`, and `validate.py` re-reads those
artefacts and asserts the claim each number belongs to.

## One-command reproduction

    working directory:  papers/issue-120        (the package root - run it from there)
    command:            bash reproduce.sh

Expected output:

    VALIDATE 40/40
    SELFTEST 7/7 plants caught
    RESULT: PASS

and, on the full tier, one `wrote <name>_results.json` line per instrument plus a per-figure line.
`RESULT: PASS` is the verdict a verifier compares; the interpreter and the wall-clock are printed
above it and are machine-dependent.

**`reproduce.sh` is re-entrant: it prints `RESULT: PASS` on the first run and on every run after it,
over the same copy.** It rewrites only the artefacts it owns (`spike_v*_results.json`,
`figures/*.png`, `figures/manifest.json`, `run.log`), and no check compares those files to a static
record — every check re-derives from the files the run just wrote.

### Tiers

| tier | command | what it does | measured wall-clock |
|---|---|---|---|
| **full** (default) | `bash reproduce.sh` | recomputes all six artefacts, regenerates the five figures, validates, runs the suite's own plant control | **99 s** |
| **quick** | `REPRODUCE_QUICK=1 bash reproduce.sh` | validates the artefacts **as committed**, regenerates figures | 8 s |

The full tier is what the package stands behind: it shows the stored artefacts are what the code
produces. The quick tier is for a reader who wants the verdict without the recomputation.

### Tolerance: exact, not statistical

`validate.py` prints `VALIDATE <passed>/<run>` and **all 40 checks must pass**; each is attached to a
named claim, and the check label names the section of the manuscript it belongs to (`5.1 certificate`,
`5.6 matched pair`, `refs: ...`). A single failed check fails the run, and so does an instrument that
exits non-zero.

The suite also runs **a two-sided control on itself** (`validate.py --selftest`): each check is
re-run against a mutated copy of the artefact it reads, and every mutation must produce a failure.
`SELFTEST 7/7 plants caught` is that result. A check that cannot fire is decoration, so this is the
check on the checks.

### Determinism, and the one thing it does **not** cover

Every instrument is deterministic: a seeded `random.Random` per cell, no clocks, no hash-ordered
iteration, no environment reads. **Measured: two consecutive full runs produced 11 byte-identical
files** (6 artefacts + 5 figures, `sha256` compared).

**The artefact bytes depend on the interpreter, not only on the code and the seed.** The committed
artefacts were produced by **CPython 3.13.9** (`python3` on the authoring machine, recorded in
`run.log`). Re-running the same code on **CPython 3.9.6** reproduces every integer, every verdict and
every curve shape, but values that are floating-point sums differ in the **last one or two ULPs** —
CPython 3.12 changed `sum()` to use compensated (Neumaier) summation, so the same additions
accumulate differently. Nothing in the paper turns on those digits (the checks are tolerance-based,
and the exact-integer routes — the certificate, the Mattson pairs, the matched pair's miss counts —
are identical under both), but a byte-for-byte comparison of the artefacts across interpreters will
report a difference, and it is a difference in the *build*, not in the measurement. This is why
`reproduce.sh` prints the interpreter it selected and writes it into `run.log`: a reproduction claim
that does not name its build is a claim a verifier cannot apply.

## Environment

- **Instruments and validator**: any CPython >= 3.8, **standard library only** — no numpy, no scipy,
  no third-party package. Override with `EMRG_PYTHON=/path/to/python`.
- **Figures**: one interpreter with matplotlib. Override with `EMRG_FIG_PYTHON=/path/to/python`.
  Figures are a presentation step: if matplotlib is missing the script says so and continues, and the
  manifest check in `validate.py` still reads the committed figures.

## What the files are

| file | what it is |
|---|---|
| `manuscript.md` | the paper. Generated from `manuscript.src.md` by `build_manuscript.py`. |
| `manuscript.src.md` | the manuscript **source**: same text, with citations written as `@<identifier>` keys. |
| `build_manuscript.py` | numbers the citation keys in order of first appearance and renders `## References` from `refs/curated.json` + `refs/meta.json`. |
| `spike_v0.py` .. `spike_v5.py` | the six instruments. Each prints its tables and writes `<name>_results.json`. |
| `spike_v*_results.json` | the artefacts. **Every number in the manuscript is read from one of these.** |
| `make_figures.py` | draws the five figures from the artefacts; writes `figures/manifest.json` (sha256 per figure). |
| `validate.py` | the 40-check suite; `--selftest` runs its own plant control. |
| `refs_discover.py` | the external scan that built the candidate pool (53 queries). |
| `refs_curate.py` | the four-limb curation rule that produced the 129-entry set. |
| `refs_tool.py` | verification by identifier (`verify`) and the two-sided plant control (`plant`). |
| `refs_meta.py` | author/year metadata; probes the API and falls back per id to the abstract page. |
| `refs/curated.json` | the 129 curated entries (identifier, title, year, role, stated difference). |
| `refs/meta.json` | the fetched author/year record for each entry (129/129 with authors). |
| `refs/verify.log` | the committed verification run: 129 lines, each an `OK` verdict with the resolved title. |
| `reference-check.md` | the citation report: authenticity method, per-entry record, coverage and ambiguity. |
| `figures/` | the five figures and their manifest. |
| `run.log` | the last `reproduce.sh` run: interpreter, mode, per-step timings, the validation output. |

## Reproduction status

| item | value |
|---|---|
| full-tier run | `VALIDATE 40/40`, `SELFTEST 7/7`, `RESULT: PASS`, 99 s |
| artefacts + figures across two consecutive full runs | **11 files byte-identical** (`sha256`) |
| interpreter that produced the committed artefacts | CPython 3.13.9, recorded in `run.log` |
| cross-interpreter behaviour | every integer, verdict and curve shape reproduces; float sums differ in the last 1-2 ULPs (see *Determinism*) |
| reference layer | 129 entries, 129 `OK` / 0 `PROBLEM`, 129/129 with authors, 129 cited / 0 uncited |

## Reference layer

The reference layer was built by an external arXiv scan (53 queries, ~1,100 candidates), curated by a
four-limb rule to 129 entries, verified by re-fetching each entry **by its own identifier**, and given
author metadata in a second pass. Two things are worth stating plainly, because they are the parts a
reviewer can check and the parts that went wrong on the way:

- **A verified identifier is not a verified citation record.** The identifier pass confirms *title
  identity*; it says nothing about the author field a reference list needs. Author metadata was
  fetched separately (`refs_meta.py`; 129/129), and every author name in `manuscript.md` is rendered
  from `refs/meta.json` — none is typed by hand.
- **Transport.** The arXiv *API* endpoint is intermittently unanswered from the authoring host: the
  read times out rather than returning an error. The verifier is therefore cache-first, and the
  metadata pass falls back per id to the arXiv abstract page, which carries the same fields as
  schema.org `citation_*` meta tags. The fallback re-compares the title it read against the curated
  title, so it cannot silently substitute a different paper. Re-running `refs_tool.py verify` in full
  needs network reachability; the committed `refs/verify.log` is the record of the run performed.

## Presentation requirements

The manuscript embeds five figures, each with a caption and a sentence in the body that refers to it,
and it carries **one** `## References` section (after Appendix A) with **129 numbered entries**,
each beginning on its own line and separated by a blank line, each cited in the body by its numbered
key, and each carrying a one-line stated difference from this work.

## Links

Every markdown link in this package and in `manuscript.md` resolves **at the linking file's own
directory**. The figure links in `manuscript.md` are relative to `papers/issue-120/` (the file's own
directory), not to the repository root.
