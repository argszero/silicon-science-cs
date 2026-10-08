#!/usr/bin/env python3
"""spike_v2 -- the CURRENT DESIGN, adopted from the host's rant item 5 (2026-10-08T07:57):

  "AN OPERATING POINT IS PER-STATISTIC AND PER-LENGTH-BAND, NOT A CUT ... the deliverable is the
   (statistic x band) operating point, and the statistic is a length-dependent choice."

So the threshold is now set the way the host sets it: tau(L, stat) = p95 of that statistic's own
NULL pool at that length (an FPR-matched operating point), and recall is measured on a
character/token substitution ladder. The null stays UNRELATED segments of the same length
(per-side length-matched, as the host does).

Objects measured here:
  N(L,stat)  the null's median and p95          -> item 5's "the null rises with length"
  FPR(L,stat) the ACTUAL false-positive rate of tau on a FRESH null pool   (must be ~0.05)
  R(eps; L,stat) recall on the substitution ladder -> eps* (recall 0.5), width, standardized collapse
Two parameterisations of the ladder: RATE (each token substituted w.p. eps) and COUNT (exactly
round(eps*L) tokens) -- they differ exactly in how a short artefact is damaged.
"""
import io, json, math, random, hashlib
import spike_v0 as s0

L_GRID   = [40, 70, 150, 350, 750, 1500, 3000]
EPS_GRID = [0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,
            0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,1.00]
STATS    = ["jac3", "jac5", "dice2c", "cos"]
N_REFS   = 50
N_NULL   = 300
N_FRESH  = 300

def sim(stat, A, B, idf):
    if stat == "jac3":
        return s0.jaccard(s0.shingles(A,3), s0.shingles(B,3))
    if stat == "jac5":
        return s0.jaccard(s0.shingles(A,5), s0.shingles(B,5))
    if stat == "cos":
        return s0.similarity("cos", A, B, idf)
    if stat == "dice2c":
        a=set(s0._char2(A)); b=set(s0._char2(B))
        u=len(a)+len(b)
        return (2*len(a&b)/u) if u else 0.0
    raise ValueError(stat)

def perturb_rate(a, eps, vocab, rng):
    if eps<=0: return list(a)
    return [(rng.choice(vocab) if rng.random()<eps else w) for w in a]

def perturb_count(a, eps, vocab, rng):
    m = int(round(eps*len(a)))
    if m<=0: return list(a)
    b = list(a)
    for i in rng.sample(range(len(b)), min(m, len(b))):
        b[i] = rng.choice(vocab)
    return b

def cross(eg, rec, p=0.5):
    for i in range(len(eg)-1):
        r0,r1=rec[i],rec[i+1]
        if (r0-p)*(r1-p)<=0 and r0!=r1:
            return eg[i]+(p-r0)*(eg[i+1]-eg[i])/(r1-r0)
    return None

def width(eg, rec):
    lo=cross(eg,rec,0.9); hi=cross(eg,rec,0.1)
    return (hi-lo) if (lo is not None and hi is not None) else None

def main():
    books=s0.load_books()
    from collections import Counter
    cnt=Counter(w for _,ws in books for w in ws)
    vocab=[w for w,_ in cnt.most_common(20000)]
    df=Counter()
    for _,ws in books: df.update(set(ws))
    N=len(books); idf={w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt}
    out={"L_grid":L_GRID,"eps_grid":EPS_GRID,"stats":STATS,"n_refs":N_REFS,
         "n_cal":N_NULL,"convention":"tau = p95 of the unrelated-segment null at the same L",
         "null":{},"fpr":{},"recall":{}}
    for stat in STATS:
        for L in L_GRID:
            rng=random.Random(s0.SEED0 + L*104729 + len(stat)*7919 + sum(map(ord,stat)))
            segs=[]
            need=N_NULL*2+N_FRESH*2+N_REFS
            for i in range(need):
                bk,ws=books[i%len(books)]
                off=rng.randrange(0,max(1,len(ws)-L-1)); segs.append(ws[off:off+L])
            null=[sim(stat,segs[2*i],segs[2*i+1],idf) for i in range(N_NULL)]
            off=N_NULL*2
            fresh=[sim(stat,segs[off+2*i],segs[off+2*i+1],idf) for i in range(N_FRESH)]
            off+=N_FRESH*2
            refs=[segs[off+i] for i in range(N_REFS)]
            med=s0.pct(null,0.5); p95=s0.pct(null,0.95); p99=s0.pct(null,0.99)
            fpr=sum(1 for v in fresh if v>=p95)/N_FRESH
            degenerate = (p95 <= 0.0)  # tau at the floor -> every pair passes -> FPR 1
            out["null"]["%s|L=%d"%(stat,L)]={"median":med,"p95":p95,"p99":p99,"n":N_NULL}
            out["fpr"]["%s|L=%d"%(stat,L)]={"fpr_at_p95":fpr,"n":N_FRESH,
                                              "degenerate_tau_zero":bool(degenerate)}
            for param,fn in (("rate",perturb_rate),("count",perturb_count)):
                rec=[]; med_curve=[]
                for eps in EPS_GRID:
                    hit=0; vals=[]
                    for r in range(N_REFS):
                        b=fn(refs[r],eps,vocab,rng)
                        sv=sim(stat,refs[r],b,idf)
                        vals.append(sv); hit += (sv>=p95)
                    rec.append(hit/N_REFS); med_curve.append(s0.pct(vals,0.5))
                key="%s|L=%d|%s"%(stat,L,param)
                out["recall"][key]={"recall":rec,"median_decay":med_curve,"tau":p95,
                                    "eps_star":cross(EPS_GRID,rec),
                                    "width_10_90":width(EPS_GRID,rec)}
            es=out["recall"]["%s|L=%d|rate"%(stat,L)]["eps_star"]
            print("%-7s L=%-5d null med=%.4f p95=%.4f FPR=%.3f%s | eps*=%s"
                  %(stat,L,med,p95,fpr,"(DEGENERATE)" if degenerate else "",
                    ("%.3f"%es) if es else "(censored)"))
    js=json.dumps(out,indent=1,sort_keys=True)
    io.open("spike_v2_results.json","w",encoding="utf-8").write(js)
    print("\nartefact sha256:",hashlib.sha256(js.encode()).hexdigest()[:16],"bytes",len(js.encode()))

if __name__=="__main__": main()
