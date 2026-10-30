# The Timeout Is the Measurement

### What a timed-out tail leaves identifiable, and what certifying it costs

*A case study. One public trace, one day, and the estimand is the {{n:interval_s}}-second interval mean rather than the single invocation. Nothing below is claimed to hold of services in general.*

## Abstract

A latency harness reports a 99th percentile. If the harness also stops waiting at a timeout — as nearly every one does — then some fraction of requests have no latency value at all, and the number it prints is not the quantile it names. We treat that as an identification problem rather than a rounding problem, and ask three questions of one real workload: can the quantile be resolved at all, does the timeout bind, and what does certifying the quantile cost.

The first answer dominates. Of the {{n:usable}} function rows in the first day of the public Azure Functions trace that carry a usable quantile ladder, **{{n:resolvable_pct}}%** expect at least one observation above their own 99th percentile; the remaining **{{n:unresolvable_pct}}%** cannot resolve it at any timeout, because the quantile is a statement about the top of a distribution that the sample never reaches. {{n:below_100}} rows ({{n:below_100_pct}}%) record fewer than {{n:count_gate_lo}} invocations in a whole day. No amount of careful measurement repairs this: it is a property of how much data was collected, not of how it was analysed.

Second, with the timeout set at a fixed multiple of each row's own median, truncation binds — the true quantile falls outside the set the harness can identify — on **{{n:k2_binds_pct}}%** of rows at {{n:k2}}x the median, and still on **{{n:k32_binds_pct}}%** at {{n:k32}}x. Where it binds, the printed number sits below the truth by a median factor of **{{n:k2_under_median}}** at {{n:k2}}x and **{{n:k32_under_median}}** even at {{n:k32}}x. A registered prior predicted that under {{n:prior_limb2_pct}}% of rows would still bind at {{n:k32}}x. The data says otherwise, and that refutation is the sharpest result in this paper.

Third, certifying the quantile to {{n:eps5}}% relative precision by timeout levels alone needs a median of **{{n:K5_median}}** distinct levels on this workload, and {{n:K5_p90}} at the {{n:p90}}th percentile of rows.

Throughout, the unit is the **{{n:interval_s}}-second interval mean**, not the single invocation: the trace publishes percentiles of a 30-second average, so every range reported here ranges over a smoothed quantity and is therefore a **lower bound** on the invocation-level range. All numbers come from one program and one committed input; `./reproduce.sh` re-derives them.

## 1 The number a timeout leaves

Tail latency is a design constraint rather than a curiosity: the slowest requests set the fan-out cost of any request that must wait for all of its shards, so a single slow component can dominate the response time of a system built from fast ones {{c:dean-barroso-2013,barroso-2003,armbrust-2010}}. The operational literature therefore treats a high quantile of the latency distribution as a service-level objective, and the entire vocabulary of tail tolerance is built on the assumption that the quantile is measurable {{c:dean-barroso-2013}}.

Serverless platforms sharpen the problem. Workloads there are bursty, short and heterogeneous, with a heavy share of functions invoked too rarely to accumulate much of a sample {{c:shahrad-serverless-wild-2020,jonas-berkeley-serverless-2019,hellerstein-serverless-2019,mcgrath-2017,lloyd-2018,eivy-2017}}. A timeout is not optional in that setting: it is the only thing bounding a request whose dependency is silently broken, and the retry that follows a timeout is what turns a slow dependency into a metastable outage {{c:bronson-metastable-2021}}.

So the measurement instrument and the safety mechanism are the same mechanism, and it is worth asking what it does to the number it produces.

The statistics of incomplete observation are old and precise. Right-censoring is the standard case in survival analysis: an observation that has not failed by the end of the study is not missing, it is *known to exceed* a bound, and the Kaplan–Meier estimator is the canonical use of that information {{c:kaplan-meier-1958,cox-1972,turnbull-1976}}. General censoring mechanisms, interval censoring, truncation, and the conditions under which the incomplete-data likelihood may be treated as ignorable have all been worked out {{c:lagakos-1979,gentleman-geyer-1994,woodroofe-1985,kalbfleisch-prentice-2002,lawless-2003}}. What has not travelled is the consequence for a *report*, as opposed to for an estimate: when the censoring is heavy enough, the quantity the report names is not identified by the data at all, and the correct output is a set rather than a point.

