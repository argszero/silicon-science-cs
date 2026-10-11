# How Many Runs Does a Claim Need? The Repeat-Count Law of Stochastic Evaluation, and the Item–Repeat Budget Boundary

*Contribution level: `theory+empirics` — an exactly computable law, twice derived and Monte-Carlo
checked, plus a measured-input arm on a real stochastic optimisation and a grounding arm on a pinned
public benchmark.*

## Abstract

A stochastic evaluation is routinely decided by a majority over a handful of repeats: three runs,
five seeds, best-of-n generations. The field has spent a decade answering *how many items* such an
evaluation needs — sequential stopping rules, power analyses, item-response models, variance
decompositions — while the **repeat** axis has stayed at the folk constants `N = 3` and `N = 5` with
no statement of what error they buy. This paper makes the repeat axis the estimand. We give (i) an
**exact** error surface `E(N, p, rule)` for a decision over `N` exchangeable repeats at a measured
per-run disagreement rate `p`, covering the strict-majority, unanimity, any-of and mean-threshold
rules; (ii) the located **estimate-versus-decide crossover** — the `p` below which the binding cost is
measuring `p` and above which it is the decision itself; (iii) an **item–repeat budget boundary**
`N* = sqrt(a·sigma^2 / (b·tau^2))` that is scale-free in the budget, with the AM-GM optimum
`Var*·B = (sqrt(a·tau^2) + sqrt(b·sigma^2))^2` and a boundary that moves from `N* = 1` to
`N* = sqrt(2)` when integrality is made explicit; and (iv) the **item-size axis**, where the two
inputs obey `tau^2(T) = c_tau / T` and `sigma^2(T) = sigma_inf^2 + c_sig / T`, giving an interior
three-knob optimum. The laws are then measured, not assumed: on a synthetic stochastic optimisation
the inputs are estimated as `sigma^2 = {{v2.sigma2}}` and `tau^2 = {{v2.tau2}}`, and on a pinned
public benchmark (UCI *Concrete*, `sha256 {{v4.data_sha}}`) `tau^2(T)` falls as `1/T` with a log-log
slope of `{{v4.tau_slope}}` against the predicted `-1` — the prescription is about the *shape* of the
variance, not a Gaussian data-generating process. The
sharpest empirical result is a refutation-shaped one: across a `{{v4.Tspan}}x` span in item size the
single-run wrong-verdict rate stays flat at about one half (`{{v4.p.T16}}` at `T = 16`,
`{{v4.p.T4096}}` at `T = 4096`), so where two models are nearly tied, buying test items does not make
a single run's verdict reliable — "bigger test set" and "more seeds" are not substitutes. Every
number in this paper is resolved from a committed artefact by the build script that renders it.

## 1. Introduction

Consider the ordinary act of comparing two models on a benchmark. Run the comparison `N` times,
count the wins, report the winner. `N` is almost always 3 or 5, and it is almost never derived. The
same convention appears in RL seed studies, in LLM judge ensembles, in verifier cascades, and in the
journal's own review process, where experimental rigor is scored on repeated runs.

The natural question — *how many runs does a claim need?* — is answerable, but only if two things are
separated that the literature habitually fuses. The first is **estimation**: how many runs are needed
to know `p`, the rate at which a single run disagrees with itself (or rather, the rate at which a
single run reaches the wrong verdict). The second is **decision**: how many runs are needed for the
majority verdict itself to be right. These two requirements have different laws, they diverge in
opposite directions as `p` grows, and the folk constants sit inside a regime where neither is met.

This paper supplies both laws, the crossover between them, and the budget geometry that follows when
the items and the repeats are competing for the same compute. It is a theory paper in which the
theory is *checked against the artefacts that measure its inputs*: the exact arm is verified by two
independent computational routes and a Monte-Carlo, and the measured arm estimates the law's
parameters rather than assuming them.

### 1.1 Contributions

1. **An exact error surface for decisions over repeats** (§3). For a strict-majority decision over
   `N` exchangeable runs at per-run error `p`, the family's error is a binomial tail, and we give it
   alongside the unanimity, any-of and mean-threshold rules and the even-versus-odd comparison at
   equal cost. The law is checked by two independent routes to `{{v0.ab_max_abs_diff}}` over
   `{{v0.ab_cells}}` cells and against a Monte-Carlo of `{{v0.mc_trials}}` trials.
2. **The estimate-versus-decide crossover** (§5). A located `p*` (measured at `{{v0.cross_p}}`)
   separating a regime where the run count is set by the precision of `p` from one where it is set by
   the decision.
