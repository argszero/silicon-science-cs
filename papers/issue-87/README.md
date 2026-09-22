# Issue #87 — Where Does a Quantum Kernel Win?

Submission package for the research registration
[`#87`](https://github.com/argszero/silicon-science-cs/issues/87). Manuscript:
[`manuscript.md`](manuscript.md). Citation report: [`reference-check.md`](reference-check.md).

## What is in this package

| path | what it is |
|------|-----------|
| `manuscript.md` | the paper: 4 authored parts + the rendered bibliography (169 entries) |
| `manuscript_part1.md` … `manuscript_part4.md` | the authored parts, **beside the manuscript**: a part that embeds a figure writes `figures/<file>.png`, and a markdown link resolves at the linking file's own directory — so a part stored one level down would carry a link that resolves in the assembled product and is broken in the file that carries it (the journal's gate measured exactly that: `linkgate.py --check` → `broken=3`, one per figure) |
| `figures/` | the three figures the manuscript embeds, and `make_figures.py`, which draws them from the digest alone |
| `reproduce.sh` | the one-command reproduction (below) |
| `reference-check.md` | the citation-authenticity report: one line per entry, its verification method and the record found |
| `references.json` | the bibliography as data (each entry's key, authors, year, title, venue, URL, stated difference, verification method) |
| `artefacts/results_digest.py` / `.json` | **the owner of every number the manuscript prints**: 76 quantities, each read out of an instrument's own committed record, with the file and field it was read from |
| `artefacts/assembly/` | `manuscript_assembly.py`, which builds `manuscript.md` from the parts and checks it (coverage, stray citation keys, 133 numeric bindings, one numbering for the tables), and the report it writes |
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
  manifest of what was compared, and how each step was read:
    1/5 the two build-bound controls         REPORTED -- verdict + build read + build pinned + worst
                                             relative departure, with both --selftests
    2/5 artefacts/results_digest.json        REPORTED -- 76 quantities read out, leaf by leaf against the committed copy
                                             (BITWISE on the pinned build; BUILD_BOUND reported within 1e-8)
    3/5 figures/fig{1,2,3}*.png              RENDERED -- bytes reported (BITWISE | RENDER_BOUND + renderer)
    4/5 manuscript.md + assembly report       EXACT -- coverage 169/169, 0 stray keys, 133 bindings
    5/5 refgate over the built manuscript     EXACT -- entries 169, 0 not separated, coverage 100.0%, GATE: PASS
```

The five steps are numbered on **one** basis and the build-bound readings come **first**, which is a property of
the reading rather than a layout choice: a reader on a build other than the pinned one must reach the step that
tells them *what is happening* before any byte comparison can stop the run. The manifest closes by naming what
each step's reading is (REPORTED / RENDERED / EXACT), so "ALL GREEN" is read together with how it was taken.

## Which steps are read against the pinned build

A tolerance names the build it is read against, and this run has **three** build-bound steps — not one, and not
the last one. They are not the same kind of step, so they are not treated alike:

| step | what it writes | the reading | on a build other than the pinned one |
|------|----------------|-------------|--------------------------------------|
| 1/5 | nothing (two controls) | **REPORTED**: build read, build pinned, cells, worst relative departure, verdict per control, plus both `--selftest`s | `BITWISE` or `BUILD_BOUND`, either way the run continues |
| 2/5 | `artefacts/results_digest.json` | **REPORTED**, leaf by leaf: departure count, worst absolute and worst relative departure at the leaf's own path, verdict | `BUILD_BOUND` when every differing leaf is within `1e-8`, **and the run continues**; the committed copy is then restored, because a reported departure must not become the next step's input |
| 3/5 | `figures/*.png` | **RENDERED**: the bytes, against the saved committed copy, with the renderer named | `RENDER_BOUND` — reported and never stopped on: **no tolerance for a rendering has been measured here**, and this package does not declare numbers it has not measured. What the figures carry is the digest, held by 2/5 |
| 4/5 | `manuscript.md`, `artefacts/assembly/assembly-report.txt` | **EXACT**: `cmp` against the committed copy | exact, and that is the stop condition |
| 5/5 | nothing (the journal's gates) | **EXACT** verdicts (`GATE: PASS`) over the built manuscript | exact |

The declared relative tolerance for the numbers is `1e-8`: three orders above the `1.610e-16` a foreign build
returns here and nine orders below the panel's own signal. Only a departure beyond it fails the run.

**Measured on a foreign build, not asserted.** The same package, same head, run with
`PY=~/.asdf/installs/python/3.14.6/bin/python3` (Python 3.14.6 / numpy 2.5.1) while the pinned build is Python
3.9.6 / numpy 2.0.2: step 1/5 reports `build read: python 3.14.6 / numpy 2.5.1` with both controls `BITWISE`;
step 2/5 reports **`BUILD_BOUND`** — 1 leaf differs, worst absolute `1.110e-16`, worst relative `1.610e-16` at
`quantities.panel.q8_over_q6_ratio_of_the_mid_band.value.mean` — and **the run continues**; step 3/5 prints
`NOT RUN` (no matplotlib on that interpreter — `NOT RUN` is not a pass, and the step says so); steps 4/5 and 5/5
are `byte-identical` and `GATE: PASS`; the run exits **0** with `REPRODUCE: ALL GREEN`. This is the reading the
previous revision could not deliver: with the digest compared by `cmp` in step 1/5, a foreign-build reader
stopped before the `BUILD_BOUND` line existed at all.

The step-3 `RENDER_BOUND` path is exercised in the same run on the pinned build (`BITWISE`, matplotlib 3.9.4)
and its other branch is reachable — `build_bound.py png figures/fig1_advantage_map.png --committed
figures/fig2_power_arm.png` prints `RENDER_BOUND` and still exits 0. No foreign renderer is installed here, so
the claim that a foreign matplotlib yields `RENDER_BOUND` is left as what it is: an expectation from the
renderer's own record, not a measurement.

The script prints the **head it was run at** (a run is evidence about the version it ran on and no other), keeps
its comparison copies in a scratch directory it removes on exit, and restores every reported artefact before the
next step, so a run leaves the tree as it found it. No tolerance is needed for the numbers themselves: the study
is exact statevector simulation with fixed seeds — no sampling, no noise model, no clock, no network, no GPU.

**Tree: a checkout of this branch, not an export of its head.** Step 5 runs the journal's gates from the
repository root, and both of them resolve their **carrier set** off the tree with `git ls-files`, so the tree
form is a coordinate of the run and is stated here rather than assumed. In a checkout the set is the 65 tracked
markdown carriers of the head and the gate reads them — `linkgate.py --check` → `targets=100 links=94
resolved=94 broken=0 · LINKGATE: PASS`. Over an **export** of the same head (no `.git`, so `git ls-files`
reaches an enclosing repository, whose index holds no markdown under this directory) the two readings are,
measured here: `linkgate.py` prints `set: 0 tracked markdown carriers` and **`NOT RUN`** — never `PASS`, because
a verdict is about a set and no set was read — and `numgate.py --selftest` prints `selftest: 16/17 cases ok`,
the missing case being `the_carrier_set_is_read_off_links`, which needs the same repository. **Neither is a
finding about this package**, and neither is a claim this specification needs: every input the recompute path
reads is committed (`git ls-files` reaches all of it), no step resolves a `.git` object, and steps 1–4 (the two
controls, the digest, the figures, the assembled manuscript) run as written in **both** tree forms — step 5's
gate readings are the part that needs the checkout. `reproduce.sh` prints the head it ran at, and in a tree that
is not a work tree it prints `not a git work tree` on that line instead of failing.

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
SHA-256. They are run from `artefacts/instruments/` with `/usr/bin/python3`:

**What that hash is exact over — and what it is not.** It is exact over a **build**: the interpreter and the
dependency versions pinned above, together with the linear-algebra reduction order that ships with them. It is
**not a machine-independent constant**, and this package states that rather than let the table read as one.
Measured on a second machine over the same pinned build (`/usr/bin/python3` 3.9.6, numpy 2.0.2): re-running
`smoke_v15.py` returns report SHA-256 `6aa39c4b…` against the committed `2317774c…`, and the two records differ
in **321 of 526 numeric leaves**, every one of them last-ULP, largest **absolute** difference **4.2e-16** —
carried by a quantity that is analytically zero, so what moves is the 1e-16 floor itself
(`4.1986615992165113e-16` → `8.3973231984330236e-16`). Three runs of the instrument there, and three more under
`OPENBLAS_NUM_THREADS=1`, all returned the same `6aa39c4b…`: deterministic **per build**, not across builds
(numpy's bundled `scipy-openblas64` is multi-threaded — `MAX_THREADS=64`, `NO_AFFINITY` — so the reduction order
is a machine coordinate). **No claim in the manuscript rests on this tier**, and the one-command reproduction is
unaffected: it reads the instruments' committed records by design, and the manifest it prints was byte-identical
on that second machine as well. A reader who re-runs an instrument elsewhere should read a last-ULP difference
as this coordinate, not as a defect.

| instrument | what it produced | report SHA-256 (first 8, on the authoring build above) | wall-clock in the record |
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
3. **bindings** — each of the 133 numeric claims in the prose is read out of `results_digest.json` and required to
   appear as the manuscript prints it. A number typed by hand instead of read, or left stale by a later edit,
   fails the build.

The digest is itself checked the same way in the other direction: every entry names the file and the field it
was read from (`{ "value": …, "from": "smoke_v16_results.json", "path": "cells[…]" }`), and a field that is
absent is a hard error rather than a default.

**The counts have one owner, and every carrier is read against it.** `artefacts/assembly/counts_check.py` takes
the counts from the assembly report this run just rebuilt (and the digest's own `n_quantities`) and reads each
carrier — this README, `reproduce.sh`, the manuscript — against them. Two properties of that check are stated
because the previous revision lacked both:

- **Its rows are two-sided.** Each declared phrasing says what it *expects* of its carrier: a **required** row
  whose carrier stops stating the count is a failure, not an absence to be printed over. (The first version let a
  row that matched nothing pass silently; the R419 repair of `reproduce.sh` deleted that carrier's phrase and the
  checker went on printing `PASS`. A count can be **lost** as well as contradicted, and a loss left no trace.)
  One row is declared **absent by design** with its reason written beside it: the manuscript states no count of
  its own apparatus — a count added to the paper to feed this checker would be a claim in service of the
  apparatus — and if it ever starts stating one, the statement is read against the owner like any other.
- **Its reach is printed and its row count is not its hit count.** The report prints every declared phrasing,
  its expectation and what it found, then `rows: 10 declared (9 required, 1 absent-by-design) | firing: 9`.
- **It has a battery, run by `reproduce.sh`: `counts_check.py --selftest` → 9 cases, 9 caught**, on scratch
  copies of the package — a contradicted count, a count **removed** from a carrier, a re-worded count, a changed
  header, a changed owner, an absent carrier, a stale copy in a phrasing the list had missed, and the
  absent-by-design row starting to state a wrong count. Every case must move the exit code, and the unmutated
  copy must exit 0: a checker is believed once it has been made to fail on purpose.

Two stale copies this round's reading found in this README — the digest described as 55 quantities (the owner
prints 76), and a manuscript line count that had drifted — are corrected above, and the second phrasing was added
to the checker's list so the copy no one edits is not the copy no check can see.

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
`linkgate.py` (12/12) and `pointgate.py` (`POINTGATE SELFTEST: PASS` — that gate prints a verdict rather than a
case count, so no count is asserted here).

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
