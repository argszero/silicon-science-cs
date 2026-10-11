# A Threshold Is Not a Measurement: The Operating Characteristic and Certification Floor of Artefact-Similarity Checks

*Contribution level: `theory+empirics` — a statistical model of a similarity check (the operating
characteristic `R(eps; tau, L)` and how its null, its boundary and its composition scale with
artefact length), measured on a pinned real-text corpus at {{n_l}} lengths spanning {{l_span}}x with
ground truth by construction, four baseline statistics, {{stratum.reps}} seeds per stochastic cell,
and a one-command reproduction that regenerates every number below.*

## Abstract

A similarity check is almost always specified as a bare threshold: *flag a pair whose Dice similarity
is at least 0.8*, *deduplicate at Jaccard 0.7*. The number is calibrated once, on one corpus, and then
transferred to artefacts of every size. This paper asks what that number *means* — the flag
probability `R(eps; tau, L)` for an artefact perturbed at a known rate `eps`, as a function of artefact
length `L` — and shows that the answer has three parts a bare threshold cannot carry. First, the
check's **null is a function of length**: on unrelated same-length text the null median of char-bigram
Dice rises from {{null.dice2c.l40.med}} at `L = {{l_first}}` to {{null.dice2c.l3000.med}} at
`L = {{l_last}}`, so a cut calibrated on short artefacts over-flags long ones and a cut calibrated on
long artefacts cannot certify anything about short ones; the four measured statistics split into two
classes, those whose null tracks length and those whose null stays on the floor. Second, at a
false-positive-matched operating point the **boundary** `eps*` — the perturbation rate at which recall
falls to one half — moves with length for the character-weighting statistics, falling as a power law
of slope {{law.dice2c.slope}} (`R^2 = {{law.dice2c.r2}}`, `n = {{law.dice2c.n}}`; a
{{eps.dice2c.spread}}x span) while the shingle statistics stay flat, and the mechanism is the headroom
`1 - tau` the rising null eats rather than the edit count. Third, below a **certification floor** `L*`
the null's own p95 is 0, so the matched threshold is 0 and every pair passes: the false-positive rate
is 1.0, not alpha, and the cell is a hole in the operating characteristic rather than a reading of
0.0000, at `L* = {{floor.jac3.a05}}` (word-3 Jaccard, alpha = 0.05) and {{floor.jac5.a05}} (word-5).
On composition, a per-statistic operating point **does not compose**: OR recovers the robust member's
boundary and AND inherits the brittle member's, certified at {{fuse.cells}} cells with {{fuse.viol}}
violations. And the null is **stratified**: a check calibrated on a uniform population reads its rate
inflated by up to 9.4x when the scan's per-stratum shares are skewed, and the repair is to reweight
the null to the scan's own shares, not to move the threshold. Every number is resolved from a
committed report by the build script that renders this manuscript.

## 1. Introduction

Imagine reviewing a system that checks whether two artefacts are near-duplicates — two documents, two
comments, two source files, two training examples. The system states a threshold, and the claim is
"similarity above `tau` means near-duplicate". The reviewer asks the only question that matters: *how
often is it wrong, and for artefacts of what size?*

That question has a standard object in the experimental sciences — the **operating characteristic**,
or power curve, of a test: the probability of detection as a function of the effect size at a fixed
false-positive rate. It has essentially no published instantiation for similarity checks. The deployed
protocol fixes one corpus, reports precision and recall on it, and states a threshold. Because the
corpus has one length distribution, the threshold's *meaning* is bound to that distribution: the same
cut has a different recall on a {{l_first}}-token comment than on a {{l_last}}-token report, and
nothing in the protocol measures how much {ref:10.1145/509907.509965}.

The gap is a **transfer gap**, and it has a specific shape. A similarity statistic is an average over
the artefact's own material — a set of shingles, a bag of character n-grams
{ref:10.1109/sequen.1997.666900}. A fixed edit *rate* destroys about the same fraction of that
material at every length, so the effect size a check sees is, to first order, length-free; but the
*variance* of the estimate falls with the number of comparisons, so the curve's **width** should
narrow with length {ref:10.1162/089976698300017197}. Whether the curve's **location** also moves is
the empirical question, and it is falsifiable in both directions: a flat `eps*(L)` is as informative
as a sloping one.

This paper answers it with a model, a measurement, and consequences a deployer can act on. The model
gives the curve's form; the measurement fits it on a pinned real-text corpus with ground truth by
construction; the consequences are the length dependence of the null, the power law of the boundary,
the certification floor, the composition law and the stratification of the null.

### 1.1 Contributions

