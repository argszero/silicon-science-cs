# Issue #87 — R393 notes: the FDR layer built, its size control FAILED, and the failure is a bias not a variance

R391 and R392 read leads off marginal 95 % paired CIs and said so. The registration requires FDR control
across the grid before an advantage is *declared*, so this round built the correction layer — and, more
importantly, validated it. **The size control failed at 47–50 % against a nominal 5 %**, and the mechanism
turned out to be neither of the two things I first suspected.

## 1. What the layer is (`smoke_v7.py`, sha256 `56db65ad…`)

- **Declared family**: the whole q = 6 / cycle / L = 2 grid — 2 conventions × 3 alignments × 7 bandwidths
  = 42 rows, of which the γ = 0 rows are degenerate by construction.
- **Three independent p-value routes** per cell (sign-flip permutation, percentile bootstrap, normal
  approximation), with their maximum disagreement reported — a p-value is an instrument and owes a control.
- **BH** at q = 0.05/0.10 and **Benjamini–Yekutieli** q = 0.05 (valid under arbitrary dependence), plus the
  measured dependence of the family: mean |off-diagonal correlation| **0.173**, max **0.945**.
- **Size control**: 8 independent null cells (planted A = 0 → pure noise), pooled p-values tested for
  uniformity (KS D = 0.359, p = 0.0000) and false declarations counted.
- **Power control — the registration's own planted-alignment control**: a handicap ladder
  `W_t = (1−t)·W_map + t·diag(W_map)`, t ∈ {0, 0.25, 0.5, 1}. At t = 0.25/0.5/1 it declares 16/15/16 of 21
  tests. So **the pipeline does find an advantage when the geometry is withheld** — the fallback clause's
  question is answered affirmatively, which is what makes the near-empty map informative.

Mechanically the layer is correct (unit-checked before the run: BH rejects the right cells with the right
q-values, BY inflates by Σ1/i, a degenerate identical delta lands on the p-floor, and the three routes agree
to 0.006 on pure-noise data).

## 2. The size control failed, and the two obvious explanations are both wrong

**On the null the procedure declares a difference in 47–50 % of tests** (nominal 5 %): pooled over 12 seeds
and 6 usable bandwidths, percentile CI 36/72 = 50.0 %, sign-flip 36/72 = 50.0 %, bootstrap-t 34/72 = 47.2 %.

**(a) It is NOT the resampling design.** The 120 splits are overlapping partitions of the same 64 points, so
the deltas are correlated and the within-cell SE could understate the variance of the mean. It does not:
the across-seed spread of the cell means — an unbiased estimate, since each seed is an independent noise
realisation — matches the within-cell SE at every bandwidth (ratio **0.67–1.46×**, γ = 0.5 → 1.20,
γ = 1.0 → 1.46, γ = 3.0 → 0.85). *An unbiased variance estimate is not a valid test; the expectation can be
biased while the SE is right.*

**(b) It is not correctable skewness, and the machinery itself is fine.** The null deltas are strongly
asymmetric (skew −0.71…−2.36 at γ ≤ 2, +3.59 at γ = 3; kurtosis 6.3–30.1; extremes asymmetric by 2–3×), so
the symmetry assumption behind the sign-flip test is violated — and studentising does not rescue it
(bootstrap-t 47.2 %). But **the mechanism is confirmed by a construction that removes the asymmetry**: take
the same null deltas, keep |d| and randomise the sign, and the SAME tests return to nominal —

| method | actual data | symmetrised data |
|---|---|---|
| percentile bootstrap CI | 50.0 % | **5.6 %** |
| sign-flip permutation | 50.0 % | **2.8 %** |
| bootstrap-t | 47.2 % | **1.4 %** |

So the statistical machinery reads ~5 % exactly when its assumption holds. The data violate the assumption,
and no reweighting of the same statistic repairs a violation of that size.

**(c) What it actually is: a SYSTEMATIC BIAS, and the null is not neutral.** Per bandwidth the null's
failure rate is 12/12 at γ = 0.5, 9/12 at γ = 2.0 and 3.0, 3/12 at γ = 1.0, 2/12 at γ = 0.25, 1/12 at
γ = 0.1 — and the cell means are systematically signed: **quantum "leads" by ~0.05 at γ ≤ 1 and loses by
~0.04 at γ ≥ 2, on a target that is pure noise.** Three independent seed families on the same cell give
it the same way: 8/8, 12/12, 9/10 "significant" at γ = 0.5 (29 of 30), e.g. seed 5074: mean −0.0490,
CI [−0.0882, −0.0160].

