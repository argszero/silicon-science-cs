#!/usr/bin/env python3
"""Verify issue #47's correction ROUND 3 -- the durability of the report's attributions.

Round 3 has one required change, stated by the round as an OUTCOME rather than as a re-take: the report
must not be *required* to name the copy of the journal's reference gate **that the reader's tree
carries**.  That copy is the journal's own file and it moves as ordinary journal work, so a requirement
that is green only at the head it was generated at is a requirement the package cannot hold.  The three
reads the amendment names are taken here, each in the tree it is about:

  * READ 1 -- this checkout: `gate_read_v1.py --check` exits 0 and `--selftest` exits 0;
  * READ 2 -- a PATH-LIMITED EXPORT of this head (`git archive <rev> papers/issue-47`, which carries
    no `.github/`): both exit 0;
  * READ 3 -- a copy of this head whose `.github/tools/refgate.py` differs by **one appended comment
    line**: both exit 0.  This is the read the round exists for.

Each read is two-sided, because a green read that cannot go red reads nothing: in trees 2 and 3 the
report's primary `copy:` line is broken by the check's OWN planter (the revision taken off it), and the
check must exit 1 in each.  The check this round REPLACED is run in tree 3 as well, where its revision
can still be resolved out of git, and must exit 1 there -- the defect the round was opened on,
reproduced rather than quoted.

Run:  python3 verify_correction_r3.py
Writes correction_r3_verify.log BESIDE this package (a log path outside the package is a defect this
package has already recorded once).  Exit status follows the verdict.
"""
import io
import importlib.util
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True  # a checker must not write byte-code into the package it reads

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.basename(HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
REPORT = os.path.join(HERE, "reference-check.md")
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
LOG = os.path.join(HERE, "correction_r3_verify.log")
APPENDED = "\n# one appended comment line: the round-3 durability control\n"

out = []


def say(s):
    out.append(s)
    print(s)


def run(args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.stdout + p.stderr, p.returncode


def git(args):
    p = subprocess.run(["git", "-C", REPO] + args, capture_output=True)
    return p.stdout.decode("utf-8", "replace").strip(), p.returncode


def head():
    return git(["rev-parse", "HEAD"])[0]


def archive(rev, dest):
    """A path-limited export of `rev`: only this package, and therefore no `.github/`."""
    p = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", rev, "papers/" + PKG],
                       capture_output=True)
    if p.returncode != 0:
        return None, p.stderr.decode("utf-8", "replace").strip()
    tf = tarfile.open(fileobj=io.BytesIO(p.stdout))
    tf.extractall(dest)
    return os.path.join(dest, "papers", PKG), None


def copy_package(dest, gate_extra=""):
    """This package as it stands, with the journal's gate (optionally edited) put back above it."""
    pkg = os.path.join(dest, "papers", PKG)
    os.makedirs(os.path.dirname(pkg), exist_ok=True)
    shutil.copytree(HERE, pkg, ignore=shutil.ignore_patterns("research", "__pycache__", "*.pyc",
                                                             "correction_r3_verify.log"))
    if gate_extra and os.path.exists(GATE):
        tgt = os.path.join(dest, ".github", "tools", "refgate.py")
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        io.open(tgt, "w", encoding="utf-8").write(io.open(GATE, encoding="utf-8").read() + gate_extra)
    return pkg


def tool():
    """The check and its planter, loaded from the shipped file -- the readers the control must use."""
    spec = importlib.util.spec_from_file_location("_r3_gate_read", os.path.join(HERE, "gate_read_v1.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def two_reads(pkg):
    """(--check exit, its last line, --selftest exit, its last line) in one tree."""
    says, rc = run([sys.executable, "gate_read_v1.py", "--check"], pkg)
    sst, src = run([sys.executable, "gate_read_v1.py", "--selftest"], pkg)
    tail = [l.strip() for l in says.strip().splitlines() if l.strip()][-1:] or [""]
    stail = [l.strip() for l in sst.strip().splitlines() if l.strip()][-1:] or [""]
    return rc, tail[0], src, stail[0]


def check_checkout():
    rc, line, src, sline = two_reads(HERE)
    fails = []
    if rc != 0:
        fails.append("--check exits %d in this checkout: %s" % (rc, line[-160:]))
    if src != 0:
        fails.append("--selftest exits %d in this checkout: %s" % (src, sline[-160:]))
    return fails, "checkout: --check exit %d, battery exit %d -- %r / %r" % (rc, src, line, sline)


def check_export():
    """READ 2, and the control that the read can go red in the same tree."""
    rev = head()
    fails = []
    tmp = tempfile.mkdtemp(prefix="issue47-r3-export-")
    try:
        pkg, err = archive(rev, tmp)
        if pkg is None:
            return ["`git archive %s` failed: %s" % (rev, err)], "export not built"
        if os.path.exists(os.path.join(tmp, ".github")):
            return ["the export unexpectedly carries .github/"], "the control tree is wrong"
        rc, line, src, sline = two_reads(pkg)
        if rc != 0:
            fails.append("--check exits %d in the export of %s: %s" % (rc, rev[:12], line[-160:]))
        if src != 0:
            fails.append("--selftest exits %d in the export of %s: %s" % (src, rev[:12], sline[-160:]))
        # the control: the same tree, the report's primary `copy:` line broken by the tool's own planter
        mod = tool()
        rpt = os.path.join(pkg, "reference-check.md")
        text = io.open(rpt, encoding="utf-8").read()
        planted = mod.plant("primary_revision", text)
        if planted is None or planted == text:
            fails.append("the control could not be derived from the exported report")
        else:
            io.open(rpt, "w", encoding="utf-8").write(planted)
            crc, cline, _, _ = two_reads(pkg)
            if crc == 0:
                fails.append("with the revision taken off the primary `copy:` line the check still "
                             "exits 0 in the export: the read is decoration")
            else:
                return fails, ("export of %s (no .github/): --check exit %d, battery exit %d; control "
                               "caught (exit %d on a `copy:` line with no revision)"
                               % (rev[:12], rc, src, crc))
        return fails, "export of %s: --check exit %d, battery exit %d" % (rev[:12], rc, src)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_durability():
    """READ 3: the journal edits its own gate by one appended comment line -- the read must not move."""
    if not os.path.exists(GATE):
        return [], ("SKIP this tree carries no `.github/`: the durability read names a copy of the "
                    "journal's gate and there is none here")
    before = io.open(GATE, encoding="utf-8").read()
    fails = []
    tmp = tempfile.mkdtemp(prefix="issue47-r3-durable-")
    try:
        pkg = copy_package(tmp, APPENDED)
        tgt = os.path.join(tmp, ".github", "tools", "refgate.py")
        after = io.open(tgt, encoding="utf-8").read()
        if after == before:
            return ["the control tree's gate copy is unchanged: the read proves nothing"], "no edit planted"
        rc, line, src, sline = two_reads(pkg)
        if rc != 0:
            fails.append("--check exits %d in a tree whose gate carries one appended comment line: %s"
                         % (rc, line[-160:]))
        if src != 0:
            fails.append("--selftest exits %d in a tree whose gate carries one appended comment line: %s"
                         % (src, sline[-160:]))
        detail = ("one appended comment line to the gate copy (lines %d -> %d): --check exit %d, "
                  "battery exit %d" % (before.count("\n"), after.count("\n"), rc, src))
        # the control: the same tree, the report's primary `copy:` line broken by the tool's own planter
        mod = tool()
        rpt = os.path.join(pkg, "reference-check.md")
        text = io.open(rpt, encoding="utf-8").read()
        planted = mod.plant("primary_revision", text)
        if planted is None or planted == text:
            fails.append("the control could not be derived from the report in this tree")
        else:
            io.open(rpt, "w", encoding="utf-8").write(planted)
            crc, _, _, _ = two_reads(pkg)
            if crc == 0:
                fails.append("with the revision taken off the primary `copy:` line the check still "
                             "exits 0 in this tree: the read is decoration")
            else:
                detail += "; control caught (exit %d)" % crc
        return fails, detail
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_replaced():
    """The check this round replaced, in the durability tree: it must be RED there. That is the defect."""
    g, rc = git(["rev-parse", "origin/main"])
    if rc != 0 or not g:
        return [], "SKIP `origin/main` is not resolvable here: the replaced check cannot be read"
    text, trc = git(["show", "%s:papers/%s/gate_read_v1.py" % (g, PKG)])
    if trc != 0 or not text:
        return [], "SKIP the replaced check is not in %s" % g[:12]
    if text == io.open(os.path.join(HERE, "gate_read_v1.py"), encoding="utf-8").read():
        return [], "SKIP the file at %s IS this round's check (nothing replaced yet)" % g[:12]
    fails = []
    tmp = tempfile.mkdtemp(prefix="issue47-r3-replaced-")
    try:
        pkg = copy_package(tmp, APPENDED)
        pre = os.path.join(pkg, "gate_read_v1.pre_round.py")
        io.open(pre, "w", encoding="utf-8").write(text)
        says, prc = run([sys.executable, pre, "--check"], pkg)
        line = [l for l in says.strip().splitlines() if l.strip()]
        if prc == 0:
            fails.append("the replaced check exits 0 in the durability tree: the round's premise does "
                         "not reproduce here")
            return fails, "replaced check NOT red in the durability tree"
        return fails, ("the replaced check (as published, %s) exits %d in the durability tree -- %s"
                       % (g[:12], prc, (line[-1][:120] if line else "")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


CHECKS = [
    ("R3-1 this checkout", check_checkout),
    ("R3-2 path-limited export", check_export),
    ("R3-3 durability control", check_durability),
    ("R3-4 the replaced check", check_replaced),
]


def main():
    say("issue #47 correction round 3 -- the report's attributions, read in the trees the round names")
    say("  package: %s" % HERE)
    say("  head read: %s" % head()[:12])
    say("")
    allfail = []
    for name, fn in CHECKS:
        fails, detail = fn()
        say("%-26s %s" % (name, "SKIP" if (not fails and detail.startswith("SKIP")) else
                          ("PASS" if not fails else "FAIL")))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        say("")
        allfail += fails
    say("R3: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
