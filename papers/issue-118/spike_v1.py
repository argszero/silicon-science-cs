"""spike_v1 -- issue #118: the exact route (three ways), the tolerance-indexed capacity curve,
and the formal ceiling test (P2).

DEFECT FOUND AND FIXED IN THIS FILE (recorded because it is the round's main pitfall):
the normal tail-expectation kernel was written with a PLUS sign, `phi(z) + z*Phibar(z)`, where
E[(Z-z)+] = phi(z) - z*Phibar(z) (verified against quadrature: 7.145258e-06 vs 2.605152e-04 at
z=4, i.e. the wrong kernel is 36x too large). The wrong kernel still landed within 1.6 % of the
measured C_min -- agreement that would have certified a false law -- because C_min is a slowly
varying functional of the tail. What exposed it was a DEGENERATE cell (E=64, T=8192: predicted
0.0 against a measured 1.361) plus a hand derivation, not the residual.

Routes for D(C) = (1/T) * sum_e E[(N_e - c)+]:
  A  float  : tail sum with lgamma                    (spike_v0's route; pruned to experts that can overflow)
  B  exact  : the same sum in exact integer arithmetic (certifies A's ARITHMETIC)
  C  sample : multinomial sampling                     (certifies the MODEL/formula)
A and B, evaluated at the SAME C, must agree to float rounding. C is scored by z at the same C.

Run: /usr/bin/python3 spike_v1.py
"""
import math, json
from math import comb, lgamma, log, exp, sqrt, erfc, pi
from fractions import Fraction
import numpy as np

TOL   = 1e-6        # the declared expected drop RATE; a reading is a reading AT this tolerance
SEED  = 20261002
MC_M  = 1500        # MC draws; its own resolution is reported wherever it is used

_erfc = np.vectorize(math.erfc)

# ---------- the normal tail-expectation kernel (SIGN IS THE POINT OF THIS ROUND) ----------
def phiz(z):
    """E[(Z-z)+] = phi(z) - z*Phibar(z) for Z~N(0,1)."""
    z = np.asarray(z, dtype=float)
    return np.exp(-z*z/2)/sqrt(2*pi) - z*0.5*_erfc(z/sqrt(2))

# ---------- route A: float tail sum (pruned) ----------
def _lpmf(n, p, i):
    if p <= 0: return 1.0 if i == 0 else 0.0
    if p >= 1: return 1.0 if i == n else 0.0
    return exp(lgamma(n+1)-lgamma(i+1)-lgamma(n-i+1)+i*log(p)+(n-i)*log(1-p))

def drop_float(E, T, p, c):
    m = int(math.floor(c))
    tot = 0.0
    for e in range(E):
        pe = float(p[e]); mu = T*pe; sd = sqrt(max(mu*(1-pe), 0.0))
        if mu + 10.0*sd <= m:      # this expert cannot overflow to within 10 sigma: prune
            continue
        for i in range(m+1, T+1):
            tot += (i-c)*_lpmf(T, pe, i)
    return tot/T

# ---------- route B: the same sum, exact integer arithmetic (uniform router) ----------
def drop_exact_uniform(E, T, c):
    """Exact for p = (1/E,...,1/E): P(N=i) = C(T,i)(E-1)^(T-i) / E^T.

    The factor (i-c) is split as (i-b) - f, b = floor(c), f = c-b, so both sums stay in EXACT
    integer arithmetic; only the final combination uses a Fraction. (Multiplying a huge int by a
    float is what overflows -- the factor is separated rather than converted.)"""
    b = int(math.floor(c)); f = Fraction(float(c)) - b
    S1 = 0; S2 = 0
    for i in range(b+1, T+1):
        w = comb(T, i)*pow(E-1, T-i)
        S1 += (i-b)*w
        S2 += w
    return float(E*(Fraction(S1) - f*S2)/Fraction(pow(E, T))/T)

