#!/usr/bin/env python3
"""Verify issue #47's correction ROUND 3 -- the durability of the report's attributions.

Round 3 has one required change, stated by the round as an OUTCOME rather than as a re-take: the report
must not be *required* to name the copy of the journal's reference gate **that the reader's tree
carries**.  That copy is the journal's own file and it moves as ordinary journal work, so a requirement
that is green only at the head it was generated at is a requirement the package cannot hold.  The three
reads the round names are taken here, each in the tree it is about:

  * READ 1 -- this checkout: `gate_read_v1.py --check` exits 0 and `--selftest` exits 0;
  * READ 2 -- a PATH-LIMITED TREE of this package, carrying no `.github/` above it (the shape the
    reader's own `git archive HEAD papers/issue-47` produces): both exit 0;
  * READ 3 -- a copy of this package whose `.github/tools/refgate.py` differs by **one appended comment
    line**: both exit 0.  This is the read the round exists for.

Each read is two-sided, because a green read that cannot go red reads nothing: in trees 2 and 3 the
report's primary `copy:` line is broken by the check's OWN planter (the revision taken off it), and the
check must exit 1 in each.

WHY THERE IS NO `git` READ HERE.  The package reads no git object, and its own coordinate census forbids
it (C1, "the census proves it rather than asserting it").  A verifier is part of the package, so it is
no exception: the tree READ 2 is taken in is built by COPYING this package into a directory that carries
no `.github/`, which is the same tree for every file the check reads -- and the log names that tree by
the digests of the two files the read depends on, so it is named by content rather than by a revision
string the read never used.

Run:  python3 verify_correction_r3.py
Writes correction_r3_verify.log BESIDE this package (a log path outside the package is a defect this
package has already recorded once).  Exit status follows the verdict.
"""
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # a checker must not write byte-code into the package it reads

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.basename(HERE)
REPORT = os.path.join(HERE, "reference-check.md")
CHECKER = os.path.join(HERE, "gate_read_v1.py")
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


def sha12(path):
    """A content coordinate: the digest of a file the read depends on, never a typed revision."""
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()[:12]


def copy_package(dest, gate_extra=""):
    """This package's files inside `dest`, with the journal's gate (optionally edited) put back above
    them -- or, with no gate copy, the path-limited shape the reader's own export carries."""
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
    """The check and its planter, loaded from the shipped file -- the readers the controls must use."""
    spec = importlib.util.spec_from_file_location("_r3_gate_read", CHECKER)
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


def control(pkg, mod, why):
    """Break the report's primary `copy:` line with the check's own planter; the check must go red."""
    rpt = os.path.join(pkg, "reference-check.md")
    text = io.open(rpt, encoding="utf-8").read()
    planted = mod.plant("primary_revision", text)
    if planted is None or planted == text:
        return None, "the control could not be derived from the report in this tree"
    io.open(rpt, "w", encoding="utf-8").write(planted)
    rc, line, _, _ = two_reads(pkg)
    if rc == 0:
        return False, ("with the revision taken off the primary `copy:` line the check still exits 0 "
                       "in %s: the read is decoration" % why)
    return True, "control caught (exit %d on a `copy:` line with no revision)" % rc


def check_checkout():
    rc, line, src, sline = two_reads(HERE)
    fails = []
    if rc != 0:
        fails.append("--check exits %d in this checkout: %s" % (rc, line[-160:]))
    if src != 0:
        fails.append("--selftest exits %d in this checkout: %s" % (src, sline[-160:]))
    return fails, "checkout: --check exit %d, battery exit %d -- %r / %r" % (rc, src, line, sline)


def check_export():
    """READ 2, in the tree the reader's own path-limited export produces, and its control."""
    fails = []
    tmp = tempfile.mkdtemp(prefix="issue47-r3-export-")
    try:
        pkg = copy_package(tmp)
        if os.path.exists(os.path.join(tmp, ".github")):
            return ["the temporary tree unexpectedly carries .github/"], "the control tree is wrong"
        rc, line, src, sline = two_reads(pkg)
        if rc != 0:
            fails.append("--check exits %d in a tree with no .github/: %s" % (rc, line[-160:]))
        if src != 0:
            fails.append("--selftest exits %d in a tree with no .github/: %s" % (src, sline[-160:]))
        ok, cdetail = control(pkg, tool(), "the no-.github/ tree")
        if ok is False:
            fails.append(cdetail)
        return fails, ("no `.github/` above the package (the shape `git archive <head> papers/%s` "
                       "produces; read here as gate_read_v1.py %s / reference-check.md %s): --check "
                       "exit %d, battery exit %d; %s"
                       % (PKG, sha12(CHECKER), sha12(REPORT), rc, src, cdetail))
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
        ok, cdetail = control(pkg, tool(), "the durability tree")
        if ok is False:
            fails.append(cdetail)
        return fails, ("one appended comment line to the gate copy (%d -> %d lines, sha256 %s -> %s): "
                       "--check exit %d, battery exit %d; %s"
                       % (before.count("\n"), after.count("\n"),
                          sha12(GATE),
                          hashlib.sha256(after.encode("utf-8")).hexdigest()[:12], rc, src, cdetail))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


CHECKS = [
    ("R3-1 this checkout", check_checkout),
    ("R3-2 path-limited tree", check_export),
    ("R3-3 durability control", check_durability),
]


def main():
    say("issue #47 correction round 3 -- the report's attributions, read in the trees the round names")
    say("  package: %s" % HERE)
    say("  content read: gate_read_v1.py %s, reference-check.md %s"
        % (sha12(CHECKER), sha12(REPORT)))
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
