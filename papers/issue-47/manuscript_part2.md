
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
[@fiat] [@alberssurvey] [@chenpreliminaries]. Measuring a **realized** ratio therefore requires the
optimum itself rather than a bound on it, and the three problems here are chosen because their
optima are computable exactly for every instance the instrument generates:

* **Ski rental** (`ski`) — buy or rent under an unknown horizon. The offline optimum is exact by
  enumeration over the purchase day, so the realized ratio is exact for every stream. The problem is
  the field's canonical test-bed [@lotker] [@khanaferconstrained] [@zhangcombinatorial], and its
  prediction-augmented variants are the most numerous in the literature
  [@kodialam] [@fujiwarabuy] [@kangbayesian] [@wangmultishop] [@shinmultislope].
* **Paging** (`paging`) — evict-on-full with a cache. The offline optimum is Belady's, computable
  exactly for every trace, and the classical analyses of paging are stated against it
  [@irani] [@achlioptas] [@alberslookahead]; the problem is the one the learning-augmented caching
  literature is built on [@lykouris] [@rohatgi] [@bansalweighted] [@jiangweightedpaging].
* **Scheduling** (`sched`) — single machine, known processing times, minimise total completion time.
  The optimum is exactly the shortest-processing-time order [@choscheduling], the problem on which
  scheduling-with-predictions results are stated [@mitzenmachermisprediction] [@lindermayrpermutation].

The grid is instantiated at a fixed size: `{{D:trace_len}}` steps per trace, `{{D:n_jobs}}` jobs for
the scheduling instances, and `{{D:n_pages}}` pages with a cache of `{{D:k_pages}}` for paging. The
three problems are reported **separately throughout**; no number in this paper pools them.

### 3.2 The prediction is a profile of five coordinates, and the blend is one parameter

A prediction stream is generated from a **declared profile** carrying five coordinates — bias,
spread, autocorrelation, tail probability and tail multiplier. The profile set is fixed at
`{{D:n_profiles}}` members (Table 1), chosen so that the stream's mean, its spread and its tail can
be moved independently of one another. That independence is what makes Section 4.4 readable as a
statement about *which* coordinate the worst-case calibration reacts to, rather than a statement
about "noisy predictions" in general.

{{T:profiles}}

**Table 1.** The `{{D:n_profiles}}` declared error profiles. Each row is one generator: `bias` and
`spread` are the location and scale of the error, `autocorrelation` is the lag-1 retention, and the
tail is a `tail probability` of an error multiplied by `tail multiplier`. This profile set is used
unchanged by every result in Section 4.

The profile is consumed through a single blend parameter `lambda` on a `{{D:n_lambdas}}`-point grid,
which interpolates between the prediction-following arm and the robust arm — the construction the
learning-augmented literature states its consistency–robustness trade-off on
[@lykouris] [@weioptimal] [@shencalibrated] [@lipredictionspecific]. Every cell is
`{{D:n_profiles}}` profiles × `{{D:n_lambdas}}` blend settings × `{{D:replicates}}` replicates ×
`{{D:traces_per_rep}}` traces per replicate, and the **scalar baseline** carried along on the same
held-out cells is a regression of realized loss on `|error|` — the statistic the field's bounds are
written against [@anandregression] [@mitzenmacher] [@lassurvey].

### 3.3 Paging has two attachments, and they are not the same experiment

A prediction must be attached to something before it can be used. Two attachments are available in
this instrument: a **step-common** multiplier applied to every candidate's score, and a **per-page**
multiplier. They are not interchangeable, and the difference is measured rather than argued. The
step-common attachment is provably blind to positive errors — a common factor cannot reorder an
argmax — and it reproduces the zero-error cost exactly
(`{{X:claims.L1_attachment.C5_attachment_control.a_shared_attachment_exact_on_nonnegative_errors}}`
traces on non-negative errors), while the per-page attachment differs on the same information
(`{{X:claims.L1_attachment.C5_attachment_control.b_per_page_attachment_differs_on_the_same_information}}`
traces). The control's third relation is the trap it exists to catch: a positive **bias** is not a
non-negative **multiplier**, and a shared attachment still changes the realized cost on
`{{X:claims.L1_attachment.C5_attachment_control.c_shared_attachment_differs_on_a_positive_BIAS_profile}}`
traces of the `over_extreme` profile, because the scored distance floors and ties.

