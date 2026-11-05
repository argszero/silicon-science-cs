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

A benchmark reports one number per (index, recall@k) cell. The measure descends from the
vector-space and probabilistic-relevance tradition of information retrieval
{{c:salton-vsm-1975,robertson-relevance-weighting-1976,sparck-jones-idf-1972,robertson-bm25-2009}},
whose textbook
treatments are explicit that an effectiveness figure is an estimate over a judged set rather than
a property of the system alone {{c:manning-ir-book-2008,zobel-similarity-space-1998}}. The number
is computed against an exhaustive ground truth: sort every database point by its distance to the
query, take the first k, ask how many of them the index returned. The sorting step hides an assumption. When several
points sit at exactly the k-th distance, the sorted list still gives k points, but *which* ones is
decided by the implementation's internal order rather than by the data.

Two points share a distance at the boundary when the distance takes few distinct values. Hamming
distance on a `b`-bit code can take only `b+1`; a real-valued distance takes as many values as the
floating-point representation allows. So the question this paper asks is narrow enough to be
answerable: **does the width of recall@k's identified set follow the coarseness of the distance
in the neighbourhood that matters, rather than the identity of the quantiser that induced it?**

That question has a practitioner's form. A team comparing a `32`-bit code with a `64`-bit code
reads the recall gap and decides. If the gap is smaller than the width the metric admits on that corpus,
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

The quantity is a statement about order, so the statistics that apply are the ones built for
agreement about ranks rather than about values: rank correlation for the association between the
tie group and the resolution {{c:kendall-1938,spearman-1904}}, and the association measures for
cross-classifications for the categorical version of the same question
{{c:goodman-kruskal-1954,cohen-kappa-1960}}. Those coefficients quantify agreement between two
readers of a ranking; a tie group is the case where the ranking itself does not determine which of
two readers saw the same objects.

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
that makes this safe — tail control for quadratic forms in independent variables
{{c:hanson-wright-1971,laurent-massart-2000}} — is checked, not assumed; the check is the pass
that compares two independently computed matrices, and the array and linear-algebra
implementations it runs on are the standard ones {{c:harris-numpy-2020,virtanen-scipy-2020}}.

**Interval language.** Every aggregate here is a mean over queries, and over seeds where the design
has them; a proportion is reported with a score interval rather than a bare point
{{c:wilson-1927,agresti-coull-1998}}, a difference between families uses the two-sample interval
{{c:newcombe-1998}}, and where the design is paired the interval is the matched one
{{c:efron-bootstrap-1979}}. Denominators are the number of queries the cell actually measured,
with the denominator stated in the text rather than implied; an empty denominator is printed as
`NOT RUN`, never as zero.

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

- **random-hyperplane Hamming** — `b` random hyperplanes, one bit each, the construction that
 descends from similarity estimation by rounding {{c:charikar-2002}} and from the p-stable
 families built on it {{c:datar-pstable-lsh-2004,andoni-indyk-2006,andoni-razenshteyn-2015}},
 with the kernelised and survey treatments of the same family
 {{c:kulis-kernel-lsh-2009,pauleve-lsh-2010}}; the distance takes `b+1` values;
- **product quantisation** — the descriptor split into sub-vectors, each replaced by one of many
 integer centroids {{c:jegou-douze-schmid-2011,ge-optimized-pq-2013,ge-optimized-pq-2014}}, with
 the additive and hash-addressed variants as the neighbouring design points
 {{c:babenko-additive-quant-2014,martinez-additive-quant-2016,matsui-pqtable-2018}}; the distance
 takes on the order of the number of distinct reconstructions;
- **scalar quantisation** — each component rounded onto a small set of integer levels, the
 one-dimensional case of the classical theory {{c:gray-vector-quantization-1984,
 gersho-gray-vq-book-1992,lloyd-least-squares-1982}}.

The result is a monotone ordering, and it is the same ordering whether the ordering is read off the
tie group or off the resolution. Median boundary tie group across the configurations runs from
{{n:A.hamming32.median_t}} at the coarsest Hamming budget to {{n:A.hamming256.median_t}} at the
finest, and the mean floor at the finely resolved families is {{n:A.pq32.floor}} and
{{n:A.pq64.floor}} against a Hamming floor that stays far below it. The families are not ordered by
which quantiser is "better": at equal bit budget product quantisation is a substantially more
accurate code than random hyperplanes, and that accuracy is not the variable. The variable is how
many distinct values the distance can take in the neighbourhood where the k-th point sits.

