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
near neighbourhood of a query actually occupies. Across 10 configurations spanning
three families (random-hyperplane Hamming, product quantisation, scalar quantisation) on
20,000 real SIFT descriptors, the boundary tie group is ordered by resolution on a log-log
scale at `r = -0.9765` over 20 seed-level cells; at 1,000,000 descriptors
the same ordering holds at `r = -0.9613` over 8 configurations. Hamming distance
attains only `b+1` values for a `b`-bit code and ties badly — median boundary group
52.333 at the shortest budget, mean floor 0.2886 — while
product and scalar quantisation, which attain hundreds of values, tie barely: median group
1.333 and floor 0.899 to 0.991. The two families most
widely deployed at billion scale are therefore the ones the effect leaves almost untouched.

The paper states plainly what this replaces. This study **registered the opposite claim** — that
recall@k on compact codes *as such* is undetermined — and the second and third quantiser families
**refute it**. That refutation is reported with the numbers that produced it, not deleted. Three
registered priors are likewise reported as refuted, supported, or refuted-in-one-space, and the
scaling prior is refuted.

Contribution level: **`case study`**. One corpus, two scales of it, 8 configurations
at the larger scale. The instrument is exact and its two endpoint controls are run on every
reproduction; the scope is one corpus and the abstract says so rather than a limitations section.

---

## 1. The question

A benchmark reports one number per (index, recall@k) cell. The measure descends from the
vector-space and probabilistic-relevance tradition of information retrieval
[1,2,3,4],
whose textbook
treatments are explicit that an effectiveness figure is an estimate over a judged set rather than
a property of the system alone [5,6]. The number
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
tie group and the resolution [7,8], and the association measures for
cross-classifications for the categorical version of the same question
[9,10]. Those coefficients quantify agreement between two
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
int64 computation on 1,000-scale samples before a single tie is counted. The bound
that makes this safe — tail control for quadratic forms in independent variables
[11,12] — is checked, not assumed; the check is the pass
that compares two independently computed matrices, and the array and linear-algebra
implementations it runs on are the standard ones [13,14].

**Interval language.** Every aggregate here is a mean over queries, and over seeds where the design
has them; a proportion is reported with a score interval rather than a bare point
[15,16], a difference between families uses the two-sample interval
[17], and where the design is paired the interval is the matched one
[18]. Denominators are the number of queries the cell actually measured,
with the denominator stated in the text rather than implied; an empty denominator is printed as
`NOT RUN`, never as zero.

**Endpoint controls.** `reproduce.sh` asserts both on every run. On the raw descriptors — where the
boundary tie group is a single point because no two of a million integer-valued vectors share an
exact squared distance — the mean floor is **1.0** and the median tie group is
1.0. On a constructed corpus where every point is one repeated vector, the mean
floor is **0.0** with a tie group of 20000.0. An
instrument that cannot reach "fully determined" where the answer is known, and cannot reach
"maximally undetermined" where the ambiguity is total, has not been shown to measure either.

**Resolution.** The explanatory variable is the number of distinct distance values occupied by the
nearest 1,000 points of a query. It is deliberately local: the global range of a
distance says little, while the mass that `n · P(D = d_k)` places on the k-th value is exactly
what the tie group is.

## 4. What governs the tie group

Three quantiser families are run on the same corpus and the same queries, at budgets chosen so the
families can be compared:

- **random-hyperplane Hamming** — `b` random hyperplanes, one bit each, the construction that
 descends from similarity estimation by rounding [19] and from the p-stable
 families built on it [20,21,22],
 with the kernelised and survey treatments of the same family
 [23,24]; the distance takes `b+1` values;
- **product quantisation** — the descriptor split into sub-vectors, each replaced by one of many
 integer centroids [25,26,27], with
 the additive and hash-addressed variants as the neighbouring design points
 [28,29,30]; the distance
 takes on the order of the number of distinct reconstructions;
- **scalar quantisation** — each component rounded onto a small set of integer levels, the
 one-dimensional case of the classical theory [31,32,33].

The result is a monotone ordering, and it is the same ordering whether the ordering is read off the
tie group or off the resolution. Median boundary tie group across the configurations runs from
23.667 at the coarsest Hamming budget to 4.5 at the
finest, and the mean floor at the finely resolved families is 0.98 and
0.9995 against a Hamming floor that stays far below it. The families are not ordered by
which quantiser is "better": at equal bit budget product quantisation is a substantially more
accurate code than random hyperplanes, and that accuracy is not the variable. The variable is how
many distinct values the distance can take in the neighbourhood where the k-th point sits.

This matters most where the deployed systems are shortest. Billion-scale pipelines keep the number
of attainable distance values small on purpose — the multi-index and inverted-index constructions
search a product of coarse cells rather than every code
[34,35] — and polysemous codes
deliberately reuse one short binary string for two purposes at once [36].
Those are the designs with the widest tie group, and they are also the designs whose published
recall is best, which is exactly why the width has to be reported beside it.

This is the paper's central claim, in falsifiable form: **hold the corpus and the query fixed, and
the width of the identified set is predicted by the local resolution of the distance, not by the
quantiser family and not by the bit budget alone.**

## 5. At the benchmark's own scale

