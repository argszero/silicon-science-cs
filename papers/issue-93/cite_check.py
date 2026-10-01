#!/usr/bin/env python3
"""#93 R417 -- the manuscript's citation keys: resolve every in-text key, and report coverage.

The manuscript cites by KEY (`[@wang2026]`, `[@irshad2026;@kumar2026]`); the house bibliography is numbered
`[1]`-`[n]` **in the order of first citation**, which this script derives from the finished text.  Two
properties are read, and they are read separately because they fail differently:

  RESOLUTION  every key in the text names a built record.  A key that names nothing is an ERROR (a citation to
              a record that does not exist, which is the defect the journal's authenticity bar is about).
  COVERAGE    how many of the built records the text actually cites.  The journal's bar requires every entry to
              be genuinely cited in the body, so an uncited record is padding -- reported here for every round,
              and required to reach zero before submission.

Run:  python3 cite_check.py                     (resolve + coverage + the numbering)
      python3 cite_check.py --selftest          (plus a mutation: a key renamed in a copy must be caught)
"""
import copy
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Two contexts, one rule: in the WORKING tree this script sits in `manuscript/` beside the parts; in the shipped
# PACKAGE it sits at the root beside the product.  The product is preferred when it is there, because the product
# is what a reader has -- reading the parts in the package would be checking a source the package does not ship.
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "manuscript" else HERE
KEYS = os.path.join(ROOT, "refs", "refs_keys.json")
PRODUCT = os.path.join(ROOT, "manuscript.md")
PARTS = ([PRODUCT] if os.path.exists(PRODUCT)
         else sorted(glob.glob(os.path.join(HERE, "part*.md"))))

CITE = re.compile(r"\[@([^\]]+)\]")
# A citation whose bracket is MALFORMED is invisible to the regex above, and that is how a real defect survived a
# green run: `[(@modic2014;@brodersen2013;@marteau1989)]` -- a `[` followed by `(` -- matched NOTHING, so three
# citations were silently unread while the report said "0 unknown".  The limb below is the other side of the same
# property: every `@key`-shaped token must be inside a well-formed bracket, and a stray one is an ERROR.  A reader
# that skips what it cannot parse is a check narrower than its object (the Class 114 family).
ANY_AT = re.compile(r"@[A-Za-z][A-Za-z0-9_.-]*")
CODE = re.compile(r"`[^`\n]*`")


def unquote(text):
    """Blank out inline code spans, keeping every offset: `[(@a;@b;@c)]` inside backticks is a QUOTATION of a
    defect, not a citation.  Found by self-reference: the section that documents the malformed limb quotes the
    malformed form, and the limb then fired on its own repair's documentation (4 hits, R427).  Quoted tokens are
    counted and reported rather than silently dropped -- a citation that exists ONLY inside a code span has to be
    visible to the author, and the coverage limb would still refuse its record as uncited.
    """
    return CODE.sub(lambda m: " " * len(m.group(0)), text)


def quoted(texts):
    """The `@`-shaped tokens INSIDE inline code, counted per text.  The first version of this counted every token
    of a text that happened to contain one inside code (`214`, against 4 real hits) -- a counter whose object was
    not the object it named, and it is the same defect family as the resolution hole `verify_s5.py` had at the same
    hour: a quantity read off the wrong set."""
    out = []
    for lab, text in texts:
        spans = [m.span() for m in CODE.finditer(text)]
        n = sum(1 for m in ANY_AT.finditer(text) if any(s <= m.start() and m.end() <= e for s, e in spans))
        if n:
            out.append((lab, n))
    return out


def malformed(texts):
    """Every `@key`-shaped occurrence NOT consumed by a well-formed `[@...]` citation: (part, snippet)."""
    out = []
    for label, text in texts:
        text = unquote(text)
        spans = [m.span() for m in CITE.finditer(text)]
        for m in ANY_AT.finditer(text):
            if any(s <= m.start() and m.end() <= e for s, e in spans):
                continue
            lo, hi = max(0, m.start() - 30), min(len(text), m.end() + 30)
            out.append((label, text[lo:hi].replace("\n", " ")))
    return out


