# The Frame Is a Level: Background-Frame Level as a Declared Parameter of Similarity Guards, and the Systematic Misclassification a Corpus-Wide Frame Leaves

*Contribution level: `theory+empirics` — a formal dilution law for a document-frequency thresholded
background frame (its exact critical share and its residue boundary), measured on SHA256-pinned real
text in five languages with ground truth by construction, two statistics, four baseline levels, and a
one-command byte-identical reproduction that regenerates every number below.*

## Abstract

A near-duplicate guard rarely fires on similarity alone. The rule that ships is a two-stage rule: flag
a pair iff the similarity is at least `tau` **and** the material the two artefacts share *after
subtracting a background frame* is at least `r`. That frame is the guard's definition of "what does
not count as content", and in practice it is computed over the whole corpus, as a document-frequency
cutoff or a stop-list. This paper asks whether the **level** at which the frame is computed — corpus,
script or register pool, author, pair — is a parameter of the guard or an implementation detail, and
answers with a law, a measurement, and the failure the law predicts.

The law is not the identity the direction first registered. The registered form was set containment,
`F_corpus subset F_script subset F_author`; measured on {{v0.docs}} pinned documents it fails in
**{{v0.viol.both}} of {{v0.cells}}** cells **in both directions** (violations {{v0.viol.lo}}–{{v0.viol.hi}}
and {{v0.viol.p.lo}}–{{v0.viol.p.hi}}). The relation that does hold is a **dilution**: for a unit
confined to a population of share `s`, `df_corpus(u) = s * df_pool(u)` **exactly** — worst residual
{{v0.dil.char.worst}} over {{v0.dil.char.pairs}} confined character-bigram pairs and {{v0.dil.w3.worst}}
over {{v0.dil.w3.pairs}} confined word-3-shingle pairs. A unit that is generic inside its own community
is therefore **invisible** to a corpus-wide frame below the critical share `s* = theta / df_pool(u)`,
and the finer frame is strictly *larger* because of it.

On the measurement the level is first-order and the error is systematic, not random. On a
{{v1.docs}}-document five-language corpus with two genuine communities (share {{v1.it.share}} and
{{v1.en.share}} of the corpus), a register whose pooled prevalence is below the critical prevalence is
fired on by the corpus-level frame for **{{v1.lad.05.corpus}} of {{v1.lad.05.pass}}** community pairs
while the community-level frame fires on **none**; above it, both fire on {{v1.lad.hi.corpus}}. The
critical prevalence itself is measured, not assumed, and it is **wider for the smaller community**
({{v1.phi.it}} against {{v1.phi.en}}) — so the same register at the same prevalence is missed entirely
in the minority community and caught entirely in the majority. The deciding variable is the
**statistic**, not the community: the certificate `s * phi < theta  <=>  hidden` holds in
**{{v1.cs.w3.agree}} of {{v1.cs.w3.total}}** word-3-shingle cells and in **{{v1.cs.c2.hidden}} of
{{v1.cs.c2.total}}** character-bigram cells, because universal bigrams are corpus-generic at any share
and so are never hidden. A {{v2.cells}}-cell grid locates the second gate's boundary: the level effect
is flat over every `r` up to the register's own size ({{v2.r.reg}} units, {{v2.r.lo.induced}} induced
fires) and zero above it ({{v2.r.over.induced}} at `r = 40`), a **derived** zero — the corpus residue
never exceeds {{v2.r.over.corpusmax}} units while the community residue never exceeds
{{v2.r.over.poolmax}}. Because a pair below the similarity gate is *ineligible* rather than unflagged,
the rate is reported over the eligible subset: **{{v2.elig.20}}** there, against the same effect
diluted to {{v2.comm.dil}} over random community pairs. Finally the null is a level too: a filter
applied to the scan but not to its null inflates the expectation by {{v3.infl.10}}x at the reader's own
rule and {{v3.infl.100}}x at a stricter one, a bootstrap interval does not transfer to a subset carved
out after it was resampled ([{{v3.int.nonid.lo}}, {{v3.int.nonid.hi}}] against the degenerate
[1.0, 1.0]), and reproducing two length *marginals* is not reproducing the pair's *joint*
({{v3.ctl.marg}} against {{v3.ctl.anchor}} on a calibrated control). Every number is resolved from a
committed report by the build script that renders this manuscript.

## 1. Introduction

Ask a platform team what their duplicate check does and you get a threshold: "we flag at 0.8". Ask what
the check *is* and you get the two-stage rule — a similarity score, and a residue test that asks whether
the shared material surviving the subtraction of a **background frame** is substantial. The frame is
where the system writes down its answer to *what is content and what is boilerplate*: a
document-frequency cutoff removes the units that occur too often to be distinctive {ref:10.1108/00220410410560573},
a stop-list is the same object with the population fixed by hand {ref:10.18653/v1/w18-2502}, and a
template extractor is the same object again for web pages {ref:10.1145/1141277.1141534}.

The frame has a **level**. It can be computed over the whole corpus, over a script or register pool,
over one author, or over the pair itself. Every deployed guard we can find chooses one of those levels
implicitly — usually the corpus — and then quotes a single threshold as if the choice were free. This
paper asks whether it is free. The question has an exact form and a falsifiable answer:

> At a fixed `(tau, r)`, does moving the frame from the corpus level to the community level change the
> guard's flag count, and is the error a corpus-wide frame leaves **systematic in who is writing**
> rather than random?

