## 3. The instrument

### 3.1 Generator, ground truth, and the units of every number

Data are the full hypercube: `z ∈ {0,1}^q` uniform, so a cell at q = 6 has 64 points and a cell at q = 8 has
256. The feature map is the ZZ map applied at the *angle vector* `x = γ·z`, so that γ is the bandwidth axis and
γ → 0 is the small-bandwidth regime the closed-form reduction [19] is stated for. The circuit is
`|φ(x)⟩ = (H U(x))^L H^q |0⟩` with `U(x) = diag_z exp(iθ(x,z))` and
`θ(x,z) = Σ_i 2 x_i z_i + Σ_(i,j)∈E 2 g(x_i,x_j) z_i z_j`, where `g = (π−x_i)(π−x_j)` under the *shifted*
convention and `g = x_i x_j` under the *unshifted* one; L = 2 layers, which is where the metric is a field
rather than a function of the graph alone. The kernel is the exact fidelity `K(x,x') = |⟨φ(x)|φ(x')⟩|²`,
computed by statevector simulation: no sampling, no noise model, no hardware, no clock.

The target is a pure interaction function, `y = zᵀ A z + ε`, with `ε ~ N(0, σ²)` and σ = 0.30 · sd(f). The
interaction matrix is planted with its Frobenius alignment to the graph's own interaction structure swept **by
construction**:

```
A(α) = α · Q̂_int + sqrt(1 − α²) · R_perp
```

where `Q̂_int` is the unit-Frobenius off-diagonal part of the signless Laplacian Q of the entanglement graph and
`R_perp` is a random symmetric zero-diagonal matrix with its Q-component projected out, so `cos_F(A, Q_int) = α`
holds algebraically and is *measured* as a control rather than trusted (C1 reads its worst deviation as
2.2e−16). The graph is a cycle at the study's main stratum, with a path and the complete graph as the other two
strata.

Ground truth is by construction: the Bayes predictor *is* f, and every reported error is the **excess risk over
the Bayes predictor on the same test set, in units of the target's variance**,

```
excess(pred) = (MSE_test(pred) − MSE_test(f)) / Var(f),
```

so a predictor at the Bayes risk scores 0, and the constant predictor scores ≈ 1. An earlier version of the
instrument read excess against the *declared* σ² and reported a *negative* excess for a near-Bayes predictor,
because the realized test noise differs from its expectation; the digest's values are all read against the
oracle predictor on the same test set. Each cell averages 6 independent target draws × 50 resampled
train/test splits (the ladder and the fallback instrument) or 5 disjoint streams × 40 splits (the panel), and
a split trains on half the points.

### 3.2 The arms

Every arm is a kernel ridge predictor sharing one protocol: the same training half, the same nested tuning over
the envelope grid `s ∈ {0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10}` and the ridge grid `λ ∈ {1e−5 … 1}`, selected on
the training half only. Two things this sentence used to paper over are now stated, because a fixed
hyperparameter on one arm converts that hyperparameter into part of the finding: the arms whose kernel is a
*family* are `matched`, `closedform`, `rbf`, `randfeat` and `matchedlocal`, and the arms whose kernel is fixed by
construction are `quantum`, `product`, `linear` and `oracle` — the map fixes its own kernel, and the last two have
no envelope to tune. The local arm's envelope was left at 1 in the instrument of record, a handicap larger than
the effect under study; it is swept here like every other family, and §7 item 1 reports the measurement.

| arm | kernel | role |
|-----|--------|------|
| `quantum` | the exact ZZ fidelity kernel | the arm under test |
| `matched` | Mahalanobis Gaussian with precision = the map's own metric (mean over data of the exact per-point state-derivative metric `2g`) | **the metric-matched rival — the comparison this paper is about** |
| `closedform` | the same shape with the metric the 2026 closed form hands a practitioner: an affine function of the graph, `k₀ I + k₁ Q`, no simulation | is the closed form as good as the fitted metric? |
| `rbf` | isotropic Gaussian on Hamming distance | the family baseline the field compares against |
| `randfeat` | random-projection Gaussian with a wide envelope | the weak surrogate the field's residual advantages are measured against [1, 87] |
| `product` | the same quantum map with the edge set emptied, at matched q | isolates entanglement from encoding |
| `oracle` | the Gram matrix of the target's own span `[1, z_i, z_i z_j]` | must be the best predictor in every cell (C3) |
| `linear` | `zᵀz'` | the "no geometry at all" floor |

