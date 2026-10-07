# How Much Fairness Is Free? The Zero-Cost Region of Group Quotas in Diversity Selection

## Abstract

Group quotas in clustering, subset selection and ranking are usually justified by a *worst-case* bound:
the field knows how bad a fairness constraint *can* be, and reports approximation ratios or a price of
fairness that holds for the hardest instance. This paper asks the complementary and, in practice, more
consequential question: **for a given instance, is the quota free at all, and how much of it is free
before it costs anything?** We formalise the free region with a single scalar. Selecting the
lowest-tightness proportional quota is equivalent to fixing a *forced-seat count* `M`; we define `M*` as
the largest `M` for which the constrained optimum still equals the unconstrained one, and call `M*/k` the
**free width** — the fraction of the selection that can be constrained at zero cost.

We measure the free region exactly (complete enumeration, cross-checked by an integer program) on two
objectives — a bottleneck (`max-min`) and a sum (`max-sum`) — over 64 synthetic cases (1152 cells) and on
a real corpus across 416 further cases, and report four findings, each registered as a prior before it was
measured. **(P1′ confirmed)** A non-empty free region is the rule, not the exception: the first binding
quota is free in **32/32** and **30/32** synthetic settings and **24/24** on real rows; the free width has
median **0.80–0.90**, and the *whole* quota is free in **19 of 64** synthetic cases (30 %) and **5 of 24**
real cases (21 %). **(P2′ refuted)** No cheap statistic predicts the free width. A solve-free geometric
proxy and three instance statistics were tested on a real-row sweep whose alignment input spans
**0.183–1.037** (spread 0.854) while the output spans **0.000–1.000** — both wide enough for a negative to
mean something — and every candidate loses to predicting the median. **(P3 inverted)** Above `M*`, the two
objectives behave *oppositely* to the registered prediction: the `max-min` cost curve is a **step** (median
exponent `beta = 0.000`) and the `max-sum` curve is a **slope** (`beta = 0.92`). **(P4 confirmed, with a
boundary)** The "cost of fairness" measured against a greedy baseline is **objective-specific**:
farthest-first greedy is already short of the unconstrained optimum in **7/32** `max-min` cases (median gap
17.1 %) but in only **29/32** `max-sum` cases — though the effect shrinks as groups become well separated.

The practical consequence is a decision rule a practitioner can run once: solve the unconstrained problem,
then raise the forced-seat count until the optimum first moves. The result is one number — where the free
quota ends — and this paper establishes that (i) it is usually well inside the quota, (ii) it must be
*measured*, not predicted from an instance statistic, and (iii) the shape of the cost beyond it depends on
whether the objective is a bottleneck or a sum.

## 1. Introduction

Fairness constraints on a set-selection problem are normally analysed adversarially. Fair clustering asks
for a partition in which every protected group occupies a bounded share of every cluster, and the
literature's contribution is an **approximation ratio** that holds for the worst instance
[@arxiv:1802.05733] [@arxiv:1901.08628] [@arxiv:1901.08668]. The same shape appears across constrained
clustering [@doi:10.1109/cvprw.2009.5206852] [@arxiv:2009.03078], diversity maximization
[@doi:10.1145/2487575.2487636] [@arxiv:2502.02530], fair allocation [@doi:10.1145/2940716.2940726] [@arxiv:1704.00222] and fair ranking [@arxiv:1905.09947] [@arxiv:2010.06986]: a guarantee that holds no
matter how unfavourable the instance is. A price-of-fairness result [@arxiv:1508.05253] [@arxiv:1406.5722] [@doi:10.24963/ijcai.2019/12] answers the attendant question — how much efficiency must be sacrificed —
again as a worst-case bound.