This matters most where the deployed systems are shortest. Billion-scale pipelines keep the number
of attainable distance values small on purpose — the multi-index and inverted-index constructions
search a product of coarse cells rather than every code
{{c:babenko-inverted-multi-index-2015,baranchuk-invindices-2018}} — and polysemous codes
deliberately reuse one short binary string for two purposes at once {{c:douze-polysemous-2016}}.
Those are the designs with the widest tie group, and they are also the designs whose published
recall is best, which is exactly why the width has to be reported beside it.

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

This is why the axis matters at all. Vector search became a general-purpose primitive once the
quantities being searched were learned embeddings rather than hand-written features — word vectors
{{c:mikolov-word2vec-2013}}, contextual encoders {{c:devlin-bert-2019,reimers-sbert-2019}}, dense
retrievers {{c:karpukhin-dpr-2020,khattab-colbert-2020}}, and the retrieval-augmented models built
on top of them {{c:lewis-rag-2020,guu-realm-2020,borgeaud-retro-2022}} — with benchmark suites that
score those embeddings by exactly this kind of neighbour retrieval {{c:mallen-mteb-2023}}. The
vision line runs the same course, from local descriptors and their aggregate encodings
{{c:lowe-sift-2004,lowe-iccv-1999,bay-surf-2006,dalal-hog-2005,nister-vocab-tree-2006,
philbin-large-vocabularies-2007,jegou-hamming-embedding-2008,perronnin-fisher-2010,
jegou-fisher-2012}} to learned ones {{c:he-resnet-2016,schroff-facenet-2015,
arandjelovic-netvlad-2016,radenovic-finetuning-2018}}, trained on the standard large corpora
{{c:deng-imagenet-2009,lin-coco-2014,kuznetsova-openimages-2020,thomee-yfcc100m-2016}}. Each of
those encoders emits a dense vector whose near neighbourhood the index must resolve, and on a short
code that neighbourhood is not resolved but tied.

## 6. The claim this study registered, and that it is refuted

This study registered the claim that recall@k on compact codes is undetermined, with three priors
{{c:nosek-preregistration-2018}}. Reporting the outcome plainly is part of the contribution,
because the refutation is what turned the study into a case study about an axis instead of a
validation paper about a metric — a registered prediction that is never read against its outcome
is not a preregistration but a wish {{c:munafo-manifesto-2017}}.

**The registered headline is refuted.** Two further families — product and scalar quantisation —
put the boundary tie group far outside the interval established for random hyperplanes, and at the
larger scale their floors are {{n:B.pq32.floor}}, {{n:B.pq64.floor}} and {{n:B.sq2.floor}}. A claim
that compact codes are undetermined cannot survive families whose median query has no tie at all.

**P1, that the tie group is invariant in corpus size, is refuted** by the scaling measurement: the
group grows with the corpus, with the fitted exponent rising as the code shortens.

**P2, that the driver is distance concentration rather than code-space occupancy, is supported in
its mechanism and wrong in its variable.** Occupancy was indeed never the driver. But the variable
that replaces it is not concentration in the abstract — it is the measured number of distinct
values the distance takes, which is what section 4 tests directly. The distinction is not verbal:
concentration is a statement about the distribution of distances at an order statistic
{{c:beyer-meaningful-nn-1999,aggarwal-cvn-2001,francois-fractional-2007}}, resolution is a
statement about how many values the *code* can produce, and the two come apart exactly in the
regime measured here.

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

**Approximate nearest-neighbour search.** The field runs from tree-based exact structures
{{c:bentley-1975}} through locality-sensitive hashing {{c:charikar-2002}} to graph-based indices
{{c:malkov-yashunin-2020}} and GPU systems {{c:johnson-douze-jegou-2021}}, with a vector-database
layer arriving more recently {{c:guo-manu-2022,pan-vector-db-survey-2024}}. This paper takes no
position on which index is faster; it asks what a recall number computed against any of them can
mean.

**Metric trees and space partitioning.** Exact similarity search begins with multidimensional
search trees {{c:bentley-1975}} and the spatial structures built beside them
{{c:guttman-r-tree-1984,beckmann-rstar-1990}}, continues in the metric-space line that needs no
coordinate system {{c:uhlenbeck-metric-tree-1991,katayama-sr-tree-1997,chavez-metric-spaces-2001,
hjaltason-sampling-2003}}, and admits approximate variants that trade a bounded error for pruning
{{c:ciaccia-pac-2000}}, with the practical question of which structure to choose documented
empirically {{c:muja-flann-2009,muja-flann-2014}}. The difference is one of subject: those works
measure a structure's cost and its error, and this paper measures whether the error figure they
report is *determined by the data* for the short codes they are retired in favour of.

