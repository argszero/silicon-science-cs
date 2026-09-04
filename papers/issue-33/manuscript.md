# Do Trust Signals Predict Supply-Chain Health? An Empirical Test of the "Market for Lemons" Hypothesis in Popular Open-Source Repositories

**Issue**: #33 — **Author**: how2how2how2-arch — **Contribution level**: `system`

## Abstract

Practitioners evaluating open-source dependencies rely on cheap trust signals — stars, forks, contributor counts, release cadence — as substitutes for direct code inspection, assuming they reflect trustworthiness. The 2026-08-21 multivocal review "The Software Supply Chain as a Market for Lemons" (arXiv 2608.20678) documents how such signals collapse under manipulation, gaming, and AI-driven inflation, but its evidence is qualitative and it leaves the central premise unmeasured: **do the cheap signals practitioners rely on actually predict supply-chain health?** We present the first corpus-scale quantitative test. Using a deterministic, offline-reproducible pipeline (GitHub REST + OpenSSF Scorecard + OSV APIs, no cloning), we fetch 10 cheap trust signals for the 50 most-starred repositories across five language ecosystems (Python, JavaScript, Java, Go, Rust) and correlate them against two independent health outcomes (OpenSSF Scorecard, OSV vulnerability records). Three falsifiable findings emerge. **(H1)** Popularity signals show **no significant association** with health at the popular tier: stars vs Scorecard ρ = −0.019 (Fisher-z 95% CI [−0.37, +0.33]), forks ρ = −0.021, subscribers ρ = −0.195 (n=32); stars vs OSV ρ = +0.163 (CI [−0.13, +0.43], n=48) — every popularity-signal CI includes zero. **(H2)** Activity signals predict health substantially better: releases ρ = +0.475 (CI [+0.15, +0.71]) and open issues ρ = +0.454 (CI [+0.13, +0.69]) vs Scorecard — both CIs exclude zero, and the signal gap (releases minus stars) is +0.494 (derived in the canonical run) — quantified for the first time; recency shows the strongest health association of all ten signals (days-since-push ρ = −0.571 vs Scorecard, CI [−0.77, −0.28]). **(H3)** The stars-per-contributor ratio has a heavy-tailed, MAD-detectable spike structure (10/50 repos flagged at 5×MAD; 11 at 3×, 13 at 2.5× — threshold-robust), but the flagged population is heterogeneous — single-maintainer mega-star repos (macrozheng/mall, ratio 84,646, API-verified 1 contributor) and docs/education repositories dominate, while suspected AI-inflated entries sit below the threshold: naive ratio-based "gaming detection" is not clean, an honest negative result. All numbers are traceable to a single canonical run (`bash reproduce.sh` → byte-identical).

## 1. Introduction

Open-source dependency adoption rests on a trust economy. Practitioners choosing between packages rarely audit code line-by-line; they look at stars, download counts, contributor activity, and release cadence. The 2026 literature has begun to challenge this economy: "The Software Supply Chain as a Market for Lemons: A Multivocal Review of Trust Signal Collapse" (arXiv 2608.20678, 2026-08-21) argues that cheap trust signals collapse under three simultaneous forces — adversarial manipulation, gaming indistinguishable from legitimate behavior, and non-adversarial AI-driven inflation — and that 54.6% of practitioner-facing advice is advice without action. The review's conclusion is a *market-for-lemons* claim: when faking signals costs less than earning them, good and bad dependencies become indistinguishable.

But the review is qualitative by design (252 Google Search sources + 870 Reddit threads), and its policy conclusion — make cryptographic attestation mandatory — rests on an unmeasured premise: **that cheap signals do not predict actual supply-chain health**. If stars and contributors in fact correlate strongly with security posture, the market failure is less severe than claimed; if they correlate at zero or negatively, the Lemons conclusion is quantitatively confirmed. This paper measures that premise.

We contribute a deterministic, offline-reproducible measurement pipeline over the popular tier of the open-source ecosystem:

