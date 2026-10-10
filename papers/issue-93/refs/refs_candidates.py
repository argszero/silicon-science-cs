#!/usr/bin/env python3
"""Dump candidate records from #93's committed pools, grouped by the query that returned them, compactly.

Usage: python3 refs_candidates.py [pass1|pass2|all] [per_query]
Prints: id | year | primary | title | summary(180 chars) -- so a selection can be authored from the RECORDS,
never from memory of them.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
which = sys.argv[1] if len(sys.argv) > 1 else "all"
per = int(sys.argv[2]) if len(sys.argv) > 2 else 6


def emit(label, rows, seen):
    print("\n### %s" % label)
    shown = 0
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        print("  %-11s %s %-9s | %s" % (r["id"], r.get("year") or "????", r.get("primary", "")[:9],
                                        " ".join((r.get("title") or "").split())[:104]))
        print("      %s" % " ".join((r.get("summary") or "").split())[:185])
        shown += 1
        if shown >= per:
            break


def main():
    seen = set()
    if which in ("pass2", "all"):
        p2 = json.loads(io.open(os.path.join(HERE, "refs_raw2.json"), encoding="utf-8").read())
        for lab, blk in sorted(p2["arxiv"].items()):
            emit("pass2 %s (%s)" % (lab, blk["query"]), blk["rows"], seen)
    if which in ("pass1", "all"):
        p1 = json.loads(io.open(os.path.join(HERE, "refs_raw.json"), encoding="utf-8").read())
        for lab, blk in sorted(p1["arxiv"].items()):
            if lab.endswith(("-approval", "-oversight", "-escalation", "-aicontrol", "-defer", "-abstention",
                             "-hijack", "-substitution", "-binding", "-provenance", "-toctou", "-rendering",
                             "-fatigue", "-approvalfatigue", "-oob", "-scalable")):
                emit("pass1 %s (%s)" % (lab, blk["query"]), blk["rows"], seen)
    cl = json.loads(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8").read())
    print("\n### classic (Crossref, matched)")
    for t, v in sorted(cl["queries"].items()):
        m = v.get("matched")
        if m:
            print("  %-46s %s | %s" % (m["doi"], m.get("year"), m["title"][:80]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