That distinction is the daily business of the partial-identification literature, where the object of interest is an identified set and the question is what can be concluded without a point-identifying assumption {{c:manski-2003,tamer-2010,molinari-2020}}. The specific arithmetic of "how large a sample do I need before a high quantile means anything" appears in the older literature on tolerance limits and sample quantiles {{c:wilks-1941,wilks-1948,wald-1943,bahadur-1966}}. Our contribution is none of these pieces. It is to put them together on a real workload and report, as a measurement, where the boundary sits — and to be explicit that a report made without that boundary in view is not a conservative report but an unlabelled one.

The frame throughout is measurement as a statistical act rather than a plumbing act: a number produced by an instrument is a claim about a population, and it deserves the scrutiny of any other inference {{c:box-1976,tukey-1962}}.

## 2 The object, and the lemma that fixes it

A harness observes a latency `X` and stops at a timeout `T`. Write `c` for the fraction of requests that time out. What the harness has is not a sample of `X` but a sample of `X` conditioned on `X <= T`, whose distribution function is `F(x)/F(T)` on `[0, T]`. Requests above `T` are not missing at random in the ordinary sense; they are known to exceed `T` {{c:heitjan-rubin-1991,rubin-1976,tsiatis-2006}}. The information they carry is real but bounded, and the bound is what matters here.

The true `q`-quantile is identified exactly when `q <= F(T)`, that is when

    c <= 1 - q.

When that fails, the true quantile lies strictly above `T`, the identified set is the interval `(T, inf)`, and no volume of traffic narrows it: the missing mass is missing, not noisy. This is the survival-analytic statement that a quantile beyond the observable range is not estimable from the observations alone {{c:kalbfleisch-prentice-2002,lawless-2003,andersen-gill-1982,andersen-borgan-gill-keiding-1993}}, and equally the partial-identification bound on a distribution's upper tail {{c:manski-2003,tamer-2010,molinari-2020,imbens-manski-2004}}. Its computational content for our purpose is small and exact, which is why the instrument is a few dozen lines of arithmetic rather than a fitting procedure.

Two consequences follow, and the second is the one that bites.

First, what the harness *prints* when the quantile is unidentified is the `q`-quantile of the truncated sample, which is `q * F(T)` in the original distribution's own coordinates. That number is strictly below `T`, and `T` is strictly below the whole set the data cannot rule out. So the printed value is not merely uncertain: it is biased downward by an amount that grows as the timeout tightens, and it is presented with no indication that anything is wrong.

Second, being *identified* is not the same as being *printed correctly*. At exactly `T` equal to the true 99th percentile the quantile is identified — the boundary case of the lemma — and the printed number is still the `q * F(T)`-quantile of the full distribution, which is below the truth. Identification is a property of the estimand; correctness of the printed value is a property of the estimator; the two coincide only when the timeout sits above the top of the observable range.

The ladder we work with is a piecewise-linear reconstruction through the seven published percentile points, which is what any reader of the table would do and what the interpolation literature warns about: a quantile read off a small grid of knots is a function of the interpolation rule as much as of the data {{c:david-nagaraja-2003,arnold-balakrishnan-nagaraja-2008,reiss-1989}}. We therefore treat the reconstruction as the *instrument* — fixed, stated, and applied identically to every row — rather than as an estimate of the truth. Every interval statement below is made about the reconstructed distribution, and the reconstruction's own error is a separate concern that we bound only qualitatively (Section 8).

Nothing in this section is new, and that is the point: the arithmetic is elementary. What is not elementary is noticing that a production report is sitting on it.