The consequence is carried as limit **L1**: every statement this paper makes about *positive-bias*
predictions in paging is a statement about the per-page attachment, not an attachment-free fact. The
literature's caching constructions differ in exactly this place — which quantity the advice is
allowed to touch [@chenrobustpaging] [@weibettersimpler] [@antoniadissuccinct] — so a paper that
reported a positive-bias result without naming its attachment would be reporting an artefact of the
attachment as a property of the problem.

### 3.4 The resolution unit is the profile, not the repeated measurement

Every verdict is quoted in **cluster** units: the minimum detectable effect is computed over
`(profile, replicate)` clusters, not over the paired units an earlier version of this pipeline used
[@bulusmde] [@burstynmde] [@hunterpump]. Paired units share the error generator, the
implementation and the fit, so an MDE computed over them was optimistic by 3.7–6.3×, measured. Under
the cluster unit the tightest resolution in the design is
`{{X:facts.claim1.worst_block_mde.value|4f}}` competitive-ratio units. This is a correction of the
instrument by the instrument, and it is carried as limit **L5**.

### 3.5 The null is shifted, so a negative verdict is uninterpretable

The design compares a signed arm against a scalar arm matched **in form** — both are two-term, and
they differ in the odd term. Matching the form is necessary but not sufficient, because the
object-level test is not sign-free. The instrument calls this test the **specificity control**:
under a synthetic **even** target, which by construction has no sign dependence, the odd parameter
is penalised, one per problem, by ski rental
`{{X:facts.limit.L2_null_shift.ski.value|2f}}`, scheduling
`{{X:facts.limit.L2_null_shift.sched.value|2f}}` and paging
`{{X:facts.limit.L2_null_shift.paging.value|2f}}` cluster MDEs. A design that punishes its own odd
term under a sign-free target cannot read a negative as evidence against a signed model.

Two consequences are frozen as limit **L2** and applied everywhere below: only the **positive**
resolutions are reported as evidence, and the earlier unmatched-form reading is **retired** — its
sign is not even stable across problems (ski `{{X:facts.claim2.confounded_advantage_mde.ski.value|2f}}`,
sched `+{{X:facts.claim2.confounded_advantage_mde.sched.value|2f}}`, paging
`{{X:facts.claim2.confounded_advantage_mde.paging.value|2f}}`), which is what a form confound looks
like when it is measured instead of assumed.

### 3.6 The external cell, the controls, and the coordinate census

Three apparatuses bound what the instrument may conclude, and each reports a measurement rather than
a promise:

* **The external cell**, anchored to one published system result [@lahanchor], reproduces the
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
  or entropy read — and reports `{{X:coordinate_census.violations}}` violations over all three.
  Reproducibility apparatus in this literature
  is usually stated as an intention [@fehrbestpractices] [@flittnerartefact] [@thorpereprorubric];
  here it is a reading, and its own limits are reported with it [@brookssmoke] [@pesericoartifact].

## 4. Results

The four subsections are the four contributions of Section 1.3, in that order, each with the
measurement that establishes it and the limit it has to carry.

### 4.1 The scalar error is not sufficient, and the witness is by construction

