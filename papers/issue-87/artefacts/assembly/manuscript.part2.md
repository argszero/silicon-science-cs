### 2.5 Dequantization and classical simulability (E)

If a quantum model can be dequantized, a matched classical rival is not a straw man but a construction. [60]
dequantizes supervised quantum machine learning with random Fourier features, [61] dequantizes variational
quantum machine learning kernel-based and *without* random Fourier features, and [62] states the potential *and
the limitations* of random Fourier features for that purpose: these target worst-case complexity, whereas our
question is what the same geometry is worth at finite sample size on a controlled task. [63] robustly dequantizes
the quantum singular-value transformation and quantum machine learning algorithms, and [64] dequantizes quantum
machine learning models with tensor networks — a different surrogate family [22, 125] from the one we match.
[65] asks when an input distribution defeats dequantization; we construct the input and sweep its alignment, so
the question becomes empirical. [66] dequantizes diagonally weighted matrix functions — a matrix-function
construction rather than a kernel-regression comparison.

### 2.6 Classical kernel machinery and its quantum extensions (F)

The rival arms are drawn from this group, and the difference from our study is the same in every case: the
quantum part enters as a *family*, never as a geometry handed to the classical arm. [67] aligns a quantum kernel
with the target by stochastic gradient descent — alignment as an objective to be optimised, while we hold the
alignment as a swept property of the data. [68] shows manifold approximation leads to robust kernel alignment,
the classical result from which we take the reading that alignment is the axis that decides a kernel comparison.
[69] constructs feature maps for the Laplacian kernel and its generalisations, making graph-Laplacian metrics
classically explicit — which is what our matched rival exploits in the shifted convention. [70] unifies spectral
equivariance and geometric transport in reproducing kernel Hilbert spaces, a kernel-geometry framework that does
not carry a learning comparison. [71], [72] and [73] apply quantum multiple-kernel learning to drug discovery
(small-data ligand classification, Morgan-anchored hybrids, and a bottleneck-overcoming variant): multiple-kernel
combination is the technique in each, and the classical arm is a fixed family rather than a metric-matched rival.
[74] builds quantum-classical multiple-kernel learning in which the quantum part enters as an *additional kernel
family* — precisely the comparison design this study replaces. [75] explores an implementation of a quantum
learning pipeline for support vector machines, [76] applies quantum-kernel and HHL-based support vector machines
to multi-class classification with classical SVMs among the comparisons, and [77] uses quantum-kernel SVMs for
multispectral satellite cloud detection with a classical SVM baseline: implementations and applications, none with
a metric-matched arm. [78] estimates the number of shots quantum-kernel methods need — a sampling-cost analysis,
which is the cost axis our reproduction spec reports rather than the statistical one. [79] proposes a
resource-efficient quantum kernel, where the resource is qubits and gates. [80] and [81] review quantum kernel
methods as a class and the non-variational subfamily respectively; the former names the matched comparison as
open, which is the gap this paper fills. [82] benchmarks quantum-*inspired* feature maps against their classical
counterparts under a matched *spectral* design: this is the closest prior comparison in the literature, and the
difference is exact — it matches the spectral description of a quantum-inspired map, while we hand the quantum
map's own fitted metric to the rival and sweep the target's alignment to it.

### 2.7 Random features and kernel approximations (G)

This group supplies the *control* that the field's residual advantages rest on. [83] analyses the Nyström
approximation for preconditioning in kernel machines and [84] randomises clustered Nyström for scale: classical
approximation schemes whose error is analysed for a fixed kernel, not against a quantum arm. [85] reduces the
variance of random-feature couplings and [86] constructs simplex random features — refinements of the surrogate
family that our random-feature arm is drawn from. [87] shows all random-feature representations are equivalent:
an equivalence that explains *why* a random-feature rival cannot exploit a specific geometry, and therefore why
the advantages measured against it are not about geometry. [88] studies random features and polynomial rules —
a spectral analysis of the approximation family. [89] frames quantum random features as a spectral framework for
quantum machine learning; a spectral view with no matched rival. [90] estimates dynamic models by matching random
features — an econometric matching argument that supports our use of a matching construction rather than a
tuned one. [91] gives a scalable Nyström-based kernel two-sample test with permutations, cited for the resampling
discipline our paired intervals follow. [92] uses graph random features for scalable Gaussian processes, a
scalability result in the baseline family we tune against. [93] develops random features for Grassmannian kernels,
showing that geometry-aware classical approximations exist for specific geometries — the observation that makes
"the classical family cannot see this geometry" a claim requiring an argument rather than an assumption.

