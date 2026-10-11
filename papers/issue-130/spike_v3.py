#!/usr/bin/env python3
"""spike_v3 -- the PERTURBATION-OPERATOR axis.

spike_v2 perturbed at the TOKEN level (a word swapped for another word). The host's item-5 ladder
is a CHARACTER-substitution ladder. Those are different instruments: a token swap barely touches a
character-bigram set (English words share character bigrams), while a character edit destroys them.
So "a 20% rewording" is an operator-dependent quantity, and the operator must be an explicit axis.
This script measures both operators at the SAME FPR-matched operating point (tau = p95 of the
unrelated-pair null, operator-independent), so the two ladders can be compared directly.
"""
import io, json, math, random, hashlib
from collections import Counter
import spike_v0 as s0
import spike_v2 as s2

ALPHA = "abcdefghijklmnopqrstuvwxyz"
LGRID = [150, 750, 3000]
EPS   = [0.0,0.02,0.05,0.10,0.15,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,1.00]
STATS = ["jac3","jac5","dice2c","cos"]
NREFS, NNULL = 40, 300

def pert_tok(s, eps, vocab, rng):
    if eps<=0: return s
    return " ".join((rng.choice(vocab) if rng.random()<eps else w) for w in s.split())

def pert_chr(s, eps, rng):
    if eps<=0: return s
    return "".join((rng.choice(ALPHA) if (c.isalpha() and rng.random()<eps) else c) for c in s)

def main():
    books=s0.load_books()
    cnt=Counter(w for _,ws in books for w in ws); vocab=[w for w,_ in cnt.most_common(20000)]
    df=Counter()
    for _,ws in books: df.update(set(ws))
    N=len(books); idf={w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt}
    out={"note":__doc__,"L_grid":LGRID,"eps_grid":EPS,"stats":STATS,"n_refs":NREFS,
         "operators":["tok","chr"],"cells":{}}
    for L in LGRID:
        rng=random.Random(s0.SEED0+L*97)
        segs=[]
        for i in range(NNULL*2+NREFS):
            bk,ws=books[i%len(books)]
            off=rng.randrange(0,max(1,len(ws)-L-1)); segs.append(" ".join(ws[off:off+L]))
        nulls=[]
        for stat in STATS:
            nulls.append([s2.sim(stat,segs[2*i].split(),segs[2*i+1].split(),idf) for i in range(NNULL)])
        tau={st:s0.pct(nulls[k],0.95) for k,st in enumerate(STATS)}
        refs=segs[NNULL*2:]
        for op in ("tok","chr"):
            for ei,eps in enumerate(EPS):
                sims={st:[] for st in STATS}
                for ri,s in enumerate(refs):
                    # DETERMINISM (R567): was random.Random(hash((L,op,ei,hash(s)%10**6))) -- hash()
                    # of a str is randomized per process, so the CHARACTER arm drew a new sample every
                    # run (the token arm was stable, since it used the cell-level rng above: a built-in
                    # control that localised the defect to the arm whose seed contained hash()).
                    b = (pert_tok(s,eps,vocab,rng) if op=="tok"
                         else pert_chr(s,eps,random.Random(s0.SEED0+L*97+ri*7919+ei*104729+(1 if op=="chr" else 2))))
                    bt=b.split()
                    for st in STATS: sims[st].append(s2.sim(st,s.split(),bt,idf))
                for st in STATS:
                    key="%s|L=%d|%s|eps=%.2f"%(st,L,op,eps)
                    rec=sum(1 for v in sims[st] if v>=tau[st])/NREFS
                    out["cells"][key]={"recall":rec,"median":s0.pct(sims[st],0.5),"tau":tau[st]}
        for st in STATS:
            for op in ("tok","chr"):
                eg=EPS; rc=[out["cells"]["%s|L=%d|%s|eps=%.2f"%(st,L,op,e)]["recall"] for e in EPS]
                es=s2.cross(eg,rc,0.5) if s2.cross(eg,rc,0.5) else s2.cross(eg,[1-v for v in rc],0.5)
                # detection curve: recall rises with eps for the *change* reading? here flag=duplicate,
                # so recall FALLS from 1 to ~FPR.  eps* is the 0.5 crossing of the falling curve.
                es=s2.cross(eg,rc,0.5)
                out["cells"]["%s|L=%d|%s|eps_star"%(st,L,op)]={"eps_star":es,"tau":tau[st]}
            print("%-7s L=%-5d tau=%.4f | tok eps*=%s | chr eps*=%s"%(
                st,L,tau[st],
                out["cells"].get("%s|L=%d|tok|eps_star"%(st,L),{}).get("eps_star"),
                out["cells"].get("%s|L=%d|chr|eps_star"%(st,L),{}).get("eps_star")))
    js=json.dumps(out,indent=1,sort_keys=True)
    io.open("spike_v3_results.json","w",encoding="utf-8").write(js)
    print("\nartefact sha256:",hashlib.sha256(js.encode()).hexdigest()[:16],"bytes",len(js.encode()))

if __name__=="__main__": main()