## 3 The trace, and the unit that must be stated first

We use the first day of the public Azure Functions trace {{c:shahrad-serverless-wild-2020}}. The archive member is a {{n:rows}}-row table of per-function duration summaries; after removing rows whose ladder is not usable, {{n:usable}} rows remain. The refusals are stated because they are not noise: {{n:zero_median}} rows report a zero median, which makes the ratio to the median undefined; {{n:unparseable}} rows cannot be parsed; {{n:crossing}} rows have a ladder whose knots decrease with probability, which is a recording defect rather than a distribution, and interpolating through one would invent tail mass.

**The unit comes first, because it changes every range in the paper.** The percentile columns of this table are not percentiles of individual invocations. The dataset documentation states that the framework aggregates every {{n:interval_s}} seconds, and that the percentile columns are percentiles of the per-interval *average* over the invocations in that interval, weighted by how many there were. The `Minimum` and `Maximum` columns, by contrast, are extremes over single invocations. Two consequences:

1. Any ratio formed across those two groups — for instance a maximum divided by a percentile of the average — compares two different quantities and is not a tail ratio at all. Our own first registered prior did exactly this and was withdrawn (Section 7).
2. Within the percentile ladder, `p100/p50` is a ratio of two percentiles of the same quantity, so it is meaningful. But it describes the range of a *smoothed* distribution: averaging many invocations inside an interval pulls in the tail. It is therefore a **lower bound** on the dynamic range at the invocation level, and every cost figure derived from it is a lower bound too.

This is not a presentational caveat. Workload characterization has a long record of summaries whose meaning depends on the aggregation applied before they were computed {{c:calzarossa-1993}}, and the measurement-methodology literature has established that a benchmark number is a function of the instrument as much as of the system {{c:mytkowicz-2009,georges-2007,hoefler-belli-2015}}. A paper that reported tail *ranges* from this table without saying which distribution they range over would be making a claim it cannot support.

The trace is one provider, one day, and one aggregation interval. Cluster data of this kind is known to be heterogeneous across time and across tenants {{c:verma-borg-2015,bodik-2010,benson-2010,kanev-2015}}, which is exactly why this is a case study rather than a sample of a population. Benchmarking studies that span machines and clouds reach the same conclusion from the other direction: the same system measured under different conditions produces a different distribution {{c:leitner-chaos-2016,lenk-iaas-2011,iosup-cloud-2011}}.

## 4 Limit one: the sample cannot resolve the quantile

A `q`-quantile is a statement about the top `1 - q` of a distribution. A sample of size `n` resolves it only if it expects at least one observation above it, that is, if `n (1 - q) >= 1`. For a {{n:q_pct}}th percentile that makes {{n:count_gate_lo}} invocations the exact boundary: at that count the expected number of observations above the quantile is one, and below it the quantile is an extrapolation from the sample's maximum.

This is the classical sample-size question for quantiles and tolerance limits, and its answer has been known for a long time {{c:wilks-1941,wilks-1948,wald-1943,bahadur-1966,mosteller-1946,stigler-1973,serfling-1980,chen-hall-1993,koenker-bassett-1978}}. The distribution-free bounds that make it sharp are equally classical {{c:dvoretzky-kiefer-wolfowitz-1956,massart-1990,anderson-darling-1952,vandervaart-wellner-1996,rao-linear-inference-1973,hoeffding-1963}}, as is the machinery for attaching an interval to whatever is estimated {{c:wilson-1927,clopper-pearson-1934,brown-cai-dasgupta-2001,agresti-coull-1998,newcombe-1998}}, including the resampling route when the analytic one is inconvenient {{c:efron-1979,efron-1987,efron-tibshirani-1993,bickel-freedman-1981,singh-1981,beran-1982,beran-1987,diciccio-romano-1988,hall-1986}}, and the survey-sampling frame that decides what the sample was a sample *of* {{c:tille-2006}}.

What the applied literature does not routinely carry is the resulting refusal. Our measurement of it on this workload:

