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
measures reference density rather than relevance. Across 30 seeds in Computer
Science and 30 in Social Sciences, the per-request yield falls with hop
depth: the excess is +54.6 points at hop 1 and
+14.0 at hop 2 in the first field
(+61.1 and
+17.9 in the second), against a null whose chance
coupling is about 1.0 percent. The decay is structural, not an
artefact of how long the reference lists are. The allocation then has a price: depth wins only if one
depth batch costs less than **0.473** of a breadth page in Computer Science and
**0.401** in Social Sciences, with intervals
[0.326, 0.643] and [0.301, 0.515]. Both lie entirely below
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
saturation [1,2] — with the two routes compared in practice and the
recall-versus-effort trade-off stated rather than assumed [3]. Screening what comes back
is the cost that motivates automation [4], and evaluating what a search returned has a
methodology of its own [5,6,7], including the uncomfortable part: a
test collection carries the biases of how it was built [8,9,10].
Where to look next has been modelled before — information foraging treats a literature as a set of
patches and predicts movement by information scent [11,12] — and a search is ended by a
stopping rule rather than at the frontier [13,14]. That a retrieval has a price is old
in economics [15], and that disjoint literatures can each hold knowledge neither can see is
the strongest reason to walk at all [16]. What this literature does not supply is a **yield
per request** for the walk: it supplies stopping rules and recall targets, which are different objects.

### 2.2 What a citation link is evidence of

Two works sharing a reference are bibliographically coupled [17]; two works cited together
are co-cited [18]; both are similarity constructs, and both were used to map a field before
anyone called the result retrieval [19,20]. The literature is equally clear that a
citation is not a vote for quality: the motivations for citing vary [21,22],
cumulative advantage is real [23], and the validity of evaluative citation analysis is
contested rather than settled [24,25,26,27]. Scientometrics
has been reviewed as a field holding its own theory and practice [28], which is why the
claim made here is stated as an estimand rather than as a verdict on quality. Underneath, the distributions
are heavy tailed [29,30,31], citation of a work ages with a distributional rather
than a fixed form [32], and the networks those citations form are worth measuring on their
own terms [33,34]. This paper therefore uses a citation only as a **link**, never as
a score, and compares ranked things only where a measure for the comparison exists
[35,36,37].

### 2.3 Matching, and why an unmatched control lies

Reference lists are not stationary: they have grown and narrowed [38], and what a
bibliographic database can see lags what is being published [39], so a control drawn without
matching measures the archive at two different moments at once. Adjusting for a covariate removes that
covariate's effect and nothing else [40,41,42], the adjustment needs the
confounder to have been measured at all [43], and selection into the sample has to be
modelled rather than assumed away [44]; the general form of that problem — a sample whose
distribution differs from the target's — has a name [45]. The bibliometric version of the
same lesson is that productivity and impact are skewed [46,47] and that authorship and
collaboration structures drift [48,49]. A summary built on an unmatched base rate
reports the base rate.

### 2.4 Chance agreement, and saying an absence out loud

An observed share contains the agreement chance alone would produce, and removing it is standard
[50]; a quantity is worth reporting only when it is defined as one [51]. An
interval for a share of a fixed sample has a closed form [52,53], and where no closed
form exists the bootstrap supplies one [54]. The reporting side matters as much: a p-value is
not the probability that a hypothesis is true [55], which is why every verdict in this
paper is an interval placed against a floor rather than a threshold crossed.

### 2.5 Allocation, which is a sequential decision

Spending the next request wide or deep is an allocation over a finite number of pulls, and it has a name
in the decision literature: exploration against exploitation [56], written as a policy over
states [57], with probability matching as the original rule for dividing finite trials
[58] and sequential assignment across arms as the formal object [59]; bandit
treatments are the modern statement of the same problem [60,61]. Proximity on a
citation-like graph has been computed for a long time — through hubs and authorities
[62], link ranking [63] and random walks with restart [64] — and all of
it answers *what is near this seed*, not *what the next request buys*. The one prior bearing directly on
order is that attention to a paper decays [65]: if a seed's citers are a wasting asset, then
**when** a request is spent is part of what it is worth, which is why this paper prices a request and not
a work.

