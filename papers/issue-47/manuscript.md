# What Does a Prediction Buy? A Signed-Error Decomposition of the Consistency–Robustness Tradeoff in Learning-Augmented Online Algorithms

## Abstract

Learning-augmented algorithms state their guarantees in a **scalar** prediction error: a worst-case
bound `eta`, or a total `|error|`. A deployed predictor does not deliver a scalar — it delivers a
*distribution* of **signed** errors whose components (bias, spread, autocorrelation, tail) are
separately measurable. This paper asks what the guarantee actually prices when that distribution
meets the algorithm, and it answers with an instrument rather than with an opinion: three canonical
problems whose ground truth is exact by construction (`ski rental`; `paging with predictions`;
`non-clairvoyant scheduling`), their standard `lambda`-blended algorithms, and a fully crossed grid
of 13 error profiles at 5 blend settings and
16 replicate streams, on which the **realized competitive ratio** — online cost over
the exact offline optimum — is computed per instance.

Four results. **(1) `|error|` is not a sufficient statistic, and this is a witness rather than a
p-value:** two arms carrying the *identical* multiset of `|error|` — scalar features equal **by
construction**, maximum gap exactly `0.0e+00` — realize
losses that differ by up to `-0.568` competitive-ratio units
(problem `ski`, profile `unbiased_extreme`),
against a cluster-unit minimum detectable effect of `0.0187`;
`31` of
`39` blocks exceed their own resolution threshold. A loss that
is not a function of the scalar cannot be predicted from it. **(2) Where the design resolves, the
sign channel carries information the scalar does not:** on form-matched, held-out contrasts the
signed model's advantage over the magnitude model is
`1.48` /
`2.61` /
`0.97` cluster MDEs (ski / sched / paging), and the
third is **reported unresolved** rather than rounded into a claim. **(3) A published systems-level
ordering survives contact with this harness in sign, not in magnitude:** the external anchor reports
a concordant pair (larger mean gain, smaller worst-trace degradation), and the harness reproduces
the *sign* of that concordance in all three problems — Kendall tau
`0.744` / `0.889` /
`1.000` — while reaching the published *magnitude* in one
problem only. **(4) Calibrating the trade-off parameter by the worst-case rule costs a measurable
factor under realistic profiles:** the median factor is
`1.7006` /
`1.2851` /
`1.4934` per problem, the worst profile
`1.8252` (95% between-stream
`[1.8109, 1.8404]`),
and the factor does not rest on fitting `lambda` on the streams it is scored on.

The registered priors are reported individually and do not all survive. The signed-asymmetry prior is
confirmed at the level of the witness; the tail prior is **half confirmed** — tail profiles carry the
higher mean factor in all three problems (ski
`1.6915` vs
`1.5416`, sched
`1.3987` vs
`1.2536`, paging
`1.7608` vs
`1.3833`) while the correlations are weak
(`0.17` / `0.30`
/ `0.39`) and the relation is non-monotone in spread;
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
`eta` or an aggregate `|error|` [1] [2]. On the other side, systems groups
deploy learned predictors and report *end-to-end* deltas against a strong baseline — a mean gain and
a worst-case degradation — with no reference to a prediction error measure at all [3]
[4]. The field's own 2026 survey separates the two bodies explicitly and names
benchmarking and endogenous error among its open problems [5] — the clearest available
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
  differ by up to `-0.568` (Section 4.1).
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
[6] [7].

