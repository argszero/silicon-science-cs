#!/usr/bin/env python3
"""Issue #87 -- R394: replace zero-anchored p-values with a SIMULATED null band, and validate the layer
on an exchangeability arm.

WHY THIS ROUND EXISTS.  R393 built the multiplicity layer and its size control FAILED: 47-50 % false
declarations at a nominal 5 %, and the cause was not the resampling design (the within-split SE was
unbiased, 0.67-1.46x of the across-seed truth) but a SYSTEMATIC bias -- on a pure-noise target the two
arms are not exchangeable, because the map-fixed kernel shrinks to a nearly constant kernel and that is
optimal when there is no signal.  The null band it measured was +-0.06, i.e. the same size as several
"leads" the study had been reporting (Class 86).

WHAT IS BUILT HERE.

  1. A CALIBRATED NULL BAND per bandwidth, from N_CAL independent pure-noise cells, replacing zero as the
     yardstick.  Resolution 1/(N_CAL+1) < q is asserted, not assumed.
  2. The band's own SIZE: a SECOND, independent family of pure-noise cells (different seed stream) is read
     against the band, and the false-declaration rate is reported with a binomial interval.  A band that
     has never been shown to be the right size is decoration.
  3. An EXCHANGEABILITY arm.  Note what does NOT work: giving both arms the SAME kernel makes the paired
     difference identically zero and tests nothing (both arms go through one fitting function).  The
     construction that IS exchangeable is to randomise the ARM each split gets -- equivalently to keep
     |d| and flip the sign of each paired difference -- which is exactly the symmetry the sign-flip test
     and the paired bootstrap assume.  On that arm the machinery must read ~5 %.  R393 measured this once
     on a fixed randomisation; here it is repeated over 40 independent randomisations, and BH is run over
     the whole family each time.
  4. THE OLD PROCEDURE RUNS ALONGSIDE.  For every null family the v7-style zero-anchored marginal rate is
     recomputed on the SAME deltas, so the report shows the fix as a difference and not as a new number.
  5. The R393 defect fixes: the degeneracy predicate is KERNEL-keyed (max|Kq - K_rival| < 1e-12), which
     excludes the gamma = 0 rows by measurement instead of by a threshold on a round-off mean, and every
     count is reported two-sided with leads and losses in separate fields.

Run:  /usr/bin/python3 smoke_v8.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Writes smoke_v8_results.json beside this file.  Several minutes: 80 pure-noise cells dominate.
"""
import hashlib
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S0
import smoke_v5 as S5
import smoke_v7 as S7

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v8_results.json")

QUBITS = 6
LAYERS = 2
EDGE_KIND = "cycle"
CONVS = ("shifted", "unshifted")
ALIGNS = (1.0, 0.0, -1.0)
GAMMAS = S5.GAMMAS
N_SPLITS = 120
N_CAL = 40                     # calibration cells per family: resolution 1/(N_CAL+1) = 0.024 < 0.05
N_VAL = 20                     # independent validation cells per convention (bands are read, not built)
N_EXCH = 40                    # independent arm-randomisations for the exchangeability arm
CAL_SEED0 = 7000
VAL_SEED0 = 9000
EXCH_SEED0 = 11000
Q_LEVELS = (0.05, 0.10)
KERNEL_SAME_EPS = 1e-12        # kernel-keyed degeneracy: measured separation is 4.4e-16 vs >= 1e-1
CELL_DELTAS = {}               # (cell key, gamma) -> the delta array, so an arm reads the SAME object


# ------------------------------------------------------------------ cell runners
def _fit_risks(Ks_tr, Ks_te, ytr, yte, fte, var_f, mode):
    """One arm's per-split risk, through the ONE shared fitting protocol.  Arms differ in kernels only."""
    pred, _, _ = S5.krr_tuned(Ks_tr, ytr, Ks_te)
    if mode == "noise":
        return float(np.mean((pred - yte) ** 2) / S5.NOISE_FRAC ** 2)
    return S5.excess_risk(pred, yte, fte, var_f)