## 3. The null, and why it has to be length-matched

Two reference lists of lengths `a` and `b` drawn from a field's vocabulary couple at a rate that rises
with both. A control sample whose median reference list is empty therefore measures the archive's
coverage, not the field's behaviour. We bin every candidate by its own reference-list length
(1-9, 10-49, 50-99, 100+), draw a null pool of
field works in the same year window, and compute the same predicate against the **same seed**. A bin
with fewer than 10 null works is reported NOT RUN and is never read as a zero.

The sample is drawn from OpenAlex [66], and coverage in any bibliographic database is uneven
by region and language [67,68] — a different database would let a different study
see different things [68] — while the sampling design is part of the estimator rather than a
preliminary to it [69]. Field assignment is the same kind of commitment: publication-level
classifications differ and the choice moves the answer [70,71], normalisation
methods for cross-field comparison rest on different assumptions [72,73], and
fields differ in reporting behaviour in ways normalisation does not remove [74]. It is also
why the two fields are never pooled: combining subgroups can reverse a comparison [75], a
reversal that has bitten real data [76], and the between-field difference is the quantity
under test rather than an inconvenience to be averaged away.

## 4. Frame, and the cost model

Seeds are drawn reproducibly inside a top-level field with a fixed year window, citation band and
sampling seed; the field's `display_name` is verified before sampling, because a filter without a field
constraint silently lands in another discipline while every instrument check stays green.

Both arms are named by the register's own identifiers rather than by a label typed here: the first field
is field 17 and the second is field 33, and each
arm's filter constrains `primary_topic.field.id` — the top-level field itself, not a subfield beneath
it. The identifier is printed because the name alone does not fix the referent: the same register also
carries a *domain* under which that field sits, and the domain's display name is identical to the
second field's, so "field" is the word doing the work in every sentence that compares the two.

The cost model is the API's, not ours, and both constants are measured from the service's own refusals
rather than chosen: a page (`filter=cites:`) returns at most 200
works (one more is refused), and an id filter accepts at most
100 values (more is refused with *"Maximum number of values exceeded"*).
One page therefore sells twice the works of one batch for the same one request. The cost ratio `w` is
defined as *the price of one depth batch divided by the price of one breadth page*; the API's own
accounting is `w = 1`, and a batch can never cost less than zero, so the admissible range is `w ≥ 1`.

Both constants are measured rather than chosen, and that is a design commitment rather than a
formality: case-study research has to state its design and the inferences it licenses
[77,78], benchmarking practice needs its own critique [79], and an
impact signal that is convenient to compute is not thereby the right one [80,81]. The two
constants this paper uses happen to be exact, because the service states them by refusing to exceed
them.

## 5. Results

### 5.1 The decay

Table 1. Coupled share and its excess over the length-matched, field-matched null.

| hop | field | coupled / defined | observed | null | excess |
|---|---|---|---|---|---|
| hop 1 | Computer Science | 783 / 1408 | 0.556 | 0.010 | 0.546 |
| hop 2 | Computer Science | 777 / 5212 | 0.149 | 0.009 | 0.140 |
| hop 1 | Social Sciences | 967 / 1545 | 0.626 | 0.015 | 0.611 |
| hop 2 | Social Sciences | 825 / 4280 | 0.193 | 0.014 | 0.179 |

The pooled share is not the statistic we judge; it weights each seed by how many works it contributed.
The per-seed statistic is `d(s) = excess(hop 2) - excess(hop 1)`, and it is judged over the seed-level
distribution, because works inside one seed share its reference vocabulary and a binomial pooled across
seeds would be over-precise.

Table 2. Per-seed decay, by field.

| field | seeds | mean `d` | 95% interval | median | seeds `d<0` | law |
|---|---|---|---|---|---|---|
| Computer Science | 30 | -0.4031 | [-0.490, -0.316] | -0.430 | 27 | holds |
| Social Sciences | 30 | -0.4241 | [-0.487, -0.351] | -0.448 | 29 | holds |

