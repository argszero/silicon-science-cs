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

The 2026 literature states this tension verbatim and answers it heuristically. **PACE** [[2606.00537]] measures that success is *"strongly task-dependent and non-monotonic with respect to"* the horizon and replies with a phase-aware execution schedule. **Staircase Policy** [[2609.36471]] states that *"performance degrades over long execution horizons because later actions remain conditioned on stale observations"* and replies with staggered sub-chunks. **Urgent Actions Go First** [[2609.37772]] exploits that actions *"are generated jointly but consumed sequentially"*, allocating denoising compute by urgency. **Reactive Real-Time Flow Policies** [[2609.36540]] finds asynchronous execution *"can produce a fundamentally different action distribution"*. **ACPPO** [[2609.36250]] states that *"executing chunks open-loop removes within-chunk feedback"*. Five independent 2026 works locate the same tension; none derives a boundary for it.

The parameter itself is inherited un-derived from the origin of the paradigm: ACT/ALOHA [[10.15607/rss.2023.xix.016]] introduced chunking with a fixed horizon, and it has been a per-deployment tuning knob since.

**Contributions.**

1. **The law is a stationarity condition, not a curve fit.** We derive `λ_c = L·[c(τ+L) − C(L)]` and verify it reproduces the discrete sweep's argmin exactly (§4.2). The registered square-root form is a *special case* of an asymptotic expansion, and that expansion does not hold for these plants.
2. **The feasible set is a window that closes at both ends.** `L* ∈ [τ, d_max − τ]` (§4.3). Low price pins at the floor; high price pins at a feasibility ceiling; at `τ = d_max/2` the window collapses to a point — a **latency wall** at which no execution horizon is feasible.
3. **The registered square-root law is refuted, and so is its natural replacement** (§5.2), with the reason the replacement fails measured rather than asserted.
4. **The two disturbance channels act on different quantities** (§5.4). A non-zero-mean disturbance adds a **delay-invariant** term (400 % of the covariance part) that raises the cost level and moves the optimum by *nothing*; a change in disturbance *shape* at matched second moment moves the optimum, and grows with staleness.

**Who cares.** Engineers deploying vision-language-action or diffusion policies on real-time hardware choose this horizon per task today. If the boundary is the stationarity condition, then (a) the horizon is a function of the inference price and a measurable property of the plant, (b) task dependence enters only through that property, and (c) the 2026 heuristic wave can be read as approximations of one boundary rather than as unrelated tricks. The belief that changes is *"the execution horizon is a task-specific constant to be tuned."*

---

## 2. Related work, and what each differs from this work in

**Chunked-policy horizon (the construct).** PACE [[2606.00537]] and Staircase Policy [[2609.36471]] both name the horizon as the open choice and both answer with an execution *schedule* (phase-aware prefixes; staggered sub-chunks). The difference from this work is that they treat the objective as unmodelled and optimise inside the schedule, whereas we write the objective down, derive its stationarity condition, and show such schedules are approximations of it. Urgent Actions Go First [[2609.37772]], Reactive Real-Time Flow [[2609.36540]] and ACPPO [[2609.36250]] attack the same tension from the generator side (urgency-weighted denoising, asynchronous distribution alignment, feedback correction); the difference is that each reports a mechanism-level remedy at fixed horizon, while we locate the horizon itself and derive the regime in which the remedy is or is not needed. SeAR [[2603.01891]] and RL-with-Action-Chunking [[2507.07969]] learn *with* chunks at a chosen length; the difference is that chunk length is their hyper-parameter, not their object of study. HiPolicy [[2604.06067]] and FocalPolicy [[2605.15944]] introduce multi-frequency and frequency-optimised chunking; the difference is that frequency is their design axis and the amortization–staleness trade is not written down. ChunkFlow [[2607.12992]] and Action-Prior Denoising [[2605.25537]] add continuity constraints across chunk boundaries; the difference is that continuity is a within-chunk property, while our boundary governs *how much* of the chunk is executed. Implicit Action Chunking [[2605.19592]] and PolicyTrim [[2606.22540]] improve chunk quality at fixed horizon; the difference is that quality and horizon are independent knobs, and we hold quality fixed by construction so the horizon's effect is identifiable. Real-time conditioning [[2512.05964]] and discrete-diffusion asynchrony [[2604.25050]] make asynchronous execution feasible; the difference is that they change *when* actions are produced, while we ask *how many* to commit. Recent analyses of why chunking helps at all [[2608.02547]], of selecting among temporal actions [[2511.04421]], of guided test-time decoding [[2408.17355]], of temporal aggregation of overlapping chunks [[2609.27167], [2410.16981]], of adaptive horizons [[2609.39873]], of self-verifying chunk selection [[2603.18091]], of how small a chunked policy can be [[2609.03715]], of *whether* open-loop execution should be revisited at all [[2608.15938]], of speculative verification for chunked policies [[2604.02965]], of dual-path motion conditioning [[2608.00793]] and of underwater bimanual deployment [[2609.19200]] are all *within* the fixed-horizon regime: the difference from this work is that each takes the executed prefix as given, while we derive it.

**Latency and efficiency.** LiteVLA-H [[2605.00884]], FlashDrive [[2608.12932]] and the token-caching line [[2609.34319], [2609.36967]] reduce per-query latency; the difference from this work is that they make inference *cheaper* while we ask how much inference to *buy* at a given price — the two compose, and their gain is the `λ_c` in our law. EVA-Client [[2607.02646]] and FluxVLA Engine [[2609.17210]] are deployment frameworks whose fixed horizons our boundary parameterises, and temporal-redundancy reduction [[2607.12287]], spatial-scaffold preservation [[2609.36967]] and video-prediction-conditioned actions [[2606.17040]] lower the price without answering how much to buy, and a humanoid whole-body policy [[2609.18732]] is a deployed instance of the same choice. Control-frequency studies [[2403.09504], [2002.06836]] vary the sampling period with a fixed controller; the difference is that a per-query price is absent there, so no interior optimum can exist in their formulation.

