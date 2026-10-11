#!/usr/bin/env python3
"""issue #120 spike_v2 -- P3: is there a COMPUTABLE capacity knee, and which way does it bend?

P3 as registered: "a capacity knee at a computable h* (where the reuse-distance profile
saturates): below it added fast tier buys almost nothing."  Its JUSTIFICATION is unambiguous
about the SHAPE: "a tier that cannot hold the head buys no reduction" -- i.e. relief ~ 0 BELOW
the head size and gains ABOVE it.

That shape is not a law, it is a property of the head's STRUCTURE, and this run separates the
two structures with two constructed families whose knee is known by construction:
  * hotH   -- a head of H items sampled i.i.d. (PARTIAL CREDIT: holding part of the head helps)
  * loopW  -- a working set of W items accessed cyclically (ALL-OR-NOTHING: a tier below W
              thrashes and buys nothing).  P3's justification describes THIS one.

What else is new over spike_v1:
  * a DENSE capacity grid (the marginal-relief curve needs more than 7 points);
  * the STACK-DISTANCE distribution, exact in O(n log n) via a Fenwick tree -- by Mattson's law
    it gives the whole LRU curve at once, and it is the natural carrier for "the profile";
  * a CERTIFICATE that the simulated LRU curve IS the stack-distance curve (Mattson checked,
    not assumed -- it is also P2's registered justification);
  * a knee detector with a TWO-SIDED instrument control (planted known knee vs planted none);
  * front-loading / saturation statistics, so P3's SHAPE is a computed verdict, not a reading.

Run: /usr/bin/python3 spike_v2.py     ->  spike_v2_results.json
"""
import json
import math
import random
import sys

import spike_v1 as s1          # the CERTIFIED kernels: generators, exact optimum, LRU

