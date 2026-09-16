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
exactly two numbers, the node's own mean and standard deviation, fix its detectability. Four
consequences are counter-intuitive, and they are what we test. First, **where** the budget helps is
a transition band around the threshold, and it is the *comparison between rules* — not the power
— that is non-monotone in the budget: power is monotone in `k` for a fixed node (Section 3.2),
while the quantity that is non-monotone in `k` is the construct's own approximation error
(Section 7.1). The band's measured width tracks the construct's prediction to
`{{F:crit_b.max_width_rel_err_refined|p2}}` and shrinks as `1/sqrt(k)` exactly. Second, the
construct has a **ceiling** that bounds the
*prize* rather than the detection: above a saturated operating point the derived rule still
wins, but the maximum achievable gain falls to `{{F:S2.saturated_max_gain|5f}}` against
`{{F:S2.unsaturated_max_gain|4f}}` below it. Third, against a **location-preserving** node
whose moments match an honest node's, detection is pinned at the false-positive floor at every
budget, so one more re-execution buys nothing at all. Fourth, **decidability is set by the effect
size rather than by the budget**: inverting each cell's interval, only `{{F:S3.n_decidable|d}}` of
`{{F:S3.n_cells|d}}` informative cells certify an advantage at the budget this study ran, and the
streams those cells need are set by their effect size (Section 7.3). We report
a pre-registered study: four registered criteria, all met, and three registered priors, all
confirmed. A sensitivity block
then measures the construct's own limits rather than hedging them: its usable boundary is a
lattice ratio rather than a rate of convergence, the ceiling's cost is a fraction of a
percentage point, and the saturated cells' intervals contain zero, so their bound is reported as
an upper bound rather than as a certified gain. The practical answer to
the title question is that the marginal value of a re-execution is set by *where* the node sits
relative to the threshold and how dispersed it is — never by the budget alone.

**Keywords**: trustless verification, re-execution, nondeterministic pipelines, detection
power, sample-size ceiling, budget allocation

---

## 1. Introduction

A verifier who cannot trust a computation is increasingly told to *re-execute it*: run the
pipeline again, compare a pinned metric against a threshold, and reject the run if the metric
moves too far. This is the mechanism behind replayable evidence for autonomous agents
[@nova], behind the threshold rules measured for compound AI workflows [@threshold], and
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
   `{{F:crit_b.max_width_rel_err_refined|p2}}` (registered tolerance `{{F:crit_b.tol|p0}}`), and it
   shrinks as `1/sqrt(k)` exactly — `width * sqrt(k) / sigma` is constant to
   `{{F:crit_b.width_law_spread_max|1e}}` at every spread across `k = {{F:crit_b.k_band_min|d}}` to
   `{{F:crit_b.k_band_max|d}}`.
2. **There is a ceiling, and it bounds the prize, not the detection.** Above a saturated
   operating point the difference between a well-calibrated rule and a naive one remains
   statistically resolvable but shrinks to `{{F:S2.saturated_max_gain|5f}}`, against
   `{{F:S2.unsaturated_max_gain|4f}}` below it.
3. **Some node behaviours are free.** A location-preserving divergence — one whose expected
   metric value is unchanged — is detected at the false-positive rate at every budget. No
   value of `k` improves the verifier's situation, and a node that best-responds to the
   verifier picks exactly that behaviour.
4. **The comparison is decidable only for a minority of operating points.** Inverting each
   cell's interval, only `{{F:S3.n_decidable|d}}` of `{{F:S3.n_cells|d}}` informative cells
   certify an advantage at the budget this study ran; the streams a cell needs are set by its
   effect size (median `{{F:S3.n_min_median|d}}`, range `{{F:S3.n_min_min|d}}` to
   `{{F:S3.n_min_max|d}}`), not by the budget.

**Contributions.** Our organising quantity is not new, and we say so first: `u` in Section 3.2 is
the standard normal-approximation power of a one-sample mean test, three lines of algebra from the
sample-mean standard error, with its antecedents in the sample-size literature ([@power] [@wald]
[@groupseq] [@adapt]). We do not claim it as a new construct. What we contribute is what it implies
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
median factor of `{{F:crit_c.median_factor|4f}}` — that does **not** vanish as the calibration set
grows, to `n_cal = {{F:crit_c.by_n_cal.1000.n_cal|d}}` (Section 6.3), with the mechanism, its
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
`{{F:S3.n_min_median|d}}` streams to certify what `{{F:S3.n_decidable|d}}` of
`{{F:S3.n_cells|d}}` cells got for free. A verifier who reads only "more samples are better"
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
that the threshold, not the sample size, bounds trustless verification [@threshold]. That
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
declared-stream completeness below one [@nova]. That work establishes *that* re-execution is
the mechanism; it does not analyse how much of it to do, and its third-party verification is
specified rather than evaluated. We take replay's soundness for granted and ask what an
additional re-execution buys once the mechanism exists.

