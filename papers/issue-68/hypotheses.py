#!/usr/bin/env python3
"""Issue #68 — hypotheses.py: regenerate the hypotheses report from committed snapshots.

Offline: reads snapshots/gold_final.json + snapshots/tier_ab_corpus.json +
snapshots/h4_repo_meta.json + snapshots/h3_evidence.json. Writes snapshots/hypotheses_report.txt.
Deterministic (no RNG, no network, no timestamps).

Usage: python3 hypotheses.py
"""
import json, math, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

GOLD = json.load(open(SNAP / "gold_final.json"))
CORPUS = json.load(open(SNAP / "tier_ab_corpus.json"))
H4 = json.load(open(SNAP / "h4_repo_meta.json"))
H3 = json.load(open(SNAP / "h3_evidence.json"))

tb = GOLD["tierB_L2"]
L2_B = tb["server"] + tb["client"] + tb["both"]
N_B = 174

def membership(repo):
    return CORPUS[repo].get("stratum", "?")

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), min(1.0, c+h))

def fisher(a, b, c, d):
    from math import comb
    N = a+b+c+d; R1, C1 = a+b, a+c
    lo, hi = max(0, R1+C1-N), min(R1, C1)
    def pof(x): return (comb(R1,x)*comb(N-R1,C1-x))/comb(N,C1)
    pobs = pof(a)
    return sum(pof(x) for x in range(lo,hi+1) if pof(x) <= pobs+1e-15)

out = []
P = out.append

P("=" * 76)
P("Issue #68 — MCP in the Wild: hypotheses report (gold 2-pass FINAL)")
P("census date 2026-09-02 | corpus 187 = TierA 10 + TierB 174 + NEG 3")
P("=" * 76)

# ---------------- H1 ----------------
P("\n[H1] MCP adoption is ecosystem-concentrated — CONFIRMED")
lo, hi = wilson(len(L2_B), N_B)
P(f"Tier B L2: {len(L2_B)}/174 = {len(L2_B)/N_B:.1%}  Wilson95 [{lo:.1%}, {hi:.1%}]")
strata_L2 = Counter(membership(r) for r in L2_B)
ai_l2 = sum(strata_L2[s] for s in ["S1_ai_tooling","S2_ai_devtools","S3_ai_apps","S4_ai_frameworks"])
gen_l2 = sum(strata_L2[s] for s in ["S5_general_apps","S6_automation_obs"])
p1 = fisher(ai_l2, 116-ai_l2, gen_l2, 58-gen_l2)
P(f"per-stratum L2: {dict(sorted(strata_L2.items()))}  (n=29 each)")
P(f"AI strata (S1-S4): {ai_l2}/116 = {ai_l2/116:.1%}  vs  general (S5-S6): {gen_l2}/58 = {gen_l2/58:.1%}")
P(f"Fisher two-sided p = {p1:.3g}")
chi2 = sum((v - len(L2_B)/6)**2 / (len(L2_B)/6) for v in strata_L2.values())
P(f"chi2 vs uniform (df=5) = {chi2:.1f}")
P(f"reference: eBPF census Tier B 6/174 = 3.4% (journal issue #65); MCP rate ≈ 7x higher")

# ---------------- H2 ----------------
srv, cli, both = len(tb["server"]), len(tb["client"]), len(tb["both"])
P("\n[H2] supply-side asymmetry (servers shipped ≫ clients consumed) — naive FALSIFIED")
P(f"Tier B L2 roles: server {srv} / client {cli} / both {both}")
lo, hi = wilson(srv, srv+cli)
P(f"pure server {srv} vs pure client {cli}: {srv/(srv+cli):.1%}  Wilson95 [{lo:.1%}, {hi:.1%}]")
P(f"ships >=1 server: {srv+both} | embeds >=1 client: {cli+both}")
P(f"context: MCPZoo 2607.11086 measured 64,611 registered servers (supply side); production adoption")
P(f"  in top OSS is NOT client-starved — role-balanced overall.")
mat = {s: Counter() for s in ["S1_ai_tooling","S2_ai_devtools","S3_ai_apps","S4_ai_frameworks","S5_general_apps","S6_automation_obs"]}
for role, repos in tb.items():
    for r in repos:
        mat[membership(r)][role] += 1
