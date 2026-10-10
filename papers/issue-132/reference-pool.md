# Reference pool -- issue #132

Every entry below was discovered by `refscan132.py` (never typed from memory) and checked
against a LIVE external record by comparing the returned TITLE with the stored title
(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a
remembered identifier can resolve to a DIFFERENT real paper, so the check is the title
comparison, not the HTTP status.

- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with
  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)
  and `works/<doi>` (verification)
- pool: 257 entries (241 arXiv, 16 Crossref)
- an entry whose title does not match its live record is dropped, never kept

| key | source | verified against | title |
|-----|--------|------------------|-------|
| 0909.4385 | arxiv | arXiv id_list | The meta book and size-dependent properties of written language |
| 0912.3959 | arxiv | arXiv id_list | Web Based Cross Language Plagiarism Detection |
| 10.1007/3-540-45123-4_1 | crossref | Crossref works/<doi> | Identifying and Filtering Near-Duplicate Documents |
| 10.1007/978-3-642-36973-5_66 | crossref | Crossref works/<doi> | Cross-Language Plagiarism Detection Using a Multilingual Semantic Network |
| 10.1016/j.scico.2009.02.007 | crossref | Crossref works/<doi> | Comparison and evaluation of code clone detection techniques and tools: A qualitative approach |
| 10.1016/s0169-7552(97)00031-7 | crossref | Crossref works/<doi> | Syntactic clustering of the Web |
| 10.1108/00220410410560573 | crossref | Crossref works/<doi> | A statistical interpretation of term specificity and its application in retrieval |
| 10.1109/ams.2011.19 | crossref | Crossref works/<doi> | Survey of Plagiarism Detection Methods |
| 10.1109/sequen.1997.666900 | crossref | Crossref works/<doi> | On the resemblance and containment of documents |
| 10.1111/j.2517-6161.1995.tb02031.x | crossref | Crossref works/<doi> | Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing |
| 10.1145/1141277.1141534 | crossref | Crossref works/<doi> | Template detection for large scale search engines |
| 10.1145/1242572.1242592 | crossref | Crossref works/<doi> | Detecting near-duplicates for web crawling |
| 10.1145/2884781.2884877 | crossref | Crossref works/<doi> | SourcererCC: scaling code clone detection to big-code |
| 10.1145/509907.509965 | crossref | Crossref works/<doi> | Similarity estimation techniques from rounding algorithms |
| 10.1145/872757.872770 | crossref | Crossref works/<doi> | Winnowing: local algorithms for document fingerprinting |
| 10.18653/v1/w18-2502 | crossref | Crossref works/<doi> | Stop Word Lists in Free Open-source Software Packages |
| 10.32614/cran.package.textcat | crossref | Crossref works/<doi> | textcat: N-Gram Based Text Categorization |
| 10.37200/ijpr/v24i1/pr200254 | crossref | Crossref works/<doi> | A Survey on Plagiarism Detection Techniques |
| 1001.3487 | arxiv | arXiv id_list | Features Based Text Similarity Detection |
| 1003.4065 | arxiv | arXiv id_list | Plagiarism Detection using ROUGE and WordNet |
| 1104.4723 | arxiv | arXiv id_list | Bayesian approach for near-duplicate image detection |
| 1204.0182 | arxiv | arXiv id_list | Hybrid Information Retrieval Model For Web Images |
| 1206.6606 | arxiv | arXiv id_list | A Sampling-based Tool for Plagiarism Detection in Student Texts |
| 1208.2486 | arxiv | arXiv id_list | `CodeAliker' - Plagiarism Detection on the Cloud |
| 1210.3729 | arxiv | arXiv id_list | Inference of Fine-grained Attributes of Bengali Corpus for Stylometry Detection |
| 1210.7678 | arxiv | arXiv id_list | Plagiarism Detection: Keeping Check on Misuse of Intellectual Property |
| 1212.2616 | arxiv | arXiv id_list | Languages cool as they expand: Allometric scaling and the decreasing need for new words |
| 1401.2258 | arxiv | arXiv id_list | Assessing Wikipedia-Based Cross-Language Retrieval Models |
| 1403.1310 | arxiv | arXiv id_list | AntiPlag: Plagiarism Detection on Electronic Submissions of Text Based Assignments |
| 1403.2871 | arxiv | arXiv id_list | Shape-Based Plagiarism Detection for Flowchart Figures in Texts |
| 1406.1143 | arxiv | arXiv id_list | Identifying Duplicate and Contradictory Information in Wikipedia |
| 1411.5732 | arxiv | arXiv id_list | A Joint Probabilistic Classification Model of Relevant and Irrelevant Sentences in Mathematical  |
| 1412.7782 | arxiv | arXiv id_list | Plagiarism Detection on Electronic Text based Assignments using Vector Space Model (ICIAfS14) |
| 1512.06448 | arxiv | arXiv id_list | SourcererCC: Scaling Code Clone Detection to Big Code |
| 1512.07046 | arxiv | arXiv id_list | News Across Languages - Cross-Lingual Document Similarity and Event Tracking |
| 1606.09403 | arxiv | arXiv id_list | Learning Crosslingual Word Embeddings without Bilingual Corpora |
| 1611.04122 | arxiv | arXiv id_list | Cross-lingual Dataless Classification for Languages with Small Wikipedia Presence |
| 1701.03227 | arxiv | arXiv id_list | Prior matters: simple and general methods for evaluating and improving topic quality in topic mo |
| 1702.01032 | arxiv | arXiv id_list | Semi-Supervised Spam Detection in Twitter Stream |
| 1702.03082 | arxiv | arXiv id_list | UsingWord Embedding for Cross-Language Plagiarism Detection |
| 1704.01346 | arxiv | arXiv id_list | CompiLIG at SemEval-2017 Task 1: Cross-Language Plagiarism Detection Methods for Semantic Textua |
| 1704.05617 | arxiv | arXiv id_list | Deduplication in a massive clinical note dataset |
| 1705.08828 | arxiv | arXiv id_list | Deep Investigation of Cross-Language Plagiarism Detection Methods |
| 1707.07182 | arxiv | arXiv id_list | Native Language Identification on Text and Speech |
| 1707.08349 | arxiv | arXiv id_list | Can string kernels pass the test of time in Native Language Identification? |
| 1707.09443 | arxiv | arXiv id_list | Bilingual Document Alignment with Latent Semantic Indexing |
| 1710.08615 | arxiv | arXiv id_list | Computational Social Scientist Beware: Simpson's Paradox in Behavioral Data |
| 1712.01813 | arxiv | arXiv id_list | Neural Cross-Lingual Entity Linking |
| 1712.02820 | arxiv | arXiv id_list | A Deep Network Model for Paraphrase Detection in Short Text Messages |
| 1712.08946 | arxiv | arXiv id_list | Judicious Judgment Meets Unsettling Updating: Dilation, Sure Loss, and Simpson's Paradox |
| 1712.10309 | arxiv | arXiv id_list | Methods for Detecting Paraphrase Plagiarism |
| 1801.02607 | arxiv | arXiv id_list | Web2Text: Deep Structured Boilerplate Removal |
| 1801.04385 | arxiv | arXiv id_list | Can you Trust the Trend: Discovering Simpson's Paradoxes in Social Data |
| 1804.07954 | arxiv | arXiv id_list | Automated essay scoring with string kernels and word embeddings |
| 1805.00879 | arxiv | arXiv id_list | Unsupervised Cross-Lingual Information Retrieval using Monolingual Data Only |
| 1805.03094 | arxiv | arXiv id_list | Using Simpson's Paradox to Discover Interesting Patterns in Behavioral Data |
| 1807.11057 | arxiv | arXiv id_list | NMT-based Cross-lingual Document Embeddings |
| 1810.03099 | arxiv | arXiv id_list | Multi-reference Cosine: A New Approach to Text Similarity Measurement in Large Collections |
| 1810.03102 | arxiv | arXiv id_list | A Fast Text Similarity Measure for Large Document Collections using Multi-reference Cosine and G |
| 1810.11903 | arxiv | arXiv id_list | Dynamic Thresholding Mechanisms for IR-Based Filtering in Efficient Source Code Plagiarism Detec |
| 1812.09617 | arxiv | arXiv id_list | Exploiting Cross-Lingual Subword Similarities in Low-Resource Document Classification |
| 1812.10464 | arxiv | arXiv id_list | Massively Multilingual Sentence Embeddings for Zero-Shot Cross-Lingual Transfer and Beyond |
| 1901.04216 | arxiv | arXiv id_list | Albanian Language Identification in Text Documents |
| 1903.03243 | arxiv | arXiv id_list | Context-Aware Cross-Lingual Mapping |
| 1905.02973 | arxiv | arXiv id_list | On the Feasibility of Automated Detection of Allusive Text Reuse |
| 1906.11761 | arxiv | arXiv id_list | Improving Academic Plagiarism Detection for STEM Documents by Analyzing Mathematical Content and |
| 1909.02827 | arxiv | arXiv id_list | Master your Metrics with Calibration |
| 1909.07950 | arxiv | arXiv id_list | Semantic Relatedness Based Re-ranker for Text Spotting |
| 1910.11005 | arxiv | arXiv id_list | Wasserstein distances for evaluating cross-lingual embeddings |
| 1911.00561 | arxiv | arXiv id_list | Twin-Finder: Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 1911.02991 | arxiv | arXiv id_list | Semi-Supervised Method using Gaussian Random Fields for Boilerplate Removal in Web Browsers |
| 1911.12637 | arxiv | arXiv id_list | Legal document retrieval across languages: topic hierarchies based on synsets |
| 1912.03570 | arxiv | arXiv id_list | From Boltzmann to Zipf through Shannon and Jaynes |
| 1912.05171 | arxiv | arXiv id_list | Character 3-gram Mover's Distance: An Effective Method for Detecting Near-duplicate Japanese-lan |
| 1912.12068 | arxiv | arXiv id_list | A Multi-cascaded Model with Data Augmentation for Enhanced Paraphrase Detection in Short Texts |
| 2001.04338 | arxiv | arXiv id_list | Extraction of Relevant Images for Boilerplate Removal in Web Browsers |
| 2002.04279 | arxiv | arXiv id_list | Testing of Support Tools for Plagiarism Detection |
| 2002.05204 | arxiv | arXiv id_list | Multi-threshold token-based code clone detection |
| 2002.11844 | arxiv | arXiv id_list | The hypergeometric test performs comparably to TF-IDF on standard text analysis tasks |
| 2003.07193 | arxiv | arXiv id_list | TF-IDFC-RF: A Novel Supervised Term Weighting Scheme |
| 2004.05265 | arxiv | arXiv id_list | Visual Spoofing in content based spam detection |
| 2004.05991 | arxiv | arXiv id_list | A Simple Approach to Learning Unsupervised Multilingual Embeddings |
| 2004.14294 | arxiv | arXiv id_list | Boilerplate Removal using a Neural Sequence Labeling Model |
| 2005.07356 | arxiv | arXiv id_list | Near-duplicate video detection featuring coupled temporal and perceptual visual structures and l |
| 2005.08229 | arxiv | arXiv id_list | Identification/Segmentation of Indian Regional Languages with Singular Value Decomposition based |
| 2005.12994 | arxiv | arXiv id_list | A Study of Neural Matching Models for Cross-lingual IR |
| 2006.02633 | arxiv | arXiv id_list | Stopwords in Technical Language Processing |
| 2006.09719 | arxiv | arXiv id_list | Automatically Ranked Russian Paraphrase Corpus for Text Generation |
| 2006.14505 | arxiv | arXiv id_list | Source Code Comments: Overlooked in the Realm of Code Clone Detection |
| 2006.15454 | arxiv | arXiv id_list | A Deep Reinforced Model for Zero-Shot Cross-Lingual Summarization with Bilingual Semantic Simila |
| 2007.05727 | arxiv | arXiv id_list | Feature Selection on Noisy Twitter Short Text Messages for Language Identification |
| 2009.05456 | arxiv | arXiv id_list | WOLI at SemEval-2020 Task 12: Arabic Offensive Language Identification on Different Twitter Data |
| 2010.01263 | arxiv | arXiv id_list | Multilevel Text Alignment with Cross-Document Attention |
| 2011.00701 | arxiv | arXiv id_list | Cross-Lingual Document Retrieval with Smooth Learning |
| 2101.03026 | arxiv | arXiv id_list | Scalable Cross-lingual Document Similarity through Language-specific Concept Hierarchies |
| 2102.10315 | arxiv | arXiv id_list | EXTRA: Explanation Ranking Datasets for Explainable Recommendation |
| 2104.08588 | arxiv | arXiv id_list | Sentence Alignment with Parallel Documents Facilitates Biomedical Machine Translation |
| 2104.12231 | arxiv | arXiv id_list | Model-based metrics: Sample-efficient estimates of predictive model subpopulation performance |
| 2105.11246 | arxiv | arXiv id_list | Cross-lingual Text Classification with Heterogeneous Graph Neural Network |
| 2105.11933 | arxiv | arXiv id_list | Integrated Reasoning Engine for Pointer-related Code Clone Detection |
| 2105.12068 | arxiv | arXiv id_list | Taxonomy of academic plagiarism methods |
| 2106.00734 | arxiv | arXiv id_list | Post-mortem on a deep learning contest: a Simpson's paradox and the complementary roles of scale |
| 2106.05764 | arxiv | arXiv id_list | Analyzing Non-Textual Content Elements to Detect Academic Plagiarism |
| 2109.02789 | arxiv | arXiv id_list | Mixed Attention Transformer for Leveraging Word-Level Knowledge to Neural Cross-Lingual Informat |
| 2110.01092 | arxiv | arXiv id_list | Towards Informative Tagging of Code Fragments to Support the Investigation of Code Clones |
| 2110.08343 | arxiv | arXiv id_list | Hyperseed: Unsupervised Learning with Vector Symbolic Architectures |
| 2110.10493 | arxiv | arXiv id_list | On the Effectiveness of Clone Detection for Detecting IoT-related Vulnerable Clones |
| 2111.10864 | arxiv | arXiv id_list | The Impact of Main Content Extraction on Near-Duplicate Detection |
| 2111.14183 | arxiv | arXiv id_list | Code Clone Detection based on Event Embedding and Event Dependency |
| 2111.15278 | arxiv | arXiv id_list | Bilingual Topic Models for Comparable Corpora |
| 2112.13742 | arxiv | arXiv id_list | Hamtajoo: A Persian Plagiarism Checker for Academic Manuscripts |
| 2201.03423 | arxiv | arXiv id_list | A Survey of Plagiarism Detection Systems: Case of Use with English, French and Arabic Languages |
| 2201.06517 | arxiv | arXiv id_list | Demographic Confounding Causes Extreme Instances of Lifestyle Politics on Facebook |
| 2201.06573 | arxiv | arXiv id_list | PerPaDa: A Persian Paraphrase Dataset based on Implicit Crowdsourcing Data Collection |
| 2203.04831 | arxiv | arXiv id_list | Automatic Language Identification for Celtic Texts |
| 2203.07167 | arxiv | arXiv id_list | Dataset and Case Studies for Visual Near-Duplicates Detection in the Context of Social Media |
| 2203.13430 | arxiv | arXiv id_list | Plagiarism Detection in the Bengali Language: A Text Similarity-Based Approach |
| 2204.01028 | arxiv | arXiv id_list | MSCCD: Grammar Pluggable Clone Detection Based on ANTLR Parser Generation |
| 2204.03062 | arxiv | arXiv id_list | Abusive and Threatening Language Detection in Urdu using Supervised Machine Learning and Feature |
| 2204.03064 | arxiv | arXiv id_list | The 2021 Urdu Fake News Detection Task using Supervised Machine Learning and Feature Combination |
| 2204.07501 | arxiv | arXiv id_list | Evaluating few shot and Contrastive learning Methods for Code Clone Detection |
| 2205.04913 | arxiv | arXiv id_list | Cross-Language Source Code Clone Detection Using Deep Learning with InferCode |
| 2205.15494 | arxiv | arXiv id_list | Certifying Some Distributional Fairness with Subpopulation Decomposition |
| 2206.04730 | arxiv | arXiv id_list | A Neural Network Architecture for Program Understanding Inspired by Human Behaviors |
| 2206.08726 | arxiv | arXiv id_list | Evaluation of Contrastive Learning with Various Code Representations for Code Clone Detection |
| 2208.02252 | arxiv | arXiv id_list | GROWN+UP: A Graph Representation Of a Webpage Network Utilizing Pre-training |
| 2208.12588 | arxiv | arXiv id_list | Generalizability of Code Clone Detection on CodeBERT |
| 2209.06378 | arxiv | arXiv id_list | RMExplorer: A Visual Analytics Approach to Explore the Performance and the Fairness of Disease R |
| 2209.14613 | arxiv | arXiv id_list | Fair admission risk prediction with proportional multicalibration |
| 2210.04600 | arxiv | arXiv id_list | YFACC: A Yorùbá speech-image dataset for cross-lingual keyword localisation through visual groun |
| 2210.07755 | arxiv | arXiv id_list | Simpson's Paradox in Recommender Fairness: Reconciling differences between per-user and aggregat |
| 2211.12364 | arxiv | arXiv id_list | Method for Determining the Similarity of Text Documents for the Kazakh language, Taking Into Acc |
| 2302.04335 | arxiv | arXiv id_list | Will ChatGPT get you caught? Rethinking of Plagiarism Detection |
| 2302.07185 | arxiv | arXiv id_list | When mitigating bias is unfair: multiplicity and arbitrariness in algorithmic group fairness |
| 2302.14261 | arxiv | arXiv id_list | Augmented Transformers with Adaptive n-grams Embedding for Multilingual Scene Text Recognition |
| 2303.17566 | arxiv | arXiv id_list | Non-Invasive Fairness in Learning through the Lens of Data Drift |
| 2304.02780 | arxiv | arXiv id_list | A Transformer-Based Deep Learning Approach for Fairly Predicting Post-Liver Transplant Risk Fact |
| 2304.12155 | arxiv | arXiv id_list | The African Stopwords project: curating stopwords for African languages |
| 2304.12191 | arxiv | arXiv id_list | "Genlangs" and Zipf's Law: Do languages generated by ChatGPT statistically look human? |
| 2305.03712 | arxiv | arXiv id_list | Statistical Inference for Fairness Auditing |
| 2305.12622 | arxiv | arXiv id_list | Evaluating the Impact of Social Determinants on Health Prediction in the Intensive Care Unit |
| 2305.13193 | arxiv | arXiv id_list | TEIMMA: The First Content Reuse Annotator for Text, Images, and Math |
| 2306.08122 | arxiv | arXiv id_list | Beyond Black Box AI-Generated Plagiarism Detection: From Sentence to Document Level |
| 2306.11181 | arxiv | arXiv id_list | Insufficiently Justified Disparate Impact: A New Criterion for Subgroup Fairness |
| 2307.14448 | arxiv | arXiv id_list | VISPUR: Visual Aids for Identifying and Interpreting Spurious Associations in Data-Driven Decisi |
| 2307.14850 | arxiv | arXiv id_list | Turkish Native Language Identification V2 |
| 2308.01191 | arxiv | arXiv id_list | Towards Understanding the Capability of Large Language Models on Code Clone Detection: A Survey |
| 2308.12842 | arxiv | arXiv id_list | Text Similarity from Image Contents using Statistical and Semantic Analysis Techniques |
| 2308.13754 | arxiv | arXiv id_list | ZC3: Zero-Shot Cross-Language Code Clone Detection |
| 2309.14198 | arxiv | arXiv id_list | (Predictable) Performance Bias in Unsupervised Anomaly Detection |
| 2310.03146 | arxiv | arXiv id_list | Fairness-enhancing mixed effects deep learning improves fairness on in- and out-of-distribution  |
| 2310.06730 | arxiv | arXiv id_list | Sparse topic modeling via spectral decomposition and thresholding |
| 2310.06786 | arxiv | arXiv id_list | OpenWebMath: An Open Dataset of High-Quality Mathematical Web Text |
| 2311.06840 | arxiv | arXiv id_list | Omitted Labels Induce Nontransitive Paradoxes in Causality |
| 2311.07277 | arxiv | arXiv id_list | AdaCCD: Adaptive Semantic Contrasts Discovery Based Cross Lingual Adaptation for Code Clone Dete |
| 2311.08778 | arxiv | arXiv id_list | Gitor: Scalable Code Clone Detection by Building Global Sample Graph |
| 2311.12684 | arxiv | arXiv id_list | Adversarial Reweighting Guided by Wasserstein Distance for Bias Mitigation |
| 2312.10083 | arxiv | arXiv id_list | The Limits of Fair Medical Imaging AI In The Wild |
| 2401.09885 | arxiv | arXiv id_list | Source Code Clone Detection Using Unsupervised Similarity Measures |
| 2401.13802 | arxiv | arXiv id_list | Investigating the Efficacy of Large Language Models for Code Clone Detection |
| 2401.16969 | arxiv | arXiv id_list | Taxonomy of Mathematical Plagiarism |
| 2402.11338 | arxiv | arXiv id_list | Fair Classification with Partial Feedback: An Exploration-Based Data Collection Approach |
| 2403.18202 | arxiv | arXiv id_list | TGMM: Combining Parse Tree with GPU for Scalable Multilingual and Multi-Granularity Code Clone D |
| 2404.01582 | arxiv | arXiv id_list | BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection System |
| 2405.00428 | arxiv | arXiv id_list | CC2Vec: Combining Typed Tokens with Contrastive Learning for Effective Code Clone Detection |
| 2405.05934 | arxiv | arXiv id_list | Theoretical Guarantees of Data Augmented Last Layer Retraining Methods |
| 2405.06841 | arxiv | arXiv id_list | Bridging the Gap: Protocol Towards Fair and Consistent Affect Analysis |
| 2406.06487 | arxiv | arXiv id_list | When is Multicalibration Post-Processing Necessary? |
| 2406.11029 | arxiv | arXiv id_list | Curating Stopwords in Marathi: A TF-IDF Approach for Improved Text Analysis and Information Retr |
| 2406.16288 | arxiv | arXiv id_list | PlagBench: Exploring the Duality of Large Language Models in Plagiarism Generation and Detection |
| 2407.02402 | arxiv | arXiv id_list | Assessing the Code Clone Detection Capability of Large Language Models |
| 2407.13105 | arxiv | arXiv id_list | Survey on Plagiarism Detection in Large Language Models: The Impact of ChatGPT and Gemini on Aca |
| 2408.04430 | arxiv | arXiv id_list | The Struggles of LLMs in Cross-lingual Code Clone Detection |
| 2408.07321 | arxiv | arXiv id_list | VERCATION: Precise Vulnerable Open-source Software Version Identification based on Static Analys |
| 2410.00502 | arxiv | arXiv id_list | Multi-Target Cross-Lingual Summarization: a novel task and a language-neutral approach |
| 2410.03600 | arxiv | arXiv id_list | Efficiently Identifying Watermarked Segments in Mixed-Source Texts |
| 2410.08728 | arxiv | arXiv id_list | From N-grams to Pre-trained Multilingual Models For Language Identification |
| 2411.09730 | arxiv | arXiv id_list | SureMap: Simultaneous Mean Estimation for Single-Task and Multi-Task Disaggregated Evaluation |
| 2411.19096 | arxiv | arXiv id_list | Pralekha: Cross-Lingual Document Alignment for Indic Languages |
| 2412.06241 | arxiv | arXiv id_list | Plagiarism Detection Using Machine Learning |
| 2412.11758 | arxiv | arXiv id_list | Establishing a Foundation for Tetun Ad-Hoc Text Retrieval: Stemming, Indexing, Retrieval, and Ra |
| 2412.18904 | arxiv | arXiv id_list | FedCFA: Alleviating Simpson's Paradox in Model Aggregation with Counterfactual Federated Learnin |
| 2501.03212 | arxiv | arXiv id_list | Leveraging Explainable AI for LLM Text Attribution: Differentiating Human-Written and Multiple L |
| 2501.05260 | arxiv | arXiv id_list | Enhancing Plagiarism Detection in Marathi with a Weighted Ensemble of TF-IDF and BERT Embeddings |
| 2501.11171 | arxiv | arXiv id_list | Counteracting temporal attacks in Video Copy Detection |
| 2501.18998 | arxiv | arXiv id_list | Adversarial Attacks on AI-Generated Text Detection Models: A Token Probability-Based Approach Us |
| 2502.10161 | arxiv | arXiv id_list | Revisiting the Berkeley Admissions data: Statistical Tests for Causal Hypotheses |
| 2502.20936 | arxiv | arXiv id_list | WebFAQ: A Multilingual Collection of Natural Q&A Datasets for Dense Retrieval |
| 2503.19211 | arxiv | arXiv id_list | MASRAD: Arabic Terminology Management Corpora with Semi-Automatic Construction |
| 2504.08776 | arxiv | arXiv id_list | SemCAFE: When Named Entities make the Difference Assessing Web Source Reliability through Entity |
| 2504.17066 | arxiv | arXiv id_list | Whence Is A Model Fair? Fixing Fairness Bugs via Propensity Score Matching |
| 2504.21677 | arxiv | arXiv id_list | 20min-XD: A Comparable Corpus of Swiss News Articles |
| 2505.07157 | arxiv | arXiv id_list | HAMLET: Healthcare-focused Adaptive Multilingual Learning Embedding-based Topic Modeling |
| 2505.12181 | arxiv | arXiv id_list | Reliable fairness auditing with semi-supervised inference |
| 2505.15070 | arxiv | arXiv id_list | An Alternative to FLOPS Regularization to Effectively Productionize SPLADE-Doc |
| 2506.01230 | arxiv | arXiv id_list | Stress-Testing ML Pipelines with Adversarial Data Corruption |
| 2506.10995 | arxiv | arXiv id_list | Evaluating Small-Scale Code Models for Code Clone Detection |
| 2506.14470 | arxiv | arXiv id_list | AST-Enhanced or AST-Overloaded? The Surprising Impact of Hybrid Graph Representations on Code Cl |
| 2507.14176 | arxiv | arXiv id_list | Predictive Representativity: Uncovering Racial Bias in AI-based Skin Cancer Detection |
| 2507.15226 | arxiv | arXiv id_list | Code Clone Detection via an AlphaFold-Inspired Framework |
| 2507.15742 | arxiv | arXiv id_list | A Fisher's exact test justification of the TF-IDF term-weighting scheme |
| 2508.01357 | arxiv | arXiv id_list | HyClone: Bridging LLM Understanding and Dynamic Execution for Semantic Code Clone Detection |
| 2508.02555 | arxiv | arXiv id_list | Building and Aligning Comparable Corpora |
| 2508.03435 | arxiv | arXiv id_list | StoneDetector: Conventional and versatile code clone detection for Java |
| 2508.06495 | arxiv | arXiv id_list | Semi-automated Fact-checking in Portuguese: Corpora Enrichment using Retrieval with Claim extrac |
| 2508.15096 | arxiv | arXiv id_list | Nemotron-CC-Math: A 133 Billion-Token-Scale High Quality Math Pretraining Dataset |
| 2509.02033 | arxiv | arXiv id_list | StructCoh: Structured Contrastive Learning for Context-Aware Text Semantic Matching |
| 2509.22978 | arxiv | arXiv id_list | Towards Human-interpretable Explanation in Code Clone Detection using LLM-based Post Hoc Explain |
| 2510.01447 | arxiv | arXiv id_list | SoftAdaClip: A Smooth Clipping Strategy for Fair and Private Model Training |
| 2510.15480 | arxiv | arXiv id_list | Selecting and Combining Large Language Models for Scalable Code Clone Detection |
| 2510.15577 | arxiv | arXiv id_list | BiMax: Bidirectional MaxSim Score for Document-Level Alignment |
| 2510.24241 | arxiv | arXiv id_list | MAGNET: A Multi-Graph Attentional Network for Code Clone Detection |
| 2511.01176 | arxiv | arXiv id_list | An Empirical Study of LLM-Based Code Clone Detection |
| 2511.04699 | arxiv | arXiv id_list | Cross-Lingual SynthDocs: A Large-Scale Synthetic Corpus for Any to Arabic OCR and Document Under |
| 2511.07025 | arxiv | arXiv id_list | Llama-Embed-Nemotron-8B: A Universal Text Embedding Model for Multilingual and Cross-Lingual Tas |
| 2511.19325 | arxiv | arXiv id_list | Generative Query Expansion with Multilingual LLMs for Cross-Lingual Information Retrieval |
| 2512.16816 | arxiv | arXiv id_list | Toward Systematic Counterfactual Fairness Evaluation of Large Language Models: The CAFFE Framewo |
| 2512.23504 | arxiv | arXiv id_list | Automatic Detection of Complex Quotation Patterns in Aggadic Literature |
| 2602.00094 | arxiv | arXiv id_list | Trade-offs Between Individual and Group Fairness in Machine Learning: A Comprehensive Review |
| 2602.05707 | arxiv | arXiv id_list | Fix Representation (Optimally) Before Fairness: Finite-Sample Shrinkage Population Correction an |
| 2602.09147 | arxiv | arXiv id_list | Overview of PAN 2026: Voight-Kampff Generative AI Detection, Text Watermarking, Multi-Author Wri |
| 2603.02174 | arxiv | arXiv id_list | De-paradox Tree: Breaking Down Simpson's Paradox via A Kernel-Based Partition Algorithm |
| 2603.15004 | arxiv | arXiv id_list | TriFusion-LLM: Prior-Guided Multimodal Fusion with LLM Arbitration for Fine-grained Code Clone D |
| 2603.29937 | arxiv | arXiv id_list | Rewrite the News: Tracing Editorial Reuse Across News Agencies |
| 2604.06165 | arxiv | arXiv id_list | HaloProbe: Bayesian Detection and Mitigation of Object Hallucinations in Vision-Language Models |
| 2604.13783 | arxiv | arXiv id_list | Zero-shot Evaluation of Deep Learning for Java Code Clone Detection |
| 2604.14352 | arxiv | arXiv id_list | PROXIMA: A Reliability Scoring Framework for Proxy Metrics in Online Controlled Experiments |
| 2604.22640 | arxiv | arXiv id_list | Quality-Driven Selective Mutation for Deep Learning |
| 2604.26266 | arxiv | arXiv id_list | Explaining the "Why": A Unified Framework for the Additive Attribution of Changes in Arbitrary M |
| 2604.27315 | arxiv | arXiv id_list | Cross-lingual Comparison of Research Funding Projects with Multilingual Sentence-BERT: Evidence  |
| 2605.02860 | arxiv | arXiv id_list | Standing on the Shoulders of Giants: Stabilized Knowledge Distillation for Cross--Language Code  |
| 2605.06294 | arxiv | arXiv id_list | Log-Likelihood, Simpson's Paradox, and the Detection of Machine-Generated Text |
| 2605.09236 | arxiv | arXiv id_list | Matching Meaning at Scale: Evaluating Semantic Search for 18th-Century Intellectual History thro |
| 2605.09421 | arxiv | arXiv id_list | MACAA: Belief-Revision Multi-Agent Reasoning for Code Authorship Verification |
| 2605.11017 | arxiv | arXiv id_list | Simpson's Paradox in Behavioral Curves: How Aggregation Distorts Parametric Models of User Dynam |
| 2605.27636 | arxiv | arXiv id_list | Simorgh at SemEval-2026 task 7: Region-Aware Hybrid Retrieval for Low-Resource Cultural Reasonin |
| 2605.31171 | arxiv | arXiv id_list | MIMO: Multilingual Information Retrieval via Monolingual Objectives |
| 2606.01252 | arxiv | arXiv id_list | Understanding LLM Behavior in Multi-Target Cross-Lingual Summarization |
| 2606.06972 | arxiv | arXiv id_list | Accounting for Context: Shaping Moral Credences for Value Alignment |
| 2606.22711 | arxiv | arXiv id_list | Beyond Simpson's Paradox: A Cascade of Confounders in AI Agent Pull-Request Co-Authorship |
| 2606.25272 | arxiv | arXiv id_list | Semantic Code Clone Detection: Are We There Yet? |
| 2607.14607 | arxiv | arXiv id_list | Auditing Fairness-Privacy Trade-offs: Subpopulation-Level Effects of Fairness-Enhancing Algorith |
| 2607.15238 | arxiv | arXiv id_list | Language Identification via Compositional Data Analysis: A Linear-Time Classifier Based on Log-R |
| 2607.24641 | arxiv | arXiv id_list | Efficient Topic Model Estimation under Heavy-Tailed Document Lengths |
| 2608.03859 | arxiv | arXiv id_list | Beyond Representational Similarity: Source-Conditioned Description-Length Gain for Generative Pl |
| 2608.21023 | arxiv | arXiv id_list | Scaling Unsupervised Word Alignment to Documents via Structural Constraints |
| 2608.22383 | arxiv | arXiv id_list | Learning Spectral Representations of Code through Latent Graph Learning for Generalizable Cross- |
| 2608.25707 | arxiv | arXiv id_list | Fairness-Aware Test-Time Prompt Tuning |
| 2608.30568 | arxiv | arXiv id_list | Collapsibility of Performance Metrics in Clinical Predictive AI |
| 2609.07699 | arxiv | arXiv id_list | Fine PT-PT Web: A High-Quality 41 Billion Tokens Data Collection of the European Portuguese Web |
| 2609.11023 | arxiv | arXiv id_list | RCL: A Retrieval-Confidence Layer for Detecting Insufficient Context in Enterprise Retrieval-Aug |
| 2609.17338 | arxiv | arXiv id_list | Type-IV Code Clone Detection via Layer-Wise Non-Contrastive Representation Learning |
| 2609.19153 | arxiv | arXiv id_list | Stop Removing Stopwords: How an Inherited Preprocessing Default Distorts Legal Text-as-Data |
| 2609.33983 | arxiv | arXiv id_list | High-Level Text Preprocessing for Semantic Similarity Analysis of Discursive Texts: A Framework  |
| 2609.36161 | arxiv | arXiv id_list | From Dead Code and Static Requirements to Working Engines: Software Revival with Coding Agents |
| cs/0609060 | arxiv | arXiv id_list | Automatic Identification of Document Translations in Large Multilingual Document Collections |
| cs/0609064 | arxiv | arXiv id_list | Exploiting multilingual nomenclatures and language-independent text features as an interlingua f |
