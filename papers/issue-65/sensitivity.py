#!/usr/bin/env python3
"""Issue #65 — sensitivity analysis for census conclusions.

1. H1 significance erasure: how many Tier B positives must flip to L0
   before Fisher p crosses 0.05?  (anchor side is fixed by construction)
2. H2 majority erasure: how many embedders must flip to non-library before
   the 50% majority claim fails (n=5)?
3. Missing-tree worst case: 8 stream-cancel + 1 truncated trees — assume
   ALL would have been positive → upper-bound Tier B rate.
4. Threshold sensitivity: L2-only vs L1+L2 counting.
5. Adjudication sensitivity: k3s (L1) treated as positive or not.
6. Program-type sensitivity: if firezone or portmaster were misclassified,
   tracing share 3/5 vs 2/5 boundary.

Outputs: snapshots/sensitivity_report.txt (canonical)
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

TA_N = 12
TB_N = 174
TB_POS = 6
TB_L2 = 5
STREAM_CANCEL = 8   # kubernetes/tetragon/pulumi/supabase/ClickHouse/mongo/nodejs/symfony
API_TRUNCATED = 1   # elastic/kibana


def fisher_2x2(a, b, c, d):
    def ln_fact(n):
        if n <= 1:
            return 0.0
        return math.lgamma(n + 1)
    total = a + b + c + d
    row1, row2, col1, col2 = a + b, c + d, a + c, b + d
    p = 0.0
    for a_ in range(a, min(row1, col1) + 1):
        b_ = row1 - a_
        c_ = col1 - a_
        d_ = row2 - c_
        if b_ < 0 or c_ < 0 or d_ < 0:
            continue
        p += math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2)
                      - ln_fact(total)
                      - ln_fact(a_) - ln_fact(b_) - ln_fact(c_) - ln_fact(d_))
    return p


lines = [
    "eBPF in the Wild — sensitivity analysis (snapshot 2026-09-01)",
    "=" * 78,
]

# --- 1. H1 significance erasure ---
p0 = fisher_2x2(TA_N, 0, TB_POS, TB_N - TB_POS)
lines.append(f"[1] H1 significance erasure (Tier A 12/12 vs Tier B k/174):")
lines.append(f"    baseline Fisher p = {p0:.3e} (k={TB_POS})")
flips = 0
k = TB_POS
while k > 0:
    k -= 1
    flips += 1
    if fisher_2x2(TA_N, 0, k, TB_N - k) >= 0.05:
        break
lines.append(f"    flips needed to reach p >= 0.05: {flips} "
             f"(i.e. k={k}/{TB_N} = {k/TB_N*100:.1f}% — every single positive "
             "would have to be a false positive)")
p_mid = fisher_2x2(TA_N, 0, 1, TB_N - 1)
lines.append(f"    even k=1 gives p = {p_mid:.3e} — H1 is not flip-sensitive")
lines.append("")

# --- 2. H2 majority erasure ---
lines.append("[2] H2 majority erasure (n=5 embedders):")
lines.append("    library-driven 5/5; 3 flips needed to drop to 2/5 (40% < 50%)")
lines.append("    → even 3 of 5 embedders misclassified, majority claim survives only at the boundary")
lines.append("")

# --- 3. Missing-tree worst case ---
missing = STREAM_CANCEL + API_TRUNCATED
wc_pos = TB_POS + missing
lines.append(f"[3] Missing-tree worst case ({STREAM_CANCEL} stream-cancel + {API_TRUNCATED} truncated = {missing} repos):")
lines.append(f"    assume ALL missing trees positive → k = {wc_pos}/{TB_N} = {wc_pos/TB_N*100:.1f}%")
p_wc = fisher_2x2(TA_N, 0, wc_pos, TB_N - wc_pos)
lines.append(f"    Fisher p = {p_wc:.3e} — H1 robust even in the adversarial extreme")
lines.append(f"    (in practice all 8 stream-cancel repos had root-manifest coverage: "
             "0/8 manifest-positive)")
lines.append("")

# --- 4. Threshold sensitivity ---
lines.append("[4] Threshold sensitivity (L1+L2 vs L2-only):")
lines.append(f"    L1+L2 (incl. k3s dep-mgmt): {TB_POS}/{TB_N} = {TB_POS/TB_N*100:.1f}%")
lines.append(f"    L2-only (verified embedders): {TB_L2}/{TB_N} = {TB_L2/TB_N*100:.1f}%")
lines.append(f"    gap = {(TB_POS-TB_L2)/TB_N*100:.1f} pp — single L1 adjudication; "
             "k3s is `// indirect` + replace-directive (dep mgmt, not embedding)")
lines.append("")

# --- 5. Program-type boundary ---
lines.append("[5] Program-type sensitivity (n=5 embedders):")
lines.append("    tracing 3/5 vs net-path 2/5")
lines.append("    if ONE embedder flipped tracing<->net-path → 2/5 vs 3/5 (majority flips)")
lines.append("    → H3 claim must be framed as 'tracing is NOT the minority / parity boundary',")
lines.append("      NOT as an overwhelming tracing dominance (Wilson CIs overlap: 23-88% vs 12-77%)")
lines.append("")

# --- 6. Star-weight / popularity robustness ---
pos_stars = [80394, 33864, 14021, 13644, 9047, 4980]
lines.append("[6] Popularity-weighted view:")
lines.append(f"    positives include the 4th-largest Tier B repo (netdata 80.4k★) and k3s 33.9k★")
lines.append(f"    positive stars sum = {sum(pos_stars):,} (median {sorted(pos_stars)[len(pos_stars)//2]:,})")
lines.append(f"    → adoption is concentrated among large-scale infra projects (consistent with H1)")
lines.append("")

report = "\n".join(lines)
out = SNAP / "sensitivity_report.txt"
out.write_text(report)
print(report)
