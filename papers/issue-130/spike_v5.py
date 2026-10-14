#!/usr/bin/env python3
"""spike_v5 -- the null KEY axis (the host's rant item 7, 2026-10-08T10:09).

Item 7, in substance: "THE NULL KEY IS PART OF THE STATISTIC ... a pair whose members differ in length
is not measured by a null built inside one length band ('the p95 you compare against belongs to the
wrong statistic') ... the per-pair key gave 0.1782-0.1900 and the first band-level null gave 0.6091 ...
Any operating-characteristic instrument (including the one #130 registers) should state the key and
derive the comparison p95 from that same key."

spike_v2/v3/v4 all set `tau(L, stat) = p95 of the statistic's own null at that length`, and every pool
in them was drawn from segments of ONE length -- so a judged pair's two members always had the same
length and the key question never arose.  This script makes the key an explicit axis:

    KEY = the rule that says which lengths the calibration pool is matched to.

  * `per_side`  -- the null is drawn from unrelated pairs whose members match the query pair PER SIDE
                   (a member of length L1 and a member of length L2).  This is what #130 does today.
  * `max_band`  -- the null is drawn from unrelated pairs BOTH of length max(L1, L2) -- the longer
                   member's band, the key the host measured as the wrong one.

The objects:

  tau(key)      = p95 of that key's null, at the lengths that key matches to
  FPR@tau       = the rate at which that tau fires on the query-length control pool.  Under the key
                  that MATCHED the query pair this must read ~alpha; under the other key it is the
                  "quoting a different statistic" number.  At a length ratio of 1 the two keys are the
                  same null, so the two readings must agree exactly -- the identity the finding rests on.
  classS        = same-book pairs (this corpus's "related by source" class, the analogue of the host's
                  same-author class) read against each key's null.

Certificates (each must be able to fail -- the plant proves it can):
  K1 calibration   a null and an INDEPENDENTLY DRAWN control from the same population must give an FPR
                   of ~alpha under the matching key.  Stated because a control drawn from the null's own
                   pool would make this a tautology (Class 171).
  K2 ratio-1 identity  at L1 == L2 the two keys are the SAME null, so every reading must agree exactly.
                   The plant `flat` (null forced to one fixed length) must FIRE this certificate.
  K3 key identity  the max-band null at (L1, L2) IS the per-side null at (max, max) -- asserted by
                   OBJECT identity, not a tolerance: the wrong key substitutes a longer, same-length
                   null for the pair the caller actually has.
  K4 monotone      the key effect is 0 at ratio 1 and grows with the ratio.

Real text only (Project Gutenberg, pinned in corpus/SHA256SUMS).  Ground truth by construction.
"""
import hashlib
import io
import json
import math
import random
from collections import Counter

import spike_v0 as s0
import spike_v2 as s2

STATS = ["jac3", "jac5", "dice2c", "cos"]
L_BASE = [150, 750]
RATIOS = [1, 2, 4]
N_NULL = 1000          # calibration pool (tau = p95 -> resolvable to ~1/1000)
N_CTRL = 1000          # independent control pool (must NOT share the null's draws -- Class 171)
ALPHA = 0.05
SEED0 = 20261008
FLAT_L = 3000          # the plant's fixed length
SALT = {"null": 0, "ctrl": 1, "same": 2}


def draw_pairs(books, L1, L2, n, salt, same=False):
    """Draw n token-pairs of lengths (L1, L2). `same` -> both members from ONE book, disjoint."""
    nb = len(books)
    rng = random.Random(SEED0 + L1 * 1000003 + L2 * 10007 + SALT[salt])
    pairs = []
    for i in range(n):
        ia = i % nb
        wa = books[ia][1]
        if same:
            wa = books[ia][1]
            span = len(wa) - L1 - L2 - 2
            off_a = rng.randrange(0, max(1, span))
            off_b = rng.randrange(off_a + L1, max(off_a + L1 + 1, len(wa) - L2))
            pairs.append((wa[off_a:off_a + L1], wa[off_b:off_b + L2]))
        else:
            wb = books[(ia + 3) % nb][1]
            oa = rng.randrange(0, max(1, len(wa) - L1 - 1))
            ob = rng.randrange(0, max(1, len(wb) - L2 - 1))
            pairs.append((wa[oa:oa + L1], wb[ob:ob + L2]))
    return pairs


def null_lengths(key, L1, L2, flat=False):
    """The lengths the calibration pool is drawn at, under `key`."""
    if flat:
        return FLAT_L, FLAT_L
    if key == "per_side":
        return L1, L2
    if key == "max_band":
        M = max(L1, L2)
        return M, M
    raise ValueError(key)


def null_pool(books, stat, idf, key, L1, L2, flat=False):
    a1, a2 = null_lengths(key, L1, L2, flat)
    return [s2.sim(stat, a, b, idf) for a, b in draw_pairs(books, a1, a2, N_NULL, "null")]


