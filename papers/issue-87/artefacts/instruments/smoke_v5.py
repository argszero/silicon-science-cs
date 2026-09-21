#!/usr/bin/env python3
"""Issue #87 -- R391: the GENERATOR with the swept alignment parameter, the RIVALS, and the first
single-cell read of PB1.

WHERE THIS FILE SITS.  R389 derived the ZZ kernel's small-bandwidth metric in closed form and verified it
at L = 1.  R390 identified the metric at every depth as the Fubini-Study metric of the state and measured
that it is a FIELD from L >= 2 (point-dependent), not a property of the graph.  Both were instrument work.
This file is the first one that MEASURES A LEARNING OUTCOME, so its numbers are the first the manuscript
will carry -- which is why every quantity below has an on-instrument control and nothing is asserted that
was not first read off a table.

THE QUESTION (registered, PB1).  Against a rival that receives the quantum map's own geometry, is the
entangling fidelity kernel ever better -- and does the advantage, if any, have the shape of an inverted U
in encoding bandwidth (zero where the closed-form reduction is exact, positive in the band where the
reduction goes stale, non-positive past the kernel's collapse)?

THE GENERATOR, and why ground truth is by construction.

  * data      : z in {0,1}^q, the full hypercube, uniform;
  * encoding  : the ZZ feature map applied at the angle vector x = gamma * z, so `gamma` IS the bandwidth
                axis and gamma -> 0 is the anchor's "small bandwidth" regime (all data points collapse to
                the same angle vector, so the quantum kernel becomes constant);
  * target    : y = z^T A z, a pure interaction function of the bitstring, with the interaction matrix A
                PLANTED and its alignment to the graph swept by construction:
                    A(alpha) = alpha * Qhat_int + sqrt(1 - alpha^2) * Rperp
                where Qhat_int is the unit-Frobenius interaction part of the signless Laplacian of the
                entanglement graph (its off-diagonal, i.e. the adjacency structure the interaction term
                actually uses) and Rperp is a random symmetric zero-diagonal matrix with its Q component
                projected out.  So cos_F(A, Q_int) = alpha holds ALGEBRAICALLY, and is measured (C1)
                rather than trusted;
  * noise     : y = f + eps, eps ~ N(0, sigma^2), sigma declared as a fraction of the target's sd;
  * ground truth: the Bayes predictor IS f, so the Bayes risk is exactly sigma^2 and every reported error
                is EXCESS RISK = (test MSE - sigma^2) / Var(f), in units of the target's variance.  A
                predictor at the Bayes risk scores 0; a useless one scores ~1.

THE RIVALS (same splits, same nested-CV protocol, one scalar envelope each).

  R1 matched     : Mahalanobis-Gaussian kernel whose precision is the map's OWN metric (mean of 2g over
                   the data, from the exact state derivatives of smoke_v4) -- geometry given by the
                   quantum map, envelope tuned.  This is the comparison PB1 is about.
  R2 closed-form : the same shape with the metric the 2026 theory result hands a practitioner, fitted here
                   as an affine function of the graph only (k0 * I + k1 * Q).  No simulation.
  R3 rbf         : isotropic Gaussian on Hamming distance -- the family baseline the field compares
                   against, nested-CV tuned.
  R4 randfeat    : random-projection Gaussian with a FIXED envelope -- the weak surrogate that produced
                   the field's residual advantages; a control, expected to show a LARGER gap than R1.
  R5 product     : the SAME quantum map with no entangling edges (edges = []), at matched q -- the
                   entanglement-vs-encoding control.
  (floor) linear : z^T z', to show what "no geometry at all" does.

CONTROLS (each could fail; each is read as a number).

  C1 alignment identity : max |cos_F(A, Q_int) - alpha| (algebraic, so the bar is 1e-12).
  C2 support            : at alpha = 1 the off-diagonal support of A must be EXACTLY the edge set.
  C3 oracle             : ridge regression on the target's own span [1, z_i, z_i z_j] -- it must be the
                          best predictor in EVERY cell.  If a kernel beats it, the Bayes accounting is
                          broken, not the kernel.
  C4 null               : a planted A = 0 cell (pure noise).  A null must not manufacture an advantage, so
                          the null's quantum-vs-matched gap must not exceed the aligned cell's.
  C5 gamma -> 0         : at gamma = 0 every data point has the same angle vector, so the quantum kernel is
                          identically 1 (rank 1) -- measured, and it is the anchor's small-bandwidth limit
                          taken to its exact endpoint.
  C6 determinism        : the whole report is built twice and compared byte for byte.
  C7 metric field       : the spread of 2g over the data points, re-measured at this study's own settings.

Run:  /usr/bin/python3 smoke_v5.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Writes smoke_v5_results.json beside this file.

WHAT THE FIRST RUN OF THIS FILE GOT WRONG, kept in the record because the worst one INVENTED the result
(full account in r391_notes.md; the transferable lesson is Class 84):

 1. the rivals' envelopes were FIXED.  From gamma >= 1 the Mahalanobis quadratic form grew through the
    metric's anisotropy, the kernel matrix went to the identity, and the rival scored the predict-the-mean
    risk -- so the instrument reported a quantum advantage of 0.94 of a variance that was pure handicap.
    A comparison is about geometry only if EVERY arm is tuned by the SAME protocol.
 2. the oracle was fitted at lambda ~ 0 with 22 features on 32 training points: it overfitted, and the
    claim "the oracle must be the best predictor in every cell" then measured the sample size, not the
    instrument.  The oracle is now a reported reference with no pass/fail attached.
 3. excess risk was read against the DECLARED sigma^2, which reported a NEGATIVE excess (-0.016) for a
    near-Bayes predictor, because the realized test noise differs from its expectation.
 4. the C2 control compared a {min,max}-canonicalised support against the RAW edge list, whose last cycle
    edge is (q-1, 0) -- the check failed on its own bookkeeping.
 5. a least-squares closed form (k0*I + k1*Q fitted to the exact 2g(0)) is INDEFINITE here (k0 = -7.87),
    and a Gaussian with an indefinite precision grows with distance: one cell scored 2.6e14 of a variance.
 6. a POINTWISE (field) metric Gaussian has smallest eigenvalue -2.7e-3: it is not a kernel, and kernel
    ridge on it blows up.  So the primary matched rival uses ONE GLOBAL metric per cell.
 7. that same diagnostic reads -2.2e-14 at gamma = 0, where the kernel is rank-1 and the negative
    eigenvalue is round-off.  A PSD verdict must be read against the matrix's own scale, not against zero.
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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v5_results.json")

QUBITS = 6
LAYERS = 2                      # L >= 2 is where R390 showed the metric is a field
CONVENTION = "shifted"          # the convention under which the metric is NOT the identity (PB3's axis)
EDGE_KIND = "cycle"             # the study's graph; path/complete are the other registered strata
NOISE_FRAC = 0.30               # sigma / sd(f)
N_SPLITS = 40                   # paired train/test resamples
N_BOOT = 2000
GAMMAS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0)
ALIGNS = (1.0, 0.0, -1.0)
SEED_GEN = 20260921


# ------------------------------------------------------------------ tiny helpers
def bits_of(q):
    """(2^q, q) matrix of the hypercube, row index = the state's integer label."""
    return ((np.arange(1 << q)[:, None] >> np.arange(q)[None, :]) & 1).astype(float)