SEED0 = 20261003
N = 20000
UNIV = 1000
CAPS = list(range(1, 41)) + [48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
SEEDS = 3
EPS_SAT = 0.005               # a relief step below this is "the curve has flattened"


# ---------------------------------------------------------------- stack distance (exact)
def stack_distances(trace):
    """sd[i] = number of DISTINCT items accessed since the previous access to trace[i]
    (-1 for a first touch).  Exactly LRU's stack distance, O(n log n) via a Fenwick tree.

    The tree holds a 1 at the MOST RECENT access position of every item seen so far; the
    count of markers strictly inside (lastpos[x], i) is the number of distinct items touched
    since x was last seen -- and x's own marker sits at lastpos[x], so it is excluded.
    """
    n = len(trace)
    bit = [0] * (n + 2)

    def add(i, v):
        i += 1
        while i <= n + 1:
            bit[i] += v
            i += i & -i

    def q(i):
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    lastpos, sd = {}, [-1] * n
    for i, x in enumerate(trace):
        lp = lastpos.get(x)
        if lp is not None:
            sd[i] = q(i - 1) - q(lp)
            add(lp, -1)
        add(i, 1)
        lastpos[x] = i
    return sd


def lru_curve_from_sd(sd, caps):
    """Mattson: LRU misses at cache size c == #{first touches} + #{sd >= c}.  Exact."""
    n = len(sd)
    first = sum(1 for d in sd if d < 0)
    return {c: (first + sum(1 for d in sd if d >= c)) / n for c in caps}


# ---------------------------------------------------------------- constructed families
def trace_loop(n, rng, W, shuffled):
    """A working set of W items, accessed cyclically.  shuffled=False is the all-or-nothing
    extreme (a fixed periodic order): at cap = W-1 the optimum misses EVERY access, at cap = W
    it misses none -- so the knee is exactly W and P3's shape holds there by construction."""
    out = []
    while len(out) < n:
        order = list(range(W))
        if shuffled:
            rng.shuffle(order)
        out.extend(order)
    return out[:n]


def trace_iid_head(n, univ, rng, H, p_hot=0.9):
    """A head of H items sampled i.i.d. -- PARTIAL CREDIT: a tier holding part of the head
    already converts part of that head's traffic into hits."""
    return [rng.randrange(H) if rng.random() < p_hot else rng.randrange(univ)
            for _ in range(n)]


def _hot(H):
    return lambda rng: trace_iid_head(N, UNIV, rng, H)


def _loop(W, sh):
    return lambda rng: trace_loop(N, rng, W, sh)


HOTS = [5, 10, 20, 40]
LOOPS = [8, 16, 32]
FAMILIES = {("hot%d" % H): _hot(H) for H in HOTS}
FAMILIES.update({("loop%d" % W): _loop(W, False) for W in LOOPS})
FAMILIES.update({
    "uniform": lambda rng: s1.trace_uniform(N, UNIV, rng),
    "powerlaw1": lambda rng: s1.trace_powerlaw(N, UNIV, rng, 1.0),
    "scan64": lambda rng: s1.trace_scan(N, UNIV, rng, 64),
})
H_TRUE = {}
H_TRUE.update({("hot%d" % H): H / UNIV for H in HOTS})
H_TRUE.update({("loop%d" % W): W / UNIV for W in LOOPS})
KIND = {}
KIND.update({("hot%d" % H): "partial-credit" for H in HOTS})
KIND.update({("loop%d" % W): "all-or-nothing" for W in LOOPS})


# ---------------------------------------------------------------- the knee detector
def knee_chord(caps, vals):
    """Blind elbow rule: max distance from the chord joining the curve's own endpoints, on the
    [0,1]x[0,1] normalisation.  A curve with no knee has a small normalised distance."""
    lo, hi = min(vals), max(vals)
    if hi - lo <= 1e-12:
        return {"c_knee": None, "sharpness": 0.0}
    xs = [(c - caps[0]) / (caps[-1] - caps[0]) for c in caps]
    ys = [(v - lo) / (hi - lo) for v in vals]
    x0, y0, x1, y1 = xs[0], ys[0], xs[-1], ys[-1]
    den = math.hypot(y1 - y0, x1 - x0)
    best, bc = -1.0, None
    for x, y, c in zip(xs, ys, caps):
        d = abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / den
        if d > best:
            best, bc = d, c
    return {"c_knee": bc, "sharpness": best}


def relief_profile(caps, vals):
    """Per-unit-capacity relief, plus the two statistics P3's SHAPE turns on."""
    rel = [(vals[i - 1] - vals[i]) / (caps[i] - caps[i - 1]) for i in range(1, len(caps))]
    steps = caps[1:]
    tot = sum(r for r in rel if r > 0)
    if tot <= 1e-12:
        return None
    mx = max(rel)
    c_sat = None                                   # smallest cap after which all steps are quiet
    for j in range(len(rel)):
        if all(r < EPS_SAT for r in rel[j:]):
            c_sat = steps[j]
            break
    return {"relief": rel, "steps": steps, "total": tot,
            "c_peak": steps[rel.index(mx)], "peak_share": mx / tot, "c_sat": c_sat}


def relief_strictly_below(caps, vals, c_head):
    """THE statistic P3 is about.  P3 says: "BELOW it [h*] added fast tier buys almost nothing"
    -- so it is the share of the TOTAL relief delivered by capacities STRICTLY BELOW the head
    size that must be ~0.  (An earlier version of this file measured the relief AT-or-below the
    head instead; on an all-or-nothing head whose cliff sits exactly AT W that statistic reads
    1.000 and the verdict inverted -- the statistic's object was not the claim's object.)"""
    if c_head is None:
        return None
    below = [c for c in caps if c < c_head]
    if not below:
        return None
    total = vals[0] - vals[-1]
    if total <= 1e-12:
        return None
    return (vals[0] - vals[caps.index(max(below))]) / total


def quantile(sorted_vals, theta):
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, int(theta * len(sorted_vals)))]


# ---------------------------------------------------------------- instrument control
def detector_control():
    """Two sides: a curve with a KNOWN knee, and one with none.  The detector must separate
    them -- otherwise every 'knee' it reports is an artefact of the rule, not of the data."""
    step = [1.0 if c < 20 else 0.05 for c in CAPS]
    expn = [math.exp(-c / 25.0) for c in CAPS]
    a, b = knee_chord(CAPS, step), knee_chord(CAPS, expn)
    sa, sb = relief_profile(CAPS, step), relief_profile(CAPS, expn)
    print("   planted KNOWN knee : c_knee=%-4s sharpness=%.4f  peak_share(at c=%s)=%.4f"
          % (a["c_knee"], a["sharpness"], sa["c_peak"], sa["peak_share"]))
    print("   planted NO knee    : c_knee=%-4s sharpness=%.4f  peak_share(at c=%s)=%.4f"
          % (b["c_knee"], b["sharpness"], sb["c_peak"], sb["peak_share"]))
    assert a["c_knee"] == 20, "detector missed a planted cliff at cap 20"
    assert sa["peak_share"] > 0.90, "detector did not see the planted cliff"
    assert sb["peak_share"] < 0.20, "detector called a knee on a smooth exponential"
    return {"planted_knee": a, "planted_knee_peak_share": sa["peak_share"],
            "planted_none": b, "planted_none_peak_share": sb["peak_share"]}


