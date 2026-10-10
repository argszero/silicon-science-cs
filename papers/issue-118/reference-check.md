# Citation report - issue #118

Companion to `manuscript.md`. Two duties: (i) **authenticity** of every reference, and
(ii) **coverage** of the in-text citation keys. This report is a declaration; reviewers
verify independently. It is **generated** by `refs/refs_report.py` from the two committed
artefacts, and `reproduce.sh` requires the committed file to equal the generator's output
byte for byte -- so no number here can have been typed by hand and survived a run.

## (i) Authenticity - how the entries were verified

**Method.** Verification is a different act from discovery and from curation, and it lives
in a different file: `refs/refs_tool.py` re-fetches **each curated entry by its own
identifier** from the index that owns that identifier (arXiv, `id_list=<id>`) and compares
the returned title to the title recorded for that key, after normalisation (case,
punctuation and whitespace folded).

```
python3 refs/refs_tool.py verify     # re-fetches and re-writes refs/verify.log
python3 refs/refs_tool.py plant      # two-sided control on a throwaway copy
```

**Result: entries=105  resolved=105  problems=0.** The command exits non-zero if any
entry fails, so this is a check rather than a statement. The generator additionally asserts
that the log and the curated set name the *same* identifiers in both directions and that
every returned title normalises to the curated one.

| artefact | what it is | sha256 |
|---|---|---|
| `refs/verify.log` | the verifier's own output (105 lines) | `256931ab53095588a58050e9ac2d2e63df79a3002f15e86ac5db45bcce337e4a` |
| `refs/curated.json` | the curated set, with the role and the stated difference of each entry | `d1583a061ad88ec0d565d2c6ae6199b0b837a62d8a0af5544b6bda4be5ce2b16` |
| `refs/authors.json` | the author names as the 105 records state them, captured in the same fetch that resolved each title | `55076fa78cf6d9627b4ecf9facf14772b5bab4c214290572fbcac284b964d931` |

## (i-b) The author component of every entry

The entry style is a test over **every** entry, and the author component is part of it.
It is **read from the record**, never typed: the verifier captures it in the same request
that resolves the title (`refs_tool.py`), so the author is evidence about the record the
title check is evidence about, rather than a second, later claim about it.

| carrier | what it returns | the order it states |
|---|---|---|
| arXiv API (`export.arxiv.org/api/query?id_list=`) | one `<author><name>` per author | `Given Family` |

The printed form is `Family, I.` -- initials taken from the given names, a hyphenated given
name taking one initial per part (`Maria-Florina Balcan` -> `Balcan, M. F.`); **four or more**
authors print the first three then `; et al.`; a record giving **one token and no more** prints
that token alone, never padded to `Family, I.`. The **raw string the record returned is kept
beside the printed one** in the table below, so the split is an auditable derivation rather
than a claim. Where a record carried none the renderer prints a sentence naming the gap and
the identifier instead of leaving the position empty; no entry here takes that branch.

The editor's own read of the rendered list is the journal gate -- run from a checkout of the
repository, over the product rather than the source:

```
python3 .github/tools/refgate.py papers/issue-118/manuscript.md
```

Its `author form:` and `block form:` lines are the two readings this component exists to
satisfy; they are quoted by the editor at triage, not reproduced here, because a log line
copied into a generated file is a typed number the moment the gate changes.

**Two-sided controls** (`refs_tool.py plant`, against a throwaway copy; the committed
artefact is never mutated). A verifier that cannot fail is decoration, so both plants must
be caught and the command exits non-zero if either escapes:

| control | expected | observed |
|---|---|---|
| one title replaced by a different paper's title | fail | exit 1, `MISMATCH`, both strings named |
| one invented identifier (`9999.99999`) | fail | exit 1, `UNRESOLVED` for that identifier |

## (ii) Coverage of the in-text keys

The manuscript cites `[[identifier]]`, never a number: a literal `[N]` in the body would
re-point the moment the list is renumbered, so the body carries identifiers and the numbers
are assigned at build time by `refs/refs_build.py`.

| quantity | value |
|---|---|
| curated entries | 105 |
| cited in the body | 105 |
| curated but never cited | 0 |
| cited but not curated | 0 |
| journal floor | 100 |

`refs/refs_build.py check` is the command that produces those four numbers; it also scans
the body for a literal `[N]`, which must be found zero times. The generator asserts them
independently, over the same inputs.

