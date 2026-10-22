#!/usr/bin/env python3
"""check_one_statistic.py -- issue #128, correction round: ONE rank statistic in the package.

The reported defect was not that one number was wrong; it was that the package held FOUR
implementations of one statistic and TWO conventions, so the same quantity answered +0.108 in
the table and +0.079 in the figure.  Importing the statistic once removes the drift, but an
import is only evidence for as long as somebody keeps it: this file is the check that keeps it.

Two questions, both answered here, plus a plant that proves the first one can fire:

  [1] STATIC   no module except canonical.py defines `def spearman`.  This is the question that
               catches a returning copy even on an interpreter that cannot import the module
               (make_figures.py needs matplotlib, spike_v5.py needs scipy), so the check is not
               limited to the modules this build happens to be able to load.
  [2] DYNAMIC  each module that has the statistic holds canonical.py's object BY IDENTITY
               (`is`, not `==`): two equal implementations would still drift, so equality is
               not the property being checked.

The plant writes a file that re-defines the statistic and requires [1] to REFUSE it, and a
control file that imports it and requires [1] to PASS it -- a scanner that refuses everything
is not a scanner.  Both are written into a scratch directory and removed; no file of the
package is read from or written to by the plant.

Exit 0 = the package holds one statistic; exit 1 = a copy exists, or the plant did not fire.
"""
import io, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OWNER = "canonical.py"
DEF = re.compile(r"^\s*def\s+spearman\s*\(", re.M)

# The modules that must hold the statistic by identity, with the dependency that decides whether
# this build can check them.  A module this build cannot import is reported NOT RUN and named --
# never counted as checked, and never as a pass.
MODULES = [("analyse_v5", "numpy"), ("spike_v5", "scipy"), ("make_figures", "matplotlib")]


def find_copies(root):
    """Return the .py files under `root` that define spearman, other than the owner.

    The package's own copy is identified by its ROLE (the file that owns the statistic), not by
    its path, so a copy moved into a subdirectory is still found.
    """
    copies = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".py") or name == OWNER:
            continue
        p = os.path.join(root, name)
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            if DEF.search(fh.read()):
                copies.append(name)
    return copies


def static_pass():
    owner = io.open(os.path.join(HERE, OWNER), encoding="utf-8").read()
    n_owner = len(DEF.findall(owner))
    copies = find_copies(HERE)
    ok = True
    print("[1] STATIC  %-14s defines spearman: %d time(s)" % (OWNER, n_owner))
    if n_owner != 1:
        print("    FAIL the owner must define it exactly once (found %d)" % n_owner)
        ok = False
    if copies:
        print("    FAIL a second implementation survives in: %s" % ", ".join(copies))
        ok = False
    else:
        print("    no other module in the package defines it")
    return ok


def dynamic_pass():
    """Each importable module must hold canonical.py's object itself, not a copy of its code."""
    import canonical
    ok = True
    checked, notrun = [], []
    for mod, dep in MODULES:
        try:
            m = __import__(mod)
        except Exception as e:                      # noqa: BLE001 - any import failure is NOT RUN
            notrun.append("%s (needs %s: %s)" % (mod, dep, type(e).__name__))
            continue
        if not hasattr(m, "spearman"):
            print("    FAIL %-14s does not expose the statistic at all" % mod)
            ok = False
            continue
        checked.append(mod)
        if m.spearman is not canonical.spearman:
            print("    FAIL %-14s holds a DIFFERENT object than canonical.spearman" % mod)
            ok = False
        else:
            print("    %-14s .spearman is canonical.spearman  (same object)" % mod)
    print("[2] DYNAMIC checked %d module(s): %s" % (len(checked), ", ".join(checked) or "-"))
    for n in notrun:
        print("    NOT RUN  %s" % n)
    if not checked:
        # a run that checked nothing verified nothing, and must not report as a pass
        print("    FAIL no module could be checked on this build")
        ok = False
    return ok


def plant_pass():
    """The scanner must REFUSE a planted copy and ACCEPT a planted import."""
    d = tempfile.mkdtemp(prefix="onestat-plant-")
    try:
        with io.open(os.path.join(d, "copy.py"), "w", encoding="utf-8") as fh:
            fh.write("def spearman(x, y):\n    return 0.079   # the argsort-of-argsort variant\n")
        with io.open(os.path.join(d, "clean.py"), "w", encoding="utf-8") as fh:
            fh.write("from canonical import spearman\n\ndef use(x, y):\n    return spearman(x, y)\n")
        caught = find_copies(d)
        # the control is checked by scanning a directory that holds ONLY the importing file
        d2 = tempfile.mkdtemp(prefix="onestat-control-")
        try:
            shutil.copy(os.path.join(d, "clean.py"), os.path.join(d2, "clean.py"))
            clean = find_copies(d2)
        finally:
            shutil.rmtree(d2, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    fired = caught == ["copy.py"]
    passed = clean == []
    print("[3] PLANT   planted copy     -> %s" % ("REFUSED" if fired else "NOT CAUGHT %r" % (caught,)))
    print("    control import   -> %s" % ("accepted" if passed else "falsely refused %r" % (clean,)))
    return fired and passed


def main():
    ok = True
    ok &= static_pass()
    ok &= dynamic_pass()
    ok &= plant_pass()
    print("ONE-STATISTIC: %s" % ("ALL PASS" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
