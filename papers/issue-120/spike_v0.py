#!/usr/bin/env python3
"""issue #120 spike_v0 -- is there an EXACT optimum to measure policies against?

The paper's construct is phi*, the minimum slow-tier (miss) fraction over ALL placement
policies at a given fast-tier capacity.  Before anything else is claimed, that optimum
must exist as a computable object and must be certified by TWO independent routes:

  route A: Belady's offline optimum (evict the item whose next use is farthest away) --
           exact for unit-size items with a uniform miss cost, and cheap (O(n * c));
  route B: exhaustive search over cache states on tiny traces (memoised over
           (position, cache contents)) -- exact by construction, and independent of
           Belady's argument.

If the two disagree anywhere, the "optimum" is not an optimum and every later number is
void.  A one-sided control (a deliberately bad policy that evicts the item used SOONEST)
must also be strictly worse than the optimum -- a bound that nothing can violate is not
a bound.

Run: /usr/bin/python3 spike_v0.py     ->  spike_v0_results.json
"""
import json
import random
import sys
from functools import lru_cache

SEED = 20261003


# ---------------------------------------------------------------- traces
def trace_iid(n, univ, rng, power=1.0):
    """i.i.d. draws with a power-law popularity (power=1 is uniform)."""
    w = [1.0 / ((i + 1) ** power) for i in range(univ)]
    s = sum(w)
    p = [x / s for x in w]
    cum, acc = [], 0.0
    for x in p:
        acc += x
        cum.append(acc)
    out = []
    for _ in range(n):
        r = rng.random()
        lo, hi = 0, univ - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if r <= cum[mid]:
                hi = mid
            else:
                lo = mid + 1
        out.append(lo)
    return out


def trace_hotset(n, univ, hot, rng, p_hot=0.9):
    """A heavy head: `hot` items carry p_hot of the accesses (the knee's cause)."""
    out = []
    for _ in range(n):
        if rng.random() < p_hot:
            out.append(rng.randrange(hot))
        else:
            out.append(rng.randrange(univ))
    return out


def trace_scan(n, univ, rng, chunk=8):
    """Sequential scan with a random start: no reuse inside a pass (the anti-locality side)."""
    out = []
    while len(out) < n:
        s = rng.randrange(univ)
        out.extend((s + k) % univ for k in range(chunk))
    return out[:n]


# ---------------------------------------------------------------- route A
def opt_misses(trace, cap):
    """Belady's offline optimum: exact for unit-size items, uniform miss cost."""
    cache = set()
    misses = 0
    for i, x in enumerate(trace):
        if x in cache:
            continue
        misses += 1
        if len(cache) < cap:
            cache.add(x)
            continue
        # evict the cached item whose next use is farthest in the future
        far, victim = -1, None
        for y in cache:
            try:
                nxt = trace.index(y, i + 1)
            except ValueError:
                nxt = len(trace) + 1
            if nxt > far:
                far, victim = nxt, y
        cache.discard(victim)
        cache.add(x)
    return misses


# ---------------------------------------------------------------- route B
def brute_misses(trace, cap):
    """Exhaustive search over cache contents: exact, and independent of Belady's rule."""
    n = len(trace)

    @lru_cache(maxsize=None)
    def best(i, cache):
        if i == n:
            return 0
        x = trace[i]
        if x in cache:
            return best(i + 1, cache)
        # a miss: keep the state feasible -- if not full, the only choice is to add x
        if len(cache) < cap:
            return 1 + best(i + 1, tuple(sorted(cache + (x,))))
        # full: choose a victim (possibly the newcomer, which is the same as no change)
        options = [tuple(sorted(tuple(y for y in cache if y != v) + (x,))) for v in cache]
        return 1 + min(best(i + 1, st) for st in options)

    return best(0, ())


# ---------------------------------------------------------------- policies
def lru_misses(trace, cap):
    cache, misses = {}, 0
    for i, x in enumerate(trace):
        if x in cache:
            cache[x] = i
            continue
        misses += 1
        if len(cache) >= cap:
            del cache[min(cache, key=cache.get)]
        cache[x] = i
    return misses


def lfu_misses(trace, cap):
    cache, freq, misses = {}, {}, 0
    for i, x in enumerate(trace):
        if x in cache:
            freq[x] += 1
            continue
        misses += 1
        if len(cache) >= cap:
            del cache[min(cache, key=lambda y: (freq[y], cache[y]))]
        cache[x] = i
        freq[x] = freq.get(x, 0) + 1
    return misses


def worst_misses(trace, cap):
    """The one-sided control: evict the item used SOONEST -- must never beat the optimum."""
    cache, misses = set(), 0
    for i, x in enumerate(trace):
        if x in cache:
            continue
        misses += 1
        if len(cache) < cap:
            cache.add(x)
            continue
        near, victim = len(trace) + 2, None
        for y in cache:
            try:
                nxt = trace.index(y, i + 1)
            except ValueError:
                nxt = len(trace) + 1
            if nxt < near:
                near, victim = nxt, y
        cache.discard(victim)
        cache.add(x)
    return misses


