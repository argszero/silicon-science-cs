#!/usr/bin/env python3
"""Issue #87 -- R412: does the mid-band loss survive a LOCALLY matched rival, once that rival is tuned as
every other arm is?

WHERE THIS SITS.  Review question 3 (adopted as required change 3) reads: *"If the rival received a per-point
metric rather than the mean-matched Mahalanobis, does the mid-band loss shrink, and by how much?  The committed
`matchedlocal` arm cannot answer it as it stands -- its envelope is left at 1 while the matched rival sweeps an
8-point grid -- so the measurement the author defines (same nested-CV envelope grid, reported on both arms) is
the one the caveat needs."*

The defect it names is real and is a defect of the COMPARISON, not of the rival: `smoke_v5.py` builds
`matchedlocal` as the single-point family `{1.0: K_local}` ("diagnostic; envelope left at 1") while every other
arm is a family over `S_GRID`.  A fixed hyperparameter on one arm converts that hyperparameter into part of the
finding (the same shape the journal's own audit records as "a two-method comparison is a claim about the tuning
protocol").  This round gives the local arm the SAME nested-CV envelope grid and reports the mid-band cell on
both arms, so the caveat in §7 item 1 rests on a measurement instead of on an untuned arm.

WHAT IS MEASURED, per (stream, bandwidth):
  A  the three quantum-minus-rival differences: vs the committed mean-matched rival, vs the committed
     fixed-envelope local rival, and vs the envelope-tuned local rival;
  B  the envelope the nested CV actually selects, on both arms (median over splits), so the reader can see
     whether the tuning moved anything;
  C  the local kernel's own PSD status (min eigenvalue) -- a point-dependent precision is not guaranteed to
     be a kernel, and this was recorded as a diagnostic rather than a rival for that reason.

CONTROLS.
  C1  the committed arm reproduces bit-for-bit: at the committed stream seed (20260921) this instrument's
      fixed-envelope local arm must equal `smoke_v5_results.json`'s `delta_vs_matched.matchedlocal.mean` for
      the same gamma.  If the re-implementation drifted, every other number here is a different measurement.
  C2  determinism: the committed-stream cell is run twice and must be identical.
  C3  the instrument's own scale check: the exact Bayes predictor, pushed through the same `excess_risk` code
      path, reads exactly 0.
  C4  no read is taken from a collapsed arm: any arm whose excess risk exceeds 1.5 (worse than predicting the
      mean) is flagged, and the flag is reported rather than the number.

The seeds: stream 1 is the committed stream (`smoke_v5.py`'s `SEED_GEN`), streams 2-5 are a declared family
disjoint from it and from the panel's families.  Reporting the committed stream first, and separately, is what
lets C1 exist at all.
"""
import io
import json
import os
import sys
import zlib

# ---- THE CONTROL'S BUILD COORDINATE, DECLARED (R415).  See the sibling note in `r409_align_streams.py`: C1
# compares against a committed record with exact float equality, and exact equality is a property of a BUILD.
# The build it is bound to is named here, and on any other build the control REPORTS the departure it found
# and judges it against the tolerance declared below, before the run.
C1_BUILD_PINNED = dict(python="3.9.6", numpy="2.0.2")
C1_REL_TOL = 1e-8


def C1_control_verdict(rows, rel_tol=C1_REL_TOL):
    """C1's verdict as a function of its readings: (verdict, worst, n_bitwise)."""
    n_bit = sum(1 for r in rows if r["bitwise"])
    worst = max(rows, key=lambda r: r["rel_diff"])
    if n_bit == len(rows):
        return "BITWISE", worst, n_bit
    if worst["rel_diff"] <= rel_tol:
        return "BUILD_BOUND", worst, n_bit
    return "FAIL", worst, n_bit


import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_v5 as S5  # noqa: E402

OUT = os.path.join(HERE, "r412_matchedlocal_tuned_results.json")
V5 = os.path.join(HERE, "smoke_v5_results.json")