Worst-case bounds answer "how bad can it get?". A practitioner deploying a quota faces a different
question. They hold **one** instance — a candidate pool, a set of embedding vectors, a shortlist — and a
constraint they are told to satisfy. The question that decides whether the constraint is worth imposing is
whether it costs anything *on this instance*, and if so where the cost begins. For a proportional
group-quota requirement, "no group may be under-represented beyond a fixed level", this has a clean form.
The constraint families are naturally *indexed*: as the required representation tightens, some first level
binds and the optimum drops; all weaker levels are, on that instance, **free**.

This paper makes that observation a measured object. We select a `k`-subset of `n` points under a
proportional per-group **floor** (the largest-remainder allocation of `M` forced seats, so the floors sum to
`M` exactly). At `M = 0` the problem is the unconstrained metric diversity problem; as `M` increases, the
optimum can only fall. Define

    M*  = the largest M such that OPT(M) = OPT(0),      free width = M*/k.

`M*` is the number of seats that can be *forced* into the required groups for free, and `M*/k` is the
fraction of the selection that carries the constraint at no cost. Everything at or below `M*` is a level a
practitioner may impose without paying for it; `M*+1` is where the trade-off starts.

We ask four questions and answer them with exact computation, not approximation:

1. **How wide is the free region?** (§4) It is wide: the first binding quota is free in almost every
   instance we construct, the free width has median 0.80–0.90, and a substantial minority of instances
   carry the entire quota for free.
2. **What does the cost curve above `M*` look like?** (§5) It depends on the *objective family*, and in a
   way we registered backwards: a bottleneck objective jumps to a plateau (a step), a sum objective grows
   smoothly (a slope).
3. **Is a "cost of fairness" measured against the standard greedy baseline even the constraint's cost?**
   (§6) On a bottleneck objective the greedy gap and the constraint cost are confounded, and the confound
   shrinks as groups become well separated.
4. **Can the free width be predicted cheaply, without solving the constrained problem?** (§7) No — and
   we establish it on a real-row sweep deliberately built to have enough input and output range for the
   negative to be interpretable.

**Contributions.**

- A construct — the **zero-cost region** `M*` and the **free width** `M*/k` — that turns a worst-case bound
  into an instance-level, measurable quantity, with exact computation (§3).
- A positive empirical result: the free region is non-empty and usually wide, measured on synthetic
  families, on a real corpus, and on a sweep designed to test the predictor (§4).
- An inverted cost law: the `max-min` objective pays a **step** and the `max-sum` objective a **slope**,
  the reverse of the registered direction, with a mechanism (§5).
- A boundary on the standard baseline: greedy-vs-exact confounding is objective-specific and weakens as
  groups separate (§6).
- A negative result stated against its own prior: **no cheap statistic predicts the free width**,
  established with the input *and* output ranges measured first (§7).

**Significance.** The result changes a decision. A team imposing a proportional quota — on a candidate
shortlist, a benchmark suite, a diversifying data selector — currently has no way to know, before solving
the constrained problem, whether the quota costs them anything. This paper shows the answer is almost
always "nothing, up to a point", gives an exact and cheap procedure to find that point, and shows the point
is *not* predictable from an instance statistic, so it must be computed. That converts a design question
from "should we accept a fairness/quality trade-off?" into "where does our trade-off actually begin?" —
usually a different, easier decision.

## 2. Related work, and what this paper does differently

