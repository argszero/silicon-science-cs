# The Timeout Is the Measurement

### What a timed-out tail leaves identifiable, and what certifying it costs

*A case study. One public trace, one day, and the estimand is the 30-second interval mean rather than the single invocation. Nothing below is claimed to hold of services in general.*

## Abstract

A latency harness reports a 99th percentile. If the harness also stops waiting at a timeout — as nearly every one does — then some fraction of requests have no latency value at all, and the number it prints is not the quantile it names. We treat that as an identification problem rather than a rounding problem, and ask three questions of one real workload: can the quantile be resolved at all, does the timeout bind, and what does certifying the quantile cost.

The first answer dominates. Of the 47,502 function rows in the first day of the public Azure Functions trace that carry a usable quantile ladder, **34.35%** expect at least one observation above their own 99th percentile; the remaining **65.65%** cannot resolve it at any timeout, because the quantile is a statement about the top of a distribution that the sample never reaches. 31,185 rows (65.65%) record fewer than 100 invocations in a whole day. No amount of careful measurement repairs this: it is a property of how much data was collected, not of how it was analysed.

Second, with the timeout set at a fixed multiple of each row's own median, truncation binds — the true quantile falls outside the set the harness can identify — on **57.52%** of rows at 2x the median, and still on **12.24%** at 32x. Where it binds, the printed number sits below the truth by a median factor of **4.24** at 2x and **3.06** even at 32x. A registered prior predicted that under 10% of rows would still bind at 32x. The data says otherwise, and that refutation is the sharpest result in this paper.

Third, certifying the quantile to 5% relative precision by timeout levels alone needs a median of **25** distinct levels on this workload, and 98 at the 90th percentile of rows.

Throughout, the unit is the **30-second interval mean**, not the single invocation: the trace publishes percentiles of a 30-second average, so every range reported here ranges over a smoothed quantity and is therefore a **lower bound** on the invocation-level range. All numbers come from one program and one committed input; `./reproduce.sh` re-derives them.

## 1 The number a timeout leaves

Tail latency is a design constraint rather than a curiosity: the slowest requests set the fan-out cost of any request that must wait for all of its shards, so a single slow component can dominate the response time of a system built from fast ones [1,2,3]. The operational literature therefore treats a high quantile of the latency distribution as a service-level objective, and the entire vocabulary of tail tolerance is built on the assumption that the quantile is measurable [1].

Serverless platforms sharpen the problem. Workloads there are bursty, short and heterogeneous, with a heavy share of functions invoked too rarely to accumulate much of a sample [4,5,6,7,8,9]. A timeout is not optional in that setting: it is the only thing bounding a request whose dependency is silently broken, and the retry that follows a timeout is what turns a slow dependency into a metastable outage [10].

So the measurement instrument and the safety mechanism are the same mechanism, and it is worth asking what it does to the number it produces.

The statistics of incomplete observation are old and precise. Right-censoring is the standard case in survival analysis: an observation that has not failed by the end of the study is not missing, it is *known to exceed* a bound, and the Kaplan–Meier estimator is the canonical use of that information [11,12,13]. General censoring mechanisms, interval censoring, truncation, and the conditions under which the incomplete-data likelihood may be treated as ignorable have all been worked out [14,15,16,17,18]. What has not travelled is the consequence for a *report*, as opposed to for an estimate: when the censoring is heavy enough, the quantity the report names is not identified by the data at all, and the correct output is a set rather than a point.

That distinction is the daily business of the partial-identification literature, where the object of interest is an identified set and the question is what can be concluded without a point-identifying assumption [19,20,21]. The specific arithmetic of "how large a sample do I need before a high quantile means anything" appears in the older literature on tolerance limits and sample quantiles [22,23,24,25]. Our contribution is none of these pieces. It is to put them together on a real workload and report, as a measurement, where the boundary sits — and to be explicit that a report made without that boundary in view is not a conservative report but an unlabelled one.

The frame throughout is measurement as a statistical act rather than a plumbing act: a number produced by an instrument is a claim about a population, and it deserves the scrutiny of any other inference [26,27].

## 2 The object, and the lemma that fixes it

A harness observes a latency `X` and stops at a timeout `T`. Write `c` for the fraction of requests that time out. What the harness has is not a sample of `X` but a sample of `X` conditioned on `X <= T`, whose distribution function is `F(x)/F(T)` on `[0, T]`. Requests above `T` are not missing at random in the ordinary sense; they are known to exceed `T` [28,29,30]. The information they carry is real but bounded, and the bound is what matters here.

The true `q`-quantile is identified exactly when `q <= F(T)`, that is when

    c <= 1 - q.

When that fails, the true quantile lies strictly above `T`, the identified set is the interval `(T, inf)`, and no volume of traffic narrows it: the missing mass is missing, not noisy. This is the survival-analytic statement that a quantile beyond the observable range is not estimable from the observations alone [17,18,31,32], and equally the partial-identification bound on a distribution's upper tail [19,20,21,33]. Its computational content for our purpose is small and exact, which is why the instrument is a few dozen lines of arithmetic rather than a fitting procedure.

Two consequences follow, and the second is the one that bites.

First, what the harness *prints* when the quantile is unidentified is the `q`-quantile of the truncated sample, which is `q * F(T)` in the original distribution's own coordinates. That number is strictly below `T`, and `T` is strictly below the whole set the data cannot rule out. So the printed value is not merely uncertain: it is biased downward by an amount that grows as the timeout tightens, and it is presented with no indication that anything is wrong.

Second, being *identified* is not the same as being *printed correctly*. At exactly `T` equal to the true 99th percentile the quantile is identified — the boundary case of the lemma — and the printed number is still the `q * F(T)`-quantile of the full distribution, which is below the truth. Identification is a property of the estimand; correctness of the printed value is a property of the estimator; the two coincide only when the timeout sits above the top of the observable range.

The ladder we work with is a piecewise-linear reconstruction through the seven published percentile points, which is what any reader of the table would do and what the interpolation literature warns about: a quantile read off a small grid of knots is a function of the interpolation rule as much as of the data [34,35,36]. We therefore treat the reconstruction as the *instrument* — fixed, stated, and applied identically to every row — rather than as an estimate of the truth. Every interval statement below is made about the reconstructed distribution, and the reconstruction's own error is a separate concern that we bound only qualitatively (Section 8).

Nothing in this section is new, and that is the point: the arithmetic is elementary. What is not elementary is noticing that a production report is sitting on it.