3. **An item–repeat budget boundary** (§6). With one unit of budget buying either an item or a
   repeat, the population optimum is `N* = sqrt(a·sigma^2/(b·tau^2))`, **independent of the budget
   size**, with the AM-GM variance
   `Var* = (sqrt(a·tau^2) + sqrt(b·sigma^2))^2 / B`. The closed form is a *relaxation*: we state its
   domain, and we show that integrality moves the corner from `N* = 1` to `N* = sqrt(2)`.
4. **The item-size axis** (§8). `T` is a genuine third knob: `tau^2(T) = c_tau/T` while
   `sigma^2(T) = sigma_inf^2 + c_sig/T`, so the optimum in `T` is interior.
5. **Measurement, not assumption** (§7, §9). The law's inputs are estimated in a stochastic
   optimisation and then re-estimated on a pinned public benchmark, where the *same* machinery,
   imported unchanged, yields the same shape.

### 1.2 What this is not

This is not a claim that three runs is always wrong. At `p = {{v2.p.u000}}` — a comparison so lopsided
that a single run is essentially never wrong — three runs is generous, and the honest prescription is
to spend the money on items. The claim is that the required `N` is a *function of a measurable
quantity*, that the function is exactly computable, and that the field currently has no practice of
measuring the argument.

## 2. Related work

**Repeat counts and statistical power.** The closest literature establishes that seed counts matter,
chiefly by power analysis. Henderson et al. compute the number of random seeds a deep-RL comparison
needs to reach a given power {ref:1806.08295}; subsequent work extends power reasoning to cluster
analysis {ref:2003.00381}, to bias-assessment tests {ref:2501.04683}, to genetic-algorithm power manifolds
{ref:2209.00215}, and to sample-size formulas for machine-learning studies {ref:2609.09547} {ref:2409.06180}.
Related planning work treats variance reduction as the lever that lowers the required count once the
target is a mean rather than a decision {ref:2209.13858} {ref:2604.06796}. These answer *how many seeds
for a fixed detectable effect*, on an average; they do not state the error of the aggregation rule the
seeds are fed into, and they do not connect it to a measured run-to-run disagreement rate. The distinction is not pedantic: the mean-threshold rule and the
majority rule have different error laws under the same `p`, and only the latter is what practitioners
report.

**Variance in benchmark evaluation.** A second line measures how much evaluation results move at all:
`Quantifying Variance in Evaluation Benchmarks` {ref:2406.10229}, the demonstration that single-seed
benchmarks fail in Bayesian deep learning {ref:2604.23114}, the finding that repetitions strengthen
reliability in LLM evaluations {ref:2509.24086} and that multiple generations carry information a single
one does not {ref:2502.08943}. This
Variance is also used as a *signal* rather than a nuisance — hallucinations live in variance
{ref:2601.07058} {ref:2507.04137}, variance-stabilised and variance-regularised estimators appear
throughout {ref:2508.12042} {ref:2608.21559} {ref:2609.35473}, including in software-engineering
prediction where the variance of fault predictors is measured directly {ref:2310.17264}, and a
speculative-evaluation study measures how much of a stochastic evaluation can be short-circuited
{ref:2609.28560}. This work establishes the *phenomenon* — that `p` is far from negligible. It does
not convert the phenomenon into the number of runs a decision needs, which is the step this paper
takes.

**Significance testing for model comparison.** The classical treatment of "is A better than B" is
statistical: paired tests over folds {ref:10.1162/089976698300017197}, recommended protocols
{ref:10.1023/a:1009752403260}, cross-validation surveys {ref:10.1214/09-ss054}, sequential cross-validation
{ref:1206.2248}, and the NLP-specific guidance that made significance testing routine {ref:1809.01448}.
Multiple-comparison control is standard {ref:10.1111/j.2517-6161.1995.tb02031.x}. These tests are about
the *items*; the repeats enter only as a nuisance, and the test's own error is the object, not the
error of a rule applied to the repeats.

**Item-response and adaptive evaluation.** The item axis now has a mature methodology: IRT for
evaluation scales {ref:1605.08889}, IRT-based test-set comparison {ref:2106.00840}, IRT for safety
{ref:2608.05086}, contextual multidimensional IRT {ref:2608.22295}, multilingual extensions {ref:2606.15643}, and
the diagnosis that benchmarks are lost without it {ref:2505.15055}. Adaptive testing appears as an
efficient allocation scheme {ref:2511.04689} {ref:2603.23506} {ref:2603.21362}. Item quality itself is studied
{ref:2503.10533} {ref:2601.02580} {ref:2511.04120}. Item-aware evaluation extends to memory and
competency measurement {ref:2609.35312} {ref:2603.02663} {ref:2509.22888}, to difficulty prediction
from simulated students {ref:2507.05129}, to rubric-based assessment {ref:2507.08487}
{ref:2503.20182}, and to score imputation for missing annotations {ref:2506.20119}; the question of
*which items to spend on* is studied directly {ref:2501.18251} {ref:2609.37515}. This is precisely the
budget axis that the repeat axis competes with — and, as §6 shows, the two have different scaling laws, so the split is a decision,
not a convention.

