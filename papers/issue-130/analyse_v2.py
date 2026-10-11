#!/usr/bin/env python3
"""analyse_v2 -- the laws of the FPR-matched operating point, with a certificate.

Claim (to be certified, not asserted): the boundary is fixed by WHERE THE NULL'S THRESHOLD SITS
on the duplicate's own decay curve,  eps* = f^{-1}(tau(L)),  where f(eps) is the median similarity
of an artefact against its own eps-perturbed copy and tau(L) is the null's p95.
Certificate: predict eps* from the MEASURED f and the MEASURED tau (by interpolating the measured
decay curve), and compare with the measured eps* -- two routes to the same number.
"""
import json, math
d=json.load(open("spike_v2_results.json"))
Ls=d["L_grid"]; EP=d["eps_grid"]; ST=d["stats"]

def interp_solve(eg, f, target):
    """smallest eps where f crosses target (f decreasing); linear interpolation."""
    for i in range(len(eg)-1):
        a,b=f[i],f[i+1]
        if (a-target)*(b-target)<=0 and a!=b:
            return eg[i]+(target-a)*(eg[i+1]-eg[i])/(b-a)
    return None

print("="*100)
print("TABLE 1 -- the null population is LENGTH-DEPENDENT (host rant item 5, replicated)")
print("%-7s %s"%("stat"," ".join("L=%-6d"%L for L in Ls)))
for stat in ST:
    med=[d["null"]["%s|L=%d"%(stat,L)]["median"] for L in Ls]
    p95=[d["null"]["%s|L=%d"%(stat,L)]["p95"] for L in Ls]
    print("%-7s median %s"%(stat," ".join("%-8.4f"%v for v in med)))
    print("%-7s p95    %s"%("",  " ".join("%-8.4f"%v for v in p95)))
print()
print("="*100)
print("TABLE 2 -- FPR control at tau=p95 (must be ~0.05; DEGENERATE = tau at the floor, FPR 1)")
for stat in ST:
    row=[]
    for L in Ls:
        f=d["fpr"]["%s|L=%d"%(stat,L)]
        row.append(("%.3f"%f["fpr_at_p95"])+("*" if f["degenerate_tau_zero"] else ""))
    print("  %-7s %s"%("stat" if stat==ST[0] else "", " ".join("%-7s"%v for v in row)))
print("  * = tau is 0.0000 (the null has no positive p95 at this length) -> every pair passes")
print()
print("="*100)
print("TABLE 3 -- the boundary eps* (recall 0.5) at the FPR-matched operating point")
for stat in ST:
    for param in ("rate","count"):
        vals=[]
        for L in Ls:
            c=d["recall"]["%s|L=%d|%s"%(stat,L,param)]
            vals.append(c["eps_star"])
        ok=[v for v in vals if v]
        sp = ("%.2fx"%(max(ok)/min(ok))) if len(ok)>=2 else "-"
        print("  %-7s %-6s %s   spread=%s"%(stat,param,
              " ".join(("%-9s"%("%.3f"%v)) if v else "%-9s"%"cens" for v in vals), sp))
print()
print("="*100)
print("TABLE 4 -- CERTIFICATE: eps* predicted from the measured decay curve vs measured")
print("  %-7s %-6s %6s | %s"%("stat","L","pred","measured   |diff|"))
worst=0.0; n=0
for stat in ST:
    for L in Ls:
        if d["fpr"]["%s|L=%d"%(stat,L)]["degenerate_tau_zero"]: continue
        c=d["recall"]["%s|L=%d|rate"%(stat,L)]
        pred=interp_solve(EP, c["median_decay"], c["tau"])
        meas=c["eps_star"]
        if pred is None or meas is None: continue
        df=abs(pred-meas); worst=max(worst,df); n+=1
        print("  %-7s %-6d %6.3f | %6.3f     %.3f"%(stat,L,pred,meas,df))
print("  certificate: %d cells, worst |diff| = %.3f (grid resolution %.2f)"%(n,worst,EP[1]-EP[0]))
print()
print("="*100)
print("TABLE 5 -- power-law fit of eps* vs L  (slope of log eps* on log L)")
for stat in ST:
    for param in ("rate","count"):
        xs=[];ys=[]
        for L in Ls:
            c=d["recall"]["%s|L=%d|%s"%(stat,L,param)]
            if d["fpr"]["%s|L=%d"%(stat,L)]["degenerate_tau_zero"]: continue
            if c["eps_star"]: xs.append(math.log(L)); ys.append(math.log(c["eps_star"]))
        if len(xs)>=3:
            m=len(xs); mx=sum(xs)/m; my=sum(ys)/m
            sl=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
            # r2
            b=my-sl*mx
            ss=sum((y-(sl*x+b))**2 for x,y in zip(xs,ys))
            st=sum((y-my)**2 for y in ys)
            print("  %-7s %-6s slope=%+.3f  (n=%d, R2=%.3f)"%(stat,param,sl,m,1-ss/st if st else 0))
        else:
            print("  %-7s %-6s too few resolvable cells (n=%d)"%(stat,param,len(xs)))
print()
print("="*100)
print("TABLE 6 -- mechanism: headroom (1 - tau) vs the boundary")
for stat in ST:
    print("  %-7s"%stat, " ".join("L=%-5d headroom=%.3f eps*=%.3f"%(L,1-d["null"]["%s|L=%d"%(stat,L)]["p95"],
        d["recall"]["%s|L=%d|rate"%(stat,L)]["eps_star"] or float('nan')) for L in Ls if not d["fpr"]["%s|L=%d"%(stat,L)]["degenerate_tau_zero"]))
