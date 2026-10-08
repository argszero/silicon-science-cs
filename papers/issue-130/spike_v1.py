#!/usr/bin/env python3
"""spike_v1 -- the decisive P1/P2 test: hold tau FIXED (the deployed convention) and ask
whether the boundary eps*(tau) and the transition width w(tau) depend on the artefact length L.
spike_v0 calibrated tau per length (which conflates the calibration's L-dependence with the check's);
the deployer fixes one number, so the fixed-tau surface is the object that decides P1.
"""
import io, json, math, random, hashlib
import spike_v0 as s0

TAUS  = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
LEPS  = [0.00,0.01,0.02,0.03,0.05,0.07,0.10,0.13,0.16,0.20,0.25,0.30,0.40,0.50]
N_REFS = 60

def width_10_90(eg, rec):
    def cross(p):
        for i in range(len(eg)-1):
            r0,r1=rec[i],rec[i+1]
            if (r0-p)*(r1-p)<=0 and r0!=r1:
                return eg[i]+(p-r0)*(eg[i+1]-eg[i])/(r1-r0)
        return None
    lo,hi=cross(0.1),cross(0.9)
    return (hi-lo) if (lo is not None and hi is not None) else None

def main():
    books=s0.load_books()
    allt=[w for _,ws in books for w in ws]
    from collections import Counter
    cnt=Counter(allt); vocab=[w for w,_ in cnt.most_common(20000)]
    df=Counter()
    for _,ws in books: df.update(set(ws))
    N=len(books); idf={w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt}

    out={"taus":TAUS,"eps_grid":LEPS,"n_refs":N_REFS,"cells":{}}
    for stat in ("jac5","cos","jac3c"):
        for L in s0.L_GRID:
            rng=random.Random(s0.SEED0+L*7919+len(stat))
            refs=[]
            for r in range(N_REFS):
                bk,ws=books[r%len(books)]
                off=rng.randrange(0,max(1,len(ws)-L-1)); refs.append(ws[off:off+L])
            # per-eps similarities (paired across taus: one edit draw, many thresholds)
            sims={eps:[] for eps in LEPS}
            for eps in LEPS:
                for r in range(N_REFS):
                    a=refs[r]; e=a if eps==0.0 else s0.perturb(a,eps,vocab,rng)
                    sims[eps].append(s0.similarity(stat,a,e,idf))
            for tau in TAUS:
                rec=[sum(1 for v in sims[e] if v<tau)/N_REFS for e in LEPS]
                est=s0.crossing(LEPS,rec); w=width_10_90(LEPS,rec)
                # null (eps=0): the check must NOT fire on the unedited artefact
                null_fire=sum(1 for v in sims[0.0] if v<tau)
                key="%s|L=%d|tau=%.1f"%(stat,L,tau)
                out["cells"][key]={"eps_star":est,"width_10_90":w,
                                   "recall":rec,"null_fire":null_fire,"n":N_REFS}
            row={}
            for tau in TAUS:
                k="%s|L=%d|tau=%.1f"%(stat,L,tau); row[tau]=(out["cells"][k]["eps_star"],out["cells"][k]["width_10_90"])
            print("%-7s L=%-4d "%(stat,L)+"  ".join(
                "t%.1f:%s/%s"%(t,("%.3f"%row[t][0]) if row[t][0] else "  -  ",
                                 ("%.3f"%row[t][1]) if row[t][1] else "  -  ") for t in TAUS[2:6]))
    js=json.dumps(out,indent=1,sort_keys=True)
    io.open("spike_v1_results.json","w",encoding="utf-8").write(js)
    print("\nartefact sha256:",hashlib.sha256(js.encode()).hexdigest()[:16],"bytes",len(js.encode()))

if __name__=="__main__":
    main()
