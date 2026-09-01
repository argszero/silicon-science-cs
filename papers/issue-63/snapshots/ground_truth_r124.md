# Ground truth — R124 gold annotation (2-pass, same-annotator, 2026-09-01)

Adjudication protocol (mirrors #57/#61): pass-1 = classifier v0 label +
manifest/source evidence review; pass-2 = independent re-verification of
boundary cells (indirect deps, self-impl claims, substring collisions).
Disagreements resolved by rule application (documented below).

## Tier B positive cells (15 candidates, 12 confirmed)

| repo | v0 | v1 | verdict | rule applied |
|------|----|----|---------|--------------|
| ClickHouse/ClickHouse | L2 | L2 | REAL (nuraft embedded, contrib/CMakeLists) | source-verified |
| typesense/typesense | L2 | L2 | REAL (braft vendored via bazel, CMakeLists CORE_LIBS) | vendored=CAPABLE |
| apache/rocketmq | L2 | L2 | REAL (sofa-jraft JRaftController) | source-verified |
| emqx/emqx | L2 | L2 | REAL (builtin Erlang raft, emqx_ds_builtin_raft) | family=Raft, channel=self (NOT raft-rs — substring) |
| ceph/ceph | L2 | L2 | REAL (src/mon/Paxos.cc self-impl) | source-verified self |
| cosmos/cosmos-sdk | L2 | L2 | REAL (cometbft direct dep v0.40.0) | direct dep + source |
| tendermint/tendermint | L2 | L2 | REAL (the BFT implementation itself) | self |
| cubefs/cubefs | L2 | L2 | REAL (etcd-raft direct v3.5.8) | direct dep + source |
| ProvableHQ/snarkOS | L2 | L2 | REAL (narwhal via snarkvm-ledger-narwhal, AleoBFT) | direct dep (lock-level) |
| qdrant/qdrant | L1 | L1 | REAL (raft = { workspace = true } Cargo.toml) | manifest direct |
| dapr/dapr | L1 | L1 | REAL (hashicorp/raft v1.7.3 DIRECT — no indirect marker) | direct dep |
| dgraph-io/dgraph | L1 | L1 | REAL (etcd-raft v3.5.29 direct — no indirect marker) | direct dep |
| pingcap/tidb | L1 | **L0** | **DOWNGRADED** — etcd-raft `// indirect` (via etcd client); TiDB consensus lives in TiKV (raft-rs, separate repo) | indirect-only → L0 |
| lightningnetwork/lnd | L1 | **L0** | **DOWNGRADED** — etcd-raft `// indirect` (via etcd-client kvdb backend); no raft runtime | indirect-only → L0 |
| smartcontractkit/chainlink | L1 | **L0** | **DOWNGRADED** — cometbft `// indirect` (via cosmos-sdk); Chainlink uses OCR consensus | indirect-only → L0 |

**Indirect rule (new, R124)**: go.mod `// indirect` consensus dependency with no
source-level usage evidence → transitive dependency (usually pulled by a
coordination/other client), repo does not run that consensus → L0. This mirrors
#61's "types-only/docs-only → L0" and the coordination-client≠consensus rule.
Without it, H1/H2 would over-count by 3 (25% of positives).

## L0 negative controls (12 sampled, all verified L0)

reth (PoS client consensus — non-classic), chia-blockchain (PoST — non-classic;
`graftroot` substring ≠ Raft), glusterfs (custom management daemons — no classic
protocol), lowdb, ntfy, plus 7 more (see classifier_v1_labels.json). All clean:
no Raft/Paxos/BFT-family library or self-impl. Confirms L0 is not a false-negative.

## Tier A anchors (16) — consensus by construction

etcd (Raft), consul (Raft/hashicorp), zookeeper (ZAB/Paxos-family), kafka (KRaft),
tikv (Raft/raft-rs), redpanda (Raft self), scylladb (Paxos+raft self), foundationdb
(Paxos self), dragonboat (Raft lib), raft-rs (Raft lib), hashicorp/raft (Raft lib),
braft (Raft lib), cometbft (BFT self), fabric (Raft/etcd-raft vendored), sui (BFT
self), aptos (BFT self). All 16/16 = L1/L2.

## Net effect vs v0

- Tier B consensus-positive: 15 → **12** (removed 3 indirect-only)
- H1 Raft 10/15 → **8/12 = 66.7%** (CI [39.1, 86.2], 2 flips)
- H2 lib 13/15 → **9/12 = 75.0%** (CI [46.8, 91.1], 3 flips)
- H3 anchors 16/16 vs Tier B 12/174 = 6.9% (Fisher p = 4.2e-16)
- Go share among adopters: 8/15 → 5/12 = 41.7% (still largest single language)
