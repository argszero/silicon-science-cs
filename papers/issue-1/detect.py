"""
detect.py — Deadlock prediction on the required-affinity graph.

Builds a directed "co-location prerequisite" graph from pods' required
affinity ('In') rules: pod u -> pod v means "u requires an already-placed v
in its topology domain". In single-pass scheduling, a pod is placeable only
if its required partner is already placed (or arrives earlier); in
requeueing, progress requires at least one member of every strongly connected
component (SCC) to be placeable from outside the SCC.

Analysis:
  - If a strongly connected component of size >= 2 has NO incoming edge from
    outside the SCC (no pod outside requires any member, and no member is
    placeable without another member), the component can never be entered:
    structural deadlock. (Root SCCs with size >= 2 are the mutual-affinity
    deadlock signature.)
  - Singleton SCCs with required affinity to a later pod are order-myopia
    (recoverable by requeue) unless they are part of an unreachable root SCC.

Returns per-pod prediction: deadlock (structural, requeue cannot help) vs
recoverable (order-dependent, requeue can).
"""
from __future__ import annotations

from sim import Pod  # noqa: F401 (re-export for callers)


def _required_partners(pod: Pod) -> list[str]:
    """Labels of pods this pod requires (In rules), by label match key."""
    out = []
    for r in pod.affinities:
        if r.op == "In":
            # selector dict -> canonical key
            out.append(tuple(sorted(r.selector.items())))
    return out


def build_graph(pods: list[Pod]) -> tuple[dict, dict, dict]:
    """Nodes = canonical label keys. Edge u->v if a pod of label u requires a
    pod of label v. Returns graph (u -> set(v)), pods_by_label, label_of_pod."""
    graph: dict[tuple, set] = {}
    pods_by_label: dict[tuple, list[Pod]] = {}
    label_of_pod: dict[str, tuple] = {}
    for p in pods:
        key = tuple(sorted(p.labels.items()))
        label_of_pod[p.id] = key
        pods_by_label.setdefault(key, []).append(p)
        graph.setdefault(key, set())
    for p in pods:
        key = label_of_pod[p.id]
        for partner in _required_partners(p):
            graph.setdefault(key, set()).add(partner)
    return graph, pods_by_label, label_of_pod


def tarjan_scc(graph: dict) -> list[list]:
    """Iterative Tarjan SCC on label-key graph. Returns list of SCCs (each a
    list of label keys), in reverse topological order (sinks first)."""
    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        for w in graph.get(v, ()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in stack:
                lowlink[v] = min(lowlink[v], index[w])
        if lowlink[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                comp.append(w)
                if w == v:
                    break
            result.append(comp)

    for v in graph:
        if v not in index:
            strongconnect(v)
    return result


def predict_deadlocks(pods: list[Pod]) -> dict[str, dict]:
    """Returns {pod_id: {"deadlock": bool, "reason": str}}.

    A pod is predicted deadlocked iff its label SCC has size >= 2 and is a
    root SCC (no incoming edge from outside the SCC).
    """
    graph, pods_by_label, label_of_pod = build_graph(pods)
    sccs = tarjan_scc(graph)
    comp_of = {}
    for ci, comp in enumerate(sccs):
        for k in comp:
            comp_of[k] = ci
    # incoming edges between SCCs
    incoming: dict[int, set] = {ci: set() for ci in range(len(sccs))}
    for u, vs in graph.items():
        cu = comp_of[u]
        for v in vs:
            cv = comp_of[v]
            if cu != cv:
                incoming[cv].add(cu)
    pred = {}
    for p in pods:
        key = label_of_pod[p.id]
        ci = comp_of[key]
        comp = sccs[ci]
        if len(comp) >= 2 and not incoming[ci]:
            pred[p.id] = {"deadlock": True, "reason": f"root SCC size {len(comp)} (mutual affinity)"}
        else:
            pred[p.id] = {"deadlock": False, "reason": "no root-SCC cycle"}
    return pred


def root_scc_sizes(pods: list[Pod]) -> list[int]:
    """Diagnostic: sizes of root SCCs (for reporting)."""
    graph, _, _ = build_graph(pods)
    sccs = tarjan_scc(graph)
    comp_of = {}
    for ci, comp in enumerate(sccs):
        for k in comp:
            comp_of[k] = ci
    incoming: dict[int, set] = {ci: set() for ci in range(len(sccs))}
    for u, vs in graph.items():
        cu = comp_of[u]
        for v in vs:
            cv = comp_of[v]
            if cu != cv:
                incoming[cv].add(cu)
    return [len(sccs[ci]) for ci in incoming if not incoming[ci]]
