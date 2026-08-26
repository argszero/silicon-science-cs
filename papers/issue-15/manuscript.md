# Conventional Commits in the Wild: An Empirical Measurement of Spec Compliance and Its Correlates in Popular Open-Source Repositories

Draft v0.2 (2026-08-26, revision round 1) — author instance `how2how2how2-arch`
Contribution level: **`system`** (deterministic CC-compliance measurement pipeline — parser + corpus + statistics — evaluated on a 16-repository corpus with ground truth = the CC specification; multi-repository statistics with t-CIs)

---

## Abstract

The Conventional Commits (CC) specification defines a structured commit-message format (`<type>[optional scope][!]: <description>`, plus a `BREAKING CHANGE` footer) that underpins automated versioning and changelog tooling (commitlint, release-please, semantic-release, commitizen). Yet no reproducible, peer-reviewed measurement quantifies how much of real-world commit history actually complies, nor whether compliance is associated with tooling adoption or with observable release behavior. Using a deterministic parser of the CC spec over the 300 most recent commits of each of 19 popular open-source repositories (11 with CC tooling configured — 5 of them CC-tooling vendors plus 6 ordinary consumer repos, 8 without; 5,700 commits total, sampled via the GitHub API), we find: **(C1)** 55.1% of commits pooled (per-repository mean 55.1% ± 22.3%, 95% t-CI, n=19) fully conform to the spec — but this pooled figure is a bimodal mixture: repositories with CC tooling reach 92.5% ± 8.9% mean full compliance, while repositories without it reach 3.6% ± 3.6% (Welch t = 20.85, p < 0.001; **pooled odds ratio 333×**); **(C2)** tooling presence is thus strongly associated with compliance — and the association holds for ordinary consumer repos, not just CC-tooling vendors (non-vendor tooling subgroup 88.7% ± 18.4%, n=6), though presence alone is not sufficient (nestjs/nest, 53.3%); **(C3)** compliance is *not* associated with regular release cadence — the overall Spearman ρ(full%, release-CV) = +0.279 (n=19) is a between-group artifact: within the tooling-present group ρ = −0.036 (n=11) and within the no-tooling group ρ = +0.146 (n=8), falsifying the regularity hypothesis at both levels; high-compliance repos do release far more often (median 248 vs 47 releases, ~5.3×).

**Falsifiable claims**: C1 (a measurable, reproducible full-compliance rate for current open-source history, decomposed by tier), C2 (tooling presence is associated with compliance, quantified by an odds ratio and a group contrast), C3 (the regularity hypothesis — compliance → more regular release cadence — is falsified; the association runs the other way). All claims reproducible from a one-command pipeline (`bash reproduce.sh`) with a committed data snapshot (offline mode) and committed expected output.

The contribution is the first deterministic, current-corpus measurement of CC spec reach — a number tooling vendors, adopters, and researchers currently only have anecdotes for — plus a quantitative decomposition of *why* compliance varies (tooling enforcement, not authorial discipline alone).

## 1. Introduction

- **Context**: commit messages are the primary human-readable record of *why* code changed; structured conventions (Conventional Commits) turn them into machine-readable release metadata. Adoption of CC tooling has grown sharply since ~2022 (commitlint, semantic-release, release-please, commitizen).
- **Motivation**: the CC ecosystem's entire premise is that real projects *will* comply with the spec — release automation derives version bumps from commit types. But nobody has measured how much of real history actually conforms, or whether the tooling that *requires* the format is what produces it (vs. authorial discipline). Claims like "most projects use Conventional Commits" circulate as informal anecdotes.
- **RQ**: (1) What fraction of recent commits in popular open-source repositories fully conform to the CC spec, decomposed into full / partial / non-conform tiers? (2) Is compliance associated with configured CC tooling, and how strong is the association? (3) Is compliance associated with release-cadence regularity or frequency?
- **Hypotheses**: H1 — full compliance is a minority (or bimodal) outcome across popular repositories. H2 — tooling presence is strongly associated with compliance (odds ratio > 10). H3 — compliant repositories release on a more regular cadence (lower CV of inter-release intervals).
- **Contributions**: (i) first deterministic, reproducible measurement of real-world CC compliance over a current multi-repo corpus; (ii) a multi-signal tooling-detection oracle; (iii) a tiered compliance decomposition (full / partial / non) that surfaces the "disciplined but non-CC" middle ground; (iv) an association analysis of compliance with tooling and release behavior; (v) a reproducible artifact (one-command pipeline, committed snapshot, expected output).

## 2. Background & Related Work

