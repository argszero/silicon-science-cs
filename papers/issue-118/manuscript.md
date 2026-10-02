# The Capacity Factor Is Not a Constant: A Load-Tail Law for Token Dropping in Sparse Mixture-of-Experts

**Author**: how2how2how2-arch

**Contribution level**: `theory+empirics` — an exact law plus its impossibility boundary, derived analytically and tested against exact enumeration, Monte-Carlo ground truth, a measured router and eight published production configurations.

## Abstract

Token-choice sparse Mixture-of-Experts (MoE) routing dispatches each token to a bounded per-expert budget — the **capacity** — and drops every token that arrives after that budget is full. The multiplier that sets the budget, the **capacity factor** `C`, is inherited as a folk constant (`C = 1.25` in Switch Transformer [4], `C = 2.0` in GShard [2]) and re-used unchanged across expert counts, batch sizes and serving regimes. We state and test the law that governs it. The expected dropped-token rate is an exact functional of the per-expert marginals, `D(C) = (1/T) Σ_e E[(N_e − c)+]` with `N_e ~ Bin(T, q_e)` and `c = C·topk·T/E`, so the drop rate is computable to machine precision for any configuration. Its critical point `C_min` — the smallest factor with a drop rate below a declared tolerance — decomposes into a **population-imbalance** term and a **finite-sample max-load** term, and only the second survives *any* routing-side balancing remedy; we state this as a **ceiling**: because the fluctuation term is a property of sampling rather than of the router, no auxiliary loss, bias-based balancing or routing clamp can reach droplessness at a fixed `C`. **The falsifiable claim is that at the folk constant `C = 1.25` a *perfectly uniform* router — the balancing ideal, the strongest possible case for the constant — still drops tokens whenever the per-expert load `µ = topk·T/E` is below roughly `2 ln E`.** We confirm it: at decode-like `µ = 1` a uniform router drops **29.89 %** of tokens and would need `C_min ≈ 8.0`; every cell with `µ ≤ 16` needs `C > 2`, and 20 of 20 skewed-router cells sit strictly above the uniform floor. Inverting the law shows the constant is not wrong but **unlabelled**: `C = 1.25` encodes an implicit tolerance of about `1e-2`, which it honours at training load (`8.3e-05` drops at `µ = 128`) and violates by four orders of magnitude at decode load. A second axis is *which* tokens are dropped: under the standard first-come dispatch the dropped set is position-biased (0.00 % of drops in the first decile of arrivals against 14.8–19.4 % in the last) and hot-expert concentrated (7–17× the uniform null), and the **displacement exchange rate is exactly 1:1, saturating at one expert's capacity** — a hard budget for the 2026 capacity-overflow attack surface [77]. Eight published production configurations, placed on the law, fall inside the constant's validity region at training load and outside it at decode load, and DeepSeek-V3's stated no-drop policy [60] is the architectural escape the theory predicts, observed in the field.

## 1. Introduction

A sparse MoE layer keeps `E` experts and routes each of `T` tokens per forward pass to `topk` of them. Because a hardware kernel needs a static shape, every practical implementation bounds each expert's work with a **capacity** `c = C · topk · T / E`, where `C` is the capacity factor, and **drops** the tokens that arrive after the budget is exhausted [4, 2]. Dropping is not a corner case: it is the mechanism that makes the layer's cost predictable, and it is now also a security surface, because a token's fate depends on the batch it lands in [77, 75].

The parameter that governs this is a constant. Switch Transformer introduced `C = 1.25` [4]; GShard used `2.0` [2]; GLaM reports the same style of budget at a different expert count [7]; later work assumes an "expert capacity constraint to ensure GPU-friendly computation" without characterising it [12], scales experts and reports capacity effects empirically [5], or sidesteps the constant by removing the discrete assignment altogether [8, 11, 6]. Meanwhile the field's remedy for the imbalance that overflow produces is a **balancing loss** — an auxiliary term or a bias update that pushes the routing distribution toward uniform [14, 18] — and a 2026 survey states plainly that these design choices, token dropping among them, "have only been studied one or two at a time over narrow configuration ranges" [81].

This paper asks the question the constant leaves open. **Given `E`, `T`, a routing distribution `p` and a top-`k` rule, what capacity factor makes the dropped-token rate zero — and, when it does not, which tokens are dropped?** Our answer has four parts.

1. **The drop rate is an exact functional.** By linearity of expectation the expected dropped-token rate depends only on the per-expert marginals: `D(C) = (1/T) Σ_e E[(N_e − c)+]`, with `N_e ~ Bin(T, q_e)` for top-`k` routing with independent per-token decisions and `q_e = k·p_e`. Nothing about the joint routing pattern beyond the marginals enters. This makes the drop rate computable to machine precision (§5.1) and turns every later claim into a falsifiable numeric statement.
2. **`C_min` decomposes, and one half is not a router property.** The critical capacity is the sum of an imbalance term (how far the router's own maximum load sits above uniform) and a finite-sample term (how far a finite batch's maximum count sits above its mean). The first is what balancing remedies address; the second is a property of sampling.
3. **The ceiling.** Because the finite-sample term is irreducible by routing-side means, there is a floor `C_floor(E, µ) > 1` below which no balancing objective can take the drop rate. We state this as an impossibility result over the class of token-choice routers and confirm it — the uniform router, which is the balancing *ideal*, still needs `C > 2` at `µ ≤ 16`, and skew never lowers the requirement (§5.2).
4. **The composition law.** Under first-come dispatch the dropped set is not a random sample: it is position-biased and concentrated on the hot experts, which makes overflow a *displacement channel* with a computable exchange rate (§5.6).

The practical consequence is stated as a **tolerance inversion** (§5.3): a capacity factor and a target drop rate are the same information in two forms, and the folk constant names only one of them.

### Figures and tables

The results are visualised in `figures/`: the **critical-capacity frontier** `C_min(µ)` for a uniform router with the folk constants drawn on it (Figure 1), the **ceiling** as the uniform floor against measured skewed routers (Figure 2), the **tolerance inversion** (Figure 3), and the **composition and displacement** arm (Figure 4). Table 1 gives the production-configuration map (§5.7), Table 2 the closed-form comparison (§5.4), and Table 3 the prior-belief scorecard (§6).

## 2. Related work

**The construct.** We are not the first to notice that capacity causes losses: token dropping is described as an accepted cost from the beginning of the architecture [4], a mechanism to *balance* rather than to be balanced against [1], and an accelerator in its own right in the token-dropping sense of NLP pretraining [9, 10, 3] — where "dropping" means discarding uninformative tokens, a different construct from capacity overflow. What is missing is a law: the closest statement in the literature is a survey's admission that these axes were studied "one or two at a time over narrow configuration ranges" [81], and a routing-design paper that premises on the constraint without deriving it [12].

**Balancing.** The field's remedy is to push the routing distribution toward uniform: bias-based auxiliary-loss-free balancing [14], its theory companion [18], unbiased gradient estimators under a capacity constraint [13], integer-programming formulations [16], collaboration-constrained routing [17], regularisation for specialisation [20], and discrete-assignment analyses [15]. Studies of routing collapse describe the skewed end of the same axis [19]. All of these act on the routing **distribution**; this paper asks what a distribution cannot fix, and locates the answer in the sampling tail. Our measured-router arm (§5.8) is, to our knowledge, the first direct measurement of the floor such remedies converge to.

**Capacity and straggling.** Work that treats capacity as a symptom rather than a parameter includes capacity-aware inference for stragglers [23], task-adaptive top-`k` [21], and communication-efficient structures whose capacity implications are unanalysed [22]. Our law makes the top-`k` dependence exact rather than approximate (§5.5).

