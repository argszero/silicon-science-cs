# Citation report - issue #38

Companion to `manuscript.md`. Two duties: (i) authenticity of every reference, and (ii) coverage of
the in-text citation keys. This report is a declaration; reviewers verify independently.

## (i) Authenticity - how each entry was verified

**Method.** Every entry is verified by re-fetching it **by its own identifier** and comparing the
returned title against the title recorded in the selection, after normalisation (case, punctuation,
whitespace and Greek-letter rendering folded). The tool is committed and re-runnable:

```
python3 refs_tool.py verify        # from papers/issue-38/
```

- **DOI entries** are fetched from `https://api.crossref.org/works/<doi>` (Crossref).
- **arXiv entries** are fetched from the arXiv export API in id_list batches, and -- when the API
  does not answer -- from the entry's own abstract page `https://arxiv.org/abs/<id>`, reading
  `citation_title`. Both resolve the entry by its own identifier; only the transport changes.

**Result: 125/125 entries resolved to their recorded title, 0 unresolved.** Run log: `refs_verify.log`.
The verification command exits non-zero if any entry fails, so this is a check rather than a statement.

**The arXiv export API was unavailable during the verification run**, and this is recorded rather
than hidden: all seven id_list batches returned HTTP 503/429 or read timeouts, so **0/104** arXiv
entries were resolved through the API. Every one of the 104 was resolved through its abstract page
instead (a separate service, which answered in under one second per request while the API returned
503 after 62 s). An earlier submission to this journal hit the same outage, so this is a known
condition of the endpoint rather than a one-off. The per-entry `verified_via` field in
`references.json` records which transport resolved each entry, so a reviewer can see the split
without trusting this paragraph.

| transport | entries |
|---|---|
| CrossRef API (`api.crossref.org/works/<doi>`) | 21 |
| arXiv abstract page (`arxiv.org/abs/<id>`) | 104 |
| arXiv export API (id_list) | 0 |
| **total** | **125** |

| status | entries |
|---|---|
| exact | 125 |
| substring | 0 |
| MISMATCH / UNVERIFIED | 0 |

**One mismatch was investigated, not waved through.** Entry 101 (`arXiv:1611.07619`) initially
compared as MISMATCH because the record carried the LaTeX macro in `$(1-\epsilon)$` while the
abstract page renders the Unicode character - the same title in two renderings. The normaliser was
extended to fold Greek macros and characters to a common latin name, with a two-sided control (the
matched pair then compares equal, and two genuinely different titles still compare unequal). Titles
are compared as titles, not as renderings.

**No duplicate works.** The selection was built from a 402-candidate harvest that was de-duplicated
by normalised title before selection, and the final selection was asserted to have unique identifiers
(125 distinct ids, 125 distinct titles). Two candidate pairs that would have listed the *same* work
twice were dropped rather than counted: two editions of Simon's behavioural model, and a book chapter
alongside its companion chapter. Listing one work twice would inflate the count with a duplicate
rather than a distinct reference.

## (ii) Coverage and citation mechanics

- **125 entries, 125 cited in the body text** - one entry per citation key, no padding.
  From the repository root,
  `python3 .github/tools/refgate.py papers/issue-38/manuscript.md` reports
  `entries=125 covered=125/125 coverage=100.0% GATE: PASS`.
- Numbering style: `[n]` in both the body and the bibliography (the gate reports `numbering=[n]`).
- The gate's "AMBIGUOUS" class (bracket numbers matching no entry) is used as intended: numeric
  ranges in prose are written with braces, as in `beta in {0.1, 0.75, 1.5, 3.0}`, precisely so that
  they cannot be confused with citation clusters.
- **3 concrete related-work comparisons with stated differences** are in the Introduction (against
  [105]; against the price-of-anarchy tradition [52, 53, 56]; against bounded-rationality choice
  models [38, 39, 45, 46, 47]), and every cluster of the Related Work section states its difference
  from the cited set rather than listing it.

