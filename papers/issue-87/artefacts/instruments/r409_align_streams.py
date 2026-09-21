#!/usr/bin/env python3
"""Issue #87 -- R409: does the alpha = 0 sign inversion SURVIVE RE-DRAWING THE STREAM?

WHY THIS EXISTS.  The review of #87 at b8855d1 asks (Q1): "Does the alpha = 0 sign inversion (section 5.3,
Table 4) reproduce in >= 3 disjoint streams?  If it does not, how much of PB2's 'direction refuted' survives
on the alpha = +-1 panel alone -- where the alignment sign is measured to be irrelevant?"  The question is
sharp because Table 4's alpha = 0 row is the weakest-evidenced half of the paper's two headline
prior-refutations, and section 5.3 already discloses that it holds under one convention only.

WHAT THE COMMITTED ROW ACTUALLY IS.  Table 4's alpha = 0 numbers reproduce bit-for-bit from
`smoke_v9_results.json`'s `rows` (`shifted|alpha=0` and `unshifted|alpha=0`), i.e. from ONE call of
`cell_runner(..., seed_gen = S5.SEED_GEN)` per (convention, alpha).  That runner draws ONE target
(`make_interaction(q, Q_int, alpha, seed_gen)`), ONE noise realisation (`default_rng(seed_gen + 7)`) and 50
train/test SPLITS inside that single draw.  So the row rests on one stream, not on the six independent target
draws the Table 4 caption names: `N_TARGET = 6` lives in `smoke_v12.py` (R398), whose `ALPHAS = (1.0, -1.0)`
has no alpha = 0 at all.  The caption describes the map's instrument, not this row's.

WHAT IS MEASURED.

  A  A k = 5 DISJOINT STREAM PANEL over the alignment axis, alpha in {+1, 0, -1} x both conventions x the 6
     bandwidths, q = 6, matched rival, using the SAME `cell_runner` the committed row came from.  A stream
     changes the planted target, the label noise and the splits, and nothing else.
  B  THE SIX-TARGET AVERAGE at alpha = 0 (the design the caption names), so the answer is read at BOTH
     sample sizes: the one the row was actually computed at, and the one the manuscript claims.
  C  CROSS-STREAM STATISTICS per cell: mean, sd (ddof = 1), range, sign unanimity, and a 95 % t interval
     (df = 4) on the two cells the section calls the inversion.

WHAT IS PRE-REGISTERED HERE, BEFORE THE RUN (so the result can contradict the author):

  P1  INSTRUMENT CONTROL: the stream seed S5.SEED_GEN reproduces `smoke_v9_results.json`'s shifted and
      unshifted alpha = 0 rows exactly, at all 6 bandwidths.  If this fails the panel is not the instrument.
  P2  THE INVERSION IS STREAM-STABLE: under the shifted convention, delta(alpha = 0) is NEGATIVE in at least
      4 of the 5 fresh streams at gamma = 1 AND at gamma = 2 (committed single stream: -0.1676, -0.2754).
  P3  THE CONVENTION SPLIT IS STREAM-STABLE: under the unshifted convention, delta(alpha = 0) at gamma = 1
      stays POSITIVE in at least 4 of 5 (committed: +0.4110).  The section's own caveat must be a property of
      the stream ensemble, not of one draw.
  P4  THE GAP FROM alpha = +1 IS STREAM-STABLE: delta(0) - delta(+1) is NEGATIVE in at least 4 of 5 streams
      at gamma = 1 and gamma = 2 (this is the sentence "deleting the target's alignment inverts the mid-band
      sign").
  P5  HONEST POWER ON THE NEAR-ZERO CELLS: among the shifted alpha = 0 cells with |committed| <= 0.05
      (gamma = 0.1), the sign FLIPS across the 5 streams -- those signs are stream noise, not findings, and
      are reported as such.
  P6  THE SIX-TARGET AVERAGE KEEPS THE SIGN (the caption's design): with N_TARGET = 6 independent targets at
      gamma = 1 and gamma = 2, the shifted alpha = 0 mean stays negative.

  FALSIFIER, stated before the run.  If P2 fails (the shifted mid-band cell is negative in <= 3 of 5 fresh
  streams), then Table 4's inversion is a property of one draw, and the honest reading of PB2 is that the
  direction refutation rests on the alpha = +-1 panel alone -- where section 5.3 itself measures the alignment
  sign to be irrelevant (max alpha-difference 0.0052, no cell changing sign).  That would require the abstract
  and section 5.3 to be weakened, and it would be reported as such rather than re-worded.

Run:  /usr/bin/python3 r409_align_streams.py       (numpy 2.0.2; writes r409_align_streams_results.json)
Reads only committed reports (for the control), imports the committed instruments, writes nothing but its own
two files.  The manuscript head is NOT touched: this is a review answer, not a revision.
"""
import io
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SRC = os.path.join(HERE, "smoke_v9_results.json")
OUT = os.path.join(HERE, "r409_align_streams_results.json")

