# Issue #33 — Do Trust Signals Predict Supply-Chain Health? Reproduction

Manuscript: [`manuscript.md`](./manuscript.md) — Issue #33 — Author: `how2how2how2-arch`

**Contribution level**: `system` — a deterministic measurement pipeline (GitHub REST
signals + OpenSSF Scorecard + OSV outcomes over a 50-repo, 5-ecosystem corpus),
evaluated by byte-identical offline reproduction; baseline = null correlation and the
H2-vs-H1 signal-class comparison (activity vs popularity signals).

## One-command reproduction

```bash
bash reproduce.sh
```

- **Requires**: Python 3 (stdlib only), network NOT required (fully offline).
- **Input**: committed `data_snapshot/` (50 per-repository JSON snapshots: 10 trust
  signals + Scorecard/OSV outcomes + fetch-time pinning + manifest).
- **Expected output**: `expected_output/discovery_results.txt` (canonical results,
  committed: per-repo table, Spearman ρ by signal, ecosystem medians, H3 spike
  detector, derived coverage/gap stats).
- **Tolerance**: **byte-identical** — `reproduce.sh` regenerates the canonical output
  from the snapshots and exits 0 iff `diff` reports no difference.

## Refresh (optional, network required)

```bash
python3 reproduce.py fetch        # re-pull all 50 repos (GitHub REST + Scorecard + OSV)
python3 reproduce.py fetch <repo> # single repo, e.g. react/react
python3 reproduce.py summary      # per-repo signals table from data_snapshot/
```

Fresh fetches write into `data_snapshot/` and re-derive the canonical output;
`reproduce.sh` then verifies byte-identity against the committed expected output.
Note: fresh fetches may drift from the 2026-08-28 snapshots as upstream moves
(snapshot-drift threat, §5) — the committed snapshots are the pinned evidence.

## File layout

```
papers/issue-33/
├── manuscript.md            # full paper (all numbers traceable to expected_output/)
├── README.md                # this file
├── reproduce.sh             # one-command offline reproduction (exit 0 iff byte-identical)
├── reproduce.py             # pipeline: fetch / summary / offline modes
├── corpus.json              # corpus definition (50 repos, 5 ecosystems, selection rule)
├── data_snapshot/           # 50 repo snapshots + manifest (committed evidence, 208 KB)
└── expected_output/         # canonical discovery_results.txt (frozen)
```

## Traceability statement

Every number in the manuscript (Spearman ρ values, ecosystem medians, H3 outlier
fraction 10/50 (20.0%), coverage 32/50 (64%) / 48/50 (96%), signal gap +0.502)
derives from `data_snapshot/` via `reproduce.py offline` and is frozen in
`expected_output/discovery_results.txt`. The narrative and the canonical run tell
the same story.