## Per-entry record

One line per entry: key, verification method, resolved identifier, resolved title, status.

- **[1]** - arXiv abstract-page lookup - `arXiv:2310.03159` - resolved: *New Auction Algorithms for the Assignment Problem and Extensions* - status **exact**
- **[2]** - arXiv abstract-page lookup - `arXiv:1810.03562` - resolved: *The equivalence between two classic algorithms for the assignment problem* - status **exact**
- **[3]** - arXiv abstract-page lookup - `arXiv:2101.07155` - resolved: *Revisiting the Auction Algorithm for Weighted Bipartite Perfect Matchings* - status **exact**
- **[4]** - arXiv abstract-page lookup - `arXiv:2002.07407` - resolved: *Constrained Multiagent Rollout and Multidimensional Assignment with the Auction Algorithm* - status **exact**
- **[5]** - arXiv abstract-page lookup - `arXiv:2005.11792` - resolved: *Global Sensitivity Analysis for the Linear Assignment Problem* - status **exact**
- **[6]** - arXiv abstract-page lookup - `arXiv:2605.09382` - resolved: *Learning-Augmented Scalable Linear Assignment Problem Optimization via Neural Dual Warm-Starts* - status **exact**
- **[7]** - arXiv abstract-page lookup - `arXiv:2301.11201` - resolved: *Relative-Interior Solution for the (Incomplete) Linear Assignment Problem with Applications to the Quadratic Assignment Problem* - status **exact**
- **[8]** - arXiv abstract-page lookup - `arXiv:1403.7721` - resolved: *Maximum Quadratic Assignment Problem: Reduction from Maximum Label Cover and LP-based Approximation Algorithm* - status **exact**
- **[9]** - CrossRef DOI lookup - `doi:10.46254/au01.20220498` - resolved: *Assessment of Assignment Problem using Hungarian Method* - status **exact**
- **[10]** - CrossRef DOI lookup - `doi:10.1111/j.1540-6261.1961.tb02789.x` - resolved: *COUNTERSPECULATION, AUCTIONS, AND COMPETITIVE SEALED TENDERS* - status **exact**
- **[11]** - CrossRef DOI lookup - `doi:10.1017/cbo9780511528354.015` - resolved: *Competitive Market Institutions: Double Auctions vs. Sealed Bid-Offer Auctions* - status **exact**
- **[12]** - CrossRef DOI lookup - `doi:10.2139/ssrn.1120963` - resolved: *Optimal Auction Design Under Non-Commitment* - status **exact**
- **[13]** - CrossRef DOI lookup - `doi:10.2139/ssrn.5861082` - resolved: *Optimal Auction Design under Costly Learning* - status **exact**
- **[14]** - CrossRef DOI lookup - `doi:10.7249/r0874` - resolved: *The Assignment Game I: The Core* - status **exact**
- **[15]** - CrossRef DOI lookup - `doi:10.21236/ad0251958` - resolved: *COLLEGE ADMISSIONS AND THE STABILITY OF MARRIAGE* - status **exact**
- **[16]** - CrossRef DOI lookup - `doi:10.4337/9781781950005.00012` - resolved: *The market for 'lemons': quality uncertainty and the market mechanism* - status **exact**
- **[17]** - CrossRef DOI lookup - `doi:10.2307/1911865` - resolved: *A Theory of Auctions and Competitive Bidding* - status **exact**
- **[18]** - CrossRef DOI lookup - `doi:10.1007/s40505-022-00234-2` - resolved: *Revisiting the convergence theorem for competitive bidding in common value auctions* - status **exact**
- **[19]** - CrossRef DOI lookup - `doi:10.2139/ssrn.2753074` - resolved: *Efficient Mechanisms for Bilateral Trading with Moderately Informed Broker* - status **exact**
- **[20]** - CrossRef DOI lookup - `doi:10.1016/b978-0-934613-63-7.50039-5` - resolved: *The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver* - status **exact**
- **[21]** - arXiv abstract-page lookup - `arXiv:2507.14472` - resolved: *Strategyproofness and Monotone Allocation of Auction in Social Networks* - status **exact**
- **[22]** - arXiv abstract-page lookup - `arXiv:2401.01656` - resolved: *Deep Automated Mechanism Design for Integrating Ad Auction and Allocation in Feed* - status **exact**
- **[23]** - arXiv abstract-page lookup - `arXiv:2502.08369` - resolved: *Equitable Auction Design with Provable Regret Guarantees* - status **exact**
- **[24]** - arXiv abstract-page lookup - `arXiv:1903.00836` - resolved: *Revenue Maximization with Imprecise Distribution* - status **exact**
- **[25]** - arXiv abstract-page lookup - `arXiv:2508.02015` - resolved: *A Group Consensus-Driven Auction Algorithm for Cooperative Task Allocation Among Heterogeneous Multi-Agents* - status **exact**
- **[26]** - arXiv abstract-page lookup - `arXiv:2107.00144` - resolved: *Greedy Decentralized Auction-based Task Allocation for Multi-Agent Systems* - status **exact**
- **[27]** - arXiv abstract-page lookup - `arXiv:2304.01976` - resolved: *Reactive Multi-agent Coordination using Auction-based Task Allocation and Behavior Trees* - status **exact**
- **[28]** - arXiv abstract-page lookup - `arXiv:2404.02111` - resolved: *Risk-Aware Real-Time Task Allocation for Stochastic Multi-Agent Systems under STL Specifications* - status **exact**
- **[29]** - arXiv abstract-page lookup - `arXiv:2304.02333` - resolved: *Reactive Task Allocation for Balanced Servicing of Multiple Task Queues* - status **exact**
- **[30]** - arXiv abstract-page lookup - `arXiv:2605.21932` - resolved: *Auction-Consensus Algorithm with Learned Bidding Scheme for Multi-Robot Systems* - status **exact**
- **[31]** - arXiv abstract-page lookup - `arXiv:2606.24462` - resolved: *Varying Bundle Size Reactive Multi-Task Assignment using Selective Cost Estimation for Multi-Agent Systems* - status **exact**
- **[32]** - arXiv abstract-page lookup - `arXiv:1312.4259` - resolved: *Modification of Contract Net Protocol(CNP) : A Rule-Updation Approach* - status **exact**
- **[33]** - arXiv abstract-page lookup - `arXiv:2007.06172` - resolved: *Bottom-up mechanism and improved contract net protocol for the dynamic task planning of heterogeneous Earth observation resources* - status **exact**
- **[34]** - arXiv abstract-page lookup - `arXiv:2608.12371` - resolved: *Multi-Agent Scheduling with LLM-Assisted Contract Net Negotiation for Stream Processing in Mobile Edge Computing* - status **exact**
- **[35]** - arXiv abstract-page lookup - `arXiv:1902.09687` - resolved: *Market-Based Model in CR-WSN: A Q-Probabilistic Multi-agent Learning Approach* - status **exact**
- **[36]** - arXiv abstract-page lookup - `arXiv:2303.00506` - resolved: *Fast and Interpretable Dynamics for Fisher Markets via Block-Coordinate Updates* - status **exact**
- **[37]** - arXiv abstract-page lookup - `arXiv:2206.02344` - resolved: *Decentralized, Communication- and Coordination-free Learning in Structured Matching Markets* - status **exact**
- **[38]** - CrossRef DOI lookup - `doi:10.7249/p365` - resolved: *Behavioral Model of Rational Choice* - status **exact**
- **[39]** - CrossRef DOI lookup - `doi:10.3386/w19318` - resolved: *Behavioral Implications of Rational Inattention with Shannon Entropy* - status **exact**
- **[40]** - arXiv abstract-page lookup - `arXiv:1305.6037` - resolved: *Semi-bounded Rationality: A model for decision making* - status **exact**
- **[41]** - arXiv abstract-page lookup - `arXiv:1511.01710` - resolved: *Adaptive information-theoretic bounded rational decision-making with parametric priors* - status **exact**
- **[42]** - arXiv abstract-page lookup - `arXiv:1103.3687` - resolved: *Cost Based Satisficing Search Considered Harmful* - status **exact**
- **[43]** - arXiv abstract-page lookup - `arXiv:2104.14002` - resolved: *Modeling Managerial Search Behavior based on Simon's Concept of Satisficing* - status **exact**
- **[44]** - arXiv abstract-page lookup - `arXiv:2302.03220` - resolved: *The satisficing secretary problem: when closed-form solutions meet simulated annealing* - status **exact**
- **[45]** - arXiv abstract-page lookup - `arXiv:2502.14879` - resolved: *Limited attention and models of choice: A behavioral equivalence* - status **exact**
- **[46]** - arXiv abstract-page lookup - `arXiv:2508.05939` - resolved: *Rational Inattention to States and Choice Characteristics* - status **exact**
- **[47]** - arXiv abstract-page lookup - `arXiv:2306.09964` - resolved: *Robust Predictions in Games with Rational Inattention* - status **exact**
- **[48]** - arXiv abstract-page lookup - `arXiv:1701.02694` - resolved: *Limited individual attention and online virality of low-quality information* - status **exact**
- **[49]** - arXiv abstract-page lookup - `arXiv:1410.1668` - resolved: *Competing for Attention in Social Media under Information Overload Conditions* - status **exact**
- **[50]** - CrossRef DOI lookup - `doi:10.3389/fpsyg.2018.01133` - resolved: *Is Attention Really Effort? Revisiting Daniel Kahneman’s Influential 1973 Book Attention and Effort* - status **exact**
- **[51]** - CrossRef DOI lookup - `doi:10.7551/mitpress/5677.003.0005` - resolved: *Selective Attention* - status **exact**
- **[52]** - CrossRef DOI lookup - `doi:10.1109/sfcs.2000.892069` - resolved: *How bad is selfish routing?* - status **exact**
- **[53]** - arXiv abstract-page lookup - `arXiv:1010.4812` - resolved: *Polynomial Bottleneck Congestion Games with Optimal Price of Anarchy* - status **exact**
- **[54]** - arXiv abstract-page lookup - `arXiv:1412.0845` - resolved: *On the Robustness of the Approximate Price of Anarchy in Generalized Congestion Games* - status **exact**
- **[55]** - arXiv abstract-page lookup - `arXiv:2203.01740` - resolved: *Exact Price of Anarchy for Weighted Congestion Games with Two Players* - status **exact**
- **[56]** - arXiv abstract-page lookup - `arXiv:1308.4101` - resolved: *The Price of Anarchy is Unbounded for Congestion Games with Superpolynomial Latency Costs* - status **exact**
- **[57]** - arXiv abstract-page lookup - `arXiv:1112.3680` - resolved: *The Robust Price of Anarchy of Altruistic Games* - status **exact**
- **[58]** - arXiv abstract-page lookup - `arXiv:2107.06331` - resolved: *The Unintended Consequences of Minimizing the Price of Anarchy in Congestion Games* - status **exact**
- **[59]** - arXiv abstract-page lookup - `arXiv:2005.05191` - resolved: *The Value of Information in Selfish Routing* - status **exact**
- **[60]** - arXiv abstract-page lookup - `arXiv:1707.00208` - resolved: *Reconciling Selfish Routing with Social Good* - status **exact**
- **[61]** - arXiv abstract-page lookup - `arXiv:1202.2877` - resolved: *Improving the Price of Anarchy for Selfish Routing via Coordination Mechanisms* - status **exact**
- **[62]** - arXiv abstract-page lookup - `arXiv:2012.04327` - resolved: *Settling the complexity of Nash equilibrium in congestion games* - status **exact**
- **[63]** - arXiv abstract-page lookup - `arXiv:2209.07580` - resolved: *Exploring the Tradeoff between Competitive Ratio and Variance in Online-Matching Markets* - status **exact**
- **[64]** - arXiv abstract-page lookup - `arXiv:2508.08658` - resolved: *Byzantine-Resilient Decentralized Online Resource Allocation* - status **exact**
- **[65]** - arXiv abstract-page lookup - `arXiv:2402.11425` - resolved: *Online Resource Allocation with Average Budget Constraints* - status **exact**
- **[66]** - arXiv abstract-page lookup - `arXiv:2401.16945` - resolved: *Online Resource Allocation with Non-Stationary Customers* - status **exact**
- **[67]** - arXiv abstract-page lookup - `arXiv:2302.04182` - resolved: *Online Resource Allocation: Bandits feedback and Advice on Time-varying Demands* - status **exact**
- **[68]** - arXiv abstract-page lookup - `arXiv:2505.05169` - resolved: *Bandit Max-Min Fair Allocation* - status **exact**
- **[69]** - arXiv abstract-page lookup - `arXiv:2410.05856` - resolved: *Stochastic Bandits for Egalitarian Assignment* - status **exact**
- **[70]** - arXiv abstract-page lookup - `arXiv:1507.08025` - resolved: *Multi-armed Bandit Models for the Optimal Design of Clinical Trials: Benefits and Challenges* - status **exact**
- **[71]** - arXiv abstract-page lookup - `arXiv:2602.16183` - resolved: *Multi-Agent Combinatorial-Multi-Armed-Bandit framework for the Submodular Welfare Problem under Bandit Feedback* - status **exact**
- **[72]** - arXiv abstract-page lookup - `arXiv:2403.15669` - resolved: *Review of Large-Scale Simulation Optimization* - status **exact**
- **[73]** - arXiv abstract-page lookup - `arXiv:2511.00685` - resolved: *SOCRATES: Simulation Optimization with Correlated Replicas and Adaptive Trajectory Evaluations* - status **exact**
- **[74]** - arXiv abstract-page lookup - `arXiv:1302.1611` - resolved: *Bounded regret in stochastic multi-armed bandits* - status **exact**
- **[75]** - arXiv abstract-page lookup - `arXiv:1204.5721` - resolved: *Regret Analysis of Stochastic and Nonstochastic Multi-armed Bandit Problems* - status **exact**
- **[76]** - arXiv abstract-page lookup - `arXiv:2408.05214` - resolved: *A new Simheuristics procedure for stochastic combinatorial optimization* - status **exact**
- **[77]** - arXiv abstract-page lookup - `arXiv:0809.0460` - resolved: *Stochastic Combinatorial Optimization under Probabilistic Constraints* - status **exact**
- **[78]** - arXiv abstract-page lookup - `arXiv:2409.00075` - resolved: *A survey on combinatorial optimization* - status **exact**
- **[79]** - arXiv abstract-page lookup - `arXiv:2505.04757` - resolved: *Primal-dual algorithm for contextual stochastic combinatorial optimization* - status **exact**
- **[80]** - arXiv abstract-page lookup - `arXiv:2010.05127` - resolved: *Approximation Algorithms for Stochastic Minimum Norm Combinatorial Optimization* - status **exact**
- **[81]** - arXiv abstract-page lookup - `arXiv:2509.16451` - resolved: *Overfitting in Adaptive Robust Optimization* - status **exact**
- **[82]** - arXiv abstract-page lookup - `arXiv:2106.12858` - resolved: *Adaptive Relaxations for Multistage Robust Optimization* - status **exact**
- **[83]** - arXiv abstract-page lookup - `arXiv:2602.16465` - resolved: *The Complexity Landscape of Two-Stage Robust Selection Problems with Budgeted Uncertainty* - status **exact**
- **[84]** - arXiv abstract-page lookup - `arXiv:2403.18494` - resolved: *Learning in PINNs: Phase transition, diffusion equilibrium, and generalization* - status **exact**
- **[85]** - arXiv abstract-page lookup - `arXiv:0808.3230` - resolved: *Phase Transitions on Fixed Connected Graphs and Random Graphs in the Presence of Noise* - status **exact**
- **[86]** - arXiv abstract-page lookup - `arXiv:1111.6822` - resolved: *Optimal Phase Transitions in Compressed Sensing* - status **exact**
- **[87]** - arXiv abstract-page lookup - `arXiv:1610.00653` - resolved: *Phase transitions in distributed control systems with multiplicative noise* - status **exact**
- **[88]** - arXiv abstract-page lookup - `arXiv:2403.03695` - resolved: *Spectral Phase Transition and Optimal PCA in Block-Structured Spiked models* - status **exact**
- **[89]** - arXiv abstract-page lookup - `arXiv:0801.1877` - resolved: *Resource allocation pattern in infrastructure networks* - status **exact**
- **[90]** - arXiv abstract-page lookup - `arXiv:2008.07871` - resolved: *Fast Agent-Based Simulation Framework with Applications to Reinforcement Learning and the Study of Trading Latency Effects* - status **exact**
- **[91]** - arXiv abstract-page lookup - `arXiv:2010.08992` - resolved: *Analysis of the impact of maker-taker fees on the stock market using agent-based simulation* - status **exact**
- **[92]** - arXiv abstract-page lookup - `arXiv:2409.16589` - resolved: *The Impact of Designated Market Makers on Market Liquidity and Competition: A Simulation Approach* - status **exact**
- **[93]** - arXiv abstract-page lookup - `arXiv:2502.11822` - resolved: *Assessing the impacts of tradable credit schemes through agent-based simulation* - status **exact**
- **[94]** - arXiv abstract-page lookup - `arXiv:2507.20985` - resolved: *Behavioral Study of Dashboard Mechanisms* - status **exact**
- **[95]** - arXiv abstract-page lookup - `arXiv:1708.01401` - resolved: *Spot Pricing in the Cloud Ecosystem: A Comparative Investigation* - status **exact**
- **[96]** - CrossRef DOI lookup - `doi:10.1145/2517349.2522716` - resolved: *Sparrow* - status **exact**
- **[97]** - CrossRef DOI lookup - `doi:10.1145/2741948.2741964` - resolved: *Large-scale cluster management at Google with Borg* - status **exact**
- **[98]** - CrossRef DOI lookup - `doi:10.1145/2523616.2523633` - resolved: *Apache Hadoop YARN* - status **exact**
- **[99]** - CrossRef DOI lookup - `doi:10.1109/hpcc.2008.172` - resolved: *Market-Oriented Cloud Computing: Vision, Hype, and Reality for Delivering IT Services as Computing Utilities* - status **exact**
- **[100]** - arXiv abstract-page lookup - `arXiv:1304.6176` - resolved: *An Auction Mechanism for Resource Allocation in Mobile Cloud Computing Systems* - status **exact**
- **[101]** - arXiv abstract-page lookup - `arXiv:1611.07619` - resolved: *A Truthful $(1-\epsilon)$-Optimal Mechanism for On-demand Cloud Resource Provisioning* - status **exact**
- **[102]** - arXiv abstract-page lookup - `arXiv:2511.12879` - resolved: *Resilient and Efficient Allocation for Large-Scale Autonomous Fleets via Decentralized Coordination* - status **exact**
- **[103]** - arXiv abstract-page lookup - `arXiv:2509.07497` - resolved: *DREAMS: Decentralized Resource Allocation and Service Management across the Compute Continuum Using Service Affinity* - status **exact**
- **[104]** - arXiv abstract-page lookup - `arXiv:2507.09083` - resolved: *Learning from Synthetic Labs: Language Models as Auction Participants* - status **exact**
- **[105]** - arXiv abstract-page lookup - `arXiv:2608.23867` - resolved: *Markets, Not Planners: Decentralized Orchestration of LLM Agents with Private Information* - status **exact**
- **[106]** - arXiv abstract-page lookup - `arXiv:2609.04667` - resolved: *ERPBench: Evaluating LLM Agents for Enterprise Decision-Making Across Competitive Market Ecologies* - status **exact**
- **[107]** - arXiv abstract-page lookup - `arXiv:2603.08853` - resolved: *LLM-Agent Interactions on Markets with Information Asymmetries* - status **exact**
- **[108]** - arXiv abstract-page lookup - `arXiv:2605.10059` - resolved: *Strategic Exploitation in LLM Agent Markets: A Simulation Framework for E-Commerce Trust* - status **exact**
- **[109]** - arXiv abstract-page lookup - `arXiv:2604.17774` - resolved: *Prompt Optimization Enables Stable Algorithmic Collusion in LLM Agents* - status **exact**
- **[110]** - arXiv abstract-page lookup - `arXiv:2509.10147` - resolved: *Virtual Agent Economies* - status **exact**
- **[111]** - arXiv abstract-page lookup - `arXiv:2505.15799` - resolved: *The Agentic Economy* - status **exact**
- **[112]** - arXiv abstract-page lookup - `arXiv:2604.18602` - resolved: *Machine Spirits: Speculation and Adaptation of LLM Agents in Asset Markets* - status **exact**
- **[113]** - arXiv abstract-page lookup - `arXiv:2609.02580` - resolved: *Competitive Market Behavior of LLMs* - status **exact**
- **[114]** - arXiv abstract-page lookup - `arXiv:2607.09702` - resolved: *Fundamental market design as a layer of AI-agent alignment* - status **exact**
- **[115]** - arXiv abstract-page lookup - `arXiv:2601.08815` - resolved: *Agent Contracts: A Formal Framework for Resource-Bounded Autonomous AI Systems* - status **exact**
- **[116]** - arXiv abstract-page lookup - `arXiv:2508.10146` - resolved: *Agentic AI Frameworks: Architectures, Protocols, and Design Challenges* - status **exact**
- **[117]** - arXiv abstract-page lookup - `arXiv:2602.03128` - resolved: *Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis* - status **exact**
- **[118]** - arXiv abstract-page lookup - `arXiv:2608.25992` - resolved: *ProgRouter: Online Progress-Guided Orchestration for Multi-Agent LLM Workflows under Quality-Cost Tradeoffs* - status **exact**
- **[119]** - arXiv abstract-page lookup - `arXiv:2605.02801` - resolved: *Reinforcement Learning for LLM-based Multi-Agent Systems through Orchestration Traces* - status **exact**
- **[120]** - arXiv abstract-page lookup - `arXiv:2511.17621` - resolved: *From Competition to Coordination: Market Making as a Scalable Framework for Safe and Aligned Multi-Agent LLM Systems* - status **exact**
- **[121]** - arXiv abstract-page lookup - `arXiv:2504.00587` - resolved: *AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems* - status **exact**
- **[122]** - arXiv abstract-page lookup - `arXiv:2605.03310` - resolved: *Coordination as an Architectural Layer for LLM-Based Multi-Agent Systems* - status **exact**
- **[123]** - arXiv abstract-page lookup - `arXiv:2310.10826` - resolved: *Mechanism Design for Large Language Models* - status **exact**
- **[124]** - arXiv abstract-page lookup - `arXiv:2403.12031` - resolved: *RouterBench: A Benchmark for Multi-LLM Routing System* - status **exact**
- **[125]** - arXiv abstract-page lookup - `arXiv:2207.10342` - resolved: *Language Model Cascades* - status **exact**
