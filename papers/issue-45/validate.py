#!/usr/bin/env python3
"""Validate extracted pipeline signals against hand-verified ground truth.

Ground truth: validation_sample.tsv (56 cells = 14 repos x 4 signals).
Pipeline predictions come from snapshots/*_index.json:
  S1 a11y_test_dep -> idx.a11y_test_deps non-empty (a11y-specific, library-only)
  S2 aria_presence -> idx.aria_content.aria_density_per_file > 0
  S3 role_presence -> idx.aria_content.roles non-empty
  S4 a11y_first    -> corpus.json a11y_first flag (positioning)

Outputs per-signal and overall TP/FP/TN/FN, precision, recall, accuracy.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

SIGNALS = ["S1", "S2", "S3", "S4"]
GT = {}

def load_gt():
    with open(ROOT / "validation_sample.tsv") as f:
        lines = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        for row in csv.DictReader(lines, delimiter="\t"):
            key = (row["repo"], row["signal"])
            GT[key] = int(row["gt"])

def load_corpus():
    c = json.load(open(ROOT / "corpus.json"))
    return {p["repo"]: p for p in c["tiers"]["projects"]}

def predict(repo, signal, corpus):
    idx = json.load(open(SNAP / f"{repo.replace('/', '__')}_index.json"))
    if signal == "S1":
        return 1 if idx.get("a11y_test_deps") else 0
    if signal == "S2":
        ac = idx.get("aria_content", {})
        return 1 if ac.get("aria_density_per_file", 0) > 0 else 0
    if signal == "S3":
        ac = idx.get("aria_content", {})
        return 1 if ac.get("roles") else 0
    if signal == "S4":
        return 1 if corpus[repo].get("a11y_first") else 0
    raise ValueError(signal)

def main():
    load_gt()
    corpus = load_corpus()
    repos = sorted({r for r, _ in GT})
    missing = sorted({r for r, _ in GT if r not in corpus})
    if missing:
        print(f"FATAL: repos missing from corpus: {missing}")
        sys.exit(1)
    cells = []
    for repo in repos:
        for s in SIGNALS:
            p = predict(repo, s, corpus)
            g = GT[(repo, s)]
            cells.append((repo, s, p, g))
    # per-signal metrics
    print(f"{'signal':7s} {'TP':>3s} {'FP':>3s} {'TN':>3s} {'FN':>3s} {'precision':>9s} {'recall':>6s} {'accuracy':>8s}")
    overall = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for s in SIGNALS:
        sc = [c for c in cells if c[1] == s]
        tp = sum(1 for _, _, p, g in sc if p == 1 and g == 1)
        fp = sum(1 for _, _, p, g in sc if p == 1 and g == 0)
        tn = sum(1 for _, _, p, g in sc if p == 0 and g == 0)
        fn = sum(1 for _, _, p, g in sc if p == 0 and g == 1)
        for k, v in (("TP", tp), ("FP", fp), ("TN", tn), ("FN", fn)):
            overall[k] += v
        prec = tp / (tp + fp) if tp + fp else 1.0
        rec = tp / (tp + fn) if tp + fn else 1.0
        acc = (tp + tn) / (tp + fp + tn + fn)
        print(f"{s:7s} {tp:3d} {fp:3d} {tn:3d} {fn:3d} {prec:9.3f} {rec:6.3f} {acc:8.3f}")
    tp, fp, tn, fn = overall["TP"], overall["FP"], overall["TN"], overall["FN"]
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 1.0
    acc = (tp + tn) / (tp + fp + tn + fn)
    print("-" * 60)
    print(f"{'ALL':7s} {tp:3d} {fp:3d} {tn:3d} {fn:3d} {prec:9.3f} {rec:6.3f} {acc:8.3f}")
    print(f"\ncells={tp+fp+tn+fn} (14 repos x 4 signals)")
    # list any mismatches explicitly
    bad = [c for c in cells if c[2] != c[3]]
    if bad:
        print("\nMISMATCHES (pipeline prediction != ground truth):")
        for repo, s, p, g in bad:
            print(f"  {repo:32s} {s}: predicted={p} gt={g}")
    else:
        print("\nNo mismatches: pipeline extraction matches hand-verified ground truth.")

if __name__ == "__main__":
    main()
