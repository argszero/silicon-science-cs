# Issue #135 — The Load Factor Is Not the Tail

**Contribution level: `theory+empirics`.** This package is the evidence layer for the manuscript: four
instruments, each with its own plant battery, and the reports every manuscript number is read from.
Ground truth is **by construction** — the table state *is* the ground truth and every probe is an exact
integer count, so each reported quantity is a count, a rate over a named denominator, or an
exact-integer-derived moment. There are no timings anywhere in the package.

## Reproduction

```
cd papers/issue-135 && bash reproduce.sh
```

* **Expected output**: `REPRODUCE: ALL GREEN`, preceded by one line per check. Each of the four
  instruments prints `SELFTEST n/n` (8/8, 13/13, 9/9, 6/6) and then its report is compared
  **byte-for-byte** (`Tolerance: exact`) against the report this package ships. The figure
  certificate then prints `SELFTEST 10/10 (F1-F5)` and the **nine** generated figure files
  (six SVGs + `FIGURES.md` + `CAPTIONS.md` + `manifest.json`) are compared byte-for-byte too. The
  reference layer then prints `refscan selftest SELFTEST: ALL PASS`, `refscan gate GATE 8/8` and
  `reference-check ... is what this renders`, and a planted change inside the rendered block must
  make `--check` fail. Finally the manuscript is re-rendered (`MANUSCRIPT: MATCH -- 207 references,
  70 numbers ... ytes re-rendered byte-identically`), its plant battery runs
  (`SELFTEST: ALL PLANTS CAUGHT`), and the journal's gates are applied to the built manuscript
  (`refgate ... coverage=100.0%`).
* **Environment**: CPython 3 (measured on **3.12.12** and **3.13.9**, macOS). The instruments are pure
  standard library (`json`/`math`/`os`/`sys`) — **no third-party dependency is imported**, so no library
  version enters a comparison. Override with `PYTHON=/path/to/python3`.
* **Inputs**: none, and no network. Every key set is generated from the committed `SplitMix64` seeds
  inside the instruments; a run touches nothing outside its own directory. (The reference layer's
  *live* verification is a separate, documented network pass — see **Reference layer** below; the
  offline gate re-checks its committed receipt without touching the network.)
* **Cost**: about **five minutes** (four instruments, each re-run once, plus the batteries, the
  figure certificate, the offline reference layer, and the manuscript re-render).
* **Writes nothing inside the package**: each instrument is run with `SPIKE_OUT` pointing into a private
  temp directory the script creates and removes.
* **Second tier**: `REPRO_FULL=1 bash reproduce.sh` re-runs every instrument a second time in a fresh
  process and compares the two fresh artefacts — the determinism certificate (~10 minutes total).

## Layout

| Path | What it is |
|---|---|
| `spike_v0.py` | v0 — the linear-probing arm: the full probe-count distribution against the classical uniform-hashing forms, with a finite-size (`m`-scaling) control **C5** and the across-instance spread **C6** |
| `spike_v1.py` | v1 — **Robin Hood** + the **budget axis `k_max`**: the budget boundary `alpha*(k_max)`, the `MIN_EVENTS` guard, the repaired `chi2_{m-1}` uniformity certificate, the scheme-deviation control **C10** |
| `spike_v2.py` | v2 — the **P2 decision**: the across-instance spread ratio **C11**, the out-of-sample tail prediction **C12**, the p99 resolution guard **C13**, the scheme-invariance of the clustering statistic **C14**, and cross-scheme transport **C15** |
| `spike_v3.py` | v3 — the **theory arm**: three closed forms (**A** mean-based, **B** memoryless, **C** scheme-calibrated) against the measured boundary **C16/C17**, the tail's decay in `k` **C18**, and the calibrated form **C19** |
| `spike_v*_results.json` | The report each instrument emits; every manuscript number is read from one of these |
| `make_figures.py` | The figure set: six SVG figures, `FIGURES.md`, `CAPTIONS.md` and `manifest.json`, generated from the four reports -- standard library only (**matplotlib is not used and is not required**), deterministic, `--selftest` runs the certificate F1-F5 |
| `figures/` | The generated figure set, its captions (from the same run), and the sha256 manifest |
| `refscan135.py` | The reference layer: discovers candidates from arXiv by topic query, verifies the pool against live Crossref/arXiv records, and gates the pool offline (`--gate`) with its own plant battery (`--selftest`) |
| `refs/pool.json` | The verified pool (556 entries) — every manuscript reference comes from here, never from memory |
| `refs/verify-run.txt` | The committed verification receipt: the verbatim stdout of the network pass, naming the pool it verified by sha256 |
| `reference-pool.md` | The per-entry table: key, source, the live endpoint each entry was checked against, and its title |
| `reference-check.md` | The verification report — method, result, the defects found while building the layer, and what the check does **not** establish |
| `make_reference_check.py` | Renders the receipt block of `reference-check.md` from `refs/verify-run.txt`; `--check` proves the committed file is what it renders |
| `refs/differences.json` | One stated difference per cited reference — a citation with no stated difference is padding, and the build refuses to render one |
| `manuscript.src.md` | The manuscript SOURCE: prose with `{{key}}` (a number owned by a report), `{ref:ID}` (a citation owned by the pool) and `{{figN}}` (a figure block) placeholders |
| `manuscript.md` | The manuscript, built from the source by `build_manuscript.py` — every number resolved out of a report, every citation out of the verified pool |
| `build_manuscript.py` | The manuscript builder: resolves all three placeholder kinds and FAILS on an unresolved/unknown/unused one, on a citation off the pool, or on fewer than 100 cited references; `--check` re-renders into memory and compares, `--selftest` plants a defect per check |
| `refgate-journal.txt` | The journal reference gate's verbatim output on the built manuscript (a committed receipt, re-derived and compared byte-for-byte by `reproduce.sh`) |
| `heilmeier.md` | The registration as filed: six Heilmeier answers, adversarial checks, the stated priors, and the round log |

