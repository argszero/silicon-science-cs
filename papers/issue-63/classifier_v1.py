#!/usr/bin/env python3
"""Issue #63 — classifier v1: L0/L1/L2 with indirect-dependency adjudication.

Changes vs v0 (R124 gold-annotation round):
  R1. **Indirect rule**: go.mod `// indirect` consensus deps with NO source-level
      evidence are transitive (via etcd-client / cosmos-sdk / etc.) and the repo
      does NOT run that consensus → L0. Applies to: tidb (etcd-raft indirect,
      consensus lives in TiKV), lnd (etcd-raft via etcd-client kvdb backend),
      chainlink (cometbft via cosmos-sdk; own OCR consensus).
  R2. **emqx correction**: `emqx_ds_builtin_raft` matched `raft_proto` substring
      of raft-rs pattern; emqx's consensus is a built-in Erlang Raft (self-impl).
      family=Raft, channel=self, signal="builtin-raft".
  R3. SnarkOS: narwhal via snarkvm-ledger-narwhal (AleoBFT) — keep L1 (lock-level,
      direct AleoBFT dependency), evidence noted.

Outputs: snapshots/classifier_v1_labels.json, snapshots/classifier_v1_stats.txt
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

MANIFEST_EVIDENCE = json.load(open(SNAP / "consensus_dep_evidence.json"))
v0_labels = json.load(open(SNAP / "classifier_v0_labels.json"))

# --- R124 manual adjudications (gold annotation, 2-pass, same-annotator) ---
# indirect-only consensus dep (no source usage) -> L0
INDIRECT_ONLY_L0 = {
    "pingcap/tidb": "etcd-raft // indirect (via etcd client; TiDB consensus lives in TiKV/raft-rs)",
    "lightningnetwork/lnd": "etcd-raft // indirect (via etcd-client kvdb backend; no raft runtime)",
    "smartcontractkit/chainlink": "cometbft // indirect (via cosmos-sdk; Chainlink uses OCR consensus)",
}
# emqx: builtin Erlang Raft (self-impl), not raft-rs
EMQX_CORRECTION = {
    "family": "Raft",
    "channel": "self",
    "evidence": "builtin Erlang raft (emqx_ds_builtin_raft; self-implemented, not raft-rs)",
}

# Consensus vs coord (from v0)
CONSENSUS_SIGNALS = {
    "etcd-raft", "hashicorp/raft", "raft-rs crate", "openraft", "dragonboat",
    "braft", "nuraft", "sofa-jraft", "ratis", "atomix", "logcabin",
    "phxpaxos", "libpaxos", "zookeeper(ZAB)", "cometbft", "tendermint",
    "tendermint-rs", "libhotstuff", "narwhal", "bullshark", "paxos", "kraft",
    "raft-rs", "jraft", "builtin-raft", "zab",
}
COORD_SIGNALS = {"etcd-client", "zookeeper-client"}
FAMILY_RAFT = {"etcd-raft", "hashicorp/raft", "raft-rs crate", "raft-rs",
               "openraft", "dragonboat", "braft", "nuraft", "sofa-jraft",
               "jraft", "ratis", "atomix", "logcabin", "kraft", "builtin-raft"}
FAMILY_PAXOS = {"phxpaxos", "libpaxos", "zookeeper(ZAB)", "paxos", "zab"}
FAMILY_BFT = {"cometbft", "tendermint", "tendermint-rs", "libhotstuff",
              "narwhal", "bullshark"}


def family_of(signals):
    s = set(signals)
    if s & FAMILY_RAFT:
        return "Raft"
    if s & FAMILY_PAXOS:
        return "Paxos"
    if s & FAMILY_BFT:
        return "BFT"
    return None


def main():
    labels = {}
    for repo, v in v0_labels.items():
        entry = dict(v)

        # apply indirect-only L0 adjudication
        if repo in INDIRECT_ONLY_L0:
            entry["level"] = "L0"
            entry["evidence"] = "INDIRECT-ONLY: " + INDIRECT_ONLY_L0[repo]
            entry["signals"] = []
            entry["family"] = None
            entry["channel"] = None
        elif repo == "emqx/emqx":
            entry["level"] = "L2"  # source-verified (builtin raft dirs)
            entry["family"] = EMQX_CORRECTION["family"]
            entry["channel"] = EMQX_CORRECTION["channel"]
            entry["evidence"] = EMQX_CORRECTION["evidence"]
            entry["signals"] = ["builtin-raft"]
        labels[repo] = entry

    json.dump(labels, open(SNAP / "classifier_v1_labels.json", "w"), indent=1)

    tb = {r: v for r, v in labels.items() if v["membership"] == "TierB"}
    ta = {r: v for r, v in labels.items() if v["membership"] == "TierA"}
    neg = {r: v for r, v in labels.items() if v["membership"] == "NEG"}

    def dist(d):
        c = defaultdict(int)
        for v in d.values():
            c[v["level"]] += 1
        return dict(c)

    pos = {r: v for r, v in tb.items() if v["level"] in ("L1", "L2")}
    from collections import Counter
    fam = Counter(v["family"] for v in pos.values())
    chan = Counter(v["channel"] for v in pos.values())

    lines = [
        f"corpus: {len(labels)} (TierA {len(ta)} / TierB {len(tb)} / NEG {len(neg)})",
        f"TierB: {dist(tb)}",
        f"TierA: {dist(ta)}",
        f"NEG: {dist(neg)}",
        f"TierB consensus-positive: {len(pos)}/{len(tb)} = {len(pos)/len(tb)*100:.1f}%",
        f"family: {dict(fam)}  channel: {dict(chan)}",
        "",
        "Tier B consensus-positive (gold-annotated):",
    ]
    for r, v in sorted(pos.items(), key=lambda kv: -kv[1]["stars"]):
        lines.append(f"  {v['stars']:>7} {v['language'] or '?':<9} {v['level']} {v['family'] or '-':<5} "
                     f"{v['channel'] or '-':<4} {r} — {v['evidence'][:60]}")
    lines.append("")
    lines.append("Downgraded to L0 (R124 indirect adjudication):")
    for r in INDIRECT_ONLY_L0:
        lines.append(f"  {r}")
    open(SNAP / "classifier_v1_stats.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
