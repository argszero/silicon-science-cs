# Reference pool -- issue #135

Every entry below was discovered by `refscan135.py` (never typed from memory) and checked
against a LIVE external record by comparing the returned TITLE with the stored title
(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a
remembered identifier can resolve to a DIFFERENT real paper, so the check is the title
comparison, not the HTTP status.

- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with
  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)
  and `works/<doi>` (verification)
- pool: 556 entries (543 arXiv, 13 Crossref)
- an entry whose title does not match its live record is dropped, never kept

| key | source | verified against | title |
|-----|--------|------------------|-------|
| 0803.3693 | arxiv | arXiv id_list | Succinct Data Structures for Retrieval and Approximate Membership |
| 0805.1300 | arxiv | arXiv id_list | Throughput and Delay Analysis of Wireless Random Access Networks |
| 0805.4300 | arxiv | arXiv id_list | Balanced Families of Perfect Hash Functions and Their Applications |
| 0806.3284 | arxiv | arXiv id_list | Optimal hash functions for approximate closest pairs on the n-cube |
| 0811.3062 | arxiv | arXiv id_list | Dynamic External Hashing: The Limit of Buffering |
| 0901.1155 | arxiv | arXiv id_list | Balanced allocation: Memory performance tradeoffs |
| 0902.2206 | arxiv | arXiv id_list | Feature Hashing for Large Scale Multitask Learning |
| 0903.0391 | arxiv | arXiv id_list | De-amortized Cuckoo Hashing: Provable Worst-Case Performance and Experimental Results |
| 0903.4647 | arxiv | arXiv id_list | Phase Transitions in Gravitational Allocation |
| 0905.4100 | arxiv | arXiv id_list | Online Stochastic Matching: Beating 1-1/e |
| 0907.2563 | arxiv | arXiv id_list | Gossip-based Search in Multipeer Communication Networks |
| 0909.2547 | arxiv | arXiv id_list | Simple implementation of deletion from open-address hash table |
| 0910.0827 | arxiv | arXiv id_list | Performance of Statistical Tests for Single Source Detection using Random Matrix Theory |
| 0910.5147 | arxiv | arXiv id_list | Sharp Load Thresholds for Cuckoo Hashing |
| 0910.5535 | arxiv | arXiv id_list | Maximum Matchings in Random Bipartite Graphs and the Space Utilization of Cuckoo Hashtables |
| 0912.0287 | arxiv | arXiv id_list | Tight Thresholds for Cuckoo Hashing via XORSAT |
| 0912.5424 | arxiv | arXiv id_list | Backyard Cuckoo Hashing: Constant Worst-Case Operations with a Succinct Representation |
| 10.1007/11575832_11 | crossref | Crossref works/<doi> | Cache-Conscious Collision Resolution in String Hash Tables |
| 10.1007/978-3-642-14165-2_60 | crossref | Crossref works/<doi> | On the k-Independence Required by Linear Probing and Minwise Independence |
| 10.1007/978-3-642-27848-8_97-2 | crossref | Crossref works/<doi> | Cuckoo Hashing |
| 10.1007/pl00009208 | crossref | Crossref works/<doi> | The Analysis of Linear Probing Hashing with Buckets |
| 10.1017/cbo9780511813603.015 | crossref | Crossref works/<doi> | Balanced Allocations |
| 10.1109/71.963420 | crossref | Crossref works/<doi> | The power of two choices in randomized load balancing |
| 10.1109/sfcs.1982.39 | crossref | Crossref works/<doi> | Storing a sparse table with O(1) worst case access time |
| 10.1109/sfcs.1985.48 | crossref | Crossref works/<doi> | Robin hood hashing |
| 10.1109/sfcs.1988.21968 | crossref | Crossref works/<doi> | Dynamic perfect hashing: upper and lower bounds |
| 10.1145/100216.100245 | crossref | Crossref works/<doi> | The analysis of closed hashing under limited randomness |
| 10.1145/1090191.1080114 | crossref | Crossref works/<doi> | Fast hash table lookup using extended bloom filter: an aid to network processing |
| 10.1145/1250790.1250839 | crossref | Crossref works/<doi> | Linear probing with constant independence |
| 10.1145/2674005.2674994 | crossref | Crossref works/<doi> | Cuckoo Filter: Practically Better Than Bloom |
| 1004.2772 | arxiv | arXiv id_list | Boosting Multi-Core Reachability Performance with Shared Hash Tables |
| 1004.4548 | arxiv | arXiv id_list | Multiplication of sparse Laurent polynomials and Poisson series on modern hardware architectures |
| 1004.5373 | arxiv | arXiv id_list | The Forgetfulness of Balls and Bins |
| 1005.2616 | arxiv | arXiv id_list | Chains-into-Bins Processes |
| 1006.1231 | arxiv | arXiv id_list | On the Insertion Time of Cuckoo Hashing |
| 1007.1946 | arxiv | arXiv id_list | Maximum Bipartite Matching Size And Application to Cuckoo Hashing |
| 1011.5200 | arxiv | arXiv id_list | The Power of Simple Tabulation Hashing |
| 1104.5111 | arxiv | arXiv id_list | Cuckoo Hashing with Pages |
| 1104.5400 | arxiv | arXiv id_list | A cuckoo hashing variant with improved memory utilization and insertion time |
| 1104.5533 | arxiv | arXiv id_list | External-Memory Multimaps |
| 1107.4378 | arxiv | arXiv id_list | Fully De-Amortized Cuckoo Hashing for Cache-Oblivious Dictionaries and Multimaps |
| 1111.0762 | arxiv | arXiv id_list | Multidimensional Balanced Allocation for Multiple Choice & (1 + Beta) Processes |
| 1111.0801 | arxiv | arXiv id_list | Perfectly Balanced Allocation With Estimated Average Using Expected Constant Retries |
| 1201.5335 | arxiv | arXiv id_list | A new approach to the orientation of random hypergraphs |
| 1203.1506 | arxiv | arXiv id_list | Towards Optimal Degree-distributions for Left-perfect Matchings in Random Bipartite Graphs |
| 1204.4431 | arxiv | arXiv id_list | Explicit and Efficient Hash Families Suffice for Cuckoo Hashing with a Stash |
| 1205.1312 | arxiv | arXiv id_list | Converting online algorithms to local computation algorithms |
| 1205.2958 | arxiv | arXiv id_list | b-Bit Minwise Hashing in Practice: Large-Scale Batch and Online Learning and Using GPUs for Fast |
| 1206.1264 | arxiv | arXiv id_list | Heavy Traffic Optimal Resource Allocation Algorithms for Cloud Computing Clusters |
| 1206.3634 | arxiv | arXiv id_list | Balls into Bins: strict Capacities and Edge Weights |
| 1207.1659 | arxiv | arXiv id_list | Convergence of multivariate belief propagation, with applications to cuckoo hashing and load bal |
| 1207.2125 | arxiv | arXiv id_list | Balls into Bins via Local Search |
| 1207.2904 | arxiv | arXiv id_list | Effective Capacity of a Rayleigh Fading Channel in the Presence of Interference |
| 1209.5313 | arxiv | arXiv id_list | Random k-SAT and the Power of Two Choices |
| 1209.5360 | arxiv | arXiv id_list | Balanced Allocations and Double Hashing |
| 1210.4666 | arxiv | arXiv id_list | Asymptotic properties of covariate-adaptive randomization |
| 1211.3439 | arxiv | arXiv id_list | Optimal Hitting Sets for Combinatorial Shapes |
| 1304.0917 | arxiv | arXiv id_list | A Succinct Grammar Compression |
| 1304.2881 | arxiv | arXiv id_list | Balanced offline allocation of weighted balls into bins |
| 1305.5270 | arxiv | arXiv id_list | On adaptive posterior concentration rates |
| 1309.5616 | arxiv | arXiv id_list | Scan statistic tail probability assessment based on process covariance and window size |
| 1309.6772 | arxiv | arXiv id_list | The Multiple-orientability Thresholds for Random Hypergraphs |
| 1310.0801 | arxiv | arXiv id_list | Balls into bins via local search: cover time and maximum load |
| 1310.5367 | arxiv | arXiv id_list | Balanced Allocations: A Simple Proof for the Heavily Loaded Case |
| 1311.3121 | arxiv | arXiv id_list | Simple Tabulation, Fast Expanders, Double Tabulation, and High Independence |
| 1312.0526 | arxiv | arXiv id_list | Cache-Oblivious Peeling of Random Hypergraphs |
| 1312.4678 | arxiv | arXiv id_list | Simple, compact and robust approximate string dictionary |
| 1401.0223 | arxiv | arXiv id_list | Unbalanced Allocations |
| 1401.7616 | arxiv | arXiv id_list | A New Approach to Analyzing Robin Hood Hashing |
| 1402.3543 | arxiv | arXiv id_list | Inequalities and tail bounds for elementary symmetric polynomial with applications |
| 1403.5012 | arxiv | arXiv id_list | A Non-Cooperative Game Model for Reliability-Based Task Scheduling in Cloud Computing |
| 1404.0286 | arxiv | arXiv id_list | Wear Minimization for Cuckoo Hashing: How Not to Throw a Lot of Eggs into One Basket |
| 1404.1124 | arxiv | arXiv id_list | A Task Allocation Schema Based on Response Time Optimization in Cloud Computing |
| 1404.6724 | arxiv | arXiv id_list | Approximately Minwise Independence with Twisted Tabulation |
| 1404.7479 | arxiv | arXiv id_list | The Power of Two Choices in Distributed Voting |
| 1404.7688 | arxiv | arXiv id_list | On User Availability Prediction and Network Applications |
| 1406.2108 | arxiv | arXiv id_list | Linear time Constructions of some $d$-Restriction Problems |
| 1407.2575 | arxiv | arXiv id_list | Balanced Allocation on Graphs: A Random Walk Approach |
| 1407.6846 | arxiv | arXiv id_list | The Power of Two Choices with Simple Tabulation |
| 1407.8433 | arxiv | arXiv id_list | The 1-2-3-Toolkit for Building Your Own Balls-into-Bins Algorithm |
| 1408.0442 | arxiv | arXiv id_list | Power Distribution in Randomized Weighted Voting: the Effects of the Quota |
| 1409.5327 | arxiv | arXiv id_list | Store-Forward and its implications for Proportional Scheduling |
| 1410.5967 | arxiv | arXiv id_list | A unified approach to linear probing hashing with buckets |
| 1412.5889 | arxiv | arXiv id_list | Dense Testers: Almost Linear Time and Locally Explicit Constructions |
| 1501.00162 | arxiv | arXiv id_list | Expected number of uniformly distributed balls in a most loaded bin using placement with simple  |
| 1503.00658 | arxiv | arXiv id_list | More Analysis of Double Hashing for Balanced Allocations |
| 1503.04245 | arxiv | arXiv id_list | Bijection: Parking-like structures and Tree-like structures |
| 1503.06029 | arxiv | arXiv id_list | Massively Parallel Construction of the Cell Graph |
| 1503.08848 | arxiv | arXiv id_list | A conditional Berry-Esseen bound and a conditional large deviation result without Laplace transf |
| 1504.00788 | arxiv | arXiv id_list | The Power of Both Choices: Practical Load Balancing for Distributed Stream Processing Engines |
| 1504.02333 | arxiv | arXiv id_list | Lower bounds on $q$-wise independence tails and applications to min-entropy condensers |
| 1505.01523 | arxiv | arXiv id_list | Fast and Powerful Hashing using Tabulation |
| 1506.00718 | arxiv | arXiv id_list | Peeling Algorithm on Random Hypergraphs with Superlinear Number of Hyperedges |
| 1507.00954 | arxiv | arXiv id_list | Bounds and Constructions for $\overline{3}$-Separable Codes with Length $3$ |
| 1508.05253 | arxiv | arXiv id_list | Price of Fairness for Allocating a Bounded Resource |
| 1509.02235 | arxiv | arXiv id_list | Per-bucket concurrent rehashing algorithms |
| 1509.04549 | arxiv | arXiv id_list | Linear Probing with 5-Independent Hashing |
| 1510.07623 | arxiv | arXiv id_list | Partial Key Grouping: Load-Balanced Partitioning of Distributed Streams |
| 1601.04017 | arxiv | arXiv id_list | Concurrent Hash Tables: Fast and General?(!) |
| 1601.04807 | arxiv | arXiv id_list | Separating hash families: A Johnson-type bound and new constructions |
| 1602.04652 | arxiv | arXiv id_list | On the insertion time of random walk cuckoo hashing |
| 1602.08298 | arxiv | arXiv id_list | Balanced Allocation: Patience is not a Virtue |
| 1603.02188 | arxiv | arXiv id_list | Self-stabilizing Balls & Bins in Batches |
| 1603.02235 | arxiv | arXiv id_list | Deviation results for sparse tables in hashing with linear probing |
| 1603.04330 | arxiv | arXiv id_list | Fast Scalable Construction of (Minimal Perfect Hash) Functions |
| 1604.06067 | arxiv | arXiv id_list | Cuckoo Filter: Simplification and Analysis |
| 1605.04031 | arxiv | arXiv id_list | Robin Hood Hashing really has constant average search cost and variance in full tables |
| 1605.05236 | arxiv | arXiv id_list | Fast Concurrent Cuckoo Kick-Out Eviction Schemes for High-Density Tables |
| 1605.06581 | arxiv | arXiv id_list | On the Rate of Convergence of the Power-of-Two-Choices to its Mean-Field Limit |
| 1608.05678 | arxiv | arXiv id_list | Revisiting Reuse in Main Memory Database Systems |
| 1608.05699 | arxiv | arXiv id_list | Memory-efficient and Ultra-fast Network Lookup and Forwarding using Othello Hashing |
| 1608.07635 | arxiv | arXiv id_list | Random sets and intersections |
| 1609.09840 | arxiv | arXiv id_list | Regular and almost universal hashing: an efficient implementation |
| 1610.03803 | arxiv | arXiv id_list | Robust Scheduling for Flexible Processing Networks |
| 1610.05961 | arxiv | arXiv id_list | Proximity-Aware Balanced Allocations in Cache Networks |
| 1611.00029 | arxiv | arXiv id_list | A Simple Hash Class with Strong Randomness Properties in Graphs and Hypergraphs |
| 1611.04717 | arxiv | arXiv id_list | #Exploration: A Study of Count-Based Exploration for Deep Reinforcement Learning |
| 1611.07786 | arxiv | arXiv id_list | A Faster Algorithm for Cuckoo Insertion and Bipartite Matching in Large Graphs |
| 1702.03154 | arxiv | arXiv id_list | Fast and scalable minimal perfect hashing for massive key sets |
| 1702.03375 | arxiv | arXiv id_list | Derandomized Balanced Allocation |
| 1703.00667 | arxiv | arXiv id_list | A resource-frugal probabilistic dictionary and applications in bioinformatics |
| 1703.10575 | arxiv | arXiv id_list | Delay versus Stickiness Violation Trade-offs for Load Balancing in Large-Scale Data Centers |
| 1704.02054 | arxiv | arXiv id_list | Optimal Las Vegas Locality Sensitive Data Structures |
| 1704.06818 | arxiv | arXiv id_list | Adaptive Cuckoo Filters |
| 1705.00997 | arxiv | arXiv id_list | Dynamic Space Efficient Hashing |
| 1706.05085 | arxiv | arXiv id_list | Horcrux: A Password Manager for Paranoids |
| 1706.10209 | arxiv | arXiv id_list | Storage, Communication, and Load Balancing Trade-off in Distributed Cache Networks |
| 1707.03974 | arxiv | arXiv id_list | Paradeisos: a perfect hashing algorithm for many-body eigenvalue problems |
| 1707.06855 | arxiv | arXiv id_list | Load Thresholds for Cuckoo Hashing with Overlapping Blocks |
| 1707.09757 | arxiv | arXiv id_list | Coded Load Balancing in Cache Networks |
| 1708.04945 | arxiv | arXiv id_list | Balanced Allocation Through Random Walk |
| 1708.08663 | arxiv | arXiv id_list | Large ball probability, Gaussian comparison and anti-concentration |
| 1708.09059 | arxiv | arXiv id_list | Answering Spatial Multiple-Set Intersection Queries Using 2-3 Cuckoo Hash-Filters |
| 1709.04711 | arxiv | arXiv id_list | EMOMA: Exact Match in One Memory Access |
| 1710.00308 | arxiv | arXiv id_list | Load Balancing in Hypergraphs |
| 1711.08797 | arxiv | arXiv id_list | Practical Hash Functions for Similarity Estimation and Dimensionality Reduction |
| 1712.09494 | arxiv | arXiv id_list | Analysing the Performance of GPU Hash Tables for State Space Exploration |
| 1712.09624 | arxiv | arXiv id_list | Cuckoo++ Hash Tables: High-Performance Hash Tables for Networking Applications |
| 1801.00167 | arxiv | arXiv id_list | A Concentration Inequality for Random Polytopes, Dirichlet-Voronoi Tiling Numbers and the Geomet |
| 1801.01613 | arxiv | arXiv id_list | High Throughput Low Delay Wireless Multicast via Multi-Channel Moving Window Codes |
| 1801.02436 | arxiv | arXiv id_list | Asymptotic Miss Ratio of LRU Caching with Consistent Hashing |
| 1802.05471 | arxiv | arXiv id_list | Smooth heaps and a dual view of self-adjusting data structures |
| 1804.01018 | arxiv | arXiv id_list | Distributionally Linearizable Data Structures |
| 1804.09684 | arxiv | arXiv id_list | Power of $d$ Choices with Simple Tabulation |
| 1805.04794 | arxiv | arXiv id_list | Lock-Free Search Data Structures: Throughput Modelling with Poisson Processes |
| 1805.09423 | arxiv | arXiv id_list | Optimal Hashing in External Memory |
| 1806.02004 | arxiv | arXiv id_list | Another Proof of Cuckoo hashing with New Variants |
| 1806.03611 | arxiv | arXiv id_list | CuCoTrack: Cuckoo Filter Based Connection Tracking |
| 1807.01132 | arxiv | arXiv id_list | The power of thinning in balanced allocation |
| 1807.10083 | arxiv | arXiv id_list | Optimal Design in Hierarchical Models with application in Multi-center Trials |
| 1808.04602 | arxiv | arXiv id_list | Hashing with Linear Probing and Referential Integrity |
| 1809.02221 | arxiv | arXiv id_list | Time-dependent balls and bins model with positive feedback |
| 1809.04339 | arxiv | arXiv id_list | Concurrent Robin Hood Hashing |
| 1809.07471 | arxiv | arXiv id_list | Local Density Estimation in High Dimensions |
| 1809.08019 | arxiv | arXiv id_list | Propagation of Chaos for a Balls into Bins Model |
| 1810.02722 | arxiv | arXiv id_list | Balanced Allocation with Random Walk Based Sampling |
| 1810.04161 | arxiv | arXiv id_list | A Note On the Size of Largest Bins Using Placement With Linear Transformations |
| 1810.04254 | arxiv | arXiv id_list | Extreme Classification in Log Memory |
| 1810.09104 | arxiv | arXiv id_list | Norm-Range Partition: A Universal Catalyst for LSH based Maximum Inner Product Search (MIPS) |
| 1810.12086 | arxiv | arXiv id_list | A study on load-balanced variants of the bin packing problem |
| 1810.13029 | arxiv | arXiv id_list | BCL: A Cross-Platform Distributed Container Library |
| 1810.13187 | arxiv | arXiv id_list | Non-Empty Bins with Simple Tabulation Hashing |
| 1811.06444 | arxiv | arXiv id_list | Secretary Ranking with Minimal Inversions |
| 1811.06803 | arxiv | arXiv id_list | A Constructive Arboricity Approximation Scheme |
| 1901.08200 | arxiv | arXiv id_list | DistCache: Provable Load Balancing for Large-Scale Storage Systems with Distributed Caching |
| 1904.07532 | arxiv | arXiv id_list | Parallel Balanced Allocations: The Heavily Loaded Case |
| 1904.10639 | arxiv | arXiv id_list | Efficient Simulation Budget Allocation for Subset Selection Using Regression Metamodels |
| 1904.11323 | arxiv | arXiv id_list | Performance Prediction for Coarse-Grained Locking |
| 1905.00163 | arxiv | arXiv id_list | Separate Chaining Meets Compact Hashing |
| 1905.00369 | arxiv | arXiv id_list | Fast hashing with Strong Concentration Bounds |
| 1905.02776 | arxiv | arXiv id_list | Optimal Randomness in Swarm-Based Search |
| 1906.03876 | arxiv | arXiv id_list | Propagation of chaos for a General Balls into Bins dynamics |
| 1906.08296 | arxiv | arXiv id_list | Model-free posterior inference on the area under the receiver operating characteristic curve |
| 1907.02900 | arxiv | arXiv id_list | HashGraph -- Scalable Hash Tables Using A Sparse Graph Data Structure |
| 1907.04750 | arxiv | arXiv id_list | Efficient Gauss Elimination for Near-Quadratic Matrices with One Short Random Block per Row, wit |
| 1907.04930 | arxiv | arXiv id_list | Degenerate Turán densities of sparse hypergraphs |
| 1907.09579 | arxiv | arXiv id_list | ZKlaims: Privacy-preserving Attribute-based Credentials using Non-interactive Zero-knowledge Tec |
| 1908.10260 | arxiv | arXiv id_list | Asymptotic Results of a Multiple-entry Reinforcement Process |
| 1910.02158 | arxiv | arXiv id_list | RDMA vs. RPC for Implementing Distributed Data Structures |
| 1910.06416 | arxiv | arXiv id_list | RecSplit: Minimal Perfect Hashing via Recursive Splitting |
| 1910.13830 | arxiv | arXiv id_list | Extreme Classification in Log Memory using Count-Min Sketch: A Case Study of Amazon Search with  |
| 1911.01348 | arxiv | arXiv id_list | Nearly Optimal Static Las Vegas Succinct Dictionary |
| 1911.03028 | arxiv | arXiv id_list | Lock-Free Hopscotch Hashing |
| 1911.05170 | arxiv | arXiv id_list | The Power of Two Choices for Random Walks |
| 1911.10099 | arxiv | arXiv id_list | Constructing Minimal Perfect Hash Functions Using SAT Technology |
| 1912.08258 | arxiv | arXiv id_list | Xor Filters: Faster and Smaller Than Bloom and Cuckoo Filters |
| 1912.11118 | arxiv | arXiv id_list | Detecting stuffing of a user's credentials at her own accounts |
| 2001.03147 | arxiv | arXiv id_list | Age-Partitioned Bloom Filters |
| 2001.05053 | arxiv | arXiv id_list | Tight Static Lower Bounds for Non-Adaptive Data Structures |
| 2001.05293 | arxiv | arXiv id_list | Lazy object copy as a platform for population-based probabilistic programming |
| 2001.08250 | arxiv | arXiv id_list | Talek: Private Group Messaging with Hidden Access Patterns |
| 2001.10500 | arxiv | arXiv id_list | Peeling Close to the Orientability Threshold: Spatial Coupling in Hashing-Based Data Structures |
| 2001.11246 | arxiv | arXiv id_list | Mixing time for the Repeated Balls into Bins dynamics |
| 2003.03801 | arxiv | arXiv id_list | Multiset Synchronization with Counting Cuckoo Filters |
| 2003.07302 | arxiv | arXiv id_list | Dash: Scalable Hashing on Persistent Memory |
| 2004.01156 | arxiv | arXiv id_list | No Repetition: Fast Streaming with Highly Concentrated Hashing |
| 2004.08450 | arxiv | arXiv id_list | Reducing Commutativity Verification to Reachability with Differencing Abstractions |
| 2005.02537 | arxiv | arXiv id_list | Conditional Cuckoo Filters |
| 2006.00819 | arxiv | arXiv id_list | DHash: Enabling Dynamic and Efficient Hash Tables |
| 2006.07588 | arxiv | arXiv id_list | Balanced Allocation on Hypergraphs |
| 2006.15254 | arxiv | arXiv id_list | Optimizing Cuckoo Filter for high burst tolerance,low latency, and high throughput |
| 2006.15463 | arxiv | arXiv id_list | Queues with Small Advice |
| 2007.08311 | arxiv | arXiv id_list | A Genetic Algorithm for Obtaining Memory Constrained Near-Perfect Hashing |
| 2007.15497 | arxiv | arXiv id_list | Minimum Feedback for Collision-Free Scheduling in Massive Random Access |
| 2008.00793 | arxiv | arXiv id_list | Distributed Dispatching in the Parallel Server Model |
| 2008.07171 | arxiv | arXiv id_list | CARGO : Context Augmented Critical Region Offload for Network-bound datacenter Workloads |
| 2008.09406 | arxiv | arXiv id_list | $(2+ε)$-ANN for time series under the Fréchet distance |
| 2009.07914 | arxiv | arXiv id_list | WarpCore: A Library for fast Hash Tables on GPUs |
| 2010.01890 | arxiv | arXiv id_list | Generalized Cuckoo Hashing with a Stash, Revisited |
| 2010.08287 | arxiv | arXiv id_list | Heuristic for Edge-enabled Network Slicing Optimization using the Power of Two Choices |
| 2010.15206 | arxiv | arXiv id_list | Rosella: A Self-Driving Distributed Scheduler for Heterogeneous Clusters |
| 2011.02653 | arxiv | arXiv id_list | On the Analysis of Spatially Constrained Power of Two Choice Policies |
| 2011.04453 | arxiv | arXiv id_list | Improved List-Decodability of Reed--Solomon Codes via Tree Packings |
| 2011.07523 | arxiv | arXiv id_list | Thin-shell concentration for random vectors in Orlicz balls via moderate deviations and Gibbs me |
| 2012.01046 | arxiv | arXiv id_list | PiPoMonitor: Mitigating Cross-core Cache Attacks Using the Auto-Cuckoo Filter |
| 2012.06613 | arxiv | arXiv id_list | Beyond Scaling: Calculable Error Bounds of the Power-of-Two-Choices Mean-Field Model in Heavy-Tr |
| 2101.02343 | arxiv | arXiv id_list | Distributing hash families with few rows |
| 2103.01052 | arxiv | arXiv id_list | On the Cost of Unsuccessful Searches in Search Trees with Two-way Comparisons |
| 2103.12544 | arxiv | arXiv id_list | DeepBF: Malicious URL detection using Learned Bloom Filter and Evolutionary Deep Learning |
| 2104.05093 | arxiv | arXiv id_list | Load Balancing with Dynamic Set of Balls and Bins |
| 2104.10402 | arxiv | arXiv id_list | PTHash: Revisiting FCH Minimal Perfect Hashing |
| 2105.00766 | arxiv | arXiv id_list | Joint D2D Collaboration and Task Offloading for Edge Computing: A Mean Field Graph Approach |
| 2105.01409 | arxiv | arXiv id_list | Hardness-Preserving Reductions via Cuckoo Hashing |
| 2105.02393 | arxiv | arXiv id_list | Randomized and Balanced Allocation of Units into Treatment Groups Using the Finite Selection Mod |
| 2105.06741 | arxiv | arXiv id_list | A Heuristically Assisted Deep Reinforcement Learning Approach for Network Slice Placement |
| 2105.09508 | arxiv | arXiv id_list | Fast Nonblocking Persistence for Concurrent Data Structures |
| 2105.10622 | arxiv | arXiv id_list | Support Optimality and Adaptive Cuckoo Filters |
| 2105.13603 | arxiv | arXiv id_list | High Performance and Scalable NAT System on Commodity Platforms |
| 2106.02350 | arxiv | arXiv id_list | Parallel and External-Memory Construction of Minimal Perfect Hash Functions with PTHash |
| 2106.06051 | arxiv | arXiv id_list | The Power of Two Choices in Graphical Allocation |
| 2107.01250 | arxiv | arXiv id_list | Linear Probing Revisited: Tombstones Mark the Death of Primary Clustering |
| 2107.01464 | arxiv | arXiv id_list | When Are Learned Models Better Than Hash Functions? |
| 2107.02318 | arxiv | arXiv id_list | Incremental Edge Orientation in Forests |
| 2107.02866 | arxiv | arXiv id_list | Telescoping Filter: A Practical Adaptive Filter |
| 2107.03916 | arxiv | arXiv id_list | Balanced Allocations with Incomplete Information: The Power of Two Queries |
| 2107.08824 | arxiv | arXiv id_list | Verifying a Realistic Mutable Hash Table |
| 2108.07232 | arxiv | arXiv id_list | Better GPU Hash Tables |
| 2108.08497 | arxiv | arXiv id_list | Monarch: A Durable Polymorphic Memory For Data Intensive Applications |
| 2109.01947 | arxiv | arXiv id_list | Stretching Your Data With Taffy Filters |
| 2109.04548 | arxiv | arXiv id_list | Iceberg Hashing: Optimizing Many Hash-Table Criteria at Once |
| 2110.00511 | arxiv | arXiv id_list | ASH: A Modern Framework for Parallel Spatial Hashing in 3D Perception |
| 2110.05009 | arxiv | arXiv id_list | Long-term balanced allocation via thinning |
| 2110.10759 | arxiv | arXiv id_list | Balanced Allocations: Caching and Packing, Twinning and Thinning |
| 2111.00602 | arxiv | arXiv id_list | On the Optimal Time/Space Tradeoff for Hash Tables |
| 2111.01432 | arxiv | arXiv id_list | Practical and Light-weight Secure Aggregation for Federated Submodel Learning |
| 2111.06856 | arxiv | arXiv id_list | Approximate Membership Query Filters with a False Positive Free Set |
| 2111.12800 | arxiv | arXiv id_list | Tiny Pointers |
| 2111.14905 | arxiv | arXiv id_list | Bounding the Last Mile: Efficient Learned String Indexing |
| 2111.15172 | arxiv | arXiv id_list | Asymptotically Optimal Sampling Policy for Selecting Top-m Alternatives |
| 2201.01174 | arxiv | arXiv id_list | Binary Fuse Filters: Fast and Smaller Than Xor Filters |
| 2201.03126 | arxiv | arXiv id_list | An examination of the spillage distribution |
| 2201.07782 | arxiv | arXiv id_list | Contextual Ranking and Selection with Gaussian Processes |
| 2201.11899 | arxiv | arXiv id_list | Private Classical Communication over Quantum Multiple-Access Channels |
| 2202.05546 | arxiv | arXiv id_list | Insertion Time of Random Walk Cuckoo Hashing below the Peeling Threshold |
| 2202.10054 | arxiv | arXiv id_list | Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution |
| 2203.07621 | arxiv | arXiv id_list | Practical Detectability for Persistent Lock-Free Data Structures |
| 2203.12400 | arxiv | arXiv id_list | Tight Bounds for Repeated Balls-into-Bins |
| 2203.13902 | arxiv | arXiv id_list | Balanced Allocations in Batches: Simplified and Generalized |
| 2203.13957 | arxiv | arXiv id_list | Design and performance evaluation in Kiefer-Weiss problems when sampling from discrete exponenti |
| 2203.17139 | arxiv | arXiv id_list | Prefix Filter: Practically and Theoretically Better Than Bloom |
| 2204.00613 | arxiv | arXiv id_list | On the Importance of Asymmetry for Siamese Representation Learning |
| 2204.04057 | arxiv | arXiv id_list | The Power of Filling in Balanced Allocations |
| 2204.05724 | arxiv | arXiv id_list | Balls-in-bins models with asymmetric feedback and reflection |
| 2204.13087 | arxiv | arXiv id_list | Faster online calibration without randomization: interval forecasts and the power of two choices |
| 2205.01453 | arxiv | arXiv id_list | Understanding the Moments of Tabulation Hashing via Chaoses |
| 2205.06558 | arxiv | arXiv id_list | Balanced Allocations: The Heavily Loaded Case with Deletions |
| 2205.10255 | arxiv | arXiv id_list | Tower: Data Structures in Quantum Superposition |
| 2205.14494 | arxiv | arXiv id_list | Balls and Bins -- Simple Concentration Bounds |
| 2206.06461 | arxiv | arXiv id_list | Self-Supervised Representation Learning With MUlti-Segmental Informational Coding (MUSIC) |
| 2206.07503 | arxiv | arXiv id_list | Balanced Allocations with the Choice of Noise |
| 2206.12380 | arxiv | arXiv id_list | VIP Hashing -- Adapting to Skew in Popularity of Data on the Fly (extended version) |
| 2207.07533 | arxiv | arXiv id_list | Selection of the Most Probable Best |
| 2208.07489 | arxiv | arXiv id_list | Single Round-trip Hierarchical ORAM via Succinct Indices |
| 2208.07927 | arxiv | arXiv id_list | Semi-supervised Transfer Learning for Evaluation of Model Classification Performance |
| 2209.02220 | arxiv | arXiv id_list | Three Distributions in the Extended Occupancy Problem |
| 2209.03268 | arxiv | arXiv id_list | Measuring the Interpretability of Unsupervised Representations via Quantized Reverse Probing |
| 2209.06038 | arxiv | arXiv id_list | A Hash Table Without Hash Functions, and How to Get the Most Out of Your Random Bits |
| 2209.06955 | arxiv | arXiv id_list | Adversarial Correctness and Privacy for Probabilistic Data Structures |
| 2209.11809 | arxiv | arXiv id_list | Optimal Computing Budget Allocation for Data-driven Ranking and Selection |
| 2209.14667 | arxiv | arXiv id_list | Domain-aware Self-supervised Pre-training for Label-Efficient Meme Analysis |
| 2210.01560 | arxiv | arXiv id_list | SicHash -- Small Irregular Cuckoo Tables for Perfect Hashing |
| 2210.04068 | arxiv | arXiv id_list | IcebergHT: High Performance PMEM Hash Tables Through Stability and Low Associativity |
| 2210.11075 | arxiv | arXiv id_list | Freeze then Train: Towards Provable Representation Learning under Spurious Correlations and Feat |
| 2210.13097 | arxiv | arXiv id_list | Locality-Preserving Minimal Perfect Hashing of k-mers |
| 2211.01270 | arxiv | arXiv id_list | Secure and Efficient Privacy-preserving Authentication Scheme using Cuckoo Filter in Remote Pati |
| 2212.01887 | arxiv | arXiv id_list | The Optimality of Blocking Designs in Equally and Unequally Allocated Randomized Experiments wit |
| 2212.09562 | arxiv | arXiv id_list | High Performance Construction of RecSplit Based Minimal Perfect Hash Functions |
| 2212.11935 | arxiv | arXiv id_list | GraphTango: A Hybrid Representation Format for Efficient Streaming Graph Updates and Analysis |
| 2301.09810 | arxiv | arXiv id_list | Balanced Allocations with Heterogeneous Bins: The Power of Memory |
| 2301.10191 | arxiv | arXiv id_list | Distinct Elements in Streams: An Algorithm for the (Text) Book |
| 2301.10564 | arxiv | arXiv id_list | Succinct Planar Encoding with Minor Operations |
| 2302.04399 | arxiv | arXiv id_list | Balanced Allocations in Batches: The Tower of Two Choices |
| 2303.00869 | arxiv | arXiv id_list | The Power of Two Choices with Load Comparison Errors |
| 2303.18232 | arxiv | arXiv id_list | DIME-FM: DIstilling Multimodal and Efficient Foundation Models |
| 2304.04341 | arxiv | arXiv id_list | Regret Distribution in Stochastic Bandits: Optimal Trade-off between Expectation and Tail Risk |
| 2304.10520 | arxiv | arXiv id_list | Contrastive Tuning: A Little Help to Make Masked Autoencoders Forget |
| 2304.11012 | arxiv | arXiv id_list | Learned Monotone Minimal Perfect Hashing |
| 2305.03110 | arxiv | arXiv id_list | A Sparse Johnson-Lindenstrauss Transform using Fast Hashing |
| 2306.01968 | arxiv | arXiv id_list | On the Power of Delayed Flexibility: Balls, Bins, and a Few Opaque Promotions |
| 2306.02253 | arxiv | arXiv id_list | Tight Cell-Probe Lower Bounds for Dynamic Succinct Dictionaries |
| 2306.08842 | arxiv | arXiv id_list | ViP: A Differentially Private Foundation Model for Computer Vision |
| 2306.11220 | arxiv | arXiv id_list | Cuckoo Hashing in Cryptography: Optimal Parameters, Robustness and Applications |
| 2307.00644 | arxiv | arXiv id_list | What if we tried Less Power? -- Lessons from studying the power of choices in hashing-based data |
| 2307.13640 | arxiv | arXiv id_list | Optical Flow boosts Unsupervised Localization and Segmentation |
| 2308.02408 | arxiv | arXiv id_list | Evaluating the structure of cognitive tasks with transfer learning |
| 2308.02801 | arxiv | arXiv id_list | DiCuPIT: Distributed Cuckoo Filter-based Pending Interest Table |
| 2308.05087 | arxiv | arXiv id_list | Mean-Biased Processes for Balanced Allocations |
| 2308.09561 | arxiv | arXiv id_list | ShockHash: Towards Optimal-Space Minimal Perfect Hashing Beyond Brute-Force |
| 2308.10734 | arxiv | arXiv id_list | A Study of the Probability Distribution of the Balls in Bins Process with Power Law Feedback |
| 2308.11083 | arxiv | arXiv id_list | An Improved Drift Theorem for Balanced Allocations |
| 2308.11295 | arxiv | arXiv id_list | Uncertainty Estimation of Transformers' Predictions via Topological Analysis of the Attention Ma |
| 2308.13632 | arxiv | arXiv id_list | ChainedFilter: Combining Membership Filters by Chain Rule |
| 2308.14134 | arxiv | arXiv id_list | Locally Uniform Hashing |
| 2309.02450 | arxiv | arXiv id_list | Self-Supervised Video Transformers for Isolated Sign Language Recognition |
| 2309.03045 | arxiv | arXiv id_list | An Evaluation of Software Sketches |
| 2309.03999 | arxiv | arXiv id_list | Adapting Self-Supervised Representations to Multi-Domain Setups |
| 2309.05308 | arxiv | arXiv id_list | Two-way Linear Probing Revisited |
| 2309.05972 | arxiv | arXiv id_list | Self-supervised Extraction of Human Motion Structures via Frame-wise Discrete Features |
| 2309.09359 | arxiv | arXiv id_list | Concurrent Deterministic Skiplist and Other Data Structures |
| 2310.04342 | arxiv | arXiv id_list | Minerva: Decentralized Collaborative Query Processing over InterPlanetary File System |
| 2310.05240 | arxiv | arXiv id_list | Limitations of Stochastic Selection with Pairwise Independent Priors |
| 2310.14959 | arxiv | arXiv id_list | ShockHash: Near Optimal-Space Minimal Perfect Hashing Beyond Brute-Force |
| 2311.04743 | arxiv | arXiv id_list | Sharper analysis of the random graph $d$-process via a balls-in-bins model |
| 2311.09671 | arxiv | arXiv id_list | Generalization Bounds for Robust Contrastive Learning: From Theory to Practice |
| 2312.02366 | arxiv | arXiv id_list | Evaluating General Purpose Vision Foundation Models for Medical Image Analysis: An Experimental  |
| 2312.04000 | arxiv | arXiv id_list | LiDAR: Sensing Linear Probing Performance in Joint Embedding SSL Architectures |
| 2312.10019 | arxiv | arXiv id_list | Understanding Probe Behaviors through Variational Bounds of Mutual Information |
| 2401.08652 | arxiv | arXiv id_list | An Efficient Dynamic Transaction Storage Mechanism for Sustainable High Throughput Bitcoin |
| 2401.08833 | arxiv | arXiv id_list | Revisiting Self-supervised Learning of Speech Representation from a Mutual Information Perspecti |
| 2401.14394 | arxiv | arXiv id_list | O(1) Insertion for Random Walk d-ary Cuckoo Hashing up to the Load Threshold |
| 2402.10093 | arxiv | arXiv id_list | MIM-Refiner: A Contrastive Learning Boost from Intermediate Pre-Trained Representations |
| 2402.10482 | arxiv | arXiv id_list | Rethinking Self-Distillation: Label Averaging and Enhanced Soft Label Refinement with Partial La |
| 2403.04200 | arxiv | arXiv id_list | ACC-ViT : Atrous Convolution's Comeback in Vision Transformers |
| 2403.10153 | arxiv | arXiv id_list | Improving Medical Multi-modal Contrastive Learning with Expert Annotations |
| 2403.10696 | arxiv | arXiv id_list | On the low-shot transferability of [V]-Mamba |
| 2403.11441 | arxiv | arXiv id_list | Experimental Quantum Byzantine Agreement on a Three-User Quantum Network with Integrated Photoni |
| 2403.19531 | arxiv | arXiv id_list | SecGraph: Towards SGX-based Efficient and Confidentiality-Preserving Graph Search |
| 2404.07011 | arxiv | arXiv id_list | An asymptotically optimal algorithm for generating bin cardinalities |
| 2404.12172 | arxiv | arXiv id_list | How to Benchmark Vision Foundation Models for Semantic Segmentation? |
| 2404.18497 | arxiv | arXiv id_list | PHOBIC: Perfect Hashing with Optimized Bucket Sizes and Interleaved Coding |
| 2405.08787 | arxiv | arXiv id_list | Explicit Orthogonal Arrays and Universal Hashing with Arbitrary Parameters |
| 2405.10253 | arxiv | arXiv id_list | Adaptive Quotient Filters |
| 2405.10876 | arxiv | arXiv id_list | Steady-State Convergence of the Continuous-Time Routing System with General Distributions in Hea |
| 2405.12414 | arxiv | arXiv id_list | The Power of Two in Token Systems |
| 2405.16747 | arxiv | arXiv id_list | Understanding Linear Probing then Fine-tuning Language Models from NTK Perspective |
| 2405.16989 | arxiv | arXiv id_list | Uncertainty Learning for High-dimensional Mean-variance Portfolio |
| 2406.06363 | arxiv | arXiv id_list | Automating Food Drop: The Power of Two Choices for Dynamic and Fair Food Allocation |
| 2406.09255 | arxiv | arXiv id_list | Compact Parallel Hash Tables on the GPU |
| 2406.18099 | arxiv | arXiv id_list | CompassDB: Pioneering High-Performance Key-Value Store with Perfect Hash |
| 2407.07718 | arxiv | arXiv id_list | High-Performance Sorting-Based k-mer Counting in Distributed Memory with Flexible Hybrid Paralle |
| 2407.08131 | arxiv | arXiv id_list | Asynchronous measurement-device-independent quantum digital signatures |
| 2407.12210 | arxiv | arXiv id_list | A Closer Look at Benchmarking Self-Supervised Pre-training with Image Classification |
| 2409.11280 | arxiv | arXiv id_list | Tight Bounds for Classical Open Addressing |
| 2409.13566 | arxiv | arXiv id_list | Deep Learning and Machine Learning, Advancing Big Data Analytics and Management: Tensorflow Pret |
| 2411.07810 | arxiv | arXiv id_list | Routing algorithm within the multiple non-overlapping paths approach for quantum key distributio |
| 2411.10695 | arxiv | arXiv id_list | Series Expansion of Probability of Correct Selection for Improved Finite Budget Allocation in Ra |
| 2411.12365 | arxiv | arXiv id_list | Brief Announcement: Parallel Construction of Bumped Ribbon Retrieval |
| 2411.19394 | arxiv | arXiv id_list | Hashing for Sampling-Based Estimation |
| 2412.04616 | arxiv | arXiv id_list | Assessing and Learning Alignment of Unimodal Vision and Language Models |
| 2412.10655 | arxiv | arXiv id_list | Optimal Static Dictionary with Worst-Case Constant Query Time |
| 2412.11084 | arxiv | arXiv id_list | BarcodeMamba: State Space Models for Biodiversity Analysis |
| 2501.02305 | arxiv | arXiv id_list | Optimal Bounds for Open Addressing Without Reordering |
| 2501.02312 | arxiv | arXiv id_list | Efficient $d$-ary Cuckoo Hashing at High Load Factors by Bubbling Up |
| 2501.03402 | arxiv | arXiv id_list | On the Adversarial Robustness of Benjamini Hochberg |
| 2501.04005 | arxiv | arXiv id_list | LargeAD: Large-Scale Cross-Sensor Data Pretraining for Autonomous Driving |
| 2501.07879 | arxiv | arXiv id_list | Distributed Nonparametric Estimation: from Sparse to Dense Samples per Terminal |
| 2501.11014 | arxiv | arXiv id_list | Transfer Learning Strategies for Pathological Foundation Models: A Systematic Evaluation in Brai |
| 2501.11582 | arxiv | arXiv id_list | Tight Analyses of Ordered and Unordered Linear Probing |
| 2501.11855 | arxiv | arXiv id_list | A New Construction Structure on Coded Caching with Linear Subpacketization: Non-Half-Sum Disjoin |
| 2501.12074 | arxiv | arXiv id_list | Optimizing Portfolio Performance through Clustering and Sharpe Ratio-Based Optimization: A Compa |
| 2501.14685 | arxiv | arXiv id_list | Rethinking Foundation Models for Medical Image Classification through a Benchmark Study on MedMN |
| 2501.15098 | arxiv | arXiv id_list | CFT-RAG: An Entity Tree Based Retrieval Augmented Generation Algorithm With Cuckoo Filter |
| 2501.18977 | arxiv | arXiv id_list | Blocked Bloom Filters with Choices |
| 2501.19086 | arxiv | arXiv id_list | Fairness Analysis of CLIP-Based Foundation Models for X-Ray Image Classification |
| 2502.03566 | arxiv | arXiv id_list | CLIP Behaves like a Bag-of-Words Model Cross-modally but not Uni-modally |
| 2502.04226 | arxiv | arXiv id_list | Keep It Light! Simplifying Image Clustering Via Text-Free Adapters |
| 2502.05613 | arxiv | arXiv id_list | Combined Search and Encoding for Seeds, with an Application to Minimal Perfect Hashing |
| 2502.05851 | arxiv | arXiv id_list | Fairness Driven Slot Allocation Problem in Billboard Advertisement |
| 2502.10977 | arxiv | arXiv id_list | The Bathroom Model: A Realistic Approach to Hash Table Algorithm Optimization |
| 2502.13197 | arxiv | arXiv id_list | Girth of the Cayley graph and Cayley hash functions |
| 2502.15021 | arxiv | arXiv id_list | Thicker and Quicker: A Jumbo Token for Fast Plain Vision Transformers |
| 2502.15539 | arxiv | arXiv id_list | PtrHash: Minimal Perfect Hashing at RAM Throughput |
| 2503.05007 | arxiv | arXiv id_list | Dynamic Indexing Through Learned Indices with Worst-case Guarantees |
| 2503.10161 | arxiv | arXiv id_list | MorphisHash: Improving Space Efficiency of ShockHash for Minimal Perfect Hashing |
| 2503.10171 | arxiv | arXiv id_list | Verifiable, Efficient and Confidentiality-Preserving Graph Search with Transparency |
| 2503.13628 | arxiv | arXiv id_list | Optimal Non-Oblivious Open Addressing |
| 2503.15282 | arxiv | arXiv id_list | SENAI: Towards Software Engineering Native Generative Artificial Intelligence |
| 2503.21016 | arxiv | arXiv id_list | History-Independent Concurrent Hash Tables |
| 2504.08635 | arxiv | arXiv id_list | Latent Diffusion Autoencoders: Toward Efficient and Meaningful Unsupervised Representation Learn |
| 2504.14374 | arxiv | arXiv id_list | A fast MPI-based Distributed Hash-Table as Surrogate Model demonstrated in a coupled reactive tr |
| 2504.17918 | arxiv | arXiv id_list | PHast -- Perfect Hashing made fast |
| 2504.20001 | arxiv | arXiv id_list | Engineering Minimal k-Perfect Hash Functions |
| 2505.05847 | arxiv | arXiv id_list | Smaller and More Flexible Cuckoo Filters |
| 2505.15195 | arxiv | arXiv id_list | Self-Boost via Optimal Retraining: An Analysis via Approximate Message Passing |
| 2505.21571 | arxiv | arXiv id_list | FCOS: A Two-Stage Recoverable Model Pruning Framework for Automatic Modulation Recognition |
| 2506.05329 | arxiv | arXiv id_list | Admissibility of Completely Randomized Trials: A Large-Deviation Approach |
| 2506.06536 | arxiv | arXiv id_list | Modern Minimal Perfect Hashing: A Survey |
| 2506.10178 | arxiv | arXiv id_list | Attention, Please! Revisiting Attentive Probing Through the Lens of Efficiency |
| 2506.11777 | arxiv | arXiv id_list | Self-supervised Learning of Echocardiographic Video Representations via Online Cluster Distillat |
| 2506.21826 | arxiv | arXiv id_list | Few-Shot Segmentation of Historical Maps via Linear Probing of Vision Foundation Models |
| 2506.22567 | arxiv | arXiv id_list | Unifying Biomedical Vision-Language Expertise: Towards a Generalist Foundation Model via Multi-C |
| 2507.00737 | arxiv | arXiv id_list | Dispersion models on a circle: universal properties and asymptotic results |
| 2507.03931 | arxiv | arXiv id_list | The Supermarket Model on a Dynamic Regular Hypergraph |
| 2507.09080 | arxiv | arXiv id_list | BioAnalyst: A Foundation Model for Biodiversity |
| 2507.14828 | arxiv | arXiv id_list | eMargin: Revisiting Contrastive Learning with Margin-Based Separation |
| 2508.03611 | arxiv | arXiv id_list | Astrolabe: Balancing Load in LLM Serving with Randomized Prediction-Guided Scheduling |
| 2508.08180 | arxiv | arXiv id_list | RedDino: A foundation model for red blood cell analysis |
| 2508.12527 | arxiv | arXiv id_list | A Polylogarithmic Competitive Algorithm for Stochastic Online Sorting and TSP |
| 2508.18613 | arxiv | arXiv id_list | ModAn-MulSupCon: Modality-and Anatomy-Aware Multi-Label Supervised Contrastive Pretraining for M |
| 2509.00812 | arxiv | arXiv id_list | Adaptive t Design Dummy-Gate Obfuscation for Cryogenic Scale Enforcement |
| 2509.02232 | arxiv | arXiv id_list | Efficient Geometry Compression and Communication for 3D Gaussian Splatting Point Clouds |
| 2509.16407 | arxiv | arXiv id_list | WarpSpeed: A High-Performance Library for Concurrent GPU Hash Tables |
| 2509.20786 | arxiv | arXiv id_list | LiLAW: Lightweight Learnable Adaptive Weighting to Learn Sample Difficulty & Improve Noisy Train |
| 2509.24793 | arxiv | arXiv id_list | Sparse Autoencoders Make Audio Foundation Models more Explainable |
| 2510.05518 | arxiv | arXiv id_list | Time To Replace Your Filter: How Maplets Simplify System Design |
| 2510.06185 | arxiv | arXiv id_list | Probabilistic Guarantees to Explicit Constructions: Local Properties of Linear Codes |
| 2510.06892 | arxiv | arXiv id_list | Stress concentration via quasi-Minnaert resonance in bubble-elastic structures and applications |
| 2510.07104 | arxiv | arXiv id_list | Permutations in competing growth processes and balls-in-bins |
| 2510.07870 | arxiv | arXiv id_list | Symmetric Rule-Based Achlioptas Processes for Random $k$-SAT |
| 2510.10015 | arxiv | arXiv id_list | End-to-end Compositional Verification of Program Safety through Verified and Verifying Compilati |
| 2510.14798 | arxiv | arXiv id_list | Balls and Bins and the Infinite Process with Random Deletions |
| 2510.15095 | arxiv | arXiv id_list | Hive Hash Table: A Warp-Cooperative, Dynamically Resizable Hash Table for GPUs |
| 2510.27629 | arxiv | arXiv id_list | Best Practices for Biorisk Evaluations on Open-Weight Bio-Foundation Models |
| 2511.01910 | arxiv | arXiv id_list | Security Audit of intel ICE Driver for e810 Network Interface Card |
| 2511.04053 | arxiv | arXiv id_list | Interpreting Multi-Attribute Confounding through Numerical Attributes in Large Language Models |
| 2511.09742 | arxiv | arXiv id_list | Feature Quality and Adaptability of Medical Foundation Models: A Comparative Evaluation for Radi |
| 2511.12158 | arxiv | arXiv id_list | Data-Efficient Self-Supervised Algorithms for Fine-Grained Birdsong Analysis |
| 2511.18124 | arxiv | arXiv id_list | MIDAS: Adaptive Proxy Middleware for Mitigating Metadata Hotspots in HPC I/O at Scale |
| 2512.02340 | arxiv | arXiv id_list | Reasoning Path and Latent State Analysis for Multi-view Visual Spatial Reasoning: A Cognitive Sc |
| 2512.08513 | arxiv | arXiv id_list | Minimax and Bayes Optimal Adaptive Experimental Design for Treatment Choice |
| 2601.08358 | arxiv | arXiv id_list | Linear probing enables Ship-Radiated Noise recognition with pretrained audio embeddings |
| 2601.10874 | arxiv | arXiv id_list | Balanced allocation: considerations from large scale service environments |
| 2601.17396 | arxiv | arXiv id_list | GO-OSC and VASH: Geometry-Aware Representation Learning for Early Degradation Detection in Oscil |
| 2601.17883 | arxiv | arXiv id_list | EEG-FM-Compass: Progress, Benchmarking, and Future Directions for EEG Foundation Models |
| 2601.20678 | arxiv | arXiv id_list | Helper-Assisted Coding for Gaussian Wiretap Channels: Deep Learning Meets PhySec |
| 2602.04297 | arxiv | arXiv id_list | Revisiting Prompt Sensitivity in Large Language Models for Text Classification: The Role of Prom |
| 2602.06502 | arxiv | arXiv id_list | DualMap: Enabling Both Cache Affinity and Load Balancing for Distributed LLM Serving |
| 2602.14672 | arxiv | arXiv id_list | MeFEm: Medical Face Embedding model |
| 2602.17050 | arxiv | arXiv id_list | Multi-Probe Zero Collision Hash (MPZCH): Mitigating Embedding Collisions and Enhancing Model Fre |
| 2602.18888 | arxiv | arXiv id_list | Dual-Kernel Adapter: Expanding Spatial Horizons for Data-Constrained Medical Image Analysis |
| 2602.23533 | arxiv | arXiv id_list | Few-Shot Continual Learning for 3D Brain MRI with Frozen Foundation Models |
| 2603.00898 | arxiv | arXiv id_list | High Probability Work Efficient Parallel Algorithms |
| 2603.01476 | arxiv | arXiv id_list | Entropy-Guided GRVQ for Ultra-Low Bitrate Neural Speech Codec |
| 2603.04081 | arxiv | arXiv id_list | Revisiting the Role of Foundation Models in Cell-Level Histopathological Image Analysis under Sm |
| 2603.04165 | arxiv | arXiv id_list | PlaneCycle: Training-Free 2D-to-3D Lifting of Foundation Models Without Adapters |
| 2603.05280 | arxiv | arXiv id_list | Layer by layer, module by module: Choose both for optimal OOD probing of ViT |
| 2603.05956 | arxiv | arXiv id_list | Fair and Efficient Balanced Allocation for Indivisible Goods |
| 2603.06405 | arxiv | arXiv id_list | Tag-specific Regret Minimization Problem in Outdoor Advertising |
| 2603.07645 | arxiv | arXiv id_list | Evaluating Synthetic Data for Baggage Trolley Detection in Airport Logistics |
| 2603.15251 | arxiv | arXiv id_list | Space Upper Bounds for $α$-Perfect Hashing |
| 2603.15486 | arxiv | arXiv id_list | Cuckoo-GPU: Accelerating Cuckoo Filters on Modern GPUs |
| 2603.17168 | arxiv | arXiv id_list | HierarchicalKV: A GPU Hash Table with Cache Semantics for Continuous Online Embedding Storage |
| 2603.17228 | arxiv | arXiv id_list | From Drop-off to Recovery: A Mechanistic Analysis of Segmentation in MLLMs |
| 2603.17624 | arxiv | arXiv id_list | Do Language Models Encode Semantic Relations? Probing and Sparse Feature Analysis |
| 2603.20060 | arxiv | arXiv id_list | Power laws and power-of-two-choices |
| 2603.23211 | arxiv | arXiv id_list | The NCS-Model: A seismic foundation model trained on the Norwegian repository of public data |
| 2603.26668 | arxiv | arXiv id_list | Bridge-RAG: An Abstract Bridge Tree Based Retrieval Augmented Generation Algorithm |
| 2603.26907 | arxiv | arXiv id_list | Information-Theoretic Solutions for Seedless QRNG Bootstrapping and Hybrid PQC-QKD Key Combinati |
| 2603.27218 | arxiv | arXiv id_list | Unsupervised Evaluation of Deep Audio Embeddings for Music Structure Analysis |
| 2603.27518 | arxiv | arXiv id_list | Over-Refusal and Representation Subspaces: A Mechanistic Analysis of Task-Conditioned Refusal in |
| 2604.03928 | arxiv | arXiv id_list | Supervised Dimensionality Reduction Revisited: Why LDA on Frozen CNN Features Deserves a Second  |
| 2604.04037 | arxiv | arXiv id_list | Geometric Limits of Knowledge Distillation: A Minimum-Width Theorem via Superposition Theory |
| 2604.04159 | arxiv | arXiv id_list | Online Graph Balancing and the Power of Two Choices |
| 2604.05649 | arxiv | arXiv id_list | Analogical Reasoning as a Doctor: A Foundation Model for Gastrointestinal Endoscopy Diagnosis |
| 2604.07259 | arxiv | arXiv id_list | Pilot Allocation for Multi-Hop Over-the-Air Neural Inference under Imperfect CSI |
| 2604.08087 | arxiv | arXiv id_list | DeepForestSound: a multi-species automatic detector for passive acoustic monitoring in African t |
| 2604.14128 | arxiv | arXiv id_list | Rhetorical Questions in LLM Representations: A Linear Probing Study |
| 2604.18519 | arxiv | arXiv id_list | LLM Safety From Within: Detecting Harmful Content with Internal Representations |
| 2604.23719 | arxiv | arXiv id_list | AIPsy-Affect: A Keyword-Free Clinical Stimulus Battery for Mechanistic Interpretability of Emoti |
| 2604.28160 | arxiv | arXiv id_list | From Quantum Shots to Training Data: Reorganizing Measurement Records in Quantum Machine Learnin |
| 2605.02904 | arxiv | arXiv id_list | StateSMix: Online Lossless Compression via Mamba State Space Models and Sparse N-gram Context Mi |
| 2605.09881 | arxiv | arXiv id_list | Dissecting Jet-Tagger Through Mechanistic Interpretability |
| 2605.11875 | arxiv | arXiv id_list | Modulation Consistency-based Contrastive Learning for Self-Supervised Automatic Modulation Class |
| 2605.15486 | arxiv | arXiv id_list | Hybrid LLM-based Intelligent Framework for Robot Task Scheduling |
| 2605.19462 | arxiv | arXiv id_list | When Does Self-Supervised Learning Transfer to Time-Series Tasks? |
| 2605.20105 | arxiv | arXiv id_list | Optimal Representation Size: High-Dimensional Analysis of Pretraining and Linear Probing |
| 2605.20302 | arxiv | arXiv id_list | Neural Collapse by Design: Learning Class Prototypes on the Hypersphere |
| 2605.21835 | arxiv | arXiv id_list | An Open Multi-Center Whole-Body FDG PET/CT Foundation Model for Tumor Segmentation |
| 2605.29549 | arxiv | arXiv id_list | Learning Representations from 3D Gaussian Splats |
| 2605.29700 | arxiv | arXiv id_list | Using Set Shaping Theory to Trade RAM Accesses for CPU Computation |
| 2605.30482 | arxiv | arXiv id_list | Discovering a Zeta Map Algorithm on Dyck Paths via Mechanistic Interpretability |
| 2606.09317 | arxiv | arXiv id_list | A Comparative Study of Pre-trained Speech Encoders and Training Objectives for Large-Scale Indic |
| 2606.09850 | arxiv | arXiv id_list | Mechanistic Analysis of Alignment Algorithms in Language Models |
| 2606.10778 | arxiv | arXiv id_list | From Patches to Patients: A study of the tile-to-slide performance transferability in Digital Pa |
| 2606.17315 | arxiv | arXiv id_list | Space-Efficient Lock-Free Linear-Probing Hash Table |
| 2606.21973 | arxiv | arXiv id_list | SPOTR: Spatio-temporal Pooling One-Token Reconstruction for Universal Physiological Signal Self- |
| 2606.24073 | arxiv | arXiv id_list | Hash Table Design for RDMA:Challenges and Opportunities |
| 2606.31626 | arxiv | arXiv id_list | PrISM-IQA: Image Quality Assessment Made Practical for Smartphone Photography |
| 2606.31811 | arxiv | arXiv id_list | MuSViT: A Foundation Vision Model for Sheet Music Representation |
| 2607.00946 | arxiv | arXiv id_list | A Geometric Perspective on Composable Emotion Steering in Text-to-Speech Models |
| 2607.03304 | arxiv | arXiv id_list | Adaptive Loss Balancing for Multi-Task Bioacoustic Classification of Bird Species and Call Types |
| 2607.05226 | arxiv | arXiv id_list | The Exact Worst-Case Tail Probability under Bounded Kurtosis |
| 2607.06211 | arxiv | arXiv id_list | Load Balancing under Adaptive Bin Deletions |
| 2607.06392 | arxiv | arXiv id_list | InsideSSL: Understanding Self-Supervised Speech Representations using a Model-Centric Perspectiv |
| 2607.07257 | arxiv | arXiv id_list | Non-Minimal $k$-Perfect Hashing: Tight Lower Bounds and an Application to Fast Static Hash Table |
| 2607.13247 | arxiv | arXiv id_list | Quadratic Probing Revisited: Smoothed Analysis and the Fall of Robin Hood |
| 2607.13728 | arxiv | arXiv id_list | Cluster with Auctions for Vector Search |
| 2607.14703 | arxiv | arXiv id_list | Pretraining Multiple Instance Learning Networks with Multi-Teacher Distillation from Pathology S |
| 2607.15321 | arxiv | arXiv id_list | Rethinking the Readout: Unlocking Video Backbones for AI-Generated Video Detection |
| 2607.16390 | arxiv | arXiv id_list | Locality in Open Addressing Hash Tables |
| 2607.17494 | arxiv | arXiv id_list | Linear Probing with Non-Greedy Insertions |
| 2607.20704 | arxiv | arXiv id_list | RAMSES-GPU: Cell-by-Cell Adaptive Mesh Refinement with Magneto-Hydrodynamics and Self-Gravity on |
| 2607.24545 | arxiv | arXiv id_list | Fast Insertion for Bucketized Cuckoo Hashing |
| 2607.25183 | arxiv | arXiv id_list | Stochastic Load Balancing with Machine Reservations |
| 2607.26530 | arxiv | arXiv id_list | When to Treeify Hash Table Buckets: A Reproducible C Study of List, Hybrid, and Red-Black Tree C |
| 2607.27157 | arxiv | arXiv id_list | Bounded Independence for $k$-Min-Wise Hashing: Tight Bounds and Limitations of Structured Hashin |
| 2607.28892 | arxiv | arXiv id_list | Succinct and Fast Tiny Pointer Hash Tables |
| 2608.02486 | arxiv | arXiv id_list | Cultural Awareness is Represented but Not Decoded: Tracing Mythological Knowledge across 18 Open |
| 2608.04381 | arxiv | arXiv id_list | NodeJEPA: Structure-Conditioned Latent Prediction for Node-Level Graph Self-Supervised Learning |
| 2608.06325 | arxiv | arXiv id_list | Fair and Efficient Balanced Allocations for Additive Valuations |
| 2608.06638 | arxiv | arXiv id_list | MI-MIDI: Mechanistic Interpretability of Text-to-MIDI Generation Models via Probing, Lenses and  |
| 2608.07609 | arxiv | arXiv id_list | Hit Selection Using SSMD-Based Machine Learning Performance Metrics in High-Throughput Screening |
| 2608.08013 | arxiv | arXiv id_list | A Simple Analysis of Quadratic Probing and Other Open Addressing Schemes |
| 2608.08287 | arxiv | arXiv id_list | What Irregularity Costs: CUDA C++, Rust, and Triton on a Hash-Blocked GPU Workload |
| 2608.08425 | arxiv | arXiv id_list | PSP: Low-Overhead Packet-Level Load Balancing for Stale-State and Bandwidth-Asymmetric Networks |
| 2608.13970 | arxiv | arXiv id_list | CavityRank: Zero-Extra-Byte Residual Routing for Cuckoo Filters |
| 2608.15790 | arxiv | arXiv id_list | CrevasseSeg: A Label-Efficient UAV Crevasse Segmentation Framework |
| 2608.16123 | arxiv | arXiv id_list | A Simple Las Vegas Algorithm for Sparse Nonnegative Convolution |
| 2608.20924 | arxiv | arXiv id_list | Generalized Balls into Bins |
| 2608.24597 | arxiv | arXiv id_list | Taming foundation model with invariance-oriented pre-training for broad-spectrum EEG analysis ac |
| 2608.28512 | arxiv | arXiv id_list | Quadratic Probing Insertions Are $ε^{-(1+o(1))}$ Time |
| 2609.03600 | arxiv | arXiv id_list | Employing the Structural Power to Achieve Supply-Demand Balanced Payment Channel Networks |
| 2609.09854 | arxiv | arXiv id_list | When Does Low-Bit Quantization Preserve the Decisions of Vector Search? |
| 2609.12584 | arxiv | arXiv id_list | Clustering-Based Balanced Sampling and Allocation with Data Parallelism for High-Performance Fin |
| 2609.14924 | arxiv | arXiv id_list | Sharp Gaussian Asymptotics for Marginals of Euclidean Balls |
| 2609.18554 | arxiv | arXiv id_list | CARA: Collision-Aware Resolution Adaptation for Multiresolution Hash Encoding Based Image Fittin |
| 2609.19685 | arxiv | arXiv id_list | Almost Optimal FPT Inapproximability for k-SetCover |
| 2609.22337 | arxiv | arXiv id_list | When and Why Do Linear Bias Probes Fail? A Geometric and Statistical Theory of Bias Detectabilit |
| 2609.24736 | arxiv | arXiv id_list | MiTHras: Task-specific Hierarchical Semi-supervised Contrastive Masked Autoencoder for Mitotic F |
| 2609.35405 | arxiv | arXiv id_list | Reduce, Then Encode: Multiscale Volumetric Reduction for 2D Foundation Models in Brain MRI |
| 2609.38726 | arxiv | arXiv id_list | Local decisions, diffusive influence, and lower bounds for graphical balanced allocation |
| 2609.39233 | arxiv | arXiv id_list | MultiTable: A Faster Hash Table at any Physical Load Factor up to and Including One |
| 2609.39557 | arxiv | arXiv id_list | Consensus for Compressed Static Functions |
| 2610.00414 | arxiv | arXiv id_list | From Image Latent Space to Fuzzy Rules: Interpretable Analysis of Gastrointestinal Foundation Mo |
| 2610.00688 | arxiv | arXiv id_list | The Power of Two-Choice Linear Probing |
| 2610.02385 | arxiv | arXiv id_list | Fine-Grained Analysis of SIMD-Based Hash Table Implementations |
| 2610.04830 | arxiv | arXiv id_list | Cluster Validation Indices as Self-Supervised Objectives for Text Representation Learning |
| 2610.10245 | arxiv | arXiv id_list | MorphCL: Morphological Contrastive Learning for Inertial-based Human Activity Recognition |
| 2610.11525 | arxiv | arXiv id_list | Should Your Database Systems Use Hardware-Assisted Memory Safety Extensions in Production? |
| cond-mat/0205336 | arxiv | arXiv id_list | Exact Solution of a Drop-push Model for Percolation |
| cs/0303011 | arxiv | arXiv id_list | Lock-free dynamic hash tables with open addressing |
| cs/0303022 | arxiv | arXiv id_list | Probabilistic behavior of hash tables |
| cs/0407023 | arxiv | arXiv id_list | Efficient Hashing with Lookups in two Memory Accesses |
| cs/0502032 | arxiv | arXiv id_list | On Dynamic Range Reporting in One Dimension |
| cs/0506098 | arxiv | arXiv id_list | Distributed Selfish Load Balancing |
| cs/0510086 | arxiv | arXiv id_list | Balanced Allocation on Graphs |
| cs/0608037 | arxiv | arXiv id_list | Cascade hash tables: a series of multilevel double hashing schemes with O(1) worst case lookup t |
| cs/0702159 | arxiv | arXiv id_list | Perfect Hashing for Data Management Applications |
| cs/9801103 | arxiv | arXiv id_list | Linear probing and graphs |
| hep-lat/9608085 | arxiv | arXiv id_list | Improvements for Vachaspati-Vilenkin-type Algorithms for Cosmic String and Disclination Formatio |
| hep-ph/9412264 | arxiv | arXiv id_list | Fermi Ball Detection |
| math/0501060 | arxiv | arXiv id_list | Phase transition for parking blocks, Brownian excursion and coalescence |
| math/0508451 | arxiv | arXiv id_list | On the power of two choices: Balls and bins in continuous time |
| math/0510415 | arxiv | arXiv id_list | The Onset of Dominance in Balls-in-Bins Processes with Feedback |
| math/0510648 | arxiv | arXiv id_list | Balls-in-bins with feedback and Brownian Motion |
| math/0510663 | arxiv | arXiv id_list | Avoiding defeat in a balls-in-bins process with feedback |
