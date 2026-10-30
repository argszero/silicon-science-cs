# What Decides Whether Recall@k Is Determined: The Resolution of the Index's Distance

### A case study on one corpus, three quantiser families, and two scales

---

## Abstract

Approximate nearest-neighbour search is measured by recall@k against an exhaustive ground
truth, and when several database points share the k-th distance the procedure names some of them
and not others. For a *provably correct* index the metric can therefore take any value in an
identified set `[floor, 1]`, and this paper asks a question the recall literature does not: what
decides whether that set has any width at all?

The answer this study measures is not the quantiser family and not the bit budget. It is the
**local resolution of the distance the index computes** — how many distinct distance values the
near neighbourhood of a query actually occupies. Across {{n:A.configs}} configurations spanning
three families (random-hyperplane Hamming, product quantisation, scalar quantisation) on
{{n:A.corpus.n}} real SIFT descriptors, the boundary tie group is ordered by resolution on a log-log
scale at `r = {{n:A.r}}` over {{n:A.n_cells}} seed-level cells; at {{n:B.corpus.n}} descriptors
the same ordering holds at `r = {{n:B.r}}` over {{n:B.configs}} configurations. Hamming distance
attains only `b+1` values for a `b`-bit code and ties badly — median boundary group
{{n:B.hamming32.median_t}} at the shortest budget, mean floor {{n:B.hamming32.floor}} — while
product and scalar quantisation, which attain hundreds of values, tie barely: median group
{{n:B.pq32.median_t}} and floor {{n:B.pq32.floor}} to {{n:B.pq64.floor}}. The two families most
widely deployed at billion scale are therefore the ones the effect leaves almost untouched.

The paper states plainly what this replaces. This study **registered the opposite claim** — that
recall@k on compact codes *as such* is undetermined — and the second and third quantiser families
**refute it**. That refutation is reported with the numbers that produced it, not deleted. Three
registered priors are likewise reported as refuted, supported, or refuted-in-one-space, and the
scaling prior is refuted.

Contribution level: **`case study`**. One corpus, two scales of it, {{n:B.configs}} configurations
at the larger scale. The instrument is exact and its two endpoint controls are run on every
reproduction; the scope is one corpus and the abstract says so rather than a limitations section.

---

## 1. The question

A benchmark reports one number per (index, recall@k) cell. The number is computed against an
exhaustive ground truth: sort every database point by its distance to the query, take the first
k, ask how many of them the index returned. The sorting step hides an assumption. When several
points sit at exactly the k-th distance, the sorted list still gives k points, but *which* ones is
decided by the implementation's internal order rather than by the data.

Two points share a distance at the boundary when the distance takes few distinct values. Hamming
distance on a `b`-bit code can take only `b+1`; a real-valued distance takes as many values as the
floating-point representation allows. So the question this paper asks is narrow enough to be
answerable: **does the width of recall@k's identified set follow the coarseness of the distance
in the neighbourhood that matters, rather than the identity of the quantiser that induced it?**

That question has a practitioner's form. A team comparing a 32-bit code with a 64-bit code reads
the recall gap and decides. If the gap is smaller than the width the metric admits on that corpus,
the comparison cannot be resolved by the two published numbers regardless of how carefully either
was computed. The question of *which* indices are subject to that is the question of this paper.

## 2. What recall@k does at a tie

For one query, let `d_k` be the k-th smallest distance. Write

- `r` for the number of boundary slots the top-k must still fill after every point strictly nearer
 than `d_k` has been taken,
- `t` for the number of points at exactly `d_k`.

Any admissible tie-break may take any `r` of those `t` points. A provably correct index that
disagrees with the stored ground truth on which `r` it took scores at worst `(k - 2r)/k` when the
tie group is large enough, and at best `1`. The identified set is therefore `[floor, 1]`, with

 floor = ((k - r) + max(0, 2r - t)) / k

which needs no sampling and no enumeration: it is an arithmetic consequence of `r` and `t`. This
paper calls `floor` the **identified-set floor** and reports it alongside every tie-group size.

Two properties of `floor` are worth stating because they make it checkable at its endpoints. When
the boundary tie group holds a single point (`t = 1`), there is nothing to choose and `floor = 1`:
the metric is fully determined. When the entire top-k lies inside one tie group, `floor` attains
its minimum for that `r`, and in the degenerate case where the whole corpus is one group and
`k <= n` it is `0`. Those two endpoints are the controls of section 3.

## 3. The instrument, and its two endpoint controls

The instrument is a function of the query's distance row alone: sort, find `d_k`, count `r` and
`t`, evaluate `floor`. Three things are needed for it to measure anything.

**Exactness.** The subject is *which distances are equal*, so distances measured in floating point
would measure rounding noise. Every distance this paper reports is an exact integer. SIFT
descriptors are integer-valued, so the quantiser reconstructions are constrained to the same
integer grid (product-quantisation centroids are rounded onto it, scalar-quantisation levels are
integers), and the float32 matrix product that computes them is asserted against an independent
int64 computation on {{n:A.corpus.knn}}-scale samples before a single tie is counted. The bound
that makes this safe is checked, not assumed.

