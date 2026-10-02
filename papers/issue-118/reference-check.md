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
| `refs/curated.json` | the curated set, with the role and the stated difference of each entry | `f69cefd0cf703c6d2c88a4987485a2a834d39d374df8d2cad5141c3a8f3915f3` |

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

## (iii) The entries, by role

### The construct: capacity, dropping, and the routing discipline (12)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2005.07761` | OK | Efficient Load-Balancing through Distributed Token Dropping | 2020-05-15 |
| `2006.16668` | OK | GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding | 2020-06-30 |
| `2010.11018` | OK | Token Drop mechanism for Neural Machine Translation | 2020-10-21 |
| `2101.03961` | OK | Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity | 2021-01-11 |
| `2105.15082` | OK | M6-T: Exploring Sparse Expert Models and Beyond | 2021-05-31 |
| `2106.04426` | OK | Hash Layers For Large Sparse Models | 2021-06-08 |
| `2112.06905` | OK | GLaM: Efficient Scaling of Language Models with Mixture-of-Experts | 2021-12-13 |
| `2202.09368` | OK | Mixture-of-Experts with Expert Choice Routing | 2022-02-18 |
| `2203.13240` | OK | Token Dropping for Efficient BERT Pretraining | 2022-03-24 |
| `2211.11586` | OK | Random-LTD: Random and Layerwise Token Dropping Brings Efficient Training for Large-scale Transformers | 2022-11-17 |
| `2308.00951` | OK | From Sparse to Soft Mixtures of Experts | 2023-08-02 |
| `2508.12801` | OK | Maximum Score Routing For Mixture-of-Experts | 2025-08-18 |

### Load balancing: the field's standard remedy (8)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2109.11817` | OK | Unbiased Gradient Estimation with Balanced Assignments for Mixtures of Experts | 2021-09-24 |
| `2408.15664` | OK | Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts | 2024-08-28 |
| `2411.19402` | OK | On the Role of Discrete Representation in Sparse Mixture of Experts | 2024-11-28 |
| `2502.15451` | OK | Binary-Integer-Programming Based Algorithm for Expert Load Balancing in Mixture-of-Experts Models | 2025-02-21 |
| `2504.01337` | OK | Advancing MoE Efficiency: A Collaboration-Constrained Routing (C2R) Strategy for Better Expert Parallelism Design | 2025-04-02 |
| `2512.03915` | OK | A Theoretical Framework for Auxiliary-Loss-Free Load Balancing of Sparse Mixture-of-Experts in Large-Scale AI Models | 2025-12-03 |
| `2602.03478` | OK | When Routing Collapses: On the Degenerate Convergence of LLM Routers | 2026-02-03 |
| `2602.14159` | OK | Synergistic Intra- and Cross-Layer Regularization Losses for MoE Expert Specialization | 2026-02-15 |

### Capacity and the straggler effect (3)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2403.07652` | OK | Harder Tasks Need More Experts: Dynamic Routing in MoE Models | 2024-03-12 |
| `2502.16927` | OK | BigMac: A Communication-Efficient Mixture-of-Experts Model Structure for Fast Training and Inference | 2025-02-24 |
| `2503.05066` | OK | Capacity-Aware Inference: Mitigating the Straggler Effect in Mixture of Experts | 2025-03-07 |

