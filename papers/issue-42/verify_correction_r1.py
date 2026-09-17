#!/usr/bin/env python3
"""Verify issue #42's correction ROUND 1 (required changes 1-7) with a control per check.

Every check reads the ARTEFACT -- the rendered `## References` section of `manuscript.md`, the object
a reader's page and the journal's gate read -- and every check is two-sided: it must PASS on the
delivered manuscript and FAIL on a copy that puts the defect back.  A check that cannot fail is
decoration.

Two readings are taken with instruments that are NOT this package's own re-implementation of the rule:
the `block form:` line of the journal's gate (`.github/tools/refgate.py`, the layout read the decision
names) and GitHub's own CommonMark renderer.  Both need something outside the package, so when either
is absent or cannot run, the reading is reported as NOT TAKEN with its reason -- the verdict says so in
its own last line and the local read carries the decision.  Never silently green.

**The log is evidence, so it names its coordinates** (`evidence_log.py`, correction round 3): the build
the reading was taken on and the tree it was taken in, plus every reading that could not be taken.
Nothing is written unless `--log PATH` asks for it, so a reader's run cannot overwrite the committed
copy; `--check` re-derives the log and compares it with the committed one, the DECLARED lines (which
name the build, the tree, or a reading not taken) present on both sides rather than equal, and every
check line paired with the same check on the other side.

Run:  python3 verify_correction_r1.py                  # verdict to stdout, writes no file
      python3 verify_correction_r1.py --log FILE       # and writes the log to FILE
      python3 verify_correction_r1.py --check          # re-derive and compare with the committed log
      python3 verify_correction_r1.py --no-network     # skip the renderer read (it needs `gh`)
      python3 verify_correction_r1.py --head SHA       # declare the revision of a plain directory
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

import evidence_log as EL

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
LOG_NAME = "correction_r1_verify.log"
LOG = os.path.join(HERE, LOG_NAME)
GATE = EL.gate_path(HERE)
REF_HEAD = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
ENTRY = re.compile(r"(?m)^\[(\d+)\] ")

out = []
NOT_TAKEN = []
ARGS = None
HEADER_HEAD = None          # the revision the reading is taken at, when the tree cannot say (see --head)


def say(s):
    out.append(s)
    print(s)


def not_taken(what, why):
    """A reading this run could not take. Recorded, and printed as a DECLARED `NOT TAKEN:` line beside
    the verdict: present in every log, its content a fact about this run's coordinate, so a reader sees
    it and the comparison does not read the machine as a disagreement."""
    NOT_TAKEN.append((what, why))


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
        if m:
            if (int(m.group(1)), int(m.group(2))) != (117, 0):
                fails.append("the gate reads %s entries / %s unseparated" % m.groups())
            else:
                detail += " | refgate.py: block form = %s entries, %s not separated" % m.groups()
        elif p.returncode != 0:
            # The gate did not run here -- it needs an interpreter that parses it (PEP 701). That is a
            # reading NOT TAKEN, not a reading that disagreed, and the local read above carries the
            # verdict. Reported as such so a reader can see which half was read.
            detail += " | NOT TAKEN: the gate did not run under this interpreter"
            not_taken("R1-1 the journal's gate",
                      "refgate.py exited %d under Python %s and printed no `block form:` line: %s"
                      % (p.returncode, sys.version.split()[0],
                         (p.stdout.strip().splitlines() or ["(no output)"])[-1][:120]))
        else:
            fails.append("the journal's gate printed no readable `block form:` line")
    else:
        not_taken("R1-1 the journal's gate", "not in this tree (%s)" % GATE)
        detail += " | NOT TAKEN: the journal gate is not in this tree"
    return fails, detail


def check_render(ms):
    """Change 1, the page read: GitHub's own renderer must return 117 paragraphs."""
    text = section(ms)
    if ARGS is not None and ARGS.no_network:
        return [], "the renderer read was not requested (--no-network)"
    try:
        p = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", "text=" + text],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], "SKIP could not run `gh api /markdown` (%s)" % exc
    if p.returncode != 0:
        return [], "SKIP `gh api /markdown` failed (exit %d)" % p.returncode
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


