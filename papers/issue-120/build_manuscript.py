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

# One line of prose the reader MEETS at the head of the list, declaring what the difference lines
# are scoped to.  The curated difference line is generated from the entry's ROLE (refs_curate.py's
# diff_for), so a role class of 46 works carries ONE sentence 46 times: honest about the class,
# but a reader can take it for a claim read off each individual paper.  The editorial return of
# 2026-10-10 named exactly that (120 of 129 entries role-templated), and it offered this as the
# alternative to writing 129 entry-specific lines -- which would mean stating a difference for each
# of 129 works that the author has not read, i.e. inventing them.  So the form is DECLARED.
ROLE_LABEL = {
    "tiering": ("memory-tiering systems", "the application"),
    "policy": ("deployed replacement policies", None),
    "profile": ("treatments of the recurrence profile", None),
    "adjacent": ("adjacent caches (KV / buffer pool / storage / edge)", None),
    "construct": ("treatments of the offline optimum / the ceiling", "the construct"),
    "theory": ("competitive-analysis results for paging", None),
}


def refs_note(cur, order):
    """The declaration the reader meets above the entry list -- counts read from the curated set,
    never typed, so the sentence cannot drift from the list it describes."""
    counts = {}
    for k in order:
        r = cur[k]["role"]
        counts[r] = counts.get(r, 0) + 1
    parts = []
    for r in sorted(counts, key=lambda r: (-counts[r], r)):
        label, gloss = ROLE_LABEL.get(r, (r, None))
        parts.append("%d %s" % (counts[r], label + (" (%s)" % gloss if gloss else "")))
    return (
        "**The difference lines are scoped by role class, and this is the intended house style of "
        "this list.** Each of the %d entries is assigned the role its work plays in this paper's "
        "argument -- %s -- and its one-line *difference from this work* states the difference that "
        "**role class** makes from this work, rather than a claim read off that one paper. The "
        "specific differences from the closest works are stated in Sections 1-2, and an entry whose "
        "difference is not its class's states it in its own words."
        % (len(order), ", ".join(parts)))



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
        # house style: the entry marker is `[n]`, matching the in-text citation form and the four
        # published bibliographies (refgate reads `[n]`, `n.` or `n)` at the start of a line).
        lines.append("[%d] %s (%s). *%s*. %s. %s — %s"
                     % (num[k], astr, m["year"], e["title"],
                        "DOI: %s" % k if k.startswith("10.") else "arXiv:%s" % k,
                        link(e), e["diff"]))
    refs = "## References\n\n" + refs_note(cur, order) + "\n\n" + "\n\n".join(lines) + "\n"
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