Figure 1 (`figures/fig1_decay.png`) draws the same distribution seed by seed, and each axis label
carries that field's own count of negative seeds rather than a summary word — the law is a statement
about the mean, and the figure is drawn so that a reader can see how much of it the seeds carry.

Between the two fields the difference of the mean `d` is
-0.0209 with a 95% interval
[-0.131, 0.088]: indistinguishable at this sample size, which is what a replication looks
like. **The fields are deliberately not pooled** — the between-field variation is the claim under test,
and pooling would buy precision by erasing it.

### 5.2 The price at which the allocation would change

Table 3. What one request buys, and the flip ratio.

| field | coupled per page | coupled per batch | page worth, in batches | `w*` | 95% interval | admissible? |
|---|---|---|---|---|---|---|
| Computer Science | 28.667 | 13.567 | 2.113 | 0.473 | [0.326, 0.643] | no |
| Social Sciences | 32.233 | 12.933 | 2.492 | 0.401 | [0.301, 0.515] | no |

`w*` is the largest batch price at which buying depth beats spending the same request budget on
breadth; Figure 2 (`figures/fig2_price_bound.png`) places both intervals against the floor. Since `w ≥ 1` always, an interval entirely below one is not a near miss but a closed
direction **for this registrant**: no plausible client pays a tenth of a request for a batch. A
registry whose batch carried more than 2.11 times a page's
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
effect gives a task a known cost [82]. Here that known effect is the coupling that
reference-list length alone produces, and it is what the null in §3 removes.

## 6. Prior beliefs, reported against the data

These were registered on the issue before the decisive measurement.

The registered priors are stated as magnitudes because a prior stated as a direction cannot be wrong
in an interesting way. That choice follows the metric literature: a metric needs a statement of what it
measures before it is used [83,84], an aggregate can look authoritative while not
being an article-level quantity [85], and an index without a statistical basis cannot carry
an interval at all [86,87]. It also follows the statistical literature on how such statements
fail: significance is a threshold and not a finding [88], a small study's interval must be
read against the effect it could have detected [89,90], an absence is reported by
testing for equivalence rather than by failing to reject [91], and the judgement of what a
result means is subject to stated biases [92].

| prior | statement | outcome |
|---|---|---|
| P1 | breadth beats depth per request by at least a factor of two at equal budget | **confirmed in direction, wrong in magnitude as stated**: the page-to-batch ratio is 2.11 in Computer Science and 2.49 in Social Sciences |
| P2 | hop 2 is not worthless: its excess is many times chance | **confirmed**, 0.140 against a null of 0.009 |
| P3 | the breadth advantage is not an artefact of the cost model | **unresolved, and reported as such**: with the price pinned from the API's own refusals the ratio is 2.11, but the flip ratio moves with the budget-to-pool ratio, so the advantage is partly a property of the model |

## 7. Contribution level, and what this study can detect

The level this paper claims is **`theory+empirics`**, on the evidence it actually carries and narrowed
where that evidence narrows it. The theory is the price bound derived from the cost model in §5.2: depth
wins only if one depth batch costs less than `w*` breadth pages. The empirics are a decay law judged
against a length-matched null, measured in two independent fields, the second chosen by a rule fixed
before it was measured, with two controls — an arm that follows the opposite rule, and a hindsight
oracle. The universal claim stops at the registry: the bound is a statement about this API's documented
request caps, not about citation networks in general.

The obligations taken on here are not self-imposed ceremony. Preregistration changes what a result can
mean [93], a registered report goes further and fixes the analysis before the data exist
[94], and the space of defensible analyses that leaves open is exactly why a result can be
made to look robust after the fact [95]. The reproducibility agenda this joins is stated as a
standard rather than an aspiration [96], an openness programme [97,98], and
it now applies to machine learning and artificial intelligence as much as to the fields it began in
[99].

That level also obliges the paper to say what it cannot resolve, and to place each verdict above
against the sample's own noise. The half-width of an interval is the smallest effect this study can
distinguish; an effect narrower than it is **no information**, and is never reported here as evidence
for or against a prior.

