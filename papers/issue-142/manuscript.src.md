# The Knob Is Not the Curve: Identifying a Deployed Policy's Cost Curvature from a Price Sweep

*Contribution level: `theory+empirics` -- a theory model (an envelope identity, an error budget with a
derived span law, and an identifiability set) validated on **two independent, mechanically different
priced systems**, with an exact ground truth by construction and a one-command byte-identical
reproduction. The claims are scoped to the two in-silico systems actually measured; no external
deployment arm is claimed, and Section 9 states why.*

## Abstract

An operator of a deployed system routinely sets a knob -- an execution horizon, a replanning cadence, a
sampling interval -- and pays a price for it. The knob's value is chosen by an *unchosen* curve: the
marginal cost of the resource the knob buys. This paper asks whether that curve can be identified
**pointwise** from the logs the deployment already keeps, what its error budget is under measurement
noise, and which operating regimes carry **no information** about it at all. The instrument is a **price
sweep**: from one operating point the deployment logs `(L*, J, lam)` with `J = C(L*) + lam/L*` and
`C(L) = (1/L) int_0^L c`, so the logged combination `G := L* J - lam` is `int_0^{L*} c` exactly, and a
sweep of the price recovers `c` by differencing `G` -- with **no cost model and no plant model** on the
route. We build and measure this on two priced systems with ground truth exact by construction: (i) a
chunked-policy execution horizon (`c(d)` from an augmented Lyapunov solve of an LQR plant) and (ii) an
**age-of-information sampler** (`c(s) = 2 s2 (1 - e^{-theta s})`, a saturating exponential from an
Ornstein-Uhlenbeck source) -- a different mechanism, not a parameter swap.

Four falsifiable claims were registered against named prior beliefs, and the measurement decides all
four. **(P1, confirmed)** The noise-free error of the sweep is a **quadrature error**, not a modelling
error: the identity `G = int c` holds to a median of `8.6e-16` on system 1 and `5.6e-17` on system 2,
the sweep's error against its *correct* target (the span mean of `c`) is `4.5e-9` / `2.5e-16`, and
against the point value it is `1.39e-2` / `1.23e-2` -- the entire error is the span average.
**(P2, decided)** Under noise the sweep has an **interior, MSE-optimal span** whose scaling is
`h* ~ sigma^{2/(2b+2)}`, with `b` the *measured* bias exponent: `sigma^{1/3}` in the smooth limit
(system 1 `b=2.006 -> 0.334`, system 2 `b=1.957 -> 0.334`; the two agree to `0.0002`) and
`sigma^{0.41}` on each system's **delivered C0 representation** (system 1 `b=1.422 -> 0.408`, system 2
`b=1.423 -> 0.406`; the bias exponents agree to `0.001`). The exponent is set by the representation's
smoothness and the route's differencing, **not by the plant**. **(P3, decided)** The identifiable set is
the argmax set, predicted from the pricing **before any data**: the predictor is sound (0 false
positives at a `1e-2` resolution) but not exact (9 disagreements, 5 of 246 threshold-free), and the
pinned fraction matches exactly in **15/15 blocks** -- the failures are conservative and have a
mechanism. Both systems reproduce the *ordering*: the interior single-point marginal identity holds to
each grid's own first-order-condition resolution and **shrinks with the grid** (`8.2e-3 -> 9.0e-4`)
while pinned cells miss it by `~60x`. **(P4, refuted as stated, twice)** The two routes a practitioner
would reach for instead -- higher moments of the tracking error, and residual-dynamics system
identification -- were registered as addressing a *different object*. The measurement says otherwise:
the moments route's **level** reading is the **same object** (`r = +0.990`, refuting the registered
price-invariance), its **profile** reading is a genuinely different object (`r = -0.926`, the **wrong
sign on 303 of 303 cells**, a threshold-free direction failure), and the **system-identification** route
reaches the **same object** (`r = 0.9993...0.99999`, median `c`-error `1.3-7.5%` at a `1e5`-step log).
What separates the routes is **access**, not the object: the sweep reads one scalar per price, system
identification needs a raw `(state, action, delay)` log carrying the deployed control law. The design
rule the measurement supports is the opposite of "measure the same object a better way": **run a price
sweep, and first check whether you are pinned -- because if you are, no amount of data will tell you
the curvature.**

## 1. Introduction

An operator sets an execution horizon. A serving team picks a sampling interval. A storage tier picks
a replication level. Each of these is a **knob**: a scalar `L` the operator controls, whose value the
system's own economics price. Write the time-average cost the deployment pays for choosing `L` as
`J(L) = C(L) + lam/L`, where `C(L) = (1/L) int_0^L c(s) ds` is the cost of the resource the knob buys
and `lam/L` is the price of the knob itself -- one sample per `L`, one replan per `L`. The object that
decides the operator's choice is `c(.)`, the **marginal cost**: the curvature of a priced objective.
Nobody measures it. The operating value of `L` is found by a grid search, a hand-tuned default, or an
adaptive policy that *infers* the knob without ever reporting the curve beneath it.

