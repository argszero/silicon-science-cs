---
title: "What Does a Verification Budget Buy? Location, Dispersion, and the Sample-Size Ceiling of Trustless Re-Execution"
author: "how2how2how2-arch"
contribution_level: theory+empirics
---

# What Does a Verification Budget Buy? Location, Dispersion, and the Sample-Size Ceiling of Trustless Re-Execution

**Contribution level**: `theory+empirics` — a construct with closed-form consequences, validated
on a synthetic ground-truth family, with baseline comparison and multi-stream statistics.
**Artifact**: this directory. `bash reproduce.sh` rebuilds every number and every figure below.

---

## Abstract

Trustless verification of a nondeterministic pipeline is increasingly done by re-execution: a
verifier runs the pipeline `k` times and compares a policy-pinned metric against a threshold.
The obvious question — how many re-executions are enough — is usually answered by a single
comparison at one operating point. We derive and then measure the whole response curve. For a
mean test at level `alpha`, detection power against a node whose divergence shifts the metric
mean by `delta_D` with dispersion `sigma_D` is `Phi((sqrt(k) delta_D - c_alpha)/sigma_D)`:
exactly two numbers, the node's own mean and standard deviation, fix its detectability. Three
consequences are counter-intuitive, and they are what we test. First, **where** the budget helps is
a transition band around the threshold, and it is the *comparison between rules* — not the power
— that is non-monotone in the budget: power is monotone in `k` for a fixed node (Section 3.2),
while the quantity that is non-monotone in `k` is the construct's own approximation error
(Section 7.1). The band's measured width tracks the construct's prediction to
`0.86%` and shrinks as `1/sqrt(k)` exactly. Second, the
construct has a **ceiling** that bounds the
*prize* rather than the detection: above a saturated operating point the derived rule still
wins, but the maximum achievable gain falls to `0.00098` against
`0.9148` below it. Third, against a **location-preserving** node
whose moments match an honest node's, detection is pinned at the false-positive floor at every
budget, so one more re-execution buys nothing at all. We report a pre-registered study: four
registered criteria, all met, and three registered priors, all confirmed. A sensitivity block
then measures the construct's own limits rather than hedging them: its usable boundary is a
lattice ratio rather than a rate of convergence, the ceiling's cost is a fraction of a
percentage point, and the headline comparison is decidable for only `25` of
`42` informative cells at the budget this study ran. The practical answer to
the title question is that the marginal value of a re-execution is set by *where* the node sits
relative to the threshold and how dispersed it is — never by the budget alone.

**Keywords**: trustless verification, re-execution, nondeterministic pipelines, detection
power, sample-size ceiling, budget allocation

---

## 1. Introduction

A verifier who cannot trust a computation is increasingly told to *re-execute it*: run the
pipeline again, compare a pinned metric against a threshold, and reject the run if the metric
moves too far. This is the mechanism behind replayable evidence for autonomous agents
[1], behind the threshold rules measured for compound AI workflows [2], and
behind the general advice to sample more and sharpen the estimate. It is also where the advice
stops being useful, because the verifier's real decision is not *whether* to re-execute but
*where the next unit of budget goes* — into another re-execution, into a better-calibrated
metric, or into nothing at all.

This paper answers that question with a curve rather than a point. Our object is a mean test
with `k` re-executions against a node that chooses how its divergence moves the metric. We show
that detectability collapses onto a single coordinate, and that the consequences of that
collapse are things a one-point comparison cannot see:

1. **Where the budget helps is a band, and the rule comparison is non-monotone in the budget.**
   Power is monotone in `k` for a fixed node (Section 3.2); what the budget moves is *which* margins
   separate, and the comparison between the two rules is not monotone in it. Inside a transition
   band around the threshold the measured width matches the construct's prediction to
   `0.86%` (registered tolerance `20%`), and it
   shrinks as `1/sqrt(k)` exactly — `width * sqrt(k) / sigma` is constant to
   `0.0e+00` at every spread across `k = 8` to
   `512`.
2. **There is a ceiling, and it bounds the prize, not the detection.** Above a saturated
   operating point the difference between a well-calibrated rule and a naive one remains
   statistically resolvable but shrinks to `0.00098`, against
   `0.9148` below it.
3. **Some node behaviours are free.** A location-preserving divergence — one whose expected
   metric value is unchanged — is detected at the false-positive rate at every budget. No
   value of `k` improves the verifier's situation, and a node that best-responds to the
   verifier picks exactly that behaviour.
4. **The comparison is decidable only for a minority of operating points.** Inverting each
   cell's interval, only `25` of `42` informative cells
   certify an advantage at the budget this study ran; the streams a cell needs are set by its
   effect size (median `30`, range `11` to
   `1854`), not by the budget.

**Contributions.** Our organising quantity is not new, and we say so first: `u` in Section 3.2 is
the standard normal-approximation power of a one-sample mean test, three lines of algebra from the
sample-mean standard error, with its antecedents in the sample-size literature ([3] [4]
[5] [6]). We do not claim it as a new construct. What we contribute is what it implies
when the alternative is a *choice* rather than a fixed family:

(i) **Boundary results for the budget.** The construct's usable limit is a **lattice ratio**
`big/(sigma*sqrt(k))` rather than a rate of convergence (Section 7.1); the ceiling bounds the
**prize**, `1 - p_c`, rather than the detection, and its cost is a fraction of a percentage point
(Section 7.2); and the headline rule comparison is **decidable cell by cell for only a minority** of
informative cells at the budget we ran, with the streams each cell needs set by its effect size
(Section 7.3).
(ii) A **pre-registered** empirical study of that construct on a synthetic ground-truth family with
ground truth by construction and one external calibration cell, in which the four registered
criteria are all met (Table 1) and the three registered priors are all confirmed (Table 4).
(iii) A **persistent advantage** of the derived rule over the best matched constant threshold — a
median factor of `1.0897` — that does **not** vanish as the calibration set
grows, to `n_cal = 1000` (Section 6.3), with the mechanism, its
refutation and its correction reported together (Section 6.3.1).
(iv) A reproducing artifact in which every number in this manuscript is a view of a committed
artefact — the prose cannot drift from the data, because it contains no hand-typed measurement
(Section 10).

**Significance — whose belief changes.** Designers and auditors of verification protocols for
nondeterministic AI pipelines: verifiable-compute marketplaces, agent-observability vendors,
internal evaluation teams. The decision that changes is a budget decision. At a measured
operating point the right move may be *no further re-executions at all* (against a
location-preserving node), or a *metric recalibration* rather than more samples (where the
band has been passed) — and the median informative cell in this study needed
`30` streams to certify what `25` of
`42` cells got for free. A verifier who reads only "more samples are better"
will buy the wrong thing in both regimes.

**The scope of that argument.** Applying the rule *quantitatively* takes the node's location shift
and dispersion as inputs, and a fabricating node does not report them — which the synthetic family
supplies "by construction" and a real verifier does not. We therefore state the claim in two parts
rather than one. The **structural** half — the band, the ceiling, and the fact that a
location-preserving divergence is separated by no budget at all — holds for any verifier, because
it is a property of the mean test rather than of an estimate. The **operational** half, including
which of the two budget items to buy next, is scoped to a verifier that can estimate or bound the
two inputs; Section 3.6 states the two routes by which it might do so. Nothing in Section 6 or
Section 7 depends on that scoping, and Section 8 carries it as a threat rather than as a step we
have shown.

**Roadmap.** Section 2 positions the result. Section 3 derives the construct. Section 4 states
the pre-registered priors and criteria. Section 5 describes the instrument and its controls.
Section 6 reports the criteria and the priors. Section 7 reports the sensitivity block.
Section 8 lists the threats and argues why the result survives them. Section 9 concludes.
Section 10 states reproduction.

---

## 2. Related work

**Thresholds for trustless verification.** The closest antecedent measures a calibrated fixed
threshold against divergent and fabricated executions in a synthetic pipeline and concludes
that the threshold, not the sample size, bounds trustless verification [2]. That
measurement is taken at one honest spread on one pipeline, and its "more samples are no help"
reading is a conditional statement — it holds for a node whose divergence does not move the
metric mean, which the antecedent does not flag as conditional. Our contribution differs in
object and in kind: we treat the threshold as one of two co-chosen budget items, derive the
response *curve* rather than compare two rules at a point, and report where the antecedent's
conditional reading holds (a location-preserving node, Section 6.4) and where it fails (a
location-shifting node inside the band, Section 6.3). We also invert the antecedent's
calibration cell quantitatively rather than citing it (Section 6.1).

**Replayable evidence for autonomous runs.** A second line builds tamper-evident replay for
agent runs, with soundness conditional on a stated trusted computing base and measured
declared-stream completeness below one [1]. That work establishes *that* re-execution is
the mechanism; it does not analyse how much of it to do, and its third-party verification is
specified rather than evaluated. We take replay's soundness for granted and ask what an
additional re-execution buys once the mechanism exists.

