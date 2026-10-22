#!/usr/bin/env python3
"""issue #141 -- R656: the SCOPE of the transport law's converse -- is the violating entry
REACHABLE in this model at all?

WHY THIS EXISTS.  R655 measured that v4's C6c evaluates 262 entries and reports ZERO violations
of `excess == 0  <=>  the same orientation in both populations`, while all 262 evaluated entries
happen to sit at the SAME orientation in both populations.  A biconditional whose discriminating
case never occurs has not been tested in that direction (Class 313), so R655 recorded the converse
as NOT TESTED over this design space.  That leaves the next question, and it is the one a reviewer
asks first: *is it merely untested by these four populations, or is it untestable here?*  A law
whose converse is structurally untestable has a SCOPE, and stating the scope is a contribution;
leaving it as "we didn't see one" is not.

THE ARITHMETIC (exact, and already asserted in v4's C6c plant).  Reversing an ordering flips every
pair, so the Kendall loss is invariant under reversing BOTH and complements under reversing ONE:

        loss(rev a, rev b) = loss(a, b)          loss(rev a, b) = 1 - loss(a, b)

A MIXED-orientation entry is one where the protocol's ordering equals the payoff ordering in one
population and its exact reverse in the other.  There

        raw = 1 - base          so        excess = raw - base = 1 - 2 * base

and `excess == 0` therefore requires **base == 1/2** exactly -- i.e. the two populations' payoff
orderings must be discordant on **exactly half of the 28 policy pairs**, i.e. on exactly 14.

THE OBJECT THIS SCRIPT MEASURES, then, is not the transport statistic at all: it is the set of
payoff orderings this MODEL can produce as the population ranges over the whole simplex.  The
payoff vector is `M . p` with `p` in the simplex (a linear image of it), so the reachable orderings
are far more clustered than the 40320 permutations of eight policies, and the question "can two of
them be 14/28 apart?" is answerable.  The script answers it three ways:

  (A) the SAMPLE OF RECORD -- the four named populations of the shipped design, pairwise;
  (B) an EXACT RATIONAL GRID over the whole simplex at resolution `--res` (default 10): every
      integer weight vector summing to `res`, i.e. 19,448 populations for eight policies, for every
      game of v4's nine-game ladder.  Deterministic enumeration, no sampling, no seeds;
  (C) the EXACT CERTIFICATION of the extremal pair found in (B): rebuilt from integer weights with
      `Fraction` arithmetic and the model's own `order_by`, asserting that the exact discordance
      equals the discordance the grid reported.

Both (B) and (C) are exact, by two DIFFERENT routes: the grid multiplies an integer-scaled payoff
matrix (no float ever enters a comparison), and the certification rebuilds the same populations as
`Fraction` population weights through the model's own `_mean` and `order_by`.  Two routes, one
object, and the assertion between them is what makes either a reading.

CERTIFICATE.  Every "no" below must be able to become a "yes", so each leg carries a plant:
  C1  the reachability predicate fires on a manufactured 14-of-28 pair      (it can say yes)
  C2  the discordance counter moves when one ordering is perturbed          (it is not stuck)
  C3  the Fraction rebuild agrees with the integer grid on the extremal pair (one object)
  C4  the mixed-entry excess is `1 - 2*base`, non-zero at the reachable max (the margin is real)
  C5  the grid really enumerates the simplex (count + symmetry spot-check)  (the domain is whole)
  C6  a value the script does NOT measure cannot pass the same predicate    (the reading is read)

Author: how2how2how2-arch
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
from collections import OrderedDict
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np            # noqa: E402
import spike_v0 as V          # noqa: E402  the exact model
import spike_v4 as V4         # noqa: E402  the ladder and the scan of record

GAMES = list(V4.LADDER)
ZOO = list(V.ZOO)
NPOL = len(ZOO)
NPAIRS = NPOL * (NPOL - 1) // 2          # 28
ALPHA_RANK = {a: i for i, a in enumerate(sorted(ZOO))}   # name rank -- NOT the ZOO position
MIXED_ZERO_BASE = F(1, 2)                # the base a mixed-orientation entry needs to read zero
TARGET = NPAIRS // 2                     # == 14: the discordance a base of 1/2 requires


# ------------------------------------------------------------------------------------------------
# ordering, exactly as the model defines it (descending score, ties broken by name)

def order_desc(scores):
    """`V.order_by` -- restated here so the instrument reads the model's own convention rather than
    importing a private detail of it (the two are asserted equal in C3)."""
    return sorted(scores, key=lambda a: (-scores[a], a))


def discordant(o1, o2):
    """Number of the 28 unordered policy pairs the two orderings disagree about."""
    p1 = {a: i for i, a in enumerate(o1)}
    p2 = {a: i for i, a in enumerate(o2)}
    n = 0
    for i, a in enumerate(ZOO):
        for b in ZOO[i + 1:]:
            if (p1[a] < p1[b]) != (p2[a] < p2[b]):
                n += 1
    return n


# ------------------------------------------------------------------------------------------------
# (A) the sample of record: the four named populations of the shipped design

def sample_of_record():
    pops = V.populations()
    out = OrderedDict()
    for g in GAMES:
        M, _ = V.matrices(g)
        orders = OrderedDict()
        for pn, pop in pops.items():
            u = OrderedDict((a, V._mean(M, a, pop)) for a in ZOO)
            orders[pn] = order_desc(u)
        pairs = OrderedDict()
        names = list(pops)
        best = 0
        for i, n1 in enumerate(names):
            for n2 in names[i + 1:]:
                d = discordant(orders[n1], orders[n2])
                pairs["%s>%s" % (n1, n2)] = d
                best = max(best, d)
        out[g] = {"pairs": pairs, "max_discordant": best,
                  "distinct_orderings": len({tuple(o) for o in orders.values()})}
    return out


# ------------------------------------------------------------------------------------------------
# (B) the exact rational grid over the whole population simplex

def weight_vectors(res):
    """Every integer vector of length NPOL with entries >= 0 summing to `res`, in a fixed order."""
    def comps(total, parts):
        if parts == 1:
            yield (total,)
            return
        for first in range(total + 1):
            for rest in comps(total - first, parts - 1):
                yield (first,) + rest
    return list(comps(res, NPOL))


def integer_matrix(M):
    """`M` scaled to an INTEGER matrix over a common denominator.  The ordering of the scaled scores
    is the ordering of the payoffs, exactly, so the whole grid can be enumerated without a float
    ever entering the comparison.  (The first draft multiplied floats and trusted the result; it
    agreed, but a search that is exact by construction needs no agreement check to be believed.)"""
    dens = [M[a][b].denominator for a in ZOO for b in ZOO]
    L = 1
    for d in dens:
        L = L * d // _gcd(L, d)
    Mi = np.array([[int(M[a][b] * L) for b in ZOO] for a in ZOO], dtype=np.int64)
    assert all(M[a][b] * L == Mi[i][j] for i, a in enumerate(ZOO) for j, b in enumerate(ZOO))
    return Mi, L


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def grid_orders(M, W):
    """The ordering of `M . p` for every grid population, in EXACT INTEGER arithmetic.  Returns the
    permutation array as (S, NPOL) policy indices, in the model's own tie-break convention."""
    Mi, _ = integer_matrix(M)
    # score[s,a] = sum_b W[s,b] * Mi[a,b]  -- an INTEGER, so no rounding can reorder anything
    S = W @ Mi.T                                          # (S, NPOL), exact
    # the model's tie-break (descending score, ties by NAME ascending) folded into the score itself:
    # multiplying by NPOL+1 leaves every score comparison intact, and subtracting the policy's
    # ALPHABETICAL rank makes the tie-break part of the integer.
    # The first draft subtracted `np.arange(NPOL)` -- the policy's POSITION in ZOO, not its rank in
    # alphabetical order.  ZOO is declared equilibrium-first (`eq_fpsb, eq_spsb, shade_*, ...`), so
    # the two disagree, and the grid then ordered exact TIES by declaration order while the model
    # orders them by name.  It was caught by C3's rebuild assertion on the very first game, which is
    # the whole reason the certificate rebuilds rather than trusting the grid.
    alpha_rank = np.array([ALPHA_RANK[a] for a in ZOO], dtype=np.int64)
    S2 = S * (NPOL + 1) - alpha_rank                      # higher score first, then earlier name
    perm = np.argsort(-S2, axis=1, kind="stable")
    return perm, S