**LLM-as-judge reliability.** The repeat problem is now most visible where judges are stochastic:
LLM judges give different answers on re-runs, and the reliability literature has grown quickly
{ref:2311.00681} {ref:2411.15594} {ref:2412.12509} {ref:2402.10770} {ref:2408.13006} {ref:2506.13639} {ref:2601.22548}
{ref:2606.13685} {ref:2510.25860} {ref:2512.09662} {ref:2601.11783} {ref:2607.22554} {ref:2603.03330}. Fragility under
prompt and ordering perturbation is measured {ref:2602.17316} {ref:2602.17262} {ref:2509.11026} {ref:2606.17634},
agreement and self-preference are audited {ref:2601.22548} {ref:2604.03376} {ref:2608.00717}, and the
general-purpose automated-evaluation frameworks that aggregate such judges are surveyed
{ref:2505.21389} {ref:2607.28282}. Ensembling and confidence estimation are the remedies the judge
literature reaches for {ref:2511.07364} {ref:2601.08118}, and human-sourced judging is under the same
pressure {ref:2205.11930} {ref:2509.14023}. Almost all of this reports *disagreement rates*; almost
none converts one into the error of the ensemble decision built from it.

**Reproducibility of stochastic results.** Reproducibility studies supply the field's prior that such
numbers are unstable: the AAAI reproducibility state of the art {ref:10.1609/aaai.v32i1.11503}, the
variance of RL agents across runs {ref:1904.06312}, meta-evaluation of MT research {ref:2106.15195}, seed
stability control {ref:2604.17694}, stress-testing of reasoning reliability {ref:2608.08514}, and the
double-descent reproducibility investigation {ref:2203.08124}. Human-evaluation reproduction is studied
in {ref:2308.06527} {ref:2107.14154}. Determinism-relevant sources of drift are catalogued — data
ordering {ref:1912.03606}, random initialisation in embedding stability {ref:2005.10039}, fine-tuning
instability {ref:2006.04884} — alongside replication studies that re-run an existing result and report
what moved {ref:2603.15034} {ref:2401.14429} {ref:2609.06133} {ref:2504.02587}. Artifact and reporting
infrastructure appears throughout {ref:1906.00299} {ref:2003.00381} {ref:2107.14154}. Our contribution sits downstream of all of it: given that the
reproducibility literature has established the instability, what does the instability *imply* for the
number of runs?

**Uncertainty in evaluation and benchmark reliability.** Recent work makes uncertainty explicit:
uncertainty and statistical variability in NLP evaluation {ref:2509.22612}, robust reliability of
benchmarks {ref:2509.04013}, benchmark-based evaluation robustness {ref:2509.04013}, the reliability of
evaluation under release decisions {ref:2609.32267}, blind spots in imbalanced-regression evaluation
{ref:2609.25152}, stability-based definitions of generalization {ref:2610.01428}, and the position that
evaluation scores are perishable claims {ref:2607.26191}. Methodological libraries for statistically
rigorous comparison are emerging {ref:2607.04429}, and validation-crisis findings show cross-validation
reducing benchmarking variance {ref:2606.12552} and rankings being less reliable than they look
{ref:2608.04613}. Benchmark construction is itself being redesigned for extensibility and fluidity
{ref:2509.11106} {ref:2604.12843}, amortised and confidence-gated evaluation is proposed as an
efficiency measure {ref:2503.13335}, and difficulty-level re-examination shows that generalisation
claims move with the level chosen {ref:2511.21692} {ref:2512.07795}. These are the closest in spirit;
the difference is that they quantify uncertainty about a *score*, whereas we quantify error about a
*decision over repeats*, which is what a claim is.

**Significance beyond the score.** A final cluster warns that significance of a score difference does
not transfer to significance about the system {ref:2511.02246}, that statistical earnestness is required
to re-evaluate headline results {ref:2605.28700}, and that evaluation practice must move from averages to
coverage {ref:2604.20763} {ref:2404.00748} {ref:2607.23514}. We agree, and we supply the missing arithmetic: the
coverage claim has a repeat budget, and the budget has a law.

