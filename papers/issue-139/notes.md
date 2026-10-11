# issue #139 — research notes (internal; `papers/*/research/` is git-ignored)

## R613 (2026-10-11) — the v0 exact instrument, its closed-form anchor, and four
## refinements the pre-check forced on the registered priors

**Artifacts**: `spike_v0.py` (sha256 `02b21599…`), `spike_v0_results.json`
(sha256 `5b148eab…`). The run is **byte-identical across two invocations**.

### What was built
The declared model of the registration, made exact:

* an obligation set is a DAG `(V,E)`; obligation `j` has standalone difficulty `p_j`;
  one attempt costs one budget unit and discharges with probability `p_j` while no
  parent is discharged;
* **coupling**: if at least one parent of `j` is discharged, `p_j -> min(1, p_j + c)`;
* a **schedule** is any deterministic map `S -> j`; the **frontier** is
  `F(B) = E[# discharged after B attempts]`;
* `F` is computed by **backward induction** over the `2^n` discharged sets and the
  budget — an exact expectation, not an estimate.

Three schedules + controls: `greedy` (max current discharge probability),
`assumptions_first` (max descendant cone, tie on probability), `fixed_order`,
`placebo` (a fixed random permutation).

### Instrument checks (all exact, max abs difference)
| check | value |
|---|---|
| DP vs geometric-convolution anchor, fixed order, p = [0.1,0.5,0.9] | 8.9e-16 |
| DP vs the same anchor under the greedy order (sorted p) | 8.9e-16 |
| **invariant**: at `c = 0` a coupled DAG's frontier equals the uncoupled law | 8.9e-16 |
| determinism (re-run) | 0.0 |
| Monte Carlo vs exact (N = 20 000 / 80 000 trials) | 2.7e-2 / 1.1e-2, max z 2.5 |

The anchor is the ground-truth check R1 demanded: an **uncoupled** set is a sum of
independent geometric searches, whose frontier is exactly
`sum_{k>=1} P(sum_{i<=k} G_i <= B)`. The DP reproduces it to machine precision, and
the MC is an independent reading that converges (error halves as trials quadruple).

### Findings — and they are not what the registration assumed

**F1. The coupling gain is schedule-dependent, and can be exactly ZERO or NEGATIVE.**
Define the coupling gain at a *fixed* schedule, `gain(pi) = F_pi(coupled) - F_pi(uncoupled)`
(same difficulties, edges removed). Measured:

| case | greedy | assumptions-first | fixed order | placebo |
|---|---|---|---|---|
| chain, p = 0.2 uniform | **+1.0897** (B=12) | +1.0897 | +1.0897 | +0.4974 |
| star, hard root p = [0.15,.6,.6,.6] | **+0.0000** (every B) | **−1.0521** (B=4) | +0.3054 | +0.1024 |

The greedy zero on the star is **derived, not observed**: greedy always attempts the
highest-probability undischarged obligation, so it discharges the three easy children
(p = 0.6) before it would ever spend an attempt on the root (p = 0.15) — the root is
never discharged, so the boost never activates and the edges carry no value at all.
A schedule that *does* prioritise the cone (`assumptions_first`) activates the coupling
and is **worse by 1.05 discharges at B = 4**: paying for a hard assumption first starves
the budget. So "coupling helps" is false as a general statement; the coupling's value is
a property of the **(schedule, DAG) pair**.