## (iv) The entries, by role

### The construct: capacity, dropping, and the routing discipline (12)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2005.07761` | OK | Efficient Load-Balancing through Distributed Token Dropping | 2020-05-15 | Sebastian Brandt<br>Barbara Keller<br>Joel Rybicki<br>(+2 more) | Brandt, S.; Keller, B.; Rybicki, J.; et al. |
| `2006.16668` | OK | GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding | 2020-06-30 | Dmitry Lepikhin<br>HyoukJoong Lee<br>Yuanzhong Xu<br>(+6 more) | Lepikhin, D.; Lee, H.; Xu, Y.; et al. |
| `2010.11018` | OK | Token Drop mechanism for Neural Machine Translation | 2020-10-21 | Huaao Zhang<br>Shigui Qiu<br>Xiangyu Duan<br>(+1 more) | Zhang, H.; Qiu, S.; Duan, X.; et al. |
| `2101.03961` | OK | Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity | 2021-01-11 | William Fedus<br>Barret Zoph<br>Noam Shazeer | Fedus, W.; Zoph, B.; Shazeer, N. |
| `2105.15082` | OK | M6-T: Exploring Sparse Expert Models and Beyond | 2021-05-31 | An Yang<br>Junyang Lin<br>Rui Men<br>(+12 more) | Yang, A.; Lin, J.; Men, R.; et al. |
| `2106.04426` | OK | Hash Layers For Large Sparse Models | 2021-06-08 | Stephen Roller<br>Sainbayar Sukhbaatar<br>Arthur Szlam<br>(+1 more) | Roller, S.; Sukhbaatar, S.; Szlam, A.; et al. |
| `2112.06905` | OK | GLaM: Efficient Scaling of Language Models with Mixture-of-Experts | 2021-12-13 | Nan Du<br>Yanping Huang<br>Andrew M. Dai<br>(+24 more) | Du, N.; Huang, Y.; Dai, A. M.; et al. |
| `2202.09368` | OK | Mixture-of-Experts with Expert Choice Routing | 2022-02-18 | Yanqi Zhou<br>Tao Lei<br>Hanxiao Liu<br>(+7 more) | Zhou, Y.; Lei, T.; Liu, H.; et al. |
| `2203.13240` | OK | Token Dropping for Efficient BERT Pretraining | 2022-03-24 | Le Hou<br>Richard Yuanzhe Pang<br>Tianyi Zhou<br>(+4 more) | Hou, L.; Pang, R. Y.; Zhou, T.; et al. |
| `2211.11586` | OK | Random-LTD: Random and Layerwise Token Dropping Brings Efficient Training for Large-scale Transformers | 2022-11-17 | Zhewei Yao<br>Xiaoxia Wu<br>Conglong Li<br>(+4 more) | Yao, Z.; Wu, X.; Li, C.; et al. |
| `2308.00951` | OK | From Sparse to Soft Mixtures of Experts | 2023-08-02 | Joan Puigcerver<br>Carlos Riquelme<br>Basil Mustafa<br>(+1 more) | Puigcerver, J.; Riquelme, C.; Mustafa, B.; et al. |
| `2508.12801` | OK | Maximum Score Routing For Mixture-of-Experts | 2025-08-18 | Bowen Dong<br>Yilong Fan<br>Yutao Sun<br>(+4 more) | Dong, B.; Fan, Y.; Sun, Y.; et al. |

