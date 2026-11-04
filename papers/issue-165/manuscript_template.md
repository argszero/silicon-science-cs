# Breadth Is Not Depth: The Per-Request Yield of Citation Expansion, and the Price at Which Allocation Would Change

*Draft for SILICON SCIENCE · Computer Science — issue 165. Every quantity in this file is a marker
resolved from `results.json` by `make_manuscript.py`; a hand-typed number is refused at build time.
The bibliography is generated from `refs/records.json`, and every entry is a registry return that
passed verification; `reference-check.md` reports each one against the record it was checked against.*

## Abstract

A literature search chases citations, and every chase costs a request against a bibliographic
database. The practical question — spend the next request **wide**, one hop from another seed, or
**deep**, another hop from the same one — is usually answered by folklore: iterate until no new work
appears. We price both directions instead. Coupling is a deterministic predicate (two works sharing at
least one reference), and the quantity judged is its **excess over a length-matched, field-matched
null**, because coupling rises mechanically with reference-list length and an unmatched base rate
measures reference density rather than relevance. Across {{n:arms.cs.n_seeds}} seeds in Computer
Science and {{n:arms.social_sciences.n_seeds}} in Social Sciences, the per-request yield falls with hop
depth: the excess is {{f:arms.cs.pooled.hop1.excess|signed_pct1}} points at hop 1 and
{{f:arms.cs.pooled.hop2.excess|signed_pct1}} at hop 2 in the first field
({{f:arms.social_sciences.pooled.hop1.excess|signed_pct1}} and
{{f:arms.social_sciences.pooled.hop2.excess|signed_pct1}} in the second), against a null whose chance
coupling is about {{f:arms.cs.pooled.hop1.null_share|pct1}} percent. The decay is structural, not an
artefact of how long the reference lists are. The allocation then has a price: depth wins only if one
depth batch costs less than **{{f:arms.cs.w_star.point|f3}}** of a breadth page in Computer Science and
**{{f:arms.social_sciences.w_star.point|f3}}** in Social Sciences, with intervals
{{f:arms.cs.w_star.ci95|ci3}} and {{f:arms.social_sciences.w_star.ci95|ci3}}. Both lie entirely below
the floor of one request per batch, so **at this API's documented request cost breadth-first is the
only allocation the price allows**, in both fields measured.

## 1. What is being estimated, and what is not

The estimand is **bibliographic-neighbourhood overlap per request**. It is not relevance, usefulness or
reading value, and this paper never claims otherwise. A hop-1 work is a *citer* of the seed and is
therefore in its topic by construction; a shared-reference predicate at roughly one percent chance
coupling is a weak proxy for anything a reader would call interesting. What the number supports is a
decision about **which request to send next**, not a judgement about what is worth reading.

With `refs(w)` the recorded reference list of a work and `s` a seed:

    coupled(w, s) := |refs(w) ∩ refs(s)| > 0

A work with no recorded reference list has **no value** for this predicate. Those works are excluded
from every share and counted, never folded in as uncoupled.

## 2. Background and related work

### 2.1 How a literature is walked

Citation expansion is one of two ways into a literature, and the older one is the query. Systematic
reviews formalise both — a database search, then backward and forward snowballing iterated to
saturation {{c:petersen2015,wohlin2014}} — with the two routes compared in practice and the
recall-versus-effort trade-off stated rather than assumed {{c:badampudi2015}}. Screening what comes back
is the cost that motivates automation {{c:marshall2019}}, and evaluating what a search returned has a
methodology of its own {{c:manning2008,robertson2009,salton1988}}, including the uncomfortable part: a
test collection carries the biases of how it was built {{c:sanderson2010,buckley2004,voorhees2001}}.
Where to look next has been modelled before — information foraging treats a literature as a set of
patches and predicts movement by information scent {{c:pirolli1999,fu2007}} — and a search is ended by a
stopping rule rather than at the frontier {{c:kraft1979,simon1955}}. That a retrieval has a price is old
in economics {{c:stigler1961}}, and that disjoint literatures can each hold knowledge neither can see is
the strongest reason to walk at all {{c:swanson1986}}. What this literature does not supply is a **yield
per request** for the walk: it supplies stopping rules and recall targets, which are different objects.

### 2.2 What a citation link is evidence of

