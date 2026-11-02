#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seal_artefacts.py -- the digests of the files this package derives, and the check against them.

Why this exists. `reproduce.sh` used to decide "did the run reproduce the committed artefacts?" with
`git diff --quiet` and `git ls-files --error-unmatch`. Both need a `.git` directory, and a reader who
follows the README does not have one: `git archive` -- the export this journal's own audit uses, and
what a tarball download gives -- carries no `.git`, so those three steps reported NOT RUN for every
reader while reporting `[ok]` for the author. A check that only the author can run is not a check.

The repair is a committed manifest of SHA-256 digests. It travels inside the package, it does not
need git, and it is a digest rather than a comparison against the working tree, so it also catches the
case `git diff` cannot: an artefact that was regenerated identically to a *modified* index.

Two modes, deliberately asymmetric:

  --seal     rewrite the manifest from the files on disk. A maintenance act: it says "these bytes are
             now the package". Nothing runs it except a person who has decided that.
  --verify   recompute and compare. This is what `reproduce.sh` runs, and it fails by naming the file.

The asymmetry is the point. If verification could rewrite the manifest, every defect would be
self-healing; a seal is a claim someone made once, and verification is the read that holds it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "artefacts.sha256")

# What the run derives. `manuscript.src.md`, `placements.py`, the corpus and the instruments are
# authored, not derived: they are the inputs, and sealing an input would only restate the file.
DERIVED = ("nines_findings.json", "manuscript.md", "reference-check.md")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def seal():
    rows = {}
    for name in DERIVED:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            print("cannot seal %s: it does not exist" % name)
            return 1
        rows[name] = digest(p)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("# SHA-256 of the files this package derives. Sealed by seal_artefacts.py --seal.\n")
        fh.write("# Verification is reproduce.sh step 4: it recomputes these and names any that differ.\n")
        for name in DERIVED:
            fh.write("%s  %s\n" % (rows[name], name))
    print("sealed %d artefact(s) -> %s" % (len(rows), os.path.basename(MANIFEST)))
    return 0


def read_manifest():
    if not os.path.exists(MANIFEST):
        return None
    out = {}
    with open(MANIFEST, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) == 2:
                out[parts[1]] = parts[0]
    return out


def verify():
    want = read_manifest()
    if want is None:
        print("NOT RUN: no %s in this package, so nothing is sealed to check against"
              % os.path.basename(MANIFEST))
        return 3
    missing = [n for n in DERIVED if n not in want]
    if missing:
        print("NOT RUN: the manifest does not cover %s" % ", ".join(missing))
        return 3
    bad, absent = [], []
    for name in DERIVED:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            absent.append(name)
            continue
        got = digest(p)
        if got != want[name]:
            bad.append((name, want[name][:12], got[:12]))
    for name in absent:
        print("  [FAIL] %s is sealed but absent -- the run did not regenerate it" % name)
    for (name, a, b) in bad:
        print("  [FAIL] %s differs from the sealed digest (sealed %s..., now %s...)" % (name, a, b))
    if bad or absent:
        print("\nSEAL: %d FAILED -- the run does not reproduce the sealed artefact(s)" % (len(bad) + len(absent)))
        return 1
    print("  [ok]   %d artefact(s) match their sealed digests" % len(DERIVED))
    print("\nSEAL: ALL GREEN (%d artefact(s))" % len(DERIVED))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Seal or verify the digests of this package's artefacts.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--seal", action="store_true", help="rewrite the manifest from the files on disk")
    g.add_argument("--verify", action="store_true", help="recompute and compare (what reproduce.sh runs)")
    args = ap.parse_args(argv)
    return seal() if args.seal else verify()


if __name__ == "__main__":
    sys.exit(main())