### Load balancing: the field's standard remedy (8)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2109.11817` | OK | Unbiased Gradient Estimation with Balanced Assignments for Mixtures of Experts | 2021-09-24 | Wouter Kool<br>Chris J. Maddison<br>Andriy Mnih | Kool, W.; Maddison, C. J.; Mnih, A. |
| `2408.15664` | OK | Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts | 2024-08-28 | Lean Wang<br>Huazuo Gao<br>Chenggang Zhao<br>(+2 more) | Wang, L.; Gao, H.; Zhao, C.; et al. |
| `2411.19402` | OK | On the Role of Discrete Representation in Sparse Mixture of Experts | 2024-11-28 | Giang Do<br>Kha Pham<br>Hung Le<br>(+1 more) | Do, G.; Pham, K.; Le, H.; et al. |
| `2502.15451` | OK | Binary-Integer-Programming Based Algorithm for Expert Load Balancing in Mixture-of-Experts Models | 2025-02-21 | Yuan Sun | Sun, Y. |
| `2504.01337` | OK | Advancing MoE Efficiency: A Collaboration-Constrained Routing (C2R) Strategy for Better Expert Parallelism Design | 2025-04-02 | Mohan Zhang<br>Pingzhi Li<br>Jie Peng<br>(+2 more) | Zhang, M.; Li, P.; Peng, J.; et al. |
| `2512.03915` | OK | A Theoretical Framework for Auxiliary-Loss-Free Load Balancing of Sparse Mixture-of-Experts in Large-Scale AI Models | 2025-12-03 | X. Y. Han<br>Yuan Zhong | Han, X. Y.; Zhong, Y. |
| `2602.03478` | OK | When Routing Collapses: On the Degenerate Convergence of LLM Routers | 2026-02-03 | Guannan Lai<br>Han-Jia Ye | Lai, G.; Ye, H. J. |
| `2602.14159` | OK | Synergistic Intra- and Cross-Layer Regularization Losses for MoE Expert Specialization | 2026-02-15 | Rizhen Hu<br>Yuan Cao<br>Boao Kong<br>(+2 more) | Hu, R.; Cao, Y.; Kong, B.; et al. |

### Capacity and the straggler effect (3)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2403.07652` | OK | Harder Tasks Need More Experts: Dynamic Routing in MoE Models | 2024-03-12 | Quzhe Huang<br>Zhenwei An<br>Nan Zhuang<br>(+8 more) | Huang, Q.; An, Z.; Zhuang, N.; et al. |
| `2502.16927` | OK | BigMac: A Communication-Efficient Mixture-of-Experts Model Structure for Fast Training and Inference | 2025-02-24 | Zewen Jin<br>Shengnan Wang<br>Jiaan Zhu<br>(+5 more) | Jin, Z.; Wang, S.; Zhu, J.; et al. |
| `2503.05066` | OK | Capacity-Aware Inference: Mitigating the Straggler Effect in Mixture of Experts | 2025-03-07 | Shwai He<br>Weilin Cai<br>Jiayi Huang<br>(+1 more) | He, S.; Cai, W.; Huang, J.; et al. |

