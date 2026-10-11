#!/usr/bin/env python3
"""issue #120 spike_v3 -- THE CORRECTED CAPACITY LAW.

R511 refuted P1 (the gap's direction) and P2's statistic.  R512 refuted P3 for the oracle and
showed the "knee" is the POLICY's thrashing cliff, not a feature of phi*.  What is left is the
construct itself: what shape does phi*(c) have, and can its SCALE be computed from the profile?

This run:
  * gives a WIDE family sweep (24 families: bounded cyclic working sets, iid head + cold tail,
    power laws, scan chunks, mixtures, uniform);
  * verifies an EXACT closed form on the bounded-working-set family -- phi*(c) is LINEAR,
    rate(c) = (W-c)/(W-1), which is a positive analytic result rather than a fit;
  * defines the relief SCALE scale-free: c_d = the smallest capacity delivering a fraction d of
    the trace's total possible relief (so no arbitrary absolute epsilon);
  * asks the corrected P3 question -- is c_d computable from the profile? -- with a TRAIN/TEST
    SPLIT over families, so a good fit on the training families cannot be mistaken for a law.

Run: /usr/bin/python3 spike_v3.py     ->  spike_v3_results.json
"""
import json
import math
import random
import sys

import spike_v1 as s1
import spike_v2 as s2

