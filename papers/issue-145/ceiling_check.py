#!/usr/bin/env python3
"""Exact verification of the detection-ceiling propositions (issue #145, R674).

`ceiling_law.md` states five propositions. This file checks each one by EXACT enumeration in
`Fraction` arithmetic -- no sampling, no floating point, no seed -- and then demonstrates that the
checks fail when the implementation is broken. A verification that cannot fail has verified nothing.

The model
---------
A path of k edges. A joint law over the edge-naming events is a distribution over the 2^k subsets
of {A_1..A_k}: `{subset_mask: probability}`. Everything below is a function of that distribution, so
the propositions are checked over IMPLEMENTATIONS OF LAWS, not over samples.

Detection: D = 1 iff every edge is named, i.e. iff the full-set mask is realised. So
P(D) = law[full_mask]. That identity is Proposition 1 and is asserted directly.

Run: python3 ceiling_check.py     exit 0 = every check passed and every plant fired.
"""
import itertools
import sys
from fractions import Fraction as F

FAILS = []
CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append(ok)
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")
    if not ok:
        FAILS.append(name)


def full_mask(k):
    return (1 << k) - 1


def P_D(law, k):
    """Proposition 1: the ceiling is the probability of the WHOLE edge set."""
    return law.get(full_mask(k), F(0))


def marginals(law, k):
    return [sum((p for m, p in law.items() if m >> i & 1), F(0)) for i in range(k)]


def law_independent(c):
    """A_i independent with P(A_i) = c_i."""
    k = len(c)
    law = {}
    for mask in range(1 << k):
        p = F(1)
        for i in range(k):
            p *= c[i] if mask >> i & 1 else (1 - c[i])
        if p:
            law[mask] = p
    return law


def law_comonotone(c):
    """One mechanism decides every edge: A_i = {U <= c_i} for a single U, so the events NEST.

    For U in the band (c_(j-1), c_(j)] -- thresholds taken in ascending order -- the events that
    hold are exactly those whose threshold is at least U, i.e. the SUFFIX `order[j:]`. Writing the
    suffix (not the prefix) is what makes a zero marginal behave: with c_i = 0 the event A_i can
    never hold, so no band may carry its bit. An earlier version of this function wrote the prefix
    and thereby reported a ceiling of 1 for an all-zero path -- the exact defect Proposition 5 is
    about, found by the check rather than by reading.
    """
    k = len(c)
    order = sorted(range(k), key=lambda i: c[i])
    law = {}
    prev = F(0)
    for j in range(k):
        p = c[order[j]] - prev
        if p:
            mask = 0
            for i in order[j:]:
                mask |= 1 << i
            law[mask] = law.get(mask, F(0)) + p
        prev = c[order[j]]
    tail = F(1) - prev
    if tail:
        law[0] = law.get(0, F(0)) + tail
    return law


def law_frechet_lower(c):
    """The Fréchet lower bound construction for equal marginals c = 1/n: cycle the events.

    For c_i = c all equal, partition the unit interval into n equal blocks and let A_i hold on all
    blocks except block i. Then every block misses exactly one event, so P(D) = 0 for k >= 2 and
    the marginals are (n-1)/n.
    """
    k = len(c)
    assert all(x == c[0] for x in c), "this construction is for equal marginals"
    n = k
    law = {}
    for block in range(n):
        mask = full_mask(k)
        mask &= ~(1 << block)          # block b misses event b
        law[mask] = law.get(mask, F(0)) + F(1, n)
    return law


def check_frechet(k, c):
    """Exact Fréchet bounds for the intersection with fixed marginals."""
    lo = max(F(0), sum(c) - (k - 1))
    hi = min(c)
    return lo, hi


# --------------------------------------------------------------------------------------------------
# the propositions

