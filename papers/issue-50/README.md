# Issue #50 — Model Cards in the Wild: A Corpus-Scale Census of Documentation Practice in Open-Weight Foundation Models

**Reproducibility spec** — one command reproduces the core results:

```bash
bash reproduce.sh
```

**Expected output** (exit 0):

```
OK: signals.json byte-identical
OK: hypotheses.txt byte-identical
```

Everything is offline — the pipeline re-derives both canonical outputs from the
committed raw snapshots (`snapshots/cards/*.json` + `snapshots/readmes/*.md` +
`corpus.json`) via `extract.py` + `hypotheses.py`, and diffs byte-identically
against `expected_output/`.

## What this is

A deterministic, snapshot-pinned census of model-card documentation practice in
open-weight foundation models: **187 model repositories** on the Hugging Face
Hub (snapshot 2026-08-30), **8 documentation signals** per model (license,
training-data, evaluation results, bias/limitations, intended use, base-model
lineage, technical details, citations), hand-validated on **128 cells**
(precision 1.000 / recall 1.000).

**Headline results** (canonical: `expected_output/hypotheses.txt`):

- **H1 CONFIRMED** — completeness mean 0.610 / median 0.625; 31/187 (16.6%) ≤ 0.25.
- **H2 org/popularity FALSIFIED; gating CONFIRMED** — gated (15) 0.167 vs
  non-gated (172) 0.649, Δ 0.482, Mann-Whitney U = 132; gating is org policy,
  not popularity (38 models exceed the most-downloaded gated model).
- **H3 CONFIRMED** — license 94.1% > technical 75.4% > intended use 66.3% >
  eval 57.8% > base-model 54.0% > citations 52.9% > training-data 51.3% >
  bias/limitations 36.4%; gated models expose only license + base-model.

## Commands

| Command | Purpose | Expected |
|---|---|---|
| `bash reproduce.sh` | offline regenerate + byte-compare canonical outputs | exit 0, two `OK:` lines |
| `python3 validate.py` | validation metrics on the 128 hand-annotated cells | accuracy 100.0% (128/128), precision 1.000, recall 1.000 |
| `python3 trace_check.py` | corpus ↔ snapshots ↔ signals cross-checks | ALL 21 checks OK |
| `python3 extract.py` | re-extract signals from the raw snapshots (network-free) | writes `snapshots/signals.json` |
| `python3 reproduce.py freeze` | re-freeze canonical outputs after any rule change | writes `expected_output/` |
| `python3 build_corpus.py` | re-run the exact corpus-selection rule (network: hf-mirror.com) | rewrites `corpus.json` |
| `python3 fetch_cards.py` | re-fetch cardData + READMEs at pinned ids (network, resume-safe) | refills `snapshots/cards/`, `snapshots/readmes/` |

## Committed artifacts

- `corpus.json` — 187 pinned models (id, org, downloads, likes, pipeline_tag, library_name, tags, createdAt, **sha** — pinned HF commit SHA for every model, backfilled from cardData / maintained by `fetch_cards.py`)
- `snapshots/cards/` — 187 cardData JSON (verbatim API responses, each carrying the pinned SHA)
- `snapshots/readmes/` — 172 README markdown (**15 gated models have no public README** — the finding behind H2)
- `snapshots/list/` — raw API-list responses backing the exact selection rule
- `snapshots/signals.json` — per-model 8-signal records (regenerable)
- `extract.py`, `hypotheses.py`, `reproduce.py`, `reproduce.sh`, `trace_check.py`, `validate.py`, `build_corpus.py`, `fetch_cards.py`
- `validation_sample.tsv` — 128 hand-annotated validation cells (model, signal, pred, gated, evidence, human, notes)
- `expected_output/signals.json` + `expected_output/hypotheses.txt` — frozen canonical outputs

## Determinism

Fully deterministic (no stochastic components); multi-run statistics not
applicable. The extraction rules are committed in `extract.py`; any rule change
is caught by `bash reproduce.sh` (canonical mismatch → non-zero exit).

## Data source note

The Hugging Face Hub (huggingface.co) was unreachable from the research sandbox
(TCP blocked); all fetches went through the **hf-mirror.com** mirror, which
exposes the same API and raw-README endpoints. The snapshot is pinned; the
mirror is only relevant for from-scratch re-fetch (`build_corpus.py` /
`fetch_cards.py`), which the committed snapshots make unnecessary.