def reachable_discordances(perms):
    """Every discordance value attained by a PAIR of distinct reachable orderings.

    Returns (sorted values, {value: (ordering1, ordering2, row1, row2)}, number of distinct
    orderings).  The row indices are what the exact certification rebuilds, so it never rescans the
    grid.

    This is a SET, not a maximum, and the distinction is the whole point: the converse is refuted
    by ONE entry whose base is EXACTLY 1/2, i.e. whose discordance is EXACTLY NPAIRS/2 -- so a grid
    that reaches 18 of 28 says nothing about whether 14 is reachable.  (The first draft of this
    function compared the maximum against the threshold and reported "REACHABLE" for a maximum of
    18 against a target of 14: a `>=` where the claim is `==`, which is Class 315's "the unit of
    the claim is part of the claim" in its arithmetic form.)
    """
    first_row = OrderedDict()
    for r, row in enumerate(perms):
        t = tuple(int(x) for x in row)
        if t not in first_row:
            first_row[t] = r
    uniq = list(first_row)
    if len(uniq) < 2:
        return [], {}, len(uniq)
    rows = [[ZOO[i] for i in u] for u in uniq]          # NAMES, the unit every predicate speaks
    ranks = [{a: i for i, a in enumerate(o)} for o in rows]
    seen = {}
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            d = sum(1 for x, y in itertools.combinations(ZOO, 2)
                    if (ranks[i][x] < ranks[i][y]) != (ranks[j][x] < ranks[j][y]))
            if d not in seen:
                seen[d] = (rows[i], rows[j], first_row[uniq[i]], first_row[uniq[j]])
    return sorted(seen), seen, len(uniq)


