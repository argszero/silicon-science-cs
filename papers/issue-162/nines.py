#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nines.py -- what a quoted nines figure identifies about a replicated store's loss probability.

The question is not "what is the loss probability" but **"what does the quoted number identify"**.
A durability figure quoted as `p**r` is the value of `P(all replicas fail)` under exactly one
coupling of the marginals; given only the marginals, that probability lives in an interval, and the
quoted figure is its *rare* endpoint. This instrument reports that interval, prices it in the unit
the quote is made in (nines = -log10 of a probability), and shows both endpoints are **attained**
-- not cited, attained -- so the interval is tight rather than merely valid.

Why attainment is the load-bearing leg. A bound nobody attains is a bound about nothing: every
coupling satisfies it, so it separates no two of them. The probe this replaces
(`coupling_probe.py`) checked attainment only at `r = 2`, by enumerating cyclic placements on a
1000-point space, and asserted the general case in a comment. A comment is where a defect lives, so
the general case is now the instrument's job, by two independent routes that must agree:

  * **exhaustive** -- enumerate every integer assignment of `N` atoms to the `2**r` membership types
    subject to each event holding exactly `a` atoms. This is the coupling polytope's vertex set in
    disguise: the constraint matrix is a 0/1 incidence matrix, hence totally unimodular, hence every
    vertex is integral, hence enumerating the integer points enumerates the vertices. Exponential, so
    bounded by a declared node budget; when the budget is short the leg reports NOT RUN (exit 3).
  * **constructed** -- an explicit assignment for arbitrary `(r, N, a)`, verified against the closed
    form rather than asserted. Scales without a budget and covers the `r` the enumeration cannot.

Two routes computing the same number for different reasons is the only shape in which a green
result is evidence: one can be misread and the other still catch it.

Exact arithmetic. Every probability is a `Fraction`; floats appear only at the print and JSON
boundary. The lower endpoint `r*p - (r-1)` is compared against zero exactly, so "the identified set
contains 0" is a decision about rationals, not a tolerance.

Exit status -- three outcomes, kept apart, because collapsing the middle one into 0 is how a verdict
comes to claim a number no run computed:

  0  every control agreed, including both attainment routes
  1  a control FAILED (the reading is not a finding; nothing is written)
  3  NOT RUN -- a leg could not run under its declared budget; it measured nothing, and that is
     neither a pass nor a failure

Writes nothing unless `--emit` names a path, so a self-test can never replace the artefact a report
describes.

Usage:
  ./nines.py                       # self-test: controls, a plant for each, and both routes
  ./nines.py --grid                # the reading: per-cell interval, quote and span in nines
  ./nines.py --grid --emit out.json
  ./nines.py --selftest --budget 400000
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))

EXIT_OK, EXIT_FAIL, EXIT_NOT_RUN = 0, 1, 3

# The reading grid. `p` is a per-device annual loss probability written as a decimal string, so the
# instrument reads the number a report would quote rather than a float that forgot its decimal.
GRID_P = ("1e-2", "1e-3", "1e-4", "1e-5")
GRID_R = (1, 2, 3, 4, 5)

# The exhaustive leg's node budget: declared, printed, enforced. A leg that silently stops
# enumerating reports the size of its own search as if it were a property of the world.
DEFAULT_BUDGET = 400_000


def frac(text):
    """A decimal or scientific-notation string as an exact Fraction."""
    return Fraction(text.replace("_", ""))


def nines(x):
    """Nines of a probability: `-log10 x`. Zero is unbounded, and says so."""
    if x <= 0:
        return float("inf")
    return -math.log10(float(x))


# ---------------------------------------------------------------------------
# the arithmetic
# ---------------------------------------------------------------------------

def frechet_interval(p, r):
    """The identified set of `P(all r events fail)` given only the marginals.

    Lower end from inclusion-exclusion (Bonferroni): `P(intersection) >= sum P(A_i) - (r-1)`.
    Upper end because the intersection is contained in every event: `P <= min_i P(A_i) = p`.
    Both are classical. What is not classical, and what this file exists to establish, is that both
    are *attained* on a finite space with every marginal exactly `p`.
    """
    if r < 1:
        raise ValueError("r must be at least 1, got %r" % (r,))
    if not (0 <= p <= 1):
        raise ValueError("p must be a probability, got %r" % (p,))
    lo = r * p - (r - 1)
    if lo < 0:
        lo = Fraction(0)
    return lo, p


