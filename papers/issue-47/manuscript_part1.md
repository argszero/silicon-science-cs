# What Does a Prediction Buy? A Signed-Error Decomposition of the Consistency–Robustness Tradeoff in Learning-Augmented Online Algorithms

## Abstract

Learning-augmented algorithms state their guarantees in a **scalar** prediction error: a worst-case
bound `eta`, or a total `|error|`. A deployed predictor does not deliver a scalar — it delivers a
*distribution* of **signed** errors whose components (bias, spread, autocorrelation, tail) are
separately measurable. This paper asks what the guarantee actually prices when that distribution
meets the algorithm, and it answers with an instrument rather than with an opinion: three canonical
problems whose ground truth is exact by construction (`ski rental`; `paging with predictions`;
`non-clairvoyant scheduling`), their standard `lambda`-blended algorithms, and a fully crossed grid
of {{D:n_profiles|d}} error profiles at {{D:n_lambdas|d}} blend settings and
{{D:replicates|d}} replicate streams, on which the **realized competitive ratio** — online cost over
the exact offline optimum — is computed per instance.

Four results. **(1) `|error|` is not a sufficient statistic, and this is a witness rather than a
p-value:** two arms carrying the *identical* multiset of `|error|` — scalar features equal **by
construction**, maximum gap exactly `{{X:facts.claim1.scalar_gap_max_exact.value|1e}}` — realize
losses that differ by up to `{{X:facts.claim1.worst_loss_gap.value|3f}}` competitive-ratio units
(problem `{{X:facts.claim1.worst_problem.value}}`, profile `{{X:facts.claim1.worst_profile.value}}`),
against a cluster-unit minimum detectable effect of `{{X:facts.claim1.worst_block_mde.value|4f}}`;
`{{X:facts.claim1.blocks_exceeding_own_mde.value|d}}` of
`{{X:facts.claim1.blocks_total.value|d}}` blocks exceed their own resolution threshold. A loss that
is not a function of the scalar cannot be predicted from it. **(2) Where the design resolves, the
sign channel carries information the scalar does not:** on form-matched, held-out contrasts the
signed model's advantage over the magnitude model is
`{{X:facts.claim2.clean_advantage_mde.ski.value|2f}}` /
`{{X:facts.claim2.clean_advantage_mde.sched.value|2f}}` /
`{{X:facts.claim2.clean_advantage_mde.paging.value|2f}}` cluster MDEs (ski / sched / paging), and the
third is **reported unresolved** rather than rounded into a claim. **(3) A published systems-level
ordering survives contact with this harness in sign, not in magnitude:** the external anchor reports
a concordant pair (larger mean gain, smaller worst-trace degradation), and the harness reproduces
the *sign* of that concordance in all three problems — Kendall tau
`{{X:facts.claim3.tau_all.ski.value|3f}}` / `{{X:facts.claim3.tau_all.paging.value|3f}}` /
`{{X:facts.claim3.tau_all.sched.value|3f}}` — while reaching the published *magnitude* in one
problem only. **(4) Calibrating the trade-off parameter by the worst-case rule costs a measurable
factor under realistic profiles:** the median factor is
`{{X:facts.claim4.lambda_loss_median.ski.value|4f}}` /
`{{X:facts.claim4.lambda_loss_median.sched.value|4f}}` /
`{{X:facts.claim4.lambda_loss_median.paging.value|4f}}` per problem, the worst profile
`{{X:facts.claim4.lambda_loss_max.paging.value|4f}}` (95% between-stream
`[{{X:facts.claim4.lambda_loss_interval_lo.paging.value|4f}}, {{X:facts.claim4.lambda_loss_interval_hi.paging.value|4f}}]`),
and the factor does not rest on fitting `lambda` on the streams it is scored on.

The registered priors are reported individually and do not all survive. The signed-asymmetry prior is
confirmed at the level of the witness; the tail prior is **half confirmed** — tail profiles carry the
higher mean factor in all three problems (ski
`{{X:facts.claim4.lambda_mean_loss_tail.ski.value|4f}}` vs
`{{X:facts.claim4.lambda_mean_loss_other.ski.value|4f}}`, sched
`{{X:facts.claim4.lambda_mean_loss_tail.sched.value|4f}}` vs
`{{X:facts.claim4.lambda_mean_loss_other.sched.value|4f}}`, paging
`{{X:facts.claim4.lambda_mean_loss_tail.paging.value|4f}}` vs
`{{X:facts.claim4.lambda_mean_loss_other.paging.value|4f}}`) while the correlations are weak
(`{{X:facts.claim4.lambda_corr_tail.ski.value|2f}}` / `{{X:facts.claim4.lambda_corr_tail.sched.value|2f}}`
/ `{{X:facts.claim4.lambda_corr_tail.paging.value|2f}}`) and the relation is non-monotone in spread;
and the problem-structured-sign prior is not resolved by this design at the resolution it was
registered at (Section 7). Six frozen limits travel with the claims — an attachment that is
model-dependent, a design whose own null is **shifted** so that negative verdicts are
uninterpretable, an uneven unit reach reported per profile, a concordance that is rank agreement and
not magnitude, a generalising unit that is the profile rather than the repeated measurement, and a
synthetic harness anchored to one real system (Section 5). Everything reproduces from one CPU-only
command with the classic competitive ratios as exact anchors.

