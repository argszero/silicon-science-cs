#!/usr/bin/env python3
"""Issue #47 -- WHICH copy of the journal's reference gate this package read.

    python3 gate_read_v1.py            # check: the report names the copy this tree carries, and quotes it
    python3 gate_read_v1.py --selftest # liveness: one planted wrong statement per case

WHY THIS FILE EXISTS.  The journal's citation gate is not vendored into this package: `reproduce.sh`
reads it at `../../.github/tools/refgate.py`, so the copy it runs is **the one the reader's tree
carries** -- and a path does not fix which copy that is.  `reference-check.md` quoted an output and
named "the head this file was generated at": a revision of THIS package, not of the tool.  The quote was
therefore a claim about an instrument that did not say which instrument.  Measured 2026-09-17 and
re-takeable from this tree: the manuscript branch never touches `.github/`, so an export of the branch
carries its BASE's copy of the gate, and the two copies differ in ways a reader would otherwise read as
the author's omissions -- the base copy prints **no** `window:` line and its `--selftest` holds fewer
cases than the journal `main` copy, while both return the same verdict on this manuscript.

WHAT IS CHECKED, and against what:

* **the copy present in this tree** -- its line count, its sha256, the case count its own `--selftest`
  prints, and whether its run prints a `window:` line -- read by RUNNING it, never typed, and required
  to stand in a `copy:` line of `reference-check.md` carrying those same four facts;
* **the output the report quotes** -- required to be, verbatim, this copy's own output on
  `manuscript.md`;
* **every other `copy:` line** -- a reading of a copy this tree does not carry, so it must state the
  revision it was read at (`read at <rev>`).  A reading that names no revision is a claim about an
  unnamed copy, which is the defect this file exists for.

A gate that is not in this tree at all is reported as such -- a fact about the tree, not a defect of the
package -- and the check is then about the report's own statement of that fact.  A `copy:` block for a
copy the tree does carry but the report does not describe is a FAILURE, not a skip.

The battery plants one wrong statement per case (a sha, a case count, a quoted line, a missing
revision), each derived from the copy in this tree rather than pinned, and requires exactly that case to
be caught.
"""
import hashlib
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
REPORT = os.path.join(HERE, "reference-check.md")
MANUSCRIPT = "manuscript.md"
ABSENT_ANCHOR = "not in this tree"


def run(args, cwd=HERE):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.stdout + p.stderr, p.returncode


def identity(path):
    """The four facts about a copy, each read from the copy itself."""
    raw = io.open(path, "rb").read()
    src = raw.decode("utf-8")
    out, rc = run([sys.executable, path, "--selftest"])
    m = re.search(r"selftest: (\d+)/(\d+) cases ok", out)
    cases = int(m.group(1)) if m else None
    if m is None:
        return {"error": "the copy's `--selftest` printed no `N/N cases ok` line (exit %d)" % rc}
    runout, rrc = run([sys.executable, path, MANUSCRIPT])
    return {"lines": src.count("\n"), "sha12": hashlib.sha256(raw).hexdigest()[:12],
            "cases": cases, "cases_pair": (int(m.group(1)), int(m.group(2))),
            "window": any(l.strip().startswith("window:") for l in runout.splitlines()),
            "selftest_rc": rc, "run_rc": rrc, "output": runout.strip()}


def copy_line(ident, revision=None):
    return ("copy: %d lines, sha256 %s\u2026, --selftest %d/%d cases ok, %s%s"
            % (ident["lines"], ident["sha12"], ident["cases_pair"][0], ident["cases_pair"][1],
               "prints the window line" if ident["window"] else "prints no window line",
               ", read at %s" % revision if revision else ""))


def fenced_after(text, pos):
    """The first fenced block after `pos`, or None."""
    start = text.find("```", pos)
    if start == -1:
        return None
    end = text.find("```", start + 3)
    if end == -1:
        return None
    return text[start + 3:end].strip("\n")


