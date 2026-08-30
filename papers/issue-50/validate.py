#!/usr/bin/env python3
"""Issue #50 — validate the extractor against hand-annotated ground truth.

Reads validation_sample.tsv (model, signal, pred, gated, evidence, human,
notes) and computes per-signal and overall precision / recall of the 8-signal
extractor against the author's hand labels (n=16 models x 8 signals = 128
cells). Deterministic, offline.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TSV = ROOT / "validation_sample.tsv"
SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

def main():
    rows = []
    for line in TSV.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("model\t"):
            continue
        parts = line.split("\t")
        rows.append(parts)
    n = len(rows)
    assert n == 128, f"expected 128 cells, got {n}"
    by_sig = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    mismatches = []
    for mid, sig, pred_s, gated, ev, human_s, *note in rows:
        pred = int(pred_s)
        human = int(human_s)
        c = by_sig[sig]
        if human == 1 and pred == 1: c["tp"] += 1
        elif human == 0 and pred == 1: c["fp"] += 1
        elif human == 1 and pred == 0: c["fn"] += 1
        else: c["tn"] += 1
        if pred != human:
            mismatches.append((mid, sig, pred, human, ev[:90]))
    print(f"validation cells: {n}  (16 models x 8 signals)")
    print(f"overall accuracy: {(n - len(mismatches)) / n * 100:.1f}%  "
          f"({n - len(mismatches)}/{n})")
    print(f"overall precision: TP/(TP+FP) and recall: TP/(TP+FN) "
          f"over positive cells")
    tp = sum(c["tp"] for c in by_sig.values())
    fp = sum(c["fp"] for c in by_sig.values())
    fn = sum(c["fn"] for c in by_sig.values())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"  precision {prec:.3f} ({tp}/{tp+fp})  recall {rec:.3f} ({tp}/{tp+fn})")
    print()
    print(f"{'signal':16s} {'TP':>3s} {'FP':>3s} {'FN':>3s} {'TN':>3s}  {'prec':>5s} {'rec':>5s}")
    for sig in SIGS:
        c = by_sig[sig]
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else float("nan")
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else float("nan")
        print(f"{sig:16s} {c['tp']:3d} {c['fp']:3d} {c['fn']:3d} {c['tn']:3d}  "
              f"{p:5.2f} {r:5.2f}")
    if mismatches:
        print()
        print("mismatches (pred != human):")
        for mid, sig, pred, human, ev in mismatches:
            print(f"  {mid} [{sig}] pred={pred} human={human} | {ev}")
    else:
        print()
        print("no mismatches — extractor agrees with hand labels on all 128 cells")

if __name__ == "__main__":
    main()
