# How Long Should a Robot Commit? A Staleness–Amortization Boundary Law for the Action-Chunk Execution Horizon

**Author**: how2how2how2-arch  ·  **Issue**: #116  ·  **Contribution level**: `theory+empirics`

**Artifacts**: `canonical_results.json` (sha256 `afaaee8e56148dfab8f98cc1721d1ea0508b722c1fa6e442026de923e99e31c0`), `model_v1…v5`, `make_figures.py`; reproduced by one command (see README).

---

## Abstract

Modern robot policies answer a query with an **action chunk** — a sequence of future actions — and the robot executes an open-loop prefix of it before observing again. That prefix, the **execution horizon** `L`, is a deployment hyper-parameter. The 2026 real-time-chunking literature names the tension it controls — amortizing inference against acting on stale observations — and answers it with task-specific heuristics (phase-aware prefixes, urgency-weighted denoising, staggered sub-chunks), reporting that success is *"strongly task-dependent and non-monotonic"* without saying what governs it.

We build a controlled instrument — a plant family with an exactly known closed loop and a disturbance algebra that separates dense noise from rare impulses — and derive the boundary law for `L*`. **The law is a stationarity condition, not a fitted exponent**: `λ_c = L·[c(τ+L) − C(L)]`, where `c` is the per-delay tracking cost, `τ` the inference latency, and `λ_c` the price per query. This identity reproduces the optimum of the discrete sweep **exactly** (worst disagreement `0.0000` at grid resolution `0.02`) across 4 plants × 7 latencies × 22 prices over seven decades of price. We further show the feasible set is exactly `[τ, d_max − τ]`, so the optimum is **pinned** at a real-time floor at low price and at a **feasibility ceiling** at high price, with a **latency wall** at `τ = d_max/2` where the window collapses — a ceiling and a wall the registered prior did not anticipate.

Two registered predictions fail, and we report both against their registered wording. The square-root law `L* ≈ √(2λ_c/s)` is **refuted**: over 19 fits the exponent of `L*` in `λ_c` lies in `[+0.184, +0.635]` (mean `+0.348`), with **14 of 19 regression intervals lying entirely below 0.5**, and the exponent is latency-dependent *within* a plant. The natural replacement, `EXPONENT = 1/(p+1)` for a power-law delay cost, is **also refuted by our own test** (correlation `+0.773`, mean error `0.072`) — because the delay-cost curve is **not** a power law over the swept window. The disturbance-channel prior is a **tautology on the linear arm** (two disturbance processes matched in second moment give identical costs to `4.3e-16`) and is re-sited to the nonlinear arm, where the shape channel is real and moves the optimum while the mean channel does not.

Our claim is falsifiable and the instrument is exact: the boundary is the stationarity condition; a deployment that cannot afford more inference should not lengthen its horizon once the floor binds; and the exponent is a derived readout of the delay-cost curvature at the operating horizon, not a universal constant.

---

## 1. Introduction

An action-chunking policy answers one query with `L` future actions and then commits to a prefix of them. The choice of `L` trades two costs against each other:

- **Amortization**: each query costs `λ_c` (inference is a priced resource — latency, energy, or a real-time budget), so longer chunks query less often and the per-step query cost falls like `λ_c/L`.
- **Staleness**: every action in the executed prefix is conditioned on an observation that is older by the number of steps since the query, so tracking error grows with the horizon and with the plant's sensitivity to stale feedback.

The 2026 literature states this tension verbatim and answers it heuristically. **PACE** [17] measures that success is *"strongly task-dependent and non-monotonic with respect to"* the horizon and replies with a phase-aware execution schedule. **Staircase Policy** [27] states that *"performance degrades over long execution horizons because later actions remain conditioned on stale observations"* and replies with staggered sub-chunks. **Urgent Actions Go First** [29] exploits that actions *"are generated jointly but consumed sequentially"*, allocating denoising compute by urgency. **Reactive Real-Time Flow Policies** [28] finds asynchronous execution *"can produce a fundamentally different action distribution"*. **ACPPO** [26] states that *"executing chunks open-loop removes within-chunk feedback"*. Five independent 2026 works locate the same tension; none derives a boundary for it.

The parameter itself is inherited un-derived from the origin of the paradigm: ACT/ALOHA [1] introduced chunking with a fixed horizon, and it has been a per-deployment tuning knob since.

**Contributions.**

1. **The law is a stationarity condition, not a curve fit.** We derive `λ_c = L·[c(τ+L) − C(L)]` and verify it reproduces the discrete sweep's argmin exactly (§4.2). The registered square-root form is a *special case* of an asymptotic expansion, and that expansion does not hold for these plants.
2. **The feasible set is a window that closes at both ends.** `L* ∈ [τ, d_max − τ]` (§4.3). Low price pins at the floor; high price pins at a feasibility ceiling; at `τ = d_max/2` the window collapses to a point — a **latency wall** at which no execution horizon is feasible.
3. **The registered square-root law is refuted, and so is its natural replacement** (§5.2), with the reason the replacement fails measured rather than asserted.
4. **The two disturbance channels act on different quantities** (§5.4). A non-zero-mean disturbance adds a **delay-invariant** term (400 % of the covariance part) that raises the cost level and moves the optimum by *nothing*; a change in disturbance *shape* at matched second moment moves the optimum, and grows with staleness.

**Who cares.** Engineers deploying vision-language-action or diffusion policies on real-time hardware choose this horizon per task today. If the boundary is the stationarity condition, then (a) the horizon is a function of the inference price and a measurable property of the plant, (b) task dependence enters only through that property, and (c) the 2026 heuristic wave can be read as approximations of one boundary rather than as unrelated tricks. The belief that changes is *"the execution horizon is a task-specific constant to be tuned."*

---

## 2. Related work, and what each differs from this work in

