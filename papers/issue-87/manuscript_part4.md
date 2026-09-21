### 5.4 The registered power arm: which way of withholding geometry actually handicaps the rival?

An empty map is evidence only if the pipeline would have found an advantage had one existed. The registration
makes that a promise — a *planted-alignment control*: "a cell where the metric-matched rival is deliberately
handicapped". The study audits that promise by asking a narrower question of every candidate handicap: **does
making the rival's metric worse actually make the rival worse?** Six axes are tested, each a trace-preserving
mixture `W_t = (1−t) W + t (…)` so that every level of an axis has the same mean quadratic form — the envelope
tuning problem is unchanged and the differences are pure shape. The read is the rival's *own* excess-risk change
`dR(t) = R_rival(t) − R_rival(0)`; positive means the handicap acted.

**Table 5 — the handicap ladder (median of the per-cell `dR` at the maximum handicap t = 1; `valid/mixed/rev`
counts cells whose effect is resolvably positive, sign-unstable inside the ladder, or resolvably negative).**

| axis | manipulation | cycle: median (valid/mixed/rev) | path: median (valid/mixed/rev) |
|------|--------------|--------------------------------|-------------------------------|
| A registered | remove the metric's off-diagonal | +0.0074 (5 / 19 / 0) | +0.0059 (8 / 15 / 1) |
| B wrong graph | model a path graph instead | +0.0240 (18 / 0 / 0) † | +0.0120 (21 / 0 / 0) † |
| **C wrong metric** | **trace-matched random PSD metric** | **+0.1256 (24 / 0 / 0)** | **+0.1215 (24 / 0 / 0)** |
| D flat scales | flatten per-qubit scale | −1.9e−16 (1 / 1 / 22) | +0.0080 (14 / 0 / 10) |
| E permuted | same spectrum, wrong structure | +0.0282 (15 / 1 / 8) | +0.0511 (20 / 1 / 3) |
| F identity (negative control) | leave the metric untouched | 0.0000 (0 / 24 / 0) | 0.0000 (0 / 24 / 0) |

† `mixed` counts are per-axis; B and E's zero mixed counts are reported as they are read.