**Fair clustering and group-quota selection.** The dominant formalism balances every cluster with respect to
protected groups. The two anchor problems are fairlets, which reduce fair `k`-median to an unfair one
[@arxiv:1802.05733], and the `(k, f)`-fairness criterion with its `(3, 1)`-to-`(9, 1)` approximations and the
later improvements that carried the guarantees to `(3, 1)` and beyond [@arxiv:1901.08628] [@arxiv:2103.02512] [@arxiv:2206.11210] [@arxiv:2202.06259] [@arxiv:2002.07892]. Fair `k`-center and colorful variants form their
own line [@arxiv:1901.08628] [@arxiv:1907.08906] [@arxiv:2007.04059] [@arxiv:2101.12403] [@arxiv:2002.07682] [@arxiv:2302.09911] [@arxiv:2207.11337] [@arxiv:2205.14358] [@arxiv:2104.12116], as do individual-fairness and
distributional notions [@arxiv:2006.04960] [@arxiv:2002.06742] [@arxiv:2106.14043] [@arxiv:2412.04943] [@arxiv:2006.12589] [@arxiv:2109.04554] [@arxiv:2510.06130] [@arxiv:2412.10923]. Coresets and streaming analyses
extend the same guarantees to large data [@arxiv:1906.08484] [@arxiv:2007.10137] [@arxiv:1812.10854] [@arxiv:2605.13759] [@arxiv:2602.21509] [@arxiv:2602.11500]. Socially-fair and group-representation objectives
give the multi-group versions [@doi:10.1145/3442188.3445906] [@arxiv:2206.11210] [@arxiv:2103.02512] [@arxiv:2002.07892] [@arxiv:2202.01391] [@arxiv:1910.05113] [@arxiv:2006.11009]. **Difference.** All of this work
is worst-case: it proves a ratio and proves it is necessary. We fix the *instance* and ask when the constraint
is inactive; our objects are exact optima `OPT(M)` for every `M`, not an approximation ratio for one `M`.

**Proportional fairness and metric committee selection.** The proportionality principle itself has a
clustering literature [@arxiv:1905.03674] [@arxiv:2310.18162] [@arxiv:2312.10369] [@arxiv:2301.03862] [@arxiv:2502.10068] [@arxiv:2410.23273] [@arxiv:2606.07285] and an approval-voting line [@arxiv:1704.02183] [@arxiv:2211.12820] [@arxiv:2512.24934]. **Difference.** Those define what a "proportional" partition *is* and
approximate it; we take the proportional floor as the constraint and measure the level at which it first
costs.

**The price of fairness.** Price-of-fairness bounds quantify the efficiency lost to a fairness constraint,
for divisible resources [@arxiv:1508.05253], for a bounded number of indivisible items [@arxiv:1406.5722],
and for indivisible goods [@doi:10.24963/ijcai.2019/12] [@arxiv:2402.16145] [@arxiv:2205.10836]; and the "cost
of fairness" appears in algorithmic-decision-making settings [@arxiv:1701.08230] [@arxiv:2606.20461] [@arxiv:2602.05707]. **Difference.** A price-of-fairness number is a supremum over instances. We ask for the
*set of instances* on which the price is exactly zero, and we measure its width rather than its worst case.

**Coverage, diversity and dispersion maximization.** Selecting a `k`-subset that maximises spread among
points is the `max-sum` and `max-min` dispersion problem [@arxiv:cs/0310037] [@arxiv:1203.6397] [@arxiv:1511.02402] [@arxiv:1511.07077] [@arxiv:1607.04557] [@arxiv:1809.09521] [@arxiv:1605.05590] [@arxiv:1607.06203] [@arxiv:2302.07771], now with coresets, matroid constraints and fairness constraints layered on
[@doi:10.1145/2487575.2487636] [@arxiv:2002.03175] [@arxiv:2301.02053] [@arxiv:2502.02530] [@arxiv:2411.02845] [@arxiv:2307.04329] [@arxiv:2002.03256] [@arxiv:2203.01857] [@arxiv:2211.02176]. **Difference.** These works are
our *unconstrained* baseline, and their `max-sum` / `max-min` split is the axis along which we find the cost
law inverts (§5); we import exactly that split and add the floor.

