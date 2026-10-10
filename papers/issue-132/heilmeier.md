# Issue #132 — Heilmeier, adversarial checks, priors, and the plan

Direction registered **R583 (2026-10-09)**. Title: *The Frame Is a Level: Background-Frame Level as a
Declared Parameter of Similarity Guards, and the Systematic Misclassification a Corpus-Wide Frame
Leaves*. Label `in-preparation`. Body of record: issue #132.

Anchor: the host's own reader-correction rants on our published duplicate-check post (the same thread
that produced #130's anchor), newest **2026-10-09T05:14:21** (items 19–21), which corrected the
enrichment figure **21× → 35.8×** and the flag count **156 → 25** and located the mechanism (a
corpus-wide generic frame is blind to a sub-community register; a script-pool frame removes it).

---

## 0. Hotspot rationale (which signals)

- **Host rant (highest priority, host-specified)** — the reader thread measured the effect directly on
  a real platform corpus (a corpus DF frame is blind to a 0.4–0.5 %-share register; a script frame
  collapses that class's rate 55.9 % → 3.2 %).
- **External signal (multilingual evaluation wave)** — arXiv:2609.06771 (AuthBench, 2026-09-06)
  standardizes authorship evaluation across 10 languages / 9 genres *because* the field was fragmented
  across language, genre and length. It does **not** stratify by the level at which a detector's
  background is computed. `cs.CL` multilingual/plagiarism submissions are visibly dense in the scan
  (2026-01…2026-10).
- **External signal (templated material at scale)** — arXiv:2609.24106 (2026-09-21) measures that
  >70 % of the top-thousand web questions are boilerplate/templated, i.e. frequency conflates
  publication with content. A background frame exists to remove exactly that material; its level is
  unstudied there.
- **External signal (reuse detection to heterogeneous corpora)** — arXiv:2603.29937 (cross-lingual
  journalism reuse, 7 languages), arXiv:2608.27343 (fragmented historical reuse), arXiv:2607.27595
  ("beyond similarity": scores say *where*, not *how/why*). None varies the frame's level.

## 1. The construct

A two-stage guard: fire a pair iff `sim(a,b) ≥ τ` **and** `|shared(a,b) \ F_ℓ| ≥ r`, where `F_ℓ` is the
**background frame** computed over the population at level `ℓ ∈ {corpus, script/register pool, author,
pair}`.

**The relation that actually holds (corrected at R584; the set-containment form was registered at R583 and is REFUTED).**

The registration asserted `F_corpus ⊆ F_script ⊆ F_author` as **sets**. `spike_v0.py` measured it on the
pinned corpus: **24 of 24 cells fail in BOTH directions** (violations 21–125 and 9–82). It is not an
identity and never was — the corpus is the pool *plus* other documents, so a pool-generic unit's corpus
frequency is **diluted**, not included.

**The exact relation that does hold — the dilution law.** With `df_ℓ(u)` the fraction of documents *in
population ℓ* containing `u`, for a unit `u` **confined** to a pool `P` of share `s = N_P/N_corpus`
(every corpus document containing `u` lies in `P`):

    df_corpus(u) = s · df_P(u)        (**exactly** — the counts coincide, c_corpus(u) = c_P(u))

*Measured*: worst |violation| **4.34e-19** over **318** confined char-bigram pairs and **8.67e-19**
over **685,502** confined word-3-shingle pairs. Worst word-3 case: the phrase **"the white whale"**
(generic inside *Moby Dick*, invisible to the corpus frame).

**The mechanism, and its critical share.** A unit generic inside its pool (`df_P ≥ θ`) is **invisible**
to a corpus frame whenever `s · df_P(u) < θ`, i.e. below the critical share

    s* = θ / df_P(u).

A unit at `df_P = 1.0` is invisible to any pool under share `θ`. So the residue removal is monotone in
the level *because the finer frame is strictly LARGER*, not because of any containment.

**The measured share law** (`spike_v0_results.json`, word-3 shingles, θ = 0.01, pooling the first *k*
books) — and it is **exactly 0.0 % at share 1.0**, which is the control:

| books pooled | share | `\|F_pool\|` | pool-generic but corpus-invisible | fraction |
|---|---|---|---|---|
| 1 | 0.135 | 44 | 39 | **88.6 %** |
| 2 | 0.265 | 25 | 19 | 76.0 % |
| 4 | 0.545 | 22 | 15 | 68.2 % |
| 8 | 1.000 | 7 | **0** | **0.0 %** |

Char-bigrams over the same sweep: 3.9 % / 2.6 % / 4.9 % / 0.0 % — **statistic-dependent**, like #130's
width law. At share 0.135 the pool frame holds 44 units against the corpus frame's 7: the finer frame
is the larger one, as the reader reported (1,070 vs 789 on their corpus).

**Limitation this round adds (stated, not hidden):** this corpus is **monolingual** (8 English books),
so the pool level here is *book/author*, not *script/language*. The **share** mechanism is measured; the
**language axis P2 turns on is NOT**. R585 must add non-English strata (fetched + SHA-pinned) before P2
is claimed.

## 2. Six Heilmeier answers

1. **Problem** — for a background-subtracting similarity guard, does the **level** at which the generic
   frame is computed change its operating characteristic, and does a corpus-level frame produce an error
   that is **systematic and language-correlated** rather than random?
2. **Current approaches & limitations** — detectors subtract a background (DF cutoff / stop-list / IDF:
   2603.29937, 2608.27343); the 2026 benchmark wave standardizes *evaluation* across languages and
   genres (2609.06771) and web-scale work measures templated contamination in *counts* (2609.24106).
   The frame's **level** is an implementation detail in all of them: not declared, its operating-point
   effect unmeasured, and no work reports whether its error is a function of **who is writing**.
3. **Novelty** — the frame level is promoted to a **declared parameter**, with (i) a measured
   operating-characteristic consequence at fixed threshold, (ii) a **systematic, language-correlated**
   misclassification law (mechanism: a DF cutoff is a *share*, so it is blind to any population that is
   a small share of the corpus), and (iii) the exact condition under which an enrichment is a
   measurement (both sides drawn from the same class) rather than a composition artifact.
4. **Who cares** — deployers of similarity / near-duplicate / plagiarism / spam guards on multi-lingual
   or multi-register corpora; readers of the multilingual-benchmark literature (a threshold without its
   frame level is under-specified); and the sub-communities a corpus-wide frame systematically
   misclassifies. **Significance**: if the level is first-order, "our threshold is 0.8" stops being a
   specification — the changed decision is *declare and re-calibrate the frame level per population*.
5. **Success metrics** — (i) the ladder with ground truth by construction, two-route agreement between
   the measured flags and the exact residue identity; (ii) each level effect bracketed to a stated
   resolution with a two-sided control at the adjacent level; (iii) the systematic claim as a
   **stratified concentration ratio with an interval**; (iv) every rate over its **eligible** subset
   with the dilution factor, every enrichment with its **matched** value first.
6. **Risks & fallback** — R1 corpus-specificity → build the ladder on synthetic ground truth + a pinned
   multi-language public corpus (Gutenberg), state the law for the exact class, MEASURE transport.
   R2 the language correlation may be an artefact of comparing a minority against a majority → the
   registered claim is the **mechanism** (a share-based cutoff is blind below the share), so a
   constructed corpus makes the **share** the control variable and carries the direction; the real
   corpus is a scope check.

## 3. Adversarial checks

- **Reverse gap** — the frame sits *inside* a detector as preprocessing; the surrounding ecology
  optimizes the *score* and the *threshold*, not the *population the score is normalized against*.
  Defaulting the frame to the whole corpus is the path of least resistance (no per-population
  calibration, no declaration). Search form (arXiv API, window 2020-01-01…2026-10-09, scan 2026-10-09):
  `all:"background frame" AND all:similarity` → 0 relevant; `all:"generic frame" AND all:threshold` → 0;
  `abs:"document frequency" AND abs:"near-duplicate"` → none varying the frame's level;
  `abs:"plagiarism" AND abs:"low-resource"` → 0. Scoped claim: *no work measuring a frame-level effect
  for a similarity guard in the space these searches reach.*
- **Evidence pre-assessment** — ground truth **by construction**: planted verbatim templates (must fire
  at EVERY level) and planted register-only pairs (must clear at exactly the level whose population
  makes them generic). Real data: the SHA256-pinned Gutenberg corpus (multi-language) for register
  strata. Cells: ≥ 4 levels × ≥ 4 statistics × ≥ 3 strata, two-sided control at each level effect.
  Baseline: the **corpus-wide frame** (standard practice). Not a single anecdote.
- **Upgradability** — more levels (genre, community, time window); a **diagnostic** that reads a
  deployed detector's configuration and reports the class of pairs its frame is blind to; theory (the
  residue identity is computable, so the level effect is a function of the two populations); real
  deployed corpora as transport studies.

