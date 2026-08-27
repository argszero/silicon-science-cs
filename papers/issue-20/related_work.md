# Related Work — Issue #20: Coding-Agent Instruction Files in Popular Open-Source Repositories

Five concrete related works are compared; each entry states what the prior work does,
its limitation, and the specific difference of this paper.

## 1. GHAgentFiles: A dataset of coding agent context file histories in GitHub repositories (Zenodo 10.5281/zenodo.20396488, Jul 2026)

- **What**: releases a dataset of coding-agent context file *histories* over a broad
  SEART-filtered corpus (repos with ≥300 commits, ≥10 stars, active last year), with
  exploratory presence analysis via the `cofee` tool.
- **Limitation**: a presence/history dataset over a huge corpus; no deterministic
  content-structure taxonomy; no popular-tier focus (the tier consumers' agents
  actually read daily).
- **Our difference**: a deterministic content-structure measurement on the popular
  tier (41 most-starred + AI-native stratum) with size/section/SHA-256 analysis,
  fully reproducible offline byte-identical (their dataset is a compressed artifact,
  not a reproducible pipeline).

## 2. One Repository, Multiple Instruction Files: A Cross-Sectional Study of Semantic Divergence (2026-07-30)

- **What**: analyzes *meaning* divergence between co-existing instruction files using
  LLM-based semantic comparison.
- **Limitation**: LLM-dependent analysis — not rule-reproducible; measures divergence
  (differences), not convergence (duplication) or structure.
- **Our difference**: we measure *syntactic* structure and *byte-level* duplication
  deterministically (SHA-256), fully reproducible without an LLM; our C3 finding
  (5/23 byte-identical AGENTS.md ≡ CLAUDE.md) shows the ecosystem currently
  *converges* by copying — a complement to their divergence analysis.

## 3. Harness-IF: Evaluating Instruction Following Across Instruction Surfaces in Coding Agents (2026-08-12)

- **What**: an evaluation harness for how well coding agents follow instructions
  across surfaces.
- **Limitation**: evaluates agent *behavior*; treats the instruction files as a given
  input — it does not measure the files themselves.
- **Our difference**: we measure the files that instruction-following is about —
  adoption (C1), structure (C2), duplication (C3) — the input layer Harness-IF
  evaluates against.

## 4. SPECTER CONFIGWORM — Agentic Configuration File Weaponisation (2026-08-20)

- **What**: security analysis of agent configuration files as an attack surface
  (weaponization, prompt injection via repository files).
- **Limitation**: attack-focused; does not quantify how widespread the *absence* of
  defensive guidance is.
- **Our difference**: our C2 security-section finding (security sections in only
  4/39 agent files, 10.3%) quantifies the guidance gap in the very files
  CONFIGWORM-style attacks target.

## 5. The AGENTS.md community protocol (agents.md, standardized late 2025)

- **What**: the informal standard defining what AGENTS.md should contain (build/test/
  conventions guidance) and where it should live.
- **Limitation**: prescriptive; no measurement of actual conformance or adoption.
- **Our difference**: we measure actual adoption (42.6% of popular repos have
  AGENTS.md) and section coverage (build 48.7%, test 38.5%, security 10.3%),
  quantifying the gap between the protocol's intent and practice.
