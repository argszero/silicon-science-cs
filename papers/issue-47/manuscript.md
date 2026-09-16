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
third contrast is **not resolved** at this design's resolution, a limit of this result rather
than the outcome of a registered prior (the priors' outcomes are stated below and in Section 7), so
it is reported rather than rounded into a claim. **(3) A published systems-level
ordering survives contact with this harness in sign, not in magnitude:** the external anchor reports
a concordant pair (larger mean gain, smaller worst-trace degradation), and the harness reproduces
the *sign* of that concordance in all three problems — Kendall tau
`0.744` / `0.889` /
`1.000` — while reaching the published *magnitude* in one
problem only. **(4) Calibrating the trade-off parameter by the worst-case rule costs a measurable
factor on this instrument's generated profiles:** the median factor is
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
and the problem-structured-sign prior is **refuted**: the registration fixed the verdict rule in
advance, and the measured dominant sign for paging is the opposite of the registered one, with the
measured direction uniform across the design (Section 7). Six frozen limits travel with the claims — an attachment that is
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
  coordinate census are shipped as procedures, and the registered priors are reported one by one
  against the verdict rules the registration fixed in advance — including the one it refutes, and the
  mechanism that refutation leaves unresolved (Sections 5–7).

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
* **Paging** (`paging`) — evict-on-full with a cache. The offline optimum is Belady's, computable
  exactly for every trace, and the classical analyses of paging are stated against it
  [62] [63] [66]; the problem is the one the learning-augmented caching
  literature is built on [2] [11] [12] [13].
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
[141] [142] [143]. Paired units share the error generator, the
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
  is usually stated as an intention [144] [145] [146];
  here it is a reading, and its own limits are reported with it [147] [68].

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
[8] [9] [92] [94], while on the objective side the loss
literature says the same thing about what a learner minimises: the loss must carry the *direction* of
the cost, not its magnitude
[103] [101] [102] [105] [104]. The
instrument says which half of the error a loss is reacting to, and §4.4 prices the consequence.

### 4.3 A published ordering survives contact with the harness, in sign

The external cell takes one published system result [10] and asks whether this instrument
reproduces the *ordering* of its reported pair. The published pair is concordant: the cache with the
larger mean gain (`26%` over its predecessor, against
`16.7%` for the comparison cache, derived as a
ratio in the artefact rather than asserted) is also the one with the smaller worst-trace degradation
over the non-learned baseline (0.8% against 8.8%). Ranking the harness's own
78-pair grid of 13 profiles by mean gain and by
the best unit's tail, the concordance holds in all three problems — Kendall's tau
`0.744` for ski, `0.889` for
paging and `1.000` for scheduling — and it still holds when the
zero-error anchor, which is extreme on both axes by construction, is dropped:
`0.697` /
`0.873` /
`1.000`.

**A tau is a ratio, so the counts behind it travel with it.** Each problem ranks
78 pairs; the disagreeing ones number
`10` (ski),
`4` (paging) and
`0` (scheduling), and the pairs tied on one axis — which
the stage's tau drops from numerator and denominator alike — are
`6` in paging and none elsewhere. The weakest reading is
ski's, and its source is stated rather than left to be inferred: it is carried by
`10` of 78 pairs
disagreeing, **not** by a coarse ranking — dropping the anchor leaves
66 pairs and moves the tau by less than the interval's
width (`0.697` against
`0.744`), the anchor itself being concordant against
`12` others. The interval is the stage's
**profile-level bootstrap** — the profiles resampled with replacement
2000 times from seed
31, 2.5/97.5 percentiles, re-run in the canonical runner
rather than quoted from the artefact — so it measures how much the ordering read depends on *which
profiles the grid happens to contain*, not unit-level sampling error: ski
[`0.420`, `1.000`], paging
[`0.667`, `1.000`],
scheduling [`1.000`,
`1.000`]. No lower bound crosses zero, so the **sign-level**
concordance survives the grid-dependence the interval quantifies; the **magnitude** of the agreement
does not, which is what the reach row below then bounds.

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
axis [75] [74] [77] [4]
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

### 4.6 Streams, the unit of inference, and the flip bound per headline number

Each cell is measured over `16` replicate streams, and every verdict above is quoted in
cluster units (§3.4), so the robustness question is not whether the numbers move but whether the
**verdicts** move. Three things are measured:

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
* **The flip bound, per headline number.** The criterion's wording promises a *flip count* — how
  many of the observations a number rests on would have to change for its verdict to reverse. It is
  computed over the committed stage artefacts (`flip_bound_v1.py`), one unit at a time: the unit is
  the smallest observation the producing stage records, a unit is *inverted* by giving its
  contribution the mirror value, and inversions are applied strongest-support-first, so each count
  below is the **fewest** changes that could reverse that verdict — the number a reader can rely on,
  since the verdict survives any change to fewer units. Two distinctions are part of the reading, and
  both are reported rather than assumed:

  * **Direction.** A verdict that asserts an effect is falsified by evidence against it, and gets an
    inversion count. A verdict that asserts an *absence* — a limit, a "not resolved" — cannot be
    reversed by inversions at all, because only *more* support moves it across; for those the margin
    is the distance to the decision boundary, and no inversion count is invented. The sign-channel
    result is both at once: it asserts an effect for scheduling
    (`25` cluster inversions reverse it), and asserts an
    *absence* for paging and
    ski rental, whose margins are the
    `0.5206` and
    `1.0335` cluster MDEs they sit below the bar.
  * **Exactness.** Where the stage records the units individually the bound is exact; where it keeps
    only an aggregate (a cluster mean with its interval) the bound is an estimate under a stated
    equal-magnitude assumption, and the artefact says which is which. The specificity control (§4.5)
    is the case where the bound is **not derivable** at all from the committed artefact — the per-unit
    rows behind its aggregate were never recorded — and it is reported that way rather than estimated
    into a number.

  **What the bound buys, and the one place it changes the paper's emphasis.** The witness of §4.1 has
  two forms, and they are not equally robust. Its **count form** — the sign channel clears its own
  resolution in `31` of
  `39` blocks — needs
  `12` block inversions to reverse, and inverting a block's
  median takes more than half of that block's paired observations
  (`9 of 16`), so the count form resists any change
  to fewer than `108` paired observations.
  Its **aggregate-interval form** needs `2` blocks —
  `18` paired observations — because
  the aggregate's interval is tight and two well-placed blocks erase it. The identity leg is stronger still: the
  scalar-feature gap is exactly zero in every block, and no change to the streams can move a quantity
  that is zero by construction, so it has no flip bound at all. The paper therefore reports the
  identity and the count as the load-bearing evidence for the witness and treats the aggregate
  interval as the weaker statement it is — which is what a flip bound is for. The external ordering
  (§4.3) carries the largest margins on this instrument
  (`39` / `32` /
  `29` pair inversions for scheduling, paging and ski rental), and
  the external *reach* statement is the weakest headline in the paper by this measure: no profile
  reaches the published robustness scale, and a single profile would (`L3`), which is why the excluded
  profiles are listed one by one in §4.3 rather than summarised.


## 5. The limits, each with the measurement that establishes it

A limit is stated here as a measurement rather than an apology. Each was found by running the
instrument, and each was declared before this manuscript was written.

**L1 — the paging attachment is model-dependent.** Two attachments are possible, and they are not the
same experiment (Section 3.3). The step-common attachment is blind to positive errors and reproduces
the zero-error cost exactly, while the per-page attachment differs on the same information. Both
relations are measured, and the third is the trap: a positive *bias* is not a non-negative
*multiplier*. **Consequence:** every statement this paper makes about positive-bias predictions in
paging is a statement about the per-page attachment. **Why it does not sink the paper:** the
attachment is declared, the alternative is measured against it, and the paging result is reported as
unresolved anyway — so no claim in this paper rests on the attachment being canonical.

**L2 — the null of the object-level design is shifted, so negative verdicts are uninterpretable.**
Under a synthetic even target with no sign dependence, the odd parameter is penalised by
`-12.95` / `-13.12` /
`-1.53` cluster MDEs (ski / sched / paging). A design that
punishes its own odd term under a sign-free target cannot read a negative as evidence. **Consequence:
only the positive resolutions are reported as evidence, and the unmatched-form reading is retired.
Why it does not sink the paper:** the surviving verdicts are the conservative ones — a positive result
obtained against a null that is shifted *against* it is a lower bound on the effect, and the paper
says so in the result itself rather than in a footnote.

**L3 — unit reach is uneven, and the external cell says where.** Against the published robustness
scale (a 0.8–8.8% worst-trace degradation), the harness reaches that scale in ski rental
(`12` of
`13` profiles at or above 0.8%,
`11` at or above 8.8%) and in **neither** paging
nor scheduling (`0` and
`0` of 13; the harness's worst unit is better
than the non-learned baseline at every profile there, minima
`-0.4060` and
`-0.3080`). **Consequence:** the cell
supports a claim about ordering in all three problems and about magnitude in one. **Why it does not
sink the paper:** the reach row is reported as a measurement rather than gated, so a reader knows
exactly which of the two claims each problem carries; and the asymmetry itself is informative — it
locates the interface between an error generator and predictor-like errors.

**L4 — concordance is rank agreement, not a magnitude match.** No unit conversion between the
harness's ratios and the published cache's miss ratios is attempted or claimed. **Consequence:** the
external cell is a sign-level anchor. **Why it does not sink the paper:** the claim made from it is
the one the measurement supports — the *ordering* — and the derived comparison figure (`1.26/1.08-1`)
is written into the artefact as a derivation rather than presented as a transcription.

**L5 — the generalising unit is the profile, not the repeated measurement.** Measured: an MDE computed
over paired units that share the error generator, implementation and fit was optimistic by 3.7–6.3×.
**Consequence:** every resolution verdict quotes the cluster unit `(profile, replicate)`, and the
tightest resolution quoted anywhere in this paper is `0.0187`.
**Why it does not sink the paper:** the correction moves the verdicts in the conservative direction
and is itself one of the paper's method contributions (Section 1.3, C5) — the instrument was corrected
by its own controls.

**L6 — a synthetic harness with one real anchor.** All losses come from this paper's generators; the
external cell anchors ordering against a published system and is not a reproduction of it.
**Consequence:** the paper's claims are about the relationship between prediction-error structure and
realized loss *in this harness*, with the published anchor carrying the sign of that relationship into
the literature. **Why it does not sink the paper:** the counterfactual is exact by construction — the
offline optimum is computable for every instance — which is precisely what a measured-live-system
study cannot have; the harness buys ground truth at the price of realism, and the price is stated.

**The sensitivity margin is measured, and its limits are stated.** The registration's fourth success
criterion names a flip-count bound per headline number, and it is computed per unit in §4.6 — with two
limits that belong here rather than there: where a headline rests on a number the stage recorded only
as an aggregate, the bound is an *estimate* under a stated equal-magnitude assumption (exact bounds
are reported for the block-level, pair-level and threshold-count headlines, which the stage records
unit by unit); and for the specificity control no bound in units is derivable at all from the
committed artefact, which is stated instead of estimated. A sensitivity margin is only as good as the
units the stage kept.

## 6. Methodology, and how to reproduce it

### 6.1 The methodological stance, and what this paper takes from the evaluation literature

The instrument is built on four methodological commitments, each borrowed from a literature that
already argues for it, and each applied here to a simulation rather than to a deployed system.

* **A simulation is designed, not repeated arbitrarily.** The profile grid is declared before any run
  and used unchanged by every result, so a cell's meaning is fixed by construction [148]
  — versus growing the number of replicates until a verdict appears — and where replication is carried
  out at scale it needs a framework of its own rather than more repetitions [149].
* **A resolution is quoted, not assumed.** Every verdict is stated in cluster-unit minimum detectable
  effects [141] [142] [143], so "the design can see this" is a number rather
  than a hope.
* **Reproducibility is a reading, not an intention.** The apparatus is checked rather than promised:
  one command, byte-identical output, and a published digest block [144]
  [145] [146]; and what an independent re-run can and cannot establish is
  part of the claim [150] [147].
* **A replication's result is not self-authenticating.** The literature on replications is a warning
  that a repeated measurement can misread its own remit [151] [152]
  [153] [154], and the same field argues that reproducibility and
  benchmarking practice need explicit machinery rather than good intentions [155]
  [156], which is why every stage of this package recomputes its numbers from the primitives
  and a liveness control requires each recomputation to be able to fail (below).

**Specific difference.** That literature studies replications of *published* systems and analyses,
usually in software engineering; this paper applies the same disciplines to a measurement instrument
it builds itself, on a theory problem, and it publishes the two things that literature asks for and
rarely gets — a resolution unit and a liveness control — as committed machinery rather than as
guidance.

### 6.2 The package: one command, and what it recomputes

`bash reproduce.sh` runs the whole package on one CPU core with the Python standard library and **no
network**, and exits non-zero unless every step passes. It has seven steps: (1) `8`
stages plus the canonical aggregate, which **recomputes** every cited number from the stage artefacts'
primitives and cross-checks it against the value each stage recorded about itself
(`113` facts, 0 disagreements when this was written); (2) the aggregate's liveness control,
which corrupts each recomputation in a throwaway copy and requires it to notice; (3) the external
cell's own check-liveness, 13 mutations, one per named check, each of which must make exactly that
check fail; (4) the design-freeze document checked against the artefacts, 46 checks including the
digest table; (5) the manuscript assembly, which resolves every measurement placeholder out of the
artefacts and fails on an unresolvable one or a citation key with no reference entry; (6) the
**support limb** of citation integrity (Section 6.3); and (7) the digest block.

Two further properties are reported rather than assumed. The **coordinate census** scans the package
for hidden inputs the authoring machine supplies silently: it reports
`0` violations over the classes it declares, with 8 of 8 detectors
firing on a planted instance — and it reports the classes where the package *does* read the outside
world (its own directory, the manuscript parts one level above the package, and the interpreter),
because a census that printed only its zeroes would be a census of one direction. The **run
environment** is recorded with the run: the package is deterministic (no clock, no entropy, no
socket), and two full runs to byte-identical logs are the check.

### 6.3 The two relations of a citation, and the one this paper had to build

A citation owes two relations, and they are read in different places. **Identity** — the record is the
work the entry names — is read in the list, by comparing the returned year, venue and authors against
the entry's own line; every entry's record was resolved against Crossref or arXiv and the report is
`reference-check.md`. **Support** — that work is the work the claim at the key needs — is read in the
text, and no step of this pipeline read it until this paper built one.

The support limb is read per **occurrence**, not per key: the `113`-fact aggregate is not a
citation, and the manuscript's 39 blocks are not references either,
but of the cited keys 51 appear in more than one sentence, and a per-key read would hide the
occurrence that fails. Each occurrence is recorded against the sentence it sits in, with the role the
key plays there (a bound source, a survey, an instance of the enumerated class, the published anchor,
…), and the check fails on a missing read, on an edit that leaves a recorded sentence no longer in the
text, and on an occurrence marked unsupported. The read found four occurrences in this manuscript's
own draft where the work could not carry its sentence — a source for the exactness of an offline
optimum that was three competitive analyses; a structural-equation sample-size app cited for
cluster-level resolution; five asymmetric-loss papers cited for a claim about guarantees; and a
theory bound listed among systems measurements. All four were corrected, and all four are kept on the
record in `support-read.md`: a corrected finding that leaves no trace is indistinguishable from one
that was never made.

**Specific difference.** The citation-integrity literature and the journal's own bar both read the
list; the relation that a *sentence* depends on is usually left to the author's judgement with no
record of what was judged. This paper makes the second relation a mechanism: the quote is what binds
a verdict to a sentence, so an edit anywhere in the text either moves nothing (if it is not a cited
sentence) or is reported as the pair it is.

### 6.4 Threats to validity, and why this is still worth publishing

Four things could make the paper wrong, and each is bounded rather than waved away.

1. **The harness is synthetic (L6).** Its realism is anchored at one point — the sign of a published
   system's ordering — and the anchor's own reach is measured and reported as uneven (L3). The
   counterfactual is exact by construction, which no live measurement of this quantity has. A reader
   who wants live numbers gets none here; a reader who wants the *structure* of the loss gets a
   ground-truth instrument, and the two are complements rather than substitutes.
2. **The object-level design is weak by construction (L2, L5).** Its null is shifted against the
   hypothesis, and the resolution unit was corrected upward by 3.7–6.3×. Both move the paper's
   verdicts in the conservative direction: the reported resolutions are what survived a design that
   is biased *against* reporting them. That is also why the headline does not rest on the object-level
   test — it rests on a constructive identity (Section 4.1), which no test resolution can overturn.
3. **The scope is three problems and one profile family.** The profile grid moves mean, spread and
   tail independently, but the real predictor-error structures of deployed systems are not enumerated
   here. The claims are stated per problem throughout and never pooled, so a reader can see which of
   them rests on one problem's cell and which on three.
4. **One anchor, one derived comparison figure (L4).** The external cell reproduces the *ordering* of
   one published pair. The concordance could be a property of the harness rather than of caching; the
   paper's response is to make the reach row a measurement and to report the rank agreement without a
   magnitude claim.

Against these: the paper's first claim is not a statistical result but an identity — two arms with the
same multiset of `|error|` whose realized losses differ by up to
`-0.568` competitive-ratio units — and its fourth claim prices the
field's standard calibration rule in the currency a deployer uses, with a between-stream interval and
an out-of-sample check on the parameter it accuses. Both survive the limits above, and neither was
available before this instrument.

## 7. The registered priors, and what happened to each

The registration stated three prior beliefs, with directions and justifications, before any deciding
run. Each is reported here with its outcome, and the criteria the registration fixed are reported in
Section 4.5.

**P1 — the realized loss is signed-asymmetric, so `|error|` is not a sufficient statistic.
Outcome: confirmed, and more strongly than predicted.** The registration's falsification condition was
that the scalar regression match the decomposition on held-out cells. It does not: the constructive
witness (§4.1) is an identity, not a comparison — identical scalar features by construction, losses
that differ by up to `-0.568` competitive-ratio units against a
cluster MDE of `0.0187`. The registered *predictive* clause — that
the decomposition explains held-out loss better — resolved in one of three problems at the clean
object-level design (§4.2), which is weaker than the witness and is reported as such.

**P2 — the worst-case calibration costs a measurable factor, and the loss tracks the spread's tail
rather than its mean. Outcome: the first half confirmed, the second half only partially.**
The factor is measured: a median of `1.701` /
`1.285` /
`1.493` (ski / sched / paging), with the worst
profile's factor at `1.751` /
`1.457` / `1.825`
and a 95% between-stream interval that stays away from 1. The direction the prior predicted — the
tail, not the mean — is present in all three problems (the two tail profiles carry the higher mean
factor, `1.69` /
`1.40` /
`1.76` against
`1.54` /
`1.25` /
`1.38`), and the *magnitude* the prior implied is
not: the correlations are `0.166`,
`0.301` and
`0.390`, and the relation is non-monotone in spread —
in ski rental the extreme-spread profiles carry the *lowest* factor. Reported as **partially
confirmed**: the direction stands, the mechanism sentence does not.

**P3 — which sign is priced is problem-structured. Outcome: refuted, and the refutation is
informative.** The registration predicted that paging prices over-prediction and ski rental
under-prediction, stable across algorithms within a problem. Measured: **under-prediction is the worse
arm in all three problems**, and the direction is uniform rather than marginal — in every block that
separates the two arms at all, the over-predicting arm is the better one:
`12` of `12`
blocks for ski rental, `7` of
`7` for paging, and
`12` of
`12` for scheduling. For paging that is the
opposite of the registered prediction, and the registration fixed the verdict rule in advance — "if
the coefficients' signs differ across algorithms within one problem, or the measured dominant sign is
the opposite of the above for a stated problem, P3 is refuted" — so the clause is met for a stated
problem, and the prior is **refuted on the registration's own terms** rather than on a reading chosen
afterwards. The prior was anchored on a mechanism (act early versus defer) that would make the sign
follow the problem; the measurement says the sign follows something the mechanism did not name. That
is a genuine contradiction of a theory-anchored prior, and it is reported as the paper's most
surprising single result rather than buried: a statement of the form "this problem prices that sign"
cannot be inferred from the shape of the decision alone.

**What the refutation does not establish, stated so the two are not conflated.** The uniform direction
has at least two readings, and this design does not separate them: the sign may follow the harness's own
cost structure — the same asymmetric cost form is used in all three problems — or the three problems may
share a dominant sign for a reason the prior did not name. The first reading is measurable rather than
rhetorical: §3.5's shifted null is that structure's own pull, measured at
`-12.95` / `-13.12`
/ `-1.53` cluster MDEs under a sign-free target. The ambiguity is
about the **cause** — which mechanism produces the uniform direction — and it is a limit (**L2**, and the
synthetic-harness limit **L6**), not a rescue of the prediction: on both readings, the registered claim
that the dominant sign is *problem-structured* is not what the instrument observed, and the falsification
clause the registration wrote is met. What the design cannot do is say what *does* determine the sign;
the prior's mechanism cannot be repaired here by re-reading the same cells, and a design that varies the
cost structure while holding the problem fixed is named as future work rather than claimed as this
paper's result.

**On reporting a refutation.** A prior whose falsification condition was met is the strongest
available evidence that the instrument can fail — the paper is not only confirming its own beliefs.
The refuted prior (P3) and the partially confirmed one (P2) are the two places where this work changed
what its author believed going in, and both are stated in the abstract.

## 8. Conclusion

The question this paper set out to answer was what a prediction buys — not what it guarantees in the
worst case, but what the loss actually is as a function of *which way* the prediction is wrong. The
answer has four parts, and the first is an identity rather than a statistic: two arms with the same
scalar error statistics, differing only in sign, realize losses that differ by up to
`-0.568` competitive-ratio units — above the resolution of their
own block in `31` of
`39` blocks. `|error|` is therefore not the object the field's
guarantees should be stated over; a decomposition into signed components is.

The second part is where the instrument can resolve and what happens there: the sign channel carries
information beyond the scalar when the design is matched in form, in
`measured` form for scheduling and as an
object-level contrast for ski rental, with paging reported unresolved rather than as a small effect.
The third is a published system ordering reproduced in sign, with the cell's own reach reported as a
limit instead of hidden as a success. The fourth prices the field's standard worst-case calibration:
a factor of `1.70`–`1.29`
per problem in the typical case, with the parameter the rule chooses differing from the profile's own
best on most profiles and the factor surviving an out-of-sample refit.

What a reader should take away is not a number but a change of object. A consistency bound written in
`eta` or `|error|` is a statement about the magnitude of an error; the measurement here says the loss
is governed by its direction, and that the direction is not the direction the literature's mechanism
arguments predict. A deployer's next unit of effort — spend it on the predictor or on the fallback —
is a question about a signed quantity, and this paper supplies the instrument that prices it, together
with the limits under which that price holds.

## References

[1] Mitzenmacher, M.; Vassilvitskii, S. *Algorithms with Predictions*. Beyond the Worst-Case Analysis of Algorithms, 2020. `10.1017/9781108637435.037` https://doi.org/10.1017/9781108637435.037 - Difference from this work: framed the interpolation between the online and the offline optimum; the interpolation is in error MAGNITUDE, and this paper reads the same frontier channel by channel
[2] Lykouris, T.; Vassilvitskii, S. *Competitive Caching with Machine Learned Advice*. Journal of the ACM, 2021. `10.1145/3447579` https://doi.org/10.1145/3447579 - Difference from this work: the canonical blend, with the guarantee stated in the prediction error's magnitude; the direction of that error never appears in it
[3] Feng, Y.; Yang, Z.; Zhang, Y. *Competitive Non-Clairvoyant KV-Cache Scheduling for LLM Inference*. arXiv preprint, 2026. `arXiv:2601.22996v1` https://arxiv.org/abs/2601.22996v1 - Difference from this work: schedules a KV cache competitively for LLM inference: the same algorithmic family on a new workload, with no signed-error measurement
[4] Zhou, W.; Wang, Q. *An Efficient Cache Eviction Strategy based on Learning and Belady Algorithm*. 2023 IEEE 12th International Conference on Cloud Networking (CloudNet), 2023. `10.1109/cloudnet59005.2023.10490040` https://doi.org/10.1109/cloudnet59005.2023.10490040 - Difference from this work: learns an eviction strategy against Belady's rule: an applied learned policy, again without a signed-error account
[5] Zhao, H.; Tang, X.; Chen, P.; et al. *Learning-Augmented Algorithms: Guarantees, Construction Mechanisms, and System-Level Implications*. arXiv preprint, 2026. `arXiv:2609.04787v2` https://arxiv.org/abs/2609.04787v2 - Difference from this work: the field's own survey separates formal guarantees from systems evidence and names the benchmarks -- it states the gap this paper fills, and reports no measurement
[6] Wei, A.; Zhang, F. *Optimal Robustness-Consistency Trade-offs for Learning-Augmented Online Algorithms*. arXiv preprint, 2020. `arXiv:2010.11443v1` https://arxiv.org/abs/2010.11443v1 - Difference from this work: proved the optimal robustness-consistency trade-off curve for a class of one-dimensional problems: the frontier this paper measures, DERIVED for that class, with a symmetric error model
[7] Shen, J. H.; Vitercik, E.; Wikum, A. *Algorithms with Calibrated Machine Learning Predictions*. arXiv preprint, 2025. `arXiv:2502.02861v4` https://arxiv.org/abs/2502.02861v4 - Difference from this work: replaces the worst-case error with a calibration condition -- a sharper way to bound error, still one number
[8] Elmachtoub, A. N.; Grigas, P. *Smart "Predict, then Optimize"*. arXiv preprint, 2017. `arXiv:1710.08005v5` https://arxiv.org/abs/1710.08005v5 - Difference from this work: introduced the smart predict-then-optimize formulation: regret is in the prediction error's magnitude, and the loss is trained rather than decomposed
[9] Vanderschueren, T.; Verdonck, T.; Baesens, B.; et al. *Predict-then-optimize or predict-and-optimize? An empirical evaluation of cost-sensitive learning strategies*. Information Sciences, 2022. `10.1016/j.ins.2022.02.021` https://doi.org/10.1016/j.ins.2022.02.021 - Difference from this work: empirically compares predict-then-optimize against predict-and-optimize: a comparison of frameworks, in which no online ratio is involved
[10] Xia, H.; Nixon, W.; Marthen, B. D.; et al. *Learning-Augmented Heuristics: Simple, yet Smart, Robust and Interpretable Cache Eviction*. arXiv preprint, 2026. `arXiv:2608.27975v1` https://arxiv.org/abs/2608.27975v1 - Difference from this work: the published cache-eviction result this paper's external cell is anchored to: it reports a concordant PAIR -- a larger mean gain over the classical rule -- and a mean is silent about which direction of error produced it
[11] Rohatgi, D. *Near-Optimal Bounds for Online Caching with Machine Learned Advice*. arXiv preprint, 2019. `arXiv:1910.12172v2` https://arxiv.org/abs/1910.12172v2 - Difference from this work: near-optimal caching bounds under a stated error eta -- one symbol for error, so the two directions are pooled by construction
[12] Bansal, N.; Coester, C.; Kumar, R.; et al. *Learning-Augmented Weighted Paging*. arXiv preprint, 2020. `arXiv:2011.09076v2` https://arxiv.org/abs/2011.09076v2 - Difference from this work: extended the caching guarantee to weighted paging through the error's magnitude; this paper asks what the SIGN of that same error does
[13] Jiang, Z.; Panigrahi, D.; Sun, K. *Online Algorithms for Weighted Paging with Predictions*. arXiv preprint, 2020. `arXiv:2006.09509v1` https://arxiv.org/abs/2006.09509v1 - Difference from this work: weighted-paging bounds under a prediction, with the error entering symmetrically by construction
[14] Wei, A. *Better and Simpler Learning-Augmented Online Caching*. arXiv preprint, 2020. `arXiv:2005.13716v1` https://arxiv.org/abs/2005.13716v1 - Difference from this work: a better and simpler learning-augmented caching rule; a rule, with the same magnitude-only dependence on the error
[15] Dinitz, M.; Im, S.; Lavastida, T.; et al. *Algorithms with Prediction Portfolios*. arXiv preprint, 2022. `arXiv:2210.12438v2` https://arxiv.org/abs/2210.12438v2 - Difference from this work: a portfolio of predictors hedges WHICH predictor is wrong, not which direction it is wrong in
[16] Anand, K.; Ge, R.; Kumar, A.; et al. *Online Algorithms with Multiple Predictions*. arXiv preprint, 2022. `arXiv:2205.03921v3` https://arxiv.org/abs/2205.03921v3 - Difference from this work: treats several predictions as confidence ratings: several magnitudes, with no result separating a sign from a magnitude
[17] Kodialam, R. *Optimal Algorithms for Ski Rental with Soft Machine-Learned Predictions*. arXiv preprint, 2019. `arXiv:1903.00092v2` https://arxiv.org/abs/1903.00092v2 - Difference from this work: replaces binary advice with a confidence in the soft-prediction model: confidence is a magnitude, and no channel is divided
[18] Antoniadis, A.; Coester, C.; Eliáš, M.; et al. *Mixing predictions for online metric algorithms*. arXiv preprint, 2023. `arXiv:2304.01781v2` https://arxiv.org/abs/2304.01781v2 - Difference from this work: mixing several predictors is a way to hedge error MAGNITUDE; nothing here asks which DIRECTION of error each predictor contributes
[19] Coester, C.; Tudose, A.; Turoczy, A. *Learning-Augmented Online Minimization with Dual Predictions*. arXiv preprint, 2026. `arXiv:2606.05380v1` https://arxiv.org/abs/2606.05380v1 - Difference from this work: adds a second channel in the dual model -- a second PREDICTION, where this paper's second channel is the error's sign
[20] Khodak, M.; Balcan, M. F.; Talwalkar, A.; et al. *Learning Predictions for Algorithms with Predictions*. arXiv preprint, 2022. `arXiv:2202.09312v2` https://arxiv.org/abs/2202.09312v2 - Difference from this work: learns the prediction to minimise the downstream ratio -- training the predictor, where this paper measures the value of a given one
[21] Sun, B.; Huang, J.; Christianson, N.; et al. *Online Algorithms with Uncertainty-Quantified Predictions*. arXiv preprint, 2023. `arXiv:2310.11558v2` https://arxiv.org/abs/2310.11558v2 - Difference from this work: quantifies the prediction's own uncertainty: uncertainty about magnitude, with the guarantee staying in magnitude
[22] Gupta, A.; Panigrahi, D.; Subercaseaux, B.; et al. *Augmenting Online Algorithms with e-Accurate Predictions*. Advances in Neural Information Processing Systems 35, 2022. `10.52202/068431-0154` https://doi.org/10.52202/068431-0154 - Difference from this work: assumes an epsilon-accurate prediction: a single accuracy parameter, so both error directions share one symbol by construction
[23] Li, S.; Christianson, N.; Li, T. *Prediction-Specific Design of Learning-Augmented Algorithms*. arXiv preprint, 2025. `arXiv:2510.14887v1` https://arxiv.org/abs/2510.14887v1 - Difference from this work: designs the algorithm around the prediction's own error measure -- the closest relative to this paper's construct; the measure is chosen per problem and enters as a magnitude, and the two directions are never separated
[24] Fotakis, D.; Gergatsouli, E.; Gouleakis, T.; et al. *Improved Bounds for Online Facility Location with Predictions*. arXiv preprint, 2021. `arXiv:2107.08277v4` https://arxiv.org/abs/2107.08277v4 - Difference from this work: improved facility-location bounds with predictions: the bound is in the error, and consistency-robustness is not the object of study
[25] Angelopoulos, S.; Arsenio, D.; Kamali, S. *Competitive Sequencing with Query Predictions*. Elsevier BV, 2024. `10.2139/ssrn.4975891` https://doi.org/10.2139/ssrn.4975891 - Difference from this work: sequencing with query predictions -- the prediction buys queries; this paper asks what a numerical prediction buys in ratio terms
[26] Lavastida, T.; Moseley, B.; Ravi, R.; et al. *Learnable and Instance-Robust Predictions for Online Matching, Flows and Load Balancing*. arXiv preprint, 2020. `arXiv:2011.11743v2` https://arxiv.org/abs/2011.11743v2 - Difference from this work: makes predictions learnable and instance-robust for matching and load balancing: robust against the INSTANCE, not against a signed error
[27] Lassota, A.; Lindermayr, A.; Megow, N.; et al. *Minimalistic Predictions to Schedule Jobs with Online Precedence Constraints*. arXiv preprint, 2023. `arXiv:2301.12863v1` https://arxiv.org/abs/2301.12863v1 - Difference from this work: minimalistic predictions for jobs with precedence constraints: another objective with a magnitude-only guarantee
[28] Boyar, J.; Favrholdt, L. M.; Kamali, S.; et al. *Online Interval Scheduling with Predictions*. arXiv preprint, 2023. `arXiv:2302.13701v2` https://arxiv.org/abs/2302.13701v2 - Difference from this work: interval scheduling with predictions: another objective, again with a magnitude-only guarantee
[29] Balkanski, E.; Ou, T.; Stein, C.; et al. *Scheduling with Speed Predictions*. arXiv preprint, 2022. `arXiv:2205.01247v2` https://arxiv.org/abs/2205.01247v2 - Difference from this work: scheduling with speed predictions: the guarantee is in the error's magnitude, and the two directions are not separated
[30] Bampis, E.; Escoffier, B.; Xefteris, M. *Canadian Traveller Problem with Predictions*. arXiv preprint, 2022. `arXiv:2209.11100v1` https://arxiv.org/abs/2209.11100v1 - Difference from this work: the Canadian traveller problem with predictions: a different objective, with the analysis worst-case in the error's magnitude
[31] Azar, Y.; Panigrahi, D.; Touitou, N. *Online Graph Algorithms with Predictions*. arXiv preprint, 2021. `arXiv:2112.11831v1` https://arxiv.org/abs/2112.11831v1 - Difference from this work: extends the framework to online graph problems, with the tradeoff stated as a ratio bound rather than decomposed by the error's sign
[32] Rutten, D.; Mukherjee, D. *Online Capacity Scaling Augmented With Unreliable Machine Learning Predictions*. arXiv preprint, 2021. `arXiv:2101.12160v2` https://arxiv.org/abs/2101.12160v2 - Difference from this work: studies capacity scaling under unreliable predictions: unreliability is modelled as error MAGNITUDE, and no channel is divided
[33] Rutten, D.; Christianson, N.; Mukherjee, D.; et al. *Smoothed Online Optimization with Unreliable Predictions*. arXiv preprint, 2022. `arXiv:2202.03519v2` https://arxiv.org/abs/2202.03519v2 - Difference from this work: analyses smoothed online optimization with unreliable predictions: again the error's magnitude-driven, with no signed channel
[34] Lindermayr, A.; Megow, N. *Permutation Predictions for Non-Clairvoyant Scheduling*. arXiv preprint, 2022. `arXiv:2202.10199v2` https://arxiv.org/abs/2202.10199v2 - Difference from this work: permutation predictions for non-clairvoyant scheduling: the prediction is an ordering, so an error 'sign' is not even defined
[35] Azar, Y.; Leonardi, S.; Touitou, N. *Flow Time Scheduling with Uncertain Processing Time*. arXiv preprint, 2021. `arXiv:2103.05604v1` https://arxiv.org/abs/2103.05604v1 - Difference from this work: bounds flow time under uncertain processing times: uncertainty is a set, not a signed prediction error, so no consistency-robustness curve is measured
[36] Grigorescu, E.; Lin, Y. S.; Song, M. *A Simple Learning-Augmented Algorithm for Online Packing with Concave Objectives*. arXiv preprint, 2024. `arXiv:2406.03574v1` https://arxiv.org/abs/2406.03574v1 - Difference from this work: a simple learning-augmented online packing algorithm: simplicity is the contribution, not an account of what the prediction is worth
[37] Hsieh, W. H.; Liang, Y. C. *Asymptotically Robust Learning-Augmented Algorithms for Preemptive FIFO Buffer Management*. arXiv preprint, 2026. `arXiv:2604.26349v1` https://arxiv.org/abs/2604.26349v1 - Difference from this work: asymptotically robust FIFO buffer management -- a theory bound that is robust TO error, and says nothing about its direction
[38] Chawla, S.; Christou, D. *Online Time-Windows TSP with Predictions*. arXiv preprint, 2023. `arXiv:2304.01958v1` https://arxiv.org/abs/2304.01958v1 - Difference from this work: online time-windows TSP with predictions: a different problem family, and the error enters through a bound rather than a signed channel
[39] Cohen, I. R.; Panigrahi, D. *A General Framework for Learning-Augmented Online Allocation*. arXiv preprint, 2023. `arXiv:2305.18861v1` https://arxiv.org/abs/2305.18861v1 - Difference from this work: a framework covering several online allocation problems at once; the generality is bought by stating the guarantee in the error's magnitude
[40] Komm, D. *Advice Complexity*. Texts in Theoretical Computer Science. An EATCS Series, 2016. `10.1007/978-3-319-42749-2_3` https://doi.org/10.1007/978-3-319-42749-2_3 - Difference from this work: advice complexity bounds the bits a hard problem needs: it prices INFORMATION, not error direction
[41] Boyar, J.; Favrholdt, L. M.; Kudahl, C.; et al. *The Advice Complexity of a Class of Hard Online Problems*. arXiv preprint, 2014. `arXiv:1408.7033v3` https://arxiv.org/abs/1408.7033v3 - Difference from this work: the advice complexity of a class of hard online problems counts advice BITS, the coarsest version of 'what a prediction buys'
[42] Berg, M.; Boyar, J.; Favrholdt, L. M.; et al. *Complexity Classes for Online Problems with and without Predictions*. arXiv preprint, 2024. `arXiv:2406.18265v4` https://arxiv.org/abs/2406.18265v4 - Difference from this work: places prediction-augmented problems in complexity classes -- a decidability result, not a measured tradeoff
[43] Cho, W. H.; Henderson, S.; Shmoys, D. *Scheduling with Predictions*. arXiv preprint, 2022. `arXiv:2212.10433v1` https://arxiv.org/abs/2212.10433v1 - Difference from this work: a survey of scheduling with predictions: it catalogues bounds rather than measuring a tradeoff on one instrument
[44] Mitzenmacher, M.; Shahout, R. *Queueing, Predictions, and LLMs: Challenges and Open Problems*. arXiv preprint, 2025. `arXiv:2503.07545v1` https://arxiv.org/abs/2503.07545v1 - Difference from this work: a queueing note of open problems where predictions and LLM workloads meet; motivating, and no measurement
[45] Mitzenmacher, M. *Scheduling with Predictions and the Price of Misprediction*. arXiv preprint, 2019. `arXiv:1902.00732v2` https://arxiv.org/abs/1902.00732v2 - Difference from this work: prices a misprediction in scheduling -- a price, not a decomposition: the sign of the misprediction is not a variable of that analysis
[46] Mandarapu, M.; Kunkunuru, S. *Caching for Dollars, Not Hits: An Exact Offline Reference for Cloud-Egress Caching and the Crossover That Decides When It Pays*. arXiv preprint, 2026. `arXiv:2606.20539v2` https://arxiv.org/abs/2606.20539v2 - Difference from this work: prices caching in dollars rather than hits: a different currency, and an exact offline reference rather than a measured tradeoff
[47] Gómez-Vargas, N.; Maldonado, S.; Vairetti, C. *A predict-and-optimize approach to profit-driven churn prevention*. arXiv preprint, 2023. `arXiv:2310.07047v2` https://arxiv.org/abs/2310.07047v2 - Difference from this work: a predict-and-optimize application to churn prevention: an applied instance, with no statement about how error direction prices out
[48] Fujiwara, H.; Iwama, K. *Average-Case Competitive Analyses for Ski-Rental Problems*. Algorithmica, 2005. `10.1007/s00453-004-1142-x` https://doi.org/10.1007/s00453-004-1142-x - Difference from this work: average-case competitive analyses for ski rental: the distribution replaces the error, so no prediction is being priced
[49] Lotker, Z.; Patt-Shamir, B.; Rawitz, D. *Rent, Lease or Buy: Randomized Algorithms for Multislope Ski Rental*. arXiv preprint, 2008. `arXiv:0802.2832v1` https://arxiv.org/abs/0802.2832v1 - Difference from this work: randomized multislope ski rental: randomness is the hedge, where this paper prices the prediction's own direction
[50] Shin, Y.; Lee, C.; Lee, G.; et al. *Improved Learning-Augmented Algorithms for the Multi-Option Ski Rental Problem via Best-Possible Competitive Analysis*. arXiv preprint, 2023. `arXiv:2302.06832v1` https://arxiv.org/abs/2302.06832v1 - Difference from this work: improved learning-augmented algorithms for multi-option ski rental: the improvement is in the constants of a magnitude-only bound
[51] Shin, Y.; Lee, C.; An, H. C. *On Optimal Consistency-Robustness Trade-Off for Learning-Augmented Multi-Option Ski Rental*. arXiv preprint, 2023. `arXiv:2312.02547v1` https://arxiv.org/abs/2312.02547v1 - Difference from this work: characterises the optimal consistency-robustness trade-off for multi-option ski rental -- the frontier itself, derived for one problem under a symmetric error model
[52] Kang, B.; Park, H.; Fan, C. *Learning-Augmented Ski Rental with Discrete Distributions: A Bayesian Approach*. arXiv preprint, 2025. `arXiv:2512.07313v1` https://arxiv.org/abs/2512.07313v1 - Difference from this work: a Bayesian treatment of ski rental with discrete distributions: the prior is the object, not a signed prediction error
[53] Cui, Q.; Dinitz, M. *Ski Rental with Distributional Predictions of Unknown Quality*. arXiv preprint, 2026. `arXiv:2602.21104v1` https://arxiv.org/abs/2602.21104v1 - Difference from this work: distributional predictions of unknown quality: quality is a magnitude, and the sign of the deviation is not a variable of the analysis
[54] Kim, J.; Fan, C. *Robust and Consistent Ski Rental with Distributional Advice*. arXiv preprint, 2026. `arXiv:2603.29233v1` https://arxiv.org/abs/2603.29233v1 - Difference from this work: poses and solves distributional advice for ski rental as a robust and consistent threshold problem for ONE problem; this paper measures across three and separates the error's sign
[55] Wang, S.; Li, J.; Wang, S. *Online Algorithms for Multi-shop Ski Rental with Machine Learned Advice*. arXiv preprint, 2020. `arXiv:2002.05808v2` https://arxiv.org/abs/2002.05808v2 - Difference from this work: multi-shop ski rental with machine-learned advice: the advice is consumed as a scalar error
[56] Cui, Q.; Dinitz, M. *Controlling tail risk in two-slope ski rental*. arXiv preprint, 2025. `arXiv:2508.06809v2` https://arxiv.org/abs/2508.06809v2 - Difference from this work: controls tail risk in two-slope ski rental: tail control is worst-case in the error, orthogonal to the direction of a given error
[57] Dinitz, M.; Im, S.; Lavastida, T.; et al. *Controlling Tail Risk in Online Ski-Rental*. arXiv preprint, 2023. `arXiv:2308.05067v1` https://arxiv.org/abs/2308.05067v1 - Difference from this work: controls tail risk in online ski rental: it prices the worst case, and the signed error channel is not opened
[58] Chen, J.; Zhang, J. *A new performance metric for the ski rental problem*. Operations Research Letters, 2026. `10.1016/j.orl.2025.107382` https://doi.org/10.1016/j.orl.2025.107382 - Difference from this work: proposes a new performance METRIC for ski rental: a metric, not a decomposition of one
[59] Antoniadis, A.; Coester, C.; Eliáš, M.; et al. *Learning-Augmented Dynamic Power Management with Multiple States via New Ski Rental Bounds*. arXiv preprint, 2021. `arXiv:2110.13116v1` https://arxiv.org/abs/2110.13116v1 - Difference from this work: reduces dynamic power management to new ski-rental bounds, with the prediction entering as a threshold in magnitude
[60] Zhang, H.; Conitzer, V. *Combinatorial Ski Rental and Online Bipartite Matching*. Proceedings of the 21st ACM Conference on Economics and Computation, 2020. `10.1145/3391403.3399470` https://doi.org/10.1145/3391403.3399470 - Difference from this work: combinatorial ski rental alongside online bipartite matching: two problems, one magnitude-based guarantee
[61] Khanafer, A.; Kodialam, M.; Puttaswamy, K. P. N. *The constrained Ski-Rental problem and its application to online cloud cost optimization*. 2013 Proceedings IEEE INFOCOM, 2013. `10.1109/infcom.2013.6566944` https://doi.org/10.1109/infcom.2013.6566944 - Difference from this work: the constrained ski-rental problem for cloud cost: a constraint is added, and the error model stays one-sided
[62] Irani, S. *Competitive analysis of paging*. Lecture Notes in Computer Science, 1998. `10.1007/bfb0029564` https://doi.org/10.1007/bfb0029564 - Difference from this work: the standard account of competitive paging: it supplies the classical bound this paper's baseline realises exactly, and has no error parameter
[63] Achlioptas, D.; Chrobak, M.; Noga, J. *Competitive analysis of randomized paging algorithms*. Theoretical Computer Science, 2000. `10.1016/s0304-3975(98)00116-9` https://doi.org/10.1016/s0304-3975(98)00116-9 - Difference from this work: competitive analysis of randomized paging: a classical bound against an adversary, with no prediction and hence no channel to decompose
[64] McGeoch, L. A.; Sleator, D. D. *A strongly competitive randomized paging algorithm*. Algorithmica, 1991. `10.1007/bf01759073` https://doi.org/10.1007/bf01759073 - Difference from this work: a strongly competitive randomized paging algorithm: a ratio result, no prediction
[65] Blum, A.; Burch, C.; Kalai, A. *Finely-competitive paging*. 40th Annual Symposium on Foundations of Computer Science (Cat. No.99CB37039), 1999. `10.1109/sffcs.1999.814617` https://doi.org/10.1109/sffcs.1999.814617 - Difference from this work: finely-competitive paging: a refinement of the ratio itself, with no prediction channel at all
[66] Albers, S. *On the Influence of Lookahead in Competitive Paging Algorithms*. Algorithmica, 1997. `10.1007/pl00009158` https://doi.org/10.1007/pl00009158 - Difference from this work: how lookahead changes competitive paging: lookahead is free information, not a prediction carrying an error
[67] Peserico, E. *Paging with dynamic memory capacity*. arXiv preprint, 2013. `arXiv:1304.6007v1` https://arxiv.org/abs/1304.6007v1 - Difference from this work: paging with dynamic memory capacity: the varying quantity is the cache, not the error
[68] Peserico, E.; Scquizzato, M. *Is competitive online paging an artifact?*. arXiv preprint, 2026. `arXiv:2606.23955v1` https://arxiv.org/abs/2606.23955v1 - Difference from this work: asks whether competitive online paging is an artefact: a critique of the baseline, not of the prediction
[69] Moruz, G.; Negoescu, A. *Outperforming LRU via Competitive Analysis on Parametrized Inputs for Paging*. Proceedings of the Twenty-Third Annual ACM-SIAM Symposium on Discrete Algorithms, 2012. `10.1137/1.9781611973099.132` https://doi.org/10.1137/1.9781611973099.132 - Difference from this work: outperforms LRU via competitive analysis on PARAMETRIZED INPUTS: parametrised inputs, not a parametrised error direction
[70] Emek, Y.; Kutten, S.; Shi, Y. *Online Paging with a Vanishing Regret*. arXiv preprint, 2020. `arXiv:2011.09439v2` https://arxiv.org/abs/2011.09439v2 - Difference from this work: online paging with a vanishing regret: the objective is regret, not consistency-robustness
[71] Levy, O.; Touitou, N.; Rosenberg, A. *Online Weighted Paging with Unknown Weights*. arXiv preprint, 2024. `arXiv:2410.21266v1` https://arxiv.org/abs/2410.21266v1 - Difference from this work: online weighted paging with unknown weights: the unknown is the WEIGHT, not the prediction error
[72] Chen, P.; Zhao, H.; Tang, X.; et al. *Towards Optimal Robustness in Learning-Augmented Paging*. arXiv preprint, 2026. `arXiv:2606.01342v3` https://arxiv.org/abs/2606.01342v3 - Difference from this work: pushes towards optimal robustness in learning-augmented paging: robustness is maximised, not separated from consistency
[73] Antoniadis, A.; Boyar, J.; Eliáš, M.; et al. *Paging with Succinct Predictions*. arXiv preprint, 2022. `arXiv:2210.02775v1` https://arxiv.org/abs/2210.02775v1 - Difference from this work: bounds what a BUDGET of prediction bits buys in paging; this paper asks what the direction of a fixed-size error buys
[74] Jain, A.; Lin, C. *A Taxonomy of Cache Replacement Policies*. Synthesis Lectures on Computer Architecture, 2019. `10.1007/978-3-031-01762-9_2` https://doi.org/10.1007/978-3-031-01762-9_2 - Difference from this work: a taxonomy of the replacement policies a practitioner meets: no error model, and hence no error channel
[75] Sethumurugan, S.; Yin, J.; Sartori, J. *Designing a Cost-Effective Cache Replacement Policy using Machine Learning*. 2021 IEEE International Symposium on High-Performance Computer Architecture (HPCA), 2021. `10.1109/hpca51647.2021.00033` https://doi.org/10.1109/hpca51647.2021.00033 - Difference from this work: a cost-effective learned replacement policy measured on traces, with no account of what its prediction's error direction costs
[76] Souza, M. A.; Freitas, H. C. *Reinforcement Learning-Based Cache Replacement Policies for Multicore Processors*. IEEE Access, 2024. `10.1109/access.2024.3409228` https://doi.org/10.1109/access.2024.3409228 - Difference from this work: reinforcement-learned replacement policies for multicore processors: learning the policy, where this paper holds the policy fixed and varies the error
[77] Student, D. o. C. S. R. C. o. E. B. I.; P, P.; A, R. S.; et al. *Machine Learning-Based Cache Replacement Policies: A Survey*. International Journal of Engineering and Advanced Technology, 2021. `10.35940/ijeat.f2907.0810621` https://doi.org/10.35940/ijeat.f2907.0810621 - Difference from this work: collects the cache-replacement policies a deployed cache chooses between: it compares policies and does not price the predictor inside them
[78] Im, S.; Kumar, R.; Montazer Qaem, M.; et al. *Non-Clairvoyant Scheduling with Predictions*. Proceedings of the 33rd ACM Symposium on Parallelism in Algorithms and Architectures, 2021. `10.1145/3409964.3461790` https://doi.org/10.1145/3409964.3461790 - Difference from this work: sets the non-clairvoyant scheduling guarantee under a prediction -- the canonical instantiation of the error-bound form this paper decomposes
[79] Benomar, Z.; Perchet, V. *Non-clairvoyant Scheduling with Partial Predictions*. arXiv preprint, 2024. `arXiv:2405.01013v2` https://arxiv.org/abs/2405.01013v2 - Difference from this work: non-clairvoyant scheduling with partial predictions: 'partial' is about HOW MUCH of the schedule is predicted, not which direction the error runs
[80] Benomar, Z.; Cosson, R.; Lindermayr, A.; et al. *Non-Clairvoyant Scheduling with Progress Bars*. arXiv preprint, 2025. `arXiv:2509.19662v1` https://arxiv.org/abs/2509.19662v1 - Difference from this work: non-clairvoyant scheduling with progress bars: information replaces prediction
[81] Lindermayr, A.; Megow, N.; Rapp, M. *Speed-Oblivious Online Scheduling: Knowing (Precise) Speeds is not Necessary*. arXiv preprint, 2023. `arXiv:2302.00985v2` https://arxiv.org/abs/2302.00985v2 - Difference from this work: shows that precise speeds are not necessary: the finding is about knowledge of the INSTANCE, not about a prediction's error
[82] Lindermayr, A.; Schlöter, J. *Delayed-Clairvoyant Flow Time Scheduling via a Borrow Graph Analysis*. arXiv preprint, 2026. `arXiv:2602.21827v1` https://arxiv.org/abs/2602.21827v1 - Difference from this work: delayed-clairvoyant flow time through a borrow graph: DELAY is the quantity, and the analysis is not error-parameterised
[83] Chen, T.; Tan, Z. *Tighter Bounds on Non-clairvoyant Parallel Machine Scheduling with Prediction to Minimize Makespan*. arXiv preprint, 2025. `arXiv:2504.10945v1` https://arxiv.org/abs/2504.10945v1 - Difference from this work: tighter bounds on non-clairvoyant parallel-machine scheduling with predictions: tighter constants on a magnitude-based bound
[84] Baba, K.; Bampis, E.; Mitropoulos, G. *Learning-Augmented Approximation for Unrelated-Machines Makespan Scheduling*. arXiv preprint, 2026. `arXiv:2606.13133v1` https://arxiv.org/abs/2606.13133v1 - Difference from this work: learning-augmented approximation for unrelated-machines makespan: an approximation ratio in the error, one symbol
[85] Angelopoulos, S.; Bienkowski, M.; Dürr, C.; et al. *Contract Scheduling with Distributional and Multiple Advice*. arXiv preprint, 2024. `arXiv:2404.12485v1` https://arxiv.org/abs/2404.12485v1 - Difference from this work: contract scheduling with distributional and multiple advice: advice quality again enters as a magnitude
[86] Bansal, N.; Dhamdhere, K.; Könemann, J.; et al. *Non-Clairvoyant Scheduling for Minimizing Mean Slowdown*. Algorithmica, 2004. `10.1007/s00453-004-1115-0` https://doi.org/10.1007/s00453-004-1115-0 - Difference from this work: minimises mean slowdown without clairvoyance: a classical ratio result, with no prediction to price
[87] Kim, J. H.; Chwa, K. Y. *Non-clairvoyant scheduling for weighted flow time*. Information Processing Letters, 2003. `10.1016/s0020-0190(03)00231-x` https://doi.org/10.1016/s0020-0190(03)00231-x - Difference from this work: studies non-clairvoyant weighted flow time: a classical ratio result, no prediction
[88] Albers, S.; Eckl, A. *Explorable Uncertainty in Scheduling with Non-uniform Testing Times*. Lecture Notes in Computer Science, 2021. `10.1007/978-3-030-80879-2_9` https://doi.org/10.1007/978-3-030-80879-2_9 - Difference from this work: explorable uncertainty with non-uniform testing times: the uncertainty is RESOLVED BY QUERYING, not given as a prediction with a sign
[89] Bamas, É.; Maggiori, A.; Rohwedder, L.; et al. *Learning Augmented Energy Minimization via Speed Scaling*. arXiv preprint, 2020. `arXiv:2010.11629v1` https://arxiv.org/abs/2010.11629v1 - Difference from this work: minimises energy through speed scaling with learned advice, under a magnitude-only guarantee
[90] Mandi, J.; Kotary, J.; Berden, S.; et al. *Decision-Focused Learning: Foundations, State of the Art, Benchmark and Future Opportunities*. Journal of Artificial Intelligence Research, 2024. `10.1613/jair.1.15320` https://doi.org/10.1613/jair.1.15320 - Difference from this work: surveys decision-focused learning's foundations and benchmarks: it maps the methods and reports no consistency-robustness decomposition
[91] Mandi, J.; Bucarey, V.; Mulamba, M.; et al. *Decision-Focused Learning: Through the Lens of Learning to Rank*. arXiv preprint, 2021. `arXiv:2112.03609v4` https://arxiv.org/abs/2112.03609v4 - Difference from this work: reads decision-focused learning through learning to rank: a reformulation, with the error again treated as a magnitude
[92] Schutte, N.; Postek, K.; Yorke-Smith, N. *Robust Losses for Decision-Focused Learning*. arXiv preprint, 2023. `arXiv:2310.04328v2` https://arxiv.org/abs/2310.04328v2 - Difference from this work: proposes robust losses for decision-focused learning: the loss is made robust to the error's magnitude, and the sign does not enter
[93] Farhat, Y. *On the Robustness of Decision-Focused Learning*. arXiv preprint, 2023. `arXiv:2311.16487v4` https://arxiv.org/abs/2311.16487v4 - Difference from this work: tests the robustness of decision-focused learning empirically against perturbations: robustness measured against perturbations, where this paper's robustness is a ratio read per error channel
[94] Liu, M. *Decision-Focused Learning: When and Why Traditional Prediction Models Fail*. arXiv preprint, 2026. `arXiv:2606.21773v1` https://arxiv.org/abs/2606.21773v1 - Difference from this work: asks when and why traditional prediction models fail: a diagnosis of failure, not a decomposition of the error that causes it
[95] Wang, S.; Tian, X. *A Deficiency of the Predict-Then-Optimize Framework: Decreased Decision Quality with Increased Data Size*. Mathematics, 2023. `10.3390/math11153359` https://doi.org/10.3390/math11153359 - Difference from this work: describes a deficiency in which decision quality falls as data grows: a counter-intuitive empirical finding whose mechanism is not an error channel
[96] Huang, M.; Gupta, V. *Decision-Focused Learning with Directional Gradients*. arXiv preprint, 2024. `arXiv:2402.03256v4` https://arxiv.org/abs/2402.03256v4 - Difference from this work: decision-focused learning with directional gradients: 'directional' names the GRADIENT's direction, not the error's sign
[97] Wang, Z.; Loke, G. G.; Zuo, R. *Autocorrelated Optimize-via-Estimate: Predict-then-Optimize versus Finite-sample Optimal*. arXiv preprint, 2026. `arXiv:2602.01877v1` https://arxiv.org/abs/2602.01877v1 - Difference from this work: studies an autocorrelated optimize-via-estimate regime: dependence BETWEEN samples, not between the two directions of one error
[98] Ziliaskopoulos, K.; Vinel, A.; Smith, A. E. *Decision-Value Attribution in Predict-then-Optimize Systems*. arXiv preprint, 2026. `arXiv:2606.29878v1` https://arxiv.org/abs/2606.29878v1 - Difference from this work: attributes decision value in predict-then-optimize systems: value attribution, with the online tradeoff out of scope
[99] Balghiti, O. E.; Elmachtoub, A. N.; Grigas, P.; et al. *Generalization Bounds in the Predict-then-Optimize Framework*. arXiv preprint, 2019. `arXiv:1905.11488v3` https://arxiv.org/abs/1905.11488v3 - Difference from this work: bounds generalization in the predict-then-optimize framework: a bound on error, with no separation of its direction
[100] Shariatmadar, K.; Yorke-Smith, N.; Osman, A.; et al. *Generalized Decision Focused Learning under Imprecise Uncertainty--Theoretical Study*. arXiv preprint, 2025. `arXiv:2502.17984v2` https://arxiv.org/abs/2502.17984v2 - Difference from this work: generalises decision-focused learning to imprecise uncertainty: uncertainty is represented, and the online ratio is not the object
[101] Ben-Baruch, E.; Ridnik, T.; Zamir, N.; et al. *Asymmetric Loss For Multi-Label Classification*. arXiv preprint, 2020. `arXiv:2009.14119v4` https://arxiv.org/abs/2009.14119v4 - Difference from this work: uses an asymmetric loss for multi-label classification: an objective-side asymmetry, from which no online guarantee follows
[102] Zhou, X.; Liu, X.; Jiang, J.; et al. *Asymmetric Loss Functions for Learning with Noisy Labels*. arXiv preprint, 2021. `arXiv:2106.03110v1` https://arxiv.org/abs/2106.03110v1 - Difference from this work: asymmetric loss functions for learning with noisy labels: LABEL noise rather than prediction error, with the asymmetry in the objective
[103] Barnes, B. M.; Henn, M. A. *Addressing misclassification costs in machine learning through asymmetric loss functions*. Metrology, Inspection, and Process Control XXXVII, 2023. `10.1117/12.2662027` https://doi.org/10.1117/12.2662027 - Difference from this work: addresses misclassification costs through asymmetric loss functions: the asymmetry is in the LOSS, where this paper's asymmetry is in the PREDICTION ERROR and is measured at the decision end
[104] Lozano, A. C.; Abe, N. *Multi-class cost-sensitive boosting with p-norm loss functions*. Proceedings of the 14th ACM SIGKDD international conference on Knowledge discovery and data mining, 2008. `10.1145/1401890.1401953` https://doi.org/10.1145/1401890.1401953 - Difference from this work: multi-class cost-sensitive boosting with p-norm loss functions: an objective-side asymmetry, and nothing about online ratios
[105] Fu, S.; Tian, Y.; Tang, J.; et al. *Cost-sensitive learning with modified Stein loss function*. Neurocomputing, 2023. `10.1016/j.neucom.2023.01.052` https://doi.org/10.1016/j.neucom.2023.01.052 - Difference from this work: cost-sensitive learning with a modified Stein loss function: the loss is made to carry the decision direction, but no consistency-robustness frontier is measured
[106] Kotary, J.; Di Vito, V.; Cristopher, J.; et al. *Learning Joint Models of Prediction and Optimization*. arXiv preprint, 2024. `arXiv:2409.04898v1` https://arxiv.org/abs/2409.04898v1 - Difference from this work: learns joint models of prediction and optimization: the model is the contribution, not the price of its error
[107] Kotary, J.; Di Vito, V.; Christopher, J.; et al. *Predict-Then-Optimize by Proxy: Learning Joint Models of Prediction and Optimization*. arXiv preprint, 2023. `arXiv:2311.13087v1` https://arxiv.org/abs/2311.13087v1 - Difference from this work: the proxy formulation of the same joint learning: again a modelling contribution
[108] Elmachtoub, A. N.; Liang, J. C. N.; McNellis, R. *Decision Trees for Decision-Making under the Predict-then-Optimize Framework*. arXiv preprint, 2020. `arXiv:2003.00360v2` https://arxiv.org/abs/2003.00360v2 - Difference from this work: decision trees under the predict-then-optimize framework: an instance of the framework, not a statement about the error's direction
[109] Kang, J.; Kim, Y. S. *Decision-Focused Learning to Bridge the Prediction-Operation Gap in Energy Storage System Participation in Reserve Markets*. 2026 IEEE PES International Meeting (PES IM), 2026. `10.1109/pesim67009.2026.11438642` https://doi.org/10.1109/pesim67009.2026.11438642 - Difference from this work: bridges the prediction-operation gap in energy storage systems: an application, with no per-channel pricing
[110] Tang, B.; Khalil, E. B. *PyEPO: a PyTorch-based end-to-end predict-then-optimize library for linear and integer programming*. Mathematical Programming Computation, 2024. `10.1007/s12532-024-00255-x` https://doi.org/10.1007/s12532-024-00255-x - Difference from this work: supplies the standard end-to-end predict-then-optimize library: the tool this paper could have used, measuring tasks rather than error channels
[111] Sun, H.; Liu, A. L. *Robust Generalization with Adaptive Optimal Transport Priors for Decision-Focused Learning*. arXiv preprint, 2026. `arXiv:2602.01427v2` https://arxiv.org/abs/2602.01427v2 - Difference from this work: robustifies decision-focused learning with adaptive optimal-transport priors: a robustification method whose object is the error's magnitude
[112] Jin, B.; Ma, W. *Online Bipartite Matching with Advice: Tight Robustness-Consistency Tradeoffs for the Two-Stage Model*. Advances in Neural Information Processing Systems 35, 2022. `10.52202/068431-1058` https://doi.org/10.52202/068431-1058 - Difference from this work: gives tight robustness-consistency trade-offs for bipartite matching with advice: the frontier for another problem, derived under a symmetric error model
[113] Chan, H.; Lin, J.; Wang, C. *Consistency-Robustness Tradeoffs for Strategyproof Scheduling with Predictions*. arXiv preprint, 2026. `arXiv:2609.14088v1` https://arxiv.org/abs/2609.14088v1 - Difference from this work: gives matching lower bounds for a mechanism class with predictions, putting strategyproof scheduling on the current worst-case frontier -- a frontier bounded, not measured per error channel
[114] Pokou, F. *Learning-Augmented Online Allocation under Unreliable Advice: Robustness, Exposure Fairness, and Distribution Shift*. arXiv preprint, 2026. `arXiv:2608.26889v1` https://arxiv.org/abs/2608.26889v1 - Difference from this work: adds exposure fairness and distribution shift to a loss proportional to the prediction error under bounded-error assumptions: more objectives on the same magnitude-based error model
[115] Yoshinaga, T.; Kawase, Y. *Analyzing the effect of prediction accuracy on the distributionally-robust competitive ratio*. arXiv preprint, 2026. `arXiv:2601.06813v1` https://arxiv.org/abs/2601.06813v1 - Difference from this work: analyses how prediction ACCURACY moves the distributionally-robust competitive ratio: accuracy is the variable, not the direction of the error
[116] Patel, Y.; Tewari, A. *Distribution-Free Robust Predict-Then-Optimize in Function Spaces*. arXiv preprint, 2026. `arXiv:2602.08215v2` https://arxiv.org/abs/2602.08215v2 - Difference from this work: distribution-free robust predict-then-optimize in function spaces: robustness in the statistical sense, not the competitive-ratio sense
[117] Albers, S. *Online algorithms: a survey*. Mathematical Programming, 2003. `10.1007/s10107-003-0436-0` https://doi.org/10.1007/s10107-003-0436-0 - Difference from this work: the field's standard starting point: it organises the classical bounds this paper's baseline is drawn from, and contains no prediction-error experiment
[118] Fiat, A.; Woeginger, G. J. *Competitive analysis of algorithms*. Lecture Notes in Computer Science, 1998. `10.1007/bfb0029562` https://doi.org/10.1007/bfb0029562 - Difference from this work: sets the yardstick this paper's measured ratios are read against; with no error parameter there is no frontier to decompose
[119] Chen, M.; Chau, S. C. K. *Preliminaries of Online Algorithms and Competitive Analysis*. Synthesis Lectures on Learning, Networks, and Algorithms, 2022. `10.1007/978-3-031-11549-3_2` https://doi.org/10.1007/978-3-031-11549-3_2 - Difference from this work: lays out the preliminaries of online algorithms and competitive analysis: definitional material, not a measurement
[120] Anand, K.; Ge, R.; Kumar, A.; et al. *A Regression Approach to Learning-Augmented Online Algorithms*. arXiv preprint, 2022. `arXiv:2205.08717v2` https://arxiv.org/abs/2205.08717v2 - Difference from this work: a regression approach to learning-augmented online algorithms: the learning is the contribution, and the guarantee stays in the error's magnitude
[121] Ameli, A. J.; Sanita, L.; Venzin, M. *Learning-Augmented Online Covering Problems*. arXiv preprint, 2025. `arXiv:2507.06032v1` https://arxiv.org/abs/2507.06032v1 - Difference from this work: learning-augmented online covering problems: another problem family with a magnitude-based guarantee
[122] Kevi, E.; Nguyen, K. T. *Online Covering with Multiple Experts*. arXiv preprint, 2023. `arXiv:2312.14564v1` https://arxiv.org/abs/2312.14564v1 - Difference from this work: online covering with multiple experts: several experts, where this paper has one prediction and asks about its error's direction
[123] Kesselheim, T.; Molinaro, M.; Patton, K.; et al. *Online Algorithms via Minimax and Posterior Matching*. arXiv preprint, 2026. `arXiv:2608.01616v1` https://arxiv.org/abs/2608.01616v1 - Difference from this work: derives online algorithms via minimax and posterior matching: a proof technique, not an error model
[124] Coester, C.; Turoczy, A. *Primal-Dual Online Algorithms for the Parking Permit Problem*. arXiv preprint, 2026. `arXiv:2607.08262v1` https://arxiv.org/abs/2607.08262v1 - Difference from this work: primal-dual online algorithms for the parking permit problem: a primal-dual construction, with no prediction
[125] Tiedemann, M.; Ide, J.; Schöbel, A. *Competitive Analysis for Multi-objective Online Algorithms*. Lecture Notes in Computer Science, 2015. `10.1007/978-3-319-15612-5_19` https://doi.org/10.1007/978-3-319-15612-5_19 - Difference from this work: analyses competitive ratio for multi-objective online problems: several objectives, where this paper's two axes are the error's two directions
[126] Zhao, X.; Shen, H. *Online algorithms for 2D bin packing with advice*. Neurocomputing, 2016. `10.1016/j.neucom.2015.11.035` https://doi.org/10.1016/j.neucom.2015.11.035 - Difference from this work: online algorithms for 2D bin packing with advice: advice bits again, with no signed error channel
[127] Ma, M.; Tzamos, C. *Buying Information for Stochastic Optimization*. arXiv preprint, 2023. `arXiv:2306.03607v1` https://arxiv.org/abs/2306.03607v1 - Difference from this work: prices the INFORMATION an online algorithm buys: information has a price, where this paper asks what a prediction's error direction costs
[128] Horiyama, T.; Iwama, K.; Kawahara, J. *Finite-State Online Algorithms and Their Automated Competitive Analysis*. Lecture Notes in Computer Science, 2006. `10.1007/11940128_9` https://doi.org/10.1007/11940128_9 - Difference from this work: automates competitive analysis for finite-state online algorithms: a tool for ratios, with no prediction
[129] Parkhouse, J. *Competitive Online Algorithms for the Discrete Evacuation Problem in General Graphs*. Elsevier BV, 2025. `10.2139/ssrn.5200079` https://doi.org/10.2139/ssrn.5200079 - Difference from this work: competitive online algorithms for the discrete evacuation problem on general graphs: a ratio result, with no prediction channel
[130] Christou, D.; Fotakis, D.; Koumoutsos, G. *Memoryless Algorithms for the Generalized k-server Problem on Uniform Metrics*. Lecture Notes in Computer Science, 2021. `10.1007/978-3-030-80879-2_10` https://doi.org/10.1007/978-3-030-80879-2_10 - Difference from this work: bounds memoryless algorithms for the generalized k-server problem on uniform metrics: a structural restriction, no prediction
[131] Kraska, T.; Beutel, A.; Chi, E. H.; et al. *The Case for Learned Index Structures*. arXiv preprint, 2017. `arXiv:1712.01208v3` https://arxiv.org/abs/1712.01208v3 - Difference from this work: the case for learned index structures: the result that made learned components standard, argued from end-to-end gains rather than from error structure
[132] Marcus, R.; Kipf, A.; van Renen, A.; et al. *Benchmarking learned indexes*. Proceedings of the VLDB Endowment, 2020. `10.14778/3421424.3421425` https://doi.org/10.14778/3421424.3421425 - Difference from this work: benchmarks learned indexes rather than asserting their advantage: the correction this paper applies to the ratio literature, applied to a different object
[133] Kipf, A.; Marcus, R.; van Renen, A.; et al. *SOSD: A Benchmark for Learned Indexes*. arXiv preprint, 2019. `arXiv:1911.13014v1` https://arxiv.org/abs/1911.13014v1 - Difference from this work: builds a searchable benchmark for learned indexes: a benchmark, reporting end-to-end deltas without an error channel
[134] Bachfischer, M.; Borovica-Gajic, R.; Rubinstein, B. I. P. *Testing the Robustness of Learned Index Structures*. arXiv preprint, 2022. `arXiv:2207.11575v1` https://arxiv.org/abs/2207.11575v1 - Difference from this work: tests the robustness of learned index structures: robustness to worst-case INPUTS, not to a signed prediction error
[135] Ding, J.; Minhas, U. F.; Yu, J.; et al. *ALEX: An Updatable Adaptive Learned Index*. Proceedings of the 2020 ACM SIGMOD International Conference on Management of Data, 2020. `10.1145/3318464.3389711` https://doi.org/10.1145/3318464.3389711 - Difference from this work: makes a learned index updatable in ALEX: an engineering advance, with no error decomposition
[136] Kipf, A.; Marcus, R.; van Renen, A.; et al. *RadixSpline: A Single-Pass Learned Index*. arXiv preprint, 2020. `arXiv:2004.14541v2` https://arxiv.org/abs/2004.14541v2 - Difference from this work: builds a learned index in a single pass: a construction result, with no error model
[137] Abu-Libdeh, H.; Altınbüken, D.; Beutel, A.; et al. *Learned Indexes for a Google-scale Disk-based Database*. arXiv preprint, 2020. `arXiv:2012.12501v1` https://arxiv.org/abs/2012.12501v1 - Difference from this work: deploys learned indexes at Google scale: a deployment report, with no measurement of how the predictor's error direction prices out
[138] Jue, A. *Poisoning Learned Index Structures: Static and Dynamic Adversarial Attacks on ALEX*. arXiv preprint, 2026. `arXiv:2604.24975v1` https://arxiv.org/abs/2604.24975v1 - Difference from this work: poisons learned index structures with static and dynamic attacks: the adversary is external, not the prediction's own error
[139] Yang, J.; Karimi, R.; Sæmundsson, T.; et al. *MITHRIL: Mining Sporadic Associations for Cache Prefetching*. arXiv preprint, 2017. `arXiv:1705.07400v1` https://arxiv.org/abs/1705.07400v1 - Difference from this work: mines sporadic associations for cache prefetching: a prefetching mechanism, with no prediction-error analysis
[140] Kim, K.; Li, J.; Hong, K.; et al. *Saving GPU Hours in LLM Inference System Development and Online Workloads with Simulation and DBMS-Inspired Cache Replacement Policies*. arXiv preprint, 2024. `arXiv:2411.07447v5` https://arxiv.org/abs/2411.07447v5 - Difference from this work: saves GPU hours with DBMS-inspired cache replacement policies: a systems cost saving, with the predictor's error not a variable
[141] Bulus, M. *Minimum Detectable Effect Size Computations for Cluster-Level Regression Discontinuity: Quadratic Functional Form and Beyond*. arXiv preprint, 2019. `arXiv:1910.12925v2` https://arxiv.org/abs/1910.12925v2 - Difference from this work: computes minimum detectable effect sizes for cluster-level designs -- the design calculation this paper borrows for cluster-level MDEs, not an error decomposition
[142] Burstyn, I.; Cox, L. A.; Carneal, T.; et al. *Minimum Detectable Effect (MDE) Calculator for Linear Regression: Optimizing Number of Subjects (LIN-N)*. SciPinion, 2025. `10.63565/scipinion.resource.lin-n` https://doi.org/10.63565/scipinion.resource.lin-n - Difference from this work: an MDE calculator that fixes the number of subjects for a target effect: the arithmetic of resolvability, adopted here as a per-block resolution threshold
[143] Hunter, K.; Miratrix, L.; Porter, K. *Power Under Multiplicity Project (PUMP): Estimating Power, Minimum Detectable Effect Size, and Sample Size When Adjusting for Multiple Outcomes in Multi-level Experiments*. arXiv preprint, 2021. `arXiv:2112.15273v3` https://arxiv.org/abs/2112.15273v3 - Difference from this work: estimates power, minimum detectable effect size and multiplicity correction together: MULTIPLICITY is its axis, where this paper's is the error's direction
[144] Fehr, J.; 1 Institute of Engineering and Computational Mechanics at the University of Stuttgart, P. 9. D. 7. S. G.; Heiland, J.; et al. *Best practices for replicability, reproducibility and reusability of computer-based experiments exemplified by model reduction software*. AIMS Mathematics, 2016. `10.3934/math.2016.3.261` https://doi.org/10.3934/Math.2016.3.261 - Difference from this work: codifies best practices for reusability of computational experiments: the standard this paper's reproduce.sh is written against
[145] Flittner, M.; Bauer, R.; Rizk, A.; et al. *Taming the Complexity of Artifact Reproducibility*. Proceedings of the Reproducibility Workshop, 2017. `10.1145/3097766.3097770` https://doi.org/10.1145/3097766.3097770 - Difference from this work: studies how to tame the complexity of artefact reproducibility: the artefact-level problem, which this paper answers in one command
[146] Thorpe, B. *The ReproRubric: Evaluation Criteria for the Reproducibility of Computational Analyses*. Center for Open Science, 2019. `10.31219/osf.io/thvef` https://doi.org/10.31219/osf.io/thvef - Difference from this work: scores the reproducibility of a computational analysis as an ARTEFACT: a rubric, where this paper's evidence for its own claims is a re-run
[147] Brooks, A.; Chambers, J.; Lee, C. N.; et al. *A Partial Replication with a Sample Size of One: A Smoke Test for Empirical Software Engineering*. 2013 3rd International Workshop on Replication in Empirical Software Engineering Research, 2013. `10.1109/reser.2013.7` https://doi.org/10.1109/reser.2013.7 - Difference from this work: a partial replication with a sample size of one: the same discipline of reporting a study's own scale, which this paper's threats section applies to itself
[148] Souto, H. G.; Neto, F. L. *Beyond Arbitrary Replications: A Principled Approach to Simulation Design in Causal Inference*. arXiv preprint, 2024. `arXiv:2409.05161v3` https://arxiv.org/abs/2409.05161v3 - Difference from this work: argues for a principled approach to simulation design over arbitrary replications: the design argument this paper's instrument follows
[149] Gardner, J.; Brooks, C.; Andres, J. M. L.; et al. *MORF: A Framework for Predictive Modeling and Replication At Scale With Privacy-Restricted MOOC Data*. arXiv preprint, 2018. `arXiv:1801.05236v3` https://arxiv.org/abs/1801.05236v3 - Difference from this work: builds a framework for predictive modelling and replication AT SCALE: replication at scale, the opposite side of the contrast from designing one study to be checkable
[150] Zilberman, N. *An Artifact Evaluation of NDP*. ACM SIGCOMM Computer Communication Review, 2020. `10.1145/3402413.3402418` https://doi.org/10.1145/3402413.3402418 - Difference from this work: evaluates the NDP artefact and shows what an independent re-run can and cannot check: the boundary of artefact evaluation, which this paper's threats section restates for its own package
[151] Shepperd, M. *Replication studies considered harmful*. Proceedings of the 40th International Conference on Software Engineering: New Ideas and Emerging Results, 2018. `10.1145/3183399.3183423` https://doi.org/10.1145/3183399.3183423 - Difference from this work: argues that replication studies considered harmful misread their own remit: the argument that a repeated measurement can misread its remit, which this paper states as a limitation of its own
[152] Santos, A.; Vegas, S.; Oivo, M.; et al. *Comparing the Results of Replications in Software Engineering*. arXiv preprint, 2020. `arXiv:2011.02861v1` https://arxiv.org/abs/2011.02861v1 - Difference from this work: compares the results of replications: how replications AGREE, not how a measurement's own resolution bounds the claims built on it
[153] Penzenstadler, B.; Eckhardt, J.; Fernandez, D. M. *Two Replication Studies for Evaluating Artefact Models in RE: Results and Lessons Learnt*. 2013 3rd International Workshop on Replication in Empirical Software Engineering Research, 2013. `10.1109/reser.2013.17` https://doi.org/10.1109/reser.2013.17 - Difference from this work: reports two replication studies for artefact models in requirements engineering: replication results in another subfield, cited here for their lessons rather than used as evidence
[154] Liu, C.; Gao, C.; Xia, X.; et al. *On the Reproducibility and Replicability of Deep Learning in Software Engineering*. ACM Transactions on Software Engineering and Methodology, 2021. `10.1145/3477535` https://doi.org/10.1145/3477535 - Difference from this work: studies the replicability and reproducibility of deep learning in software engineering: a measurement of our field's practice, and the reporting standard this paper adopted for itself
[155] Fund, F. *We Need More Reproducibility Content Across the Computer Science Curriculum*. Proceedings of the 2023 ACM Conference on Reproducibility and Replicability, 2023. `10.1145/3589806.3600033` https://doi.org/10.1145/3589806.3600033 - Difference from this work: argues for more reproducibility content across the computer science curriculum: a call for practice, of which this paper's package is one instance
[156] Geng, H.; Ruan, H.; Wang, R.; et al. *Benchmarking PtO and PnO Methods in the Predictive Combinatorial Optimization Regime*. arXiv preprint, 2023. `arXiv:2311.07633v5` https://arxiv.org/abs/2311.07633v5 - Difference from this work: benchmarks predict-then-optimize and predict-and-optimize together: a benchmark comparison, not a decomposition of the error channel