| quantity | half-width of its 95% interval | how a narrower effect must be read |
|---|---|---|
| mean decay `d`, Computer Science | 0.087 | a mean decay smaller than this is not resolved |
| mean decay `d`, Social Sciences | 0.068 | same, in the second field |
| `w*`, Computer Science | 0.159 | `w*` is located to about this much of a page |
| `w*`, Social Sciences | 0.107 | same, in the second field |
| difference of the two fields | 0.110 | the observed difference is far inside it |

Read against this table, the two headline results are not marginal: the mean decay is
-0.403 in the first field (interval [-0.490, -0.316]) and
-0.424 in the second ([-0.487, -0.351]),
so each interval clears zero by more than its own half-width, and each `w*` interval clears the floor the
same way. The third prior in §6 is a different case, which is why it is reported as unresolved rather
than as a refutation: the field-to-field difference is
-0.0209 with interval [-0.131, 0.088], which
contains zero, so at this sample size it is no information either way.

## 8. A correction kept visible

An earlier draft of this work reported the flip ratio as a value above one and concluded that the two
allocations tie at the API's own price. That number was wrong, and wrong for a reason worth recording:
the breadth arm was credited with the **first `B` seeds in sample order**, an arbitrary draw that
happened to be weak, while every depth arm was averaged. Recomputing over random orderings moved the
flip ratio from the published figure to **0.473** in Computer Science. The
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
(W2907281321); its contribution is a labelled zero, not a measurement, and it
marks where the statistic is defined.

**The per-request price is a request count.** Rate limits differ per endpoint in ways this study does
not measure, so `w` is a count ratio and not wall-clock or money.

**A negative finding is still a claim about the world, and this literature exists because such claims
fail.** That is why an interval is printed next to every verdict: published findings have repeatedly
failed to hold [100], that failure has been made measurable rather than rhetorical
[101], and the response has been a stated programme rather than an appeal to care
[102]. A reader who accepts the decay law should be able to re-derive it from the committed
arms in one command, which is what the reproduction section sets out.

**Why it is still worth publishing.** The bound is falsifiable in one step and it tells a tool builder
where to look: a batch-shaped endpoint would have to beat a page by more than
2.11 before depth deserves any of the budget.

## 10. Reproduction

`README.md` states the one command and the expected output. The committed data are the two arms'
reference lists, with digests taken over the decompressed bytes, and `analysis.py` is a pure function of
them: it fetches nothing and imports nothing outside the standard library.

## References

[1] Petersen, Kai; Vakkalanka, Sairam; Kuzniarz, Ludwik. Guidelines for conducting systematic mapping studies in software engineering: An update. Information and Software Technology, 2015. doi:10.1016/j.infsof.2015.03.007

[2] Wohlin, Claes. Guidelines for snowballing in systematic literature studies and a replication in software engineering. Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering, 2014. doi:10.1145/2601248.2601268

[3] Badampudi, Deepika; Wohlin, Claes; Petersen, Kai. Experiences from using snowballing and database searches in systematic literature studies. Proceedings of the 19th International Conference on Evaluation and Assessment in Software Engineering, 2015. doi:10.1145/2745802.2745818

[4] Marshall, Iain J.; Wallace, Byron C.. Toward systematic review automation: a practical guide to using machine learning tools in research synthesis. Systematic Reviews, 2019. doi:10.1186/s13643-019-1074-9

[5] Manning, Christopher D.; Raghavan, Prabhakar; Schütze, Hinrich. Introduction to Information Retrieval. 2008. doi:10.1017/cbo9780511809071

[6] Robertson, Stephen; Zaragoza, Hugo. The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends® in Information Retrieval, 2009. doi:10.1561/1500000019

[7] Salton, Gerard; Buckley, Christopher. Term-weighting approaches in automatic text retrieval. Information Processing & Management, 1988. doi:10.1016/0306-4573(88)90021-0

[8] Sanderson, Mark. Test Collection Based Evaluation of Information Retrieval Systems. Foundations and Trends® in Information Retrieval, 2010. doi:10.1561/1500000009

[9] Buckley, Chris; Voorhees, Ellen M.. Retrieval evaluation with incomplete information. Proceedings of the 27th annual international ACM SIGIR conference on Research and development in information retrieval, 2004. doi:10.1145/1008992.1009000