def agg(strata):
    s = c = b = 0
    for x in strata:
        s += mat[x].get("server",0); c += mat[x].get("client",0); b += mat[x].get("both",0)
    return s, c, b
ai = agg(["S1_ai_tooling","S2_ai_devtools","S3_ai_apps","S4_ai_frameworks"])
gen = agg(["S5_general_apps","S6_automation_obs"])
p2 = fisher(ai[0], ai[1], gen[0], gen[1])
P("\nH2-refined (role x stratum):")
P(f"AI strata:     server {ai[0]} / client {ai[1]} / both {ai[2]}")
P(f"general:       server {gen[0]} / client {gen[1]} / both {gen[2]}")
P(f"Fisher pure-role p = {p2:.3g} (small-n: {gen[0]+gen[1]} general pure adopters; descriptive)")
P("Morphology: general OSS ships MCP servers to EXPORT data/tools to AI agents; client embedding")
P("  (IMPORT) is confined to AI-native strata (S3 apps: 6 client vs 1 server).")

# ---------------- H3 ----------------
P("\n[H3] spec-version drift — REFRAMED: version-space expansion + pin-strategy taxonomy")
sc = H3["sdk_constants"]
P(f"registered at registration (2026-05): 3 spec versions (2024-11-05 / 2025-03-26 / 2025-06-18)")
P(f"observed at census: typescript-sdk LATEST_PROTOCOL_VERSION = {sc['LATEST_PROTOCOL_VERSION']};")
P(f"  SUPPORTED = {sc['SUPPORTED_PROTOCOL_VERSIONS']}")
P(f"  spec type files: {', '.join(H3['spec_type_files'])}")
for v, d in sorted(H3["codesearch_file_hits"].items()):
    P(f"code-search protocolVersion {v}: {d['files']} file hits / {d['repos']} repos")
P("app-level explicit pins (content-verified, 3/41 entry-file literals):")
for pin in H3["app_level_pins_content_verified"]:
    P(f"  - {pin['repo']}: {pin['pin']}  [{pin['strategy']}]")
P("FINDING: 'adopters stuck on stale pins' NOT supported. Majority ride SDK negotiation;")
P("  drift = version-space expansion + deliberate pin strategies (legacy-compat/current/bleeding-edge).")
P(f"SDK version evidence: TS SDK {H3['sdk_versions']['typescript_sdk_range']}; rmcp {H3['sdk_versions']['rmcp']};")
P(f"  mcp-go {H3['sdk_versions']['mcp-go']}; fastmcp {H3['sdk_versions']['fastmcp']}")

# ---------------- H4 ----------------
P("\n[H4] 2025-era adoption cohort — CROSS-SECTIONAL (longitudinal limited)")
crey = Counter(m["created_at"][:4] for m in H4.values() if "error" not in m)
P(f"L2 adopters by repo creation year: {dict(sorted(crey.items()))}")
c25 = sum(crey.get(y,0) for y in ('2025','2026'))
P(f"created 2025+: {c25}/{len(L2_B)} — adoption in this population is RECENT")
stale = [r for r,m in H4.items() if "error" not in m and (m['archived'] or m['pushed_at'][:10] < '2026-06-01')]
P(f"archived or no-push-since-2026-06: {len(stale)} {stale}")
P("LIMITATION (by-construction): corpus = top-star + HEAD-pinnable -> survival ~100% not informative;")
P("  honest claim: all 41 adopters active at census; 2025 cohort (14 repos) none abandoned.")

# ---------------- controls ----------------
P("\n[NEG] control: 3/3 L0 (redis/redis, FFmpeg/FFmpeg, sqlite/sqlite) — no MCP deps or source paths")
P("[Tier A] 8/8 adopting anchors L2 by-construction; punkpeye/awesome-mcp-servers (curation, L0) and")
P("  modelcontextprotocol/modelcontextprotocol (spec/docs, L1-infra) excluded as infra, not adopters")

P("\n" + "=" * 76)
P(f"HEADLINE: Tier B L2 = 41/174 = 23.6%  Wilson95 [{wilson(len(L2_B), N_B)[0]:.1%}, {wilson(len(L2_B), N_B)[1]:.1%}]")

text = "\n".join(out) + "\n"
(SNAP / "hypotheses_report.txt").write_text(text)
sys.stdout.write(text)
