#!/usr/bin/env python3
"""Verify issue #44's correction ROUND 2 (required changes 1-5) with a control per check.

Every check reads the ARTEFACT -- the `## References` section of `manuscript.md`, the object a
reader's page and the journal's gate read -- and every check is two-sided: it must PASS on the
delivered manuscript and FAIL on a copy that puts the defect back.  A check that cannot fail is
decoration.

Two readings are taken with instruments that are NOT this package's own re-implementation of the
rule: the `block form:` line of the journal's gate (`.github/tools/refgate.py`, the layout read the
decision names by its reading) and GitHub's own CommonMark renderer (`gh api /markdown`).  Both need
something outside the package, so when either is absent the check says SKIP WITH THE REASON and the
local read carries the verdict -- never silently green.

One reading is NOT about this round at all and is here because the round's premise is that it holds:
R2-6 requires that the 103 works the list names are the 103 works `references.md` verified -- the form
changed, the CONTENT did not.  A correction that quietly rewrote a title or re-pointed an identifier
would be a different correction.

Run:  python3 verify_correction_r2.py            (from papers/issue-44/)
Writes correction_r2_verify.log beside this package.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
SRC = os.path.join(HERE, "references.md")
DIFFS = os.path.join(HERE, "refs_differences.json")
LOG = os.path.join(HERE, "correction_r2_verify.log")
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
REF_HEAD = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
ENTRY = re.compile(r"(?m)^\[(\d+)\] ")

out = []


def say(s):
    out.append(s)
    print(s)


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
    return json.load(io.open(os.path.join(HERE, "refs_display.json"), encoding="utf-8"))


def diffs():
    return json.load(io.open(DIFFS, encoding="utf-8"))


DIFF_MARK = re.compile(r"(?m)^\s*Difference: ")


def marker(blk):
    """The closing `Difference: ` marker, read at a LINE START.

    Searching for the first occurrence of the string instead reads entry 48's TITLE --
    `Reporting Score Distributions Makes a Difference: Performance Study ...` -- as if it were the
    marker, and reports the entry as carrying a difference that is not the authored line.
    """
    return DIFF_MARK.search(blk)


def rec_of(d, n):
    return [v for v in d.values() if str(v["n"]) == n][0]


def verified():
    """`references.md` -> {key: (authors, title, venue, identifier)}: the works that were verified."""
    rows = {}
    for line in io.open(SRC, encoding="utf-8"):
        if not line.startswith("[@"):
            continue
        key, _, rest = line.rstrip("\n")[2:].partition("] ")
        mi = re.search(r"`([^`]+)`\s*$", rest)
        ident = mi.group(1) if mi else ""
        head = rest[:mi.start()].strip() if mi else rest
        stars = [i for i, c in enumerate(head) if c == "*"]
        authors = head[:stars[0]].strip()
        title = head[stars[0] + 1:stars[1]].strip()
        venue = head[stars[1] + 1:].strip().lstrip(".").strip().rstrip(".").rsplit(",", 1)[0].strip()
        rows[key] = (authors, title, venue, ident)
    return rows


# --------------------------------------------------------------------------- the checks
def check_layout(ms):
    """Change 1: each entry on its own line, separated from the one above by a blank line."""
    sec = section(ms)
    lines = sec.split("\n")
    pos = [i for i, l in enumerate(lines) if ENTRY.match(l)]
    ents = blocks(sec)
    unsep = [i for k, i in enumerate(pos) if k and lines[i - 1].strip()]
    fails = []
    if len(ents) != 103:
        fails.append("parsed %d entries, expected 103" % len(ents))
    if unsep:
        fails.append("%d entr(y|ies) not separated from the entry above by a blank line (lines %s)"
                     % (len(unsep), unsep[:5]))
    detail = "%d entries, %d of them not separated from the entry above by a blank line" % (len(ents), len(unsep))
    #  the journal's gate -- the instrument the decision NAMES for this change.  It needs an
    #  interpreter with PEP 701 (a backslash inside an f-string expression); on one that lacks it the
    #  file raises SyntaxError, which is a property of the interpreter and not of the manuscript, so
    #  the candidates are tried and the one that ran is named in the log.
    if os.path.exists(GATE):
        why = []
        for interp in [sys.executable, "python3", "/usr/local/bin/python3"]:
            if not interp:
                continue
            try:
                p = subprocess.run([interp, GATE, os.path.basename(MS)], cwd=HERE, timeout=180,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            except (OSError, subprocess.SubprocessError) as exc:
                why.append("%s: %s" % (interp, exc))
                continue
            line = next((l.strip() for l in p.stdout.splitlines() if "block form:" in l), "")
            m = re.search(r"block form: (\d+) entries, (\d+) of them not separated", line)
            if m:
                if (int(m.group(1)), int(m.group(2))) != (103, 0):
                    fails.append("the gate reads %s entries / %s unseparated" % m.groups())
                else:
                    detail += " | refgate.py (%s): block form = %s entries, %s not separated" % (
                        os.path.basename(interp), m.groups()[0], m.groups()[1])
                why = []
                break
            tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
            why.append("%s: exit %d, no `block form:` line (%s)" % (interp, p.returncode, tail[0][:80]))
        if why:
            detail += " | SKIP the journal gate did not run in this tree (%s)" % "; ".join(why)
    else:
        detail += " | SKIP the journal gate is not in this tree (%s)" % GATE
    return fails, detail


def check_render(ms):
    """Change 1, the page read: GitHub's own renderer must return 103 paragraphs."""
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
    return ([] if n_p == 103 else ["GitHub's renderer returns %d <p> for the 103 entries" % n_p],
            "GitHub's own renderer: %d <p> for the 103 entries" % n_p)


