#!/usr/bin/env python3
"""The file table in README.md, read against the files this package actually ships.

Why this exists. `price_search.py` and the artefact it writes were in the package, were run by
`reproduce.sh` as step 6, and appeared in no row of README.md's file table: a reader who took the
table as the package's contents would not know the section-8 search existed, and nothing in the
package could fail because of it. This is the same defect as a stated step count drifting from the
counted one -- a document's list is a second copy of a fact the filesystem owns, and a copy drifts.

Both directions are read, because they are different defects:

  * **a shipped file with no row** -- the reader's inventory is narrower than the package (this is
    the one that happened);
  * **a row naming a file that is not shipped** -- the inventory describes a package that does not
    exist, which is what a renamed or deleted file leaves behind.

The shipped set is a filesystem walk, not `git ls-files`: `reproduce.sh` has to run in a
`git archive` export, where there is no `.git`, and a check only the author can run is not a check.
The one exclusion is the run's own log (`*.log`), which the run creates and which is not part of the
package; it is printed rather than silently dropped, and the counts compared/skipped are printed too.

Usage:
  ./check_file_table.py                  # this package
  ./check_file_table.py --readme R --root D   # other copies (the selftest's fixtures)
  ./check_file_table.py --selftest       # both directions on fixtures, plus the log exclusion

Exit codes: 0 the two sets are one set; 1 they differ (each difference is named); 3 NOT RUN -- no
file table was found, so nothing was compared and no verdict is taken.
"""
import argparse
import os
import re
import sys
import tempfile

SKIP = re.compile(r'\.log$')
ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|', re.M)
SECTION = re.compile(r'^##\s+Files\s*$', re.M)
NEXT = re.compile(r'^##\s', re.M)


def rows(readme_text):
    """The first-column paths of the file table, and None when there is no such table."""
    m = SECTION.search(readme_text)
    if not m:
        return None
    rest = readme_text[m.end():]
    nxt = NEXT.search(rest)
    block = rest[:nxt.start()] if nxt else rest
    return [r for r in ROW.findall(block)]


def shipped(root):
    """Every file the package ships, as relative paths; the run log is returned separately."""
    out, skipped = [], []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(base, f), root).replace(os.sep, "/")
            (skipped if SKIP.search(rel) else out).append(rel)
    return sorted(out), sorted(skipped)


def compare(readme_text, root):
    tabled = rows(readme_text)
    if tabled is None:
        return 3, ["no `## Files` table in README.md"], 0, 0
    have, skipped = shipped(root)
    named, seen = [], set()
    dupes = []
    for r in tabled:
        if r in seen:
            dupes.append(r)
        seen.add(r)
        named.append(r)
    missing_row = [f for f in have if f not in seen]
    missing_file = [r for r in named if r not in set(have)]
    msgs = []
    for f in missing_row:
        msgs.append("shipped but in no row: %s" % f)
    for r in missing_file:
        msgs.append("row names a file this package does not ship: %s" % r)
    for d in dupes:
        msgs.append("two rows for one file: %s" % d)
    if skipped:
        msgs.append("skipped (the run's own log, not part of the package): %s" % ", ".join(skipped))
    msgs.append("compared %d row(s) against %d shipped file(s), %d skipped"
                % (len(named), len(have), len(skipped)))
    return (1 if (missing_row or missing_file or dupes) else 0), msgs, len(named), len(have)


def selftest():
    """Every verdict the two directions can take, on fixtures, with the exclusion demonstrated."""
    cases, fails = 0, []
    with tempfile.TemporaryDirectory() as tmp:
        def fixture(name, files, table):
            d = os.path.join(tmp, name)
            os.makedirs(d, exist_ok=True)
            for f in files:
                path = os.path.join(d, f)
                os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(f) else None
                open(path, "w").close()
            readme = "## Files\n\n| file | authored or derived | what it holds |\n|---|---|---|\n"
            readme += "".join("| `%s` | authored | x |\n" % t for t in table)
            readme += "\n## Next section\n"
            return readme, d

        def case(label, want, readme, d):
            nonlocal cases
            cases += 1
            rc, msgs, _, _ = compare(readme, d)
            if rc != want:
                fails.append("%s: expected exit %d, got %d (%s)" % (label, want, rc, "; ".join(msgs)))

        # (1) one set: table and files agree.
        case("clean pair", 0, *fixture("clean", ["a.py", "b.json"], ["a.py", "b.json"]))
        # (2) a shipped file with no row -- the defect this gate was written for.
        case("file without a row", 1, *fixture("norow", ["a.py", "price_search.py"], ["a.py"]))
        # (3) a row naming a file that is not shipped.
        case("row without a file", 1, *fixture("nofile", ["a.py"], ["a.py", "gone.py"]))
        # (4) the same file rowed twice.
        case("duplicate row", 1, *fixture("dup", ["a.py"], ["a.py", "a.py"]))
        # (5) no table at all is NOT RUN, never a pass.
        cases += 1
        rc, msgs, _, _ = compare("# nothing here\n\n## Other\n", tmp)
        if rc != 3:
            fails.append("no table: expected exit 3, got %d (%s)" % (rc, "; ".join(msgs)))
        # (6) the run's log is excluded, and the exclusion is printed.
        readme, d = fixture("log", ["a.py"], ["a.py"])
        open(os.path.join(d, "reproduce.log"), "w").close()
        cases += 1
        rc, msgs, _, _ = compare(readme, d)
        if rc != 0 or not any("skipped" in m for m in msgs):
            fails.append("run log: expected exit 0 with the skip printed, got %d (%s)"
                         % (rc, "; ".join(msgs)))
    for f in fails:
        sys.stderr.write("FAIL %s\n" % f)
    sys.stdout.write("selftest: %d/%d case(s) behaved as required\n" % (cases - len(fails), cases))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="read README.md's file table against the shipped files")
    ap.add_argument("--readme")
    ap.add_argument("--root")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    here = os.path.dirname(os.path.abspath(__file__))
    readme = args.readme or os.path.join(here, "README.md")
    root = args.root or here
    with open(readme, encoding="utf-8") as fh:
        text = fh.read()
    rc, msgs, _, _ = compare(text, root)
    for m in msgs:
        (sys.stderr if rc else sys.stdout).write(("FINDING " if rc == 1 else "") + m + "\n")
    if rc == 3:
        sys.stderr.write("NOT RUN: %s\n" % msgs[0])
    return rc


if __name__ == "__main__":
    sys.exit(main())