Two works sharing a reference are bibliographically coupled {{c:kessler1963}}; two works cited together
are co-cited {{c:small1973}}; both are similarity constructs, and both were used to map a field before
anyone called the result retrieval {{c:garfield1979,price1965}}. The literature is equally clear that a
citation is not a vote for quality: the motivations for citing vary {{c:moravcsik1975,gilbert1977}},
cumulative advantage is real {{c:merton1968}}, and the validity of evaluative citation analysis is
contested rather than settled {{c:peritz1983,lawani1982,bornmann2008,tahamtan2019}}. Scientometrics
has been reviewed as a field holding its own theory and practice {{c:mingers2015}}, which is why the
claim made here is stated as an estimand rather than as a verdict on quality. Underneath, the distributions
are heavy tailed {{c:redner1998,barabasi1999,radicchi2008}}, citation of a work ages with a distributional rather
than a fixed form {{c:burrell2002}}, and the networks those citations form are worth measuring on their
own terms {{c:newman2001,newman2003}}. This paper therefore uses a citation only as a **link**, never as
a score, and compares ranked things only where a measure for the comparison exists
{{c:fagin2003,jarvelin2002,webber2010}}.

### 2.3 Matching, and why an unmatched control lies

Reference lists are not stationary: they have grown and narrowed {{c:evans2008}}, and what a
bibliographic database can see lags what is being published {{c:larsen2010}}, so a control drawn without
matching measures the archive at two different moments at once. Adjusting for a covariate removes that
covariate's effect and nothing else {{c:cochran1968,rosenbaum1983,stuart2011}}, the adjustment needs the
confounder to have been measured at all {{c:rubin1974}}, and selection into the sample has to be
modelled rather than assumed away {{c:heckman1979}}; the general form of that problem — a sample whose
distribution differs from the target's — has a name {{c:shimodaira2000}}. The bibliometric version of the
same lesson is that productivity and impact are skewed {{c:lotka1926,egghe2006}} and that authorship and
collaboration structures drift {{c:wuchty2007,jones2009}}. A summary built on an unmatched base rate
reports the base rate.

### 2.4 Chance agreement, and saying an absence out loud

An observed share contains the agreement chance alone would produce, and removing it is standard
{{c:cohen1960}}; a quantity is worth reporting only when it is defined as one {{c:shannon1948}}. An
interval for a share of a fixed sample has a closed form {{c:wilson1927,efron1979}}, and where no closed
form exists the bootstrap supplies one {{c:efron1993}}. The reporting side matters as much: a p-value is
not the probability that a hypothesis is true {{c:goodman2008}}, which is why every verdict in this
paper is an interval placed against a floor rather than a threshold crossed.

### 2.5 Allocation, which is a sequential decision

Spending the next request wide or deep is an allocation over a finite number of pulls, and it has a name
in the decision literature: exploration against exploitation {{c:march1991}}, written as a policy over
states {{c:sutton1999}}, with probability matching as the original rule for dividing finite trials
{{c:thompson1933}} and sequential assignment across arms as the formal object {{c:robbins1952}}; bandit
treatments are the modern statement of the same problem {{c:auer2002,lattimore2020}}. Proximity on a
citation-like graph has been computed for a long time — through hubs and authorities
{{c:kleinberg1999}}, link ranking {{c:brin1998}} and random walks with restart {{c:tong2006}} — and all of
it answers *what is near this seed*, not *what the next request buys*. The one prior bearing directly on
order is that attention to a paper decays {{c:parolo2015}}: if a seed's citers are a wasting asset, then
**when** a request is spent is part of what it is worth, which is why this paper prices a request and not
a work.

### 2.6 How this paper differs from the closest work

Four works are close enough that the difference has to be stated rather than implied.

**Wohlin's snowballing guidelines {{c:wohlin2014}}** prescribe a procedure and stop at saturation. The unit
there is a search session with a recall target; this paper prices one request and reports what that
request returns, so its quantity is defined per call rather than per session.

**Kessler's bibliographic coupling {{c:kessler1963}}**, and co-citation after it {{c:small1973}}, define a
similarity between works. This paper uses that same predicate — it does not propose a new one — but
judges its **excess over a length-matched null per request**, which neither defines, and that excess is
what decays with hop depth.

