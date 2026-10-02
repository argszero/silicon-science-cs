#!/usr/bin/env python3
"""Plant audit for the specification layer (issue #114).

Copies these modules to a scratch tree, corrupts ONE thing, runs
smoke_frontier.py there, and requires it to exit nonzero.  Six plants, each aimed
at a specific control; a plant that goes undetected means that control is decoration.

  S1  satisfies() always True            -> F4 must fire (detection would collapse)
  S2  exposure() returns 0.0 always      -> F7 must fire (axis detached from the object)
  S3  specificity() returns a constant   -> F1 must fire
  S4  the constructor ignores r_target   -> F1b must fire (a reachable cell goes unreached)
  S5  the reachability quantum is huge   -> F1c must fire (an unreachable cell is passed off)
  S6  representational clauses never checked -> F5-struct must fire

Run: python3 plant_audit_specs.py      (exit 0 == every plant caught)
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

RESEARCH = pathlib.Path(__file__).resolve().parent
SCRATCH = RESEARCH / "_plant_scratch_specs"

PLANTS = [
    ("S1 satisfies() always True ", "specs.py",
     "def satisfies(spec, prog) -> bool:\n    \"\"\"Does `prog` meet every clause of `spec`?\"\"\"\n",
     "def satisfies(spec, prog) -> bool:\n    \"\"\"PLANT\"\"\"\n    return True\n"),
    ("S2 exposure() always 0.0   ", "specs.py",
     "    if total == 0:\n        return 0.0\n    n_struct = sum(1 for c in spec[\"clauses\"] if c[0] != \"obs\")\n    return n_struct / total",
     "    return 0.0  # PLANT"),
    ("S3 specificity() constant  ", "specs.py",
     "    n_obs = sum(1 for c in spec[\"clauses\"] if c[0] == \"obs\")\n    return n_obs / M",
     "    return 0.5  # PLANT"),
    ("S4 constructor ignores r   ", "specs.py",
     "    b = budget(len(obs), r_target, len(cands))\n",
     "    b = 0  # PLANT\n"),
    ("S5 reachability quantum 1.0", "specs.py",
     "    quantum = 1.0 / (total + 1) if total else 1.0",
     "    quantum = 1.0  # PLANT"),
    ("S6 structural clauses unchecked", "specs.py",
     "        elif kind == \"top\":\n            if prog[0] != c[1]:\n                return False",
     "        elif kind == \"top\":\n            pass  # PLANT"),
]


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    ok = True
    try:
        for i, (label, fname, old, new) in enumerate(PLANTS, 1):
            d = SCRATCH / f"p{i}"
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(RESEARCH, d,
                            ignore=shutil.ignore_patterns("_plant_scratch*"))
            p = d / fname
            text = p.read_text()
            if old not in text:
                print(f"  {label:<30} SETUP-FAIL: anchor not found in {fname}")
                ok = False
                continue
            p.write_text(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "smoke_frontier.py"], cwd=d,
                               capture_output=True, text=True, timeout=900)
            caught = r.returncode != 0
            reason = ""
            for line in (r.stdout or "").splitlines():
                if line.strip().startswith(("FAIL", "SPECS: FAIL")):
                    reason = line.strip()[:64]
                    break
            if not reason and r.stderr:
                last = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-1]
                reason = "crash: " + last[:54]
            print(f"  {label:<30} {'CAUGHT' if caught else 'MISSED':<6} {reason}")
            ok = ok and caught
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print()
    print("SPEC-LAYER PLANT AUDIT: " + ("ALL PLANTS CAUGHT" if ok else "SOME PLANTS MISSED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
