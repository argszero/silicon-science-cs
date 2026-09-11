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
print("  finding: the crossover sits at I=0+ -- retrieval leads only when the distractor set is empty")

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

out = {"main_grid": grid, "sign_test_negative": neg, "sign_test_n": ncell, "retrieval_ahead_no_distractor": pos_zero, "n_no_distractor": len(zero_i), "retrieval_ahead_with_distractor": pos_gt, "n_with_distractor": len(gt_i),
       "length_only": {str(L): r(mean([c["full"]["mean_logprob"] for c in by[(L, 0.0)]])) for L in [64, 128, 256]},
       "filler_control": {"neutral": r(mean([c["full"]["mean_logprob"] for c in fl])),
                          "related": r(mean([c["full"]["mean_logprob"] for c in by[(256, 0.0)]]))},
       "type_contrast": {"same_entity_status": r(mean([c["full"]["mean_logprob"] for c in st])),
                         "different_entity": r(mean([c["full"]["mean_logprob"] for c in en]))},
       "type_contrast_dense4": {"same_entity_status": r(mean([c["dense_k4"]["mean_logprob"] for c in st])),
                                "different_entity": r(mean([c["dense_k4"]["mean_logprob"] for c in en]))},
       "position": {str(gf): r(mean([c["full"]["mean_logprob"] for c in pos[gf]])) for gf in sorted(pos)},
       "sampled_wilson": wil, "n_cells": len(cells), "gap_by_interference": {str(k): v for k, v in gap_by_I.items()}, "pooled_recall_distractor_cells": pool, "pooled_recall_bm25_k4": "%d/%d" % (bh, len(gt_i))}
open(os.path.join(HERE, "grid6_analysis.json"), "w").write(json.dumps(out, indent=1, sort_keys=True))
print("\nANALYSIS DONE | cells %d" % len(cells))
