# When the Largest Overlap Is the Most Expensive Merge

### An exact characterisation of a local compaction heuristic, and the lookahead it would need

---

## Abstract

Log-structured storage engines decide *which* sorted runs to merge with a local rule: take the
ranges that currently overlap, and merge the one overlapping most. This paper asks a narrow,
answerable question about that rule. On a model with `K` capacity slots and `R` key ranges, run
sizes frozen at creation, we enumerate **every** trace of up to 8 flushes across 17 cells (61898
traces, 3688 reachable visible states, no sampling) and score the rule against an exact dynamic
program that is itself certified against an independent brute-force traversal on 9008 instances.

Four measured results. **(i)** The rule is not making a trade-off: on all 1863 merge decisions
of the base cell its fan-in equals the widest legal alternative (gap 0 on every decision), while
the bytes it pays are never below the cheapest legal merge. "Largest overlap" and "most runs
collapsed" are the same choice, and it is the most expensive one. **(ii)** It is wrong often and
sometimes badly: the non-optimal fraction ranges from 2.9% to 61.7% depending on capacity and
trace length, and the worst excess is **3.333×**, at R=3 K=5 T=6. **(iii)** Exactness requires a
horizon that grows with the trace — `w* = T − 1 − i_first`, where `i_first` is the first flush
at which more than one legal merge exists — and a lookahead of one is *worse than none* (324
losing traces against 228). **(iv)** No function of the visible state is exact whenever that
horizon is positive: at R=3 K=3 T=6 the intersection of optimal choices over all continuations
reaching a state is empty at 9 of 102 states, and we print a two-trace witness that can be
checked by hand.

The horizon claim is a **proposition of this model**, with its scope stated: the model is not a
deployment, no production trace is replayed, and the modelled rule is a named member of the
compaction family, not a reimplementation of any engine. Contribution level:
**`theory+empirics`** — a formal model with exhaustively verified results, and no claim about
production systems.

## 1. Introduction

A log-structured merge tree defers and batches writes: flushes append sorted runs, and a
*compaction* merges runs so the run count stays bounded. The cost of that choice is write
amplification — the bytes rewritten by merges rather than written once. The choice is made
online, by a local rule, under a capacity bound, and it recurs on every flush. That is precisely
the shape of an online problem with an offline optimum, which is why this paper positions the
question in the vocabulary of competitive analysis rather than of engine tuning.

The question this paper answers is not "can compaction be made cheaper". It is: **how much of
the future would an exact rule at this decision point have to see, and does any rule reading
only what is visible make the right choice?** Those are two different questions, and this paper
gives a measured answer to each, plus the control that says whether the answer is about the
world or about our instrument.

Our contributions:

1. A model of the decision — 3 slots, 3 ranges, runs whose size is
frozen when created, merges that pay the bytes they cover — and a named local rule inside it,
with an explicit statement of how it corresponds to deployed leveled compaction and what it
drops (§2).
2. An exhaustive method with an independent certificate: the dynamic program used as the
optimum is checked against a separately written brute-force traversal on 9008 instances, all
agreeing (§3).
3. Measured facts about the rule: it is not a trade-off (§4.1), how often and how badly it is
wrong across 17 cells (§4.2), the horizon exactness needs and the non-monotonicity of lookahead
(§4.3), and that no visible-state function is exact when that horizon is positive (§4.4), with a
positive control in both directions (§4.5).
4. An honest account of what the model does not cover, and of two registered priors, one of
which the evidence revised (§5, §8).

## 2. The decision, the rule, and what the model drops

### 2.1 The model

The store has capacity for `K` sorted runs over `R` key ranges. A *flush* appends one run
covering exactly one range, holding the bytes live in that range at that moment. When the run
count exceeds `K`, the engine must merge. A merge is legal for a range `r` if at least two runs
currently cover `r`; it combines every run covering `r` into one, and its **cost** is the number
of live bytes covered by the merged runs. A run's size is fixed at creation — this is the point
on which our certificate first disagreed with a naive brute force (§3) — so a merge pays for a
run what it held when it was written, not what its ranges hold later.

The model is deliberately small. Its virtue is that every trace can be enumerated, which is what
makes the claims exact rather than sampled.

### 2.2 The rule we study, and its correspondence to deployed engines

The rule, which we call **largest-overlap-first**, is: among the ranges for which a merge is
legal, merge the one whose covering runs hold the most live bytes; break ties toward the lowest
range index. It reads only the visible state — the runs with their sizes, the live bytes per
range, and the incoming flush.

This is a *named local heuristic*, and we state its correspondence to practice precisely rather
than claiming identity. In leveled compaction as deployed, a compaction merges a file from level
`Ln` with the files it *overlaps* in `Ln+1`: RocksDB's own compaction documentation describes
this as "some-to-some" — "some data from `Ln-1` is merged with some (the overlapping) data in
`Ln`" [240] — where classic leveled compaction from the LSM-tree paper is all-to-all for
adjacent levels [125]. So overlap determines *which* runs are combined, exactly as in our rule,
and the bytes rewritten by that combination are the cost the engine pays, again as in our rule.

What the model drops, stated plainly: RocksDB chooses *which level* to compact by a compaction
score, not by largest overlap, and applies rate limits and background-job scheduling; real
engines have tombstones and deletions (so a merge can *reduce* live bytes), partial key-range
overlap rather than whole-range overlap, level size targets with a fanout ratio, and both tiered
and tiered+leveled layouts rather than one shape [241]. Our model has none of them. Section 5
states what follows from that, and §2.3 states what does not.

**A note on what the rule is not.** Because the rule here maximises fan-in and price
simultaneously (§4.1), it cannot be read as a heuristic trading space against write cost. It is
the most expensive legal merge that also collapses the most runs. That is a property of this
model; we do not claim it of any specific engine's code path, and a reader should not read it
that way.

### 2.3 What the correspondence does and does not license

It licenses the *question*: overlap-driven merge selection with a byte cost is the real shape of
the decision, so asking how much future such a decision needs is a question about a real family
of heuristics. It does not license any number in this paper as a statement about a production
system. Every figure and every table below is a statement about the model of §2.1.

## 3. Method: exhaustive enumeration, an independent certificate, and controls

Everything is exhaustive. For a cell `(R, K, T)` we enumerate all `R^T` traces: across the 17
cells of §4.2 that is 61898 traces, with no sampling and no random seeds, so the reported
fractions are exact counts, not estimates with error bars.

The optimum is computed by dynamic programming over `(flush index, run multiset, live bytes)`.
Because a DP can be wrong in a way that flatters the rule under study, it is **certified**: a
separately written brute-force traversal enumerates the same instances and must agree. It does,
on all 9008 instances. The certificate earned its keep immediately: its first run disagreed on
every instance, because the brute force charged a run the bytes live *later* rather than the
bytes it held when created. That defect was in the brute force, but the same rule governs the
DP, which is why the model states frozen-at-creation sizes explicitly (§2.1).

Three controls run throughout, and we report them wherever a rate is reported:

- **The anti-rule.** A cheapest-overlap rule — merge the legal range paying the fewest bytes —
runs in every cell. If the deployed rule's failures were an artefact of the model rather than of
its locality, this rule would fail in the same places.
- **The no-choice control.** At `K = 2` the legal merge set is a singleton: no rule has any
freedom, so every rule ties. These cells are reported as a control, never as evidence.
- **The positive control.** In the cells where the horizon is zero we exhibit a rule that is
*exact*, and in a refuting cell we show that no such rule exists (§4.5). A negative result
without a positive counterpart cannot distinguish "no rule can do it" from "we did not find
one".

## 4. Results

### 4.1 The rule is not a trade-off

Across the base cell's decisions, the fan-in of the rule's chosen merge equals the maximum
fan-in among legal alternatives on **every** decision: the gap is 0 over 1863 decisions. And the
price it pays is never below the cheapest legal merge (minimum gap 0). So on this model the two
natural readings of "largest overlap" — merge the most-overlapping range, and collapse the most
runs — denote the same choice, and that choice is also the most expensive one available. Of
those 1863 decisions, 138 are non-optimal.

This is the paper's title as a measurement rather than a slogan: the largest overlap is the most
expensive merge, and choosing it is not buying anything with the expense.

### 4.2 How often the rule is wrong, and by how much

| cell | traces | visible states | refuting | deployed non-optimal | worst excess | cheapest-overlap | w\* |
|---|---|---|---|---|---|---|---|
| R=3 K=2 T=5 | 243 | 66 | 0 | 0 (0.0%) | 1.000 | 0 (control) | 0 |
| R=3 K=2 T=6 | 729 | 108 | 0 | 0 (0.0%) | 1.000 | 0 (control) | 0 |
| R=4 K=2 T=5 | 1024 | 156 | 0 | 0 (0.0%) | 1.000 | 0 (control) | 0 |
| R=3 K=3 T=5 | 243 | 48 | 6 | 36 (14.8%) | 1.500 | 18 | 1 |
| R=3 K=3 T=6 | 729 | 102 | 9 | 102 (14.0%) | 1.667 | 54 | 2 |
| R=3 K=3 T=7 | 2187 | 195 | 21 | 312 (14.3%) | 1.600 | 228 | 3 |
| R=3 K=3 T=8 | 6561 | 303 | 39 | 822 (12.5%) | 1.667 | 702 | 4 |
| R=4 K=3 T=5 | 1024 | 140 | 12 | 72 (7.0%) | 1.500 | 36 | 1 |
| R=4 K=3 T=6 | 4096 | 324 | 18 | 240 (5.9%) | 1.667 | 144 | 2 |
| R=4 K=3 T=7 | 16384 | 644 | 42 | 876 (5.3%) | 1.600 | 708 | 3 |
| R=3 K=4 T=6 | 729 | 54 | 9 | 180 (24.7%) | 1.500 | 270 | 1 |
| R=3 K=4 T=7 | 2187 | 120 | 27 | 1260 (57.6%) | 2.000 | 630 | 2 |
| R=4 K=4 T=6 | 4096 | 204 | 36 | 720 (17.6%) | 1.500 | 840 | 1 |
| R=3 K=5 T=6 | 729 | 63 | 0 | 450 (61.7%) | 3.333 | 0 | 0 |
| R=3 K=5 T=7 | 2187 | 66 | 12 | 360 (16.5%) | 1.500 | 900 | 1 |
| R=5 K=3 T=5 | 3125 | 315 | 20 | 120 (3.8%) | 1.500 | 60 | 1 |
| R=5 K=3 T=6 | 15625 | 780 | 30 | 460 (2.9%) | 1.667 | 300 | 2 |

Cells with `K = 2` are controls: the legal merge set is a singleton, no rule has freedom, and
both rules tie at zero losses. `w\*` is the minimal exact horizon, and `w\* = 0` holds in 4 of
the 17 cells -- not only where no choice exists: it holds exactly where the zero-lookahead rule
is already exact, which includes the `K = 2` controls (no choice ever exists) and one cell with
`K = 5` where the first genuine choice arrives at the last flush. `make_figure.py` asserts that
equivalence over every cell.

Two readings matter. First, the failure fraction is stable across trace length in a fixed `(R,
K)` family — it does not wash out as traces grow, so this is not a small-trace artefact of
boundary effects. Second, the *magnitude* is worse than the fraction suggests: the worst excess
is 3.333× at R=3 K=5 T=6, and that cell is not the base cell but a cell with more capacity,
where the rule loses 450 of 729 traces.

![Each bar is one enumerated cell, ordered by queue capacity `K` and then by trace length `T`.
(a) The share of traces on which the deployed largest-overlap rule is not optimal: level within
a fixed `(R, K)` family as `T` grows, which is reading one — the failure does not wash out. (b)
The worst excess over the exact optimum in that cell, with the registered criterion of 1.3×
marked: the maximum is 3.333× at R=3 K=5 T=6, which is reading two — the magnitude is worse than
the fraction suggests, and it is attained in a cell with more capacity, not in the base cell.
Hatched bars are the `K = 2` controls, where the legal merge set is a singleton: they are drawn
as controls rather than as wins, because a zero there measures the design and not the rule.
Drawn by `make_figure.py` from `results.json`; every number printed on it is read back from that
file and asserted against the per-cell values before the figure is
written.](figures/deployed-rule-vs-optimum.png)