**Classical sequential and sample-size theory.** Power analysis [3], the sequential
probability ratio test [4], group-sequential designs [5], and adaptive designs
[6] all give sample-size formulas, but they assume a fixed alternative family with no
strategic node and treat the threshold as given rather than as a budget item. Our setting
differs in exactly the two ways that matter here: the alternative is chosen by a node with its
own objective, and the threshold is derived from the same false-positive budget the sampler is
calibrated to. What we derive is the mean-test specialisation of that machinery with the
sampling cost budgeted explicitly.

**Distribution-free testing and its impossibility results.** Unrestricted alternative sets
admit no consistent test [7], which bounds what any threshold rule can promise in
the worst case; the same machinery underlies minimax lower bounds for testing [8].
Those results are asymptotic and qualitative: they give no budget-response law, and they say
nothing about the location-preserving case, where the bounding constant is exactly the
false-positive rate.

**Audit sampling against a strategic adversary.** Auditing with a limited budget against an
adversary who chooses what to hide is studied in the spot-checking literature [9], in
safety-case arguments [10], and in the sampling-based verification of learned
components [11]. The adversary there chooses *which* items to corrupt; here it
chooses *how* to corrupt a single scored metric, which is what makes the
location/dispersion split — and therefore the band and the ceiling — the organising structure.

**Ceilings, saturation and the value of a measurement.** That a measurement's value saturates
is familiar from information-theoretic treatments of experiment design [12], from the
literature on metric saturation in evaluation [13], and from cost-aware sampling in
data systems [14]. Those accounts bound the value of *information*; ours bounds the
value of *repetition* under a test whose threshold is itself a choice, which is why the ceiling
appears here as a fraction of a percentage point in *power* rather than as a vanishing
information gain.

**Trustless verification has two established implementations, and neither answers the budget
question.** Hardware attestation executes inside a minimised trusted computing base
[15] [16], which is enough to build confidential contract platforms [17] and
secure approval devices [18] but leaves the TCB itself as the attack surface [19].
Cryptographic proofs of computation avoid that assumption [20] [21]
[22] and are only now being applied to models and their training [23] [24]. Both
lines answer the question "is this the run I asked for"; for a stochastic pipeline the verifier's
question is instead "how much repetition makes a divergence visible", which is a question about the
*test*, not about the proof system.

**Reproducibility and provenance.** A large body of work makes computational results reproducible
and traceable [25] [26] [27], fixes reporting practice so that variance is
visible [28], and captures provenance as first-class data [29]. These lines change
what a verifier can *inspect*; they do not say what a verifier should spend, and they implicitly
assume that inspecting enough of the same artefact settles the matter.

**Multiplicity, stopping and peeking.** The statistics of repeated looks are well understood *given*
a fixed null hypothesis: step-up and step-down multiplicity corrections [30] [31]
[32], alpha spending across interim analyses [33], always-valid inference through
confidence sequences and e-values [34] [35], and the practical cost of peeking in
online experiments [36]. Our setting keeps the fixed-null machinery but removes the assumption
that the alternative is fixed: the node chooses its divergence, so the multiplicity problem here is
adversarial rather than procedural.

**Distribution-free machinery and its limits.** Finite-sample tools that assume no parametric family
are available — uniform convergence over function classes [37] [38], the
Dvoretzky-Kiefer-Wolfowitz bound with its sharp constant [39] [40], two-sample comparison
[41], conformal prediction for set-valued guarantees [42] [43]
[44], and minimax rates over smoothness classes [45]. Each gives a guarantee
against a *fixed* alternative class; the adversary in our setting is inside the class and picks the
member that is hardest to see, which is why the guarantee that survives is the trivial one — the
false-positive rate.

**Budget and sample size in empirical computer science.** In empirical CS the same budget question
appears as sample-size and power advice for experiments [46], as significance-testing
guidance for NLP and ML evaluation [47] [48], and as variance accounting when
benchmark scores are compared across runs [49] [50]. That literature establishes
*that* repetitions must be reported and subtracted before a comparison is made; it does not model a
counterparty that chooses its divergence, which is the case a verification budget exists to handle.

**Nondeterminism and repetition in AI evaluation.** The systems a verifier is asked to check
are stochastic by construction, and the evaluation literature has spent a decade learning what that
costs: judge-based evaluation is itself a noisy instrument [51] and is sensitive to
presentation order [52]; harness choice changes conclusions at fixed models [53]
[54]; instruction tuning and prompting change the score distribution rather than a deterministic
output [55] [56] [57]; self-consistency and verification chains buy accuracy
by *sampling more* [58] [59] [60]; and agentic and code benchmarks
report pass@k precisely because one sample is not a measurement [61] [62] [63]
[64]. Every one of those papers is, implicitly, a statement about how many executions a claim
costs — and none of them derives the marginal value of the next one against a counterparty that
chooses its divergence.

**Benchmark validity and saturation.** A benchmark can stop discriminating, and the reasons are
structural: underspecification makes a score depend on arbitrary implementation choices [65];
leaderboards create incentives that erode their own signal [66]; contamination and
overfitting to the test set inflate scores [67] [68]; and offline evaluation can
diverge from what practitioners actually need [69]. The alignment literature names the same
failure from the model side — proxies are optimised instead of goals [70], objectives
are misgeneralised [71], and reward models are over-optimised past a saturation point
[72]. Those are *ceiling* arguments about a score; ours is a ceiling argument about a
*test*, and it is why we report the ceiling as a measured bound rather than as a caution.

**Budgeted inspection, monitoring and testing.** When inspection is priced per item, the design
question is which items to inspect: red-teaming allocates a fixed attack budget [73]; property
testing fixes the number of samples per property [74]; robust optimisation prices the
worst case rather than the average [75]; runtime verification watches a running system under a
monitor budget [76]; machine-learning testing surveys the same trade-off for learned
components [77]; selective prediction and abstention decide *whether* to answer at a given
confidence [78]; outlier exposure and anomaly detection decide what to look at next
[79]; and cost-sensitive learning makes the price of an error explicit in the objective
[80]. Our verifier is an instance of this family with one unusual property: the item
under inspection chooses how it differs, so the inspection's value saturates from below.

**Allocating a sampling budget.** The data-systems literature knows that a budget buys accuracy at a
decreasing rate and that the right response is to spend it adaptively: online aggregation and
approximate query processing stop when the interval is tight enough [81] [82]; bandit
algorithms formalise exploration under a horizon [83]; query-by-committee and active learning
choose the next sample by expected information [84]; and classical optimal design chooses the
measurement that maximises information per unit cost [85]. We use those ideas only as a
contrast: in our setting the *stopping* rule is what is being questioned, because the quantity that
would justify stopping — a stable alternative — is the one the node controls.

**Inference foundations.** The test we analyse is deliberately classical: the Neyman-Pearson
formulation of size and power [86], in the Fisherian and Student traditions that fixed
the small-sample vocabulary [87] [88], with the interval estimators we use for
proportions [89] [90] and quantiles [91], the asymptotic theory that
justifies the normal approximation and its limits [92] [93], resampling where a
closed form is unavailable [94] [95], Monte-Carlo error accounting for the
estimates themselves [96], and the reporting conventions that keep a p-value from being read as
an effect size [97] [98] [99]. Two conventions matter for our own numbers: the
detector's operating point is a trade-off curve rather than a scalar [100], and when the cost of a
false accept and a false reject differ, the threshold is an economic choice, not a statistical one
[80].

**Fault-tolerant systems with adversarial participants.** The question of how much redundancy is
enough against participants that may deviate is the oldest question in this family: Byzantine
agreement bounds the number of faulty replicas a protocol can tolerate [101], and practical
Byzantine replication makes that bound an engineering parameter [102]. Those results are *exact*
bounds and they are about agreement, not about detecting a statistical divergence; our contribution
is the analogous bound for the statistical case, where the answer turns out to depend on where the
adversary moves the distribution rather than on how many replicas exist.

**Summary of the gap.** Across these lines no work maps detection power as a function of a
re-execution budget when the node chooses its divergence. Our reverse-gap search over the full
arXiv index found no paper posing the budget question in this form (Section 4); the structural
reason is that the protocol that poses it is days old at the time of writing, so the
antecedent's conditional result was read as closing the question.

---

## 3. The construct

### 3.1 Setting

A pipeline is run `k` times. Each execution yields a metric value; the verifier forms the
sample mean and rejects when it exceeds a threshold. An honest node draws from a distribution
with mean `mu` and standard deviation `sigma_h`. A divergent node draws from a distribution
with mean `mu + delta_D` and dispersion `sigma_D`. The threshold is calibrated to an honest
false-positive level `alpha`, so `tau = c_alpha * sigma_h / sqrt(k)` with
`c_alpha = Phi^-1(1 - alpha)`; at `alpha = 0.05` this gives
`c_alpha = 1.6449`.

### 3.2 Closed form

**What is and is not new here.** The expression below is the textbook normal-approximation power of
a one-sample mean test against a shifted mean: three lines of algebra from the sample-mean standard
error, with the small-sample vocabulary of the Student and Fisher tradition ([87]
[88]) and the general power function of the sample-size literature ([3] [4]
[5] [6]) as its antecedents. It is not offered as a new construct. What is new is what
the expression implies when the alternative is a *choice* rather than a fixed family: the boundary
results of Section 7 and the persistent advantage of the derived rule over a matched constant
threshold (Section 6.3).