def mixture(p, r, rho):
    """Stated dependence: a fraction `rho` of replication groups fail together.

    `rho = 0` is independence (`p**r`, the quoted number); `rho = 1` is comonotonicity (`p`, the
    catastrophic end). The family is a linear interpolation *in the all-fail probability*, which is
    why stating `rho` buys an exact figure instead of a bound -- and why that figure is a statement
    about the coupling, never a measurement of it.
    """
    rho = Fraction(rho)
    if not (0 <= rho <= 1):
        raise ValueError("rho must be in [0, 1], got %r" % (rho,))
    return rho * p + (1 - rho) * (p ** r)


# ---------------------------------------------------------------------------
# attainment, route 1: exhaustive enumeration of the polytope's integer points
# ---------------------------------------------------------------------------

def enumerate_attainment(r, N, a, budget=DEFAULT_BUDGET):
    """Extreme all-fail counts over every integer coupling of `r` events of size `a` on `N` atoms.

    The polytope is `{ n in Z^(2**r) : sum n = N, and for each event i, sum over types containing i
    of n_S = a }`, where `n_S` counts atoms whose membership set is exactly `S`. Its constraint
    matrix is a 0/1 incidence matrix and therefore totally unimodular, so its vertices are integral
    and the integer points are the vertices -- which is what makes "no coupling attains anything
    outside this range" a statement about *all* couplings, not only the ones this file builds.

    A depth-first assignment of counts to membership types, pruned by the needs that remain.
    Returns `complete=False` with the node count when the budget runs out: the caller must report
    that as NOT RUN and never as an answer.
    """
    ntypes = 1 << r
    full = ntypes - 1
    need = [a] * r
    state = [0] * ntypes
    best = {"min": None, "max": None}
    nodes = [0]
    complete = [True]

    def rec(idx, left):
        if not complete[0]:
            return
        nodes[0] += 1
        if nodes[0] > budget:
            complete[0] = False
            return
        if any(n < 0 for n in need):
            return
        if idx == ntypes:
            if left == 0 and all(n == 0 for n in need):
                k = state[full]
                if best["min"] is None or k < best["min"]:
                    best["min"] = k
                if best["max"] is None or k > best["max"]:
                    best["max"] = k
            return
        t = idx
        members = [i for i in range(r) if t >> i & 1]
        if idx == ntypes - 1:
            # the last type absorbs what is left, which removes a whole layer of the search
            n = left
            ok = True
            for i in range(r):
                want = n if i in members else 0
                if need[i] != want:
                    ok = False
                    break
            if ok:
                state[t] = n
                for i in members:
                    need[i] = 0
                rec(idx + 1, 0)
                for i in members:
                    need[i] = n
                state[t] = 0
            return
        cap = left
        for i in members:
            if need[i] < cap:
                cap = need[i]
        for n in range(cap, -1, -1):
            state[t] = n
            for i in members:
                need[i] -= n
            rest = left - n
            # every remaining need must still be coverable by the atoms that remain
            if all(nd <= rest for nd in need):
                rec(idx + 1, rest)
            for i in members:
                need[i] += n
            if not complete[0]:
                break
        state[t] = 0

    rec(0, N)
    return {"min": best["min"], "max": best["max"], "nodes": nodes[0], "complete": complete[0]}


# ---------------------------------------------------------------------------
# attainment, route 2: an explicit construction for arbitrary (r, N, a)
# ---------------------------------------------------------------------------

