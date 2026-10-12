## 6. The item–repeat budget boundary

### 6.1 The decision

A fixed budget buys items and repeats. If an item costs `a` and a repeat costs `b`, then with `M`
items and `N` repeats each, `B = M·(a + b·N)`. The score's variance has two parts: a within-item part
that the repeats average down, `sigma^2 / N`, and a between-item part that only more items reduce,
`tau^2 / M`. Minimising

    Var(M, N) = sigma^2 / N + tau^2 / M    subject to   M(a + b·N) = B

gives the population optimum

    N* = sqrt(a·sigma^2 / (b·tau^2)),      M* = B / (a + b·N*),

and the AM-GM minimum

    Var* · B = ( sqrt(a·tau^2) + sqrt(b·sigma^2) )^2 .

Two structural facts follow immediately and are the reason the boundary is worth stating. First,
`N*` does not depend on `B`: a bigger budget buys *proportionally more of both*, not more repeats —
measured across four decades of budget, the optimum moves by `{{v1.scalefree_move}}`.
Second, `Var*·B` is a constant, so the achievable error falls exactly as `1/B` — there is no regime
where more compute suddenly helps a lot.

### 6.2 The closed form is a relaxation, and its domain matters

The population form is a relaxation of the integer problem, and we state its domain rather than
presenting it as the answer. Over the interior of the grid it is tight: the worst relative error
between the relaxed and brute-force optimum is `{{v1.domain.interior_worst_rel}}` across
`{{v1.ab_cells}}` cells checked by two independent routes (worst relative disagreement
`{{v1.ab_worst_rel}}`). In the corner it is not: the relaxed form understates the achievable variance
by up to a factor of `{{v1.domain.corner_worst_ratio}}`.

The corner is where the decision is "buy no repeats at all", and there the continuous and discrete
problems genuinely differ. The relaxed boundary is `N* = {{v1.boundary_relax}}`. The *integer*
boundary is `N* = {{v1.boundary_discrete}}` — that is, `sqrt(2)`. The reason is that integrality
enters through the comparison `f(2) - f(1) = b·tau^2 - a·sigma^2/2`, so the discrete problem leaves
`N = 1` exactly when `a·sigma^2 > 2·b·tau^2`: **integrality widens the corner by exactly a factor of
two** in the parameter that decides whether to buy a repeat. Reporting the rounded continuous
boundary is therefore wrong by `sqrt(2)` in the one quantity the boundary exists to compute.

Controls bracket the mechanism on both sides: forcing the size-dependent variance to zero drives the
optimum to `N* = 1` exactly, and the zero-variance controls return the expected degenerate values
(`tau^2 = 0` gives `{{v1.ctl.tau2_zero_expect}}` and `sigma^2 = 0` gives
`{{v1.ctl.sigma2_zero_expect}}`). The interiority certificate reports
`{{v1.interior_cells}}` interior cells and `{{v1.interior_viol}}` violations.

![Figure 4](figures/fig4_budget.png)

*Figure 4. Left: the optimal repeats per item against the variance ratio, one line per item/repeat
price ratio — the optimum is scale-free in the budget. Right: the closed form's price; the
relaxation is tight in the interior and degrades in the corner.*

### 6.3 A pool cap is a floor

If the items are drawn from a finite pool of `K = {{v1.pool.K}}` and the same items may be reused,
the between-item term cannot be averaged below `tau^2 / K` no matter how large the budget grows — the
first thing a growing budget stops buying is *new* information. Concretely, at a budget large enough
for thousands of repeats the excess over that floor is `{{v1.pool.cap_excess}}`. The floor is the
reason the `1/B` decay of §6.1 is an idealisation: it holds until the pool binds.

## 7. Measuring the inputs: the empirical arm

The law in §3 and the boundary in §6 are only useful if `p`, `sigma^2` and `tau^2` can be measured.
This section measures them in a stochastic optimisation with a known ground truth: a linear model
comparison in which a *correct* model and a *misspecified* model compete, on a design grid of
difficulty cells `u`, with `{{v2.n_test}}` test rows, `{{v2.n_train}}` training rows and
`{{v2.r_runs}}` independent runs per cell, replicated `{{v2.n_reps}}` times. The data-generating
process has `{{v2.d}}` features of which `{{v2.k_info}}` are informative; `u` scales the omitted
block's coefficient relative to the value at which the two models tie.

