#!/usr/bin/env python3
"""Issue #43 — validate automatic eval-practice extraction against hand-verified ground truth.

Reads validation_sample.tsv (64 cells = 16 repos × 4 signals: harness/judge/benchmark/validation)
and prints the confusion matrix. Predictions ('pred') come from the automatic extractor
(snapshots/*_index.json); ground truth ('gt') is hand-verified (mechanisms.json).

Exit 0 always (metrics are informational; byte-identical reproduction is checked by reproduce.sh).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    rows = list(csv.reader(open(ROOT / "validation_sample.tsv"), delimiter="\t"))[1:]
    tp = fp = tn = fn = 0
    for repo, sig, pred, gt in rows:
        if gt == "P" and pred == "P":
            tp += 1
        elif gt == "A" and pred == "P":
            fp += 1
        elif gt == "A" and pred == "A":
            tn += 1
        else:
            fn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    acc = (tp + tn) / len(rows)
    print(f"eval-practice cell validation: {len(rows)} hand-verified cells")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"precision={prec:.3f} recall={rec:.3f} accuracy={acc:.3f}")
    print("note: 2 FP are the validation signal over-triggering on framework 'ground truth'")
    print("API parameters (langchain/haystack evaluator components); H3 rests on the")
    print("hand-verified mechanisms.json classification (validation 0/16).")


if __name__ == "__main__":
    main()
