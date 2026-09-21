#!/usr/bin/env python3
"""Issue #87 -- R392: PB3's instrument, and the scope of the claim it was registered to test.

PB3 (registered) reads: "under the phase convention that makes the metric the identity (the anchor's
unshifted convention) the advantage region is empty at every alignment level, with data, qubit count and
rival unchanged.  Refuted if a non-empty advantage survives the convention change."

Two things had to be settled before that clause can be tested at all, and this file settles them with
controls rather than with algebra.

(A) IS THE CONVENTION CHANGE A COORDINATE CHANGE?  The two conventions differ only in the interaction
    angle -- shifted: (pi - x_i)(pi - x_j), unshifted: x_i x_j.  If they were the same map in different
    angle coordinates, then K_unshifted(gamma') = K_shifted(gamma) for some gamma' and comparing them at
    FIXED gamma would be comparing two different bandwidths -- the study would then attribute a bandwidth
    difference to "the convention".  The probe below searches a fine gamma grid for exactly that match.
    Its POSITIVE side is what makes its negative result mean anything: restricted to the SAME convention,
    the search must return the query's own gamma (residual ~1e-16), and the residual it leaves when that
    gamma is EXCLUDED measures the search's own resolution floor there.  The cross-convention residual is
    read against that floor, never against zero.

(B) WHAT IS THE UNSHIFTED METRIC?  R390 recorded "the unshifted metric's on-edge anisotropy is EXACTLY 0
    at L = 1 and L = 2", and this study inherited that as "the unshifted convention makes the metric the
    identity".  Measured at the base point R390 used (x = 0) that is exactly right -- 2g = 2I to machine
    precision, which is control C2.  Measured at the bandwidths the study actually runs it is NOT: the
    unshifted interaction angle is gamma^2 z_i z_j, which vanishes only at gamma = 0, so for every
    gamma > 0 the unshifted metric still carries the graph's structure.  R390's statistic measured the
    ON-EDGE coefficient AT x = 0; the honest statement of the scope is the distance profile in C3.  PB3
    as registered -- empty region because the metric is the identity -- therefore tests a premise that
    holds only in the gamma -> 0 limit, and the clause is read below in that corrected form.

THE READ.  The whole R391 grid is re-run under BOTH conventions (same generator, same arms, same nested-CV
protocol, matched rival rebuilt from that convention's own metric at that bandwidth), so PB3 becomes a
comparison of two grids rather than an assertion about one.

Run:  /usr/bin/python3 smoke_v6.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Writes smoke_v6_results.json beside this file.
"""
import hashlib
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S0
import smoke_v4 as S4
import smoke_v5 as S5

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v6_results.json")

QUBITS = 6
LAYERS = 2
EDGE_KIND = "cycle"
NOISE_FRAC = S5.NOISE_FRAC
N_SPLITS = S5.N_SPLITS
GAMMAS = S5.GAMMAS
ALIGNS = S5.ALIGNS
CONVS = ("shifted", "unshifted")
PROBE_GRID = [0.0] + [round(x * 0.01, 2) for x in range(1, 301)]


def alive(K):
    n = K.shape[0]
    return float((K.sum() - n) / (n * (n - 1)))


def kernel_at(q, edges, Z, gamma, convention):
    return S5.k_quantum(q, edges, Z, gamma, convention, LAYERS)


