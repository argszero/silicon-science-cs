# Reference authenticity check -- issue #130

Every cited reference was checked against a LIVE external record by
`verify_citations.py`, which verifies the whole **344-entry** pool (not only the cited
subset) so that the `cited but unverified` case cannot hide.  The results are in
`citation-verification.json` and this table is rendered from them.

A resolver that merely answers is not enough: a remembered identifier can resolve to a
DIFFERENT real paper, so the check is the returned TITLE against the stored title, scored
two-sided (the smaller of the two coverage fractions, threshold 0.80).
No identifier here was typed from memory into the manuscript; each came from the
verified pool, which was itself discovered by `refscan130.py`.

- manuscript: `manuscript.md` (built by `build_manuscript.py` from `manuscript.src.md`)
- cited references: **136** (journal bar 100)
- by source: arxiv 120, crossref 16
- carrier, by row: Crossref works/<doi> (title+subtitle compare) 16, arXiv id_list (batched, title compare) 120
- every cited entry matched its LIVE record at a two-sided title score >= 0.80; the
  worst observed score is **1.000** -- read below before treating that as evidence

## What the two carriers establish, and what they do not

The API pass reads the pool's stored title back from the same backend field the harvest
wrote it from, so a perfect score is **expected rather than informative**: it is a
REGRESSION check on the harvest.  It catches an id-to-title mismatch introduced by our
own parsing, a truncated response, or a record withdrawn or renamed between the harvest
and this pass -- it is not independent evidence that the id names the work we think it
does.  (The `id_list` endpoint caps a request at 10 entries unless `max_results` says
otherwise; the tool sets it per chunk and asserts the returned count, because a silent
truncation otherwise looks like records that do not exist.)

The closest thing to independent evidence available is a **second carrier**: the arXiv
abstract page's `citation_title` meta tag, a different endpoint and a different field.
Measured this cycle over a fixed sample of 18 entries: **abstract-page SPOT CHECK (second carrier): agree 18 / 18** -- reported
as a spot check over a sample, never as the full pass.

Three canonical works this paper would naturally cite have no Crossref or arXiv record
and are therefore EXCLUDED rather than entered on a remembered identifier: Cohen 2003
(*A Comparison of String Distance Metrics for Name-Matching Tasks*, an IJCAI workshop
paper) and Demsar 2006 (*Statistical Comparisons of Classifiers over Multiple Data Sets*,
JMLR, which registers no DOI).  The absence is stated here so the hole is visible.

