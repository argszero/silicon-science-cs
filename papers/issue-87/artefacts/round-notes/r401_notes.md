# Issue #87 — R401 notes: the q = 8 cell

Script `smoke_v15.py`. Comment `5754789036`. Class 94 in `verification-self-audit-lesson.md`.
Report sha `2317774cba975c36980f084fbd287e9db0203327315f910f8a94be8debc6b8c4`.

## Pre-registered (in the script header, before the run)

Q1 ≥20/24 sign agreement with the q = 6 map · Q2 aliveness lower at q = 8 in every band, drop largest in the
middle band · Q3 matched-vs-isotropic-RBF separation ≤0.02 · Q4 the four main-claim cells still ≥0.25 under the
random-metric handicap.

## Outcome

| Q | prediction | result |
|---|---|---|
| Q1 | ≥20/24 signs | **19/24** — not met as written; **8/8 in the structure cells** (\|q6 δ\| ≥ 0.1), 11/16 among near-zero cells; all 5 flips have \|δ\| ≤ 0.035 in BOTH streams |
| Q2a | aliveness lower in every band | **12/12 CONFIRMED** (0.053→0.021 at shifted γ = 0.5; 0.967→0.957 at unshifted γ = 0.1) |
| Q2b | drop largest in the middle band | **not supported** — largest drop 0.0928 (unshifted γ = 0.5) is tied with γ = 3 (0.0913/0.0912) |
| Q3 | ≤ 0.02 | **CONFIRMED on three reads**: −0.0187 (R391, shifted, 12 cells) / −0.0047 (R398 instrument, 24 cells) / +0.0020 (this round) |
| Q4 | 4 cells ≥ 0.25 under the random metric | **4 of 8 readings** — matched → random: 0.332→0.284, 0.335→0.286, 0.278→0.243, 0.279→0.247, 0.321→0.287, 0.316→0.284, 0.255→0.221, 0.248→0.214 |

## New facts this round

1. **Structure is stable, near-zero signs are not.** At q = 8 the matched rival still dominates the middle band
   and the quantum kernel leads in 6 of 24 cells (vs 11 of 24 at q = 6) — the leads concentrate at the extremes
   (γ = 3 both conventions, unshifted γ = 0.1).
2. **The gap attenuates ~30 % with the qubit count.** shifted|1 +0.448→+0.279; unshifted|2 +0.419→+0.255;
   shifted|0.5 +0.421→+0.332. Within-stream cell spread is 0.001–0.013 (6 draws), so the attenuation is a q
   effect, not seed noise. **The manuscript must state the q its numbers belong to.**
3. **dq(W) uniformity at q = 8**: cycle 1.7e−15, complete <1e−15, path 6.4e−1 — the R398/R399 mechanism table
   holds at the second dimension.
4. `draw_spread_delta` (between-draw sd, 6 draws) is now reported per cell: ratio |δ|/sd is 23–58 in the
   structure cells and 3 of 24 cells have |δ| < 2 sd — so within a stream every map claim is solid, and the
   cross-q/cross-stream moves above are far outside it.

## The reading error (Class 94) and what caught it

`q6_reference()` (first version) looped `for conv in CONVS` and read R391's rows twice, **inventing an
unshifted column** for a report whose settings declare `convention: "shifted"` and whose cells carry no
convention field. Symptom that caught it: R391's aliveness was *identical* for both conventions — impossible
given R390's own finding that the metric is convention-dependent. The first version of the comment would have
said Q2 was refuted and D invalid.

Fix, and the convention adopted from now on: the primary q = 6 reference is **R398's stream** (same
construction as this round, both conventions); R391 is kept as an explicitly single-convention secondary read;
the q = 6 aliveness used by Q2 is **measured by this round's own code** (`q6_aliveness()`), because no committed
file carries the per-convention quantity.

## Cost / operational

* q = 8 cost model (measured, useful for the manuscript): `metric_field` 1.9 s per band at q = 8 vs 0.08 s at
  q = 6; kernel fit ~0.002 s (quantum) / ~0.017 s (8-envelope rival) per split; a full 12-band × 2-α × 6-draw ×
  40-split × 5-arm map is ~7 min + 70 s for the 3-graph diag table.
* Initial cost estimate was 4× the truth because the first probe (N_TARGET=1, N_SPLITS=5) was dominated by the
  22 s of metric fields, not by the fits — the estimate scaled the wrong term.
* The scoped determinism control needed the band's index in the FULL band list to seed the target; a filtered
  index would have silently changed the target and made the control vacuous. Verified by comparing the full run
  against a filtered rebuild of the same band (identical) before launching.
