# Issue #87 — R391 notes: the generator, the rivals, and the first read of PB1

R389 and R390 were instrument rounds (the closed form; the metric at every depth). **R391 is the first
round that measures a learning outcome**, and the first thing it did was falsify a "finding" that the
first version of its own instrument produced. That part is recorded first.

## 1. Seven defects this round produced, and what caught each

1. **A fixed-envelope rival manufactures an advantage.** With the Mahalanobis envelope fixed at 1, the
   quadratic form grew through the metric's own anisotropy, the kernel matrix went to the identity from
   gamma ~ 1, and the rival scored the predict-the-mean risk (0.93–1.02 of the target's variance). The
   instrument then "found" a quantum advantage of **0.94 of a variance** — every bit of it the untuned
   rival. The fix is the field's own protocol (`2608.18155`): every rival is a FAMILY over its envelope
   and the ridge, tuned jointly by nested CV on the training half only, and the rivals differ in the
   **geometry** they receive and in nothing else. After the fix the same cell reads −0.07 instead of
   −0.94. *A calibrated comparison is a claim about the tuning protocol, not only about the rival.*
2. **The oracle was mis-specified, and the claim on it measured the sample size.** It was fitted at
   λ ~ 0 with 22 features on 32 training points, so it overfitted and was beaten by kernels; the claim
   "the oracle must be the best predictor in every cell" then failed everywhere. Tuned, it still sits
   ~0.12 above the Bayes floor — which is what 22 features on 32 points costs, a property of the design
   rather than a broken instrument. The claim was replaced (below) and the oracle kept as a *reported
   reference* with no pass/fail attached.
3. **The excess-risk read was taken against the declared σ², not against the Bayes predictor.** It
   reported **−0.016** for a near-Bayes predictor: a negative excess risk, which is impossible in
   expectation. Reading against the Bayes predictor's own test error removes the bias by construction
   (the Bayes predictor is known here — the target is planted).
4. **The edge-set control failed on its own bookkeeping.** The support was {min,max}-canonicalised and
   compared against the raw edge list, whose last cycle edge is `(q−1, 0)`: the control read False at
   α = 1. Third round in a row of *a check whose object is not the object it names*.
5. **The least-squares closed-form metric is indefinite.** Fitting `2g(0) ~ k0 I + k1 Q` gives
   k0 = **−7.87** on this graph; a Gaussian with an indefinite precision *grows* with distance, and one
   cell scored **2.6e14** of a variance. The fit is meaningful (its diagonal prediction 28.91 matches the
   measured 28.91 exactly) but it is not a usable kernel, so the rival now uses the anchor's stated form
   `I + π²Q` verbatim, and the fit is kept as a *staleness reading*.
6. **A pointwise-matched Gaussian is not a kernel.** R390's field fact taken literally gives
   `K = exp(−½ dᵀ(W(z)+W(z'))/2 d)`, whose smallest eigenvalue is **−2.7e−3** at γ = 0.1 (genuinely
   indefinite) — kernel ridge on it blows up. So the primary matched rival must use ONE global metric per
   cell, and R390's "match pointwise" requirement cannot be met by a plain local Gaussian. That is a
   design finding, not a rival.
7. **"Numerically zero" is not "genuinely indefinite".** The same diagnostic reads **−2.2e−14** at γ = 0 —
   where the kernel is a rank-1 constant matrix and the negative eigenvalue is round-off. A PSD verdict
   has to be read against the matrix's own scale, not against zero.

## 2. The generator, and why ground truth is by construction

- data: `z ∈ {0,1}^q`, the full hypercube, uniform;
- encoding: the ZZ map at the angle vector `x = γ·z`, so `γ` IS the bandwidth axis;
- target: `y = zᵀAz`, a pure interaction function, with **A planted** so that
  `cos_F(A, Q_int) = α` holds algebraically (`A = α Q̂_int + √(1−α²) R⊥`, `R⊥` random with its `Q`
  component projected out), measured at **2.22e−16** (C1);
- ground truth: the Bayes predictor IS `f`, so excess risk is read against the Bayes predictor's own test
  error (defect 3) and is in units of the target's variance.

**A declared design consequence**: the labels do not depend on γ — the target is a function of the
bitstring, and γ only controls the map. That is why the isotropic RBF, the random-feature kernel and the
oracle read the same value at every bandwidth of a cell; they are the γ-free reference lines against which
the map's bandwidth dependence is read.

## 3. The first read (q = 6, cycle(6), L = 2, shifted convention, σ = 0.30, 40 paired splits)

Excess risk over the Bayes floor, in units of the target's variance. `Δ = quantum − matched`; negative
means the quantum kernel leads.

| α | γ | quantum | matched | closed-form | rbf | randfeat | oracle | Δ [95% CI] |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 1.0215 | 1.0215 | 1.0215 | 0.1615 | 0.5364 | 0.1234 | +0.0000 (tie, both constant) |
| 1 | 0.10 | **0.1116** | 0.1357 | 0.1412 | 0.1615 | 0.5364 | 0.1234 | **−0.0241** [−0.046,−0.005] |
| 1 | 0.25 | 0.2014 | 0.1454 | 0.1415 | 0.1615 | 0.5364 | 0.1234 | +0.0560 [+0.008,+0.098] |
| 1 | 0.50 | 0.5256 | 0.1403 | 0.1411 | 0.1615 | 0.5364 | 0.1234 | +0.3853 [+0.321,+0.451] |
| 1 | 1.00 | 0.5643 | 0.1480 | 0.1427 | 0.1615 | 0.5364 | 0.1234 | +0.4163 [+0.353,+0.482] |
| 1 | 2.00 | 0.1595 | 0.1389 | 0.1356 | 0.1615 | 0.5364 | 0.1234 | +0.0206 (tie) |
| 1 | 3.00 | **0.0772** | 0.1512 | 0.1409 | 0.1615 | 0.5364 | 0.1234 | **−0.0740** [−0.096,−0.052] |
| 0 | 0.10 | 0.8076 | 0.8418 | 0.6077 | **0.2045** | 1.1198 | 0.1577 | −0.0343 (tie) |
| 0 | 0.25 | 0.9641 | 0.8421 | 0.6141 | **0.2045** | 1.1198 | 0.1577 | +0.1220 |
| 0 | 0.50 | 0.7342 | 0.8291 | 0.6155 | **0.2045** | 1.1198 | 0.1577 | −0.0949 |
| 0 | 1.00 | 0.7081 | 0.8282 | 0.6029 | **0.2045** | 1.1198 | 0.1577 | −0.1201 |
| 0 | 2.00 | 0.3432 | 0.6002 | 0.6449 | **0.2045** | 1.1198 | 0.1577 | −0.2570 |
| 0 | 3.00 | 0.7477 | 0.3066 | 0.6686 | **0.2045** | 1.1198 | 0.1577 | +0.4411 |
| −1 | 0.10 | 0.1100 | 0.1213 | 0.1327 | 0.1461 | 0.6126 | 0.1144 | −0.0112 (tie) |
| −1 | 0.50 | 0.5037 | 0.1216 | 0.1352 | 0.1461 | 0.6126 | 0.1144 | +0.3821 |
| −1 | 1.00 | 0.5409 | 0.1358 | 0.1292 | 0.1461 | 0.6126 | 0.1144 | +0.4051 |
| −1 | 3.00 | **0.0688** | 0.1400 | 0.1365 | 0.1461 | 0.6126 | 0.1144 | **−0.0712** [−0.088,−0.055] |

**What the first read says, stated at the strength a single cell supports.**

1. **PB1's middle clause is not observed at α = 1** — the registered inverted U is absent; the matched
   rival dominates a wide middle band (γ ∈ [0.25, 1.0]) by up to **0.42 of a variance**, and the quantum
   kernel leads only at the two extreme bandwidths, by **0.024** (γ = 0.1) and **0.074** (γ = 3.0). One
   cell, one graph, one seed: this is a first read, and the registered scoring rule already says a
   flat/absent middle refutes that clause if it survives the other strata.
2. **The weak-surrogate control works.** Against the random-feature kernel the quantum kernel wins at
   every γ > 0 in the α = 1 cell (0.11–0.56 vs 0.5364; at γ = 0 both are degenerate and the quantum kernel
   is the worse of the two at 1.0215) — the field's residual advantage is reproduced — and it *dissolves*
   against the matched rival and against a tuned isotropic RBF. That is the whole point of the
   metric-matched comparison, measured.
3. **The direction of the α-dependence is the opposite of PB2's registered direction** (the orthogonal
   cell shows *larger* quantum leads than the aligned one: four leads up to 0.257 against the aligned
   cell's two leads of 0.024 and 0.074). The mechanism is visible in the table and is not mysterious: the
   matched and closed-form rivals inherit a geometry fitted to `Q`, so when the target is orthogonal to
   `Q` the inherited prior actively hurts (0.60–0.84 through γ = 2), while the geometry-free tuned RBF is
   unaffected and wins the whole cell at **0.2045**. PB2's direction is therefore *unresolved-to-
   contradicted* and is the single most interesting thing to interrogate next.
4. **The graph-only closed form is a strong rival.** `I + π²Q`, with no simulation at all, sits at
   0.13–0.14 in the α = 1 cells — inside the matched rival's own interval. The reduction is not the
   weak point of the comparison; the *field* is (defect 6).
5. **PB3 is not measured yet** — only the shifted convention ran.

## 4. Instrument status after R391

- generator: alignment planted algebraically (C1 2.22e−16), support control reads the expected
  True/False/True pattern at α = 1/0/−1 (C2);
- estimator: one nested-CV protocol for every predictor (8 envelopes × 6 ridge values × 3 folds);
  excess risk anchored exactly at 0 by the Bayes predictor through the real code path (C3) and read at
  ~1 by the constant kernel at γ = 0 (1.0215 / 1.0561 / 0.9942, reported, no threshold invented);
- null (A = 0): advantage 0.0567, below the aligned cell's 0.0740 (C4) — the null does not manufacture a
  lead;
- γ = 0: kernel identically 1, rank 1, |K−1| ≤ 4.44e−16 (C5);
- determinism: byte-identical on rebuild, sha256 in the report (C6);
- runtime 34 s, numpy 2.0.2, CPU-only, offline.

## 5. Next

- run the **unshifted (identity-metric) convention** — PB3's instrument — on the same grid;
- the **path / complete** graph strata, and one q = 8 cell, for stability;
- the **planted-alignment control** the registration promises: a cell where the matched rival is
  deliberately handicapped, which would have found an advantage had one existed;
- and the PB2 mechanism, read properly: `cos_F(A, Q)` swept finely at fixed γ, against the RBF's score.

Files: `smoke_v5.py` + `smoke_v5_results.json`. The first run's output is not kept as a file, but every
defect it exposed is written down above and in the source's docstring.
