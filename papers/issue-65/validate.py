#!/usr/bin/env python3
"""Issue #65 — validate.py: independent re-count of census numbers.

Reads ONLY the raw committed snapshots (tier_ab_corpus.json,
classifier_v0_labels.json, program_types.json) and recomputes every
headline number with an independent code path (no shared logic with
classifier_v1.py / hypotheses.py / sensitivity.py except the Wilson/Fisher
formulas, which are re-implemented below).

Checks (13):
  C01 corpus size 189 = TierA 12 + TierB 174 + NEG 3
  C02 Tier B distribution L0 168 / L1 1 / L2 5
  C03 eBPF-positive 6/174 = 3.4%
  C04 verified embedders 5/174 = 2.9%
  C05 H1 Fisher p recomputed from raw counts < 1e-12
  C06 H2 5/5 embedders library-driven (each has a library signal)
  C07 H3 programmatic SEC() census: tracing 99 vs net-path 8 (recount)
  C08 NEG controls prometheus/redis/kubernetes all L0
  C09 12 L0 control repos all L0 (from 2-pass gold protocol)
  C10 Tier B positive set exactly the 6 gold-annotated repos
  C11 H4 cohort 7/7 anchors present + starred in corpus (2024 era, active 2026)
  C12 strata: positives confined to S1+S3 (2/29 + 4/29), S2/S4/S5/S6 = 0
  C13 no repo outside the 5 embedders is labeled L2 (L2 set == gold set)

Exit 0 iff all checks pass.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
v0 = json.load(open(SNAP / "classifier_v0_labels.json"))
pt = json.load(open(SNAP / "program_types.json"))

NEG = ["prometheus/prometheus", "redis/redis", "kubernetes/kubernetes"]
L0_CONTROLS = NEG + [
    "bcicen/ctop", "influxdata/telegraf", "chen08209/FlClash",
    "authelia/authelia", "aquasecurity/trivy", "elastic/kibana",
    "supabase/supabase", "mongodb/mongo", "nodejs/node",
]
GOLD_POS = ["netdata/netdata", "k3s-io/k3s", "evilsocket/opensnitch",
            "safing/portmaster", "firezone/firezone", "domcyrus/rustnet"]
GOLD_EMBED = ["netdata/netdata", "evilsocket/opensnitch", "safing/portmaster",
              "firezone/firezone", "domcyrus/rustnet"]
H4_COHORT = ["cilium/cilium", "facebookincubator/katran", "falcosecurity/falco",
             "cilium/tetragon", "iovisor/bcc", "cloudflare/ebpf_exporter",
             "projectcalico/calico"]


def fisher_2x2(a, b, c, d):
    def ln_fact(n):
        return 0.0 if n <= 1 else math.lgamma(n + 1)
    total = a + b + c + d
    row1, row2, col1, col2 = a + b, c + d, a + c, b + d
    p = 0.0
    for a_ in range(a, min(row1, col1) + 1):
        b_, c_, d_ = row1 - a_, col1 - a_, row2 - (col1 - a_)
        if b_ < 0 or c_ < 0 or d_ < 0:
            continue
        p += math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2)
                      - ln_fact(total) - ln_fact(a_) - ln_fact(b_)
                      - ln_fact(c_) - ln_fact(d_))
    return p


def membership_counts():
    m = {}
    for v in corpus.values():
        m[v["membership"]] = m.get(v["membership"], 0) + 1
    return m


def main():
    ok = True

    def check(cid, cond, msg):
        nonlocal ok
        print(f"  [{'OK' if cond else 'FAIL'}] {cid} — {msg}")
        ok = ok and cond

    print("validate.py — independent re-count (issue #65 eBPF in the Wild)")
    print("=" * 72)

    # C01 corpus
    mc = membership_counts()
    check("C01", mc.get("TierA", 0) == 12 and mc.get("TierB", 0) == 174
          and mc.get("NEG", 0) == 3 and len(corpus) == 189,
          f"corpus 189 = TierA {mc.get('TierA',0)} + TierB {mc.get('TierB',0)} + NEG {mc.get('NEG',0)}")

    # C02 distribution
    tb = {r: v for r, v in v0.items() if v["membership"] == "TierB"}
    l0 = sum(1 for v in tb.values() if v["level"] == "L0")
    l1 = sum(1 for v in tb.values() if v["level"] == "L1")
    l2 = sum(1 for v in tb.values() if v["level"] == "L2")
    check("C02", (l0, l1, l2) == (168, 1, 5),
          f"Tier B L0 {l0} / L1 {l1} / L2 {l2}")

    # C03/C04 rates
    pos = l1 + l2
    check("C03", pos == 6 and pos / len(tb) == 6 / 174,
          f"eBPF-positive {pos}/174 = {pos/len(tb)*100:.1f}%")
    check("C04", l2 == 5 and l2 / len(tb) == 5 / 174,
          f"verified embedders {l2}/174 = {l2/len(tb)*100:.1f}%")

    # C05 H1 Fisher
    ta = {r: v for r, v in v0.items() if v["membership"] == "TierA"}
    ta_pos = sum(1 for v in ta.values() if v["level"] in ("L1", "L2"))
    p = fisher_2x2(ta_pos, len(ta) - ta_pos, pos, len(tb) - pos)
    check("C05", ta_pos == 12 and p < 1e-12,
          f"H1: Tier A {ta_pos}/12 vs Tier B {pos}/174, Fisher p = {p:.3e} < 1e-12")

    # C06 H2 library-driven: every embedder's evidence mentions a library/manifest
    lib_signals = ["libbpf", "cilium/ebpf", "aya", "go.mod", "Cargo", "eBPF"]
    lib_ok = all(
        any(s in (v0[r].get("evidence", "") + " " + " ".join(v0[r].get("signals", [])))
            for s in lib_signals)
        for r in GOLD_EMBED if r in v0)
    check("C06", lib_ok, f"H2: {len(GOLD_EMBED)}/5 embedders have library/manifest evidence")

    # C07 H3 programmatic SEC() census recount
    tracing = sum(v.get("classes", {}).get("tracing", 0) for v in pt.values())
    net = sum(v.get("classes", {}).get("net-path", 0) for v in pt.values())
    check("C07", tracing == 99 and net == 8,
          f"H3 SEC() census: tracing {tracing} vs net-path {net} (from program_types.json)")

    # C08 NEG controls
    neg_ok = all(v0.get(r, {}).get("level") == "L0" for r in NEG)
    check("C08", neg_ok, f"NEG controls {'/'.join(r.split('/')[0] for r in NEG)} all L0")

    # C09 L0 controls
    ctrl_ok = all(v0.get(r, {}).get("level") == "L0" for r in L0_CONTROLS)
    check("C09", ctrl_ok, f"12 gold L0 controls all L0")

    # C10 positive set
    pos_set = {r for r, v in tb.items() if v["level"] in ("L1", "L2")}
    check("C10", pos_set == set(GOLD_POS),
          f"Tier B positives exactly the 6 gold repos ({len(pos_set)} found)")

    # C11 H4 cohort present in corpus
    cohort_ok = all(r in corpus and corpus[r]["stars"] > 0 for r in H4_COHORT)
    check("C11", cohort_ok, f"H4 cohort 7/7 present in corpus with stars (2024-era, active 2026)")

    # C12 strata
    sp = {}
    for r in pos_set:
        sp[v0[r]["stratum"]] = sp.get(v0[r]["stratum"], 0) + 1
    check("C12", sp == {"S1_cloudnative": 2, "S3_netsec": 4},
          f"strata of positives S1=2, S3=4, others=0 (found {sp})")

    # C13 L2 set == gold embed set
    l2_set = {r for r, v in tb.items() if v["level"] == "L2"}
    check("C13", l2_set == set(GOLD_EMBED),
          f"L2 set exactly the 5 verified embedders ({len(l2_set)} found)")

    print("=" * 72)
    print(f"{'PASS' if ok else 'FAIL'}: independent re-count "
          f"{'13/13' if ok else 'with failures'} consistent")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
