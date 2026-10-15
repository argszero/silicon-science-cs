# Reference pool -- issue #142

Every entry below was discovered by `refscan142.py` (never typed from memory) and checked
against a LIVE external record by comparing the returned TITLE with the stored title
(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a
remembered identifier can resolve to a DIFFERENT real paper, so the check is the title
comparison, not the HTTP status.

- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with
  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)
  and `works/<doi>` (verification)
- pool: 826 entries (803 arXiv, 23 Crossref)
- an entry whose title does not match its live record is dropped, never kept

| key | source | verified against | title |
|-----|--------|------------------|-------|
| 0802.1180 | arxiv | arXiv id_list | First derivatives estimates for finite-difference schemes |
| 0805.3149 | arxiv | arXiv id_list | Higher order derivative estimates for finite-difference schemes |
| 0903.0324 | arxiv | arXiv id_list | Discrete derivative estimation in LISA Pathfinder data reduction |
| 0912.3995 | arxiv | arXiv id_list | Gaussian Process Optimization in the Bandit Setting: No Regret and Experimental Design |
| 10.1007/978-1-4612-5110-1_9 | crossref | Crossref works/<doi> | A Stochastic Approximation Method |
| 10.1007/978-3-642-27645-3_18 | crossref | Crossref works/<doi> | Reinforcement Learning in Robotics: A Survey |
| 10.1007/978-81-951961-1-1 | crossref | Crossref works/<doi> | Stochastic Approximation: A Dynamical Systems Viewpoint |
| 10.1007/b97441 | crossref | Crossref works/<doi> | Stochastic Approximation and Recursive Algorithms and Applications |
| 10.1007/bf01068601 | crossref | Crossref works/<doi> | Numerical optimization |
| 10.1016/s0004-3702(98)00023-x | crossref | Crossref works/<doi> | Planning and acting in partially observable stochastic domains |
| 10.1016/s0005-1098(99)00214-9 | crossref | Crossref works/<doi> | Constrained model predictive control: Stability and optimality |
| 10.1023/a:1013689704352 | crossref | Crossref works/<doi> | Finite-time Analysis of the Multiarmed Bandit Problem |
| 10.1109/9.119632 | crossref | Crossref works/<doi> | Multivariate stochastic approximation using a simultaneous perturbation gradient approximation |
| 10.1109/9.580874 | crossref | Crossref works/<doi> | An analysis of temporal-difference learning with function approximation |
| 10.1109/9780470544334.ch8 | crossref | Crossref works/<doi> | Contributions to the Theory of Optimal Control |
| 10.1109/isit.2014.6875100 | crossref | Crossref works/<doi> | Age of information with packet management |
| 10.1109/jproc.2015.2494218 | crossref | Crossref works/<doi> | Taking the Human Out of the Loop: A Review of Bayesian Optimization |
| 10.1109/tit.2018.2871079 | crossref | Crossref works/<doi> | The Age of Information: Real-Time Status Updating by Multiple Sources |
| 10.1111/1468-0262.00296 | crossref | Crossref works/<doi> | Envelope Theorems for Arbitrary Choice Sets |
| 10.1137/0330046 | crossref | Crossref works/<doi> | Acceleration of Stochastic Approximation by Averaging |
| 10.1142/9789819808250_0007 | crossref | Crossref works/<doi> | Optimal Control and Dynamic Programming |
| 10.1145/3035918.3064029 | crossref | Crossref works/<doi> | Automatic Database Management System Tuning Through Large-scale Machine Learning |
| 10.1145/3292500.3330701 | crossref | Crossref works/<doi> | Optuna: A Next-generation Hyperparameter Optimization Framework |
| 10.1561/9781601986276 | crossref | Crossref works/<doi> | Regret Analysis of Stochastic and Nonstochastic Multi-armed Bandit Problems |
| 10.1561/9781680831719 | crossref | Crossref works/<doi> | Introduction to Online Convex Optimization |
| 10.2307/3003320 | crossref | Crossref works/<doi> | Moral Hazard and Observability |
| 10.7551/mitpress/3206.001.0001 | crossref | Crossref works/<doi> | Gaussian Processes for Machine Learning |
| 1012.5483 | arxiv | arXiv id_list | Differentiation by integration with Jacobi polynomials |
| 1102.2599 | arxiv | arXiv id_list | Rapid-convergent nonlinear differentiator |
| 1103.0652 | arxiv | arXiv id_list | Error analysis of a class of derivative estimators for noisy signals |
| 1103.4286 | arxiv | arXiv id_list | Design and frequency analysis of continuous finite-time-convergent differentiator |
| 1103.4311 | arxiv | arXiv id_list | Design and analysis of continuous hybrid differentiator |
| 1206.2944 | arxiv | arXiv id_list | Practical Bayesian Optimization of Machine Learning Algorithms |
| 1303.3181 | arxiv | arXiv id_list | On Optimal Input Design for Feed-forward Control |
| 1310.3973 | arxiv | arXiv id_list | Adaptive experiment design for LTI systems |
| 1411.2683 | arxiv | arXiv id_list | A Probabilistic Approach to Robust Optimal Experiment Design with Chance Constraints |
| 1411.6250 | arxiv | arXiv id_list | Identification and Estimation of Multidimensional Screening |
| 1412.6980 | arxiv | arXiv id_list | Adam: A Method for Stochastic Optimization |
| 1503.04108 | arxiv | arXiv id_list | Capacity of Random Channels with Large Alphabets |
| 1503.07232 | arxiv | arXiv id_list | A note on optimal experiment design for nonlinear systems using dynamic programming |
| 1504.00702 | arxiv | arXiv id_list | End-to-End Training of Deep Visuomotor Policies |
| 1506.02438 | arxiv | arXiv id_list | High-Dimensional Continuous Control Using Generalized Advantage Estimation |
| 1506.06256 | arxiv | arXiv id_list | Collective Mind, Part II: Towards Performance- and Cost-Aware Software Engineering as a Natural  |
| 1507.07238 | arxiv | arXiv id_list | Estimator Selection: End-Performance Metric Aspects |
| 1510.00455 | arxiv | arXiv id_list | Semidefinite relaxations in optimal experiment design with application to substrate injection fo |
| 1510.03013 | arxiv | arXiv id_list | Gaussian information matrix for Wiener model identification |
| 1511.09198 | arxiv | arXiv id_list | Optimal design of calibration signals in space borne gravitational wave detectors |
| 1608.05046 | arxiv | arXiv id_list | Practical optimal experiment design with probabilistic programs |
| 1610.03688 | arxiv | arXiv id_list | On the optimal experimental design for heat and moisture parameter estimation |
| 1610.05561 | arxiv | arXiv id_list | Adaptive stimulus design for dynamic recurrent neural network models |
| 1611.02408 | arxiv | arXiv id_list | Real-time Algorithm for Self-Reflective Model Predictive Control |
| 1612.05143 | arxiv | arXiv id_list | Sampling-based Motion Planning for Active Multirotor System Identification |
| 1702.06118 | arxiv | arXiv id_list | Derivative Based Focal Plane Array Nonuniformity Correction |
| 1702.08567 | arxiv | arXiv id_list | Optimal Experiment Design for Causal Discovery from Fixed Number of Experiments |
| 1704.06565 | arxiv | arXiv id_list | An efficient method to estimate sorption isotherm curve coefficients |
| 1705.02869 | arxiv | arXiv id_list | On the estimation of moisture permeability and advection coefficients of a wood fibre material u |
| 1709.04562 | arxiv | arXiv id_list | An efficient adaptive sparse grid collocation method through derivative estimation |
| 1710.08062 | arxiv | arXiv id_list | Optimal Experiment Design for Magnetic Resonance Fingerprinting: Cramér-Rao Bound Meets Spin Dyn |
| 1801.06553 | arxiv | arXiv id_list | Reduced basis approximation and a posteriori error estimation: applications to elasticity proble |
| 1802.01312 | arxiv | arXiv id_list | Competitive Online Algorithms for Resource Allocation over the Positive Semidefinite Cone |
| 1803.05460 | arxiv | arXiv id_list | Autonomous Efficient Experiment Design for Materials Discovery with Bayesian Model Averaging |
| 1806.08537 | arxiv | arXiv id_list | Subgradient-Free Stochastic Optimization Algorithm for Non-smooth Convex Functions over Time-Var |
| 1807.08213 | arxiv | arXiv id_list | T-optimal designs for multi-factor polynomial regression models via a semidefinite relaxation me |
| 1808.03233 | arxiv | arXiv id_list | OBOE: Collaborative Filtering for AutoML Model Selection |
| 1810.03717 | arxiv | arXiv id_list | Comparing Models of Associative Meaning: An Empirical Investigation of Reference in Simple Langu |
| 1901.06228 | arxiv | arXiv id_list | On-line Application Autotuning Exploiting Ensemble Models |
| 1902.00931 | arxiv | arXiv id_list | Optimal Experiment Design in Nonlinear Parameter Estimation with Exact Confidence Regions |
| 1905.12745 | arxiv | arXiv id_list | Comparison of Derivative Estimation Methods in Solving Optimal Control Problems Using Direct Col |
| 1906.08509 | arxiv | arXiv id_list | Online A-Optimal Design and Active Linear Regression |
| 1908.10834 | arxiv | arXiv id_list | AWB-GCN: A Graph Convolutional Network Accelerator with Runtime Workload Rebalancing |
| 1909.11219 | arxiv | arXiv id_list | The converse envelope theorem |
| 1909.13720 | arxiv | arXiv id_list | On Incentive Compatibility in Dynamic Mechanism Design With Exit Option in a Markovian Environme |
| 1910.02353 | arxiv | arXiv id_list | Optimizing Data Freshness in Time-Varying Wireless Networks with Imperfect Channel State |
| 1910.08280 | arxiv | arXiv id_list | Robust modal regression with direct log-density derivative estimation |
| 1910.09379 | arxiv | arXiv id_list | Uncertainty amplification due to density/refractive-index gradients in volumetric PTV and BOS ex |
| 1912.05947 | arxiv | arXiv id_list | Minimizing Age of Information with Power Constraints: Multi-user Opportunistic Scheduling in Mul |
| 1912.09017 | arxiv | arXiv id_list | Optimal Experiment Design for AC Power Systems Admittance Estimation |
| 2001.04218 | arxiv | arXiv id_list | Optimal Scheduling for Maximizing Information Freshness & System Performance in Industrial Cyber |
| 2001.08355 | arxiv | arXiv id_list | Gradient and Hessian approximations in Derivative Free Optimization |
| 2001.09863 | arxiv | arXiv id_list | Optimal Sampling and Scheduling for Timely Status Updates in Multi-source Networks |
| 2002.09719 | arxiv | arXiv id_list | Joint Transmission and Computing Scheduling for Status Update with Mobile Edge Computing |
| 2003.04816 | arxiv | arXiv id_list | Data Freshness and Energy-Efficient UAV Navigation Optimization: A Deep Reinforcement Learning A |
| 2004.03695 | arxiv | arXiv id_list | Offsite Autotuning Approach -- Performance Model Driven Autotuning Applied to Parallel Explicit  |
| 2005.03063 | arxiv | arXiv id_list | Learning, transferring, and recommending performance knowledge with Monte Carlo tree search and  |
| 2005.05292 | arxiv | arXiv id_list | Remote Short Blocklength Process Monitoring: Trade-off Between Resolution and Data Freshness |
| 2005.07798 | arxiv | arXiv id_list | Data Freshness in Leader-Based Replicated Storage |
| 2006.06141 | arxiv | arXiv id_list | On-the-fly Closed-loop Autonomous Materials Discovery via Bayesian Active Learning |
| 2006.15751 | arxiv | arXiv id_list | Optimal and Quantized Mechanism Design for Fresh Data Acquisition |
| 2006.16805 | arxiv | arXiv id_list | Pricing Fresh Data |
| 2007.01980 | arxiv | arXiv id_list | Linear Bandits with Limited Adaptivity and Learning Distributional Optimal Design |
| 2007.12536 | arxiv | arXiv id_list | Performance-Driven Cascade Controller Tuning with Bayesian Optimization |
| 2007.14069 | arxiv | arXiv id_list | Convergence of the Kiefer-Wolfowitz algorithm in the presence of discontinuities |
| 2008.13087 | arxiv | arXiv id_list | Efficient Nested Simulation Experiment Design via the Likelihood Ratio Method |
| 2010.00674 | arxiv | arXiv id_list | Reducing the Dimensionality of Optimal Experiment Design for Magnetic Resonance Fingerprinting |
| 2011.00143 | arxiv | arXiv id_list | Nonparametric Identification of Production Function, Total Factor Productivity, and Markup from  |
| 2011.00925 | arxiv | arXiv id_list | Maximum Likelihood Estimation in Data-Driven Modeling and Control |
| 2012.09351 | arxiv | arXiv id_list | Battle between Rate and Error in Minimizing Age of Information |
| 2104.05959 | arxiv | arXiv id_list | AutoOED: Automated Optimal Experiment Design Platform |
| 2107.12771 | arxiv | arXiv id_list | Theoretical Study and Comparison of SPSA and RDSA Algorithms |
| 2108.03778 | arxiv | arXiv id_list | Velocity-adaptive Access Scheme for MEC-assisted Platooning Networks: Access Fairness Via Data F |
| 2108.06007 | arxiv | arXiv id_list | Sleep, Sense or Transmit: Energy-Age Tradeoff for Status Update with Two-Thresholds Optimal Poli |
| 2108.10571 | arxiv | arXiv id_list | Envelope theorems for static optimization and calculus of variations |
| 2109.04784 | arxiv | arXiv id_list | Scheduling Policies for AoI Minimization with Timely Throughput Constraints |
| 2111.07534 | arxiv | arXiv id_list | A Probabilistic Hard Attention Model For Sequentially Observed Scenes |
| 2111.09175 | arxiv | arXiv id_list | Estimation of the thermal properties of an historic building wall by combining Modal Identificat |
| 2112.06815 | arxiv | arXiv id_list | Envelope theorem and discontinuous optimisation: the case of positioning choice problems |
| 2201.02929 | arxiv | arXiv id_list | Optimal Sampling for Data Freshness: Unreliable Transmissions with Random Two-way Delay |
| 2202.05959 | arxiv | arXiv id_list | Formalization of a Stochastic Approximation Theorem |
| 2203.05128 | arxiv | arXiv id_list | LlamaTune: Sample-Efficient DBMS Configuration Tuning |
| 2203.14011 | arxiv | arXiv id_list | Approximations for Optimal Experimental Design in Power System Parameter Estimation |
| 2203.14473 | arxiv | arXiv id_list | Towards Dynamic and Safe Configuration Tuning for Cloud Databases |
| 2204.05838 | arxiv | arXiv id_list | Benchmarking Active Learning Strategies for Materials Optimization and Discovery |
| 2204.14123 | arxiv | arXiv id_list | Towards Optimal Tradeoff Between Data Freshness and Update Cost in Information-update Systems |
| 2205.04092 | arxiv | arXiv id_list | Age-driven Joint Sampling and Non-slot Based Scheduling for Industrial Internet of Things |
| 2205.05787 | arxiv | arXiv id_list | Bridging Model-based Safety and Model-free Reinforcement Learning through System Identification  |
| 2205.13804 | arxiv | arXiv id_list | End-to-End Learning of Hybrid Inverse Dynamics Models for Precise and Compliant Impedance Contro |
| 2205.15009 | arxiv | arXiv id_list | Carleman Lifting for Nonlinear System Identification with Guaranteed Error Bounds |
| 2206.03305 | arxiv | arXiv id_list | Physics-Inspired Temporal Learning of Quadrotor Dynamics for Accurate Model Predictive Trajector |
| 2206.05596 | arxiv | arXiv id_list | Neural Network-based Flight Control Systems: Present and Future |
| 2206.07384 | arxiv | arXiv id_list | Blockchain-based Federated Learning for Industrial Metaverses: Incentive Scheme with Optimal AoI |
| 2206.13313 | arxiv | arXiv id_list | Pontryagin principle and envelope theorem |
| 2207.04897 | arxiv | arXiv id_list | Bounds and convex heuristics for bi-objective optimal experiment design in water networks |
| 2208.00549 | arxiv | arXiv id_list | Unifying Approaches in Active Learning and Active Sampling via Fisher Information and Informatio |
| 2208.01969 | arxiv | arXiv id_list | Regulation and Frontier Housing Supply |
| 2208.07243 | arxiv | arXiv id_list | Exponential Concentration in Stochastic Approximation |
| 2209.00092 | arxiv | arXiv id_list | A rapid-prototype MPC tool based on gPROMS platform |
| 2209.01466 | arxiv | arXiv id_list | Age-Dependent Differential Privacy |
| 2210.00701 | arxiv | arXiv id_list | Near-Optimal Deployment Efficiency in Reward-Free Reinforcement Learning with Linear Function Ap |
| 2210.05222 | arxiv | arXiv id_list | Stochastic Direct Search Method for Blind Resource Allocation |
| 2210.11245 | arxiv | arXiv id_list | Neural ODEs as Feedback Policies for Nonlinear Optimal Control |
| 2211.05797 | arxiv | arXiv id_list | Optimizing the Age of Information in Mixed-Critical Wireless Communication Networks |
| 2212.07114 | arxiv | arXiv id_list | Age of Information Optimization in Multi-Channel Network with Sided Information |
| 2301.12537 | arxiv | arXiv id_list | Non-Asymptotic State-Space Identification of Closed-Loop Stochastic Linear Systems using Instrum |
| 2302.04370 | arxiv | arXiv id_list | Adaptive State-Dependent Diffusion for Derivative-Free Optimization |
| 2302.12349 | arxiv | arXiv id_list | Reward Learning as Doubly Nonparametric Bandits: Optimal Design and Scaling Laws |
| 2303.02227 | arxiv | arXiv id_list | Online simulator-based experimental design for cognitive model selection |
| 2303.08976 | arxiv | arXiv id_list | Towards a Benchmarking Suite for Kernel Tuners |
| 2303.16245 | arxiv | arXiv id_list | ytopt: Autotuning Scientific Applications for Energy Efficiency at Large Scales |
| 2304.02379 | arxiv | arXiv id_list | A Dual System-Level Parameterization for Identification from Closed-Loop Data |
| 2304.02878 | arxiv | arXiv id_list | Online Stabilization of Unknown Linear Time-Varying Systems |
| 2304.06842 | arxiv | arXiv id_list | A Dynamic Adverse Selection Multiagent Model with Off-Menu Actions |
| 2304.07949 | arxiv | arXiv id_list | Metrics for Bayesian Optimal Experiment Design under Model Misspecification |
| 2305.00192 | arxiv | arXiv id_list | MIMO Grid Impedance Identification of Three-Phase Power Systems: Parametric vs. Nonparametric Ap |
| 2305.10650 | arxiv | arXiv id_list | Iteration Complexity and Finite-Time Efficiency of Adaptive Sampling Trust-Region Methods for St |
| 2306.07549 | arxiv | arXiv id_list | Fixed-Budget Best-Arm Identification with Heterogeneous Reward Variances |
| 2306.09210 | arxiv | arXiv id_list | Optimal Exploration for Model-Based RL in Nonlinear Systems |
| 2306.09778 | arxiv | arXiv id_list | Gradient is All You Need? How Consensus-Based Optimization can be Interpreted as a Stochastic Re |
| 2306.11872 | arxiv | arXiv id_list | Predicting Strategic Energy Storage Behaviors |
| 2307.00535 | arxiv | arXiv id_list | Goal-oriented Tensor: Beyond Age of Information Towards Semantics-Empowered Goal-Oriented Commun |
| 2307.07386 | arxiv | arXiv id_list | Real-time system identification of superconducting cavities with a recursive least-squares algor |
| 2307.07923 | arxiv | arXiv id_list | Modeling Physical Activity Impact on Glucose Dynamics in People with Type 1 Diabetes for a Fully |
| 2307.15975 | arxiv | arXiv id_list | Blockchain-empowered Federated Learning for Healthcare Metaverses: User-centric Incentive Mechan |
| 2308.07905 | arxiv | arXiv id_list | The Role of Early Sampling in Age of Information Minimization in the Presence of ACK Delays |
| 2308.09106 | arxiv | arXiv id_list | Optimal Closed Loop Control of G2V/V2G Action Using Model Predictive Controller |
| 2309.05974 | arxiv | arXiv id_list | Optimizing Reported Age of Information with Short Error Correction and Detection Codes |
| 2309.16617 | arxiv | arXiv id_list | Adaptive Output-Feedback Model Predictive Control of Hammerstein Systems with Unknown Linear Dyn |
| 2310.00243 | arxiv | arXiv id_list | Age-Optimal Multi-Flow Status Updating with Errors: A Sample-Path Approach |
| 2310.05792 | arxiv | arXiv id_list | Two-timescale Derivative Free Optimization for Performative Prediction with Markovian Data |
| 2310.12286 | arxiv | arXiv id_list | System identification and closed-loop control of laser hot-wire directed energy deposition using |
| 2310.12795 | arxiv | arXiv id_list | Self-triggered Consensus Control of Multi-agent Systems from Data |
| 2310.20275 | arxiv | arXiv id_list | Age Optimum Sampling in Non-Stationary Environment |
| 2311.00940 | arxiv | arXiv id_list | Dynamic Uploading Scheduling in mmWave-Based Sensor Networks via Mobile Blocker Detection |
| 2311.02749 | arxiv | arXiv id_list | Fast Point Cloud to Mesh Reconstruction for Deformable Object Tracking |
| 2311.06522 | arxiv | arXiv id_list | Semantic-aware Sampling and Transmission in Energy Harvesting Systems: A POMDP Approach |
| 2311.11143 | arxiv | arXiv id_list | Goal-Oriented Communications for Remote Inference under Two-Way Delay with Memory |
| 2312.00279 | arxiv | arXiv id_list | Age-Based Scheduling for Mobile Edge Computing: A Deep Reinforcement Learning Approach |
| 2312.00914 | arxiv | arXiv id_list | Optimizing Information Freshness over a Channel that Wears Out |
| 2312.02828 | arxiv | arXiv id_list | Convergence Rates for Stochastic Approximation: Biased Noise with Unbounded Variance, and Applic |
| 2312.04272 | arxiv | arXiv id_list | Data-driven control of input saturated systems: a LMI-based approach |
| 2312.11200 | arxiv | arXiv id_list | Solving the Optimal Experiment Design Problem with Mixed-Integer Convex Methods |
| 2312.15836 | arxiv | arXiv id_list | Optimized experiment design and analysis for fully randomized benchmarking |
| 2401.01263 | arxiv | arXiv id_list | Identification of Additive Continuous-time Systems in Open and Closed loop |
| 2401.04669 | arxiv | arXiv id_list | Transfer-Learning-Based Autotuning Using Gaussian Copula |
| 2401.05221 | arxiv | arXiv id_list | Closed-loop Identification of a MSW Grate Incinerator using Bayesian Optimization for Selecting  |
| 2401.15792 | arxiv | arXiv id_list | Sample Complexity of the Sign-Perturbed Sums Identification Method: Scalar Case |
| 2402.00352 | arxiv | arXiv id_list | A Data-Driven Autopilot for Fixed-Wing Aircraft Based on Model Predictive Control |
| 2402.00845 | arxiv | arXiv id_list | When to Preempt in a Status Update System? |
| 2402.05607 | arxiv | arXiv id_list | Internal Model Control design for systems learned by Control Affine Neural Nonlinear Autoregress |
| 2403.01723 | arxiv | arXiv id_list | Statistical Mechanics of Dynamical System Identification |
| 2403.05455 | arxiv | arXiv id_list | Control-Oriented Identification for the Linear Quadratic Regulator: Technical Report |
| 2403.11365 | arxiv | arXiv id_list | Determination of a Small Elliptical Anomaly in Electrical Impedance Tomography using Minimal Mea |
| 2403.11744 | arxiv | arXiv id_list | A First-Order Gradient Approach for the Connectivity Optimization of Markov Chains |
| 2403.20128 | arxiv | arXiv id_list | Simple inverse kinematics computation considering joint motion efficiency |
| 2404.01229 | arxiv | arXiv id_list | Age of Information in a Single-Source Generate-at-Will Dual-Server Status Update System |
| 2404.03227 | arxiv | arXiv id_list | Transferable Graphical MARL for Real-Time Estimation in Dynamic Wireless Networks |
| 2404.03371 | arxiv | arXiv id_list | The Nearest Graph Laplacian in Frobenius Norm |
| 2404.04062 | arxiv | arXiv id_list | Derivative-free tree optimization for complex systems |
| 2404.04937 | arxiv | arXiv id_list | Optimizing Information Propagation for Blockchain-empowered Mobile AIGC: A Graph Attention Netwo |
| 2404.06043 | arxiv | arXiv id_list | Automatic Configuration Tuning on Cloud Database: A Survey |
| 2404.07684 | arxiv | arXiv id_list | Merger Analysis with Unobserved Prices |
| 2404.08362 | arxiv | arXiv id_list | Optimization-Based System Identification and Moving Horizon Estimation Using Low-Cost Sensors fo |
| 2404.08955 | arxiv | arXiv id_list | Consistency analysis of refined instrumental variable methods for continuous-time system identif |
| 2404.11893 | arxiv | arXiv id_list | Derivative-Free Optimization via Adaptive Sampling Strategies |
| 2404.15751 | arxiv | arXiv id_list | Guided-SPSA: Simultaneous Perturbation Stochastic Approximation assisted by the Parameter Shift  |
| 2404.16009 | arxiv | arXiv id_list | How to Make Money From Fresh Data: Subscription Strategies in Age-Based Systems |
| 2404.16281 | arxiv | arXiv id_list | Timely Communications for Remote Inference |
| 2405.01094 | arxiv | arXiv id_list | Closed-Loop Sensitivity Identification for Cross-Directional Systems |
| 2405.02042 | arxiv | arXiv id_list | Sampling to Achieve the Goal: An Age-aware Remote Markov Decision Process |
| 2405.02924 | arxiv | arXiv id_list | Optimal Sampling for Uncertainty-of-Information Minimization in a Remote Monitoring System |
| 2405.03154 | arxiv | arXiv id_list | Learning Nonlinear Dynamics Using Kalman Smoothing |
| 2405.04431 | arxiv | arXiv id_list | Optimizing Information Freshness in IoT Systems with Update Rate Constraints: A Token-Based Appr |
| 2405.05638 | arxiv | arXiv id_list | A Correlation-induced Finite Difference Estimator |
| 2405.06186 | arxiv | arXiv id_list | Sensing-Assisted Adaptive Channel Contention for Mobile Delay-Sensitive Communications |
| 2406.00616 | arxiv | arXiv id_list | EMIT: Micro-Invasive Database Configuration Tuning |
| 2406.02139 | arxiv | arXiv id_list | Statistical Age of Information: A Risk-Aware Metric and Its Applications in Status Updates |
| 2406.05764 | arxiv | arXiv id_list | Global Sensitivity Analysis of Uncertain Parameters in Bayesian Networks |
| 2406.07892 | arxiv | arXiv id_list | A Finite-Sample Analysis of an Actor-Critic Algorithm for Mean-Variance Optimization in a Discou |
| 2406.14594 | arxiv | arXiv id_list | Age of Information Versions: a Semantic View of Markov Source Monitoring |
| 2406.15073 | arxiv | arXiv id_list | KnobTree: Intelligent Database Parameter Configuration via Explainable Reinforcement Learning |
| 2407.00978 | arxiv | arXiv id_list | Hybrid RAG-empowered Multi-modal LLM for Secure Data Management in Internet of Medical Things: A |
| 2407.02342 | arxiv | arXiv id_list | Optimizing Age of Information in Vehicular Edge Computing with Federated Graph Neural Network Mu |
| 2407.08587 | arxiv | arXiv id_list | From AoI to QVAoI: Query-Based Semantics-Aware Scheduling for Energy-Harvesting IoT Systems |
| 2407.14786 | arxiv | arXiv id_list | A Pseudo-Gradient Approach for Model-free Markov Chain Optimization |
| 2407.17491 | arxiv | arXiv id_list | Robust Adaptation of Foundation Models with Black-Box Visual Prompting |
| 2408.02570 | arxiv | arXiv id_list | Whittle's index-based age-of-information minimization in multi-energy harvesting source networks |
| 2408.04625 | arxiv | arXiv id_list | Adaptive Sampling-Based Bi-Fidelity Stochastic Trust Region Method for Derivative-Free Stochasti |
| 2408.12589 | arxiv | arXiv id_list | Age and Value of Information Optimization for Systems with Multi-Class Updates |
| 2408.16261 | arxiv | arXiv id_list | Evaluating Time-Series Training Dataset through Lens of Spectrum in Deep State Space Models |
| 2409.13088 | arxiv | arXiv id_list | Informative Input Design for Dynamic Mode Decomposition |
| 2409.15858 | arxiv | arXiv id_list | Identification For Control Based on Neural Networks: Approximately Linearizable Models |
| 2409.16285 | arxiv | arXiv id_list | Age of Gossip in Networks with Multiple Views of a Source |
| 2410.03920 | arxiv | arXiv id_list | Learning Object Properties Using Robot Proprioception via Differentiable Robot-Object Interactio |
| 2410.05852 | arxiv | arXiv id_list | A$^3$L-FEC: Age-Aware Application Layer Forward Error Correction Flow Control |
| 2410.06624 | arxiv | arXiv id_list | Optimized Magnetic Resonance Fingerprinting Using Ziv-Zakai Bound |
| 2410.07215 | arxiv | arXiv id_list | Analysis and Optimization of Seismic Monitoring Networks with Bayesian Optimal Experiment Design |
| 2410.08706 | arxiv | arXiv id_list | Goal-Oriented Status Updating for Real-time Remote Inference over Networks with Two-Way Delay |
| 2410.09823 | arxiv | arXiv id_list | Simultaneous Computation and Memory Efficient Zeroth-Order Optimizer for Fine-Tuning Large Langu |
| 2410.14842 | arxiv | arXiv id_list | Efficient Parameter Tuning for a Structure-Based Virtual Screening HPC Application |
| 2411.00112 | arxiv | arXiv id_list | Derivative-Free Optimization via Finite Difference Approximation: An Experimental Study |
| 2411.05016 | arxiv | arXiv id_list | Reservoir computing for system identification and predictive control with limited data |
| 2411.06981 | arxiv | arXiv id_list | On strong posterior contraction rates for Besov-Laplace priors in the white noise model |
| 2411.09267 | arxiv | arXiv id_list | Towards efficient compression and communication for prototype-based decentralized learning |
| 2411.17463 | arxiv | arXiv id_list | How long is long enough? Finite-horizon approximation of energy storage scheduling problems |
| 2412.01085 | arxiv | arXiv id_list | Data-driven optimal control of unknown nonlinear dynamical systems using the Koopman operator |
| 2412.09052 | arxiv | arXiv id_list | GREAT: Grassmannian REcursive Algorithm for Tracking & Online System Identification |
| 2412.10554 | arxiv | arXiv id_list | Prescribing Decision Conservativeness in Two-Stage Power Markets: A Distributionally Robust End- |
| 2412.11036 | arxiv | arXiv id_list | Stochastic Approximation and Brownian Repulsion based Evolutionary Search |
| 2412.12789 | arxiv | arXiv id_list | 2D-AoI: Age-of-Information of Distributed Sensors for Spatio-Temporal Processes |
| 2412.17838 | arxiv | arXiv id_list | Coordinated Power Smoothing Control for Wind Storage Integrated System with Physics-informed Dee |
| 2412.18119 | arxiv | arXiv id_list | Age Optimal Sampling for Unreliable Channels under Unknown Channel Statistics |
| 2412.20283 | arxiv | arXiv id_list | Convex Data-Driven Contraction With Riemannian Metrics |
| 2501.04783 | arxiv | arXiv id_list | Traffic Simulations: Multi-City Calibration of Metropolitan Highway Networks |
| 2501.06693 | arxiv | arXiv id_list | Vid2Sim: Realistic and Interactive Simulation from Video for Urban Navigation |
| 2501.11921 | arxiv | arXiv id_list | Goal-oriented Transmission Scheduling: Structure-guided DRL with a Unified Dual On-policy and Of |
| 2501.13431 | arxiv | arXiv id_list | Optimizing the Trade-off Between Throughput and PAoI Outage Exponents |
| 2501.13886 | arxiv | arXiv id_list | On the Almost Sure Convergence of the Stochastic Three Points Algorithm |
| 2501.14367 | arxiv | arXiv id_list | Joint System Latency and Data Freshness Optimization for Cache-enabled Mobile Crowdsensing Netwo |
| 2501.14708 | arxiv | arXiv id_list | Decision-Focused Learning for Complex System Identification: HVAC Management System Application |
| 2502.00893 | arxiv | arXiv id_list | ToddlerBot: Open-Source ML-Compatible Humanoid Platform for Loco-Manipulation |
| 2502.03367 | arxiv | arXiv id_list | SyMANTIC: An Efficient Symbolic Regression Method for Interpretable and Parsimonious Model Disco |
| 2502.05776 | arxiv | arXiv id_list | Dynamic Pricing in the Linear Valuation Model using Shape Constraints |
| 2502.07069 | arxiv | arXiv id_list | Semantics-Aware Updates from Remote Energy Harvesting Devices to Interconnected LEO Satellites |
| 2502.11359 | arxiv | arXiv id_list | Simulation-Based Optimization for Policy Incentives and Planning of Hybrid Microgrids |
| 2502.15014 | arxiv | arXiv id_list | Inferring System and Optimal Control Parameters of Closed-Loop Systems from Partial Observations |
| 2502.15649 | arxiv | arXiv id_list | A Simulation Pipeline to Facilitate Real-World Robotic Reinforcement Learning Applications |
| 2502.15667 | arxiv | arXiv id_list | Probabilistic Formulations for System Identification of Linear Dynamics with Bilinear Observatio |
| 2502.17042 | arxiv | arXiv id_list | On Space-Filling Input Design for Nonlinear Dynamic Model Learning: A Gaussian Process Approach |
| 2502.20319 | arxiv | arXiv id_list | Impilict Runge-Kutta based sparse identification of governing equations in biologically motivate |
| 2502.20819 | arxiv | arXiv id_list | Enhanced Derivative-Free Optimization Using Adaptive Correlation-Induced Finite Difference Estim |
| 2502.21065 | arxiv | arXiv id_list | Lifted Frequency-Domain Identification of Closed-Loop Multirate Systems: Applied to Dual-Stage A |
| 2503.01801 | arxiv | arXiv id_list | TUNA: Tuning Unstable and Noisy Cloud Applications |
| 2503.02285 | arxiv | arXiv id_list | Minimizing Age of Detection for a Markov Source over a Lossy Channel |
| 2503.02985 | arxiv | arXiv id_list | Regularization for Covariance Parameterization of Direct Data-Driven LQR Control |
| 2503.03291 | arxiv | arXiv id_list | Goal-Oriented Random Access (GORA) |
| 2503.03460 | arxiv | arXiv id_list | Visualising Policy-Reward Interplay to Inform Zeroth-Order Preference Optimisation of Large Lang |
| 2503.08355 | arxiv | arXiv id_list | On Vector Field Reconstruction from Noisy ODE in High Ambient Dimension |
| 2503.08851 | arxiv | arXiv id_list | Age of Positioning with Stochastic Motion Models |
| 2503.14898 | arxiv | arXiv id_list | Online Optimization with Unknown Time-varying Parameters |
| 2503.21633 | arxiv | arXiv id_list | Static and Repeated Cooperative Games for the Optimization of the AoI in IoT Networks |
| 2503.22601 | arxiv | arXiv id_list | Neural Identification of Feedback-Stabilized Nonlinear Systems |
| 2504.01289 | arxiv | arXiv id_list | Derivative estimation by RKHS regularization for learning dynamics from time-series data |
| 2504.04414 | arxiv | arXiv id_list | Redefining Information Freshness: AoGI for Generative AI in 6G Networks |
| 2504.04916 | arxiv | arXiv id_list | Age-of-information minimization under energy harvesting and non-stationary environment |
| 2504.05371 | arxiv | arXiv id_list | Status Updating with Time Stamp Errors |
| 2504.08188 | arxiv | arXiv id_list | Safe Data-Driven Predictive Control |
| 2504.11756 | arxiv | arXiv id_list | AQETuner: Reliable Query-level Configuration Tuning for Analytical Query Engines |
| 2504.15818 | arxiv | arXiv id_list | Uniqueness of Parisi measures for enriched convex vector spin glass |
| 2504.17927 | arxiv | arXiv id_list | Recursive Identification of Structured Systems: An Instrumental-Variable Approach Applied to Mec |
| 2504.19507 | arxiv | arXiv id_list | From Freshness to Effectiveness: Goal-Oriented Sampling for Remote Decision Making |
| 2504.20313 | arxiv | arXiv id_list | System Identification of Thrust and Torque Characteristics for a Bipedal Robot with Integrated P |
| 2504.20542 | arxiv | arXiv id_list | Digital Twin-Empowered Cooperative Autonomous Car-sharing Services: Proof-of-Concept |
| 2505.00585 | arxiv | arXiv id_list | Dimension-reduced Optimization of Multi-zone Thermostatically Controlled Loads |
| 2505.06407 | arxiv | arXiv id_list | Direct Data Driven Control Using Noisy Measurements |
| 2505.06691 | arxiv | arXiv id_list | Distributed Event-Triggered Nash Equilibrium Seeking for Noncooperative Games |
| 2505.09725 | arxiv | arXiv id_list | Branched harmonic majorants: representations for multidimensional optimal stopping |
| 2505.14169 | arxiv | arXiv id_list | Statistically Optimal Structured Additive MIMO Continuous-time System Identification |
| 2505.14307 | arxiv | arXiv id_list | Timely CPU Scheduling for Computation-intensive Status Updates |
| 2505.14515 | arxiv | arXiv id_list | Data-Driven Modeling Approaches for Optimal Control and Control Co-Design of Floating Offshore W |
| 2505.15519 | arxiv | arXiv id_list | Exploiting Age of Information in Network Digital Twins for AI-driven Real-Time Link Blockage Det |
| 2505.15972 | arxiv | arXiv id_list | Extremum Seeking for PDE Systems using Physics-Informed Neural Networks |
| 2505.18090 | arxiv | arXiv id_list | Evaluation of derivatives using approximate generalized parameter shift rule |
| 2505.20750 | arxiv | arXiv id_list | Data-Driven Existence and Design of Target Output Controllers |
| 2505.22170 | arxiv | arXiv id_list | Attention-Enhanced Prompt Decision Transformers for UAV-Assisted Communications with AoI |
| 2505.23138 | arxiv | arXiv id_list | System Identification for Virtual Sensor-Based Model Predictive Control: Application to a 2-DoF  |
| 2506.00397 | arxiv | arXiv id_list | A Family of Robust Generalized Adaptive Filters and Application for Time-series Prediction |
| 2506.02980 | arxiv | arXiv id_list | Non-stationary Bandit Convex Optimization: A Comprehensive Study |
| 2506.03650 | arxiv | arXiv id_list | Fast Sampling for System Identification: Overcoming Noise, Offsets, and Closed-Loop Challenges w |
| 2506.11279 | arxiv | arXiv id_list | Smart Predict-Then-Control: Control-Aware Surrogate Refinement for System Identification |
| 2506.11293 | arxiv | arXiv id_list | Influence Functions for Data Attribution in Linear System Identification and LQR Control |
| 2506.11311 | arxiv | arXiv id_list | Optimal experiment design for practical parameter identifiability and model discrimination |
| 2506.16392 | arxiv | arXiv id_list | State-Space Kolmogorov Arnold Networks for Interpretable Nonlinear System Identification |
| 2507.01727 | arxiv | arXiv id_list | Auto-optimization of Energy Generation for Wave Energy Converters with Active Learning |
| 2507.03799 | arxiv | arXiv id_list | On the Distribution of Age of Information in Time-varying Updating Systems |
| 2507.07749 | arxiv | arXiv id_list | A Model-Free Extremum Seeking Controller with Application to Tracking a Nonlinear Chemical React |
| 2507.10134 | arxiv | arXiv id_list | FRSICL: LLM-Enabled In-Context Learning Flight Resource Allocation for Fresh Data Collection in  |
| 2507.10797 | arxiv | arXiv id_list | Multi-Armed Sampling Problem and the End of Exploration |
| 2507.12317 | arxiv | arXiv id_list | Road Roughness Estimation via Fusion of Standard Onboard Automotive Sensors |
| 2507.15713 | arxiv | arXiv id_list | Extremum Seeking (ES) is Practically Stable Whenever Model-Based ES is Stable |
| 2507.19661 | arxiv | arXiv id_list | Interpolation-Based Gradient-Error Bounds for Use in Derivative-Free Optimization of Noisy Funct |
| 2507.20524 | arxiv | arXiv id_list | A Lyapunov-Guided Diffusion-Based Reinforcement Learning Approach for UAV-Assisted Vehicular Net |
| 2507.22176 | arxiv | arXiv id_list | Derivative Estimation from Coarse, Irregular, Noisy Samples: An MLE-Spline Approach |
| 2507.23433 | arxiv | arXiv id_list | From Timestamps to Versions: Version AoI in Single- and Multi-Hop Networks |
| 2508.05279 | arxiv | arXiv id_list | Passive Lifted FIR Filters for Nonlinear System Identification |
| 2508.07555 | arxiv | arXiv id_list | Multimodal Remote Inference |
| 2508.07865 | arxiv | arXiv id_list | Age of Information Minimization in Goal-Oriented Communication with Processing and Cost of Actua |
| 2508.08485 | arxiv | arXiv id_list | Gradient- and Newton-Based Unit Vector Extremum Seeking Control |
| 2508.11533 | arxiv | arXiv id_list | Integrating Uncertainties for Koopman-Based Stabilization |
| 2508.14017 | arxiv | arXiv id_list | Analog computation with transcriptional networks |
| 2508.14328 | arxiv | arXiv id_list | Multi-Source Peak Age of Information Optimization in Mobile Edge Computing Systems |
| 2508.18813 | arxiv | arXiv id_list | Recursive Experiment Design for Closed-Loop Identification of ARMAX Systems with Output Perturba |
| 2508.20836 | arxiv | arXiv id_list | First Experimental Demonstration of Natural Hovering Extremum Seeking: A New Paradigm in Flappin |
| 2509.01926 | arxiv | arXiv id_list | AoI-based Scheduling of Correlated Sources for Timely Inference |
| 2509.04424 | arxiv | arXiv id_list | Global Convergence and Acceleration for Single Observation Gradient Free Optimization |
| 2509.07634 | arxiv | arXiv id_list | A kernel-based approach to physics-informed nonlinear system identification |
| 2509.14219 | arxiv | arXiv id_list | Data Denoising and Derivative Estimation for Data-Driven Modeling of Nonlinear Dynamical Systems |
| 2509.14505 | arxiv | arXiv id_list | Sequential test sampling for stochastic derivative-free optimization |
| 2509.15509 | arxiv | arXiv id_list | Bayesian Risk-Sensitive Policy Optimization For MDPs With General Loss Functions |
| 2509.16365 | arxiv | arXiv id_list | Servos for Local Map Exploration Onboard Nonholonomic Vehicles for Extremum Seeking |
| 2509.17103 | arxiv | arXiv id_list | Clarke Differentials and the Envelope Theorem in Dynamic Programming |
| 2509.17282 | arxiv | arXiv id_list | Task-Oriented Communications for 3D Scene Representation: Balancing Timeliness and Fidelity |
| 2509.19651 | arxiv | arXiv id_list | RIS-assisted Data Collection and Wireless Power Transfer in Low-altitude Wireless Networks |
| 2509.21423 | arxiv | arXiv id_list | Near-Optimal Experiment Design in Linear non-Gaussian Cyclic Models |
| 2509.21814 | arxiv | arXiv id_list | Distributed Time-Varying Optimization via Unbiased Extremum Seeking |
| 2509.23360 | arxiv | arXiv id_list | Absorbing Markov Chain-Based Analysis of Age of Information in Discrete-Time Dual-Queue Systems |
| 2510.01269 | arxiv | arXiv id_list | Safe Reinforcement Learning-Based Vibration Control: Overcoming Training Risks with LQR Guidance |
| 2510.02490 | arxiv | arXiv id_list | Improved Robustness of Deep Reinforcement Learning for Control of Time-Varying Systems by Bounde |
| 2510.03823 | arxiv | arXiv id_list | Distributed Area Coverage with High Altitude Balloons Using Multi-Agent Reinforcement Learning |
| 2510.05023 | arxiv | arXiv id_list | Rethinking Langevin Thompson Sampling from A Stochastic Approximation Perspective |
| 2510.05563 | arxiv | arXiv id_list | Unbiased Extremum Seeking for MPPT in Photovoltaic Systems |
| 2510.06403 | arxiv | arXiv id_list | Generalized Multi-Constraint Extremum Seeking |
| 2510.08117 | arxiv | arXiv id_list | Near-optimal Rank Adaptive Inference of High Dimensional Matrices |
| 2510.13024 | arxiv | arXiv id_list | Data to Certificate: Guaranteed Cost Control with Quantization-Aware System Identification |
| 2510.19531 | arxiv | arXiv id_list | The Confusing Instance Principle for Online Linear Quadratic Control |
| 2510.22288 | arxiv | arXiv id_list | Optimal Sampling and Scheduling for Remote Fusion Estimation of Correlated Wiener Processes |
| 2510.22402 | arxiv | arXiv id_list | Model-Free Optimization and Control of Rigid Body Dynamics: An Extremum Seeking for Vibrational  |
| 2510.22458 | arxiv | arXiv id_list | Derivative-Free Sequential Quadratic Programming for Equality-Constrained Stochastic Optimizatio |
| 2510.24246 | arxiv | arXiv id_list | Precoding-free Hierarchical Rate-Splitting Multiple Access via Stacked Intelligent Metasurface |
| 2510.26708 | arxiv | arXiv id_list | Pareto-Optimal Sampling and Resource Allocation for Timely Communication in Shared-Spectrum Low- |
| 2511.00208 | arxiv | arXiv id_list | Multivariable Gradient-Based Extremum Seeking Control with Saturation Constraints |
| 2511.00752 | arxiv | arXiv id_list | Model-free source seeking of exponentially convergent unicycle: theoretical and robotic experime |
| 2511.01602 | arxiv | arXiv id_list | L2T-Tune:LLM-Guided Hybrid Database Tuning with LHS and TD3 |
| 2511.04917 | arxiv | arXiv id_list | Computationally Efficient Spline-Based Modeling of DER Dynamics for Voltage Stability in Active  |
| 2511.08612 | arxiv | arXiv id_list | Learning based Modelling of Throttleable Engine Dynamics for Lunar Landing Mission |
| 2511.09710 | arxiv | arXiv id_list | Echoing: Identity Failures when LLM Agents Talk to Each Other |
| 2511.11994 | arxiv | arXiv id_list | Extremum-Seeking Boundary Control for Schrödinger-Type PDEs |
| 2511.14388 | arxiv | arXiv id_list | Integral Bayesian symbolic regression for optimal discovery of governing equations from scarce a |
| 2511.14926 | arxiv | arXiv id_list | Finite-Horizon LQR for General Markov Jump Linear Systems: Deterministic Reformulation and Reduc |
| 2511.20457 | arxiv | arXiv id_list | A Fully Probabilistic Tensor Network for Regularized Volterra System Identification |
| 2512.00985 | arxiv | arXiv id_list | Age Optimal Sampling and Routing under Intermittent Links and Energy Constraints |
| 2512.02532 | arxiv | arXiv id_list | Laplace Approximation For Tensor Train Kernel Machines In System Identification |
| 2512.02551 | arxiv | arXiv id_list | CUDA-L2: Surpassing cuBLAS Performance for Matrix Multiplication through Reinforcement Learning |
| 2512.02803 | arxiv | arXiv id_list | System Identification for Dynamic Modeling of Large Steering Angle Vehicles |
| 2512.09113 | arxiv | arXiv id_list | On Event-Triggered Extremum Seeking via Standard and Lie-Bracket Averaging: A Hybrid Dynamical S |
| 2512.10654 | arxiv | arXiv id_list | Strong Global Convergence of the Consensus-Based Optimization Algorithm |
| 2512.11990 | arxiv | arXiv id_list | Policy Gradient Algorithms for Age-of-Information Cost Minimization |
| 2512.15678 | arxiv | arXiv id_list | Hybrid Set-Seeking Systems: Model-Free Feedback Optimization via Hybrid Inclusions |
| 2512.16356 | arxiv | arXiv id_list | Optimal chiller loading including transients |
| 2512.18222 | arxiv | arXiv id_list | Regularized Distributed MPC for UAV Networks: Stabilizing Coupled Motion and Hybrid Beam Alignme |
| 2512.20622 | arxiv | arXiv id_list | How Feasible are Passive Network Attacks on 5G Networks and Beyond? A Survey |
| 2512.21412 | arxiv | arXiv id_list | A Survey of Freshness-Aware Wireless Networking with Reinforcement Learning |
| 2512.22467 | arxiv | arXiv id_list | GLUE: Gradient-free Learning to Unify Experts |
| 2601.00728 | arxiv | arXiv id_list | Precision autotuning for linear solvers via contextual bandit-based RL |
| 2601.01160 | arxiv | arXiv id_list | Gradient-Free Approaches is a Key to an Efficient Interaction with Markovian Stochasticity |
| 2601.01747 | arxiv | arXiv id_list | Crafting Adversarial Inputs for Large Vision-Language Models Using Black-Box Optimization |
| 2601.02607 | arxiv | arXiv id_list | Extremum Seeking Control for Wave-PDE Actuation with Distributed Effects |
| 2601.07815 | arxiv | arXiv id_list | Uniform-in-time convergence and turnpike properties of linear-quadratic mean field control probl |
| 2601.09998 | arxiv | arXiv id_list | Extremum Seeking Nonovershooting Control of Strict-Feedback Systems Under Unknown Control Direct |
| 2601.14089 | arxiv | arXiv id_list | Data-Driven Safe Output Regulation of Strict-Feedback Linear Systems with Input Delay |
| 2601.14416 | arxiv | arXiv id_list | Event-Triggered Newton Extremum Seeking for Multivariable Optimization |
| 2601.14670 | arxiv | arXiv id_list | In-Situ Inverse Design of a Plasma Metamaterial Beam Steering Device |
| 2601.17920 | arxiv | arXiv id_list | Agentic AI for Self-Driving Laboratories in Soft Matter: Taxonomy, Benchmarks,and Open Challenge |
| 2601.19527 | arxiv | arXiv id_list | Fuzzy expert system for the process of collecting and purifying acidic water: a digital twin app |
| 2601.20183 | arxiv | arXiv id_list | C-AoEI-Aware Cross-Layer Optimization in Satellite IoT Systems: Balancing Data Freshness and Tra |
| 2602.00097 | arxiv | arXiv id_list | Rough Martingale Optimal Transport: Theory, Implementation, and Regulatory Applications for Non- |
| 2602.02634 | arxiv | arXiv id_list | A Reduction from Delayed to Immediate Feedback for Online Convex Optimization with Improved Guar |
| 2602.02992 | arxiv | arXiv id_list | Data-driven stabilization of continuous-time systems with noisy input-output data |
| 2602.03246 | arxiv | arXiv id_list | Joint Network-and-Server Congestion in Multi-Source Traffic Allocation: A Convex Formulation and |
| 2602.04132 | arxiv | arXiv id_list | LC-SAC: Lyapunov-Constrained Soft Actor-Critic via Koopman Operator Theory for Trajectory Tracki |
| 2602.05263 | arxiv | arXiv id_list | Nonlinear Predictive Cost Adaptive Control of Pseudo-Linear Input-Output Models Using Polynomial |
| 2602.13098 | arxiv | arXiv id_list | Barron-Wiener-Laguerre models |
| 2602.13269 | arxiv | arXiv id_list | Modality-Tailored Age of Information for Multimodal Data in Edge Computing Systems |
| 2602.13615 | arxiv | arXiv id_list | On the Existence of Periodic Solutions with Applications to Extremum-Seeking |
| 2602.13654 | arxiv | arXiv id_list | From time series to dissipativity of linear systems with dynamic supply rates |
| 2602.15722 | arxiv | arXiv id_list | Pricing Discrete and Nonlinear Markets With Semidefinite Relaxations |
| 2602.15954 | arxiv | arXiv id_list | Hybrid Model Predictive Control with Physics-Informed Neural Network for Satellite Attitude Cont |
| 2602.16358 | arxiv | arXiv id_list | System Identification under Constraints and Disturbance: A Bayesian Estimation Approach |
| 2602.18933 | arxiv | arXiv id_list | A Stochastic Gradient Descent Approach to Design Policy Gradient Methods for LQR |
| 2602.21331 | arxiv | arXiv id_list | CableRobotGraphSim: A Graph Neural Network for Modeling Partially Observable Cable-Driven Robot  |
| 2602.22392 | arxiv | arXiv id_list | DIAL: Decentralized I/O AutoTuning via Learned Client-side Local Metrics for Parallel File Syste |
| 2602.22423 | arxiv | arXiv id_list | CARAT: Client-Side Adaptive RPC and Cache Co-Tuning for Parallel File Systems |
| 2602.23053 | arxiv | arXiv id_list | Marinarium: A Modular Experimental Facility for Reproducible Maritime and Space-Analog Field Rob |
| 2602.24101 | arxiv | arXiv id_list | Bayesian inference of flame impulse responses |
| 2603.01084 | arxiv | arXiv id_list | Kernel-Based LMI Approaches to Solving the Hamilton-Jacobi-Bellman Equation and Nonlinear Optima |
| 2603.01200 | arxiv | arXiv id_list | Non-Local Extremum Seeking Based on the Divergence Theorem |
| 2603.02823 | arxiv | arXiv id_list | Extremum Seeking with Double Integrators in the Presence of Local Extrema |
| 2603.05201 | arxiv | arXiv id_list | Towards a data-scale independent regulariser for robust sparse identification of non-linear dyna |
| 2603.06380 | arxiv | arXiv id_list | Kinetic-based regularization: Learning spatial derivatives and PDE applications |
| 2603.07775 | arxiv | arXiv id_list | Stability-Aligned Residual Adaptation for Rapid Recovery from Dynamics Shifts |
| 2603.08518 | arxiv | arXiv id_list | Breaking the Bias Barrier in Concave Multi-Objective Reinforcement Learning |
| 2603.08863 | arxiv | arXiv id_list | Adaptive SINDy: Residual Force System Identification Based UAV Disturbance Rejection |
| 2603.09399 | arxiv | arXiv id_list | Vision-Augmented On-Track System Identification for Autonomous Racing via Attention-Based Priors |
| 2603.09908 | arxiv | arXiv id_list | NanoBench: A Multi-Task Benchmark Dataset for Nano-Quadrotor System Identification, Control, and |
| 2603.10219 | arxiv | arXiv id_list | A Diffusion Analysis of Policy Gradient for Stochastic Bandits |
| 2603.10569 | arxiv | arXiv id_list | Win-score promotion gates in aggregator-routed RFQ markets: A two-tier stochastic control model |
| 2603.14514 | arxiv | arXiv id_list | High-Probability Bounds for SGD under the Polyak-Lojasiewicz Condition with Markovian Noise |
| 2603.14762 | arxiv | arXiv id_list | Online Learning for Supervisory Switching Control |
| 2603.14910 | arxiv | arXiv id_list | Generalizable Optimal Control with Transformers: One Policy Across Diverse Systems |
| 2603.15078 | arxiv | arXiv id_list | Timely Best Arm Identification in Restless Shared Networks |
| 2603.17416 | arxiv | arXiv id_list | Physics-informed Deep Mixture-of-Koopmans Vehicle Dynamics Model with Dual-branch Encoder for Di |
| 2603.18642 | arxiv | arXiv id_list | Evaluating Model-Free Policy Optimization in Masked-Action Environments via an Exact Blackjack O |
| 2603.19073 | arxiv | arXiv id_list | Finite-sample bounds for multi-output system identification |
| 2603.21539 | arxiv | arXiv id_list | Stochastic Trajectory Influence Functions for LQR: Joint Sensitivity Through Dynamics and Noise  |
| 2603.22039 | arxiv | arXiv id_list | RAFL: Generalizable Sim-to-Real of Soft Robots with Residual Acceleration Field Learning |
| 2603.22708 | arxiv | arXiv id_list | Why Database Manuals Are Not Enough: Efficient and Reliable Configuration Tuning for DBMSs via C |
| 2603.24756 | arxiv | arXiv id_list | Nested Extremum Seeking Converges to Stackelberg Equilibrium |
| 2603.25840 | arxiv | arXiv id_list | Accelerating Bayesian Optimization for Nonlinear State-Space System Identification with Applicat |
| 2603.26339 | arxiv | arXiv id_list | Curvature-aware Expected Free Energy as an Acquisition Function for Bayesian Optimization |
| 2603.26547 | arxiv | arXiv id_list | A Lyapunov Analysis of Softmax Policy Gradient for Stochastic Bandits |
| 2603.27039 | arxiv | arXiv id_list | Measuring Human Behavior Through Controlled Perturbations: A Framework for Behavioral System Ide |
| 2603.27442 | arxiv | arXiv id_list | Interpretable Physics Extraction from Data for Linear Dynamical Systems using Lie Generator Netw |
| 2603.27586 | arxiv | arXiv id_list | Huber-based Robust System Identification with Near-Optimal Guarantees Across Independent and Adv |
| 2603.27615 | arxiv | arXiv id_list | Adaptive differentiating filter: case study of PID feedback control |
| 2603.28938 | arxiv | arXiv id_list | Optimistic Online LQR via Intrinsic Rewards |
| 2604.00520 | arxiv | arXiv id_list | BLISS: Global Blind Identification of Linear Systems with Sparse Inputs |
| 2604.01142 | arxiv | arXiv id_list | Planning for Change: Reinforcement Learning Combined with Bounded Extremum Seeking for Robotic C |
| 2604.01406 | arxiv | arXiv id_list | Causal Optimal Coupling for Gaussian Input-Output Distributional Data |
| 2604.01450 | arxiv | arXiv id_list | Discrete-Time Event-Triggered Extremum Seeking |
| 2604.02438 | arxiv | arXiv id_list | Mitigating Data Scarcity in Spaceflight Applications for Offline Reinforcement Learning Using Ph |
| 2604.02503 | arxiv | arXiv id_list | Nonlinear System Identification of Variable-Pitch Propellers Using a Wiener Model |
| 2604.03138 | arxiv | arXiv id_list | Logarithmic Barrier Functions for Practically Safe Extremum Seeking Control |
| 2604.04754 | arxiv | arXiv id_list | Extremum Seeking of Static Maps in the Presence of Unknown Large Time-Varying Delays |
| 2604.04986 | arxiv | arXiv id_list | Enhancing sample efficiency in reinforcement-learning-based flow control: replacing the critic w |
| 2604.05518 | arxiv | arXiv id_list | Optimal Centered Active Excitation in Linear System Identification |
| 2604.05639 | arxiv | arXiv id_list | Estimating Dynamic Marginal Policy Effects under Sequential Unconfoundedness |
| 2604.05856 | arxiv | arXiv id_list | Neural Network Pruning via QUBO Optimization |
| 2604.06158 | arxiv | arXiv id_list | Distributionally Robust Regret Optimal LQR with Common Stage-Law Ambiguity |
| 2604.06338 | arxiv | arXiv id_list | Adaptive Control with Sparse Identification of Nonlinear Dynamics |
| 2604.07069 | arxiv | arXiv id_list | Controller Design for Structured State-space Models via Contraction Theory |
| 2604.08185 | arxiv | arXiv id_list | State and Trajectory Estimation of Tensegrity Robots via Factor Graphs and Chebyshev Polynomials |
| 2604.09340 | arxiv | arXiv id_list | Designing Markets for Screening: Optimal Composition and the Geometry of Surplus |
| 2604.11930 | arxiv | arXiv id_list | Quantized Online LQR |
| 2604.13224 | arxiv | arXiv id_list | Micro and Macro Perspectives on Production-Based Markups |
| 2604.14879 | arxiv | arXiv id_list | SOLIS: Physics-Informed Learning of Interpretable Neural Surrogates for Nonlinear Systems |
| 2604.14924 | arxiv | arXiv id_list | Dynamic Lagrange Multipliers in a Non-concave Utility Framework |
| 2604.17627 | arxiv | arXiv id_list | SLO-Guard: Crash-Aware, Budget-Consistent Autotuning for SLO-Constrained LLM Serving |
| 2604.17693 | arxiv | arXiv id_list | COSAC: Counterfactual Credit Assignment in Sequential Cooperative Teams |
| 2604.18507 | arxiv | arXiv id_list | Learning the Riccati solution operator for time-varying LQR via Deep Operator Networks |
| 2604.21270 | arxiv | arXiv id_list | CLT-Optimal Parameter Error Bounds for Linear System Identification |
| 2604.22138 | arxiv | arXiv id_list | Training Dynamics and Induced Preconditioning of ReLU Policy Gradient for Scalar LQR |
| 2604.23269 | arxiv | arXiv id_list | WSINDy for Model Predictive Control with Applications to Fusion, Drones, and Chaos |
| 2604.23650 | arxiv | arXiv id_list | On Tikhonov Regularization for Direct and Indirect Data-Driven LQR Control |
| 2605.00317 | arxiv | arXiv id_list | Real-Time Neural Distributed Energy Resources Dispatch with Feasibility Guarantees |
| 2605.01550 | arxiv | arXiv id_list | Joint typical periodic optimization: systems with stable hyperbolicity |
| 2605.02517 | arxiv | arXiv id_list | Least Costly Space-Filling Experiment Design for the Identification of a Nonlinear System |
| 2605.02600 | arxiv | arXiv id_list | CoRAL: Contact-Rich Adaptive LLM-based Control for Robotic Manipulation |
| 2605.03208 | arxiv | arXiv id_list | Kerncap: Automated Kernel Extraction and Isolation for AMD GPUs |
| 2605.04419 | arxiv | arXiv id_list | A Numerical Investigation of Extremum-Seeking-Based Command Generation for Adaptively Controlled |
| 2605.05152 | arxiv | arXiv id_list | Age of Gossip in Ring Networks With Non-Poisson Updates |
| 2605.05514 | arxiv | arXiv id_list | When Semantic Communication Meets Queueing: Cross-Layer Latency and Task Fidelity Optimization |
| 2605.05644 | arxiv | arXiv id_list | AoI-Guided Client Selection for Robust and Timely Federated Intrusion Detection in Cloud-Edge Se |
| 2605.06804 | arxiv | arXiv id_list | Data-Driven Koopman-Enhanced Extremum Seeking for Oscillation Damping in Nonlinear Systems |
| 2605.07052 | arxiv | arXiv id_list | A Behavioral Framework for Data-Driven Modeling of Nonlinear Systems in Vector-Valued Reproducin |
| 2605.07674 | arxiv | arXiv id_list | Differentially Private Auditing Under Strategic Response |
| 2605.08362 | arxiv | arXiv id_list | Kernel-based linear system identification using augmented Krylov subspaces |
| 2605.09164 | arxiv | arXiv id_list | Data-Driven Inverse Reinforcement Learning of Linear Systems with Model Uncertainty: A Convex Op |
| 2605.10745 | arxiv | arXiv id_list | How Time-Sensitive are IoBNT Networks? An Age of Information Perspective for In-Body Monitoring |
| 2605.12203 | arxiv | arXiv id_list | Efficient Learning of Affine and Rational Dependency LPV Models With Linear Fractional Represent |
| 2605.13209 | arxiv | arXiv id_list | Comparing the Performance of Heterogeneous Conjugate Gradient and Cholesky Solvers on Various Ha |
| 2605.14161 | arxiv | arXiv id_list | Optimizing Grid-Forming Controls using Relay-based Extremum Seeking to Enhance Transient Perform |
| 2605.14351 | arxiv | arXiv id_list | Randomized Atomic Feature Models for Physics-Informed Identification of Dynamic Systems |
| 2605.14489 | arxiv | arXiv id_list | A Novel Schur-Decomposition-Based Weight Projection Method for Stable State-Space Neural-Network |
| 2605.14526 | arxiv | arXiv id_list | DiffPhD: A Unified Differentiable Solver for Projective Heterogeneous Materials in Elastodynamic |
| 2605.15431 | arxiv | arXiv id_list | Optimizing Chilled Water Systems with Cooling Towers via Virtual Power Metrics and Extremum-Seek |
| 2605.15590 | arxiv | arXiv id_list | Generalized Error Bounds in the Recovery of Solitary Wave Profiles |
| 2605.16176 | arxiv | arXiv id_list | How Far Back in Time a Digital Twin Reflects the State of the Physical Object: Age of Staleness |
| 2605.16584 | arxiv | arXiv id_list | Provably Efficient Sensor Allocation for Unknown High-dimensional Systems with Limited Sensing |
| 2605.17394 | arxiv | arXiv id_list | Stochastic Zeroth-Order Optimization Under Heavy-Tailed Noise |
| 2605.17964 | arxiv | arXiv id_list | Fractional-Order Subband p-Norm Adaptive Filter via Transformation Nearest Kronecker Product Dec |
| 2605.18373 | arxiv | arXiv id_list | Dynamic robotic cloth folding with efficient Koopman operator-based model predictive control |
| 2605.19468 | arxiv | arXiv id_list | Optimal airfoils in the intermediate Reynolds number range |
| 2605.20038 | arxiv | arXiv id_list | A New Simple-to-Configure Self-Perturbing Multivariable Extremum-Seeking Controller |
| 2605.20232 | arxiv | arXiv id_list | Universal Extremum Seeking Mechanism for Lift Variation in Soaring Birds Flight: A New Paradigm  |
| 2605.21013 | arxiv | arXiv id_list | Rectangular Multispectral Perturbation Theory |
| 2605.21016 | arxiv | arXiv id_list | Partially Observable Restless Bandits for Age-Optimal Scheduling over Markov Channels |
| 2605.21179 | arxiv | arXiv id_list | KSOS-BO: Improving Sampling in Bayesian Optimization via Kernel Sum of Squares |
| 2605.21328 | arxiv | arXiv id_list | SAOITHE: Sustainable Age-of-Information-Based Timely Status Updating for Hardware-constrained Ed |
| 2605.23029 | arxiv | arXiv id_list | Extremum seeking with exponential convergence via high-order Lie bracket approximations |
| 2605.24317 | arxiv | arXiv id_list | Quantitative Stability of Generalized $p$-Area Minimizing Surfaces |
| 2605.24714 | arxiv | arXiv id_list | Age of Information Optimization for Status Updates in Integrated Sensing and Communication Syste |
| 2605.25105 | arxiv | arXiv id_list | Model-Free Control approach for pH Regulation in Thin-Layer Photobioreactors |
| 2605.26247 | arxiv | arXiv id_list | Age of Information in Time-Varying Multi-Priority Queues |
| 2605.26619 | arxiv | arXiv id_list | PIDM-DP: Physics-Informed Diffusion with Dormand-Prince Integration for Chaotic System Identific |
| 2605.27076 | arxiv | arXiv id_list | Cost of Structural Learning Under Censored Feedback: A Threshold-Bandit Approach |
| 2605.28399 | arxiv | arXiv id_list | Information Age-Controllability Trade-offs in Communication-Constrained Networks |
| 2605.29939 | arxiv | arXiv id_list | CRB-Guided Framework Design and Resource Allocation for Indoor mmWave ISCC Systems |
| 2606.00059 | arxiv | arXiv id_list | Reinforcement Learning for Optimal Experiment Design in Parameter Identification of Mechatronic  |
| 2606.00969 | arxiv | arXiv id_list | Nonsmooth High-Order Averaging Theory with Application to Extremum Seeking Optimization and Cont |
| 2606.04361 | arxiv | arXiv id_list | When Mean Age Is Not Enough: Distribution-Aware Scheduling for Networked LQR Control |
| 2606.06790 | arxiv | arXiv id_list | Learning All-Terrain Locomotion for a Planetary Rover with Actively Articulated Suspension |
| 2606.07906 | arxiv | arXiv id_list | Extremum Seeking Control Based Adaptive Compensation of Position Sensor Harmonics in PMSM Drives |
| 2606.08315 | arxiv | arXiv id_list | Benchmarking Sequential Feedback Optimization for Wind Farm Power Maximization |
| 2606.09829 | arxiv | arXiv id_list | Adaptive Derivative Estimation via Stein's Unbiased Risk |
| 2606.09902 | arxiv | arXiv id_list | The Whale That Outswam Evolution: Swarm Intelligence Maximises Memory in Connectome Reservoirs |
| 2606.10774 | arxiv | arXiv id_list | Asynchronous Decentralized Federated Learning over Lossy Wireless Links via Reception- and Age-A |
| 2606.11474 | arxiv | arXiv id_list | Mahalanobis-Guided Latent OOD Detection for Hybrid ES-DRL Control in Time-Varying Systems |
| 2606.12314 | arxiv | arXiv id_list | Near Field Multi-Band Localization: CRB, Efficient Estimator, and Threshold SNR |
| 2606.12349 | arxiv | arXiv id_list | Traceable Virtual Sea Trials in the Marine Robotics Unity Simulator for Manoeuvring Assessment o |
| 2606.12612 | arxiv | arXiv id_list | The Mathematics of Heuristic Portfolio Optimization (HPO) |
| 2606.14312 | arxiv | arXiv id_list | PLRTune: Importance Pre-Sampling and LLM-Guided Reinforcement Learning for Automatic Database Tu |
| 2606.14426 | arxiv | arXiv id_list | A Floquet Mode LQR for Orbital Station-Keeping in Cislunar Space |
| 2606.14942 | arxiv | arXiv id_list | Bayesian Variational System Identification with Weak-Form Residual Likelihoods |
| 2606.15688 | arxiv | arXiv id_list | Twin-in-the-Loop Optimization and Fundamental Limits of Position--Velocity Estimation in Cell-Fr |
| 2606.15746 | arxiv | arXiv id_list | Age and Stability Trade-offs in Remote Monitoring Systems |
| 2606.17388 | arxiv | arXiv id_list | Agent Utilities over Generalized Voronoi Regions and their Gradients |
| 2606.18887 | arxiv | arXiv id_list | Efficient Image Registration for Ultrasound Localization Microscopy by Obtaining Gradients via I |
| 2606.19275 | arxiv | arXiv id_list | Reconstruction Limits for Repeated Differentially Private Aggregates: A Cramer-Rao Perspective o |
| 2606.20318 | arxiv | arXiv id_list | AgenticDB: Self-Evolving Reconfiguration Framework for Database Workloads |
| 2606.20373 | arxiv | arXiv id_list | AutoPass: Evidence-Guided LLM Agents for Compiler Performance Tuning |
| 2606.20907 | arxiv | arXiv id_list | Velocity Information Geometry of Coherent Intra-CPI Waveform Agility |
| 2606.21621 | arxiv | arXiv id_list | Differential LEO Navigation under Asynchronous Satellite Clocks: Architecture and Performance Bo |
| 2606.21636 | arxiv | arXiv id_list | Second order mixed moment inequalities based on Gram matrices |
| 2606.22040 | arxiv | arXiv id_list | Deep RL- Tuned Mo del-Free Adaptive Control for Lower-Limb Exoskeletons During Sit-to-Stand Tran |
| 2606.22223 | arxiv | arXiv id_list | Regret-Guaranteed Safe Switching: LQR Setting with Unknown Dynamics |
| 2606.23077 | arxiv | arXiv id_list | Non-intrusive nonlinear reduced-order modeling with variable projection |
| 2606.23119 | arxiv | arXiv id_list | Enormous Fluid Antenna Systems (E-FAS) for Wireless Sensing: Channel Modeling and Conditional Es |
| 2606.25566 | arxiv | arXiv id_list | Interplay between VAoI, Packet Error Rate, and Delay for Energy-Efficient Remote Monitoring |
| 2606.25716 | arxiv | arXiv id_list | Imprecise Transition Matrices for Markov Cohort Models: Lower and Upper Expectations with a Prac |
| 2606.26164 | arxiv | arXiv id_list | \chisao{}: A GPU-Native Parallel Optimizer for Multimodal Black-Box Functions via Convergence-An |
| 2606.26376 | arxiv | arXiv id_list | pysib: An Open-Source Python Toolbox for Linear System Identification |
| 2606.26575 | arxiv | arXiv id_list | IDEA: Insensitive to Dynamics Mismatch via Effect Alignment for Sim-to-Real Transfer in Multi-Ag |
| 2606.27455 | arxiv | arXiv id_list | Directed Graph Topology Inference via Graph Filter Identification |
| 2606.28586 | arxiv | arXiv id_list | Constructor-Theoretic Optical Time: Delay, Phase, and Fisher Distinguishability as Physical Task |
| 2606.29611 | arxiv | arXiv id_list | Age of Information Under DCC Rate Constraints for V2I Broadcast Along Urban Corridors |
| 2606.30568 | arxiv | arXiv id_list | Towards World Model-Empowered Integrated Sensing, Communication, and Decision for Complex Unmann |
| 2606.30776 | arxiv | arXiv id_list | Optimal Auction Design for Constrained Buyers |
| 2606.31303 | arxiv | arXiv id_list | Minimizing Quantized Semantic Age of Information (QSAoI) in Foundation Model-Based Semantic Comm |
| 2607.01739 | arxiv | arXiv id_list | Development and Identification of a Linear Low-Speed Ship Maneuvering Model from Full-Scale Data |
| 2607.02205 | arxiv | arXiv id_list | Actuator Reality Shaping for Zero-Shot Sim-to-Real Robot Learning |
| 2607.02458 | arxiv | arXiv id_list | Nonholonomic Source Seeking by Torque Tuning: Local and Semi-Global Feedbacks |
| 2607.02566 | arxiv | arXiv id_list | Earth-baseline VLBI restores the observability of a lunar surface station in joint orbit-and-clo |
| 2607.03067 | arxiv | arXiv id_list | Robust optical design and closed-form tolerancing through autodiff-based Hessian spectral analys |
| 2607.04996 | arxiv | arXiv id_list | Version-Aware Communication in Multi-Hop IoT Networks with Feedback |
| 2607.05957 | arxiv | arXiv id_list | Delay-Aware Active Triangulation with Uncertainty-Driven Multi-Agent Reinforcement Learning for  |
| 2607.06103 | arxiv | arXiv id_list | Repeated Contention Scheduling: A Novel Resource Allocation Algorithm Toward 6G Vehicular Networ |
| 2607.06642 | arxiv | arXiv id_list | The Approximation Ratio for the Risk of Myopic Bayesian Active Learning for Linear Regression |
| 2607.10276 | arxiv | arXiv id_list | Bayesian Robustness Values for Modern Causal Panel Estimators via Riesz Representations |
| 2607.11063 | arxiv | arXiv id_list | AdvNav: Behavior-Guided Black-Box Adversarial Attacks on Vision-Language Navigation |
| 2607.12721 | arxiv | arXiv id_list | High-Precision Hybrid FA-PSO Based Inversion of Building Material Parameters for Fundamental Wir |
| 2607.13319 | arxiv | arXiv id_list | Adapting Generalist Vehicle Models for High-Speed MPC Across Terrains |
| 2607.16672 | arxiv | arXiv id_list | A projection-free approach toward mapping the structured polarization fields |
| 2607.16849 | arxiv | arXiv id_list | Attosecond delay metrology beyond the photon coherence time with spectrally resolved Hong-Ou-Man |
| 2607.16902 | arxiv | arXiv id_list | Learning to Stay Fresh: A Self-Learning Semantic Framework for Underwater Internet of Things |
| 2607.18509 | arxiv | arXiv id_list | When Trade Produces Knowledge: Dynamic Pricing, Bilateral Learning, and Trust |
| 2607.18736 | arxiv | arXiv id_list | Non-Square UPA-Enabled XL-MIMO Systems: Anisotropic Near-Field Characterization, Fundamental Lim |
| 2607.18766 | arxiv | arXiv id_list | Low-Altitude UAV-Assisted Bistatic ISAC: Closed-form 3D CRLB and Coverage Analysis |
| 2607.18893 | arxiv | arXiv id_list | Flexible Intelligent Metasurface-Aided ISAC: User Fairness Optimization and Performance Evaluati |
| 2607.19216 | arxiv | arXiv id_list | Squeezing the Most Out of Preemption for AoI Minimization: Single-source Case |
| 2607.19271 | arxiv | arXiv id_list | Model-Agnostic Meta Learning for Differentiable MPC |
| 2607.20967 | arxiv | arXiv id_list | Update the Unseen Only: Minimizing AoI for Collaborative Perception through Online Learning |
| 2607.22357 | arxiv | arXiv id_list | Uncertainty-Aware Fusion for Resilient Distributed Radar Sensing |
| 2607.23005 | arxiv | arXiv id_list | Mobile Tracking via Target-Mounted IRS-Assisted ISAC System |
| 2607.23595 | arxiv | arXiv id_list | Age-of-Information Aware Federated Learning with Finite Speed Pinching Antenna |
| 2607.23725 | arxiv | arXiv id_list | Near-Oracle Robustification of Finite-Difference Stochastic Gradient Estimators via Cheap Pilot  |
| 2607.24161 | arxiv | arXiv id_list | Slowly Divergent Trajectories for Weighted Singular Vectors in R^2 |
| 2607.24778 | arxiv | arXiv id_list | Warm-Start Interior-Point Methods for Online Second-Order Cone Programming |
| 2607.25223 | arxiv | arXiv id_list | Event-Triggered Discrete-Time Multivariable Extremum Seeking Systems |
| 2607.27524 | arxiv | arXiv id_list | Estimated-State Adaptive Sliding Mode Control and Disturbance Observation Using Second-Order Sur |
| 2607.27626 | arxiv | arXiv id_list | Real-Time Hard Peak Age-of-Information Safety with No-Regret Learning |
| 2607.28158 | arxiv | arXiv id_list | Stochastic Average Consensus Filtering and Distributed State Estimation for Boolean Control Netw |
| 2607.28614 | arxiv | arXiv id_list | Tampered Memory Elephant Random Walk on One-Dimensional Integer Lattice |
| 2607.29060 | arxiv | arXiv id_list | Geometry-Aware Resource Allocation for Network-Level ISAC Systems |
| 2607.29445 | arxiv | arXiv id_list | QR-Structured Thermal Triggers for Targeted Semantic Attacks on Infrared Vision-Language Models |
| 2607.29593 | arxiv | arXiv id_list | Convergence and Regret of the Policy Gradient for Multi-Armed Bandits in Diffusion Environment |
| 2608.00061 | arxiv | arXiv id_list | Reliability- and Connectivity-Constrained Age-of-Information Optimization for UAV Swarm IoT Data |
| 2608.01006 | arxiv | arXiv id_list | Age Dispersion and Higher-Order AoI in Status Update Systems |
| 2608.01128 | arxiv | arXiv id_list | MA-HEAD-Net: Adaptive Rule-Guided Multi-Agent DRL for AoI Minimization in UAV-Assisted Emergency |
| 2608.01555 | arxiv | arXiv id_list | Sensitivity-driven Adaptive Contention Window Optimization for IEEE 802.11 based V2I Networks |
| 2608.01998 | arxiv | arXiv id_list | TALSC: Timeliness-Aware Large-Small VLM Collaboration for Infrastructure-Assisted Autonomous Dri |
| 2608.02075 | arxiv | arXiv id_list | Efficient re-sampling in quasi-probability decompositions |
| 2608.02231 | arxiv | arXiv id_list | Open-Loop Transmission with Discrete Blocklengths: Characterization of AoI-Optimal Schedules |
| 2608.02286 | arxiv | arXiv id_list | A Spatio-Temporal Model for Information Freshness in Massive Random Access |
| 2608.02485 | arxiv | arXiv id_list | Age of Information in Non-Terrestrial Networks with Energy Harvesting |
| 2608.02872 | arxiv | arXiv id_list | Accurate Multi-perturbation Localization in Optical Fibers with Polarization-based Forward Sensi |
| 2608.03293 | arxiv | arXiv id_list | Prior-Aided Iterative Channel Reconstruction with Optimized Frame Structure for DSE Mitigation i |
| 2608.03483 | arxiv | arXiv id_list | Continue or Replan? Bernoulli-Continuation Policy Learning for Adaptive Horizon Execution |
| 2608.03548 | arxiv | arXiv id_list | Adaptive Stepsizes With Certified Convergence in Distributed Gradient Tracking With Quadratic Co |
| 2608.04189 | arxiv | arXiv id_list | Structured Differentiable Optimization for Efficient Decision-focused Learning in Power Systems |
| 2608.04673 | arxiv | arXiv id_list | Differential 6-DOF Pose Estimation with Provable First-Order Immunity to Camera Calibration Erro |
| 2608.04817 | arxiv | arXiv id_list | A Knowledge-Centric Communication For Autonomous Cislunar Networks |
| 2608.05348 | arxiv | arXiv id_list | TSDM: A Scheduling Policy for Joint Throughput-AoI Optimization in Multichannel Wireless Network |
| 2608.05416 | arxiv | arXiv id_list | Spectral Distillation: From Nonlinear Dynamics to Linear State-Space Models |
| 2608.06574 | arxiv | arXiv id_list | Implicit Neural Speckle Denoising |
| 2608.07636 | arxiv | arXiv id_list | Adversarial Attacks on Deep OCR Systems |
| 2608.08060 | arxiv | arXiv id_list | ZOMP: Zeroth-Order Multi-Modal Prompt Tuning for Vision-Language Models |
| 2608.09125 | arxiv | arXiv id_list | Trajectory Divergence Horizon Decision for Reliable Dual-Arm Surgical Subtask Manipulation |
| 2608.09411 | arxiv | arXiv id_list | Joint Age-of-Latent and Resource Minimization for Wireless Multi-Camera Perception With Temporal |
| 2608.09492 | arxiv | arXiv id_list | Rethink Before You Execute: Adaptive Execution for World Action Models |
| 2608.10246 | arxiv | arXiv id_list | Towards Co-Designed Event-Triggered Extremum Seeking |
| 2608.10270 | arxiv | arXiv id_list | Achievable Accuracy and Cramer Rao Bounds for SSB Based LEO Positioning in NR NTN |
| 2608.10474 | arxiv | arXiv id_list | Stay or Stray - A Dynamical Systems Viewpoint of Popularity Bias |
| 2608.10640 | arxiv | arXiv id_list | Threshold-Based Spiking Neural Networks for Event-Driven Status Update Systems |
| 2608.10729 | arxiv | arXiv id_list | Optimal Stopping of Self-Refining Foundation Models |
| 2608.11130 | arxiv | arXiv id_list | Posterior contraction rates in Sobolev norms and Bayesian derivative estimation for infinite-dim |
| 2608.11486 | arxiv | arXiv id_list | Stability of Finite-Batch Particle Mean-Field Variational Inference Beyond Strong Convexity |
| 2608.11599 | arxiv | arXiv id_list | An AoI-oriented Time-Frequency Distributed Access Mechanism in Wireless Sensor Networks with Spe |
| 2608.11932 | arxiv | arXiv id_list | Structure and Conditioning in Finite-Horizon Continuous-Time Inverse LQR with Unknown Dynamics |
| 2608.12521 | arxiv | arXiv id_list | Dynamical uncertainty geometry for nonlinear transport |
| 2608.13083 | arxiv | arXiv id_list | AoI-Guaranteed Dynamic Route Planning for Connected Vehicles |
| 2608.13294 | arxiv | arXiv id_list | Deterministic Maximum Likelihood Direction Finding in the Mixture Noise of Gaussian and Spherica |
| 2608.13360 | arxiv | arXiv id_list | Robust Space-Filling Input Design via Stochastic Optimization |
| 2608.14184 | arxiv | arXiv id_list | Positioning with Flexible Reflectors: Solution and Performance Analysis |
| 2608.14769 | arxiv | arXiv id_list | Impulse Response Estimation via Laguerre-Fourier Expansion |
| 2608.14856 | arxiv | arXiv id_list | BRAID: Learning Equilibrium Maps in Interdependent Security Games via Weight-Tied Iterative Grap |
| 2608.15501 | arxiv | arXiv id_list | Target Localization and Self-Calibration in a Multistatic Radar System |
| 2608.15792 | arxiv | arXiv id_list | Tensor Decomposition-Based Wireless Sensing for MIMO-OFDM ISAC via Flexible Spatial-Temporal-Spe |
| 2608.15894 | arxiv | arXiv id_list | Adaptive Sampling Trust Region Optimization for Derivative-free Stochastic Functions and Determi |
| 2608.15966 | arxiv | arXiv id_list | A Banach-Space Theory of Markovian Halpern Iteration for Non-Expansive Maps |
| 2608.16216 | arxiv | arXiv id_list | Beyond Peak Backlog: Conditional Energy and Temporal Geometry in Capacity-Constrained Delayed Ba |
| 2608.18123 | arxiv | arXiv id_list | Learning the Center and Radius of Wasserstein Ambiguity Sets for Data-Driven Decision Making |
| 2608.18129 | arxiv | arXiv id_list | Simulation-Optimization of Systems of Optimizers: Exploiting the Inner Optimization's Geometry |
| 2608.18374 | arxiv | arXiv id_list | Inference and Uncertainty Quantification for Streaming $r$-PCA |
| 2608.19074 | arxiv | arXiv id_list | A Mini-Batch Counterexample to Last-Iterate Convergence in Definable Optimization |
| 2608.20207 | arxiv | arXiv id_list | Direct vs. Indirect Data-Driven Control: Case-study of Switching Systems Stability |
| 2608.20545 | arxiv | arXiv id_list | AoI-Oriented Globally Optimal Joint Source and Update Scheduling in Fluid Antenna Systems |
| 2608.21407 | arxiv | arXiv id_list | Mamba-based Selective State Space Modeling Improves the Accuracy-Complexity Tradeoff of SmolVLA  |
| 2608.21533 | arxiv | arXiv id_list | Model-Free Adaptive Parameter Tuning for Efficient Multi-Robot Warehouse Operations |
| 2608.21596 | arxiv | arXiv id_list | Age-Optimal Target Wake Time: Provably Good Wake Schedules for Energy-Constrained Wi-Fi Status U |
| 2608.22250 | arxiv | arXiv id_list | Deterministic Cramer-Rao Bounds for Coherent Direction-of-Arrival Estimation: Rank Information V |
| 2608.22636 | arxiv | arXiv id_list | Q-Learning with Stable Infinite-Dimensional Linear Function Approximation |
| 2608.22840 | arxiv | arXiv id_list | Equilibrium in Multi-Agent Reinforcement Learning |
| 2608.23887 | arxiv | arXiv id_list | Interpreting Control Latents for System Identification via Conditional Flow Matching |
| 2608.25304 | arxiv | arXiv id_list | SAUSS: Stochastic Approximation with Unbiased Simulated Scores for Limited Dependent Variable Mo |
| 2608.26505 | arxiv | arXiv id_list | Closing the Loop on the Poppy Humanoid: Bipedal Locomotion with Linear-Quadratic Control and Lea |
| 2608.26548 | arxiv | arXiv id_list | Camera Calibration Using Inaccurate and Asynchronous Discrete GPS Trajectory from Drones |
| 2608.27688 | arxiv | arXiv id_list | SafeStep: An Interactive Demonstration of Semantic Communication for Pedestrian Safety Monitorin |
| 2608.28173 | arxiv | arXiv id_list | Resource Allocation for Cloud Radar Networks with Communication Constraints |
| 2608.28235 | arxiv | arXiv id_list | Direct Adaptive Certification of High-Dimensional Entanglement with Bell Tests |
| 2608.29641 | arxiv | arXiv id_list | Harness-RL: Black-Box Reinforcement Learning with Action-Args Decoupling for Central-Agent Multi |
| 2608.29908 | arxiv | arXiv id_list | Finite Sample Identification of Analytic Nonlinear Systems |
| 2608.30382 | arxiv | arXiv id_list | Convergence rates for the RMSprop optimizer with full control of the hyperparameters |
| 2608.30433 | arxiv | arXiv id_list | A Hybrid PEM-GP Framework for Uncertainty-Aware System Identification of Quadcopters |
| 2608.30554 | arxiv | arXiv id_list | Strong law of large numbers for generalized operator means II |
| 2608.31140 | arxiv | arXiv id_list | Semantic Freshness Optimal Sampling and Transmission for Gossiping Receivers |
| 2609.00484 | arxiv | arXiv id_list | Extremum Seeking Control: Three Revolutions and the Road Ahead |
| 2609.00717 | arxiv | arXiv id_list | Extending Subsampling to Sequential Stopping |
| 2609.00771 | arxiv | arXiv id_list | Non-Prehensile Throwing: A Reinforcement Learning Perspective |
| 2609.01082 | arxiv | arXiv id_list | Update for Decisions, Not Freshness: Goal-Oriented Status Updating and Selective Offloading at t |
| 2609.01225 | arxiv | arXiv id_list | Freshness-Aware Constrained Sensing-Aided Beam Prediction with Knowledge Distillation |
| 2609.01838 | arxiv | arXiv id_list | Differential Games for Compositional Handling of Competing Control Tasks |
| 2609.02042 | arxiv | arXiv id_list | Act More, Decide Less: Skill-Guided Adaptive Action Chunking for Long-Horizon LLM Agents |
| 2609.02071 | arxiv | arXiv id_list | Turnpike properties in nonlinear system identification |
| 2609.02363 | arxiv | arXiv id_list | On the invariance of risk-sensitive LQR gain under input randomization |
| 2609.03921 | arxiv | arXiv id_list | Data-Based Clustering and Control of Similar Biological Systems |
| 2609.04363 | arxiv | arXiv id_list | Phase Independent Measurement of Weak Coherent Optical Signals |
| 2609.04364 | arxiv | arXiv id_list | Scalable Edge-assisted Fusion and Path Prediction for Connected Autonomous Vehicles |
| 2609.04401 | arxiv | arXiv id_list | Multivariable Extremum Seeking for Locally Lipschitz Objectives |
| 2609.06135 | arxiv | arXiv id_list | Physical-Field Reconstruction from Sparse Observations: When Are Diffusion Models Preferable to  |
| 2609.06191 | arxiv | arXiv id_list | Optimization Algorithm-Assisted Nanostructure Engineering for Performance Enhancement of Thin-Fi |
| 2609.06505 | arxiv | arXiv id_list | Lie bracket approximations of RMSprop for Extremum Seeking Control |
| 2609.06696 | arxiv | arXiv id_list | Bayes Estimators with Performance Comparable to Empirical Bayes Estimators and Improved Local Ro |
| 2609.07484 | arxiv | arXiv id_list | Robust Multi-Source DoA Estimation under Weather-Induced Distortion: Structured Covariance Metho |
| 2609.08567 | arxiv | arXiv id_list | Structured Positive-Definite Optimal Control Synthesis of Closed-Loop Recommendation Systems ove |
| 2609.08740 | arxiv | arXiv id_list | PAC-Bayesian Bounds for Learning Partially Observed Stochastic Linear Time-Invariant State-Space |
| 2609.08751 | arxiv | arXiv id_list | Optimal input design via Frank-Wolfe |
| 2609.08827 | arxiv | arXiv id_list | Hybrid Continuous DoA Estimation with Shared-Radius Co-Prime Circular Arrays |
| 2609.08929 | arxiv | arXiv id_list | The consequences of high SMR operating costs in electricity markets |
| 2609.09480 | arxiv | arXiv id_list | Gaussian Approximation in Wasserstein-p: Markovian Martingale Differences and Stochastic Approxi |
| 2609.09934 | arxiv | arXiv id_list | Fast Collision-Free Acquisition in 1-Persistent Age-Threshold Slotted ALOHA via Role-Protected C |
| 2609.10252 | arxiv | arXiv id_list | Surrogate-Assisted Inverse Design and Temperature-Dependent Electrothermal Analysis of an All-Ox |
| 2609.11171 | arxiv | arXiv id_list | A sequential smoothing majorant stochastic approximation method for nonconvex nonconcave minimax |
| 2609.11432 | arxiv | arXiv id_list | AoI-driven Anomaly Detection Framework for Communication Networks |
| 2609.11567 | arxiv | arXiv id_list | Non-monotone direct-search methods for deterministic and stochastic derivative-free optimization |
| 2609.13622 | arxiv | arXiv id_list | Worse Routes, Fresher Information: Preemption Redefines Which Route is Best |
| 2609.14192 | arxiv | arXiv id_list | Resilient Extremum Seeking Control for Cyber-Physical Systems Under Denial-of-Service Attacks |
| 2609.14232 | arxiv | arXiv id_list | Gaussian-trigonometric functional link artificial neural network: design and analysis |
| 2609.14327 | arxiv | arXiv id_list | Nonparametric Variance-Penalized Actor-Critic: Statistical Inference for Risk-Sensitive Reinforc |
| 2609.14800 | arxiv | arXiv id_list | Self-Adaptive Threshold ALOHA |
| 2609.14922 | arxiv | arXiv id_list | Steady-State Convergence of Stochastic Approximation |
| 2609.14959 | arxiv | arXiv id_list | High-Probability Nash Regret for Decentralized Learning in Markov $α$-Potential Games: Episodic  |
| 2609.15356 | arxiv | arXiv id_list | Sparse Channel Estimation and Signal Recovery for Reduced-PAPR Visible Light Optical OFDM System |
| 2609.15406 | arxiv | arXiv id_list | Statistical Inference-Based Channel Estimation for LD-Driven Visible Light O-OFDM Systems in the |
| 2609.15420 | arxiv | arXiv id_list | Data-Aided Variational Bayesian Inference for CSI Estimation over Doubly-Selective DCO-OTFS MIMO |
| 2609.15537 | arxiv | arXiv id_list | Safe Newton-Based Extremum Seeking for Static Maps with Delayed Output Measurements |
| 2609.16523 | arxiv | arXiv id_list | On Delay-robustness of Extremum Seeking of Nonlinear Static Maps with Small Disturbance |
| 2609.16569 | arxiv | arXiv id_list | Joint Freshness and Age-Dispersion Control over Finite-State Markov Wireless Channels |
| 2609.17759 | arxiv | arXiv id_list | Derivative-Free Structured Updates for Muon |
| 2609.17859 | arxiv | arXiv id_list | Hybrid Sequential Feedback Optimization for Wind Farm Power Maximization |
| 2609.18127 | arxiv | arXiv id_list | Learning Fractional-Order Dynamics from a Single Trajectory |
| 2609.18631 | arxiv | arXiv id_list | Automatic denoising and differentiation based on Savitzky-Golay filtering and Homogeneous Differ |
| 2609.20138 | arxiv | arXiv id_list | Fast-varying Natural Frequencies and Damping Ratio Identification for Linear Time-Varying System |
| 2609.20409 | arxiv | arXiv id_list | The Bias of Nonlinear Two-Time-scale Stochastic Approximation under Constant Step-Sizes |
| 2609.21566 | arxiv | arXiv id_list | Goal-Oriented Communication and Control Co-Design via Semantic Push-Pull in Industrial IoT |
| 2609.22312 | arxiv | arXiv id_list | Data-Aided Bayesian Learning for CSI Estimation over Doubly-Selective DCO-OTFS MIMO VLC Channels |
| 2609.22642 | arxiv | arXiv id_list | Locally Private Inference for Riemannian Stochastic Optimization |
| 2609.22865 | arxiv | arXiv id_list | AoI-Driven Hierarchical Learning for Cooperative Resource Sharing in Multi-Operator UAV Networks |
| 2609.23199 | arxiv | arXiv id_list | LMMSE-Based Phase Estimator for Fiber-Optic Coherent Spread-Spectrum FBG-Based Sensing Systems |
| 2609.23323 | arxiv | arXiv id_list | Robust Beamforming and Antenna Position Optimization for MA-Assisted ISAC with Imperfectly Posit |
| 2609.23823 | arxiv | arXiv id_list | Design and Operation of a 3-Crystal Multi-Volume Reflection Array for Loss Reduction in CERN SPS |
| 2609.23848 | arxiv | arXiv id_list | Anytime-Feasible Gradient Descent for Constrained Optimization Under Gradient Uncertainty |
| 2609.24117 | arxiv | arXiv id_list | PAC-Bayesian Meta-Learning for Few-Shot Identification of Linear Dynamical Systems |
| 2609.24274 | arxiv | arXiv id_list | vla.simd: Efficient CPU Inference for Language-Conditioned Manipulation |
| 2609.25674 | arxiv | arXiv id_list | Teaching Reinforcement Learning and Humanoid Robotics to High-School Students: An Expert-Validat |
| 2609.25798 | arxiv | arXiv id_list | Secure ISAC with Sensing Privacy under Eavesdropper Uncertainty |
| 2609.27499 | arxiv | arXiv id_list | Distributed Stochastic Approximation Algorithms and Heavy-Tailed Age of Information |
| 2609.28082 | arxiv | arXiv id_list | Exact Average Consensus under Noisy Communication Links: A Decentralized Gradient Perspective |
| 2609.28728 | arxiv | arXiv id_list | Multivariable Newton-Based Extremum Seeking with Bounded Update Rates |
| 2609.28815 | arxiv | arXiv id_list | Near-Field MIMO LoS Channel Recovery Under User Antenna Asymmetry |
| 2609.29159 | arxiv | arXiv id_list | Functional dynamic mode decomposition: Learning infinite-dimensional systems from data |
| 2609.29833 | arxiv | arXiv id_list | Shrinking-Tube Concentration for Adaptive Markovian Stochastic Approximation |
| 2609.30451 | arxiv | arXiv id_list | Practical Algebraic Parameter Estimation for Noisy Data via Gaussian Process Regression |
| 2609.31172 | arxiv | arXiv id_list | Data-Driven Switched State Estimation with Sparse Sensor Scheduling for Nonlinear Networked Syst |
| 2609.31890 | arxiv | arXiv id_list | FARE: Deep Reinforcement Learning For Fair Exposure Constrained Uncertainty Aware Financial Cont |
| 2609.32837 | arxiv | arXiv id_list | Scanning While Imagining: A Scene-Graph World Model for Robotic Ultrasound Navigation |
| 2609.34791 | arxiv | arXiv id_list | Finite-Time Concentration and Convergence Rates for Projected Two-Time-Scale Stochastic Approxim |
| 2609.34911 | arxiv | arXiv id_list | Don't Throw Away the Tail: Action Upcycling for Policy Acceleration |
| 2609.35603 | arxiv | arXiv id_list | Control-Geometry Straightening for Sampling-Based Latent Planning |
| 2609.36090 | arxiv | arXiv id_list | Control and Estimation Co-Design via Envelope-Theorem Gradients |
| 2609.36250 | arxiv | arXiv id_list | Action Chunking Proximal Policy Optimization with Feedback Correction |
| 2609.36395 | arxiv | arXiv id_list | DORA: Divergence-Oriented Data-Relay Algorithm for Partially Connected Robot Teams |
| 2609.36471 | arxiv | arXiv id_list | Staircase Policy: Streaming Inference for World-Action Models with Large Action Chunks |
| 2609.36600 | arxiv | arXiv id_list | Second-Moment Stochastic Approximation Methods |
| 2609.37063 | arxiv | arXiv id_list | Controller Identifiability: The Boundary Between Logarithmic and Square-Root Local Minimax Regre |
| 2609.37147 | arxiv | arXiv id_list | Improved Distributional Diffusion Models |
| 2609.37239 | arxiv | arXiv id_list | Differentiating Bisimulation Metrics: A Framework for Parametric Markov Chain Fitting via Bicaus |
| 2609.37552 | arxiv | arXiv id_list | Wrench-ACT: Enhancing Robot Policies for Contact Rich Behavior Using Direct Wrench Control |
| 2609.37757 | arxiv | arXiv id_list | Innovation-Based Sampling for New Information |
| 2609.37899 | arxiv | arXiv id_list | Scaling Zero-Order Pretraining through Model Sharding |
| 2609.38515 | arxiv | arXiv id_list | A Frequency Domain Approach to Bounding Riccati Equation Perturbations |
| 2609.38845 | arxiv | arXiv id_list | Blind Interference Suppression in IRS-Aided Wireless Systems: A Statistical Channel Ratio Estima |
| 2609.39322 | arxiv | arXiv id_list | A Biophysically Detailed C. elegans Circuit as a Task-Agnostic Dynamical Core for Visually Robus |
| 2609.39479 | arxiv | arXiv id_list | Version Age-of-Information-based Semantic Secrecy Region Analysis |
| 2609.39667 | arxiv | arXiv id_list | Distribution of Age of Information in the Erlang Loss System |
| 2609.39754 | arxiv | arXiv id_list | ChunkTrust: Adapting Execution Horizons for Robot Policies with Action-Expert Evidence |
| 2609.39873 | arxiv | arXiv id_list | SplineWAM: Adaptive Action Horizons for World Action Models via B-Spline Representations |
| 2609.39983 | arxiv | arXiv id_list | Proximal Empirical Bayes for Sparse Regression with Posterior Decision Support |
| 2609.40338 | arxiv | arXiv id_list | Weak Convergence Rates for Partial-Sum Processes of Nonlinear Stochastic Approximation |
| 2610.00201 | arxiv | arXiv id_list | Simultaneous Perturbation as a Spectral Filter |
| 2610.00365 | arxiv | arXiv id_list | Manifold-Constrained Initial Noise Optimization for Efficient Generative Model Alignment |
| 2610.00390 | arxiv | arXiv id_list | Computational complexity of static output feedback stabilization |
| 2610.01258 | arxiv | arXiv id_list | ColoACT: Multi-Cue Action Chunking for Smooth Autonomous Colon Navigation on a Self-Propelled En |
| 2610.01626 | arxiv | arXiv id_list | Measuring the Stability Assumption Behind Action Chunking |
| 2610.01856 | arxiv | arXiv id_list | ChunkVLA-AM: Parallel Action Chunking for Vision-Language-Action Robot Control in Additive Manuf |
| 2610.02370 | arxiv | arXiv id_list | Network-in-the-Loop at Scale: GPU-Batched 5G Simulation for Massively Parallel Robot Learning |
| 2610.02609 | arxiv | arXiv id_list | Exact random centering and hybrid fluctuation limits for interacting reinforced processes under  |
| 2610.02633 | arxiv | arXiv id_list | High-Dimensional Regularization of the Spatial Sign Covariance Matrix for Robust Shape Estimatio |
| 2610.02989 | arxiv | arXiv id_list | System Level Synthesis for Fast Chance-Constrained Post-Fault Ascent Replanning under Persistent |
| 2610.03165 | arxiv | arXiv id_list | Sample complexity of variance-reduced policy gradient: weaker assumptions and lower bounds |
| 2610.03880 | arxiv | arXiv id_list | Reinforcement Learning on the Discrete Composition Channel of a Crystal Generator: Validated Gai |
| 2610.04568 | arxiv | arXiv id_list | Gradient-Free Sampling from Generative Models via Stochastic Bounded Extremum Seeking |
| 2610.04612 | arxiv | arXiv id_list | An End-to-End Framework for Modelling Pneumatic Soft Robots Based on Differentiable Finite Eleme |
| 2610.05019 | arxiv | arXiv id_list | Joint Target-Tag Estimation in Ambient Backscatter-Based ISAC |
| 2610.05058 | arxiv | arXiv id_list | A Statistical Inference Framework for PMI Estimation and SGNS Word Embeddings |
| 2610.05331 | arxiv | arXiv id_list | VAMPS: Visual and Motor Policies from Sampling-Based Planning |
| 2610.05595 | arxiv | arXiv id_list | Moment-Accurate Gaussian Mixtures for Constant-Step Stochastic Approximation |
| 2610.05856 | arxiv | arXiv id_list | On the Sequentially Semiseparable Structure of SDE-Induced Kernels and Efficient Algorithms for  |
| 2610.06554 | arxiv | arXiv id_list | Prediction Error Method for Identification of Subnetworks of Dynamical Systems |
| 2610.06565 | arxiv | arXiv id_list | Blind Beamforming for Intelligent Reflecting Surfaces: A Gradient Bandit Approach |
| 2610.07056 | arxiv | arXiv id_list | Behavioral Cloning Mystery |
| 2610.07221 | arxiv | arXiv id_list | Open-System Probe Selection and Optimal Measurements for Dispersive Coupling Metrology |
| 2610.07226 | arxiv | arXiv id_list | Minimal Witness Reinforcement Learning |
| 2610.07292 | arxiv | arXiv id_list | Assumption-lean logistic regression with missing covariates |
| 2610.07475 | arxiv | arXiv id_list | Adapting to Changes in Agent Behavior via Finite-Depth Policy Sensitivity |
| 2610.07949 | arxiv | arXiv id_list | Commit While Futures Agree: Consequence-Aware Adaptive Action Chunking for Robot Manipulation |
| 2610.08917 | arxiv | arXiv id_list | CARE: Certifying Acceleration for Vision-Language-Action Inference |
| 2610.09220 | arxiv | arXiv id_list | Regret-Optimal Linear-Quadratic Control under Distributional Drift |
| 2610.09276 | arxiv | arXiv id_list | CATune: Structural Constraint-Aware Bayesian Optimization for DBMS Configuration Tuning |
| 2610.09461 | arxiv | arXiv id_list | Deep learning driven framework for optimization of polycrystalline microstructures under competi |
| 2610.09632 | arxiv | arXiv id_list | Age of Information in Queueing Systems with Merging Server Streams |
| 2610.09886 | arxiv | arXiv id_list | Sparsifying Stochasticity, Not Capacity: Partial Stochasticity via Deep Weight Factorization of  |
| 2610.10022 | arxiv | arXiv id_list | Improved Berry-Esseen bounds for multivariate nonlinear statistics in convex distance |
| 2610.10246 | arxiv | arXiv id_list | Stationary Bias and Extrapolation in Nonlinear Two-Timescale Stochastic Approximation |
| 2610.10367 | arxiv | arXiv id_list | Temporally Interpretable Differentiable Decision Trees |
| 2610.10598 | arxiv | arXiv id_list | Performance Analysis and Sensing-Aware Resource Allocation for Full-Duplex Massive MIMO ISCC Net |
| 2610.10905 | arxiv | arXiv id_list | Informationally Decoupled Trajectory Design for Sim-to-Real System Identification |
| 2610.11396 | arxiv | arXiv id_list | DRL-Based AoI Minimization for RSMA in Finite-Blocklength MU-MISO |
| 2610.11555 | arxiv | arXiv id_list | Best of Both Worlds in Federated LSA: Speedup When Possible, Personalization Always |
| 2610.11906 | arxiv | arXiv id_list | RobustLDS: Learning linear dynamical systems under adversarial corruptions |
| 2610.11917 | arxiv | arXiv id_list | Multi-period Mean-Expectile Portfolio Optimization under Wasserstein Ambiguity: Reformulation, D |
| 2610.12420 | arxiv | arXiv id_list | A Unified Bellman Operator for Safety-Critical Reinforcement Learning |
| 2610.12873 | arxiv | arXiv id_list | An efficient stochastic generalized method of moments estimator for nonlinear moment models |
| 2610.12886 | arxiv | arXiv id_list | LeapBot-JAC: Joint Action Chains for World Action Models |
| 2610.12934 | arxiv | arXiv id_list | Self-Calibration DOA Estimation for Moving Dilated Arrays with Gain and Phase Errors |
| 2610.13142 | arxiv | arXiv id_list | Structure-Aware Online Optimization of the Age of Information with Unknown System Statistics |
| 2610.13751 | arxiv | arXiv id_list | Estimation, Sensitivity Analysis, and Optimization of Distortion Risk Measures via Simulation |
| 2610.13884 | arxiv | arXiv id_list | Interacting Stochastic Systems with Agent-Based Sampling and Connection-Based Reinforcement |
| 2610.13923 | arxiv | arXiv id_list | Goal-Oriented Bundle Management and Flow Control for Deep-Space Communications via Reinforcement |
| 2610.14225 | arxiv | arXiv id_list | Shaping the Menu: Information Design under Screening |
| 2610.14288 | arxiv | arXiv id_list | cvxoptdes: convex optimal experiment design in R |
| 2610.14333 | arxiv | arXiv id_list | Decentralized Bandit Learning of Markov Perfect Equilibria |
| 2610.14621 | arxiv | arXiv id_list | Shifted-Chart Composition for Horizon-Optimal Time-Varying LQR |
| 2610.14864 | arxiv | arXiv id_list | Predict in Chunks, Revise in Spans: History-conditioned Action Regeneration for Robotic Manipula |
| 2610.15047 | arxiv | arXiv id_list | Multilevel Monte Carlo for Zeroth-Order Stochastic Bilevel Optimization with Inexact Lower Level |
| 2610.15446 | arxiv | arXiv id_list | A Multi-View Low-Latency Direction-Sensing for Low-Altitude Network via a Multi-Armed Array |
| 2610.15585 | arxiv | arXiv id_list | StreamingWAM: Streaming World Action Modeling via Chunk-Wise Staircase Flow Matching |
| 2610.16448 | arxiv | arXiv id_list | Tikhonov-Stabilized Bezier Representation Forecasting for Training-free Diffusion Acceleration |
| 2610.17101 | arxiv | arXiv id_list | A Feasible Direction Method with Active-Set Identification for Derivative-Free Optimization |
| 2610.17321 | arxiv | arXiv id_list | GPU Goldmines: Tunable WebGPU Kernels for Edge LLM Inference |
| 2610.17333 | arxiv | arXiv id_list | Accounting for model error in ensemble variational data assimilation through learned generative  |
| 2610.17825 | arxiv | arXiv id_list | Minimal norm control problems for linear mean-field control systems |
| 2610.17830 | arxiv | arXiv id_list | Spatial Kernel Restricted Canonical Correlation Analysis: Population Targets, Identifiability, a |
| 2610.18216 | arxiv | arXiv id_list | TextualRL: Textual Reinforcement Learning for Context Management |
| 2610.18228 | arxiv | arXiv id_list | Generic Local Identifiability Does Not Imply Generic Global Identifiability in Linear Networks |
| 2610.18453 | arxiv | arXiv id_list | The forward-loop-erased ants walk |
| 2610.18552 | arxiv | arXiv id_list | Unbalanced W-Flow: Unbalanced Wasserstein Drifting under Finite-Batch Marginal Fluctuations |
| 2610.18563 | arxiv | arXiv id_list | Shadow Pricing in Transient Stability-Constrained Optimal Power Flow |
| 2610.18738 | arxiv | arXiv id_list | Enabling Token-wise Importance Sampling in Off-Policy RLVR with Proximal KL Regularization |
| 2610.18808 | arxiv | arXiv id_list | Optimizing Team Behavior via Extremum-seeking Control in Multi-agent Reinforcement Learning |
| 2610.18839 | arxiv | arXiv id_list | Fast Rates for Offline Q-Learning with KL Regularization |
| 2610.18874 | arxiv | arXiv id_list | ChunkAct: Action Chunking for Agentic Robotics |
| 2610.19229 | arxiv | arXiv id_list | Per-Bundle, Pre-Reconstruction Inversion for Temporal CT: Flux-Compensation Design and Multi-Pat |
| 2610.19656 | arxiv | arXiv id_list | Accelerating VLA Inference with Perturbation Informed Execution |
| 2610.19765 | arxiv | arXiv id_list | Refine Actions If Needed: Adaptive Action Chunk Refinement for Robot Manipulation |
| 2610.19826 | arxiv | arXiv id_list | Simultaneous Secure Communications and Sensing Privacy with Full Duplex MIMO Radios |
| 2610.20219 | arxiv | arXiv id_list | TRP-UE Bistatic Sensing for 6G Performance Analysis and Insights |
| 2610.20347 | arxiv | arXiv id_list | Non-asymptotic Convergence of Average-reward Q-learning with Options |
| cs/0408007 | arxiv | arXiv id_list | Online convex optimization in the bandit setting: gradient descent without a gradient |