## 3 The trace, and the unit that must be stated first

We use the first day of the public Azure Functions trace [4]. The archive member is a 49,728-row table of per-function duration summaries; after removing rows whose ladder is not usable, 47,502 rows remain. The refusals are stated because they are not noise: 2,219 rows report a zero median, which makes the ratio to the median undefined; 7 rows cannot be parsed; 0 rows have a ladder whose knots decrease with probability, which is a recording defect rather than a distribution, and interpolating through one would invent tail mass.

**The unit comes first, because it changes every range in the paper.** The percentile columns of this table are not percentiles of individual invocations. The dataset documentation states that the framework aggregates every 30 seconds, and that the percentile columns are percentiles of the per-interval *average* over the invocations in that interval, weighted by how many there were. The `Minimum` and `Maximum` columns, by contrast, are extremes over single invocations. Two consequences:

1. Any ratio formed across those two groups — for instance a maximum divided by a percentile of the average — compares two different quantities and is not a tail ratio at all. Our own first registered prior did exactly this and was withdrawn (Section 7).
2. Within the percentile ladder, `p100/p50` is a ratio of two percentiles of the same quantity, so it is meaningful. But it describes the range of a *smoothed* distribution: averaging many invocations inside an interval pulls in the tail. It is therefore a **lower bound** on the dynamic range at the invocation level, and every cost figure derived from it is a lower bound too.

This is not a presentational caveat. Workload characterization has a long record of summaries whose meaning depends on the aggregation applied before they were computed [37], and the measurement-methodology literature has established that a benchmark number is a function of the instrument as much as of the system [38,39,40]. A paper that reported tail *ranges* from this table without saying which distribution they range over would be making a claim it cannot support.

The trace is one provider, one day, and one aggregation interval. Cluster data of this kind is known to be heterogeneous across time and across tenants [41,42,43,44], which is exactly why this is a case study rather than a sample of a population. Benchmarking studies that span machines and clouds reach the same conclusion from the other direction: the same system measured under different conditions produces a different distribution [45,46,47].

## 4 Limit one: the sample cannot resolve the quantile

A `q`-quantile is a statement about the top `1 - q` of a distribution. A sample of size `n` resolves it only if it expects at least one observation above it, that is, if `n (1 - q) >= 1`. For a 99th percentile that makes 100 invocations the exact boundary: at that count the expected number of observations above the quantile is one, and below it the quantile is an extrapolation from the sample's maximum.

This is the classical sample-size question for quantiles and tolerance limits, and its answer has been known for a long time [22,23,24,25,48,49,50,51,52]. The distribution-free bounds that make it sharp are equally classical [53,54,55,56,57,58], as is the machinery for attaching an interval to whatever is estimated [59,60,61,62,63], including the resampling route when the analytic one is inconvenient [64,65,66,67,68,69,70,71,72], and the survey-sampling frame that decides what the sample was a sample *of* [73].

What the applied literature does not routinely carry is the resulting refusal. Our measurement of it on this workload:

| quantity | rows | share of usable |
|---|---|---|
| usable rows | 47,502 | — |
| can resolve a 99th percentile (expects at least one observation above it) | 16,317 | **34.35%** |
| cannot resolve it at any timeout | 31,185 | 65.65% |
| fewer than 100 invocations in the day | 31,185 | 65.65% |
| fewer than 1,000 invocations in the day | 40,993 | 86.3% |

The median row expects 0.24 observations above its own 99th percentile — that is, the median row does not expect even one.

Two things follow. The obvious one is that for two rows in three a reported 99th percentile is an extrapolation, and no timeout setting changes that. The less obvious one is that this limit is *independent* of the censoring limit in Section 5: a row can be perfectly identified with respect to its timeout and still unable to resolve the quantile, because its sample is too thin. The two limits are computed from different quantities — the invocation count versus the ladder's shape — so a paper reporting only the second would be describing the smaller of the two problems.

We report counts rather than a proportion with a confidence interval because these rows are not a sample: they are every row in the day. The uncertainty here is not sampling uncertainty within the day; it is whether the day stands for anything beyond itself, which no interval computed on these rows can answer, and we decline to dress it as one.

## 5 Limit two: the crossover, and the prior it refuted

The timeout is set by an operator, so the interesting question is not whether *some* timeout makes the report wrong but where the boundary sits as the timeout is relaxed. We fixed a grid of multipliers before looking — each row's timeout is a multiple of that row's own median, so the timeout does not depend on the quantity under test:

    T = k * median of the row,   k in 2, 4, 8, 16, 32.

Fixing the grid in advance matters. The obvious alternative — evaluate at `T` equal to the row's own 99th percentile — makes `c = 1 - q` hold by construction, so the boundary case is decided by the choice of grid rather than by the data; it is an identity wearing a measurement's clothes. Our first registered prior did that too, and it is recorded in Section 7.

| timeout | binds (% of rows) | `c` median | `c` 90th pct | understated, median | understated, 90th pct |
|---|---|---|---|---|---|
| 2x median | **57.52%** | 0.1472 | 0.4057 | 4.24x | 61.57x |
| 4x median | 41.22% | 0 | 0.2492 | 3.83x | 69.54x |
| 8x median | 28.46% | 0 | 0.2314 | 3.45x | 69.61x |
| 16x median | 18.91% | 0 | 0.1842 | 3.26x | 58.32x |
| 32x median | **12.24%** | 0 | 0.0847 | 3.06x | 35.38x |

"Binds" means the true quantile falls outside the set the harness can identify, `c > 1 - q`. "Understated" is the ratio of the true quantile to the printed one, taken **only on the rows where the boundary binds** — this restriction is not cosmetic. On a row whose timeout sits above its top knot nothing is censored, the printed number equals the truth, and a ratio averaged over all identified rows is a column of exactly one that says nothing about anything. We made that mistake and the corrected column is what the table reports.

The refuted prior is the last row. It predicted under 10% of rows would still bind at 32x; the measurement is 12.24%, so the prediction failed. What makes the failure interesting is the reason it is not merely a calibration error: at a timeout of thirty-two times the median, on a workload whose median row records a handful of invocations, the harness still cannot identify the quantile for one row in eight, and there it understates by a median 3.06x. The decay from 57.52% to 12.24% — a fall of 45.28 percentage points across a sixteen-fold relaxation — is slower than the intuition that a generous timeout makes censoring irrelevant.