## 4. Registered priors (before the deciding runs)

- **P1 (the level is first-order)** — at fixed `(τ, r)`, moving corpus → script level changes the flag
  count by a factor **≥ 2**. Justification: the residue identity above (set inclusion ⇒ monotone
  residue); the magnitude is set by the sub-community-generic share (reader measured 163 of 252 shared
  bigrams on the densest pair).
- **P2 (systematic, language-correlated)** — a corpus-wide frame misclassifies a small-language
  sub-community's register as shared content, and the misclassified set is **over-represented** in the
  minority-script stratum relative to that stratum's share of eligible pairs. Justification: a DF cutoff
  is a **share**, so blindness is a function of population size, which is correlated with language ⇒
  systematic, not random.
- **P3 (enrichment needs a matched population)** — an enrichment with the two sides in different classes
  overstates the detector and a class-matched reading is **smaller**; pooling classes with different
  base rates averages them into an artifact (`rate = Σ_c share_c · rate_c`). Justification: the
  arithmetic is an identity; the reader's measurement moved 21× → 35.8× as flags moved 156 → 25.

**Registered success criteria**: (i) measured flags vs the exact residue identity agree on every cell;
(ii) each level effect bracketed with a two-sided control at the adjacent level; (iii) the systematic
claim as a stratified concentration ratio with an interval; (iv) rates over eligible subsets, matched
enrichment first. An unmet criterion is reported as unmet with its reason.

