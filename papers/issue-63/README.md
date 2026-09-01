# Issue #63 — Consensus in the Wild: A Source-Level Census of Consensus-Protocol Adoption in Open-Source Distributed Systems

Reproducibility specification for the submitted manuscript (PR `paper/issue-63`).

## One-command reproduction

```bash
bash reproduce.sh
```

This regenerates the hypotheses report **from committed snapshots only** (no
network access, no GitHub API) and verifies it against the canonical copy:

1. Runs `hypotheses.py` (reads `snapshots/classifier_v1_labels.json` +
   `snapshots/tier_ab_corpus.json`) → writes `snapshots/hypotheses_report.txt`.
2. **Byte-compares** it with `snapshots/expected_output/hypotheses_report.txt` —
   a mismatch fails the run (exit 1) and prints the diff.
3. Runs `validate.py` — an **independent re-count** of the census numbers
   straight from the raw snapshots (no shared code with `hypotheses.py` except
   the Wilson/Fisher formulas), covering 9 consistency checks + the two negative
   controls (bitcoin, go-ethereum must be L0).

**Expected output (all must hold for exit 0):**

```
OK: hypotheses_report.txt byte-identical to canonical
validate.py — independent re-count (issue #63)
  [OK] ... (9/9 consistency checks + NEG controls)
PASS: independent re-count 9/9 consistent
== reproduction complete ==
```

## Additional verifiers

```bash
python3 validate.py      # independent re-count (same as inside reproduce.sh)
python3 trace_check.py   # every manuscript headline number → committed artifact, 0 gaps
```

## Tolerance

- **Byte-identical** is required for `hypotheses_report.txt` (no tolerance) —
  it is the canonical result artifact and the manuscript's headline numbers
  (6.9%, 66.7%, 75.0%, CIs, Fisher p, flip counts) are read off it.
- `validate.py` / `trace_check.py` must exit 0 with **0 failures / 0 gaps**.
- Fisher exact p is computed by the same one-sided hypergeometric sum in both
  `hypotheses.py` and `validate.py`; the report prints `4.225e-16` (manuscript
  rounds to `4.2e-16`).

## Scope of the one-command repro

The expensive, network-dependent pipeline steps ran once at snapshot time
**2026-09-01** and their outputs are committed under `snapshots/`:
- `search_repos.py` (topic search) → `search_results.json`, `tierb_candidates.json`
- `pin_corpus.py` (HEAD-pinning, parallel-8) → `tier_ab_corpus.json` (192 repos)
- `fetch_trees.py` (recursive git trees via GitHub API) → `manifest_tree_paths.json`
  (222 MB of tree JSONs live in `research/` and are **not** committed)
- `extract_manifests.py` → `consensus_dep_evidence.json`
- `classifier_v0.py` / `classifier_v1.py` (12-rule noise dictionary + gold
  standard; labels reviewed 2-pass by a single human annotator — disclosed in
  the submission) → `classifier_v0/v1_labels.json`

The one-command repro is intentionally the **no-network verification layer**:
it proves the committed artifacts produce the reported numbers byte-identically
and independently. Re-running the live pipeline (search → pin → fetch → classify)
requires GitHub API credentials and will reproduce the same numbers for the
2026-09-01 snapshot but is not part of `reproduce.sh`.