def real_cell(q, edges, Z, alpha, conv, metrics, seed_gen):
    """A signal cell: planted interaction A at alignment `alpha`, matched Mahalanobis rival.

    Returns per-bandwidth paired differences (quantum - rival), the rival kernel's distance from the
    quantum kernel (the degeneracy key), and the quantum kernel's health.
    """
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
    A = S5.make_interaction(q, Q_int, alpha, seed_gen)
    f = S5.standardise(S5.target_raw(Z, A))
    var_f = float(f.var(ddof=0))
    rng = np.random.default_rng(seed_gen + 7)
    sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
    out = {}
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
        rival = {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S5.S_GRID}
        kdiff = float(np.max(np.abs(Kq - rival[min(S5.S_GRID)])))
        d = []
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte, fte = y[tr], y[te], f[te]
            rq = _fit_risks({1.0: Kq[np.ix_(tr, tr)]}, {1.0: Kq[np.ix_(te, tr)]}, ytr, yte, fte, var_f, "excess")
            rr = _fit_risks({s: K[np.ix_(tr, tr)] for s, K in rival.items()},
                            {s: K[np.ix_(te, tr)] for s, K in rival.items()}, ytr, yte, fte, var_f, "excess")
            d.append(rq - rr)
        out[gamma] = dict(delta=np.array(d), mean=float(np.mean(d)), ci=S5.paired_ci(np.array(d)),
                          spread=spread, kernel_max_absdiff=kdiff)
    return dict(alpha=alpha, conv=conv, rows=out)


def null_cell(q, edges, Z, conv, metrics, seed_gen):
    """A pure-noise cell: the target is noise, so the Bayes predictor is the zero function and every risk
    is in units of the noise variance.  Nothing here is a discovery; this is the yardstick."""
    rng = np.random.default_rng(seed_gen + 7)
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [rng.normal(scale=S5.NOISE_FRAC, size=n) for _ in range(N_SPLITS)]
    out = {}
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
        rival = {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S5.S_GRID}
        kdiff = float(np.max(np.abs(Kq - rival[min(S5.S_GRID)])))
        d = []
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte = y[tr], y[te]
            rq = _fit_risks({1.0: Kq[np.ix_(tr, tr)]}, {1.0: Kq[np.ix_(te, tr)]}, ytr, yte, None, None, "noise")
            rr = _fit_risks({s: K[np.ix_(tr, tr)] for s, K in rival.items()},
                            {s: K[np.ix_(te, tr)] for s, K in rival.items()}, ytr, yte, None, None, "noise")
            d.append(rq - rr)
        out[gamma] = dict(delta=np.array(d), mean=float(np.mean(d)), spread=spread,
                          kernel_max_absdiff=kdiff)
    return dict(conv=conv, seed=seed_gen, rows=out)


def band_from_means(means, lo=2.5, hi=97.5):
    """The empirical null band: percentiles of independent null cell means.  Not an interval for a normal
    -- the null is skewed (R393: skew -0.71..-2.36), and the percentiles need no shape assumption."""
    v = np.sort(np.asarray(means, dtype=float))
    return [float(np.percentile(v, lo)), float(np.percentile(v, hi))], v


def empirical_p(x, null_means):
    """Two-sided empirical p-value with the resolution floor made explicit: (k+1)/(N+1)."""
    v = np.asarray(null_means, dtype=float)
    N = len(v)
    ge = float(np.sum(v >= x) + 1) / (N + 1)
    le = float(np.sum(v <= x) + 1) / (N + 1)
    return float(min(1.0, 2.0 * min(ge, le)))


def wilson(k, n, z=1.96):
    """Wilson score interval -- the census family's own convention, reused here for a rate."""
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def zero_anchored_p(d, n_flip=2000, n_boot=1000):
    """R393's three routes at a reduced resampling budget, for the SAME deltas -- the comparison arm."""
    d = np.asarray(d, dtype=float)
    N = len(d)
    rng = np.random.default_rng(101)
    obs = abs(float(d.mean()))
    signs = rng.integers(0, 2, size=(n_flip, N)) * 2.0 - 1.0
    p_flip = float((np.sum(np.abs((signs * d).mean(axis=1)) >= obs) + 1) / (n_flip + 1))
    rng = np.random.default_rng(202)
    means = d[rng.integers(0, N, size=(n_boot, N))].mean(axis=1)
    p_boot = 2.0 * float(np.mean(means >= 0.0)) if d.mean() <= 0 else 2.0 * float(np.mean(means <= 0.0))
    p_boot = float(min(1.0, max(p_boot, 1.0 / (n_boot + 1))))
    se = float(d.std(ddof=1)) / math.sqrt(N)
    p_norm = 1.0 if se <= 0 else float(min(1.0, math.erfc((abs(float(d.mean())) / se) / math.sqrt(2.0))))
    return p_flip, p_boot, p_norm