**`p` is measurable, and it is large.** The measured per-run wrong-verdict rate is
`{{v2.p.u000}}` in the easiest cell, rising to `{{v2.p.u050}}`, `{{v2.p.u080}}`, `{{v2.p.u095}}` and
`{{v2.p.u099}}` as the difficulty approaches the crossing — a spread of `{{v2.p.spread}}x`. The
registered prior P2 predicted at least one cell above `p = 0.10` with more than a 2x spread; four of
the five cells are above 0.10.

**The resolution of `p` is part of the claim.** A proportion resting on a handful of events is not a
reading. The easiest cell is the binding one: at the originally planned run count it carried only
3.8 expected wrong runs, which the instrument's own gate refuses. At `{{v2.r_runs}}` runs it carries
`{{v2.p.events_u000}}` expected events, and every cell clears the 30-event floor. This matters beyond
bookkeeping: buying resolution is what *found* the two instrument defects recorded in §7.3, both of
which had passed at the lower run count.

**The folk convention is adequate in exactly one regime.** At `N = 3` the law's error is
`{{v2.ctl.n3_err_u000}}` in the easiest cell and `{{v2.ctl.n3_err_u099}}` in the hardest. The
three-run convention is a defensible default where `p` is small and is indefensible where it is not —
and the paper's point is that which of the two a study is in is *measurable in advance*, from a pilot
of runs the study is already doing.

### 7.1 The measured law reproduces

The measured inputs feed the §6 boundary: `sigma^2 = {{v2.sigma2}}`, `tau^2 = {{v2.tau2}}`, giving
`N* = {{v2.nstar}}` repeats per item. The exact conditional closed form predicts the measured
difference between the two models to within `{{v2.decomp_worst_z}}` standard deviations at worst — at
the middle cell, `{{v2.cell.pred_u050}}` predicted against `{{v2.cell.meas_u050}}` measured — and
the per-cell check of `p`'s reproducibility across independent training halves is within
`{{v2.p_within_worst_z}}` standard deviations — the reproducibility check holds its own nuisance
fixed, since comparing `p` across *different* test sets measures `tau^2`, which is a different
quantity and is reported separately.

### 7.2 Criterion (ii): the law predicts the observed majority error

The law's predicted error is compared against the observed majority error of the actual runs, in the
same tie convention on both sides, over `{{v2.crit2_cells}}` countable cells: the prediction is
inside three standard deviations in `{{v2.crit2_frac}}` % of them, with `{{v2.crit2_excl}}` rows
correctly excluded as vacuous (too few expected wrong blocks to carry information). The prediction
used is the *mixture* of the per-test-set laws — see §7.3.

### 7.3 A prediction must condition on the same object as its observation

Two defects were found by buying resolution, and both have the same shape: a comparison whose two
sides averaged over different objects.

**The omitted block is owed twice.** Model A omits a block of features, and the exact conditional
error of A must carry not only that block's contribution to the test residual but also its effect
*inside the fit*: because the block is present in the data and absent from the model, it acts as extra
noise in A's training regression, inflating the estimation term by a factor. Until that second term
was carried, the prediction departed from the measurement by several standard deviations at the
informative cell — a discrepancy that was invisible at the lower run count, where the missing term
sat an order of magnitude below its own standard error, and that only buying resolution could expose.
With the term carried, the worst departure over the grid is `{{v2.decomp_worst_z}}` standard
deviations.

**A nonlinear law does not commute with averaging.** The observed majority error pools blocks drawn
from several independent test sets, while the original prediction applied the law to the cell's
*averaged* `p`. Because the majority-error law is nonlinear in `p`, the law of the average is not the
average of the law; at the middle cell the two forms differ by several standard errors of the pooled
observation — the measured gap is real, the wrong prediction is what created it. Predicting
the mixture — the block-weighted average of the per-test-set laws, which is legitimate because
*conditional on its own test set* a replication's runs are i.i.d. — restores agreement.

**The crossing is a construct, not a grid point.** The conditional crossing — the difficulty at which
the two models are exactly tied — is not a fixed `u`: across `{{v2.cross.reps}}` test sets of the
same design it moves from `{{v2.cross.u_rep0}}` to `{{v2.cross.u_rep3}}`, driven by the item axis. A
grid therefore cannot be built to *contain* it, and a design that requires a grid cell to sit on the
crossing is testing the draw rather than the construct. Solving each replication's own root and
measuring there, the constructed points read zero (worst `{{v2.cross.worst_z}}` standard deviations),
while the population form would call those same cells a win for one model by
`{{v2.cross.pop_se_rep0}}` to `{{v2.cross.pop_se_rep3}}` standard deviations.