The metric handed to `matched` is a *field*: the per-point metric varies over the data set, so a global rival is
matched at most at the mean. The spread of that field is measured in every cell (it grows from 1.14 to 6.18
across the bandwidth grid in the study's first instrument) and is reported as a limitation rather than hidden —
it is the reason the matched rival is a *proxy* for the map's geometry, not the geometry itself.

### 3.3 Reproduction

The package recomputes everything from committed scripts: the instrument's own JSONs are the digest's inputs,
the digest owns every number the text prints, and the figures are drawn from the digest. `README.md` states the
one command, the environment, the expected output and the tolerance.

## 4. The design, and the controls that could have failed

**Table 1 — the design.**

| axis | values |
|------|--------|
| qubit count q | 6, 8 |
| layers L | 2 |
| data | the full hypercube (64 points at q = 6; 256 at q = 8), uniform |
| graph | cycle (main stratum), path, complete |
| bandwidth γ | 0.1, 0.25, 0.5, 1, 2, 3 (γ = 0 is degenerate by measurement) |
| phase convention | shifted, unshifted |
| planted alignment α | +1, −1 (the map and the panel); α ∈ {+1, 0, −1} in the alignment instrument |
| label noise | σ = 0.30 · sd(f) |
| draws | 6 target draws × 50 splits per cell (ladder, fallback); 5 disjoint streams × 40 splits (panel) |
| envelope / ridge grid | s ∈ {0.003 … 10}; λ ∈ {1e−5 … 1}, nested selection on the training half |
| cells | 24 (2 conventions × 6 bandwidths × 2 alignment signs) |

**Table 2 — the controls, each of which could have failed.** A control that cannot fail is decoration, so each
is listed with the read that decides it.

| control | what it reads | value |
|---------|---------------|-------|
| alignment identity (C1) | worst deviation of the measured `cos_F(A, Q_int)` from the planted α | 2.2e−16 (algebraic) |
| support (C2) | at α = ±1 the off-diagonal support of A is exactly the edge set | true (α = 0 false, as constructed) |
| oracle (C3) | the target's own span is the best predictor in every cell | true; the Bayes risk through the code path reads exactly 0.0 |
| null (C4) | a signal-free cell must not manufacture an advantage | aligned-cell max advantage 0.0740 vs null-cell max 0.0567 — the null does not exceed it |
| γ → 0 (C5) | at γ = 0 the kernel is identically 1 (rank 1) | max deviation from 1: 4.4e−16 |
| determinism (C6) | the report rebuilt byte-for-byte | identical at q = 6, q = 8, and on the path stratum |
| cross-harness reproduction (C7) | the second graph's harness re-derives the first graph's 24 × 24 committed cells | 576 of 576 exact, max |Δ| 0.0 |
| panel C2 | the panel's harness re-derives the committed q = 8 record | 8 of 8 values identical, 0 mismatches |
| panel C3 | the sign-unanimity instrument fires | clean 5/5 → a planted one-entry flip reads 4/5 |
| panel C4 | the paired-effect instrument fires | an injected −0.10 is returned to 1e−12 and flagged resolvable; a zero-effect panel is *not* resolvable |
| panel C5a/C5b | the five streams are disjoint and actually differ | seed ranges disjoint by arithmetic (offset 51 146 < stride 110 000); spread inside the structure cells 0.0337 |

Two of these controls changed the study's design rather than merely clearing it. The oracle control caught an
instrument defect (a badly specified oracle, λ ≈ 0 on 22 features over 32 training points, that overfitted its way
below several kernels), and the cross-harness control caught a metric copied without its bandwidth argument.
Both are recorded in the package's round notes with the repairs applied.

## 5. Results

### 5.1 The map's metric is scale-uniform exactly where the graph is symmetric

The statistic that locates the region is not fitted: it is the relative deviation of the metric's diagonal from
uniformity. On a vertex-transitive graph every vertex has the same degree and the same neighbourhood structure,
and `diag(W)` is uniform to machine precision — a max relative deviation of **8.2e−16** on the cycle and
**4.8e−16** on the complete graph at q = 6, and **1.7e−15** / **1.9e−15** at q = 8. On a **path** the symmetry is
broken and the same statistic reads **6.1e−1** at q = 6 and **6.4e−1** at q = 8 — twelve orders of magnitude
above the vertex-transitive value, and stable across qubit counts.

**What that is evidence for, stated exactly.** The record holds **two poles, not a boundary curve**: three
graphs, two of them vertex-transitive and one not, with nothing measured between them. The statistic is therefore
a **two-case classification** — vertex-transitive (≈ 1e−15, and it is exact there rather than threshold-fitted)
versus not (6.1e−1) — and "the map's boundary is a computable statistic" is a statement about those two cases,
not about a location in graph space. The experiment that would give it a resolution is the **cycle-with-k-chords**
family: `k = 0` and `k = q` are the two poles already measured, and a sweep over `k` would say whether the
deviation moves continuously with the symmetry deficit or jumps. That sweep is not run here; §7 item 3 records it
as future work.

![Fig. 3 — the map's metric is scale-uniform on vertex-transitive graphs and not on a path: the statistic that locates the region](figures/fig3_metric_structure.png)

This is the paper's one structural theorem-shaped statement, and it is why the registered power arm behaves the
way it does (§5.4): a handicap that flattens per-qubit scale is *exactly* the identity map on a
vertex-transitive graph, so the registration's own way of withholding geometry from the rival had no effect by
algebra rather than by measurement. The consequence for the map is that the region's location is a property of
the (graph, bandwidth, convention) triple that can be computed before any learning run happens.

### 5.2 The advantage map: a valley with two rims, and the registered shape is absent

Table 3 is the study's headline: the paired excess-risk difference (quantum − matched) per cell, as a
cross-stream mean with its sd over 5 disjoint streams, at both qubit counts. Positive means the entangling
kernel is **worse** than the rival that received its own geometry.

**Table 3 — the advantage map (excess risk, quantum − metric-matched rival).** `sd` is the cross-stream sd over
5 disjoint streams; `sgn` is the number of streams of 5 whose sign agrees with the mean.

| convention | γ | α | q = 6 mean | sd | sgn | q = 8 mean | sd | sgn |
|------------|-----|-----|-----------|------|-----|-----------|------|-----|
| shifted | 0.1 | +1 | −0.0173 | 0.0056 | 5/5 | +0.0100 | 0.0014 | 5/5 |
| shifted | 0.1 | −1 | −0.0169 | 0.0029 | 5/5 | +0.0102 | 0.0009 | 5/5 |
| shifted | 0.25 | +1 | +0.0861 | 0.0069 | 5/5 | +0.0663 | 0.0013 | 5/5 |
| shifted | 0.25 | −1 | +0.0847 | 0.0073 | 5/5 | +0.0661 | 0.0013 | 5/5 |
| shifted | 0.5 | +1 | **+0.4314** | 0.0104 | 5/5 | **+0.3366** | 0.0061 | 5/5 |
| shifted | 0.5 | −1 | **+0.4264** | 0.0133 | 5/5 | **+0.3370** | 0.0031 | 5/5 |
| shifted | 1 | +1 | **+0.4546** | 0.0120 | 5/5 | **+0.2791** | 0.0013 | 5/5 |
| shifted | 1 | −1 | **+0.4550** | 0.0109 | 5/5 | **+0.2785** | 0.0019 | 5/5 |
| shifted | 2 | +1 | +0.0238 | 0.0075 | 5/5 | +0.0316 | 0.0013 | 5/5 |
| shifted | 2 | −1 | +0.0271 | 0.0051 | 5/5 | +0.0316 | 0.0023 | 5/5 |
| shifted | 3 | +1 | −0.0523 | 0.0050 | 5/5 | −0.0143 | 0.0010 | 5/5 |
| shifted | 3 | −1 | −0.0552 | 0.0041 | 5/5 | −0.0139 | 0.0005 | 5/5 |
| unshifted | 0.1 | +1 | −0.0076 | 0.0034 | 5/5 | −0.0024 | 0.0003 | 5/5 |
| unshifted | 0.1 | −1 | −0.0087 | 0.0020 | 5/5 | −0.0021 | 0.0004 | 5/5 |
| unshifted | 0.25 | +1 | −0.0266 | 0.0032 | 5/5 | +0.0028 | 0.0006 | 5/5 |
| unshifted | 0.25 | −1 | −0.0283 | 0.0031 | 5/5 | +0.0028 | 0.0007 | 5/5 |
| unshifted | 0.5 | +1 | −0.0038 | 0.0050 | 4/5 | +0.0278 | 0.0016 | 5/5 |
| unshifted | 0.5 | −1 | −0.0044 | 0.0043 | 4/5 | +0.0277 | 0.0011 | 5/5 |
| unshifted | 1 | +1 | **+0.4158** | 0.0134 | 5/5 | **+0.3216** | 0.0057 | 5/5 |
| unshifted | 1 | −1 | **+0.4110** | 0.0102 | 5/5 | **+0.3216** | 0.0049 | 5/5 |
| unshifted | 2 | +1 | **+0.4402** | 0.0145 | 5/5 | **+0.2521** | 0.0062 | 5/5 |
| unshifted | 2 | −1 | **+0.4294** | 0.0128 | 5/5 | **+0.2533** | 0.0038 | 5/5 |
| unshifted | 3 | +1 | −0.0726 | 0.0023 | 5/5 | −0.0351 | 0.0011 | 5/5 |
| unshifted | 3 | −1 | −0.0632 | 0.0038 | 5/5 | −0.0352 | 0.0011 | 5/5 |

![Fig. 1 — the advantage map: paired difference in excess risk (quantum − metric-matched rival), mean ± sd over 5 disjoint stream draws per cell, with the mid-band block shaded](figures/fig1_advantage_map.png)

Three reads decide the study's claims.

**(i) The middle band is a loss, and it is the largest effect in the grid.** In the 8-cell block that spans the
bandwidth window 0.5–2 under both conventions and both alignment signs, the entangling kernel is worse than the
matched rival by **+0.4110 … +0.4550** at q = 6 and **+0.2521 … +0.3370** at q = 8, with **8 of 8 cells
sign-unanimous across all 5 streams** at both qubit counts (the only cells anywhere in the grid with a 4/5 read
are the two `unshifted|0.5` cells, which are *not* in the block). The cross-stream sd inside the block is at most
0.0145, against the smallest gap between the block and its neighbouring cells of 0.4110 — a ratio of roughly 30,
so the block's boundary is not a sampling artefact. As intervals rather than points, the eight q = 6 readings
carry 95 % t intervals (df = 4) whose lower bounds are **+0.3984, +0.3991, +0.4098, +0.4135, +0.4184, +0.4222,
+0.4396, +0.4414**: every lower bound is at least +0.398 of a target-variance below zero-difference.

**(ii) The only leads are the two rims, and they are an order of magnitude smaller.** Where the kernel does lead,
it leads by **0.0076 … 0.0726** — the small-bandwidth rim (γ = 0.1 under the shifted convention, 0.1–0.5 under
the unshifted one) and the collapse rim (γ = 3 under both). The largest lead anywhere, 0.0726, is a sixth of the
smallest mid-band loss. On the small-bandwidth rim the lead is real but tiny and it does **not** survive the
qubit count: at γ = 0.1 the shifted cells read −0.0173/−0.0169 at q = 6 and +0.0100/+0.0102 at q = 8, i.e. the
sign flips with q while remaining small in both. On the collapse rim the lead is convention-stable and
q-stable in sign (−0.0523/−0.0552 shifted and −0.0726/−0.0632 unshifted at q = 6; −0.0143/−0.0139 and
−0.0351/−0.0352 at q = 8, where the q = 8 kernel's aliveness has dropped in 12 of 12 bands and risen in none).
The registered reading of that rim — PB1's "advantage ≤ 0 at large bandwidth, where the kernel collapses" — is
therefore **refuted in direction**: the advantage is *positive* exactly where the kernel is dying, which is what
a collapsing pair of arms both converging on the trivial predictor would produce if the collapse is slower on
the quantum side than on the rival's.

**(iii) The registered shape does not appear at all.** The counts make this discrete and checkable. At q = 6 the
number of cells in which the kernel leads is 10, 12, 12, 12, 12 across the five streams (mean 11.6 of 24); at
q = 8 it is exactly 6 in all five streams, and the six-cell lead set is *identical* in every stream. So the map
is not "mostly empty with noise": it is a reproducible partition of the grid into a mid-band block that the
matched rival wins everywhere and two rims the kernel wins slightly — and the rims are where the field does not
make its claims.

**PB1 outcome.** The small-bandwidth clause (≈ 0) is the only one standing, and it stands as an approximation:
the largest small-bandwidth reading is 0.0173 against a mid-band loss of 0.4550, and under the unshifted
convention at q = 8 the same rim reads +0.0028, i.e. a small loss. The middle clause (advantage > 0 in an
intermediate band) is **refuted with the sign inverted** — the intermediate band is where the loss is largest.
The large-bandwidth clause (≤ 0) is **refuted in direction**, with the scope stated above: the positive lead
there is ≤ 0.0726 and shrinks by roughly a factor of 4 at q = 8. **PB3** — "under the identity-metric
convention the advantage region is empty at every alignment level" — is **refuted as written**: the collapse-rim
lead survives the convention change with its sign intact (−0.0726 shifted vs −0.0632 unshifted at q = 6), so the
rim lead is *not* the metric anisotropy that the convention removes; and the region is not empty under either
convention, it is merely different in sign from cell to cell.

### 5.3 The alignment axis: the sign moves, but opposite to the registration

The registration's PB2 predicts that the sign of the advantage is set by the alignment between the target's
interaction spectrum and Q. The panel's two alignment signs test the *signed* version of that prediction at its
strongest point, and they leave the sign alone: across all 24 cells the difference between α = +1 and α = −1 is
at most 0.0052 of a variance, and no cell changes sign between them. Perfect alignment in the positive direction
(α = +1) is where the mid-band loss *peaks* (+0.4550, the largest loss in the grid), which is the opposite of
what "alignment to the map's structure produces an advantage" predicts.

The alignment axis does move the sign, but only when it is *removed* rather than flipped, and only under one
convention. Table 4's α = 0 rows come from the dedicated alignment instrument `smoke_v10.py` — **one target
draw, one noise realisation, and 50 train/test splits inside that draw**, declared through the calibrated
predictive null of §5.6 — and **not** from the map's `6 target draws × 50 splits` design, which is
`smoke_v12.py`'s and is reported beside these rows as Table 5.

**Table 4 — the alignment axis at α = 0 (no alignment between the target's interaction structure and Q).**
Positive = the quantum kernel is worse; the `p` row belongs to the shifted row above it, and `p` values are
FDR-declared at q = 0.05 across the 36-cell grid. **The instrument that produced these rows is `smoke_v10.py`,
whose `rows` at `alpha == 0` are one `cell_runner` call per cell — one target draw, one noise realisation, and 50
train/test splits inside that draw. It is not the map's `6 target draws × 50
splits` design: that design belongs to `smoke_v12.py`, which runs α = ±1 only. Its α = ±1 panel is reported
beside these rows as Table 5, so the two designs can be read side by side.**

| convention | γ = 0.1 | 0.25 | 0.5 | 1 | 2 | 3 |
|------------|---------|------|-----|---|---|---|
| shifted, α = 0 | −0.0372 | +0.0602 | **−0.1192** | **−0.1676** | **−0.2754** | +0.3671 |
| shifted, α = 0 (p) | 0.203 | 0.044 | 0.013 | 0.0010 | 0.0010 | 0.0010 |
| unshifted, α = 0 | −0.0267 | +0.0312 | +0.0127 | **+0.4110** | +0.0832 | +0.0746 |

**Table 5 — the α = ±1 panel the map itself is measured on (`smoke_v12.py`: 6 independent target draws × 50
splits per cell, the design Table 4's caption used to name).** The two rows of a pair differ only in the sign of
the planted alignment.

| convention | γ | α = +1 | α = −1 |
|------------|-----|--------|--------|
| shifted | 0.5 | **+0.4213** | **+0.4303** |
| shifted | 1 | **+0.4482** | **+0.4691** |
| shifted | 2 | +0.0105 | +0.0155 |
| unshifted | 0.5 | −0.0025 | +0.0010 |
| unshifted | 1 | **+0.3983** | **+0.4098** |
| unshifted | 2 | **+0.4192** | **+0.4233** |

Read against Table 4, the two instruments answer different questions. Table 5 is the map's own design and says
the *sign* of the planted alignment is irrelevant: flipping α from +1 to −1 moves no mid-band cell by more than
0.021, in either convention. Table 4 removes the alignment instead of flipping it, on one target draw, and the
submission read a sign inversion out of it. **That inversion does not survive the panel below, and is
withdrawn.**

**Table 6 — the α = 0 cell re-measured over 13 disjoint streams in three declared seed families**
(`r409_align_streams.py`, shipped in this package; the committed single-draw value is shown beside each).

| γ | pool of 13 streams | sd | streams negative | committed draw | gap to the pool |
|---|--------------------|----|------------------|----------------|-----------------|
| 1 | **+0.2848** | 0.1080 | **0 / 13** | −0.1676 | −4.2 sd |
| 2 | **+0.0402** | 0.0497 | 2 / 13 | −0.2754 | −6.3 sd |

The γ = 1 cell is **positive in every one of the thirteen streams** (95 % t interval [+0.2017, +0.3679]) and the
γ = 2 cell is positive in eleven of thirteen: the one-draw value the submission printed is an outlier of its own
ensemble, and the ensemble itself says the cell is not inverted. The instrument's first control reproduces the committed
twelve-cell Table 4 record exactly, **12 of 12 bitwise**, on the build that record pins
(`python 3.9.6` + `numpy 2.0.2`). That equality is a property of a build, not of the claim, and the control
reports the departure it finds rather than only failing: on the editorial re-check's build
(`python 3.14.2` + `numpy 2.4.2`) **0 of 12** cells are bitwise equal, with a worst **relative** departure of
**2.19e−11** — three orders below the panel's own signal (the gaps this table reports are 4.2 and 6.3
cross-stream sd), so the panel is measuring the same thing the submission measured, more than once.

**PB2 outcome: the mechanism clause stands as measured, and the direction clause is not refuted on the
alignment axis.** The registered criterion's first half — the sign is not set by qubit count or Hilbert-space
dimension — is confirmed: qubit count (§5.8) flips no sign in any cell. The half that names *alignment* is now
measured on two instruments, and what it measures is an **attenuation rather than a sign effect**: fixing the
target's alignment to the map's own structure makes the mid-band loss **larger** by 0.1401 at γ = 1 (5 of 5
streams) and leaves it unchanged at γ = 2 (+0.0461, 0 of 5 negative), while the α = ±1 panel (Table 5) shows the
*sign* of the planted alignment to move no mid-band cell by more than 0.021 in either convention. Because the
α = 0 sign inversion the submission reported does not reproduce (Table 6), the registered direction clause is
**not refuted on this axis**: the axis establishes the *size* of the loss where the target is aligned — the worst
mid-band cell in the map is the aligned one, on the panel's own design — and this paper reports that, with the
inversion withdrawn. The prior is therefore neither confirmed nor refuted in its direction clause, and the
novelty signal an earlier version of this section claimed on it is withdrawn with the inversion. The map's
headline does not rest on it: the mid-band loss, its survival under the strongest valid handicap, and the absence
of the registered inverted-U all stand on the α = ±1 panel and on the 24-cell grid.
