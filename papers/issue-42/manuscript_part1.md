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
primary's own budget response decides 100 percent of the 60 calibrated held-out cells (99.2 percent
on the synthetic grid). Third, and most sharply, **identical summary
statistics do not determine composition**: two stacked configurations with the same capacity and the
same nominal alignment deliver cumulative four-layer catches 8.5 percent apart, because allocation —
not the summary statistic — decides which strata saturate. We also report a registered prediction
that our own instrument refuted, scored exactly as registered.

## 1. Introduction

Supervision in computing systems is almost never a single mechanism. Code changes pass a reviewer
**[@bacchelli2013codereview; @sadowski2018googlereview]** and then a continuous-integration pipeline;
an autoscaler acts and then a monitoring rule fires; a model answers and a verifier scores the answer
**[@lightman2023verify; @cobbe2021verifiers]**; a human decision is checked by a second human. The
design question behind every such stack is the same: **does adding the next check buy more than
spending the same capacity on the check we already have?**

The literature answers a neighbouring question. Selective prediction asks when a model should
abstain **[@{selectivegeifman2017}; @{selectivenet2019}; @{chow1970reject}]**; learning to defer asks
when a model should hand an item to a human **[@{mozannar2020defer}; @{unbiaseddeferral2021};
@{calibrateddefer2022}]**; ensemble theory asks how correlated voters change aggregate accuracy
**[@{kuncheva2003diversity}; @{littlewood1989coincident}]**. The closest prior work asks the layered question directly but not quantitatively: a qualitative
interview study with five practitioners finds that organisations distribute supervision across
multiple guardrail layers and that the question of how existing guardrails evolve in response is
open **[@{layered2026}]**. It reports the *shape* of the problem — layers, shifting load, no
measurement — and we take that shape as given here.

All three concern a **single** gate:
should this item be escalated, abstained on, or decided? None of them prices the **second** gate —
the one that exists because the first gate is already deployed and already imperfect.

This paper argues that the missing quantity is the **residual catch profile**. Two second layers can
have the same accuracy and be worth very different amounts, because worth depends on **where** the
catches fall: on items the first layer already got right (redundant), or on items it missed
(complementary). We make this testable by introducing a **dial** that moves a layer's catches between
those two populations while holding its overall catch rate exactly constant. Independence — the
classical assumption that a second layer's errors are unrelated to the first's **[@{breiman1996bagging};
@{dietterich2000ensemble}]** — turns out to be one point on that dial, not a default.

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
7.1 measures it at 0.527 of achievable reduction on that instrument's 300-cell grid, and Section 7.2
at 0.689 on its 504-cell held-out grid, against 1.000 for a residual-catch rule on both), and that
the correct rule is a comparison between the residual product and the primary's marginal response.

## 2. Related work

### 2.1 Learning to defer and selective prediction

Selective prediction formalises abstention: Chow derived the optimal error-reject tradeoff
**[@{chow1970reject}]**, and modern treatments learn a selector jointly with the predictor
**[@{selectivegeifman2017}; @{selectivenet2019}]** or calibrate the score before thresholding
**[@{jiang2018trust}]**. Learning to defer extends the gate to a human expert, with consistent
surrogate losses **[@{mozannar2020defer}]**, multiple experts **[@{unbiaseddeferral2021};
@{workload2024}; @{coverage2024}]**, populations rather than individuals **[@{deferpopulation2024};
@{popdemos2025}]**, sequences **[@{partialdefer2025}; @{seqdefer2021}]**, and always with a workload
or coverage constraint **[@{coverage2024}; @{limitedexpert2023}]**.

