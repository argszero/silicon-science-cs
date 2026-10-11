#!/usr/bin/env python3
"""check_references (#126, R552) -- the reference section read as the PRODUCT, not as the source.

The bibliography is produced by a three-stage pipeline (build_refs -> refs_build_display ->
refs_render), and every stage agrees with itself by construction: the body is numbered by the same
file that numbers the record layer, the record layer is rendered by a renderer that reads it, and a
script that wrote both would pass any check that read only one of them (Class 118(b): a plant that
re-renders the mutated object satisfies itself).  So this file reads the OBJECT A READER GETS --
`manuscript.md` -- and checks it against the two claims a reader is entitled to:

  R1  exactly one `## References` section, and it is the file's last section;
  R2  its entries are numbered 1..n, in order, once each (the numbers the body cites);
  R3  the entries are separated from one another by a blank line -- consecutive entry lines are ONE
      paragraph to a CommonMark renderer, so a list of 107 entries prints as one unbroken block
      (measured in this journal: four published bibliographies, three of them read as 1 or 2
      paragraphs; `refgate.py` prints the counts that read it);
  R4  every entry closes with its one-line `Difference: ...` (the house style's last component);
  R5  every entry carries a resolvable URL -- `https://doi.org/...` or `https://arxiv.org/abs/...` --
      and never a bare DOI string and never a URL inside backticks;
  R6  the body CITES every number in the section and no number outside it (both directions: an
      uncited entry is padding, and a citation with no entry is a dangling reference);
  R7  no entry prints an author component in the capitals a registry stores it in, and no entry
      carries an XML/HTML character reference (`O&#39;Brien`);
  R8  the section is the renderer's output for THIS record layer: the entry numbered k carries the
      URL of `references.json`'s entry with key k.  This is the cross-layer read no single stage can
      make, because each stage is consistent with itself by construction.

Usage: python3 check_references.py [--selftest]
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
REC = os.path.join(HERE, "references.json")

HDR = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
ENTRY = re.compile(r"(?m)^\[(\d+)\] ")
URL = re.compile(r"https://(?:doi\.org|arxiv\.org/abs)/\S+")
ESC = re.compile(r"&#?[0-9A-Za-z]+;")


def blocks(sec):
    """The entries as a CommonMark renderer groups them: a blank line starts a new block."""
    out, cur = [], []
    for line in sec.split("\n")[1:]:
        if not line.strip():
            if cur:
                out.append("\n".join(cur))
                cur = []
            continue
        cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def analyse(text, recs):
    """Return the list of problems.  `text` and `recs` are arguments so the plants can mutate the
    object under test rather than the repository."""
    p = []
    heads = list(HDR.finditer(text))
    if len(heads) != 1:
        return ["R1 the file carries %d `## References` heading(s), not 1" % len(heads)]
    head = heads[0]
    body, sec = text[:head.start()], text[head.end():]
    if "\n## " in sec:
        p.append("R1 the references section is not the file's last section")
    bs = blocks(sec)
    nums = [int(m.group(1)) for m in ENTRY.finditer(sec)]
    if nums != list(range(1, len(nums) + 1)):
        p.append("R2 the entry numbers are not 1..n in order: %s" % nums[:12])
    # R3: one entry per block.  A block carrying two entry starts is two entries in one paragraph;
    # a block carrying none is a continuation line of the entry above it, which is normal wrapping.
    for i, b in enumerate(bs, 1):
        starts = len(re.findall(r"(?m)^\[\d+\] ", b))
        if starts > 1:
            p.append("R3 block %d carries %d entries (they are one paragraph to a renderer): %r"
                     % (i, starts, b[:60]))
    flat = " ".join(re.sub(r"\s+", " ", b) for b in bs)
    # R4/R5/R7: per entry, on the entry's own block
    ents = []
    for b in bs:
        m = re.match(r"^\[(\d+)\] ", b)
        if m:
            ents.append((int(m.group(1)), b))
    if len(ents) != len(nums):
        p.append("R4 %d entry blocks for %d entry starts" % (len(ents), len(nums)))
    for k, b in ents:
        flatb = re.sub(r"\s+", " ", b)
        if "Difference: " not in flatb:
            p.append("R4 entry [%d] closes with no `Difference: ...` clause" % k)
        if not URL.search(flatb):
            p.append("R5 entry [%d] carries no resolvable https URL" % k)
        if "`" in flatb:
            p.append("R5 entry [%d] carries a backticked token" % k)
        au = re.match(r"^\[%d\] (.*?) \((?:19|20)\d\d\)\." % k, flatb)
        if au:
            for comp in au.group(1).split("; "):
                letters = [c for c in comp if c.isalpha()]
                if letters and all(c.isupper() for c in letters):
                    p.append("R7 entry [%d] prints an ALL-CAPS author component: %r" % (k, comp))
        if ESC.search(flatb):
            p.append("R7 entry [%d] carries a character reference: %r" % (k, ESC.search(flatb).group(0)))
    # R6: cited numbers, both directions
    coded = set(int(x) for x in re.findall(r"\[(\d+)\]", body))
    sec_nums = set(nums)
    for k in sorted(sec_nums - coded):
        p.append("R6 entry [%d] is never cited in the body" % k)
    for k in sorted(coded - sec_nums):
        p.append("R6 the body cites [%d], which has no entry" % k)
    # R8: the section is the renderer's output for THIS record layer
    if recs is not None:
        want = {e["key"]: e["url"] for e in recs}
        for k, b in ents:
            if k in want and want[k] not in re.sub(r"\s+", " ", b):
                p.append("R8 entry [%d] does not carry the record layer's URL %s" % (k, want[k]))
    return p


def load():
    recs = None
    if os.path.exists(REC):
        recs = json.load(io.open(REC, encoding="utf-8"))["entries"]
    return io.open(MS, encoding="utf-8").read(), recs


def main():
    text, recs = load()
    probs = analyse(text, recs)
    for x in probs[:40]:
        print("*** " + x)
    h = HDR.search(text)
    n = len(re.findall(r"(?m)^\[\d+\] ", text[h.end():])) if h else 0
    print("check_references: %d entries, %d problem(s)" % (n, len(probs)))
    return 0 if not probs else 1


def selftest():
    text, recs = load()
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-36s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    def fires(name, mut):
        nonlocal ok
        got = analyse(mut, recs)
        holds(name, bool(got))
        if got:
            print("        -> %s" % got[0][:100])

    holds("clean-manuscript", analyse(text, recs) == [])
    head = HDR.search(text)
    body, sec = text[:head.start()], text[head.end():]
    # R2: renumber one entry so the sequence has a gap
    m = re.search(r"(?m)^\[2\] ", sec)
    fires("R2-plant-renumbered", text[:head.end()] + sec[:m.start()] + sec[m.start():].replace("[2]", "[9]", 1))
    # R3: remove the blank line between the first two entries
    i = sec.find("\n\n[2] ")
    fires("R3-plant-no-blank-line", text[:head.end()] + sec[:i] + sec[i + 1:])
    # R4: strip one entry's Difference clause
    j = sec.find("Difference:")
    k = sec.find("\n\n", j)
    fires("R4-plant-no-difference", text[:head.end()] + sec[:j] + sec[k:])
    # R5: backtick a URL in one entry
    fires("R5-plant-backticked-url", text[:head.end()] + sec.replace("https://doi.org/10.1007/bf01397083",
                                                                     "`https://doi.org/10.1007/bf01397083`", 1))
    # R6: delete one body citation -- the entry it named becomes uncited
    for num in range(1, len(re.findall(r"(?m)^\[\d+\] ", sec)) + 1):
        if ("[%d]" % num) in body:
            fires("R6-plant-uncited-entry",
                  text[:head.start()].replace("[%d]" % num, "") + text[head.start():])
            break
    # and the other direction: a citation with no entry
    fires("R6-plant-dangling-citation",
          text[:head.start()].replace("[1]", "[999]", 1) + text[head.start():])
    # R7: print one author component in capitals
    fires("R7-plant-caps-author", text[:head.end()] + re.sub(r"(?m)^\[1\] [^\n]*? \(", "[1] DEKKER, T. J. (", sec, count=1))
    # R8: point one entry at another record's URL
    if recs:
        fires("R8-plant-wrong-url", text[:head.end()] + sec.replace(recs[0]["url"], recs[1]["url"], 1))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
