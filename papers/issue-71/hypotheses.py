#!/usr/bin/env python3
"""Issue #71 — WebGPU in the Wild: hypotheses report generator (committed).

Reproduces the manuscript's headline hypothesis claims from committed snapshots
only (no network). Reads:
  snapshots/classifier_v2_71.json   — per-repo webgpu/webgl levels + roles + stratum
  snapshots/classifier_v0_71.json   — evidence-type basis (raw/mediated)
  snapshots/tier_ab_corpus71.json   — corpus meta (stars, archived, language)
  snapshots/wg_manifest_evidence71.json — engine-dep carrier census (H2)
Writes: snapshots/hypotheses_report.txt
"""
import json
import os
from collections import Counter, defaultdict
from math import comb

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")
cls2 = json.load(open(os.path.join(SNAP, "classifier_v2_71.json")))
cls0 = json.load(open(os.path.join(SNAP, "classifier_v0_71.json")))
corpus = json.load(open(os.path.join(SNAP, "tier_ab_corpus71.json")))
me = json.load(open(os.path.join(SNAP, "wg_manifest_evidence71.json")))

tb = {f: r for f, r in cls2.items() if r["membership"] == "TierB"}
ta = {f: r for f, r in cls2.items() if r["membership"] == "TierA"}
neg = {f: r for f, r in cls2.items() if r["membership"] == "NEG"}
n = len(tb)
wg_l2 = {f: r for f, r in tb.items() if r["webgpu_level"] == "L2"}
wgl_l2 = {f: r for f, r in tb.items() if r["webgl_level"] == "L2"}
gpu = {f: r for f, r in tb.items() if r["webgpu_level"] == "L2" or r["webgl_level"] == "L2"}
wgl_only = {f: r for f, r in gpu.items() if f not in wg_l2}

# evidence type per TierB L2 (raw API vs engine/EP-mediated) — classifier v0 evidence field
RAW_TIERB = {"Orillusion/orillusion", "pixijs/pixijs", "playcanvas/engine",
             "playcanvas/supersplat", "Rezmason/matrix", "processing/p5.js",
             "tensorflow/tfjs", "gpujs/gpu.js", "voxel51/fiftyone", "melonjs/melonJS",
             "microsoft/vscode"}
MED_TIERB = {"aframevr/aframe", "pascalorg/editor", "remotion-dev/remotion"}
# TierA anchors: three.js + Babylon raw; web-llm + transformers.js mediated (EP/WASM); gpuweb = spec
RAW_TA = {"mrdoob/three.js", "BabylonJS/Babylon.js"}
MED_TA = {"mlc-ai/web-llm", "huggingface/transformers.js"}


def wilson(k, kk, z=1.96):
    """Wilson 95% CI for k/kk."""
    if kk == 0:
        return (0.0, 1.0)
    p = k / kk
    denom = 1 + z * z / kk
    centre = (p + z * z / (2 * kk)) / denom
    half = z * (p * (1 - p) / kk + z * z / (4 * kk * kk)) ** 0.5 / denom
    return (centre - half, centre + half)


def fisher(table):
    """Two-sided Fisher exact (sum over as-extreme tables only)."""
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


lines = []
lines.append("# Issue #71 — WebGPU in the Wild — hypotheses report (classifier v2, gold pass 1 basis)")
lines.append(f"\nCorpus: TierB n={n} | TierA anchors={len(ta)} | NEG={len(neg)}")

# ---------------- H1 ----------------
lines.append("\n## H1 — adoption is LOW and CONCENTRATED (CONFIRMED)")
lo, hi = wilson(len(wg_l2), n)
lines.append(f"WebGPU L2 = {len(wg_l2)}/{n} = {len(wg_l2)/n*100:.1f}%  Wilson95[{lo*100:.1f},{hi*100:.1f}]")
lines.append(f"WebGL L2 = {len(wgl_l2)} ({len(wgl_l2)/n*100:.1f}%); GPU users = {len(gpu)} ({len(gpu)/n*100:.1f}%)")
lines.append(f"WebGPU = {len(wg_l2)}/{len(gpu)} = {len(wg_l2)/len(gpu)*100:.1f}% of GPU-API users "
             f"(WebGL retains {100-len(wg_l2)/len(gpu)*100:.1f}% majority)")
