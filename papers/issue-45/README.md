# Issue #45 — Accessibility Practice in the Wild: ARIA, Testing, and Semantics in Top Open-Source UI Component Libraries

Companion to the manuscript (issue #45, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot indexes.

## One-command reproduction

```bash
cd papers/issue-45
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
cd papers/issue-45
python3 validate.py
```

**Expected output** (tail):

```
ALL      33   0  23   0     1.000  1.000    1.000
cells=56 (14 repos x 4 signals)
No mismatches: pipeline extraction matches hand-verified ground truth.
```

Ground truth lives in `validation_sample.tsv` (56 hand-verified cells = 14 repos × 4
signals: a11y-test-dep / aria-presence / role-presence / a11y-first, each with file-level
evidence). Predictions come from `snapshots/*_index.json` (automatic extractor).

## Traceability

```bash
cd papers/issue-45
python3 trace_check.py
```

**Expected output**: `traceability: ALL 18 checks OK` (every manuscript number traces to the
frozen canonical output).

## From-scratch extraction (requires network)

1. `python3 extract.py trees` — pins head SHAs and fetches recursive git trees for all 14 corpus repos (mui/material-ui uses a prefix-correct segmented walker for its 42.6k-entry tree).
2. `python3 extract.py fetch-manifests` — fetches dependency manifests (parallel, jsDelivr @ pinned SHA).
3. `python3 extract.py signals` — extracts a11y-test-dep + role-path signals into `snapshots/*_index.json`.
4. `python3 extract.py fetch-components` — fetches the deterministic ≤150-file library-source sample.
5. `python3 extract.py aria` — content-level ARIA density + role coverage into the snapshot indexes.
6. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt`. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `validate.py` | recompute 56-cell validation metrics (predictions vs hand-verified ground truth) |
| `trace_check.py` | manuscript-number traceability check |
| `extract.py` + `fetch_one.sh` | network extraction pipeline (regenerates snapshot indexes) |
| `corpus.json` | 14 pinned repositories with head SHAs + a11y-first classification |
| `a11y_first_evidence.md` | auditable H3 grouping evidence (self-description quotes + links + pinned SHAs) |
| `validation_sample.tsv` | 56 hand-verified cells (14 repos × 4 signals) with evidence |
| `snapshots/*_index.json` | per-repo extracted signals (committed input to aggregation) |
| `expected_output/discovery_results.txt` | frozen canonical output (source of every number in the manuscript) |

## Determinism

The census is deterministic: no stochastic components (seeded 150-file sample, pinned SHAs,
regex-based counting). Multi-run statistics are not applicable and are not reported (stated
in the manuscript §Threats). The 150-file per-repo sample is a documented estimate bound,
not an exhaustive count.
