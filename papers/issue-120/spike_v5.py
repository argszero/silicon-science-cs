#!/usr/bin/env python3
"""issue #120 spike_v5 -- THE PROFILE-INVISIBLE FRACTION (quantifying the no-go).

spike_v4 proved phi* is not a function of the stack-distance profile by exhibiting ONE matched
pair.  A no-go does not say HOW MUCH the profile fails to determine.  This run measures it.

Method: bucket traces by their stack-distance profile (exact multiset at small scale; exact
histogram at larger scale) and ask, inside each bucket,
    (i)  how much does phi* vary?   -> the PROFILE-INVISIBLE component
    (ii) does the LRU curve vary?   -> it must NOT (Mattson), asserted per bucket

Within one profile class the policy's own curve is fixed while the ceiling moves: the spread of
phi* inside a class is exactly the part of the oracle's advantage that NO profile-based method can
see -- not a bad statistic, but information the profile does not carry.

Parts:
  1. EXHAUSTIVE: all distinct arrangements of a fixed symbol multiset, bucketed by exact profile;
  2. MID-SCALE: random traces, bucketed by exact stack-distance histogram;
  3. PRACTICAL SCALE: the spike_v4 matched pair repeated K times (sd-L1 exactly 0 by construction).

Controls: LRU invariance asserted inside every bucket (Mattson); an alphabet-relabelling control
asserting relabelling neither moves a trace between buckets nor changes phi*.

Run: /usr/bin/python3 spike_v5.py     ->  spike_v5_results.json
"""
import itertools
import json
import random
import sys
from collections import Counter

import spike_v1 as s1
import spike_v2 as s2

SEED0 = 20261003
CAPS = [1, 2, 3]
PAIR_A = [1, 2, 1, 2, 0, 1, 0, 2, 1]
PAIR_B = [2, 0, 1, 0, 2, 0, 1, 0, 2]


def sd_profile(trace):
    """The canonical PROFILE: the multiset of stack distances (order-free and label-free)."""
    return tuple(sorted(s2.stack_distances(trace)))


def lru_curve(trace, caps):
    return [s2.lru_curve_from_sd(s2.stack_distances(trace), caps)[c] for c in caps]


def phi_curve(trace, caps):
    n = len(trace)
    return [s1.opt_heap(trace, c) / n for c in caps]


def analyse_bucket(members):
    """members share a profile.  Returns the spread of phi* and asserts the LRU curve is constant
    across them (Mattson: the profile fixes every stack algorithm's curve)."""
    curves = [phi_curve(t, CAPS) for t in members]
    lrus = [lru_curve(t, CAPS) for t in members]
    for l in lrus[1:]:
        assert l == lrus[0], "LRU varies inside a profile class -- Mattson violated"
    res = []
    for j, c in enumerate(CAPS):
        vals = [cu[j] for cu in curves]
        lo, hi = min(vals), max(vals)
        ratio = (hi / lo) if lo > 1e-12 else (float("inf") if hi > 1e-12 else 1.0)
        res.append({"cap": c, "min": lo, "max": hi, "ratio": ratio, "abs_spread": hi - lo})
    return {"n": len(members), "phi": res, "lru": lrus[0]}


def exhaustive_pattern(counts):
    """Every distinct arrangement of a fixed symbol multiset, bucketed by exact profile."""
    items = []
    for sym, k in enumerate(counts):
        items.extend([sym] * k)
    buckets = {}
    for perm in set(itertools.permutations(items)):
        buckets.setdefault(sd_profile(perm), []).append(list(perm))
    return buckets