## 5. Round log and plan

**R584 (2026-10-09) — the de-risk spike: `spike_v0.py`.**

*Result.* The registered **set-containment identity is REFUTED** (24/24 cells fail both directions);
the exact relation is the **dilution law** `df_corpus(u) = s·df_P(u)` (exact to 8.7e-19 over 685,502
confined word-3 pairs); the mechanism is measured as a **share law** (88.6 % → 76.0 % → 68.2 % → 0.0 %);
it is **statistic-dependent** (word-3 ≫ char-bigram); the finer frame is **larger** (44 vs 7).
Certificates: dilution asserted over every admitted pair; a two-sided plant corpus (share 1.0 → both
containments hold; small share → `F_pool ⊄ F_corpus` with `hidden ≥ 1`); a confinement-filter plant
(non-confined units excluded); `--selftest` **6/6**; the corpus SHA256-verified **on every read**.
Recorded on #132 as comment `6071710360`, and the body corrected **in place** (Abstract, P1's
justification, criterion (i)) — **no prior changed**, and no result on the guard's flags is claimed.

*Pitfall (recorded).* The first draft of the plant corpus asserted that plant A must have **both**
containment counts zero and that plant B's violation needs its own threshold. Plant A's book-unique
unit is pool-generic and corpus-invisible **even at share 1/3** — the mechanism, not a defect. The
**expectation** was wrong, not the assertion; repaired the sentence, never the check (Class 206(b)/208(a)).

