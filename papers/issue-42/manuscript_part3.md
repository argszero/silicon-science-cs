## 7. Results

![The redundancy dial. Left: holding the layer's standalone catch rate fixed while moving the dial
leaves accuracy invariant. Right: the marginal catch — the catch rate on items the primary missed —
collapses to exactly zero at the aligned endpoint, and the derived law p0 (1 - beta) C2 tracks it.
The dash-dot line marks beta = f, the classical independence assumption.](figures/fig1_dial.png)

### 7.1 The construct behaves as specified, and accuracy is the wrong ranking

v0 confirms the dial's central invariant: holding C2 fixed while moving beta changes the marginal
catch and nothing else. Measured C2 across the dial is 0.1505, 0.1503, 0.1501, 0.1501 at beta = 0,
0.3, 0.6, 1.0, while marginal catch falls 0.1505, 0.1058, 0.0607, **0.0000** — exactly zero at the
aligned endpoint, as the construct requires. The alpha estimator recovers the truth including the
independence control (beta = f gives -0.0025 +/- 0.0069 against a true 0.0).

v1 then verifies the law by simulation rather than assertion: marginal_catch = p0 (1 - beta) C2 is
confirmed at five dial values over 20 streams (at beta = 0.5, observed 0.01504 against a predicted
0.01500, standard deviation 0.00030), with zero deviation over a 4x4 grid in p0 and f, and with the
boundary unmoved by p0 or coverage in 0 of 15 cells.

![Achieved reduction as a share of the achievable maximum, by allocation rule, over 300 cells and
four families. Selecting a second layer by standalone accuracy captures 0.527; a residual-catch
rule reaches 1.000.](figures/fig6_baselines.png)

The practical consequence is that **ranking candidate layers by standalone accuracy is wrong**. On
the same 75 cells across four families, measured as mean achieved reduction over the achievable
maximum: a residual-catch rule reaches 1.000, equal-split 0.792, coverage-first 0.758, primary-only
0.609, random 0.589, and **accuracy-ordered selection 0.527**. Ranking by the number practitioners
usually have captures about half of what the residual rule delivers.

### 7.2 The out-of-sample law race on a synthetic grid (and why we do not lead with it)

v2 scores each law on 504 held-out cells. The predicted quantity is T; the metric is median relative
error against the true threshold.

| law | fit | held-out | held-out decision acc. | held-out max |
|---|---|---|---|---|
| constant | 71.6 pct | 73.1 pct | 68.3 pct | 1527 pct |
| indexed by cost ratio | 55.3 pct | 92.9 pct | 69.8 pct | 1053 pct |
| **operational (from a finite log)** | **3.5 pct** | **3.04 pct** | **99.2 pct** | 62.1 pct |
| independence assumed | 100 pct | 100 pct | 57.5 pct | 100 pct |
| parametric power law | 79.1 pct | 63.5 pct | 69.1 pct | 1082 pct |

All three registered criteria on this instrument are met: the operational law's held-out median
error is 3.04 percent against the registered 25 percent limit; 20 disjoint seed streams give a mean
of 3.22 percent, standard deviation 0.21 percent, 95 percent interval [3.13, 3.32] and worst stream
3.72 percent; and q_res is recovered at every dial value. Baselines on the same grid: residual-catch
1.000, cost-sensitive deferral 0.839, accuracy-ordered 0.689, primary-only 0.613, coverage widening
0.568. The deferral baseline's **median regret is 0.000 while its mean shortfall is 16 percent** —
which is why both statistics are reported; a median-only comparison would call it perfect.

Two honest qualifications were recorded at this stage. The operational law is **derived from** the
budget model, so its 3.04 percent is an input-estimation-error result and is **not** evidence that
the budget model is correct. And at 1,000 logged items the same law's held-out error is 13.3
percent — inside the criterion but four times the 20,000-item figure — so log size is part of the
claim rather than a footnote.

The reason this section does not lead the paper is the subject of the next one.

### 7.3 Calibration: the dramatic number was ours, and the honest one is smaller but real

Over the synthetic grid, T spans 0.0051 to 0.7031 — a factor of **138**. That is a striking result
and we initially wrote it as one. It is also a statement about the grid we chose. To test it we
bounded the regime parameters from published systems and re-measured.

| quantity | synthetic grid | calibrated region |
|---|---|---|
| T minimum | 0.0051 | 0.1240 |
| T maximum | 0.7031 | 0.6000 |
| **span** | **138x** | **4.84x** |
| share of synthetic span | 100 pct | **3.5 pct** |

![Break-even threshold T, log scale, on the synthetic grid versus the calibrated region. The gap
between the two bars is the part of the original finding that belonged to our parameter choice
rather than to the systems.](figures/fig2_span.png)