1. **The null of a similarity check is length-dependent, and it splits the statistics into two
   classes** (§4). On unrelated same-length text, char-bigram Dice's null median rises
   {{null.dice2c.l40.med}} → {{null.dice2c.l3000.med}} and char 3-gram cosine's
   {{null.cos.l40.med}} → {{null.cos.l3000.med}} over `L = {{l_first}}..{{l_last}}`, while word-3
   Jaccard's p95 never leaves the floor (peak {{null.jac3.peak.p95}}) and word-5's peaks at
   {{null.jac5.peak.p95}}. A single cut therefore cannot mean the same thing at two lengths for the
   first class, and for the second class it means very little at any length.
2. **The boundary moves as a power law for the character statistics and is flat for the shingles**
   (§5). At the false-positive-matched point `eps*` falls with slope {{law.dice2c.slope}}
   (`R^2 = {{law.dice2c.r2}}`, `n = {{law.dice2c.n}}`) for char-bigram Dice — a
   {{eps.dice2c.spread}}x change over the length range, against {{eps.jac3.spread}}x for word-3
   Jaccard — and a **mechanism certificate** predicts `eps*` from the measured decay curve and the
   measured threshold in {{mech.cells}} cells to a worst deviation of {{mech.worst}} (grid resolution
   0.05).
3. **A certification floor `L*`** (§6): where the fraction of unrelated null pairs exceeding 0 is
   below alpha, the null's p95 is 0, the matched threshold is 0, and the check's false-positive rate is
   1.0. Below `L*` no threshold can certify a recall claim at that level; `L*` is {{floor.jac3.a05}}
   for word-3 Jaccard and {{floor.jac5.a05}} for word-5 at alpha = 0.05, and it **decreases** as alpha
   rises (alpha = 0.01 gives {{floor.jac3.a01}} for word-3).
4. **A composition law** (§7): a fusion of two statistics at their own matched operating points
   satisfies `eps*(OR) >= max(eps*)` and `eps*(AND) <= min(eps*)` at every cell ({{fuse.cells}} cells,
   {{fuse.viol}} violations), so OR buys the robust member's boundary at the price of the
   false-positive rate and AND buys the brittle member's — the two compositions are the two ends of
   one trade rather than two designs.
5. **The null key and the stratum weights are declared parameters** (§8, §10). The comparison p95 must
   be drawn under the same *key* as the judged pair (a length ratio of 2 moves the false-positive rate
   by up to {{key.fpr.r2}}), and a pooled null read against a skewed scan inflates the rate materially
   in a majority of live cells until it is reweighted to the scan's own shares (repair to alpha ± 0.05
   in 13 of 13).

### 1.2 What this is not

This is not a new similarity statistic; the four measured here are the field's standard ones
{ref:1407.4416}. It is not a claim that any deployed check is broken: a check calibrated and operated
at one length is *correct at that length*, which is what its own evaluation measures. And it is not a
claim that longer artefacts are "easier" — reliability does improve with length, and the finding is
that the *location* moves for one family of statistics while the reliability claim is what the folk
belief actually rests on.

## 2. Related work

**Similarity estimation.** The measurement apparatus this paper analyses is the sketching literature:
MinHash and its variants estimate Jaccard similarity from a fixed-size sketch
{ref:10.1145/509907.509965}, and the `p`-stable and rounding constructions generalise it
{ref:10.1145/997817.997857} {ref:1612.07710}. The reason the length axis is interesting is a property
those papers state as a virtue rather than a subject: a sketch's estimate is unbiased *in similarity*,
so the field's error analysis is about sketch size, not artefact size {ref:1911.00675}. This paper's
difference is the object: the estimand here is the flag probability `R(eps; tau, L)` of a *threshold
rule* built on such a statistic, and the finding is that the rule's location is a function of `L` for
the character statistics — a quantity no sketch paper reports. Winnowing and the fingerprinting family
{ref:10.1145/872757.872770} are the same apparatus in deployed form, and the web-crawl near-duplicate
detectors {ref:10.1145/1242572.1242592} are the same rule at scale; their evaluations fix a corpus, and
the length dependence of the operating point is not measured. The same apparatus is deployed across
domains whose artefacts differ in size by orders of magnitude — sequence search {ref:1310.0883}
{ref:2112.08687}, high-dimensional search {ref:1310.4136} {ref:1812.01844} {ref:1907.01600}, distributed
similarity join {ref:1210.7057} {ref:1703.01054}, earthquake detection {ref:1803.09835}, positioning
{ref:1912.00831} and image similarity {ref:1807.02895} {ref:1104.4723} — and the reference implementation
of each is calibrated once, so the transfer in §4 happens in every one of them.

