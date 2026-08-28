#!/usr/bin/env python3
"""Issue #36 — offline aggregation: channels -> canonical output.

Reads data_snapshot_c236/*.json (per-instance C1a/C1b/C2/C3 records, fetch-pinned)
and emits expected_output/discovery_results.txt (byte-identical contract).

Modes:
  offline : aggregate snapshots -> expected_output/discovery_results.txt
"""
import json, glob, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data_snapshot_c236"
OUT = ROOT / "expected_output"

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))

def main():
    recs = [json.load(open(f)) for f in sorted(glob.glob(str(SNAP / "*.json")))]
    n = len(recs)
    out = []
    out.append("SWE-BENCH VERIFIED CONTAMINATION CHANNELS — issue #36 (canonical, offline)")
    out.append(f"instances: {n}/500 (SWE-bench_Verified snapshot 2026-08-28, "
               f"GitHub mirror OpenAgentsInc/swe-bench-verified)")
    out.append("")
    def rate(pred):
        return sum(1 for r in recs if pred(r))
    # ---- headline channel rates ----
    out.append("per-channel contamination rates (Wilson 95% CI):")
    channels = [
        ("C1a issue publicly available", lambda r: r.get("c1a_issue_available")),
        ("C1b issue-text verbatim (jac>=0.8)", lambda r: r.get("c1b_hit")),
        ("C2 test file present at base_commit", lambda r: r.get("c2_present_at_base") is True),
        ("C3 fix discoverable via issue commit search", lambda r: r.get("c3_hit")),
    ]
    for label, pred in channels:
        k = rate(pred)
        lo, hi = wilson_ci(k, n)
        out.append(f"  {label:48s} {k}/{n} ({k/n:.1%}, Wilson95 {lo:.1%}-{hi:.1%})")
    out.append("")
    # ---- C1b Jaccard distribution ----
    jac = sorted(r["c1b_jaccard"] for r in recs)
    med = jac[n // 2]; p90 = jac[int(n * 0.9)]; mx = jac[-1]
    out.append(f"C1b Jaccard distribution: median={med:.3f} p90={p90:.3f} max={mx:.3f}")
    out.append("")
    # ---- C2 nuance: test file pre-exists (file-level exposure) ----
    out.append("C2 semantics: test_patch primary file path exists in tree at "
               "base_commit (file-level exposure; new test assertions arrive with the fix).")
    out.append("")
    # ---- per-repo stratification ----
    out.append("per-repo channel rates:")
    byrepo = {}
    for r in recs:
        byrepo.setdefault(r["repo"], []).append(r)
    for repo in sorted(byrepo):
        rs = byrepo[repo]
        m = len(rs)
        c1b = sum(1 for r in rs if r["c1b_hit"])
        c2 = sum(1 for r in rs if r.get("c2_present_at_base") is True)
        c3 = sum(1 for r in rs if r["c3_hit"])
        out.append(f"  {repo:28s} n={m:3d} c1b={c1b:3d} c2={c2:3d} c3={c3:3d}")
    out.append("")
    # ---- issue-year stratification (C1a exposure timeline) ----
    out.append("issue-year distribution (C1a exposure timeline):")
    years = {}
    for r in recs:
        d = (r.get("c1a_issue_created_at") or "")[:4]
        years[d] = years.get(d, 0) + 1
    for y in sorted(years):
        out.append(f"  {y}: {years[y]}")
    out.append("")
    out.append("canonical-run key: every number derives from data_snapshot_c236/ "
               "via deterministic fetch + offline aggregation.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "discovery_results.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))

if __name__ == "__main__":
    main()