def check(text, ident):
    """Read the report against the copy this tree carries (ident=None: the gate is not here)."""
    lines = re.findall(r"(?m)^copy: .*$", text)
    if ident is None:
        have = ABSENT_ANCHOR in text and "refgate.py" in text
        return have, ("the gate is not in this tree (%s); the report %s that fact" %
                      (GATE, "states" if have else "does NOT state"))
    want = copy_line(ident)
    mine = [l for l in lines if ident["sha12"] in l]
    if len(mine) != 1:
        return False, ("the copy this tree carries (sha256 %s\u2026) stands in %d `copy:` line(s); the "
                       "report must name it exactly once" % (ident["sha12"], len(mine)))
    if mine[0].strip() != want:
        return False, ("the `copy:` line for this tree's copy states %r; the copy itself reads %r"
                       % (mine[0].strip(), want))
    quoted = fenced_after(text, text.index(mine[0]))
    if quoted != ident["output"]:
        return False, ("the output quoted under this tree's copy is not the copy's own run on %s\n"
                       "  quoted: %r\n  run:    %r"
                       % (MANUSCRIPT, (quoted or "")[:120], ident["output"][:120]))
    foreign = [l for l in lines if ident["sha12"] not in l]
    nameless = [l for l in foreign if "read at " not in l]
    if nameless:
        return False, ("%d `copy:` line(s) describe a copy this tree does not carry and name no "
                       "revision: %s" % (len(nameless), nameless))
    return True, ("this tree's copy (%d lines, sha256 %s\u2026, --selftest %d/%d, %s) is named once "
                  "and quoted verbatim; %d further cop(y|ies) named with a revision"
                  % (ident["lines"], ident["sha12"], ident["cases_pair"][0], ident["cases_pair"][1],
                     "prints the window line" if ident["window"] else "prints no window line",
                     len(foreign)))


# One check, named by this module's own list (so the count a reader states about this tool's
# battery is the tool's own -- `readme_check_v1.py` asks for it).
CHECKS = ["gate_read/copy_is_named_and_quoted"]

# One planted defect per case, each DERIVED from the copy in this tree: a pinned anchor turns a
# legitimate change of copy into a red battery (the defect R354 recorded).  The five cases fall in
# two groups, and each group is derivable in the tree it belongs to:
#
#   * four about the copy THIS tree carries  -- derivable only where there is a copy to read;
#   * one about the ABSENT-tree statement      -- derivable in BOTH trees, because the report states
#     that fact unconditionally (correction round 2, 2026-09-17).  Before that case existed, a
#     path-limited export could not run this battery at all: `plant` returned None for every kind.
MUTATIONS = [
    (CHECKS[0], "sha"),
    (CHECKS[0], "cases"),
    (CHECKS[0], "output"),
    (CHECKS[0], "revision"),
    (CHECKS[0], "absent"),
]

# Which tree each case belongs to.  A case that belongs to the OTHER tree is SKIPped with a reason
# rather than failed: the copy cases read a file this tree does not have, and the absent case reads a
# path this tree does not take.  Every case that belongs to the tree at hand must be caught -- a
# battery that skipped everything would be caught by the counts below.
COPY_CASES = ("sha", "cases", "output", "revision")


def plant(kind, text, ident):
    if ident is None and kind != "absent":
        raise AssertionError("case %r needs a copy, and this tree carries none" % kind)
    if kind == "sha":
        other = ("0" if ident["sha12"][-1] != "0" else "1")
        return text.replace(ident["sha12"], ident["sha12"][:-1] + other)
    if kind == "cases":
        a, b = ident["cases_pair"]
        return text.replace("--selftest %d/%d cases ok" % (a, b), "--selftest %d/%d cases ok" % (a - 1, b))
    if kind == "output":
        m = re.search(r"(?m)^  entries=(\d+)", text)
        if not m:
            return None
        return text.replace(m.group(0), "  entries=%d" % (int(m.group(1)) - 1))
    if kind == "revision":
        foreign = [l for l in re.findall(r"(?m)^copy: .*$", text) if ident["sha12"] not in l]
        if not foreign:
            return None
        return text.replace(foreign[0], foreign[0].replace(", read at ", ", revision "))
    if kind == "absent":
        # The statement the absent-tree branch of `check()` requires, moved to a near-miss: the
        # paragraph stays about a tree without `.github/` and stops carrying the string the branch
        # reads.  EVERY occurrence goes -- the statement carries the anchor twice, and a planter that
        # replaced only the first left the read satisfied (measured: the case read "NOT caught" the
        # first time it ran, because the second occurrence still answered the branch's test).
        if ABSENT_ANCHOR not in text:
            return None
        return text.replace(ABSENT_ANCHOR, "absent from this export")
    raise AssertionError(kind)