**Submodular maximization under cardinality and matroid constraints.** Constrained selection is the
submodular-maximization problem when the objective is monotone submodular, and its algorithms (cardinality,
matroid, local search, streaming) are the machinery a floor sits on top of
[@doi:10.1137/1.9781611973402.106] [@arxiv:1204.4526] [@arxiv:1101.4450] [@arxiv:1705.06319] [@arxiv:1508.02157] [@arxiv:1007.1632] [@arxiv:2312.14299] [@arxiv:2305.15118] [@arxiv:2304.06596] [@arxiv:1411.0541] [@arxiv:2002.05477] [@arxiv:2102.09679] [@arxiv:2204.13832] [@arxiv:2408.03583] [@arxiv:1811.03093] [@arxiv:1607.07957] [@arxiv:2307.13996]. **Difference.** A proportional floor is a *laminar* constraint, not a cardinality or
matroid one, and our question is about its threshold behaviour rather than about a `(1 - 1/e)`-style ratio.

**Fair allocation, indivisible goods and representation.** The quota-shaped problem appears as max-min fair
allocation and as proportional representation in multi-winner elections [@arxiv:1611.08060] [@arxiv:1704.00222] [@arxiv:1703.01649] [@arxiv:1704.02183] [@arxiv:2202.08713] [@arxiv:1806.00218] [@arxiv:1906.02775] [@arxiv:2410.15738] [@arxiv:2406.15009] [@arxiv:2006.10498]. **Difference.** These allocate *items to agents*; we
select a *subset of a metric space*, so "free" is a geometric statement about the optimum, not a welfare
statement about an allocation.

**Constrained and balanced clustering.** Balancing a partition under lower-bound or coverage constraints is
studied for its own sake [@doi:10.1109/cvprw.2009.5206852] [@arxiv:2009.03078] [@doi:10.1109/tii.2023.3342888] [@arxiv:2401.05502] [@arxiv:2301.08460] [@arxiv:1809.00932] [@arxiv:2112.03183] [@arxiv:2204.00893] [@arxiv:2504.06980]. **Difference.** Those works ask for a feasible balanced solution and its cost; we ask
where the cost *begins*, and show the beginning is a property of the instance that must be computed.

**Selection with quotas and affirmative action.** Quota-shaped selection appears in admissions, sortition and
top-`k` candidate selection [@arxiv:1905.09947] [@arxiv:2006.13699] [@arxiv:1905.10870] [@arxiv:2004.10846] [@arxiv:2007.01202] [@arxiv:2112.14074] [@arxiv:2106.08652] [@arxiv:2010.06986] [@arxiv:2010.04412] [@arxiv:2204.13019] [@arxiv:2110.15503]. **Difference.** These evaluate policies under welfare or fairness objectives on the
selected set; we isolate the *constraint's own* cost on a single instance and measure the region where it is
zero.

**Fairness in machine learning, and the disparate-impact view.** The broader fairness literature supplies the
vocabulary of group harm the quota is meant to bound [@arxiv:1610.08452] [@arxiv:1801.05398] [@arxiv:2310.20673] [@arxiv:2202.09724] [@arxiv:2208.10451] [@arxiv:2102.12258]. **Difference.** These measure outcomes of a learnt
model; we measure the price of a hard constraint on a combinatorial optimum.

**Our own anchoring literature.** This is the third study in a series on the *boundary* of a downstream
requirement — when it stops being free [@arxiv:2607.06709] [@arxiv:2602.11500] — and it keeps that series'
discipline: a construct reduced to a countable statistic, a prior registered before measurement, and a control
that can refute its author.

## 3. Problem formulation and method

**Instance.** A set of `n` points with an integer metric `d` (squared Euclidean after a fixed quantisation,
so all distances and all objective values are integers), a partition of the points into `m` groups, a
selection size `k`, and an objective in a family `F`.

**Objectives.** A **bottleneck** objective, `max-min`: maximise the minimum pairwise distance inside the
chosen `k`-subset. A **sum** objective, `max-sum`: maximise the sum of pairwise distances. Both are standard
in dispersion maximization [@arxiv:cs/0310037] [@arxiv:1203.6397], and they are the two ends of a family —
the smallest order statistic and the sum of all of them — that §5 separates.