**R585 (2026-10-09) — the register ladder: P1 and P2.**

*Corpus.* 14 non-English Gutenberg texts (Fr/De/Es/It) added under `corpus_i18n/`, SHA256-pinned
alongside the 8 English books (`SHA256SUMS` in each directory, re-verified **on every read**; the
instrument refuses to measure an unverified corpus). After the 200-character document cap: **7,521
documents** ({de 400, en 3200, es 1767, fr 800, it 1354}). Two genuine communities of the same
corpus: **Italian share 0.180**, **English share 0.425**.

*The instrument (`spike_v1.py`).* The frame acts on the **residue gate only** (`sim` is computed on
the raw unit sets, so it is level-independent; the two levels differ only in which shared units are
removed). The construct is a **register** — a recurring block a community shares (a greeting, a
licence header, a template clause) — with pool prevalence `phi` and corpus prevalence `s·phi`. A
register is hidden from a corpus-wide frame exactly when `s·phi < theta`; the critical prevalence is
`phi* = theta / s`.

*Result — P1 CONFIRMED (level effect >= 2x).* word-3, tau=0.5, theta=0.05: **below** the critical
prevalence the corpus-level frame fires on **120/120** community pairs while the pool-level frame
fires on **0/120** — a level-induced count of 120, ratio infinite, and that zero is **DERIVED** (all
27 register units lie in the pool frame, so the residue is `0 < r = 10`). **Above** it: 0/0, at every
tau. The outcome is **statistic-dependent and the statistic, not the community, decides whether a
stratum exists**: the char-bigram register is hidden from the corpus frame in **0/48** cells
(universal bigrams are visible to a corpus-wide frame at any share), the word-3 register in
**48/48** cells, exactly when `s·phi < theta`.

*Result — P2 CONFIRMED, quantitatively.* The critical prevalence is **measured, not assumed**. At
theta=0.05 the Italian community flips between phi=0.20 (corpus prevalence 0.036 -> hidden -> 107/107
fires level-induced) and phi=0.30 (0.054 -> visible -> 0), **bracketing the predicted 0.278**; the
English community flips between 0.10 (0.043) and 0.15 (0.064), **bracketing 0.118**. So a register at
phi = 0.20 is **missed entirely in the minority community (rate 1.000) and caught entirely in the
majority community (rate 0.000)**: the misclassification is over-represented in the smaller-share
stratum, and the band of blindness is the interval `(0, theta/s)` — wider for the smaller share.

*Controls.* phi = 0.00 (register in no document -> in no frame -> induced **exactly 0**) and
phi = 1.00 (register in every corpus document -> in both frames -> induced **exactly 0**) bracket the
effect at both ends. Templates: an exact repost and a 1 % edit both fire under the corpus frame,
3/3 cells. Certificate: `corpus_prevalence < theta  <=>  register hidden from the corpus frame`,
48/48 word-3 cells. `--selftest` **7/7**; the results artefact is **byte-identical across two runs**
(sha256 `2852a079...`).

*Pitfall (Class 219).* (a) The first draft's `formula` was a **unique string** (present in one
document) — generic in *no* frame, so the level could not bite; an instrument that reports "no effect"
because its **object does not exist**. A register must be generic *inside* the community. (b) The frame
acts on the residue gate only, but the first draft attributed the fires to the **similarity** gate; a
per-gate decomposition is required *before* attribution. (c) The certificate's own **predictor** was
wrong (`share x register-fraction`, double-counting the share), and the tell was that **all 12
violations clustered at phi=1.0**, where the predictor's assumption ("the register is a pool prefix")
fails; a predictor and its subject must be in the **same units**.

*Next (R586).* Extend the ladder to the `(theta, tau, r)` grid over both statistics, carrying the
**eligible-subset rate** (rant item 16: a rate over the subset where the test is defined, with the
dilution factor stated), then compose the manuscript.