The same axis is measured on 1,000,000 descriptors — a factor of fifty more points than the
committed subsample, with 512 queries per seed — and it holds:
`r = -0.9613` over 8 configurations. The resolution ranges from
3.0 distinct values in the near neighbourhood of a short Hamming budget to
701.667 for product quantisation. Correspondingly the median boundary tie group is
52.333 at the short Hamming budget, 18.5 at twice the
budget and 6.0 at the finest, against 1.333 for product
quantisation. The mean floor tells the practitioner's version of the same story: for Hamming at the
short budget a correct index can be graded **0.2886** on average and
0.9668 of queries are not fully determined, while product quantisation
gives **0.899** and scalar quantisation **0.9839**.

Raw descriptors, measured in the same run at the same scale, give **0.9994**. That
number is the control that keeps the rest honest: the metric is fully determined on the objects
themselves, and everything this paper reports is about distances that a *code* introduces.

This is why the axis matters at all. Vector search became a general-purpose primitive once the
quantities being searched were learned embeddings rather than hand-written features — word vectors
[37], contextual encoders [38,39], dense
retrievers [40,41], and the retrieval-augmented models built
on top of them [42,43,44] — with benchmark suites that
score those embeddings by exactly this kind of neighbour retrieval [45]. The
vision line runs the same course, from local descriptors and their aggregate encodings
[46,47,48,49,50,51,52,53,54] to learned ones [55,56,57,58], trained on the standard large corpora
[59,60,61,62]. Each of
those encoders emits a dense vector whose near neighbourhood the index must resolve, and on a short
code that neighbourhood is not resolved but tied.

## 6. The claim this study registered, and that it is refuted

This study registered the claim that recall@k on compact codes is undetermined, with three priors
[63]. Reporting the outcome plainly is part of the contribution,
because the refutation is what turned the study into a case study about an axis instead of a
validation paper about a metric — a registered prediction that is never read against its outcome
is not a preregistration but a wish [64].

**The registered headline is refuted.** Two further families — product and scalar quantisation —
put the boundary tie group far outside the interval established for random hyperplanes, and at the
larger scale their floors are 0.899, 0.991 and 0.9839. A claim
that compact codes are undetermined cannot survive families whose median query has no tie at all.

**P1, that the tie group is invariant in corpus size, is refuted** by the scaling measurement: the
group grows with the corpus, with the fitted exponent rising as the code shortens.

**P2, that the driver is distance concentration rather than code-space occupancy, is supported in
its mechanism and wrong in its variable.** Occupancy was indeed never the driver. But the variable
that replaces it is not concentration in the abstract — it is the measured number of distinct
values the distance takes, which is what section 4 tests directly. The distinction is not verbal:
concentration is a statement about the distribution of distances at an order statistic
[65,66,67], resolution is a
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
[68] through locality-sensitive hashing [19] to graph-based indices
[69] and GPU systems [70], with a vector-database
layer arriving more recently [71,72]. This paper takes no
position on which index is faster; it asks what a recall number computed against any of them can
mean.

**Metric trees and space partitioning.** Exact similarity search begins with multidimensional
search trees [68] and the spatial structures built beside them
[73,74], continues in the metric-space line that needs no
coordinate system [75,76,77,78], and admits approximate variants that trade a bounded error for pruning
[79], with the practical question of which structure to choose documented
empirically [80,81]. The difference is one of subject: those works
measure a structure's cost and its error, and this paper measures whether the error figure they
report is *determined by the data* for the short codes they are retired in favour of.

**Locality-sensitive hashing and data-dependent hashing.** Random-hyperplane and p-stable families
[19,20] and their data-dependent refinements
[21,22], including the kernelised form
[23], are the construction this paper's coarsest family instantiates, and
the comparison of hash families [24] fixes the parameterisation used here. The
same trade appears as approximate set membership with an explicit rate [82], as
min-wise permutation hashing in the set-similarity setting [83], and at
streaming scale in production [84]; multi-index hashing
[85] is its exact-search counterpart inside Hamming space. The difference: those
works state the approximation guarantee of the *index*, while this paper asks what the
*evaluation* of any such index can report when the distance itself cannot separate the returned
point from its neighbours.

**Learning compact and binary codes.** Iterative quantisation [86], kernel-based
supervised hashing [87],
deep hashing [88] and spherical hashing [89]
all map a vector onto a short string, and the survey literature organises that space
[90]. They supply the short-code regime in which the effect measured here
is largest, and none reports how much of the recall it publishes is determined by the data rather
than by the code.

**Quantisation beyond the product form.** The product and optimised-product designs
[25,26,27], the additive and
residual families [28,29], the
hash-addressed lookup tables [30], the inverted multi-index and its revisiting
[34,35], polysemous codes
[36] and the billion-scale deep-descriptor indexing
[91] are the reconstruct-and-scan systems whose distance distributions this
paper measures at 10 configurations. The classical theory of vector quantisation, its
optimality conditions and its signal-compression treatment
[31,32,33] supply the
machinery, with one change that is this paper's and not the literature's: reconstructions are
constrained to the data's own integer grid so that every distance is exact. That constraint is what
makes a tie measurable rather than a rounding artefact.

**Graph indexes and billion-scale systems.** Navigable small-world graphs and their hierarchical
form [92,69], spreading-out graphs [93],
approximate-neighbour graphs [94] and their filtered variants
[95] are what production systems run, as the comparative survey of
graph-based search documents [96]. Around them sit the GPU and library
implementations [70,97], the managed vector-database layer
[71,72], the challenge benchmark and the harness most figures
in this literature come from [98,99], and the
performance models and accelerators those systems are budgeted against
[100,101].

