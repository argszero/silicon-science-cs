# Issue #155 — reproduction

**One command, offline, deterministic.** Run it from *this* directory:

```sh
./reproduce.sh
```

**Expected final line:** `REPRODUCE: ALL GREEN (3 steps)`. **Exit status:** the number of failed
steps (0 on success) — failures accumulate, so no later step can mask an earlier one.

**Expected runtime:** about 9 minutes on one core. The cost is exhaustive enumeration, not
sampling: the largest single sweep evaluates 5,040 arrival orders at every queue count.

**Tolerance:** none, and none is possible. Every step is exhaustive enumeration over a finite set
of windows with no sampling and no random seeds, so every output is an exact integer count or an
exact rational and is expected to be reproduced **byte for byte**. `results.json` is written with
sorted keys and fixed indentation, so a difference in the file is a difference in a number.

## Environment

| what | value |
|---|---|
| interpreter | CPython 3.9.6 at `/usr/bin/python3` (override with `PY=...`) |
| third-party dependency | `matplotlib` **3.9.4** — used only by step 2, to draw the figure |
| everything else | Python standard library only |
| network | not used by any step |

`matplotlib` is the only import outside the standard library (`make_figure.py`); steps 1 and 3 run
on a bare interpreter. If `matplotlib` is absent, step 2 fails with an import error and steps 1 and
3 still run — that is a **missing dependency, not a defect in the numbers**, and the failure is
attributable because the step names itself.

## Inputs

**None are read from outside this package.** The inputs are constructed by the programs: every
window is an arrival order over ranks, enumerated in-process. There is no corpus, no download, no
cache, and no file that must be obtained separately — which is also why nothing has to be shipped
under `refs/`.

## What each step establishes

| step | program | establishes |
|---|---|---|
| 1 | `emit_results.py` | `results.json`. Certifies the fast floor against an independently written exhaustive one (5,016 distinct-rank and 1,068 tie-bearing (window, k) pairs, 0 mismatches); verifies the exact strict-priority threshold statistic over all arrival orders at n = 4..7; verifies the candidate statistics under ties over 6,285 windows; emits both discipline-gap distributions; measures the deployed-shaped rule against the floor in every cell, with the misaligned control; and reports the `k=1` cells as forced rather than as comparisons. |
| 2 | `make_figure.py` | `figures/discipline-gap.svg` and `.png`, drawn from `results.json`, with the caption's claims asserted as invariants (the stacked fractions sum to 1 in every bar; the maximum gap is 2 under distinct ranks and 1 under ties). |
| 3 | `check_results.py` | every stored **summary** value recomputed from the per-cell rows it summarises, plus the claim relations the manuscript leans on. A summary is the number that goes stale when a row moves and the summary does not, so it is recomputed here rather than trusted. |

## This command recomputes; it does not validate

Step 1 re-derives every number from the model. It is not a checksum check over committed outputs,
and `results.json` is an **output** of the run, not an input to it — which means a run in a copy of
this package overwrites the committed `results.json` and the two figure files. The committed
versions are what the manuscript's numbers were taken from; a verifier comparing them should
compare against the shipped files at the head, not against a copy a run was made in.

## What is deliberately not covered

- **Ties beyond n = 6**, and distinct ranks beyond **n = 7**. The threshold equivalence is verified
  exhaustively up to those sizes and is not claimed past them.
- **Interleaved arrival.** The model is batch: every packet arrives, then dequeuing begins. This is
  a stated boundary of the model, not an oversight, and the paper says so where it matters.
- **Any measurement of real hardware or production traffic.** No trace, no implementation, no
  deployment is measured anywhere in this package, and no claim is made about one. The figure's
  panels are properties of the model.

## Planted checks

Both guards were seen to fail on a defect before being trusted:

- a stored summary edited to disagree with its rows makes step 3 exit **1** (`gap_summary` and
  `threshold_ties_totals` each reported), and restoring the file returns it to **0**;
- a histogram edited so the figure's "max gap = 1" caption would be false makes step 2 exit **1**,
  and restoring returns it to **0**.