# ------------------------------------------------------------------ (A) the convention probe
def convention_probe(q, edges, Z):
    """Is K_unshifted(gamma') = K_shifted(gamma) for some gamma'?

    Per query gamma: cross_min_resid (min over the UNSHIFTED grid -- the actual question); cross_argmin;
    same_resid_excl_query (min over the SHIFTED grid with the query gamma excluded -- the search's own
    resolution floor at that gamma, given a grid step of 0.01); and same_self_resid (min including the
    query gamma, which must be ~1e-16 and is the positive control on the machinery).
    """
    Ss = {g: kernel_at(q, edges, Z, g, "shifted") for g in PROBE_GRID}
    Su = {g: kernel_at(q, edges, Z, g, "unshifted") for g in PROBE_GRID}
    rows = []
    for g in GAMMAS:
        A = Ss[g]
        na = float(np.linalg.norm(A))
        argmin_u, min_u = None, math.inf
        for gu, K in Su.items():
            r = float(np.linalg.norm(K - A)) / na
            if r < min_u:
                argmin_u, min_u = gu, r
        argmin_s, min_s_excl, min_s_self = None, math.inf, math.inf
        for gs, K in Ss.items():
            r = float(np.linalg.norm(K - A)) / na
            if abs(gs - g) < 1e-12:
                min_s_self = r
                continue
            if r < min_s_excl:
                argmin_s, min_s_excl = gs, r
        # At gamma = 0 the interaction angle of BOTH conventions vanishes and the rank-1 CONSTANT kernel
        # is reached by both, so K_u(0) = K_s(0) EXACTLY for the trivial reason that neither map has any
        # content there.  That is a vacuous match, not a discovered reparameterization, and it is excluded
        # from the verdict rather than read as one.
        #
        # The predicate must test the object it names.  The first version of this check wrote
        # `alive(K) < 1e-12` -- but `alive` is the MEAN OFF-DIAGONAL, which is 1.0 for a CONSTANT kernel
        # and ~0 for a DECORRELATED one, so the predicate flagged the opposite of what it said: it marked
        # no row at all (nothing here is fully decorrelated) and let the one vacuous row through, which
        # then failed the verdict.  The object is "is this kernel the constant matrix", so test that.
        const_s = float(np.max(np.abs(Ss[g] - 1.0)))
        const_u = float(np.max(np.abs(Su[g] - 1.0)))
        rows.append(dict(
            gamma=g, cross_min_resid=min_u, cross_argmin=argmin_u,
            same_self_resid=min_s_self, same_resid_excl_query=min_s_excl,
            same_argmin_excl_query=argmin_s,
            ratio_cross_over_same=(float(min_u / min_s_excl) if min_s_excl > 0 else None),
            alive_shifted=alive(Ss[g]), alive_unshifted=alive(Su[g]),
            # threshold-free evidence that the two conventions are different maps: how differently they
            # respond to bandwidth at all.  Needs no grid step and no arbitrary bar.
            alive_gap=abs(alive(Ss[g]) - alive(Su[g])),
            max_dev_from_constant=const_s, max_dev_from_constant_unshifted=const_u,
            degenerate_constant=bool(max(const_s, const_u) < 1e-12),
        ))
    return rows


# ------------------------------------------------------------------ (B) the metric under both conventions
def metric_shape(q, edges, Z, gamma, convention):
    """2g at x = 0, and the mean 2g over the data summarised by GRAPH DISTANCE.

    `profile` groups the mean off-diagonal magnitude by graph distance, so the profile says how the
    geometry decays with distance -- which is what "the metric is the graph's Laplacian" really asserts.
    """
    g0, _, _ = S4.fs_metric(q, edges, np.zeros(q), convention, LAYERS)
    W0 = 2.0 * g0
    dev_from_identity = float(np.max(np.abs(W0 - 2.0 * np.eye(q))))
    _, Wm, spread = S5.metric_field(q, edges, Z, gamma, convention, LAYERS)
    scale = float(np.mean(np.abs(np.diag(Wm))))
    dist = np.full((q, q), 99)
    for i in range(q):
        dist[i, i] = 0
    for i, j in edges:
        dist[i, j] = dist[j, i] = 1
    for k in range(q):
        for i in range(q):
            for j in range(q):
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]
    prof = {}
    for d in range(1, int(dist[dist < 99].max()) + 1):
        vals = [abs(Wm[i, j]) for i in range(q) for j in range(i + 1, q) if dist[i, j] == d]
        prof["d%d" % d] = float(np.mean(vals)) if vals else 0.0
    on_edge = prof.get("d1", 0.0)
    return dict(conv=convention, gamma=gamma,
                W0_dev_from_2I=dev_from_identity,
                mean_offdiag_over_diag=float(
                    max(abs(Wm[i, j]) for i in range(q) for j in range(i + 1, q)) / scale),
                profile=prof,
                profile_rel={k: (v / on_edge if on_edge else None) for k, v in prof.items()},
                spread_over_data=spread, diag_scale=scale)