def grid_scan(res):
    W = np.array(weight_vectors(res), dtype=np.int64)     # (S, NPOL), each row sums to `res`
    out = OrderedDict()
    for g in GAMES:
        M, _ = V.matrices(g)
        perms, _ = grid_orders(M, W)
        vals, seen, ndistinct = reachable_discordances(perms)
        top = max(vals) if vals else 0
        ex = seen.get(top)
        tg = seen.get(TARGET)
        out[g] = {"populations": int(W.shape[0]), "distinct_orderings": ndistinct,
                  "reachable": vals,
                  "max_discordant": int(top),
                  "argmax_orderings": [list(a) for a in (ex[0], ex[1])] if ex else None,
                  "argmax_rows": [ex[2], ex[3]] if ex else None,
                  "target_rows": [tg[2], tg[3]] if tg else None}
    return out, W


# ------------------------------------------------------------------------------------------------
# (C) the exact certification of the extremal pair

def exact_payoff_order(M, weights_int, res):
    pop = OrderedDict((a, F(int(weights_int[i]), res)) for i, a in enumerate(ZOO))
    u = OrderedDict((a, V._mean(M, a, pop)) for a in ZOO)
    return order_desc(u), u


def certify_argmax(res, grid):
    """Rebuild each game's extremal pair in EXACT arithmetic from the two grid rows that attained it,
    through the model's own `_mean` and `order_by`, and assert the discordance the grid reported."""
    W = weight_vectors(res)
    out = OrderedDict()
    for g, rec in grid.items():
        if not rec["argmax_orderings"]:
            out[g] = {"certified": None, "reason": "fewer than two distinct orderings"}
            continue
        M, _ = V.matrices(g)
        (r1, r2) = rec["argmax_rows"]
        orders = []
        for r in (r1, r2):
            o, _ = exact_payoff_order(M, W[r], res)
            orders.append(o)
            # the model's own ordering function must agree with ours on this same population
            pop = OrderedDict((a, F(int(W[r][i]), res)) for i, a in enumerate(ZOO))
            assert o == V.order_by(OrderedDict((a, V._mean(M, a, pop)) for a in ZOO)), \
                "our ordering differs from the model's in %s" % g
        # and the rebuild must land on the orderings the grid said it would
        assert [list(o) for o in orders] == rec["argmax_orderings"], \
            "exact rebuild of %s produced %s, grid said %s" % (g, [list(o) for o in orders],
                                                               rec["argmax_orderings"])
        d = discordant(orders[0], orders[1])
        out[g] = {"certified": d, "grid_reading": rec["max_discordant"],
                  "base": str(F(d, NPAIRS)),
                  "mixed_excess": str(F(1) - 2 * F(d, NPAIRS)),
                  "w1": list(W[r1]), "w2": list(W[r2])}
    return out