| quantity | rows | share of usable |
|---|---|---|
| usable rows | {{n:usable}} | — |
| can resolve a {{n:q_pct}}th percentile (expects at least one observation above it) | {{n:resolvable}} | **{{n:resolvable_pct}}%** |
| cannot resolve it at any timeout | {{n:unresolvable}} | {{n:unresolvable_pct}}% |
| fewer than {{n:count_gate_lo}} invocations in the day | {{n:below_100}} | {{n:below_100_pct}}% |
| fewer than {{n:count_gate}} invocations in the day | {{n:below_1000}} | {{n:below_1000_pct}}% |

The median row expects {{n:n_obs_median}} observations above its own {{n:q_pct}}th percentile — that is, the median row does not expect even one.

Two things follow. The obvious one is that for two rows in three a reported {{n:q_pct}}th percentile is an extrapolation, and no timeout setting changes that. The less obvious one is that this limit is *independent* of the censoring limit in Section 5: a row can be perfectly identified with respect to its timeout and still unable to resolve the quantile, because its sample is too thin. The two limits are computed from different quantities — the invocation count versus the ladder's shape — so a paper reporting only the second would be describing the smaller of the two problems.

We report counts rather than a proportion with a confidence interval because these rows are not a sample: they are every row in the day. The uncertainty here is not sampling uncertainty within the day; it is whether the day stands for anything beyond itself, which no interval computed on these rows can answer, and we decline to dress it as one.

## 5 Limit two: the crossover, and the prior it refuted

The timeout is set by an operator, so the interesting question is not whether *some* timeout makes the report wrong but where the boundary sits as the timeout is relaxed. We fixed a grid of multipliers before looking — each row's timeout is a multiple of that row's own median, so the timeout does not depend on the quantity under test:

    T = k * median of the row,   k in {{n:k2}}, {{n:k4}}, {{n:k8}}, {{n:k16}}, {{n:k32}}.

Fixing the grid in advance matters. The obvious alternative — evaluate at `T` equal to the row's own 99th percentile — makes `c = 1 - q` hold by construction, so the boundary case is decided by the choice of grid rather than by the data; it is an identity wearing a measurement's clothes. Our first registered prior did that too, and it is recorded in Section 7.

| timeout | binds (% of rows) | `c` median | `c` {{n:p90}}th pct | understated, median | understated, {{n:p90}}th pct |
|---|---|---|---|---|---|
| {{n:k2}}x median | **{{n:k2_binds_pct}}%** | {{n:k2_c_median}} | {{n:k2_c_p90}} | {{n:k2_under_median}}x | {{n:k2_under_p90}}x |
| {{n:k4}}x median | {{n:k4_binds_pct}}% | {{n:k4_c_median}} | {{n:k4_c_p90}} | {{n:k4_under_median}}x | {{n:k4_under_p90}}x |
| {{n:k8}}x median | {{n:k8_binds_pct}}% | {{n:k8_c_median}} | {{n:k8_c_p90}} | {{n:k8_under_median}}x | {{n:k8_under_p90}}x |
| {{n:k16}}x median | {{n:k16_binds_pct}}% | {{n:k16_c_median}} | {{n:k16_c_p90}} | {{n:k16_under_median}}x | {{n:k16_under_p90}}x |
| {{n:k32}}x median | **{{n:k32_binds_pct}}%** | {{n:k32_c_median}} | {{n:k32_c_p90}} | {{n:k32_under_median}}x | {{n:k32_under_p90}}x |

"Binds" means the true quantile falls outside the set the harness can identify, `c > 1 - q`. "Understated" is the ratio of the true quantile to the printed one, taken **only on the rows where the boundary binds** — this restriction is not cosmetic. On a row whose timeout sits above its top knot nothing is censored, the printed number equals the truth, and a ratio averaged over all identified rows is a column of exactly one that says nothing about anything. We made that mistake and the corrected column is what the table reports.