### Inference serving: the decode regime (27)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2201.05596` | OK | DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training to Power Next-Generation AI Scale | 2022-01-14 | Samyam Rajbhandari<br>Conglong Li<br>Zhewei Yao<br>(+5 more) | Rajbhandari, S.; Li, C.; Yao, Z.; et al. |
| `2308.12066` | OK | Pre-gated MoE: An Algorithm-System Co-Design for Fast and Scalable Mixture-of-Expert Inference | 2023-08-23 | Ranggi Hwang<br>Jianyu Wei<br>Shijie Cao<br>(+4 more) | Hwang, R.; Wei, J.; Cao, S.; et al. |
| `2308.15030` | OK | SwapMoE: Serving Off-the-shelf MoE-based Large Language Models with Tunable Memory Budget | 2023-08-29 | Rui Kong<br>Yuanchun Li<br>Qingtian Feng<br>(+5 more) | Kong, R.; Li, Y.; Feng, Q.; et al. |
| `2401.14361` | OK | MoE-Infinity: Efficient MoE Inference on Personal Machines with Sparsity-Aware Expert Cache | 2024-01-25 | Leyang Xue<br>Yao Fu<br>Zhan Lu<br>(+2 more) | Xue, L.; Fu, Y.; Lu, Z.; et al. |
| `2410.17954` | OK | ExpertFlow: Efficient Mixture-of-Experts Inference via Predictive Expert Caching and Token Scheduling | 2024-10-23 | Xin He<br>Shunkang Zhang<br>Kaijie Tang<br>(+8 more) | He, X.; Zhang, S.; Tang, K.; et al. |
| `2411.01433` | OK | HOBBIT: A Mixed Precision Expert Offloading System for Fast MoE Inference | 2024-11-03 | Peng Tang<br>Jiacheng Liu<br>Xiaofeng Hou<br>(+5 more) | Tang, P.; Liu, J.; Hou, X.; et al. |
| `2501.10375` | OK | DAOP: Data-Aware Offloading and Predictive Pre-Calculation for Efficient MoE Inference | 2024-12-16 | Yujie Zhang<br>Shivam Aggarwal<br>Tulika Mitra | Zhang, Y.; Aggarwal, S.; Mitra, T. |
| `2502.05370` | OK | Taming Latency-Memory Trade-Off in MoE-Based LLM Serving via Fine-Grained Expert Offloading | 2025-02-07 | Hanfei Yu<br>Xingqi Cui<br>Hong Zhang<br>(+2 more) | Yu, H.; Cui, X.; Zhang, H.; et al. |
| `2502.06888` | OK | Klotski: Efficient Mixture-of-Expert Inference via Expert-Aware Multi-Batch Pipeline | 2025-02-09 | Zhiyuan Fang<br>Yuegui Huang<br>Zicong Hong<br>(+5 more) | Fang, Z.; Huang, Y.; Hong, Z.; et al. |
| `2502.12224` | OK | Fate: Fast Edge Inference of Mixture-of-Experts Models via Cross-Layer Gate | 2025-02-17 | Zhiyuan Fang<br>Zicong Hong<br>Yuegui Huang<br>(+5 more) | Fang, Z.; Hong, Z.; Huang, Y.; et al. |
| `2504.02263` | OK | MegaScale-Infer: Serving Mixture-of-Experts at Scale with Disaggregated Expert Parallelism | 2025-04-03 | Ruidong Zhu<br>Ziheng Jiang<br>Chao Jin<br>(+17 more) | Zhu, R.; Jiang, Z.; Jin, C.; et al. |
| `2504.05897` | OK | HybriMoE: Hybrid CPU-GPU Scheduling and Cache Management for Efficient MoE Inference | 2025-04-08 | Shuzhang Zhong<br>Yanfan Sun<br>Ling Liang<br>(+3 more) | Zhong, S.; Sun, Y.; Liang, L.; et al. |
| `2505.16056` | OK | Not All Models Suit Expert Offloading: On Local Routing Consistency of Mixture-of-Expert Models | 2025-05-21 | Jingcong Liang<br>Siyuan Wang<br>Miren Tian<br>(+3 more) | Liang, J.; Wang, S.; Tian, M.; et al. |
| `2506.12708` | OK | Serving Large Language Models on Huawei CloudMatrix384 | 2025-06-15 | Pengfei Zuo<br>Huimin Lin<br>Junbo Deng<br>(+43 more) | Zuo, P.; Lin, H.; Deng, J.; et al. |
| `2508.09208` | OK | CoMoE: Collaborative Optimization of Expert Aggregation and Offloading for MoE-based LLMs at Edge | 2025-08-10 | Muqing Li<br>Ning Li<br>Xin Yuan<br>(+4 more) | Li, M.; Li, N.; Yuan, X.; et al. |
| `2508.18983` | OK | SMoE: An Algorithm-System Co-Design for Pushing MoE to the Edge via Expert Substitution | 2025-08-26 | Guoying Zhu<br>Meng Li<br>Haipeng Dai<br>(+6 more) | Zhu, G.; Li, M.; Dai, H.; et al. |
| `2508.19373` | OK | HAP: Hybrid Adaptive Parallelism for Efficient Mixture-of-Experts Inference | 2025-08-26 | Haoran Lin<br>Xianzhi Yu<br>Kang Zhao<br>(+7 more) | Lin, H.; Yu, X.; Zhao, K.; et al. |
| `2512.12990` | OK | SliceMoE: Bit-Sliced Expert Caching under Miss-Rate Constraints for Efficient MoE Inference | 2025-12-15 | Yuseon Choi<br>Sangjin Kim<br>Jungjun Oh<br>(+3 more) | Choi, Y.; Kim, S.; Oh, J.; et al. |
| `2601.05296` | OK | MoEBlaze: Breaking the Memory Wall for Efficient MoE Training on Modern GPUs | 2026-01-08 | Jiyuan Zhang<br>Yining Liu<br>Siqi Yan<br>(+6 more) | Zhang, J.; Liu, Y.; Yan, S.; et al. |
| `2602.16052` | OK | MoE-Spec: Expert Budgeting for Efficient Speculative Decoding | 2026-02-17 | Bradley McDanel<br>Steven Li<br>Sruthikesh Surineni<br>(+1 more) | McDanel, B.; Li, S.; Surineni, S.; et al. |
| `2603.06350` | OK | MoEless: Efficient MoE LLM Serving with Serverless Experts | 2026-03-06 | Hanfei Yu<br>Bei Ouyang<br>Shwai He<br>(+2 more) | Yu, H.; Ouyang, B.; He, S.; et al. |
| `2604.18788` | OK | Efficient Mixture-of-Experts LLM Inference with Apple Silicon NPUs | 2026-04-20 | Afsara Benazir<br>Felix Xiaozhu Lin | Benazir, A.; Lin, F. X. |
| `2604.23150` | OK | Scaling Multi-Node Mixture-of-Experts Inference Using Expert Activation Patterns | 2026-04-25 | Abhimanyu Bambhaniya<br>Geonhwa Jeong<br>Jason Park<br>(+6 more) | Bambhaniya, A.; Jeong, G.; Park, J.; et al. |
| `2605.10670` | OK | Surviving Partial Rank Failures in Wide Expert-Parallel MoE Inference | 2026-05-11 | Xun Sun<br>Shaoyuan Chen<br>Pingchuan Ma<br>(+18 more) | Sun, X.; Chen, S.; Ma, P.; et al. |
| `2609.33385` | OK | OLED-MoE: Accelerating MoE-Based dLLM Inference via Inter-Iteration Locality-Aware Expert Offloading | 2026-09-27 | Jingyuan Xiao<br>Jiayue Wang<br>Yitao Hu<br>(+7 more) | Xiao, J.; Wang, J.; Hu, Y.; et al. |
| `2610.01265` | OK | RapidMoE: Exploiting Cross-Asymmetry via Adaptive Residual Offloading for Large-Scale MoE Inference | 2026-10-01 | Wenxun Wang<br>Likai Ma<br>Zongle Huang<br>(+2 more) | Wang, W.; Ma, L.; Huang, Z.; et al. |
| `2610.01950` | OK | MoE-CORE: Coordinated Expert Offloading and Residency for Memory-Constrained MoE Inference | 2026-10-01 | Ke Yang<br>Yongji Gao<br>Xushi Li<br>(+16 more) | Yang, K.; Gao, Y.; Li, X.; et al. |

