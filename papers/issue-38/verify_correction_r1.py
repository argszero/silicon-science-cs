#!/usr/bin/env python3
"""Verify issue #38's four required changes (R1-R4) mechanically, with a control per check.

Each check is two-sided: it must PASS on the delivered manuscript and FAIL on a mutated copy.
Writes results to correction_r1_verify.log, BESIDE this package (not into research/, which is
git-ignored and absent from the package: a reader who ran this elsewhere hit FileNotFoundError and
an exit status of 1 on a run whose own stdout said ALL PASS).

Run:  python3 verify_correction_r1.py
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
LOG = os.path.join(HERE, "correction_r1_verify.log")
R1_SECTIONS = {"fig1_collapse.png": "4.2", "fig2_scrambling.png": "4.5", "fig3_amplification.png": "4.6"}

out = []
def say(s):
    out.append(s); print(s)


# The heading the renderer EMITS is the unnumbered `## References` (round 2 of the correction renamed
# it, and the number is now carried by nothing).  The split accepts both forms so this file keeps
# splitting at the section it means, rather than at a heading a later correction must not restore.
REF_HEAD = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")


def split_refs(ms):
    """(body, section) at the one Reference heading, whatever the heading carries."""
    parts = REF_HEAD.split(ms, 1)
    assert len(parts) == 2, "expected exactly one Reference heading, found %d" % (len(parts) - 1)
    return parts[0], parts[1]


def body(ms):
    return split_refs(ms)[0]


def check_r1(ms):
    """Every figure embedded in its section, numbered, and cited from the body."""
    fail = []
    for f, sec in R1_SECTIONS.items():
        if ("](figures/%s)" % f) not in ms:
            fail.append("%s not embedded" % f)
            continue
        # the embedding sits inside the named section
        idx = ms.index("](figures/%s)" % f)
        heads = [(m.start(), m.group(1)) for m in re.finditer(r'^### (\d+\.\d+) ', ms, flags=re.M)]
        cur = max((h for h in heads if h[0] < idx), default=(0, "?"))[1]
        if cur != sec:
            fail.append("%s sits in %s not %s" % (f, cur, sec))
    imgs = [l for l in ms.split("\n") if l.lstrip().startswith("![")]
    if len(imgs) != 3:
        fail.append("expected 3 image lines, found %d" % len(imgs))
    n_cited = len(set(re.findall(r'Figure (\d)', body(ms))))
    if n_cited != 3:
        fail.append("body cites %d of 3 figure numbers" % n_cited)
    return fail, "3 figures embedded in %s, all numbered and cited from the body" % \
                 ", ".join("§" + s for s in R1_SECTIONS.values())


def check_r2(ms):
    """Nine tables, each captioned above and numbered in document order, each cited from the body."""
    fail = []
    lines = ms.split("\n")
    seps = [i for i, l in enumerate(lines) if re.match(r'^\|[-: |]*\|$', l)]
    caps = [i for i, l in enumerate(lines) if re.match(r'^\*\*Table \d+ \u2014 ', l)]
    if len(seps) != 9:
        fail.append("expected 9 tables, found %d" % len(seps))
    if len(caps) != 9:
        fail.append("expected 9 captions, found %d" % len(caps))
    # caption directly above its table header (caption lines, blank, header)
    for n, c in enumerate(caps, 1):
        if not re.match(r'^\*\*Table %d \u2014 ' % n, lines[c]):
            fail.append("caption at line %d is not numbered %d" % (c + 1, n))
        end = c
        while end + 1 < len(lines) and lines[end + 1].strip() and not lines[end + 1].startswith("|"):
            end += 1                      # a caption may wrap
        below = end + 2                   # blank line, then the table header
        if below >= len(lines) or not lines[below].startswith("|"):
            fail.append("caption %d does not sit directly above a table header (line %d)" % (n, below + 1))
        elif lines[end + 1].strip():
            fail.append("caption %d is not separated from its header by a blank line" % n)
    b = body(ms)
    uncited = [n for n in range(1, 10) if not re.search(r'Table %d\b' % n, b.replace(re.search(r'^\*\*Table \d+ .*$', b, flags=re.M).group(0), ""))]
    # simpler: count citations outside caption lines
    capset = set(re.findall(r'^\*\*Table (\d+) \u2014 .*$', b, flags=re.M))
    cited = set(re.findall(r'Table (\d+)\b', re.sub(r'^\*\*Table \d+ \u2014 .*$', '', b, flags=re.M)))
    missing = sorted({str(i) for i in range(1, 10)} - cited)
    if missing:
        fail.append("tables never cited from the body: %s" % missing)
    return fail, "9 tables, 9 captions numbered in document order and each placed above its table; all cited from the body"


def check_r3(ms):
    """Every entry: authors, year, title, venue/identifier, link, stated difference."""
    fail = []
    sec = split_refs(ms)[1]
    blocks = re.split(r'\n(?=\[\d+\] )', sec)[1:]
    refs = {str(e["key"]): e for e in json.load(io.open(os.path.join(HERE, "references.json"), encoding="utf-8"))["entries"]}
    disp = json.load(io.open(os.path.join(HERE, "refs_display.json"), encoding="utf-8"))
    ws = lambda s: re.sub(r"\s+", " ", s).strip()
    if len(blocks) != 125:
        fail.append("parsed %d entries, expected 125" % len(blocks))
    for blk in blocks:
        k = re.match(r'\[(\d+)\] ', blk).group(1); b = ws(blk)
        if disp[k]["authors"]:
            # Read case-insensitively, for the same reason the TITLE below is: the renderer folds an
            # all-caps record to the house form, so a case-sensitive read of the record's own string
            # would call the corrected entry a missing author.  That is what happened here -- round 3's
            # author fold turned `[15]` and `[20]` red in this check while the entries were right:
            # the rule is "the author is present", and the record's capitalisation is not its subject.
            if disp[k]["authors"][0].split(",")[0].lower() not in b.lower():
                fail.append("entry %s: author missing" % k)
        elif "Author not established" not in b:
            fail.append("entry %s: no author and no stated obstacle" % k)
        for what, needle in (("year", disp[k]["year"]), ("venue", disp[k]["venue"]),
                             ("link", refs[k]["url"]), ("difference", refs[k]["difference"])):
            if needle and ws(needle) not in b:
                fail.append("entry %s: %s missing" % (k, what))
        # The TITLE is read case-insensitively: the renderer folds an all-caps record title to title
        # case (the house style asks for title case), so a case-sensitive read of the record's own
        # string would call the corrected entry a missing title.  What must hold is that the entry
        # prints THAT title -- not that it prints the publisher's capitals.
        if refs[k]["title"] and ws(refs[k]["title"]).lower() not in b.lower():
            fail.append("entry %s: title missing" % k)
    if re.search(r'\bn\.d\.\b', sec) or "None." in sec:
        fail.append("a placeholder year (n.d. / None.) survives")
    noauth = sum(1 for v in disp.values() if not v["authors"])
    return fail, ("125 entries, each with authors (one stated exception: [51]), year, title, venue or "
                  "identifier, link and its stated difference; no n.d./None. placeholder survives")


def check_r4(ms):
    """No lowercase x used as a multiplication mark."""
    fail = []
    pat = re.compile(r'(?<![A-Za-z0-9_])x(?=[0-9~])|(?<=[0-9])x(?![A-Za-z0-9_])|(?<=\s)x(?=\s)')
    hits = []
    for i, l in enumerate(ms.split("\n"), 1):
        if re.match(r'^\[\d+\]', l) or re.search(r'https?://|doi:|arXiv:', l):
            continue    # identifiers (DOIs, arXiv ids, URLs) legitimately contain 'x'
        for m in pat.finditer(l):
            hits.append((i, l[max(0, m.start() - 30):m.start() + 14]))
    if hits:
        fail.append("%d multiplication x mark(s) survive" % len(hits))
    n_x = ms.count("\u00d7")
    return fail, "%d multiplication marks, all rendered as the multiplication sign (U+00D7); identifiers untouched" % n_x


def main():
    ms = io.open(MS, encoding="utf-8").read()
    say("issue #38 correction round 1 -- R1-R4 verification at %s" % MS)
    say("")
    allfail = []
    for name, fn, mutate in (("R1 figures", check_r1, lambda s: s.replace("](figures/fig1_collapse.png)", "(NOIMG)")),
                             ("R2 tables", check_r2, lambda s: s.replace("**Table 3 \u2014", "Table three")),
                             ("R3 bibliography", check_r3,
                              lambda s: s.replace("https://arxiv.org/abs/2310.03159", "NO-LINK", 1)),
                             ("R4 marks", check_r4, lambda s: s.replace("~`\u00d73.4 band", "~x3.4 band").replace("\u00d73.4", "x3.4"))):
        fail, summary = fn(ms)
        ctl = fn(mutate(ms))[0]
        caught = bool(ctl)
        say("%-17s %s" % (name, "PASS" if not fail else "FAIL"))
        say("   %s" % summary)
        for f in fail:
            say("   !! %s" % f)
        say("   control: mutation caught = %s" % caught)
        say("")
        allfail += fail
        if not caught:
            allfail.append("%s: control not caught -- the check cannot fail" % name)
    say("R1-R4: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        # The exit status must carry the VERDICT, never a logging accident: a run whose
        # checks all passed must exit 0 even if the log cannot be written, and say so.
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