def check_differences(ms):
    """Change 2: every entry closes with a stated difference, and it is the AUTHORED line."""
    sec = section(ms)
    d = disp()
    authored = diffs()
    fails = []
    n_diff = 0
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        key = rec_of(d, k)["key"]
        want = authored[key].strip()
        m = marker(blk)
        if not m:
            fails.append("entry %s carries no stated difference" % k)
            continue
        got = ws(blk[m.end():])
        if got != want:
            fails.append("entry %s: the printed difference is not the authored line" % k)
        else:
            n_diff += 1
    return fails, "%d of 103 entries close with their authored stated difference" % n_diff


def check_urls(ms):
    """Change 3: a resolvable URL on every entry, and no backticked identifier anywhere."""
    sec = section(ms)
    fails = []
    bad = []
    for blk in blocks(sec):
        t = ws(blk)
        if not re.search(r"https?://\S+", t):
            bad.append(ENTRY.match(blk).group(1))
    if bad:
        fails.append("%d entr(y|ies) carry no resolvable URL: %s" % (len(bad), bad[:5]))
    n_backtick = sec.count("`")
    if n_backtick:
        fails.append("%d backticked token(s) survive in the list" % n_backtick)
    return fails, ("%d entries each carry a resolvable https URL; %d backticked token(s) in the section"
                   % (len(blocks(sec)), n_backtick))


def check_year(ms):
    """Change 4: the year in parentheses after the author block, printed once, before the title."""
    sec = section(ms)
    fails = []
    twice, late = [], []
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        if not re.match(r"^\[%s\] \S.*\((?:19|20)\d\d\)\." % k, t):
            fails.append("entry %s: the year is not in parentheses after the author block" % k)
        head = t.split("Difference:", 1)[0]
        if len(re.findall(r"\((?:19|20)\d\d\)", head)) != 1:
            twice.append(k)
        ya, ua = head.find("("), head.find("https://")
        if ua >= 0 and ya > ua:
            late.append(k)
    if twice:
        fails.append("%d entr(y|ies) print their year more than once before the difference: %s"
                     % (len(twice), twice[:5]))
    if late:
        fails.append("%d entr(y|ies) print the year after the URL: %s" % (len(late), late[:5]))
    return fails, "103 entries print exactly one parenthesised year, after the author block and before the URL"


def check_order(ms):
    """Change 5: one order for the whole list -- authors, (year), title, venue, URL, closing difference."""
    sec = section(ms)
    fails = []
    for blk in blocks(sec):
        k = ENTRY.match(blk).group(1)
        t = ws(blk)
        tok = list(re.finditer(r"https?://\S+", t))
        if not tok:
            fails.append("entry %s: no URL to close on" % k)
            continue
        m = marker(blk)
        if not m:
            fails.append("entry %s: no closing `Difference:` marker" % k)
        elif m.start() < tok[-1].end():
            fails.append("entry %s: the `Difference:` marker does not close the entry" % k)
        ym = re.search(r"\((?:19|20)\d\d\)\.", t)
        if not ym:
            fails.append("entry %s: no parenthesised year" % k)
        elif t.index(ym.group(0)) > tok[-1].start():
            fails.append("entry %s: the year prints after the URL" % k)
        #  the emphasis read is taken over the ENTRY (authors, title, venue, link) and not over the
        #  closing prose line, which is a sentence and may set a word off -- the record's field
        #  emphasis is what must not survive into the printed list.
        if re.search(r"\*[^*]+\*", t[:m.start()] if m else t):
            fails.append("entry %s: the record's *emphasis* survives into the printed list" % k)
        if ENTRY.match(t).end() > tok[0].start():
            fails.append("entry %s: the first URL precedes the author block" % k)
    return fails, "103 entries: authors, (year), title, venue, resolvable URL, closing `Difference:`"


