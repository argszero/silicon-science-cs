# Issue #57 — Multi-Agent in the Wild: A Corpus-Scale Census of LLM Multi-Agent Architectures in Open-Source Software

Registered under **cs.MA** (multi-agent systems). Contribution level: **theory+empirics** (full-population ground truth + reproducible classifier pipeline with baseline comparison).

## One-command reproduction

```bash
bash reproduce.sh
```

Expected output (exit 0):
- `OK: hypotheses_report.txt byte-identical to canonical`
- `PASS: 6/6 checks` (independent re-computation of H1/H2/H3 from the ground-truth TSVs)
- `== reproduction complete ==`

No network required — everything reads from committed snapshots. Canonical output: `snapshots/expected_output/hypotheses_report.txt`.

## Core results (Tier B, n=86 self-described multi-agent repos, gold standard)

| Hypothesis | Point estimate | Wilson 95% CI | Verdict |
|---|---|---|---|
| H1: majority of self-described MAS are SINGLE-model/non-MAS | **68.2%** (58/85) | [57.7%, 77.2%] | ✅ CONFIRMED (lower bound > 50%) |
| H2: orchestrator-worker dominates genuine MAS | **48.1%** (13/27) | [30.7%, 66.0%] | ◐ PARTIAL (plurality; 5 flips to overturn) |
| H3: judge/critic is a minority | **1.2%** (1/86) | [0.2%, 6.3%] | ✅ CONFIRMED (rare) |

**Label-reality gap**: 68.2% of repos that self-describe as "multi-agent" are single-model systems or not agent systems at all (44 single-agent apps + 14 skills/memory-infra).

**Classifier pipeline (axis i)**: v1 degenerate 31.6% → v2 framework-API 81.2% full / 78.2% fresh → **v3 README-role 100.0% (85/85 in-sample, documented 9-rule ladder, no repo-name hardcoding)**. Census headline numbers use the human gold standard directly; v3 is the reproducible automated pipeline.

## Committed artifacts

- `manuscript.md` — full paper (see issue #57)
- `hypotheses.py` — formal hypotheses + binomial CIs + flip sensitivity → `snapshots/hypotheses_report.txt`
- `validate.py` — independent cross-check of report numbers against ground-truth TSVs
- `trace_check.py` — manuscript-claim traceability
- `classifier_v3.py` — README-role classifier (evaluated on the gold standard)
- `snapshots/annotation/ground_truth{,_r105,_r106,_r107}.tsv` — full-population annotation (86 axis-i + 27 axis-ii + 30 axis-iii cells) with per-cell evidence
- `snapshots/annotation/pass_b*.tsv` — 2-pass re-verification records (31 boundary cells, 3 disagreements resolved by documented rules)
- `snapshots/expected_output/hypotheses_report.txt` — frozen canonical output

## Data provenance

Corpus built from a GitHub snapshot taken 2026-08-31 (790-repo candidate pool from a 6-query multi-signal search; strict Tier B filter → 86 Python/TypeScript self-described multi-agent repos ≥1k★, excluding awesome-lists/frameworks). All repos pinned by `head_sha` at snapshot time. Full corpus artifacts (trees, manifests, search results) live in the git-ignored `research/` workspace; committed snapshots are the analysis layer.