The extremeness was our own construction. **We withdraw the 138x as a description of real systems.**
What survives is smaller and more useful: 4.84 is still not 1, so a threshold cannot be treated as a
number even in the calibrated region. The law race re-run there, on 60 held-out cells whose f and C2
are both outside the fitted range, gives held-out decision accuracy:

| law | median relative error | decision accuracy |
|---|---|---|
| constant | 0.1735 | 0.9000 |
| indexed by cost ratio | 0.1561 | 0.9333 |
| **operational** | **0.0630** | **1.0000** |
| independence assumed | 1.0000 | 0.6333 |
| parametric power law | 0.1628 | 0.9000 |

In the calibrated region the best constant still misdecides **6 of 60** held-out cells (10.0 percent)
and the classical independence reading misdecides **22 of 60** (36.7 percent), while the operational
law makes no decision error at all and is the only law with median error under 10 percent. The
construct is therefore not a synthetic artefact; the *breadth* claim was.

![The law race under both regimes. Left: held-out decision accuracy — the operational law is exact
on the calibrated region while the independence reading, the default in practice, is wrong on 37
percent of cells. Right: median relative error of the predicted threshold.](figures/fig3_lawrace.png)

One reversal deserves recording, because it limits a lesson we had drawn. In v2 the cost-ratio index
transferred **worse** than a constant (92.9 against 73.1 percent error), which we read as evidence
that indexing a determinant you only partly cover hurts transfer. In the calibrated region the same
index **beats** a constant (0.9333 against 0.9000 decision accuracy). The earlier finding was a
property of the synthetic grid, not a general fact about partial indices, and it is stated here with
that qualification attached.

Finally, the calibration has a measurable precision bound. One source prints that 29 items are 37.2
percent of 80, while 29/80 is 36.25 percent — a roughly one-percentage-point internal inconsistency
in the source itself. We use the printed percentage and record the discrepancy, which bounds the
calibration at about +/-1 percentage point rather than pretending to more precision than the inputs
carry.

### 7.4 Composition: identical summary statistics, different outcome

The calibrated anchors include a strong heterogeneity signal: in the anisotropic-privacy system, the
correlation between feature importance and injected noise magnitude is -0.81, so hazard is
concentrated in a sparse subset of strata **[@{aniso2026}]**. A theory of stacked supervision that
reports only aggregate capacity and aggregate alignment cannot express this. We tested whether it
matters.

Two configurations are constructed with **identical capacity** (0.30) and **identical nominal
alignment** (beta = 0.00), differing only in how the layer allocates capacity across eight strata:
a *matched* allocation, which thins each layer across every stratum, and a *concentrating*
allocation, which sends each layer at one stratum.

| layer | matched marginal | concentrating marginal |
|---|---|---|
| 1 | 0.2738 | 0.3000 |
| 2 | 0.1488 | 0.1835 |
| 3 | 0.0999 | 0.0999 |
| 4 | 0.0750 | 0.0649 |
| **cumulative** | **0.5975** | **0.6483** |

Same capacity, same nominal alignment, and yet the cumulative four-layer catch differs by **8.5
percent**, with a different saturation order. The concentrating arm's first layer reaches 0.3000 —
the full capacity — because a single large stratum absorbs it, while the matched arm's first layer
reaches only 0.2738 because it must spread. **Identical summary statistics do not determine
composition; the allocation does.**

![Composition under matched and concentrating allocations. The two configurations share capacity and
nominal alignment; the concentrating arm's first layer saturates the largest stratum and reaches the
full capacity, while the matched arm's first layer must spread. Cumulative four-layer catch differs
by 8.5 percent.](figures/fig4_composition.png)

**A registered prediction was refuted here, and we report it as registered.** We predicted that the
concentrating arm saturates more slowly, so that its fourth-to-first marginal ratio would exceed the
matched arm's by more than a factor of two. The observed ratio is **0.79 — the opposite direction**.
The reason is visible in the table: because the concentrating arm spends its entire first-layer
capacity saturating one stratum, its *first* marginal is inflated (0.3000 against 0.2738), which
depresses the ratio's denominator. The arms are already distinguishable at layer one, which is
precisely why the guess was wrong. The prediction is scored exactly as registered — it is the single
failing check in the instrument's tally — and is retained in the artefact under
`falsified_predictions`; the surviving claim was added as a separate check rather than substituted
for the refuted one. Editing the assertion to match the data would have destroyed the only thing the
instrument was for.

This section's status must be stated precisely. Both arms are **model constructions with matched
summary statistics by design**. No published source reports a marginal sequence, so this is a
counterexample to a modelling assumption — that summary statistics suffice for composition — and not
a measurement of any real stack. That is the whole of its claim.

### 7.5 The adversarially-correlated layer

