#!/usr/bin/env python3
"""Issue #38 — extraction validation: hand-labeled sample vs extractor predictions.

Ground truth lives in validation_sample.tsv (gt_class, hand-verified per rules
documented in the manuscript: kernel selftests progs/*.c are BPF objects by the
kernel build system; other PROG rows require SEC/entry markers or .bpf.c/_kern.c
naming; NON rows were individually verified as loaders/headers/harnesses).

Predictions are the extractor's is_bpf_source flag in snapshots/*_index.json.
The confusion matrix and precision/recall/accuracy are recomputed deterministically
from these two committed inputs — no network, no cached raw sources needed.
"""
import json, glob, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

def load():
    files = []
    for ix in sorted(glob.glob(str(SNAP / "*_index.json"))):
        d = json.load(open(ix))
        for r in d["files"]:
            files.append((d["repo"], r))
    by_path = {r["path"]: r for _, r in files}
    return by_path

def main():
    by_path = load()
    tp = fp = tn = fn = 0
    n = 0
    for line in open(ROOT / "validation_sample.tsv"):
        line = line.strip()
        if not line or line.startswith("class"):
            continue
        cls, repo, path, gt_class = line.split("\t")
        r = by_path.get(path)
        if r is None:
            print(f"WARN: {path} not in indexes", file=sys.stderr)
            continue
        predicted = r["is_bpf_source"]
        ground = gt_class == "PROG"
        n += 1
        if predicted and ground: tp += 1
        elif predicted and not ground: fp += 1
        elif not predicted and ground: fn += 1
        else: tn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    acc = (tp + tn) / (tp + fp + tn + fn) if n else 0.0
    print(f"validation sample: {n} files")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"precision={prec:.3f} recall={rec:.3f} accuracy={acc:.3f}")

if __name__ == "__main__":
    main()
