#!/usr/bin/env python3
"""Verify issue #42's correction ROUND 1 (required changes 1-7) with a control per check.

Every check reads the ARTEFACT -- the rendered `## References` section of `manuscript.md`, the object
a reader's page and the journal's gate read -- and every check is two-sided: it must PASS on the
delivered manuscript and FAIL on a copy that puts the defect back.  A check that cannot fail is
decoration.

Two readings are taken with instruments that are NOT this package's own re-implementation of the rule:
the `block form:` line of the journal's gate (`.github/tools/refgate.py`, the layout read the decision
names) and GitHub's own CommonMark renderer.  Both need something outside the package, so when either
is absent the check says SKIP WITH THE REASON and the local read carries the verdict -- never silently
green.

Run:  python3 verify_correction_r1.py            (from papers/issue-42/)
      python3 verify_correction_r1.py --no-network
Writes correction_r1_verify.log beside this package.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
LOG = os.path.join(HERE, "correction_r1_verify.log")
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
REF_HEAD = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
ENTRY = re.compile(r"(?m)^\[(\d+)\] ")

out = []


def say(s):
    out.append(s)
    print(s)


def load_ms():
    return io.open(MS, encoding="utf-8").read()


def section(ms):
    """The section INCLUDING its heading line (cut by line index, not by splitting on the heading)."""
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if REF_HEAD.match(l)]
    assert len(starts) == 1, "expected exactly one Reference heading, found %d" % len(starts)
    return "\n".join(lines[starts[0]:]).rstrip("\n")


def blocks(sec):
    return [b for b in re.split(r"(?m)^(?=\[\d+\] )", sec.strip("\n")) if ENTRY.match(b)]


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


def disp():
    return json.load(io.open(os.path.join(HERE, "artefacts", "refs_display.json"), encoding="utf-8"))


# --------------------------------------------------------------------------- the checks
def check_layout(ms):
    """Change 1: each entry on its own line, separated from the one above by a blank line."""
    sec = section(ms)
    lines = sec.split("\n")
    pos = [i for i, l in enumerate(lines) if ENTRY.match(l)]
    ents = [b for b in blocks(sec)]
    unsep = [i for k, i in enumerate(pos) if k and lines[i - 1].strip()]
    fails = []
    if len(ents) != 117:
        fails.append("parsed %d entries, expected 117" % len(ents))
    if unsep:
        fails.append("%d entr(y|ies) not separated from the entry above by a blank line (lines %s)"
                     % (len(unsep), unsep[:5]))
    detail = "%d entries, %d of them not separated from the entry above by a blank line" % (len(ents), len(unsep))
    if os.path.exists(GATE):
        p = subprocess.run([sys.executable, GATE, os.path.basename(MS)], cwd=HERE,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        line = next((l.strip() for l in p.stdout.splitlines() if "block form:" in l), "")
        m = re.search(r"block form: (\d+) entries, (\d+) of them not separated", line)
        if not m:
            fails.append("the journal's gate printed no readable `block form:` line")
        elif (int(m.group(1)), int(m.group(2))) != (117, 0):
            fails.append("the gate reads %s entries / %s unseparated" % m.groups())
        else:
            detail += " | refgate.py: block form = %s entries, %s not separated" % m.groups()
    else:
        detail += " | SKIP the journal gate is not in this tree (%s)" % GATE
    return fails, detail


def check_render(ms):
    """Change 1, the page read: GitHub's own renderer must return 117 paragraphs."""
    text = section(ms)
    try:
        p = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", "text=" + text],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], "SKIP could not run `gh api /markdown` (%s): the renderer read was not taken" % exc
    if p.returncode != 0:
        return [], ("SKIP `gh api /markdown` failed (exit %d): the renderer read was not taken"
                    % p.returncode)
    n_p = p.stdout.count("<p>")
    return ([] if n_p == 117 else ["GitHub's renderer returns %d <p> for the 117 entries" % n_p],
            "GitHub's own renderer: %d <p> for the 117 entries" % n_p)


def check_differences(ms):
    """Change 2: every entry closes with a stated difference, and it is the AUTHORED line."""
    sec = section(ms)
    d = disp()
    fails = []
    n_diff = 0
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        want = d[[kk for kk in d if str(d[kk]["n"]) == k][0]]["difference"]
        if "Difference: " not in t:
            fails.append("entry %s carries no stated difference" % k)
            continue
        got = t.split("Difference: ", 1)[1].strip()
        if got != want:
            fails.append("entry %s: the printed difference is not the authored line" % k)
        else:
            n_diff += 1
    return fails, "%d of 117 entries close with their authored stated difference" % n_diff


def check_urls(ms):
    """Change 3: a resolvable URL on every entry, and no bare `DOI: 10.…` identifier."""
    sec = section(ms)
    fails = []
    bad = []
    for blk in blocks(sec):
        t = ws(blk)
        if not re.search(r"https?://\S+", t):
            bad.append(ENTRY.match(blk).group(1))
        if re.search(r"\bDOI: 10\.", t):
            fails.append("entry %s still prints a bare `DOI: ` identifier" % ENTRY.match(blk).group(1))
    if bad:
        fails.append("%d entr(y|ies) carry no resolvable URL: %s" % (len(bad), bad[:5]))
    return fails, "%d entries each carry a resolvable https URL; 0 bare `DOI: ` identifiers" % len(blocks(sec))