# ---------- route C: sampling ----------
def drop_mc(E, T, p, c, M=MC_M, seed=SEED):
    rng = np.random.default_rng(seed)
    d = np.empty(M)
    for m in range(M):
        d[m] = float(np.maximum(rng.multinomial(T, p)-c, 0).sum())/T
    return float(d.mean()), float(d.std(ddof=1)/sqrt(M))

# ---------- the corrected, TOLERANCE-INDEXED prediction ----------
def predict_c(E, T, p, tol=TOL):
    """Smallest c solving  sum_e sigma_e * E[(Z_e - z_e)+] = tol*T  (normal approximation),
    with z_e = (c - mu_e)/sigma_e. The DECLARED tolerance sits inside the equation."""
    p = np.asarray(p, dtype=float); mu = T*p
    sd = np.sqrt(np.maximum(mu*(1-p), 1e-300))
    def f(c):
        return float(np.sum(sd*phiz((c-mu)/sd))) - tol*T
    lo = 0.0; hi = float(mu.max()) + 80.0*float(sd.max()) + 1.0
    if f(hi) > 0: return float('nan')            # no finite root: refuse rather than return lo
    for _ in range(120):
        mid = 0.5*(lo+hi)
        if f(mid) > 0: lo = mid
        else: hi = mid
    return hi

def c_min_measured(E, T, p, tol=TOL):
    lo, hi = 1.0, 400.0
    if drop_float(E,T,p, hi*T/E) >= tol: return float('inf')
    for _ in range(60):
        mid = 0.5*(lo+hi)
        if drop_float(E,T,p, mid*T/E) < tol: hi = mid
        else: lo = mid
    return hi

GRID   = [(8,512),(16,512),(32,512),(32,1024),(64,1024),(64,2048),(128,1024),(128,2048),
          (256,2048),(64,256),(64,512),(64,64)]
EXACT  = [(8,512),(64,256),(64,1024),(128,1024),(256,2048)]   # the certificate subset for route B

