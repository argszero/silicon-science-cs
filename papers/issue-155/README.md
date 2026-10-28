# Issue #155 — reproduction

**One command, offline, deterministic.** Run it from *this* directory:

```sh
./reproduce.sh
```

**Expected final line:** `REPRODUCE: ALL GREEN (6 steps)`. **Exit status:** the number of failed
steps (0 on success) — failures accumulate, so no later step can mask an earlier one.

**The step count is checked, not remembered.** A final check compares the number of steps this
script executes with the count it declares, with the denominator in every step label, and with the
verdict line quoted in `README.md` and in the manuscript's reproducibility section. A second copy of
the program that nothing reads is how the same drift appeared on #128, #145 and #149.

**The bibliography's entry form is checked by entry block, not by line.** `check_references.py`
reads the `## References` section as blocks — one paragraph is one entry, which is also the unit a
renderer prints as one paragraph — asserts the components in the order the house style resolves them
(`[n]`, the authors, the year in parentheses, the title, the venue, a resolvable URL, and the entry
closing with its one-line `Difference:`), and prints one line per entry with each component's length
so a reader can see which component moved. It reads and writes nothing else. The check was
demonstrated **red before it was trusted**: run against the manuscript at `5809544` it reports 208
problems, two per entry (no parenthesised year, no closing `Difference:`), which is exactly the
editorial finding it exists to keep fixed.

**Expected runtime:** about 10 minutes on one core (measured **564 s** on the reference machine for
the six steps below, including the `n = 8` rule cells the registered criteria require; the editorial
triage of 2026-10-28 read **668 s** on its own host, which is a machine difference and not a change
in the work — this sentence names the machine its number came from). The cost is exhaustive
enumeration, not sampling: the largest single sweep evaluates 5,040 arrival orders at every queue
count.

**Tolerance:** none, and none is possible. Every step is exhaustive enumeration over a finite set
of windows with no sampling and no random seeds, so every output is an exact integer count or an
exact rational and is expected to be reproduced **byte for byte**. `results.json` is written with
sorted keys and fixed indentation, so a difference in the file is a difference in a number.

The two figure files hold to the same standard, which they did not at first: matplotlib stamps an SVG
with a `<dc:date>` and derives every clip-path id from a per-process random hash salt, so a
regenerated figure differed from the committed one in 49 lines while every plotted number was equal —
a diff that looks like a change and carries no information. `make_figure.py` now pins
`svg.hashsalt` and suppresses the date, and two consecutive runs produce both files byte-identically.

## Environment

| what | value |
|---|---|
| interpreter | CPython 3.9.6 at `/usr/bin/python3` (override with `PY=...`) |
| third-party dependency | `matplotlib` **3.9.4** — used only by step 2, to draw the figure |
| everything else | Python standard library only |
| network | not used by any step of `reproduce.sh`; the reference verifier uses it separately (see References) |

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
| 1 | `emit_results.py` | `results.json`. Certifies the fast floor against an independently written exhaustive one (5,016 distinct-rank and 1,068 tie-bearing (window, k) pairs, 0 mismatches); verifies the exact strict-priority threshold statistic over all arrival orders at n = 4..7; verifies the candidate statistics under ties over 6,285 windows; emits both discipline-gap distributions; measures the deployed-shaped rule against the floor in every cell to **n = 8**, with the misaligned control, and reports on both the cell population (`k < m`) and the registered prior's own population (`k < LDS`); and reports the `k=1` cells as forced rather than as comparisons. |
| 2 | `make_figure.py` | `figures/discipline-gap.svg` and `.png`, drawn from `results.json`, with the caption's claims asserted as invariants (the stacked fractions sum to 1 in every bar; the maximum gap is 2 under distinct ranks and 1 under ties). |
| 3 | `check_results.py` | every stored **summary** value recomputed from the per-cell rows it summarises, plus the claim relations the manuscript leans on. A summary is the number that goes stale when a row moves and the summary does not, so it is recomputed here rather than trusted. |
| 4 | `place_refs.py --check` | that the reference placement still resolves every named record to exactly one harvested candidate, keeps no pruned key alive, and matches the committed `placement.json` **byte for byte**. It compares rather than writes: a gate that rewrote the artifact would leave `reference-check.md` describing a placement that no longer exists. |
| 5 | `make_manuscript.py --check` | that every number in the manuscript still binds to `results.json`, every one of the 104 references is still cited in the body, the stray-number scan is still clean, and `manuscript.md` matches the committed bytes. It compares rather than writes, for the same reason step 4 does. |

## References

The bibliography is a **funnel with a counted reason at every stage**, not a keyword list. Each stage
writes an artifact, so the drop is auditable rather than silent:

| stage | program | artifact | result |
|---|---|---|---|
| harvest | `build_refs.py` | `pool.json` | 56 construct-named Crossref queries → 1,879 unique records; 98 rejected by academic type, 139 missing year or venue → **1,642 kept** |
| screen | `screen_refs.py` | `candidates.json` | rejects bare-term titles (136), other-field records (120: ATM 17, wireless 66, active queue management 14, queueing theory 15, cache 4) and records with no construct (604) → **782 candidates**, 383 of which touch the central constructs |
| place | `place_refs.py` | `placement.json` | each record must name **a section and the sentence it supports**; 100 named + 4 DOI seeds → **104 placed**, 6 pruned with a reason (3 recalled titles that were never in the pool, 3 duplicate DOIs) |
| verify | `verify_refs.py` | `reference-check.md` | each placed DOI re-fetched **by identifier** from Crossref, independent of the query that harvested it → **104 / 104 resolve to the work they claim**, 7 with an edition-year note |

Two things this pipeline does that a query list does not:

- **A title collision is settled by DOI.** Eleven of the named records matched more than one harvested
  title; the placement names the DOI rather than a longer substring, because a DOI identifies a work
  and a title identifies a string. The resolver refuses on ambiguity — it never takes whichever record
  printed first — and it did refuse: the first run placed 91 of 107 and named all 16 refusals.
- **Seeds are declared, not smuggled.** Four records cannot be returned by construct queries at all
  (Even–Itai 1971, Tarjan 1972, Pratt 1973 and the originating PIFO paper — the last does not use
  "PIFO" in its title). `fetch_seeds.py` fetches them by DOI and records *why the harvest missed each
  one*; `place_refs.py` refuses to run if a seed is missing or failed to resolve.

**`verify_refs.py` uses the network and is therefore not a step of `reproduce.sh`.** `reference-check.md`
is the stored result of a run made at the head; re-running the verifier is what a reviewer should do
to check the citations, and it is deliberately kept out of the offline script so that "one command
reproduces every number" stays literally true.

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
  and restoring returns it to **0**;
- a placement file whose entry names a **non-existent DOI** makes `verify_refs.py` report `NOT-FOUND`
  and exit **1**, and one that names a **real DOI belonging to a different work** reports
  `TITLE-MISMATCH` (`token agreement 0.00 < 0.80`) and exits **1**;
- a `placement.json` edited to disagree with the placement it stores makes step 4 exit **1**
  (`STALE`), and restoring it returns step 4 to **0**.