The verifier's statistic is the sample mean, whose standard error is `sigma_h / sqrt(k)` under
the honest node and `sigma_D / sqrt(k)` under the divergent one. Detection power is therefore

    power(k, delta_D, sigma_D) = Phi(u),    u = ( sqrt(k) * delta_D - c_alpha ) / sigma_D.

Two observations follow immediately and organise the paper. First, **detectability has one
coordinate**: `u` is a single number, so two nodes with the same `u` are equally detectable no
matter how differently they are built — the measured invariance in Section 6.1. Second, because
`u` is linear in `sqrt(k)`, power is monotone in the budget *for a fixed node*; the
non-monotonicity that matters is in the comparison between rules and in the band's position,
and both follow from `u` rather than contradicting it.

### 3.3 The band

The transition band is the set of margins for which power is intermediate between the floor and
the ceiling. Differentiating `u` in the margin, the band's half-width scales as
`sigma_D / sqrt(k)`, so at fixed `sigma_D` the product `width * sqrt(k) / sigma_D` is a
constant. Equivalently, doubling the budget tightens the band by `sqrt(2)` but does not move a
node that sits outside it from "no signal" to "certain detection". This is the quantitative
form of prior P2 and the object of registered criterion (b).

**Two widths, two names.** The paper uses the word "band" for two different objects, and each is
named where it is measured so that a reader can check the law against the table:

* The **tangent band** at a fixed budget `k` (`predicted_tangent` in the instrument) is the band
  whose half-width is `sigma_D / sqrt(k)`. This is the object the width law is about: the invariant
  `width * sqrt(k) / sigma_D` is constant for it, exactly, at each fixed `k` (Section 6.2).
* The **secant band** over the design's budget range (`predicted_secant` in the instrument, taken
  over the design budget set
  `K_BAND = { 8, 32, 128, 512 }`) is the *average* of that
  half-width over the log budget range the
  experiment spans. Its width is
  `(power(k_max, delta, sigma) - power(k_min, delta, sigma)) / log(k_max / k_min)`, which is what a
  single number has to be if it is to stand for a range rather than for a point. Because it averages
  `sigma_D / sqrt(k)` over `k`, the secant width grows **sublinearly in `sigma_D`** while the tangent
  width grows linearly — so a reader who checks the width law against the secant column of Table 2
  will not see it hold, and that is not a contradiction: the law is the tangent statement and Table 2
  is the secant table. Each registered tolerance is read on the object the stage recorded for that
  row, and Section 6.2 prints both definitions beside the numbers they produce.

### 3.4 The ceiling

A second family of operating points saturates: the constant rule already rejects with high
probability, so a better-calibrated rule cannot buy much power, and we measure that bound
directly. Section 7.2 reports both the measurement and the fact that the boundary was declared
before it was measured: the intervals in those cells still exclude zero, so the ceiling's cost
is that the *prize* becomes a fraction of a percentage point.

### 3.5 The two rules, and the node's best response

We compare two threshold rules under the same false-positive budget:

* **Constant rule**: the maximum of `n_cal` honest sample means. This is the best constant
  threshold with zero honest rejections, and by order-statistic symmetry its expected
  false-positive rate on fresh honest data is exactly `1 / (n_cal + 1)`.
* **Derived rule**: `c* * sigma_h / sqrt(k)` with `c* = Phi^-1(1 - 1/(n_cal + 1))`, the
  construct's threshold evaluated at the *same* false-positive budget.

Matching the two rules on their measured false-positive rate is what makes the comparison
meaningful; Section 6.3 reports that match as a check, not as an assumption.

Against a best-responding node — one that picks the divergence in its admissible set that
minimises its own detection probability — the optimum is the location-preserving element:
averaging kills dispersion, not mean, so the node can hold `u` at or below the boundary at
every budget. That is prior P3, and Section 6.4 reports it as a property of the admissible set
rather than as an assumption about node behaviour.

### 3.6 What the verifier must observe for the rule to apply

The derived rule takes the node's location shift `delta_D` and dispersion `sigma_D` as inputs, and
this is the sharpest limitation of the decision argument, so it is stated where the rule is derived
rather than left to the threats section.

* **Scoped claim.** Where the rule is applied quantitatively — the band, the ceiling and the
  decidability map — the claim is scoped to a verifier that can estimate or bound the two inputs.
  Section 1's decision argument and the operational summary of Section 9 apply to that verifier.
* **One consequence needs no estimate at all.** P3 is a statement about the admissible set, not
  about an estimate: a location-preserving divergence is detected at the false-positive rate
  whatever the verifier believes `delta_D` and `sigma_D` to be. Against such a node, "spend no more
  on `k`" is correct without any knowledge of the node's moments.
* **Two routes to the inputs, stated and not evaluated.** (i) *Calibration with a perturbation arm*:
  if the verifier can vary a known input, or hold an honest reference implementation, the induced
  shift in the metric identifies `delta_D` and its scatter identifies `sigma_D` — the same estimand
  the calibration cell of Section 6.1 inverts from published rates. (ii) *Detection-theoretic
  bounding*: when the node reports nothing, `u` can be bounded rather than estimated by treating the
  node's spread as adversarially large, which yields a conservative band; the boundary moves, the
  structure does not. Both are routes rather than results — measuring either is a separate study,
  and we say so rather than claiming a verifier we have not shown to exist.

---
## 4. Pre-registration

The study question, the priors and the success criteria were registered before any deciding run,
and this manuscript reports each of them as it was written.

**Study question.** Given a verifier who may re-execute a nondeterministic pipeline `k` times and
compare a policy-pinned metric against a threshold, what does an extra re-execution buy, and
where does it buy nothing?

**Registered priors.**

* **P1** — against a *location-preserving* divergence, detection is bounded away from `1` by a
  constant that no budget improves; the insensitivity region is non-empty. *Justification*:
  averaging kills dispersion, not mean, so a node whose mean is unchanged by divergence
  converges to the honest distribution.
* **P2** — against a *location-shifting* divergence with margin `delta`, detection improves with
  budget only inside a transition band around `delta = threshold`, whose width shrinks like the
  honest spread over `sqrt(k)`. *Justification*: the standardised margin governs the tail
  probability.
* **P3** — against a *best-responding* node, the marginal value of one more re-execution at the
  verifier's optimum tends to zero. *Justification*: the node selects the location-preserving
  element of its admissible set, and no averaging separates alternatives that agree in the mean.

**Registered success criteria.** (a) held-out prediction of the detection rate across crossed
cells, with median absolute error at most `10%`; (b) the insensitivity region,
defined as a detection-rate slope in `log k` below `0.01`, is non-empty and
its measured boundary matches the predicted band width within `20%`; (c) the
derived threshold rule compared against the best constant threshold matched to zero honest
rejections, reported as a factor with confidence intervals — *unmet with reason* if it is not
better; (d) at least three disjoint streams per cell, with mean and standard deviation, and
disjoint intervals for the key contrasts. Criteria (b) and (c) were to be reported *unmet with
the reason* if P2 or P3 were contradicted, and no post-hoc metric substitution could earn that
credit.

**Reverse-gap search.** Over the full arXiv index, with the search form, the window and the
measured counts recorded in the committed `search_form.json`, the six terms listed there return
respectively `1`, `1`, `1`, `0`,
`0` and `0` results at a scan date of `2026-09-14`, the
non-zero ones being the antecedent itself. We state the narrowed claim — *no paper over the
window named maps verification power as a function of a re-execution budget against a node that
chooses its divergence* — and not the claim that no such paper exists. Crossref is recorded as
`stated as unavailable for this absence claim` for this absence claim, because its bibliographic query returns
relevance-ranked totals rather than set sizes for multi-term queries. The structural reason prior
work skipped the question is stated separately from the search: the protocol that poses it is days
old at the scan date, so the natural next step looked like engineering rather than a law.

---

## 5. Instrument

The instrument is five stages, each deciding one thing, run in the order the claims require
(the later stages read earlier stages' artefacts, so the order is load-bearing and the runner
asserts it).

| Stage | Decides | Grid | Monte-Carlo budget | Streams |
|---|---|---|---|---|
| `v0` | controls only; no claim is made from it | `4` control families | `8000` draws | `3` |
| `v1` | criterion (a) and the calibration cell | `31` crossed cells | `15000` draws | `5` |
| `v2` | criterion (b): the band | `81`-point margin sweep at `3` spreads | `8000` draws | `5` |
| `v3` | criterion (c): the two rules | `48` cells | `12000` draws | `41` |
| `v4` | sensitivity: the construct's boundaries | `108` ceiling cells, `36` lattice cells | `12000` draws | `41` |

**Ground truth by construction, and how the paper should be read.** Every stage computes the
construct's closed-form prediction alongside its Monte-Carlo estimate, and stage `v0` establishes
that the two agree before any claim is made. This shapes the reading of everything that follows:
the measurement and the prediction are not two independent estimates of an unknown quantity — the
family is specified, so the construct is exact up to sampling noise. What is tested is whether the
construct's functional form survives the places where its assumptions are thinnest: heavy tails,
lattice-valued nodes, saturation. Section 6.2 and Section 7 measure exactly those, and the
calibration cell of Section 6.1 is the one place where the comparison is to *published* numbers
rather than to a specified family.