A constructive witness settles sufficiency without a model-selection argument: two arms are built
with the **same multiset of `|error|`** — same mean, same standard deviation, same 95th percentile —
differing only in sign, so their scalar features agree by construction. The largest remaining gap
between the two arms' scalar features, over every block of the design, is exactly
`{{X:facts.claim1.scalar_gap_max_exact.value|1e}}`. Their **realized losses** differ by up to
`{{X:facts.claim1.worst_loss_gap.value|3f}}` competitive-ratio units (problem
`{{X:facts.claim1.worst_problem.value}}`, profile `{{X:facts.claim1.worst_profile.value}}`), against
a cluster-unit minimum detectable effect of `{{X:facts.claim1.worst_block_mde.value|4f}}` — a gap
above its own resolution threshold in `{{X:facts.claim1.blocks_exceeding_own_mde.value}}` of
`{{X:facts.claim1.blocks_total.value}}` blocks, with at least
`{{X:facts.claim1.pairs_per_block_min.value}}` pairs in every block.

![The witness, in the two panels its claim has. **Top:** the largest scalar-feature gap between the
two arms, for each of the 39 design blocks — every mark on the axis, because the gap is exactly zero
in every block by construction (the arms share a multiset of `|error|`). **Bottom:** the same blocks'
realized loss differences, each divided by that block's own cluster-unit minimum detectable effect,
so the dashed line at 1 is the block's own resolution; the 31 filled bars above it are differences
the block can resolve, and the 8 hollow marks on the axis are the blocks where the arms did not
separate at all — the error-free and coincident-arm control cases. Generated from
`sufficiency_v1_results.json` by `figures/make_figures_v1.py`, regenerated and byte-compared by
`reproduce.sh`.](figures/fig1_witness.svg)

The reading is not statistical. A loss that is not a function of the scalar cannot be predicted from
it, so no amount of capacity in the scalar regression can recover the difference — which is why the
witness is stated as an identity (the scalar features are equal) plus a measured gap (the losses are
not). **What the witness is a claim about, stated because the design cannot separate the two:** the
sign is uniform across all three problems (§7: `12`/`12`, `7`/`7`, `12`/`12` separating blocks), and
this harness prices over-prediction and under-prediction through **one** asymmetric cost form (limits
L2, L6). So the witness is a claim about how these **algorithms** consume a signed prediction *under a
fixed cost geometry*; it is not evidence that the same sign ordering survives a design that varies the
cost structure across problems, which is a different experiment and is not run here. What survives
such a change is the identity half — two arms with equal scalar features and unequal losses — because
that half is a property of how the arms are built, not of how the loss is priced; the direction of the
gap is the half that would move, and §1.4's decision sentence is the sentence that would move with it. This is the sharpest available form of the objection to the field's own quantifier, where
`|error|` or `eta` appears as a sufficient statistic for the price of misprediction
[@mitzenmacher] [@lassurvey] [@mitzenmachermisprediction] [@weioptimal]. Criterion (a)'s held-out
model comparison returns **`{{X:criteria.a_signed_beats_scalar_on_held_out_cells.state}}`** for
scheduling and does **not** resolve for ski rental or paging under this design; the object-level
contrasts carry those two (§4.2), and the criterion is reported per problem rather than as one
verdict.

### 4.2 Where the design resolves, the sign channel carries information

The second result is the one the shifted null constrains most tightly, so it is reported in the
direction the design can support. Comparing the signed arm against the scalar arm matched in form,
per problem, on cells held out by profile, the advantage is
`+{{X:facts.claim2.clean_advantage_mde.ski.value|2f}}` cluster MDEs for ski rental and
`+{{X:facts.claim2.clean_advantage_mde.sched.value|2f}}` for scheduling; for paging it is
`+{{X:facts.claim2.clean_advantage_mde.paging.value|2f}}`, below the resolution threshold, and it is
reported as **unresolved** rather than as a small effect. The paging null is not noise: its own
shifted-null penalty is roughly a tenth of the other two problems'
(`{{X:facts.limit.L2_null_shift.paging.value|2f}}` against
`{{X:facts.limit.L2_null_shift.ski.value|2f}}` and
`{{X:facts.limit.L2_null_shift.sched.value|2f}}`), so paging is the problem where the design comes
closest to resolving and still does not.

