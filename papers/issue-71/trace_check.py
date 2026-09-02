#!/usr/bin/env python3
"""Issue #71 — trace_check.py: every manuscript headline number must trace to a
committed artifact (snapshots/expected_output/*, snapshots/*.json).

Manuscript numbers and their provenance:
  182 repos = TierA 5 + TierB 174 + NEG 3            -> hypotheses_report.txt
  14/174 = 8.0% Wilson95 [4.9%, 13.1%]               -> hypotheses_report.txt
  WebGL L2 = 48 (27.6%); WebGL-only 37; GPU 51       -> hypotheses_report.txt
  WebGPU 27.5% of GPU users (WebGL 72.5%)            -> hypotheses_report.txt
  S1 7/29 = 24%; S3 10%; others 3%                   -> hypotheses_report.txt
  Fisher S1-vs-rest p = 0.0021                       -> hypotheses_report.txt
  anchors-vs-TierB p = 0.000346                      -> hypotheses_report.txt
  S3-AI p = 0.464 NOT elevated                       -> hypotheses_report.txt
  robust to 61+ flips (CI crosses 50% at k=75)       -> hypotheses_report.txt
  parity needs >=12 dual or >=23 L0->WebGPU flips    -> hypotheses_report.txt
  raw 11 / mediated 3                                -> hypotheses_report.txt
  engine-dep carriers 26 / 7 L2 (2 engines, 5 app)   -> hypotheses_report.txt
  roles render 10 / compute 2 / both 2               -> hypotheses_report.txt
  dual-renderer 11/14 = 79%                          -> hypotheses_report.txt
  adopters live 14/14; anchors live 5/5              -> hypotheses_report.txt
  NEG 3/3 dual-L0; TierA 4/5 L2 (gpuweb spec)        -> hypotheses_report.txt
  L1 = 3 (deck.gl/galacean/tres); upper 17/174 9.8%  -> sensitivity_report.txt
  vscode raw WebGPU in editor/browser/gpu            -> gold_pass1_71.json
  web-llm zero navigator.gpu (EP/WASM mediated)      -> gold_pass1_71.json
  trees 182/182, 0 truncated                         -> tree_status.json / sensitivity_report.txt
  S1 flips: survives >=3 (p<0.05 through 2)          -> sensitivity_report.txt
  appendix 14 L2 repos, dual cells                   -> classifier_v2_71.json
Exit 0 iff every number is found in its artifact.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "snapshots" / "expected_output"

hy = (EXP / "hypotheses_report.txt").read_text()
se = (EXP / "sensitivity_report.txt").read_text()
gold = json.loads((ROOT / "snapshots" / "gold_pass1_71.json").read_text())
cls2 = json.loads((ROOT / "snapshots" / "classifier_v2_71.json").read_text())
ts = json.loads((ROOT / "snapshots" / "tree_status.json").read_text())

# appendix rows: repo -> expected role + dual flag from manuscript appendix A
APPENDIX = {
    "Orillusion/orillusion": ("render", True),
    "pixijs/pixijs": ("render", True),
    "playcanvas/engine": ("render", True),
    "playcanvas/supersplat": ("render", True),
    "Rezmason/matrix": ("both", False),
    "aframevr/aframe": ("render", True),
    "pascalorg/editor": ("render", True),
    "processing/p5.js": ("render", True),
    "tensorflow/tfjs": ("compute", True),
    "gpujs/gpu.js": ("compute", False),
    "voxel51/fiftyone": ("render", True),
    "microsoft/vscode": ("render", False),
    "melonjs/melonJS": ("render", True),
    "remotion-dev/remotion": ("both", True),
}

CHECKS = []
def check(label, cond):
    CHECKS.append((label, bool(cond)))


# headline + migration
check("corpus 182 = TierA 5 + TierB 174 + NEG 3", "Corpus: TierB n=174 | TierA anchors=5 | NEG=3" in hy)
check("14/174 = 8.0%", "14/174 = 8.0%" in hy)
check("Wilson95 [4.9,13.1]", "[4.9,13.1]" in hy)
check("WebGL L2 = 48 (27.6%)", "48 (27.6%)" in hy)
check("WebGL-only = 37/51 = 73%", "37/51 = 73%" in hy)
check("WebGPU 27.5% of GPU-API users", "14/51 = 27.5%" in hy)
check("WebGL retains 72.5% majority", "72.5% majority" in hy)
check("S1 7/29 = 24%", "S1_web3d_graphics: 7/29 = 24%" in hy)
check("S3 3/29 = 10%", "S3_ai_web: 3/29 = 10%" in hy)
check("S2/S4/S5/S6 1/29 = 3%", "1/29 = 3%" in hy)
check("Fisher S1-vs-rest 0.0021", "0.0021" in hy)
check("Fisher anchors-vs-TierB 0.000346", "0.000346" in hy)
check("Fisher S3-AI 0.464 NOT elevated", "0.464" in hy)
# flip robustness
check("robust to 61+ flips", "61+ flips" in hy)
check("CI crosses 50% at k=75", "k=75" in hy)
check("parity >=12 dual flips", ">=12 WebGL-only->dual" in hy)
check("parity >=23 L0->WebGPU flips", ">=23 L0->WebGPU" in hy)
check("S1 survives >=3 flips", "survives >=3 S1 flips" in se)
check("S1 p<0.05 through 2 flips crosses at 3", "crosses 0.05" in se)
# H2
check("raw-API L2 = 11", "Raw-API TierB L2: 11" in hy)
check("mediated L2 = 3", "Mediated TierB L2: 3" in hy)
check("engine-dep carriers 26", "26 TierB repos carry" in hy)
check("7 L2 carriers (2 engines + 5 app)", "7 are WebGPU L2 — 2 are the engines" in hy and "5 app-level dependents select WebGPU" in hy)
check("19 carriers stay WebGL-default", "remaining 19 ship the engine" in hy)
# H3
check("roles render 10 / compute 2 / both 2", "{'render': 10, 'both': 2, 'compute': 2}" in hy)
check("compute-only tfjs + gpu.js", "gpujs/gpu.js', 'tensorflow/tfjs" in hy)
check("dual-renderer 11/14 = 79%", "11/14 = 79%" in hy)
# H4 + calibration
check("adopters live 14/14", "14/14" in hy)
check("anchors live 5/5", "5/5" in hy)
check("TierA 4/5 L2", "TierA L2: 4/5" in hy)
check("NEG 0/3 non-L0", "NEG non-L0: 0/3" in hy)
check("gpuweb spec L0-as-adopter", "gpuweb = spec, L0-as-adopter" in hy)
check("L1 = 3 (deck.gl/galacean/tres)", "3 = ['Tresjs/tres', 'galacean/engine', 'visgl/deck.gl']" in hy)
check("L1 upper 17/174 = 9.8% CI[6.2,15.1]", "17/174 = 9.8% Wilson95[6.2,15.1]" in hy)
# gold / trees
check("gold: vscode editor/browser/gpu raw paths",
      any("editor/browser/gpu" in p for p in gold.get("microsoft/vscode", {}).get("l1_codesearch", [])))
def sig(entry):
    out = []
    for _p, info in entry.items():
        if isinstance(info, dict):
            out.extend(info.get("signals", []))
    return out
check("gold: web-llm zero navigator.gpu (EP/WASM)", "navigator.gpu" not in sig(gold.get("mlc-ai/web-llm", {})))
check("trees 182/182 ok, 0 truncated",
      sum(1 for v in ts.values() if v.startswith("ok")) == 182 and
      all("truncated=True" not in v for v in ts.values()))
# appendix: each of 14 repos L2 with matching role + dual cell
missing_appendix = []
for repo, (role, dual) in APPENDIX.items():
    r = cls2.get(repo)
    if not r or r.get("membership") != "TierB" or r.get("webgpu_level") != "L2":
        missing_appendix.append(repo)
    elif r.get("webgpu_role") != role:
        missing_appendix.append(f"{repo}:role")
    elif (r.get("webgl_level") == "L2") != dual:
        missing_appendix.append(f"{repo}:dual")
check("appendix 14 L2 rows (role + dual cells) match classifier v2", not missing_appendix,
      )
if missing_appendix:
    print("  appendix mismatches:", missing_appendix)

ok = True
print("trace_check.py — manuscript headline numbers -> committed artifacts")
print("=" * 72)
for label, cond in CHECKS:
    print(f"  [{'OK' if cond else 'MISS'}] {label}")
    ok = ok and cond
print("=" * 72)
print(f"{'PASS: 0 gaps' if ok else 'FAIL: gaps found'}")
sys.exit(0 if ok else 1)