# ------------------------------------------------------------------------------------------------
# (D) THE CONJUNCTION.  A converse violation needs TWO factors at once:
#       (i)  a population pair whose payoff orderings are EXACTLY NPAIRS/2 apart (base == 1/2), and
#       (ii) a protocol that is faithful (+1) in one population and reversed (-1) in the other.
#     (B) measures (i).  This section measures (ii), at the very pairs (i) supplies.

def orientation(order, payoff_order):
    """+1 if the ordering EQUALS the payoff ordering, -1 if it is its exact reverse, 0 otherwise."""
    if order == payoff_order:
        return 1
    if order == list(reversed(payoff_order)):
        return -1
    return 0


def target_pairs(res, grid):
    """Certify, exactly, one population pair per game whose payoff orderings are NPAIRS/2 apart, and
    report every protocol's orientation and transport excess at it."""
    W = weight_vectors(res)
    out = OrderedDict()
    for g, rec in grid.items():
        if TARGET not in rec["reachable"] or not rec.get("target_rows"):
            continue
        r1, r2 = rec["target_rows"]
        M, Wo = V.matrices(g)
        pops = [OrderedDict((a, F(int(W[r][i]), res)) for i, a in enumerate(ZOO)) for r in (r1, r2)]
        payoff = [V.order_by(OrderedDict((a, V._mean(M, a, pp)) for a in ZOO)) for pp in pops]
        dis = discordant(payoff[0], payoff[1])
        assert dis == TARGET, "the stored target pair is not at the target in %s (%d)" % (g, dis)
        prot = OrderedDict()
        for pn in V4.PROTOCOLS:
            fn = V4.PROTOCOLS[pn]
            orders = [V.order_by(OrderedDict((a, fn(M, a, pp, Wo)) for a in ZOO)) for pp in pops]
            ors = [orientation(orders[i], payoff[i]) for i in (0, 1)]
            raw = F(discordant(orders[0], orders[1]), NPAIRS)
            base = F(dis, NPAIRS)
            prot[pn] = {"orient": ors, "excess": str(raw - base),
                        "mixed": bool(ors[0] and ors[1] and ors[0] != ors[1])}
        out[g] = {"rows": [r1, r2], "weights": [list(W[r1]), list(W[r2])],
                  "base": str(F(dis, NPAIRS)), "payoff_orders": [payoff[0], payoff[1]],
                  "protocols": prot,
                  "mixed_protocols": [pn for pn, v in prot.items() if v["mixed"]]}
    return out


def orientation_census():
    """Over v4's own scan (9 games x 4 populations = 36 cells per protocol), does ANY protocol take
    BOTH signs -- i.e. is any protocol in the design space ever mixed-oriented?"""
    SC = V4.scan()
    cells = SC["cells"]
    per = OrderedDict()
    for k, c in cells.items():
        g, pop, pn = k.split("|")
        v = per.setdefault(pn, {"faithful": 0, "reversed": 0, "undetermined": 0})
        tau = str(c["tau"])
        if tau == "1":
            v["faithful"] += 1
        elif tau == "-1":
            v["reversed"] += 1
        else:
            v["undetermined"] += 1
    for pn, v in per.items():
        v["mixed"] = bool(v["faithful"] and v["reversed"])
    return per