The mechanism is structural, not numerical: **the two arms have different capacities to shrink.** With no
signal the Bayes predictor is the mean, so the arm that shrinks hardest wins. The quantum kernel's shape is
fixed by the map, and at collapsed bandwidth the kernel is nearly constant — it predicts the training mean
and is *optimal* on noise — while the Mahalanobis rival is a properly structured Gaussian and fits noise.
A pure-noise target therefore does not make the arms exchangeable; it measures robustness to noise.

**This retro-corrects R391's C4 control**, which read "the null cell's advantage 0.0567 does not exceed the
aligned cell's 0.0740 — the null does not manufacture a lead". It was manufacturing a lead; the bias at
γ = 0.5 (~0.05) is the same magnitude as the "lead" it was innocuously compared against. A control that
reads a bias as reassurance is worse than no control, because it certifies the thing it should have caught.

## 3. What survives, and what does not

The per-bandwidth **null band** — the across-seed spread of the null cell means, ±0.06 at the worst
bandwidths — is the only yardstick the study has for "no effect", and it replaces zero:

| claim | effect | null band | verdict |
|---|---|---|---|
| γ = 0.5–1.0 aligned / orthogonal cells | 0.12–0.45 | ±0.06 | **far outside** — survives |
| γ = 3.0, α = ±1 (the R392 finding, both conventions) | 0.05–0.08 | ±0.06 at γ = 3 | at the band edge — **must be re-read, not carried over** |
| γ = 0.1–0.25 "leads" (0.013–0.083) | 0.013–0.083 | ±0.06 | **inside the band — not reportable as leads** |

So the large effects stand on their size, and the borderline ones do not. The declared FDR counts from v7
(12 leads + 16 losses at q = 0.05) are **not usable**: they were computed from p-values whose null is
mis-specified, which is exactly what the size control was there to detect.

## 4. Defects this round produced

1. **The degeneracy predicate keyed on the wrong object — again (third occurrence in this study).** It was
   `|mean delta| < 1e-15`; the object is "are the two kernels numerically indistinguishable". At γ = 0 the
   shifted-convention rows have round-off means of 1e-12–6e-12 (three orders above the threshold), so
   **3 bogus rows entered the family and m = 39 instead of 36**, shifting every BH threshold by 39/36.
   The correct key is measured: **max|K_quantum − K_rival| = 4.441e-16 at γ = 0** and 1.0e-1…9.7e-1 for
   γ > 0 — a six-order separation with nothing in between. (None of the bogus rows was declared, q ≈ 0.25–0.67,
   so the damage is the threshold shift, not a false discovery.)
2. **Two of my own reports counted different objects under the same words.** v7 printed "marginal leads:
   12" next to "BH declares 28" — the 28 is 12 leads **plus 16 losses**; BH is sign-agnostic and I was not.
   And the 21 %-vs-50 % discrepancy between v7's size control and the diagnostic was not a data difference
   at all: v7's counter took `ci[1] < 0` (one-sided, leads only) while the diagnostic took both signs. One
   quantity, two conventions, and the labels did not distinguish them.

## 5. The fix (R394), stated concretely

- **Validate the machinery on an exchangeability null**: two arms with the SAME kernel must return ~5 %.
  This is the only control that tests the procedure without confounding it with shrinkage. (The
  symmetrised-data result above is the same idea one step removed, and it already passes.)
- **Replace zero-anchored p-values with a simulated null band**: for each bandwidth, simulate ≥ 40 null cells
  (a second independent seed family) so the empirical-null resolution 1/(N+1) < q = 0.05, and read each
  cell's effect against that band. That is a calibration by simulation, and it makes no assumption the data
  can violate.
- **Adopt the kernel-keyed degeneracy predicate** (max|Kq − K_rival| < 1e-12) so the family is exactly the
  36 real hypotheses.
- Report **two-sided** counts everywhere a difference is counted, and keep "leads" and "losses" in separate
  fields.