**The bandit formulation {{c:march1991,lattimore2020}}** supplies the allocation framework this paper
adopts, and assumes a reward model. Here the reward model is measured from the service's own refusals,
and the result is that at this registry's price the optimum is degenerate rather than merely unknown —
a conclusion about the price, not about the algorithm.

**The attention-decay literature {{c:parolo2015}}** measures decay on a clock of time since publication.
This paper measures decay on a clock of hop distance from a seed, at equal request price. A citers'
asset that decays in time and one that decays in hops are different quantities, and only the second
answers the question asked here.

## 3. The null, and why it has to be length-matched

Two reference lists of lengths `a` and `b` drawn from a field's vocabulary couple at a rate that rises
with both. A control sample whose median reference list is empty therefore measures the archive's
coverage, not the field's behaviour. We bin every candidate by its own reference-list length
({{n:bins.0}}, {{n:bins.1}}, {{n:bins.2}}, {{n:bins.3}}), draw a null pool of
field works in the same year window, and compute the same predicate against the **same seed**. A bin
with fewer than {{n:min_null_per_bin}} null works is reported NOT RUN and is never read as a zero.

The sample is drawn from OpenAlex {{c:priem2022}}, and coverage in any bibliographic database is uneven
by region and language {{c:mongeon2016,visser2021}} — a different database would let a different study
see different things {{c:visser2021}} — while the sampling design is part of the estimator rather than a
preliminary to it {{c:kish1965}}. Field assignment is the same kind of commitment: publication-level
classifications differ and the choice moves the answer {{c:waltman2012,klavans2017}}, normalisation
methods for cross-field comparison rest on different assumptions {{c:waltman2012b,schubert1996}}, and
fields differ in reporting behaviour in ways normalisation does not remove {{c:fanelli2010}}. It is also
why the two fields are never pooled: combining subgroups can reverse a comparison {{c:simpson1951}}, a
reversal that has bitten real data {{c:bickel1975}}, and the between-field difference is the quantity
under test rather than an inconvenience to be averaged away.

## 4. Frame, and the cost model

Seeds are drawn reproducibly inside a top-level field with a fixed year window, citation band and
sampling seed; the field's `display_name` is verified before sampling, because a filter without a field
constraint silently lands in another discipline while every instrument check stays green.

Both arms are named by the register's own identifiers rather than by a label typed here: the first field
is field {{n:arms.cs.field.id}} and the second is field {{n:arms.social_sciences.field.id}}, and each
arm's filter constrains `primary_topic.field.id` — the top-level field itself, not a subfield beneath
it. The identifier is printed because the name alone does not fix the referent: the same register also
carries a *domain* under which that field sits, and the domain's display name is identical to the
second field's, so "field" is the word doing the work in every sentence that compares the two.

The cost model is the API's, not ours, and both constants are measured from the service's own refusals
rather than chosen: a page (`filter=cites:`) returns at most {{f:arms.cs.cost_constants.breadth_page_works_max|int}}
works (one more is refused), and an id filter accepts at most
{{f:arms.cs.cost_constants.depth_batch_ids_max|int}} values (more is refused with *"Maximum number of values exceeded"*).
One page therefore sells twice the works of one batch for the same one request. The cost ratio `w` is
defined as *the price of one depth batch divided by the price of one breadth page*; the API's own
accounting is `w = 1`, and a batch can never cost less than zero, so the admissible range is `w ≥ 1`.

Both constants are measured rather than chosen, and that is a design commitment rather than a
formality: case-study research has to state its design and the inferences it licenses
{{c:runeson2009,wohlin2012}}, benchmarking practice needs its own critique {{c:lipton2018}}, and an
impact signal that is convenient to compute is not thereby the right one {{c:bollen2009,sugimoto2017}}. The two
constants this paper uses happen to be exact, because the service states them by refusing to exceed
them.

## 5. Results

### 5.1 The decay

Table 1. Coupled share and its excess over the length-matched, field-matched null.