That shape is what the extreme-value literature would predict, though we do not fit a tail model and do not claim one. The behaviour of exceedances over a high threshold is what peak-over-threshold methods were built to describe [74,75,76,77], the limiting laws for maxima are classical [78,79], and the estimation of the tail index and of high quantiles from few exceedances is well developed [80,81,82,83,84,85,86], including the rare-event simulation machinery for when the events are too rare to sample directly [87,88] and the theory of records for the maxima themselves [89]. Our contribution is not a tail estimator. It is the observation that a threshold set for *configuration* reasons can be read as a censoring threshold, and that the correct report of a conditional quantile is conditioned on the threshold it was computed under.

Two controls run on every execution of the measurement, and both hold. With the timeout placed above each row's own maximum, the quantile is identified and the printed number equals the truth on 5,000 of 5,000 rows tested (100%): if that ever stopped holding, the instrument would be broken rather than the data. And the degenerate class the cost law predicts does appear in real data: 11,972 rows (25.2%) have no dynamic range at all, with `p100` equal to `p50`. A further 12,664 rows (26.66%) are certified by a single timeout level, which is the same set only up to the precision one asks for — the two counts differ by every row whose range is non-trivial but smaller than the requested precision, and reporting one number in place of both would be a label that lies about its own set.

## 6 Limit three: what certifying the quantile costs

If an operator wants to certify a quantile to relative precision `eps` by choosing a timeout, and only the timeout is available as a dial, the number of distinct timeout levels needed is a property of the range the quantile spans:

    K = ceil(log R / log(1 + eps)),   R = p100 / p50.

The law is deliberately crude and deliberately conservative. It counts levels, not invocations, and it therefore answers the question "how many experiments does certifying this cost" rather than "how much traffic does it need" — the second is the sample-count limit of Section 4. Its degenerate endpoint is what keeps it honest: at `R = 1` it returns one level, because a workload with no range is certified by a single timeout.

| precision | `K` median | `K` 90th pct | `K` max | rows certified by one level |
|---|---|---|---|---|
| 5% | **25** | 98 | 259 | 26.66% |
| 10% | 13 | 50 | 133 | 27.81% |
| 20% | 7 | 26 | 70 | 29.88% |

The ranges behind these counts are wide: `R` has median 3.33, 90th percentile 114.1, and maximum 300241. Because each `R` is a ratio of two percentiles of the interval mean, both counts are **lower bounds** on what the invocation-level workload would require — averaging inside the interval compresses the range it is computed from.

The queueing picture supplies the intuition for why a tail is worth this much attention even when its median behaviour is tame: in heavy traffic the waiting-time distribution is governed by the normalisation of the arrival and service processes rather than by their detailed laws [90,91], the many-server regime has its own limit theory [92,93], and the approximations practitioners actually use for multi-server queues are explicit about the regime in which they hold [94,95,96]. None of this is needed to compute `K`; it is needed to see that a tail quantile is not a small correction to a mean.

Two further bodies of work keep the cost claim from being over-read. Estimating a quantile from a *simulation* has its own run-length and variance questions, and the answers depend on the output process being stationary in a sense a production trace does not guarantee [97,98]. And treating a certification as a decision problem — what it is worth paying to narrow a set — is exactly the comparison of risk functions that decision theory formalises [99,100]; we compute the cost of certifying and leave the value of certifying to the operator.

## 7 Registered priors, evaluated limb by limb

The priors below were registered on the study's issue before the deciding run, together with the reason each was expected to hold. We report them as registered, including the one we withdrew, because a prior that is quietly edited after the fact is not a prior.

**P1 — the reported quantile is monotone in the timeout, and its spread across the grid exceeds the spread of repeated measurement.** The first limb is a theorem of the lemma and holds by construction; the self-test pins it. The second limb is **NOT RUN**, and the reason is not a missing dependency a reader could install. Recomputing the statistics on a fixed published table is deterministic: two independent passes over the same bytes agree exactly, so the "repeated-measurement spread" is zero by construction, and "the effect exceeds zero noise" is then either vacuous or a statement about rounding. Estimating that spread properly needs per-invocation latencies or replicated measurements of the same population; this table carries neither, because its percentiles are percentiles of a 30-second mean and one published day is one measurement. The honest verdict is *no information*, and `./reproduce.sh` reports it as `NOT RUN` on every run so that the package cannot claim it.

**P2 — most rows have a maximum at least twice their 99th percentile.  Withdrawn before the deciding run.** The prior was refuted by its own justification: the same registration recorded a measured median of about one for that ratio, which is a different statement from the one the threshold asserted. Worse, the ratio itself compares two quantities in different units — a single-invocation maximum over a percentile of the 30-second mean (Section 3) — so it is not a tail ratio at all. It was withdrawn in public on the issue, and replaced by P2′ below.

**P2′ — with the timeout set at a multiple of the row's own median, the fraction of rows whose quantile is unidentified is at least 50% at the smallest multiplier, and under 10% at the largest.** First limb **MET**: 57.52% at 2x. Second limb **UNMET**: 12.24% at 32x. The conjunction therefore fails, and we do not rescue it by reporting the limb that held: a conjunction is refuted by one false limb, and the false limb is the more informative of the two.

**P3 — certifying the median workload to 5% needs at least 20 timeout levels.** **MET**: the median is 25, with a 90th percentile of 98 across rows.

Reporting a refuted prior is only a novelty signal as far as the study could have detected the contrary. For P2′'s second limb the threshold was a share of rows, computed over every usable row in the day rather than over a sample of them, so there is no sampling error to compare against: the measured 12.24% is the value for this population of rows, not an estimate of it. What is uncertain is whether the population generalises — Section 9 — and that uncertainty is not something a confidence interval on these rows could express.

### What this study can and cannot detect

The study's sensitivity differs by quantity, and saying so is more useful than a single power figure.

For the shares reported in Sections 4 to 6 the "sample" is the entire day: 47,502 rows, every one measured. The quantities are therefore censuses of a finite population, and their sampling error is zero by construction. What they cannot answer is any question of the form "would another day, or another provider, show the same". The design has no second day and no second provider, so between-day and between-provider variation is not estimable here at all — not "small", not "large", *not estimated*. Any reader who needs that variation must supply a second trace, and we expect a reviewer to want it.

For the second limb of P1 the sensitivity is zero in a different sense: the denominator of the comparison is identically zero on this input, so no effect size, however large, could have been detected as exceeding it. This is why that limb is reported as no information rather than as support.

