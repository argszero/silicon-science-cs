#!/usr/bin/env python3
"""floor_v2 -- the CERTIFICATION FLOOR (P4, reformulated): the shortest artefact at which a
statistic's FPR-matched operating point EXISTS at all (tau = null p95 > 0). Below it the
operating point is degenerate: tau sits on the floor, every pair passes, and the FPR is 1.0.
Measured by bisection on real text, with the null pool rebuilt at every probe.
"""
import random, json, hashlib, io, math
from collections import Counter
import spike_v0 as s0
import spike_v2 as s2

def null_p95(stat, L, n, rng, vocab, idf, books):
    segs=[]
    for i in range(n*2):
        bk,ws=books[i%len(books)]
        off=rng.randrange(0,max(1,len(ws)-L-1)); segs.append(ws[off:off+L])
    vals=[s2.sim(stat,segs[2*i],segs[2*i+1],idf) for i in range(n)]
    return s0.pct(vals,0.95)

def main():
    books=s0.load_books()
    cnt=Counter(w for _,ws in books for w in ws); vocab=[w for w,_ in cnt.most_common(20000)]
    df=Counter()
    for _,ws in books: df.update(set(ws))
    N=len(books); idf={w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt}
    out={"definition":"smallest L at which null p95 > 0 (bisection; 200 null pairs per probe)",
         "n_null_per_probe":200,"lo":100,"hi":4000,"floors":{}}
    for stat in ("jac3","jac5"):
        lo,hi=100,4000
        # ensure hi is non-degenerate
        rng=random.Random(s0.SEED0+3331)
        if null_p95(stat,hi,200,rng,vocab,idf,books)<=0.0:
            print("  %-5s: still degenerate at L=%d -- widen"%(stat,hi)); continue
        trace=[]
        while hi-lo>50:
            mid=(lo+hi)//2
            p=null_p95(stat,mid,200,random.Random(s0.SEED0+mid),vocab,idf,books)
            trace.append((mid,round(p,5)))
            if p>0.0: hi=mid
            else: lo=mid
        out["floors"][stat]={"L_floor":hi,"bracket":[lo,hi],"trace":trace}
        print("  %-5s certification floor L* = %d  (bracket [%d,%d])"%(stat,hi,lo,hi))
        print("        probes:",trace)
    js=json.dumps(out,indent=1,sort_keys=True)
    io.open("floor_v2_results.json","w",encoding="utf-8").write(js)
    print("artefact sha256:",hashlib.sha256(js.encode()).hexdigest()[:16])

if __name__=="__main__": main()