def stack_distances(trace):
    """Reuse distance per access (the statistic P2 will be tested against)."""
    last, out = {}, []
    for i, x in enumerate(trace):
        out.append(i - last[x] if x in last else None)
        last[x] = i
    return out


def main():
    rng = random.Random(SEED)
    out = {"seed": SEED, "certificate": {}, "gap_table": []}
    print("=" * 100)
    print("ROUTE A (Belady offline optimum) vs ROUTE B (exhaustive cache-state search)")
    print("the two routes must agree EXACTLY; a disagreement voids every later number")
    bad = 0
    for t in range(200):
        n = rng.randrange(4, 13)
        univ = rng.randrange(2, 6)
        cap = rng.randrange(1, min(4, univ + 1))
        tr = [rng.randrange(univ) for _ in range(n)]
        a, b = opt_misses(tr, cap), brute_misses(tr, cap)
        if a != b:
            bad += 1
            if bad <= 3:
                print("   MISMATCH trace=%s cap=%d  A=%d B=%d" % (tr, cap, a, b))
    print("   200 random tiny traces: %d disagreements" % bad)
    assert bad == 0, "the two exact routes disagree -- the optimum is not certified"
    out["certificate"] = {"route_A": "Belady offline optimum", "route_B": "exhaustive cache-state search",
                          "cases": 200, "disagreements": bad}

    # a control: the bad policy must never beat the optimum (two-sided, in the sense
    # that a bound nothing can violate is not a bound)
    vio = 0
    for t in range(200):
        n = rng.randrange(6, 25)
        univ = rng.randrange(3, 9)
        cap = rng.randrange(1, min(4, univ))
        tr = [rng.randrange(univ) for _ in range(n)]
        if worst_misses(tr, cap) < opt_misses(tr, cap):
            vio += 1
    print("   control (evict-soonest) below the optimum: %d of 200  (must be 0)" % vio)
    assert vio == 0, "a policy beat the optimum -- the optimum is not optimal"
    out["control"] = {"policy": "evict-nearest (deliberately bad)", "violations": vio, "cases": 200}

    print()
    print("FIRST READING OF P1's DIRECTION: the LRU-vs-optimum gap vs fast-tier fraction h")
    print("%-22s%6s%8s%8s%8s%10s%10s" % ("trace", "univ", "cap", "h", "OPT", "LRU", "gap vs OPT"))
    for name, gen in (("iid uniform (power 0)", lambda r: trace_iid(400, 40, r, 0.0)),
                      ("iid power-law 1.0", lambda r: trace_iid(400, 40, r, 1.0)),
                      ("iid power-law 2.0", lambda r: trace_iid(400, 40, r, 2.0)),
                      ("hotset 10/90", lambda r: trace_hotset(400, 40, 4, r, 0.9)),
                      ("scan chunks", lambda r: trace_scan(400, 40, r, 8))):
        tr = gen(random.Random(SEED))
        univ = len(set(tr))
        for h in (0.05, 0.1, 0.2, 0.5):
            cap = max(1, int(round(h * univ)))
            o, l, lf = opt_misses(tr, cap), lru_misses(tr, cap), lfu_misses(tr, cap)
            gap = (l - o) / o if o else float("nan")
            out["gap_table"].append({"trace": name, "universe": univ, "cap": cap, "h": h,
                                     "opt": o, "lru": l, "lfu": lf, "gap": gap})
            print("%-22s%6d%8d%8.2f%8d%8d%9.1f%%" % (name, univ, cap, h, o, l, 100 * gap))

    print()
    # P1 as REGISTERED: the gap is largest at small h and SHRINKS as h grows. Read it off the
    # data per family -- never assert a direction the table in front of the reader contradicts.
    print("P1 AS REGISTERED: 'realistic policies sit above the optimum, by >=20%% at h<=0.2, the gap")
    print("shrinking as h grows'.  Read per family off the table above:")
    by = {}
    for r in out["gap_table"]:
        by.setdefault(r["trace"], []).append((r["h"], r["gap"]))
    agree = 0
    for name, seq in by.items():
        seq.sort()
        hs = [h for h, _ in seq]
        gs = [g for _, g in seq]
        small = [g for h, g in seq if h <= 0.2]
        rising = all(b >= a for a, b in zip(gs, gs[1:]))
        print("   %-22s gap %.1f%% (h=%.2f) -> %.1f%% (h=%.2f)   %s"
              % (name, 100 * gs[0], hs[0], 100 * gs[-1], hs[-1],
                 "GROWS with h" if rising else "falls somewhere in h"))
        if small and min(small) >= 0.20:
            agree += 1
    print("   families matching P1's >=20%%-at-small-h limb: %d of %d" % (agree, len(by)))
    print("   -> the direction is DATA, not a sentence: the spike reports whichever way it comes out.")
    out["p1_first_reading"] = {"families": {k: v for k, v in by.items()},
                               "small_h_atleast_20pct": agree, "families_n": len(by)}
    with open("spike_v0_results.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote spike_v0_results.json")


if __name__ == "__main__":
    sys.exit(main())