This is the result that makes the paper's object *directional*, and it is where the decision-focused
literature and this instrument meet from opposite sides: that literature shows that a scalar
training objective is the wrong objective for a downstream decision
[@elmachtoub] [@vanderschueren] [@schutterobust] [@liuwhenwhy], while on the objective side the loss
literature says the same thing about what a learner minimises: the loss must carry the *direction* of
the cost, not its magnitude
[@barnesmisclassification] [@benbaruch] [@zhounoisylabels] [@fusteinsloss] [@lozanoboosting]. The
instrument says which half of the error a loss is reacting to, and §4.4 prices the consequence.

### 4.3 A published ordering survives contact with the harness, in sign

The external cell takes one published system result [@lahanchor] and asks whether this instrument
reproduces the *ordering* of its reported pair. The published pair is concordant: the cache with the
larger mean gain (`{{X:facts.claim3.published_mean_gain.value|p0}}` over its predecessor, against
`{{X:facts.claim3.published_implied_mean_gain.value|p1}}` for the comparison cache, derived as a
ratio in the artefact rather than asserted) is also the one with the smaller worst-trace degradation
over the non-learned baseline (0.8% against 8.8%). Ranking the harness's own
{{X:facts.claim3.pairs_all.ski.value|d}}-pair grid of {{D:n_profiles}} profiles by mean gain and by
the best unit's tail, the concordance holds in all three problems — Kendall's tau
`{{X:facts.claim3.tau_all.ski.value|3f}}` for ski, `{{X:facts.claim3.tau_all.paging.value|3f}}` for
paging and `{{X:facts.claim3.tau_all.sched.value|3f}}` for scheduling — and it still holds when the
zero-error anchor, which is extreme on both axes by construction, is dropped:
`{{X:facts.claim3.tau_excluding_zero_anchor.ski.value|3f}}` /
`{{X:facts.claim3.tau_excluding_zero_anchor.paging.value|3f}}` /
`{{X:facts.claim3.tau_excluding_zero_anchor.sched.value|3f}}`.

**A tau is a ratio, so the counts behind it travel with it.** Each problem ranks
{{X:facts.claim3.pairs_all.ski.value|d}} pairs; the disagreeing ones number
`{{X:facts.claim3.discordant_all.ski.value|d}}` (ski),
`{{X:facts.claim3.discordant_all.paging.value|d}}` (paging) and
`{{X:facts.claim3.discordant_all.sched.value|d}}` (scheduling), and the pairs tied on one axis — which
the stage's tau drops from numerator and denominator alike — are
`{{X:facts.claim3.tied_all.paging.value|d}}` in paging and none elsewhere. The weakest reading is
ski's, and its source is stated rather than left to be inferred: it is carried by
`{{X:facts.claim3.discordant_all.ski.value|d}}` of {{X:facts.claim3.pairs_all.ski.value|d}} pairs
disagreeing, **not** by a coarse ranking — dropping the anchor leaves
{{X:facts.claim3.pairs_excl_zero.ski.value|d}} pairs and moves the tau by less than the interval's
width (`{{X:facts.claim3.tau_excluding_zero_anchor.ski.value|3f}}` against
`{{X:facts.claim3.tau_all.ski.value|3f}}`), the anchor itself being concordant against
`{{X:facts.claim3.anchor_concordant_pairs.ski.value|d}}` others. The interval is the stage's
**profile-level bootstrap** — the profiles resampled with replacement
{{X:facts.claim3.bootstrap_reps.value|d}} times from seed
{{X:facts.claim3.bootstrap_seed.value|d}}, 2.5/97.5 percentiles, re-run in the canonical runner
rather than quoted from the artefact — so it measures how much the ordering read depends on *which
profiles the grid happens to contain*, not unit-level sampling error: ski
[`{{X:facts.claim3.tau_ci_lo.ski.value|3f}}`, `{{X:facts.claim3.tau_ci_hi.ski.value|3f}}`], paging
[`{{X:facts.claim3.tau_ci_lo.paging.value|3f}}`, `{{X:facts.claim3.tau_ci_hi.paging.value|3f}}`],
scheduling [`{{X:facts.claim3.tau_ci_lo.sched.value|3f}}`,
`{{X:facts.claim3.tau_ci_hi.sched.value|3f}}`]. No lower bound crosses zero, so the **sign-level**
concordance survives the grid-dependence the interval quantifies; the **magnitude** of the agreement
does not, which is what the reach row below then bounds.

