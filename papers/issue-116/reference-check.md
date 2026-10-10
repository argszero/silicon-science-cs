# Citation report - issue #116

Companion to `manuscript.md`. Two duties: (i) authenticity of every reference, and
(ii) coverage of the in-text citation keys. This report is a declaration; reviewers
verify independently. Every number below is read from the committed artefacts
(`refs/refs_keys.json`, `refs/refs_verify.log`) rather than typed.

## (i) Authenticity - how each entry was verified

**Method.** Every entry is verified by re-fetching it **by its own identifier** and
comparing the returned title against the title recorded for that key, after
normalisation (case, punctuation and whitespace folded).

```
python3 refs/refs_tool.py verify      # arXiv entries, by identifier
python3 refs/refs_tool.py doi         # the DOI entry, via Crossref
```

- **arXiv entries** are fetched from `https://export.arxiv.org/api/query?id_list=<id>`.
  When that API is throttled (HTTP 429) the tool falls back to the entry's **abstract
  page** (`https://arxiv.org/abs/<id>`) and reads its `citation_title` meta tag - a
  different service carrying the same record - marking those entries `+abs-page` in the
  log below.
- **DOI entries** are fetched from `https://api.crossref.org/works/<doi>`.
- The command exits non-zero if any entry fails, so this is a check rather than a
  statement. **entries=137 resolved=137 problems=0**, and **0 of 136** arXiv entries were resolved through
  the abstract-page fallback.

Run log: `refs/refs_verify.log` (sha256 `ea395a1877f6c058426c60e8f48d621f124a1f47034d6fee7449015520c3c032`).
Key map incl. verified titles: `refs/refs_keys.json` (sha256 `d0d4e0d2a96914536bf5882a506561fe676c151f9c9749b270f512d3b4e0a607`).

**Two-sided controls** (run against a throwaway copy of the keys file; the recorded
artefact was never mutated):

| control | expected | observed |
|---|---|---|
| one title replaced by a different paper's title | fail | exit 1, `TITLE MISMATCH`, both strings named |
| one invented identifier | fail | exit 1, `NOT RETURNED by the arXiv API` |
| a title corrupted on an entry verified via the abstract-page fallback | fail | exit 1, `TITLE MISMATCH` |
| restored | pass | exit 0, `resolved=137 problems=0` |

**Independent spot-checks outside the tool** (plain `curl`, not via `refs_tool.py`):

| key | identifier | fetched title | verdict |
|---|---|---|---|
| `2608.02547` | arXiv:2608.02547 | Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control | matches |
| `2606.00537` | arXiv:2606.00537 | PACE: Phase-Aware Chunk Execution for Robot Policies with Action Chunking | matches |
| `2403.09504` | arXiv:2403.09504 | Is Data All That Matters? The Role of Control Frequency for Learning-Based Sampled-Data Control of Uncertain Systems | matches |
| `2603.08493` | arXiv:2603.08493 | Pareto-Optimal Anytime Algorithms via Bayesian Racing | matches (abstract page) |
| `2602.21445` | arXiv:2602.21445 | VLA Knows Its Limits: Adaptive Execution Horizons for Robot Policies | matches (added revision round 1) |
| `2606.11408` | arXiv:2606.11408 | Dynamic Execution Horizon Prediction for Chunk-based Robot Policies | matches (added revision round 1) |
| `2609.39754` | arXiv:2609.39754 | ChunkTrust: Adapting Execution Horizons for Robot Policies with Action-Expert Evidence | matches (added revision round 1) |

The last three rows are the concurrent **adaptive-execution-horizon** family added in revision
round 1 (required change W2): each entry is inside this submission's declared scan window
(2025-11-01 → 2026-10-02) and is cited in §1 and §2, with its difference stated in the dedicated
related-work paragraph.

## (ii) Coverage

The manuscript cites by **identifier** (`[[<arxiv-id>]]` / `[[<doi>]]`) and the number is
assigned at build time by `refs/refs_build.py render`, so a number cannot drift from its
entry. Coverage is a **check**, not a promise:

```
python3 refs/refs_build.py check        # exit non-zero on any failure
```

`COVERAGE OK: all 137 entries cited, all in-text keys curated, and 137 >= 100` - every curated entry is cited in the body, every in-text key is curated,
the count is above the journal's floor of 100, and the citation guard finds no literal
`[N]` in the body (a number typed into the body is a claim whose referent can move; the
guard was validated by planting `[17]` in the text and requiring exit 1).

**Reference count: 137**, of which 1 DOI and 136 arXiv.
`manuscript.md` sha256 `837a7684728c36da44acccc28cc63e58f1db4a77f3675e7d74cb5b894a9118aa`.

## (iv) The author component of every entry

The entry style is a test over **every** entry, and the author component is part of it. It is
**read from the record**, never typed: the verifier captures it in the same fetch that resolves the
title, and stores it in `refs/refs_keys.json` under `verified_authors`.

