# Related Work — Issue #15: Conventional Commits in the Wild

Each entry: what it does → limitation → **our difference**.

1. **Conventional Commit Message Generation: How Far Are We?** (Zenodo
   DOI 10.5281/zenodo.19252792, 2026-03-27) — evaluates LLM-based
   generation of CC-format commit messages against a benchmark; treats CC
   as the target format.
   *Limitation*: never measures how widely the real world complies — the
   benchmark assumes the convention's reach.
   **Our difference**: we measure whether real repositories actually produce
   CC-format messages at all, at repository scale (19 repos, 5,700 commits),
   and decompose the result by tier and by tooling presence.

2. **Automatic Commit Message Generation: A Critical Review and Directions
   for Future Work** (TSE 2024) — the field's critical review; entirely
   generation-centric; flags real-world commit-message *structure*
   measurement as an open direction.
   *Limitation*: no empirical structure measurement itself.
   **Our difference**: we supply the measurement — a deterministic,
   reproducible CC-conformance statistic over a current corpus, plus a
   tooling-contrast analysis.

3. **ApacheCM dataset** (2026-03-01) — large dataset of Apache-project
   commit messages for generation/analysis research.
   *Limitation*: a data artifact; no conformance measurement or
   specification-derived classification.
   **Our difference**: a spec-derived three-tier classifier and an
   association analysis with tooling and release metadata — not just data,
   but a measurement with a falsifiable claim.

4. **commitlint / semantic-release / release-please / commitizen / cz-conventional
   (primary tooling sources, docs)** — the enforcement and release
   infrastructure of the CC ecosystem; define what compliance *should* be.
   *Limitation*: document the norm, never the actual; enforcement presence
   in a repo is a config fact, not a compliance fact.
   **Our difference**: we quantify the gap between "tooling configured" and
   "history conforms" (nestjs/nest 53.3% shows presence ≠ enforcement), and
   between "structured discipline" and "CC conformance" (numpy 80.7%
   structured, 0% CC).

5. **The Conventional Commits specification** (conventionalcommits.org) —
   the ground-truth grammar (open type set, optional scope, `!`/`BREAKING
   CHANGE` markers).
   *Limitation*: informal grammar leaves room for interpretation; no
   canonical measurement procedure.
   **Our difference**: we fix a deterministic, documented interpretation
   (three-tier classifier; canonical-type set; exact regex) so the
   measurement is reproducible and comparable.