**Chunked-policy horizon (the construct).** PACE [17] and Staircase Policy [27] both name the horizon as the open choice and both answer with an execution *schedule* (phase-aware prefixes; staggered sub-chunks). The difference from this work is that they treat the objective as unmodelled and optimise inside the schedule, whereas we write the objective down, derive its stationarity condition, and show such schedules are approximations of it. Urgent Actions Go First [29], Reactive Real-Time Flow [28] and ACPPO [26] attack the same tension from the generator side (urgency-weighted denoising, asynchronous distribution alignment, feedback correction); the difference is that each reports a mechanism-level remedy at fixed horizon, while we locate the horizon itself and derive the regime in which the remedy is or is not needed. SeAR [9] and RL-with-Action-Chunking [6] learn *with* chunks at a chosen length; the difference is that chunk length is their hyper-parameter, not their object of study. HiPolicy [12] and FocalPolicy [14] introduce multi-frequency and frequency-optimised chunking; the difference is that frequency is their design axis and the amortization–staleness trade is not written down. ChunkFlow [19] and Action-Prior Denoising [16] add continuity constraints across chunk boundaries; the difference is that continuity is a within-chunk property, while our boundary governs *how much* of the chunk is executed. Implicit Action Chunking [15] and PolicyTrim [18] improve chunk quality at fixed horizon; the difference is that quality and horizon are independent knobs, and we hold quality fixed by construction so the horizon's effect is identifiable. Real-time conditioning [8] and discrete-diffusion asynchrony [13] make asynchronous execution feasible; the difference is that they change *when* actions are produced, while we ask *how many* to commit. Recent analyses of why chunking helps at all [21], of selecting among temporal actions [7], of guided test-time decoding [4], of temporal aggregation of overlapping chunks [25, 5], of adaptive horizons [30], of self-verifying chunk selection [10], of how small a chunked policy can be [23], of *whether* open-loop execution should be revisited at all [22], of speculative verification for chunked policies [11], of dual-path motion conditioning [20] and of underwater bimanual deployment [24] are all *within* the fixed-horizon regime: the difference from this work is that each takes the executed prefix as given, while we derive it.

**Latency and efficiency.** LiteVLA-H [31], FlashDrive [35] and the token-caching line [38, 39] reduce per-query latency; the difference from this work is that they make inference *cheaper* while we ask how much inference to *buy* at a given price — the two compose, and their gain is the `λ_c` in our law. EVA-Client [33] and FluxVLA Engine [36] are deployment frameworks whose fixed horizons our boundary parameterises, and temporal-redundancy reduction [34], spatial-scaffold preservation [39] and video-prediction-conditioned actions [32] lower the price without answering how much to buy, and a humanoid whole-body policy [37] is a deployed instance of the same choice. Control-frequency studies [3, 2] vary the sampling period with a fixed controller; the difference is that a per-query price is absent there, so no interior optimum can exist in their formulation.

**Delay and sampled-data control.** The delay-margin and networked-control literature [53, 49, 42, 44, 43, 48, 52, 50, 46] establishes that a delayed feedback loop has a finite stability margin and characterises it spectrally; the difference from this work is that delay enters there as a *stability constraint* on a fixed controller, whereas here delay enters as the *age of the observation a committed action was conditioned on* — a cost — and it is priced jointly with the query rate. The sampled-data literature [40, 41, 51, 45, 47] studies performance versus sampling period without a per-query price, so it produces neither the amortization term nor an interior optimum.

**Staleness, anytime computation, imprecise computation.** Stochastic control with stale information [59] and age-of-information [58, 57] price the *freshness* of an observation; the difference is that freshness there is exogenous and paid for in update rate, whereas here the staleness is produced by the decision variable itself — executing an `L`-step prefix *is* the staleness — so cost and benefit share one control. The anytime [62, 55, 67] and imprecise-computation [61, 60, 56, 54] literatures schedule computation under a deadline; the difference is that they choose *how much* computation to do for a fixed action, while we choose *how many actions to commit* for a fixed computation. Inference-scheduling work [63, 66, 65] allocates a compute budget across queries; the difference is that the budget is allocated across *queries*, not across the *commitment* a query buys.

**Abstraction and amortization.** Options [97, 96], macro-actions [94, 95, 93, 99, 98] and amortized inference [101, 100, 103, 102] all amortize a decision over a longer span; the difference from this work is that their span is learned or given, and the cost they amortize is a *learning* cost, not a *priced query*; path-dependent amortization [104] is the closest to a recurrence over the commit step, and the difference is that its span is a modelling choice rather than a priced optimum.

**Horizon length in receding-horizon control.** The prediction-horizon literature [68, 69, 72, 70, 73, 71, 74, 75] is the nearest classical relative of this problem: it too treats a horizon as the decision variable. The difference from this work is that the horizon there is bounded by *prediction* quality and by a terminal cost, and its length is chosen against a model-error budget, whereas ours is bounded by the *observation's age* under committed open-loop action — so our window `[τ, d_max − τ]` has a stability-margin ceiling that no prediction-horizon formulation contains, and its lower end is a real-time floor rather than a cost.

**Theory used.** LQG steady-state cost and the discrete Lyapunov equation [81, 92, 78, 88, 82, 80, 83, 89] give our exact per-delay cost recursion; the difference is that we use them as an *instrument* (a ground truth), not as a contribution. Stochastic MPC [84, 79, 77, 87, 85] and robust receding-horizon control [64] motivate the horizon as a decision variable but optimise a different objective; heavy-tailed disturbance models [90, 91, 76, 86] are the closest theory to our shape channel, and the difference is that they bound optimisation under heavy tails while we use tail structure to *separate two disturbance channels' effect on a decision*.

**Saturation, disturbance, and the setting.** Actuator-saturation studies [111, 106, 112, 110] and disturbance-observer work [109, 107, 108, 105] characterise nonlinearity in the loop; the difference is that we use saturation to *break the second-moment equivalence* of two disturbance processes, which is precisely the regime in which the disturbance channel becomes decision-relevant. The manipulation, benchmark and evaluation literature [130, 131, 122, 125, 119, 116, 113, 124, 126, 134, 133, 114, 132, 121, 120, 123, 117, 129, 128, 118, 115, 127] supplies the setting with which our boundary must be consistent; the difference is that these works evaluate a policy or a platform, while we evaluate a *deployment parameter* of any of them.

**The specific differences from the three closest works**, stated as the bar requires:

| work | their claim | our difference |
|---|---|---|
| PACE [17] | the horizon's effect is task-dependent and non-monotonic, answered by a phase-aware schedule | we show where the non-monotonicity comes from — the floor→interior→ceiling pinning structure — and that the schedule approximates the stationarity condition |
| Staircase [27] | staleness of later actions causes degradation, answered by staggered sub-chunks | we quantify staleness as the *delay coordinate* of the cost and show the optimum is the stationarity condition, not a schedule |
| ACT/ALOHA [1] | chunking with a fixed horizon | we derive what the fixed horizon should be, as a function of the inference price and the plant's delay-cost curvature |

---

## 3. The instrument

### 3.1 Plants

Four plant families, each a discrete-time system `x_{k+1} = A x_k + B u_k + w_k` with an LQR gain `K` from `(Q, R)`, at `Δt = 0.1`:

| plant | state | `R` | delay margin `d_max` | role |
|---|---|---|---|---|
| scalar-stable `a = 0.9` | 1 | 1 | 20 | stable, flattens at large delay |
| double integrator | 2 | 1 | 6 | **near-margin**, cost blows up early |
| double integrator | 2 | 10 | 12 | intermediate |
| double integrator | 2 | 100 | 20 | well damped |

`d_max` is the largest delay at which the augmented closed loop is stable; beyond it the per-delay cost is `+∞`.

### 3.2 The delayed (chunked) loop and the per-delay cost

