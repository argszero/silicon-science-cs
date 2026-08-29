# Issue #43 — LLM-as-Judge and Evaluation Practice in the Wild: A Corpus-Scale Census of How Open-Source LLM Projects Evaluate

Companion to the manuscript (issue #43, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot indexes.

## One-command reproduction

```bash
cd papers/issue-43
bash reproduce.sh
```

**Expected output** (stdout):

```
== offline -> expected_output/discovery_results.txt ==
OK: discovery_results byte-identical
```

**Exit code**: `0`. **Tolerance**: byte-identical — any deviation prints a diff and exits non-zero.
No network access is required; the run consumes only committed files.

## Validation recomputation

```bash
cd papers/issue-43
python3 validate.py
```

**Expected output**:

```
eval-practice cell validation: 64 hand-verified cells
TP=13 FP=2 TN=49 FN=0
precision=0.867 recall=1.000 accuracy=0.969
```

Ground truth lives in `mechanisms.json` (hand-verified per-repo evaluation-mechanism
classification: built-in-module / hand-rolled / external-harness / benchmark-run / none,
plus judge and validation presence) and `validation_sample.tsv` (64 hand-verified cells =
16 repos × 4 signals: harness/judge/benchmark/validation). Predictions come from
`snapshots/*_index.json` (automatic extractor).

## Traceability

```bash
cd papers/issue-43
python3 trace_check.py
```

**Expected output**: `traceability: ALL 8 checks OK` (every manuscript number traces to the
frozen canonical output).

## From-scratch extraction (requires network)

1. `python3 extract.py trees` — pins head SHAs and fetches recursive git trees for all 16 corpus repos.
2. `python3 extract.py fetch-manifests` — fetches dependency manifests (parallel, jsDelivr @ pinned SHA + raw fallback).
3. `python3 extract.py signals` — extracts per-repo signals into `snapshots/*_index.json`.
4. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt`. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `validate.py` | recompute 64-cell validation metrics (predictions vs hand-verified ground truth) |
| `trace_check.py` | manuscript-number traceability check |
| `extract.py` + `fetch_one.sh` | network extraction pipeline (regenerates snapshot indexes) |
| `corpus.json` | 16 pinned repositories with head SHAs |
| `mechanisms.json` | hand-verified evaluation-mechanism classification (ground truth for H2/H3) |
| `validation_sample.tsv` | 64 hand-verified cells (16 repos × 4 signals) |
| `snapshots/*_index.json` | per-repo extracted signals (committed input to aggregation) |
| `expected_output/discovery_results.txt` | frozen canonical output (source of every number in the manuscript) |

## Determinism

The census is deterministic: no stochastic components. Multi-run statistics are not
applicable and are not reported (stated in the manuscript §Data & Reproduction).