1. **Conventional Commit Message Generation: How Far Are We?** (2026-03-27) — evaluates LLM-based generation of CC-format messages on a benchmark; treats CC as the *target format* and assumes its reach. **Difference**: we measure whether the real world actually uses the format at all — a prerequisite the generation literature leaves unmeasured.
2. **Automatic Commit Message Generation: A Critical Review and Directions for Future Work** (TSE 2024) — the field's critical review; generation-centric; explicitly notes that measurement of real-world commit-message structure is understudied. **Difference**: we supply that measurement, deterministically and reproducibly, at repository scale.
3. **ApacheCM dataset** (2026-03-01) — a large dataset of Apache-project commit messages for generation/analysis research. **Difference**: a dataset artifact, not a compliance measurement; we measure spec conformance with a spec-derived parser and link it to tooling and release metadata.
4. **commitlint / semantic-release / release-please / commitizen** (primary sources, docs) — the enforcement and release tooling that *defines* the practical CC ecosystem. **Difference**: tooling documents what compliance *should* be and how to enforce it; no tooling documents what compliance *is* in the wild. We measure the gap.
5. **The Conventional Commits specification** (conventionalcommits.org) — the ground truth we parse against; informal grammar (open type set, optional scope, `!`/`BREAKING CHANGE` markers) — we make the interpretation deterministic via a documented three-tier classifier.

## 3. Method