**Locality-sensitive hashing and data-dependent hashing.** Random-hyperplane and p-stable families
{{c:charikar-2002,datar-pstable-lsh-2004}} and their data-dependent refinements
{{c:andoni-indyk-2006,andoni-razenshteyn-2015}}, including the kernelised form
{{c:kulis-kernel-lsh-2009}}, are the construction this paper's coarsest family instantiates, and
the comparison of hash families {{c:pauleve-lsh-2010}} fixes the parameterisation used here. The
same trade appears as approximate set membership with an explicit rate {{c:bloom-1970}}, as
min-wise permutation hashing in the set-similarity setting {{c:broder-minhash-1997}}, and at
streaming scale in production {{c:sundaram-lsh-tweets-2013}}; multi-index hashing
{{c:norouzi-mih-2014}} is its exact-search counterpart inside Hamming space. The difference: those
works state the approximation guarantee of the *index*, while this paper asks what the
*evaluation* of any such index can report when the distance itself cannot separate the returned
point from its neighbours.

**Learning compact and binary codes.** Iterative quantisation {{c:gong-itq-2011}}, kernel-based
supervised hashing {{c:liu-ksh-2012}},
deep hashing {{c:liong-deep-hashing-2015}} and spherical hashing {{c:heo-spherical-hashing-2012}}
all map a vector onto a short string, and the survey literature organises that space
{{c:wang-hashing-survey-2018}}. They supply the short-code regime in which the effect measured here
is largest, and none reports how much of the recall it publishes is determined by the data rather
than by the code.

**Quantisation beyond the product form.** The product and optimised-product designs
{{c:jegou-douze-schmid-2011,ge-optimized-pq-2013,ge-optimized-pq-2014}}, the additive and
residual families {{c:babenko-additive-quant-2014,martinez-additive-quant-2016}}, the
hash-addressed lookup tables {{c:matsui-pqtable-2018}}, the inverted multi-index and its revisiting
{{c:babenko-inverted-multi-index-2015,baranchuk-invindices-2018}}, polysemous codes
{{c:douze-polysemous-2016}} and the billion-scale deep-descriptor indexing
{{c:babenko-deep1b-2016}} are the reconstruct-and-scan systems whose distance distributions this
paper measures at {{n:A.configs}} configurations. The classical theory of vector quantisation, its
optimality conditions and its signal-compression treatment
{{c:gray-vector-quantization-1984,gersho-gray-vq-book-1992,lloyd-least-squares-1982}} supply the
machinery, with one change that is this paper's and not the literature's: reconstructions are
constrained to the data's own integer grid so that every distance is exact. That constraint is what
makes a tie measurable rather than a rounding artefact.

**Graph indexes and billion-scale systems.** Navigable small-world graphs and their hierarchical
form {{c:malkov-nsw-2014,malkov-yashunin-2020}}, spreading-out graphs {{c:fu-nsg-2019}},
approximate-neighbour graphs {{c:harwood-fanng-2016}} and their filtered variants
{{c:gollapudi-filtered-diskann-2023}} are what production systems run, as the comparative survey of
graph-based search documents {{c:wang-ann-graph-survey-2021}}. Around them sit the GPU and library
implementations {{c:johnson-douze-jegou-2021,douze-faiss-2024}}, the managed vector-database layer
{{c:guo-manu-2022,pan-vector-db-survey-2024}}, the challenge benchmark and the harness most figures
in this literature come from {{c:simhadri-bigann-2022,aumuller-ann-benchmarks-2017}}, and the
performance models and accelerators those systems are budgeted against
{{c:williams-roofline-2009,jouppi-tpu-2017}}.

**Evaluation methodology in information retrieval.** Effectiveness measurement and pooling have a
long critical literature {{c:manning-ir-book-2008}}, from the early large-scale evaluation
campaigns {{c:harman-trec1-1993,voorhees-qa-trec-2001}} through the analysis of what incomplete
judgements do to a reported number
{{c:buckley-incomplete-info-2004,buckley-pooling-bias-2007,aslam-savell-2003,aslam-pavlu-2003}},
the treatment of a ranking as the object being measured {{c:zobel-similarity-space-1998}} and the
inverted index underneath it {{c:zobel-inverted-files-2006}}; the claim-verification datasets and
late-interaction retrievers {{c:thorne-fever-2018,khattab-colbert-2020}} are the current downstream
consumers of that methodology. The difference: that literature studies *incomplete* judgements,
where the ground truth is a sample of a larger judged set, whereas the ambiguity measured here is
present in a *complete* exhaustive ground truth and is introduced by the representation rather than
by the sampling.

