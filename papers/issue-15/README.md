# Issue #15 — Conventional Commits in the Wild

**Title**: *Conventional Commits in the Wild: An Empirical Measurement of
Spec Compliance and Its Correlates in Popular Open-Source Repositories*

Empirical measurement (deterministic parser, stdlib-only) of Conventional
Commits (CC) spec compliance over 16 popular open-source repositories
(8 with CC tooling configured, 8 without; 4,800 commits total), plus the
association of compliance with tooling presence and release behavior.

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

The snapshot was fetched from the GitHub REST API on 2026-08-26; a refresh
would create a *new* snapshot and change numbers — the committed
`expected_output/manuscript_results.txt` always matches the committed
`data_snapshot/` in offline mode.

## Corpus (16 repos, balanced)

| group | repos |
|-------|-------|
| **tooling-present** (8) | commitizen/cz-cli, semantic-release/semantic-release, conventional-changelog/conventional-changelog, googleapis/release-please, googleapis/google-cloud-python, google/zx, conventional-changelog/commitlint, nestjs/nest |
| **tooling-absent** (8) | pallets/click, pallets/flask, fastapi/typer, tqdm/tqdm, dateutil/dateutil, jakubroztocil/httpie, psf/requests, numpy/numpy |

Tooling presence = deterministic multi-signal oracle: root-level CC config
file, `package.json` CC-tool dependency, or CC-tooling GitHub topic.

## Expected output (key numbers)

```
C1 pooled full: 2270/4800 = 47.3% ; per-repo mean 47.3% ± 24.6% (95% t-CI, n=16)
C2 tooling:     91.0% ± 12.8%  vs  no-tooling 3.6% ± 3.6% ; Welch t=15.50 p<0.001 ; OR 272×
C3 Spearman rho(full%, release-CV) = +0.639 (n=16) — regularity hypothesis falsified
```

Full per-repository table and tier decomposition in
`expected_output/manuscript_results.txt`.
