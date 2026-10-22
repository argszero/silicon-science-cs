#!/usr/bin/env python3
"""depth2.py -- issue #149: does COUPLING make the minimal certificate cheaper than |M|?

THE QUESTION THIS FILE EXISTS TO ANSWER.  At depth 1 each parent names a dependency once, the
per-edge domains are independent, and the ambiguity graph is a clique, so the minimum distinguishing
key is exactly the ambiguous set: |K*| = |M|.  That identity is a consequence of the PRODUCT
structure, not a measurement -- it is the analytic null, and it means depth 1 can never show a saving.

A saving needs coupling: the same package reached from two parents with different ranges, so that one
choice can exclude another.  Then the feasible set is not a product, projections overlap, and a key
smaller than |M| becomes possible.  This file builds those graphs and decides it.

THE MODEL, stated so it can be attacked.  For one declaring version r (fixed):
  * a DEPTH-1 package is present, with the versions admissible from r's own declared range;
  * a DEPTH-2 package is present iff the DEPTH-1 version actually selected declares it, and its
    versions are those satisfying the ranges of EVERY selected parent that declares it -- this is
    where coupling enters;
  * a solution is a tuple over all packages in the closure, with the sentinel ABSENT for a package no
    selected parent declares.
Enumerating these solutions exactly is the only way to state |K*| rather than a bound, so an instance
is admitted only when its product of domains is within BUDGET and it names at most MAXPKG packages.
Everything else is COUNTED as intractable -- measured, not argued away.

FALSIFIER (fixed in results.md before this file ran): the leg closes if |K*|/|M| >= 0.95 on the median
(F1) or the exact problem is intractable at the sizes real closures reach (F2).

Usage: python3 depth2.py [--check]   (offline: reads snapshot_<eco>.json, no network, no clock)
"""
import io
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, os.pardir))
OUT = os.path.join(PKG, "depth2.json")

sys.path.insert(0, HERE)
from fetch_snapshot import parse_spec, satisfies, is_prerelease  # noqa: E402

BUDGET = 200000     # solutions enumerated per instance
MAXPKG = 12         # packages in an instance
ABSENT = "\u22a5"


def load(eco):
    return json.load(io.open(os.path.join(PKG, "snapshot_%s.json" % eco), encoding="utf-8"))


def admiss(pkg, spec, pep440):
    alts = parse_spec(spec, pep440=pep440)
    if alts is None or not pkg:
        return None
    return sorted(v for v, m in pkg["versions"].items()
                  if not m["prerelease"] and not m["yanked"] and satisfies(v, alts))


def instance(snap, dv, pep440):
    """The closure of one declaring version, or None when it is not enumerable."""
    PK = snap["packages"]
    name, ver = dv["package"], dv["version"]
    rec = (PK.get(name) or {}).get("versions", {}).get(ver)
    if not rec:
        return None
    d1 = {}
    for dep, spec in (rec.get("deps") or {}).items():
        a = admiss(PK.get(dep), spec, pep440)
        if a:
            d1[dep] = a
    if not d1:
        return None
    prod = 1
    for a in d1.values():
        prod *= len(a)
    if len(d1) > MAXPKG:
        return None
    # depth-2 packages: everything any admissible depth-1 version declares
    d2 = {}
    for dep, avail in d1.items():
        for v in avail:
            for d2name, spec in ((PK[dep]["versions"].get(v) or {}).get("deps") or {}).items():
                if d2name in PK and d2name not in d1:
                    d2.setdefault(d2name, set()).add((dep, v, spec))
    if len(d1) + len(d2) > MAXPKG:
        return None
    return {"declaring": "%s@%s" % (name, ver), "d1": d1, "d2": d2, "product": prod}


def enumerate_solutions(inst, snap, pep440, budget=BUDGET):
    """Every solution of the declaration: depth-1 assignments x the depth-2 sets they induce."""
    PK = snap["packages"]
    d1, d2 = inst["d1"], inst["d2"]
    names = sorted(d1) + sorted(d2)
    sols, truncated = [], False
    for combo in itertools.product(*[d1[k] for k in sorted(d1)]):
        chosen = dict(zip(sorted(d1), combo))
        allow = {}
        ok = True
        for n2, parents in d2.items():
            living = [(p, v, s) for (p, v, s) in parents if chosen.get(p) == v]
            if not living:
                allow[n2] = [ABSENT]
                continue
            sets = []
            for (p, v, s) in living:
                a = admiss(PK.get(n2), s, pep440)
                if a is None:
                    ok = False
                    break
                sets.append(set(a))
            if not ok:
                break
            common = set.intersection(*sets) if sets else set()
            if not common:
                ok = False            # the choice is infeasible: coupling binds here
                break
            allow[n2] = sorted(common)
        if not ok:
            continue
        for combo2 in itertools.product(*[allow[k] for k in sorted(allow)]):
            sols.append(tuple(chosen[k] for k in sorted(d1)) + tuple(combo2))
            if len(sols) > budget:
                truncated = True
                break
        if truncated:
            break
    return names, sols, truncated