The honest second half of this result is the reach row, and it is a limit before it is a finding. The
published robustness scale is a 0.8–8.8% worst-trace degradation; the harness reaches that scale in
**one** problem and in neither of the other two. Ski rental has
`{{X:facts.limit.L3_reach_at_or_above_0.8pct.ski.value}}` of
`{{X:facts.limit.L3_reach_profiles.ski.value}}` profiles at or above 0.8% and
`{{X:facts.limit.L3_reach_at_or_above_8.8pct.ski.value}}` at or above 8.8%; paging and scheduling
have `{{X:facts.limit.L3_reach_at_or_above_0.8pct.paging.value}}` each, and in those two problems
the harness's worst unit is *better* than the non-learned baseline at every profile (minimum
`{{X:facts.limit.L3_reach_min_worst_unit_degradation.paging.value|4f}}` for paging,
`{{X:facts.limit.L3_reach_min_worst_unit_degradation.sched.value|4f}}` for scheduling). The
generated errors are therefore uniformly gentler than a real predictor's errors wherever the reach
row is zero, and the cell supports a claim about **ordering** there and none about magnitude.

That asymmetry is itself informative: it locates the interface between an error generator and
predictor-like errors, which is the quantity the learned-systems literature reports from the other
end — end-to-end deltas against a strong baseline, with no prediction-error measure on the horizontal
axis [@sethumurugan] [@jaintaxonomy] [@cachereplsurvey] [@zhoulearningbelady]
[@fengkvcache]. Read as limits **L3** and **L4**, the cell is a sign-level anchor, not a
reproduction: no unit conversion is attempted or claimed.

### 4.4 What worst-case calibration costs, and which coordinate it reacts to

The fourth result prices the field's standard calibration rule for the blend parameter. The rule
evaluated here is the worst-case choice the consistency–robustness literature states
[@weioptimal] [@shintradeoff] [@lipredictionspecific], and the measured object is its cost relative
to the profile's own best blend setting, per profile, in cluster units.

| problem | median factor | worst profile's factor | 95% between-stream interval | profiles where the certificate's blend differs | Pearson r (tail, factor) |
|---|---|---|---|---|---|
| `ski` | `{{X:facts.claim4.lambda_loss_median.ski.value|3f}}` | `{{X:facts.claim4.lambda_loss_max.ski.value|3f}}` | `[{{X:facts.claim4.lambda_loss_interval_lo.ski.value|3f}}, {{X:facts.claim4.lambda_loss_interval_hi.ski.value|3f}}]` | `{{X:facts.claim4.lambda_displaced.ski.value}}` of 12 | `{{X:facts.claim4.lambda_corr_tail.ski.value|3f}}` |
| `sched` | `{{X:facts.claim4.lambda_loss_median.sched.value|3f}}` | `{{X:facts.claim4.lambda_loss_max.sched.value|3f}}` | `[{{X:facts.claim4.lambda_loss_interval_lo.sched.value|3f}}, {{X:facts.claim4.lambda_loss_interval_hi.sched.value|3f}}]` | `{{X:facts.claim4.lambda_displaced.sched.value}}` of 12 | `{{X:facts.claim4.lambda_corr_tail.sched.value|3f}}` |
| `paging` | `{{X:facts.claim4.lambda_loss_median.paging.value|3f}}` | `{{X:facts.claim4.lambda_loss_max.paging.value|3f}}` | `[{{X:facts.claim4.lambda_loss_interval_lo.paging.value|3f}}, {{X:facts.claim4.lambda_loss_interval_hi.paging.value|3f}}]` | `{{X:facts.claim4.lambda_displaced.paging.value}}` of 12 | `{{X:facts.claim4.lambda_corr_tail.paging.value|3f}}` |