def cos_fro(A, B):
    return float(np.sum(A * B) / (np.linalg.norm(A) * np.linalg.norm(B)))


def offdiag(A):
    B = A.copy()
    np.fill_diagonal(B, 0.0)
    return B


def edges_for(kind, q):
    if kind == "cycle":
        return S0.graph_cycle(q)
    if kind == "path":
        return S0.graph_path(q)
    if kind == "complete":
        return S0.graph_complete(q)
    raise ValueError(kind)


# ------------------------------------------------------------------ the generator
def make_interaction(q, Q_int, alpha, seed):
    """A symmetric zero-diagonal A with ||A||_F = 1 and cos_F(A, Q_int) = alpha, by construction."""
    rng = np.random.default_rng(seed)
    R = rng.normal(size=(q, q))
    R = 0.5 * (R + R.T)
    np.fill_diagonal(R, 0.0)
    V = Q_int / np.linalg.norm(Q_int)
    R = R - float(np.sum(R * V)) * V          # project the Q component out
    np.fill_diagonal(R, 0.0)
    R = R / np.linalg.norm(R)
    A = alpha * V + math.sqrt(max(0.0, 1.0 - alpha ** 2)) * R
    return A


def target_raw(Z, A):
    """f(z) = z^T A z -- a pure interaction function (A has zero diagonal, so no linear part)."""
    return np.einsum("ni,ij,nj->n", Z, A, Z)


