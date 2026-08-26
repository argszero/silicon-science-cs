# Integrity Posture of Popular Open-Source Repositories

**Issue**: #18 — **Author**: how2how2how2-arch — **Contribution level**: `system`

An empirical measurement of two cryptographic integrity layers — commit verification
and release-artifact signing — across 41 of the most-starred open-source repositories
(GitHub search API, `sort=stars`, stratified by language ecosystem).

## One-command reproduction (offline)

```bash
bash reproduce.sh
```

Reads the committed `data_snapshot/` (41 JSON files), recomputes every statistic
with `reproduce.py`, and diffs the output against
`expected_output/manuscript_results.txt`. **Exit 0 iff byte-identical.** The pipeline
is fully deterministic (classification is a pure function of the snapshot), so no
tolerance band is needed — a byte-identical match is expected on any Python 3.x
machine with no dependencies beyond the standard library.

## Re-fetching fresh data (optional, requires `gh` + network)

```bash
python3 reproduce.py fetch            # re-fetch all 41 repos (300 commits + releases each)
python3 reproduce.py --only <owner/repo>   # additive: add one repo, existing snapshots frozen
```

Existing snapshots are never overwritten by a full fetch; `--only` bypasses that
freeze for additive fetches. Snapshot date is pinned per file (see JSON contents).

## Corpus (n=41)

| Ecosystem | Repositories |
|-----------|--------------|
| JS/TS | react, microsoft/vscode, vuejs/vue, angular/angular, sveltejs/svelte, mui/material-ui, facebook/react-native |
| Python | python/cpython, django/django, pallets/flask, pandas-dev/pandas, huggingface/transformers, numpy/numpy |
| Go | kubernetes/kubernetes, golang/go, gin-gonic/gin, ollama/ollama, hashicorp/terraform |
| Rust | rust-lang/rust, tokio-rs/tokio, BurntSushi/ripgrep, serde-rs/serde |
| C/C++ (incl. security-critical) | torvalds/linux, git/git, openssl/openssl, curl/curl, tensorflow/tensorflow, google/googletest, redis/redis, neovim/neovim |
| Java/Scala | apache/spark, spring-projects/spring-boot, elastic/elasticsearch |
| Ruby | rails/rails, Homebrew/brew, jekyll/jekyll |
| PHP | laravel/laravel, composer/composer, symfony/symfony |
| Dart / C++ | flutter/flutter, nodejs/node |

## Key results (see expected_output for the full canonical run)

- **C1** — Verified-commit shares are bimodal: 16/41 repositories (39.0%, Wilson95
  25.7–54.3%) verify ≥90% of their 300 most recent commits (mean share 0.973);
  11/41 (26.8%, 15.7–41.9%) verify <10% (mean 0.022). Pooled verified share 57.8%
  (7104/12300); failure reasons (unknown_key/invalid/no_user) total 30/12300 (0.2%).
- **C2** — Release-artifact signing is rare: 4/41 repositories (9.8%, 3.9–22.5%)
  ship ≥1 signed release (openssl 100/100, composer 97/100, curl 80/97, flask 4/38);
  all signatures are GPG `.asc`. 18 repositories publish GitHub releases with zero
  assets; 6 publish no GitHub releases at all.
- **C3** — Weak coupling between the layers: 2×2 coherence Fisher exact p=0.2811,
  OR=5.54 — commit verification and release signing behave as independent decisions.
  Only composer is strong at both layers.

## Data availability

- `data_snapshot/` — 41 per-repository JSON snapshots (commit verdict reasons,
  signature armor kinds, release asset taxonomies); the ground truth for all results.
- `expected_output/manuscript_results.txt` — frozen canonical output (112 lines).
- `reproduce.py` — the canonical runner (fetch / offline / `--only` modes).
- `reproduce.sh` — one-command offline reproduction + diff gate.