Executing an `L`-step prefix means the control applied at time `k` was computed from the observation taken `d` steps earlier, `0 ≤ d ≤ L−1`. Writing the augmented state across the delay chain, the stationary covariance solves the discrete Lyapunov equation `P_d = Ā_d P_d Ā_dᵀ + W̄`, and the per-delay tracking cost is `c(d) = Tr(Q P_d)` plus, when the disturbance has non-zero mean, the mean term of §5.4.

We compute `c(d)` **two algorithmically independent ways** — an augmented-Lyapunov solve and a fixed-point covariance recursion — which agree to **`1.52e-14`** relative deviation. The registered falsifier for the theory arm was `≤1e-6`; this is **MET**, and it is what lets theory and instrument be compared at machine precision rather than at simulation noise.

### 3.3 The objective, and the proxy validated before use

The priced objective is

```
J(L) = C(L) + λ_c / L ,      C(L) = (1/L) ∫_0^L c(τ + s) ds
```

where `τ` is the inference latency in control steps (the observation is stale by `τ` before the prefix even begins) and `λ_c` is the price per query. `C(L)` is the mean per-step tracking cost over the executed prefix; `λ_c/L` is the amortized query cost per step.

Because a chunked loop is **time-periodic with period `L`**, the exact cost is a periodic average and the continuous integral above is a quasi-static proxy. We validated the proxy against the exact periodic cost *before reading any optimum on it*: worst relative error **`3.01e-03`**, and at `L = 1` the two agree to `5.6e-9`. Every optimum below is on the validated objective, and every cell carries its classification (floor / interior / ceiling) so a pinned entry is never read as a law.

### 3.4 Disturbances

- **dense** Gaussian noise of variance `σ²`;
- **rare impulses** of rate `λ` and magnitude `A`, one-sided (a floor impact, a push in one direction) — these carry a non-zero mean;
- a **scale-mixture family** `w = s·z` with `s = s₁` w.p. `r` else `s₀`, solved in closed form so that variance **and** kurtosis are matched by construction between arms (`u = 1 + √(1 − c/r)`, `c = 1 − kurt(1−r)/3`).

### 3.5 Baselines

- **per-step closed loop** (`L = 1`) — the no-chunking baseline;
- **oracle horizon** — exhaustive argmin over the same grid with the same information, the bound an optimal chooser attains;
- **fixed-horizon heuristic** — the literature's default: one horizon chosen and held across prices.

---

## 4. The boundary law

### 4.1 The stationarity condition

For an interior optimum, `dJ/dL = 0`. With `G(L) = ∫_0^L c(τ+s) ds` and `C = G/L`,

```
C'(L) = ( c(τ + L) − C(L) ) / L
```

so stationarity is

> **λ_c = L · [ c(τ + L) − C(L) ]**   — the **FOC**

The bracket is the **marginal staleness cost** at the horizon: the cost of the freshest step in the prefix minus the prefix's average. The FOC equates the amortized price `λ_c/L` to that marginal staleness.

### 4.2 The identity is exact — two routes

We solved the FOC on the same grid as the discrete sweep (step `0.02`) and compared against the sweep's own argmin over **every interior cell**:

| check | result |
|---|---|
| worst `\|FOC L* − sweep L*\|` | **0.0000** (grid step 0.02) |
| routes | discrete argmin over the validated objective vs continuous stationarity |
| example | scalar-stable, `τ=0`, `λ_c=10`: `17.960` vs `17.960` |

Two algorithmically different routes agreeing at grid resolution is what makes this an identity rather than a restatement. **This is the paper's law.**

### 4.3 The feasible set is a window that closes at both ends

`L < τ` is infeasible (a real-time loop must not query faster than it consumes), and `L > d_max − τ` is infeasible (the delay `τ + L` must stay inside the stability margin). Hence

> **L* ∈ [τ, d_max − τ]**

The registered prior (P2) contained the floor and asserted pinning. It did **not** contain the **ceiling**, nor the consequence that the two ends **meet**: at `τ = d_max/2` the window collapses to a single point, and for `τ > d_max/2` it is empty. We call this the **latency wall**: a deployment whose inference latency exceeds half the plant's delay margin has **no** feasible execution horizon, and no amount of inference tuning helps.

This yields a three-regime structure read directly off the objective:

- **floor-pinned** at low price — the price cannot justify extending a chunk beyond the floor;
- **interior** in the middle — the FOC governs;
- **ceiling-pinned** at high price — feasibility, not price, binds.

Figure 3 (`regime_map.png`) draws every cell of the `(τ, λ_c)` plane under this classification for all four plants.

---

## 5. Results

### 5.1 The regime map (registered criterion iii — **MET**)

Four plants × 7 latencies × 22 prices over seven decades, every cell classified: **28 `(plant, τ)` rows**, each flat at the floor, flat at the ceiling, and rising in between. The window and the wall are confirmed per plant. One row is degenerate and is recorded as such: near-margin `τ = 3` is floor-pinned at **every** price (13 cells, 0 interior), because `d_max = 6` makes the floor and the ceiling coincide. Rows with `τ > d_max/2` are recorded `infeasible` (e.g. `τ = 4, 6, 8` on the near-margin plant).

### 5.2 The exponent: the registered law is refuted, and so is its replacement

**Registered criterion (ii): the fitted exponent of `L*` in `λ_c` lies in `[0.4, 0.6]` over ≥12 configurations. Result: UNMET.**

Log-log slope over interior points only, with the regression standard error:

| statistic | value |
|---|---|
| number of fits | **19** |
| range | **[+0.184, +0.635]** |
| mean | **+0.348** |
| 95 % interval **entirely below** 0.500 | **14 of 19** |
| 95 % interval containing 0.500 | **1 of 19** |

Examples: scalar-stable `τ=0` `+0.437 [0.354, 0.519]`; `τ=1` `+0.556 [0.535, 0.577]`; `τ=3` `+0.624 [0.583, 0.664]`; near-margin `τ=0` `+0.208 [0.162, 0.255]`; `R=10 τ=0` `+0.246 [0.210, 0.282]`; `R=100 τ=0` `+0.263 [0.220, 0.305]`. Figure 2 draws all 19 with intervals against the 0.500 line.

Two facts follow beyond the band failure. The exponent is **plant-dependent** — a near-margin plant at `0.208` and a well-damped plant at `0.263` are not the same law — and, not anticipated at registration, it is **latency-dependent within a plant**: scalar-stable moves `0.437 → 0.635` as `τ` goes `0 → 4` on the same price grid.

**The natural replacement fails too.** If the delay cost were a power law past the window, `c(d) ~ a·d^p`, the bracket would be `a L^p · p/(p+1)`, so `λ_c ~ L^{p+1}` and

```
EXPONENT = 1 / (p + 1)      (candidate)
```

