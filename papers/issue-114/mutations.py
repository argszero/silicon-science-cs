#!/usr/bin/env python3
"""Mutation algebra with a semantics-preservation oracle (issue #114).

WHY THIS FILE EXISTS
--------------------
The study contrasts two things a specification can constrain:
  * *observable* behaviour (what the program computes), and
  * *representational* internals (how it computes it).
To measure either, the instrument needs a population of program changes that is
labelled by construction but *decided* by the reference interpreter:

  intent = "legit"  -> the operator is semantics-preserving BY CONSTRUCTION
                       (commutativity in Z_M, folding, double negation, ...)
  intent = "defect" -> the operator is intended to break semantics

The oracle in oracle.py does NOT trust `intent`.  It computes the tables of the
original and the mutant under toylang's reference interpreter and compares them.
The two can disagree, and the disagreement is a *finding*, not a bug:

  * a "defect" that is computed preserving is a **semantically masked defect**
    (e.g. swapping the branches of an `ite` whose branches are equal); such a
    mutation is invisible to ANY specification, however strong.
  * a "legit" that is computed changing would be an error in this file, and the
    smoke battery asserts there are none (a two-sided control).

So every mutation carries (intent, site, description) and the oracle adds the
computed verdict.  No human labels are involved anywhere.

MUTATION OPERATORS  (single-site; the walk enumerates every subtree)
--------------------------------------------------------------------
legit  : add-commute, mul-commute, add-zero, mul-one, ite-negate-swap,
         double-negation, conjoin-true, fold-add, fold-mul, fold-lt, fold-mod
defect : const-off-by-one, add-to-sub, mul-to-add, lt-swap, ite-swap-no-negate,
         and-to-or, and-drop, max-to-min, mod-arg-inc
"""

from __future__ import annotations

import copy

from toylang import M

LEGIT = "legit"
DEFECT = "defect"


# --------------------------------------------------------------------------
# walking / rewriting
# --------------------------------------------------------------------------

def walk(e, path=()):
    """Yield (path, subtree) for every node; path is a tuple of child indices."""
    yield path, e
    for i, child in enumerate(e[1:], start=1):
        if isinstance(child, tuple):
            yield from walk(child, path + (i,))


def _node_at(e, path):
    for i in path:
        e = e[i]
    return e


def is_literal_slot(prog, path) -> bool:
    """True iff the node at `path` is a *literal* position, not an expression position.

    Only `(mod e <int>)` has one: its second argument is a compile-time modulus,
    not an expression.  An expression-level rewrite (double negation, add-zero, a
    branch swap, ...) inserted there would make the program ill-typed, so the
    enumerator must not offer it -- the language guarantees the divisor is a
    literal and `table` relies on that to stay total (no division by zero).
    """
    if not path or path[-1] != 2:
        return False
    return _node_at(prog, path[:-1])[0] == "mod"


# Operators that yield a `const` node, i.e. the only ones admissible at a
# literal slot.  Every other operator returns a non-constant expression.
_CONST_PRODUCING = {
    "const-off-by-one", "mod-arg-inc",
    "fold-add", "fold-sub", "fold-mul", "fold-max", "fold-min",
    "fold-lt", "fold-mod",
}


def replace_at(e, path, new):
    """Return a copy of `e` with the subtree at `path` replaced by `new`."""
    if not path:
        return new
    head, rest = path[0], path[1:]
    children = list(e[1:])
    idx = head - 1
    children[idx] = replace_at(children[idx], rest, new)
    return (e[0], *children)


def size(e) -> int:
    return 1 + sum(size(c) for c in e[1:] if isinstance(c, tuple))


# --------------------------------------------------------------------------
# legit operators: semantics-preserving for EVERY program (by construction)
# --------------------------------------------------------------------------

def _l_add_commute(e):
    if e[0] == "add":
        return [("add-commute", ("add", e[2], e[1]))]
    return []


def _l_mul_commute(e):
    if e[0] == "mul":
        return [("mul-commute", ("mul", e[2], e[1]))]
    return []


def _l_add_zero(e):
    # e + 0 == e for all e in Z_M
    return [("add-zero", ("add", e, ("const", 0)))]


def _l_mul_one(e):
    # only where a literal 1 is already present, otherwise it is an insertion
    if e[0] == "mul" and e[1] == ("const", 1):
        return [("mul-one", e[2])]
    if e[0] == "mul" and e[2] == ("const", 1):
        return [("mul-one", e[1])]
    return []


def _l_ite_negate_swap(e):
    # (ite c a b) == (ite (not c) b a)
    if e[0] == "ite":
        return [("ite-negate-swap", ("ite", ("not", e[1]), e[3], e[2]))]
    return []