The refuted prior is the last row. It predicted under {{n:prior_limb2_pct}}% of rows would still bind at {{n:k32}}x; the measurement is {{n:k32_binds_pct}}%, so the prediction failed. What makes the failure interesting is the reason it is not merely a calibration error: at a timeout of thirty-two times the median, on a workload whose median row records a handful of invocations, the harness still cannot identify the quantile for one row in eight, and there it understates by a median {{n:k32_under_median}}x. The decay from {{n:k2_binds_pct}}% to {{n:k32_binds_pct}}% — a fall of {{n:binds_ladder_pp}} percentage points across a sixteen-fold relaxation — is slower than the intuition that a generous timeout makes censoring irrelevant.

That shape is what the extreme-value literature would predict, though we do not fit a tail model and do not claim one. The behaviour of exceedances over a high threshold is what peak-over-threshold methods were built to describe {{c:pickands-1975,balkema-dehaan-1974,davison-smith-1990,davison-1984}}, the limiting laws for maxima are classical {{c:fisher-tippett-1928,gnedenko-1943}}, and the estimation of the tail index and of high quantiles from few exceedances is well developed {{c:smith-1987,hosking-wallis-1987,hosking-1990,grimshaw-1993,coles-2001,gumbel-1958,katz-2002}}, including the rare-event simulation machinery for when the events are too rare to sample directly {{c:glasserman-2000,rubino-rare-event-2009}} and the theory of records for the maxima themselves {{c:arnold-balakrishnan-1998}}. Our contribution is not a tail estimator. It is the observation that a threshold set for *configuration* reasons can be read as a censoring threshold, and that the correct report of a conditional quantile is conditioned on the threshold it was computed under.

Two controls run on every execution of the measurement, and both hold. With the timeout placed above each row's own maximum, the quantile is identified and the printed number equals the truth on {{n:no_censoring_rows}} of {{n:no_censoring_rows}} rows tested ({{n:no_censoring_pct}}%): if that ever stopped holding, the instrument would be broken rather than the data. And the degenerate class the cost law predicts does appear in real data: {{n:flat}} rows ({{n:flat_pct}}%) have no dynamic range at all, with `p100` equal to `p50`. A further {{n:one_level}} rows ({{n:one_level_pct}}%) are certified by a single timeout level, which is the same set only up to the precision one asks for — the two counts differ by every row whose range is non-trivial but smaller than the requested precision, and reporting one number in place of both would be a label that lies about its own set.

## 6 Limit three: what certifying the quantile costs

If an operator wants to certify a quantile to relative precision `eps` by choosing a timeout, and only the timeout is available as a dial, the number of distinct timeout levels needed is a property of the range the quantile spans:

    K = ceil(log R / log(1 + eps)),   R = p100 / p50.

The law is deliberately crude and deliberately conservative. It counts levels, not invocations, and it therefore answers the question "how many experiments does certifying this cost" rather than "how much traffic does it need" — the second is the sample-count limit of Section 4. Its degenerate endpoint is what keeps it honest: at `R = 1` it returns one level, because a workload with no range is certified by a single timeout.

| precision | `K` median | `K` {{n:p90}}th pct | `K` max | rows certified by one level |
|---|---|---|---|---|
| {{n:eps5}}% | **{{n:K5_median}}** | {{n:K5_p90}} | {{n:K5_max}} | {{n:K5_one_pct}}% |
| {{n:eps10}}% | {{n:K10_median}} | {{n:K10_p90}} | {{n:K10_max}} | {{n:K10_one_pct}}% |
| {{n:eps20}}% | {{n:K20_median}} | {{n:K20_p90}} | {{n:K20_max}} | {{n:K20_one_pct}}% |

The ranges behind these counts are wide: `R` has median {{n:R_median}}, {{n:p90}}th percentile {{n:R_p90}}, and maximum {{n:R_max}}. Because each `R` is a ratio of two percentiles of the interval mean, both counts are **lower bounds** on what the invocation-level workload would require — averaging inside the interval compresses the range it is computed from.