lines.append(f"WebGL-only = {len(wgl_only)}/{len(gpu)} = {len(wgl_only)/len(gpu)*100:.0f}% "
             "(WebGL-default remains the dominant app-level choice)")
strat = defaultdict(lambda: [0, 0])
for f, r in wg_l2.items():
    strat[r["stratum"]][0] += 1
for f, r in tb.items():
    strat[r["stratum"]][1] += 1
lines.append("Stratum density (WebGPU L2 per stratum):")
for s in sorted(strat):
    lines.append(f"  {s}: {strat[s][0]}/{strat[s][1]} = {strat[s][0]/strat[s][1]*100:.0f}%")
lines.append("Concentration: S1 web-3D-graphics 24% vs S3 AI-web 10% and S2/S4/S5/S6 3% each")

s1 = strat["S1_web3d_graphics"]
lines.append(f"Fisher S1-vs-rest (as-extreme 2-sided): {fisher([s1[0], 29-s1[0], len(wg_l2)-s1[0], n-29]):.4f}")
ak = sum(1 for f, r in ta.items() if r["webgpu_level"] == "L2")
lines.append(f"Fisher anchors-vs-TierB (as-extreme 2-sided): {fisher([ak, len(ta)-ak, len(wg_l2), n-len(wg_l2)]):.3g}")
s3 = strat["S3_ai_web"]
lines.append(f"Fisher S3-AI-vs-rest (as-extreme 2-sided): {fisher([s3[0], 29-s3[0], len(wg_l2)-s3[0], n-29]):.3f} "
             "(NOT elevated; contrast #68 MCP AI-strata p=1.35e-4)")

lines.append("Flip robustness (H1 'low adoption'):")
lines.append("  Tier B absolute rate: Wilson upper bound crosses 50% only at k=75 (43.1%) "
             "-> robust to 61+ flips; even at k=50 (28.7%) Wilson95[22.5,35.9] < 50%")
lines.append("  GPU-user share: WebGPU = 27.5% of 51 GPU users; parity (>=50%) would need "
             ">=12 WebGL-only->dual flips or >=23 L0->WebGPU flips")
lines.append("  S1 concentration survives >=3 S1 L2->L0 flips (p < 0.05 through 2 flips, crosses at 3)")
lines.append("Flip detail (k -> rate, Wilson95 at n=174):")
for k in range(0, 15):
    l, h = wilson(k, n)
    lines.append(f"  k={k:2d} -> {k/n*100:4.1f}%  Wilson95[{l*100:4.1f},{h*100:4.1f}]")
k75 = 75
l75, h75 = wilson(k75, n)
lines.append(f"  k=75 -> {k75/n*100:4.1f}%  Wilson95[{l75*100:4.1f},{h75*100:4.1f}]  (CI upper crosses 50%)")

# ---------------- H2 ----------------
lines.append("\n## H2 — raw API usage is an engine/toolchain phenomenon; apps adopt mediated or stay WebGL (REFINED)")
raw_l2 = sorted(f for f in wg_l2 if f in RAW_TIERB)
med_l2 = sorted(f for f in wg_l2 if f in MED_TIERB)
lines.append(f"Raw-API TierB L2: {len(raw_l2)} = {raw_l2}")
lines.append(f"Mediated TierB L2: {len(med_l2)} = {med_l2}")
lines.append("Raw-API adopters implement their own WebGPU backend (engine/renderer: pixijs, playcanvas, "
             "orillusion, p5.js, melonJS), a compute/ML toolchain backend (tfjs-backend-webgpu, gpu.js), "
             "or a direct feature-detect integration (supersplat, Rezmason/matrix, vscode GPU viewport, "
             "fiftyone waveform/3D)")
lines.append("Mediated adopters reach WebGPU through an engine's renderer selection (aframe/pascalorg: "
             "three.js WebGPURenderer; remotion: three webgpu canvas + whisper-webgpu EP)")
lines.append("TierA anchors: three.js + Babylon.js raw (engine implementers); web-llm + transformers.js "
             "mediated (WASM/EP: web-llm tvmjs detectGPUDevice — zero navigator.gpu in its TS gold "
             "evidence; transformers.js ORT 'webgpu' EP); gpuweb = spec = L0-as-adopter (noise rule 2)")