### Named architectures (14)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2401.04088` | OK | Mixtral of Experts | 2024-01-08 | Albert Q. Jiang<br>Alexandre Sablayrolles<br>Antoine Roux<br>(+23 more) | Jiang, A. Q.; Sablayrolles, A.; Roux, A.; et al. |
| `2401.06066` | OK | DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models | 2024-01-11 | Damai Dai<br>Chengqi Deng<br>Chenggang Zhao<br>(+14 more) | Dai, D.; Deng, C.; Zhao, C.; et al. |
| `2405.04434` | OK | DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model | 2024-05-07 | DeepSeek-AI<br>Aixin Liu<br>Bei Feng<br>(+154 more) | DeepSeek-AI; Liu, A.; Feng, B.; et al. |
| `2406.00023` | OK | Expert-Token Resonance MoE: Bidirectional Routing with Efficiency Affinity-Driven Active Selection | 2024-05-24 | Jing Li<br>Zhijie Sun<br>Dachao Lin<br>(+5 more) | Li, J.; Sun, Z.; Lin, D.; et al. |
| `2406.13233` | OK | AdaMoE: Token-Adaptive Routing with Null Experts for Mixture-of-Experts Language Models | 2024-06-19 | Zihao Zeng<br>Yibo Miao<br>Hongcheng Gao<br>(+2 more) | Zeng, Z.; Miao, Y.; Gao, H.; et al. |
| `2407.10671` | OK | Qwen2 Technical Report | 2024-07-15 | An Yang<br>Baosong Yang<br>Binyuan Hui<br>(+59 more) | Yang, A.; Yang, B.; Hui, B.; et al. |
| `2409.02060` | OK | OLMoE: Open Mixture-of-Experts Language Models | 2024-09-03 | Niklas Muennighoff<br>Luca Soldaini<br>Dirk Groeneveld<br>(+21 more) | Muennighoff, N.; Soldaini, L.; Groeneveld, D.; et al. |
| `2410.10456` | OK | Ada-K Routing: Boosting the Efficiency of MoE-based LLMs | 2024-10-14 | Tongtian Yue<br>Longteng Guo<br>Jie Cheng<br>(+2 more) | Yue, T.; Guo, L.; Cheng, J.; et al. |
| `2412.10302` | OK | DeepSeek-VL2: Mixture-of-Experts Vision-Language Models for Advanced Multimodal Understanding | 2024-12-13 | Zhiyu Wu<br>Xiaokang Chen<br>Zizheng Pan<br>(+24 more) | Wu, Z.; Chen, X.; Pan, Z.; et al. |
| `2412.19437` | OK | DeepSeek-V3 Technical Report | 2024-12-27 | DeepSeek-AI<br>Aixin Liu<br>Bei Feng<br>(+197 more) | DeepSeek-AI; Liu, A.; Feng, B.; et al. |
| `2503.15798` | OK | Mixture of Lookup Experts | 2025-03-20 | Shibo Jie<br>Yehui Tang<br>Kai Han<br>(+4 more) | Jie, S.; Tang, Y.; Han, K.; et al. |
| `2505.22323` | OK | Advancing Expert Specialization for Better MoE | 2025-05-28 | Hongcan Guo<br>Haolang Lu<br>Guoshun Nan<br>(+8 more) | Guo, H.; Lu, H.; Nan, G.; et al. |
| `2604.12163` | OK | Nucleus-Image: Sparse MoE for Image Generation | 2026-04-14 | Chandan Akiti<br>Ajay Modukuri<br>Murali Nandan Nagarapu<br>(+2 more) | Akiti, C.; Modukuri, A.; Nagarapu, M. N.; et al. |
| `2608.17402` | OK | MoE-ViE: Mixture of Experts Vision Encoder for Efficient Image and Video Understanding | 2026-08-18 | Bonan Zhang<br>Shiyu Dong<br>Quan Hung Tran<br>(+9 more) | Zhang, B.; Dong, S.; Tran, Q. H.; et al. |