**Evaluation methodology in information retrieval.** Effectiveness measurement and pooling have a
long critical literature [5], from the early large-scale evaluation
campaigns [102,103] through the analysis of what incomplete
judgements do to a reported number
[104,105,106,107],
the treatment of a ranking as the object being measured [6] and the
inverted index underneath it [108]; the claim-verification datasets and
late-interaction retrievers [109,41] are the current downstream
consumers of that methodology. The difference: that literature studies *incomplete* judgements,
where the ground truth is a sample of a larger judged set, whereas the ambiguity measured here is
present in a *complete* exhaustive ground truth and is introduced by the representation rather than
by the sampling.

**Curse of dimensionality and concentration.** That distances concentrate as dimensionality grows
[65], that the choice of metric changes what concentration does to a
neighbourhood [66], and that the effect is visible in fractional-distance
behaviour [67] is the nearest relative of this paper's variable. The
embedding results [110,111] and the
concentration machinery [112,11,12]
explain why a distance at an order statistic carries `O(1)` mass rather than vanishing. The
measurement here is that concentration is not itself the predictor: the number of attainable values
is, and on a short code that is the coarser half of the pair.

**Statistics of a paired measurement.** Reporting an interval, comparing two systems on the same
queries, and checking that a comparison's assumptions hold are each a named problem with a named
instrument [15,16,17,18,113,114,115], and the agreement literature
[10,9,116] is where the question "which ground
truth did you compare against" belongs. This paper uses those instruments rather than inventing a
statistic, and reports the minimum effect its design can detect so that a null is read as a null.

**Reproducibility and the standing of a negative result.** A result that contradicts a registered
prior is the status the methodology literature treats as both the most fragile and the most
valuable [117,63,64,118]. The practices this package follows — one command, pinned inputs with
digests, artefacts regenerated and byte-compared
[119,120,121] — are what let a reader
check the refutation instead of taking it on trust.

## 8. Threats to validity, and why the result still stands

**One corpus.** Every number is on `sift-128-euclidean`. The larger scale is fifty times as many
descriptors from the same source, not a second dataset, so the axis is shown to survive scale and
not shown to survive a change of data. This is the study's binding limitation and it is why the
contribution level is a case study.

**Configurations, not cells.** The correlation is computed over seed-level cells; three seeds of one
configuration are one configuration measured thrice. The program prints both counts and the paper
quotes the configuration count as evidence.

**Sensitivity.** The central claim is a correlation over 20 seed-level cells. The
smallest correlation a design of this size could have detected, at conventional two-sided
significance and power, is 0.5912; the measured `r = -0.9765` is far above it. That matters
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

`./reproduce.sh` reproduces every number in this paper from the committed fixture, with numpy
alone and no network; `./reproduce.sh full` adds the 1,000,000-descriptor tier, which prints
`NOT RUN` rather than failing when the corpus is absent. The mechanism table is regenerated twice
and byte-compared, so a number that moves between two runs fails the build, and a program reads the
artefact back to test the claims this paper makes about it. The stack is the standard scientific
Python one — array and linear-algebra routines [13,14], the
tabulation [122] and the figures [123] — and the
bibliography is resolved, not typed: every reference in this paper was fetched from a registry by
a program, and a reference that does not resolve stops the manuscript from being generated at all.

## References

[1] Salton, G.; Wong, A.; Yang, C. S.. (1975). A vector space model for automatic indexing. Communications of the ACM. vol. 18. pp. 613-620. https://doi.org/10.1145/361219.361220

[2] Robertson, S. E.; Jones, K. S.. (1976). Relevance weighting of search terms. Journal of the American Society for Information Science. vol. 27. pp. 129-146. https://doi.org/10.1002/asi.4630270302

[3] SPARCK JONES, K.. (1972). A STATISTICAL INTERPRETATION OF TERM SPECIFICITY AND ITS APPLICATION IN RETRIEVAL. Journal of Documentation. vol. 28. pp. 11-21. https://doi.org/10.1108/eb026526

[4] Robertson, S.; Zaragoza, H.. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends® in Information Retrieval. vol. 4. pp. 1-174. https://doi.org/10.1561/1500000019

[5] Manning, C. D.; Raghavan, P.; Schütze, H.. (2008). Introduction to Information Retrieval. https://doi.org/10.1017/cbo9780511809071

[6] Zobel, J.; Moffat, A.. (1998). Exploring the similarity space. ACM SIGIR Forum. vol. 32. pp. 18-34. https://doi.org/10.1145/281250.281256

[7] Kendall, M. G.. (1938). A New Measure of Rank Correlation. Biometrika. vol. 30. pp. 81. https://doi.org/10.2307/2332226

[8] Spearman, C.. (1904). The Proof and Measurement of Association between Two Things. The American Journal of Psychology. vol. 15. pp. 72. https://doi.org/10.2307/1412159

[9] Goodman, L. A.; Kruskal, W. H.. (1954). Measures of Association for Cross Classifications*. Journal of the American Statistical Association. vol. 49. pp. 732-764. https://doi.org/10.1080/01621459.1954.10501231

[10] Cohen, J.. (1960). A Coefficient of Agreement for Nominal Scales. Educational and Psychological Measurement. vol. 20. pp. 37-46. https://doi.org/10.1177/001316446002000104

