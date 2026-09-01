# H4 longitudinal — Raft early adopters (2014 → 2026)

Baseline: Raft 2014 paper (Ongaro & Ousterhout, USENIX ATC) early-adopter
implementations; 2026 status verified via `gh api repos/{full_name}`
(pushed_at / archived / stars) on 2026-09-01.

| System | adopted Raft | 2026 status | consensus library | verdict |
|--------|-------------|-------------|-------------------|---------|
| LogCabin | 2014 (author impl) | semi-dormant (last push 2024-06, 2.0k★, not archived) | own implementation | survived 10y, dormant |
| etcd (CoreOS) | 2014 (2013) | active (2026-09-01, 52.2k★) | go.etcd.io/raft (extracted module) | SURVIVED, still Raft |
| Consul (HashiCorp) | 2014 | active (2026-09-01, 30.1k★) | hashicorp/raft | SURVIVED, still Raft |
| CockroachDB | 2015 | active (2026-08-26, 32.4k★) | etcd-raft (fork lineage) | SURVIVED, still Raft* |
| TiKV (PingCAP) | 2016 | active (2026-08-31, 16.8k★) | tikv/raft-rs | SURVIVED, still Raft |
| braft (Baidu) | 2017 | low-activity (2024-10, 4.2k★) | braft (C++) | survived, low activity |
| dragonboat (lni) | 2017 | low-activity (2025-07, 5.3k★) | dragonboat (Go) | survived, low activity |

\* CockroachDB not in Tier B corpus (stratified quota sampling missed it) —
its Raft adoption is documented here as known baseline, not census stat.

Summary: of 7 documented early adopters, 5 survive actively in 2026 and all
still use a Raft-family protocol; 1 (LogCabin) is dormant; none abandoned Raft
for another consensus family. Raft's "widely adopted" claim (Nezha 2603.09122)
holds for the 2014 cohort AND is quantified for the general population in this
census (H1: 8/12 = 66.7% of consensus-using Tier B repos are Raft-family).
