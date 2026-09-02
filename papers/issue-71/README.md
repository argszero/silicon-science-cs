# Issue #71 — WebGPU in the Wild: A Source-Level Census of WebGPU Adoption in Web Open-Source Software

Reproducibility specification for the submitted manuscript (PR `paper/issue-71`).

**Contribution level**: `theory+empirics` — 182-repo stratified population census of a web-platform
GPU API (multi-system measurement), gold-annotated classifier (single-annotator 2-pass, disclosed),
within-corpus WebGL migration baseline (every corpus repository gets a GPU-API state: WebGL-only /
WebGPU / dual), mediation stratification (raw API vs engine-mediated vs execution-provider),
fallback-morphology instrument (dual-renderer count), baseline comparisons (Tier A anchors by
construction; WebGL majority within corpus; #68 MCP / #65 eBPF / #61 PQC cross-census rates) +
flip-sensitivity analysis.

## One-command reproduction

```bash
bash reproduce.sh
```

This regenerates every report **from committed snapshots only** (no network access, no GitHub API) and
verifies it against the canonical copy:

1. Runs `hypotheses.py` (reads `snapshots/classifier_v2_71.json` +
   `snapshots/classifier_v0_71.json` + `snapshots/tier_ab_corpus71.json` +
   `snapshots/wg_manifest_evidence71.json`) → `snapshots/hypotheses_report.txt`.
2. Runs `sensitivity.py` (reads the same snapshots + `snapshots/tree_status.json`) →
   `snapshots/sensitivity_report.txt`.
3. **Byte-compares** both reports against `snapshots/expected_output/` — any mismatch fails the run
   (exit 1) and prints the diff.
4. Runs `validate.py` — an **independent re-count** of the census numbers straight from the raw
   snapshots (no shared code with the report generators except the Wilson/Fisher formulas),
   19 consistency checks (corpus composition, strata quotas, head-SHA pinning, NEG dual-L0 purity,
   Tier-A calibration, headline rate + CI, WebGL baseline counts, WebGPU share of GPU users, roles,
   dual-renderer count, per-stratum density, L1 set + upper bound, H1 Fisher concentration,
   S3-AI non-elevation, gold-pass anchors, tree coverage, liveness, language mix, engine-dep carrier
   census).
5. Runs `trace_check.py` — every manuscript headline number traced to a committed artifact (report
   text, gold JSON, classifier JSON, tree status, appendix table), 0 gaps allowed.

**Expected output (all must hold for exit 0):**

```
== reproduction complete: all byte-identical, 19/19 re-count OK, 0 gaps ==
```

## Tolerance

None — byte-identical. The pipeline is deterministic (no RNG, no network, no timestamps in outputs).

## Committed artifacts

| file | contents |
|---|---|
| `snapshots/tier_ab_corpus71.json` | 182 repos, head_sha-pinned 2026-09-02, strata + stars + language + archived |
| `snapshots/classifier_v2_71.json` | classifier v2 (post-gold-pass): per-repo WebGPU level (L0/L1/L2) + role (render/compute/both) + WebGL level |
| `snapshots/classifier_v0_71.json` | classifier v0 evidence basis (pre-gold) — used for the adjudication-sensitivity bound |
| `snapshots/gold_pass1_71.json` | gold-standard pass-1 evidence: decisive-file signals per positive; code-search results for L1/L0 adjudications (vscode discovery paths) |
| `snapshots/wg_manifest_evidence71.json` | manifest scan evidence (engine-dep carrier census, `@webgpu/*` types) |
| `snapshots/tree_status.json` | recursive-tree fetch status at pinned HEAD (182/182 ok, 0 truncated) |
| `snapshots/expected_output/` | canonical reports (byte-compare targets) |
| `hypotheses.py` / `sensitivity.py` | report generators |
| `validate.py` | independent re-count (19 checks) |
| `trace_check.py` | manuscript-number → artifact trace (0 gaps) |
| `manuscript.md` | the manuscript |

## Research workspace (git-ignored, not committed)

`research/` holds the full upstream pipeline: `search_repos_71.py` (domain topic queries only — never
outcome-gated) → `tierb_filter_71.py` (exclusion/REMAP log `tierb_stats71.txt`) → `pin_corpus_71.py`
→ `fetch_trees_71.py` → `scan_71.py` (path prescreen + manifest scan) → `webgl_baseline_71.py`
(C4 WebGL channel) → `content_probe_71.py` + `c2_codesearch_71.py` → `classifier_v0/v1/v2_71.py` →
`gold_pass1_71.py` → hypotheses → sensitivity → manuscript. The 4-channel signal dictionary
(`wg_signal_dict_v1.md`), the 10-rule noise dictionary, the stratum REMAP log, and the
single-annotator 2-pass gold protocol (including the pass-2 `microsoft/vscode` L1→L2 discovery) are
documented there. Reproduction from committed snapshots requires none of these.

## Gold-standard disclosure (single annotator, 2-pass)

Labels were produced by a single annotator in two independent passes. Pass 2 re-verified every
positive at pinned HEAD (decisive-file re-grep), code-searched all L1 candidates for raw
`navigator.gpu`, and re-checked 6 L0 controls. Pass 2 independently caught one real Pass-1 error
(`microsoft/vscode` was L1 after a single-file probe missed raw WebGPU in
`src/vs/editor/browser/gpu/` — production GPU-accelerated viewport rendering; code search found
`gpuDisposable.ts`/`rectangleRenderer.ts`/`viewLinesGpu.ts` → L2). Inter-rater agreement is not
reportable with n=1 — disclosed; flip sensitivity (sensitivity_report.txt) shows no conclusion
depends on any single label (headline needs 61+ re-annotations for the Wilson upper bound to cross
50%; GPU-user parity needs ≥12 dual- or ≥23 L0→WebGPU flips; S1 concentration survives ≥3 S1 flips).