| carrier | what it returns | the order it states |
|---|---|---|
| arXiv API (`export.arxiv.org/api/query?id_list=`) | one `<author><name>` per author | `Given Family` |
| arXiv abstract page (the throttled fallback) | one `<meta name="citation_author">` per author | `Family, Given` |
| Crossref (`api.crossref.org/works/<doi>`) | an `author` object carrying `family` and `given` | structured, no split needed |

The two arXiv carriers state the **same record in different orders**, so the comma decides which form
is in hand: a name carrying a comma is `Family, Given`; otherwise the last token is the family. The
printed form is `Family, I.` -- initials taken from the given names, a hyphenated given name taking one
initial per part (`Maria-Florina Balcan` -> `Balcan, M. F.`); **four or more** authors print the first
three then `; et al.`; a record giving **one token and no more** prints that token alone, never padded
to `Family, I.`. The **raw string the record returned is kept beside the printed one**, so the split is
an auditable derivation rather than a claim: last column of the table below.

Read by the journal's gate over the product:

```
python3 .github/tools/refgate.py papers/issue-116/manuscript.md
  entries=137  numbering=[n]
  block form: 137 entries, 0 of them not separated from the entry above by a blank line
  author form: 137/137 entry(s) carry the read's window (a family name, a comma, an initial ...
               0 print the family name ALL-CAPS, 0 carry a character reference (&...;)
  in-text cited numbers=137  covered=137/137  coverage=100.0%
  GATE: PASS
```

**137 of 137 entries name an author.** Where a record carried none the renderer would print
`author not established on the record read for this identifier [<identifier>]` rather than leaving the
position empty or guessing from the title; no entry here takes that branch.

## (iii) The entries