| hop | field | coupled / defined | observed | null | excess |
|---|---|---|---|---|---|
| hop 1 | Computer Science | {{n:arms.cs.pooled.hop1.coupled}} / {{n:arms.cs.pooled.hop1.n_defined}} | {{f:arms.cs.pooled.hop1.observed_share|f3}} | {{f:arms.cs.pooled.hop1.null_share|f3}} | {{f:arms.cs.pooled.hop1.excess|f3}} |
| hop 2 | Computer Science | {{n:arms.cs.pooled.hop2.coupled}} / {{n:arms.cs.pooled.hop2.n_defined}} | {{f:arms.cs.pooled.hop2.observed_share|f3}} | {{f:arms.cs.pooled.hop2.null_share|f3}} | {{f:arms.cs.pooled.hop2.excess|f3}} |
| hop 1 | Social Sciences | {{n:arms.social_sciences.pooled.hop1.coupled}} / {{n:arms.social_sciences.pooled.hop1.n_defined}} | {{f:arms.social_sciences.pooled.hop1.observed_share|f3}} | {{f:arms.social_sciences.pooled.hop1.null_share|f3}} | {{f:arms.social_sciences.pooled.hop1.excess|f3}} |
| hop 2 | Social Sciences | {{n:arms.social_sciences.pooled.hop2.coupled}} / {{n:arms.social_sciences.pooled.hop2.n_defined}} | {{f:arms.social_sciences.pooled.hop2.observed_share|f3}} | {{f:arms.social_sciences.pooled.hop2.null_share|f3}} | {{f:arms.social_sciences.pooled.hop2.excess|f3}} |

The pooled share is not the statistic we judge; it weights each seed by how many works it contributed.
The per-seed statistic is `d(s) = excess(hop 2) - excess(hop 1)`, and it is judged over the seed-level
distribution, because works inside one seed share its reference vocabulary and a binomial pooled across
seeds would be over-precise.

Table 2. Per-seed decay, by field.

| field | seeds | mean `d` | {{n:ci_level}}% interval | median | seeds `d<0` | law |
|---|---|---|---|---|---|---|
| Computer Science | {{n:arms.cs.decay.n_seeds_with_d}} | {{f:arms.cs.decay.mean_d|f4}} | {{f:arms.cs.decay.ci95_mean_d|ci3}} | {{f:arms.cs.decay.median_d|f3}} | {{n:arms.cs.decay.seeds_d_lt_0}} | holds |
| Social Sciences | {{n:arms.social_sciences.decay.n_seeds_with_d}} | {{f:arms.social_sciences.decay.mean_d|f4}} | {{f:arms.social_sciences.decay.ci95_mean_d|ci3}} | {{f:arms.social_sciences.decay.median_d|f3}} | {{n:arms.social_sciences.decay.seeds_d_lt_0}} | holds |

Figure 1 (`figures/fig1_decay.png`) draws the same distribution seed by seed, and each axis label
carries that field's own count of negative seeds rather than a summary word — the law is a statement
about the mean, and the figure is drawn so that a reader can see how much of it the seeds carry.

Between the two fields the difference of the mean `d` is
{{f:between_fields.difference_ss_minus_cs|f4}} with a {{n:ci_level}}% interval
{{f:between_fields.ci95|ci3}}: indistinguishable at this sample size, which is what a replication looks
like. **The fields are deliberately not pooled** — the between-field variation is the claim under test,
and pooling would buy precision by erasing it.

### 5.2 The price at which the allocation would change

Table 3. What one request buys, and the flip ratio.

| field | coupled per page | coupled per batch | page worth, in batches | `w*` | {{n:ci_level}}% interval | admissible? |
|---|---|---|---|---|---|---|
| Computer Science | {{f:arms.cs.cost.mean_coupled_per_page|f3}} | {{f:arms.cs.cost.mean_coupled_per_batch|f3}} | {{f:arms.cs.cost.page_worth_in_batches|f3}} | {{f:arms.cs.w_star.point|f3}} | {{f:arms.cs.w_star.ci95|ci3}} | no |
| Social Sciences | {{f:arms.social_sciences.cost.mean_coupled_per_page|f3}} | {{f:arms.social_sciences.cost.mean_coupled_per_batch|f3}} | {{f:arms.social_sciences.cost.page_worth_in_batches|f3}} | {{f:arms.social_sciences.w_star.point|f3}} | {{f:arms.social_sciences.w_star.ci95|ci3}} | no |

