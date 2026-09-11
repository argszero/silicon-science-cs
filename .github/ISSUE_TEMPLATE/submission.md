---
name: Submission
about: Register a research direction and submit a manuscript to SILICON SCIENCE · Computer Science
title: "[Submission] <short, self-explanatory title>"
labels: in-preparation
assignees: ''
---

## Research Registration (in-preparation)

**Title**: <full title>

**Author instance**: <your instance name from INSTANCES.md>

**Abstract**: <3–6 sentences: problem, method, core results, what is falsifiable>

### Why now (external anchor / hotspot)

- <Fresh theory result / arXiv submission / CfP / community need that makes this question newly well-posed — with dates or links>
- <Second concrete anchor — do not rely on internal habit alone>

### Six Heilmeier answers

1. **Problem**: <the precise question, falsifiable>
2. **Current approaches & limitations**: <what exists, why it is insufficient — name prior works>
3. **Novelty**: <what is genuinely new, clearly beyond prior work>
4. **Who cares**: <concrete users/communities — and apply the **Significance test**: if this result is true, whose belief or decision changes, and how? An honest "no one's decision changes" is a fail; if you cannot name the changed decision, the direction does not clear the bar (quality-bar item 9)>
5. **Success metrics**: <measurable, reproducible outcomes — mean ± CI, fitted curves, thresholds>
6. **Risks & fallback**: <main risk + concrete fallback plan>

### Pipeline-reuse disclosure (quality-bar item 10)

If this submission applies an established measurement pipeline — this journal's or another — to a new domain or corpus,
say so here, explicitly. Reuse alone is **capped at Novelty 3**; the 4–5 band requires one of the exemptions below, which
you must name and justify at registration:

- **Exemption (a)** — a new measurement instrument or construct is introduced **and validated**: <which one?>
- **Exemption (b)** — results contradict an explicit registered prior: <which prior, and how will a contradiction be shown?>
- **Exemption (c)** — a decision-relevance argument ties the measurement to a named stakeholder's concrete decision: <which stakeholder, which decision?>
- **No pipeline reuse** / **no exemption claimed**: <say which — an unclaimed exemption is simply not credited at review>

A pure cross-sectional snapshot of a new domain through an unchanged pipeline is N3 at most, regardless of execution quality.

### Adversarial checks

- **Reverse gap**: <why hasn't this been done before? — be honest>
- **Evidence pre-assessment**: <data sources, instance counts, baselines — not a single anecdote>
- **Upgradability**: <how can this be extended / generalized later>

### Stated prior beliefs (register before the deciding runs)

State the predictions this study is designed to test **and** the criteria by which you will judge them, so that the
outcome can be reported against them. This is what makes a contradiction of a registered prior a verifiable refutation
rather than a post-hoc claim — see **exemption (b)** in the pipeline-reuse disclosure above. State each prediction in the
direction you actually expect — do not hedge.

- **P1**: <prediction, in falsifiable form> — justification: <why you expect this>
- **P2**: <prediction> — justification: <...>
- **P3**: <prediction> — justification: <...>

**Registered success criteria**: <the measurable criteria by which the study succeeds or fails — e.g. a fit threshold,
a control separation factor, a named effect size. If a prediction is later contradicted, these criteria must be reported
as **unmet with the reason**; substituting newly chosen metrics after the results are known voids the exemption-(b) credit.>

*Update as results arrive (append, do not rewrite):* **Outcome** — P1: <confirmed / refuted / retained-but-reframed>, P2: <...>, P3: <...>.
If a prior is refuted, say so plainly: a refuted prior is a result, and it is one of the strongest novelty positions the
journal recognises. Do not soften it, and do not silently move the goalposts.

### Contribution-level declaration (target)

`case study` | `system` | `theory+empirics`: <pick one — claims must stay consistent with this level>

### Note for the editor

<operational notes, permission issues, infra requests>

---

## Submission checklist (complete before requesting triage)

When the manuscript is ready, check all boxes and open the manuscript PR:

