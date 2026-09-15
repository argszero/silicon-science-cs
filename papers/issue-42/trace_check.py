#!/usr/bin/env python3
"""Check the trace chain: manuscript -> figures -> artefacts -> registry.

Where validate.py asserts VALUES, this asserts the chain that makes the values checkable:
every figure the manuscript references exists, no figure is orphaned, every citation number
resolves to a verified reference, and the bibliography has no gaps.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    doc = io.open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()
    fig = sorted(os.listdir(os.path.join(HERE, "figures")))
    refs = json.load(io.open(os.path.join(HERE, "artefacts", "refs_ordered.json"), encoding="utf-8"))
    fails = []

    # 1. every referenced figure exists on disk
    referenced = re.findall(r"\]\(figures/([A-Za-z0-9_.\-]+)\)", doc)
    missing = [f for f in referenced if not os.path.exists(os.path.join(HERE, "figures", f))]
    print("   figures: %d referenced, %d on disk, missing=%s" % (len(referenced), len(fig), missing or "none"))
    if missing:
        fails.append("missing figures: %s" % missing)

    # 2. no orphaned figure (a file nobody cites is unreviewed evidence)
    orphans = [f for f in fig if f not in referenced]
    print("   orphaned figures: %s" % (orphans or "none"))
    if orphans:
        fails.append("orphan figures: %s" % orphans)

    # 3. every citation number resolves, and the numbering is dense 1..N
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)(?:\s*,\s*\d+)*\]", doc)})
    nums = [r["n"] for r in refs]
    dense = nums == list(range(1, len(nums) + 1))
    in_range = all(1 <= c <= len(nums) for c in cited)
    print("   bibliography: %d entries, dense=%s, max citation=%d, all in range=%s"
          % (len(nums), dense, max(cited) if cited else 0, in_range))
    if not dense:
        fails.append("bibliography numbering has gaps")
    if not in_range:
        fails.append("citation number out of range")

    # 4. every reference carries a positive verification record
    unverified = [r["key"] for r in refs if r.get("verdict") != "verified"]
    print("   unverified references: %s" % (unverified or "none"))
    if unverified:
        fails.append("unverified: %s" % unverified)

    # 5. the reference threshold
    print("   reference count: %d (threshold 100)" % len(nums))
    if len(nums) < 100:
        fails.append("reference count %d below threshold 100" % len(nums))

    # 6. every reference is actually cited in the body (numbering is by first appearance,
    #    so a gap in citations is exactly a reference that is never used)
    unused = [r["n"] for r in refs if r["n"] not in cited]
    print("   references never cited: %s" % (unused or "none"))
    if unused:
        fails.append("uncited references: %s" % unused)

    if fails:
        print("\nTRACE FAILED:")
        for f in fails:
            print("   -", f)
        return 1
    print("TRACE: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