import smoke_v5 as S5                      # noqa: E402  the generator, kernels, metric fields
import smoke_v9 as S9                      # noqa: E402  the cell runner Table 4's alpha axis came from

Q = 6
CONVS = ("shifted", "unshifted")
ALPHAS = (1.0, 0.0, -1.0)
GAMMAS = tuple(S9.GAMMAS)                  # (0.1, 0.25, 0.5, 1.0, 2.0, 3.0)
N_TARGET = 6                               # the caption's design, for arm B
# The stream ensemble, declared before any cell is read.  A panel whose seeds share a magnitude is a panel of
# ONE draw's neighbourhood, so the ensemble is built in three families and the families are reported separately:
# if the five clustered seeds disagreed with the neighbours, the clusters -- not the stream -- would be the
# finding.  S5.SEED_GEN (20260921) is the committed stream and is used ONLY as the control.
SEED_FAMILIES = {
    "cluster": (41020261, 41020262, 41020263, 41020264, 41020265),
    "wide_magnitude": (7, 1009, 123457, 2718281, 14142135),
    "adjacent": (20260922, 20260923, 20260924),
}
STREAM_SEEDS = tuple(s for fam in SEED_FAMILIES.values() for s in fam)
MID_BAND = (1.0, 2.0)                      # the two cells section 5.3 calls the inversion
NEAR_ZERO_MAX = 0.05                       # |committed| <= this -> the cell is a near-zero cell for P5


def build(q=Q):
    edges = S5.edges_for(S9.EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, S9.LAYERS) for g in GAMMAS} for c in CONVS}
    return edges, Z, metrics


def cell(edges, Z, metrics, conv, alpha, seed):
    return S9.cell_runner(Q, edges, Z, alpha, conv, metrics[conv], seed, S9.matched_w)


def multi_target(edges, Z, metrics, conv, alpha, seeds):
    """The caption's design: N_TARGET independent targets, each with its own 50 splits, averaged per gamma.
    Deliberately implemented as the mean of N_TARGET single-target cells, which is exactly what 'averaged over
    N_TARGET independent target draws x 50 splits' computes -- and it lets the two designs be compared on the
    SAME code path (Class 83)."""
    per = {g: [] for g in GAMMAS}
    for s in seeds:
        rows = cell(edges, Z, metrics, conv, alpha, s)["rows"]
        for g in GAMMAS:
            per[g].append(rows[g]["mean"])
    return {g: dict(mean=float(np.mean(v)), sd=float(np.std(v, ddof=1)), n=len(v), per_seed=v)
            for g, v in per.items()}