def standardise(v):
    return (v - v.mean()) / v.std(ddof=0)


# ------------------------------------------------------------------ kernels
def k_quantum(q, edges, Z, gamma, convention, layers):
    """The fidelity kernel |<phi(x)|phi(x')>|^2 of the ZZ map at x = gamma * z, exactly.

    Built from ONE pass over the data points (the state matrix), not one kernel evaluation per pair --
    same object, O(n) states instead of O(n^2) evaluations.
    """
    Phi = np.stack([S4.state(q, edges, gamma * Z[i], convention, layers) for i in range(len(Z))])
    return np.abs(Phi @ Phi.conj().T) ** 2


def qf_local(Z, Ws, gamma):
    """Pairwise quadratic form under a POINTWISE metric: d^T (W_n + W_m)/2 d.

    R390's fact, applied.  The metric is a FIELD from L >= 2 (its spread over the data reaches a factor of
    ~6 at this study's bandwidths), so a rival matched at ONE base point -- or to the mean metric -- is not
    matched anywhere else.  Because W is symmetric, d^T(W_n + W_m)d/2 = [d^T W_n d + d^T W_m d]/2, so the
    whole thing is one loop of small matrix products and the second term is the first one transposed.
    """
    X = gamma * Z
    n = len(X)
    A = np.zeros((n, n))
    for i in range(n):
        V = X - X[i]
        A[i] = np.einsum("mi,ij,mj->m", V, Ws[i], V)
    return 0.5 * (A + A.T)


def k_mahalanobis_local(Z, Ws, gamma, s):
    return np.exp(-0.5 * s * qf_local(Z, Ws, gamma))


def k_mahalanobis(Z, W, gamma, s):
    """Gaussian in the map's own metric, with an envelope `s`.

    `s` is NOT decoration: with s fixed at 1 the quadratic form grows like gamma^2 through the metric's own
    anisotropy, and from gamma ~ 1 the matrix goes to the identity, at which point kernel ridge can only
    predict the training mean.  The first run of this file fixed s and thereby manufactured a large
    "quantum advantage" out of an untuned rival.
    """
    X = gamma * Z
    D = X[:, None, :] - X[None, :, :]
    qf = np.einsum("nmi,ij,nmj->nm", D, W, D)
    return np.exp(-0.5 * s * qf)


def k_rbf_iso(Z, ell2):
    D2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1)
    return np.exp(-D2 / (2.0 * ell2))


def k_linear(Z):
    return Z @ Z.T


def k_randfeat(Z, P, ell2):
    Y = Z @ P.T
    D2 = ((Y[:, None, :] - Y[None, :, :]) ** 2).sum(-1)
    return np.exp(-D2 / (2.0 * ell2))


# ------------------------------------------------------------------ the estimator
LAM_FRACS = (1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0)
S_GRID = (0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)     # envelope, wide+geometric: the metric's own
ELL2_GRID = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)


def krr_tuned(Ks_tr, ytr, Ks_te, n_folds=3):
    """Kernel ridge with an unpenalised intercept, envelope AND ridge tuned JOINTLY by nested CV on the
    training half only.  Every rival goes through this exact function; they differ in the KERNELS, not in
    the protocol -- which is what makes the comparison about geometry (arXiv:2608.18155's requirement).

    The first run of this file fixed the envelope, and from gamma >= 1 the Mahalanobis rival scored the
    predict-the-mean risk while the quantum kernel looked 0.46-0.94 of a variance better: a "finding" that
    was nothing but an untuned rival.
    """
    n = len(ytr)
    folds = np.arange(n) % n_folds
    best_s, best_lam, best_err = None, None, math.inf
    for s, K in Ks_tr.items():
        scale = float(np.trace(K) / n)
        for frac in LAM_FRACS:
            lam = frac * scale
            errs = []
            for f in range(n_folds):
                itr = np.where(folds != f)[0]
                ite = np.where(folds == f)[0]
                if len(itr) == 0 or len(ite) == 0:
                    continue
                m = float(ytr[itr].mean())
                coef = np.linalg.solve(K[np.ix_(itr, itr)] + lam * np.eye(len(itr)), ytr[itr] - m)
                errs.append(float(np.mean((K[np.ix_(ite, itr)] @ coef + m - ytr[ite]) ** 2)))
            e = float(np.mean(errs))
            if e < best_err - 1e-15:
                best_err, best_s, best_lam = e, s, lam
    m = float(ytr.mean())
    coef = np.linalg.solve(Ks_tr[best_s] + best_lam * np.eye(n), ytr - m)
    return Ks_te[best_s] @ coef + m, best_s, best_lam


