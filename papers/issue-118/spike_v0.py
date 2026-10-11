"""spike_v0 -- theory arm of issue #118: the capacity/overflow law.

Ground truth is by construction:
  * the EXACT route sums marginal binomial tails (N_e ~ Bin(T, p_e) for top-1 routing, and the
    expectation of a sum is the sum of expectations, so the marginals suffice);
  * the INDEPENDENT route samples the full multinomial and counts overflow per expert.
The two must agree; a disagreement is a defect in one of them.

Run: /usr/bin/python3 spike_v0.py
"""
import math, json, sys
from math import lgamma, log, exp, sqrt
import numpy as np

TOL = 1e-6          # a C_min reading is a claim AT this tolerance; it is printed with every value
SEED = 20261002

def bin_pmf(n, p, i):
    if p <= 0: return 1.0 if i == 0 else 0.0
    if p >= 1: return 1.0 if i == n else 0.0
    return exp(lgamma(n+1)-lgamma(i+1)-lgamma(n-i+1)+i*log(p)+(n-i)*log(1-p))

def bin_drop(n, p, c):
    """E[(N-c)+] for N~Bin(n,p) -- exact, by summing the tail."""
    m = int(math.floor(c))
    if m >= n: return 0.0
    if m < 0: m = -1
    s = 0.0
    for i in range(m+1, n+1):
        s += (i-c)*bin_pmf(n, p, i)
    return s

def exact_drop_rate(E, T, p, C, topk=1):
    """Expected dropped tokens per token, top-1 routing.  c = C * (topk*T/E)."""
    c = C * (topk*T/E)
    tot = 0.0
    for e in range(E):
        tot += bin_drop(T, p[e], c)
    return tot/T

def mc_drop_rate(E, T, p, C, M=2000, seed=SEED, topk=1):
    """Independent route: sample the multinomial, count overflow."""
    rng = np.random.default_rng(seed)
    c = C * (topk*T/E)
    drops = np.empty(M)
    for m in range(M):
        counts = rng.multinomial(T, p)
        drops[m] = float(np.maximum(counts-c, 0).sum())
    d = drops/T
    return float(d.mean()), float(d.std(ddof=1)/sqrt(M))

def c_min(E, T, p, tol=TOL, topk=1):
    """Smallest C with expected drop rate < tol (exact route).  A reading AT tolerance tol."""
    lo, hi = 1.0, 100.0
    if exact_drop_rate(E,T,p,hi,topk) >= tol: return float('inf')
    for _ in range(80):
        mid = 0.5*(lo+hi)
        if exact_drop_rate(E,T,p,mid,topk) < tol: hi = mid
        else: lo = mid
    return hi

def predict_c_min(E, T, p, topk=1):
    """The registered decomposition: imbalance term + finite-sample max-load term."""
    mu = np.array([topk*T*p[e] for e in range(E)])
    imb = float(mu.max()*(E/(topk*T)))                       # c must reach the hottest expert's mean
    z = sqrt(2*log(E)) if E > 1 else 0.0                     # max of E counts ~ sqrt(2 ln E) sigma
    c_pred = mu.max() + z*sqrt(max(mu.max(),1e-12))          # mean + fluctuation of the max
    noise = float((c_pred - mu.max())*(E/(topk*T)))
    return imb + noise, imb, noise

def dirichlet_p(E, alpha, rng):
    if alpha is None: return np.full(E, 1.0/E)
    w = rng.dirichlet(np.full(E, alpha))
    return w

def main():
    rng = np.random.default_rng(SEED)
    out = {"tol": TOL, "seed": SEED, "cells": []}
    print("=" * 96)
    print("METRIC (i)+(ii): exact vs Monte-Carlo, and the C_min decomposition     tol=%.0e" % TOL)
    print(f"{'E':>5}{'T':>7}{'mu':>7}{'C=1.25 exact':>14}{'C=1.25 MC+-sd':>20}{'C_min meas':>12}{'C_min pred':>12}{'imb':>8}{'noise':>8}")
    for E, T in [(8,512),(16,512),(32,512),(32,1024),(64,1024),(64,2048),(128,1024),(128,4096),(256,2048),(256,4096),(64,8192),(128,8192)]:
        p = np.full(E, 1.0/E)
        ex = exact_drop_rate(E,T,p,1.25)
        m, s = mc_drop_rate(E,T,p,1.25,M=1500)
        cm = c_min(E,T,p); pred,imb,noise = predict_c_min(E,T,p)
        mu = T/E
        print(f"{E:>5}{T:>7}{mu:>7.1f}{ex:>14.6f}{m:>13.6f}+-{s:<6.6f}{cm:>12.4f}{pred:>12.4f}{imb:>8.3f}{noise:>8.3f}")
        out["cells"].append(dict(E=E,T=T,mu=mu,exact_1_25=ex,mc_1_25=m,mc_sd=s,c_min_meas=cm,c_min_pred=pred,imb=imb,noise=noise))
    print()
    print("METRIC (iv) BALANCING-CEILING: uniform router, is C_min > 1.25?  (mu <= 16)")
    bad = 0
    for c in out["cells"]:
        if c["mu"] <= 16:
            verdict = "ABOVE 1.25 -> drops at the folk constant" if c["c_min_meas"] > 1.25 else "at/below 1.25"
            if c["c_min_meas"] > 1.25: bad += 1
            print(f"   E={c['E']:>4} mu={c['mu']:>5.1f}  C_min={c['c_min_meas']:.3f}  {verdict}")
    print(f"   -> {bad} of the mu<=16 cells need C > 1.25 EVEN WITH A PERFECTLY UNIFORM ROUTER")
    out["ceiling_cells_above_1_25"] = bad
    print()
    print("SKEW ARM: how much of C_min is population imbalance?  (E=64, T=2048 -> mu=32)")
    E, T = 64, 2048
    for alpha in [None, 1.0, 0.2, 0.05]:
        p = dirichlet_p(E, alpha, rng)
        cm = c_min(E,T,p); pred,imb,noise = predict_c_min(E,T,p)
        print(f"   alpha={str(alpha):>5}  max_p/(1/E)={E*p.max():>6.2f}  C_min_meas={cm:>6.3f}  pred={pred:>6.3f} (imb {imb:.3f} + noise {noise:.3f})")
        out.setdefault("skew", []).append(dict(alpha=alpha, max_over_mean=float(E*p.max()), c_min=cm, pred=pred, imb=imb, noise=noise))
    with open("spike_v0_results.json","w") as f: json.dump(out,f,indent=1)
    print("\nwrote spike_v0_results.json")

if __name__ == "__main__":
    main()