def main():
    text = io.open(REPORT, encoding="utf-8").read()
    if not os.path.exists(GATE):
        ok, detail = check(text, None)
        print("%s   gate_read/%s   %s" % ("PASS" if ok else "FAIL", "copy_is_named_and_quoted", detail))
        return 0 if ok else 1
    ident = identity(GATE)
    if "error" in ident:
        print("FAIL   gate_read/copy_is_named_and_quoted   %s" % ident["error"])
        return 1
    ok, detail = check(text, ident)
    print("%s   gate_read/%s   %s" % ("PASS" if ok else "FAIL", "copy_is_named_and_quoted", detail))
    return 0 if ok else 1


def selftest():
    text = io.open(REPORT, encoding="utf-8").read()
    ident = None if not os.path.exists(GATE) else identity(GATE)
    if ident is not None and "error" in ident:
        print("FAIL   the battery cannot run: %s" % ident["error"])
        return 1
    base_ok, base_detail = check(text, ident)
    if not base_ok:
        print("FAIL   the battery needs a clean base; already failing: %s" % base_detail)
        return 1
    ok, detail = check(text, ident)
    print("%-6s %-56s %s" % ("PASS" if ok else "FAIL", "control/unmodified_report", detail[:90]))
    bad = 0 if ok else 1
    skipped = 0
    for name, kind in MUTATIONS:
        # A case about the copy this tree carries cannot be derived where there IS no copy -- and
        # that is a property of the tree, not a defect of the package.  It is reported as SKIP WITH A
        # REASON rather than as a failure (the branch that reads the absent tree is what carries the
        # verdict there), and the case that IS derivable in both trees -- the absent statement -- is
        # what keeps this battery alive in an export that carries no `.github/`.
        if ident is None and kind in COPY_CASES:
            print("SKIP   %-56s no copy in this tree to derive the case from" % ("%s [%s]" % (name, kind)))
            skipped += 1
            continue
        if ident is not None and kind not in COPY_CASES:
            print("SKIP   %-56s this tree carries a copy, so the absent-tree paragraph is not the "
                  "read taken here" % ("%s [%s]" % (name, kind)))
            skipped += 1
            continue
        planted = plant(kind, text, ident)
        if planted is None:
            print("FAIL   %-56s the case could not be derived from this tree" % name)
            bad += 1
            continue
        if planted == text:
            print("FAIL   %-56s the planted text is identical to the shipped report" % name)
            bad += 1
            continue
        was_ok, was_detail = check(planted, ident)
        good = not was_ok
        print("%-6s %-56s %s" % ("PASS" if good else "FAIL", "%s [%s]" % (name, kind),
                                 ("caught: " + was_detail[:56]) if good else "NOT caught"))
        bad += 0 if good else 1
    derived = len(MUTATIONS) - skipped
    print("selftest: %d case(s), %d failure(s) over 1 check -- %d derived in this tree, %d SKIPped%s"
          % (len(MUTATIONS) + 1, bad, derived, skipped,
             " (no copy in this tree)" if ident is None else ""))
    if derived == 0:
        # A battery in which every case was skipped is not a battery: it would print `0 failure(s)`
        # and pass while reading nothing, which is the shape this file exists to catch.
        print("FAIL   no case could be derived in this tree: the battery read nothing")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