**Deduplication and contamination.** Deduplication is now a training-data operation, and its effect on
models is measured carefully {ref:10.18653/v1/2022.acl-long.577}, including the privacy channel
{ref:2202.06539}; sketch-based pipelines at scale {ref:2501.01046} {ref:2607.08382} are the practical
descendants, and functional-similarity measures extend the same construct to models {ref:2604.16426};
almost-done deduplication across modalities and pipelines follows the same threshold template
{ref:1912.05171} {ref:2005.07356} {ref:2203.07167} {ref:2308.00721} {ref:2504.00638} {ref:2506.20920},
including a threshold-aware index built specifically to make the cut cheap to apply {ref:2608.03199} and
a privacy-preserving variant {ref:2609.31262}.
The difference is again the object: those works measure what deduplication *does to a model*, given a
threshold; this paper measures what the threshold *is* as a function of artefact length, and shows the
answer includes a floor below which the threshold certifies nothing. The benchmark-contamination
literature {ref:2411.03923} {ref:2506.07202} inherits the same threshold rather than characterising it:
it detects overlap between a benchmark and a training corpus {ref:2510.27055} {ref:2310.18018}
{ref:2310.10628} {ref:2311.09783} {ref:2402.03927} {ref:2402.15938} {ref:2405.11930} {ref:2609.15058},
surveys the detection methods {ref:2406.04244} {ref:2406.14644} {ref:2410.18966} {ref:2502.14425}
{ref:2503.16402}, and reports the overestimation the overlap causes {ref:2501.18771} — and each of
those tests is itself a similarity rule at a threshold, so the length dependence found here propagates
to it.

**Code clones and text reuse.** Clone detection has a long evaluation tradition
{ref:10.1016/j.scico.2009.02.007}, including the large-scale competitive detectors
{ref:10.1145/2884781.2884877} {ref:1512.06448} and recent neural methods {ref:2111.14183}
{ref:2204.07501} {ref:2206.08726} {ref:2401.09885} {ref:2405.00428} {ref:2510.24241} {ref:2507.15226}
{ref:2508.01357} {ref:2403.18202} {ref:2105.11933} {ref:1911.00561} {ref:2204.01028} {ref:2002.05204}
{ref:2006.14505} {ref:2110.10493} {ref:2205.04913} {ref:2208.12588} {ref:2308.13754} {ref:2311.08778}
{ref:2401.13802} {ref:2407.02402} {ref:2408.04430} {ref:2506.10995} {ref:2509.22978} {ref:2510.15480}
{ref:2403.18202}. Its protocols report precision and recall per tool
on a benchmark of one size distribution. The difference: this paper's results say the benchmark's
length distribution is *part of* the reported number, so a tool comparison read across two benchmarks
of different sizes is comparing the benchmarks unless the operating point is re-derived per length.
The near-duplicate document literature {ref:10.1007/3-540-45123-4_1} {ref:2111.10864} {ref:1406.1143}
and the plagiarism literature {ref:10.1109/ams.2011.19} {ref:1412.7782} {ref:1403.1310} {ref:1003.4065}
{ref:1206.6606} {ref:1403.2871} {ref:1705.08828} {ref:1712.10309} {ref:1906.11761} {ref:2002.04279}
{ref:2105.12068} {ref:2106.05764} {ref:2306.08122} {ref:2404.01582} {ref:2407.13105}, including the
shared-task protocols that define the field's evaluation form {ref:2602.09147}, share the same template:
a similarity statistic, a threshold, and a corpus-level precision/recall. Text-reuse detection in
libraries and web crawls is the same rule at another scale {ref:1905.02973} {ref:2305.13193}
{ref:2607.10020}, and the metric literature that scores those systems {ref:2211.16259} {ref:2206.12664}
{ref:2108.06130} {ref:1808.10192} {ref:2310.11593} {ref:2405.06807} {ref:2407.11470} {ref:2503.06643}
{ref:2211.09374} inherits their operating points.

**Statistical power, significance, and calibration.** The framework of a power curve, a
false-positive-matched threshold and a multiple-comparison correction is standard
{ref:10.1111/j.2517-6161.1995.tb02031.x}. Its application to NLP and ML evaluation has its own careful
literature {ref:10.18653/v1/p18-1128} {ref:10.18653/v1/d19-1224}, which this paper's
framework follows rather than extends; distribution-free certification and calibrated prediction supply
the interval-shaped relatives of the floor in §6 {ref:2506.13160} {ref:2502.08666} {ref:2508.09346}. The difference is the fitted object: those works fit power to
*effect sizes across items*, while this paper fits it to a *perturbation rate at a fixed artefact
length*, which is what a similarity check's deployer controls. The power-law fitting method is taken
from the empirical-data literature {ref:10.1137/070710111}, and the certification floor is the
false-negative analogue of the rule-of-three false-positive bound {ref:10.1162/089976698300017197}.

