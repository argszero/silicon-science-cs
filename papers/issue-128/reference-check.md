# Reference authenticity check -- issue #128

Every entry **cited by the manuscript** was checked against a LIVE external record, comparing
the returned TITLE against the stored title (two-sided token match, threshold 0.80).  A
resolver that merely answers is not enough: a remembered identifier can resolve to a
DIFFERENT real paper, so the check is the title comparison, not the HTTP status.

- sources: arXiv API `id_list` (batched, `max_results` set per chunk) + Crossref `works/<doi>`
- verified pool: 527 entries; **cited by the manuscript: 126** (119 arXiv, 7 Crossref)
- last full pass: 2026-10-07T14:41:52Z  rc=0  VERIFIED 527 / 527 ; TITLE MISMATCH 0 ; TRANSPORT-UNKNOWN 0 (batches failed: 0)
- an entry is dropped, never kept, if its title does not match; the manuscript may cite only
  pool entries, so the list below is a subset of the verified pool by construction

| ref | citation key | source | verified against | title as returned | link |
|-----|--------------|--------|------------------|-------------------|------|
| [1] | `arxiv:1802.05733` | arxiv | arXiv id_list | Fair Clustering Through Fairlets | https://arxiv.org/abs/1802.05733 |
| [2] | `arxiv:1901.08628` | arxiv | arXiv id_list | Fair k-Center Clustering for Data Summarization | https://arxiv.org/abs/1901.08628 |
| [3] | `arxiv:1901.08668` | arxiv | arXiv id_list | Guarantees for Spectral Clustering with Fairness Constraints | https://arxiv.org/abs/1901.08668 |
| [4] | `doi:10.1109/cvprw.2009.5206852` | crossref | Crossref works/<doi> | Constrained clustering via spectral regularization | https://doi.org/10.1109/cvprw.2009.5206852 |
| [5] | `arxiv:2009.03078` | arxiv | arXiv id_list | Achieving anonymity via weak lower bound constraints for k-median and k-means | https://arxiv.org/abs/2009.03078 |
| [6] | `doi:10.1145/2487575.2487636` | crossref | Crossref works/<doi> | Diversity maximization under matroid constraints | https://doi.org/10.1145/2487575.2487636 |
| [7] | `arxiv:2502.02530` | arxiv | arXiv id_list | Max-Min Diversification with Asymmetric Distances | https://arxiv.org/abs/2502.02530 |
| [8] | `doi:10.1145/2940716.2940726` | crossref | Crossref works/<doi> | The Unreasonable Fairness of Maximum Nash Welfare | https://doi.org/10.1145/2940716.2940726 |
| [9] | `arxiv:1704.00222` | arxiv | arXiv id_list | Fair Allocation of Indivisible Goods: Improvement and Generalization | https://arxiv.org/abs/1704.00222 |
| [10] | `arxiv:1905.09947` | arxiv | arXiv id_list | Affirmative Action Policies for Top-k Candidates Selection, With an Application to the Design of Policies for University Admissions | https://arxiv.org/abs/1905.09947 |
| [11] | `arxiv:2010.06986` | arxiv | arXiv id_list | On the Problem of Underranking in Group-Fair Ranking | https://arxiv.org/abs/2010.06986 |
| [12] | `arxiv:1508.05253` | arxiv | arXiv id_list | Price of Fairness for Allocating a Bounded Resource | https://arxiv.org/abs/1508.05253 |
| [13] | `arxiv:1406.5722` | arxiv | arXiv id_list | The price of fairness for a small number of indivisible items | https://arxiv.org/abs/1406.5722 |
| [14] | `doi:10.24963/ijcai.2019/12` | crossref | Crossref works/<doi> | The Price of Fairness for Indivisible Goods | https://doi.org/10.24963/ijcai.2019/12 |
| [15] | `arxiv:2103.02512` | arxiv | arXiv id_list | Approximation Algorithms for Socially Fair Clustering | https://arxiv.org/abs/2103.02512 |
| [16] | `arxiv:2206.11210` | arxiv | arXiv id_list | Constant-Factor Approximation Algorithms for Socially Fair $k$-Clustering | https://arxiv.org/abs/2206.11210 |
| [17] | `arxiv:2202.06259` | arxiv | arXiv id_list | New Approximation Algorithms for Fair $k$-median Problem | https://arxiv.org/abs/2202.06259 |
| [18] | `arxiv:2002.07892` | arxiv | arXiv id_list | Fair Clustering with Multiple Colors | https://arxiv.org/abs/2002.07892 |
| [19] | `arxiv:1907.08906` | arxiv | arXiv id_list | A Constant Approximation for Colorful k-Center | https://arxiv.org/abs/1907.08906 |
| [20] | `arxiv:2007.04059` | arxiv | arXiv id_list | Fair Colorful k-Center Clustering | https://arxiv.org/abs/2007.04059 |
| [21] | `arxiv:2101.12403` | arxiv | arXiv id_list | Fair Resource Allocation for Demands with Sharp Lower Tail Inequalities | https://arxiv.org/abs/2101.12403 |
| [22] | `arxiv:2002.07682` | arxiv | arXiv id_list | How to Solve Fair $k$-Center in Massive Data Models | https://arxiv.org/abs/2002.07682 |
| [23] | `arxiv:2302.09911` | arxiv | arXiv id_list | Fair $k$-Center: a Coreset Approach in Low Dimensions | https://arxiv.org/abs/2302.09911 |
| [24] | `arxiv:2207.11337` | arxiv | arXiv id_list | Fair Range k-center | https://arxiv.org/abs/2207.11337 |
| [25] | `arxiv:2205.14358` | arxiv | arXiv id_list | Fair Labeled Clustering | https://arxiv.org/abs/2205.14358 |
| [26] | `arxiv:2104.12116` | arxiv | arXiv id_list | Fair-Capacitated Clustering | https://arxiv.org/abs/2104.12116 |
| [27] | `arxiv:2006.04960` | arxiv | arXiv id_list | A Notion of Individual Fairness for Clustering | https://arxiv.org/abs/2006.04960 |
| [28] | `arxiv:2002.06742` | arxiv | arXiv id_list | Individual Fairness for $k$-Clustering | https://arxiv.org/abs/2002.06742 |
| [29] | `arxiv:2106.14043` | arxiv | arXiv id_list | Improved Approximation Algorithms for Individually Fair Clustering | https://arxiv.org/abs/2106.14043 |
| [30] | `arxiv:2412.04943` | arxiv | arXiv id_list | A Subquadratic Time Approximation Algorithm for Individually Fair k-Center | https://arxiv.org/abs/2412.04943 |
| [31] | `arxiv:2006.12589` | arxiv | arXiv id_list | Distributional Individual Fairness in Clustering | https://arxiv.org/abs/2006.12589 |
| [32] | `arxiv:2109.04554` | arxiv | arXiv id_list | Feature-based Individual Fairness in k-Clustering | https://arxiv.org/abs/2109.04554 |
| [33] | `arxiv:2510.06130` | arxiv | arXiv id_list | Local Search-based Individually Fair Clustering with Outliers | https://arxiv.org/abs/2510.06130 |
| [34] | `arxiv:2412.10923` | arxiv | arXiv id_list | Linear Programming based Approximation to Individually Fair k-Clustering with Outliers | https://arxiv.org/abs/2412.10923 |
| [35] | `arxiv:1906.08484` | arxiv | arXiv id_list | Coresets for Clustering with Fairness Constraints | https://arxiv.org/abs/1906.08484 |
| [36] | `arxiv:2007.10137` | arxiv | arXiv id_list | On Coresets for Fair Clustering in Metric and Euclidean Spaces and Their Applications | https://arxiv.org/abs/2007.10137 |
| [37] | `arxiv:1812.10854` | arxiv | arXiv id_list | Fair Coresets and Streaming Algorithms for Fair k-Means Clustering | https://arxiv.org/abs/1812.10854 |
| [38] | `arxiv:2605.13759` | arxiv | arXiv id_list | Fast and effective algorithms for fair clustering at scale | https://arxiv.org/abs/2605.13759 |
| [39] | `arxiv:2602.21509` | arxiv | arXiv id_list | Fair Model-based Clustering | https://arxiv.org/abs/2602.21509 |
| [40] | `arxiv:2602.11500` | arxiv | arXiv id_list | A Generic Framework for Fair Consensus Clustering in Streams | https://arxiv.org/abs/2602.11500 |
| [41] | `doi:10.1145/3442188.3445906` | crossref | Crossref works/<doi> | Socially Fair k-Means Clustering | https://doi.org/10.1145/3442188.3445906 |
| [42] | `arxiv:2202.01391` | arxiv | arXiv id_list | Fair Representation Clustering with Several Protected Classes | https://arxiv.org/abs/2202.01391 |
| [43] | `arxiv:1910.05113` | arxiv | arXiv id_list | Fairness in Clustering with Multiple Sensitive Attributes | https://arxiv.org/abs/1910.05113 |
| [44] | `arxiv:2006.11009` | arxiv | arXiv id_list | Fair clustering via equitable group representations | https://arxiv.org/abs/2006.11009 |
| [45] | `arxiv:1905.03674` | arxiv | arXiv id_list | Proportionally Fair Clustering | https://arxiv.org/abs/1905.03674 |
| [46] | `arxiv:2310.18162` | arxiv | arXiv id_list | Proportional Fairness in Clustering: A Social Choice Perspective | https://arxiv.org/abs/2310.18162 |
| [47] | `arxiv:2312.10369` | arxiv | arXiv id_list | Proportional Representation in Metric Spaces and Low-Distortion Committee Selection | https://arxiv.org/abs/2312.10369 |
| [48] | `arxiv:2301.03862` | arxiv | arXiv id_list | Proportionally Fair Matching with Multiple Groups | https://arxiv.org/abs/2301.03862 |
| [49] | `arxiv:2502.10068` | arxiv | arXiv id_list | Proportional Clustering, the $β$-Plurality Problem, and Metric Distortion | https://arxiv.org/abs/2502.10068 |
| [50] | `arxiv:2410.23273` | arxiv | arXiv id_list | Proportional Fairness in Non-Centroid Clustering | https://arxiv.org/abs/2410.23273 |
| [51] | `arxiv:2606.07285` | arxiv | arXiv id_list | Improved Lower Bounds for Proportionally Fair Clustering | https://arxiv.org/abs/2606.07285 |
| [52] | `arxiv:1704.02183` | arxiv | arXiv id_list | Proportional Approval Voting, Harmonic k-median, and Negative Association | https://arxiv.org/abs/1704.02183 |
| [53] | `arxiv:2211.12820` | arxiv | arXiv id_list | Fairly Allocating Utility in Constrained Multiwinner Elections | https://arxiv.org/abs/2211.12820 |
| [54] | `arxiv:2512.24934` | arxiv | arXiv id_list | Fair Committee Selection under Ordinal Preferences and Limited Cardinal Information | https://arxiv.org/abs/2512.24934 |
| [55] | `arxiv:2402.16145` | arxiv | arXiv id_list | Egalitarian Price of Fairness for Indivisible Goods | https://arxiv.org/abs/2402.16145 |
| [56] | `arxiv:2205.10836` | arxiv | arXiv id_list | On the Price of Fairness of Allocating Contiguous Blocks | https://arxiv.org/abs/2205.10836 |
| [57] | `arxiv:1701.08230` | arxiv | arXiv id_list | Algorithmic decision making and the cost of fairness | https://arxiv.org/abs/1701.08230 |
| [58] | `arxiv:2606.20461` | arxiv | arXiv id_list | Data Bias Mitigation under Coverage Constraints & The Price of Fairness | https://arxiv.org/abs/2606.20461 |
| [59] | `arxiv:2602.05707` | arxiv | arXiv id_list | Fix Representation (Optimally) Before Fairness: Finite-Sample Shrinkage Population Correction and the True Price of Fairness Under Subpopulation Shift | https://arxiv.org/abs/2602.05707 |
| [60] | `arxiv:cs/0310037` | arxiv | arXiv id_list | Maximum dispersion and geometric maximum weight cliques | https://arxiv.org/abs/cs/0310037 |
| [61] | `arxiv:1203.6397` | arxiv | arXiv id_list | Max-Sum Diversification, Monotone Submodular Functions and Dynamic Updates | https://arxiv.org/abs/1203.6397 |
| [62] | `arxiv:1511.02402` | arxiv | arXiv id_list | Max-Sum Diversification, Monotone Submodular Functions and Semi-metric Spaces | https://arxiv.org/abs/1511.02402 |
| [63] | `arxiv:1511.07077` | arxiv | arXiv id_list | Max-sum diversity via convex programming | https://arxiv.org/abs/1511.07077 |
| [64] | `arxiv:1607.04557` | arxiv | arXiv id_list | Local Search for Max-Sum Diversification | https://arxiv.org/abs/1607.04557 |
| [65] | `arxiv:1809.09521` | arxiv | arXiv id_list | Diversity maximization in doubling metrics | https://arxiv.org/abs/1809.09521 |
| [66] | `arxiv:1605.05590` | arxiv | arXiv id_list | MapReduce and Streaming Algorithms for Diversity Maximization in Metric Spaces of Bounded Doubling Dimension | https://arxiv.org/abs/1605.05590 |
| [67] | `arxiv:1607.06203` | arxiv | arXiv id_list | Greedy bi-criteria approximations for $k$-medians and $k$-means | https://arxiv.org/abs/1607.06203 |
| [68] | `arxiv:2302.07771` | arxiv | arXiv id_list | Fully dynamic clustering and diversity maximization in doubling metrics | https://arxiv.org/abs/2302.07771 |
| [69] | `arxiv:2002.03175` | arxiv | arXiv id_list | A General Coreset-Based Approach to Diversity Maximization under Matroid Constraints | https://arxiv.org/abs/2002.03175 |
| [70] | `arxiv:2301.02053` | arxiv | arXiv id_list | Max-Min Diversification with Fairness Constraints: Exact and Approximation Algorithms | https://arxiv.org/abs/2301.02053 |
| [71] | `arxiv:2411.02845` | arxiv | arXiv id_list | Max-Distance Sparsification for Diversification and Clustering | https://arxiv.org/abs/2411.02845 |
| [72] | `arxiv:2307.04329` | arxiv | arXiv id_list | Improved Diversity Maximization Algorithms for Matching and Pseudoforest | https://arxiv.org/abs/2307.04329 |
| [73] | `arxiv:2002.03256` | arxiv | arXiv id_list | Diversity and Inclusion Metrics in Subset Selection | https://arxiv.org/abs/2002.03256 |
| [74] | `arxiv:2203.01857` | arxiv | arXiv id_list | Improved Approximation Algorithms and Lower Bounds for Search-Diversification Problems | https://arxiv.org/abs/2203.01857 |
| [75] | `arxiv:2211.02176` | arxiv | arXiv id_list | Connected k-Center and k-Diameter Clustering | https://arxiv.org/abs/2211.02176 |
| [76] | `doi:10.1137/1.9781611973402.106` | crossref | Crossref works/<doi> | Submodular Maximization with Cardinality Constraints | https://doi.org/10.1137/1.9781611973402.106 |
| [77] | `arxiv:1204.4526` | arxiv | arXiv id_list | A Tight Combinatorial Algorithm for Submodular Maximization Subject to a Matroid Constraint | https://arxiv.org/abs/1204.4526 |
| [78] | `arxiv:1101.4450` | arxiv | arXiv id_list | Adaptive Submodular Optimization under Matroid Constraints | https://arxiv.org/abs/1101.4450 |
| [79] | `arxiv:1705.06319` | arxiv | arXiv id_list | Constrained Submodular Maximization via Greedy Local Search | https://arxiv.org/abs/1705.06319 |
| [80] | `arxiv:1508.02157` | arxiv | arXiv id_list | Deterministic Algorithms for Submodular Maximization Problems | https://arxiv.org/abs/1508.02157 |
| [81] | `arxiv:1007.1632` | arxiv | arXiv id_list | Submodular Maximization by Simulated Annealing | https://arxiv.org/abs/1007.1632 |
| [82] | `arxiv:2312.14299` | arxiv | arXiv id_list | Fairness in Submodular Maximization over a Matroid Constraint | https://arxiv.org/abs/2312.14299 |
| [83] | `arxiv:2305.15118` | arxiv | arXiv id_list | Fairness in Streaming Submodular Maximization over a Matroid Constraint | https://arxiv.org/abs/2305.15118 |
| [84] | `arxiv:2304.06596` | arxiv | arXiv id_list | Beyond Submodularity: A Unified Framework of Randomized Set Selection with Group Fairness Constraints | https://arxiv.org/abs/2304.06596 |
| [85] | `arxiv:1411.0541` | arxiv | arXiv id_list | Distributed Submodular Maximization | https://arxiv.org/abs/1411.0541 |
| [86] | `arxiv:2002.05477` | arxiv | arXiv id_list | Approximability of Monotone Submodular Function Maximization under Cardinality and Matroid Constraints in the Streaming Model | https://arxiv.org/abs/2002.05477 |
| [87] | `arxiv:2102.09679` | arxiv | arXiv id_list | Improved Multi-Pass Streaming Algorithms for Submodular Maximization with Matroid Constraints | https://arxiv.org/abs/2102.09679 |
| [88] | `arxiv:2204.13832` | arxiv | arXiv id_list | Efficient Algorithms for Monotone Non-Submodular Maximization with Partition Matroid Constraint | https://arxiv.org/abs/2204.13832 |
| [89] | `arxiv:2408.03583` | arxiv | arXiv id_list | Deterministic Algorithm and Faster Algorithm for Submodular Maximization subject to a Matroid Constraint | https://arxiv.org/abs/2408.03583 |
| [90] | `arxiv:1811.03093` | arxiv | arXiv id_list | An Optimal Approximation for Submodular Maximization under a Matroid Constraint in the Adaptive Complexity Model | https://arxiv.org/abs/1811.03093 |
| [91] | `arxiv:1607.07957` | arxiv | arXiv id_list | On maximizing a monotone k-submodular function subject to a matroid constraint | https://arxiv.org/abs/1607.07957 |
| [92] | `arxiv:2307.13996` | arxiv | arXiv id_list | Fast algorithms for k-submodular maximization subject to a matroid constraint | https://arxiv.org/abs/2307.13996 |
| [93] | `arxiv:1611.08060` | arxiv | arXiv id_list | On ($1$, $ε$)-Restricted Max-Min Fair Allocation Problem | https://arxiv.org/abs/1611.08060 |
| [94] | `arxiv:1703.01649` | arxiv | arXiv id_list | Fair Allocation of Indivisible Goods to Asymmetric Agents | https://arxiv.org/abs/1703.01649 |
| [95] | `arxiv:2202.08713` | arxiv | arXiv id_list | Algorithmic Fair Allocation of Indivisible Items: A Survey and New Questions | https://arxiv.org/abs/2202.08713 |
| [96] | `arxiv:1806.00218` | arxiv | arXiv id_list | Asymptotic Existence of Proportionally Fair Allocations | https://arxiv.org/abs/1806.00218 |
| [97] | `arxiv:1906.02775` | arxiv | arXiv id_list | Fair Division Without Disparate Impact | https://arxiv.org/abs/1906.02775 |
| [98] | `arxiv:2410.15738` | arxiv | arXiv id_list | A Fair Allocation is Approximately Optimal for Indivisible Chores, or Is It? | https://arxiv.org/abs/2410.15738 |
| [99] | `arxiv:2406.15009` | arxiv | arXiv id_list | Fair, Manipulation-Robust, and Transparent Sortition | https://arxiv.org/abs/2406.15009 |
| [100] | `arxiv:2006.10498` | arxiv | arXiv id_list | Neutralizing Self-Selection Bias in Sampling for Sortition | https://arxiv.org/abs/2006.10498 |
| [101] | `doi:10.1109/tii.2023.3342888` | crossref | Crossref works/<doi> | Balanced Fair K-Means Clustering | https://doi.org/10.1109/tii.2023.3342888 |
| [102] | `arxiv:2401.05502` | arxiv | arXiv id_list | Diversity-aware clustering: Computational Complexity and Approximation Algorithms | https://arxiv.org/abs/2401.05502 |
| [103] | `arxiv:2301.08460` | arxiv | arXiv id_list | Coresets for Constrained Clustering: General Assignment Constraints and Improved Size Bounds | https://arxiv.org/abs/2301.08460 |
| [104] | `arxiv:1809.00932` | arxiv | arXiv id_list | Faster Balanced Clusterings in High Dimension | https://arxiv.org/abs/1809.00932 |
| [105] | `arxiv:2112.03183` | arxiv | arXiv id_list | Modification-Fair Cluster Editing | https://arxiv.org/abs/2112.03183 |
| [106] | `arxiv:2204.00893` | arxiv | arXiv id_list | On resolution coresets for constrained clustering | https://arxiv.org/abs/2204.00893 |
| [107] | `arxiv:2504.06980` | arxiv | arXiv id_list | Clustering under Constraints: Efficient Parameterized Approximation Schemes | https://arxiv.org/abs/2504.06980 |
| [108] | `arxiv:2006.13699` | arxiv | arXiv id_list | On Fair Selection in the Presence of Implicit Variance | https://arxiv.org/abs/2006.13699 |
| [109] | `arxiv:1905.10870` | arxiv | arXiv id_list | Equal Opportunity and Affirmative Action via Counterfactual Predictions | https://arxiv.org/abs/1905.10870 |
| [110] | `arxiv:2004.10846` | arxiv | arXiv id_list | Reducing the Filtering Effect in Public School Admissions: A Bias-aware Analysis for Targeted Interventions | https://arxiv.org/abs/2004.10846 |
| [111] | `arxiv:2007.01202` | arxiv | arXiv id_list | Towards Data-Driven Affirmative Action Policies under Uncertainty | https://arxiv.org/abs/2007.01202 |
| [112] | `arxiv:2112.14074` | arxiv | arXiv id_list | On the Equivalence of Two Competing Affirmative Actions in School Choice | https://arxiv.org/abs/2112.14074 |
| [113] | `arxiv:2106.08652` | arxiv | arXiv id_list | Maxmin-Fair Ranking: Individual Fairness under Group-Fairness Constraints | https://arxiv.org/abs/2106.08652 |
| [114] | `arxiv:2010.04412` | arxiv | arXiv id_list | Fair and Representative Subset Selection from Data Streams | https://arxiv.org/abs/2010.04412 |
| [115] | `arxiv:2204.13019` | arxiv | arXiv id_list | Allocating with Priorities and Quotas: Algorithms, Complexity, and Dynamics | https://arxiv.org/abs/2204.13019 |
| [116] | `arxiv:2110.15503` | arxiv | arXiv id_list | A Pre-processing Method for Fairness in Ranking | https://arxiv.org/abs/2110.15503 |
| [117] | `arxiv:1610.08452` | arxiv | arXiv id_list | Fairness Beyond Disparate Treatment & Disparate Impact: Learning Classification without Disparate Mistreatment | https://arxiv.org/abs/1610.08452 |
| [118] | `arxiv:1801.05398` | arxiv | arXiv id_list | On the Direction of Discrimination: An Information-Theoretic Analysis of Disparate Impact in Machine Learning | https://arxiv.org/abs/1801.05398 |
| [119] | `arxiv:2310.20673` | arxiv | arXiv id_list | Balancing Act: Constraining Disparate Impact in Sparse Models | https://arxiv.org/abs/2310.20673 |
| [120] | `arxiv:2202.09724` | arxiv | arXiv id_list | Bayes-Optimal Classifiers under Group Fairness | https://arxiv.org/abs/2202.09724 |
| [121] | `arxiv:2208.10451` | arxiv | arXiv id_list | Minimax AUC Fairness: Efficient Algorithm with Provable Convergence | https://arxiv.org/abs/2208.10451 |
| [122] | `arxiv:2102.12258` | arxiv | arXiv id_list | Classification with abstention but without disparities | https://arxiv.org/abs/2102.12258 |
| [123] | `arxiv:2607.06709` | arxiv | arXiv id_list | A scalable linear programming-based framework for data clustering | https://arxiv.org/abs/2607.06709 |
| [124] | `arxiv:1603.09535` | arxiv | arXiv id_list | Local search yields approximation schemes for k-means and k-median in Euclidean and minor-free metrics | https://arxiv.org/abs/1603.09535 |
| [125] | `arxiv:1711.08715` | arxiv | arXiv id_list | Interpolating between $k$-Median and $k$-Center: Approximation Algorithms for Ordered $k$-Median | https://arxiv.org/abs/1711.08715 |
| [126] | `arxiv:2407.08295` | arxiv | arXiv id_list | Hybrid k-Clustering: Blending k-Median and k-Center | https://arxiv.org/abs/2407.08295 |