def load_keys():
    return json.loads(io.open(KEYS, encoding="utf-8").read())["keys"]


def scan(texts):
    """Return the citation order (first appearance) and every occurrence."""
    order, occ = [], []
    for label, text in texts:
        for m in CITE.finditer(unquote(text)):
            for k in m.group(1).split(";"):
                k = k.strip().lstrip("@").strip()
                if not k:
                    continue
                occ.append((label, k))
                if k not in order:
                    order.append(k)
    return order, occ


def report(texts, keys):
    order, occ = scan(texts)
    bad_cites = malformed(texts)
    unknown = [k for k in order if k not in keys]
    uncited = [k for k in keys if k not in set(order)]
    lines = []
    obj = ("the product manuscript.md" if PARTS == [PRODUCT] else "%d part(s)" % len(texts))
    lines.append("%s | citations %d | distinct keys %d of %d built records"
                 % (obj, len(occ), len(order), len(keys)))
    lines.append("RESOLUTION  unknown keys %d %s" % (len(unknown), unknown[:5]))
    lines.append("MALFORMED   citation-shaped token(s) outside a well-formed bracket: %d" % len(bad_cites))
    for lab, snip in bad_cites[:5]:
        lines.append("            %s: ...%s..." % (lab, snip))
    nq = sum(n for _lab, n in quoted(texts))
    lines.append("QUOTED      citation-shaped token(s) inside inline code, not counted as citations: %d" % nq)
    lines.append("COVERAGE    uncited records %d of %d (bar: 0 at submission)" % (len(uncited), len(keys)))
    if uncited:
        lines.append("            first uncited: %s" % uncited[:8])
    lines.append("NUMBERING (first-citation order; this is the [n] the bibliography renders in)")
    for i, k in enumerate([k for k in order if k in keys], 1):
        lines.append("  [%d] %s  %s (%s)" % (i, k, keys[k]["title"][:58], keys[k]["year"]))
    return (not unknown and not bad_cites), lines, dict(order=order, unknown=unknown, uncited=uncited,
                                                       malformed=bad_cites)


def main():
    keys = load_keys()
    texts = [(os.path.basename(p), io.open(p, encoding="utf-8").read()) for p in PARTS]
    if not texts:
        print("no manuscript parts found under %s" % HERE)
        return 1
    ok, lines, stats = report(texts, keys)
    print("\n".join(lines))
    rc = 0 if ok else 1
    if "--selftest" in sys.argv:
        # A key renamed in a copy must be caught: the check has to fire on the property it names, and an
        # inert mutation (one that changes nothing read) is reported as such rather than counted as a pass.
        victim = stats["order"][0]
        mut = [(lab, t.replace("[@" + victim + "]", "[@" + victim + "_renamed]")) for lab, t in texts]
        before, after = "".join(t for _l, t in texts), "".join(t for _l, t in mut)
        if before == after:
            print("\nSELFTEST  MUTATION INERT (key %r not found as a bracketed citation)" % victim)
            return 1
        ok2, _l2, st2 = report(mut, keys)
        caught = (not ok2) and st2["unknown"] == [victim + "_renamed"]
        print("\nSELFTEST  renamed [@%s] -> %s" % (victim, "caught" if caught else "MISSED"))
        if not caught:
            rc = 1
        # The malformed limb owes its own cases, two-sided: a bracket the regex cannot read must be caught, and
        # a well-formed citation must NOT be reported as malformed (a check that fires on its own passing case
        # is as useless as one that never fires).
        cases = [
            ("a citation with a malformed bracket is caught, not skipped",
             "[(@" + victim + ")] is a real citation written wrongly", True),
            ("a well-formed citation is NOT reported as malformed",
             "[@" + victim + "] is a real citation written correctly", False),
            ("a citation whose bracket is never closed is caught",
             "an unterminated citation [@" + victim + " runs on to the end of the paragraph", True),
        ]
        for name, text, want_bad in cases:
            got = malformed([("probe", text)])
            ok_case = bool(got) == want_bad
            print("SELFTEST  %-58s %s" % (name[:58], "ok" if ok_case else "MISSED"))
            if not ok_case:
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