### 2.8 The statistics of comparison (H)

The study's inference rests on this group. [94] regularises cross-validation for stability — a selection-side
remedy, whereas our protocol *fixes* the selection rule and reports its consequences. [95] tests predictive
performance with exhaustive nested cross-validation, the procedure our envelope grid is nested inside.
[96] calibrates multiple testing without labels, which is the shape of our calibrated predictive null.
[97] unifies conformalised multiple testing with full data efficiency — the family of procedures our declaration
step belongs to. [98] controls the false discovery rate through a bandit formulation, an online method from which
our fixed-grid FDR control is the offline special case. [99] gives lower bounds in multiple testing through
derandomised proxies: it bounds what any procedure of our kind can detect, which is the resolution floor we report
beside every count. [100] derives Bentkus-type asymptotic e-values, the modern alternative to the p-value
calibration our null uses. [101] gives dynamic algorithms for online multiple testing; our grid is fixed before
the run, which is why a fixed-grid procedure applies. [102] proposes a robust multiple-testing method that
leverages ancillary information — a shrinkage-style improvement whose failure mode (misleading ancillary
information) is why we do not borrow strength across bands. [103] learns hyperparameters by bilevel optimisation,
cited for the nested protocol our rival's envelope grid implements.

### 2.9 Model selection and tuning bias (I)

The single most load-bearing methodological decision in this study is that every arm is tuned by the same
protocol, because the alternative converts a hyperparameter into the finding. [104] shows structured features
overfit where random features grok — a mechanism for why a rival's family choice interacts with the data's
structure, and why a fixed envelope would have manufactured the result. [105] balances expressivity and
overfitting in quantum Gaussian-process regression, a single-model balance with no rival receiving the map's
metric. [106] introduces manifold random features, a classical construction that makes a data-geometry-aware
rival available outside the quantum literature — and one our matched rival must therefore beat, not merely
differ from. [107] applies quantum-enhanced manifold learning to anomaly recognition with an unmatched classical
comparison; [108] builds a hybrid pipeline for parity-structured classification with quantum kernels — a pipeline
for one structure, whereas our generator sweeps the structure; and [109] designs structured quantum kernels for
chaotic forecasting, evaluated against classical forecasters of a different family. [110] derives barren plateaus
from learning scramblers with local cost functions (the variational mechanism behind our large-bandwidth reading),
and [111] trains quantum kernels with quantum neural networks, moving the map to improve performance where we fix
the map and compare geometry.

### 2.10 Quantum computation: background and hardware (J)

These establish what our claims are *not* about. [112] estimates expectation values efficiently with extended
stabilizer frameworks and adaptive variance estimation: how cheaply a quantity can be estimated, not what a
learning outcome is worth. [113] certifies quantum advantage robustly against loopholes — the certification
standard our controlled comparison is not a substitute for. [114] studies quantum advantage in tolerant junta
testing, a query-complexity separation of a different kind from a learning comparison. [115] characterises the
power of *noisy* quantum kernels and [118] studies noisy quantum kernel machines: noise is their axis, and our
study is noiseless by construction, which is what makes the metric computable and the comparison exact.
[116] solves differential equations with quantum kernel methods against numerical baselines, and [117] uses
non-classically simulable feature maps chosen for hardness. [119] builds a compact quantum kernel-based binary
classifier for near-term hardware, and [121] applies quantum machine learning to cyber-physical anomaly detection
in unmanned aerial vehicles: hardware-oriented and application-oriented constructions, each evaluated against a
classical family. [120] studies Fisher-efficiency transitions for non-unitary quantum machine learning, an
information-theoretic transition cited as an example of a quantum-side statistic that is not an advantage over a
matched classical model.

### 2.11 Exact simulation and its cost (K)

The instrument's cost is part of its evidence. [122] compares array frameworks for quantum-circuit simulation,
the runtime axis our reproduction specification reports. [123] simulates observable quantum dynamics on dynamic
subspaces and [124] prepares tensor-network states with belief-propagation disentanglers: fast-simulation and
state-preparation techniques that bound the cost of exact statevector simulation at the qubit counts we use, and
are the reason q ≤ 8 is the honest ceiling for a full-grid panel here rather than a choice of convenience.