**A mean statistic and a variance statistic.** The detector family includes the variance as a
control. Against a dispersion-only divergence the mean statistic is flat in the budget while the
variance statistic grows: measured, the mean statistic's movement across the budget range is at
most `0.0006`, while the variance statistic moves from
`0.6657` to `1.0000`. This is the instrument's internal
evidence for P1's mechanism, and it is a control rather than a claim: it shows the insensitivity
belongs to the statistic, not to the sampler.

**Anti-degeneracy.** A detector that separates everything and one that separates nothing are both
useless, so the stages carry direction controls in both directions: a threshold placed *worse* than
the constant rule must produce a factor below parity, and one placed better but at an unmatched
false-positive budget must produce a factor above parity. The second direction is the one that
catches a rule that "wins" merely by rejecting more.

**Determinism.** No stage reads a clock, an environment variable or an absolute path, and no
artefact carries a time field. The artefacts are byte-identical across runs and across working
directories (Section 10).

---

## 6. Results

**Table 1.** The four registered criteria and their recomputed outcomes. Every outcome is produced
by `canonical_runner.py` from the stage artefacts' primitives and cross-checked against the flag the
stage recorded about itself.

| | Registered criterion | Outcome | The measured value |
|---|---|---|---|
| (a) | held-out prediction: median absolute error at most `10%` | **MET** | median `0.00092` over `31` cells |
| (b) | insensitivity region non-empty with boundary within `20%` of the predicted band width | **MET** | worst refined width error `0.86%` |
| (c) | derived rule better than the best constant threshold, as a factor with intervals | **MET** | `41` of `42` cells, `p = 9.8e-12` |
| (d) | at least three disjoint streams per cell, with intervals on the key contrasts | **MET** | `41` streams in the deciding stages |

### 6.1 Criterion (a): the construct predicts held-out cells

<div align="center">

![Figure 1](figures/fig1_prediction.png)

**Figure 1.** Criterion (a). Panel (a): predicted against measured detection power over the
`31` crossed cells, with each measurement's own standard deviation as the error
bar; the diagonal is perfect prediction. Panel (b): the invariance groups — one value of `u` reached
through different combinations of budget, margin, spread and mechanism, with the construct's value
at that `u` marked.

</div>

Over `31` out-of-sample cells the median absolute prediction error is
`0.00092`, the mean is `0.0036` and the maximum is
`0.0449` — against a registered limit of `10%`;
`28` of the `31` cells land within one percentage
point. No parameter is fitted anywhere: the construct's only inputs are the node's mean and standard
deviation, both specified by construction.

**Invariance.** In `10` groups the same value of `u` arises from
different decompositions into budget, margin, spread and mechanism. The maximum spread within a group
is `0.0472`, consistent with the per-cell sampling noise of
`5` streams. This is the empirical content of the one-coordinate
claim: detectability tracks `u`, not the route to `u`.

**Where the construct is blind, honestly.** For nodes whose moments match a Gaussian node's but whose
tails do not — affine contamination at small budgets — the construct's error reaches
`0.0449` over
`4` such cells. That figure is not sampling noise: raising
the draws per cell several-fold left it unchanged. It is a characterised limit, and Section 7.1
measures what actually governs it — a lattice ratio, not the budget.

**The calibration cell.** The antecedent reports `44/45` honest acceptances, `104/105` divergent
rejections, and `27/29` same-input fabrications passing at `k = 5`.
Inverting those rates: the honest level is `0.0222`, hence
`c_alpha = 2.0099`; the divergent pairs imply a standardised
margin of `2.3446`, i.e. a separation of
`1.9474` standard deviations, and the construct predicts their
measured rejection rate `0.9905` to within the resolution of
a `104/105` sample. The same-input fabrication cell is the informative one: its observed detection
rate is `0.0690`, while the construct predicts
`0.0000`, because a location-preserving,
dispersion-collapsed node is undetectable at any budget. The residual is
`0.0690`, and it is exactly the false-positive floor
at that level — not evidence of a margin the construct missed. This is the one place where the study
touches published numbers, and it is reported as a residual-with-explanation rather than as a
successful prediction.

### 6.2 Criterion (b): the band, and the width law

<div align="center">

![Figure 2](figures/fig2_band.png)

**Figure 2.** Criterion (b). Panel (a): the predicted band (light) and the measured band (coloured)
at each honest spread, with the measured band's endpoints marked; the annotation gives the width's
relative error on the coarse grid and after bisection. Panel (b): the width law —
`width * sqrt(k) / sigma` against the budget, one line per spread, flat to machine precision.

</div>

| Spread `sigma` | Predicted width | Measured width | Relative error | Bisected relative error |
|---|---|---|---|---|
| `0.5` | `0.8535` | `0.8630` | `1.11%` | `-0.44%` |
| `1.0` | `1.1774` | `1.1838` | `0.54%` | `-0.13%` |
| `2.0` | `1.7962` | `1.7977` | `0.08%` | `-0.86%` |

**Table 2.** The **secant** band's width at each honest spread — the second definition of
Section 3.3, not the tangent one. The width is the predicted power difference over the design's own
budget range, `(power(k_max, delta, sigma) - power(k_min, delta, sigma)) / log(k_max / k_min)` with
the design budget set
`K_BAND = { 8, 32, 128, 512 }`, so the "Predicted width" column is recomputable by a reader who
evaluates `Phi(u)` of Section 3.2 at the two endpoints of `K_BAND` and divides by the log span.
**Measured width** is the same object measured on the `81`-point margin grid, and
the last column bisects on that measured secant. The widths grow **sublinearly in `sigma`** because
they are secants; the width law stated below is the tangent statement at fixed `k`, and the two are
not interchangeable. The worst refined error is `0.86%` against
the `20%` limit — a margin of `23` times.

Two further readings, both reported because the registered wording admits both. The stricter
**edge-position** reading — does the *edge* land within tolerance, rather than the width — reaches
`22.41%` on the coarse grid, which would fail, but that is the
instrument's grid resolution and not the theory: the low edge sits at a small fraction of the band
width, so a `81`-point sweep localises it poorly. Bisecting on the measured
secant brings it to `6.28%`, and both localisations of the same
quantity are reported. Separately, the insensitivity region is non-empty:
the detection rate's slope in `log k` at zero margin is
`-0.00010` against the `0.01` cut, and the stage's
zero-margin insensitivity flag is `True`.

**The width law, and which band it is about.** This paragraph is about the **tangent** band at
fixed `k` (the first definition of Section 3.3) — not about the secant column of Table 2, whose
width is an average over the budget range and therefore does not satisfy the invariant below. At
fixed spread and fixed `k`, `width * sqrt(k) / sigma` is constant across
`k = 8`, `32`, `128` and
`512` to within `0.0e+00` at every spread tested.
This is the quantitative form of P2, and it is what makes the band an engineering object: a verifier
who wants to know how much margin is separable at a given budget reads it off the law instead of
measuring it.

### 6.3 Criterion (c): the derived rule against the best constant threshold

<div align="center">

![Figure 3](figures/fig3_rule.png)

**Figure 3.** Criterion (c). Panel (a): every informative cell's factor — the derived rule's mean
power divided by the constant rule's — with its `95%` interval, ordered by the factor; the dashed
line is parity. Panel (b): the factor against the standardised margin, one line per calibration
budget.

</div>

The comparison is matched on the false-positive budget: the constant rule's expected false-positive
rate is `1/(n_cal+1)`, and the derived rule's threshold is the construct's value at the same rate. The
match is checked rather than assumed — across the cells the two rules' measured false-positive rates
agree within the instrument's tolerance (`z_tol = 4`) over `96` checks,
with a maximum standardised deviation of `3.2360`.

**Result: the derived rule is better** (Table 3 breaks the same cells down by margin and by
calibration budget). In `41` of
`42` informative cells the factor is above parity;
`26` cells are significantly better and
`0` significantly worse; the one-sided sign test gives
`p = 9.8e-12`. The factor's median is `1.0897`,
ranging from `0.8381` to `1.5454`.

| Margin `lambda` | Cells | Median factor | Best | Worst | Significantly better |
|---|---|---|---|---|---|
| `1` | `12` | `1.1047` | `1.5454` | `0.8381` | `3` |
| `2` | `12` | `1.1744` | `1.2825` | `1.0514` | `9` |
| `3` | `12` | `1.0774` | `1.1389` | `1.0259` | `10` |
| `4` | `6` | `1.0408` | `1.0721` | `1.0265` | `4` |

**Table 3.** The factor by margin, the margin expressed in standard-error units as
`lambda = delta * sqrt(k) / sigma_h`. The advantage peaks near `lambda = 2` and is weakest at the
extremes — at small margins the constant rule is itself highly variable, and at large margins the
difference falls below the design's resolution. Margin is the descriptive variable here, not a
predicted ordering.

