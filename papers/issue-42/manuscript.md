# When Does Another Check Help? Failure-Mode Alignment Sets the Marginal Value of a Supervision Layer

**Contribution level: `theory+empirics`** (a formal construct + a derived boundary law, calibrated
against 12 cells drawn from 10 independent published systems).

## Abstract

Teams that add a second check to an existing one — a second reviewer, a second verifier, a second
model, a redundant monitor — implicitly assume the new layer catches failures the first missed.
We show that this assumption is a single point on a dial rather than a generic regime, and that the
decision to add a layer is governed by a quantity that is almost never measured: the **residual
catch**, the new layer's catch rate on the population the previous layer got wrong. We formalise a
**redundancy dial** that reallocates where a layer's catches fall while holding its accuracy exactly
fixed, so that same-accuracy-different-worth becomes testable. Three results follow. First, the
marginal catch of an added layer is governed by the residual product p0 (1 - beta) C2, and the
break-even condition against spending the same capacity on the primary is T = f2 - f — not a number
but a function of the primary's catch rate, the layer's own budget response and the cost ratio.
Second, on a synthetic regime grid T spans a factor of 138, but calibrated to 12 cells drawn from 10
independent published systems it spans only 4.84 — 3.5 percent of the synthetic span. The dramatic
breadth claim is withdrawn as an artefact of our own grid; what survives is that 4.84 is still not
1, so the best constant still misdecides 10.0 percent of held-out cells and the classical
independence reading (always add the layer) misdecides 36.7 percent, while a law that reads the
primary's own budget response decides 100 percent. Third, and most sharply, **identical summary
statistics do not determine composition**: two stacked configurations with the same capacity and the
same nominal alignment deliver cumulative four-layer catches 8.5 percent apart, because allocation —
not the summary statistic — decides which strata saturate. We also report a registered prediction
that our own instrument refuted, scored exactly as registered.

## 1. Introduction

Supervision in computing systems is almost never a single mechanism. Code changes pass a reviewer
**[1, 2]** and then a continuous-integration pipeline;
an autoscaler acts and then a monitoring rule fires; a model answers and a verifier scores the answer
**[3, 4]**; a human decision is checked by a second human. The
design question behind every such stack is the same: **does adding the next check buy more than
spending the same capacity on the check we already have?**

The literature answers a neighbouring question. Selective prediction asks when a model should
abstain **[5, 6, 7]**; learning to defer asks
when a model should hand an item to a human **[8, 9, 10]**; ensemble theory asks how correlated voters change aggregate accuracy
**[11, 12]**. The closest prior work asks the layered question directly but not quantitatively: a qualitative
interview study with five practitioners finds that organisations distribute supervision across
multiple guardrail layers and that the question of how existing guardrails evolve in response is
open **[13]**. It reports the *shape* of the problem — layers, shifting load, no
measurement — and we take that shape as given here.

All three concern a **single** gate:
should this item be escalated, abstained on, or decided? None of them prices the **second** gate —
the one that exists because the first gate is already deployed and already imperfect.

This paper argues that the missing quantity is the **residual catch profile**. Two second layers can
have the same accuracy and be worth very different amounts, because worth depends on **where** the
catches fall: on items the first layer already got right (redundant), or on items it missed
(complementary). We make this testable by introducing a **dial** that moves a layer's catches between
those two populations while holding its overall catch rate exactly constant. Independence — the
classical assumption that a second layer's errors are unrelated to the first's **[14, 15]** — turns out to be one point on that dial, not a default.

We then derive the decision. Letting f be the primary's catch rate, C2 the layer's standalone catch
rate and beta the dial, the marginal catch of the added layer is p0 (1 - beta) C2 — free of f and of
the layer's cost structure. Adding the layer beats investing in the primary exactly when that
product exceeds a threshold T = f2 - f, where f2 is what the primary's catch would become if it
received the layer's budget. The central structural finding is that **T is a function, not a
number**, because f2 depends on the primary's own budget-response curve.

Our initial measurement of that function was alarming. Over a synthetic regime grid, T spanned a
factor of **138**, which would mean that no scalar rule can ever track it. Before publishing that, we
tested it against the world it would have to describe. Calibrating the regime parameters to 12 cells
drawn from 10 independent published systems collapses the span to **4.84** — 3.5 percent of the
synthetic figure. The headline number was a property of our grid. Section 7.3 reports this as a
refutation of our own claim, and shows what survives: the threshold is still not a constant, but the
claim must be made at a bounded, calibrated width rather than a dramatic one.

**Contributions.**

1. A **construct** — the residual catch profile and the redundancy dial beta — that separates a
   layer's accuracy from its marginal value, with the classical independence assumption identified
   as the single dial value beta = f (Sections 4).
2. A **boundary law**: marginal catch equals p0 (1 - beta) C2, and the layer-addition decision is a
   break-even on T = f2 - f, which is not a scalar (Sections 5).
3. A **calibrated empirical claim** about the width of that boundary: 138x on a synthetic grid, 4.84x
   on 12 cells from 10 published systems, with the operational law reaching 100 percent held-out
   decision accuracy where a constant reaches 90.0 percent and the independence reading 63.3 percent
   (Sections 7.3).
4. A **composition result** that constrains any summary-statistic theory of stacked supervision:
   equal capacity and equal nominal alignment still differ by 8.5 percent in cumulative catch,
   because allocation decides which strata saturate (Sections 7.4).
5. An **honest accounting** of two predictions our own instrument refuted — a prior claim about the
   synthetic span and a registered prediction about saturation order — plus a model-derived
   adversarial crossover that is explicitly flagged as not measured (Sections 7.5 and 8).

**Whose belief changes.** Anyone who allocates supervision capacity: an engineering team deciding
between a second reviewer and a better first reviewer; an evaluation lead choosing between a second
judge and a stronger first judge; a systems designer adding a third redundancy layer. The paper's
actionable content is that accuracy-ranked selection of a second layer is the wrong rule (Section
7.1 measures it at 0.527 of achievable reduction against 1.000 for a residual-catch rule), and that
the correct rule is a comparison between the residual product and the primary's marginal response.