### 7.4 The item axis

The population closed form of §6 drops a term: the correlation between the omitted block and the
*realised* test noise. That term has zero expectation over test draws but is a fixed offset for the
one test set a study holds, and its size is set not by the repeats but by the item axis. Its RMS is
`{{v2.item.250.ratio}}` times the population gap at `{{v2.n_test}}` test rows, falling to
`{{v2.item.16000.ratio}}` at 16000 — a log-log slope of `{{v2.item_slope}}`, against the `-0.5` that
`1/sqrt(N_test)` implies. In the `u = 0.8` cell it is `{{v2.cell.cross_u080}}` times the gap being
measured, i.e. of the same order as the effect the comparison is trying to resolve. The repeat axis cannot shrink it. This is the other end of the `N*` trade:
the same error can be bought with repeats or with items, and §8 shows the two have different prices.

## 8. The item-size axis: a third knob

`N*` above was computed at a fixed item size `T`. But `T` is not a constant of nature; it is a
choice, and it moves both inputs. Over a `{{v3.Tspan}}x` span in `T`, measured on the synthetic
design:

    tau^2(T) = c_tau / T          with  c_tau = {{v3.c_tau}}
    sigma^2(T) = sigma_inf^2 + c_sig / T   with  sigma_inf^2 = {{v3.sigma_inf}}, c_sig = {{v3.c_sig}}

The `tau^2` law is clean: a log-log slope of `{{v3.tau_slope}}` against the predicted `-1`, with a
chi-square consistency statistic of `{{v3.tau_chi2}}` on `{{v3.tau_df}}` degrees of freedom against a
99 % critical value of `{{v3.tau_chi2_crit}}`. Concretely, `tau^2` runs from `{{v3.tau_at_125}}` at
`T = 125` to `{{v3.tau_at_8000}}` at `T = 8000`.

![Figure 5](figures/fig5_itemsize.png)

*Figure 5. The two item-size laws, synthetic and real: the between-item variance falls as `1/T`
while the within-item variance floors, and the shape survives the swap of the data source.*

The `sigma^2` law is not a pure power law: it *floors* at `sigma_inf^2`. The reason is structural and
it is the same reason the item axis of §7.4 exists. The between-item spread is carried by
finite-test-set terms, which average down as `T` grows; the within-item noise is carried by the
*training* draw, which is common to every test point, so it cannot average down at all. More test
rows make each run more precise about the thing it is measuring, but they do not make the thing
itself more stable.

Because `T` enters both inputs, the three-knob budget has an **interior** optimum:
`T* = {{v3.Tstar}}` repeats `N*` at a fixed price ratio, with the size zero-variance control driving
`T*` to `{{v3.ctl.no_size_var}}` and the free-size control driving it to the cap
`{{v3.ctl.free_size}}`. Two-sided controls bracket the reference on opposite sides, which is what an
optimum claim owes.

The laws are held out, not fitted in place: predicting one item-size's values from the others'
fit leaves relative errors of `{{v3.holdout_rel_sigma2}}` for `sigma^2` and
`{{v3.holdout_rel_tau2}}` for `tau^2`.

## 9. Grounding: the same laws on a public benchmark

Synthetic laws are laws about a data-generating process. The question is whether they are laws about
*evaluation*. To answer it, the machinery of §8 is imported unchanged and the data is swapped for a
pinned public benchmark: UCI *Concrete Compressive Strength*, `sha256 {{v4.data_sha}}`, checked on
every read, evaluated by a real protocol in which a reduced feature set competes with the full one at
`{{v4.k_items}}` item sizes, `{{v4.n_train}}` training rows and `{{v4.r_runs}}` runs per cell.

**The shape survives.** `tau^2(T)` again falls as `1/T` — slope `{{v4.tau_slope}}`, chi-square
`{{v4.tau_chi2}}` on `{{v4.tau_df}}` degrees of freedom — and `sigma^2(T)` again floors, at
`sigma_inf^2 = {{v4.sigma_inf}}` with `c_sig = {{v4.c_sig}}`. The held-out relative errors are
`{{v4.holdout_rel_sigma2}}` and `{{v4.holdout_rel_tau2}}`. The interior three-knob optimum appears
here too, at `T* = {{v4.Tstar}}` with `N* = {{v4.n_star_in_budget}}` repeats.

