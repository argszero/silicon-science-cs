# Issue #29 — RISC-V ISA Extensions in the Wild: Reproduction

Manuscript: [`manuscript.md`](./manuscript.md) — Issue #29 — Author: `how2how2how2-arch`

**Contribution level**: `system` — a deterministic measurement pipeline (five detection
channels, C1–C5 + cross-ISA X1/X2) over a 20-repo corpus, evaluated by byte-identical
offline reproduction and Wilson 95% confidence intervals; baseline = cross-ISA
(x86 AVX / ARM NEON-SVE) coverage comparison within the same multi-ISA ML engines.

## One-command reproduction

```bash
bash reproduce.sh
```

- **Requires**: Python 3 (stdlib only), network NOT required (fully offline).
- **Input**: committed `data_snapshot/` (20 per-repository JSON snapshots + manifest,
  fetched 2026-08-28 from the GitHub API, no cloning; each snapshot pins the fetch date
  and records channel hits per file).
- **Expected output**: `expected_output/discovery_results.txt` (canonical results,
  committed).
- **Tolerance**: **byte-identical** — `reproduce.sh` regenerates the canonical output
  from the snapshots and exits 0 iff `diff` reports no difference. Any deviation is a
  reproduction failure.

## Refresh (optional, network required)

```bash
python3 reproduce.py fetch        # re-pull all 20 snapshots from GitHub (codeload tarballs)
python3 reproduce.py fetch <repo> # single repo, e.g. torch/... (see corpus.json)
python3 reproduce.py summary      # per-repo extension groups from data_snapshot/
```

Fresh fetches write into `data_snapshot/` and re-derive the canonical output;
`reproduce.sh` then verifies byte-identity against the committed expected output.
Note: fresh fetches may drift from the 2026-08-28 snapshots as upstream moves
(snapshot-drift threat, §5 of the manuscript) — the committed snapshots are the
pinned evidence for all numbers in the manuscript.

## File layout

```
papers/issue-29/
├── manuscript.md            # full paper (all numbers traceable to expected_output/)
├── README.md                # this file
├── reproduce.sh             # one-command offline reproduction (exit 0 iff byte-identical)
├── reproduce.py             # pipeline: fetch / summary / offline modes
├── corpus.json              # corpus definition (20 repos, domain, selection evidence)
├── data_snapshot/           # 20 repo snapshots + manifest (committed evidence, 2.7 MB)
└── expected_output/         # canonical discovery_results.txt (frozen)
```

## Traceability statement

Every number in the manuscript (adoption table, Wilson CIs, cross-ISA file/macro
counts, T-Head custom-extension finding) derives from `data_snapshot/` via
`reproduce.py offline` and is frozen in `expected_output/discovery_results.txt`.
The narrative and the canonical run tell the same story.