## 2. Related work

### 2.1 Learning to defer and selective prediction

Selective prediction formalises abstention: Chow derived the optimal error-reject tradeoff
**[7]**, and modern treatments learn a selector jointly with the predictor
**[5, 6]** or calibrate the score before thresholding
**[16]**. Learning to defer extends the gate to a human expert, with consistent
surrogate losses **[8]**, multiple experts **[9, 17, 18]**, populations rather than individuals **[19, 20]**, sequences **[21, 22]**, and always with a workload
or coverage constraint **[18, 23]**.

**Specific difference.** This literature asks **whether to defer this item** and evaluates the
resulting human-machine team. We ask a question it does not pose: given that a gate already exists
and is already imperfect, **where should the next unit of supervision capacity go**, and what
measurable property of the candidate layer decides that? Deferral work treats the human as the
second stage and measures accuracy; we treat the stage as arbitrary (a human, a verifier, a memory
checker, an ECC layer) and measure the **overlap of its catches with the previous stage's failures**.
The design space around the gate is now well mapped: triage and differentiability of the deferral
rule **[24]**, uncertainty-aware deferral **[25]**, teaching the human
when to defer **[26]**, closed-loop pipeline design **[27]**, predictors
built to complement a specific human **[28, 29]**, guiding experts
with personalised models **[30]**, and application-specific instantiations in fraud
**[31]**, team coordination **[32]**, causal evaluation of deferring systems
**[33]**, multi-objective post-processing **[34]**, unseen experts
**[35]**, ranking **[36]**, security operations
**[37]**, reasoning agents **[38]**, knowledge tracing **[39]**,
explicit requests for human input **[40]**, fatigue-constrained deferral **[41]**,
segmentation **[42]**, clinical model selection **[43]**, fair
cooperation **[44, 45]**, abstention in multimodal QA
**[46]**, and conformal control of expert queries **[47]**.

Recent work has begun to question whether uncertainty quantification can substitute for deferral
**[48]** and whether deferral is needed at all **[49]**; our construct
explains why those questions are ill-posed without a residual-catch measurement: a layer's value is
not a property of its confidence but of its failure-mode alignment with what precedes it.

### 2.2 Ensembles, diversity and correlated failure

Ensembles improve accuracy by combining voters **[14, 50, 51]**, stacked **[52]** or combined as mixtures and products
**[53, 54, 55]**, and diversity is the accepted
explanatory variable **[15, 11]**, with deep ensembles
supplying calibrated uncertainty **[56]** and negative-correlation training
pushing diversity explicitly **[57]**. Adversarial ensembling studies diversity under
attack **[58]**, and domain applications continue the pattern
**[59, 60, 61, 62, 63]**.

**Specific difference.** Diversity measures are properties of a **parallel** set: they quantify how
much voters disagree. Our dial is a property of a **sequential** pair and is defined against the
previous layer's *errors*, not against other voters. This distinction matters numerically: a pair can
be maximally diverse in the ensemble sense while the second layer's catches fall entirely on items
the first already caught, in which case its marginal catch is exactly zero — a case ensemble theory
does not isolate because it does not condition on the first layer's outcome.

### 2.3 Verification layers, critics and cascades

Modern pipelines verify rather than trust: process reward models score reasoning steps
**[3, 4]**, self-consistency samples and votes
**[64, 65]**, self-refinement and reflection critique an output
with the same model **[66, 67, 68, 69]**, constitutional methods use AI feedback **[70]**, judges
grade outputs **[71]**, and dedicated verifiers are trained for the role
**[72, 73, 74]**. Failures of self-correction are documented
**[75]**, uncertainty-based trustworthiness is surveyed **[76]**, and
the classical cascade — early exit, boosting, staged detection — predates all of it
**[77, 78, 79]**. Long-context behaviour adds its
own failure modes **[80]**, and the transformer substrate is universal
**[81, 82]**.

**Specific difference.** These systems report that a verifier **helps**, usually as an accuracy
delta against no verifier. That comparison cannot distinguish a verifier that catches new failures
from one that re-catches known ones, which is precisely the distinction our dial isolates. We
therefore report a quantity absent from these evaluations: the catch rate **conditional on the
previous layer having failed**, and the complementary rate conditional on it having succeeded.

### 2.4 Human oversight, automation bias and AI-assisted engineering

Human factors research has long warned that added automation changes the human's own behaviour:
ironies of automation **[83]**, use-misuse-disuse-abuse **[84]**,
appropriate reliance and calibrated trust **[85]**, and algorithm aversion after
observed error **[86]**. Engineering studies show review is the binding
constraint **[1, 2]** and that AI assistance shifts
where the load lands **[87]**. Recent work examines machine behaviour on humans
**[88]**, reviewer confidence signals **[89]**, calibrated
human-in-the-loop grading **[90]**, metacognitive collaboration policies
**[91]**, perception models **[92]**, unequal uncertainty across
groups **[93]**, and out-of-domain uncertainty **[94]**.

**Specific difference (the closest work).** The layered-supervision interview study
**[13]** reports that guardrail layers exist, that load shifts between them, and that
how they evolve is open; it does not measure what any layer buys. We supply the missing
measurement and the decision attached to it, and in exchange we adopt its structure — a sequence of
standing checks rather than a single gate — as the object of the model. Neither of us can answer the
other's question: it has the practice without the quantity, and this paper has the quantity without
the organisational detail.

**Specific difference.** This work studies how a human responds to being given a layer. Our
adversarial analysis (Section 7.5) formalises the complementary direction the human-factors
literature establishes qualitatively: a layer that degrades items the primary already handled
correctly has a **finite** crossover beyond which its net effect is negative. The published
evidence we use establishes only the sign; we flag the magnitude as model-derived.

### 2.5 Redundancy and fault tolerance

Redundancy is the oldest form of a second check: triple modular redundancy
**[95]**, recovery blocks **[96]**, N-version programming
**[97, 98]**, and replicated agreement
**[99, 100]**. The decisive empirical result for our purposes is
that **independence between replicas is false**: coincident failures are real and measurable
**[101, 12, 102]**, which is exactly
the failure our dial parameterises.

