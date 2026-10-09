#!/usr/bin/env python3
"""Which clause family drives detection, and which drives breakage? (issue #114)

The sweep reports breakage as one number; a mechanism must be countable, so this
splits it.  For each representational clause KIND and for the observational family,
it counts the mutations that violate at least one clause of that kind:

    changing (semantics-changing per the oracle)  -> that kind CONTRIBUTES to detection
    preserving (semantics-preserving per the oracle) -> that kind CREATES breakage

Run: python3 diag_clauses.py
"""

from __future__ import annotations

import sys
from collections import Counter

from frontier import BASE_PROGRAMS, population
from mutations import enumerate_mutations
from oracle import classify
from specs import make_spec, satisfies
from toylang import parse

S_TARGET = 0.25   # a mid grade: enough pinned inputs to detect, not saturated
R_TARGET = 0.05   # a low exposure: few structural clauses, so the kinds are resolvable


def kinds_violated(spec, prog):
    """The clause kinds `prog` violates (obs / top / no_op / node_op / size / depth)."""
    out = set()
    import specs as S
    for c in spec["clauses"]:
        single = {"reference": spec["reference"], "clauses": [c]}
        if not S.satisfies(single, prog):
            out.add(c[0])
    return out


def main() -> int:
    programs = [parse(s) for s in BASE_PROGRAMS]
    programs.append(parse("(ite (lt x 10) (add x 1) (add x 1))"))  # the masked-branch shape
    print("=" * 76)
    print(f"issue #114 -- which clause kind does the work?  (s_target={S_TARGET}, r_target={R_TARGET})")
    print("=" * 76)

    spec = make_spec(programs[0], S_TARGET, R_TARGET)
    print("\nstructural clause kinds present in the spec for the first program:")
    from specs import clause_counts, exposure, specificity
    print(f"  computed s={specificity(spec):.4f}  r={exposure(spec):.4f}  "
          f"clauses obs+struct={clause_counts(spec)}")
    by_kind = Counter(c[0] for c in spec["clauses"])
    for k, v in sorted(by_kind.items()):
        print(f"    {k:<9} {v}")

    chg_hits, prs_hits = Counter(), Counter()
    for prog in programs:
        spec = make_spec(prog, S_TARGET, R_TARGET)
        changing, preserving = population(prog)
        for m in changing:
            for k in kinds_violated(spec, m):
                chg_hits[k] += 1
        for m in preserving:
            for k in kinds_violated(spec, m):
                prs_hits[k] += 1

    n_chg = sum(len(population(p)[0]) for p in programs)
    n_prs = sum(len(population(p)[1]) for p in programs)
    print(f"\nover {len(programs)} programs: {n_chg} changing, {n_prs} preserving mutations")
    print(f"{'kind':<9} {'violated by':>12} {'violated by':>12}")
    print(f"{'':<9} {'CHANGING':>12} {'PRESERVING':>12}   <- detection contribution | breakage created")
    for k in ("obs", "top", "no_op", "node_op", "size_le", "depth_le"):
        c = chg_hits.get(k, 0)
        p = prs_hits.get(k, 0)
        if c or p:
            print(f"{k:<9} {c:>12} {p:>12}")
    print("\nreading: a kind with 0 in the PRESERVING column can never create a false alarm;")
    print("         'obs' must be 0 there -- that is the mechanism the study claims.")

    obs_prs = prs_hits.get("obs", 0)
    if obs_prs != 0:
        print(f"\nMECHANISM VIOLATED: observational clauses caused {obs_prs} false alarm(s)")
        return 1
    print("\nMECHANISM HOLDS: no observational clause was violated by any preserving mutation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