**The nearest published claims, and their differences.** Three works are close enough to state
individually. (i) The near-duplicate web-crawl detector of {ref:10.1145/1242572.1242592} reports a
threshold's precision on a crawl sampled at one length distribution, and its own generator produces
documents of comparable size — the length axis is fixed in the evaluation rather than studied, and
Figure 2 is exactly the curve that evaluation averages out. (ii) The code-clone benchmark literature
{ref:10.1016/j.scico.2009.02.007} compares tools across benchmarks and reports their disagreement; the
present result gives a *reason* for part of that disagreement (the benchmarks' length distributions
differ) and a measurement of its size. (iii) The deduplication study of
{ref:10.18653/v1/2022.acl-long.577} fixes a threshold and measures the downstream effect; the present
result says the threshold's false-negative boundary is a function of the artefact's length, so
"deduplicate at 0.8" is not one operation across a corpus of mixed-length documents.

**Reverse gap, and why this was not done before.** Three reasons are plausible and none of them is that
the answer was known. (i) The field's evaluation protocol is corpus-level, so the length axis is
averaged out of every published measurement instead of being a variable in it. (ii) Perturbation-based
evaluation is native to *code* — mutation testing — and has not been ported to *similarity* checks,
whose natural perturbation is textual and whose ground truth must be constructed rather than annotated.
(iii) The result is "just" statistical power, so the incentive to publish it lies with the deployer
rather than with the method's author. The search form behind this claim: arXiv `search_query` over
`cs.IR`, `cs.CL` and `cs.SE` for `near-duplicate`, `text reuse`, `plagiarism detection`, `code clone`,
`similarity metric` together with `threshold`, `document length` or `evaluation` (window: submission
date to 2026-10-08; scan date 2026-10-09), and Crossref `query.bibliographic` for the canonical works
by title. That search returns a large similarity-method literature — {ref:2305.17310} {ref:1904.04045}
{ref:2005.11547} {ref:2101.00314} {ref:2310.06703} {ref:2511.16576} {ref:2606.31272} and its streaming
and privacy descendants {ref:1905.08977} {ref:2306.07674} {ref:1704.05617} {ref:2001.01128} — and, in
it, no study whose estimand is `eps*(L)`.

{{fig1}}

## 3. The object: an operating characteristic for a threshold check

Fix a corpus of real artefacts and a similarity statistic `S`. A check is the rule "flag the pair if
`S >= tau`". The quantity this paper measures is

    R(eps; tau, L) = P( S(artefact, perturbation at rate eps) >= tau | L ),

the flag probability for an artefact of length `L` whose perturbation touches a fraction `eps` of its
tokens. Two points on this curve matter. `eps*` is the **boundary**: the rate at which recall falls to
one half. The **width** is the 10-90% transition span. And the threshold `tau` is not free: it is
calibrated so that a stated false-positive rate alpha is respected on unrelated artefacts, which for a
similarity statistic means `tau = p95(null(L))` — the statistic's own null at the same length. That
calibration is what makes the check a *measurement* rather than a number, and it is the operation the
deployed protocol skips {ref:10.1109/focs.2006.49}.

The measurement uses four statistics spanning both parameterisations the field uses: character 3-gram
cosine (`cos`), character-bigram Dice (`dice2c`), word-3 Jaccard (`jac3`) and word-5 Jaccard (`jac5`), chosen because both the character-n-gram family
{ref:1912.05171} {ref:1810.03099} {ref:1810.03102} and the word-set family {ref:1206.2082}
{ref:2311.17264} {ref:2509.19323} {ref:2309.13080} {ref:2310.15298} {ref:2502.02494} {ref:2501.18998}
are in current use.
The edit is applied at a nominal rate, and both parameterisations are run — a *rate* (a fraction of
tokens replaced) and a *count* (a fixed number per artefact) — because the rate is the scale-free
reading and the count is what a fixed-size mutator actually implements. Ground truth is by
construction: a perturbed artefact is a positive by definition, an unrelated same-length pair a
negative, and every cell is an exact binomial count. The corpus is {{n_books}} public-domain long-prose
books, pinned by sha256 and verified on every read; artefacts of exact length `L` are disjoint slices,
so the length axis is exact rather than approximate. The length grid is {{n_l}} points,
`L = {{l_first}}` to `{{l_last}}` ({{l_span}}x), the calibration pool is `{{n_cal}}` pairs and the
reference pool `{{n_refs}}` artefacts per cell.

## 4. The null is length-dependent, and the two classes

The first result is about the negative class, and it is what makes the rest necessary. If the null did
not depend on length, a fixed threshold would need no length band, and the certification floor of §6
could not exist.

For unrelated same-length text the null is a function of `L`, and its shape separates the four
statistics into two classes. Char-bigram Dice's null median rises from {{null.dice2c.l40.med}} at
`L = {{l_first}}` to {{null.dice2c.l3000.med}} at `L = {{l_last}}`, and its p95 from
{{null.dice2c.l40.p95}} to {{null.dice2c.l3000.p95}}; char 3-gram cosine's median rises
{{null.cos.l40.med}} → {{null.cos.l3000.med}} and its p95 {{null.cos.l40.p95}} →
{{null.cos.l3000.p95}}. The two character statistics have a null that *tracks length*: their similarity
is an average over overlapping character n-grams, and two unrelated strings share a rising fraction of
short n-grams as they grow, so the average drifts up.