def main():
    t0 = time.time()
    res = {"what": "issue #87 R409 -- does the alpha = 0 sign inversion survive re-drawing the stream?",
           "why": "review question 1 on #87 at b885d51/b8855d1: is the Table 4 inversion stream-stable?",
           "scope": "q = 6, cycle graph, depth 2, matched (Mahalanobis) rival, both phase conventions",
           "preregistered": dict(
               P1="control: SEED_GEN reproduces smoke_v9_results.json's alpha = 0 rows exactly",
               P2="shifted alpha = 0 negative in >= 4 of 5 fresh streams at gamma = 1 AND gamma = 2 (first family)",
               P3="unshifted alpha = 0 positive in >= 4 of 5 at gamma = 1",
               P4="delta(0) - delta(+1) negative in >= 4 of 5 at gamma = 1 and gamma = 2",
               P5="shifted near-zero cells (|committed| <= 0.05) flip sign across streams",
               P6="the six-target average keeps the sign at gamma = 1 and gamma = 2",
               falsifier="P2 fails (<= 3 of 5) -> the inversion is one draw's property; PB2's direction "
                         "refutation rests on the alpha = +-1 panel alone and the abstract must be weakened"),
           "stream_seeds": list(STREAM_SEEDS), "seed_families": {k: list(v) for k, v in SEED_FAMILIES.items()},
           "committed_stream_seed": S5.SEED_GEN}

    edges, Z, metrics = build()
    res["build"] = dict(python="%s.%s.%s" % tuple(map(str, sys.version_info[:3])), numpy=np.__version__)

    # ---- P1: the control.  The panel must contain the committed reading, bit for bit.
    committed = {c: {g: None for g in GAMMAS} for c in CONVS}
    rep = json.loads(io.open(SRC, encoding="utf-8").read())
    for row in rep["rows"]:
        if row["alpha"] == 0.0:
            committed[row["conv"]][row["gamma"]] = row["delta_mean"]
    ctl_rows, ctl_ok = [], True
    for c in CONVS:
        got = cell(edges, Z, metrics, c, 0.0, S5.SEED_GEN)["rows"]
        for g in GAMMAS:
            same = bool(got[g]["mean"] == committed[c][g])
            ctl_ok = ctl_ok and same
            ctl_rows.append(dict(conv=c, gamma=g, committed=committed[c][g], recomputed=got[g]["mean"],
                                 bitwise_same=same))
    res["control_P1"] = dict(rows=ctl_rows, all_bitwise=ctl_ok)
    print("P1  control  : committed rows reproduced bitwise at all %d cells: %s" % (len(ctl_rows), ctl_ok))
    for r in ctl_rows[:2] + ctl_rows[6:8]:
        print("      %-9s gamma=%-5g committed %+.6f  recomputed %+.6f  %s"
              % (r["conv"], r["gamma"], r["committed"], r["recomputed"], "same" if r["bitwise_same"] else "DIFF"))
    if not ctl_ok:
        raise RuntimeError("the panel is not the instrument: the committed alpha = 0 rows do not reproduce")

    # ---- the five-stream panel
    panel = {}
    for c in CONVS:
        for a in ALPHAS:
            for s in STREAM_SEEDS:
                key = "%s|alpha=%+g|seed=%d" % (c, a, s)
                rows = cell(edges, Z, metrics, c, a, s)["rows"]
                panel[key] = dict(conv=c, alpha=a, seed=s,
                                  gamma={str(g): float(rows[g]["mean"]) for g in GAMMAS})
                print("      stream %d %-9s alpha=%+g done  (%.0fs)" % (s, c, a, time.time() - t0))
    res["panel"] = panel

    # ---- per-cell cross-stream statistics
    stats = {}
    for c in CONVS:
        for a in ALPHAS:
            for g in GAMMAS:
                v = np.array([panel["%s|alpha=%+g|seed=%d" % (c, a, s)]["gamma"][str(g)]
                              for s in STREAM_SEEDS])
                n = len(v)
                se = float(v.std(ddof=1) / np.sqrt(n))
                stats["%s|alpha=%+g|%g" % (c, a, g)] = dict(
                    conv=c, alpha=a, gamma=g, mean=float(v.mean()), sd=float(v.std(ddof=1)),
                    lo=float(v.min()), hi=float(v.max()), n=n,
                    n_negative=int((v < 0).sum()), n_positive=int((v > 0).sum()),
                    unanimous=bool((v > 0).all() or (v < 0).all()),
                    t_lo=float(v.mean() - 2.776 * se), t_hi=float(v.mean() + 2.776 * se))
    res["cross_stream"] = stats

    # ---- the ensemble's own uniformity check: are the three families telling one story?
    fam = {}
    for name, seeds in SEED_FAMILIES.items():
        for g in GAMMAS:
            v = np.array([panel["shifted|alpha=+0|seed=%d" % s]["gamma"][str(g)] for s in seeds])
            fam["%s|%g" % (name, g)] = dict(name=name, gamma=g, n=len(v), mean=float(v.mean()),
                                            sd=float(v.std(ddof=1)), lo=float(v.min()), hi=float(v.max()),
                                            n_negative=int((v < 0).sum()))
    res["by_family"] = fam
    print()
    print("-- the ensemble checked for clustering (shifted, alpha = 0): the three seed families --")
    for g in GAMMAS:
        print("   gamma=%-5g " % g + " | ".join(
            "%-15s %+.4f (sd %.4f, neg %d/%d)" % (name, fam["%s|%g" % (name, g)]["mean"],
                                                  fam["%s|%g" % (name, g)]["sd"],
                                                  fam["%s|%g" % (name, g)]["n_negative"],
                                                  fam["%s|%g" % (name, g)]["n"])
            for name in SEED_FAMILIES))

    def cell_stat(c, a, g, seeds=SEED_FAMILIES["cluster"]):
        key = "%s|alpha=%+g|%g" % (c, a, g)
        v = np.array([panel["%s|alpha=%+g|seed=%d" % (c, a, s)]["gamma"][str(g)] for s in seeds])
        return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), n=len(v),
                    n_negative=int((v < 0).sum()), n_positive=int((v > 0).sum()),
                    per_seed=[float(x) for x in v])

    # P2 is judged on the panel the registration named (the five-cluster family), with the rule as written:
    # at least 4 of 5.  The other families are replication under the SAME rule and are reported separately,
    # so a rescue cannot be read into a criterion that was moved after the fact.
    def rule(family, conv, alpha, gammas, want="negative"):
        out = {}
        for g in gammas:
            st = cell_stat(conv, alpha, g, SEED_FAMILIES[family])
            ok = 1.0 * st["n_negative"] / st["n"] >= 0.8
            if want == "positive":
                ok = 1.0 * st["n_positive"] / st["n"] >= 0.8
            out["%g" % g] = dict(met=bool(ok), mean=st["mean"], sd=st["sd"], n=st["n"],
                                 n_negative=st["n_negative"], n_positive=st["n_positive"])
        return out

    verdicts = {}
    p2 = rule("cluster", "shifted", 0.0, MID_BAND)
    verdicts["P2_shifted_midband_negative_in_4of5"] = dict(met=bool(all(v["met"] for v in p2.values())),
                                                           per_gamma=p2, judged_on="cluster (5 seeds)")
    verdicts["P2_replication_wide_magnitude"] = dict(met=bool(all(v["met"] for v in
                                                                 rule("wide_magnitude", "shifted", 0.0, MID_BAND).values())),
                                                     per_gamma=rule("wide_magnitude", "shifted", 0.0, MID_BAND),
                                                     judged_on="wide_magnitude (5 seeds)")
    verdicts["P2_replication_adjacent"] = dict(met=bool(all(v["met"] for v in
                                                            rule("adjacent", "shifted", 0.0, MID_BAND).values())),
                                               per_gamma=rule("adjacent", "shifted", 0.0, MID_BAND),
                                               judged_on="adjacent (3 seeds, all 3 must hold)")
    # NOTE (defect found while reading this round's own output): the first version of this dict called
    # cell_stat WITHOUT the family argument, so "pooled over 13" reported the 5-seed cluster family's mean
    # under a 13-seed label.  The statistic must name the set it read.
    p2all = {("%g" % g): dict(met=bool(cell_stat("shifted", 0.0, g, STREAM_SEEDS)["n_negative"]
                                       >= 0.8 * len(STREAM_SEEDS)),
                              mean=cell_stat("shifted", 0.0, g, STREAM_SEEDS)["mean"],
                              sd=cell_stat("shifted", 0.0, g, STREAM_SEEDS)["sd"],
                              n_negative=cell_stat("shifted", 0.0, g, STREAM_SEEDS)["n_negative"],
                              n=len(STREAM_SEEDS))
             for g in MID_BAND}
    verdicts["P2_pooled_13_streams"] = dict(met=bool(all(v["met"] for v in p2all.values())), per_gamma=p2all,
                                            judged_on="all 13 seeds")
    u = cell_stat("unshifted", 0.0, 1.0)
    verdicts["P3_unshifted_stays_positive"] = dict(met=bool(1.0 * u["n_positive"] / u["n"] >= 0.8),
                                                   n_positive=u["n_positive"], n=u["n"], mean=u["mean"])
    gaps = {}
    for g in MID_BAND:
        z = np.array([panel["shifted|alpha=+0|seed=%d" % s]["gamma"][str(g)]
                      - panel["shifted|alpha=+1|seed=%d" % s]["gamma"][str(g)] for s in SEED_FAMILIES["cluster"]])
        gaps["%g" % g] = dict(n_negative=int((z < 0).sum()), mean=float(z.mean()), sd=float(z.std(ddof=1)),
                              per_stream=[float(x) for x in z])
    verdicts["P4_gap_from_alpha_plus1_negative"] = dict(
        met=bool(all(1.0 * gaps["%g" % g]["n_negative"] / len(SEED_FAMILIES["cluster"]) >= 0.8 for g in MID_BAND)),
        per_gamma=gaps, judged_on="cluster (5 seeds)")

    # ---- P5: the near-zero cells, where the honest answer is that the sign is noise
    nz = []
    for g in GAMMAS:
        cm = committed["shifted"][g]
        if abs(cm) <= NEAR_ZERO_MAX:
            st = cell_stat("shifted", 0.0, g)
            nz.append(dict(gamma=g, committed=cm, mean=st["mean"], sd=st["sd"],
                           flips=bool(st["n_negative"] not in (0, st["n"]))))
    verdicts["P5_near_zero_cells_flip"] = dict(met=bool(any(x["flips"] for x in nz)), cells=nz)

    # ---- P6: the caption's design -- six independent targets at alpha = 0
    multi = {"shifted": {}, "unshifted": {}}
    for c in CONVS:
        ms = tuple(S5.SEED_GEN + 1000 * k + 13 for k in range(N_TARGET))
        per = multi_target(edges, Z, metrics, c, 0.0, ms)
        for g in GAMMAS:
            multi[c]["%g" % g] = per[g]
        print("      six-target %-9s alpha=+0 done  (%.0fs)" % (c, time.time() - t0))
    s1, s2 = multi["shifted"]["1"]["mean"], multi["shifted"]["2"]["mean"]
    verdicts["P6_six_target_average_keeps_sign"] = dict(met=bool(s1 < 0 and s2 < 0), gamma1=s1, gamma2=s2,
                                                       n_target=N_TARGET,
                                                       per_seed_gamma1=multi["shifted"]["1"]["per_seed"])
    res["six_target"] = multi

    res["verdicts"] = verdicts
    res["falsifier_fired"] = bool(not verdicts["P2_shifted_midband_negative_in_4of5"]["met"])
    print()
    print("-- verdicts " + "-" * 88)
    for k, v in verdicts.items():
        print("   %-38s met=%s" % (k, v["met"]))
    print("   falsifier fired (P2 failed): %s" % res["falsifier_fired"])
    print()
    print("-- the two cells section 5.3 calls the inversion, pooled over ALL %d streams of the ensemble --"
          % len(STREAM_SEEDS))
    for g in MID_BAND:
        st = cell_stat("shifted", 0.0, g, STREAM_SEEDS)     # all 13, NOT the cluster family
        se = st["sd"] / np.sqrt(st["n"])
        lo95, hi95 = st["mean"] - 2.179 * se, st["mean"] + 2.179 * se      # t(df = 12)
        commit = committed["shifted"][g]
        print("   shifted   gamma=%-5g alpha= 0  mean %+.4f  sd %.4f  negative %d/%d  95%% CI [%+.4f, %+.4f]"
              % (g, st["mean"], st["sd"], st["n_negative"], st["n"], lo95, hi95))
        print("                                   committed single draw %+.4f  =  %.1f cross-stream sd away"
              % (commit, (commit - st["mean"]) / st["sd"]))
    for g in MID_BAND:
        st = cell_stat("shifted", 1.0, g, STREAM_SEEDS)
        se = st["sd"] / np.sqrt(st["n"])
        print("   shifted   gamma=%-5g alpha=+1  mean %+.4f  sd %.4f  negative %d/%d  95%% CI [%+.4f, %+.4f]"
              % (g, st["mean"], st["sd"], st["n_negative"], st["n"],
                 st["mean"] - 2.179 * se, st["mean"] + 2.179 * se))
    print()
    print("-- the gap delta(alpha = 0) - delta(alpha = +1): the sentence 'deleting alignment inverts it' --")
    for g in MID_BAND:
        gp = verdicts["P4_gap_from_alpha_plus1_negative"]["per_gamma"]["%g" % g]
        print("   gamma=%-5g mean %+.4f  sd %.4f  negative %d/%d   (a negative gap = removing alignment"
              % (g, gp["mean"], gp["sd"], gp["n_negative"], len(SEED_FAMILIES["cluster"])))
        print("             helps the kernel, but the sign is only inverted if the alpha = 0 mean is negative)")
    res["report_sha256_source"] = None
    probe = dict(res)
    import hashlib
    res["report_sha256"] = hashlib.sha256(
        json.dumps(probe, sort_keys=True).encode("utf-8")).hexdigest()
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print()
    print("wrote %s   (%.0fs total)" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