### Efficiency and systems adjacency (9)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2206.00277` | OK | Task-Specific Expert Pruning for Sparse Mixture-of-Experts | 2022-06-01 | Tianyu Chen<br>Shaohan Huang<br>Yuan Xie<br>(+5 more) | Chen, T.; Huang, S.; Xie, Y.; et al. |
| `2404.05019` | OK | Shortcut-connected Expert Parallelism for Accelerating Mixture-of-Experts | 2024-04-07 | Weilin Cai<br>Juyong Jiang<br>Le Qin<br>(+3 more) | Cai, W.; Jiang, J.; Qin, L.; et al. |
| `2407.04656` | OK | Lazarus: Resilient and Elastic Training of Mixture-of-Experts Models | 2024-07-05 | Yongji Wu<br>Wenjie Qu<br>Xueshen Liu<br>(+10 more) | Wu, Y.; Qu, W.; Liu, X.; et al. |
| `2411.15419` | OK | Communication-Efficient Sparsely-Activated Model Training via Sequence Migration and Token Condensation | 2024-11-23 | Fahao Chen<br>Peng Li<br>Zicong Hong<br>(+2 more) | Chen, F.; Li, P.; Hong, Z.; et al. |
| `2411.16786` | OK | Staleness-Centric Optimizations for Parallel Diffusion MoE Inference | 2024-11-25 | Jiajun Luo<br>Lizhuo Luo<br>Jianru Xu<br>(+4 more) | Luo, J.; Luo, L.; Xu, J.; et al. |
| `2503.06881` | OK | ResMoE: Space-efficient Compression of Mixture of Experts LLMs via Residual Restoration | 2025-03-10 | Mengting Ai<br>Tianxin Wei<br>Yifan Chen<br>(+7 more) | Ai, M.; Wei, T.; Chen, Y.; et al. |
| `2504.14960` | OK | MoE Parallel Folding: Heterogeneous Parallelism Mappings for Efficient Large-Scale MoE Model Training with Megatron Core | 2025-04-21 | Dennis Liu<br>Zijie Yan<br>Xin Yao<br>(+15 more) | Liu, D.; Yan, Z.; Yao, X.; et al. |
| `2506.23635` | OK | Towards Building Private LLMs: Exploring Multi-Node Expert Parallelism on Apple Silicon for Mixture-of-Experts Large Language Model | 2025-06-30 | Mu-Chi Chen<br>Po-Hsuan Huang<br>Xiangrui Ke<br>(+3 more) | Chen, M. C.; Huang, P. H.; Ke, X.; et al. |
| `2608.28511` | OK | Training Communication-Efficient Mixture-of-Experts Language Models with Layer Re-Configuration | 2026-08-28 | Simeng Sun<br>Roger Waleffe | Sun, S.; Waleffe, R. |

