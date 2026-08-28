# Issue #38 — eBPF Programs in the Wild: A Corpus-Scale Census

Companion to the manuscript (issue #38, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot indexes.

## One-command reproduction

```bash
cd papers/issue-38
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
cd papers/issue-38
python3 validate.py
```

**Expected output**:

```
validation sample: 40 files
TP=19 FP=1 TN=20 FN=0
precision=0.950 recall=1.000 accuracy=0.975
```

Ground truth lives in `validation_sample.tsv` (hand-verified, seed-42 stratified sample);
predictions come from `snapshots/*_index.json`.

## From-scratch extraction (requires network)

1. `python3 extract.py` — fetches the pinned head SHAs in `corpus.json` via the GitHub tree API,
   extracts per-file signals (SEC / context / helpers / features), caches raw sources under
   `research/snapshots/`, writes `snapshots/*_index.json`.
2. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt` from the
   regenerated indexes. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `validate.py` | recompute extraction precision/recall/accuracy |
| `extract.py` | network extraction pipeline (regenerates snapshot indexes) |
| `corpus.json` | 12 pinned repositories with head SHAs |
| `census.json` | per-repo summary (files / programs / SEC families / helpers / features) |
| `kernel_helpers.txt` | 216 canonical kernel helpers (from `bpf_helper_defs.h`) |
| `validation_sample.tsv` | hand-labeled stratified ground-truth sample (n=40) |
| `snapshots/*_index.json` | per-repo extracted signal indexes (committed input to aggregation) |
| `expected_output/discovery_results.txt` | frozen canonical output (source of every number in the manuscript) |

## Determinism

The census is deterministic: no stochastic components, no random seeds in aggregation.
Multi-run statistics are not applicable and are not reported (stated in the manuscript §Data & Reproduction).
