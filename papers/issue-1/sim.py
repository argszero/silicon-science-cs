"""
sim.py — Kubernetes-scheduler-semantics simulator (simplified but faithful).

Models the core of kube-scheduler for the *placement decision*:
  - predicate phase: resource fit, nodeSelector, required podAffinity /
    podAntiAffinity (inter-pod topology-domain constraints)
  - scoring phase: kube-scheduler-style LeastRequestedPriority

Pods are scheduled sequentially in a given order (k8s semantics); a pod that
has no feasible node is left unschedulable (counted, not retried).

Semantics notes (from Kubernetes docs):
  - required podAffinity: pod can be placed on node n only if there exists an
    already-placed pod matching the rule's label selector in the same topology
    domain as n (topologyKey = domain dimension, e.g. "rack" or "host").
  - required podAntiAffinity: pod can be placed on node n only if there is NO
    already-placed matching pod in the same topology domain as n.
  - A node's own topology domain includes itself (a matching pod on the same
    node satisfies affinity; an anti-affinity match on the same node forbids it).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------
# models
# --------------------------------------------------------------------------

@dataclass
class Node:
    id: str
    cpu_cap: float
    mem_cap: float
    labels: dict[str, str] = field(default_factory=dict)  # e.g. {"az": "a", "rack": "r1"}

    def topo_value(self, key: str) -> Optional[str]:
        return self.labels.get(key)


@dataclass
class AffinityRule:
    """One required inter-pod constraint.

    selector: label the *other* pod must carry to count as a match.
    topology_key: domain dimension ("rack"/"host").
    op: "In" (co-locate: >=1 match in domain) | "NotIn" (anti: 0 matches in domain).
    """
    selector: dict[str, str]
    topology_key: str
    op: str  # "In" | "NotIn"

    def matches(self, other_labels: dict[str, str]) -> bool:
        return all(other_labels.get(k) == v for k, v in self.selector.items())


@dataclass
class Pod:
    id: str
    cpu_req: float
    mem_req: float
    labels: dict[str, str] = field(default_factory=dict)  # labels this pod carries
    node_selector: dict[str, str] = field(default_factory=dict)  # label constraint on nodes
    affinities: list[AffinityRule] = field(default_factory=list)  # required affinity/anti-affinity


@dataclass
class Cluster:
    nodes: list[Node]

    def topo_group(self, key: str, value: str) -> list[Node]:
        return [n for n in self.nodes if n.labels.get(key) == value]


# --------------------------------------------------------------------------
# feasibility (predicate phase)
# --------------------------------------------------------------------------

def _node_fits(node: Node, pod: Pod, used: dict[str, tuple[float, float]]) -> bool:
    uc, um = used.get(node.id, (0.0, 0.0))
    return uc + pod.cpu_req <= node.cpu_cap + 1e-9 and um + pod.mem_req <= node.mem_cap + 1e-9


def _selector_ok(node: Node, pod: Pod) -> bool:
    return all(node.labels.get(k) == v for k, v in pod.node_selector.items())


def _affinity_ok(node: Node, pod: Pod, placed: list[tuple[Pod, Node]]) -> bool:
    """Check all required affinity/anti-affinity rules against `placed` pods."""
    for rule in pod.affinities:
        tv = node.topo_value(rule.topology_key)
        matches = [
            (p, n) for (p, n) in placed
            if rule.matches(p.labels) and n.topo_value(rule.topology_key) == tv
        ]
        if rule.op == "In" and not matches:
            return False
        if rule.op == "NotIn" and matches:
            return False
    return True


def feasible_nodes(cluster: Cluster, pod: Pod, placed: list[tuple[Pod, Node]],
                   used: dict[str, tuple[float, float]]) -> list[Node]:
    out = []
    for node in cluster.nodes:
        if not _node_fits(node, pod, used):
            continue
        if not _selector_ok(node, pod):
            continue
        if not _affinity_ok(node, pod, placed):
            continue
        out.append(node)
    return out


# --------------------------------------------------------------------------
# scoring (kube-scheduler LeastRequestedPriority flavor)
# --------------------------------------------------------------------------

def least_requested_score(node: Node, pod: Pod, used: dict[str, tuple[float, float]]) -> float:
    """Higher = node has more free capacity after placement (spread-like)."""
    uc, um = used.get(node.id, (0.0, 0.0))
    free_cpu = (node.cpu_cap - (uc + pod.cpu_req)) / node.cpu_cap
    free_mem = (node.mem_cap - (um + pod.mem_req)) / node.mem_cap
    return (free_cpu + free_mem) / 2.0


def best_fit_score(node: Node, pod: Pod, used: dict[str, tuple[float, float]]) -> float:
    """Higher = node most packed after placement (bin-pack-like)."""
    uc, um = used.get(node.id, (0.0, 0.0))
    used_cpu = (uc + pod.cpu_req) / node.cpu_cap
    used_mem = (um + pod.mem_req) / node.mem_cap
    return (used_cpu + used_mem) / 2.0


# --------------------------------------------------------------------------
# sequential schedulers
# --------------------------------------------------------------------------

def schedule(cluster: Cluster, pods: list[Pod], order: list[int],
             score_fn, rng=None, max_checks: Optional[int] = None) -> dict:
    """Sequentially place pods in `order` (indices into `pods`).

    Returns placement map pod.id -> node.id, placed count, and feasibility
    check count (proxy for scheduling cost).
    """
    placed: list[tuple[Pod, Node]] = []
    used: dict[str, tuple[float, float]] = {}
    checks = 0
    for idx in order:
        pod = pods[idx]
        feas = feasible_nodes(cluster, pod, placed, used)
        checks += len(cluster.nodes)
        if not feas:
            continue  # unschedulable
        if score_fn is None:  # random policy
            target = rng.choice(feas)
        else:
            target = max(feas, key=lambda n: score_fn(n, pod, used))
        placed.append((pod, target))
        uc, um = used.get(target.id, (0.0, 0.0))
        used[target.id] = (uc + pod.cpu_req, um + pod.mem_req)
    return {
        "placed": {p.id: n.id for p, n in placed},
        "n_placed": len(placed),
        "n_pods": len(pods),
        "checks": checks,
    }


def schedule_with_requeue(cluster: Cluster, pods: list[Pod], order: list[int],
                          score_fn, rng=None, max_retries: int = 100) -> dict:
    """Round-based scheduling with bounded requeueing (k8s-like).

    Unplaced pods are requeued to the next round instead of dropped, up to
    max_retries total rounds. Mirrors kube-scheduler's backoff/requeue
    behavior (without the delay: retry count + total checks proxy latency).

    Returns placed%, total checks, per-pod retry counts, and the round at
    which the last pod was placed (makespan proxy).
    """
    placed: list[tuple[Pod, Node]] = []
    used: dict[str, tuple[float, float]] = {}
    checks = 0
    retries = {p.id: 0 for p in pods}
    last_round = 0
    queue = list(order)
    for rnd in range(1, max_retries + 1):
        if not queue:
            break
        next_queue = []
        for idx in queue:
            pod = pods[idx]
            feas = feasible_nodes(cluster, pod, placed, used)
            checks += len(cluster.nodes)
            if not feas:
                retries[pod.id] += 1
                next_queue.append(idx)
                continue
            if score_fn is None:
                target = rng.choice(feas)
            else:
                target = max(feas, key=lambda n: score_fn(n, pod, used))
            placed.append((pod, target))
            uc, um = used.get(target.id, (0.0, 0.0))
            used[target.id] = (uc + pod.cpu_req, um + pod.mem_req)
            last_round = rnd
        queue = next_queue
    return {
        "placed": {p.id: n.id for p, n in placed},
        "n_placed": len(placed),
        "n_pods": len(pods),
        "checks": checks,
        "rounds": last_round,
        "max_retries": max_retries,
        "unplaced": [pods[i].id for i in queue],
        "retries": retries,
    }