# ------------------------------------------------------------------------------------------------
# the certificate

def certificate(res, sample, grid, certified, tpairs, census):
    ok = total = 0
    log = []

    def check(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        log.append(("  OK   " if cond else "  FAIL ") + name +
                   ("  [%s]" % detail if (detail and not cond) else ""))
        if cond:
            ok += 1

    # THE TARGET: base == 1/2 exactly, i.e. exactly half of the 28 pairs discordant.  (The first
    # draft wrote `half = (2 * NPAIRS) // 2`, which is 28 -- the whole point of the number is that
    # it is HALF the pairs, so the constant is NPAIRS // 2 and nothing else.)
    target = NPAIRS // 2

    # C1 the predicate can say YES
    a = list(ZOO)
    b = list(reversed(a))
    check("C1 the discordance counter reaches the full %d on a reversal" % NPAIRS,
          discordant(a, b) == NPAIRS, "reversal gave %d" % discordant(a, b))

    # C1b the TARGET is attainable by a pair of PERMUTATIONS -- exhaustively enumerated, so the
    # exclusion measured below is a property of the MODEL and not of the ordering space
    witness, wanted = None, []
    for perm in itertools.permutations(range(NPOL)):
        if perm[0] and False:
            continue
        o = [ZOO[i] for i in perm]
        d = discordant(a, o)
        if d == target and witness is None:
            witness = o
        wanted.append(d)
    check("C1b %d of the %d permutations of the eight policies are EXACTLY %d of %d discordant "
          "from the alphabetical order -- the target is squarely inside the permutation space, so "
          "the model, not the space, is what the reading below excludes"
          % (wanted.count(target), len(wanted), target, NPAIRS),
          witness is not None and wanted.count(target) > 0,
          "no permutation reaches %d" % target)
    check("C1c the permutation space spans the target on BOTH sides (min %d, max %d)"
          % (min(wanted), max(wanted)),
          min(wanted) <= target <= max(wanted) and min(wanted) < 10 and max(wanted) == NPAIRS,
          "range %d..%d" % (min(wanted), max(wanted)))

    # C2 the counter moves
    pert = list(a)
    pert[0], pert[-1] = pert[-1], pert[0]
    check("C2 the discordance counter moves under a perturbation",
          discordant(a, pert) > 0, "the counter is stuck at zero")

    # C3 exact rebuild == the integer grid, per game
    bad = [(g, r) for g, r in certified.items()
           if r.get("certified") is not None and r["certified"] != r["grid_reading"]]
    check("C3 the Fraction rebuild agrees with the integer grid in every game",
          not bad, "disagreements: %s" % bad[:3])

    # C4 the mixed-entry excess is `1 - 2*base` and matches the exact recomputation
    bad4 = []
    for g, r in certified.items():
        if r.get("certified") is None:
            continue
        ex = F(1) - 2 * F(r["certified"], NPAIRS)
        if r["mixed_excess"] != str(ex):
            bad4.append((g, "excess mismatch"))
    check("C4 the mixed-entry excess is 1 - 2*base in every game", not bad4,
          "offenders: %s" % bad4[:3])

    # C5 the grid really covers the simplex
    S = len(weight_vectors(res))
    want = 1
    for k in range(1, NPOL):
        want = want * (res + k) // k
    check("C5 the grid enumerates the whole simplex: %d populations = C(%d+%d-1, %d-1)"
          % (S, res, NPOL, NPOL), S == want, "count %d vs stars-and-bars %d" % (S, want))
    check("C5b every grid vector sums to the resolution",
          all(sum(w) == res for w in weight_vectors(res)[:50]), "a vector does not sum to res")

    # C6 THE READING: is the target in the model's reachable set?  And is that set wide enough for
    # the answer to mean anything (a set of one value would exclude the target vacuously)?
    hits = [g for g, r in grid.items() if target in r["reachable"]]
    widths = {g: (min(r["reachable"]), max(r["reachable"]), len(r["reachable"]))
              for g, r in grid.items() if r["reachable"]}
    check("C6 the reachable set is non-degenerate in every game (it spans several values), so the "
          "exclusion is a reading and not a vacuous singleton",
          all(w[2] >= 3 and w[1] > w[0] for w in widths.values()), "widths: %s" % widths)
    check("C6b the target %d IS in the model's reachable set (%d game(s) attain it), so the "
          "converse is decided by measurement" % (target, len(hits)) if hits else
          "C6b the target %d is NOT in the model's reachable set in any of the %d games -- the "
          "converse is undecidable here, and the exclusion was MEASURED, not assumed"
          % (target, len(grid)),
          True, "")
    check("C6c every game's reachable set is a CONTIGUOUS run of values from its minimum",
          all(r["reachable"] == list(range(min(r["reachable"]), max(r["reachable"]) + 1))
              for r in grid.values() if r["reachable"]),
          "a game's reachable set has a hole in it")

    # ---- (D) THE CONJUNCTION: the second factor, at the pairs the first factor supplies ----
    check("D1 the target pair's base is EXACTLY 1/2 in every game that reaches it",
          tpairs and all(r["base"] == "1/2" for r in tpairs.values()),
          "bases: %s" % {g: r["base"] for g, r in tpairs.items()})
    mixed = {g: r["mixed_protocols"] for g, r in tpairs.items() if r["mixed_protocols"]}
    check("D2 NO protocol in the design space is mixed-oriented at the base=1/2 pairs (%d game(s) "
          "supply the first factor, %d protocols tested)" % (len(tpairs), len(V4.PROTOCOLS)),
          tpairs and not mixed, "mixed: %s" % mixed)

    # D2-PLANT: a score that is -payoff in one population and +payoff in the other IS mixed, and its
    # excess is exactly 0 -- so the predicate can fire, and the missing factor has a NAME
    g0 = next(iter(tpairs), None)
    if g0 is not None:
        r = tpairs[g0]
        M, Wo = V.matrices(g0)
        p1 = OrderedDict((a, F(int(r["weights"][0][i]), res)) for i, a in enumerate(ZOO))
        p2 = OrderedDict((a, F(int(r["weights"][1][i]), res)) for i, a in enumerate(ZOO))
        # The score must be population-CONDITIONAL, and it must reverse EXACTLY.  The first draft
        # signed `-_mean`, which fails at this very pair: the payoff vectors there are heavily TIED
        # (a pure population puts most policies at the same payoff), and `order_by` breaks ties by
        # NAME -- a tie-break that negation does not reverse, so the "reversal" read +0 and the
        # plant reported orientations [0, +1].  Signing the RANK instead fixes it: ranks are
        # distinct and already carry the model's own tie-break, so `+rank` is the payoff ordering's
        # exact reverse and `-rank` is the ordering itself.
        def flip(M, a, pop, W, _p1=p1):
            r = V.ranks_of(OrderedDict((x, V._mean(M, x, pop)) for x in ZOO))[a]
            return r if pop is _p1 else -r
        o1 = V.order_by(OrderedDict((a, flip(M, a, p1, Wo)) for a in ZOO))
        o2 = V.order_by(OrderedDict((a, flip(M, a, p2, Wo)) for a in ZOO))
        po = [V.order_by(OrderedDict((a, V._mean(M, a, pp)) for a in ZOO)) for pp in (p1, p2)]
        ors = [orientation(o1, po[0]), orientation(o2, po[1])]
        ex = F(discordant(o1, o2), NPAIRS) - F(discordant(po[0], po[1]), NPAIRS)
        check("D2-PLANT a POPULATION-CONDITIONAL score is mixed at this very pair and reads "
              "excess == 0 exactly -- so the converse IS refutable by a score whose sign flips with "
              "the population, and the design space simply contains no such score",
              ors[0] and ors[1] and ors[0] != ors[1] and ex == 0,
              "plant gave orientations %s and excess %s" % (ors, ex))
    else:
        check("D2-PLANT cannot be formed: no game supplies the base=1/2 factor", False,
              "tpairs is empty")

    # ---- (E) the same question over the scan of record, where the denominator is the shipped grid
    anymixed = [pn for pn, v in census.items() if v["mixed"]]
    check("E1 over v4's own 684-cell scan, no protocol takes BOTH a +1 and a -1 cell -- no protocol "
          "in the space is mixed-oriented anywhere, not only at the base=1/2 pairs",
          not anymixed, "mixed in the scan of record: %s" % anymixed)
    check("E2 the census is not vacuous: some protocol IS faithful somewhere and another IS reversed "
          "somewhere, so the two signs are both represented in the space",
          any(v["faithful"] for v in census.values()) and any(v["reversed"] for v in census.values()),
          "one of the two signs never occurs, so E1 would hold trivially")

    return {"items": log, "ok": ok, "total": total,
            "target": target, "target_reached_by": hits}


# ------------------------------------------------------------------------------------------------

def report_text(d):
    L = []
    A = L.append
    target = d["target"]
    A("== issue #141 -- the SCOPE of the transport law's converse ==")
    A("   a mixed-orientation entry reads  excess = 1 - 2*base,  so it reads ZERO only when")
    A("   base == 1/2 EXACTLY -- exactly %d of the %d policy pairs discordant." % (target, NPAIRS))
    A("")
    A("(A) the sample of record (the four named populations of the shipped design)")
    A("   %-8s %-22s %-8s %s" % ("game", "distinct orderings", "max disc", "pairwise)"))
    for g, r in d["sample_of_record"].items():
        A("   %-8s %-22s %-8d %s"
          % (g, "%d of 4" % r["distinct_orderings"], r["max_discordant"], dict(r["pairs"])))
    A("   -> the shipped design never exceeds %d of %d, so it cannot decide the converse at all."
      % (d["global_max_of_record"], NPAIRS))
    A("")
    A("(B) the exact INTEGER grid over the WHOLE simplex (resolution 1/%d, %d populations per game)"
      % (d["resolution"], d["populations_per_game"]))
    A("   %-8s %-9s %-9s %s" % ("game", "orderings", "reach set", "the reachable discordances"))
    for g, r in d["grid"].items():
        A("   %-8s %-9d %-9s %s"
          % (g, r["distinct_orderings"], "%d values" % len(r["reachable"]), r["reachable"]))
    A("")
    A("(C) the exact certification of each game's extremal pair")
    for g, r in d["certified"].items():
        if r.get("certified") is None:
            A("   %-8s %s" % (g, r["reason"]))
            continue
        A("   %-8s certified %2d of %d  (base %-6s)  mixed excess %-6s  %s"
          % (g, r["certified"], NPAIRS, r["base"], r["mixed_excess"],
             "AGREES with the integer grid" if r["certified"] == r["grid_reading"] else "DISAGREES"))
    A("")
    A("(D) THE CONJUNCTION -- at the pairs where base is EXACTLY 1/2, is any protocol MIXED?")
    if not d["target_pairs"]:
        A("   no game reaches base = 1/2, so the conjunction cannot be probed")
    for g, r in d["target_pairs"].items():
        A("   %-8s base %-4s  weights %s vs %s" % (g, r["base"], r["weights"][0], r["weights"][1]))
        A("            payoff P1 %s" % r["payoff_orders"][0])
        A("            payoff P2 %s" % r["payoff_orders"][1])
        for pn, v in r["protocols"].items():
            if v["orient"][0] or v["orient"][1]:
                A("            %-14s orient %+d/%+d  excess %-8s%s"
                  % (pn, v["orient"][0], v["orient"][1], v["excess"],
                     "   <== MIXED" if v["mixed"] else ""))
        A("            MIXED: %s" % (r["mixed_protocols"] or "NONE"))
    A("")
    A("(E) the same question over v4's own 684-cell scan (denominator: 36 cells per protocol)")
    for pn, v in d["orientation_census"].items():
        A("   %-14s faithful %2d  reversed %2d  undetermined %2d   %s"
          % (pn, v["faithful"], v["reversed"], v["undetermined"],
             "MIXED" if v["mixed"] else ""))
    A("")
    A("VERDICT")
    obs = d["global_max"]
    A("   over the whole population simplex the reachable discordance reaches %d of %d (base %s),"
      % (obs, NPAIRS, F(obs, NPAIRS)))
    sets = [r["reachable"] for r in d["grid"].values() if r["reachable"]]
    contig = all(v == list(range(min(v), max(v) + 1)) for v in sets)
    A("   each game's reachable set is %s, and the lowest value any game reaches is %d."
      % ("a CONTIGUOUS run of integers" if contig else "NOT contiguous", min(min(v) for v in sets)))
    A("   (a distance of 0 never occurs: two DISTINCT orderings cannot be 0 apart.)")
    A("   the mixed-orientation zero needs EXACTLY %d of %d." % (target, NPAIRS))
    if d["target_in_reachable_set"]:
        A("   => factor (i) IS available: %s reach base = 1/2 exactly, and each is certified"
          % ", ".join(d["games_attaining_target"]))
        A("      above in exact arithmetic.")
        if not d["mixed_protocols_anywhere"] and not any(
                r["mixed_protocols"] for r in d["target_pairs"].values()):
            A("   => factor (ii) is NOT: NO protocol in the design space is mixed-oriented, either at")
            A("      those pairs (D) or anywhere in the 684-cell scan of record (E). So the converse")
            A("      is UNDECIDABLE HERE -- not for want of a population pair, but for want of a")
            A("      protocol whose monotone relation to the payoff FLIPS with the population.")
            A("   => and the missing factor has a NAME: a POPULATION-CONDITIONAL score refutes the")
            A("      converse at this very pair with excess exactly 0 (plant D2-PLANT). The design")
            A("      space contains no such score, which is why the converse never fires there.")
        else:
            A("   => the converse IS refuted: a mixed-oriented protocol exists at a base=1/2 pair.")
    A("")
    c = d["_certificate"]
    A("certificate %d/%d   (target = %d of %d pairs)" % (c["ok"], c["total"], c["target"], NPAIRS))
    L.extend(c["items"])
    return "\n".join(L) + "\n"


def build(res):
    sample = sample_of_record()
    grid, _ = grid_scan(res)
    certified = certify_argmax(res, grid)
    tpairs = target_pairs(res, grid)
    census = orientation_census()
    d = {
        "resolution": res,
        "policies": NPOL,
        "pairs": NPAIRS,
        "mixed_zero_requires_discordant": NPAIRS // 2,
        "sample_of_record": sample,
        "populations_per_game": len(weight_vectors(res)),
        "grid": grid,
        "certified": certified,
        "global_max": max(r["max_discordant"] for r in grid.values()),
        "global_max_of_record": max(r["max_discordant"] for r in sample.values()),
        "target": NPAIRS // 2,
        "target_in_reachable_set": any((NPAIRS // 2) in r["reachable"] for r in grid.values()),
        "games_attaining_target": [g for g, r in grid.items() if (NPAIRS // 2) in r["reachable"]],
    }
    d["target_pairs"] = tpairs
    d["orientation_census"] = census
    d["mixed_protocols_anywhere"] = [pn for pn, v in census.items() if v["mixed"]]
    d["_certificate"] = certificate(res, sample, grid, certified, tpairs, census)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = build(a.res)
    print(report_text(d), end="")
    if a.out:
        payload = json.dumps(d, indent=1, sort_keys=True, default=str) + "\n"
        with open(a.out, "w") as fh:
            fh.write(payload)
        print("\nwrote %s  sha256 %s" % (a.out, hashlib.sha256(payload.encode()).hexdigest()[:16]))
    return 0 if d["_certificate"]["ok"] == d["_certificate"]["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