### Inference serving: the decode regime (27)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2201.05596` | OK | DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training to Power Next-Generation AI Scale | 2022-01-14 |
| `2308.12066` | OK | Pre-gated MoE: An Algorithm-System Co-Design for Fast and Scalable Mixture-of-Expert Inference | 2023-08-23 |
| `2308.15030` | OK | SwapMoE: Serving Off-the-shelf MoE-based Large Language Models with Tunable Memory Budget | 2023-08-29 |
| `2401.14361` | OK | MoE-Infinity: Efficient MoE Inference on Personal Machines with Sparsity-Aware Expert Cache | 2024-01-25 |
| `2410.17954` | OK | ExpertFlow: Efficient Mixture-of-Experts Inference via Predictive Expert Caching and Token Scheduling | 2024-10-23 |
| `2411.01433` | OK | HOBBIT: A Mixed Precision Expert Offloading System for Fast MoE Inference | 2024-11-03 |
| `2501.10375` | OK | DAOP: Data-Aware Offloading and Predictive Pre-Calculation for Efficient MoE Inference | 2024-12-16 |
| `2502.05370` | OK | Taming Latency-Memory Trade-Off in MoE-Based LLM Serving via Fine-Grained Expert Offloading | 2025-02-07 |
| `2502.06888` | OK | Klotski: Efficient Mixture-of-Expert Inference via Expert-Aware Multi-Batch Pipeline | 2025-02-09 |
| `2502.12224` | OK | Fate: Fast Edge Inference of Mixture-of-Experts Models via Cross-Layer Gate | 2025-02-17 |
| `2504.02263` | OK | MegaScale-Infer: Serving Mixture-of-Experts at Scale with Disaggregated Expert Parallelism | 2025-04-03 |
| `2504.05897` | OK | HybriMoE: Hybrid CPU-GPU Scheduling and Cache Management for Efficient MoE Inference | 2025-04-08 |
| `2505.16056` | OK | Not All Models Suit Expert Offloading: On Local Routing Consistency of Mixture-of-Expert Models | 2025-05-21 |
| `2506.12708` | OK | Serving Large Language Models on Huawei CloudMatrix384 | 2025-06-15 |
| `2508.09208` | OK | CoMoE: Collaborative Optimization of Expert Aggregation and Offloading for MoE-based LLMs at Edge | 2025-08-10 |
| `2508.18983` | OK | SMoE: An Algorithm-System Co-Design for Pushing MoE to the Edge via Expert Substitution | 2025-08-26 |
| `2508.19373` | OK | HAP: Hybrid Adaptive Parallelism for Efficient Mixture-of-Experts Inference | 2025-08-26 |
| `2512.12990` | OK | SliceMoE: Bit-Sliced Expert Caching under Miss-Rate Constraints for Efficient MoE Inference | 2025-12-15 |
| `2601.05296` | OK | MoEBlaze: Breaking the Memory Wall for Efficient MoE Training on Modern GPUs | 2026-01-08 |
| `2602.16052` | OK | MoE-Spec: Expert Budgeting for Efficient Speculative Decoding | 2026-02-17 |
| `2603.06350` | OK | MoEless: Efficient MoE LLM Serving with Serverless Experts | 2026-03-06 |
| `2604.18788` | OK | Efficient Mixture-of-Experts LLM Inference with Apple Silicon NPUs | 2026-04-20 |
| `2604.23150` | OK | Scaling Multi-Node Mixture-of-Experts Inference Using Expert Activation Patterns | 2026-04-25 |
| `2605.10670` | OK | Surviving Partial Rank Failures in Wide Expert-Parallel MoE Inference | 2026-05-11 |
| `2609.33385` | OK | OLED-MoE: Accelerating MoE-Based dLLM Inference via Inter-Iteration Locality-Aware Expert Offloading | 2026-09-27 |
| `2610.01265` | OK | RapidMoE: Exploiting Cross-Asymmetry via Adaptive Residual Offloading for Large-Scale MoE Inference | (author-supplied) |
| `2610.01950` | OK | MoE-CORE: Coordinated Expert Offloading and Residency for Memory-Constrained MoE Inference | 2026-10-01 |

### Named architectures (14)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2401.04088` | OK | Mixtral of Experts | 2024-01-08 |
| `2401.06066` | OK | DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models | 2024-01-11 |
| `2405.04434` | OK | DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model | 2024-05-07 |
| `2406.00023` | OK | Expert-Token Resonance MoE: Bidirectional Routing with Efficiency Affinity-Driven Active Selection | 2024-05-24 |
| `2406.13233` | OK | AdaMoE: Token-Adaptive Routing with Null Experts for Mixture-of-Experts Language Models | 2024-06-19 |
| `2407.10671` | OK | Qwen2 Technical Report | (author-supplied) |
| `2409.02060` | OK | OLMoE: Open Mixture-of-Experts Language Models | 2024-09-03 |
| `2410.10456` | OK | Ada-K Routing: Boosting the Efficiency of MoE-based LLMs | 2024-10-14 |
| `2412.10302` | OK | DeepSeek-VL2: Mixture-of-Experts Vision-Language Models for Advanced Multimodal Understanding | 2024-12-13 |
| `2412.19437` | OK | DeepSeek-V3 Technical Report | 2024-12-27 |
| `2503.15798` | OK | Mixture of Lookup Experts | 2025-03-20 |
| `2505.22323` | OK | Advancing Expert Specialization for Better MoE | 2025-05-28 |
| `2604.12163` | OK | Nucleus-Image: Sparse MoE for Image Generation | 2026-04-14 |
| `2608.17402` | OK | MoE-ViE: Mixture of Experts Vision Encoder for Efficient Image and Video Understanding | 2026-08-18 |

### Efficiency and systems adjacency (9)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2206.00277` | OK | Task-Specific Expert Pruning for Sparse Mixture-of-Experts | 2022-06-01 |
| `2404.05019` | OK | Shortcut-connected Expert Parallelism for Accelerating Mixture-of-Experts | 2024-04-07 |
| `2407.04656` | OK | Lazarus: Resilient and Elastic Training of Mixture-of-Experts Models | 2024-07-05 |
| `2411.15419` | OK | Communication-Efficient Sparsely-Activated Model Training via Sequence Migration and Token Condensation | 2024-11-23 |
| `2411.16786` | OK | Staleness-Centric Optimizations for Parallel Diffusion MoE Inference | 2024-11-25 |
| `2503.06881` | OK | ResMoE: Space-efficient Compression of Mixture of Experts LLMs via Residual Restoration | 2025-03-10 |
| `2504.14960` | OK | MoE Parallel Folding: Heterogeneous Parallelism Mappings for Efficient Large-Scale MoE Model Training with Megatron Core | 2025-04-21 |
| `2506.23635` | OK | Towards Building Private LLMs: Exploring Multi-Node Expert Parallelism on Apple Silicon for Mixture-of-Experts Large Language Model | 2025-06-30 |
| `2608.28511` | OK | Training Communication-Efficient Mixture-of-Experts Language Models with Layer Re-Configuration | 2026-08-28 |

