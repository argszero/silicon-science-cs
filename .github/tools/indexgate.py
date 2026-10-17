#!/usr/bin/env python3
"""indexgate_v1 - the published index read against the packages it indexes.

`papers/README.md`'s table is the journal's public record of publication: the one
artefact a reader outside this machine reads to learn what has been published. Its
own prose states the source of every column - *Issue* and *Manuscript* from the path
convention, *Author* from the registration's `Author instance` line, *Title* from the
manuscript's own title, *Published* from the ACCEPT merge's **UTC** date - and it says
plainly what reads them:

    No step reads this file's columns - it is the journal's public record and its
    readers are outside the machine - so the sources are stated here for a reader
    who checks a row.

That sentence is true, and it is the defect this tool answers: a **copy** (the table)
of an **artefact** (the merged packages under `papers/issue-<N>/`) with no step that
re-compares them. A row is written once, by hand, at the moment of an ACCEPT; from
then on nothing notices if a later merge lands without one, if a row links a
neighbour's manuscript, if a title is edited in one place and not the other, or if
the date is written in the writer's local epoch rather than the stated UTC one.

**What this tool reads, and what it does not.**

  * the **row set** is parsed out of `papers/README.md`'s table - the table's own
    lines carrying an `| #N |` cell - and the **package set** is every
    `papers/issue-<N>/` directory in the tree. A package directory on `main` is a
    publication (the research workspace is git-ignored, so a registration in
    preparation has no directory here).
  * **set equality is checked in both directions**: a package with no row is a
    **stale index** (the failure the file itself names - "if a merged manuscript is
    missing from the table below, the index is stale"); a row whose package is not in
    the tree is a **pointer to nothing**.
  * **the link is read against the row that carries it**: a row for `#N` whose
    manuscript cell targets `issue-<M>/manuscript.md` is reported as the mismatch it
    is, and a target that does not exist is reported separately from one that names
    the wrong package.
  * **the title is read at the manuscript**: the row's `Title` cell against the first
    ATX heading (`# ...`) of `papers/issue-<N>/manuscript.md`, whitespace-normalised.
    The file states the manuscript is the source, and the issue title is not (it
    carries a `[Submission]` prefix).
  * **the date is read at the commit that added the manuscript**, in **UTC**: the
    oldest commit `git log --diff-filter=A` returns for
    `papers/issue-<N>/manuscript.md`, its committer date converted to UTC. The epoch
    is not a detail - the file states it because the editor's local date can be the
    next day - and slicing the first ten characters of a `%cI` stamp reads the
    **local** date. That is this tool's own first mistake, made by hand at R592 and
    kept as a plant (`date-local-epoch`).
  * **the order is read as a property**: the file says a new row is appended below the
    last published row, so `Published` is non-decreasing down the table. A row
    inserted in a neighbour's place breaks that without breaking any cell.
  * **the empty-state placeholder is a state, not a fixture**: the file says the
    placeholder row existed only until the first ACCEPT and never returns, so its
    presence beside real rows is a finding.

**What this tool does not decide.** It does not read the **`Author` cell**: its source
is the registration thread on GitHub, not this tree, and a tool that reached the API
would be a tool that cannot run offline. It prints that cell as **NOT READ** rather
than counting it as agreed - an unread column is not a passing one. It does not decide
whether a publication was *warranted* (that is the decision's business) and it does not
read the manuscript's content. It does not resolve the tree's git objects: it needs a
**checkout** (a `git archive` export carries no `.git`), so over an export the date
column is `NOT RUN` with that reason and never a pass - `README.md` -> *A reading owes
its tree*.

Classes, every one counted and named:
  MISSING ROW    a package on disk with no row in the index
  STRAY ROW      a row whose package is not in the tree
  DUPLICATE ROW  one issue carried by more than one row
  LINK           a row's manuscript cell naming another issue, or a target that is absent
  TITLE          the row's title and the manuscript's own heading disagree
  DATE           the row's `Published` and the adding commit's UTC date disagree
  ORDER          `Published` decreases down the table
  PLACEHOLDER    the empty-state row appears beside real rows
  FORM           a table line that names no issue, or a row whose cell count is not five

Verdicts and exit codes: `INDEXGATE: PASS` (0), `INDEXGATE: FAIL` (1),
`INDEXGATE: NOT RUN` (2) with its reason. A set this tool could not read is never a
set it cleared.

usage:  python3 .github/tools/indexgate.py            # read this checkout
        python3 .github/tools/indexgate.py --root DIR  # read another tree
        python3 .github/tools/indexgate.py --json
        python3 .github/tools/indexgate.py --selftest  # the plant battery
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

INDEX = os.path.join("papers", "README.md")
ISSUE_DIR = re.compile(r"^issue-(\d+)$")
ROW = re.compile(r"^\|\s*#(\d+)\s*\|")
LINK = re.compile(r"^\[[^\]]*\]\(issue-(\d+)/manuscript\.md\)$")
PLACEHOLDER = "(no published papers yet)"

# a table line that is neither a row nor a separator nor the header
SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")


def packages(root):
    """The published set: every papers/issue-<N>/ directory, as an int."""
    base = os.path.join(root, "papers")
    if not os.path.isdir(base):
        return None
    out = []
    for name in sorted(os.listdir(base)):
        if ISSUE_DIR.match(name) and os.path.isdir(os.path.join(base, name)):
            out.append(int(ISSUE_DIR.match(name).group(1)))
    return out


def table(path):
    """[(issue, cells, lineno)] plus the placeholder line numbers and form findings."""
    rows, placeholders, forms = [], [], []
    if not os.path.isfile(path):
        return None, placeholders, forms
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            s = line.rstrip("\n")
            if not s.startswith("|") or SEPARATOR.match(s):
                continue
            if PLACEHOLDER in s:
                placeholders.append(i)
                continue
            m = ROW.match(s)
            if not m:
                # the header row prints its cells; a line naming no issue is a row
                # this index cannot carry, and it is reported rather than skipped.
                if "Issue" not in s.split("|")[1]:
                    forms.append((i, "table line naming no issue: %s" % s[:70]))
                continue
            cells = [c.strip() for c in s.strip().strip("|").split("|")]
            if len(cells) != 5:
                forms.append((i, "row #%s carries %d cell(s), not 5 (a `|` inside a cell?)"
                              % (m.group(1), len(cells))))
                continue
            rows.append((int(m.group(1)), cells, i))
    return rows, placeholders, forms


def manuscript_title(root, issue):
    path = os.path.join(root, "papers", "issue-%d" % issue, "manuscript.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                return m.group(1)
    return None


def _norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def added_utc_date(root, issue):
    """(date_iso, None) for the commit that added the manuscript, else (None, reason)."""
    if not os.path.isdir(os.path.join(root, ".git")):
        return None, "no .git (an exported tree carries no history)"
    rel = "papers/issue-%d/manuscript.md" % issue
    proc = subprocess.run(["git", "-C", root, "log", "--diff-filter=A",
                           "--format=%cI", "--", rel], capture_output=True, text=True)
    if proc.returncode != 0:
        return None, "git log failed: %s" % proc.stderr.strip()[:80]
    stamps = [l for l in proc.stdout.strip().split("\n") if l.strip()]
    if not stamps:
        return None, "no commit in this history adds %s" % rel
    oldest = stamps[-1].strip()
    # %cI carries the committer's own offset; the row's epoch is UTC.  Some git
    # builds print a bare `Z` for UTC, which `datetime.fromisoformat` accepts only
    # from Python 3.11 - and the declared base interpreter here is 3.9.6, where it
    # raises.  The stamp is normalised before it is parsed.
    text = oldest[:-1] + "+00:00" if oldest.endswith("Z") else oldest
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None, "cannot parse the commit date %r" % oldest
    return stamp.astimezone(timezone.utc).date().isoformat(), None


def read_index(root):
    """Return the report dict.  No printing here."""
    report = {"root": root, "rows": [], "packages": [], "findings": [],
              "unread": [], "verdict": None, "reason": None,
              "titles_ok": 0, "dates_ok": 0, "dates_not_run": 0}
    pkgs = packages(root)
    idx = os.path.join(root, INDEX)
    if pkgs is None:
        report.update(verdict="NOT RUN", reason="no papers/ directory in this tree")
        return report
    rows, placeholders, forms = table(idx)
    if rows is None:
        report.update(verdict="NOT RUN", reason="no %s in this tree" % INDEX,
                      packages=pkgs)
        return report
    if not rows and not pkgs:
        report.update(verdict="NOT RUN", packages=pkgs,
                      reason="no published package and no row - nothing to compare")
        return report
    report["packages"] = pkgs
    report["rows"] = [r[0] for r in rows]
    findings = report["findings"]
    for lineno, what in forms:
        findings.append(("FORM", "line %d: %s" % (lineno, what)))
    for lineno in placeholders:
        if rows:
            findings.append(("PLACEHOLDER",
                             "line %d: the empty-state row appears beside %d real row(s)"
                             % (lineno, len(rows))))

    seen = {}
    for issue, cells, lineno in rows:
        seen.setdefault(issue, []).append(lineno)
    for issue, lines in sorted(seen.items()):
        if len(lines) > 1:
            findings.append(("DUPLICATE ROW", "#%d carried by lines %s"
                             % (issue, ", ".join(str(l) for l in lines))))

    row_set = sorted(seen)
    for issue in pkgs:
        if issue not in seen:
            findings.append(("MISSING ROW",
                             "#%d has papers/issue-%d/ on disk and no row in the index"
                             % (issue, issue)))
    for issue in row_set:
        if issue not in pkgs:
            findings.append(("STRAY ROW",
                             "#%d has a row and no papers/issue-%d/ in this tree"
                             % (issue, issue)))

    previous = None
    for issue, cells, lineno in rows:
        _, title, _author, published, link = cells
        if issue not in pkgs:
            # STRAY ROW already names it; reading a title and a date at a package
            # that is not here would report an absence this tree has no control for.
            if published and previous and published < previous:
                findings.append(("ORDER", "#%d line %d: Published %s comes after %s"
                                 % (issue, lineno, published, previous)))
            if published:
                previous = published
            continue
        m = LINK.match(link)
        if not m:
            findings.append(("LINK", "#%d line %d: the manuscript cell is not "
                                     "`[...](issue-<N>/manuscript.md)`: %s"
                             % (issue, lineno, link[:60])))
        else:
            target = int(m.group(1))
            if target != issue:
                findings.append(("LINK", "#%d line %d: the cell targets issue-%d"
                                 % (issue, lineno, target)))
            elif not os.path.isfile(os.path.join(root, "papers", "issue-%d" % issue,
                                                 "manuscript.md")):
                findings.append(("LINK", "#%d line %d: issue-%d/manuscript.md is absent"
                                 % (issue, lineno, issue)))
        truth = manuscript_title(root, issue)
        if truth is None:
            findings.append(("TITLE", "#%d line %d: no `# ` heading in "
                                      "papers/issue-%d/manuscript.md"
                             % (issue, lineno, issue)))
        elif _norm(title) != _norm(truth):
            report["titles_ok"] += 0
            findings.append(("TITLE", "#%d line %d: row %r != manuscript %r"
                             % (issue, lineno, _norm(title)[:70], _norm(truth)[:70])))
        else:
            report["titles_ok"] += 1

        date, why = added_utc_date(root, issue)
        if date is None:
            report["dates_not_run"] += 1
            if why not in report["unread"]:
                report["unread"].append(why)
        elif published != date:
            findings.append(("DATE", "#%d line %d: row reads %s, the adding commit's "
                                     "UTC date is %s" % (issue, lineno, published, date)))
        else:
            report["dates_ok"] += 1

        if published and previous and published < previous:
            findings.append(("ORDER", "#%d line %d: Published %s comes after %s"
                             % (issue, lineno, published, previous)))
        if published:
            previous = published

    if findings:
        report["verdict"] = "FAIL"
    elif report["dates_not_run"]:
        # a column this tool claims to read and could not is not a column it cleared
        report["verdict"] = "NOT RUN"
        report["reason"] = ("%d of %d date(s) could not be read: %s"
                            % (report["dates_not_run"], len(rows),
                               "; ".join(report["unread"])[:160]))
    else:
        report["verdict"] = "PASS"
    return report


def render(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return
    print("indexgate_v1 - the published index read against the packages it indexes")
    print("root: %s" % report["root"])
    if report["verdict"] == "NOT RUN":
        print("INDEXGATE: NOT RUN - %s" % report["reason"])
        return
    print("set: %d row(s) in %s - %d package(s) under papers/"
          % (len(report["rows"]), INDEX, len(report["packages"])))
    print("instrument: `git log --diff-filter=A` for the commit that added "
          "<package>/manuscript.md, committer date read in UTC")
    print("author cell: NOT READ - its source is the registration thread, "
          "not this tree")
    rows = max(len(report["rows"]), 1)
    print("  titles: %d/%d agree with the manuscript's own first heading"
          % (report["titles_ok"], rows))
    if report["dates_not_run"]:
        print("  dates: %d/%d read (NOT RUN for %d - %s)"
              % (report["dates_ok"], rows, report["dates_not_run"],
                 "; ".join(report["unread"])[:120]))
    else:
        print("  dates: %d/%d agree with the adding commit's UTC date"
              % (report["dates_ok"], rows))
    if report["findings"]:
        for cls, detail in report["findings"]:
            print("  FINDING %-14s %s" % (cls, detail))
        print("INDEXGATE: FAIL - %d finding(s)" % len(report["findings"]))
    else:
        print("INDEXGATE: PASS - the table is as wide as the packages it indexes")


# --------------------------------------------------------------------------- plants

def _plant(root, files, when="2026-10-14T09:00:00+00:00"):
    """A throwaway checkout: a git repo with the given files and one commit."""
    os.makedirs(root)
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    for name, text in files.items():
        path = os.path.join(root, name)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    env = dict(os.environ,
               GIT_AUTHOR_NAME="plant", GIT_AUTHOR_EMAIL="plant@example.invalid",
               GIT_COMMITTER_NAME="plant", GIT_COMMITTER_EMAIL="plant@example.invalid",
               GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "-C", root, "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "plant"],
                   check=True, env=env, capture_output=True)


HEAD = ("| Issue | Title | Author | Published | Manuscript |\n"
        "|-------|-------|--------|-----------|-------------|\n")


def _index(*rows):
    return "# Published Papers\n\n" + HEAD + "".join(rows)


def _row(n, title, date="2026-10-14", author="argszero", target=None):
    return ("| #%d | %s | `%s` | %s | [manuscript](issue-%d/manuscript.md) |\n"
            % (n, title, author, date, n if target is None else target))


MANUSCRIPT = "# The Knob Is Not the Curve\n\nBody.\n"

PLANT = {
    "clean": {
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "missing-row": {                      # a merged package with no row: stale index
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
        "papers/issue-8/manuscript.md": "# Another Paper\n\nBody.\n",
    },
    "stray-row": {                        # a row whose package is not in the tree
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve"),
                                   _row(9, "Gone", date="2026-10-14")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "wrong-link": {                       # the row links its neighbour's manuscript
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve", target=8)),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
        "papers/issue-8/manuscript.md": "# Another Paper\n\nBody.\n",
        "papers/issue-8/.keep": "",
    },
    "title-differs": {
        "papers/README.md": _index(_row(7, "The Knob Is the Curve")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "date-local-epoch": {                 # 2026-10-14T17:00Z is 2026-10-15 at +08:00
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve", date="2026-10-15")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "duplicate-row": {
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve"),
                                   _row(7, "The Knob Is Not the Curve")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "out-of-order": {
        "papers/README.md": _index(_row(8, "Another Paper", date="2026-10-14"),
                                   _row(7, "The Knob Is Not the Curve", date="2026-10-13")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
        "papers/issue-8/manuscript.md": "# Another Paper\n\nBody.\n",
    },
    "placeholder-with-rows": {
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve"),
                                   "| — | *(no published papers yet)* | — | — | — |\n"),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "empty-index": {                      # nothing published: a set it cannot compare
        "papers/README.md": _index("| — | *(no published papers yet)* | — | — | — |\n"),
    },
    "title-no-heading": {                 # a manuscript whose title is not an ATX `# ` line
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve")),
        "papers/issue-7/manuscript.md": "The Knob Is Not the Curve\n\nBody.\n",
    },
    "no-index": {
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
    "exported-tree": {                    # an export carries the files and no history
        "papers/README.md": _index(_row(7, "The Knob Is Not the Curve")),
        "papers/issue-7/manuscript.md": MANUSCRIPT,
    },
}

# plants whose commit is written at a local-evening UTC instant, so a local-date
# slice disagrees with the stated epoch
WHEN = {"date-local-epoch": "2026-10-14T17:00:00+00:00"}


def _run(root):
    here = os.path.abspath(__file__)
    proc = subprocess.run([sys.executable, here, "--root", root],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout


def selftest():
    expect = {
        "clean": ("PASS", 0),
        "missing-row": ("FAIL", 1),
        "stray-row": ("FAIL", 1),
        "wrong-link": ("FAIL", 1),
        "title-differs": ("FAIL", 1),
        "date-local-epoch": ("FAIL", 1),
        "duplicate-row": ("FAIL", 1),
        "out-of-order": ("FAIL", 1),
        "placeholder-with-rows": ("FAIL", 1),
        "title-no-heading": ("FAIL", 1),
        "empty-index": ("NOT RUN", 2),
        "no-index": ("NOT RUN", 2),
        "exported-tree": ("NOT RUN", 2),
    }
    # each finding must also name the member it caught, not only the verdict
    member = {
        "missing-row": "MISSING ROW",
        "stray-row": "STRAY ROW",
        "wrong-link": "targets issue-8",
        "title-differs": "TITLE",
        "date-local-epoch": "UTC date is 2026-10-14",
        "duplicate-row": "DUPLICATE ROW",
        "out-of-order": "ORDER",
        "placeholder-with-rows": "PLACEHOLDER",
        "title-no-heading": "no `# ` heading",
        "exported-tree": "no .git",
    }
    tmp = tempfile.mkdtemp(prefix="indexgate-selftest-")
    cases, ok = [], 0
    try:
        for label, files in PLANT.items():
            root = os.path.join(tmp, label)
            _plant(root, files, WHEN.get(label, "2026-10-14T09:00:00+00:00"))
            if label == "exported-tree":
                # what `git archive` gives a verifier: the tracked files, no .git
                shutil.rmtree(os.path.join(root, ".git"))
            code, out = _run(root)
            # the verdict is read off the line the tool prints for it, never from a
            # substring anywhere in the output: an unread date prints "NOT RUN" in a
            # report whose verdict line is FAIL.
            m = re.search(r"^INDEXGATE: (PASS|FAIL|NOT RUN)", out, re.M)
            verdict = m.group(1) if m else "NO VERDICT LINE"
            want, want_code = expect[label]
            good = verdict == want and code == want_code
            if label in member and member[label] not in out:
                good = False
            cases.append((label, good, "%s/exit %d (want %s/exit %d)"
                          % (verdict, code, want, want_code)))
            ok += 1 if good else 0
        # the negative control: a failing plant read with its row corrected
        root = os.path.join(tmp, "title-differs")
        with open(os.path.join(root, "papers", "README.md"), "w", encoding="utf-8") as fh:
            fh.write(_index(_row(7, "The Knob Is Not the Curve")))
        code, out = _run(root)
        good = code == 0 and "INDEXGATE: PASS" in out
        cases.append(("title-differs + row corrected -> PASS", good, "exit %d" % code))
        ok += 1 if good else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for label, good, detail in cases:
        print("  [%s] %-46s %s" % ("ok" if good else "FAIL", label, detail))
    print("selftest: %d/%d cases ok" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    as_json = "--json" in argv
    root = os.getcwd()
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            root = os.path.abspath(argv[i + 1])
    if not os.path.isdir(root):
        print("indexgate: %s is not a directory" % root, file=sys.stderr)
        return 2
    report = read_index(root)
    render(report, as_json)
    if report["verdict"] == "PASS":
        return 0
    if report["verdict"] == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