[10] Voorhees, Ellen M.. The Philosophy of Information Retrieval Evaluation. Lecture Notes in Computer Science, 2002. doi:10.1007/3-540-45691-0_34

[11] Pirolli, Peter; Card, Stuart. Information foraging.. Psychological Review, 1999. doi:10.1037/0033-295x.106.4.643

[12] Fu, Wai-Tat; Pirolli, Peter. SNIF-ACT: A Cognitive Model of User Navigation on the World Wide Web. 2007. doi:10.21236/ada462156

[13] Kraft, D.H.; Lee, T.. Stopping rules and their effect on expected search length. Information Processing & Management, 1979. doi:10.1016/0306-4573(79)90007-4

[14] Simon, Herbert A.. A Behavioral Model of Rational Choice. The Quarterly Journal of Economics, 1955. doi:10.2307/1884852

[15] Stigler, George J.. The Economics of Information. Journal of Political Economy, 1961. doi:10.1086/258464

[16] Don R. Swanson. Undiscovered Public Knowledge. The Library Quarterly, 1986. doi:10.1086/601720

[17] Kessler, M. M.. Bibliographic coupling between scientific papers. American Documentation, 1963. doi:10.1002/asi.5090140103

[18] Small, Henry. Co‐citation in the scientific literature: A new measure of the relationship between two documents. Journal of the American Society for Information Science, 1973. doi:10.1002/asi.4630240406

[19] Goodwin, Jack; Garfield, Eugene. Citation Indexing-Its Theory and Application in Science, Technology, and Humanities. Technology and Culture, 1980. doi:10.2307/3104125

[20] Price, Derek J. de Solla. Networks of Scientific Papers. Science, 1965. doi:10.1126/science.149.3683.510

[21] Moravcsik, Michael J.; Murugesan, Poovanalingam. Some Results on the Function and Quality of Citations. Social Studies of Science, 1975. doi:10.1177/030631277500500106

[22] Nigel Gilbert, G.. Referencing as Persuasion. Social Studies of Science, 1977. doi:10.1177/030631277700700112

[23] Robert Κ. Merton. The Matthew Effect in Science. Science, 1968. doi:10.1126/science.159.3810.56

[24] Peritz, Bluma C.. A classification of citation roles for the social sciences and related fields. Scientometrics, 1983. doi:10.1007/bf02147226

[25] Lawani, Stephen M.. On the Heterogeneity and Classification of Author Self‐Citations. Journal of the American Society for Information Science, 1982. doi:10.1002/asi.4630330506

[26] Bornmann, Lutz; Daniel, Hans‐Dieter. What do citation counts measure? A review of studies on citing behavior. Journal of Documentation, 2008. doi:10.1108/00220410810844150

[27] Tahamtan, Iman; Bornmann, Lutz. What do citation counts measure? An updated review of studies on citations in scientific documents published between 2006 and 2018. Scientometrics, 2019. doi:10.1007/s11192-019-03243-4

[28] Mingers, John; Leydesdorff, Loet. A review of theory and practice in scientometrics. European Journal of Operational Research, 2015. doi:10.1016/j.ejor.2015.04.002

[29] Redner, S.. How popular is your paper? An empirical study of the citation distribution. The European Physical Journal B, 1998. doi:10.1007/s100510050359

[30] Barabási, Albert-László; Albert, Réka. Emergence of Scaling in Random Networks. Science, 1999. doi:10.1126/science.286.5439.509

[31] Radicchi, Filippo; Fortunato, Santo; Castellano, Claudio. Universality of citation distributions: Toward an objective measure of scientific impact. Proceedings of the National Academy of Sciences, 2008. doi:10.1073/pnas.0806977105

[32] Burrell, Quentin L.. The nth-citation distribution and obsolescence. Scientometrics, 2002. doi:10.1023/a:1014816911511

[33] Newman, M. E. J.. Scientific collaboration networks.  I. Network construction and fundamental results. Physical Review E, 2001. doi:10.1103/physreve.64.016131

[34] Newman, M. E. J.. Mixing patterns in networks. Physical Review E, 2003. doi:10.1103/physreve.67.026126