For the tail quantities themselves the binding constraint is not statistical but structural: the ladder has seven knots, so any quantile between knots is produced by the interpolation rule. The reconstruction cannot distinguish two distributions that agree at the knots, and an effect confined between two knots is invisible to this instrument regardless of how many rows are behind it. We state the ladder as part of the instrument rather than pretending the instrument is transparent.

## 8 Threats to validity

**The unit.** Every range reported here is a range of the 30-second interval mean. The invocation-level range is larger, by an amount this table cannot quantify, so the cost figures in Section 6 are lower bounds and the tail compression we measure is a lower bound on the compression at the invocation level. A reader who reads `R` as an invocation-level dynamic range will overestimate how cheap certification actually is.

**One trace, one day, one provider.** This is a case study and we do not generalise from it. The direction of the result — that a timeout leaves a quantile unidentified for a substantial share of workloads — is a consequence of the lemma and cannot be undone by another day; the magnitudes are properties of this workload and would move.

**The reconstruction is a model.** Piecewise-linear interpolation between seven knots is a choice. It is stated, applied identically to every row, and embedded in committed code [34,36], but a different reconstruction would move the crossover slightly. Since the lemma's boundary depends on the CDF evaluated at the timeout, and the CDF between knots is exactly what interpolation supplies, this is the most substantive modelling assumption in the paper.

**Determinism is not replication.** Our reproduction check proves that the same program on the same bytes yields the same numbers. That is a statement about the instrument, not about the world, and it is why the noise limb is reported as unmeasured rather than as passed — a confusion this literature has warned about for a long time [38,39,40,101].

**Rows we refused.** 2,226 of 49,728 rows could not be used, mostly because they report a zero median. Refusing them is a judgement: a zero median makes the ratio to the median undefined, and the alternative — substituting a small positive number — would manufacture a dynamic range where the data reports none. The share is small but not zero, and if zero-median rows are systematically the thinnest, their exclusion flatters the resolvable share slightly.

**Why it is still worth publishing.** Because the first limit is arithmetic and the report that ignores it is wrong in a direction the operator cannot see. A practitioner who reads this can compute, from their own invocation counts, how many of their reported percentiles are extrapolations; and can compute, from their own timeout and median, whether the boundary binds. Neither computation needs our data.

## 9 Related work, and what the estimand is in each case

Three lines of work are close enough that the difference has to be stated rather than assumed.

*Censoring and survival analysis.* Kaplan–Meier and its descendants estimate a distribution from right-censored observations and use the censoring information rather than discarding it [11,12,13,14,15]. Our estimand is the same object — a quantile of a partially observed distribution — but the deliverable differs: they produce an estimate, we report the region in which the estimate is unidentifiable and the condition under which it collapses. Relatedly, the engineering reliability literature uses censored data to plan tests and to certify lifetimes [102,103,104,105,106,107], which is the closest analogue of our certification cost, but its thresholds are physical failure times rather than a configuration dial.

*Partial identification.* The identified-set formulation here is that literature's object, applied to a latency quantile instead of a treatment effect [19,20,21,33,108,109,110,111,112,113,114,115]. The difference is that the set here is unbounded above and has a closed-form boundary in the observable fraction, so no inference machinery is needed; the contribution is the measurement of where the boundary falls on a real workload, not a new inference procedure. Where that literature exists because the data are intrinsically uninformative about a parameter, here the un-informativeness is *manufactured by a configuration setting*, which means it can be removed by changing the setting — a distinction with practical content that the econometric framing does not need to make.

*Tail latency in systems.* The systems literature on tail latency is about causes and mitigations: fan-out amplification, queueing, interference, and the techniques that bound them [1,2,3,44]. Its measurements are usually made with a timeout in place, and the reporting convention rarely says which one. Our claim is compatible with all of it and constrains none of it: we are not saying tails are smaller than reported, we are saying that for a computable set of workloads the reported number does not identify the quantity it names, and that the set is large in a public trace.

Two studies in this journal touch the same sentence — "a count is not a property of the system" — with different estimands, and the difference is worth making explicit. The probe-count study (`#135`) asks what a *probe* count determines about the object being probed: its count is a property of the measurement schedule, and the estimand is the quantity the probes are meant to certify. The proof-cost study (`#139`) asks what certifying an invariant costs in *proof steps*: its count is work, and the estimand is the shortest certificate. Ours counts timeout levels, and the estimand is a tail quantile of a partially observed distribution. All three refuse to read a count as a fact about the system, and all three differ in what the count is a count of — which is why citing either as precedent for the other would be a category error rather than a comparison.

Distributed systems studies of *failure* supply the reason the timeout exists at all, and the reason it is usually set generously: silent failures and retry storms are the events one is defending against [10], and the diagnosis tooling for such systems has its own measurement burden [116,117,118,119,120]. Nothing in that literature depends on our result, but every deployment it describes is exposed to it.

## What changes, and what does not

If this is true, three beliefs change, and each changes a decision.

A reported high quantile is not automatically a measurement of the tail; it is a measurement of the tail *conditioned on a threshold*, and the conditioning has to be reported with it. The decision that follows is a reporting one: state the timeout, or state that the quantile may be unidentified.

A generous timeout is not a conservative one. At 32x the median, on this workload, one row in eight still has an unidentifiable quantile, and there it is understated by a median 3.06x. The decision that follows is operational: a timeout chosen for safety does not thereby make the latency report safe.

Thin workloads cannot report tails at all, and the share is not marginal: 65.65% of usable rows in this day cannot resolve their own 99th percentile at any timeout. The decision that follows is architectural: a per-function tail objective on a function invoked a few dozen times a day is a control that cannot be evaluated, and a monitoring system that prints one anyway is printing an extrapolation.

Each of these is a bound a practitioner can recompute for their own system from two numbers they already have — their invocation count and their timeout as a multiple of their median. That is the sense in which the result is meant to be useful: not as a fact about one trace, but as arithmetic that was missing from a report.

## Availability

The instrument, the committed input and every number in this paper are in this directory. `./reproduce.sh` runs the six steps that re-derive them and prints its verdict; a `NOT RUN` step means a claim the data cannot carry, and the package is designed so that verdict can never read as though that number had been reproduced.

## References

[1] Dean, J.; Barroso, L. A. (2013). The tail at scale. Communications of the ACM. vol. 56. pp. 74-80. https://doi.org/10.1145/2408776.2408794