| # | key | method | result | live record read |
|---|-----|--------|--------|------------------|
| 1 | `10.1145/509907.509965` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Similarity estimation techniques from rounding algorithms |
| 2 | `10.1109/sequen.1997.666900` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | On the resemblance and containment of documents |
| 3 | `10.1162/089976698300017197` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms |
| 4 | `1407.4416` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | In Defense of MinHash Over SimHash |
| 5 | `10.1145/997817.997857` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Locality-sensitive hashing scheme based on p-stable distributions |
| 6 | `1612.07710` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Set Similarity Search Beyond MinHash |
| 7 | `1911.00675` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | ProbMinHash -- A Class of Locality-Sensitive Hash Algorithms for the (Probability) Jaccard Similarity |
| 8 | `10.1145/872757.872770` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Winnowing: local algorithms for document fingerprinting |
| 9 | `10.1145/1242572.1242592` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Detecting near-duplicates for web crawling |
| 10 | `1310.0883` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Scalable Protein Sequence Similarity Search using Locality-Sensitive Hashing and MapReduce |
| 11 | `2112.08687` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | BLEND: A Fast, Memory-Efficient, and Accurate Mechanism to Find Fuzzy Seed Matches in Genome Analysis |
| 12 | `1310.4136` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Scalable Locality-Sensitive Hashing for Similarity Search in High-Dimensional, Large-Scale Multimedia Datasets |
| 13 | `1812.01844` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Improving Similarity Search with High-dimensional Locality-sensitive Hashing |
| 14 | `1907.01600` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Approximate Similarity Search Under Edit Distance Using Locality-Sensitive Hashing |
| 15 | `1210.7057` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Efficient Distributed Locality Sensitive Hashing |
| 16 | `1703.01054` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | When Hashes Met Wedges: A Distributed Algorithm for Finding High Similarity Vectors |
| 17 | `1803.09835` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Locality-Sensitive Hashing for Earthquake Detection: A Case Study of Scaling Data-Driven Science |
| 18 | `1912.00831` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Reducing the Complexity of Fingerprinting-Based Positioning using Locality-Sensitive Hashing |
| 19 | `1807.02895` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Filter of Minhash for Image Similarity Measures |
| 20 | `1104.4723` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Bayesian approach for near-duplicate image detection |
| 21 | `10.18653/v1/2022.acl-long.577` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Deduplicating Training Data Makes Language Models Better |
| 22 | `2202.06539` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Deduplicating Training Data Mitigates Privacy Risks in Language Models |
| 23 | `2501.01046` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | SEDD: Scalable and Efficient Dataset Deduplication with GPUs |
| 24 | `2607.08382` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | H3D: Benchmarking Unsupervised Text Hashing for Fine-Grained Document Deduplication |
| 25 | `2604.16426` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Functional Similarity Metric for Neural Networks: Overcoming Parametric Ambiguity via Activation Region Analysis |
| 26 | `1912.05171` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Character 3-gram Mover's Distance: An Effective Method for Detecting Near-duplicate Japanese-language Recipes |
| 27 | `2005.07356` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Near-duplicate video detection featuring coupled temporal and perceptual visual structures and logical inference based matching |
| 28 | `2203.07167` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Dataset and Case Studies for Visual Near-Duplicates Detection in the Context of Social Media |
| 29 | `2308.00721` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Pre-trained Data Deduplication Model based on Active Learning |
| 30 | `2504.00638` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Impact of Data Duplication on Deep Neural Network-Based Image Classifiers: Robust vs. Standard Models |
| 31 | `2506.20920` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | FineWeb2: One Pipeline to Scale Them All -- Adapting Pre-Training Data Processing to Every Language |
| 32 | `2608.03199` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | SieveIVF: Threshold-Aware IVF Execution for Large-Scale Training Data Deduplication |
| 33 | `2609.31262` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Deduplication-while-Training: A Resilient Paradigm for Privacy-Preserving Cross-Client Deduplication in Federated Learning |
| 34 | `2411.03923` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Evaluation data contamination in LLMs: how do we measure it and (when) does it matter? |
| 35 | `2506.07202` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Reasoning Multimodal Large Language Model: Data Contamination and Dynamic Evaluation |
| 36 | `2510.27055` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Detecting Data Contamination in LLMs via In-Context Learning |
| 37 | `2310.18018` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark |
| 38 | `2310.10628` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Data Contamination Through the Lens of Time |
| 39 | `2311.09783` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Investigating Data Contamination in Modern Benchmarks for Large Language Models |
| 40 | `2402.03927` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Leak, Cheat, Repeat: Data Contamination and Evaluation Malpractices in Closed-Source LLMs |
| 41 | `2402.15938` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Generalization or Memorization: Data Contamination and Trustworthy Evaluation for Large Language Models |
| 42 | `2405.11930` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Data Contamination Calibration for Black-box LLMs |
| 43 | `2609.15058` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Fast Label-Filtering Approximate Nearest Neighbor Search via Progressive Label Set Stratification |
| 44 | `2406.04244` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Benchmark Data Contamination of Large Language Models: A Survey |
| 45 | `2406.14644` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Unveiling the Spectrum of Data Contamination in Language Models: A Survey from Detection to Remediation |
| 46 | `2410.18966` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Does Data Contamination Detection Work (Well) for LLMs? A Survey and Evaluation on Detection Assumptions |
| 47 | `2502.14425` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Survey on Data Contamination for Large Language Models |
| 48 | `2503.16402` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | The Emperor's New Clothes in Benchmarking? A Rigorous Examination of Mitigation Strategies for LLM Benchmark Data Contamination |
| 49 | `2501.18771` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Overestimation in LLM Evaluation: A Controlled Large-Scale Study on Data Contamination's Impact on Machine Translation |
| 50 | `10.1016/j.scico.2009.02.007` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Comparison and evaluation of code clone detection techniques and tools: A qualitative approach |
| 51 | `10.1145/2884781.2884877` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | SourcererCC: scaling code clone detection to big-code |
| 52 | `1512.06448` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | SourcererCC: Scaling Code Clone Detection to Big Code |
| 53 | `2111.14183` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Code Clone Detection based on Event Embedding and Event Dependency |
| 54 | `2204.07501` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Evaluating few shot and Contrastive learning Methods for Code Clone Detection |
| 55 | `2206.08726` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Evaluation of Contrastive Learning with Various Code Representations for Code Clone Detection |
| 56 | `2401.09885` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Source Code Clone Detection Using Unsupervised Similarity Measures |
| 57 | `2405.00428` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | CC2Vec: Combining Typed Tokens with Contrastive Learning for Effective Code Clone Detection |
| 58 | `2510.24241` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | MAGNET: A Multi-Graph Attentional Network for Code Clone Detection |
| 59 | `2507.15226` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Code Clone Detection via an AlphaFold-Inspired Framework |
| 60 | `2508.01357` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | HyClone: Bridging LLM Understanding and Dynamic Execution for Semantic Code Clone Detection |
| 61 | `2403.18202` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | TGMM: Combining Parse Tree with GPU for Scalable Multilingual and Multi-Granularity Code Clone Detection |
| 62 | `2105.11933` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 63 | `1911.00561` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Twin-Finder: Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 64 | `2204.01028` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | MSCCD: Grammar Pluggable Clone Detection Based on ANTLR Parser Generation |
| 65 | `2002.05204` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Multi-threshold token-based code clone detection |
| 66 | `2006.14505` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Source Code Comments: Overlooked in the Realm of Code Clone Detection |
| 67 | `2110.10493` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | On the Effectiveness of Clone Detection for Detecting IoT-related Vulnerable Clones |
| 68 | `2205.04913` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Cross-Language Source Code Clone Detection Using Deep Learning with InferCode |
| 69 | `2208.12588` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Generalizability of Code Clone Detection on CodeBERT |
| 70 | `2308.13754` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | ZC3: Zero-Shot Cross-Language Code Clone Detection |
| 71 | `2311.08778` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Gitor: Scalable Code Clone Detection by Building Global Sample Graph |
| 72 | `2401.13802` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Investigating the Efficacy of Large Language Models for Code Clone Detection |
| 73 | `2407.02402` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Assessing the Code Clone Detection Capability of Large Language Models |
| 74 | `2408.04430` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | The Struggles of LLMs in Cross-lingual Code Clone Detection |
| 75 | `2506.10995` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Evaluating Small-Scale Code Models for Code Clone Detection |
| 76 | `2509.22978` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Towards Human-interpretable Explanation in Code Clone Detection using LLM-based Post Hoc Explainer |
| 77 | `2510.15480` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Selecting and Combining Large Language Models for Scalable Code Clone Detection |
| 78 | `10.1007/3-540-45123-4_1` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Identifying and Filtering Near-Duplicate Documents |
| 79 | `2111.10864` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | The Impact of Main Content Extraction on Near-Duplicate Detection |
| 80 | `1406.1143` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Identifying Duplicate and Contradictory Information in Wikipedia |
| 81 | `10.1109/ams.2011.19` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Survey of Plagiarism Detection Methods |
| 82 | `1412.7782` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Plagiarism Detection on Electronic Text based Assignments using Vector Space Model (ICIAfS14) |
| 83 | `1403.1310` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | AntiPlag: Plagiarism Detection on Electronic Submissions of Text Based Assignments |
| 84 | `1003.4065` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Plagiarism Detection using ROUGE and WordNet |
| 85 | `1206.6606` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Sampling-based Tool for Plagiarism Detection in Student Texts |
| 86 | `1403.2871` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Shape-Based Plagiarism Detection for Flowchart Figures in Texts |
| 87 | `1705.08828` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Deep Investigation of Cross-Language Plagiarism Detection Methods |
| 88 | `1712.10309` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Methods for Detecting Paraphrase Plagiarism |
| 89 | `1906.11761` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Improving Academic Plagiarism Detection for STEM Documents by Analyzing Mathematical Content and Citations |
| 90 | `2002.04279` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Testing of Support Tools for Plagiarism Detection |
| 91 | `2105.12068` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Taxonomy of academic plagiarism methods |
| 92 | `2106.05764` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Analyzing Non-Textual Content Elements to Detect Academic Plagiarism |
| 93 | `2306.08122` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Beyond Black Box AI-Generated Plagiarism Detection: From Sentence to Document Level |
| 94 | `2404.01582` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection System |
| 95 | `2407.13105` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Survey on Plagiarism Detection in Large Language Models: The Impact of ChatGPT and Gemini on Academic Integrity |
| 96 | `2602.09147` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Overview of PAN 2026: Voight-Kampff Generative AI Detection, Text Watermarking, Multi-Author Writing Style Analysis, Generative Plagiarism Detection, and Reasoning Trajectory Detection |
| 97 | `1905.02973` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | On the Feasibility of Automated Detection of Allusive Text Reuse |
| 98 | `2305.13193` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | TEIMMA: The First Content Reuse Annotator for Text, Images, and Math |
| 99 | `2607.10020` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | FindMyText: Robust, Scalable Detection of Text Containment in Large Web-Crawled Corpora |
| 100 | `2211.16259` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Measuring the Measuring Tools: An Automatic Evaluation of Semantic Metrics for Text Corpora |
| 101 | `2206.12664` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Evaluation of Semantic Answer Similarity Metrics |
| 102 | `2108.06130` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Semantic Answer Similarity for Evaluating Question Answering Models |
| 103 | `1808.10192` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Towards a Better Metric for Evaluating Question Generation Systems |
| 104 | `2310.11593` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Automated Evaluation of Personalized Text Generation using Large Language Models |
| 105 | `2405.06807` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Execution-Based Evaluation of Natural Language to Bash and PowerShell for Incident Remediation |
| 106 | `2407.11470` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Beyond Correctness: Benchmarking Multi-dimensional Code Generation for Large Language Models |
| 107 | `2503.06643` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Is Your Benchmark Still Useful? Dynamic Benchmarking for Code Language Models |
| 108 | `2211.09374` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Execution-based Evaluation for Data Science Code Generation Models |
| 109 | `10.1111/j.2517-6161.1995.tb02031.x` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing |
| 110 | `10.18653/v1/p18-1128` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing |
| 111 | `10.18653/v1/d19-1224` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Show Your Work: Improved Reporting of Experimental Results |
| 112 | `2506.13160` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | CertDW: Towards Certified Dataset Ownership Verification via Conformal Calibration |
| 113 | `2502.08666` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Hallucination, Monofacts, and Miscalibration: An Empirical Investigation |
| 114 | `2508.09346` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | How Safe Will I Be Given What I Saw? Calibrated Prediction of Safety Chances for Image-Controlled Autonomy |
| 115 | `10.1137/070710111` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Power-Law Distributions in Empirical Data |
| 116 | `2305.17310` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | DotHash: Estimating Set Similarity Metrics for Link Prediction and Document Deduplication |
| 117 | `1904.04045` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Subsets and Supermajorities: Optimal Hashing-based Set Similarity Search |
| 118 | `2005.11547` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | DartMinHash: Fast Sketching for Weighted Sets |
| 119 | `2101.00314` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | SetSketch: Filling the Gap between MinHash and HyperLogLog |
| 120 | `2310.06703` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | DeepLSH: Deep Locality-Sensitive Hash Learning for Fast and Efficient Near-Duplicate Crash Report Detection |
| 121 | `2511.16576` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | PolyMinHash: Efficient Area-Based MinHashing of Polygons for Approximate Nearest Neighbor Search |
| 122 | `2606.31272` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | The Decomposition Is the Fingerprint: Per-Component Identity for Agent Skills |
| 123 | `1905.08977` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Memory-Efficient Sketch Method for Estimating High Similarities in Streaming Sets |
| 124 | `2306.07674` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Differentially Private One Permutation Hashing and Bin-wise Consistent Weighted Sampling |
| 125 | `1704.05617` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Deduplication in a massive clinical note dataset |
| 126 | `2001.01128` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Locality-Sensitive Hashing for Efficient Web Application Security Testing |
| 127 | `10.1109/focs.2006.49` | Crossref works/<doi> (title+subtitle compare) | VERIFIED (1.00) | Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions |
| 128 | `1810.03099` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Multi-reference Cosine: A New Approach to Text Similarity Measurement in Large Collections |
| 129 | `1810.03102` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | A Fast Text Similarity Measure for Large Document Collections using Multi-reference Cosine and Genetic Algorithm |
| 130 | `1206.2082` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Dimension Independent Similarity Computation |
| 131 | `2311.17264` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | RETSim: Resilient and Efficient Text Similarity |
| 132 | `2509.19323` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Magnitude Matters: a Superior Class of Similarity Metrics for Holistic Semantic Understanding |
| 133 | `2309.13080` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | SPICED: News Similarity Detection Dataset with Multiple Topics and Complexity Levels |
| 134 | `2310.15298` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | TaskDiff: A Similarity Metric for Task-Oriented Conversations |
| 135 | `2502.02494` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Analyzing Similarity Metrics for Data Selection for Language Model Pretraining |
| 136 | `2501.18998` | arXiv id_list (batched, title compare) | VERIFIED (1.00) | Adversarial Attacks on AI-Generated Text Detection Models: A Token Probability-Based Approach Using Embeddings |

A key that cannot be verified is deleted from the manuscript, not reported: the build
refuses to render a citation whose key is absent from the verified pool, and this
generator refuses to write when a cited key carries no verdict.
