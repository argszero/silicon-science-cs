#!/usr/bin/env python3
"""#87 R404 -- the bibliography's selection: which record carries which claim, and the one-line difference.

This file is the AUTHORED part of the bibliography: one entry per work, keyed by its record identifier
(arXiv id or DOI), with the one-line stated difference the journal's presentation rules require. Nothing here
is generated: the record's own fields (authors, year, title, venue, URL) are resolved by `refs_build_v87.py`
from the committed pools and re-read from the index by `refs_verify_v87.py`, so a mistyped identifier fails a
control instead of entering the list.

Ordering is the bibliography's order, which is the manuscript's order of first citation:
  A  the advantage claim and its audits            G  random features and approximations
  B  quantum-kernel theory and closed forms        H  statistics of comparison
  C  feature maps, encoding and geometry           I  model selection and tuning bias
  D  trainability, concentration and collapse      J  quantum computation: background and hardware
  E  dequantization and classical simulability     K  exact simulation and its cost
  F  classical kernel machinery
"""

ARXIV = [
    # ---- A  the advantage claim and its audits
    ("2608.18155", "Benchmarks quantum models against tuned classical ones under a calibration- and "
                   "noise-aware attribution protocol; its surviving advantages are measured against a "
                   "random-feature surrogate, and no rival receives the quantum map's own geometry."),
    ("2409.04406", "Audits quantum-kernel methods as a family across datasets and reports where they fail; "
                   "it compares kernel families rather than matching one rival to the quantum metric, "
                   "and sweeps no alignment axis."),
    ("2607.20168", "Documents a vanishing advantage on a financial cross-section and attributes it to the "
                   "data; we hold the data-generating process fixed and sweep the alignment between the "
                   "target's interaction structure and the map's."),
    ("2604.24597", "Finds a quantum-kernel advantage inside frozen foundation-model embeddings, measured "
                   "against classical kernels of a different metric rather than a rival built to "
                   "receive the quantum geometry."),
    ("2607.15815", "Argues from a Fourier-frequency argument that public tabular data cannot support "
                   "quantum advantage and offers a recipe; the claim is about datasets, ours is about "
                   "where a matched rival is beaten on a controlled generator."),
    ("2608.15617", "Shows evaluation choices (splits, calibration, metrics) decide the reported outcome in "
                   "one application domain; we fix the protocol and vary the geometry, and the package "
                   "records the choices so they can be re-read."),
    ("2604.18837", "Benchmarks quantum-kernel SVMs against classical baselines on tabular data with a "
                   "tuned but unmatched classical arm, so a better geometry and a quantum geometry are "
                   "not separated."),
    ("2608.27764", "Compares quantum feature-encoding strategies with a QSVM on a binary task; encoding "
                   "is varied at fixed data, whereas our design varies the data-side alignment against "
                   "a fixed encoding family."),
    ("2603.09901", "Asks whether quantum advantage has been achieved and reviews the evidence; a review "
                   "of claims, with no controlled instrument able to falsify a specific advantage "
                   "mechanism."),
    ("2603.18825", "Reads quantum advantage through tensor networks and identifies where classical "
                   "representations suffice; it speaks to simulability, not to the test error of a "
                   "quantum kernel against a matched rival."),
    ("2607.07927", "Builds invariance audits for quantum kernels and a real-to-Hermitian taxonomy; the "
                   "audit tests invariances of a map, while our question is whether the map beats a "
                   "rival that inherits its metric."),
    ("2608.12712", "Gives a closed-form benchmark for fixed-map denoising networks; a closed form for a "
                   "different task family, with no paired rival and no swept data-side axis."),
    ("2607.04915", "Stress-tests variational models on a cloud-microphysics dataset and finds the "
                   "advantage hard to reach; a single-domain stress test rather than a map over a "
                   "controlled grid with a matched rival."),
    ("2601.22194", "Evaluates quantum-kernel methods on noisy radar data against classical kernels, with "
                   "no metric-matched surrogate and no planted alignment."),
    ("2508.05720", "Surveys the varieties of quantum advantage and their resource requirements; it "
                   "catalogues advantage claims rather than testing one under a matched-rival "
                   "protocol."),
    ("2606.00932", "Learns in active quantum subspaces for a scalable hybrid advantage; the advantage "
                   "comes from restricting the subspace, a mechanism our grid does not vary."),
    ("2609.21243", "Separates trainability diagnostics from optimization claims and states which controls "
                   "variational quantum studies owe; those controls are for optimization landscapes, "
                   "and we adopt the lesson for a regression comparison instead."),
    ("2602.16097", "Mitigates exponential concentration with local and multi-scale strategies; a remedy "
                   "for kernel degeneracy, while we ask what the degeneracy does to a comparison "
                   "against a matched rival."),

    # ---- B  quantum-kernel theory and closed forms
    ("2608.29422", "Proves the ZZ feature map's kernel is an anisotropic Gaussian whose metric is the "
                   "identity plus the signless Laplacian of the entanglement graph, and gives a "
                   "closed-form classical surrogate; it reports two dataset points and states the "
                   "failing regime only qualitatively, whereas we map the advantage over alignment and "
                   "bandwidth with that surrogate as the rival."),
    ("2609.00475", "Predicts quantum-kernel collapse from the data's fractal dimension and gives a "
                   "ceiling as a qubit budget; it predicts kernel death, not the sign of the advantage "
                   "against a matched rival, which is our outcome."),
    ("2503.20683", "Reads quantum kernels as entangled tensor kernels and unifies several map families; a "
                   "representational identity, with no paired comparison against a rival holding the "
                   "same metric."),
    ("2606.20402", "Shows quantum kernels are spectral tensor networks with a controlled bond dimension; "
                   "a simulability construction, which we read as a mechanism witness rather than as a "
                   "rival arm."),
    ("2311.13552", "Unifies trace-induced quantum kernels into one framework; the framework makes the "
                   "map's form explicit but measures no advantage against a metric-matched classical "
                   "kernel."),
    ("2106.03747", "Shows quantum kernels carry an inductive bias aligned with the group structure of the "
                   "data; the bias is demonstrated at fixed bandwidth, and our grid sweeps bandwidth "
                   "and phase convention as well."),
    ("2604.15214", "Gives the optimal algorithmic complexity of inference in quantum-kernel methods; a "
                   "complexity statement about sampling, not a statistical comparison of test error."),
    ("2510.11744", "Develops convergence theory and separation bounds for quantum-kernel methods; the "
                   "bounds are asymptotic and no finite-sample map of the advantage region is "
                   "exhibited."),
    ("2004.03489", "Establishes a theory of the quantum kernel-based binary classifier, including its "
                   "consistency; a fixed-map theory with no rival that receives the map's metric."),
    ("2309.14419", "Shows which kernels are expressible by embedding quantum kernels and where they gain; "
                   "expressivity of the map at one bandwidth, rather than advantage against a matched "
                   "rival."),
    ("2506.03779", "Argues quantum kernel machines should move beyond scalar-valued kernels; a position "
                   "about the class of kernels, while our question is whether a scalar-valued quantum "
                   "kernel beats its metric-matched counterpart."),
    ("2602.01330", "Simulates quantum-classical dual kernels with tensor networks at scale; a simulation "
                   "result bounding what can be simulated, not what a rival attains."),
    ("2604.17202", "Reports double descent in quantum kernel ridge regression; the curve runs over model "
                   "complexity at one geometry, whereas we fix complexity and sweep alignment."),
    ("2501.10077", "Finds double descent in quantum kernel methods and locates its onset; a "
                   "complexity-axis result rather than an alignment-axis map."),
    ("2503.17020", "Establishes benign overfitting for quantum kernels; a generalisation result under an "
                   "assumption on the kernel, with no empirical advantage boundary."),
    ("2605.31449", "Constructs a scalable quantum kernel inside an SVM; scalability of the map, with the "
                   "comparison against a tuned but unmatched classical arm."),
    ("2407.15961", "Benchmarks quantum fidelity kernels inside Gaussian-process regression; the rival is "
                   "a classical GP kernel family, not a surrogate built from the quantum metric."),
    ("2512.20567", "Places quantum kernels inside a radial-basis-function network and classifies; an "
                   "architecture choice, and the classical arm receives no part of the quantum "
                   "geometry."),

    # ---- C  feature maps, encoding and geometry
    ("2509.02795", "Studies geodesics of quantum feature maps on the space of operators; the geometry of "
                   "the map as a manifold, while our question is what that geometry buys against a rival "
                   "that is given it."),
    ("2606.05387", "Surveys quantum feature encoding with practical guidelines; a survey of choices, with "
                   "no controlled comparison against a metric-matched rival."),
    ("2505.14295", "Benchmarks data-encoding methods for quantum machine learning over datasets; encoding "
                   "families are compared with each other, and the classical arm is unmatched."),
    ("2105.11853", "Searches for quantum embeddings that improve a downstream model; a search over maps "
                   "with the classical rival held fixed across the search."),
    ("2503.14062", "Compares data-encoding schemes for variational circuits and proposes a hybrid; the "
                   "target is classification accuracy of one circuit family, not the advantage's "
                   "boundary."),
    ("2609.08058", "Sets out the theory and practice of quantum data encoding; a treatment of encodings as "
                   "objects, without a paired rival that inherits an encoding's metric."),
    ("2609.04652", "Meta-learns encoding selection for quantum-kernel methods; selection among encodings, "
                   "where we instead sweep the data-side alignment at a fixed encoding and qubit "
                   "count."),
    ("2506.21161", "Designs hardware-aware quantum kernels with graph neural networks; the objective is "
                   "hardware performance, and no metric-matched classical arm is fitted."),
    ("2209.05142", "Studies the role of entanglement for enhancing quantum kernels in classification; the "
                   "entanglement axis is varied, while we ask whether the resulting geometry can be "
                   "given to the rival."),
    ("2607.12487", "Benchmarks loss functions for trainable quantum feature maps; a training-side "
                   "comparison, whereas our comparison is between a map and a rival at matched "
                   "capacity."),
    ("2602.16266", "Gives structured unitary tensor-network representations for circuit-efficient data "
                   "encoding; a construction that lowers encoding cost, with no advantage claim and no "
                   "rival."),
    ("2607.13847", "Proposes a quantum topological data encoding; a new encoding whose evaluation is "
                   "against classical topological descriptors, not against a metric-matched kernel."),
    ("2410.22084", "Analyses encoding of real-world data through feature maps and expanded "
                   "pseudo-entropy; a diagnostic of encodings, with no advantage boundary and no "
                   "matched-rival protocol."),
    ("2508.07104", "Searches for efficient quantum feature maps with an evolutionary, training-free "
                   "procedure; the search is over maps, and the comparison is not against a rival "
                   "given the chosen map's metric."),
    ("2608.08433", "Argues the input side is a permanent bottleneck for quantum machine learning; a "
                   "position about data rather than a measurement of where a matched rival is beaten."),

    # ---- D  trainability, concentration and collapse
    ("2208.11060", "Proves exponential concentration of quantum kernels and ties it to the map's "
                   "geometry; concentration is the ceiling our large-bandwidth arm observes, and we "
                   "read its effect on the comparison rather than on trainability."),
    ("2501.07433", "Establishes an equivalence between exponential concentration in quantum-kernel "
                   "machine learning and barren plateaus in variational models; a theoretical "
                   "equivalence, with no rival arm and no swept alignment."),
    ("2609.04462", "Gives a representation-theoretic framework that characterises barren plateaus; a "
                   "characterisation of when gradients vanish, not of when a kernel loses to a "
                   "matched rival."),
    ("2607.24014", "Studies trainability, expressivity and efficiency together for scalable quantum "
                   "machine learning; the axes are the model's own, whereas our axes are the data-side "
                   "alignment and the encoding bandwidth."),
    ("2512.04861", "Proves concentration bounds for intrinsic-dimension estimation with Gaussian "
                   "kernels; a classical-kernel concentration result that bounds the behaviour of our "
                   "isotropic baseline arm."),
    ("1909.03347", "Shows concentration of kernel matrices and applies it to spectral clustering; the "
                   "concentration is of a classical kernel matrix as the sample grows, whereas ours is "
                   "over the map's phase convention and bandwidth at fixed n."),
    ("2607.11174", "Uses Lie-algebraic subspace quantization to mitigate barren plateaus and enable "
                   "zero-shot learning; a mitigation technique whose benefit is measured inside the "
                   "variational setting, not against a matched classical rival."),
    ("2509.14337", "Builds trainable kernels for symmetry-structured data without exponential "
                   "concentration; it shows concentration is avoidable by construction, which supports "
                   "reading our large-bandwidth arm as a genuine collapse rather than a protocol "
                   "artefact."),

    # ---- E  dequantization and classical simulability
    ("2505.15902", "Dequantizes supervised quantum machine learning with random Fourier features; the "
                   "dequantization targets worst-case complexity, while we ask about average test error "
                   "under a rival that holds the map's own metric."),
    ("2503.23931", "Dequantizes variational quantum machine learning kernel-based, without random Fourier "
                   "features; a complexity statement, and the resulting classical model is not fitted "
                   "to the quantum metric in our sense."),
    ("2309.11647", "States the potential and the limitations of random Fourier features for dequantizing "
                   "quantum machine learning; it bounds what a specific classical family can do, not "
                   "what a metric-matched kernel does."),
    ("2304.04932", "Robustly dequantizes the quantum singular-value transformation and quantum machine "
                   "learning algorithms; an algorithmic dequantization, with no comparison of kernel "
                   "test error."),
    ("2307.06937", "Dequantizes quantum machine learning models with tensor networks; the surrogate is a "
                   "tensor network, a different rival family from the closed-form metric-matched "
                   "surrogate we use."),
    ("2405.13273", "Studies dequantizability from inputs; it asks when an input distribution defeats "
                   "dequantization, whereas we construct the input and the rival ourselves so the "
                   "comparison is exact."),
    ("2609.10729", "Dequantizes diagonally weighted matrix functions in a quantum-inspired way; a "
                   "matrix-function construction rather than a kernel-regression comparison."),

    # ---- F  classical kernel machinery and its quantum extensions
    ("2304.09899", "Aligns a quantum kernel with the target by stochastic gradient descent; alignment is "
                   "an objective to be optimised, while we hold the map fixed and measure what its "
                   "geometry is worth against a rival given it."),
    ("2510.22953", "Shows manifold approximation leads to robust kernel alignment; a classical alignment "
                   "result we use to argue that alignment is the right axis for a comparison."),
    ("2502.15575", "Constructs feature maps for the Laplacian kernel and its generalisations; it makes "
                   "graph-Laplacian metrics classically explicit, which is the construction our "
                   "closed-form rival needs."),
    ("2512.13073", "Unifies spectral equivariance and geometric transport in reproducing kernel Hilbert "
                   "spaces; a framework for kernels' geometry, with no quantum counterpart arm."),
    ("2506.14920", "Applies quantum multiple-kernel learning to drug discovery; multiple-kernel "
                   "combination is the technique, and the classical arm is not given the combined "
                   "metric."),
    ("2606.21213", "Combines classical Morgan fingerprints with quantum multiple-kernel learning for "
                   "ligand classification; the hybrid's gain is measured inside one application and "
                   "against unmatched classical kernels."),
    ("2607.11701", "Overcomes classical bottlenecks in drug discovery with quantum multiple-kernel "
                   "learning; a domain application whose classical arm does not receive the quantum "
                   "metric."),
    ("2305.17707", "Builds quantum-classical multiple-kernel learning; the quantum part enters as an "
                   "additional kernel family, which is precisely the setup our matched rival isolates."),
    ("2509.04983", "Explores an implementation of a quantum learning pipeline for support vector "
                   "machines; an implementation study, with a tuned classical SVM rather than a "
                   "metric-matched rival."),
    ("2509.10190", "Applies quantum kernel and HHL-based support vector machines to multi-class "
                   "classification; the comparison includes classical SVMs but no surrogate holding "
                   "the quantum metric."),
    ("2307.07281", "Uses quantum-kernel SVMs for multispectral satellite cloud detection; an application "
                   "with a classical SVM baseline, and no geometry-matched control."),
    ("2407.15776", "Estimates the number of shots needed by quantum-kernel methods in search of "
                   "advantage; a sampling-cost analysis rather than a test-error comparison against a "
                   "matched rival."),
    ("2507.03689", "Proposes a resource-efficient quantum kernel; the resource is qubits and gates, while "
                   "our resource question is whether the geometric information is separable from the "
                   "quantum construction."),
    ("2405.01780", "Reviews quantum kernel methods as a class and their relation to classical kernels; a "
                   "review that names the matched comparison as open, which our study performs."),
    ("2604.07896", "Reviews non-variational supervised quantum-kernel methods; a survey of the family "
                   "without a controlled advantage map."),
    ("2605.24324", "Benchmarks quantum-inspired feature maps against their classical counterparts under a "
                   "matched spectral design; the closest prior control, but the maps are "
                   "quantum-inspired classical embeddings, not entangling quantum kernels with a "
                   "phase-convention axis."),

    # ---- G  random features and kernel approximations
    ("2312.03311", "Uses the Nyström approximation for preconditioning in kernel machines; a classical "
                   "approximation scheme whose error is analysed for a fixed kernel, not compared with "
                   "a quantum map."),
    ("1612.06470", "Randomises clustered Nyström for large-scale kernel machines; a scaling technique "
                   "whose target is runtime, not advantage."),
    ("2405.16541", "Reduces the variance of random-feature couplings; a refinement of the classical "
                   "surrogate family that the field's residual advantages are usually measured "
                   "against."),
    ("2301.13856", "Constructs simplex random features with lower variance; another refinement of the "
                   "weak surrogate, and we include the family as our weak-rival control."),
    ("2406.18802", "Shows all random-feature representations are equivalent; the equivalence explains "
                   "why a random-feature rival cannot exploit a specific geometry, which is why our "
                   "headline rival is not of that family."),
    ("2402.10164", "Studies random features and polynomial rules; a spectral analysis of an "
                   "approximation family, with no quantum arm."),
    ("2601.21746", "Frames quantum random features as a spectral framework for quantum machine learning; "
                   "a spectral view of quantum maps, with no matched-rival comparison of test error."),
    ("2607.21916", "Estimates dynamic models by matching random features; an econometric matching "
                   "argument that supports our use of a matching construction for the rival's metric."),
    ("2502.13570", "Gives a scalable Nyström-based kernel two-sample test with permutations; a classical "
                   "testing instrument, cited for the resampling practice our protocol follows."),
    ("2509.03691", "Uses graph random features for scalable Gaussian processes; a classical scalability "
                   "result for the baseline family we tune against the quantum maps."),
    ("2504.21533", "Develops random features for Grassmannian kernels; a geometry-specific classical "
                   "approximation, cited to show that geometry-aware classical constructions are "
                   "available outside the quantum setting."),

    # ---- H  statistics of comparison
    ("2505.06927", "Regularises cross-validation for stability; a selection-side remedy, whereas our "
                   "protocol fixes the selection rule and reports the comparison's uncertainty."),
    ("2408.03138", "Tests predictive performance with exhaustive nested cross-validation for "
                   "high-dimensional data; a testing procedure, which we cite for the nested-CV "
                   "discipline our rival's tuning follows."),
    ("2606.19737", "Calibrates multiple testing without labels; a calibration method for testing "
                   "procedures, related to our null calibration but not to the kernel comparison."),
    ("2508.12085", "Unifies conformalised multiple testing with full data efficiency; a testing "
                   "framework, cited for the family of procedures our declaration rule belongs to."),
    ("1809.02235", "Controls the false discovery rate through a bandit formulation; an online "
                   "multiple-testing method, from which our fixed-grid FDR control differs by design."),
    ("2005.03725", "Gives lower bounds in multiple testing through derandomised proxies; it bounds what "
                   "any procedure of our kind can detect, which is why we report the declaration "
                   "count's saturation as a finding."),
    ("2606.06332", "Derives Bentkus-type asymptotic e-values; a calibration result for e-value tests, "
                   "cited as the modern alternative to the p-value layer we use."),
    ("2010.13953", "Gives dynamic algorithms for online multiple testing; an online setting, whereas our "
                   "grid is fixed before the run."),
    ("2409.03618", "Proposes a robust multiple-testing method that leverages ancillary information; a "
                   "shrinkage-style improvement, which we cite for why null calibration matters in our "
                   "own predictive null."),
    ("2510.05568", "Bilevel optimisation for learning hyperparameters; a joint tuning scheme, cited for "
                   "the nested protocol our rival's envelope grid follows."),

    # ---- I  model selection and tuning bias
    ("2609.15047", "Shows structured features overfit where random features grok; a mechanism for why a "
                   "rival's family choice interacts with the data's structure, which our grid "
                   "controls."),
    ("2609.09407", "Balances expressivity and overfitting in quantum Gaussian-process regression; a "
                   "single-model balance, with no rival receiving the model's metric."),
    ("2602.03797", "Introduced manifold random features; a classical construction that makes a "
                   "data-geometry-aware rival available outside the quantum setting."),
    ("2512.11071", "Applies quantum-enhanced manifold learning to anomaly recognition; an application "
                   "whose classical comparison is unmatched."),
    ("2605.05625", "Builds a hybrid pipeline for parity-structured classification with quantum kernels; a "
                   "pipeline for one structure, whereas our generator sweeps the alignment between "
                   "structure and map."),
    ("2609.13360", "Designs structured quantum kernels for chaotic forecasting; a forecasting task whose "
                   "evaluation is against classical forecasters with different capacity."),
    ("2205.06679", "Derives barren plateaus from learning scramblers with local cost functions; a "
                   "variational mechanism result cited for why our large-bandwidth arm is read as "
                   "collapse rather than as a tuning failure."),
    ("2401.04642", "Trains quantum kernels with quantum neural networks; it moves the map to improve "
                   "performance, while we fix the map and compare against a rival built from its "
                   "metric."),

    # ---- J  quantum computation: background and hardware
    ("2609.14252", "Estimates expectation values efficiently with extended stabilizer frameworks and "
                   "adaptive variance estimation; it measures how cheaply a quantum model can be "
                   "evaluated, not how it compares with a matched classical rival."),
    ("2607.13090", "Certifies quantum advantage robustly against loopholes; a certification protocol "
                   "for advantage claims, cited as the standard our controlled comparison is not."),
    ("2606.23194", "Studies quantum advantage in tolerant junta testing; a query-complexity separation, "
                   "which is an advantage of a different kind from the statistical one we map."),
    ("2401.17526", "Characterises the power of noisy quantum kernels; noise is the axis, and our study "
                   "is noiseless by construction, so it isolates the geometric question."),
    ("2203.08884", "Solves differential equations with quantum kernel methods; a solver application whose "
                   "classical comparison is a numerical baseline, not a matched kernel."),
    ("2103.11381", "Uses non-classically simulable feature maps in hybrid quantum-classical "
                   "architectures; the map is chosen for hardness, whereas we choose maps we can read "
                   "exactly so the geometry is computable."),
    ("2204.12192", "Studies noisy quantum kernel machines; a noise-focused study, cited because our "
                   "noiseless design is what makes the metric computable in closed form."),
    ("2202.02151", "Builds a compact quantum kernel-based binary classifier for near-term hardware; a "
                   "hardware-oriented construction evaluated against unmatched classical baselines."),
    ("2603.27377", "Studies Fisher efficiency transitions for non-unitary quantum machine learning; an "
                   "information-theoretic transition, cited as an example of a boundary derived rather "
                   "than mapped."),
    ("2605.19233", "Applies quantum machine learning to cyber-physical anomaly detection in unmanned "
                   "aerial vehicles; an application whose evaluation varies many factors at once."),

    # ---- K  exact simulation and its cost
    ("2609.19147", "Compares array frameworks for quantum-circuit simulation; a runtime comparison of "
                   "simulators, which is the cost axis our reproduction spec reports honestly."),
    ("2609.09806", "Simulates observable quantum dynamics on dynamic subspaces; a fast-simulation "
                   "technique that bounds the cost of the exact statevector path we use at q <= 8."),
    ("2608.21902", "Prepares tensor-network states with belief-propagation disentanglers; a state "
                   "preparation technique, cited as an alternative to exact statevector simulation."),
    ("2512.13548", "Formulates dequantized algorithms in tensor-network language; a formulation that "
                   "explains when classical simulation is exact, which our closed-form rival does for "
                   "the small-bandwidth regime."),
]

