#!/usr/bin/env python3
"""Issue #120 -- assemble the manuscript and number its reference list.

Reads the two manuscript parts (both written with `@<bare-id>` citation keys), finds the keys in
order of first appearance, numbers them, rewrites the in-text citations, and renders the reference
list from the curated + metadata artefacts.

Nothing about a reference is typed here: the title is the curated title (which the metadata route
re-read from the index and matched), the authors and year come from refs/meta.json (fetched from the
index that owns each id), and the difference line comes from curated.json.  A key with no curated
entry is a hard error; a curated entry no part cites is reported, because an uncited entry does not
count toward the reference bar.

Usage:  /usr/bin/python3 build_manuscript.py
Out:    manuscript.md   (+ a summary line per check)
"""
import json
import re
import sys

PARTS = ["manuscript.src.md"]
OUT = "manuscript.md"
MARKER = "<!-- REFERENCES -->"
CITE = re.compile(r"@([A-Za-z0-9][A-Za-z0-9./\-]*)")


def author_form(names):
    """'Given Family' -> 'Family, I.'; a single token prints alone (never padded to an initial)."""
    out = []
    for n in names:
        toks = n.split()
        if len(toks) == 1:
            out.append(toks[0])
        else:
            out.append("%s, %s." % (toks[-1], toks[0][0].upper()))
    return out


def link(e):
    return "https://doi.org/%s" % e["bare"] if e["id"].startswith("10.") else \
           "https://arxiv.org/abs/%s" % e["bare"]


def main():
    text = "\n".join(open(p, encoding="utf-8").read() for p in PARTS)
    cur = {e["bare"]: e for e in json.load(open("refs/curated.json"))["entries"]}
    meta = json.load(open("refs/meta.json"))["meta"]

    order, seen = [], set()
    for m in CITE.finditer(text):
        k = m.group(1)
        if k not in cur:
            print("FATAL: citation key @%s has no curated entry" % k)
            return 1
        if k not in seen:
            seen.add(k)
            order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}

    def repl(m):
        return "[%d]" % num[m.group(1)]

    body = CITE.sub(repl, text)
    # collapse adjacent groups: [3][4] -> [3, 4]  (only for directly abutting groups)
    body = re.sub(r"\[(\d+)\](?:\[(\d+)\])+",
                  lambda m: "[" + ", ".join(m.group(0)[1:-1].split("][")) + "]", body)

    lines = []
    for k in order:
        e, m = cur[k], meta.get(k)
        if m is None:
            print("FATAL: no metadata for %s" % k)
            return 1
        auth = author_form(m["authors"])
        if len(auth) > 3:
            astr = ", ".join(auth[:3]) + ", et al."
        else:
            astr = ", ".join(auth[:-1] + [auth[-1]]) if len(auth) > 1 else auth[0]
        lines.append("%d. %s (%s). *%s*. %s. %s — %s"
                     % (num[k], astr, m["year"], e["title"],
                        "DOI: %s" % k if k.startswith("10.") else "arXiv:%s" % k,
                        link(e), e["diff"]))
    refs = "## References\n\n" + "\n\n".join(lines) + "\n"
    body = body.replace(MARKER, refs)

    open(OUT, "w", encoding="utf-8").write(body)
    uncited = [k for k in cur if k not in seen]
    print("parts read      : %s" % ", ".join(PARTS))
    print("cited entries   : %d of %d curated" % (len(order), len(cur)))
    print("uncited entries : %d %s" % (len(uncited), uncited[:12]))
    print("references block: %d entries in one ## References section" % len(order))
    print("-> %s (%d chars)" % (OUT, len(body)))
    return 1 if uncited else 0


if __name__ == "__main__":
    sys.exit(main())