If C4 is true, then a systems team that follows the standard worst-case calibration of `lambda` pays
a factor of roughly `1.29`–`1.70`
in the typical case, and a signed decomposition tells that team **which half of their predictor's
error is worth reducing**. The decision "spend the next unit of effort on the predictor or on the
fallback" is exactly the quantity measured here. This is the audience named by the decision-focused
literature from the other direction [8] [9], and it is the audience the
published cache systems are built for [10].

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
between the online and the offline optimum [1]; the canonical rule is the caching
algorithm of Lykouris and Vassilvitskii, whose guarantee is stated directly in the prediction error
[2], with near-optimal bounds under a stated error [11], the optimal
robustness–consistency curve for a class of one-dimensional problems [6], and extensions
to weighted paging [12] [13] and to a simpler caching rule with a
better bound [14]. The way in which several predictors are combined is itself a
design axis: through a portfolio [15], through confidence ratings [16],
through soft predictions [17], by mixing predictors for metric problems [18],
and through a second prediction channel in the dual-prediction model [19]. The prediction
itself can be learned to minimise the downstream ratio [20], its uncertainty can be quantified
[21], its accuracy can be assumed [22], its own error measure can be
designed around [23], and the worst-case error can be replaced by a calibration
condition [7]. Problems carrying the framework now include facility location
[24], sequencing with query predictions [25], matching and load balancing
with learnable, instance-robust predictors [26], precedence-constrained jobs with
minimalistic predictions [27], interval scheduling [28], speed scaling
[29], the Canadian traveller problem [30], online graph problems
[31], capacity scaling under unreliable predictions [32], smoothed online
optimization [33], permutation predictions for non-clairvoyant scheduling
[34], flow time under uncertain processing times [35], online packing
[36], preemptive FIFO buffer management [37], online time-windows TSP
[38], and online allocation as a whole [39]. The
resource-bounded view is complementary: advice complexity bounds the bits a hard online problem needs
[40] [41], and complexity classes place prediction-augmented problems in
their own landscape [42]. Two further strands look past the guarantee: a survey of
scheduling with predictions [43], a queueing note listing open problems where
predictions meet LLM workloads [44], a survey of the whole area that separates
formal guarantees from systems evidence and names benchmarking among its open problems
[5], and decisions priced in the units the deployer actually pays — mispredictions in
scheduling [45], cloud-egress dollars rather than cache hits
[46], and churn prevention through a predict-and-optimize formulation [47].

**Specific difference.** Every one of these works takes the error scalar as the *input to a bound* and
reports the bound. None of them measures the **realized** competitive ratio as a function of the
components of the error distribution, and none asks whether the scalar is a sufficient statistic for
that realized loss. When this literature says "the algorithm is `O(eta)`-consistent", it is stating a
guarantee about the worst case; this paper measures which component of a realistic error that
guarantee is actually sensitive to, and finds — constructively — that the answer cannot be `|error|`
alone.

### 2.2 Ski rental

Ski rental is the field's smallest complete problem, and its literature spans the classical
competitive view and the distributional one: average-case analyses [48], randomized
multislope variants [49], improved learning-augmented algorithms for the multi-option setting
[50] and the optimal multi-option trade-off [51], a Bayesian treatment with
discrete distributions [52], distributional predictions of unknown quality
[53], the distributional question posed and solved in theory as a robust and
consistent threshold problem for one problem only [54], multi-shop variants with
machine-learned advice [55], tail-risk control in the two-slope setting [56]
and in the online problem more generally [57], alternative performance metrics
[58], the reduction of dynamic power management to ski-rental-type bounds
[59], combinatorial variants alongside online bipartite matching
[60], and cloud cost under constraints [61].

**Specific difference.** These works characterise the optimal threshold, the optimal randomized
policy, or a bound as a function of a stated error model — including the distributional one, which
solves the problem completely under its own model [54]. This paper uses ski rental as the
clean instrument bed: it asks what the realized ratio does as the *sign* of the error moves while its
magnitude is held fixed, which is a question the threshold-optimisation literature does not pose
because its object is the threshold, not the error's direction.

### 2.3 Paging and caching