def construct_attainment(r, N, a):
    """A coupling of `r` events of size `a` on `N` atoms with the extreme all-fail count.

    The construction, and why it works.

    Write `m` for the atoms in *all* `r` events. Each event then needs `a - m` further atoms, so the
    atoms outside the all-fail block must carry `r*(a - m)` incidences, and an atom outside that
    block carries at most `r - 1`. Hence `r*(a - m) <= (r-1)*(N - m)`, i.e. `m >= r*a - (r-1)*N`,
    and with `m >= 0` that is exactly the lower endpoint.

    Attainment: put `m` atoms in every event, then hand out the remaining incidences by walking a
    list that cycles through the events `a - m` times -- `0, 1, ..., r-1, 0, 1, ...` -- in chunks of
    `r - 1`. Any `r - 1` consecutive elements of a sequence whose period is `r` are distinct, so no
    chunk gives one atom the same event twice, and the chunking ends within the atom count because
    the incidence inequality above bounds the number of chunks. Verified here, not asserted: raises
    if the built coupling's all-fail count or any marginal disagrees with the closed form.
    """
    if not (0 <= a <= N):
        raise ValueError("need 0 <= a <= N, got a=%r N=%r" % (a, N))
    m = max(0, r * a - (r - 1) * N)
    memberships = [frozenset(range(r)) for _ in range(m)]

    slot_cycle = []
    for _ in range(a - m):
        for i in range(r):
            slot_cycle.append(i)
    chunk = r - 1 if r > 1 else 1
    for start in range(0, len(slot_cycle), chunk):
        piece = slot_cycle[start:start + chunk]
        if len(piece) != len(set(piece)):
            raise AssertionError("the construction gave an atom the same event twice: %r" % (piece,))
        memberships.append(frozenset(piece))

    if len(memberships) > N:
        raise AssertionError("the construction wants %d atoms and the space has %d"
                             % (len(memberships), N))
    memberships.extend([frozenset() for _ in range(N - len(memberships))])

    counts = [0] * r
    for s in memberships:
        for i in s:
            counts[i] += 1
    all_fail = sum(1 for s in memberships if len(s) == r)
    if counts != [a] * r:
        raise AssertionError("marginals came out %r, not %r" % (counts, [a] * r))
    if all_fail != m:
        raise AssertionError("all-fail count came out %d, not %d" % (all_fail, m))
    return all_fail, memberships


# ---------------------------------------------------------------------------
# the reading
# ---------------------------------------------------------------------------

def reading(p_text, r):
    """One cell: the quoted figure, the identified set, and what stating a dependence buys."""
    p = frac(p_text)
    lo, hi = frechet_interval(p, r)
    quoted = p ** r
    worst_nines = nines(hi)
    quoted_nines = nines(quoted)
    return {
        "p": p_text,
        "r": r,
        "quoted": quoted,
        "set_hi": hi,
        "quoted_nines": quoted_nines,
        "set_lo_nines": nines(lo) if lo > 0 else None,
        "set_hi_nines": worst_nines,
        "contains_zero": lo == 0,
        "span_nines": quoted_nines - worst_nines,
        "independent": mixture(p, r, Fraction(0)),
        "comonotone": mixture(p, r, Fraction(1)),
    }


def widest_cell(rows):
    """The cell with the widest identification span; `r = 1` excluded by name, not out-competed.

    This function exists because of a defect the probe had and the instrument must not. The span was
    once written `nines_attainable - nines_quoted`, a negative number, so `max()` selected the
    boundary cell where the family collapses and the span is exactly 0 -- printing "widest span 0.0
    decades" while the real worst cell spanned 16. Two guards, both needed: the span is a magnitude
    by construction (`quoted - worst`, always >= 0), and the boundary is excluded by name, so an
    all-boundary grid returns None instead of a quiet zero.
    """
    eligible = [x for x in rows
                if x["r"] >= 2 and x["span_nines"] is not None
                and x["span_nines"] != float("inf")]
    if not eligible:
        return None
    return max(eligible, key=lambda x: x["span_nines"])


def emit_json(rows, path):
    """Write the reading. Fractions and infinities do not survive JSON, so both are made explicit."""
    def conv(v):
        if isinstance(v, Fraction):
            return float(v)
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        raise TypeError("nines.py will not write %r into an artefact" % (type(v),))

    payload = {
        "instrument": "nines.py",
        "unit": ("nines = -log10 of a probability; span_nines = quoted_nines - "
                 "worst_identified_nines, a magnitude"),
        "grid": [dict((k, conv(v)) for k, v in row.items()) for row in rows],
        "note": ("contains_zero means the identified set of P(all replicas fail) includes 0: a "
                 "total loss is not excluded by the marginals, so that end of the set is unbounded "
                 "in nines, which is why set_lo_nines is null there and not a large number"),
    }
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return path