def check_year(ms):
    """Change 4: the year in parentheses after the author block, printed once."""
    sec = section(ms)
    fails = []
    twice = []
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        if not re.match(r"^\[%s\] \S.*\((?:19|20)\d\d\)\." % k, t):
            fails.append("entry %s: the year is not in parentheses after the author block" % k)
        if len(re.findall(r"\((?:19|20)\d\d\)", t.split("Difference:", 1)[0])) != 1:
            twice.append(k)
    if twice:
        fails.append("%d entr(y|ies) print their year more than once before the difference: %s"
                     % (len(twice), twice[:5]))
    return fails, "117 entries print exactly one parenthesised year, after the author block"


def check_etal(ms):
    """Change 5: no doubled period (`et al..`), and `et al.` present where four or more authors."""
    sec = section(ms)
    fails = []
    if "et al.." in sec:
        fails.append("%d doubled `et al..` survive" % sec.count("et al.."))
    d = disp()
    need = [v for v in d.values() if len(v["authors"]) >= 4]
    have = len(re.findall(r"; et al\.(?![.])", sec))
    if have != len(need):
        fails.append("%d entries print `et al.`, expected %d (four or more authors)" % (have, len(need)))
    return fails, "0 doubled `et al..`; %d entries print the single-period `et al.`" % have


def check_authors(ms):
    """Change 6: authors in `Family, I.` form, family first, and the record's own list."""
    sec = section(ms)
    d = disp()
    fails = []
    bad = []
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        m = re.match(r"^\[%s\] (.*?) \((?:19|20)\d\d\)\." % k, t)
        if not m:
            bad.append((k, "no author block"))
            continue
        rec = [v for v in d.values() if str(v["n"]) == k][0]
        if rec["authors"]:
            want = "; ".join(rec["authors"][:3]) + ("; et al." if len(rec["authors"]) >= 4 else "")
            if m.group(1) != want:
                bad.append((k, "%r vs %r" % (m.group(1), want)))
    if bad:
        fails.append("%d entr(y|ies) whose author block is not the record in house form: %s"
                     % (len(bad), bad[:3]))
    return fails, "117 entries print their authors as `Family, I.` (first three + `et al.` for 4+)"


def check_order(ms):
    """Change 7: one order for the whole list -- authors, (year), title, venue, URL, closing difference."""
    sec = section(ms)
    fails = []
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        toks = list(re.finditer(r"https?://\S+", t))
        if not toks:
            fails.append("entry %s: no URL to close on" % k)
            continue
        tail = t[toks[-1].end():]
        if "Difference:" not in tail:
            fails.append("entry %s: the `Difference:` marker does not close the entry" % k)
        if "`" in t:
            fails.append("entry %s: a backticked identifier survives" % k)
        ym = re.search(r"\((?:19|20)\d\d\)\.", t)
        if not ym:
            fails.append("entry %s: no parenthesised year" % k)
        elif t.index(ym.group(0)) > toks[-1].start():
            fails.append("entry %s: the year prints after the URL" % k)
    return fails, "117 entries: authors, (year), title, venue, resolvable URL, closing `Difference:`"


def collapse(ms):
    """The published reading: the same section with the blank lines between entries removed."""
    sec = section(ms)
    lines = sec.split("\n")
    head = lines[0]
    rest = "\n".join(l for l in lines[1:] if l.strip())
    return ms.replace(sec, head + "\n" + rest)


CHECKS = [
    ("R1-1 layout", check_layout, collapse),
    ("R1-1b renderer", check_render, collapse),
    ("R1-2 differences", check_differences,
     lambda s: s.replace("\n    Difference: ", "\n    DIFFERENCE: ", 1)),
    ("R1-3 urls", check_urls,
     lambda s: s.replace("https://doi.org/10.1109/ICSE.2013.6606617", "DOI: 10.1109/ICSE.2013.6606617", 1)),
    ("R1-4 year", check_year, lambda s: s.replace("Bacchelli, A.; Bird, C. (2013).", "Bacchelli, A.; Bird, C. 2013.", 1)),
    ("R1-5 etal", check_etal, lambda s: s.replace("; et al. (", "; et al.. (", 1)),
    ("R1-6 authors", check_authors,
     lambda s: s.replace("[1] Bacchelli, A.; Bird, C.", "[1] Alberto Bacchelli, Christian Bird", 1)),
    ("R1-7 order", check_order,
     lambda s: s.replace("Bacchelli, A.; Bird, C. (2013).", "Bacchelli, A.; Bird, C. 2013.", 1)),
]


def main():
    ms = load_ms()
    say("issue #42 correction round 1 -- required changes 1-7 verification at %s" % MS)
    say("")
    allfail = []
    for name, fn, mutate in CHECKS:
        try:
            fails, detail = fn(ms)
        except Exception as exc:
            fails, detail = ["the check raised %s: %s" % (type(exc).__name__, exc)], "no reading taken"
        try:
            planted = mutate(ms)
        except Exception as exc:
            planted = ms
            detail += " | control could not be derived (%s)" % exc
        if planted == ms:
            catches = ["the control could not be derived: the mutation changed nothing"]
        else:
            try:
                catches = fn(planted)[0]
            except Exception as exc:
                catches = ["the check raised on the planted copy: %s" % exc]
        say("%-18s %s" % (name, "PASS" if not fails else "FAIL"))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        say("   control: mutation caught = %s" % bool(catches))
        allfail += fails
        if not catches:
            allfail.append("%s: control not caught -- the check cannot fail" % name)
        say("")
    say("R1 changes 1-7: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