[35] Ronald Fagin; Ravi Kumar; D. Sivakumar. Comparing top k lists. 2003. doi:10.5555/644108.644113

[36] Järvelin, Kalervo; Kekäläinen, Jaana. Cumulated gain-based evaluation of IR techniques. ACM Transactions on Information Systems, 2002. doi:10.1145/582415.582418

[37] Webber, William; Moffat, Alistair; Zobel, Justin. A similarity measure for indefinite rankings. ACM Transactions on Information Systems, 2010. doi:10.1145/1852102.1852106

[38] Evans, James A.. Electronic Publication and the Narrowing of Science and Scholarship. Science, 2008. doi:10.1126/science.1150473

[39] Larsen, Peder Olesen; von Ins, Markus. The rate of growth in scientific publication and the decline in coverage provided by Science Citation Index. Scientometrics, 2010. doi:10.1007/s11192-010-0202-z

[40] Cochran, W. G.. The Effectiveness of Adjustment by Subclassification in Removing Bias in Observational Studies. Biometrics, 1968. doi:10.2307/2528036

[41] ROSENBAUM, PAUL R.; RUBIN, DONALD B.. The central role of the propensity score in observational studies for causal effects. Biometrika, 1983. doi:10.1093/biomet/70.1.41

[42] Stuart, Elizabeth A.. Matching Methods for Causal Inference: A Review and a Look Forward. Statistical Science, 2010. doi:10.1214/09-sts313

[43] Rubin, Donald B.. Estimating causal effects of treatments in randomized and nonrandomized studies.. Journal of Educational Psychology, 1974. doi:10.1037/h0037350

[44] Heckman, James J.. Sample Selection Bias as a Specification Error. Econometrica, 1979. doi:10.2307/1912352

[45] Shimodaira, Hidetoshi. Improving predictive inference under covariate shift by weighting the log-likelihood function. Journal of Statistical Planning and Inference, 2000. doi:10.1016/s0378-3758(00)00115-4

[46] G.F.S.. The frequency distribution of scientific productivity. Journal of the Franklin Institute, 1926. doi:10.1016/s0016-0032(26)91166-6

[47] Egghe, Leo. Theory and practise of the g-index. Scientometrics, 2006. doi:10.1007/s11192-006-0144-7

[48] Wuchty, Stefan; Jones, Benjamin F.; Uzzi, Brian. The Increasing Dominance of Teams in Production of Knowledge. Science, 2007. doi:10.1126/science.1136099

[49] Jones, Benjamin F.; Wuchty, Stefan; Uzzi, Brian. Multi-University Research Teams: Shifting Impact, Geography, and Stratification in Science. Science, 2008. doi:10.1126/science.1158357

[50] Cohen, Jacob. A Coefficient of Agreement for Nominal Scales. Educational and Psychological Measurement, 1960. doi:10.1177/001316446002000104

[51] Claude E. Shannon. A Mathematical Theory of Communication. Bell System Technical Journal, 1948. doi:10.1002/j.1538-7305.1948.tb01338.x

[52] Wilson, Edwin B.. Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association, 1927. doi:10.1080/01621459.1927.10502953

[53] Efron, B.. Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics, 1979. doi:10.1214/aos/1176344552

[54] Efron, Bradley; Tibshirani, R.J.. An Introduction to the Bootstrap. 1994. doi:10.1201/9780429246593

[55] Goodman, Steven. A Dirty Dozen: Twelve P-Value Misconceptions. Seminars in Hematology, 2008. doi:10.1053/j.seminhematol.2008.04.003

[56] March, James G.. Exploration and Exploitation in Organizational Learning. Organization Science, 1991. doi:10.1287/orsc.2.1.71

[57] Sutton, Richard S.; Precup, Doina; Singh, Satinder. Between MDPs and semi-MDPs: A framework for temporal abstraction in reinforcement learning. Artificial Intelligence, 1999. doi:10.1016/s0004-3702(99)00052-1

[58] Thompson, William R.. On the Likelihood that One Unknown Probability Exceeds Another in View of the Evidence of Two Samples. Biometrika, 1933. doi:10.2307/2332286