**Endpoint controls.** `reproduce.sh` asserts both on every run. On the raw descriptors — where the
boundary tie group is a single point because no two of a million integer-valued vectors share an
exact squared distance — the mean floor is **{{n:A.float.floor}}** and the median tie group is
{{n:A.float.median_t}}. On a constructed corpus where every point is one repeated vector, the mean
floor is **{{n:A.constructed.floor}}** with a tie group of {{n:A.constructed.median_t}}. An
instrument that cannot reach "fully determined" where the answer is known, and cannot reach
"maximally undetermined" where the ambiguity is total, has not been shown to measure either.

**Resolution.** The explanatory variable is the number of distinct distance values occupied by the
nearest {{n:A.corpus.knn}} points of a query. It is deliberately local: the global range of a
distance says little, while the mass that `n · P(D = d_k)` places on the k-th value is exactly
what the tie group is.

## 4. What governs the tie group

Three quantiser families are run on the same corpus and the same queries, at budgets chosen so the
families can be compared:

- **random-hyperplane Hamming** — `b` random hyperplanes, one bit each; the distance takes `b+1`
 values;
- **product quantisation** — the descriptor split into sub-vectors, each replaced by one of many
 integer centroids; the distance takes on the order of the number of distinct reconstructions;
- **scalar quantisation** — each component rounded onto a small set of integer levels.

The result is a monotone ordering, and it is the same ordering whether the ordering is read off the
tie group or off the resolution. Median boundary tie group across the configurations runs from
{{n:A.hamming32.median_t}} at the coarsest Hamming budget to {{n:A.hamming256.median_t}} at the
finest, and the mean floor at the finely resolved families is {{n:A.pq32.floor}} and
{{n:A.pq64.floor}} against a Hamming floor that stays far below it. The families are not ordered by
which quantiser is "better": at equal bit budget product quantisation is a substantially more
accurate code than random hyperplanes, and that accuracy is not the variable. The variable is how
many distinct values the distance can take in the neighbourhood where the k-th point sits.

This is the paper's central claim, in falsifiable form: **hold the corpus and the query fixed, and
the width of the identified set is predicted by the local resolution of the distance, not by the
quantiser family and not by the bit budget alone.**

## 5. At the benchmark's own scale

The same axis is measured on {{n:B.corpus.n}} descriptors — a factor of fifty more points than the
committed subsample, with {{n:B.corpus.n_queries}} queries per seed — and it holds:
`r = {{n:B.r}}` over {{n:B.configs}} configurations. The resolution ranges from
{{n:B.hamming32.atoms}} distinct values in the near neighbourhood of a short Hamming budget to
{{n:B.pq32.atoms}} for product quantisation. Correspondingly the median boundary tie group is
{{n:B.hamming32.median_t}} at the short Hamming budget, {{n:B.hamming64.median_t}} at twice the
budget and {{n:B.hamming256.median_t}} at the finest, against {{n:B.pq32.median_t}} for product
quantisation. The mean floor tells the practitioner's version of the same story: for Hamming at the
short budget a correct index can be graded **{{n:B.hamming32.floor}}** on average and
{{n:B.hamming32.frac_floor_lt1}} of queries are not fully determined, while product quantisation
gives **{{n:B.pq32.floor}}** and scalar quantisation **{{n:B.sq2.floor}}**.

Raw descriptors, measured in the same run at the same scale, give **{{n:B.float.floor}}**. That
number is the control that keeps the rest honest: the metric is fully determined on the objects
themselves, and everything this paper reports is about distances that a *code* introduces.

## 6. The claim this study registered, and that it is refuted

This study registered the claim that recall@k on compact codes is undetermined, with three priors.
Reporting the outcome plainly is part of the contribution, because the refutation is what turned
the study into a case study about an axis instead of a validation paper about a metric.

**The registered headline is refuted.** Two further families — product and scalar quantisation —
put the boundary tie group far outside the interval established for random hyperplanes, and at the
larger scale their floors are {{n:B.pq32.floor}}, {{n:B.pq64.floor}} and {{n:B.sq2.floor}}. A claim
that compact codes are undetermined cannot survive families whose median query has no tie at all.

**P1, that the tie group is invariant in corpus size, is refuted** by the scaling measurement: the
group grows with the corpus, with the fitted exponent rising as the code shortens.

**P2, that the driver is distance concentration rather than code-space occupancy, is supported in
its mechanism and wrong in its variable.** Occupancy was indeed never the driver. But the variable
that replaces it is not concentration in the abstract — it is the measured number of distinct values
the distance takes, which is what section 4 tests directly.

**P3, on the harness's stored ground truth, is refuted in the space the metric lives in.** The
stored ground truth is not an arbitrary draw: it agrees with a data-determined rule on the
overwhelming majority of queries, and in the space the benchmark scores in a correct index that
returns a different admissible member loses a quantity of recall far below any decision threshold.

