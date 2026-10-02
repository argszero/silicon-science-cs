#!/usr/bin/env python3
"""Instrument self-audit for the DECISIVE RUN (issue #114, Step 5).

A control that never fires is decoration.  For each plant: copy the research tree to a
scratch directory, corrupt ONE thing, run `smoke_decide.py` there, and require it to exit
NONZERO.

Plants:
  D1 the fast path ignores the pin-set ALIGNMENT (always the default permutation)
     -> R1 must fire: the mask no longer equals the checker's own verdict
  D2 the fast path spends the whole menu (b = B) instead of the exposure budget
     -> R4 must fire: the fast path no longer agrees with `make_spec`
  D3 reachability reverted to the tolerance-only rule
     -> R5a must fire: an empty spec "satisfies" a positive exposure request
  D4 the oracle always answers "preserving"
     -> R7 must fire: with no changing mutation the generated population collapses
  D5 the semantic dedup disabled in the reference set
     -> R7b must fire: two references denote the same table

D3 is the plant for a defect this round actually found (the Step 2-4 grid printed
`reached yes` on its s = 0 rows); D5 is the plant for a filter that silently inflates the
population.  Run: python3 plant_decide.py     (exit 0 == all caught)
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

RESEARCH = pathlib.Path(__file__).resolve().parent
SCRATCH = RESEARCH / "_plant_scratch_decide"

PLANTS = [
    ("D1 fast path ignores the alignment", "fast.py",
     "        if align not in self._obs_prefix_cache:\n"
     "            out, cur = [0], 0\n"
     "            for i in domain_perm(align):\n",
     "        if align not in self._obs_prefix_cache:\n"
     "            out, cur = [0], 0\n"
     "            for i in domain_perm(None):  # PLANT\n"),
    ("D2 fast path spends the whole menu", "fast.py",
     "        b = budget(k, r_target, self.B)\n",
     "        b = self.B  # PLANT\n"),
    ("D3 vacuous reachability tolerance", "specs.py",
     "    if r_target <= 0.0:\n"
     "        return achieved, quantum, b == 0\n"
     "    reached = b > 0 and abs(achieved - r_target) <= quantum + 1e-12\n"
     "    return achieved, quantum, reached\n",
     "    return achieved, quantum, abs(achieved - r_target) <= quantum + 1e-12  # PLANT\n"),
    ("D4 oracle always says preserving", "oracle.py",
     "    t0 = table(prog)\n    t1 = table(mutant)\n",
     "    t0 = table(prog)\n    t1 = table(prog)  # PLANT\n"),
    ("D5 semantic dedup disabled", "progspace.py",
     "        rep.setdefault(table(p), p)      # canonical-first representative of each table\n",
     "        rep[to_str(p)] = p  # PLANT: dedup by SOURCE, not by semantics\n"),
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
                            ignore=shutil.ignore_patterns("_plant_scratch*", "__pycache__"))
            p = d / fname
            text = p.read_text()
            if old not in text:
                print(f"  {label:<46} SETUP-FAIL: anchor not found in {fname}")
                ok = False
                continue
            p.write_text(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "smoke_decide.py"], cwd=d,
                               capture_output=True, text=True, timeout=900)
            caught = r.returncode != 0
            reason = ""
            for line in (r.stdout or "").splitlines():
                if line.strip().startswith("[FAIL]"):
                    reason = line.strip()[:78]
                    break
            if not reason and r.stderr:
                last = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-1]
                reason = "crash: " + last[:64]
            print(f"  {label:<46} {'CAUGHT' if caught else 'MISSED':<6} {reason}")
            report.append((label, caught))
            ok = ok and caught
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print()
    print("DECISIVE-RUN SELF-AUDIT: " + ("ALL PLANTS CAUGHT" if ok else "SOME PLANTS MISSED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
