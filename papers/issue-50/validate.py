#!/usr/bin/env python3
"""Issue #50 — validate the extractor against hand-annotated ground truth.

Reads validation_sample.tsv (16 boundary models, 128 cells) AND
validation_complement.tsv (8 download-quantile-spanning models, 64 cells) and
computes per-signal and overall precision / recall of the 8-signal extractor
against the author's hand labels (n=192 cells total). Deterministic, offline.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TSV = ROOT / "validation_sample.tsv"
COMP = ROOT / "validation_complement.tsv"
SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

def read_rows(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("model\t"):
            continue
        rows.append(line.split("\t"))
    return rows

def tally(rows):
    per = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    mism = []
    n = 0
    for parts in rows:
        mid, sig, pred_s, gated, ev, human_s = parts[:6]
        pred, human = int(pred_s), int(human_s)
        c = per[sig]
        if human == 1 and pred == 1: c["tp"] += 1
        elif human == 0 and pred == 1: c["fp"] += 1
        elif human == 1 and pred == 0: c["fn"] += 1
        else: c["tn"] += 1
        n += 1
        if pred != human:
            mism.append((mid, sig, pred, human, ev[:80]))
    return per, mism, n

def report(per, mism, n, label, tp, fp, fn):
    acc = (n - fp - fn) / n
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"== {label}: {n} cells  accuracy {acc*100:.1f}% ({n-fp-fn}/{n})  "
          f"precision {prec:.3f} ({tp}/{tp+fp})  recall {rec:.3f} ({tp}/{tp+fn})")
    print(f"   {'signal':16s} {'TP':>3s} {'FP':>3s} {'FN':>3s} {'TN':>3s}  {'prec':>5s} {'rec':>5s}")
    for sig in SIGS:
        c = per[sig]
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else float("nan")
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else float("nan")
        print(f"   {sig:16s} {c['tp']:3d} {c['fp']:3d} {c['fn']:3d} {c['tn']:3d}  {p:5.2f} {r:5.2f}")
    return mism

def main():
    sample_rows = read_rows(TSV)
    comp_rows = read_rows(COMP)
    assert len(sample_rows) == 128, f"sample expected 128 cells, got {len(sample_rows)}"
    assert len(comp_rows) == 64, f"complement expected 64 cells, got {len(comp_rows)}"

    per_s, mism_s, n_s = tally(sample_rows)
    per_c, mism_c, n_c = tally(comp_rows)
    all_rows = sample_rows + comp_rows
    per_a, mism_a, n_a = tally(all_rows)

    tp_s = sum(c["tp"] for c in per_s.values()); fp_s = sum(c["fp"] for c in per_s.values()); fn_s = sum(c["fn"] for c in per_s.values())
    tp_c = sum(c["tp"] for c in per_c.values()); fp_c = sum(c["fp"] for c in per_c.values()); fn_c = sum(c["fn"] for c in per_c.values())
    tp_a = sum(c["tp"] for c in per_a.values()); fp_a = sum(c["fp"] for c in per_a.values()); fn_a = sum(c["fn"] for c in per_a.values())

    report(per_s, mism_s, n_s, "BOUNDARY SAMPLE (16 models x 8 signals, extreme morphologies)", tp_s, fp_s, fn_s)
    print()
    report(per_c, mism_c, n_c, "COMPLEMENT (8 models x 8 signals, download-quantile-spanning)", tp_c, fp_c, fn_c)
    print()
    report(per_a, mism_a, n_a, "COMBINED (192 cells)", tp_a, fp_a, fn_a)

    if mism_a:
        print()
        print("mismatches (pred != human):")
        for mid, sig, pred, human, ev in mism_a:
            print(f"  {mid} [{sig}] pred={pred} human={human} | {ev}")
    else:
        print()
        print("no mismatches in any set")

if __name__ == "__main__":
    main()