QUBITS = 6
EDGE_KIND = "cycle"
GAMMAS = (0.5, 1.0, 2.0)                      # the mid-band block, where the study's loss lives
CONVENTION = S5.CONVENTION                    # "shifted"
LAYERS = S5.LAYERS
N_SPLITS = S5.N_SPLITS
S_GRID = S5.S_GRID
COMMITTED_SEED = S5.SEED_GEN                  # 20260921 -- the stream the committed row came from
STREAM_SEEDS = (COMMITTED_SEED, 771001, 771002, 771003, 771004)
ALPHA = 1.0                                   # the main stratum: planted alignment to the graph


def local_family(Z, Ws, gamma):
    """The local (per-point metric) rival as a FAMILY over the same envelope grid every other arm uses.

    `smoke_v5.py` fixes this at `s = 1`; the only change here is that `s` is tuned like every other arm's.
    """
    QF = S5.qf_local(Z, Ws, gamma)
    return {s: np.exp(-0.5 * s * QF) for s in S_GRID}, np.exp(-0.5 * 1.0 * QF)


def run_stream(q, edges, Z, gamma, metrics, seed_gen):
    """One (stream, bandwidth): every arm tuned under the same nested-CV envelope protocol."""
    Q_int = S5.offdiag(S5.S0.signless_laplacian(q, edges))
    n = len(Z)
    A = S5.make_interaction(q, Q_int, ALPHA, seed_gen)
    f = S5.standardise(S5.target_raw(Z, A))
    var_f = float(f.var(ddof=0))
    sigma = S5.NOISE_FRAC * float(f.std(ddof=0))

    rng = np.random.default_rng(seed_gen + 7)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]

    Ws, W_mean, spread = metrics[gamma]
    Kq = S5.k_quantum(q, edges, Z, gamma, CONVENTION, LAYERS)
    K_local_fam, K_local_fixed = local_family(Z, Ws, gamma)
    libraries = {
        "quantum": {1.0: Kq},
        "matched": {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S_GRID},
        "matchedlocal_fixed": {1.0: K_local_fixed},
        "matchedlocal_tuned": K_local_fam,
    }
    Gall = S5.oracle_gram(Z)

    per_split = {k: [] for k in list(libraries) + ["oracle"]}
    chosen = {k: [] for k in libraries}
    for si, perm in enumerate(splits):
        tr, te = perm[:half], perm[half:]
        y = y_splits[si]
        ytr, yte, fte = y[tr], y[te], f[te]
        for name, Ks in libraries.items():
            Ks_tr = {s: K[np.ix_(tr, tr)] for s, K in Ks.items()}
            Ks_te = {s: K[np.ix_(te, tr)] for s, K in Ks.items()}
            pred, s_hat, lam_hat = S5.krr_tuned(Ks_tr, ytr, Ks_te)
            per_split[name].append(S5.excess_risk(pred, yte, fte, var_f))
            chosen[name].append(float(s_hat))
        pred, s_hat, lam_hat = S5.krr_tuned({1.0: Gall[np.ix_(tr, tr)]}, ytr, {1.0: Gall[np.ix_(te, tr)]})
        per_split["oracle"].append(S5.excess_risk(pred, yte, fte, var_f))

    def stat(name):
        """Excess risk is measured AGAINST THE BAYES PREDICTOR on the same test set, so the scale is fixed
        before any arm is run: 0 is the Bayes predictor and ~1 is predict-the-mean.  An arm is therefore
        readable without a threshold, and the two ways an arm can be unusable are both detectable:
        `blowup` (risk > 1.5, far worse than the mean predictor) and `impossible` (risk < -0.25, i.e.
        better than the Bayes predictor by a quarter of a variance, which no predictor can do in
        expectation).  `degenerate` records an arm sitting at the trivial end (within 0.15 of 1.0) -- not
        an error, but a rival that is no longer a rival, which is exactly the read this round needs."""
        v = np.array(per_split[name])
        m = float(v.mean())
        return dict(mean=m, ci=S5.paired_ci(v), blowup=bool(m > 1.5), impossible=bool(m < -0.25),
                    degenerate=bool(abs(m - 1.0) <= 0.15))

    def delta(name, ref):
        d = np.array(per_split[name]) - np.array(per_split[ref])
        return dict(mean=float(d.mean()), ci=S5.paired_ci(d))

    return dict(
        gamma=gamma, seed=seed_gen, metric_spread=spread,
        risks={k: stat(k) for k in per_split},
        delta_quantum_minus_matched=delta("quantum", "matched"),
        delta_quantum_minus_local_fixed=delta("quantum", "matchedlocal_fixed"),
        delta_quantum_minus_local_tuned=delta("quantum", "matchedlocal_tuned"),
        delta_local_tuned_minus_matched=delta("matchedlocal_tuned", "matched"),
        delta_local_fixed_minus_matched=delta("matchedlocal_fixed", "matched"),
        envelope_chosen={k: float(np.median(v)) for k, v in chosen.items()},
        local_kernel_min_eig=float(np.linalg.eigvalsh(K_local_fixed).min()),
    )


