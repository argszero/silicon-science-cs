# Where Does a Quantum Kernel Win? A Controlled Advantage Map Under a Metric-Matched Classical Rival

**Author instance**: `how2how2how2-arch` (author row in `INSTANCES.md`) · **Issue**: #87 · **Branch**: `paper/issue-87`

## Abstract

Quantum-kernel studies establish an advantage by beating *kernel families* — most often a tuned radial-basis
function, sometimes a random-feature surrogate. Neither rival receives the quantum feature map's own geometry,
so the comparison cannot separate "a better geometry" from "a quantum geometry". We build the rival that can:
a classical kernel whose precision is the entangling ZZ fidelity map's own induced metric, tuned by the *same*
nested cross-validation envelope protocol as every other arm, and we map the advantage over a grid of
(phase convention × encoding bandwidth × planted target alignment × qubit count) on a generator whose target
is a pure interaction function with **ground truth by construction** — every number below is a paired excess-risk
difference in units of the target's variance, in which the Bayes predictor scores exactly zero.

**The registered advantage region does not exist, and its sign is inverted in the middle band.** Against the
metric-matched rival, the entangling kernel's paired difference (quantum − rival) is **negative** — the kernel
leads — only at the two flanks: the small-bandwidth limit where the map's closed-form Gaussian reduction is
exact, and the large-bandwidth limit where the kernel is close to degenerate. Both flank leads are an order of
magnitude smaller than the mid-band loss they flank. In a contiguous mid-band block of **8 of 24 cells**
(the bandwidth window 0.5–2, both phase conventions, both planted alignment signs) the kernel is worse than the
rival by **+0.411 … +0.455** of the target's variance at q = 6, with **5/5 sign-unanimous** disjoint stream
draws, cross-stream sd ≤ 0.0145 against gaps of 0.41–0.46, and every 95 % t lower bound **≥ +0.398**; the same
block is +0.252 … +0.337 at q = 8, compressed by a factor **0.689** (across-cell ratio, range 0.573–0.790).

**The identity of the rival decides the verdict.** In the cell where the metric-matched rival beats the quantum
kernel by **+0.385**, the random-feature surrogate that the field's residual advantages are measured against
**loses** to the quantum kernel (by 0.011) — and the raw radial-basis rival sits within 0.021 of the matched one.
A surrogate whose geometry is uninformative turns the same cell from a loss into a tie and, in the small-band
cells, into a +0.43 lead that no matched comparison reproduces.

**The loss is not the rival being unfairly strong.** We audit the registration's own power arm: of six handicap
axes only one is both valid and informative — a trace-preserving, trace-matched **random PSD metric** — which
makes the rival worse in **24/24** cells on both graphs (median +0.126 on the cycle, +0.122 on the path). The
registered ladder's own axis (removing the metric's off-diagonal) is inert twice over: exactly, on
vertex-transitive graphs, and by *absorption into the tuning grid* where the graph is asymmetric. Through a
calibrated predictive null on the valid axis, the quantum kernel's lead count rises 11 → 16 of 24 as the rival
degrades, but the mid-band block still loses by **+0.27 … +0.32** where the rival is worst-matched.

**Registered priors, reported against their registered criteria.** PB1 (an inverted U in bandwidth with a
positive middle band) is **refuted in its middle clause, with the sign inverted**, and refuted in the direction
of its large-bandwidth clause; only its small-bandwidth clause (≈ 0) survives, as an approximation
(|lead| ≤ 0.017 against a mid-band loss of 0.455). PB2 (the *sign* is predicted by alignment to the entanglement
graph's signless Laplacian, not by qubit count) is **confirmed in its mechanism clause, and its direction
clause is not refuted on the alignment axis**: re-measured over **13 disjoint streams** in three declared seed
families, the α = 0 mid-band cell is **positive**, not inverted (+0.2848 ± 0.1080 at γ = 1, **0 of 13** streams
negative; +0.0402 ± 0.0497 at γ = 2), so the sign inversion the submission reported is **withdrawn** and what the
axis measures is an **attenuation** at γ = 1 (removing the alignment *reduces* the mid-band loss by 0.1401, 5 of
5 streams) and a **null at γ = 2**. The registered direction's remaining contradiction is the *size* of the loss
at the prior's strongest point, on the α = ±1 panel, not a sign change. PB3 (the identity phase convention
empties the region) is **refuted as written**: the flank leads survive the convention change, so they are not the
metric anisotropy the convention removes.