# ------------------------------------------------------------------ the grid, per convention
def run_cell(q, edges, Z, alpha, conv, metrics, seed_gen):
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
    A = S5.make_interaction(q, Q_int, alpha, seed_gen)
    f = S5.standardise(S5.target_raw(Z, A))
    var_f = float(f.var(ddof=0))
    rng = np.random.default_rng(seed_gen + 7)
    sigma = NOISE_FRAC * float(f.std(ddof=0))
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
    P = np.linalg.qr(np.random.default_rng(3).normal(size=(q, 3)))[0].T
    Gall = S5.oracle_gram(Z)
    W_cf = S5.closed_form_metric(q, edges, S0.signless_laplacian(q, edges))

    rows = []
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        Kq = kernel_at(q, edges, Z, gamma, conv)
        Kprod = kernel_at(q, [], Z, gamma, conv)
        libraries = {
            "quantum": {1.0: Kq},
            "product": {1.0: Kprod},
            "linear": {1.0: S5.k_linear(Z)},
            "matched": {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S5.S_GRID},
            "closedform": {s: S5.k_mahalanobis(Z, W_cf, gamma, s) for s in S5.S_GRID},
            "rbf": {e: S5.k_rbf_iso(Z, e) for e in S5.ELL2_GRID},
            "randfeat": {e: S5.k_randfeat(Z, P, e) for e in S5.ELL2_GRID},
        }
        per_split = {k: [] for k in list(libraries) + ["oracle"]}
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte, fte = y[tr], y[te], f[te]
            for name, Ks in libraries.items():
                pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                          {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                per_split[name].append(S5.excess_risk(pred, yte, fte, var_f))
            pred, _, _ = S5.krr_tuned({1.0: Gall[np.ix_(tr, tr)]}, ytr, {1.0: Gall[np.ix_(te, tr)]})
            per_split["oracle"].append(S5.excess_risk(pred, yte, fte, var_f))

        def stat(name):
            v = np.array(per_split[name])
            return dict(mean=float(v.mean()), ci=S5.paired_ci(v))

        def delta(name, ref="matched"):
            d = np.array(per_split[name]) - np.array(per_split[ref])
            return dict(mean=float(d.mean()), ci=S5.paired_ci(d))

        rows.append(dict(gamma=gamma, metric_spread=spread, risks={k: stat(k) for k in per_split},
                         delta_vs_matched={k: delta(k) for k in
                                           ("quantum", "randfeat", "rbf", "product", "closedform")},
                         alive=alive(Kq)))
    return dict(alpha=alpha, conv=conv, align_measured=S5.cos_fro(A, Q_int), rows=rows)


def build_report():
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)

    probe = convention_probe(q, edges, Z)
    shapes = [metric_shape(q, edges, Z, g, c) for c in CONVS for g in (0.0, 0.5, 1.0)]

    grids = {}
    for conv in CONVS:
        metrics = {g: S5.metric_field(q, edges, Z, g, conv, LAYERS) for g in GAMMAS}
        grids[conv] = [run_cell(q, edges, Z, a, conv, metrics, S5.SEED_GEN) for a in ALIGNS]

    probe_self_ok = all(r["same_self_resid"] < 1e-12 for r in probe)
    # The verdict is a CLASSIFICATION, not one boolean: a single flag over all rows was too crude a claim
    # for what the table shows, and it is the shape of the finding that matters -- the conventions differ
    # across the band the study uses and coincide only in the limits where both are degenerate.
    #   degenerate rows   -- both kernels constant (vacuous match, excluded from the verdict)
    #   distinct rows     -- cross residual exceeds the search's own resolution at that gamma
    #   coincident rows   -- cross residual at or below the resolution, which at gamma = 3 is the two
    #                        maps reaching the SAME decorrelated regime rather than a coordinate change
    degenerate = [r["gamma"] for r in probe if r["degenerate_constant"]]
    live = [r for r in probe if not r["degenerate_constant"]]
    distinct = [r["gamma"] for r in live if r["cross_min_resid"] > r["same_resid_excl_query"]]
    coincident = [r["gamma"] for r in live if r["cross_min_resid"] <= r["same_resid_excl_query"]]
    gap_row = max(probe, key=lambda r: r["alive_gap"])
    x0_identity = all(abs(s["W0_dev_from_2I"]) < 1e-12
                      for s in shapes if s["conv"] == "unshifted" and s["gamma"] == 0.0)
    pb3 = {}
    for conv in CONVS:
        for cell in grids[conv]:
            leads = [(r["gamma"], r["delta_vs_matched"]["quantum"]["mean"])
                     for r in cell["rows"]
                     if r["delta_vs_matched"]["quantum"]["ci"][1] < 0 and r["gamma"] > 0.0]
            pb3["%s|alpha=%g" % (conv, cell["alpha"])] = dict(
                leads=[g for g, _ in leads], n_leads=len(leads),
                mean_lead_magnitude=(float(np.mean([-d for _, d in leads])) if leads else 0.0))
    # the convention-level comparison PB3 is actually about
    pb3_conv = {}
    for conv in CONVS:
        mags = [m for k, v in pb3.items() if k.startswith(conv) for m in [v["mean_lead_magnitude"]]
                if v["n_leads"]]
        n = sum(v["n_leads"] for k, v in pb3.items() if k.startswith(conv))
        pb3_conv[conv] = dict(n_leads_total=n, mean_of_cell_mean_magnitudes=float(np.mean(mags)) if mags
                              else 0.0)
    return dict(
        round="R392",
        settings=dict(q=q, edges=EDGE_KIND, layers=LAYERS, noise_frac=NOISE_FRAC,
                      n_splits=N_SPLITS, gammas=list(GAMMAS), aligns=list(ALIGNS),
                      convs=list(CONVS), numpy=np.__version__,
                      probe_grid_step=0.01, probe_grid_n=len(PROBE_GRID)),
        controls=dict(
            probe_self_match_residual=[r["same_self_resid"] for r in probe],
            probe_self_match_ok=bool(probe_self_ok),
            probe_resolution_floor=[r["same_resid_excl_query"] for r in probe],
            probe_cross_residual=[r["cross_min_resid"] for r in probe],
            probe_cross_over_floor=[r["ratio_cross_over_same"] for r in probe],
            probe_no_reparameterization=[r["gamma"] for r in live],
            probe_verdict_n_rows=len(live),
            probe_degenerate_rows=degenerate,
            probe_distinct_rows=distinct,
            probe_coincident_rows=coincident,
            probe_alive_curve_max_gap=float(gap_row["alive_gap"]),
            probe_alive_curve_max_gap_gamma=float(gap_row["gamma"]),
            probe_alive_curve_gap_at_3=float([r["alive_gap"] for r in probe if r["gamma"] == 3.0][0]),
            C2_unshifted_metric_is_2I_at_x0=bool(x0_identity),
        ),
        probe=probe, metric_shape=shapes, grids=grids, pb3=pb3, pb3_conv=pb3_conv,
    )