**Specific difference.** This literature measures whether replicas fail together. We reuse its
central caution — that independent failure cannot be assumed — but convert it from a warning into a
**design dial with a decision rule attached**. Rather than reporting that dependence exists, we ask
at what dependence the added replica stops being worth its budget, and show that the answer depends
on the primary's response curve rather than on the dependence alone.

### 2.6 Decision-theoretic foundations

Metareasoning prices the cost of computation **[103]**; information value
theory prices information before it arrives **[104]**; cost-sensitive learning
shifts thresholds when errors are unequally priced, with ROC analysis as the standard instrument
**[105]**. Statistical machinery used throughout: Wilson intervals **[106]**,
the bootstrap **[107]**, and false-discovery control for multiplicity
**[108]**.

**Specific difference.** Metareasoning and value-of-information ask whether to compute more at all.
Our question is narrower and more concrete — between two ways of spending a fixed supervision
budget — and its answer turns out to depend on a quantity neither framework requires you to
estimate, namely the residual catch rate of the specific candidate layer.

## 3. Prior beliefs (registered before the deciding runs)

The following priors were fixed in the research registration before the adjudicating experiments,
with the grounds for each prediction. They are reported here with their outcomes; Section 8 returns
to what the refutations do and do not license.

**P1.** *Realistic supervision layers are strongly aligned with the layer beneath them, so residual*
*catch is substantially below standalone catch.* Grounds: N-version and multiversion studies found
coincident failures to be the norm rather than the exception **[101, 12]**, and self-critique methods reuse the same model that produced the
output **[66, 75]**. **Outcome: CONFIRMED in the
calibration.** The published systems we could read report between-layer agreement far above the
independence benchmark: two formalisation pipelines agree on 31.0 percent of their overlap where
independence predicts 100 percent **[109]**; an uncoordinated three-layer ECC stack
duplicates redundancy by design **[110]**; a verification tool's headline finding is
independently re-found by a human-filed report **[111]**. Betas in the calibrated set run
from 0.00 to 0.80 with a majority above 0.3.

**P2.** *Accuracy ranking overstates marginal value: there is a non-corner inversion region in which*
*a lower-accuracy but decorrelated layer dominates a higher-accuracy fully aligned one.* Grounds:
the marginal quantity does not contain the layer's accuracy **[8]**; ensemble
theory separates individual from combined accuracy **[11]**. **Outcome: MET,
with a caveat we flag rather than bank.** 32 percent of equal-cost strictly-lower-accuracy pairs are
inversions, 66.7 percent when both alignments are interior — but the identical figure appears in all
four families because the condition is scale-free in p0, so the registered three-of-four-families
clause is satisfied **trivially** and is not counted as four independent confirmations. The inversion
additionally requires the layer to be cheaper per unit of hazard.

**P3.** *A one-scalar threshold law predicts the layer-addition decision out of sample.* Grounds:
cost-sensitive thresholds are typically stated as scalars **[105]**. **Outcome:
UNMET in the registered one-scalar form.** Out-of-sample median relative error for a constant on the
residual product is 38.0 percent, against the registered 25 percent limit. The registered fallback
applies: the **driver** is confirmed (the residual product), the **one-scalar threshold** is false.

## 4. The construct: residual catch and the redundancy dial

Consider two supervision layers in sequence. The primary catches a fraction f of the items that need
supervision; a population fraction p0 of items are hazardous. A candidate second layer has a
standalone catch rate C2. What matters for the decision to add it is **where its catches fall**.
Define the **residual catch**

    q_res = P(layer catches | primary missed)
    q_red = P(layer catches | primary caught)

and the alignment **alpha = q_red - q_res**. Equal accuracy does not imply equal alpha, and alpha is
what the layer's marginal value depends on. To make this testable we introduce a dial that moves the
layer's catches between the two populations while holding its accuracy **exactly** fixed:

    q_red = beta * C2 / f
    q_res = (1 - beta) * C2 / (1 - f)

so that f * q_red + (1 - f) * q_res = C2 for every beta. The dial has three interpretable values.
At **beta = 1** the layer is perfectly aligned: every catch lands on an item the primary already
caught, and the marginal catch is exactly zero. At **beta = 0** the layer is perfectly
complementary. At **beta = f** we recover q_res = q_red = C2 — which is precisely the classical
**independence** assumption **[14, 15]**. Independence is
therefore a single point on this dial, not a regime, and the single point at which a practitioner
who never measures alignment implicitly operates.

Two consequences follow immediately and are used throughout. First, the marginal contribution of the
layer is

    marginal_catch = p0 * (1 - beta) * C2,

because the residual pool is p0 (1 - f) and q_res = (1 - beta) C2 / (1 - f), so f cancels. The
marginal value is therefore **free of the primary's accuracy** — a fact that contradicts the natural
intuition that a stronger primary makes a second layer worth less. Second, the estimand is directly
observable from logs: q_res is a conditional rate, so a deployer need not estimate beta to apply the
rule. This matters because beta is a latent construct; q_res is not.

## 5. Theory: when does adding the layer beat spending on the primary?

Adding the layer is a choice against the alternative of giving the layer's budget to the primary.
Let the primary's catch rate respond to budget, and let r = kappa2 / kappa1 be the cost ratio of a
unit of layer capacity to a unit of primary capacity. If the primary received one unit of layer
capacity it would reach f2. Adding the layer is optimal exactly when

    (1 - beta) * C2  exceeds  T(f, r, C2) = f2 - f .          (1)

The threshold T is the object of study. Under the budget model used throughout, the primary's
response composes catch in the log-odds domain,

    f2 = 1 - exp( -( H(f) + r * H(C2) ) ),     H(x) = -log(1 - x),       (2)

so T depends jointly on f, on r, and on C2. Three structural facts follow, and each is checked
against simulation rather than asserted (Section 6):

**S1.** T is not a constant: it moves with all three arguments, so any rule that fits one number
will fail on the region that number does not cover.
**S2.** The decision rule is nevertheless writable in deployable variables, because q_res and f are
observable from a log while beta need not be. Recomputing T from the primary's own observed budget
response is the **operational** form.
**S3.** The classical independence reading (assume beta = f, therefore always add) predicts T = 0 for
every cell, i.e. it never declines to add a layer. It is the correct rule only at one dial value.