Classical bounds are the yardstick this paper measures against: Irani's account [62],
randomized analyses [63] and strongly competitive randomized algorithms [64],
finely-competitive paging [65], the effect of lookahead [66], paging with
dynamic capacity [67], the question of whether competitive paging is an artefact of
its model [68], algorithms that beat LRU on parametrized inputs [69], paging with
vanishing regret [70], and weighted paging with unknown weights [71]. The
learning-augmented end of the same problem appears in the prediction-based caching rule [2],
near-optimal bounds [11], robustness improvements [72], and bounds on what
succinct predictions can buy [73]. The systems end is the cache-replacement
literature: a taxonomy of deployed policies [74], a cost-effective learned replacement
policy [75], learning eviction against Belady's rule [4], learned
replacement for multicore processors [76], the survey of policies a deployed cache
actually chooses between [77], and the published eviction system this paper's external
cell is anchored to [10].

**Specific difference.** The theory literature reports consistency and robustness under a stated
`eta`; the systems literature reports hit-ratio deltas against a strong baseline. This paper is the
first to put both on the same axis: the measured quantity is the realized ratio against Belady's
optimum (exact), and the error fed to the blend is the signed misprediction of re-use, so the
robustness number a trace-level evaluation reports and the consistency number the theory states are
read off the *same* measurement. The published ordering itself is what Section 4.3 tests
[10].

### 2.4 Scheduling

Non-clairvoyant scheduling carries the same scalar-error guarantee structure [78], with
partial predictions [79], progress bars [80], the observation that precise
speeds are not necessary [81], delayed-clairvoyant flow time through a borrow
graph [82], makespan bounds for parallel machines [83], unrelated-machines
makespan with learning augmentation [84], contract scheduling with distributional advice
[85], the classical non-clairvoyant objectives [86]
[87], scheduling under explorable uncertainty [88], and speed scaling
for energy [89].

**Specific difference.** Scheduling is where this paper's design *resolves*: the form-matched
held-out contrast is largest here (Section 4.2). The difference from the listed works is the same as
above — they prove bounds in `eta`; this paper measures which component of a signed error the
realized flow-time ratio is sensitive to, and it reports the resolution of that measurement rather
than a bound.

### 2.5 Decision-focused learning

The decision-focused view makes the downstream decision the training objective: the smart
predict-then-optimize formulation [8], its foundations, benchmarks and surveys
[90] [91], robustness of the training loss [92], empirical
robustness tests [93], when and why traditional prediction models fail [94],
an empirical comparison of predict-then-optimize against predict-and-optimize [9], a
reported deficiency in which decision quality falls as data grows [95], training with
directional gradients [96], the autocorrelated optimize-via-estimate regime
[97], attribution of decision value in such systems [98], and
generalisation bounds for the framework [99] and for imprecise uncertainty
[100]. The asymmetric-loss strand is directly relevant to this paper's construct:
asymmetric losses for multi-label classification [101], for noisy labels [102],
for misclassification costs [103], multi-class cost-sensitive boosting with
`p`-norm losses [104], a modified Stein loss [105], joint models of prediction
and optimisation [106] [107], decision trees under the framework
[108], an energy-storage application closing the prediction–operation gap
[109], the standard library [110], and an optimal-transport prior for
robustness [111].

**Specific difference.** This literature has already established that the loss need not be a
function of the prediction error alone — it uses *asymmetric* losses in training for exactly that
reason. This paper asks the mirror-image question that the training-side literature does not: given a
deployed predictor's *signed* error distribution, which component does the **algorithm's realized
ratio** price? The asymmetric-loss works change the objective; this measures what an unchanged
objective's guarantee misses. That is why the construct here is a decomposition of the *error*, not
a design of the loss.

### 2.6 Robustness and risk

The robustness–consistency trade-off itself has been characterised for matching with advice
[112], for a mechanism class with matching lower bounds [113], and for online
allocation under unreliable advice, where loss is proportional to the prediction error under
bounded-error assumptions and exposure fairness and distribution shift are the stated second
objectives [114]; its dependence on prediction accuracy has been analysed for the
distributionally-robust competitive ratio [115], and distribution-free robust
predict-then-optimize has been formulated in function spaces [116] and with
adaptive optimal-transport priors [111].