def _l_double_negation(e):
    # -(-v) == v in Z_M, and truthiness is preserved for the boolean positions
    return [("double-negation", ("sub", ("const", 0), ("sub", ("const", 0), e)))]


def _l_conjoin_true(e):
    # (lt a b) AND true  ==  (lt a b)  -- the boolean analogue of add-zero
    if e[0] == "lt":
        return [("conjoin-true", ("and", e, ("const", 1)))]
    return []


def _fold(e):
    """Constant folding -- each variant is exact arithmetic in Z_M."""
    if e[0] not in ("add", "sub", "mul", "max", "min", "lt", "mod"):
        return []
    if not all(isinstance(c, tuple) and c[0] == "const" for c in e[1:]):
        return []
    if e[0] == "add":
        return [("fold-add", ("const", (e[1][1] + e[2][1]) % M))]
    if e[0] == "sub":
        return [("fold-sub", ("const", (e[1][1] - e[2][1]) % M))]
    if e[0] == "mul":
        return [("fold-mul", ("const", (e[1][1] * e[2][1]) % M))]
    if e[0] == "max":
        return [("fold-max", ("const", max(e[1][1], e[2][1])))]
    if e[0] == "min":
        return [("fold-min", ("const", min(e[1][1], e[2][1])))]
    if e[0] == "lt":
        return [("fold-lt", ("const", 1 if e[1][1] < e[2][1] else 0))]
    if e[0] == "mod":
        return [("fold-mod", ("const", e[1][1] % e[2][1]))]
    return []


LEGIT_OPS = (
    _l_add_commute,
    _l_mul_commute,
    _l_add_zero,
    _l_mul_one,
    _l_ite_negate_swap,
    _l_double_negation,
    _l_conjoin_true,
    _fold,
)


# --------------------------------------------------------------------------
# defect operators: intended to change semantics (may still be masked)
# --------------------------------------------------------------------------

def _d_const_off_by_one(e):
    if e[0] == "const":
        return [("const-off-by-one", ("const", (e[1] + 1) % M))]
    return []


def _d_add_to_sub(e):
    if e[0] == "add":
        return [("add-to-sub", ("sub", e[1], e[2]))]
    return []


def _d_mul_to_add(e):
    if e[0] == "mul":
        return [("mul-to-add", ("add", e[1], e[2]))]
    return []


def _d_lt_swap(e):
    if e[0] == "lt":
        return [("lt-swap", ("lt", e[2], e[1]))]
    return []


def _d_ite_swap(e):
    if e[0] == "ite":
        return [("ite-swap-no-negate", ("ite", e[1], e[3], e[2]))]
    return []


def _d_and_to_or(e):
    if e[0] == "and":
        return [("and-to-or", ("or", e[1], e[2]))]
    return []


def _d_and_drop(e):
    if e[0] == "and":
        return [("and-drop", e[1])]
    return []


def _d_max_to_min(e):
    if e[0] == "max":
        return [("max-to-min", ("min", e[1], e[2]))]
    return []


def _d_mod_arg_inc(e):
    if e[0] == "mod" and e[2][1] + 1 < M:
        return [("mod-arg-inc", ("mod", e[1], ("const", e[2][1] + 1)))]
    return []


DEFECT_OPS = (
    _d_const_off_by_one,
    _d_add_to_sub,
    _d_mul_to_add,
    _d_lt_swap,
    _d_ite_swap,
    _d_and_to_or,
    _d_and_drop,
    _d_max_to_min,
    _d_mod_arg_inc,
)


# --------------------------------------------------------------------------
# enumeration
# --------------------------------------------------------------------------

def enumerate_mutations(prog, include_legit=True, include_defect=True):
    """All single-site mutations of `prog`.

    Returns a list of dicts:
      {path, intent, operator, description, mutant}
    The verdict (preserving or not) is NOT decided here -- see oracle.py.
    """
    out = []
    ops = []
    if include_legit:
        ops.append((LEGIT, LEGIT_OPS))
    if include_defect:
        ops.append((DEFECT, DEFECT_OPS))
    for path, sub in walk(prog):
        literal = is_literal_slot(prog, path)
        for intent, table_ops in ops:
            for fn in table_ops:
                for name, new_sub in fn(sub):
                    if new_sub == sub:
                        continue  # a no-op rewrite is not a mutation
                    if literal and name not in _CONST_PRODUCING:
                        continue  # ill-typed at a literal slot
                    mutant = replace_at(prog, path, copy.deepcopy(new_sub))
                    out.append({
                        "path": path,
                        "intent": intent,
                        "operator": name,
                        "description": f"{name} at path {path or 'root'}",
                        "mutant": mutant,
                    })
    return out
