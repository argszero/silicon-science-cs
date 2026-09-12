"""Analysis for the full corrected grid (issue #1).

Reads grid6_results.json and derives every headline number in the note: the
full-context versus retrieval gap on both metrics and at every (length,
interference) cell, the sign-test count, the length-only and interference-only
sweeps, the distractor-type contrast at matched density, the evidence-position
ladder, the retrieval-budget sweep, and Wilson intervals on the sampled exact
rates. Writes grid6_analysis.json and prints a human-readable summary.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "grid6_results.json")))
cells = d["cells"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(p, 4), round(max(0.0, c - half), 4), round(min(1.0, c + half), 4))


def mean(xs):
    return sum(xs) / len(xs)


# two-sided 95% t critical values, keyed by degrees of freedom
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        20: 2.086, 25: 2.060, 29: 2.045, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def tcrit(df):
    if df in _T95:
        return _T95[df]
    ks = sorted(_T95)
    lo = max([k for k in ks if k <= df] or [ks[0]])
    hi = min([k for k in ks if k >= df] or [ks[-1]])
    if lo == hi:
        return _T95[lo]
    # linear interpolation in 1/df, which is where the t distribution is smooth
    f = (1.0 / df - 1.0 / lo) / (1.0 / hi - 1.0 / lo)
    return _T95[lo] + f * (_T95[hi] - _T95[lo])


def t_interval(xs):
    """mean and two-sided 95% t interval over the sample (n-1 df)."""
    n = len(xs)
    m = mean(xs)
    if n < 2:
        return m, m, m
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    half = tcrit(n - 1) * math.sqrt(var / n)
    return m, m - half, m + half


def r(x, n=3):
    return round(x, n)


main = [c for c in cells if c["arm"] == "MAIN"]
by = {}
for c in main:
    by[(c["n_chunks"], c["interference"])] = by.get((c["n_chunks"], c["interference"]), []) + [c]

print("== MAIN sweep: full-context versus retrieval, means over 2 instances ==")
print("L    I     full    dense1  dense4  dense8  bm25_4  none    gap_d4  gap_bm4  ex_g  ex_s  rank_d")
signs = []
grid = []
for L in [64, 128, 256]:
    for I in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]:
        cs = by[(L, I)]
        full = mean([c["full"]["mean_logprob"] for c in cs])
        d1 = mean([c["dense_k1"]["mean_logprob"] for c in cs])
        d4 = mean([c["dense_k4"]["mean_logprob"] for c in cs])
        d8 = mean([c["dense_k8"]["mean_logprob"] for c in cs])
        b4 = mean([c["bm25_k4"]["mean_logprob"] for c in cs])
        ne = mean([c["no_evidence"]["mean_logprob"] for c in cs])
        ex_g = sum(1 for c in cs if c["full"]["greedy_exact"])
        ex_s = mean([c["full"]["sampled_exact_rate"] for c in cs])
        rk = mean([c["dense_rank_gold"] for c in cs])
        g4 = d4 - full
        gb = b4 - full
        signs += [1 if (c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"]) < 0 else 0 for c in cs]
        grid.append({"L": L, "I": I, "full": r(full), "dense_k1": r(d1), "dense_k4": r(d4),
                     "dense_k8": r(d8), "bm25_k4": r(b4), "no_evidence": r(ne),
                     "gap_dense4": r(g4), "gap_bm25": r(gb),
                     "greedy_exact": ex_g, "sampled_exact_mean": r(ex_s, 4),
                     "dense_rank_gold_mean": r(rk, 2)})
        print("%-4d %.2f  %+.3f  %+.3f  %+.3f  %+.3f  %+.3f  %+.3f  %+.3f  %+.3f   %d/2   %.2f   %5.1f" % (
            L, I, full, d1, d4, d8, b4, ne, g4, gb, ex_g, ex_s, rk))

ncell = len(main)
neg = sum(signs)


def ahead(c):
    d = c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"]
    return (d - 0 != 0) and (not (d < 0))


zero_i = [c for c in main if c["interference"] == 0.0]
gt_i = [c for c in main if c["interference"] != 0.0]
pos_zero = sum(1 for c in zero_i if ahead(c))
pos_gt = sum(1 for c in gt_i if ahead(c))
print("\nretrieval-loses cells (dense_k4 gap negative): %d / %d" % (neg, ncell))
print("  no-distractor cells (I=0.00, n=%d): retrieval ahead in %d / %d" % (len(zero_i), pos_zero, len(zero_i)))
print("  distractor cells (I nonzero, n=%d): retrieval ahead in %d / %d" % (len(gt_i), pos_gt, len(gt_i)))
print("  finding: the registered crossover does not appear -- the I=0.00 rung is a null (cells split 3-3), and retrieval is behind on every rung that separates from zero")

print("\n== length-only sweep (I=0.00, no distractors): full-context mean logprob ==")
for L in [64, 128, 256]:
    cs = by[(L, 0.0)]
    print("  L=%-4d full %+.3f  sampled exact %.2f  greedy exact %d/2" % (
        L, mean([c["full"]["mean_logprob"] for c in cs]),
        mean([c["full"]["sampled_exact_rate"] for c in cs]),
        sum(1 for c in cs if c["full"]["greedy_exact"])))
fl = [c for c in cells if c["arm"] == "FILLER_neutral"]
print("  pure-length filler control (L=256, I=0, neutral filler): full %+.3f  sampled %.2f" % (
    mean([c["full"]["mean_logprob"] for c in fl]),
    mean([c["full"]["sampled_exact_rate"] for c in fl])))

print("\n== interference-only sweep at fixed length: reader degrades, retriever degrades faster ==")
for L in [64, 256]:
    cs = [by[(L, I)] for I in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]]
    print("  L=%d full drop %+.3f (I=0 to 0.8); dense_k4 drop %+.3f; bm25_k4 drop %+.3f" % (
        L,
        mean([c["full"]["mean_logprob"] for c in cs[-1]]) - mean([c["full"]["mean_logprob"] for c in cs[0]]),
        mean([c["dense_k4"]["mean_logprob"] for c in cs[-1]]) - mean([c["dense_k4"]["mean_logprob"] for c in cs[0]]),
        mean([c["bm25_k4"]["mean_logprob"] for c in cs[-1]]) - mean([c["bm25_k4"]["mean_logprob"] for c in cs[0]])))

print("\n== distractor type at matched length and density (L=256, I=0.60) ==")
st = by[(256, 0.6)]
en = [c for c in cells if c["arm"] == "TYPE_entity"]
for name, cs in (("same-entity status confusable", st), ("different entity", en)):
    full = mean([c["full"]["mean_logprob"] for c in cs])
    d4 = mean([c["dense_k4"]["mean_logprob"] for c in cs])
    b4 = mean([c["bm25_k4"]["mean_logprob"] for c in cs])
    r1 = sum(c["dense_recall"]["1"] for c in cs)
    print("  %-30s full %+.3f  dense_k4 %+.3f  bm25_k4 %+.3f  gap %+.3f  dense rec@1 %d/2" % (
        name, full, d4, b4, d4 - full, r1))

print("\n== evidence position ladder (L=256, I=0.60) ==")
pos = {}
for c in cells:
    if c["arm"] in ("POSITION", "MAIN") and c["n_chunks"] == 256 and c["interference"] == 0.6:
        pos.setdefault(c["gold_frac"], []).append(c)
for gf in sorted(pos):
    cs = pos[gf]
    full = mean([c["full"]["mean_logprob"] for c in cs])
    ex = sum(1 for c in cs if c["full"]["greedy_exact"])
    se = mean([c["full"]["sampled_exact_rate"] for c in cs])
    d4 = mean([c["dense_k4"]["mean_logprob"] for c in cs])
    print("  gold at frac %.2f: full %+.3f (greedy %d/2, sampled %.2f)  dense_k4 %+.3f" % (
        gf, full, ex, se, d4))

print("\n== retrieval budget sweep: does more k rescue retrieval? (L=256, I=0.60) ==")
cs = by[(256, 0.6)]
for k in [1, 2, 4, 8]:
    print("  k=%d dense %+.3f  recall@k %d/2" % (
        k, mean([c["dense_k%d" % k]["mean_logprob"] for c in cs]),
        sum(c["dense_recall"][str(k)] for c in cs)))

print("\n== sampled exact rates with Wilson intervals (pooled over instances) ==")
wil = []
for L in [64, 128, 256]:
    for I in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]:
        cs = by[(L, I)]
        k = sum(1 for c in cs for s in c["full"]["sampled"] if s["exact"])
        n = sum(len(c["full"]["sampled"]) for c in cs)
        p, lo, hi = wilson(k, n)
        wil.append({"L": L, "I": I, "k": k, "n": n, "rate": p, "lo": lo, "hi": hi})
        print("  L=%-4d I=%.2f full-context sampled exact %d/%d = %.3f  Wilson95[%.3f, %.3f]" % (
            L, I, k, n, p, lo, hi))

print("\n== gap by interference level (dense_k4 minus full-context, mean over lengths and instances) ==")
gap_by_I = {}
for I in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]:
    cs = [c for c in main if c["interference"] == I]
    g = mean([c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"] for c in cs])
    gap_by_I[I] = r(g)
    print("  I=%.2f  n=%d  gap %+.3f" % (I, len(cs), g))

print("\n== pooled retrieval recall over distractor cells (I nonzero) ==")
pool = {}
for k in [1, 2, 4, 8]:
    hits = sum(c["dense_recall"][str(k)] for c in gt_i)
    pool["dense_k%d" % k] = "%d/%d" % (hits, len(gt_i))
    print("  dense k=%-2d gold recovered in %d / %d cells" % (k, hits, len(gt_i)))
bh = sum(c["bm25_recall"]["4"] for c in gt_i)
print("  bm25  k=4  gold recovered in %d / %d cells" % (bh, len(gt_i)))
print("  worst-case dense gold rank in those cells: %d" % max(c["dense_rank_gold"] for c in gt_i))

print("\n== gap by interference with a 95% t interval over the six cells at that level ==")
gap_ci = {}
for I in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]:
    cs = [c for c in main if c["interference"] == I]
    g = [c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"] for c in cs]
    m, lo, hi = t_interval(g)
    gap_ci[I] = {"mean": r(m), "lo": r(lo), "hi": r(hi), "n": len(g),
                 "n_positive": sum(1 for x in g if x > 0), "n_negative": sum(1 for x in g if x < 0),
                 "excludes_zero": bool(lo > 0 or hi < 0)}
    print("  I=%.2f  n=%d  gap %+.3f  95%% CI [%+.3f, %+.3f]  %s  (%d+/%d-)" % (
        I, len(g), m, lo, hi, "separated from 0" if (lo > 0 or hi < 0) else "INCLUDES 0",
        gap_ci[I]["n_positive"], gap_ci[I]["n_negative"]))

print("\n== retrieval-budget ladder over the %d distractor cells ==" % len(gt_i))
ladder = {}
for k in [1, 2, 4, 8]:
    g = [c["dense_k%d" % k]["mean_logprob"] - c["full"]["mean_logprob"] for c in gt_i]
    m, lo, hi = t_interval(g)
    hits = sum(c["dense_recall"][str(k)] for c in gt_i)
    ladder["k%d" % k] = {"mean": r(m), "lo": r(lo), "hi": r(hi), "pooled_recall": "%d/%d" % (hits, len(gt_i))}
    print("  k=%-2d  mean gap %+.3f  95%% CI [%+.3f, %+.3f]  pooled recall %d/%d" % (k, m, lo, hi, hits, len(gt_i)))

print("\n== worst and best single MAIN cells (dense k=4 minus full-context) ==")
worst_main = min(main, key=lambda c: c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"])
best_main = max(main, key=lambda c: c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"])
worst_gap = r(worst_main["dense_k4"]["mean_logprob"] - worst_main["full"]["mean_logprob"])
print("  worst %+.3f at L=%d I=%.2f" % (worst_gap, worst_main["n_chunks"], worst_main["interference"]))
print("  best  %+.3f at L=%d I=%.2f" % (best_main["dense_k4"]["mean_logprob"] - best_main["full"]["mean_logprob"],
                                        best_main["n_chunks"], best_main["interference"]))

print("\n== recall-matched type control (gold inside the k=4 set for both families) ==")
typerm = {}
for kind in ("status", "entity"):
    cs = [c for c in cells if c["arm"] == "TYPERM_" + kind]
    if not cs:
        continue
    typerm[kind] = {
        "n": len(cs),
        "recall_k4": "%d/%d" % (sum(c["dense_recall"]["4"] for c in cs), len(cs)),
        "mean_dense_rank": r(mean([c["dense_rank_gold"] for c in cs]), 2),
        "reading": r(mean([c["full"]["mean_logprob"] for c in cs])),
        "retrieval_k4": r(mean([c["dense_k4"]["mean_logprob"] for c in cs])),
        "gap": r(mean([c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"] for c in cs])),
    }
    print("  %-7s n=%d  recall@4 %s  mean rank %.2f  reading %+.3f  retrieval %+.3f  gap %+.3f" % (
        kind, typerm[kind]["n"], typerm[kind]["recall_k4"], typerm[kind]["mean_dense_rank"],
        typerm[kind]["reading"], typerm[kind]["retrieval_k4"], typerm[kind]["gap"]))
if len(typerm) == 2:
    typerm["gap_difference_entity_minus_status"] = r(typerm["entity"]["gap"] - typerm["status"]["gap"])
    print("  gap difference (entity - status): %+.3f" % typerm["gap_difference_entity_minus_status"])

# The control only isolates TYPE where BOTH families left the gold record inside the k=4 set
# in the same instance at the same density. Those pairs are the recall-matched subset; the
# others still carry the recall confound and are counted as such rather than averaged in.
print("\n== recall-matched subset (paired: gold in the k=4 set for BOTH families) ==")
by_key = {(c["n_chunks"], c["interference"], c["gold_frac"] if "gold_frac" in c else c["inst_id"],
           c["kind"]): c for c in cells if c["arm"].startswith("TYPERM_")}
pairs = []
for c in cells:
    if c["arm"] != "TYPERM_status":
        continue
    e = [x for x in cells if x["arm"] == "TYPERM_entity" and x["inst_id"] == c["inst_id"]
         and x["n_chunks"] == c["n_chunks"] and x["interference"] == c["interference"]]
    if not e:
        continue
    e = e[0]
    if c["dense_recall"]["4"] == 1 and e["dense_recall"]["4"] == 1:
        pairs.append((c, e))
gof = lambda c: c["dense_k4"]["mean_logprob"] - c["full"]["mean_logprob"]
matched = {"n_pairs": len(pairs),
           "n_cells_examined": len([c for c in cells if c["arm"].startswith("TYPERM_")]),
           "status_reading": r(mean([c["full"]["mean_logprob"] for c, _ in pairs])),
           "entity_reading": r(mean([e["full"]["mean_logprob"] for _, e in pairs])),
           "status_retrieval_k4": r(mean([c["dense_k4"]["mean_logprob"] for c, _ in pairs])),
           "entity_retrieval_k4": r(mean([e["dense_k4"]["mean_logprob"] for _, e in pairs])),
           "status_gap": r(mean([gof(c) for c, _ in pairs])),
           "entity_gap": r(mean([gof(e) for _, e in pairs]))}
matched["gap_difference_entity_minus_status"] = r(matched["entity_gap"] - matched["status_gap"])
diffs = [gof(e) - gof(c) for c, e in pairs]
if len(diffs) >= 2:
    dm, dlo, dhi = t_interval(diffs)
    matched["difference_ci"] = {"mean": r(dm), "lo": r(dlo), "hi": r(dhi), "n": len(diffs),
                                "excludes_zero": bool(dlo > 0 or dhi < 0)}
print("  pairs %d of %d control cells | status gap %+.3f  entity gap %+.3f  difference %+.3f" % (
    matched["n_pairs"], matched["n_cells_examined"], matched["status_gap"], matched["entity_gap"],
    matched["gap_difference_entity_minus_status"]))
if "difference_ci" in matched:
    c = matched["difference_ci"]
    print("  paired 95%% CI on the difference [%+.3f, %+.3f] (n=%d) %s" % (
        c["lo"], c["hi"], c["n"], "excludes 0" if c["excludes_zero"] else "INCLUDES 0"))

out = {"main_grid": grid, "sign_test_negative": neg, "sign_test_n": ncell, "retrieval_ahead_no_distractor": pos_zero, "n_no_distractor": len(zero_i), "retrieval_ahead_with_distractor": pos_gt, "n_with_distractor": len(gt_i),
       "length_only": {str(L): r(mean([c["full"]["mean_logprob"] for c in by[(L, 0.0)]])) for L in [64, 128, 256]},
       "filler_control": {"neutral": r(mean([c["full"]["mean_logprob"] for c in fl])),
                          "related": r(mean([c["full"]["mean_logprob"] for c in by[(256, 0.0)]]))},
       "type_contrast": {"same_entity_status": r(mean([c["full"]["mean_logprob"] for c in st])),
                         "different_entity": r(mean([c["full"]["mean_logprob"] for c in en]))},
       "type_contrast_dense4": {"same_entity_status": r(mean([c["dense_k4"]["mean_logprob"] for c in st])),
                                "different_entity": r(mean([c["dense_k4"]["mean_logprob"] for c in en]))},
       "position": {str(gf): r(mean([c["full"]["mean_logprob"] for c in pos[gf]])) for gf in sorted(pos)},
       "sampled_wilson": wil, "n_cells": len(cells),
       "gap_by_interference": {str(k): v for k, v in gap_by_I.items()},
       "gap_ci_by_interference": {str(k): v for k, v in gap_ci.items()},
       "budget_ladder": ladder,
       "worst_main_cell": {"gap": worst_gap, "L": worst_main["n_chunks"], "I": worst_main["interference"]},
       "type_contrast_recall_matched": typerm,
       "type_contrast_matched_subset": matched,
       "pooled_recall_distractor_cells": pool, "pooled_recall_bm25_k4": "%d/%d" % (bh, len(gt_i))}
open(os.path.join(HERE, "grid6_analysis.json"), "w").write(json.dumps(out, indent=1, sort_keys=True))
print("\nANALYSIS DONE | cells %d" % len(cells))
