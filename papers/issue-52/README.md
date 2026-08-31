# Issue #52 — Rust in the Wild: A Corpus-Scale Census of C/C++ → Rust Rewrites in Open-Source Software

Companion to the manuscript (issue #52, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot inputs.

## One-command reproduction

```bash
cd papers/issue-52
bash reproduce.sh
```

**Expected output** (stdout):

```
== offline -> expected_output/discovery_results.txt ==
OK: discovery_results byte-identical
```

**Exit code**: `0`. **Tolerance**: byte-identical — any deviation prints a diff and exits non-zero.
No network access is required; the run consumes only committed files
(`snapshots/component_classes.json`, `snapshots/repo_signals.json`,
`snapshots/validation_result.json`, `corpus.json`).

## Validation recomputation

```bash
cd papers/issue-52
python3 validate.py
```

**Expected output**:

```
validation cells: 36  accuracy 36/36 = 1.000
  RUST   prec 1.000 (18/18)  rec 1.000 (18/18)
  C      prec 1.000 (16/16)  rec 1.000 (16/16)
  CPP    prec 1.000 (1/1)  rec 1.000 (1/1)
  MIXED  prec 1.000 (1/1)  rec 1.000 (1/1)
boundary cells: 7  accuracy 7/7 = 1.000
```

The 2-pass annotation protocol (editor watch-item) and the pass-A/pass-B
disagreement resolution are documented in `validation_report.txt`.

## Traceability

```bash
cd papers/issue-52
python3 trace_check.py
```

**Expected output**: `traceability: ALL 11 checks OK` (every manuscript number
traces to the frozen canonical output).

## From-scratch extraction (requires network)

1. `python3 fetch_trees.py` — fetches recursive git trees for all 32 repos at the pinned SHAs → `snapshots/trees/`.
2. `python3 extract.py` — component-level language classification → `snapshots/component_classes.json`.
3. `python3 signals.py` — repo signals + binding_vs_rewrite → `snapshots/repo_signals.json`.
4. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt`. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `build_corpus.py` | corpus-selection rule (16 era-pairs, verbatim list; re-queries GitHub) |
| `fetch_trees.py` | recursive tree fetching (network; resume-safe) |
| `extract.py` | component-level classification (manifest-aware + FFI-auxiliary rule) |
| `signals.py` | repo signals + binding_vs_rewrite |
| `validate.py` | recompute 36-cell validation metrics (predictions vs hand-verified ground truth) |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `trace_check.py` | manuscript-number traceability check |
| `corpus.json` | 32 pinned repositories (head SHAs, tiers, roles, stars, default branches) |
| `validation_sample.tsv` | 36 hand-verified cells (repo, component, human label, boundary flag, evidence) |
| `validation_report.txt` | 2-pass annotation protocol + disagreement resolution |
| `snapshots/component_classes.json` | per-component language classification (252 components) |
| `snapshots/repo_signals.json` | per-repo signals + binding verdicts |
| `snapshots/validation_result.json` | validation metrics |
| `expected_output/discovery_results.txt` | frozen canonical output |
