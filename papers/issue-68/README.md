# Issue #68 — MCP in the Wild: A Source-Level Census of Model Context Protocol Adoption in Open-Source Software

Reproducibility specification for the submitted manuscript (PR `paper/issue-68`).

**Contribution level**: `theory+empirics` — 187-repo stratified population census (multi-system
measurement), gold-annotated classifier (single-annotator 2-pass, independently re-derived, disclosed),
baseline comparison (AI-tooling anchors by construction; MCPZoo 2607.11086 supply-side census; eBPF
census #65 rate contrast) + flip-sensitivity analysis.

## One-command reproduction

```bash
bash reproduce.sh
```

This regenerates every report **from committed snapshots only** (no network access, no GitHub API) and
verifies it against the canonical copy:

1. Runs `hypotheses.py` (reads `snapshots/gold_final.json` + `snapshots/tier_ab_corpus.json` +
   `snapshots/h4_repo_meta.json` + `snapshots/h3_evidence.json`) → `snapshots/hypotheses_report.txt`.
2. Runs `sensitivity.py` → `snapshots/sensitivity_report.txt`.
3. **Byte-compares** both reports against `snapshots/expected_output/` — any mismatch fails the run
   (exit 1) and prints the diff.
4. Runs `validate.py` — an **independent re-count** of the census numbers straight from the raw
   snapshots (no shared code with the report generators except the Wilson/Fisher formulas),
   15 consistency checks (corpus composition, L2 roles, headline rate + CI, H1 Fisher, per-stratum,
   H2 purity CI, H2-refined morphology, NEG, Tier-A exclusion, downgrade audit, H3 SDK constants,
   H3 codesearch totals, H4 recency/liveness, robustness).
5. Runs `trace_check.py` — every manuscript headline number traced to a committed artifact,
   0 gaps allowed.

**Expected output (all must hold for exit 0):**

```
== reproduction complete: all byte-identical, 15/15 re-count OK, 0 gaps ==
```

## Tolerance

None — byte-identical. The pipeline is deterministic (no RNG, no network, no timestamps in outputs).

## Committed artifacts

| file | contents |
|---|---|
| `snapshots/tier_ab_corpus.json` | 187 repos, head_sha-pinned 2026-09-02, strata + stars |
| `snapshots/gold_final.json` | gold-standard 2-pass result: 41 L2 (roles server/client/both), pass-2 deltas |
| `snapshots/h4_repo_meta.json` | GitHub repo metadata for the 41 L2 adopters (created/pushed/archived) |
| `snapshots/h3_evidence.json` | spec-version evidence: SDK constants, code-search tallies, app-level pins |
| `snapshots/expected_output/` | canonical reports (byte-compare targets) |
| `hypotheses.py` / `sensitivity.py` | report generators |
| `validate.py` | independent re-count (15 checks) |
| `trace_check.py` | manuscript-number → artifact trace (25 checks) |
| `manuscript.md` | the manuscript |

## Research workspace (git-ignored, not committed)

`research/` holds the full upstream pipeline: `search_repos.py` → `tierb_filter.py` → `pin_corpus.py`
→ `fetch_trees.py` (187/187 trees) → `extract_manifests.py` → `classifier_v0.py` → gold passes 1-2
(`ground_truth_r141.md`, `ground_truth_final.md`) → hypotheses → sensitivity. The annotation protocol,
per-repo evidence basis ([M] manifest / [S] in-tree source / [C] content probe / [N] name rule), the
9-rule noise dictionary, and the pass-2 independent re-derivation are documented there. Reproduction
from committed snapshots requires none of these.

## Gold-standard disclosure (single annotator, 2-pass)

Labels were produced by a single human annotator in two independent passes (Pass 2 re-derived
candidates from raw manifest evidence without reference to Pass 1). Pass 2 independently caught one
real Pass-1 error (`coze-dev/coze-studio`: platform-MCP-API consumer, not protocol adopter — noise
rule 8) and confirmed the Pass-1 content-probe downgrades (`elizaOS/eliza`, `GoogleChrome/lighthouse`).
Inter-rater agreement is not reportable with n=1 — disclosed; flip sensitivity (sensitivity_report.txt)
shows no conclusion depends on any single label (headline needs 7+ re-adjudicated positives to move
below 20%; H1 needs 11+ AI-strata flips to cross p = 0.05).