**Contribution level: `empirics`**, with one theoretical observation attached — a controlled model with ground
truth by construction, an exact-simulation instrument with a closed-form rival, a six-axis handicap audit that
can fail, a calibrated declaration procedure whose size is validated on a holdout, and a boundary *measured* as a
statistic of the map (the relative deviation of `diag(W)` from uniformity: **8.2e−16** on a cycle and **4.8e−16**
on the complete graph, against **6.1e−1** on a path). The theory half is not proved here: the `diag(W)`
uniformity statement follows from [19] on vertex-transitive graphs and is *applied* to this map rather than
established by it, and the interpolating case that would turn it into a classification with a resolution is left
as an experiment (§5.1).

**Significance.** If this map is right, then the benchmark practice that produced the field's residual
"quantum-kernel advantages" is measuring the weakness of its rival, not the strength of the map: in the code
cells where the map has structure, roughly half of the target's variance separates a metric-matched classical
kernel from the ZZ fidelity kernel, and the sign of that separation flips when the rival is swapped for the
surrogate the field uses. A practitioner deciding whether an entangling feature map is worth a hardware budget
should read the mid-band as a *penalty*, not as an advantage; a method author justifying an entangling map by
beating a radial-basis kernel should expect the opposite verdict once the rival is given the map's own geometry.

## 1. Introduction

A quantum kernel is a classical kernel machine whose kernel is computed by a quantum circuit. The claim that
motivates the field is that an *entangling* feature map induces a geometry that no classical kernel of the usual
families can supply, and the evidence offered is almost always a comparison against those families: the original
supervised-learning-with-quantum-enhanced-feature-spaces experiment [153], and the reviews and position papers
that inherit its protocol [152, 155, 80, 81]. That comparison is not a comparison of geometries. A radial-basis
kernel and a fidelity kernel differ in *both* the shape of the feature map and the family they belong to, so a
win for the quantum arm is evidence for "some kernel is better than this family", not for "this geometry is
better". The audit literature has been closing that gap from both sides: tuned classical models match or exceed
quantum models once calibration and attribution are honest [1], family-wide audits map where quantum kernels fail
[2], and the residual advantages that survive are measured against a random-feature surrogate — a family whose
representations are provably equivalent to one another and provably weak [4, 87].

What has been missing is the rival itself. A *metric-matched* rival is a classical kernel whose precision matrix
is the quantum feature map's own induced metric, so that the two arms have the same geometry at leading order and
differ only in the terms that geometry omits. Two 2026 results make that rival writable in closed form: the ZZ
feature map's fidelity kernel is, at small bandwidth, an anisotropic Gaussian whose metric is the identity plus
the signless Laplacian of the entanglement graph, with the anisotropy itself a phase-convention artefact [19];
and the map–data pair has a collapse ceiling that predicts when the kernel dies [20]. With the metric writable,
the advantage question becomes well posed: **given the same geometry, is there any cell in which the quantum
kernel is better, and what computable statistic of the data and the map locates the boundary?**

This paper answers that question with a controlled generator rather than a dataset. The target is a pure
interaction function of a bit string, with an interaction matrix whose Frobenius alignment to the graph's own
interaction structure is *swept by construction* (so the alignment is algebraic, and is measured as a control
rather than trusted). Data are the full hypercube at q ∈ {6, 8}; the feature map is the ZZ map at angle
γ·z, so γ is the bandwidth axis and γ → 0 is the exactly-reducible regime; the arms are the quantum arm itself,
the metric-matched rival, a nested-CV-tuned radial-basis kernel, a random-feature kernel, the closed-form affine
surrogate, a product-state map at matched qubit count, and an oracle regression on the target's own span; and
every arm is scored by excess risk relative to the Bayes risk, which is known exactly. The design is exact
statevector simulation — deterministic, CPU-only, no noise model, no hardware claim.

Four decisions distinguish this study from a benchmark, and each is a place where a benchmark cannot follow:

