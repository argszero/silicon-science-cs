# Issue #15 — Conventional Commits in the Wild

**Title**: *Conventional Commits in the Wild: An Empirical Measurement of
Spec Compliance and Its Correlates in Popular Open-Source Repositories*

Empirical measurement (deterministic parser, stdlib-only) of Conventional
Commits (CC) spec compliance over 19 popular open-source repositories
(11 with CC tooling configured — 5 CC-tooling vendors + 6 consumer repos —
8 without; 5,700 commits total), plus the association of compliance with
tooling presence and release behavior. Revision round 1 added 3 ordinary
consumer repos with commitlint (element-plus, pnpm, google/blockly) to
bound the tooling estimate against self-selection.

- `manuscript.md` — full manuscript (falsifiable claims C1–C3 with
  hypotheses H1–H3, method, results with t-CIs / Welch t / odds ratio /
  Spearman rho, threats, conclusion)
- `reproduce.py` — canonical analyzer (deterministic, stdlib `ast`/JSON only)
- `reproduce.sh` — one-command reproduction (offline mode)
- `data_snapshot/` — committed data snapshot (16 files: commit messages +
  release dates per repo, fetched from the GitHub REST API on 2026-08-26)
- `expected_output/manuscript_results.txt` — committed expected output
  (canonical-run traceability: every number in the manuscript appears here)
- `related_work.md` — 5 related works with stated differences

## One-command reproduction

```bash
bash reproduce.sh
```

This script runs the canonical analyzer in **offline mode** over the
committed data snapshot and diffs the fresh output against
`expected_output/manuscript_results.txt` — exits 0 iff byte-identical.
No network required.

**Requirements**: `bash`, `python3 ≥ 3.10` (standard library only — no pip
packages).

### Refreshing the data (optional, online)

```bash
python3 reproduce.py            # fetch fresh data via gh api + analyze
python3 reproduce.py --offline  # analyze the (possibly refreshed) snapshot
```

The snapshot was fetched from the GitHub REST API on 2026-08-26 (3 consumer repos added 2026-08-26 in revision round 1); a refresh
would create a *new* snapshot and change numbers — the committed
`expected_output/manuscript_results.txt` always matches the committed
`data_snapshot/` in offline mode.

## Corpus (19 repos, balanced)

| group | repos |
|-------|-------|
| **tooling-present** (11) | CC-tooling vendors: commitizen/cz-cli, semantic-release/semantic-release, conventional-changelog/conventional-changelog, googleapis/release-please, conventional-changelog/commitlint · consumer repos: googleapis/google-cloud-python, google/zx, nestjs/nest, element-plus/element-plus, pnpm/pnpm, google/blockly |
| **tooling-absent** (8) | pallets/click, pallets/flask, fastapi/typer, tqdm/tqdm, dateutil/dateutil, jakubroztocil/httpie, psf/requests, numpy/numpy |

Tooling presence = deterministic multi-signal oracle: root-level CC config
file, `package.json` CC-tool dependency, or CC-tooling GitHub topic.

## Expected output (key numbers)

```
C1 pooled full: 3139/5700 = 55.1% ; per-repo mean 55.1% ± 22.3% (95% t-CI, n=19)
C2 tooling:     92.5% ± 8.9%   vs  no-tooling 3.6% ± 3.6% ; Welch t=20.85 p<0.001 ; OR 333×
   non-vendor subgroup: 88.7% ± 18.4% (n=6)
C3 overall rho = +0.279 (n=19); within tooling rho = -0.036, within no-tooling rho = +0.146
   median releases: tooling 248 vs no-tooling 47 — regularity hypothesis falsified at both levels
```

Full per-repository table and tier decomposition in
`expected_output/manuscript_results.txt`.