## 1. Introduction

### 1.1 The measurement gap

Two bodies of work in this area do not share a metric. On one side, guarantees for
learning-augmented algorithms are *functions of a scalar error*: the consistency–robustness
trade-off is stated over a coefficient `lambda`, and the degradation term is written in a worst-case
`eta` or an aggregate `|error|` [@mitzenmacher] [@lykouris]. On the other side, systems groups
deploy learned predictors and report *end-to-end* deltas against a strong baseline — a mean gain and
a worst-case degradation — with no reference to a prediction error measure at all [@fengkvcache]
[@zhoulearningbelady]. The field's own 2026 survey separates the two bodies explicitly and names
benchmarking and endogenous error among its open problems [@lassurvey] — the clearest available
statement that the measurement layer connecting them does not exist yet.

The gap is not a lack of care in either camp; it is that **the scalar is the natural object of
worst-case analysis and the distribution is the natural object of a deployed predictor**, so the two
sides have no shared quantity to disagree about. This paper measures the quantity they would
disagree about.

### 1.2 What is measured

We take the field's own yardstick — the competitive ratio — and compute it *realized*, per instance,
against ground truth that is exact by construction: the offline optimum is computable exactly for
every instance in all three problems (the classic buy-or-rent optimum; Belady's optimum for paging;
the optimal schedule with known processing times). Each instance carries a prediction drawn from a
profile with a **measured** structure — bias, spread, autocorrelation, tail probability and tail
multiplier — and the blend parameter `lambda` trades the prediction-following arm against the robust
arm.

The measured object is therefore the **loss realized by the blended algorithm as a function of the
components of the prediction's signed error**: not a bound, not a worst case, and not a summary
statistic of the error. The scalar `|error|` regression that the field's bounds are written against
is carried along as the baseline, on the same held-out cells.

### 1.3 Contributions

* **C1 — an instrument, and a constructive witness that `|error|` is not sufficient.** The
  decomposition (positive bias, negative bias, spread, tail) is validated against the scalar
  baseline on held-out cells and against the classic ratios at both ends of the error range. The
  witness is exact: two arms with the same scalar features by construction, whose realized losses
  differ by up to `{{X:facts.claim1.worst_loss_gap.value|3f}}` (Section 4.1).
* **C2 — where the design resolves, the sign channel is real** (Section 4.2), and where it does not,
  the paper says so and says why: the unmatched-form reading is retired and the paging contrast is
  reported unresolved (Section 5, L2).
* **C3 — a published system-level ordering is reproduced in sign** by a synthetic harness, and the
  limits of that reproduction are measured per profile rather than asserted (Sections 4.3 and 5,
  L3–L4).
* **C4 — the cost of worst-case calibration is a measured factor**, with between-stream intervals and
  an out-of-sample check on the `lambda` it uses (Section 4.4), reported per problem rather than
  pooled.
* **C5 — a method contribution**: the resolution unit, the shifted null, the reach statement and the
  coordinate census are shipped as procedures, and the registered priors are reported one by one,
  including the one that does not resolve (Sections 5–7).

### 1.4 Significance: whose belief changes

If C1 is true, then a guarantee written in `eta` or in an aggregate `|error|` is **loose for one of
the two signs by a measurable amount**, and the object a theorem should be stated over is
*directional*. That changes what an "optimal consistency–robustness trade-off" is a trade-off
between, which is a question for the theory of this field, not a matter of numeric polish
[@weioptimal] [@shencalibrated].

If C4 is true, then a systems team that follows the standard worst-case calibration of `lambda` pays
a factor of roughly `{{X:facts.claim4.lambda_loss_median.sched.value|2f}}`–`{{X:facts.claim4.lambda_loss_median.ski.value|2f}}`
in the typical case, and a signed decomposition tells that team **which half of their predictor's
error is worth reducing**. The decision "spend the next unit of effort on the predictor or on the
fallback" is exactly the quantity measured here. This is the audience named by the decision-focused
literature from the other direction [@elmachtoub] [@vanderschueren], and it is the audience the
published cache systems are built for [@lahanchor].

