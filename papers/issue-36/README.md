# Issue #36 — Git-History Forensics of SWE-Bench-Verified: Direct Contamination Evidence — Reproduction

Manuscript: [`manuscript.md`](./manuscript.md) — Issue #36 — Author: `how2how2how2-arch`

**Contribution level**: `system` — a deterministic forensic measurement pipeline (GitHub
REST channel probes + offline aggregation) over all 500 SWE-Bench-Verified instances,
evaluated by byte-identical offline reproduction; baseline = the 2025 model-probing
inferences (arXiv 2512.10218, 2506.12286) and a verbatim-leakage null.

## One-command reproduction

```bash
bash reproduce.sh
```

- **Requires**: Python 3 (stdlib only), network NOT required (fully offline).
- **Input**: committed `data_snapshot_c236/` (500 per-instance JSON records: C1a/C1b/C2/C3
  channel results + issue metadata + fetch-time pinning).
- **Expected output**: `expected_output/discovery_results.txt` (canonical results,
  committed: per-channel rates with Wilson 95% CIs, C1b Jaccard distribution,
  per-repo stratification, issue-year timeline).
- **Tolerance**: **byte-identical** — `reproduce.sh` regenerates the canonical output
  from the snapshots and exits 0 iff `diff` reports no difference.

## Measurement pipeline (`channels.py`, network required to re-run from scratch)

```bash
python3 channels.py <data_snapshot_c236>   # re-run C1a/C1b/C2/C3 probes over SWE-bench instances
python3 reproduce.py offline               # aggregate snapshots -> canonical output
```

`channels.py` reads SWE-bench instances (from `raw/swe_bench_verified.jsonl`, the
committed 2026-08-28 GitHub-mirror snapshot) and probes public GitHub history per
instance: C1a issue availability + issue-body fetch, C1b token-Jaccard vs
`problem_statement`, C2 test-file path existence at `base_commit`, C3 issue-number
commit search. Every probe result is cached (snapshot-pinned); `reproduce.py offline`
is a pure function of the cache. Note: re-running `channels.py` from scratch requires
GitHub API access and takes 30+ minutes under search-API rate limits (~2–3 s/call,
batched); the committed `data_snapshot_c236/` makes the canonical output reproducible
offline regardless.

## File layout

```
papers/issue-36/
├── manuscript.md            # full paper (all numbers traceable to expected_output/)
├── README.md                # this file
├── reproduce.sh             # one-command offline reproduction (exit 0 iff byte-identical)
├── reproduce.py             # offline aggregation (pure function of data_snapshot_c236/)
├── channels.py              # measurement pipeline (C1a/C1b/C2/C3 probes, fetch + cache)
├── raw/                     # committed SWE-bench_Verified snapshot (8.08 MB JSONL, 2026-08-28)
├── data_snapshot_c236/      # 500 per-instance channel records (committed evidence)
└── expected_output/         # canonical discovery_results.txt (frozen)
```

## Traceability statement

Every number in the manuscript (channel rates 100.0%/0.0%/97.8%/92.8% with Wilson 95%
CIs, Jaccard median/p90/max 0.096/0.203/0.647, per-repo tables, issue-year timeline)
derives from `data_snapshot_c236/` via `reproduce.py offline` and is frozen in
`expected_output/discovery_results.txt`. The narrative and the canonical run tell the
same story.

**Source-data note**: instances originate from the GitHub mirror
`OpenAgentsInc/swe-bench-verified` (HF hub unreachable from the compute host at
snapshot time; see manuscript §5 Threats). The committed `raw/` JSONL is the exact
8.08 MB snapshot fetched 2026-08-28; `channels.py` parses it with full schema
validation (500/500 instances, all fields present).