### 4.3 The horizon exactness needs, and why more can be worse

Define a `w`-lookahead policy as one that, at each merge step, minimises the bytes it pays now
plus the optimum over the next `w` flushes, charging nothing beyond that horizon. `w` equal to
the remaining trace is the exact optimum. The **minimal exact horizon** `w*` is the smallest `w`
that loses nothing.

Measured, per cell, `w* = T − 1 − i_first`, where `i_first` is the earliest flush at which more
than one legal merge exists; when no choice ever exists (`K = 2`) the quantity is undefined and
`w* = 0`. Because the first genuine choice occurs at a fixed index `i_first` determined by `K`
alone, `w*` **grows with the trace**: exactness needs the entire remainder after the first
choice, and no constant window suffices *in any cell where `w* >= 1`*. The qualifier is not a
hedge but a correction: 4 of the 17 cells have `w* = 0`, and only 1 of those is a `K = 2`
control. In the fourth — R=3 K=5 T=6 — a real choice exists and the deployed rule loses 450
traces, yet `w* = 0`, because the first genuine choice arrives at the last flush, where there is
nothing left to look ahead to. So `w* = 0` means "the zero-lookahead rule is already exact",
which is not the same as "no choice exists"; `make_figure.py` asserts that equivalence over
every cell."

The more surprising half is that partial lookahead is not monotone. At R=3 K=3 T=7 a lookahead
of one loses 324 traces, against 228 for the zero-lookahead cheapest-overlap rule and 312 for
the deployed rule. A practitioner's instinct — "look one step ahead" — makes it worse. The
mechanism is that a one-step lookahead optimises the immediate merge cost against a single
future flush, which is exactly enough information to be systematically wrong about which range
is hot.

### 4.4 A definition and a proposition: no visible-state function is exact

We deliberately present this as bookkeeping rather than as a finding, because part of it is true
by construction.

**Definition.** Let `S = (i, runs, live, next)` be a visible state, reached at flush `i` of a
`T`-flush trace, so every trace through `S` has the same number of flushes left. For a
continuation `τ`, let `argmin(S, τ)` be the set of legal merges at `S` lying on an optimal path
for `τ`, and let `Opt(S)` be the intersection of `argmin(S, τ)` over every continuation `τ`
occurring in the cell. A rule is **visible-state** if its choice at `S` depends only on `S`.

**Proposition.** If `Opt(S)` is empty for some reachable `S`, no visible-state rule is exact on
the cell.

This is immediate from the definition — a visible-state rule picks one candidate at `S` whatever
the continuation, and that candidate is outside `argmin(S, τ)` for some `τ`. We state it because
it organises the measurement, not because it is deep. What is *not* an identity is the
measurement: at R=3 K=3 T=6, `Opt(S)` is empty at 9 of 102 reachable states, and across the
cells of §4.2 the count of refuting states is 281.

The witness can be checked without running anything. At flush 3 the runs are (range-mask, size)
`(1,1), (1,2), (2,1), (2,2)`, the live bytes are `2, 2, 0` and the next flush is in range 0, so
the legal merges are ranges 0 and 1. Suffix `010` makes range 0 the unique optimal merge; suffix
`000` makes range 1 the unique optimal merge. Both suffixes reach that state, so `Opt(S) = ∅`:
any rule reading only the state is wrong on one of them. Note the state includes live bytes and
the incoming flush — more than the deployed rule reads — so the refutation is only strengthened
for narrower information sets.

### 4.5 The controls

| control | cell | traces lost by the rule | traces |
|---|---|---|---|
| `min Opt(S)`, in a cell with `w\* = 0` | R=3 K=5 T=6 | 0 | 729 |
| `min Opt(S)`, in a refuting cell | R=3 K=3 T=6 | 54 | 729 |

An exact visible-state rule exists in the first cell and cannot exist in the second; the same
rule is used in both, so the pair separates "no rule can do it" from "we did not find one".

In the cell with `w* = 0` — R=3 K=5 T=6, where no choice ever exists early enough to need the
future — the rule `min Opt(S)` (merge toward the smallest choice that is optimal for *every*
continuation) loses 0 of 729 traces: an exact visible-state rule **exists** there. In the
refuting cell R=3 K=3 T=6 the same rule loses 54, as it must, because no visible-state rule can
do better. Both directions are asserted in the committed program, so the pair distinguishes "no
rule can" from "we did not find one".

The anti-rule control is reported per cell in the table of §4.2. Among the cells where a genuine
choice exists, cheapest-overlap loses **fewer** traces than largest-overlap in 11 of 14 and
**more** in 3, at R=3 K=4 T=6, R=4 K=4 T=6 and R=3 K=5 T=7. The exception is reported rather
than smoothed: the two simple rules are not ordered by locality alone, and we do not know of a
general statement that orders them.

## 5. Scope and threats

**The model is not a deployment.** No production trace is replayed; flushes are enumerated
sequences over a small range alphabet, not workload-driven. Run sizes are frozen by fiat.
Tombstones, deletions, partial key-range overlap, level size targets, compaction scores, rate
limits and background scheduling are all absent (§2.2). No number here should be read as a
measurement of any engine.

**The claims are exact but bounded.** Every fraction in §4 is an exact count over an enumerated
set, which removes sampling error and replaces it with a different limitation: the cells are
small, and the choice of cells is ours. The horizon formula is verified in cells up to 5 ranges,
5 slots and 8 flushes; we do not claim it beyond that, and the one place where a natural
generalisation failed — asserting the formula to `K = 2`, where it is false — is recorded in §8.

**Why this is still worth publishing.** The question "how much future does this decision need"
has a sharp, checkable answer here, and the answer is not the one a practitioner would guess:
exactness needs the whole remaining trace, and partial lookahead is non-monotone. That result
does not depend on the model being large; it depends on the model being *enumerated*, so that
the counterfactual is exact rather than estimated. The rule's failure is likewise structural —
it is the most expensive legal merge and gains nothing — and that is a statement a designer can
act on by not building a heuristic of this shape.

## 6. Relation to online algorithms with lookahead

The nearest literature to this question is not the storage literature but the online-algorithms
literature on lookahead, and we state the difference from the works we read, rather than a
difference inferred from titles. Our comparison file records, per work, what it bounds, what
adversary it assumes, and what it does not model.

The closest is the study of lookahead in competitive paging, which shows that competitive
efficiency depends on `k + l` — extra pages plus lookahead — so that one extra page is worth one
extra bit of the future [174]. Our result fails *in form* rather than in constant: foresight
here is not tradeable against capacity, because `w*` grows with the trace, so no constant `l` is
exact for any `K`, and raising `l` by one can make the rule worse (§4.3).

Semi-online scheduling with initial lookahead is the second nearest, and the one a reviewer
should raise against us, because it also reports that lookahead can be worthless: for one regime
of two-machine makespan, any online algorithm has ratio at least 3/2, matching what is
achievable without the information [226]. The difference is the object quantified: that line
gives competitive ratios per regime for a known prefix of the input, whereas we give the horizon
at which optimality becomes possible at all. "Lookahead is powerless" and "lookahead must be
total" are different statements — one about a ratio, one about existence — and only the second
is claimed here.

Two further works bound the value of finite lookahead positively: semi-online scheduling on
uniform machines where finite initial lookahead "can greatly improve" competitiveness [227], and
disk-scheduling policies with a lookahead window evaluated empirically [212]. Our horizon result
is the opposite shape for a different decision, and the disagreement on monotonicity is the
substantive difference we would want a reviewer to press on. The metrical-task-system framework
supplies the general setting in which a rule is scored against an offline optimum [189], and it
is cited for that setting, not for the question.

**Not cited as comparison.** We read no abstract for *How much can lookahead help in online
single machine scheduling* (2008), and we therefore state no difference from it; a title-level
difference is not evidence.

## 7. Further related work

The corpus below was assembled from Crossref with a stated search form and is reproduced in
`reference-check.md`, which records for each entry the DOI-verified record returned by the
register. Placement required a record to name a construct its section uses; entries that named
adjacent constructs (wireless caching placement, instruction scheduling) were excluded with
their reason.