**Table 2.** The cost of the worst-case calibration rule, per problem, over the 12 non-zero profiles
of the declared set (the `zero` profile has no error to calibrate against). *Factor* is the
certificate rule's realized ratio divided by the profile's own best blend setting's, so a factor of
1.0 means the worst-case choice was already optimal. The interval is over streams. The last column is
the correlation between the factor and the profile's tail coordinate.

Three further readings belong with the table, and one of them does **not** confirm the prior:

* The certificate's blend setting is an **endpoint** on every problem — the rule is bang-bang here —
  and it differs from the profile's own best setting on
  `{{X:facts.claim4.lambda_displaced.ski.value}}`, `{{X:facts.claim4.lambda_displaced.sched.value}}`
  and `{{X:facts.claim4.lambda_displaced.paging.value}}` of the 12 profiles respectively, so the cost
  is not an artefact of one profile.
* The factor does not rest on choosing the blend setting on the streams it is scored on: refitting
  the setting out of sample leaves the worst profile's factor at 1.7030 for ski (in-sample
  `{{X:facts.claim4.lambda_loss_max.ski.value|3f}}`), 1.2838 for scheduling and 1.4517 for paging.
* The registered prior said the loss tracks the **tail** of the spread rather than its mean. The
  measured correlations are `{{X:facts.claim4.lambda_corr_tail.ski.value|3f}}` for ski,
  `{{X:facts.claim4.lambda_corr_tail.sched.value|3f}}` for scheduling and
  `{{X:facts.claim4.lambda_corr_tail.paging.value|3f}}` for paging: positive in all three problems,
  and too small in all three to carry the claim on its own. Profiles with no tail show a mean factor
  of `{{X:facts.claim4.lambda_mean_loss_other.ski.value|2f}}` /
  `{{X:facts.claim4.lambda_mean_loss_other.sched.value|2f}}` /
  `{{X:facts.claim4.lambda_mean_loss_other.paging.value|2f}}` (ski/sched/paging) against
  `{{X:facts.claim4.lambda_mean_loss_tail.ski.value|2f}}` /
  `{{X:facts.claim4.lambda_mean_loss_tail.sched.value|2f}}` /
  `{{X:facts.claim4.lambda_mean_loss_tail.paging.value|2f}}` for the two profiles that have a tail:
  the direction the prior predicted is present, and the magnitude is not what the prior implied.
  Section 7 reports this prior as *partially confirmed*, not as confirmed.

Finally, the factor is reported as a **ratio of means** as well as as a median
(`{{X:facts.claim4.lambda_ratio_of_means_median.ski.value|3f}}` /
`{{X:facts.claim4.lambda_ratio_of_means_median.sched.value|3f}}` /
`{{X:facts.claim4.lambda_ratio_of_means_median.paging.value|3f}}` for ski/sched/paging), because a
median of per-profile ratios and a ratio of means are different statistics and the registered
criterion initially named only the first. The two agree to three decimals here; the pair is reported
so that a reader who wants the aggregate-level statement has it.

### 4.5 The registered criteria, one by one

The registration fixed four success criteria before the deciding runs. Reported against the
committed artefacts, with no pooling across problems:

| criterion | state | what it returned |
|---|---|---|
| (a) the signed decomposition beats the scalar `|error|` on held-out cells | `{{X:criteria.a_signed_beats_scalar_on_held_out_cells.state}}` | resolved for scheduling; did not resolve for ski rental or paging under this design, where the constructive witness (§4.1) carries the claim instead |
| (b) the classic anchors are recovered | `{{X:criteria.b_classic_anchors_recovered.state}}` | the known competitive ratios are reproduced at both ends of the error range |
| (c) the cost of worst-case calibration is measured | `{{X:criteria.c_lambda_calibration_loss.state}}` | a factor per problem, with a between-stream interval and an out-of-sample check on the blend setting it uses (§4.4) |
| (d) the streams are independent and the result is sensitive to them | `{{X:criteria.d_streams_and_sensitivity.state}}` | reported per problem, with the flip analysis, in §4.6 |