[2] Barroso, L.; Dean, J.; Holzle, U. (2003). Web search for a planet: the google cluster architecture. IEEE Micro. vol. 23. pp. 22-28. https://doi.org/10.1109/mm.2003.1196112

[3] Armbrust, M.; Fox, A.; Griffith, R.; et al. (2010). A view of cloud computing. Communications of the ACM. vol. 53. pp. 50-58. https://doi.org/10.1145/1721654.1721672

[4] Mohammad Shahrad; Rodrigo Fonseca; Íñigo Goiri; et al. (2020). Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider. arXiv preprint 2003.03423v3. http://arxiv.org/abs/2003.03423v3

[5] Eric Jonas; Johann Schleier-Smith; Vikram Sreekanti; et al. (2019). Cloud Programming Simplified: A Berkeley View on Serverless Computing. arXiv preprint 1902.03383v1. http://arxiv.org/abs/1902.03383v1

[6] Joseph M. Hellerstein; Jose Faleiro; Joseph E. Gonzalez; et al. (2018). Serverless Computing: One Step Forward, Two Steps Back. arXiv preprint 1812.03651v1. http://arxiv.org/abs/1812.03651v1

[7] McGrath, G.; Brenner, P. R. (2017). Serverless Computing: Design, Implementation, and Performance. 2017 IEEE 37th International Conference on Distributed Computing Systems Workshops (ICDCSW). pp. 405-410. https://doi.org/10.1109/icdcsw.2017.36

[8] Lloyd, W.; Ramesh, S.; Chinthalapati, S.; et al. (2018). Serverless Computing: An Investigation of Factors Influencing Microservice Performance. 2018 IEEE International Conference on Cloud Engineering (IC2E). pp. 159-169. https://doi.org/10.1109/ic2e.2018.00039

[9] Eivy, A.; Weinman, J. (2017). Be Wary of the Economics of "Serverless" Cloud Computing. IEEE Cloud Computing. vol. 4. pp. 6-12. https://doi.org/10.1109/mcc.2017.32

[10] Bronson, N.; Aghayev, A.; Charapko, A.; et al. (2021). Metastable failures in distributed systems. Proceedings of the Workshop on Hot Topics in Operating Systems. pp. 221-227. https://doi.org/10.1145/3458336.3465286

[11] Kaplan, E. L.; Meier, P. (1958). Nonparametric Estimation from Incomplete Observations. Journal of the American Statistical Association. vol. 53. pp. 457-481. https://doi.org/10.1080/01621459.1958.10501452

[12] Cox, D. R. (1972). Regression Models and Life-Tables. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 34. pp. 187-202. https://doi.org/10.1111/j.2517-6161.1972.tb00899.x

[13] Turnbull, B. W. (1976). The Empirical Distribution Function with Arbitrarily Grouped, Censored and Truncated Data. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 38. pp. 290-295. https://doi.org/10.1111/j.2517-6161.1976.tb01597.x

[14] Lagakos, S. W. (1979). General Right Censoring and Its Impact on the Analysis of Survival Data. Biometrics. vol. 35. pp. 139. https://doi.org/10.2307/2529941

[15] GENTLEMAN, R.; GEYER, C. J. (1994). Maximum likelihood for interval censored data: Consistency and computation. Biometrika. vol. 81. pp. 618-623. https://doi.org/10.1093/biomet/81.3.618

[16] Woodroofe, M. (1985). Estimating a Distribution Function with Truncated Data. The Annals of Statistics. vol. 13. pp. 163-177. https://doi.org/10.1214/aos/1176346584

[17] Kalbfleisch, J. D.; Prentice, R. L. (2002). The Statistical Analysis of Failure Time Data. Wiley Series in Probability and Statistics. https://doi.org/10.1002/9781118032985

[18] Lawless, J. F. (2002). Statistical Models and Methods for Lifetime Data. Wiley Series in Probability and Statistics. https://doi.org/10.1002/9781118033005

[19] (2003). Partial Identification of Probability Distributions. Springer Series in Statistics. https://doi.org/10.1007/b97478

[20] Manski, C. F. (None). partial identification in econometrics. The New Palgrave Dictionary of Economics. pp. 300-306. https://doi.org/10.1057/9780230226203.1251

[21] (2020). Microeconometrics with partial identification. Handbook of Econometrics. pp. 355-486. https://doi.org/10.1016/bs.hoe.2020.05.002

[22] Wilks, S. S. (1941). Determination of Sample Sizes for Setting Tolerance Limits. The Annals of Mathematical Statistics. vol. 12. pp. 91-96. https://doi.org/10.1214/aoms/1177731788

[23] (None). Order Statistics. SpringerReference. https://doi.org/10.1007/springerreference_65446

[24] Wald, A. (1943). An Extension of Wilks' Method for Setting Tolerance Limits. The Annals of Mathematical Statistics. vol. 14. pp. 45-55. https://doi.org/10.1214/aoms/1177731491

[25] Bahadur, R. R. (1966). A Note on Quantiles in Large Samples. The Annals of Mathematical Statistics. vol. 37. pp. 577-580. https://doi.org/10.1214/aoms/1177699450

[26] Box, G. E. P. (1976). Science and Statistics. Journal of the American Statistical Association. vol. 71. pp. 791-799. https://doi.org/10.1080/01621459.1976.10480949

[27] Tukey, J. W. (1962). The Future of Data Analysis. The Annals of Mathematical Statistics. vol. 33. pp. 1-67. https://doi.org/10.1214/aoms/1177704711

[28] Heitjan, D. F.; Rubin, D. B. (1991). Ignorability and Coarse Data. The Annals of Statistics. vol. 19. pp. 2244-2253. https://doi.org/10.1214/aos/1176348396

[29] RUBIN, D. B. (1976). Inference and missing data. Biometrika. vol. 63. pp. 581-592. https://doi.org/10.1093/biomet/63.3.581

[30] (2006). Semiparametric Theory and Missing Data. Springer Series in Statistics. https://doi.org/10.1007/0-387-37345-4

[31] Andersen, P. K.; Gill, R. D. (1982). Cox's Regression Model for Counting Processes: A Large Sample Study. The Annals of Statistics. vol. 10. pp. 1100-1120. https://doi.org/10.1214/aos/1176345976