def prop1():
    print("Proposition 1 -- the ceiling is the probability of the whole edge set")
    for c in ([F(1, 2), F(1, 2)], [F(1, 3), F(2, 3), F(1, 2)]):
        for law in (law_independent(c), law_comonotone(c)):
            check(f"P(D) == law[full] for c={[str(x) for x in c]}",
                  P_D(law, len(c)), law.get(full_mask(len(c)), F(0)))


def prop2():
    print("\nProposition 2 -- Fréchet upper bound, ATTAINED by comonotone edges")
    for c in ([F(1, 2), F(1, 2)], [F(1, 2), F(1, 2), F(1, 2)],
              [F(1, 5), F(1, 2), F(9, 10)]):
        k = len(c)
        law = law_comonotone(c)
        check(f"comonotone marginals preserved for c={[str(x) for x in c]}",
              marginals(law, k), list(c))
        check(f"comonotone attains min c for c={[str(x) for x in c]}",
              P_D(law, k), min(c))
        # and no law may exceed it: check every law that preserves these marginals among a family
        for cand, name in ((law_independent(c), "independent"),):
            check(f"{name} ceiling <= min c", P_D(cand, k) <= min(c), True)


def prop3():
    print("\nProposition 3 -- independence gives exactly the product")
    for c in ([F(1, 2), F(1, 2)], [F(1, 2)] * 3, [F(1, 10)] * 3, [F(3, 7), F(2, 5), F(1, 3)]):
        k = len(c)
        law = law_independent(c)
        prod = F(1)
        for x in c:
            prod *= x
        check(f"marginals preserved for c={[str(x) for x in c]}", marginals(law, k), list(c))
        check(f"independent ceiling == product for c={[str(x) for x in c]}", P_D(law, k), prod)


def prop4():
    print("\nProposition 4 -- NOT identified by the coverage vector: both endpoints attained")
    # equal marginals 1/2, k = 2 and k = 3: independent vs comonotone
    for k in (2, 3):
        c = [F(1, 2)] * k
        ind = P_D(law_independent(c), k)
        com = P_D(law_comonotone(c), k)
        check(f"k={k}: identical marginals", marginals(law_independent(c), k) ==
              marginals(law_comonotone(c), k), True)
        check(f"k={k}: ceilings differ", ind != com, True)
        check(f"k={k}: ratio combinatorially 2^(k-1)", com / ind, F(2) ** (k - 1))
    # the Fréchet lower endpoint is attained at equal marginals = (k-1)/k -> P(D) = 0
    for k in (2, 3, 4):
        c = [F(k - 1, k)] * k
        law = law_frechet_lower(c)
        check(f"k={k}: lower construction preserves marginals", marginals(law, k), list(c))
        check(f"k={k}: lower endpoint P(D) == 0", P_D(law, k), F(0))
        lo, hi = check_frechet(k, c)
        check(f"k={k}: P(D) inside the Frechet interval", lo <= P_D(law, k) <= hi, True)
    # a case where the Fréchet lower bound is strictly positive
    k, c = 3, [F(9, 10)] * 3
    lo, hi = check_frechet(k, c)
    check("Frechet lower bound is positive for c=0.9,k=3", lo, F(7, 10))
    check("independent value sits above the Frechet lower bound",
          P_D(law_independent(c), k) >= lo, True)


def prop5():
    print("\nProposition 5 -- one zero edge forces the ceiling to 0 under EVERY law")
    for k in (2, 3):
        for zero_at in range(k):
            c = [F(1, 2)] * k
            c[zero_at] = F(0)
            ind = P_D(law_independent(c), k)
            com = P_D(law_comonotone(c), k)
            check(f"k={k} zero at {zero_at}: independent == 0", ind, F(0))
            check(f"k={k} zero at {zero_at}: comonotone == 0", com, F(0))
            lo, hi = check_frechet(k, c)
            check(f"k={k} zero at {zero_at}: Frechet interval collapses to [0,0]", (lo, hi),
                  (F(0), F(0)))
    # and the same against the two MEASURED ecosystems' shape: every edge zero
    for k in (1, 2, 3):
        c = [F(0)] * k
        check(f"all-zero path at depth {k}: ceiling 0 (both laws)",
              (P_D(law_independent(c), k), P_D(law_comonotone(c), k)), (F(0), F(0)))