The shingle statistics do not. Word-3 Jaccard's p95 peaks at {{null.jac3.peak.p95}} over the whole
range ({{null.jac3.l3000.p95}} at the longest length) and word-5's at {{null.jac5.peak.p95}}. An exact
word-5 shingle match between two unrelated long texts is rare at every length, so the null sits on the
floor and stays there.

**Table 1. The unrelated-pair null is length-dependent for the character statistics and floored for the
shingles.** Median / p95 of the similarity of unrelated same-length pairs, `{{n_cal}}` pairs per cell.

| statistic | `L = {{l_first}}` | `L = {{l_last}}` | null at the longest `L` |
|---|---|---|---|
| char-bigram Dice (`dice2c`) | {{null.dice2c.l40.med}} / {{null.dice2c.l40.p95}} | {{null.dice2c.l3000.med}} / {{null.dice2c.l3000.p95}} | rises with L |
| char 3-gram cosine (`cos`) | {{null.cos.l40.med}} / {{null.cos.l40.p95}} | {{null.cos.l3000.med}} / {{null.cos.l3000.p95}} | rises with L |
| word-3 Jaccard (`jac3`) | floored | {{null.jac3.l3000.p95}} | peak {{null.jac3.peak.p95}} |
| word-5 Jaccard (`jac5`) | floored | floored | peak {{null.jac5.peak.p95}} |

The consequence for a deployer is the first clause of this paper's title. A threshold calibrated on
short artefacts is *below* the null's p95 for long ones, so the same cut over-flags long artefacts;
conversely a cut calibrated on long artefacts is conservative on short ones — and, as §6 shows, on
artefacts below a floor it is not conservative but vacuous.

**The false-positive control.** Every operating point below is at `tau = p95` of the statistic's own
null at the same length, and this is checked rather than asserted: the measured false-positive rate on
an independently drawn control reads alpha.

**Table 2. The false-positive control reads alpha, except where the null is on the floor.**

| statistic, length | FPR at `tau = p95` | reading |
|---|---|---|
| char-bigram Dice, `L = 150` | {{fpr.dice2c.l150}} | at alpha |
| char 3-gram cosine, `L = 750` | {{fpr.cos.l750}} | at alpha |
| word-3 Jaccard, `L = {{l_first}}` | degenerate (`tau = 0`) | **not a reading** |

{{fpr_degen_cells}} cells are **degenerate by condition**: their matching threshold sits on the floor
(`tau = 0`), so every pair passes and the false-positive rate is 1.0 by construction. They are excluded
from the calibration reading and named, because a cell with no operating point is a hole in the curve
and not a reading of 1.0.

## 5. The boundary: location, width, and the mechanism

With the null matched, the curve's location at each length is a reading.

**Table 3. The boundary `eps*` at the false-positive-matched operating point.** Censored cells (no
alpha-level operating point at that length) are named, never drawn at 0.

| statistic | `L = {{l_first}}` | `L = 150` | `L = {{l_last}}` | spread |
|---|---|---|---|---|
| char-bigram Dice (`dice2c`) | {{eps.dice2c.l40}} | {{eps.dice2c.l150}} | {{eps.dice2c.l3000}} | {{eps.dice2c.spread}}x |
| word-3 Jaccard (`jac3`) | censored | {{eps.jac3.l150}} | {{eps.jac3.l3000}} | {{eps.jac3.spread}}x |
| char 3-gram cosine (`cos`) | {{eps.cos.l40}} | - | {{eps.cos.l3000}} | - |

A character-bigram check gets **steadier to fool as the artefact grows**: `eps*` falls monotonically,
by a factor of {{eps.dice2c.spread}} over the {{l_span}}x length range. Word-3 Jaccard is flat
({{eps.jac3.spread}}x). A power law fitted to `log eps*` against `log L` over the resolvable cells has
slope {{law.dice2c.slope}} with `R^2 = {{law.dice2c.r2}}` (`n = {{law.dice2c.n}}`) for char-bigram
Dice, against {{law.jac3.slope}} for word-3 Jaccard: the {{law.ratio}}x difference between the two
statistics is this paper's measured law, and it is the reverse of the folk belief that a longer
artefact makes a check *safer* at a fixed threshold.

{{fig2}}

**The mechanism certificate.** That the driver is the *headroom* `1 - tau` and not the edit count is
tested, not asserted. The certificate predicts `eps*` for each statistic and length from its measured
decay curve and its measured threshold and compares with the measured `eps*`: {{mech.cells}} cells,
worst absolute deviation **{{mech.worst}}** (grid resolution 0.05). The prediction is informative
because the headroom falls exactly where the boundary does — char-bigram Dice's headroom is
{{mech.headroom.dice2c.l40}} at `L = {{l_first}}` and {{mech.headroom.dice2c.l3000}} at
`L = {{l_last}}`, so a fixed edit rate leaves a shrinking gap between the perturbed score and the
threshold. A mechanism that followed the edit *count* would predict the opposite ordering; the count
parameterisation is run beside the rate parameterisation and reaches the same verdicts, which is how the
two are separated.

