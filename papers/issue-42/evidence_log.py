#!/usr/bin/env python3
"""The verdict log's format -- owned here, not typed into each checker (issue #42, correction round 3).

A correction checker's log is evidence a reader opens. It owes three things that reader cannot infer
from the verdict alone:

  * the **build** the reading was taken on -- because the package's own tolerance is read against a
    build (round 2), a verdict whose numbers depend on the arithmetic must say which arithmetic;
  * the **tree** it was taken in, named by identity rather than by location: an export that does not
    carry the journal's gate `.github/tools/refgate.py` cannot take the gate's reading, and a reader
    who is handed only the verdict cannot tell which half was read;
  * every reading that could **not** be taken, in the verdict itself -- a `SKIP` has to be visible
    from the last line of the file, not only from a detail line above it.

Two consequences, and they are what this file exists for:

  * **a run does not overwrite the committed copy.** The log destination is an argument and the
    default is to write nothing, so a reader's run of a checker cannot replace the evidence it is
    reading. The checkers' `--check` mode re-derives the log and compares it with the committed one.
  * **the committed copy is re-derivable by a step of the spec**, with the *coordinate* lines excepted:
    `taken on:` and `taken in:` name the machine and the tree, so they are DECLARED -- compared for
    presence and well-formedness, not for equality -- while every other line must be identical. A line
    that in a fresh run says a reading was not taken is reported as such rather than as a
    disagreement, because a reading that cannot be taken here is not a failed check.

Used by `verify_correction_r1.py` and `verify_correction_r2.py`; both write their log through it and
both take the `--check` comparison from `compare()` below.
"""
import io
import json
import os
import re
import subprocess
import sys

# A line whose content names the machine, the tree, or a reading this run could not take is DECLARED:
# it is evidence about the reading, not the reading, so two runs of the same package at different
# coordinates legitimately print different ones -- and a comparison that demanded equality there would
# be reading the machine instead of the package (correction round 3).
DECLARED_PREFIXES = ("taken on:", "taken in:", "observed:", "NOT TAKEN:")
NOT_TAKEN_RE = re.compile(r"\b(SKIP|NOT TAKEN|NOT RUN)\b")
CHECK_ID_RE = re.compile(r"^(R\d+[-\w]*)")


def measured_build():
    """The BUILD this run is: the interpreter version and the version of the one dependency whose
    values enter the package's comparison. Measured, never typed."""
    py = sys.version.split()[0]
    try:
        import numpy
        np_ = numpy.__version__
    except Exception:                                    # any import failure is the fact
        np_ = "ABSENT"
    return {"python": py, "numpy": np_}