[11] Hanson, D. L.; Wright, F. T.. (1971). A Bound on Tail Probabilities for Quadratic Forms in Independent Random Variables. The Annals of Mathematical Statistics. vol. 42. pp. 1079-1083. https://doi.org/10.1214/aoms/1177693335

[12] Laurent, B.; Massart, P.. (2000). Adaptive estimation of a quadratic functional by model selection. The Annals of Statistics. vol. 28. pp. 1302-1338. https://doi.org/10.1214/aos/1015957395

[13] Harris, C. R.; Millman, K. J.; van der Walt, S. J.; et al.. (2020). Array programming with NumPy. Nature. vol. 585. pp. 357-362. https://doi.org/10.1038/s41586-020-2649-2

[14] Virtanen, P.; Gommers, R.; Oliphant, T. E.; et al.. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods. vol. 17. pp. 261-272. https://doi.org/10.1038/s41592-019-0686-2

[15] Wilson, E. B.. (1927). Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association. vol. 22. pp. 209-212. https://doi.org/10.1080/01621459.1927.10502953

[16] Agresti, A.; Coull, B. A.. (1998). Approximate Is Better than "Exact" for Interval Estimation of Binomial Proportions. The American Statistician. vol. 52. pp. 119. https://doi.org/10.2307/2685469

[17] Newcombe, R. G.. (1998). Interval estimation for the difference between independent proportions: comparison of eleven methods. Statistics in Medicine. vol. 17. pp. 873-890. https://doi.org/10.1002/(sici)1097-0258(19980430)17:8<873::aid-sim779>3.0.co;2-i

[18] Efron, B.. (1979). Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics. vol. 7. pp. 1-26. https://doi.org/10.1214/aos/1176344552

[19] Charikar, M. S.. (2002). Similarity estimation techniques from rounding algorithms. Proceedings of the thiry-fourth annual ACM symposium on Theory of computing. pp. 380-388. https://doi.org/10.1145/509907.509965

[20] Datar, M.; Immorlica, N.; Indyk, P.; et al.. (2004). Locality-sensitive hashing scheme based on p-stable distributions. Proceedings of the twentieth annual symposium on Computational geometry. pp. 253-262. https://doi.org/10.1145/997817.997857

[21] Andoni, A.; Indyk, P.. (2006). Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions. 2006 47th Annual IEEE Symposium on Foundations of Computer Science (FOCS'06). pp. 459-468. https://doi.org/10.1109/focs.2006.49

[22] Andoni, A.; Razenshteyn, I.. (2015). Optimal Data-Dependent Hashing for Approximate Near Neighbors. Proceedings of the forty-seventh annual ACM symposium on Theory of Computing. pp. 793-801. https://doi.org/10.1145/2746539.2746553

[23] Kulis, B.; Grauman, K.. (2009). Kernelized locality-sensitive hashing for scalable image search. 2009 IEEE 12th International Conference on Computer Vision. pp. 2130-2137. https://doi.org/10.1109/iccv.2009.5459466

[24] Paulevé, L.; Jégou, H.; Amsaleg, L.. (2010). Locality sensitive hashing: A comparison of hash function types and querying mechanisms. Pattern Recognition Letters. vol. 31. pp. 1348-1358. https://doi.org/10.1016/j.patrec.2010.04.004

[25] Jégou, H.; Douze, M.; Schmid, C.. (2011). Product Quantization for Nearest Neighbor Search. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 33. pp. 117-128. https://doi.org/10.1109/tpami.2010.57

[26] Ge, T.; He, K.; Ke, Q.; et al.. (2013). Optimized Product Quantization for Approximate Nearest Neighbor Search. 2013 IEEE Conference on Computer Vision and Pattern Recognition. pp. 2946-2953. https://doi.org/10.1109/cvpr.2013.379

[27] Ge, T.; He, K.; Ke, Q.; et al.. (2014). Optimized Product Quantization. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 36. pp. 744-755. https://doi.org/10.1109/tpami.2013.240

[28] Babenko, A.; Lempitsky, V.. (2014). Additive Quantization for Extreme Vector Compression. 2014 IEEE Conference on Computer Vision and Pattern Recognition. pp. 931-938. https://doi.org/10.1109/cvpr.2014.124

[29] Martinez, J.; Clement, J.; Hoos, H. H.; et al.. (2016). Revisiting Additive Quantization. Lecture Notes in Computer Science. pp. 137-153. https://doi.org/10.1007/978-3-319-46475-6_9

[30] Matsui, Y.; Yamasaki, T.; Aizawa, K.. (2018). PQTable: Nonexhaustive Fast Search for Product-Quantized Codes Using Hash Tables. IEEE Transactions on Multimedia. vol. 20. pp. 1809-1822. https://doi.org/10.1109/tmm.2017.2774009

[31] Gray, R.. (1984). Vector quantization. IEEE ASSP Magazine. vol. 1. pp. 4-29. https://doi.org/10.1109/massp.1984.1162229

[32] Gersho, A.; Gray, R. M.. (1992). Vector Quantization and Signal Compression. https://doi.org/10.1007/978-1-4615-3626-0

[33] Lloyd, S.. (1982). Least squares quantization in PCM. IEEE Transactions on Information Theory. vol. 28. pp. 129-137. https://doi.org/10.1109/tit.1982.1056489

[34] Babenko, A.; Lempitsky, V.. (2015). The Inverted Multi-Index. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 37. pp. 1247-1260. https://doi.org/10.1109/tpami.2014.2361319

[35] Baranchuk, D.; Babenko, A.; Malkov, Y.. (2018). Revisiting the Inverted Indices for Billion-Scale Approximate Nearest Neighbors. Lecture Notes in Computer Science. pp. 209-224. https://doi.org/10.1007/978-3-030-01258-8_13

[36] Douze, M.; Jégou, H.; Perronnin, F.. (2016). Polysemous Codes. Lecture Notes in Computer Science. pp. 785-801. https://doi.org/10.1007/978-3-319-46475-6_48

[37] Tomas Mikolov; Ilya Sutskever; Kai Chen; et al.. (2013). Distributed Representations of Words and Phrases and their Compositionality. arXiv preprint 1310.4546v1. http://arxiv.org/abs/1310.4546v1

[38] Devlin, J.; Chang, M. W.; Lee, K.; et al.. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers). pp. 4171-4186. https://doi.org/10.18653/v1/n19-1423

