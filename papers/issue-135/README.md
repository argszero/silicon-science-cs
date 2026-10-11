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
  (six SVGs + `FIGURES.md` + `CAPTIONS.md` + `manifest.json`) are compared byte-for-byte too.
* **Environment**: CPython 3 (measured on **3.12.12** and **3.13.9**, macOS). The instruments are pure
  standard library (`json`/`math`/`os`/`sys`) — **no third-party dependency is imported**, so no library
  version enters a comparison. Override with `PYTHON=/path/to/python3`.
* **Inputs**: none, and no network. Every key set is generated from the committed `SplitMix64` seeds
  inside the instruments; a run touches nothing outside its own directory.
* **Cost**: about **four minutes** (four instruments, each re-run once, plus the batteries and
  the figure certificate).
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
