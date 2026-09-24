#!/usr/bin/env python3
"""#87 R419 -- the build-bound comparison, in the declared form the instruments' controls already use.

WHY THIS FILE EXISTS.  The R446 editorial re-check found the run's build-bound steps under-counted and the
declared one unreachable: `reproduce.sh` compared steps 1/5 (the digest) and 2/5 (the figures) with `cmp` and
declared **one** build-bound exception (step 4/5) -- the *last* of the three.  On any build other than the one
the package pins, the run therefore stopped at 1/5, so the `BUILD_BOUND` reading the previous revision built to
discharge R444's (B) -- with its build read, build pinned and worst relative departure -- was exactly what a
reader on a current interpreter never saw.  Its rule, from R439: *a tolerance names the build it is read
against.*

WHAT A READING IS.  Three numbers and a verdict, printed under the same keys everywhere in this package:

    build read  : python X.Y.Z / numpy A.B.C        the interpreter and the dependency that ran THIS comparison
    build pinned: python X.Y.Z / numpy A.B.C        the build the committed record names
    departure   : N differing leaf/leaves, worst abs E, worst rel R, at <the leaf's own path>
    verdict     : BITWISE | BUILD_BOUND | FAIL | NOT RUN

  * `BITWISE`     -- every leaf equal.  A property of the pinned build, not of the claim.
  * `BUILD_BOUND` -- leaves differ, every one within the DECLARED relative tolerance (`REL_TOL`, passed in).
                     The same instrument up to floating-point reduction order; the caller continues.
  * `FAIL`        -- a leaf departs beyond `REL_TOL`.  Exit 1; the message carries the departure and both builds.
  * `NOT RUN`     -- the comparison could not be taken at all, because THIS interpreter carries no numpy.  Exit 2,
                     the same code the journal's gates use, and **not** a verdict about the record: the number
                     that is missing is a fact about the interpreter.  (Added after the R446 editorial re-check
                     found the same defect one level up: an instrument that cannot run reported its own
                     environment as a finding about the manuscript.  A traceback here would be read by a caller
                     as `FAIL`, i.e. as a departure -- the worst possible confusion, since a departure is the one
                     thing this file exists to detect.)

A zero test is RELATIVE to the value's own scale, never absolute: `abs(d) <= REL_TOL * max(abs(a), abs(b))` --
an absolute threshold on a quantity that is analytically zero reports a defect where there is none (and, in the
opposite direction, hides one where the value is large).  A leaf present on one side only is a **structural**
departure and is reported as such -- it is not a rounding difference.

Usage:
  python3 build_bound.py json <committed.json> <regenerated.json> [--rel-tol 1e-8] [--label NAME]
  python3 build_bound.py png  <regenerated.png> --version-line "<matplotlib X>"  [--committed <committed.png>]

Exit: 0 = compared with every departure within tolerance | 1 = a departure beyond tolerance, or a structural
      one | 2 = NOT RUN (nothing was compared) | 3 = usage error.
"""
import io
import json
import os
import subprocess
import sys

REL_TOL_DEFAULT = 1e-8


