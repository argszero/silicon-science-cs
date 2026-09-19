# Issue #50 — When Does Speculative Tool Execution Pay? Contention Boundaries, Latency Tails, and the Parallelism the Serial Baseline Already Had

Reproduction package for the manuscript in this directory. Every number the paper cites is **computed
from a committed artefact** by `assemble.py`: a measurement in the prose is a `{{fact}}` placeholder,
the fact is built from a JSON artefact under `artefacts/`, and a placeholder that cannot be resolved
fails the assembly rather than printing an empty string. The four figures are written by
`figures/make_figures_v1.py` from the same artefacts, and `manuscript_check_v1.py` binds the prose's
*words* — the registered verdicts, the section references, the figures, and the headline measurements —
to the objects that own them.

**Contribution level declared: `theory + empirics`** — a construct (`rho*(A, h)`), an instrument that
computes it, a decomposition, and registered predictions tested against the instrument's own output; the
external limb reads three published systems' own reported numbers and is described as three cells, not
as a population.

## Reproduce

```bash
bash reproduce.sh          # every step: the twelve sweeps, then the manuscript layer
bash reproduce.sh fast     # the four sweeps that finish in seconds — a declared PARTIAL run
```

**Dependencies: the Python standard library only** — no numpy, no scipy, no matplotlib, no network for
any step that must pass. `sys.stdlib_module_names` is read by the assembly (3.2 below), so the floor is
**Python 3.10+**; the runs recorded here were taken on **CPython 3.13.9**.

**Tolerance: byte-identical, not "close enough".** Each sweep is re-run from the command that sweep's
own artefact records and compared byte for byte with the committed file; the figures are regenerated and
compared byte for byte; the reference-check report is re-rendered and compared byte for byte. **No
wall-clock tolerance is claimed**: the runtime is a coordinate of the machine that ran it, so the check
is on the printed verdicts and on every measurement, never on how long it took.

The verdict of every step, and the exit status, as the full run prints them:

```
rebuilding 12 artefact(s)  (the twelve sweeps, in the order listed by --list)
REBUILD: 12 of 12 byte-identical, 0 differing
  instrument sweeps: OK
  sweep-comparison liveness: OK
  manuscript assembly: OK
  bibliography writers: OK
  reference-check report: OK
  journal reference gate: OK
  journal link gate: OK
  figure bytes and liveness: OK
  manuscript claims and liveness: OK
verdict: OK
REPRODUCE: ALL GREEN
```

The partial run prints the same verdicts, with `REBUILD: 4 of 4 byte-identical` in place of the
first two lines, and reaches `REPRODUCE: ALL GREEN` as well. On this machine the full run takes about
**thirty minutes** on one CPU core and the `fast` run **about ten seconds**; the sweeps are CPU-only and
independent of the clock, the working directory and the process id, which is why the byte comparison is a
check rather than a hope.

Step 10 prints the sha256 of every file this package ships. That block is **not** quoted here, and the
reason is a rule this package applies to itself: the block contains this file's own digest, so quoting it
would make the README stale the moment the README changed. Copy it from the run; never type it.

**Failure is attributable.** Each step exits non-zero with the object it read and the property that
failed: the sweeps step names the artefact whose bytes moved (with both digests), the assembly names the
unresolved fact, the bibliography writers name the entry, the claim check names the criterion and the
paragraph or the typed literal, and the figure check names the figure and the value planted in it.

**Declared outputs, and nothing written outside the package.** `artefacts/*.json` are the evidence;
`manuscript.md` is the assembled body plus the rendered bibliography; `refs_order.json`,
`references.json` and `refs_display.json` are the reference layer; `reference-check.md` is the citation
report; `figures/*.svg` are the figures. `reproduce.sh` uses one scratch directory inside the package
(`.repro-scratch/`) and removes it at the end; no step mutates the evidence it reads.

## The steps, and what each one is for