**Specific difference.** This literature asks **whether to defer this item** and evaluates the
resulting human-machine team. We ask a question it does not pose: given that a gate already exists
and is already imperfect, **where should the next unit of supervision capacity go**, and what
measurable property of the candidate layer decides that? Deferral work treats the human as the
second stage and measures accuracy; we treat the stage as arbitrary (a human, a verifier, a memory
checker, an ECC layer) and measure the **overlap of its catches with the previous stage's failures**.
The design space around the gate is now well mapped: triage and differentiability of the deferral
rule **[@{triage2021}]**, uncertainty-aware deferral **[@{uncertaintydefer2021}]**, teaching the human
when to defer **[@{exemplars2021}]**, closed-loop pipeline design **[@{closedloop2022}]**, predictors
built to complement a specific human **[@{complement2022}; @{sampleefficient2022}]**, guiding experts
with personalised models **[@{guideexperts2023}]**, and application-specific instantiations in fraud
**[@{fifar2023}]**, team coordination **[@{a2c2024}]**, causal evaluation of deferring systems
**[@{causaldefer2024}]**, multi-objective post-processing **[@{multidefer2024}]**, unseen experts
**[@{identityfree2025}]**, ranking **[@{abstainrank2025}]**, security operations
**[@{socdefer2025}]**, reasoning agents **[@{failfast2025}]**, knowledge tracing **[@{knowdefer2025}]**,
explicit requests for human input **[@{ask2025}]**, fatigue-constrained deferral **[@{fatigue2026}]**,
segmentation **[@{deferredseg2026}]**, clinical model selection **[@{l2dclinical2026}]**, fair
cooperation **[@{faircoop2026}; @{abstainfair2023}]**, abstention in multimodal QA
**[@{vqaabstain2022}]**, and conformal control of expert queries **[@{querycontrol2025}]**.

Recent work has begun to question whether uncertainty quantification can substitute for deferral
**[@{uqvsdefer2025}]** and whether deferral is needed at all **[@{nodefer2025}]**; our construct
explains why those questions are ill-posed without a residual-catch measurement: a layer's value is
not a property of its confidence but of its failure-mode alignment with what precedes it.

### 2.2 Ensembles, diversity and correlated failure

Ensembles improve accuracy by combining voters **[@{breiman1996bagging}; @{breiman2001forests};
@{freund1997boosting}]**, stacked **[@{wolpert1992stacked}]** or combined as mixtures and products
**[@{jacobs1991mixture}; @{hinton1999product}; @{shazeer2017moe}]**, and diversity is the accepted
explanatory variable **[@{dietterich2000ensemble}; @{kuncheva2003diversity}]**, with deep ensembles
supplying calibrated uncertainty **[@{deepensembles2016}]** and negative-correlation training
pushing diversity explicitly **[@{negcorr2020}]**. Adversarial ensembling studies diversity under
attack **[@{deceptionensembles2019}]**, and domain applications continue the pattern
**[@{dexdeepfm2021}; @{gnnensembles2023}; @{ltauf2024}; @{heteroens2025}; @{rashomon2025}]**.

**Specific difference.** Diversity measures are properties of a **parallel** set: they quantify how
much voters disagree. Our dial is a property of a **sequential** pair and is defined against the
previous layer's *errors*, not against other voters. This distinction matters numerically: a pair can
be maximally diverse in the ensemble sense while the second layer's catches fall entirely on items
the first already caught, in which case its marginal catch is exactly zero — a case ensemble theory
does not isolate because it does not condition on the first layer's outcome.

### 2.3 Verification layers, critics and cascades

Modern pipelines verify rather than trust: process reward models score reasoning steps
**[@{lightman2023verify}; @{cobbe2021verifiers}]**, self-consistency samples and votes
**[@{wang2023selfconsistency}; @{wei2022cot}]**, self-refinement and reflection critique an output
with the same model **[@{madaan2023selfrefine}; @{shinn2023reflexion}; @{yao2022react};
@{yao2023tree}]**, constitutional methods use AI feedback **[@{bai2022constitutional}]**, judges
grade outputs **[@{zheng2023judge}]**, and dedicated verifiers are trained for the role
**[@{opv2025}; @{vlgenrm2025}; @{neuroformal2026}]**. Failures of self-correction are documented
**[@{huang2023selfcorrect}]**, uncertainty-based trustworthiness is surveyed **[@{uqsurvey2023}]**, and
the classical cascade — early exit, boosting, staged detection — predates all of it
**[@{viola2001cascade}; @{branchynet2016}; @{confidadptive2022}]**. Long-context behaviour adds its
own failure modes **[@{liu2023lostmiddle}]**, and the transformer substrate is universal
**[@{vaswani2017attention}; @{lecun2015deeplearning}]**.

