#!/usr/bin/env python3
"""Issue #87 -- R402: does the advantage map survive RE-DRAWING THE NOISE?

Every number in the map so far (R391-R401) rests on ONE seed stream: the per-cell delta averages 6 target
draws x 40 splits, and all of them came from a single realisation of that ensemble.  R396/R397 already showed
the null blocks' dispersion gap was a REALISED DRAW, not a mechanism -- so the map's own claims owe the same
question: how much of a cell's delta is the stream?

WHAT IS MEASURED.

  A  A k = 5 STREAM PANEL: five paired (q = 6, q = 8) maps, each a full 24-cell grid (2 phase conventions x 6
     bandwidths x 2 planted alignments), each under a seed stream disjoint from every earlier round's and from
     each other.  The stream changes what a stream can change -- the planted target, the label noise and the
     train/test permutations -- and nothing else (metric fields, kernels and the rival are deterministic
     functions of the band).
  B  PER-CELL CROSS-STREAM STATISTICS: mean, sd (ddof = 1), range and SIGN UNANIMITY across the 5 streams, at
     both qubit counts, plus a 95 % t interval (df = 4) on the four cells that carry the main claim.
  C  THE PAIRED q-EFFECT: within each stream, e_s = delta(q = 8) - delta(q = 6) per cell -- so the qubit-count
     comparison is paired on the stream, and the attenuation R401 measured at ~30 % stops being a single
     difference of two single-stream maps.
  D  THE SAMPLING UNIT: the across-stream sd against the within-stream draw sd R401 reported per cell
     (0.001-0.013).  If the stream is the bigger unit, per-cell error bars built from draws alone understate
     the uncertainty -- the same lesson R397 priced for the null blocks.
  E  THE MAP'S STRUCTURE SET, defined OUTSIDE this round: the cells with |delta| >= 0.1 in R398's committed
     q = 6 stream (an independent realisation, used here only to name the cells), against the cells that are
     near zero there.  The structure cells are predicted stable; the near-zero cells are predicted NOT to be.

WHAT IS PRE-REGISTERED HERE, BEFORE THE RUN (so the result can contradict it):

  Q1  STRUCTURE IS STREAM-STABLE: in the 8 structure cells the cross-stream sign is unanimous (5/5) in at least
      7 of 8 cells at each qubit count, and the cross-stream sd there stays below 0.05 -- smaller than half the
      smallest structure gap.
  Q2  NEAR-ZERO CELLS ARE NOT RESOLVED: among the cells with |delta_R398| <= 0.05, at least 3 flip sign across
      the 5 streams at q = 6 (an honest power statement: those signs are stream noise, not findings).
  Q3  THE ATTENUATION IS A q EFFECT, NOT A STREAM ARTEFACT: in the three attenuation cells (shifted|1,
      unshifted|2, shifted|0.5) the paired effect e_s is NEGATIVE in at least 4 of 5 streams for both planted
      alignments, and |mean e| >= 3 x sd(e).
  Q4  THE HEADLINE HAS A REAL INTERVAL: the four main-claim cells at q = 6 keep a 95 % t-interval lower bound
      above +0.15 for both alpha = +-1 -- the "matched rival dominates" claim is not a point estimate.
  Q5  THE STREAM IS A BIGGER UNIT THAN A DRAW: the across-stream sd exceeds R401's within-stream draw sd
      (6 draws) in at least 15 of the 24 cells.
  Q6  MATCHED-vs-ISOTROPIC-RBF SEPARATION STAYS SMALL in every stream: max |delta_vs_matched - delta_vs_rbf|
      median over cells <= 0.02 of a variance.

CONTROLS (each owns a plant where a plant is possible):

  C1  determinism WITHIN a stream: one band's cells rebuilt under the same stream reproduce the main run
      exactly (max |diff| == 0), at both qubit counts.
  C2  COMMITTED-STREAM REPRODUCTION: the harness re-run at R401's own stream (SEED_T0 = 900000) on one q = 8
      band reproduces the committed smoke_v15_results.json rows bit-for-bit -- the panel's instrument is the
      instrument that produced the committed record, not a look-alike.
  C2b harvest completeness of the committed q = 6 reference (24 finite cells), so Q2's reference set is not
      silently short.
  C3  the SIGN-UNANIMITY instrument FIRES: a planted one-entry sign flip must turn its cell's unanimity red
      (and a clean vector must stay green).
  C4  the PAIRED-EFFECT instrument FIRES: a synthetic paired panel with a known injected effect returns that
      effect to 1e-12 and reports unanimity; a zero-effect panel returns 0 and its resolvability check goes
      red -- a check that cannot go red is decoration.
  C5  STREAMS REALLY DIFFER (the "same stream twice" failure of Class 94): the 5 seed ranges are asserted
      disjoint by arithmetic, AND the stream-to-stream spread in the structure cells must exceed 0.01.

Run:  /usr/bin/python3 -u smoke_v16.py   (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v12_results.json (R398's q = 6 stream: the structure set) and smoke_v15_results.json (R401's q = 8
stream: C2's target); writes smoke_v16_results.json.
"""
import hashlib
import io
import json
import os
import sys