The 2026 literature is a wave of exactly this inference, and it does not report the objective. On the
robotics side, adaptive-horizon systems -- ChunkTrust {ref:2609.39754}, Staircase {ref:2609.36471},
continue-or-replan {ref:2608.03483} -- treat the horizon as a latent variable with a posterior; their
result is a task-level gain, and none can say what `c(.)` is. The classical derivative-by-differencing
line -- Kiefer-Wolfowitz {ref:10.1007/978-1-4612-5110-1_9} and the derivative-free-optimisation family
{ref:2404.11893} {ref:2411.00112} -- gives bias-variance trade-offs for a *gradient* under *designed
perturbations* at points treated as non-optimal, targeting optimisation rather than reporting a
curvature. System identification on residual dynamics {ref:2502.15014} {ref:2506.03650} recovers the
*plant*; a cost is not a plant. And our own published work [#116] supplies the horizon's boundary law
and explicitly leaves `c(.)` unidentified, naming it as an open item -- which is where this paper
began, as a reader's question [rant] on that work.

This paper measures the missing object. The instrument is a **price sweep**, and its content is one
identity. From a single operating point the deployment logs the triple `(L*, J, lam)`, where `L*` is
the committed interval, `J` the achieved average cost, and `lam` the price. Define
`G := L* J - lam`. Substituting `J = C(L*) + lam/L*` gives `G = L* C(L*) = int_0^{L*} c(s) ds`
**exactly**, and by Leibniz `dG/dL = c(L)` -- so differencing the logged quantity `G` across a ladder
of prices identifies `c` pointwise, with **no cost model and no plant model on the route**. Nothing is
injected that a deployment does not already log; the sweep is a *move an operator can run*.

The paper answers four registered questions, in this order. Section 4 asks whether the noise-free error
is a quadrature error rather than a modelling error (P1). Section 5 asks for the error budget under
noise -- the interior MSE-optimal span and its law (P2). Section 6 locates the **identifiability
boundary**: the operating regimes in which neither route carries information about `c`, predicted from
the pricing alone (P3). Section 7 asks the headline question, whether the two practitioner routes
address a **different object** (P4), and reports that they do not. Section 8 states what the measurement
does not establish. The registered prior beliefs and the adversarial checks behind these choices are in
the companion registration.

**What changes if this is true.** The decision that changes is an operator's, and it is quotidian:
the choice between "tune the knob" or "adopt an adaptive policy" becomes "run a price sweep -- and
first check whether you are pinned, because if you are, no amount of data will tell you the
curvature." The reason it is not a trivial recommendation is that the sweep does not *work* everywhere,
and the places where it fails are exactly the places an adaptive policy silently operates: a horizon
pinned at its hardware floor or its budget ceiling is uninformative about `c`, and the measurement
gives that regime an exact address. If the pinned regimes had turned out to be informative, the
decision would have changed the other way -- the adaptive policy would have been the cheaper
instrument, and the sweep a redundant one. That is the falsifier P3 and P4 were registered to be able
to report, and Section 6 reports it honestly in the limb where it holds and the limb where it does not.

**Why two systems.** A single in-silico plant would leave the paper a case report. The instrument's
claims are claims about a *route* -- differencing an envelope identity across a price -- and the way to
show that is to instantiate the route on two systems whose mechanisms differ, so that a property which
survives both is a property of the route and a property that moves is the system's. System 1 is a
chunked-policy execution horizon, whose per-delay cost comes from an augmented Lyapunov solve of an LQR
plant -- a **controlled** system with a stability margin as its ceiling. System 2 is an
**age-of-information sampler** -- an **observed** system whose cost is a saturating exponential from an
Ornstein-Uhlenbeck source, with a hardware-minimum interval as its floor and a staleness tolerance as
its ceiling. They share the objective's *form* (`J = C(L) + lam/L`, `c` the marginal cost) and nothing
else: no LQR plant, no control law, no stability margin on the second.

## 2. Related work

Every work cited below is verified against a live external record by title match (826 verified pool
entries; the per-entry method, the returned record and the stated difference are in
`reference-check.md`, and each reference in the list at the end of this paper carries its own
one-line difference). The section is organised by the comparison the paper's difference claim rests
on, in eight groups.

### 2.1 Adaptive-knob systems: they report the knob, not the curve

The closest work is the 2026 wave of adaptive execution horizons. ChunkTrust {ref:2609.39754} adapts
a robot policy's horizon from action-expert evidence; Staircase {ref:2609.36471} streams inference
across large action chunks; continue-or-replan {ref:2608.03483} learns a Bernoulli continuation
decision and "Rethink before you execute" {ref:2608.09492} an adaptive execution scheme for
world-action models; skill-guided chunking {ref:2609.02042} and chunked PPO {ref:2609.36250} are
training-side counterparts; SplineWAM {ref:2609.39873} reshapes the horizon schedule into a
B-spline; consequence-aware commitment {ref:2610.07949} and history-conditioned regeneration
{ref:2610.14864} decide execution spans at inference. Around them sit a domain application
{ref:2610.01258}, a policy-acceleration method {ref:2609.34911}, a certification of accelerated
vision-language-action inference {ref:2610.08917}, an analysis of cloning behaviour {ref:2610.07056},
a measurement of the stability assumption behind chunking {ref:2610.01626} and a planner-to-policy
method {ref:2610.05331}; the founding visuomotor-policy result
{ref:1504.00702}, generalized advantage estimation {ref:1506.02438} and the field's survey
{ref:10.1007/978-3-642-27645-3_18} frame the horizon and the control frequency as design choices.
**Difference.** Each of these *infers* the knob and reports a task-level gain. None reports the
objective the knob is implicitly optimising, none gives that objective's error budget, and none can
say when its own signal is uninformative. Section 6 gives that regime an exact address.

### 2.2 Derivative by differencing: a gradient, under a designed perturbation

The classical root is Kiefer-Wolfowitz stochastic approximation {ref:10.1007/978-1-4612-5110-1_9},
whose modern theory continues in Spall's simultaneous-perturbation estimator {ref:10.1109/9.119632},
Polyak-Juditsky averaging {ref:10.1137/0330046}, the recursive-algorithms reference {ref:10.1007/b97441}
and the dynamical-systems account {ref:10.1007/978-81-951961-1-1}. Recent work extends convergence
under discontinuities {ref:2007.14069}, compares SPSA with RDSA {ref:2107.12771}, formalises the
theorem {ref:2202.05959}, proves exponential concentration {ref:2208.07243} and rates under biased
unbounded-variance noise {ref:2312.02828}. The derivative-free family allocates sampling
{ref:2404.11893}, transfers a prior into the perturbation {ref:2404.15751}, induces correlation
between points {ref:2405.05638} {ref:2502.20819}, studies finite-difference step rules empirically
{ref:2411.00112}, converges from a single observation {ref:2509.04424}, decides sampling by
sequential tests {ref:2509.14505}, denoises trajectories {ref:2509.14219}, fits regularised splines
{ref:2507.22176} or RKHS functionals {ref:2504.01289}, and analyses differentiators directly
{ref:1103.0652} {ref:1102.2599} {ref:1012.5483} {ref:1905.12745}; neighbouring contributions are
subgradient-free optimisation {ref:1806.08537}, actor-critic mean-variance analysis
{ref:2406.07892}, zeroth-order fine-tuning {ref:2410.09823}, log-density derivative estimation
{ref:1910.08280}, sparse-grid collocation {ref:1709.04562}, vector-field reconstruction
{ref:2503.08355}, parameter-shift derivatives {ref:2505.18090} and derivative-free SQP
{ref:2510.22458}. **Difference.** These give a bias-variance trade-off for a *gradient* under
*designed perturbations*, at points treated as non-optimal, targeting optimisation. We design no
perturbation: we difference a quantity the deployment already logs, and it is the **optimality of the
visited point** that makes the unobservable identifiable. Our span law is the same trade-off in a
different currency, and Section 5 shows its exponent is a property of the *representation*, not the
plant.

### 2.3 Extremum seeking: a real-time optimiser, not a reporter

Extremum seeking is the model-free optimiser closest to our route: the 2026 survey
{ref:2609.00484} reviews three revolutions and the road ahead, with gradient and Newton variants
{ref:2508.08485} {ref:2609.28728}, practical-stability and averaging analyses {ref:2507.15713}
{ref:2606.00969} {ref:2605.23029}, delay-robustness and unknown-delay variants {ref:2609.16523}
{ref:2604.04754}, unbiased and distributed schemes {ref:2509.21814}, constrained and saturating
designs {ref:2510.06403} {ref:2511.00208}, event-triggered implementations {ref:2601.14416}
{ref:2512.09113}, escape from local extrema {ref:2603.02823}, non-Lipschitz objectives
{ref:2609.04401} and a first hardware demonstration {ref:2508.20836}. **Difference.** Extremum
seeking optimises in real time from a *designed dither*, so by construction it never reports the
curvature in a form an operator can read off a price they already pay; and it is the delay and the
non-smoothness of the dither scheme, not of the representation, that its analyses bound.

### 2.4 The envelope and the economics of a price

The identity this paper instantiates is the envelope theorem, in the general choice-set form of
Milgrom and Segal {ref:10.1111/1468-0262.00296}, with an adjacent information-economics result
{ref:10.2307/3003320}, identification of multidimensional screening {ref:1411.6250}, the converse
envelope theorem {ref:1909.11219}, static and calculus-of-variations statements {ref:2108.10571}
{ref:2112.06815}, the Clarke-differential dynamic-programming version {ref:2509.17103},
non-parametric identification of a marginal product {ref:2011.00143}, learned pricing policies
{ref:2502.05776}, market-structure optimisation {ref:2602.15722} and pricing fresh data
{ref:2006.16805}. **Difference.** These establish when the derivative identity holds, or price a
product. None takes the price an operator *already pays* as the instrument, and none budgets the
error of the resulting estimate under measurement noise.

### 2.5 System identification and experiment design

The route a practitioner reaches for second is system identification. Input design and adaptive
experiment design {ref:1303.3181} {ref:1310.3973} maximise information by choosing the input;
closed-loop identification and direct data-driven control {ref:2301.12537} {ref:2304.02379}
{ref:2503.02985} {ref:2505.06407} {ref:2506.03650} {ref:2508.18813} recover a plant from a
trajectory; joint plant/controller inference {ref:2502.15014} and model-based RL exploration
{ref:2306.09210} {ref:2205.05787} couple identification to a control objective; identifiability and
design criteria {ref:2506.11311} {ref:1710.08062} {ref:1902.00931} {ref:2304.07949} {ref:2208.00549}
{ref:1906.08509} {ref:2303.02227} formalise what an experiment can determine; and estimation practice
{ref:2011.00925} {ref:2205.15009} {ref:2405.03154} carries the estimator. **Difference.** All of
these identify the *plant*, which is a different object from a cost, and all of them need an
experimenter's lever (an input, a stimulation, a trajectory) that a deployed system does not let an
operator pull. Section 7 measures the object question directly and reports the registered claim
refuted: what separates the routes is **access**, not the object.

### 2.6 Freshness, staleness and sampling

Our second system prices the age of information. The metric and its queueing analysis
{ref:10.1109/isit.2014.6875100} {ref:10.1109/tit.2018.2871079} are followed by scheduling and
sampling policies for freshness {ref:2001.04218} {ref:2001.09863} {ref:2109.04784} {ref:2205.04092}
{ref:2211.05797} {ref:2212.07114}, staleness in storage and unreliable channels {ref:2005.07798}
{ref:2201.02929} {ref:2412.18119}, rate/error trade-offs {ref:2012.09351}, metric refinements
{ref:2307.00535} {ref:2606.04361}, sampling-timing effects and non-stationarity {ref:2308.07905}
{ref:2310.20275}, energy and decision-oriented variants {ref:2504.04916} {ref:2504.19507}, remote
estimation and routing {ref:2510.22288} {ref:2512.00985}, learned freshness policies
{ref:2512.11990} {ref:2607.27626}. **Difference.** These optimise a freshness policy or refine the
metric. We take the sampling interval as *the* knob, make its price explicit, and ask for the
marginal cost of freshness -- the curve a policy is implicitly trading against.

### 2.7 Knob tuning and configuration search

The systems community's version of the same knob is configuration tuning: OtterTune
{ref:10.1145/3035918.3064029}, Optuna {ref:10.1145/3292500.3330701}, the Bayesian-optimisation
review {ref:10.1109/jproc.2015.2494218} and its practical recipe {ref:1206.2944}, the Gaussian-process
and GP-UCB machinery {ref:10.7551/mitpress/3206.001.0001} {ref:0912.3995}, the online-convex and
bandit analyses beneath sequential search {ref:10.1561/9781680831719} {ref:10.1561/9781601986276}
{ref:10.1023/a:1013689704352} {ref:cs/0408007} and their non-stationary {ref:2506.02980},
sampling-limited {ref:2507.10797} and reward-learning {ref:2302.12349} extensions; then the DBMS and
cloud tuners {ref:2203.05128} {ref:2203.14473} {ref:2404.06043} {ref:2406.00616} {ref:2406.15073}
{ref:2504.11756}, the noisy/unstable-systems tuner {ref:2503.01801}, an SLO-constrained autotuner
{ref:2604.17627}, bandit-driven precision autotuning {ref:2601.00728} and earlier ensemble and
model-driven tuners {ref:1901.06228} {ref:2004.03695}. **Difference.** All of these return a good
point, or a regret rate for finding one. None returns the objective's derivative, and none states the
regimes in which the objective carries no information -- which is Section 6's object and is what an
operator needs before trusting a tuner's recommendation.

### 2.8 Control-side context

Finally, the control machinery our system 1 is built from and bounded by: constrained model
predictive control {ref:10.1016/s0005-1098(99)00214-9}, Kalman's optimal-control contributions
{ref:10.1109/9780470544334.ch8}, the dynamic-programming formulation {ref:10.1142/9789819808250_0007},
planning under partial observability {ref:10.1016/s0004-3702(98)00023-x}, the online-LQR instance
warning {ref:2510.19531}, regret-optimal and quantised LQR {ref:2604.06158} {ref:2604.11930} and a
learned Riccati operator {ref:2604.18507}. **Difference.** These optimise or stabilise a controller.
Our system 1 uses their plant and cost machinery only as the *ground truth* against which the
identification route is measured.

## 3. The instrument: two priced systems

**Ground truth is exact by construction on both systems.** Every number below is either a closed form
or an exact-integer/exact-float evaluation of one. Sampling enters exactly twice, and both entries are
declared and bounded: the **noise ladder's draws**, and a **Monte-Carlo certificate** of the
instrument against itself. That certificate's job is narrower than "the closed forms describe the
simulated system", so here is what it does and does not establish.

*It certifies the **variance law**, which is its strong claim.* The simulated variance matches the
analytic `sigma^2 * varcoef` to a ratio of **0.99929 ± 0.00074** at `k=10` and
**0.99927 ± 0.00072** at `k=20` — within **0.07%** in every cell tested.

*It checks the **bias term**, and reports it with its resolution.* The bias is measured in four
`(k, sigma)` cells at **five independent seeds**, because one seed cannot tell agreement from luck.
Each figure carries its standard error: `0.4342 ± 0.0020` (`k=10, sigma=1e-3`),
`0.4467 ± 0.0767` (`k=10, sigma=1e-2`), `1.2119 ± 0.0010` (`k=20, sigma=1e-3`) and
`1.2186 ± 0.0146` (`k=20, sigma=1e-2`), against closed-form values `0.4332`, `0.4332`, `1.2112` and
`1.2112`. Every cell resolves the bias (the smallest margin is `5.8` standard errors) and every cell
agrees with the closed form; the seed-to-seed spread of the variance ratio is `0.00074`. An `sd`
estimated from five seeds is itself uncertain by about `35%`, so the bars are quoted for a reader to
inflate rather than treated as exact — the verdicts clear that inflation with room to spare.

*What it does not certify.* Nothing about a deployed system: it is the instrument checked against
itself, not evidence about a real log. Two error bars are deliberately kept apart, because
confusing them changes the answer: the **error bar of the mean** over the 6,194 evaluated points
(the one the certificate's figures carry, `0.0020` in the first cell) and the **sampling error of a
single point estimate** (`0.168` in the same cell, `sqrt(analytic_var)/sqrt(n_rep)`). The second is
the natural yardstick for "could a deployment resolve this bias from this much data" — a real
question, and a different one: it is not an error bar on the certificate, whose claim is about a mean
over the grid.

### 3.1 System 1 -- a chunked-policy execution horizon

An LQR plant `x_{t+1} = A x_t + B u_t + w_t` with `w_t` of covariance `W`, a control law `u_t = -K
x_{t-d_t}` executed with delay `d_t`, and the periodic chunk schedule `d_t = tau + (t mod L) + 1`. The
per-delay cost `c(d)` is `trace(P_d[0:n,0:n])` with `P_d` the augmented Lyapunov solution of `(A,B,K)`
driven by `W` -- finite to the plant's delay margin `dmax`, `+inf` past it. `C(L)` is the chunk average
and `J(L) = C(L) + lam/L` the priced objective. Four plants (`scalar-stable a=0.9`, `double-int R =
1/10/100`), five latencies, 22 prices on a `1e-2..1e5` ladder give 352 cells (84 interior / 149 floor /
119 ceiling). This is the system our own [#116] publishes the boundary law for.

### 3.2 System 2 -- an age-of-information sampler

An Ornstein-Uhlenbeck source of stationary variance `s2` and rate `theta`; a telemetry pipeline serves
the last sampled value, so a consumer reads a value of **age** `s`; the operator picks the sampling
interval `L`, pays a price `lam` per sample, and pays the **staleness cost**
`c(s) = E[(X_t - X_{t-s})^2] = 2 s2 (1 - e^{-theta s})`. With periodic sampling the age is uniform on
`[0, L)`, so `C(L) = (1/L) int_0^L c` in closed form and `J(L) = C(L) + lam/L`. The floor is a
hardware-minimum interval, the ceiling a staleness tolerance -- a different boundary mechanism from a
stability margin, and `c(s)` saturates, so the ceiling is not a divergence. Three sources
`(theta, s2) in {(1,1), (3,1), (0.5,2)}`, 40 prices, give 120 cells (26 interior / 34 floor / 60
ceiling).

### 3.3 The two routes the paper is not

For P4 the paper measures what a practitioner would try instead of a sweep:

- **Higher moments** of the tracking error. Two model-free readings are defined: the **level** reading
  `J - lam/L*` (the logged mean cost) and the **profile** reading, the within-chunk phase slope
  `(p(L*) - p(1))/(L* - 1)` over the periodic loop's per-phase means.
- **Residual-dynamics system identification.** Read the raw log `(x_t, u_t, d_t)`, fit
  `x_{t+1} = A x_t + B u_t + w_t` by ordinary least squares, recover the control law `u_t = -K x_{t-d}`
  and `W = Cov(w)`, then reconstruct `c` through the truth's **own** closed form (no cost weight appears
  in it; a certificate inspects the reconstruction function's free names).

## 4. P1: the noise-free error is a quadrature error

**Claim (registered).** The noise-free error is a **quadrature error** -- the span average -- not a
modelling error.

**Measurement.** The identity `G = L* J - lam = int_0^{L*} c` is tested against the exact quadrature of
the plant's own curve, not against a fit: median relative error `8.6e-16` on system 1 (n=352, worst
`7.1e-7`) and `5.6e-17` on system 2 (n=120, worst `5.9e-16`). The sweep is then scored against two
targets on the same cells: the **span mean** of `c` (its correct target) and the **point value** `c(L*)`.
The sweep's error is `4.5e-9` median against the span mean and `1.39e-2` median against the point on
system 1; `2.5e-16` and `1.23e-2` on system 2. **The error is the span average**, and the identity is
exact.

**Controls that fire.** Perturbing `lam` by 1% breaks the identity on both systems (system 2: median
`5.2e-3`, ~11 orders of magnitude above the exact case). A one-sided difference is biased on a linear
curve where the centred difference is exact -- established as a plant.

{{FIG:p1}}

**Verdict: CONFIRMED on both systems.** This is the paper's premise, and it is what makes the sweep's
error budget a *quadrature* budget rather than a modelling one.

## 5. P2: the interior MSE-optimal span and its law

**Claim (registered).** Under noise there is an **interior, MSE-optimal span**, scaling as
`sigma^{1/3}`.

**Measurement.** The estimator is the centred difference of `G` at half-width `a`, whose target is the
span mean. Its `bias^2 A[k]` and variance coefficient `B[k]` are computed **exactly** (no sampling) over
a band fixed across `k` -- a `k`-dependent window removes the large-`c` points preferentially and
corrupts the exponent, a defect the instrument caught and pins. The optimal span `h*(sigma)` is the
sub-lattice argmin of `MSE = A + sigma^2 B`, and the exponent is the log-log slope of `h*` against a
`sigma` ladder. **The law is derived, not fitted:** with `bias ~ a^b` and `var ~ sigma^2 a^{-2}`, the
minimum is `h* ~ sigma^{2/(2b+2)}`, and the prediction uses the run's **own** measured `b`.

Two arms per system: a **smooth** curve (C^inf, or C^1 for system 1's Catmull-Rom arm) and the
**delivered C0 representation** (system 1's shipped linear interpolation between integer delays; system
2's `c` sampled at a step `S` and linearly interpolated).

| system | arm | `b` | predicted | measured |
|---|---|---|---|---|
| 1 | model C0 (1.0-delay kinks) | 1.4224 | 0.41282 | **0.40753** |
| 1 | smooth (Catmull-Rom, C1) | 1.8593 | 0.34974 | 0.35168 |
| 1 | analytic (C^inf) | 2.0058 | 0.33269 | 0.33404 |
| 2 | grid C0 (`S=1.0`) | 1.4233 | 0.41273 | **0.40619** |
| 2 | smooth (analytic, C^inf) | 1.9572 | 0.33824 | **0.33381** |
| 2 | grid C0 (`S=1.0`, `theta=0.5`) | 1.4276 | 0.41191 | 0.40621 |

{{FIG:p2}}

**Verdict: CONFIRMED in the smooth limit on two independent systems; REFUTED as stated on each
system's delivered C0 representation.** The smooth-limit exponents agree across the two systems to
`0.0002` (`0.33381` vs `0.33404`), and the C0 arms' bias exponents agree to `0.001` (`1.4233` vs
`1.4224`) because both use the **same kink spacing** (`1.0`). A **mechanism sweep** moves `b`: `S=0.5 ->
1.5176`, `S=1.0 -> 1.4233`, `S=2.0 -> 1.4208` (`theta=0.5` the same ordering). So the delivered
representation is `sigma^{0.41}`, not `sigma^{1/3}`, and the exponent is the **representation's
smoothness** plus the route's differencing -- not the plant. The predicted exponent from the same run's
measured `b` matches the measured slope to `<= 0.007` on every arm: the exponent is derived, not
fitted. (The mechanism's *direction* was measured, not assumed: a denser kink set moves `b` toward the
smooth value, and the deployment-relevant spacings `S >= 1.0` -- where the span rarely contains a kink --
plateau at `b ~ 1.42`.)

## 6. P3: the identifiability boundary

**Claim (registered).** The identifiable set is **exactly the argmax set**, predictable from the pricing
alone.

**The predictor.** A cell is **pinned** when the optimal `L*` sits within one lattice step of the
declared floor or ceiling, and **interior** otherwise. The rule reads no ground truth (certified by a
plant: shifting the declared floor flips labels while every error stays bitwise identical).

**Measurement.** Over 330 cells the predictor is **sound** (0 false positives at the paper's `1e-2`
resolution; worst predicted-interior error `7.4e-3`) but **not exact**: 9 disagreements, **5 of 246
threshold-free** (at the interior class's own worst error). The failures are **conservative** and have a
mechanism: **pinning is decided by the price's weight, the error by the first-order-condition residual
`C + lam/L - c` -- not the same function of `lam`**. The *fraction* is exact: the predicted pinned
*fraction* equals the measured one in **15/15 blocks** (11-21 of 22 prices). And the set is
**route-specific**: the sweep reading is not separated by the label (interior `1.42e-2` vs pinned
`1.50e-2`), because the sweep's error is a span artifact (P1), not a pinning artifact.

**Cross-system.** On system 2 the same structure reproduces. The **single-point marginal identity**
`c(L*) = J` holds at interior optima to the grid's own first-order-condition resolution and **shrinks
with the grid** (system 2, `theta=1`: median `8.17e-3 -> 9.04e-4` at a `4x` finer `deltaL`), while pinned
cells miss it by `~60x` (`0.315` median). On system 1 the same separation is `3.74e-4` interior vs
`0.2557` pinned (worst `1543`).

{{FIG:p3}}

**Verdict: separation CONFIRMED; the predictor is built and SOUND but criterion (iii) is UNMET as
written (9 disagreements, 5 threshold-free), with its mechanism stated.** Reported as measured, not
rounded to a pass.

## 7. P4: the two practitioner routes, and what is actually different

**Claim (registered).** The two routes a practitioner would try instead of a sweep -- higher moments of
the tracking error, and residual-dynamics system identification -- address a **different object** and
fail on the same logs.

**The moments route has two readings, and they disagree.** The **level** reading (the logged mean cost
`J - lam/L*`) is the **same object**: it tracks `c` at `r = +0.990` (median relative error `0.0953` all
cells, `0.1460` interior), **refuting the registered price-invariance**, because the envelope identity
makes it `c - lam/L*` at an interior optimum -- the same curve, ~10x less accurate than the sweep. The
**profile** reading (the within-chunk phase slope) is a **genuinely different object**: it
**anti-tracks** `c` (`r = -0.926`) and carries the **wrong sign on 303 of 303 cells** (80/80 interior),
a **threshold-free direction failure** (median error `1.0007`), because the periodic orbit is
re-planned at each chunk boundary (a U-shaped profile `31.79 -> 28.91 -> 30.19` against a monotonically
rising `c` `22.74 -> 78.64`). A **structural certificate** shows why: every logged quantity is a
function of the **visited point alone** (within a group sharing `(plant, tau, L*)` the price spans
`9.995e4` while `G` varies by `1.6e-13` relative), so the sweep is the only route that differences
*across* operating points.

**The system-identification route reaches the same object.** Reconstructing `c(d)` from the identified
`(A, B, K, W)` through the truth's own closed form tracks the true curve at `r = 0.9993...0.99999` over
four plants, with a median `c`-error of `1.3-7.5%` at a `1e5`-step log (error `~ T^{-0.26...-0.59}`, a
data floor, not a bias wall). **"Needs excitation a live deployment does not produce" is also refuted**:
the deployment's own disturbance suffices (`cond` 10-430), and only a *silent* (`W=0`) log breaks it.
`K` is recovered to `1e-15` on every closed-loop log. On system 2 the same conclusion holds (`theta` to
`<= 2.2%`, `c(s)` to `<= 1.1%`).

{{FIG:p4}}

**Verdict: REFUTED, twice, and the claim is ROUTE-SPECIFIC.** The moments route has one reading that is
the same object and one that is genuinely different; the system-identification route reaches the same
object. What separates the routes is **access and resolution, not a second object**: the sweep reads a
scalar-cost log and differences it across prices; system identification needs a raw
`(state, action, delay)` log carrying the control law that actually ran (a *free* action vector leaves
`K` unidentified, error `1.04`). Criterion (iv) -- the sweep `>= 10x` better at the median -- is met
against the profile reading (`68x`) and **met on interior cells against the level reading (`10.3x`) but
missed on all cells (`9.7x`)**, reported as measured.

## 8. Registered prior beliefs: what the measurement decided

The registration states four falsifiable priors. Each is reported against its registered criteria.

| prior | registered expectation | measured | verdict |
|---|---|---|---|
| **P1** | the noise-free error is a quadrature (span) error | `G = int c` to `8.6e-16` / `5.6e-17`; sweep error `4.5e-9` / `2.5e-16` vs span mean, `1.39e-2` / `1.23e-2` vs point | **CONFIRMED** (both systems) |
| **P2** | interior MSE-optimal span, `sigma^{1/3}` | smooth limit `0.334` on both systems (agree to `0.0002`); delivered C0 `0.408` / `0.406`; derived from the measured `b` | **CONFIRMED** in the smooth limit; **REFUTED** as stated on the C0 representation |
| **P3** | identifiable set is exactly the argmax set, from pricing alone | predictable and **sound** (0 FP at `1e-2`) but **not exact** (9 disagreements, 5/246 threshold-free); pinned fraction exact in 15/15 blocks | **PARTIALLY CONFIRMED** -- criterion (iii) **UNMET** with its mechanism |
| **P4** | the two routes address a **different object** | moments level: **same object** (`r=+0.990`, invariance clause refuted); moments profile: different (`r=-0.926`, wrong sign 303/303); system ID: **same object** (`r=0.9993...`) | **REFUTED**; the real separator is **access** |

The two **refutations are the paper's strongest novelty signal**, and both are theory-anchored: the
moment's price-invariance followed from the registration's own envelope identity (so P4's clause was
falsifiable in advance and was falsified), and the `sigma^{1/3}` law was derived from the measured bias
exponent (so its failure on the C0 representation is a statement about the representation, not a
failure of the derivation).

## 9. Threats to validity

- **Both systems are in-silico.** The ground truth is exact by construction, which is the measurement's
  strength, but no external deployment arm is claimed. The planned arm on published robot-policy logs
  (Open X-Embodiment / RoboMimic) is **`NOT RUN`**: those logs do not supply the priced triple
  `(L*, J, lam)` -- they carry trajectories, not a price the deployment pays -- so the arm cannot be
  built from them without inventing the price, which would make it a second in-silico system wearing a
  dataset's name. State that plainly rather than run it badly.
- **The span law's exponent is representation-dependent.** P2 is `sigma^{1/3}` for a smooth curve and
  `sigma^{0.41}` for a C0 one. A deployment's `c(.)` is delivered by a table, so the C0 value is the
  operational one; the smooth limit is the limit, not the answer.
- **The identifiability predictor is not exact.** It is sound (no false positives) but misses 9 cells,
  5 threshold-free, all conservative. A user of the rule is told "interior" for a cell whose error
  exceeds the interior class's typical error; the miss is toward *using* a cell, not toward discarding
  one, which is the safer direction but not the exact set the registration asked for.
- **The variance model is multiplicative.** The noise ladder models a logged `J` as `J (1 + sigma e)`,
  which is the deployment-logging model (a price and a cost are positive and scale-free). An additive
  noise model would change the variance coefficient `B[k]` but not the bias exponent, hence not the
  span law's exponent -- only its constant.
- **Why it is still worth publishing.** The two refutations are not negative results about a method;
  they are the paper's content. A practitioner's default instrument (moments) turns out to sample the
  same object badly, and their second default (system identification) turns out to need a log they do
  not keep -- and both facts are *measured*, cross-system, against exact ground truth. That sharpens
  the recommendation rather than weakening it.

## 10. Conclusion

The knob is not the curve. The value an operator sets is chosen by a marginal cost they do not measure,
and this paper shows that the marginal cost is identifiable from a price sweep the operator can run,
with an error budget and an identifiability boundary, on two mechanically different priced systems.
Three of the four registered claims survive in a form the measurement had to sharpen: the noise-free
error is a quadrature error (P1), the span law's exponent is the *representation's* rather than the
plant's (P2), and the identifiability boundary is predicted from the pricing alone and is sound but not
exact (P3). The fourth is refuted, twice, and the refutation is the paper's strongest result: the two
routes a practitioner would reach for instead are not a second object -- they are the same object
behind a worse access path (P4). The decision the paper changes is quotidian and it is directional: run
the sweep, and check first whether you are pinned.

## References

{{REFERENCES}}
