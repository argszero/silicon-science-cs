#!/usr/bin/env python3
"""floor_v3 -- the CERTIFICATION FLOOR, principled: a statistic has an FPR-matched operating point
at level alpha only if the null pool's alpha-quantile is ABOVE the statistic's floor. For shingle
statistics the floor is 0, so the condition is P(a null pair shares >=1 shingle) >= alpha.
Measured directly (fraction of null pairs with S > 0) over a length grid, for alpha = 0.05 and 0.01.
Consequence: the floor is a property of (statistic, length, alpha) -- a stricter FPR needs longer text.
"""
import io, json, math, random, hashlib
from collections import Counter
import spike_v0 as s0, spike_v2 as s2

LS=[40,70,100,150,250,400,700,1200,2000,3500]
NNULL=400
ALPHAS=[0.05,0.01]

def main():
    books=s0.load_books()
    out={"definition":"share(L) = fraction of unrelated same-length null pairs with S > 0; "
                      "floor L*(alpha) = smallest L with share(L) >= alpha",
         "n_null":NNULL,"alphas":ALPHAS,"L_grid":LS,"share":{},"L_star":{}}
    for stat in ("jac3","jac5"):
        for L in LS:
            rng=random.Random(s0.SEED0+L*13+len(stat))
            segs=[]
            for i in range(NNULL*2):
                bk,ws=books[i%len(books)]
                off=rng.randrange(0,max(1,len(ws)-L-1)); segs.append(ws[off:off+L])
            share=sum(1 for i in range(NNULL) if s2.sim(stat,segs[2*i],segs[2*i+1],s2_idf(books))>0.0)/NNULL
            out["share"]["%s|L=%d"%(stat,L)]=share
        row=[]
        for a in ALPHAS:
            hit=None
            for L in LS:
                if out["share"]["%s|L=%d"%(stat,L)]>=a: hit=L; break
            out["L_star"]["%s|alpha=%.2f"%(stat,a)]=hit
            row.append("alpha=%.2f -> L*=%s"%(a,hit if hit else "beyond %d"%LS[-1]))
        print("  %-6s share(L): %s"%(stat," ".join("%d:%.3f"%(L,out["share"]["%s|L=%d"%(stat,L)]) for L in LS)))
        print("         %s"%("  |  ".join(row)))
    js=json.dumps(out,indent=1,sort_keys=True)
    io.open("floor_v3_results.json","w",encoding="utf-8").write(js)
    print("artefact sha256:",hashlib.sha256(js.encode()).hexdigest()[:16])

_IDF={}
def s2_idf(books):
    if not _IDF:
        from collections import Counter
        df=Counter()
        for _,ws in books: df.update(set(ws))
        N=len(books)
        cnt=Counter(w for _,ws in books for w in ws)
        _IDF.update({w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt})
    return _IDF

if __name__=="__main__": main()