**Positioning.** Three differences separate this paper from the nearest work. It makes the *repeat*
axis the estimand rather than a nuisance. It states the *rule* — not the mean — as the object whose
error is computed. And it joins the two axes into one budget, which the item-axis literature cannot
express because it fixes `N` by convention.

## 3. The repeat-count law

### 3.1 The model

A stochastic evaluation decides between two candidates by repeating a run `N` times and aggregating.
Each run is right with probability `q = 1 - p`; `p` is the per-run disagreement rate. Under
exchangeability the count of wrong runs is `X ~ Binomial(N, p)`.

For the **strict-majority** rule the decision is wrong when the wrong runs are a strict majority:

    E_maj(N, p) = P(X > N/2)      (with X ~ Binomial(N, p)),

and for even `N` the ties `X = N/2` are a third outcome, counted separately as *unresolved*:
`E_maj(2k, p) = P(X > k)` and `U(2k, p) = P(X = k)`. That third outcome is not a technicality. A
study reporting "4 of 5 runs" has a different quantity from one reporting "3 of 4", and the difference
is exactly the tie mass.

The rule matters enormously, and it is rarely the rule people think they are using. Under the same
`p = 0.10`:

| rule | `N = 3` | `N = 5` | `N = 10` |
|---|---|---|---|
| strict majority | `{{v0.maj.p010.n3}}` | `{{v0.maj.p010.n5}}` | `{{v0.maj.p010.n10}}` |
| unanimity | `{{v0.unanimity.p010.n3}}` | — | `{{v0.unanimity.p010.n10}}` |
| any-of | `{{v0.anyof.p010.n3}}` | — | `{{v0.anyof.p010.n10}}` |
| mean threshold | `{{v0.mean.p010.n1}}` | — | `{{v0.mean.p010.n10}}` |

![Figure 1](figures/fig1_repeat_law.png)

*Figure 1. Left: the exact error of the strict-majority decision against the repeat count, at four
per-run disagreement rates. Right: at a fixed `p = 0.10` the four aggregation rules diverge — the
unanimity rule's error RISES with `N` while any-of falls geometrically.*

Two things are worth reading off the table. First, **unanimity gets worse as `N` grows**:
`{{v0.unanimity.p010.n3}}` at `N = 3` rises to `{{v0.unanimity.p010.n10}}` at `N = 10`, because
requiring all runs to agree is a conjunction of `N` failure opportunities. A "we only accept
unanimous verdicts" policy is therefore not conservative — above a certain `N` it is worse than a
coin flip's complement. Second, **any-of collapses geometrically** (`p^N`: `{{v0.anyof.p010.n3}}` to
`{{v0.anyof.p010.n10}}`, ten orders of magnitude) while the mean rule falls far more slowly
(`{{v0.mean.p010.n1}}` to `{{v0.mean.p010.n10}}`, a factor of five over the same span). A
practitioner who replaces a majority vote with an average score, believing it to be more robust, has
changed the *law of large numbers regime* they were relying on.

### 3.2 Even beats odd at equal cost

If runs cost the same, an even `N` dominates the odd `N` above it, because the tie mass of the larger
`N` is the odd `N`'s error plus the ties. At `p = 0.10`: `{{v0.eo.p010.n3}}` for `N = 3`,
`{{v0.eo.p010.n4}}` for `N = 4`, `{{v0.eo.p010.n5}}` for `N = 5`. The consequence for practice is
that **the tie rule is a first-class design decision**: with an even `N` the study must say what a tie
means, and "we counted ties as a failure" is a policy with a computable price.

![Figure 2](figures/fig2_even_odd.png)

*Figure 2. Left: at equal cost an even `N` beats the odd `N` above it at every measured `p`.
Right: the tie mass is a third outcome, not a loss, and it is what an even `N` trades against.*

### 3.3 A rate is not a count

It is tempting to summarise the law by its large-deviation rate, `D(1/2 || p)`, so that the required
`N` is `log(1/eps) / D`. That summary is wrong in the regime where the number matters. At
`p = 0.49`, `D = {{v0.div.p049}}`, which predicts about `{{v0.div.p049.n25}}` runs for a 25 %
error, while the exact count is different by a factor that the rate cannot see: the exact binomial
tail is the ground truth and the rate is its asymptotic envelope, valid only once `N·D` is large. At
`p = 0.02` the same form gives `D = {{v0.div.p020}}` and a requirement of `{{v0.div.p020.n25}}` runs.
A law stated in the asymptotic language must carry the regime in which it holds; here that regime is
the *small-`p`* end, and the small-`p` end is precisely where the decision is easy and the counting is
hard. The exact tail, by contrast, needs no regime: at `p = 0.02` and `N = 3` it reads
`{{v0.maj.p002.n3}}`, a number the rate form cannot produce at any `N` because the rate is an
envelope rather than a value.