| step | object it reads | what it proves |
|---|---|---|
| 1 `rebuild_artefacts_v1.py --rebuild` | `artefacts/*.py`, `artefacts/*.json` | each sweep re-run from the command **derived from its own recorded parameters** returns byte-identical output |
| 2 `rebuild_artefacts_v1.py --selftest` | the comparison itself | the comparison reports a rebuilt file identical **and** a moved file different |
| 3 `assemble.py --check` | the parts, the artefacts | the committed manuscript is what the evidence produces; 137 citations numbered in first-use order; 0 uncited entries |
| 4 `refs_build_display.py --check`, `refs_render.py --check` | `artefacts/refs_selection_v50.json`, `artefacts/refs_verified_v50.json` | both bibliography writers reproduce, and the citation order matches the body |
| 5 `artefacts/refs_verify_v50.py --report` | `artefacts/refs_verified_v50.json` | `reference-check.md` is a **rendering** of the verification artefact, byte for byte |
| 6 `.github/tools/refgate.py` | `manuscript.md` | `GATE: PASS`, 137/137 entries cited — *skipped with a reason* if this package is read as a path-limited export (see below) |
| 7 `.github/tools/linkgate.py --check` | every tracked markdown carrier | `broken=0` |
| 8 `figures/make_figures_v1.py --check/--selftest` | `artefacts/*.json` | 4 of 4 figures regenerate byte-identically; one planted change per figure moves its figure |
| 9 `manuscript_check_v1.py` + `--selftest` | the parts, `manuscript.md`, the artefacts | the registered verdicts are the ones the artefacts decided; every section reference resolves; every figure is reachable and pointed at; no headline measurement is typed into the prose; the criteria the artefacts mark unmet are the ones the summary states as unmet, with the count quoted through its own placeholder — each with a planted defect that must be reported |
| 10 `readme_check_v1.py` + `--selftest` | this README, and the objects that own its numbers | the file count, the module count, the reference layer, the figures and the sweeps are their owners' values — one planted defect per claim |

Steps 6 and 7 read the journal's tools from **this tree** (`.github/tools/`, two directories up). A
path-limited export of the package carries no `.github/`, so where the tool is absent the step prints
`NOT RUN` **with that reason**, the summary counts it under `steps NOT RUN`, and it is not counted as a
pass. In the tree this package was submitted from, both ran and both passed; their own output is what
steps 6 and 7 print, and their verdicts are in the run block above.

## The figures

| figure | what it draws | the artefact that owns every coordinate |
|---|---|---|
| `fig1_boundary.svg` | mean per-step benefit against measured contention at `h = 1.0`, six pool sizes, each family's located crossing marked | `artefacts/boundary_v2_h100.json` |
| `fig2_tail.svg` | the registered tail claim, refuted: mean-matched heavy and light classes, paired by seed, with the paired difference | `artefacts/tail_v1_h100.json` |
| `fig3_prediction.svg` | `F`, and the blind arm's share `1 - F`, against the speculation width `h` | `artefacts/variant_v1.json` |
| `fig4_mixture.svg` | the step-level reading at the cells straddling each family's crossing: the share of steps whose benefit is negative | `artefacts/sideeffect_v1.json` |

The figures are **SVG written by a script in this package** rather than plotted through a library: the
package's claim is that it needs a Python interpreter and nothing else (6.2), and a figure drawn through
a library would make both that claim and the byte comparison false. `--facts` prints every value the
four figures draw, so a reader can bind the picture to the JSON without reading the drawing code.

## What the first full rebuild found

Running step 1 over all twelve sweeps for the first time found that **ten reproduced byte-identically and
two did not** — `boundary_v2_h090.json` and `boundary_v2_h100.json`. The difference was not a
measurement: every measured leaf of both files agreed, and the only differing path was the top-level
`extend` key, which the current `boundary_v2.py` always writes and which those two committed records did
not carry (14 bytes each) — they had been written by an earlier revision of the script. Both records were
regenerated by this script's own derived commands, so the committed bytes are now what the committed code
produces; the paper's numbers did not move, because no measured leaf moved.

The sweeps' exact invocations were, until this round, in the research notes and in the author's memory and
**nowhere in the package**. One of them could not have been reconstructed from the script's defaults at
all: `boundary_v2_h050.json` was produced with `--extend 3`, and a default run reproduces the same schema
with a different extent (163,062 B against 221,526 B, `c_range` [2,5] instead of [1,5]).
`rebuild_artefacts_v1.py --list` prints the derived command for each artefact, and derives it by reading
the parameters the artefact records rather than by typing it.

## Files

- `manuscript.md` — the assembled paper (body + rendered bibliography); `manuscript_part1..4.md` are the
  parts it is assembled from, and they are the carrier the claim check reads.
- `assemble.py` — resolves every measurement and numbers every citation.
- `refs_build_display.py`, `refs_render.py`, `refs_order.json`, `references.json`, `refs_display.json` —
  the reference layer: 137 entries, each cited, each rendered from the record that was read.
- `reference-check.md` — the citation authenticity report: every entry verified against its live record
  (arXiv or Crossref), with the query form, the control and the record found; written by
  `artefacts/refs_verify_v50.py`, which is the **shipped** copy of the instrument that produced it (the
  report names that path, not the git-ignored research workspace it was developed in).
- `rebuild_artefacts_v1.py`, `manuscript_check_v1.py`, `figures/make_figures_v1.py`, `reproduce.sh` — the
  checks and the one command; each has a `--selftest` that plants a defect it must report.
- `artefacts/` — 44 files, the instrument's scripts and the JSON evidence every number comes from. The
  scripts import 27 modules in total, **none outside the standard library and none outside this
  directory** (read by parsing the sources, in 6.2).
- `research/` — the git-ignored design workspace (notes, registrations, drafts). It is **not** needed to
  reproduce anything here.