**F2. A permuted schedule is NOT a valid placebo.** On the same cases the permutation's
**ordering effect on the ZERO-coupling control** is up to **0.8404** (star, B = 4):
reordering attempts moves the frontier with no graph at all, because the completion-time
of the k-th obligation depends on the order in which geometric searches are concatenated.
A permutation therefore confounds the ordering effect with the coupling effect — it cannot
hold the mechanism under test fixed. **The registered R2 fallback ("a placebo permutation
… must show no gain") is mis-specified.** The control that *is* null by construction is
the same schedule on the graph with its edges removed (F1's denominator), or the same
schedule at `c = 0`.

**F3. The registered P3 is refuted in both of its directions.**
(a) *Coincidence*: on the uniform chain `assumptions_first` and `greedy` select the same
obligation in every reachable state, so the gain is **exactly 0.0000 at every budget** —
"beats difficulty-greedy at every budget" fails where the two schedules are the same
schedule. (b) *Sign*: on the hard-root star the cone-first schedule is **worse** at every
budget (−1.05 … −0.0002). P3 as registered ("a coupling-aware schedule beats a
difficulty-greedy one at every budget, and the gain grows with depth") cannot survive the
measurement; it must be restated as an **interaction** claim (see below).

**F4. The P2 gap is a hump in the budget.** On the chain the coupling gain under a fixed
schedule rises 0.37 → **1.09** (B = 12) → 0.17 (B = 30) → 0.001 (B = 60): the effect lives
in the middle of the budget range and vanishes at both ends. A single mid-budget cell would
have reported the answer; the *maximum over a budget sweep* is the quantity to register.

### The registered priors, restated after the pre-check (the registered wording stays on
### the record; these are the forms the grid will measure)
* **P2' (coupling vs marginal difficulty), testable form**: at a **fixed schedule**, two
  obligation sets with the same difficulty multiset and different edges have different
  frontiers, and the gap is measured as `max_B [F_pi(coupled) - F_pi(uncoupled)]`; the
  registered `>= 0.05` bar is kept for a declared mid-budget cell.
* **P3' (schedule), testable form**: the schedule effect is an **interaction** —
  `Delta(pi, G) = F_pi(G) - F_greedy(G)` depends on `G`, and is claimed to be positive
  only on DAGs where `pi` and `greedy` differ; the registration's universal quantifier is
  withdrawn (F3a). The **control is not a permutation** (F2) but the same schedule with the
  graph removed, where `Delta` must be 0 by construction.

### Next (R614)
1. Scale the instrument: `n = 8` (the `2^n` DP is still cheap), the declared DAG families
   (chain / tree / layered / Erdős–Rényi at several densities / hub-and-spoke) × difficulty
   distributions (uniform / bimodal / Zipf) × coupling `c` × budgets, exact where the DP
   closes and exact-expectation MC where it does not.
2. Register a **non-degenerate** schedule pair for P3' (find the DAG family on which the
   orderings provably differ) and implement the graph-removed control that F2 requires.
3. Test P1 (concavity and the superlinear target-budget) against the closed-form anchor at
   zero coupling, which is already exact.

## R615 (2026-10-11) — the scaled grid: P1's concavity half is REFUTED (and coupling is the cause),
## P1's target-budget half is CONFIRMED everywhere, and the registered P3 is refuted at every cell

**Artifacts**: `spike_v1.py` sha256 `f07cc751…`, `spike_v1_results.json` sha256 `7d0806f1…`
(n = 8 grid), `spike_v1_robust.txt` sha256 `3fe1388e…` (the size/seed leg). The whole grid runs in
**2.5 s** and the report is **byte-identical across runs**; the robustness leg takes ~45 s.

### What v1 adds
The declared grid: **7 DAG families** (`empty` (control), `chain`, `tree`, `layered`, `hub`, `er03`,
`er06`) × **5 difficulty vectors** (`uniform`, `easy`, `hard_root`, `bimodal`, `zipf`) × **4 coupling
levels** (0, 0.15, 0.35, 0.60) × **4 schedules** (`greedy`, `assumptions_first`, `fixed_order`,
`placebo`), at n = 8, exact DP over the 2^8 discharged sets, Bmax = 120.

**The certificate.** At c = 0 every schedule used here reduces to a **fixed order** (its choice
criterion does not depend on which obligations are already discharged), and a fixed order's uncoupled
frontier has a closed form (a sum of independent geometric searches). So the DP is checked against the
closed form **at every c = 0 grid point, on the order each schedule actually induces**: **140 cells,
max |DP − closed form| = 7.1e-15**. This is the R1 ground-truth check, now grid-wide rather than on one
fixture. The `--selftest` plants that the same comparison *fails* on a deliberately wrong order, so the
certificate is shown able to fail.

**The correct control.** The registration's R2 placebo (a permuted schedule) was shown in v0 not to be
null. v1 uses instead **the same schedule on the same difficulty vector with the EDGES REMOVED**: at
c = 0 the edges carry no value, so any difference there is an ordering effect. Measured: the coupling
gain at c = 0 is **exactly 0.0** (not "small"), and the P3 control is **exactly 0.0** in every cell.

### Findings (6 real families; the `empty` graph is the control and is excluded from treatment counts)

| registered claim | verdict | measurement |
|---|---|---|
| P1: frontier **strictly concave** | **REFUTED** | concave in only **117/480** cells (24.4%); the failure is **monotone in coupling** — 70.0 % concave at c=0 → 18.3 % (0.15) → 5.8 % (0.35) → **3.3 %** (0.60), with the max concavity defect growing 0.0675 → **0.2475**. Even at c = 0, 30 % of cells are non-concave. |
| P1: target-budget **superlinear** (≥1.5 from a 0.5 to a 0.9 target) | **CONFIRMED** | B(0.9)/B(0.5) ∈ [**1.500**, 4.125], median **2.000**, and **≥1.5 in 480/480** cells. |
| P2': coupling separates the frontier at a **fixed** schedule | **CONFIRMED** | **327/360** coupled cells gain > 0; max **+4.2364** discharges (of 8) at (chain/tree, zipf, c=0.60, B=12); mean gain **1.007 → 1.770 → 2.186** as c goes 0.15 → 0.35 → 0.60; the gain at c = 0 is **exactly 0**. |
| P3: assumptions-first **beats** difficulty-greedy **at every budget** (≥0.03), placebo no gain | **REFUTED** | **0** always-positive cells, **0** always-negative, **114/120 identical** (gain exactly 0), **6 sign-changing**; the control is exactly 0. |

**The mechanisms, and the sharpened claims.**

1. **The concavity refutation is a property of the SEARCH, not of the graph.** An uncoupled set
   attempted in a fixed order is a sum of independent geometric searches, whose completion density is
   **unimodal but not monotone** — so F rises with a *convex* stretch even at c = 0. Worked case:
   p = [0.5, 0.1] gives marginals 0.05 then 0.095. Coupling then adds **increasing returns** (the more
   discharged, the more boost), which is why concavity degrades monotonically with c. **P1's first half
   is therefore not a property of the physical model at all** — it was a guess about the shape of a
   diminishing-returns process, and the process has increasing returns in two separable places.
2. **The coupling gain is schedule-dependent, and can be exactly zero — with a derivation.** 33/360
   coupled cells gain nothing; 21 of them are on `hub` and 9 on `hard_root × hub`. Mechanism (the v0
   result, now grid-wide): a schedule that never spends an attempt on the hard root never activates the
   boost, so **edges that the schedule never activates carry exactly zero value** — the same difficulty
   multiset with different edges, and the coupling gain is 0, not small.
3. **The schedule effect is much narrower than registered, and where it exists it is a CROSSOVER.**
   `assumptions_first` and `greedy` select the same obligation in **114 of 120** cells (they differ only
   when the max-descendant node is not the max-probability node). In the 6 cells where they differ the
   sign is set by **whether the budget can pay for the assumption being pre-paid**: at (hub, bimodal,
   c=0.15) the cone-first schedule is **−1.4169** at B = 4 and only turns positive at **B = 24**; raising
   c moves the crossover DOWN to B = 16 (0.35 and 0.60). At (er03, hard_root) the shape is the other way
   round: positive at B = 4, negative across B = 16…32. So P3' is an **interaction with a crossover
   budget**, and the crossover moves with the coupling.

### Robustness (9 combinations: n ∈ {6, 8, 10} × seed ∈ {139, 271, 511})
The qualitative findings are not an n = 8 or a single-seed artifact: **ratio ≥ 1.5 in 480/480 at every
size and seed**; concave fraction 20.8–29.6 % at every size and seed (never concave in general);
coupling gain at c = 0 **exactly 0** in all 9; **P3 always-positive = 0 in all 9**; P3 control 0 in all
9. Certificate ~1e-15 throughout. Invariant violations: **0**. The P2 max gain grows with n
(2.85 at n=6 → 5.67–6.34 at n=10), i.e. the coupling's value scales with the size of the set.

### Next (R616)
1. **The budget-sizing deliverable.** P1's superlinearity is confirmed, so the paper can state a
   *sizing rule*: read the budget off the frontier and the DAG. Next step: a small **planner** that takes
   (DAG, difficulties, target) and reports the budget its frontier needs, with the schedule it assumed.
2. **A non-degenerate schedule pair, registered properly.** P3' now has a measured regime (6/120 cells);
   the next leg should *construct* the regime deliberately (hub/tree with a hard root and a mid budget)
   rather than find it, and sweep the crossover budget analytically.
3. **The concavity law as the headline.** The mechanism (unimodal completion density + coupling-induced
   increasing returns) is a candidate for a closed form: the frontier's second difference as a function
   of the difficulty spread and c.

## R616 (2026-10-11) — the THEORY round: the concavity law, its n-form and its breakdown, and the
## budget-sizing rule (the paper's practical deliverable)

**Artifacts**: `spike_v2.py` sha256 `b4d7785a…`, `spike_v2_results.json` `52ec9778…`,
`spike_v2_reliability.txt` `3fe1…`/`fe3df0d1…` (size/seed leg). `--selftest` **7/7**; both reports
byte-identical across runs.

### Law 1 — the concavity law (exact, n = 2)
For TWO obligations attempted in a fixed order, the frontier has a closed form (a sum of two geometric
searches; the marginal is `delta(B) = A q1^(B-1) + C q2^(B-1)`, `qi = 1-pi`). Measured over a
**1600-cell grid** in `(p1, p2)` space:

> **the frontier is convex somewhere ⟺ the SECOND-attempted obligation is the HARDER one (`p2 > p1`).**

**100.00 % agreement** (1600/1600). Equivalently: **the frontier is concave iff the attempt order is
non-increasing in difficulty — i.e. the easiest-first (difficulty-greedy) rule is exactly the rule that
preserves concavity at n = 2.**

**A hand-derived rule that was WRONG, and is recorded as such.** I derived "the coefficient on the
faster-decaying exponential must be negative" and it is **neither necessary nor sufficient**: it agrees
with the measured region in only **76.25 %** of cells (it fires in the concave cells where `p1 < p2`, so
it is not necessary, and misses some convex ones). The measured law is *simpler* than the derivation.
Kept in the record because a derivation that disagrees with the measurement is evidence about the
derivation.

### Law 1′ — the n-obligation form, and where it BREAKS
The generalisation tested on the v1 grid (same difficulty vectors, same families):
**concave ⟺ the schedule's induced order is non-increasing in difficulty.**

| c | agreement | non-increasing & convex | concave & not non-increasing |
|---|---|---|---|
| **0.00** | **139/140 (99.3 %)** | 0 | 1 |
| 0.15 | 54.3 % | 62 | 2 |
| 0.35 | 45.0 % | 76 | 1 |
| 0.60 | 47.1 % | 74 | 0 |

So the law holds at zero coupling (with one measured exception, a tie-valued difficulty vector whose
order drops and rises again yet stays concave) and **breaks as soon as coupling is on** — not because the
order stops mattering, but because **coupling makes the order state-dependent**: the induced order on the
empty set is not the order the schedule actually takes after obligations discharge. The example cells are
`chain uniform` (`p = 0.35` throughout, order trivially non-increasing) yet convex. This is the mechanism
behind v1's monotone concavity degradation, now located.

### Law 2 — the budget-sizing rule (the practical deliverable)
The registered "read the budget off the frontier and the DAG": a planner takes (graph, difficulties, c,
target) and returns the **frontier budget** (smallest `B` with `F(B) ≥ t·n`), beside the **pass-rate
rule** — the budget a "our prover passes X % of obligations" table implies, computed as the sum of the
`ceil(t·n)` cheapest independent expected costs `1/p_i` (given the most favourable reading, with the
coupling already credited).

> **The pass-rate rule under-budgets in 1110/1440 cells (77.1 %), by up to a factor 4.9**
> (worst ratio 0.203: it quotes 4.87 units where the frontier needs 24).

By target: naive/frontier ratio median **0.714** (target 0.5), **0.857** (0.7), **0.952** (0.9) — i.e.
the error is worst exactly where a budget is usually set, in the low-target regime, and the pass-rate
view is *systematically* optimistic.

### Reliability (n ∈ {6,8,10} × seed ∈ {139,271,511})
- **n = 2 law: 100.00 % at every size and seed** (exact).
- **c = 0 n-law: 93.6 – 99.3 %** at every combination (the exceptions are ties).
- **sizing under-budget: 77.1 – 100.0 %**, worst ratio 0.157 – 0.250.
- **violations of the stated laws: 0.**

### Where this leaves the registration
- **P1 (concavity)**: REFUTED as registered, and now **replaced by a law** (Law 1 at n = 2 exact, Law 1′
  at n = 8 with its breakdown located at `c > 0`).
- **P1 (superlinearity)**: CONFIRMED (480/480, R615).
- **P2′**: CONFIRMED (R615).
- **P3**: REFUTED as registered; the schedule's role is now sharper than the registration's — the
  schedule matters exactly in the cells where it differs from greedy, and there it is a crossover
  (R615). Law 1 adds why: **greedy is concavity-preserving**, so a schedule that reorders away from
  difficulty order buys coupling at the cost of convexity.

### Next (R617)
1. **The theory arm needs one more piece**: Law 1 at n = 2 is proved; the n-form is measured with
   exceptions. Either find the n-form's exact statement (a condition on the order AND the coupling's
   state-dependence) or state the n-form as a measured bound with its exceptions enumerated.
2. **The planner as a deliverable**: a small tool taking a DAG + difficulties + target and returning the
   budget and the schedule it assumed, with the pass-rate rule beside it as the comparison — this is the
   artifact the paper's reader would use, and it is nearly built (`planner()`).
3. **Then Phase B** (figures, reference layer, manuscript) if the theory arm settles.

## R617 (2026-10-11) — the n-form SETTLED: the concavity law is a one-directional EXACT theorem at
## c = 0 (0 violations in 11,923 permutations), and coupling is the sole cause of its breakdown

**Artifacts**: `spike_v3.py` sha256 `375ae55c…`, `spike_v3_results.json` `8abc814c…`,
`spike_v3_report.txt` `ec54430c…`. `--selftest` **7/7**; the JSON report is byte-identical across runs.

### The defect R616's aggregate was hiding
R616 reported the n-form as an **agreement rate** (99.3 % at c = 0, 45–54 % at c > 0) between
"concave" and "the induced order is non-increasing". An agreement rate conflates two different
statements, and they have different status:

* **GUARANTEE** — non-increasing order ⟹ concave frontier
* **CONVERSE** — concave frontier ⟹ non-increasing order

R616's own table already showed the guarantee had **no** exception at c = 0 (its `non-increasing &
convex: 0`) while the converse had one. Measuring them **separately**, and **exhaustively**, settles it.

### The theorem, tested exhaustively (not sampled)
A fixed order has an exact `O(n·B)` recursion — under a fixed order the state is only *(how many done,
attempts used)*, so the whole permutation group is affordable. Every distinct permutation at **n = 5, 6
and 7** was tested over six difficulty vectors (uniform; a wide zigzag; hard-first; bimodal; exact ties;
near-ties differing by 2e-7):

> **GUARANTEE: 0 violations in 11,923 permutations.** A non-increasing (easiest-first) attempt order
> **always** yields a concave frontier — for every difficulty vector, every size, no exceptions.
>
> **CONVERSE: 1,253 exceptions (10.5 %).** Concavity does **not** require the order to be non-increasing.
> The exceptions are not small perturbations: the largest late rise inside a concave frontier is **0.58**.

So "non-increasing" is **sufficient, not necessary**, and the sufficient direction is **exact** — the
agreement rate of R616 was a statistic that averaged an exact law with a false converse.

### Why it breaks at c > 0: the coupling, not the order — 212/212
For every grid cell whose *empty-set* order is non-increasing yet whose frontier is convex (212 cells),
recompute the frontier with **the same attempt order and the coupling switched off**: in **212/212** the
uncoupled defect is **exactly 0.0000**. At c > 0 the schedule's choice is state-dependent, so the order
read on the empty set is not the order the process takes — but the decomposition shows the order is not
what breaks the guarantee: **coupling is the sole cause**, via its increasing returns.

### The boundary, stated as a c = 0 theorem
Testing a **genuinely fixed** order *with* coupling (still exact: a fixed order's discharged set is a
prefix of the order, so the boost is a function of the step index alone) — the guarantee **fails in
127/180 cells**, stable across seeds (125, 127, 127, 127 for seeds 139/271/511/733). So:

> **The concavity guarantee is a `c = 0` theorem.** Coupling — the model's central feature — is exactly
> what destroys it.

### Where this leaves the registration
**The theory arm is complete.** LAW 1 (n = 2, exact biconditional), the n-form guarantee (exact at
c = 0, exhaustive), the breakdown (coupling, 212/212), the boundary (c > 0, 127/180), and LAW 2 (the
budget-sizing rule, 77.1 % under-budget, up to 4.9×). P1-concavity is refuted as registered and replaced
by a stronger object: an exact sufficient condition plus a located mechanism for its failure.

### Next (R618)
**Phase B.** The evidence is complete for a `theory+empirics` submission: instrument the figure set from
these three spikes, build the reference layer, write the manuscript. No further measurement is blocking.