**Specific difference.** These are the closest works to this paper's question, and the difference is
the unit of the answer: they report a *bound* as a function of an accuracy parameter or a divergence
ball — a lower bound for a mechanism class [113], a loss bound under a
bounded-error assumption [114] — while this paper reports a *measured factor*: the
ratio between the worst-case calibrated blend and the empirically optimal blend, with a
between-stream interval, so that the robustness price is a number a deployer can compare against the
cost of improving the predictor.

### 2.7 Competitive analysis

The classical frame is Albers's survey [117] and Fiat's account [118], with the
preliminaries laid out explicitly [119]. Its modern algorithmic range includes
regression-based learning augmentation [120], online covering with learning augmentation
[121] and with multiple experts [122], minimax and posterior-matching
constructions [123], primal-dual algorithms for the parking-permit problem
[124], multi-objective competitive ratios [125], 2D bin packing with
advice [126], the pricing of information an online algorithm buys [127],
automated competitive analysis for finite-state behaviours [128], online algorithms for
the discrete evacuation problem [129], and memoryless bounds for the generalized
`k`-server problem [130].

**Specific difference.** Competitive analysis supplies the *exact* ground-truth quantity this paper
computes, which is why the harness can be anchored at both ends — zero error must reproduce the
consistency end, and zero-information prediction must reproduce the classic ratios (Section 3.4). The
difference is that this literature states and proves bounds, while this paper uses the same quantity
as an instrument reading and takes the classical algorithms — not a bound — as its exact anchors.

### 2.8 Learned components in systems

The reason the scalar/distribution gap matters in practice is that learned components are deployed:
the learned index [131], its benchmarking rather than assertion [132]
and searchable benchmark [133], its robustness under test [134], its
updatability [135] and single-pass construction [136], and its deployment at
Google scale [137], together with its adversarial surface [138]. The cache
side of the same deployment reality is the prefetching and replacement literature [139]
[140] [77], and the newest instance is KV-cache scheduling for LLM inference
[3].

**Specific difference.** These systems report end-to-end deltas against a strong baseline and are
exactly the deployments this paper's C4 addresses; they do not report a prediction error measure, so
their results cannot be compared with any consistency bound. This paper supplies the missing
quantity — a realized, component-resolved loss — and anchors its ordering to one published result of
exactly this kind [10], reporting the anchor's own reach limits rather than claiming a
reproduction.

## 3. Instrument and design

This section defines the instrument: the three decision problems and their exact ground truth
(§3.1), the error profiles and the blend that consumes them (§3.2), the attachment question that has
to be settled before paging can be reported at all (§3.3), the unit every verdict is quoted in
(§3.4), the null the design is measured against (§3.5), and the external cell, the controls and the
coordinate census that bound what the instrument is allowed to conclude (§3.6). The instrument is
deterministic, reads no clock, opens no socket, and every number in Section 4 is recomputed from
committed stage artefacts rather than transcribed from a run's console.

### 3.1 Three decision problems, and an offline optimum that is exact

The field's yardstick is the competitive ratio — the online cost over the offline optimum
[118] [117] [119]. Measuring a **realized** ratio therefore requires the
optimum itself rather than a bound on it, and the three problems here are chosen because their
optima are computable exactly for every instance the instrument generates:

* **Ski rental** (`ski`) — buy or rent under an unknown horizon. The offline optimum is exact by
  enumeration over the purchase day, so the realized ratio is exact for every stream. The problem is
  the field's canonical test-bed [49] [61] [60], and its
  prediction-augmented variants are the most numerous in the literature
  [17] [48] [52] [55] [50].
* **Paging** (`paging`) — evict-on-full with a cache. Belady's optimum is exact
  [62] [63] [66], and the problem is the one the learning-augmented
  caching literature is built on [2] [11] [12] [13].
* **Scheduling** (`sched`) — single machine, known processing times, minimise total completion time.
  The optimum is exactly the shortest-processing-time order [43], the problem on which
  scheduling-with-predictions results are stated [45] [34].