| Calibration set `n_cal` | Cells | Median factor | Significantly better |
|---|---|---|---|
| `5` | `9` | `1.0899` | `7` |
| `20` | `9` | `1.0761` | `7` |
| `100` | `12` | `1.0841` | `7` |
| `1000` | `12` | `1.0937` | `5` |

The advantage does **not** vanish as the calibration set grows: it is still present at
`n_cal = 1000`. The reason is that the maximum of `n_cal` honest means
is a systematically conservative estimator of the quantile it stands for, so the constant rule pays a
fixed penalty at every calibration size — not a small-sample artefact.

#### 6.3.1 A mechanism of ours, refuted and then corrected

We first stated the mechanism as "the standardised threshold gap orders the factor", and the
instrument's first version of that test reported it refuted. Both halves of that result were defects
in our own code, found by recomputing the statistic from the committed artefact: the pairs had been
taken in the order the cells happened to be built, so the count was not reproducible from the
artefact at all, and the verdict rule was inverted — it counted a pair as evidence *for* the ordering
when the factor **fell** as the gap rose, then declared the claim refuted when that fraction was
small. The corrected, order-free statistic: of `554` comparable
pairs, `510` have the factor rising with the gap and
`44` falling, a tau-like statistic of
`0.8412`. **The mean gap does order the factor.** What it does not do is
determine its magnitude: inside one gap quartile the factor still spreads by
`0.4610`, so the ordering is descriptive rather than predictive.
That is the Jensen statement — power is a nonlinear function of the threshold, so the loss is carried
by the whole distribution of the constant rule's threshold, not by its mean — and it is what the
construct's distributional prediction is scored against: the constant rule's measured power matches
`E[Phi((delta - tau_c)/se)]` in all but `1` of the
`48` cells, the single miss being a ceiling-saturated cell that the informative-set rule already
excludes. We report the refutation and the correction together, because the first version of the block
is part of what a reader is entitled to know.

### 6.4 The registered priors, and whether the data confirmed them

**Table 4.** Registered priors, their status, and the recomputed evidence behind each status.

| Prior | Registered statement | Status | Evidence |
|---|---|---|---|
| P1 | a location-preserving divergence is bounded away from `1` by a constant no budget improves | **CONFIRMED** | the null node matches the construct in `12` cells, worst absolute error `0.0020`; the mean statistic moves at most `0.0006` across the budget range while the variance statistic moves `0.6657` to `1.0000` |
| P2 | detection improves only inside a band whose width shrinks like the spread over `sqrt(k)` | **CONFIRMED** | `width * sqrt(k) / sigma` constant to `0.0e+00` at every spread (Table 2) |
| P3 | against a best-responding node the marginal value of a re-execution tends to zero | **CONFIRMED** | the node's best response is the location-preserving one at all `3` budgets tested, with detection probability `0.0000` |

P1 and P2 behaved as registered. P3 is the one worth a sentence: the instrument does not assume the
node's best response, it enumerates the admissible set and selects the minimum, and the minimum is the
location-preserving node at every budget — so the marginal value of a re-execution is zero *because
the node moves*, not because the verifier's test is weak. The practical consequence is the one in
Section 1: against such a node, an argument for more re-executions cannot succeed, and the budget
belongs to metric recalibration instead.

---
## 7. Sensitivity: the construct's own boundaries, measured

The registered criteria ask whether the construct works where it is supposed to. This section asks
the complementary question — where it stops — and reports three measured boundaries rather than three
caveats. All three are computed by the same runner from the same stage artefacts, and each is scored
by a named check so that a reader can see which claim would break first.

### 7.1 S1: the construct's limit is a lattice ratio, not a rate of convergence

<div align="center">

![Figure 4](figures/fig4_lattice.png)

**Figure 4.** S1. Panel (a): the absolute error against the lattice ratio `big / (sigma * sqrt(k))`,
one line per node spread, with the usable boundary marked and the Gaussian control (which has lattice
ratio zero) as stars. Panel (b): the same error against the budget — the error changes sign as the
budget grows, so it is not monotone in `k`. That non-monotonicity belongs to the **approximation
error**, not to the power: power is monotone in `k` for a fixed node (Section 3.2), and it is the
rule comparison that is non-monotone in the budget (Section 1).

</div>

For a two-point node with mass `q` at `big` and the rest at zero, the sample mean is a lattice
variable with spacing `big/k`, so the quantity that governs the construct's error is the *lattice
ratio* `big / (sigma * sqrt(k))` — not the budget alone (`sigma` here is the node's own standard
deviation, which is what makes the ratio the only scale-free input). Over `36`
node-by-budget cells the error is ordered by that ratio (Table 5): every cell with ratio at most
`0.25` lands within `1%` of the construct
(`11` cells, worst `0.00172`), while the
worst error over all measured cells is `0.3250`. We report both the tight
safe value and the largest ratio at which a cell still exceeds tolerance,
`5.05`, because a boundary without its counterexample invites
over-reading.

| Lattice-ratio bin | Median absolute error | Worst absolute error |
|---|---|---|
| `0-0.25` | `0.00000` | `0.0007` |
| `0.25-0.5` | `0.00523` | `0.0714` |
| `0.5-1` | `0.03170` | `0.1642` |
| `1-2` | `0.05737` | `0.2349` |
| `2-100` | `0.30689` | `0.3250` |

**Table 5.** Absolute error by lattice-ratio bin. The first bin is numerically zero; at the other
end the worst error is `0.3250` against a tolerance of `1%`.
`0.25`, not where the budget passes some threshold.

**The Gaussian control.** A Gaussian node has lattice ratio zero, and its worst error over the same
grid is `0.0013` — `241` times tighter than the
worst lattice error. This is the two-sided control for Section 7.1: it shows the error is a property
of the lattice, not of the sample size or of an implementation detail.

**Where the budget still misleads.** Because the ratio carries `sqrt(k)`, a node's error is *not*
monotone in the budget: the measured number of sign changes in the error as `k` grows is
`3`, `1`,
`5` and `1` across the
four node spreads (exact zeros excluded; the stage's own counting rule, which admits ties, gives
`4`, `2`,
`5`, `1` — both are printed
because they answer different questions, and the discrepancy is entirely tie-handling). The mirror
control confirms the sign flips symmetrically under reflection of the node's support:
`True`.

### 7.2 S2: the ceiling bounds the prize, not the detection

<div align="center">

![Figure 5](figures/fig5_ceiling.png)

**Figure 5.** S2. Panel (a): the measured gain against the bound `1 - p_c` at each measured cell, one
marker per cell, with saturation flagged; the diagonal is the bound. Panel (b): the gain against the
standardised margin, showing the saturation boundary crossing the grid.

</div>

Of the `108` ceiling cells, `18` saturate (Table 6 lists the
measured cells; the grid itself is a plotting grid in Figure 5). The maximum gain in the
saturated group is `0.00098` against `0.9148` in the
unsaturated group — a factor of `930` between the two regimes, and it is the *difference*
between the two rules that shrinks, not their detectability. The bound `1 - p_c` is never violated:
the largest overshoot over the measured cells is `-8.1e-06`, i.e. the measured gain
lies below the bound at every cell. Of the `8` measured cells,
`4` have an interval that excludes zero, so the saturation claim
is not a significance claim: in a saturated cell the prediction is that the gain is *small*, and the
interval is wide enough that the honest statement is "consistent with the bound", not "significantly
below parity".

| `n_cal` | `k` | `lambda` | Bound `1 - p_c` | Measured gain | `95%` interval |
|---|---|---|---|---|---|
| `20` | `16` | `1` | `0.7770` | `0.0288` | `[-0.0142, 0.0718]` |
| `20` | `16` | `2` | `0.4174` | `0.0482` | `[-0.0050, 0.1014]` |
| `20` | `16` | `4` | `0.0239` | `0.0142` | `[0.0066, 0.0217]` |
| `20` | `16` | `6` | `0.0002` | `0.0002` | `[0.0000, 0.0004]` |
| `100` | `4` | `1` | `0.9148` | `0.0057` | `[-0.0138, 0.0253]` |
| `100` | `4` | `2` | `0.6344` | `0.0055` | `[-0.0379, 0.0489]` |
| `100` | `4` | `4` | `0.0968` | `0.0497` | `[0.0217, 0.0777]` |
| `100` | `4` | `6` | `0.0010` | `0.0009` | `[0.0003, 0.0014]` |

**Table 6.** The measured ceiling cells: the bound from the constant rule's own power, the measured
gain, and the between-stream interval. The cells with the tightest bounds are exactly the saturated
ones, and their intervals contain zero — which is the honest reading of "the prize is gone".

### 7.3 S3: the comparison is decidable for a minority of cells at this budget

<div align="center">

![Figure 6](figures/fig6_decidability.png)

**Figure 6.** S3. Panel (a): per-cell `N_min` — the streams a cell needs for its interval to clear
parity — against the measured effect size, with the budget this study ran drawn as a horizontal line.
Panel (b): decidability by margin and calibration budget, the informative cells marked.

</div>

