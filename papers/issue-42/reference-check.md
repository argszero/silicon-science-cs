# Citation authenticity report — issue #42

Every reference below was resolved against an external registry before submission. Protocol:

- **DOI present** -> Crossref, `https://api.crossref.org/works/<doi>`.
- **arXiv-only (no publisher DOI)** -> DataCite, `https://api.datacite.org/dois/10.48550/arXiv.<id>`.
- **Gate = TITLE MATCH, not reachability.** A response must be HTTP 200 *and* the record's title must
  match the title the manuscript claims. That gate fired: three candidates recalled from memory
  returned 200 while resolving to an unrelated paper — `2001.08049` is "On Last-Layer Algorithms
  for Classification", not Mozannar & Sontag's learning-to-defer paper; `2206.04805` is a BirdCLEF
  paper; `1904.01685` is "Measuring Calibration in Deep Learning". All three were replaced by
  the true identifiers (`2006.01862`, dropped, `1901.09192`) before entering the list.

The same gate also caught recalled DOIs for Avizienis, Randell, Littlewood and Dietvorst each resolving
to an entirely different paper. A reachability-only check would have shipped **seven** fabricated
citations.

Result: **117 entries, 117 verified, 0 unreachable, 0 title-mismatched.**

| # | key | method | result | real record found (title — DOI) |
|---|---|---|---|---|
| 1 | `chow1970reject` | Crossref | **verified** | On optimum recognition error and reject tradeoff — `10.1109/tit.1970.1054406` |
| 2 | `fawcett2006roc` | Crossref | **verified** | An introduction to ROC analysis — `10.1016/j.patrec.2005.10.010` |
| 3 | `selectivegeifman2017` | DataCite (arXiv DOI) | **verified** | Selective Classification for Deep Neural Networks — `10.48550/arXiv.1705.08500` |
| 4 | `selectivenet2019` | DataCite (arXiv DOI) | **verified** | SelectiveNet: A Deep Neural Network with an Integrated Reject Option — `10.48550/arXiv.1901.09192` |
| 5 | `jiang2018trust` | DataCite (arXiv DOI) | **verified** | To Trust Or Not To Trust A Classifier — `10.48550/arXiv.1805.11783` |
| 6 | `mozannar2020defer` | DataCite (arXiv DOI) | **verified** | Consistent Estimators for Learning to Defer to an Expert — `10.48550/arXiv.2006.01862` |
| 7 | `unbiaseddeferral2021` | DataCite (arXiv DOI) | **verified** | Towards Unbiased and Accurate Deferral to Multiple Experts — `10.48550/arXiv.2102.13004` |
| 8 | `triage2021` | DataCite (arXiv DOI) | **verified** | Differentiable Learning Under Triage — `10.48550/arXiv.2103.08902` |
| 9 | `uncertaintydefer2021` | DataCite (arXiv DOI) | **verified** | Incorporating Uncertainty in Learning to Defer Algorithms for Safe Computer-Aided Diagno — `10.48550/arXiv.2108.07392` |
| 10 | `seqdefer2021` | DataCite (arXiv DOI) | **verified** | Learning-to-defer for sequential medical decision-making under uncertainty — `10.48550/arXiv.2109.06312` |
| 11 | `exemplars2021` | DataCite (arXiv DOI) | **verified** | Teaching Humans When To Defer to a Classifier via Exemplars — `10.48550/arXiv.2111.11297` |
| 12 | `calibrateddefer2022` | DataCite (arXiv DOI) | **verified** | Calibrated Learning to Defer with One-vs-All Classifiers — `10.48550/arXiv.2202.03673` |
| 13 | `closedloop2022` | DataCite (arXiv DOI) | **verified** | Designing Closed Human-in-the-loop Deferral Pipelines — `10.48550/arXiv.2202.04718` |
| 14 | `complement2022` | DataCite (arXiv DOI) | **verified** | Forming Effective Human-AI Teams: Building Machine Learning Models that Complement the C — `10.48550/arXiv.2206.07948` |
| 15 | `sampleefficient2022` | DataCite (arXiv DOI) | **verified** | Sample Efficient Learning of Predictors that Complement Humans — `10.48550/arXiv.2207.09584` |
| 16 | `limitedexpert2023` | DataCite (arXiv DOI) | **verified** | Learning to Defer with Limited Expert Predictions — `10.48550/arXiv.2304.07306` |
| 17 | `guideexperts2023` | DataCite (arXiv DOI) | **verified** | Learning to Guide Human Experts via Personalized Large Language Models — `10.48550/arXiv.2308.06039` |
| 18 | `fifar2023` | DataCite (arXiv DOI) | **verified** | FiFAR: A Fraud Detection Dataset for Learning to Defer — `10.48550/arXiv.2312.13218` |
| 19 | `a2c2024` | DataCite (arXiv DOI) | **verified** | A2C: A Modular Multi-stage Collaborative Decision Framework for Human-AI Teams — `10.48550/arXiv.2401.14432` |
| 20 | `deferpopulation2024` | DataCite (arXiv DOI) | **verified** | Learning to Defer to a Population: A Meta-Learning Approach — `10.48550/arXiv.2403.02683` |
| 21 | `workload2024` | DataCite (arXiv DOI) | **verified** | Cost-Sensitive Learning to Defer to Multiple Experts with Workload Constraints — `10.48550/arXiv.2403.06906` |
| 22 | `causaldefer2024` | DataCite (arXiv DOI) | **verified** | A Causal Framework for Evaluating Deferring Systems — `10.48550/arXiv.2405.18902` |
| 23 | `multidefer2024` | DataCite (arXiv DOI) | **verified** | A Unifying Post-Processing Framework for Multi-Objective Learn-to-Defer Problems — `10.48550/arXiv.2407.12710` |
| 24 | `coverage2024` | DataCite (arXiv DOI) | **verified** | Coverage-Constrained Human-AI Cooperation with Multiple Experts — `10.48550/arXiv.2411.11976` |
| 25 | `partialdefer2025` | DataCite (arXiv DOI) | **verified** | Learning to Partially Defer for Sequences — `10.48550/arXiv.2502.01459` |
| 26 | `identityfree2025` | DataCite (arXiv DOI) | **verified** | Identity-Free Deferral For Unseen Experts — `10.48550/arXiv.2502.10533` |
| 27 | `abstainrank2025` | DataCite (arXiv DOI) | **verified** | Bounded-Abstention Pairwise Learning to Rank — `10.48550/arXiv.2505.23437` |
| 28 | `socdefer2025` | DataCite (arXiv DOI) | **verified** | Adaptive alert prioritisation in security operations centres via learning to defer with  — `10.48550/arXiv.2506.18462` |
| 29 | `failfast2025` | DataCite (arXiv DOI) | **verified** | Fail Fast, or Ask: Mitigating the Deficiencies of Reasoning LLMs with Human-in-the-Loop  — `10.48550/arXiv.2507.14406` |
| 30 | `uqvsdefer2025` | DataCite (arXiv DOI) | **verified** | Is Uncertainty Quantification a Viable Alternative to Learned Deferral? — `10.48550/arXiv.2508.02319` |
| 31 | `nodefer2025` | DataCite (arXiv DOI) | **verified** | No Need for Learning to Defer? A Training Free Deferral Framework to Multiple Experts th — `10.48550/arXiv.2509.12573` |
| 32 | `knowdefer2025` | DataCite (arXiv DOI) | **verified** | Knowing When to Defer: Selective Prediction for Responsible Knowledge Tracing — `10.48550/arXiv.2509.21514` |
| 33 | `ask2025` | DataCite (arXiv DOI) | **verified** | To Ask or Not to Ask: Learning to Require Human Feedback — `10.48550/arXiv.2510.08314` |
| 34 | `popdemos2025` | DataCite (arXiv DOI) | **verified** | Learning To Defer To A Population With Limited Demonstrations — `10.48550/arXiv.2510.19351` |
| 35 | `fatigue2026` | DataCite (arXiv DOI) | **verified** | Fatigue-Aware Learning to Defer via Constrained Optimisation — `10.48550/arXiv.2604.00904` |
| 36 | `deferredseg2026` | DataCite (arXiv DOI) | **verified** | DeferredSeg:A Multi-Expert Deferral Framework for Medical Image Segmentation — `10.48550/arXiv.2604.12411` |
| 37 | `l2dclinical2026` | DataCite (arXiv DOI) | **verified** | L2D-Clinical: Learning to Defer for Adaptive Model Selection in Clinical Text Classifica — `10.48550/arXiv.2604.13285` |
| 38 | `faircoop2026` | DataCite (arXiv DOI) | **verified** | People-Centred Medical Image Analysis via Fairness-Aware Human-AI Cooperation — `10.48550/arXiv.2604.26991` |
| 39 | `abstainfair2023` | DataCite (arXiv DOI) | **verified** | Fair Classifiers that Abstain without Harm — `10.48550/arXiv.2310.06205` |
| 40 | `vqaabstain2022` | DataCite (arXiv DOI) | **verified** | Reliable Visual Question Answering: Abstain Rather Than Answer Incorrectly — `10.48550/arXiv.2204.13631` |
| 41 | `querycontrol2025` | DataCite (arXiv DOI) | **verified** | Sample-Efficient Expert Query Control in Active Imitation Learning via Conformal Predict — `10.48550/arXiv.2512.00453` |
| 42 | `breiman1996bagging` | Crossref | **verified** | Bagging predictors — `10.1007/bf00058655` |
| 43 | `breiman2001forests` | Crossref | **verified** | Random Forests — `10.1023/a:1010933404324` |
| 44 | `freund1997boosting` | Crossref | **verified** | A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting — `10.1006/jcss.1997.1504` |
| 45 | `dietterich2000ensemble` | Crossref | **verified** | Ensemble Methods in Machine Learning — `10.1007/3-540-45014-9_1` |
| 46 | `kuncheva2003diversity` | Crossref | **verified** | Measures of Diversity in Classifier Ensembles and Their Relationship with the Ensemble A — `10.1023/a:1022859003006` |
| 47 | `wolpert1992stacked` | Crossref | **verified** | Stacked generalization — `10.1016/s0893-6080(05)80023-1` |
| 48 | `hinton1999product` | Crossref | **verified** | Products of experts — `10.1049/cp:19991075` |
| 49 | `deepensembles2016` | DataCite (arXiv DOI) | **verified** | Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles — `10.48550/arXiv.1612.01474` |
| 50 | `deceptionensembles2019` | DataCite (arXiv DOI) | **verified** | Deep Neural Network Ensembles against Deception: Ensemble Diversity, Accuracy and Robust — `10.48550/arXiv.1908.11091` |
| 51 | `negcorr2020` | DataCite (arXiv DOI) | **verified** | Generalized Negative Correlation Learning for Deep Ensembling — `10.48550/arXiv.2011.02952` |
| 52 | `dexdeepfm2021` | DataCite (arXiv DOI) | **verified** | DexDeepFM: Ensemble Diversity Enhanced Extreme Deep Factorization Machine Model — `10.48550/arXiv.2104.01924` |
| 53 | `gnnensembles2023` | DataCite (arXiv DOI) | **verified** | Graph Neural Network Interatomic Potential Ensembles with Calibrated Aleatoric and Epist — `10.48550/arXiv.2305.16325` |
| 54 | `ltauf2024` | DataCite (arXiv DOI) | **verified** | LTAU-FF: Loss Trajectory Analysis for Uncertainty in Atomistic Force Fields — `10.48550/arXiv.2402.00853` |
| 55 | `heteroens2025` | DataCite (arXiv DOI) | **verified** | Heterogeneous Ensemble Enables a Universal Uncertainty Metric for Atomistic Foundation M — `10.48550/arXiv.2507.21297` |
| 56 | `rashomon2025` | DataCite (arXiv DOI) | **verified** | Exploring the Rashomon Set for Concept-Based Models — `10.48550/arXiv.2511.19636` |
| 57 | `vaswani2017attention` | DataCite (arXiv DOI) | **verified** | Attention Is All You Need — `10.48550/arXiv.1706.03762` |
| 58 | `wei2022cot` | DataCite (arXiv DOI) | **verified** | Chain-of-Thought Prompting Elicits Reasoning in Large Language Models — `10.48550/arXiv.2201.11903` |
| 59 | `wang2023selfconsistency` | DataCite (arXiv DOI) | **verified** | Self-Consistency Improves Chain of Thought Reasoning in Language Models — `10.48550/arXiv.2203.11171` |
| 60 | `lightman2023verify` | DataCite (arXiv DOI) | **verified** | Let's Verify Step by Step — `10.48550/arXiv.2305.20050` |
| 61 | `bai2022constitutional` | DataCite (arXiv DOI) | **verified** | Constitutional AI: Harmlessness from AI Feedback — `10.48550/arXiv.2212.08073` |
| 62 | `madaan2023selfrefine` | DataCite (arXiv DOI) | **verified** | Self-Refine: Iterative Refinement with Self-Feedback — `10.48550/arXiv.2303.17651` |
| 63 | `shinn2023reflexion` | DataCite (arXiv DOI) | **verified** | Reflexion: Language Agents with Verbal Reinforcement Learning — `10.48550/arXiv.2303.11366` |
| 64 | `zheng2023judge` | DataCite (arXiv DOI) | **verified** | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena — `10.48550/arXiv.2306.05685` |
| 65 | `yao2023tree` | DataCite (arXiv DOI) | **verified** | Tree of Thoughts: Deliberate Problem Solving with Large Language Models — `10.48550/arXiv.2305.10601` |
| 66 | `yao2022react` | DataCite (arXiv DOI) | **verified** | ReAct: Synergizing Reasoning and Acting in Language Models — `10.48550/arXiv.2210.03629` |
| 67 | `cobbe2021verifiers` | DataCite (arXiv DOI) | **verified** | Training Verifiers to Solve Math Word Problems — `10.48550/arXiv.2110.14168` |
| 68 | `huang2023selfcorrect` | DataCite (arXiv DOI) | **verified** | Large Language Models Cannot Self-Correct Reasoning Yet — `10.48550/arXiv.2310.01798` |
| 69 | `opv2025` | DataCite (arXiv DOI) | **verified** | OPV: Outcome-based Process Verifier for Efficient Long Chain-of-Thought Verification — `10.48550/arXiv.2512.10756` |
| 70 | `vlgenrm2025` | DataCite (arXiv DOI) | **verified** | VL-GenRM: Enhancing Vision-Language Verification via Vision Experts and Iterative Traini — `10.48550/arXiv.2506.13888` |
| 71 | `neuroformal2026` | DataCite (arXiv DOI) | **verified** | Neuro-Symbolic Generation and Validation of Memory-Aware Formal Function Specifications — `10.48550/arXiv.2603.13414` |
| 72 | `uqsurvey2023` | DataCite (arXiv DOI) | **verified** | Survey on Leveraging Uncertainty Estimation Towards Trustworthy Deep Neural Networks: Th — `10.48550/arXiv.2304.04906` |
| 73 | `liu2023lostmiddle` | DataCite (arXiv DOI) | **verified** | Lost in the Middle: How Language Models Use Long Contexts — `10.48550/arXiv.2307.03172` |
| 74 | `confidadptive2022` | Crossref | **verified** | Confident Adaptive Language Modeling — `10.52202/068431-1269` |
| 75 | `branchynet2016` | Crossref | **verified** | BranchyNet: Fast inference via early exiting from deep neural networks — `10.1109/icpr.2016.7900006` |
| 76 | `viola2001cascade` | Crossref | **verified** | Rapid object detection using a boosted cascade of simple features — `10.1109/cvpr.2001.990517` |
| 77 | `shazeer2017moe` | DataCite (arXiv DOI) | **verified** | Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer — `10.48550/arXiv.1701.06538` |
| 78 | `jacobs1991mixture` | Crossref | **verified** | Adaptive Mixtures of Local Experts — `10.1162/neco.1991.3.1.79` |
| 79 | `bacchelli2013codereview` | Crossref | **verified** | Expectations, outcomes, and challenges of modern code review — `10.1109/icse.2013.6606617` |
| 80 | `sadowski2018googlereview` | Crossref | **verified** | Modern code review — `10.1145/3183519.3183525` |
| 81 | `peng2023copilot` | DataCite (arXiv DOI) | **verified** | The Impact of AI on Developer Productivity: Evidence from GitHub Copilot — `10.48550/arXiv.2302.06590` |
| 82 | `dietvorst2015aversion` | Crossref | **verified** | Algorithm aversion: People erroneously avoid algorithms after seeing them err. — `10.1037/xge0000033` |
| 83 | `parasuraman1997automationbias` | Crossref | **verified** | Humans and Automation: Use, Misuse, Disuse, Abuse — `10.1518/001872097778543886` |
| 84 | `bainbridge1983ironies` | Crossref | **verified** | Ironies of automation — `10.1016/0005-1098(83)90046-8` |
| 85 | `leesee2004trust` | Crossref | **verified** | Trust in Automation: Designing for Appropriate Reliance — `10.1518/hfes.46.1.50_30392` |
| 86 | `psychmachines2026` | DataCite (arXiv DOI) | **verified** | The Psychology of Learning from Machines: Anthropomorphic AI and the Paradox of Automati — `10.48550/arXiv.2601.06172` |
| 87 | `reviewerconfidence2025` | DataCite (arXiv DOI) | **verified** | Are the confidence scores of reviewers consistent with the review content? Evidence from — `10.48550/arXiv.2505.15031` |
| 88 | `chilgrader2026` | DataCite (arXiv DOI) | **verified** | CHiL(L)Grader: Calibrated Human-in-the-Loop Short-Answer Grading — `10.48550/arXiv.2603.11957` |
| 89 | `metacog2026` | DataCite (arXiv DOI) | **verified** | Adaptive Collaboration with Humans: Metacognitive Policy Optimization for Multi-Agent LL — `10.48550/arXiv.2603.07972` |
| 90 | `causalperception2024` | DataCite (arXiv DOI) | **verified** | Toward A Causal Framework for Modeling Perception — `10.48550/arXiv.2401.13408` |
| 91 | `unequalunc2025` | DataCite (arXiv DOI) | **verified** | Unequal Uncertainty: Rethinking Algorithmic Interventions for Mitigating Discrimination  — `10.48550/arXiv.2508.07872` |
| 92 | `oodunc2024` | DataCite (arXiv DOI) | **verified** | Using Uncertainty Quantification to Characterize and Improve Out-of-Domain Learning for  — `10.48550/arXiv.2403.10642` |
| 93 | `knight1986nversion` | Crossref | **verified** | An experimental evaluation of the assumption of independence in multiversion programming — `10.1109/tse.1986.6312924` |
| 94 | `avizienis1985nversion` | Crossref | **verified** | The N-Version Approach to Fault-Tolerant Software — `10.1109/tse.1985.231893` |
| 95 | `randell1975faulttolerance` | Crossref | **verified** | System structure for software fault tolerance — `10.1145/800027.808467` |
| 96 | `littlewood1989coincident` | Crossref | **verified** | Conceptual modeling of coincident failures in multiversion software — `10.1109/32.58771` |
| 97 | `eckhardt1985coincident` | Crossref | **verified** | A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Erro — `10.1109/tse.1985.231895` |
| 98 | `lyons1962tmr` | Crossref | **verified** | The Use of Triple-Modular Redundancy to Improve Computer Reliability — `10.1147/rd.62.0200` |
| 99 | `recoveryblocks1985` | Crossref | **verified** | Recovery Blocks in Action: A System Supporting High Reliability — `10.1007/978-3-642-82470-8_9` |
| 100 | `lamport1982byzantine` | Crossref | **verified** | The Byzantine Generals Problem — `10.1145/357172.357176` |
| 101 | `castro1999pbft` | Crossref | **verified** | Practical byzantine fault tolerance and proactive recovery — `10.1145/571637.571640` |
| 102 | `russell1991metareasoning` | Crossref | **verified** | Principles of metareasoning — `10.1016/0004-3702(91)90015-c` |
| 103 | `howard1966valueinfo` | Crossref | **verified** | Information Value Theory — `10.1109/tssc.1966.300074` |
| 104 | `efron1979bootstrap` | Crossref | **verified** | Bootstrap Methods: Another Look at the Jackknife — `10.1214/aos/1176344552` |
| 105 | `wilson1927probable` | Crossref | **verified** | Probable Inference, the Law of Succession, and Statistical Inference — `10.1080/01621459.1927.10502953` |
| 106 | `benjamini1995fdr` | Crossref | **verified** | Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Test — `10.1111/j.2517-6161.1995.tb02031.x` |
| 107 | `lecun2015deeplearning` | Crossref | **verified** | Deep learning — `10.1038/nature14539` |
| 108 | `layered2026` | DataCite (arXiv DOI) | **verified** | When Review Alone No Longer Scales: Layered Supervision in AI-Assisted Software Engineer — `10.48550/arXiv.2608.26316` |
| 109 | `cerberus2026` | DataCite (arXiv DOI) | **verified** | Cerberus: Cross-Layer ECC Co-Design for Robust and Efficient Memory Protection — `10.48550/arXiv.2605.02220` |
| 110 | `bmc2026` | DataCite (arXiv DOI) | **verified** | Agentic Model Checking — `10.48550/arXiv.2605.21434` |
| 111 | `helios2026` | DataCite (arXiv DOI) | **verified** | HELIOS: An LLM-Driven Autonomous Indirect Trajectory Optimization Agent — `10.48550/arXiv.2607.24051` |
| 112 | `specgen2026` | DataCite (arXiv DOI) | **verified** | How Powerful are LLMs in Generating Formal Program Specifications? — `10.48550/arXiv.2608.13077` |
| 113 | `ltd2026` | DataCite (arXiv DOI) | **verified** | Too Much of the Same: From Algorithmic to Human Bias in Learning to Defer — `10.48550/arXiv.2608.28050` |
| 114 | `flowbyflow2026` | DataCite (arXiv DOI) | **verified** | Flow-by-Flow:Content-Judgment Bypass for Governing AI Output in High-Loss Domains — `10.48550/arXiv.2608.07474` |
| 115 | `aniso2026` | DataCite (arXiv DOI) | **verified** | Feature-Aware Anisotropic Local Differential Privacy for Utility-Preserving Graph Repres — `10.48550/arXiv.2604.05077` |
| 116 | `mllmunc2026` | DataCite (arXiv DOI) | **verified** | Uncertainty-Aware Decision Making in Multimodal Large Language Models — `10.48550/arXiv.2608.17084` |
| 117 | `feat2025` | DataCite (arXiv DOI) | **verified** | FEAT: A Multi-Agent Forensic AI System with Domain-Adapted Large Language Model for Auto — `10.48550/arXiv.2508.07950` |

## Corrections forced by the gate

| recalled identifier | what it actually resolves to | replacement |
|---|---|---|
| `10.1109/TC.1985.1676513` | Fault-Tolerant Multiprocessor Link and Bus Network Architectures | `10.1109/tse.1985.231893 Avizienis N-version` |
| `10.1109/TSE.1975.233554` | 404 not found | `10.1145/800027.808467 Randell` |
| `10.1109/32.58790` | Formal verification of Ada programs | `10.1109/32.58771 Littlewood and Miller` |
| `10.1109/TSE.1985.231890` | Bayesian Extensions to a Basic Model of Software Reliability | `10.1109/tse.1985.231895 Eckhardt and Lee` |
| `10.1287/mnsc.2014.1984` | The Impact of Corporate Sustainability on Organizational Processes | `10.1037/xge0000033 Dietvorst et al.` |
| `arXiv:2001.08049` | On Last-Layer Algorithms for Classification | `arXiv:2006.01862 Mozannar and Sontag` |
| `arXiv:1904.01685` | Measuring Calibration in Deep Learning | `arXiv:1901.09192 SelectiveNet` |