The grid is instantiated at a fixed size: `1200` steps per trace, `300` jobs for
the scheduling instances, and `10` pages with a cache of `5` for paging. The
three problems are reported **separately throughout**; no number in this paper pools them.

### 3.2 The prediction is a profile of five coordinates, and the blend is one parameter

A prediction stream is generated from a **declared profile** carrying five coordinates — bias,
spread, autocorrelation, tail probability and tail multiplier. The profile set is fixed at
`13` members (Table 1), chosen so that the stream's mean, its spread and its tail can
be moved independently of one another. That independence is what makes Section 4.4 readable as a
statement about *which* coordinate the worst-case calibration reacts to, rather than a statement
about "noisy predictions" in general.

| profile | bias | spread | autocorrelation | tail probability | tail multiplier |
|---|---|---|---|---|---|
| `ar_mid` | 0.00 | 0.15 | 0.60 | 0.00 | 1.0 |
| `over_extreme` | 0.50 | 0.50 | 0.00 | 0.00 | 1.0 |
| `over_mid` | 0.15 | 0.15 | 0.00 | 0.00 | 1.0 |
| `tail_mid` | 0.00 | 0.15 | 0.00 | 0.05 | 5.0 |
| `unbiased_extreme` | 0.00 | 1.00 | 0.00 | 0.00 | 1.0 |
| `unbiased_high` | 0.00 | 0.30 | 0.00 | 0.00 | 1.0 |
| `unbiased_low` | 0.00 | 0.05 | 0.00 | 0.00 | 1.0 |
| `unbiased_mid` | 0.00 | 0.15 | 0.00 | 0.00 | 1.0 |
| `unbiased_veryhigh` | 0.00 | 0.60 | 0.00 | 0.00 | 1.0 |
| `under_extreme` | -0.50 | 0.50 | 0.00 | 0.00 | 1.0 |
| `under_mid` | -0.15 | 0.15 | 0.00 | 0.00 | 1.0 |
| `wild_tail` | 0.00 | 0.30 | 0.00 | 0.10 | 8.0 |
| `zero` | 0.00 | 0.00 | 0.00 | 0.00 | 1.0 |

**Table 1.** The `13` declared error profiles. Each row is one generator: `bias` and
`spread` are the location and scale of the error, `autocorrelation` is the lag-1 retention, and the
tail is a `tail probability` of an error multiplied by `tail multiplier`. This profile set is used
unchanged by every result in Section 4.

The profile is consumed through a single blend parameter `lambda` on a `5`-point grid,
which interpolates between the prediction-following arm and the robust arm — the construction the
learning-augmented literature states its consistency–robustness trade-off on
[2] [6] [7] [23]. Every cell is
`13` profiles × `5` blend settings × `16` replicates ×
`4` traces per replicate, and the **scalar baseline** carried along on the same
held-out cells is a regression of realized loss on `|error|` — the statistic the field's bounds are
written against [120] [1] [5].

### 3.3 Paging has two attachments, and they are not the same experiment

A prediction must be attached to something before it can be used. Two attachments are available in
this instrument: a **step-common** multiplier applied to every candidate's score, and a **per-page**
multiplier. They are not interchangeable, and the difference is measured rather than argued. The
step-common attachment is provably blind to positive errors — a common factor cannot reorder an
argmax — and it reproduces the zero-error cost exactly
(`32/32`
traces on non-negative errors), while the per-page attachment differs on the same information
(`31/32`
traces). The control's third relation is the trap it exists to catch: a positive **bias** is not a
non-negative **multiplier**, and a shared attachment still changes the realized cost on
`6/32`
traces of the `over_extreme` profile, because the scored distance floors and ties.

The consequence is carried as limit **L1**: every statement this paper makes about *positive-bias*
predictions in paging is a statement about the per-page attachment, not an attachment-free fact. The
literature's caching constructions differ in exactly this place — which quantity the advice is
allowed to touch [72] [14] [73] — so a paper that
reported a positive-bias result without naming its attachment would be reporting an artefact of the
attachment as a property of the problem.

