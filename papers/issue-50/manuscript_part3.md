## 4. Results, in the order the study registered them

### 4.1 How to read this section

The study registered six success criteria and four prior beliefs before its deciding runs, and this
section reports them in the registered order. Each criterion is reported **met** or **unmet with the
reason**; no criterion is silently replaced by a nearby quantity that happens to be available, and no
number here is typed: every one is computed from a committed artefact by the assembly step. What that
step *enforces* is a named list rather than everything: the six registered verdicts must be the words
the deciding artefacts carry (A), every section reference must resolve (B), every figure must be
embedded and pointed at (C), the headline measurements must not be typed into the prose (D), and every
quantified sentence -- a ratio, or a count of a registered set -- must rest on two independent
bindings of one declared domain, with no registered count left unquoted (E). A sentence that
disagrees with a measurement one of those checks covers fails the build; a number outside their reach
is the review's, which is what the round-1 review found and what this revision repairs.

Of the six criteria, {{n_criteria_unmet_outright}} are unmet outright and {{n_criteria_unmet_part}} more
carries an unmet part, and in each case the reason is itself a result: (ii) is unmet, the separation
coming out in the opposite direction to the registered one (4.4); (v) is unmet, for the closed-form
comparison found no comparable boundary to compare against (4.7); and (i) is partly unmet, the
sharpness statistic having asked for a fall the measured windows do not contain (4.2). Section 4.9 records a correction the study made to one of its
own earlier readings, because the wrong reading was reported first.

### 4.2 (i) The boundary, cell by cell

Six pool sizes were swept at `h = 1.0` with {{boundary_seeds}} seeds each. **{{b_families_located}} of
{{b_families_total}} families located a crossing and {{b_families_ambiguous}} were ambiguous**:
every family had exactly one
positive-to-nonpositive sign change inside its window, which is the condition the crossing rule
requires before it will report a number at all.

`rho*` declines across the range (Figure 1): {{rho_star_A16}} at `A = 16` and {{rho_star_A96}} at `A = 96` for the
speculative arm, {{rho_star_serial_A16}} to {{rho_star_serial_A96}} for the serial arm. The span is
{{rho_star_span}}, against a mean per-seed interval width of {{rho_interval_width}} -- a ratio of
{{rho_span_over_interval}} -- but the decline is not strict, and the artefact records the step itself:
{{rho_star_A64}} at `A = 64` sits above {{rho_star_A48}} at `A = 48` by {{rho_rise_A48_A64}}, a rise
smaller than that interval width, so the statement is about the mean and not about every step. A
two-sample comparison of the two extreme pool sizes gives a difference of
{{rho_two_sample_delta}} with an interval of [{{rho_two_sample_ci_lo}}, {{rho_two_sample_ci_hi}}], which
excludes zero and therefore does not rest on the span exceeding an interval width.

The boundary's location does not follow from contention alone. Cells from *different* pool sizes whose
measured contention agrees to within {{boundary_tol}} number {{boundary_matched_pairs}} pairs, and
**{{boundary_matched_disagreeing}} of them disagree in sign** -- two cells at the same measured
utilisation, one with a positive mean benefit and one with a negative one. That is the empirical form of
the paper's central claim, and it is why the boundary is written `rho*(A, h)` rather than `rho*`.