`w*` is the largest batch price at which buying depth beats spending the same request budget on
breadth; Figure 2 (`figures/fig2_price_bound.png`) places both intervals against the floor. Since `w ≥ 1` always, an interval entirely below one is not a near miss but a closed
direction **for this registrant**: no plausible client pays a tenth of a request for a batch. A
registry whose batch carried more than {{f:arms.cs.cost.page_worth_in_batches|f2}} times a page's
coupled yield would open it again, and that is the falsifier a reader should test.

### 5.3 What would have made depth look good, and did not

Two analyses are reported because they are the ones an allocation claim would have leaned on, and both
came out negative. First, selecting seeds on a statistic already paid for does not raise the yield:
rank correlations between a seed's depth yield and its cited-by count, citer count and candidate-pool
size were all below about a quarter in absolute value (registered on the issue thread, reproduced in
`results.json`). Second, even a hindsight oracle — the seeds whose actual combined yield is highest —
beats pure breadth by an interval that includes one. The depth-wins branch is not merely hard to select;
in this sample it is barely worth selecting.

Both analyses are controls of one kind: they hold the budget fixed and change only the rule. A control
earns the name when the effect it is meant to remove is known in advance, the way a named interference
effect gives a task a known cost {{c:stroop1935}}. Here that known effect is the coupling that
reference-list length alone produces, and it is what the null in §3 removes.

## 6. Prior beliefs, reported against the data

These were registered on the issue before the decisive measurement.

The registered priors are stated as magnitudes because a prior stated as a direction cannot be wrong
in an interesting way. That choice follows the metric literature: a metric needs a statement of what it
measures before it is used {{c:hicks2015,ioannidis2014b}}, an aggregate can look authoritative while not
being an article-level quantity {{c:seglen1997}}, and an index without a statistical basis cannot carry
an interval at all {{c:waltman2012c,bornmann2007h}}. It also follows the statistical literature on how such statements
fail: significance is a threshold and not a finding {{c:amrhein2019}}, a small study's interval must be
read against the effect it could have detected {{c:borenstein2009,king2001b}}, an absence is reported by
testing for equivalence rather than by failing to reject {{c:lakens2017}}, and the judgement of what a
result means is subject to stated biases {{c:tversky1974}}.

| prior | statement | outcome |
|---|---|---|
| P1 | breadth beats depth per request by at least a factor of two at equal budget | **confirmed in direction, wrong in magnitude as stated**: the page-to-batch ratio is {{f:arms.cs.cost.page_worth_in_batches|f2}} in Computer Science and {{f:arms.social_sciences.cost.page_worth_in_batches|f2}} in Social Sciences |
| P2 | hop 2 is not worthless: its excess is many times chance | **confirmed**, {{f:arms.cs.pooled.hop2.excess|f3}} against a null of {{f:arms.cs.pooled.hop2.null_share|f3}} |
| P3 | the breadth advantage is not an artefact of the cost model | **unresolved, and reported as such**: with the price pinned from the API's own refusals the ratio is {{f:arms.cs.cost.page_worth_in_batches|f2}}, but the flip ratio moves with the budget-to-pool ratio, so the advantage is partly a property of the model |

## 7. Contribution level, and what this study can detect

The level this paper claims is **`theory+empirics`**, on the evidence it actually carries and narrowed
where that evidence narrows it. The theory is the price bound derived from the cost model in §5.2: depth
wins only if one depth batch costs less than `w*` breadth pages. The empirics are a decay law judged
against a length-matched null, measured in two independent fields, the second chosen by a rule fixed
before it was measured, with two controls — an arm that follows the opposite rule, and a hindsight
oracle. The universal claim stops at the registry: the bound is a statement about this API's documented
request caps, not about citation networks in general.

The obligations taken on here are not self-imposed ceremony. Preregistration changes what a result can
mean {{c:nosek2018}}, a registered report goes further and fixes the analysis before the data exist
{{c:chambers2013}}, and the space of defensible analyses that leaves open is exactly why a result can be
made to look robust after the fact {{c:gelman2014}}. The reproducibility agenda this joins is stated as a
standard rather than an aspiration {{c:peng2011}}, an openness programme {{c:nosek2012,miguel2014}}, and
it now applies to machine learning and artificial intelligence as much as to the fields it began in
{{c:hutson2018}}.

That level also obliges the paper to say what it cannot resolve, and to place each verdict above
against the sample's own noise. The half-width of an interval is the smallest effect this study can
distinguish; an effect narrower than it is **no information**, and is never reported here as evidence
for or against a prior.

