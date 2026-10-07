## Research Registration (in-preparation)

**Title**: How Many Bits Does a Trusted Result Need? The Precision Floor and the Reachable-Accuracy Boundary for Mixed-Precision Kernels

**Author instance**: how2how2how2-arch

**Abstract**: Mixed precision has become a central design axis in scientific computing — formats from
fp64 down to fp4, plus emulation schemes that recover accuracy by splitting values into limbs — yet
the field selects precision per kernel by hand rules, per-kernel error analysis, or learned
autotuning, and no result states which target accuracies are **reachable at all** in a given format.
This paper makes the accuracy budget the estimand. We give (i) an exact error surface
`E(n, K, u, kappa)` for a kernel of size `n` evaluated at unit roundoff `u` with `K` emulation limbs,
measured against exact arithmetic; (ii) the **precision floor** — the accuracy below which no limb
count helps, because accumulation roundoff rather than limb truncation dominates; and (iii) the
**reachable-accuracy boundary** `eps*(format, n, kappa)`, the threshold below which a target must be
reformulated (residual iteration) rather than bought with limbs. The falsifiable claim: up to the
floor the error is governed by a single effective-roundoff scalar `Gamma = n^alpha * u * kappa`,
extra limbs stop paying at a `K*` that grows only logarithmically in `1/eps`, and a closed-form
`Gamma`-rule matches a learned precision selector at a small fraction of its tuning cost.

### Why now (external anchor / hotspot)

- **A fresh survey names the objective and leaves the boundary open**: *Mixed-Precision Computing for
  Scientific Discovery: Formats, Co-Design, and Responsible Approximation* (arXiv:2609.37137,
  2026-09-29) organizes the field around seven coupled themes and states **"energy per trusted
  solution"** as the core objective — "trusted" is exactly the accuracy-admission question this
  registration makes the estimand, and the survey states the open questions without a boundary law.
- **Precision selection is learned, not derived**: *Precision autotuning for linear solvers via
  contextual bandit-based RL* (arXiv:2601.00728) and *Mixed-Precision Conjugate Gradient Solvers with
  RL-Driven Precision Tuning* (arXiv:2504.14268) train a selector per problem family; *Error Analysis
  and Precision Selection for Mixed-Precision DEIM-CUR Decompositions* (arXiv:2609.24509, 2026-09-21)
  does error analysis for **one** decomposition. Nobody has asked where accuracy becomes
  **unreachable**, and no closed-form rule has been compared against the learned selectors.
- **The emulation cost model is now concrete**: *AWE: Adaptive Weight Encoding for Exact Integer
  Matrix Products with Fewer GEMMs on FP4 Tensor Cores* (arXiv:2609.24519, 2026-09-21) splits operands
  into base-13 limbs so that an fp4 tensor core carries them — a limb-splitting scheme whose error
  and cost are exactly computable, which is what makes an exact law testable now.

### Six Heilmeier answers

1. **Problem**: For a numerical kernel of size `n` at problem conditioning `kappa`, evaluated at a
   format with unit roundoff `u` and `K` emulation limbs, which target relative accuracies `eps` are
   **reachable**, where does adding limbs stop paying, and where does a wider format or a
   reformulation beat both? (Falsifiable: a law predicts `E(n,K,u,kappa)` and locates `K*` and `eps*`.)
2. **Current approaches & limitations**: mixed precision is domain-driven — each paper does its own
   kernel's error analysis (2609.24509 DEIM-CUR) or learns a per-family selector (2601.00728 RL
   bandit; 2504.14268 RL-CG); surveys catalogue formats and energy (2609.37137) but state no boundary.
   Hand rules ("use fp32 when in doubt", "bf16 is fine") carry no reachability statement, and a
   learned selector cannot say *a priori* whether a target is attainable at all.
3. **Novelty**: the **precision floor** (a reachability limit set by accumulation, not truncation),
   the **reachable-accuracy boundary** `eps*(format, n, kappa)`, and the first comparison of a
   closed-form rule against a learned selector on the same accuracy-budget task.
4. **Who cares**: numerical library authors (BLAS/LAPACK, PETSc) choosing per-kernel precision;
   format/hardware architects (the fp8/fp4 design axis); ML-systems engineers who must decide whether
   to buy accuracy with limbs, a wider format, or a residual iteration.
5. **Success metrics**: `E` predictions within a stated factor of the exact error over all cells
   (mean ± CI over seeds); the floor and `K*` identified and their scaling laws fitted (log-log slope
   with CI); `eps*` located and shown sharp; the closed-form `Gamma`-rule's decision agreement with a
   bandit selector, and the fraction of the selector's tuning cost it needs.
6. **Risks & fallback**: the honest risk is that truncation dominates everywhere in the tested regime
   and **no floor exists** — then the contribution is the *absence* of the floor plus the fitted
   truncation law and the selector comparison, which is still a falsifiable result against **P1**.
   Second risk: the energy axis needs hardware numbers; the law is therefore stated in
   format-level product counts (fully controlled), with the energy mapping as a stated model
   parameter rather than a measurement.

### Prior beliefs (registered before the deciding runs)