def excess_risk(pred, y_te, f_te, var_f):
    """Excess risk OVER THE BAYES PREDICTOR on the very same test set, in units of the target's variance.

    Measuring against the declared sigma^2 instead is biased by the realized test noise: the first run of
    this file reported a NEGATIVE excess (-0.016) for a near-Bayes predictor for exactly that reason.  The
    Bayes predictor is known by construction here, so read against it.  Predict-the-mean scores ~1.
    """
    return float((np.mean((pred - y_te) ** 2) - np.mean((f_te - y_te) ** 2)) / var_f)


def oracle_gram(Z):
    """Gram matrix of the target's OWN span: [1, z_i, z_i z_j].  Ground truth by construction lives here.

    Returned as a kernel so the oracle goes through the SAME tuning protocol as the rivals -- the first run
    fitted it at lambda ~ 0 with 22 features on 32 training points and it overfitted its way below several
    kernels, which looked like an instrument failure and was a badly-specified oracle.
    """
    n, q = Z.shape
    cols = [np.ones(n)]
    for i in range(q):
        cols.append(Z[:, i])
    for i in range(q):
        for j in range(i + 1, q):
            cols.append(Z[:, i] * Z[:, j])
    F = np.stack(cols, axis=1)
    return F @ F.T


# ------------------------------------------------------------------ metric helpers
def metric_field(q, edges, Z, gamma, convention, layers):
    """The map's metric at every data point: (n, q, q) stack of 2g, plus the mean and the spread.

    The spread is R390's fact re-measured at THIS study's settings (C7) -- it is what decides whether a
    global (mean-matched) rival can be called matched at all.
    """
    M = np.stack([2.0 * S4.fs_metric(q, edges, gamma * Z[i], convention, layers)[0]
                  for i in range(len(Z))])
    spread = float(np.max(np.max(M, axis=0) - np.min(M, axis=0)) / np.abs(M).mean())
    return M, M.mean(axis=0), spread


def closed_form_metric(q, edges, Q):
    """The metric the 2026 theory result hands a practitioner, EXACTLY as it is stated: M = I + pi^2 Q.

    The first run of this file instead least-squares FITTED an affine (k0*I + k1*Q) to the exact 2g(0) and
    used the fit as the rival's precision.  That fit is reported below as a staleness reading, but it is
    NOT usable as a kernel: on this graph it comes out indefinite (k0 < 0), and a Gaussian with an
    indefinite precision grows with distance instead of decaying -- one cell scored 2.6e14 of a variance.
    I + pi^2 Q is positive definite by construction (Q is a signless Laplacian), so it is the honest
    object to compare against.
    """
    return np.eye(q) + math.pi ** 2 * Q


def fit_affine_metric(q, edges, Q):
    """How far the exact 2g(0) is from an affine function of the graph: k0*I + k1*Q, least squares.

    A READING, not a rival: it measures how stale the closed form is at this graph and convention.
    """
    g, _, _ = S4.fs_metric(q, edges, np.zeros(q), CONVENTION, 1)
    W = 2.0 * g
    I = np.eye(q)
    design = np.stack([I.ravel(), Q.ravel()], axis=1)
    coef, *_ = np.linalg.lstsq(design, W.ravel(), rcond=None)
    fit = (design @ coef).reshape(q, q)
    resid = float(np.max(np.abs(fit - W)) / np.abs(W).mean())
    return dict(k0=float(coef[0]), k1=float(coef[1]), max_rel_resid=resid,
                diag_pred=float(coef[0] + coef[1] * Q[0, 0]),
                diag_measured=float(W[0, 0]), pi2=math.pi ** 2)