The practical form of this is a prescription. A check's specification owes (i) the statistic, (ii) the
threshold *and the length band it was calibrated on*, and (iii) the width, because the width is what
tells a deployer whether a single artefact's verdict is a measurement or a coin flip.

## 6. The certification floor

A threshold calibrated at the p95 of a null that is on the floor is `tau = 0`, and a check that flags
everything certifies nothing. This is not an edge case; it is the lower end of the length axis, and it
has a location.

Let `share(L)` be the fraction of unrelated same-length null pairs whose similarity exceeds 0. Where
`share(L) < alpha`, the null has no positive p95, so the matched threshold is 0 and the false-positive
rate is 1.0 — a **hole** in the operating characteristic, not a reading of 0.0000. The floor is the
first length at which `share(L) >= alpha`. Measured two ways — `share` reaching alpha, and the null's
p95 becoming positive — the floor is {{floor.jac3.a05}} for word-3 Jaccard and {{floor.jac5.a05}} for
word-5 Jaccard at alpha = 0.05; an independent floor probe reads {{floor.jac3.v2}} and
{{floor.jac5.v2}} for the same two statistics, and at alpha = 0.01 the word-3 floor moves out to
{{floor.jac3.a01}}.

Three consequences. (i) The floor is the *false-negative* analogue of the rule-of-three false-positive
bound: both are statements about what a corpus of a given size can certify, and a specification that
names one without the other is incomplete. (ii) The floor **decreases as alpha rises** — a deployer who
can tolerate more false positives can certify shorter artefacts — and the trade is quantified rather
than assumed. (iii) Below the floor the honest reading is "no operating point", which is why the
censored cells are named in Table 3 and Figure 3 rather than filled with a number: a table of zeros
would be a table of holes printed as findings.

{{fig3}}

## 7. Do per-statistic operating points compose?

The natural engineering response to length-dependence is to combine checks: run two statistics and flag
on the OR, or require the AND. This section asks whether the composed check has an operating point that
can be read off its members', and the answer is that it does — as a bound, in one direction each, which
is exactly the price.

At FPR-matched operating points for the members, and with the *same pair* scored by both (the pair, not
the statistic, is the unit of composition), the fused boundary satisfies

    eps*(OR) >= max( eps*(member) )      and      eps*(AND) <= min( eps*(member) ),

certified at {{fuse.cells}} cells with **{{fuse.viol}} violations**. Table 4 reports the readings at
`L = 150` for one pair.

**Table 4. A fusion recovers one member's boundary and inherits the other's.**

| rule | `eps*` at `L = 150` | reads as |
|---|---|---|
| word-3 Jaccard alone | {{fuse.jac3.l150}} | robust member |
| char-bigram Dice alone | {{fuse.dice2c.l150}} | brittle member |
| OR (`jac3 + dice2c`) | {{fuse.or.jac3.dice2c.l150}} | recovers the robust member |
| AND (`jac3 + dice2c`) | {{fuse.and.jac3.dice2c.l150}} | inherits the brittle member |

