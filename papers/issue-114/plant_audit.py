#!/usr/bin/env python3
"""Instrument self-audit for issue #114: do the smoke battery's controls actually fire?

A control that never fires is decoration.  For each plant we copy these modules to a scratch tree,
corrupt ONE thing, run smoke_oracle.py there, and require it to exit NONZERO.

Four plants:
  P1  the oracle always answers "preserving"       -> must be caught (C4 fires)
  P2  a "legit" operator rewritten to be broken    -> must be caught (C1 fires)
  P3  the semantics domain truncated to {0}        -> must be caught (C6 fires)
  P4  the `mod` literal-slot guard removed         -> must be caught (assert fires)

P3 is the plant that was MISSED before control C6 existed: truncating the domain makes the oracle
unsound while every other control still passed, because widening a check's tolerance is invisible to
controls written inside that tolerance.  Run: python3 plant_audit.py   (exit 0 == all caught)
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

RESEARCH = pathlib.Path(__file__).resolve().parent
SCRATCH = RESEARCH / "_plant_scratch"

PLANTS = [
    ("P1 oracle always says preserving", "oracle.py",
     "    t0 = table(prog)\n    t1 = table(mutant)\n",
     "    t0 = table(prog)\n    t1 = table(prog)  # PLANT\n"),
    ("P2 broken legit operator", "mutations.py",
     '    return [("add-zero", ("add", e, ("const", 0)))]',
     '    return [("add-zero", ("add", e, ("const", 1)))]  # PLANT'),
    ("P3 truncated semantics domain", "toylang.py",
     "    if domain is None:\n        domain = range(M)",
     "    if domain is None:\n        domain = range(1)  # PLANT"),
    ("P4 literal-slot guard removed", "mutations.py",
     "                    if literal and name not in _CONST_PRODUCING:\n"
     "                        continue  # ill-typed at a literal slot\n",
     "                    if False:\n                        continue  # PLANT\n"),
]


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    ok, report = True, []
    try:
        for i, (label, fname, old, new) in enumerate(PLANTS, 1):
            d = SCRATCH / f"p{i}"
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(RESEARCH, d,
                            ignore=shutil.ignore_patterns("_plant_scratch"))
            p = d / fname
            text = p.read_text()
            if old not in text:
                print(f"  {label:<38} SETUP-FAIL: anchor not found in {fname}")
                ok = False
                continue
            p.write_text(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "smoke_oracle.py"], cwd=d,
                               capture_output=True, text=True, timeout=300)
            caught = r.returncode != 0
            reason = ""
            for line in (r.stdout or "").splitlines():
                if line.strip().startswith(("FAIL", "SMOKE: FAIL")):
                    reason = line.strip()[:70]
                    break
            if not reason and r.stderr:
                last = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-1]
                reason = "crash: " + last[:60]
            print(f"  {label:<38} {'CAUGHT' if caught else 'MISSED':<6} {reason}")
            report.append((label, caught))
            ok = ok and caught
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print()
    print("INSTRUMENT SELF-AUDIT: " + ("ALL PLANTS CAUGHT" if ok else "SOME PLANTS MISSED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
