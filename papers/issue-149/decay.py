#!/usr/bin/env python3
"""decay.py -- issue #149: how long a declaring version keeps determining an install (P2).

THE QUESTION.  A declaration that determines an install today need not determine one in a year:
registries publish underneath it.  This file measures the survival curve -- the fraction of edges
that are still singletons k months after the declaring version was published -- and asks whether the
DECAY IS THE DIALECT'S, which is the claim the paper needs:

    ^x.y.z / ~x.y.z   bounded above by design     -> should saturate
    >=x / >x          no upper bound at all        -> should decay without a floor
    =x.y.z            pinned                       -> should not decay at all

If the strata coincide, the honest finding is "boundedness buys nothing measurable here" and that is
what gets reported: the mechanism claim exists only if they separate.

THE AT-RISK SET, chosen once and stated.  At each k the denominator is the edges that were
**singletons at k = 0** -- an edge already ambiguous when written cannot lose a determination it never
had.  The denominator is printed at every k alongside a Wilson band, and an empty denominator prints
NOT RUN rather than a 0.0.

THE OBSERVABILITY RULE, fixed before the run (results.md, R681).  A version DELETED before the snapshot
instant is invisible, so a deletion can make an admissible set shrink and survival appear to RISE.  A k
where survival rises above k-1 is therefore reported as NON-MONOTONE -- a candidate unobservable
deletion -- counted, and never as a refutation of the monotonicity lemma and never as a bug in this
instrument.

Usage: python3 decay.py [--check]     (offline: reads snapshot_<eco>.json; no network, no clock)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE  # the package directory holds the snapshot AND the artifact. HERE/.. read
# papers/ and found nothing, so the committed scripts could not reproduce the committed
# numbers on a clean checkout. A reproduction path that depends on a directory the package
# does not own is not a reproduction path.
OUT = os.path.join(PKG, "decay.json")

sys.path.insert(0, HERE)
from fetch_snapshot import parse_spec, satisfies, is_prerelease, _day  # noqa: E402
from ambiguous import wilson  # noqa: E402

MONTHS = 12


def add_months(day_number, k):
    """A month grid over day numbers.  Exact enough for a cohort grid: 30.44 days per month, and the
    curve is read at whole months, so a day of slop cannot move a stratum."""
    return day_number + int(round(k * 30.4375))


def stratum(spec, pep440):
    """The form the range is WRITTEN in -- assigned from the text, never from the outcome."""
    s = (spec or "").strip()
    if not s:
        return None
    if "||" in s or "," in s and ">=" in s and "<" in s:
        return "other"                      # a compound range: reported apart, never merged
    if s.startswith("^"):
        return "caret"
    if s.startswith("~"):
        return "tilde"
    if s.startswith(">=") or s.startswith(">"):
        return "unbounded"
    if s.startswith("=") or re.match(r"^[vV]?\d+(\.\d+){0,2}$", s):
        return "exact"
    return "other"


def admissible_at(pkg, spec, at_day, pep440):
    """The admissible set at an instant.  None = the target is not in the snapshot (UNKNOWN, never 0)."""
    if not pkg:
        return None
    alts = parse_spec(spec, pep440=pep440)
    if alts is None:
        return None
    out = []
    for v, m in pkg["versions"].items():
        if m["prerelease"] or is_prerelease(v) or m["yanked"]:
            continue
        if _day(m["published_at"]) > at_day:
            continue
        if satisfies(v, alts):
            out.append(v)
    return out


def cohort(eco):
    snap = json.load(io.open(os.path.join(PKG, "snapshot_%s.json" % eco), encoding="utf-8"))
    pep440 = (eco == "pypi")
    PK = snap["packages"]
    panel = [d for d in snap["declaring"] if d.get("role") == "panel"]
    return snap, PK, pep440, panel


def curve(eco):
    snap, PK, pep440, panel = cohort(eco)
    # edge-level tallies: stratum -> k -> [at_risk, still_singleton]
    tallies, decl_t = {}, {}
    unknown_edges, unparsed_edges = 0, 0
    yank_events = 0
    rows = []
    for dv in panel:
        name, ver = dv["package"], dv["version"]
        rec = (PK.get(name) or {}).get("versions", {}).get(ver)
        if not rec:
            continue
        t0 = _day(rec["published_at"])
        edges = []
        for dep, spec in (rec.get("deps") or {}).items():
            tgt = PK.get(dep)
            a0 = admissible_at(tgt, spec, t0, pep440)
            if a0 is None:
                if parse_spec(spec, pep440=pep440) is None:
                    unparsed_edges += 1
                else:
                    unknown_edges += 1
                continue
            edges.append((dep, spec, tgt, a0))
        if not edges:
            continue
        rows.append({"declaring": "%s@%s" % (name, ver), "edges": len(edges)})
        for k in range(MONTHS + 1):
            at = add_months(t0, k)
            det_decl = True
            for dep, spec, tgt, a0 in edges:
                st = stratum(spec, pep440)
                if st is None:
                    continue
                ak = admissible_at(tgt, spec, at, pep440)
                if ak is None:
                    continue
                # yank observability: a yanked version inside the window is COUNTED (PyPI shows it)
                if at > t0:
                    for v, m in tgt["versions"].items():
                        if m["yanked"] and t0 < _day(m["published_at"]) <= at and satisfies(
                                v, parse_spec(spec, pep440=pep440) or []):
                            yank_events += 1
                if len(ak) != 1:
                    det_decl = False
                if len(a0) == 1:                       # the at-risk set
                    cell = tallies.setdefault(st, {}).setdefault(k, [0, 0])
                    cell[0] += 1
                    if len(ak) == 1:
                        cell[1] += 1
            if all(len(admissible_at(tgt, spec, t0, pep440) or []) == 1
                   for dep, spec, tgt, a0 in edges):
                cell = decl_t.setdefault(k, [0, 0])
                cell[0] += 1
                if det_decl:
                    cell[1] += 1
    return {"tallies": tallies, "declaration": decl_t, "edges_unknown_target": unknown_edges,
            "edges_unparsed": unparsed_edges, "yank_events_in_windows": yank_events,
            "declarations": len(rows)}


def summarise(eco):
    c = curve(eco)
    out = {"ecosystem": eco, "declarations_in_panel": c["declarations"],
           "edges_unknown_target": c["edges_unknown_target"],
           "edges_unparsed": c["edges_unparsed"],
           "yank_events_in_windows": c["yank_events_in_windows"], "strata": {}, "non_monotone": {}}
    for st, ks in sorted(c["tallies"].items()):
        series, prev, nonmono = [], None, 0
        for k in range(MONTHS + 1):
            at, ok = ks.get(k, [0, 0])
            if at == 0:
                series.append({"k": k, "at_risk": 0, "determined": None, "rate": None,
                               "wilson": None, "verdict": "NOT RUN"})
                continue
            rate = float(ok) / at
            if prev is not None and rate > prev + 1e-12:
                nonmono += 1
            prev = rate
            series.append({"k": k, "at_risk": at, "determined": ok, "rate": rate,
                           "wilson": wilson(ok, at), "verdict": "measured"})
        out["strata"][st] = series
        out["non_monotone"][st] = nonmono
    series, prev, nonmono = [], None, 0
    for k in range(MONTHS + 1):
        at, ok = c["declaration"].get(k, [0, 0])
        if at == 0:
            series.append({"k": k, "at_risk": 0, "determined": None, "rate": None,
                           "wilson": None, "verdict": "NOT RUN"})
            continue
        rate = float(ok) / at
        if prev is not None and rate > prev + 1e-12:
            nonmono += 1
        prev = rate
        series.append({"k": k, "at_risk": at, "determined": ok, "rate": rate,
                       "wilson": wilson(ok, at), "verdict": "measured"})
    out["declaration_survival"] = series
    out["paired"] = paired_control(eco)
    out["declaration_non_monotone"] = nonmono
    return out



def paired_control(eco):
    """The same TARGET package seen under both a bounded and an unbounded form.

    Stratifying inside one ecosystem already removes most of the cadence story, but a sceptic can say
    the strata simply attach to different packages -- popular ones decay faster.  This control holds
    the package fixed: for every target that appears under more than one stratum, compare survival at
    k = 12 within that target only, and count how often the bounded form outlives the unbounded one.
    """
    snap, PK, pep440, panel = cohort(eco)
    per_tgt = {}
    for dv in panel:
        rec = (PK.get(dv["package"]) or {}).get("versions", {}).get(dv["version"])
        if not rec:
            continue
        t0 = _day(rec["published_at"])
        for dep, spec in (rec.get("deps") or {}).items():
            st = stratum(spec, pep440)
            tgt = PK.get(dep)
            if st is None or tgt is None:
                continue
            a0 = admissible_at(tgt, spec, t0, pep440)
            if a0 is None or len(a0) != 1:
                continue
            a12 = admissible_at(tgt, spec, add_months(t0, 12), pep440)
            if a12 is None:
                continue
            per_tgt.setdefault(dep, {}).setdefault(st, []).append(1 if len(a12) == 1 else 0)
    # EVERY pair of distinct strata present on the SAME target, so the control is not restricted to a
    # contrast that the data may not contain: within npm the pairs that exist are exact-vs-caret, and
    # that is the comparison cadence cannot explain.
    rows, pairs = [], {}
    for dep, by_st in sorted(per_tgt.items()):
        sts = sorted(k for k in by_st if by_st[k])
        for i in range(len(sts)):
            for j in range(i + 1, len(sts)):
                a, b = sts[i], sts[j]
                ra = float(sum(by_st[a])) / len(by_st[a])
                rb = float(sum(by_st[b])) / len(by_st[b])
                key = "%s>%s" % (a, b)
                cells = pairs.setdefault(key, [0, 0, 0])
                cells[0] += 1
                if ra > rb:
                    cells[1] += 1
                elif rb > ra:
                    cells[2] += 1
                rows.append({"target": dep, "stratum_a": a, "n_a": len(by_st[a]), "surv_a": ra,
                             "stratum_b": b, "n_b": len(by_st[b]), "surv_b": rb})
    return {"targets_compared": len(set(r["target"] for r in rows)),
            "pairs": dict((k, {"targets": v[0], "a_outlives": v[1], "b_outlives": v[2]})
                          for k, v in sorted(pairs.items())),
            "rows": rows[:60]}


def check():
    """Known-answer plants: each is a case where a plausible implementation reports the wrong curve."""
    ok = True

    def mk(times_versions, spec):
        return {"versions": dict((v, {"published_at": t, "deps": {}, "prerelease": False,
                                      "yanked": False}) for v, t in times_versions)}

    d0 = _day("2025-01-01T00:00:00Z")
    # 1: an EXACT pin cannot decay -- no matter how much the target publishes afterwards
    tgt = mk([("1.0.0", "2024-06-01T00:00:00Z"), ("1.0.1", "2025-06-01T00:00:00Z"),
              ("2.0.0", "2025-12-01T00:00:00Z")], None)
    at1 = admissible_at(tgt, "=1.0.0", add_months(d0, 12), False)
    good = at1 == ["1.0.0"]
    print("  plant exact pin stays singleton at k=12                %s (%s)"
          % ("OK" if good else "FAILED", at1))
    ok &= good

    # 2: an UNBOUNDED range decays -- a later publish enters the admissible set
    at2 = admissible_at(tgt, ">=1.0.0", add_months(d0, 12), False)
    good = at2 == ["1.0.0", "1.0.1", "2.0.0"]
    print("  plant unbounded range grows at k=12                    %s (%d versions)"
          % ("OK" if good else "FAILED", len(at2 or [])))
    ok &= good

    # 3: a CARET range stops at the major bound -- 2.0.0 must NOT enter
    at3 = admissible_at(tgt, "^1.0.0", add_months(d0, 12), False)
    good = at3 == ["1.0.0", "1.0.1"]
    print("  plant caret range saturates at the major bound          %s (%s)"
          % ("OK" if good else "FAILED", at3))
    ok &= good

    # 4: the as-of read must not see the future: at k=0 only the first version exists
    at4 = admissible_at(tgt, ">=1.0.0", d0, False)
    good = at4 == ["1.0.0"]
    print("  plant as-of k=0 excludes every later publish            %s (%s)"
          % ("OK" if good else "FAILED", at4))
    ok &= good

    # 5: a target ABSENT from the snapshot is UNKNOWN, never an empty (ambiguous) reading
    at5 = admissible_at(None, ">=1.0.0", d0, False)
    good = at5 is None
    print("  plant absent target is UNKNOWN, not ambiguous           %s" % ("OK" if good else "FAILED"))
    ok &= good

    # 6: strata are read from the TEXT, and a compound range is not silently pooled
    got = [stratum("^1.2.3", False), stratum("~1.2.3", False), stratum(">=1.2.3", False),
           stratum("=1.2.3", False), stratum(">=1.0.0,<2.0.0", True)]
    good = got == ["caret", "tilde", "unbounded", "exact", "other"]
    print("  plant strata from the range text                       %s (%s)"
          % ("OK" if good else "FAILED", got))
    ok &= good

    # 7: an empty denominator must read NOT RUN, never 0.0
    good = wilson(0, 0) is None
    print("  plant empty denominator is NOT RUN, not 0.0             %s" % ("OK" if good else "FAILED"))
    ok &= good

    print("PLANTS: %s" % ("ALL PASS" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    if "--check" in sys.argv:
        return check()
    out = {"panel": "declarations at least 12 months old; at-risk = edges singleton at k=0",
           "observability": "a deletion before the snapshot instant is invisible; a k where survival "
                            "rises is reported NON-MONOTONE, counted, never as a refutation",
           "ecosystems": {}}
    for eco in ("npm", "pypi"):
        s = summarise(eco)
        out["ecosystems"][eco] = s
        print("== %s: %d declarations in panel (unknown-target edges %d, unparsed %d, yanks %d)"
              % (eco, s["declarations_in_panel"], s["edges_unknown_target"],
                 s["edges_unparsed"], s["yank_events_in_windows"]))
        print("   %-10s %s" % ("stratum", "survival at k = 0,3,6,9,12 months (n at risk)"))
        for st, series in sorted(s["strata"].items()):
            cells = []
            for k in (0, 3, 6, 9, 12):
                c = series[k]
                if c["verdict"] == "NOT RUN":
                    cells.append("NOT RUN")
                else:
                    cells.append("%.3f (n=%d)" % (c["rate"], c["at_risk"]))
            print("   %-10s %s   [non-monotone points: %d]"
                  % (st, "  ".join(cells), s["non_monotone"][st]))
        ds = s["declaration_survival"]
        cells = []
        for k in (0, 3, 6, 9, 12):
            c = ds[k]
            cells.append("NOT RUN" if c["verdict"] == "NOT RUN" else "%.3f (n=%d)" % (c["rate"], c["at_risk"]))
        print("   %-10s %s   [non-monotone: %d]"
              % ("DECL", "  ".join(cells), s["declaration_non_monotone"]))
        p = s["paired"]
        print("   paired control (same target, two strata): %d target(s) with a comparable pair"
              % p["targets_compared"])
        for key, v in p["pairs"].items():
            print("      %-18s targets %3d | first outlives %3d | second outlives %3d"
                  % (key, v["targets"], v["a_outlives"], v["b_outlives"]))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