**Constraint family.** The floor family is indexed by the **forced-seat count** `M ∈ {0, …, k}`. Given the
group sizes, `ell(M)` distributes exactly `M` seats over the groups in proportion to their size by the
largest-remainder rule, and the constraint is `|S ∩ G_i| ≥ ell_i(M)` for every group `i`. `M = 0` imposes
nothing; `M = k` requires every group to receive its full proportional share. `OPT(M)` is the constrained
optimum value and `OPT(0)` the unconstrained one.

**Definition (zero-cost region).** `M* = max { M : OPT(M) = OPT(0) }`, and the **free width** is `M*/k`.
Every `M ≤ M*` is a quota level that can be imposed at no cost on this instance; `M* + 1` is the first level
that binds.

**Exact computation, two routes.** `OPT(M)` is computed by **complete enumeration** over every feasible
`k`-subset (route 1) — the definition, with no failure mode — and independently by an **integer program**
(route 2) on a *declared* subsample of settings. A third check, the max-sum coordinate identity, is
evaluated on every `max-sum` cell. Across the synthetic study (64 cases, **1152 cells**) the two routes
**never disagree** (0 cross-disagreements), no cell is unresolved, and the only non-optimal cells are
**8 infeasible** floor vectors — a legitimate verdict, never a timeout. The distinction matters: an
infeasible `M` is *measured* (that level admits no selection meeting every floor), an unresolved cell would
be a missing measurement, and only the first occurred. Integer-valued distances make every artefact
byte-identical across runs, which is what lets §10 reproduce it.

**Real corpora.** Three public datasets with real features and a real grouping variable are used: UCI
**Wine Quality (red)** — 1599 rows, 11 numeric predictors, an ordinal `quality` label used as the natural
grouping (`{3:10, 4:53, 5:681, 6:638, 7:199, 8:18}`, sha-256 `4a402cf0…`) — and UCI **Wine** (178 × 13,
three classes) and **Seeds** (210 × 7, 70/70/70), whose labels are genuinely separable in the real feature
space. All are SHA-256-pinned; the instrument re-hashes before it reads.

**Baselines.** Two constrained heuristics are measured on the same cells as the exact optimum: farthest-
first greedy with a feasibility repair, and a 1-swap local search that keeps the constraint satisfied
[@arxiv:1603.09535] [@arxiv:1607.06203]. §6 is about what it means to compare to them.

## 4. The zero-cost region: how wide it is (P1′)

**Registered prior P1′.** *Before measurement:* the free region is non-empty and its width is a non-trivial
fraction of `k`, because forcing a proportional share into large groups rarely changes the unconstrained
optimum; the first binding quota satisfies `M* > 1`.

**Result.** P1′ is confirmed, and more strongly than the prior expected.

| study | cases | `M* > M_first` | median free width `M*/k` | whole quota free |
|---|---|---|---|---|
| synthetic, setting A (`n=18, m=3, k=9`) | 32 | **32/32** | 0.833 | 11 |
| synthetic, setting B (`n=20, m=4, k=10`) | 32 | **30/32** | 0.800 | 8 |
| real, Wine Quality groups = quality bins | 24 | **24/24** | 0.900 | 5 |

The free width is not a corner case. Across the 64 synthetic cases the median is **0.80** and the whole
quota is free in **19 cases (30 %)**; on the real corpus the median is **0.90** and the whole quota is free
in **5 of 24 cases (21 %)**. By synthetic family, the median free width separates the geometries:

| family | median `M*/k` |
|---|---|
| clustered (2-D, well separated) | 0.667 |
| unequal group sizes (2-D) | 0.789 |
| uniform (5-D) | 0.894 |
| uniform (2-D) | 0.944 |

![Free width by synthetic family and on the real corpus](figures/fig2_free_width.png)

**Figure 2.** The zero-cost region by synthetic family and on the real corpus. Bars are the median free
width `M*/k`; the dashed line is the whole quota. Every family is well above zero.