![The boundary over six pool sizes at `h` = 1.0: mean per-step benefit against measured contention `rho`, each family's located crossing marked by a dashed rule. The crossing moves from {{rho_star_A16}} at `A` = 16 to {{rho_star_A96}} at `A` = 96, and cells of different pool sizes at the same measured contention sit on opposite sides of zero.](figures/fig1_boundary.svg)

**Unmet, with the reason: the sharpness statistic.** The registration asked for the `rho`-width of the
fall from +5% to -5% of serial latency. The windows were chosen to bracket the *zero* crossing, which is
what `rho*` is, and they therefore do not contain a +5% to -5% fall: across all
{{boundary_seeds}}-seed cells in all families the benefit runs from {{window_benefit_max}}% down to
{{window_benefit_min}}%, so the windows never reach -5%, and only one family ever exceeds +5%. The
nearest quantities the study does have are the crossing bracket's own `rho`-width
({{bracket_width_min}} to {{bracket_width_max}}, a grid-resolution quantity) and the fall's *slope*,
which the tail study measures directly (4.4). Reporting either as if it were the registered statistic
would be exactly the substitution this section exists to avoid, so the criterion is reported unmet and
the measurement that would satisfy it is stated: a sweep designed to bracket `+/-5%` rather than zero,
which needs cells well outside every window measured here.

### 4.3 The pool effect is not the service time

The registered belief behind the boundary was that the amount of latency available to hide indexes it.
The instrument's decomposition separates the per-step benefit into three terms -- the hiding channel `S`
(the share of the call the thinking absorbs), the overshoot debit, and the wait the step spends behind
other steps' speculative calls `w_s` -- and the pool-size contrast, over {{dec_contrast_cells}} matched
cell pairs, is carried by the debits rather than by the hidden quantity:
**{{dec_carrying_overshoot}} of {{dec_contrast_cells}} pairs** have the overshoot term as their largest
contributor, and the mean absolute movement of that term is {{dec_overshoot_abs}} percentage points of
step latency against {{dec_S_abs}} for the service term. What moves the boundary as the pool grows is
not how long a call takes but whether it is displaced at all.

### 4.4 (ii) The tail separation test: refuted in both halves

The registered claim had two halves: a heavier tail gives a *larger* `rho*` (more to hide) and a
*steeper* fall past it. Both are refuted, and the second refutation is the interesting one.

The premise holds first (Figure 2), so the comparison is not confounded: the two latency classes are mean-matched
by construction, with a worst relative mean gap of {{tail_mean_gap_rel_worst}} over the two families, and
the heavy class does have the *larger* unloaded hiding limit ({{tail_hiding_limit_heavy}} against
{{tail_hiding_limit_light}}). That is the quantity the registered belief said would order the boundary.

![The registered tail claim, refuted: mean-matched heavy and light latency classes, paired by seed, at three pool sizes. In {{tail_families_located}} of {{tail_families_tested}} located families the heavy tail's boundary sits *below* the light tail's, and the paired difference is strictly below zero.](figures/fig2_tail.svg)

* **First half, refuted.** In **{{tail_families_located}} of {{tail_families_tested}}** located
  families the heavy tail's boundary is **below** the light tail's, not above it: at `A = 16` the paired
  difference is {{tail_delta_A16}} with an interval of [{{tail_delta_ci_lo}}, {{tail_delta_ci_hi}}],
  entirely below zero.
* **The registered separation is not remotely met.** The criterion asked for a difference of at least
  0.15 in `rho*` with disjoint intervals. The largest absolute difference over the three families is
  {{tail_delta_worst_abs}} (at `A = {{tail_delta_worst_A}}`) -- smaller than the registered threshold by
  a factor of {{tail_shortfall_factor}}, and about {{tail_delta_over_pool_span}} of the span that the *pool size* buys. The tail is not
  the coordinate that locates this boundary.
* **Second half, refuted.** The fall past the crossing is *shallower* for the heavy tail, not steeper:
  measured as the secant from each seed's own crossing over the two cells above it, the heavy class
  falls at {{tail_fall_heavy_A16}} benefit-percent per unit `rho` at `A = 16` against
  {{tail_fall_light_A16}} for the light class, and the paired difference is strictly below zero in three
  of three families at {{tail_fall_step}} cells (in one of three at the single-cell sensitivity reading).

So the criterion is **unmet**, and the reason is a measurement rather than a shortfall: the tail moves
`rho*` by roughly a fifth of a percent while the pool size moves it by two percent, in the opposite
direction to the registered one, and the ordering the registration predicted is not what the
distribution's tail weight does to a queue.

### 4.5 (iii) What prediction buys: the matched-parallelism control

The registered criterion asked whether the fraction `F` of the gain attributable to prediction stays
below 0.7 once the baseline is allowed to spend the same capacity on unpredicted useful work. That
control was built directly: two arms issue **exactly the same number of early calls against the same
pool** -- the identity `k` = {{variant_k_by_width}} early calls per agent at the three widths,
verified over {{variant_identity_runs}} runs with {{variant_identity_bad}} exceptions -- differing
only in *which* steps are issued
early -- the treatment picks the steps with the largest hideable amount, the control picks uniformly at
random. `F = (G_selected - G_blind) / G_selected`, paired by seed.

Over {{variant_cells}} cells ({{variant_h_values}} in width by {{variant_c_values}} in pool size,
{{variant_seeds}} seeds each), **`F` is below 0.7 in every cell**, from {{F_min}} to {{F_max}}: at
`h = 0.25` it is {{F_h025}} (Figure 3), at `h = 0.50` {{F_h050}} with an interval of
[{{F_h050_ci_lo}}, {{F_h050_ci_hi}}], and at `h = 0.75` {{F_h075}}. In words: at half width, a blind
schedule of the same size already buys {{blind_share_h050}} of the informed gain.

The registered *direction* is not the direction the data has. The registration predicted `F` falling in
`rho`; what the data shows is `F` falling in the **width** `h` -- a factor of about
{{F_ratio_narrow_to_wide}} from the narrowest to the widest setting -- while at fixed `h` the pool
coordinate changes nothing at all once the pool is at least the agent count (`c = 4, 8, 16` are the same
run; only `c = 2` differs). The criterion's threshold half is **met at every cell**; its registered
direction is **not met**, and the honest report is both.

**The other reading of the same threshold, reported rather than chosen.** The same 0.7 was tested
earlier against a different quantity: the share of the net benefit contributed by the hiding channel,
rather than the share of the gain that information buys over a blind schedule of equal width. Read that
way the number is not below 0.7 but above 1 (minimum {{channel_F_min}}, rising with `rho`, Spearman up to
{{channel_spearman_worst}}): at these rates the unit benefit really is the hiding channel, with the
debit terms subtracting from it. That reading does not test the registered sentence, which names a
matched-capacity blind baseline, and both readings are stated here so that a reader can see which
quantity each one is about.

![What prediction buys against a blind schedule of the same width: `F` at two pool sizes and the blind arm's share `1 - F`, against the speculation width `h`. `F` is below the registered 0.7 at every width; it falls with `h` rather than with contention, and at half width the blind arm already carries {{blind_share_h050}} of the informed gain.](figures/fig3_prediction.svg)

### 4.6 (iv) The side-effect channel: a smaller shrinkage than registered, and a permitted-but-harmful set that is not empty

The registered belief had three parts; it is confirmed, refuted, and confirmed.

* **The safe region shrinks -- confirmed.** With a non-idempotent fraction `q` and a compensating cost
  of `comp` worker-time units, **all {{p4a_families}} load-bearing families** have a paired shrinkage
  interval strictly above zero. Work that no step waits for still moves the boundary.
* **The registered magnitude -- refuted.** The registration expected a shrinkage of at least 0.05 in
  `rho*` at `q = 0.05`, `comp = 1.0`. The four families measured there shrink by between
  {{p4b_lowest}} and {{p4b_highest}}, all below the threshold, with a shortfall factor of
  {{p4b_shortfall}}. The channel is real and it is smaller than believed.
* **The permitted-but-harmful set is non-empty -- confirmed, and carried by individual steps.** Of
  {{p4c_cells_located}} cells that can be read, **{{p4c_cells_losing}} contain steps with negative
  benefit**, at a fraction between {{p4c_frac_lo}} and {{p4c_frac_hi}}. The other reading of the same
  claim is by construction ({{p4c_by_construction}} cells above a located crossing are negative whatever
  the crossing's location is), so the claim is carried by the step-level reading, not by the
  constructive one.

The step-level reading is what makes the finding concrete (Figure 4). At one cell at the boundary,
**{{m4b_neg_steps}} of {{m4b_steps}} steps have negative benefit** ({{m4b_frac_neg}}) while the mean
step gains {{m4b_mean_benefit}} and a losing step loses {{m4b_mean_negative}} -- a mixture in which
about half the steps pay for the other half, and only {{m4b_hidden_frac}} of steps can be hidden at all.
A rule that speculates only on idempotent edges does not remove those steps, because they lose to
contention rather than to a side effect.

![The step-level reading at the cells that straddle each family's crossing: the share of steps whose benefit is negative, with the artefact's own interval. Between {{p4c_frac_lo}} and {{p4c_frac_hi}} of steps lose, while the mean step at those cells still gains -- about half the steps pay for the other half.](figures/fig4_mixture.svg)

**A declared-load law is inconsistent.** If the charge were a matter of load alone, families with the
same declared load and different `h` would shrink by the same amount. Their intervals are not merely
different but disjoint. The effect is carried by the slope rather than by the load level
({{db_per_load_lo}} to {{db_per_load_hi}} basis points per unit load between two families at the same
load `q = 0.01`, `comp = 1.0`), and the load that would be required to reach the registered 0.05
threshold differs by a factor of about {{load_for_threshold_ratio}} between two families of the same
pool size ({{load_for_threshold_lo}} against {{load_for_threshold_hi}}). The charge channel is therefore indexed by the same three coordinates
as the boundary, not by a scalar load.

### 4.7 (v) The closed-form fixed point: no boundary to compare with

The criterion asked the closed-form fixed point to land within +/- 0.05 of the simulated `rho*` in at
least 80% of cells. **It is unmet, and the reason is a property of the comparison, not a tuning
residual**: the criterion was read over {{fixedpoint_evaluated}} swept (family, width) pairs, and all
{{fixedpoint_excluded}} of them were excluded for one kind of reason -- the closed-form model's
benefit stays positive at every pool size from 1 upwards, so it has no
boundary in the simulated window to be compared with. (The unit matters: a *pair* is a family at a
width, and it is not the same object as the {{fix_secondary_n}} same-cell rows the secondary reading
below counts.) No pair produced a boundary in both models' own terms, and the fraction is therefore
undefined rather than zero.

What the study reports instead is a *secondary* reading in a coordinate both models do have: at equal
`rho` and equal `h`, the closed-form and simulated *benefits* agree within the declared tolerance in
**{{fix_secondary_within}} of {{fix_secondary_n}} rows**, a median absolute difference of
{{fix_secondary_median}} percentage points of step latency and a worst case of {{fix_secondary_worst}}.
This is reported as a secondary reading of a different quantity, and it does not discharge the criterion.

### 4.8 (vi) The external cell: the published sign reproduces, and one magnitude does not

Three published cells from three independent 2026 systems were read at their own reported operating
points ({{ext_cells}} cells, sources and quoted sentences recorded in the artefact). **The published
sign reproduces in {{ext_sign_match}} of {{ext_cells}}**, with both signs computed rather than the
model's sign compared against a constant.

* **SPORK** (reported P95 reduction {{ext_spork_published}}%): the model's band for the reported region
  is [{{ext_band_lo}}, {{ext_band_hi}}]%, the reported region maps to a required tool-wait share in
  [{{ext_region_lo}}, {{ext_region_hi}}], and the model at the probe accuracy the paper itself reports
  gives {{ext_spork_probe}}% ([{{ext_spork_probe_ci_lo}}, {{ext_spork_probe_ci_hi}}]) against
  {{ext_oracle}}% for an oracle. The published number is **reached**.
* **Speculative Macro Commit** ({{ext_smc_telecom_published}}% latency reduction): **reachable** -- the
  model inverts the unloaded ceiling to state which tool-wait shares could produce that reduction, and
  the published number sits inside [{{ext_smc_band_lo}}, {{ext_smc_band_hi}}].
* **The same system's second benchmark** ({{ext_appworld_published}}%): **not reached**, and reported as
  such. The published reduction exceeds the model's unloaded ceiling {{ext_ceiling}}% -- the most a
  single-step speculation can buy when the tool wait is at most half the step -- so no tool-wait share
  reproduces it in this instrument. The shortfall is
  {{ext_appworld_shortfall}} percentage points, and the reason is the published
  mechanism: multi-step macro commits are outside this instrument's action space. Smoothing that into an
  agreement would have been the easier paper and the wrong one.

The criterion is **met** on the sign, which is what it asked for, with the unreachable magnitude
reported beside it rather than dropped.

### 4.9 The registered prior beliefs, one line each

| prior | registered claim | outcome |
|---|---|---|
| P1 | a sharp boundary `rho*(h)` exists and moves with the speculation rate | **unresolved as registered** -- the boundary moves with the *pool*; the registered closed-form law for its movement deviates in {{hr_deviating}} of {{hr_groups}} groups, and the shift decomposition is mixed ({{hshift_consistent}} of {{hr_groups}} groups consistent) |
| P2 | the tail, not the mean, sets the boundary; heavier tail gives larger `rho*` and a steeper fall | **refuted in both halves** (4.4) |
| P3 | the prediction-attributable fraction is below 0.7 and falls with contention | **threshold met at every cell; registered direction not met** -- it falls with the width, not with contention (4.5) |
| P4a | the safe region shrinks under a non-idempotent fraction | **confirmed** |
| P4b | the shrinkage is at least 0.05 at `q = 0.05` | **refuted** (shortfall factor {{p4b_shortfall}}) |
| P4c | an admissibility rule leaves permitted-but-harmful states | **confirmed**, carried by the step-level reading |

Three of the six registered beliefs were refuted or left unresolved, and the two that were confirmed did
not survive unchanged: P3's threshold held while its direction did not, and P4's shrinkage arrived an
order of magnitude smaller than registered. For a study whose contribution is a boundary rather than a
speedup, that is the expected shape -- but it is worth saying plainly that the pre-registration did not
make the results more comfortable; it made three of them falsifiable in advance, which is the only thing
it was for.

### 4.10 A correction we made to our own earlier reading

One reading reported during the study had to be corrected. An intermediate reading described the
step-level mixture as "83-99.7% of steps have negative benefit", computed as one minus the fraction of
*fully hidden* steps. That is not a count of steps with negative benefit: a step can be partly hidden and
still gain. The step-level reading reported in 4.6 counts the sign of each step's own benefit
({{p4c_frac_lo}} to {{p4c_frac_hi}} negative), and the two readings are of different quantities. The
mixture conclusion is unchanged -- about half the steps at the boundary lose -- but the sharp sentence
was wrong and is corrected here rather than in a footnote.

The correct sentence is the weaker and more useful one: at the boundary, roughly half the steps lose and
the amounts won and lost are of comparable size, so an average that is near zero is an average over two
populations rather than a uniformly small effect.