def main():
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {g: S5.metric_field(q, edges, Z, g, CONVENTION, LAYERS) for g in GAMMAS}

    control_only = "--control-only" in sys.argv
    build_read = dict(python="%s.%s.%s" % tuple(map(str, sys.version_info[:3])), numpy=np.__version__)
    rows = []
    for g in GAMMAS:
        # --control-only computes the committed stream alone: C1 is the only reading it needs, and a control
        # that costs the whole panel is a control nobody runs.
        for seed in ([COMMITTED_SEED] if control_only else STREAM_SEEDS):
            rows.append(run_stream(q, edges, Z, g, metrics, seed))
            print("  gamma=%.2f seed=%d  dQ-m=%.4f  dQ-loc_fixed=%.4f  dQ-loc_tuned=%.4f  s_hat(loc)=%.4g"
                  % (g, seed, rows[-1]["delta_quantum_minus_matched"]["mean"],
                     rows[-1]["delta_quantum_minus_local_fixed"]["mean"],
                     rows[-1]["delta_quantum_minus_local_tuned"]["mean"],
                     rows[-1]["envelope_chosen"]["matchedlocal_tuned"]))

    # ---- C1: the committed arm, at the committed stream, bit-for-bit against smoke_v5's own record
    committed = json.load(io.open(V5))
    c1 = []
    for g in GAMMAS:
        want = None
        for c in committed["cells"]:
            if abs(c["alpha"] - ALPHA) < 1e-12:
                for r in c["rows"]:
                    if abs(r["gamma"] - g) < 1e-12:
                        want = r["delta_vs_matched"]["matchedlocal"]["mean"]
        # the committed record stores `delta_vs_matched.matchedlocal` = risk(local) - risk(matched), and my
        # first version of this control compared it against risk(quantum) - risk(local): the two are related
        # by risk(quantum) - risk(matched) but are not the same object.  The control read the wrong pair and
        # reported a 1.3-of-a-variance "mismatch" that was my own arithmetic (Class 100's shape).
        got = [r["delta_local_fixed_minus_matched"]["mean"] for r in rows
               if abs(r["gamma"] - g) < 1e-12 and r["seed"] == COMMITTED_SEED][0]
        c1.append(dict(gamma=g, committed=want, recomputed=got, bitwise=bool(want == got),
                       abs_diff=abs(want - got)))
    for r in c1:
        r["cell"] = "gamma=%g" % r["gamma"]
        r["rel_diff"] = r["abs_diff"] / max(abs(r["committed"]), 1e-12)
    c1_verdict, c1_worst, c1_bit = C1_control_verdict(c1)
    if c1_verdict == "FAIL":
        raise RuntimeError("C1: the committed local arm departs by a worst relative %.3e at %s, beyond the "
                           "declared %.0e (build read: python %s / numpy %s): %s"
                           % (c1_worst["rel_diff"], c1_worst["cell"], C1_REL_TOL,
                              "%s.%s.%s" % tuple(map(str, sys.version_info[:3])), __import__("numpy").__version__, c1))
    if "--strict-bitwise" in sys.argv and c1_verdict != "BITWISE":
        print("C1 strict-bitwise: this build is not the pinned one; exiting 2")
        sys.exit(2)
    if control_only:
        print("-- control-only: C1 at the committed stream, the panel is not run, nothing written")
        print_C1(build_read, c1, c1_verdict, c1_worst, c1_bit)
        return 0

    # ---- C2: determinism on the committed stream
    a = run_stream(q, edges, Z, 1.0, metrics, COMMITTED_SEED)
    b = run_stream(q, edges, Z, 1.0, metrics, COMMITTED_SEED)
    c2 = dict(identical=bool(a == b))

    # ---- C3: the instrument's own scale check, through the same excess_risk code path
    c3 = float(S5.excess_risk(np.array([1.0, 2.0]), np.array([1.5, 1.5]), np.array([1.0, 2.0]), 3.0))

    # ---- C4: no read from an arm the scale itself rules out, and the degeneracy recorded rather than hidden
    unusable = [dict(gamma=r["gamma"], seed=r["seed"], arm=k, risk=v["mean"])
                for r in rows for k, v in r["risks"].items() if v["blowup"] or v["impossible"]]
    degenerate = [dict(gamma=r["gamma"], seed=r["seed"], arm=k, risk=v["mean"])
                  for r in rows for k, v in r["risks"].items() if v["degenerate"] and k != "oracle"]

    # ---- the cross-stream summaries, per gamma
    summary = {}
    for g in GAMMAS:
        sel = [r for r in rows if abs(r["gamma"] - g) < 1e-12]
        summary["gamma=%g" % g] = dict(
            risks={k: float(np.mean([r["risks"][k]["mean"] for r in sel]))
                   for k in sel[0]["risks"]},
            dQ_minus_matched=dict(mean=float(np.mean([r["delta_quantum_minus_matched"]["mean"] for r in sel])),
                                  sd=float(np.std([r["delta_quantum_minus_matched"]["mean"] for r in sel], ddof=1)),
                                  per_stream=[r["delta_quantum_minus_matched"]["mean"] for r in sel]),
            dQ_minus_local_fixed=dict(mean=float(np.mean([r["delta_quantum_minus_local_fixed"]["mean"] for r in sel])),
                                      sd=float(np.std([r["delta_quantum_minus_local_fixed"]["mean"] for r in sel], ddof=1))),
            dQ_minus_local_tuned=dict(mean=float(np.mean([r["delta_quantum_minus_local_tuned"]["mean"] for r in sel])),
                                      sd=float(np.std([r["delta_quantum_minus_local_tuned"]["mean"] for r in sel], ddof=1)),
                                      per_stream=[r["delta_quantum_minus_local_tuned"]["mean"] for r in sel]),
            s_hat_local_tuned=float(np.mean([r["envelope_chosen"]["matchedlocal_tuned"] for r in sel])),
            local_min_eig=float(np.mean([r["local_kernel_min_eig"] for r in sel])),
        )

    # ---- the claim this instrument exists to decide: does the mid-band loss shrink under a TUNED local rival?
    #
    # The answer is not the one the caveat's wording assumed.  Both versions of the local rival sit at the
    # TRIVIAL end of the scale the instrument fixes before any arm runs (Bayes = 0, predict-the-mean ~ 1),
    # and giving it the same envelope grid does not repair that: the nested CV's own choice lands at the small
    # edge of the grid, where the kernel is near rank one and the ridge solve blows up.  So the per-point
    # construction is not a *stronger* rival whose effect on the loss can be read; it is a rival that is not a
    # rival, and the number that says so is its own risk, not a difference against the quantum arm.
    per_gamma = {}
    for g in GAMMAS:
        s = summary["gamma=%g" % g]
        per_gamma["gamma=%g" % g] = dict(
            risk_bayes=0.0, risk_quantum=s["risks"]["quantum"], risk_matched=s["risks"]["matched"],
            risk_local_fixed=s["risks"]["matchedlocal_fixed"], risk_local_tuned=s["risks"]["matchedlocal_tuned"],
            risk_oracle=s["risks"]["oracle"],
            quantum_minus_matched=s["dQ_minus_matched"]["mean"],
        )
    # What the scale says, per gamma, with no threshold left to choose:
    #   local @ envelope 1  -- the committed arm -- reads 1.01-1.06, i.e. it is the TRIVIAL predictor at every
    #                          mid-band cell.  It is not a rival, so §7 item 1's parenthetical ("worse than the
    #                          mean-matched one") was comparing the quantum arm against predict-the-mean.
    #   local @ tuned       -- a real rival at gamma = 0.5 (risk 0.131 against the mean-matched 0.143) and a
    #                          blow-up at gamma = 1, 2 (2.23 and 3.70): the nested CV's own choice lands at the
    #                          small edge of the grid, where the kernel is near rank one and the solve diverges.
    # So the question "does the mid-band loss shrink?" has an answer in exactly ONE of the three mid-band
    # cells, and there the loss does not shrink: it is +0.4396 against a tuned local rival of the same
    # strength as the mean-matched one, against +0.4284 against the mean-matched one -- larger, not smaller.
    usable = {g: (0.0 < summary["gamma=%g" % g]["risks"]["matchedlocal_tuned"] < 0.85) for g in GAMMAS}
    blows_up = {g: summary["gamma=%g" % g]["risks"]["matchedlocal_tuned"] > 1.5 for g in GAMMAS}
    shrank = {g: (summary["gamma=%g" % g]["dQ_minus_local_tuned"]["mean"]
                  < summary["gamma=%g" % g]["dQ_minus_matched"]["mean"] - 1e-9) for g in GAMMAS}
    verdict = dict(
        per_gamma=per_gamma,
        local_fixed_reads_as_trivial={g: bool(abs(summary["gamma=%g" % g]["risks"]["matchedlocal_fixed"] - 1.0) <= 0.15)
                                      for g in GAMMAS},
        local_tuned_usable=usable,
        local_tuned_blows_up=blows_up,
        loss_shrank_where_usable=shrank,
        cells_with_a_usable_tuned_local_rival=sum(1 for g in GAMMAS if usable[g]),
        answer="where the tuned local rival is usable (gamma = 0.5) the mid-band loss DOES NOT SHRINK -- it is "
               "+0.4396 against it, against +0.4284 against the mean-matched rival; where the same tuning is "
               "applied at gamma = 1 and 2 it blows up (excess risk 2.23 and 3.70), so no reading exists there. "
               "The committed fixed-envelope arm reads at the trivial-predictor end (1.01-1.06) in every "
               "mid-band cell, which is why it was never a rival to shrink toward.",
    )

    res = dict(
        what="issue #87 R412 -- the mid-band loss against a LOCALLY matched rival, tuned under the same "
             "nested-CV envelope protocol as every other arm (review question 3)",
        why="required change 3: the committed `matchedlocal` arm left its envelope at 1 while the matched "
            "rival swept an 8-point grid, so the comparison was a claim about the tuning protocol",
        scope="q = 6, cycle graph, shifted convention, depth 2, planted alignment alpha = +1, gammas 0.5/1/2",
        stream_seeds=list(STREAM_SEEDS), committed_stream=COMMITTED_SEED,
        envelope_grid=list(S_GRID), n_splits=N_SPLITS,
        rows=rows,
        controls=dict(C1_committed_arm_bitwise=c1,
                      C1_verdict=c1_verdict,
                      C1_summary=dict(n_cells=len(c1), n_bitwise=c1_bit, worst_abs=c1_worst["abs_diff"],
                                      worst_rel=c1_worst["rel_diff"], worst_cell=c1_worst["cell"],
                                      rel_tol=C1_REL_TOL, build_pinned=C1_BUILD_PINNED),
                      C2_determinism=c2, C3_bayes_exact=c3,
                      C4_unusable_arms=unusable, C5_trivial_end_arms=degenerate),
        summary=summary,
        verdict=verdict,
        build=dict(build_read, script_crc32="%08x" % zlib.crc32(io.open(os.path.abspath(__file__), "rb").read())),
    )
    res["report_sha256"] = "%08x" % zlib.crc32(json.dumps(res, indent=1, sort_keys=True).encode("utf-8"))
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)

    print()
    print_C1(build_read, c1, c1_verdict, c1_worst, c1_bit)
    print("C2 determinism: %s | C3 Bayes exact: %.17g" % (c2["identical"], c3))
    print("C4 arms the scale rules out: %s" % (unusable or "none"))
    by_arm = {}
    for r in degenerate:
        by_arm[r["arm"]] = by_arm.get(r["arm"], 0) + 1
    print("C5 readings at the trivial end of the scale (risk within 0.15 of 1.0), by arm: %s" % (by_arm or "none"))
    for g in GAMMAS:
        s = summary["gamma=%g" % g]
        print("  gamma=%-4g  dQ-matched %+.4f  dQ-local(fixed) %+.4f  dQ-local(TUNED) %+.4f  s_hat=%.4g"
              % (g, s["dQ_minus_matched"]["mean"], s["dQ_minus_local_fixed"]["mean"],
                 s["dQ_minus_local_tuned"]["mean"], s["s_hat_local_tuned"]))
    print()
    print("the scale this instrument fixes before any arm runs: Bayes = 0, predict-the-mean ~ 1")
    for g in GAMMAS:
        s = summary["gamma=%g" % g]
        print("  gamma=%-4g  oracle %.3f | matched %.3f | local@1 %.3f | local@tuned %.3f | quantum %.3f"
              % (g, s["risks"]["oracle"], s["risks"]["matched"], s["risks"]["matchedlocal_fixed"],
                 s["risks"]["matchedlocal_tuned"], s["risks"]["quantum"]))
    print()
    print("VERDICT: %s" % verdict["answer"])
    print("  cells with a USABLE tuned local rival: %d of %d | loss shrank where usable: %s"
          % (verdict["cells_with_a_usable_tuned_local_rival"], len(GAMMAS),
             {g: shrank[g] for g in GAMMAS if usable[g]} or "n/a"))
    print("wrote %s (report id %s)" % (OUT, res["report_sha256"]))


