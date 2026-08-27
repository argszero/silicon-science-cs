# Coding-Agent Instruction Files in Popular Open-Source Repositories

**Issue**: #20 — **Author**: how2how2how2-arch — **Contribution level**: `system`

An empirical measurement of the new documentation layer read by AI coding agents
(AGENTS.md / CLAUDE.md / .github/copilot-instructions.md / Cursor rules) across 47
popular open-source repositories (41 most-starred across ten ecosystems + 6 AI-native
tools), using the GitHub contents API with no cloning.

## One-command reproduction (offline)

```bash
bash reproduce.sh
```

Reads the committed `data_snapshot/` (47 per-repository JSON snapshots plus
`manifest.json` pinning the fetch date 2026-08-27T08:23:33+08:00), recomputes every
statistic with `reproduce.py`, and diffs the output against
`expected_output/manuscript_results.txt`. **Exit 0 iff byte-identical.** The pipeline
is fully deterministic (classification is a pure function of the snapshot), so no
tolerance band is needed — a byte-identical match is expected on any Python 3.x
machine with no dependencies beyond the standard library.

## Re-fetching fresh data (optional, requires `gh` + network)

```bash
python3 reproduce.py fetch            # re-fetch all 47 repos (7 file probes + .cursor/rules)
python3 reproduce.py --only <owner/repo>   # additive: add one repo, existing snapshots frozen
```

Existing snapshots are never overwritten by a full fetch; `--only` bypasses that
freeze for additive fetches and never rewrites the manifest (old snapshots keep
their original fetch date). **Changing the probe list requires a full re-fetch**
(delete `data_snapshot/*.json` first — the probe set is part of the snapshot schema).

## Corpus (n=47)

| Stratum | Repositories |
|---------|--------------|
| JS/TS | react, microsoft/vscode, vuejs/vue, angular/angular, sveltejs/svelte, mui/material-ui, facebook/react-native |
| Python | python/cpython, django/django, pallets/flask, pandas-dev/pandas, huggingface/transformers, numpy/numpy |
| Go | kubernetes/kubernetes, golang/go, gin-gonic/gin, ollama/ollama, hashicorp/terraform |
| Rust | rust-lang/rust, tokio-rs/tokio, BurntSushi/ripgrep, serde-rs/serde |
| C/C++ | torvalds/linux, git/git, openssl/openssl, curl/curl, tensorflow/tensorflow, google/googletest, redis/redis, neovim/neovim |
| Java/Scala | apache/spark, spring-projects/spring-boot, elastic/elasticsearch |
| Ruby | rails/rails, Homebrew/brew, jekyll/jekyll |
| PHP | laravel/laravel, composer/composer, symfony/symfony |
| Dart / C++ | flutter/flutter, nodejs/node |
| AI-native (contrast) | opencode-ai/opencode, Aider-AI/aider, cline/cline, langchain-ai/langchain, microsoft/autogen, vercel/ai |

## Key results (see expected_output for the full canonical run)

- **C1** — Fragmented adoption: AGENTS.md 20/47 (42.6%, Wilson95 29.5–56.7%),
  CLAUDE.md 12/47 (25.5%, 15.3–39.5%), copilot-instructions 5/47 (10.6%,
  4.6–22.6%), Cursor rules 0/47; 23/47 (48.9%) have ≥1 agent file, 13/47 (27.7%)
  mix ≥2 types; CONTRIBUTING.md baseline 31/47 (66.0%, 51.7–77.8%).
- **C2** — Heterogeneous structure: 39 agent files, size 10–19838 B (median 3529 B),
  10.3% stubs (<50 B); section coverage: commit 53.8%, build 48.7%, conventions
  41.0%, architecture 38.5%, test 38.5%, commands 33.3%, **security 10.3%**.
- **C3** — Cross-vendor duplication: 5/23 agent-file repos have byte-identical
  AGENTS.md ≡ CLAUDE.md (SHA-256 equal; apache/spark, huggingface/transformers,
  langchain-ai/langchain, laravel/laravel, vercel/ai).

## Data availability

- `data_snapshot/` — 47 per-repository JSON snapshots (probe presence, size, line
  count, SHA-256, detected sections per file) + `manifest.json` pinning the fetch
  date; the ground truth for all results.
- `expected_output/manuscript_results.txt` — frozen canonical output (99 lines).
- `reproduce.py` — the canonical runner (fetch / offline / `--only` modes).
- `reproduce.sh` — one-command offline reproduction + diff gate.
