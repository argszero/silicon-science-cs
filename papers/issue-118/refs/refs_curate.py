#!/usr/bin/env python3
"""Issue #118 -- reference CURATION.

Curation is NOT discovery and NOT verification.  This file makes an EXPLICIT choice: a list of
bare arXiv ids with a role and a one-line stated difference from this work.  Titles are COPIED from
the discovery artefact (`refs/candidates.json`) by identifier -- never retyped -- and any chosen id
that is not in the pool must be declared in EXTRAS with its own title, so the difference between
"found by search" and "supplied by the author" stays visible.

A role is a statement about WHERE an entry is used, not a quality label.

Usage:  /usr/bin/python3 refs_curate.py
Out:    refs/curated.json
"""
import json
import os
import re
import sys

CAND = "refs/candidates.json"
OUT = "refs/curated.json"

# (bare arXiv id, role, stated difference / use)
CHOSEN = [
    # ---------------- construct: the capacity factor, dropping, and the routing discipline -------
    ("2101.03961", "construct", "origin of expert capacity with C = 1.25 and of token dropping as an accepted cost"),
    ("2006.16668", "construct", "origin of the C = 2.0 capacity factor in a sharded sparse model"),
    ("2112.06905", "construct", "a 64-expert top-2 model whose capacity factor is stated rather than derived"),
    ("2508.12801", "construct", "premises on an expert capacity constraint to keep computation GPU-friendly, without characterising it"),
    ("2202.09368", "construct", "inverts the assignment direction (experts choose tokens), which is the architectural escape this paper bounds"),
    ("2308.00951", "construct", "removes the discrete assignment altogether, the C -> infinity limit of the same dispatch"),
    ("2005.07761", "construct", "drops tokens to balance load; this paper asks what dropping costs and what capacity prevents it"),
    ("2203.13240", "construct", "token dropping as a training accelerator for BERT, a different sense of the word (importance-based, not capacity-based)"),
    ("2211.11586", "construct", "random layer-wise token dropping for training cost, no per-expert budget involved"),
    ("2106.04426", "construct", "fixed hash-based assignment, i.e. the deterministic dispatch this paper identifies as the escape"),
    ("2105.15082", "construct", "scales experts and reports capacity effects empirically without a drop law"),
    ("2010.11018", "construct", "an early token-drop mechanism for NMT, before MoE capacity budgets existed"),

    # ---------------- balancing: the field's standard remedy -------------------------------------
    ("2408.15664", "balancing", "the bias-based auxiliary-loss-free balancing the field now uses; this paper shows it cannot fix overflow"),
    ("2512.03915", "balancing", "a theory of auxiliary-loss-free balancing over the routing DISTRIBUTION, never over its tail"),
    ("2109.11817", "balancing", "unbiased gradient estimators under a capacity constraint; the constraint is assumed, not derived"),
    ("2502.15451", "balancing", "formulates balancing as binary integer programming; a routing-side remedy, so bounded by the ceiling here"),
    ("2602.03478", "balancing", "studies degenerate routing collapse, the skew end of the imbalance this law separates from the sampling term"),
    ("2504.01337", "balancing", "a collaboration-constrained routing strategy; again a population fix for a tail problem"),
    ("2411.19402", "balancing", "argues discrete assignment matters for a different reason (representation), not for overflow"),
    ("2602.14159", "balancing", "regularisation losses for expert specialisation; measured against the balance floor this paper derives"),

    # ---------------- capacity / straggler -------------------------------------------------------
    ("2503.05066", "capacity", "mitigates the straggler effect that an over-set capacity factor causes; treats the symptom this law prices"),
    ("2403.07652", "capacity", "routes harder tasks to more experts, i.e. varies top-k, whose effect on capacity this law makes exact"),
    ("2502.16927", "capacity", "a communication-efficient structure whose capacity implications are not analysed"),

    # ---------------- serving: the decode regime where the constant is out of domain -------------
    ("2201.05596", "serving", "an early MoE inference/training system; reports throughput without a capacity law"),
    ("2308.12066", "serving", "pre-gates to avoid fetching inactive experts, a caching answer to the same dispatch problem"),
    ("2401.14361", "serving", "expert caching for personal machines; the cache-miss regime is where per-expert load falls into the tail-dominated range"),
    ("2410.17954", "serving", "predictive expert caching, an alternative to buying capacity"),
    ("2411.01433", "serving", "mixed-precision offloading; memory-bound decode where the folk constant is out of domain"),
    ("2502.05370", "serving", "fine-grained expert offloading for the latency-memory trade-off; no capacity characterisation"),
    ("2504.05897", "serving", "hybrid CPU-GPU scheduling with cache management; another systems-side answer"),
    ("2504.02263", "serving", "disaggregated expert parallelism at scale; dispatch volume is the cost this law's capacity factor governs"),
    ("2505.16056", "serving", "reports that routing consistency decides offloading viability, a measured property of the load distribution"),
    ("2506.12708", "serving", "a production serving system for large models; capacity policy is an implementation detail there"),
    ("2512.12990", "serving", "bit-sliced expert caching under miss-rate constraints; the constraint this law would let one derive"),
    ("2602.16052", "serving", "expert budgeting for speculative decoding, where draft trees activate many unique experts at once"),
    ("2603.06350", "serving", "serverless experts for MoE serving; straggler control by systems means"),
    ("2604.18788", "serving", "routing produces dynamic tensor shapes that fight fixed NPU kernels -- a hardware reason the capacity must be bounded"),
    ("2604.23150", "serving", "multi-node inference driven by expert activation patterns; the measured load distribution this law takes as input"),
    ("2609.33385", "serving", "inter-iteration locality-aware expert caching; a decode-time system"),
    ("2610.01950", "serving", "coordinated expert offloading and residency, published 2026-10-01 within the hotspot window"),
    ("2308.15030", "serving", "tunable memory budgets for serving off-the-shelf MoE models"),
    ("2502.06888", "serving", "expert-aware multi-batch pipelining; batching changes T and therefore mu, which this law makes explicit"),
    ("2508.09208", "serving", "collaborative expert aggregation and offloading"),
    ("2508.19373", "serving", "hybrid adaptive parallelism for MoE inference"),
    ("2508.18983", "serving", "pushing MoE to the edge via expert substitution"),
    ("2501.10375", "serving", "data-aware offloading with predictive pre-calculation"),
    ("2502.12224", "serving", "cross-layer gate prediction for edge inference"),
    ("2601.05296", "serving", "breaking the memory wall for MoE training on modern GPUs"),
    ("2605.10670", "serving", "surviving partial rank failures in wide expert-parallel inference"),

    # ---------------- architecture: the named systems the map places on the curve -----------------
    ("2401.04088", "architecture", "sparse top-2 of 8; one of the ten configurations the production map places on the law"),
    ("2401.06066", "architecture", "fine-grained expert segmentation with shared experts; the paper that precedes the DeepSeek line"),
    ("2405.04434", "architecture", "the 160-expert top-6 configuration used in the production map"),
    ("2412.19437", "architecture", "states explicitly that it drops no tokens -- the architectural escape observed in a production system"),
    ("2409.02060", "architecture", "a fully open MoE with published expert counts and routing"),
    ("2406.00023", "architecture", "bidirectional routing affinity; a routing design against which the drop functional could be evaluated"),
    ("2406.13233", "architecture", "token-adaptive routing with null experts, i.e. a structured way to avoid overflow rather than bound it"),
    ("2410.10456", "architecture", "adaptive-k routing, which changes the number of experts per token and hence the effective capacity"),
    ("2505.22323", "architecture", "advancing expert specialisation, the objective that pushes the router toward the skew this law costs"),
    ("2503.15798", "architecture", "a lookup-expert structure that trades routing for retrieval"),
    ("2412.10302", "architecture", "the multimodal member of the DeepSeek MoE line"),
    ("2608.08650", "survey", "a 2026 survey of MoE routing and topology, the closest thing to a map of the design space this paper formalises a cell of"),
    ("2602.03204", "survey", "quantifies MoE expressivity via tropical geometry -- a capacity-free view of the same architecture"),
    ("2602.17798", "survey", "concentration-controlled routing on a subspace manifold, a geometric routing variant"),
    ("2603.11114", "survey", "task-conditioned routing signatures, evidence that router distributions are measurable objects"),

    # ---------------- theory: tails, occupancy, order statistics, saddlepoint --------------------
    ("0508451", "theory", "the power of two choices, the canonical result that extra information beats extra capacity"),
    ("1201.3310", "theory", "tight bounds for multiple-choice balls-into-bins, the family this paper's finite-sample term belongs to"),
    ("2203.12400", "theory", "tight bounds for REPEATED balls-into-bins, the regime a serving loop actually sits in"),
    ("2205.14494", "theory", "simple concentration bounds for balls and bins, the form used for the finite-sample term"),
    ("1207.2125", "theory", "balls into bins via local search, an algorithmic route to lowering the maximum load"),
    ("1310.0801", "theory", "cover time and maximum load under local search, the trade-off the ceiling bounds"),
    ("2209.02220", "theory", "three distributions in the extended occupancy problem, the occupancy view of per-expert counts"),
    ("0410174", "theory", "large deviation asymptotics for occupancy problems, the rate-function machinery behind a tail-exact drop functional"),
    ("0609498", "theory", "the variance of the number of occupied boxes, the other occupancy functional a router controls"),
    ("0701718", "theory", "general asymptotics for the occupancy problem with infinitely many boxes"),
    ("1005.2616", "theory", "chains-into-bins, a dependent-arrival variant of the same occupancy model"),
    ("0911.2077", "theory", "central binomial tail bounds, one of the closed forms against which the exact route is compared"),
    ("2211.01688", "theory", "nearly tight universal binomial tail bounds, the modern replacement for the normal approximation this paper measures as low"),
    ("2502.18611", "theory", "tight binomial CDF bounds via KL-divergence, the sharpest tail reference"),
    ("2012.09968", "theory", "binomial tails for community analysis, a domain application of the same tail functional"),
    ("0508606", "theory", "Tusnady's inequality, a binomial-vs-Poisson comparison the lattice-correction finding touches"),
    ("1107.1533", "theory", "martingale couplings and tail bounds, the general machinery behind the tail-expectation kernel"),
    ("1111.6358", "theory", "tail bounds using skewness and kurtosis, exactly what the Edgeworth correction in this paper exploits"),
    ("0806.1007", "theory", "competition between discrete random variables with occupancy applications, a maximum-of-counts analysis"),
    ("0407023", "theory", "hashing with two memory accesses, the algorithmic sibling of power-of-two-choices for a shared budget"),
    ("1203.3106", "theory", "saddlepoint approximations for likelihood-ratio-like statistics, the method this paper tested and rejected with a control"),
    ("0508604", "theory", "saddlepoint approximation without moment conditions, the family's robustness result"),
    ("0803.2132", "theory", "uniform saddlepoint approximations for ratios of quadratic forms"),

    # ---------------- security: overflow as an attack surface ------------------------------------
    ("2608.25371", "security", "makes capacity-bounded dispatch a backdoor blind spot; this paper quantifies the displacement budget that attack consumes"),
    ("2504.18598", "security", "backdoors MoE routing by trigger optimisation; routing is the attack surface, capacity is the budget"),
    ("2510.13462", "security", "dynamic expert routing in backdoored MoE models, a second independent routing-attack study"),
    ("2410.22884", "security", "prompt stealing from MoE models via the routing signal, evidence that per-expert load is observable to an adversary"),

    # ---------------- efficiency: adjacency the paper does not claim to supersede -----------------
    ("2206.00277", "efficiency", "task-specific expert pruning, which changes E and therefore the capacity curve"),
    ("2503.06881", "efficiency", "space-efficient expert compression via residual restoration"),
    ("2404.05019", "efficiency", "shortcut-connected expert parallelism to cut dispatch cost"),
    ("2504.14960", "efficiency", "heterogeneous parallelism mappings for large-scale MoE training"),
    ("2411.15419", "efficiency", "sequence migration and token routing to cut communication, i.e. the cost side of a capacity choice"),
    ("2608.28511", "efficiency", "layer reconfiguration for communication-efficient MoE training"),
    ("2407.04656", "efficiency", "resilient and elastic MoE training, where expert loss and imbalance interact"),
    ("2411.16786", "efficiency", "staleness-centric optimisations for parallel diffusion MoE inference"),
    ("2506.23635", "efficiency", "multi-node expert parallelism on Apple Silicon, a hardware-specific dispatch study"),
    ("2604.12163", "architecture", "a sparse MoE image generator, evidence the routing pattern is architecture-independent"),
    ("2608.17402", "architecture", "an MoE vision encoder; the same dispatch discipline in a non-text modality"),
]

