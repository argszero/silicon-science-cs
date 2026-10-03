#!/usr/bin/env python3
"""issue #120 spike_v1 -- THE CELL GRID: the deciding run for P1, and a first look at P2.

spike_v0 took one reading on short traces (n=400, one seed per cell).  It certified the
optimum (two routes, 0/200 disagreements) and produced a preliminary contradiction of P1's
registered direction: the LRU-vs-OPTIMUM gap GREW with the fast-tier fraction h in 3 of 5
families, where P1 predicts it shrinks.  This file is the deciding run.

What it adds:
  * an EFFICIENT exact optimum (lazy max-heap over next-use positions, O(n log n)), certified
    in this same run against the naive Belady scan AND the exhaustive cache-state search --
    so the grid can run at n = 50000;
  * a grid over (trace family, h, seed) with >= 3 seeds per cell, reporting the mean;
  * three deployed-typical policies (LRU, LFU, SRRIP), not LRU alone;
  * the reuse-distance summary that P2 is tested against, computed per trace.

P1's verdict is COMPUTED at print time, never typed.

Run: /usr/bin/python3 spike_v1.py     ->  spike_v1_results.json
"""
import json
import math
import random
import sys
from functools import lru_cache

SEED0 = 20261003
N = 50000           # trace length
UNIV = 2000         # universe of distinct items
SEEDS = 3           # independent seeds per cell
HS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5]
INF = float("inf")


# ------------------------------------------------------------------ traces
def _power_law_cdf(univ, power):
    w = [1.0 / ((i + 1) ** power) for i in range(univ)]
    s = sum(w)
    cum, acc = [], 0.0
    for x in w:
        acc += x / s
        cum.append(acc)
    return cum


