# Reference pool -- issue #130

Every entry below was discovered by `refscan130.py` (never typed from memory) and checked
against a LIVE external record by comparing the returned TITLE with the stored title
(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a
remembered identifier can resolve to a DIFFERENT real paper, so the check is the title
comparison, not the HTTP status.

- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with
  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)
  and `works/<doi>` (verification)
- pool: 344 entries (328 arXiv, 16 Crossref)
- an entry whose title does not match its live record is dropped, never kept

| key | source | verified against | title |
|-----|--------|------------------|-------|
| 10.1007/3-540-45123-4_1 | crossref | Crossref works/<doi> | Identifying and Filtering Near-Duplicate Documents |
| 10.1016/j.scico.2009.02.007 | crossref | Crossref works/<doi> | Comparison and evaluation of code clone detection techniques and tools: A qualitative approach |
| 10.1109/ams.2011.19 | crossref | Crossref works/<doi> | Survey of Plagiarism Detection Methods |
| 10.1109/focs.2006.49 | crossref | Crossref works/<doi> | Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions |
| 10.1109/sequen.1997.666900 | crossref | Crossref works/<doi> | On the resemblance and containment of documents |
| 10.1111/j.2517-6161.1995.tb02031.x | crossref | Crossref works/<doi> | Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing |
| 10.1137/070710111 | crossref | Crossref works/<doi> | Power-Law Distributions in Empirical Data |
| 10.1145/1242572.1242592 | crossref | Crossref works/<doi> | Detecting near-duplicates for web crawling |
| 10.1145/2884781.2884877 | crossref | Crossref works/<doi> | SourcererCC: scaling code clone detection to big-code |
| 10.1145/509907.509965 | crossref | Crossref works/<doi> | Similarity estimation techniques from rounding algorithms |
| 10.1145/872757.872770 | crossref | Crossref works/<doi> | Winnowing: local algorithms for document fingerprinting |
| 10.1145/997817.997857 | crossref | Crossref works/<doi> | Locality-sensitive hashing scheme based on p-stable distributions |
| 10.1162/089976698300017197 | crossref | Crossref works/<doi> | Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms |
| 10.18653/v1/2022.acl-long.577 | crossref | Crossref works/<doi> | Deduplicating Training Data Makes Language Models Better |
| 10.18653/v1/d19-1224 | crossref | Crossref works/<doi> | Show Your Work: Improved Reporting of Experimental Results |
| 10.18653/v1/p18-1128 | crossref | Crossref works/<doi> | The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing |
| 1001.3487 | arxiv | arXiv id_list | Features Based Text Similarity Detection |
| 1003.4065 | arxiv | arXiv id_list | Plagiarism Detection using ROUGE and WordNet |
| 1006.3514 | arxiv | arXiv id_list | Similarity Search and Locality Sensitive Hashing using TCAMs |
| 1104.3212 | arxiv | arXiv id_list | Similarity Join Size Estimation using Locality Sensitive Hashing |
| 1104.4723 | arxiv | arXiv id_list | Bayesian approach for near-duplicate image detection |
| 1110.1328 | arxiv | arXiv id_list | Bayesian Locality Sensitive Hashing for Fast Similarity Search |
| 1111.5062 | arxiv | arXiv id_list | EsPRESSo: Efficient Privacy-Preserving Evaluation of Sample Set Similarity |
| 1206.2082 | arxiv | arXiv id_list | Dimension Independent Similarity Computation |
| 1206.6606 | arxiv | arXiv id_list | A Sampling-based Tool for Plagiarism Detection in Student Texts |
| 1208.2486 | arxiv | arXiv id_list | `CodeAliker' - Plagiarism Detection on the Cloud |
| 1209.5833 | arxiv | arXiv id_list | Locality-Sensitive Hashing with Margin Based Feature Selection |
| 1210.3729 | arxiv | arXiv id_list | Inference of Fine-grained Attributes of Bengali Corpus for Stylometry Detection |
| 1210.7057 | arxiv | arXiv id_list | Efficient Distributed Locality Sensitive Hashing |
| 1210.7678 | arxiv | arXiv id_list | Plagiarism Detection: Keeping Check on Misuse of Intellectual Property |
| 1212.6110 | arxiv | arXiv id_list | Hyperplane Arrangements and Locality-Sensitive Hashing with Lift |
| 1303.4169 | arxiv | arXiv id_list | Markov Chain Monte Carlo for Arrangement of Hyperplanes in Locality-Sensitive Hashing |
| 1310.0883 | arxiv | arXiv id_list | Scalable Protein Sequence Similarity Search using Locality-Sensitive Hashing and MapReduce |
| 1310.4136 | arxiv | arXiv id_list | Scalable Locality-Sensitive Hashing for Similarity Search in High-Dimensional, Large-Scale Multi |
| 1403.1310 | arxiv | arXiv id_list | AntiPlag: Plagiarism Detection on Electronic Submissions of Text Based Assignments |
| 1403.2871 | arxiv | arXiv id_list | Shape-Based Plagiarism Detection for Flowchart Figures in Texts |
| 1406.1143 | arxiv | arXiv id_list | Identifying Duplicate and Contradictory Information in Wikipedia |
| 1407.4416 | arxiv | arXiv id_list | In Defense of MinHash Over SimHash |
| 1412.3103 | arxiv | arXiv id_list | Sequential Hypothesis Tests for Adaptive Locality Sensitive Hashing |
| 1412.7782 | arxiv | arXiv id_list | Plagiarism Detection on Electronic Text based Assignments using Vector Space Model (ICIAfS14) |
| 1507.03225 | arxiv | arXiv id_list | CoveringLSH: Locality-sensitive Hashing without False Negatives |
| 1512.06448 | arxiv | arXiv id_list | SourcererCC: Scaling Code Clone Detection to Big Code |
| 1607.02952 | arxiv | arXiv id_list | Are human interactivity times lognormal? |
| 1612.07710 | arxiv | arXiv id_list | Set Similarity Search Beyond MinHash |
| 1701.05290 | arxiv | arXiv id_list | Range-efficient consistent sampling and locality-sensitive hashing for polygons |
| 1702.01032 | arxiv | arXiv id_list | Semi-Supervised Spam Detection in Twitter Stream |
| 1703.01054 | arxiv | arXiv id_list | When Hashes Met Wedges: A Distributed Algorithm for Finding High Similarity Vectors |
| 1703.04040 | arxiv | arXiv id_list | Locality-sensitive hashing of curves |
| 1704.04370 | arxiv | arXiv id_list | Fast Similarity Sketching |
| 1704.05617 | arxiv | arXiv id_list | Deduplication in a massive clinical note dataset |
| 1705.07258 | arxiv | arXiv id_list | PrivMin: Differentially Private MinHash for Jaccard Similarity Computation |
| 1705.08828 | arxiv | arXiv id_list | Deep Investigation of Cross-Language Plagiarism Detection Methods |
| 1706.05698 | arxiv | arXiv id_list | SuperMinHash - A New Minwise Hashing Algorithm for Jaccard Similarity Estimation |
| 1712.02820 | arxiv | arXiv id_list | A Deep Network Model for Paraphrase Detection in Short Text Messages |
| 1712.10309 | arxiv | arXiv id_list | Methods for Detecting Paraphrase Plagiarism |
| 1803.03465 | arxiv | arXiv id_list | Malytics: A Malware Detection Scheme |
| 1803.09835 | arxiv | arXiv id_list | Locality-Sensitive Hashing for Earthquake Detection: A Case Study of Scaling Data-Driven Science |
| 1805.01923 | arxiv | arXiv id_list | A Rank-Based Similarity Metric for Word Embeddings |
| 1806.06870 | arxiv | arXiv id_list | The Off-Topic Memento Toolkit |
| 1807.02895 | arxiv | arXiv id_list | A Filter of Minhash for Image Similarity Measures |
| 1808.10192 | arxiv | arXiv id_list | Towards a Better Metric for Evaluating Question Generation Systems |
| 1809.04052 | arxiv | arXiv id_list | Maximally Consistent Sampling and the Jaccard Index of Probability Distributions |
| 1810.03099 | arxiv | arXiv id_list | Multi-reference Cosine: A New Approach to Text Similarity Measurement in Large Collections |
| 1810.03102 | arxiv | arXiv id_list | A Fast Text Similarity Measure for Large Document Collections using Multi-reference Cosine and G |
| 1810.11903 | arxiv | arXiv id_list | Dynamic Thresholding Mechanisms for IR-Based Filtering in Efficient Source Code Plagiarism Detec |
| 1811.04633 | arxiv | arXiv id_list | A Review for Weighted MinHash Algorithms |
| 1812.01844 | arxiv | arXiv id_list | Improving Similarity Search with High-dimensional Locality-sensitive Hashing |
| 1901.00650 | arxiv | arXiv id_list | A Fast Sketch Method for Mining User Similarities over Fully Dynamic Graph Streams |
| 1904.04045 | arxiv | arXiv id_list | Subsets and Supermajorities: Optimal Hashing-based Set Similarity Search |
| 1904.08572 | arxiv | arXiv id_list | node2bits: Compact Time- and Attribute-aware Node Representations for User Stitching |
| 1904.09442 | arxiv | arXiv id_list | Personalized sentence generation using generative adversarial networks with author-specific word |
| 1905.02973 | arxiv | arXiv id_list | On the Feasibility of Automated Detection of Allusive Text Reuse |
| 1905.08977 | arxiv | arXiv id_list | A Memory-Efficient Sketch Method for Estimating High Similarities in Streaming Sets |
| 1906.11761 | arxiv | arXiv id_list | Improving Academic Plagiarism Detection for STEM Documents by Analyzing Mathematical Content and |
| 1907.01600 | arxiv | arXiv id_list | Approximate Similarity Search Under Edit Distance Using Locality-Sensitive Hashing |
| 1907.02251 | arxiv | arXiv id_list | Hardness of Bichromatic Closest Pair with Jaccard Similarity |
| 1908.04042 | arxiv | arXiv id_list | Evaluating Tag Recommendations for E-Book Annotation Using a Semantic Similarity Metric |
| 1909.07950 | arxiv | arXiv id_list | Semantic Relatedness Based Re-ranker for Text Spotting |
| 1910.10683 | arxiv | arXiv id_list | Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer |
| 1911.00561 | arxiv | arXiv id_list | Twin-Finder: Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 1911.00675 | arxiv | arXiv id_list | ProbMinHash -- A Class of Locality-Sensitive Hash Algorithms for the (Probability) Jaccard Simil |
| 1912.00831 | arxiv | arXiv id_list | Reducing the Complexity of Fingerprinting-Based Positioning using Locality-Sensitive Hashing |
| 1912.05171 | arxiv | arXiv id_list | Character 3-gram Mover's Distance: An Effective Method for Detecting Near-duplicate Japanese-lan |
| 1912.12068 | arxiv | arXiv id_list | A Multi-cascaded Model with Data Augmentation for Enhanced Paraphrase Detection in Short Texts |
| 2001.01128 | arxiv | arXiv id_list | Locality-Sensitive Hashing for Efficient Web Application Security Testing |
| 2002.03909 | arxiv | arXiv id_list | Locality-sensitive hashing in function spaces |
| 2002.04279 | arxiv | arXiv id_list | Testing of Support Tools for Plagiarism Detection |
| 2002.05204 | arxiv | arXiv id_list | Multi-threshold token-based code clone detection |
| 2004.04478 | arxiv | arXiv id_list | Recommendation Chart of Domains for Cross-Domain Sentiment Analysis:Findings of A 20 Domain Stud |
| 2004.05265 | arxiv | arXiv id_list | Visual Spoofing in content based spam detection |
| 2004.11131 | arxiv | arXiv id_list | Privacy at Scale: Introducing the PrivaSeer Corpus of Web Privacy Policies |
| 2005.07356 | arxiv | arXiv id_list | Near-duplicate video detection featuring coupled temporal and perceptual visual structures and l |
| 2005.11547 | arxiv | arXiv id_list | DartMinHash: Fast Sketching for Weighted Sets |
| 2005.12065 | arxiv | arXiv id_list | On the Problem of $p_1^{-1}$ in Locality-Sensitive Hashing |
| 2006.09719 | arxiv | arXiv id_list | Automatically Ranked Russian Paraphrase Corpus for Text Generation |
| 2006.11284 | arxiv | arXiv id_list | Improving Locality Sensitive Hashing by Efficiently Finding Projected Nearest Neighbors |
| 2006.14505 | arxiv | arXiv id_list | Source Code Comments: Overlooked in the Realm of Code Clone Detection |
| 2007.09660 | arxiv | arXiv id_list | Introduction to Random Fields |
| 2008.04308 | arxiv | arXiv id_list | CG-SENSE revisited: Results from the first ISMRM reproducibility challenge |
| 2008.08134 | arxiv | arXiv id_list | Differentially Private Sketches for Jaccard Similarity Estimation |
| 2010.01263 | arxiv | arXiv id_list | Multilevel Text Alignment with Cross-Document Attention |
| 2010.06150 | arxiv | arXiv id_list | Improving Text Generation Evaluation with Batch Centering and Tempered Word Mover Distance |
| 2101.00314 | arxiv | arXiv id_list | SetSketch: Filling the Gap between MinHash and HyperLogLog |
| 2101.02733 | arxiv | arXiv id_list | Layer reconstruction and missing link prediction of multilayer network with a Maximum A Posterio |
| 2101.04339 | arxiv | arXiv id_list | Locality Sensitive Hashing for Efficient Similar Polygon Retrieval |
| 2102.10315 | arxiv | arXiv id_list | EXTRA: Explanation Ranking Datasets for Explainable Recommendation |
| 2104.14962 | arxiv | arXiv id_list | PSEUDo: Interactive Pattern Search in Multivariate Time Series with Locality-Sensitive Hashing a |
| 2105.11933 | arxiv | arXiv id_list | Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 2105.12068 | arxiv | arXiv id_list | Taxonomy of academic plagiarism methods |
| 2106.05764 | arxiv | arXiv id_list | Analyzing Non-Textual Content Elements to Detect Academic Plagiarism |
| 2107.06499 | arxiv | arXiv id_list | Deduplicating Training Data Makes Language Models Better |
| 2108.06130 | arxiv | arXiv id_list | Semantic Answer Similarity for Evaluating Question Answering Models |
| 2109.03337 | arxiv | arXiv id_list | C-MinHash: Rigorously Reducing $K$ Permutations to Two |
| 2109.04595 | arxiv | arXiv id_list | C-MinHash: Practically Reducing Two Permutations to Just One |
| 2109.08789 | arxiv | arXiv id_list | When Similarity Digest Meets Vector Management System: A Survey on Similarity Hash Function |
| 2110.01092 | arxiv | arXiv id_list | Towards Informative Tagging of Code Fragments to Support the Investigation of Code Clones |
| 2110.10493 | arxiv | arXiv id_list | On the Effectiveness of Clone Detection for Detecting IoT-related Vulnerable Clones |
| 2110.11934 | arxiv | arXiv id_list | Cleaning Dirty Books: Post-OCR Processing for Previously Scanned Texts |
| 2111.07839 | arxiv | arXiv id_list | Learnable Locality-Sensitive Hashing for Video Anomaly Detection |
| 2111.09544 | arxiv | arXiv id_list | C-OPH: Improving the Accuracy of One Permutation Hashing (OPH) with Circulant Permutations |
| 2111.10864 | arxiv | arXiv id_list | The Impact of Main Content Extraction on Near-Duplicate Detection |
| 2111.14183 | arxiv | arXiv id_list | Code Clone Detection based on Event Embedding and Event Dependency |
| 2112.05492 | arxiv | arXiv id_list | BCD: A Cross-Architecture Binary Comparison Database Experiment Using Locality Sensitive Hashing |
| 2112.08687 | arxiv | arXiv id_list | BLEND: A Fast, Memory-Efficient, and Accurate Mechanism to Find Fuzzy Seed Matches in Genome Ana |
| 2112.13742 | arxiv | arXiv id_list | Hamtajoo: A Persian Plagiarism Checker for Academic Manuscripts |
| 2201.06573 | arxiv | arXiv id_list | PerPaDa: A Persian Paraphrase Dataset based on Implicit Crowdsourcing Data Collection |
| 2202.06539 | arxiv | arXiv id_list | Deduplicating Training Data Mitigates Privacy Risks in Language Models |
| 2203.07167 | arxiv | arXiv id_list | Dataset and Case Studies for Visual Near-Duplicates Detection in the Context of Social Media |
| 2203.13430 | arxiv | arXiv id_list | Plagiarism Detection in the Bengali Language: A Text Similarity-Based Approach |
| 2204.01028 | arxiv | arXiv id_list | MSCCD: Grammar Pluggable Clone Detection Based on ANTLR Parser Generation |
| 2204.07501 | arxiv | arXiv id_list | Evaluating few shot and Contrastive learning Methods for Code Clone Detection |
| 2204.11209 | arxiv | arXiv id_list | Hierarchical Locality Sensitive Hashing for Structured Data: A Survey |
| 2205.04913 | arxiv | arXiv id_list | Cross-Language Source Code Clone Detection Using Deep Learning with InferCode |
| 2206.04730 | arxiv | arXiv id_list | A Neural Network Architecture for Program Understanding Inspired by Human Behaviors |
| 2206.08726 | arxiv | arXiv id_list | Evaluation of Contrastive Learning with Various Code Representations for Code Clone Detection |
| 2206.12664 | arxiv | arXiv id_list | Evaluation of Semantic Answer Similarity Metrics |
| 2208.12588 | arxiv | arXiv id_list | Generalizability of Code Clone Detection on CodeBERT |
| 2209.10031 | arxiv | arXiv id_list | The exact probability law for the approximated similarity from the Minhashing method |
| 2210.17203 | arxiv | arXiv id_list | Using Locality-sensitive Hashing for Rendezvous Search |
| 2211.09374 | arxiv | arXiv id_list | Execution-based Evaluation for Data Science Code Generation Models |
| 2211.11902 | arxiv | arXiv id_list | Evaluating the Knowledge Dependency of Questions |
| 2211.16259 | arxiv | arXiv id_list | Measuring the Measuring Tools: An Automatic Evaluation of Semantic Metrics for Text Corpora |
| 2302.04335 | arxiv | arXiv id_list | Will ChatGPT get you caught? Rethinking of Plagiarism Detection |
| 2302.14785 | arxiv | arXiv id_list | Joint Representations of Text and Knowledge Graphs for Retrieval and Evaluation |
| 2303.08179 | arxiv | arXiv id_list | MEDBERT.de: A Comprehensive German BERT Model for the Medical Domain |
| 2305.10160 | arxiv | arXiv id_list | Stop Uploading Test Data in Plain Text: Practical Strategies for Mitigating Data Contamination b |
| 2305.13193 | arxiv | arXiv id_list | TEIMMA: The First Content Reuse Annotator for Text, Images, and Math |
| 2305.13693 | arxiv | arXiv id_list | Automated Metrics for Medical Multi-Document Summarization Disagree with Human Evaluations |
| 2305.16626 | arxiv | arXiv id_list | Evaluation of Question Generation Needs More References |
| 2305.17310 | arxiv | arXiv id_list | DotHash: Estimating Set Similarity Metrics for Link Prediction and Document Deduplication |
| 2306.02563 | arxiv | arXiv id_list | Large-Scale Distributed Learning via Private On-Device Locality-Sensitive Hashing |
| 2306.07674 | arxiv | arXiv id_list | Differentially Private One Permutation Hashing and Bin-wise Consistent Weighted Sampling |
| 2306.08122 | arxiv | arXiv id_list | Beyond Black Box AI-Generated Plagiarism Detection: From Sentence to Document Level |
| 2307.05663 | arxiv | arXiv id_list | Objaverse-XL: A Universe of 10M+ 3D Objects |
| 2308.00721 | arxiv | arXiv id_list | A Pre-trained Data Deduplication Model based on Active Learning |
| 2308.01191 | arxiv | arXiv id_list | Towards Understanding the Capability of Large Language Models on Code Clone Detection: A Survey |
| 2308.11240 | arxiv | arXiv id_list | Minwise-Independent Permutations with Insertion and Deletion of Features |
| 2308.12134 | arxiv | arXiv id_list | DarkDiff: Explainable web page similarity of TOR onion sites |
| 2308.12842 | arxiv | arXiv id_list | Text Similarity from Image Contents using Statistical and Semantic Analysis Techniques |
| 2308.13754 | arxiv | arXiv id_list | ZC3: Zero-Shot Cross-Language Code Clone Detection |
| 2309.04823 | arxiv | arXiv id_list | FaNS: a Facet-based Narrative Similarity Metric |
| 2309.05610 | arxiv | arXiv id_list | Privacy Side Channels in Machine Learning Systems |
| 2309.09400 | arxiv | arXiv id_list | CulturaX: A Cleaned, Enormous, and Multilingual Dataset for Large Language Models in 167 Languag |
| 2309.12250 | arxiv | arXiv id_list | SQUARE: Automatic Question Answering Evaluation using Multiple Positive and Negative References |
| 2309.13080 | arxiv | arXiv id_list | SPICED: News Similarity Detection Dataset with Multiple Topics and Complexity Levels |
| 2310.06703 | arxiv | arXiv id_list | DeepLSH: Deep Locality-Sensitive Hash Learning for Fast and Efficient Near-Duplicate Crash Repor |
| 2310.10628 | arxiv | arXiv id_list | Data Contamination Through the Lens of Time |
| 2310.11593 | arxiv | arXiv id_list | Automated Evaluation of Personalized Text Generation using Large Language Models |
| 2310.15298 | arxiv | arXiv id_list | TaskDiff: A Similarity Metric for Task-Oriented Conversations |
| 2310.17589 | arxiv | arXiv id_list | An Open Source Data Contamination Report for Large Language Models |
| 2310.18018 | arxiv | arXiv id_list | NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark |
| 2311.07277 | arxiv | arXiv id_list | AdaCCD: Adaptive Semantic Contrasts Discovery Based Cross Lingual Adaptation for Code Clone Dete |
| 2311.08778 | arxiv | arXiv id_list | Gitor: Scalable Code Clone Detection by Building Global Sample Graph |
| 2311.09783 | arxiv | arXiv id_list | Investigating Data Contamination in Modern Benchmarks for Large Language Models |
| 2311.14898 | arxiv | arXiv id_list | HongTu: Scalable Full-Graph GNN Training on Multiple GPUs (via communication-optimized CPU data  |
| 2311.17264 | arxiv | arXiv id_list | RETSim: Resilient and Efficient Text Similarity |
| 2312.12343 | arxiv | arXiv id_list | LatestEval: Addressing Data Contamination in Language Model Evaluation through Dynamic and Time- |
| 2401.09885 | arxiv | arXiv id_list | Source Code Clone Detection Using Unsupervised Similarity Measures |
| 2401.13802 | arxiv | arXiv id_list | Investigating the Efficacy of Large Language Models for Code Clone Detection |
| 2401.16969 | arxiv | arXiv id_list | Taxonomy of Mathematical Plagiarism |
| 2401.18064 | arxiv | arXiv id_list | Neural Locality Sensitive Hashing for Entity Blocking |
| 2402.03927 | arxiv | arXiv id_list | Leak, Cheat, Repeat: Data Contamination and Evaluation Malpractices in Closed-Source LLMs |
| 2402.13433 | arxiv | arXiv id_list | Structured Tree Alignment for Evaluation of (Speech) Constituency Parsing |
| 2402.15938 | arxiv | arXiv id_list | Generalization or Memorization: Data Contamination and Trustworthy Evaluation for Large Language |
| 2403.06350 | arxiv | arXiv id_list | IndicLLMSuite: A Blueprint for Creating Pre-training and Fine-Tuning Datasets for Indian Languag |
| 2403.12958 | arxiv | arXiv id_list | Dated Data: Tracing Knowledge Cutoffs in Large Language Models |
| 2403.15747 | arxiv | arXiv id_list | CodeShell Technical Report |
| 2403.18202 | arxiv | arXiv id_list | TGMM: Combining Parse Tree with GPU for Scalable Multilingual and Multi-Granularity Code Clone D |
| 2404.01582 | arxiv | arXiv id_list | BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection System |
| 2404.03555 | arxiv | arXiv id_list | From News to Summaries: Building a Hungarian Corpus for Extractive and Abstractive Summarization |
| 2404.05898 | arxiv | arXiv id_list | Inexact Simplification of Symbolic Regression Expressions with Locality-sensitive Hashing |
| 2404.08817 | arxiv | arXiv id_list | Revisiting Code Similarity Evaluation with Abstract Syntax Tree Edit Distance |
| 2405.00428 | arxiv | arXiv id_list | CC2Vec: Combining Typed Tokens with Contrastive Learning for Effective Code Clone Detection |
| 2405.06807 | arxiv | arXiv id_list | Execution-Based Evaluation of Natural Language to Bash and PowerShell for Incident Remediation |
| 2405.11930 | arxiv | arXiv id_list | Data Contamination Calibration for Black-box LLMs |
| 2405.15523 | arxiv | arXiv id_list | The Mosaic Memory of Large Language Models |
| 2405.16930 | arxiv | arXiv id_list | From Obstacles to Resources: Semi-supervised Learning Faces Synthetic Data Contamination |
| 2405.19711 | arxiv | arXiv id_list | SimiSketch: Efficiently Estimating Similarity of streaming Multisets |
| 2406.04244 | arxiv | arXiv id_list | Benchmark Data Contamination of Large Language Models: A Survey |
| 2406.11813 | arxiv | arXiv id_list | How Do Large Language Models Acquire Factual Knowledge During Pretraining? |
| 2406.14644 | arxiv | arXiv id_list | Unveiling the Spectrum of Data Contamination in Language Models: A Survey from Detection to Reme |
| 2406.16288 | arxiv | arXiv id_list | PlagBench: Exploring the Duality of Large Language Models in Plagiarism Generation and Detection |
| 2407.02402 | arxiv | arXiv id_list | Assessing the Code Clone Detection Capability of Large Language Models |
| 2407.02596 | arxiv | arXiv id_list | Towards More Realistic Extraction Attacks: An Adversarial Perspective |
| 2407.11470 | arxiv | arXiv id_list | Beyond Correctness: Benchmarking Multi-dimensional Code Generation for Large Language Models |
| 2407.13105 | arxiv | arXiv id_list | Survey on Plagiarism Detection in Large Language Models: The Impact of ChatGPT and Gemini on Aca |
| 2407.21614 | arxiv | arXiv id_list | Maintaining $k$-MinHash Signatures over Fully-Dynamic Data Streams with Recovery |
| 2408.04430 | arxiv | arXiv id_list | The Struggles of LLMs in Cross-lingual Code Clone Detection |
| 2408.04645 | arxiv | arXiv id_list | Evaluating the Impact of Advanced LLM Techniques on AI-Lecture Tutors for a Robotics Course |
| 2408.07321 | arxiv | arXiv id_list | VERCATION: Precise Vulnerable Open-source Software Version Identification based on Static Analys |
| 2409.08519 | arxiv | arXiv id_list | Fast Comparative Analysis of Merge Trees Using Locality Sensitive Hashing |
| 2409.09927 | arxiv | arXiv id_list | Towards Data Contamination Detection for Modern Large Language Models: Limitations, Inconsistenc |
| 2410.03600 | arxiv | arXiv id_list | Efficiently Identifying Watermarked Segments in Mixed-Source Texts |
| 2410.03817 | arxiv | arXiv id_list | A novel TLS-based Fingerprinting approach that combines feature expansion and similarity mapping |
| 2410.15005 | arxiv | arXiv id_list | CAP: Data Contamination Detection via Consistency Amplification |
| 2410.18966 | arxiv | arXiv id_list | Does Data Contamination Detection Work (Well) for LLMs? A Survey and Evaluation on Detection Ass |
| 2411.03823 | arxiv | arXiv id_list | Both Text and Images Leaked! A Systematic Analysis of Data Contamination in Multimodal LLM |
| 2411.03923 | arxiv | arXiv id_list | Evaluation data contamination in LLMs: how do we measure it and (when) does it matter? |
| 2411.04905 | arxiv | arXiv id_list | OpenCoder: The Open Cookbook for Top-Tier Code Large Language Models |
| 2411.05706 | arxiv | arXiv id_list | Image2Text2Image: A Novel Framework for Label-Free Evaluation of Image-to-Text Generation with T |
| 2411.08446 | arxiv | arXiv id_list | LSH-MoE: Communication-efficient MoE Training via Locality-Sensitive Hashing |
| 2411.09558 | arxiv | arXiv id_list | Adaptive Deviation Learning for Visual Anomaly Detection with Data Contamination |
| 2412.06241 | arxiv | arXiv id_list | Plagiarism Detection Using Machine Learning |
| 2412.13670 | arxiv | arXiv id_list | AntiLeakBench: Preventing Data Contamination by Automatically Constructing Benchmarks with Updat |
| 2412.18291 | arxiv | arXiv id_list | DeepCRCEval: Revisiting the Evaluation of Code Review Comment Generation |
| 2501.01046 | arxiv | arXiv id_list | SEDD: Scalable and Efficient Dataset Deduplication with GPUs |
| 2501.02628 | arxiv | arXiv id_list | Cracks in The Stack: Hidden Vulnerabilities and Licensing Risks in LLM Pre-Training Datasets |
| 2501.03212 | arxiv | arXiv id_list | Leveraging Explainable AI for LLM Text Attribution: Differentiating Human-Written and Multiple L |
| 2501.04591 | arxiv | arXiv id_list | Quantum-inspired Embeddings Projection and Similarity Metrics for Representation Learning |
| 2501.05260 | arxiv | arXiv id_list | Enhancing Plagiarism Detection in Marathi with a Weighted Ensemble of TF-IDF and BERT Embeddings |
| 2501.11171 | arxiv | arXiv id_list | Counteracting temporal attacks in Video Copy Detection |
| 2501.13983 | arxiv | arXiv id_list | AdEval: Alignment-based Dynamic Evaluation to Mitigate Data Contamination in Large Language Mode |
| 2501.17581 | arxiv | arXiv id_list | CSEval: Towards Automated, Multi-Dimensional, and Reference-Free Counterspeech Evaluation using  |
| 2501.18771 | arxiv | arXiv id_list | Overestimation in LLM Evaluation: A Controlled Large-Scale Study on Data Contamination's Impact  |
| 2501.18998 | arxiv | arXiv id_list | Adversarial Attacks on AI-Generated Text Detection Models: A Token Probability-Based Approach Us |
| 2502.02494 | arxiv | arXiv id_list | Analyzing Similarity Metrics for Data Selection for Language Model Pretraining |
| 2502.05239 | arxiv | arXiv id_list | Enhancing Knowledge Graph Construction: Evaluating with Emphasis on Hallucination, Omission, and |
| 2502.08666 | arxiv | arXiv id_list | Hallucination, Monofacts, and Miscalibration: An Empirical Investigation |
| 2502.09188 | arxiv | arXiv id_list | Matina: A Large-Scale 73B Token Persian Text Corpus |
| 2502.14425 | arxiv | arXiv id_list | A Survey on Data Contamination for Large Language Models |
| 2502.17521 | arxiv | arXiv id_list | Recent Advances in Large Langauge Model Benchmarks against Data Contamination: From Static to Dy |
| 2502.20936 | arxiv | arXiv id_list | WebFAQ: A Multilingual Collection of Natural Q&A Datasets for Dense Retrieval |
| 2503.04149 | arxiv | arXiv id_list | Dynamic Benchmarking of Reasoning Capabilities in Code Large Language Models Under Data Contamin |
| 2503.06643 | arxiv | arXiv id_list | Is Your Benchmark Still Useful? Dynamic Benchmarking for Code Language Models |
| 2503.13572 | arxiv | arXiv id_list | VeriContaminated: Assessing LLM-Driven Verilog Coding for Data Contamination |
| 2503.14043 | arxiv | arXiv id_list | Beyond Next Token Probabilities: Learnable, Fast Detection of Hallucinations and Data Contaminat |
| 2503.16402 | arxiv | arXiv id_list | The Emperor's New Clothes in Benchmarking? A Rigorous Examination of Mitigation Strategies for L |
| 2504.00638 | arxiv | arXiv id_list | Impact of Data Duplication on Deep Neural Network-Based Image Classifiers: Robust vs. Standard M |
| 2504.02172 | arxiv | arXiv id_list | LogLSHD: Fast Log Parsing with Locality-Sensitive Hashing and Dynamic Time Warping |
| 2504.16286 | arxiv | arXiv id_list | The Paradox of Poetic Intent in Back-Translation: Evaluating the Quality of Large Language Model |
| 2504.17066 | arxiv | arXiv id_list | Whence Is A Model Fair? Fixing Fairness Bugs via Propensity Score Matching |
| 2505.11683 | arxiv | arXiv id_list | Evaluating Design Decisions for Dual Encoder-based Entity Disambiguation |
| 2505.17844 | arxiv | arXiv id_list | Locality-Sensitive Hashing for Efficient Hard Negative Sampling in Contrastive Learning |
| 2506.07202 | arxiv | arXiv id_list | Reasoning Multimodal Large Language Model: Data Contamination and Dynamic Evaluation |
| 2506.10995 | arxiv | arXiv id_list | Evaluating Small-Scale Code Models for Code Clone Detection |
| 2506.13160 | arxiv | arXiv id_list | CertDW: Towards Certified Dataset Ownership Verification via Conformal Calibration |
| 2506.14470 | arxiv | arXiv id_list | AST-Enhanced or AST-Overloaded? The Surprising Impact of Hybrid Graph Representations on Code Cl |
| 2506.19881 | arxiv | arXiv id_list | Blameless Users in a Clean Room: Defining Copyright Protection for Generative Models |
| 2506.20920 | arxiv | arXiv id_list | FineWeb2: One Pipeline to Scale Them All -- Adapting Pre-Training Data Processing to Every Langu |
| 2507.09863 | arxiv | arXiv id_list | Towards Realistic and Interpretable Market Simulations: Factorizing Financial Power Law using Op |
| 2507.10532 | arxiv | arXiv id_list | Reasoning or Memorization? Unreliable Results of Reinforcement Learning Due to Data Contaminatio |
| 2507.11405 | arxiv | arXiv id_list | DCR: Quantifying Data Contamination in LLMs Evaluation |
| 2507.15226 | arxiv | arXiv id_list | Code Clone Detection via an AlphaFold-Inspired Framework |
| 2507.22936 | arxiv | arXiv id_list | Evaluating Large Language Models (LLMs) in Financial NLP: A Comparative Study on Financial Repor |
| 2508.01357 | arxiv | arXiv id_list | HyClone: Bridging LLM Understanding and Dynamic Execution for Semantic Code Clone Detection |
| 2508.03435 | arxiv | arXiv id_list | StoneDetector: Conventional and versatile code clone detection for Java |
| 2508.05640 | arxiv | arXiv id_list | Request-Only Optimization for Recommendation Systems |
| 2508.06495 | arxiv | arXiv id_list | Semi-automated Fact-checking in Portuguese: Corpora Enrichment using Retrieval with Claim extrac |
| 2508.09346 | arxiv | arXiv id_list | How Safe Will I Be Given What I Saw? Calibrated Prediction of Safety Chances for Image-Controlle |
| 2508.10906 | arxiv | arXiv id_list | PersonaTwin: A Multi-Tier Prompt Conditioning Framework for Generating and Evaluating Personaliz |
| 2508.13180 | arxiv | arXiv id_list | Search-Time Data Contamination |
| 2508.14062 | arxiv | arXiv id_list | Assessing and Mitigating Data Memorization Risks in Fine-Tuned Large Language Models |
| 2509.02033 | arxiv | arXiv id_list | StructCoh: Structured Contrastive Learning for Context-Aware Text Semantic Matching |
| 2509.05608 | arxiv | arXiv id_list | BinaryShield: Cross-Service Threat Intelligence in LLM Services using Privacy-Preserving Fingerp |
| 2509.18782 | arxiv | arXiv id_list | Emergence of power laws in hierarchical dynamics on multi-level graphs |
| 2509.19323 | arxiv | arXiv id_list | Magnitude Matters: a Superior Class of Similarity Metrics for Holistic Semantic Understanding |
| 2509.22978 | arxiv | arXiv id_list | Towards Human-interpretable Explanation in Code Clone Detection using LLM-based Post Hoc Explain |
| 2509.24420 | arxiv | arXiv id_list | A Data-Centric Perspective on the Influence of Image Data Quality in Machine Learning Models |
| 2510.09259 | arxiv | arXiv id_list | Detecting Data Contamination from Reinforcement Learning Post-training for Large Language Models |
| 2510.15480 | arxiv | arXiv id_list | Selecting and Combining Large Language Models for Scalable Code Clone Detection |
| 2510.21182 | arxiv | arXiv id_list | KBE-DME: Dynamic Multimodal Evaluation via Knowledge Enhanced Benchmark Evolution |
| 2510.23169 | arxiv | arXiv id_list | MATCH: Task-Driven Code Evaluation through Contrastive Learning |
| 2510.24241 | arxiv | arXiv id_list | MAGNET: A Multi-Graph Attentional Network for Code Clone Detection |
| 2510.27055 | arxiv | arXiv id_list | Detecting Data Contamination in LLMs via In-Context Learning |
| 2511.01176 | arxiv | arXiv id_list | An Empirical Study of LLM-Based Code Clone Detection |
| 2511.16576 | arxiv | arXiv id_list | PolyMinHash: Efficient Area-Based MinHashing of Polygons for Approximate Nearest Neighbor Search |
| 2512.03310 | arxiv | arXiv id_list | Randomized Masked Finetuning: An Efficient Way to Mitigate Memorization of PIIs in LLMs |
| 2512.16816 | arxiv | arXiv id_list | Toward Systematic Counterfactual Fairness Evaluation of Large Language Models: The CAFFE Framewo |
| 2512.23239 | arxiv | arXiv id_list | RS-Prune: Training-Free Data Pruning at High Ratios for Efficient Remote Sensing Diffusion Found |
| 2512.23504 | arxiv | arXiv id_list | Automatic Detection of Complex Quotation Patterns in Aggadic Literature |
| 2601.10455 | arxiv | arXiv id_list | SurgGoal: Rethinking Surgical Planning Evaluation via Goal-Satisfiability |
| 2601.14994 | arxiv | arXiv id_list | Obscuring Data Contamination Through Translation: Evidence from Arabic Corpora |
| 2601.21083 | arxiv | arXiv id_list | OpenSec: Measuring Incident Response Agent Calibration Under Adversarial Evidence |
| 2601.22913 | arxiv | arXiv id_list | Multi-Cue Anomaly Detection and Localization under Data Contamination |
| 2602.09147 | arxiv | arXiv id_list | Overview of PAN 2026: Voight-Kampff Generative AI Detection, Text Watermarking, Multi-Author Wri |
| 2602.22827 | arxiv | arXiv id_list | TARAZ: Persian Short-Answer Question Benchmark for Cultural Evaluation of Language Models |
| 2603.00633 | arxiv | arXiv id_list | FDR Control for Complex-Valued Data with Application in Single Snapshot Multi-Source Detection a |
| 2603.00958 | arxiv | arXiv id_list | S-VoCAL: A Dataset and Evaluation Framework for Inferring Speaking Voice Character Attributes in |
| 2603.04413 | arxiv | arXiv id_list | Simulating Meaning, Nevermore! Introducing ICR: A Semiotic-Hermeneutic Metric for Evaluating Mea |
| 2603.09998 | arxiv | arXiv id_list | Automated evaluation of LLMs for effective machine translation of Mandarin Chinese to English |
| 2603.14217 | arxiv | arXiv id_list | Rethinking Evaluation in Retrieval-Augmented Personalized Dialogue: A Cognitive and Linguistic P |
| 2603.15004 | arxiv | arXiv id_list | TriFusion-LLM: Prior-Guided Multimodal Fusion with LLM Arbitration for Fine-grained Code Clone D |
| 2603.28838 | arxiv | arXiv id_list | GMA-SAWGAN-GP: A Novel Data Generative Framework to Enhance IDS Detection Performance |
| 2603.29937 | arxiv | arXiv id_list | Rewrite the News: Tracing Editorial Reuse Across News Agencies |
| 2604.13783 | arxiv | arXiv id_list | Zero-shot Evaluation of Deep Learning for Java Code Clone Detection |
| 2604.16426 | arxiv | arXiv id_list | Functional Similarity Metric for Neural Networks: Overcoming Parametric Ambiguity via Activation |
| 2604.22640 | arxiv | arXiv id_list | Quality-Driven Selective Mutation for Deep Learning |
| 2605.02860 | arxiv | arXiv id_list | Standing on the Shoulders of Giants: Stabilized Knowledge Distillation for Cross--Language Code  |
| 2605.07153 | arxiv | arXiv id_list | Beyond Reasoning: Reinforcement Learning Unlocks Parametric Knowledge in LLMs |
| 2605.09236 | arxiv | arXiv id_list | Matching Meaning at Scale: Evaluating Semantic Search for 18th-Century Intellectual History thro |
| 2605.11551 | arxiv | arXiv id_list | VNDUQE: Information-Theoretic Novelty Detection using Deep Variational Information Bottleneck |
| 2605.21856 | arxiv | arXiv id_list | The Illusion of Reasoning: Exposing Evasive Data Contamination in LLMs via Zero-CoT Truncation |
| 2605.30642 | arxiv | arXiv id_list | Diffusion Models Preferentially Memorize Prototypical Examples or: Why Does My Diffusion Model L |
| 2606.24998 | arxiv | arXiv id_list | Internal Data Repetition Destroys Language Models |
| 2606.25272 | arxiv | arXiv id_list | Semantic Code Clone Detection: Are We There Yet? |
| 2606.31272 | arxiv | arXiv id_list | The Decomposition Is the Fingerprint: Per-Component Identity for Agent Skills |
| 2607.01842 | arxiv | arXiv id_list | Understanding Software Defect Prediction: A Large-scale Empirical Study Across Uncertainty Quant |
| 2607.02577 | arxiv | arXiv id_list | Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluation |
| 2607.08382 | arxiv | arXiv id_list | H3D: Benchmarking Unsupervised Text Hashing for Fine-Grained Document Deduplication |
| 2607.08700 | arxiv | arXiv id_list | Do You Need a Frontier Model as a Citation Verifier? Benchmarking Rubric LLMs for Deep-Research  |
| 2607.10020 | arxiv | arXiv id_list | FindMyText: Robust, Scalable Detection of Text Containment in Large Web-Crawled Corpora |
| 2607.11591 | arxiv | arXiv id_list | Similarity-Guided Curriculum Fine-Tuning of LLMs for Neural Architecture Synthesis |
| 2607.17596 | arxiv | arXiv id_list | E-Values For Multiplicity Control In Multiverse Analysis |
| 2607.18027 | arxiv | arXiv id_list | L1 Augmented Attention as an Improved Vector Similarity Metric |
| 2607.19368 | arxiv | arXiv id_list | Spectral-LSH: Sub-Quadratic Prompt Compression via Krylov-Projected Locality-Sensitive Hashing |
| 2608.00144 | arxiv | arXiv id_list | Leak It: Per-Document Extraction Beyond Aggregate Membership Inference |
| 2608.03199 | arxiv | arXiv id_list | SieveIVF: Threshold-Aware IVF Execution for Large-Scale Training Data Deduplication |
| 2608.03859 | arxiv | arXiv id_list | Beyond Representational Similarity: Source-Conditioned Description-Length Gain for Generative Pl |
| 2608.15090 | arxiv | arXiv id_list | Distribution-free false-alarm calibration and chance-corrected spatial evaluation for industrial |
| 2608.22383 | arxiv | arXiv id_list | Learning Spectral Representations of Code through Latent Graph Learning for Generalizable Cross- |
| 2608.23547 | arxiv | arXiv id_list | Robustness of Anomaly Detection Models for Industrial Control Systems under Training-Time Data C |
| 2608.30023 | arxiv | arXiv id_list | Demand-Side Measurement for Generative Engine Optimization: Constructing and Validating a Millio |
| 2608.30175 | arxiv | arXiv id_list | Benchmarking Peptide-Protein Affinity Prediction Across Peptide and Target Shifts |
| 2609.11023 | arxiv | arXiv id_list | RCL: A Retrieval-Confidence Layer for Detecting Insufficient Context in Enterprise Retrieval-Aug |
| 2609.15058 | arxiv | arXiv id_list | Fast Label-Filtering Approximate Nearest Neighbor Search via Progressive Label Set Stratificatio |
| 2609.17338 | arxiv | arXiv id_list | Type-IV Code Clone Detection via Layer-Wise Non-Contrastive Representation Learning |
| 2609.24980 | arxiv | arXiv id_list | Residual Community Prototypes Under-Reject Held-Out Malware Families in FCG-MFD |
| 2609.29507 | arxiv | arXiv id_list | What a Cross-Model Fixed-Point Census Can and Cannot Arbitrate About Repetition |
| 2609.31262 | arxiv | arXiv id_list | Deduplication-while-Training: A Resilient Paradigm for Privacy-Preserving Cross-Client Deduplica |
| 2609.36161 | arxiv | arXiv id_list | From Dead Code and Static Requirements to Working Engines: Software Revival with Coding Agents |
| 2609.38012 | arxiv | arXiv id_list | A Function-level Dataset of Vulnerable and Fixed Source Code in JavaScript and TypeScript |
| 2609.39623 | arxiv | arXiv id_list | Semantic Watermarking for Malicious Image Manipulation Detection |
| 2610.00421 | arxiv | arXiv id_list | Scores That Hold, Benchmarks That Leak: Measuring Dataset Contamination in Public Brain-Tumor MR |
| 2610.05387 | arxiv | arXiv id_list | GNN-CB: A Graph Neural Network Competition Benchmark for Human and LLM Evaluation |
