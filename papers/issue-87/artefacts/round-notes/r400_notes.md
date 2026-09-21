# Issue #87 — R400 notes: the fallback clause read through the calibrated declaration procedure

Script `smoke_v14.py`. Comment `5754412004`. Class 93 in `verification-self-audit-lesson.md`.
Report sha `5a43b19cff7aa5a6ff8eecc684f648d8c041886e0821697e846e18a0f629995a`.

## What the round had to answer

The registration's risks clause promises a power arm ("would this pipeline have found an advantage if one
existed") and R398/R399 delivered only a **handicap magnitude** (axis C: random-PSD metric, 24/24 effective,
median dR +0.126). This round reads the study's own grid through the **calibrated declaration procedure**
(R396's predictive null) along that axis, which is the clause's own currency.

## Design (and the pre-registered expectations, written before the run)

* null population: 60 cells per band, A = 0, same generator, same 50 splits as the observed cells;
* predictive null per band (pooled shape across a convention's 6 bands, loc+scale per band), N_SIM = 20,000
  ⇒ resolution 1.0e−4, below BH's smallest threshold 2.08e−3 at m = 24;
* observed: 24 cells (12 bands × α = ±1), 6 draws × 50 splits, at 4 axis-C levels;
* BH at q = 0.05 per level; instrument SIZE validated on a holdout (fit on half the null cells, declare on
  the other half).
* Q1 size ≤ 5 % · Q2 8–16 declared at t = 0 · Q3 count non-decreasing in t and materially higher at t = 1 ·
  Q4 resolution finer than BH's threshold.

## Results

| read | result |
|---|---|
| Q1 size (holdout, null by construction) | **0.28 %** (1 of 360) — PASS, and 20× conservative ⇒ counts are lower bounds |
| Q4 resolution | 1.0e−4 < 2.08e−3 — PASS, counts not floor-limited |
| C1 identity vs R398's committed t = 0 cells | 24/24, max \|Δδ\| 1.7e−16 |
| C4 determinism | byte-identical rebuild |
| **Q2 declared at t = 0** | **23/24** — REFUTED (predicted 8–16) |
| **Q3 declarations along t** | 23 → 22 → 24 → 24 — **REFUTED: the count saturates** |
| quantum leads (mean δ < 0) along t | **11 → 12 → 14 → 16 of 24**, 5 cells flip sign |

* The study's own calibrated answer: at the **matched** rival **23 of 24 cells are declared**; the only cell
  indistinguishable from a no-signal cell is `unshifted|0.5|a=−1` (|δ| = 0.0010). The procedure resolves
  |δ| ≈ 0.0025 — ~20× finer than the smallest effect the manuscript discusses (0.05).
* Saturation is explained by measurement, not assertion: the null's within-band dispersion is 0.0013–0.0030,
  two orders below the study's effects (0.01–0.52).
* The clause IS discharged, in the study's own currency: the **lead count** is monotone 11 → 16 with 5 sign
  flips (`shifted|0.25 ±`, `shifted|2 ±`, `unshifted|0.5|a=−1`).
* Headline in sharper form: at t = 1 the quantum kernel still loses by +0.27…+0.32 at `shifted|0.5–1` and
  `unshifted|1–2` — the four bandwidth cells that carry the main claim survive the rival being *badly* matched.
* Measured arm asymmetry: the null's LOCATION is off zero per band (up to ±0.005, tens of standard errors of
  its own mean) — the quantum and matched arms are not exchangeable even with no signal. This is the
  quantified form of R395/R396's "declared ≠ quantum wins".

## Dependence check (R397's rule)

The two α cells of a band share their split/noise draw: within-band correlation of their per-draw δ has
median **+0.19** but reaches **+0.87** (`shifted|0.5`) and **+0.75** (`unshifted|2`). Across bands, cells with
the same α share neither target nor splits: mean pairwise ρ = **+0.04**. So the 24-cell count carries **12
independent split/noise units**; the count is stable under either reading precisely because it saturates.

## Pitfalls

* `hash(key)` in the predictive-seed expression: Python randomises string hashing per process, so the C4
  determinism control would have failed spuriously — replaced by `zlib.crc32`. (A determinism control catches
  this class only if the run is actually repeated; it was, and it now passes byte-identically.)
* The first probe compared ONE draw against R398's SIX-draw mean and looked like an identity failure
  (0.4273 vs 0.4213). The comparison had to be like-for-like (6-draw mean → 5.6e−17). A near-miss like this
  is exactly how a real identity failure gets dismissed as "floating point".
* The null statistic's units differ from R397's by a factor σ² (absolute MSE vs noise-variance units) — noted
  because the two rounds' bands are not directly comparable and a future reader will otherwise try.

## Next

q = 8 (the map rests on one qubit count), then Phase B assembly.
