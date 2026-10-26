#!/usr/bin/env python3
"""Presence-vs-coverage separation, as a ratio with a Wilson interval.

Registered success criterion (ii) of issue #145: "the presence-vs-coverage separation
as a ratio with a Wilson interval". This script owns that number, deriving every
count from the committed snapshot artifacts rather than from notes.

Two rates are computed per ecosystem, on their own denominators:

  presence  = attested units / all units in the frame
  coverage  = units with a non-empty declared closure and c > 0 / units with a
              non-empty declared closure

The second denominator is the honest one: `c` is undefined (n/a) for a release that
declares no dependencies, so those units are not evidence of zero coverage and are
not in the denominator. Coverage is also reported at dependency level.

Wilson score interval, 95%, z = 1.959963984540054. Exact counts are printed with
their denominators so no printed ratio is unaccompanied.
"""
import json
import math
import sys

Z = 1.959963984540054


def wilson(k, n, z=Z):
    """Wilson score interval for k successes of n trials, as (low, high, point)."""
    if n == 0:
        return (None, None, None)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return (lo, hi, p)


def fmt(k, n):
    lo, hi, p = wilson(k, n)
    if n == 0:
        return "n=0 (undefined)"
    return ("%d/%d = %.4f  Wilson95%% [%.4f, %.4f]" % (k, n, p, lo, hi))


def npm(path="snapshot_npm_d1_pilot.json"):
    s = json.load(open(path))
    rows = s["rows"]
    att = [r for r in rows if r["attested"]]
    with_deps = [r for r in att if r["n_deps"] > 0]
    covered_units = [r for r in with_deps if r["n_covered"] > 0]
    deps_total = sum(r["n_deps"] for r in with_deps)
    deps_cov = sum(r["n_covered"] for r in with_deps)
    return {
        "ecosystem": "npm",
        "units": len(rows),
        "attested": len(att),
        "with_deps": len(with_deps),
        "covered_units": len(covered_units),
        "deps_total": deps_total,
        "deps_covered": deps_cov,
        "presence": (len(att), len(rows)),
        "coverage_given_closure": (len(covered_units), len(with_deps)),
        "coverage_given_attested": (len(covered_units), len(att)),
        "closure_given_present": (len(with_deps), len(att)),
    }


def pypi(path="snapshot_pypi.json"):
    """PyPI's snapshot nests one record per project, each holding a list of files.

    The unit of analysis is the file (a statement is per file), so the rows are
    flattened from the projects. Returns None when the frame yields no rows at all —
    an empty denominator is NOT RUN, never a zero.
    """
    s = json.load(open(path))
    rows = []
    for proj in s.get("projects") or []:
        for f in proj.get("files") or []:
            row = dict(f)
            row.setdefault("package", proj.get("package"))
            row.setdefault("version", proj.get("version"))
            rows.append(row)
    if not rows:
        return {
            "ecosystem": "pypi", "empty": True,
            "units": 0, "attested": 0, "with_deps": 0, "covered_units": 0,
            "deps_total": 0, "deps_covered": 0,
            "presence": (0, 0), "coverage_given_closure": (0, 0),
            "coverage_given_attested": (0, 0), "closure_given_present": (0, 0),
            "summary": s.get("summary", {}),
        }
    att = [r for r in rows if r.get("attested")]
    with_deps = [r for r in att if (r.get("n_deps") or 0) > 0]
    covered_units = [r for r in with_deps if (r.get("n_covered") or 0) > 0]
    deps_total = sum((r.get("n_deps") or 0) for r in with_deps)
    deps_cov = sum((r.get("n_covered") or 0) for r in with_deps)
    return {
        "ecosystem": "pypi",
        "empty": False,
        "units": len(rows),
        "attested": len(att),
        "with_deps": len(with_deps),
        "covered_units": len(covered_units),
        "deps_total": deps_total,
        "deps_covered": deps_cov,
        "presence": (len(att), len(rows)),
        "coverage_given_closure": (len(covered_units), len(with_deps)),
        "coverage_given_attested": (len(covered_units), len(att)),
        "closure_given_present": (len(with_deps), len(att)),
    }


def report(d):
    print("== %s ==" % d["ecosystem"])
    if d.get("empty"):
        print("  NOT RUN: the frame yielded no rows")
        return
    print("  units in frame            : %d" % d["units"])
    print("  presence  (attested/frame): %s" % fmt(*d["presence"]))
    print("  closure   (withdeps/att.) : %s" % fmt(*d["closure_given_present"]))
    print("  COVERAGE  (cov/withdeps)  : %s" % fmt(*d["coverage_given_closure"]))
    print("  coverage  (cov/attested)  : %s" % fmt(*d["coverage_given_attested"]))
    print("  deps      (covered/total) : %s" % fmt(d["deps_covered"], d["deps_total"]))
    lo_p, hi_p, _ = wilson(*d["presence"])
    lo_c, hi_c, _ = wilson(*d["coverage_given_closure"])
    if lo_p is not None and hi_c is not None:
        gap = lo_p - hi_c
        verdict = "DISJOINT" if gap > 0 else "OVERLAPPING"
        print("  presence-lo minus coverage-hi = %.4f  -> intervals %s" % (gap, verdict))


def main():
    ds = [npm(), pypi()]
    for d in ds:
        report(d)
    # the separation is claimable only if, in every ecosystem, the two intervals
    # are disjoint: presence is measured well above zero, coverage is bounded
    # near zero, and the gap is not sampling noise.
    ok = True
    for d in ds:
        lo_p, _, _ = wilson(*d["presence"])
        _, hi_c, _ = wilson(*d["coverage_given_closure"])
        if d["attested"] == 0 or d["with_deps"] == 0:
            print("NOT RUN: %s has an empty denominator" % d["ecosystem"])
            ok = False
        elif not (lo_p > hi_c):
            ok = False
    print("\nSEPARATION: %s" % ("DISJOINT IN EVERY ECOSYSTEM" if ok else "NOT ESTABLISHED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
