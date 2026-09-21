# Issue #87 — R402 notes: does the advantage map survive re-drawing the noise?

Scripts `smoke_v16.py` (the panel) · `r402_followup.py` (post-run reads + the Q5 repair) ·
`r402_drawspread.py` (addendum: the draw spread at a MATCHED qubit count). Report sha
`861285cb9d593ee95738cae4624cedb771aa1ac928aef1fe4667c0337831248f`.

## Why this round

Every number in the map (R391–R401) rests on ONE seed stream: a cell's delta averages 6 target draws x 40
splits from a single realisation. R396/R397 showed the null blocks' dispersion gap was a REALISED DRAW rather
than a mechanism, so the map's own claims owed the same question — and the submission bar wants multi-run
statistics. R402 runs a **k = 5 stream panel**: five paired (q = 6, q = 8) full 24-cell maps, each under a seed
stream disjoint from every earlier round's and from each other. A stream re-draws the planted target, the label
noise and the train/test permutations; the metric fields, the kernels and the rival are deterministic functions
of the band. Cost: 5 x (0.8 min at q = 6 + ~4.5 min at q = 8) ≈ 30 min.

## Controls (all pass)

| control | result |
|---|---|
| C1 determinism within a stream | q = 6 and q = 8 both **exact**, max \|diff\| 0.000e+00 |
| C2 committed-stream reproduction | the harness at R401's own stream reproduces the committed `smoke_v15_results.json` rows **bit-for-bit** (8 values, 0 mismatches) |
| C2b harvest completeness | R398's q = 6 reference: 24 cells, all finite |
| C3 sign-unanimity instrument | fires (clean 5/5 → one planted flip 4/5) |
| C4 paired-effect instrument | fires (injected −0.10 recovered to 1e−12, resolvable; zero-effect panel **not** resolvable) |
| C5a seed-range disjointness | offset_max 51146 < stride 110000, asserted |
| C5b the streams really differ | max stream spread inside the structure cells 0.0337 > 0.01 |

## Pre-registered outcomes

| Q | prediction | result |
|---|---|---|
| Q1 | structure cells stream-stable (≥7/8 unanimous, sd < 0.05) | **8/8 unanimous at BOTH q**; max sd 0.0145 (q6) / 0.0062 (q8) — **MET** |
| Q2 | ≥3 of the 10 near-zero cells flip sign across streams | **2 of 10** — **NOT MET** (and the refutation is informative, below) |
| Q3 | attenuation is a q effect (≥4/5 negative, \|mean\| ≥ 3 sd) | **6/6 readings negative in 5/5 streams, all resolvable** — **MET** |
| Q4 | 4 main-claim cells' 95 % t lower bound > +0.15 | **8 of 8** (lower bounds +0.398 … +0.442) — **MET** |
| Q5 | across-stream sd > the within-stream draw sd | **0 of 24** — **NOT MET AS WRITTEN: the comparison was mis-specified** (see the repair) |
| Q6 | matched-vs-isotropic-RBF separation ≤ 0.02 | median 0.0054 (q6) / 0.0022 (q8) — **MET** |

## New facts

1. **The map is a property of the setup, not of the noise draw.** The panel's q = 6 mean differs from R398's
   committed independent stream by median 0.0055 (max 0.0211) — 1.0 x the panel's own sd at the median, 2.27x at
   worst, with **0 cells above 3 sd**. Two independent realisations of the whole ensemble agree cell by cell.
2. **Structure is stream-stable; the near-zero signs are MORE stable than predicted.** 8/8 structure cells keep
   their sign in 5/5 streams at both qubit counts, with cross-stream sd ≤ 0.0145 against gaps of 0.41–0.46 (a
   ratio of ~30). Only 2 of 10 near-zero cells flip (`unshifted|0.5`, both planted alignments) — and those are
   exactly the 2 cells that are contested in the lead set. The honest power statement is therefore narrower than
   predicted: the near-zero cells are stream-reproducible, and what moves them is **q**, not the draw.
3. **The ~30 % attenuation is a q effect, now paired on the stream.** All six attenuation readings are negative
   in 5/5 streams and resolvable: `shifted|1` −0.1755 / −0.1765, `unshifted|2` −0.1881 / −0.1762,
   `shifted|0.5` −0.0948 / −0.0894 (α = +1 / −1), i.e. 6.8–18.8 x their own sd. Across the 8 structure cells the
   compression is uniform: ratio q8/q6 in [0.573, 0.790], mean **0.689**.