**Table 3.** The four registered success criteria, each with its state in the committed artefact and
what it returned. Criterion (a) is reported per problem because the criterion is a comparison, and a
comparison that resolves in one problem and not the others is not a single verdict.

### 4.6 Streams, the unit of inference, and the flip bound per headline number

Each cell is measured over `{{D:replicates}}` replicate streams, and every verdict above is quoted in
cluster units (§3.4), so the robustness question is not whether the numbers move but whether the
**verdicts** move. Three things are measured:

* **Disjoint streams.** Every cell's streams are its own: no stream is reused across cells, so a
  verdict that holds in two cells is not one measurement counted twice. The registration's fourth
  success criterion is this property, and it is reported as
  `{{X:criteria.d_streams_and_sensitivity.state}}` in Table 3.
* **Interval over streams.** Where a factor is reported (Table 2), its interval is the between-stream
  interval at the cluster unit, and the out-of-sample refit in §4.4 is the check that the factor does
  not depend on choosing the blend setting on the streams it is scored on. The witness of §4.1 needs
  no such check: an identity plus a gap that clears its own resolution in
  `{{X:facts.claim1.blocks_exceeding_own_mde.value}}` of `{{X:facts.claim1.blocks_total.value}}`
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
    (`{{F:F1_2_sign_channel.sched.k_inversions}}` cluster inversions reverse it), and asserts an
    *absence* for paging and
    ski rental, whose margins are the
    `{{F:F1_2_sign_channel.ski.distance_to_boundary}}` and
    `{{F:F1_2_sign_channel.paging.distance_to_boundary}}` cluster MDEs they sit below the bar.
  * **Exactness.** Where the stage records the units individually the bound is exact; where it keeps
    only an aggregate (a cluster mean with its interval) the bound is an estimate under a stated
    equal-magnitude assumption, and the artefact says which is which. The **specificity control** — the sign-free even target of §3.5, frozen as limit L2 —
    is the case where the bound is **not derivable** at all from the committed artefact — the per-unit
    rows behind its aggregate were never recorded — and it is reported that way rather than estimated
    into a number.

  **What the bound buys, and the one place it changes the paper's emphasis.** The witness of §4.1 has
  two forms, and they are not equally robust. Its **count form** — the sign channel clears its own
  resolution in `{{X:facts.claim1.blocks_exceeding_own_mde.value}}` of
  `{{X:facts.claim1.blocks_total.value}}` blocks — needs
  `{{F:F1_1_witness.legs.count.k_inversions}}` block inversions to reverse, and inverting a block's
  median takes more than half of that block's paired observations
  (`{{F:F1_1_witness.paired_observations_per_inverted_block}}`), so the count form resists any change
  to fewer than `{{F:F1_1_witness.legs.count.k_paired_observations_lower_bound}}` paired observations.
  Its **aggregate-interval form** needs `{{F:F1_1_witness.legs.interval.k_inversions}}` blocks —
  `{{F:F1_1_witness.legs.interval.k_paired_observations_lower_bound}}` paired observations — because
  the aggregate's interval is tight and two well-placed blocks erase it. The identity leg is stronger still: the
  scalar-feature gap is exactly zero in every block, and no change to the streams can move a quantity
  that is zero by construction, so it has no flip bound at all. The paper therefore reports the
  identity and the count as the load-bearing evidence for the witness and treats the aggregate
  interval as the weaker statement it is — which is what a flip bound is for. The external ordering
  (§4.3) carries the largest margins on this instrument
  (`{{F:F1_3_ordering.sched.k_inversions}}` / `{{F:F1_3_ordering.paging.k_inversions}}` /
  `{{F:F1_3_ordering.ski.k_inversions}}` pair inversions for scheduling, paging and ski rental), and
  the external *reach* statement is the weakest headline in the paper by this measure: no profile
  reaches the published robustness scale, and a single profile would (`L3`), which is why the excluded
  profiles are listed one by one in §4.3 rather than summarised.