The final element is the capacity **allocation**. A layer distributes its capacity over strata, and
strata differ in how much hazard they hold. Writing u for the capacity allocation over strata, the
catch available to layer k is bounded by the remaining hazard in each stratum:

    marginal_k = sum_s min( capacity * u_s , remaining_hazard_s ).      (3)

Equation 3 is what makes the composition question of Section 7.4 non-trivial: two configurations
can share capacity and nominal alignment and still allocate differently, and the min() makes the
difference persistent rather than cosmetic.

## 6. Experimental setup

All experiments are deterministic given seeds and run on CPU. Four instruments were built in
sequence, each augmenting rather than replacing its predecessor; every headline number in this
paper is emitted by one of them and reproduced by a single command (Section 6.1).

- **v0** (`instrument_v0.py`) establishes the construct: 400,000 items per cell, f = 0.30, C2 = 0.15,
  p0 = 0.20. It checks accuracy invariance across the dial, the monotone decline of marginal catch,
  endpoint reproduction, layer inertness, and recovery of alpha including the independence control.
  **19/19 reductions.**
- **v1** (`instrument_v1.py`) measures the marginal-value surface over (beta, cost ratio) with four
  baselines, and locates the inversion region. **18/18 checks.**
- **v2** (`instrument_v2.py`) performs the out-of-sample law race required by the registration: fit
  on 4 families x 3 cost ratios x 5 layer accuracies x 5 dial values (300 cells), score on 3
  families, 4 cost ratios, 7 accuracies and 6 dial values **never fitted** (504 held-out cells,
  disjointness asserted on all four axes). The predicted quantity is T, the metric is **median
  relative error** as registered. **14/14 checks.**
- **v3** (`instrument_v3.py`) calibrates, composes and adversarially stresses the model. **24/25
  checks**, where the single failure is a registered prediction the instrument refuted (Section 7.5).

**Reproduction.** `bash reproduce.sh` runs all four instruments and validates the emitted artefacts
against committed expectations; `validate.py` asserts the numbers quoted in this manuscript against
the JSON they come from, and `trace_check.py` checks that every quoted figure has a producing cell.
Random seeds are fixed and recorded; the artefacts carry a content digest.

### 6.1 Calibration protocol

The v3 calibration required bounding the regime parameters from real systems. The arXiv export API
was unavailable for compound queries throughout (repeated timeouts and HTTP 429 across retries), so
the **declared fallback transport** was used: `arxiv.org/abs` abstract pages and `arxiv.org/html`
full texts, with the transport recorded per entry. Each calibration cell carries a verbatim quote,
the numbers the source reports, and the derivation from those numbers to (f, C2, beta, r). Every
quote is verified against a committed capture, and the verifier is **two-sided** (a mutated quote is
rejected). The resulting set is 12 cells drawn from 10 independent published systems, of which 7 are
quantitative and 5 are construct or mechanism anchors. The quantitative anchors are a compilation
repair loop that raises success from 36-55 percent to 64-100 percent, i.e. a near-zero alignment on
the failed population **[112]**; two formalisation pipelines that agree on 31.0 percent of
their overlap **[109]**; a three-layer ECC stack whose layers evolved independently
**[110]**; a verification tool whose finding a human independently re-files
**[111]**; a human layer that is anti-correlated with the primary **[113]**; and an
allocation anchor whose noise is negatively correlated with feature importance at -0.81
**[114]**. The mechanism anchors establish the direction of the cost ratio
**[115]**, that uncertainty sources are separable for analysis but "not independent in
practice" **[116]**, that redundant-information elimination is a named advantage of
stacked agents across six independent cohorts **[117]**, and that guardrail artifacts can
contradict one another or evolve independently **[13]**.

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
concentrated in a sparse subset of strata **[114]**. A theory of stacked supervision that
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
that this happens **[83, 84, 85]**.
The clearest quantitative anchor we found reports that the added human layer is **anti-correlated**
with the primary: deferral concentrates on the minority class and participants perform worse on
whichever class is the majority in their condition **[113]**.

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
literature **[101, 12]** — into a decision rule with a
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

