#!/usr/bin/env python3
"""Issue #48 — validate package classification against hand-verified ground truth.

Ground truth: validation_sample.tsv (22 cells: repo, package path, hand-verified
class ROS1/ROS2/dual/none). Predictions: snapshots/package_classes.json (from
ros_extract.py classify). Reports per-class precision/recall + overall accuracy.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASSES = json.load(open(ROOT / "snapshots" / "package_classes.json"))

def predict(repo, pkg_path):
    for r in CLASSES.get(repo, []):
        if r["path"] == pkg_path:
            return r["class"]
    return "MISSING"

def main():
    cells = []
    with open(ROOT / "validation_sample.tsv") as f:
        for row in csv.DictReader([ln for ln in f if not ln.startswith("#") and ln.strip()], delimiter="\t"):
            cells.append((row["repo"], row["package"], row["gt"]))
    print(f"validation cells: {len(cells)}")
    print(f"{'repo':44s} {'package':50s} {'pred':>5s} {'gt':>5s} {'ok':>3s}")
    correct = 0
    cls_gt = {c: 0 for c in ("ROS1", "ROS2", "dual", "none")}
    cls_tp = {c: 0 for c in ("ROS1", "ROS2", "dual", "none")}
    cls_pred = {c: 0 for c in ("ROS1", "ROS2", "dual", "none")}
    for repo, pkg, gt in cells:
        pred = predict(repo, pkg)
        cls_gt[gt] += 1
        cls_pred[pred] += 1
        ok = pred == gt
        if ok:
            correct += 1
            cls_tp[gt] += 1
        print(f"{repo:44s} {pkg:50s} {pred:>5s} {gt:>5s} {'✓' if ok else '✗'}")
    print("-" * 110)
    print(f"overall accuracy: {correct}/{len(cells)} = {correct/len(cells):.3f}")
    for c in ("ROS1", "ROS2", "dual", "none"):
        prec = cls_tp[c] / cls_pred[c] if cls_pred[c] else 1.0
        rec = cls_tp[c] / cls_gt[c] if cls_gt[c] else 1.0
        print(f"  {c:5s} precision {prec:.3f} ({cls_tp[c]}/{cls_pred[c]})  recall {rec:.3f} ({cls_tp[c]}/{cls_gt[c]})")
    if correct != len(cells):
        print("MISMATCHES PRESENT — investigate before freezing")
        sys.exit(1)

if __name__ == "__main__":
    main()