**Curse of dimensionality and concentration.** That distances concentrate as dimensionality grows
{{c:beyer-meaningful-nn-1999}}, that the choice of metric changes what concentration does to a
neighbourhood {{c:aggarwal-cvn-2001}}, and that the effect is visible in fractional-distance
behaviour {{c:francois-fractional-2007}} is the nearest relative of this paper's variable. The
embedding results {{c:johnson-lindenstrauss-1984,achlioptas-random-projections-2003}} and the
concentration machinery {{c:talagrand-isoperimetric-1994,hanson-wright-1971,laurent-massart-2000}}
explain why a distance at an order statistic carries `O(1)` mass rather than vanishing. The
measurement here is that concentration is not itself the predictor: the number of attainable values
is, and on a short code that is the coarser half of the pair.

**Statistics of a paired measurement.** Reporting an interval, comparing two systems on the same
queries, and checking that a comparison's assumptions hold are each a named problem with a named
instrument {{c:wilson-1927,agresti-coull-1998,newcombe-1998,efron-bootstrap-1979,mcnemar-1947,
mann-whitney-1947,shapiro-wilk-1965}}, and the agreement literature
{{c:cohen-kappa-1960,goodman-kruskal-1954,bland-altman-1986}} is where the question "which ground
truth did you compare against" belongs. This paper uses those instruments rather than inventing a
statistic, and reports the minimum effect its design can detect so that a null is read as a null.

**Reproducibility and the standing of a negative result.** A result that contradicts a registered
prior is the status the methodology literature treats as both the most fragile and the most
valuable {{c:ioannidis-why-false-2005,nosek-preregistration-2018,munafo-manifesto-2017,
peng-reproducible-2011}}. The practices this package follows — one command, pinned inputs with
digests, artefacts regenerated and byte-compared
{{c:wilkinson-fair-2016,sandve-ten-rules-2013,stodden-enhancing-2016}} — are what let a reader
check the refutation instead of taking it on trust.

## 8. Threats to validity, and why the result still stands

**One corpus.** Every number is on `sift-128-euclidean`. The larger scale is fifty times as many
descriptors from the same source, not a second dataset, so the axis is shown to survive scale and
not shown to survive a change of data. This is the study's binding limitation and it is why the
contribution level is a case study.

**Configurations, not cells.** The correlation is computed over seed-level cells; three seeds of one
configuration are one configuration measured thrice. The program prints both counts and the paper
quotes the configuration count as evidence.

**Sensitivity.** The central claim is a correlation over {{n:A.n_cells}} seed-level cells. The
smallest correlation a design of this size could have detected, at conventional two-sided
significance and power, is {{n:A.mde}}; the measured `r = {{n:A.r}}` is far above it. That matters
for reading section 6: the refutations there rest on differences larger than the design's own
sensitivity, so they are evidence against the registered priors rather than an absence of one.

**Resolution is measured, not derived.** No closed form predicts the number of distinct distance
values a quantiser induces, so the axis is an empirical predictor. That is enough to falsify the
"family" explanation and to order the families, and it is not a theory of the axis.

Why the result stands anyway: the refutation of the registered claim does not depend on any of the
limitations — product and scalar quantisation tie barely on this corpus, and that contradicts the
registered generalisation whatever else is true. And the axis is the object that survives: it
explains the presence *and* the absence of the effect with one measured quantity, where the
registered claim explained only its presence.

## 9. Reproduction

`./reproduce.sh` reproduces tier A — the mechanism table, both endpoint controls and this
manuscript — from the committed fixture, with numpy alone and no network. The
{{n:B.corpus.n}}-descriptor numbers in section 5 are **tier B, the opt-in tier**: they are
reproduced by `./reproduce.sh full`, which needs the corpus fetched by `fetch_corpus.sh` and `h5py`, and which
reports `NOT RUN` rather than failing when either is absent. A reader who runs only the default
command therefore reproduces every tier-A number and is told, on the spot, that the tier-B ones were
not recomputed — rather than being shown a green verdict over a number that was never computed. The mechanism table is regenerated twice
and byte-compared, so a number that moves between two runs fails the build, and a program reads the
artefact back to test the claims this paper makes about it. The stack is the standard scientific
Python one — array and linear-algebra routines {{c:harris-numpy-2020,virtanen-scipy-2020}}, the
tabulation {{c:mckinney-pandas-2010}} and the figures {{c:hunter-matplotlib-2007}} — and the
bibliography is resolved, not typed: every reference in this paper was fetched from a registry by
a program, and a reference that does not resolve stops the manuscript from being generated at all.

## References

{{refs}}
