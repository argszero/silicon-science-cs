# Reference verification -- issue #155

Every placed reference re-fetched **by DOI** from Crossref (`api.crossref.org/works/<doi>`), independently of the query pass that harvested it. Title agreement is token-set Jaccard against the stored title; the pass threshold is 0.80. A DOI that resolves to a different work, or does not resolve at all, is fatal.

| verdict | entries |
|---|---|
| VERIFIED | 100 |
| VERIFIED-EDITION | 7 |
| **total** | **107** |

## Entry-by-entry

| # | key | section | verdict | agreement | DOI | Crossref title |
|---|---|---|---|---|---|---|
| 1 | `evenitai1971` | 1 Prior art | VERIFIED | 1.00 | `10.1016/b978-0-12-417750-5.50011-7` | QUEUES, STACKS AND GRAPHS |
| 2 | `pratt1973` | 1 Prior art | VERIFIED | 1.00 | `10.1145/800125.804058` | Computing permutations with double-ended queues, parallel stacks and parallel queues |
| 3 | `tarjan1972` | 1 Prior art | VERIFIED | 1.00 | `10.1145/321694.321704` | Sorting Using Networks of Queues and Stacks |
| 4 | `acceltor2025` | 2 Background | VERIFIED | 1.00 | `10.1109/ton.2025.3550902` | AccelToR: Accelerating TCP for Circuit/Packet Hybrid Data Centers With Packet Scheduling |
| 5 | `anomaly2026` | 2 Background | VERIFIED | 1.00 | `10.1109/ojcoms.2026.3686225` | ALADA: Packet-Level Analysis for Line Rate Anomaly Detection Using a Programmable Dataplan |
| 6 | `cipo2024` | 2 Background | VERIFIED | 1.00 | `10.1016/j.comnet.2024.110355` | CIPO: Efficient, lightweight and programmable packet scheduling |
| 7 | `ctpifo2025` | 2 Background | VERIFIED | 1.00 | `10.1109/icccn65249.2025.11134021` | CT-PIFO: A Congruity Tree Based Packet Scheduler to Improve Flow Completion Time |
| 8 | `ddspq2025` | 2 Background | VERIFIED | 1.00 | `10.1109/icccs65393.2025.11069454` | DDSPQ: Strict-Priority Queue Schedule for Multi-Tiered Service Accommodation in SD-WAN |
| 9 | `dpdk2021` | 2 Background | VERIFIED | 1.00 | `10.3390/fi13030078` | An Adaptive Throughput-First Packet Scheduling Algorithm for DPDK-Based Packet Processing  |
| 10 | `dpifo2024` | 2 Background | VERIFIED | 1.00 | `10.1109/cscwd61410.2024.10580504` | D-PIFO: A Dynamic Priority Scheduling Algorithm for Performance-Critical Packets Based on  |
| 11 | `drpifo2024` | 2 Background | VERIFIED | 1.00 | `10.1109/tnsm.2023.3304894` | DR-PIFO: A Dynamic Ranking Packet Scheduler Using a Push-In-First-Out Queue |
| 12 | `exppifo2025` | 2 Background | VERIFIED | 1.00 | `10.1145/3749217` | Exp-PIFO: Scalable and Efficient Programmable Packet Scheduling |
| 13 | `fifo2024` | 2 Background | VERIFIED | 1.00 | `10.1049/iet-com.2010.0378` | Enhanced first-in-first-out-based round-robin multicast scheduling algorithm for input-que |
| 14 | `fipo2025` | 2 Background | VERIFIED | 1.00 | `10.1109/jsyst.2025.3567017` | FIPO: A Lightweight and Customized Software-Defined Programmable Packet Scheduling Primiti |
| 15 | `hwrank2023` | 2 Background | VERIFIED | 1.00 | `10.1109/access.2023.3286726` | A Hardware Architecture of a Dynamic Ranking Packet Scheduler for Programmable Network Dev |
| 16 | `lark2025` | 2 Background | VERIFIED | 1.00 | `10.1109/infocom55648.2025.11044448` | Lark: A Buffer-aware Building Block for Programmable Packet Scheduling in Datacenters |
| 17 | `nearsched2024` | 2 Background | VERIFIED | 1.00 | `10.1145/3673660.3655069` | Near-Optimal Packet Scheduling in Multihop Networks with End-to-End Deadline Constraints |
| 18 | `p4sched2021` | 2 Background | VERIFIED | 1.00 | `10.1109/icccn52240.2021.9522193` | A P4-Based Packet Scheduling Approach for Clustered Deep Packet Inspection Appliances |
| 19 | `p4survey2023` | 2 Background | VERIFIED | 1.00 | `10.1109/comst.2022.3217613` | AI-Driven Packet Forwarding With Programmable Data Plane: A Survey |
| 20 | `pifo2016` | 2 Background | VERIFIED | 1.00 | `10.1145/2934872.2934899` | Programmable Packet Scheduling at Line Rate |
| 21 | `qosdp2024` | 2 Background | VERIFIED | 1.00 | `10.1109/tmlcn.2024.3475968` | An Intelligent and Programmable Data Plane for QoS-Aware Packet Processing |
| 22 | `ratesched2024` | 2 Background | VERIFIED | 1.00 | `10.1109/iccect60629.2024.10545661` | A Programmable Packet Scheduling Method Based on Traffic Rate |
| 23 | `scaleuppifo2026` | 2 Background | VERIFIED | 1.00 | `10.1145/3789240.3829190` | Scale-up PIFO: Interleaving Multiple Priority Queues for High Speed Programmable Schedulin |
| 24 | `schedfpga2025` | 2 Background | VERIFIED | 1.00 | `10.1109/6gnet68413.2025.11314135` | Demo: Programmable Packet Scheduling on FPGA-Based Switches |
| 25 | `smartnic2023` | 2 Background | VERIFIED | 1.00 | `10.1145/3603269.3604882` | Unleashing SmartNIC Packet Processing Performance in P4 |
| 26 | `sppifo2022` | 2 Background | VERIFIED | 1.00 | `10.1109/infocomwkshps54753.2022.9798055` | Programmable Packet Scheduling With SP-PIFO: Theory, Algorithms and Evaluation |
| 27 | `spring2025` | 2 Background | VERIFIED | 1.00 | `10.36244/icj.2025.3.1` | Spring: Theory and an Efficient Heuristic for Programmable Packet Scheduling with SP-PIFO |
| 28 | `timeaware2025` | 2 Background | VERIFIED | 1.00 | `10.1109/isorc65339.2025.00038` | Time-Aware Packet Forwarding in Programmable Data Planes |
| 29 | `tsfifo2023` | 2 Background | VERIFIED | 1.00 | `10.1186/s13677-023-00518-3` | Making programmable packet scheduling time-sensitive with a FIFO queue |
| 30 | `vpifo2024` | 2 Background | VERIFIED | 1.00 | `10.1145/3651890.3672270` | vPIFO: Virtualized Packet Scheduler for Programmable Hierarchical Scheduling in High-Speed |
| 31 | `bvn2024` | 3 The device model | VERIFIED | 1.00 | `10.23919/eusipco63174.2024.10715087` | Orthogonal Matching Pursuit-Based Algorithms for the Birkhoff-Von Neumann Decomposition |
| 32 | `cbllfq2020` | 3 The device model | VERIFIED | 1.00 | `10.3837/tiis.2020.02.001` | Implementation of Class-Based Low Latency Fair Queueing (CBLLFQ) Packet Scheduling Algorit |
| 33 | `ciocq2026` | 3 The device model | VERIFIED | 1.00 | `10.1109/ojcoms.2026.3726416` | Delay Impact of Bursty Cross Traffic in Combined Input and Output Queued Switches Using Vi |
| 34 | `clos2007` | 3 The device model | VERIFIED | 1.00 | `10.1109/lcomm.2007.061617` | Module Matching Schemes for Input-Queued Clos-Network Packet Switches |
| 35 | `cqswitch2013` | 3 The device model | VERIFIED | 1.00 | `10.1109/telfor.2013.6716184` | Dynamic weighted round robin in crosspoint queued switch |
| 36 | `drr2012` | 3 The device model | VERIFIED | 1.00 | `10.1109/iccnc.2012.6167459` | Cycle time distribution and control for the Deficit Round Robin packet scheduler |
| 37 | `drr2025` | 3 The device model | VERIFIED | 1.00 | `10.23919/wiopt66569.2025.11123403` | Convexity and Optimization in Deficit Round Robin Scheduling for Delay-Constrained Systems |
| 38 | `hdmrr2019` | 3 The device model | VERIFIED | 1.00 | `10.1109/icis46139.2019.8940224` | Half-Draining Round Robin Matching for High Performance Input Queued Switches |
| 39 | `lqf2010` | 3 The device model | VERIFIED | 1.00 | `10.1109/isita.2010.5648873` | Longest queue first in round-robin matching for input-queued switches |
| 40 | `maxweight2020` | 3 The device model | VERIFIED | 1.00 | `10.1016/j.peva.2020.102143` | Heavy traffic analysis of approximate max-weight matching algorithms for input-queued swit |
| 41 | `multicast2017` | 3 The device model | VERIFIED | 1.00 | `10.1109/ccece.2017.7946605` | Iterative multicast scheduling algorithm for input-queued switch with variable packet size |
| 42 | `mwm2012` | 3 The device model | VERIFIED | 1.00 | `10.1287/12-ssy061` | Diffusion Approximation for an Input-queued Switch Operating under a Maximum Weight Matchi |
| 43 | `nocqos2012` | 3 The device model | VERIFIED | 1.00 | `10.1109/ispa.2012.93` | A Scalable NoC Router Design Providing QoS Support Using Weighted Round Robin Scheduling |
| 44 | `oqsq2009` | 3 The device model | VERIFIED | 1.00 | `10.1109/tnet.2009.2014948` | On Tracking the Behavior of an Output-Queued Switch Using an Input-Queued Switch |
| 45 | `owfq2023` | 3 The device model | VERIFIED | 1.00 | `10.1109/iccc59590.2023.10507624` | OWFQ: Reducing Packet Drops for Approximate Weighted Fair Queueing with Calendar Queues |
| 46 | `pim2009` | 3 The device model | VERIFIED | 1.00 | `10.1109/apcc.2009.5375476` | Performance analysis on dynamics of parallel iterative matching in an input-buffered switc |
| 47 | `priowfq2020` | 3 The device model | VERIFIED | 1.00 | `10.11591/ijeecs.v19.i1.pp241-247` | Improving network performance with an integrated priority queue and weighted fair queue sc |
| 48 | `qpsr2021` | 3 The device model | VERIFIED | 1.00 | `10.1016/j.peva.2021.102197` | QPS-r: A cost-effective iterative switching algorithm for input-queued switches |
| 49 | `rr2014` | 3 The device model | VERIFIED | 1.00 | `10.19026/rjaset.7.498` | Packet Scheduling in High-speed Networks Using Improved Weighted Round Robin |
| 50 | `rrbuffer2010` | 3 The device model | VERIFIED | 1.00 | `10.1109/glocom.2010.5683309` | Designing Packet Buffers Using Random Round Robin |
| 51 | `strprio2016` | 3 The device model | VERIFIED | 1.00 | `10.1109/iccci.2016.7480023` | An improvement mechanism for low priority traffic TCP performance in Strict Priority Queue |
| 52 | `voq2019` | 3 The device model | VERIFIED | 1.00 | `10.1049/iet-net.2018.5115` | Randomised scheduling algorithm for virtual output queuing switch at the presence of non‐u |
| 53 | `wfq2010` | 3 The device model | VERIFIED | 1.00 | `10.1016/j.peva.2010.05.004` | Approximation for a two-class weighted fair queueing discipline |
| 54 | `wfq2012` | 3 The device model | VERIFIED | 1.00 | `10.1145/2377677.2377679` | Multi-resource fair queueing for packet processing |
| 55 | `chaindecomp2022` | 4 Combinatorics | VERIFIED-EDITION | 1.00 | `10.1007/s12469-022-00304-5` | Optimal balanced chain decomposition of partially ordered sets with applications to operat |
| 56 | `continfrac2018` | 4 Combinatorics | VERIFIED | 1.00 | `10.23638/dmtcs-19-2-11` | Continued fractions for permutation statistics |
| 57 | `descents2025` | 4 Combinatorics | VERIFIED | 1.00 | `10.1016/j.spl.2024.110320` | Moderate deviations for the number of descents in a random permutation |
| 58 | `desclargedev2024` | 4 Combinatorics | VERIFIED | 1.00 | `10.1017/jpr.2023.86` | Sharp large deviations and concentration inequalities for the number of descents in a rand |
| 59 | `descsharp2025` | 4 Combinatorics | VERIFIED | 1.00 | `10.1214/24-aap2138` | Sharp analysis on the joint distribution of the number of descents and inverse descents in |
| 60 | `dilworth2009` | 4 Combinatorics | VERIFIED | 1.00 | `10.1007/978-0-8176-4842-8_10` | A Decomposition Theorem for Partially Ordered Sets |
| 61 | `dilworthgen2024` | 4 Combinatorics | VERIFIED | 1.00 | `10.4314/aujst.v5i1.6` | A Generalization of Dilworth’s Decomposition Theorem for Partially Ordered Multisets |
| 62 | `dynamiclis2021` | 4 Combinatorics | VERIFIED | 1.00 | `10.1145/3406325.3451026` | Improved dynamic algorithms for longest increasing subsequence |
| 63 | `ehrt2019` | 4 Combinatorics | VERIFIED | 1.00 | `10.3390/a12110237` | What Do a Longest Increasing Subsequence and a Longest Decreasing Subsequence Know about E |
| 64 | `incr2020` | 4 Combinatorics | VERIFIED | 1.00 | `10.37236/9506` | Pattern Avoiding Permutations with a Unique Longest Increasing Subsequence |
| 65 | `lislds2019` | 4 Combinatorics | VERIFIED | 1.00 | `10.3390/a12110237` | What Do a Longest Increasing Subsequence and a Longest Decreasing Subsequence Know about E |
| 66 | `lisrevisited2026` | 4 Combinatorics | VERIFIED | 1.00 | `10.1088/1572-9494/ae9b87` | The longest increasing subsequence problem revisited |
| 67 | `mallows2022` | 4 Combinatorics | VERIFIED | 1.00 | `10.1214/21-aihp1167` | A central limit theorem for descents of a Mallows permutation and its inverse |
| 68 | `parallellis2023` | 4 Combinatorics | VERIFIED | 1.00 | `10.1145/3558481.3591078` | Nearly Optimal Parallel Algorithms for Longest Increasing Subsequence |
| 69 | `patience2018` | 4 Combinatorics | VERIFIED | 1.00 | `10.1090/bull/1623` | Commentary on “Longest increasing subsequences: from patience sorting to the Baik–Deift–Jo |
| 70 | `posetramsey2024` | 4 Combinatorics | VERIFIED | 1.00 | `10.1007/s11083-024-09663-z` | Poset Ramsey Number $$R(P,Q_n)$$. II. N-Shaped Poset |
| 71 | `rsk2019` | 4 Combinatorics | VERIFIED | 1.00 | `10.1090/stml/091/08` | The Robinson–Schensted–Knuth correspondence |
| 72 | `rsk2024` | 4 Combinatorics | VERIFIED-EDITION | 1.00 | `10.1007/s00026-024-00708-z` | A Bump Statistic on Permutations Resulting from the Robinson–Schensted Correspondence |
| 73 | `rskpoisson2023` | 4 Combinatorics | VERIFIED | 1.00 | `10.1016/j.aam.2022.102478` | Poisson limit theorems for the Robinson–Schensted correspondence and for the multi-line Ha |
| 74 | `sortnetstack2008` | 4 Combinatorics | VERIFIED | 1.00 | `10.1007/978-3-540-87744-8_35` | The Complexity of Sorting with Networks of Stacks and Queues |
| 75 | `spacelis2019` | 4 Combinatorics | VERIFIED-EDITION | 1.00 | `10.1007/s00224-018-09908-6` | Space-Efficient Algorithms for Longest Increasing Subsequence |
| 76 | `stacksort2026` | 4 Combinatorics | VERIFIED | 1.00 | `10.1016/j.disc.2025.114834` | Stack-sorting with stacks avoiding vincular patterns |
| 77 | `sublinear2021` | 4 Combinatorics | VERIFIED | 1.00 | `10.1137/1.9781611976465.115` | Improved Sublinear Time Algorithm for Longest Increasing Subsequence |
| 78 | `widthentropy2015` | 4 Combinatorics | VERIFIED-EDITION | 1.00 | `10.1007/s11083-015-9346-z` | Poset Entropy Versus Number of Linear Extensions: The Width-2 Case |
| 79 | `competcloud2024` | 5 Online algorithms | VERIFIED | 1.00 | `10.3390/a17060237` | Competitive Analysis of Algorithms for an Online Distribution Problem |
| 80 | `lookaheadcorr2021` | 5 Online algorithms | VERIFIED-EDITION | 1.00 | `10.1007/s10288-021-00479-w` | Correction to: Exact distributional analysis of online algorithms with lookahead |
| 81 | `lookaheadexact2020` | 5 Online algorithms | VERIFIED-EDITION | 1.00 | `10.1007/s10288-020-00442-1` | Exact distributional analysis of online algorithms with lookahead |
| 82 | `machinemin2020` | 5 Online algorithms | VERIFIED-EDITION | 1.00 | `10.1007/s10878-020-00633-w` | Online machine minimization with lookahead |
| 83 | `metmatch2021` | 5 Online algorithms | VERIFIED | 1.00 | `10.1142/s1793830921501561` | Competitive analysis for two variants of online metric matching problem |
| 84 | `onlineinterval2019` | 5 Online algorithms | VERIFIED | 1.00 | `10.1007/s10878-019-00381-6` | Online interval scheduling on two related machines: the power of lookahead |
| 85 | `onpktlookahead2019` | 5 Online algorithms | VERIFIED | 1.00 | `10.1016/j.tcs.2019.01.013` | Online packet scheduling with bounded delay and lookahead |
| 86 | `permpred2025` | 5 Online algorithms | VERIFIED | 1.00 | `10.1145/3711872` | Permutation Predictions for Non-Clairvoyant Scheduling |
| 87 | `semiuniform2024` | 5 Online algorithms | VERIFIED | 1.00 | `10.1051/ro/2024042` | Semi-online scheduling on two uniform parallel machines with initial lookahead |
| 88 | `unitbatch2019` | 5 Online algorithms | VERIFIED | 1.00 | `10.1142/s0217595919500246` | Online Algorithms for Scheduling Unit Length Jobs on Unbounded Parallel-Batch Machines wit |
| 89 | `antq2023` | 6 Data structures | VERIFIED | 1.00 | `10.1109/dsd60849.2023.00070` | AnTiQ: A Hardware-Accelerated Priority Queue Design with Constant Time Arbitrary Element R |
| 90 | `binaryheaps2025` | 6 Data structures | VERIFIED | 1.00 | `10.1145/3731333.3731359` | Binary Heaps and Priority Queues |
| 91 | `binomialheaps2000` | 6 Data structures | VERIFIED | 1.00 | `10.1016/s0167-8191(00)00064-8` | Parallel priority queues based on binomial heaps |
| 92 | `deap1987` | 6 Data structures | VERIFIED | 1.00 | `10.1016/0020-0190(87)90033-0` | The deap—a double-ended heap to implement double-ended priority queues |
| 93 | `decreasingkeys2024` | 6 Data structures | VERIFIED | 1.00 | `10.1016/j.tcs.2024.114563` | Priority queues with decreasing keys |
| 94 | `delaunay1993` | 6 Data structures | VERIFIED | 1.00 | `10.1007/bf01179371` | The relaxed min-max heap |
| 95 | `fastpq2024` | 6 Data structures | VERIFIED | 1.00 | `10.1109/ipdpsw63119.2024.00038` | A Fast Scalable Hardware Priority Queue and Optimizations for Multi-Pushes |
| 96 | `jheaps2021` | 6 Data structures | VERIFIED | 1.00 | `10.1016/j.softx.2021.100869` | JHeaps: An open-source library of priority queues |
| 97 | `minmax1999` | 6 Data structures | VERIFIED | 1.00 | `10.1016/s0020-0190(99)00014-9` | Symmetric Min-Max heap: A simpler data structure for double-ended priority queue |
| 98 | `pipelinedheap2007` | 6 Data structures | VERIFIED | 1.00 | `10.1109/tnet.2007.892882` | Pipelined Heap (Priority Queue) Management for Advanced Scheduling in High-Speed Networks |
| 99 | `qpidsr2026` | 6 Data structures | VERIFIED | 1.00 | `10.1145/3816782.3819208` | Brief Announcement: QPID: A Scalable, Strict Concurrent Priority Queue |
| 100 | `randpq1998` | 6 Data structures | VERIFIED | 1.00 | `10.1006/jpdc.1998.1429` | Randomized Priority Queues for Fast Parallel Access |
| 101 | `fct2025` | 7 Measurement | VERIFIED | 1.00 | `10.1109/icccn65249.2025.11134021` | CT-PIFO: A Congruity Tree Based Packet Scheduler to Improve Flow Completion Time |
| 102 | `frag2026` | 7 Measurement | VERIFIED | 1.00 | `10.1109/icc59461.2026.11587563` | Offloading IP Packet Fragmentation from CPU to SmartNIC Using P4 |
| 103 | `noc2024` | 7 Measurement | VERIFIED | 1.00 | `10.1002/ett.5043` | <scp>RETRACTION</scp>
                    : Design and Implementation of Network‐on‐chip R |
