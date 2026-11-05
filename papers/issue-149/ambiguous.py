#!/usr/bin/env python3
"""ambiguous.py -- issue #149: what a declaration leaves open, measured from the pinned snapshot.

WHAT THIS COMPUTES, and what it deliberately does not.  The obvious number -- "share of declared
edges that admit more than one published version" -- is NOT the finding: caret and tilde ranges admit
patches BY DESIGN, so that number reports how ranges are written, and a reviewer who says so is right.
The estimand here is the DISPERSION of the solution set:

  (1) how many distinct direct installs one declaration admits        |S| = prod_e |A(e,t)|
  (2) the load-bearing one: for an edge with |A| >= 2, do the ALTERNATIVES' own declared dependency
      sets differ?  If version x and version y of `d` bring different dependencies, the choice changes
      the CLOSURE, not just a version string -- which is what survives the "ranges are meant to
      float" objection, because it says what floating costs;
  (3) the two baselines on the same graphs: pin-everything and pin-direct-only, as COSTS (packages
      pinned) rather than as install counts, so they are commensurable with the certificate size;
  (4) growth: the same declaration read at its own publication instant and at the snapshot's last
      instant, which is where the monotonicity lemma is tested rather than assumed -- including its
      exception, counted (yanked versions) and not argued away.

WHY THE AS-OF INSTANT MATTERS.  Every admissible set is read `as of` the declaring version's own
publication time.  A rate read off today's registry answers a different question (what an install
resolves to now) and would make the paper's claim about the wrong moment.

OFFLINE.  This file reads `snapshot_<eco>.json` and nothing else; no network, no clock.  Two runs on
one snapshot are byte-identical, which is what lets `reproduce.sh` compare them.

Usage: python3 ambiguous.py [--check]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE  # the package directory holds the snapshot AND the artifact. HERE/.. read
# papers/ and found nothing, so the committed scripts could not reproduce the committed
# numbers on a clean checkout. A reproduction path that depends on a directory the package
# does not own is not a reproduction path.
OUT = os.path.join(PKG, "rates.json")

sys.path.insert(0, HERE)
from fetch_snapshot import parse_spec, satisfies, vtuple, is_prerelease  # noqa: E402  (pure functions)


def load(eco):
    path = os.path.join(PKG, "snapshot_%s.json" % eco)
    return json.load(io.open(path, encoding="utf-8"))


def wilson(k, n, z=1.96):
    """A proportion with its interval.  k/n = 0 is an UPPER BOUND, never a zero."""
    if n == 0:
        return None
    p = float(k) / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, centre - half), min(1.0, centre + half)]


def admissible(pkg, spec, as_of, pep440):
    """The versions a declaration leaves available at an instant, and why each was excluded.

    A package that is NOT IN THE SNAPSHOT returns None, never an empty set.  The first version of this
    function read a missing package as "no admissible versions", which is absence read as a
    measurement: when the depth-2 fetch added those packages, the published rate moved (npm 12.8 ->
    14.3%, PyPI 80.1 -> 93.4%) with no change in what any declaration says.  That movement is the
    defect's own signature, and it is why the count is printed beside the rate.
    """
    if not pkg:
        return None, {"unparsed": True, "reason": "package not in snapshot"}
    alts = parse_spec(spec, pep440=pep440)
    if alts is None:
        return None, {"unparsed": True}
    out, prerelease, yanked, later, unsatisfied = [], 0, 0, 0, 0
    for v, m in (pkg or {}).get("versions", {}).items():
        if m.get("prerelease") or is_prerelease(v):
            prerelease += 1
            continue
        if m.get("yanked"):
            yanked += 1
            continue
        if as_of is not None and m["published_at"] > as_of:
            later += 1
            continue
        if not satisfies(v, alts):
            unsatisfied += 1
            continue
        out.append(v)
    return sorted(out), {"unparsed": False, "prerelease": prerelease, "yanked": yanked,
                         "published_later": later, "not_matching": unsatisfied}


def depset(pkg, version, with_specs=True):
    """What a version declares -- the observable the closure measure turns on.

    Two grades, because they mean different things and merging them would overstate the finding:
      * the NAMES (with_specs=False): a package appears or disappears, so the closure changes shape;
      * the name -> range MAPPING (with_specs=True): the same packages are named but an alternative
        constrains them differently, so the closure can resolve to different versions.
    The mapping test is the conservative one -- it counts a difference the downstream resolver MAY
    realise, not one it will.  None means the record is absent from the snapshot: reported, never
    read as 'declares nothing'.
    """
    m = ((pkg or {}).get("versions") or {}).get(version)
    if m is None:
        return None
    d = m.get("deps")
    if d is None:
        return None
    return frozenset(d.items()) if with_specs else frozenset(d.keys())


def analyse(eco):
    snap = load(eco)
    pep440 = (eco == "pypi")
    packages = snap["packages"]
    now = max((m["published_at"] for p in packages.values() for m in p["versions"].values()),
              default=None)
    rows, edge_rows = [], []
    for dv in snap["declaring"]:
        name, ver = dv["package"], dv["version"]
        rec = (packages.get(name) or {}).get("versions", {}).get(ver)
        if rec is None:
            continue
        t = rec["published_at"]
        deps = rec.get("deps") or {}
        edges, unparsed, amb, amb_differ, amb_shape, amb_unknown = 0, 0, 0, 0, 0, 0
        unknown_pkg = 0
        prod_asof, prod_now = 1, 1
        grew_edges = 0
        for dep, spec in sorted(deps.items()):
            a_asof, why = admissible(packages.get(dep), spec, t, pep440)
            if a_asof is None:
                unparsed += 1
                if (why or {}).get("reason") == "package not in snapshot":
                    unknown_pkg += 1
                continue
            a_now, _ = admissible(packages.get(dep), spec, None, pep440)
            edges += 1
            prod_asof *= max(1, len(a_asof))
            prod_now *= max(1, len(a_now or []))
            if len(a_asof) >= 2:
                amb += 1
                # THE LOAD-BEARING MEASURE: do the alternatives bring different dependencies?
                maps = [depset(packages.get(dep), v, with_specs=True) for v in a_asof]
                names = [depset(packages.get(dep), v, with_specs=False) for v in a_asof]
                known = [x for x in maps if x is not None]
                known_n = [x for x in names if x is not None]
                if len(known) < 2 or len(known_n) < 2:
                    amb_unknown += 1
                else:
                    if len(set(known_n)) > 1:
                        amb_shape += 1          # a dependency is added or removed
                    if len(set(known)) > 1:
                        amb_differ += 1         # the same names, constrained differently
                edge_rows.append({"declaring": "%s@%s" % (name, ver), "dep": dep, "spec": spec,
                                  "as_of": len(a_asof),
                                  "closure_differs": (None if len(known) < 2
                                                      else len(set(known)) > 1)})
            if len(a_now or []) > len(a_asof):
                grew_edges += 1
        rows.append({"declaring": "%s@%s" % (name, ver), "package": name,
                         "published_at": t, "edges": edges, "unparsed": unparsed,
                         "unknown_pkg": unknown_pkg,
                         "ambiguous": amb, "differ": amb_differ, "shape": amb_shape,
                         "unknown": amb_unknown,
                     "installs_asof": prod_asof, "installs_now": prod_now,
                     "grew_edges": grew_edges})
    return snap, now, rows, edge_rows



def certificate_check(eco, max_edges=8, max_solutions=6000):
    """Is the minimal distinguishing key computable at real sizes?  Answered by BRUTE FORCE here.

    THE CLAIM.  For one declaration, write the ambiguous edges as the set M (|A| >= 2) and the rest as
    determined.  Then the minimum key is exactly |K*| = |M|:
      * LOWER bound -- for p in M there are two solutions differing only at p, and any record that
        determines the install must distinguish them, so p must be in K.  Hence |K| >= |M|.
      * UPPER bound -- recording the version of every p in M leaves every remaining domain a
        singleton, so the install is determined.  Hence |K| <= |M|.
    The vertex-cover bound argued for in the registration is VALID BUT NOT ATTAINED on this structure:
    the ambiguity graph of an independent product is a clique, whose cover is |M|-1, and no cover of
    size |M|-1 can determine the install.  That correction is the reason this function exists.

    What brute force adds: the claim is checked against exhaustive search on every declaration small
    enough to enumerate, so "computable" is a measurement on this data rather than an assertion.
    """
    snap = load(eco)
    pep440 = (eco == "pypi")
    packages = snap["packages"]
    checked, mismatches, skipped = 0, [], 0
    for dv in snap["declaring"]:
        name, ver = dv["package"], dv["version"]
        rec = (packages.get(name) or {}).get("versions", {}).get(ver)
        if rec is None:
            continue
        t = rec["published_at"]
        doms = {}
        for dep, spec in sorted((rec.get("deps") or {}).items()):
            a, _ = admissible(packages.get(dep), spec, t, pep440)
            if a is None or not a:
                continue
            doms[dep] = a
        if not doms or len(doms) > max_edges:
            skipped += 1
            continue
        prod = 1
        for a in doms.values():
            prod *= len(a)
        if prod > max_solutions:
            skipped += 1
            continue
        keys = sorted(doms)
        # every solution of the declaration, as a tuple in `keys` order
        sols = [()]
        for k in keys:
            sols = [s + (v,) for s in sols for v in doms[k]]
        amb = [i for i, k in enumerate(keys) if len(doms[k]) >= 2]
        # exhaustive minimum distinguishing key: smallest subset making the projection injective
        best = None
        idx = list(range(len(keys)))
        import itertools
        for size in range(0, len(keys) + 1):
            found = False
            for sub in itertools.combinations(idx, size):
                seen = set()
                ok = True
                for s2 in sols:
                    proj = tuple(s2[i] for i in sub)
                    if proj in seen:
                        ok = False
                        break
                    seen.add(proj)
                if ok:
                    found = True
                    break
            if found:
                best = size
                break
        checked += 1
        if best != len(amb):
            mismatches.append({"declaring": "%s@%s" % (name, ver), "brute": best,
                               "closed_form": len(amb), "edges": len(keys)})
    return {"instances_checked": checked, "skipped_too_large": skipped,
            "brute_equals_closed_form": not mismatches, "mismatches": mismatches[:5]}


def summarise(eco):
    snap, now, rows, edges = analyse(eco)
    n_pkg = len(set(r["package"] for r in rows))
    tot_edges = sum(r["edges"] for r in rows)
    tot_amb = sum(r["ambiguous"] for r in rows)
    tot_differ = sum(r["differ"] for r in rows)
    tot_unknown = sum(r["unknown"] for r in rows)
    tot_unparsed = sum(r["unparsed"] for r in rows)
    tot_shape = sum(r["shape"] for r in rows)
    grew = sum(r["grew_edges"] for r in rows)
    # a declaration is UNDER-DETERMINED when its direct install count exceeds 1
    undet = [r for r in rows if r["installs_asof"] > 1]
    yanked = sum(1 for p in snap["packages"].values() for m in p["versions"].values() if m.get("yanked"))
    return {
        "ecosystem": eco,
        "snapshot_content_sha256": snap.get("content_sha256"),
        "as_of_now_instant": now,
        "declaring_versions": len(rows),
        "declaring_versions_with_edges": sum(1 for r in rows if r["edges"]),
        "declaring_versions_declaring_nothing": sum(1 for r in rows
                                                   if r["edges"] == 0 and r["unparsed"] == 0),
        "declaring_versions_all_specs_unparsed": sum(1 for r in rows
                                                     if r["edges"] == 0 and r["unparsed"] > 0),
        "declaring_packages": n_pkg,
        "edges": tot_edges,
        "unparsed_specs": tot_unparsed,
        "edges_unknown_package": sum(r.get("unknown_pkg", 0) for r in rows),
        # demoted: how ranges are WRITTEN, not the finding
        "ambiguous_edges": tot_amb,
        "ambiguous_share": (float(tot_amb) / tot_edges) if tot_edges else None,
        "ambiguous_wilson": wilson(tot_amb, tot_edges),
        # the finding: what the alternatives cost
        "ambiguous_with_closure_difference": tot_differ,
        "closure_difference_share": (float(tot_differ) / tot_amb) if tot_amb else None,
        "closure_difference_wilson": wilson(tot_differ, tot_amb),
        "closure_difference_unknown": tot_unknown,
        "closure_shape_share": (float(tot_shape) / tot_amb) if tot_amb else None,
        "closure_shape_wilson": wilson(tot_shape, tot_amb),
        "certificate": certificate_check(eco),
        # dispersion of the solution set
        # THE POPULATION AT RISK is the declaring version that declares something.  A package that
        # declares nothing is trivially determined, so counting it in the denominator dilutes the
        # share without adding information -- both figures are reported, the risk-set one first.
        "declarations_under_determined": len(undet),
        "declarations_with_edges": sum(1 for r in rows if r["edges"]),
        "declarations_share_under_determined_at_risk":
            (float(len(undet)) / sum(1 for r in rows if r["edges"]))
            if sum(1 for r in rows if r["edges"]) else None,
        "declarations_under_determined_wilson_at_risk":
            wilson(len(undet), sum(1 for r in rows if r["edges"])),
        "declarations_share_under_determined_all": (float(len(undet)) / len(rows)) if rows else None,
        "declarations_under_determined_wilson_all": wilson(len(undet), len(rows)),
        "installs_asof_max": max([r["installs_asof"] for r in rows], default=None),
        "installs_asof_median": sorted(r["installs_asof"] for r in rows)[len(rows) // 2] if rows else None,
        "edges_that_grew": grew,
        "yanked_versions_in_snapshot": yanked,
        "baselines": {
            # pin-everything: the number of package pins a lockfile spends on this declaration
            "pin_everything_pins": sum(r["edges"] for r in rows),
            # pin-direct-only: the pins a direct-only pinner spends, against the installs it leaves open
            "pin_direct_only_pins": sum(r["ambiguous"] for r in rows),
            "install_count_pin_everything": len(rows),
            "install_count_pin_direct_only": sum(r["installs_now"] for r in rows),
        },
    }


def selftest():
    """The measure must be shown to DISTINGUISH, on cases whose answer is known by construction.

    A rate that cannot come out wrong is not a measurement, so each plant is a case where a naive
    implementation returns the wrong number and this one must not.
    """
    ok = True
    cases = []

    # plant 1: alternatives with IDENTICAL declared deps must not count as a closure difference
    fake = {"versions": {"1.0.0": {"published_at": "2020-01-01T00:00:00Z", "deps": {"a": "1"}},
                         "1.0.1": {"published_at": "2020-02-01T00:00:00Z", "deps": {"a": "1"}}}}
    sets = [depset(fake, v) for v in ("1.0.0", "1.0.1")]
    fired = len(set(s for s in sets if s is not None)) == 1
    cases.append(("identical closures -> NOT a difference", fired))

    # plant 2: one added dependency IS a difference
    fake2 = {"versions": {"1.0.0": {"published_at": "2020-01-01T00:00:00Z", "deps": {"a": "1"}},
                          "1.0.1": {"published_at": "2020-02-01T00:00:00Z", "deps": {"a": "1", "b": "1"}}}}
    sets = [depset(fake2, v) for v in ("1.0.0", "1.0.1")]
    cases.append(("one added dependency -> IS a difference",
                  len(set(s for s in sets if s is not None)) > 1))

    # plant 3: as-of filtering must EXCLUDE versions published after the declaration
    pkg = {"versions": {"1.0.0": {"published_at": "2020-01-01T00:00:00Z", "deps": {}},
                        "1.0.1": {"published_at": "2030-01-01T00:00:00Z", "deps": {}}}}
    got, _ = admissible(pkg, "^1.0.0", "2025-01-01T00:00:00Z", False)
    cases.append(("a version published later is not admissible as-of", got == ["1.0.0"]))
    got_now, _ = admissible(pkg, "^1.0.0", None, False)
    cases.append(("the same range read now admits it", got_now == ["1.0.0", "1.0.1"]))

    # plant 4: a prerelease is never admitted by a plain range (npm/PEP 440 both)
    pkg2 = {"versions": {"1.0.0": {"published_at": "2020-01-01T00:00:00Z", "deps": {}},
                         "1.1.0-rc.1": {"published_at": "2020-02-01T00:00:00Z", "deps": {}}}}
    got, _ = admissible(pkg2, "^1.0.0", None, False)
    cases.append(("prereleases are not admissible", got == ["1.0.0"]))

    # plant 5: an unparsed spec is REPORTED, never silently counted as unambiguous
    got, why = admissible({"versions": {}}, "npm:foo@1", None, False)
    cases.append(("an unparsed spec returns None, not an empty set", got is None and why["unparsed"]))

    # plant 6: k/n = 0 must give a ceiling, not a zero
    w = wilson(0, 52)
    cases.append(("wilson(0,52) has a positive upper bound", w is not None and w[0] == 0.0 and w[1] > 0.05))

    for label, good in cases:
        print("  plant %-52s %s" % (label, "OK" if good else "FAILED"))
        ok &= bool(good)
    print("PLANTS: %d/%d ok" % (sum(1 for _, g in cases if g), len(cases)))
    return 0 if ok else 1


def main():
    if "--check" in sys.argv:
        return selftest()
    out = {"generated_by": "ambiguous.py", "snapshot_note":
           "every number below is a function of snapshot_<eco>.json and nothing else",
           "estimand": "dispersion of the solution set; the per-edge rate is reported but demoted",
           "ecosystems": {}}
    for eco in ("npm", "pypi"):
        s = summarise(eco)
        out["ecosystems"][eco] = s
        print("== %s (snapshot %s)" % (eco, (s["snapshot_content_sha256"] or "")[:16]))
        print("   declaring versions %d over %d packages; edges %d (unparsed specs %d, "
              "edges naming a package absent from the snapshot %d)"
              % (s["declaring_versions"], s["declaring_packages"], s["edges"], s["unparsed_specs"],
                 s["edges_unknown_package"]))
        print("   [demoted] edges admitting >=2 versions: %d/%d = %.3f  wilson %s"
              % (s["ambiguous_edges"], s["edges"], s["ambiguous_share"] or 0.0,
                 ["%.4f" % x for x in (s["ambiguous_wilson"] or [])]))
        print("   FINDING  alternatives that change the closure: %d/%d = %.3f  wilson %s  (unknown %d)"
              % (s["ambiguous_with_closure_difference"], s["ambiguous_edges"],
                 s["closure_difference_share"] or 0.0,
                 ["%.4f" % x for x in (s["closure_difference_wilson"] or [])],
                 s["closure_difference_unknown"]))
        print("   declaring versions: %d total = %d with edges + %d declaring nothing + %d all-unparsed"
              % (s["declaring_versions"], s["declaring_versions_with_edges"],
                 s["declaring_versions_declaring_nothing"],
                 s["declaring_versions_all_specs_unparsed"]))
        print("   closure SHAPE difference (a dep added/removed): %s  wilson %s"
              % (("%.3f" % s["closure_shape_share"]) if s["closure_shape_share"] is not None else "n/a",
                 ["%.4f" % x for x in (s["closure_shape_wilson"] or [])]))
        c = s["certificate"]
        print("   certificate |K*| = #ambiguous: brute force %d instance(s), skipped %d, agrees %s"
              % (c["instances_checked"], c["skipped_too_large"], c["brute_equals_closed_form"]))
        print("   declarations admitting >1 install: %d/%d = %.3f  wilson %s   (over all %d: %.3f)"
              % (s["declarations_under_determined"], s["declarations_with_edges"],
                 s["declarations_share_under_determined_at_risk"] or 0.0,
                 ["%.4f" % x for x in (s["declarations_under_determined_wilson_at_risk"] or [])],
                 s["declaring_versions"], s["declarations_share_under_determined_all"] or 0.0))
        print("   installs per declaration: median %s, max %s; edges that grew since declaration %d"
              % (s["installs_asof_median"], s["installs_asof_max"], s["edges_that_grew"]))
        print("   yanked versions in snapshot (the lemma's exception): %d"
              % s["yanked_versions_in_snapshot"])
        print("   baselines: pin-everything %d pins vs pin-direct-only %d pins"
              % (s["baselines"]["pin_everything_pins"], s["baselines"]["pin_direct_only_pins"]))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
