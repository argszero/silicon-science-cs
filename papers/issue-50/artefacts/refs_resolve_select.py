#!/usr/bin/env python3
"""Bind the authored selection to records the controlled scan returned.

An anchor that resolves to no record, or to more than one, is reported and the
run fails -- so no bibliography entry can be typed in: each is bound to a
record the scan produced.  Ambiguity is reported rather than resolved silently,
because "the first match" is how a wrong work enters a bibliography.
"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from refs_select_part1 import PART1
from refs_select_part2 import PART2
from refs_select_part3 import PART3

SEL = PART1 + PART2 + PART3

# A record whose title carries a supplement marker is the supplement of a work,
# not the work: it must not be able to answer a binding (R339/R340 family).
SUPPLEMENTARY = re.compile(r"(_supp?\d+|\.pdf$|/mm\d+$|\bsupplement)", re.I)

def main():
    raw = json.load(io.open(os.path.join(HERE, "bib_pool_v50.json"), encoding="utf-8"))["records"]
    pool = [r for r in raw if not SUPPLEMENTARY.search(r["title"])]
    print("pool %d records, %d dropped as supplementary material" % (len(raw), len(raw) - len(pool)))
    by_key = {}
    unresolved, ambiguous, dup = [], [], []
    for row in SEL:
        key, anchor, sec, diff = row[0], row[1], row[2], row[3]
        explicit = row[4] if len(row) > 4 else None
        if key in by_key:
            dup.append(key); continue
        if explicit:
            hits = [r for r in pool if explicit.lower() in str(r["id"]).lower()]
        else:
            hits = [r for r in pool
                    if anchor.lower() in r["title"].lower()]
        if not hits:
            unresolved.append((key, anchor)); continue
        if len(hits) > 1:
            ambiguous.append((key, anchor, [h["title"][:70] for h in hits]))
            continue
        r = hits[0]
        by_key[key] = {
            "key": key, "section": sec, "difference": diff,
            "anchor": anchor, "locator": r["id"],
            "locator_kind": "arXiv" if r["source"] == "arxiv" else "DOI",
            "title": r["title"], "year": r.get("year"),
            "authors": r.get("authors") or [], "venue": r.get("venue", ""),
            "source": r["source"], "seen_in": r.get("seen_in", [r.get("query", "")]),
        }
    print("selection rows %d ; bound %d ; unresolved %d ; ambiguous %d ; duplicate keys %d"
          % (len(SEL), len(by_key), len(unresolved), len(ambiguous), len(dup)))
    for k, a in unresolved:
        print("  UNRESOLVED  %-22s %s" % (k, a))
    for k, a, ts in ambiguous:
        print("  AMBIGUOUS   %-22s %s" % (k, a))
        for t in ts:
            print("        -", t)
    if dup:
        print("  DUPKEY      ", dup)
    if unresolved or ambiguous or dup:
        print("\nRESULT: FAILED -- fix the anchors and rerun")
        return 1
    out = {"what": "issue #50 authored bibliography selection, bound to the controlled pool",
           "n": len(by_key), "rows": [by_key[r[0]] for r in SEL if r[0] in by_key]}
    with io.open(os.path.join(HERE, "refs_selection_v50.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print("by section:", json.dumps(Counter(v["section"] for v in by_key.values()).most_common()))
    print("locator kinds:", json.dumps(Counter(v["locator_kind"] for v in by_key.values()).most_common()))
    print("RESULT: OK -> refs_selection_v50.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