def projections(names, sols):
    out = []
    for i in range(len(names)):
        out.append(set(s[i] for s in sols))
    return out


def min_key(names, sols, cap=MAXPKG):
    """The exact minimum distinguishing key, by exhaustive search over subsets."""
    idx = list(range(len(names)))
    for size in range(0, len(names) + 1):
        for sub in itertools.combinations(idx, size):
            seen = set()
            good = True
            for s in sols:
                proj = tuple(s[i] for i in sub)
                if proj in seen:
                    good = False
                    break
                seen.add(proj)
            if good:
                return len(sub)
    return len(names)


def vertex_cover(names, sols):
    """Minimum vertex cover of the ambiguity graph: pairs of solutions differing at exactly two
    coordinates.  This is the registration's bound, computed on the depth-2 graphs so it can be shown
    to be either right or a decoration."""
    idx = {n: i for i, n in enumerate(names)}
    edges = set()
    for a, b in itertools.combinations(sols, 2):
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(diff) == 2:
            edges.add(tuple(sorted(diff)))
    vs = sorted({i for e in edges for i in e})
    for size in range(0, len(vs) + 1):
        for sub in itertools.combinations(vs, size):
            cov = set(sub)
            if all(u in cov or w in cov for (u, w) in edges):
                return size, len(edges)
    return len(vs), len(edges)


def analyse(eco):
    snap = load(eco)
    pep440 = (eco == "pypi")
    rows, skipped_size, skipped_trunc, skipped_none = [], 0, 0, 0
    for dv in snap["declaring"]:
        inst = instance(snap, dv, pep440)
        if inst is None:
            skipped_size += 1
            continue
        names, sols, truncated = enumerate_solutions(inst, snap, pep440)
        if truncated:
            skipped_trunc += 1
            continue
        if not sols:
            skipped_none += 1
            continue
        proj = projections(names, sols)
        M = [n for n, p in zip(names, proj) if len(p) > 1]
        k = min_key(names, sols)
        tau, nedges = vertex_cover(names, sols)
        rows.append({"declaring": inst["declaring"], "packages": len(names),
                     "solutions": len(sols), "M": len(M), "K": k,
                     "ratio": (float(k) / len(M)) if M else None,
                     "vertex_cover": tau, "ambiguity_edges": nedges,
                     "cover_would_be": len(M) - 1 if M else None,
                     "pins_pin_everything": len(names),
                     "pins_direct_only": len(inst["d1"])})
    return rows, {"not_enumerable_at_depth1": skipped_size,
                  "enumeration_truncated": skipped_trunc,
                  "no_feasible_solution": skipped_none}


