#!/usr/bin/env python3
"""Assemble manuscript.md from the part files, numbering citations by first appearance.

The parts carry symbolic keys (@key or [@k1; @k2]); this script assigns numbers in order of
first appearance and emits the bibliography from artefacts/refs_final.json.  It FAILS LOUDLY
if a cited key is not in the verified reference set, or if a verified reference is never
cited -- an uncited reference is padding and does not count toward the reference threshold.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROUP = re.compile(r"\[@\{?([a-z0-9_]+)\}?(?:\s*;\s*@\{?([a-z0-9_]+)\}?)*\]")


def main():
    txt = "".join(io.open(os.path.join(HERE, "manuscript_part%d.md" % i), encoding="utf-8").read()
                  for i in (1, 2, 3))
    refs = {r["key"]: r for r in json.load(
        io.open(os.path.join(HERE, "artefacts", "refs_final.json"), encoding="utf-8"))}
    order, num = [], {}

    def assign(k):
        if k not in num:
            num[k] = len(order) + 1
            order.append(k)
        return num[k]

    body = GROUP.sub(lambda m: "[" + ", ".join(
        str(assign(k)) for k in re.findall(r"@\{?([a-z0-9_]+)\}?", m.group(0))) + "]", txt)
    unknown = [k for k in num if k not in refs]
    uncited = [k for k in refs if k not in set(num)]
    if unknown or uncited:
        print("ASSEMBLY FAILED: unknown keys cited=%s ; verified refs uncited=%s" % (unknown, uncited))
        return 1
    if len(order) < 100:
        print("ASSEMBLY FAILED: only %d references (threshold is 100)" % len(order))
        return 1
    bib = []
    for k in order:
        r = refs[k]
        au = r.get("authors") or []
        astr = ", ".join(au[:3]) + (", et al." if len(au) > 3 else "")
        bib.append("[%d] %s. %s. %s, %s. DOI: %s" % (num[k], astr or "(no author metadata)",
                    r["title"].rstrip("."), r.get("venue") or "preprint", r.get("year"), r.get("doi")))
    doc = body.replace("@@REFERENCES@@", "\n".join(bib))
    io.open(os.path.join(HERE, "manuscript.md"), "w", encoding="utf-8").write(doc)
    print("manuscript.md assembled: %d references, %d figures, %d bytes"
          % (len(order), doc.count("](figures/"), len(doc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
