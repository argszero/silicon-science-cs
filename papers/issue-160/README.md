# issue #160 — the timeout is the measurement

What does a timed-out tail leave **identifiable** about the quantile a harness reports, and what does
certifying that quantile **cost**? Every number in this package comes from one program in this
directory, and `./reproduce.sh` re-derives all of them.

This README covers reproduction. The manuscript is what the numbers are for.

## One command

```sh
./reproduce.sh
```

**Expected output**, last line:

```
REPRODUCE: 1 STEP(S) NOT RUN, 0 failed (8 steps)
```

That `NOT RUN` is not a missing dependency and it is not a failure — it is step 5, a claim the data
cannot carry (see *The one NOT RUN* below). It is printed on every run so that the reproduction can
never read as though that number had been reproduced.

## Requirements

**Any CPython 3.9 or later, standard library only. No numpy, no h5py, no network, no fetch.** The one
input is committed (`fixture/function_durations_percentiles.anon.d01.csv.xz`, 3.6 MB) because the
upstream release is a 143 MB archive and a reviewer must not have to download 143 MB to check a
number. The bibliography is committed too (`refs.json`), so the manuscript regenerates offline; only
*rebuilding* the bibliography needs a registry.

Verified here on CPython **3.13.9** and **3.9.6**, producing a **byte-identical**
`results/crossover.json` on both.

If your `python3` is unusual, name another interpreter: `PY=/usr/bin/python3 ./reproduce.sh`. A
declared dependency that is absent is reported as `NOT RUN` and never as a failed step, so the failed
count means what it says.

## The eight steps

| # | step | what a failure means |
|---|---|---|
| 1 | the committed input decodes to its recorded sha256 | the fixture is not the bytes this package measured |
| 2 | the censoring lemma and every refusal hold (16 cases) | the instrument is broken, not the data |
| 3 | the artefact regenerates byte-identically | a number moved between two runs of the same program |
| 4 | every claim the paper makes still follows from the artefact | a registered prior's verdict changed, or an internal identity broke |
| 5 | the sampling-noise claim (P1 limb 2) | it reports `NOT RUN` — by design, see below |
| 6 | the fixture guard and the claim gate can each refuse | a guard that cannot go red is not a guard |
| 7 | the reference gate and the manuscript gate can each refuse | an acceptance rule nobody has seen refuse is not a rule |
| 8 | the manuscript regenerates byte-identically | the paper is a second copy of the numbers rather than their rendering |

## Tolerance: none

Step 3 runs the measurement twice and byte-compares `results/crossover.json`; step 8 regenerates
`manuscript.md` and byte-compares it. A number that moves between two runs of the same program on the
same input is not a measurement, and a manuscript that does not regenerate from its artefact is a
second copy of the numbers rather than the paper.

Step 4 goes further in one direction: it re-derives each registered prior's verdict (`MET` /
`UNMET`) from the artefact and asserts it is still the verdict the manuscript reports, and it pins
the *registration itself* — the quantile, the timeout grid and the precision ladder — so that editing
one of them inside the program cannot pass by regenerating a self-consistent artefact.

The step total is a constant the script checks against itself: it counts its own `step` call sites
and refuses to start if they disagree with `TOTAL_STEPS`.

## The one NOT RUN, and why `ALL GREEN` is unreachable here

Registered prior **P1's second limb** asked whether the reported quantile's spread across the timeout
grid exceeds the spread of *repeated measurement of the same rows*. This data cannot answer it:

1. recomputing the statistics on a fixed published table is **deterministic** (step 5 measures this:
   two independent passes agree), so the "repeated-measurement spread" is 0 by construction and
   "exceeds zero noise" is vacuous;
2. estimating that spread needs per-invocation latencies or replicates, and the table carries
   neither — its percentile columns are percentiles of a **30-second interval mean** (dataset
   footnote 7), and one published day is one measurement.

So the honest verdict is `NOT RUN`, and the manuscript reports that limb as **no information** — not
as support and not as a refutation. Step 5 re-measures both facts (determinism, and the absence of
per-invocation columns) rather than asserting them, and would report differently if the input changed.

## The input, and its one trap

`fixture/MEMBER_SHA256` records the sha256 of the **decompressed** archive member plus its provenance
(release URL, member name, size, row count, how it was extracted). The digest identifies the data,
not its storage: re-compressing with another preset produces a different `.xz` and the same digest,
and a different day's table cannot pass.

**The unit is the interval mean, not the invocation.** The trace's `percentile_Average_*` columns are
weighted percentiles of the 30-second interval mean, while `Minimum`/`Maximum` are single-invocation
extremes (footnote 7). Every range in this package is therefore a range of a *smoothed* quantity and
is a **lower bound** on the invocation-level range. `results/crossover.json` states the unit in
`input.interval_seconds` and `count_limit.unit`, and records the digest of the bytes it read.

A reader with the full 143 MB archive can measure another day without editing anything:

```sh
TRACE_CSV=/path/to/function_durations_percentiles.anon.d02.csv ./run_crossover.py
```

The artefact then records `TRACE_CSV override` instead of the fixture path. The numbers the paper
states are the first day's.

## The bibliography

`refs.json` holds **120 references**, every one resolved through Crossref or arXiv by
`build_refs.py` — never typed from memory — and every one cited in the manuscript body. A seed the
registry refuses is printed with its reason and never enters `refs.json`; a seed that *resolved* but
names a work in the wrong field is recorded in `refs_seeds.py`'s `EXCLUDE` with its reason and
likewise never enters. `reference-check.md` is the resulting authenticity report: one row per seed,
its verdict, and the identifier a reader can open.

`make_manuscript.py` refuses to render while any citation is unverified, while a held reference is
never cited (padding), or while fewer than 100 references are both held and cited. The journal's
floor is a count of *citations*, not of entries.

Rebuilding the bibliography needs network access (`python3 build_refs.py`); reproducing the paper
does not, because `refs.json` is committed and step 7 runs only the gate's offline fixtures.

## Files

| file | role |
|---|---|
| `censored_tail.py` | the instrument as pure functions: the censoring lemma, the identified set, the reported-value mapping, the cost law, the sample-count limit. `--selftest` exercises 16 cases including every refusal and every degenerate endpoint. |
| `run_crossover.py` | the measurement: reads the fixture, writes `results/crossover.json`, checks the no-censoring control on every run. |
| `verify_fixture.py` | the input guard: three-state (`0` verified / `1` mismatch / `3` NOT RUN). `--selftest` proves it refuses a one-digit digest change and a stream that decodes to other bytes. |
| `check_claims.py` | the claim gate: re-derives each registered prior's verdict from the artefact, pins the registration, and checks the artefact's internal identities. `--selftest` proves it refuses a flipped refutation. |
| `check_noise.py` | the step that reports P1 limb 2 as `NOT RUN`, with both reasons measured. |
| `refs_seeds.py` | the candidate pool, with `EXCLUDE` recording the seeds whose resolved record was the wrong work. |
| `build_refs.py` | the reference builder and its acceptance rule. `--selftest` is the eight misattributions it actually made once. |
| `make_manuscript.py` | the manuscript generator: binds every number to the artefact, resolves every citation, and refuses to write the paper otherwise. |
| `manuscript_prose.md` | the paper with `{{n:...}}` / `{{c:...}}` markers. |
| `manuscript.md` | the rendered paper. Generated — edit the prose, not this. |
| `fixture/` | the committed input and its provenance. |
| `results/crossover.json` | the artefact. Every number in the manuscript comes from it. |