**Baselines have to be tuned to be compared.** The reduced model here is not a straw man: on this
benchmark it wins, which is the empirical form of the warning that comparing an untuned classical
baseline against a tuned successor measures the tuning {ref:2607.09905}.

**The instrument's own truth assumption failed first.** The design intended the full model to be the
better one — it nests the reduced model, and nesting is usually taken to imply superiority. Measured
on the population, the gap is `{{v4.pop_gap}}` with standard error `{{v4.pop_gap_se}}`, i.e. the
*reduced* model wins: with this many training rows the extra parameters cost more variance than the
dropped features carry signal. The direction-agnostic instrument — which asserts a gap exists and
then *reads* its sign — caught this; a hand-flipped sign would have hidden it.

![Figure 6](figures/fig6_flat_p.png)

*Figure 6. The single-run wrong-verdict rate against the item size on the real benchmark: flat at
about one half across the whole tested span.*

**The refutation-shaped result.** The single-run wrong-verdict rate is `{{v4.p.T16}}` at `T = 16`,
`{{v4.p.T128}}` at `T = 128`, and `{{v4.p.T4096}}` at `T = 4096` — across the whole `{{v4.Tspan}}x`
span it is flat at about one half. This is the paper's sharpest empirical statement, and it is
negative: when two candidates are close enough that their scores are nearly tied, **no amount of test
data makes a single run's verdict reliable**. The rate is not a small-p regime that more items move
into; it is the tie regime, and it is where any comparison of near-equal systems lives. Buying items
and buying repeats are therefore not substitutes: items buy precision about the gap, repeats buy
reliability of the decision *given* that gap, and where the gap is small only the second helps.

## 10. Registered prior beliefs and success criteria, against their outcomes

The registration fixed three priors and five success criteria in writing **before the deciding runs**,
and this section reports them in the form the registration itself asks for: one status per prior, and
`met` or `unmet with its reason` per criterion. The registration's own `Outcome` line carries the same
statuses, so the two records are read against each other rather than taken separately.

| prior | registered direction | outcome |
|---|---|---|
| **P1** the exact law | the error of a strict-majority decision over `N` exchangeable repeats equals the exact binomial tail, and no simulation cell departs from it beyond its Monte-Carlo band | **CONFIRMED for exchangeable repeats** (§3.4) — with its **stated boundary measured**: at `p = 0.05`, `N = 7`, a dependence `rho = 0.1` raises the error `{{v0.corr.ratio010}}x` and `rho = 0.8` raises it `{{v0.corr.ratio080}}x` (§4), so `p` alone is not sufficient |
| **P2** `p` is not small | at least one measured cell has `p >= 0.10`, where three runs carry an error above 5 %, and `p` varies by more than a factor of two | **CONFIRMED** (§7): the measured rate spans `{{v2.p.u000}}` to `{{v2.p.u099}}`, a `{{v2.p.spread}}x` spread, and four of the five cells lie above `0.10` |
| **P3** the binding requirement switches | the runs needed are governed by *estimation* at small `p` and by the *decision* near `p = 1/2`, with a located crossover inside `(0.05, 0.40)` | **CONFIRMED** (§5): the switch is bracketed by the adjacent grid cells `p = 0.35` (estimation binds) and `p = {{v0.cross_p}}` (decision binds), i.e. at the registered interval's upper edge |

The registered success criteria resolve as follows.