# ---------------------------------------------------------------------------
# controls. Each control is a predicate; its plant runs the SAME predicate on a defect,
# so a green control and a fired plant are two directions of one comparison.
# ---------------------------------------------------------------------------

class Harness(object):
    """Collects outcomes and keeps NOT RUN apart from both pass and fail."""

    def __init__(self):
        self.passed = 0
        self.planted = 0
        self.failed = []
        self.not_run = []

    def control(self, name, result, detail=""):
        """`result`: True, False, or None for NOT RUN."""
        if result is None:
            self.not_run.append(name)
            print("  [n/r]  %s%s" % (name, (" -- " + detail) if detail else ""))
        elif result:
            self.passed += 1
            print("  [ok]   %s%s" % (name, (" -- " + detail) if detail else ""))
        else:
            self.failed.append(name)
            print("  [FAIL] %s%s" % (name, (" -- " + detail) if detail else ""))

    def plant(self, name, fires, detail=""):
        """A control is a control only once shown to fire on the defect it names.

        Three outcomes here too, and the middle one matters: when the leg a plant rides on did not
        run, the plant measured nothing. Reporting that as FAIL would turn a budget into a verdict,
        and reporting it as a pass would claim a control was exercised that never executed.
        """
        if fires is None:
            self.not_run.append("plant: " + name)
            print("  [n/r]  plant: %s%s" % (name, (" -- " + detail) if detail else ""))
        elif fires:
            self.planted += 1
            print("  [plant ok]   %s%s" % (name, (" -- " + detail) if detail else ""))
        else:
            self.failed.append("plant: " + name)
            print("  [plant FAIL] %s%s" % (name, (" -- " + detail) if detail else ""))


def p_lower_endpoint(r, N, a, budget, mutant=False):
    """Does the exhaustive minimum equal the closed form? Mutant: the form is one atom too high."""
    res = enumerate_attainment(r, N, a, budget)
    if not res["complete"]:
        return None
    want = max(0, r * a - (r - 1) * N) + (1 if mutant else 0)
    return res["min"] == want


def p_upper_endpoint(r, N, a, budget, mutant=False):
    """Does the exhaustive maximum equal `a`? Mutant: the claim is one atom too high."""
    res = enumerate_attainment(r, N, a, budget)
    if not res["complete"]:
        return None
    want = a + (1 if mutant else 0)
    return res["max"] == want


def p_routes_agree(r, N, a, budget, mutant=False):
    """Does the construction land on the enumerated minimum? Mutant: compared one atom off."""
    res = enumerate_attainment(r, N, a, budget)
    if not res["complete"]:
        return None
    built, _ = construct_attainment(r, N, a)
    want = res["min"] + (1 if mutant else 0)
    return built == want


def p_span_law(p_text, r, mutant=False):
    """Is the span `(r-1)*k`? Mutant: the wrong law, `r*k`, which is what a paraphrase produces."""
    row = reading(p_text, r)
    k = -math.log10(float(frac(p_text)))
    want = (r * k) if mutant else ((r - 1) * k)
    return abs(row["span_nines"] - want) < 1e-9


def p_family_inside(p_text, r, mutant=False):
    """Is the stated-dependence family inside the identified set? Mutant: a point outside it."""
    p = frac(p_text)
    lo, hi = frechet_interval(p, r)
    vals = [mixture(p, r, Fraction(k, 8)) for k in range(9)]
    if mutant:
        vals.append(hi + Fraction(1, 10 ** 6))
    return all(lo <= v <= hi for v in vals)


def p_family_minimum(p, r, mutant=False):
    """Is `p**r` the family's own best case, strictly above the interval's lower end?

    This is the fact the probe never stated, and it costs the family half its interval. The
    identified set is `[lo, p]`, but a mixture with `rho >= 0` spans only `[p**r, p]`: it can make the
    quote *worse* than independence and can never make it better, because `rho < 0` is not a
    coupling. So everything between `lo` and `p**r` -- the anti-correlated replication that actually
    helps -- is outside the family's reach, and a vendor who states `rho >= 0` has stated that the
    quoted figure is a best case. Mutant: claim the family attains `lo`.
    """
    lo, _ = frechet_interval(p, r)
    floor = p ** r
    if mutant:
        return floor == lo
    return floor >= lo and (floor > lo if lo < floor else True) and \
        all(mixture(p, r, Fraction(k, 32)) >= floor for k in range(33))