| key | identifier | status | verified title | year | authors (as the record gives them) |
|---|---|---|---|---|---|
|---|---|---|---|---|
| `10.15607/rss.2023.xix.016` | DOI:10.15607/rss.2023.xix.016 | crossref | 'Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware' | 2023 | Tony Zhao; Vikash Kumar; Sergey Levine (+1) |
| `1007.0683` | arXiv:1007.0683 | recorded | 'Scheduling Periodic Real-Time Tasks with Heterogeneous Reward Requirements' | 2010-06-21 | I-Hong Hou; P. R. Kumar |
| `1010.2265` | arXiv:1010.2265 | recorded | "The Lambert Way to Gaussianize heavy tailed data with the inverse of Tukey's h as a special case" | 2010-10-11 | Georg M. Goerg |
| `1208.3830` | arXiv:1208.3830 | recorded | 'On the Stability of Receding Horizon Control for Continuous-Time Stochastic Systems' | 2012-08-19 | Fajin Wei; Andrea Lecchini-Visintini |
| `1301.7381` | arXiv:1301.7381 | recorded | 'Hierarchical Solution of Markov Decision Processes using Macro-actions' | 2013-01-30 | Milos Hauskrecht; Nicolas Meuleau; Leslie Pack Kaelbling (+2) |
| `1301.7384` | arXiv:1301.7384 | recorded | 'An Anytime Algorithm for Decision Making under Uncertainty' | 2013-01-30 | Michael C. Horsch; David L. Poole |
| `1306.0448` | arXiv:1306.0448 | recorded | 'Adaptive Fixed Priority End-To-End Imprecise Scheduling In Distributed Real Time Systems' | 2013-06-03 | W. El-Haweet; Islam Elgedawy; Ibrahim Abd El-Salam |
| `1311.0388` | arXiv:1311.0388 | recorded | 'Non-linear Task-Space Disturbance Observer for Position Regulation of Redundant Robot Arms against Perturbations in 3D Environments' | 2013-11-02 | Tapomayukh Bhattacharjee; Yonghwan Oh; Sang-Rok Oh |
| `1402.4568` | arXiv:1402.4568 | recorded | 'Linear Receding Horizon Control with Probabilistic System Parameters' | 2014-02-19 | Raktim Bhattacharya; James Fisher |
| `1410.5083` | arXiv:1410.5083 | recorded | 'Stability for Receding-horizon Stochastic Model Predictive Control' | 2014-10-19 | Joel A. Paulson; Stefan Streif; Ali Mesbah |
| `1506.08637` | arXiv:1506.08637 | recorded | 'On The Age Of Information In Status Update Systems With Packet Management' | 2015-06-29 | Maice Costa; Marian Codreanu; Anthony Ephremides |
| `1507.02100` | arXiv:1507.02100 | recorded | 'Iterative methods for the delay Lyapunov equation with T-Sylvester preconditioning' | 2015-07-08 | Elias Jarlebring; Federico Poloni |
| `1511.03488` | arXiv:1511.03488 | recorded | 'Constraint-Tightening and Stability in Stochastic Model Predictive Control' | 2015-11-11 | Matthias Lorenzen; Fabrizio Dabbene; Roberto Tempo (+1) |
| `1512.04797` | arXiv:1512.04797 | recorded | 'Pontryagin maximum principle for optimal sampled-data control problems' | 2015-12-15 | Loïc Bourdin; Emmanuel Trélat |
| `1604.06350` | arXiv:1604.06350 | recorded | 'Linear-quadratic optimal sampled-data control problems: convergence result and Riccati theory' | 2016-04-21 | Loïc Bourdin; Emmanuel Trélat |
| `1608.03729` | arXiv:1608.03729 | recorded | 'Boundary control of cascaded ODE-Heat equations under actuator saturation' | 2016-08-12 | Wen Kang; Emilia Fridman |
| `1610.05735` | arXiv:1610.05735 | recorded | 'Deep Amortized Inference for Probabilistic Programs' | 2016-10-18 | Daniel Ritchie; Paul Horsfall; Noah D. Goodman |
| `1612.01554` | arXiv:1612.01554 | recorded | 'Robustness of Control Barrier Functions for Safety Critical Control' | 2016-12-05 | Xiangru Xu; Paulo Tabuada; Jessy W. Grizzle (+1) |
| `1701.06927` | arXiv:1701.06927 | recorded | 'Age and Value of Information: Non-linear Age Case' | 2017-01-24 | Antzela Kosta; Nikolaos Pappas; Anthony Ephremides (+1) |
| `1709.10087` | arXiv:1709.10087 | recorded | 'Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations' | 2017-09-28 | Aravind Rajeswaran; Vikash Kumar; Abhishek Gupta (+4) |
| `1803.09487` | arXiv:1803.09487 | recorded | 'Lower bounds on the maximum delay margin by analytic interpolation' | 2018-03-26 | Axel Ringh; Johan Karlsson; Anders Lindquist |
| `1805.08913` | arXiv:1805.08913 | recorded | 'Amortized Inference Regularization' | 2018-05-23 | Rui Shu; Hung H. Bui; Shengjia Zhao (+2) |
| `1807.04700` | arXiv:1807.04700 | recorded | 'Technical Report: Infinite Horizon Discrete-Time Linear Quadratic Gaussian Tracking Control Derivation' | 2018-07-12 | Kasra Yazdani; Matthew Hale |
| `1807.10715` | arXiv:1807.10715 | recorded | 'Residual-based iterations for the generalized Lyapunov equation' | 2018-07-27 | Tobias Breiten; Emil Ringh |
| `1810.10983` | arXiv:1810.10983 | recorded | 'Stochastic Control with Stale Information--Part I: Fully Observable Systems' | 2018-10-25 | Touraj Soleymani; John S. Baras; Karl H. Johansson |
| `1811.07534` | arXiv:1811.07534 | recorded | 'Note on the exact delay stability margin computation of hybrid dynamical systems' | 2018-11-19 | V. Bellet; C. Poussot-Vassal; C. Pagetti (+1) |
| `1811.08067` | arXiv:1811.08067 | recorded | 'Reinforcement Learning of Active Vision for Manipulating Objects under Occlusions' | 2018-11-20 | Ricson Cheng; Arpit Agarwal; Katerina Fragkiadaki |
| `1902.06235` | arXiv:1902.06235 | recorded | 'Optimal Stabilization Control for Discrete-time Markov Jump Linear System with Control Input Delay' | 2019-02-17 | Chunyan Han; Hongdan Li; Huanshui Zhang |
| `1902.09032` | arXiv:1902.09032 | recorded | 'Disturbance Observer-based Robust Control and Its Applications: 35th Anniversary Overview' | 2019-02-24 | Emre Sariyildiz; Roberto Oboe; Kouhei Ohnishi |
| `1903.06368` | arXiv:1903.06368 | recorded | 'Robust Decidability of Sampled-Data Control of Nonlinear Systems with Temporal Logic Specifications' | 2019-03-15 | Jun Liu |
| `1904.12660` | arXiv:1904.12660 | recorded | 'Tracking Performance Limitations of MIMO Networked Control Systems with Multiple Communication Constraints' | 2019-04-25 | Chao-Yang Chen; Weihua Gui; Lianghong Wu (+2) |
| `1905.04391` | arXiv:1905.04391 | recorded | 'Energy-Aware Scheduling of Task Graphs with Imprecise Computations and End-to-End Deadlines' | 2019-05-10 | Amirhossein Esmaili; Mahdi Nazemi; Massoud Pedram |
| `1906.01434` | arXiv:1906.01434 | recorded | 'Sampled-Data Control of the Stefan System' | 2019-05-31 | Shumon Koga; Iasson Karafyllis; Miroslav Krstic |
| `1912.06331` | arXiv:1912.06331 | recorded | 'A Guide to Design Disturbance Observer' | 2019-12-13 | Emre Sariyildiz; Kouhei Ohnishi |
| `1912.08734` | arXiv:1912.08734 | recorded | 'An analytic interpolation approach to stability margins with emphasis on time delay' | 2019-12-18 | Axel Ringh; Johan Karlsson; Anders Lindquist |
| `2002.06836` | arXiv:2002.06836 | recorded | 'Control Frequency Adaptation via Action Persistence in Batch Reinforcement Learning' | 2020-02-17 | Alberto Maria Metelli; Flavio Mazzolini; Lorenzo Bisi (+2) |
| `2003.02327` | arXiv:2003.02327 | recorded | 'Learning View and Target Invariant Visual Servoing for Navigation' | 2020-03-04 | Yimeng Li; Jana Kosecka |
| `2003.05999` | arXiv:2003.05999 | recorded | 'Adaptive Control and Regret Minimization in Linear Quadratic Gaussian (LQG) Setting' | 2020-03-12 | Sahin Lale; Kamyar Azizzadenesheli; Babak Hassibi (+1) |
| `2004.08332` | arXiv:2004.08332 | recorded | 'On the Stability Margin and Input Delay Margin of Linear Multi-agent systems' | 2020-04-17 | Rajnish Bhusal; Kamesh Subbarao |
| `2004.08646` | arXiv:2004.08646 | recorded | 'Macro-Action-Based Deep Multi-Agent Reinforcement Learning' | 2020-04-18 | Yuchen Xiao; Joshua Hoffman; Christopher Amato |
| `2004.08932` | arXiv:2004.08932 | recorded | 'Discounted Cost Linear Quadratic Gaussian Control for Descriptor Systems' | 2020-04-19 | Hermann Mena; Lena-Maria Pfurtscheller; Matthias Voigt |
| `2010.04296` | arXiv:2010.04296 | recorded | 'CausalWorld: A Robotic Manipulation Benchmark for Causal Structure and Transfer Learning' | 2020-10-08 | Ossama Ahmed; Frederik Träuble; Anirudh Goyal (+5) |
| `2011.00778` | arXiv:2011.00778 | recorded | 'Learning Sequences of Manipulation Primitives for Robotic Assembly' | 2020-11-02 | Nghia Vuong; Hung Pham; Quang-Cuong Pham |
| `2011.01112` | arXiv:2011.01112 | recorded | 'Scheduling Real-time Deep Learning Services as Imprecise Computations' | 2020-11-02 | Shuochao Yao; Yifan Hao; Yiran Zhao (+6) |
| `2011.03813` | arXiv:2011.03813 | recorded | 'MAGIC: Learning Macro-Actions for Online POMDP Planning' | 2020-11-07 | Yiyuan Lee; Panpan Cai; David Hsu |
| `2012.14942` | arXiv:2012.14942 | recorded | 'LISPR: An Options Framework for Policy Reuse with Reinforcement Learning' | 2020-12-29 | Daniel Graves; Jun Jin; Jun Luo |
| `2101.00649` | arXiv:2101.00649 | recorded | 'A scheduling algorithm for networked control systems' | 2021-01-03 | Atreyee Kundu |
| `2101.02859` | arXiv:2101.02859 | recorded | 'Disturbance Observer' | 2021-01-08 | Hyungbo Shim |
| `2102.11122` | arXiv:2102.11122 | recorded | 'Reinforcement Learning of the Prediction Horizon in Model Predictive Control' | 2021-02-22 | Eivind Bøhn; Sebastien Gros; Signe Moe (+1) |
| `2102.12571` | arXiv:2102.12571 | recorded | 'The Logical Options Framework' | 2021-02-24 | Brandon Araki; Xiao Li; Kiran Vodrahalli (+3) |
| `2104.10383` | arXiv:2104.10383 | recorded | 'Stochastic Model Predictive Control for Linear Systems with Unbounded Additive Uncertainties' | 2021-04-21 | Fei Li; Huiping Li; Yuyao He |
| `2107.08149` | arXiv:2107.08149 | recorded | 'Dual Quaternion-Based Visual Servoing for Grasping Moving Objects' | 2021-07-17 | Cristiana de Farias; Maxime Adjigble; Brahim Tamadazte (+2) |
| `2108.08014` | arXiv:2108.08014 | recorded | 'Model Predictive Control with Models of Different Granularity and a Non-uniformly Spaced Prediction Horizon' | 2021-08-18 | Tim Brüdigam; Daniel Prader; Dirk Wollherr (+1) |
| `2110.13356` | arXiv:2110.13356 | recorded | 'Event-triggered Consensus of Matrix-weighted Networks Subject to Actuator Saturation' | 2021-10-26 | Lulu Pan; Haibin Shao; Yuanlong Li (+2) |
| `2112.14507` | arXiv:2112.14507 | recorded | 'Optimal Sampled-Data Control of a Nonlinear System' | 2021-12-29 | Yasuaki Oishi; Noboru Sakamoto |
| `2203.08098` | arXiv:2203.08098 | recorded | 'RB2: Robotic Manipulation Benchmarking with a Twist' | 2022-03-15 | Sudeep Dasari; Jianren Wang; Joyce Hong (+12) |
| `2203.13251` | arXiv:2203.13251 | recorded | 'Dexterous Imitation Made Easy: A Learning-Based Framework for Efficient Dexterous Manipulation' | 2022-03-24 | Sridhar Pandian Arunachalam; Sneha Silwal; Ben Evans (+1) |
| `2204.05681` | arXiv:2204.05681 | recorded | 'Learning Stable Dynamical Systems for Visual Servoing' | 2022-04-12 | Antonio Paolillo; Matteo Saveriano |
| `2204.06207` | arXiv:2204.06207 | recorded | 'Safe Stochastic Model Predictive Control' | 2022-04-13 | Tim Brüdigam; Robert Jacumet; Dirk Wollherr (+1) |
| `2205.11640` | arXiv:2205.11640 | recorded | 'Generalization Gap in Amortized Inference' | 2022-05-23 | Mingtian Zhang; Peter Hayes; David Barber |
| `2205.14292` | arXiv:2205.14292 | recorded | 'BulletArm: An Open-Source Robotic Manipulation Benchmark and Learning Framework' | 2022-05-28 | Dian Wang; Colin Kohler; Xupeng Zhu (+2) |
| `2206.04477` | arXiv:2206.04477 | recorded | 'Receding Horizon Inverse Reinforcement Learning' | 2022-06-09 | Yiqing Xu; Wei Gao; David Hsu |
| `2209.08728` | arXiv:2209.08728 | recorded | 'Control Barrier Functions for Stochastic Systems and Safety-critical Control Designs' | 2022-09-19 | Yuki Nishimura; Kenta Hoshino |
| `2210.10549` | arXiv:2210.10549 | recorded | 'Visual Servoing with Geometrically Interpretable Neural Perception' | 2022-10-19 | Antonio Paolillo; Mirko Nava; Dario Piga (+1) |
| `2211.00867` | arXiv:2211.00867 | recorded | 'Heavy-Tailed NGG Mixture Models' | 2022-11-02 | Vianey Palacios Ramirez; Miguel de Carvalho; Luis Gutierrez Inostroza |
| `2303.08428` | arXiv:2303.08428 | recorded | 'Criteria for stabilizing a multi-delay stochastic system with multiplicative control-dependent noises' | 2023-03-15 | Cheng Tan; Zhengqiang Zhang; Haoting Sui (+1) |
| `2305.19262` | arXiv:2305.19262 | recorded | 'Stochastic Model Predictive Control with Dynamic Chance Constraints' | 2023-05-30 | Maico Hendrikus Wilhelmus Engelaar; Sofie Haesaert; Mircea Lazar |
| `2308.14265` | arXiv:2308.14265 | recorded | 'A Risk-Aware Control: Integrating Worst-Case CVaR with Control Barrier Function' | 2023-08-28 | Masako Kishida |
| `2311.09062` | arXiv:2311.09062 | recorded | 'Brain Functional Connectivity under Teleoperation Latency: a fNIRS Study' | 2023-11-15 | Yang Ye; Tianyu Zhou; Qi Zhu (+2) |
| `2312.11374` | arXiv:2312.11374 | recorded | 'Mastering Stacking of Diverse Shapes with Large-Scale Iterative Reinforcement Learning on Real Robots' | 2023-12-18 | Thomas Lampe; Abbas Abdolmaleki; Sarah Bechtle (+12) |
| `2403.00336` | arXiv:2403.00336 | recorded | 'Never-Ending Behavior-Cloning Agent for Robotic Manipulation' | 2024-03-01 | Wenqi Liang; Gan Sun; Yao He (+3) |
| `2403.08807` | arXiv:2403.08807 | recorded | 'Effective anytime algorithm for multiobjective combinatorial optimization problems' | 2024-02-06 | Miguel Ángel Domínguez-Ríos; Francisco Chicano; Enrique Alba |
| `2403.09504` | arXiv:2403.09504 | recorded | 'Is Data All That Matters? The Role of Control Frequency for Learning-Based Sampled-Data Control of Uncertain Systems' | 2024-03-14 | Ralf Römer; Lukas Brunke; Siqi Zhou (+1) |
| `2404.12484` | arXiv:2404.12484 | recorded | 'Neural Methods for Amortized Inference' | 2024-04-18 | Andrew Zammit-Mangion; Matthew Sainsbury-Dale; Raphaël Huser |
| `2404.16391` | arXiv:2404.16391 | recorded | 'Stability-Oriented Prediction Horizons Design of Generalized Predictive Control for DC/DC Boost Converter' | 2024-04-25 | Yuan Li; Subham Sahoo; Sergio Vazquez (+3) |
| `2405.14636` | arXiv:2405.14636 | recorded | 'PerLLM: Personalized Inference Scheduling with Edge-Cloud Collaboration for Diverse LLM Services' | 2024-05-23 | Zheming Yang; Yuanhao Yang; Chang Zhao (+3) |
| `2406.06005` | arXiv:2406.06005 | recorded | 'WoCoCo: Learning Whole-Body Humanoid Control with Sequential Contacts' | 2024-06-10 | Chong Zhang; Wenli Xiao; Tairan He (+1) |
| `2406.07324` | arXiv:2406.07324 | recorded | 'Lyapunov equations: a (fixed) point of view' | 2024-06-11 | Richard Pates |
| `2408.00342` | arXiv:2408.00342 | recorded | 'MuJoCo MPC for Humanoid Control: Evaluation on HumanoidBench' | 2024-08-01 | Moritz Meser; Aditya Bhatt; Boris Belousov (+1) |
| `2408.17355` | arXiv:2408.17355 | recorded | 'Bidirectional Decoding: Improving Action Chunking via Guided Test-Time Sampling' | 2024-08-30 | Yuejiang Liu; Jubayer Ibn Hamid; Annie Xie (+3) |
| `2409.05113` | arXiv:2409.05113 | recorded | 'Nonlinear Cooperative Output Regulation with Input Delay Compensation' | 2024-09-08 | Shiqi Zheng; Choon Ki Ahn; Xiaowei Jiang (+2) |
| `2410.16981` | arXiv:2410.16981 | recorded | 'Proleptic Temporal Ensemble for Improving the Speed of Robot Tasks Generated by Imitation Learning' | 2024-10-22 | Hyeonjun Park; Daegyu Lim; Seungyeon Kim (+1) |
| `2504.03515` | arXiv:2504.03515 | recorded | 'Dexterous Manipulation through Imitation Learning: A Survey' | 2025-04-04 | Shan An; Ziyu Meng; Chao Tang (+9) |
| `2504.08005` | arXiv:2504.08005 | recorded | 'Extremum Seeking Control for Multivariable Maps under Actuator Saturation' | 2025-04-09 | Enzo Ferreira Tomaz Silva; Pedro Henrique Silva Coutinho; Tiago Roux Oliveira (+1) |
| `2506.01392` | arXiv:2506.01392 | recorded | 'Sparse Imagination for Efficient Visual World Model Planning' | 2025-06-02 | Junha Chun; Youngjoon Jeong; Taesup Kim |
| `2506.13690` | arXiv:2506.13690 | recorded | 'Meta-learning how to Share Credit among Macro-Actions' | 2025-06-16 | Ionel-Alexandru Hosu; Traian Rebedea; Razvan Pascanu |
| `2507.07969` | arXiv:2507.07969 | recorded | 'Reinforcement Learning with Action Chunking' | 2025-07-10 | Qiyang Li; Zhiyuan Zhou; Sergey Levine |
| `2507.10251` | arXiv:2507.10251 | recorded | 'ToMacVF : Temporal Macro-action Value Factorization for Asynchronous Multi-Agent Reinforcement Learning' | 2025-07-14 | Wenjing Zhang; Wei Zhang |
| `2510.06153` | arXiv:2510.06153 | recorded | 'Robust Data-Driven Receding Horizon Control' | 2025-10-07 | Jian Zheng; Sahand Kiani; Mario Sznaier (+1) |
| `2511.04421` | arXiv:2511.04421 | recorded | 'Temporal Action Selection for Action Chunking' | 2025-11-06 | Yueyang Weng; Xiaopeng Zhang; Yongjin Mu (+2) |
| `2511.09290` | arXiv:2511.09290 | recorded | 'Prediction horizon shapes representations in predictive learning' | 2025-11-12 | Aviv Ratzon; Omri Barak |
| `2511.14358` | arXiv:2511.14358 | recorded | 'Identifying Time-varying Costs in Finite-horizon Linear Quadratic Gaussian Games' | 2025-11-18 | Kai Ren; Maryam Kamgarpour |
| `2512.05964` | arXiv:2512.05964 | recorded | 'Training-Time Action Conditioning for Efficient Real-Time Chunking' | 2025-12-05 | Kevin Black; Allen Z. Ren; Michael Equi (+1) |
| `2512.18725` | arXiv:2512.18725 | recorded | 'ML Inference Scheduling with Predictable Latency' | 2025-12-21 | Haidong Zhao; Nikolaos Georgantas |
| `2602.07425` | arXiv:2602.07425 | recorded | 'Sign-Based Optimizers Are Effective Under Heavy-Tailed Noise' | 2026-02-07 | Dingzhi Yu; Hongyi Tao; Yuanyu Wan (+2) |
| `2602.18002` | arXiv:2602.18002 | recorded | 'Asynchronous Heavy-Tailed Optimization' | 2026-02-20 | Junfei Sun; Dixi Yao; Xuchen Gong (+3) |
| `2602.18247` | arXiv:2602.18247 | recorded | 'Hybrid Control of ADT Switched Linear Systems subject to Actuator Saturation' | 2026-02-20 | Fen Wu; Chengzhi Yuan |
| `2602.21445` | arXiv:2602.21445 | resolved-from-api | 'VLA Knows Its Limits: Adaptive Execution Horizons for Robot Policies' | 2026-02-24 | Haoxuan Wang; Gengyu Zhang; Yan Yan (+2) |
| `2603.01891` | arXiv:2603.01891 | recorded | 'SEAR: Sample Efficient Action Chunking Reinforcement Learning' | 2026-03-02 | C. F. Maximilian Nagy; Onur Celik; Emiliyan Gospodinov (+4) |
| `2603.06403` | arXiv:2603.06403 | recorded | 'Adapter-Augmented Bandits for Online Multi-Constrained Multi-Modal Inference Scheduling' | 2026-03-06 | Xianzhi Zhang; Yue Xu; Yinlin Zhu (+4) |
| `2603.08493` | arXiv:2603.08493 | recorded | 'Pareto-Optimal Anytime Algorithms via Bayesian Racing' | 2026-03-09 | Jonathan Wurth; Helena Stegherr; Neele Kemper (+2) |
| `2603.18091` | arXiv:2603.18091 | recorded | 'Action Draft and Verify: A Self-Verifying Framework for Vision-Language-Action Model' | 2026-03-18 | Chen Zhao; Zhuoran Wang; Haoyang Li (+6) |
| `2603.25981` | arXiv:2603.25981 | recorded | 'Policy-Guided World Model Planning for Language-Conditioned Visual Navigation' | 2026-03-26 | Amirhosein Chahe; Lifeng Zhou |
| `2604.02965` | arXiv:2604.02965 | recorded | 'Open-Loop Planning, Closed-Loop Verification: Speculative Verification for VLA' | 2026-04-03 | Zihua Wang; Zhitao Lin; Ruibo Li (+4) |
| `2604.06067` | arXiv:2604.06067 | recorded | 'HiPolicy: Hierarchical Multi-Frequency Action Chunking for Policy Learning' | 2026-04-07 | Jiyao Zhang; Zimu Han; Junhan Wang (+7) |
| `2604.25050` | arXiv:2604.25050 | recorded | 'DiscreteRTC: Discrete Diffusion Policies are Natural Asynchronous Executors' | 2026-04-27 | Pengcheng Wang; Kaiwen Hong; Chensheng Peng (+4) |
| `2605.00884` | arXiv:2605.00884 | recorded | 'LiteVLA-H: Dual-Rate Vision-Language-Action Inference for Onboard Aerial Guidance and Semantic Perception' | 2026-04-27 | Justin williams; Kishor Datta Gupta; Roy George (+1) |
| `2605.15926` | arXiv:2605.15926 | recorded | 'Delay periodic Lyapunov equation' | 2026-05-15 | Irina V. Aleksandrova; Juan J. L. Velázquez |
| `2605.15944` | arXiv:2605.15944 | recorded | 'FocalPolicy: Frequency-Optimized Chunking and Locally Anchored Flow Matching for Coherent Visuomotor Policy' | 2026-05-15 | Qian He; Zhenshuo Yang; Wenqi Liang (+3) |
| `2605.19592` | arXiv:2605.19592 | recorded | 'Implicit Action Chunking for Smooth Continuous Control' | 2026-05-19 | Bosun Liang; Shuo Pei; Zirui Chen (+5) |
| `2605.25537` | arXiv:2605.25537 | recorded | 'Action-Prior Denoising for Smooth Real-Time Chunking' | 2026-05-25 | Dongyang Liu; Zhaowen Zheng; Yu Sun (+3) |
| `2606.00537` | arXiv:2606.00537 | resolved-from-api | 'PACE: Phase-Aware Chunk Execution for Robot Policies with Action Chunking' | 2026-05-30 | Junnan Nie; Jiayi Li; Chenghao Liu (+5) |
| `2606.11408` | arXiv:2606.11408 | resolved-from-api | 'Dynamic Execution Horizon Prediction for Chunk-based Robot Policies' | 2026-06-09 | Yuchi Zhao; Miroslav Bogdanovic; Arjun Sohal (+5) |
| `2606.17040` | arXiv:2606.17040 | recorded | 'R2RDreamer: 3D-aware Data Augmentation for Spatially-generalized 2D Manipulation Policies' | 2026-06-15 | Xiuwei Xu; Haowen Sun; Angyuan Ma (+7) |
| `2606.22540` | arXiv:2606.22540 | recorded | 'PolicyTrim: Boosting Intrinsic Policy Efficiency of Vision-Language-Action Models' | 2026-06-21 | Xianghui Wang; Feng Chen; Wenbo Zhang (+4) |
| `2607.02646` | arXiv:2607.02646 | recorded | 'EVA-Client: A Unified Data Collection, Inference, and Deployment Framework for Embodied Policies on Real Robots' | 2026-07-02 | Heqing Yang; Yang Yi; Liyao Wang (+8) |
| `2607.12287` | arXiv:2607.12287 | recorded | 'Reducing Temporal Redundancy for Efficient Vision-Language-Action Inference' | 2026-07-14 | Yuzhou Wu; Yuxin Zheng; Muchun Niu (+6) |
| `2607.12992` | arXiv:2607.12992 | recorded | 'ChunkFlow: Towards Continuity-Consistent Chunked Policy Learning' | 2026-07-14 | Zhao Yang; Yinan Shi; Mingyuan Yao (+3) |
| `2608.00793` | arXiv:2608.00793 | recorded | 'DynamicWAM: Dual-Path Motion Conditioning for World-Action Models in Dynamic Manipulation' | 2026-08-01 | Yunfan Lou; Hewen Gao; Xiyu Zhu (+6) |
| `2608.02547` | arXiv:2608.02547 | recorded | 'Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control?' | 2026-08-03 | Filippo Lazzati; Kyle Stachowicz; William Chen (+3) |
| `2608.08644` | arXiv:2608.08644 | recorded | 'Path-dependent Discrete Amortized Inference' | 2026-08-09 | Tiago da Silva; Esmeralda S. Whitammer; Salem Lahlou |
| `2608.12932` | arXiv:2608.12932 | recorded | 'FlashDrive: Flash Vision-Language-Action Inference for Autonomous Driving' | 2026-08-13 | Zekai Li; Yihao Liang; Hongfei Zhang (+3) |
| `2608.15938` | arXiv:2608.15938 | recorded | 'Revisiting Open-Loop Execution in Robotics: Toward Reactive, Higher-Performing Policies' | 2026-08-16 | Michael Zeng; Abhinav Agarwal; Ajay Bati (+3) |
| `2609.03715` | arXiv:2609.03715 | recorded | 'MINERVA: How Small Can a Manipulation Policy Be and Still Solve LIBERO?' | 2026-09-03 | Kohei Sendai; Tatsuya Matsushima; Yusuke Iwasawa |
| `2609.17210` | arXiv:2609.17210 | recorded | 'FluxVLA Engine: A One-Stop VLA Engineering Platform for Embodied Intelligence' | 2026-09-15 | Yinhao Li; Weixin Mao; Zihan Lan (+21) |
| `2609.18732` | arXiv:2609.18732 | recorded | 'PASSAGE: Scaling Scene-Aligned Motion Learning for Perceptive Humanoid Traversal in Cluttered Environments' | 2026-09-16 | Yuxuan Ma; Zicheng Zeng; Chunlin Peng (+17) |
| `2609.19200` | arXiv:2609.19200 | recorded | 'ULOHA: An Underwater Bimanual Robot System for Robot Learning' | 2026-09-16 | Masato Kobayashi; Takeru Tsunoori |
| `2609.22276` | arXiv:2609.22276 | recorded | 'D3DWA: Adaptive Weight and Prediction-Horizon for Dynamic Window Approach via Dueling Double Deep Q-Network' | 2026-09-11 | Zahra Jooyandeh; Masato Kobayashi; Yuki Uranishi |
| `2609.27167` | arXiv:2609.27167 | recorded | 'Median Temporal Ensembling: Training-Free Robust Aggregation for Action-Chunked Visuomotor Policies' | 2026-09-22 | Yuhang Jiang |
| `2609.34319` | arXiv:2609.34319 | recorded | 'Text-Vision Synergistic Token Caching: A Training-Free Framework for Efficient Vision-Language-Action Inference' | 2026-09-28 | Qianer Li; Chengjie Zhang; Jingwen Chen (+3) |
| `2609.36250` | arXiv:2609.36250 | recorded | 'Action Chunking Proximal Policy Optimization with Feedback Correction' | 2026-09-28 | Sanghyun Hahn; Jonghyun Choi |
| `2609.36471` | arXiv:2609.36471 | resolved-from-api | 'Staircase Policy: Streaming Inference for World-Action Models with Large Action Chunks' | 2026-09-29 | Guoheng Sun; Chen Chen; Jin Wang (+2) |
| `2609.36540` | arXiv:2609.36540 | resolved-from-api | 'Reactive Real-Time Flow Policies via Asynchronous Distribution Alignment' | 2026-09-29 | Moritz Zoellner; Reece O'Mahoney; Ioannis Havoutis (+1) |
| `2609.36967` | arXiv:2609.36967 | recorded | 'Beyond Token Importance: Preserving Spatial Scaffolds for Efficient Vision-Language-Action Inference' | 2026-09-29 | Jiayu Chen; Shuyong Gao; Jingkai Jia (+6) |
| `2609.37772` | arXiv:2609.37772 | resolved-from-api | 'Urgent Actions Go First: Urgency-Aware Denoising for Real-Time VLA Control' | 2026-09-29 | Zibo Wang; Haochen Han; Pengzhen Ren (+2) |
| `2609.39754` | arXiv:2609.39754 | resolved-from-api | 'ChunkTrust: Adapting Execution Horizons for Robot Policies with Action-Expert Evidence' | 2026-09-30 | Fanding Huang; Jingyan Jiang; Shifeng Bao (+13) |
| `2609.39873` | arXiv:2609.39873 | recorded | 'SplineWAM: Adaptive Action Horizons for World Action Models via B-Spline Representations' | 2026-09-30 | Jun Guo; Xiaoshen Han; Qiwei Li (+7) |