import numpy as np

import smoke_v5 as S5
import smoke_v12 as S12
import smoke_v15 as S15

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v16_results.json")
REF_Q6 = os.path.join(HERE, "smoke_v12_results.json")     # R398: the structure set's external definition
REF_Q8 = os.path.join(HERE, "smoke_v15_results.json")     # R401: C2's reproduction target

Q6, Q8 = 6, 8
CONVS = S12.CONVS
GAMMAS = S12.GAMMAS
ALPHAS = S12.ALPHAS
N_TARGET = S15.N_TARGET
N_SPLITS = S15.N_SPLITS
QUBITS_PAIR = (Q6, Q8)

# five disjoint streams: the per-stream seed offsets are 10007*k + 101*idx <= 10007*5 + 101*11 = 51146,
# so a stride of 110000 keeps every stream's seed set disjoint from every other's (asserted in code).
STREAM_T0 = [1100003, 1210007, 1320011, 1430017, 1540021]
STREAM_STRIDE = 110000
R401_T0 = 900000                                  # C2: the committed q = 8 stream
REF_STRUCT_THRESH = 0.10                          # |delta| at q = 6 in R398's stream -> "structure cell"
REF_TIE_THRESH = 0.05                             # |delta| at q = 6 in R398's stream -> "near-zero cell"
MAIN_CLAIM_CELLS = [("shifted", 0.5), ("shifted", 1.0), ("unshifted", 1.0), ("unshifted", 2.0)]
ATTENUATION_CELLS = [("shifted", 1.0), ("unshifted", 2.0), ("shifted", 0.5)]
T95_DF4 = 2.776                                   # two-sided 95 % t quantile, df = 4


def key_of(conv, gamma, alpha):
    return "%s|%g|a=%+g" % (conv, gamma, alpha)


# ---------------------------------------------------------------- references (outside the new streams)

def harvest_q6():
    """R398's committed q = 6 stream, cell -> delta_vs_matched (the structure set's definition)."""
    raw = json.loads(io.open(REF_Q6, encoding="utf-8").read())
    out = {}
    for k, v in raw["rows"].items():
        out[k] = float(v["cells"]["A_registered|t=0.000"]["delta_mean"])
    return out


def harvest_q8():
    """R401's committed q = 8 stream, cell -> its row (only C2's target band is used)."""
    raw = json.loads(io.open(REF_Q8, encoding="utf-8").read())
    return {k: dict(row) for k, row in raw["rows"].items()}


def uniformity(vals):
    """Sign unanimity of one cell's cross-stream delta vector: the count of entries agreeing with the mode."""
    signs = [int(np.sign(v)) for v in vals]
    if any(s == 0 for s in signs):
        return 0, 0
    pos = sum(1 for s in signs if s > 0)
    return max(pos, len(signs) - pos), (1 if pos >= len(signs) - pos else -1)


def paired_effect(d6, d8):
    e = [b - a for a, b in zip(d6, d8)]
    mean_e = float(np.mean(e))
    sd_e = float(np.std(e, ddof=1)) if len(e) > 1 else float("nan")
    unan, sgn = uniformity(e)
    return dict(per_stream=e, mean=mean_e, sd=sd_e, unanimity=unan, n=len(e), sign=sgn,
                resolvable=bool(abs(mean_e) >= 3.0 * sd_e) if sd_e > 0 else bool(mean_e != 0.0))


def t_interval(vals):
    m = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    half = T95_DF4 * sd / np.sqrt(len(vals))
    return dict(mean=m, sd=sd, lo=m - half, hi=m + half, half=float(half), n=len(vals))


# ---------------------------------------------------------------- plants