### Capacity overflow as an attack surface (4)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2410.22884` | OK | Stealing User Prompts from Mixture of Experts | 2024-10-30 | Itay Yona<br>Ilia Shumailov<br>Jamie Hayes<br>(+1 more) | Yona, I.; Shumailov, I.; Hayes, J.; et al. |
| `2504.18598` | OK | BadMoE: Backdooring Mixture-of-Experts LLMs via Optimizing Routing Triggers and Infecting Dormant Experts | 2025-04-24 | Qingyue Wang<br>Qi Pang<br>Xixun Lin<br>(+2 more) | Wang, Q.; Pang, Q.; Lin, X.; et al. |
| `2510.13462` | OK | Who Speaks for the Trigger? Dynamic Expert Routing in Backdoored Mixture-of-Experts Transformers | 2025-10-15 | Xin Zhao<br>Xiaojun Chen<br>Bingshan Liu<br>(+3 more) | Zhao, X.; Chen, X.; Liu, B.; et al. |
| `2608.25371` | OK | Capacity Overflow: A Blind Spot for Backdoor Attacks in Vision MoE | 2026-08-26 | Xiaocheng Zou<br>Tiancheng Zheng<br>Xiaolin Xu<br>(+1 more) | Zou, X.; Zheng, T.; Xu, X.; et al. |

### Surveys and the design space (5)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `2602.03204` | OK | Sparsity is Combinatorial Depth: Quantifying MoE Expressivity via Tropical Geometry | 2026-02-03 | Ye Su<br>Huayi Tang<br>Zixuan Gong<br>(+1 more) | Su, Y.; Tang, H.; Gong, Z.; et al. |
| `2602.17798` | OK | Grassmannian Mixture-of-Experts: Concentration-Controlled Routing on Subspace Manifolds | 2026-02-19 | Ibne Farabi Shihab<br>Sanjeda Akter<br>Anuj Sharma | Shihab, I. F.; Akter, S.; Sharma, A. |
| `2603.11114` | OK | Task-Conditioned Routing Signatures in Sparse Mixture-of-Experts Transformers | 2026-03-11 | Mynampati Sri Ranganadha Avinash | Avinash, M. S. R. |
| `2605.11689` | OK | Slicing and Dicing: Configuring Optimal Mixtures of Experts | 2026-05-12 | Margaret Li<br>Sneha Kudugunta<br>Danielle Rothermel<br>(+1 more) | Li, M.; Kudugunta, S.; Rothermel, D.; et al. |
| `2608.08650` | OK | The Evolution of Mixture-of-Experts Architectures in Large Language Models: Routing, Topology, Load Balancing, and Expert Parallelism | 2026-08-09 | Jiguo Li | Li, J. |

### Theory: occupancy, tails, order statistics (23)

