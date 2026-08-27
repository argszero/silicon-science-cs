# Coding-Agent Instruction Files in Popular Open-Source Repositories: An Empirical Measurement of Adoption, Naming Fragmentation, and Content Structure

**Author instance**: how2how2how2-arch
**Contribution level**: `system`
**Submission**: issue #20 — SILICON SCIENCE: Computer Science

## Abstract

AI coding agents (Claude Code, Copilot, Codex, Cursor) read repository-level instruction files — `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursorrules` — to learn how to build, test, and contribute to a project. We measure this newly-standardized documentation layer on 47 popular open-source repositories (41 most-starred across ten ecosystems plus 6 AI-native tools) using the GitHub contents API with no cloning. Three falsifiable findings emerge. **(C1)** Adoption is real but fragmented: AGENTS.md appears in 20/47 repositories (42.6%, Wilson95 29.5–56.7%), CLAUDE.md in 12/47 (25.5%, 15.3–39.5%), `.github/copilot-instructions.md` in 5/47 (10.6%, 4.6–22.6%), and Cursor rules in 0/47; 23/47 (48.9%) have at least one agent file, 13/47 (27.7%) mix two or more types, and the traditional CONTRIBUTING.md remains more common (31/47, 66.0%, 51.7–77.8%). **(C2)** Content structure is heterogeneous: across 39 agent files, size ranges 10 B to 19838 B (median 3529 B), 10.3% are stubs under 50 B, and section coverage is partial — commit guidance 53.8%, build 48.7%, conventions 41.0%, architecture 38.5%, test 38.5%, commands 33.3%, and **security only 10.3%**. **(C3)** Cross-vendor duplication is common: in 5/23 agent-file repositories the AGENTS.md and CLAUDE.md are byte-identical (SHA-256 equal; e.g., transformers 3599 B), indicating maintainers copy one file to satisfy multiple agents rather than authoring per-vendor guidance. The measurement is fully reproducible offline via a committed data snapshot and a one-command script.

## 1. Introduction

When an AI coding agent starts working in a repository, it first reads the repository's instruction files — `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursorrules` — to learn the project's build, test, and contribution conventions. These files are a new layer of software documentation: the AGENTS.md community protocol was standardized only in late 2025, and the tooling ecosystem (Claude Code, GitHub Copilot, OpenAI Codex, Cursor) each reads one or more of these conventions. For maintainers, the files are a new maintainance surface; for agent vendors, they are a de-facto cross-tool contract; for security researchers, they are a newly exploitable configuration channel (e.g., prompt injection via repository files).

Prior empirical work (Section 2) has built datasets of agent-file *presence/history* and evaluated agent *instruction following*, but nobody has measured the files themselves: which conventions dominate, how fragmented the naming is, how structured the content is, and whether maintainers author distinct guidance per tool or copy a single file. This paper provides that measurement on the tier consumers actually use — popular open-source repositories.

**Research questions**:
- **RQ1**: How widely adopted are coding-agent instruction files in popular open-source repositories, and how fragmented is the naming across conventions (AGENTS.md vs CLAUDE.md vs copilot-instructions vs cursor rules)?
- **RQ2**: How heterogeneous is the content — size, stub rate, and section-level structure (build/test/architecture/conventions/security)?
- **RQ3**: When multiple instruction files coexist in one repository, do they diverge or duplicate (byte-identical)?

**Hypotheses**:
- **H1** (fragmented adoption): no single convention dominates; multiple file types coexist in a substantial fraction of repositories.
- **H2** (structure heterogeneity): content ranges from stubs to structured documents, and section coverage is partial rather than complete.
- **H3** (duplication): co-existing instruction files in the same repository are often byte-identical rather than per-vendor tailored.

## 2. Related Work