def plant_sign_instrument():
    """C3: a clean vector stays green; a one-entry flip must turn its cell red."""
    clean = [0.30, 0.29, 0.31, 0.30, 0.30]
    flipped = [0.30, 0.29, 0.31, 0.30, -0.02]
    u_clean, _ = uniformity(clean)
    u_flip, _ = uniformity(flipped)
    return dict(clean_unanimity=u_clean, flipped_unanimity=u_flip, n=5,
                fires=bool(u_clean == 5 and u_flip == 4))


def plant_paired_instrument():
    """C4: an injected effect must be returned; a zero-effect panel must fail resolvability."""
    d6 = [0.40, 0.38, 0.42, 0.39, 0.41]
    d8_inj = [x - 0.10 for x in d6]
    r_inj = paired_effect(d6, d8_inj)
    r_zero = paired_effect(d6, list(d6))
    return dict(injected=-0.10, recovered=r_inj["mean"], recovered_ok=bool(abs(r_inj["mean"] + 0.10) < 1e-12),
                injected_unanimity=r_inj["unanimity"], injected_resolvable=r_inj["resolvable"],
                zero_mean=r_zero["mean"], zero_resolvable=r_zero["resolvable"],
                fires=bool(abs(r_inj["mean"] + 0.10) < 1e-12 and r_inj["resolvable"] and not r_zero["resolvable"]))


def plant_stream_disjointness():
    """C5a: the seed sets must be pairwise disjoint, argued by arithmetic on the offset ranges."""
    off_max = 10007 * (N_TARGET - 1) + 101 * (len(CONVS) * len(GAMMAS) - 1)
    ok = all(STREAM_T0[i + 1] - STREAM_T0[i] > off_max for i in range(len(STREAM_T0) - 1))
    return dict(offset_max=off_max, stride=STREAM_STRIDE, disjoint=bool(ok))


def dumps(rep):
    return json.dumps(rep, indent=1, sort_keys=True, default=float)


# ---------------------------------------------------------------- main