def named_build(package_dir, record_name="build.json"):
    """The build the package's committed artefacts were re-derived under, from its own record."""
    path = os.path.join(package_dir, record_name)
    if not os.path.exists(path):
        return None
    try:
        rec = json.load(io.open(path, encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if not rec.get("python"):
        return None
    return {"python": rec.get("python"), "numpy": rec.get("numpy")}


def gate_path(package_dir):
    return os.path.normpath(os.path.join(package_dir, "..", "..", ".github", "tools", "refgate.py"))


def git_info(package_dir, marker="manuscript.md"):
    """The tree's identity, or None when the package is not part of a git work tree.

    A `git archive` export carries no `.git`, but a directory can also sit INSIDE somebody else's
    repository -- and then `git rev-parse` answers with that repository's head, which is a different
    tree entirely. So the answer is taken only when this package's own files are tracked in the
    repository that would be named (`git ls-files --error-unmatch`), and an enclosing repository that
    does not track them is reported as what it is: a plain directory.
    """
    def g(*args):
        try:
            p = subprocess.run(["git"] + list(args), cwd=package_dir, capture_output=True, text=True)
        except OSError:
            return None
        return p.stdout.strip() if p.returncode == 0 else None

    head = g("rev-parse", "HEAD")
    if not head:
        return None
    if g("ls-files", "--error-unmatch", marker) is None:
        return None
    return {"head": head, "branch": g("rev-parse", "--abbrev-ref", "HEAD") or "?",
            "dirty": bool(g("status", "--porcelain"))}


def header(package_dir, record_name="build.json", declared_head=None):
    """The two coordinate lines. Named by identity, never by an absolute path from the author's tree:
    a reader needs to know WHICH tree and WHICH build, and a machine-specific path is neither. A plain
    directory (a `git archive` export, which is what a reader is handed) carries no `.git`, so the
    revision is DECLARED by the run that takes the reading (`--head`), never inferred."""
    here = measured_build()
    named = named_build(package_dir, record_name)
    if named is None:
        on = ("taken on: build Python %s / numpy %s   |   no %s in this package: no named build to"
              " compare with" % (here["python"], here["numpy"], record_name))
    else:
        same = here["python"] == named["python"] and here["numpy"] == named["numpy"]
        on = ("taken on: build Python %s / numpy %s   |   named build Python %s / numpy %s (%s)"
              % (here["python"], here["numpy"], named["python"], named["numpy"],
                 "the named build" if same else "DIFFERENT"))
    gate = "present" if os.path.exists(gate_path(package_dir)) else "ABSENT"
    gi = git_info(package_dir)
    if gi:
        inn = ("taken in: a git work tree at head %s (branch %s, %s); journal gate"
               " (.github/tools/refgate.py): %s"
               % (gi["head"][:12], gi["branch"], "dirty" if gi["dirty"] else "clean", gate))
    elif declared_head:
        inn = ("taken in: a plain directory at head %s (declared by the run; no .git to derive it"
               " from); journal gate (.github/tools/refgate.py): %s" % (declared_head[:12], gate))
    else:
        inn = ("taken in: not a git work tree (a plain directory; no head declared); journal gate"
               " (.github/tools/refgate.py): %s" % gate)
    return [on, inn]


def is_declared(line):
    return line.strip().startswith(DECLARED_PREFIXES)


def same_reading(x, y):
    """Are these two lines the SAME reading, so that one side reporting it as not taken is a fact about
    the run rather than a disagreement? Two lines qualify when they name the same check, or when they
    open with the same text -- the marker is appended to a reading's own line, so its detail can differ
    from its counterpart's while the reading named is the same one."""
    if check_id(x) and check_id(x) == check_id(y):
        return True
    head = 40
    return len(x[:head].strip()) >= 20 and x[:head].rstrip() == y[:head].rstrip()


def check_id(line):
    """The check a line reports on (`R2-6b`), so a line whose DETAIL moved can be paired with the same
    check's line on the other side instead of with whatever happened to be at that line number."""
    m = CHECK_ID_RE.match(line.strip())
    return m.group(1) if m else None


def compare(committed_text, fresh_text):
    """(ok, declared, not_taken, mismatches) for a committed log against a fresh render of it.

    The comparison pairs lines by content, not by line number -- a reading that could not be taken adds
    a line, and a line number is a coordinate, so an index-paired read would report one skip as a
    cascade of disagreements. Three kinds of difference are not disagreements:

      * a DECLARED line (`taken on:`, `taken in:`, `observed:`, `NOT TAKEN:`) -- present on both sides,
        its content is a fact about the run's coordinate rather than about the package;
      * a check line whose detail reports a reading NOT TAKEN on one side and a reading on the other --
        paired by the check it names, never by position;
      * an absent declared line on the other side.

    Everything else must be identical, and the disagreements are returned with their lines.
    """
    a, b = committed_text.split("\n"), fresh_text.split("\n")
    i = j = declared = nottaken = 0
    mism = []
    while i < len(a) or j < len(b):
        x = a[i] if i < len(a) else None
        y = b[j] if j < len(b) else None
        if x is not None and y is not None and x == y:
            i += 1
            j += 1
            continue
        if x is not None and is_declared(x):
            declared += 1
            i += 1
            continue
        if y is not None and is_declared(y):
            declared += 1
            j += 1
            continue
        if x is not None and y is not None and (NOT_TAKEN_RE.search(x) or NOT_TAKEN_RE.search(y)) \
                and same_reading(x, y):
            nottaken += 1
            i += 1
            j += 1
            continue
        mism.append((i + 1, x if x is not None else "<the committed log has no such line>",
                     y if y is not None else "<this run produced no such line>"))
        i += 1
        j += 1
    return (not mism), declared, nottaken, mism


def render(lines):
    return "\n".join(lines) + "\n"


def write(path, lines):
    io.open(path, "w", encoding="utf-8", newline="\n").write(render(lines))
    return path