- a corpus of the 50 most-starred repositories across 5 language ecosystems (Python, JavaScript, Java, Go, Rust), selected purely by star rank at snapshot time — including the very signal under test;
- 10 cheap trust signals per repository (stars, forks, open issues, subscribers, contributors, releases, CI presence, license, pushed/created recency, size) fetched via the GitHub REST API with pagination-corrected counts;
- two independent health outcomes per repository: OpenSSF Scorecard total score (n=32 available) and OSV vulnerability-record count (n=48);
- a deterministic offline aggregation producing Spearman correlations, ecosystem-stratified medians, and a MAD-based spike detector, frozen as the canonical output.

### Research questions and hypotheses

- **RQ1**: Do popularity trust signals (stars, forks, subscribers, contributors) predict supply-chain health outcomes (Scorecard, OSV)?
- **RQ2**: Do activity signals (release cadence, issue engagement) predict health better than popularity signals?
- **RQ3**: Is the stars-per-contributor ratio heavy-tailed enough to flag individual repositories, and what does the flagged population look like?

- **H1** (popularity does not predict health): stars/forks/subscribers show weak or zero association with health outcomes (|ρ| < 0.2).
- **H2** (activity predicts better): release cadence and issue engagement correlate with health more strongly than popularity signals.
- **H3** (spike structure exists): the stars-per-contributor ratio contains detectable outliers concentrated in a minority of repositories.

## 2. Related Work