![Fig. 2 — the power arm: the rival's own handicap effect by axis, and the mid-band loss that survives the strongest valid handicap](figures/fig2_power_arm.png)

Three findings come out of the audit, and only the third is a design success.

**(i) The registered axis is inert twice over.** Withholding the metric's off-diagonal (axis A) moves the rival
by +0.0074 of a variance in the median and acts resolvably in 5 of 24 cells. R398's first explanation was
symmetry, and P2 of R399 predicted A would be materially stronger on the path, where the symmetry is broken by
construction and `diag(W)` is non-uniform by 61 %. Measured: **+0.0059 (8/24)**. The prediction is refuted, and
the reason is not symmetry: removing the off-diagonal leaves a *diagonal* metric, i.e. the kernel
`exp(−sγ² Σ_i d_i (z_i − z'_i)²)`, a coordinate-weighted Hamming kernel whose weights are absorbed by the
envelope grid that every arm is tuned over (the same exponent spans 0.003 to 10). **A handicap the tuning
protocol can undo is not a handicap**; it is a reparameterisation.

**(ii) A second axis is an exact identity, and that is a theorem rather than a measurement.** Axis D flattens
per-qubit scale; on a vertex-transitive graph `diag(W)` is already uniform (§5.1), so D is exactly the identity
map — its median effect on the cycle is −1.9e−16, i.e. zero to machine precision, with 22 of 24 cells reading
exactly zero. On the path the same axis becomes real: +0.0080 with 14 of 24 cells resolvable. This is the one
prediction of R399 that is confirmed, and it is confirmed *in kind but weak in size*: it settles how to report
the axis, not that it is a useful power arm.

**(iii) Exactly one axis is both valid and informative, and it is not the registered one.** A trace-preserving,
trace-matched **random PSD metric** (axis C) makes the rival worse in **24 of 24** cells on both graphs, with a
median effect of **+0.1256** on the cycle and **+0.1215** on the path — graph-independent, because it does not
manipulate the graph's structure at all but destroys the metric's *fit*. It is therefore the axis the
registration's power clause should have named: it is the only way in this grid to degrade the rival without
either reparameterising it or depending on a symmetry that the graph may not have. The positive control (E,
permutation: same spectrum, wrong structure) nearly doubles between graphs (+0.0282 → +0.0511), and the negative
control (F) reads exactly zero in all 48 graph × cell combinations, which is what makes the other numbers
readable.

**A defect the second graph exposed, and its repair.** Axis D's mixture leaves the positive-definite cone on the
path graph in **8 of 12 bands** — `exp(−sQ)` is not a kernel there — with the minimum eigenvalue reaching
**−6.2**. The defect cannot fire on the cycle, because the axis is a no-op there; it was found by the pre-run
probe and not by the long run. The repair is recorded rather than silently applied: add `(|λ_min| + 1e−9)·I` and
rescale so the trace is restored exactly, which adds between **0.30 % and 19.8 %** of the mean diagonal at scales
0.835–0.997 and leaves the axis's named endpoint exact (t = 1 still reproduces the identity control at 0.0).

### 5.5 The identity of the rival decides the reported verdict

The methodological claim of this paper is not that the quantum kernel loses to *a* rival; it is that the
*literature's* rival produces the opposite verdict in the same cell. Table 6 is the study's first instrument
(the cycle, q = 6, α = +1, 6 draws × 40 splits) read arm by arm across the bandwidth axis.

**Table 6 — excess risk by arm and bandwidth, and the verdict each rival implies (cycle, q = 6, α = +1).**
`Δ` columns are the quantum arm minus that arm; negative means the quantum kernel is better.

| γ | quantum | matched | closed form | product | RBF | random features | oracle | Δ matched | Δ RBF | Δ random features |
|---|---------|---------|-------------|---------|-----|-----------------|--------|-----------|-------|-------------------|
| 0.1 | 0.1116 | 0.1357 | 0.1412 | 0.1711 | 0.1615 | 0.5364 | 0.1234 | −0.0241 | −0.0499 | **−0.4249** |
| 0.25 | 0.2014 | 0.1454 | 0.1415 | 0.1697 | 0.1615 | 0.5364 | 0.1234 | +0.0560 | +0.0399 | **−0.3350** |
| 0.5 | 0.5256 | 0.1403 | 0.1411 | 0.1582 | 0.1615 | 0.5364 | 0.1234 | **+0.3853** | +0.3640 | −0.0109 |
| 1 | 0.5643 | 0.1480 | 0.1427 | 0.3382 | 0.1615 | 0.5364 | 0.1234 | **+0.4163** | +0.4028 | +0.0279 |
| 2 | 0.1595 | 0.1389 | 0.1356 | 0.5272 | 0.1615 | 0.5364 | 0.1234 | +0.0206 | −0.0020 | **−0.3769** |
| 3 | 0.0772 | 0.1512 | 0.1409 | 0.1674 | 0.1615 | 0.5364 | 0.1234 | −0.0740 | −0.0843 | **−0.4593** |

Three properties of this table matter. First, the oracle — regression on the target's own span — is the best
arm in **every** cell (0.1234), which is what makes the Bayes accounting of §3.1 checkable rather than
asserted. Second, the two *serious* rivals agree: the affine closed form that the theory result hands a
practitioner is within 0.0008 of the fitted matched metric at γ = 0.5, and in the stream panel an isotropic
Gaussian on Hamming distance is within a median 0.0054 (q = 6) and 0.0022 (q = 8) of the matched rival, with a
maximum separation of 0.0180 and 0.0333 — so "the matched rival wins the mid-band" is not an artefact of one
rival's idiosyncrasy. Third, the **weak surrogate reverses the verdict**: the random-feature arm's excess risk is
0.5364 in *every* band (it does not see the bandwidth), and against it the quantum kernel appears to win by
**0.4249, 0.3350, 0.3769 and 0.4593** of a variance at γ = 0.1, 0.25, 2 and 3 — the four cells
where the matched rival shows no such advantage (−0.0241, +0.0560, +0.0206, −0.0740). The residual "quantum-kernel advantages" that
survive a family-baseline audit are, in this generator, a measurement of the surrogate's weakness: the surrogate
is a fixed-envelope predictor whose error does not depend on the bandwidth, so the difference against it is a
rescaled copy of the quantum arm's own error curve.

### 5.6 The fallback clause, read in the study's own currency

The registration's fallback is a power statement: report an empty region as a falsification *together with the
control that would have found an advantage if one existed*. §5.4 gives the handicap magnitude; this section
reads the study's own grid through the **calibrated declaration procedure** — the multiple-testing layer the
study uses to decide which cells carry a departure from noise at all. The null is built by the same generator
with the signal removed (60 null cells per band, A = 0, the same splits), fitted per band as a
location-scale family pooled across a convention's six bands, and simulated 20 000 times per cell, which puts
the procedure's resolution at **1.0e−4** — below the smallest Benjamini–Hochberg threshold on this grid
(2.08e−3 at m = 24), so the counts cannot be floor-limited. Its size is validated on a holdout half of the null:
**0.28 %** (1 of 360 cells declared), i.e. twenty times conservative, so every count below is a lower bound.

**Table 7 — the fallback clause along the valid handicap axis (C), with the pre-registered expectations.**

| read | registered | measured |
|------|-----------|----------|
| size of the procedure on a holdout null | ≤ 5 % | **0.28 %** (1/360) — pass, 20× conservative |
| resolution vs the declaration threshold | finer than BH's | 1.0e−4 < 2.08e−3 — pass |
| cells declared at the **matched** rival (t = 0) | 8–16 | **23 of 24** — refuted |
| declared count along the ladder | non-decreasing, materially higher at t = 1 | **23 → 22 → 24 → 24** — refuted: the count saturates |
| cells the quantum kernel leads (mean δ < 0) along the ladder | — | **11 → 12 → 14 → 16 of 24**, 5 cells flipping sign |
| the mid-band block at maximum handicap | — | still loses **+0.2922 … +0.3219** |

The clause is discharged in the currency that still varies, and the refutation is informative rather than a
failure: the declaration count saturates because the null's own within-band dispersion (0.0013–0.0030) is two
orders of magnitude below the study's effects (0.01–0.52), so a dependence-free procedure declares almost
everything. The *count of leads* is the quantity with headroom, and it moves monotonically 11 → 16 as the rival
degrades — which is the power statement the registration asked for, in the form the instrument can support. What
does **not** move is the mid-band block: at the strongest valid handicap the quantum kernel still loses
0.29–0.32 of the target's variance in the four worst cells (shifted, γ = 0.5 and 1, both alignment signs) — so
the paper's central negative result is not the rival being unfairly strong.

Two further reads qualify the procedure. First, **arms are not exchangeable even with no signal**: the null's own
location is off zero per band by up to ±0.005, tens of standard errors of its own mean, so "declared" means
"departs from the null" and never "the quantum kernel wins". Second, the 24-cell count is not 24 independent
reads: the two alignment cells of a band share their split and noise draw (within-band correlation of the paired
differences has median +0.19, reaching +0.87 at shifted γ = 0.5), so the count carries 12 independent units, and
it is stable under either reading precisely because it saturates.

### 5.7 The second graph: the map is not a cycle artefact

The whole map above lives on the cycle graph, so the study re-runs the grid on a **path** — the graph where the
metric's scale uniformity is broken (§5.1) and where the registered handicap A was predicted to bite. The
cross-harness control first re-derives the cycle's 24 cells × 24 ladder levels: **576 of 576 exact**, maximum
absolute difference 0.0. On the path, the map's signs agree with the cycle's in **23 of 24** cells; the single
disagreement is `unshifted|0.5` at α = −1, a cell whose cycle reading is +0.0010 and whose path reading is
−0.0121 — the same cell the declaration procedure cannot distinguish from a no-signal cell. The matched rival
dominates the mid-band on both graphs. The 8 ≤ 12 PSD repairs above are part of this stratum's evidence, not a
footnote: the second graph is what turns a machine-precision identity into a measured effect and a latent defect
into a visible one.

### 5.8 Qubit count: no sign moves, every magnitude compresses

The panel re-runs the full 24-cell map at q = 8 under five disjoint seed streams. The discrete map is *more*
stable at the higher qubit count — the set of leading cells is identical in all five streams (6 cells) — while
the mid-band loss attenuates. Across the 8-cell mid-band block the ratio q = 8 / q = 6 has mean **0.6894**
(median 0.6936, range 0.5727–0.7904), and all six attenuation readings are negative in 5 of 5 streams
(shifted γ = 0.5: −0.0948 / −0.0894; shifted γ = 1: −0.1755 / −0.1765; unshifted γ = 2: −0.1881 / −0.1762, at
α = +1 / −1), each resolvable at 6.8–18.8 times its own cross-stream sd. So **qubit count does not flip a single
sign in the grid**: PB2's "not by qubit count or Hilbert-space dimension" half is confirmed, and the compression
is reported as a magnitude effect with an error bar rather than as a new regime.

**Table 8 — the panel's pre-registered questions.**

| Q | prediction | result |
|---|-----------|--------|
| Q1 | the 8 structure cells are stream-stable (≥ 7/8 sign-unanimous, sd < 0.05) | **8/8 unanimous at both qubit counts**; max sd 0.0145 (q = 6) / 0.0062 (q = 8) — met |
| Q2 | ≥ 3 of the 10 near-zero cells flip sign across streams | **2 of 10** (10 further cells tie) — not met |
| Q3 | the attenuation is a qubit-count effect (≥ 4/5 negative, ≥ 3 sd) | 6/6 readings negative in 5/5 streams, all resolvable — met |
| Q4 | the 4 main-claim cells' 95 % lower bound > +0.15 | **8 of 8**, lower bounds +0.398 … +0.442 — met |
| Q5 | the across-stream sd exceeds the within-stream draw sd | 0 of 24 — **not met, and the comparison was mis-specified** (see below) |
| Q6 | the matched-vs-isotropic-RBF separation is ≤ 0.02 | median 0.0054 (q = 6) / 0.0022 (q = 8) — met |

The Q5 repair is this study's most transferable methodological result and it is reported against itself: the
registered inequality compared the sd of a *stream mean* — an average over 6 target draws — against the sd of a
*single draw*. Under independent draws the first should be ≈ σ_draw/√6, so the inequality was mis-specified, and
the panel's aggregate denominator mixed the two qubit counts, i.e. it averaged over the very factor the ratio was
then read across. Measured with a matched denominator on the panel's own code path, the corrected ratio
`sd_stream / (σ_draw/√6)` is a median **0.9955** at q = 6 (3 of 24 cells above 1.2) and **1.0611** at q = 8
(7 of 24), with σ_draw = 0.0191 (q = 6) and 0.0050 (q = 8): the stream adds no variance detectable at this
sample size beyond the draws it averages, so the cross-stream sd may be used directly as a per-cell error bar.
The aggregate-denominator version of the ratio (1.467 / 0.427) was **manufactured by its denominator**; it is
kept in the package's notes as an example rather than dropped. Pairing the q = 6 and q = 8 maps buys nothing
either: they share a stream label but cannot share a draw (different Hilbert-space dimension, hence different
targets and permutations), and the paired sd agrees with the unpaired `√(sd₆² + sd₈²)` to a median ratio of
1.017. The qubit effect is resolvable because it is 5–16× the between-stream scatter, not because pairing helped.

## 6. Discussion: what changes if this map is right

### 6.1 The claim in one paragraph

Against a classical rival that receives the entangling ZZ fidelity map's own induced metric, and under the same
nested tuning protocol as every other arm, the map has no advantage region in the registered shape anywhere in a
24-cell grid swept over two phase conventions, six bandwidths, two planted alignment signs and two qubit counts.
What it has instead is a **valley with two rims**: the kernel loses **+0.41 … +0.46** of a target-variance in a
contiguous mid-band block at q = 6 (sign-unanimous in all five streams, every 95 % lower bound ≥ +0.398), loses
**+0.25 … +0.34** in the same block at q = 8, and leads by at most **0.073** on the two flanks. The loss survives
the strongest *valid* handicap of the rival, and the rival's own geometry is the mechanism: where the planted
target's interaction structure is the map's graph, the rival is exactly right and wins by half a variance. Where
alignment is removed the loss is *attenuated* at γ = 1 (by 0.1401, in 5 of 5 streams) and unchanged at γ = 2: the
sign does not move, and the sign inversion an earlier version of this paragraph reported is withdrawn.

### 6.2 Significance: whose belief changes

- **Practitioners deciding on a hardware budget.** The decision rule the field offers is "does the quantum kernel
  beat a tuned classical kernel?". In this map the answer depends entirely on *which* classical kernel: a
  random-feature surrogate says yes by 0.4249 at γ = 0.1; a nested-CV-tuned radial-basis kernel says no by 0.3640 in
  the mid-band cell; a kernel given the map's own metric says no by 0.3853. A reader who takes the first comparison as evidence
  for an entangling map changes that belief here.
- **Method authors who justify an entangling map by its representational power.** The map's entanglement axis
  does not decide the sign [45]: alignment does, and in the direction opposite to the registered prediction. The
  honest reading of the mid-band is that the map's geometry is *right* for the target and the rival simply
  implements it better than the map's own higher-order terms do — an argument that a stronger entangling map
  should be justified against a matched rival, not against a family.
- **The benchmarking community.** A synthetic, exactly solvable generator with a known Bayes risk gives what a
  dataset cannot: a labelled alignment axis. The study's four decisions (§1) are reproducible by anyone with
  numpy, and the metric-matched rival is writable in closed form from a published theorem [19] — the difference
  between this study and a benchmark is therefore an afternoon of assembly, not a new instrument.
- **The theory community.** The closed-form reduction [19] is stated qualitatively where it fails; this map
  measures the scope. The measured boundary is not a curve fitted to the grid but a statistic of the map
  (`diag(W)`'s uniformity, exact to machine precision exactly where the graph is vertex-transitive) plus the
  metric-field spread, which is what an a-priori screening rule for "is this map worth a hardware budget" would
  need.

### 6.3 What the study does *not* claim

It does not claim that quantum kernels are useless, nor that entangling maps never win. It claims that in this
generator, against a rival built from the map's own geometry, the win is confined to two regimes that the field
does not cite as evidence, and that the regime the field does cite is the one where the rival wins largest. It
makes no noise claim: the instrument is exact statevector simulation with no noise model, and the metric is
computable exactly because of that. It makes no hardware claim: nothing here is run on a device, and the
random-feature and Hamming-RBF arms are classical by construction. And it makes no claim about *all* quantum
kernels: one map family (ZZ), one depth (L = 2), two qubit counts, three graphs, and the fidelity kernel's own
metric as the matching object.

## 7. Threats to validity

1. **The matched rival is a proxy, not the geometry — and the per-point construction that was supposed to test
   that is now measured.** The map's metric is a *field* (spread 1.14 to 6.18 across the bandwidth grid), so a
   global Mahalanobis rival can be matched only at the mean. This is the study's largest single limitation, and
   it is the reason the paper reports the field's spread in every cell. The obvious follow-up — replace the
   mean-matched rival with a per-point one — is answered here rather than deferred (`r412_matchedlocal_tuned.py`,
   shipped in this package, five disjoint streams). The instrument's scale is fixed before any arm runs: excess
   risk is measured against the Bayes predictor on the same test set, so 0 is the Bayes predictor and ≈ 1 is
   predict-the-mean. On that scale:
   - the **per-point rival as previously committed** (envelope held at 1) reads **1.012 / 1.055 / 1.055** at
     γ = 0.5 / 1 / 2 — it is the trivial predictor, not a rival, so the earlier parenthetical that it is "worse
     than the mean-matched one" was comparing the quantum arm against predict-the-mean;
   - **swept over the same nested-CV envelope grid as every other family**, it becomes a real rival in exactly
     one of the three mid-band cells (γ = 0.5: excess risk **0.131** against the mean-matched **0.143**) and
     there **the mid-band loss does not shrink: it is +0.4396 against it, against +0.4284 against the
     mean-matched rival** — larger by 0.011, the wrong sign for the caveat's hope;
   - at γ = 1 and γ = 2 the same sweep **blows up** (excess risk 2.231 and 3.696: the nested CV's own choice
     lands at the small edge of the envelope grid, where the kernel is near rank one and the ridge solve
     diverges), so no reading is available there and none is reported.
   The conclusion the measurement supports is therefore not "a stronger local rival shrinks the loss" but
   "the per-point construction is either the trivial predictor or numerically unusable in this regime", which
   is why the mid-band result rests on the mean-matched rival and states so.
2. **One generator, planted targets.** The alignment axis is swept by construction, which is the study's
   methodological advantage over a dataset and also its scope limit: the target family is a quadratic
   interaction function of a uniform hypercube. A reader who believes real data are not of this form should read
   the map as a *bound* on what alignment can buy — the direction of the alignment effect (aligned ⇒ loss) is the
   transferable claim, not its magnitude.
3. **The alignment axis is measured on two instruments, and the axis reads as an attenuation rather than a sign
   effect.** Table 4's α = 0 rows come from the alignment instrument (`smoke_v10.py`: one target draw, one noise
   realisation, 50 splits inside that draw, declared through the calibrated null); Table 5's α = ±1 rows come
   from the map's own design (`smoke_v12.py`: 6 independent target draws × 50 splits). The α = 0 cell has now
   been re-measured over 13 disjoint streams in three declared seed families (Table 6, instrument shipped), and
   the one-draw sign inversion **does not reproduce** — the cell is positive in 13 of 13 streams at γ = 1 and 11
   of 13 at γ = 2 — so that claim is withdrawn at every site. What the alignment axis supports is an
   **attenuation** (removing the alignment reduces the mid-band loss by 0.1401 at γ = 1, 5 of 5 streams) and a
   **null at γ = 2** (+0.0461, 0 of 5 negative); the registered direction's remaining contradiction is the *size*
   of the loss at the prior's strongest point, which is read on the α = ±1 panel (Table 5) rather than on a sign
   change. Two further reads are missing and are the axis's own future work: the interpolation between the two
   `diag(W)` poles (**cycle with k chords**, §5.1), and an alignment level between α = 0 and α = ±1 — a
   half-aligned target, which the construction currently cannot express because the support of A is the edge set
   or empty.
4. **Qubit count is not a continuum.** The attenuation at q = 8 (mean ratio 0.689) is measured at two points. If
   the trend continued, the mid-band loss would vanish near q ≈ 14 — outside exact statevector reach, where the
   comparison would need a different instrument and a noise model this study deliberately does not have.
5. **The handicap axes are mixtures, not metric families.** Axis C is a random PSD metric, which is *uninformed*
   rather than *wrong* in a structured way. A family of adversarially wrong metrics (e.g. one built from a
   different graph with matched spectrum) would be a stronger power arm than the one found valid here.
6. **Inference is resampling-based.** Runs are deterministic, so the intervals are over resampled splits and
   over five disjoint streams — not run-to-run variation. The panel's own Q5 repair (r ≈ 1) is the evidence that
   the stream is the right unit at this sample size; it is not evidence that it would be at a smaller one.
7. **The declaration procedure is conservative by 20×.** A size of 0.28 % on a holdout null means the counts
   reported in §5.6 are lower bounds; a procedure calibrated to its nominal 5 % would declare more, and the
   saturation result would be unchanged or stronger.
8. **Why this is still worth publishing.** The negative result is not "we measured a system and it did not
   work". It is a *falsification of a registered, theory-anchored prior using the prior's own instrument*, with
   the boundary stated as a computable statistic, with the power arm audited rather than assumed, and with the
   comparison that produces the opposite verdict identified numerically. Every number in the text is owned by a
   committed artefact through the digest, and every instrument defect this study found is in the package with
   its repair.

## 8. Conclusion

We built the rival that the quantum-kernel advantage claim requires — a classical kernel given the map's own
metric under the same tuning protocol — and mapped the advantage over conventions, bandwidths, alignment signs
and qubit counts on a generator with ground truth by construction. The registered region does not exist, and the
sign of the mid-band is inverted: the map is a valley whose rims are the two degenerate limits, and the band
where the field reads its evidence is the band where a metric-matched rival wins by half a target-variance, in
eight cells, at both qubit counts, with five streams of sign-unanimity and every lower bound above +0.39. The
same cell yields an apparent win of +0.42 against the weak surrogate the field uses. The registered power arm
turned out to be inert for two reasons that had to be separated — an exact identity on a symmetric graph, and
absorption into the tuning protocol — and exactly one handicap axis is both valid and informative, which is the
axis on which the loss was re-measured and survived. The map's boundary is a computable statistic of the map
rather than a fitted curve. If the field's remaining advantage claims are to be believed, they should be measured
against a rival that receives the geometry they claim credit for.
