#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_declared_env.py -- the README's module list, read against the modules the code imports.

Why this exists. `README.md` tells a reader what they need in one sentence: "Stdlib-only Python 3
(developed under CPython 3.9.6): `argparse json math ...`". That sentence is a **claim about the
build**, and this package's own history is what makes it worth gating: `gate_citations.py` imports
`html`, and the list did not name it. Nothing failed -- the code ran, the artefacts reproduced, and
every journal gate passed -- because the instrument this journal owns for exactly this class,
`.github/tools/envgate.py`, reads the declaration **one way only**: it takes the set the code
imports, classifies each name, and asks whether every **third-party** name appears in the
declaration. A standard-library name is classified and then never asserted, so an omission inside
the stdlib half of the list is invisible to it by construction. That is a property of the gate's
question, not a defect of it -- and it means the second half of the claim has no instrument at all
unless it is here.

So this reads both halves, in the direction the gate does not:

  * **every name the code imports is declared** -- an undeclared name is the #142 defect: a build
    spec narrower than the code, which a reader discovers with `ModuleNotFoundError` (here the
    module would be found, since it is stdlib, and the spec would simply be wrong about what the
    program is);
  * **every declared name is imported** -- a declaration naming a module nothing imports is a wish,
    and it is the same drift from the other side: the sentence stops describing this program and
    starts describing one it might have been.

Both failures name the module. A count that is printed and not named is a number a reader cannot
act on.

Exit: 0 the two sets are one set · 1 they differ (the module is named) · 3 nothing to read.
`--selftest` plants both directions and requires each to be refused by name.
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")

# The sentence that makes the claim. It is read as a region rather than as a phrase: the list is
# whatever backticked identifiers sit between the marker and the full stop that ends the sentence.
MARKER = "Stdlib-only"
END = "There is nothing to install"
# The list is written as ONE backticked span holding several space-separated names -- not one
# backtick per name. The first version of this parser required a single identifier between backticks
# and therefore read **zero** declared names off a sentence that plainly declares eleven, which is
# the same shape as the defect the file exists for: a reader narrower than the text it reads. Fixed
# by taking the spans first and splitting them, which is the form the sentence actually uses.
SPAN = re.compile(r"`([^`]+)`")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

# Modules the code imports that are not dependencies: a sibling module of this package, and the
# `__future__` compiler directive, which imports nothing at run time.
NOT_A_DEPENDENCY = {"__future__"}


def declared(path=README):
    """The module names the README declares, in the order it declares them."""
    with io.open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.find(MARKER)
    if start < 0:
        return None
    stop = text.find(END, start)
    region = text[start:stop if stop > 0 else start + 600]
    names = []
    for span in SPAN.findall(region):
        for token in re.split(r"[\s,]+", span.strip()):
            if token and IDENT.match(token):
                names.append(token)
    return names


def sibling_modules(root=HERE):
    """The package's own modules, which are imported by name and are not dependencies."""
    return {os.path.splitext(f)[0] for f in os.listdir(root) if f.endswith(".py")}


def imported(root=HERE):
    """Every top-level module the package's own .py files import."""
    used = set()
    for name in sorted(os.listdir(root)):
        if not name.endswith(".py"):
            continue
        with io.open(os.path.join(root, name), encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    used.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    used.add(node.module.split(".")[0])
    return used - NOT_A_DEPENDENCY - sibling_modules(root)


def compare(declared_names, imported_names):
    """(missing, extra) -- what the code has and the sentence lacks, and the reverse."""
    declared_set = set(declared_names or [])
    missing = sorted(imported_names - declared_set)
    extra = sorted(declared_set - imported_names)
    return missing, extra


def selftest():
    """Both directions, planted. A check that has only been seen to pass is not a check."""
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    used = {"argparse", "html", "json"}
    missing, extra = compare(["argparse", "json"], used)
    expect("a module the code imports and the sentence omits is refused, by name",
           missing == ["html"] and not extra, "missing=%s extra=%s" % (missing, extra))

    missing, extra = compare(["argparse", "html", "json", "typing"], used)
    expect("a declared module nothing imports is refused, by name",
           extra == ["typing"] and not missing, "missing=%s extra=%s" % (missing, extra))

    missing, extra = compare(["argparse", "html", "json"], used)
    expect("one set read as one set passes on an exact match",
           not missing and not extra, "missing=%s extra=%s" % (missing, extra))

    # The real defect this file was written for, replayed against the real sentence: the committed
    # declaration without `html` must be refused, and with it must pass. This is the leg that makes
    # the repair a check rather than an edit -- a version of this file that quietly matched the
    # README it was born beside would report the same verdict before and after the fix.
    real = imported()
    if real:
        without = sorted(real - {"html"})
        missing, extra = compare(without, real)
        expect("the committed import set without `html` reproduces the defect this file exists for",
               missing == ["html"], "missing=%s" % (missing,))
        missing, extra = compare(sorted(real), real)
        expect("and the committed import set read against itself is clean",
               not missing and not extra, "missing=%s extra=%s" % (missing, extra))

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    names = declared()
    if names is None:
        print("NOT RUN: README.md carries no %r sentence, so nothing declares an environment"
              % MARKER)
        return 3
    used = imported()
    if not used:
        print("NOT RUN: no package .py file imported anything, so there is no set to read")
        return 3

    missing, extra = compare(names, used)
    print("declared: %d name(s) in README.md" % len(names))
    print("imported: %d name(s) across %d package file(s)"
          % (len(used), len([f for f in os.listdir(HERE) if f.endswith(".py")])))
    if missing:
        print("UNDECLARED: %s -- the code imports %s and the README does not name it"
              % (", ".join(missing), "this" if len(missing) == 1 else "these"))
    if extra:
        print("DECLARED BUT UNUSED: %s -- the README names %s and no file imports it"
              % (", ".join(extra), "it" if len(extra) == 1 else "them"))
    if missing or extra:
        print("VERDICT: the declaration and the code are not one set "
              "(%d missing, %d unused)" % (len(missing), len(extra)))
        return 1
    print("VERDICT: the declared set and the imported set are one set (%d names)" % len(used))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
