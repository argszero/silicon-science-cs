#!/usr/bin/env python3
"""Issue #57 — validate.py: cross-check hypotheses numbers against ground truth
from an independent re-implementation (mirrors #52's validation discipline).

Re-computes the census counts + point estimates directly from the committed
ground-truth TSVs and compares them with hypotheses_report.txt. Exit 0 iff
every reported number matches within floating tolerance.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = SNAP / "annotation"


def load_axis(path, axis):
    rows = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#") or line.startswith("repo\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        if parts[1] == axis:
            rows[parts[0]] = parts[2]
    return rows


def main():
    tierb = json_load = __import__("json").load
    tb = sorted({r.get("repo") or r.get("full_name", "") for r in tierb(open(SNAP / "tierb_candidates.json"))})
    n = len(tb)

    gt_i = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv", "ground_truth_r106.tsv"):
        gt_i.update(load_axis(OUT / f, "i"))
    gt_ii = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv", "ground_truth_r107.tsv"):
        gt_ii.update(load_axis(OUT / f, "ii"))
    gt_iii = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv"):
        gt_iii.update(load_axis(OUT / f, "iii"))

    c_i = Counter(gt_i[r] for r in tb)
    single, multi, unk = c_i["SINGLE"], c_i["MULTI"], c_i["UNKNOWN"]
    decided = single + multi
    p1 = single / decided

    mas = [r for r in tb if gt_i.get(r) == "MULTI"]
    topo = Counter(gt_ii.get(r, "MISSING") for r in mas)
    ow = topo.get("ORCH-WORKER", 0)
    p2 = ow / len(mas)

    n_iii = sum(1 for r in tb if r in gt_iii)
    judge = sum(1 for r in tb if gt_iii.get(r) == "JUDGE")
    p3 = judge / n

    report = (SNAP / "hypotheses_report.txt").read_text()

    checks = [
        ("H1 SINGLE count", str(single), re.search(r"SINGLE=(\d+)", report).group(1)),
        ("H1 point %", f"{100*p1:.1f}", re.search(r"point estimate: (\d+\.\d)%", report).group(1)),
        ("H2 ORCH-WORKER count", str(ow), re.search(r"ORCH-WORKER (\d+) / TEAM", report).group(1)),
        ("H2 point %", f"{100*p2:.1f}", re.search(r"ORCH-WORKER (\d+\.\d)%", report).group(1)),
        ("H3 JUDGE count", str(judge), re.search(r"JUDGE=(\d+)", report).group(1)),
        ("H3 point %", f"{100*p3:.1f}", re.search(r"JUDGE (\d+\.\d)%", report).group(1)),
    ]
    ok = True
    print("validate.py — hypotheses cross-check")
    for name, got, want in checks:
        match = got == want
        ok &= match
        print(f"  [{'OK' if match else 'FAIL'}] {name}: got={got} report={want}")
    print(f"\n{'PASS' if ok else 'FAIL'}: {sum(1 for c in checks if c[1]==c[2])}/{len(checks)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