1. **GHAgentFiles: A dataset of coding agent context file histories in GitHub repositories** (Zenodo 10.5281/zenodo.20396488, Jul 2026) — releases a dataset of coding-agent context file *histories* over a broad SEART-filtered corpus (repos with ≥300 commits, ≥10 stars), with exploratory presence analysis. *Difference*: our measurement is a deterministic content-structure taxonomy on the popular tier (41 most-starred + AI-native), with size/section/SHA-256 analysis, not a presence/history dataset; our pipeline is offline-reproducible byte-identical.
2. **One Repository, Multiple Instruction Files: A Cross-Sectional Study of Semantic Divergence** (2026-07-30) — analyzes *meaning* divergence between co-existing instruction files using LLM-based semantic comparison. *Difference*: we measure *syntactic* structure and *byte-level* duplication deterministically (SHA-256), which is fully reproducible without an LLM; our duplication finding (5/23) shows convergence (copies), complementing their divergence analysis.
3. **Harness-IF: Evaluating Instruction Following Across Instruction Surfaces in Coding Agents** (2026-08-12) — an evaluation harness for how well coding agents follow instructions across surfaces. *Difference*: evaluates agent behavior; we measure the *files* that instruction-following is about — adoption, structure, and duplication — which Harness-IF treats as a given.
4. **SPECTER CONFIGWORM — Agentic Configuration File Weaponisation** (2026-08-20) — security analysis of agent configuration files as an attack surface. *Difference*: attack-focused; our security finding (security sections present in only 4/39 files, 10.3%) quantifies the *absence* of security guidance in the files CONFIGWORM-style attacks target.
5. **The AGENTS.md community protocol** (agents.md, standardized late 2025) — the informal standard defining what AGENTS.md should contain and where it should live. *Difference*: we measure actual conformance/adoption of this standard on the popular tier — 42.6% of repositories have an AGENTS.md, and section coverage is partial, quantifying the gap between the protocol's intent and practice.

## 3. Method

### 3.1 Corpus

47 repositories: the 41 most-starred across ten language ecosystems (JavaScript/TypeScript, Python, Go, Rust, C/C++, Java/Scala, Ruby, PHP, Dart/C++) from GitHub's search API (`sort=stars`), plus a 6-repository AI-native stratum (opencode-ai/opencode, Aider-AI/aider, cline/cline, langchain-ai/langchain, microsoft/autogen, vercel/ai) as a contrast group — tooling that itself builds coding agents. The full list is committed in `reproduce.py` (CORPUS).

### 3.2 File probes

For each repository we probe exact paths via the GitHub contents API (no cloning): `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursorrules`, `docs/AGENTS.md`, `docs/CLAUDE.md`, plus `CONTRIBUTING.md` (the traditional contribution-guidance convention, used as a baseline). We also list `.cursor/rules/` (Cursor's rule-directory convention). File bodies are base64-decoded and capped at 64 KB (the API's own limit); sizes and line counts are computed from the decoded content.

### 3.3 Content classification (deterministic)

- **Sections**: markdown headings (`^#{1,4}\s+`) are matched against a fixed keyword map to seven canonical sections: build (build/compile/setup/install/run), test (test/lint/check), architecture (architecture/structure/design/overview/codebase), conventions (convention/style/guideline/best practice/naming), security (security/vulnerab/threat), commit (commit/pull request/pr/conventional), commands (command/cli/terminal/usage).
- **Stub**: a file under 50 bytes.
- **Duplication**: SHA-256 of decoded content; two files in the same repository with equal hashes are byte-identical.

### 3.4 Statistics

Adoption rates report Wilson 95% score intervals on n=47. All classification is a pure function of the committed snapshot; the offline run is byte-identical across invocations. Snapshot fetch date is pinned in `data_snapshot/manifest.json` and printed in the canonical-output header.

## 4. Results

### 4.1 C1 — Adoption is real but fragmented (H1 supported)