The queueing picture supplies the intuition for why a tail is worth this much attention even when its median behaviour is tame: in heavy traffic the waiting-time distribution is governed by the normalisation of the arrival and service processes rather than by their detailed laws {{c:kingman-1961,kingman-1962}}, the many-server regime has its own limit theory {{c:halfin-whitt-1981,reiman-1984}}, and the approximations practitioners actually use for multi-server queues are explicit about the regime in which they hold {{c:whitt-1993,abate-whitt-1992,harchol-balter-2013}}. None of this is needed to compute `K`; it is needed to see that a tail quantile is not a small correction to a mean.

Two further bodies of work keep the cost claim from being over-read. Estimating a quantile from a *simulation* has its own run-length and variance questions, and the answers depend on the output process being stationary in a sense a production trace does not guarantee {{c:welch-1983,heidelberger-1981}}. And treating a certification as a decision problem — what it is worth paying to narrow a set — is exactly the comparison of risk functions that decision theory formalises {{c:lehmann-casella-1998,berger-1985}}; we compute the cost of certifying and leave the value of certifying to the operator.

## 7 Registered priors, evaluated limb by limb

The priors below were registered on the study's issue before the deciding run, together with the reason each was expected to hold. We report them as registered, including the one we withdrew, because a prior that is quietly edited after the fact is not a prior.

**P1 — the reported quantile is monotone in the timeout, and its spread across the grid exceeds the spread of repeated measurement.** The first limb is a theorem of the lemma and holds by construction; the self-test pins it. The second limb is **NOT RUN**, and the reason is not a missing dependency a reader could install. Recomputing the statistics on a fixed published table is deterministic: two independent passes over the same bytes agree exactly, so the "repeated-measurement spread" is zero by construction, and "the effect exceeds zero noise" is then either vacuous or a statement about rounding. Estimating that spread properly needs per-invocation latencies or replicated measurements of the same population; this table carries neither, because its percentiles are percentiles of a 30-second mean and one published day is one measurement. The honest verdict is *no information*, and `./reproduce.sh` reports it as `NOT RUN` on every run so that the package cannot claim it.

**P2 — most rows have a maximum at least twice their 99th percentile.  Withdrawn before the deciding run.** The prior was refuted by its own justification: the same registration recorded a measured median of about one for that ratio, which is a different statement from the one the threshold asserted. Worse, the ratio itself compares two quantities in different units — a single-invocation maximum over a percentile of the 30-second mean (Section 3) — so it is not a tail ratio at all. It was withdrawn in public on the issue, and replaced by P2′ below.

**P2′ — with the timeout set at a multiple of the row's own median, the fraction of rows whose quantile is unidentified is at least {{n:prior_limb1_pct}}% at the smallest multiplier, and under {{n:prior_limb2_pct}}% at the largest.** First limb **MET**: {{n:k2_binds_pct}}% at {{n:k2}}x. Second limb **UNMET**: {{n:k32_binds_pct}}% at {{n:k32}}x. The conjunction therefore fails, and we do not rescue it by reporting the limb that held: a conjunction is refuted by one false limb, and the false limb is the more informative of the two.

**P3 — certifying the median workload to {{n:eps5}}% needs at least {{n:prior_p3}} timeout levels.** **MET**: the median is {{n:K5_median}}, with a {{n:p90}}th percentile of {{n:K5_p90}} across rows.

Reporting a refuted prior is only a novelty signal as far as the study could have detected the contrary. For P2′'s second limb the threshold was a share of rows, computed over every usable row in the day rather than over a sample of them, so there is no sampling error to compare against: the measured {{n:k32_binds_pct}}% is the value for this population of rows, not an estimate of it. What is uncertain is whether the population generalises — Section 9 — and that uncertainty is not something a confidence interval on these rows could express.

### What this study can and cannot detect

The study's sensitivity differs by quantity, and saying so is more useful than a single power figure.

