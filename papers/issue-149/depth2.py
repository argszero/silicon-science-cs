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
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE  # the package directory holds the snapshot AND the artifact. HERE/.. read
# papers/ and found nothing, so the committed scripts could not reproduce the committed
# numbers on a clean checkout. A reproduction path that depends on a directory the package
# does not own is not a reproduction path.
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


def ambiguity_edges_fast(nsols):
    """Edge set of the ambiguity graph in O(n * k^2), without enumerating solution PAIRS.

    Two solutions differ at exactly {i, j} iff they agree on every other coordinate AND disagree at
    BOTH i and j.  So for each coordinate pair (i, j), group the solutions by their projection onto
    the other coordinates; (i, j) is an edge iff some group holds two entries differing on both axes.

    The first version of this function tested only that the group held two DIFFERENT (i, j) values,
    which also fires when the two entries differ on one axis alone -- i.e. on a one-coordinate
    difference, which is not an edge at all.  Over a 40-case random comparison against the pair
    definition it reported 4 spurious edges out of 10, and the plant below caught it; the condition is
    now >=2 distinct values on EACH axis.

    The naive form -- itertools.combinations(sols, 2) -- produces the same set at O(n^2): at the
    budget of 200 000 solutions per instance that is ~2e10 pairs, which is why a full run could not
    terminate. The set is identical, so this changes the cost of the measurement, not its value.
    """
    k = len(nsols[0]) if nsols else 0
    edges = set()
    for i in range(k):
        for j in range(i + 1, k):
            rest = [c for c in range(k) if c != i and c != j]
            xs, ys = {}, {}
            for row in nsols:
                key = tuple(row[c] for c in rest)
                xs.setdefault(key, set()).add(row[i])
                ys.setdefault(key, set()).add(row[j])
                if len(xs[key]) >= 2 and len(ys[key]) >= 2:
                    edges.add((i, j))
                    break
    return edges


def ambiguity_edges_naive(nsols):
    """The original O(n^2) definition, kept as the oracle the fast form is tested against."""
    edges = set()
    for a, b in itertools.combinations(nsols, 2):
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(diff) == 2:
            edges.add(tuple(sorted(diff)))
    return edges


def vertex_cover(names, sols):
    """Minimum vertex cover of the ambiguity graph: pairs of solutions differing at exactly two
    coordinates -- the registration's bound, computed on real depth-2 graphs so it can be shown to be
    either right or a decoration.  Edges come from ambiguity_edges_fast; the pair definition lives on
    in ambiguity_edges_naive as the oracle its plant compares against."""
    idx = {n: i for i, n in enumerate(names)}
    edges = ambiguity_edges_fast(sols)
    vs = sorted({i for e in edges for i in e})
    for size in range(0, len(vs) + 1):
        for sub in itertools.combinations(vs, size):
            cov = set(sub)
            if all(u in cov or w in cov for (u, w) in edges):
                return size, len(edges)
    return len(vs), len(edges)


