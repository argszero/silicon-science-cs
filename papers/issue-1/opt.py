"""
opt.py — Optimal placement ground truth (small instances).

Pure-Python backtracking over pod->node assignments. Solves the *joint*
offline placement problem (what greedy cannot see): maximize the number of
placed pods; tie-break by minimizing total used resource fraction.

Global consistency is enforced at every partial step:
  - every affinity rule of a placed pod must be satisfiable by an *already
    placed* matching pod in the same topology domain, or by a *future* pod
    that still has at least one feasible node in that domain (sound pruning:
    we only keep partial states that can still be completed).

Exhaustive search is exponential; use for small instances (<= ~8 pods,
<= ~5 nodes). Larger instances need a real ILP solver (scipy.optimize.milp
or OR-Tools) — see notes.md for the upgrade path.
"""
from __future__ import annotations

from sim import Cluster, Pod, Node, feasible_nodes


def _topo_domains(cluster: Cluster, rule) -> list[tuple[str, list[Node]]]:
    """Group nodes by topology_key value; None-valued nodes form their own group."""
    groups: dict[str, list[Node]] = {}
    for n in cluster.nodes:
        v = n.labels.get(rule.topology_key)
        key = v if v is not None else f"__none__{n.id}"
        groups.setdefault(key, []).append(n)
    return list(groups.items())


def _can_satisfy_affinity(pod: Pod, node: Node, cluster: Cluster,
                          placed: list[tuple[Pod, Node]],
                          remaining: list[Pod]) -> bool:
    """Sound pruning for 'In' rules: prune only when a matching pod literally
    cannot fit in the topology domain (neither placed nor remaining).

    'NotIn' rules are NOT pruned here (future placements may violate them);
    the final verification catches those. This keeps the search sound: we
    never prune a state that could still complete.
    """
    used_per_node: dict[str, tuple[float, float]] = {}
    for p, n in placed:
        uc, um = used_per_node.get(n.id, (0.0, 0.0))
        used_per_node[n.id] = (uc + p.cpu_req, um + p.mem_req)

    for rule in pod.affinities:
        if rule.op != "In":
            continue
        tv = node.topo_value(rule.topology_key)
        # already-placed match in domain?
        if any(rule.matches(p.labels) and n.topo_value(rule.topology_key) == tv
               for p, n in placed):
            continue
        # remaining pod with matching labels that can still fit on some domain node
        domain_nodes = [n for n in cluster.nodes if n.topo_value(rule.topology_key) == tv]
        ok = False
        for fp in remaining:
            if not rule.matches(fp.labels):
                continue
            for dn in domain_nodes:
                uc, um = used_per_node.get(dn.id, (0.0, 0.0))
                if uc + fp.cpu_req <= dn.cpu_cap + 1e-9 and um + fp.mem_req <= dn.mem_cap + 1e-9:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            return False
    return True


def _final_check(pods: list[Pod], assign: dict[int, int], nodes_by_id) -> bool:
    """Verify all constraints on a complete assignment."""
    placed = [(pods[i], nodes_by_id[nid]) for i, nid in assign.items()]
    # resources
    used_c: dict[str, float] = {}
    used_m: dict[str, float] = {}
    for p, n in placed:
        used_c[n.id] = used_c.get(n.id, 0.0) + p.cpu_req
        used_m[n.id] = used_m.get(n.id, 0.0) + p.mem_req
    for n in nodes_by_id.values():
        if used_c.get(n.id, 0.0) > n.cpu_cap + 1e-9 or used_m.get(n.id, 0.0) > n.mem_cap + 1e-9:
            return False
    # selectors
    for p, n in placed:
        if not all(n.labels.get(k) == v for k, v in p.node_selector.items()):
            return False
    # affinities (global: matches may be anywhere in the domain, order-free)
    for p, n in placed:
        for rule in p.affinities:
            tv = n.topo_value(rule.topology_key)
            matches = [q for q, m in placed
                       if rule.matches(q.labels) and m.topo_value(rule.topology_key) == tv]
            if rule.op == "In" and not matches:
                return False
            if rule.op == "NotIn" and matches:
                return False
    return True


def optimal_placement(cluster: Cluster, pods: list[Pod], node_limit: int = 500_000) -> dict:
    """Max placed pods (tie-break: min used resource fraction). Returns summary.

    node_limit caps total DFS expansions; when the cap is hit the best solution
    found so far is returned with exact=False (approximate; real ILP is the
    planned upgrade for large instances — see notes.md).
    """
    nodes = cluster.nodes
    nodes_by_id = {n.id: n for n in nodes}

    best_placed: dict[int, int] = {}
    best_frac = float("inf")
    expansions = 0
    capped = False

    def used_fraction(assign: dict[int, int]) -> float:
        uc: dict[str, float] = {}
        um: dict[str, float] = {}
        for i, nid in assign.items():
            uc[nid] = uc.get(nid, 0.0) + pods[i].cpu_req
            um[nid] = um.get(nid, 0.0) + pods[i].mem_req
        tot = 0.0
        for n in nodes:
            tot += (uc.get(n.id, 0.0) / n.cpu_cap + um.get(n.id, 0.0) / n.mem_cap) / 2.0
        return tot

    def dfs(i: int, assign: dict[int, int], placed_list: list[tuple[Pod, Node]]):
        nonlocal best_placed, best_frac, expansions, capped
        if expansions >= node_limit:
            capped = True
            return
        expansions += 1
        if i == len(pods):
            if len(assign) > len(best_placed) or (
                    len(assign) == len(best_placed) and used_fraction(assign) < best_frac):
                best_placed = dict(assign)
                best_frac = used_fraction(assign)
            return
        # prune: cannot beat best even if all remaining pods placed
        if len(assign) + (len(pods) - i) < len(best_placed):
            return
        pod = pods[i]
        remaining = pods[i + 1:]
        # option 1: leave pod unplaced
        dfs(i + 1, assign, placed_list)
        # option 2: place on a feasible node
        # per-node used resources (NOT cluster-wide)
        used_per_node: dict[str, tuple[float, float]] = {}
        for p, n in placed_list:
            uc, um = used_per_node.get(n.id, (0.0, 0.0))
            used_per_node[n.id] = (uc + p.cpu_req, um + p.mem_req)
        for node in nodes:
            uc, um = used_per_node.get(node.id, (0.0, 0.0))
            if uc + pod.cpu_req > node.cpu_cap + 1e-9:
                continue
            if um + pod.mem_req > node.mem_cap + 1e-9:
                continue
            if not all(node.labels.get(k) == v for k, v in pod.node_selector.items()):
                continue
            if not _can_satisfy_affinity(pod, node, cluster, placed_list, remaining):
                continue
            assign[i] = node.id
            placed_list.append((pod, node))
            dfs(i + 1, assign, placed_list)
            placed_list.pop()
            del assign[i]

    dfs(0, {}, [])
    # final verification of the best assignment
    ok = _final_check(pods, best_placed, nodes_by_id)
    return {
        "placed": {pods[i].id: nodes_by_id[nid].id for i, nid in best_placed.items()},
        "n_placed": len(best_placed),
        "n_pods": len(pods),
        "verified": ok,
        "exact": not capped,
    }