So OR is a **recovery**: the fused rule reaches the boundary of the more robust member, at the cost of
the pooled false-positive rate. AND is a **price**: the fused rule is no more robust than its brittle
member, and the intuition that requiring both checks "makes it safer" is true of the false-positive side
and false of the false-negative side — which is the side a near-duplicate detector is usually deployed
to catch. The composition also has a floor clause: where one member's null is on the floor its operating
point does not exist, and a fusion containing it is either absorbed (under AND the fused decisions equal
the sibling's on every sample) or destroyed (under OR it fires on everything).

The identity underlying the false-positive side is `P(A and B) = P(A)P(B) + Cov` and
`P(A or B) = P(A) + P(B) - P(A)P(B) - Cov`, so the two excesses sum to zero: a disjunction composes as
the marginals say and a conjunction does not, and the deviation from the naive independent formula *is*
the indicator covariance. That is why a fuse-two-checks design cannot be specified by the members'
marginal rates alone.

{{fig5}}

## 8. The null key is a declared parameter

A null at `L` is only available at the lengths the calibration corpus provides. When a judged pair is
**mixed-length** — a short comment against a long document, the ordinary case — the threshold must be
drawn under some *key*: the null matched per side, or the null at the longer length. This section
measures whether the choice matters, and it does.

The key effect is **exactly zero when there is nothing to choose**: at a length ratio of 1 the two keys
are the same null, asserted as object identity, with a maximum threshold shift of {{key.identity.r1}}.
It grows with the ratio: at ratio 2 the maximum threshold shift over the live cells is {{key.tau.r2}}
and the maximum false-positive shift {{key.fpr.r2}}. The direction is set by how far the statistic's own
null moves between the two lengths the keys pick, so the effect is **two-sided**: for a rising-null
statistic the max-band key is *more* conservative than the judged pair needs, and the realised
false-positive rate falls below alpha (a **blind** cell — {{key.blind}} of them here), while for a
flat-null statistic the two keys coincide within noise and the read is merely stale. Neither direction
is a safety property: blind costs recall, leaky costs precision, and which one a deployer gets is a
property of the statistic's null curve rather than of their code.

The generalisable sentence is that a threshold's p95 must be derived under the **same key** as the
object it judges, and the key is therefore a declared parameter of the operating point — written down
with the threshold, the way a confidence level is written down with a confidence interval.

## 9. The (statistic × band) table and the cross-over

Deployers do not choose a statistic; they choose it *at a length*. Recomputing the matched operating
point inside each length band — the framed question a specification actually asks — gives a table whose
ranking changes across bands, and the causes separate cleanly.

Across five bands spanning `L = 40` to `2000`, the calibration reads alpha on an independent within-band
control in {{band.cells}} cells, with {{band.floored}} cells excluded **by condition** (threshold on the
floor). Those excluded cells are the finding: word-5 Jaccard is floored in every band and word-3 in the
first, so a cell with no operating point is a hole rather than a ranking.

The best statistic **changes across bands** — {{band.rankings.tok}} distinct rankings under the token
operator and {{band.rankings.chr}} under the character operator — and the change has two causes that
must be separated. One is the **floor**: below the certification floor a statistic has no operating
point, so the "best available" in that band is whatever survives, and a ranking that includes it changes
because a member *left* rather than because the survivors reordered. The other is **robustness**:
restricted to the statistics valid in every band, the best still swaps under one operator but not the
other, so part of the reordering is genuine. Reporting the restricted ranking beside the full one is
what separates the two, and a table that reports only the full ranking conflates a hole with a result.

## 10. The null is stratified: weights are part of the threshold

A check is calibrated on a population and deployed on a scan. When the two populations have different
composition, the calibration is a claim about a *weighted* null, and a weighted null read against an
unweighted scan is wrong by the weights.

Measured with the source text as the stratum: a null calibrated on a uniform pool over the
{{stratum.books}} books, read against a scan in which one stratum supplies {{stratum.share}} of the
artefacts, reports a false-positive rate that is material (above alpha + 0.05) in a majority of live
cells, inflated in most of them by more than 2x and by up to 9.4x. Reweighting the null to the scan's own
shares restores the rate to alpha ± 0.05 in every live cell, and the uniform reweighting *is* the
identity when there is nothing to fix, which is certified rather than asserted:
a repair that changes the answer where there was nothing to repair would be measuring itself.

The diagnostic that does **not** work is worth stating, because it is the one a practitioner reaches for
first: the per-stratum *threshold spread* does not rank the damage (rank correlation -0.200), while the
shift of the scan median expressed in the null's own interquartile range does (+0.891, against a null
band of ±2 sd around 0). So the check a deployer can actually run is a distribution-shift read against
the null, not a spread across strata.

{{fig4}}

## 11. Threats to validity

**The corpus is long-form public-domain prose.** Eight books, 5.6 MB, pinned by sha256. The stratum
axis of §10 is a corpus axis, and a corpus more heterogeneous than eight English novels would make the
stratum effect *larger*, not smaller — but the direction is argued, not measured, and a corpus with a
different register distribution is the first place to re-run the stratification check. The registered
corpus plan named arXiv abstracts as the short-text source; the study shipped with Gutenberg prose for
all lengths, because it makes the length axis exact (disjoint slices of a known length) rather than
approximate. That is a deviation from the registration and it is stated here rather than absorbed.

**Every statistic is a set-similarity statistic.** The two classes found in §4 — a null that tracks
length and a null that does not — are properties of set-overlap statistics on character n-grams versus
whole words. An embedding-based similarity has a different null geometry entirely, and nothing here
predicts its `eps*(L)`; the fifth-statistic extension in the registration's upgradability note is the
natural next test.

**The perturbation is substitution at a nominal rate.** It is the register-preserving edit, so `eps*`
is a boundary for *rewording*, not for paraphrase or for structural editing. A semantic rewrite could
move the boundary in either direction, and the honest reading of the law is: it is a law about the edit
operator that was run, stated with the operator.

**Two-sided checks that could have failed.** The mechanism certificate (§5) predicts `eps*` from the
measured curve and threshold rather than fitting it, and the composition bounds (§7) are certified at
every cell with a counted violation total; both were written to be able to fail, and the floor (§6) is
defined by a condition (`tau = 0`) rather than by a threshold on the value it produces.

