# Reference pool -- issue #139

Every entry below was discovered by `refscan139.py` (never typed from memory) and checked
against a LIVE external record by comparing the returned TITLE with the stored title
(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a
remembered identifier can resolve to a DIFFERENT real paper, so the check is the title
comparison, not the HTTP status.

- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with
  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)
  and `works/<doi>` (verification)
- pool: 288 entries (277 arXiv, 11 Crossref)
- an entry whose title does not match its live record is dropped, never kept

| key | source | verified against | title |
|-----|--------|------------------|-------|
| 0907.1357 | arxiv | arXiv id_list | Graph Based Reduction of Program Verification Conditions |
| 10.1007/978-1-4612-6315-9_9 | crossref | Crossref works/<doi> | An Axiomatic Basis for Computer Programming |
| 10.1007/978-3-540-78800-3_24 | crossref | Crossref works/<doi> | Z3: An Efficient SMT Solver |
| 10.1007/978-3-642-17511-4_20 | crossref | Crossref works/<doi> | Dafny: An Automatic Program Verifier for Functional Correctness |
| 10.1007/978-3-642-37036-6_8 | crossref | Crossref works/<doi> | Why3 — Where Programs Meet Provers |
| 10.1007/s10817-009-9155-4 | crossref | Crossref works/<doi> | A Formally Verified Compiler Back-end |
| 10.1007/s10817-013-9286-5 | crossref | Crossref works/<doi> | Premise Selection for Mathematics by Corpus Analysis and Kernel Methods |
| 10.1007/s10817-020-09580-x | crossref | Crossref works/<doi> | TacticToe: Learning to Prove with Tactics |
| 10.1145/1629575.1629596 | crossref | Crossref works/<doi> | seL4: formal verification of an OS kernel |
| 10.1145/357073.357079 | crossref | Crossref works/<doi> | Simplification by Cooperating Decision Procedures |
| 10.1145/3611643.3616243 | crossref | Crossref works/<doi> | Baldur: Whole-Proof Generation and Repair with Large Language Models |
| 10.52202/068431-1910 | crossref | Crossref works/<doi> | HyperTree Proof Search for Neural Theorem Proving |
| 1106.1372 | arxiv | arXiv id_list | Phase Selection Heuristics for Satisfiability Solvers |
| 1210.6857 | arxiv | arXiv id_list | The Geometry of Types (Long Version) |
| 1403.2628 | arxiv | arXiv id_list | Interaction and Depth against Nondeterminism in Proof Search |
| 1410.5467 | arxiv | arXiv id_list | Machine Learning of Coq Proof Guidance: First Experiments |
| 1508.03894 | arxiv | arXiv id_list | An experimental Study using ACSL and Frama-C to formulate and verify Low-Level Requirements from |
| 1508.06827 | arxiv | arXiv id_list | On Deciding Local Theory Extensions via E-matching |
| 1509.03534 | arxiv | arXiv id_list | Premise Selection and External Provers for HOL4 |
| 1607.07797 | arxiv | arXiv id_list | Combined Top-Down and Bottom-Up Approaches to Performance-guaranteed Integrated Task and Motion  |
| 1702.01332 | arxiv | arXiv id_list | Manyopt: An Extensible Tool for Mixed, Non-Linear Optimization Through SMT Solving |
| 1704.07935 | arxiv | arXiv id_list | Z3str3: A String Solver with Theory-aware Branching |
| 1707.02115 | arxiv | arXiv id_list | A Verified Certificate Checker for Finite-Precision Error Bounds in Coq and HOL4 |
| 1804.02503 | arxiv | arXiv id_list | Symbolic Reasoning for Automatic Signal Placement (Extended Version) |
| 1809.05959 | arxiv | arXiv id_list | Lazy Modeling of Variants of Token Swapping Problem and Multi-agent Path Finding through Combina |
| 1811.00796 | arxiv | arXiv id_list | Automated Theorem Proving in Intuitionistic Propositional Logic by Deep Reinforcement Learning |
| 1811.10814 | arxiv | arXiv id_list | Lightweight Interactive Proving inside an Automatic Program Verifier |
| 1811.10818 | arxiv | arXiv id_list | Experience Report on Formally Verifying Parts of OpenJDK's API with KeY |
| 1901.05456 | arxiv | arXiv id_list | TrABin: Trustworthy Analyses of Binaries |
| 1903.03182 | arxiv | arXiv id_list | ENIGMA-NG: Efficient Neural and Gradient-Boosted Inference Guidance for E |
| 1904.03241 | arxiv | arXiv id_list | HOList: An Environment for Machine Learning of Higher-Order Theorem Proving |
| 1905.09381 | arxiv | arXiv id_list | Learning to Prove Theorems via Interacting with Proof Assistants |
| 1905.10501 | arxiv | arXiv id_list | Learning to Reason in Large Theories without Imitation |
| 1907.07794 | arxiv | arXiv id_list | Generating Correctness Proofs with Neural Networks |
| 1908.01979 | arxiv | arXiv id_list | Non-Invasive Reverse Engineering of Finite State Machines Using Power Analysis and Boolean Satis |
| 1909.09137 | arxiv | arXiv id_list | Bayesian Optimisation with Gaussian Processes for Premise Selection |
| 1910.11797 | arxiv | arXiv id_list | Deep Reinforcement Learning for Synthesizing Functions in Higher-Order Logic |
| 1911.02065 | arxiv | arXiv id_list | A Deep Reinforcement Learning Approach to First-Order Logic Theorem Proving |
| 2002.00423 | arxiv | arXiv id_list | An Experimental Study of Formula Embeddings for Automated Theorem Proving in First-Order Logic |
| 2003.07959 | arxiv | arXiv id_list | Learning Nonlinear Loop Invariants with Gated Continuous Logic Networks (Extended Version) |
| 2007.02559 | arxiv | arXiv id_list | Enhancing SAT solvers with glue variable predictions |
| 2008.10061 | arxiv | arXiv id_list | An Incremental Abstraction Scheme for Solving Hard SMT-Instances over Bit-Vectors |
| 2010.07253 | arxiv | arXiv id_list | An SMT Solver for Regular Expressions and Linear Arithmetic over String Length |
| 2010.10296 | arxiv | arXiv id_list | Definitional Quantifiers Realise Semantic Reasoning for Proof by Induction |
| 2102.06203 | arxiv | arXiv id_list | Proof Artifact Co-training for Theorem Proving with Language Models |
| 2102.09756 | arxiv | arXiv id_list | TacticZero: Learning to Prove Theorems from Scratch with Deep Reinforcement Learning |
| 2103.02209 | arxiv | arXiv id_list | SciviK: A Versatile Framework for Specifying and Verifying Smart Contracts |
| 2106.02550 | arxiv | arXiv id_list | Certified DQBF Solving by Definition Extraction |
| 2109.00110 | arxiv | arXiv id_list | MiniF2F: a cross-system benchmark for formal Olympiad-level mathematics |
| 2109.00542 | arxiv | arXiv id_list | Shared Certificates for Neural Network Verification |
| 2207.08775 | arxiv | arXiv id_list | Model Checking for Rectangular Hybrid Systems: A Quantified Encoding Approach |
| 2210.03590 | arxiv | arXiv id_list | Machine Learning Meets The Herbrand Universe |
| 2211.10219 | arxiv | arXiv id_list | Local Search For Satisfiability Modulo Integer Arithmetic Theories |
| 2211.10675 | arxiv | arXiv id_list | Proceedings 9th Workshop on Horn Clauses for Verification and Synthesis and 10th International W |
| 2212.08578 | arxiv | arXiv id_list | Provable Fairness for Neural Network Models using Formal Verification |
| 2301.13867 | arxiv | arXiv id_list | Mathematical Capabilities of ChatGPT |
| 2305.02521 | arxiv | arXiv id_list | Towards a Scalable Proof Engine: A Performant Prototype Rewriting Primitive for Coq |
| 2306.15626 | arxiv | arXiv id_list | LeanDojo: Theorem Proving with Retrieval-Augmented Language Models |
| 2309.12711 | arxiv | arXiv id_list | The Mathematical Game |
| 2309.15806 | arxiv | arXiv id_list | Lyra: Orchestrating Dual Correction in Automated Theorem Proving |
| 2310.04353 | arxiv | arXiv id_list | An In-Context Learning Agent for Formal Theorem-Proving |
| 2311.03739 | arxiv | arXiv id_list | Leveraging Large Language Models for Automated Proof Synthesis in Rust |
| 2311.03755 | arxiv | arXiv id_list | Multilingual Mathematical Autoformalization |
| 2312.14188 | arxiv | arXiv id_list | Enhancing Neural Theorem Proving through Data Augmentation and Dynamic Sampling Method |
| 2312.17353 | arxiv | arXiv id_list | Towards Auto-Modeling of Formal Verification for NextG Protocols: A Multimodal cross- and self-a |
| 2401.00963 | arxiv | arXiv id_list | Leveraging Large Language Models to Boost Dafny's Developers Productivity |
| 2401.02950 | arxiv | arXiv id_list | The Tactician's Web of Large-Scale Formal Knowledge |
| 2401.14320 | arxiv | arXiv id_list | Quantifying Software Correctness by Combining Architecture Modeling and Formal Program Analysis |
| 2402.08957 | arxiv | arXiv id_list | MUSTARD: Mastering Uniform Synthesis of Theorem and Proof Data |
| 2403.04017 | arxiv | arXiv id_list | Learning Guided Automated Reasoning: A Brief Survey |
| 2403.12627 | arxiv | arXiv id_list | Enhancing Formal Theorem Proving: A Comprehensive Dataset for Training AI Models on Coq Code |
| 2404.00762 | arxiv | arXiv id_list | Enchanting Program Specification Synthesis by Large Language Models using Static Analysis and Pr |
| 2404.09939 | arxiv | arXiv id_list | A Survey on Deep Learning for Theorem Proving |
| 2404.12534 | arxiv | arXiv id_list | Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean |
| 2405.02580 | arxiv | arXiv id_list | PropertyGPT: LLM-driven Formal Verification of Smart Contracts through Retrieval-Augmented Prope |
| 2405.14333 | arxiv | arXiv id_list | DeepSeek-Prover: Advancing Theorem Proving in LLMs through Large-Scale Synthetic Data |
| 2405.14414 | arxiv | arXiv id_list | Proving Theorems Recursively |
| 2405.17216 | arxiv | arXiv id_list | Autoformalizing Euclidean Geometry |
| 2406.06555 | arxiv | arXiv id_list | An Evaluation Benchmark for Autoformalization in Lean4 |
| 2406.07222 | arxiv | arXiv id_list | Reliable Evaluation and Benchmarks for Statement Autoformalization |
| 2406.11915 | arxiv | arXiv id_list | miniCodeProps: a Minimal Benchmark for Proving Code Properties |
| 2406.17762 | arxiv | arXiv id_list | Solving Hard Mizar Problems with Instantiation and Strategy Invention |
| 2406.18964 | arxiv | arXiv id_list | DNLSAT: A Dynamic Variable Ordering MCSAT Framework for Nonlinear Real Arithmetic |
| 2407.00695 | arxiv | arXiv id_list | Learning Formal Mathematics From Intrinsic Motivation |
| 2407.14521 | arxiv | arXiv id_list | Towards Automated Functional Equation Proving: A Benchmark Dataset and A Domain-Specific In-Cont |
| 2408.14017 | arxiv | arXiv id_list | Making Formulog Fast: An Argument for Unconventional Datalog Evaluation (Extended Version) |
| 2410.10135 | arxiv | arXiv id_list | FormalAlign: Automated Alignment Evaluation for Autoformalization |
| 2410.15748 | arxiv | arXiv id_list | Alchemy: Amplifying Theorem-Proving Capability through Symbolic Mutation |
| 2410.19940 | arxiv | arXiv id_list | Cobblestone: A Divide-and-Conquer Approach for Automating Formal Verification |
| 2410.22419 | arxiv | arXiv id_list | Towards SMT Solver Stability via Input Normalization |
| 2410.23493 | arxiv | arXiv id_list | Linear and non-linear relational analyses for Quantum Program Optimization |
| 2411.01829 | arxiv | arXiv id_list | Formal Theorem Proving by Rewarding LLMs to Decompose Proofs Hierarchically |
| 2411.10393 | arxiv | arXiv id_list | Guaranteed Bounds on Posterior Distributions of Discrete Probabilistic Programs with Loops |
| 2411.13627 | arxiv | arXiv id_list | CryptoFormalEval: Integrating LLMs and Formal Verification for Automated Cryptographic Protocol  |
| 2411.15143 | arxiv | arXiv id_list | dafny-annotator: AI-Assisted Verification of Dafny Programs |
| 2412.08805 | arxiv | arXiv id_list | Generative Agents for Multi-Agent Autoformalization of Interaction Scenarios |
| 2412.10483 | arxiv | arXiv id_list | Enhancing Automated Loop Invariant Generation for Complex Programs with Large Language Models |
| 2412.10657 | arxiv | arXiv id_list | Probabilistic Guarantees for Practical LIA Loop Invariant Automation |
| 2412.16058 | arxiv | arXiv id_list | SAT Solving for Variants of First-Order Subsumption |
| 2412.20735 | arxiv | arXiv id_list | HunyuanProver: A Scalable Data Synthesis Framework and Guided Tree Search for Automated Theorem  |
| 2501.17493 | arxiv | arXiv id_list | Certifying Pareto-Optimality in Multi-Objective Maximum Satisfiability |
| 2501.17766 | arxiv | arXiv id_list | Formally Verified Binary-level Pointer Analysis |
| 2501.18310 | arxiv | arXiv id_list | ProofAug: Efficient Neural Theorem Proving via Fine-grained Proof Structure Analysis |
| 2502.03438 | arxiv | arXiv id_list | BFS-Prover: Scalable Best-First Tree Search for LLM-based Automatic Theorem Proving |
| 2502.04671 | arxiv | arXiv id_list | ProofWala: A Framework for Multilingual Proof Data Synthesis and Theorem-Proving |
| 2502.05344 | arxiv | arXiv id_list | RAG-Verus: Repository-Level Program Verification with LLMs using Retrieval Augmented Generation |
| 2502.15795 | arxiv | arXiv id_list | Lean-ing on Quality: How High-Quality Data Beats Diverse Multilingual Data in AutoFormalization |
| 2502.17840 | arxiv | arXiv id_list | A Combinatorial Identities Benchmark for Theorem Proving via Automated Theorem Generation |
| 2502.17925 | arxiv | arXiv id_list | LeanProgress: Guiding Search for Neural Theorem Proving via Proof Progress Prediction |
| 2502.19963 | arxiv | arXiv id_list | Exploiting Partial-Assignment Enumeration in Optimization Modulo Theories |
| 2503.03205 | arxiv | arXiv id_list | MA-LoT: Model-Collaboration Lean-based Long Chain-of-Thought Reasoning enhances Formal Theorem P |
| 2503.09730 | arxiv | arXiv id_list | Local Look-Ahead Guidance via Verifier-in-the-Loop for Automated Theorem Proving |
| 2504.02246 | arxiv | arXiv id_list | C*: Unifying Programming and Verification in C |
| 2504.06122 | arxiv | arXiv id_list | Leanabell-Prover: Posttraining Scaling in Formal Reasoning |
| 2504.07642 | arxiv | arXiv id_list | Cache-a-lot: Pushing the Limits of Unsatisfiable Core Reuse in SMT-Based Program Analysis |
| 2504.21230 | arxiv | arXiv id_list | Kimina Lean Server: A High-Performance Lean Server for Large-Scale Verification |
| 2505.02735 | arxiv | arXiv id_list | FormalMATH: Benchmarking Formal Mathematical Reasoning of Large Language Models |
| 2505.03171 | arxiv | arXiv id_list | CombiBench: Benchmarking LLM Capability for Combinatorial Mathematics |
| 2505.04528 | arxiv | arXiv id_list | Beyond Theorem Proving: Formulation, Framework and Benchmark for Formal Problem-Solving |
| 2505.05758 | arxiv | arXiv id_list | APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning |
| 2505.10328 | arxiv | arXiv id_list | A Comparative Study of SMT and MILP for the Nurse Rostering Problem |
| 2505.10962 | arxiv | arXiv id_list | MPS-Prover: Advancing Stepwise Theorem Proving by Multi-Perspective Search and Data Curation |
| 2505.12031 | arxiv | arXiv id_list | LLM-based Automated Theorem Proving Hinges on Scalable Synthetic Data Generation |
| 2505.12680 | arxiv | arXiv id_list | Ineq-Comp: Benchmarking Human-Intuitive Compositional Reasoning in Automated Theorem Proving on  |
| 2505.13454 | arxiv | arXiv id_list | pyeb: A Python Implementation of Event-B Refinement Calculus |
| 2505.15740 | arxiv | arXiv id_list | HybridProver: Augmenting Theorem Proving with LLM-Driven Proof Synthesis and Refinement |
| 2505.15959 | arxiv | arXiv id_list | HornStr: Invariant Synthesis for Regular Model Checking as Constrained Horn Clauses(Technical Re |
| 2505.22846 | arxiv | arXiv id_list | RocqStar: Leveraging Similarity-driven Retrieval and Agentic Systems for Rocq generation |
| 2505.23311 | arxiv | arXiv id_list | Towards LLM-based Generation of Human-Readable Proofs in Polynomial Formal Verification |
| 2505.23754 | arxiv | arXiv id_list | DeepTheorem: Advancing LLM Reasoning for Theorem Proving Through Natural Language and Reinforcem |
| 2505.24230 | arxiv | arXiv id_list | ProofNet++: A Neuro-Symbolic System for Formal Proof Verification with Self-Correction |
| 2506.04592 | arxiv | arXiv id_list | Safe: Enhancing Mathematical Reasoning in Large Language Models via Retrospective Step-aware For |
| 2506.07047 | arxiv | arXiv id_list | Mathesis: Towards Formal Theorem Proving from Natural Languages |
| 2506.11487 | arxiv | arXiv id_list | Reviving DSP for Advanced Theorem Proving in the Era of Reasoning Models |
| 2506.19923 | arxiv | arXiv id_list | Prover Agent: An Agent-Based Framework for Formal Mathematical Proofs |
| 2506.22005 | arxiv | arXiv id_list | LeanConjecturer: Automatic Generation of Mathematical Conjectures for Theorem Proving |
| 2506.22370 | arxiv | arXiv id_list | Can Large Language Models Help Students Prove Software Correctness? An Experimental Study with D |
| 2507.02726 | arxiv | arXiv id_list | Bourbaki: Self-Generated and Goal-Conditioned MDPs for Theorem Proving |
| 2507.03659 | arxiv | arXiv id_list | Specification-Guided Repair of Arithmetic Errors in Dafny Programs using LLMs |
| 2507.06804 | arxiv | arXiv id_list | Towards Solving More Challenging IMO Problems via Decoupled Reasoning and Proving |
| 2507.07399 | arxiv | arXiv id_list | Generalized Tree Edit Distance (GTED): A Faithful Evaluation Metric for Statement Autoformalizat |
| 2507.14330 | arxiv | arXiv id_list | Leveraging LLMs for Formal Software Requirements -- Challenges and Prospects |
| 2507.15225 | arxiv | arXiv id_list | Solving Formal Math Problems by Decomposition and Iterative Reflection |
| 2507.16331 | arxiv | arXiv id_list | Re:Form -- Reducing Human Annotations in Scalable Formal Software Verification with RL in LLMs:  |
| 2507.18885 | arxiv | arXiv id_list | A Minimalist Proof Language for Neural Theorem Proving over Isabelle/HOL |
| 2507.20199 | arxiv | arXiv id_list | StepFun-Prover Preview: Let's Think and Verify Step by Step |
| 2508.02733 | arxiv | arXiv id_list | What's in a Proof? Analyzing Expert Proof-Writing Processes in F* and Verus |
| 2508.15878 | arxiv | arXiv id_list | Lean Meets Theoretical Computer Science: Scalable Synthesis of Theorem Proving Challenges in For |
| 2508.18798 | arxiv | arXiv id_list | CASP: An evaluation dataset for formal verification of C code |
| 2508.18914 | arxiv | arXiv id_list | FormaRL: Enhancing Autoformalization with no Labeled Data |
| 2508.20340 | arxiv | arXiv id_list | Once4All: Skeleton-Guided SMT Solver Fuzzing with LLM-Synthesized Generators |
| 2509.06493 | arxiv | arXiv id_list | Scaling up Multi-Turn Off-Policy RL and Multi-Agent Tree Search for LLM Step-Provers |
| 2509.06809 | arxiv | arXiv id_list | Saturation-Driven Dataset Generation for LLM Mathematical Reasoning in the TPTP Ecosystem |
| 2509.16237 | arxiv | arXiv id_list | parSAT: Parallel Solving of Floating-Point Satisfiability |
| 2509.22819 | arxiv | arXiv id_list | Hilbert: Recursively Building Formal Proofs with Informal Reasoning |
| 2509.23061 | arxiv | arXiv id_list | Local Success Does Not Compose: Benchmarking Large Language Models for Compositional Formal Veri |
| 2509.25197 | arxiv | arXiv id_list | Towards Repository-Level Program Verification with Large Language Models |
| 2510.02335 | arxiv | arXiv id_list | FormalML: A Benchmark for Evaluating Formal Subgoal Completion in Machine Learning Theory |
| 2510.06857 | arxiv | arXiv id_list | Autoformalizer with Tool Feedback |
| 2510.08988 | arxiv | arXiv id_list | MASA: LLM-Driven Multi-Agent Systems for Autoformalization |
| 2510.10131 | arxiv | arXiv id_list | Proof Strategy Extraction from LLMs for Enhancing Symbolic Provers |
| 2510.11225 | arxiv | arXiv id_list | A Theorem-Proving-Based Evaluation of Neural Semantic Parsing |
| 2510.12787 | arxiv | arXiv id_list | Ax-Prover: A Deep Reasoning Agentic Framework for Theorem Proving in Mathematics and Quantum Phy |
| 2510.15981 | arxiv | arXiv id_list | ProofFlow: A Dependency Graph Approach to Faithful Proof Autoformalization |
| 2510.17919 | arxiv | arXiv id_list | ParaVul: A Parallel Large Language Model and Retrieval-Augmented Framework for Smart Contract Vu |
| 2510.24592 | arxiv | arXiv id_list | ReForm: Reflective Autoformalization with Prospective Bounded Sequence Optimization |
| 2510.25427 | arxiv | arXiv id_list | RLMEval: Evaluating Research-Level Neural Theorem Proving |
| 2511.00125 | arxiv | arXiv id_list | Inferring multiple helper Dafny assertions with LLMs |
| 2511.10356 | arxiv | arXiv id_list | SITA: A Framework for Structure-to-Instance Theorem Autoformalization |
| 2511.11990 | arxiv | arXiv id_list | Improving Autoformalization Using Direct Dependency Retrieval |
| 2511.17330 | arxiv | arXiv id_list | Agentic Verification of Software Systems |
| 2511.18760 | arxiv | arXiv id_list | HERMES: Towards Efficient and Verifiable Mathematical Reasoning in LLMs |
| 2512.00997 | arxiv | arXiv id_list | IndiMathBench: Autoformalizing Mathematical Reasoning Problems with a Human Touch |
| 2512.15816 | arxiv | arXiv id_list | A Neurosymbolic Approach to Loop Invariant Generation via Weakest Precondition Reasoning |
| 2512.18256 | arxiv | arXiv id_list | MSC-180: A Benchmark for Automated Formal Theorem Proving from Mathematical Subject Classificati |
| 2512.23511 | arxiv | arXiv id_list | Beyond Correctness: Exposing LLM-generated Logical Flaws in Reasoning via Multi-step Automated T |
| 2512.24379 | arxiv | arXiv id_list | Incremental Certificate Learning for Hybrid Neural Network Verification . A Solver Architecture  |
| 2512.24594 | arxiv | arXiv id_list | A Tale of 1001 LoC: Potential Runtime Error-Guided Specification Synthesis for Verifying Large-S |
| 2601.06795 | arxiv | arXiv id_list | GDEPO: Group Dual-dynamic and Equal-right Advantage Policy Optimization with Enhanced Training D |
| 2601.14027 | arxiv | arXiv id_list | Numina-Lean-Agent: An Open and General Agentic Reasoning System for Formal Mathematics |
| 2601.15737 | arxiv | arXiv id_list | PhysProver: Advancing Automatic Theorem Proving for Physics |
| 2601.18944 | arxiv | arXiv id_list | Neural Theorem Proving for Verification Conditions: A Real-World Benchmark |
| 2601.19747 | arxiv | arXiv id_list | Veri-Sure: A Contract-Aware Multi-Agent Framework with Temporal Tracing and Formal Verification  |
| 2601.20055 | arxiv | arXiv id_list | VERGE: Formal Refinement and Guidance Engine for Verifiable LLM Reasoning |
| 2602.00715 | arxiv | arXiv id_list | Beyond Basic Specifications? A Systematic Study of Logical Constructs in LLM-based Specification |
| 2602.08384 | arxiv | arXiv id_list | Towards Real-World Industrial-Scale Verification: LLM-Driven Theorem Proving on seL4 |
| 2602.10512 | arxiv | arXiv id_list | Exponential Sample Complexity Separation between Flat and Hierarchical Agentic Theorem Provers |
| 2602.16554 | arxiv | arXiv id_list | MerLean: An Agentic Framework for Autoformalization in Quantum Computation |
| 2602.18307 | arxiv | arXiv id_list | VeriSoftBench: Repository-Scale Formal Verification Benchmarks for Lean |
| 2602.22631 | arxiv | arXiv id_list | TorchLean: Formalizing Neural Networks in Lean |
| 2602.24273 | arxiv | arXiv id_list | A Minimal Agent for Automated Theorem Proving |
| 2603.02895 | arxiv | arXiv id_list | SpecLoop: An Agentic RTL-to-Specification Framework with Formal Verification Feedback Loop |
| 2603.12744 | arxiv | arXiv id_list | TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib? |
| 2603.14628 | arxiv | arXiv id_list | s2n-bignum-bench: A practical benchmark for evaluating low-level code reasoning of LLMs |
| 2603.18334 | arxiv | arXiv id_list | Can LLMs Reason Like Automated Theorem Provers for Rust Verification? VCoT-Bench: Evaluating via |
| 2603.19329 | arxiv | arXiv id_list | Goedel-Code-Prover: Hierarchical Proof Search for Open State-of-the-Art Code Verification |
| 2603.19828 | arxiv | arXiv id_list | FormalEvolve: Neuro-Symbolic Evolutionary Search for Diverse Autoformalization |
| 2603.21065 | arxiv | arXiv id_list | LongCat-Flash-Prover: Advancing Native Formal Reasoning via Agentic Tool-Integrated Reinforcemen |
| 2603.22114 | arxiv | arXiv id_list | Automated Lemma Discovery in Agentic Program Verification |
| 2603.24465 | arxiv | arXiv id_list | MechMath: Sorrifier-Driven Formal Decomposition Workflow for Automated Theorem Proving |
| 2603.29088 | arxiv | arXiv id_list | WybeCoder: Verified Imperative Code Generation |
| 2604.01483 | arxiv | arXiv id_list | Type-Checked Compliance: Deterministic Guardrails for Agentic Financial Systems Using Lean 4 The |
| 2604.03789 | arxiv | arXiv id_list | Automated Conjecture Resolution with Formal Verification |
| 2604.07455 | arxiv | arXiv id_list | Munkres' General Topology Autoformalized in Isabelle/HOL |
| 2604.08388 | arxiv | arXiv id_list | Awakening the Sleeping Agent: Lean-Specific Agentic Data Reactivates General Tool Use in Goedel  |
| 2604.10761 | arxiv | arXiv id_list | Improving Dynamic Specification Inference with LLM-Generated Counterexamples |
| 2604.15839 | arxiv | arXiv id_list | Discover and Prove: An Open-source Agentic Framework for Hard Mode Automated Theorem Proving in  |
| 2604.18587 | arxiv | arXiv id_list | Compile to Compress: Boosting Formal Theorem Provers by Compiler Outputs |
| 2604.19000 | arxiv | arXiv id_list | Decompose, Structure, and Repair: A Neuro-Symbolic Framework for Autoformalization via Operator  |
| 2604.19558 | arxiv | arXiv id_list | On Reasoning-Centric LLM-based Automated Theorem Proving |
| 2604.23002 | arxiv | arXiv id_list | FormalScience: Scalable Human-in-the-Loop Autoformalisation of Science with Agentic Code Generat |
| 2604.23698 | arxiv | arXiv id_list | Benchmarking Testing in Automated Theorem Proving |
| 2604.24354 | arxiv | arXiv id_list | Understanding and Improving Automated Proof Synthesis for Interactive Theorem Provers |
| 2605.01394 | arxiv | arXiv id_list | LiveFMBench: Unveiling the Power and Limits of Agentic Workflows in Specification Generation |
| 2605.10141 | arxiv | arXiv id_list | FormalRewardBench: A Benchmark for Formal Theorem Proving Reward Models |
| 2605.11905 | arxiv | arXiv id_list | Rethinking Supervision Granularity: Segment-Level Learning for LLM-Based Theorem Proving |
| 2605.13616 | arxiv | arXiv id_list | Scalable Deductive Verification of Data-Level Parallel Programs |
| 2605.14061 | arxiv | arXiv id_list | MathAtlas: A Benchmark for Autoformalization in the Wild |
| 2605.15445 | arxiv | arXiv id_list | From LLM-Generated Conjectures to Lean Formalizations: Automated Polynomial Inequality Proving v |
| 2605.17255 | arxiv | arXiv id_list | CAM-Bench: A Benchmark for Computational and Applied Mathematics in Lean |
| 2605.17475 | arxiv | arXiv id_list | Event-B Agent: Towards LLM Agent for Formal Model Synthesis and Repair |
| 2605.20120 | arxiv | arXiv id_list | Using Aristotle API for AI-Assisted Theorem Proving in Lean 4: A Formalisation Case Study of the |
| 2605.21385 | arxiv | arXiv id_list | Verification of Configurable SRA Systems |
| 2605.22257 | arxiv | arXiv id_list | What are the Right Symmetries for Formal Theorem Proving? |
| 2605.22763 | arxiv | arXiv id_list | Advancing Mathematics Research with AI-Driven Formal Proof Search |
| 2605.22885 | arxiv | arXiv id_list | ImProver 2: Iteratively Self-Improving LMs for Neurosymbolic Proof Optimization |
| 2605.23772 | arxiv | arXiv id_list | Agentic Proving for Program Verification |
| 2605.26457 | arxiv | arXiv id_list | Verus-SpecGym: An Agentic Environment for Evaluating Specification Autoformalization |
| 2605.27485 | arxiv | arXiv id_list | Automating Formal Verification with Agent-Guided Tree Search |
| 2605.27531 | arxiv | arXiv id_list | Agentic Separation Logic Specification Synthesis |
| 2605.29955 | arxiv | arXiv id_list | Formalizing Mathematics at Scale |
| 2605.30914 | arxiv | arXiv id_list | Automating Formal Verification with Reinforcement Learning and Recursive Inference |
| 2606.03303 | arxiv | arXiv id_list | LEAP: Supercharging LLMs for Formal Mathematics with Agentic Frameworks |
| 2606.03743 | arxiv | arXiv id_list | Proof-Refactor: Refactoring Generated Formal Proofs into Modular Artifacts |
| 2606.04883 | arxiv | arXiv id_list | Optimizing the Cost-Quality Tradeoff of Agentic Theorem Provers in Lean |
| 2606.08728 | arxiv | arXiv id_list | Artificial Intelligence for Mathematical Reasoning: An Integrated Survey of Language Models, Neu |
| 2606.11430 | arxiv | arXiv id_list | Towards a Bridge Layer Between Bibliographic and Formalized Mathematical Knowledge |
| 2606.13782 | arxiv | arXiv id_list | MA-ProofBench: A Two-Tiered Evaluation of LLMs for Theorem Proving in Mathematical Analysis |
| 2606.14357 | arxiv | arXiv id_list | No Accidental Software Agent First Canonical Code for Human Code Entropy Reduction and 30 to 500 |
| 2606.16886 | arxiv | arXiv id_list | Neuro-Symbolic Software Verification: Hyper-charging Local Language Models with Symbolic Reasoni |
| 2606.19315 | arxiv | arXiv id_list | Diffusion-Proof: Recipe for Formal Theorem Proving Beyond Auto-Regressive Generation |
| 2606.20068 | arxiv | arXiv id_list | Process-Verified Reinforcement Learning for Theorem Proving via Lean |
| 2606.20740 | arxiv | arXiv id_list | VeriBound: PAC-Bayesian Generalization Bounds for Process Reward Models Trained with Formal Veri |
| 2606.21867 | arxiv | arXiv id_list | ForEx: A Formal Verification Framework for Explainable Reasoning in Logical Fallacy Detection an |
| 2606.22063 | arxiv | arXiv id_list | Guarded Equivalence Predicates for Scalable Formal Hardware Information-Flow Verification |
| 2606.26442 | arxiv | arXiv id_list | AXLE: A Cloud Infrastructure for Lean 4 Theorem Proving Utilities |
| 2606.27926 | arxiv | arXiv id_list | Verifiable Geometry Problem Solving: Solver-Driven Autoformalization and Theorem Proposing |
| 2606.31134 | arxiv | arXiv id_list | Beyond the Library: An Agentic Framework for Autoformalizing Research Mathematics |
| 2606.32007 | arxiv | arXiv id_list | AxDafny: Agentic Verified Code Generation in Dafny |
| 2607.04631 | arxiv | arXiv id_list | Formal Disco: Scalable Open-Ended Generation of Formally Verified Programs |
| 2607.06820 | arxiv | arXiv id_list | Evaluating SageMath-Augmented LLM Agents for Computational and Experimental Mathematics |
| 2607.07779 | arxiv | arXiv id_list | From Solvers to Research: Large Language Model-Driven Formal Mathematics at the Research Frontie |
| 2607.09217 | arxiv | arXiv id_list | OpenProver: Agentic and Interactive Theorem Proving with Lean 4 |
| 2607.11307 | arxiv | arXiv id_list | Efficient Test-Time Optimization for Multi-Agent Proof Autoformalization |
| 2607.14082 | arxiv | arXiv id_list | Building Shor's Algorithm in Lean: An Agentic Formalization of Quantum Attacks on RSA-2048 and P |
| 2607.16372 | arxiv | arXiv id_list | AoA: Theorem Proving Agent over Abstract Syntax Tree of Redesigned Language |
| 2607.21533 | arxiv | arXiv id_list | Benchmarking Agents for Proving Theorems in Quantum Algorithms and Quantum Information |
| 2607.26306 | arxiv | arXiv id_list | Foundational Refinement Proofs for Deployed Bytecode, at the Price of Tokens |
| 2607.27259 | arxiv | arXiv id_list | CircuitProver: Agentic Lean 4 Theorem Proving with Reusable Circuit Proof Library for Hardware V |
| 2607.28877 | arxiv | arXiv id_list | Open-Source LLM-Driven Formal Verification: A Multi-Agent Pipeline for RTL Repair |
| 2608.00894 | arxiv | arXiv id_list | Rethinking Agentic Kernel Generation for Emerging Accelerators |
| 2608.02295 | arxiv | arXiv id_list | MechGeo: Autoformalizing and Proving Euclidean Geometry in Lean 4 |
| 2608.04886 | arxiv | arXiv id_list | A Cost-Aware Probability Monad for Liquid Haskell |
| 2608.05420 | arxiv | arXiv id_list | Can Open-Weight LLMs Produce Kernel-Verified Coq Proofs? A Pilot Study |
| 2608.12375 | arxiv | arXiv id_list | Pipeline Denotational Design: Correct-by-Construction Data Pipelines at Zero Cost |
| 2608.12629 | arxiv | arXiv id_list | CAKE: Compiler-Agent Co-Design for Frontier Kernel Evolution |
| 2608.13077 | arxiv | arXiv id_list | How Powerful are LLMs in Generating Formal Program Specifications? |
| 2608.13757 | arxiv | arXiv id_list | A Barrier-Free Synchronization Algorithm for Multi-Engine AI Accelerators |
| 2608.18084 | arxiv | arXiv id_list | Compiler-Guided Adaptive Proof Search with Cross-Model Synergy on Context-Dependent Theorem Prov |
| 2608.21356 | arxiv | arXiv id_list | AI with Authority, from Application to Silicon |
| 2608.21516 | arxiv | arXiv id_list | Neuro-Formal Verification: Agentic Language-Agnostic Formal Program Reasoning |
| 2608.25220 | arxiv | arXiv id_list | FLARE: Verifying MILP Reformulations with LLM-Based Theorem Proving |
| 2608.28639 | arxiv | arXiv id_list | Reward-Oracle MCTS for Formal Theorem Proving: Sample-Efficient Search and the Need for Kernel-L |
| 2608.29270 | arxiv | arXiv id_list | SHADOWBENCH: Toward Reliable Automatic Evaluation of Semantic Alignment in Autoformalization |
| 2609.19391 | arxiv | arXiv id_list | MAGS: Multi-agent Auto-formalization Guarantees Safety for Agentic Outputs |
| 2609.22347 | arxiv | arXiv id_list | Verification Reward Model for Reinforcement Learning in Chip Design Verification |
| 2609.24252 | arxiv | arXiv id_list | Iris in Lean |
| 2609.25575 | arxiv | arXiv id_list | Direct Optimization of Generators for Search in Automated Theorem Proving |
| 2609.27162 | arxiv | arXiv id_list | Agentic-IC3: Enabling Semantic Proof Search in IC3 Model Checking |
| 2609.37203 | arxiv | arXiv id_list | Learning to Prove, Not Just to Answer: Reinforcement Learning from Formal Verification for Natur |
| 2609.39544 | arxiv | arXiv id_list | Growing an Agent/Prover Interface: Evolutionary Tool Design for Cost-Efficient Theorem Proving i |
| 2610.00885 | arxiv | arXiv id_list | FORALL-LEAN-AGENT for Auditable Reasoning in Formal Mathematics and Software Verification |
| 2610.02792 | arxiv | arXiv id_list | Law And Order: Tax Law Autoformalization |
| 2610.08319 | arxiv | arXiv id_list | SCOPE: Certified Theorem Proving with a Language Model as the Policy Planner |
| 2610.09681 | arxiv | arXiv id_list | Cost-Efficient Theorem Proving via Agent Orchestration in Program Verification |
| 2610.11605 | arxiv | arXiv id_list | NanoProof: Open and Efficient Automated Theorem Proving in Lean 4 |
| 2610.11862 | arxiv | arXiv id_list | LEVER: Adaptive Cost-Aware Proof Search Over AND/OR Graphs |
| cs/0701184 | arxiv | arXiv id_list | Structure and Problem Hardness: Goal Asymmetry and DPLL Proofs in<br> SAT-Based Planning |
