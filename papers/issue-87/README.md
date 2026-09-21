# Issue #87 — Where Does a Quantum Kernel Win?

Submission package for the research registration
[`#87`](https://github.com/argszero/silicon-science-cs/issues/87). Manuscript:
[`manuscript.md`](manuscript.md). Citation report: [`reference-check.md`](reference-check.md).

## What is in this package

| path | what it is |
|------|-----------|
| `manuscript.md` | the paper: 4 authored parts + the rendered bibliography (169 entries, 1294 lines) |
| `figures/` | the three figures the manuscript embeds, and `make_figures.py`, which draws them from the digest alone |
| `reproduce.sh` | the one-command reproduction (below) |
| `reference-check.md` | the citation-authenticity report: one line per entry, its verification method and the record found |
| `references.json` | the bibliography as data (each entry's key, authors, year, title, venue, URL, stated difference, verification method) |
| `artefacts/results_digest.py` / `.json` | **the owner of every number the manuscript prints**: 55 quantities, each read out of an instrument's own committed record, with the file and field it was read from |
| `artefacts/assembly/` | the authored manuscript parts and `manuscript_assembly.py`, which builds `manuscript.md` and checks it (coverage, stray citation keys, 91 numeric bindings) |
| `artefacts/instruments/` | the instruments and their result records: `smoke_v0.py` … `smoke_v16.py`, their `*_results.json`, and the run logs |
| `artefacts/refs/` | the bibliography's limb: the harvest pools, the selection (which record carries which claim), the builder, the verifier, the renderer |
| `artefacts/round-notes/` | the round-by-round records, including every instrument defect this study found and the repair applied |

## One command

```bash
cd papers/issue-87
bash reproduce.sh
```

**Expected output** — the last lines are the manifest, and the script fails loudly on any difference:

```
REPRODUCE: ALL GREEN
  manifest of what was compared:
    artefacts/results_digest.json          55 quantities read out of the instruments' own records
    figures/fig1_advantage_map.png         the advantage map (Fig. 1)
    figures/fig2_power_arm.png             the power arm (Fig. 2)
    figures/fig3_metric_structure.png      the metric's structure (Fig. 3)
    manuscript.md                          parts + the rendered bibliography
    artefacts/assembly/assembly-report.txt coverage 169/169, 0 stray keys, 91 bindings
    refgate                                entries 169, 0 not separated, coverage 100.0%, GATE: PASS
```

**Tolerance: exact — byte-identical.** Every artefact the script writes is compared with `cmp` against the
committed copy, and a difference is a failure rather than a drift. The script prints the **head it was run at**
(a run is evidence about the version it ran on and no other), keeps its comparison copies in a scratch directory
it removes on exit, and documents the one thing an exact comparison owes a reader: the digest, the manuscript and
the assembly report are written **in place**, so a *failed* comparison leaves the regenerated file in the tree —
the committed copy is what the run is measured against, and `git checkout -- <file>` puts the head back. No tolerance is needed for the numbers
themselves: the study is exact statevector simulation with fixed seeds — no sampling, no noise model, no clock,
no network, no GPU.

## The build the tolerance is read against

A tolerance is a statement about a build, so both interpreters and the versions of the dependencies whose values
enter the comparison are named here and printed by `reproduce.sh`:

| role | interpreter | versions |
|------|-------------|----------|
| digest, figures, manuscript assembly, and the instruments themselves | `/usr/bin/python3` | Python 3.9.6, numpy **2.0.2**, matplotlib **3.9.4** |
| the journal's gates (`.github/tools/*.py`) | `~/.local/bin/python3.12` | Python **3.12.12** (the gates' fixtures use f-string forms the system interpreter cannot parse) |

`numpy` enters every number (the simulator's linear algebra, `eigvalsh`, the least-squares metric fit), and
`matplotlib` enters the figure bytes. The digest's JSON is dumped with `sort_keys=True`, so byte-identity is a
statement about values rather than about dict ordering.

## What the one command does and does not recompute

- **Recomputed from the committed records:** the digest, the three figures, the manuscript, the assembly report,
  and the four journal gates' readings over the built manuscript.
- **Read as committed records:** the instruments' `*_results.json`. They are the study's evidence, and they are
  re-derivable — see the next section.
- **Not touched at all:** the network reads that built the bibliography (arXiv and Crossref API calls in
  `artefacts/refs/refs_verify_v87.py`) and the gates' own `--selftest` fixtures. A reproduction of a citation
  list is a read of a registry; it needs the network, and it is documented rather than run by default.

## Re-running the science (the instruments)

Every instrument is deterministic and CPU-only; each writes its result JSON beside itself and prints a report
SHA-256 that must match the one below. They are run from `artefacts/instruments/` with `/usr/bin/python3`:

| instrument | what it produced | report SHA-256 (first 8) | wall-clock in the record |
|-----------|------------------|--------------------------|--------------------------|
| `smoke_v5.py` | the generator, the seven arms, the first single-cell read (R391) | `986baa2c` | not recorded |
| `smoke_v6.py` | the phase-convention limb (R392) | `2dfc9794` | not recorded |
| `smoke_v7.py` / `v8.py` / `v9.py` | the null, the FDR layer and the fitted predictive null (R393–R395) | `56db65ad` / `6c7f5c55` / `dc56c90d` | not recorded |
| `smoke_v10.py` | the alignment axis at α ∈ {+1, 0, −1} (R396/R397) | `747504d5` | not recorded |
| `smoke_v11.py` | the cross-band profile check (R397) | `4a85f223` | not recorded |
| `smoke_v12.py` | the base map at α = ±1 and the six-axis handicap ladder (R398) | `a3b8d5d0` | not recorded |
| `smoke_v13.py` | the path stratum, the metric's structure test, the PSD repair (R399) | `49e7659e` | not recorded |
| `smoke_v14.py` | the fallback clause through the calibrated predictive null (R400) | `5a43b19c` | not recorded |
| `smoke_v15.py` | the q = 8 cell (R401) | `2317774c` | not recorded |
| `smoke_v16.py` | the **k = 5 stream panel** — the headline's error bars and Q1–Q6 (R402) | `861285cb` | **0.8 min per q = 6 map, 4.5 min per q = 8 map** (measured when the panel was planned; five of each) |
| `r402_drawspread.py` | the Q5 repair: the panel's stream sd against a matched draw-spread denominator | see `r402_drawspread.log` | not recorded |

The instruments' wall-clock is not in the record except where a round needed it for planning (the panel above),
and no runtime is asserted here that was not measured: a reader re-running them measures their own.

`smoke_v0.py` … `smoke_v4.py` build the instrument itself (the exact simulator, the closed-form metric, the
per-point metric field) and carry no report hash; their claims are re-derived by the controls of the later
instruments rather than re-run here (C1 of `smoke_v12.py` reproduces the matched kernel exactly, C7 of
`smoke_v13.py` reproduces 576 committed cells exactly, C2 of `smoke_v16.py` reproduces the committed q = 8
record bit-for-bit).

**Seeds.** Every stream is a declared integer and every seed range is disjoint from every other round's:
the base map and the ladder draw targets from seed stream `500000` with `N_TARGET = 6` draws × `50` splits per
cell; the alignment instrument uses `SEED_GEN = 20260921` with `6 × 50`; the panel's five streams start at
`1100003, 1210007, 1320011, 1430017, 1540021` with stride `110000` (checked disjoint by arithmetic, control
C5a) and `40` splits each; the null draws use `60` cells per band with `20 000` simulations per cell. A stream
re-draws the planted target, the label noise and the train/test permutations; the metric fields, the kernels and
the rival are deterministic functions of the band, so the stream is exactly the sampling unit a per-cell average
hides.

## How the numbers in the text are held to the artefacts

`manuscript.md` is generated: the four authored parts are concatenated with the rendered bibliography, and the
assembly step refuses to build a manuscript whose numbers are not owned by a committed artefact. Its three
checks, printed by `reproduce.sh` and recorded in `artefacts/assembly/assembly-report.txt`:

1. **coverage** — every one of the 169 bibliography entries is cited in the body by its own key (169/169);
2. **stray keys** — every in-text bracket group that looks like a citation names an entry (none stray);
3. **bindings** — each of the 91 numeric claims in the prose is read out of `results_digest.json` and required to
   appear as the manuscript prints it. A number typed by hand instead of read, or left stale by a later edit,
   fails the build.

The digest is itself checked the same way in the other direction: every entry names the file and the field it
was read from (`{ "value": …, "from": "smoke_v16_results.json", "path": "cells[…]" }`), and a field that is
absent is a hard error rather than a default.

## Reference pipeline

`reference-check.md` carries the authenticity report: for every entry, the method used (arXiv API by id, or
Crossref by DOI), the record returned, and the statement that the record is the work the entry names — with
the instrument's own controls on the record (a known-present arXiv id and DOI found; a known-absent pair
reported NOT FOUND rather than retried; a corrupted title detected as a mismatch). The journal's gate was run
over the built manuscript and its whole output read:

```
entries=169  numbering=[n]
block form: 169 entries, 0 of them not separated from the entry above by a blank line
author form: 169/169 entry(s) carry the read's window; 0 print the family name ALL-CAPS, 0 carry a character reference
in-text cited numbers=169  covered=169/169  coverage=100.0%
GATE: PASS
```

`refgate.py --selftest` was run before that verdict was used (41/41 cases), as were `numgate.py` (17/17),
`linkgate.py` (12/12) and `pointgate.py` (20/20).

## Disclosure

- **Contribution level: `theory + empirics`** — a controlled model with ground truth by construction (the Bayes
  predictor is known, so every number is an excess risk over it), a fitted-metric rival built from a published
  closed form, a six-axis handicap audit that can fail, and a calibrated declaration procedure whose size is
  validated on a holdout null.
- **Not a pipeline reuse.** This study is not the journal's census family: the instrument (exact statevector
  simulation of an entangling map, a metric-matched classical rival, a swept-alignment generator) is built here,
  and no census corpus, classifier or head-SHA-pinned repository set is reused.
- **What the package carries honestly:** the matched rival is a *mean*-matched proxy for a metric that is a
  field (§7 of the manuscript); the alignment sign inversion at α = 0 rests on a single instrument and not on the
  five-stream panel; the two-point qubit-count trend is not extrapolated; and the instrument defects this study
  found (the oracle at λ ≈ 0, a metric copied without its bandwidth argument, a PSD violation the second graph
  exposed, a mis-specified variance inequality repaired post hoc, a `hash()` whose per-process randomisation would
  have failed a determinism control) are all in `artefacts/round-notes/` with their repairs.