### 3.4 Verification

The exact arm is checked three ways. Two independent computational routes (a direct binomial tail and
an independent recursion) agree to `{{v0.ab_max_abs_diff}}` over `{{v0.ab_cells}}` cells; a
Monte-Carlo with `{{v0.mc_trials}}` trials agrees within `{{v0.mc_max_abs_z}}` standard deviations
over `{{v0.mc_cells}}` cells; and the monotonicity invariants report `{{v0.mono_viol}}` violations. A
control at `N = 1` returns exactly `p` (`{{v0.ctl.n1_err}}`), as it must, since a single run's error
is `p` by definition. At `p = 1/2` the law must read one half minus half the unresolved mass: it reads
`{{v0.ctl.p_half_N1000}}` with `{{v0.ctl.p_half_N1000_unres}}` unresolved at `N = 1000`, and exactly
`{{v0.ctl.p_half_N1001}}` at `N = 1001`, where no tie is possible.

## 4. Dependent runs: the boundary of the i.i.d. law

The law above assumes exchangeable runs. Real repeats are correlated: a seed changes more than the
initialisation, a judge's temperature is shared across a batch, a training run's environment leaks
into its successors. The registered prior for this paper (P1) anticipated exactly this boundary, and
the correction is standard: an effective sample size.

The classical treatment of agreement is the intraclass correlation
{ref:10.1037/0033-2909.86.2.420}, which is exactly the quantity a repeat count needs and almost never
the quantity a report supplies. We model dependence as a two-state Markov chain per run and show what
it costs at fixed `p` and `N`.
At `p = 0.05` and `N = 7`, independence gives `{{v0.corr.rho0}}`. A small dependence `rho = 0.1`
raises it to `{{v0.corr.rho010}}` — a factor of `{{v0.corr.ratio010}}` — and a strong `rho = 0.8`
raises it to `{{v0.corr.rho080}}`, a factor of `{{v0.corr.ratio080}}`. The effective sample size
falls in step, from `{{v0.corr.neff010}}` to `{{v0.corr.neff080}}` out of `N = 7`.

The control is the identity the correction is built on: at `rho = 0` the Markov error must equal the
i.i.d. error exactly, and it does, to `{{v0.rho0_identity}}`. A Monte-Carlo over the dependent chain
agrees within `{{v0.markov_mc_z}}` standard deviations. The practical reading is that **`p` alone is
not sufficient** — a study must report the disagreement rate *and* something about the dependence, or
its repeat count is calibrated against the wrong law.

## 5. Estimate versus decide: the crossover

Two requirements compete for the same runs. To *estimate* `p` to a relative precision, the runs needed
grow as `1/p` (a rate estimated from `N` Bernoulli trials has relative standard error
`sqrt((1-p)/(Np))`, which explodes as `p` shrinks). To *decide*, the runs needed grow as `1/D(1/2||p)`,
which explodes as `p` *approaches* `1/2`. The curves therefore cross, and the crossover is where a
study's budget should be spent on the other thing.

The exact law locates it. Requiring the decision's error below 5 % and the estimate of `p` to 25 %
relative precision:

| `p` | runs to decide (5 %) | runs to estimate `p` (25 %) | binding |
|---|---|---|---|
| `0.02` | `{{v0.req.p002.dec}}` | `{{v0.req.p002.est}}` | estimation |
| 0.05 | — | `{{v0.req.p005.est}}` | estimation |
| 0.10 | — | `{{v0.req.p010.est}}` | estimation |

![Figure 3](figures/fig3_crossover.png)

*Figure 3. The two requirements cross: as `p` shrinks the decision gets cheaper while the
measurement of `p` gets more expensive. The dotted line is the registered crossover `p*`.*

At small `p` the decision is cheap and the *measurement* is expensive: knowing that `p` is small
enough to trust three runs itself costs hundreds of runs. The registered prior P3 expected a located
crossover inside `(0.05, 0.40)`; the measured crossing sits at `p* = {{v0.cross_p}}`, above the
small-`p` cells in the grid, which is what the design anticipated. Above `p*`, a study that wants more
reliability should spend on the decision; below it, on the measurement — and, as §6 shows, below it
there is a third option, which is to spend neither and buy items instead.