### 1.5 Roadmap

Section 2 places the instrument against the literature it borrows from and the literature it
measures. Section 3 defines the instrument and the design, including the two attachments, the
shifted null and the resolution unit. Section 4 reports the four results. Section 5 states the six
frozen limits, each with the measurement that establishes it. Section 6 gives the methodology and
the reproduction specification. Section 7 reports the registered priors. Section 8 states the
threats and argues why the result is still worth publishing. Section 9 concludes.

## 2. Related work

This section is organised by the literatures the instrument stands on, and each subsection ends with
the **specific** difference between that literature and this paper. The subsections are not a
survey; they are the places where a reasonable reader would expect this paper's claims to have been
made already.

### 2.1 Algorithms with predictions

The framework is due to Mitzenmacher and Vassilvitskii, who framed a prediction as an interpolation
between the online and the offline optimum [@mitzenmacher]; the canonical rule is the caching
algorithm of Lykouris and Vassilvitskii, whose guarantee is stated directly in the prediction error
[@lykouris], with near-optimal bounds under a stated error [@rohatgi], the optimal
robustness–consistency curve for a class of one-dimensional problems [@weioptimal], and extensions
to weighted paging [@bansalweighted] [@jiangweightedpaging] and to a simpler caching rule with a
better bound [@weibettersimpler]. The way in which several predictors are combined is itself a
design axis: through a portfolio [@dinitzportfolio], through confidence ratings [@anandmultiple],
through soft predictions [@kodialam], by mixing predictors for metric problems [@antoniadismixing],
and through a second prediction channel in the dual-prediction model [@coesterdual]. The prediction
itself can be learned to minimise the downstream ratio [@khodak], its uncertainty can be quantified
[@sunquantified], its accuracy can be assumed [@guptaaccurate], its own error measure can be
designed around [@lipredictionspecific], and the worst-case error can be replaced by a calibration
condition [@shencalibrated]. Problems carrying the framework now include facility location
[@fotakis], sequencing with query predictions [@angelopoulossequencing], matching and load balancing
with learnable, instance-robust predictors [@lavastida], precedence-constrained jobs with
minimalistic predictions [@lassota], interval scheduling [@boyarinterval], speed scaling
[@balkanskispeed], the Canadian traveller problem [@bampiscanadian], online graph problems
[@azargraph], capacity scaling under unreliable predictions [@ruttencapacity], smoothed online
optimization [@ruttensmoothed], permutation predictions for non-clairvoyant scheduling
[@lindermayrpermutation], flow time under uncertain processing times [@azarflowtime], online packing
[@grigorescupacking], preemptive FIFO buffer management [@hsiehfifo], online time-windows TSP
[@angelopouloswindows], and online allocation as a whole [@generalframeworkallocation]. The
resource-bounded view is complementary: advice complexity bounds the bits a hard online problem needs
[@kommadvice] [@boyaradviceclass], and complexity classes place prediction-augmented problems in
their own landscape [@bergclasses]. Two further strands look past the guarantee: a survey of
scheduling with predictions [@choscheduling], a queueing note listing open problems where
predictions meet LLM workloads [@mitzenmacherqueueing], a survey of the whole area that separates
formal guarantees from systems evidence and names benchmarking among its open problems
[@lassurvey], and decisions priced in the units the deployer actually pays — mispredictions in
scheduling [@mitzenmachermisprediction], cloud-egress dollars rather than cache hits
[@mandarapucaching], and churn prevention through a predict-and-optimize formulation [@gomezchurn].

**Specific difference.** Every one of these works takes the error scalar as the *input to a bound* and
reports the bound. None of them measures the **realized** competitive ratio as a function of the
components of the error distribution, and none asks whether the scalar is a sufficient statistic for
that realized loss. When this literature says "the algorithm is `O(eta)`-consistent", it is stating a
guarantee about the worst case; this paper measures which component of a realistic error that
guarantee is actually sensitive to, and finds — constructively — that the answer cannot be `|error|`
alone.

### 2.2 Ski rental