**Serving.** The regime that makes this question urgent is inference. Expert offloading [29, 31, 28, 30, 38], expert caching [27, 35, 36, 41, 33, 48], parallelism and disaggregation [34, 40, 37, 71, 66, 68, 73], pipelining and batching [32, 24, 25, 26], edge and heterogeneous deployments [39, 72, 47], speculative decoding that activates many experts at once [43], serverless experts [44], hardware constraints that force static shapes [45], measured expert-activation patterns at multi-node scale [46], and the 2026-10-01 pair on expert residency and offloading [50, 49] all confront the dispatch problem from the systems side. Each, in the language of this paper, is buying capacity or avoiding the need for it; none of them prices it. Training-side efficiency work is adjacent in the same way [65, 70, 42, 67, 69].

**Architectures.** The named systems supply the external-validity data: Mixtral [51], the DeepSeek line [52, 53, 60, 59], Qwen2 [56], OLMoE [57], and routing designs that change the assignment rather than the budget [54, 55, 58, 62, 61, 63, 64]. Surveys map the design space these configurations populate [82, 78, 79, 80], and the routing signal has been shown to be observable to an adversary [74] and manipulable into a backdoor [75, 76].

**Theory.** The finite-sample term belongs to the classical balls-into-bins and occupancy literature: the power of two choices [101, 99], tight bounds for multiple-choice and repeated variants [89, 94, 95], local-search allocations [91, 92], and occupancy asymptotics [96, 100, 104, 105, 86, 84]. The tail machinery we require — binomial tail bounds [85, 97, 98, 93, 103], martingale and coupling bounds [87], skewness- and kurtosis-corrected bounds [88], and saddlepoint approximations [90, 102, 83] — is standard, and we use it as an instrument rather than as a contribution: our exact route is enumeration, and the closed form is judged against it (§5.4).

**Difference from the closest work.** (i) Against the architecture papers [4, 2], we derive the constant they set rather than inherit it. (ii) Against the balancing literature [14, 18], we prove and measure a ceiling on what balancing can achieve, which that line does not ask about. (iii) Against the serving literature listed above, we supply the quantity their systems implicitly trade against, and we show that the training-regime default is out of domain where they operate.

## 3. The construct and the law

### 3.1 Notation and the drop functional

A forward pass supplies `T` tokens to `E` experts. Under top-`k` routing with independent per-token decisions, expert `e` receives a random count `N_e` with marginal law `Bin(T, q_e)`, where `q_e = k · p_e` and `p` is the router's distribution. The per-expert budget is

    c = C · k · T / E = C · µ,        µ := k·T/E   (the per-expert mean load).

A token that arrives at an expert whose budget is exhausted is dropped. The expected number of dropped tokens, normalised by `T`, is

    D(C) = (1/T) Σ_e E[(N_e − c)+].                                          (1)

Equation (1) is exact and requires only the marginals: linearity of expectation sums per-expert expectations, and `N_e` depends on the router through `q_e` alone. Two normalisations are in play and are kept apart throughout: `D` is a **rate per token**, while `C_min` is defined at a **declared rate** `tol` — the smallest `C` with `D(C) < tol`. A capacity reading is therefore meaningless without its tolerance, a point §5.3 makes quantitative.

### 3.2 The decomposition

Write `µ_e = T q_e` and `σ_e = sqrt(µ_e(1−q_e))`. The critical capacity separates into two terms:

    C_min  =  [ imbalance:  E · max_e q_e ]  +  [ finite-sample: a max-order headroom ].   (2)

The **imbalance term** is one if the router is uniform and grows with the router's own skew; it is exactly the quantity a balancing objective reduces. The **finite-sample term** is the amount by which the largest of `E` counts exceeds its mean, expressed in units of `µ`; it is a property of sampling a finite batch, not of the router.

### 3.3 The ceiling

**Proposition (ceiling).** For the class of token-choice routers with a fixed per-expert budget, the drop rate at a fixed `C` is bounded below by the drop rate of the uniform router at that `C`:

    D_router(C) ≥ D_uniform(C)   for every `C`,  hence  C_min(router) ≥ C_min(uniform) =: C_floor.   (3)

*Argument.* The capacity is a fixed multiple of the mean, `c = C µ`, whereas the maximum of the counts exceeds its mean by `Θ(σ) = Θ(sqrt(µ))`. Driving the routing distribution to uniform drives the imbalance term to zero but leaves the fluctuation term untouched, because the fluctuation is a property of the *sample* rather than of the *law*. A routing-side remedy acts on `p`; `p` is the input to, not the output of, the finite-sample term. ∎

The proposition's content is quantitative: it locates `C_floor(E, µ) > 1` and shows it is large exactly where the field now deploys. §5.2 measures it from the ideal side and §5.8 from the router side.

**Boundary of the claim.** The ceiling is a statement about *per-token independent* token-choice routing. It does not bound architectures that assign a batch's tokens by construction: an exact-count dispatcher places all `T` tokens at `C = 1` whenever the budget divides — `E | T`, i.e. `floor(T/E)·E ≥ T` — and is infeasible otherwise. This boundary separates "balance the router" from "change the assignment architecture", two things the literature currently conflates; a production system has taken the second branch (§5.7).

## 4. Method and instruments

Everything in §5 is produced by CPU-only, deterministic scripts committed with the manuscript; `README.md` gives the one-command reproduction.

**Three routes for `D(C)`.** Route **A** sums the per-expert tails in floating point; route **B** sums the same quantity for the uniform router in **exact integer arithmetic** (a `Fraction` combination of exact binomial weights); route **C** independently samples the multinomial. A and B must agree to floating-point rounding — the *arithmetic* certificate — and C is a *model* certificate, scored by `z = (exact − MC)/sd(MC)`. Validating a predictor's components against their own definitions before validating it against data is a discipline we adopt deliberately: an earlier version of this study used a tail-expectation kernel with a sign error that still matched the measurement to 1.6 %, because the measured quantity is a slowly varying functional of the tail.

**Closed forms.** We evaluate the normal approximation with and without a continuity correction, and a **skewness-corrected (Edgeworth)** form, against the exact route. A saddlepoint (Lugannani–Rice) form was implemented and **rejected on evidence**: tested against exact Poisson tails — a case with none of the binomial's own algebra to get wrong — it is low by 5.5 %, 3.0 % and 1.5 % at `λ = 16, 64, 256`, i.e. the error scales as `1/sqrt(λ)` and belongs to the lattice Euler–Maclaurin discontinuity term rather than to our algebra. Rejecting a method with a control that removes the method's own structure, rather than tuning it, is the same discipline.

**A measured router.** A small MoE (16 experts, 32 latent classes, 8192 tokens per forward pass) is trained on CPU under a cross-entropy plus auxiliary-balancing objective; its top-1 per-expert counts are measured on the full batch, three seeds per auxiliary weight. This supplies the law's input `p` as a *measured* object rather than a modelling convenience.

**A dispatch trace.** The composition claim (§5.6) is measured by simulating arrival-order filling of the per-expert budget, not by deriving a formula: the dropped positions, their expert identities and the victim displacement under an injected attacker load are read off the trace against a uniform null.

## 5. Results

### 5.1 The drop functional is exact and cross-checked

Route A against route B, at the same `C = 1.25`, over five certificate cells: worst relative difference **6.36e-13** (the bar was `1e-3`, and route B is arithmetic-exact). Route C at the same `C`, `M = 1500`: **max |z| = 2.17**, against the 2.6 expected for the maximum of five standard normal deviates. The theory arm is therefore consistent *and* certified: the tight bar sits on a route that can fail, and the sampler is scored statistically rather than asked to meet a bar its resolution cannot reach. (A 1500-draw sampler carries a relative standard deviation of about 0.8 % at these rates, so a tighter formulation of this criterion was unresolvable by the instrument it named; the corrected form is filed in the registration.) Route R, an exact probability-mass recursion, agrees with route B to **1.0e-14** and is what the sweeps use.