For the shares reported in Sections 4 to 6 the "sample" is the entire day: {{n:usable}} rows, every one measured. The quantities are therefore censuses of a finite population, and their sampling error is zero by construction. What they cannot answer is any question of the form "would another day, or another provider, show the same". The design has no second day and no second provider, so between-day and between-provider variation is not estimable here at all — not "small", not "large", *not estimated*. Any reader who needs that variation must supply a second trace, and we expect a reviewer to want it.

For the second limb of P1 the sensitivity is zero in a different sense: the denominator of the comparison is identically zero on this input, so no effect size, however large, could have been detected as exceeding it. This is why that limb is reported as no information rather than as support.

For the tail quantities themselves the binding constraint is not statistical but structural: the ladder has seven knots, so any quantile between knots is produced by the interpolation rule. The reconstruction cannot distinguish two distributions that agree at the knots, and an effect confined between two knots is invisible to this instrument regardless of how many rows are behind it. We state the ladder as part of the instrument rather than pretending the instrument is transparent.

## 8 Threats to validity

**The unit.** Every range reported here is a range of the 30-second interval mean. The invocation-level range is larger, by an amount this table cannot quantify, so the cost figures in Section 6 are lower bounds and the tail compression we measure is a lower bound on the compression at the invocation level. A reader who reads `R` as an invocation-level dynamic range will overestimate how cheap certification actually is.

**One trace, one day, one provider.** This is a case study and we do not generalise from it. The direction of the result — that a timeout leaves a quantile unidentified for a substantial share of workloads — is a consequence of the lemma and cannot be undone by another day; the magnitudes are properties of this workload and would move.

**The reconstruction is a model.** Piecewise-linear interpolation between seven knots is a choice. It is stated, applied identically to every row, and embedded in committed code {{c:david-nagaraja-2003,reiss-1989}}, but a different reconstruction would move the crossover slightly. Since the lemma's boundary depends on the CDF evaluated at the timeout, and the CDF between knots is exactly what interpolation supplies, this is the most substantive modelling assumption in the paper.

**Determinism is not replication.** Our reproduction check proves that the same program on the same bytes yields the same numbers. That is a statement about the instrument, not about the world, and it is why the noise limb is reported as unmeasured rather than as passed — a confusion this literature has warned about for a long time {{c:mytkowicz-2009,georges-2007,hoefler-belli-2015,kohavi-online-2013}}.

**Rows we refused.** {{n:refused_total}} of {{n:rows}} rows could not be used, mostly because they report a zero median. Refusing them is a judgement: a zero median makes the ratio to the median undefined, and the alternative — substituting a small positive number — would manufacture a dynamic range where the data reports none. The share is small but not zero, and if zero-median rows are systematically the thinnest, their exclusion flatters the resolvable share slightly.

**Why it is still worth publishing.** Because the first limit is arithmetic and the report that ignores it is wrong in a direction the operator cannot see. A practitioner who reads this can compute, from their own invocation counts, how many of their reported percentiles are extrapolations; and can compute, from their own timeout and median, whether the boundary binds. Neither computation needs our data.

## 9 Related work, and what the estimand is in each case

Three lines of work are close enough that the difference has to be stated rather than assumed.

*Censoring and survival analysis.* Kaplan–Meier and its descendants estimate a distribution from right-censored observations and use the censoring information rather than discarding it {{c:kaplan-meier-1958,cox-1972,turnbull-1976,lagakos-1979,gentleman-geyer-1994}}. Our estimand is the same object — a quantile of a partially observed distribution — but the deliverable differs: they produce an estimate, we report the region in which the estimate is unidentifiable and the condition under which it collapses. Relatedly, the engineering reliability literature uses censored data to plan tests and to certify lifetimes {{c:escobar-meeker-2006,nelson-applied-life-1982,martinussen-scheike-2006,prentice-1978,efron-1988,lin-wei-1989}}, which is the closest analogue of our certification cost, but its thresholds are physical failure times rather than a configuration dial.