def dumps(rep):
    return json.dumps(rep, sort_keys=True, indent=1)


def main():
    rep = build_report()
    a = dumps(rep)
    b = dumps(build_report())
    rep["controls"]["C6_determinism_byte_identical"] = bool(a == b)
    rep["report_sha256"] = hashlib.sha256(a.encode()).hexdigest()
    a = dumps(rep)
    io.open(OUT, "w", encoding="utf-8").write(a + "\n")
    write_text(rep)
    return 0


def write_text(rep):
    c = rep["controls"]
    s = rep["settings"]
    print("Issue #87 R392 -- PB3's instrument, and the scope of its premise")
    print("  q=%d %s  L=%d  noise=%.2f sigma  splits=%d  numpy=%s"
          % (s["q"], s["edges"], s["layers"], s["noise_frac"], s["n_splits"], s["numpy"]))
    print()
    print("  (A) IS THE CONVENTION CHANGE A COORDINATE CHANGE?   (PB3's premise, part 1)")
    print("      cross = min over the UNSHIFTED grid for a SHIFTED query kernel")
    print("      floor = min over the SHIFTED grid with the query's own gamma excluded -- the search's own")
    print("              resolution at that gamma (grid step %.2f) -- the scale the cross residual must beat"
          % s["probe_grid_step"])
    print()
    print("      gamma  alive_s  alive_u   |gap|    cross_resid  argmin   floor      cross/floor   self_resid")
    for r in rep["probe"]:
        mark = "  [DEGENERATE: both kernels constant]" if r["degenerate_constant"] else ""
        print("      %5.2f  %7.4f  %7.4f  %7.4f   %11.5f  %6.2f   %.5f  %11.1fx   %.2e%s"
              % (r["gamma"], r["alive_shifted"], r["alive_unshifted"], r["alive_gap"],
                 r["cross_min_resid"], r["cross_argmin"], r["same_resid_excl_query"],
                 r["ratio_cross_over_same"], r["same_self_resid"], mark))
    print("      positive control -- the search returns the query's own gamma: %s"
          % c["probe_self_match_ok"])
    print("      THRESHOLD-FREE EVIDENCE the conventions are different maps: the largest gap between")
    print("        their bandwidth responses is %.4f of the mean off-diagonal, at gamma = %.2f"
          % (c["probe_alive_curve_max_gap"], c["probe_alive_curve_max_gap_gamma"]))
    print("      VERDICT (a classification, not one boolean) over %d non-degenerate rows:"
          % c["probe_verdict_n_rows"])
    print("        distinct (cross residual ABOVE the search's own resolution): %s" % c["probe_distinct_rows"])
    print("        coincident (at or below it): %s" % c["probe_coincident_rows"])
    print("        degenerate rows excluded: %s   -- at gamma = 0 both conventions reach the CONSTANT"
          % c["probe_degenerate_rows"])
    print("        kernel, so a match there is vacuous, not a discovered reparameterization")
    print()
    print("  (B) WHAT IS THE UNSHIFTED METRIC?   (PB3's premise, part 2)")
    print("      conv        gamma   |2g(x=0)-2I|   max|offd|/diag   mean |offdiag| by graph distance")
    for sh in rep["metric_shape"]:
        pr = "  ".join("d%d=%.4f" % (d, sh["profile"]["d%d" % d]) for d in (1, 2, 3)
                       if "d%d" % d in sh["profile"])
        rel = "  ".join("d%d/d1=%.4f" % (d, sh["profile_rel"]["d%d" % d]) for d in (1, 2, 3)
                        if sh["profile_rel"].get("d%d" % d) is not None)
        print("      %-10s  %5.2f   %12.2e   %15.4f   %s" % (sh["conv"], sh["gamma"],
                                                             sh["W0_dev_from_2I"],
                                                             sh["mean_offdiag_over_diag"], pr))
        print("      %-10s  %5.2f   %12s   %15s   %s" % ("", sh["gamma"], "", "", rel))
    print("      C2 the unshifted metric IS exactly 2I at x = 0 (R390's measurement, re-taken): %s"
          % c["C2_unshifted_metric_is_2I_at_x0"])
    print()
    print("  THE PB3 READ -- quantum vs its OWN metric-matched rival, per convention")
    print("  (delta = quantum - matched; a NEGATIVE CI is a lead.  'spread' = the convention's metric")
    print("   variation over the data; 'alive' = mean off-diagonal of the quantum kernel)")
    print()
    for conv in CONVS:
        print("  --- %s ---" % conv)
        print("   alpha  gamma  alive   spread  quantum [95% CI]            matched [95% CI]            rbf      randfeat  oracle   delta [95% CI]           lead?")
        for cell in rep["grids"][conv]:
            for r in cell["rows"]:
                rk = r["risks"]
                d = r["delta_vs_matched"]["quantum"]
                lead = "YES" if d["ci"][1] < 0 else ("no" if d["ci"][0] > 0 else "tie")
                print("   %5.1f  %5.2f  %5.3f  %6.3f  %8.4f [%6.4f,%6.4f] %8.4f [%6.4f,%6.4f] %8.4f %9.4f %8.4f  %+7.4f [%+6.4f,%+6.4f]  %s"
                      % (cell["alpha"], r["gamma"], r["alive"], r["metric_spread"],
                         rk["quantum"]["mean"], rk["quantum"]["ci"][0], rk["quantum"]["ci"][1],
                         rk["matched"]["mean"], rk["matched"]["ci"][0], rk["matched"]["ci"][1],
                         rk["rbf"]["mean"], rk["randfeat"]["mean"], rk["oracle"]["mean"],
                         d["mean"], d["ci"][0], d["ci"][1], lead))
        print()
    print("  PB3 SUMMARY -- bandwidths (gamma > 0) at which the quantum kernel leads its matched rival.")
    print("  NO FDR CONTROL HERE YET (the registration requires it before a lead is DECLARED), so these")
    print("  counts are an upper bound on the true discoveries; magnitudes are quoted alongside them.")
    for k in sorted(rep["pb3"]):
        v = rep["pb3"][k]
        print("     %-18s %d lead(s), mean magnitude %.4f%s"
              % (k, v["n_leads"], v["mean_lead_magnitude"],
                 (": gamma = " + str(v["leads"])) if v["leads"] else ""))
    print()
    print("     convention aggregate:  shifted: %d leads, mean-of-cell-mean-magnitude %.4f"
          % (rep["pb3_conv"]["shifted"]["n_leads_total"],
             rep["pb3_conv"]["shifted"]["mean_of_cell_mean_magnitudes"]))
    print("                            unshifted: %d leads, mean-of-cell-mean-magnitude %.4f"
          % (rep["pb3_conv"]["unshifted"]["n_leads_total"],
             rep["pb3_conv"]["unshifted"]["mean_of_cell_mean_magnitudes"]))
    print()
    print("  C6 report byte-identical on rebuild = %s" % c["C6_determinism_byte_identical"])
    print("  report sha256 = %s" % rep["report_sha256"])
    print("  written to %s" % os.path.basename(OUT))


if __name__ == "__main__":
    sys.exit(main())