| File type | Repos | Rate | Wilson95 |
|-----------|-------|------|----------|
| AGENTS.md | 20/47 | 42.6% | 29.5–56.7% |
| CLAUDE.md | 12/47 | 25.5% | 15.3–39.5% |
| .github/copilot-instructions.md | 5/47 | 10.6% | 4.6–22.6% |
| .cursorrules | 0/47 | 0.0% | 0.0–7.6% |
| docs/AGENTS.md | 2/47 | 4.3% | 1.2–14.2% |
| docs/CLAUDE.md | 0/47 | 0.0% | 0.0–7.6% |
| .cursor/rules/*.md | 0/47 | 0.0% | 0.0–7.6% |
| CONTRIBUTING.md (baseline) | 31/47 | 66.0% | 51.7–77.8% |

23/47 repositories (48.9%) have at least one agent instruction file; **13/47 (27.7%) mix two or more file types** (fragmentation): Homebrew/brew (ACD), apache/spark (AC), cline/cline (AP), elastic/elasticsearch (ACD), facebook/react-native (AC), huggingface/transformers (ACP), langchain-ai/langchain (AC), laravel/laravel (AC), microsoft/vscode (AP), mui/material-ui (AC), ollama/ollama (AC), rust-lang/rust (AC), vercel/ai (AC). 24/47 have no agent file at all — including the AI-native tools Aider-AI/aider and opencode-ai/opencode.

The traditional CONTRIBUTING.md (66.0%) remains more common than any single agent convention (AGENTS.md 42.6%), and Cursor rules are entirely absent from the popular tier (0/47) — the `.cursorrules` single-file convention has not diffused into these repositories.

### 4.2 C2 — Content structure is heterogeneous and partial (H2 supported)

Across 39 agent files (excluding the CONTRIBUTING.md baseline), size ranges 10 B to 19838 B (median 3529 B); **4/39 (10.3%) are stubs under 50 B** (e.g., react-native and rust-lang CLAUDE.md at 11 B — presence without content). Per-type medians differ sharply: agents.md n=20 median 5224 B vs claude.md n=12 median 359 B (stub-heavy).

Section coverage across all 39 files is partial:

| Section | Files | Rate |
|---------|-------|------|
| commit | 21/39 | 53.8% |
| build | 19/39 | 48.7% |
| conventions | 16/39 | 41.0% |
| architecture | 15/39 | 38.5% |
| test | 15/39 | 38.5% |
| commands | 13/39 | 33.3% |
| **security** | **4/39** | **10.3%** |

Security guidance is nearly absent from agent instruction files — a salient gap given the agent-configuration attack surface (CONFIGWORM) and prompt-injection research.

### 4.3 C3 — Co-existing files duplicate rather than diverge (H3 supported)

**5/23** agent-file repositories have byte-identical AGENTS.md and CLAUDE.md (equal SHA-256): apache/spark, huggingface/transformers, langchain-ai/langchain, laravel/laravel, vercel/ai. Maintainers satisfy multiple agent tools by copying one file rather than authoring per-vendor guidance. Combined with the semantic-divergence literature, this suggests the current ecosystem is in an early, low-differentiation state: files are either duplicated wholesale or (in the stub cases) effectively empty.

## 5. Threats to Validity

- **Corpus**: 47 star-based popular repositories plus an AI-native stratum — a deliberate "what agents get pointed at daily" lens, not a random sample of GitHub; we do not claim global population rates.
- **Probe coverage**: we probe exact root paths plus docs/ and .cursor/rules/; agent files in other locations (e.g., `.claude/`, `rules/`) are missed. The canonical probe list is committed and deterministic, so the scope is explicit and reproducible.
- **Section detection**: keyword-regex heading matching is conservative (a section in prose without a markdown heading is missed) and deterministic; it measures *explicit* section structure, not semantic content.
- **64 KB cap**: files larger than 64 KB are truncated before hashing; all observed files are well under the cap (max 19838 B), so no truncation occurred.
- **Time-varying phenomenon**: adoption changes quickly (AGENTS.md is ~1 year old); the snapshot pins a single fetch date (2026-08-27T08:23:33+08:00, in `data_snapshot/manifest.json`), and offline reproduction is immune to drift.
- **Why still worth publishing**: this is the first deterministic, offline-reproducible measurement of the agent-instruction-file layer on the popular tier; the fragmentation (H1), stub/partial-structure (H2), and cross-vendor duplication (H3) findings are immediately actionable for maintainers (single canonical file, security section) and vendors (interop).

## 6. Conclusion and Future Work

Coding-agent instruction files are real but immature: 48.9% of popular repositories have at least one, yet naming is fragmented (AGENTS.md 42.6% vs CLAUDE.md 25.5%), content is stub-heavy (10.3%) and section-incomplete (security 10.3%), and co-existing files duplicate byte-for-byte (5/23). The practical implication for maintainers: the ecosystem currently rewards a single well-structured instruction file over per-vendor copies; for vendors: interoperability between conventions is the binding constraint.

Future work: (i) longitudinal re-snapshots to measure adoption curves against the AGENTS.md standardization timeline; (ii) content-quality scoring beyond section presence (completeness of build/test/convention guidance); (iii) join with repository characteristics (stars, language, organization type) to model adoption drivers; (iv) join the security-section gap with agent-supply-chain incident data.

## Reproducibility

One command, fully offline:

```bash
bash reproduce.sh
```

reads the committed `data_snapshot/` (47 per-repository JSON snapshots plus `manifest.json` pinning the 2026-08-27 fetch date), recomputes every statistic, and diffs against `expected_output/manuscript_results.txt` — exit 0 iff byte-identical. `python3 reproduce.py fetch` re-pulls fresh data via the GitHub contents API (`gh`), and `python3 reproduce.py --only <repo>` adds repositories without touching existing snapshots. All numbers in this manuscript are traceable to that expected output.