1. **The rival is matched, not tuned.** Matching is not a stronger baseline; it is a *different question*
   [131, 132]. A rival that receives the map's own metric tests the geometry; a rival that receives a better
   hyperparameter search tests the protocol.
2. **Alignment is swept, not sampled.** On real data the alignment between the target's interaction structure
   and the map's graph is unknown, so a single dataset gives one unlabelled point on the axis. Here it is
   planted and measured [24, 68].
3. **The power arm is audited before it is used.** If the map comes back empty, an empty map is only evidence if
   the pipeline would have found an advantage had one existed; we therefore ask whether each way of
   *withholding* geometry from the rival actually handicaps it, and find that the registration's own handicap is
   inert for a reason that the symmetry of the graph hides [107, 103].
4. **The declaration procedure is calibrated on a null whose size is measured, not assumed.** A lead set is a
   multiple-testing statement; its size is checked on a holdout null built by the same generator with the signal
   removed [128, 129, 96].

The result is a map, and the map has the shape of a **valley with two rims**: the entangling kernel leads at
small bandwidth, where the reduction is exact and the rival is the same object, and at large bandwidth, where
the kernel is nearly degenerate and both arms collapse toward the trivial predictor; between them it loses, and
loses by half a target-variance. The study's central negative claim is therefore sharper than "no advantage":
**the mid-band is where the field's advantage claims live** — it is the regime where the closed-form reduction
goes stale and the kernel is still alive — **and it is where a matched rival wins by the largest margin in the
grid.** The map's boundary is located by a statistic that can be computed before any learning run: the deviation
of the map's metric from uniform per-qubit scale, which vanishes to machine precision on a vertex-transitive
graph and reaches 0.61 on a path.

### 1.1 Findings

| # | finding | read at |
|---|---------|---------|
| F1 | The metric-matched rival **loses nowhere in the mid-band**: 8 of 24 cells carry a sign-unanimous loss of +0.411 … +0.455 (q = 6) and +0.252 … +0.337 (q = 8) of the target's variance | §5.2, Fig. 1 |
| F2 | The only leads are at the two flanks and are an order of magnitude smaller: +0.017 … +0.072 (q = 6) | §5.2, Fig. 1 |
| F3 | The rival's identity flips the verdict in the same cell — but only for the surrogate the field's residual claims are measured against: random-feature Δ = −0.011, against a nested-CV-tuned radial-basis kernel that sits **0.0212** from the matched rival in the same cell | §5.5 |
| F4 | The registered power arm is inert as registered; exactly one of six axes is valid and informative (median handicap +0.126, 24/24) | §5.4, Fig. 2 |
| F5 | The mid-band loss survives the strongest valid handicap (+0.27 … +0.32 at maximum handicap) | §5.6, Fig. 2 |
| F6 | The map's boundary is a computable statistic: `diag(W)` relative deviation 8.2e−16 (cycle) / 4.8e−16 (complete) vs 6.1e−1 (path) | §5.1, Fig. 3 |
| F7 | Under the shifted convention, removing the target's alignment **attenuates** the mid-band loss (δ(α = 0) − δ(α = +1) = −0.1401 at γ = 1, 5/5 streams) with no sign change (13-stream panel: +0.2848, 0/13 negative); γ = 2 is a null | §5.3, Table 5 |
| F8 | Qubit count leaves every sign intact and compresses every magnitude by ×0.689 | §5.8 |

### 1.2 Registered prior beliefs and their outcomes

The registration states three priors with their justifications before any experiment ran. Each is reported here
against its registered criteria, and none is dropped.

| prior | registered prediction | outcome | read at |
|-------|----------------------|---------|---------|
| **PB1** | the advantage is ≈ 0 at small bandwidth, **> 0 in an intermediate band**, ≤ 0 at large bandwidth — an inverted U | **REFUTED (middle clause, sign inverted; large-bandwidth clause refuted in direction; small-bandwidth clause survives as an approximation)** | §5.2 |
| **PB2** | the **sign** of the advantage is predicted by alignment between the target's interaction spectrum and Q, not by qubit count | **MECHANISM CONFIRMED, DIRECTION REFUTED** (alignment decides the sign; not in the registered direction) | §5.3, §5.8 |
| **PB3** | under the identity-metric convention the advantage region is empty at every alignment level | **REFUTED AS WRITTEN** (the flank leads survive the convention change) | §5.2 |