# ------------------------------------------------------------------ the report
def build_report():
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in GAMMAS} for c in CONVS}

    # ---- the declared family: the whole grid, degeneracy keyed on the KERNELS
    grid = {}
    for conv in CONVS:
        for alpha in ALIGNS:
            grid["%s|alpha=%g" % (conv, alpha)] = real_cell(q, edges, Z, alpha, conv, metrics[conv],
                                                           S5.SEED_GEN)
    family = []
    for key, cell in grid.items():
        for gamma, row in cell["rows"].items():
            family.append(dict(cell=key, gamma=gamma, conv=cell["conv"], alpha=cell["alpha"],
                               delta_mean=row["mean"], ci_zero=row["ci"],
                               kernel_max_absdiff=row["kernel_max_absdiff"], spread=row["spread"],
                               degenerate=bool(row["kernel_max_absdiff"] < KERNEL_SAME_EPS)))
    same_rows = [r for r in family if r["degenerate"]]
    testable = [r for r in family if not r["degenerate"]]

    # ---- CALIBRATION: independent pure-noise cells -> a band per (convention, bandwidth)
    cal = {c: [null_cell(q, edges, Z, c, metrics[c], CAL_SEED0 + 37 * i) for i in range(N_CAL)]
           for c in CONVS}
    val = {c: [null_cell(q, edges, Z, c, metrics[c], VAL_SEED0 + 53 * i) for i in range(N_VAL)]
           for c in CONVS}
    band, cal_means, val_means = {}, {}, {}
    for c in CONVS:
        band[c], cal_means[c], val_means[c] = {}, {}, {}
        for g in GAMMAS:
            cm = [cell["rows"][g]["mean"] for cell in cal[c]]
            vm = [cell["rows"][g]["mean"] for cell in val[c]]
            band[c][g] = band_from_means(cm)[0]
            cal_means[c][g] = cm
            val_means[c][g] = vm

    # ---- the band's own SIZE, read on the independent validation family
    size_rows, k_tot, n_tot = [], 0, 0
    for c in CONVS:
        for g in GAMMAS:
            b = band[c][g]
            hits = [x for x in val_means[c][g] if x < b[0] or x > b[1]]
            size_rows.append(dict(conv=c, gamma=g, n=len(val_means[c][g]), n_outside=len(hits),
                                  band=b, rate=len(hits) / max(1, len(val_means[c][g]))))
            if g != 0.0:                              # gamma = 0 is degenerate, not a test
                k_tot += len(hits)
                n_tot += len(val_means[c][g])

    # ---- the OLD (zero-anchored, v7-style) rate on the SAME nulls, both families, both conventions
    old = dict(m_tests=0, marginal_cal=0, marginal_val=0, bh05_cal=0, bh05_val=0,
               n_cal_tests=0, n_val_tests=0)
    for c in CONVS:
        for tag, fam in (("cal", cal[c]), ("val", val[c])):
            ps, marg = [], 0
            for cell in fam:
                for g in GAMMAS:
                    if g == 0.0:
                        continue
                    d = cell["rows"][g]["delta"]
                    ps.append(zero_anchored_p(d)[0])
                    ci = S5.paired_ci(d)
                    if ci[0] > 0.0 or ci[1] < 0.0:
                        marg += 1
            old["m_tests"] += len(ps)
            old["marginal_" + tag] += marg
            old["bh05_" + tag] += S7.bh_qvalues(np.array(ps), 0.05)[1]
            old["n_" + tag + "_tests"] += len(ps)

    # ---- the real read: empirical p-value against the band, then BH across the family
    p_emp, p_zero = [], []
    for r in testable:
        nm = cal_means[r["conv"]][r["gamma"]]
        r["p_emp"] = empirical_p(r["delta_mean"], nm)
        r["band"] = band[r["conv"]][r["gamma"]]
        r["outside_band"] = bool(r["delta_mean"] < r["band"][0] or r["delta_mean"] > r["band"][1])
        pf, pb, pn = zero_anchored_p(grid[r["cell"]]["rows"][r["gamma"]]["delta"])
        r["p_flip_zero"], r["p_boot_zero"], r["p_norm_zero"] = pf, pb, pn
        r["route_gap"] = float(max(abs(pf - pb), abs(pf - pn), abs(pb - pn)))
        r["sign"] = "loss" if r["delta_mean"] > 0 else "lead"
        p_emp.append(r["p_emp"])
        p_zero.append(pf)
    qe05, ke05 = S7.bh_qvalues(np.array(p_emp), 0.05)
    qe10, ke10 = S7.bh_qvalues(np.array(p_emp), 0.10)
    qeb, keb = S7.by_qvalues(np.array(p_emp), 0.05)
    qz05, kz05 = S7.bh_qvalues(np.array(p_zero), 0.05)
    for i, r in enumerate(testable):
        r["q_emp_bh05"] = float(qe05[i])
        r["q_emp_bh10"] = float(qe10[i])
        r["q_emp_by05"] = float(qeb[i])
        r["q_zero_bh05"] = float(qz05[i])

    declared = [r for r in testable if r["q_emp_bh05"] <= 0.05]
    zero_decl = [r for r in testable if r["q_zero_bh05"] <= 0.05]
    CELL_DELTAS.clear()
    for key, cell in grid.items():
        for g, row in cell["rows"].items():
            CELL_DELTAS[(key, g)] = row["delta"]
    return dict(
        round="R394",
        settings=dict(q=q, edges=EDGE_KIND, layers=LAYERS, convs=list(CONVS), aligns=list(ALIGNS),
                      gammas=list(GAMMAS), n_splits=N_SPLITS, n_cal=N_CAL, n_val=N_VAL, n_exch=N_EXCH,
                      cal_seed0=CAL_SEED0, val_seed0=VAL_SEED0, kernel_same_eps=KERNEL_SAME_EPS,
                      numpy=np.__version__),
        controls=dict(
            C1_band_resolution=dict(one_over_n_plus_1=1.0 / (N_CAL + 1), q_levels=list(Q_LEVELS),
                                    resolution_below_q=bool(1.0 / (N_CAL + 1) < min(Q_LEVELS))),
            C2_band_size_validation=dict(rows=size_rows, pooled_k=k_tot, pooled_n=n_tot,
                                         pooled_rate=k_tot / max(1, n_tot), pooled_wilson=wilson(k_tot, n_tot)),
            C4_old_zero_anchored_on_same_nulls=old,
            C5_degeneracy_kernel_keyed=dict(
                excluded=[dict(cell=r["cell"], gamma=r["gamma"],
                               kernel_max_absdiff=r["kernel_max_absdiff"]) for r in same_rows],
                min_kernel_absdiff_kept=float(min(r["kernel_max_absdiff"] for r in testable)),
                eps=KERNEL_SAME_EPS),
            C6_route_agreement_zero_anchored=dict(
                max_gap=float(max(r["route_gap"] for r in testable)),
                over_1em3=[[r["cell"], r["gamma"], r["route_gap"]] for r in testable
                           if r["route_gap"] > 1e-3]),
            C8_band_width=dict(**{c: {str(g): [band[c][g][0], band[c][g][1],
                                               band[c][g][1] - band[c][g][0]] for g in GAMMAS}
                                  for c in CONVS}),
        ),
        family=family, testable_m=len(testable), degenerate_m=len(same_rows),
        fdr_emp=dict(m=len(testable), n_declared_bh05=ke05, n_declared_bh10=ke10, n_declared_by05=keb,
                     n_leads=int(sum(r["sign"] == "lead" for r in declared)),
                     n_losses=int(sum(r["sign"] == "loss" for r in declared)),
                     declared=[[r["cell"], r["gamma"], r["delta_mean"], r["p_emp"], r["q_emp_bh05"],
                                r["sign"]] for r in declared]),
        fdr_zero=dict(m=len(testable), n_declared_bh05=kz05,
                      n_leads=int(sum(r["sign"] == "lead" for r in zero_decl)),
                      n_losses=int(sum(r["sign"] == "loss" for r in zero_decl)),
                      declared=[[r["cell"], r["gamma"], r["delta_mean"], r["p_flip_zero"],
                                 r["q_zero_bh05"], r["sign"]] for r in zero_decl]),
        cal_means={c: {str(g): cal_means[c][g] for g in GAMMAS} for c in CONVS},
        val_means={c: {str(g): val_means[c][g] for g in GAMMAS} for c in CONVS},
    )


