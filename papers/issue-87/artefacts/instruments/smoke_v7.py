#!/usr/bin/env python3
"""Issue #87 -- R393: FDR control across the declared grid, and the correction layer's own validation.

WHY THIS ROUND EXISTS.  The registration's success metric says "advantage declared only when the CI
excludes 0, with FDR control across the grid".  R391 and R392 reported lead COUNTS (6 of 21, 6 of 21 per
convention) taken from marginal 95% CIs and said so in their own text -- but a marginal CI is not a
declared discovery.  With 36 correlated cells in the family, roughly one in twenty marginal intervals
excludes 0 by chance alone, so the uncorrected counts are an UPPER BOUND and are not evidence for any
individual cell.  This file builds the correction layer and -- this is the part that matters -- VALIDATES
it, because a multiplicity procedure that has never been shown to be the right SIZE when nothing is there,
or to have POWER when something is, is decoration.

WHAT IS MEASURED.

  * The declared family: the whole q = 6 / cycle / L = 2 grid (2 phase conventions x 3 alignment levels x
    7 bandwidths).  The gamma = 0 rows are excluded as degenerate BY CONSTRUCTION and their p-values are
    still reported.  At zero bandwidth every data point shares one angle vector, so the quantum kernel and
    its matched rival are the SAME constant kernel and the paired difference is identically zero.  Nothing
    is hidden by the exclusion -- the rows are in the report.
  * Three INDEPENDENT p-value routes per cell, because a p-value is an instrument and owes a control:
      - sign-flip permutation (exact under symmetry of the paired differences about 0),
      - percentile bootstrap of the paired difference,
      - normal approximation from the paired mean and its standard error.
    Their maximum discrepancy is reported (C4).  Where routes disagree materially, no p-value is trusted.
  * Two multiplicity procedures: Benjamini-Hochberg at q = 0.05 and 0.10, plus Benjamini-Yekutieli (valid
    under ARBITRARY dependence -- which matters here because neighbouring bandwidths share resampling noise).
  * SIZE (C1): null cells (planted A = 0, so the target is pure noise) across 8 independent seeds.  The null
    p-values are pooled and tested for uniformity (KS) and the false declarations are counted.  A
    correction layer that declares discoveries on a null is broken.
  * POWER (C2) -- and this is the registration's own PLANTED-ALIGNMENT CONTROL: a ladder that handicaps
    the rival by withholding a DECLARED fraction of the map's geometry,
        W_t = (1 - t) * W_map + t * diag(W_map),
    so t = 0 is the fully matched rival, t = 0.5 withholds half the graph structure, t = 1 leaves only the
    diagonal.  The ladder answers the question the fallback clause asks: WOULD THIS PIPELINE HAVE FOUND AN
    ADVANTAGE IF ONE EXISTED?  If the corrected procedure declares nothing even at t = 1 the near-empty map
    is uninformative; if it declares at some t* and not below, t* bounds how much geometry the rival may be
    given before the advantage disappears -- a statement about the study, not about the procedure.

Run:  /usr/bin/python3 smoke_v7.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Writes smoke_v7_results.json beside this file.
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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v7_results.json")

QUBITS = 6
LAYERS = 2
EDGE_KIND = "cycle"
CONVS = ("shifted", "unshifted")
ALIGNS = (1.0, 0.0, -1.0)
GAMMAS = S5.GAMMAS                      # includes 0.0, which is degenerate by construction
N_SPLITS = 120                          # the registration asks for >= 100 resampled splits
N_FLIP = 10000
N_BOOT = 4000
N_NULL_SEEDS = 8
HANDICAP_LEVELS = (0.0, 0.25, 0.5, 1.0)
Q_LEVELS = (0.05, 0.10)


# ------------------------------------------------------------------ p-value routes
def signflip_p(d, n_flip=N_FLIP, seed=101):
    """Exact-under-symmetry permutation p: flip the sign of each paired difference at random.

    Under H0 (the paired differences are symmetric about 0) every one of the 2^n sign patterns is equally
    likely, so the fraction of patterns whose |mean| reaches the observed |mean| is a valid p-value that
    needs no centring, no distributional assumption beyond symmetry, and no grid step.
    """
    d = np.asarray(d, dtype=float)
    rng = np.random.default_rng(seed)
    obs = abs(float(d.mean()))
    signs = rng.integers(0, 2, size=(n_flip, len(d))) * 2.0 - 1.0
    means = np.abs((signs * d).mean(axis=1))
    return float((np.sum(means >= obs) + 1) / (n_flip + 1))


def boot_p(d, n_boot=N_BOOT, seed=202):
    """Percentile bootstrap p: the bootstrap distribution's mass on the wrong side of zero, doubled."""
    d = np.asarray(d, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(d)
    means = d[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    if d.mean() <= 0:
        p = 2.0 * float(np.mean(means >= 0.0))
    else:
        p = 2.0 * float(np.mean(means <= 0.0))
    return float(min(1.0, max(p, 1.0 / (n_boot + 1))))


def normal_p(d):
    """Asymptotic two-sided p from the paired mean and its standard error (normal at n = 120)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    se = float(d.std(ddof=1)) / math.sqrt(n)
    if se <= 0.0:
        return 1.0
    z = abs(float(d.mean())) / se
    return float(max(0.0, min(1.0, math.erfc(z / math.sqrt(2.0)))))


# ------------------------------------------------------------------ multiplicity
def bh_qvalues(p, q):
    """Benjamini-Hochberg step-up q-values and the number of rejections at level q.

    q_i = min_{j >= i} p_(j) * m / j over the sorted p-values; reject every p_(i) with q_(i) <= q.
    """
    p = np.asarray(p, dtype=float)
    m = len(p)
    order = np.argsort(p, kind="stable")
    ps = p[order]
    qv = np.empty(m)
    running = 1.0
    for i in range(m - 1, -1, -1):
        val = ps[i] * m / (i + 1)
        running = min(running, val)
        qv[i] = running
    out = np.empty(m)
    out[order] = np.minimum(qv, 1.0)
    return out, int(np.sum(out <= q))


def by_qvalues(p, q):
    """Benjamini-Yekutieli: BH with the sum(1/i) inflation -- valid under ARBITRARY dependence."""
    m = len(p)
    c = float(np.sum(1.0 / np.arange(1, m + 1)))
    p = np.asarray(p, dtype=float)
    order = np.argsort(p, kind="stable")
    ps = p[order]
    qv = np.empty(m)
    running = 1.0
    for i in range(m - 1, -1, -1):
        val = ps[i] * m * c / (i + 1)
        running = min(running, val)
        qv[i] = running
    out = np.empty(m)
    out[order] = np.minimum(qv, 1.0)
    return out, int(np.sum(out <= q))


def ks_uniform(p):
    """Two-sided Kolmogorov-Smirnov statistic and asymptotic p against Uniform(0,1)."""
    p = np.sort(np.asarray(p, dtype=float))
    n = len(p)
    if n == 0:
        return 0.0, 1.0
    d = float(np.max(np.maximum(np.arange(1, n + 1) / n - p, p - np.arange(0, n) / n)))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    kp = 2.0 * sum((-1) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam) for j in range(1, 40))
    return d, float(max(0.0, min(1.0, kp)))


# ------------------------------------------------------------------ the cell runner
def cell_deltas(q, edges, Z, alpha, conv, metrics, seed_gen, W_rival_fn):
    """Per-split paired differences (quantum - rival) at every bandwidth, plus the quantum kernel's health.

    `W_rival_fn(gamma, W_mean)` returns the rival's precision matrix at that bandwidth, so the IDENTICAL
    code path serves the fully matched rival (the map's own mean metric), the handicap ladder, and the
    null -- which is what makes the ladder a legitimate power arm rather than a second experiment.
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
    Gall = S5.oracle_gram(Z)

    out = {}
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        W_r = W_rival_fn(gamma, W_mean)
        Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
        libs = {
            "quantum": {1.0: Kq},
            "rival": {s: S5.k_mahalanobis(Z, W_r, gamma, s) for s in S5.S_GRID},
            "rbf": {e: S5.k_rbf_iso(Z, e) for e in S5.ELL2_GRID},
        }
        per_split = {k: [] for k in list(libs) + ["oracle"]}
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte, fte = y[tr], y[te], f[te]
            for name, Ks in libs.items():
                pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                          {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                per_split[name].append(S5.excess_risk(pred, yte, fte, var_f))
            pred, _, _ = S5.krr_tuned({1.0: Gall[np.ix_(tr, tr)]}, ytr, {1.0: Gall[np.ix_(te, tr)]})
            per_split["oracle"].append(S5.excess_risk(pred, yte, fte, var_f))
        d = np.array(per_split["quantum"]) - np.array(per_split["rival"])
        out[gamma] = dict(
            mean=float(d.mean()), ci=S5.paired_ci(d),
            p_flip=signflip_p(d), p_boot=boot_p(d), p_norm=normal_p(d),
            mean_rbf=float(np.mean(per_split["rbf"])), mean_oracle=float(np.mean(per_split["oracle"])),
            alive=float((Kq.sum() - n) / (n * (n - 1))), spread=spread, delta_mean_abs=float(abs(d.mean())),
        )
        out[gamma]["delta"] = d
    return dict(alpha=alpha, conv=conv, rows=out)


def null_cell_deltas(q, edges, Z, conv, metrics, seed_gen):
    """The A = 0 null: the target is pure noise, so the Bayes predictor is the zero function and every
    predictor's excess risk is measured in units of the noise variance.  A correction layer must find no
    structure here; these p-values are what the SIZE control is computed from."""
    rng = np.random.default_rng(seed_gen + 7)
    sigma = S5.NOISE_FRAC
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
    out = {}
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
        libs = {"quantum": {1.0: Kq},
                "rival": {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S5.S_GRID}}
        per_split = {k: [] for k in libs}
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte = y[tr], y[te]
            for name, Ks in libs.items():
                pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                          {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                per_split[name].append(float(np.mean((pred - yte) ** 2) / sigma ** 2))
        d = np.array(per_split["quantum"]) - np.array(per_split["rival"])
        out[gamma] = dict(mean=float(d.mean()), ci=S5.paired_ci(d),
                          p_flip=signflip_p(d), p_boot=boot_p(d), p_norm=normal_p(d), spread=spread,
                          delta_mean_abs=float(abs(d.mean())))
        out[gamma]["delta"] = d
    return dict(alpha=None, conv=conv, seed=seed_gen, rows=out)


def handicap_w(t, W_mean):
    """The registered planted-alignment control: withhold a DECLARED fraction of the geometry.

    W_t = (1 - t) * W_mean + t * diag(W_mean).  t = 0 is the fully matched rival; t = 1 leaves only the
    diagonal, so the rival inherits the map's per-qubit scale but none of the graph structure.  Symmetrised
    and spectrum-floored so the "Gaussian" cannot grow with distance (R391's defect 5, not repeated).
    """
    W = (1.0 - t) * W_mean + t * np.diag(np.diag(W_mean))
    W = 0.5 * (W + W.T)
    ev = np.linalg.eigvalsh(W)
    if ev.min() <= 0.0:
        W = W + (abs(ev.min()) + 1e-9) * np.eye(W.shape[0])
    return W


def matched_w(gamma, W_mean):
    return W_mean


def handicap_wf(t):
    return lambda gamma, W_mean: handicap_w(t, W_mean)


# ------------------------------------------------------------------ the report
def build_report():
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in GAMMAS} for c in CONVS}

    # ---- the declared family: the whole grid
    grid = {}
    for conv in CONVS:
        for alpha in ALIGNS:
            grid["%s|alpha=%g" % (conv, alpha)] = cell_deltas(
                q, edges, Z, alpha, conv, metrics[conv], S5.SEED_GEN, matched_w)

    family = []
    for key, cell in grid.items():
        for gamma, row in cell["rows"].items():
            family.append(dict(cell=key, gamma=gamma, delta_mean=row["mean"], ci=row["ci"],
                               p_flip=row["p_flip"], p_boot=row["p_boot"], p_norm=row["p_norm"],
                               alive=row["alive"], spread=row["spread"],
                               degenerate=bool(abs(row["mean"]) < 1e-15)))
    testable = [r for r in family if not r["degenerate"]]
    p_primary = np.array([r["p_flip"] for r in testable])
    bh05, k05 = bh_qvalues(p_primary, 0.05)
    bh10, k10 = bh_qvalues(p_primary, 0.10)
    by05, kby = by_qvalues(p_primary, 0.05)
    for i, r in enumerate(testable):
        r["q_bh"] = float(bh05[i])
        r["q_bh10"] = float(bh10[i])
        r["q_by"] = float(by05[i])
        r["route_gap"] = float(max(abs(r["p_flip"] - r["p_boot"]), abs(r["p_flip"] - r["p_norm"]),
                                   abs(r["p_boot"] - r["p_norm"])))
        r["marginal_lead"] = bool(r["ci"][1] < 0.0)

    # ---- SIZE: null cells across seeds
    nulls = [null_cell_deltas(q, edges, Z, "shifted", metrics["shifted"], 5000 + 37 * s)
             for s in range(N_NULL_SEEDS)]
    null_p = []
    null_false = {"bh05": 0, "bh10": 0, "by05": 0, "marginal": 0, "m_tests": 0}
    for nc in nulls:
        rows = [r for r in nc["rows"].values() if r["delta_mean_abs"] > 1e-15]
        ps = np.array([r["p_flip"] for r in rows])
        null_p.extend(ps.tolist())
        null_false["m_tests"] += len(rows)
        if len(ps) == 0:
            continue
        null_false["bh05"] += bh_qvalues(ps, 0.05)[1]
        null_false["bh10"] += bh_qvalues(ps, 0.10)[1]
        null_false["by05"] += by_qvalues(ps, 0.05)[1]
        null_false["marginal"] += int(np.sum([r["ci"][1] < 0.0 for r in rows]))
    ks_d, ks_p = ks_uniform(null_p)

    # ---- POWER: the planted-alignment (handicap) ladder
    ladder_family = []
    ladder_rows = {}
    for t in HANDICAP_LEVELS:
        if t == 0.0:
            continue                                  # t = 0 IS the matched rival, already in the family
        for alpha in ALIGNS:
            cell = cell_deltas(q, edges, Z, alpha, "shifted", metrics["shifted"], S5.SEED_GEN,
                               handicap_wf(t))
            for gamma, row in cell["rows"].items():
                if row["delta_mean_abs"] <= 1e-15:
                    continue
                ladder_family.append(dict(cell="t=%g|alpha=%g" % (t, alpha), gamma=gamma,
                                          delta_mean=row["mean"], ci=row["ci"], p_flip=row["p_flip"],
                                          alive=row["alive"]))
    lp = np.array([r["p_flip"] for r in ladder_family])
    lq, lk = bh_qvalues(lp, 0.05)
    for i, r in enumerate(ladder_family):
        r["q_bh"] = float(lq[i])
        r["marginal_lead"] = bool(r["ci"][1] < 0.0)
    for t in HANDICAP_LEVELS:
        sel = [r for r in ladder_family if r["cell"].startswith("t=%g|" % t)]
        ladder_rows["t=%g" % t] = dict(
            n_tests=len(sel), n_declared=int(sum(r["q_bh"] <= 0.05 for r in sel)),
            n_marginal=int(sum(r["marginal_lead"] for r in sel)),
            best_delta=float(min([r["delta_mean"] for r in sel] or [0.0])))

    # ---- the family's own correlation structure, reported rather than assumed
    corr_note = None
    if len(testable) > 2:
        M = np.stack([grid[r["cell"]]["rows"][r["gamma"]]["delta"] for r in testable])
        C = np.corrcoef(M)
        off = np.abs(C - np.eye(len(C)))
        corr_note = dict(mean_abs_offdiag=float(np.mean(off)), max_abs_offdiag=float(np.max(off)))

    return dict(
        round="R393",
        settings=dict(q=q, edges=EDGE_KIND, layers=LAYERS, convs=list(CONVS), aligns=list(ALIGNS),
                      gammas=list(GAMMAS), n_splits=N_SPLITS, n_flip=N_FLIP, n_boot=N_BOOT,
                      n_null_seeds=N_NULL_SEEDS, handicap_levels=list(HANDICAP_LEVELS),
                      q_levels=list(Q_LEVELS), numpy=np.__version__),
        controls=dict(
            C4_max_route_gap=float(max(r["route_gap"] for r in testable)),
            C4_route_gap_over_1em3=[[r["cell"], r["gamma"], r["route_gap"]] for r in testable
                                    if r["route_gap"] > 1e-3],
            C1_null_n_pvalues=len(null_p),
            C1_null_ks_stat=ks_d, C1_null_ks_p=ks_p,
            C1_null_false_declarations=null_false,
            C1_null_rate_bh05=float(null_false["bh05"] / max(1, null_false["m_tests"])),
            C1_null_rate_marginal=float(null_false["marginal"] / max(1, null_false["m_tests"])),
            C2_ladder=ladder_rows,
            C5_family_correlation=corr_note,
        ),
        family=family, testable_m=len(testable),
        fdr=dict(m=len(testable), n_declared_bh05=k05, n_declared_bh10=k10, n_declared_by05=kby,
                 n_marginal_leads=int(sum(r["marginal_lead"] for r in testable))),
        ladder_family=ladder_family,
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
    f = rep["fdr"]
    print("Issue #87 R393 -- FDR control across the declared grid, and the correction layer's validation")
    print("  q=%d %s  L=%d  splits=%d  flips=%d  numpy=%s"
          % (s["q"], s["edges"], s["layers"], s["n_splits"], s["n_flip"], s["numpy"]))
    print()
    print("  DECLARED FAMILY: the whole grid, %d rows (degenerate gamma=0 rows excluded by construction)"
          % len(rep["family"]))
    print("  TESTED: m = %d" % rep["testable_m"])
    print("  marginal leads (uncorrected 95%% CI excludes 0): %d   <-- the R391/R392 number"
          % f["n_marginal_leads"])
    print("  after Benjamini-Hochberg  q=0.05: %d declared   q=0.10: %d declared"
          % (f["n_declared_bh05"], f["n_declared_bh10"]))
    print("  after Benjamini-Yekutieli q=0.05: %d declared   (valid under ARBITRARY dependence)"
          % f["n_declared_by05"])
    cn = c["C5_family_correlation"]
    if cn:
        print("  family dependence, measured: mean |off-diag correlation| = %.3f, max = %.3f"
              % (cn["mean_abs_offdiag"], cn["max_abs_offdiag"]))
    print()
    print("  CONTROLS")
    print("   C4 max disagreement across the three p-value routes = %.2e" % c["C4_max_route_gap"])
    for row in c["C4_route_gap_over_1em3"]:
        print("        > 1e-3: %s gamma=%.2f gap=%.2e" % (row[0], row[1], row[2]))
    print("   C1 SIZE on the null (%d p-values from %d null cells, %d tests):"
          % (c["C1_null_n_pvalues"], s["n_null_seeds"], c["C1_null_false_declarations"]["m_tests"]))
    print("        uniformity of the null p-values: KS = %.4f (p = %.4f)   [~uniform is what we want]"
          % (c["C1_null_ks_stat"], c["C1_null_ks_p"]))
    print("        false declarations -- marginal CI: %d, BH q=0.05: %d, BH q=0.10: %d, BY q=0.05: %d"
          % (c["C1_null_false_declarations"]["marginal"], c["C1_null_false_declarations"]["bh05"],
             c["C1_null_false_declarations"]["bh10"], c["C1_null_false_declarations"]["by05"]))
    print("   C2 POWER on the planted handicap ladder (registered planted-alignment control):")
    for t in sorted(c["C2_ladder"], key=lambda k: float(k.split("=")[1])):
        v = c["C2_ladder"][t]
        print("        %-7s of %2d tests: %2d declared at q=0.05 (marginal: %2d), best delta %+.4f"
              % (t, v["n_tests"], v["n_declared"], v["n_marginal"], v["best_delta"]))
    print("   C6 report byte-identical on rebuild = %s" % c["C6_determinism_byte_identical"])
    print()
    print("  THE DECLARED LEADS (BH q <= 0.05), sorted by p:")
    rows = sorted([r for r in rep["family"] if r.get("q_bh", 1.0) <= 0.05], key=lambda r: r["p_flip"])
    if not rows:
        print("     none")
    for r in rows:
        print("     %-16s gamma=%4.2f  delta %+7.4f [%+7.4f,%+7.4f]  p=%.2e  q_BH=%.4f  q_BY=%.3f  alive=%.3f"
              % (r["cell"], r["gamma"], r["delta_mean"], r["ci"][0], r["ci"][1], r["p_flip"],
                 r["q_bh"], r["q_by"], r["alive"]))
    print()
    print("  MARGINAL-ONLY (uncorrected CI excluded 0 but BH does not declare it) -- these are the ones the")
    print("  uncorrected counts were counting:")
    for r in sorted([x for x in rep["family"] if x.get("marginal_lead") and x.get("q_bh", 1.0) > 0.05],
                    key=lambda r: r["p_flip"]):
        print("     %-16s gamma=%4.2f  delta %+7.4f [%+7.4f,%+7.4f]  p=%.3e  q_BH=%.4f"
              % (r["cell"], r["gamma"], r["delta_mean"], r["ci"][0], r["ci"][1], r["p_flip"], r["q_bh"]))
    print()
    print("  report sha256 = %s" % rep["report_sha256"])
    print("  written to %s" % os.path.basename(OUT))


if __name__ == "__main__":
    sys.exit(main())