The answer begins with an identity, and the identity is where the direction's own registration was
wrong. We registered `F_corpus subset F_script subset F_author` as *sets*: a finer frame removes more,
so the residue is monotone in the level. The de-risk spike refutes that immediately — the corpus is the
pool *plus* other documents, so a pool-generic unit's corpus frequency is diluted, not included, and the
containment fails in **{{v0.viol.both}} of {{v0.cells}}** cells in both directions (§4). What actually
holds is the **dilution** `df_corpus(u) = s * df_pool(u)` for units confined to a pool of share `s`,
exact to the last bit. The monotonicity survives, but its mechanism is the opposite of the one
registered: the finer frame is strictly **larger**, and it is larger by exactly the share factor.

That single correction carries the paper. A frame is a threshold on a **share**. A community that is a
small share of the corpus writes material whose corpus frequency is that share times its frequency at
home, so a corpus-wide cutoff is structurally blind to it — and the blindness is not a random error over
pairs; it is concentrated in the community that is small. Section 5 measures the resulting **critical
prevalence** `phi* = theta / s`, and shows it is wider for the minority community, so the same register
is missed there and caught in the majority. Section 6 asks where the effect stops: the residue gate `r`
has a boundary at the register's own size, and every rate is reported over the pairs whose similarity
gate actually opened. Section 7 turns the same lens one layer down, on the null: the population a null
is drawn from decides the expectation, the interval and the pairing, so an enrichment is a claim about a
filter chain and not only about a flag count.

### 1.1 Contributions

1. **The level relation is a dilution, and the registered containment is refuted** (§4). On
   {{v0.docs}} pinned documents, set containment fails in {{v0.viol.both}} of {{v0.cells}} cells in
   both directions; the exact relation `df_corpus(u) = s * df_pool(u)` holds for every confined unit to
   a worst residual of {{v0.dil.w3.worst}} over {{v0.dil.w3.pairs}} word-3 pairs. The mechanism is
   measured as a **share law**: the fraction of a pool's own generic units that a corpus frame misses
   falls {{v0.sweep.1}} % → {{v0.sweep.2}} % → {{v0.sweep.4}} % → **{{v0.sweep.8}} %** as the pool's
   share goes to 1.0 — the control, where the pool *is* the corpus.
2. **The level is first-order, and the deciding variable is the statistic** (§5). Below the critical
   prevalence the corpus frame fires on {{v1.lad.05.corpus}} of {{v1.lad.05.pass}} community pairs while
   the community frame fires on none; above it both read {{v1.lad.hi.corpus}}. The certificate
   `s * phi < theta <=> hidden` holds {{v1.cs.w3.agree}}/{{v1.cs.w3.total}} on word-3 shingles — and
   fails on character bigrams ({{v1.cs.c2.hidden}}/{{v1.cs.c2.total}} hidden), because bigrams are not
   confined to the community. The word-3 case is a **derived** zero: all {{v1.lad.lo.reg}} register
   units lie in the community frame, so the residue is 0 < `r = {{sim.r}}`.
3. **The error is systematic, and the critical prevalence is wider for the minority** (§5). `phi*` is
   measured by bracketing: {{v1.phi.it}} for the community of share {{v1.it.share}} against
   {{v1.phi.en}} for the community of share {{v1.en.share}}. A register at prevalence 0.20 is therefore
   missed at rate 1.000 in the minority community and caught at rate 0.000 in the majority.
4. **The residue gate has a boundary at the register's size, and a rate is owed over its eligible
   subset** (§6). Across {{v2.cells}} cells the level effect is flat for every `r` up to {{v2.r.reg}}
   ({{v2.r.lo.induced}} induced) and {{v2.r.over.induced}} at `r = 40`, where the corpus residue never
   reaches the cutoff (maximum {{v2.r.over.corpusmax}} units against the community's
   {{v2.r.over.poolmax}}). The eligible-subset rate is {{v2.elig.20}}, against the diluted
   {{v2.comm.dil}} a community sample reports — the whole difference between the two numbers.
5. **The null is also a level** (§7). A filter chain applied to the scan but not the null is a
   **sensitivity curve**, not a point ({{v3.infl.10}}x → {{v3.infl.25}}x → {{v3.infl.50}}x →
   {{v3.infl.100}}x as the de-genericity rule tightens); a bootstrap interval belongs to the population
   it resampled, so the non-identical subset owns [{{v3.int.nonid.lo}}, {{v3.int.nonid.hi}}] rather
   than the whole-ensemble [1.0, 1.0]; and reproducing two length marginals independently moves a
   calibrated null by {{v3.ctl.marg}} against a control's {{v3.ctl.anchor}}.

### 1.2 What this is not

This is not a claim that a corpus-wide frame is a bug. A guard calibrated and operated at one level is
**correct at that level** — its own evaluation measures that level. It is not a claim that character
bigrams and word shingles can be treated alike; §5 shows the opposite, and the mechanism predicts which
is which. And it is not a claim that any deployed system's numbers are wrong: the reader correction that
anchored this direction was about how a number is *reported*, and §7's contribution is to say what a
rate and an interval are a rate and an interval **of**.

## 2. Related work