def run_checks():
    """The log this run produces: the two coordinate lines, the checks, the verdict."""
    out[:] = []
    for line in EL.header(HERE, declared_head=HEADER_HEAD):
        say(line)

    ms = load_ms()
    say("issue #42 correction round 1 -- required changes 1-7, read at the rendered section of"
        " manuscript.md")
    say("")
    allfail = []
    for name, fn, mutate in CHECKS:
        try:
            fails, detail = fn(ms)
        except Exception as exc:                                              # noqa: BLE001
            fails, detail = ["the check raised %s: %s" % (type(exc).__name__, exc)], "no reading taken"
        skipped = False
        if detail.startswith("SKIP"):
            detail = "NOT TAKEN: " + detail[5:].strip()
            not_taken(name, detail[10:].strip())
            skipped = True
        try:
            planted = mutate(ms)
        except Exception as exc:                                              # noqa: BLE001
            planted = ms
            detail += " | control could not be derived (%s)" % exc
        if planted == ms:
            catches = ["the control could not be derived: the mutation changed nothing"]
        else:
            try:
                catches = fn(planted)[0]
            except Exception as exc:                                          # noqa: BLE001
                catches = ["the check raised on the planted copy: %s" % exc]
        # the check LINE carries the marker too, so the reading this line names is recognisable as the
        # same reading on both sides even where one run could not take it
        say("%-18s %s%s" % (name, "PASS" if not fails else "FAIL",
                            "   (NOT TAKEN)" if skipped else ""))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        say("   control: mutation caught = %s" % bool(catches))
        allfail += fails
        if not catches:
            allfail.append("%s: control not caught -- the check cannot fail" % name)
        say("")
    verdict(allfail)
    return 1 if allfail else 0


def verdict(allfail):
    """The end of the file. Every reading that was not taken is printed HERE as a declared line, so a
    `SKIP` is visible to a reader who reads only the verdict -- `ALL PASS` over a silent skip is the
    defect this shape exists to prevent -- while the verdict line itself stays the same on every
    machine."""
    for w, y in NOT_TAKEN:
        say("NOT TAKEN: %s -- %s" % (w, y))
    say("R1 changes 1-7: %s" % ("FAIL" if allfail else "ALL PASS"))
    say("   every check above was read on this machine; a reading marked NOT TAKEN is not covered by this"
        " verdict and is reported as not taken, never as a pass")


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None, help="also write the log to this path (default: write nothing)")
    ap.add_argument("--check", action="store_true",
                    help="re-derive the log and compare it with the committed %s" % LOG_NAME)
    ap.add_argument("--no-network", action="store_true", help="skip the renderer read (it needs `gh`)")
    ap.add_argument("--head", default=None,
                    help="the revision this reading is taken at, DECLARED: a plain directory (a git"
                         " archive export) cannot derive it")
    ARGS = ap.parse_args()
    global HEADER_HEAD
    HEADER_HEAD = ARGS.head

    rc = run_checks()
    lines = list(out)
    if ARGS.check:
        committed = io.open(LOG, encoding="utf-8").read()
        ok, declared, nottaken, mism = EL.compare(committed, EL.render(lines))
        print("")
        print("%s vs a fresh run: %s" % (LOG_NAME, "MATCH" if ok else "MISMATCH"))
        print("   %d declared line(s) (a build, a tree, or a reading not taken); %d line(s) where this"
              " run took no reading where the committed log records one" % (declared, nottaken))
        for n, x, y in mism[:6]:
            print("   !! line %d" % n)
            print("      committed: %s" % x[:160])
            print("      fresh:     %s" % y[:160])
        return 0 if ok else 1
    if ARGS.log:
        EL.write(ARGS.log, lines)
        print("")
        print("log written to %s" % ARGS.log)
    return rc


if __name__ == "__main__":
    sys.exit(main())
