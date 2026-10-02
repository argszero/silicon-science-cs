#!/usr/bin/env python3
"""Graded specification family for issue #114.

WHY THIS FILE EXISTS
--------------------
The study's constructs are **observational specificity `s`** and **representation
exposure `r`**.  Neither may be asserted: both are computed from the specification
itself, so the x-axis and the z-axis of every later figure are *derived* quantities.
This module defines

  * what a specification IS  (a set of clauses over the toy language),
  * how `specificity(spec)` and `exposure(spec)` are computed from it,
  * how `satisfies(spec, program)` decides whether a program meets it, and
  * how to *construct* a specification with a target (s, r), for use as a grid axis.

CLAUSES
-------
Two families, and the split is exactly the construct:

  observational  ("obs", i, v)     output at input i must equal v
  representational ("top", op)     the root operator must be `op`
                   ("no_op", op)    operator `op` must not occur
                   ("node_op", path, op)   the node at `path` must be `op`
                   ("size_le", n)   node count <= n
                   ("depth_le", n)  AST depth <= n

`specificity` counts ONLY the pinned observable behaviour:
        s = |{i : ("obs", i, ·) in spec}| / |domain|
`exposure` is the registered wording -- the share of the spec's constraints that
mention internals:
        r = |representational clauses| / |all clauses|

CONSEQUENCE WORTH NAMING (it is the study's mechanism, not a footnote): a purely
observational specification (r = 0) has **breakage exactly 0**, because a
semantics-preserving change preserves the whole table and therefore every clause.
So false alarms cannot be produced by specificity alone; they can only be produced
by exposure.  `smoke_frontier.py` asserts this as a control rather than assuming it.

CONSTRUCTION
------------
`make_spec(prog, s_target, r_target)` builds a spec *for* a reference program
`prog`: the observational clauses pin its outputs on a nested prefix of a fixed
input permutation (so higher grades strictly contain lower ones), and the
representational clauses are tight facts about its syntax (root operator, absent
operators, the operator at each path, exact size/depth bounds).  Every clause is
therefore TRUE of the reference; a mutation fails one only by differing from it.

Note on reachability: r is bounded by the number of representational candidates the
reference's syntax offers, so a high (s, r) corner may be unreachable.  The
reported r is always the COMPUTED one; the target is only a request.
"""

from __future__ import annotations

import random

from toylang import M, table
from mutations import size, walk

ALL_OPS = ("add", "sub", "mul", "mod", "max", "min", "lt", "not", "and", "or", "ite", "const", "x")

# A fixed permutation of the input domain, used so that grade k pins a prefix and
# grade k+1 strictly contains grade k (nesting).  97 is coprime with 256.
_PERM = tuple((i * 97) % M for i in range(M))

# The pin-set ALIGNMENT axis (Step 5).  Pinning a prefix of a permutation of the domain
# makes `s` = k/M exactly, for EVERY permutation -- so several permutations give several
# pin sets at MATCHED specificity, and the spread of the measurement across them is the
# alignment band.  `align=None` is the spread permutation used since Step 2, so every
# earlier number is reproduced unchanged; an integer (or "rand<n>") is a seeded
# permutation of the domain, i.e. a uniformly random k-subset for the prefix of grade k.
_PERM_CACHE: dict = {}


