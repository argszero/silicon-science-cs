# Reference authenticity check -- issue #158

Every entry below was resolved through a real registry on 2026-10-30, by a program (`build_refs.py`) and not by hand, and each row names the identifier a reader can open. The acceptance rule is stated here as the code implements it, because a report that describes a rule the code no longer applies is a second copy that no gate reads.

From Crossref a record is accepted only when its title, after folding stopwords and punctuation, equals the query -- or else contains all but at most one of the query's content words and adds at most three of its own, the shape of a subtitle or an appended note. A query of three content words or fewer is admitted on exact equality only, because a word-overlap ratio has no resolution on a short title: 'Spectral hashing' is a 100% word match for 'Fully non-local super-resolution via spectral hashing'. The issued year must agree within two years. A book seed instead requires exact title equality AND a book-shaped record type, because a book review carries the book's title and a DOI.

From arXiv, used for the venues Crossref does not index at all, a record is accepted only on exact normalised title equality with the year within one, and the row is labelled arxiv: so a reader can see that a preprint was cited.

Two slugs that resolve to one work are refused as duplicates: the bibliography may not be lengthened by naming one paper twice.

| slug | query | verdict | record found |
|---|---|---|---|
| `bentley-1975` | Multidimensional binary search trees used for associative searching | **verified** |  doi:10.1145/361002.361007 |
| `guttman-r-tree-1984` | R-trees: a dynamic index structure for spatial searching | **verified** |  doi:10.1007/springerreference_62807 |
| `beckmann-rstar-1990` | The R*-tree: an efficient and robust access method for points and rect | **verified** |  doi:10.1145/93597.98741 |
| `uhlenbeck-metric-tree-1991` | Satisfying general proximity/similarity queries with metric trees | **verified** |  doi:10.1016/0020-0190(91)90074-r |
| `katayama-sr-tree-1997` | The SR-tree: an index structure for high-dimensional nearest neighbor  | **verified** |  doi:10.1002/(sici)1520-684x(19980615)29:6<59::aid-scj6>3.3.co;2-d |
| `ciaccia-pac-2000` | PAC nearest neighbor queries: approximate and controlled search in hig | **verified** |  doi:10.1109/icde.2000.839417 |
| `chavez-metric-spaces-2001` | Searching in metric spaces | **verified** |  doi:10.1145/502807.502808 |
| `hjaltason-sampling-2003` | Index-driven similarity search in metric spaces | **verified** |  doi:10.1145/958942.958948 |
| `muja-flann-2009` | Fast approximate nearest neighbors with automatic algorithm configurat | **verified** |  doi:10.5220/0001787803310340 |
| `muja-flann-2014` | Scalable nearest neighbor algorithms for high dimensional data | **verified** |  doi:10.1109/tpami.2014.2321376 |
| `indyk-motwani-1998` | Approximate nearest neighbors: towards removing the curse of dimension | **NO RECORD (arxiv: no exact title match)** | - |
| `gionis-indyk-motwani-1999` | Similarity search in high dimensions via hashing | **NO RECORD (arxiv: no exact title match)** | - |
| `charikar-2002` | Similarity estimation techniques from rounding algorithms | **verified** |  doi:10.1145/509907.509965 |
| `datar-pstable-lsh-2004` | Locality-sensitive hashing scheme based on p-stable distributions | **verified** |  doi:10.1145/997817.997857 |
| `bawa-lsh-forest-2005` | LSH forest: self-tuning indexes for similarity search | **NO RECORD (arxiv: no exact title match)** | - |
| `andoni-indyk-2006` | Near-optimal hashing algorithms for approximate nearest neighbor in hi | **verified** |  doi:10.1109/focs.2006.49 |
| `pauleve-lsh-2010` | Locality sensitive hashing: a comparison of hash function types and qu | **verified** |  doi:10.1016/j.patrec.2010.04.004 |
| `sundaram-lsh-tweets-2013` | Streaming similarity search over one billion tweets using parallel loc | **verified** |  doi:10.14778/2556549.2556574 |
| `andoni-razenshteyn-2015` | Optimal data-dependent hashing for approximate near neighbors | **verified** |  doi:10.1145/2746539.2746553 |
| `broder-minhash-1997` | On the resemblance and containment of documents | **verified** |  doi:10.1109/sequen.1997.666900 |
| `bloom-1970` | Space/time trade-offs in hash coding with allowable errors | **verified** |  doi:10.1145/362686.362692 |
| `norouzi-mih-2014` | Fast exact search in Hamming space with multi-index hashing | **verified** |  doi:10.1109/tpami.2013.231 |
| `heo-spherical-hashing-2012` | Spherical hashing | **verified** |  doi:10.1109/cvpr.2012.6248024 |
| `weiss-spectral-hashing-2009` | Spectral hashing | **NO RECORD (arxiv: no exact title match)** | - |
| `gong-itq-2011` | Iterative quantization: a procrustean approach to learning binary code | **verified** |  doi:10.1109/cvpr.2011.5995432 |
| `norouzi-minimal-loss-2011` | Minimal loss hashing for compact binary codes | **NO RECORD (arxiv: no exact title match)** | - |
| `liu-ksh-2012` | Supervised hashing with kernels | **verified** |  doi:10.1109/cvpr.2012.6247912 |
| `liong-deep-hashing-2015` | Deep hashing for compact binary codes learning | **verified** |  doi:10.1109/cvpr.2015.7298862 |
| `wang-hashing-survey-2018` | A survey on learning to hash | **verified** |  doi:10.1109/tpami.2017.2699960 |
| `lloyd-least-squares-1982` | Least squares quantization in PCM | **verified** |  doi:10.1109/tit.1982.1056489 |
| `gray-vector-quantization-1984` | Vector quantization | **verified** |  doi:10.1109/massp.1984.1162229 |
| `gersho-gray-vq-book-1992` | Vector quantization and signal compression | **verified** |  doi:10.1007/978-1-4615-3626-0 |
| `arthur-kmeanspp-2007` | k-means++: the advantages of careful seeding | **NO RECORD (arxiv: no exact title match)** | - |
| `jegou-douze-schmid-2011` | Product quantization for nearest neighbor search | **verified** |  doi:10.1109/tpami.2010.57 |
| `ge-optimized-pq-2013` | Optimized product quantization for approximate nearest neighbor search | **verified** |  doi:10.1109/cvpr.2013.379 |
| `ge-optimized-pq-2014` | Optimized product quantization | **verified** |  doi:10.1109/tpami.2013.240 |
| `babenko-additive-quant-2014` | Additive quantization for extreme vector compression | **verified** |  doi:10.1109/cvpr.2014.124 |
| `babenko-inverted-multi-index-2015` | The inverted multi-index | **verified** |  doi:10.1109/tpami.2014.2361319 |
| `babenko-deep1b-2016` | Efficient indexing of billion-scale datasets of deep descriptors | **verified** |  doi:10.1109/cvpr.2016.226 |
| `martinez-additive-quant-2016` | Revisiting additive quantization | **verified** |  doi:10.1007/978-3-319-46475-6_9 |
| `douze-polysemous-2016` | Polysemous codes | **verified** |  doi:10.1007/978-3-319-46475-6_48 |
| `baranchuk-invindices-2018` | Revisiting the inverted indices for billion-scale approximate nearest  | **verified** |  doi:10.1007/978-3-030-01258-8_13 |
| `matsui-pqtable-2018` | PQTable: nonexhaustive fast search for product-quantized codes using h | **verified** |  doi:10.1109/tmm.2017.2774009 |
| `malkov-nsw-2014` | Approximate nearest neighbor algorithm based on navigable small world  | **verified** |  doi:10.1016/j.is.2013.10.006 |
| `harwood-fanng-2016` | FANNG: fast approximate nearest neighbour graphs | **verified** |  doi:10.1109/cvpr.2016.616 |
| `jayaram-diskann-2019` | DiskANN: fast accurate billion-point nearest neighbor search on a sing | **NO RECORD (arxiv: no exact title match)** | - |
| `malkov-yashunin-2020` | Efficient and robust approximate nearest neighbor search using Hierarc | **verified** |  doi:10.1109/tpami.2018.2889473 |
| `fu-nsg-2019` | Fast approximate nearest neighbor search with the navigating spreading | **verified** |  doi:10.14778/3303753.3303754 |
| `wang-ann-graph-survey-2021` | A comprehensive survey and experimental comparison of graph-based appr | **verified** |  doi:10.14778/3476249.3476255 |
| `gollapudi-filtered-diskann-2023` | Filtered-DiskANN: graph algorithms for approximate nearest neighbor se | **verified** |  doi:10.1145/3543507.3583552 |
| `johnson-douze-jegou-2021` | Billion-scale similarity search with GPUs | **verified** |  doi:10.1109/tbdata.2019.2921572 |
| `douze-faiss-2024` | The Faiss library | **verified** |  doi:10.1109/tbdata.2025.3618474 |
| `wang-milvus-2021` | Milvus: a purpose-built vector data management system | **NO RECORD (arxiv: no exact title match)** | - |
| `pan-vector-db-survey-2024` | Survey of vector database management systems | **verified** |  doi:10.1007/s00778-024-00864-x |
| `guo-manu-2022` | Manu: a cloud native vector database management system | **verified (arxiv)** |  arxiv:2206.13843 |
| `simhadri-bigann-2022` | Results of the NeurIPS'21 challenge on billion-scale approximate neare | **verified (arxiv)** |  arxiv:2205.03763 |
| `aumuller-ann-benchmarks-2017` | ANN-Benchmarks: a benchmarking tool for approximate nearest neighbor a | **verified** |  doi:10.1007/978-3-319-68474-1_3 |
| `williams-roofline-2009` | Roofline: an insightful visual performance model for multicore archite | **verified** |  doi:10.2172/1407078 |
| `jouppi-tpu-2017` | In-datacenter performance analysis of a tensor processing unit | **verified** |  doi:10.1145/3140659.3080246 |
| `manning-ir-book-2008` | Introduction to Information Retrieval | **verified** |  doi:10.1017/cbo9780511809071 |
| `voorhees-trec-book-2005` | TREC: experiment and evaluation in information retrieval | **NO RECORD (arxiv: no exact title match)** | - |
| `harman-trec1-1993` | Overview of the first TREC conference | **verified** |  doi:10.1145/160688.160692 |
| `buckley-incomplete-info-2004` | Retrieval evaluation with incomplete information | **verified** |  doi:10.1145/1008992.1009000 |
| `buckley-pooling-bias-2007` | Bias and the limits of pooling for large collections | **verified** |  doi:10.1007/s10791-007-9032-x |
| `aslam-savell-2003` | On the effectiveness of evaluating retrieval systems in the absence of | **verified** |  doi:10.1145/860500.860501 |
| `aslam-pavlu-2003` | A unified model for metasearch, pooling, and system evaluation | **verified** |  doi:10.1145/956950.956953 |
| `voorhees-qa-trec-2001` | The TREC question answering track | **verified** |  doi:10.1017/s1351324901002789 |
| `zobel-similarity-space-1998` | Exploring the similarity space | **verified** |  doi:10.1145/281250.281256 |
| `zobel-inverted-files-2006` | Inverted files for text search engines | **verified** |  doi:10.1145/1132956.1132959 |
| `salton-vsm-1975` | A vector space model for automatic indexing | **verified** |  doi:10.1145/361219.361220 |
| `sparck-jones-idf-1972` | A statistical interpretation of term specificity and its application i | **verified** |  doi:10.1108/eb026526 |
| `robertson-relevance-weighting-1976` | Relevance weighting of search terms | **verified** |  doi:10.1002/asi.4630270302 |
| `robertson-bm25-2009` | The probabilistic relevance framework: BM25 and beyond | **verified** |  doi:10.1561/1500000019 |
| `khattab-colbert-2020` | ColBERT: efficient and effective passage search via contextualized lat | **verified (arxiv)** |  arxiv:2004.12832 |
| `thorne-fever-2018` | FEVER: a large-scale dataset for fact extraction and verification | **verified** |  doi:10.18653/v1/n18-1074 |
| `spearman-1904` | The proof and measurement of association between two things | **verified** |  doi:10.2307/1412159 |
| `wilson-1927` | Probable inference, the law of succession, and statistical inference | **verified** |  doi:10.1080/01621459.1927.10502953 |
| `kendall-1938` | A new measure of rank correlation | **verified** |  doi:10.2307/2332226 |
| `mann-whitney-1947` | On a test of whether one of two random variables is stochastically lar | **verified** |  doi:10.1214/aoms/1177730491 |
| `mcnemar-1947` | Note on the sampling error of the difference between correlated propor | **verified** |  doi:10.1007/bf02295996 |
| `goodman-kruskal-1954` | Measures of association for cross classifications | **verified** |  doi:10.1080/01621459.1954.10501231 |
| `cohen-kappa-1960` | A coefficient of agreement for nominal scales | **verified** |  doi:10.1177/001316446002000104 |
| `shapiro-wilk-1965` | An analysis of variance test for normality | **verified** |  doi:10.2307/2333709 |
| `cochran-sampling-1977` | Sampling techniques | **NO RECORD (arxiv: no exact title match)** | - |
| `efron-bootstrap-1979` | Bootstrap methods: another look at the jackknife | **verified** |  doi:10.1214/aos/1176344552 |
| `bland-altman-1986` | Statistical methods for assessing agreement between two methods of cli | **verified** |  doi:10.1016/s0140-6736(86)90837-8 |
| `agresti-coull-1998` | Approximate is better than exact for interval estimation of binomial p | **verified** |  doi:10.2307/2685469 |
| `newcombe-1998` | Interval estimation for the difference between independent proportions | **verified** |  doi:10.1002/(sici)1097-0258(19980430)17:8<873::aid-sim779>3.0.co;2-i |
| `hanson-wright-1971` | A bound on tail probabilities for quadratic forms in independent rando | **verified** |  doi:10.1214/aoms/1177693335 |
| `johnson-lindenstrauss-1984` | Extensions of Lipschitz mappings into a Hilbert space | **verified** |  doi:10.1090/conm/026/737400 |
| `talagrand-isoperimetric-1994` | Concentration of measure and isoperimetric inequalities in product spa | **verified** |  doi:10.1007/bf02699376 |
| `weber-high-dim-analysis-1998` | A quantitative analysis and performance study for similarity-search me | **NO RECORD (arxiv: no exact title match)** | - |
| `beyer-meaningful-nn-1999` | When is nearest neighbor meaningful? | **verified** |  doi:10.1007/3-540-49257-7_15 |
| `laurent-massart-2000` | Adaptive estimation of a quadratic functional by model selection | **verified** |  doi:10.1214/aos/1015957395 |
| `aggarwal-cvn-2001` | On the surprising behavior of distance metrics in high dimensional spa | **verified** |  doi:10.1007/3-540-44503-x_27 |
| `ledoux-concentration-2001` | The Concentration of Measure Phenomenon | **NO RECORD (arxiv: no exact title match)** | - |
| `achlioptas-random-projections-2003` | Database-friendly random projections: Johnson-Lindenstrauss with binar | **verified** |  doi:10.1016/s0022-0000(03)00025-4 |
| `francois-fractional-2007` | The concentration of fractional distances | **verified** |  doi:10.1109/tkde.2007.1037 |
| `boucheron-concentration-2013` | Concentration Inequalities: A Nonasymptotic Theory of Independence | **NO RECORD (arxiv: no exact title match)** | - |
| `vershynin-highdim-probability-2018` | High-Dimensional Probability: An Introduction with Applications in Dat | **NO RECORD (arxiv: no exact title match)** | - |
| `wainwright-highdim-statistics-2019` | High-Dimensional Statistics: A Non-Asymptotic Viewpoint | **NO RECORD (arxiv: no exact title match)** | - |
| `lowe-iccv-1999` | Object recognition from local scale-invariant features | **verified** |  doi:10.1109/iccv.1999.790410 |
| `lowe-sift-2004` | Distinctive image features from scale-invariant keypoints | **verified** |  doi:10.1023/b:visi.0000029664.99615.94 |
| `bay-surf-2006` | Speeded-up robust features (SURF) | **verified** |  doi:10.1016/j.cviu.2007.09.014 |
| `dalal-hog-2005` | Histograms of oriented gradients for human detection | **verified** |  doi:10.1109/cvpr.2005.177 |
| `nister-vocab-tree-2006` | Scalable recognition with a vocabulary tree | **verified** |  doi:10.1109/cvpr.2006.264 |
| `philbin-large-vocabularies-2007` | Object retrieval with large vocabularies and fast spatial matching | **verified** |  doi:10.1109/cvpr.2007.383172 |
| `jegou-hamming-embedding-2008` | Hamming embedding and weak geometric consistency for large scale image | **verified** |  doi:10.1007/978-3-540-88682-2_24 |
| `perronnin-fisher-2010` | Improving the Fisher kernel for large-scale image classification | **verified** |  doi:10.1007/978-3-642-15561-1_11 |
| `jegou-fisher-2012` | Aggregating local image descriptors into compact codes | **verified** |  doi:10.1109/tpami.2011.235 |
| `arandjelovic-netvlad-2016` | NetVLAD: CNN architecture for weakly supervised place recognition | **verified** |  doi:10.1109/tpami.2017.2711011 |
| `radenovic-finetuning-2018` | Fine-tuning CNN image retrieval with no human annotation | **verified** |  doi:10.1109/tpami.2018.2846566 |
| `deng-imagenet-2009` | ImageNet: a large-scale hierarchical image database | **verified** |  doi:10.1109/cvpr.2009.5206848 |
| `lin-coco-2014` | Microsoft COCO: common objects in context | **verified** |  doi:10.1007/978-3-319-10602-1_48 |
| `thomee-yfcc100m-2016` | YFCC100M: the new data in multimedia research | **verified (arxiv)** |  arxiv:1503.01817 |
| `kuznetsova-openimages-2020` | The Open Images dataset V4 | **verified** |  doi:10.1007/s11263-020-01316-z |
| `schroff-facenet-2015` | FaceNet: a unified embedding for face recognition and clustering | **verified** |  doi:10.1109/cvpr.2015.7298682 |
| `he-resnet-2016` | Deep residual learning for image recognition | **verified** |  doi:10.1109/cvpr.2016.90 |
| `devlin-bert-2019` | BERT: pre-training of deep bidirectional transformers for language und | **verified** |  doi:10.18653/v1/n19-1423 |
| `reimers-sbert-2019` | Sentence-BERT: sentence embeddings using Siamese BERT-networks | **verified** |  doi:10.18653/v1/d19-1410 |
| `karpukhin-dpr-2020` | Dense passage retrieval for open-domain question answering | **verified** |  doi:10.18653/v1/2020.emnlp-main.550 |
| `lewis-rag-2020` | Retrieval-augmented generation for knowledge-intensive NLP tasks | **verified (arxiv)** |  arxiv:2005.11401 |
| `mikolov-word2vec-2013` | Distributed representations of words and phrases and their composition | **verified (arxiv)** |  arxiv:1310.4546 |
| `guu-realm-2020` | REALM: retrieval-augmented language model pre-training | **verified (arxiv)** |  arxiv:2002.08909 |
| `borgeaud-retro-2022` | Improving language models by retrieving from trillions of tokens | **verified (arxiv)** |  arxiv:2112.04426 |
| `virtanen-scipy-2020` | SciPy 1.0: fundamental algorithms for scientific computing in Python | **verified** |  doi:10.1038/s41592-019-0686-2 |
| `harris-numpy-2020` | Array programming with NumPy | **verified** |  doi:10.1038/s41586-020-2649-2 |
| `hunter-matplotlib-2007` | Matplotlib: a 2D graphics environment | **verified** |  doi:10.1109/mcse.2007.55 |
| `mckinney-pandas-2010` | Data structures for statistical computing in Python | **verified** |  doi:10.25080/majora-92bf1922-00a |
| `h5py-collette` | Python and HDF5 | **NO RECORD (arxiv: no exact title match)** | - |
| `ioannidis-why-false-2005` | Why most published research findings are false | **verified** |  doi:10.1371/journal.pmed.0020124 |
| `nosek-preregistration-2018` | The preregistration revolution | **verified** |  doi:10.31219/osf.io/2dxu5 |
| `munafo-manifesto-2017` | A manifesto for reproducible science | **verified** |  doi:10.1038/s41562-016-0021 |
| `peng-reproducible-2011` | Reproducible research in computational science | **verified** |  doi:10.1126/science.1213847 |
| `wilkinson-fair-2016` | The FAIR guiding principles for scientific data management and steward | **verified** |  doi:10.1038/sdata.2016.18 |
| `sandve-ten-rules-2013` | Ten simple rules for reproducible computational research | **verified** |  doi:10.1371/journal.pcbi.1003285 |
| `stodden-enhancing-2016` | Enhancing reproducibility for computational methods | **verified** |  doi:10.1126/science.aah6168 |
| `thakur-beir-2021` | BEIR: a heterogeneous benchmark for zero-shot evaluation of informatio | **NO RECORD (arxiv: no exact title match)** | - |
| `mallen-mteb-2023` | MTEB: massive text embedding benchmark | **verified** |  doi:10.18653/v1/2023.eacl-main.148 |
| `kulis-kernel-lsh-2009` | Kernelized locality-sensitive hashing for scalable image search | **verified** |  doi:10.1109/iccv.2009.5459466 |

**123 of 140 seeds verified.** Rejections by reason: NO RECORD x17. A refusal is not a failure to look: every refused seed is named with its reason, because a silently dropped citation is a lie of omission.

The journal's floor is 100 references, all cited in the body; this file and `refs.json` together are what that count is read from, and `make_manuscript.py` refuses to render while the count is short or while a held reference is never cited.