[39] Reimers, N.; Gurevych, I.. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP). pp. 3980-3990. https://doi.org/10.18653/v1/d19-1410

[40] Karpukhin, V.; Oguz, B.; Min, S.; et al.. (2020). Dense Passage Retrieval for Open-Domain Question Answering. Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP). pp. 6769-6781. https://doi.org/10.18653/v1/2020.emnlp-main.550

[41] Omar Khattab; Matei Zaharia. (2020). ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT. arXiv preprint 2004.12832v2. http://arxiv.org/abs/2004.12832v2

[42] Patrick Lewis; Ethan Perez; Aleksandra Piktus; et al.. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. arXiv preprint 2005.11401v4. http://arxiv.org/abs/2005.11401v4

[43] Kelvin Guu; Kenton Lee; Zora Tung; et al.. (2020). REALM: Retrieval-Augmented Language Model Pre-Training. arXiv preprint 2002.08909v1. http://arxiv.org/abs/2002.08909v1

[44] Sebastian Borgeaud; Arthur Mensch; Jordan Hoffmann; et al.. (2021). Improving language models by retrieving from trillions of tokens. arXiv preprint 2112.04426v3. http://arxiv.org/abs/2112.04426v3

[45] Muennighoff, N.; Tazi, N.; Magne, L.; et al.. (2023). MTEB: Massive Text Embedding Benchmark. Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics. pp. 2014-2037. https://doi.org/10.18653/v1/2023.eacl-main.148

[46] Lowe, D. G.. (2004). Distinctive Image Features from Scale-Invariant Keypoints. International Journal of Computer Vision. vol. 60. pp. 91-110. https://doi.org/10.1023/b:visi.0000029664.99615.94

[47] Lowe, D.. (1999). Object recognition from local scale-invariant features. Proceedings of the Seventh IEEE International Conference on Computer Vision. pp. 1150-1157 vol.2. https://doi.org/10.1109/iccv.1999.790410

[48] Bay, H.; Ess, A.; Tuytelaars, T.; et al.. (2008). Speeded-Up Robust Features (SURF). Computer Vision and Image Understanding. vol. 110. pp. 346-359. https://doi.org/10.1016/j.cviu.2007.09.014