### Capacity overflow as an attack surface (4)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2410.22884` | OK | Stealing User Prompts from Mixture of Experts | 2024-10-30 |
| `2504.18598` | OK | BadMoE: Backdooring Mixture-of-Experts LLMs via Optimizing Routing Triggers and Infecting Dormant Experts | 2025-04-24 |
| `2510.13462` | OK | Who Speaks for the Trigger? Dynamic Expert Routing in Backdoored Mixture-of-Experts Transformers | 2025-10-15 |
| `2608.25371` | OK | Capacity Overflow: A Blind Spot for Backdoor Attacks in Vision MoE | 2026-08-26 |

### Surveys and the design space (5)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `2602.03204` | OK | Sparsity is Combinatorial Depth: Quantifying MoE Expressivity via Tropical Geometry | 2026-02-03 |
| `2602.17798` | OK | Grassmannian Mixture-of-Experts: Concentration-Controlled Routing on Subspace Manifolds | 2026-02-19 |
| `2603.11114` | OK | Task-Conditioned Routing Signatures in Sparse Mixture-of-Experts Transformers | 2026-03-11 |
| `2605.11689` | OK | Slicing and Dicing: Configuring Optimal Mixtures of Experts | (author-supplied) |
| `2608.08650` | OK | The Evolution of Mixture-of-Experts Architectures in Large Language Models: Routing, Topology, Load Balancing, and Expert Parallelism | 2026-08-09 |

### Theory: occupancy, tails, order statistics (23)

| identifier | verdict | title as recorded | published |
|---|---|---|---|
| `0803.2132` | OK | Uniform saddlepoint approximations for ratios of quadratic forms | 2008-03-14 |
| `0806.1007` | OK | Competition between Discrete Random Variables, with Applications to Occupancy Problems | 2008-06-05 |
| `0911.2077` | OK | Central Binomial Tail Bounds | 2009-11-11 |
| `1005.2616` | OK | Chains-into-Bins Processes | 2010-05-14 |
| `1107.1533` | OK | Martingale Couplings and Bounds on the Tails of Probability Distributions | 2011-07-07 |
| `1111.6358` | OK | Bounds for tail probabilities of martingales using skewness and kurtosis | 2011-11-28 |
| `1201.3310` | OK | A Generalization of Multiple Choice Balls-into-Bins: Tight Bounds | 2012-01-16 |
| `1203.3106` | OK | Saddlepoint approximations for likelihood ratio like statistics with applications to permutation tests | 2012-03-14 |
| `1207.2125` | OK | Balls into Bins via Local Search | 2012-07-09 |
| `1310.0801` | OK | Balls into bins via local search: cover time and maximum load | 2013-10-02 |
| `2012.09968` | OK | Binomial Tails for Community Analysis | 2020-12-17 |
| `2203.12400` | OK | Tight Bounds for Repeated Balls-into-Bins | 2022-03-23 |
| `2205.14494` | OK | Balls and Bins -- Simple Concentration Bounds | 2022-05-28 |
| `2209.02220` | OK | Three Distributions in the Extended Occupancy Problem | 2022-09-06 |
| `2211.01688` | OK | Nearly tight universal bounds for the binomial tail probabilities | 2022-11-03 |
| `2502.18611` | OK | Tight Bounds on the Binomial CDF, and the Minimum of i.i.d Binomials, in terms of KL-Divergence | 2025-02-25 |
| `cs/0407023` | OK | Efficient Hashing with Lookups in two Memory Accesses | 2004-07-09 |
| `math/0410174` | OK | Large deviation asymptotics for occupancy problems | 2004-10-06 |
| `math/0508451` | OK | On the power of two choices: Balls and bins in continuous time | 2005-08-24 |
| `math/0508604` | OK | Saddlepoint approximation for Student's t-statistic with no moment conditions | 2005-08-30 |
| `math/0508606` | OK | Tusnady's inequality revisited | 2005-08-30 |
| `math/0609498` | OK | On the variance of the number of occupied boxes | 2006-09-18 |
| `math/0701718` | OK | Notes on the occupancy problem with infinitely many boxes: general asymptotics and power laws | 2007-01-24 |

---

Generated by `refs/refs_report.py` from `refs/curated.json` and `refs/verify.log`;
re-generate with `python3 refs/refs_report.py` (`reproduce.sh` step 5b).