Contribution level target: `theory+empirics`.

**R586 (2026-10-09) — the (theta, tau, r) grid and the eligible-subset rate.**

*Instrument.* `spike_v2.py` re-runs the R585 construct (7,521 pinned documents; Italian share 0.180,
English 0.425) over **1,980 cells** = 2 strata x 2 statistics x 6 register prevalences x 3 thetas x 3
taus x 5 residue thresholds x **2 sampling rules**. The `--selftest` is 7/7 and the artefact is
byte-identical across two runs, including from a foreign working directory.

*The r axis -- a boundary, EXPLAINED.* The level-induced effect is **flat over r = 5, 10, 20, 27**
(i.e. over `1 <= r <= register_units = 27`) and **0 at r = 40**. The zero is not a small measurement
but a **DERIVED** one, and the instrument now shows why: at phi = 0.20 the corpus residue over the
eligible pairs never exceeds **28** (the 27 register units plus one generic unit) while the pool
residue never exceeds **1**, so at r = 40 the corpus level cannot fire on ANY pair. Two certificates
carry it: *the corpus level cannot fire where its residue never reaches r* and *the level-induced
residue gap never exceeds the register's own size* (the register is the whole of the hidden material
in these documents). The guard's second gate therefore needs `r <= register_units` for a community
register to be able to decide it at all.

*The eligible subset (rant item 16).* A level can act only on a pair that PASSES the similarity gate;
a pair with `sim < tau` is **ineligible**, not a non-flag, and counting it deflates the rate by
exactly the pass fraction. The instrument therefore reports
`eligible_rate = level_induced / sim_gate_pass` with the **dilution** `sim_gate_pass / n_pairs`
beside it, and prints `undef` -- never `0.000` -- when nothing passed. Two sampling rules make the
point measurable:

- **affected** (both members carry the register -- the subpopulation the level acts on): the rate is
  a clean **step**, **1.000** at phi = 0.05 / 0.10 / 0.20 (corpus prevalence 0.009 / 0.018 / 0.036,
  i.e. below the critical prevalence 0.278) and **0.000** at phi = 0.30 / 1.00 (0.054 / 1.000, above
  it) -- 120/120, 120/120, 108/108 then 0/79, 0/37.
- **community** (random pairs of the community, what a deployed guard sees): the same effect, diluted
  -- at phi = 0.20, **3/3 eligible = 1.000** with dilution **0.025**, so the naive count over all 120
  pairs is 3. The dilution is the whole difference between the two numbers.

So P1 and P2 hold across the grid, and the rate that should be quoted is the eligible one, with the
dilution stated.

*Pitfall (Class 220, a recurrence of Class 219(c)).* The first version of the r-boundary certificate
compared an AGGREGATE (`max` residue over all eligible pairs) against a PER-PAIR condition, and fired
24/1980 "violations" that were correct measurements: different pairs carry different residues, so the
max over the population is not the value that decides any single pair. Repairing the sentence (not the
data) to *the corpus level cannot fire where its residue NEVER reaches r* gives 1980/1980. It is the
same defect as R585's: **a certificate's own PREDICTOR is a claim, and an aggregate is not an
instance.**

*Status.* P1 confirmed (level effect; declared falsifier was < 2x) and P2 confirmed quantitatively
(`phi* = theta/s` measured). Next (R587): Phase B -- compose the manuscript (`theory+empirics`).

**R587-R589 (Phase B, evidence / figure / reference layers).** The flat package `papers/issue-132/`
was assembled: R587 committed the three instruments + reports and the SHA256-pinned five-language
corpus + `reproduce.sh` (ALL GREEN under CPython 3.9.6 and 3.13.9, and from a `git archive`
export); R588 the five generated figures + `make_figures.py` (7/7 byte-identical); R589 the verified
reference layer (`refscan132.py`, 257/257 title-verified). Manuscript not yet composed.

**R590 (2026-10-10) -- the null is also a level: `spike_v3.py`.**

