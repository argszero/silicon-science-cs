#!/usr/bin/env python3
"""Issue #63 — trace_check.py: every manuscript headline number must trace to a
committed artifact (snapshots/hypotheses_report.txt, sensitivity_report.txt,
h4_longitudinal.md, ground_truth_r124.md). Exit 0 iff zero gaps.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
MS = (ROOT / "manuscript.md").read_text()
HYP = (SNAP / "hypotheses_report.txt").read_text()
SEN = (SNAP / "sensitivity_report.txt").read_text()
H4 = (SNAP / "h4_longitudinal.md").read_text()
GT = (SNAP / "ground_truth_r124.md").read_text()

# (name, manuscript needle, artifact needle, artifact text)
CHECKS = [
    ("corpus n=192", "corpus of 192", "corpus: 192", HYP),
    ("Tier A 16 / Tier B 174", "Tier A = 16", "Tier A 16 / Tier B 174", HYP),
    ("Tier B n=174", "Tier B total **174**", "Tier B 174", HYP),
    ("L0/L1/L2 162/3/9", "L0 162 / L1 3 / L2 9", "L0 162 / L1 3 / L2 9", HYP),
    ("positive 12/174 6.9%", "12/174 = 6.9%", "12/174 = 6.9%", HYP),
    ("H1 Raft 8/12 66.7%", "8/12 = 66.7%", "Raft share = 8/12 = 66.7%", HYP),
    ("H1 CI [39.1,86.2]", "[39.1%, 86.2%]", "[39.1%, 86.2%]", HYP),
    ("H1 flips 2", "2 flips", "flips to lose majority (50%): 2", HYP),
    ("H2 lib 9/12 75.0%", "9/12 = 75.0%", "lib share = 9/12 = 75.0%", HYP),
    ("H2 CI [46.8,91.1]", "[46.8%, 91.1%]", "[46.8%, 91.1%]", HYP),
    ("H2 flips 3", "3 flips", "flips to drop below 50%: 3", HYP),
    ("H3 anchors 16/16 100%", "16/16 = 100%", "16/16 = 100.0%", HYP),
    ("H3 Fisher 4.2e-16", "p = 4.2e-16", "4.225e-16", HYP),
    ("H3 Go 5/12 41.7%", "5/12 = 41.7%", "Go share among Tier B adopters: 5/12 = 41.7%", HYP),
    ("NEG controls", "bitcoin/ethereum", "bitcoin/go-ethereum -> L0", HYP),
    ("positives list", "ClickHouse", "ClickHouse/ClickHouse", HYP),
    ("positives list", "typesense", "typesense/typesense", HYP),
    ("positives list", "rocketmq", "apache/rocketmq", HYP),
    ("positives list", "emqx", "emqx/emqx", HYP),
    ("positives list", "qdrant", "qdrant/qdrant", HYP),
    ("positives list", "dgraph", "dgraph-io/dgraph", HYP),
    ("positives list", "cubefs", "cubefs/cubefs", HYP),
    ("positives list", "ceph", "ceph/ceph", HYP),
    ("positives list", "cosmos-sdk", "cosmos/cosmos-sdk", HYP),
    ("positives list", "tendermint", "tendermint/tendermint", HYP),
    ("positives list", "snarkOS", "ProvableHQ/snarkOS", HYP),
    ("S1 indirect-off 8.6%/86.7%", "15/174 = 8.6%", "15/174 = 8.6%", SEN),
    ("S1 H2 86.7%", "H2 86.7%", "H2 lib 13/15 = 86.7%", SEN),
    ("S2 emqx 83.3%", "H2 83.3%", "H2 lib 10/12 = 83.3%", SEN),
    ("S3 H1 50.0% boundary", "50.0%", "Raft 6/12 = 50.0%", SEN),
    ("S4 H2 50.0% boundary", "50.0%", "lib 6/12 = 50.0%", SEN),
    ("S5 H1 90% CI", "[43.1%, 84.1%]", "90% CI [43.1%, 84.1%]", SEN),
    ("S5 H2 90% CI", "[51.3%, 89.5%]", "90% CI [51.3%, 89.5%]", SEN),
    ("H4 cohort etcd", "etcd, Consul, CockroachDB, TiKV", "etcd", H4),
    ("H4 cohort Consul", "etcd, Consul, CockroachDB, TiKV", "Consul", H4),
    ("H4 cohort CockroachDB", "etcd, Consul, CockroachDB, TiKV", "CockroachDB", H4),
    ("H4 cohort TiKV", "etcd, Consul, CockroachDB, TiKV", "TiKV", H4),
    ("H4 LogCabin dormant", "LogCabin", "LogCabin", H4),
    ("H4 none abandoned", "None of the surviving", "NONE abandoned", H4),
    ("gold standard 12 positives", "12 consensus-using", "12", GT),
]

gaps = 0
print("trace_check.py — manuscript → committed artifacts (issue #63)")
for name, ms_needle, art_needle, art in CHECKS:
    ms_ok = ms_needle.lower() in MS.lower()
    art_ok = art_needle.lower() in art.lower()
    ok = ms_ok and art_ok
    if not ok:
        gaps += 1
    print(f"  [{'OK' if ok else 'GAP'}] {name}: manuscript={ms_ok} artifact={art_ok}")

print(f"\n{'PASS' if gaps == 0 else 'FAIL'}: {len(CHECKS)} traces, {gaps} gaps")
sys.exit(0 if gaps == 0 else 1)