def domain_perm(align=None) -> tuple:
    """The domain permutation whose k-prefix is the pin set of grade k.

    `None` is the spread permutation of Steps 2-4 (stride 97), so every earlier number is
    reproduced exactly.  A NAMED alignment is a structured construction -- an author's
    guess about where to pin -- and an INTEGER is a seeded random permutation, i.e. a
    uniformly random k-subset for the prefix of grade k.  Both matter: the structured ones
    are the habits people actually have (pin the interesting corner, pin low, pin high,
    pin the evens), and the random ones are the null to compare them against.
    """
    if align in _PERM_CACHE:
        return _PERM_CACHE[align]
    if align is None:
        perm = _PERM
    elif isinstance(align, str) and not align.startswith("rand"):
        if align == "low":
            perm = tuple(range(M))
        elif align == "high":
            perm = tuple(range(M - 1, -1, -1))
        elif align == "even":
            perm = tuple(range(0, M, 2)) + tuple(range(1, M, 2))
        elif align == "odd":
            perm = tuple(range(1, M, 2)) + tuple(range(0, M, 2))
        elif align == "edges":
            out = []
            for i in range(M // 2):
                out.append(i)
                out.append(M - 1 - i)
            perm = tuple(out)
        else:
            raise ValueError(f"unknown alignment {align!r}")
    else:
        seed = int(align[4:]) if isinstance(align, str) and align.startswith("rand") \
            else int(align)
        order = list(range(M))
        random.Random(seed).shuffle(order)
        perm = tuple(order)
    if len(set(perm)) != M:
        raise AssertionError(f"alignment {align!r} is not a permutation of the domain")
    _PERM_CACHE[align] = perm
    return perm


def _node_at(e, path):
    """The subtree at `path`, or None if the path does not resolve to a node.

    TOTAL on purpose.  A clause's path is valid in the REFERENCE, but `satisfies` is
    also called on mutants, where an ancestor may have become a leaf -- e.g. the
    reference's ("node_op", (1, 1), "const") meets a mutant whose node at (1,) is a
    `const`, and then index 1 of that node is the integer payload, not a node.  Walking
    blindly into an int raised TypeError, which is a crash where the correct answer is
    simply "this clause is false of that program".
    """
    cur = e
    for i in path:
        if not isinstance(cur, tuple) or i >= len(cur):
            return None
        cur = cur[i]
    # the LAST step can land on a non-node too (a `const`'s payload is an int), so the
    # result is checked, not assumed
    return cur if isinstance(cur, tuple) else None


def _operators(e):
    out = {e[0]}
    for c in e[1:]:
        if isinstance(c, tuple):
            out |= _operators(c)
    return out


def depth(e) -> int:
    kids = [c for c in e[1:] if isinstance(c, tuple)]
    return 1 + (max(depth(c) for c in kids) if kids else 0)


def _consts(e):
    out = set()
    if e[0] == "const":
        out.add(e[1])
    for c in e[1:]:
        if isinstance(c, tuple):
            out |= _consts(c)
    return out


def _count_ops(e):
    """How many nodes carry each operator (the reference's own multiplicities)."""
    out = {}
    stack = [e]
    while stack:
        n = stack.pop()
        out[n[0]] = out.get(n[0], 0) + 1
        for c in n[1:]:
            if isinstance(c, tuple):
                stack.append(c)
    return out


def kind_of(clause) -> str:
    """The clause kind.  Declared once, here, and used by the checker's dispatch
    check so that a kind can never be handled in one place and forgotten in another."""
    return clause[0]


# Every clause kind this module knows.  `satisfies` asserts against this set, so an
# unhandled kind is a loud failure rather than a silently-ignored clause.
CLAUSE_KINDS = (
    "obs",
    "top", "no_op", "node_op", "child_op", "op_count_le",
    "const_present", "const_absent",
    "size_le", "depth_le",
)

OBS_KINDS = ("obs",)


# --------------------------------------------------------------------------
# candidates and construction
# --------------------------------------------------------------------------

def representational_candidates(prog):
    """Tight, TRUE-of-`prog` representational clauses, in a deterministic order."""
    cands = [("top", prog[0])]
    used = _operators(prog)
    for op in sorted(set(ALL_OPS) - used):
        cands.append(("no_op", op))
    for path, sub in walk(prog):
        cands.append(("node_op", path, sub[0]))
    # --- added in Step 4: three richer representational families -----------------
    # (a) the operator at each CHILD SLOT -- finer than the node's own operator, and
    #     it is what a legitimate rewrite moves when it re-associates or re-wraps;
    for path, sub in walk(prog):
        for i, c in enumerate(sub[1:], start=1):
            if isinstance(c, tuple):
                cands.append(("child_op", path, i, c[0]))
    # (b) an upper bound on how many nodes carry each operator PRESENT in the
    #     reference -- violated by any change that grows the tree structurally;
    counts = _count_ops(prog)
    for op in sorted(counts):
        cands.append(("op_count_le", op, counts[op]))
    # (c) the literal set: every present literal, plus the absent NEIGHBOURS (c +/- 1)
    #     of each.  The neighbours are the natural off-by-one targets, so this family
    #     is small and sharply constraining.
    present = _consts(prog)
    for v in sorted(present):
        cands.append(("const_present", v))
    for v in sorted(present):
        for w in ((v + 1) % M, (v - 1) % M):
            if w not in present:
                cands.append(("const_absent", w))
    cands.append(("size_le", size(prog)))
    cands.append(("depth_le", depth(prog)))
    return cands


def mixed_candidates(prog, mix):
    """The candidate list re-ordered deterministically.

    `mix is None` keeps the kind-grouped default order.  An integer seed shuffles the
    list, which changes WHICH clauses a spec of a given size contains while leaving its
    SIZE (and therefore `r`) untouched.  That is what makes the composition of the
    exposure axis measurable instead of assumed: two specs with the same (s, r) can
    differ in kind mix, and the spread of breakage across mixes is a property of the
    axis that the study has to report rather than average away.
    """
    cands = representational_candidates(prog)
    if mix is None:
        return cands
    out = list(cands)
    random.Random(mix).shuffle(out)
    return out


def budget(n_obs: int, r_target: float, n_cands: int) -> int:
    """How many representational clauses a request for `r_target` buys.

    THE single site of this rule: `make_spec` and the fast evaluator (`fast.py`) both
    call it, so the decisive run's grid and the reference constructor can never disagree
    about how big `b` is.  `r_target <= 0` (or no observational clause at all) buys zero:
    a structural-only spec has r = 1 and pins no behaviour, so this constructor declines
    to build it.
    """
    if r_target <= 0.0 or n_obs == 0:
        return 0
    b = round(r_target * n_obs / (1.0 - r_target))
    return max(0, min(b, n_cands))


def exposure_plan(n_obs: int, b: int, r_target: float):
    """(achieved, quantum, reached) for a spec with `n_obs` observational and `b` structural clauses.

    `reached` is computed from the ACHIEVED value and the lattice's own spacing, because
    exposure is quantized: `r = b / (b + n_obs)` with integer `b`, so at a fixed `s` the
    reachable exposures form a ladder of spacing ~1/(b + n_obs) -- fine where `s` is large
    and COARSE where `s` is small.

    The empty-spec case is NOT a lattice case and must be decided before the tolerance:
    with no clauses at all `quantum` is 1.0, so "within one step of the request" would be
    true for EVERY request -- the tolerance is vacuous exactly where there is no lattice to
    be tolerant about.  An empty spec answers a positive request with r = 0 and has not met
    it.  (This was a real defect: the Step 2-4 grid printed `reached yes` on its s = 0 rows,
    where every r > 0 request collapses to the empty spec.)
    """
    total = n_obs + b
    achieved = (b / total) if total else 0.0
    quantum = 1.0 / (total + 1) if total else 1.0
    if r_target <= 0.0:
        return achieved, quantum, b == 0
    reached = b > 0 and abs(achieved - r_target) <= quantum + 1e-12
    return achieved, quantum, reached


def make_spec(prog, s_target: float, r_target: float, mix=None, align=None):
    """Build a spec for `prog` aiming at (s_target, r_target).

    Returns a dict with the clauses, plus the REQUESTED targets and a flag saying
    whether the request was actually met.

    Construction choice worth stating: `s_target = 0` builds the empty spec (no
    clauses, r = 0).  A structural-only spec (|obs| = 0, b > 0) would have r = 1 and
    pin no behaviour at all, so this constructor declines to build it and reports any
    request for r > 0 at s = 0 as unmet.

    `mix` chooses the candidate ORDER (which kinds fill the exposure budget, at a fixed
    count) and `align` chooses the pin set (which inputs are pinned, at a fixed count).
    """
    if not (0.0 <= s_target <= 1.0):
        raise ValueError("s_target must be in [0, 1]")
    if not (0.0 <= r_target < 1.0):
        raise ValueError("r_target must be in [0, 1)")
    k = round(s_target * M)
    pinned = domain_perm(align)[:k]
    tbl = table(prog)
    obs = [("obs", i, tbl[i]) for i in pinned]
    cands = mixed_candidates(prog, mix)
    b = budget(len(obs), r_target, len(cands))
    achieved, quantum, reached = exposure_plan(len(obs), b, r_target)
    return {
        "reference": prog,
        "clauses": obs + cands[:b],
        "s_target": s_target,
        "r_target": r_target,
        "r_gap": abs(achieved - r_target),
        "r_quantum": quantum,
        "r_reachable": reached,
        "n_pinned": k,
        "n_cand": b,
    }


# --------------------------------------------------------------------------
# the computed axes -- never asserted
# --------------------------------------------------------------------------

def specificity(spec) -> float:
    """Share of the observable behaviour space this spec pins."""
    n_obs = sum(1 for c in spec["clauses"] if c[0] == "obs")
    return n_obs / M


def exposure(spec) -> float:
    """Share of this spec's constraints that mention internals."""
    total = len(spec["clauses"])
    if total == 0:
        return 0.0
    n_struct = sum(1 for c in spec["clauses"] if c[0] != "obs")
    return n_struct / total


# --------------------------------------------------------------------------
# the checker
# --------------------------------------------------------------------------

def satisfies(spec, prog) -> bool:
    """Does `prog` meet every clause of `spec`?"""
    tbl = None
    for c in spec["clauses"]:
        kind = c[0]
        if kind == "obs":
            if tbl is None:
                tbl = table(prog)
            if tbl[c[1]] != c[2]:
                return False
        elif kind == "top":
            if prog[0] != c[1]:
                return False
        elif kind == "no_op":
            if c[1] in _operators(prog):
                return False
        elif kind == "node_op":
            node = _node_at(prog, c[1])
            if node is None or node[0] != c[2]:
                return False
        elif kind == "child_op":
            node = _node_at(prog, c[1])
            if not isinstance(node, tuple) or c[2] >= len(node):
                return False
            child = node[c[2]]
            if not isinstance(child, tuple) or child[0] != c[3]:
                return False
        elif kind == "op_count_le":
            if _count_ops(prog).get(c[1], 0) > c[2]:
                return False
        elif kind == "const_present":
            if c[1] not in _consts(prog):
                return False
        elif kind == "const_absent":
            if c[1] in _consts(prog):
                return False
        elif kind == "size_le":
            if size(prog) > c[1]:
                return False
        elif kind == "depth_le":
            if depth(prog) > c[1]:
                return False
        else:
            raise ValueError(f"unknown clause kind {kind!r}")
    return True


def clause_counts(spec):
    obs = sum(1 for c in spec["clauses"] if c[0] == "obs")
    return obs, len(spec["clauses"]) - obs