| criterion | outcome |
|---|---|
| **(i)** the exact law agrees with Monte-Carlo in every cell (`\|z\| <= 3`), the disagreement reported per cell and not aggregated | **MET** (§3.4): two independent routes agree to `{{v0.ab_max_abs_diff}}` over `{{v0.ab_cells}}` cells, the Monte-Carlo agrees within `{{v0.mc_max_abs_z}}` standard deviations over `{{v0.mc_cells}}` cells, and the monotonicity invariants report `{{v0.mono_viol}}` violations |
| **(ii)** the measured-`p` arm's predicted error falls inside the observed interval in >= 90 % of cells | **MET** (§7.2): inside three standard deviations in `{{v2.crit2_frac}}` % of the `{{v2.crit2_cells}}` countable cells, with `{{v2.crit2_excl}}` correctly excluded as vacuous |
| **(iii)** the crossover `p*` is located as an interval with a two-sided control separating the two regimes, not merely as a fitted point | **MET** (§5): the switch is bracketed by two adjacent grid cells that each carry one regime (estimation at `p = 0.35`, decision at `p = 0.40`), so both sides of the located point are evidenced |
| **(iv)** the item–repeat budget boundary is located and its control separates | **MET** (§6.2): the relaxed and integer optima agree to a worst relative error of `{{v1.domain.interior_worst_rel}}` over `{{v1.ab_cells}}` cells checked by two independent routes, the mechanism is bracketed by controls on both sides, and the interiority certificate reports `{{v1.interior_cells}}` interior cells with `{{v1.interior_viol}}` violations |
| **(v)** every stochastic cell reports >= 3 seeds with an interval | **MET** (§7): `{{v2.r_runs}}` runs per cell in `{{v2.n_reps}}` independent replications, each cell reporting a standard error |

No registered prior is left unresolved and no criterion is unmet. The two refutation-shaped results in
this paper — the flat single-run wrong-verdict rate across a `256x` span in item size (§8, §9) and the
non-sufficiency of `p` alone (§4) — are *additional* findings the registered priors did not fix, not
failures of the ones they did.

---

## 11. Threats to validity

**The synthetic arm is Gaussian.** The measured `p`, `sigma^2` and `tau^2` of §7 come from a linear
model comparison with Gaussian noise. §9 answers this partially, by re-running the same machinery on
a real benchmark, and the laws survive the swap — which is evidence that the laws are about the
*shape* of the variance rather than about the noise family. It is not proof, and a heavier-tailed or
heteroscedastic protocol could move the coefficients `c_tau` and `c_sig`.

**The dependence model is a two-state chain.** Real correlation is not Markov over runs, and the
effective-sample-size correction of §4 is a first-order answer. The correction is directionally
right — dependence always makes the i.i.d. law optimistic — but the *magnitude* is model-dependent,
and a study should treat `N_eff/N` as an estimate with its own uncertainty.

**Rank aggregation over more than two candidates is not treated.** The law here is for a pairwise
decision. Extending it to a winner among `k` systems changes the object (the error of the argmax over
`k` noisy scores) and adds a comparison multiplicity that {ref:10.1111/j.2517-6161.1995.tb02031.x}
addresses for tests but not for the repeat axis.

**The budget model prices an item and a repeat linearly.** Real evaluation cost is often step-shaped
(a repeat re-uses a trained artefact; an item may require new annotation). The boundary's *structure*
— that `N*` is scale-free in the budget — does not depend on linearity, but the constants do.

**What remains valuable despite these.** The three claims that survive every limitation are: (i) the
decision's error is exactly computable from a measurable `p` and the rule used; (ii) the repeat
budget and the item budget trade against each other with different scaling laws, so the split is a
decision and not a convention; and (iii) the single-run verdict rate can be flat at one half across
orders of magnitude of item size, so "buy a bigger test set" is not a remedy for unreliable single
runs. Each of these is falsifiable and each is checked against a committed artefact.

## 12. Reproduction

Every number in this document is resolved from a committed artefact by `build_manuscript.py`, which
refuses to build when a placeholder has no owner, when an owned number is never used, when an
artefact is unreadable, or when fewer than 100 references are cited. The instruments are
`spike_v0.py` (the exact law and its three checks), `spike_v1.py` (the budget boundary),
`spike_v2.py` (the measured inputs), `spike_v3.py` (the item-size axis) and `spike_v4_grounding.py`
(the public-benchmark grounding). Every instrument's certificates carry a plant control.
`spike_v1.py`–`spike_v4_grounding.py` expose `--selftest`, which plants a defect per certificate and
requires it to fire (`spike_v2.py`–`spike_v4_grounding.py` additionally require the healthy case to
hold), and `spike_v0.py`'s control is the separate harness `plant124.py`, which plants three defects
against a clean copy of the instrument. A certificate that passes on every planted defect is reported
as decoration; `reproduce.sh` runs every one of them.

The reference layer is regenerated from the verified pool rather than assembled by hand: every entry
was checked against a live external record by title comparison, and an identifier that merely
*resolves* is not accepted, because a remembered identifier can resolve to a different real paper.