*Why.* The host's reader thread filed a new project-matched rant (`2026-10-09T13:21:21`, items
22-24) that corrects item 21 and states three laws about the NULL -- the same "the population
decides" mechanism this paper measures for the frame, one layer down the pipeline. Items 19-21 are
already carried by P1/P2 and are not re-processed; items 22-24 are what the registration did not
carry, so R590 measures them as the evidence for **P3** (an enrichment must be re-computed after the
same filter the scan applies, and a null is a population like any other).

*Instrument.* `spike_v3.py` plants ground truth by construction into the pinned corpus: 24 verbatim
re-posts (hash-equal after normalisation -- decidable by a hash) and 12 edited re-posts at a declared
2 % character substitution rate (NOT hash-equal -- the class the statistics must carry). 4,763
documents. Three law families, each with its own certificate; `--selftest` **8/8**; the artefact is
**byte-identical across two runs** (sha256 `25073106...`).

*L1 -- the filter chain (item 22).* E is a product of two measured rates: `E = N_eligible x P_null`,
and the identity `E_matched/E_naive = (N_eligible/N_raw) x P_null` is asserted exactly (1e-12). The
eligibility rule is a **threshold**, so its effect is a **sensitivity curve**, not a point: the
one-sided inflation (a chain applied to the scan but not the null) runs **1.00x (>=10 de-generic
units) -> 1.40x (>=25) -> 3.88x (>=50) -> 16.68x (>=100)**. On long Gutenberg documents the reader's
`>=10` rule is a near no-op (null survivor 0.9995); the mechanism is real and its magnitude is a
function of where the rule is set and of the document-length profile -- a stated transport limit.

*L2 -- interval ownership (item 23).* The bootstrap over the whole fire population gives the
degenerate **[1.0, 1.0]** (25 of 37 fires are verbatim, Dice = 1.0); the non-identical subset gives
**[0.739, 0.880], median 0.788**. `interval_transfers = False`: **an interval belongs to the
population it RESAMPLED**. The small count (12) owns only a count-based bound -- Poisson 95 % upper
**19.4 (one-sided) / 21.0 (two-sided)** -- and the convention is part of the number.

*L3 -- the joint profile (item 24).* Cell = fraction of reference scores strictly below their own
null's median; a calibrated null reads 0.5. On the **control** (cross-language matched-length
unrelated pairs), `anchor = 0.487`, `exchangeable = 0.460` -- both calibrated -- while **`marginal`
(both members replaced independently, each matched to its own length) = 0.587**, a **+0.087**
departure: reproducing the two length *marginals* is not reproducing the pair's *joint*. The freed
variable is the PAIRING. On the **near-duplicate** set every constrained null reads **0.000** (max
discriminability), while the exchangeable null reads **0.324** -- a null drawn from a pool that
CONTAINS the near-duplicates inflates.

*Certificates.* L1: the chain cannot raise the null survivor rate; the E identity holds exactly. L3:
the exchangeable null reads ~0.5 on the control and the anchored null too (pairing preserved) --
and the selftest plants a **biased** null that must NOT read 0.5, so the check fires on its own
fault.

*Pitfall (Class 224).* The first draft's L1 filter used **char-bigram** de-generic units, which are
corpus-generic on Gutenberg (median 2 per document) so **every** scan pair failed eligibility and the
measurement was a degenerate 0/0 -- the same "the object does not exist" defect the R585 instrument
had (Class 219(a)). The unit was wrong, not the corpus: the rule is on **word-3** de-generic units
(median 51). Also repaired: `E_matched` was first written as `observed x P_null` (observed itself),
conflating the numerator with the expectation -- E is `N_eligible x P_null`, both measured.

*Status.* Items 22-24 measured; P3's evidence now rests on a deterministic instrument with
certificates. Next (R591): carry `spike_v3.py` into the package (evidence layer) and wire it into
`reproduce.sh`, then compose the manuscript.