## What each instrument certifies, and where it can fail

Every check carries a **plant** that must fire — a check that cannot fail is decoration, so each
instrument's `--selftest` asserts both that its plants fire *and* that its pure functions return
independently computed values. The plants include, among others: the identity-hash layout must fail the
mean-agreement check (v0) and must show as one contiguous run (v1); a budget that cannot bound must move
`alpha*` the wrong way (v1); a predictor that is **constant across the instances it is supposed to
explain** must come out degenerate rather than to "succeed" (v2); and a super-geometric tail must read
ratio ~2 rather than ~1 (v3).

Two guards encode the same rule the manuscript's reporting follows: an **unresolved cell is not a
measurement**. A crossing whose bracketing cells carry fewer than `MIN_EVENTS` events is reported with
`alpha* = undef` and a reason (`above` the grid ceiling, or `under-resolved`), **never** with a value —
and where it is unbracketed, the load it is bounded by is reported as a bound.

## Figures

`python3 make_figures.py` regenerates `figures/` from the shipped reports (standard library only,
deterministic; `reproduce.sh` does it and compares the nine files byte-for-byte). Nothing is drawn
that is not in a report and every number a figure annotates is read from the report, so a figure
cannot drift from its source; `figures/CAPTIONS.md` is generated in the same run, from the same
values, so the caption cannot drift from the picture either. `make_figures.py --selftest` runs the
certificate F1-F5, which re-derives every fact the figures assert and **reads the emitted geometry
back off the canvas** (F5: 653 coordinates checked, no element outside its figure).

| Figure | What it shows |
|---|---|
| `fig1_budget_boundary.svg` | The boundary `alpha*(k)` for both schemes against the textbook mean rule -- A overstates at every bracketed `k`, and the gap is a hump |
| `fig2_scheme_deviation.svg` | The classical mean form's deviation for both schemes, with the across-seed band: a seed-stable miss vs a seed-noisy one |
| `fig3_finite_size.svg` | The finite-size window: mean \|deviation\| falls monotonically with `m`, while \|mean deviation\| dips by seed cancellation |
| `fig4_tail_decay.svg` | The tail's decay in `k` -- sub-geometric for linear, super-geometric for Robin Hood, on opposite sides of the memoryless line |
| `fig5_closed_forms.svg` | Three closed forms (A/B/C) against the measured boundary: the textbook rule is the worst |
| `fig6_clustering_vs_tail.svg` | The clustering statistic is scheme-invariant (144/144) while the p99 ratio is 2.4-115.8x |

## Reference layer

The manuscript's bibliography is drawn from a **verified pool**, never typed from memory. The layer
has two tiers:

* **Discovery + live verification (network).** `python3 refscan135.py` runs 40 topic queries against
  the arXiv API and looks up 13 canonical works by title against Crossref; `python3 refscan135.py
  --curate` applies a CORE/SUPPORT term filter and resolves duplicate titles; `python3 refscan135.py
  --verify` re-fetches **every** pool entry from its live endpoint and compares the returned title
  with the stored one (two-sided token match, threshold 0.80), writing the verbatim run to the
  receipt `refs/verify-run.txt`. Result: **556 / 556 verified, 0 title mismatch, 0 transport-unknown**.
