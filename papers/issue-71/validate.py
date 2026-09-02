#!/usr/bin/env python3
"""Issue #71 — validate.py: independent re-count of the census numbers.

Recomputes every headline number STRAIGHT from the committed raw snapshots
(no shared code with hypotheses.py/sensitivity.py except the Wilson/Fisher
formulas). Fails (exit 1) on any check that does not match the manuscript's
published values. Reads only:
  snapshots/tier_ab_corpus71.json, snapshots/classifier_v2_71.json,
  snapshots/gold_pass1_71.json, snapshots/wg_manifest_evidence71.json,
  snapshots/tree_status.json
"""
import json
import os
import sys
from collections import Counter
from math import comb

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")
corpus = json.load(open(os.path.join(SNAP, "tier_ab_corpus71.json")))
cls2 = json.load(open(os.path.join(SNAP, "classifier_v2_71.json")))
gold = json.load(open(os.path.join(SNAP, "gold_pass1_71.json")))
me = json.load(open(os.path.join(SNAP, "wg_manifest_evidence71.json")))
tstatus = json.load(open(os.path.join(SNAP, "tree_status.json")))

tb = {f: r for f, r in cls2.items() if r["membership"] == "TierB"}
ta = {f: r for f, r in cls2.items() if r["membership"] == "TierA"}
neg = {f: r for f, r in cls2.items() if r["membership"] == "NEG"}
N_TB = 174
wg_l2 = {f: r for f, r in tb.items() if r["webgpu_level"] == "L2"}
wgl_l2 = {f: r for f, r in tb.items() if r["webgl_level"] == "L2"}
gpu = {f for f, r in tb.items() if r["webgpu_level"] == "L2" or r["webgl_level"] == "L2"}
l1 = {f: r for f, r in tb.items() if r["webgpu_level"] == "L1"}


def wilson(k, kk):
    z = 1.96
    if kk == 0:
        return (0.0, 1.0)
    p = k / kk
    denom = 1 + z * z / kk
    centre = (p + z * z / (2 * kk)) / denom
    half = z * (p * (1 - p) / kk + z * z / (4 * kk * kk)) ** 0.5 / denom
    return (centre - half, centre + half)


def fisher(table):
    a, b, c, d = table
    total = a + b + c + d
    row1, col1 = a + b, a + c
    lo = max(0, row1 - (b + d))
    hi = min(row1, col1)
    p_obs = comb(col1, a) * comb(total - col1, row1 - a) / comb(total, row1)
    p = 0.0
    for x in range(lo, hi + 1):
        px = comb(col1, x) * comb(total - col1, row1 - x) / comb(total, row1)
        if px <= p_obs * 1.0000001:
            p += px
    return p


CHECKS = []
def check(label, cond, detail=""):
    CHECKS.append((label, bool(cond), detail))


# C01 corpus composition
check("C01 corpus = TierA 5 + TierB 174 + NEG 3 = 182",
      len(ta) == 5 and len(tb) == N_TB and len(neg) == 3 and len(cls2) == 182,
      f"actual TierA={len(ta)} TierB={len(tb)} NEG={len(neg)} total={len(cls2)}")
# C02 strata quotas
sc = Counter(r["stratum"] for r in tb.values())
check("C02 six TierB strata x 29", all(sc[s] == 29 for s in
      ["S1_web3d_graphics", "S2_dataviz_creative", "S3_ai_web",
       "S4_webapps_editors", "S5_games_web", "S6_web_infra"]), str(dict(sc)))
# C03 head_sha pinned
pinned = sum(1 for f, r in corpus.items() if r.get("head_sha"))
check("C03 all 182 repos head_sha-pinned", pinned == 182, f"{pinned}/182")
# C04 NEG dual-L0
neg_clean = all(r["webgpu_level"] == "L0" and r["webgl_level"] == "L0" for r in neg.values())
check("C04 NEG 3/3 dual-L0 (react/axios/prettier)", neg_clean and len(neg) == 3)
# C05 TierA anchors 4/5 L2 webgpu (gpuweb = spec L1)
ta_l2 = sorted(f for f, r in ta.items() if r["webgpu_level"] == "L2")
check("C05 TierA 4/5 L2 webgpu (gpuweb spec not adopter)", len(ta_l2) == 4 and "gpuweb/gpuweb" not in ta_l2,
      str(ta_l2))
# C06 headline rate + CI
lo, hi = wilson(len(wg_l2), N_TB)
check("C06 WebGPU L2 = 14/174 = 8.0% Wilson95[4.9,13.1]",
      len(wg_l2) == 14 and abs(len(wg_l2) / N_TB * 100 - 8.0) < 0.05 and
      abs(lo * 100 - 4.9) < 0.2 and abs(hi * 100 - 13.1) < 0.2,
      f"k={len(wg_l2)} CI=[{lo*100:.2f},{hi*100:.2f}]")
# C07 WebGL baseline counts
wgl_only = gpu - set(wg_l2)
check("C07 WebGL L2 = 48; webgl-only = 37; GPU users = 51",
      len(wgl_l2) == 48 and len(wgl_only) == 37 and len(gpu) == 51,
      f"webgl={len(wgl_l2)} webgl-only={len(wgl_only)} gpu={len(gpu)}")
# C08 WebGPU share of GPU users
share = len(wg_l2) / len(gpu) * 100
check("C08 WebGPU = 27.5% of GPU users (WebGL 72.5%)", abs(share - 27.5) < 0.05,
      f"{share:.2f}%")
# C09 roles
roles = Counter(r["webgpu_role"] for r in wg_l2.values())
check("C09 roles render 10 / compute 2 / both 2",
      roles["render"] == 10 and roles["compute"] == 2 and roles["both"] == 2,
      str(dict(roles)))