# Entries the author supplies that the search did NOT surface (declared, with their own titles).
EXTRAS = [
    ("2605.11689", "survey", "states that MoE design choices including token dropping were studied one or two at a time over narrow configuration ranges -- the gap this paper fills",
     "Slicing and Dicing: Configuring Optimal Mixtures of Experts"),
    ("2610.01265", "serving", "adaptive residual offloading for large-scale MoE inference, the other half of the 2026-10-01 hotspot pair (author-anchored; not surfaced by the discovery queries)",
     "RapidMoE: Exploiting Cross-Asymmetry via Adaptive Residual Offloading for Large-Scale MoE Inference"),
    ("2407.10671", "architecture", "the MoE member of the Qwen2 family, one of the configurations the production map places on the law (author-anchored; the discovery queries reached only Qwen-CUA)",
     "Qwen2 Technical Report"),
]

def bare(aid):
    return re.sub(r"v\d+$", "", aid)

def main():
    if not os.path.exists(CAND):
        print("missing %s -- run refs_discover.py first" % CAND, file=sys.stderr); sys.exit(1)
    pool = json.load(open(CAND))["candidates"]
    bybare = {}
    for c in pool:
        bybare.setdefault(bare(c["id"]), c)
    out, missing = [], []
    for aid, role, diff in CHOSEN:
        c = bybare.get(bare(aid))
        if c is None:
            missing.append(aid); continue
        out.append(dict(id=c["id"], bare=bare(c["id"]), title=c["title"], published=c["published"],
                        cats=c["cats"], role=role, diff=diff, source="discovery"))
    for aid, role, diff, title in EXTRAS:
        out.append(dict(id=aid, bare=bare(aid), title=title, published="(author-supplied)",
                        cats=[], role=role, diff=diff, source="author"))
    if missing:
        print("!! %d chosen ids NOT in the pool: %s" % (len(missing), missing), file=sys.stderr)
        sys.exit(2)
    ids = [o["bare"] for o in out]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        print("!! duplicate curated ids: %s" % dupes, file=sys.stderr); sys.exit(3)
    roles = {}
    for o in out:
        roles[o["role"]] = roles.get(o["role"], 0) + 1
    os.makedirs("refs", exist_ok=True)
    json.dump(dict(n=len(out), roles=roles, entries=out), open(OUT, "w"), indent=1)
    print("curated %d entries -> %s" % (len(out), OUT))
    for r in sorted(roles):
        print("   %-14s %d" % (r, roles[r]))

if __name__ == "__main__":
    main()