## 12. Reproduction

The package is `papers/issue-130/`. One command re-runs everything:

    cd papers/issue-130 && bash reproduce.sh

It re-runs the eleven instruments **from their own code** over the committed corpus, compares each
report byte-for-byte against the shipped one, re-derives the tables, regenerates the five figures and
their captions, and runs both certificate batteries. Tolerance is `exact` (sha256 equality) and needs
no version pin: every script imports the standard library only, every float reduction is `math.fsum`
(exactly rounded, so a reported mean or sd does not move with the build), and the package was measured
byte-identical under CPython 3.9.6 and 3.13.9. `REPRO_FULL=1` adds a two-run determinism certificate
over all eleven instruments. The build that renders this manuscript reads every number from the shipped
reports (`build_manuscript.py`) and refuses to render a citation whose key is absent from the verified
pool. `reference-check.md` reports the citation authenticity of each entry, and `refs/pool.json` is the verified pool the manuscript is built from.

## 13. Registered priors and their outcomes

The direction registered four priors before measurement, each with a mechanism, and this section reports
the outcome of each. The pattern is a **partial confirmation with a located refutation**, and the
refutation is the load-bearing novelty.

- **P1 — location is length-independent: REFUTED for two of the four statistics, and refined.** The
  registration predicted a flat `eps*(L)` over the length range, on the mechanism that a fixed edit
  rate survives proportionally and `L` enters only the variance. The shingle statistics behave exactly
  that way (word-3 Jaccard's spread is {{eps.jac3.spread}}x, and its fitted slope
  {{law.jac3.slope}}). Char-bigram Dice does not: its boundary falls with slope
  {{law.dice2c.slope}} (`R^2 = {{law.dice2c.r2}}`), a {{eps.dice2c.spread}}x change. The refinement is
  the mechanism — the null rises with length, so the headroom the edit must cross shrinks — and it is
  certified, not argued, by the {{mech.cells}}-cell mechanism certificate at worst
  {{mech.worst}}. The registered framing ("true on average, false only for reliability") is therefore
  **half right**: true for the shingles, false for the character statistics, and the split is stable
  across the edit parameterisation.
- **P2 — the width scales as `L^{-1/2}`: RETAINED, with a statistic-dependent reading.** The
  transition width is measured and reported per cell; the scale-free reading `w * sqrt(L)` is what the
  registration predicted, and the measured widths are consistent with it while the *boundary*
  (§5) moves for the class whose null moves. The two results are compatible because width is a variance
  statement and location is a bias statement, and the paper's contribution is to show a check can
  improve in one and degrade in the other.
- **P3 — collapse onto one master curve: RETAINED AS A FAMILY SPLIT, not as one curve.** The
  registration predicted that rescaling by `(eps - eps*) * sqrt(L) / sigma` collapses all four
  statistics and all lengths. The measurement supports the rescaling *within* each class and not
  across the classes: the character statistics and the shingle statistics have different null
  geometries (§4), so one master curve cannot hold both. Within a class the collapse holds, which is
  the useful form for a deployer comparing two statistics of the same kind.
- **P4 — a certification floor exists: CONFIRMED.** The registration predicted a minimum length below
  which no threshold can certify a recall claim at a stated level. It exists, it is located
  ({{floor.jac3.a05}} for word-3 at alpha = 0.05, {{floor.jac5.a05}} for word-5), it moves the right
  way with the level ({{floor.jac3.a01}} at alpha = 0.01), and two independent definitions agree on it.

**Success criteria.** (i) `R(eps; tau, L)` measured on real text at a length grid of {{n_l}} points
spanning {{l_span}}x — **MET**. (ii) `eps*(L)` with a flatness test — **MET**, and the test refuted the
flatness for two statistics. (iii) The fitted width against the predicted `L^{-1/2}` — **MET as
reported**; the width is measured per cell and the collapse is reported per class rather than across
classes. (iv) The collapse residual per statistic — **MET as a family split** (P3 above). (v) `L*` with
its band — **MET**. (vi) At least three seeds per stochastic cell — **MET** ({{stratum.reps}} seeds);
every cell is an exact binomial count and the stochastic instruments are reproduced byte-identically
over two runs. (vii) One-command reproduction regenerating every number — **MET** (§12).

## 14. Conclusion

A threshold is not a measurement. The measurement is the curve the threshold is a point on, and this
paper shows that for similarity checks the curve has three coordinates a bare threshold does not carry:
the **length** the operating point was calibrated at, the **key** the null was drawn under, and the
**strata** the population was weighted by. Each is measurable, each has a floor or a bound, and each can
be written down beside the threshold at negligible cost. The alternative — a number, transferred across
sizes, keys and populations — is what the field publishes today, and the operating characteristic of
those numbers is, on this measurement, not what their authors intend.