# C10 dual-renderer
dual = sum(1 for f in wg_l2 if tb[f]["webgl_level"] == "L2")
check("C10 dual-renderer 11/14 = 79%", dual == 11, f"{dual}/14")
# C11 per-stratum webgpu L2 counts
per_s = Counter(r["stratum"] for r in wg_l2.values())
check("C11 strata S1=7 S2=1 S3=3 S4=1 S5=1 S6=1",
      per_s == Counter({"S1_web3d_graphics": 7, "S2_dataviz_creative": 1, "S3_ai_web": 3,
                        "S4_webapps_editors": 1, "S5_games_web": 1, "S6_web_infra": 1}),
      str(dict(per_s)))
# C12 L1 repos and upper bound
l1_names = sorted(l1)
p_s1 = fisher([7, 29 - 7, 14 - 7, N_TB - 29])
p_s3 = fisher([3, 29 - 3, 14 - 3, N_TB - 29])
check("C12 L1 = 3 (deck.gl/galacean/tres); upper bound 17/174 = 9.8%",
      len(l1) == 3 and set(l1_names) == {"Tresjs/tres", "galacean/engine", "visgl/deck.gl"},
      str(l1_names))
k_up = len(wg_l2) + len(l1)
lo_up, hi_up = wilson(k_up, N_TB)
check("C12b L1-upper 9.8% CI[6.2,15.1]", k_up == 17 and abs(lo_up * 100 - 6.2) < 0.2 and
      abs(hi_up * 100 - 15.1) < 0.2, f"CI=[{lo_up*100:.2f},{hi_up*100:.2f}]")
# C13 S1 concentration Fisher
check("C13 Fisher S1-vs-rest p = 0.0021", abs(p_s1 - 0.00208) < 0.001, f"p={p_s1:.5f}")
# C14 S3-AI NOT elevated
check("C14 Fisher S3-AI p >= 0.4 (NOT elevated vs #68 MCP)", p_s3 > 0.4, f"p={p_s3:.4f}")
# C15 gold pass anchors: vscode L2 raw WebGPU (codesearch paths in editor/browser/gpu);
# web-llm EP-only (gold signals have zero navigator.gpu)
vsc_gold = gold.get("microsoft/vscode", {})
webllm_gold = gold.get("mlc-ai/web-llm", {})
vsc_paths = " ".join(vsc_gold.get("l1_codesearch", []))
def signals_of(entry):
    out = []
    for path, info in entry.items():
        if isinstance(info, dict):
            out.extend(info.get("signals", []))
    return out
webllm_sig = signals_of(webllm_gold)
check("C15 gold: vscode raw WebGPU (editor/browser/gpu); web-llm EP-only (zero navigator.gpu)",
      "editor/browser/gpu" in vsc_paths and "navigator.gpu" not in webllm_sig,
      f"vscode paths w/ gpu layer={'Y' if 'editor/browser/gpu' in vsc_paths else 'N'}; "
      f"web-llm navigator.gpu={'Y' if 'navigator.gpu' in webllm_sig else 'N'}")
# C16 tree coverage
ok_t = sum(1 for v in tstatus.values() if v.startswith("ok"))
trunc_t = sum(1 for v in tstatus.values() if "truncated=True" in v)
check("C16 trees 182/182 @ pinned HEAD, 0 truncated", ok_t == 182 and trunc_t == 0 and len(tstatus) == 182,
      f"ok={ok_t} truncated={trunc_t}")
# C17 liveness
live_tb = sum(1 for f in wg_l2 if corpus.get(f, {}).get("archived") is False)
live_ta = sum(1 for f in ta if corpus.get(f, {}).get("archived") is False)
check("C17 all adopters + anchors live (archived=False)",
      live_tb == len(wg_l2) == 14 and live_ta == len(ta) == 5, f"tb={live_tb}/14 ta={live_ta}/5")
# C18 language mix
lang = Counter(corpus[f].get("language") for f in corpus)
check("C18 language mix TS102/JS70 (n=182)", lang.get("TypeScript") == 102 and lang.get("JavaScript") == 70,
      str(dict(lang)))
# C19 engine-dep carrier census (H2): 26 carriers / 7 L2 (2 engines + 5 app)
ENGINE_DEPS = ("three", "@babylonjs/core", "pixi.js", "playcanvas", "@galacean/engine")
carrier = {}
for f, manifests in me.items():
    if f not in tb:
        continue
    hits = []
    for mf, deps in manifests.items():
        for x in deps:
            if any(e in x.lower() for e in ENGINE_DEPS):
                hits.append(x)
    if hits:
        carrier[f] = sorted(set(hits))
carrier_l2 = set(carrier) & set(wg_l2)
carrier_eng = {f for f in carrier_l2 if f in {"pixijs/pixijs", "playcanvas/engine"}}
check("C19 engine-dep carriers: 26 total / 7 L2 (2 engines + 5 app-level selectors)",
      len(carrier) == 26 and len(carrier_l2) == 7 and len(carrier_eng) == 2,
      f"carriers={len(carrier)} l2={len(carrier_l2)} engines={len(carrier_eng)}")

ok = True
print("validate.py — independent re-count of manuscript census numbers")
print("=" * 72)
for label, passed, detail in CHECKS:
    print(f"  [{'OK' if passed else 'FAIL'}] {label}" + (f"  ({detail})" if not passed else ""))
    ok = ok and passed
print("=" * 72)
print(f"{'PASS: all checks match manuscript values' if ok else 'FAIL: mismatches found'}")
sys.exit(0 if ok else 1)