[32] Andersen, P. K.; Borgan, Ø.; Gill, R. D.; et al. (1993). Statistical Models Based on Counting Processes. Springer Series in Statistics. https://doi.org/10.1007/978-1-4612-4348-9

[33] Manski, C. F.; Imbens, G. (2003). Confidence intervals for partially identified parameters. Working Paper Series. https://doi.org/10.1920/wp.cem.2003.0903

[34] David, H. A.; Nagaraja, H. N. (2003). Order Statistics. Wiley Series in Probability and Statistics. https://doi.org/10.1002/0471722162

[35] Arnold, B. C.; Balakrishnan, N.; Nagaraja, H. N. (2008). A First Course in Order Statistics. https://doi.org/10.1137/1.9780898719062

[36] Reiss, R. D. (1989). Approximate Distributions of Order Statistics. Springer Series in Statistics. https://doi.org/10.1007/978-1-4613-9620-8

[37] Calzarossa, M.; Serazzi, G. (1993). Workload characterization: a survey. Proceedings of the IEEE. vol. 81. pp. 1136-1150. https://doi.org/10.1109/5.236191

[38] Mytkowicz, T.; Diwan, A.; Hauswirth, M.; et al. (2009). Producing wrong data without doing anything obviously wrong!. ACM SIGPLAN Notices. vol. 44. pp. 265-276. https://doi.org/10.1145/1508284.1508275

[39] Georges, A.; Buytaert, D.; Eeckhout, L. (2007). Statistically rigorous java performance evaluation. Proceedings of the 22nd annual ACM SIGPLAN conference on Object-oriented programming systems, languages and applications. pp. 57-76. https://doi.org/10.1145/1297027.1297033

[40] Hoefler, T.; Belli, R. (2015). Scientific benchmarking of parallel computing systems. Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis. pp. 1-12. https://doi.org/10.1145/2807591.2807644

[41] Verma, A.; Pedrosa, L.; Korupolu, M.; et al. (2015). Large-scale cluster management at Google with Borg. Proceedings of the Tenth European Conference on Computer Systems. pp. 1-17. https://doi.org/10.1145/2741948.2741964

[42] Bodik, P.; Fox, A.; Franklin, M. J.; et al. (2010). Characterizing, modeling, and generating workload spikes for stateful services. Proceedings of the 1st ACM symposium on Cloud computing. pp. 241-252. https://doi.org/10.1145/1807128.1807166

[43] Benson, T.; Akella, A.; Maltz, D. A. (2010). Network traffic characteristics of data centers in the wild. Proceedings of the 10th ACM SIGCOMM conference on Internet measurement. pp. 267-280. https://doi.org/10.1145/1879141.1879175

[44] Kanev, S.; Darago, J. P.; Hazelwood, K.; et al. (2015). Profiling a warehouse-scale computer. ACM SIGARCH Computer Architecture News. vol. 43. pp. 158-169. https://doi.org/10.1145/2872887.2750392

[45] Leitner, P.; Cito, J. (2016). Patterns in the Chaos—A Study of Performance Variation and Predictability in Public IaaS Clouds. ACM Transactions on Internet Technology. vol. 16. pp. 1-23. https://doi.org/10.1145/2885497

[46] Lenk, A.; Menzel, M.; Lipsky, J.; et al. (2011). What Are You Paying For? Performance Benchmarking for Infrastructure-as-a-Service Offerings. 2011 IEEE 4th International Conference on Cloud Computing. pp. 484-491. https://doi.org/10.1109/cloud.2011.80

[47] Iosup, A.; Ostermann, S.; Yigitbasi, M. N.; et al. (2011). Performance Analysis of Cloud Computing Services for Many-Tasks Scientific Computing. IEEE Transactions on Parallel and Distributed Systems. vol. 22. pp. 931-945. https://doi.org/10.1109/tpds.2011.66

[48] Mosteller, F. (1946). On Some Useful "Inefficient" Statistics. The Annals of Mathematical Statistics. vol. 17. pp. 377-408. https://doi.org/10.1214/aoms/1177730881

[49] Stigler, S. M. (1973). The Asymptotic Distribution of the Trimmed Mean. The Annals of Statistics. vol. 1. pp. 472-477. https://doi.org/10.1214/aos/1176342412

[50] Serfling, R. J. (1980). Approximation Theorems of Mathematical Statistics. Wiley Series in Probability and Statistics. https://doi.org/10.1002/9780470316481

[51] Chen, S. X.; Hall, P. (1993). Smoothed Empirical Likelihood Confidence Intervals for Quantiles. The Annals of Statistics. vol. 21. pp. 1166-1181. https://doi.org/10.1214/aos/1176349256

[52] Koenker, R.; Bassett, G. (1978). Regression Quantiles. Econometrica. vol. 46. pp. 33. https://doi.org/10.2307/1913643

[53] Dvoretzky, A.; Kiefer, J.; Wolfowitz, J. (1956). Asymptotic Minimax Character of the Sample Distribution Function and of the Classical Multinomial Estimator. The Annals of Mathematical Statistics. vol. 27. pp. 642-669. https://doi.org/10.1214/aoms/1177728174

[54] Massart, P. (1990). The Tight Constant in the Dvoretzky-Kiefer-Wolfowitz Inequality. The Annals of Probability. vol. 18. pp. 1269-1283. https://doi.org/10.1214/aop/1176990746

[55] Anderson, T. W.; Darling, D. A. (1952). Asymptotic Theory of Certain "Goodness of Fit" Criteria Based on Stochastic Processes. The Annals of Mathematical Statistics. vol. 23. pp. 193-212. https://doi.org/10.1214/aoms/1177729437

[56] van der Vaart, A. W.; Wellner, J. A. (1996). Weak Convergence and Empirical Processes. Springer Series in Statistics. https://doi.org/10.1007/978-1-4757-2545-2

[57] Rao, C. R. (1973). Linear Statistical Inference and its Applications. Wiley Series in Probability and Statistics. https://doi.org/10.1002/9780470316436

[58] Hoeffding, W. (1963). Probability Inequalities for Sums of Bounded Random Variables. Journal of the American Statistical Association. vol. 58. pp. 13-30. https://doi.org/10.1080/01621459.1963.10500830

[59] Wilson, E. B. (1927). Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association. vol. 22. pp. 209-212. https://doi.org/10.1080/01621459.1927.10502953