# ---- DOI entries: the classical and statistical spine, every one read at the registry the round queried
CROSSREF = [
    ("10.1162/089976698300017197", "Compares supervised classifiers over multiple data sets with "
                                   "paired tests and recommends a procedure; a testing protocol, where "
                                   "our contribution is the map of a comparison's outcome rather than "
                                   "a test for it."),
    ("10.1186/1471-2105-7-91", "Measures the bias that cross-validation introduces when it is also used "
                               "for selection; the bias our rival's nested protocol is designed to "
                               "remove, cited as the reason the nested grid is part of the rival "
                               "definition."),
    ("10.1111/j.2517-6161.1995.tb02031.x", "Introduces the false discovery rate and the Benjamini-"
                                           "Hochberg procedure; the declaration rule we apply to our "
                                           "grid before any lead is announced."),
    ("10.1214/aos/1013699998", "Extends false-discovery control to dependent test statistics; the "
                               "dependency our grid's tests have by construction, which is why the "
                               "control is reported with its structure rather than as a bare count."),
    ("10.1093/biomet/6.1.1", "Gives the small-sample paired statistic and its distribution; the "
                             "t-interval we report per cell across the stream panel."),
    ("10.1214/ss/1009213726", "Argues for the algorithmic-modelling culture against the data-modelling "
                              "one; the argument for controlled generators, which is the design this "
                              "study uses."),
    ("10.1162/neco.1996.8.7.1341", "Shows no learner is a priori superior without assumptions on the "
                                   "problem distribution; the reason a comparison must name the "
                                   "geometry it holds fixed, as ours does."),
    ("10.1080/01621459.1979.10481038", "Introduces locally weighted regression and its smoothing "
                                       "parameter; an early statement that a nonparametric fit's "
                                       "bandwidth decides its behaviour, the axis our grid sweeps for "
                                       "the quantum map."),
    ("10.21236/ada296533", "Establishes the theory of reproducing kernels; the framework in which a "
                           "kernel is a metric, which is what makes a metric-matched rival meaningful."),
    ("10.1017/CBO9780511809682", "Sets out kernel methods for pattern analysis as a design discipline; "
                                 "the classical toolbox our rival arms are drawn from."),
    ("10.1098/rspa.1909.0075", "Gives the positive-definite condition for a function to be a kernel; the "
                               "condition our rival metrics must satisfy for the comparison to be "
                               "between kernels at all."),
    ("10.1145/130385.130401", "Introduces the kernel trick for optimal margin classifiers; the "
                              "construction that makes a geometry and a hypothesis class separable "
                              "questions."),
    ("10.1023/A:1022627411411", "Introduces support-vector networks with soft margins; the classifier "
                                "family our arms are scored inside, through kernel ridge regression "
                                "with a linear readout."),
    ("10.1023/A:1012450327387", "Chooses multiple kernel parameters by gradient descent on a "
                                "generalisation bound; an early statement that kernel parameters are "
                                "themselves a fitting problem, which our nested envelope grid "
                                "implements."),
    ("10.1145/1015330.1015424", "Learns a combination of kernels through conic duality; the "
                                "multiple-kernel setting in which a rival's metric is chosen rather "
                                "than given, cited to delimit what our fixed-metric rival claims."),
    ("10.1162/089976698300017467", "Introduces kernel principal component analysis; a classical use of "
                                   "a kernel's geometry, cited to show that geometry exploitation is "
                                   "not peculiar to the quantum setting."),
    ("10.1162/089976698300017746", "Introduces natural-gradient learning; the geometry-aware "
                                   "optimisation idea that our rival's metric-matching transfers to "
                                   "regression."),
    ("10.1023/A:1010933404324", "Introduces random forests; a strong classical baseline of a different "
                                "family, included so the manuscript's baseline claim is not confined "
                                "to kernel machines."),
    ("10.1007/s10994-006-6226-1", "Introduces extremely randomized trees; a second tree-family "
                                  "baseline, cited for the same reason as random forests."),
    ("10.1109/5.726791", "Applies gradient-based learning to document recognition; a reference for the "
                          "conventional machine-learning baselines a kernel comparison should "
                          "acknowledge."),
    ("10.1145/1143844.1143874", "Relates precision-recall and ROC curves; the reason our reported "
                                 "metric is excess risk against the Bayes predictor rather than an "
                                 "accuracy curve."),
    ("10.1007/978-3-319-21852-6_3", "States the uniform convergence of empirical frequencies used "
                                     "throughout learning theory; the capacity view that motivates "
                                     "controlling the rival's envelope grid."),
    ("10.1214/aos/1176346060", "Proves convergence properties of the EM algorithm; a classical "
                                "estimation-theory landmark, cited to mark how far a fitted-metric "
                                "rival is from a construction with a closed-form metric."),
    ("10.1038/323533a0", "Shows learning by back-propagation; the historical baseline that motivates "
                          "holding capacity fixed across the arms of a comparison."),
    ("10.22331/q-2018-08-06-79", "Describes the NISQ era and its constraints; the hardware setting the "
                                 "field's advantage claims are made in, and the reason an exactly "
                                 "simulated comparison is informative."),
    ("10.1098/rspa.1985.0070", "States the universal quantum computer and its relation to the "
                                "Church-Turing principle; the foundational statement of what a quantum "
                                "computation is."),
    ("10.1038/nature23474", "Surveys quantum machine learning as a discipline; the field-level framing "
                             "our matched-rival comparison argues within."),
    ("10.1038/s41586-019-0980-2", "Demonstrates supervised learning with quantum-enhanced feature "
                                   "spaces on hardware; the experiment that established the "
                                   "quantum-kernel advantage claim our study subjects to a matched "
                                   "rival."),
    ("10.1103/PhysRevLett.122.040504", "Puts quantum machine learning in feature Hilbert spaces; the "
                                        "formal setting in which a feature map is a kernel, which our "
                                        "instrument computes exactly."),
    ("10.22331/q-2021-08-30-531", "Analyses the power of quantum kernels in the NISQ era and shows "
                                   "where classical data defeats them; the closest prior argument, "
                                   "stated for specific constructions rather than as a mapped "
                                   "advantage region."),
    ("10.1126/science.abn7293", "Demonstrates quantum advantage in learning from experiments; an "
                                 "advantage of a different kind (sample access), cited to separate it "
                                 "from the test-error advantage we map."),
    ("10.1103/PhysRevX.11.041011", "Shows barren plateaus are absent in quantum convolutional neural "
                                    "networks with local cost functions; the architectural escape "
                                    "from collapse, cited against our large-bandwidth arm."),
    ("10.1038/s41567-019-0648-8", "Introduces quantum convolutional neural networks; a variational "
                                   "architecture, included so the manuscript's map is not read as a "
                                   "statement about all quantum models."),
    ("10.1038/s41467-024-49287-w", "Shows exponential concentration in quantum kernel methods and ties "
                                    "it to the kernel's spectrum; the concentration result our "
                                    "large-bandwidth arm reproduces as a comparison outcome."),
    ("10.1103/PhysRevA.97.042315", "Applies quantum machine learning to quantum anomaly detection; an "
                                    "early kernel application whose comparison is against classical "
                                    "kernels of a different metric."),
    ("10.1103/PhysRevLett.122.140504", "Accelerates the variational quantum eigensolver; an optimisation "
                                        "result, cited to contrast optimisation gains with the "
                                        "statistical comparison this study makes."),
    ("10.1162/089976600300015475", "Describes a simulation environment for compartmental neuron models; "
                                    "a computational-neuroscience tool, cited only as an instance of "
                                    "the simulator-versus-model distinction our threats section "
                                    "draws."),
    ("10.1162/089976603321780317", "Introduces Laplacian eigenmaps; a spectral embedding whose "
                                    "graph-Laplacian operator is the classical object our "
                                    "closed-form rival's metric is built from."),
    ("10.1007/BF02289343", "Develops confirmatory maximum-likelihood factor analysis; a "
                            "latent-structure method, cited as an example of a model whose geometry is "
                            "fixed by construction rather than fitted."),
    ("10.1109/TPAMI.2005.127", "Gives sparse multinomial logistic regression with fast algorithms; a "
                                "capacity-controlled classifier, cited for the envelope discipline our "
                                "rival's grid imposes."),
    ("10.1145/1143844.1143977", "Learns structured predictors discriminatively and without labels; a "
                                 "semi-supervised construction, cited to delimit what our supervised "
                                 "comparison covers."),
    ("10.1007/978-3-540-78646-7_21", "Uses citation terms for information retrieval; a "
                                      "term-selection study, cited as the method this package's "
                                      "reference search does not use."),
    ("10.1103/PhysRevA.105.032416", "Self-tests multipartite entangled states; a certification "
                                     "protocol for entanglement, cited as the kind of guarantee that "
                                     "a statistical advantage claim does not by itself carry."),
    ("10.1038/s41534-019-0187-2", "Simulates imaginary-time evolution with a variational ansatz; a "
                                   "variational quantum algorithm, cited as background for the "
                                   "ansatz-based maps our grid does not use."),
]