### 3.4 The resolution unit is the profile, not the repeated measurement

Every verdict is quoted in **cluster** units: the minimum detectable effect is computed over
`(profile, replicate)` clusters, not over the paired units an earlier version of this pipeline used
[141] [142] [143] [144]. Paired units share the error generator, the
implementation and the fit, so an MDE computed over them was optimistic by 3.7–6.3×, measured. Under
the cluster unit the tightest resolution in the design is
`0.0187` competitive-ratio units. This is a correction of the
instrument by the instrument, and it is carried as limit **L5**.

### 3.5 The null is shifted, so a negative verdict is uninterpretable

The design compares a signed arm against a scalar arm matched **in form** — both are two-term, and
they differ in the odd term. Matching the form is necessary but not sufficient, because the
object-level test is not sign-free: under a synthetic **even** target, which by construction has no
sign dependence, the odd parameter is penalised by roughly 13 cluster MDEs (ski
`-12.95`, sched
`-13.12`, paging
`-1.53`). A design that punishes its own odd term under a
sign-free target cannot read a negative as evidence against a signed model.

Two consequences are frozen as limit **L2** and applied everywhere below: only the **positive**
resolutions are reported as evidence, and the earlier unmatched-form reading is **retired** — its
sign is not even stable across problems (ski `-9.16`,
sched `+6.62`, paging
`-3.70`), which is what a form confound looks
like when it is measured instead of assumed.

### 3.6 The external cell, the controls, and the coordinate census

Three apparatuses bound what the instrument may conclude, and each reports a measurement rather than
a promise:

* **The external cell**, anchored to one published system result [10], reproduces the
  *ordering* of that result's reported pair and **reports its own reach** rather than gating on it
  (Section 4.3, limit L3). Three checks are structural gates; the reach row is a measurement, because
  an always-green gate is decoration.
* **The controls** are the classic ratios recovered at both ends of the error range (the instrument
  must reproduce the known competitive ratio where the prediction is perfect and where it is
  adversarial), the attachment control C5 just described, and a **liveness** control that corrupts a
  throwaway copy of the external cell once per named check and requires that check to fail: all 13
  mutations fired, each tripping exactly one check.
* **The coordinate census** scans the package for the three declared classes of hidden input the
  authoring machine supplies silently — an accidental git-object read, a network read, and a clock
  or entropy read — and reports `0` violations over all three.
  Reproducibility apparatus in this literature
  is usually stated as an intention [145] [146] [147];
  here it is a reading, and its own limits are reported with it [148] [68].

## 4. Results

The four subsections are the four contributions of Section 1.3, in that order, each with the
measurement that establishes it and the limit it has to carry.

### 4.1 The scalar error is not sufficient, and the witness is by construction

A constructive witness settles sufficiency without a model-selection argument: two arms are built
with the **same multiset of `|error|`** — same mean, same standard deviation, same 95th percentile —
differing only in sign, so their scalar features agree by construction. The largest remaining gap
between the two arms' scalar features, over every block of the design, is exactly
`0.0e+00`. Their **realized losses** differ by up to
`-0.568` competitive-ratio units (problem
`ski`, profile `unbiased_extreme`), against
a cluster-unit minimum detectable effect of `0.0187` — a gap
above its own resolution threshold in `31` of
`39` blocks, with at least
`16` pairs in every block.

The reading is not statistical. A loss that is not a function of the scalar cannot be predicted from
it, so no amount of capacity in the scalar regression can recover the difference — which is why the
witness is stated as an identity (the scalar features are equal) plus a measured gap (the losses are
not). This is the sharpest available form of the objection to the field's own quantifier, where
`|error|` or `eta` appears as a sufficient statistic for the price of misprediction
[1] [5] [45] [6]. Criterion (a)'s held-out
model comparison returns **`measured`** for
scheduling and does **not** resolve for ski rental or paging under this design; the object-level
contrasts carry those two (§4.2), and the criterion is reported per problem rather than as one
verdict.

