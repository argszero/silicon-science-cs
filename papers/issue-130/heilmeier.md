# Heilmeier screen + adversarial checks — Issue #130

**Title**: A Threshold Is Not a Measurement: The Operating Characteristic and Certification Floor of Artefact-Similarity Checks
**Registered**: 2026-10-08 (R565), `in-preparation`. Author instance `how2how2how2-arch`.

## Candidate pool (Phase A step 1-2): sources scanned this round

External scan first (all via the arXiv API, `https://`, sorted by `submittedDate`, window = last ~6 months to 2026-10-08),
plus Crossref as a second route for the chosen candidate.

| # | Theme queried | Newest hits (date) | Verdict |
|---|---|---|---|
| A | `cs.SE` agent evaluation | 2026-09-30 Approval Laundering; 2026-09-28 unearned passes; 2026-09-26 financial-agent measurement boundaries | **dedup risk**: #93 owns approval binding; #124 owns repeat counts |
| B | `cs.DB` ANN | 2026-10-02 RaBitQ-SSD; 2026-09-02 "A Power Law in Logarithm's Clothing" | **dedup**: #91 owns ANN plan regret |
| C | `cs.AR` prefetchers | 2026-09-03 confidence-gated admission; 2026-08-13 "Why Do Prefetchers Fail?" | **dedup**: #96 owns the prefetch crossover |
| D | `cs.MS` mixed precision | 2026-09-29 running-error bounds; 2026-09-29 mixed-precision survey | **dedup**: #126 owns the precision floor |
| E | `cs.RO` fleet/energy | 2026-09-15 Robot Data Factory; 2026-03-24 fleet battery-health scheduling | plausible, but a scheduling-boundary repeat of #98/#124 in spirit |
| F | **`cs.SD` audio watermarking** | **7 papers in 3 weeks** (2026-10-04 NeuMark-Native; 10-03 model-driven reconstruction; 09-27 Redwing; 09-24 ×2) | **hotspot, new subfield — but infeasible here**: the 2026 frontier is *neural-codec* channels; no torch/codec available, and the classical capacity theory is already published (so the runnable part is the known part) |
| G | `cs.PL` incremental analysis | 2026-09-30 Fixing the Fixpoint | needs a compiler toolchain; not runnable in this environment |
| H | `cs.DB` cardinality estimation | 2026-09-11 QEmbed | **dedup**: #91 |
| I | `cs.HC` overreliance | 2026-09-23 skill-sustaining reliance; 2026-09-15 temporal fingerprint | human-subject data; no cheap ground truth |
| J | `cs.SE` flaky tests | 2026-09-22 Shaker; 2026-07-10 limits of code-based detection | needs per-project runners; ground truth acquisition is the whole cost |
| K | `cs.DC` serverless | 2026-09-22 fragmentation-aware allocation | cold-start space, adjacent to #98 |
| L | `cs.CR` prompt injection | 2026-10-06 RAG-PIBench; 2026-10-05 RAISED | **dedup**: #93/#89 own the defense-collapse space |
| O | `cs.DC` carbon/energy | 2026-09-30 FissionReady; 2026-09-13 CATS | plausible; would be the 4th cs.DC direction (rotation penalty) |
| **★** | **host rant 2026-10-08T03:20:07 (item 2)** | reader-validated need, on *our own* published output | **selected** — host-anchored, so the rotation penalty is waived (Phase A priority: host-specified > hotspot) |

**Hotspot rationale (step 2)**: the selected direction sits inside two live 2026 themes — *evaluation integrity* (the
2026-09 evaluation-audit cluster: instrumented benchmarking, unearned passes, metric audits) and *provenance /
near-duplicate checking* (the audio/LLM/diffusion watermarking cluster plus duplicate-detection venues). The specific
object it measures is unclaimed on both routes (below).

## Six Heilmeier answers

1. **Problem.** For a similarity-threshold check on a real artefact, what is the flag probability `R(eps; tau, L)` for
   an artefact perturbed at a *known rate* `eps`, as a function of artefact length `L` — and is the threshold's
   *meaning* (the curve's location `eps*`) or only its *reliability* (the curve's width) a function of `L`?
   Falsifiable in both directions: `eps*(L)` flat vs sloping.
2. **Current approaches & limitations.** Deployed checks are specified as a bare threshold plus one corpus-level
   point (`2212.10041`; `2205.11630`; Crossref 2008 *Achieving both high precision and high recall in near-duplicate
   detection*; PAN-style protocols). Because the protocol fixes one corpus with one length distribution, the
   threshold's meaning is bound to that corpus: the same cut means a different recall on a short comment than on a
   long report, and nothing in the protocol measures it. **The gap is a transfer gap**: the statistical object
   (the operating characteristic / power curve) is standard in the experimental sciences, but the object it should
   be fitted to — a similarity check as a function of artefact size — has no published characterisation.
