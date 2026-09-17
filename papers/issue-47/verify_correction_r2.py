#!/usr/bin/env python3
"""Verify issue #47's correction ROUND 2 -- the absent-tree branch, read in both reader trees.

Round 2 has one required change: `reference-check.md` states the fact its own absent-gate path
requires.  A required change about a BRANCH has to be read in the tree that branch is for, so this
verifier builds that tree rather than arguing about it:

  * the ACCEPTANCE read, in a tree carrying no `.github/` (a path-limited export, made here by copying
    the package into a temporary directory whose `../../.github/` does not exist):
    `gate_read_v1.py --check` exits 0 and `reproduce.sh` prints `journal reference gate: NOT RUN` with
    `verdict: OK`;
  * the SAME read in the tree this file lives in, when that tree carries `.github/` (else SKIP with a
    reason);
  * every check is two-sided, and the control for the absent tree is the PUBLISHED report -- the one
    without the sentence -- planted into the same temporary tree, where the check must exit 1.  That
    control is the editor's own measurement of the defect, reproduced rather than quoted.

Run:  python3 verify_correction_r2.py
Writes correction_r2_verify.log BESIDE this package (a log path outside the package is a defect this
package has already recorded once).
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "reference-check.md")
REPRO = os.path.join(HERE, "reproduce.sh")
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
ABSENT_ANCHOR = "not in this tree"
LOG = os.path.join(HERE, "correction_r2_verify.log")

out = []


def say(s):
    out.append(s)
    print(s)


def run(args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.stdout + p.stderr, p.returncode


def export_without_github(dest):
    """A tree of this package that carries no `.github/` -- the reader tree the else-branch names."""
    pkg = os.path.join(dest, "papers", os.path.basename(HERE))
    os.makedirs(os.path.dirname(pkg), exist_ok=True)
    shutil.copytree(HERE, pkg, ignore=shutil.ignore_patterns("research", "__pycache__",
                                                             "correction_r2_verify.log", "*.pyc"))
    return pkg


def check_absent_tree():
    """Acceptance read 1: the branch passes in the tree it was written for."""
    fails = []
    tmp = tempfile.mkdtemp(prefix="issue47-r2-")
    try:
        pkg = export_without_github(tmp)
        if os.path.exists(os.path.join(tmp, ".github")):
            return ["the temporary tree unexpectedly carries .github/"], "the control tree is wrong"
        says, rc = run([sys.executable, "gate_read_v1.py", "--check"], pkg)
        if rc != 0:
            fails.append("gate_read_v1.py --check exits %d in a tree with no .github/: %s"
                         % (rc, says.strip()[-160:]))
        sst, src = run([sys.executable, "gate_read_v1.py", "--selftest"], pkg)
        if src != 0:
            fails.append("gate_read_v1.py --selftest exits %d in a tree with no .github/: %s"
                         % (src, sst.strip()[-160:]))
        # the same run through the package's one command: the step and the verdict
        rout, rrc = run(["bash", "reproduce.sh"], pkg)
        # The step's OWN lines: the verdict line and the NOT RUN reading.  A bare substring match
        # catches the README battery's own output, which mentions the step's subject ("step 7: the
        # journal reference gate") -- measured: the first run of this check reported a README PASS
        # line as the step's verdict, i.e. the check's object was not the object it named.
        step = [l for l in rout.splitlines()
                if l.strip().startswith("journal reference gate:") or l.strip().startswith("NOT RUN")]
        if rrc != 0:
            fails.append("reproduce.sh exits %d in a tree with no .github/" % rrc)
        if not any("NOT RUN" in l for l in step):
            fails.append("step 7 did not print the NOT RUN reading: %s" % step[:2])
        if not any("journal reference gate: OK" in l for l in step):
            fails.append("step 7 did not reach verdict OK: %s" % step[:2])
        detail = ("no `.github/`: --check exit %d, battery exit %d, reproduce.sh exit %d, step 7 reads "
                  "%r" % (rc, src, rrc, (step[-1].strip() if step else "?")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return fails, detail


def control_published_report():
    """The control: the PUBLISHED report (no sentence) in the same tree must fail the check."""
    tmp = tempfile.mkdtemp(prefix="issue47-r2ctl-")
    try:
        pkg = export_without_github(tmp)
        rpt = os.path.join(pkg, "reference-check.md")
        text = io.open(rpt, encoding="utf-8").read()
        if ABSENT_ANCHOR not in text:
            return ["the shipped report does not carry the anchor: nothing to remove"], "control not derivable"
        planted = text.replace(ABSENT_ANCHOR, "absent from this tree")
        if planted == text:
            return ["the control changed nothing"], "control not derivable"
        io.open(rpt, "w", encoding="utf-8").write(planted)
        says, rc = run([sys.executable, "gate_read_v1.py", "--check"], pkg)
        if rc == 0:
            return ["with the sentence removed the check still exits 0: the sentence is not read"], \
                   "control NOT caught"
        return [], "control caught: without the sentence the check exits %d (%s)" % (
            rc, says.strip().splitlines()[0][-80:] if says.strip() else "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_present_tree():
    """Acceptance read 2: the tree carrying `.github/` is unchanged."""
    if not os.path.exists(GATE):
        return [], "SKIP this tree carries no `.github/`: the present path is not the read taken here"
    fails = []
    says, rc = run([sys.executable, "gate_read_v1.py", "--check"], HERE)
    if rc != 0:
        fails.append("gate_read_v1.py --check exits %d in this tree: %s" % (rc, says.strip()[-160:]))
    sst, src = run([sys.executable, "gate_read_v1.py", "--selftest"], HERE)
    if src != 0:
        fails.append("gate_read_v1.py --selftest exits %d in this tree: %s" % (src, sst.strip()[-160:]))
    return fails, ("this tree carries the gate (%d lines): --check exit %d, battery exit %d"
                   % (io.open(GATE, "rb").read().decode("utf-8").count("\n"), rc, src))


def check_report_states_it():
    """The statement is in the artefact the branch reads, and it says what the branch needs."""
    text = io.open(REPORT, encoding="utf-8").read()
    fails = []
    if ABSENT_ANCHOR not in text:
        fails.append("the report does not carry %r" % ABSENT_ANCHOR)
    if "refgate.py" not in text:
        fails.append("the report does not name `refgate.py` where the branch reads it")
    if "another tree" not in text:
        fails.append("the report does not say the `copy:` reading describes a copy of another tree")
    return fails, ("the report states the absent-tree fact: %d occurrence(s) of %r, and it names the "
                   "copy reading as a copy of another tree"
                   % (text.count(ABSENT_ANCHOR), ABSENT_ANCHOR))


CHECKS = [
    ("R2-1 report states it", check_report_states_it),
    ("R2-2 absent reader tree", check_absent_tree),
    ("R2-3 present reader tree", check_present_tree),
]


def main():
    say("issue #47 correction round 2 -- the absent-tree branch, read in the trees it names")
    say("  package: %s" % HERE)
    say("")
    allfail = []
    for name, fn in CHECKS:
        fails, detail = fn()
        say("%-24s %s" % (name, "PASS" if not fails else "FAIL"))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        say("")
        allfail += fails
    cfails, cdetail = control_published_report()
    say("%-24s %s" % ("R2-2 control", "PASS" if not cfails else "FAIL"))
    say("   %s" % cdetail)
    for f in cfails:
        say("   !! %s" % f)
    say("")
    allfail += cfails
    say("R2: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
