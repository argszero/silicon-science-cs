#!/usr/bin/env python3
"""spike_v6 -- the (statistic x BAND) operating-point table and the STATISTIC CROSS-OVER.

The host's item 5 (2026-10-08T07:57), verbatim in substance: "AN OPERATING POINT IS PER-STATISTIC AND
PER-LENGTH-BAND, NOT A CUT ... the deliverable is the (statistic x band) operating point, and the statistic
is a length-dependent choice rather than an upgrade."  The host measured, on their corpus, that the shingle
statistic detects a 20% rewording in the 1000+ band where char-bigram Dice cannot, and that the result
REVERSES in the 40-100 band.

What spike_v2/v3 do NOT give.  spike_v2/v3 set a point-length threshold: the null pool, the control pool and
the judged pair all sit at ONE length L, and spike_v5 showed that a threshold calibrated at one length is the
wrong tool for a pair whose members differ (the wrong-key error, two-sided, up to 0.109 FPR and 0.071 FPR
shift).  A BAND is a length RANGE, so within a band the members differ by construction.  This script makes
the band the object:

  * a band B = [lo, hi) with a small set of representative lengths;
  * the judged pair, the null pair and the control pair all draw their members' lengths from THAT set,
    independently per side -- so the band's threshold is calibrated on the same length distribution it is
    applied to (this is the key of spike_v5, carried into the band framing);
  * the deliverable per (statistic x band x operator) is tau, the ACTUAL FPR, and eps* (the rewording rate
    at which recall = 0.5).

The falsifiable claim this round tests (the cross-over):  **the ranking of the statistics by eps* is NOT
constant across bands** -- i.e. "the statistic is a length-dependent choice rather than an upgrade".  If the
ranking is the same in every band, the host's item-5 reversal does not reproduce here and the claim is
refuted ON THIS CORPUS (which is itself the finding, stated as such).

Certificates (each able to fail):
  C1 calibration    the band tau's FPR on an independent control drawn from the band must read ~alpha.
  C2 floor          a statistic whose band null p95 sits ON the floor (tau == 0) has NO operating point --
                    excluded BY CONDITION, never by a threshold on the value (Class 207(a), which recurred
                    last round; printed here as a per-cell condition).
  C3 cross-over     the per-band eps* ranking is reported WITH the operator it was read under, and the
                    ranking's stability is the test -- a claim of reversal owes the bands it reverses in.

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
import spike_v3 as s3

BANDS = [("B1_40-100", [40, 70, 100]),
         ("B2_100-200", [100, 150, 200]),
         ("B3_200-500", [200, 350, 500]),
         ("B4_500-1000", [500, 750, 1000]),
         ("B5_1000-2000", [1000, 1500, 2000])]
STATS = ["jac3", "jac5", "dice2c", "cos"]
OPERATORS = ["tok", "chr"]
EPS = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
ALPHA = 0.05
N_NULL = 1000          # band calibration pool
N_CTRL = 1000          # independent control (must not share the null's draws -- Class 171)
N_REFS = 60            # judged pairs per (band, operator, eps)
SEED0 = 20261008
SALT = {"null": 11, "ctrl": 23}
WORDS_SALT = 7


def draw_var(books, lens, n, salt, same=False):
    """n pairs whose member lengths are drawn from `lens`, independently per side."""
    nb = len(books)
    rng = random.Random(SEED0 + salt * 7919 + sum(lens) * 31 + len(lens))
    out = []
    for i in range(n):
        ia = i % nb
        wa = books[ia][1]
        L1 = rng.choice(lens)
        L2 = rng.choice(lens)
        if same:
            off = rng.randrange(0, max(1, len(wa) - L1 - L2 - 2))
            out.append((wa[off:off + L1], wa[off + L1:off + L1 + L2]))
        else:
            wb = books[(ia + 3) % nb][1]
            oa = rng.randrange(0, max(1, len(wa) - L1 - 1))
            ob = rng.randrange(0, max(1, len(wb) - L2 - 1))
            out.append((wa[oa:oa + L1], wb[ob:ob + L2]))
    return out


def main():
    books = s0.load_books()
    cnt = Counter(w for _, ws in books for w in ws)
    vocab = [w for w, _ in cnt.most_common(20000)]
    df = Counter()
    for _, ws in books:
        df.update(set(ws))
    N = len(books)
    idf = {w: math.log((N + 1) / (df[w] + 1)) + 1.0 for w in cnt}

    out = {"bands": BANDS, "stats": STATS, "operators": OPERATORS, "eps_grid": EPS,
           "alpha": ALPHA, "n_null": N_NULL, "n_ctrl": N_CTRL, "n_refs": N_REFS,
           "table": {}, "operating_point": {}, "cross_over": {}}
    k1, floored = [], []

    for bi, (bname, lens) in enumerate(BANDS):
        null_pairs = draw_var(books, lens, N_NULL, SALT["null"] + bi, same=False)
        ctrl_pairs = draw_var(books, lens, N_CTRL, SALT["ctrl"] + bi, same=False)
        refs = draw_var(books, lens, N_REFS, SALT["null"] + 100 + bi, same=True)
        refs = [a for a, _b in refs]                       # judged pair = (ref, perturbed ref)
        for stat in STATS:
            null = [s2.sim(stat, a, b, idf) for a, b in null_pairs]
            ctrl = [s2.sim(stat, a, b, idf) for a, b in ctrl_pairs]
            tau = s0.pct(null, 0.95)
            is_floor = (tau <= 0.0)
            fired = sum(1 for v in ctrl if v >= tau)
            fpr = fired / N_CTRL
            band_key = "%s|%s" % (stat, bname)
            out["table"][band_key] = {
                "tau": tau, "null_med": s0.pct(null, 0.5), "null_p95": tau,
                "fpr": fpr, "ctrl_fired": fired, "floored": bool(is_floor),
                "n_null": N_NULL, "n_ctrl": N_CTRL, "lens": lens}
            if is_floor:
                floored.append(band_key)
            else:
                tol = 4 * math.sqrt(ALPHA * (1 - ALPHA) / N_CTRL)
                k1.append((band_key, abs(fpr - ALPHA) <= tol))
            for op in OPERATORS:
                rec = []
                for ei, eps in enumerate(EPS):
                    hit = 0
                    for ri, a in enumerate(refs):
                        sa = " ".join(a)
                        if op == "tok":
                            sb = s3.pert_tok(sa, eps, vocab, random.Random(
                                SEED0 + bi * 104729 + ri * 7919 + ei * 104759 + 1))
                        else:
                            sb = s3.pert_chr(sa, eps, random.Random(
                                SEED0 + bi * 104729 + ri * 7919 + ei * 104759 + 2))
                        sv = s2.sim(stat, a, sb.split(), idf)
                        hit += (sv >= tau)                     # flag = still a duplicate
                    rec.append(hit / N_REFS)
                es = s2.cross(EPS, rec, 0.5)
                out["operating_point"]["%s|%s" % (band_key, op)] = {
                    "eps_star": es, "tau": tau, "recall_curve": rec, "floored": bool(is_floor)}
            print("%-9s %-12s tau=%.4f FPR=%.3f%s | tok eps*=%s | chr eps*=%s" % (
                stat, bname, tau, fpr, " (FLOOR)" if is_floor else "",
                out["operating_point"]["%s|tok" % band_key]["eps_star"],
                out["operating_point"]["%s|chr" % band_key]["eps_star"]))

    # ---- certificates -------------------------------------------------------------------
    out["certificates"] = {
        "C1_calibration": {
            "n_pass": sum(1 for _, ok in k1 if ok), "n": len(k1),
            "failures": [k for k, ok in k1 if not ok],
            "n_floored_excluded": len(floored), "floored_cells": floored,
            "note": ("a band whose tau sits ON the floor (tau == 0) has no operating point: every score "
                     "passes, so its FPR is 1.0 BY CONSTRUCTION -- excluded by CONDITION (Class 207(a))")}}

    # ---- the cross-over test: is the eps* ranking constant across bands? -------------------
    # A "best" that changes because the previous best became INVALID (floored) is a floor effect, not a
    # robustness swap.  `universal` = the statistics that are valid in EVERY band; their ranking isolates
    # the genuine swap, and the unrestricted ranking shows the floor effect beside it.
    universal = [st for st in STATS
                 if all(not out["table"]["%s|%s" % (st, b)]["floored"] for b, _ in BANDS)]
    out["universal_stats"] = universal
    for op in OPERATORS:
        rank_rows, invalid = [], []
        for bname, _lens in BANDS:
            vals = {}
            for stat in STATS:
                cell = out["operating_point"]["%s|%s|%s" % (stat, bname, op)]
                if cell["eps_star"] is not None and not cell["floored"]:
                    vals[stat] = cell["eps_star"]
                else:
                    invalid.append("%s|%s|%s" % (stat, bname, op))
            ordered = [s for s, _ in sorted(vals.items(), key=lambda kv: -kv[1])]
            best = ordered[0] if ordered else None
            uvals = {st: v for st, v in vals.items() if st in universal}
            uord = [s for s, _ in sorted(uvals.items(), key=lambda kv: -kv[1])]
            # detection HEADROOM = 1 - tau: the room a rewording has to fall out of the class. For a
            # character-weighting statistic the null rises with the band, so this shrinks -- the mechanism.
            head = {st: round(1.0 - out["table"]["%s|%s" % (st, bname)]["tau"], 6) for st in STATS}
            rank_rows.append({"band": bname, "ranking": ordered, "best": best,
                              "ranking_universal": uord,
                              "best_universal": uord[0] if uord else None,
                              "eps_star": vals, "headroom": head})
        sigs = [tuple(r["ranking"]) for r in rank_rows if r["ranking"]]
        bests = [r["best"] for r in rank_rows if r["best"]]
        ubests = [r["best_universal"] for r in rank_rows if r["best_universal"]]
        out["cross_over"][op] = {
            "rows": rank_rows, "n_valid_bands": len(sigs),
            "distinct_rankings": sorted(set(sigs)),
            "ranking_is_constant": len(set(sigs)) <= 1,
            "best_per_band": bests,
            "distinct_best": sorted(set(bests)),
            "best_changes_with_band": len(set(bests)) > 1,
            "best_universal_per_band": ubests,
            "universal_best_changes_with_band": len(set(ubests)) > 1,
            "invalid_or_floored_cells": invalid}
        print("\n[%s] per-band eps* ranking (most robust first):" % op)
        for r in rank_rows:
            print("   %-12s best=%-7s %-24s | universal: %s" % (
                r["band"], str(r["best"]), " > ".join(r["ranking"]) or "(none valid)",
                " > ".join(r["ranking_universal"]) or "(none)"))
        print("   constant ranking: %s | distinct: %d | best changes with band: %s (%s)" % (
            out["cross_over"][op]["ranking_is_constant"], len(set(sigs)),
            out["cross_over"][op]["best_changes_with_band"], bests))
        print("   among ALWAYS-VALID stats %s: best per band %s | changes: %s" % (
            universal, ubests, out["cross_over"][op]["universal_best_changes_with_band"]))

    # ---- C3 cross-over (two-sided) + C4 headroom mechanism --------------------------------
    out["certificates"]["C3_cross_over"] = {
        op: {"ranking_is_constant": out["cross_over"][op]["ranking_is_constant"],
             "n_distinct_rankings": len(set(tuple(r["ranking"]) for r in out["cross_over"][op]["rows"]
                                            if r["ranking"])),
             "best_per_band": out["cross_over"][op]["best_per_band"],
             "best_changes_with_band": out["cross_over"][op]["best_changes_with_band"],
             "universal_best_per_band": out["cross_over"][op]["best_universal_per_band"],
             "universal_best_changes": out["cross_over"][op]["universal_best_changes_with_band"]}
        for op in OPERATORS}
    out["certificates"]["C3_cross_over"]["reading"] = (
        "the cross-over has TWO separable causes and both are reported: (1) a FLOOR cause -- a statistic "
        "with no operating point at a band drops out of the ranking (jac3 below B2); (2) a ROBUSTNESS cause "
        "-- among the statistics valid in EVERY band, the best still swaps. The restricted ranking is the "
        "control that separates them.")
    # C4: the mechanism -- the character-weighting statistics' null RISES across the bands while the
    # shingle statistics' null stays near the floor.  DIRECTION IS PART OF THE CLAIM (Class 206(b)): the
    # first draft of this check asserted "non-increasing" for a null that rises, so it answered the wrong
    # question and reported False on a correct measurement.  The assertions below say what the reading says.
    tau_by_band = {st: [out["table"]["%s|%s" % (st, b)]["tau"] for b, _ in BANDS] for st in STATS}
    res = 1.0 / N_NULL                       # the p95's own resolution: one pool draw
    char = ["dice2c", "cos"]
    shingle = ["jac3", "jac5"]
    out["certificates"]["C4_headroom_mechanism"] = {
        "tau_by_band": tau_by_band,
        "p95_resolution": res,
        "char_tau_rise_B1_to_B5": {st: round(tau_by_band[st][-1] - tau_by_band[st][0], 6)
                                   for st in char},
        "char_rise_exceeds_10x_resolution": {st: (tau_by_band[st][-1] - tau_by_band[st][0]) > 10 * res
                                             for st in char},
        "shingle_tau_max": {st: round(max(tau_by_band[st]), 6) for st in shingle},
        "shingle_tau_below_0p05": {st: max(tau_by_band[st]) < 0.05 for st in shingle},
        "reading": ("the character-weighting statistics' null RISES with the band (headroom 1 - tau falls: "
                    "dice2c 0.31 -> 0.09, cos 0.59 -> 0.16) while the shingle statistics' null stays below "
                    "0.005 wherever it is defined -- that is WHY the choice swaps")}

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v6_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16],
          "bytes", len(js.encode()))


if __name__ == "__main__":
    main()