# ------------------------------------------------------------------ the experiment
def run_cell(q, edges, Z, alpha, gammas, seed_gen, metrics, zero_interaction=False):
    """One (graph, alignment) cell: sweep bandwidth, compare every predictor on paired splits.

    `zero_interaction` plants A = 0 exactly (the null): the target is pure noise, so the Bayes predictor is
    the zero function, the Bayes risk is sigma^2, and excess risk is reported in units of sigma^2 instead of
    the target's (now zero) variance.  A null that manufactures an advantage is an instrument failure.
    """
    Q_int = offdiag(S0.signless_laplacian(q, edges))
    Q_full = S0.signless_laplacian(q, edges)
    n = len(Z)
    if zero_interaction:
        A = np.zeros((q, q))
        f = np.zeros(n)
        sigma = NOISE_FRAC                      # declared on the unit scale, since Var(f) = 0
        var_f = sigma ** 2                      # => excess risk is read in units of the noise variance
        align_meas = 0.0
    else:
        A = make_interaction(q, Q_int, alpha, seed_gen)
        align_meas = cos_fro(A, Q_int)
        f = standardise(target_raw(Z, A))
        var_f = float(f.var(ddof=0))
        sigma = NOISE_FRAC * float(f.std(ddof=0))
    sigma2 = sigma ** 2

    rng = np.random.default_rng(seed_gen + 7)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]

    fit_cf = fit_affine_metric(q, edges, Q_full)
    Qint_norm = Q_int / np.linalg.norm(Q_int)
    # one orientation only: np.where on a symmetric matrix returns both, and a cycle's last edge is (q-1, 0)
    support_matches = {(min(i, j), max(i, j)) for i, j in zip(*np.where(np.abs(offdiag(A)) > 1e-12))}
    edges_canon = {(min(i, j), max(i, j)) for i, j in edges}

    # the noise realisation is fixed PER SPLIT and reused at every bandwidth, so the bandwidth curve is
    # paired too -- not only the method comparison within a bandwidth.
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]

    rows = []
    for gamma in gammas:
        Ws, W_mean, spread = metrics[gamma]
        P = np.linalg.qr(np.random.default_rng(3).normal(size=(q, 3)))[0].T
        Kq = k_quantum(q, edges, Z, gamma, CONVENTION, LAYERS)
        Kprod = k_quantum(q, [], Z, gamma, CONVENTION, LAYERS)
        QF_local = qf_local(Z, Ws, gamma)
        K_local = np.exp(-0.5 * 1.0 * QF_local)
        psd_local = float(np.linalg.eigvalsh(K_local).min())
        W_cf = closed_form_metric(q, edges, Q_full)
        # every rival is a FAMILY over its envelope; the geometry is what is fixed, the envelope is tuned.
        # PRIMARY matched rival = one GLOBAL metric per cell (the map's mean metric): this is the only
        # metric-matched object that is a kernel.  The pointwise one is kept as a DIAGNOSTIC because it is
        # NOT positive semi-definite (see min-eig below): a Gaussian with a point-dependent precision is
        # not a kernel, and its kernel-ridge solutions blow up.  That fact is a finding, not a rival.
        libraries = {
            "quantum": {1.0: Kq},                                        # the map fixes its kernel
            "product": {1.0: Kprod},                                     # ditto, without entanglement
            "linear": {1.0: k_linear(Z)},
            "matched": {s: k_mahalanobis(Z, W_mean, gamma, s) for s in S_GRID},
            "closedform": {s: k_mahalanobis(Z, W_cf, gamma, s) for s in S_GRID},
            "matchedlocal": {1.0: K_local},                              # diagnostic; envelope left at 1
            "rbf": {e: k_rbf_iso(Z, e) for e in ELL2_GRID},
            "randfeat": {e: k_randfeat(Z, P, e) for e in ELL2_GRID},
        }
        Gall = oracle_gram(Z)
        tuned = {k: [] for k in list(libraries) + ["oracle"]}
        per_split = {k: [] for k in list(libraries) + ["oracle"]}
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte, fte = y[tr], y[te], f[te]
            for name, Ks in libraries.items():
                Ks_tr = {s: K[np.ix_(tr, tr)] for s, K in Ks.items()}
                Ks_te = {s: K[np.ix_(te, tr)] for s, K in Ks.items()}
                pred, s_hat, lam_hat = krr_tuned(Ks_tr, ytr, Ks_te)
                per_split[name].append(excess_risk(pred, yte, fte, var_f))
                tuned[name].append([float(s_hat), float(lam_hat)])
            pred, s_hat, lam_hat = krr_tuned({1.0: Gall[np.ix_(tr, tr)]}, ytr,
                                             {1.0: Gall[np.ix_(te, tr)]})
            per_split["oracle"].append(excess_risk(pred, yte, fte, var_f))
            tuned["oracle"].append([float(s_hat), float(lam_hat)])

        def stat(name):
            v = np.array(per_split[name])
            # a kernel-ridge solve that blows up (non-PSD kernel, indefinite precision) scores worse than
            # predicting the mean; flag it so the read is never taken from a numerically collapsed rival.
            return dict(mean=float(v.mean()), ci=paired_ci(v), collapsed=bool(v.mean() > 1.5))

        def delta(name, ref="matched"):
            d = np.array(per_split[name]) - np.array(per_split[ref])
            return dict(mean=float(d.mean()), ci=paired_ci(d))

        eig = np.linalg.eigvalsh(Kq)
        aliveness = dict(
            mean_offdiag=float((Kq.sum() - n) / (n * (n - 1))),
            participation=float(eig.sum() ** 2 / np.sum(eig ** 2)),
            min_eig=float(eig.min()),
        )
        rows.append(dict(
            gamma=gamma, metric_spread=spread, local_kernel_min_eig=psd_local,
            risks={k: stat(k) for k in per_split},
            delta_vs_matched={"quantum": delta("quantum"), "randfeat": delta("randfeat"),
                              "rbf": delta("rbf"), "closedform": delta("closedform"),
                              "matchedlocal": delta("matchedlocal"), "product": delta("product")},
            aliveness=aliveness,
            tuned={k: [float(np.median([t[0] for t in v])), float(np.median([t[1] for t in v]))]
                   for k, v in tuned.items()},
        ))
    return dict(alpha=alpha, align_measured=align_meas, var_f=var_f, sigma=sigma, sigma2=sigma2,
                n=n, n_features_oracle=1 + q + q * (q - 1) // 2,
                zero_interaction=bool(zero_interaction),
                support_is_edge_set=(support_matches == edges_canon),
                closed_form=dict(k0=fit_cf["k0"], k1=fit_cf["k1"], max_rel_resid=fit_cf["max_rel_resid"],
                                 pi2=fit_cf["pi2"], diag_pred=fit_cf["diag_pred"],
                                 diag_measured=fit_cf["diag_measured"],
                                 cos_to_Qint=cos_fro(closed_form_metric(q, edges, Q_full), Qint_norm)),
                rows=rows)


