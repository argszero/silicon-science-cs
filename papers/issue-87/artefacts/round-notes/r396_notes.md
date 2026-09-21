# Issue #87 — R396 notes: was R395's PIT audit valid?  Three sources separated, and a self-correction

R395 replaced the empirical band with a fitted null, then reported that the fitted null's **SHAPE is wrong**
(out-of-sample PIT KS 0.1903, p ≈ 0, 5.0 % above the 95th percentile vs 2.1 % below the 5th). This round
asked the opposite question about the same evidence, and the answer splits three ways: one part of that
verdict was my own audit's fault, one part was a real defect I had mis-attributed, and the third part is new
and now measured.

## 1. Identity first (`smoke_v10.py`, sha `747504d5…`)

The new instrument recomputes R395's PIT statistic from the committed draws and must reproduce it exactly:
**reported 0.1903, recomputed 0.1903 — match.** A new instrument that cannot reproduce the old number is
measuring something else. (It first failed to: my `plug_in_fit` omitted the shape fit and silently measured
a normal, which is exactly what an identity control exists to catch.)

## 2. Source (a): the audit charged the model for the fit's estimation error

An out-of-sample audit that plugs in parameters estimated from a *different* finite sample tests the model
and the estimation error together. The magnitude here: a 40-draw fit's location error is **median 0.241 σ
(per-bandwidth), p90 0.514 σ, max 0.941 σ**, and the calibration family's dispersion is 0.92×–1.68× the
validation family's across the 12 bandwidths.

The fix is a **predictive null** — bootstrap the calibration draws, refit location and scale, then draw a new
cell mean from the fitted shape — because a study cell IS one draw of exactly that kind, so this is the
distribution its threshold should come from. Its PIT on the same 240 validation cells improves **0.1903 →
0.1402** (mean 0.5393). So part of R395's failure was the audit's own construction.

## 3. Source (b): the decomposition REFUTES R395's "the shape is wrong"

Refitting one component at a time on the validation family (shifted convention):

| reading | PIT KS | mean PIT |
|---|---|---|
| (a) everything from the calibration family, as R395 did | **0.2552** | 0.6422 |
| (b) location + scale refitted on the validation family | **0.0563** | 0.5009 |
| (c) shape refitted on the validation family as well | **0.0578** | 0.5005 |

**Refitting only location and scale collapses the statistic; refitting the shape as well changes nothing
(+0.0015).** The shape was never the problem — it is adequate (fitted on the validation draws it is
ε = −0.211, δ = 0.942, essentially the same family). **R395's stated conclusion is withdrawn**: the defect it
named was the wrong one, and the evidence for it (a KS that stays large when the shape is refitted) does not
exist.

## 4. Source (c): the audit is NOT merely invalid — the two null seed blocks genuinely differ in dispersion

Even with the correct predictive construction the model is still rejected (KS 0.1402, p = 0.01 against the
audit's own simulated reference). So there is a real third source, and it has a name. One quantity decides
it — the ratio of dispersions between a 40-draw and a 20-draw block:

| reading | median ratio | fraction > 1 | two-sided sign test |
|---|---|---|---|
| **observed**: calibration (40) vs validation (20) | **1.44** | **11/12** | **p = 0.006** |
| split-half control: calibration cut 20 vs 20 | 0.86 | 2/12 | p = 0.039 |
| **synthetic same-null**: 40 vs 20 drawn from the fitted null itself | **1.02** | 0.53 | **p = 0.000** for the observed count |

The synthetic control is the decisive one: drawing 40 + 20 from the *fitted* null reproduces the expected
ratio (1.02, 53 % above 1), and the probability of seeing 11 of 12 bands above 1 under that reference is
**0.000**. So the observed gap is not a heavy-tail small-sample artefact of the estimator — **the calibration
block and the validation block are not the same distribution.** The split-half adds a direction: inside the
calibration block the first 20 draws are less dispersed than the second 20 (10 of 12 bands, p = 0.039), so
dispersion appears to drift with the seed index, and the two blocks sit at different points of that drift.

The consequence is the one that matters for the study: **a null band estimated from 40 draws is not
transferable to another block of 40 draws.** The band is a property of the seed block, not of the pipeline.
That was invisible while the band was judged against zero (R394/R395), and it is what the shape audit was
really detecting.

## 5. The instrument as it now stands, and the read

- **Size** on the 240 independent null cells: plug-in **3.33 %**, predictive **2.08 %** — both conservative,
  the predictive more so (it deliberately carries the estimation width).
- **It fires**: injected shifts of 1 / 2 / 3 / 5 predictive σ → **20.0 / 67.9 / 96.7 / 100 %** declared. So the
  conservatism costs power only at the smallest shifts, and a large advantage would be found.
- **The read**: predictive **24 declared (9 leads)** vs plug-in 28 (11 leads). All **11** rows with
  |δ| ≥ 0.25 are declared; **20 of 22** with |δ| ≥ 0.05. The smallest declared effect is still
  **0.0059 of a variance** — so R395's caveat stands unchanged: "declared" means *this cell does not behave
  like a no-signal cell of this pipeline*, because the null's **location** is off zero; it does not mean
  "quantum beats the matched rival by this much".

## 6. What the study can and cannot say

* **Can**: the large effects (|δ| ≥ 0.25: 11 rows, 10 losses +0.367…+0.446 and γ = 3 leads −0.053…−0.077)
  are declared by every instrument tried, sit far outside every band, and are unaffected by any of this
  round's corrections.
* **Cannot**: classify anything below |δ| ≈ 0.05, and that bound is now *measured* rather than guessed — the
  null's dispersion is not stable across 40-draw blocks (1.44×, p = 0.006).
* **Withdrawn**: R395's "the fitted shape is wrong". **Unchanged**: PB1's middle clause NOT OBSERVED (R391),
  PB3 REFUTED as written (R392), and no advantage declared in the registration's sense.

## 7. Carried to R397

The blocking item is the seed-block dispersion difference, and it is a *generation* question, not a
modelling one: find its mechanism (leading candidate — the cell mean's dispersion drifts with the seed
index, which the split-half shows at p = 0.039 and which a larger sweep could settle), or measure the null on
enough draws per bandwidth that the dispersion estimate is stable (R394 measured the requirement at
N ≈ 1,400 for the p-value floor; the estimate of the *dispersion* has its own, much closer requirement).
Until one of those lands, the study cannot write an advantage map for small effects. Then the still-untouched
**path/complete strata and one q = 8 cell**.

Honest limits of this round: the homogeneity test has 12 bands, which is a small sample (the strongest
evidence is the synthetic reference's p = 0.000, with the sign test at 0.006 as the direct one); the
split-half direction is suggestive, not established; the reference distribution is simulated under three
candidate truths (fitted / normal / heavier-tailed) so it is not anchored on one; and the predictive
instrument's conservatism is reported as a size (2.08 %), not corrected away.