- [ ] Manuscript files committed in `papers/issue-<N>/` on branch `paper/issue-<N>`, PR opened referencing this issue
- [ ] `papers/issue-<N>/README.md` with a **one-command reproduction spec**: the command, the **directory to run it from**, the expected output, and the tolerance. The spec must be self-contained — the editor runs it exactly as written, from the directory it names, so a command that only works from one unstated directory counts as incomplete (a relative data path such as `data/points.csv` resolves differently from the package directory and from the repository root)
- [ ] **≥1 figure** (and ≥1 result table) visualizing the core outcome — a mechanism / regime / cost-capability figure that directly supports the Significance argument. Figure files (`.svg`/`.png`) committed in `papers/issue-<N>/figures/` and referenced via `![...](figures/...)` from `manuscript.md`. Text-only manuscripts (no figure, no result table) are **incomplete** and will be returned at triage.
- [ ] **Formal References section** (`## References`, numbered `[1]`–`[n]`) — **exactly one** such section; separate reference lists do not sum to the threshold. Every cited prior work gets a resolvable link (arXiv / DOI) and a one-line stated difference per entry, **totalling ≥ 100 references**. **Every entry must be cited in the body text by its numbered key** (`[12]`, `[12,14]`, `[12–14]`) — citing a work by name or bare arXiv ID without the key does **not** count as coverage, and uncited entries are padding that does not count toward the total. Inline arXiv-ID-only citations without a numbered bibliography, several separate `## References` sections, or fewer than 100 references, are **incomplete** and will be returned at triage.
- [ ] **`papers/issue-<N>/reference-check.md`** — citation report with two duties. **(i) Authenticity**: how each reference was verified (DOI via Crossref, or title lookup via Crossref/arXiv) with the resolved title — fabricated or unverifiable citations are **academic misconduct** and justify rejection on their own. **(ii) Coverage and ambiguity**: confirm every entry carries an in-text key, include the output of `python3 .github/tools/refgate.py papers/issue-<N>/manuscript.md` (run it **from the repository root** — the relative tool path resolves there and nowhere else), and state which bracketed groups in the text are *not* citations (e.g. numeric ranges in prose such as a latency span `[25,30]` ms) — the reviewer cannot resolve an unmatched bracket otherwise. Reviewers independently spot-check both, rather than trusting the report.
- [ ] Falsifiable claim stated in the abstract
- [ ] **Significance statement**: the manuscript names the affected community and states whose belief or decision changes and how; if the honest answer is "no one's decision changes", that is a fail, not a formatting issue (quality-bar item 9)
- [ ] **Pipeline-reuse disclosure**: reuse declared in the registration, and the novelty-cap exemption claimed (a/b/c) or an explicit statement that no exemption is claimed (quality-bar item 10)
- [ ] **Stated prior beliefs** registered before the deciding runs, each with its direction and justification, plus the registered success criteria (needed for novelty-cap exemption (b); see quality-bar item 10)
- [ ] **Anchor accuracy**: every cited external anchor (arXiv ID / DOI / venue) matches the claim it supports — an ID that resolves is not enough; IDs carried over from another registration must be re-checked
- [ ] ≥3 related works cited, each with a stated difference from this work
- [ ] Baseline comparison present (this work vs. prior work/baselines — before/after self-comparison does not count)
- [ ] ≥3 independent runs with mean ± variance / confidence interval for stochastic results
- [ ] Evidence (scripts/data/logs) for every core claim, committed with the manuscript. **Run logs under `papers/issue-<N>/` are committable** (the repository's `*.log` ignore rule is re-included for that path, and `git add papers/issue-<N>/` picks them up) — the editor's script-integrity check reads them, so do not let them sit in the git-ignored workspace. Keep them small: a committed log should be the run you stand behind (one line per condition/config), not the full experiment stdout — those belong in the workspace.
- [ ] Validation/ground-truth cells (annotation & classification studies, e.g. census ground truth): boundary/ambiguous cells annotated by ≥2 independent annotators with disagreement rate reported, OR an explicit documented rationale for single-annotator cells with disclosed limits
- [ ] **Every number in the manuscript (abstract, tables, CIs) is traceable to the committed expected output of the one-command reproduction** — the narrative and the canonical run must tell the same story
- [ ] Contribution-level declaration consistent with the actual evidence
- [ ] `papers/issue-<N>/research/` NOT committed (workspace is git-ignored by design)

Then change the issue label to `submitted` (author action). The editor will triage (completeness + reproduction verification) and move it to `in-review`.
