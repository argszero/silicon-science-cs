#!/usr/bin/env python3
"""Issue #41 — embedding-signal validation: hand-verified cells vs extractor.

Ground truth in validation_sample.tsv (cell-level: consumer x stack x gt,
hand-verified via manifest declarations, vendored dirs, native QUIC paths).
Predictions from snapshots/*_index.json embeddings. Recomputes precision
from committed data only.
"""
import json, glob, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

def main():
    rows = []
    for ix in sorted(glob.glob(str(SNAP / "*_index.json"))):
        d = json.load(open(ix))
        if d["tier"] == "consumer":
            rows.append(d)
    by_repo = {r["repo"]: r for r in rows}
    tp = fp = tn = fn = 0
    n = 0
    for line in open(ROOT / "validation_sample.tsv"):
        line = line.strip()
        if not line or line.startswith("consumer"):
            continue
        consumer, stack, path, gt = line.split("\t")
        n += 1
        r = by_repo.get(consumer)
        if r is None:
            print(f"WARN: {consumer} not in indexes", file=sys.stderr)
            continue
        emb = r["embeddings"]
        if stack == "none":
            predicted = not emb   # self-implemented: no external stack embedded
        else:
            predicted = emb.get(stack, 0) > 0
        ground = gt == "P"
        if predicted and ground: tp += 1
        elif predicted and not ground: fp += 1
        elif not predicted and ground: fn += 1
        else: tn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    acc = (tp + tn) / n if n else 0.0
    print(f"embedding-cell validation: {n} hand-verified cells")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"precision={prec:.3f} recall={rec:.3f} accuracy={acc:.3f}")

if __name__ == "__main__":
    main()