def dumps(rep):
    return json.dumps(rep, sort_keys=True, indent=1)


def main():
    rep = build_report()
    rep["controls"]["C3_exchangeability"] = exchangeability_report(
        [((r["conv"], r["gamma"]), CELL_DELTAS[(r["cell"], r["gamma"])]) for r in rep["family"]
         if not r["degenerate"]])

    # ---- determinism: a full second report would double a 6-minute run, so the check is aimed at the
    # dominant cost (one calibration cell re-derived from scratch) and reports bitwise equality.
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in GAMMAS} for c in CONVS}
    rec = null_cell(q, edges, Z, "shifted", metrics["shifted"], CAL_SEED0)
    stored = rep["cal_means"]["shifted"]
    same = all(rec["rows"][g]["mean"] == stored[str(g)][0] for g in GAMMAS)
    rep["controls"]["C7_determinism_spot_check"] = dict(
        what="cal[shifted][0] re-derived from scratch after the report was built",
        per_gamma_identical=same,
        stored=[stored[str(g)][0] for g in GAMMAS],
        recomputed=[rec["rows"][g]["mean"] for g in GAMMAS])

    a = dumps(rep)
    rep["report_sha256"] = hashlib.sha256(a.encode()).hexdigest()
    io.open(OUT, "w", encoding="utf-8").write(dumps(rep) + "\n")
    write_text(rep)
    return 0


