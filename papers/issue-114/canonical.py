#!/usr/bin/env python3
"""Check (or rewrite) the committed artefact `canonical_results.json`.

WHY A CHECK RATHER THAN A REGENERATION
--------------------------------------
`decide.py` already writes this file, so "reproduce" could just be "run it again".  That
proves the run is DETERMINISTIC (two runs in one process agree) but not that the file
committed here is what the code produces -- the two claims are different, and only the
second one is what a reader of the paper relies on.  So the default action is:

    regenerate into a temporary file, compare BYTE FOR BYTE with the committed one, and
    fail if they differ

with `--write` as the deliberate act that replaces the committed artefact.  The comparison
counts what it compared and prints the count, because "regenerated vs committed" is a claim
about a set of files and an unstated count is not a check.

Usage:
    python3 canonical.py            # check (exit 0 iff committed == regenerated)
    python3 canonical.py --write    # overwrite canonical_results.json
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "canonical_results.json")
REQUIRED_KEYS = ("protocol", "population", "cells", "frontier", "alignment", "mix",
                 "mechanism_by_kind", "kind_ranking", "menu_sizes", "findings")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def regenerate(dest: str) -> None:
    r = subprocess.run([sys.executable, os.path.join(HERE, "decide.py"), "--json", dest],
                       cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stdout.write(r.stdout[-2000:])
        sys.stderr.write(r.stderr[-2000:])
        raise SystemExit(f"decide.py exited {r.returncode}")


def main(argv) -> int:
    write = "--write" in argv
    with tempfile.TemporaryDirectory() as td:
        fresh = os.path.join(td, "canonical_results.json")
        regenerate(fresh)
        new = open(fresh, "rb").read()

        # the artefact must CARRY the keys the paper reads: a byte-identical file that has
        # lost a section is still a failure
        D = json.loads(new)
        missing = [k for k in REQUIRED_KEYS if k not in D]
        if missing:
            print(f"CANONICAL: FAIL -- regenerated artefact is missing {missing}")
            return 1

        if write:
            with open(TARGET, "wb") as fh:
                fh.write(new)
            print(f"CANONICAL: written   {TARGET}  {len(new)} B  {sha(new)[:16]}…")
            return 0

        if not os.path.exists(TARGET):
            print(f"CANONICAL: FAIL -- {TARGET} does not exist (run with --write)")
            return 1
        old = open(TARGET, "rb").read()

    same = old == new
    print(f"CANONICAL: {'byte-identical' if same else 'DIFFERS'}   "
          f"committed {len(old)} B {sha(old)[:16]}…  regenerated {len(new)} B {sha(new)[:16]}…")
    if not same:
        return 1
    n_cells = len(D["cells"])
    n_reached = sum(1 for c in D["cells"].values() if c["reached"])
    print(f"CANONICAL: {D['population']['references']} references · "
          f"{D['population']['changing_mutations']} changing / "
          f"{D['population']['preserving_mutations']} preserving mutations · "
          f"{n_cells} cells ({n_reached} reached) · "
          f"{D['protocol']['n_draws']} draws · "
          f"p1 span {D['findings']['p1_worst_alignment_span']:.3f}x · "
          f"p3 breakage@r0 {D['findings']['p3_breakage_at_r0_max']:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