[1] Alberto Bacchelli, Christian Bird. Expectations, outcomes, and challenges of modern code review. 2013 35th International Conference on Software Engineering (ICSE), 2013. DOI: 10.1109/icse.2013.6606617
[2] Caitlin Sadowski, Emma Söderberg, Luke Church, et al.. Modern code review. Proceedings of the 40th International Conference on Software Engineering: Software Engineering in Practice, 2018. DOI: 10.1145/3183519.3183525
[3] Lightman, Hunter, Kosaraju, Vineet, Burda, Yura, et al.. Let's Verify Step by Step. arXiv preprint, 2023. DOI: 10.48550/arXiv.2305.20050
[4] Cobbe, Karl, Kosaraju, Vineet, Bavarian, Mohammad, et al.. Training Verifiers to Solve Math Word Problems. arXiv preprint, 2021. DOI: 10.48550/arXiv.2110.14168
[5] Geifman, Yonatan, El-Yaniv, Ran. Selective Classification for Deep Neural Networks. arXiv preprint, 2017. DOI: 10.48550/arXiv.1705.08500
[6] Geifman, Yonatan, El-Yaniv, Ran. SelectiveNet: A Deep Neural Network with an Integrated Reject Option. arXiv preprint, 2019. DOI: 10.48550/arXiv.1901.09192
[7] C. Chow. On optimum recognition error and reject tradeoff. IEEE Transactions on Information Theory, 1970. DOI: 10.1109/tit.1970.1054406
[8] Mozannar, Hussein, Sontag, David. Consistent Estimators for Learning to Defer to an Expert. arXiv preprint, 2020. DOI: 10.48550/arXiv.2006.01862
[9] Keswani, Vijay, Lease, Matthew, Kenthapadi, Krishnaram. Towards Unbiased and Accurate Deferral to Multiple Experts. arXiv preprint, 2021. DOI: 10.48550/arXiv.2102.13004
[10] Verma, Rajeev, Nalisnick, Eric. Calibrated Learning to Defer with One-vs-All Classifiers. arXiv preprint, 2022. DOI: 10.48550/arXiv.2202.03673
[11] Ludmila I. Kuncheva, Christopher J. Whitaker. Measures of Diversity in Classifier Ensembles and Their Relationship with the Ensemble Accuracy. Machine Learning, 2003. DOI: 10.1023/a:1022859003006
[12] B. Littlewood, D.R. Miller. Conceptual modeling of coincident failures in multiversion software. IEEE Transactions on Software Engineering, 1989. DOI: 10.1109/32.58771
[13] Stolze, Markus, Strässle, Mirco. When Review Alone No Longer Scales: Layered Supervision in AI-Assisted Software Engineering. arXiv preprint, 2026. DOI: 10.48550/arXiv.2608.26316
[14] Leo Breiman. Bagging predictors. Machine Learning, 1996. DOI: 10.1007/bf00058655
[15] Thomas G. Dietterich. Ensemble Methods in Machine Learning. Lecture Notes in Computer Science, 2000. DOI: 10.1007/3-540-45014-9_1
[16] Jiang, Heinrich, Kim, Been, Guan, Melody Y., et al.. To Trust Or Not To Trust A Classifier. arXiv preprint, 2018. DOI: 10.48550/arXiv.1805.11783
[17] Alves, Jean V., Leitão, Diogo, Jesus, Sérgio, et al.. Cost-Sensitive Learning to Defer to Multiple Experts with Workload Constraints. arXiv preprint, 2024. DOI: 10.48550/arXiv.2403.06906
[18] Zhang, Zheng, Nguyen, Cuong, Wells, Kevin, et al.. Coverage-Constrained Human-AI Cooperation with Multiple Experts. arXiv preprint, 2024. DOI: 10.48550/arXiv.2411.11976
[19] Tailor, Dharmesh, Patra, Aditya, Verma, Rajeev, et al.. Learning to Defer to a Population: A Meta-Learning Approach. arXiv preprint, 2024. DOI: 10.48550/arXiv.2403.02683
[20] Ramgolam, Nilesh, Carneiro, Gustavo, Chen, Hsiang-Ting. Learning To Defer To A Population With Limited Demonstrations. arXiv preprint, 2025. DOI: 10.48550/arXiv.2510.19351
[21] Rayan, Sahana, Tewari, Ambuj. Learning to Partially Defer for Sequences. arXiv preprint, 2025. DOI: 10.48550/arXiv.2502.01459
[22] Joshi, Shalmali, Parbhoo, Sonali, Doshi-Velez, Finale. Learning-to-defer for sequential medical decision-making under uncertainty. arXiv preprint, 2021. DOI: 10.48550/arXiv.2109.06312
[23] Hemmer, Patrick, Thede, Lukas, Vössing, Michael, et al.. Learning to Defer with Limited Expert Predictions. arXiv preprint, 2023. DOI: 10.48550/arXiv.2304.07306
[24] Okati, Nastaran, De, Abir, Gomez-Rodriguez, Manuel. Differentiable Learning Under Triage. arXiv preprint, 2021. DOI: 10.48550/arXiv.2103.08902
[25] Liu, Jessie, Gallego, Blanca, Barbieri, Sebastiano. Incorporating Uncertainty in Learning to Defer Algorithms for Safe Computer-Aided Diagnosis. arXiv preprint, 2021. DOI: 10.48550/arXiv.2108.07392
[26] Mozannar, Hussein, Satyanarayan, Arvind, Sontag, David. Teaching Humans When To Defer to a Classifier via Exemplars. arXiv preprint, 2021. DOI: 10.48550/arXiv.2111.11297
[27] Keswani, Vijay, Lease, Matthew, Kenthapadi, Krishnaram. Designing Closed Human-in-the-loop Deferral Pipelines. arXiv preprint, 2022. DOI: 10.48550/arXiv.2202.04718
[28] Hemmer, Patrick, Schellhammer, Sebastian, Vössing, Michael, et al.. Forming Effective Human-AI Teams: Building Machine Learning Models that Complement the Capabilities of Multiple Experts. arXiv preprint, 2022. DOI: 10.48550/arXiv.2206.07948
[29] Charusaie, Mohammad-Amin, Mozannar, Hussein, Sontag, David, et al.. Sample Efficient Learning of Predictors that Complement Humans. arXiv preprint, 2022. DOI: 10.48550/arXiv.2207.09584
[30] Banerjee, Debodeep, Teso, Stefano, Passerini, Andrea. Learning to Guide Human Experts via Personalized Large Language Models. arXiv preprint, 2023. DOI: 10.48550/arXiv.2308.06039
[31] Alves, Jean V., Leitão, Diogo, Jesus, Sérgio, et al.. FiFAR: A Fraud Detection Dataset for Learning to Defer. arXiv preprint, 2023. DOI: 10.48550/arXiv.2312.13218
[32] Tariq, Shahroz, Chhetri, Mohan Baruwal, Nepal, Surya, et al.. A2C: A Modular Multi-stage Collaborative Decision Framework for Human-AI Teams. arXiv preprint, 2024. DOI: 10.48550/arXiv.2401.14432
[33] Palomba, Filippo, Pugnana, Andrea, Alvarez, José Manuel, et al.. A Causal Framework for Evaluating Deferring Systems. arXiv preprint, 2024. DOI: 10.48550/arXiv.2405.18902
[34] Charusaie, Mohammad-Amin, Samadi, Samira. A Unifying Post-Processing Framework for Multi-Objective Learn-to-Defer Problems. arXiv preprint, 2024. DOI: 10.48550/arXiv.2407.12710
[35] Strong, Joshua, Saha, Pramit, Ibrahim, Yasin, et al.. Identity-Free Deferral For Unseen Experts. arXiv preprint, 2025. DOI: 10.48550/arXiv.2502.10533
[36] Ferrara, Antonio, Pugnana, Andrea, Bonchi, Francesco, et al.. Bounded-Abstention Pairwise Learning to Rank. arXiv preprint, 2025. DOI: 10.48550/arXiv.2505.23437
[37] Jalalvand, Fatemeh, Chhetri, Mohan Baruwal, Nepal, Surya, et al.. Adaptive alert prioritisation in security operations centres via learning to defer with human feedback. arXiv preprint, 2025. DOI: 10.48550/arXiv.2506.18462
[38] Zellinger, Michael J., Thomson, Matt. Fail Fast, or Ask: Mitigating the Deficiencies of Reasoning LLMs with Human-in-the-Loop Systems Engineering. arXiv preprint, 2025. DOI: 10.48550/arXiv.2507.14406
[39] Mitton, Joshua, Bhattacharyya, Prarthana, Abboud, Ralph, et al.. Knowing When to Defer: Selective Prediction for Responsible Knowledge Tracing. arXiv preprint, 2025. DOI: 10.48550/arXiv.2509.21514
[40] Pugnana, Andrea, De Toni, Giovanni, Barbera, Cesare, et al.. To Ask or Not to Ask: Learning to Require Human Feedback. arXiv preprint, 2025. DOI: 10.48550/arXiv.2510.08314
[41] Zhang, Zheng, Nguyen, Cuong C., Rosewarne, David, et al.. Fatigue-Aware Learning to Defer via Constrained Optimisation. arXiv preprint, 2026. DOI: 10.48550/arXiv.2604.00904
[42] Tian, Qiuyu, Sun, Haoliang, Wang, Yunshan, et al.. DeferredSeg:A Multi-Expert Deferral Framework for Medical Image Segmentation. arXiv preprint, 2026. DOI: 10.48550/arXiv.2604.12411
[43] Kondadadi, Rishik, Ortega, John E.. L2D-Clinical: Learning to Defer for Adaptive Model Selection in Clinical Text Classification. arXiv preprint, 2026. DOI: 10.48550/arXiv.2604.13285
[44] Zhang, Zheng, Masroor, Milad, Nguyen, Cuong, et al.. People-Centred Medical Image Analysis via Fairness-Aware Human-AI Cooperation. arXiv preprint, 2026. DOI: 10.48550/arXiv.2604.26991
[45] Yin, Tongxin, Ton, Jean-François, Guo, Ruocheng, et al.. Fair Classifiers that Abstain without Harm. arXiv preprint, 2023. DOI: 10.48550/arXiv.2310.06205
[46] Whitehead, Spencer, Petryk, Suzanne, Shakib, Vedaad, et al.. Reliable Visual Question Answering: Abstain Rather Than Answer Incorrectly. arXiv preprint, 2022. DOI: 10.48550/arXiv.2204.13631
[47] Firouzkouhi, Arad, Mirzaeedodangeh, Omid, Lindemann, Lars. Sample-Efficient Expert Query Control in Active Imitation Learning via Conformal Prediction. arXiv preprint, 2025. DOI: 10.48550/arXiv.2512.00453
[48] Wundram, Anna M., Baumgartner, Christian F.. Is Uncertainty Quantification a Viable Alternative to Learned Deferral?. arXiv preprint, 2025. DOI: 10.48550/arXiv.2508.02319
[49] Bary, Tim, Macq, Benoît, Petit, Louis. No Need for Learning to Defer? A Training Free Deferral Framework to Multiple Experts through Conformal Prediction. arXiv preprint, 2025. DOI: 10.48550/arXiv.2509.12573
[50] Leo Breiman. Random Forests. Machine Learning, 2001. DOI: 10.1023/a:1010933404324
[51] Yoav Freund, Robert E Schapire. A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting. Journal of Computer and System Sciences, 1997. DOI: 10.1006/jcss.1997.1504
[52] David H. Wolpert. Stacked generalization. Neural Networks, 1992. DOI: 10.1016/s0893-6080(05)80023-1
[53] Robert A. Jacobs, Michael I. Jordan, Steven J. Nowlan, et al.. Adaptive Mixtures of Local Experts. Neural Computation, 1991. DOI: 10.1162/neco.1991.3.1.79
[54] G.E. Hinton. Products of experts. 9th International Conference on Artificial Neural Networks: ICANN '99, 1999. DOI: 10.1049/cp:19991075
[55] Shazeer, Noam, Mirhoseini, Azalia, Maziarz, Krzysztof, et al.. Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer. arXiv preprint, 2017. DOI: 10.48550/arXiv.1701.06538
[56] Lakshminarayanan, Balaji, Pritzel, Alexander, Blundell, Charles. Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles. arXiv preprint, 2016. DOI: 10.48550/arXiv.1612.01474
[57] Buschjäger, Sebastian, Pfahler, Lukas, Morik, Katharina. Generalized Negative Correlation Learning for Deep Ensembling. arXiv preprint, 2020. DOI: 10.48550/arXiv.2011.02952
[58] Liu, Ling, Wei, Wenqi, Chow, Ka-Ho, et al.. Deep Neural Network Ensembles against Deception: Ensemble Diversity, Accuracy and Robustness. arXiv preprint, 2019. DOI: 10.48550/arXiv.1908.11091
[59] Chen, Ling, Shi, Hongyu. DexDeepFM: Ensemble Diversity Enhanced Extreme Deep Factorization Machine Model. arXiv preprint, 2021. DOI: 10.48550/arXiv.2104.01924
[60] Busk, Jonas, Schmidt, Mikkel N., Winther, Ole, et al.. Graph Neural Network Interatomic Potential Ensembles with Calibrated Aleatoric and Epistemic Uncertainty on Energy and Forces. arXiv preprint, 2023. DOI: 10.48550/arXiv.2305.16325
[61] Vita, Joshua A., Samanta, Amit, Zhou, Fei, et al.. LTAU-FF: Loss Trajectory Analysis for Uncertainty in Atomistic Force Fields. arXiv preprint, 2024. DOI: 10.48550/arXiv.2402.00853
[62] Liu, Kai, Wei, Zixiong, Gao, Wei, et al.. Heterogeneous Ensemble Enables a Universal Uncertainty Metric for Atomistic Foundation Models. arXiv preprint, 2025. DOI: 10.48550/arXiv.2507.21297
[63] Feng, Shihan, Zhang, Cheng, Xi, Michael, et al.. Exploring the Rashomon Set for Concept-Based Models. arXiv preprint, 2025. DOI: 10.48550/arXiv.2511.19636
[64] Wang, Xuezhi, Wei, Jason, Schuurmans, Dale, et al.. Self-Consistency Improves Chain of Thought Reasoning in Language Models. arXiv preprint, 2022. DOI: 10.48550/arXiv.2203.11171
[65] Wei, Jason, Wang, Xuezhi, Schuurmans, Dale, et al.. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. arXiv preprint, 2022. DOI: 10.48550/arXiv.2201.11903
[66] Madaan, Aman, Tandon, Niket, Gupta, Prakhar, et al.. Self-Refine: Iterative Refinement with Self-Feedback. arXiv preprint, 2023. DOI: 10.48550/arXiv.2303.17651
[67] Shinn, Noah, Cassano, Federico, Berman, Edward, et al.. Reflexion: Language Agents with Verbal Reinforcement Learning. arXiv preprint, 2023. DOI: 10.48550/arXiv.2303.11366
[68] Yao, Shunyu, Zhao, Jeffrey, Yu, Dian, et al.. ReAct: Synergizing Reasoning and Acting in Language Models. arXiv preprint, 2022. DOI: 10.48550/arXiv.2210.03629
[69] Yao, Shunyu, Yu, Dian, Zhao, Jeffrey, et al.. Tree of Thoughts: Deliberate Problem Solving with Large Language Models. arXiv preprint, 2023. DOI: 10.48550/arXiv.2305.10601
[70] Bai, Yuntao, Kadavath, Saurav, Kundu, Sandipan, et al.. Constitutional AI: Harmlessness from AI Feedback. arXiv preprint, 2022. DOI: 10.48550/arXiv.2212.08073
[71] Zheng, Lianmin, Chiang, Wei-Lin, Sheng, Ying, et al.. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv preprint, 2023. DOI: 10.48550/arXiv.2306.05685
[72] Wu, Zijian, Kong, Lingkai, Zhang, Wenwei, et al.. OPV: Outcome-based Process Verifier for Efficient Long Chain-of-Thought Verification. arXiv preprint, 2025. DOI: 10.48550/arXiv.2512.10756
[73] Zhang, Jipeng, Miao, Kehao, Pi, Renjie, et al.. VL-GenRM: Enhancing Vision-Language Verification via Vision Experts and Iterative Training. arXiv preprint, 2025. DOI: 10.48550/arXiv.2506.13888
[74] Zhang, Liao, Chen, Tong, Wu, Xiwei, et al.. Neuro-Symbolic Generation and Validation of Memory-Aware Formal Function Specifications. arXiv preprint, 2026. DOI: 10.48550/arXiv.2603.13414
[75] Huang, Jie, Chen, Xinyun, Mishra, Swaroop, et al.. Large Language Models Cannot Self-Correct Reasoning Yet. arXiv preprint, 2023. DOI: 10.48550/arXiv.2310.01798
[76] Hasan, Mehedi, Abdar, Moloud, Khosravi, Abbas, et al.. Survey on Leveraging Uncertainty Estimation Towards Trustworthy Deep Neural Networks: The Case of Reject Option and Post-training Processing. arXiv preprint, 2023. DOI: 10.48550/arXiv.2304.04906
[77] P. Viola, M. Jones. Rapid object detection using a boosted cascade of simple features. Proceedings of the 2001 IEEE Computer Society Conference on Computer Vision and Pattern Recognition. CVPR 2001, None. DOI: 10.1109/cvpr.2001.990517
[78] Surat Teerapittayanon, Bradley McDanel, H.T. Kung. BranchyNet: Fast inference via early exiting from deep neural networks. 2016 23rd International Conference on Pattern Recognition (ICPR), 2016. DOI: 10.1109/icpr.2016.7900006
[79] Tal Schuster, Adam Fisch, Jai Gupta, et al.. Confident Adaptive Language Modeling. Advances in Neural Information Processing Systems 35, 2022. DOI: 10.52202/068431-1269
[80] Liu, Nelson F., Lin, Kevin, Hewitt, John, et al.. Lost in the Middle: How Language Models Use Long Contexts. arXiv preprint, 2023. DOI: 10.48550/arXiv.2307.03172
[81] Vaswani, Ashish, Shazeer, Noam, Parmar, Niki, et al.. Attention Is All You Need. arXiv preprint, 2017. DOI: 10.48550/arXiv.1706.03762
[82] Yann LeCun, Yoshua Bengio, Geoffrey Hinton. Deep learning. Nature, 2015. DOI: 10.1038/nature14539
[83] Lisanne Bainbridge. Ironies of automation. Automatica, 1983. DOI: 10.1016/0005-1098(83)90046-8
[84] Raja Parasuraman, Victor Riley. Humans and Automation: Use, Misuse, Disuse, Abuse. Human Factors: The Journal of the Human Factors and Ergonomics Society, 1997. DOI: 10.1518/001872097778543886
[85] J. D. Lee, K. A. See. Trust in Automation: Designing for Appropriate Reliance. Human Factors: The Journal of the Human Factors and Ergonomics Society, 2004. DOI: 10.1518/hfes.46.1.50_30392
[86] Berkeley J. Dietvorst, Joseph P. Simmons, Cade Massey. Algorithm aversion: People erroneously avoid algorithms after seeing them err. Journal of Experimental Psychology: General, 2015. DOI: 10.1037/xge0000033
[87] Peng, Sida, Kalliamvakou, Eirini, Cihon, Peter, et al.. The Impact of AI on Developer Productivity: Evidence from GitHub Copilot. arXiv preprint, 2023. DOI: 10.48550/arXiv.2302.06590
[88] Qadir, Junaid, Mumtaz, Muhammad. The Psychology of Learning from Machines: Anthropomorphic AI and the Paradox of Automation in Education. arXiv preprint, 2026. DOI: 10.48550/arXiv.2601.06172
[89] Wu, Wenqing, Xi, Haixu, Zhang, Chengzhi. Are the confidence scores of reviewers consistent with the review content? Evidence from top conference proceedings in AI. arXiv preprint, 2025. DOI: 10.48550/arXiv.2505.15031
[90] Raikote, Pranav, Randl, Korbinian, Miliou, Ioanna, et al.. CHiL(L)Grader: Calibrated Human-in-the-Loop Short-Answer Grading. arXiv preprint, 2026. DOI: 10.48550/arXiv.2603.11957
[91] Yang, Wei, Cao, Defu, Pang, Jiacheng, et al.. Adaptive Collaboration with Humans: Metacognitive Policy Optimization for Multi-Agent LLMs with Continual Learning. arXiv preprint, 2026. DOI: 10.48550/arXiv.2603.07972
[92] Alvarez, Jose M., Ruggieri, Salvatore. Toward A Causal Framework for Modeling Perception. arXiv preprint, 2024. DOI: 10.48550/arXiv.2401.13408
[93] Sargeant, Holli, Jorgensen, Mackenzie, Shah, Arina, et al.. Unequal Uncertainty: Rethinking Algorithmic Interventions for Mitigating Discrimination from AI. arXiv preprint, 2025. DOI: 10.48550/arXiv.2508.07872
[94] Mouli, S. Chandra, Maddix, Danielle C., Alizadeh, Shima, et al.. Using Uncertainty Quantification to Characterize and Improve Out-of-Domain Learning for PDEs. arXiv preprint, 2024. DOI: 10.48550/arXiv.2403.10642
[95] R. E. Lyons, W. Vanderkulk. The Use of Triple-Modular Redundancy to Improve Computer Reliability. IBM Journal of Research and Development, 1962. DOI: 10.1147/rd.62.0200
[96] T. Anderson, R. Kerr. Recovery Blocks in Action: A System Supporting High Reliability. Reliable Computer Systems, 1985. DOI: 10.1007/978-3-642-82470-8_9
[97] A. Avizienis. The N-Version Approach to Fault-Tolerant Software. IEEE Transactions on Software Engineering, 1985. DOI: 10.1109/tse.1985.231893
[98] B. Randell. System structure for software fault tolerance. Proceedings of the international conference on Reliable software  -, 1975. DOI: 10.1145/800027.808467
[99] Leslie Lamport, Robert Shostak, Marshall Pease. The Byzantine Generals Problem. ACM Transactions on Programming Languages and Systems, 1982. DOI: 10.1145/357172.357176
[100] Miguel Castro, Barbara Liskov. Practical byzantine fault tolerance and proactive recovery. ACM Transactions on Computer Systems, 2002. DOI: 10.1145/571637.571640
[101] John C. Knight, Nancy G. Leveson. An experimental evaluation of the assumption of independence in multiversion programming. IEEE Transactions on Software Engineering, 1986. DOI: 10.1109/tse.1986.6312924
[102] D.E. Eckhardt, L.D. Lee. A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors. IEEE Transactions on Software Engineering, 1985. DOI: 10.1109/tse.1985.231895
[103] Stuart Russell, Eric Wefald. Principles of metareasoning. Artificial Intelligence, 1991. DOI: 10.1016/0004-3702(91)90015-c
[104] Ronald Howard. Information Value Theory. IEEE Transactions on Systems Science and Cybernetics, 1966. DOI: 10.1109/tssc.1966.300074
[105] Tom Fawcett. An introduction to ROC analysis. Pattern Recognition Letters, 2006. DOI: 10.1016/j.patrec.2005.10.010
[106] Edwin B. Wilson. Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association, 1927. DOI: 10.1080/01621459.1927.10502953
[107] B. Efron. Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics, 1979. DOI: 10.1214/aos/1176344552
[108] Yoav Benjamini, Yosef Hochberg. Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. Journal of the Royal Statistical Society Series B: Statistical Methodology, 1995. DOI: 10.1111/j.2517-6161.1995.tb02031.x
[109] Yang, Fanpeng, Li, Xing, Wang, Shuling, et al.. How Powerful are LLMs in Generating Formal Program Specifications?. arXiv preprint, 2026. DOI: 10.48550/arXiv.2608.13077
[110] Kim, Junhwan, Kim, Seunghyun, Ryu, Yesin, et al.. Cerberus: Cross-Layer ECC Co-Design for Robust and Efficient Memory Protection. arXiv preprint, 2026. DOI: 10.48550/arXiv.2605.02220
[111] Sun, Youcheng, Liu, Jiawen, Kroening, Daniel, et al.. Agentic Model Checking. arXiv preprint, 2026. DOI: 10.48550/arXiv.2605.21434
[112] Huang, An-yi. HELIOS: An LLM-Driven Autonomous Indirect Trajectory Optimization Agent. arXiv preprint, 2026. DOI: 10.48550/arXiv.2607.24051
[113] Pesenti, Dario, Bogani, Alessandro, Teso, Stefano, et al.. Too Much of the Same: From Algorithmic to Human Bias in Learning to Defer. arXiv preprint, 2026. DOI: 10.48550/arXiv.2608.28050
[114] Islam, MD Shafikul, Bappy, Mahathir Mohammad, Tushar, Saifur Rahman, et al.. Feature-Aware Anisotropic Local Differential Privacy for Utility-Preserving Graph Representation Learning in Metal Additive Manufacturing. arXiv preprint, 2026. DOI: 10.48550/arXiv.2604.05077
[115] Naito, Hiroki. Flow-by-Flow:Content-Judgment Bypass for Governing AI Output in High-Loss Domains. arXiv preprint, 2026. DOI: 10.48550/arXiv.2608.07474
[116] Boudiaf, Abderrahmene, Hussain, Irfan, Javed, Sajid. Uncertainty-Aware Decision Making in Multimodal Large Language Models. arXiv preprint, 2026. DOI: 10.48550/arXiv.2608.17084
[117] Shen, Chen, Zhang, Wanqing, Li, Kehan, et al.. FEAT: A Multi-Agent Forensic AI System with Domain-Adapted Large Language Model for Automated Cause-of-Death Analysis. arXiv preprint, 2025. DOI: 10.48550/arXiv.2508.07950