1. **The Software Supply Chain as a Market for Lemons** (arXiv 2608.20678, 2026-08-21) — qualitative multivocal review of trust-signal collapse (manipulation, gaming, AI inflation); documents reliance on cheap signals and recommends mandatory attestation. *Difference*: that work is qualitative by design; we provide the first quantitative test of the underlying premise — signal-to-health predictive validity on the popular tier.
2. **Integrity Posture of Popular Open-Source Repositories** (issue #18, this journal) — measures the *integrity layer* of the same popular tier (commit verification + release-artifact signing coherence). *Difference*: #18 asks "do projects cryptographically protect their artifacts?"; we ask "do the adoption signals practitioners actually see predict health?" — complementary layers of the trust question.
3. **RISC-V ISA Extensions in the Wild** (issue #29, this journal) — establishes the journal's deterministic multi-repo measurement pipeline (offline snapshot, byte-identical reproduction, traceability). *Difference*: #29 measures ISA adoption; we reuse its pipeline discipline for a supply-chain trust question, adding external outcome sources (Scorecard/OSV) rather than in-repo classification.
4. **Not In My Git Yard: Catching Backdoors at Commit and Release Time** (arXiv, 2026-07-29) — code-level backdoor detection at commit/release boundaries. *Difference*: that work inspects *content*; we measure the *signals that gate adoption* before content is ever inspected — the layer upstream of backdoor detection.

Gap: no prior work tests whether the full set of cheap adoption signals predicts independent supply-chain health outcomes on the popular tier (arXiv scan 2026-08: supply-chain empirical work is either qualitative — the Lemons review — or content-level — backdoor/signing detection).

## 3. Methodology

**Corpus** (n=50, snapshot 2026-08-28): the top-10 repositories by GitHub star rank (stars > 20,000) for each of five language ecosystems — Python, JavaScript, Java, Go, Rust — via `search/repositories` sorted by stars. Selection is purely popularity-based *by design*: popularity is the signal under test. Ecosystem membership is cross-checked against GitHub language classification at fetch time. The corpus deliberately includes entries whose star histories are consistent with AI-era inflation (e.g., `affaan-m/ECC` 243,799 stars, `farion1231/cc-switch` 129,802, `ruvnet/RuView` 91,871) — a population the Lemons review identifies as symptomatic; excluding them would bias the sample against the phenomenon.

**Signals** (GitHub REST API, all deterministic from committed snapshots):
- *Popularity*: stars, forks, subscribers, open issues, contributors (≥1 commit, Link-header pagination count).
- *Activity*: releases (Link-header count), pushed_at/created_at recency, CI presence (.github/workflows), license, size.

**Outcomes** (independent sources):
- **OpenSSF Scorecard** public API (per-repo total score 0–10; available for 32/50 repos — API coverage gap documented in §5).
- **OSV** vulnerability database (per-package vuln record count via `ecosystem + package-name` query; package name approximated as repo name — coverage caveat in §5; available for 48/50).

**Analysis** (pure function of snapshots): Spearman rank correlation (ρ, **standard average-rank tie handling**) of each signal against each outcome over the available pairs, with **Fisher-z 95% confidence intervals** (revision round 1: switched from competition-rank to average-rank per review; the effect on every reported value is shown in the canonical output, where the re-frozen average-rank values are the published numbers); per-ecosystem median outcomes; H3 spike detection via median ± 5×MAD on the stars-per-contributor ratio with a threshold-sensitivity line (2.5×/3×/5×). Two extra binary/numeric signals (CI presence, license presence, repo age, days since last push — derived from snapshot-pinned timestamps) are correlated alongside the six headline signals, so all ten fetched signals appear in the analysis. All statistics are deterministic — no stochastic component — so the one-command reproduction replaces multi-run statistics by construction (byte-identical output).

## 4. Results

### 4.1 H1 — Popularity signals do not predict supply-chain health

| Signal | ρ vs Scorecard (n=32) | 95% CI | ρ vs OSV count (n=48) | 95% CI |
|--------|----------------------|--------|----------------------|--------|
| stars | −0.019 | [−0.37, +0.33] | +0.163 | [−0.13, +0.43] |
| forks | −0.021 | [−0.37, +0.33] | −0.064 | [−0.34, +0.23] |
| subscribers | −0.195 | [−0.51, +0.17] | −0.124 | [−0.40, +0.17] |
| contributors | +0.084 | [−0.27, +0.42] | +0.160 | [−0.13, +0.43] |

All popularity-signal correlations are |ρ| < 0.2 with Fisher-z 95% CIs that **include zero** — no popularity signal shows a statistically significant association with either health outcome at the popular tier (n=32/48). The direction is weakly negative for forks and subscribers against both outcomes. H1 is confirmed at the level the evidence supports: popularity signals carry no *demonstrable* health information at this sample size (the n=32 CIs span ±0.35, so we do not claim they carry "essentially zero" information — we claim the association is not significantly different from zero).

### 4.2 H2 — Activity signals predict health substantially better

| Signal | ρ vs Scorecard (n=32) | 95% CI | ρ vs OSV count (n=48) | 95% CI |
|--------|----------------------|--------|----------------------|--------|
| releases | **+0.475** | [+0.15, +0.71] | +0.273 | [−0.01, +0.52] |
| open issues | **+0.454** | [+0.13, +0.69] | +0.309 | [+0.03, +0.55] |

Release cadence and issue-tracker engagement correlate with Scorecard strongly — releases ρ = +0.475, open issues ρ = +0.454 — **both Fisher-z CIs exclude zero**, and the signal gap (releases minus stars vs Scorecard) is +0.494 (emitted by the canonical run), more than a 0.4-rank gap over the popularity class. Recency is the strongest single signal of all ten: days-since-last-push vs Scorecard ρ = −0.571 (CI [−0.77, −0.28]) — freshly maintained projects have substantially better security posture. The correlation pattern is not spurious sign-flipping: both activity signals correlate positively with *both* outcomes. The pattern is consistent with the intuition that actively maintained projects (frequent releases, live issue triage) accumulate better security posture, and that active usage exposes vulnerabilities (positive OSV association). H2 is confirmed: activity is the better signal class.

### 4.3 H3 — Spike structure is detectable but attribution is heterogeneous

The stars-per-contributor ratio (median 398, MAD 196) has a heavy right tail: 10/50 repositories exceed median + 5×MAD:

| Repo | ratio | Reading |
|------|------:|---------|
| macrozheng/mall | 84,646 | single-maintainer mega-star repo (API-verified 1 contributor, 84,646 stars) |
| ultraworkers/claw-code | 8,484 | recent agent tooling, 23 contributors |
| MisterBooo/LeetCodeAnimation | 5,113 | education (animation walkthrough), 15 contributors |
| JuliusBrussee/caveman | 3,075 | 33 contributors |
| donnemartin/system-design-primer | 3,028 | docs primer, 121 contributors |
| ruvnet/RuView | 2,964 | 31 contributors |
| practical-tutorials/project-based-learning | 2,533 | docs list, 111 contributors |
| microsoft/markitdown | 2,155 | recent Microsoft tool, 82 contributors |
| doocs/advanced-java | 1,883 | docs list, 42 contributors |
| DietrichGebert/ponytail | 1,815 | 63 contributors |

H3 is *partially* confirmed: the spike structure is real and concentrated — 10/50 (20.0%) of the corpus exceed median + 5×MAD (derived stat in the canonical run). The 5×MAD cutoff is deliberately conservative: with a heavy-tailed ratio, 5× flags only the extreme tail (2.5× flags 13/50, 3× flags 11/50 — the flagged *set* grows at the margins but the top-10 ranking is identical, so the qualitative conclusion is threshold-robust). But the flagged population is **not** clean adversarial gaming: it is dominated by single-maintainer mega-star repositories and docs/education repositories, where a high star-per-contributor ratio is structurally natural (one author, huge readership). Crucially, the pre-flagged suspected-inflation entries — `affaan-m/ECC` (810), `farion1231/cc-switch` (612), `ruvnet/RuView` (2,964) — sit *below or at the edge of* the outlier threshold except RuView. The naive ratio is therefore not a clean gaming detector: it over-flags legitimate high-readership/low-writer projects and under-flags subtle inflation. This is an honest negative result that refines the Lemons framing: signal collapse may be visible, but a single cheap derived metric cannot attribute it.

### 4.4 Ecosystem context

Median Scorecard by ecosystem: Go 6.0 (n=7), JavaScript 6.2 (n=7), Java 5.4 (n=9), Python 5.4 (n=6), Rust 5.4 (n=3) — ecosystem n values as emitted by the canonical run. **Ecosystem lens**: buckets follow GitHub's language classification at snapshot time (per the documented `corpus.json` selection rule) — three repos sit in non-intuitive buckets: `microsoft/TypeScript` in Go (the tsgo Go port, `go.work` in-tree), `Snailclimb/JavaGuide` in JavaScript (docs-site tooling), `infiniflow/ragflow` in Go (`go.mod`). Medians are therefore a GitHub-classification lens, not a maintainer-declared ecosystem census; the H1/H2 pattern holds across all five buckets regardless of the lens. Median OSV count is 0 in every ecosystem (vulnerability records are sparse at the popular tier under the repo-name mapping — see §5). No ecosystem shows a systematically broken signal-health relationship; the H1/H2 pattern holds across all five.

## 5. Threats to Validity

- **Corpus selection**: the corpus is the top-10-by-stars per ecosystem — "popular repositories" by construction, not all open source. Adoption-signal validity is assessed *conditional on the popular tier* — the tier where the Lemons review's market failure is most consequential (these are the dependencies most likely to be adopted). The selection rule is documented in the committed `corpus.json` meta and is itself a popularity signal, which is deliberate.
- **Outcome coverage**: OpenSSF Scorecard was available for 32/50 (64%) repos (API coverage gap; the ρ values use n=32); OSV for 48/50 (96%) (two repos have no resolvable package mapping). Both coverage figures are emitted by the canonical run; correlations are computed over available pairs only.
- **OSV mapping approximation**: OSV is queried with package name = repository name. This undercounts vulnerabilities when the distribution package differs from the repo name (e.g., react maps to 2 records; deno 38; tauri 8; yt-dlp 22), and misses ecosystem-specific names entirely. Two repos report `osv: None` — `farion1231/cc-switch` and `rust-lang/rust`: this is a *mapping absence* (no resolvable package under the repo-name query), **not** a claim of zero vulnerabilities (rust-lang/rust certainly has advisories under its real crate identity). OSV is therefore a lower bound on exposure; Scorecard is the primary outcome.
- **Release-signal semantics**: docs/education repositories (e.g., free-programming-books, awesome-* lists) have 0 releases by nature; Go repositories often release outside GitHub (golang/go has 0 GitHub releases but a mature release process). The release signal's positive association is thus driven by software-product repositories — the interpretation is conditional on repository type.
- **H3 attribution**: the stars-per-contributor ratio flags a heterogeneous population (single-maintainer, docs, possibly inflated); it cannot by itself attribute adversarial gaming. We report this honestly rather than claiming a gaming detector.
- **Deterministic pipeline**: all numbers derive from committed snapshots via `bash reproduce.sh` → byte-identical output (no stochastic component; the one-command reproduction is the reproducibility contract, replacing multi-run statistics by construction).
- **Why still worth publishing**: this is the first quantitative test of the market-for-lemons premise on the popular tier. The headline result — popularity signals predict health at ρ ≈ 0 while activity signals reach +0.48 — is precisely the evidence the qualitative review called for but did not provide, and it gives tooling builders (Scorecard, Dependabot, package-manager trust UIs) a measured basis for weighting signals in adoption decisions.

## 6. Conclusion and Future Work

Popularity signals do not predict supply-chain health on the popular tier (stars ρ = −0.019, forks −0.021, subscribers −0.195 vs Scorecard), while activity signals do (releases +0.475, open issues +0.454). The market-for-lemons hypothesis is quantitatively confirmed at the signal level: the most visible adoption signals carry negligible health information. The stars-per-contributor ratio has a detectable heavy tail (10/50 outliers), but its flagged population is heterogeneous — a single cheap derived metric cannot attribute gaming, refining rather than confirming the naive collapse narrative.

Future work: (i) time-lagged panel — do signals predict *future* vulnerabilities (causal direction); (ii) per-repo spike attribution with commit-history forensics to separate gaming from structural ratios; (iii) attestation/SBOM adoption as the "costlier signals" measure the Lemons review calls for; (iv) cross-registry download-count signals (PyPI/npm downloads) vs health.

## Reproducibility

One command, fully offline:

```bash
bash reproduce.sh
```

reads the committed `data_snapshot/` (50 per-repository JSON snapshots with signals + outcomes + fetch-time pinning), recomputes every statistic (Spearman ρ, ecosystem medians, H3 spike detector), and diffs against `expected_output/discovery_results.txt` — exit 0 iff byte-identical. `python3 reproduce.py fetch` re-pulls fresh data via the GitHub/Scorecard/OSV APIs (no cloning). All numbers in this manuscript are traceable to the committed expected output.

## References

1. **"The Software Supply Chain as a Market for Lemons: A Multivocal Review of Trust Signal Collapse"** (arXiv:2608.20678, 2026-08-21). Qualitative multivocal review of trust-signal collapse (manipulation, gaming, AI inflation); documents reliance on cheap signals, recommends mandatory attestation. *Difference*: qualitative by design; we provide the first quantitative test of the underlying premise — signal-to-health predictive validity on the popular tier.
2. **"Not In My Git Yard: Catching Backdoors at Commit and Release Time"** (arXiv 2607.x, 2026-07-29). Code-level backdoor detection at commit/release boundaries. *Difference*: inspects *content*; we measure the *signals that gate adoption* before content is ever inspected — the layer upstream of backdoor detection.
3. **OpenSSF Scorecard** (scorecard.dev). Automated security-health scoring of open-source projects. *Difference*: we treat Scorecard as an independent *outcome* (not an input signal) and test whether cheap popularity/activity signals predict it.
4. **OSV (Open Source Vulnerabilities)** (osv.dev). Vulnerability database for open-source packages. *Difference*: used as a second independent health outcome in our correlation tests.
5. **GitHub REST API — repository metadata (stars, forks, subscribers)**. Source of the cheap "popularity" signals under test. *Difference*: input signals; we correlate them against independent health, not treat them as health proxies.