SEED0 = 20261003
N = 20000
UNIV = 1000
CAPS = list(range(1, 41)) + [48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
DELTAS = [0.5, 0.9, 0.99]


# ---------------------------------------------------------------- generators
def trace_mixture(n, univ, rng, H, p_hot):
    return [rng.randrange(H) if rng.random() < p_hot else rng.randrange(univ)
            for _ in range(n)]


FAMILIES = {}
for W in (4, 8, 16, 32, 64):
    FAMILIES["loop%d" % W] = ("cyclic", lambda r, W=W: s2.trace_loop(N, r, W, False))
for H in (5, 10, 20, 40):
    FAMILIES["hot%d" % H] = ("iid-head", lambda r, H=H: trace_mixture(N, UNIV, r, H, 0.9))
for H in (10, 40):
    FAMILIES["hot%dw" % H] = ("iid-head", lambda r, H=H: trace_mixture(N, UNIV, r, H, 0.5))
for pw in (0.5, 1.0, 1.5, 2.0, 3.0):
    FAMILIES["pow%s" % str(pw).replace(".", "")] = (
        "powerlaw", lambda r, pw=pw: s1.trace_powerlaw(N, UNIV, r, pw))
for ch in (4, 16, 64):
    FAMILIES["scan%d" % ch] = ("scan", lambda r, ch=ch: s1.trace_scan(N, UNIV, r, ch))
FAMILIES["uniform"] = ("uniform", lambda r: s1.trace_uniform(N, UNIV, r))
for H, p in ((8, 0.7), (8, 0.95), (32, 0.7), (32, 0.95)):
    FAMILIES["mix%d_%d" % (H, int(p * 100))] = (
        "mixture", lambda r, H=H, p=p: trace_mixture(N, UNIV, r, H, p))


# ---------------------------------------------------------------- relief scale
def relief_scale(caps, vals, delta):
    """scale-free: smallest capacity c with relief(c) >= delta * total relief, where
    relief(c) = vals[0] - vals(c) and total = vals[0] - vals(floor)."""
    floor = min(vals)
    total = vals[0] - floor
    if total <= 1e-12:
        return None
    for c, v in zip(caps, vals):
        if (vals[0] - v) >= delta * total:
            return c
    return caps[-1]


# ---------------------------------------------------------------- profile statistics
def sd_quantile(sds, theta):
    a = sorted(sds)
    return a[min(len(a) - 1, int(theta * len(a)))]


def topk_cover(trace, frac):
    """smallest number of distinct items whose accesses cover `frac` of the trace (the
    'hot set size' at that coverage) -- a computable profile statistic."""
    from collections import Counter
    cnt = Counter(trace)
    tot = len(trace)
    need = frac * tot
    acc = 0
    for k, (_item, c) in enumerate(cnt.most_common(), 1):
        acc += c
        if acc >= need:
            return k
    return len(cnt)


def main():
    out = {"seed0": SEED0, "n": N, "universe": UNIV, "caps": CAPS, "deltas": DELTAS,
           "families": list(FAMILIES), "rows": []}

    print("=" * 104)
    print("EXACT SHAPE ON THE BOUNDED WORKING SET -- is phi*(c) linear, rate = (W-c)/(W-1)?")
    print("   W     cap   phi*(c)      (W-c)/(W-1)   abs.err")
    maxerr = 0.0
    for W in (8, 16, 32):
        rng = random.Random(SEED0)
        tr = s2.trace_loop(N, rng, W, False)
        for c in (max(1, W // 2), max(1, W - 2), max(1, W - 1)):
            p = s1.opt_heap(tr, c) / N
            pred = (W - c) / (W - 1) if c < W else 0.0
            # the finite-trace form carries the W compulsory misses as a constant
            pred_fin = ((W - c) * (N - W) / (W - 1) + W) / N if c < W else W / N
            maxerr = max(maxerr, abs(p - pred_fin))
            print("   %-5d %-5d %-12.6f %-14.6f %.2e" % (W, c, p, pred_fin, abs(p - pred_fin)))
    print("   max |measured - closed form| over these cells: %.2e" % maxerr)
    assert maxerr < 1e-3, "the closed form for the cyclic family is wrong"
    out["closed_form"] = {"max_err": maxerr, "form": "phi*(c) = ((W-c)*(N-W)/(W-1) + W)/N"}
    print("   -> the bounded-working-set family has an EXACT closed form: linear in c.")

    print()
    print("=" * 104)
    print("THE FAMILY SWEEP -- relief scale of the ORACLE and of LRU on the same traces")
    print("%-11s%-11s%7s%7s%7s%9s%9s%9s%9s"
          % ("family", "kind", "D", "q50sd", "hs90", "c1/2", "c9/10", "c99/100", "lru c1/2"))
    for fam, (kind, gen) in FAMILIES.items():
        rng = random.Random(SEED0 + 1000 * list(FAMILIES).index(fam))
        tr = gen(rng)
        assert len(tr) == N
        sd = s2.stack_distances(tr)
        phis = [s1.opt_heap(tr, c) / N for c in CAPS]
        lru = [s2.lru_curve_from_sd(sd, CAPS)[c] for c in CAPS]
        sds = [d for d in sd if d >= 0]
        row = {"family": fam, "kind": kind, "D": len(set(tr)),
               "sd_q50": sd_quantile(sds, 0.5), "sd_q90": sd_quantile(sds, 0.9),
               "sd_q99": sd_quantile(sds, 0.99),
               "hs90": topk_cover(tr, 0.90), "hs95": topk_cover(tr, 0.95),
               "hs99": topk_cover(tr, 0.99), "hs50": topk_cover(tr, 0.50),
               "phi1": phis[0], "phi_floor": min(phis),
               "lru_floor": min(lru), "lru1": lru[0]}
        for d in DELTAS:
            row["c_%s" % d] = relief_scale(CAPS, phis, d)
            row["lru_c_%s" % d] = relief_scale(CAPS, lru, d)
        out["rows"].append(row)
        print("%-11s%-11s%7d%7d%7d%9s%9s%9s%9s"
              % (fam, kind, row["D"], row["sd_q50"], row["hs90"], row["c_0.5"],
                 row["c_0.9"], row["c_0.99"], row["lru_c_0.5"]))

    # ---------------- is c_d computable?  TRAIN/TEST split over families
    print()
    print("=" * 104)
    print("IS THE RELIEF SCALE COMPUTABLE FROM THE PROFILE?  train/test split over families")
    stats = ["sd_q50", "sd_q90", "sd_q99", "hs50", "hs90", "hs95", "hs99", "D"]
    targets = ["c_0.5", "c_0.9", "c_0.99"]
    idx = list(FAMILIES)
    train = [f for i, f in enumerate(idx) if i % 2 == 0]
    test = [f for i, f in enumerate(idx) if i % 2 == 1]
    rows = {r["family"]: r for r in out["rows"]}
    print("   train families %d, test families %d" % (len(train), len(test)))
    print("   %-9s%-9s%-10s%-11s%-11s" % ("target", "statistic", "k(train)", "maxerr(train)",
                                           "maxerr(TEST)"))
    results = {}
    for t in targets:
        for s in stats:
            tr_pairs = [(rows[f][s], rows[f][t]) for f in train if rows[f][t] and rows[f][s]]
            if len(tr_pairs) < 3:
                continue
            num = sum(a * b for a, b in tr_pairs)
            den = sum(a * a for a, _ in tr_pairs)
            k = num / den if den else 0.0
            e_tr = max(abs(k * a - b) / b for a, b in tr_pairs)
            te_pairs = [(rows[f][s], rows[f][t]) for f in test if rows[f][t] and rows[f][s]]
            e_te = [abs(k * a - b) / b for a, b in te_pairs]
            mte = max(e_te) if e_te else float("nan")
            med = sorted(e_te)[len(e_te) // 2] if e_te else float("nan")
            results["%s|%s" % (t, s)] = {"k": k, "train_max": e_tr, "test_max": mte,
                                         "test_median": med, "n_test": len(te_pairs)}
            print("   %-9s%-9s%-10.4f%-11.3f%-11.3f" % (t, s, k, e_tr, mte))
    out["predictor"] = results
    best = {t: min((s for s in stats if "%s|%s" % (t, s) in results),
                   key=lambda s: results["%s|%s" % (t, s)]["test_max"]) for t in targets}
    print()
    for t in targets:
        b = best[t]
        r = results["%s|%s" % (t, b)]
        print("   best for %-7s : %-8s  k=%.4f  test max rel.err %.3f  median %.3f"
              % (t, b, r["k"], r["test_max"], r["test_median"]))
    out["best"] = best

    with open("spike_v3_results.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nwrote spike_v3_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
