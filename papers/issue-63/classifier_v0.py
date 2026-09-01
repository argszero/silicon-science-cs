#!/usr/bin/env python3
"""Issue #63 — classifier v0: consensus adoption level (L0/L1/L2) over the corpus.

Levels (dict v1.1):
  L0: no consensus signal (neither manifest nor source)
  L1: dependency-capable — consensus library in manifest, usage not verified
  L2: verified/self-implemented — source-level library identifiers (imports/call
      sites) OR in-repo self-implemented consensus (ceph Paxos, kafka KRaft,
      scylladb paxos+raft)
  L3: API-usage call-site verification — deferred to R124 (content probes)

Channels:
  Channel 1 (manifest): snapshots/consensus_dep_evidence.json (R122)
  Channel 2 (source paths): scan of snapshots/trees/*.json with dict v1.1
      library-identifier patterns

Outputs:
  snapshots/classifier_v0_labels.json — {repo: {level, evidence, signals}}
  snapshots/classifier_v0_stats.txt
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

# Channel 1 (manifest) signals per repo — from R122
MANIFEST_EVIDENCE = json.load(open(SNAP / "consensus_dep_evidence.json"))

# Channel 2 (source-path) library identifiers — dict v1.1 refined.
# (path-level, exact-ish; bare words banned per noise rules)
SOURCE_PATTERNS = {
    "etcd-raft":      [r"etcd/raft/", r"/raft/v3/", r"etcd-io/raft", r"raftpb"],
    "hashicorp/raft": [r"hashicorp/raft"],
    "raft-rs":        [r"/raft-rs/", r"raftstore", r"raft_proto", r"raft-proto"],
    "openraft":       [r"openraft/"],
    "braft":          [r"src/braft/", r"braft::", r"/braft/", r"brpc.*braft"],
    "nuraft":         [r"nuraft"],
    "dragonboat":     [r"dragonboat"],
    "sofa-jraft":     [r"sofa-jraft", r"jraft"],
    "ratis":          [r"/ratis/"],
    "cometbft":       [r"cometbft", r"tendermint"],
    "narwhal":        [r"narwhal"],
    "paxos":          [r"(^|/)paxos/", r"paxos\.(cc|h|hh|cpp)", r"mmonpaxos"],
    "kraft":          [r"kraft", r"quorumcontroller", r"controller/.*quorum"],
    # anchor-specific (their own trees use internal names, not lib import paths)
    "etcd-raft":      [r"etcdserver/api/raft", r"rafthttp"],
    "zab":            [r"server/quorum/"],   # zookeeper ZAB only (bare 'zab' matches serializable/freezable)
    "sui-consensus":  [r"^consensus/"],
    "aptos-consensus": [r"^consensus/"],
}

# Anchor fallback: Tier A anchors are consensus implementations by construction
# (mirrors #61 Tier A = crypto anchors). If no signal detected, assign L2 with
# family/channel from this known mapping (evidence notes "by construction").
ANCHOR_CONSENSUS = {
    "etcd-io/etcd":        ("Raft", "lib",  "etcd embeds its own raft module (go.etcd.io/raft)"),
    "hashicorp/consul":    ("Raft", "lib",  "consul embeds hashicorp/raft"),
    "apache/zookeeper":    ("Paxos", "self", "ZAB quorum protocol (server/quorum/, Zab.tla)"),
    "apache/kafka":        ("Raft", "self", "KRaft quorum controller (raft-like, self-impl)"),
    "tikv/tikv":           ("Raft", "lib",  "raft-rs embedded (raftstore)"),
    "redpanda-data/redpanda": ("Raft", "self", "self-implemented raft (consensus/)"),
    "scylladb/scylladb":   ("Paxos", "self", "service/paxos/ + service/raft/ self-impl"),
    "apple/foundationdb":  ("Paxos", "self", "paxos-based commit protocol (architecture docs; no paxos paths)"),
    "lni/dragonboat":      ("Raft", "lib",  "dragonboat library itself"),
    "tikv/raft-rs":        ("Raft", "lib",  "raft-rs library itself"),
    "hashicorp/raft":      ("Raft", "lib",  "hashicorp/raft library itself"),
    "baidu/braft":         ("Raft", "lib",  "braft library itself"),
    "cometbft/cometbft":   ("BFT", "self",  "tendermint BFT implementation itself"),
    "hyperledger/fabric":  ("Raft", "lib",  "orderer uses etcd-raft (vendored)"),
    "MystenLabs/sui":      ("BFT", "self",  "narwhal/bullshark BFT (consensus crate)"),
    "aptos-labs/aptos-core": ("BFT", "self", "jolteon BFT (consensus crate)"),
}

# Self-implementation detection: repos known (R122 path scan) to implement
# classic consensus in-repo (no external lib). These are L2 via Channel 2.
SELF_IMPL_PATHS = {
    "ceph/ceph":          ["src/mon/Paxos.cc", "src/mon/Paxos.h", "src/messages/MMonPaxos.h"],
    "scylladb/scylladb":  ["service/paxos/", "service/raft/"],
    "apache/kafka":       ["kraft", "QuorumController"],
}

# Consensus-library signals vs coordination-client signals (rule 5).
# A repo is consensus-positive iff it has >=1 consensus signal; coord-only -> L0.
CONSENSUS_SIGNALS = {
    "etcd-raft", "hashicorp/raft", "raft-rs crate", "openraft", "dragonboat",
    "braft", "nuraft", "sofa-jraft", "ratis", "atomix", "logcabin",
    "phxpaxos", "libpaxos", "zookeeper(ZAB)", "cometbft", "tendermint",
    "tendermint-rs", "libhotstuff", "narwhal", "bullshark", "paxos", "kraft",
    # source-channel family names map to the same consensus set:
    "raft-rs", "jraft",
}
COORD_SIGNALS = {"etcd-client", "zookeeper-client"}

# Family assignment for H1 (Raft vs Paxos vs BFT).
FAMILY_RAFT = {"etcd-raft", "hashicorp/raft", "raft-rs crate", "raft-rs",
               "openraft", "dragonboat", "braft", "nuraft", "sofa-jraft",
               "jraft", "ratis", "atomix", "logcabin", "kraft"}
FAMILY_PAXOS = {"phxpaxos", "libpaxos", "zookeeper(ZAB)", "paxos"}
FAMILY_BFT = {"cometbft", "tendermint", "tendermint-rs", "libhotstuff",
              "narwhal", "bullshark"}

# Repos that self-implement consensus in-repo (no external library) — L2 via
# Channel 2, and channel=SELF for H2.
SELF_IMPL_REPOS = {
    "ceph/ceph": "paxos",                 # src/mon/Paxos.cc
    "scylladb/scylladb": "paxos",         # service/paxos/ (also service/raft/)
    "apache/kafka": "kraft",              # KRaft controller (raft-like)
    "apple/foundationdb": "paxos",        # internal paxos
    "tendermint/tendermint": "bft",       # the implementation itself
    "cometbft/cometbft": "bft",           # the implementation itself
}


def family_of(signals):
    s = set(signals)
    if s & FAMILY_RAFT:
        return "Raft"
    if s & FAMILY_PAXOS:
        return "Paxos"
    if s & FAMILY_BFT:
        return "BFT"
    return None


def channel_of(repo, signals, level):
    """'lib' = dependency-library-embedded; 'self' = in-repo implementation."""
    if repo in SELF_IMPL_REPOS:
        return "self"
    if level in ("L1", "L2"):
        return "lib"
    return None


def source_probe(repo):
    """Scan tree paths for Channel-2 identifiers. Returns {signal: [paths]}."""
    fname = repo.replace("/", "__") + ".json"
    fpath = SNAP / "trees" / fname
    if not fpath.exists():
        return {}
    data = json.load(open(fpath))
    hits = defaultdict(list)
    for entry in data.get("tree", []):
        p = entry.get("path", "")
        pl = p.lower()
        for sig, pats in SOURCE_PATTERNS.items():
            if any(re.search(pat, pl, re.IGNORECASE) for pat in pats):
                hits[sig].append(p)
    return dict(hits)


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    labels = {}
    stats = defaultdict(int)

    for repo, meta in corpus.items():
        membership = meta.get("membership", "?")
        manifest_hits = MANIFEST_EVIDENCE.get(repo, {})
        man_signals = sorted({h["signal"] for paths in manifest_hits.values() for h in paths})
        src = source_probe(repo)
        src_signals = sorted(src.keys())

        # classify
        if membership == "NEG":
            level = "L0"
            evidence = "negative-control (PoW/PoS)"
            signals = []
        else:
            # consensus-positive iff >=1 consensus signal (manifest or source)
            man_cons = [s for s in man_signals if s in CONSENSUS_SIGNALS]
            src_cons = [s for s in src_signals if s in CONSENSUS_SIGNALS]
            man_coord = [s for s in man_signals if s in COORD_SIGNALS]
            src_coord = [s for s in src_signals if s in COORD_SIGNALS]
            if man_cons or src_cons:
                if src_cons or src_signals:
                    # source-level usage (library identifiers or self-impl)
                    level = "L2"
                    evidence = "source-path identifiers: " + ", ".join((src_cons or src_signals)[:5])
                else:
                    level = "L1"
                    evidence = "manifest-only: " + ", ".join(man_cons[:5])
                signals = sorted(set(man_cons + src_cons))
            elif man_coord or src_coord:
                level = "L0"
                evidence = "coordination-client only (NOT consensus): " + ", ".join(sorted(set(man_coord + src_coord))[:4])
                signals = []
            else:
                level = "L0"
                evidence = "no consensus signal"
                signals = []
            # anchor fallback: consensus implementation by construction
            if level == "L0" and repo in ANCHOR_CONSENSUS:
                fam, ch, why = ANCHOR_CONSENSUS[repo]
                level = "L2"
                evidence = f"anchor consensus implementation ({why})"
                signals = [fam.lower()]
                # stash family/channel for later (overwritten below)
                labels_family = fam
                labels_channel = ch
            else:
                labels_family = family_of(signals)
                labels_channel = channel_of(repo, signals, level)

        labels[repo] = {
            "level": level,
            "membership": membership,
            "stratum": meta.get("stratum", ""),
            "language": meta.get("language"),
            "stars": meta.get("stars"),
            "evidence": evidence,
            "signals": signals,
            "family": labels_family,
            "channel": labels_channel,
        }
        stats[level] += 1

    json.dump(labels, open(SNAP / "classifier_v0_labels.json", "w"), indent=1)

    # stats by membership
    tb = {r: v for r, v in labels.items() if v["membership"] == "TierB"}
    ta = {r: v for r, v in labels.items() if v["membership"] == "TierA"}
    neg = {r: v for r, v in labels.items() if v["membership"] == "NEG"}
    def dist(d):
        c = defaultdict(int)
        for v in d.values():
            c[v["level"]] += 1
        return dict(c)

    lines = [
        f"corpus: {len(labels)}  (TierA {len(ta)} / TierB {len(tb)} / NEG {len(neg)})",
        f"all: {dict(stats)}",
        f"TierB: {dist(tb)}",
        f"TierA: {dist(ta)}",
        f"NEG: {dist(neg)}",
        "",
        "Tier B L2 repos (verified/self-impl):",
    ]
    for r, v in sorted(tb.items(), key=lambda kv: -kv[1]["stars"]):
        if v["level"] == "L2":
            lines.append(f"  {v['stars']:>7} {(v['language'] or '?'):<10} {r} [{v['stratum']}] — {v['evidence'][:70]}")
    lines.append("")
    lines.append("Tier B L1 repos (manifest-only):")
    for r, v in sorted(tb.items(), key=lambda kv: -kv[1]["stars"]):
        if v["level"] == "L1":
            lines.append(f"  {v['stars']:>7} {(v['language'] or '?'):<10} {r} [{v['stratum']}] — {v['evidence'][:70]}")
    open(SNAP / "classifier_v0_stats.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
