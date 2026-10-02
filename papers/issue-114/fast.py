#!/usr/bin/env python3
"""The fast evaluator for the decisive run (issue #114, Step 5).

WHY THIS FILE EXISTS
--------------------
The decisive run sweeps a grid of (s, r) cells over ~40 draws (pin-set alignments x
candidate mixes) over ~260 reference programmes, each with its own population of
mutations.  Evaluating every specification against every mutation through
`specs.satisfies` would be O(cells x draws x programmes x mutations x clauses) and is
minutes of Python.

So each clause's failure over a programme's WHOLE mutation population is computed ONCE,
as a bitmask (one bit per mutant), and a specification's rejection set is the OR of its
clauses' masks.  That is exactly equivalent to `satisfies` -- and "exactly" is a claim
this file does not get to make about itself: `smoke_results.py` control R1 re-derives the
masks through the reference route (`specs.satisfies`) and through a direct clause-by-clause
OR, and requires all three routes to agree on every (specification, mutant) pair it
samples.  A fast path whose equivalence is assumed is a fast path nobody can trust.

TWO NESTED PREFIXES, ONE OR
---------------------------
The clauses of `make_spec` are a prefix of the pin ORDER (the first k inputs of the
domain permutation) followed by a prefix of the candidate ORDER (the first b candidates
of the mix).  Both are cumulative, so each is OR-ed up once per (alignment | mix) and a
cell's mask is then a single OR of two precomputed masks.  `spec_mask` still takes k and
b from `specs.budget`, the same function `make_spec` uses, so the fast path cannot invent
a different exposure budget than the reference constructor.
"""

from __future__ import annotations

from mutations import enumerate_mutations
from oracle import classify
from specs import (budget, domain_perm, mixed_candidates, representational_candidates,
                   satisfies, exposure, exposure_plan)
from toylang import M, table


def popcount(x: int) -> int:
    return bin(x).count("1")


class Model:
    """Everything the decisive run needs about ONE reference programme."""

    def __init__(self, prog, src: str = "", tier: str = ""):
        self.prog = prog
        self.src = src
        self.tier = tier

        muts = enumerate_mutations(prog)
        rows = [(m["mutant"], classify(prog, m["mutant"])[0]) for m in muts]
        self.mutants = [r[0] for r in rows]
        self.mutant_tables = [table(m) for m in self.mutants]
        self.n_mutants = len(rows)
        self.changing_mask = 0
        self.preserving_mask = 0
        for j, (_, preserving) in enumerate(rows):
            if preserving:
                self.preserving_mask |= 1 << j
            else:
                self.changing_mask |= 1 << j
        self.n_changing = popcount(self.changing_mask)
        self.n_preserving = popcount(self.preserving_mask)

        self.ref_table = table(prog)

        # --- observational clauses: ("obs", i, ref_table[i]) -------------------------
        self.obs_masks = []
        for i in range(M):
            v = self.ref_table[i]
            mask = 0
            for j, t in enumerate(self.mutant_tables):
                if t[i] != v:
                    mask |= 1 << j
            self.obs_masks.append(mask)

        # --- representational clauses ------------------------------------------------
        self.cands = representational_candidates(prog)
        self._mask_by_clause = {c: self._cand_mask(c) for c in self.cands}
        self.B = len(self.cands)

        self._obs_prefix_cache = {}
        self._cand_prefix_cache = {}

    # -- clause-level ---------------------------------------------------------

    def _cand_mask(self, clause) -> int:
        """The mask of mutants that FAIL this representational clause.

        Decided by `satisfies` -- the reference checker -- rather than by re-implementing
        each clause kind here.  A second implementation of the clause semantics is a
        second thing to be wrong, and the bitmask is only worth having if it is the
        reference checker's own answer.
        """
        mask = 0
        spec = {"reference": self.prog, "clauses": [clause]}
        for j, mu in enumerate(self.mutants):
            if not satisfies(spec, mu):
                mask |= 1 << j
        return mask

    def mask_of(self, clause) -> int:
        if clause[0] == "obs":
            return self.obs_masks[clause[1]]
        return self._mask_by_clause[clause]

    def naive_mask(self, clauses) -> int:
        """The direct route: OR the clauses' masks one at a time."""
        mask = 0
        for c in clauses:
            mask |= self.mask_of(c)
        return mask

    # -- prefixes -------------------------------------------------------------

    def obs_prefix(self, align=None):
        """Cumulative OR of the pins IN THE PERMUTATION'S ORDER, indexed by k."""
        if align not in self._obs_prefix_cache:
            out, cur = [0], 0
            for i in domain_perm(align):
                cur |= self.obs_masks[i]
                out.append(cur)
            self._obs_prefix_cache[align] = out
        return self._obs_prefix_cache[align]

    def cand_prefix(self, mix=None):
        """Cumulative OR of the candidates in THIS MIX's order, indexed by b."""
        if mix not in self._cand_prefix_cache:
            out, cur = [0], 0
            for c in mixed_candidates(self.prog, mix):
                cur |= self._mask_by_clause[c]
                out.append(cur)
            self._cand_prefix_cache[mix] = out
        return self._cand_prefix_cache[mix]

    # -- the cell -------------------------------------------------------------

    def spec_mask(self, k: int, b: int, align=None, mix=None) -> int:
        return self.obs_prefix(align)[k] | self.cand_prefix(mix)[b]

    def cell(self, s_target: float, r_target: float, align=None, mix=None):
        """(reject_mask, k, b, r_achieved, reached) for this cell on this programme."""
        k = round(s_target * M)
        b = budget(k, r_target, self.B)
        achieved, _, reached = exposure_plan(k, b, r_target)
        return self.spec_mask(k, b, align, mix), k, b, achieved, reached


def mask_scores(mask: int, model: Model):
    """(detection, breakage) counts implied by a rejection mask, for one programme."""
    return popcount(mask & model.changing_mask), popcount(mask & model.preserving_mask)


def make_model_set(programs):
    return [Model(p["prog"], p["src"], p["tier"]) for p in programs]


def spec_exposure(spec) -> float:
    """Exposure of a spec dict, so the fast path can be compared with the constructor."""
    return exposure(spec)
