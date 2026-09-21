#!/usr/bin/env python3
"""#87 -- the package's counted claims have ONE owner: the assembly report.  This checker reads every carrier.

WHY.  The R415 editorial re-check found the same defect in the previous head twice: `reproduce.sh`'s header
said 91 numeric bindings while its own manifest said 128.  A number restated in several carriers goes stale in
all but the one that was edited, so the repair is not another edit -- it is an owner and a check:

  * the OWNER is the assembly report (`artefacts/assembly/assembly-report.txt`), which prints the counts the
    assembly itself measured: bibliography entries, in-text coverage and bound numbers;
  * every other carrier (this README, `reproduce.sh`, the manuscript) is READ against it, and a carrier that
    states a different number is a defect of the carrier, not a rounding difference.

The patterns are narrow and declared: they match the house phrasings a count is written in ("N numeric
bindings", "N bindings", "N/169 coverage", "N numeric claims").  A phrasing outside the list is not read --
the list is the coordinate, and it is printed with the verdict so a reader can see what was and was not
scanned.

Run:  python3 artefacts/assembly/counts_check.py        exit 0 = every carrier agrees with the owner
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # papers/issue-87/artefacts/assembly
PKG = os.path.dirname(os.path.dirname(HERE))               # papers/issue-87
OWNER = os.path.join(HERE, "assembly-report.txt")

# The carriers, and the house phrasings.  (file, regex with the number in group 1, what the number counts)
CARRIERS = [
    ("README.md", r'(\d+)\s+quantities read out', "quantities"),
    ("reproduce.sh", r'(\d+)\s+quantities read out', "quantities"),
    ("README.md", r'(\d+)\s+numeric bindings', "bindings"),
    ("README.md", r'(\d+)\s+numeric claims', "bindings"),
    ("README.md", r'coverage (\d+)/\d+,', "entries"),
    ("README.md", r'(\d+)\s+bindings', "bindings"),
    ("reproduce.sh", r'BINDINGS=(\d+)', "bindings"),
    ("reproduce.sh", r'COVERAGE=(\d+)', "entries"),
    ("manuscript.md", r'(\d+)\s+numeric bindings', "bindings"),
]


def owner_counts():
    """Read the counts out of their owners: the assembly report, and the digest it was built from."""
    txt = io.open(OWNER, encoding="utf-8").read()
    out = {}
    dig = json.load(io.open(os.path.join(os.path.dirname(HERE), "results_digest.json"), encoding="utf-8"))
    out["quantities"] = dig["n_quantities"]
    m = re.search(r'CHECK 3 bindings: (\d+) bound', txt)
    if m:
        out["bindings"] = int(m.group(1))
    m = re.search(r'CHECK 1 coverage: cited (\d+) distinct keys; missing (\d+)', txt)
    if m:
        out["entries"] = int(m.group(1))
        out["missing"] = int(m.group(2))
    m = re.search(r'bibliography: (\d+) entries', txt)
    if m:
        out["bibliography"] = int(m.group(1))
    return out


def main():
    own = owner_counts()
    print("owner: artefacts/assembly/assembly-report.txt")
    for k in sorted(own):
        print("  %-14s %d" % (k, own[k]))
    if "bindings" not in own or "entries" not in own:
        print("COUNTS: FAIL -- the owner does not print the counts this checker reads")
        return 1
    rows, bad = [], []
    for rel, pat, which in CARRIERS:
        p = os.path.join(PKG, rel)
        txt = io.open(p, encoding="utf-8").read()
        hits = re.findall(pat, txt)
        rows.append((rel, pat, which, hits))
        for h in hits:
            if int(h) != own[which]:
                bad.append("%s: %r states %s, the assembly prints %d" % (rel, pat, h, own[which]))
    print("\ncarriers read (the declared phrasings, so the scan's own reach is visible):")
    for rel, pat, which, hits in rows:
        print("  %-16s %-34s -> %-8s %s" % (rel, pat, which, hits or "-- not present --"))
    print()
    if bad:
        for b in bad:
            print("COUNTS: FAIL -- " + b)
        return 1
    print("COUNTS: PASS -- %d carrier reading(s) agree with the owner" %
          sum(len(h) for _, _, _, h in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