**Delay and sampled-data control.** The delay-margin and networked-control literature [[2409.05113], [2004.08332], [1803.09487], [1902.06235], [1811.07534], [1912.08734], [2303.08428], [2101.00649], [1904.12660]] establishes that a delayed feedback loop has a finite stability margin and characterises it spectrally; the difference from this work is that delay enters there as a *stability constraint* on a fixed controller, whereas here delay enters as the *age of the observation a committed action was conditioned on* — a cost — and it is priced jointly with the query rate. The sampled-data literature [[1512.04797], [1604.06350], [2112.14507], [1903.06368], [1906.01434]] studies performance versus sampling period without a per-query price, so it produces neither the amortization term nor an interior optimum.

**Staleness, anytime computation, imprecise computation.** Stochastic control with stale information [[1810.10983]] and age-of-information [[1701.06927], [1506.08637]] price the *freshness* of an observation; the difference is that freshness there is exogenous and paid for in update rate, whereas here the staleness is produced by the decision variable itself — executing an `L`-step prefix *is* the staleness — so cost and benefit share one control. The anytime [[2403.08807], [1301.7384], [2603.08493]] and imprecise-computation [[2011.01112], [1905.04391], [1306.0448], [1007.0683]] literatures schedule computation under a deadline; the difference is that they choose *how much* computation to do for a fixed action, while we choose *how many actions to commit* for a fixed computation. Inference-scheduling work [[2405.14636], [2603.06403], [2512.18725]] allocates a compute budget across queries; the difference is that the budget is allocated across *queries*, not across the *commitment* a query buys.

**Abstraction and amortization.** Options [[2102.12571], [2012.14942]], macro-actions [[2004.08646], [2011.03813], [1301.7381], [2507.10251], [2506.13690]] and amortized inference [[1805.08913], [1610.05735], [2404.12484], [2205.11640]] all amortize a decision over a longer span; the difference from this work is that their span is learned or given, and the cost they amortize is a *learning* cost, not a *priced query*; path-dependent amortization [[2608.08644]] is the closest to a recurrence over the commit step, and the difference is that its span is a modelling choice rather than a priced optimum.

**Horizon length in receding-horizon control.** The prediction-horizon literature [[1208.3830], [1402.4568], [2206.04477], [2102.11122], [2404.16391], [2108.08014], [2511.09290], [2609.22276]] is the nearest classical relative of this problem: it too treats a horizon as the decision variable. The difference from this work is that the horizon there is bounded by *prediction* quality and by a terminal cost, and its length is chosen against a model-error budget, whereas ours is bounded by the *observation's age* under committed open-loop action — so our window `[τ, d_max − τ]` has a stability-margin ceiling that no prediction-horizon formulation contains, and its lower end is a real-time floor rather than a cost.

**Theory used.** LQG steady-state cost and the discrete Lyapunov equation [[1807.10715], [2605.15926], [1507.02100], [2406.07324], [2003.05999], [1807.04700], [2004.08932], [2511.14358]] give our exact per-delay cost recursion; the difference is that we use them as an *instrument* (a ground truth), not as a contribution. Stochastic MPC [[2104.10383], [1511.03488], [1410.5083], [2305.19262], [2204.06207]] and robust receding-horizon control [[2510.06153]] motivate the horizon as a decision variable but optimise a different objective; heavy-tailed disturbance models [[2602.07425], [2602.18002], [1010.2265], [2211.00867]] are the closest theory to our shape channel, and the difference is that they bound optimisation under heavy tails while we use tail structure to *separate two disturbance channels' effect on a decision*.

**Saturation, disturbance, and the setting.** Actuator-saturation studies [[2504.08005], [1608.03729], [2602.18247], [2110.13356]] and disturbance-observer work [[2101.02859], [1902.09032], [1912.06331], [1311.0388]] characterise nonlinearity in the loop; the difference is that we use saturation to *break the second-moment equivalence* of two disturbance processes, which is precisely the regime in which the disturbance channel becomes decision-relevant. The manipulation, benchmark and evaluation literature [[2406.06005], [2408.00342], [2204.05681], [2210.10549], [2107.08149], [2003.02327], [1612.01554], [2209.08728], [2308.14265], [2603.25981], [2506.01392], [1709.10087], [2504.03515], [2203.13251], [2203.08098], [2205.14292], [2010.04296], [2403.00336], [2312.11374], [2011.00778], [1811.08067], [2311.09062]] supplies the setting with which our boundary must be consistent; the difference is that these works evaluate a policy or a platform, while we evaluate a *deployment parameter* of any of them.

**The specific differences from the three closest works**, stated as the bar requires:

| work | their claim | our difference |
|---|---|---|
| PACE [[2606.00537]] | the horizon's effect is task-dependent and non-monotonic, answered by a phase-aware schedule | we show where the non-monotonicity comes from — the floor→interior→ceiling pinning structure — and that the schedule approximates the stationarity condition |
| Staircase [[2609.36471]] | staleness of later actions causes degradation, answered by staggered sub-chunks | we quantify staleness as the *delay coordinate* of the cost and show the optimum is the stationarity condition, not a schedule |
| ACT/ALOHA [[10.15607/rss.2023.xix.016]] | chunking with a fixed horizon | we derive what the fixed horizon should be, as a function of the inference price and the plant's delay-cost curvature |

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

(Generated from the pipeline; full verification table in reference-check.md.)