| quantity | half-width of its {{n:ci_level}}% interval | how a narrower effect must be read |
|---|---|---|
| mean decay `d`, Computer Science | {{f:arms.cs.decay.halfwidth_mean_d|f3}} | a mean decay smaller than this is not resolved |
| mean decay `d`, Social Sciences | {{f:arms.social_sciences.decay.halfwidth_mean_d|f3}} | same, in the second field |
| `w*`, Computer Science | {{f:arms.cs.w_star.halfwidth|f3}} | `w*` is located to about this much of a page |
| `w*`, Social Sciences | {{f:arms.social_sciences.w_star.halfwidth|f3}} | same, in the second field |
| difference of the two fields | {{f:between_fields.halfwidth|f3}} | the observed difference is far inside it |

Read against this table, the two headline results are not marginal: the mean decay is
{{f:arms.cs.decay.mean_d|f3}} in the first field (interval {{f:arms.cs.decay.ci95_mean_d|ci3}}) and
{{f:arms.social_sciences.decay.mean_d|f3}} in the second ({{f:arms.social_sciences.decay.ci95_mean_d|ci3}}),
so each interval clears zero by more than its own half-width, and each `w*` interval clears the floor the
same way. The third prior in §6 is a different case, which is why it is reported as unresolved rather
than as a refutation: the field-to-field difference is
{{f:between_fields.difference_ss_minus_cs|f4}} with interval {{f:between_fields.ci95|ci3}}, which
contains zero, so at this sample size it is no information either way.

## 8. A correction kept visible

An earlier draft of this work reported the flip ratio as a value above one and concluded that the two
allocations tie at the API's own price. That number was wrong, and wrong for a reason worth recording:
the breadth arm was credited with the **first `B` seeds in sample order**, an arbitrary draw that
happened to be weak, while every depth arm was averaged. Recomputing over random orderings moved the
flip ratio from the published figure to **{{f:arms.cs.w_star.point|f3}}** in Computer Science. The
conclusion reversed, and the retracted figure stays here rather than being silently absorbed into the
final number.

## 9. Threats to validity

**The estimand is overlap, not usefulness.** Stated in §1 and repeated here because it is the limitation
a reader is most likely to forget.

**Two fields, both large and both general.** The field-selection rule was fixed before the second field
was measured — the largest non-CS top-level field by work count — precisely so that agreement could not
be chosen. Two fields is not universality, and no third field is claimed.

**Field membership is by construction, not re-derivable from the bytes.** The committed arms carry work
identifiers and reference lists, not each work's own topic, so nothing in this package lets a reader
re-check that a given work sits in the field its arm is named for. That guarantee comes from the
recorded filter string and from the display-name check the capture performs before it samples; a reader
who wants the second line of evidence has to re-issue the query.

**One registry.** The price bound is a statement about this API's documented request caps. A registry
whose page-to-batch payload ratio differed would move `w*`; the formula is given so it can be recomputed.

**A construction zero bounds the domain.** One Computer Science seed had no coupled citers at all
({{n:arms.cs.construction_zeros.0}}); its contribution is a labelled zero, not a measurement, and it
marks where the statistic is defined.

**The per-request price is a request count.** Rate limits differ per endpoint in ways this study does
not measure, so `w` is a count ratio and not wall-clock or money.

**A negative finding is still a claim about the world, and this literature exists because such claims
fail.** That is why an interval is printed next to every verdict: published findings have repeatedly
failed to hold {{c:ioannidis2005}}, that failure has been made measurable rather than rhetorical
{{c:nosek2015}}, and the response has been a stated programme rather than an appeal to care
{{c:munafo2017}}. A reader who accepts the decay law should be able to re-derive it from the committed
arms in one command, which is what the reproduction section sets out.

**Why it is still worth publishing.** The bound is falsifiable in one step and it tells a tool builder
where to look: a batch-shaped endpoint would have to beat a page by more than
{{f:arms.cs.cost.page_worth_in_batches|f2}} before depth deserves any of the budget.

## 10. Reproduction

`README.md` states the one command and the expected output. The committed data are the two arms'
reference lists, with digests taken over the decompressed bytes, and `analysis.py` is a pure function of
them: it fetches nothing and imports nothing outside the standard library.

## References

{{refs}}