def summarise(eco):
    rows, skipped = analyse(eco)
    ratios = sorted(r["ratio"] for r in rows if r["ratio"] is not None)
    saved = [r for r in rows if r["ratio"] is not None and r["ratio"] < 1.0]
    cover_attained = [r for r in rows if r["vertex_cover"] == r["K"]]
    M_total = sum(r["M"] for r in rows)
    K_total = sum(r["K"] for r in rows)
    return {
        "ecosystem": eco,
        "instances": len(rows),
        "skipped": skipped,
        "median_ratio": ratios[len(ratios) // 2] if ratios else None,
        "instances_with_a_saving": len(saved),
        "instances_with_a_saving_share": (float(len(saved)) / len(rows)) if rows else None,
        "pooled_ratio": (float(K_total) / M_total) if M_total else None,
        "pooled_M": M_total, "pooled_K": K_total,
        "vertex_cover_equals_K": len(cover_attained),
        "ratio_histogram": {"1.0": sum(1 for r in ratios if r >= 0.999),
                            "<1.0": sum(1 for r in ratios if r < 0.999),
                            "<0.75": sum(1 for r in ratios if r < 0.75),
                            "<0.5": sum(1 for r in ratios if r < 0.5)},
        "baselines": {
            "pins_pin_everything": sum(r["pins_pin_everything"] for r in rows),
            "pins_direct_only": sum(r["pins_direct_only"] for r in rows),
            "pins_certificate": K_total,
        },
        "rows": rows,
    }


def check():
    """Known-answer plants: a coupling-free closure must give ratio 1, a coupling-built one must not."""
    ok = True
    # a closure with NO coupling: two independent leaves, two versions each -> K must be 2 = |M|
    fake = {"packages": {
        "root": {"versions": {"1.0.0": {"published_at": "t", "deps": {"a": "^1.0.0", "b": "^1.0.0"},
                                        "prerelease": False, "yanked": False}}},
        "a": {"versions": {"1.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False},
                           "1.0.1": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False}}},
        "b": {"versions": {"1.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False},
                           "1.0.1": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False}}}}}
    inst = instance(fake, {"package": "root", "version": "1.0.0"}, False)
    names, sols, _ = enumerate_solutions(inst, fake, False)
    proj = projections(names, sols)
    M = [n for n, p in zip(names, proj) if len(p) > 1]
    k = min_key(names, sols)
    good = len(M) == 2 and k == 2
    print("  plant no coupling -> |K*| = |M| = 2                  %s (M=%d K=%d)"
          % ("OK" if good else "FAILED", len(M), k))
    ok &= good

    # a closure WITH coupling: c's range is FIXED BY a's choice, so c is ambiguous yet determined by
    # a -- the only mechanism that makes a key cheaper than the ambiguous set.  The first version of
    # this plant modelled coupling that merely KILLS a branch, which leaves M=1 and cannot show a
    # saving at all; that distinction is the point of the plant, so it is recorded here.
    coup = {"packages": {
        "root": {"versions": {"1.0.0": {"published_at": "t", "deps": {"a": "^1.0.0"},
                                        "prerelease": False, "yanked": False}}},
        "a": {"versions": {"1.0.0": {"published_at": "t", "deps": {"c": "1.0.0"},
                                     "prerelease": False, "yanked": False},
                           "1.1.0": {"published_at": "t", "deps": {"c": "2.0.0"},
                                     "prerelease": False, "yanked": False}}},
        "c": {"versions": {"1.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False},
                           "2.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False}}}}}
    inst = instance(coup, {"package": "root", "version": "1.0.0"}, False)
    names, sols, _ = enumerate_solutions(inst, coup, False)
    proj = projections(names, sols)
    M = [n for n, p in zip(names, proj) if len(p) > 1]
    k = min_key(names, sols)
    good2 = len(M) == 2 and k == 1
    print("  plant functional dependence -> |K*| < |M|         %s (M=%d K=%d sols=%d)"
          % ("OK" if good2 else "FAILED", len(M), k, len(sols)))
    ok &= good2

    # and the negative control for THAT: two independent ambiguous leaves must still cost 2
    good3 = True
    for nm, sc in (("free leaves", fake),):
        it = instance(sc, {"package": "root", "version": "1.0.0"}, False)
        n2, s2, _ = enumerate_solutions(it, sc, False)
        p2 = projections(n2, s2)
        M2 = [n for n, pp in zip(n2, p2) if len(pp) > 1]
        k2 = min_key(n2, s2)
        good3 = (k2 == len(M2) == 2)
        print("  control no dependence -> |K*| = |M|                %s (M=%d K=%d)"
              % ("OK" if good3 else "FAILED", len(M2), k2))
    ok &= good3

    print("PLANTS: %s" % ("ALL PASS" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    if "--check" in sys.argv:
        return check()
    out = {"falsifier": {"F1_median_ratio_ge": 0.95, "F1_saving_share_lt": 0.25,
                         "F2": "exact enumeration intractable at real closure sizes"},
           "model": "depth-1 domains from the root's ranges; a depth-2 package is present iff a "
                    "selected parent declares it, and must satisfy every selected parent's range",
           "ecosystems": {}}
    for eco in ("npm", "pypi"):
        s = summarise(eco)
        out["ecosystems"][eco] = s
        print("== %s: %d instances enumerable exactly" % (eco, s["instances"]))
        print("   skipped: %s" % s["skipped"])
        print("   |K*|/|M|: median %s | pooled %s (K=%d / M=%d)"
              % (s["median_ratio"], s["pooled_ratio"], s["pooled_K"], s["pooled_M"]))
        print("   instances with a saving below 1.0: %d/%d = %s"
              % (s["instances_with_a_saving"], s["instances"],
                 s["instances_with_a_saving_share"]))
        print("   ratio histogram beyond 1.0: %s" % s["ratio_histogram"])
        print("   vertex cover == K*: %d/%d instances" % (s["vertex_cover_equals_K"], s["instances"]))
        print("   pins: pin-everything %d | pin-direct-only %d | certificate %d"
              % (s["baselines"]["pins_pin_everything"], s["baselines"]["pins_direct_only"],
                 s["baselines"]["pins_certificate"]))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