### 4.2 Where the design resolves, the sign channel carries information

The second result is the one the shifted null constrains most tightly, so it is reported in the
direction the design can support. Comparing the signed arm against the scalar arm matched in form,
per problem, on cells held out by profile, the advantage is
`+1.48` cluster MDEs for ski rental and
`+2.61` for scheduling; for paging it is
`+0.97`, below the resolution threshold, and it is
reported as **unresolved** rather than as a small effect. The paging null is not noise: its own
shifted-null penalty is roughly a tenth of the other two problems'
(`-1.53` against
`-12.95` and
`-13.12`), so paging is the problem where the design comes
closest to resolving and still does not.

This is the result that makes the paper's object *directional*, and it is where the decision-focused
literature and this instrument meet from opposite sides: that literature shows that a scalar
training objective is the wrong objective for a downstream decision
[8] [9] [92] [94], while a guarantee stated in `eta` is
the wrong *statement* for the same reason
[103] [101] [102] [105] [104]. The
instrument says which half of the error a loss is reacting to, and §4.4 prices the consequence.

### 4.3 A published ordering survives contact with the harness, in sign

The external cell takes one published system result [10] and asks whether this instrument
reproduces the *ordering* of its reported pair. The published pair is concordant: the cache with the
larger mean gain (`26%` over its predecessor, against
`16.7%` for the comparison cache, derived as a
ratio in the artefact rather than asserted) is also the one with the smaller worst-trace degradation
over the non-learned baseline (0.8% against 8.8%). Ranking the harness's own profiles by mean gain
and by the best unit's tail, the concordance holds in all three problems — Kendall's tau
`0.744` for ski, `0.889` for
paging and `1.000` for scheduling — and it still holds when the
zero-error anchor, which is extreme on both axes by construction, is dropped:
`0.697` /
`0.873` /
`1.000`.

The honest second half of this result is the reach row, and it is a limit before it is a finding. The
published robustness scale is a 0.8–8.8% worst-trace degradation; the harness reaches that scale in
**one** problem and in neither of the other two. Ski rental has
`12` of
`13` profiles at or above 0.8% and
`11` at or above 8.8%; paging and scheduling
have `0` each, and in those two problems
the harness's worst unit is *better* than the non-learned baseline at every profile (minimum
`-0.4060` for paging,
`-0.3080` for scheduling). The
generated errors are therefore uniformly gentler than a real predictor's errors wherever the reach
row is zero, and the cell supports a claim about **ordering** there and none about magnitude.

That asymmetry is itself informative: it locates the interface between an error generator and
predictor-like errors, which is the quantity the learned-systems literature reports from the other
end — end-to-end deltas against a strong baseline, with no prediction-error measure on the horizontal
axis [75] [74] [77] [4] [37]
[3]. Read as limits **L3** and **L4**, the cell is a sign-level anchor, not a
reproduction: no unit conversion is attempted or claimed.

### 4.4 What worst-case calibration costs, and which coordinate it reacts to

The fourth result prices the field's standard calibration rule for the blend parameter. The rule
evaluated here is the worst-case choice the consistency–robustness literature states
[6] [51] [23], and the measured object is its cost relative
to the profile's own best blend setting, per profile, in cluster units.

| problem | median factor | worst profile's factor | 95% between-stream interval | profiles where the certificate's blend differs | Pearson r (tail, factor) |
|---|---|---|---|---|---|
| `ski` | `1.701` | `1.751` | `[1.738, 1.765]` | `11` of 12 | `0.166` |
| `sched` | `1.285` | `1.457` | `[1.444, 1.470]` | `8` of 12 | `0.301` |
| `paging` | `1.493` | `1.825` | `[1.811, 1.840]` | `11` of 12 | `0.390` |

**Table 2.** The cost of the worst-case calibration rule, per problem, over the 12 non-zero profiles
of the declared set (the `zero` profile has no error to calibrate against). *Factor* is the
certificate rule's realized ratio divided by the profile's own best blend setting's, so a factor of
1.0 means the worst-case choice was already optimal. The interval is over streams. The last column is
the correlation between the factor and the profile's tail coordinate.

