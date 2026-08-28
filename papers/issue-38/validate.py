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
    # Wilson 95% CIs (reviewer-requested; exact binomial for the observed counts)
    def wilson(x, nn):
        if nn == 0:
            return (0.0, 0.0)
        z = 1.959963985
        phat = x / nn
        denom = 1 + z * z / nn
        center = (phat + z * z / (2 * nn)) / denom
        hw = z * ((phat * (1 - phat) / nn + z * z / (4 * nn * nn)) ** 0.5) / denom
        lo = max(0.0, center - hw)
        hi = min(1.0, center + hw)
        return (lo, hi)
    p_lo, p_hi = wilson(tp, tp + fp)
    r_lo, r_hi = wilson(tp, tp + fn)
    a_lo, a_hi = wilson(tp + tn, tp + fp + tn + fn)
    print(f"wilson95 precision=[{p_lo:.3f},{p_hi:.3f}] recall=[{r_lo:.3f},{r_hi:.3f}] "
          f"accuracy=[{a_lo:.3f},{a_hi:.3f}]")

if __name__ == "__main__":
    main()
