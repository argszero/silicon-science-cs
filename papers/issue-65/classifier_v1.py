#!/usr/bin/env python3
"""Issue #65 — classifier v1: final labels with program-type field (H3).

Takes classifier_v0_labels.json (R131 adjudication) and enriches each Tier B
positive + Tier A anchor with a program_type field from the R132 SEC() probe
(program_types.json) + manual annotation (ground_truth_r133.md / notes_r132.md).

Program types: 'tracing' | 'net-path' | 'security' | 'cgroup' | 'other' | None.
Outputs: snapshots/classifier_v1_labels.json, snapshots/classifier_v1_stats.txt
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

v0 = json.load(open(SNAP / "classifier_v0_labels.json"))
pt = json.load(open(SNAP / "program_types.json"))

# Manual program-type assignment (R132 notes; Go/Rust embedders have no SEC() macros).
# Tier B embedders:
MANUAL_TYPES = {
    "netdata/netdata": "tracing",       # tracepoint markers verified in ebpf.c
    "evilsocket/opensnitch": "tracing", # procmon/dns hooks (cilium/ebpf links)
    "safing/portmaster": "net-path",    # tc/bandwidth codegen (bpf_bpfeb.go)
    "firezone/firezone": "net-path",    # XDP TURN router (ebpf-turn-router crate)
    "domcyrus/rustnet": "tracing",      # kprobe/fentry/task_file .bpf.c
    # Tier A anchors (from SEC() probe where available, else known architecture):
    "cilium/cilium": "net-path",        # dataplane XDP/TC + tracing mix; primary = net
    "iovisor/bcc": "tracing",           # 59 tracing SEC() in probe
    "bpftrace/bpftrace": "tracing",     # tracing language
    "falcosecurity/falco": "tracing",   # syscall tracing (driver)
    "cilium/ebpf": None,                # library, no programs
    "projectcalico/calico": "net-path", # eBPF dataplane (XDP/TC)
    "facebookincubator/katran": "net-path",  # 8 net-path SEC() in probe
    "cilium/tetragon": "tracing",       # security observability (kprobe-based)
    "aya-rs/aya": None,                 # library, no programs
    "libbpf/libbpf": None,              # library, no programs
    "cloudflare/ebpf_exporter": "tracing",  # 22 tracing SEC() in probe
    "aquasecurity/libbpfgo": "tracing", # libbpf Go bindings (9 tracing + 1 security + 1 cgroup)
}

v1 = {}
for repo, lab in v0.items():
    entry = dict(lab)
    if repo in MANUAL_TYPES:
        entry["program_type"] = MANUAL_TYPES[repo]
    else:
        # fall back to SEC() probe class max if present
        pr = pt.get(repo, {})
        classes = pr.get("classes", {})
        if classes:
            entry["program_type"] = max(classes, key=classes.get)
        else:
            entry["program_type"] = None
    v1[repo] = entry

json.dump(v1, open(SNAP / "classifier_v1_labels.json", "w"), indent=1)

# stats
tb = {r: v for r, v in v1.items() if v["membership"] == "TierB"}
emb = {r: v for r, v in tb.items() if v["level"] == "L2"}
ptype = defaultdict(list)
for r, v in emb.items():
    ptype[v.get("program_type")].append(r)
lines = [
    "classifier v1 — final labels (R131 adjudication + R132 program types)",
    f"corpus: {len(v1)}  (TierA 12 / TierB {len(tb)} / NEG 3)",
    f"TierB: L0 {sum(1 for v in tb.values() if v['level']=='L0')} "
    f"/ L1 {sum(1 for v in tb.values() if v['level']=='L1')} "
    f"/ L2 {sum(1 for v in tb.values() if v['level']=='L2')}",
    f"TierB positive (L1+L2): {sum(1 for v in tb.values() if v['level'] in ('L1','L2'))}/174",
    f"verified embedders (L2): {len(emb)}/174",
    "",
    "program-type of verified embedders (Tier B L2):",
]
for t in sorted(ptype, key=lambda x: -len(ptype[x])):
    lines.append(f"  {t}: {len(ptype[t])} — {sorted(ptype[t])}")
lines.append("")
lines.append("Tier B L2 repos:")
for r, v in sorted(emb.items(), key=lambda kv: -kv[1]["stars"]):
    lines.append(f"  {v['stars']:>7} {v['language'] or '?':<10} {v['program_type']:<9} {r}")
open(SNAP / "classifier_v1_stats.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