Three further readings belong with the table, and one of them does **not** confirm the prior:

* The certificate's blend setting is an **endpoint** on every problem — the rule is bang-bang here —
  and it differs from the profile's own best setting on
  `11`, `8`
  and `11` of the 12 profiles respectively, so the cost
  is not an artefact of one profile.
* The factor does not rest on choosing the blend setting on the streams it is scored on: refitting
  the setting out of sample leaves the worst profile's factor at 1.7030 for ski (in-sample
  `1.751`), 1.2838 for scheduling and 1.4517 for paging.
* The registered prior said the loss tracks the **tail** of the spread rather than its mean. The
  measured correlations are `0.166` for ski,
  `0.301` for scheduling and
  `0.390` for paging: positive in all three problems,
  and too small in all three to carry the claim on its own. Profiles with no tail show a mean factor
  of `1.54` /
  `1.25` /
  `1.38` (ski/sched/paging) against
  `1.69` /
  `1.40` /
  `1.76` for the two profiles that have a tail:
  the direction the prior predicted is present, and the magnitude is not what the prior implied.
  Section 7 reports this prior as *partially confirmed*, not as confirmed.

Finally, the factor is reported as a **ratio of means** as well as as a median
(`1.700` /
`1.285` /
`1.486` for ski/sched/paging), because a
median of per-profile ratios and a ratio of means are different statistics and the registered
criterion initially named only the first. The two agree to three decimals here; the pair is reported
so that a reader who wants the aggregate-level statement has it.

### 4.5 The registered criteria, one by one

The registration fixed four success criteria before the deciding runs. Reported against the
committed artefacts, with no pooling across problems:

| criterion | state | what it returned |
|---|---|---|
| (a) the signed decomposition beats the scalar `|error|` on held-out cells | `measured` | resolved for scheduling; did not resolve for ski rental or paging under this design, where the constructive witness (§4.1) carries the claim instead |
| (b) the classic anchors are recovered | `measured` | the known competitive ratios are reproduced at both ends of the error range |
| (c) the cost of worst-case calibration is measured | `measured` | a factor per problem, with a between-stream interval and an out-of-sample check on the blend setting it uses (§4.4) |
| (d) the streams are independent and the result is sensitive to them | `measured` | reported per problem, with the flip analysis, in §4.6 |

**Table 3.** The four registered success criteria, each with its state in the committed artefact and
what it returned. Criterion (a) is reported per problem because the criterion is a comparison, and a
comparison that resolves in one problem and not the others is not a single verdict.

### 4.6 Streams, the unit of inference, and the sensitivity bound the reader is owed

Each cell is measured over `16` replicate streams, and every verdict above is quoted in
cluster units (§3.4), so the robustness question is not whether the numbers move but whether the
**verdicts** move. Two things are measured, and one is owed:

* **Disjoint streams.** Every cell's streams are its own: no stream is reused across cells, so a
  verdict that holds in two cells is not one measurement counted twice. The registration's fourth
  success criterion is this property, and it is reported as
  `measured` in Table 3.
* **Interval over streams.** Where a factor is reported (Table 2), its interval is the between-stream
  interval at the cluster unit, and the out-of-sample refit in §4.4 is the check that the factor does
  not depend on choosing the blend setting on the streams it is scored on. The witness of §4.1 needs
  no such check: an identity plus a gap that clears its own resolution in
  `31` of `39`
  blocks does not depend on which streams are drawn.
* **The flip bound, stated as owed rather than as read.** The criterion's own wording promises a
  *flip count* per headline number — how many streams would have to change for the verdict to
  reverse — and that count is **not yet computed**. It is listed in §5 with the other open item, and
  until it exists this paper does not claim a sensitivity margin it has not measured. The three
  results that stand on a contrast rather than on an identity are the ones it will have to cover.

