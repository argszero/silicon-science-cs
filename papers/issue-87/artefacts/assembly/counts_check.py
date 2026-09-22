#!/usr/bin/env python3
"""#87 -- the package's counted claims have ONE owner: the assembly report.  This checker reads every carrier.

WHY.  The R415 editorial re-check found the same defect in the previous head twice: `reproduce.sh`'s header
said 91 numeric bindings while its own manifest said 128.  A number restated in several carriers goes stale in
all but the one that was edited, so the repair is not another edit -- it is an owner and a check:

  * the OWNER is the assembly report (`artefacts/assembly/assembly-report.txt`), which prints the counts the
    assembly itself measured: bibliography entries, in-text coverage and bound numbers;
  * every other carrier (this README, `reproduce.sh`, the manuscript) is READ against it, and a carrier that
    states a different number is a defect of the carrier, not a rounding difference.

TWO-SIDED AS OF R419 -- THE DEFECT THIS FILE WAS REBUILT FOR.  The first version printed a row per declared
phrasing and let a row that matched NOTHING pass silently ("-- not present --").  The R419 repair of
`reproduce.sh` therefore DELETED the phrase "76 quantities read out" from that carrier while the checker kept
printing PASS: a count can be lost, not only contradicted, and a loss left no trace.  Every row now declares
what it expects of its carrier:

  * `required`        -- the carrier STATES this count in this phrasing.  Zero matches is a FAILURE of the
                         carrier (the count was removed or re-worded), not an absence to be printed over.
  * `absent-design`   -- the carrier states no such count, by design, and the reason is written in the row.
                         Zero matches is then the expected reading; if the carrier STARTS stating it, any hit
                         is still read against the owner (a new statement must agree like every other).

A row that can never fire is decoration, so the summary reports the row count and the firing count separately,
and the verdict is taken from the rows, never from the number of hits.  The declared patterns are narrow and
printed with the verdict: the list is the coordinate, so a reader sees what was and was not scanned.

Run:  python3 artefacts/assembly/counts_check.py                 exit 0 = every carrier agrees with the owner
      python3 artefacts/assembly/counts_check.py --selftest      the checker's own battery, on scratch copies
      python3 artefacts/assembly/counts_check.py --pkg <dir>     read another package root (the battery's route)
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # papers/issue-87/artefacts/assembly
PKG = os.path.dirname(os.path.dirname(HERE))               # papers/issue-87
OWNER_REL = os.path.join("artefacts", "assembly", "assembly-report.txt")
DIGEST_REL = os.path.join("artefacts", "results_digest.json")

# The carriers, and the house phrasings.  (file, regex with the number in group 1, what the number counts,
# what the row expects of the carrier, and -- for an absent-by-design row -- why it expects nothing there).
REQUIRED = "required"
ABSENT = "absent-design"
CARRIERS = [
    ("README.md", r'(\d+)\s+quantities read out', "quantities", REQUIRED,
     "the reproduction spec's own listing of what the run reads"),
    ("README.md", r'(\d+)\s+quantities, each read out', "quantities", REQUIRED,
     "the artefact table's description of the digest -- ADDED IN R419: this row carried a stale 55 while the "
     "checker's phrasing list did not reach it, so the copy no one had edited was the copy no check could see"),
    ("reproduce.sh", r'(\d+)\s+quantities read out', "quantities", REQUIRED,
     "the run's manifest states the digest's size"),
    ("README.md", r'(\d+)\s+numeric bindings', "bindings", REQUIRED,
     "the artefact table's description of the assembly"),
    ("README.md", r'(\d+)\s+numeric claims', "bindings", REQUIRED,
     "the section explaining how the prose's numbers are bound"),
    ("README.md", r'coverage (\d+)/\d+,', "entries", REQUIRED,
     "the reproduction spec's expected output line"),
    ("README.md", r'(\d+)\s+bindings', "bindings", REQUIRED,
     "the binding count itself"),
    ("reproduce.sh", r'BINDINGS=(\d+)', "bindings", REQUIRED,
     "the header the script asserts the printed count against"),
    ("reproduce.sh", r'COVERAGE=(\d+)', "entries", REQUIRED,
     "the header the script asserts the printed coverage against"),
    ("manuscript.md", r'(\d+)\s+numeric bindings', "bindings", ABSENT,
     "the manuscript states no such count of its own apparatus (read: grep -i bind over the built text -- "
     "the only hits are the citation markers [133] and a table row); a count added to the paper to feed this "
     "checker would be a claim in service of the apparatus, so the row declares the absence instead"),
]


def owner_counts(pkg):
    """Read the counts out of their owners: the assembly report, and the digest it was built from."""
    txt = io.open(os.path.join(pkg, OWNER_REL), encoding="utf-8").read()
    out = {}
    dig = json.load(io.open(os.path.join(pkg, DIGEST_REL), encoding="utf-8"))
    out["quantities"] = dig["n_quantities"]
    m = re.search(r'CHECK 3 bindings: (\d+) bound', txt)
    if m:
        out["bindings"] = int(m.group(1))
    m = re.search(r'CHECK 1 coverage: cited (\d+) distinct keys; missing (\d+)', txt)
    if m:
        out["entries"] = int(m.group(1))
        out["missing"] = int(m.group(2))
    m = re.search(r'bibliography: (\d+) entries', txt)
    if m:
        out["bibliography"] = int(m.group(1))
    return out


def check(pkg):
    """Returns (exit code, the report text).  Split from main() so the battery can read the verdict itself."""
    out = []
    own = owner_counts(pkg)
    out.append("owner: %s" % OWNER_REL)
    for k in sorted(own):
        out.append("  %-14s %d" % (k, own[k]))
    if "bindings" not in own or "entries" not in own:
        out.append("COUNTS: FAIL -- the owner does not print the counts this checker reads")
        return 1, "\n".join(out)
    rows, bad, lost = [], [], []
    for rel, pat, which, expect, why in CARRIERS:
        p = os.path.join(pkg, rel)
        if not os.path.exists(p):
            lost.append("%s: the carrier itself is absent" % rel)
            continue
        txt = io.open(p, encoding="utf-8").read()
        hits = re.findall(pat, txt)
        rows.append((rel, pat, which, expect, hits))
        for h in hits:
            if int(h) != own[which]:
                bad.append("%s: %r states %s, the assembly prints %d" % (rel, pat, h, own[which]))
    out.append("\ncarriers read (the declared phrasings, the row's expectation, and its reach):")
    for rel, pat, which, expect, hits in rows:
        if hits:
            shown = hits
        elif expect == REQUIRED:
            shown = "-- NOT PRESENT: this carrier must state the count --"
        else:
            shown = "-- absent by design --"
        out.append("  %-16s %-34s -> %-8s %-13s %s" % (rel, pat, which, expect, shown))
    fired = sum(1 for _, _, _, _, h in rows if h)
    required = sum(1 for _, _, _, e, _ in rows if e == REQUIRED)
    out.append("\n  rows: %d declared (%d required, %d absent-by-design) | firing: %d | required rows that fired: "
               "%d of %d" % (len(rows), required, len(rows) - required, fired, fired, required))
    for rel, pat, which, expect, hits in rows:
        if expect == REQUIRED and not hits:
            bad.append("%s: %r is no longer stated -- a count can be LOST as well as contradicted, and a "
                       "required row owes its presence (R419)" % (rel, pat))
    for rel, pat, which, expect, hits in rows:
        if expect == ABSENT and hits:
            out.append("  note: %s now states %r -- read against the owner above like any other statement"
                       % (rel, pat))
    out.append("")
    if bad or lost:
        for b in bad + lost:
            out.append("COUNTS: FAIL -- " + b)
        return 1, "\n".join(out)
    out.append("COUNTS: PASS -- every required carrier fired and agrees with the owner (%d reading(s); the "
               "row count above is the reach, not the hit count)" % fired)
    return 0, "\n".join(out)


def selftest():
    """The checker's own battery, on scratch copies of the package: each case must move the exit code.

    The failure this battery exists for is the one the previous version could not see: a required count
    REMOVED from a carrier.  Its absence case runs in the same battery as its successes (a checker is
    believed when it has been made to fail on purpose).
    """
    cases, ok = [], True
    with tempfile.TemporaryDirectory() as tmp:
        def scratch():
            dst = os.path.join(tmp, "pkg")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.makedirs(os.path.join(dst, "artefacts", "assembly"))
            for rel in (OWNER_REL, DIGEST_REL):
                shutil.copy(os.path.join(PKG, rel), os.path.join(dst, rel))
            for rel in ("README.md", "reproduce.sh", "manuscript.md"):
                shutil.copy(os.path.join(PKG, rel), os.path.join(dst, rel))
            return dst

        def case(name, mutate, expect_code):
            nonlocal ok
            dst = scratch()
            if mutate is not None:
                mutate(dst)
            code, txt = check(dst)
            graded = (code == expect_code)
            ok = ok and graded
            cases.append((name, expect_code, code, graded))

        def edit(rel, old, new):
            def apply(dst):
                p = os.path.join(dst, rel)
                t = io.open(p, encoding="utf-8").read()
                assert old in t, "plant not present: %r" % old
                io.open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
            return apply

        case("unmutated package", None, 0)
        case("a required count CONTRADICTED (README 133 bindings -> 132)",
             edit("README.md", "133 numeric bindings", "132 numeric bindings"), 1)
        case("a required count LOST from the run (reproduce.sh's quantities phrase removed)",
             edit("reproduce.sh", "76 quantities read out", "the digest"), 1)
        case("a stale copy in the phrasing the list had missed (README '76 quantities, each read out' -> 55)",
             edit("README.md", "76 quantities, each read out", "55 quantities, each read out"), 1)
        case("a required header changed (BINDINGS=133 -> 1337)",
             edit("reproduce.sh", "BINDINGS=133", "BINDINGS=1337"), 1)
        case("the owner itself changed (assembly report's binding count)",
             edit(OWNER_REL, "CHECK 3 bindings: 133 bound", "CHECK 3 bindings: 100 bound"), 1)
        case("a carrier absent (reproduce.sh deleted)",
             lambda dst: os.remove(os.path.join(dst, "reproduce.sh")), 1)
        case("a required count re-worded (README 'coverage 169/169,' -> 'coverage 169 of 169')",
             edit("README.md", "coverage 169/169,", "coverage 169 of 169,"), 1)
        case("the absent-by-design row STARTING to state a WRONG count (manuscript says 132)",
             edit("manuscript.md", "\n## References", "\n132 numeric bindings are checked.\n\n## References"), 1)
    print("COUNTS CHECKER SELFTEST -- %d case(s), %d caught" % (len(cases), sum(1 for c in cases if c[3])))
    for name, want, got, graded in cases:
        print("  %-6s %-84s exit %d (want %d)" % ("ok" if graded else "MISSED", name, got, want))
    print("SELFTEST: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    if "--pkg" in argv:
        code, txt = check(argv[argv.index("--pkg") + 1])
        print(txt)
        return code
    if "--selftest" in argv:
        return selftest()
    code, txt = check(PKG)
    print(txt)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
