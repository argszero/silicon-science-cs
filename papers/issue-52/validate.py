#!/usr/bin/env python3
"""Issue #52 — validation: classifier predictions vs hand-annotated ground truth.

Reads validation_sample.tsv (human labels, hand-verified from tree inventories)
+ snapshots/component_classes.json (predictions). Reports per-class precision/
recall and overall accuracy, with boundary-cell breakdown.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASSES = json.load(open(ROOT / "snapshots" / "component_classes.json"))

rows = list(csv.DictReader(open(ROOT / "validation_sample.tsv"), delimiter="\t"))

def pred_for(repo, comp):
    d = CLASSES[repo]["component_detail"]
    key = comp if comp != "(root)" else ""
    return d.get(key, {}).get("class")

results = []
for r in rows:
    human = r["human"]
    pred = pred_for(r["repo"], r["component"])
    ok = pred == human
    results.append({**r, "pred": pred, "ok": ok})
    if not ok:
        print(f"MISMATCH: {r['repo']} {r['component']} pred={pred} human={human}")

n = len(results)
n_ok = sum(1 for r in results if r["ok"])
print(f"\nvalidation cells: {n}  accuracy {n_ok}/{n} = {n_ok/n:.3f}")

# per-class
classes = ["RUST", "C", "CPP", "MIXED"]
per_class = {}
for c in classes:
    pred_c = [r for r in results if r["pred"] == c]
    hum_c = [r for r in results if r["human"] == c]
    tp = sum(1 for r in results if r["pred"] == c and r["human"] == c)
    prec = tp / len(pred_c) if pred_c else 1.0
    rec = tp / len(hum_c) if hum_c else 1.0
    per_class[c] = {"prec": round(prec, 3), "rec": round(rec, 3), "tp": tp,
                    "n_pred": len(pred_c), "n_hum": len(hum_c)}
    print(f"  {c:6s} prec {prec:.3f} ({tp}/{len(pred_c)})  rec {rec:.3f} ({tp}/{len(hum_c)})")

boundary = [r for r in results if r["boundary"] == "1"]
b_ok = sum(1 for r in boundary if r["ok"])
print(f"\nboundary cells: {len(boundary)}  accuracy {b_ok}/{len(boundary)} = {b_ok/len(boundary):.3f}")
clear = [r for r in results if r["boundary"] == "0"]
c_ok = sum(1 for r in clear if r["ok"])
print(f"clear cells:    {len(clear)}  accuracy {c_ok}/{len(clear)} = {c_ok/len(clear):.3f}")

# save
out = {**{"n": n, "accuracy": n_ok / n, "boundary_acc": b_ok / len(boundary),
          "clear_acc": c_ok / len(clear), "per_class": per_class}, "cells": results}
json.dump(out, open(ROOT / "snapshots" / "validation_result.json", "w"), indent=2)
print("wrote validation_result.json")