[60] CLOPPER, C. J.; PEARSON, E. S. (1934). THE USE OF CONFIDENCE OR FIDUCIAL LIMITS ILLUSTRATED IN THE CASE OF THE BINOMIAL. Biometrika. vol. 26. pp. 404-413. https://doi.org/10.1093/biomet/26.4.404

[61] Brown, L. D.; Cai, T. T.; DasGupta, A. (2001). Interval Estimation for a Binomial Proportion. Statistical Science. vol. 16. pp. 101-133. https://doi.org/10.1214/ss/1009213286

[62] Agresti, A.; Coull, B. A. (1998). Approximate Is Better than "Exact" for Interval Estimation of Binomial Proportions. The American Statistician. vol. 52. pp. 119. https://doi.org/10.2307/2685469

[63] Newcombe, R. G. (1998). Two-sided confidence intervals for the single proportion: comparison of seven methods. Statistics in Medicine. vol. 17. pp. 857-872. https://doi.org/10.1002/(sici)1097-0258(19980430)17:8<857::aid-sim777>3.0.co;2-e

[64] Efron, B. (1979). Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics. vol. 7. pp. 1-26. https://doi.org/10.1214/aos/1176344552

[65] Efron, B. (1987). Better Bootstrap Confidence Intervals. Journal of the American Statistical Association. vol. 82. pp. 171-185. https://doi.org/10.1080/01621459.1987.10478410

[66] Efron, B.; Tibshirani, R. (1994). An Introduction to the Bootstrap. https://doi.org/10.1201/9780429246593

[67] Bickel, P. J.; Freedman, D. A. (1981). Some Asymptotic Theory for the Bootstrap. The Annals of Statistics. vol. 9. pp. 1196-1217. https://doi.org/10.1214/aos/1176345637

[68] Singh, K. (1981). On the Asymptotic Accuracy of Efron's Bootstrap. The Annals of Statistics. vol. 9. pp. 1187-1195. https://doi.org/10.1214/aos/1176345636

[69] Beran, R. (1982). Estimated Sampling Distributions: The Bootstrap and Competitors. The Annals of Statistics. vol. 10. pp. 212-225. https://doi.org/10.1214/aos/1176345704

[70] Beran, R. (1987). Prepivoting to Reduce Level Error of Confidence Sets. Biometrika. vol. 74. pp. 457. https://doi.org/10.2307/2336685

[71] Diciccio, T. J.; Romano, J. P. (1988). A Review of Bootstrap Confidence Intervals. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 50. pp. 338-354. https://doi.org/10.1111/j.2517-6161.1988.tb01732.x

[72] Hall, P. (1986). On the Number of Bootstrap Simulations Required to Construct a Confidence Interval. The Annals of Statistics. vol. 14. pp. 1453-1462. https://doi.org/10.1214/aos/1176350169

[73] (2006). Sampling Algorithms. Springer Series in Statistics. https://doi.org/10.1007/0-387-34240-0

[74] III, J. P. (1975). Statistical Inference Using Extreme Order Statistics. The Annals of Statistics. vol. 3. pp. 119-131. https://doi.org/10.1214/aos/1176343003

[75] Balkema, A. A.; de Haan, L. (1974). Residual Life Time at Great Age. The Annals of Probability. vol. 2. pp. 792-804. https://doi.org/10.1214/aop/1176996548

[76] Davison, A. C.; Smith, R. L. (1990). Models for Exceedances Over High Thresholds. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 52. pp. 393-425. https://doi.org/10.1111/j.2517-6161.1990.tb01796.x

[77] Davison, A. C. (1984). Modelling Excesses over High Thresholds, with an Application. Statistical Extremes and Applications. pp. 461-482. https://doi.org/10.1007/978-94-017-3069-3_34

[78] Fisher, R. A.; Tippett, L. H. C. (1928). Limiting forms of the frequency distribution of the largest or smallest member of a sample. Mathematical Proceedings of the Cambridge Philosophical Society. vol. 24. pp. 180-190. https://doi.org/10.1017/s0305004100015681

[79] Gnedenko, B. (1943). Sur La Distribution Limite Du Terme Maximum D'Une Serie Aleatoire. The Annals of Mathematics. vol. 44. pp. 423. https://doi.org/10.2307/1968974

[80] Smith, R. L. (1987). Estimating Tails of Probability Distributions. The Annals of Statistics. vol. 15. pp. 1174-1207. https://doi.org/10.1214/aos/1176350499

[81] Hosking, J. R.; Wallis, J. R. (1987). Parameter and Quantile Estimation for the Generalized Pareto Distribution. Technometrics. vol. 29. pp. 339-349. https://doi.org/10.1080/00401706.1987.10488243

[82] Hosking, J. R. M. (1990). L-Moments: Analysis and Estimation of Distributions Using Linear Combinations of Order Statistics. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 52. pp. 105-124. https://doi.org/10.1111/j.2517-6161.1990.tb01775.x

[83] Grimshaw, S. D. (1993). Computing Maximum Likelihood Estimates for the Generalized Pareto Distribution. Technometrics. vol. 35. pp. 185-191. https://doi.org/10.1080/00401706.1993.10485040

[84] Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer Series in Statistics. https://doi.org/10.1007/978-1-4471-3675-0

[85] Gumbel, E. J. (1958). Statistics of Extremes. https://doi.org/10.7312/gumb92958

[86] Katz, R. W.; Parlange, M. B.; Naveau, P. (2002). Statistics of extremes in hydrology. Advances in Water Resources. vol. 25. pp. 1287-1304. https://doi.org/10.1016/s0309-1708(02)00056-8

[87] Glasserman, P.; Heidelberger, P.; Shahabuddin, P. (2000). Variance Reduction Techniques for Estimating Value-at-Risk. Management Science. vol. 46. pp. 1349-1364. https://doi.org/10.1287/mnsc.46.10.1349.12274

[88] (2009). Rare Event Simulation using Monte Carlo Methods. https://doi.org/10.1002/9780470745403

[89] Arnold, B. C.; Balakrishnan, N.; Nagaraja, H. N. (1998). Records. Wiley Series in Probability and Statistics. https://doi.org/10.1002/9781118150412

[90] Kingman, J. F. C. (1961). The single server queue in heavy traffic. Mathematical Proceedings of the Cambridge Philosophical Society. vol. 57. pp. 902-904. https://doi.org/10.1017/s0305004100036094

[91] Kingman, J. F. C. (1962). On Queues in Heavy Traffic. Journal of the Royal Statistical Society Series B: Statistical Methodology. vol. 24. pp. 383-392. https://doi.org/10.1111/j.2517-6161.1962.tb00465.x