def main():
    out = {"seed0": SEED0, "caps": CAPS, "exhaustive": {}, "midscale": {}, "practical": {}}

    print("=" * 104)
    print("PART 1 -- EXHAUSTIVE: every distinct arrangement of a fixed symbol multiset, bucketed")
    print("by its exact stack-distance multiset.  'spread' classes = those whose members do NOT all")
    print("share one phi*; 'ratio' = phi*(max)/phi*(min) inside such a class, at cap 2.")
    print("%-16s%8s%9s%9s%8s%11s%11s%11s"
          % ("symbol counts", "arrngs", "classes", "multi", "spread", "%spread",
             "max ratio", "mean ratio"))
    patterns = [(3, 3, 3), (4, 2, 2, 2), (2, 2, 2, 2), (5, 2, 2), (4, 3, 2), (2, 2, 2, 2, 2)]
    for pat in patterns:
        buckets = exhaustive_pattern(pat)
        narr = sum(len(v) for v in buckets.values())
        multi, ratios = 0, []
        for prof, members in buckets.items():
            if len(members) < 2:
                continue
            multi += 1
            # Mattson check per class: the profile fixes every stack algorithm's curve
            lrus = {tuple(lru_curve(t, CAPS)) for t in members}
            assert len(lrus) == 1, "LRU varies inside a profile class -- Mattson violated"
            values = {s1.opt_heap(t, 2) for t in members}
            if len(values) > 1:                       # a class that actually carries a spread
                ratios.append(max(values) / min(values))
        finite = [r for r in ratios if r != float("inf")]
        rec = {"arrangements": narr, "classes": len(buckets), "multi_member": multi,
               "spread_classes": len(ratios),
               "frac_spread": len(ratios) / len(buckets),
               "max_ratio": max(ratios) if ratios else 1.0,
               "mean_ratio": (sum(finite) / len(finite)) if finite else 1.0}
        out["exhaustive"]["_".join(map(str, pat))] = rec
        print("%-16s%8d%9d%9d%8d%8.0f%%%11s%11.3f"
              % (str(pat), narr, len(buckets), multi, len(ratios), 100 * rec["frac_spread"],
                 ("%.2f" % rec["max_ratio"]) if ratios else "-", rec["mean_ratio"]))

    print()
    print("CONTROL -- an alphabet relabelling must not change the class or phi*")
    base = [1, 2, 1, 2, 0, 1, 0, 2, 1]
    perm = [2, 0, 1]
    relab = [perm[x] for x in base]
    same_class = sd_profile(base) == sd_profile(relab)
    same_phi = (s1.opt_heap(base, 2) == s1.opt_heap(relab, 2))
    print("   base phi*(cap2)=%d  relabelled phi*(cap2)=%d  same class=%s"
          % (s1.opt_heap(base, 2), s1.opt_heap(relab, 2), same_class))
    assert same_class and same_phi, "relabelling control FAILED"
    out["relabel_control"] = {"same_class": same_class, "same_phi": same_phi}

    print()
    print("=" * 104)
    print("PART 2 -- MID-SCALE: random traces, bucketed by EXACT stack-distance profile")
    print("   n     alphabet   drawn    classes   spread   %spread   max ratio   max abs spread")
    AL, LEN, DRAWS = 4, 40, 60000
    rng = random.Random(SEED0)
    buckets = {}
    for _ in range(DRAWS):
        tr = tuple(rng.randrange(AL) for _ in range(LEN))
        if len(set(tr)) < AL:
            continue
        buckets.setdefault(sd_profile(tr), []).append(list(tr))
    multi, maxr, maxd = 0, 1.0, 0.0
    for prof, members in buckets.items():
        if len(members) < 2:
            continue
        a = analyse_bucket(members[:6])
        row = a["phi"][1]
        if row["ratio"] > 1.0:
            multi += 1
            maxr = max(maxr, row["ratio"])
            maxd = max(maxd, row["abs_spread"])
    print("   %-5d %-10d %-8d %-9d %-8d %-8.0f%% %-11.3f %.4f"
          % (LEN, AL, DRAWS, len(buckets), multi, 100 * multi / len(buckets), maxr, maxd))
    out["midscale"] = {"n": LEN, "alphabet": AL, "draws": DRAWS, "classes": len(buckets),
                       "multi_classes": multi, "max_ratio": maxr, "max_abs_spread": maxd}
    assert multi > 0, "no multi-member classes at mid scale -- the search is too thin"

    print()
    print("=" * 104)
    print("PART 3 -- PRACTICAL SCALE: the matched pair repeated K times (sd-L1 exactly 0)")
    print("   K       n      phi*_A   phi*_B   B/A-1     lru_A    lru_B    sd-L1")
    for K in (1, 20, 200, 1000):
        a, b = PAIR_A * K, PAIR_B * K
        pa = s1.opt_heap(a, 2) / len(a)
        pb = s1.opt_heap(b, 2) / len(b)
        la = s2.lru_curve_from_sd(s2.stack_distances(a), [2])[2]
        lb = s2.lru_curve_from_sd(s2.stack_distances(b), [2])[2]
        ca, cb = Counter(s2.stack_distances(a)), Counter(s2.stack_distances(b))
        l1 = sum(abs(ca[k] / len(a) - cb[k] / len(b)) for k in set(ca) | set(cb))
        print("   %-6d %-7d %-8.4f %-8.4f %+8.1f%% %-8.4f %-8.4f %8.4f"
              % (K, len(a), pa, pb, 100 * (pb / pa - 1), la, lb, l1))
        out["practical"]["K=%d" % K] = {"n": len(a), "phi_A": pa, "phi_B": pb,
                                        "gap": pb / pa - 1, "lru": la, "sd_l1": l1}
        assert l1 == 0.0, "the practical-scale pair drifted off the matched profile"
        assert la == lb, "LRU differs on a matched pair -- Mattson violated"
    print("   -> at every scale: the same profile, the same LRU curve, phi* differing by up to 2x.")

    with open("spike_v5_results.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote spike_v5_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