**Similarity and near-duplicate detection.** The measurement apparatus this paper analyses is the
sketching and fingerprinting literature: resemblance and containment as set statistics
{ref:10.1109/sequen.1997.666900}, the MinHash estimator that a Jaccard threshold is placed on
{ref:10.1145/509907.509965}, and the deployed fingerprints — Winnowing {ref:10.1145/872757.872770},
syntactic clustering of the web {ref:10.1016/s0169-7552(97)00031-7}, the web-crawl near-duplicate rule
{ref:10.1145/1242572.1242592} and the identify-and-filter pipeline {ref:10.1007/3-540-45123-4_1}. The
near-duplicate detection literature continues the same template at other scales and modalities
{ref:1104.4723} {ref:1406.1143} {ref:1702.01032} {ref:1704.05617} {ref:1810.03099} {ref:1810.03102}
{ref:1912.05171} {ref:2005.07356} {ref:2102.10315}. The difference is the object: those works evaluate
a statistic or a threshold on one population, and this paper's estimand is what changes when the
**population the background is computed over** is declared to be a different one.

**Plagiarism and text reuse.** Text-reuse detection is the same rule with a documentary reading
{ref:1001.3487} {ref:1003.4065} {ref:1206.6606} {ref:1208.2486} {ref:1210.3729} {ref:1210.7678}
{ref:1403.1310} {ref:1403.2871} {ref:1412.7782} {ref:1705.08828} {ref:1712.02820} {ref:1712.10309}
{ref:1906.11761} {ref:1909.07950} {ref:1912.12068} {ref:2002.04279} {ref:2004.05265} {ref:2006.09719}
{ref:2010.01263} {ref:2105.12068}; the field's evaluation form is fixed by shared-task protocols and
surveys {ref:10.1109/ams.2011.19} {ref:10.37200/ijpr/v24i1/pr200254}; and cross-language detection
extends the comparison across a translation axis {ref:0912.3959} {ref:1702.03082} {ref:1704.01346}
{ref:2201.03423} {ref:2605.09421} {ref:10.1007/978-3-642-36973-5_66}, while cross-lingual similarity
work varies the language of the comparison rather than the population behind the frame {ref:1401.2258}
{ref:1512.07046} {ref:1606.09403} {ref:1611.04122} {ref:1707.09443} {ref:1712.01813} {ref:1805.00879}
{ref:1807.11057} {ref:1812.09617} {ref:1812.10464} {ref:1903.03243} {ref:1910.11005} {ref:1911.12637}
{ref:2004.05991}. Recent reuse work pushes the same detection into news archives and historical corpora
{ref:1905.02973} {ref:2512.23504} {ref:2603.29937} {ref:2605.09236}. Every one of them subtracts a
background; none of them treats the level of that background as a variable.

**Frames with a fixed population.** The frame's manual ancestors are the stop-list and the term weight.
Stop-word removal is the hand-built frame {ref:1411.5732} {ref:1701.03227} {ref:2006.02633}
{ref:2204.03062} {ref:2204.03064} {ref:2304.12155} {ref:2406.11029} {ref:10.18653/v1/w18-2502}; IDF is
its automatic, corpus-frequency version {ref:10.1108/00220410410560573} {ref:1204.0182} {ref:2002.11844}
{ref:2003.07193} {ref:2211.12364} {ref:2507.15742}; and boilerplate and template removal is the same
object for web pages {ref:1801.02607} {ref:1911.02991} {ref:2001.04338} {ref:2004.14294} {ref:2208.02252}
{ref:2310.06786} {ref:2504.08776} {ref:10.1145/1141277.1141534}. The difference is not the frame but the
question asked of it: an IDF weight and a stop-list are evaluated by the retrieval quality they buy at
one population, whereas this paper measures what the population itself changes, and shows the change is
a *share* effect (`s* = theta / df_pool`) rather than a tuning effect.

**Whose text it is.** The population is also the unit of a second literature: language identification
reads a writer's population from an n-gram profile {ref:1707.07182} {ref:1707.08349} {ref:1804.07954}
{ref:1901.04216} {ref:2005.08229} {ref:2007.05727} {ref:2009.05456} {ref:10.32614/cran.package.textcat},
and the natural-frequency literature shows a text's statistics depend on the population it is drawn from
{ref:0909.4385} {ref:1212.2616} {ref:1912.03570} {ref:2304.12191}. This paper's dilution law is that
same dependence, measured for the units a frame is built from. Code clones are the same two-stage rule
on a different artefact {ref:1512.06448} {ref:1911.00561} {ref:2002.05204} {ref:2006.14505}
{ref:2105.11933} {ref:2110.01092} {ref:2110.10493} {ref:2111.14183} {ref:2204.01028} {ref:2204.07501}
{ref:2205.04913} {ref:2206.04730} {ref:10.1145/2884781.2884877} {ref:10.1016/j.scico.2009.02.007},
where the frame's level is undeclared in exactly the same way.