[92] Halfin, S.; Whitt, W. (1981). Heavy-Traffic Limits for Queues with Many Exponential Servers. Operations Research. vol. 29. pp. 567-588. https://doi.org/10.1287/opre.29.3.567

[93] Reiman, M. I. (1984). Open Queueing Networks in Heavy Traffic. Mathematics of Operations Research. vol. 9. pp. 441-458. https://doi.org/10.1287/moor.9.3.441

[94] WHITT, W. (1993). APPROXIMATIONS FOR THE GI/G/m QUEUE. Production and Operations Management. vol. 2. pp. 114-161. https://doi.org/10.1111/j.1937-5956.1993.tb00094.x

[95] Abate, J.; Whitt, W. (1992). The Fourier-series method for inverting transforms of probability distributions. Queueing Systems. vol. 10. pp. 5-87. https://doi.org/10.1007/bf01158520

[96] Harchol-Balter, M. (2013). Performance Modeling and Design of Computer Systems. https://doi.org/10.1017/cbo9781139226424

[97] Law, A. M. (1983). Feature Article—Statistical Analysis of Simulation Output Data. Operations Research. vol. 31. pp. 983-1029. https://doi.org/10.1287/opre.31.6.983

[98] Heidelberger, P.; Welch, P. D. (1981). A spectral method for confidence interval generation and run length control in simulations. Communications of the ACM. vol. 24. pp. 233-245. https://doi.org/10.1145/358598.358630

[99] (1998). Theory of Point Estimation. Springer Texts in Statistics. https://doi.org/10.1007/b98854

[100] Berger, J. O. (1985). Statistical Decision Theory and Bayesian Analysis. Springer Series in Statistics. https://doi.org/10.1007/978-1-4757-4286-2

[101] Kohavi, R.; Deng, A.; Frasca, B.; et al. (2013). Online controlled experiments at large scale. Proceedings of the 19th ACM SIGKDD international conference on Knowledge discovery and data mining. pp. 1168-1176. https://doi.org/10.1145/2487575.2488217

[102] Escobar, L. A.; Meeker, W. Q. (2006). A Review of Accelerated Test Models. Statistical Science. vol. 21. pp. 552-577. https://doi.org/10.1214/088342306000000321

[103] Nelson, W. (1982). Applied Life Data Analysis. Wiley Series in Probability and Statistics. https://doi.org/10.1002/0471725234

[104] (2006). Dynamic Regression Models for Survival Data. Statistics for Biology and Health. https://doi.org/10.1007/0-387-33960-4

[105] Prentice, R. L.; Kalbfleisch, J. D.; Peterson, A. V.; et al. (1978). The Analysis of Failure Times in the Presence of Competing Risks. Biometrics. vol. 34. pp. 541. https://doi.org/10.2307/2530374

[106] Efron, B. (1988). Logistic Regression, Survival Analysis, and the Kaplan-Meier Curve. Journal of the American Statistical Association. vol. 83. pp. 414-425. https://doi.org/10.1080/01621459.1988.10478612

[107] Lin, D. Y.; Wei, L. J. (1989). The Robust Inference for the Cox Proportional Hazards Model. Journal of the American Statistical Association. vol. 84. pp. 1074-1078. https://doi.org/10.1080/01621459.1989.10478874

[108] Chernozhukov, V.; Hong, H.; Tamer, E. (2007). Estimation and Confidence Regions for Parameter Sets in Econometric Models. Econometrica. vol. 75. pp. 1243-1284. https://doi.org/10.1111/j.1468-0262.2007.00794.x

[109] (2010). Inference for Parameters Defined by Moment Inequalities Using Generalized Moment Selection. Econometrica. vol. 78. pp. 119-157. https://doi.org/10.3982/ecta7502

[110] Romano, J. P.; Shaikh, A. M. (2008). Inference for identifiable parameters in partially identified econometric models. Journal of Statistical Planning and Inference. vol. 138. pp. 2786-2807. https://doi.org/10.1016/j.jspi.2008.03.015

[111] (2010). Bootstrap Inference in Partially Identified Models Defined by Moment Inequalities: Coverage of the Identified Set. Econometrica. vol. 78. pp. 735-753. https://doi.org/10.3982/ecta8056

[112] Newey, W. K.; McFadden, D. (1994). Chapter 36 Large sample estimation and hypothesis testing. Handbook of Econometrics. pp. 2111-2245. https://doi.org/10.1016/s1573-4412(05)80005-4

[113] Manski, C. F. (2007). PARTIAL IDENTIFICATION OF COUNTERFACTUAL CHOICE PROBABILITIES*. International Economic Review. vol. 48. pp. 1393-1410. https://doi.org/10.1111/j.1468-2354.2007.00467.x

[114] Horowitz, J. L.; Manski, C. F. (2000). Nonparametric Analysis of Randomized Experiments with Missing Covariate and Outcome Data. Journal of the American Statistical Association. vol. 95. pp. 77-84. https://doi.org/10.1080/01621459.2000.10473902

[115] Rosenbaum, P. R. (2002). Observational Studies. Springer Series in Statistics. https://doi.org/10.1007/978-1-4757-3692-2

[116] Gunawi, H. S.; Hao, M.; Leesatapornwongsa, T.; et al. (2014). What Bugs Live in the Cloud? A Study of 3000+ Issues in Cloud Systems. Proceedings of the ACM Symposium on Cloud Computing. pp. 1-14. https://doi.org/10.1145/2670979.2670986

[117] Ousterhout, J.; Gopalan, A.; Gupta, A.; et al. (2015). The RAMCloud Storage System. ACM Transactions on Computer Systems. vol. 33. pp. 1-55. https://doi.org/10.1145/2806887

[118] Ousterhout, J.; Agrawal, P.; Erickson, D.; et al. (2011). The case for RAMCloud. Communications of the ACM. vol. 54. pp. 121-130. https://doi.org/10.1145/1965724.1965751

[119] Smith, C. U.; Williams, L. G. (None). Software Performance Engineering. UML for Real. pp. 343-365. https://doi.org/10.1007/0-306-48738-1_16

[120] Woodside, M.; Franks, G.; Petriu, D. C. (2007). The Future of Software Performance Engineering. Future of Software Engineering (FOSE '07). pp. 171-187. https://doi.org/10.1109/fose.2007.32