def determiners(names, sols, proj, parents=None, sol_cap=5000):
    """For every ambiguous coordinate, the smallest set of OTHER coordinates that determines it.

    This measures the lemma's own hypothesis instead of assuming it. The lower-bound step of the
    §3.1 lemma reads "for each p in M there exist two solutions that differ only at p"; that holds
    exactly when no coordinate is a FUNCTION of the others. Two solutions agreeing on a set S and
    disagreeing on q are a witness that S does not determine q, so the test is injectivity of the
    projection onto S, read backwards.

    Candidate determiners are the coordinates that can structurally be one. A depth-2 package's
    domain is derived from the versions of the packages that declare it, so only those can determine
    it. A depth-1 package is CHOSEN, but that does not make it undetermined: where a child is a
    bijective relabeling of its parent, the child determines the parent too, and the plant below
    caught exactly that in the first version of this function, which had restricted depth-1
    candidates to the other depth-1 packages. So a depth-1 coordinate's candidates are every other
    coordinate. Above `sol_cap` solutions the depth-2 restriction is used and the instance is marked
    as not exhaustively searched; below it, every other coordinate is a candidate either way.

    A coordinate with no determiner is reported as NOT ESTABLISHED at the depth searched, never as
    independent: the search stops at |S| = 1, so absence of a determiner is absence of evidence for
    any higher-order dependence.
    """
    amb = [i for i, p in enumerate(proj) if len(p) > 1]
    children = set((parents or {}).keys())
    out, exhaustive = {}, True
    for q in amb:
        if parents is not None and len(sols) > sol_cap and names[q] in children:
            cands = [j for j in range(len(names)) if names[j] in (parents.get(names[q]) or ())]
            exhaustive = False
        else:
            cands = [j for j in range(len(names)) if j != q]
        found = None
        for j in cands:
            seen, ok = {}, True
            for s in sols:
                vj, vq = s[j], s[q]
                prev = seen.get(vj)
                if prev is None:
                    seen[vj] = vq
                elif prev != vq:
                    ok = False
                    break
            if ok:
                found = [names[j]]
                break
        out[names[q]] = found
    return out, exhaustive


def wilson(k, n, z=1.96):
    """95 % Wilson interval, the same form ambiguous.py uses for every other rate in this package."""
    if n == 0:
        return None
    p = float(k) / n
    den = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def worked_example(eco, declaring):
    """Print one compressing instance from its own solution set, so the mechanism is read, not argued."""
    snap = load(eco)
    pep440 = (eco == "pypi")
    name, ver = declaring.rsplit("@", 1)
    inst = instance(snap, {"package": name, "version": ver}, pep440)
    if inst is None:
        return
    names, sols, _ = enumerate_solutions(inst, snap, pep440)
    proj = projections(names, sols)
    det, _ = determiners(names, sols, proj)
    print("\n   worked example %s: %d solutions over %d packages" % (declaring, len(sols), len(names)))
    for n, p in zip(names, proj):
        by = det.get(n)
        print("     %-20s |domain|=%-3d %s" % (n, len(p),
              ("determined by %s" % ", ".join(by)) if by else ""))
    for child, parents in sorted(inst["d2"].items()):
        rows = sorted(parents)
        print("     %s is declared by %d parent version(s); first six:" % (child, len(rows)))
        for (p, v, sp) in rows[:6]:
            print("       %s@%s declares %s %r -> admits %s"
                  % (p, v, child, sp, admiss(snap["packages"].get(child), sp, pep440)))


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
        det, exhaustive = determiners(names, sols, proj,
                                      parents={k: {p[0] for p in v} for k, v in inst["d2"].items()})
        rows.append({"declaring": inst["declaring"], "packages": len(names),
                     "solutions": len(sols), "M": len(M), "K": k,
                     "ratio": (float(k) / len(M)) if M else None,
                     "vertex_cover": tau, "ambiguity_edges": nedges,
                     "cover_would_be": len(M) - 1 if M else None,
                     "pins_pin_everything": len(names),
                     "pins_direct_only": len(inst["d1"]),
                     # the lemma's hypothesis, measured on this instance rather than assumed:
                     # which ambiguous coordinates are a FUNCTION of others, and by how much the
                     # certificate is cheaper than |M| because of it
                     "saving": len(M) - k,
                     "determined": {q: by for q, by in det.items() if by},
                     "dependence_search_exhaustive": exhaustive})
    return rows, {"not_enumerable_at_depth1": skipped_size,
                  "enumeration_truncated": skipped_trunc,
                  "no_feasible_solution": skipped_none}