| 104 | `smartnicallreduce2024` | 7 Measurement | VERIFIED | 1.00 | `10.1109/ispa63168.2024.00030` | Leveraging SmartNIC for Ring AllReduce Offloading |
| 105 | `tail2025` | 7 Measurement | VERIFIED | 1.00 | `10.1109/infocom55648.2025.11044448` | Lark: A Buffer-aware Building Block for Programmable Packet Scheduling in Datacenters |
| 106 | `trimmer2022` | 7 Measurement | VERIFIED | 1.00 | `10.1109/iscas48785.2022.9937607` | A Templated VHDL Architecture for Terabit/s P4-programmable FPGA-based Packet Parsing |
| 107 | `xdp2023` | 7 Measurement | VERIFIED | 1.00 | `10.1109/icpads56603.2022.00103` | OXDP: Offloading XDP to SmartNIC for Accelerating Packet Processing |

## Edition notes

These DOIs resolve to the right work but Crossref gives a different year than the one stored at placement. The bibliography uses the Crossref year; a reprint or a later indexing year is not an error, but it must be stated rather than smoothed over.

- `chaindecomp2022` -- placed as 2022, Crossref says 2023: Optimal balanced chain decomposition of partially ordered sets with applications to operating cost minimization in aircraft routing problems
- `rsk2024` -- placed as 2024, Crossref says 2025: A Bump Statistic on Permutations Resulting from the Robinson–Schensted Correspondence
- `spacelis2019` -- placed as 2019, Crossref says 2020: Space-Efficient Algorithms for Longest Increasing Subsequence
- `widthentropy2015` -- placed as 2015, Crossref says 2016: Poset Entropy Versus Number of Linear Extensions: The Width-2 Case
- `lookaheadcorr2021` -- placed as 2021, Crossref says 2022: Correction to: Exact distributional analysis of online algorithms with lookahead
- `lookaheadexact2020` -- placed as 2020, Crossref says 2021: Exact distributional analysis of online algorithms with lookahead
- `machinemin2020` -- placed as 2020, Crossref says 2022: Online machine minimization with lookahead