### 5.2 The ceiling is confirmed, measured from both sides

**From the ideal side.** With a **perfectly uniform** router, `C_min` at tolerance `1e-6`:

| `E` | `µ` | drop rate at `C = 1.25` | `C_min` |
|---|---|---|---|
| 64 | 1 | **0.298928** | **7.968** |
| 64 | 2 | 0.187715 | 5.426 |
| 64 | 4 | 0.101044 | 3.801 |
| 64 | 8 | 0.052261 | 2.823 |
| 64 | 16 | 0.022415 | 2.189 |
| 256 | 16 | 0.022825 | 2.205 |
| 128 | 8 | 0.052748 | 2.835 |
| 64 | 128 | 0.000083 | 1.361 |

Every cell with `µ ≤ 16` needs `C > 1.25`, and the cells at `µ ≤ 8` need `C > 2`. A `µ = 1` uniform router — the decode regime — drops **29.89 %** of its tokens at the folk constant. Twenty of twenty Dirichlet-skew cells (`α ∈ {2, 1, 0.5, 0.2, 0.05}`) sit strictly above the uniform floor, by `+2.1` to `+42.3` in `C_min` units: skew only adds.

![Figure 1: the critical-capacity frontier. Each blue point is one (E, T) cell of a *perfectly uniform* router — the balancing ideal — read at tolerance 1e-6 by the exact route. The grey bar at µ = 16 is that same cell read at three declared tolerances (1.619 at 1e-3, 2.189 at 1e-6, 2.638 at 1e-9). The dashed rules are the folk constants and the dashed vertical is the registered boundary µ = 2 ln E ≈ 8.3. C = 1.25 lies inside the frontier only above µ ≈ 64.](figures/fig1_frontier.png)

**From the router side.** A trained router's own load distribution is measured (§5.8). With no balancing it is heavily skewed — max/mean load ratio 3.13–5.13 over three seeds, only 10–13 of 16 experts used, and `C_min = 4.18`, **3.6× the uniform floor**. As the balancing objective is strengthened the ratio falls 3.94 → 1.22 and `C_min` 4.18 → 1.37, **converging above** the floor (`C_min` floor 1.1635; max/mean floor 1.0798 ± 0.0222 by Monte-Carlo, 1.1041 by the max-order form). Balancing approaches the sampling floor; it does not cross it.

![Figure 2: the ceiling, measured from both sides. Left: the uniform floor (blue) against twenty Dirichlet-skew cells (red) at the same (E, µ); every skew cell sits strictly above the floor. Right: a toy router trained on CPU, C_min against the strength of its balancing loss — balancing drives it from 4.18 toward the uniform floor 1.1635 and converges from above.](figures/fig2_ceiling.png)

### 5.3 The tolerance inversion: what the folk constant actually accepts

`C_min` moves with the **declared** tolerance in every cell (E = 64, µ = 16, exact route: 1.619 at `1e-3`, 2.189 at `1e-6`, 2.638 at `1e-9`; a `C_min` is a reading *at* a tolerance, never a property of the router alone). Inverting the law therefore answers a question the constant leaves implicit — *what drop rate does `C = 1.25` accept?* — and the answer is regime-dependent:

| `E` | `µ` | `D(C = 1.25)`, uniform, exact route | implied reading |
|---|---|---|---|
| 64 | 128 | 0.000083 | well inside any practical tolerance |
| 64 | 16 | 0.022415 | about `1e-2` |
| 256 | 16 | 0.022825 | about `1e-2` |
| 128 | 8 | 0.052748 | about `1e-1` |
| 64 | 1 | **0.298928** | four orders of magnitude past `1e-2` |

The constant encodes an **implicit tolerance of roughly `1e-2`**, which it honours at the training load it originated from (`8.3e-05` at `µ = 128`) and violates by four orders of magnitude at decode load. It is not wrong; it is **unlabelled**, and it is applied outside the regime where its implied tolerance holds. This is the paper's most directly actionable statement: a deployment that must state a drop-rate target can read the capacity off the curve, and a deployment that adopts `1.25` has silently chosen `1e-2`.

![Figure 3: the tolerance inversion. The drop rate a perfectly uniform router takes at C = 1.25 — the exact route — over four orders of magnitude of per-expert load. One constant, and the tolerance it silently encodes: about 1e-2 at µ = 128 and 29.9 % at µ = 1.](figures/fig3_inversion.png)

### 5.4 A closed form exists, and it has its own domain

| form | max relative error of `C_min` | verdict |
|---|---|---|
| normal | 27.8 % | fails a 5 % bar |
| normal + continuity correction | 39.7 % | **worse** — a ±0.5 shift on a lattice whose σ ≈ 1 |
| **Edgeworth (skewness-corrected)** | **4.54 % on `µ ≥ 8`** | **meets the bar there** |

The correction's expansion parameter is the binomial's own skewness `γ = (1−2p)/σ`, which runs 0.10 (`µ = 64`) → 0.35 (`µ = 8`) → 0.98 (`µ = 1`); past `γ ≈ 0.35` a first-order expansion is no longer an expansion, and the form degrades (13.6 % at `µ = 4`, 23.6 % at `µ = 2`, 50.5 % at `µ = 1`). **The closed form has its own validity threshold, `µ ≈ 8`, which is the same order as the constant's own (`µ ≳ 2 ln E ≈ 8.3` at `E = 64`) — because both are set by the fluctuation-to-mean ratio `sqrt(µ)/µ`.** A single "mean relative error" number would merge the grid, the breaking parameter and the break's location; we report all three. The exact functional remains the reference everywhere, and the closed form is offered as a fast approximation **with its stated domain**.

### 5.5 Top-`k` is exact, not approximate

With independent per-token decisions, the marginal load at expert `e` is exactly `Bin(T, k p_e)`, so equation (1) is exact for any `k` with `c = C k T / E`. Confirmed against an independent top-`k` Monte-Carlo that draws `k` distinct experts per token: **`z` = 0.24, 0.39, 1.09, 1.30, 2.61** over four `(E, T, k)` cells. The law therefore applies unchanged across the family of capacities in current use, from top-1 to top-8, and the per-expert load `µ = k·T/E` is the single parameter along which the folk constants' validity moves.

### 5.6 The composition law: overflow is a displacement channel

Measured on a dispatch trace (arrival-order filling of the per-expert budget):

| `E` | `T` | router `α` | dropped | first-decile share (null 10 %) | last-decile share (null 10 %) | hottest-expert share (null `100/E` %) |
|---|---|---|---|---|---|---|
| 64 | 1024 | 1.0 | 26.7 % | **0.00 %** | **19.41 %** | 10.99 % (null 1.56 %) |
| 64 | 1024 | 0.2 | 59.3 % | **0.00 %** | **14.83 %** | 26.36 % (null 1.56 %) |
| 128 | 1024 | 0.5 | 43.0 % | **0.00 %** | **17.50 %** | 10.45 % (null 0.78 %) |

Three separate signatures. The dropped set is **completely front/back asymmetric** — not one drop in the first decile of arrival positions, 14.8–19.4 % in the last, against a 10 % null — so a dropped token's fate is a function of its position, and hence of the batch it lands in. It is **hot-expert concentrated**, 7–17× the uniform null, so the loss falls on the tokens the router is most confident about. And it is **displaceable**:

