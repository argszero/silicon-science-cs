# Issue #65 — eBPF in the Wild: A Source-Level Census of BPF Program Adoption in Open-Source Projects

Reproducibility specification for the submitted manuscript (PR `paper/issue-65`).

**Contribution level**: `theory+empirics` — 189-repo stratified census, gold-annotated classifier (2-pass, single annotator, disclosed), baseline (anchor ecosystem) + sensitivity analysis.

## One-command reproduction

```bash
bash reproduce.sh
```

This regenerates every report **from committed snapshots only** (no network access, no GitHub API) and verifies it against the canonical copy:

1. Runs `classifier_v1.py` (reads `snapshots/classifier_v0_labels.json` + `snapshots/program_types.json`) → writes `snapshots/classifier_v1_labels.json` + `snapshots/classifier_v1_stats.txt`.
2. Runs `hypotheses.py` (reads `classifier_v1_labels.json`) → `snapshots/hypotheses_report.txt`.
3. Runs `sensitivity.py` → `snapshots/sensitivity_report.txt`.
4. **Byte-compares** all three reports against `snapshots/expected_output/` — any mismatch fails the run (exit 1) and prints the diff.
5. Runs `validate.py` — an **independent re-count** of the census numbers straight from the raw snapshots (no shared code with the report generators except the Wilson/Fisher formulas), 13 consistency checks including the 3 NEG controls and 12 L0 controls.
6. Runs `trace_check.py` — every manuscript headline number traced to a committed artifact, 0 gaps allowed.

**Expected output (all must hold for exit 0):**

```
== reproduction complete: all byte-identical, 13/13 re-count OK, 0 gaps ==
```

## Tolerance

None — byte-identical. The pipeline is deterministic (no RNG, no network, no timestamps in outputs).

## Committed artifacts

| file | contents |
|---|---|
| `snapshots/tier_ab_corpus.json` | 189 repos, head_sha-pinned 2026-09-01, strata + stars |
| `snapshots/classifier_v0_labels.json` | raw L0/L1/L2 adjudication + evidence chains |
| `snapshots/program_types.json` | SEC()/Attach* program-type census (17 repos) |
| `snapshots/classifier_v1_labels.json` | final labels + program_type field |
| `snapshots/expected_output/` | canonical reports (byte-compare targets) |
| `classifier_v1.py` / `hypotheses.py` / `sensitivity.py` | report generators |
| `validate.py` | independent re-count (13 checks) |
| `trace_check.py` | manuscript-number → artifact trace (15 checks) |
| `manuscript.md` | the manuscript |

## Research workspace (git-ignored, not committed)

`research/` holds the full upstream pipeline: `search_repos.py` → `tierb_filter.py` → `pin_corpus.py` → `fetch_trees.py` (181 trees) → `extract_manifests.py` → `classifier_v0.py` → `program_types.py` → this committed area. The annotation protocol and evidence chains are in `research/ground_truth_r133.md`, program-type evidence in `research/notes_r132.md`, longitudinal cohort in `research/h4_longitudinal.md`. Reproduction from committed snapshots requires none of these.

## Gold-standard disclosure (single annotator, 2-pass)

Labels were produced by a single human annotator in two independent passes (Pass 2 re-derived from raw evidence chains without reference to Pass 1). Zero disagreements in the final set. Inter-rater agreement is not reportable with n=1 — disclosed; flip sensitivity (§5 of the manuscript) shows no conclusion depends on any single label.
