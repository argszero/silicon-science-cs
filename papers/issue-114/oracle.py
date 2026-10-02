#!/usr/bin/env python3
"""The semantics-preservation oracle (issue #114).

Given a base program P and a mutation of it, decide -- by computation, not by
the operator's declared intent -- whether the mutation preserves semantics.

    preserving(P, mutant) := table(P) == table(mutant)

`intent` comes from the operator's construction ("legit" rewrites are
preserving for every program; "defect" rewrites are meant to break it).  The
oracle ignores intent.  Where the two disagree we record it, because the
disagreement is the phenomenon:

    masked defect   : intent=defect, oracle=preserving
                      -> invisible to every specification, however strong
    broken legit    : intent=legit,  oracle=changing
                      -> an error in mutations.py; the smoke battery asserts 0

The output of `analyze` is the raw material for every later measurement, so it
is emitted as plain JSON-serialisable rows with no derived statistics baked in
(statistics are computed where they are reported, not stored here).
"""

from __future__ import annotations

import json

from mutations import enumerate_mutations
from toylang import equivalent, table, to_str


def classify(prog, mutant):
    """Return (preserving: bool, difference_count: int)."""
    t0 = table(prog)
    t1 = table(mutant)
    if t0 == t1:
        return True, 0
    return False, sum(1 for a, b in zip(t0, t1) if a != b)


def analyze(prog, include_legit=True, include_defect=True):
    """Every single-site mutation of `prog`, with the computed verdict attached."""
    rows = []
    for mut in enumerate_mutations(prog, include_legit, include_defect):
        preserving, ndiff = classify(prog, mut["mutant"])
        rows.append({
            "base": to_str(prog),
            "base_size": None,  # filled by the caller if wanted; kept out of the oracle
            "path": mut["path"],
            "operator": mut["operator"],
            "intent": mut["intent"],
            "mutant": to_str(mut["mutant"]),
            "preserving": preserving,
            "n_differing_inputs": ndiff,
        })
    return rows


def summarize(rows):
    """Counts only -- no interpretation.  Kept separate so the numbers a report
    prints are re-derived from the rows rather than stored alongside them."""
    legit = [r for r in rows if r["intent"] == "legit"]
    defect = [r for r in rows if r["intent"] == "defect"]
    return {
        "total": len(rows),
        "legit": len(legit),
        "defect": len(defect),
        "legit_preserving": sum(1 for r in legit if r["preserving"]),
        "legit_changing": sum(1 for r in legit if not r["preserving"]),
        "defect_changing": sum(1 for r in defect if not r["preserving"]),
        "defect_masked": sum(1 for r in defect if r["preserving"]),
    }


def dumps(rows):
    """Stable serialisation -- used by the determinism control."""
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))