**Specific difference.** These systems report that a verifier **helps**, usually as an accuracy
delta against no verifier. That comparison cannot distinguish a verifier that catches new failures
from one that re-catches known ones, which is precisely the distinction our dial isolates. We
therefore report a quantity absent from these evaluations: the catch rate **conditional on the
previous layer having failed**, and the complementary rate conditional on it having succeeded.

### 2.4 Human oversight, automation bias and AI-assisted engineering

Human factors research has long warned that added automation changes the human's own behaviour:
ironies of automation **[@{bainbridge1983ironies}]**, use-misuse-disuse-abuse **[@{parasuraman1997automationbias}]**,
appropriate reliance and calibrated trust **[@{leesee2004trust}]**, and algorithm aversion after
observed error **[@{dietvorst2015aversion}]**. Engineering studies show review is the binding
constraint **[@{bacchelli2013codereview}; @{sadowski2018googlereview}]** and that AI assistance shifts
where the load lands **[@{peng2023copilot}]**. Recent work examines machine behaviour on humans
**[@{psychmachines2026}]**, reviewer confidence signals **[@{reviewerconfidence2025}]**, calibrated
human-in-the-loop grading **[@{chilgrader2026}]**, metacognitive collaboration policies
**[@{metacog2026}]**, perception models **[@{causalperception2024}]**, unequal uncertainty across
groups **[@{unequalunc2025}]**, and out-of-domain uncertainty **[@{oodunc2024}]**.

**Specific difference (the closest work).** The layered-supervision interview study
**[@{layered2026}]** reports that guardrail layers exist, that load shifts between them, and that
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
**[@{lyons1962tmr}]**, recovery blocks **[@{recoveryblocks1985}]**, N-version programming
**[@{avizienis1985nversion}; @{randell1975faulttolerance}]**, and replicated agreement
**[@{lamport1982byzantine}; @{castro1999pbft}]**. The decisive empirical result for our purposes is
that **independence between replicas is false**: coincident failures are real and measurable
**[@{knight1986nversion}; @{littlewood1989coincident}; @{eckhardt1985coincident}]**, which is exactly
the failure our dial parameterises.

**Specific difference.** This literature measures whether replicas fail together. We reuse its
central caution — that independent failure cannot be assumed — but convert it from a warning into a
**design dial with a decision rule attached**. Rather than reporting that dependence exists, we ask
at what dependence the added replica stops being worth its budget, and show that the answer depends
on the primary's response curve rather than on the dependence alone.

### 2.6 Decision-theoretic foundations

Metareasoning prices the cost of computation **[@{russell1991metareasoning}]**; information value
theory prices information before it arrives **[@{howard1966valueinfo}]**; cost-sensitive learning
shifts thresholds when errors are unequally priced, with ROC analysis as the standard instrument
**[@{fawcett2006roc}]**. Statistical machinery used throughout: Wilson intervals **[@{wilson1927probable}]**,
the bootstrap **[@{efron1979bootstrap}]**, and false-discovery control for multiplicity
**[@{benjamini1995fdr}]**.

**Specific difference.** Metareasoning and value-of-information ask whether to compute more at all.
Our question is narrower and more concrete — between two ways of spending a fixed supervision
budget — and its answer turns out to depend on a quantity neither framework requires you to
estimate, namely the residual catch rate of the specific candidate layer.