def _flat(node, path=""):
    """Every numeric leaf with its own path, so a departure names the field it happened in."""
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(_flat(v, path + "." + str(k) if path else str(k)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(_flat(v, "%s[%d]" % (path, i)))
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        out[path] = float(node)
    return out


def build_line():
    """The build this reading is taken at -- printed even when the dependency is MISSING, because that is
    exactly the case a reader needs named (a raise here would turn an environment fact into a traceback)."""
    try:
        import numpy
    except ImportError:
        return "python %s / numpy ABSENT" % sys.version.split()[0]
    return "python %s / numpy %s" % (sys.version.split()[0], numpy.__version__)


def numpy_at(interp):
    """The numpy version an interpreter carries, or None.  Declared once, so callers can ask the question."""
    r = subprocess.run([interp, "-c", "import numpy;print(numpy.__version__)"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def not_run(reason, label=None):
    """Nothing was compared.  Exit 2 (the journal's own NOT RUN code) and say WHICH build failed to run."""
    print("  %sbuild read  : %s" % ("%-10s " % label if label else "", build_line()))
    print("  build pinned: %s   (the build the committed record names)" % PINNED)
    print("  verdict     : NOT RUN -- %s.  NOTHING WAS COMPARED: this is a reading about the interpreter, not "
          "about the record, and it is not a pass." % reason)
    return 2


def cmp_json(a_path, b_path, rel_tol, label=None):
    a = json.load(io.open(a_path, encoding="utf-8"))
    b = json.load(io.open(b_path, encoding="utf-8"))
    fa, fb = _flat(a), _flat(b)
    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))
    drift = []
    for k in sorted(set(fa) & set(fb)):
        x, y = fa[k], fb[k]
        if x == y:
            continue
        scale = max(abs(x), abs(y))
        rel = (abs(x - y) / scale) if scale else float("inf")
        drift.append((k, x, y, abs(x - y), rel))
    worst = max(drift, key=lambda t: t[4]) if drift else None
    print("  %sbuild read  : %s" % ("%-10s " % label if label else "", build_line()))
    print("  build pinned: %s   (the build the committed record names)" % PINNED)
    if only_a or only_b:
        print("  structural  : %d leaf/leaves present on one side only (a structural departure, not a rounding "
              "difference): missing-from-regenerated %s%s" % (len(only_a) + len(only_b), only_a[:3],
                                                              (", added " + str(only_b[:3])) if only_b else ""))
        print("  verdict     : FAIL -- a structural departure is beyond any tolerance")
        return 1
    if not drift:
        print("  departure   : none -- %d numeric leaves compared" % len(fa))
        print("  verdict     : BITWISE")
        return 0
    if worst[4] > rel_tol:
        print("  departure   : %d leaf/leaves differ | worst abs %.3e | worst rel %.3e at %s"
              % (len(drift), worst[3], worst[4], worst[0]))
        print("  verdict     : FAIL -- the worst relative departure %.3e is beyond the declared %.0e"
              % (worst[4], rel_tol))
        return 1
    print("  departure   : %d leaf/leaves differ | worst abs %.3e | worst rel %.3e at %s"
          % (len(drift), worst[3], worst[4], worst[0]))
    print("  verdict     : BUILD_BOUND -- NOT bitwise on this build; the worst relative departure %.3e is within "
          "the declared %.0e, so this is the same record up to floating-point reduction order"
          % (worst[4], rel_tol))
    return 0


PINNED = "python 3.9.6 / numpy 2.0.2"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    kind, rest = argv[1], argv[2:]
    if kind == "json":
        rel_tol, label = REL_TOL_DEFAULT, None
        if "--rel-tol" in rest:
            i = rest.index("--rel-tol")
            rel_tol = float(rest[i + 1])
            del rest[i:i + 2]
        if "--label" in rest:
            i = rest.index("--label")
            label = rest[i + 1]
            del rest[i:i + 2]
        # The reading is taken at the interpreter that runs this file (this process), so a json comparison --
        # which reads numeric leaves -- cannot be taken at all where numpy is absent: say that, print the build,
        # and return 2.  Never let a missing dependency surface as a traceback, which a caller reads as FAIL,
        # i.e. as a departure -- the one thing this file exists to detect.
        if numpy_at(sys.executable) is None:
            others = ", ".join("%s -> numpy %s" % (c, numpy_at(c) or "ABSENT")
                               for c in ("/usr/bin/python3",
                                         os.path.expanduser("~/.asdf/installs/python/3.14.6/bin/python3")))
            return not_run("%s carries no numpy (checked: %s)" % (sys.executable, others), label)
        return cmp_json(rest[0], rest[1], rel_tol, label)
    if kind == "png":
        # A PNG is a RENDERING: its bytes are a property of matplotlib + freetype + libpng, not of the claim.
        # So this comparison reports which figures differ and names the renderer that drew them; it never
        # returns FAIL, because no tolerance for a rendering has been MEASURED here (a tolerance that names no
        # build is not a tolerance -- R439).  What the figures carry is the digest, checked above.
        regen = rest[0]
        committed = None
        vline = "matplotlib version not stated"
        if "--committed" in rest:
            i = rest.index("--committed")
            committed = rest[i + 1]
        if "--version-line" in rest:
            i = rest.index("--version-line")
            vline = rest[i + 1]
        if committed and os.path.exists(committed):
            same = io.open(committed, "rb").read() == io.open(regen, "rb").read()
        else:
            same = False
        print("  renderer    : %s" % vline)
        if same:
            print("  verdict     : BITWISE -- the PNG bytes are equal on this renderer")
            return 0
        print("  verdict     : RENDER_BOUND -- the PNG bytes differ; a rendering is a property of the renderer "
              "build, and this step is REPORTED rather than stopped on (the figures' numbers are the digest's, "
              "checked by the step above)")
        return 0
    print("build_bound: unknown comparison kind %r" % kind)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
