# Reference authenticity check -- issue #126

Every entry **cited by the manuscript** was checked against a LIVE external record, comparing
the returned TITLE against the stored title (two-sided token match, threshold 0.80).  A
resolver that merely answers is not enough: a remembered identifier can resolve to a
DIFFERENT real paper, so the check is the title comparison, not the HTTP status.

- sources: arXiv API `id_list` (batched, `max_results` set per chunk) + Crossref `works/<doi>`
- verified pool: 337 entries; **cited by the manuscript: 107** (91 arXiv, 16 Crossref)
- last full pass: 2026-10-07T03:03:46Z  rc=0  VERIFIED 337 / 337 ; TITLE MISMATCH 0 ; TRANSPORT-UNKNOWN 0 (batches failed: 0)
- an entry is dropped, never kept, if its title does not match; the manuscript may cite only
  pool entries, so the list below is a subset of the verified pool by construction

| ref | citation key | source | verified against | title as returned | link |
|-----|--------------|--------|------------------|-------------------|------|
| [1] | `doi:10.1007/bf01397083` | crossref | Crossref works/<doi> | A floating-point technique for extending the available precision | https://doi.org/10.1007/bf01397083 |
| [2] | `arxiv:2504.08009` | arxiv | arXiv id_list | Ozaki Scheme II: A GEMM-oriented emulation of floating-point matrix multiplication using an integer modular technique | https://arxiv.org/abs/2504.08009 |
| [3] | `arxiv:2608.06812` | arxiv | arXiv id_list | DGEMM with Ozaki Scheme I/II on FP4 Tensor Cores: A Base-13 E2M1 Limb Representation | https://arxiv.org/abs/2608.06812 |
| [4] | `doi:10.1137/17m1140819` | crossref | Crossref works/<doi> | Accelerating the Solution of Linear Systems by Iterative Refinement in Three Precisions | https://doi.org/10.1137/17m1140819 |
| [5] | `doi:10.1137/1.9780898718027` | crossref | Crossref works/<doi> | Accuracy and Stability of Numerical Algorithms | https://doi.org/10.1137/1.9780898718027 |
| [6] | `doi:10.1137/1.9781611977523` | crossref | Crossref works/<doi> | Rounding Errors in Algebraic Processes | https://doi.org/10.1137/1.9781611977523 |
| [7] | `doi:10.1137/18m1226312` | crossref | Crossref works/<doi> | A New Approach to Probabilistic Rounding Error Analysis | https://doi.org/10.1137/18m1226312 |
| [8] | `arxiv:2404.12556` | arxiv | arXiv id_list | Bias- and Variance-Aware Probabilistic Rounding Error Analysis for Floating-Point Arithmetic | https://arxiv.org/abs/2404.12556 |
| [9] | `arxiv:2411.18747` | arxiv | arXiv id_list | Deterministic and Probabilistic Rounding Error Analysis for Mixed-Precision Arithmetic on Modern Computing Units | https://arxiv.org/abs/2411.18747 |
| [10] | `arxiv:2109.01232` | arxiv | arXiv id_list | A Study of Mixed Precision Strategies for GMRES on GPUs | https://arxiv.org/abs/2109.01232 |
| [11] | `arxiv:2107.06200` | arxiv | arXiv id_list | Multistage Mixed Precision Iterative Refinement | https://arxiv.org/abs/2107.06200 |
| [12] | `arxiv:2609.24519` | arxiv | arXiv id_list | AWE: Adaptive Weight Encoding for Exact Integer Matrix Products with Fewer GEMMs on FP4 Tensor Cores | https://arxiv.org/abs/2609.24519 |
| [13] | `arxiv:2203.15928` | arxiv | arXiv id_list | Precision-aware Deterministic and Probabilistic Error Bounds for Floating Point Summation | https://arxiv.org/abs/2203.15928 |
| [14] | `arxiv:2607.14742` | arxiv | arXiv id_list | Newton-Based Mixed Precision Iterative Refinement for Large-Scale Sparse Continuous-Time Algebraic Riccati Equations | https://arxiv.org/abs/2607.14742 |
| [15] | `arxiv:2007.06674` | arxiv | arXiv id_list | A Survey of Numerical Methods Utilizing Mixed Precision Arithmetic | https://arxiv.org/abs/2007.06674 |
| [16] | `arxiv:2506.11728` | arxiv | arXiv id_list | The Cambrian Explosion of Mixed-Precision Matrix Multiplication for Quantized Deep Learning Inference | https://arxiv.org/abs/2506.11728 |
| [17] | `doi:10.1145/363707.363723` | crossref | Crossref works/<doi> | Pracniques: further remarks on reducing truncation errors | https://doi.org/10.1145/363707.363723 |
| [18] | `doi:10.1137/030601818` | crossref | Crossref works/<doi> | Accurate Sum and Dot Product | https://doi.org/10.1137/030601818 |
| [19] | `doi:10.1137/s1064827502407627` | crossref | Crossref works/<doi> | Accurate and Efficient Floating Point Summation | https://doi.org/10.1137/s1064827502407627 |
| [20] | `doi:10.1137/080738490` | crossref | Crossref works/<doi> | Ultimately Fast Accurate Summation | https://doi.org/10.1137/080738490 |
| [21] | `doi:10.1137/20m1334796` | crossref | Crossref works/<doi> | Stochastic Rounding and Its Probabilistic Backward Error Analysis | https://doi.org/10.1137/20m1334796 |
| [22] | `arxiv:2107.01604` | arxiv | arXiv id_list | Deterministic and Probabilistic Error Bounds for Floating Point Summation Algorithms | https://arxiv.org/abs/2107.01604 |
| [23] | `arxiv:2607.18758` | arxiv | arXiv id_list | A Second-Moment Theory for Floating-Point Reduction Trees | https://arxiv.org/abs/2607.18758 |
| [24] | `doi:10.1137/17m1122918` | crossref | Crossref works/<doi> | A New Analysis of Iterative Refinement and Its Application to Accurate Solution of Ill-Conditioned Sparse Linear Systems | https://doi.org/10.1137/17m1122918 |
| [25] | `arxiv:2201.09827` | arxiv | arXiv id_list | Mixed Precision GMRES-based Iterative Refinement with Recycling | https://arxiv.org/abs/2201.09827 |
| [26] | `arxiv:2202.10204` | arxiv | arXiv id_list | Mixed Precision Iterative Refinement with Sparse Approximate Inverse Preconditioning | https://arxiv.org/abs/2202.10204 |
| [27] | `arxiv:2307.03914` | arxiv | arXiv id_list | Mixed Precision Iterative Refinement with Adaptive Precision Sparse Approximate Inverse Preconditioning | https://arxiv.org/abs/2307.03914 |
| [28] | `arxiv:2401.03755` | arxiv | arXiv id_list | Mixed Precision FGMRES-Based Iterative Refinement for Weighted Least Squares | https://arxiv.org/abs/2401.03755 |
| [29] | `arxiv:2406.16499` | arxiv | arXiv id_list | Mixed precision iterative refinement for least squares with linear equality constraints and generalized least squares problems | https://arxiv.org/abs/2406.16499 |
| [30] | `arxiv:2409.08335` | arxiv | arXiv id_list | Mixed precision iterative refinement for linear inverse problems | https://arxiv.org/abs/2409.08335 |
| [31] | `arxiv:2501.04229` | arxiv | arXiv id_list | Three-precision iterative refinement with parameter regularization and prediction for solving large sparse linear systems | https://arxiv.org/abs/2501.04229 |
| [32] | `arxiv:2408.13400` | arxiv | arXiv id_list | Iterative Refinement with Low-Precision Posits | https://arxiv.org/abs/2408.13400 |
| [33] | `arxiv:2401.17957` | arxiv | arXiv id_list | Avoiding breakdown in incomplete factorizations in low precision arithmetic | https://arxiv.org/abs/2401.17957 |
| [34] | `arxiv:2403.13123` | arxiv | arXiv id_list | Developing robust incomplete Cholesky factorizations in half precision arithmetic | https://arxiv.org/abs/2403.13123 |
| [35] | `arxiv:2106.09877` | arxiv | arXiv id_list | HIFIR: Hybrid Incomplete Factorization with Iterative Refinement for Preconditioning Ill-conditioned and Singular Systems | https://arxiv.org/abs/2106.09877 |
| [36] | `arxiv:2103.07329` | arxiv | arXiv id_list | XAMG: A library for solving linear systems with multiple right-hand side vectors | https://arxiv.org/abs/2103.07329 |
| [37] | `arxiv:2509.09139` | arxiv | arXiv id_list | Hybrid-Precision Block-Jacobi Preconditioned GMRES Solver for Linear System in Circuit Simulation | https://arxiv.org/abs/2509.09139 |
| [38] | `arxiv:2208.01907` | arxiv | arXiv id_list | A Hybrid Factorization Algorithm for Sparse Matrix with Mixed Precision Arithmetic | https://arxiv.org/abs/2208.01907 |
| [39] | `arxiv:2412.08059` | arxiv | arXiv id_list | Parameter optimization for restarted mixed precision iterative sparse solver | https://arxiv.org/abs/2412.08059 |
| [40] | `arxiv:2512.21164` | arxiv | arXiv id_list | Mixed Precision General Alternating-Direction Implicit Method for Solving Large Sparse Linear Systems | https://arxiv.org/abs/2512.21164 |
| [41] | `arxiv:2410.06319` | arxiv | arXiv id_list | Mixed precision sketching for least-squares problems and its application in GMRES-based iterative refinement | https://arxiv.org/abs/2410.06319 |
| [42] | `arxiv:2209.04626` | arxiv | arXiv id_list | A mixed precision Jacobi SVD algorithm | https://arxiv.org/abs/2209.04626 |
| [43] | `arxiv:2607.12430` | arxiv | arXiv id_list | A mixed precision algorithm for the matrix square root | https://arxiv.org/abs/2607.12430 |
| [44] | `arxiv:2503.03456` | arxiv | arXiv id_list | Mixed-precision algorithms for solving the Sylvester matrix equation | https://arxiv.org/abs/2503.03456 |
| [45] | `arxiv:2510.02126` | arxiv | arXiv id_list | Mixed-precision iterative refinement for low-rank Lyapunov equations | https://arxiv.org/abs/2510.02126 |
| [46] | `arxiv:2007.06614` | arxiv | arXiv id_list | Algebraic error analysis for mixed-precision multigrid solvers | https://arxiv.org/abs/2007.06614 |
| [47] | `arxiv:2307.00216` | arxiv | arXiv id_list | Rounding-Error Analysis of Multigrid V-Cycles | https://arxiv.org/abs/2307.00216 |
| [48] | `arxiv:2410.12614` | arxiv | arXiv id_list | Mixed-precision finite element kernels and assembly: Rounding error analysis and hardware acceleration | https://arxiv.org/abs/2410.12614 |
| [49] | `arxiv:2609.37844` | arxiv | arXiv id_list | Running error bounds in finite element kernels | https://arxiv.org/abs/2609.37844 |
| [50] | `arxiv:2602.14450` | arxiv | arXiv id_list | Mixed precision solvers with half-precision floating point numbers for Lattice QCD on A64FX processor | https://arxiv.org/abs/2602.14450 |
| [51] | `arxiv:0911.3191` | arxiv | arXiv id_list | Solving Lattice QCD systems of equations using mixed precision solvers on GPUs | https://arxiv.org/abs/0911.3191 |
| [52] | `arxiv:2404.19163` | arxiv | arXiv id_list | Efficient Mixed-Precision Matrix Factorization of the Inverse Overlap Matrix in Electronic Structure Calculations with AI-Hardware and GPUs | https://arxiv.org/abs/2404.19163 |
| [53] | `arxiv:2107.02737` | arxiv | arXiv id_list | Quantum-based Molecular Dynamics Simulations Using Tensor Cores | https://arxiv.org/abs/2107.02737 |
| [54] | `arxiv:2203.09621` | arxiv | arXiv id_list | Quantum perturbation theory using Tensor cores and a deep neural network | https://arxiv.org/abs/2203.09621 |
| [55] | `arxiv:2510.23621` | arxiv | arXiv id_list | Speeding Up MACE: Low-Precision Tricks for Equivarient Force Fields | https://arxiv.org/abs/2510.23621 |
| [56] | `arxiv:2207.14598` | arxiv | arXiv id_list | Climate Change Modelling at Reduced Float Precision with Stochastic Rounding | https://arxiv.org/abs/2207.14598 |
| [57] | `arxiv:0812.2976` | arxiv | arXiv id_list | Parallel Algorithm for Solving Kepler's Equation on Graphics Processing Units: Application to Analysis of Doppler Exoplanet Searches | https://arxiv.org/abs/0812.2976 |
| [58] | `arxiv:2306.03737` | arxiv | arXiv id_list | orbitN: A symplectic integrator for planetary systems dominated by a central mass -- Insight into long-term solar system chaos | https://arxiv.org/abs/2306.03737 |
| [59] | `arxiv:1812.08011` | arxiv | arXiv id_list | Training Deep Neural Networks with 8-bit Floating Point Numbers | https://arxiv.org/abs/1812.08011 |
| [60] | `arxiv:1905.12322` | arxiv | arXiv id_list | A Study of BFLOAT16 for Deep Learning Training | https://arxiv.org/abs/1905.12322 |
| [61] | `arxiv:1905.12334` | arxiv | arXiv id_list | Mixed Precision Training With 8-bit Floating Point | https://arxiv.org/abs/1905.12334 |
| [62] | `arxiv:2010.06192` | arxiv | arXiv id_list | Revisiting BFloat16 Training | https://arxiv.org/abs/2010.06192 |
| [63] | `arxiv:2305.10947` | arxiv | arXiv id_list | Revisiting 16-bit Neural Network Training: A Practical Approach for Resource-Limited Learning | https://arxiv.org/abs/2305.10947 |
| [64] | `arxiv:2509.17791` | arxiv | arXiv id_list | Elucidating the Design Space of FP4 training | https://arxiv.org/abs/2509.17791 |
| [65] | `arxiv:2606.20381` | arxiv | arXiv id_list | Rethinking Shrinkage Bias in LLM FP4 Pretraining: Geometric Origin, Systemic Impact, and UFP4 Recipe | https://arxiv.org/abs/2606.20381 |
| [66] | `arxiv:2607.24953` | arxiv | arXiv id_list | Stable FP4 Training via Transposition-Invariant Block Quantization | https://arxiv.org/abs/2607.24953 |
| [67] | `arxiv:2601.22813` | arxiv | arXiv id_list | Quartet II: Accurate LLM Pre-Training in NVFP4 by Improved Unbiased Gradient Estimation | https://arxiv.org/abs/2601.22813 |
| [68] | `arxiv:2511.05811` | arxiv | arXiv id_list | MOSS: Efficient and Accurate FP8 LLM Training with Microscaling and Automatic Scaling | https://arxiv.org/abs/2511.05811 |
| [69] | `doi:10.1145/3480935` | crossref | Crossref works/<doi> | Ginkgo : A Modern Linear Operator Algebra Framework for High Performance Computing | https://doi.org/10.1145/3480935 |
| [70] | `arxiv:2508.00441` | arxiv | arXiv id_list | DGEMM without FP64 Arithmetic - Using FP64 Emulation and FP8 Tensor Cores with Ozaki Scheme | https://arxiv.org/abs/2508.00441 |
| [71] | `arxiv:2101.06584` | arxiv | arXiv id_list | Acceleration of multiple precision matrix multiplication based on multi-component floating-point arithmetic using AVX2 | https://arxiv.org/abs/2101.06584 |
| [72] | `arxiv:2606.25453` | arxiv | arXiv id_list | EmuGEMM: Fused Tensor Core Kernels for Precision Emulation in Matrix Multiplication | https://arxiv.org/abs/2606.25453 |
| [73] | `arxiv:2511.13778` | arxiv | arXiv id_list | Guaranteed DGEMM Accuracy While Using Reduced Precision Tensor Cores Through Extensions of the Ozaki Scheme | https://arxiv.org/abs/2511.13778 |
| [74] | `arxiv:2506.11277` | arxiv | arXiv id_list | Analysis of Floating-Point Matrix Multiplication Computed via Integer Arithmetic | https://arxiv.org/abs/2506.11277 |
| [75] | `arxiv:2406.02579` | arxiv | arXiv id_list | An Open-Source Framework for Efficient Numerically-Tailored Computations | https://arxiv.org/abs/2406.02579 |
| [76] | `arxiv:2607.11391` | arxiv | arXiv id_list | Performance evaluation of branch-free fused multiply-add algorithms for multi-component-type multiple-precision floating-point arithmetic | https://arxiv.org/abs/2607.11391 |
| [77] | `doi:10.7717/peerj-cs.330` | crossref | Crossref works/<doi> | Numerical behavior of NVIDIA tensor cores | https://doi.org/10.7717/peerj-cs.330 |
| [78] | `arxiv:2512.07004` | arxiv | arXiv id_list | Accurate Models of NVIDIA Tensor Cores | https://arxiv.org/abs/2512.07004 |
| [79] | `arxiv:2511.10909` | arxiv | arXiv id_list | Bit-Accurate Modeling of GPU Matrix Multiply-Accumulate Units: Demystifying Numerical Discrepancy and Accuracy | https://arxiv.org/abs/2511.10909 |
| [80] | `arxiv:2206.02874` | arxiv | arXiv id_list | Dissecting Tensor Cores via Microbenchmarks: Latency, Throughput and Numeric Behaviors | https://arxiv.org/abs/2206.02874 |
| [81] | `arxiv:1803.04014` | arxiv | arXiv id_list | NVIDIA Tensor Core Programmability, Performance & Precision | https://arxiv.org/abs/1803.04014 |
| [82] | `arxiv:2609.11356` | arxiv | arXiv id_list | Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification | https://arxiv.org/abs/2609.11356 |
| [83] | `arxiv:2403.00232` | arxiv | arXiv id_list | FTTN: Feature-Targeted Testing for Numerical Properties of NVIDIA & AMD Matrix Accelerators | https://arxiv.org/abs/2403.00232 |
| [84] | `arxiv:1901.06015` | arxiv | arXiv id_list | Supporting mixed-datatype matrix multiplication within the BLIS framework | https://arxiv.org/abs/1901.06015 |
| [85] | `arxiv:2306.11975` | arxiv | arXiv id_list | DGEMM on Integer Matrix Multiplication Unit | https://arxiv.org/abs/2306.11975 |
| [86] | `arxiv:1808.10387` | arxiv | arXiv id_list | Compensated de Casteljau algorithm in $K$ times the working precision | https://arxiv.org/abs/1808.10387 |
| [87] | `arxiv:1306.2392` | arxiv | arXiv id_list | Practical Implementation of High-Order Multiple Precision Fully Implicit Runge-Kutta Methods with Step Size Control Using Embedded Formula | https://arxiv.org/abs/1306.2392 |
| [88] | `arxiv:2601.00728` | arxiv | arXiv id_list | Precision autotuning for linear solvers via contextual bandit-based RL | https://arxiv.org/abs/2601.00728 |
| [89] | `arxiv:2504.14268` | arxiv | arXiv id_list | Mixed-Precision Conjugate Gradient Solvers with RL-Driven Precision Tuning | https://arxiv.org/abs/2504.14268 |
| [90] | `arxiv:2609.24509` | arxiv | arXiv id_list | Error Analysis and Precision Selection for Mixed-Precision DEIM-CUR Decompositions | https://arxiv.org/abs/2609.24509 |
| [91] | `arxiv:2603.20421` | arxiv | arXiv id_list | Hawkeye: Reproducing GPU-Level Non-Determinism | https://arxiv.org/abs/2603.20421 |
| [92] | `arxiv:2005.07282` | arxiv | arXiv id_list | Reproducibility of Parallel Preconditioned Conjugate Gradient in Hybrid Programming Environments | https://arxiv.org/abs/2005.07282 |
| [93] | `arxiv:2207.03837` | arxiv | arXiv id_list | The Positive Effects of Stochastic Rounding in Numerical Algorithms | https://arxiv.org/abs/2207.03837 |
| [94] | `arxiv:2010.16225` | arxiv | arXiv id_list | Effects of round-to-nearest and stochastic rounding in the numerical solution of the heat equation in low precision | https://arxiv.org/abs/2010.16225 |
| [95] | `arxiv:2202.12276` | arxiv | arXiv id_list | On the influence of stochastic roundoff errors and their bias on the convergence of the gradient descent method with low-precision floating-point computation | https://arxiv.org/abs/2202.12276 |
| [96] | `arxiv:2410.10517` | arxiv | arXiv id_list | Stochastic Rounding 2.0, with a View towards Complexity Analysis | https://arxiv.org/abs/2410.10517 |
| [97] | `arxiv:2603.06060` | arxiv | arXiv id_list | What is New in Stochastic Rounding: a Survey on Theory, Hardware, and Applications | https://arxiv.org/abs/2603.06060 |
| [98] | `arxiv:2006.00489` | arxiv | arXiv id_list | Improved stochastic rounding | https://arxiv.org/abs/2006.00489 |
| [99] | `arxiv:2504.20634` | arxiv | arXiv id_list | On Stochastic Rounding with Few Random Bits | https://arxiv.org/abs/2504.20634 |
| [100] | `arxiv:2408.03069` | arxiv | arXiv id_list | Probabilistic error analysis of limited-precision stochastic rounding | https://arxiv.org/abs/2408.03069 |
| [101] | `arxiv:2207.10321` | arxiv | arXiv id_list | Stochastic rounding variance and probabilistic bounds: A new approach | https://arxiv.org/abs/2207.10321 |
| [102] | `arxiv:2411.13601` | arxiv | arXiv id_list | Error Analysis of Sum-Product Algorithms under Stochastic Rounding | https://arxiv.org/abs/2411.13601 |
| [103] | `arxiv:2404.14010` | arxiv | arXiv id_list | A Stochastic Rounding-Enabled Low-Precision Floating-Point MAC for DNN Training | https://arxiv.org/abs/2404.14010 |
| [104] | `doi:10.1098/rsos.211631` | crossref | Crossref works/<doi> | Stochastic rounding: implementation, error analysis and applications | https://doi.org/10.1098/rsos.211631 |
| [105] | `doi:10.1145/2049662.2049663` | crossref | Crossref works/<doi> | The university of Florida sparse matrix collection | https://doi.org/10.1145/2049662.2049663 |
| [106] | `doi:10.1109/sc.2018.00050` | crossref | Crossref works/<doi> | Harnessing GPU Tensor Cores for Fast FP16 Arithmetic to Speed up Mixed-Precision Iterative Refinement Solvers | https://doi.org/10.1109/sc.2018.00050 |
| [107] | `arxiv:2609.37137` | arxiv | arXiv id_list | Mixed-Precision Computing for Scientific Discovery: Formats, Co-Design, and Responsible Approximation | https://arxiv.org/abs/2609.37137 |
