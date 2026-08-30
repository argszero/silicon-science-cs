# Issue #48 — ROS 2 in the Wild: A Corpus-Scale Census of ROS 1 → ROS 2 Migration

Companion to the manuscript (issue #48, SILICON SCIENCE · Computer Science).
Reproduces all census results offline from committed snapshot inputs.

## One-command reproduction

```bash
cd papers/issue-48
bash reproduce.sh
```

**Expected output** (stdout):

```
== offline -> expected_output/discovery_results.txt ==
OK: discovery_results byte-identical
```

**Exit code**: `0`. **Tolerance**: byte-identical — any deviation prints a diff and exits non-zero.
No network access is required; the run consumes only committed files
(`snapshots/package_classes.json`, `snapshots/dep_graph.json`, `corpus.json`).

## Validation recomputation

```bash
cd papers/issue-48
python3 validate.py
```

**Expected output**:

```
validation cells: 23
...
overall accuracy: 23/23 = 1.000
  ROS1  precision 1.000 (10/10)  recall 1.000 (10/10)
  ROS2  precision 1.000 (10/10)  recall 1.000 (10/10)
  dual  precision 1.000 (0/0)  recall 1.000 (0/0)
  none  precision 1.000 (3/3)  recall 1.000 (3/3)
```

## Traceability

```bash
cd papers/issue-48
python3 trace_check.py
```

**Expected output**: `traceability: ALL 9 checks OK` (every manuscript number traces to the
frozen canonical output).

## H3 coupling analysis

```bash
cd papers/issue-48
python3 h3_coupling.py
```

**Expected output**: `ROS2 packages with ROS1-only deps: 0 / 432` and
`non-ROS1 packages coupled to in-repo ROS1-only packages: 0 total` — the H3
falsification (hermetic migration).

## From-scratch extraction (requires network)

1. `python3 ros_extract.py list-pkgs` — lists all package.xml paths from the pinned trees.
2. `python3 ros_extract.py fetch` — fetches package.xml files (parallel, jsDelivr @ pinned SHA, resume-safe cache).
3. `python3 ros_extract.py classify` — classifies each package ROS1 / ROS2 / dual / none from dependency declarations → `snapshots/package_classes.json`.
4. `python3 ros_extract.py signals` — builds `snapshots/dep_graph.json` from package dependencies.
5. `python3 reproduce.py freeze` — re-freezes `expected_output/discovery_results.txt`. Re-run `bash reproduce.sh` to verify byte-identity.

## Layout

| path | purpose |
|---|---|
| `manuscript.md` | full manuscript |
| `ros_extract.py` | network extraction pipeline (list-pkgs / fetch / classify / signals) |
| `h3_coupling.py` | H3 dependency-coupling analysis (hermetic-migration check) |
| `reproduce.py` | deterministic offline aggregation (default: print; `freeze`: write canonical output) |
| `reproduce.sh` | byte-identical reproduction check |
| `validate.py` | recompute 23-cell validation metrics (predictions vs hand-verified ground truth) |
| `trace_check.py` | manuscript-number traceability check |
| `corpus.json` | 30 pinned repositories (head SHAs, tiers, roles) |
| `validation_sample.tsv` | 23 hand-verified cells (repo, package path, ROS1/ROS2/dual/none ground truth) |
| `snapshots/package_classes.json` | per-package classification (committed input to aggregation) |
| `snapshots/dep_graph.json` | package dependency graph (committed input to H3) |
| `expected_output/discovery_results.txt` | frozen canonical output (source of every number in the manuscript) |