Ski rental is the field's smallest complete problem, and its literature spans the classical
competitive view and the distributional one: average-case analyses [@fujiwarabuy], randomized
multislope variants [@lotker], improved learning-augmented algorithms for the multi-option setting
[@shinmultislope] and the optimal multi-option trade-off [@shintradeoff], a Bayesian treatment with
discrete distributions [@kangbayesian], distributional predictions of unknown quality
[@cuidistributional], the distributional question posed and solved in theory as a robust and
consistent threshold problem for one problem only [@skidistadvice], multi-shop variants with
machine-learned advice [@wangmultishop], tail-risk control in the two-slope setting [@cuitwoslope]
and in the online problem more generally [@dinitztailrisk], alternative performance metrics
[@chenmetric], the reduction of dynamic power management to ski-rental-type bounds
[@antoniadispowermanagement], combinatorial variants alongside online bipartite matching
[@zhangcombinatorial], and cloud cost under constraints [@khanaferconstrained].

**Specific difference.** These works characterise the optimal threshold, the optimal randomized
policy, or a bound as a function of a stated error model — including the distributional one, which
solves the problem completely under its own model [@skidistadvice]. This paper uses ski rental as the
clean instrument bed: it asks what the realized ratio does as the *sign* of the error moves while its
magnitude is held fixed, which is a question the threshold-optimisation literature does not pose
because its object is the threshold, not the error's direction.

### 2.3 Paging and caching

Classical bounds are the yardstick this paper measures against: Irani's account [@irani],
randomized analyses [@achlioptas] and strongly competitive randomized algorithms [@mcgeoch],
finely-competitive paging [@blumfinely], the effect of lookahead [@alberslookahead], paging with
dynamic capacity [@pesericodynamic], the question of whether competitive paging is an artefact of
its model [@pesericoartifact], algorithms that beat LRU on parametrized inputs [@moruz], paging with
vanishing regret [@emekvanishing], and weighted paging with unknown weights [@levyunknown]. The
learning-augmented end of the same problem appears in the prediction-based caching rule [@lykouris],
near-optimal bounds [@rohatgi], robustness improvements [@chenrobustpaging], and bounds on what
succinct predictions can buy [@antoniadissuccinct]. The systems end is the cache-replacement
literature: a taxonomy of deployed policies [@jaintaxonomy], a cost-effective learned replacement
policy [@sethumurugan], learning eviction against Belady's rule [@zhoulearningbelady], learned
replacement for multicore processors [@souzarlreplacement], the survey of policies a deployed cache
actually chooses between [@cachereplsurvey], and the published eviction system this paper's external
cell is anchored to [@lahanchor].

**Specific difference.** The theory literature reports consistency and robustness under a stated
`eta`; the systems literature reports hit-ratio deltas against a strong baseline. This paper is the
first to put both on the same axis: the measured quantity is the realized ratio against Belady's
optimum (exact), and the error fed to the blend is the signed misprediction of re-use, so the
robustness number a trace-level evaluation reports and the consistency number the theory states are
read off the *same* measurement. The published ordering itself is what Section 4.3 tests
[@lahanchor].

### 2.4 Scheduling

Non-clairvoyant scheduling carries the same scalar-error guarantee structure [@imnclairvoyant], with
partial predictions [@benomarpartial], progress bars [@benomarprogress], the observation that precise
speeds are not necessary [@lindermayrspeedoblivious], delayed-clairvoyant flow time through a borrow
graph [@lindermayrdelayed], makespan bounds for parallel machines [@chentighter], unrelated-machines
makespan with learning augmentation [@babamakespan], contract scheduling with distributional advice
[@angelopouloscontract], the classical non-clairvoyant objectives [@bansalslowdown]
[@kimweightedflow], scheduling under explorable uncertainty [@albersexplorable], and speed scaling
for energy [@bamasspeedscaling].

**Specific difference.** Scheduling is where this paper's design *resolves*: the form-matched
held-out contrast is largest here (Section 4.2). The difference from the listed works is the same as
above — they prove bounds in `eta`; this paper measures which component of a signed error the
realized flow-time ratio is sensitive to, and it reports the resolution of that measurement rather
than a bound.

### 2.5 Decision-focused learning

The decision-focused view makes the downstream decision the training objective: the smart
predict-then-optimize formulation [@elmachtoub], its foundations, benchmarks and surveys
[@mandifoundations] [@mandirank], robustness of the training loss [@schutterobust], empirical
robustness tests [@farfatrobustness], when and why traditional prediction models fail [@liuwhenwhy],
an empirical comparison of predict-then-optimize against predict-and-optimize [@vanderschueren], a
reported deficiency in which decision quality falls as data grows [@wangdeficiency], training with
directional gradients [@huangdirectional], the autocorrelated optimize-via-estimate regime
[@wangautocorrelated], attribution of decision value in such systems [@ziliaskopoulos], and
generalisation bounds for the framework [@liugeneralization] and for imprecise uncertainty
[@donggeneralizeddfl]. The asymmetric-loss strand is directly relevant to this paper's construct:
asymmetric losses for multi-label classification [@benbaruch], for noisy labels [@zhounoisylabels],
for misclassification costs [@barnesmisclassification], multi-class cost-sensitive boosting with
`p`-norm losses [@lozanoboosting], a modified Stein loss [@fusteinsloss], joint models of prediction
and optimisation [@kotaryjoint] [@kotaryproxy], decision trees under the framework
[@elmachtoubtrees], an energy-storage application closing the prediction–operation gap
[@kangenergystorage], the standard library [@tangpyepo], and an optimal-transport prior for
robustness [@wenoptimaltransport].