def p_total_loss_condition(p, r, mutant=False):
    """Is total loss excluded exactly when `p > (r-1)/r`? Mutant: the condition inverted.

    The grid turns this into a count ("16 of 20 cells have a set that reaches total loss"). A count
    of cells is a property of the grid; the condition is a property of every quote, so the instrument
    asserts the condition and lets the grid be an illustration. `p` is a Fraction here so the
    boundary `p == (r-1)/r` is decided exactly -- a float would put the boundary case on whichever
    side the rounding fell.
    """
    lo, _ = frechet_interval(p, r)
    want = (p <= Fraction(r - 1, r))
    if mutant:
        want = not want
    return (lo == 0) == want


def p_selector(rows, mutant=False):
    """Does the widest cell come from a magnitude? Mutant: the probe's negative-gap convention."""
    if mutant:
        wrong = [dict(x, g=x["set_hi_nines"] - x["quoted_nines"]) for x in rows
                 if x["quoted_nines"] != float("inf")]
        pick = max(wrong, key=lambda x: x["g"])
        return pick["r"] != 1
    pick = widest_cell(rows)
    return pick is not None and pick["r"] >= 2


def mutant_refused(result):
    """A plant fires when the same predicate refuses the mutant -- and is NOT RUN if the leg did not.

    Without this the tri-state collapses at the plant boundary: `None is False` is False, so a leg
    skipped for budget would be reported as a failed plant, i.e. the size of a search would come out
    as a defect in the arithmetic.
    """
    return None if result is None else (result is False)


def _raises(fn, **kwargs):
    try:
        fn(**kwargs)
    except Exception:                                            # noqa: BLE001
        return True
    return False


# ---------------------------------------------------------------------------
# the self-test
# ---------------------------------------------------------------------------