4. **The discrete statistic is stable where it matters.** The set of cells the quantum kernel leads at q = 8 is
   **identical in all 5 streams** (6 cells: `shifted|3`, `unshifted|0.1`, `unshifted|3`, both α). At q = 6 the
   count is [10, 12, 12, 12, 12] with a stable core of 10 and exactly the contested pair moving.
5. **Q4 gives the manuscript an interval, not a point**: at q = 6 the eight main-claim readings have 95 % t
   intervals (df = 4) of width 0.026–0.036 and lower bounds ≥ +0.398.
6. **18 of 24 paired q-effects are resolvable** and 23 of 24 are sign-unanimous across streams. The 6
   non-resolvable cells are all in the small-\|delta\| region (`shifted|0.25`, `shifted|2`, `unshifted|0.1`) — the
   q-effect is established where the map has structure, not everywhere. State this in the manuscript.

## The Q5 repair (post-hoc, and it is the round's most useful methodological result)

Q5 as registered compared the **cross-stream sd** (the sd of a stream MEAN, i.e. of an average over 6 draws)
against R401's `draw_spread_delta` (the sd of a **single draw**). Under iid draws the stream mean's sd should be
≈ σ_draw/√6 = 0.408 σ_draw, so the registered inequality was mis-specified. The panel's own
`within_draw_sd_mean` is aggregated over BOTH qubit counts (10 realisations), which is worse than mis-specified:
it mixes the factor the ratio is then read across. Measured with the addendum (2 streams, both q, its own code
path):

* σ_draw at q = 6: **0.0191**; at q = 8: **0.0050** — a factor of 3.8 apart, so the aggregate denominator
  inflated one r and deflated the other.
* Corrected ratio r = sd_stream / (σ_draw/√6): **median 0.996 at q = 6** (min 0.643, max 2.402; 3/24 above 1.2) and
  **1.061 at q = 8** (min 0.310, max 2.370; 7/24 above 1.2).
* Verdict: with a matched denominator, **r ≈ 1 at both qubit counts** — the stream adds no variance detectable at
  this sample size beyond the draws it averages. R401's draw-spread-based uncertainty statements are therefore
  calibrated, and the panel's own cross-stream sd may be used directly as a per-cell error bar.
* The aggregate-denominator version (1.467 at q = 6, 0.427 at q = 8) was **manufactured by the denominator**,
  not by the data — a two-sided "finding" that did not exist.

## Pairing buys nothing (and the manuscript must say so)

Within a stream, the q = 6 and q = 8 maps share the stream LABEL but cannot share a draw realisation (different
Hilbert-space dimension, hence different targets and permutations). The paired sd and the unpaired
√(sd6² + sd8²) agree to a median ratio of **1.017**. The q-effect is resolvable because it is 5–16 x the
between-stream scatter, **not** because pairing helped. Calling it "paired" is defensible only as "the two maps
come from the same stream index", and the estimates are in effect unpaired.

## Cost / operational

* Measured cost model (useful for the manuscript's reproduction spec): a map is ~0.8 min at q = 6 and ~4.5 min at
  q = 8 (per-band: 0.10 s metric + 0.04 s fits at q = 6; 2.03 s + 0.21 s at q = 8 — the probe timed the two terms
  separately, unlike R401's). The 5-stream panel ≈ 30 min; the addendum ≈ 11 min.
* **Pitfall (cost 11 min)**: `r402_drawspread.py`'s first version iterated R401's whole report instead of its
  `rows`, raising a KeyError **after** the fits were paid for; the per-cell draw spreads were lost and the
  measurement had to be re-run. Fixed by reading `["rows"]` + asserting 24 keys, and the addendum now persists
  its partial JSON after **every** (stream, q) block.
* `RuntimeWarning: overflow/divide-by-zero in matmul` appears in `smoke_v5.krr_tuned` at large bandwidths — it is
  present in every committed round's instrument; the panel's own output is finite in all 24 cells (checked in the
  follow-up, R2), and C2's bit-for-bit reproduction of R401 confirms the code path is unchanged.