### 2.12 The classical and statistical spine

Beyond the quantum literature, the study's instrument is assembled from classical results, and they are cited for
the component each supplies rather than as prior comparisons. The paired-testing protocol comes from [126], which
compares classifiers over multiple data sets with paired tests, and from [130], which gives the small-sample
paired statistic and its distribution that the panel's t intervals use; [127] measures the bias cross-validation
introduces when it is *also* used for selection, which is the bias the rival's nested protocol is designed to
avoid. The declaration step uses the false-discovery-rate procedure of [128] and its dependency-corrected
extension [129] (our grid's tests are dependent by construction). The case for controlled generators over
observational data is [131]'s argument for algorithmic modelling, and the reason a comparison must name the
geometry it is about is [132]'s result that no learner is a priori superior without assumptions on the problem
distribution; [133] is the early statement that a nonparametric fit's *bandwidth* decides its behaviour, which is
the axis our map is drawn over.

The kernel machinery itself: [134] establishes the theory of reproducing kernels, the framework in which a kernel
*is* a metric and therefore the framework that makes a metric-matched rival definable; [135] sets out kernel
methods as a design discipline; [136] gives the positive-definiteness condition our rival metrics must satisfy; and
[137] introduces the kernel trick, the construction that separates a geometry from a hypothesis class. The
classifier family our arms are scored inside is [138]. Kernel *parameters* as the object of learning enter with
[139], which chooses multiple parameters by gradient descent on a generalisation bound, and [140], which learns a
combination of kernels through conic duality — the multiple-kernel setting in which a rival's metric is chosen
rather than inherited, and the reason our rival is *given* the metric instead. [141] and [142] are classical uses
of a kernel's geometry (kernel principal component analysis; natural-gradient learning) cited to show that
exploiting a metric is not a quantum privilege. The baseline claim is not confined to kernel machines: [143] and
[144] supply two tree-family baselines, and [145] a conventional neural baseline, so that "the geometry explains
the outcome" is not an artefact of comparing kernels with kernels. [146] is why the reported metric is excess risk
against the Bayes predictor rather than an ROC-style summary; [147] is the capacity view that motivates a
controlled generator with a known Bayes risk; [148] and [149] are estimation-theory landmarks cited to mark how
far a fitted-metric rival is from a learned representation.

Finally, the field's setting and the background of its claims: [150] describes the NISQ era whose constraints the
field's advantage claims are made under, and [151] the universal quantum computer whose abstraction the study's
simulator implements; [152] frames quantum machine learning as a discipline, and [153] is the experiment that
established the quantum-kernel protocol this paper's comparison corrects. [154] places machine learning in feature
Hilbert spaces, the formal setting in which a feature map *is* a kernel; [155] analyses the power of quantum
kernels in the NISQ era and shows where classical data defeats them, stated as an argument rather than a swept
map; [156] demonstrates an advantage of a different kind (sample access) whose separation from a statistical
advantage this paper's design enforces; [158] introduces quantum convolutional neural networks and [161] an
accelerated variational eigensolver, so that the map is not read as a statement about variational architectures
generally; [160] applies quantum machine learning to quantum anomaly detection, an early kernel application
compared against classical kernels of another family. Three entries are cited as *instances of a practice rather
than as comparisons*: [162] is a simulation environment for compartmental neuron models, cited as an example of a
computational tool whose reproducibility rests on a declared environment; [163] introduces Laplacian eigenmaps,
whose graph-Laplacian operator is the classical object our closed-form rival's metric is built from; [164] is a
latent-structure method cited as an example of a model whose geometry is assumed rather than measured;
[165] supplies a capacity-controlled classifier cited for the envelope discipline every arm is tuned under;
[166] delimits what a supervised comparison may infer about unsupervised structure; [167] is a term-selection
study in information retrieval, cited as the method this package's reference search does *not* use (its record set
is read from a registry rather than assembled from citation terms); [168] self-tests entangled states — the kind
of certification guarantee a statistical advantage claim does not carry; and [169] simulates imaginary-time
evolution with a variational ansatz, cited as background for the ansatz-based maps this study deliberately does
not use, so that the map's scope is stated by what it excludes.