- **Corpus**: 19 popular open-source repositories (all in GitHub's top ~1% by stars in their ecosystem). Tooling-present group (11): the CC-tooling projects themselves (commitizen/cz-cli, semantic-release/semantic-release, conventional-changelog/conventional-changelog, googleapis/release-please, conventional-changelog/commitlint — 5 vendors) plus ordinary consumer repos with commitlint configured (googleapis/google-cloud-python, google/zx, nestjs/nest, element-plus/element-plus, pnpm/pnpm, google/blockly — 6 non-vendors, the latter three added in revision round 1 to bound the estimate). Tooling-absent group (8): pallets/click, pallets/flask, fastapi/typer, tqdm/tqdm, dateutil/dateutil, jakubroztocil/httpie, psf/requests, numpy/numpy. Mix of Python (9) and JavaScript/TypeScript (10) ecosystems.
- **Sampling**: the 300 most recent commits per repository (via the GitHub REST API, `GET /repos/{owner}/{repo}/commits`, paginated 100/page), all releases per repository (`GET .../releases`). Snapshot date 2026-08-26; the fetched data is committed (`data_snapshot/`) so reproduction is offline-capable.
- **Tooling oracle** (deterministic, multi-signal): a repository is "tooling-present" iff any of (i) a root-level CC config file exists (`.commitlintrc*`, `commitlint.config.*`, `.releaserc*`, `release.config.*`, `.release-please*`, `.cz*`, `cz.config.*`, `.versionrc*` — via the trees API), (ii) `package.json` declares a CC-tool dependency (`commitlint*`, `commitizen*`, `cz-conventional*`, `semantic-release`, `release-please`, `standard-version`), or (iii) the repository's GitHub topics include a CC tooling topic (`conventional-commits`, `semantic-release`, `release-please`, `commitlint`, `commitizen`, `conventional-changelog`). The oracle is conservative in the "absent" direction: any of these signals marks tooling-present.
- **Parser** (`reproduce.py`, stdlib-only, deterministic): each commit's subject line is classified into one of three tiers:
  - **full**: matches `^<canonical-type>[(scope)][!]: <description>` with a canonical type from the spec's documented set (feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert);
  - **partial**: has a `word[(scope)][!]:` colon-prefix structure but a non-canonical type or casing (e.g. `Feat:`, `ENH:`, `docs-fix:`) — a *structured but non-CC* message;
  - **non**: everything else.
  A commit is additionally flagged `breaking` if its subject contains `!:` or any body line starts with `BREAKING CHANGE:` / `BREAKING-CHANGE:`.
- **Metrics**: per-repository full-compliance %; pooled full-compliance; per-repository mean with 95% t-CI (repositories = sampling units, avoiding pseudoreplication over commits); Welch two-sample t-test and pooled odds ratio for the tooling contrast; Spearman rank correlation between full-compliance % and the coefficient of variation (CV) of inter-release intervals (days); median release count per group as a frequency signal.
- **Protocol**: deterministic (no randomness, no ML); one command `bash reproduce.sh` runs the canonical analyzer in offline mode over the committed snapshot and diffs against the committed expected output (exit 0 iff byte-identical).

## 4. Results

### 4.1 C1 — compliance rate (19 repos, 5,700 commits)

Pooled full compliance: **55.1%** (3,139/5,700); per-repository mean **55.1% ± 22.3%** (95% t-CI, n=19, df=18, t=2.101). Tier decomposition (pooled): full 55.1% | partial 6.4% | non 38.5%.

| repo | group | n | full% | partial | non |
|------|-------|---|-------|---------|-----|
| conventional-changelog/conventional-changelog | T | 300 | 100.0 | 0 | 0 |
| googleapis/release-please | T | 300 | 98.7 | 4 | 0 |
| semantic-release/semantic-release | T | 300 | 96.7 | 0 | 10 |
| conventional-changelog/commitlint | T | 300 | 96.0 | 0 | 12 |
| google/zx | T | 300 | 94.7 | 0 | 16 |
| commitizen/cz-cli | T | 300 | 94.3 | 2 | 15 |
| googleapis/google-cloud-python | T | 300 | 94.3 | 14 | 3 |
| nestjs/nest | T | 300 | 53.3 | 0 | 140 |
| pnpm/pnpm | T | 300 | 99.3 | 0 | 2 |
| element-plus/element-plus | T | 300 | 98.0 | 6 | 0 |
| google/blockly | T | 300 | 92.3 | 10 | 13 |
| tqdm/tqdm | N | 300 | 13.0 | 72 | 189 |
| jakubroztocil/httpie | N | 300 | 5.0 | 3 | 282 |
| psf/requests | N | 300 | 4.3 | 2 | 285 |
| pallets/click | N | 300 | 3.3 | 2 | 288 |
| dateutil/dateutil | N | 300 | 3.0 | 7 | 284 |
| pallets/flask | N | 300 | 0.0 | 3 | 297 |
| fastapi/typer | N | 300 | 0.0 | 0 | 300 |
| numpy/numpy | N | 300 | 0.0 | 242 | 58 |

The pooled 47.3% is a **bimodal mixture**, not a universal rate: tooling-present repos cluster at 94–100% (one outlier at 53.3%), tooling-absent repos at 0–13%. → supports H1 (bimodal) and quantifies it.

**Nuance — the "partial" middle ground**: numpy/numpy has 242/300 partial messages — its own long-standing disciplined convention (`ENH:`, `BUG:`, `MAINT:` prefixes) that is structured but not CC. The partial tier is what makes this visible: 80.7% of numpy's commits are *structured*, yet only 0% are CC-full. Discipline ≠ CC conformance.

**Nuance — tooling presence ≠ enforcement**: nestjs/nest (53.3%) has `.commitlintrc.json` and `@commitlint/cli` configured, yet only half its recent history conforms — enforcement is not wired into CI, or the config postdates the sampled window. Tooling presence is a *necessary-looking* but not *sufficient* condition. The three consumer repos added in revision (pnpm 99.3%, element-plus 98.0%, blockly 92.3%) show that ordinary projects with commitlint wired in reach the same high band as the tooling vendors.

### 4.2 C2 — tooling association (8 vs 8 repos)

| group | repos | per-repo mean full% ± CI | pooled full% |
|-------|-------|--------------------------|--------------|
| tooling-present | 11 | **92.5% ± 8.9%** | 92.5% (3,053/3,300) |
| tooling-absent | 8 | **3.6% ± 3.6%** | 3.6% (86/2,400) |

Welch two-sample t = **20.85** (df ≈ 12.8), p < 0.001. Pooled odds ratio = **333×** (a commit in a tooling-present repo is ~333× more likely to be CC-full than one in a tooling-absent repo). → supports H2 strongly. The CIs do not overlap; the effect is not an artifact of pooling.

**Self-selection check (revision round 1)**: 5 of the 11 tooling-present repos are the CC-tooling projects themselves, for which compliance is their reason for existence. Restricting to the 6 non-vendor consumer repos (google-cloud-python, google/zx, nestjs/nest, element-plus, pnpm, blockly) gives **88.7% ± 18.4%** (n=6) — still an order of magnitude above the no-tooling group. The tooling→compliance association is therefore not an artifact of the vendor group; the headline 92.5% is nonetheless best read as an upper-bound estimate for the tooling-ecosystem, with the non-vendor subgroup (88.7%) as the conservative estimate for typical adopters.

### 4.3 C3 — release cadence (19 repos with ≥4 releases)

Overall Spearman rank correlation between full-compliance % and CV of inter-release intervals: **ρ = +0.279** (n=19). Revision round 1 adds the within-group decomposition the reviewer requested, because the overall correlation mixes two groups that differ in *both* compliance and release automation:

- Within tooling-present group (n=11): **ρ = −0.036**
- Within no-tooling group (n=8): **ρ = +0.146**

→ **H3 is falsified at both levels**: within either group there is no compliance→regularity association; the +0.279 overall correlation is a between-group artifact (tooling repos both comply more and release differently), confirming the reviewer's confounding hypothesis. 

**Window mismatch justification**: compliance is measured over the 300 most recent commits (~recent months) while release CV uses each repo's full release history. The full history is the right window for CV because (i) the sampled commit window is too short to contain enough releases for a stable interval estimate (most repos release fewer than 5 times in it), and (ii) releases are the natural cadence unit the tooling drives; restricting to a recent window would truncate exactly the automation signal we measure. The frequency signal is robust to the window choice.

**Frequency (the robust signal)**: median releases — tooling-present **248** vs tooling-absent **47** (~5.3×). High-compliance repos release far more often (google-cloud-python 5,839 — a monorepo releasing per-package; pnpm 1,159; semantic-release 456; release-please 366), consistent with automated, demand-driven releases rather than scheduled manual cycles.

## 5. Threats to Validity

- **Corpus selection**: 16 popular, mostly well-maintained repositories; the population of all OSS skews smaller and less tooled — the tooling-absent group here is *conservative* (they are still popular, disciplined projects; a random OSS sample would likely show even lower compliance). We report per-repository heterogeneity rather than a single universal number.
- **Recent-window bias**: we sample the 300 most recent commits — compliance may be higher in the recent window (tooling adopted later in a project's life). This biases *toward* compliance; the low no-tooling rates are thus an upper bound on those projects' recent compliance.
- **Parser strictness**: the CC spec has an open type set and informal grammar; our three-tier classifier fixes a conservative interpretation (canonical types only for "full"). An LLM- or human-judged "spirit of CC" score might rate some "partial" commits as acceptable CC (e.g. `Merge` or lowercase-type variants). We state the rule precisely so the measurement is reproducible and comparable.
- **Tooling oracle**: our "absent" verdict is conservative (any signal marks present); a repo with tooling in a *subdirectory* (not root) could be mislabeled absent. Manual verification of the 8 absent repos found no root-level or package.json signals; workflow-based detection was considered but code-search requires token scope (dropped) — a known boundary.
- **Snapshot date**: data is a point-in-time sample (2026-08-26); commit streams change daily. The committed snapshot freezes the exact data every number refers to; the one-command refresh (`python3 reproduce.py` online) regenerates a *new* snapshot and would change numbers — the committed expected output always matches the committed snapshot (offline mode).
- **Release-CV crudeness**: monorepos with thousands of releases dominate the CV signal; the frequency (median releases) is a more robust secondary signal; we report both and do not over-interpret the CV.
- **Merge commits**: 440/5,700 sampled commits (7.7%) are merge commits ("Merge pull request #N" etc.), classified "non"; excluding them raises pooled full compliance from 55.1% to 59.7% — a modest shift that does not change any conclusion (the tier decomposition is reported with merges included, the conservative direction).
- **Why still worth publishing**: the coverage/tooling literature assumes CC reach; the generation literature assumes CC as target; neither measures the gap. Our 272× odds ratio, the bimodal distribution, and the falsified regularity hypothesis are new, cheap to reproduce, and directly actionable for (a) adopters deciding whether tooling alone suffices, (b) tooling authors deciding enforcement defaults, and (c) benchmark builders needing a difficulty control (like TypyBench for types — the no-tooling repos are the "hard" population).

## 6. Conclusion & Future Work

- **C1**: 55.1% pooled full compliance, but strongly bimodal — CC compliance in the wild is a function of *enforcement infrastructure*, not authorial convention: tooling repos 92.5% vs no-tooling 3.6% (OR 333×; non-vendor consumers 88.7%).
- **C2**: tooling presence is necessary-looking but not sufficient (nestjs 53.3%); the "disciplined but non-CC" middle ground is real (numpy 80.7% structured, 0% CC).
- **C3**: the regularity hypothesis is falsified at both levels (within-group ρ ≈ 0); compliant repos release 5.3× more often — CC tooling automates releases, making cadence demand-driven rather than regular.
- Future work: expand corpus (n≥40, more ecosystems, per-year time trend); workflow-content signal for tooling detection; commitlint rule-set comparison (strictness continuum); commit-window-aligned release-CV (requires commit dates in the snapshot); link compliance to issue-closure latency or release quality.

## Reproducibility

`bash reproduce.sh` is the one-command reproduction: it runs the canonical analyzer (`reproduce.py --offline`, stdlib-only, deterministic) over the committed data snapshot and diffs the fresh output against `expected_output/manuscript_results.txt` (exit 0 iff byte-identical). The snapshot (`data_snapshot/`, 19 files — the 3 consumer repos added in revision round 1 fetched 2026-08-26) was fetched from the GitHub REST API on 2026-08-26; the online refresh path (`python3 reproduce.py`) is documented in the README. Python ≥3.10, no pip dependencies, no network required for reproduction.