def summarise(eco):
    rows, skipped = analyse(eco)
    ratios = sorted(r["ratio"] for r in rows if r["ratio"] is not None)
    saved = [r for r in rows if r["ratio"] is not None and r["ratio"] < 1.0]
    # A cover equal to |K*| is a real attainment only where there is something to cover: at M = 0
    # the equality is 0 = 0. The first version counted those 120 degenerate instances as attainments
    # and printed "vertex cover == K*: 134/292", which a reader takes as "the bound is attained
    # 134 times" while the prose said it never is. Both readings are wrong; the split is the fix.
    cover_all = [r for r in rows if r["vertex_cover"] == r["K"]]
    cover_nonempty = [r for r in rows if r["M"] > 0 and r["vertex_cover"] == r["K"]]
    M_total = sum(r["M"] for r in rows)
    K_total = sum(r["K"] for r in rows)
    # ---- the lemma's hypothesis, measured: exceptions to |K*| = |M|, and whether functional
    # dependence is present in exactly those instances (both directions, so the detector cannot
    # merely be firing everywhere)
    with_edges = [r for r in rows if r["M"] > 0]
    exc = [r for r in with_edges if r["K"] < r["M"]]
    det_among_exc = [r for r in exc if r["determined"]]
    det_among_clean = [r for r in with_edges if r["K"] == r["M"] and r["determined"]]
    clean = [r for r in rows if r not in exc]
    saving_hist = {}
    for r in exc:
        saving_hist[str(r["saving"])] = saving_hist.get(str(r["saving"]), 0) + 1
    b_all = sum(r["pins_pin_everything"] for r in rows)
    b_clean = sum(r["pins_pin_everything"] for r in clean)
    price_all = (float(K_total) / b_all) if b_all else None
    price_clean = (float(sum(r["K"] for r in clean)) / b_clean) if b_clean else None
    return {
        "ecosystem": eco,
        # the difference the tail makes to the price, in percentage points: a derived number the
        # prose prints, so the artifact owns it rather than the sentence computing it
        "price_delta_points": (round(100.0 * (price_all - price_clean), 1)
                               if price_all is not None and price_clean is not None else None),
        "snapshot_content_sha256": load(eco).get("content_sha256"),
        "instances": len(rows),
        "skipped": skipped,
        "median_ratio": ratios[len(ratios) // 2] if ratios else None,
        "instances_with_a_saving": len(saved),
        "instances_with_a_saving_share": (float(len(saved)) / len(rows)) if rows else None,
        "pooled_ratio": (float(K_total) / M_total) if M_total else None,
        "pooled_M": M_total, "pooled_K": K_total,
        "vertex_cover_equals_K": len(cover_all),
        "vertex_cover_equals_K_all": len(cover_all),
        "vertex_cover_equals_K_with_ambiguous_edges": len(cover_nonempty),
        "vertex_cover_equals_K_degenerate": len(cover_all) - len(cover_nonempty),
        "ratio_histogram": {"1.0": sum(1 for r in ratios if r >= 0.999),
                            "<1.0": sum(1 for r in ratios if r < 0.999),
                            "<0.75": sum(1 for r in ratios if r < 0.75),
                            "<0.5": sum(1 for r in ratios if r < 0.5)},
        "exceptions": {
            "instances_with_an_ambiguous_edge": len(with_edges),
            "instances_below_one_ratio": len(exc),
            "rate": (float(len(exc)) / len(with_edges)) if with_edges else None,
            "wilson95": wilson(len(exc), len(with_edges)),
            "distinct_declaring_roots": len({r["declaring"].rsplit("@", 1)[0] for r in exc}),
            "declaring_roots": sorted({r["declaring"].rsplit("@", 1)[0] for r in exc}),
            "max_saving": max([r["saving"] for r in exc], default=0),
            "saving_histogram": saving_hist,
            "with_a_measured_functional_determiner": len(det_among_exc),
            "without_a_measured_functional_determiner": len(exc) - len(det_among_exc),
            "unexplained": sorted(r["declaring"] for r in exc if not r["determined"]),
            # the other direction: a determiner present in an instance that still needs |M| records
            # would mean the detector explains something else, so it is counted, not assumed empty
            "determiner_but_no_saving": len(det_among_clean),
            "determiner_but_no_saving_instances": sorted(r["declaring"] for r in det_among_clean),
        },
        "baselines": {
            "pins_pin_everything": sum(r["pins_pin_everything"] for r in rows),
            "pins_direct_only": sum(r["pins_direct_only"] for r in rows),
            "pins_certificate": K_total,
        },
        # the same price over the population the lemma actually covers, so a pooled figure can say
        # whether its tail is inside it
        "baselines_excluding_exceptions": {
            "instances": len(clean),
            "pins_pin_everything": sum(r["pins_pin_everything"] for r in clean),
            "pins_direct_only": sum(r["pins_direct_only"] for r in clean),
            "pins_certificate": sum(r["K"] for r in clean),
            "pooled_M": sum(r["M"] for r in clean),
        },
        "rows": rows,
    }


def check():
    """Known-answer plants: a coupling-free closure must give ratio 1, a coupling-built one must not."""
    seen = []

    def plant(label, good, extra=""):
        print("  %-56s %s%s" % (label, "OK" if good else "FAILED", extra))
        seen.append(bool(good))
        return good

    # a closure with NO coupling: two independent leaves, two versions each -> K must be 2 = |M|
    fake = {"packages": {
        "root": {"versions": {"1.0.0": {"published_at": "t", "deps": {"a": "^1.0.0", "b": "^1.0.0"},
                                        "prerelease": False, "yanked": False}}},
        "a": {"versions": {"1.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False},
                           "1.0.1": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False}}},
        "b": {"versions": {"1.0.0": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False},
                           "1.0.1": {"published_at": "t", "deps": {}, "prerelease": False, "yanked": False}}}}}
    # The O(n*k^2) rewrite must produce the SAME SET as the O(n^2) definition. A rewrite that drops
    # edges would report a smaller cover and make the registration's bound look attained.
    import random as _r
    _r.seed(11)
    agree = True
    for _trial in range(40):
        kk = _r.randint(2, 5)
        # n distinct tuples cannot exceed the space 2^kk: asking for 12 distinct pairs over a
        # 2-letter alphabet is 4 points, and the generator then never terminates. The first version
        # of this guard hung the whole plant run on exactly that.
        nn = min(_r.randint(2, 12), 2 ** kk)
        pts = set()
        while len(pts) < nn:
            pts.add(tuple(_r.choice("ab") for _ in range(kk)))
        pts = sorted(pts)
        if ambiguity_edges_fast(pts) != ambiguity_edges_naive(pts):
            agree = False
            break
    plant("plant fast ambiguity edges == naive pairs (40 random)", agree)
    # and a case that MUST have an edge, so agreement is not vacuous agreement on two empty sets
    plant("plant two solutions differing at two coords IS an edge",
          ambiguity_edges_fast([("1", "0", "0"), ("0", "1", "0")]) == {(0, 1)})

    inst = instance(fake, {"package": "root", "version": "1.0.0"}, False)
    names, sols, _ = enumerate_solutions(inst, fake, False)
    proj = projections(names, sols)
    M = [n for n, p in zip(names, proj) if len(p) > 1]
    k = min_key(names, sols)
    plant("plant no coupling -> |K*| = |M| = 2", len(M) == 2 and k == 2, " (M=%d K=%d)" % (len(M), k))

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
    plant("plant functional dependence -> |K*| < |M|", len(M) == 2 and k == 1,
          " (M=%d K=%d sols=%d)" % (len(M), k, len(sols)))

    # and the negative control for THAT: two independent ambiguous leaves must still cost 2
    it = instance(fake, {"package": "root", "version": "1.0.0"}, False)
    n2, s2, _ = enumerate_solutions(it, fake, False)
    p2 = projections(n2, s2)
    M2 = [n for n, pp in zip(n2, p2) if len(pp) > 1]
    plant("control no dependence -> |K*| = |M|", min_key(n2, s2) == len(M2) == 2,
          " (M=%d K=%d)" % (len(M2), min_key(n2, s2)))

    # THE LEMMA'S HYPOTHESIS IS NOW A MEASUREMENT, so its instrument is planted in both directions:
    # it must name c as a function of a in the coupling closure, and it must find NO determiner in
    # the independent one. A detector that fires everywhere would "explain" the 34 exceptions while
    # explaining nothing, which is the failure mode this pair exists to exclude.
    dc, _ = determiners(names, sols, proj)
    # The coupling closure is a BIJECTION -- a=1.0.0 <-> c=1.0.0, a=1.1.0 <-> c=2.0.0 -- so each
    # coordinate determines the other and one record covers both. Asserting only "c is determined by
    # a" is what failed the first version of this plant, and the failure was the truth: dependence
    # here is symmetric.
    fires = dc.get("c") == ["a"] and dc.get("a") == ["c"]
    plant("plant determiner detector fires both ways on the bijection", fires, " (%s)" % dc)
    dn, _ = determiners(n2, s2, p2)
    silent = not any(v for v in dn.values())
    plant("control determiner detector silent on the independent closure", silent, " (%s)" % dn)

    print("PLANTS: %d/%d %s" % (sum(1 for x in seen if x), len(seen),
                               "ALL PASS" if all(seen) else "FAILED"))
    return 0 if all(seen) else 1


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
        # Two numbers, two labels: the equality is 0 = 0 wherever there is nothing to cover, so a
        # single "cover == K*" count reads as an attainment count while holding 120 degeneracies.
        print("   vertex cover == K*: %d/%d (with an ambiguous edge: %d; degenerate M=0: %d)"
              % (s["vertex_cover_equals_K_with_ambiguous_edges"] + s["vertex_cover_equals_K_degenerate"],
                 s["instances"], s["vertex_cover_equals_K_with_ambiguous_edges"],
                 s["vertex_cover_equals_K_degenerate"]))
        e = s["exceptions"]
        print("   EXCEPTIONS to |K*| = |M|: %d/%d instances with an ambiguous edge = %s [%s]"
              % (e["instances_below_one_ratio"], e["instances_with_an_ambiguous_edge"],
                 ("%.4f" % e["rate"]) if e["rate"] is not None else "n/a",
                 ", ".join("%.4f" % x for x in e["wilson95"]) if e["wilson95"] else "n/a"))
        print("     from %d distinct declaring roots; max saving %d per instance; histogram %s"
              % (e["distinct_declaring_roots"], e["max_saving"], e["saving_histogram"]))
        print("     with a measured functional determiner: %d | without: %d %s"
              % (e["with_a_measured_functional_determiner"],
                 e["without_a_measured_functional_determiner"],
                 ("(unexplained: %s)" % ", ".join(e["unexplained"])) if e["unexplained"] else ""))
        print("     determiner present but NO saving (detector over-firing?): %d"
              % e["determiner_but_no_saving"])
        b2 = s["baselines_excluding_exceptions"]
        if b2["pins_pin_everything"]:
            print("   price, exceptions included : %d/%d certificates/pins = %.4f"
                  % (s["baselines"]["pins_certificate"], s["baselines"]["pins_pin_everything"],
                     float(s["baselines"]["pins_certificate"]) / s["baselines"]["pins_pin_everything"]))
            print("   price, exceptions excluded : %d/%d certificates/pins = %.4f over %d instances"
                  % (b2["pins_certificate"], b2["pins_pin_everything"],
                     float(b2["pins_certificate"]) / b2["pins_pin_everything"], b2["instances"]))
        print("   pins: pin-everything %d | pin-direct-only %d | certificate %d"
              % (s["baselines"]["pins_pin_everything"], s["baselines"]["pins_direct_only"],
                 s["baselines"]["pins_certificate"]))
    worked_example("npm", "accepts@1.3.4")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