def main():
    print("=" * 104)
    print("ISSUE #87 -- R402: does the advantage map survive re-drawing the noise?  (k = %d streams, q = 6 and 8)"
          % len(STREAM_T0))
    print("=" * 104)

    ref6 = harvest_q6()
    ref8 = harvest_q8()
    c2b = dict(n_cells=len(ref6), all_finite=bool(all(np.isfinite(v) for v in ref6.values())),
               n_cells_q8=len(ref8))
    print("-- harvest: R398's q = 6 stream %d cells (all finite %s); R401's q = 8 stream %d cells"
          % (c2b["n_cells"], c2b["all_finite"], c2b["n_cells_q8"]))
    assert c2b["n_cells"] == 24 and c2b["all_finite"], c2b

    struct = sorted([k for k, v in ref6.items() if abs(v) >= REF_STRUCT_THRESH])
    ties = sorted([k for k, v in ref6.items() if abs(v) <= REF_TIE_THRESH])
    print("   structure set (|delta_R398| >= %.2f): %d cells -- %s" % (REF_STRUCT_THRESH, len(struct), struct))
    print("   near-zero set (|delta_R398| <= %.2f): %d cells" % (REF_TIE_THRESH, len(ties)))

    # ---- A: the stream panel
    maps = {}
    for si, t0 in enumerate(STREAM_T0):
        S15.SEED_T0 = t0
        rowset = {}
        for q in QUBITS_PAIR:
            rowset[q] = S15.run_map(q)
            print("   stream %d/%d (SEED_T0 = %d): q = %d map done (%d cells)"
                  % (si + 1, len(STREAM_T0), t0, q, len(rowset[q])), flush=True)
        maps[si] = rowset

    keys = sorted(maps[0][Q6].keys())
    assert len(keys) == 24, len(keys)

    # ---- C1: determinism within a stream
    DET_BANDS = [("shifted", 0.5), ("unshifted", 2.0)]
    S15.SEED_T0 = STREAM_T0[0]
    det = {}
    for q in QUBITS_PAIR:
        det_rows = S15.run_map(q, only=DET_BANDS)
        worst, ncmp, mismatch = 0.0, 0, []
        for k, r in sorted(det_rows.items()):
            for f in ("r_quantum", "r_matched", "r_rbf", "delta_vs_matched",
                      "delta_vs_matched_random_metric"):
                a, b = maps[0][q][k][f], r[f]
                worst = max(worst, abs(a - b))
                ncmp += 1
                if a != b:
                    mismatch.append((k, f, a, b))
        det[q] = dict(max_abs_diff=float(worst), n_values=ncmp, n_mismatched=len(mismatch),
                      identical=bool(len(mismatch) == 0))
    print("-- C1 determinism within stream 1: q = 6 %s (max |diff| %.3e) | q = 8 %s (max |diff| %.3e)"
          % (det[Q6]["identical"], det[Q6]["max_abs_diff"], det[Q8]["identical"], det[Q8]["max_abs_diff"]))

    # ---- C2: reproduce the committed q = 8 stream on one band
    S15.SEED_T0 = R401_T0
    repro = S15.run_map(Q8, only=[("shifted", 1.0)])
    c2_worst, c2_n, c2_mis = 0.0, 0, 0
    for k, r in sorted(repro.items()):
        for f in ("r_quantum", "r_matched", "delta_vs_matched", "r_matched_random_metric"):
            a, b = ref8[k][f], r[f]
            c2_worst = max(c2_worst, abs(a - b))
            c2_n += 1
            c2_mis += int(a != b)
    c2 = dict(max_abs_diff=float(c2_worst), n_values=c2_n, n_mismatched=int(c2_mis), identical=bool(c2_mis == 0))
    print("-- C2 committed-stream reproduction (R401 stream, band shifted|1, q = 8): identical %s (%d values, "
          "max |diff| %.3e)" % (c2["identical"], c2_n, c2_worst))

    # ---- C3/C4/C5 plants
    c3 = plant_sign_instrument()
    c4 = plant_paired_instrument()
    c5a = plant_stream_disjointness()
    print("-- C3 sign instrument fires: %s (clean %d/%d, one flip %d/%d)"
          % (c3["fires"], c3["clean_unanimity"], c3["n"], c3["flipped_unanimity"], c3["n"]))
    print("-- C4 paired instrument fires: %s (injected %+.2f recovered %+.12f; zero-effect resolvable %s)"
          % (c4["fires"], c4["injected"], c4["recovered"], c4["zero_resolvable"]))
    print("-- C5a seed ranges disjoint: %s (offset_max %d < stride %d)"
          % (c5a["disjoint"], c5a["offset_max"], c5a["stride"]))

    # ---- B/C/D: the per-cell statistics
    cells = {}
    for k in keys:
        d6 = [maps[s][Q6][k]["delta_vs_matched"] for s in maps]
        d8 = [maps[s][Q8][k]["delta_vs_matched"] for s in maps]
        within = [abs(maps[s][q][k]["draw_spread_delta"]) for s in maps for q in QUBITS_PAIR]
        u6, s6 = uniformity(d6)
        u8, s8 = uniformity(d8)
        sep6 = float(np.mean([abs(maps[s][Q6][k]["delta_vs_matched"] - maps[s][Q6][k]["delta_vs_rbf"])
                              for s in maps]))
        sep8 = float(np.mean([abs(maps[s][Q8][k]["delta_vs_matched"] - maps[s][Q8][k]["delta_vs_rbf"])
                              for s in maps]))
        cells[k] = dict(
            conv=str(maps[0][Q6][k]["conv"]), gamma=float(maps[0][Q6][k]["gamma"]),
            alpha=float(maps[0][Q6][k]["alpha"]),
            ref_q6_r398=float(ref6[k]),
            d6=[float(x) for x in d6], d8=[float(x) for x in d8],
            mean6=float(np.mean(d6)), sd6=float(np.std(d6, ddof=1)),
            mean8=float(np.mean(d8)), sd8=float(np.std(d8, ddof=1)),
            min6=float(min(d6)), max6=float(max(d6)), min8=float(min(d8)), max8=float(max(d8)),
            unanimity6=u6, sign6=s6, unanimity8=u8, sign8=s8,
            within_draw_sd_mean=float(np.mean(within)), within_draw_sd_max=float(np.max(within)),
            paired=paired_effect(d6, d8),
            sep_q6=sep6, sep_q8=sep8,
            ci6=t_interval(d6), ci8=t_interval(d8),
        )

    # ---- Q1
    q1 = {}
    for q, unan_key, sd_key, mean_key in ((Q6, "unanimity6", "sd6", "mean6"), (Q8, "unanimity8", "sd8", "mean8")):
        unanimous = [k for k in struct if cells[k][unan_key] == len(STREAM_T0)]
        sdmax = max(cells[k][sd_key] for k in struct)
        smallest_gap = min(abs(cells[k][mean_key]) for k in struct)
        q1[q] = dict(n_unanimous=len(unanimous), n_struct=len(struct), unanimous=unanimous,
                     max_sd=float(sdmax), smallest_gap=float(smallest_gap),
                     sd_below_half_gap=bool(sdmax < 0.5 * smallest_gap),
                     met=bool(len(unanimous) >= len(struct) - 1 and sdmax < 0.05))
    flips6 = [k for k in ties if cells[k]["unanimity6"] < len(STREAM_T0)]
    q2 = dict(n_ties=len(ties), n_flipped=len(flips6), flipped=flips6,
              met=bool(len(flips6) >= 3), thresh=REF_TIE_THRESH)

    # ---- Q3
    q3_cells = {}
    for conv, g in ATTENUATION_CELLS:
        for a in ALPHAS:
            k = key_of(conv, g, a)
            p = cells[k]["paired"]
            q3_cells[k] = dict(mean=p["mean"], sd=p["sd"], unanimity=p["unanimity"], n=p["n"],
                               negative_in=int(sum(1 for v in p["per_stream"] if v < 0)),
                               resolvable=p["resolvable"])
    q3 = dict(cells=q3_cells,
              met=bool(all(v["negative_in"] >= 4 and v["resolvable"] for v in q3_cells.values())))

    # ---- Q4
    q4 = {}
    for conv, g in MAIN_CLAIM_CELLS:
        for a in ALPHAS:
            k = key_of(conv, g, a)
            c = cells[k]["ci6"]
            q4[k] = dict(mean=c["mean"], lo=c["lo"], hi=c["hi"], above_015=bool(c["lo"] > 0.15))
    q4_met = all(v["above_015"] for v in q4.values())

    # ---- Q5
    q5_worse = [k for k in keys if cells[k]["sd6"] > cells[k]["within_draw_sd_max"]]
    q5 = dict(n_cells=len(keys), n_worse=len(q5_worse), cells=q5_worse, met=bool(len(q5_worse) >= 15),
              median_sd_ratio=float(np.median([cells[k]["sd6"] / max(cells[k]["within_draw_sd_max"], 1e-12)
                                               for k in keys])))

    # ---- Q6
    sep = {str(Q6): [cells[k]["sep_q6"] for k in keys], str(Q8): [cells[k]["sep_q8"] for k in keys]}
    q6 = dict(median_abs_sep={q: float(np.median(v)) for q, v in sep.items()},
              max_abs_sep={q: float(max(v)) for q, v in sep.items()},
              met=bool(max(float(np.median(v)) for v in sep.values()) <= 0.02))

    # ---- C5b: the streams really differ
    spread = max(max(cells[k]["d6"]) - min(cells[k]["d6"]) for k in struct)
    c5b = dict(max_stream_spread_in_structure_cells=float(spread), fires=bool(spread > 0.01))

    # ---- leads (the R400 currency, now with an interval)
    leads6 = [int(sum(1 for k in keys if maps[s][Q6][k]["delta_vs_matched"] < 0)) for s in maps]
    leads8 = [int(sum(1 for k in keys if maps[s][Q8][k]["delta_vs_matched"] < 0)) for s in maps]

    # ---- print the panel
    print()
    print("-- B  the map across streams (per-cell cross-stream mean +/- sd, %d streams) -------------------"
          % len(STREAM_T0))
    print("   %-22s %8s %8s %7s %7s | %8s %8s %7s | %s"
          % ("cell", "ref6", "mean6", "sd6", "u6", "mean8", "sd8", "u8", "paired q-effect"))
    for k in keys:
        c = cells[k]
        print("   %-22s %+8.4f %+8.4f %7.4f %5d/5 | %+8.4f %+8.4f %5d/5 | %+.4f (sd %.4f, %d/5 neg)%s"
              % (k, c["ref_q6_r398"], c["mean6"], c["sd6"], c["unanimity6"], c["mean8"], c["sd8"],
                 c["unanimity8"], c["paired"]["mean"], c["paired"]["sd"],
                 sum(1 for v in c["paired"]["per_stream"] if v < 0),
                 "  *STRUCT*" if k in struct else ("  ~tie~" if k in ties else "")))

    print()
    print("-- C  the paired q-effect on the attenuation cells (q = 8 minus q = 6, same stream) ------------")
    for k, v in sorted(q3_cells.items()):
        print("   %-22s mean %+.4f  sd %.4f  negative in %d/5  resolvable %s"
              % (k, v["mean"], v["sd"], v["negative_in"], v["resolvable"]))

    print()
    print("-- D/Q4 the four main-claim cells, 95 %% t interval at q = 6 (df = 4) ---------------------------")
    for k, v in sorted(q4.items()):
        print("   %-22s mean %+.4f  95%% CI [%+.4f, %+.4f]  lower bound > 0.15: %s"
              % (k, v["mean"], v["lo"], v["hi"], v["above_015"]))

    print()
    print("-- verdicts ------------------------------------------------------------------------------------")
    print("   Q1 structure stream-stable : q=6 %d/%d unanimous (max sd %.4f) met=%s | q=8 %d/%d (max sd %.4f) met=%s"
          % (q1[Q6]["n_unanimous"], len(struct), q1[Q6]["max_sd"], q1[Q6]["met"],
             q1[Q8]["n_unanimous"], len(struct), q1[Q8]["max_sd"], q1[Q8]["met"]))
    print("   Q2 near-zero unresolved    : %d of %d near-zero cells flip sign across streams met=%s -> %s"
          % (q2["n_flipped"], len(ties), q2["met"], flips6))
    print("   Q3 attenuation is a q effect: %d of %d attenuation readings negative in >= 4/5 streams and "
          "resolvable met=%s" % (sum(1 for v in q3_cells.values() if v["negative_in"] >= 4 and v["resolvable"]),
                                 len(q3_cells), q3["met"]))
    print("   Q4 headline interval       : %d of %d main-claim readings have CI lower bound > 0.15 met=%s"
          % (sum(1 for v in q4.values() if v["above_015"]), len(q4), q4_met))
    print("   Q5 stream > draw           : %d of %d cells met=%s (median sd ratio %.2f)"
          % (q5["n_worse"], q5["n_cells"], q5["met"], q5["median_sd_ratio"]))
    print("   Q6 matched-vs-RBF separation: median q=6 %.4f q=8 %.4f met=%s"
          % (q6["median_abs_sep"]["6"], q6["median_abs_sep"]["8"], q6["met"]))
    print("   C5b streams differ          : max stream spread in the structure cells %.4f fires=%s"
          % (c5b["max_stream_spread_in_structure_cells"], c5b["fires"]))
    print("   quantum leads per stream    : q=6 %s (mean %.1f) | q=8 %s (mean %.1f)"
          % (leads6, float(np.mean(leads6)), leads8, float(np.mean(leads8))))

    rep = dict(round="R402", qubits=list(QUBITS_PAIR), graph="cycle", layers=S15.LAYERS,
               n_target=N_TARGET, n_splits=N_SPLITS, stream_t0=list(STREAM_T0), r401_t0=R401_T0,
               gammas=list(GAMMAS), alphas=list(ALPHAS), convs=list(CONVS),
               stream_def_note="A stream re-draws the planted target, the label noise and the train/test "
                               "permutations; the metric fields, the kernels and the rival are deterministic "
                               "functions of the band and are identical across streams.",
               cells=cells, structure_set=struct, near_zero_set=ties,
               q1_structure_stable=q1, q2_near_zero_unresolved=q2, q3_attenuation=q3,
               q4_main_claim_ci={k: dict(v) for k, v in q4.items()},
               q5_stream_vs_draw=q5, q6_matched_vs_rbf=q6,
               quantum_leads_per_stream=dict(q6=leads6, q8=leads8,
                                             mean_q6=float(np.mean(leads6)), mean_q8=float(np.mean(leads8))),
               controls=dict(c1_determinism=det, c2_committed_reproduction=c2, c2b_harvest=c2b,
                             c3_sign_instrument=c3, c4_paired_instrument=c4, c5a_seed_disjointness=c5a,
                             c5b_streams_differ=c5b, all_pass=bool(
                                 all(det[q]["identical"] for q in QUBITS_PAIR) and c2["identical"]
                                 and c2b["all_finite"] and c3["fires"] and c4["fires"]
                                 and c5a["disjoint"] and c5b["fires"])))
    fine = dumps(rep)
    sha = hashlib.sha256(fine.encode("utf-8")).hexdigest()
    print()
    print("   controls ALL PASS: %s" % rep["controls"]["all_pass"])
    print("   report sha256 = %s" % sha)
    io.open(OUT, "w", encoding="utf-8").write(fine)
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