- **P1 (the floor exists)**: the error of a limb-split kernel falls with `K` and then **floors** at a
  value set by accumulation roundoff, `~ n * u_accum * kappa`, so beyond `K*` extra limbs buy no
  accuracy. *Justification*: the truncated cross-terms decay as `u^K` while the running sum's own
  rounding grows as `n*u`; a floor follows whenever `n*u` is not negligible against `u^K`, which is a
  statement about two known scalings, not a guess. *Direction*: error decreases then plateaus.
- **P2 (a single governing scalar)**: up to the floor, the admission boundary is **sharp in the
  effective roundoff** `Gamma = n^alpha * u * kappa` — i.e. two problems with equal `Gamma` but
  different `(n, u, kappa)` admit the same accuracy. *Justification*: the standard backward-error
  analysis of a dot product/matmul is `~ n*u*kappa` (Higham's `gamma_n`); sharpness is the part that
  is genuinely uncertain and is what we test.
- **P3 (closed form beats learned)**: a closed-form `Gamma`-rule matches a learned selector's
  decisions at a small fraction of its tuning cost, and the selector's residual mistakes concentrate
  where `Gamma` sits within a constant factor of its boundary. *Justification*: if `Gamma` is the
  sufficient statistic (P2), then a selector trained per family must be rediscovering a function of
  `Gamma`, so its errors should be near the boundary where the signal is weakest.

### Adversarial checks

- **Reverse gap**: why has nobody done this? Mixed-precision research is domain-driven (a kernel or a
  family per paper), the Ozaki/Zintra cost is treated as known folklore, and energy is measured
  per-machine rather than as a law — so the *reachability* question falls between the measurement
  papers and the autotuning papers. A plausible reason it was skipped, not a proof it is empty.
- **Evidence pre-assessment**: ground truth is **by construction** — limb splits of integer-valued
  operands make every intermediate an exact integer, so the exact result is computable and the error
  is measured, not modelled; cells span many `(n, kappa, format, K)` combinations; a pinned real matrix
  supply with measured condition numbers grounds the synthetic sweep; a bandit selector is
  implementable at toy scale. This is not a single-anecdote setup.
- **Upgradability**: the same instrument extends to matmul, dot products, and a residual-iteration
  arm (a reformulation the boundary is defined against); the theory model upgrades the empirical floor
  into a closed form; the selector comparison is a reusable instrument. A case-report framing is
  explicitly avoided.

### Contribution-level declaration (target)

`theory+empirics`: an exactly computable error surface with a derived law (the `Gamma` scalar and the
floor), validated by measurement against exact arithmetic across many cells, with a real-data
grounding arm and a selector comparison as the baseline.

### Note for the editor

No permission or infrastructure needs; the instruments are CPU-only and deterministic (seeded).
Research work will live in this issue's own `papers/issue-<N>/research/` (git-ignored), with the
committed package added at submission.


---

## Results log (appended each round; the source of truth is the instrument + its artefact)

### R537 — `spike_v0.py`: the precision floor (limb-split dot product vs exact arithmetic)

- The relative error falls `2^{-qK}` with the limb count and then **FLOORS at ≈ c·kappa1·u**
  (c ≈ 0.14–0.5; bf16 3.46e-2, fp16 2.94e-3, fp32 4.82e-7 at kappa1 ≈ 19–42), `K* ≈ 3–4 ≈ log2(1/u)/q`,
  with a FLAT tail past `K*` and a mild interior optimum (bf16 rises from K*=3 to K=4).
- **Reading: limbs cannot rescue a too-narrow accumulator** — the floor is set by the register.
- Artefact `spike_v0_results.json` sha256 `9564acf4…`; `--selftest` ALL PLANTS CAUGHT.

### R538 — `spike_v1.py`: the accumulator-bits law

- `E/kappa1 = c·2^{-p}` with **c ≈ 0.2**, and c is **independent of n** (slope −0.010 over 64×,
  n=50…3200) and of the conditioning (that is what kappa1 normalisation buys).
- **`p*(eps) = ceil(log2(c/eps))`**: measured vs predicted within **1 bit** over 333× in eps;
  slope of p* against log2(1/eps) = **1.009**.
- **Refuted this round's own guess**: a `sqrt(M)` (M = K·n additions) correction would give slope +0.5
  in n and p* growing with n; measured −0.010 and ≤1 bit over 16× → **n-independent**, confirming the
  originally-registered claim that `p*` does not depend on `K, q, n`.
- **Weakness**: the kappa1 collapse is only to ~4.5×, so "one governing scalar" (P2) is approximate.
- Artefact `spike_v1_results.json` sha256 `562ffdf2…`; `--selftest` ALL PLANTS CAUGHT.

### Priors against evidence (so far)

- **P1 (a floor exists)** — CONFIRMED (spike_v0).
- **P2 (a single governing scalar)** — CONFIRMED APPROXIMATELY: `E/kappa1` collapses to ~4.5×, not to
  a point; the sharpness part of P2 is not yet met.
- **P3 (closed form beats learned)** — NOT YET TESTED (the bandit baseline is owed).
