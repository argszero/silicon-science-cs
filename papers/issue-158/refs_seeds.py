#!/usr/bin/env python3
"""refs_seeds.py -- the candidate pool that build_refs.py tries to resolve.

Each row is `slug: (title as I believe it to be, year)`. Nothing here is a reference: a seed is
a *proposal* to the registry, and only a record the registry returns becomes a reference. A seed
the registry refuses is printed with its reason and never enters refs.json, so a wrong guess
costs a query rather than a fabricated citation.

The pool is grouped by the role the work plays in this paper, because a reference earns its
place by the sentence it supports, not by sharing vocabulary with the title.
"""
# slug -> (query title, expected year or None)
SEEDS = {
    # ---- metric trees and space partitioning ----------------------------------------------
    "bentley-1975": ("Multidimensional binary search trees used for associative searching", 1975),
    "guttman-r-tree-1984": ("R-trees: a dynamic index structure for spatial searching", 1984),
    "beckmann-rstar-1990": ("The R*-tree: an efficient and robust access method for points and rectangles", 1990),
    "uhlenbeck-metric-tree-1991": ("Satisfying general proximity/similarity queries with metric trees", 1991),
    "katayama-sr-tree-1997": ("The SR-tree: an index structure for high-dimensional nearest neighbor queries", 1997),
    "ciaccia-pac-2000": ("PAC nearest neighbor queries: approximate and controlled search in high-dimensional and metric spaces", 2000),
    "chavez-metric-spaces-2001": ("Searching in metric spaces", 2001),
    "hjaltason-sampling-2003": ("Index-driven similarity search in metric spaces", 2003),
    "muja-flann-2009": ("Fast approximate nearest neighbors with automatic algorithm configuration", 2009),
    "muja-flann-2014": ("Scalable nearest neighbor algorithms for high dimensional data", 2014),

    # ---- LSH and data-dependent hashing ----------------------------------------------------
    "indyk-motwani-1998": ("Approximate nearest neighbors: towards removing the curse of dimensionality", 1998),
    "gionis-indyk-motwani-1999": ("Similarity search in high dimensions via hashing", 1999),
    "charikar-2002": ("Similarity estimation techniques from rounding algorithms", 2002),
    "datar-pstable-lsh-2004": ("Locality-sensitive hashing scheme based on p-stable distributions", 2004),
    "bawa-lsh-forest-2005": ("LSH forest: self-tuning indexes for similarity search", 2005),
    "andoni-indyk-2006": ("Near-optimal hashing algorithms for approximate nearest neighbor in high dimensions", 2006),
    "pauleve-lsh-2010": ("Locality sensitive hashing: a comparison of hash function types and querying mechanisms", 2010),
    "sundaram-lsh-tweets-2013": ("Streaming similarity search over one billion tweets using parallel locality-sensitive hashing", 2013),
    "andoni-razenshteyn-2015": ("Optimal data-dependent hashing for approximate near neighbors", 2015),
    "broder-minhash-1997": ("On the resemblance and containment of documents", 1997),
    "bloom-1970": ("Space/time trade-offs in hash coding with allowable errors", 1970),
    "norouzi-mih-2014": ("Fast exact search in Hamming space with multi-index hashing", 2014),
    "heo-spherical-hashing-2012": ("Spherical hashing", 2012),

    # ---- learning binary codes -------------------------------------------------------------
    "weiss-spectral-hashing-2009": ("Spectral hashing", 2009),
    "gong-itq-2011": ("Iterative quantization: a procrustean approach to learning binary codes", 2011),
    "norouzi-minimal-loss-2011": ("Minimal loss hashing for compact binary codes", 2011),
    "liu-ksh-2012": ("Supervised hashing with kernels", 2012),
    "liong-deep-hashing-2015": ("Deep hashing for compact binary codes learning", 2015),
    "wang-hashing-survey-2018": ("A survey on learning to hash", 2018),

    # ---- vector quantisation ---------------------------------------------------------------
    "lloyd-least-squares-1982": ("Least squares quantization in PCM", 1982),
    "gray-vector-quantization-1984": ("Vector quantization", 1984),
    "gersho-gray-vq-book-1992": ("Vector quantization and signal compression", 1992),
    "arthur-kmeanspp-2007": ("k-means++: the advantages of careful seeding", 2007),
    "jegou-douze-schmid-2011": ("Product quantization for nearest neighbor search", 2011),
    "ge-optimized-pq-2013": ("Optimized product quantization for approximate nearest neighbor search", 2013),
    "ge-optimized-pq-2014": ("Optimized product quantization", 2014),
    "babenko-additive-quant-2014": ("Additive quantization for extreme vector compression", 2014),
    "babenko-inverted-multi-index-2015": ("The inverted multi-index", 2015),
    "babenko-deep1b-2016": ("Efficient indexing of billion-scale datasets of deep descriptors", 2016),
    "martinez-additive-quant-2016": ("Revisiting additive quantization", 2016),
    "douze-polysemous-2016": ("Polysemous codes", 2016),
    "baranchuk-invindices-2018": ("Revisiting the inverted indices for billion-scale approximate nearest neighbors", 2018),
    "matsui-pqtable-2018": ("PQTable: nonexhaustive fast search for product-quantized codes using hash tables", 2018),

    # ---- graph indexes ---------------------------------------------------------------------
    "malkov-nsw-2014": ("Approximate nearest neighbor algorithm based on navigable small world graphs", 2014),
    "harwood-fanng-2016": ("FANNG: fast approximate nearest neighbour graphs", 2016),
    "jayaram-diskann-2019": ("DiskANN: fast accurate billion-point nearest neighbor search on a single node", 2019),
    "malkov-yashunin-2020": ("Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", 2020),
    "fu-nsg-2019": ("Fast approximate nearest neighbor search with the navigating spreading-out graph", 2019),
    "wang-ann-graph-survey-2021": ("A comprehensive survey and experimental comparison of graph-based approximate nearest neighbor search", 2021),
    "gollapudi-filtered-diskann-2023": ("Filtered-DiskANN: graph algorithms for approximate nearest neighbor search with filters", 2023),

    # ---- GPU, systems, vector databases ----------------------------------------------------
    "johnson-douze-jegou-2021": ("Billion-scale similarity search with GPUs", 2021),
    "douze-faiss-2024": ("The Faiss library", 2024),
    "wang-milvus-2021": ("Milvus: a purpose-built vector data management system", 2021),
    "pan-vector-db-survey-2024": ("Survey of vector database management systems", 2024),
    "guo-manu-2022": ("Manu: a cloud native vector database management system", 2022),
    "simhadri-bigann-2022": ("Results of the NeurIPS'21 challenge on billion-scale approximate nearest neighbor search", 2022),
    "aumuller-ann-benchmarks-2017": ("ANN-Benchmarks: a benchmarking tool for approximate nearest neighbor algorithms", 2017),
    "williams-roofline-2009": ("Roofline: an insightful visual performance model for multicore architectures", 2009),
    "jouppi-tpu-2017": ("In-datacenter performance analysis of a tensor processing unit", 2017),

    # ---- IR evaluation, pooling, judged sets -----------------------------------------------
    "manning-ir-book-2008": ("Introduction to Information Retrieval", 2008),
    "voorhees-trec-book-2005": ("TREC: experiment and evaluation in information retrieval", 2005),
    "harman-trec1-1993": ("Overview of the first TREC conference", 1993),
    "buckley-incomplete-info-2004": ("Retrieval evaluation with incomplete information", 2004),
    "buckley-pooling-bias-2007": ("Bias and the limits of pooling for large collections", 2007),
    "aslam-savell-2003": ("On the effectiveness of evaluating retrieval systems in the absence of relevance judgments", 2003),
    "aslam-pavlu-2003": ("A unified model for metasearch, pooling, and system evaluation", 2003),
    "voorhees-qa-trec-2001": ("The TREC question answering track", 2001),
    "zobel-similarity-space-1998": ("Exploring the similarity space", 1998),
    "zobel-inverted-files-2006": ("Inverted files for text search engines", 2006),
    "salton-vsm-1975": ("A vector space model for automatic indexing", 1975),
    "sparck-jones-idf-1972": ("A statistical interpretation of term specificity and its application in retrieval", 1972),
    "robertson-relevance-weighting-1976": ("Relevance weighting of search terms", 1976),
    "robertson-bm25-2009": ("The probabilistic relevance framework: BM25 and beyond", 2009),
    "khattab-colbert-2020": ("ColBERT: efficient and effective passage search via contextualized late interaction over BERT", 2020),
    "thorne-fever-2018": ("FEVER: a large-scale dataset for fact extraction and verification", 2018),

    # ---- statistics: ties, rank correlation, agreement, intervals ---------------------------
    "spearman-1904": ("The proof and measurement of association between two things", 1904),
    "wilson-1927": ("Probable inference, the law of succession, and statistical inference", 1927),
    "kendall-1938": ("A new measure of rank correlation", 1938),
    "mann-whitney-1947": ("On a test of whether one of two random variables is stochastically larger than the other", 1947),
    "mcnemar-1947": ("Note on the sampling error of the difference between correlated proportions or percentages", 1947),
    "goodman-kruskal-1954": ("Measures of association for cross classifications", 1954),
    "cohen-kappa-1960": ("A coefficient of agreement for nominal scales", 1960),
    "shapiro-wilk-1965": ("An analysis of variance test for normality", 1965),
    "cochran-sampling-1977": ("Sampling techniques", 1977),
    "efron-bootstrap-1979": ("Bootstrap methods: another look at the jackknife", 1979),
    "bland-altman-1986": ("Statistical methods for assessing agreement between two methods of clinical measurement", 1986),
    "agresti-coull-1998": ("Approximate is better than exact for interval estimation of binomial proportions", 1998),
    "newcombe-1998": ("Interval estimation for the difference between independent proportions", 1998),

    # ---- concentration of measure and high-dimensional geometry ----------------------------
    "hanson-wright-1971": ("A bound on tail probabilities for quadratic forms in independent random variables", 1971),
    "johnson-lindenstrauss-1984": ("Extensions of Lipschitz mappings into a Hilbert space", 1984),
    "talagrand-isoperimetric-1994": ("Concentration of measure and isoperimetric inequalities in product spaces", 1994),
    "weber-high-dim-analysis-1998": ("A quantitative analysis and performance study for similarity-search methods in high-dimensional spaces", 1998),
    "beyer-meaningful-nn-1999": ("When is nearest neighbor meaningful?", 1999),
    "laurent-massart-2000": ("Adaptive estimation of a quadratic functional by model selection", 2000),
    "aggarwal-cvn-2001": ("On the surprising behavior of distance metrics in high dimensional space", 2001),
    "ledoux-concentration-2001": ("The Concentration of Measure Phenomenon", 2001),
    "achlioptas-random-projections-2003": ("Database-friendly random projections: Johnson-Lindenstrauss with binary coins", 2003),
    "francois-fractional-2007": ("The concentration of fractional distances", 2007),
    "boucheron-concentration-2013": ("Concentration Inequalities: A Nonasymptotic Theory of Independence", 2013),
    "vershynin-highdim-probability-2018": ("High-Dimensional Probability: An Introduction with Applications in Data Science", 2018),
    "wainwright-highdim-statistics-2019": ("High-Dimensional Statistics: A Non-Asymptotic Viewpoint", 2019),

    # ---- SIFT, local descriptors, image retrieval -------------------------------------------
    "lowe-iccv-1999": ("Object recognition from local scale-invariant features", 1999),
    "lowe-sift-2004": ("Distinctive image features from scale-invariant keypoints", 2004),
    "bay-surf-2006": ("Speeded-up robust features (SURF)", 2008),
    "dalal-hog-2005": ("Histograms of oriented gradients for human detection", 2005),
    "nister-vocab-tree-2006": ("Scalable recognition with a vocabulary tree", 2006),
    "philbin-large-vocabularies-2007": ("Object retrieval with large vocabularies and fast spatial matching", 2007),
    "jegou-hamming-embedding-2008": ("Hamming embedding and weak geometric consistency for large scale image search", 2008),
    "perronnin-fisher-2010": ("Improving the Fisher kernel for large-scale image classification", 2010),
    "jegou-fisher-2012": ("Aggregating local image descriptors into compact codes", 2012),
    "arandjelovic-netvlad-2016": ("NetVLAD: CNN architecture for weakly supervised place recognition", 2016),
    "radenovic-finetuning-2018": ("Fine-tuning CNN image retrieval with no human annotation", 2018),

    # ---- datasets, embeddings, dense retrieval ---------------------------------------------
    "deng-imagenet-2009": ("ImageNet: a large-scale hierarchical image database", 2009),
    "lin-coco-2014": ("Microsoft COCO: common objects in context", 2014),
    "thomee-yfcc100m-2016": ("YFCC100M: the new data in multimedia research", 2016),
    "kuznetsova-openimages-2020": ("The Open Images dataset V4", 2020),
    "schroff-facenet-2015": ("FaceNet: a unified embedding for face recognition and clustering", 2015),
    "he-resnet-2016": ("Deep residual learning for image recognition", 2016),
    "devlin-bert-2019": ("BERT: pre-training of deep bidirectional transformers for language understanding", 2019),
    "reimers-sbert-2019": ("Sentence-BERT: sentence embeddings using Siamese BERT-networks", 2019),
    "karpukhin-dpr-2020": ("Dense passage retrieval for open-domain question answering", 2020),
    "lewis-rag-2020": ("Retrieval-augmented generation for knowledge-intensive NLP tasks", 2020),
    "mikolov-word2vec-2013": ("Distributed representations of words and phrases and their compositionality", 2013),
    "guu-realm-2020": ("REALM: retrieval-augmented language model pre-training", 2020),
    "borgeaud-retro-2022": ("Improving language models by retrieving from trillions of tokens", 2022),

    # ---- numerical and software stack ------------------------------------------------------
    "virtanen-scipy-2020": ("SciPy 1.0: fundamental algorithms for scientific computing in Python", 2020),
    "harris-numpy-2020": ("Array programming with NumPy", 2020),
    "hunter-matplotlib-2007": ("Matplotlib: a 2D graphics environment", 2007),
    "mckinney-pandas-2010": ("Data structures for statistical computing in Python", 2010),
    "h5py-collette": ("Python and HDF5", 2013),

    # ---- reproducibility, measurement discipline, benchmarks -------------------------------
    "ioannidis-why-false-2005": ("Why most published research findings are false", 2005),
    "nosek-preregistration-2018": ("The preregistration revolution", 2018),
    "munafo-manifesto-2017": ("A manifesto for reproducible science", 2017),
    "peng-reproducible-2011": ("Reproducible research in computational science", 2011),
    "wilkinson-fair-2016": ("The FAIR guiding principles for scientific data management and stewardship", 2016),
    "sandve-ten-rules-2013": ("Ten simple rules for reproducible computational research", 2013),
    "stodden-enhancing-2016": ("Enhancing reproducibility for computational methods", 2016),
    "thakur-beir-2021": ("BEIR: a heterogeneous benchmark for zero-shot evaluation of information retrieval models", 2021),
    "mallen-mteb-2023": ("MTEB: massive text embedding benchmark", 2023),
    "kulis-kernel-lsh-2009": ("Kernelized locality-sensitive hashing for scalable image search", 2009),
}

# Seeds that name a BOOK. A book review in a review journal carries the book's title and a
# DOI, so a title test alone cannot tell the review from the work: "Introduction to Information
# Retrieval" resolved to a Choice Reviews Online notice before this restriction existed. These
# seeds accept only a book-shaped record whose title equals the seed's word for word.
BOOK_SEEDS = {
    "manning-ir-book-2008", "voorhees-trec-book-2005", "ledoux-concentration-2001",
    "gersho-gray-vq-book-1992", "boucheron-concentration-2013", "cochran-sampling-1977",
    "vershynin-highdim-probability-2018", "wainwright-highdim-statistics-2019",
    "h5py-collette",
}
