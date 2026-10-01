# Issue #87 — R397 notes: is the null's dispersion transferable across seed blocks?

Scripts (all in `papers/issue-87/research/`, re-runnable, byte-identical):
`smoke_v11.py` (+ `smoke_v11_fresh_cache.json`) · `r397_identity.py` · `r397_joint.py`

## What R396 left open

R396 found the null's dispersion differed between the 40-draw calibration block and the 20-draw validation
block (median ratio **1.44**, 11 of 12 bands above 1, sign test p = 0.006) and judged that gap against a
reference **drawn from the fitted null** — which carries the fitted family's tail weight by construction, so
it could not separate "real heterogeneity" from "the fitted family is too light-tailed". Its leading
mechanism candidate was **seed-index drift**. R397's job: settle it with no parametric assumption anywhere.

## What R397 did

| read | what it measures | result |
|---|---|---|
| F1 identity | one stored R396 cell reproduced through **this** generator | `-0.054373153373` = `-0.054373153373` — exact |
| F2 | 60 **fresh** cells per band at a third seed stream (30000 + 97i), pooled to 120/band | done, cached (`smoke_v11_fresh_cache.json`) |
| F3 | the observed cal/val ratio against a **non-parametric** reference (random 40/20 partitions of the pooled 120) | median 1.44, 11/12 above 1, per-band p 0.013–0.75, independence-priced count p = 0.0063 / 0.0067 |
| F4 | the same question on **fresh blocks only** (no part in R396's finding): three 20-cell blocks → three pairwise ratios per band | ratios span **0.53–2.01**, mean percentile 0.23–0.83, 12-band mean **0.47** — exchangeable |
| F5 | does dispersion drift with the **seed index** (R396's candidate mechanism)? | **No.** all \|ρ\| < 0.2, all permutation p > 0.13; half-split ratios 0.61–1.28 both directions |
| F6 | how many draws a stable dispersion estimate needs | n=10 width 1.02× median, n=20 0.69×, **n=40 0.49×**, n=80 0.34× |
| F7 | consequence: predictive null rebuilt from the pooled population | **26 declared (11 leads)** vs R396's 24 (9 leads) |
| S1 identity (whole blocks) | are the two stored blocks what this generator produces, **cell by cell**? | 4 bands × (40 cal + 20 val) = **240/240 exact**, worst \|diff\| 0.000e+00 |
| S2 (F8) joint count | the 11/12 count priced under the **design's own dependence** | profile-permutation p = **0.0321** (null count mean 6.19, sd 2.42, 5–95% [2, 10]); fresh-stream control: count 8/12, p = 0.327; pooled 180-cell population p = 0.0419 |

**Design note.** The per-band *ratio* test was calibrated first (`r397_calib.py`, 400 reps): size 0.055
(doubled tail) / 0.058 (percentile interval), power 0.82 for a 2× dispersion difference and 0.43 for 1.5× —
so the ratio test itself is usable, but F8's cross-band count is the read that decides the round, and F8 is
what pulled the count's significance back to p = 0.0321.

## Verdict

**The gap is a realised block-to-block draw, not a mechanism.** Three independent lines say so:

1. **Construction is not the explanation** — every one of 240 cells across four bands reproduces exactly, so
   the cal/val gap is not a stored-file provenance artefact (the cheapest alternative, now excluded).
2. **Drift is not the explanation** — no band shows a seed-index trend (all p > 0.13), and the fresh stream's
   own block ratios straddle 1 in both directions (F4).
3. **The significance was overstated by the count, not by the effect** — the twelve bands are *not* twelve
   independent reads: one split permutation and one noise vector are drawn per **seed** and reused by every
   band (cross-band mean pairwise correlation of \|dev\| profiles **0.129**, vs 0.122 in the fresh stream).
   Permuting the shared unit consistently across bands widens the null count (sd 2.42 vs 1.73 under
   independence) and moves the same observed count from p = 0.0067 to **p = 0.0321** — a ≈5× inflation, which
   is the ratio of the two null sds squared.

A weak residual survives (11/12, p ≈ 0.03–0.04 also on the pooled 180-cell population), so the honest
statement is *weak evidence of a cal/val dispersion difference, unexplained by drift or construction and
negligible in consequence* (F7: 26 vs 24 declarations; the cells that move are the small-\|δ\| ones).

**The usable form of the result** is F6's curve, not the ratio: a band built from 40 draws carries ≈±25%
dispersion uncertainty, so a band is **not transferable** between seed blocks at this size; 80 draws halve
the width (0.49× → 0.34×), and pooling does better still.

## Determinism

`smoke_v11.py` report sha `4a85f2230f6a227549a23fac898c4fb364793cbffdc4a7d4d58056d289af6e46` on the first
run and on the rerun (file sha `d029be4fa0d894cc3d3cc6002e931ba2026f5e95aab9205693700d0071fcff08`).
`r397_joint.py` sha `0ee9da8669e18073c84ae29a9c0aa106bf81b7d8bc5b1b7c833923dfa275c548` (rerun identical).
`r397_identity.py` sha `2424ab1af91e3e2871447eb57ed4b73da50df020a1cb9738425b885d10846c2f`.

## Cost paid to get here (recorded because it is a pattern)

Three crashes, each costing a full repayment of a ~5-minute deterministic population: `json.loads(file_obj)`
without `.read()`; `fit_shape_pooled` returning a **dict** where the call site unpacked a pair; and a missing
`import smoke_v7 as S7` that my own cross-module audit missed because the audit only checked modules that
*were* imported. The audit now also reports **declared-vs-used** aliases, and the fresh population is cached
so a late-stage crash no longer repays it.