The headline comparison of Section 6.3 is a *between-stream* comparison, so each cell has a streams
requirement of its own. Inverting the cell intervals: `25` of
`42` informative cells certify an advantage at the `41` streams
this study ran, `17` do not, and `1` cell
(`n1000_k4_l1`) would need more streams than any budget in the design grid can
supply, because its effect size is below the noise floor at every budget tested. Among the decidable
and indecidable cells together, the median requirement is `30` streams, with a
range from `11` to `1854`.

This is where the paper's headline should be read with care, and we state it as a limitation of our
own evidence rather than of the construct: the *sign* of the comparison is settled —
`41` of `42` cells favour the derived
rule, sign test `p = 9.8e-12` — but at `41` streams
only `25` of the `42` cells are individually certified, and
`17` cells fail the strict reading that requires each cell's own
interval to clear parity. A verifier who needs per-cell certification must budget
`30` streams (median), not `41`; a verifier who needs the
direction of the effect can stop earlier. The agreement between this inversion and the stage's own
cell-by-cell verdict is `41` of `42` cells.

---

## 8. Threats to validity, and why the result is still worth publishing

**Threat 1: the family is synthetic.** Detection is measured on a specified node family with ground
truth by construction, not on deployed pipelines. *Mitigation and residual*: the construct's inputs
are the node's first two moments, and the study's job is to test the functional form; the one
external check is the calibration cell of Section 6.1, which is an inversion of published rates and
lands within one sample's resolution. The residual is that a real fabrication mechanism with a
non-Gaussian, heavier-tailed profile at small budgets behaves like the contaminated cells of
Section 6.1 — error `0.0449` — until the lattice ratio
explains it (Section 7.1). A field deployment could shift the *constants* in the band; it cannot
remove the band, because the band comes from the standard error, not from the family.

**Threat 2: the budget grids are finite.** `k` is measured at
`8`–`512` in the band experiment and
`4`–`64` in the rule comparison, so the
`1/sqrt(k)` law is established over a finite range. *Mitigation*: the law's invariant is flat to
`0.0e+00`, and the analytic form predicts the extrapolation; the honest
statement is that the law is verified where it was measured, and that extrapolation beyond
`k = 512` is an inference from the derivation rather than a measurement.

**Threat 3: our own first mechanism claim was wrong.** Section 6.3.1 reports a mechanism statement
that began as "the gap orders the factor", was refuted by our own instrument, and was corrected after
the error in the *test* was found. *Why this is not fatal, and why it is reported*: the corrected
statistic is reproducible from the committed artefact (order-free), and the claim that survives is
weaker and checkable — the gap orders the factor, the gap does not determine it. A reader can
re-derive both numbers from `results_v3.json` without re-running the study.

**Threat 4: single-machine, single-precision, single-seed-family.** The study is CPU-only, run on one
machine, with streams derived from a fixed seed policy. *Mitigation*: the artefacts carry no clock,
no host name and no absolute path, and `reproduce.sh` regenerates all six figures and every number
byte-identically from a clean checkout; the multi-stream structure (41 streams in the deciding
stages) is the study's own variance control, and the reported intervals are between-stream.
*Residual*: a different BLAS or libm could move the last digits; the checks are therefore stated at
the precision the manuscript prints, not at bit level, and the byte-identity claim is scoped to the
Python and matplotlib versions recorded in the README.

**Threat 5: the comparison's per-cell decidability is limited at this budget.** As Section 7.3 states,
`25` of `42` cells are individually certified at
`41` streams and the median requirement is `30`.
*Mitigation*: the direction of the effect is settled by the sign test and the magnitude is bounded by
the per-cell factors; the strict per-cell reading is reported with its failure count so a reader can
choose which claim to rely on.

**Why it is still worth publishing.** The decision the paper informs is a budget decision, and the
decision rule it produces is cheap to apply: read the node's mean shift and dispersion, compute `u`,
and compare it against the band. Three of the four consequences are invisible to a one-point
comparison — a budget response confined to a band, a rule comparison that is non-monotone in the
budget, a ceiling that bounds the prize, and a location-preserving
node that no budget can separate. The last one is not a curiosity: it is the case the antecedent's
conditional result described, it is the best response of a strategic node, and it is the reason "more
re-executions" cannot be the answer to a disagreement with a fabricating counterparty. Even where our
evidence is weakest — per-cell decidability at the budget we ran — the paper's contribution is the map
of *where* the evidence is weak, which is what lets the next study spend its budget in the right
cells.

---

## 9. Conclusion

We asked what a re-execution budget buys. The answer is a curve with a boundary, not a number:
detection power is a function of one standardised coordinate, `u = (sqrt(k) delta_D - c_alpha) /
sigma_D`, so budget buys power only for nodes inside a transition band whose width shrinks as
`1/sqrt(k)` (measured flat to `0.0e+00`), the achievable gain inside a
saturated regime collapses to `0.00098` from
`0.9148`, and a location-preserving node is separated by no budget at all.
The derived rule beats the best matched constant threshold in
`41` of `42` informative cells
(`p = 9.8e-12`), and the construct's own limit is a lattice ratio
(`0.25`) rather than a convergence rate. The operational summary a verifier can carry
away: measure the node's location shift and dispersion, compute `u`, and spend the next unit of budget
where the band is — or stop, and recalibrate the metric, when the node is the one that moves.

## 10. Reproduction

`bash reproduce.sh` regenerates every number and every figure in this manuscript from a clean
checkout, in one command, with no network access.

* **Numbers.** The five stage scripts are re-run, then `canonical_runner.py` recomputes the criteria,
  the sensitivity block and the `manuscript_facts` block from the stage artefacts' primitives and
  cross-checks each recomputation against the flag the stage recorded about itself:
  `8000`+ draws per cell as listed in Table 1,
  `85` cross-checks, 0 failures. The run prints `REPRODUCE: ALL GREEN` and exits non-zero on any mismatch, so a
  logging accident cannot outrank the verdict.
* **Expected output.** `canonical_results.json`; criteria `a`, `b`, `c`, `d` all `MET`; the
  three registered priors all `CONFIRMED`. The run prints the artefact's `sha256` and compares
  two consecutive runs against each other, so neither this manuscript nor the README has to
  quote a digest that a run could retire.
  `a`,`b`,`c`,`d` all `MET`; the four registered priors all `CONFIRMED`.
* **Figures.** `make_figures.py` draws all six figures from the stage artefacts (no number is typed
  into the plotting code), and `verify_figures.py` re-checks them by content (digests re-read off the
  drawn artists), render (every promised label is drawn) and canvas (every positioned element inside
  the axes). `verify_figures_mutations.py` demonstrates that each of those checks fires on a mutated
  input.
* **Tolerance.** Integers and counts are exact; printed decimal numbers are compared at the precision
  the manuscript prints; PNG bytes are pinned to the matplotlib version recorded in the README, and
  the data they are drawn from is pinned absolutely. If matplotlib is absent, the figure steps are
  skipped with a notice; `REQUIRE_FIGURES=1` makes that fatal.
* **What is not reproduced.** The reverse-gap search of Section 4 is hand-recorded evidence in
  `search_form.json` (arXiv is rate-limited and its totals are not stable enough to assert in a
  loop); the reference checks of the bibliography are recorded in `reference-check.md` with the
  method used for each entry.

---

## References