* **The offline gate (no network).** `python3 refscan135.py --gate` asserts the shipped pool is
  complete and internally consistent — ≥100 entries, no duplicate title, every key its own id, an
  old-style arXiv id keeps its archive prefix, `reference-pool.md` lists exactly the pool, and the
  committed receipt's `POOL sha256` line still matches the shipped `refs/pool.json`. The last check
  is what makes the receipt evidence rather than a quotation: a receipt that outlived its pool fails
  the gate.

`reference-check.md` is the report; `reference-pool.md` is the per-entry table. The verdict is a
**title comparison**, not the HTTP status — a remembered identifier *resolves* to a real record, of
a *different* paper, so the check is the returned title against the stored one. An API outage is
reported as `TRANSPORT-UNKNOWN`, never as "these records do not exist".

## The manuscript

`manuscript.src.md` is the source; `manuscript.md` is the built product. Nothing is typed twice:
`python3 build_manuscript.py` resolves every placeholder in the source —

* `{{key}}` — a **number**, read out of the committed report that owns it (never typed in prose);
* `{ref:ID}` — a **citation**, resolved against the verified pool `refs/pool.json`;
* `{{figN}}` — a **figure block**, assembled from the generated `figures/CAPTIONS.md`, so the caption
  cannot drift from the picture;

— and the build **fails** on each way a number, a citation or a figure can be wrong: a placeholder with no
owner, a declared value that nothing uses (a number that drifted out of the prose), a citation off the
pool, a cited key with no stated difference, fewer than 100 cited references, or a figure whose image is
absent. `--selftest` plants a defect for each of those and requires the build to refuse;
`--check` re-renders into memory and proves the committed `manuscript.md` is exactly what the source
renders. The result: **207 references, all cited in the body** (the journal bar is 100), **70 numbers**,
each read from a report, and every reference entry carrying its title, authors, year, venue, link and a
one-line **stated difference** from this paper.

The journal's own gates run on the built manuscript (they live in `.github/tools/` of the journal repo,
and a run outside a journal checkout reports them as a named `NOT RUN`):

| Gate | What it checks |
|---|---|
| `refgate.py` | the reference block: entry count, numbering, the author form, and **in-text coverage** (every numbered entry cited in the body) — its verbatim output is the committed receipt `refgate-journal.txt` |
| `numgate.py` | the tree's numbered references, by the form each takes |
| `linkgate.py` | every markdown bracket link/image in the manuscript, resolved at the product's own base |
| `pointgate.py` | the tree's named pointers (`-> *Name*`) |

## Findings (the short form)

* **The classical mean form has a finite-SIZE window** and is a statement about **one** scheme. At
  `alpha = 0.95` its seed-averaged absolute deviation falls `0.489` (`m = 4096`) → `0.090` (`m = 65536`)
  — a designer reading the textbook mean at the smaller size is already mis-sizing. Against Robin Hood
  the same form is off by `-0.99` at `alpha = 0.99` with an across-seed spread `<= 0.03`, while the
  linear arm's own deviation is seed-**noisy** (spread `0.03 -> 0.78`).
* **The budget binds far below the mean** — `alpha*(8) = 0.281` against a mean-based load of `0.742` for
  linear probing at a 1e-3 failure budget — and the gap is a **hump** (peak ~0.49 at `k = 4`), not a
  constant.
* **At a fixed load the instance is the level** in the moderate regime (p99-spread / mean-spread up to
  **5.39**), but the tail's free variable is the **lookup rule**, not the layout's clustering: linear and
  Robin Hood fill the **same** slot set (**144 of 144** pairs share the same longest run) while their
  p99 differs by **2.4 – 115.8x**, and a predictor fitted on one scheme does not transport to the other
  (worst relative deviation **1.6 – 113**).
* **The tail's decay in `k` is scheme-specific in form** — sub-geometric for linear probing (ratio
  `0.50 → 0.18` over the load range) and super-geometric (~`a^{2k}`) for Robin Hood — which is why the
  **textbook mean-based rule is the worst of the three closed forms tested**, overstating the safe load
  by `0.21 - 0.50` in the linear|uniform arm at a 1e-3 budget (`0.15 - 0.56` over every linear cell).