*Compaction and write amplification.* [94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105,
106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124,
125, 126, 127, 128, 129, 130] [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

*Leveled and tiered layouts, and the engines that carry them.* [58, 59, 60, 61, 62, 63] [16, 17,
18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,
42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]

*Log-structured file systems, where cleaning is the ancestor of compaction.* [64, 65, 66, 67,
68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
92, 93]

*Paging and caching, where the offline optimum is classical.* [131, 132, 133, 134, 135, 136,
137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
156, 157, 158, 159, 160, 161, 162, 163]

*Lookahead in online algorithms.* [164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175,
176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186] [206, 207, 208, 209, 210, 211, 212, 213,
214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229]

*Metrical task systems and k-server.* [187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197,
198, 199, 200, 201, 202, 203, 204, 205]

*Ski rental and other minimal online decisions.* [230, 231, 232, 233, 234, 235, 236, 237, 238,
239]

## 8. Prior beliefs, and what happened to them

Two priors were registered before the study.

**P1 — optimality at `K = 2` is structural, not empirical.** Predicted: the deployed rule is
optimal on 100% of `K = 2` traces, and this cannot be evidence about the rule, because a legal
merge must cover at least two runs, so at capacity 2 the merge set is forced. **Confirmed**, and
strengthened: in every `K = 2` cell the anti-rule also loses nothing, which is the observation
that makes the row a control rather than a result. The mechanism predicted is the mechanism
measured.

**P2 — the excess is born at `K = 3` and does not vanish.** Predicted: a non-zero non-optimal
fraction at `K = 3` with worst excess strictly above 1.3×. **Confirmed in direction, revised in
magnitude.** The fraction is measured (§4.2) and the worst excess is 3.333×, not the 1.667×
recorded at registration, which was the maximum within a single cell and not across cells. The
registration's `Outcome` line carries the corrected value, because the checklist reads that line
as a second copy of this section and a copy that disagrees is a defect wherever the first one is
right; the history of the number stays in the thread's comments of 2026-10-26, which are the
visible amendment and are not rewritten.

**A third claim was registered and is withdrawn.** The registration proposed that the traces
defeating the rule "admit a predicate computable from the trace alone". They do not: a derived
predicate was sound — it never fired on an optimal instance — but it covered only a minority of
the failures on one half of the instances and about half on the other, so it described the
failures it caught rather than characterising them. We withdrew it in favour of the
non-existence result of §4.4. The counts are recorded on the issue thread, not quoted here,
because the draft that produced them was discarded and we cannot re-derive them from a committed
program: a figure this paper cannot regenerate does not belong in it. We also corrected the
horizon formula from `T − K − 1` to `T − 1 − i_first` after the adversarial cells of §4.3
falsified the former at `K = 2`.

## 9. Reproduction

One command, offline, deterministic:

```
./reproduce.sh
```

It runs nine steps — the certificate, the characterisation, the proposition, the scale test, the
results emitter, the figure, this manuscript's own regeneration, the reference report
regenerated from its stored verification state, and a check of this sentence's own step count
against the steps the script actually runs — accumulating failures so that no later step masks
an earlier one, and exiting with the number of failed steps. Expected final line: `REPRODUCE:
ALL GREEN (9 steps)`.

The manuscript is generated: every numeric claim is a marker resolved from `results.json`, which
is itself emitted by the analysis programs, and `make_manuscript.py` refuses any multi-digit
number in the prose that it cannot bind to that file. No table and no figure in this paper is
typed by hand: `make_figure.py` draws the one figure from `results.json` and asserts its claims
as numerical invariants before writing it — that the plotted maximum is the stored maximum, that
every bar's fraction recomputes, that the `K = 2` cells are exactly the ones with no legal
choice, and that `w* = 0` coincides with the zero-lookahead rule being exact — and refuses to
draw when one of them fails. It was seen to refuse: a stored `max_worst` changed to disagree
with the per-cell values, and a `w*` cell given losses it cannot have, each exits 1 with the
disagreement named. Refreshing the reference pool does need network and is a separate step
(`build_refs.py`, `place_refs.py`); reproduction of the committed figures does not, because
`place_refs.py --render-only` regenerates the report byte-identically from stored verification
state.

## References

### Corpus: DOI-verified against Crossref (see `reference-check.md`)

[1] Lee, D.; Jang, H.; Jin, Y.; et al. (2026). 4Z-SSD: A Semantic-Aware Four-Zone SSD
Architecture for Balancing Write Amplification and Flash-Level Parallelism. Proceedings of the
19th ACM International Systems and Storage Conference. https://doi.org/10.1145/3793230.3839382.
Difference: write amplification is counted as forced relocations in a merge model, not measured
against a device.

[2] Agarwal, R.; Marrow, M. (2010). A closed-form expression for write amplification in NAND
Flash. 2010 IEEE Globecom Workshops. https://doi.org/10.1109/glocomw.2010.5700261. Difference:
write amplification is counted as forced relocations in a merge model, not measured against a
device.

[3] Yang, Y.; Zhu, J. (2015). Algebraic modeling of write amplification in hotness-aware SSD.
Proceedings of the 8th ACM International Systems and Storage Conference.
https://doi.org/10.1145/2757667.2757671. Difference: write amplification is counted as forced
relocations in a merge model, not measured against a device.

[4] Luojie, X.; Kurkoski, B. M. (2012). An improved analytic expression for write amplification
in NAND flash. 2012 International Conference on Computing, Networking and Communications (ICNC).
https://doi.org/10.1109/iccnc.2012.6167472. Difference: write amplification is counted as forced
relocations in a merge model, not measured against a device.

[5] Wang, C.; Gao, M.; Guo, T.; et al. (2026). Enhancing SSD Endurance via ReRead-GC for
Balanced Wear Leveling and Reduced Write Amplification. 2026 8th International Conference on
Information Science, Electrical and Automat. https://doi.org/10.1109/iseae69422.2026.11544774.
Difference: write amplification is counted as forced relocations in a merge model, not measured
against a device.

[6] Sun, H.; Chen, G.; Liang, X.; et al. (2016). Exploring SSD endurance model based on write
amplification and temperature. 2016 Seventh International Green and Sustainable Computing
Conference (IGSC). https://doi.org/10.1109/igcc.2016.7892596. Difference: write amplification is
counted as forced relocations in a merge model, not measured against a device.

[7] Wang, P.; Chen, T. (2025). GraLoc: Preserving Graph Locality to Minimize Read and Write
Amplification on Flash Memory. 2025 IEEE 49th Annual Computers, Software, and Applications
Conference (COMPSAC). https://doi.org/10.1109/compsac65507.2025.00016. Difference: write
amplification is counted as forced relocations in a merge model, not measured against a device.

[8] Li, D.; Jin, H.; Liao, X.; et al. (2013). Improving write amplification in a virtualized and
multimedia SSD system. Multimedia Tools and Applications.
https://doi.org/10.1007/s11042-013-1497-6. Difference: write amplification is counted as forced
relocations in a merge model, not measured against a device.

[9] Chen, S.; Lin, J.; Chen, T.; et al. (2017). Mitigating the Write Amplification Problem of
Write-Optimized File Systems on Flash Storage. 2017 IEEE International Conference on Cluster
Computing (CLUSTER). https://doi.org/10.1109/cluster.2017.38. Difference: write amplification is
counted as forced relocations in a merge model, not measured against a device.

[10] Chen, Y.; Shih, Y.; Hsieh, J. (2023). Mitigating Write Amplification of Dual-mode Flash
Memory. 2023 20th International SoC Design Conference (ISOCC).
https://doi.org/10.1109/isocc59558.2023.10395978. Difference: write amplification is counted as
forced relocations in a merge model, not measured against a device.

[11] Houdt, B. V. (2014). On the necessity of hot and cold data identification to reduce the
write amplification in flash-based SSDs. Performance Evaluation.
https://doi.org/10.1016/j.peva.2014.08.003. Difference: write amplification is counted as forced
relocations in a merge model, not measured against a device.

[12] Park, C.; Lee, S.; Won, Y.; et al. (2017). Practical Implication of Analytical Models for
SSD Write Amplification. Proceedings of the 8th ACM/SPEC on International Conference on
Performance Engin. https://doi.org/10.1145/3030207.3030219. Difference: write amplification is
counted as forced relocations in a merge model, not measured against a device.

[13] Chakraborttii, C.; Litz, H. (2021). Reducing write amplification in flash by death-time
prediction of logical block addresses. Proceedings of the 14th ACM International Conference on
Systems and Storage. https://doi.org/10.1145/3456727.3463784. Difference: write amplification is
counted as forced relocations in a merge model, not measured against a device.

[14] Choi, Y.; Ahn, S. (2022). Separating the File System Journal to Reduce Write Amplification
of Garbage Collection on ZNS SSDs. Journal of Multimedia Information System.
https://doi.org/10.33851/jmis.2022.9.4.261. Difference: write amplification is counted as forced
relocations in a merge model, not measured against a device.

[15] Luojie, X.; Kurkoski, B. M.; Yaakobi, E. (2012). WOM codes reduce write amplification in
NAND flash memory. 2012 IEEE Global Communications Conference (GLOBECOM).
https://doi.org/10.1109/glocom.2012.6503611. Difference: write amplification is counted as
forced relocations in a merge model, not measured against a device.

[16] Zhou, Y.; Zhou, J.; Lu, K.; et al. (2024). A Contract-aware and Cost-effective LSM Store
for Cloud Storage with Low Latency Spikes. ACM Transactions on Storage.
https://doi.org/10.1145/3643851. Difference: the store is the setting the policy lives in, not
the object measured here.

[17] Chen, Z.; Zhang, K.; Wei, Q.; et al. (2026). A ReRAM-Based Processing-in-Memory Framework
for LSM-Based Key-Value Store. IEEE Transactions on Computer-Aided Design of Integrated Circuits
and Systems. https://doi.org/10.1109/tcad.2025.3591410. Difference: the store is the setting the
policy lives in, not the object measured here.

[18] Garefalakis, P.; Papadopoulos, P.; Magoutis, K. (2014). ACaZoo: A Distributed Key-Value
Store Based on Replicated LSM-Trees. 2014 IEEE 33rd International Symposium on Reliable
Distributed Systems. https://doi.org/10.1109/srds.2014.43. Difference: the store is the setting
the policy lives in, not the object measured here.

[19] Shen, Z.; Yu, D.; Wei, Q.; et al. (2024). ALSM: An Attribute-Aware LSM-Tree Based Key-Value
Store to Reduce I/O Amplification. 2024 International Conference on Meta Computing (ICMC).
https://doi.org/10.1109/icmc60390.2024.00013. Difference: the store is the setting the policy
lives in, not the object measured here.

[20] Wang, P.; Sun, G.; Jiang, S.; et al. (2014). An efficient design and implementation of
LSM-tree based key-value store on open-channel SSD. Proceedings of the Ninth European Conference
on Computer Systems. https://doi.org/10.1145/2592798.2592804. Difference: the store is the
setting the policy lives in, not the object measured here.

[21] Zhang, K.; Xia, Y.; Xia, Y.; et al. (2019). An Optimization of Key-Value Store Based on
Segmented LSM-Tree. 2019 IEEE 19th International Conference on Communication Technology (ICCT).
https://doi.org/10.1109/icct46805.2019.8947217. Difference: the store is the setting the policy
lives in, not the object measured here.

[22] Chen, Z.; Li, B.; Cai, X.; et al. (2021). Block-LSM: An Ether-aware Block-ordered LSM-tree
based Key-Value Storage Engine. 2021 IEEE 39th International Conference on Computer Design
(ICCD). https://doi.org/10.1109/iccd53106.2021.00017. Difference: the store is the setting the
policy lives in, not the object measured here.

[23] Xu, P.; Zhao, N.; Wan, J.; et al. (2021). Building A Fast and Efficient LSM-tree Store by
Integrating Local Storage with Cloud Storage. 2021 IEEE International Conference on Cluster
Computing (CLUSTER). https://doi.org/10.1109/cluster48925.2021.00032. Difference: the store is
the setting the policy lives in, not the object measured here.

[24] Li, M.; Cheng, W.; Wei, J.; et al. (2025). BVLSM: Write-Efficient LSM-Tree Storage via
WAL-Time Key-Value Separation. 2025 IEEE International Conference on High Performance Computing
and Communicati. https://doi.org/10.1109/hpcc67675.2025.00037. Difference: the store is the
setting the policy lives in, not the object measured here.

[25] Yu, Q.; Guo, C.; Zhuang, J.; et al. (2024). CaaS-LSM: Compaction-as-a-Service for LSM-based
Key-Value Stores in Storage Disaggregated Infrastructure. Proceedings of the ACM on Management
of Data. https://doi.org/10.1145/3654927. Difference: the store is the setting the policy lives
in, not the object measured here.

[26] Huang, F.; Pan, Y.; Zhang, H.; et al. (2024). CDNRocks: computable data nodes with RocksDB
to improve the read performance of LSM-tree-based distributed key-value storage systems. The
Journal of Supercomputing. https://doi.org/10.1007/s11227-024-06526-7. Difference: the store is
the setting the policy lives in, not the object measured here.

[27] Lee, H.; Lee, C.; Lee, S.; et al. (2022). Compaction-aware zone allocation for LSM based
key-value store on ZNS SSDs. Proceedings of the 14th ACM Workshop on Hot Topics in Storage and
File Systems. https://doi.org/10.1145/3538643.3539743. Difference: the store is the setting the
policy lives in, not the object measured here.

[28] Liang, J.; Chai, Y. (2021). CruiseDB: An LSM-Tree Key-Value Store with Both Better Tail
Throughput and Tail Latency. 2021 IEEE 37th International Conference on Data Engineering (ICDE).
https://doi.org/10.1109/icde51399.2021.00094. Difference: the store is the setting the policy
lives in, not the object measured here.

[29] Zhang, W.; Xu, Y. (2018). Deduplication Triggered Compaction for LSM-Tree Based Key-Value
Store. 2018 IEEE 9th International Conference on Software Engineering and Service Scien.
https://doi.org/10.1109/icsess.2018.8663897. Difference: the store is the setting the policy
lives in, not the object measured here.

[30] Im, J.; Bae, J.; Chung, C.; et al. (2021). Design of LSM-tree-based Key-value SSDs with
Bounded Tails. ACM Transactions on Storage. https://doi.org/10.1145/3452846. Difference: the
store is the setting the policy lives in, not the object measured here.

[31] Chen, L.; Yu, S.; Ho, C.; et al. (2023). Efficient Sanitization Design for LSM-based
Key-Value Store over 3D MLC NAND Flash. Proceedings of the 38th ACM/SIGAPP Symposium on Applied
Computing. https://doi.org/10.1145/3555776.3577780. Difference: the store is the setting the
policy lives in, not the object measured here.

[32] Zhang, R.; Zhou, L.; Li, M.; et al. (2024). Efficient Wear-Leveling-Aware Data Placement
for LSM-Tree based key-value store on ZNS SSDs. Journal of King Saud University - Computer and
Information Sciences. https://doi.org/10.1016/j.jksuci.2024.102156. Difference: the store is the
setting the policy lives in, not the object measured here.

[33] Li, J.; Ren, Y.; Han, S.; et al. (2024). Enhancing LSM-Tree Key-Value Stores for
Read-Modify-Writes via Key-Delta Separation. 2024 IEEE 40th International Conference on Data
Engineering (ICDE). https://doi.org/10.1109/icde60146.2024.00375. Difference: the store is the
setting the policy lives in, not the object measured here.

[34] Sun, X.; Yu, J.; Zhou, Z.; et al. (2020). FPGA-based Compaction Engine for Accelerating
LSM-tree Key-Value Stores. 2020 IEEE 36th International Conference on Data Engineering (ICDE).
https://doi.org/10.1109/icde48307.2020.00113. Difference: the store is the setting the policy
lives in, not the object measured here.

[35] Sun, H.; Xu, J.; Jiang, X.; et al. (2024). gLSM: Using GPGPU to Accelerate Compactions in
LSM-tree-based Key-value Stores. ACM Transactions on Storage. https://doi.org/10.1145/3633782.
Difference: the store is the setting the policy lives in, not the object measured here.

[36] Zhou, H.; Chen, Y.; Zeng, W.; et al. (2025). GPComp: Using GPU and SSD-GPU Peer to Peer DMA
to Accelerate LSM-Tree Compaction for Key-Value Store. IEEE Transactions on Parallel and
Distributed Systems. https://doi.org/10.1109/tpds.2025.3586616. Difference: the store is the
setting the policy lives in, not the object measured here.

[37] Zhang, J.; Wang, F.; Dong, C. (2022). HaLSM: A Hotspot-aware LSM-tree based Key-Value
Storage Engine. 2022 IEEE 40th International Conference on Computer Design (ICCD).
https://doi.org/10.1109/iccd56317.2022.00035. Difference: the store is the setting the policy
lives in, not the object measured here.

[38] Lee, C.; Moon, S.; Chae, S.; et al. (2025). Improving Compaction in LSM Tree by Applying
Simple Copy to Key-Value Separated LSM-Tree. Journal of KIISE.
https://doi.org/10.5626/jok.2025.52.11.1002. Difference: the store is the setting the policy
lives in, not the object measured here.

[39] Chen, S.; Liang, Y.; Yang, M. (2022). KVSTL: An Application Support to LSM-Tree Based
Key-Value Store via Shingled Translation Layer Data Management. IEEE Transactions on Computers.
https://doi.org/10.1109/tc.2021.3098961. Difference: the store is the setting the policy lives
in, not the object measured here.

[40] Liu, M.; Gu, J.; Zhao, T. (2024). LCKV: Learner-Cleaner Optimized Adaptive Key-Value
Separated LSM-Tree Store. 2024 IEEE 42nd International Conference on Computer Design (ICCD).
https://doi.org/10.1109/iccd63220.2024.00079. Difference: the store is the setting the policy
lives in, not the object measured here.

[41] Li, C.; Chen, H.; Ruan, C.; et al. (2021). Leveraging NVMe SSDs for Building a Fast,
Cost-effective, LSM-tree-based KV Store. ACM Transactions on Storage.
https://doi.org/10.1145/3480963. Difference: the store is the setting the policy lives in, not
the object measured here.

[42] Mei, F.; Cao, Q.; Jiang, H.; et al. (2019). LSM-Tree Managed Storage for Large-Scale
Key-Value Store. IEEE Transactions on Parallel and Distributed Systems.
https://doi.org/10.1109/tpds.2018.2864209. Difference: the store is the setting the policy lives
in, not the object measured here.

[43] Mei, F.; Cao, Q.; Jiang, H.; et al. (2017). LSM-tree managed storage for large-scale
key-value store. Proceedings of the 2017 Symposium on Cloud Computing.
https://doi.org/10.1145/3127479.3127486. Difference: the store is the setting the policy lives
in, not the object measured here.

[44] Wang, Y.; Gong, C.; Zhu, G.; et al. (2026). Making LSM-Tree-based Key-Value Store Practical
and Efficient for Multi-Tenant Serverless Cloud Databases. Proceedings of the ACM on Management
of Data. https://doi.org/10.1145/3786667. Difference: the store is the setting the policy lives
in, not the object measured here.

[45] Wang, Z.; Shao, Z. (2023). MirrorKV: An Efficient Key-Value Store on Hybrid Cloud Storage
with Balanced Performance of Compaction and Querying. Proceedings of the ACM on Management of
Data. https://doi.org/10.1145/3626736. Difference: the store is the setting the policy lives in,
not the object measured here.

[46] Lin, X.; Pan, Y.; Feng, W.; et al. (2024). MTDB: an LSM-tree-based key-value store using a
multi-tree structure to improve read performance. The Journal of Supercomputing.
https://doi.org/10.1007/s11227-024-06382-5. Difference: the store is the setting the policy
lives in, not the object measured here.

[47] Huang, H.; Ghandeharizadeh, S. (2021). Nova-LSM: A Distributed, Component-based LSM-tree
Key-value Store. Proceedings of the 2021 International Conference on Management of Data.
https://doi.org/10.1145/3448016.3457297. Difference: the store is the setting the policy lives
in, not the object measured here.

[48] Koo, H.; Moon, S.; Jeon, H.; et al. (2022). Optimization of Load Balancing on LSM-Tree
based Distributed Key-Value Store using NVMe-oF. Journal of KIISE.
https://doi.org/10.5626/jok.2022.49.7.561. Difference: the store is the setting the policy lives
in, not the object measured here.

[49] Liu, Y.; Chen, C.; Yin, S. (2024). Optimize Metadata Operations of Key-Value Store via A
Flat Indexing LSM-Tree. 2024 IEEE International Symposium on Parallel and Distributed Processing
with Ap. https://doi.org/10.1109/ispa63168.2024.00185. Difference: the store is the setting the
policy lives in, not the object measured here.

[50] Seo, Y.; Park, S. (2020). PlexDB: Efficient Compaction Algorithm for Deduplication of
LSM-tree based Key-Value Store. Journal of Digital Contents Society.
https://doi.org/10.9728/dcs.2020.21.8.1501. Difference: the store is the setting the policy
lives in, not the object measured here.

[51] Lu, Z.; Cao, Q.; Wang, S.; et al. (2023). PMLDS: An LSM-Tree Direct Managed Storage for
Key-Value Stores on Byte-Addressable Devices. Proceedings of the 52nd International Conference
on Parallel Processing. https://doi.org/10.1145/3605573.3605629. Difference: the store is the
setting the policy lives in, not the object measured here.

[52] Kim, J.; Son, S.; Cho, H.; et al. (2019). Recursive Compaction Method of LSM-tree based
Key-value Store. Journal of KIISE. https://doi.org/10.5626/jok.2019.46.9.946. Difference: the
store is the setting the policy lives in, not the object measured here.

[53] Hu, Y.; Du, Y. (2021). Reducing tail latency of LSM-tree based key-value store via limited
compaction. Proceedings of the 36th Annual ACM Symposium on Applied Computing.
https://doi.org/10.1145/3412841.3442073. Difference: the store is the setting the policy lives
in, not the object measured here.

[54] Liu, M.; Gu, J.; Zhao, T. (2025). ServerlessLSM: Fast RDMA-Codesigned Disaggregated
Compaction for Elastic Serverless LSM-Tree Key-Value Store. 2025 IEEE International Conference
on Web Services (ICWS). https://doi.org/10.1109/icws67624.2025.00100. Difference: the store is
the setting the policy lives in, not the object measured here.

[55] Ren, J.; Chen, G.; Qian, K. (2022). SplitDB: Building a large-scale key-value store based
on LSM-tree by split operations. (no venue field). https://doi.org/10.21203/rs.3.rs-2142066/v1.
Difference: the store is the setting the policy lives in, not the object measured here.

[56] Zining, Y.; Gang, J.; Yu, H.; et al. (2022). SSD-Based LSM-Tree Key-Value Storage System.
2022 19th International Computer Conference on Wavelet Active Media Technology a.
https://doi.org/10.1109/iccwamtip56608.2022.10016522. Difference: the store is the setting the
policy lives in, not the object measured here.

[57] Liang, Y.; Wang, Y.; Yang, T.; et al. (2025). ZonesDB: Building Write-Optimized and
Space-Adaptive Key-Value Store on Zoned Storage with Fragmented LSM Tree. ACM Transactions on
Storage. https://doi.org/10.1145/3715331. Difference: the store is the setting the policy lives
in, not the object measured here.

[58] 조아영; Moon, Y. (2010). An Analysis of Leveled Writing Activities in Middle School English 1
Textbooks and Workbooks and the Perceptions of Middle School Students on the Leveled Writing
Activities. Linguistic Research. https://doi.org/10.17250/khisli.27.1.201004.003. Difference:
the two deployed families are not compared with each other; one family's decision is compared
with the optimum.

[59] Hayashi, S.; Komoda, N. (2015). Evaluation of Volume Tiering Method and SSD Cache Method in
Tiered Storage System. Electronics and Communications in Japan.
https://doi.org/10.1002/ecj.11749. Difference: the two deployed families are not compared with
each other; one family's decision is compared with the optimum.

[60] Hayashi, S.; Komoda, N. (2014). Evaluation of Volume Tiering Method and SSD Cache Method in
Tiered Storage System. IEEJ Transactions on Electronics, Information and Systems.
https://doi.org/10.1541/ieejeiss.134.459. Difference: the two deployed families are not compared
with each other; one family's decision is compared with the optimum.

[61] Wu, S.; Lin, G.; Lee, P. P. C.; et al. (2025). Leveled Product Codes for Optimal Block
Repairs in Geo-distributed Storage Systems. IEEE INFOCOM 2025 - IEEE Conference on Computer
Communications. https://doi.org/10.1109/infocom55648.2025.11044776. Difference: the two deployed
families are not compared with each other; one family's decision is compared with the optimum.

[62] Li, Z.; Wang, Y.; Nie, S.; et al. (2025). Olsync: Object-level tiering and coordination in
tiered storage systems based on software-defined network. Future Generation Computer Systems.
https://doi.org/10.1016/j.future.2024.107521. Difference: the two deployed families are not
compared with each other; one family's decision is compared with the optimum.

[63] Xiao, C.; Li, S.; Zhu, S.; et al. (2021). Series of solid-solid phase change materials with
ultra-high thermal stability and controllable phase change temperature: kilogram-leveled
preparation and application investigation. Journal of Energy Storage.
https://doi.org/10.1016/j.est.2021.102405. Difference: the two deployed families are not
compared with each other; one family's decision is compared with the optimum.

[64] Jia, W.; Jiang, D.; Xiong, J. (2025). A High-Performance and Scalable Userspace
Log-Structured File System for Modern SSDs. ACM Transactions on Storage.
https://doi.org/10.1145/3728645. Difference: cleaning is the historical ancestor of the cost,
not a competing model scored on the same instances.

[65] Hirano, M.; Ogawa, H. (2016). A Log-Structured Block Preservation and Restoration System
for Proactive Forensic Data Collection in the Cloud. 2016 11th International Conference on
Availability, Reliability and Security (AR. https://doi.org/10.1109/ares.2016.8. Difference:
cleaning is the historical ancestor of the cost, not a competing model scored on the same
instances.

[66] Wu, Z. H. (2014). A Log-Structured File System Based on LevelDB. Applied Mechanics and
Materials. https://doi.org/10.4028/www.scientific.net/amm.602-605.3481. Difference: cleaning is
the historical ancestor of the cost, not a competing model scored on the same instances.

[67] Menon, J.; Stockmeyer, L. (1998). An Age-Threshold Algorithm for Garbage Collection in
Log-Structured Arrays and File Systems. High Performance Computing Systems and Applications.
https://doi.org/10.1007/978-1-4615-5611-4_13. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[68] Park, J.; Kang, D. H.; Seo, E.; et al. (2016). An Efficient Cleaning Scheme for File
Defragmentation on Log-Structured File System. Journal of KIISE.
https://doi.org/10.5626/jok.2016.43.6.627. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[69] Robinson, J. T. (1996). Analysis of steady-state segment storage utilizations in a
log-structured file system with least-utilized segment cleaning. ACM SIGOPS Operating Systems
Review. https://doi.org/10.1145/240799.240803. Difference: cleaning is the historical ancestor
of the cost, not a competing model scored on the same instances.

[70] Qi, W.; Tan, Z.; Zhang, Z.; et al. (2023). BlzFS: Crash Consistent Log-structured File
System Based on Byte-loggable Zone for ZNS SSD. 2023 IEEE 41st International Conference on
Computer Design (ICCD). https://doi.org/10.1109/iccd58817.2023.00040. Difference: cleaning is
the historical ancestor of the cost, not a competing model scored on the same instances.

[71] Tian, T. (2024). Data Correlation Aware Buffer Cache Management for Improved I/O
Performance on Log-Structured File System-based NAND Flash Storage Devices. Academic Journal of
Science and Technology. https://doi.org/10.54097/7r19rt93. Difference: cleaning is the
historical ancestor of the cost, not a competing model scored on the same instances.

[72] Peters, T. M.; Gondree, M. A.; Peterson, Z. N. J. (2015). DEFY: A Deniable, Encrypted File
System for Log-Structured Storage. Proceedings 2015 Network and Distributed System Security
Symposium. https://doi.org/10.14722/ndss.2015.23078. Difference: cleaning is the historical
ancestor of the cost, not a competing model scored on the same instances.

[73] Min, C.; Lee, S.; Eom, Y. I. (2014). Design and Implementation of a Log-Structured File
System for Flash-Based Solid State Drives. IEEE Transactions on Computers.
https://doi.org/10.1109/tc.2013.97. Difference: cleaning is the historical ancestor of the cost,
not a competing model scored on the same instances.

[74] Karacali, H.; Yildirim, T. (2022). Design and Implementation of Basic Log Structured File
System for Internal Flash on Embedded Systems. 2022 7th International Conference on Computer
Science and Engineering (UBMK). https://doi.org/10.1109/ubmk55850.2022.9919586. Difference:
cleaning is the historical ancestor of the cost, not a competing model scored on the same
instances.

[75] Hwang, I.; Lee, S.; Kim, S.; et al. (2026). Design and implementation of zoned
namespace-tailored log-structured file system for commodity ZNS SSDs. Future Generation Computer
Systems. https://doi.org/10.1016/j.future.2026.108563. Difference: cleaning is the historical
ancestor of the cost, not a competing model scored on the same instances.

[76] Cheng, W.; Zheng, T.; Zeng, L.; et al. (2022). DPLFS: A Dual-Mode PCM-based Log-Structured
File System. 2022 IEEE 40th International Conference on Computer Design (ICCD).
https://doi.org/10.1109/iccd56317.2022.00054. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[77] Kang, D. H.; Eom, Y. I. (2017). Dynamic hot-cold separation scheme on the log-structured
file system for CE devices. 2017 IEEE International Conference on Consumer Electronics (ICCE).
https://doi.org/10.1109/icce.2017.7889383. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[78] Park, J.; Kang, D. H.; Eom, Y. I. (2016). File Defragmentation Scheme for a Log-Structured
File System. Proceedings of the 7th ACM SIGOPS Asia-Pacific Workshop on Systems.
https://doi.org/10.1145/2967360.2967622. Difference: cleaning is the historical ancestor of the
cost, not a competing model scored on the same instances.

[79] Kim, J.; Yoo, H.; Yoo, S. W.; et al. (2026). GAZE: Rearchitecting Log-Structured Filesystem
for Garbage Collection on Zoned Namespace Flash Storage. Proceedings of the ACM SIGOPS 32nd
Symposium on Operating Systems Principles. https://doi.org/10.1145/3830418.3843870. Difference:
cleaning is the historical ancestor of the cost, not a competing model scored on the same
instances.

[80] Jambor, M.; Hruby, T.; Taus, J.; et al. (2007). Implementation of a Linux log-structured
file system with a garbage collector. ACM SIGOPS Operating Systems Review.
https://doi.org/10.1145/1228291.1228299. Difference: cleaning is the historical ancestor of the
cost, not a competing model scored on the same instances.

[81] Bonnie, D. (2013). Improving Small File Creation Performance in a Parallel Log-Structured
File System. (no venue field). https://doi.org/10.2172/1089476. Difference: cleaning is the
historical ancestor of the cost, not a competing model scored on the same instances.

[82] Burrows, M.; Jerian, C.; Lampson, B.; et al. (1992). On-line data compression in a
log-structured file system. Proceedings of the fifth international conference on Architectural
support for p. https://doi.org/10.1145/143365.143376. Difference: cleaning is the historical
ancestor of the cost, not a competing model scored on the same instances.

[83] Burrows, M.; Jerian, C.; Lampson, B.; et al. (1992). On-line data compression in a
log-structured file system. ACM SIGPLAN Notices. https://doi.org/10.1145/143371.143376.
Difference: cleaning is the historical ancestor of the cost, not a competing model scored on the
same instances.

[84] Lee, S.; Park, J.; Eom, Y. I. (2019). Performance Analyses on Logging Policies of
Log-structured File System. 2019 IEEE International Conference on Consumer Electronics (ICCE).
https://doi.org/10.1109/icce.2019.8662104. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[85] Gwak, H.; Kang, Y.; Shin, D. (2015). Reducing garbage collection overhead of log-structured
file systems with GC journaling. 2015 International Symposium on Consumer Electronics (ISCE).
https://doi.org/10.1109/isce.2015.7177770. Difference: cleaning is the historical ancestor of
the cost, not a competing model scored on the same instances.

[86] Gwak, H.; Shin, D. (2021). SCJ: Segment Cleaning Journaling for Log-Structured File
Systems. IEEE Access. https://doi.org/10.1109/access.2021.3121423. Difference: cleaning is the
historical ancestor of the cost, not a competing model scored on the same instances.

[87] Stabell-Kulø, T. (1997). Security and log structured file systems. ACM SIGOPS Operating
Systems Review. https://doi.org/10.1145/250007.250009. Difference: cleaning is the historical
ancestor of the cost, not a competing model scored on the same instances.

[88] Rosenblum, M. (1995). The Design and Implementation of a Log-structured file system. (no
venue field). https://doi.org/10.1007/978-1-4615-2221-8. Difference: cleaning is the historical
ancestor of the cost, not a competing model scored on the same instances.

[89] Rosenblum, M.; Ousterhout, J. K. (1991). The design and implementation of a log-structured
file system. Proceedings of the thirteenth ACM symposium on Operating systems principles.
https://doi.org/10.1145/121132.121137. Difference: cleaning is the historical ancestor of the
cost, not a competing model scored on the same instances.

[90] Rosenblum, M.; Ousterhout, J. K. (1991). The design and implementation of a log-structured
file system. ACM SIGOPS Operating Systems Review. https://doi.org/10.1145/121133.121137.
Difference: cleaning is the historical ancestor of the cost, not a competing model scored on the
same instances.

[91] Rosenblum, M.; Ousterhout, J. K. (1992). The design and implementation of a log-structured
file system. ACM Transactions on Computer Systems. https://doi.org/10.1145/146941.146943.
Difference: cleaning is the historical ancestor of the cost, not a competing model scored on the
same instances.

[92] Konishi, R.; Amagai, Y.; Sato, K.; et al. (2006). The Linux implementation of a
log-structured file system. ACM SIGOPS Operating Systems Review.
https://doi.org/10.1145/1151374.1151375. Difference: cleaning is the historical ancestor of the
cost, not a competing model scored on the same instances.

[93] Reardon, J. (2016). User-Level Secure Deletion on Log-Structured File Systems. Information
Security and Cryptography. https://doi.org/10.1007/978-3-319-28778-2_5. Difference: cleaning is
the historical ancestor of the cost, not a competing model scored on the same instances.

[94] Kim, Y.; Kim, T.; Carey, M. J.; et al. (2017). A Comparative Study of Log-Structured
Merge-Tree-Based Spatial Indexes for Big Data. 2017 IEEE 33rd International Conference on Data
Engineering (ICDE). https://doi.org/10.1109/icde.2017.61. Difference: no engine is instrumented;
one policy's merge decision is scored against an exact optimum at a fixed horizon.

[95] Jaranilla, C.; Zhao, G.; Choi, G.; et al. (2025). A Framework for Integrating
Log-Structured Merge-Trees and Key–Value Separation in Tiered Storage. Electronics.
https://doi.org/10.3390/electronics14030564. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[96] Chuppala, R. (2025). Adelson-Velsky Landis and Log Structured Merge Tree for Kubernetes
ETCD. (no venue field). https://doi.org/10.2139/ssrn.5147817. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[97] author not established on Crossref for this DOI. (2024). Adelson-Velsky Landis and Log
Structured Merge Tree for Kubernetes ETCD. Advanced International Journal of Multidisciplinary
Research. https://doi.org/10.62127/aijmr.2024.v02i05.1109. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[98] Zhang, X.; Mao, Q.; Eldawy, A.; et al. (2022). Bi-directional Log-Structured Merge Tree.
34th International Conference on Scientific and Statistical Database Management.
https://doi.org/10.1145/3538712.3538730. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[99] Sun, H.; Dai, S.; Huang, J. (2020). Cascaded Write Amplification of LSM-tree-based
Key-Value Stores underlying Solid-State Disks. Microprocessors and Microsystems.
https://doi.org/10.1016/j.micpro.2020.103217. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[100] Park, K.; Lee, D.; Jeong, Y.; et al. (2025). Correction: Towards an asynchronous commit in
micro-batch streaming systems with log-structured merge-tree based key-value store. Cluster
Computing. https://doi.org/10.1007/s10586-025-05748-5. Difference: no engine is instrumented;
one policy's merge decision is scored against an exact optimum at a fixed horizon.

[101] Huang, J.; Xue, M.; Li, C.; et al. (2024). DynamicKV: Data Storage Strategy Based on
Partition Merging of Log-Structured Merge Tree. 2024 2nd International Conference on Computer,
Vision and Intelligent Technology. https://doi.org/10.1109/iccvit63928.2024.10872622.
Difference: no engine is instrumented; one policy's merge decision is scored against an exact
optimum at a fixed horizon.

[102] Song, N. Y.; Yeom, H. Y.; Han, H. (2018). Efficient Key-Value Stores with Ranged
Log-Structured Merge Trees. 2018 IEEE 11th International Conference on Cloud Computing (CLOUD).
https://doi.org/10.1109/cloud.2018.00090. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[103] Zhu, T.; Hu, H.; Qian, W.; et al. (2019). Fault-tolerant precise data access on
distributed log-structured merge-tree. Frontiers of Computer Science.
https://doi.org/10.1007/s11704-018-7198-6. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[104] Wandile, S. (2026). GravTree: A Local-Compaction Tree for Predictable Write Latency. (no
venue field). https://doi.org/10.2139/ssrn.7487218. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[105] Wang, X.; Li, H.; Tan, H.; et al. (2024). HIndex-FLSM: Fragmented Log-Structured Merge
Trees Integrated with Heat and Index. 2024 3rd International Joint Conference on Information and
Communication Enginee. https://doi.org/10.1109/jcice61382.2024.00024. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[106] Duan, H.; Hu, H.; Qian, W.; et al. (2018). Incremental Materialized View Maintenance on
Distributed Log-Structured Merge-Tree. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-3-319-91458-9_42. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[107] Adão, R.; Wu, Z.; Zhou, C.; et al. (2025). KEIGO: Co-Designing Log-Structured Merge
Key-Value Stores with a Non-Volatile, Concurrency-Aware Storage Hierarchy. Proceedings of the
VLDB Endowment. https://doi.org/10.14778/3746405.3746414. Difference: no engine is instrumented;
one policy's merge decision is scored against an exact optimum at a fixed horizon.

[108] Jeong, J.; Kwak, J.; Lee, D.; et al. (2020). Level Aware Data Placement Technique for
Hybrid NAND Flash Storage of Log-Structured Merge-Tree Based Key-Value Store System. IEEE
Access. https://doi.org/10.1109/access.2020.3031322. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[109] author not established on Crossref for this DOI. (2024). Log Structured Merge Tree and Log
Structured Hash Table Tree for Kubernetes ETCD. Advanced International Journal of
Multidisciplinary Research. https://doi.org/10.62127/aijmr.2024.v02i05.1110. Difference: no
engine is instrumented; one policy's merge decision is scored against an exact optimum at a
fixed horizon.

[110] Mo, G.; Jia, R.; Gu, Y.; et al. (2026). LSM-Cache: An Efficient Log-Structured Merge
Hybrid Key-Value Cache for Massive Small Objects. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-981-95-5716-5_1. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[111] Zhang, B.; Du, D. H. C. (2021). NVLSM: A Persistent Memory Key-Value Store Using
Log-Structured Merge Tree with Accumulative Compaction. ACM Transactions on Storage.
https://doi.org/10.1145/3453300. Difference: no engine is instrumented; one policy's merge
decision is scored against an exact optimum at a fixed horizon.

[112] Gong, C.; He, S.; Gong, Y.; et al. (2019). On Integration of Appends and Merges in
Log-Structured Merge Trees. Proceedings of the 48th International Conference on Parallel
Processing. https://doi.org/10.1145/3337821.3337836. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[113] Song, N. Y.; Yeom, H. Y.; Han, H. (2019). Optimization of Key-Value Stores with Ranged
Log-Structured Merge Trees. KIISE Transactions on Computing Practices.
https://doi.org/10.5626/ktcp.2019.25.3.164. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[114] Chen, Y.; Yang, M.; Chang, Y.; et al. (2020). Parallel-Log-Single-Compaction-Tree:
Flash-Friendly Two-Level Key-Value Management in KVSSDs. 2020 25th Asia and South Pacific Design
Automation Conference (ASP-DAC). https://doi.org/10.1109/asp-dac47756.2020.9045144. Difference:
no engine is instrumented; one policy's merge decision is scored against an exact optimum at a
fixed horizon.

[115] Huang, C.; Hu, H.; Wei, X.; et al. (2019). Partition pruning for range query on
distributed log-structured merge-tree. Frontiers of Computer Science.
https://doi.org/10.1007/s11704-019-8234-x. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[116] Zhu, T.; Hu, H.; Qian, W.; et al. (2017). Precise Data Access on Distributed
Log-Structured Merge-Tree. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-3-319-63564-4_17. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[117] Huang, K.; Bao, M.; Zhang, K.; et al. (2026). Reducing I/O Amplification for Key-Value
Stores With a Log-Assisted Log-Structured Merge Tree. IEEE Transactions on Knowledge and Data
Engineering. https://doi.org/10.1109/tkde.2026.3699948. Difference: no engine is instrumented;
one policy's merge decision is scored against an exact optimum at a fixed horizon.

[118] Li, J.; Wang, K.; Chen, R. (2024). Reducing Write Amplification in LSM-Tree by Data
Compaction Based on Sliding-Window. 2024 6th International Academic Exchange Conference on
Science and Technology In. https://doi.org/10.1109/iaecst64597.2024.11118070. Difference: no
engine is instrumented; one policy's merge decision is scored against an exact optimum at a
fixed horizon.

[119] Shan, L.; Zhou, J.; Zhang, J.; et al. (2026). Reducing Write Amplification in LSM-Trees
Through Orchestrated Fine-Grained Compaction and Persistent Memory. IEEE Transactions on
Computers. https://doi.org/10.1109/tc.2026.3662419. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[120] Wang, X.; Jin, P.; Hua, B.; et al. (2022). Reducing Write Amplification of LSM-Tree with
Block-Grained Compaction. 2022 IEEE 38th International Conference on Data Engineering (ICDE).
https://doi.org/10.1109/icde53745.2022.00279. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[121] Bu, Z.; Wang, J.; Chen, L.; et al. (2026). Reducing Write Stall and Write Amplification
for LSM-Tree Based Key-Value Stores Using a Hybrid Compression Strategy. Lecture Notes in
Computer Science. https://doi.org/10.1007/978-981-95-5716-5_26. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[122] Lee, H.; Lee, M.; Eom, Y. I. (2021). SFM: Mitigating Read/Write Amplification Problem of
LSM-Tree-Based Key-Value Stores. IEEE Access. https://doi.org/10.1109/access.2021.3098736.
Difference: no engine is instrumented; one policy's merge decision is scored against an exact
optimum at a fixed horizon.

[123] Riyaz, P.; Varghese, S. M. (2016). SLSM - A Scalable Log Structured Merge Tree with Bloom
Filters for Low Latency Analytics. Procedia Technology.
https://doi.org/10.1016/j.protcy.2016.05.075. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[124] Lively, T.; Schroeder, L.; Mendizábal, C. (2018). Splaying Log-Structured Merge-Trees.
Proceedings of the 2018 International Conference on Management of Data.
https://doi.org/10.1145/3183713.3183723. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[125] O’Neil, P.; Cheng, E.; Gawlick, D.; et al. (1996). The log-structured merge-tree
(LSM-tree). Acta Informatica. https://doi.org/10.1007/s002360050048. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[126] Shin, J.; Wang, J.; Aref, W. G. (2021). The LSM RUM-Tree: A Log Structured Merge R-Tree
for Update-intensive Spatial Workloads. 2021 IEEE 37th International Conference on Data
Engineering (ICDE). https://doi.org/10.1109/icde51399.2021.00238. Difference: no engine is
instrumented; one policy's merge decision is scored against an exact optimum at a fixed horizon.

[127] Lee, J.; Choi, W. G.; Kim, D.; et al. (2020). TLSM: Tiered Log-Structured Merge-Tree
Utilizing Non-Volatile Memory. IEEE Access. https://doi.org/10.1109/access.2020.2985407.
Difference: no engine is instrumented; one policy's merge decision is scored against an exact
optimum at a fixed horizon.

[128] Park, K.; Lee, D.; Jeong, Y.; et al. (2025). Towards an asynchronous commit in micro-batch
streaming systems with log-structured merge-tree based key-value store. Cluster Computing.
https://doi.org/10.1007/s10586-024-05000-6. Difference: no engine is instrumented; one policy's
merge decision is scored against an exact optimum at a fixed horizon.

[129] Ding, C.; Yao, T.; Jiang, H.; et al. (2022). TriangleKV: Reducing Write Stalls and Write
Amplification in LSM-Tree Based KV Stores With Triangle Container in NVM. IEEE Transactions on
Parallel and Distributed Systems. https://doi.org/10.1109/tpds.2022.3188268. Difference: no
engine is instrumented; one policy's merge decision is scored against an exact optimum at a
fixed horizon.

[130] Chen, L.; Chen, R.; Yang, C.; et al. (2023). Workload-Aware Log-Structured Merge Key-Value
Store for NVM-SSD Hybrid Storage. 2023 IEEE 39th International Conference on Data Engineering
(ICDE). https://doi.org/10.1109/icde55515.2023.00171. Difference: no engine is instrumented; one
policy's merge decision is scored against an exact optimum at a fixed horizon.

[131] Hong, S. (1999). A Competitive Online Algorithm for the Paging Problem with “Shelf”
Memory. Lecture Notes in Computer Science. https://doi.org/10.1007/3-540-48686-0_40. Difference:
no competitive ratio is claimed: the optimum is computed exactly per instance and the gap is
reported per cell.

[132] Smith. (1976). A Modified Working Set Paging Algorithm. IEEE Transactions on Computers.
https://doi.org/10.1109/tc.1976.1674715. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[133] Mohanty, S.; Venkatachalam, M.; Yang, X. (2007). A novel algorithm for efficient paging in
mobile WiMAX. 2007 IEEE Mobile WiMAX Symposium. https://doi.org/10.1109/wimax.2007.348683.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[134] author not established on Crossref for this DOI. (2007). A SPACE-EFFICIENT ALGORITHM FOR
PAGING UNBALANCED BINARY TREES. Proceedings of the Second International Conference on Software
and Data Technolo. https://doi.org/10.5220/0001334500380043. Difference: no competitive ratio is
claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[135] McGeoch, L. A.; Sleator, D. D. (1991). A strongly competitive randomized paging algorithm.
Algorithmica. https://doi.org/10.1007/bf01759073. Difference: no competitive ratio is claimed:
the optimum is computed exactly per instance and the gap is reported per cell.

[136] Torng, E. (1998). A Unified Analysis of Paging and Caching. Algorithmica.
https://doi.org/10.1007/pl00009192. Difference: no competitive ratio is claimed: the optimum is
computed exactly per instance and the gap is reported per cell.

[137] Adamaszek, A.; Czumaj, A.; Englert, M.; et al. (2018). An O (log k )-Competitive Algorithm
for Generalized Caching. ACM Transactions on Algorithms. https://doi.org/10.1145/3280826.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[138] Achlioptas, D.; Chrobak, M.; Noga, J. (1996). Competitive analysis of randomized paging
algorithms. Lecture Notes in Computer Science. https://doi.org/10.1007/3-540-61680-2_72.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[139] Achlioptas, D.; Chrobak, M.; Noga, J. (2000). Competitive analysis of randomized paging
algorithms. Theoretical Computer Science. https://doi.org/10.1016/s0304-3975(98)00116-9.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[140] Cohen, E.; Kaplan, H.; Zwick, U. (2001). Competitive Analysis of the LRFU Paging
Algorithm. Lecture Notes in Computer Science. https://doi.org/10.1007/3-540-44634-6_14.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[141] Cohen, E.; Kaplan, H.; Zwick, U. (2002). Competitive Analysis of the LRFU Paging
Algorithm. Algorithmica. https://doi.org/10.1007/s00453-002-0936-y. Difference: no competitive
ratio is claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[142] Bar-Noy, A.; Mansour, Y. (2004). Competitive on-line paging strategies for mobile users
under delay constraints. Proceedings of the twenty-third annual ACM symposium on Principles of
distribute. https://doi.org/10.1145/1011767.1011805. Difference: no competitive ratio is
claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[143] Borodin, A.; Irani, S.; Raghavan, P.; et al. (1995). Competitive Paging with Locality of
Reference. Journal of Computer and System Sciences. https://doi.org/10.1006/jcss.1995.1021.
Difference: no competitive ratio is claimed: the optimum is computed exactly per instance and
the gap is reported per cell.

[144] Borodin, A.; Raghavan, P.; Irani, S.; et al. (1991). Competitive paging with locality of
reference. Proceedings of the twenty-third annual ACM symposium on Theory of computing - ST.
https://doi.org/10.1145/103418.103422. Difference: no competitive ratio is claimed: the optimum
is computed exactly per instance and the gap is reported per cell.

[145] Li, M.; Lu, X.; Subramoni, H.; et al. (2017). Designing Registration Caching Free
High-Performance MPI Library with Implicit On-Demand Paging (ODP) of InfiniBand. 2017 IEEE 24th
International Conference on High Performance Computing (HiPC).
https://doi.org/10.1109/hipc.2017.00017. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[146] Arora, R. K.; Subramanian, R. (1978). Exploiting the optimal paging algorithms.
Information Processing Letters. https://doi.org/10.1016/0020-0190(78)90006-6. Difference: no
competitive ratio is claimed: the optimum is computed exactly per instance and the gap is
reported per cell.

[147] Ingargiola, G.; Korsh, J. F. (1974). Finding Optimal Demand Paging Algorithms. Journal of
the ACM. https://doi.org/10.1145/321796.321801. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[148] Moruz, G.; Negoescu, A. (2013). Improved Space Bounds for Strongly Competitive Randomized
Paging Algorithms. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-3-642-39206-1_64. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[149] Park, Y.; Bahn, H. (2020). Issues in File Caching and Virtual Memory Paging with Fast SCM
Storage. Advances in Science, Technology and Engineering Systems Journal.
https://doi.org/10.25046/aj050581. Difference: no competitive ratio is claimed: the optimum is
computed exactly per instance and the gap is reported per cell.

[150] Kamali, S.; Xu, H. (2020). Multicore Paging Algorithms Cannot Be Competitive. Proceedings
of the 32nd ACM Symposium on Parallelism in Algorithms and Architect.
https://doi.org/10.1145/3350755.3400270. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[151] Cai, Z. (2009). On-line algorithm of loose competitive caching. Journal of Computer
Applications. https://doi.org/10.3724/sp.j.1087.2008.02604. Difference: no competitive ratio is
claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[152] Young, N. E. (2008). Online Paging and Caching. Encyclopedia of Algorithms.
https://doi.org/10.1007/978-0-387-30162-4_267. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[153] Young, N. E. (2016). Online Paging and Caching. Encyclopedia of Algorithms.
https://doi.org/10.1007/978-1-4939-2864-4_267. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[154] Young, N. (2015). Online Paging and Caching. Encyclopedia of Algorithms.
https://doi.org/10.1007/978-3-642-27848-8_267-2. Difference: no competitive ratio is claimed:
the optimum is computed exactly per instance and the gap is reported per cell.

[155] Kimbrel, T. (2001). Online paging and file caching with expiration times. Theoretical
Computer Science. https://doi.org/10.1016/s0304-3975(00)00263-2. Difference: no competitive
ratio is claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[156] Brodal, G. S.; Moruz, G.; Negoescu, A. (2012). OnlineMin: A Fast Strongly Competitive
Randomized Paging Algorithm. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-3-642-29116-6_14. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[157] Brodal, G. S.; Moruz, G.; Negoescu, A. (2012). OnlineMin: A Fast Strongly Competitive
Randomized Paging Algorithm. Theory of Computing Systems.
https://doi.org/10.1007/s00224-012-9427-y. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[158] Lew, A. (1976). Optimal control of demand-paging systems. Information Sciences.
https://doi.org/10.1016/0020-0255(76)90052-9. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[159] Lew, A. (1976). Optimal control of demand-paging systems. Information Sciences.
https://doi.org/10.1016/s0020-0255(76)90962-2. Difference: no competitive ratio is claimed: the
optimum is computed exactly per instance and the gap is reported per cell.

[160] Moruz, G.; Negoescu, A. (2012). Outperforming LRU via Competitive Analysis on Parametrized
Inputs for Paging. Proceedings of the Twenty-Third Annual ACM-SIAM Symposium on Discrete
Algorithms. https://doi.org/10.1137/1.9781611973099.132. Difference: no competitive ratio is
claimed: the optimum is computed exactly per instance and the gap is reported per cell.

[161] Alanko, T. O.; Verkamo, A. (1983). Segmentation, paging and optimal page sizes in virtual
memory. Computer Compacts. https://doi.org/10.1016/0167-7136(83)90150-6. Difference: no
competitive ratio is claimed: the optimum is computed exactly per instance and the gap is
reported per cell.

[162] Baghaie, T. (2013). Track Paging an Optimal Method for Minimizing Paging and Signaling
Cost in Mobile IP. Journal of Computer and Communications.
https://doi.org/10.4236/jcc.2013.14002. Difference: no competitive ratio is claimed: the optimum
is computed exactly per instance and the gap is reported per cell.

[163] Chang, C.; Chen, J. (2017). UM Paging: Unified M2M Paging with Optimal DRX Cycle. IEEE
Transactions on Mobile Computing. https://doi.org/10.1109/tmc.2016.2575835. Difference: no
competitive ratio is claimed: the optimum is computed exactly per instance and the gap is
reported per cell.

[164] Albers, S. (1994). A Competitive analysis of the list update problem with lookahead.
Lecture Notes in Computer Science. https://doi.org/10.1007/3-540-58338-6_67. Difference: the
quantity is the minimum cost attainable at a horizon, not a competitive ratio against an
adversary.

[165] Albers, S. (1998). A competitive analysis of the list update problem with lookahead.
Theoretical Computer Science. https://doi.org/10.1016/s0304-3975(97)00026-1. Difference: the
quantity is the minimum cost attainable at a horizon, not a competitive ratio against an
adversary.

[166] Dunke, F.; Nickel, S. (2016). A general modeling approach to online optimization with
lookahead. Omega. https://doi.org/10.1016/j.omega.2015.10.009. Difference: the quantity is the
minimum cost attainable at a horizon, not a competitive ratio against an adversary.

[167] Dunke, F.; Nickel, S. (2021). Correction to: Exact distributional analysis of online
algorithms with lookahead. 4OR. https://doi.org/10.1007/s10288-021-00479-w. Difference: the
quantity is the minimum cost attainable at a horizon, not a competitive ratio against an
adversary.

[168] Dunke, F.; Nickel, S. (2020). Exact distributional analysis of online algorithms with
lookahead. 4OR. https://doi.org/10.1007/s10288-020-00442-1. Difference: the quantity is the
minimum cost attainable at a horizon, not a competitive ratio against an adversary.

[169] Sarkar, U.; Chakrabarti, P.; Ghose, S.; et al. (1994). Improving Greedy Algorithms by
Lookahead-Search. Journal of Algorithms. https://doi.org/10.1006/jagm.1994.1001. Difference: the
quantity is the minimum cost attainable at a horizon, not a competitive ratio against an
adversary.

[170] Esmeir, S.; Markovitch, S. (2004). Lookahead-based algorithms for anytime induction of
decision trees. Twenty-first international conference on Machine learning - ICML '04.
https://doi.org/10.1145/1015330.1015373. Difference: the quantity is the minimum cost attainable
at a horizon, not a competitive ratio against an adversary.

[171] Wang, H.; Chaudhary, A.; Chen, D. Z. (2009). New algorithms for online rectangle filling
with k-lookahead. Journal of Combinatorial Optimization.
https://doi.org/10.1007/s10878-009-9246-5. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[172] Breslauer, D. (1996). On competitive on-line paging with lookahead. Lecture Notes in
Computer Science. https://doi.org/10.1007/3-540-60922-9_48. Difference: the quantity is the
minimum cost attainable at a horizon, not a competitive ratio against an adversary.

[173] Breslauer, D. (1998). On competitive on-line paging with lookahead. Theoretical Computer
Science. https://doi.org/10.1016/s0304-3975(98)00118-2. Difference: the quantity is the minimum
cost attainable at a horizon, not a competitive ratio against an adversary.

[174] Breslauer, D. (1995). On Competitive On-Line Paging with Lookahead. BRICS Report Series.
https://doi.org/10.7146/brics.v2i50.19951. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[175] Albers, S. (1997). On the Influence of Lookahead in Competitive Paging Algorithms.
Algorithmica. https://doi.org/10.1007/pl00009158. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[176] Li, W.; Zhang, Z.; Yang, S. (2012). Online algorithms for scheduling unit length jobs on
parallel-batch machines with lookahead. Information Processing Letters.
https://doi.org/10.1016/j.ipl.2012.01.002. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[177] Jiao, C.; Yuan, J.; Feng, Q. (2019). Online Algorithms for Scheduling Unit Length Jobs on
Unbounded Parallel-Batch Machines with Linearly Lookahead. Asia-Pacific Journal of Operational
Research. https://doi.org/10.1142/s0217595919500246. Difference: the quantity is the minimum
cost attainable at a horizon, not a competitive ratio against an adversary.

[178] Mansour, M. M. (2009). Parallel lookahead algorithms for pruned interleavers. IEEE
Transactions on Communications. https://doi.org/10.1109/tcomm.2009.11.070661. Difference: the
quantity is the minimum cost attainable at a horizon, not a competitive ratio against an
adversary.

[179] Nemeth, T.; Gyekiczki, B.; Imreh, C. (2011). Parameter learning in lookahead online
algorithms for data acknowledgment. 3rd IEEE International Symposium on Logistics and Industrial
Informatics. https://doi.org/10.1109/lindi.2011.6031146. Difference: the quantity is the minimum
cost attainable at a horizon, not a competitive ratio against an adversary.

[180] Park, J. C. H. (1987). Remarks on recent algorithms for LALR lookahead sets. ACM SIGPLAN
Notices. https://doi.org/10.1145/24714.24717. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[181] Ives, F. (1987). Response to remarks on recent algorithms for LALR lookahead sets. ACM
SIGPLAN Notices. https://doi.org/10.1145/35596.35606. Difference: the quantity is the minimum
cost attainable at a horizon, not a competitive ratio against an adversary.

[182] Dwibedy, D.; Mohanty, R. (2023). Semi-Online Scheduling with Lookahead. (no venue field).
https://doi.org/10.2139/ssrn.4485992. Difference: the quantity is the minimum cost attainable at
a horizon, not a competitive ratio against an adversary.

[183] Mizutani, E.; Dreyfus, S. (2009). Stage-lookahead dynamic programming algorithms for
stochastic problems with time-lagged control dynamics. 2009 IEEE International Conference on
Industrial Engineering and Engineering Man. https://doi.org/10.1109/ieem.2009.5373354.
Difference: the quantity is the minimum cost attainable at a horizon, not a competitive ratio
against an adversary.

[184] Albers, S. (1993). The influence of lookahead in competitive paging algorithms. Lecture
Notes in Computer Science. https://doi.org/10.1007/3-540-57273-2_39. Difference: the quantity is
the minimum cost attainable at a horizon, not a competitive ratio against an adversary.

[185] Ives, F. (1986). Unifying view of recent LALR(1) lookahead set algorithms. Proceedings of
the 1986 SIGPLAN symposium on Compiler construction. https://doi.org/10.1145/12276.13324.
Difference: the quantity is the minimum cost attainable at a horizon, not a competitive ratio
against an adversary.

[186] Ives, F. (1986). Unifying view of recent LALR(1) lookahead set algorithms. ACM SIGPLAN
Notices. https://doi.org/10.1145/13310.13324. Difference: the quantity is the minimum cost
attainable at a horizon, not a competitive ratio against an adversary.

[187] Bartal, Y.; Blum, A.; Burch, C.; et al. (1997). A polylog( n )-competitive algorithm for
metrical task systems. Proceedings of the twenty-ninth annual ACM symposium on Theory of
computing - ST. https://doi.org/10.1145/258533.258667. Difference: no task system is solved; the
framework is cited as the scoring convention this paper adopts.

[188] Bansal, N.; Buchbinder, N.; Madry, A.; et al. (2011). A Polylogarithmic-Competitive
Algorithm for the k-Server Problem. 2011 IEEE 52nd Annual Symposium on Foundations of Computer
Science. https://doi.org/10.1109/focs.2011.63. Difference: no task system is solved; the
framework is cited as the scoring convention this paper adopts.

[189] Borodin, A.; Linial, N.; Saks, M. E. (1992). An optimal on-line algorithm for metrical
task system. Journal of the ACM. https://doi.org/10.1145/146585.146588. Difference: no task
system is solved; the framework is cited as the scoring convention this paper adopts.

[190] Borodin, A.; Linial, N.; Saks, M. (1987). An optimal online algorithm for metrical task
systems. Proceedings of the nineteenth annual ACM conference on Theory of computing - STO.
https://doi.org/10.1145/28395.28435. Difference: no task system is solved; the framework is
cited as the scoring convention this paper adopts.

[191] Cosson, R.; Massoulié, L. (2024). Barely Random Algorithms and Collective Metrical Task
Systems. Advances in Neural Information Processing Systems 37.
https://doi.org/10.52202/079017-1178. Difference: no task system is solved; the framework is
cited as the scoring convention this paper adopts.

[192] Fiat, A.; Mendel, M. (2003). Better Algorithms for Unfair Metrical Task Systems and
Applications. SIAM Journal on Computing. https://doi.org/10.1137/s0097539700376159. Difference:
no task system is solved; the framework is cited as the scoring convention this paper adopts.

[193] Fiat, A.; Mendel, M. (2000). Better algorithms for unfair metrical task systems and
applications. Proceedings of the thirty-second annual ACM symposium on Theory of computing.
https://doi.org/10.1145/335305.335408. Difference: no task system is solved; the framework is
cited as the scoring convention this paper adopts.

[194] Bubeck, S.; Cohen, M. B.; Lee, J. R.; et al. (2019). Metrical task systems on trees via
mirror descent and unfair gluing. Proceedings of the Thirtieth Annual ACM-SIAM Symposium on
Discrete Algorithms. https://doi.org/10.1137/1.9781611975482.6. Difference: no task system is
solved; the framework is cited as the scoring convention this paper adopts.

[195] Bubeck, S.; Cohen, M. B.; Lee, J. R.; et al. (2021). Metrical Task Systems on Trees via
Mirror Descent and Unfair Gluing. SIAM Journal on Computing. https://doi.org/10.1137/19m1237879.
Difference: no task system is solved; the framework is cited as the scoring convention this
paper adopts.

[196] Chrobak, M.; Larmore, L. L. (1998). Metrical task systems, the server problem and the work
function algorithm. Lecture Notes in Computer Science. https://doi.org/10.1007/bfb0029565.
Difference: no task system is solved; the framework is cited as the scoring convention this
paper adopts.

[197] Burley, W. R.; Irani, S. (1997). On Algorithm Design for Metrical Task Systems.
Algorithmica. https://doi.org/10.1007/pl00009166. Difference: no task system is solved; the
framework is cited as the scoring convention this paper adopts.

[198] Bartal, Y.; Koutsoupias, E. (2004). On the competitive ratio of the work function
algorithm for the k-server problem. Theoretical Computer Science.
https://doi.org/10.1016/j.tcs.2004.06.001. Difference: no task system is solved; the framework
is cited as the scoring convention this paper adopts.

[199] Irani, S.; Seiden, S. (1995). Randomized algorithms for metrical task systems. Lecture
Notes in Computer Science. https://doi.org/10.1007/3-540-60220-8_59. Difference: no task system
is solved; the framework is cited as the scoring convention this paper adopts.

[200] Irani, S.; Seiden, S. (1998). Randomized algorithms for metrical task systems. Theoretical
Computer Science. https://doi.org/10.1016/s0304-3975(97)00006-6. Difference: no task system is
solved; the framework is cited as the scoring convention this paper adopts.

[201] Bartal, Y.; Rosen, A. (1992). The distributed k-server problem-a competitive distributed
translator for k-server algorithms. Proceedings., 33rd Annual Symposium on Foundations of
Computer Science. https://doi.org/10.1109/sfcs.1992.267756. Difference: no task system is
solved; the framework is cited as the scoring convention this paper adopts.

[202] Bartal, Y.; Rosén, A. (1997). The Distributedk-Server Problem—A Competitive Distributed
Translator fork-Server Algorithms. Journal of Algorithms.
https://doi.org/10.1006/jagm.1996.0826. Difference: no task system is solved; the framework is
cited as the scoring convention this paper adopts.

[203] Schäfer, G.; Sivadasan, N. (2004). Topology Matters: Smoothed Competitiveness of Metrical
Task Systems. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-540-24749-4_43.
Difference: no task system is solved; the framework is cited as the scoring convention this
paper adopts.

[204] Schäfer, G.; Sivadasan, N. (2005). Topology matters: Smoothed competitiveness of metrical
task systems. Theoretical Computer Science. https://doi.org/10.1016/j.tcs.2005.04.006.
Difference: no task system is solved; the framework is cited as the scoring convention this
paper adopts.

[205] Seiden, S. (1999). Unfair Problems and Randomized Algorithms for Metrical Task Systems.
Information and Computation. https://doi.org/10.1006/inco.1998.2744. Difference: no task system
is solved; the framework is cited as the scoring convention this paper adopts.

[206] Dutt, S.; Shi, O. (2018). A fast and effective lookahead and fractional search based
scheduling algorithm for high-level synthesis. 2018 Design, Automation & Test in Europe
Conference & Exhibition (DATE). https://doi.org/10.23919/date.2018.8341975. Difference: the
lookahead bounds a merge decision inside a compaction window rather than a scheduling queue.

[207] Wan, G.; Schweitzer, H. (2021). A Lookahead Algorithm for Robust Subspace Recovery. 2021
IEEE International Conference on Data Mining (ICDM).
https://doi.org/10.1109/icdm51629.2021.00175. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[208] Kim, H. H.; Choi, J. Y. (2014). An efficient one-step lookahead A* algorithm for PM-CT
scheduling problems. The International Journal of Advanced Manufacturing Technology.
https://doi.org/10.1007/s00170-014-5755-1. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[209] Li, W.; Yuan, J. (2015). An Improved Online Algorithm for the Online Preemptive Scheduling
of Equal-Length Intervals on a Single Machine with Lookahead. Asia-Pacific Journal of
Operational Research. https://doi.org/10.1142/s0217595915500475. Difference: the lookahead
bounds a merge decision inside a compaction window rather than a scheduling queue.

[210] Shmueli, E.; Feitelson, D. G. (2003). Backfilling with Lookahead to Optimize the
Performance of Parallel Job Scheduling. Lecture Notes in Computer Science.
https://doi.org/10.1007/10968987_12. Difference: the lookahead bounds a merge decision inside a
compaction window rather than a scheduling queue.

[211] Bittencourt, L. F.; Sakellariou, R.; Madeira, E. R. M. (2010). DAG Scheduling Using a
Lookahead Variant of the Heterogeneous Earliest Finish Time Algorithm. 2010 18th Euromicro
Conference on Parallel, Distributed and Network-based Proces.
https://doi.org/10.1109/pdp.2010.56. Difference: the lookahead bounds a merge decision inside a
compaction window rather than a scheduling queue.

[212] Thomasian, A.; Liu, C. (2002). Disk scheduling policies with lookahead. ACM SIGMETRICS
Performance Evaluation Review. https://doi.org/10.1145/588160.588165. Difference: the lookahead
bounds a merge decision inside a compaction window rather than a scheduling queue.

[213] Zheng, F.; Xu, Y.; Zhang, E. (2008). How much can lookahead help in online single machine
scheduling. Information Processing Letters. https://doi.org/10.1016/j.ipl.2007.10.008.
Difference: the lookahead bounds a merge decision inside a compaction window rather than a
scheduling queue.

[214] Beaty, S. J. (1992). Lookahead scheduling. ACM SIGMICRO Newsletter.
https://doi.org/10.1145/144965.145822. Difference: the lookahead bounds a merge decision inside
a compaction window rather than a scheduling queue.

[215] Kiniwa, J.; Hamada, T.; Mizoguchi, D. (2001). Lookahead scheduling requests for multisize
page caching. IEEE Transactions on Computers. https://doi.org/10.1109/12.954511. Difference: the
lookahead bounds a merge decision inside a compaction window rather than a scheduling queue.

[216] Li, W.; Wang, L.; Yuan, H. (2022). Online Batch Scheduling of Incompatible Job Families
with Variable Lookahead Interval. Asia-Pacific Journal of Operational Research.
https://doi.org/10.1142/s0217595922400127. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[217] Zheng, F.; Cheng, Y.; Liu, M.; et al. (2013). Online interval scheduling on a single
machine with finite lookahead. Computers & Operations Research.
https://doi.org/10.1016/j.cor.2012.06.003. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[218] Pinson, N.; Spieksma, F. C. R. (2019). Online interval scheduling on two related machines:
the power of lookahead. Journal of Combinatorial Optimization.
https://doi.org/10.1007/s10878-019-00381-6. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[219] Böhm, M.; Chrobak, M.; Jeż, Ł.; et al. (2019). Online packet scheduling with bounded delay
and lookahead. Theoretical Computer Science. https://doi.org/10.1016/j.tcs.2019.01.013.
Difference: the lookahead bounds a merge decision inside a compaction window rather than a
scheduling queue.

[220] Li, W.; Yuan, J.; Yang, S. (2014). Online scheduling of incompatible unit-length job
families with lookahead. Theoretical Computer Science.
https://doi.org/10.1016/j.tcs.2014.05.024. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[221] Qian, X.; Xingong, Z. (2023). Online scheduling of two-machine flowshop with lookahead and
incompatible job families. Journal of Combinatorial Optimization.
https://doi.org/10.1007/s10878-022-00974-8. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[222] Li, W.; Yuan, J.; Cao, J.; et al. (2009). Online scheduling of unit length jobs on a
batching machine to maximize the number of early jobs with lookahead. Theoretical Computer
Science. https://doi.org/10.1016/j.tcs.2009.07.056. Difference: the lookahead bounds a merge
decision inside a compaction window rather than a scheduling queue.

[223] Motwani, R.; Saraswat, V.; Torng, E. (1998). Online Scheduling with Lookahead: Multipass
Assembly Lines. INFORMS Journal on Computing. https://doi.org/10.1287/ijoc.10.3.331. Difference:
the lookahead bounds a merge decision inside a compaction window rather than a scheduling queue.

[224] Coleman, B. (2006). Quality vs. Performance in Lookahead Scheduling. Advances in
Intelligent Systems Research. https://doi.org/10.2991/jcis.2006.324. Difference: the lookahead
bounds a merge decision inside a compaction window rather than a scheduling queue.

[225] Mandelbaum, M.; Shabtay, D. (2010). Scheduling unit length jobs on parallel machines with
lookahead information. Journal of Scheduling. https://doi.org/10.1007/s10951-010-0192-y.
Difference: the lookahead bounds a merge decision inside a compaction window rather than a
scheduling queue.

[226] Zheng, F.; Chen, Y.; Liu, M.; et al. (2023). Semi-Online Scheduling on Two Identical
Parallel Machines with Initial-Lookahead Information. Asia-Pacific Journal of Operational
Research. https://doi.org/10.1142/s0217595923500033. Difference: the lookahead bounds a merge
decision inside a compaction window rather than a scheduling queue.

[227] Zheng, F.; Chen, Y.; Liu, M. (2024). Semi-online scheduling on two uniform parallel
machines with initial lookahead. RAIRO - Operations Research.
https://doi.org/10.1051/ro/2024042. Difference: the lookahead bounds a merge decision inside a
compaction window rather than a scheduling queue.

[228] Werthmann, T.; Kaschub, M.; Proebster, M.; et al. (2012). Simple Channel Predictors for
Lookahead Scheduling. 2012 IEEE 75th Vehicular Technology Conference (VTC Spring).
https://doi.org/10.1109/vetecs.2012.6240134. Difference: the lookahead bounds a merge decision
inside a compaction window rather than a scheduling queue.

[229] Gascon, A. (1988). The Lookahead Heuristic For Multi-Item Single Machine Production
Scheduling With Dynamic, Stochastic Demands. INFOR: Information Systems and Operational
Research. https://doi.org/10.1080/03155986.1988.11732058. Difference: the lookahead bounds a
merge decision inside a compaction window rather than a scheduling queue.

[230] Cho, T. S. (2012). Analysis of PLS Path Model between CRM Information Possessed by a Ski
Rental Shop and Customer Behavior. Journal of Sport and Leisure Studies.
https://doi.org/10.51979/kssls.2012.05.48.129. Difference: the minimal online decision is cited
as the base case, and no algorithm is derived from it.

[231] Zhang, H.; Conitzer, V. (2020). Combinatorial Ski Rental and Online Bipartite Matching.
Proceedings of the 21st ACM Conference on Economics and Computation.
https://doi.org/10.1145/3391403.3399470. Difference: the minimal online decision is cited as the
base case, and no algorithm is derived from it.

[232] Li, Z.; Sun, B.; Zhang, Z.; et al. (2025). Combinatorial Ski Rental Problem: Robust and
Learning-Augmented Algorithms. Advances in Neural Information Processing Systems 38.
https://doi.org/10.52202/085713-4014. Difference: the minimal online decision is cited as the
base case, and no algorithm is derived from it.

[233] Bienkowski, M.; Schmid, S. (2013). Competitive FIB Aggregation for Independent Prefixes:
Online Ski Rental on the Trie. Lecture Notes in Computer Science.
https://doi.org/10.1007/978-3-319-03578-9_8. Difference: the minimal online decision is cited as
the base case, and no algorithm is derived from it.

[234] Shin, Y.; Lee, C.; Lee, G.; et al. (2025). Improved Learning-Augmented Algorithms and
(Tight) Lower Bounds for Multi-Option Ski Rental Problem. ACM Transactions on Algorithms.
https://doi.org/10.1145/3763239. Difference: the minimal online decision is cited as the base
case, and no algorithm is derived from it.

[235] Bhattacharya, A.; Das, R. (2022). Machine learning advised algorithms for the ski rental
problem with a discount. Theoretical Computer Science.
https://doi.org/10.1016/j.tcs.2022.10.006. Difference: the minimal online decision is cited as
the base case, and no algorithm is derived from it.

[236] Wang, S.; Li, J. (2020). Online Algorithms for Multi-shop Ski Rental with Machine Learned
Predictions. International Joint Conference on Autonomous Agents and Multiagent Systems.
https://doi.org/10.65109/ocnn5096. Difference: the minimal online decision is cited as the base
case, and no algorithm is derived from it.

[237] Lee, G.; Saad, W.; Bennis, M.; et al. (2017). Online Ski Rental for ON/OFF Scheduling of
Energy Harvesting Base Stations. IEEE Transactions on Wireless Communications.
https://doi.org/10.1109/twc.2017.2672964. Difference: the minimal online decision is cited as
the base case, and no algorithm is derived from it.

[238] Lee, G.; Saad, W.; Bennis, M.; et al. (2016). Online ski rental for scheduling
self-powered, energy harvesting small base stations. 2016 IEEE International Conference on
Communications (ICC). https://doi.org/10.1109/icc.2016.7511011. Difference: the minimal online
decision is cited as the base case, and no algorithm is derived from it.

[239] Lotker, Z.; Patt-Shamir, B.; Rawitz, D. (2012). Rent, Lease, or Buy: Randomized Algorithms
for Multislope Ski Rental. SIAM Journal on Discrete Mathematics.
https://doi.org/10.1137/100794018. Difference: the minimal online decision is cited as the base
case, and no algorithm is derived from it.

### Works read in full, which Crossref does not index

[240] RocksDB. (2026). Compaction. RocksDB wiki, revision read 2026-10-27.
https://github.com/facebook/rocksdb/wiki/Compaction. Difference: the taxonomy and the
some-to-some overlap rule are read as the deployed family this paper models; no policy of theirs
is evaluated.

[241] RocksDB. (2026). RocksDB Overview. RocksDB wiki, revision read 2026-10-27.
https://github.com/facebook/rocksdb/wiki/RocksDB-Overview. Difference: level style versus
universal style is read as background; the merge decision itself is not specified there.

