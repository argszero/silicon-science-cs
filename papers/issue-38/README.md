# Issue #38 - reproduction package

**When Do Agent Markets Beat Planners? A Boundary Law for Decentralised Allocation under
Misestimated Costs and Bounded Central Attention**

Contribution level: **theory + empirics**.

This directory is the committed artefact set for issue #38: the allocation model, the canonical
runner (the single source of every number in `manuscript.md`), the artefact it produces, the
figure generator and the figures, a 92-check validation suite, a self-audit of that suite, and the
citation-authenticity report.

## One-command reproduction

    working directory:  papers/issue-38        (the package root - run it from there)
    command:            bash reproduce.sh

Expected output (tail):

    VALIDATE 92/92
    artefact sha256: ca311f90f5506d6f9c7e6af4f6ce76e6a79202802c20335f6824786c72488c50
    RESULT: PASS

Full artefact digest:

    ca311f90f5506d6f9c7e6af4f6ce76e6a79202802c20335f6824786c72488c50

**Tolerance: exact, not statistical.** `validate.py` must print `VALIDATE 92/92`; each of its 92
conditions is attached to a specific headline number of the manuscript (the reductions, the
behavioural anchors, the §4.1 series counts, the §4.2 out-of-sample table, the §4.3 closure table,
the §4.4 attention-model test, the §4.5 mechanism rates, the §4.6 ablation). Every quantity is a
deterministic function of the seed scheme, so there is no tolerance band to choose. A single failed
condition fails the run.

**Files this run rewrites, deliberately:** `canonical_results.json`, `run.log`, `figures/*.png`,
`figures/manifest.json`. Nothing compares any of those against a stored copy, so **the command is
re-entrant** - it prints `RESULT: PASS` on the first run and on every run after it over the same
checkout (verified twice in a row; the digest above was identical on both). Figure digests are
checked against `figures/manifest.json`, which is regenerated in the same run, so figure bytes may
legitimately differ across matplotlib builds without failing.

**Measured wall-clock** (Apple silicon, CPU-only, measured by the script itself): **~180 s**
(canonical runner ~175 s, figures < 1 s, validation < 1 s). Machine-dependent; not part of any claim.

### Environment

The pipeline needs **numpy** and **matplotlib**. The interpreter first on `PATH` need not be the one
that has them, so `reproduce.sh` probes for an interpreter that can actually import both and reports
an explicit `RESULT: FAIL` if none exists, rather than silently substituting one:

    bash reproduce.sh              # auto-selects; prints the interpreter and matplotlib version it used
    PY=/usr/bin/python3 bash reproduce.sh   # override

Verified here with `/usr/bin/python3` (matplotlib 3.9.4).

## What is in the package

| file | what it is |
|---|---|
| `manuscript.md` | the paper (abstract, model, registered priors, results, related work, threats) |
| `reference-check.md` | citation-authenticity report: 125/125 entries resolved, one line per entry |
| `references.json` / `refs_selected.json` | the verified bibliography and the curated selection it was built from |
| `refs_tool.py` | the bibliography tool (`harvest` / `verify`); re-runnable |
| `refs_verify.log` | the verification run log (including the recorded API outage) |
| `alloc_model.py` | the allocation model: instances, oracle, planner, market |
| `canonical_runner.py` | the canonical runner - every number in the manuscript is read out of its artefact |
| `canonical_results.json` | the artefact (reductions, anchors, law grid, out-of-sample race, closure, mechanism, ablation) |
| `run.log` | the runner's own summary of the configuration and the headline results |
| `make_figures.py`, `figures/` | the three figures and their manifest |
| `validate.py` | the 92-check validation suite (`VALIDATE 92/92`) |
| `check_audit.py` | self-audit of `validate.py`: 26 mutations, all of which must be caught |
| `reproduce.sh` | the one command above |

## Headline results (all read out of `canonical_results.json`)

| result | value |
|---|---|
| model reductions exact (attention `m=N` is the optimum; `sigma=0` market is the optimum) | **270/270** |
| registered **P1** (boundary moves toward the planner as the pool grows) | **REFUTED** - `sigma*` endpoint rises in 50/50 series, falls in 0, 173/190 steps non-negative (17 local dips) |
| registered **P2** (a parameter-free constant) | **UNMET** - the constant moves with the cost scale (median rel. error 20.8 %) |
| registered **P3** (the advantage is specialisation) | **REFUTED** - with the channel off (`beta=0`) the boundary still exists (`sigma*` = 0.410/0.570/0.739 at `N` = 16/64/256) |
| boundary law | `sigma* ~= A * p`, `A` median **2.734**, range [1.612, 13.570] |
| fit, in sample | exponent **1.0358**, R^2 **0.9176**, n = 240 (report, do not trust: see below) |
| **out-of-sample race** (240 train / 120 held-out cells) | gamma-aware proportional **18.4 %** median, trivial proportional **27.0 %**, fitted power law **28.5 %**, constant **57.6 %** |
| exponent refit on held-out cells | **0.9773** (drift -0.0585) => the exponent is 1 |
| how much the constant moves with the cost scale | 2.904 / 2.686 / 2.548 / 2.388 at gamma = 0.25 / 0.5 / 1.0 / 2.0 |
| how much it moves with the cost distribution | < 3 % (uniform 2.446, lognormal 2.496, Beta 2.423) |
| the two "physical" scales, scored out of sample | assignment gap **98.4 %** median (2546 % max), cost spread **153.9 %** -> both ruled out |
| attention-model independence | 12 never-fitted fraction-reading cells predicted at **12.4 %** median (budget-cell constant) |
| mechanism | **scrambling** - Hamming fraction 0.138 -> 0.662 over `N` = 16 -> 256; wrong-block rate **exactly 0** for `beta >= 1`, `sigma <= 0.2` |
| ablation | boundary survives with specialisation off; amplification a roughly constant **x4** (3.93/4.12/3.94); at `sigma=0` the market is **exactly** the oracle |

**Read the fit row with the race row, not without it.** An in-sample R^2 of 0.92 with ~30 % residual
scatter is not evidence of a power law; the power law *loses* to a one-parameter proportional law on
cells it has never seen. That comparison is the reason the manuscript claims a proportionality.

## Suite self-audit

    python3 check_audit.py

applies 26 mutations to throwaway copies of the package (artefact fields, the manifest, a deleted
figure, the A-breakdowns, the exponent table, the ablation numbers, the mechanism series) and
requires every one to be caught by at least one `[FAIL]` with a non-zero exit. Each mutator asserts
that it actually changed the file, and the sandbox manifest digest is refreshed first so that the
digest check cannot be the reason a semantic mutation is caught. Current result: **26/26 caught**,
with a clean run at **92/92**.

## Citation report

`reference-check.md` reports the verification of all **125** references by their own identifiers
(21 via the Crossref DOI endpoint, 104 via their arXiv abstract pages - the arXiv export API was
returning HTTP 503/429 during the run and this is recorded in the report rather than hidden), and
the in-text coverage check: `refgate.py` from the repository root reports
`entries=125 covered=125/125 coverage=100.0% GATE: PASS`.

## Seeds

Instance seed `1000*s + N`, noise seed `7*s + 3` on the law / mechanism / closure grids;
`5000*s + 7*N` and `13*s + 11` on the held-out grid. `s` runs to the per-grid seed count
(30 law, 20 out-of-sample, 25 ablation, 15 closure).