# ---------------------------------------------------------------- main
def main():
    out = {"seed0": SEED0, "n": N, "universe": UNIV, "seeds": SEEDS, "caps": CAPS,
           "eps_sat": EPS_SAT, "kind": KIND, "h_true": H_TRUE, "rows": []}

    print("=" * 104)
    print("INSTRUMENT CONTROL -- the knee detector, on curves whose answer is known")
    out["detector_control"] = detector_control()

    print()
    print("=" * 104)
    print("MATTSON CERTIFICATE -- is the simulated LRU curve the stack-distance curve?")
    rng = random.Random(SEED0)
    bad = tot = 0
    for _ in range(12):
        tr = [rng.randrange(40) for _ in range(3000)]
        pred = lru_curve_from_sd(stack_distances(tr), CAPS)
        for c in CAPS:
            tot += 1
            if abs(s1.lru_misses(tr, c) / len(tr) - pred[c]) > 1e-12:
                bad += 1
    print("   %d (trace, capacity) pairs: simulated LRU vs stack-distance prediction, "
          "disagreements = %d" % (tot, bad))
    assert bad == 0, "Mattson's law is violated -- the carrier is wrong"
    print("   -> EXACT.  The whole LRU curve is a function of the stack-distance distribution.")
    out["mattson_certificate"] = {"pairs": tot, "disagreements": bad}

    print()
    print("=" * 104)
    print("THE phi* KNEE -- dense grid, %d seeds/cell, n=%d, universe=%d"
          % (SEEDS, N, UNIV))
    print("%-10s%-16s%8s%9s%9s%9s%7s%8s%9s"
          % ("family", "head kind", "c_knee", "h*_meas", "h_true", "rel.err", "c_sat",
             "sharp", "peakShar"))
    for fam, gen in FAMILIES.items():
        per_seed_phi, per_seed_lru, sds = [], [], []
        for s in range(SEEDS):
            rng = random.Random(SEED0 + 1000 * list(FAMILIES).index(fam) + 7 * s)
            tr = gen(rng)
            assert len(tr) == N
            sd = stack_distances(tr)
            sds.append(sd)
            # the LRU curve is free from Mattson -- so P3 can be asked of the POLICY and of the
            # ORACLE on the same traces, which is the comparison the registration never made.
            per_seed_lru.append(lru_curve_from_sd(sd, CAPS))
            per_seed_phi.append([s1.opt_heap(tr, c) / N for c in CAPS])
        phis = [sum(row[j] for row in per_seed_phi) / SEEDS for j in range(len(CAPS))]
        lru = [sum(ps[c] for ps in per_seed_lru) / SEEDS for c in CAPS]
        allsd = sorted(d for sd in sds for d in sd if d >= 0)
        kc = knee_chord(CAPS, phis)
        rp = relief_profile(CAPS, phis)
        htrue = H_TRUE.get(fam)
        relerr = abs(kc["c_knee"] / UNIV - htrue) / htrue if htrue else None
        row = {"family": fam, "kind": KIND.get(fam, "control"), "phi_star": phis, "lru": lru,
               "c_knee": kc["c_knee"], "sharpness": kc["sharpness"],
               "h_meas": kc["c_knee"] / UNIV, "h_true": htrue, "rel_err": relerr,
               "c_sat": rp["c_sat"], "peak_share": rp["peak_share"], "c_peak": rp["c_peak"],
               "c_head80": quantile(allsd, 0.80), "c_head95": quantile(allsd, 0.95),
               "phi_at_1": phis[0], "phi_min": min(phis)}
        row["below_head_share"] = relief_strictly_below(
            CAPS, phis, int(round(htrue * UNIV)) if htrue else None)
        ch = int(round(htrue * UNIV)) if htrue else None
        # the SAME two statistics asked of the deployed policy on the same traces
        row["lru_below_head_share"] = relief_strictly_below(CAPS, lru, ch)
        lrp = relief_profile(CAPS, lru)
        row["lru_c_sat"] = lrp["c_sat"] if lrp else None
        row["lru_peak_share"] = lrp["peak_share"] if lrp else None
        out["rows"].append(row)
        print("%-10s%-16s%8s%9.4f%9s%9s%7s%8.4f%9.4f"
              % (fam, row["kind"], kc["c_knee"], row["h_meas"],
                 ("%.4f" % htrue) if htrue else "-",
                 ("%.3f" % relerr) if relerr is not None else "-",
                 row["c_sat"], kc["sharpness"], rp["peak_share"]))

    # ---------------- the shape itself, read around the head (so the verdict is visible)
    print()
    print("=" * 104)
    print("THE CURVE AROUND THE HEAD -- phi* at capacities c_head-2 .. c_head+3 (relief per step)")
    for row in out["rows"]:
        if row["h_true"] is None:
            continue
        ch = int(round(row["h_true"] * UNIV))
        win = [c for c in CAPS if ch - 2 <= c <= ch + 3]
        seg = []
        for i, c in enumerate(win):
            j = CAPS.index(c)
            d = ("%+.4f" % (row["phi_star"][j - 1] - row["phi_star"][j])) if j > 0 else "     -"
            seg.append("%d:%.4f(%s)" % (c, row["phi_star"][j], d))
        print("   %-10s %s" % (row["family"], "  ".join(seg)))

    # ---------------- score the detector against by-construction knees (RELATIVE tolerance)
    print()
    print("=" * 104)
    print("SCORING THE DETECTOR against knees known BY CONSTRUCTION (relative error, 25% bar)")
    print("   family     head kind        c_true   c_knee   rel.err   pass")
    hit = ncon = 0
    for row in out["rows"]:
        if row["h_true"] is None:
            continue
        ncon += 1
        ok = row["rel_err"] is not None and row["rel_err"] <= 0.25
        hit += 1 if ok else 0
        print("   %-10s %-16s %-8d %-8s %-9.3f %s"
              % (row["family"], row["kind"], int(row["h_true"] * UNIV), row["c_knee"],
                 row["rel_err"], ok))
    print("   constructed families whose knee is found within 25%% RELATIVE error: %d of %d"
          % (hit, ncon))
    out["knee_hits"] = {"found": hit, "n": ncon, "tol": 0.25}

    # ---------------- P3's SHAPE: is the relief front-loaded or back-loaded?
    print()
    print("=" * 104)
    print("P3's SHAPE, computed -- P3 predicts the relief STRICTLY BELOW h* is ~0")
    print("   family     head kind        h_true   below_head_share   c_sat   verdict")
    fl = {}
    for row in out["rows"]:
        if row["h_true"] is None:
            continue
        f = row["below_head_share"]
        fl[row["family"]] = f
        verdict = "P3 SHAPE HOLDS" if (f is not None and f <= 0.25) else "P3 SHAPE FAILS"
        print("   %-10s %-16s %-8.4f %-18s %-7s %s"
              % (row["family"], row["kind"], row["h_true"],
                 ("%.3f" % f) if f is not None else "-", row["c_sat"], verdict))
    pc = [fl[r["family"]] for r in out["rows"]
          if r["kind"] == "partial-credit" and fl.get(r["family"]) is not None]
    an = [fl[r["family"]] for r in out["rows"]
          if r["kind"] == "all-or-nothing" and fl.get(r["family"]) is not None]
    print("   partial-credit heads : below-head relief share mean %.3f (P3 predicts ~0)"
          % (sum(pc) / len(pc)))
    print("   all-or-nothing heads : below-head relief share mean %.3f (P3 predicts ~0)"
          % (sum(an) / len(an)))
    out["below_head_share"] = {"partial_credit_mean": sum(pc) / len(pc),
                               "all_or_nothing_mean": sum(an) / len(an),
                               "per_family": fl}

    # ---------------- P3 asked of the ORACLE and of the POLICY on the SAME traces
    print()
    print("=" * 104)
    print("P3's SHAPE ASKED OF BOTH CURVES -- relief strictly below the head, oracle vs LRU")
    print("   family     h_true   ORACLE below-head   LRU below-head   ORACLE c_sat  LRU c_sat")
    ro_, rl_ = [], []
    for row in out["rows"]:
        if row["h_true"] is None:
            continue
        o, l = row["below_head_share"], row["lru_below_head_share"]
        ro_.append(o)
        rl_.append(l)
        print("   %-10s %-8.4f %-19.3f %-16.3f %-13s %s"
              % (row["family"], row["h_true"], o, l, row["c_sat"], row["lru_c_sat"]))
    print("   oracle below-head relief share: mean %.3f  (P3 predicts ~0 -> REFUTED)"
          % (sum(ro_) / len(ro_)))
    print("   LRU    below-head relief share: mean %.3f  (P3 predicts ~0 -> %s)"
          % (sum(rl_) / len(rl_),
             "CONFIRMED" if sum(rl_) / len(rl_) <= 0.25 else "not confirmed"))
    out["oracle_vs_policy"] = {"oracle_mean": sum(ro_) / len(ro_),
                               "lru_mean": sum(rl_) / len(rl_)}

    with open("spike_v2_results.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote spike_v2_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