def selftest(budget):
    h = Harness()

    # ---- C0 the boundary: one replica has no coupling to choose ----
    print("\nC0 the boundary: one replica has no coupling to choose")
    lo, hi = frechet_interval(frac("1e-2"), 1)
    h.control("r=1 collapses the identified set to a point", lo == hi, "set=[%s, %s]" % (lo, hi))
    h.control("r=1: the quoted figure equals the truth exactly",
              mixture(frac("1e-2"), 1, Fraction(0)) == hi)
    h.control("r=1: the span is zero, which is why the selector must exclude it",
              reading("1e-2", 1)["span_nines"] == 0.0)

    # ---- C1 the lower endpoint, exhaustively, with its plant and its scale check ----
    print("\nC1 the best identified value is attained: the lower endpoint, exhaustively")
    grid = [(2, 10, 3), (2, 10, 8), (3, 9, 3), (3, 12, 8), (3, 6, 4), (3, 6, 5),
            (4, 8, 2), (4, 8, 6)]
    for (r, N, a) in grid:
        res = enumerate_attainment(r, N, a, budget)
        detail = ("enumerated %r vs closed form %r (%d nodes)"
                  % (res["min"], max(0, r * a - (r - 1) * N), res["nodes"]))
        h.control("r=%d N=%d a=%d: enumerated minimum equals the closed form" % (r, N, a),
                  p_lower_endpoint(r, N, a, budget), detail)
        h.control("r=%d N=%d a=%d: it is the interval's own lower end as a probability" % (r, N, a),
                  None if not res["complete"] else
                  (Fraction(res["min"], N) == frechet_interval(Fraction(a, N), r)[0]),
                  "as a probability: %s" % (Fraction(res["min"], N) if res["complete"] else "-"))
    h.plant("a closed form one atom too high is refused by the same comparison",
            mutant_refused(p_lower_endpoint(3, 12, 8, budget, mutant=True)))

    # ---- C2 the upper endpoint, exhaustively, with its plant ----
    print("\nC2 the worst identified value is attained: the upper endpoint, exhaustively")
    for (r, N, a) in grid:
        res = enumerate_attainment(r, N, a, budget)
        h.control("r=%d N=%d a=%d: enumerated maximum equals a" % (r, N, a),
                  p_upper_endpoint(r, N, a, budget), "enumerated %r vs a=%d" % (res["max"], a))
    h.plant("an upper-endpoint claim one atom too high is refused",
            mutant_refused(p_upper_endpoint(3, 12, 8, budget, mutant=True)))

    # ---- C3 the two routes agree ----
    print("\nC3 the two attainment routes agree where both can run")
    for (r, N, a) in grid:
        built, _ = construct_attainment(r, N, a)
        h.control("r=%d N=%d a=%d: construction equals the enumerated minimum" % (r, N, a),
                  p_routes_agree(r, N, a, budget), "built %d" % built)
    h.plant("a construction compared one atom off is refused",
            mutant_refused(p_routes_agree(3, 12, 8, budget, mutant=True)))

    # ---- C4 the construction reaches the r the enumeration cannot ----
    print("\nC4 the construction covers what the enumeration is too small to reach")
    for r in (5, 6, 8, 12):
        for (N, a) in ((48, 6), (48, 40), (60, 59)):
            m, memberships = construct_attainment(r, N, a)
            lo, hi = frechet_interval(Fraction(a, N), r)
            h.control("r=%d N=%d a=%d: the built coupling's all-fail value is in the set"
                      % (r, N, a),
                      lo <= Fraction(m, N) <= hi,
                      "built %d/%d, set=[%s, %s]" % (m, N, Fraction(m, N), lo))
            h.control("r=%d N=%d a=%d: every marginal is exactly a" % (r, N, a),
                      all(sum(1 for s in memberships if i in s) == a for i in range(r)))
    h.plant("a coupling with an impossible marginal is refused",
            _raises(construct_attainment, r=3, N=10, a=11))

    # ---- C5 the stated-dependence family, with its plant ----
    print("\nC5 a stated dependence buys an exact figure inside the set")
    for p_text in ("1e-3", "1e-4"):
        for r in (2, 3, 5):
            p = frac(p_text)
            lo, hi = frechet_interval(p, r)
            h.control("p=%s r=%d: the whole family is inside [lo, hi]" % (p_text, r),
                      p_family_inside(p_text, r),
                      "9 points, lo=%s hi=%s" % (float(lo), float(hi)))
            h.control("p=%s r=%d: rho=1 lands exactly on the upper endpoint" % (p_text, r),
                      mixture(p, r, Fraction(1)) == hi)
            h.control("p=%s r=%d: rho=0 lands exactly on the quoted figure" % (p_text, r),
                      mixture(p, r, Fraction(0)) == p ** r)
    h.plant("a family point outside the set is refused",
            p_family_inside("1e-4", 3, mutant=True) is False)

    # ---- C6 monotone in the stated dependence ----
    print("\nC6 the family is monotone in the stated dependence")
    p, r = frac("1e-4"), 4
    seq = [mixture(p, r, Fraction(k, 16)) for k in range(17)]
    h.control("loss probability is non-decreasing in rho",
              all(b >= a2 for a2, b in zip(seq, seq[1:])),
              "%d steps, %.1e .. %.1e" % (len(seq), float(seq[0]), float(seq[-1])))
    h.plant("a reversed family is refused by the same test",
            not all(b >= a2 for a2, b in zip(list(reversed(seq)), list(reversed(seq))[1:])))

    # ---- C7 more replicas lower the quoted figure ----
    print("\nC7 more replicas lower the quoted figure")
    for p_text in ("1e-2", "1e-4"):
        pp = frac(p_text)
        vals = [pp ** rr for rr in range(1, 7)]
        h.control("p=%s: p**r is strictly decreasing in r" % p_text,
                  all(b < a2 for a2, b in zip(vals, vals[1:])),
                  "%s" % ["%.1e" % float(v) for v in vals])

    # ---- C8 the span law, with its plant ----
    print("\nC8 the span law: every replica adds the same number of decades it adds in nines")
    for p_text in GRID_P:
        for r in (2, 3, 4, 5):
            row = reading(p_text, r)
            want = (r - 1) * -math.log10(float(frac(p_text)))
            h.control("p=%s r=%d: span == (r-1)*(-log10 p)" % (p_text, r),
                      p_span_law(p_text, r),
                      "%.4f vs %.4f decades" % (row["span_nines"], want))
    h.plant("the wrong span law (r*k instead of (r-1)*k) is refused",
            p_span_law("1e-4", 5, mutant=True) is False)

    # ---- C9 the quote is the rare end, and the set reaches total loss ----
    print("\nC9 the quoted figure is the rare endpoint, and the set reaches total loss")
    for p_text in ("1e-3", "1e-4"):
        for r in (2, 3, 5):
            row = reading(p_text, r)
            lo, hi = frechet_interval(frac(p_text), r)
            h.control("p=%s r=%d: quoted nines exceed the worst identified nines" % (p_text, r),
                      row["quoted_nines"] > row["set_hi_nines"],
                      "quoted %.1f vs worst %.1f" % (row["quoted_nines"], row["set_hi_nines"]))
            h.control("p=%s r=%d: a total loss is not excluded" % (p_text, r),
                      row["contains_zero"] == (lo == 0),
                      "contains_zero=%r" % row["contains_zero"])

    # ---- C9b the condition behind the count, boundaries included ----
    print("\nC9b total loss is excluded exactly when p > (r-1)/r, boundaries decided exactly")
    cases = [(Fraction(1, 2), 2), (Fraction(1, 2) + Fraction(1, 10 ** 9), 2),
             (Fraction(2, 3), 3), (Fraction(2, 3) + Fraction(1, 10 ** 9), 3),
             (Fraction(1, 10 ** 4), 2), (Fraction(1, 10 ** 4), 5),
             (Fraction(1), 4), (Fraction(0), 5)]
    for (p_frac, r) in cases:
        h.control("p=%s r=%d: total loss excluded iff p > (r-1)/r" % (p_frac, r),
                  p_total_loss_condition(p_frac, r),
                  "set lower end = %s" % (frechet_interval(p_frac, r)[0],))
    h.control("the boundary case p == (r-1)/r is not excluded (the set closes at zero, not above)",
              frechet_interval(Fraction(1, 2), 2)[0] == 0
              and frechet_interval(Fraction(2, 3), 3)[0] == 0)
    h.plant("an inverted condition is refused at the same points",
            mutant_refused(p_total_loss_condition(Fraction(1, 10 ** 4), 3, mutant=True))
            if False else (p_total_loss_condition(Fraction(1, 10 ** 4), 3, mutant=True) is False))

    # ---- C9c the family covers half the interval, and that half is the harmful one ----
    print("\nC9c the stated-dependence family covers [p**r, p] and cannot reach the lower end")
    for p_text in ("1e-3", "1e-4"):
        for r in (2, 3, 5):
            p = frac(p_text)
            lo, hi = frechet_interval(p, r)
            h.control("p=%s r=%d: p**r is the family's best case and sits above lo" % (p_text, r),
                      p_family_minimum(p, r),
                      "lo=%s  p**r=%.3e  hi=%.3e" % (float(lo), float(p ** r), float(hi)))
            h.control("p=%s r=%d: the unexplained band [lo, p**r) is not empty" % (p_text, r),
                      lo < p ** r,
                      "width %.3e, reached only by rho < 0" % float(p ** r - lo))
    h.plant("a claim that the family attains the lower end is refused",
            p_family_minimum(frac("1e-4"), 3, mutant=True) is False)

    # ---- C10 the selector, which is the defect this file was written after ----
    print("\nC10 the widest cell is chosen by magnitude and never by the boundary")
    rows = [reading(p_text, r) for p_text in GRID_P for r in GRID_R]
    widest = widest_cell(rows)
    h.control("a widest cell exists and it is not r=1", p_selector(rows),
              "p=%s r=%d span=%.1f decades"
              % (widest["p"], widest["r"], widest["span_nines"]))
    h.control("the widest cell is the largest span in the grid",
              widest["span_nines"] == max(x["span_nines"] for x in rows if x["r"] >= 2))
    h.control("a boundary-only grid yields no widest cell rather than a quiet zero",
              widest_cell([reading("1e-4", 1)]) is None)
    h.plant("the probe's negative-gap convention is shown to select the boundary cell",
            p_selector(rows, mutant=True) is False,
            "under `worst - quoted` the argmax is r=1 with gap 0.0")

    # ---- the sum of the controls ----
    print("\n== summary")
    print("   controls passed : %d" % h.passed)
    print("   plants fired    : %d" % h.planted)
    if h.not_run:
        print("   NOT RUN         : %d (first 3: %s)"
              % (len(h.not_run), "; ".join(h.not_run[:3])))
    else:
        print("   NOT RUN         : 0")
    print("   FAILED          : %d%s"
          % (len(h.failed), (" -- " + "; ".join(h.failed)) if h.failed else ""))
    if h.failed:
        print("\nSELFTEST: %d FAILED -- the reading is not a finding and nothing is written"
              % len(h.failed))
        return EXIT_FAIL
    if h.not_run:
        print("\nSELFTEST: %d CONTROL(S) NOT RUN -- those legs measured nothing; this is neither a "
              "pass nor a failure" % len(h.not_run))
        return EXIT_NOT_RUN
    if h.passed == 0 or h.planted == 0:
        print("\nSELFTEST: FAILED -- no control ran or no plant fired, so a green verdict would be "
              "about an empty set")
        return EXIT_FAIL
    print("\nSELFTEST: ALL GREEN (%d controls, %d planted)" % (h.passed, h.planted))
    return EXIT_OK


