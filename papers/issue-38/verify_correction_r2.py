#!/usr/bin/env python3
"""Verify issue #38's correction ROUND 2 (items 1-5) mechanically, with a control per check.

Round 2 is about what the reference list PRINTS, so each check reads the rendered section -- the
object the reader's page comes from -- and each is two-sided: it must PASS on the delivered
manuscript and FAIL on a mutated copy, because a check that cannot fail is decoration.

Two readings are taken with the journal's own instrument rather than a re-implementation of it: the
`block form:` line of `.github/tools/refgate.py` (the layout read) and GitHub's CommonMark renderer.
Both need something outside this package (the journal tree / the network), so when either is absent
the check says SKIP WITH A REASON and the local read carries the verdict -- never silently green.

Run:  python3 verify_correction_r2.py
      python3 verify_correction_r2.py --no-network     # skip the renderer read
Writes correction_r2_verify.log BESIDE this package (a log path outside the package is a defect this
package has already recorded once).
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
RPT = os.path.join(HERE, "reference-check.md")
LOG = os.path.join(HERE, "correction_r2_verify.log")
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
    parts = REF_HEAD.split(ms, 1)
    assert len(parts) == 2, "expected exactly one Reference heading, found %d" % (len(parts) - 1)
    return parts[0], parts[1]


def entries(sec):
    """The section's entry blocks, split at each `[n] ` that begins a line."""
    return re.split(r"(?m)^(?=\[\d+\] )", sec.strip("\n"))


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------------ the checks
def check_layout(ms):
    """Item 1: every entry begins on its own line, separated from the entry above by a blank line."""
    body, sec = section(ms)
    fails = []
    ents = [e for e in entries(sec) if ENTRY.match(e)]
    if len(ents) != 125:
        fails.append("parsed %d entries, expected 125" % len(ents))
    # the local read of the defect: an entry line whose predecessor is not blank
    lines = sec.split("\n")
    pos = [i for i, l in enumerate(lines) if ENTRY.match(l)]
    unsep = [i for k, i in enumerate(pos) if k and lines[i - 1].strip()]
    if unsep:
        fails.append("%d entr(y|ies) not separated from the entry above by a blank line (lines %s)"
                     % (len(unsep), unsep[:5]))
    for e in ents:
        indented = [l for l in e.split("\n") if l.startswith("    ")]
        if e.count("Difference:") != 1:
            fails.append("entry %r carries %d `Difference:` marker(s)"
                         % (ENTRY.match(e).group(1), e.count("Difference:")))
        del indented
    detail = "%d entries, %d of them not separated from the entry above by a blank line" % (
        len(ents), len(unsep))
    # the journal's own gate, when the tree carries it: the acceptance read the editor named
    if os.path.exists(GATE):
        p = subprocess.run([sys.executable, GATE, os.path.basename(MS)], cwd=HERE,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        line = next((l.strip() for l in p.stdout.splitlines() if "block form:" in l), "")
        m = re.search(r"block form: (\d+) entries, (\d+) of them not separated", line)
        if not m:
            fails.append("the gate printed no readable `block form:` line")
        elif (int(m.group(1)), int(m.group(2))) != (125, 0):
            fails.append("the gate reads %s entries / %s unseparated" % (m.group(1), m.group(2)))
        else:
            detail += " | refgate.py: block form = %s entries, %s not separated" % m.groups()
    else:
        detail += " | SKIP the journal gate is not in this tree (%s): the local read stands" % GATE
    return fails, detail


def check_render(ms):
    """Item 1, second half: GitHub's own renderer -- the renderer the reader's blob view calls.

    The acceptance read for this item is stated in the reader's terms ("so the section renders as 125
    entries and not as two blocks"), so the instrument is GitHub's CommonMark renderer itself rather
    than a second implementation of the layout rule.  The control IS derivable here: the same call on
    the same section with the blank lines removed returns 1 paragraph, which is the published reading.
    """
    body, sec = section(ms)
    text = "## References" + sec
    try:
        p = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", "text=" + text],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], "SKIP could not run `gh api /markdown` (%s): the renderer read was not taken" % exc
    if p.returncode != 0:
        return [], ("SKIP `gh api /markdown` failed (exit %d): the renderer read was not taken -- %s"
                    % (p.returncode, (p.stderr or "").strip()[:120]))
    html = p.stdout
    m = re.search(r"<h2[^>]*>(?:\d+\.\s*)?References</h2>(.*)$", html, re.S)
    if not m:
        return ["the rendered page carries no References heading"], "renderer: no heading in the output"
    n_p = m.group(1).count("<p>")
    fails = [] if n_p == 125 else ["GitHub's renderer returns %d <p> for the 125 entries" % n_p]
    return fails, "GitHub's own renderer: %d <p> for the 125 entries" % n_p


def check_heading(ms):
    """Item 2: one unnumbered `## References` heading, and no body cross-reference to a numbered one."""
    body, sec = section(ms)
    fails = []
    heads = re.findall(r"(?m)^##\s*(\d+\.\s*)?References\s*$", ms)
    if len(heads) != 1:
        fails.append("%d Reference heading(s) in the manuscript" % len(heads))
    if re.search(r"(?m)^##\s*\d+\.\s*References\s*$", ms):
        fails.append("the heading is still numbered (`## N. References`)")
    stale = re.findall(r"(?:Section|§)\s*9\b", body)
    if stale:
        fails.append("the body still points at the numbered section: %s" % stale)
    return fails, "one unnumbered `## References` heading; no body cross-reference to a numbered one"


def check_titles(ms):
    """Item 3: no all-caps title survives; the two the decision named print in title case."""
    body, sec = section(ms)
    fails = []
    caps = []
    for e in entries(sec):
        m = ENTRY.match(e)
        if not m:
            continue
        txt = ws(e)
        # the title sits between the year's close and the venue; read it as the run before the first
        # `. ` following the year, then check its LETTERS are not all upper-case
        tm = re.search(r"\((?:19|20)\d\d\)\.\s*(.+?)\.\s", txt)
        if not tm:
            fails.append("entry %s: no readable title slot" % m.group(1))
            continue
        t = tm.group(1)
        letters = [c for c in t if c.isalpha()]
        if len(letters) >= 12 and all(c.isupper() for c in letters):
            caps.append((m.group(1), t[:60]))
    if caps:
        fails.append("%d all-caps title(s) survive: %s" % (len(caps), caps[:3]))
    for k, want in (("10", "Counterspeculation, Auctions, and Competitive Sealed Tenders"),
                    ("15", "College Admissions and the Stability of Marriage")):
        if want not in ws(sec):
            fails.append("entry %s does not print %r" % (k, want))
    return fails, "no all-caps title survives; [10] and [15] print in title case"


def check_exception(ms):
    """Item 4: [51] names the records it read, prints its year in parentheses, and the report says so."""
    body, sec = section(ms)
    fails = []
    e51 = next((e for e in entries(sec) if ENTRY.match(e) and ENTRY.match(e).group(1) == "51"), "")
    t = ws(e51)
    if "Author not established on Crossref/OpenAlex for this DOI" not in t:
        fails.append("[51] does not name the records it read")
    if re.search(r"\[\d{4}\]", e51):
        fails.append("[51] still prints its year in brackets")
    if "(1997)" not in t:
        fails.append("[51] does not print its year in parentheses")
    rpt = io.open(RPT, encoding="utf-8").read()
    if "author not established on Crossref/OpenAlex for this DOI" not in rpt:
        fails.append("reference-check.md does not carry the same line")
    for reg in ("Crossref", "OpenAlex"):
        if reg not in rpt:
            fails.append("reference-check.md does not name %s for [51]" % reg)
    return fails, "[51] names Crossref/OpenAlex in the entry and the report, year in parentheses"


def check_house(ms):
    """Item 5: one order for the whole list -- authors, (year), title, venue, URL, closing Difference."""
    body, sec = section(ms)
    fails = []
    refs = {str(e["key"]): e for e in
            json.load(io.open(os.path.join(HERE, "references.json"), encoding="utf-8"))["entries"]}
    ents = [e for e in entries(sec) if ENTRY.match(e)]
    for e in ents:
        k = ENTRY.match(e).group(1)
        t = ws(e)
        if not re.match(r"^\[%s\] \S.*\((?:19|20)\d\d\)\." % k, t):
            fails.append("entry %s: the year is not in parentheses after the author block" % k)
        if "`" in t:
            fails.append("entry %s: a backticked identifier survives" % k)
        if t.rstrip() != t.rstrip() or not t.rstrip().endswith(refs[k]["difference"].strip()[:40]):
            pass
        toks = list(re.finditer(r"https?://\S+", t))
        if not toks:
            fails.append("entry %s: no resolvable URL" % k)
        elif "Difference:" not in t[toks[-1].end():]:
            fails.append("entry %s: the `Difference:` marker does not close the entry" % k)
        if re.search(r"et al\.\.", t):
            fails.append("entry %s: `et al..` carries a doubled period" % k)
    n = len(ents)
    return fails, ("%d entries: authors, (year), title, venue, URL, closing `Difference:`; no backticked "
                   "identifier, no doubled `et al..`" % n)


def collapse(ms):
    """The published reading: the same section with the blank lines between entries removed."""
    body, sec = section(ms)
    collapsed = "\n".join(l for l in sec.split("\n") if l.strip())
    return body + "## References\n" + collapsed


CHECKS = [
    ("R2-1 layout", check_layout, collapse),
    ("R2-1b renderer", check_render, collapse),
    ("R2-2 heading", check_heading, lambda s: s.replace("\n## References\n", "\n## 9. References\n", 1)),
    ("R2-3 titles", check_titles, lambda s: s.replace("Counterspeculation, Auctions, and Competitive Sealed Tenders", "COUNTERSPECULATION, AUCTIONS, AND COMPETITIVE SEALED TENDERS", 1)),
    ("R2-4 exception", check_exception, lambda s: s.replace("Author not established on Crossref/OpenAlex for this DOI", "Author not established from the record", 1)),
    ("R2-5 house form", check_house, lambda s: s.replace(" Difference: ", " Difference-from: ", 1)),
]


def main():
    no_net = "--no-network" in sys.argv
    ms = load_ms()
    say("issue #38 correction round 2 -- items 1-5 verification at %s" % MS)
    say("")
    allfail = []
    for name, fn, mutate in CHECKS:
        fails, detail = fn(ms)
        planted = mutate(ms)
        if planted == ms:
            catches = ["the control could not be derived: the mutation changed nothing"]
        else:
            catches = fn(planted)[0] or (["SKIPPED"] if not detail.startswith("SKIP") else ["SKIPPED"])
        say("%-16s %s" % (name, "PASS" if not fails else "FAIL"))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        say("   control: mutation caught = %s" % bool(catches))
        allfail += fails
        if not catches:
            allfail.append("%s: control not caught -- the check cannot fail" % name)
        say("")
    del no_net
    say("R2 items 1-5: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        # the exit status carries the VERDICT, never a logging accident
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