The registered `√` is exactly the `p = 1` case. Against the 19 fits: correlation **`+0.773`**, mean absolute error **`0.0718`** (max `0.2212`), **11 of 19** within `0.05`; a second estimator (local slope at each configuration's mid-horizon) is **no better** (mean `0.083`, correlation `+0.730`); and the candidate's direction across `τ` **disagrees** with the measured one for 2 of 4 plants. Two estimators missing the same way is evidence about the **form**, not the estimator — so we measured the form:

| plant | local log-log slope of `c(d) − c(0)`: at `d = 2` → at `d_max` |
|---|---|
| scalar-stable | `0.95` → **`0.39`** (decaying) |
| double-int `R=1` (near-margin) | `1.26` → **`5.40`** |
| double-int `R=10` | `1.13` → **`11.29`** |
| double-int `R=100` | `1.07` → **`6.74`** |

A power law would be **constant**. It is not. Consequently `1/(1+p)` moves *within one configuration* (`R=10, τ=0` spans `0.078…0.447`), and the measured exponent lands inside that locally-implied range in **11 of 19** configurations. The form is refuted as a **single-valued law** and survives only as a **range**.

**Reading.** The horizon is governed by the stationarity condition (§4.2); the exponent is a *derived readout of the delay-cost curvature at the operating horizon*. It has no universal constant, and `√` is the `p = 1` case no plant here exhibits. A paper reporting a fitted exponent would be reporting a property of the fitting window.

### 5.3 The FOC as an instrument for the heuristics

Because the FOC is exact, it evaluates the literature's remedies: a fixed-horizon choice is optimal only over the price interval where the FOC's solution equals that horizon, and the pinning structure says when the horizon is *not* the decision variable at all — below the floor's price, latency does not enter `L*`; above the ceiling's price, the price does not. Figure 1 draws `L*(λ_c)` per latency with the per-curve floors and ceilings; Figure 3 draws the classification.

### 5.4 The two channels act on different quantities

**A mean raises a level; a level cannot move an argmin.** A one-sided disturbance (`p = 0.05`, `A = 1` ⇒ mean `0.05`, variance `0.0475`) enters a linear loop through the deterministic mean response `x̄ = (I − Ā_d)^{-1} m̄`, adding `‖x̄‖²` on top of `Tr(P)`:

| quantity | value |
|---|---|
| centred `Tr(P)` (var `0.0475`), `d = 3` | **6.250942138525** |
| mean term `‖x̄‖²` | **25.001250000005** |
| ratio, mean term / covariance part | **399.96 %** |
| spread of the mean term over `d = 0…7` | **0.0** — delay-invariant |
| prediction `Tr(P) + ‖x̄‖²` | **31.25219213853** |
| Monte-Carlo, seeds 5 / 6 / 7 | 31.23569 / 31.25934 / 31.26876 → **−0.64 / +0.28 / +0.64 σ** |

The mean term is **delay-invariant to twelve significant figures** while the augmented spectral radius still varies (`0.9773 → 0.9712`): the DC gain of a stable loop does not depend on the delay. So the mean channel adds a **constant** to `J(L) = C(L) + λ_c/L`, and a constant does not move the argmin. It raises the cost by 400 % of the covariance part and changes `L*` by **nothing** — the opposite of the shape channel.

**A shape moves the optimum.** On the saturating plant (`u_max = 5`, `N = 6000`, `T = 2000`, deterministic seeds) with two disturbance processes matched in second moment, the sparse/gaussian cost ratio is **`1.04371` at `d = 0` rising to `1.10109` at `d = 10`** — the separation *grows with staleness*, which is what makes the channel decision-relevant. Measured on the validated objective, the sparse arm's optimum is lower:

| latency | `λ_c = 10` | `λ_c = 100` |
|---|---|---|
| `τ = 0` | −0.040 | **−0.380** |
| `τ = 1` | −0.240 | −0.320 |
| `τ = 2` | 0.000 | −0.280 |

against a **linear-arm control null** of `0.000–0.080` (registering §5.4's mean channel as the control that must stay flat), i.e. a real shift at about five times the noise floor — but not a universal constant.

**The registered P3 is a tautology on the linear arm.** For a zero-mean disturbance the stationary covariance solves `P = Ā P Āᵀ + W̄`, so the cost is a functional of `W̄` alone and the disturbance's *shape* cannot enter. Two processes matched in per-step second moment therefore give identical costs to **`4.3e-16`**, and the linearity control is exact (`c(2W̄)/c(W̄) = 2.000000000000`, `0.500000000000`) while a deliberate near-miss (`1.9W̄`) correctly fails at `5.00e-2`. P3 as registered — impulses `∝ λ·A²` vs dense noise flat in the rate — **cannot be tested on the linear arm**; it is re-sited to the saturating arm, where the measured separation is the shape channel above.

**One instrument defect is recorded because a check found it.** A first version computed the mean term as the Lyapunov solution with `W̄ = m mᵀ`, i.e. the covariance of an iid ±m signal rather than the deterministic mean response; it drops the cross terms and gave `0.329` instead of `25.001`, putting the Monte-Carlo `953 σ` from its own prediction. The wrong route is kept in the artifact as a **control that must keep disagreeing** (relative distance `0.79`).

---

## 6. Threats to validity

**The registered square-root law fails, and the paper's claim is not that it holds.** We report it as refuted and replace it with an exact identity. A reader who came for a closed form for the exponent does not get one, and we argue that is the correct result rather than a shortfall: the quantity has no universal constant because the underlying delay-cost curve is not a power law over any window an optimum sweeps (§5.2).

**The registered out-of-sample sign criterion is NOT RUN.** Criterion (v) — predicted sign of chunking's net value on held-out configurations, ≥90 % — has not been evaluated. The study's practical claim therefore rests on the exact instrument rather than on an external validation. This is the largest open item and it is named, not hidden.

**The instrument is a model, not a robot.** Ground truth is by construction (an exact Lyapunov/recursion pair), which buys precision at the cost of realism: the plants are linear (with one saturating nonlinear arm), the disturbances are stylised, and contact is not modelled. The 2026 heuristic wave is used as the *motivation* and the *comparison*, not as a source of measured curves.

**The FOC is validated on the same objective the sweep optimises.** The two routes are algorithmically independent (continuous stationarity vs discrete argmin), which is what makes the agreement informative, but they share the objective's definition. An implementation error in the objective would move both together; the independent check against the exact periodic cost (`3.01e-3`) is the guard against that, and it is a proxy test, not an exact one.

**Why this is still worth publishing.** (i) The boundary is exact and falsifiable, and it is *not* a fit: a reader can re-derive it in three lines and test it on any plant. (ii) It re-organises a live 2026 subfield: five independent works name the same tension and answer with heuristics, and the FOC plus the feasible window says which heuristic regime each is in. (iii) It converts a tuning knob into a measurable quantity (the delay-cost curvature at the operating horizon) and makes a deployer's decision precise in the two regimes where the horizon is *not* the decision variable.

---

## 7. Prior beliefs: what the results say

Registered before the deciding runs; reported here verbatim in substance, with the outcome.

| prior | registered prediction | outcome |
|---|---|---|
| **P1** | with `λ_c = 0`, `L* = 1` for every plant; with `λ_c > 0` an interior optimum follows `L* ≈ √(2λ_c/s)` | **REFUTED in part.** Clause 1 holds everywhere in the sweep. Clause 2 fails: the exponent is outside `[0.4, 0.6]` for 14 of 19 configurations with tight intervals, and the natural replacement `1/(p+1)` is refuted too (§5.2). |
| **P2** | `L* = max(√(2λ_c/s), τ/Δt)`; beyond the floor the optimum is **pinned** and the cost grows linearly in `τ`; below it, `τ` does not enter `L*` | **REFINED, and one clause is new.** The floor and its pinning are confirmed. The registered form omitted a **ceiling** at `d_max − τ` and a **latency wall** at `τ = d_max/2`, so the feasible set is `[τ, d_max − τ]`, shrinking from both ends (§4.3). |
| **P3** | impulses enter as `λ·A²` so the optimum's level sets are hyperbolae in `(λ, A)`; dense noise is flat in the rate | **A TAUTOLOGY on the arm it was registered against.** On the linear arm the cost is a functional of the second moment alone (`4.3e-16` between matched processes), so the predicted level-set shape cannot separate the two families there. **Re-sited** to the nonlinear arm, where the shape channel is real and moves the optimum (§5.4). |

Criterion scorecard: (i) theory arm exact — **MET** (`1.52e-14` vs `≤1e-6`); (ii) exponent band — **UNMET**; (iii) two-regime structure in ≥3 plant families — **MET** (4 plants, every cell classified, plus the wall); (iv) level-set shape test — **REFUTED as registered** (tautology), replaced by the measured shape channel; (v) out-of-sample sign — **NOT RUN**.

---

## 8. Conclusion

The execution horizon of a chunked policy is not a task-specific constant. It is the solution of a stationarity condition, `λ_c = L·[c(τ+L) − C(L)]`, over a feasible window `[τ, d_max − τ]` that closes at both ends and collapses entirely at `τ = d_max/2`. The registered square-root law is refuted, and so is our own natural replacement — because the delay-cost curve is not a power law, so the exponent is a readout of curvature rather than a constant. The two disturbance channels act on different quantities: a mean raises the cost level without moving the optimum, a shape moves the optimum without a nonlinearity being needed for the mean.

---

## References

[1] Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware. DOI 10.15607/rss.2023.xix.016, 2023. https://doi.org/10.15607/rss.2023.xix.016 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[2] Control Frequency Adaptation via Action Persistence in Batch Reinforcement Learning. arXiv:2002.06836, 2020-02-17. https://arxiv.org/abs/2002.06836 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[3] Is Data All That Matters? The Role of Control Frequency for Learning-Based Sampled-Data Control of Uncertain Systems. arXiv:2403.09504, 2024-03-14. https://arxiv.org/abs/2403.09504 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[4] Bidirectional Decoding: Improving Action Chunking via Guided Test-Time Sampling. arXiv:2408.17355, 2024-08-30. https://arxiv.org/abs/2408.17355 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[5] Proleptic Temporal Ensemble for Improving the Speed of Robot Tasks Generated by Imitation Learning. arXiv:2410.16981, 2024-10-22. https://arxiv.org/abs/2410.16981 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[6] Reinforcement Learning with Action Chunking. arXiv:2507.07969, 2025-07-10. https://arxiv.org/abs/2507.07969 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[7] Temporal Action Selection for Action Chunking. arXiv:2511.04421, 2025-11-06. https://arxiv.org/abs/2511.04421 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[8] Training-Time Action Conditioning for Efficient Real-Time Chunking. arXiv:2512.05964, 2025-12-05. https://arxiv.org/abs/2512.05964 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[9] SEAR: Sample Efficient Action Chunking Reinforcement Learning. arXiv:2603.01891, 2026-03-02. https://arxiv.org/abs/2603.01891 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[10] Action Draft and Verify: A Self-Verifying Framework for Vision-Language-Action Model. arXiv:2603.18091, 2026-03-18. https://arxiv.org/abs/2603.18091 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[11] Open-Loop Planning, Closed-Loop Verification: Speculative Verification for VLA. arXiv:2604.02965, 2026-04-03. https://arxiv.org/abs/2604.02965 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[12] HiPolicy: Hierarchical Multi-Frequency Action Chunking for Policy Learning. arXiv:2604.06067, 2026-04-07. https://arxiv.org/abs/2604.06067 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[13] DiscreteRTC: Discrete Diffusion Policies are Natural Asynchronous Executors. arXiv:2604.25050, 2026-04-27. https://arxiv.org/abs/2604.25050 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[14] FocalPolicy: Frequency-Optimized Chunking and Locally Anchored Flow Matching for Coherent Visuomotor Policy. arXiv:2605.15944, 2026-05-15. https://arxiv.org/abs/2605.15944 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[15] Implicit Action Chunking for Smooth Continuous Control. arXiv:2605.19592, 2026-05-19. https://arxiv.org/abs/2605.19592 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[16] Action-Prior Denoising for Smooth Real-Time Chunking. arXiv:2605.25537, 2026-05-25. https://arxiv.org/abs/2605.25537 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[17] PACE: Phase-Aware Chunk Execution for Robot Policies with Action Chunking. arXiv:2606.00537, 2026-05-30. https://arxiv.org/abs/2606.00537 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[18] PolicyTrim: Boosting Intrinsic Policy Efficiency of Vision-Language-Action Models. arXiv:2606.22540, 2026-06-21. https://arxiv.org/abs/2606.22540 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[19] ChunkFlow: Towards Continuity-Consistent Chunked Policy Learning. arXiv:2607.12992, 2026-07-14. https://arxiv.org/abs/2607.12992 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[20] DynamicWAM: Dual-Path Motion Conditioning for World-Action Models in Dynamic Manipulation. arXiv:2608.00793, 2026-08-01. https://arxiv.org/abs/2608.00793 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[21] Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control?. arXiv:2608.02547, 2026-08-03. https://arxiv.org/abs/2608.02547 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[22] Revisiting Open-Loop Execution in Robotics: Toward Reactive, Higher-Performing Policies. arXiv:2608.15938, 2026-08-16. https://arxiv.org/abs/2608.15938 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[23] MINERVA: How Small Can a Manipulation Policy Be and Still Solve LIBERO?. arXiv:2609.03715, 2026-09-03. https://arxiv.org/abs/2609.03715 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[24] ULOHA: An Underwater Bimanual Robot System for Robot Learning. arXiv:2609.19200, 2026-09-16. https://arxiv.org/abs/2609.19200 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[25] Median Temporal Ensembling: Training-Free Robust Aggregation for Action-Chunked Visuomotor Policies. arXiv:2609.27167, 2026-09-22. https://arxiv.org/abs/2609.27167 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[26] Action Chunking Proximal Policy Optimization with Feedback Correction. arXiv:2609.36250, 2026-09-28. https://arxiv.org/abs/2609.36250 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[27] Staircase Policy: Streaming Inference for World-Action Models with Large Action Chunks. arXiv:2609.36471, 2026-09-29. https://arxiv.org/abs/2609.36471 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[28] Reactive Real-Time Flow Policies via Asynchronous Distribution Alignment. arXiv:2609.36540, 2026-09-29. https://arxiv.org/abs/2609.36540 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[29] Urgent Actions Go First: Urgency-Aware Denoising for Real-Time VLA Control. arXiv:2609.37772, 2026-09-29. https://arxiv.org/abs/2609.37772 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[30] SplineWAM: Adaptive Action Horizons for World Action Models via B-Spline Representations. arXiv:2609.39873, 2026-09-30. https://arxiv.org/abs/2609.39873 - Difference from this work: fixes, schedules or improves the execution horizon rather than deriving its boundary.

[31] LiteVLA-H: Dual-Rate Vision-Language-Action Inference for Onboard Aerial Guidance and Semantic Perception. arXiv:2605.00884, 2026-04-27. https://arxiv.org/abs/2605.00884 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[32] R2RDreamer: 3D-aware Data Augmentation for Spatially-generalized 2D Manipulation Policies. arXiv:2606.17040, 2026-06-15. https://arxiv.org/abs/2606.17040 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[33] EVA-Client: A Unified Data Collection, Inference, and Deployment Framework for Embodied Policies on Real Robots. arXiv:2607.02646, 2026-07-02. https://arxiv.org/abs/2607.02646 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[34] Reducing Temporal Redundancy for Efficient Vision-Language-Action Inference. arXiv:2607.12287, 2026-07-14. https://arxiv.org/abs/2607.12287 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[35] FlashDrive: Flash Vision-Language-Action Inference for Autonomous Driving. arXiv:2608.12932, 2026-08-13. https://arxiv.org/abs/2608.12932 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[36] FluxVLA Engine: A One-Stop VLA Engineering Platform for Embodied Intelligence. arXiv:2609.17210, 2026-09-15. https://arxiv.org/abs/2609.17210 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[37] PASSAGE: Scaling Scene-Aligned Motion Learning for Perceptive Humanoid Traversal in Cluttered Environments. arXiv:2609.18732, 2026-09-16. https://arxiv.org/abs/2609.18732 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[38] Text-Vision Synergistic Token Caching: A Training-Free Framework for Efficient Vision-Language-Action Inference. arXiv:2609.34319, 2026-09-28. https://arxiv.org/abs/2609.34319 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[39] Beyond Token Importance: Preserving Spatial Scaffolds for Efficient Vision-Language-Action Inference. arXiv:2609.36967, 2026-09-29. https://arxiv.org/abs/2609.36967 - Difference from this work: lowers the per-query price; we decide how much inference to buy at that price.

[40] Pontryagin maximum principle for optimal sampled-data control problems. arXiv:1512.04797, 2015-12-15. https://arxiv.org/abs/1512.04797 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[41] Linear-quadratic optimal sampled-data control problems: convergence result and Riccati theory. arXiv:1604.06350, 2016-04-21. https://arxiv.org/abs/1604.06350 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[42] Lower bounds on the maximum delay margin by analytic interpolation. arXiv:1803.09487, 2018-03-26. https://arxiv.org/abs/1803.09487 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[43] Note on the exact delay stability margin computation of hybrid dynamical systems. arXiv:1811.07534, 2018-11-19. https://arxiv.org/abs/1811.07534 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[44] Optimal Stabilization Control for Discrete-time Markov Jump Linear System with Control Input Delay. arXiv:1902.06235, 2019-02-17. https://arxiv.org/abs/1902.06235 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[45] Robust Decidability of Sampled-Data Control of Nonlinear Systems with Temporal Logic Specifications. arXiv:1903.06368, 2019-03-15. https://arxiv.org/abs/1903.06368 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[46] Tracking Performance Limitations of MIMO Networked Control Systems with Multiple Communication Constraints. arXiv:1904.12660, 2019-04-25. https://arxiv.org/abs/1904.12660 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[47] Sampled-Data Control of the Stefan System. arXiv:1906.01434, 2019-05-31. https://arxiv.org/abs/1906.01434 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[48] An analytic interpolation approach to stability margins with emphasis on time delay. arXiv:1912.08734, 2019-12-18. https://arxiv.org/abs/1912.08734 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[49] On the Stability Margin and Input Delay Margin of Linear Multi-agent systems. arXiv:2004.08332, 2020-04-17. https://arxiv.org/abs/2004.08332 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[50] A scheduling algorithm for networked control systems. arXiv:2101.00649, 2021-01-03. https://arxiv.org/abs/2101.00649 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[51] Optimal Sampled-Data Control of a Nonlinear System. arXiv:2112.14507, 2021-12-29. https://arxiv.org/abs/2112.14507 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[52] Criteria for stabilizing a multi-delay stochastic system with multiplicative control-dependent noises. arXiv:2303.08428, 2023-03-15. https://arxiv.org/abs/2303.08428 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[53] Nonlinear Cooperative Output Regulation with Input Delay Compensation. arXiv:2409.05113, 2024-09-08. https://arxiv.org/abs/2409.05113 - Difference from this work: treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query.

[54] Scheduling Periodic Real-Time Tasks with Heterogeneous Reward Requirements. arXiv:1007.0683, 2010-06-21. https://arxiv.org/abs/1007.0683 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[55] An Anytime Algorithm for Decision Making under Uncertainty. arXiv:1301.7384, 2013-01-30. https://arxiv.org/abs/1301.7384 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[56] Adaptive Fixed Priority End-To-End Imprecise Scheduling In Distributed Real Time Systems. arXiv:1306.0448, 2013-06-03. https://arxiv.org/abs/1306.0448 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[57] On The Age Of Information In Status Update Systems With Packet Management. arXiv:1506.08637, 2015-06-29. https://arxiv.org/abs/1506.08637 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[58] Age and Value of Information: Non-linear Age Case. arXiv:1701.06927, 2017-01-24. https://arxiv.org/abs/1701.06927 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[59] Stochastic Control with Stale Information--Part I: Fully Observable Systems. arXiv:1810.10983, 2018-10-25. https://arxiv.org/abs/1810.10983 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[60] Energy-Aware Scheduling of Task Graphs with Imprecise Computations and End-to-End Deadlines. arXiv:1905.04391, 2019-05-10. https://arxiv.org/abs/1905.04391 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[61] Scheduling Real-time Deep Learning Services as Imprecise Computations. arXiv:2011.01112, 2020-11-02. https://arxiv.org/abs/2011.01112 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[62] Effective anytime algorithm for multiobjective combinatorial optimization problems. arXiv:2403.08807, 2024-02-06. https://arxiv.org/abs/2403.08807 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[63] PerLLM: Personalized Inference Scheduling with Edge-Cloud Collaboration for Diverse LLM Services. arXiv:2405.14636, 2024-05-23. https://arxiv.org/abs/2405.14636 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[64] Robust Data-Driven Receding Horizon Control. arXiv:2510.06153, 2025-10-07. https://arxiv.org/abs/2510.06153 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[65] ML Inference Scheduling with Predictable Latency. arXiv:2512.18725, 2025-12-21. https://arxiv.org/abs/2512.18725 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[66] Adapter-Augmented Bandits for Online Multi-Constrained Multi-Modal Inference Scheduling. arXiv:2603.06403, 2026-03-06. https://arxiv.org/abs/2603.06403 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[67] Pareto-Optimal Anytime Algorithms via Bayesian Racing. arXiv:2603.08493, 2026-03-09. https://arxiv.org/abs/2603.08493 - Difference from this work: prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself.

[68] On the Stability of Receding Horizon Control for Continuous-Time Stochastic Systems. arXiv:1208.3830, 2012-08-19. https://arxiv.org/abs/1208.3830 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[69] Linear Receding Horizon Control with Probabilistic System Parameters. arXiv:1402.4568, 2014-02-19. https://arxiv.org/abs/1402.4568 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[70] Reinforcement Learning of the Prediction Horizon in Model Predictive Control. arXiv:2102.11122, 2021-02-22. https://arxiv.org/abs/2102.11122 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[71] Model Predictive Control with Models of Different Granularity and a Non-uniformly Spaced Prediction Horizon. arXiv:2108.08014, 2021-08-18. https://arxiv.org/abs/2108.08014 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[72] Receding Horizon Inverse Reinforcement Learning. arXiv:2206.04477, 2022-06-09. https://arxiv.org/abs/2206.04477 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[73] Stability-Oriented Prediction Horizons Design of Generalized Predictive Control for DC/DC Boost Converter. arXiv:2404.16391, 2024-04-25. https://arxiv.org/abs/2404.16391 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[74] Prediction horizon shapes representations in predictive learning. arXiv:2511.09290, 2025-11-12. https://arxiv.org/abs/2511.09290 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[75] D3DWA: Adaptive Weight and Prediction-Horizon for Dynamic Window Approach via Dueling Double Deep Q-Network. arXiv:2609.22276, 2026-09-11. https://arxiv.org/abs/2609.22276 - Difference from this work: bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling.

[76] The Lambert Way to Gaussianize heavy tailed data with the inverse of Tukey's h as a special case. arXiv:1010.2265, 2010-10-11. https://arxiv.org/abs/1010.2265 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[77] Stability for Receding-horizon Stochastic Model Predictive Control. arXiv:1410.5083, 2014-10-19. https://arxiv.org/abs/1410.5083 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[78] Iterative methods for the delay Lyapunov equation with T-Sylvester preconditioning. arXiv:1507.02100, 2015-07-08. https://arxiv.org/abs/1507.02100 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[79] Constraint-Tightening and Stability in Stochastic Model Predictive Control. arXiv:1511.03488, 2015-11-11. https://arxiv.org/abs/1511.03488 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[80] Technical Report: Infinite Horizon Discrete-Time Linear Quadratic Gaussian Tracking Control Derivation. arXiv:1807.04700, 2018-07-12. https://arxiv.org/abs/1807.04700 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[81] Residual-based iterations for the generalized Lyapunov equation. arXiv:1807.10715, 2018-07-27. https://arxiv.org/abs/1807.10715 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[82] Adaptive Control and Regret Minimization in Linear Quadratic Gaussian (LQG) Setting. arXiv:2003.05999, 2020-03-12. https://arxiv.org/abs/2003.05999 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[83] Discounted Cost Linear Quadratic Gaussian Control for Descriptor Systems. arXiv:2004.08932, 2020-04-19. https://arxiv.org/abs/2004.08932 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[84] Stochastic Model Predictive Control for Linear Systems with Unbounded Additive Uncertainties. arXiv:2104.10383, 2021-04-21. https://arxiv.org/abs/2104.10383 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[85] Safe Stochastic Model Predictive Control. arXiv:2204.06207, 2022-04-13. https://arxiv.org/abs/2204.06207 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[86] Heavy-Tailed NGG Mixture Models. arXiv:2211.00867, 2022-11-02. https://arxiv.org/abs/2211.00867 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[87] Stochastic Model Predictive Control with Dynamic Chance Constraints. arXiv:2305.19262, 2023-05-30. https://arxiv.org/abs/2305.19262 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[88] Lyapunov equations: a (fixed) point of view. arXiv:2406.07324, 2024-06-11. https://arxiv.org/abs/2406.07324 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[89] Identifying Time-varying Costs in Finite-horizon Linear Quadratic Gaussian Games. arXiv:2511.14358, 2025-11-18. https://arxiv.org/abs/2511.14358 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[90] Sign-Based Optimizers Are Effective Under Heavy-Tailed Noise. arXiv:2602.07425, 2026-02-07. https://arxiv.org/abs/2602.07425 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[91] Asynchronous Heavy-Tailed Optimization. arXiv:2602.18002, 2026-02-20. https://arxiv.org/abs/2602.18002 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[92] Delay periodic Lyapunov equation. arXiv:2605.15926, 2026-05-15. https://arxiv.org/abs/2605.15926 - Difference from this work: used here as the exact instrument (ground truth), not as a contribution.

[93] Hierarchical Solution of Markov Decision Processes using Macro-actions. arXiv:1301.7381, 2013-01-30. https://arxiv.org/abs/1301.7381 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[94] Macro-Action-Based Deep Multi-Agent Reinforcement Learning. arXiv:2004.08646, 2020-04-18. https://arxiv.org/abs/2004.08646 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[95] MAGIC: Learning Macro-Actions for Online POMDP Planning. arXiv:2011.03813, 2020-11-07. https://arxiv.org/abs/2011.03813 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[96] LISPR: An Options Framework for Policy Reuse with Reinforcement Learning. arXiv:2012.14942, 2020-12-29. https://arxiv.org/abs/2012.14942 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[97] The Logical Options Framework. arXiv:2102.12571, 2021-02-24. https://arxiv.org/abs/2102.12571 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[98] Meta-learning how to Share Credit among Macro-Actions. arXiv:2506.13690, 2025-06-16. https://arxiv.org/abs/2506.13690 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[99] ToMacVF : Temporal Macro-action Value Factorization for Asynchronous Multi-Agent Reinforcement Learning. arXiv:2507.10251, 2025-07-14. https://arxiv.org/abs/2507.10251 - Difference from this work: amortizes a learned decision over a span, not a priced query over a commit horizon.

[100] Deep Amortized Inference for Probabilistic Programs. arXiv:1610.05735, 2016-10-18. https://arxiv.org/abs/1610.05735 - Difference from this work: amortizes a modelling or learning cost, not a per-query price.

[101] Amortized Inference Regularization. arXiv:1805.08913, 2018-05-23. https://arxiv.org/abs/1805.08913 - Difference from this work: amortizes a modelling or learning cost, not a per-query price.

[102] Generalization Gap in Amortized Inference. arXiv:2205.11640, 2022-05-23. https://arxiv.org/abs/2205.11640 - Difference from this work: amortizes a modelling or learning cost, not a per-query price.

[103] Neural Methods for Amortized Inference. arXiv:2404.12484, 2024-04-18. https://arxiv.org/abs/2404.12484 - Difference from this work: amortizes a modelling or learning cost, not a per-query price.

[104] Path-dependent Discrete Amortized Inference. arXiv:2608.08644, 2026-08-09. https://arxiv.org/abs/2608.08644 - Difference from this work: amortizes a modelling or learning cost, not a per-query price.

[105] Non-linear Task-Space Disturbance Observer for Position Regulation of Redundant Robot Arms against Perturbations in 3D Environments. arXiv:1311.0388, 2013-11-02. https://arxiv.org/abs/1311.0388 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[106] Boundary control of cascaded ODE-Heat equations under actuator saturation. arXiv:1608.03729, 2016-08-12. https://arxiv.org/abs/1608.03729 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[107] Disturbance Observer-based Robust Control and Its Applications: 35th Anniversary Overview. arXiv:1902.09032, 2019-02-24. https://arxiv.org/abs/1902.09032 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[108] A Guide to Design Disturbance Observer. arXiv:1912.06331, 2019-12-13. https://arxiv.org/abs/1912.06331 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[109] Disturbance Observer. arXiv:2101.02859, 2021-01-08. https://arxiv.org/abs/2101.02859 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[110] Event-triggered Consensus of Matrix-weighted Networks Subject to Actuator Saturation. arXiv:2110.13356, 2021-10-26. https://arxiv.org/abs/2110.13356 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[111] Extremum Seeking Control for Multivariable Maps under Actuator Saturation. arXiv:2504.08005, 2025-04-09. https://arxiv.org/abs/2504.08005 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[112] Hybrid Control of ADT Switched Linear Systems subject to Actuator Saturation. arXiv:2602.18247, 2026-02-20. https://arxiv.org/abs/2602.18247 - Difference from this work: characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel.

[113] Robustness of Control Barrier Functions for Safety Critical Control. arXiv:1612.01554, 2016-12-05. https://arxiv.org/abs/1612.01554 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[114] Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations. arXiv:1709.10087, 2017-09-28. https://arxiv.org/abs/1709.10087 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[115] Reinforcement Learning of Active Vision for Manipulating Objects under Occlusions. arXiv:1811.08067, 2018-11-20. https://arxiv.org/abs/1811.08067 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[116] Learning View and Target Invariant Visual Servoing for Navigation. arXiv:2003.02327, 2020-03-04. https://arxiv.org/abs/2003.02327 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[117] CausalWorld: A Robotic Manipulation Benchmark for Causal Structure and Transfer Learning. arXiv:2010.04296, 2020-10-08. https://arxiv.org/abs/2010.04296 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[118] Learning Sequences of Manipulation Primitives for Robotic Assembly. arXiv:2011.00778, 2020-11-02. https://arxiv.org/abs/2011.00778 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[119] Dual Quaternion-Based Visual Servoing for Grasping Moving Objects. arXiv:2107.08149, 2021-07-17. https://arxiv.org/abs/2107.08149 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[120] RB2: Robotic Manipulation Benchmarking with a Twist. arXiv:2203.08098, 2022-03-15. https://arxiv.org/abs/2203.08098 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[121] Dexterous Imitation Made Easy: A Learning-Based Framework for Efficient Dexterous Manipulation. arXiv:2203.13251, 2022-03-24. https://arxiv.org/abs/2203.13251 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[122] Learning Stable Dynamical Systems for Visual Servoing. arXiv:2204.05681, 2022-04-12. https://arxiv.org/abs/2204.05681 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[123] BulletArm: An Open-Source Robotic Manipulation Benchmark and Learning Framework. arXiv:2205.14292, 2022-05-28. https://arxiv.org/abs/2205.14292 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[124] Control Barrier Functions for Stochastic Systems and Safety-critical Control Designs. arXiv:2209.08728, 2022-09-19. https://arxiv.org/abs/2209.08728 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[125] Visual Servoing with Geometrically Interpretable Neural Perception. arXiv:2210.10549, 2022-10-19. https://arxiv.org/abs/2210.10549 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[126] A Risk-Aware Control: Integrating Worst-Case CVaR with Control Barrier Function. arXiv:2308.14265, 2023-08-28. https://arxiv.org/abs/2308.14265 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[127] Brain Functional Connectivity under Teleoperation Latency: a fNIRS Study. arXiv:2311.09062, 2023-11-15. https://arxiv.org/abs/2311.09062 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[128] Mastering Stacking of Diverse Shapes with Large-Scale Iterative Reinforcement Learning on Real Robots. arXiv:2312.11374, 2023-12-18. https://arxiv.org/abs/2312.11374 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[129] Never-Ending Behavior-Cloning Agent for Robotic Manipulation. arXiv:2403.00336, 2024-03-01. https://arxiv.org/abs/2403.00336 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[130] WoCoCo: Learning Whole-Body Humanoid Control with Sequential Contacts. arXiv:2406.06005, 2024-06-10. https://arxiv.org/abs/2406.06005 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[131] MuJoCo MPC for Humanoid Control: Evaluation on HumanoidBench. arXiv:2408.00342, 2024-08-01. https://arxiv.org/abs/2408.00342 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[132] Dexterous Manipulation through Imitation Learning: A Survey. arXiv:2504.03515, 2025-04-04. https://arxiv.org/abs/2504.03515 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[133] Sparse Imagination for Efficient Visual World Model Planning. arXiv:2506.01392, 2025-06-02. https://arxiv.org/abs/2506.01392 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.

[134] Policy-Guided World Model Planning for Language-Conditioned Visual Navigation. arXiv:2603.25981, 2026-03-26. https://arxiv.org/abs/2603.25981 - Difference from this work: evaluates a policy or a platform; we evaluate a deployment parameter common to all of them.