The ordering (Figure 2) is the interpretable one: when the groups are geometrically separated, satisfying a
proportional floor forces selections into each cluster and costs freedom sooner; when the groups are
interleaved in a higher-dimensional cloud, the same floor is absorbed by the unconstrained optimum.

**Reading.** On these instances a practitioner can force between two-thirds and the whole of a proportional
share of the `k` seats at zero cost. The first binding quota being free in 86 of 88 cases is the paper's
central positive claim: the interesting region of a group quota is usually *inner*, not at the margin, and
the constraint is free exactly up to the level where the groups' geometry forces the issue.

## 5. What the cost curve looks like above the threshold (P3, inverted)

**Registered prior P3.** *Before measurement:* the bottleneck objective is the fragile one. A `max-min`
optimum is fixed by a single worst pair, so a floor that removes that pair should break the value abruptly;
a `max-sum` optimum aggregates many pairs, so it should degrade gradually. The registered direction was
therefore `beta_maxmin > beta_maxsum` — a steeper exponent for the bottleneck.

**Result: the measurement is the opposite, and the mechanism favours the inversion.** Above `M*`, fit
`loss ~ (M - M*)^beta` on the levels with strictly positive loss:

| objective | fittable cases | median exponent `beta` | shape |
|---|---|---|---|
| `max-min` (bottleneck) | 5 | **0.000** | step / plateau |
| `max-sum` (sum) | 17 | **0.92** | slope (near-linear) |

The `max-min` curve is **flat** above `M*` in every case with enough points to fit: once the free levels
are exhausted, the bottleneck value drops to a plateau and stops moving, because it is determined by a
single order statistic and there is nothing else to lose. The `max-sum` curve is a **slope** at `beta≈1`:
it accumulates many small substitutions, so it grows smoothly with the number of forced seats. The
mechanism we registered pointed the wrong way: a bottleneck is *rigid* precisely because it is one order
statistic, and a sum is *gradual* precisely because it is many.

![Cost above the free region](figures/fig1_cost_curves.png)

**Figure 1.** The cost above `M*` for every case with at least two points above the threshold. Blue
(`max-sum`) curves rise approximately linearly; red (`max-min`) curves reach a plateau and stay flat —
the step-versus-slope contrast of the table above.

**Registered replacement.** `beta_maxsum ≈ 1` (linear) and `beta_maxmin ≈ 0` (step). This is a strong-
novelty outcome in the sense of the journal's bar — a registered, mechanism-anchored prior contradicted by
measurement — and §8 records it as such.

**Boundary.** The substitution the real corpora impose is coarser: on the Wine Quality corpus only 7 of 24
cases have ≥3 points above `M*`, and there the `max-min` fit aggregates to `beta = 0.000` while `max-sum`
aggregates to `0.178` (with individual values 0.744 and 0.570). The replacement survives in sign on real
data; it is simply underpowered where the free width is so large that few levels remain to fit.

## 6. The baseline confound is objective-specific (P4)

A natural way to state "the cost of a quota" is against a heuristic: run farthest-first greedy, run the
constrained optimum, and call the difference the cost of fairness. That comparison is only the constraint's
cost if greedy has already reached the unconstrained optimum. It often has not.

**Result.** On the unconstrained instance, farthest-first greedy is exact in a *minority* of bottleneck
cases and in almost all sum cases:

| substrate | `max-min` greedy exact | `max-min` median gap | `max-sum` greedy exact | `max-sum` median gap |
|---|---|---|---|---|
| synthetic (32 cases) | **7/32** | 17.1 % | **29/32** | 0.0 % |
| real, Wine Quality (12 cases) | **4/12** | 1.7 % | **9/12** | 0.0 % |
| real-row wide sweep (160 cases) | 100/160 | 0.0 % | 120/160 | 0.0 % |

