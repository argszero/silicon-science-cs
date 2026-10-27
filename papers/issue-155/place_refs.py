#!/usr/bin/env python3
"""Issue #155 -- hand-authored placement: which reference supports which claim.

A reference pool decides nothing; PLACEMENT decides it. The rule this file
enforces is the one that cost #149 a rewrite: a record may enter the bibliography
only if it can name *the section it sits in and the sentence it supports*, and
the entry is pruned with a counted reason if it cannot.

Honesty constraint on the claims below: they are written from the works' TITLES
alone. No abstract or full text was read for any of them in this round, so every
claim is of the form "names the construct X", "reports Y", "gives an algorithm
for Z" -- statements a title supports. A claim of the form "shows that X causes
Y" would not be supported by a title and is not made anywhere in this file.
Where a claim asserts a RELATION to this paper ("the closest prior statement to
this paper's question"), that relation is my own reading, not an attribution to
the work's content.

The resolver requires each named title to match exactly one harvested candidate;
ambiguity or absence is an error, never a guess.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "candidates.json")
SEEDS = os.path.join(HERE, "seeds.json")
OUT = os.path.join(HERE, "placement.json")

# (key, title substring, section, the sentence this entry supports)
PLACEMENT = [
    # ---------------- 2. Background: the programmable scheduling problem ------
    ("scaleuppifo2026", "Scale-up PIFO", "2 Background",
     "interleaves multiple priority queues for programmable scheduling, the line this paper measures"),
    ("sppifo2022", "Programmable Packet Scheduling With SP-PIFO", "2 Background",
     "gives SP-PIFO its theory and evaluation, and names the optimal queue mapping it approximates"),
    ("exppifo2025", "Exp-PIFO", "2 Background",
     "proposes a scalable programmable packet scheduling design"),
    ("vpifo2024", "vPIFO", "2 Background",
     "virtualises the packet scheduler for hierarchical scheduling"),
    ("drpifo2024", "DR-PIFO", "2 Background",
     "uses a dynamic ranking rule over a PIFO queue"),
    ("dpifo2024", "D-PIFO", "2 Background",
     "gives a dynamic priority scheduling algorithm for performance-critical packets"),
    ("cipo2024", "CIPO", "2 Background",
     "proposes a lightweight programmable packet scheduling primitive"),
    ("fipo2025", "FIPO", "2 Background",
     "proposes a software-defined programmable scheduling primitive"),
    ("spring2025", "Spring: Theory", "2 Background",
     "treats programmable packet scheduling with SP-PIFO as a problem with a heuristic"),
    ("lark2025", "Lark: A Buffer-aware", "2 Background",
     "makes buffer state part of a programmable packet scheduling building block"),
    ("schedfpga2025", "Programmable Packet Scheduling on FPGA", "2 Background",
     "demonstrates programmable packet scheduling on FPGA switches"),
    ("tsfifo2023", "Making programmable packet scheduling time-sensitive", "2 Background",
     "reconciles programmable scheduling with a FIFO queue for time-sensitive traffic"),
    ("hwrank2023", "A Hardware Architecture of a Dynamic Ranking", "2 Background",
     "gives hardware for a dynamic ranking packet scheduler"),
    ("ratesched2024", "A Programmable Packet Scheduling Method Based on Traffic Rate", "2 Background",
     "makes the arrival rate an input to packet scheduling"),
    ("fifo2024", "first-in-first-out", "2 Background",
     "analyses FIFO-based round-robin multicast scheduling, the discipline this paper compares against"),
    ("nearsched2024", "Near-Optimal Packet Scheduling in Multihop", "2 Background",
     "schedules packets to deadlines in multihop networks"),
    ("acceltor2025", "AccelToR", "2 Background",
     "uses packet scheduling to accelerate TCP in hybrid data centers"),
    ("ddspq2025", "DDSPQ", "2 Background",
     "schedules multi-tier service traffic with strict-priority queues"),
    ("p4sched2021", "A P4-Based Packet Scheduling Approach", "2 Background",
     "implements packet scheduling on a P4 data plane"),
    ("dpdk2021", "An Adaptive Throughput-First Packet Scheduling", "2 Background",
     "schedules packets in a DPDK-based processing system"),
    ("anomaly2026", "ALADA: Packet-Level Analysis", "2 Background",
     "analyses packets at line rate on a programmable data plane"),
    ("qosdp2024", "An Intelligent and Programmable Data Plane for QoS", "2 Background",
     "makes quality of service a programmable-data-plane function"),
    ("timeaware2025", "Time-Aware Packet Forwarding", "2 Background",
     "uses time as an input to forwarding decisions in programmable data planes"),
    ("p4survey2023", "AI-Driven Packet Forwarding With Programmable Data Plane", "2 Background",
     "surveys programmable-data-plane forwarding"),
    ("smartnic2023", "Unleashing SmartNIC Packet Processing", "2 Background",
     "reports what a SmartNIC data plane can do at packet rate"),

    # ---------------- 3. The device model: switch scheduling and disciplines --
    ("bvn2024", "Birkhoff-Von Neumann Decomposition", "3 The device model",
     "decomposes a switch schedule, the matrix form of the assignment this paper enumerates"),
    ("voq2019", "virtual output queuing switch", "3 The device model",
     "schedules a switch through per-output queues rather than one global order"),
    ("qpsr2021", "QPS-r", "3 The device model",
     "gives an iterative switching algorithm for input-queued switches"),
    ("hdmrr2019", "Half-Draining Round Robin Matching", "3 The device model",
     "matches a switch with a round-robin scheme"),
    ("lqf2010", "Longest queue first", "3 The device model",
     "schedules by queue occupancy, a discipline distinct from the rank-band rule measured here"),
    ("maxweight2020", "approximate max-weight matching", "3 The device model",
     "analyses matching algorithms for input-queued switches under heavy traffic"),
    ("ciocq2026", "Combined Input and Output Queued", "3 The device model",
     "reports delay under combined input-output queueing"),
    ("oqsq2009", "On Tracking the Behavior of an Output-Queued Switch", "3 The device model",
     "compares what an output-queued switch does with what an input-queued one can imitate"),
    ("pim2009", "parallel iterative matching", "3 The device model",
     "analyses parallel iterative matching, the matching approach an output-queued abstraction would need"),
    ("mwm2012", "Diffusion Approximation for an Input-queued Switch", "3 The device model",
     "approximates an input-queued switch under maximum-weight matching"),
    ("clos2007", "Clos-Network Packet Switches", "3 The device model",
     "builds scalable switch fabrics whose scheduling problem is a matching one"),
    ("multicast2017", "Iterative multicast scheduling algorithm", "3 The device model",
     "extends switch scheduling to multicast with variable packet size"),
    ("strprio2016", "Strict Priority Queueing", "3 The device model",
     "reports how low-priority traffic behaves under strict priority, the dequeue discipline modelled here"),
    ("drr2025", "Convexity and Optimization in Deficit Round Robin", "3 The device model",
     "optimises deficit round robin for delay-constrained systems"),
    ("drr2012", "Cycle time distribution and control for the Deficit Round Robin", "3 The device model",
     "analyses the cycle time of the deficit round robin packet scheduler"),
    ("owfq2023", "OWFQ", "3 The device model",
     "approximates weighted fair queueing with calendar queues"),
    ("wfq2010", "two-class weighted fair queueing discipline", "3 The device model",
     "approximates a two-class weighted fair queueing discipline"),
    ("wfq2012", "Multi-resource fair queueing for packet processing", "3 The device model",
     "extends fair queueing from links to packet-processing resources"),
    ("cbllfq2020", "Class-Based Low Latency Fair Queueing", "3 The device model",
     "implements a class-based low-latency fair queueing scheduler"),
    ("priowfq2020", "integrated priority queue and weighted fair queue", "3 The device model",
     "combines priority and weighted fair queueing in one device"),
    ("rr2014", "Improved Weighted Round Robin", "3 The device model",
     "schedules packets in high-speed networks with a weighted round-robin discipline"),
    ("cqswitch2013", "crosspoint queued switch", "3 The device model",
     "reports weighted round-robin scheduling in a crosspoint-queued switch Fabric"),
    ("nocqos2012", "NoC Router Design Providing QoS", "3 The device model",
     "applies a round-robin discipline at a network-on-chip router"),
    ("rrbuffer2010", "Designing Packet Buffers Using Random Round Robin", "3 The device model",
     "makes the buffer's own access order part of the scheduling design"),

    # ---------------- 4. Combinatorics: queue decompositions and descents -----
    ("sortnetstack2008", "The Complexity of Sorting with Networks of Stacks and Queues", "4 Combinatorics",
     "studies exactly the objects this model uses: networks of queues and stacks as sorting devices"),
    ("dilworthgen2024", "A Generalization of Dilworth", "4 Combinatorics",
     "generalises Dilworth's decomposition to partially ordered multisets, the tied-rank case here"),
    ("dilworth2009", "A Decomposition Theorem for Partially Ordered Sets", "4 Combinatorics",
     "is the decomposition theorem the free-merge threshold is a corollary of"),
    ("chaindecomp2022", "Optimal balanced chain decomposition", "4 Combinatorics",
     "computes an optimal chain decomposition of a poset"),
    ("lisrevisited2026", "The longest increasing subsequence problem revisited", "4 Combinatorics",
     "revisits the longest-increasing-subsequence problem"),
    ("patience2018", "patience sorting", "4 Combinatorics",
     "is a commentary on the patience-sorting line of longest-increasing-subsequence results, where the decreasing-subsequence statistic lives"),
    ("ehrt2019", "What Do a Longest Increasing Subsequence", "4 Combinatorics",
     "connects subsequence structure to the permutation's own statistics"),
    ("parallellis2023", "Nearly Optimal Parallel Algorithms for Longest Increasing Subsequence", "4 Combinatorics",
     "computes the increasing subsequence statistic in parallel"),
    ("dynamiclis2021", "Improved dynamic algorithms for longest increasing subsequence", "4 Combinatorics",
     "maintains the increasing subsequence statistic under updates"),
    ("sublinear2021", "Improved Sublinear Time Algorithm for Longest Increasing Subsequence", "4 Combinatorics",
     "computes the statistic in sublinear time"),
    ("spacelis2019", "Space-Efficient Algorithms for Longest Increasing Subsequence", "4 Combinatorics",
     "computes the statistic in bounded space"),
    ("incr2020", "Pattern Avoiding Permutations with a Unique Longest Increasing Subsequence", "4 Combinatorics",
     "characterises permutations by their increasing subsequence structure"),
    ("descents2025", "Moderate deviations for the number of descents", "4 Combinatorics",
     "analyses the number of descents, the statistic that sets the device threshold"),
    ("descsharp2025", "Sharp analysis on the joint distribution of the number of descents", "4 Combinatorics",
     "gives the joint distribution of descents and inverse descents, the two sides of this model"),
    ("desclargedev2024", "Sharp large deviations and concentration inequalities for the number of descents", "4 Combinatorics",
     "bounds the descents statistic's concentration"),
    ("mallows2022", "A central limit theorem for descents of a Mallows permutation", "4 Combinatorics",
     "gives a limit theorem for descents including the inverse statistic"),
    ("rsk2024", "A Bump Statistic on Permutations Resulting from the Robinson", "4 Combinatorics",
     "relates permutation statistics through the Robinson-Schensted correspondence"),
    ("rskpoisson2023", "Poisson limit theorems for the Robinson", "4 Combinatorics",
     "gives limit theorems for the correspondence that maps permutations to tableaux"),
    ("rsk2019", "The Robinson", "4 Combinatorics",
     "states the correspondence between permutations and pairs of tableaux"),
    ("continfrac2018", "Continued fractions for permutation statistics", "4 Combinatorics",
     "treats permutation statistics generationally"),
    ("widthentropy2015", "Poset Entropy Versus Number of Linear Extensions", "4 Combinatorics",
     "relates a poset's width to its linear extensions"),
    ("posetramsey2024", "Poset Ramsey Number", "4 Combinatorics",
     "studies posets combinatorially, adjacent machinery to the decomposition used here"),
    ("stacksort2026", "Stack-sorting with stacks avoiding vincular patterns", "4 Combinatorics",
     "characterises which permutations a stack-sorting device can produce"),

    # ---------------- 5. Online algorithms and lookahead ----------------------
    ("onpktlookahead2019", "Online packet scheduling with bounded delay and lookahead", "5 Online algorithms",
     "is the closest online-scheduling analogue of the foresight comparison here: what lookahead buys a packet scheduler"),
    ("lookaheadexact2020", "Exact distributional analysis of online algorithms with lookahead", "5 Online algorithms",
     "analyses online algorithms exactly under lookahead"),
    ("lookaheadcorr2021", "Correction to: Exact distributional analysis", "5 Online algorithms",
     "corrects the distributional analysis of lookahead"),
    ("onlineinterval2019", "Online interval scheduling on two related machines: the power of lookahead", "5 Online algorithms",
     "measures what lookahead buys in an online interval scheduling problem"),
    ("machinemin2020", "Online machine minimization with lookahead", "5 Online algorithms",
     "treats lookahead as information in an online minimisation problem"),
    ("unitbatch2019", "Online Algorithms for Scheduling Unit Length Jobs", "5 Online algorithms",
     "schedules unit-length jobs online under batching constraints"),
    ("metmatch2021", "online metric matching problem", "5 Online algorithms",
     "competitively analyses an online matching problem"),
    ("semiuniform2024", "Semi-online scheduling on two uniform parallel machines with initial lookahead", "5 Online algorithms",
     "measures the value of initial lookahead in semi-online scheduling"),
    ("permpred2025", "Permutation Predictions for Non-Clairvoyant Scheduling", "5 Online algorithms",
     "feeds a permutation prediction to a non-clairvoyant scheduler, the information shape this model computes exactly"),
    ("competcloud2024", "Competitive Analysis of Algorithms for an Online Distribution Problem", "5 Online algorithms",
     "applies competitive analysis to an online allocation problem"),

    # ---------------- 6. Priority-queue data structures and hardware ---------
    ("antq2023", "AnTiQ", "6 Data structures",
     "gives a hardware priority queue with constant-time removal, the device-side cost of the abstraction"),
    ("fastpq2024", "A Fast Scalable Hardware Priority Queue", "6 Data structures",
     "scales a hardware priority queue with multi-push"),
    ("pipelinedheap2007", "Pipelined Heap", "6 Data structures",
     "pipelines heap management for scheduling in high-speed networks"),
    ("randpq1998", "Randomized Priority Queues for Fast Parallel Access", "6 Data structures",
     "makes a priority queue accessible in parallel at random"),
    ("binomialheaps2000", "Parallel priority queues based on binomial heaps", "6 Data structures",
     "builds parallel priority queues on binomial heaps"),
    ("jheaps2021", "JHeaps", "6 Data structures",
     "packages priority-queue implementations as a library"),
    ("qpidsr2026", "QPID: A Scalable, Strict Concurrent Priority Queue", "6 Data structures",
     "gives a strictly concurrent priority queue"),
    ("decreasingkeys2024", "Priority queues with decreasing keys", "6 Data structures",
     "treats priority queues whose keys only decrease, a monotone-input restriction"),
    ("delaunay1993", "The relaxed min-max heap", "6 Data structures",
     "gives a double-ended heap structure"),
    ("deap1987", "The deap", "6 Data structures",
     "implements a double-ended priority queue"),
    ("minmax1999", "Symmetric Min-Max heap", "6 Data structures",
     "simplifies double-ended priority-queue construction"),
    ("binaryheaps2025", "Binary Heaps and Priority Queues", "6 Data structures",
     "states the elementary heap-to-priority-queue correspondence"),

    # ---------------- 7. Measurement context --------------------------------
    ("ctpifo2025", "CT-PIFO", "7 Measurement",
     "reports flow completion time as the end-to-end cost of the scheduler"),
    ("noc2024", "Design and Implementation of Network", "7 Measurement",
     "reports a network-on-chip router implementation, an adjacent interconnect setting"),
    ("trimmer2022", "A Templated VHDL Architecture for Terabit/s", "7 Measurement",
     "reports a packet-parsing architecture at terabit scale"),
    ("smartnicallreduce2024", "Leveraging SmartNIC for Ring AllReduce", "7 Measurement",
     "offloads a collective to a SmartNIC"),
    ("xdp2023", "OXDP", "7 Measurement", "offloads packet processing to a SmartNIC"),
    ("frag2026", "Offloading IP Packet Fragmentation", "7 Measurement",
     "offloads packet handling to a SmartNIC in P4"),
]

# ---------------------------------------------------------------------------
# Records the query harvest could not return, fetched by DOI (fetch_seeds.py).
# A seed is a declared addition, not a silent one: each carries the reason the
# harvest missed it, and each is placed like any other entry -- a section and
# the sentence it supports.
# ---------------------------------------------------------------------------
SEED_PLACEMENT = [
    ("evenitai1971", "1 Prior art",
     "established one of the queue-network sorting problems whose machinery the device statistic belongs to"),
    ("tarjan1972", "1 Prior art",
     "gives sorting with networks of queues and stacks, the same objects this model's queue bank realises"),
    ("pratt1973", "1 Prior art",
     "computes which permutations parallel queues produce -- the closest prior statement to this paper's question"),
    ("pifo2016", "2 Background",
     "introduces PIFO, the queue abstraction whose exact behaviour a programmable switch approximates"),
]

# A title that matches more than one harvested record is settled by DOI, not by
# a longer substring: the DOI names the record, the title only names a string.
DOI_OVERRIDE = {
    "sppifo2022": "10.1109/infocomwkshps54753.2022.9798055",
    "voq2019": "10.1049/iet-net.2018.5115",
    "ciocq2026": "10.1109/ojcoms.2026.3726416",
    "clos2007": "10.1109/lcomm.2007.061617",
    "cqswitch2013": "10.1109/telfor.2013.6716184",
    "dilworth2009": "10.1007/978-0-8176-4842-8_10",
    "patience2018": "10.1090/bull/1623",
    "rsk2019": "10.1090/stml/091/08",
    "posetramsey2024": "10.1007/s11083-024-09663-z",
    "unitbatch2019": "10.1142/s0217595919500246",
    "antq2023": "10.1109/dsd60849.2023.00070",
    "strprio2016": "10.1109/iccci.2016.7480023",
}

# Candidates I named and then withdrew, each with its reason. A placement list
# that only grows hides its own judgement; this one keeps the count, so the
# report can say how many of the pool's records were considered and dropped.
PRUNED = [
    ("fifo2022", "duplicate of sppifo2022 -- same record under a second key"),
    ("stacksort2013", "no such record in the pool: the title was recalled, not harvested"),
    ("twostack2019", "no such record in the pool: the title was recalled, not harvested"),
    ("fct2025", "duplicate DOI 10.1109/icccn65249.2025.11134021 -- the CT-PIFO record, kept once as ctpifo2025"),
    ("tail2025", "duplicate DOI 10.1109/infocom55648.2025.11044448 -- the Lark record, kept once as lark2025"),
    ("lislds2019", "duplicate DOI 10.3390/a12110237 -- the LIS/LDS record, kept once as ehrt2019"),
]


def load():
    with open(CAND, encoding="utf-8") as fh:
        return json.load(fh)


def load_seeds():
    if not os.path.exists(SEEDS):
        return None
    with open(SEEDS, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(key, title_sub, candidates):
    """DOI first when one is declared, else exact title, else unique substring.

    Ambiguity is an error, never a guess: two records that share a title are
    settled by naming the DOI, not by taking whichever printed first.
    """
    if key in DOI_OVERRIDE:
        want = DOI_OVERRIDE[key].lower()
        hits = [c for c in candidates if c["doi"].lower() == want]
        if len(hits) == 1:
            return hits[0], "doi"
        return None, ("DOI-%s: %s" % ("absent from pool" if not hits else "matches >1", want))
    hits = [c for c in candidates if c["title"].lower() == title_sub.lower()]
    if len(hits) == 1:
        return hits[0], "exact"
    hits = [c for c in candidates if title_sub.lower() in c["title"].lower()]
    if len(hits) == 1:
        return hits[0], "unique-substring"
    if not hits:
        return None, "ABSENT"
    return None, "AMBIGUOUS: " + " | ".join(h["title"][:60] for h in hits[:4])


def main():
    data = load()
    candidates = data["candidates"]
    placed, problems = [], []

    for key, title_sub, section, claim in PLACEMENT:
        rec, how = resolve(key, title_sub, candidates)
        if rec is None:
            problems.append("%-22s %s (%s)" % (key, title_sub[:50], how))
            continue
        placed.append({
            "key": key,
            "doi": rec["doi"],
            "title": rec["title"],
            "authors": rec["authors"],
            "venue": rec["venue"],
            "year": rec["year"],
            "type": rec["type"],
            "section": section,
            "claim": claim,
            "resolved_by": how,
        })

    # Seeds: DOI-verified records the query harvest structurally could not return.
    seed_doc = load_seeds()
    if seed_doc is None:
        problems.append("seeds.json missing -- run fetch_seeds.py (seeds are not optional)")
        seeds_by_key = {}
    else:
        if seed_doc.get("failed"):
            problems.append("seeds.json records %d failed DOI fetch(es)" % len(seed_doc["failed"]))
        seeds_by_key = {s["key"]: s for s in seed_doc.get("seeds", [])}

    for key, section, claim in SEED_PLACEMENT:
        rec = seeds_by_key.get(key)
        if rec is None:
            problems.append("%-22s seed absent from seeds.json" % key)
            continue
        placed.append({
            "key": key,
            "doi": rec["doi"],
            "title": rec["title"],
            "authors": rec["authors"],
            "venue": rec["venue"],
            "year": rec["year"],
            "type": rec["type"],
            "section": section,
            "claim": claim,
            "resolved_by": "seed-doi",
        })

    # every placed key unique, every placed entry names a section and a claim
    seen = set()
    for p in placed:
        if p["key"] in seen:
            problems.append("duplicate key %s" % p["key"])
        seen.add(p["key"])
        if not p["section"] or not p["claim"]:
            problems.append("%s has no section or no claim" % p["key"])
    # one bibliography entry per work. Two keys pointing at one DOI is the same paper
    # printed twice, which is a defect a reader sees at once and no other check sees:
    # each key resolves, each DOI verifies, and the list still contains the work twice.
    seen_doi = {}
    for p_ in placed:
        if p_["doi"] in seen_doi:
            problems.append("duplicate work: %s and %s share DOI %s"
                            % (seen_doi[p_["doi"]], p_["key"], p_["doi"]))
        seen_doi[p_["doi"]] = p_["key"]
    # a pruned key that is nevertheless placed means the withdrawal did not take
    for key, reason in PRUNED:
        if key in seen:
            problems.append("pruned key %s is still placed (%s)" % (key, reason))
    # a section that no entry names would mean a bibliography section with nothing to say
    sections = {}
    for p in placed:
        sections[p["section"]] = sections.get(p["section"], 0) + 1

    out = {
        "placed": sorted(placed, key=lambda p: (p["section"], p["key"])),
        "pruned": [{"key": k, "reason": r} for k, r in PRUNED],
        "counts": {"placed": len(placed), "by_section": sections,
                   "candidate_pool": len(candidates),
                   "attempted": len(PLACEMENT) + len(SEED_PLACEMENT),
                   "seeds": len(SEED_PLACEMENT),
                   "pruned": len(PRUNED),
                   "absent_or_ambiguous": len(problems)},
        "problems": problems,
    }
    payload = json.dumps(out, indent=2, sort_keys=True) + "\n"

    # --check recomputes and compares against the committed artifact instead of
    # writing it. A gate that rewrites what the verification report describes
    # would make that report unanchored: it would keep describing the artifact
    # of a previous run while this one silently replaced it.
    if "--check" in sys.argv[1:]:
        # A stored artifact can match a broken placement byte for byte (it was
        # written by that same broken run). The placement must resolve on its own
        # merits before any comparison to the stored file is worth making.
        if problems:
            print("PROBLEMS (%d) -- the placement does not resolve, so its stored artifact proves nothing:" % len(problems))
            for p in problems:
                print("   " + p)
            return 1
        if not os.path.exists(OUT):
            print("ARTIFACT ABSENT: %s -- run without --check to write it" % os.path.basename(OUT))
            return 1
        with open(OUT, encoding="utf-8") as fh:
            stored = fh.read()
        if stored != payload:
            print("STALE: %s does not match what this placer computes" % os.path.basename(OUT))
            print("       re-run without --check and re-verify the references")
            return 1
        print("\nPLACEMENT: IN SYNC (%d entries, %s matches)" % (len(placed), os.path.basename(OUT)))
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(payload)

    print("attempted : %d (%d harvested + %d seeds)" % (len(PLACEMENT) + len(SEED_PLACEMENT), len(PLACEMENT), len(SEED_PLACEMENT)))
    print("placed    : %d" % len(placed))
    for s in sorted(sections):
        print("   %-22s %d" % (s, sections[s]))
    print("pruned    : %d" % len(PRUNED))
    for k, r in PRUNED:
        print("   %-22s %s" % (k, r))
    if problems:
        print("\nPROBLEMS (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        return 1
    print("\nPLACEMENT: OK (every named record resolved to exactly one candidate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