**Rates over populations.** The arithmetic this paper uses for a rate over a population is the
aggregation literature's: a pooled rate is a share-weighted mixture, so pooling populations with
different base rates produces a number that is neither population's {ref:1710.08615} {ref:1712.08946}
{ref:1801.04385} {ref:1805.03094} {ref:2106.00734} {ref:2201.06517} {ref:2210.07755} {ref:2307.14448}
{ref:2311.06840}, and the same decomposition is standard in subpopulation-level evaluation and fairness
reporting {ref:1909.02827} {ref:2104.12231} {ref:2205.15494} {ref:2209.06378} {ref:2209.14613}
{ref:2302.07185} {ref:2303.17566} {ref:2304.02780} {ref:2305.03712} {ref:2305.12622} {ref:2306.11181}
{ref:2309.14198}, and in thresholds tuned inside a software-engineering evaluation {ref:1810.11903}
{ref:2504.17066} {ref:2512.16816} {ref:2604.22640} {ref:2609.11023}. The difference is which object is
decomposed: those works decompose the *score* by population, while this paper decomposes the *pipeline*
— the same population that reports a rate is the population the background frame must be computed over,
and moving one without the other is what makes a rate a composition artifact. The interval and
multiple-comparison machinery used here is taken as a tool rather than extended
{ref:10.1111/j.2517-6161.1995.tb02031.x}.

**The nearest published claims, and their differences.** Three works are close enough to state
individually. (i) The near-duplicate web-crawl detector of {ref:10.1145/1242572.1242592} reports a
corpus-wide rule's behaviour on one crawl; its background population is the crawl, so the axis this
paper varies (the level) is fixed there, and the level effect measured here is exactly what that
evaluation averages out. (ii) The template-detection work of {ref:10.1145/1141277.1141534} identifies
templates by corpus-wide frequency — the frame whose level this paper varies — and its own subject is
which templates to remove, not what a small-share community's register looks like to that rule. (iii)
The stop-list work of {ref:10.18653/v1/w18-2502} shows that hand-built lists are inconsistent across
packages; this paper's result explains *why* a hand-built list can be right for one community and wrong
for another — a list is a frame with a population fixed by hand, so its correctness is a statement about
that population.

**Reverse gap, and why this was not done before.** Three reasons are plausible and none of them is that
the answer was known. (i) The frame sits **inside** a detector as preprocessing, and the ecology around
it optimizes the *score* and the *threshold* — score normalization, benchmark standardization — rather
than the population the score is normalized against. (ii) Defaulting the frame to the whole corpus is
the path of least resistance: it needs no per-population calibration and no declaration, so no published
protocol had a reason to record the choice. (iii) The result is "just" a share effect, and the party
with the incentive to publish it is the deployer rather than the method's author. The search form behind
this claim: arXiv `search_query` over `cs.CL`, `cs.IR` and `cs.SE` for `background frame`, `generic
frame`, `document frequency`, `near-duplicate`, `plagiarism detection`, `text reuse`, `boilerplate
removal`, `stopword removal`, `cross-lingual similarity`, `language identification` and `code clone
detection` together with `threshold`, `evaluation` or `fairness` (window: submission date to
2026-10-09; scan date 2026-10-09), and Crossref `query.bibliographic` for the canonical works by title.
That search returns the literature cited above — and, in it, no study whose estimand is the level of a
background frame.

{{fig1}}

## 3. The object: a two-stage guard and the level of its frame

Fix a corpus of documents and two unit sets, one for each statistic: character bigrams (`char2`) and
word-3 shingles (`word3`). A **guard** is the rule

    fire(a, b)  iff  dice(a, b) >= tau   AND   |shared(a, b) minus F_l| >= r,