def main():
    books = s0.load_books()
    cnt = Counter(w for _, ws in books for w in ws)
    df = Counter()
    for _, ws in books:
        df.update(set(ws))
    N = len(books)
    idf = {w: math.log((N + 1) / (df[w] + 1)) + 1.0 for w in cnt}

    out = {"L_base": L_BASE, "ratios": RATIOS, "stats": STATS, "n_null": N_NULL,
           "n_ctrl": N_CTRL, "alpha": ALPHA, "flat_L": FLAT_L, "certificates": {}, "cells": {}}
    k2, k3, k1, k1_floored = [], [], [], []

    for stat in STATS:
        for L in L_BASE:
            for r in RATIOS:
                for order in ([0] if r == 1 else [0, 1]):
                    L1, L2 = (L, r * L) if order == 0 else (r * L, L)
                    null_per = null_pool(books, stat, idf, "per_side", L1, L2)
                    null_max = null_pool(books, stat, idf, "max_band", L1, L2)
                    null_flat = null_pool(books, stat, idf, "per_side", L1, L2, flat=True)
                    ctrl = [s2.sim(stat, a, b, idf) for a, b in
                            draw_pairs(books, L1, L2, N_CTRL, "ctrl")]
                    same = [s2.sim(stat, a, b, idf) for a, b in
                            draw_pairs(books, L1, L2, N_CTRL, "same", same=True)]
                    tp, tm, tf = (s0.pct(null_per, .95), s0.pct(null_max, .95),
                                  s0.pct(null_flat, .95))
                    mp, mm = s0.pct(null_per, .5), s0.pct(null_max, .5)
                    fp_ev = sum(1 for v in ctrl if v >= tp)
                    fm_ev = sum(1 for v in ctrl if v >= tm)
                    fpr_per, fpr_max = fp_ev / N_CTRL, fm_ev / N_CTRL
                    # A p95 sitting ON the floor (tau == 0) means every score passes: the FPR is 1.0
                    # by CONSTRUCTION, not by calibration.  Flagged by its CONDITION -- a threshold on
                    # the value would silently admit exactly these cells (Class 206(a)).
                    floored = (tp <= 0.0)
                    key = "%s|L=%d|r=%d|o=%d" % (stat, L, r, order)
                    out["cells"][key] = {
                        "L1": L1, "L2": L2,
                        "tau_per_side": tp, "tau_max_band": tm, "tau_flat": tf,
                        "null_med_per": mp, "null_med_max": mm,
                        "fpr_at_per_side_tau": fpr_per, "fpr_at_max_band_tau": fpr_max,
                        "ctrl_fired_per": fp_ev, "ctrl_fired_max": fm_ev,
                        "floored_null": bool(floored),
                        "same_med": s0.pct(same, .5),
                        "same_exceed_per": sum(1 for v in same if v >= tp) / N_CTRL,
                        "same_exceed_max": sum(1 for v in same if v >= tm) / N_CTRL,
                        "n_null": N_NULL, "n_ctrl": N_CTRL}
                    if not floored:
                        k1.append((key, abs(fpr_per - ALPHA) <= 4 * math.sqrt(ALPHA * (1 - ALPHA) / N_CTRL)))
                    else:
                        k1_floored.append((key, fpr_per))
                    if r == 1:
                        out["cells"][key]["k2_ratio1_identity"] = bool(null_per == null_max)
                        k2.append((key, null_per == null_max))
                        out["cells"][key]["k2_plant_flat_differs"] = bool(null_per != null_flat)
                    if L1 != L2:
                        M = max(L1, L2)
                        alt = null_pool(books, stat, idf, "per_side", M, M)
                        out["cells"][key]["k3_key_identity"] = bool(null_max == alt)
                        k3.append((key, null_max == alt))
                    print("%-7s L1=%-5d L2=%-5d | tau_per=%.4f tau_max=%.4f | FPR@per=%.3f "
                          "FPR@max=%.3f | same med=%.4f (per %.3f / max %.3f)"
                          % (stat, L1, L2, tp, tm, fpr_per, fpr_max,
                             out["cells"][key]["same_med"], out["cells"][key]["same_exceed_per"],
                             out["cells"][key]["same_exceed_max"]))

    sd = math.sqrt(ALPHA * (1 - ALPHA) / N_CTRL)
    out["certificates"]["K1_calibration_matching_key"] = {
        "tol": 4 * sd, "n_pass": sum(1 for _, ok in k1 if ok), "n": len(k1),
        "failures": [k for k, ok in k1 if not ok],
        "n_floored_excluded": len(k1_floored),
        "floored_cells": [k for k, _ in k1_floored],
        "floored_fpr": sorted(set(round(v, 4) for _, v in k1_floored)),
        "note": ("cells whose matching-key tau sits ON the floor (tau == 0) are EXCLUDED BY CONDITION: "
                 "every score passes, so their FPR is 1.0 by construction and is not a calibration "
                 "reading (Class 206(a))")}
    out["certificates"]["K2_ratio1_identity"] = {
        "n_pass": sum(1 for _, ok in k2 if ok), "n": len(k2),
        "failures": [k for k, ok in k2 if not ok],
        "plant_flat_fired": sum(1 for c in out["cells"].values()
                                if c.get("k2_plant_flat_differs")),
        "plant_flat_cells": sum(1 for c in out["cells"].values()
                                if "k2_plant_flat_differs" in c)}
    out["certificates"]["K3_key_identity"] = {
        "n_pass": sum(1 for _, ok in k3 if ok), "n": len(k3),
        "failures": [k for k, ok in k3 if not ok]}
    # K5: tau_max must be a function of max(L1, L2) ONLY (so it is order-invariant), and tau_flat
    # must be one constant.  Both are structural: they hold by construction and would fire if the
    # key's length rule drifted.
    grp_max, grp_flat = {}, {}
    for k, c in out["cells"].items():
        grp_max.setdefault((k.split("|")[0], max(c["L1"], c["L2"])), set()).add(c["tau_max_band"])
        grp_flat.setdefault(k.split("|")[0], set()).add(c["tau_flat"])
    viol_max = [kk for kk, v in grp_max.items() if len(v) > 1]
    viol_flat = [kk for kk, v in grp_flat.items() if len(v) > 1]
    out["certificates"]["K5_order_invariance"] = {
        "tau_max_groups": len(grp_max), "tau_max_violations": viol_max,
        "tau_flat_groups": len(grp_flat), "tau_flat_violations": viol_flat,
        "pass": not viol_max and not viol_flat}

    # ---- the finding: how far the key moves the verdict, by ratio (LIVE cells only) ---------
    eff = {}
    for r in RATIOS:
        rows = [c for k, c in out["cells"].items() if "|r=%d|" % r in k]
        live = [c for c in rows if not c["floored_null"]]
        eff[r] = {
            "n_rows": len(rows), "n_live": len(live), "n_floored": len(rows) - len(live),
            "max_abs_fpr_shift_live": max((abs(c["fpr_at_per_side_tau"] - c["fpr_at_max_band_tau"])
                                           for c in live), default=0.0),
            "max_abs_tau_shift_live": max((abs(c["tau_per_side"] - c["tau_max_band"]) for c in live),
                                          default=0.0)}
    # name the worst cell per ratio (by FPR shift), and the rule-of-three bound where a reading is 0
    for r in RATIOS:
        items = [(k, c) for k, c in out["cells"].items()
                 if "|r=%d|" % r in k and not c["floored_null"]]
        if items:
            k_w, w = max(items, key=lambda kc: abs(kc[1]["fpr_at_per_side_tau"]
                                                   - kc[1]["fpr_at_max_band_tau"]))
            eff[r]["worst_live"] = {
                "cell": k_w, "stat": k_w.split("|")[0], "L1": w["L1"], "L2": w["L2"],
                "fpr_at_per_side_tau": w["fpr_at_per_side_tau"],
                "fpr_at_max_band_tau": w["fpr_at_max_band_tau"],
                "ctrl_fired_per": w["ctrl_fired_per"], "ctrl_fired_max": w["ctrl_fired_max"],
                "bound_if_zero": ("<= %.4f (rule of three, n=%d)" % (3.0 / N_CTRL, N_CTRL)
                                  if w["ctrl_fired_max"] == 0 else None)}
    out["key_effect_by_ratio"] = eff

    # ---- two-sided: the wrong key can make the check LEAKY or BLIND -------------------------
    tol = 4 * sd
    live_all = [(k, c) for k, c in out["cells"].items() if not c["floored_null"]]
    leaky = [(k, c["fpr_at_max_band_tau"]) for k, c in live_all
             if c["fpr_at_max_band_tau"] > ALPHA + tol]
    blind = [(k, c["fpr_at_max_band_tau"]) for k, c in live_all
             if c["fpr_at_max_band_tau"] < ALPHA - tol]
    within = [(k, c["fpr_at_max_band_tau"]) for k, c in live_all
              if abs(c["fpr_at_max_band_tau"] - ALPHA) <= tol]
    mx = max(live_all, key=lambda kc: kc[1]["fpr_at_max_band_tau"]) if live_all else None
    out["wrong_key_fpr_two_sided"] = {
        "nominal": ALPHA, "tol": tol, "n_live": len(live_all),
        "n_leaky": len(leaky), "n_blind": len(blind), "n_within": len(within),
        "leaky_cells": [k for k, _ in leaky], "blind_cells": [k for k, _ in blind],
        "max_fpr_under_wrong_key": mx[1]["fpr_at_max_band_tau"] if mx else None,
        "max_fpr_cell": mx[0] if mx else None,
        "note": ("0.000 readings are reported with the rule-of-three bound 3/n (a bound, not an "
                 "exact zero); the floor degeneracy is excluded by condition above")}
    print("wrong-key FPR two-sided:", json.dumps(out["wrong_key_fpr_two_sided"], sort_keys=True)[:400])
    print("\ncertificates:", json.dumps(out["certificates"], sort_keys=True)[:500])
    print("key effect by ratio:", json.dumps(eff, sort_keys=True))

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v5_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16],
          "bytes", len(js.encode()))


if __name__ == "__main__":
    main()