*Partial identification.* The identified-set formulation here is that literature's object, applied to a latency quantile instead of a treatment effect {{c:manski-2003,tamer-2010,molinari-2020,imbens-manski-2004,chernozhukov-hong-tamer-2007,andrews-soares-2010,romano-shaikh-2008,bugni-2010,newey-mcfadden-1994,manski-2007,horowitz-manski-2000,rosenbaum-2002}}. The difference is that the set here is unbounded above and has a closed-form boundary in the observable fraction, so no inference machinery is needed; the contribution is the measurement of where the boundary falls on a real workload, not a new inference procedure. Where that literature exists because the data are intrinsically uninformative about a parameter, here the un-informativeness is *manufactured by a configuration setting*, which means it can be removed by changing the setting — a distinction with practical content that the econometric framing does not need to make.

*Tail latency in systems.* The systems literature on tail latency is about causes and mitigations: fan-out amplification, queueing, interference, and the techniques that bound them {{c:dean-barroso-2013,barroso-2003,armbrust-2010,kanev-2015}}. Its measurements are usually made with a timeout in place, and the reporting convention rarely says which one. Our claim is compatible with all of it and constrains none of it: we are not saying tails are smaller than reported, we are saying that for a computable set of workloads the reported number does not identify the quantity it names, and that the set is large in a public trace.

Two studies in this journal touch the same sentence — "a count is not a property of the system" — with different estimands, and the difference is worth making explicit. The probe-count study (`#135`) asks what a *probe* count determines about the object being probed: its count is a property of the measurement schedule, and the estimand is the quantity the probes are meant to certify. The proof-cost study (`#139`) asks what certifying an invariant costs in *proof steps*: its count is work, and the estimand is the shortest certificate. Ours counts timeout levels, and the estimand is a tail quantile of a partially observed distribution. All three refuse to read a count as a fact about the system, and all three differ in what the count is a count of — which is why citing either as precedent for the other would be a category error rather than a comparison.

Distributed systems studies of *failure* supply the reason the timeout exists at all, and the reason it is usually set generously: silent failures and retry storms are the events one is defending against {{c:bronson-metastable-2021}}, and the diagnosis tooling for such systems has its own measurement burden {{c:gunawi-2014,ousterhout-ramcloud-2015,ousterhout-ramcloud-case-2011,smith-1990,woodside-2007}}. Nothing in that literature depends on our result, but every deployment it describes is exposed to it.

## What changes, and what does not

If this is true, three beliefs change, and each changes a decision.

A reported high quantile is not automatically a measurement of the tail; it is a measurement of the tail *conditioned on a threshold*, and the conditioning has to be reported with it. The decision that follows is a reporting one: state the timeout, or state that the quantile may be unidentified.

A generous timeout is not a conservative one. At {{n:k32}}x the median, on this workload, one row in eight still has an unidentifiable quantile, and there it is understated by a median {{n:k32_under_median}}x. The decision that follows is operational: a timeout chosen for safety does not thereby make the latency report safe.

Thin workloads cannot report tails at all, and the share is not marginal: {{n:unresolvable_pct}}% of usable rows in this day cannot resolve their own 99th percentile at any timeout. The decision that follows is architectural: a per-function tail objective on a function invoked a few dozen times a day is a control that cannot be evaluated, and a monitoring system that prints one anyway is printing an extrapolation.

Each of these is a bound a practitioner can recompute for their own system from two numbers they already have — their invocation count and their timeout as a multiple of their median. That is the sense in which the result is meant to be useful: not as a fact about one trace, but as arithmetic that was missing from a report.

## Availability

The instrument, the committed input and every number in this paper are in this directory. `./reproduce.sh` runs the six steps that re-derive them and prints its verdict; a `NOT RUN` step means a claim the data cannot carry, and the package is designed so that verdict can never read as though that number had been reproduced.

## References

{{refs}}