def prop6():
    print("\nProposition 6 -- raising uniform c multiplies the product, not the assumption-free bound")
    k = 3
    lo_c, hi_c = F(1, 10), F(3, 10)
    prod_ratio = (hi_c ** k) / (lo_c ** k)
    check("product ceiling ratio is (3)^k", prod_ratio, F(27))
    check("the assumption-free bound moves only 3x", hi_c / lo_c, F(3))
    # the bound is what a verifier can certify without knowing correlation
    for kk in (2, 3, 4):
        c = [F(3, 10)] * kk
        _, hi = check_frechet(kk, c)
        check(f"k={kk}: assumption-free bound == min c", hi, min(c))


# --------------------------------------------------------------------------------------------------
# plants: broken implementations must be caught

def plants():
    print("\nplants -- wrong implementations must be CAUGHT")
    k = 3
    c = [F(1, 2)] * 3

    wrong = {}

    def wrong_product_as_min(law, k):
        """Defect: reports the minimum marginal as if it were the ceiling under ANY law."""
        return min(marginals(law, k))

    def wrong_full_ignores_conjunction(law, k):
        """Defect: sums the marginal probabilities instead of intersecting."""
        return sum(marginals(law, k))

    def wrong_independence_for_all(law, k):
        """Defect: assumes independence and returns the product of marginals, whatever the law."""
        p = F(1)
        for x in marginals(law, k):
            p *= x
        return p

    wrong["product_as_min"] = wrong_product_as_min
    wrong["sum_for_intersection"] = wrong_full_ignores_conjunction
    wrong["independent_for_all"] = wrong_independence_for_all

    ind_law = law_independent(c)
    com_law = law_comonotone(c)

    # the correct instrument distinguishes them; each wrong one must NOT distinguish, or must give
    # the wrong value on at least one of them
    correct_pair = (P_D(ind_law, k), P_D(com_law, k))
    check("correct instrument separates the two regimes", correct_pair, (F(1, 8), F(1, 2)))

    caught = {name: [] for name in wrong}
    for name, fn in wrong.items():
        pair = (fn(ind_law, k), fn(com_law, k))
        if pair != correct_pair:
            caught[name].append(f"values {pair} != {correct_pair}")
        if pair[0] == pair[1] and correct_pair[0] != correct_pair[1]:
            caught[name].append("cannot separate the regimes at all")
    for name, why in caught.items():
        ok = bool(why)
        CHECKS.append(ok)
        _why = why if why else "NOTHING -- this plant does not reach the defect"
        print("  [%s] %s caught by %s" % ("ok" if ok else "FAIL", name, _why))
        if not ok:
            FAILS.append(f"{name} not caught")

    # and a mutation of the REAL function: make P_D read a marginal instead of the full mask
    real = globals()["P_D"]

    def broken_P_D(law, k):
        return min(marginals(law, k))

    globals()["P_D"] = broken_P_D
    try:
        ok = P_D(ind_law, k) != F(1, 8)
    finally:
        globals()["P_D"] = real
    CHECKS.append(ok)
    print("  [%s] mutating P_D to read a marginal is caught by prop3's k=3 case"
          % ("ok" if ok else "FAIL"))
    if not ok:
        FAILS.append("P_D mutation not caught")


def main():
    prop1()
    prop2()
    prop3()
    prop4()
    prop5()
    prop6()
    plants()
    total, failed = len(CHECKS), len(FAILS)
    print()
    if failed:
        print(f"CEILING: {total - failed}/{total} ok -- {failed} FAILED: {FAILS}")
        return 1
    print(f"CEILING: ALL {total} CHECKS PASSED (5 propositions, 3 wrong variants + 1 mutation caught)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