def check_content_unchanged(ms):
    """R2-6: the works the list NAMES are the works `references.md` verified -- form, not content.

    Read by comparing, for every entry, the printed author block, title, venue and URL against the
    verified record.  The premise of this round is that it is a text fix; this is the read that would
    catch a form fix that rewrote a record.
    """
    sec = section(ms)
    d = disp()
    ver = verified()
    fails = []
    for i, blk in enumerate(blocks(sec), 1):
        n = ENTRY.match(blk).group(1)
        rec = rec_of(d, n)
        a, t_, v, ident = ver[rec["key"]]
        t = ws(blk)
        want_url = ("https://arxiv.org/abs/%s" % ident[6:]) if ident.lower().startswith("arxiv:") \
            else ("https://doi.org/%s" % ident)
        m = re.match(r"^\[\d+\] (.*?) \((?:19|20)\d\d\)\.", t)
        want_authors = "; ".join([c.strip() for c in a.split(";")][:3]) + \
            ("; et al." if len([c for c in a.split(";") if c.strip()]) >= 4 else "")
        if not m or ws(m.group(1)) != ws(want_authors):
            fails.append("entry %s: the printed author block is not the verified record's (%r)"
                         % (n, (m.group(1) if m else "")[:60]))
        if n != str(i):
            fails.append("the entries are not numbered in order at position %s" % i)
        if ws(t_) not in t:
            fails.append("entry %s: the printed title is not the verified record's (%r)" % (n, t_[:60]))
        if want_url not in t:
            fails.append("entry %s: the printed link is not the record's %s" % (n, want_url))
        if not ident.lower().startswith("arxiv:") and v and ws(v) not in t:
            fails.append("entry %s: the printed venue is not the verified record's (%r)" % (n, v[:60]))
    if len(blocks(sec)) != len(ver):
        fails.append("the list prints %d entries for %d verified works" % (len(blocks(sec)), len(ver)))
    return fails, "%d entries name the authors, title, venue and link of the verified record" % len(blocks(sec))


def collapse(ms):
    """The published reading: the same section with the blank lines between entries removed."""
    sec = section(ms)
    lines = sec.split("\n")
    return ms.replace(sec, "\n".join(l for l in lines if l.strip()))


def author_of(ms):
    rec = rec_of(disp(), "1")
    return rec["authors"]


CHECKS = [
    ("R2-1 layout", check_layout, collapse),
    ("R2-1b renderer", check_render, collapse),
    ("R2-2 differences", check_differences,
     lambda s: s.replace("\n    Difference: ", "\n    DIFFERENCE: ", 1)),
    ("R2-3 urls", check_urls, None),
    ("R2-4 year", check_year, None),
    ("R2-5 order", check_order, lambda s: s.replace("\n    Difference: ", "\n    Difference: ", 1)),
    ("R2-6 content", check_content_unchanged, None),
]


def mutation_factory(name, ms):
    """A control per check: put the defect back into a copy of the section."""
    sec = section(ms)
    first = blocks(sec)[0]
    if name.startswith("R2-1"):
        return collapse(ms)
    if name.startswith("R2-2"):
        return ms.replace("\n    Difference: ", "\n    DIFFERENCE: ", 1)
    if name.startswith("R2-3"):
        return ms.replace("https://arxiv.org/abs/2609.12582", "`arXiv:2609.12582`", 1)
    if name.startswith("R2-4"):
        return ms.replace("Ardebili, M. S. (2026).", "Ardebili, M. S. 2026.", 1)
    if name.startswith("R2-5"):
        #  the record's field emphasis put back -- the defect change 5's `one order` covers besides
        #  the component order: the list is plain text, and the record's `*title*` is not its form
        return ms.replace("NovaFabric: Tamper-Evident, Replayable Evidence for Autonomous AI Agent\n    Runs.",
                          "*NovaFabric: Tamper-Evident, Replayable Evidence for Autonomous AI Agent\n    Runs*.",
                          1)
    if name.startswith("R2-6"):
        return ms.replace("NovaFabric: Tamper-Evident", "NovaFabric: Rewritten Title", 1)
    return ms


def main():
    ms = io.open(MS, encoding="utf-8").read()
    say("issue #44 correction round 2 -- required changes 1-5 verification at %s" % MS)
    say("")
    allfail = []
    for name, fn, _legacy in CHECKS:
        try:
            fails, detail = fn(ms)
        except Exception as exc:
            fails, detail = ["the check raised %s: %s" % (type(exc).__name__, exc)], "no reading taken"
        planted = mutation_factory(name, ms)
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
    say("R2 changes 1-5: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