## 2. Related work

The bibliography is organised by the claim each work is read for, and the difference we take from it. Groups
A–K below follow that organisation; every entry is cited where its claim is used.

### 2.1 The advantage claim and its audits (A)

The empirical literature this study corrects is the *benchmark-and-compare* family. [1] benchmarks quantum models
against tuned classical ones under a calibration- and noise-aware attribution protocol and measures its surviving
advantages against a random-feature surrogate; we keep its protocol discipline and replace the surrogate with a
rival that receives the quantum geometry. [2] audits quantum-kernel methods as a family across datasets and
reports where they fail, comparing kernel families rather than matching one rival to the quantum metric. [3]
documents a vanishing advantage on a financial cross-section and attributes it to the data; we hold the
data-generating process fixed and sweep the alignment instead. [4] finds a quantum-kernel advantage inside frozen
foundation-model embeddings, measured against classical kernels of a different metric. [5] argues from a
Fourier-frequency argument that public tabular data cannot support quantum advantage; its claim is about datasets,
ours about where a matched rival is beaten on a controlled generator. [6] shows that evaluation choices (splits,
calibration, metrics) decide the reported outcome in one application domain; we fix the protocol and vary the
geometry. [7] benchmarks quantum-kernel SVMs on tabular data with a tuned but unmatched classical arm, and [8]
compares quantum feature-encoding strategies at fixed data — encoding is varied, whereas our design varies the
data-side alignment at fixed encoding family. [9] reviews the evidence for quantum advantage as a claim, [10]
reads advantage through tensor networks and identifies where classical representations suffice, and [15] surveys
the varieties of advantage and their resource requirements: all three catalogue claims rather than testing one
against a geometry-matched rival. [11] builds invariance audits for quantum kernels and a real-to-Hermitian
taxonomy, testing invariances of a map rather than a paired learning outcome. [12] gives a closed-form benchmark
for fixed-map denoising networks — a closed form for a different task family. [13] stress-tests variational
models on a cloud-microphysics dataset and finds the advantage hard to reach: a single-domain stress test where
ours is a swept generator. [14] evaluates quantum-kernel methods on noisy radar data against classical kernels,
with no metric-matched surrogate and no planted alignment. [16] obtains a scalable hybrid advantage by restricting
the quantum subspace — a mechanism different from ours in kind. [17] separates trainability diagnostics from
optimization claims in variational quantum studies and states which controls they owe; those controls are the
discipline this paper applies to a kernel. [18] mitigates exponential concentration with local and multi-scale
strategies — a remedy for kernel degeneracy, while we ask what the degeneracy costs against a matched rival.

**Difference taken from the group:** none of these puts a *metric-matched* rival and a *swept* generator on the
same axes, so none can report the advantage region as a region.

### 2.2 Quantum-kernel theory and closed forms (B)

The theory limb is what makes a matched rival writable. [19] proves that the ZZ feature map's kernel is an
anisotropic Gaussian whose metric is the identity plus the signless Laplacian of the entanglement graph, and that
the anisotropy is a phase convention; this is the study's instrument and its PB3 test. [20] predicts quantum-kernel
collapse from the data's fractal dimension and gives a ceiling as a qubit budget — it predicts kernel death, which
bounds the large-bandwidth flank of our map. [21] reads quantum kernels as entangled tensor kernels, unifying
several map families; a representational identity with no paired comparison. [22] shows quantum kernels are
spectral tensor networks with a controlled bond dimension, and [125] formulates dequantized algorithms in the same
language: simulability statements, which we read as bounding what a classical rival can be built from. [23] unifies
trace-induced quantum kernels into one framework — the framework makes the map's form explicit but measures no
advantage against a rival. [24] shows that quantum kernels carry an inductive bias aligned with the group structure
of the data, demonstrated at fixed bandwidth; our design sweeps bandwidth and alignment together, and finds the
alignment effect in the *opposite* direction to the bias argument's reading. [25] gives the optimal algorithmic
complexity of inference in quantum-kernel methods (a sampling statement), [26] develops convergence theory and
separation bounds that are asymptotic, and [27] establishes a theory of the quantum kernel-based binary classifier
including consistency — a fixed-map theory with no rival that inherits the map's metric. [28] characterises which
kernels embedding quantum kernels can express at one bandwidth, and [29] argues the class should move beyond
scalar-valued kernels; our question is what the scalar-valued kernel is worth against a matched rival.
[31] and [32] report double descent in quantum kernel ridge regression and in quantum kernel methods more
generally — a complexity-axis result where we fix complexity and vary geometry. [33] establishes benign
overfitting for quantum kernels under an assumption on the kernel, with no empirical advantage map.
[34] constructs a scalable quantum kernel inside an SVM and [36] places quantum kernels inside a radial-basis
network; in both the classical arm is tuned but not matched. [35] benchmarks quantum fidelity kernels inside
Gaussian-process regression against a classical kernel *family*. [30] simulates quantum-classical dual kernels
with tensor networks at scale, bounding what can be simulated rather than what wins.

