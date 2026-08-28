# Issue #41 — QUIC and HTTP/3 in the Wild: A Corpus-Scale Census of Protocol Adoption in Open-Source Software

Companion to the manuscript (issue #41, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot indexes.

## One-command reproduction

```bash
cd papers/issue-41
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
cd papers/issue-41
python3 validate.py
```

**Expected output**:

```
embedding-cell validation: 104 hand-verified cells
TP=10 FP=0 TN=94 FN=0
precision=1.000 recall=1.000 accuracy=1.000
```

Ground truth lives in `validation_sample.tsv` (104 hand-verified cells = the complete
8-consumer × 13-signal embedding matrix: 10 positive — covering 100% of extractor-positive
embedding predictions, including the two self-implemented consumers — + 94 verified-negative
cells covering 100% of the negative space); predictions come from `snapshots/*_index.json`.

## From-scratch extraction (requires network)

1. `python3 extract.py trees` — pins head SHAs and fetches recursive git trees for all 20 corpus repos.
2. `python3 extract.py fetch-a` — fetches Tier A implementation source files (parallel, jsDelivr CDN + raw fallback).
3. `python3 extract.py fetch-b` — fetches Tier B consumer manifest files.
4. `python3 extract.py signals` — extracts per-repo feature/embedding signals into `snapshots/*_index.json`.
5. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt`. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `validate.py` | recompute embedding-cell validation metrics |
| `trace_check.py` | manuscript-number traceability check |
| `extract.py` + `fetch_one.sh` | network extraction pipeline (regenerates snapshot indexes) |
| `corpus.json` | 20 pinned repositories with head SHAs |
| `validation_sample.tsv` | hand-verified cell-level ground truth (104 cells = full 8×13 matrix) |
| `snapshots/*_index.json` | per-repo extracted signals (committed input to aggregation) |
| `expected_output/discovery_results.txt` | frozen canonical output (source of every number in the manuscript) |

## Determinism

The census is deterministic: no stochastic components. Multi-run statistics are not
applicable and are not reported (stated in the manuscript §Data & Reproduction).