3. **Novelty.** (i) the measured **length-independence of the boundary** `eps*`; (ii) the **`L^{-1/2}` width law**;
   (iii) the **collapse** of four statistics onto one master curve in a standardized coordinate; (iv) an operational
   **certification floor** `L*` that ties the false-negative boundary to the rule-of-three false-positive bound `3/n`
   — both ends of one operating box. Reverse scan: arXiv `"similarity threshold" AND "document length"` → 0 hits;
   Crossref bibliographic queries → point-evaluation papers only.
4. **Who cares.** Journal/conference duplicate checks, platform moderation and dedup gates, licence and plagiarism
   scanners, code-clone detectors, and reviewers assessing claims of the form "our check separates at X". The changed
   decision: publish *a curve plus a length band*, never a bare threshold.
5. **Success metrics.** `R(eps; tau, L)` measured on >=300 real texts at >=6 lengths spanning ~100x; `eps*(L)` with a
   CI plus a flatness test; the fitted width against the predicted `L^{-1/2}` slope; a collapse residual per statistic;
   `L*` with its band; >=3 seeds per stochastic cell; one-command reproduction regenerating every number.
6. **Risks & fallback.** Main risk = **P1 refuted** (the boundary moves with `L`, e.g. because a fixed edit *count*
   damages a short artefact proportionally more, or a statistic normalises by count rather than rate). **Fallback**:
   report the refutation and make the *measured* `eps*(L)` scaling the paper's law — itself the missing law — with the
   rate and count parameterisations both declared and both run, so the paper is informative either way.

## Adversarial checks (all three pass)

- **Reverse gap (why not done before).** (i) The field's evaluation protocol is corpus-level, so the length axis is
   averaged out of the measurement instead of studied; (ii) perturbation-based evaluation is native to *code*
   (mutation testing) and has not been ported to *similarity* checks, whose natural perturbation is textual;
   (iii) the result is "just" statistical power, so the *method* author has no incentive to publish it — the incentive
   lies with the deployer. **Honest risk acknowledged**: reviewers may read the framework as known statistics; the
   registered claim is therefore the *specific measured law*, not the framework.
- **Evidence pre-assessment.** Real text is pinnable and cheap (arXiv abstract API; Project Gutenberg plain-text books
   for long-form prose), so real artefacts of exact length `L` are obtainable by slicing, and the length axis is exact.
   Ground truth is **by construction** (seeded perturbation at an exact rate) — no annotator, no opinion label.
   Instances: >=300 artefacts x >=6 lengths x 4 statistics x >=3 seeds; every cell an exact binomial count.
   Baselines: three further statistics plus the bare-threshold status quo. Not a single anecdote.
- **Upgradability.** (a) a fifth, embedding-style statistic (cheap hashing embedding, no neural dependency) to test
   whether the collapse is shingle-specific; (b) **fusion** — does a second check move the floor `L*`? (c) modality
   transfer (image/audio near-duplicate checks share the construct); (d) a prescriptive protocol a venue can adopt.

## Prior beliefs (registered 2026-10-08, before measurement)

- **P1 — location is length-independent**: `eps*` does not move with `L` over ~100x. *Mechanism*: for a shingle
  statistic the expected similarity is a function of the per-token survival probability, i.e. the rate `eps`; `L`
  enters only through the variance of a mean over ~L comparisons. *Folk belief this contradicts*: "longer artefacts
  are easier to check" — predicted **false on average, true only for reliability**.
- **P2 — width scales as `L^{-1/2}`**: the 10-90% transition width obeys `w ~ L^{-1/2}`, so `w*sqrt(L)` is invariant.
- **P3 — collapse**: rescaling each curve to `z = (eps - eps*)*sqrt(L)/sigma` collapses all four statistics and all
  lengths onto one master curve, up to a per-statistic sensitivity constant.
- **P4 — certification floor**: a minimum artefact length `L*` exists below which no threshold can certify a recall
  claim at a stated confidence, the false-negative analogue of the rule-of-three false-positive bound `3/n`.

**Stated in advance**: P1-P3 are expected to hold and P4 to hold with a floor inside the measured range; a refutation
of any is an equally informative result and will be reported as such.

## Corpus plan (pinned at fetch time)

- **arXiv abstracts** (real, short-to-medium prose, ids pinned, content hashed): the primary text source for
  `L <= ~250` words, fetched through the same API the project already uses.
- **Project Gutenberg plain-text books** (public domain, stable URLs, pinned by id + sha256): the long-form source for
  `L` up to several thousand words, sliced into disjoint segments of exact length.
- Neither corpus is synthetic; both are recorded with fetch date, id list and digests so the corpus is reconstructible.
