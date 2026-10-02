#!/usr/bin/env python3
"""Plant audit for the alignment axis (issue #114).

Copies the modules to a scratch tree, corrupts ONE thing, runs smoke_align.py there, and
requires it to exit nonzero.  Six plants, each aimed at a named control; a MISSED plant
means that control is decoration.

  A1  pins() ignores the alignment        -> G3 (the span collapses to 1x)
  A2  the low-region model is flipped     -> G2 (the real checker disagrees)
  A3  the wrapper changes the wrong region-> G5 (difference sets wrong)
  A4  predict_extremes returns a constant -> G3
  A5  the spec pins k+1 inputs            -> G1 (specificity no longer matched; G1 reads the
                                             built SPEC's clause list, not just the pin list)
  A6  predict_curve echoes the measurement-> expected NEUTRALISED, not caught: G2 anchors on
                                             the real checker and owns its expectation, so an
                                             echoing prediction can no longer hide a wrong
                                             measurement.  Reported honestly rather than
                                             claimed as a catch.

Run: python3 plant_audit_align.py
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

RESEARCH = pathlib.Path(__file__).resolve().parent
SCRATCH = RESEARCH / "_plant_scratch_align"

PLANTS = [
    ("A1 pins() ignores alignment  ", "align.py",
     '    if not (0 <= k <= M):\n        raise ValueError("k out of range")',
     '    if not (0 <= k <= M):\n        raise ValueError("k out of range")\n    return tuple(range(k))  # PLANT-A1'),
    ("A2 low-region model flipped  ", "align.py",
     "def detect_low(P, t) -> bool:\n    return any(i < t for i in P)",
     "def detect_low(P, t) -> bool:\n    return any(i > t for i in P)  # PLANT-A2"),
    ("A3 wrapper: wrong region     ", "align.py",
     'def regional_low(prog, t: int):\n    """Differs from `prog` exactly on x < t."""\n    return ("ite", ("lt", ("x",), ("const", t % M)), ("add", prog, ("const", 1)), prog)',
     'def regional_low(prog, t: int):\n    """PLANT-A3"""\n    return ("ite", ("lt", ("const", t % M), ("x",)), ("add", prog, ("const", 1)), prog)'),
    ("A4 predict_extremes constant ", "align.py",
     "def predict_extremes(P, region: str) -> float:\n    if not P:\n        return 0.0\n    return (M - min(P)) / M if region == \"low\" else max(P) / M",
     "def predict_extremes(P, region: str) -> float:\n    return 0.5  # PLANT-A4"),
    ("A5 specificity not matched   ", "align.py",
     'def obs_spec(prog, P):\n    """A PURE observational spec for `prog` pinning exactly the inputs in P."""\n    tbl = table(prog)\n    return {"reference": prog, "clauses": [("obs", i, tbl[i]) for i in P],',
     'def obs_spec(prog, P):\n    """PLANT-A5"""\n    tbl = table(prog)\n    return {"reference": prog, "clauses": [("obs", i, tbl[i]) for i in list(P) + [0]],'),
    ("A6 predict echoes measurement", "align.py",
     "def predict_curve(P, region: str, ts):\n    \"\"\"The closed-form prediction: a step at the pin set's own extreme.\"\"\"",
     "def predict_curve(P, region: str, ts):\n    \"\"\"PLANT-A6\"\"\"\n    return measure_curve(P, region, ts)"),
]


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    caught_all = True
    try:
        for i, (label, fname, old, new) in enumerate(PLANTS, 1):
            d = SCRATCH / f"p{i}"
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(RESEARCH, d, ignore=shutil.ignore_patterns("_plant_scratch*"))
            p = d / fname
            text = p.read_text()
            if old not in text:
                print(f"  {label} SETUP-FAIL: anchor not found in {fname}")
                caught_all = False
                continue
            p.write_text(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "smoke_align.py"], cwd=d,
                               capture_output=True, text=True, timeout=1800)
            caught = r.returncode != 0
            reason = ""
            for line in (r.stdout or "").splitlines():
                if line.strip().startswith(("FAIL", "ALIGNMENT: FAIL")):
                    reason = line.strip()[:60]
                    break
            if not reason and r.stderr:
                last = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-1]
                reason = "crash: " + last[:50]
            status = "CAUGHT" if caught else ("NEUTRALISED" if i == 6 else "MISSED")
            print(f"  {label} {status:<13} {reason}")
            if i != 6:
                caught_all = caught_all and caught
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print()
    print("ALIGNMENT PLANT AUDIT: " + ("ALL PLANTS CAUGHT (A6 neutralised by design)"
                                       if caught_all else "SOME PLANTS MISSED"))
    return 0 if caught_all else 1


if __name__ == "__main__":
    sys.exit(main())