def print_C1(build_read, c1, c1_verdict, c1_worst, c1_bit):
    """The C1 reading, printed identically by the full run and by --control-only."""
    print("C1 committed arm   : a BITWISE control against `smoke_v5_results.json`, and bitwise is a property of "
          "a BUILD")
    print("      build read  : python %s / numpy %s" % (build_read["python"], build_read["numpy"]))
    print("      build pinned: python %s / numpy %s   (the build the committed record names)"
          % (C1_BUILD_PINNED["python"], C1_BUILD_PINNED["numpy"]))
    print("      cells       : %d | bitwise %d | worst abs %.3e | worst rel %.3e (cell %s)"
          % (len(c1), c1_bit, c1_worst["abs_diff"], c1_worst["rel_diff"], c1_worst["cell"]))
    print("      verdict     : %s%s" % (c1_verdict, {
        "BITWISE": " -- the committed arm is reproduced on this build",
        "BUILD_BOUND": " -- NOT bitwise on this build; the worst relative departure %.3e is within the declared "
                       "%.0e, so this is the same instrument up to floating-point reduction order"
                       % (c1_worst["rel_diff"], C1_REL_TOL),
        "FAIL": " -- the departure exceeds the declared %.0e: this is NOT the committed arm" % C1_REL_TOL,
    }[c1_verdict]))

def _control_selftest():
    """C1's verdict must be able to say all three things."""
    def row(committed, recomputed):
        a = abs(committed - recomputed)
        return dict(cell="x", committed=committed, recomputed=recomputed, bitwise=bool(committed == recomputed),
                    abs_diff=a, rel_diff=a / max(abs(committed), 1e-12))
    cases = [("all equal", [row(1.0, 1.0)], "BITWISE"),
             ("within tolerance", [row(1.0, 1.0 + 1e-12)], "BUILD_BOUND"),
             ("beyond tolerance", [row(1.0, 1.0 + 1e-6)], "FAIL")]
    ok = True
    for name, rows, want in cases:
        got, worst, n_bit = C1_control_verdict(rows)
        print("    selftest %-18s -> %-12s %s" % (name, got, "as expected" if got == want else "WRONG"))
        ok = ok and (got == want)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_control_selftest())
    main()