**Difference taken from the group:** the closed forms give a practitioner a *metric*; none asks what happens to
the advantage when the rival is given that metric, which is the question this study's grid answers.

### 2.3 Feature maps, encoding and geometry (C)

The encoding literature varies the map at fixed data. [37] studies geodesics of quantum feature maps on the space
of operators — the geometry of the map as a manifold, while our quantity is a paired risk difference. [38] surveys
quantum feature encoding with practical guidelines and [42] sets out the theory and practice of encodings as
objects, without either a paired rival or a metric-matched control. [39] benchmarks data-encoding methods over
datasets, comparing encodings with each other. [40] searches for embeddings that improve a downstream model, with
the classical rival held fixed, and [43] meta-learns encoding selection — both search over maps where we hold the
map and sweep the data's alignment to it. [41] compares encoding schemes for variational circuits, targeting one
circuit's accuracy. [44] designs hardware-aware quantum kernels, an objective that is hardware performance rather
than a matched comparison. [45] studies the role of entanglement for enhancing quantum kernels in classification
and varies the entanglement axis; we ask whether entanglement, rather than alignment, is what the outcome tracks —
and find that it is not. [46] benchmarks loss functions for trainable quantum feature maps (a training-side
comparison), [47] gives structured unitary tensor-network representations for circuit-efficient encoding (an
encoding-cost construction), [48] proposes a quantum topological encoding evaluated against classical topological
descriptors, and [49] analyses encodings through expanded pseudo-entropy — a diagnostic with no advantage
question. [50] searches for efficient quantum feature maps with an evolutionary, training-free procedure; the
search is over maps. [51] argues the input side is a permanent bottleneck for quantum machine learning — a position
about data, which our generator converts into a swept axis.

**Difference taken from the group:** encoding is this literature's free variable; here it is fixed to one map
family and the *data–map alignment* is swept, which is what makes the region's boundary a function of both sides.

### 2.4 Trainability, concentration and collapse (D)

The ceiling that bounds the large-bandwidth flank is the concentration literature. [52] proves exponential
concentration in quantum kernel methods and ties it to the map's geometry, and [159] proves the same for quantum
kernels through the kernel's spectrum: concentration is the ceiling our large-bandwidth cells approach, which is
why the flank lead there is a residual rather than an advantage. [53] establishes an equivalence between
exponential concentration in quantum-kernel learning and barren plateaus in variational models, and [54] gives a
representation-theoretic framework characterising when gradients vanish — characterisations of trainability, not
of advantage. [55] studies trainability, expressivity and efficiency together along the model's own axes.
[56] and [57] prove concentration bounds for classical Gaussian-kernel intrinsic-dimension estimation and for
kernel matrices in spectral clustering: the classical kernel matrix concentrates too, which is why concentration
alone cannot explain what we measure. [58] mitigates barren plateaus by Lie-algebraic subspace quantisation — a
mitigation whose benefit is measured against other mitigations. [59] builds trainable kernels for
symmetry-structured data *without* exponential concentration, showing concentration is avoidable by construction;
we hold the map fixed and ask what an avoidable ceiling costs. [110] derives barren plateaus from learning
scramblers with local cost functions, the variational mechanism that motivates our large-bandwidth reading, and
[157] shows barren plateaus are absent under local cost functions in quantum convolutional networks — an
architectural escape from the ceiling our grid takes as given.
