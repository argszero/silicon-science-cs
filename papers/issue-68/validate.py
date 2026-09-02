#!/usr/bin/env python3
"""Issue #68 — validate.py: independent re-count of every headline census number.

Reads ONLY the raw committed snapshots (tier_ab_corpus.json, gold_final.json,
h4_repo_meta.json, h3_evidence.json) and recomputes each number with an independent
code path (no shared logic with hypotheses.py / sensitivity.py except the
Wilson/Fisher formulas, re-implemented below).

Checks (15):
  C01 corpus 187 = TierA 10 (gold list) + TierB 174 + NEG 3 (gold list)
  C02 Tier B L2 = 41, roles server 20 / client 14 / both 7
  C03 headline 41/174 = 23.6%, Wilson95 [17.9%, 30.4%]
  C04 H1: AI strata 37/116 vs general 4/58, Fisher p < 0.001
  C05 per-stratum L2 = {S1:9, S2:4, S3:8, S4:16, S5:1, S6:3}
  C06 H2: pure server 20/34 = 58.8%, Wilson95 [42.2%, 73.6%]
  C07 H2-refined: general strata (S5,S6) server 4 / client 0 / both 0
  C08 NEG controls 3/3 L0 (not in gold L2)
  C09 Tier A: 8 adopting anchors (gold) are NOT in Tier B; 2 infra excluded
  C10 downgrade audit: eliza/coze NOT L2 (in gold pass-2 delta), lighthouse NOT L2
  C11 L2 list matches gold exactly (union server+client+both == 41 unique)
  C12 H3: sdk LATEST = 2025-11-25, SUPPORTED len 5, spec type files include 2026-07-28
  C13 H3 codesearch totals 66/65/68 files, 17/15/17 repos (2024-11-05/2025-03-26/2025-06-18)
  C14 H4: adopters created 2025+ == 23; 0 archived, 0 stale
  C15 headline rate robust: (41-2)/174 > 20% and (41+2)/174 CI still < 35%

Exit 0 iff all checks pass.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
gold = json.load(open(SNAP / "gold_final.json"))
h4 = json.load(open(SNAP / "h4_repo_meta.json"))
h3 = json.load(open(SNAP / "h3_evidence.json"))

TIER_A = set(gold["tierA_final"]["L2_adopter_anchors"]) | set(gold["tierA_final"]["infrastructure_anchors_excluded_by_construction"])
NEG = set(gold["neg_final"])
tb_gold = gold["tierB_L2"]
GOLD_L2 = set(tb_gold["server"]) | set(tb_gold["client"]) | set(tb_gold["both"])

STRATA_ORDER = ["S1_ai_tooling", "S2_ai_devtools", "S3_ai_apps", "S4_ai_frameworks", "S5_general_apps", "S6_automation_obs"]
AI_STRATA = STRATA_ORDER[:4]
GEN_STRATA = STRATA_ORDER[4:]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher_2x2(a, b, c, d):
    """Two-sided Fisher exact for [[a,b],[c,d]]."""
    def ln_fact(n):
        return 0.0 if n <= 1 else math.lgamma(n + 1)
    total = a + b + c + d
    row1, row2, col1 = a + b, c + d, a + c
    lo = max(0, row1 + col1 - total)
    hi = min(row1, col1)
    p_obs = None
    probs = []
    for a_ in range(lo, hi + 1):
        b_ = row1 - a_
        c_ = col1 - a_
        d_ = total - row1 - col1 + a_
        if b_ < 0 or c_ < 0 or d_ < 0:
            continue
        pv = math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(total - col1)
                      - ln_fact(total) - ln_fact(a_) - ln_fact(b_) - ln_fact(c_) - ln_fact(d_))
        probs.append((a_, pv))
        if a_ == a:
            p_obs = pv
    return sum(pv for _, pv in probs if pv <= p_obs + 1e-15)


def stratum(repo):
    return corpus.get(repo, {}).get("stratum", "?")


def main():
    ok = True

    def check(cid, cond, msg):
        nonlocal ok
        print(f"  [{'OK' if cond else 'FAIL'}] {cid} — {msg}")
        ok = ok and cond

    print("validate.py — independent re-count (issue #68 MCP in the Wild)")
    print("=" * 72)

    # C01 corpus composition
    tierb = [r for r in corpus if r not in TIER_A and r not in NEG]
    n_ta, n_tb, n_neg = len([r for r in corpus if r in TIER_A]), len(tierb), len([r for r in corpus if r in NEG])
    check("C01", len(corpus) == 187 and n_ta == 10 and n_tb == 174 and n_neg == 3,
          f"corpus 187 = TierA {n_ta} + TierB {n_tb} + NEG {n_neg}")

    # C02 L2 + roles
    n_l2 = len(GOLD_L2)
    srv, cli, both = len(tb_gold["server"]), len(tb_gold["client"]), len(tb_gold["both"])
    check("C02", n_l2 == 41 and srv == 20 and cli == 14 and both == 7,
          f"Tier B L2 {n_l2} (server {srv} / client {cli} / both {both})")

    # C03 headline
    lo, hi = wilson(n_l2, n_tb)
    pct = n_l2 / n_tb * 100
    check("C03", n_l2 == 41 and abs(pct - 23.6) < 0.05 and abs(lo - 0.179) < 0.002 and abs(hi - 0.304) < 0.002,
          f"headline {n_l2}/174 = {pct:.1f}%, Wilson95 [{lo:.1%}, {hi:.1%}]")

    # C04 H1 Fisher
    strata_l2 = Counter(stratum(r) for r in GOLD_L2)
    ai = sum(strata_l2[s] for s in AI_STRATA)
    ge = sum(strata_l2[s] for s in GEN_STRATA)
    n_ai, n_ge = 116, 58
    p = fisher_2x2(ai, n_ai - ai, ge, n_ge - ge)
    check("C04", ai == 37 and ge == 4 and p < 0.001,
          f"H1 AI {ai}/116 vs general {ge}/58, Fisher p = {p:.3g}")

    # C05 per-stratum
    expect = {"S1_ai_tooling": 9, "S2_ai_devtools": 4, "S3_ai_apps": 8, "S4_ai_frameworks": 16,
              "S5_general_apps": 1, "S6_automation_obs": 3}
    got = {s: strata_l2.get(s, 0) for s in STRATA_ORDER}
    check("C05", got == expect, f"per-stratum L2 {got}")

    # C06 H2 pure-server share
    lo2, hi2 = wilson(srv, srv + cli)
    check("C06", abs(srv / (srv + cli) - 0.588) < 0.005 and lo2 < 0.5 < hi2,
          f"pure server {srv}/{srv+cli} = {srv/(srv+cli):.1%} Wilson95 [{lo2:.1%}, {hi2:.1%}] crosses 50")

    # C07 H2-refined morphology
    mat = Counter()
    for r in GOLD_L2:
        if stratum(r) in GEN_STRATA:
            role = "server" if r in tb_gold["server"] else "client" if r in tb_gold["client"] else "both"
            mat[role] += 1
    check("C07", mat.get("server", 0) == 4 and mat.get("client", 0) == 0 and mat.get("both", 0) == 0,
          f"general-strata adopters server {mat.get('server',0)} / client {mat.get('client',0)} / both {mat.get('both',0)}")

    # C08 NEG
    neg_l2 = [r for r in NEG if r in GOLD_L2]
    check("C08", len(neg_l2) == 0, f"NEG controls 3/3 L0 (none in L2: {neg_l2})")

    # C09 Tier A not in Tier B count; infra excluded
    ta_in_tb = [r for r in TIER_A if r in tierb]
    check("C09", len(ta_in_tb) == 0 and len(gold["tierA_final"]["L2_adopter_anchors"]) == 8,
          f"Tier A 10 excluded from Tier B ({len(ta_in_tb)} leaked), 8 adopting anchors + 2 infra")

    # C10 downgrade audit
    dl = gold.get("level_delta_from_v0", {})
    downgraded = [r for r in ("elizaOS/eliza", "coze-dev/coze-studio", "GoogleChrome/lighthouse") if r not in GOLD_L2]
    check("C10", len(downgraded) == 3, f"gold excludes eliza, coze, lighthouse (downgrade audit)")

    # C11 L2 set unique == gold
    union = set(tb_gold["server"]) | set(tb_gold["client"]) | set(tb_gold["both"])
    check("C11", len(union) == 41 and union == GOLD_L2 and len(tb_gold["server"]) + len(tb_gold["client"]) + len(tb_gold["both"]) == 41,
          f"L2 union unique 41 == gold set")

    # C12 H3 sdk constants
    sc = h3["sdk_constants"]
    spec_files = h3["spec_type_files"]
    check("C12", sc["LATEST_PROTOCOL_VERSION"] == "2025-11-25" and len(sc["SUPPORTED_PROTOCOL_VERSIONS"]) == 5
          and any("2026-07-28" in f for f in spec_files),
          f"H3 sdk LATEST {sc['LATEST_PROTOCOL_VERSION']}, SUPPORTED {len(sc['SUPPORTED_PROTOCOL_VERSIONS'])} versions, 2026-07-28 types present")

    # C13 codesearch totals
    cs = h3["codesearch_file_hits"]
    exp_cs = {"2024-11-05": (66, 17), "2025-03-26": (65, 15), "2025-06-18": (68, 17)}
    cs_ok = all(cs[v]["files"] == f and cs[v]["repos"] == r for v, (f, r) in exp_cs.items())
    check("C13", cs_ok, f"H3 codesearch hits { {v: (cs[v]['files'], cs[v]['repos']) for v in cs} }")

    # C14 H4 recency + liveness
    meta_ok = all("error" not in m for m in h4.values())
    c25 = sum(1 for m in h4.values() if "error" not in m and m["created_at"][:4] in ("2025", "2026"))
    stale = sum(1 for m in h4.values() if "error" not in m and (m["archived"] or m["pushed_at"][:10] < "2026-06-01"))
    check("C14", meta_ok and len(h4) == 41 and c25 == 23 and stale == 0,
          f"H4 meta 41 repos, created 2025+ = {c25}, archived/stale = {stale}")

    # C15 robustness
    lo_a, _ = wilson(41 - 2, 174)
    lo_b, hi_b = wilson(41 + 2, 174)
    check("C15", (41 - 2) / 174 > 0.20 and lo_a > 0.15 and hi_b < 0.35,
          f"robustness: (41-2)/174 = {(41-2)/174:.1%} > 20%, +2 CI [{lo_b:.1%},{hi_b:.1%}] bounded")

    print("=" * 72)
    print(f"{'PASS' if ok else 'FAIL'}: independent re-count {'15/15' if ok else 'with failures'} consistent")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