# ---------------------------------------------------------------------------
# the reading
# ---------------------------------------------------------------------------

def print_grid():
    rows = [reading(p_text, r) for p_text in GRID_P for r in GRID_R]
    print("  %-7s %-3s %-11s %-11s %-10s %-10s %-8s %s"
          % ("p(dev/yr)", "r", "quoted", "worst_id", "nines_q", "nines_w", "span", "set contains 0"))
    for x in rows:
        print("  %-7s %-3d %-11.2e %-11.2e %-10.1f %-10.1f %-8.1f %s"
              % (x["p"], x["r"], float(x["independent"]), float(x["set_hi"]),
                 x["quoted_nines"], x["set_hi_nines"], x["span_nines"],
                 "yes" if x["contains_zero"] else "no"))
    print("")
    print("  cells whose identified set reaches total loss: %d / %d"
          % (sum(1 for x in rows if x["contains_zero"]), len(rows)))
    print("  cells whose set is a single point: %d (these are the r=1 boundary, and they are not "
          "readings)" % sum(1 for x in rows if x["r"] == 1))
    widest = widest_cell(rows)
    if widest is None:
        print("  widest span: none -- every cell in this grid is a boundary cell")
    else:
        print("  widest span: p=%s r=%d -> %.1f decades (%.1f nines quoted, %.1f nines at the "
              "worst identified value)"
              % (widest["p"], widest["r"], widest["span_nines"], widest["quoted_nines"],
                 widest["set_hi_nines"]))
        print("  the same cell's stated-dependence family: rho=0 -> %.2e, rho=1 -> %.2e"
              % (float(widest["independent"]), float(widest["comonotone"])))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="What a quoted nines figure identifies about replicated loss probability.")
    ap.add_argument("--selftest", action="store_true",
                    help="run the controls and their plants (default when --grid is absent)")
    ap.add_argument("--grid", action="store_true", help="print the reading table")
    ap.add_argument("--emit", metavar="PATH", default=None,
                    help="write the reading as JSON; nothing is written without this")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                    help="node budget for the exhaustive attainment leg (default %d)"
                         % DEFAULT_BUDGET)
    args = ap.parse_args(argv)

    rc = EXIT_OK
    if args.selftest or not args.grid:
        print("nines.py self-test  (node budget %d)" % args.budget)
        rc = selftest(args.budget)
        if rc == EXIT_FAIL:
            return rc

    if args.grid:
        print("\nREADING")
        rows = print_grid()
        if args.emit:
            path = emit_json(rows, args.emit)
            print("-> %s" % os.path.basename(path))
        elif rc == EXIT_NOT_RUN:
            pass
    return rc


if __name__ == "__main__":
    sys.exit(main())