where `shared(a,b)` is the set of units the two documents have in common, `F_l` is a **background
frame** computed at level `l`, and `r` is the residue threshold (`r = {{sim.r}}` throughout, with
`tau = {{sim.tau}}` and `theta = {{sim.theta}}` where a threshold is named). The frame is the set of
units deemed generic:

    F_l = { u in U : df_l(u) >= theta },   df_l(u) = (# documents in population l containing u) / |population l|.

Two properties of this construction matter, and neither is usually written down. First, the frame acts
on the **residue gate only**: the similarity gate is computed on the raw unit sets and is therefore
level-independent, so two levels differ only in which shared units are removed. (The first version of
the instrument attributed the fires to the similarity gate; a per-gate decomposition is required before
any attribution — a defect this paper's apparatus now enforces against.) Second, the frame is a
threshold on a **share**, not on a count: a unit occurring in 90 % of one community's documents has a
corpus document-frequency of `0.9 * s`, and if that product is below `theta` the unit is not in the
corpus frame at all.

**The dilution law.** Let `P` be a population of share `s = |P| / N` of the corpus, and let a unit `u`
be **confined** to `P`: every corpus document containing `u` lies in `P`. Then the document counts
coincide, `c_corpus(u) = c_P(u)`, and since the denominators differ by exactly `N / |P|`,

    df_corpus(u) = s * df_pool(u)        (exactly).

This is an identity, not a fit, and it is the opposite of the containment the direction registered: a
pool-generic unit's corpus frequency is *smaller*, so the corpus frame is *smaller* than the pool frame,
and the residue is non-decreasing as the level widens — because the finer frame is strictly larger, not
because of any inclusion. Confinement is the premise that does the work, and it is testable: it is why a
word-3 shingle restricted to one community's writing dilutes, and why a character bigram that recurs in
every language does not.

**What counts as ground truth.** The ladder is measured with ground truth **by construction**, so no
human annotation enters the core cells. Three plants are built from the pinned corpus: a **template**
(the body of one document scaled to a fixed unit count) which must fire at *every* level; a **register**
(a recurring block carried by a fraction `phi` of a community's documents) which must clear the residue
gate under exactly the level whose population makes it generic; and a **repost** pair — verbatim, and at
a declared {{v3.editrate}} substitution rate — which must fire under any level, including the whole-corpus
null of §7. Each instrument refuses to measure a corpus whose `SHA256SUMS` does not verify on that read.

## 4. The registered identity is refuted, and the dilution law is exact

The direction registered a set-containment identity as its first theoretical claim, with the residue
monotonicity as its consequence. The de-risk spike (`spike_v0.py`) measured it before anything was built
on it, on {{v0.docs}} documents from eight SHA256-pinned books, with the frame recomputed at two levels
(whole corpus, one book as the pool) for every book and both statistics.

The identity fails, and it fails in both directions at once: **{{v0.viol.both}} of {{v0.cells}}** cells
break `F_corpus subset F_pool` and the same {{v0.viol.both}} break `F_pool subset F_corpus`. The
violations are not marginal: a corpus-generic unit absent from the pool occurs {{v0.viol.lo}} to
{{v0.viol.hi}} times per cell, and a pool-generic unit absent from the corpus frame {{v0.viol.p.lo}} to
{{v0.viol.p.hi}} times. Containment was the wrong object.

The dilution law is the right one, and it is exact. Restricting to units **confined** to the pool —
every corpus document containing the unit lies in the pool, which the instrument filters for — the
residual `|df_corpus(u) - s * df_pool(u)|` has worst case **{{v0.dil.char.worst}}** over
{{v0.dil.char.pairs}} character-bigram pairs and **{{v0.dil.w3.worst}}** over {{v0.dil.w3.pairs}}
word-3-shingle pairs. That is floating-point noise on a real-text corpus of {{v0.docs}} documents, i.e.
the relation holds exactly. The worst word-3 case is instructive: the unit is
`{{v0.unit}}`, generic inside one book and invisible to the corpus frame.

The mechanism is a **share law**, and it is measured by pooling the first *k* books as the pool and
sweeping *k*. Of the units generic inside the pool at `theta = 0.01`, the fraction the corpus frame
misses is {{v0.sweep.1}} % at share {{v0.share.1}} ({{v0.hidden.1}} of {{v0.Fpool.1}} pool-frame units
invisible), {{v0.sweep.2}} %, {{v0.sweep.4}} %, and **{{v0.sweep.8}} %** at share 1.0 — the control,
where the pool *is* the corpus and the two frames are therefore identical. The same sweep on character
bigrams gives {{v0.char.sweep.1}} % / {{v0.char.sweep.2}} % / {{v0.char.sweep.4}} % /
{{v0.char.sweep.8}} %, and only {{v0.dil.char.hidden}} bigram units are pool-generic-but-corpus-invisible
against {{v0.dil.w3.hidden}} word-3 units: the effect is **statistic-dependent**, and §5 shows the same
split deciding which community has a stratum at all.

**Two-sided certificates.** The spike's plant battery includes a pool that is the whole corpus (share
1.0, where both containments must hold and the instrument confirms both), a small-share pool where
`F_pool subset F_corpus` must fail with at least one hidden unit, and a confinement plant that requires
non-confined units to be excluded from the identity. All three fire, and the corpus is re-verified
against its own `SHA256SUMS` on every read — an unverified corpus aborts the run rather than being
measured. The registered claim is refuted; the replacement is certified rather than asserted.

## 5. The ladder: the level moves the flag, and the statistic decides the stratum

The ladder is measured on a **five-language** corpus: eight English books and twelve non-English texts
(Italian, Spanish, French, German), each SHA256-pinned in its own directory. Documents are capped at a
fixed character length, giving **{{v1.docs}}** documents. Two communities are the strata: Italian
({{v1.it.pool}} documents, share {{v1.it.share}} of the corpus) and English ({{v1.en.pool}} documents,
share {{v1.en.share}}). The community need not be a language in general — a register community is the
object — but a language is a real, non-constructed population with a real share, which is exactly what
the mechanism needs.

The instrument is `spike_v1.py`: the frame acts on the residue gate only, and the construct is a
**register** — a recurring block a community shares, such as a greeting, a licence header or a template
clause — carried by a fraction `phi` of the community's documents. Its prevalence in the corpus is
`s * phi`, so the critical prevalence at which a corpus-wide frame becomes able to remove it is
`phi* = theta / s`.

**P1 — the level is first-order: confirmed.** At `word3`, `tau = {{sim.tau}}`, `theta = {{sim.theta}}`,
the corpus-level frame fires on **{{v1.lad.05.corpus}} of {{v1.lad.05.pass}}** community pairs at
`phi = 0.05` while the community-level frame fires on **{{v1.lad.lo.pool}}**; above the critical
prevalence the corpus level reads **{{v1.lad.hi.corpus}}**, and at `phi = 1.0` (the register in every
document, hence in both frames) also **{{v1.lad.full.corpus}}**. The registered falsifier was a level
effect below 2x; the ratio here is a division by zero, and the zero is **derived**, not small: all
{{v1.lad.lo.reg}} register units of that cell lie in the community frame, so the residue is
`0 < r = {{sim.r}}` and the guard cannot fire. The bracket at both ends (`phi = 0`, where no document
carries the register, and `phi = 1.0`) is the two-sided control the registration asked for. Across the
whole grid of {{v1.cells}} cells the corpus frame fires on `{{v1.lad.lo.corpus}}` pairs at corpus
prevalence {{v1.lad.lo.cprev}} — a level-induced count of {{v1.lad.lo.induced}} — and on
`{{v1.lad.hi.corpus}}` at the higher prevalence, so the effect
exists on one side of the critical prevalence and vanishes on the other.

**P2 — the error is systematic, and `phi*` is wider for the smaller community: confirmed.** The critical
prevalence is *measured* by bracketing rather than assumed: the Italian community flips between a
prevalence at which the register is hidden and one at which it is visible, bracketing the predicted
**{{v1.phi.it}}**; the English community brackets **{{v1.phi.en}}**. Since `phi* = theta / s` and the
Italian share is smaller, its band of blindness `(0, phi*)` is **wider**: a register at prevalence 0.20
has corpus prevalence {{v1.lad.lo.cprev}} in the minority community (hidden) and
{{v1.lad.en.cprev}} in the majority (visible, {{v1.lad.en.corpus}} corpus-level fires), so the same
register is **missed entirely in the
minority and caught entirely in the majority**. That is a misclassification that is a function of *who
is writing*, which is what makes a mis-set frame a fairness defect rather than a tuning knob.

**The statistic, not the community, decides whether a stratum exists.** The certificate
`s * phi < theta  <=>  register hidden from the corpus frame` holds in **{{v1.cs.w3.agree}} of
{{v1.cs.w3.total}}** word-3 cells, and it *fails* on character bigrams, where
**{{v1.cs.c2.hidden}} of {{v1.cs.c2.total}}** predicted-hidden cells are actually hidden. The failure is
the confinement premise, not a defect: character bigrams are not confined to a community — they recur
across languages — so their corpus frequency does not dilute, and they stay inside the corpus frame at
any share. An analyst who picks the statistic picks whether their community is visible at all.

**Template controls.** A verbatim repost and a 1 %-edited repost must fire under *every* level,
including the corpus frame; both fire in all {{v1.tmpl.cells}} threshold cells (edited Dice
{{v1.tmpl.dice}}), which is what separates a *register* effect from a *similarity* effect: the level
cannot remove a genuine copy.

{{fig2}}

{{fig3}}

## 6. The residue gate's boundary, and the rate over its eligible subset

`spike_v2.py` extends the ladder to a grid of **{{v2.cells}}** cells: two strata × two statistics × six
register prevalences × three frame thresholds × three similarity thresholds × five residue thresholds ×
two sampling rules.

**The `r` axis is a boundary, and the zero above it is derived.** The level-induced count is flat for
every `r` from 5 to **{{v2.r.reg}}** (the register's own unit count; {{v2.r.lo.induced}} induced fires
at `r = 5`, {{v2.r.last.induced}} at `r = {{v2.r.reg}}`) and drops to **{{v2.r.over.induced}}** at
`r = 40`. The instrument explains the zero rather than reporting it: at that prevalence the corpus
residue over the eligible pairs never exceeds **{{v2.r.over.corpusmax}}** units while the community
residue never exceeds **{{v2.r.over.poolmax}}**, so at `r = 40` the corpus level *cannot* fire on any
pair even though {{v2.r.over.pass}} of them pass the similarity gate. The guard's second gate therefore needs `r <= register_units` for a community register to be able
to decide it at all — a boundary condition on the design, not a small measurement. The grid's own
certificate charges over the cells where `r` exceeds the register ({{v2.r.exceeds}} cells) and requires
the induced count to be zero there.

**A rate is owed over its eligible subset.** A pair whose similarity gate does not open is
**ineligible**, not unflagged, and counting it deflates the rate by exactly the pass fraction. With the
**affected** sampling rule — both members carry the register, which is the subpopulation the level acts
on — the eligible rate is a clean step: at `phi = 0.05` it is {{v2.elig.05.fire}} of
{{v2.elig.05.pass}}, at the critical prevalence it is **{{v2.elig.20}}** ({{v2.elig.20.fire}} of
{{v2.elig.20.pass}}), and above it **{{v2.elig.30}}** ({{v2.elig.30.fire}} of {{v2.elig.30.pass}}), down
to {{v2.elig.100.fire}} of {{v2.elig.100.pass}} with the register everywhere. With the **community**
sampling rule — random pairs of the community, which is what a deployed guard actually sees — the same
effect is diluted: {{v2.comm.fire}} of {{v2.comm.pass}} eligible pairs, a dilution factor of
**{{v2.comm.dil}}** against the {{v2.comm.n}} pairs a naive count would divide by. The two numbers
differ by the dilution and by nothing else, which is why the eligible rate and the dilution are reported
together, and an empty denominator is written `undef` rather than plotted as 0.000.

{{fig4}}

{{fig5}}

## 7. The null is also a level

The frame is a population; so is the null. `spike_v3.py` plants ground truth by construction into the
pinned corpus: a document set of **{{v3.docs}}** with {{v3.verbatim}} verbatim reposts (hash-equal after
normalisation, decidable by a hash) and {{v3.edited}} edited reposts at a declared {{v3.editrate}}
character substitution rate (not hash-equal: the class the statistics must carry). Three law families,
each with its own certificate.

**L1 — the filter chain is a sensitivity curve, not a point.** An expectation computed as `N_eligible *
P_null` is a product of two measured rates, and the identity `E_matched / E_naive = (N_eligible /
N_raw) * P_null` is asserted exactly (measured {{v3.ident}} on this corpus: the two routes coincide to four
decimals). When a de-genericity filter is applied to the scan but not to its
null, the expectation is inflated, and the inflation depends on where the rule is set:
{{v3.infl.10}}x at ten de-generic units, {{v3.infl.25}}x at twenty-five, {{v3.infl.50}}x at fifty and
{{v3.infl.100}}x at a hundred. On long documents the loosest rule is a near no-op — the null survivor
rate is {{v3.pnull}} — so the honest reading is that the *mechanism* is real and its *magnitude* is a
function of where the rule is set and of the document-length profile. The matched expectation
({{v3.Em}}) and the naive one ({{v3.E}}) differ by the identity above, and the observed count over that
expectation is {{v3.obs.E}}.

**L2 — an interval belongs to the population it resampled.** A bootstrap over the whole fire population
({{v3.fires}} fires, of which {{v3.verb.fires}} are verbatim and identical by the hash) gives the
degenerate **[1.0, 1.0]**; the {{v3.nonid}} non-identical fires give **[{{v3.int.nonid.lo}},
{{v3.int.nonid.hi}}]**, median {{v3.int.nonid.med}}. `interval_transfers = False`: the wider interval
cannot be read off the whole-ensemble resample, because the subset was carved out *after* the resample.
A count that small also owns a count-based bound and not a distributional one — Poisson 95 % upper
{{v3.pois.1}} (one-sided) and {{v3.pois.2}} (two-sided) for the small count — and the convention is part
of the number.

**L3 — the null's population is the pairing, not only the marginals.** Each cell is the fraction of
reference scores strictly below their own null's median, so a calibrated null reads 0.5. On the
**control** (cross-language, matched-length, unrelated pairs; {{v3.ctl.n}} pairs), the anchored null
reads **{{v3.ctl.anchor}}** and the exchangeable null **{{v3.ctl.exch}}** — both calibrated — while the
**marginal** construction, which replaces each member independently and matches each to its own length,
reads **{{v3.ctl.marg}}**. Reproducing the two length *marginals* is therefore not reproducing the
pair's *joint*: the variable the marginal null frees is the **pairing** itself. On the
**near-duplicate** set ({{v3.nd.n}} pairs) every constrained null reads **{{v3.nd.anchor}}** (maximum
discriminability) while the exchangeable null reads **{{v3.nd.exch}}** — a null drawn from a pool that
*contains* the near-duplicates inflates the reference's apparent surprise, which is the same
population-decides-the-null mechanism one layer down. The `--selftest` plants a deliberately biased null
that must *not* read 0.5, so the calibration check fires on its own fault rather than passing by
construction.

## 8. Registered priors and their outcomes

The direction registered three priors before the deciding runs, each with a mechanism, and each was
written down with the falsifier that could kill it. All three were **confirmed**, and in each case the
confirmation is carried by a certificate rather than by an aggregate. The confirmations are reported
here in the registered direction, and one of them (P1) changed its *justification* mid-study: the
mechanism the registration named was wrong and was replaced in place, with the prior itself unchanged.

- **P1 — the level is first-order: CONFIRMED.** The registration predicted that at fixed `(tau, r)`,
  moving the frame from the corpus level to the community level changes the flag count by a factor of at
  least 2. Measured: {{v1.lad.05.corpus}} of {{v1.lad.05.pass}} community pairs are fired on by the
  corpus-level frame and none by the community-level frame, a ratio that is a division by a derived
  zero. **The justification changed and the prior did not.** The registration derived the prediction
  from set containment `F_corpus subset F_script`; the de-risk spike refuted that in {{v0.viol.both}} of
  {{v0.cells}} cells in both directions (§4), and the replacement is the dilution `df_corpus(u) = s *
  df_pool(u)`, which predicts the same monotone direction by the opposite mechanism: the finer frame is
  strictly larger because a confined unit's corpus frequency is smaller, not because it is included.
  This is the round's most useful negative result, and it was found before the ladder was built.
- **P2 — the error is systematic and concentrated in the minority: CONFIRMED, quantitatively.** The
  registration predicted that a corpus-wide frame misclassifies a small-language community's register as
  shared content, and that the misclassified set is over-represented in the minority stratum relative to
  its share of eligible pairs. Measured: the critical prevalence is bracketed at **{{v1.phi.it}}** for
  the community of share {{v1.it.share}} and **{{v1.phi.en}}** for the community of share
  {{v1.en.share}}, exactly as `phi* = theta / s` requires, so the band of blindness is **wider for the
  smaller share** and a register at prevalence 0.20 is missed in the minority at rate 1.000 and caught
  in the majority at rate 0.000. The registered mechanism — a document-frequency cutoff is a *share* — is
  the one that survives measurement; the registered *justification* for it (set inclusion) is the one
  that did not.
- **P3 — an enrichment needs a matched population: CONFIRMED, and sharpened.** The registration
  predicted that an enrichment whose two sides are drawn from different classes overstates the detector,
  and that a class-matched reading is **smaller**. Measured on the null layer (§7): a filter applied to
  the scan but not the null inflates the expectation from {{v3.infl.10}}x to {{v3.infl.100}}x depending
  on where the rule is set; an interval resampled over one population does not transfer to a subset
  carved out of it ([{{v3.int.nonid.lo}}, {{v3.int.nonid.hi}}] against [1.0, 1.0]); and the arithmetic
  of the "smaller" claim is the aggregation identity `rate = sum_c share_c * rate_c` that the
  aggregation literature states {ref:1710.08615} {ref:1801.04385} {ref:2106.00734}. The sharpening is
  that "matched" is not one condition: matching the two length *marginals* independently still moves the
  calibrated control by {{v3.ctl.marg}} against {{v3.ctl.anchor}}, because the freed variable is the
  pairing.

**Registered success criteria, and their outcome.** (i) Two-route agreement between the ladder's flags
and the independently computed dilution identity — **MET**: the identity is exact
({{v0.dil.w3.worst}} worst residual over {{v0.dil.w3.pairs}} confined pairs) and the ladder's derived
zeros agree with it in every reported cell. (ii) Each located level effect bracketed to a stated
resolution with a two-sided control at the adjacent level — **MET**: `phi = 0` and `phi = 1.0` both read
{{v1.lad.full.corpus}}, and the templates fire under every level. (iii) The systematic claim reported as
a stratified concentration ratio with an interval rather than as a pooled rate — **MET as a bracketed
critical prevalence** per community ({{v1.phi.it}} / {{v1.phi.en}}); the concentrations are reported per
stratum and never pooled, and §7 states the interval ownership rule the registration's own wording
implied but did not fix. (iv) Every rate over its eligible subset with the dilution stated, and every
enrichment with its matched value first — **MET** (§6, §7). One criterion was recorded **unmet in its
first form**: the registration asked for the level effect on the `r` axis as a measured flatness, and
the correct statement turned out to be a *boundary* (`r <= register_units`) with a derived zero above it
— reported as such rather than as a flat line.

## 9. Threats to validity

**The corpus is public-domain prose, capped at a fixed length.** Eight English books and twelve
non-English ones, pinned by sha256 and verified on every read. Two consequences are stated rather than
absorbed. First, the register is a *constructed* block carried by a fraction `phi` of a community's
documents, not an observed platform register: the ground truth is by construction, which is what makes
the cells exact, and the price is that the register's realism is argued rather than measured. Second,
the document cap makes the unit counts uniform, which is what a share law needs; a corpus with a
different length profile is the first place to re-run §7's L1 magnitude.

**The community is a language here, and need not be.** The mechanism is about **share**, not about
language; the Italian/English split is used because it is a real population with a real, non-constructed
share. A register community — a platform's sub-forum, a licence-header family — is the general case, and
is not measured here.

**Confinement is the premise, and it is checkable.** The dilution law holds for confined units; the
character-bigram divergence in §5 is what a statistic that violates confinement looks like, and it is
reported as a finding rather than hidden as a nuisance. Any deployment that wants to apply the law must
check confinement on its own unit set, and the check is cheap.

**The perturbation is substitution at a declared rate.** The edited reposts are the register-preserving
edit, so the results are about rewording, not paraphrase. A semantic rewrite could move the residue in
either direction, and the honest reading of §7 is that it is a law about the edit operator that was run,
stated with the operator.

**Two-sided checks that could have failed.** The dilution law is certified over every confined pair
rather than fitted; the `r`-boundary is a derived condition rather than a threshold on the value it
produces; the certificate `s * phi < theta <=> hidden` is stated as *word-3* because it fails on
character bigrams and the failure is reported; and the L3 calibration check plants a biased null that
must not read 0.5. Each was written to be able to fail.

## 10. Reproduction

The package is `papers/issue-132/`. One command re-runs everything:

    cd papers/issue-132 && bash reproduce.sh

It re-runs the four instruments **from their own code** over the committed, SHA256-pinned corpus,
compares each report byte-for-byte against the shipped one, runs each instrument's own plant battery
(6/6, 7/7, 7/7, 8/8), runs the reference layer's offline gate, re-generates the five figures and their
captions and compares them the same way, then re-renders this manuscript from `manuscript.src.md` and
requires the result to equal the committed `manuscript.md`. Tolerance is `exact` (sha256 equality) and
needs no version pin: every script imports the standard library only, every counted quantity is an
integer and every reported average is a single division, so no float reduction depends on the build.
The package was measured byte-identical under CPython 3.9.6 and 3.13.9, and from a `git archive` export
of the branch head. `REPRO_FULL=1` adds a two-run determinism certificate over all four instruments. The
build that renders this manuscript reads every number from the shipped reports and **refuses to render a
citation whose key is absent from the verified pool**; the pool's seed is {{sim.seed}}, the shingle
side is `k = {{sim.k}}`, {{sim.pairs}} pairs per cell and {{sim.mindegen}} units is the de-genericity
floor of §7. `reference-check.md` reports the citation authenticity of every entry, and `refs/pool.json`
is the verified pool this manuscript is built from.

## 11. Conclusion

A threshold is not a specification. A similarity guard's operating point is a function of the
**population its background frame is computed over**, and that population is a level the field leaves
implicit. This paper shows what the level does: it changes the flag count by an unbounded factor below a
critical prevalence that is **wider for smaller communities**, so the error a corpus-wide frame leaves is
systematic in who is writing rather than random over pairs. The relation that carries the effect is a
dilution, `df_corpus(u) = s * df_pool(u)`, exact and measurable; the variable that decides whether a
community has a stratum at all is the **statistic** (word-3 shingles dilute, universal bigrams do not);
the second gate has a boundary at the register's own size; a rate is owed over the subset where the test
is defined; and a null is a population like any other, with its own filter chain, its own interval and
its own pairing. The changed decision is small to write down and large to omit: *declare the frame level,
re-calibrate it per population, and report the eligible subset and the matched enrichment beside every
rate.*