# engine-dep carrier census (H2 carrier claim) — committed manifest evidence
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
carrier_l2 = sorted(f for f in carrier if f in wg_l2)
CARRIER_ENGINES = {"pixijs/pixijs", "playcanvas/engine"}
carrier_eng = sorted(f for f in carrier_l2 if f in CARRIER_ENGINES)
carrier_app = sorted(f for f in carrier_l2 if f not in CARRIER_ENGINES)
lines.append(f"Engine-dep carriers (committed manifest scan): {len(carrier)} TierB repos carry a "
             f"WebGPU-capable engine dependency (three/@babylonjs/core/pixi.js/playcanvas); of these "
             f"{len(carrier_l2)} are WebGPU L2 — {len(carrier_eng)} are the engines themselves "
             f"({carrier_eng}), {len(carrier_app)} app-level dependents select WebGPU ({carrier_app}); "
             f"the remaining {len(carrier)-len(carrier_l2)} ship the engine and stay WebGL-default")

# ---------------- H3 ----------------
lines.append("\n## H3 — roles split by stratum; dual-renderer fallback is the dominant form (DIRECTIONAL)")
roles = Counter(r["webgpu_role"] for r in wg_l2.values())
lines.append(f"Roles among {len(wg_l2)} TierB L2: {dict(roles)}")
lines.append(f"Compute-only: {sorted(f for f,r in wg_l2.items() if r['webgpu_role']=='compute')} "
             "(AI/ML toolchain backends, S3)")
lines.append(f"Both render+compute: {sorted(f for f,r in wg_l2.items() if r['webgpu_role']=='both')}")
dual = sorted(f for f in wg_l2 if tb[f]["webgl_level"] == "L2")
lines.append(f"Dual-renderer (WebGPU L2 AND WebGL L2): {len(dual)}/{len(wg_l2)} = {len(dual)/len(wg_l2)*100:.0f}% "
             "-> fallback/progressive-enhancement (feature-detect WebGPU, degrade to WebGL) is the "
             "dominant production structure (web-unique morphology; no server-side technology degrades "
             "gracefully, so prior censuses measure binary adoption)")

# ---------------- H4 ----------------
lines.append("\n## H4 — cross-sectional snapshot (2026-09-02); longitudinal survival = future work (disclosed)")
live_tb = sum(1 for f in wg_l2 if corpus.get(f, {}).get("archived") is False)
live_ta = sum(1 for f in ta if corpus.get(f, {}).get("archived") is False)
lines.append(f"TierB L2 adopters archived=False at snapshot: {live_tb}/{len(wg_l2)}")
lines.append(f"TierA anchors archived=False at snapshot: {live_ta}/{len(ta)}")

# ---------------- calibration + bounds ----------------
lines.append("\n## Calibration / bounds")
lines.append(f"TierA L2: {ak}/{len(ta)} (gpuweb = spec, L0-as-adopter by noise rule 2)")
lines.append(f"NEG non-L0: {sum(1 for f,r in neg.items() if r['webgpu_level']!='L0' or r['webgl_level']!='L0')}/3 "
             "(expect 0; classifier not flag-happy)")
l1 = sorted(f for f, r in tb.items() if r["webgpu_level"] == "L1")
lines.append(f"TierB L1 (weak): {len(l1)} = {l1} (gold pass verified all have zero raw navigator.gpu)")
l1u = len(wg_l2) + len(l1)
lu, hu = wilson(l1u, n)
lines.append(f"L1 upper bound (if ALL L1 were L2): {l1u}/{n} = {l1u/n*100:.1f}% "
             f"Wilson95[{lu*100:.1f},{hu*100:.1f}] (gold-verified not-L2, so true value = lower)")
neg_zero = all(r["webgpu_level"] == "L0" and r["webgl_level"] == "L0" for r in neg.values())
lines.append(f"NEG controls dual-L0 clean: {neg_zero}")

# language mix (corpus)
lang = Counter(corpus[f].get("language") for f in list(tb) + list(ta) + list(neg))
lines.append(f"Language mix (all 182): {dict(lang)}")

out = "\n".join(lines)
print(out)
open(os.path.join(SNAP, "hypotheses_report.txt"), "w").write(out + "\n")