On a bottleneck objective, then, an empirical "cost of fairness" measured against greedy is **dominated by
approximation error** — the greedy baseline is short of the unconstrained optimum before any quota is
applied, with a median relative gap of 17 % and a maximum of 46.9 % on the synthetic family. On a sum
objective the same comparison is sound. P4 is confirmed as an objective-specific confound.

**Boundary (found on the sweep).** The confound weakens as the groups become well separated: on the
real-row wide sweep (Wine and Seeds, both with genuinely separable labels) the median greedy gap collapses
to **0.0 %** for both objectives and the exact counts rise to 100/160 and 120/160. So the P4 lesson is not
"greedy is always a bad baseline"; it is that **whether it is a valid baseline is itself an empirical
question, object-specific and instance-dependent**. A paper that measures a cost of fairness against greedy
on a bottleneck objective without checking this is reporting an approximation gap as a fairness cost.

## 7. The predictor that is not there (P2′)

**Registered prior P2′.** *Before measurement:* the free width is predictable out of sample by a cheap proxy
that does **not** solve the constrained problem — so a practitioner could estimate their free region without
running the exact computation. The candidate was a solve-free geometric proxy: the ratio of mean
within-group to mean between-group distance (the groups' *alignment* in the metric).

**Result: refuted — and the refutation is only interpretable because the test's ranges were measured
first.** We built a real-row sweep that holds the metric fixed and varies only the partition, sweeping the
alignment from label-aligned to label-blind. Across **320 cells** the predictor's input spans
**0.183–1.037** (spread **0.854**) and the output — the free width — spans **0.000–1.000** across **9
distinct values** (spread **1.000**). Both ranges are wide; a negative here is a finding, not an artefact of
a dead variable.

![Alignment versus free width](figures/fig3_alignment.png)

**Figure 3.** The predictor against the outcome on the 320-cell real-row sweep: group-metric alignment
(x) versus free width (y), both corpora overlaid. The cloud is a rectangle — no relation — and the
pooled Spearman is printed in the title.

The predictor fails on three independent readings:

| reading | value |
|---|---|
| pooled Spearman (average-rank, 320 cells) | **+0.108** (Wine +0.119, Seeds −0.006) |
| MAE vs a constant predictor | **0.1675** vs **0.1649** (it *loses*) |
| within-group ordering (alignment order = width order) | **1 of 32** groups |

The pooled correlation is not merely weak, it is a **stride across strata**, not a relation within them.
Splitting by objective shows why: inside `max-sum` the candidate is *identically degenerate* (`n_optima = 1`
in all 160 cells; a max-sum optimum is unique), so it cannot predict there, while inside `max-min` it is
**non-transportable** (Seeds `rho = +0.488` but Wine `rho = +0.161` with a negative MAE gain). A statistic
that is constant in one stratum and inverts in another is not a predictor. We tested three further cheap
candidates — a solve-free alignment proxy, the greedy gap at `M = 0`, and the unconstrained optimum's own
degeneracy — and **none has a positive MAE gain in every stratum**.

**Reading.** The free width must be computed, not predicted. This sharpens the practical rule from §4: the
procedure is to solve the unconstrained problem and then walk `M` upward until the optimum first moves —
cheap, exact, and not replaceable by an instance statistic. It also makes the paper's negative result a
clean one: the object is not merely unpredicted by *our* proxy, it is unpredicted by any of the cheap
statistics we could construct, on input and output ranges wide enough to have found a relation if one
existed.

## 8. Registered prior beliefs, against their outcomes

Each prior was recorded before measurement. Verdicts:

| prior | registered direction | outcome |
|---|---|---|
| **P1′** | the free region is non-empty and its width is a non-trivial fraction of `k` | **CONFIRMED** (32/32 and 30/32 synthetic; 24/24 real; median 0.80–0.90) |
| **P2′** | a cheap, solve-free proxy predicts `M*/k` out of sample | **REFUTED** (pooled ρ +0.108 on a 0.854-wide input; loses to the constant; 1/32 within-group) |
| **P3** | `beta_maxmin > beta_maxsum` — the bottleneck breaks abruptly | **REFUTED AND INVERTED** (`max-min` median `beta = 0.000`, `max-sum` 0.92) |
| **P4** | a greedy baseline confounds the measured cost of fairness | **CONFIRMED as objective-specific** (7/32 vs 29/32 synthetic; 4/12 vs 9/12 real), with a boundary (weakens on separable groups) |

One prior was replaced *before* the deciding runs, and the replacement is recorded here for honesty: an
initial registration used the total forced-seat fraction `F` as the constraint index, but `F` is a
re-parameterisation of `M` that changes nothing — any set achieving `OPT(0)` is, definitionally, an
unconstrained optimum — so the "prior" was a tautology and was replaced by the forced-seat count `M`, whose
grid is the one that actually binds. A prior that follows from a definition is not falsifiable and does not
belong in this table as evidence.

The P3 inversion is the paper's strongest novelty signal: a registered, mechanism-anchored prediction was
contradicted by measurement, and the mechanism was re-derived from the result rather than the result from
the mechanism.

## 9. Threats to validity

**Scale.** The exact study is at `n = 18–20`, `k = 9–10`, `m = 3–4` — small enough that complete
enumeration is possible (which is the point: the objects are exact, not approximated). Whether the free
width *grows* or *shrinks* with `n` at fixed group geometry is not established here; the construct is
computable at any `n` for which the constrained problem is solvable, and the claim we make is about the
*width of the free region*, not about its asymptotics.

**Objectives.** We study two objectives, chosen as the two ends of the order-statistic family. Intermediate
objectives (`k`-centre-style, ordered-median [@arxiv:1711.08715], hybrid [@arxiv:2407.08295]) are not
measured; the step-vs-slope law is a claim about bottleneck vs sum, and the boundary between them is left
open.

**Real corpora.** The real grouping variable is a natural one (an ordinal quality label; class labels), not
a fairness-sensitive attribute. The study is about the *behaviour of the constraint* on real metric
structure, not about a deployed fairness decision; the three corpora were chosen because their groups are
genuinely (non-)separated, which is what the predictor test needed.

**The predictor negative.** We tested four cheap statistics, not all possible ones. The claim is the
defensible weaker one — *these* candidates fail, on a sweep whose ranges were measured to be wide — not that
no statistic could ever predict the free width.

**Why still worth publishing.** The positive result (a wide, exact, cheaply-located free region) and the
inverted cost law are both instance-level facts about a construct the worst-case literature does not
measure, established on exact optima with two agreeing routes and a byte-reproducible pipeline. The
negative predictor result is a design constraint on anyone who would estimate the free region instead of
computing it, which is the natural next thing to try.

## 10. Reproducibility

Every number in this paper is re-derived from the instrument artefacts by one script, and the whole study
is reproduced by one command:

```
bash reproduce.sh           # fast: pins + certificates + canonical re-derivation -> ALL GREEN (7 steps)
bash reproduce.sh --full    # adds the instrument re-runs; requires BYTE-IDENTICAL artefacts (10 steps)
```

`canonical.py` re-derives every headline number from `spike_v3/v4/v5_results.json` and names the source of
each, so no number in the manuscript is retyped; `canonical.py --check` asserts the headline claims (the
strict `M* > M_first` counts, the wide-sweep ranges, the near-zero pooled correlation, the P3 exponents).
Each instrument and analyser carries certificates exercised on a **healthy and a mutated** object, so a
check that cannot fire is caught. The three instruments regenerate **byte-identical** on a re-run
(11m08s). Corpora are SHA-256-pinned and re-hashed before every read. All artefacts are integer-valued,
which is what makes byte-identity possible; the environment is Python 3.9 with numpy, and no random state
crosses a run boundary.

<!--REFERENCE-LIST-->