def _sample_cdf(cum, rng):
    r = rng.random()
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if r <= cum[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def trace_uniform(n, univ, rng):
    return [rng.randrange(univ) for _ in range(n)]


def trace_powerlaw(n, univ, rng, power):
    cum = _power_law_cdf(univ, power)
    return [_sample_cdf(cum, rng) for _ in range(n)]


def trace_hotset(n, univ, rng, hot_frac, p_hot):
    hot = max(1, int(hot_frac * univ))
    return [rng.randrange(hot) if rng.random() < p_hot else rng.randrange(univ)
            for _ in range(n)]


def trace_scan(n, univ, rng, chunk):
    out = []
    while len(out) < n:
        s = rng.randrange(univ)
        out.extend((s + k) % univ for k in range(chunk))
    return out[:n]


FAMILIES = {
    "uniform": lambda r: trace_uniform(N, UNIV, r),
    "powerlaw1": lambda r: trace_powerlaw(N, UNIV, r, 1.0),
    "powerlaw2": lambda r: trace_powerlaw(N, UNIV, r, 2.0),
    "hotset": lambda r: trace_hotset(N, UNIV, r, 0.01, 0.9),
    "scan8": lambda r: trace_scan(N, UNIV, r, 8),
    "scan64": lambda r: trace_scan(N, UNIV, r, 64),
}


# ------------------------------------------------------------------ optimum, route A (naive)
def opt_naive(trace, cap):
    cache, misses = set(), 0
    for i, x in enumerate(trace):
        if x in cache:
            continue
        misses += 1
        if len(cache) < cap:
            cache.add(x)
            continue
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


# ------------------------------------------------------------------ optimum, route B (exhaustive)
def opt_brute(trace, cap):
    n = len(trace)

    @lru_cache(maxsize=None)
    def best(i, cache):
        if i == n:
            return 0
        x = trace[i]
        if x in cache:
            return best(i + 1, cache)
        if len(cache) < cap:
            return 1 + best(i + 1, tuple(sorted(cache + (x,))))
        return 1 + min(best(i + 1, tuple(sorted(tuple(y for y in cache if y != v) + (x,))))
                       for v in cache)

    return best(0, ())


# ------------------------------------------------------------------ optimum, route C (lazy heap, fast)
def next_use_array(trace):
    n = len(trace)
    nxt = [INF] * n
    last = {}
    for i in range(n - 1, -1, -1):
        x = trace[i]
        nxt[i] = last.get(x, INF)
        last[x] = i
    return nxt


def opt_heap(trace, cap):
    """Belady exactly, O(n log n): evict the cached item with the farthest next use.

    Lazy heap -- an entry is valid only if its stamp is the one currently scheduled for
    its item; a hit re-schedules the item, invalidating the old entry, which is what keeps
    the heap's top equal to the true farthest next use.
    """
    import heapq
    nxt = next_use_array(trace)
    heap, sched, cache = [], {}, set()
    stamp = 0
    misses = 0
    for i, x in enumerate(trace):
        stamp += 1
        if x in cache:
            sched[x] = stamp
            heapq.heappush(heap, (-nxt[i], x, stamp))
            continue
        misses += 1
        if len(cache) >= cap:
            while True:
                _, y, st = heapq.heappop(heap)
                if y in cache and sched.get(y) == st:
                    break
            cache.discard(y)
            del sched[y]
        cache.add(x)
        sched[x] = stamp
        heapq.heappush(heap, (-nxt[i], x, stamp))
    return misses


# ------------------------------------------------------------------ policies
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


def rrip_misses(trace, cap):
    """SRRIP: 2-bit re-reference interval prediction (insert distant, hit promotes)."""
    rrpv, misses = {}, 0
    for x in trace:
        if x in rrpv:
            rrpv[x] = 0
            continue
        misses += 1
        if len(rrpv) < cap:
            rrpv[x] = 2
            continue
        while True:
            victim = next((y for y, v in rrpv.items() if v == 3), None)
            if victim is None:
                for y in rrpv:
                    rrpv[y] = min(3, rrpv[y] + 1)
                continue
            break
        del rrpv[victim]
        rrpv[x] = 2
    return misses


POLICIES = {"LRU": lru_misses, "LFU": lfu_misses, "SRRIP": rrip_misses}


# ------------------------------------------------------------------ workload statistics
def reuse_distances(trace):
    last, out = {}, []
    for i, x in enumerate(trace):
        out.append(i - last[x] if x in last else None)
        last[x] = i
    return out


def stats(trace):
    """The candidate 'one statistics' P2 is tested against, all from one pass."""
    rd = [d for d in reuse_distances(trace) if d is not None]
    if not rd:
        return {"n_reuse": 0, "mean_rd": 0.0, "median_rd": 0, "slope": 0.0, "head_mass": 0.0}
    rd.sort()
    m = len(rd)
    pts = []
    for q in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        d = rd[min(m - 1, int(q * m))]
        if d > 1:
            pts.append((math.log(d), math.log(max(1e-12, 1.0 - q))))
    if len(pts) >= 3:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = sum((a - mx) ** 2 for a in xs)
        slope = -(num / den) if den > 0 else 0.0
    else:
        slope = 0.0
    return {"n_reuse": m, "mean_rd": sum(rd) / m, "median_rd": rd[m // 2],
            "slope": slope, "head_mass": sum(1 for d in rd if d <= 1) / m}


# ------------------------------------------------------------------ main
def certify():
    print("=" * 104)
    print("CERTIFICATE: route A (naive Belady) vs route B (exhaustive) vs route C (lazy heap)")
    rng = random.Random(SEED0)
    badA = badC = 0
    for _ in range(300):
        n = rng.randrange(4, 13)
        univ = rng.randrange(2, 6)
        cap = rng.randrange(1, min(4, univ + 1))
        tr = [rng.randrange(univ) for _ in range(n)]
        a, b, c = opt_naive(tr, cap), opt_brute(tr, cap), opt_heap(tr, cap)
        if a != b:
            badA += 1
        if c != b:
            badC += 1
            if badC <= 3:
                print("   route C MISMATCH trace=%s cap=%d  C=%d B=%d" % (tr, cap, c, b))
    print("   300 tiny traces: naive-vs-exhaustive = %d ; heap-vs-exhaustive = %d"
          % (badA, badC))
    assert badA == 0 and badC == 0, "an exact route disagrees -- the optimum is not certified"
    tr = [rng.randrange(200) for _ in range(4000)]
    gs_cells = 0
    for cap in (5, 40, 200):
        a, c = opt_naive(tr, cap), opt_heap(tr, cap)
        assert a == c, "naive and heap disagree at n=4000 cap=%d (%d vs %d)" % (cap, a, c)
        gs_cells += 1
    print("   at n=4000, cap in {5,40,200}: naive == heap EXACTLY")
    return {"cases": 300, "naive_vs_exhaustive": badA, "heap_vs_exhaustive": badC,
            "grid_scale_equal": True, "grid_scale_cells": gs_cells,
            "grid_scale": "naive == heap at n=4000 for cap in {5,40,200}"}


def main():
    out = {"seed0": SEED0, "n": N, "universe": UNIV, "seeds": SEEDS, "h_grid": HS, "cells": []}
    out["certificate"] = certify()

    print()
    print("=" * 104)
    print("THE CELL GRID -- each policy's misses and its gap above the EXACT optimum, %d seeds/cell"
          % SEEDS)
    print("%-10s%7s%7s%8s%8s%10s%10s%10s%10s%10s%10s"
          % ("family", "h", "cap", "W", "h/W", "OPT", "LRU", "LFU", "SRRIP", "gapLRU", "gapSRRIP"))
    for fam, gen in FAMILIES.items():
        for h in HS:
            cap = max(1, int(round(h * UNIV)))
            run = {"family": fam, "h": h, "cap": cap,
                   "opt": [], "LRU": [], "LFU": [], "SRRIP": [], "stat": [], "distinct": []}
            for s in range(SEEDS):
                rng = random.Random(SEED0 + 1000 * list(FAMILIES).index(fam) + 7 * s)
                tr = gen(rng)
                assert len(tr) == N
                run["opt"].append(opt_heap(tr, cap))
                for nm, fn in POLICIES.items():
                    run[nm].append(fn(tr, cap))
                run["stat"].append(stats(tr))
                run["distinct"].append(len(set(tr)))
            mean = lambda k: sum(run[k]) / len(run[k])
            gl = mean("LRU") / mean("opt") - 1.0
            gr = mean("SRRIP") / mean("opt") - 1.0
            run["gap_LRU"], run["gap_SRRIP"] = gl, gr
            run["W"] = mean("distinct")
            # the EFFECTIVE capacity normalisation: W is the number of distinct items the
            # trace actually touches, which for a heavy-tailed workload is far below UNIV.
            run["h_eff"] = cap / run["W"]
            print("%-10s%7.2f%7d%8.0f%8.3f%10.0f%10.0f%10.0f%10.0f%9.1f%%%9.1f%%"
                  % (fam, h, cap, run["W"], run["h_eff"], mean("opt"), mean("LRU"), mean("LFU"),
                     mean("SRRIP"), 100 * gl, 100 * gr))
            out["cells"].append(run)

    print()
    print("=" * 104)
    print("P1 AS REGISTERED: 'a policy sits strictly above the optimum, by >=20% at h <= 0.2, and the")
    print("gap SHRINKS as h grows'.  Two limbs, each checked separately -- the verdict is computed:")
    both = 0
    for fam in FAMILIES:
        seq = sorted([c for c in out["cells"] if c["family"] == fam], key=lambda c: c["h"])
        gs, hs = [c["gap_LRU"] for c in seq], [c["h"] for c in seq]
        atsmall = [c["gap_LRU"] for c in seq if c["h"] <= 0.2]
        limb_a = bool(atsmall) and min(atsmall) >= 0.20          # >=20% at small h
        limb_b = all(b <= a + 1e-12 for a, b in zip(gs, gs[1:]))  # SHRINKING (non-increasing)
        both += 1 if (limb_a and limb_b) else 0
        print("   %-10s gap %6.1f%% (h=%.2f) -> %6.1f%% (h=%.2f)   limb_a(>=20%%@h<=.2)=%-5s "
              "limb_b(shrinking)=%-5s" % (fam, 100 * gs[0], hs[0], 100 * gs[-1], hs[-1],
                                          limb_a, limb_b))
    verdict = "REFUTED" if both < len(FAMILIES) else "CONFIRMED"
    print("   families satisfying BOTH limbs: %d of %d" % (both, len(FAMILIES)))
    print("   -> P1 AS REGISTERED: %s" % verdict)
    out["p1_verdict"] = {"families_both_limbs": both, "families_n": len(FAMILIES),
                         "verdict": verdict}

    print()
    print("WHY the direction differs -- computed, not asserted.  The gap is a ratio of two")
    print("quantities that each fall with capacity, so its direction is set by WHICH falls faster.")
    print("   %-10s%14s%16s%10s" % ("family", "phi* x-drop", "phiLRU x-drop", "gap"))
    for fam in FAMILIES:
        seq = sorted([c for c in out["cells"] if c["family"] == fam], key=lambda c: c["h"])
        p_opt = [sum(c["opt"]) / len(c["opt"]) / N for c in seq]
        p_lru = [sum(c["LRU"]) / len(c["LRU"]) / N for c in seq]
        ro = p_opt[0] / max(1e-12, p_opt[-1])
        rl = p_lru[0] / max(1e-12, p_lru[-1])
        # gap = phiLRU/phi* - 1, so gap_end/gap_start = ro/rl: the gap GROWS iff the OPTIMUM
        # improves faster than the policy, i.e. iff ro > rl.  Asserted against the endpoint
        # difference computed from the SAME cells, so a flipped comparison fails the run
        # rather than printing a verdict beside a table that contradicts it.
        grows = ro > rl
        g_start = p_lru[0] / max(1e-12, p_opt[0])
        g_end = p_lru[-1] / max(1e-12, p_opt[-1])
        assert grows == (g_end > g_start), \
            "%s: mechanism says %s but the endpoints say the reverse" % (fam, grows)
        print("   %-10s%14.1f%16.1f%10s" % (fam, ro, rl, "GROWS" if grows else "shrinks"))
    print("   -> the gap grows exactly when the OPTIMUM improves faster than the policy does: the")
    print("      mechanism is how much freedom the clairvoyant has, a property of the workload.")
    print()
    print("And the denominator in 'h' is not pinned by the registration -- W = the distinct items")
    print("the trace ACTUALLY touches, which for a heavy-tailed workload is far below the universe:")
    print("   %-10s%10s%10s%12s" % ("family", "W", "cap@h=.5", "h_eff@h=.5"))
    mono_h = mono_e = 0
    for fam in FAMILIES:
        seq = sorted([c for c in out["cells"] if c["family"] == fam], key=lambda c: c["h"])
        gs = [c["gap_LRU"] for c in seq]
        if all(b >= a - 1e-12 for a, b in zip(gs, gs[1:])):
            mono_h += 1
        seqe = sorted([c for c in out["cells"] if c["family"] == fam], key=lambda c: c["h_eff"])
        gse = [c["gap_LRU"] for c in seqe]
        if all(b >= a - 1e-12 for a, b in zip(gse, gse[1:])):
            mono_e += 1
        last = seq[-1]
        print("   %-10s%10.0f%10d%12.3f" % (fam, last["W"], last["cap"], last["h_eff"]))
    print("   families whose gap is non-decreasing: %d of %d under h = cap/UNIVERSE, %d of %d "
          "under h_eff = cap/W" % (mono_h, len(FAMILIES), mono_e, len(FAMILIES)))
    out["p1_normalisation"] = {"monotone_h": mono_h, "monotone_h_eff": mono_e,
                               "families_n": len(FAMILIES)}

    print()
    print("=" * 104)
    print("A FIRST LOOK AT P2 -- can the ceiling phi* be carried by ONE statistic?")
    print("   %-10s%8s%12s%10s%10s%10s" % ("family", "h", "phi*", "slope", "mean_rd", "head_mass"))
    for c in out["cells"]:
        st = c["stat"][0]
        phi = sum(c["opt"]) / len(c["opt"]) / N
        print("   %-10s%8.2f%12.4f%10.3f%10.1f%10.3f"
              % (c["family"], c["h"], phi, st["slope"], st["mean_rd"], st["head_mass"]))
    # is phi* a function of the slope alone?  compare cells that SHARE a slope but differ in
    # family -- if one statistic carried the ceiling, equal slopes would give equal phi*
    by_slope = {}
    for c in out["cells"]:
        s = round(c["stat"][0]["slope"], 1)
        by_slope.setdefault(s, []).append((c["family"], c["h"], sum(c["opt"]) / len(c["opt"]) / N))
    coll = {k: v for k, v in by_slope.items() if len({x[0] for x in v}) > 1}
    spread = []
    for k, v in coll.items():
        phis = [x[2] for x in v]
        spread.append((k, min(phis), max(phis), max(phis) / max(1e-12, min(phis)) - 1))
    print()
    print("   COLLISIONS -- a slope shared by >1 family, with the phi* the cells then carry:")
    if spread:
        for k, lo, hi, rel in spread[:8]:
            print("      slope~%5.1f : phi* %.4f .. %.4f  (spread %.1f%%)" % (k, lo, hi, 100 * rel))
        worst = max(spread, key=lambda t: t[3])
        print("   -> worst collision spread %.1f%%: the slope does NOT carry the ceiling alone"
              % (100 * worst[3]))
        out["p2_first_look"] = {"collisions": len(coll), "worst_spread": worst[3],
                                "verdict": "slope alone does not carry phi*"}
    else:
        print("      none among these cells (the statistic may still be insufficient -- widen the grid)")
        out["p2_first_look"] = {"collisions": 0, "verdict": "no collision observed"}

    with open("spike_v1_results.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote spike_v1_results.json")


if __name__ == "__main__":
    sys.exit(main())
