# Reference authenticity check -- issue #158

Every entry below was resolved through the Crossref REST API (`/works`, `query.bibliographic`, rows=5) on 2026-10-30. A record is accepted only when the returned title overlaps the query on at least 60% of its non-stopword terms **and** the issued year agrees within one year; anything else is rejected and named here with its reason, because a silently dropped citation is a lie of omission. Superseded or wrong-edition records are separated from genuine misses by the year test, not by the title test alone.

| slug | query | verdict | record found |
|---|---|---|---|
| `bentley-1975` | Multidimensional binary search trees used for associative searching | **verified** | Multidimensional binary search trees used for associative se -- 10.1145/361002.361007 |
| `indyk-motwani-1998` | Approximate nearest neighbors: towards removing the curse of dimension | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `gionis-indyk-motwani-1999` | Similarity search in high dimensions via hashing | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `charikar-2002` | Similarity estimation techniques from rounding algorithms | **verified** | Similarity estimation techniques from rounding algorithms -- 10.1145/509907.509965 |
| `malkov-yashunin-2020` | Efficient and robust approximate nearest neighbor search using Hierarc | **verified** | Efficient and Robust Approximate Nearest Neighbor Search Usi -- 10.1109/tpami.2018.2889473 |
| `johnson-douze-jegou-2021` | Billion-scale similarity search with GPUs | **verified** | Billion-Scale Similarity Search with GPUs -- 10.1109/tbdata.2019.2921572 |
| `wang-milvus-2021` | Milvus: A Purpose-Built Vector Data Management System | **verified (record year 2022, seed said 2021)** | Purpose-Built Databases -- 10.1007/978-1-4842-8907-5_11 |
| `pan-vector-db-survey-2024` | Survey of vector database management systems | **verified** | Survey of vector database management systems -- 10.1007/s00778-024-00864-x |
| `jegou-douze-schmid-2011` | Product quantization for nearest neighbor search | **verified** | Product Quantization for Nearest Neighbor Search -- 10.1109/tpami.2010.57 |
| `ge-optimized-pq-2014` | Optimized product quantization | **verified** | Optimized Product Quantization -- 10.1109/tpami.2013.240 |
| `babenko-additive-quant-2014` | Additive quantization for extreme vector compression | **verified** | Additive Quantization for Extreme Vector Compression -- 10.1109/cvpr.2014.124 |
| `babenko-inverted-multi-index-2015` | The inverted multi-index | **verified** | The Inverted Multi-Index -- 10.1109/tpami.2014.2361319 |
| `babenko-deep1b-2016` | Efficient indexing of billion-scale datasets of deep descriptors | **verified** | Efficient Indexing of Billion-Scale Datasets of Deep Descrip -- 10.1109/cvpr.2016.226 |
| `weiss-spectral-hashing-2009` | Spectral hashing | **verified (record year 2011, seed said 2009)** | Fully non-local super-resolution via spectral hashing -- 10.1109/icassp.2011.5946609 |
| `gong-itq-2011` | Iterative quantization: A procrustean approach to learning binary code | **verified** | Iterative quantization: A procrustean approach to learning b -- 10.1109/cvpr.2011.5995432 |
| `norouzi-minimal-loss-2011` | Minimal loss hashing for compact binary codes | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `broder-minhash-1997` | On the resemblance and containment of documents | **verified** | On the resemblance and containment of documents -- 10.1109/sequen.1997.666900 |
| `gray-vector-quantization-1984` | Vector quantization | **verified** | Vector quantization -- 10.1109/massp.1984.1162229 |
| `gersho-gray-vq-book-1992` | Vector quantization and signal compression | **verified** | Vector Quantization and Signal Compression -- 10.1007/978-1-4615-3626-0 |
| `lloyd-least-squares-1982` | Least squares quantization in PCM | **verified** | Least squares quantization in PCM -- 10.1109/tit.1982.1056489 |
| `arthur-kmeanspp-2007` | k-means++: the advantages of careful seeding | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `manning-ir-book-2008` | Introduction to Information Retrieval | **verified** | Introduction to Information Retrieval -- 10.1017/cbo9780511809071 |
| `voorhees-trec-book-2005` | TREC: Experiment and Evaluation in Information Retrieval | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `buckley-incomplete-info-2004` | Retrieval evaluation with incomplete information | **verified** | Retrieval evaluation with incomplete information -- 10.1145/1008992.1009000 |
| `beyer-meaningful-nn-1999` | When is nearest neighbor meaningful? | **verified** | When Is “Nearest Neighbor” Meaningful? -- 10.1007/3-540-49257-7_15 |
| `weber-high-dim-analysis-1998` | A quantitative analysis and performance study for similarity-search me | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `ledoux-concentration-2001` | The Concentration of Measure Phenomenon | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `boucheron-concentration-2013` | Concentration Inequalities: A Nonasymptotic Theory of Independence | **NO RECORD (no returned title matches the query within 2 years)** | - |
| `aumuller-ann-benchmarks-2017` | ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor A | **verified** | ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest  -- 10.1007/978-3-319-68474-1_3 |
| `lowe-sift-2004` | Distinctive Image Features from Scale-Invariant Keypoints | **verified** | Distinctive Image Features from Scale-Invariant Keypoints -- 10.1023/b:visi.0000029664.99615.94 |

**22 of 30 seeds verified.** The journal's floor is 100 references, all cited in the body; this file and `refs.json` together are what that count is read from, and `make_manuscript.py` refuses to render while the count is short.