**Classical sequential and sample-size theory.** Power analysis [@power], the sequential
probability ratio test [@wald], group-sequential designs [@groupseq], and adaptive designs
[@adapt] all give sample-size formulas, but they assume a fixed alternative family with no
strategic node and treat the threshold as given rather than as a budget item. Our setting
differs in exactly the two ways that matter here: the alternative is chosen by a node with its
own objective, and the threshold is derived from the same false-positive budget the sampler is
calibrated to. What we derive is the mean-test specialisation of that machinery with the
sampling cost budgeted explicitly.

**Distribution-free testing and its impossibility results.** Unrestricted alternative sets
admit no consistent test [@impossibility], which bounds what any threshold rule can promise in
the worst case; the same machinery underlies minimax lower bounds for testing [@ingster].
Those results are asymptotic and qualitative: they give no budget-response law, and they say
nothing about the location-preserving case, where the bounding constant is exactly the
false-positive rate.

**Audit sampling against a strategic adversary.** Auditing with a limited budget against an
adversary who chooses what to hide is studied in the spot-checking literature [@audit], in
safety-case arguments [@safetycase], and in sampling-based verification, where statistical
model checking trades a sample count for a confidence statement [@samplingverify]. The
adversary there chooses *which* items to corrupt; here it chooses *how* to corrupt a single
scored metric, which is what makes the
location/dispersion split — and therefore the band and the ceiling — the organising structure.

**Ceilings, saturation and the value of a measurement.** That a measurement's value saturates
is familiar from information-theoretic treatments of experiment design [@design], from the
literature on metric saturation in evaluation [@metricsat], and from cost-aware sampling in
data systems [@costsampling]. Those accounts bound the value of *information*; ours bounds the
value of *repetition* under a test whose threshold is itself a choice, which is why the ceiling
appears here as a fraction of a percentage point in *power* rather than as a vanishing
information gain.

**Trustless verification has two established implementations, and neither answers the budget
question.** Hardware attestation executes inside a minimised trusted computing base
[@attestation] [@flicker], which is enough to build confidential contract platforms [@ekiden] and
secure approval devices [@notary] but leaves the TCB itself as the attack surface [@spectre].
Cryptographic proofs of computation avoid that assumption [@verifiablecompute] [@pinocchio]
[@snarkc] and are only now being applied to models and their training [@zktraining] [@zkcnn]. Both
lines answer the question "is this the run I asked for"; for a stochastic pipeline the verifier's
question is instead "how much repetition makes a divergence visible", which is a question about the
*test*, not about the proof system.

**Reproducibility and provenance.** A large body of work makes computational results reproducible
and traceable [@peng2011] [@atoml] [@neuripsrepro], fixes reporting practice so that variance is
visible [@showyourwork], and captures provenance as first-class data [@provdb]. These lines change
what a verifier can *inspect*; they do not say what a verifier should spend, and they implicitly
assume that inspecting enough of the same artefact settles the matter.

**Multiplicity, stopping and peeking.** The statistics of repeated looks are well understood *given*
a fixed null hypothesis: step-up and step-down multiplicity corrections [@bh1995] [@hochberg1988]
[@byk2001], alpha spending across interim analyses [@landemets], always-valid inference through
confidence sequences and e-values [@timeuniform] [@evalues], and the practical cost of peeking in
online experiments [@peeking]. Our setting keeps the fixed-null machinery but removes the assumption
that the alternative is fixed: the node chooses its divergence, so the multiplicity problem here is
adversarial rather than procedural.

**Distribution-free machinery and its limits.** Finite-sample tools that assume no parametric family
are available — uniform convergence over function classes [@vc1971] [@valiant], the
Dvoretzky-Kiefer-Wolfowitz bound with its sharp constant [@dkw] [@massart], two-sample comparison
[@massey], conformal prediction for set-valued guarantees [@conformalgentle] [@conformalreg]
[@conformalvalid], and minimax rates over smoothness classes [@tsybakov]. Each gives a guarantee
against a *fixed* alternative class; the adversary in our setting is inside the class and picks the
member that is hardest to see, which is why the guarantee that survives is the trivial one — the
false-positive rate.

**Budget and sample size in empirical computer science.** In empirical CS the same budget question
appears as sample-size and power advice for experiments [@dyba2006], as significance-testing
guidance for NLP and ML evaluation [@hitchhiker] [@reportscores], and as variance accounting when
benchmark scores are compared across runs [@bouthillier] [@drlrepro]. That literature establishes
*that* repetitions must be reported and subtracted before a comparison is made; it does not model a
counterparty that chooses its divergence, which is the case a verification budget exists to handle.

