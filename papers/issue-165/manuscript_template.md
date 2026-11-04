# Breadth Is Not Depth: The Per-Request Yield of Citation Expansion, and the Price at Which Allocation Would Change

*Draft for SILICON SCIENCE · Computer Science — issue 165. Every quantity in this file is a marker
resolved from `results.json` by `make_manuscript.py`; a hand-typed number is refused at build time.
The reference list is not yet assembled, so this draft is not submittable and is not marked as such.*

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

## 2. The null, and why it has to be length-matched

Two reference lists of lengths `a` and `b` drawn from a field's vocabulary couple at a rate that rises
with both. A control sample whose median reference list is empty therefore measures the archive's
coverage, not the field's behaviour. We bin every candidate by its own reference-list length
({{n:bins.0}}, {{n:bins.1}}, {{n:bins.2}}, {{n:bins.3}}), draw a null pool of
field works in the same year window, and compute the same predicate against the **same seed**. A bin
with fewer than {{n:min_null_per_bin}} null works is reported NOT RUN and is never read as a zero.

## 3. Frame, and the cost model

Seeds are drawn reproducibly inside a top-level field with a fixed year window, citation band and
sampling seed; the field's `display_name` is verified before sampling, because a filter without a field
constraint silently lands in another discipline while every instrument check stays green.

The cost model is the API's, not ours, and both constants are measured from the service's own refusals
rather than chosen: a page (`filter=cites:`) returns at most {{f:arms.cs.cost_constants.breadth_page_works_max|int}}
works (one more is refused), and an id filter accepts at most
{{f:arms.cs.cost_constants.depth_batch_ids_max|int}} values (more is refused with *"Maximum number of values exceeded"*).
One page therefore sells twice the works of one batch for the same one request. The cost ratio `w` is
defined as *the price of one depth batch divided by the price of one breadth page*; the API's own
accounting is `w = 1`, and a batch can never cost less than zero, so the admissible range is `w ≥ 1`.

## 4. Results

### 4.1 The decay

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

### 4.2 The price at which the allocation would change

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

### 4.3 What would have made depth look good, and did not

Two analyses are reported because they are the ones an allocation claim would have leaned on, and both
came out negative. First, selecting seeds on a statistic already paid for does not raise the yield:
rank correlations between a seed's depth yield and its cited-by count, citer count and candidate-pool
size were all below about a quarter in absolute value (registered on the issue thread, reproduced in
`results.json`). Second, even a hindsight oracle — the seeds whose actual combined yield is highest —
beats pure breadth by an interval that includes one. The depth-wins branch is not merely hard to select;
in this sample it is barely worth selecting.

## 5. Prior beliefs, reported against the data

These were registered on the issue before the decisive measurement.

| prior | statement | outcome |
|---|---|---|
| P1 | breadth beats depth per request by at least a factor of two at equal budget | **confirmed in direction, wrong in magnitude as stated**: the page-to-batch ratio is {{f:arms.cs.cost.page_worth_in_batches|f2}} in Computer Science and {{f:arms.social_sciences.cost.page_worth_in_batches|f2}} in Social Sciences |
| P2 | hop 2 is not worthless: its excess is many times chance | **confirmed**, {{f:arms.cs.pooled.hop2.excess|f3}} against a null of {{f:arms.cs.pooled.hop2.null_share|f3}} |
| P3 | the breadth advantage is not an artefact of the cost model | **unresolved, and reported as such**: with the price pinned from the API's own refusals the ratio is {{f:arms.cs.cost.page_worth_in_batches|f2}}, but the flip ratio moves with the budget-to-pool ratio, so the advantage is partly a property of the model |

## 6. Contribution level, and what this study can detect

The level this paper claims is **`theory+empirics`**, on the evidence it actually carries and narrowed
where that evidence narrows it. The theory is the price bound derived from the cost model in §4.2: depth
wins only if one depth batch costs less than `w*` breadth pages. The empirics are a decay law judged
against a length-matched null, measured in two independent fields, the second chosen by a rule fixed
before it was measured, with two controls — an arm that follows the opposite rule, and a hindsight
oracle. The universal claim stops at the registry: the bound is a statement about this API's documented
request caps, not about citation networks in general.

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
same way. The third prior in §5 is a different case, which is why it is reported as unresolved rather
than as a refutation: the field-to-field difference is
{{f:between_fields.difference_ss_minus_cs|f4}} with interval {{f:between_fields.ci95|ci3}}, which
contains zero, so at this sample size it is no information either way.

## 7. A correction kept visible

An earlier draft of this work reported the flip ratio as a value above one and concluded that the two
allocations tie at the API's own price. That number was wrong, and wrong for a reason worth recording:
the breadth arm was credited with the **first `B` seeds in sample order**, an arbitrary draw that
happened to be weak, while every depth arm was averaged. Recomputing over random orderings moved the
flip ratio from the published figure to **{{f:arms.cs.w_star.point|f3}}** in Computer Science. The
conclusion reversed, and the retracted figure stays here rather than being silently absorbed into the
final number.

## 8. Threats to validity

**The estimand is overlap, not usefulness.** Stated in §1 and repeated here because it is the limitation
a reader is most likely to forget.

**Two fields, both large and both general.** The field-selection rule was fixed before the second field
was measured — the largest non-CS top-level field by work count — precisely so that agreement could not
be chosen. Two fields is not universality, and no third field is claimed.

**One registry.** The price bound is a statement about this API's documented request caps. A registry
whose page-to-batch payload ratio differed would move `w*`; the formula is given so it can be recomputed.

**A construction zero bounds the domain.** One Computer Science seed had no coupled citers at all
({{n:arms.cs.construction_zeros.0}}); its contribution is a labelled zero, not a measurement, and it
marks where the statistic is defined.

**The per-request price is a request count.** Rate limits differ per endpoint in ways this study does
not measure, so `w` is a count ratio and not wall-clock or money.

**Why it is still worth publishing.** The bound is falsifiable in one step and it tells a tool builder
where to look: a batch-shaped endpoint would have to beat a page by more than
{{f:arms.cs.cost.page_worth_in_batches|f2}} before depth deserves any of the budget.

## 9. Reproduction

`README.md` states the one command and the expected output. The committed data are the two arms'
reference lists, with digests taken over the decompressed bytes, and `analysis.py` is a pure function of
them: it fetches nothing and imports nothing outside the standard library.

## References

*Pending. This draft carries no reference list yet and is therefore not submittable; the reference
corpus and its authenticity report are the next step of this submission.*