def write_text(rep):
    ctl = rep["controls"]
    print("=" * 100)
    print("ISSUE #87 -- R394: a calibrated null band, its own size, and the exchangeability arm")
    print("=" * 100)
    print("family: m = %d usable rows (degenerate excluded: %d), N_CAL = %d, N_VAL = %d per convention"
          % (rep["testable_m"], rep["degenerate_m"], N_CAL, N_VAL))
    print("band resolution 1/(N_CAL+1) = %.4f < q_lo = %.2f : %s"
          % (ctl["C1_band_resolution"]["one_over_n_plus_1"], min(Q_LEVELS),
             ctl["C1_band_resolution"]["resolution_below_q"]))
    print()
    print("-- C2 the band's OWN SIZE, read on an independent pure-noise family ---------------------")
    print("   pooled: %d of %d tests outside the 95 %% band = %.4f  Wilson95 [%.4f, %.4f]"
          % (ctl["C2_band_size_validation"]["pooled_k"], ctl["C2_band_size_validation"]["pooled_n"],
             ctl["C2_band_size_validation"]["pooled_rate"],
             ctl["C2_band_size_validation"]["pooled_wilson"][0],
             ctl["C2_band_size_validation"]["pooled_wilson"][1]))
    for r in ctl["C2_band_size_validation"]["rows"]:
        if r["gamma"] == 0.0:
            continue
        print("     %-9s gamma=%4.2f  band [%+0.4f,%+0.4f]  outside %2d/%2d"
              % (r["conv"], r["gamma"], r["band"][0], r["band"][1], r["n_outside"], r["n"]))
    print()
    print("-- C3 exchangeability arm (arm randomised per split; the machinery must read ~5 %%) ---------")
    ex = ctl["C3_exchangeability"]
    for rt in ("signflip", "bootstrap", "normal"):
        print("   %-10s rate %.4f  Wilson95 [%.4f,%.4f]" % (rt, ex["rate_" + rt], ex["wilson_" + rt][0],
                                                            ex["wilson_" + rt][1]))
    print("   BH over the family: %.4f  Wilson95 [%.4f,%.4f]"
          % (ex["rate_bh_family"], ex["wilson_bh_family"][0], ex["wilson_bh_family"][1]))
    print()
    print("-- C4 the OLD zero-anchored procedure, on the SAME nulls --------------------------------")
    o = ctl["C4_old_zero_anchored_on_same_nulls"]
    print("   marginal CI rate: cal %d/%d = %.3f   val %d/%d = %.3f"
          % (o["marginal_cal"], o["n_cal_tests"], o["marginal_cal"] / max(1, o["n_cal_tests"]),
             o["marginal_val"], o["n_val_tests"], o["marginal_val"] / max(1, o["n_val_tests"])))
    print("   BH q=0.05 declarations: cal %d, val %d" % (o["bh05_cal"], o["bh05_val"]))
    print()
    print("-- the real read -------------------------------------------------------------------------")
    print("   calibrated (empirical band + BH): m=%d declared %d (leads %d, losses %d) | BY %d"
          % (rep["fdr_emp"]["m"], rep["fdr_emp"]["n_declared_bh05"], rep["fdr_emp"]["n_leads"],
             rep["fdr_emp"]["n_losses"], rep["fdr_emp"]["n_declared_by05"]))
    print("   zero-anchored (R393):             m=%d declared %d (leads %d, losses %d)"
          % (rep["fdr_zero"]["m"], rep["fdr_zero"]["n_declared_bh05"], rep["fdr_zero"]["n_leads"],
             rep["fdr_zero"]["n_losses"]))
    print()
    print("   DECLARED under the calibrated band:")
    for row in sorted(rep["fdr_emp"]["declared"], key=lambda r: r[3]):
        print("     %-18s gamma=%4.2f delta %+0.4f  p_emp=%.4f  q=%.4f  %s"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
    print()
    print("   Rows the calibrated procedure does NOT declare but the old one did:")
    emp_keys = set((r[0], r[1]) for r in rep["fdr_emp"]["declared"])
    for row in rep["fdr_zero"]["declared"]:
        if (row[0], row[1]) not in emp_keys:
            print("     %-18s gamma=%4.2f delta %+0.4f  p_zero=%.4f  q=%.4f  %s"
                  % (row[0], row[1], row[2], row[3], row[4], row[5]))
    print()
    print("   report sha256 = %s" % rep["report_sha256"])
    print("   written to %s" % os.path.basename(OUT))


def exchangeability_report(deltas_by_conv_gamma):
    """The EXCHANGEABILITY arm: randomise the arm each split gets (keep |d|, flip signs).  On this arm the
    paired differences ARE symmetric about zero, so the R393 machinery must read ~5 % -- machinery that
    cannot pass its own assumption is not evidence about the data."""
    rows, k_by_route = [], {"signflip": 0, "bootstrap": 0, "normal": 0, "bh_family": 0}
    n_tests = 0
    for i in range(N_EXCH):
        rng = np.random.default_rng(EXCH_SEED0 + 11 * i)
        ps_f, ps_b, ps_n = [], [], []
        for (conv, g), d in deltas_by_conv_gamma:
            sgn = rng.integers(0, 2, size=len(d)) * 2.0 - 1.0
            ds = d * sgn
            pf, pb, pn = zero_anchored_p(ds)
            ps_f.append(pf)
            ps_b.append(pb)
            ps_n.append(pn)
        k_by_route["signflip"] += int(np.sum(np.array(ps_f) < 0.05))
        k_by_route["bootstrap"] += int(np.sum(np.array(ps_b) < 0.05))
        k_by_route["normal"] += int(np.sum(np.array(ps_n) < 0.05))
        k_by_route["bh_family"] += S7.bh_qvalues(np.array(ps_f), 0.05)[1]
        n_tests += len(ps_f)
        if i < 3:
            rows.append(dict(rep=i, m=len(ps_f), n_flip=len(ps_f),
                             n_marginal_signflip=int(np.sum(np.array(ps_f) < 0.05))))
    out = dict(n_randomisations=N_EXCH, n_tests_per_randomisation=len(deltas_by_conv_gamma),
               nominal=0.05, n_tests=n_tests)
    for rt in ("signflip", "bootstrap", "normal"):
        out["rate_" + rt] = k_by_route[rt] / max(1, n_tests)
        out["wilson_" + rt] = wilson(k_by_route[rt], n_tests)
    out["rate_bh_family"] = k_by_route["bh_family"] / max(1, N_EXCH)
    out["wilson_bh_family"] = wilson(k_by_route["bh_family"], N_EXCH)
    out["first_reps"] = rows
    return out



if __name__ == "__main__":
    sys.exit(main())
