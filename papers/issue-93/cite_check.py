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


BIB_HEAD = re.compile(r"(?m)^#{1,6}\s*(?:\d+\.?\s*)?References\s*$", re.I)
BIB_ENTRY = re.compile(r"(?m)^\[(\d+)\]\s")
NUMCITE = re.compile(r"\[(\d+(?:[ \t]*,[ \t]*\d+)*)\]")


def num_index(texts, keys):
    """n -> key, read from the carrier's OWN numbered bibliography (the product's), or `(None, [])`.

    Why this exists.  The product cites by NUMBER -- the key the bibliography prints -- because the journal's
    citation bar is read in the text (*Citation mechanics*: every entry carries an in-text key matching the
    bibliography, and an entry cited by name or by bare arXiv id does not discharge coverage).  Every check this
    package had read the PARTS, which cite `[@key]`; none of them read the product's own keys, so the product
    shipped with `[@key]` tokens and a `[1]`-`[120]` list, `refgate.py` read `covered=1/120`, and the bar read
    green (measured 2026-10-01 at `d77e974`; the rendering is fixed in `research/assemble.py`, and this is the
    reader that would have caught it).

    An entry is resolved by its LINK, not by its title: the entry prints `url`, and the link is the one field that
    names the record -- a key is a mnemonic the text carries and the entry never prints.  An entry whose link
    matches no record is RETURNED as unresolved rather than dropped: a bibliography line nobody can key is the
    same defect as a citation to nothing, and a reader that skips what it cannot parse reports green on a
    narrower object (the Class 116 family).
    """
    bib = None
    for _lab, text in texts:
        heads = [m.start() for m in BIB_HEAD.finditer(text)]
        if heads:
            bib = text[heads[-1]:]
    if bib is None:
        return None, []
    link2key = {}
    for k, rec in keys.items():
        for u in ((rec.get("url") or "").strip(), (rec.get("identifier") or "").strip()):
            if u:
                link2key.setdefault(u, k)
    longest = sorted(link2key, key=len, reverse=True)
    marks = list(BIB_ENTRY.finditer(bib))
    idx, unresolved = {}, []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(bib)
        entry = bib[m.end():end]
        num = int(m.group(1))
        hit = next((link2key[u] for u in longest if u in entry), None)
        if hit:
            idx[num] = hit
        else:
            unresolved.append(num)
    return idx, unresolved


def body_of(text):
    """The carrier's prose: everything before its own bibliography.  The numbered list's own `[n]` markers are
    entry markers, and reading them as citations would make every record cite itself and mask a real uncited one."""
    head = BIB_HEAD.search(text)
    return text[:head.start()] if head else text


def scan(texts, index=None):
    """Return the citation order (first appearance) and every occurrence.

    Two forms, one rule.  The parts cite `[@key]`; the product cites the bibliography's number, resolved through
    the product's own list (`index`).  Both limbs are read where they are the carrier's form, and a bracket whose
    numbers name no entry is left out here and reported by `report` as a bracket, not silently read as a citation.
    """
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
    if index:
        for label, text in texts:
            for m in NUMCITE.finditer(unquote(body_of(text))):
                nums = [int(x) for x in m.group(1).split(",")]
                if not all(n in index for n in nums):
                    continue
                for n in nums:
                    occ.append((label, index[n]))
                    if index[n] not in order:
                        order.append(index[n])
    return order, occ


def stray(texts, index):
    """Bracket groups that name no entry: a prose range such as `[0, 1]`, or a mistyped citation.  Reported, not
    resolved -- the journal's own gate calls these AMBIGUOUS and hands them to the author's report."""
    out = []
    for label, text in texts:
        for m in NUMCITE.finditer(unquote(body_of(text))):
            nums = [int(x) for x in m.group(1).split(",")]
            if not all(n in index for n in nums):
                out.append((label, m.group(0)))
    return out


def report(texts, keys, index=None, unresolved_entries=None):
    if index is None:
        index, unresolved_entries = num_index(texts, keys)
    order, occ = scan(texts, index)
    bad_cites = malformed(texts)
    unknown = [k for k in order if k not in keys]
    uncited = [k for k in keys if k not in set(order)]
    range_brackets = stray(texts, index) if index else []
    lines = []
    obj = ("the product manuscript.md" if PARTS == [PRODUCT] else "%d part(s)" % len(texts))
    lines.append("%s | citations %d | distinct keys %d of %d built records"
                 % (obj, len(occ), len(order), len(keys)))
    lines.append("IN-TEXT KEY %s -- %s"
                 % ("numeric, resolved through the product's own bibliography" if index
                    else "key form (the carrier carries no bibliography)",
                    "entries keyed %d of %d" % (len(index), len(index) + len(unresolved_entries or []))))
    if unresolved_entries:
        lines.append("            entries whose link names no record: %s" % unresolved_entries[:8])
    lines.append("BRACKETS    bracket group(s) naming no entry (prose ranges, not citations): %d %s"
                 % (len(range_brackets), [b for _l, b in range_brackets[:8]]))
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
                                                       malformed=bad_cites, index=index,
                                                       stray=range_brackets)


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
        # And the plant is written in the CARRIER's own alphabet: the parts cite `[@key]`, the product cites
        # the bibliography's number, and a plant in the other alphabet changes nothing read (Class 119).
        victim = stats["order"][0]
        joined = "".join(t for _l, t in texts)
        if "[@" + victim + "]" in joined:
            mut = [(lab, t.replace("[@" + victim + "]", "[@" + victim + "_renamed]")) for lab, t in texts]
            before, after = joined, "".join(t for _l, t in mut)
            if before == after:
                print("\nSELFTEST  MUTATION INERT (key %r not found as a bracketed citation)" % victim)
                return 1
            ok2, _l2, st2 = report(mut, keys)
            caught = (not ok2) and st2["unknown"] == [victim + "_renamed"]
            print("\nSELFTEST  renamed [@%s] -> %s" % (victim, "caught" if caught else "MISSED"))
            if not caught:
                rc = 1
        else:
            index = stats["index"] or {}
            inv = {k: n for n, k in index.items()}
            if victim not in inv:
                print("\nSELFTEST  MUTATION INERT (the first cited key carries no number in the product)")
                return 1
            num = inv[victim]

            def rewrite(pred):
                out = []
                for lab, t in texts:
                    head = BIB_HEAD.search(t)
                    body, bib = (t[:head.start()], t[head.start():]) if head else (t, "")
                    out.append((lab, pred(body) + bib))
                return out

            # Limb 1 (resolution): the bracket that cites the first key is broken.
            broken = rewrite(lambda b: re.sub(r"\[%d\]" % num, "[%d]" % (num + 1000), b, count=1))
            if "".join(t for _l, t in broken) == joined:
                print("\nSELFTEST  MUTATION INERT (bracket [%d] is not in the product's prose)" % num)
                return 1
            _ok, _l, st = report(broken, keys)
            caught = any(b == "[%d]" % (num + 1000) for _l, b in st["stray"])
            print("SELFTEST  broke [%d] -> %s" % (num, "caught" if caught else "MISSED"))
            if not caught:
                rc = 1
            # Limb 2 (coverage): every in-text key is collapsed onto entry 1, so 119 records lose their citation.
            collapsed = rewrite(lambda b: NUMCITE.sub("[1]", b))
            _ok2, _l2, st2 = report(collapsed, keys)
            live = len(st2["uncited"]) >= len(keys) - 1
            print("SELFTEST  collapsed every citation to [1] -> %s"
                  % ("coverage limb live (%d uncited)" % len(st2["uncited"]) if live else "INERT"))
            if not live:
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
