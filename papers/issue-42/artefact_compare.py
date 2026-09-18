#!/usr/bin/env python3
"""Step 2 of issue #42's reproduction: compare the produced artefacts with the committed ones --
and, when they differ, say WHY before anyone records it as a defect of the artefact.

`correction round 2, required change 4`. The comparison itself is unchanged: the canonical digest
(sorted keys, parsed JSON) of each produced artefact must equal the committed one, and on the named
build a difference is a failure. What this file adds is the attribution the round asks for:

  * the running build is read from `build.json` (the record `build_record.py` owns) and printed;
  * on a difference, every differing LEAF is listed with its deviation;
  * each difference is then classified -- a numeric leaf inside the declared band, or a non-numeric
    leaf that is a digest RECOMPUTED from the artefact it belongs to (so the change follows the
    numbers rather than contradicting them) -- and only if every difference is explained by the
    build mismatch is the outcome reported as a **COORDINATE**, never as a defect of the artefact.

Exit codes:

    0   every artefact identical to the committed one (the comparison holds on this build)
    4   COORDINATE: the running build differs from the named build and every difference is explained
        by it -- a coordinate mismatch, NOT a failed reproduction
    1   FAILURE: the build is the named one and a difference stands; or a difference lies outside the
        declared band; or a non-numeric difference is not a derived digest; or a leaf structure
        differs; or an artefact contradicts its own declared digest

Usage:
    python3 artefact_compare.py --build <dir> [--root .] [--record build.json]
        [--run-python V] [--run-numpy V]      # the last two exist so a control can pin the running
        [--print N]                           # build instead of inheriting the verifier's machine
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VERSIONS = "0123"


def canon(path):
    with io.open(path, encoding="utf-8") as fh:
        return hashlib.sha256(json.dumps(json.load(fh), sort_keys=True).encode()).hexdigest()


def leaves(node, path=""):
    """Every leaf of a parsed artefact, keyed by its JSON pointer path."""
    if isinstance(node, dict):
        for k in node:
            for p, v in leaves(node[k], "%s/%s" % (path, k)):
                yield p, v
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for p, vv in leaves(v, "%s/%d" % (path, i)):
                yield p, vv
    else:
        yield path, node


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


def digest_fields(obj):
    """The top-level keys whose value's FORM is a digest: 64 hex characters.

    Deliberately not "the key named digest" and not "the key that happens to verify": the claim is
    read off the artefact's shape, so an artefact cannot opt out of the check by renaming the key,
    and an artefact whose digest is stale still declares the field that is stale.
    """
    if not isinstance(obj, dict):
        return set()
    return {k for k, v in obj.items() if isinstance(v, str) and _HEX64.match(v)}


def _digest_of(obj, k):
    rest = {k2: v2 for k2, v2 in obj.items() if k2 != k}
    return hashlib.sha256(json.dumps(rest, sort_keys=True).encode()).hexdigest()


def digest_breakage(tag, obj):
    """[(tag, field)] for every declared digest that does NOT match the object carrying it.

    A digest is not an independent measurement -- it is a function of the numbers beside it -- so it
    can account for a coupled difference. It can only do that while it is CONSISTENT with its own
    artefact: a stale digest is not a build effect and not a floating rounding error, it is an
    artefact the format itself says is broken -- on either side of the comparison.
    """
    return [(tag, k) for k in sorted(digest_fields(obj)) if _digest_of(obj, k) != obj[k]]


def compare(built, committed, band, print_cap):
    """(diffs, notes) for one artefact pair. `diffs` maps a leaf path to (built, committed)."""
    a = {p: v for p, v in leaves(built)}
    b = {p: v for p, v in leaves(committed)}
    only_built = sorted(set(a) - set(b))
    only_committed = sorted(set(b) - set(a))
    diffs = {p: (a[p], b[p]) for p in sorted(set(a) & set(b)) if a[p] != b[p] and not _both_nan(a[p], b[p])}
    notes = []
    if only_built or only_committed:
        notes.append("STRUCTURE: %d leaf path(s) only in the produced artefact%s, %d only in the"
                     " committed one%s"
                     % (len(only_built), _cap(only_built, print_cap),
                        len(only_committed), _cap(only_committed, print_cap)))
    return diffs, notes


def _both_nan(x, y):
    return isinstance(x, float) and isinstance(y, float) and x != x and y != y


def _cap(items, n):
    if not items:
        return ""
    head = ", ".join(items[:n])
    return " (%s%s)" % (head, ", ..." if len(items) > n else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True, help="directory the instruments wrote into")
    ap.add_argument("--root", default=HERE, help="the package whose artefacts are the reference")
    ap.add_argument("--record", default=os.path.join(HERE, "build.json"))
    ap.add_argument("--run-python", default=None, help="override the measured running build (controls)")
    ap.add_argument("--run-numpy", default=None)
    ap.add_argument("--print", dest="print_cap", type=int, default=4)
    args = ap.parse_args()

    record = json.load(io.open(args.record, encoding="utf-8"))
    band = record["band"]
    if args.run_python is None or args.run_numpy is None:
        try:
            import numpy
            run = {"python": sys.version.split()[0], "numpy": numpy.__version__}
        except ImportError:
            run = {"python": sys.version.split()[0], "numpy": "ABSENT"}
    else:
        run = {"python": args.run_python, "numpy": args.run_numpy}
    if args.run_python is not None:
        run["python"] = args.run_python
    if args.run_numpy is not None:
        run["numpy"] = args.run_numpy
    named = {"python": record["python"], "numpy": record["numpy"]}
    same_build = run == named

    print("   build: this run Python %s / numpy %s | named Python %s / numpy %s -> %s"
          % (run["python"], run["numpy"], named["python"], named["numpy"],
             "the named build" if same_build else "BUILD MISMATCH"))

    identical = True
    detail = []
    for v in VERSIONS:
        name = "results_v%s.json" % v
        bp, cp = os.path.join(args.build, name), os.path.join(args.root, "artefacts", name)
        if not os.path.exists(bp):
            print("   %-18s %s  %s" % (name, "MISSING", "the produced artefact is not there"))
            detail.append((name, "MISSING", {}, ["the produced artefact is not there"], None))
            identical = False
            continue
        if not os.path.exists(cp):
            print("   %-18s %s  %s  (%s)" % (name, "NO REFERENCE", "", cp))
            detail.append((name, "NO REFERENCE", {}, ["the committed artefact is not there"], None))
            identical = False
            continue
        da, db = canon(bp), canon(cp)
        built = json.load(io.open(bp, encoding="utf-8"))
        committed = json.load(io.open(cp, encoding="utf-8"))
        # An artefact that contradicts its own declared digest is broken BEFORE it is anything else --
        # before "identical", before "a difference the build explains". Read on both sides, so a
        # reference artefact whose digest does not match it is a defect of the package, not a licence.
        broken = digest_breakage("committed", committed) + digest_breakage("produced", built)
        if broken:
            print("   %-18s %s  %s  (%s)"
                  % (name, "BROKEN", db[:20],
                     ", ".join("%s %s does not match its own artefact" % (w, k) for w, k in broken)))
            # `{}`, not `[]`: a BROKEN artefact still has to survive the attribution pass below,
            # which reads `diffs` as a mapping. (It survived it only as an AttributeError until the
            # control that produced this very message was read at its object instead of its exit code.)
            detail.append((name, "BROKEN", {}, ["%s: the %s digest is stale relative to the numbers"
                                                " beside it" % (k, w) for w, k in broken], None))
            identical = False
            continue
        if da == db:
            print("   %-18s %s  %s" % (name, "IDENTICAL", db[:20]))
            continue
        identical = False
        fields = digest_fields(committed)
        diffs, notes = compare(built, committed, band, args.print_cap)
        worst, worst_at = 0.0, ""
        for p, (x, y) in diffs.items():
            if is_number(x) and is_number(y) and abs(x - y) > worst:
                worst, worst_at = abs(x - y), p
        print("   %-18s %s  %s  (%d differing field(s)%s)"
              % (name, "DIFFERS", db[:20], len(diffs),
                 "" if not diffs else ", worst |delta| %s at %s" % ("%g" % worst, worst_at)))
        for p, (x, y) in list(diffs.items())[:args.print_cap]:
            print("        %s  %r -> %r" % (p, x, y))
        if len(diffs) > args.print_cap:
            print("        ... %d further field(s) not printed (the counts below cover all of them)"
                  % (len(diffs) - args.print_cap))
        detail.append((name, "DIFFERS", diffs, notes, fields))

    if identical:
        if same_build:
            print("   the four artefacts are identical to the committed ones, on the named build")
        else:
            print("   the four artefacts are identical to the committed ones, on a build that is not")
            print("   the named one -- exactness held anyway, so there is nothing to attribute")
        return 0

    # ---- integrity first: a missing or self-contradicting artefact makes attribution meaningless --
    absent = [(name, st) for name, st, _d, _n, _x in detail if st in ("MISSING", "NO REFERENCE")]
    if absent:
        print("   FAILURE: %s -- an absent artefact is not a coordinate and not a build effect: %s"
              % (", ".join(name for name, _st in absent),
                 "; ".join("%s %s" % (name, "was not produced" if st == "MISSING"
                                      else "is missing from the package") for name, st in absent)))
        return 1
    broken_at = [name for name, st, _d, _n, _x in detail if st == "BROKEN"]
    if broken_at:
        print("   FAILURE: %s contradicts the digest it carries -- the artefact, not the build."
              % ", ".join(broken_at))
        return 1

    # ---- attribution: is every difference explained by the build? -------------------------------
    n_num, out_of_band, unexplained, nonnumeric = 0, [], [], 0
    for name, _st, diffs, notes, derived in detail:
        unexplained += list(notes)
        for p, (x, y) in diffs.items():
            if is_number(x) and is_number(y):
                n_num += 1
                allowed = max(band["absolute"], band["relative"] * abs(y))
                if abs(x - y) > allowed:
                    out_of_band.append("%s%s (|delta| %g > %g)" % (name, p, abs(x - y), allowed))
            else:
                nonnumeric += 1
                top = p.split("/")[1] if p.count("/") >= 1 else p
                if top not in (derived or set()):
                    unexplained.append("%s%s (%r -> %r)" % (name, p, x, y))
    print("   attribution: %d numeric field(s) differing; band %s absolute / %s relative"
          % (n_num, "%g" % band["absolute"], "%g" % band["relative"]))
    print("                %d non-numeric field(s) differing%s"
          % (nonnumeric, "" if nonnumeric == 0 else
             " (a digest recomputed from the same artefact explains it)" if not unexplained else ""))
    if out_of_band:
        print("                %d field(s) OUTSIDE the band: %s" % (len(out_of_band), _cap(out_of_band, args.print_cap)))
    if unexplained:
        print("                %d difference(s) the build cannot explain: %s"
              % (len(unexplained), _cap(unexplained, args.print_cap)))

    if not same_build and not out_of_band and not unexplained:
        print("   COORDINATE: this run's build differs from the named build and EVERY difference is")
        print("   explained by it -- a coordinate mismatch, NOT a defect of the artefact, and not a")
        print("   failed reproduction (README.md -> the tolerance rule; band and span: build.json).")
        return 4
    if same_build:
        print("   FAILURE: the running build IS the named build, so the difference is not the build's.")
    elif out_of_band:
        print("   FAILURE: the build differs, but a difference lies outside the declared band.")
    else:
        print("   FAILURE: the build differs, but a difference is not explained by it.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
