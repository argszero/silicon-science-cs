"""
gen.py — Seeded synthetic workload generator.

Creates cluster + pod set where inter-pod constraints appear between *types*
with probability `density` (the constraint-density axis of the study).

Topology: R racks x N nodes per rack. Nodes carry labels az/rack/host.
Pods: instances of types; each type has resource reqs and a label. A type
pair (t1, t2) gets an edge with probability density: affinity (t1 co-locates
with t2 at rack level) or anti-affinity (t1 avoids t2 at rack level).
"""
from __future__ import annotations

import random

from sim import Node, Pod, AffinityRule

RACK_KEY = "rack"
HOST_KEY = "host"
AZ_KEY = "az"


def gen_cluster(rng: random.Random, n_racks: int = 2, nodes_per_rack: int = 2,
                cpu_cap: float = 4.0, mem_cap: float = 8.0) -> list[Node]:
    nodes = []
    for r in range(n_racks):
        for k in range(nodes_per_rack):
            nodes.append(Node(
                id=f"n{r}-{k}",
                cpu_cap=cpu_cap,
                mem_cap=mem_cap,
                labels={AZ_KEY: f"az{0}", RACK_KEY: f"r{r}", HOST_KEY: f"n{r}-{k}"},
            ))
    return nodes


def gen_chain_pods(rng: random.Random, n_chains: int = 2, chain_len: int = 3,
                   per_type: int = 1, anti_fraction: float = 0.0) -> list[Pod]:
    """Directed prerequisite chains (greedy-trip regime).

    Chain c has types (c,0)..(c,L-1); type (c,k) requires affinity (In) with
    type (c,k+1) at rack level (k < L-1). If k+1 is placed first, k can follow;
    if k is scheduled before its prerequisite, greedy fails it. Optionally, with
    probability anti_fraction, a type also carries a required anti-affinity
    (NotIn) against the same prerequisite type (exclusion regime).
    """
    types = []
    for c in range(n_chains):
        for k in range(chain_len):
            types.append({
                "id": f"c{c}t{k}",
                "label": {"chain": f"c{c}", "pos": str(k)},
                "cpu": 1.0, "mem": 2.0,
                "aff": [(f"c{c}t{k+1}", "In")] if k + 1 < chain_len else [],
            })

    pods: list[Pod] = []
    pid = 0
    for tp in types:
        affs = []
        for target, op in tp["aff"]:
            affs.append(AffinityRule(selector={"chain": target.split("t")[0],
                                               "pos": target.split("t")[1]},
                                     topology_key=RACK_KEY, op=op))
            if rng.random() < anti_fraction:
                # exclusion: this type also avoids its prerequisite at rack level
                affs.append(AffinityRule(selector={"chain": target.split("t")[0],
                                                   "pos": target.split("t")[1]},
                                         topology_key=RACK_KEY, op="NotIn"))
        for _ in range(per_type):
            pods.append(Pod(id=f"p{pid}", cpu_req=tp["cpu"], mem_req=tp["mem"],
                            labels=tp["label"], affinities=affs))
            pid += 1
    return pods


def gen_pods(rng: random.Random, n_types: int = 3, per_type: int = 2,
             density: float = 0.5, seed_pod_affinity_both_ways: bool = True) -> list[Pod]:
    """Generate pods with type-pair constraint edges.

    density in [0,1]: probability that an unordered type pair (t1,t2) has a
    directed constraint t1 -> t2 (affinity or anti-affinity).
    """
    types = []
    for t in range(n_types):
        types.append({
            "label": {"type": f"t{t}"},
            "cpu": rng.choice([1.0, 2.0]),
            "mem": rng.choice([2.0, 4.0]),
        })

    # draw constraint edges between unordered pairs
    edges: dict[tuple[int, int], str] = {}  # (t1,t2) -> op for t1 w.r.t. t2
    for t1 in range(n_types):
        for t2 in range(t1 + 1, n_types):
            if rng.random() < density:
                op = rng.choice(["In", "NotIn"])
                edges[(t1, t2)] = op

    pods: list[Pod] = []
    pid = 0
    for t in range(n_types):
        tp = types[t]
        for _ in range(per_type):
            affs = []
            for (t1, t2), op in edges.items():
                if t == t1:
                    affs.append(AffinityRule(selector=types[t2]["label"],
                                             topology_key=RACK_KEY, op=op))
                elif t == t2:
                    # reverse direction: t2 co-locates/avoids t1
                    # (keep the same semantic for mutual edges if seeded)
                    rev_op = op if seed_pod_affinity_both_ways else rng.choice(["In", "NotIn"])
                    affs.append(AffinityRule(selector=types[t1]["label"],
                                             topology_key=RACK_KEY, op=rev_op))
            pods.append(Pod(
                id=f"p{pid}",
                cpu_req=tp["cpu"],
                mem_req=tp["mem"],
                labels=tp["label"],
                affinities=affs,
            ))
            pid += 1
    return pods