**Specific difference.** This literature has already established that the loss need not be a
function of the prediction error alone — it uses *asymmetric* losses in training for exactly that
reason. This paper asks the mirror-image question that the training-side literature does not: given a
deployed predictor's *signed* error distribution, which component does the **algorithm's realized
ratio** price? The asymmetric-loss works change the objective; this measures what an unchanged
objective's guarantee misses. That is why the construct here is a decomposition of the *error*, not
a design of the loss.

### 2.6 Robustness and risk

The robustness–consistency trade-off itself has been characterised for matching with advice
[@jinadvice], for a mechanism class with matching lower bounds [@strategyproofsched], and for online
allocation under unreliable advice, where loss is proportional to the prediction error under
bounded-error assumptions and exposure fairness and distribution shift are the stated second
objectives [@allocationunreliable]; its dependence on prediction accuracy has been analysed for the
distributionally-robust competitive ratio [@yoshinagadro], and distribution-free robust
predict-then-optimize has been formulated in function spaces [@patelfunctionspaces] and with
adaptive optimal-transport priors [@wenoptimaltransport].

**Specific difference.** These are the closest works to this paper's question, and the difference is
the unit of the answer: they report a *bound* as a function of an accuracy parameter or a divergence
ball — a lower bound for a mechanism class [@strategyproofsched], a loss bound under a
bounded-error assumption [@allocationunreliable] — while this paper reports a *measured factor*: the
ratio between the worst-case calibrated blend and the empirically optimal blend, with a
between-stream interval, so that the robustness price is a number a deployer can compare against the
cost of improving the predictor.

### 2.7 Competitive analysis

The classical frame is Albers's survey [@alberssurvey] and Fiat's account [@fiat], with the
preliminaries laid out explicitly [@chenpreliminaries]. Its modern algorithmic range includes
regression-based learning augmentation [@anandregression], online covering with learning augmentation
[@amelicovering] and with multiple experts [@kevimultipleexperts], minimax and posterior-matching
constructions [@kesselheimminimax], primal-dual algorithms for the parking-permit problem
[@coesterparking], multi-objective competitive ratios [@tiedemannmultiobjective], 2D bin packing with
advice [@zhaobinpackingadvice], the pricing of information an online algorithm buys [@mabuying],
automated competitive analysis for finite-state behaviours [@horiyamafinite], online algorithms for
the discrete evacuation problem [@evacuationgeneral], and memoryless bounds for the generalized
`k`-server problem [@memorylesskserver].

**Specific difference.** Competitive analysis supplies the *exact* ground-truth quantity this paper
computes, which is why the harness can be anchored at both ends — zero error must reproduce the
consistency end, and zero-information prediction must reproduce the classic ratios (Section 3.4). The
difference is that this literature states and proves bounds, while this paper uses the same quantity
as an instrument reading and takes the classical algorithms — not a bound — as its exact anchors.

### 2.8 Learned components in systems

The reason the scalar/distribution gap matters in practice is that learned components are deployed:
the learned index [@kraskalearnedindex], its benchmarking rather than assertion [@marcusbenchmarking]
and searchable benchmark [@kipfsosd], its robustness under test [@bachfischerrobustness], its
updatability [@dingalex] and single-pass construction [@kipfradixspline], and its deployment at
Google scale [@abulibdehgoogle], together with its adversarial surface [@juepoisoning]. The cache
side of the same deployment reality is the prefetching and replacement literature [@yangmithril]
[@kimgpuhours] [@cachereplsurvey], and the newest instance is KV-cache scheduling for LLM inference
[@fengkvcache].

**Specific difference.** These systems report end-to-end deltas against a strong baseline and are
exactly the deployments this paper's C4 addresses; they do not report a prediction error measure, so
their results cannot be compared with any consistency bound. This paper supplies the missing
quantity — a realized, component-resolved loss — and anchors its ordering to one published result of
exactly this kind [@lahanchor], reporting the anchor's own reach limits rather than claiming a
reproduction.
