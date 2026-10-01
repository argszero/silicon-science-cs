#!/usr/bin/env python3
"""The ALIGNMENT axis (issue #114, registered prior P1).

WHY THIS FILE EXISTS
--------------------
Prior P1 says: *at matched specificity, detection varies across behaviour-alignments
by >= 2x.*  `s` counts HOW MUCH of the observable behaviour a spec pins; alignment is
WHERE.  This module makes both measurable and, unusually, EXACTLY predictable.

THE CONSTRUCTION THAT MAKES ALIGNMENT VISIBLE
---------------------------------------------
A spread or clustered pin set can only be told apart by a change whose effect is
itself concentrated.  So the change distribution is parameterised directly, with a
wrapper that is expressible in the existing language:

    regional_low(P, t)  =  (ite (lt x t)      (add P 1) P)   differs exactly on [0, t)
    regional_high(P, t) =  (ite (lt t x)      (add P 1) P)   differs exactly on (t, M)

Both are semantics-CHANGING by construction (`v + 1 != v` in Z_256 for every v), and
their difference sets are known exactly, so detection at a given pin set is decidable
without running the population at all:

    detect(P, regional_low(t))  =  1  iff  P intersects [0, t)
    detect(P, regional_high(t)) =  1  iff  P intersects (t, M)

Summed over a uniform grid of t this gives a closed form in the pin set's EXTREMES:

    mean_t detect(P, low)  = (M - min(P)) / M          mean_t detect(P, high) = max(P) / M

which is what `predict_extremes` computes -- so the measurement can be checked against
a prediction rather than merely reported (control G2).

PURE OBSERVATIONAL SPECS ONLY (r = 0).  A structural clause would reject the wrapper
outright -- it changes the root to `ite` and grows the tree -- and would then confound
alignment with exposure.  r = 0 also makes breakage exactly 0, so this axis measures
detection alone.  The r = 0 restriction is a deliberate scope, stated in the report.
"""

from __future__ import annotations

import random
import sys

from specs import make_spec, satisfies
from toylang import M, parse, table

# ---- pin-set alignments (all of size k, so specificity is matched exactly) ----

_STRIDE = 97  # coprime with 256; the "spread" alignment used since Step 2


def pins(alignment: str, k: int):
    """k distinct inputs, chosen by `alignment`.  Every alignment pins exactly k."""
    if not (0 <= k <= M):
        raise ValueError("k out of range")
    if alignment == "spread":
        return tuple(sorted(((i * _STRIDE) % M) for i in range(k)))
    if alignment == "block-low":
        return tuple(range(k))
    if alignment == "block-high":
        return tuple(range(M - k, M))
    if alignment == "block-mid":
        lo = (M - k) // 2
        return tuple(range(lo, lo + k))
    if alignment == "parity-even":
        return tuple((2 * i) % M for i in range(k))
    if alignment == "parity-odd":
        return tuple((2 * i + 1) % M for i in range(k))
    if alignment.startswith("rand"):
        seed = int(alignment[4:])
        return tuple(sorted(random.Random(seed).sample(range(M), k)))
    raise ValueError(f"unknown alignment {alignment!r}")


def obs_spec(prog, P):
    """A PURE observational spec for `prog` pinning exactly the inputs in P."""
    tbl = table(prog)
    return {"reference": prog, "clauses": [("obs", i, tbl[i]) for i in P],
            "s_target": len(P) / M, "r_target": 0.0}


# ---- regional changes: difference set known by construction -------------------

def regional_low(prog, t: int):
    """Differs from `prog` exactly on x < t."""
    return ("ite", ("lt", ("x",), ("const", t % M)), ("add", prog, ("const", 1)), prog)


def regional_high(prog, t: int):
    """Differs from `prog` exactly on x > t."""
    return ("ite", ("lt", ("const", t % M), ("x",)), ("add", prog, ("const", 1)), prog)


def diff_set(prog, mut):
    """The exact set of inputs the mutation changes (ground truth, not assumed)."""
    a, b = table(prog), table(mut)
    return frozenset(i for i in range(M) if a[i] != b[i])


# ---- the measurement and its prediction --------------------------------------

def detect_low(P, t) -> bool:
    return any(i < t for i in P)


def detect_high(P, t) -> bool:
    return any(i > t for i in P)


def measure_curve(P, region: str, ts):
    """detection as a function of the change location t."""
    f = detect_low if region == "low" else detect_high
    return [1.0 if f(P, t) else 0.0 for t in ts]


def predict_curve(P, region: str, ts):
    """The closed-form prediction: a step at the pin set's own extreme."""
    if not P:
        return [0.0 for _ in ts]
    if region == "low":
        edge = min(P)          # detects iff some pin < t  -> step just after min(P)
        return [1.0 if t > edge else 0.0 for t in ts]
    edge = max(P)              # detects iff some pin > t  -> step just below max(P)
    return [1.0 if t < edge else 0.0 for t in ts]


def predict_extremes(P, region: str) -> float:
    if not P:
        return 0.0
    return (M - min(P)) / M if region == "low" else max(P) / M


ALIGNMENTS = ["spread", "block-low", "block-high", "block-mid", "parity-even", "parity-odd"] \
             + [f"rand{s}" for s in (1, 2, 3, 4, 5)]
T_GRID = [t for t in range(1, M)]      # 255 change locations
