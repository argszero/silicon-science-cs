# Reference authenticity check - issue #50

**Manuscript:** *When Does Speculative Tool Execution Pay? Contention Boundaries,
Latency Tails, and the Parallelism the Serial Baseline Already Had* (issue #50).

**Rule applied:** submission quality bar item 12 - every reference is verified against
a real external record before submission; any entry that cannot be verified is
deleted or replaced, never submitted.

## The instrument and what it read

`artefacts/refs_verify_v50.py` -- the package's own copy, which IS shipped -- reads
each selected row and re-reads its locator against the live record. Two query forms,
one per locator kind, **and every request carries a known-present control**:

| locator kind | endpoint | control |
|---|---|---|
| DOI (71 row(s)) | `https://api.crossref.org/works/<doi>` | `10.1145/2408776.2408794` |
| arXiv (66 row(s)) | `http://export.arxiv.org/api/query?id_list=...` | `1706.03762v7` |

Every field is read **twice** - the live record on its own terms (each value is reported
with the field it came from), and the entry's own line against it: title, anchor, year,
authors. A year is taken from a publication date field only. Crossref's `created` is a
DOI registration date and is not a publication date at all (measured: it reports
2002-11-07 for a paper published in 2000), and the **issue** date `published-print` is
read only where no publication date exists (measured: reading it first reported 2026 for
a paper published 2025, and reported three correct entries as defects).

**The arXiv read counts as well as controls.** arXiv's `max_results` defaults to 10 and
truncates an `id_list` silently; measured here, a request naming 15 ids without
`max_results` returns exactly 10 entries, and the control came back inside the window
either way - a control only detects the failures that can remove it. So `max_results` is
stated as the number of ids asked for, **and the returned count is compared with the
requested count**; any id a batch does not return is re-read on its own, in a request
that carries the control and asks for exactly that id, and is reported ABSENT only when
both reads agree.

## The run

- verification taken: 2026-09-19 *(a coordinate of when this reading was made, not a property of the bibliography; every other number below is read from the artefacts)*
- rows verified: **137 of 137**
- inputs: `refs_selection_v50.json` sha256 `e371fe03fdb6c461...`, `refs_year_supply_v50.json` sha256 `33aac7b5645bd3f3...`
- artefact: `refs_verified_v50.json` sha256 `4f244e9dd78598a1...`, 175537 B (byte-identical across two independent runs)
- Crossref control returned: `The tail at scale` (71 of 71 DOI row(s) returned, 0 not returned)
- arXiv control present in 2 of 2 batch(es); requested 66 id(s), returned 66; shortfalls 0, single-id fallbacks 0
- **result: DECLARED 4, SUPPLIED 66, VERIFIED 67**

`VERIFIED` = every field matched the entry's own line. `SUPPLIED` = the entry's stored
year was null and the live record carries one (the selection layer read a field only one
channel carries - see *What the first pass of this instrument got wrong*, below). `DECLARED` = the record
carries no publication date at all and the year comes from the declaration in
`refs_year_supply_v50.json`.

## Entry by entry

Format: **key** (section) - method -> result - the real record found: title / authors /
year and **the field the year was read from** / resolvable locator. The one-line stated
difference each entry carries is a property of the bibliography and is not repeated here.

1. **advised2022** (S2.6) - `crossref_doi` -> **VERIFIED** - Machine learning advised algorithms for the ski rental problem with a discount / Bhattacharya, Arghya; Das, Rathish / 2022 via issued / <https://doi.org/10.1016/j.tcs.2022.10.006>
2. **agentboundary2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - When Tool Calls Succeed but Workflows Fail: Anomalies at the Agent-Tool Boundary / Artem Trofimov; Boris Novikov / 2026 via published / <https://arxiv.org/abs/2609.15397v1>
3. **agentspec2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - AgentSpec: Speculative Decoding for Batch Inference of LLM Agents / Xin Wang; Ziming Miao; Yi Zhu; Hui Shen; Zhongwei Wan; Fan Yang; Mi Zhang / 2026 via published / <https://arxiv.org/abs/2608.24004v1>
4. **aktas2017** (S2.4) - `arxiv_id_list` -> **SUPPLIED** - Effective Straggler Mitigation: Which Clones Should Attack and When? / Mehmet Fatih Aktas; Pei Peng; Emina Soljanin / 2017 via published / <https://arxiv.org/abs/1710.00748v1>
5. **aktas2017b** (S2.4) - `arxiv_id_list` -> **SUPPLIED** - Straggler Mitigation by Delayed Relaunch of Tasks / Mehmet Fatih Aktas; Pei Peng; Emina Soljanin / 2017 via published / <https://arxiv.org/abs/1710.00414v1>
6. **alossurvey2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Is Multimodal Speculative Decoding Ready for Diffusion-Based Parallel Drafting? A Survey and Empirical Diagnosis / Yantao Li; Huanlin Gao; Fang Zhao; Chao Tan; Qiang Hui; Shuting Liu; Fuyuan Shi; Ting Lu; Shaoan Zhao; Xueqiang Guo; Xinpei Su; Jianbing Zhang; Xinyu Dai; Kai Wang; Shiguo Lian / 2026 via published / <https://arxiv.org/abs/2608.20743v2>
7. **amdahl2007** (S2.7) - `crossref_doi` -> **VERIFIED** - Parallel test description and analysis of parallel test system speedup through Amdahl&amp;#x0027;s law / Waivio, Nathan / 2007 via issued / <https://doi.org/10.1109/autest.2007.4374292>
8. **amdahl2013** (S2.7) - `crossref_doi` -> **VERIFIED** - Computer Architecture and Amdahl's Law / Amdahl, Gene M. / 2013 via issued / <https://doi.org/10.1109/mc.2013.418>
9. **amdahl2017** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - How Amdahl's low restricts supercomputer applications and building ever bigger supercomputers / János Végh / 2017 via published / <https://arxiv.org/abs/1708.01462v2>
10. **amdahl2017b** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - The Effect of Temperature on Amdahl Law in 3D Multicore Era / Leonid Yavits; Amir Morad; Ran Ginosar / 2017 via published / <https://arxiv.org/abs/1705.07280v1>
11. **amdahl2021** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - On Extending Amdahl's law to Learn Computer Performance / Chaitanya Poolla; Rahul Saxena / 2021 via published / <https://arxiv.org/abs/2110.07822v2>
12. **amdahl2026** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Modernizing Amdahl's Law: How AI Scaling Laws Shape Computer Architecture / Chien-Ping Lu / 2026 via published / <https://arxiv.org/abs/2603.20654v4>
13. **amdahl2026b** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Scaling LLM Inference Beyond Amdahl`s Limits via Eliminating Non-Scalable Overheads / Alan Zhao; Cyril Y. He; Wei Xu / 2026 via published / <https://arxiv.org/abs/2606.01927v1>
14. **anotherview1990** (S2.7) - `crossref_doi` -> **DECLARED** - Another view on parallel speedup / Sun, X.-H.; Ni, L.M. / 1990 via declared from event.name, locator / <https://doi.org/10.1109/superc.1990.130037>
15. **antoniadis2022** (S2.6) - `crossref_doi` -> **VERIFIED** - Online Algorithms for Weighted Paging with Predictions / Jiang, Zhihao; Panigrahi, Debmalya; Sun, Kevin / 2022 via issued / <https://doi.org/10.1145/3548774>
16. **antoniadis2023metric** (S2.6) - `crossref_doi` -> **VERIFIED** - Online Metric Algorithms with Untrusted Predictions / Antoniadis, Antonios; Coester, Christian; Eliáš, Marek; Polak, Adam; Simon, Bertrand / 2023 via issued / <https://doi.org/10.1145/3582689>
17. **asymspec2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - AsymSpec: Context-Asymmetric Speculative Decoding for Agentic LLMs / Sheng Liang; Yongyue Zhang; Nathanael Brian; Hang Lv; Hao Wang; Chen Zhang; Yong Liu / 2026 via published / <https://arxiv.org/abs/2608.26004v1>
18. **barik2026** (S2.3) - `crossref_doi` -> **VERIFIED** - Analysis and optimal control in an $$M^X/G/1$$ queueing model with heavy-tailed service-time distribution / Barik, Sitaram; Banik, A. D.; Chaudhry, Mohan; Ghosh, Souvik / 2026 via issued / <https://doi.org/10.1007/s12597-026-01126-w>
19. **bhattacharyya2019** (S2.1) - `arxiv_id_list` -> **SUPPLIED** - SMoTherSpectre: exploiting speculative execution through port contention / Atri Bhattacharyya; Alexandra Sandulescu; Matthias Neugschwandtner; Alessandro Sorniotti; Babak Falsafi; Mathias Payer; Anil Kurmus / 2019 via published / <https://arxiv.org/abs/1903.01843v3>
20. **bpaste2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - B-PASTE: Beam-Aware Pattern-Guided Speculative Execution for Resource-Constrained LLM Agents / Yanfei Song / 2026 via published / <https://arxiv.org/abs/2604.16469v1>
21. **bush2022** (S2.5) - `arxiv_id_list` -> **SUPPLIED** - Stable Scheduling in Transactional Memory / Costas Busch; Bogdan S. Chlebus; Dariusz R. Kowalski; Pavan Poudel / 2022 via published / <https://arxiv.org/abs/2208.07359v1>
22. **calibrated2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Algorithms with Calibrated Machine Learning Predictions / Judy Hanwen Shen; Ellen Vitercik; Anders Wikum / 2025 via published / <https://arxiv.org/abs/2502.02861v4>
23. **calibrateroute2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Calibrate, Then Route: A Measured Study of Learned Request Routing for Disaggregated LLM Serving / Srikanta Datta Tumkur; Jay Iyer; Mehar Simhadri; Sai Pavan Kumar; Sai Kapil Kumar; Ramesh Nampelly / 2026 via published / <https://arxiv.org/abs/2609.16206v1>
24. **canonne2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - With a Little Help From My Friends: Exploiting Probability Distribution Advice in Algorithm Design / Clément L. Canonne; Kenny Chen; Julián Mestre / 2025 via published / <https://arxiv.org/abs/2505.04949v2>
25. **cauligi2021** (S2.1) - `arxiv_id_list` -> **SUPPLIED** - SoK: Practical Foundations for Software Spectre Defenses / Sunjay Cauligi; Craig Disselkoen; Daniel Moghimi; Gilles Barthe; Deian Stefan / 2021 via published / <https://arxiv.org/abs/2105.05801v3>
26. **chen2008** (S2.1) - `crossref_doi` -> **VERIFIED** - Hiding I/O latency with pre-execution prefetching for parallel applications / Yong Chen; Byna, S.; Xian-He Sun; Thakur, R.; Gropp, W. / 2008 via issued / <https://doi.org/10.1109/sc.2008.5213209>
27. **chen2009** (S2.4) - `crossref_doi` -> **VERIFIED** - Influence of heavytailed distribution on network traffic / CHEN, Chu; XU, Yong; ZHANG, Ling / 2009 via issued / <https://doi.org/10.3724/sp.j.1087.2009.01520>
28. **chen2014** (S2.1) - `crossref_doi` -> **VERIFIED** - Improving MapReduce Performance Using Smart Speculative Execution Strategy / Chen, Qi; Liu, Cheng; Xiao, Zhen / 2014 via issued / <https://doi.org/10.1109/tc.2013.15>
29. **chronos2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Chronos: Efficient Bolt-on Branching Across Data Stores for Stateful Agentic Applications / Xinjing Zhou; Jason Mohoney; Samuel Madden; Michael Stonebraker; Lei Cao / 2026 via published / <https://arxiv.org/abs/2609.14889v1>
30. **chydzinski2024b** (S2.3) - `crossref_doi` -> **VERIFIED** - Response Time of Queueing Mechanisms / Chydzinski, Andrzej; Adamczyk, Blazej / 2024 via issued / <https://doi.org/10.3390/sym16030271>
31. **cnncost2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - CARB: A Characterization-Guided Framework for CNN Inference Cost Prediction and Deployment Screening / Linh Nguyen; Zhixin Pan / 2026 via published / <https://arxiv.org/abs/2608.10506v1>
32. **combinatorial2025** (S2.6) - `crossref_doi` -> **VERIFIED** - Combinatorial Ski Rental Problem: Robust and Learning-Augmented Algorithms / Li, Ziwei; Sun, Bo; Zhang, Zhiqiu; Hajiesmaili, Mohammad; Wu, Binghan; Yang, Lin; Gao, Yang / 2025 via issued / <https://doi.org/10.52202/085713-4014>
33. **costaware2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Cost-Aware Speculative Execution for LLM-Agent Workflows: An Integrated Five-Dimension Method / Faisal Fareed / 2026 via published / <https://arxiv.org/abs/2606.07846v1>
34. **cui2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Ski Rental with Distributional Predictions of Unknown Quality / Qiming Cui; Michael Dinitz / 2026 via published / <https://arxiv.org/abs/2602.21104v1>
35. **dauria2021** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - An M/M/c queue with queueing-time dependent service rates / Bernardo D'Auria; Ivo J. B. F. Adan; René Bekker; Vidyadhar Kulkarni / 2021 via published / <https://arxiv.org/abs/2107.04557v1>
36. **desai2026** (S2.5) - `crossref_doi` -> **VERIFIED** - Reliable Event-Driven Processing in Distributed Systems: Stage-Aware Retries, Idempotency, and Exactly-Once Semantics / Jay Bankimchandra Desai / 2026 via issued / <https://doi.org/10.52783/jisem.v11i2s.14608>
37. **discount2022** (S2.6) - `crossref_doi` -> **VERIFIED** - Machine Learning Advised Ski Rental Problem with a Discount / Bhattacharya, Arghya; Das, Rathish / 2022 via issued / <https://doi.org/10.1007/978-3-030-96731-4_18>
38. **discrete2026** (S2.6) - `crossref_doi` -> **VERIFIED** - Learning-Augmented Ski Rental with Discrete Distribution: A Bayesian Approach / Kang, Bosun; Park, Hyejun; Fan, Chenglin / 2026 via issued / <https://doi.org/10.1609/aaai.v40i43.40991>
39. **divisible2021** (S2.7) - `crossref_doi` -> **VERIFIED** - Integrating Amdahl-like Laws and Divisible Load Theory / Cao, Yang; Wu, Fei; Robertazzi, Thomas / 2021 via issued / <https://doi.org/10.1142/s0129626421500080>
40. **dlt2025** (S2.7) - `crossref_doi` -> **VERIFIED** - A DLT-Aware Performance Evaluation Framework for Virtual-Core Speedup Modeling / Xiang, Zile; Robertazzi, Thomas G. / 2025 via issued / <https://doi.org/10.3390/fi17110519>
41. **dusad2025** (S2.5) - `crossref_doi` -> **VERIFIED** - Taming Asynchrony in Distributed Payment Systems: Guarantees, Idempotency, and End-to-End Reconciliation / Krishna Dusad / 2025 via issued / <https://doi.org/10.32996/jcsts.2025.7.11.33>
42. **eeckhout2025** (S2.7) - `crossref_doi` -> **VERIFIED** - Use Equal-Work or Equal-Time Speedup, Not Geomean Speedup / Eeckhout, Lieven / 2025 via issued / <https://doi.org/10.1109/ispass64960.2025.00033>
43. **eeckhout2025b** (S2.7) - `crossref_doi` -> **VERIFIED** - R.I.P. Geomean Speedup Use Equal-Work (Or Equal-Time) Harmonic Mean Speedup Instead / Eeckhout, Lieven / 2025 via issued / <https://doi.org/10.1109/hpca61900.2025.00132>
44. **exp2024** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Multi-level projection with exponential parallel speedup; Application to sparse auto-encoders neural networks / Guillaume Perez; Michel Barlaud / 2024 via published / <https://arxiv.org/abs/2405.02086v2>
45. **fagin2024** (S2.5) - `crossref_doi` -> **VERIFIED** - Minimal idempotency, partial idempotency, search heuristics and constructive algorithms for idempotent integers / Fagin, Barry S. / 2024 via issued / <https://doi.org/10.5802/pmb.53>
46. **finch2019** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - M/M/$c$ Queues and the Poisson Clumping Heuristic / Steven Finch / 2019 via published / <https://arxiv.org/abs/1904.04054v1>
47. **fixedsize2011** (S2.7) - `crossref_doi` -> **VERIFIED** - Fixed-Size Speedup / (the record carries no author field) / 2011 via issued / <https://doi.org/10.1007/978-0-387-09766-4_2184>
48. **fleet2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - FleetSieve: Decision-Critical Profiling for SLO-Aware LLM Fleet Configuration / Huang Cheng; Scott Zhang; Aubert Li / 2026 via published / <https://arxiv.org/abs/2608.19659v1>
49. **forkjoin2026** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - From Fork-Join to Asynchronous Tasks: Parallelizing Tiled Cholesky Decomposition with OpenMP and HPX / Alexander Strack; Alexander Van Craen; Dirk Pflüger / 2026 via published / <https://arxiv.org/abs/2606.11937v1>
50. **gao2026** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Stability of Fork-Join Systems with Redundancy and Heterogeneous Servers / Chutong Gao; Seyed Iravani; Ohad Perry / 2026 via published / <https://arxiv.org/abs/2609.09237v1>
51. **ghosttools2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Ghost Tool Calls: Issue-Time Privacy for Speculative Agent Tools / Bardia Mohammadi; Lars Klein; Akhil Arora; Laurent Bindschaedler / 2026 via published / <https://arxiv.org/abs/2606.02483v1>
52. **gocmen2025** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Scheduling in Queueing Systems with Uncertain and Evolving Holding Costs / Caner Gocmen; Thodoris Lykouris; Deeksha Sinha; Wentao Weng / 2025 via published / <https://arxiv.org/abs/2505.21331v2>
53. **grotov2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - How to Speculate about Uncertainty in Agentic Coding? A Draft-Model Gate Method / Konstantin Grotov; Valentin Malykh / 2026 via published / <https://arxiv.org/abs/2609.05274v1>
54. **hidelatency2026** (S2.2) - `crossref_doi` -> **VERIFIED** - Hiding Service Latency: A Deterministic Asynchronous Execution Paradigm for Agent-Based Transport Simulations / Heinrich, Paul; Nagel, Kai / 2026 via issued / <https://doi.org/10.1145/3806789.3810973>
55. **hydra2026** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Hydra: Phase-Aware Workload Characterization of LLM Inference across Edge SoC Generations, Backends, and Quantization Levels / Amir Taherin; Sana Taghipour Anvari; Charles Amante; Yixiao Chen; Ruben Noroian; Zlatan Feric; Nicolas Bohm Agostini; Pu Zhao; José Cano; Bin Ren; Yanzhi Wang; David Kaeli / 2026 via published / <https://arxiv.org/abs/2608.25053v1>
56. **ibrahim2017** (S2.1) - `crossref_doi` -> **VERIFIED** - Improving MapReduce Performance with Progress and Feedback Based Speculative Execution / Ibrahim, Ibrahim Adel; Bassiouni, Mostafa / 2017 via issued / <https://doi.org/10.1109/smartcloud.2017.25>
57. **idempotency2025** (S2.5) - `crossref_doi` -> **VERIFIED** - Idempotency Mechanisms in Digital Payment Systems: Preventing Duplicate Transaction Processing / (the record carries no author field) / 2025 via issued / <https://doi.org/10.48047/jocaaa.2025.34.11.02>
58. **improved2025** (S2.6) - `crossref_doi` -> **VERIFIED** - Improved Learning-Augmented Algorithms and (Tight) Lower Bounds for Multi-Option Ski Rental Problem / Shin, Yongho; Lee, Changyeol; Lee, Gukryeol; An, Hyung-Chan / 2025 via issued / <https://doi.org/10.1145/3763239>
59. **intro1998** (S2.5) - `crossref_doi` -> **VERIFIED** - An introduction to idempotency / Gunawardena, Jeremy / 1998 via issued / <https://doi.org/10.1017/cbo9780511662508.003>
60. **irani1998paging** (S2.6) - `crossref_doi` -> **VERIFIED** - Competitive analysis of paging / Irani, Sandy / 1998 via issued / <https://doi.org/10.1007/bfb0029564>
61. **iyer2023** (S2.4) - `crossref_doi` -> **VERIFIED** - Achieving Microsecond-Scale Tail Latency Efficiently with Approximate Optimal Scheduling / Iyer, Rishabh; Unal, Musa; Kogias, Marios; Candea, George / 2023 via issued / <https://doi.org/10.1145/3600006.3613136>
62. **ji2024** (S2.3) - `crossref_doi` -> **VERIFIED** - Heavy traffic scaling limits for shortest remaining processing time queues with light tailed processing time distributions / Ji, Chunxu; Puha, Amber L. / 2024 via issued / <https://doi.org/10.1007/s11134-024-09929-8>
63. **kanev2014** (S2.4) - `crossref_doi` -> **VERIFIED** - Tradeoffs between power management and tail latency in warehouse-scale applications / Kanev, Svilen; Hazelwood, Kim; Wei, Gu-Yeon; Brooks, David / 2014 via issued / <https://doi.org/10.1109/iiswc.2014.6983037>
64. **kim2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Robust and Consistent Ski Rental with Distributional Advice / Jihwan Kim; Chenglin Fan / 2026 via published / <https://arxiv.org/abs/2603.29233v1>
65. **konasani2026** (S2.5) - `crossref_doi` -> **VERIFIED** - Graph-Based Duplicate Trade Detection and Idempotency Framework Implementation in Distributed Electronic Trading Systems / Iswarya Konasani / 2026 via issued / <https://doi.org/10.22399/ijcesen.4940>
66. **koroliouk2021** (S2.3) - `crossref_doi` -> **VERIFIED** - Diffusion Approximation of Queueing Systems and Networks / Koroliouk, Dimitri; Koroliuk, Vladimir S. / 2021 via issued / <https://doi.org/10.1002/9781119755432.ch3>
67. **latencyhiding1993** (S2.1) - `crossref_doi` -> **VERIFIED** - Empirical study of latency hiding on a fine-grain parallel processor / Hiraki, Kei; Shimada, Toshio; Sekiguchi, Satoshi / 1993 via issued / <https://doi.org/10.1145/165939.165972>
68. **lawniczak2024** (S2.4) - `crossref_doi` -> **VERIFIED** - Targeting Tail Latency in Replicated Systems with Proactive Rejection / Lawniczak, Laura; Distler, Tobias / 2024 via issued / <https://doi.org/10.1145/3652892.3700775>
69. **lengthpred2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Scheduling LLM Inference with Uncertainty-Aware Output Length Predictions / Haoyu Zheng; Yongqiang Zhang; Fangcheng Fu; Xiaokai Zhou; Hao Luo; Hongchao Zhu; Yuanyuan Zhu; Hao Wang; Xiao Yan; Jiawei Jiang / 2026 via published / <https://arxiv.org/abs/2604.00499v2>
70. **linearspeedup2005** (S2.7) - `crossref_doi` -> **VERIFIED** - Scheduling parallel jobs with linear speedup / A., Grigoriev; M.J., Uetz / 2005 via issued / <https://doi.org/10.26481/umamet.2005015>
71. **mackenzie2020** (S2.4) - `crossref_doi` -> **VERIFIED** - Managing tail latency in large scale information retrieval systems / Mackenzie, Joel M. / 2020 via issued / <https://doi.org/10.1145/3451964.3451982>
72. **marcuello2000** (S2.1) - `crossref_doi` -> **DECLARED** - A quantitative assessment of thread-level speculation techniques / Marcuello, P.; Gonzalez, A. / 2000 via declared from event.acronym, container-title.0 / <https://doi.org/10.1109/ipdps.2000.846040>
73. **martinez2004** (S2.1) - `crossref_doi` -> **VERIFIED** - Speculative Locks: Concurrent Execution of Critical Sections in Shared-Memory Multiprocessors / Martínez, José F.; Torrellas, Josep / 2004 via issued / <https://doi.org/10.1007/978-1-4419-8987-1_2>
74. **mehan2026** (S2.5) - `crossref_doi` -> **VERIFIED** - Retry Amplification in Distributed Systems: ASystematic Analysis of Retry Policies and TheirRole in Cascading Failures / Mehan, Rishabh / 2026 via issued / <https://doi.org/10.2139/ssrn.6313332>
75. **memdep2005** (S2.1) - `crossref_doi` -> **VERIFIED** - Exploiting Load/Store Parallelism via Memory Dependence Prediction Andreas Moshovos University of Toronto / (the record carries no author field) / 2005 via issued / <https://doi.org/10.1201/9781420035155-21>
76. **misra2019** (S2.4) - `crossref_doi` -> **VERIFIED** - Managing Tail Latency in Datacenter-Scale File Systems Under Production Constraints / Misra, Pulkit A.; Borge, María F.; Goiri, Íñigo; Lebeck, Alvin R.; Zwaenepoel, Willy; Bianchini, Ricardo / 2019 via issued / <https://doi.org/10.1145/3302424.3303973>
77. **model1997** (S2.7) - `crossref_doi` -> **VERIFIED** - A Model for Speedup of Parallel Programs / Downey, Allen B. / 1997 via issued / <https://doi.org/10.21236/ada637068>
78. **mohanty2024** (S2.3) - `crossref_doi` -> **VERIFIED** - Analysis of Fork-Join Scheduling on Heterogeneous Parallel Servers / Mohanty, Moonmoon; Gautam, Gaurav; Aggarwal, Vaneet; Parag, Parimal / 2024 via issued / <https://doi.org/10.1109/tnet.2024.3432183>
79. **moldable2023** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Improved Online Scheduling of Moldable Task Graphs under Common Speedup Models / Lucas Perotin; Hongyang Sun / 2023 via published / <https://arxiv.org/abs/2304.14127v1>
80. **multiagent2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Competitive Algorithms for Multi-Agent Ski-Rental Problems / Xuchuang Wang; Bo Sun; Hedyeh Beyhaghi; John C. S. Lui; Mohammad Hajiesmaili; Adam Wierman / 2025 via published / <https://arxiv.org/abs/2507.15727v2>
81. **multishop2014** (S2.6) - `crossref_doi` -> **VERIFIED** - The multi-shop ski rental problem / Ai, Lingqing; Wu, Xian; Huang, Lingxiao; Huang, Longbo; Tang, Pingzhong; Li, Jian / 2014 via issued / <https://doi.org/10.1145/2591971.2591984>
82. **newmetric2026** (S2.6) - `crossref_doi` -> **VERIFIED** - A new performance metric for the ski rental problem / Chen, Jonathan; Zhang, Jiawei / 2026 via issued / <https://doi.org/10.1016/j.orl.2025.107382>
83. **nylander2020** (S2.1) - `crossref_doi` -> **VERIFIED** - Towards Performance Modeling of Speculative Execution for Cloud Applications / Nylander, Tommi; Ruuskanen, Johan; Årzén, Karl-Erik; Maggio, Martina / 2020 via issued / <https://doi.org/10.1145/3375555.3384379>
84. **oancea2007** (S2.1) - `crossref_doi` -> **VERIFIED** - A Lightweight Model for Software Thread-Level Speculation (TLS) / Oancea, Cosmin E.; Mycroft, Alan / 2007 via issued / <https://doi.org/10.1109/pact.2007.4336247>
85. **oancea2008** (S2.1) - `crossref_doi` -> **VERIFIED** - Software thread-level speculation / Oancea, Cosmin E.; Mycroft, Alan / 2008 via issued / <https://doi.org/10.1145/1370082.1370090>
86. **oleksenko2019** (S2.1) - `arxiv_id_list` -> **SUPPLIED** - SpecFuzz: Bringing Spectre-type vulnerabilities to the surface / Oleksii Oleksenko; Bohdan Trach; Mark Silberstein; Christof Fetzer / 2019 via published / <https://arxiv.org/abs/1905.10311v4>
87. **oleksenko2023** (S2.1) - `arxiv_id_list` -> **SUPPLIED** - Hide and Seek with Spectres: Efficient discovery of speculative information leaks with random testing / Oleksii Oleksenko; Marco Guarnieri; Boris Köpf; Mark Silberstein / 2023 via published / <https://arxiv.org/abs/2301.07642v1>
88. **onlinegraph2022** (S2.6) - `crossref_doi` -> **VERIFIED** - Online Graph Algorithms with Predictions / Azar, Yossi; Panigrahi, Debmalya; Touitou, Noam / 2022 via issued / <https://doi.org/10.1137/1.9781611977073.3>
89. **optimistic2002** (S2.1) - `crossref_doi` -> **VERIFIED** - Latency Hiding with Optimistic Computations / Hybinette, Maria; Fujimoto, Richard M / 2002 via issued / <https://doi.org/10.1006/jpdc.2001.1801>
90. **pajuelo2004** (S2.1) - `crossref_doi` -> **VERIFIED** - Speculative execution for hiding memory latency / Pajuelo, Alex; González, Antonio; Valero, Mateo / 2004 via issued / <https://doi.org/10.1145/1101868.1101877>
91. **pan2023** (S2.3) - `crossref_doi` -> **VERIFIED** - Refined mean‐field approximation for discrete‐time queueing networks with blocking / Pan, Yang; Shi, Pengyi / 2023 via issued / <https://doi.org/10.1002/nav.22131>
92. **parking2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Primal-Dual Online Algorithms for the Parking Permit Problem / Christian Coester; Alex Turoczy / 2026 via published / <https://arxiv.org/abs/2607.08262v1>
93. **predictionspecific2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Prediction-Specific Design of Learning-Augmented Algorithms / Sizhe Li; Nicolas Christianson; Tongxin Li / 2025 via published / <https://arxiv.org/abs/2510.14887v1>
94. **progressive1993** (S2.5) - `crossref_doi` -> **VERIFIED** - Progressive Retry for Software Error Recovery in Distributed Systems / Wang, Yi-Min; Huang, Yennun; Fuchs, W. K. / 1993 via issued / <https://doi.org/10.21236/ada260075>
95. **raghavan2003** (S2.1) - `crossref_doi` -> **VERIFIED** - Dynamic schemes for speculative execution of code / Raghavan, Prabhakar; Shachnai, Hadas; Yaniv, Mira / 2003 via issued / <https://doi.org/10.1016/s0166-5316(02)00229-8>
96. **redkha2017** (S2.1) - `crossref_doi` -> **VERIFIED** - Big Data Cluster Processing Through Optimized Speculative Execution / Redkha, D. Sasi / 2017 via issued / <https://doi.org/10.18535/ijetst/v4i9.06>
97. **roofline2026** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - CARM Tool: Cache-Aware Roofline Model Automatic Benchmarking and Application Analysis / José Morgado; Leonel Sousa; Aleksandar Ilic / 2026 via published / <https://arxiv.org/abs/2605.29740v1>
98. **schol2019** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Large fork-join queues with nearly deterministic arrival and service times / Dennis Schol; Maria Vlasiou; Bert Zwart / 2019 via published / <https://arxiv.org/abs/1912.11661v3>
99. **schol2022** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Maximum waiting time in heavy-tailed fork-join queues / Dennis Schol; Maria Vlasiou; Bert Zwart / 2022 via published / <https://arxiv.org/abs/2211.02313v1>
100. **schol2023** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Extreme values for the waiting time in large fork-join queues / Dennis Schol; Maria Vlasiou; Bert Zwart / 2023 via published / <https://arxiv.org/abs/2309.08373v1>
101. **servegen2025** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - ServeGen: Workload Characterization and Generation of Large Language Model Serving in Production / Yuxing Xiang; Xue Li; Kun Qian; Wenyuan Yu; Ennan Zhai; Xin Jin / 2025 via published / <https://arxiv.org/abs/2505.09999v3>
102. **sigman1999** (S2.4) - `crossref_doi` -> **VERIFIED** - Appendix: A primer on heavy-tailed distributions / Sigman, Karl / 1999 via issued / <https://doi.org/10.1023/a:1019180230133>
103. **smc2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Speculative Macro Commit for Faster Tool-Using Agents / Zeyu Liu; Souvik Kundu; Peter A. Beerel / 2026 via published / <https://arxiv.org/abs/2609.03236v1>
104. **smoothness2023** (S2.6) - `crossref_doi` -> **VERIFIED** - Discrete-Smoothness in Online Algorithms with Predictions / Azar, Yossi; Panigrahi, Debmalya; Touitou, Noam / 2023 via issued / <https://doi.org/10.52202/075280-1817>
105. **specagents2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Speculative Interaction Agents: Building Real-Time Agents with Asynchronous I/O and Speculative Tool Calling / Coleman Hooper; Minwoo Kang; Suhong Moon; Nicholas Lee; Eric Wen; John Wawrzynek; Michael W. Mahoney; Yakun Sophia Shao; Amir Gholami; Kurt Keutzer / 2026 via published / <https://arxiv.org/abs/2605.13360v2>
106. **specbook2005** (S2.1) - `crossref_doi` -> **VERIFIED** - Speculative Execution in High Performance Computer Architectures / (the record carries no author field) / 2005 via issued / <https://doi.org/10.1201/9781420035155>
107. **specbox2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - SpecBox: Speculative Sandbox Scheduling for Efficient LLM Agent Serving / Yihui Zhang; Tianyu Wo; Jinghao Wang; Xiaoyang Sun; Menghao Zhang; Cangzhou Yuan; Li Li; Chunming Hu; Albert Y. Zomaya; Renyu Yang / 2026 via published / <https://arxiv.org/abs/2607.23933v2>
108. **specgen2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - SpecGen: Accelerating Agentic Kernel Optimization with Speculative Generation / Jihu Guo; Sitian Lu; Tenghui Ma; Wei Gao; Zhisheng Ye; Xingcheng Zhang; Dahua Lin / 2026 via published / <https://arxiv.org/abs/2606.17518v1>
109. **spechop2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - SpecHop: Continuous Speculation for Accelerating Multi-Hop Retrieval Agents / Mehrdad Saberi; Keivan Rezaei; Soheil Feizi / 2026 via published / <https://arxiv.org/abs/2605.21965v1>
110. **speculativecalls2025** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Optimizing Agentic Language Model Inference via Speculative Tool Calls / Daniel Nichols; Prajwal Singhania; Charles Jekel; Abhinav Bhatele; Harshitha Menon / 2025 via published / <https://arxiv.org/abs/2512.15834v1>
111. **speedupdist2024** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Using Sequential Runtime Distributions for the Parallel Speedup Prediction of SAT Local Search / Alejandro Arbelaez; Charlotte Truchet; Philippe Codognet / 2024 via published / <https://arxiv.org/abs/2403.08790v1>
112. **split2026** (S2.4) - `arxiv_id_list` -> **SUPPLIED** - SPLIT: SymPathy for Large jobs Improves Tail latency / Zhouzi Li; Mor Harchol-Balter; Alan Scheller-Wolf / 2026 via published / <https://arxiv.org/abs/2605.13749v1>
113. **spork2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - SPORK: Self-Speculative Forking to Accelerate Agentic LLM Inference / Huajun Bai; Weiwei Lv; Huichuan Zheng; Youyou Lu; Jiwu Shu / 2026 via published / <https://arxiv.org/abs/2607.03333v1>
114. **stats2026** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - How to Do Statistical Evaluations in ECE/CS Papers: A Practical Playbook for Defensible Results / Bhaskar Krishnamachari / 2026 via published / <https://arxiv.org/abs/2605.00428v1>
115. **steffan2000** (S2.1) - `crossref_doi` -> **DECLARED** - A scalable approach to thread-level speculation / Steffan, J.G.; Colohan, C.B.; Zhai, A.; Mowry, T.C. / 2000 via declared from event.acronym, locator / <https://doi.org/10.1109/isca.2000.854372>
116. **superlinear1987** (S2.7) - `crossref_doi` -> **VERIFIED** - A note on superlinear speedup / Janßen, R / 1987 via issued / <https://doi.org/10.1016/0167-8191(87)90053-6>
117. **tailaware2026** (S2.2) - `arxiv_id_list` -> **SUPPLIED** - Decoupling Readiness from Release for Tail-Aware Scheduling of Agentic LLM Workflows / Bochao Feng; Jianjiang Li; Haojie Wang; Lin Qiao; Yinghui Li; Yukun Yan; Jidong Zhai / 2026 via published / <https://arxiv.org/abs/2609.10964v1>
118. **tailawarellm2026** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Beyond Prediction: Tail-Aware Scheduling for LLM Inference / Yueying Li; Yuanfan Chen; Jiayang Chen; Esha Choukse; Haoran Qiu; G. Edward Suh; Rodrigo Fonseca; Ziv Scully; Udit Gupta / 2026 via published / <https://arxiv.org/abs/2606.18431v1>
119. **tmretry2008** (S2.5) - `crossref_doi` -> **VERIFIED** - Transactional memory retry mechanisms / Spear, Michael F.; Sveikauskas, Andrew; Scott, Michael L. / 2008 via issued / <https://doi.org/10.1145/1400751.1400850>
120. **twoslope2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Controlling tail risk in two-slope ski rental / Qiming Cui; Michael Dinitz / 2025 via published / <https://arxiv.org/abs/2508.06809v2>
121. **uht1995** (S2.1) - `crossref_doi` -> **VERIFIED** - Disjoint eager execution: an optimal form of speculative execution / Uht, A.K.; Sindagi, V.; Hall, K. / 1995 via issued / <https://doi.org/10.1109/micro.1995.476841>
122. **unconv2019** (S2.7) - `crossref_doi` -> **VERIFIED** - Unconventional Wisdom: Superlinear Speedup and Inherently Parallel Computations / Akl, Selim G. / 2019 via issued / <https://doi.org/10.1201/9781315167084-16>
123. **util2024** (S2.7) - `crossref_doi` -> **VERIFIED** - Efficient Workload Distribution for Sustainable Server Utilization in Cloud Data Centers / Yadav, Monika; Mishra, Atul / 2024 via issued / <https://doi.org/10.1109/iscs61804.2024.10581223>
124. **variance2023** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Blockwise Stochastic Variance-Reduced Methods with Parallel Speedup for Multi-Block Bilevel Optimization / Quanqi Hu; Zi-Hao Qiu; Zhishuai Guo; Lijun Zhang; Tianbao Yang / 2023 via published / <https://arxiv.org/abs/2305.18730v2>
125. **vectorproc2023** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Vector-Processing for Mobile Devices: Benchmark and Analysis / Alireza Khadem; Daichi Fujiki; Nishil Talati; Scott Mahlke; Reetuparna Das / 2023 via published / <https://arxiv.org/abs/2309.02680v1>
126. **waiting2025** (S2.6) - `arxiv_id_list` -> **SUPPLIED** - Waiting is worth it and can be improved with predictions / Ya-Chun Liang; Meng-Hsi Li; Chung-Shou Liao; Clifford Stein / 2025 via published / <https://arxiv.org/abs/2507.12822v1>
127. **whitt2000** (S2.4) - `crossref_doi` -> **VERIFIED** - The impact of a heavy-tailed service-time distribution upon the M/GI/s waiting-time distribution / Whitt, Ward / 2000 via issued / <https://doi.org/10.1023/a:1019143505968>
128. **workload2015** (S2.7) - `crossref_doi` -> **VERIFIED** - Locality Exists in Graph Processing: Workload Characterization on an Ivy Bridge Server / Beamer, Scott; Asanovic, Krste; Patterson, David / 2015 via issued / <https://doi.org/10.1109/iiswc.2015.12>
129. **workload2017** (S2.7) - `crossref_doi` -> **VERIFIED** - Workload characterization of interactive cloud services on big and small server platforms / Chen, Shuang; GalOn, Shay; Delimitrou, Christina; Manne, Srilatha; Martinez, Jose F. / 2017 via issued / <https://doi.org/10.1109/iiswc.2017.8167770>
130. **workload2024** (S2.7) - `arxiv_id_list` -> **SUPPLIED** - Towards Cloud Efficiency with Large-scale Workload Characterization / Anjaly Parayil; Jue Zhang; Xiaoting Qin; Íñigo Goiri; Lexiang Huang; Timothy Zhu; Chetan Bansal / 2024 via published / <https://arxiv.org/abs/2405.07250v1>
131. **ye2020** (S2.1) - `crossref_doi` -> **VERIFIED** - Speculative Data-Oblivious Execution: Mobilizing Safe Prediction For Safe and Efficient Speculative Execution / Yu, Jiyong; Mantri, Namrata; Torrellas, Josep; Morrison, Adam; Fletcher, Christopher W. / 2020 via issued / <https://doi.org/10.1109/isca45697.2020.00064>
132. **zhao2012** (S2.1) - `crossref_doi` -> **VERIFIED** - Hiding I/O Latency with Parallel Pre-Execution Prefetching / Zhao, Yue; Yoshigoe, Kenji / 2012 via issued / <https://doi.org/10.2316/p.2012.789-015>
133. **zhou2021layered** (S2.3) - `crossref_doi` -> **DECLARED** - A New Approximation for Multiserver Waiting Time, for Layered Queueing Systems / Zhou, Siyu / 2021 via declared from locator / <https://doi.org/10.22215/etd/2021-14846>
134. **zhu2026** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Queues with Correlated Service Times -- the $M/M_D/c$ Model / Qihui Bu; Suman Thapa; Yiqiang Q. Zhao / 2026 via published / <https://arxiv.org/abs/2606.24881v1>
135. **zuk2023** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Exact Results for the Distribution of the Partial Busy Period for a Multi-Server Queue / Josef Zuk; David Kirszenblat / 2023 via published / <https://arxiv.org/abs/2309.01874v1>
136. **zuk2023b** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Joint Queue-Length Distribution for the Non-Preemptive Multi-Server Multi-Level Markovian Priority Queue / Josef Zuk; David Kirszenblat / 2023 via published / <https://arxiv.org/abs/2311.01641v1>
137. **zuk2023c** (S2.3) - `arxiv_id_list` -> **SUPPLIED** - Explicit Results for the Distributions of Queue Lengths for a Non-Preemptive Two-Level Priority Queue / Josef Zuk; David Kirszenblat / 2023 via published / <https://arxiv.org/abs/2309.09428v1>

## Declared years

These rows print a year the record does not carry. The declaration is not trusted: every
source it names is re-read from the live record at build time, and a row with neither a
record year nor a backed declaration refuses the build.

- **anotherview1990** -> 1990, backed by `event.name` = SUPERCOMPUTING '90, `locator` = 10.1109/superc.1990.130037 - issued is [[null]] and no published-* field is present; the event name and the locator both carry the year
- **marcuello2000** -> 2000, backed by `event.acronym` = IPDPS-00, `container-title.0` = Proceedings 14th International Parallel and Distributed Processing Symposium. IPDPS 2000 - issued is [[null]] and no published-* field is present; the container title and the event acronym both name the year
- **steffan2000** -> 2000, backed by `event.acronym` = ISCA-00, `locator` = 10.1109/isca.2000.854372 - issued is [[null]] and no published-* field is present; the event the record names carries the year in its acronym
- **zhou2021layered** -> 2021, backed by `locator` = 10.22215/etd/2021-14846 - a dissertation: the record carries no publication date, no container and no event, so the locator's own year segment is the only reading - ONE SOURCE, and it is stated rather than multiplied

## Records that are themselves odd, and what the entry prints

4 of 137 records carry **no author field**: fixedsize2011, idempotency2025, memdep2005, specbook2005. The bibliography prints such an entry without
an author, which is what the record says; it is not padded with an invented one.

The record for `memdep2005` carries its own title field **polluted**: it reads
`Exploiting Load/Store Parallelism via Memory Dependence Prediction Andreas Moshovos
University of Toronto`, with the chapter author and affiliation appended and no author
field of its own. The entry prints the record's title as the record carries it; the
defect is named here rather than repaired silently.

## Declarations applied to the bibliography, and why they are readings

Two entries do not print their record's fields verbatim. Neither is a hand correction:
each names a property of the record that `refs_build_display.py` re-checks at build time,
and a declaration that fails its property fails the build.

- **title** (1 entr(y/ies)): the entry prints a title the record's own
  title field carries as a **prefix**.
  - `memdep2005`: the record's title field is the chapter title followed by the chapter's author and affiliation: 'Exploiting Load/Store Parallelism via Memory Dependence Prediction Andreas Moshovos University of Toronto' (evidence: record_title prefix; the record carries no author field of its own)
- **author** (1 entr(y/ies)): the record printed the author's two name
  fields **transposed**, and swapping them back reproduces the declared author after case
  and punctuation folding.
  - `linearspeedup2005`: the entry prints Grigoriev, A.; Uetz, M. J. -- the record states its two name fields the wrong way round: it reads `A., Grigoriev` and `M.J., Uetz`, i.e. the family field carries the given name

## The journal's reference gate, as run

Copy run: `../../.github/tools/refgate.py` at this working tree -- **761 line(s), sha256 `4e460be9a526fc90...`, its own `--selftest` reports selftest: 40/40 cases ok**.
The gate reads the last `## References` heading to the end of the file, so the section
below is the object it judged. Invoked as the package's own reader invokes it (from this
directory, on the manuscript's basename), so the name it prints is the name this report
quotes.

```
=== manuscript.md
  window: the last `## References` heading (line 992) to the end of the file (line 1746)
          — its numbered lines are read as entries
  entries=137  numbering=[n]
  block form: 137 entries, 0 of them not separated from the entry above by a blank line — consecutive entry lines are ONE paragraph to a CommonMark renderer (GitHub's preview included); read the page, not the source
  author form: 133/137 entry(s) carry the read's window (a family name, a comma, an initial — or a lone family name before the year); 0 print the family name ALL-CAPS, 0 carry a character reference (&…;) — a record's stored field is not the form an entry prints
  in-text cited numbers=137  covered=137/137  coverage=100.0%
  GATE: PASS
```

## What this does not establish

- It does not establish that the selected work **supports the sentence** that cites it.
  This check answers *is the record real and is it the work the entry names*. The
  citation-to-claim relation is a separate read and is carried by the manuscript's own
  checker.
- It does not establish that the record's own metadata is right. A record whose title
  field is polluted is reported as found, not repaired.
- The two runs shown byte-identical ran on one machine on one day. The read depends on
  the endpoints' current contents; a later run of the same instrument on the same rows
  is what re-establishes it.
- A verified row's year is the year of the version the **locator** names. Where a work
  exists in a preprint and a published version, the entry cites and dates the version the
  locator resolves to.

## Invariants checked on this reading

- `VERIFIED` rows whose stored year differs from the verified year: 0 of 137
- every row's `anchor` is carried by its record: 137 of 137
- every row's title matches its record exactly: 137 of 137
- every row shares at least one family name with its record (where either side names
  one): 137 of 137
- keys whose own trailing year contradicts the record: 0 of 137

## What the first pass of this instrument got wrong

Four defects, all found by reading the data rather than by a control, all recorded:

1. **The arXiv read did not state `max_results`.** It truncated every batch to 10
   entries and reported 33 of 66 ids as having no record - and the known-present control
   passed in every batch, because it fell inside the window either way. A control only
   detects the failures that can remove it; the fix reads the **count** as well.
2. **The family-name reader was written for one printed form and stated as if it read
   both.** Crossref prints the family first (`Steffan, J.G.`), arXiv last (`Cosmin E.
   Oancea`); the reader took the last token for both, reading every Crossref family as
   initials. The selftest case for the Crossref form caught it.
3. **The year reader preferred the issue date over the publication date**, which
   reported three correct entries (`improved2025`, `ji2024`, `pajuelo2004`) as defects:
   for `10.1145/3763239` it read `published-print` = 2026-01-31 (the issue) rather than
   `issued` = 2025-11-10 (the publication). The selftest case for this encoded the wrong
   rule and passed - a test that encodes the author's assumption certifies the
   assumption. What caught it was dumping **every** date field for each mismatch instead
   of accepting the mismatch as a citation defect.
4. **Eight of 137 keys carried a year the record contradicts** (and five, an author who
   is not on the record at all). The keys were authored by hand and nothing read them
   against the record. They are renamed to agree with the record, the renames and their
   reasons are recorded in `refs_selection_v50.json` (`renamed_at_r379`), and the
   agreement is now a hard check that fails the row.

A fifth defect is in the layer this check verifies, not in the check: the selection read
`year`, a field only the Crossref channel carries, and printed `null` for all 66 arXiv
rows, whose date lives in `published` (553 of 553 arXiv pool records carry it). Reported
here as data, not as an error.