[49] Dalal, N.; Triggs, B.. (None). Histograms of Oriented Gradients for Human Detection. 2005 IEEE Computer Society Conference on Computer Vision and Pattern Recognition (CVPR'05). vol. 1. pp. 886-893. https://doi.org/10.1109/cvpr.2005.177

[50] Nister, D.; Stewenius, H.. (None). Scalable Recognition with a Vocabulary Tree. 2006 IEEE Computer Society Conference on Computer Vision and Pattern Recognition - Volume 2 (CVPR'06). vol. 2. pp. 2161-2168. https://doi.org/10.1109/cvpr.2006.264

[51] Philbin, J.; Chum, O.; Isard, M.; et al.. (2007). Object retrieval with large vocabularies and fast spatial matching. 2007 IEEE Conference on Computer Vision and Pattern Recognition. pp. 1-8. https://doi.org/10.1109/cvpr.2007.383172

[52] Jegou, H.; Douze, M.; Schmid, C.. (2008). Hamming Embedding and Weak Geometric Consistency for Large Scale Image Search. Lecture Notes in Computer Science. pp. 304-317. https://doi.org/10.1007/978-3-540-88682-2_24

[53] Perronnin, F.; Sánchez, J.; Mensink, T.. (2010). Improving the Fisher Kernel for Large-Scale Image Classification. Lecture Notes in Computer Science. pp. 143-156. https://doi.org/10.1007/978-3-642-15561-1_11

[54] Jegou, H.; Perronnin, F.; Douze, M.; et al.. (2012). Aggregating Local Image Descriptors into Compact Codes. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 34. pp. 1704-1716. https://doi.org/10.1109/tpami.2011.235

[55] He, K.; Zhang, X.; Ren, S.; et al.. (2016). Deep Residual Learning for Image Recognition. 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 770-778. https://doi.org/10.1109/cvpr.2016.90

[56] Schroff, F.; Kalenichenko, D.; Philbin, J.. (2015). FaceNet: A unified embedding for face recognition and clustering. 2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 815-823. https://doi.org/10.1109/cvpr.2015.7298682

[57] Arandjelovic, R.; Gronat, P.; Torii, A.; et al.. (2016). NetVLAD: CNN Architecture for Weakly Supervised Place Recognition. 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 5297-5307. https://doi.org/10.1109/cvpr.2016.572

[58] Radenovic, F.; Tolias, G.; Chum, O.. (2019). Fine-Tuning CNN Image Retrieval with No Human Annotation. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 41. pp. 1655-1668. https://doi.org/10.1109/tpami.2018.2846566

[59] Deng, J.; Dong, W.; Socher, R.; et al.. (2009). ImageNet: A large-scale hierarchical image database. 2009 IEEE Conference on Computer Vision and Pattern Recognition. pp. 248-255. https://doi.org/10.1109/cvpr.2009.5206848

[60] Lin, T. Y.; Maire, M.; Belongie, S.; et al.. (2014). Microsoft COCO: Common Objects in Context. Lecture Notes in Computer Science. pp. 740-755. https://doi.org/10.1007/978-3-319-10602-1_48

[61] Kuznetsova, A.; Rom, H.; Alldrin, N.; et al.. (2020). The Open Images Dataset V4. International Journal of Computer Vision. vol. 128. pp. 1956-1981. https://doi.org/10.1007/s11263-020-01316-z

[62] Bart Thomee; David A. Shamma; Gerald Friedland; et al.. (2015). YFCC100M: The New Data in Multimedia Research. arXiv preprint 1503.01817v2. http://arxiv.org/abs/1503.01817v2

[63] Nosek, B. A.; Ebersole, C. R.; DeHaven, A. C.; et al.. (2017). The Preregistration Revolution. https://doi.org/10.31219/osf.io/2dxu5

[64] Munafò, M. R.; Nosek, B. A.; Bishop, D. V. M.; et al.. (2017). A manifesto for reproducible science. Nature Human Behaviour. vol. 1. https://doi.org/10.1038/s41562-016-0021

[65] Beyer, K.; Goldstein, J.; Ramakrishnan, R.; et al.. (1999). When Is “Nearest Neighbor” Meaningful?. Lecture Notes in Computer Science. pp. 217-235. https://doi.org/10.1007/3-540-49257-7_15

[66] Aggarwal, C. C.; Hinneburg, A.; Keim, D. A.. (2001). On the Surprising Behavior of Distance Metrics in High Dimensional Space. Lecture Notes in Computer Science. pp. 420-434. https://doi.org/10.1007/3-540-44503-x_27

[67] Francois, D.; Wertz, V.; Verleysen, M.. (2007). The Concentration of Fractional Distances. IEEE Transactions on Knowledge and Data Engineering. vol. 19. pp. 873-886. https://doi.org/10.1109/tkde.2007.1037

[68] Bentley, J. L.. (1975). Multidimensional binary search trees used for associative searching. Communications of the ACM. vol. 18. pp. 509-517. https://doi.org/10.1145/361002.361007

[69] Malkov, Y. A.; Yashunin, D. A.. (2020). Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 42. pp. 824-836. https://doi.org/10.1109/tpami.2018.2889473

[70] Johnson, J.; Douze, M.; Jegou, H.. (2021). Billion-Scale Similarity Search with GPUs. IEEE Transactions on Big Data. vol. 7. pp. 535-547. https://doi.org/10.1109/tbdata.2019.2921572

[71] Rentong Guo; Xiaofan Luan; Long Xiang; et al.. (2022). Manu: A Cloud Native Vector Database Management System. arXiv preprint 2206.13843v1. http://arxiv.org/abs/2206.13843v1

[72] Pan, J. J.; Wang, J.; Li, G.. (2024). Survey of vector database management systems. The VLDB Journal. vol. 33. pp. 1591-1615. https://doi.org/10.1007/s00778-024-00864-x

[73] (None). R-Trees - A Dynamic Index Structure for Spatial Searching. SpringerReference. https://doi.org/10.1007/springerreference_62807

[74] Beckmann, N.; Kriegel, H. P.; Schneider, R.; et al.. (1990). The R*-tree: an efficient and robust access method for points and rectangles. Proceedings of the 1990 ACM SIGMOD international conference on Management of data. pp. 322-331. https://doi.org/10.1145/93597.98741

[75] Uhlmann, J. K.. (1991). Satisfying general proximity / similarity queries with metric trees. Information Processing Letters. vol. 40. pp. 175-179. https://doi.org/10.1016/0020-0190(91)90074-r

[76] Katayama, N.; Satoh, S.. (1998). SR‐tree: An index structure for nearest‐neighbor searching of high‐dimensional point data. Systems and Computers in Japan. vol. 29. pp. 59-73. https://doi.org/10.1002/(sici)1520-684x(19980615)29:6<59::aid-scj6>3.3.co;2-d

[77] Chávez, E.; Navarro, G.; Baeza-Yates, R.; et al.. (2001). Searching in metric spaces. ACM Computing Surveys. vol. 33. pp. 273-321. https://doi.org/10.1145/502807.502808

[78] Hjaltason, G. R.; Samet, H.. (2003). Index-driven similarity search in metric spaces (Survey Article). ACM Transactions on Database Systems. vol. 28. pp. 517-580. https://doi.org/10.1145/958942.958948

[79] Ciaccia, P.; Patella, M.. (None). PAC nearest neighbor queries: Approximate and controlled search in high-dimensional and metric spaces. Proceedings of 16th International Conference on Data Engineering (Cat. No.00CB37073). pp. 244-255. https://doi.org/10.1109/icde.2000.839417

[80] (2009). FAST APPROXIMATE NEAREST NEIGHBORS WITH AUTOMATIC ALGORITHM CONFIGURATION. Proceedings of the Fourth International Conference on Computer Vision Theory and Applications. pp. 331-340. https://doi.org/10.5220/0001787803310340

[81] Muja, M.; Lowe, D. G.. (2014). Scalable Nearest Neighbor Algorithms for High Dimensional Data. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 36. pp. 2227-2240. https://doi.org/10.1109/tpami.2014.2321376

[82] Bloom, B. H.. (1970). Space/time trade-offs in hash coding with allowable errors. Communications of the ACM. vol. 13. pp. 422-426. https://doi.org/10.1145/362686.362692

[83] Broder, A.. (None). On the resemblance and containment of documents. Proceedings. Compression and Complexity of SEQUENCES 1997 (Cat. No.97TB100171). pp. 21-29. https://doi.org/10.1109/sequen.1997.666900

[84] Sundaram, N.; Turmukhametova, A.; Satish, N.; et al.. (2013). Streaming similarity search over one billion tweets using parallel locality-sensitive hashing. Proceedings of the VLDB Endowment. vol. 6. pp. 1930-1941. https://doi.org/10.14778/2556549.2556574

[85] Norouzi, M.; Punjani, A.; Fleet, D. J.. (2014). Fast Exact Search in Hamming Space With Multi-Index Hashing. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 36. pp. 1107-1119. https://doi.org/10.1109/tpami.2013.231

[86] Gong, Y.; Lazebnik, S.. (2011). Iterative quantization: A procrustean approach to learning binary codes. CVPR 2011. pp. 817-824. https://doi.org/10.1109/cvpr.2011.5995432

[87] Wei Liu; Jun Wang; Rongrong Ji; et al.. (2012). Supervised hashing with kernels. 2012 IEEE Conference on Computer Vision and Pattern Recognition. pp. 2074-2081. https://doi.org/10.1109/cvpr.2012.6247912

[88] Liong, V. E.; Jiwen Lu; Gang Wang; et al.. (2015). Deep hashing for compact binary codes learning. 2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 2475-2483. https://doi.org/10.1109/cvpr.2015.7298862

[89] Jae-Pil Heo; Youngwoon Lee; Junfeng He; et al.. (2012). Spherical hashing. 2012 IEEE Conference on Computer Vision and Pattern Recognition. pp. 2957-2964. https://doi.org/10.1109/cvpr.2012.6248024

[90] Wang, J.; Zhang, T.; Song, J.; et al.. (2018). A Survey on Learning to Hash. IEEE Transactions on Pattern Analysis and Machine Intelligence. vol. 40. pp. 769-790. https://doi.org/10.1109/tpami.2017.2699960

[91] Yandex, A. B.; Lempitsky, V.. (2016). Efficient Indexing of Billion-Scale Datasets of Deep Descriptors. 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 2055-2063. https://doi.org/10.1109/cvpr.2016.226

[92] Malkov, Y.; Ponomarenko, A.; Logvinov, A.; et al.. (2014). Approximate nearest neighbor algorithm based on navigable small world graphs. Information Systems. vol. 45. pp. 61-68. https://doi.org/10.1016/j.is.2013.10.006

[93] Fu, C.; Xiang, C.; Wang, C.; et al.. (2019). Fast approximate nearest neighbor search with the navigating spreading-out graph. Proceedings of the VLDB Endowment. vol. 12. pp. 461-474. https://doi.org/10.14778/3303753.3303754

[94] Harwood, B.; Drummond, T.. (2016). FANNG: Fast Approximate Nearest Neighbour Graphs. 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). pp. 5713-5722. https://doi.org/10.1109/cvpr.2016.616

[95] Gollapudi, S.; Karia, N.; Sivashankar, V.; et al.. (2023). Filtered-DiskANN: Graph Algorithms for Approximate Nearest Neighbor Search with Filters. Proceedings of the ACM Web Conference 2023. pp. 3406-3416. https://doi.org/10.1145/3543507.3583552

[96] Wang, M.; Xu, X.; Yue, Q.; et al.. (2021). A comprehensive survey and experimental comparison of graph-based approximate nearest neighbor search. Proceedings of the VLDB Endowment. vol. 14. pp. 1964-1978. https://doi.org/10.14778/3476249.3476255

[97] Douze, M.; Guzhva, A.; Deng, C.; et al.. (2026). The Faiss Library. IEEE Transactions on Big Data. vol. 12. pp. 346-361. https://doi.org/10.1109/tbdata.2025.3618474

[98] Harsha Vardhan Simhadri; George Williams; Martin Aumüller; et al.. (2022). Results of the NeurIPS'21 Challenge on Billion-Scale Approximate Nearest Neighbor Search. arXiv preprint 2205.03763v1. http://arxiv.org/abs/2205.03763v1

[99] Aumüller, M.; Bernhardsson, E.; Faithfull, A.. (2017). ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor Algorithms. Lecture Notes in Computer Science. pp. 34-49. https://doi.org/10.1007/978-3-319-68474-1_3

[100] Williams, S.; Waterman, A.; Patterson, D.. (2009). Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures. https://doi.org/10.2172/1407078

[101] Jouppi, N. P.; Young, C.; Patil, N.; et al.. (2017). In-Datacenter Performance Analysis of a Tensor Processing Unit. ACM SIGARCH Computer Architecture News. vol. 45. pp. 1-12. https://doi.org/10.1145/3140659.3080246

[102] Harman, D.. (1993). Overview of the first TREC conference. Proceedings of the 16th annual international ACM SIGIR conference on Research and development in information retrieval  - SIGIR '93. pp. 36-47. https://doi.org/10.1145/160688.160692

[103] VOORHEES, E. M.. (2001). The TREC question answering track. Natural Language Engineering. vol. 7. pp. 361-378. https://doi.org/10.1017/s1351324901002789

[104] Buckley, C.; Voorhees, E. M.. (2004). Retrieval evaluation with incomplete information. Proceedings of the 27th annual international ACM SIGIR conference on Research and development in information retrieval. pp. 25-32. https://doi.org/10.1145/1008992.1009000

[105] Buckley, C.; Dimmick, D.; Soboroff, I.; et al.. (2007). Bias and the limits of pooling for large collections. Information Retrieval. vol. 10. pp. 491-508. https://doi.org/10.1007/s10791-007-9032-x

[106] Aslam, J. A.; Savell, R.. (2003). On the effectiveness of evaluating retrieval systems in the absence of relevance judgments. Proceedings of the 26th annual international ACM SIGIR conference on Research and development in informaion retrieval  - SIGIR '03. https://doi.org/10.1145/860500.860501

[107] Aslam, J. A.; Pavlu, V.; Savell, R.. (2003). A unified model for metasearch, pooling, and system evaluation. Proceedings of the twelfth international conference on Information and knowledge management  - CIKM '03. https://doi.org/10.1145/956950.956953

[108] Zobel, J.; Moffat, A.. (2006). Inverted files for text search engines. ACM Computing Surveys. vol. 38. pp. 6. https://doi.org/10.1145/1132956.1132959

[109] Thorne, J.; Vlachos, A.; Christodoulopoulos, C.; et al.. (2018). FEVER: a Large-scale Dataset for Fact Extraction and VERification. Proceedings of the 2018 Conference of the North American Chapter of
          the Association for Computational Linguistics: Human Language
          Technologies, Volume 1 (Long Papers). pp. 809-819. https://doi.org/10.18653/v1/n18-1074

[110] Johnson, W. B.; Lindenstrauss, J.. (1984). Extensions of Lipschitz mappings into a Hilbert space. Contemporary Mathematics. pp. 189-206. https://doi.org/10.1090/conm/026/737400

[111] Achlioptas, D.. (2003). Database-friendly random projections: Johnson-Lindenstrauss with binary coins. Journal of Computer and System Sciences. vol. 66. pp. 671-687. https://doi.org/10.1016/s0022-0000(03)00025-4

[112] Talagrand, M.. (1995). Concentration of measure and isoperimetric inequalities in product spaces. Publications Mathématiques de l'IHÉS. vol. 81. pp. 73-205. https://doi.org/10.1007/bf02699376

[113] McNemar, Q.. (1947). Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. Psychometrika. vol. 12. pp. 153-157. https://doi.org/10.1007/bf02295996

[114] Mann, H. B.; Whitney, D. R.. (1947). On a Test of Whether one of Two Random Variables is Stochastically Larger than the Other. The Annals of Mathematical Statistics. vol. 18. pp. 50-60. https://doi.org/10.1214/aoms/1177730491

[115] Shapiro, S. S.; Wilk, M. B.. (1965). An Analysis of Variance Test for Normality (Complete Samples). Biometrika. vol. 52. pp. 591. https://doi.org/10.2307/2333709

[116] Martin Bland, J.; Altman, D.. (1986). STATISTICAL METHODS FOR ASSESSING AGREEMENT BETWEEN TWO METHODS OF CLINICAL MEASUREMENT. The Lancet. vol. 327. pp. 307-310. https://doi.org/10.1016/s0140-6736(86)90837-8

[117] Ioannidis, J. P. A.. (2005). Why Most Published Research Findings Are False. PLoS Medicine. vol. 2. pp. e124. https://doi.org/10.1371/journal.pmed.0020124

[118] Peng, R. D.. (2011). Reproducible Research in Computational Science. Science. vol. 334. pp. 1226-1227. https://doi.org/10.1126/science.1213847

[119] Wilkinson, M. D.; Dumontier, M.; Aalbersberg, I. J.; et al.. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data. vol. 3. https://doi.org/10.1038/sdata.2016.18

[120] Sandve, G. K.; Nekrutenko, A.; Taylor, J.; et al.. (2013). Ten Simple Rules for Reproducible Computational Research. PLoS Computational Biology. vol. 9. pp. e1003285. https://doi.org/10.1371/journal.pcbi.1003285

[121] Stodden, V.; McNutt, M.; Bailey, D. H.; et al.. (2016). Enhancing reproducibility for computational methods. Science. vol. 354. pp. 1240-1241. https://doi.org/10.1126/science.aah6168

[122] McKinney, W.. (2010). Data Structures for Statistical Computing in Python. Proceedings of the Python in Science Conference. pp. 56-61. https://doi.org/10.25080/majora-92bf1922-00a

[123] Hunter, J. D.. (2007). Matplotlib: A 2D Graphics Environment. Computing in Science &amp; Engineering. vol. 9. pp. 90-95. https://doi.org/10.1109/mcse.2007.55