[59] Robbins, Herbert. Some aspects of the sequential design of experiments. Bulletin of the American Mathematical Society, 1952. doi:10.1090/s0002-9904-1952-09620-8

[60] Auer, Peter; Cesa-Bianchi, Nicolò; Fischer, Paul. Finite-time Analysis of the Multiarmed Bandit Problem. Machine Learning, 2002. doi:10.1023/a:1013689704352

[61] Lattimore, Tor; Szepesvári, Csaba. Bandit Algorithms. 2020. doi:10.1017/9781108571401

[62] Kleinberg, Jon M.. Authoritative sources in a hyperlinked environment. Journal of the ACM, 1999. doi:10.1145/324133.324140

[63] Brin, Sergey; Page, Lawrence. The anatomy of a large-scale hypertextual Web search engine. Computer Networks and ISDN Systems, 1998. doi:10.1016/s0169-7552(98)00110-x

[64] Tong, Hanghang; Faloutsos, Christos; Pan, Jia-yu. Fast Random Walk with Restart and Its Applications. Sixth International Conference on Data Mining (ICDM'06), 2006. doi:10.1109/icdm.2006.70

[65] Briotta Parolo, Pietro Della; Pan, Raj Kumar; Ghosh, Rumi; et al.. Attention Decay in Science. SSRN Electronic Journal, 2015. doi:10.2139/ssrn.2575225

[66] Jason R Priem; Heather Piwowar; Richard Orr. OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv (Cornell University), 2022. doi:10.48550/arxiv.2205.01833

[67] Mongeon, Philippe; Paul-Hus, Adèle. The journal coverage of Web of Science and Scopus: a comparative analysis. Scientometrics, 2016. doi:10.1007/s11192-015-1765-5

[68] Visser, Martijn; van Eck, Nees Jan; Waltman, Ludo. Large-scale comparison of bibliographic data sources: Scopus, Web of
                    Science, Dimensions, Crossref, and Microsoft Academic. Quantitative Science Studies, 2021. doi:10.1162/qss_a_00112

[69] Freeman, Linton C.; Kish, Leslie. Survey Sampling.. Social Forces, 1966. doi:10.2307/2575802

[70] Waltman, Ludo; van Eck, Nees Jan. A new methodology for constructing a publication‐level classification system of science. Journal of the American Society for Information Science and Technology, 2012. doi:10.1002/asi.22748

[71] Klavans, Richard; Boyack, Kevin W.. Which Type of Citation Analysis Generates the Most Accurate Taxonomy of Scientific and Technical Knowledge?. Journal of the Association for Information Science and Technology, 2017. doi:10.1002/asi.23734

[72] Waltman, Ludo; van Eck, Nees Jan; van Leeuwen, Thed N.; et al.. Towards a new crown indicator: an empirical analysis. Scientometrics, 2011. doi:10.1007/s11192-011-0354-5

[73] Schubert, A.; Braun, T.. Cross-field normalization of scientometric indicators. Scientometrics, 1996. doi:10.1007/bf02129597

[74] Fanelli, Daniele. “Positive” Results Increase Down the Hierarchy of the Sciences. PLoS ONE, 2010. doi:10.1371/journal.pone.0010068

[75] Simpson, E. H.. The Interpretation of Interaction in Contingency Tables. Journal of the Royal Statistical Society Series B: Statistical Methodology, 1951. doi:10.1111/j.2517-6161.1951.tb00088.x

[76] Bickel, P. J.; Hammel, E. A.; O'Connell, J. W.. Sex Bias in Graduate Admissions: Data from Berkeley. Science, 1975. doi:10.1126/science.187.4175.398

[77] Runeson, Per; Höst, Martin. Guidelines for conducting and reporting case study research in software engineering. Empirical Software Engineering, 2009. doi:10.1007/s10664-008-9102-8

[78] Wohlin, Claes; Runeson, Per; Höst, Martin; et al.. Experimentation in Software Engineering. 2012. doi:10.1007/978-3-642-29044-2

[79] Lipton, Zachary C.; Steinhardt, Jacob. Troubling Trends in Machine Learning Scholarship. Queue, 2019. doi:10.1145/3317287.3328534

[80] Bollen, Johan; Van de Sompel, Herbert; Hagberg, Aric; et al.. A Principal Component Analysis of 39 Scientific Impact Measures. PLoS ONE, 2009. doi:10.1371/journal.pone.0006022

[81] Sugimoto, Cassidy R.; Work, Sam; Larivière, Vincent; et al.. Scholarly use of social media and altmetrics: A review of the literature. Journal of the Association for Information Science and Technology, 2017. doi:10.1002/asi.23833

[82] Stroop, J. R.. Studies of interference in serial verbal reactions.. Journal of Experimental Psychology, 1935. doi:10.1037/h0054651

[83] Hicks, Diana; Wouters, Paul; Waltman, Ludo; et al.. Bibliometrics: The Leiden Manifesto for research metrics. Nature, 2015. doi:10.1038/520429a

[84] Ioannidis, John P. A.. How to Make More Published Research True. PLoS Medicine, 2014. doi:10.1371/journal.pmed.1001747

[85] Seglen, Per O. Why the impact factor of journals should not be used for evaluating research. BMJ, 1997. doi:10.1136/bmj.314.7079.497

[86] Waltman, Ludo; van Eck, Nees Jan. The inconsistency of the h‐index. Journal of the American Society for Information Science and Technology, 2012. doi:10.1002/asi.21678

[87] Bornmann, Lutz; Daniel, Hans‐Dieter. What do we know about the
                    <i>h</i>
                    index?. Journal of the American Society for Information Science and Technology, 2007. doi:10.1002/asi.20609

[88] Amrhein, Valentin; Greenland, Sander; McShane, Blake. Scientists rise up against statistical significance. Nature, 2019. doi:10.1038/d41586-019-00857-9

[89] Borenstein, Michael; Hedges, Larry V.; Higgins, Julian P. T.; et al.. Introduction to Meta‐Analysis. 2009. doi:10.1002/9780470743386

[90] King, Gary; Zeng, Langche. Logistic Regression in Rare Events Data. Political Analysis, 2001. doi:10.1093/oxfordjournals.pan.a004868

[91] Lakens, Daniel. Equivalence Tests:  A Practical Primer for t-Tests, Correlations, and Meta-Analyses. 2016. doi:10.31234/osf.io/97gpc_v1

[92] Tversky, Amos; Kahneman, Daniel. Judgment under Uncertainty: Heuristics and Biases. 1973. doi:10.21236/ad0767426

[93] Nosek, Brian A.; Ebersole, Charles R.; DeHaven, Alexander Carl; et al.. The Preregistration Revolution. 2017. doi:10.31219/osf.io/2dxu5

[94] Chambers, Christopher D.. Registered Reports: A new publishing initiative at Cortex. Cortex, 2013. doi:10.1016/j.cortex.2012.12.016

[95] Andrew Gelman; Eric Loken. The Statistical Crisis in Science. American Scientist, 2014. doi:10.1511/2014.111.460

[96] Peng, Roger D.. Reproducible Research in Computational Science. Science, 2011. doi:10.1126/science.1213847

[97] Nosek, Brian A.; Bar-Anan, Yoav. Scientific Utopia: I. Opening Scientific Communication. Psychological Inquiry, 2012. doi:10.1080/1047840x.2012.692215

[98] Edward A. Miguel; Colin F. Camerer; Katherine Casey; et al.. Promoting Transparency in Social Science Research. Science, 2014. doi:10.1126/science.1245317

[99] Hutson, Matthew. Artificial intelligence faces reproducibility crisis. Science, 2018. doi:10.1126/science.359.6377.725

[100] Ioannidis, John P. A.. Why Most Published Research Findings Are False. PLoS Medicine, 2005. doi:10.1371/journal.pmed.0020124

[101] Brian A. Nosek; George Charles Alter; George C. Banks; et al.. Promoting an open research culture. Science, 2015. doi:10.1126/science.aab2374

[102] Munafò, Marcus R.; Nosek, Brian A.; Bishop, Dorothy V. M.; et al.. A manifesto for reproducible science. Nature Human Behaviour, 2017. doi:10.1038/s41562-016-0021