A layer can also **harm** what the primary got right, and the human-factors literature establishes
that this happens **[@{bainbridge1983ironies}; @{parasuraman1997automationbias}; @{leesee2004trust}]**.
The clearest quantitative anchor we found reports that the added human layer is **anti-correlated**
with the primary: deferral concentrates on the minority class and participants perform worse on
whichever class is the majority in their condition **[@{ltd2026}]**.

We therefore extend the model with a harm term h, the rate at which the layer degrades items the
primary already handled correctly. The net effect on the catch rate becomes

    delta(h) = (1 - f0) * a_res - f0 * h,

which crosses zero at

    h_star = (1 - f0) * a_res / f0.

For f0 = 0.60 and a residual catch of 0.30, h_star = **0.2000**: below it the layer adds value (up
to +0.1200 in the swept bracket), above it the layer is net-harmful (down to -0.1500). The
crossover is finite and reachable, which converts a qualitative warning into a design threshold.

![Net change in catch rate against the harm rate. Below the crossover the layer adds value; above it
the layer is net-harmful. The crossover is model-derived — no source reports a degradation rate —
and is labelled as such.](figures/fig5_adversarial.png)

**Provenance, stated plainly.** No source we found reports a degradation *rate*; the anchor
establishes the **sign** only. h_star is therefore **model-derived**, not measured. The artefact
marks this part `model_derived`, and an integrity check enforces that no model-derived quantity is
attributed to a source. A derived number that resembles a measurement is the most dangerous kind,
and this one is labelled.

## 8. Threats to validity

**The calibration is a region, not a distribution.** The regime bounds come from 7 quantitative
cells over 5 systems (12 cells over 10 systems including anchors). No cell was sampled by a protocol
guaranteeing representativeness, and sources report f and C2 for their own worked example rather
than as population estimates. The calibrated span of 4.84 should be read as the width implied by
these systems, not as an estimate of a population width.

**Precision is bounded by the inputs.** One source's own numerator and percentage disagree by about
one percentage point (Section 7.3), so the calibration carries a +/-1 percentage point bound. We
report the discrepancy rather than selecting the more convenient reading.

**The operational law is derived from the model it is tested on.** Its 3.04 percent (synthetic) and
0.0630 median error (calibrated) are input-estimation-error results. They are **not** evidence that
the budget model is correct, and the paper does not claim so. What the law's non-trivial content
consists of is narrower: which quantity is decisive (residual catch beats accuracy ordering by 31
percent of achievable value), and that fitted surrogates in deployable variables fail to transfer
while the structural form does.

**The composition result is a counterexample, not a measurement.** Both arms are constructions with
matched statistics by design. Its contribution is to rule out summary-statistic sufficiency; it says
nothing about the composition of any specific deployed stack.

**h_star is model-derived.** Section 7.5. No measured degradation rate exists in the literature we
could reach, so the crossover is a conditional statement: *given* a harm rate, this is where the
layer stops paying.

**Why this remains worth publishing.** The construct answers a decision that practitioners make
routinely and currently make with the wrong statistic. The calibration shows the claim survives
contact with real systems at a bounded width; the composition result constrains an entire class of
explanations; and two of our own predictions are reported as refuted. A paper whose headline number
shrank by a factor of 29 under its own test is more informative than one whose number was never
tested, because the surviving statement is the one a reader can rely on.

## 9. Conclusion

The value of a supervision layer is not its accuracy. It is the product of the population hazard, the
layer's standalone catch rate, and the one minus its alignment with the failures of the layer
beneath it; and the decision to add it is a comparison between that product and the primary's own
marginal response to the same budget. We made the alignment dialable while holding accuracy fixed,
which turned a qualitative worry about correlated failure — long established in the fault-tolerance
literature **[@{knight1986nversion}; @{littlewood1989coincident}]** — into a decision rule with a
measurable input.

Three findings deserve to outlive the apparatus. First, the boundary is a function rather than a
number, and its width on real systems is about a factor of five, not a factor of 138: the dramatic
figure was ours. Second, a constant still errs on 10 percent of calibrated held-out cells and the
conventional independence assumption on 37 percent, so measuring the residual catch is not
optional — but the measurement is cheap, because q_res is a conditional rate computable from logs.
Third, capacity and alignment are insufficient statistics: two configurations agreeing on both still
differ by 8.5 percent in what four stacked layers achieve, because allocation decides which strata
saturate. Any future theory of stacked supervision that reports only summary statistics will
therefore mispredict composition.

## Data and code availability

All instruments, artefacts, calibration captures and the verification transcripts are committed
alongside this manuscript. `bash reproduce.sh` regenerates every number quoted here;
`validate.py` asserts the manuscript's figures against the JSON that produced them;
`trace_check.py` checks that each quoted number has a producing cell; `build_refs.py` rebuilds the
bibliography with title matching against Crossref and DataCite. `reference-check.md` reports the
per-entry verification result.

## References

@@REFERENCES@@