**Nondeterminism and repetition in AI evaluation.** The systems a verifier is asked to check
are stochastic by construction, and the evaluation literature has spent a decade learning what that
costs: judge-based evaluation is itself a noisy instrument [@llmjudge] and is sensitive to
presentation order [@judgebias]; harness choice changes conclusions at fixed models [@evalharness]
[@mmlu]; instruction tuning and prompting change the score distribution rather than a deterministic
output [@instructgpt] [@cot] [@zeroshotreason]; self-consistency buys accuracy by *sampling
more* [@selfconsistency], and verification chains by *spending more tokens* [@chainofver]
[@selfrefine]; and agentic and code benchmarks report pass@k precisely because one sample
is not a measurement [@passk] [@swebench] [@agentbench]
[@gaia]. Every one of those papers is, implicitly, a statement about how many executions a claim
costs — and none of them derives the marginal value of the next one against a counterparty that
chooses its divergence.

**Benchmark validity and saturation.** A benchmark can stop discriminating, and the reasons are
structural: underspecification makes a score depend on arbitrary implementation choices [@underspec];
leaderboards create incentives that erode their own signal [@leaderboard]; contamination and
overfitting to the test set inflate scores [@contamination] [@bigbench]; and offline evaluation can
diverge from what practitioners actually need [@recsyeval]. The alignment literature names the same
failure from the model side — proxies are optimised instead of goals [@concreteproblems], objectives
are misgeneralised [@goalmisspec], and reward models are over-optimised past a saturation point
[@rewardoveropt]. Those are *ceiling* arguments about a score; ours is a ceiling argument about a
*test*, and it is why we report the ceiling as a measured bound rather than as a caution.

**Budgeted inspection, monitoring and testing.** When inspection is priced per item, the design
question is which items to inspect: red-teaming allocates a fixed attack budget [@redteam]; property
testing fixes the number of samples per property [@propertytesting]; robust optimisation prices the
worst case rather than the average [@robustopt]; runtime verification watches a running system under a
monitor budget [@runtimeverif]; machine-learning testing surveys the same trade-off for learned
components [@mltesting]; selective prediction and abstention decide *whether* to answer at a given
confidence [@selective]; outlier exposure and anomaly detection decide what to look at next
[@outlierexposure]; and cost-sensitive learning makes the price of an error explicit in the objective
[@costsensitive]. Our verifier is an instance of this family with one unusual property: the item
under inspection chooses how it differs, so the inspection's value saturates from below.

**Allocating a sampling budget.** The data-systems literature knows that a budget buys accuracy at a
decreasing rate and that the right response is to spend it adaptively: online aggregation and
approximate query processing stop when the interval is tight enough [@onlineagg] [@aqp]; bandit
algorithms formalise exploration under a horizon [@bandits]; query-by-committee and active learning
choose the next sample by expected information [@qbc]; and classical optimal design chooses the
measurement that maximises information per unit cost [@optdesign]. We use those ideas only as a
contrast: in our setting the *stopping* rule is what is being questioned, because the quantity that
would justify stopping — a stable alternative — is the one the node controls.

**Inference foundations.** The test we analyse is deliberately classical: the Neyman-Pearson
formulation of size and power [@neymanpearson], in the Fisherian and Student traditions that fixed
the small-sample vocabulary [@fisher1922] [@student1908], with the interval estimators we use for
proportions [@wilson] [@clopperpearson] and quantiles [@quantiles], the asymptotic theory that
justifies the normal approximation and its limits [@vanderVaart] [@extremevalue], resampling where a
closed form is unavailable [@bootstrap] [@permutationtests], Monte-Carlo error accounting for the
estimates themselves [@mcmcse], and the reporting conventions that keep a p-value from being read as
an effect size [@pvalues] [@effectsize] [@tost]. Two conventions matter for our own numbers: the
detector's operating point is a trade-off curve rather than a scalar [@roc], and when the cost of a
false accept and a false reject differ, the threshold is an economic choice, not a statistical one
[@costsensitive].

**Fault-tolerant systems with adversarial participants.** The question of how much redundancy is
enough against participants that may deviate is the oldest question in this family: Byzantine
agreement bounds the number of faulty replicas a protocol can tolerate [@bft], and practical
Byzantine replication makes that bound an engineering parameter [@pbft]. Those results are *exact*
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
`c_alpha = Phi^-1(1 - alpha)`; at `alpha = {{F:stage_params.v0.alpha|2f}}` this gives
`c_alpha = {{F:stage_params.v1.c_alpha|4f}}`.

### 3.2 Closed form

**What is and is not new here.** The expression below is the textbook normal-approximation power of
a one-sample mean test against a shifted mean: three lines of algebra from the sample-mean standard
error, with the small-sample vocabulary of the Student and Fisher tradition ([@fisher1922]
[@student1908]) and the general power function of the sample-size literature ([@power] [@wald]
[@groupseq] [@adapt]) as its antecedents. It is not offered as a new construct. What is new is what
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
  `K_BAND = { {{F:crit_b.k_band_min|d}}, {{F:crit_b.k_band_mid1|d}}, {{F:crit_b.k_band_mid2|d}}, {{F:crit_b.k_band_max|d}} }`) is the *average* of that
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
  threshold with zero honest rejections, and by order-statistic symmetry [@orderstats] its
  expected false-positive rate on fresh honest data is exactly `1 / (n_cal + 1)`.
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