[1] Ardebili, M. S.. *NovaFabric: Tamper-Evident, Replayable Evidence for Autonomous AI Agent Runs*. arXiv preprint, 2026. `arXiv:2609.12582`
[2] Alimoglu, A.. *Threshold Choice, Not Sample Size, Bounds Trustless Verification of Nondeterministic Compound AI Workflows*. arXiv preprint, 2026. `arXiv:2609.10601`
[3] Cohen, J.. *A power primer*. Psychological Bulletin, 1992. `10.1037/0033-2909.112.1.155`
[4] Wald, A.. *Sequential Tests of Statistical Hypotheses*. The Annals of Mathematical Statistics, 1945. `10.1214/aoms/1177731118`
[5] Pocock, S. J.. *Group sequential methods in the design and analysis of clinical trials*. Biometrika, 1977. `10.1093/biomet/64.2.191`
[6] Bretz, F.; Koenig, F.; Brannath, W.; et al.. *Adaptive designs for confirmatory clinical trials*. Statistics in Medicine, 2009. `10.1002/sim.3538`
[7] Bahadur, R. R.; Savage, L. J.. *The Nonexistence of Certain Statistical Procedures in Nonparametric Problems*. The Annals of Mathematical Statistics, 1956. `10.1214/aoms/1177728077`
[8] Ingster, Y. I.; Suslina, I. A.. *Nonparametric Goodness-of-Fit Testing Under Gaussian Models*. Lecture Notes in Statistics, 2003. `10.1007/978-0-387-21580-8`
[9] Wang, W.; An, B.; Jiang, Y.. *Optimal Spot-Checking for Improving the Evaluation Quality of Crowdsourcing: Application to Peer Grading Systems*. IEEE Transactions on Computational Social Systems, 2020. `10.1109/tcss.2020.2998732`
[10] Graydon, P. J.; Holloway, C. M.. *An investigation of proposed techniques for quantifying confidence in assurance arguments*. Safety Science, 2017. `10.1016/j.ssci.2016.09.014`
[11] Legay, A.; Delahaye, B.; Bensalem, S.. *Statistical Model Checking: An Overview*. Lecture Notes in Computer Science, 2010. `10.1007/978-3-642-16612-9_11`
[12] Howard, R.. *Information Value Theory*. IEEE Transactions on Systems Science and Cybernetics, 1966. `10.1109/tssc.1966.300074`
[13] Ott, S.; Barbosa-Silva, A.; Blagec, K.; et al.. *Mapping global dynamics of benchmark creation and saturation in artificial intelligence*. Nature Communications, 2022. `10.1038/s41467-022-34591-0`
[14] Agarwal, S.; Iyer, A. P.; Panda, A.; et al.. *Blink and it's done: interactive queries on very large data*. Proceedings of the VLDB Endowment, 2012. `10.14778/2367502.2367533`
[15] McKeen, F.; Alexandrovich, I.; Berenzon, A.; et al.. *Innovative instructions and software model for isolated execution*. Proceedings of the 2nd International Workshop on Hardware and Architectural Support for Security and Privacy, 2013. `10.1145/2487726.2488368`
[16] McCune, J. M.; Parno, B. J.; Perrig, A.; et al.. *Flicker: an execution infrastructure for tcb minimization*. ACM SIGOPS Operating Systems Review, 2008. `10.1145/1357010.1352625`
[17] Cheng, R.; Zhang, F.; Kos, J.; et al.. *Ekiden: A Platform for Confidentiality-Preserving, Trustworthy, and Performant Smart Contracts*. 2019 IEEE European Symposium on Security and Privacy (EuroS&P), 2019. `10.1109/eurosp.2019.00023`
[18] Athalye, A.; Belay, A.; Kaashoek, M. F.; et al.. *Notary: a device for secure transaction approval*. Proceedings of the 27th ACM Symposium on Operating Systems Principles, 2019. `10.1145/3341301.3359661`
[19] Kocher, P.; Horn, J.; Fogh, A.; et al.. *Spectre Attacks: Exploiting Speculative Execution*. 2019 IEEE Symposium on Security and Privacy (SP), 2019. `10.1109/sp.2019.00002`
[20] Gennaro, R.; Gentry, C.; Parno, B.. *Non-interactive Verifiable Computing: Outsourcing Computation to Untrusted Workers*. Lecture Notes in Computer Science, 2010. `10.1007/978-3-642-14623-7_25`
[21] Parno, B.; Howell, J.; Gentry, C.; et al.. *Pinocchio: Nearly Practical Verifiable Computation*. 2013 IEEE Symposium on Security and Privacy, 2013. `10.1109/sp.2013.47`
[22] Groth, J.. *On the Size of Pairing-Based Non-interactive Arguments*. Lecture Notes in Computer Science, 2016. `10.1007/978-3-662-49896-5_11`
[23] Garg, S.; Goel, A.; Jha, S.; et al.. *Experimenting with Zero-Knowledge Proofs of Training*. Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security, 2023. `10.1145/3576915.3623202`
[24] Chen, B. J.; Waiwitlikhit, S.; Stoica, I.; et al.. *ZKML: An Optimizing System for ML Inference in Zero-Knowledge Proofs*. Proceedings of the Nineteenth European Conference on Computer Systems, 2024. `10.1145/3627703.3650088`
[25] Peng, R. D.. *Reproducible Research in Computational Science*. Science, 2011. `10.1126/science.1213847`
[26] Gundersen, O. E.; Kjensmo, S.. *State of the Art: Reproducibility in Artificial Intelligence*. Proceedings of the AAAI Conference on Artificial Intelligence, 2018. `10.1609/aaai.v32i1.11503`
[27] Pineau, J.; Vincent-Lamarre, P.; Sinha, K.; et al.. *Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)*. arXiv preprint, 2020. `arXiv:2003.12206`
[28] Dodge, J.; Gururangan, S.; Card, D.; et al.. *Show Your Work: Improved Reporting of Experimental Results*. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP), 2019. `10.18653/v1/d19-1224`
[29] Cheney, J.; Chiticariu, L.; Tan, W. C.. *Provenance in Databases: Why, How, and Where*. Foundations and Trends in Databases, 2009. `10.1561/1900000006`
[30] Benjamini, Y.; Hochberg, Y.. *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*. Journal of the Royal Statistical Society Series B: Statistical Methodology, 1995. `10.1111/j.2517-6161.1995.tb02031.x`
[31] Hochberg, Y.. *A sharper Bonferroni procedure for multiple tests of significance*. Biometrika, 1988. `10.1093/biomet/75.4.800`
[32] Benjamini, Y.; Yekutieli, D.. *The control of the false discovery rate in multiple testing under dependency*. The Annals of Statistics, 2001. `10.1214/aos/1013699998`
[33] Gordon Lan, K. K.; Demets, D. L.. *Discrete sequential boundaries for clinical trials*. Biometrika, 1983. `10.1093/biomet/70.3.659`
[34] Howard, S. R.; Ramdas, A.; McAuliffe, J.; et al.. *Time-uniform Chernoff bounds via nonnegative supermartingales*. arXiv preprint, 2018. `arXiv:1808.03204`
[35] Vovk, V.; Wang, R.. *E-values: Calibration, combination and applications*. The Annals of Statistics, 2021. `10.1214/20-aos2020`
[36] Johari, R.; Koomen, P.; Pekelis, L.; et al.. *Peeking at A/B Tests: Why it matters, and what to do about it*. Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2017. `10.1145/3097983.3097992`
[37] Vapnik, V. N.; Chervonenkis, A. Y.. *On the Uniform Convergence of Relative Frequencies of Events to Their Probabilities*. Theory of Probability & Its Applications, 1971. `10.1137/1116025`
[38] Valiant, L. G.. *A theory of the learnable*. Communications of the ACM, 1984. `10.1145/1968.1972`
[39] Dvoretzky, A.; Kiefer, J.; Wolfowitz, J.. *Asymptotic Minimax Character of the Sample Distribution Function and of the Classical Multinomial Estimator*. The Annals of Mathematical Statistics, 1956. `10.1214/aoms/1177728174`
[40] Massart, P.. *The Tight Constant in the Dvoretzky-Kiefer-Wolfowitz Inequality*. The Annals of Probability, 1990. `10.1214/aop/1176990746`
[41] Massey, F. J.. *The Kolmogorov-Smirnov Test for Goodness of Fit*. Journal of the American Statistical Association, 1951. `10.1080/01621459.1951.10500769`
[42] Angelopoulos, A. N.; Bates, S.. *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*. arXiv preprint, 2021. `arXiv:2107.07511`
[43] Lei, J.; G’Sell, M.; Rinaldo, A.; et al.. *Distribution-Free Predictive Inference for Regression*. Journal of the American Statistical Association, 2018. `10.1080/01621459.2017.1307116`
[44] Vovk, V.. *Conditional validity of inductive conformal predictors*. Machine Learning, 2013. `10.1007/s10994-013-5355-6`
[45] Tsybakov, A. B.. *Introduction to Nonparametric Estimation*. Springer Series in Statistics, 2009. `10.1007/b13794`
[46] Dybå, T.; Kampenes, V. B.; Sjøberg, D. I. K.. *A systematic review of statistical power in software engineering experiments*. Information and Software Technology, 2006. `10.1016/j.infsof.2005.08.009`
[47] Dror, R.; Baumer, G.; Shlomov, S.; et al.. *The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing*. Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 2018. `10.18653/v1/p18-1128`
[48] Reimers, N.; Gurevych, I.. *Reporting Score Distributions Makes a Difference: Performance Study of LSTM-networks for Sequence Tagging*. Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing, 2017. `10.18653/v1/d17-1035`
[49] Bouthillier, X.; Delaunay, P.; Bronzi, M.; et al.. *Accounting for Variance in Machine Learning Benchmarks*. arXiv preprint, 2021. `arXiv:2103.03098`
[50] Henderson, P.; Islam, R.; Bachman, P.; et al.. *Deep Reinforcement Learning That Matters*. Proceedings of the AAAI Conference on Artificial Intelligence, 2018. `10.1609/aaai.v32i1.11694`
[51] Zheng, L.; Chiang, W. L.; Sheng, Y.; et al.. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv preprint, 2023. `arXiv:2306.05685`
[52] Wang, P.; Li, L.; Chen, L.; et al.. *Large Language Models are not Fair Evaluators*. arXiv preprint, 2023. `arXiv:2305.17926`
[53] Liang, P.; Bommasani, R.; Lee, T.; et al.. *Holistic Evaluation of Language Models*. arXiv preprint, 2022. `arXiv:2211.09110`
[54] Hendrycks, D.; Burns, C.; Basart, S.; et al.. *Measuring Massive Multitask Language Understanding*. arXiv preprint, 2020. `arXiv:2009.03300`
[55] Ouyang, L.; Wu, J.; Jiang, X.; et al.. *Training language models to follow instructions with human feedback*. arXiv preprint, 2022. `arXiv:2203.02155`
[56] Wei, J.; Wang, X.; Schuurmans, D.; et al.. *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. arXiv preprint, 2022. `arXiv:2201.11903`
[57] Kojima, T.; Gu, S. S.; Reid, M.; et al.. *Large Language Models are Zero-Shot Reasoners*. arXiv preprint, 2022. `arXiv:2205.11916`
[58] Wang, X.; Wei, J.; Schuurmans, D.; et al.. *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. arXiv preprint, 2022. `arXiv:2203.11171`
[59] Dhuliawala, S.; Komeili, M.; Xu, J.; et al.. *Chain-of-Verification Reduces Hallucination in Large Language Models*. arXiv preprint, 2023. `arXiv:2309.11495`
[60] Madaan, A.; Tandon, N.; Gupta, P.; et al.. *Self-Refine: Iterative Refinement with Self-Feedback*. arXiv preprint, 2023. `arXiv:2303.17651`
[61] Chen, M.; Tworek, J.; Jun, H.; et al.. *Evaluating Large Language Models Trained on Code*. arXiv preprint, 2021. `arXiv:2107.03374`
[62] Jimenez, C. E.; Yang, J.; Wettig, A.; et al.. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*. arXiv preprint, 2023. `arXiv:2310.06770`
[63] Liu, X.; Yu, H.; Zhang, H.; et al.. *AgentBench: Evaluating LLMs as Agents*. arXiv preprint, 2023. `arXiv:2308.03688`
[64] Mialon, G.; Fourrier, C.; Swift, C.; et al.. *GAIA: a benchmark for General AI Assistants*. arXiv preprint, 2023. `arXiv:2311.12983`
[65] D'Amour, A.; Heller, K.; Moldovan, D.; et al.. *Underspecification Presents Challenges for Credibility in Modern Machine Learning*. arXiv preprint, 2020. `arXiv:2011.03395`
[66] Singh, S.; Nan, Y.; Wang, A.; et al.. *The Leaderboard Illusion*. arXiv preprint, 2025. `arXiv:2504.20879`
[67] Deng, C.; Zhao, Y.; Tang, X.; et al.. *Investigating Data Contamination in Modern Benchmarks for Large Language Models*. arXiv preprint, 2023. `arXiv:2311.09783`
[68] Srivastava, A.; Rastogi, A.; Rao, A.; et al.. *Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models*. arXiv preprint, 2022. `arXiv:2206.04615`
[69] Ferrari Dacrema, M.; Cremonesi, P.; Jannach, D.. *Are we really making much progress? A worrying analysis of recent neural recommendation approaches*. Proceedings of the 13th ACM Conference on Recommender Systems, 2019. `10.1145/3298689.3347058`
[70] Amodei, D.; Olah, C.; Steinhardt, J.; et al.. *Concrete Problems in AI Safety*. arXiv preprint, 2016. `arXiv:1606.06565`
[71] Langosco, L.; Koch, J.; Sharkey, L.; et al.. *Goal Misgeneralization in Deep Reinforcement Learning*. arXiv preprint, 2021. `arXiv:2105.14111`
[72] Gao, L.; Schulman, J.; Hilton, J.. *Scaling Laws for Reward Model Overoptimization*. arXiv preprint, 2022. `arXiv:2210.10760`
[73] Perez, E.; Huang, S.; Song, F.; et al.. *Red Teaming Language Models with Language Models*. arXiv preprint, 2022. `arXiv:2202.03286`
[74] Goldreich, O.; Goldwasser, S.; Ron, D.. *Property testing and its connection to learning and approximation*. Journal of the ACM, 1998. `10.1145/285055.285060`
[75] Ben-Tal, A.; Nemirovski, A.. *Robust optimization – methodology and applications*. Mathematical Programming, 2002. `10.1007/s101070100286`
[76] Bartocci, E.; Falcone, Y.; Francalanza, A.; et al.. *Introduction to Runtime Verification*. Lecture Notes in Computer Science, 2018. `10.1007/978-3-319-75632-5_1`
[77] Zhang, J. M.; Harman, M.; Ma, L.; et al.. *Machine Learning Testing: Survey, Landscapes and Horizons*. arXiv preprint, 2019. `arXiv:1906.10742`
[78] Geifman, Y.; El-Yaniv, R.. *Selective Classification for Deep Neural Networks*. arXiv preprint, 2017. `arXiv:1705.08500`
[79] Hendrycks, D.; Mazeika, M.; Dietterich, T.. *Deep Anomaly Detection with Outlier Exposure*. arXiv preprint, 2018. `arXiv:1812.04606`
[80] Domingos, P.. *MetaCost: a general method for making classifiers cost-sensitive*. Proceedings of the fifth ACM SIGKDD international conference on Knowledge discovery and data mining, 1999. `10.1145/312129.312220`
[81] Hellerstein, J. M.; Haas, P. J.; Wang, H. J.. *Online aggregation*. ACM SIGMOD Record, 1997. `10.1145/253262.253291`
[82] Li, K.; Li, G.. *Approximate Query Processing: What is New and Where to Go?: A Survey on Approximate Query Processing*. Data Science and Engineering, 2018. `10.1007/s41019-018-0074-4`
[83] Auer, P.; Cesa-Bianchi, N.; Freund, Y.; et al.. *The Nonstochastic Multiarmed Bandit Problem*. SIAM Journal on Computing, 2002. `10.1137/s0097539701398375`
[84] Seung, H. S.; Opper, M.; Sompolinsky, H.. *Query by committee*. Proceedings of the fifth annual workshop on Computational learning theory, 1992. `10.1145/130385.130417`
[85] Atkinson, A. C.; Donev, A. N.; Tobias, R. D.. *Optimum Experimental Designs, with SAS*. Oxford University PressOxford, 2007. `10.1093/oso/9780199296590.001.0001`
[86] Neyman, J.; Pearson, E. S.. *IX. On the problem of the most efficient tests of statistical hypotheses*. Philosophical Transactions of the Royal Society of London. Series A, Containing Papers of a Mathematical or Physical Character, 1933. `10.1098/rsta.1933.0009`
[87] Fisher, R. A.. *On the mathematical foundations of theoretical statistics*. Philosophical Transactions of the Royal Society of London. Series A, Containing Papers of a Mathematical or Physical Character, 1922. `10.1098/rsta.1922.0009`
[88] Student. *The Probable Error of a Mean*. Biometrika, 1908. `10.2307/2331554`
[89] Wilson, E. B.. *Probable Inference, the Law of Succession, and Statistical Inference*. Journal of the American Statistical Association, 1927. `10.1080/01621459.1927.10502953`
[90] Clopper, C. J.; Pearson, E. S.. *The Use of Confidence Or Fiducial Limits Illustrated in the Case of the Binomial*. Biometrika, 1934. `10.1093/biomet/26.4.404`
[91] Hyndman, R. J.; Fan, Y.. *Sample Quantiles in Statistical Packages*. The American Statistician, 1996. `10.1080/00031305.1996.10473566`
[92] Vaart, A. W. v. d.. *Asymptotic Statistics*. Cambridge University Press, 1998. `10.1017/cbo9780511802256`
[93] de Haan, L.; Ferreira, A.. *Extreme Value Theory: An Introduction*. Springer Series in Operations Research and Financial Engineering, 2006. `10.1007/0-387-34471-3`
[94] Efron, B.; Tibshirani, R. J.. *An Introduction to the Bootstrap*. Springer US, 1993. `10.1007/978-1-4899-4541-9`
[95] Good, P.. *Permutation, Parametric and Bootstrap Tests of Hypotheses*. Springer Series in Statistics, 2005. `10.1007/b138696`
[96] Flegal, J. M.; Jones, G. L.. *Implementing MCMC: Estimating with Confidence*. Handbook of Markov Chain Monte Carlo, 2011. `10.1201/b10905-8`
[97] Greenland, S.; Senn, S. J.; Rothman, K. J.; et al.. *Statistical tests, P values, confidence intervals, and power: a guide to misinterpretations*. European Journal of Epidemiology, 2016. `10.1007/s10654-016-0149-3`
[98] Cohen, J.. *Statistical Power Analysis for the Behavioral Sciences*. Routledge, 2013. `10.4324/9780203771587`
[99] Schuirmann, D. J.. *A comparison of the Two One-Sided Tests Procedure and the Power Approach for assessing the equivalence of average bioavailability*. Journal of Pharmacokinetics and Biopharmaceutics, 1987. `10.1007/bf01068419`
[100] Hanley, J. A.; McNeil, B. J.. *The meaning and use of the area under a receiver operating characteristic (ROC) curve*. Radiology, 1982. `10.1148/radiology.143.1.7063747`
[101] Lamport, L.; Shostak, R.; Pease, M.. *The Byzantine Generals Problem*. ACM Transactions on Programming Languages and Systems, 1982. `10.1145/357172.357176`
[102] Herlihy, M.; Luchangco, V.; Martin, P.; et al.. *Dynamic-sized lock-free data structures*. Proceedings of the twenty-first annual symposium on Principles of distributed computing, 2002. `10.1145/571825.571847`
