#!/usr/bin/env python3
"""The reference program set for the decisive run (issue #114, Step 5).

WHY THIS FILE EXISTS
--------------------
Steps 2-4 ran on six hand-written programmes.  A decisive run should not choose its
population by hand: an author who picks the six programmes can pick the six that make the
story.  So the reference set is GENERATED, by a rule stated once, and every filter is a
filter on a property that is COMPUTED, not on taste:

  1. every well-formed programme of the toy language with at most `MAX_NODES` nodes, over
     a DECLARED finite literal vocabulary (the language's own `mod`-divisor rule is
     respected: the divisor is a literal in 1..M-1);
  2. deduplicated by SEMANTICS: two sources denoting the same table are one reference, and
     the canonical-first source is the representative.  (The collapse is large -- the
     count is reported -- which is exactly why dedup cannot be skipped: keeping semantic
     twins would weight the population by how many ways there are to write a function.)
  3. drop a programme whose table is CONSTANT (nothing observable to pin, nothing to
     align to), and a programme with no mutation and with no semantics-CHANGING mutation
     (the oracle decides that, like everything else here);
  4. take every survivor -- no sampling, so no selection -- and add, as a declared
     separate tier, the six named references of Steps 2-4, so every earlier number stays
     traceable to a reference that is still in the study.

Every count a rule removes is reported by `census()`, because a filter that silently
shrinks a population is how a reference set becomes a selection.

Usage: python3 progspace.py     (prints the census; exit 0)
"""

from __future__ import annotations

import sys

from mutations import enumerate_mutations
from oracle import classify
from toylang import parse, table, to_str

ARITY = {"add": 2, "sub": 2, "mul": 2, "max": 2, "min": 2,
         "lt": 2, "and": 2, "or": 2, "not": 1, "ite": 3, "mod": 2}

# The declared literal vocabulary.  Small on purpose: the study is about the SHAPE of a
# specification relative to a program, not about the 8-bit constant it happens to mention.
CONSTS = (0, 1, 2, 3, 5, 7, 10, 100, 128, 200, 255)
DIVISORS = (2, 3, 5, 7, 10, 16)

MAX_NODES = 4          # node count, not depth: ("x",) is 1 node

# The six hand-written references of Steps 2-4 (frontier.py's BASE_PROGRAMS), kept so
# every earlier number is traceable to a reference in this set.
NAMED = [
    "(add x 1)",
    "(mul x x)",
    "(max (min x 200) 10)",
    "(ite (lt x 128) (mul x 2) (sub 200 x))",
    "(mod (add (mul x 3) 7) 5)",
    "(ite (and (lt x 100) (not (lt x 50))) (sub x 50) x)",
]


# --------------------------------------------------------------------------
# generation: every well-formed programme with at most MAX_NODES nodes
# --------------------------------------------------------------------------

def by_node_count(max_nodes: int = MAX_NODES):
    """{n: [ast, ...]} for every well-formed programme of exactly n nodes."""
    sizes: dict = {1: [("x",)] + [("const", v) for v in CONSTS]}
    for n in range(2, max_nodes + 1):
        out = []
        for op, arity in ARITY.items():
            if op == "mod":
                if n < 3:            # (mod e <literal>) is at least 3 nodes
                    continue
                for a in sizes.get(n - 2, []):
                    for v in DIVISORS:
                        out.append(("mod", a, ("const", v)))
                continue
            if arity == 1:
                for a in sizes.get(n - 1, []):
                    out.append((op, a))
            elif arity == 2:
                for n1 in range(1, n - 1):
                    for a in sizes.get(n1, []):
                        for b in sizes.get(n - 1 - n1, []):
                            out.append((op, a, b))
            else:  # ite
                for n1 in range(1, n - 2):
                    for n2 in range(1, n - 1 - n1):
                        for a in sizes.get(n1, []):
                            for b in sizes.get(n2, []):
                                for c in sizes.get(n - 1 - n1 - n2, []):
                                    out.append((op, a, b, c))
        sizes[n] = out
    return sizes


def all_sources(max_nodes: int = MAX_NODES):
    """Every generated source, in a canonical order (by source string)."""
    sizes = by_node_count(max_nodes)
    out = [p for n in sorted(sizes) for p in sizes[n]]
    out.sort(key=to_str)
    return out


def stride_sample(xs, k: int):
    """A deterministic, spread sample of `xs` of size <= k (every len//k-th element).

    NOT used by `reference_set` (which takes every survivor); kept because a study that
    must shrink its population should do it by a stated stride rather than by taste, and
    the plant audit uses it to drive the reference set to a degenerate size.
    """
    if len(xs) <= k:
        return list(xs)
    step = max(1, len(xs) // k)
    return list(xs[::step])[:k]


# --------------------------------------------------------------------------
# the reference set
# --------------------------------------------------------------------------

def reference_set(max_nodes: int = MAX_NODES, with_named: bool = True):
    """The decisive run's reference programmes, with the census of what was removed."""
    census = {
        "generated_sources": 0,
        "distinct_semantics": 0,
        "dropped_constant_table": 0,
        "dropped_no_mutations": 0,
        "dropped_no_changing_mutation": 0,
        "dropped_named_duplicate": 0,
    }
    srcs = all_sources(max_nodes)
    census["generated_sources"] = len(srcs)

    rep: dict = {}
    for p in srcs:
        rep.setdefault(table(p), p)      # canonical-first representative of each table
    census["distinct_semantics"] = len(rep)

    survivors = []
    for tbl, p in rep.items():
        if len(set(tbl)) == 1:
            census["dropped_constant_table"] += 1
            continue
        muts = enumerate_mutations(p)
        if not muts:
            census["dropped_no_mutations"] += 1
            continue
        if not any(not classify(p, m["mutant"])[0] for m in muts):
            census["dropped_no_changing_mutation"] += 1
            continue
        survivors.append((to_str(p), p))
    survivors.sort()

    chosen, seen = [], set()
    for src, p in survivors:
        seen.add(table(p))
        chosen.append({"src": src, "prog": p, "tier": "systematic"})

    if with_named:
        for src in NAMED:
            p = parse(src)
            if table(p) in seen:
                census["dropped_named_duplicate"] += 1
                continue
            seen.add(table(p))
            chosen.append({"src": src, "prog": p, "tier": "named"})

    census["kept"] = len(chosen)
    return chosen, census


def main() -> int:
    from collections import Counter
    chosen, census = reference_set()
    print("=" * 84)
    print("issue #114 -- generated reference set for the decisive run")
    print("=" * 84)
    for k in ("generated_sources", "distinct_semantics", "dropped_constant_table",
              "dropped_no_mutations", "dropped_no_changing_mutation",
              "dropped_named_duplicate", "kept"):
        print(f"  {k:<30} {census[k]}")
    print()
    print("  tiers  :", dict(Counter(c["tier"] for c in chosen)))
    print("  root op:", dict(sorted(Counter(c["prog"][0] for c in chosen).items())))
    from mutations import size
    print("  sizes  :", dict(sorted(Counter(size(c["prog"]) for c in chosen).items())))
    print()
    for c in chosen[:12]:
        print(f"    [{c['tier'][:4]}] {c['src']}")
    print(f"    ... ({len(chosen)} in all)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