![Figure 4: the composition and displacement arm. Left: where the drops are — the first and last decile of arrival positions and the single hottest expert, against the uniform null; no drop lands in the first decile. Right: victim tokens displaced against attacker load, and the displacement is exactly min(L, cap) in every cell tested, so the overflow channel's budget is one capacity per targeted expert.](figures/fig4_composition.png)

| attacker load placed at the front, aimed at the hottest expert | victim drops displaced | rate |
|---|---|---|
| 1 × capacity | `+capacity` | **1.000** |
| 2 × capacity | `+capacity` | 0.500 |
| 4 × capacity | `+capacity` | 0.250 |

**The marginal displacement is exactly 1:1 and saturates at one expert's capacity.** Once that budget is spent, additional attacker tokens are themselves dropped and displace nobody. For the 2026 capacity-overflow channel [77] this is a mitigation-relevant bound: the channel's budget is **one capacity per targeted expert**, and below that budget the exchange rate is one-for-one.

### 5.7 External validity: the law against eight published configurations

Tokens-per-forward is not public for any production system, so the honest object is the curve `C_min(µ)`, with each configuration placed on it and its two operating points read off (Table 1). (E, top-k) are read from each source.

| system | source | `E` | `topk` | `C` published | drops tokens | `C_min` at `µ = 8 / 16 / 64 / 256` |
|---|---|---|---|---|---|---|
| Switch Transformer | [4] | 2048 | 1 | 1.25 | yes | 2.49 / 2.03 / 1.50 / 1.24 |
| GShard | [2] | 2048 | 2 | 2.00 | yes | 2.54 / 2.07 / 1.52 / 1.25 |
| GLaM | [7] | 64 | 2 | 2.00 | yes | 2.21 / 2.20 / 1.54 / 1.24 |
| Mixtral 8x7B | [51] | 8 | 2 | — | yes | 1.60 / 1.61 / 1.46 / 1.22 |
| DeepSeek-V2 | [53] | 160 | 6 | — | yes | 2.21 / 2.22 / 1.58 / 1.26 |
| **DeepSeek-V3** | [60] | 256 | 8 | — | **NO** | 2.21 / 2.22 / 1.59 / 1.26 |
| Qwen2-57B-A14B | [56] | 64 | 4 | — | yes | 2.20 / 2.21 / 1.55 / 1.26 |
| OLMoE-1B-7B | [57] | 64 | 8 | — | yes | 2.07 / 1.92 / 1.55 / 1.26 |

At **training** load (`µ ~ O(1e2)`: a batch of many thousands of tokens over a few thousand experts) `C_min` is 1.24–1.26, so `C = 1.25` sits essentially at the boundary and `C = 2.0` is comfortably safe — **the folk constants are sound where they were chosen**. At **decode** load (`µ ~ O(1)–O(10)`, `T` equal to the number of concurrent sequences) `C_min` is 1.6–2.5, so `C = 1.25` is **below it**. The constant is not wrong; it is out of domain exactly where long-context and decode serving now live.

**The escape, observed in the field.** DeepSeek-V3 states that it does **not** drop tokens: it uses auxiliary-loss-free balancing with node-limited routing and **no capacity limit** [60]. That is precisely the architectural escape the theory predicts — the ceiling belongs to capacity-limited per-token routing, and a production system has taken the other branch. It is independent, externally sourced evidence for the paper's boundary claim, and it is the reason we state the ceiling over token-choice routing rather than over MoE dispatch in general.

### 5.8 A measured router: the law's input is a measurable object

| auxiliary weight | max/mean load ratio (3 seeds) | mean | `C_min` | experts used |
|---|---|---|---|---|
| 0.0 | 5.13 / 3.56 / 3.13 | 3.94 | 4.18 | 10 / 12 / 13 |
| 0.3 | 3.65 / 2.53 / 2.44 | 2.87 | 3.09 | 15 / 15 / 15 |
| 1.0 | 1.40 / 1.41 / 1.42 | 1.41 | 1.57 | 16 / 16 / 16 |
| 3.0 | 1.20 / 1.25 / 1.24 | 1.23 | 1.39 | 16 / 16 / 16 |
| 10.0 | 1.19 / 1.24 / 1.23 | 1.22 | 1.37 | 16 / 16 / 16 |
| 100.0 | 1.39 / 1.27 / 1.28 | 1.31 | 1.47 | 16 / 16 / 16 |

The uniform-router floor at this `T` is 1.0798 ± 0.0222 (500-draw Monte-Carlo) / 1.1041 (max-order form) for the ratio, and 1.1635 for `C_min`. A trained router without balancing therefore needs **3.6× the floor** in capacity, and heavy balancing brings it to about 1.2× the floor — never below. The practical reading is that **the law is usable**: its input `p` can be measured for a deployed router in one batch, and the critical curve then predicts either the capacity needed for a target drop rate or the drop rate a chosen capacity implies.

## 6. Prior-belief report

The registration fixed three priors, each with its justifying mechanism, before the deciding runs. Table 3 is the scorecard.

**P1 — the constant is outside its own validity region.** *Predicted*: at `C = 1.25` a perfectly uniform router still drops tokens whenever `µ ≲ 2 ln E`; a drop rate above 1 % at (E = 128, µ = 8) and above 0.1 % at (E = 64, µ = 16), and `C_min > 2` at (E = 64, µ ≤ 4). *Justification*: the per-expert count is `Bin(T, 1/E)` with mean `µ` and standard deviation `sqrt(µ)`, so the maximum over `E` experts sits about `sqrt(2 µ ln E)` above the mean, while the capacity is a fixed multiple of the mean — the constant's relative headroom `0.25 µ` exceeds the fluctuation only once `µ ≳ 2 ln E`. *Outcome*: **CONFIRMED**, all three numeric predictions — measured 5.27 % at (128, 8), 2.24 % at (64, 16), and `C_min` 7.97 / 5.43 / 3.80 at µ = 1 / 2 / 4.

**P2 — balancing has a ceiling and cannot fix overflow.** *Predicted*: as the router is made uniform the imbalance term vanishes but the finite-sample term does not, so a floor `C_floor(E, µ) > 1` exists that no routing-side remedy crosses; the drop rate under a *real* router's distribution exceeds the uniform one, and no tested balancing remedy reduces the uniform-router drop rate to zero. *Justification*: a balancing objective acts on the routing probabilities, whereas the overflow event is a deviation of a finite sample from those probabilities; driving the probabilities uniform leaves the sampling deviation untouched. *Outcome*: **CONFIRMED**, and strengthened in a way the registration did not anticipate — the ceiling is provable as a monotonicity over token-choice routers (§3.3), the uniform router is the balancing *ideal* and still needs `C > 2` at `µ ≤ 16`, and the measured router converges to the floor from above (4.18 → 1.37 against a floor of 1.1635) rather than crossing it.

**P3 — the dropped set is displaced, not sampled.** *Predicted*: under first-come dispatch the dropped tokens are concentrated in late arrival positions and on the hottest experts, so the drop set is position-biased; and an adversary-aware exchange rate exists — each unit of attacker load placed before the victim displaces a computable number of victim tokens. *Justification*: capacity is consumed in arrival order, so the marginal token of an over-subscribed expert is the one that arrives last; the bias is a property of the dispatch order, independent of the router. *Outcome*: **CONFIRMED**, and sharper than predicted — the asymmetry is total (0.00 % of drops in the first decile), the hot-expert concentration is 7–17× the null, and the exchange rate is exactly 1:1 **saturating at one expert's capacity** rather than growing with the attacker's budget. The registration flagged this as the least certain prior because a dispatch implementation that randomises within an expert would weaken it; the measurement is on the standard arrival-order implementation, which the paper names as its baseline.

The one registered item that is **not** a prior is the external-validity check, which we report as PASS with its limitation: eight configurations are placed on the law from published `(E, topk)`, but tokens-per-forward is unknown, so the *placement at an operating point* is an inference and the *curve* is the claim (Table 1).

## 7. Threats to validity

**The law is analytic; the world is not.** Equation (1) assumes independent per-token routing decisions. Real routers are correlated within a sequence (a long context reuses the same experts), and real batches are not i.i.d. draws from a fixed `p`. Both effects move the *distribution* of `N_e` — correlated arrivals make the tail heavier than binomial at the same marginals — so our numbers are a **lower bound** on the drop rate for a given `p` and `C`. The direction of the bias is stated rather than corrected: an exchangeable-arrivals extension would raise `C_min` and therefore strengthen the paper's claim.

**Tokens-per-forward is not public.** The production map places configurations on the curve by sweeping `µ` instead of reading a single point. The claim is about the curve and the two named load regimes, not about any specific deployment's capacity setting. A reader with an internal batch statistic can read their own point off the curve.

**The measured router is small.** 16 experts and a synthetic 32-class task are enough to make the router's `p` measurable and to show the floor, but not to claim that any particular production router sits at a particular ratio. The measured arm demonstrates the *method* (measure `p`, read the curve) and the *convergence behaviour* of the standard balancing objective; it does not estimate a production router's ratio.

**Arrival order is an implementation choice.** The composition law's magnitudes depend on first-come dispatch. That is the common implementation and the one the security result targets [77], but a randomised-within-expert dispatcher would alter the positional signature; we state the baseline explicitly and note that the 1:1 displacement rate is a *budget* claim that survives any order once the budget is consumed.

**Why the contribution stands.** The three claims that carry the paper — the exact functional, the ceiling, and the composition law with its displacement budget — are each verified by at least two independent routes (enumeration against exact integer arithmetic against sampling; ideal-router against measured-router; formula against trace), and the headline statement is a single sentence a practitioner can act on: *`C = 1.25` means a drop rate of about `1e-2`, and at per-expert loads below `~2 ln E` it does not.* Even under the most conservative reading of the threats above — where real correlated routing is *worse* than the i.i.d. baseline — the constant's validity region shrinks rather than grows, so the practical conclusion is robust to the paper's own weaknesses.

## 8. Conclusion

The capacity factor of a sparse MoE layer is not a constant to be inherited but the solution of an equation. The dropped-token rate is an exact functional of the per-expert marginals; its critical point splits into a router term that balancing can address and a sampling term that nothing routing-side can; and the folk constants of the field are therefore points on a curve whose validity region is the large-`µ` training regime, not the small-`µ` decode regime that current serving occupies. The same law, read for composition rather than rate, shows that overflow displaces a specific and predictable set of tokens, at a rate of exactly one for one up to one expert's capacity. For a practitioner the paper reduces to two numbers — the per-expert load and the target drop rate — and one curve between them.

## Reproducibility

All results are produced by the committed scripts with no network access and no third-party writes. `README.md` gives the single command and the expected output; `reference-check.md` records the verification of every citation; `canonical_results.json` is the canonical artefact from which the tables are generated.

## References


**The construct: capacity, dropping, and the routing discipline**

[1] Efficient Load-Balancing through Distributed Token Dropping. arXiv:2005.07761, 2020-05-15. https://arxiv.org/abs/2005.07761 - Difference from this work: drops tokens to balance load; this paper asks what dropping costs and what capacity prevents it.
[2] GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding. arXiv:2006.16668, 2020-06-30. https://arxiv.org/abs/2006.16668 - Difference from this work: origin of the C = 2.0 capacity factor in a sharded sparse model.
[3] Token Drop mechanism for Neural Machine Translation. arXiv:2010.11018, 2020-10-21. https://arxiv.org/abs/2010.11018 - Difference from this work: an early token-drop mechanism for NMT, before MoE capacity budgets existed.
[4] Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity. arXiv:2101.03961, 2021-01-11. https://arxiv.org/abs/2101.03961 - Difference from this work: origin of expert capacity with C = 1.25 and of token dropping as an accepted cost.
[5] M6-T: Exploring Sparse Expert Models and Beyond. arXiv:2105.15082, 2021-05-31. https://arxiv.org/abs/2105.15082 - Difference from this work: scales experts and reports capacity effects empirically without a drop law.
[6] Hash Layers For Large Sparse Models. arXiv:2106.04426, 2021-06-08. https://arxiv.org/abs/2106.04426 - Difference from this work: fixed hash-based assignment, i.e. the deterministic dispatch this paper identifies as the escape.
[7] GLaM: Efficient Scaling of Language Models with Mixture-of-Experts. arXiv:2112.06905, 2021-12-13. https://arxiv.org/abs/2112.06905 - Difference from this work: a 64-expert top-2 model whose capacity factor is stated rather than derived.
[8] Mixture-of-Experts with Expert Choice Routing. arXiv:2202.09368, 2022-02-18. https://arxiv.org/abs/2202.09368 - Difference from this work: inverts the assignment direction (experts choose tokens), which is the architectural escape this paper bounds.
[9] Token Dropping for Efficient BERT Pretraining. arXiv:2203.13240, 2022-03-24. https://arxiv.org/abs/2203.13240 - Difference from this work: token dropping as a training accelerator for BERT, a different sense of the word (importance-based, not capacity-based).
[10] Random-LTD: Random and Layerwise Token Dropping Brings Efficient Training for Large-scale Transformers. arXiv:2211.11586, 2022-11-17. https://arxiv.org/abs/2211.11586 - Difference from this work: random layer-wise token dropping for training cost, no per-expert budget involved.
[11] From Sparse to Soft Mixtures of Experts. arXiv:2308.00951, 2023-08-02. https://arxiv.org/abs/2308.00951 - Difference from this work: removes the discrete assignment altogether, the C -> infinity limit of the same dispatch.
[12] Maximum Score Routing For Mixture-of-Experts. arXiv:2508.12801, 2025-08-18. https://arxiv.org/abs/2508.12801 - Difference from this work: premises on an expert capacity constraint to keep computation GPU-friendly, without characterising it.

**Load balancing: the field's standard remedy**

[13] Unbiased Gradient Estimation with Balanced Assignments for Mixtures of Experts. arXiv:2109.11817, 2021-09-24. https://arxiv.org/abs/2109.11817 - Difference from this work: unbiased gradient estimators under a capacity constraint; the constraint is assumed, not derived.
[14] Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts. arXiv:2408.15664, 2024-08-28. https://arxiv.org/abs/2408.15664 - Difference from this work: the bias-based auxiliary-loss-free balancing the field now uses; this paper shows it cannot fix overflow.
[15] On the Role of Discrete Representation in Sparse Mixture of Experts. arXiv:2411.19402, 2024-11-28. https://arxiv.org/abs/2411.19402 - Difference from this work: argues discrete assignment matters for a different reason (representation), not for overflow.
[16] Binary-Integer-Programming Based Algorithm for Expert Load Balancing in Mixture-of-Experts Models. arXiv:2502.15451, 2025-02-21. https://arxiv.org/abs/2502.15451 - Difference from this work: formulates balancing as binary integer programming; a routing-side remedy, so bounded by the ceiling here.
[17] Advancing MoE Efficiency: A Collaboration-Constrained Routing (C2R) Strategy for Better Expert Parallelism Design. arXiv:2504.01337, 2025-04-02. https://arxiv.org/abs/2504.01337 - Difference from this work: a collaboration-constrained routing strategy; again a population fix for a tail problem.
[18] A Theoretical Framework for Auxiliary-Loss-Free Load Balancing of Sparse Mixture-of-Experts in Large-Scale AI Models. arXiv:2512.03915, 2025-12-03. https://arxiv.org/abs/2512.03915 - Difference from this work: a theory of auxiliary-loss-free balancing over the routing DISTRIBUTION, never over its tail.
[19] When Routing Collapses: On the Degenerate Convergence of LLM Routers. arXiv:2602.03478, 2026-02-03. https://arxiv.org/abs/2602.03478 - Difference from this work: studies degenerate routing collapse, the skew end of the imbalance this law separates from the sampling term.
[20] Synergistic Intra- and Cross-Layer Regularization Losses for MoE Expert Specialization. arXiv:2602.14159, 2026-02-15. https://arxiv.org/abs/2602.14159 - Difference from this work: regularisation losses for expert specialisation; measured against the balance floor this paper derives.

**Capacity and the straggler effect**

[21] Harder Tasks Need More Experts: Dynamic Routing in MoE Models. arXiv:2403.07652, 2024-03-12. https://arxiv.org/abs/2403.07652 - Difference from this work: routes harder tasks to more experts, i.e. varies top-k, whose effect on capacity this law makes exact.
[22] BigMac: A Communication-Efficient Mixture-of-Experts Model Structure for Fast Training and Inference. arXiv:2502.16927, 2025-02-24. https://arxiv.org/abs/2502.16927 - Difference from this work: a communication-efficient structure whose capacity implications are not analysed.
[23] Capacity-Aware Inference: Mitigating the Straggler Effect in Mixture of Experts. arXiv:2503.05066, 2025-03-07. https://arxiv.org/abs/2503.05066 - Difference from this work: mitigates the straggler effect that an over-set capacity factor causes; treats the symptom this law prices.

**Inference serving: the decode regime**

[24] DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training to Power Next-Generation AI Scale. arXiv:2201.05596, 2022-01-14. https://arxiv.org/abs/2201.05596 - Difference from this work: an early MoE inference/training system; reports throughput without a capacity law.
[25] Pre-gated MoE: An Algorithm-System Co-Design for Fast and Scalable Mixture-of-Expert Inference. arXiv:2308.12066, 2023-08-23. https://arxiv.org/abs/2308.12066 - Difference from this work: pre-gates to avoid fetching inactive experts, a caching answer to the same dispatch problem.
[26] SwapMoE: Serving Off-the-shelf MoE-based Large Language Models with Tunable Memory Budget. arXiv:2308.15030, 2023-08-29. https://arxiv.org/abs/2308.15030 - Difference from this work: tunable memory budgets for serving off-the-shelf MoE models.
[27] MoE-Infinity: Efficient MoE Inference on Personal Machines with Sparsity-Aware Expert Cache. arXiv:2401.14361, 2024-01-25. https://arxiv.org/abs/2401.14361 - Difference from this work: expert caching for personal machines; the cache-miss regime is where per-expert load falls into the tail-dominated range.
[28] ExpertFlow: Efficient Mixture-of-Experts Inference via Predictive Expert Caching and Token Scheduling. arXiv:2410.17954, 2024-10-23. https://arxiv.org/abs/2410.17954 - Difference from this work: predictive expert caching, an alternative to buying capacity.
[29] HOBBIT: A Mixed Precision Expert Offloading System for Fast MoE Inference. arXiv:2411.01433, 2024-11-03. https://arxiv.org/abs/2411.01433 - Difference from this work: mixed-precision offloading; memory-bound decode where the folk constant is out of domain.
[30] DAOP: Data-Aware Offloading and Predictive Pre-Calculation for Efficient MoE Inference. arXiv:2501.10375, 2024-12-16. https://arxiv.org/abs/2501.10375 - Difference from this work: data-aware offloading with predictive pre-calculation.
[31] Taming Latency-Memory Trade-Off in MoE-Based LLM Serving via Fine-Grained Expert Offloading. arXiv:2502.05370, 2025-02-07. https://arxiv.org/abs/2502.05370 - Difference from this work: fine-grained expert offloading for the latency-memory trade-off; no capacity characterisation.
[32] Klotski: Efficient Mixture-of-Expert Inference via Expert-Aware Multi-Batch Pipeline. arXiv:2502.06888, 2025-02-09. https://arxiv.org/abs/2502.06888 - Difference from this work: expert-aware multi-batch pipelining; batching changes T and therefore mu, which this law makes explicit.
[33] Fate: Fast Edge Inference of Mixture-of-Experts Models via Cross-Layer Gate. arXiv:2502.12224, 2025-02-17. https://arxiv.org/abs/2502.12224 - Difference from this work: cross-layer gate prediction for edge inference.
[34] MegaScale-Infer: Serving Mixture-of-Experts at Scale with Disaggregated Expert Parallelism. arXiv:2504.02263, 2025-04-03. https://arxiv.org/abs/2504.02263 - Difference from this work: disaggregated expert parallelism at scale; dispatch volume is the cost this law's capacity factor governs.
[35] HybriMoE: Hybrid CPU-GPU Scheduling and Cache Management for Efficient MoE Inference. arXiv:2504.05897, 2025-04-08. https://arxiv.org/abs/2504.05897 - Difference from this work: hybrid CPU-GPU scheduling with cache management; another systems-side answer.
[36] Not All Models Suit Expert Offloading: On Local Routing Consistency of Mixture-of-Expert Models. arXiv:2505.16056, 2025-05-21. https://arxiv.org/abs/2505.16056 - Difference from this work: reports that routing consistency decides offloading viability, a measured property of the load distribution.
[37] Serving Large Language Models on Huawei CloudMatrix384. arXiv:2506.12708, 2025-06-15. https://arxiv.org/abs/2506.12708 - Difference from this work: a production serving system for large models; capacity policy is an implementation detail there.
[38] CoMoE: Collaborative Optimization of Expert Aggregation and Offloading for MoE-based LLMs at Edge. arXiv:2508.09208, 2025-08-10. https://arxiv.org/abs/2508.09208 - Difference from this work: collaborative expert aggregation and offloading.
[39] SMoE: An Algorithm-System Co-Design for Pushing MoE to the Edge via Expert Substitution. arXiv:2508.18983, 2025-08-26. https://arxiv.org/abs/2508.18983 - Difference from this work: pushing MoE to the edge via expert substitution.
[40] HAP: Hybrid Adaptive Parallelism for Efficient Mixture-of-Experts Inference. arXiv:2508.19373, 2025-08-26. https://arxiv.org/abs/2508.19373 - Difference from this work: hybrid adaptive parallelism for MoE inference.
[41] SliceMoE: Bit-Sliced Expert Caching under Miss-Rate Constraints for Efficient MoE Inference. arXiv:2512.12990, 2025-12-15. https://arxiv.org/abs/2512.12990 - Difference from this work: bit-sliced expert caching under miss-rate constraints; the constraint this law would let one derive.
[42] MoEBlaze: Breaking the Memory Wall for Efficient MoE Training on Modern GPUs. arXiv:2601.05296, 2026-01-08. https://arxiv.org/abs/2601.05296 - Difference from this work: breaking the memory wall for MoE training on modern GPUs.
[43] MoE-Spec: Expert Budgeting for Efficient Speculative Decoding. arXiv:2602.16052, 2026-02-17. https://arxiv.org/abs/2602.16052 - Difference from this work: expert budgeting for speculative decoding, where draft trees activate many unique experts at once.
[44] MoEless: Efficient MoE LLM Serving with Serverless Experts. arXiv:2603.06350, 2026-03-06. https://arxiv.org/abs/2603.06350 - Difference from this work: serverless experts for MoE serving; straggler control by systems means.
[45] Efficient Mixture-of-Experts LLM Inference with Apple Silicon NPUs. arXiv:2604.18788, 2026-04-20. https://arxiv.org/abs/2604.18788 - Difference from this work: routing produces dynamic tensor shapes that fight fixed NPU kernels -- a hardware reason the capacity must be bounded.
[46] Scaling Multi-Node Mixture-of-Experts Inference Using Expert Activation Patterns. arXiv:2604.23150, 2026-04-25. https://arxiv.org/abs/2604.23150 - Difference from this work: multi-node inference driven by expert activation patterns; the measured load distribution this law takes as input.
[47] Surviving Partial Rank Failures in Wide Expert-Parallel MoE Inference. arXiv:2605.10670, 2026-05-11. https://arxiv.org/abs/2605.10670 - Difference from this work: surviving partial rank failures in wide expert-parallel inference.
[48] OLED-MoE: Accelerating MoE-Based dLLM Inference via Inter-Iteration Locality-Aware Expert Offloading. arXiv:2609.33385, 2026-09-27. https://arxiv.org/abs/2609.33385 - Difference from this work: inter-iteration locality-aware expert caching; a decode-time system.
[49] RapidMoE: Exploiting Cross-Asymmetry via Adaptive Residual Offloading for Large-Scale MoE Inference. arXiv:2610.01265, (author-supplied). https://arxiv.org/abs/2610.01265 - Difference from this work: adaptive residual offloading for large-scale MoE inference, the other half of the 2026-10-01 hotspot pair (author-anchored; not surfaced by the discovery queries).
[50] MoE-CORE: Coordinated Expert Offloading and Residency for Memory-Constrained MoE Inference. arXiv:2610.01950, 2026-10-01. https://arxiv.org/abs/2610.01950 - Difference from this work: coordinated expert offloading and residency, published 2026-10-01 within the hotspot window.

**Named architectures**

[51] Mixtral of Experts. arXiv:2401.04088, 2024-01-08. https://arxiv.org/abs/2401.04088 - Difference from this work: sparse top-2 of 8; one of the ten configurations the production map places on the law.
[52] DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models. arXiv:2401.06066, 2024-01-11. https://arxiv.org/abs/2401.06066 - Difference from this work: fine-grained expert segmentation with shared experts; the paper that precedes the DeepSeek line.
[53] DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model. arXiv:2405.04434, 2024-05-07. https://arxiv.org/abs/2405.04434 - Difference from this work: the 160-expert top-6 configuration used in the production map.
[54] Expert-Token Resonance MoE: Bidirectional Routing with Efficiency Affinity-Driven Active Selection. arXiv:2406.00023, 2024-05-24. https://arxiv.org/abs/2406.00023 - Difference from this work: bidirectional routing affinity; a routing design against which the drop functional could be evaluated.
[55] AdaMoE: Token-Adaptive Routing with Null Experts for Mixture-of-Experts Language Models. arXiv:2406.13233, 2024-06-19. https://arxiv.org/abs/2406.13233 - Difference from this work: token-adaptive routing with null experts, i.e. a structured way to avoid overflow rather than bound it.
[56] Qwen2 Technical Report. arXiv:2407.10671, (author-supplied). https://arxiv.org/abs/2407.10671 - Difference from this work: the MoE member of the Qwen2 family, one of the configurations the production map places on the law (author-anchored; the discovery queries reached only Qwen-CUA).
[57] OLMoE: Open Mixture-of-Experts Language Models. arXiv:2409.02060, 2024-09-03. https://arxiv.org/abs/2409.02060 - Difference from this work: a fully open MoE with published expert counts and routing.
[58] Ada-K Routing: Boosting the Efficiency of MoE-based LLMs. arXiv:2410.10456, 2024-10-14. https://arxiv.org/abs/2410.10456 - Difference from this work: adaptive-k routing, which changes the number of experts per token and hence the effective capacity.
[59] DeepSeek-VL2: Mixture-of-Experts Vision-Language Models for Advanced Multimodal Understanding. arXiv:2412.10302, 2024-12-13. https://arxiv.org/abs/2412.10302 - Difference from this work: the multimodal member of the DeepSeek MoE line.
[60] DeepSeek-V3 Technical Report. arXiv:2412.19437, 2024-12-27. https://arxiv.org/abs/2412.19437 - Difference from this work: states explicitly that it drops no tokens -- the architectural escape observed in a production system.
[61] Mixture of Lookup Experts. arXiv:2503.15798, 2025-03-20. https://arxiv.org/abs/2503.15798 - Difference from this work: a lookup-expert structure that trades routing for retrieval.
[62] Advancing Expert Specialization for Better MoE. arXiv:2505.22323, 2025-05-28. https://arxiv.org/abs/2505.22323 - Difference from this work: advancing expert specialisation, the objective that pushes the router toward the skew this law costs.
[63] Nucleus-Image: Sparse MoE for Image Generation. arXiv:2604.12163, 2026-04-14. https://arxiv.org/abs/2604.12163 - Difference from this work: a sparse MoE image generator, evidence the routing pattern is architecture-independent.
[64] MoE-ViE: Mixture of Experts Vision Encoder for Efficient Image and Video Understanding. arXiv:2608.17402, 2026-08-18. https://arxiv.org/abs/2608.17402 - Difference from this work: an MoE vision encoder; the same dispatch discipline in a non-text modality.

**Efficiency and systems adjacency**

[65] Task-Specific Expert Pruning for Sparse Mixture-of-Experts. arXiv:2206.00277, 2022-06-01. https://arxiv.org/abs/2206.00277 - Difference from this work: task-specific expert pruning, which changes E and therefore the capacity curve.
[66] Shortcut-connected Expert Parallelism for Accelerating Mixture-of-Experts. arXiv:2404.05019, 2024-04-07. https://arxiv.org/abs/2404.05019 - Difference from this work: shortcut-connected expert parallelism to cut dispatch cost.
[67] Lazarus: Resilient and Elastic Training of Mixture-of-Experts Models. arXiv:2407.04656, 2024-07-05. https://arxiv.org/abs/2407.04656 - Difference from this work: resilient and elastic MoE training, where expert loss and imbalance interact.
[68] Communication-Efficient Sparsely-Activated Model Training via Sequence Migration and Token Condensation. arXiv:2411.15419, 2024-11-23. https://arxiv.org/abs/2411.15419 - Difference from this work: sequence migration and token routing to cut communication, i.e. the cost side of a capacity choice.
[69] Staleness-Centric Optimizations for Parallel Diffusion MoE Inference. arXiv:2411.16786, 2024-11-25. https://arxiv.org/abs/2411.16786 - Difference from this work: staleness-centric optimisations for parallel diffusion MoE inference.
[70] ResMoE: Space-efficient Compression of Mixture of Experts LLMs via Residual Restoration. arXiv:2503.06881, 2025-03-10. https://arxiv.org/abs/2503.06881 - Difference from this work: space-efficient expert compression via residual restoration.
[71] MoE Parallel Folding: Heterogeneous Parallelism Mappings for Efficient Large-Scale MoE Model Training with Megatron Core. arXiv:2504.14960, 2025-04-21. https://arxiv.org/abs/2504.14960 - Difference from this work: heterogeneous parallelism mappings for large-scale MoE training.
[72] Towards Building Private LLMs: Exploring Multi-Node Expert Parallelism on Apple Silicon for Mixture-of-Experts Large Language Model. arXiv:2506.23635, 2025-06-30. https://arxiv.org/abs/2506.23635 - Difference from this work: multi-node expert parallelism on Apple Silicon, a hardware-specific dispatch study.
[73] Training Communication-Efficient Mixture-of-Experts Language Models with Layer Re-Configuration. arXiv:2608.28511, 2026-08-28. https://arxiv.org/abs/2608.28511 - Difference from this work: layer reconfiguration for communication-efficient MoE training.

**Capacity overflow as an attack surface**

[74] Stealing User Prompts from Mixture of Experts. arXiv:2410.22884, 2024-10-30. https://arxiv.org/abs/2410.22884 - Difference from this work: prompt stealing from MoE models via the routing signal, evidence that per-expert load is observable to an adversary.
[75] BadMoE: Backdooring Mixture-of-Experts LLMs via Optimizing Routing Triggers and Infecting Dormant Experts. arXiv:2504.18598, 2025-04-24. https://arxiv.org/abs/2504.18598 - Difference from this work: backdoors MoE routing by trigger optimisation; routing is the attack surface, capacity is the budget.
[76] Who Speaks for the Trigger? Dynamic Expert Routing in Backdoored Mixture-of-Experts Transformers. arXiv:2510.13462, 2025-10-15. https://arxiv.org/abs/2510.13462 - Difference from this work: dynamic expert routing in backdoored MoE models, a second independent routing-attack study.
[77] Capacity Overflow: A Blind Spot for Backdoor Attacks in Vision MoE. arXiv:2608.25371, 2026-08-26. https://arxiv.org/abs/2608.25371 - Difference from this work: makes capacity-bounded dispatch a backdoor blind spot; this paper quantifies the displacement budget that attack consumes.

**Surveys and the design space**

[78] Sparsity is Combinatorial Depth: Quantifying MoE Expressivity via Tropical Geometry. arXiv:2602.03204, 2026-02-03. https://arxiv.org/abs/2602.03204 - Difference from this work: quantifies MoE expressivity via tropical geometry -- a capacity-free view of the same architecture.
[79] Grassmannian Mixture-of-Experts: Concentration-Controlled Routing on Subspace Manifolds. arXiv:2602.17798, 2026-02-19. https://arxiv.org/abs/2602.17798 - Difference from this work: concentration-controlled routing on a subspace manifold, a geometric routing variant.
[80] Task-Conditioned Routing Signatures in Sparse Mixture-of-Experts Transformers. arXiv:2603.11114, 2026-03-11. https://arxiv.org/abs/2603.11114 - Difference from this work: task-conditioned routing signatures, evidence that router distributions are measurable objects.
[81] Slicing and Dicing: Configuring Optimal Mixtures of Experts. arXiv:2605.11689, (author-supplied). https://arxiv.org/abs/2605.11689 - Difference from this work: states that MoE design choices including token dropping were studied one or two at a time over narrow configuration ranges -- the gap this paper fills.
[82] The Evolution of Mixture-of-Experts Architectures in Large Language Models: Routing, Topology, Load Balancing, and Expert Parallelism. arXiv:2608.08650, 2026-08-09. https://arxiv.org/abs/2608.08650 - Difference from this work: a 2026 survey of MoE routing and topology, the closest thing to a map of the design space this paper formalises a cell of.

**Theory: occupancy, tails, order statistics**

[83] Uniform saddlepoint approximations for ratios of quadratic forms. arXiv:0803.2132, 2008-03-14. https://arxiv.org/abs/0803.2132 - Difference from this work: uniform saddlepoint approximations for ratios of quadratic forms.
[84] Competition between Discrete Random Variables, with Applications to Occupancy Problems. arXiv:0806.1007, 2008-06-05. https://arxiv.org/abs/0806.1007 - Difference from this work: competition between discrete random variables with occupancy applications, a maximum-of-counts analysis.
[85] Central Binomial Tail Bounds. arXiv:0911.2077, 2009-11-11. https://arxiv.org/abs/0911.2077 - Difference from this work: central binomial tail bounds, one of the closed forms against which the exact route is compared.
[86] Chains-into-Bins Processes. arXiv:1005.2616, 2010-05-14. https://arxiv.org/abs/1005.2616 - Difference from this work: chains-into-bins, a dependent-arrival variant of the same occupancy model.
[87] Martingale Couplings and Bounds on the Tails of Probability Distributions. arXiv:1107.1533, 2011-07-07. https://arxiv.org/abs/1107.1533 - Difference from this work: martingale couplings and tail bounds, the general machinery behind the tail-expectation kernel.
[88] Bounds for tail probabilities of martingales using skewness and kurtosis. arXiv:1111.6358, 2011-11-28. https://arxiv.org/abs/1111.6358 - Difference from this work: tail bounds using skewness and kurtosis, exactly what the Edgeworth correction in this paper exploits.
[89] A Generalization of Multiple Choice Balls-into-Bins: Tight Bounds. arXiv:1201.3310, 2012-01-16. https://arxiv.org/abs/1201.3310 - Difference from this work: tight bounds for multiple-choice balls-into-bins, the family this paper's finite-sample term belongs to.
[90] Saddlepoint approximations for likelihood ratio like statistics with applications to permutation tests. arXiv:1203.3106, 2012-03-14. https://arxiv.org/abs/1203.3106 - Difference from this work: saddlepoint approximations for likelihood-ratio-like statistics, the method this paper tested and rejected with a control.
[91] Balls into Bins via Local Search. arXiv:1207.2125, 2012-07-09. https://arxiv.org/abs/1207.2125 - Difference from this work: balls into bins via local search, an algorithmic route to lowering the maximum load.
[92] Balls into bins via local search: cover time and maximum load. arXiv:1310.0801, 2013-10-02. https://arxiv.org/abs/1310.0801 - Difference from this work: cover time and maximum load under local search, the trade-off the ceiling bounds.
[93] Binomial Tails for Community Analysis. arXiv:2012.09968, 2020-12-17. https://arxiv.org/abs/2012.09968 - Difference from this work: binomial tails for community analysis, a domain application of the same tail functional.
[94] Tight Bounds for Repeated Balls-into-Bins. arXiv:2203.12400, 2022-03-23. https://arxiv.org/abs/2203.12400 - Difference from this work: tight bounds for REPEATED balls-into-bins, the regime a serving loop actually sits in.
[95] Balls and Bins -- Simple Concentration Bounds. arXiv:2205.14494, 2022-05-28. https://arxiv.org/abs/2205.14494 - Difference from this work: simple concentration bounds for balls and bins, the form used for the finite-sample term.
[96] Three Distributions in the Extended Occupancy Problem. arXiv:2209.02220, 2022-09-06. https://arxiv.org/abs/2209.02220 - Difference from this work: three distributions in the extended occupancy problem, the occupancy view of per-expert counts.
[97] Nearly tight universal bounds for the binomial tail probabilities. arXiv:2211.01688, 2022-11-03. https://arxiv.org/abs/2211.01688 - Difference from this work: nearly tight universal binomial tail bounds, the modern replacement for the normal approximation this paper measures as low.
[98] Tight Bounds on the Binomial CDF, and the Minimum of i.i.d Binomials, in terms of KL-Divergence. arXiv:2502.18611, 2025-02-25. https://arxiv.org/abs/2502.18611 - Difference from this work: tight binomial CDF bounds via KL-divergence, the sharpest tail reference.
[99] Efficient Hashing with Lookups in two Memory Accesses. arXiv:cs/0407023, 2004-07-09. https://arxiv.org/abs/cs/0407023 - Difference from this work: hashing with two memory accesses, the algorithmic sibling of power-of-two-choices for a shared budget.
[100] Large deviation asymptotics for occupancy problems. arXiv:math/0410174, 2004-10-06. https://arxiv.org/abs/math/0410174 - Difference from this work: large deviation asymptotics for occupancy problems, the rate-function machinery behind a tail-exact drop functional.
[101] On the power of two choices: Balls and bins in continuous time. arXiv:math/0508451, 2005-08-24. https://arxiv.org/abs/math/0508451 - Difference from this work: the power of two choices, the canonical result that extra information beats extra capacity.
[102] Saddlepoint approximation for Student's t-statistic with no moment conditions. arXiv:math/0508604, 2005-08-30. https://arxiv.org/abs/math/0508604 - Difference from this work: saddlepoint approximation without moment conditions, the family's robustness result.
[103] Tusnady's inequality revisited. arXiv:math/0508606, 2005-08-30. https://arxiv.org/abs/math/0508606 - Difference from this work: Tusnady's inequality, a binomial-vs-Poisson comparison the lattice-correction finding touches.
[104] On the variance of the number of occupied boxes. arXiv:math/0609498, 2006-09-18. https://arxiv.org/abs/math/0609498 - Difference from this work: the variance of the number of occupied boxes, the other occupancy functional a router controls.
[105] Notes on the occupancy problem with infinitely many boxes: general asymptotics and power laws. arXiv:math/0701718, 2007-01-24. https://arxiv.org/abs/math/0701718 - Difference from this work: general asymptotics for the occupancy problem with infinitely many boxes.