| identifier | verdict | title as recorded | published | names as the record gives them | as printed |
|---|---|---|---|---|---|
| `0803.2132` | OK | Uniform saddlepoint approximations for ratios of quadratic forms | 2008-03-14 | Ronald W. Butler<br>Marc S. Paolella | Butler, R. W.; Paolella, M. S. |
| `0806.1007` | OK | Competition between Discrete Random Variables, with Applications to Occupancy Problems | 2008-06-05 | Julia Eaton<br>Anant Godbole<br>Betsy Sinclair | Eaton, J.; Godbole, A.; Sinclair, B. |
| `0911.2077` | OK | Central Binomial Tail Bounds | 2009-11-11 | Matus Telgarsky | Telgarsky, M. |
| `1005.2616` | OK | Chains-into-Bins Processes | 2010-05-14 | Tugkan Batu<br>Petra Berenbrink<br>Colin Cooper | Batu, T.; Berenbrink, P.; Cooper, C. |
| `1107.1533` | OK | Martingale Couplings and Bounds on the Tails of Probability Distributions | 2011-07-07 | Kyle J. Luh<br>Nicholas Pippenger | Luh, K. J.; Pippenger, N. |
| `1111.6358` | OK | Bounds for tail probabilities of martingales using skewness and kurtosis | 2011-11-28 | Vidmantas Bentkus<br>Tomas Juškevičius | Bentkus, V.; Juškevičius, T. |
| `1201.3310` | OK | A Generalization of Multiple Choice Balls-into-Bins: Tight Bounds | 2012-01-16 | Gahyun Park | Park, G. |
| `1203.3106` | OK | Saddlepoint approximations for likelihood ratio like statistics with applications to permutation tests | 2012-03-14 | John Kolassa<br>John Robinson | Kolassa, J.; Robinson, J. |
| `1207.2125` | OK | Balls into Bins via Local Search | 2012-07-09 | Paul Bogdan<br>Thomas Sauerwald<br>Alexandre Stauffer<br>(+1 more) | Bogdan, P.; Sauerwald, T.; Stauffer, A.; et al. |
| `1310.0801` | OK | Balls into bins via local search: cover time and maximum load | 2013-10-02 | Karl Bringmann<br>Thomas Sauerwald<br>Alexandre Stauffer<br>(+1 more) | Bringmann, K.; Sauerwald, T.; Stauffer, A.; et al. |
| `2012.09968` | OK | Binomial Tails for Community Analysis | 2020-12-17 | Omid Madani<br>Thanh Ngo<br>Weifei Zeng<br>(+5 more) | Madani, O.; Ngo, T.; Zeng, W.; et al. |
| `2203.12400` | OK | Tight Bounds for Repeated Balls-into-Bins | 2022-03-23 | Dimitrios Los<br>Thomas Sauerwald | Los, D.; Sauerwald, T. |
| `2205.14494` | OK | Balls and Bins -- Simple Concentration Bounds | 2022-05-28 | Ernst Schulte-Geers<br>Bo Waggoner | Schulte-Geers, E.; Waggoner, B. |
| `2209.02220` | OK | Three Distributions in the Extended Occupancy Problem | 2022-09-06 | Ben O'Neill | O'Neill, B. |
| `2211.01688` | OK | Nearly tight universal bounds for the binomial tail probabilities | 2022-11-03 | Huangjun Zhu<br>Zihao Li<br>Masahito Hayashi | Zhu, H.; Li, Z.; Hayashi, M. |
| `2502.18611` | OK | Tight Bounds on the Binomial CDF, and the Minimum of i.i.d Binomials, in terms of KL-Divergence | 2025-02-25 | Xiaohan Zhu<br>Mesrob I. Ohannessian<br>Nathan Srebro | Zhu, X.; Ohannessian, M. I.; Srebro, N. |
| `cs/0407023` | OK | Efficient Hashing with Lookups in two Memory Accesses | 2004-07-09 | Rina Panigrahy | Panigrahy, R. |
| `math/0410174` | OK | Large deviation asymptotics for occupancy problems | 2004-10-06 | Paul Dupuis<br>Carl Nuzman<br>Phil Whiting | Dupuis, P.; Nuzman, C.; Whiting, P. |
| `math/0508451` | OK | On the power of two choices: Balls and bins in continuous time | 2005-08-24 | Malwina J. Luczak<br>Colin McDiarmid | Luczak, M. J.; McDiarmid, C. |
| `math/0508604` | OK | Saddlepoint approximation for Student's t-statistic with no moment conditions | 2005-08-30 | Bing-Yi Jing<br>Qi-Man Shao<br>Wang Zhou | Jing, B. Y.; Shao, Q. M.; Zhou, W. |
| `math/0508606` | OK | Tusnady's inequality revisited | 2005-08-30 | Andrew Carter<br>David Pollard | Carter, A.; Pollard, D. |
| `math/0609498` | OK | On the variance of the number of occupied boxes | 2006-09-18 | L. V. Bogachev<br>A. V. Gnedin<br>Yu. V. Yakubovich | Bogachev, L. V.; Gnedin, A. V.; Yakubovich, Y. V. |
| `math/0701718` | OK | Notes on the occupancy problem with infinitely many boxes: general asymptotics and power laws | 2007-01-24 | Alexander Gnedin<br>Ben Hansen<br>Jim Pitman | Gnedin, A.; Hansen, B.; Pitman, J. |

---

Generated by `refs/refs_report.py` from `refs/curated.json` and `refs/verify.log`;
re-generate with `python3 refs/refs_report.py` (`reproduce.sh` step 5b).
