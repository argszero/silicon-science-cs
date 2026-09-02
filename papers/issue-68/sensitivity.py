#!/usr/bin/env python3
"""Issue #68 — sensitivity.py: regenerate the sensitivity report from committed snapshots.

Offline. Reads snapshots/gold_final.json + snapshots/tier_ab_corpus.json. Writes
snapshots/sensitivity_report.txt. Deterministic.

Usage: python3 sensitivity.py
"""
import json, math, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

GOLD = json.load(open(SNAP / "gold_final.json"))
CORPUS = json.load(open(SNAP / "tier_ab_corpus.json"))
tb = GOLD["tierB_L2"]
L2_B = tb["server"] + tb["client"] + tb["both"]
N_B = 174

def membership(repo):
    return CORPUS[repo].get("stratum", "?")

def wilson(k, n, z=1.96):
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0,c-h), min(1,c+h))

def fisher(a, b, c, d):
    from math import comb
    N=a+b+c+d; R1,C1=a+b,a+c
    lo,hi=max(0,R1+C1-N),min(R1,C1)
    def pof(x): return (comb(R1,x)*comb(N-R1,C1-x))/comb(N,C1)
    pobs=pof(a)
    return sum(pof(x) for x in range(lo,hi+1) if pof(x)<=pobs+1e-15)

out = []
P = out.append
P("=" * 72)
P("Issue #68 — sensitivity analysis (gold 2-pass FINAL 41/174)")
P("=" * 72)

strata_L2 = Counter(membership(r) for r in L2_B)
ai_l2 = sum(strata_L2[s] for s in ["S1_ai_tooling","S2_ai_devtools","S3_ai_apps","S4_ai_frameworks"])
gen_l2 = sum(strata_L2[s] for s in ["S5_general_apps","S6_automation_obs"])

P("\n[1] Headline rate 41/174 = 23.6% (Wilson95 [17.9%, 30.4%])")
for target in (0.20, 0.15, 0.10):
    k = int(target*174)
    lo,hi = wilson(k,174)
    P(f"rate <= {target:.0%} requires k <= {k} -> need {41-k} more false positives (at k={k}: {k/174:.1%} Wilson95 [{lo:.1%},{hi:.1%}])")
P("all 41 false -> 0%; 35 false (6 remain) -> 3.4% (= eBPF rate, the rarity baseline)")

P("\n[2] H1 (AI {}/116 vs general {}/58): AI-flip erosion".format(ai_l2, gen_l2))
for flips in range(0, 13):
    a = ai_l2 - flips
    p = fisher(max(a,0), 116-max(a,0), gen_l2, 58-gen_l2)
    if flips in (0,1,2,3,5,8,11) or (p >= 0.05 and flips < 12):
        P(f"{flips} AI L2 -> L0: AI {max(a,0)}/116, p = {p:.3g}{'  <-- crosses 0.05' if p>=0.05 else ''}")
        if p >= 0.05: break
pg0 = fisher(ai_l2, 116-ai_l2, 0, 58)
P(f"ALL general L2 ({gen_l2}) false: p = {pg0:.3g} (still significant)")

P("\n[3] H2-refined (AI srv/cli vs gen srv4/cli0)")
for flips in range(0, 5):
    g = 4 - flips
    p = fisher(16, 14, max(g,0), 0)
    P(f"{flips} general server L2 -> L0: gen srv {max(g,0)}/cli 0, p = {p:.3g}")
P("note: baseline p = 0.126 (small-n) -> descriptive claim only; not headline")

P("\n[4] Threshold gap (L1 borderline not counted)")
P("L2->L1 downgrades in gold: elizaOS/eliza, coze-dev/coze-studio (2)")
lo,hi = wilson(43,174)
P(f"if both were L2: rate {43/174:.1%} Wilson95 [{lo:.1%},{hi:.1%}]")
lo,hi = wilson(39,174)
P(f"if both L0:       rate {39/174:.1%} Wilson95 [{lo:.1%},{hi:.1%}]")
P("-> headline robust to +/-2 adjudication at the L2/L1 boundary (CIs overlap)")

P("\n[5] Data completeness")
P("trees fetched 187/187 (0 truncate/fail); corpus 187 head_sha-pinned.")
P("-> no missing-tree correction needed (unlike eBPF census #65: 8 stream-cancel repos)")

text = "\n".join(out) + "\n"
(SNAP / "sensitivity_report.txt").write_text(text)
sys.stdout.write(text)