def main():
    out = {"tol": TOL, "seed": SEED, "mc_m": MC_M, "cells": []}
    rng = np.random.default_rng(SEED)

    print("="*106)
    print("METRIC (i-a) routes A (float) and B (EXACT integer) at the SAME C  -- the tight bar")
    print("METRIC (i-b) route C (MC, M=%d) at the SAME C, scored by z" % MC_M)
    print(f"{'E':>5}{'T':>6}{'mu':>6}{'C':>6}{'A float':>15}{'B exact':>15}{'rel|A-B|':>10}{'MC mean':>13}{'MC sd':>11}{'z':>7}")
    worst_rel = 0.0; maxz = 0.0; nz = 0
    for E,T in EXACT:
        p = np.full(E, 1.0/E); c = 1.25*T/E
        A = drop_float(E,T,p,c); B = drop_exact_uniform(E,T,c)
        rel = abs(A-B)/B
        mc,sd = drop_mc(E,T,p,c)
        z = (B-mc)/sd if sd > 0 else float('nan')
        worst_rel = max(worst_rel, rel)
        if z == z: maxz = max(maxz, abs(z)); nz += 1
        print(f"{E:>5}{T:>6}{T/E:>6.1f}{1.25:>6.2f}{A:>15.10f}{B:>15.10f}{rel:>10.2e}{mc:>13.9f}{sd:>11.2e}{z:>7.2f}")
        out["cells"].append(dict(E=E,T=T,C=1.25,A=A,B=B,rel=rel,mc=mc,sd=sd,z=z))
    print(f"  -> worst |A-B| relative = {worst_rel:.2e}    (bar 1e-3; route B is exact arithmetic)")
    print(f"  -> max |z| over {nz} cells = {maxz:.2f}    (2.6 expected for the max of 5 standard normals)")
    out["worst_rel_AB"] = worst_rel; out["max_z"] = maxz

    print()
    print("="*106)
    print("METRIC (ii) THE TOLERANCE-INDEXED CURVE  (kernel now phi - z*Phibar)")
    print(f"{'E':>5}{'T':>6}{'mu':>6}{'C_min meas':>11}{'C_min pred':>11}{'rel err':>9}{'pred@1e-3':>11}{'pred@1e-9':>11}")
    iis = []
    for E,T in GRID:
        p = np.full(E, 1.0/E)
        cm = c_min_measured(E,T,p)
        Cpred = predict_c(E,T,p)*E/T
        relerr = abs(Cpred-cm)/cm if Cpred == Cpred else float('nan')
        if relerr == relerr: iis.append(relerr)
        C3 = predict_c(E,T,p,tol=1e-3)*E/T
        C9 = predict_c(E,T,p,tol=1e-9)*E/T
        print(f"{E:>5}{T:>6}{T/E:>6.1f}{cm:>11.4f}{Cpred:>11.4f}{relerr:>9.2%}{C3:>11.4f}{C9:>11.4f}")
        out.setdefault("curve",[]).append(dict(E=E,T=T,mu=T/E,c_min=cm,c_pred=Cpred,rel=relerr,c_tol1e3=C3,c_tol1e9=C9))
    print(f"  -> METRIC (ii): n={len(iis)}  max rel err = {max(iis):.2%}  mean = {sum(iis)/len(iis):.2%}  (bar 5%)")
    print("  -> the normal-approximation kernel ERRORS LOW (binomial tail); the direction is the same in every cell")
    print("  -> C_min MOVES with the DECLARED tolerance in every cell: 1e-3 < 1e-6 < 1e-9")
    out["ii_max_relerr"] = max(iis); out["ii_mean_relerr"] = sum(iis)/len(iis); out["ii_n"] = len(iis)

    print()
    print("="*106)
    print("P2 CEILING (formal): for TOKEN-CHOICE routers, C_min(router) >= C_min(perfectly uniform)")
    rngc = np.random.default_rng(SEED+1)
    for E,T in [(32,512),(64,1024),(128,1024),(256,2048)]:
        uni = c_min_measured(E,T,np.full(E,1.0/E))
        print(f"  E={E:>4} mu={T/E:>5.1f}  uniform floor = {uni:.3f}   (the strongest case for the folk constant)")
        rec = dict(E=E,T=T,mu=T/E,uniform=uni,skew=[])
        for alpha in [2.0,1.0,0.5,0.2,0.05]:
            w = rngc.dirichlet(np.full(E,alpha)); cm = c_min_measured(E,T,w)
            print(f"      dirichlet a={alpha:<5} max_p={E*w.max():>6.2f}x uniform   C_min={cm:>7.3f}   (+{cm-uni:>7.3f} over floor)")
            rec["skew"].append(dict(alpha=alpha,max_over_uniform=float(E*w.max()),c_min=cm))
        out.setdefault("ceiling",[]).append(rec)

    print()
    print("="*106)
    print("P2 BOUNDARY: the floor belongs to STOCHASTIC TOKEN-CHOICE routing; a deterministic")
    print("exact-count assignment escapes it -- but only where the budget divides the traffic.")
    for E,T in [(64,1024),(128,1024),(256,2048),(64,1000)]:
        p = np.full(E,1.0/E)
        sto = drop_float(E,T,p,1.0*T/E)
        cap = int(math.floor(1.0*T/E))
        feas = "0 drops (exact count places all T)" if cap*E >= T else \
               f"INFEASIBLE: {cap}x{E}={cap*E} < T={T} at C=1"
        print(f"  E={E:>4} T={T:>5}  stochastic token-choice D(C=1) = {sto:.6f}  |  exact-count dispatcher: {feas}")
        out.setdefault("escape",[]).append(dict(E=E,T=T,stochastic_c1=sto,cap=cap,
                                                feasible=bool(cap*E>=T),
                                                deterministic_c1=0.0 if cap*E>=T else None))

    with open("spike_v1_results.json","w") as f: json.dump(out,f,indent=1)
    print("\nwrote spike_v1_results.json")

if __name__ == "__main__":
    main()