The direction's pre-registered stop rule distinguished one failure from two: a single family
falling outside the interval narrowed the claim, and only a *loss of metric consequence together
with* a loss of generality abandoned the direction. This study reports that reading and the
correction to its own earlier application of it — the earlier round applied the weaker condition
as if it were the stronger one, and the error is corrected in the public record rather than
quietly replaced.

## 7. Related work

**Approximate nearest-neighbour search.** The line runs from tree-based exact structures
{{c:bentley-1975}} through locality-sensitive hashing 
 {{c:charikar-2002}} and on to graph-based indices
{{c:malkov-yashunin-2020}} and GPU systems {{c:johnson-douze-jegou-2021}}, with a vector-database
layer arriving more recently {{c:wang-milvus-2021}} {{c:pan-vector-db-survey-2024}}. This paper
takes no position on which index is faster; it asks what a recall number computed against any of
them can mean.

**Compression of vectors into codes.** Product quantisation {{c:jegou-douze-schmid-2011}} and its
optimised variants {{c:ge-optimized-pq-2014}}, additive quantisation
{{c:babenko-additive-quant-2014}}, the inverted multi-index {{c:babenko-inverted-multi-index-2015}}
and billion-scale deep-descriptor indexing {{c:babenko-deep1b-2016}} are the systems whose reported
recall this paper's axis bears on. Binary-code learning — spectral hashing {{c:weiss-spectral-hashing-2009}},
iterative quantisation {{c:gong-itq-2011}}, minimal-loss hashing,
min-wise independent permutations {{c:broder-minhash-1997}} — supplies the short-code regime where
the effect is largest. The difference from all of them: none reports how much of its published
recall is determined by the data, and the axis here predicts which of them can be.

**Quantisation theory.** Vector quantisation {{c:gray-vector-quantization-1984}}
{{c:gersho-gray-vq-book-1992}}, Lloyd's optimality conditions {{c:lloyd-least-squares-1982}} and
k-means++ seeding are the machinery used here, with the one change that
reconstructions are constrained to the data's own integer grid so that distances are exact. That
constraint is this paper's, not the literature's, and it is what makes a tie measurable rather than
a rounding artefact.

**Evaluation methodology.** Effectiveness measures and pooling have a long critical literature in
information retrieval {{c:manning-ir-book-2008}} 
{{c:buckley-incomplete-info-2004}}, including what incomplete judgements do to a reported number.
The difference: that literature studies *incomplete* judgements, whereas the ambiguity here is
present in a *complete* exhaustive ground truth, introduced by the representation rather than by
the sampling.

**Curse of dimensionality and concentration.** The observation that distances concentrate as
dimensionality grows {{c:beyer-meaningful-nn-1999}} is the
nearest relative of this paper's variable, and the measurement here is that concentration is not
itself the predictor — the number of attainable values is. Concentration bounds
  supply the reason a distance at
an order statistic has `O(1)` mass rather than vanishing, which is the mechanism this paper
measures instead of assuming.

**Benchmarking practice.** The most widely used harness for this problem is `ann-benchmarks`
{{c:aumuller-ann-benchmarks-2017}}, and the corpus used here is the SIFT descriptor set
{{c:lowe-sift-2004}} it distributes. The comparison with this paper is not a criticism of that
harness: its stored ground truth is data-determined on the majority of queries in the space it
scores in, which this study verified rather than assumed.

## 8. Threats to validity, and why the result still stands

**One corpus.** Every number is on `sift-128-euclidean`. The larger scale is fifty times as many
descriptors from the same source, not a second dataset, so the axis is shown to survive scale and
not shown to survive a change of data. This is the study's binding limitation and it is why the
contribution level is a case study.

**Configurations, not cells.** The correlation is computed over seed-level cells; three seeds of one
configuration are one configuration measured thrice. The program prints both counts and the paper
quotes the configuration count as evidence.

**Resolution is measured, not derived.** No closed form predicts the number of distinct distance
values a quantiser induces, so the axis is an empirical predictor. That is enough to falsify the
"family" explanation and to order the families, and it is not a theory of the axis.

Why the result stands anyway: the refutation of the registered claim does not depend on any of the
limitations — product and scalar quantisation tie barely on this corpus, and that contradicts the
registered generalisation whatever else is true. And the axis is the object that survives: it
explains the presence *and* the absence of the effect with one measured quantity, where the
registered claim explained only its presence.

## 9. Reproduction

`./reproduce.sh` reproduces every number in this paper from the committed fixture, with numpy
alone and no network; `./reproduce.sh full` adds the {{n:B.corpus.n}}-descriptor tier, which prints
`NOT RUN` rather than failing when the corpus is absent. The mechanism table is regenerated twice
and byte-compared, so a number that moves between two runs fails the build, and a program reads the
artefact back to test the claims this paper makes about it.

## References

{{refs}}