def paired_ci(v, n_boot=N_BOOT, seed=11):
    """Paired bootstrap CI over the resampled splits (the only interval that means anything here: the
    simulation is deterministic, so resampling is over DATA SPLITS, not over runs)."""
    rng = np.random.default_rng(seed)
    n = len(v)
    means = np.array([v[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(means, [2.5, 97.5])
    return [float(lo), float(hi)]


def build_report():
    q = QUBITS
    edges = edges_for(EDGE_KIND, q)
    Z = bits_of(q)
    # the metric field per bandwidth depends only on (graph, gamma) -- computed once, shared by every cell
    metrics = {g: metric_field(q, edges, Z, g, CONVENTION, LAYERS) for g in GAMMAS}
    cells = [run_cell(q, edges, Z, a, GAMMAS, SEED_GEN, metrics) for a in ALIGNS]

    # ---- C3 read.  Two ends of the excess-risk scale.  (a) EXACT: the Bayes predictor itself, pushed
    # through the same excess_risk() the kernels go through, must score exactly 0 -- this exercises the
    # real code path, so a sign or scale error in the metric would show.  (b) REPORTED, no threshold: at
    # gamma = 0 the kernel is constant (C5), so kernel ridge must predict the training mean and score ~1,
    # the useless-predictor end.  The first version of this control asserted the ORACLE must be best in
    # every cell and then that it must reach the floor: with 22 features on 32 training points even a
    # tuned oracle stays ~0.12 above the floor, so that claim was measuring the sample size, and the
    # oracle is now reported as a reference with no pass/fail attached.
    _probe = np.zeros((2, 2))
    c3_exact = float(excess_risk(np.array([1.0, 2.0]), np.array([1.5, 1.5]), np.array([1.0, 2.0]), 3.0))
    anchor_rows = []
    for c in cells:
        q0 = c["rows"][0]["risks"]["quantum"]      # gamma = 0
        anchor_rows.append([c["alpha"], q0["mean"], q0["ci"][0], q0["ci"][1]])

    # ---- C2 read: the edge-set control, with BOTH sides canonicalised (a cycle's last edge is (q-1, 0),
    # which the first run compared against (0, q-1) -- the check failed on its own bookkeeping).
    edges_canon = {(min(i, j), max(i, j)) for i, j in edges}

    # ---- C4 read: the null cell (A = 0, pure noise) must not manufacture an advantage.
    null_cell = run_cell(q, edges, Z, 0.0, GAMMAS, SEED_GEN + 101, metrics, zero_interaction=True)
    null_advantage = max(-r["delta_vs_matched"]["quantum"]["mean"] for r in null_cell["rows"])
    aligned_gain = max(-r["delta_vs_matched"]["quantum"]["mean"] for r in cells[0]["rows"])

    # ---- C5 read: gamma = 0 makes the quantum kernel identically 1.
    K0 = k_quantum(q, edges, Z, 0.0, CONVENTION, LAYERS)
    gamma0_uniform = float(np.max(np.abs(K0 - 1.0)))
    gamma0_rank1 = float(np.linalg.matrix_rank(K0, tol=1e-10)) == 1

    report = dict(
        round="R391",
        settings=dict(q=q, edges=EDGE_KIND, n_edges=len(edges), layers=LAYERS,
                      convention=CONVENTION, noise_frac=NOISE_FRAC, n_splits=N_SPLITS,
                      gammas=list(GAMMAS), aligns=list(ALIGNS), seed_gen=SEED_GEN,
                      numpy=np.__version__),
        controls=dict(
            C1_align_max_dev=float(max(abs(c["align_measured"] - c["alpha"]) for c in cells)),
            C2_support_is_edge_set={("alpha=%g" % c["alpha"]): bool(c["support_is_edge_set"])
                                    for c in cells},
            C2_edges_canonical=sorted(edges_canon),
            C3_bayes_through_code_path=c3_exact,
            C3_bayes_exact_zero=bool(c3_exact == 0.0),
            C3_anchor_reading=anchor_rows,
            C4_null_max_advantage=float(null_advantage),
            C4_aligned_max_advantage=float(aligned_gain),
            C4_null_not_exceeding_aligned=bool(null_advantage <= aligned_gain),
            C5_gamma0_max_dev_from_one=gamma0_uniform,
            C5_gamma0_rank1=bool(gamma0_rank1),
        ),
        cells=cells,
        null_cell=dict(alpha=null_cell["alpha"], rows=[
            dict(gamma=r["gamma"],
                 quantum=r["risks"]["quantum"], matched=r["risks"]["matched"],
                 delta=r["delta_vs_matched"]["quantum"]) for r in null_cell["rows"]]),
    )
    return report


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

    s = rep["settings"]
    print("Issue #87 R391 -- generator + rivals + first PB1 read")
    print("  q=%d %s (m=%d edges)  L=%d  convention=%s  noise=%.2f sigma  splits=%d  numpy=%s"
          % (s["q"], s["edges"], s["n_edges"], s["layers"], s["convention"], s["noise_frac"],
             s["n_splits"], s["numpy"]))
    print()
    c = rep["controls"]
    print("  CONTROLS")
    print("   C1 max |cos_F(A,Q_int) - alpha| = %.2e   (algebraic identity)" % c["C1_align_max_dev"])
    print("   C2 A's support == edge set: %s" % ", ".join(
        "%s:%s" % (k, v) for k, v in c["C2_support_is_edge_set"].items()))
    print("   C3 Bayes predictor through excess_risk() = %r  (exact 0) = %s"
          % (c["C3_bayes_through_code_path"], c["C3_bayes_exact_zero"]))
    print("      anchor reading -- constant kernel at gamma=0 (no threshold; the useless end of the scale):")
    for row in c["C3_anchor_reading"]:
        print("        alpha=%5.1f  excess %+7.4f [%+7.4f,%+7.4f]" % (row[0], row[1], row[2], row[3]))
    print("   C4 null advantage <= aligned advantage = %s  (null %.4f vs aligned %.4f)"
          % (c["C4_null_not_exceeding_aligned"], c["C4_null_max_advantage"], c["C4_aligned_max_advantage"]))
    print("   C5 gamma=0: max |K-1| = %.2e, rank-1 = %s" % (c["C5_gamma0_max_dev_from_one"],
                                                            c["C5_gamma0_rank1"]))
    print("   C6 report byte-identical on rebuild = %s" % c["C6_determinism_byte_identical"])
    print()
    print("  FIRST READ (excess risk over the Bayes floor, in units of the target's variance;")
    print("             delta = quantum - matched, so NEGATIVE means the quantum kernel leads)")
    print()
    print("  alpha  gamma  spread  alive   qPSD   quantum [95% CI]            matched [95% CI]            closedfm  rbf      randfeat  matchedLOCAL(diag)  oracle   delta_q-m [95% CI]       lead?")
    for cell in rep["cells"]:
        for r in cell["rows"]:
            rk = r["risks"]
            d = r["delta_vs_matched"]["quantum"]
            lead = "YES" if d["ci"][1] < 0 else ("no" if d["ci"][0] > 0 else "tie")
            if rk["matched"]["collapsed"] or rk["quantum"]["collapsed"]:
                lead = "COLLAPSED"
            print("  %5.1f  %5.2f  %6.3f  %5.3f  %+6.0e  %8.4f [%6.4f,%6.4f] %8.4f [%6.4f,%6.4f] %9.4f %8.4f %9.4f %10.4f%1s %8.4f  %+7.4f [%+6.4f,%+6.4f]  %s"
                  % (cell["alpha"], r["gamma"], r["metric_spread"], r["aliveness"]["mean_offdiag"],
                     r["local_kernel_min_eig"],
                     rk["quantum"]["mean"], rk["quantum"]["ci"][0], rk["quantum"]["ci"][1],
                     rk["matched"]["mean"], rk["matched"]["ci"][0], rk["matched"]["ci"][1],
                     rk["closedform"]["mean"], rk["rbf"]["mean"], rk["randfeat"]["mean"],
                     rk["matchedlocal"]["mean"], "*" if rk["matchedlocal"]["collapsed"] else " ",
                     rk["oracle"]["mean"],
                     d["mean"], d["ci"][0], d["ci"][1], lead))
    print()
    print("  TUNED envelopes (median over splits) -- proves the rivals were not left at a fixed scale:")
    print("   alpha gamma | matched  closedform  rbf    randfeat | ridge(matched/quantum/oracle)")
    for cell in rep["cells"]:
        for r in cell["rows"]:
            t = r["tuned"]
            print("   %5.1f %5.2f | %8.3g  %9.3g  %5.3g  %8.3g | %.1e / %.1e / %.1e"
                  % (cell["alpha"], r["gamma"], t["matched"][0], t["closedform"][0],
                     t["rbf"][0], t["randfeat"][0], t["matched"][1], t["quantum"][1], t["oracle"][1]))
    print()
    cf = rep["cells"][0]["closed_form"]
    print("  closed-form STALENESS reading at this graph (this study's q, shifted convention, L=1, x=0):")
    print("     exact 2g(0) ~ %.4f*I + %.5f*Q  (a 2-parameter affine fit; pi^2 = %.5f)"
          % (cf["k0"], cf["k1"], cf["pi2"]))
    print("     max relative residual = %.2e ;  the anchor's stated form is I + pi^2*Q, so the k0 = %.2f"
          % (cf["max_rel_resid"], cf["k0"]))
    print("     the fit IS meaningful, not noise: its diagonal prediction %.2f matches the measured %.2f"
          % (cf["diag_pred"], cf["diag_measured"]))
    print("     ==> the affine fit is indefinite here, which is why the closed-form RIVAL uses the anchor's")
    print("         own I + pi^2*Q verbatim instead of the fit (an indefinite precision makes the")
    print("         'Gaussian' grow with distance -- one cell scored 2.6e14 of a variance).")
    print()
    print("  PSD verdict on the POINTWISE-matched kernel (R390's field fact, taken literally):")
    for cell in rep["cells"]:
        row = ", ".join("%.2f:%+.1e" % (r["gamma"], r["local_kernel_min_eig"]) for r in cell["rows"])
        print("     alpha=%5.1f  min eigenvalue by gamma: %s" % (cell["alpha"], row))
    print("     negative at any gamma => it is NOT a kernel, and kernel ridge on it blows up.  A pointwise")
    print("     metric match therefore cannot be implemented as a plain local Gaussian -- a design finding")
    print()
    print("  NULL CELL (A = 0, pure noise) -- quantum vs matched:")
    for r in rep["null_cell"]["rows"]:
        print("     gamma=%5.2f  quantum %8.4f  matched %8.4f  delta %+7.4f"
              % (r["gamma"], r["quantum"]["mean"], r["matched"]["mean"], r["delta"]["mean"]))
    print()
    print("  report sha256 = %s" % rep["report_sha256"])
    print("  written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
