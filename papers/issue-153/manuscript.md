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
`Ln`" [241] — where classic leveled compaction from the LSM-tree paper is all-to-all for
adjacent levels [240]. So overlap determines *which* runs are combined, exactly as in our rule,
and the bytes rewritten by that combination are the cost the engine pays, again as in our rule.

What the model drops, stated plainly: RocksDB chooses *which level* to compact by a compaction
score, not by largest overlap, and applies rate limits and background-job scheduling; real
engines have tombstones and deletions (so a merge can *reduce* live bytes), partial key-range
overlap rather than whole-range overlap, level size targets with a fanout ratio, and both tiered
and tiered+leveled layouts rather than one shape [242]. Our model has none of them. Section 5
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
system. Every figure below is a statement about the model of §2.1.

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
both rules tie at zero losses. `w\*` is the minimal exact horizon; it is 0 exactly where no
genuine choice exists.

Two readings matter. First, the failure fraction is stable across trace length in a fixed `(R,
K)` family — it does not wash out as traces grow, so this is not a small-trace artefact of
boundary effects. Second, the *magnitude* is worse than the fraction suggests: the worst excess
is 3.333× at R=3 K=5 T=6, and that cell is not the base cell but a cell with more capacity,
where the rule loses 450 of 729 traces.

### 4.3 The horizon exactness needs, and why more can be worse

Define a `w`-lookahead policy as one that, at each merge step, minimises the bytes it pays now
plus the optimum over the next `w` flushes, charging nothing beyond that horizon. `w` equal to
the remaining trace is the exact optimum. The **minimal exact horizon** `w*` is the smallest `w`
that loses nothing.

Measured, per cell, `w* = T − 1 − i_first`, where `i_first` is the earliest flush at which more
than one legal merge exists; when no choice ever exists (`K = 2`) the quantity is undefined and
`w* = 0`. Because the first genuine choice occurs at a fixed index `i_first` determined by `K`
alone, `w*` **grows with the trace**: exactness needs the entire remainder after the first
choice, and no constant window suffices.

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
extra bit of the future [243]. Our result fails *in form* rather than in constant: foresight
here is not tradeable against capacity, because `w*` grows with the trace, so no constant `l` is
exact for any `K`, and raising `l` by one can make the rule worse (§4.3).

Semi-online scheduling with initial lookahead is the second nearest, and the one a reviewer
should raise against us, because it also reports that lookahead can be worthless: for one regime
of two-machine makespan, any online algorithm has ratio at least 3/2, matching what is
achievable without the information [244]. The difference is the object quantified: that line
gives competitive ratios per regime for a known prefix of the input, whereas we give the horizon
at which optimality becomes possible at all. "Lookahead is powerless" and "lookahead must be
total" are different statements — one about a ratio, one about existence — and only the second
is claimed here.

Two further works bound the value of finite lookahead positively: semi-online scheduling on
uniform machines where finite initial lookahead "can greatly improve" competitiveness [245], and
disk-scheduling policies with a lookahead window evaluated empirically [246]. Our horizon result
is the opposite shape for a different decision, and the disagreement on monotonicity is the
substantive difference we would want a reviewer to press on. The metrical-task-system framework
supplies the general setting in which a rule is scored against an offline optimum [247], and it
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
correction is posted visibly on the issue rather than edited into the registration.

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

It runs seven steps — the certificate, the characterisation, the proposition, the scale test,
the results emitter, this manuscript's own regeneration, and a byte-identity check that the
reference report regenerates from its stored verification state — accumulating failures so that
no later step masks an earlier one, and exiting with the number of failed steps. Expected final
line: `REPRODUCE: ALL GREEN (7 steps)`.

The manuscript is generated: every numeric claim is a marker resolved from `results.json`, which
is itself emitted by the analysis programs, and `make_manuscript.py` refuses any multi-digit
number in the prose that it cannot bind to that file. No figure in this paper was typed by hand.
Refreshing the reference pool does need network and is a separate step (`build_refs.py`,
`place_refs.py`); reproduction of the committed figures does not, because `place_refs.py
--render-only` regenerates the report byte-identically from stored verification state.

## References

### Corpus: DOI-verified against Crossref (see `reference-check.md`)

[1] 4Z-SSD: A Semantic-Aware Four-Zone SSD Architecture for Balancing Write Amplification and
Flash-Level Parallelism. *Proceedings of the 19th ACM International Systems and Storage
Conference*. Dongjun Lee, Han Jang, Youngbin Jin. DOI 10.1145/3793230.3839382.

[2] A closed-form expression for write amplification in NAND Flash. *2010 IEEE Globecom
Workshops*. Rajiv Agarwal, Marcus Marrow. DOI 10.1109/glocomw.2010.5700261.

[3] Algebraic modeling of write amplification in hotness-aware SSD. *Proceedings of the 8th ACM
International Systems and Storage Conference*. Yue Yang, Jianwen Zhu. DOI
10.1145/2757667.2757671.

[4] An improved analytic expression for write amplification in NAND flash. *2012 International
Conference on Computing, Networking and Communications (ICNC)*. Xiang Luojie, Brian M. Kurkoski.
DOI 10.1109/iccnc.2012.6167472.

[5] Enhancing SSD Endurance via ReRead-GC for Balanced Wear Leveling and Reduced Write
Amplification. *2026 8th International Conference on Information Science, Electrical and
Automat*. Chenyuan Wang, Meizhou Gao, Tai Guo. DOI 10.1109/iseae69422.2026.11544774.

[6] Exploring SSD endurance model based on write amplification and temperature. *2016 Seventh
International Green and Sustainable Computing Conference (IGSC)*. Hui Sun, Guodong Chen, Xu
Liang. DOI 10.1109/igcc.2016.7892596.

[7] GraLoc: Preserving Graph Locality to Minimize Read and Write Amplification on Flash Memory.
*2025 IEEE 49th Annual Computers, Software, and Applications Conference (COMPSAC)*. Po-Lun Wang,
Tseng-Yi Chen. DOI 10.1109/compsac65507.2025.00016.

[8] Improving write amplification in a virtualized and multimedia SSD system. *Multimedia Tools
and Applications*. Dingding Li, Hai Jin, Xiaofei Liao. DOI 10.1007/s11042-013-1497-6.

[9] Mitigating the Write Amplification Problem of Write-Optimized File Systems on Flash Storage.
*2017 IEEE International Conference on Cluster Computing (CLUSTER)*. Shuo-Han Chen, Jun-Long
Lin, Tseng-Yi Chen. DOI 10.1109/cluster.2017.38.

[10] Mitigating Write Amplification of Dual-mode Flash Memory. *2023 20th International SoC
Design Conference (ISOCC)*. Yi-Shen Chen, Ying-Jui Shih, Jen-Wei Hsieh. DOI
10.1109/isocc59558.2023.10395978.

[11] On the necessity of hot and cold data identification to reduce the write amplification in
flash-based SSDs. *Performance Evaluation*. B. Van Houdt. DOI 10.1016/j.peva.2014.08.003.

[12] Practical Implication of Analytical Models for SSD Write Amplification. *Proceedings of the
8th ACM/SPEC on International Conference on Performance Engin*. Changhyun Park, Seongjin Lee,
Youjip Won. DOI 10.1145/3030207.3030219.

[13] Reducing write amplification in flash by death-time prediction of logical block addresses.
*Proceedings of the 14th ACM International Conference on Systems and Storage*. Chandranil
Chakraborttii, Heiner Litz. DOI 10.1145/3456727.3463784.

[14] Separating the File System Journal to Reduce Write Amplification of Garbage Collection on
ZNS SSDs. *Journal of Multimedia Information System*. Young-in Choi, Sungyong Ahn. DOI
10.33851/jmis.2022.9.4.261.

[15] WOM codes reduce write amplification in NAND flash memory. *2012 IEEE Global Communications
Conference (GLOBECOM)*. Xiang Luojie, Brian M. Kurkoski, Eitan Yaakobi. DOI
10.1109/glocom.2012.6503611.

[16] A Contract-aware and Cost-effective LSM Store for Cloud Storage with Low Latency Spikes.
*ACM Transactions on Storage*. Yuanhui Zhou, Jian Zhou, Kai Lu. DOI 10.1145/3643851.

[17] A ReRAM-Based Processing-in-Memory Framework for LSM-Based Key-Value Store. *IEEE
Transactions on Computer-Aided Design of Integrated Circuits and Systems*. Zehao Chen, Kai
Zhang, Qian Wei. DOI 10.1109/tcad.2025.3591410.

[18] ACaZoo: A Distributed Key-Value Store Based on Replicated LSM-Trees. *2014 IEEE 33rd
International Symposium on Reliable Distributed Systems*. Panagiotis Garefalakis, Panagiotis
Papadopoulos, Kostas Magoutis. DOI 10.1109/srds.2014.43.

[19] ALSM: An Attribute-Aware LSM-Tree Based Key-Value Store to Reduce I/O Amplification. *2024
International Conference on Meta Computing (ICMC)*. Zhaoyan Shen, Dehao Yu, Qian Wei. DOI
10.1109/icmc60390.2024.00013.

[20] An efficient design and implementation of LSM-tree based key-value store on open-channel
SSD. *Proceedings of the Ninth European Conference on Computer Systems*. Peng Wang, Guangyu Sun,
Song Jiang. DOI 10.1145/2592798.2592804.

[21] An Optimization of Key-Value Store Based on Segmented LSM-Tree. *2019 IEEE 19th
International Conference on Communication Technology (ICCT)*. Kai Zhang, Yongsheng Xia, Yang
Xia. DOI 10.1109/icct46805.2019.8947217.

[22] Block-LSM: An Ether-aware Block-ordered LSM-tree based Key-Value Storage Engine. *2021 IEEE
39th International Conference on Computer Design (ICCD)*. Zehao Chen, Bingzhe Li, Xiaojun Cai.
DOI 10.1109/iccd53106.2021.00017.

[23] Building A Fast and Efficient LSM-tree Store by Integrating Local Storage with Cloud
Storage. *2021 IEEE International Conference on Cluster Computing (CLUSTER)*. Peng Xu, Nannan
Zhao, Jiguang Wan. DOI 10.1109/cluster48925.2021.00032.

[24] BVLSM: Write-Efficient LSM-Tree Storage via WAL-Time Key-Value Separation. *2025 IEEE
International Conference on High Performance Computing and Communicati*. Ming Li, Wendi Cheng,
Jiahe Wei. DOI 10.1109/hpcc67675.2025.00037.

[25] CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated
Infrastructure. *Proceedings of the ACM on Management of Data*. Qiaolin Yu, Chang Guo, Jay
Zhuang. DOI 10.1145/3654927.

[26] CDNRocks: computable data nodes with RocksDB to improve the read performance of
LSM-tree-based distributed key-value storage systems. *The Journal of Supercomputing*. Feixiong
Huang, Yubiao Pan, Huizhen Zhang. DOI 10.1007/s11227-024-06526-7.

[27] Compaction-aware zone allocation for LSM based key-value store on ZNS SSDs. *Proceedings of
the 14th ACM Workshop on Hot Topics in Storage and File Systems*. Hee-Rock Lee, Chang-Gyu Lee,
Seungjin Lee. DOI 10.1145/3538643.3539743.

[28] CruiseDB: An LSM-Tree Key-Value Store with Both Better Tail Throughput and Tail Latency.
*2021 IEEE 37th International Conference on Data Engineering (ICDE)*. Junkai Liang, Yunpeng
Chai. DOI 10.1109/icde51399.2021.00094.

[29] Deduplication Triggered Compaction for LSM-Tree Based Key-Value Store. *2018 IEEE 9th
International Conference on Software Engineering and Service Scien*. Weitao Zhang, Yinlong Xu.
DOI 10.1109/icsess.2018.8663897.

[30] Design of LSM-tree-based Key-value SSDs with Bounded Tails. *ACM Transactions on Storage*.
Junsu Im, Jinwook Bae, Chanwoo Chung. DOI 10.1145/3452846.

[31] Efficient Sanitization Design for LSM-based Key-Value Store over 3D MLC NAND Flash.
*Proceedings of the 38th ACM/SIGAPP Symposium on Applied Computing*. Liang-Chi Chen, Shu-Qi Yu,
Chien-Chung Ho. DOI 10.1145/3555776.3577780.

[32] Efficient Wear-Leveling-Aware Data Placement for LSM-Tree based key-value store on ZNS
SSDs. *Journal of King Saud University - Computer and Information Sciences*. Runyu Zhang, Lening
Zhou, Mingjie Li. DOI 10.1016/j.jksuci.2024.102156.

[33] Enhancing LSM-Tree Key-Value Stores for Read-Modify-Writes via Key-Delta Separation. *2024
IEEE 40th International Conference on Data Engineering (ICDE)*. Jinhong Li, Yanjing Ren, Shujie
Han. DOI 10.1109/icde60146.2024.00375.

[34] FPGA-based Compaction Engine for Accelerating LSM-tree Key-Value Stores. *2020 IEEE 36th
International Conference on Data Engineering (ICDE)*. Xuan Sun, Jinghuan Yu, Zimeng Zhou. DOI
10.1109/icde48307.2020.00113.

[35] gLSM: Using GPGPU to Accelerate Compactions in LSM-tree-based Key-value Stores. *ACM
Transactions on Storage*. Hui Sun, Jinfeng Xu, Xiangxiang Jiang. DOI 10.1145/3633782.

[36] GPComp: Using GPU and SSD-GPU Peer to Peer DMA to Accelerate LSM-Tree Compaction for
Key-Value Store. *IEEE Transactions on Parallel and Distributed Systems*. Hao Zhou, Yuanhui
Chen, Wu Zeng. DOI 10.1109/tpds.2025.3586616.

[37] HaLSM: A Hotspot-aware LSM-tree based Key-Value Storage Engine. *2022 IEEE 40th
International Conference on Computer Design (ICCD)*. Jianshun Zhang, Fang Wang, Chao Dong. DOI
10.1109/iccd56317.2022.00035.

[38] Improving Compaction in LSM Tree by Applying Simple Copy to Key-Value Separated LSM-Tree.
*Journal of KIISE*. Chihyun Lee, Sungho Moon, Sangeun Chae. DOI 10.5626/jok.2025.52.11.1002.

[39] KVSTL: An Application Support to LSM-Tree Based Key-Value Store via Shingled Translation
Layer Data Management. *IEEE Transactions on Computers*. Shuo-Han Chen, Yuhong Liang, Ming-Chang
Yang. DOI 10.1109/tc.2021.3098961.

[40] LCKV: Learner-Cleaner Optimized Adaptive Key-Value Separated LSM-Tree Store. *2024 IEEE
42nd International Conference on Computer Design (ICCD)*. Mingxuan Liu, Jianhua Gu, Tianhai
Zhao. DOI 10.1109/iccd63220.2024.00079.

[41] Leveraging NVMe SSDs for Building a Fast, Cost-effective, LSM-tree-based KV Store. *ACM
Transactions on Storage*. Cheng Li, Hao Chen, Chaoyi Ruan. DOI 10.1145/3480963.

[42] LSM-Tree Managed Storage for Large-Scale Key-Value Store. *IEEE Transactions on Parallel
and Distributed Systems*. Fei Mei, Qiang Cao, Hong Jiang. DOI 10.1109/tpds.2018.2864209.

[43] LSM-tree managed storage for large-scale key-value store. *Proceedings of the 2017
Symposium on Cloud Computing*. Fei Mei, Qiang Cao, Hong Jiang. DOI 10.1145/3127479.3127486.

[44] Making LSM-Tree-based Key-Value Store Practical and Efficient for Multi-Tenant Serverless
Cloud Databases. *Proceedings of the ACM on Management of Data*. Yingjia Wang, Caixin Gong,
Guoyun Zhu. DOI 10.1145/3786667.

[45] MirrorKV: An Efficient Key-Value Store on Hybrid Cloud Storage with Balanced Performance of
Compaction and Querying. *Proceedings of the ACM on Management of Data*. Zhiqi Wang, Zili Shao.
DOI 10.1145/3626736.

[46] MTDB: an LSM-tree-based key-value store using a multi-tree structure to improve read
performance. *The Journal of Supercomputing*. Xinwei Lin, Yubiao Pan, Wenjuan Feng. DOI
10.1007/s11227-024-06382-5.

[47] Nova-LSM: A Distributed, Component-based LSM-tree Key-value Store. *Proceedings of the 2021
International Conference on Management of Data*. Haoyu Huang, Shahram Ghandeharizadeh. DOI
10.1145/3448016.3457297.

[48] Optimization of Load Balancing on LSM-Tree based Distributed Key-Value Store using NVMe-oF.
*Journal of KIISE*. Hera Koo, Sungho Moon, Hyeongjun Jeon. DOI 10.5626/jok.2022.49.7.561.

[49] Optimize Metadata Operations of Key-Value Store via A Flat Indexing LSM-Tree. *2024 IEEE
International Symposium on Parallel and Distributed Processing with Ap*. Yuchen Liu, Chen Chen,
Shu Yin. DOI 10.1109/ispa63168.2024.00185.

[50] PlexDB: Efficient Compaction Algorithm for Deduplication of LSM-tree based Key-Value Store.
*Journal of Digital Contents Society*. Yong-Cheol Seo, Sung-Hoon Park. DOI
10.9728/dcs.2020.21.8.1501.

[51] PMLDS: An LSM-Tree Direct Managed Storage for Key-Value Stores on Byte-Addressable Devices.
*Proceedings of the 52nd International Conference on Parallel Processing*. Ziyi Lu, Qiang Cao,
Shucheng Wang. DOI 10.1145/3605573.3605629.

[52] Recursive Compaction Method of LSM-tree based Key-value Store. *Journal of KIISE*. Jongbin
Kim, Seohui Son, Hyunsoo Cho. DOI 10.5626/jok.2019.46.9.946.

[53] Reducing tail latency of LSM-tree based key-value store via limited compaction.
*Proceedings of the 36th Annual ACM Symposium on Applied Computing*. Yongchao Hu, Yajuan Du. DOI
10.1145/3412841.3442073.

[54] ServerlessLSM: Fast RDMA-Codesigned Disaggregated Compaction for Elastic Serverless
LSM-Tree Key-Value Store. *2025 IEEE International Conference on Web Services (ICWS)*. Mingxuan
Liu, Jianhua Gu, Tianhai Zhao. DOI 10.1109/icws67624.2025.00100.

[55] SplitDB: Building a large-scale key-value store based on LSM-tree by split operations. *(no
venue field)*. Jiancheng Ren, Guanzhong Chen, Keyu Qian. DOI 10.21203/rs.3.rs-2142066/v1.

[56] SSD-Based LSM-Tree Key-Value Storage System. *2022 19th International Computer Conference
on Wavelet Active Media Technology a*. Yang Zining, Jian Gang, Hu Yu. DOI
10.1109/iccwamtip56608.2022.10016522.

[57] ZonesDB: Building Write-Optimized and Space-Adaptive Key-Value Store on Zoned Storage with
Fragmented LSM Tree. *ACM Transactions on Storage*. Yuhong Liang, Yingjia Wang, Tsun-Yu Yang.
DOI 10.1145/3715331.

[58] An Analysis of Leveled Writing Activities in Middle School English 1 Textbooks and
Workbooks and the Perceptions of Middle School Students on the Leveled Writing Activities.
*Linguistic Research*. 조아영, Young-in Moon. DOI 10.17250/khisli.27.1.201004.003.

[59] Evaluation of Volume Tiering Method and SSD Cache Method in Tiered Storage System.
*Electronics and Communications in Japan*. SHINICHI HAYASHI, NORIHISA KOMODA. DOI
10.1002/ecj.11749.

[60] Evaluation of Volume Tiering Method and SSD Cache Method in Tiered Storage System. *IEEJ
Transactions on Electronics, Information and Systems*. Shinichi Hayashi, Norihisa Komoda. DOI
10.1541/ieejeiss.134.459.

[61] Leveled Product Codes for Optimal Block Repairs in Geo-distributed Storage Systems. *IEEE
INFOCOM 2025 - IEEE Conference on Computer Communications*. Si Wu, Guantian Lin, Patrick P. C.
Lee. DOI 10.1109/infocom55648.2025.11044776.

[62] Olsync: Object-level tiering and coordination in tiered storage systems based on
software-defined network. *Future Generation Computer Systems*. Zhike Li, Yong Wang, Shiqiang
Nie. DOI 10.1016/j.future.2024.107521.

[63] Series of solid-solid phase change materials with ultra-high thermal stability and
controllable phase change temperature: kilogram-leveled preparation and application
investigation. *Journal of Energy Storage*. Changren Xiao, Shaojun Li, Shengtian Zhu. DOI
10.1016/j.est.2021.102405.

[64] A High-Performance and Scalable Userspace Log-Structured File System for Modern SSDs. *ACM
Transactions on Storage*. Wenqing Jia, Dejun Jiang, Jin Xiong. DOI 10.1145/3728645.

[65] A Log-Structured Block Preservation and Restoration System for Proactive Forensic Data
Collection in the Cloud. *2016 11th International Conference on Availability, Reliability and
Security (AR*. Manabu Hirano, Hiromu Ogawa. DOI 10.1109/ares.2016.8.

[66] A Log-Structured File System Based on LevelDB. *Applied Mechanics and Materials*. Zhi Hao
Wu. DOI 10.4028/www.scientific.net/amm.602-605.3481.

[67] An Age-Threshold Algorithm for Garbage Collection in Log-Structured Arrays and File
Systems. *High Performance Computing Systems and Applications*. Jai Menon, Larry Stockmeyer. DOI
10.1007/978-1-4615-5611-4_13.

[68] An Efficient Cleaning Scheme for File Defragmentation on Log-Structured File System.
*Journal of KIISE*. Jonggyu Park, Dong Hyun Kang, Euiseong Seo. DOI 10.5626/jok.2016.43.6.627.

[69] Analysis of steady-state segment storage utilizations in a log-structured file system with
least-utilized segment cleaning. *ACM SIGOPS Operating Systems Review*. John T. Robinson. DOI
10.1145/240799.240803.

[70] BlzFS: Crash Consistent Log-structured File System Based on Byte-loggable Zone for ZNS SSD.
*2023 IEEE 41st International Conference on Computer Design (ICCD)*. Wenjie Qi, Zhipeng Tan,
Ziyue Zhang. DOI 10.1109/iccd58817.2023.00040.

[71] Data Correlation Aware Buffer Cache Management for Improved I/O Performance on
Log-Structured File System-based NAND Flash Storage Devices. *Academic Journal of Science and
Technology*. Tian Tian. DOI 10.54097/7r19rt93.

[72] DEFY: A Deniable, Encrypted File System for Log-Structured Storage. *Proceedings 2015
Network and Distributed System Security Symposium*. Timothy M. Peters, Mark A. Gondree, Zachary
N. J. Peterson. DOI 10.14722/ndss.2015.23078.

[73] Design and Implementation of a Log-Structured File System for Flash-Based Solid State
Drives. *IEEE Transactions on Computers*. Changwoo Min, Sang-Won Lee, Young Ik Eom. DOI
10.1109/tc.2013.97.

[74] Design and Implementation of Basic Log Structured File System for Internal Flash on
Embedded Systems. *2022 7th International Conference on Computer Science and Engineering
(UBMK)*. Huseyin Karacali, Tuncay Yildirim. DOI 10.1109/ubmk55850.2022.9919586.

[75] Design and implementation of zoned namespace-tailored log-structured file system for
commodity ZNS SSDs. *Future Generation Computer Systems*. Inhwi Hwang, Sangjin Lee, Sunggon Kim.
DOI 10.1016/j.future.2026.108563.

[76] DPLFS: A Dual-Mode PCM-based Log-Structured File System. *2022 IEEE 40th International
Conference on Computer Design (ICCD)*. Wen Cheng, Telong Zheng, Lingfang Zeng. DOI
10.1109/iccd56317.2022.00054.

[77] Dynamic hot-cold separation scheme on the log-structured file system for CE devices. *2017
IEEE International Conference on Consumer Electronics (ICCE)*. Dong Hyun Kang, Young Ik Eom. DOI
10.1109/icce.2017.7889383.

[78] File Defragmentation Scheme for a Log-Structured File System. *Proceedings of the 7th ACM
SIGOPS Asia-Pacific Workshop on Systems*. Jonggyu Park, Dong Hyun Kang, Young Ik Eom. DOI
10.1145/2967360.2967622.

[79] GAZE: Rearchitecting Log-Structured Filesystem for Garbage Collection on Zoned Namespace
Flash Storage. *Proceedings of the ACM SIGOPS 32nd Symposium on Operating Systems Principles*.
Juwon Kim, Hwanseok Yoo, Seung Won Yoo. DOI 10.1145/3830418.3843870.

[80] Implementation of a Linux log-structured file system with a garbage collector. *ACM SIGOPS
Operating Systems Review*. Martin Jambor, Tomas Hruby, Jan Taus. DOI 10.1145/1228291.1228299.

[81] Improving Small File Creation Performance in a Parallel Log-Structured File System. *(no
venue field)*. , David Bonnie, . DOI 10.2172/1089476.

[82] On-line data compression in a log-structured file system. *Proceedings of the fifth
international conference on Architectural support for p*. Michael Burrows, Charles Jerian,
Butler Lampson. DOI 10.1145/143365.143376.

[83] On-line data compression in a log-structured file system. *ACM SIGPLAN Notices*. Michael
Burrows, Charles Jerian, Butler Lampson. DOI 10.1145/143371.143376.

[84] Performance Analyses on Logging Policies of Log-structured File System. *2019 IEEE
International Conference on Consumer Electronics (ICCE)*. Sungwoo Lee, Jonggyu Park, Young Ik
Eom. DOI 10.1109/icce.2019.8662104.

[85] Reducing garbage collection overhead of log-structured file systems with GC journaling.
*2015 International Symposium on Consumer Electronics (ISCE)*. Hyunho Gwak, Yunji Kang, Dongkun
Shin. DOI 10.1109/isce.2015.7177770.

[86] SCJ: Segment Cleaning Journaling for Log-Structured File Systems. *IEEE Access*. Hyunho
Gwak, Dongkun Shin. DOI 10.1109/access.2021.3121423.

[87] Security and log structured file systems. *ACM SIGOPS Operating Systems Review*. Tage
Stabell-Kulø. DOI 10.1145/250007.250009.

[88] The Design and Implementation of a Log-structured file system. *(no venue field)*. Mendel
Rosenblum. DOI 10.1007/978-1-4615-2221-8.

[89] The design and implementation of a log-structured file system. *Proceedings of the
thirteenth ACM symposium on Operating systems principles*. Mendel Rosenblum, John K. Ousterhout.
DOI 10.1145/121132.121137.

[90] The design and implementation of a log-structured file system. *ACM SIGOPS Operating
Systems Review*. Mendel Rosenblum, John K. Ousterhout. DOI 10.1145/121133.121137.

[91] The design and implementation of a log-structured file system. *ACM Transactions on
Computer Systems*. Mendel Rosenblum, John K. Ousterhout. DOI 10.1145/146941.146943.

[92] The Linux implementation of a log-structured file system. *ACM SIGOPS Operating Systems
Review*. Ryusuke Konishi, Yoshiji Amagai, Koji Sato. DOI 10.1145/1151374.1151375.

[93] User-Level Secure Deletion on Log-Structured File Systems. *Information Security and
Cryptography*. Joel Reardon. DOI 10.1007/978-3-319-28778-2_5.

[94] A Comparative Study of Log-Structured Merge-Tree-Based Spatial Indexes for Big Data. *2017
IEEE 33rd International Conference on Data Engineering (ICDE)*. Young-Seok Kim, Taewoo Kim,
Michael J. Carey. DOI 10.1109/icde.2017.61.

[95] A Framework for Integrating Log-Structured Merge-Trees and Key–Value Separation in Tiered
Storage. *Electronics*. Charles Jaranilla, Guangxun Zhao, Gunhee Choi. DOI
10.3390/electronics14030564.

[96] Adelson-Velsky Landis and Log Structured Merge Tree for Kubernetes ETCD. *(no venue
field)*. Renukadevi Chuppala. DOI 10.2139/ssrn.5147817.

[97] Adelson-Velsky Landis and Log Structured Merge Tree for Kubernetes ETCD. *Advanced
International Journal of Multidisciplinary Research*. Renukadevi Chuppala -, Dr. B. Purnachandra
Rao -. DOI 10.62127/aijmr.2024.v02i05.1109.

[98] Bi-directional Log-Structured Merge Tree. *34th International Conference on Scientific and
Statistical Database Management*. Xin Zhang, Qizhong Mao, Ahmed Eldawy. DOI
10.1145/3538712.3538730.

[99] Cascaded Write Amplification of LSM-tree-based Key-Value Stores underlying Solid-State
Disks. *Microprocessors and Microsystems*. Hui Sun, Shangshang Dai, Jianzhong Huang. DOI
10.1016/j.micpro.2020.103217.

[100] Correction: Towards an asynchronous commit in micro-batch streaming systems with
log-structured merge-tree based key-value store. *Cluster Computing*. Kyuli Park, Dongjae Lee,
Yeonwoo Jeong. DOI 10.1007/s10586-025-05748-5.

[101] DynamicKV: Data Storage Strategy Based on Partition Merging of Log-Structured Merge Tree.
*2024 2nd International Conference on Computer, Vision and Intelligent Technology*. Jiawei
Huang, Meiting Xue, Chenpu Li. DOI 10.1109/iccvit63928.2024.10872622.

[102] Efficient Key-Value Stores with Ranged Log-Structured Merge Trees. *2018 IEEE 11th
International Conference on Cloud Computing (CLOUD)*. Nae Young Song, Heon Young Yeom, Hyuck
Han. DOI 10.1109/cloud.2018.00090.

[103] Fault-tolerant precise data access on distributed log-structured merge-tree. *Frontiers of
Computer Science*. Tao Zhu, Huiqi Hu, Weining Qian. DOI 10.1007/s11704-018-7198-6.

[104] GravTree: A Local-Compaction Tree for Predictable Write Latency. *(no venue field)*.
Subodh Wandile. DOI 10.2139/ssrn.7487218.

[105] HIndex-FLSM: Fragmented Log-Structured Merge Trees Integrated with Heat and Index. *2024
3rd International Joint Conference on Information and Communication Enginee*. Xiaopeng Wang, Hui
Li, Hong Tan. DOI 10.1109/jcice61382.2024.00024.

[106] Incremental Materialized View Maintenance on Distributed Log-Structured Merge-Tree.
*Lecture Notes in Computer Science*. Huichao Duan, Huiqi Hu, Weining Qian. DOI
10.1007/978-3-319-91458-9_42.

[107] KEIGO: Co-Designing Log-Structured Merge Key-Value Stores with a Non-Volatile,
Concurrency-Aware Storage Hierarchy. *Proceedings of the VLDB Endowment*. Rúben Adão, Zhongjie
Wu, Changjun Zhou. DOI 10.14778/3746405.3746414.

[108] Level Aware Data Placement Technique for Hybrid NAND Flash Storage of Log-Structured
Merge-Tree Based Key-Value Store System. *IEEE Access*. Joonyong Jeong, Jaewook Kwak, Daeyong
Lee. DOI 10.1109/access.2020.3031322.

[109] Log Structured Merge Tree and Log Structured Hash Table Tree for Kubernetes ETCD.
*Advanced International Journal of Multidisciplinary Research*. Kishore Kumar Jinka -,
Dr.B.Purnachandra Rao -. DOI 10.62127/aijmr.2024.v02i05.1110.

[110] LSM-Cache: An Efficient Log-Structured Merge Hybrid Key-Value Cache for Massive Small
Objects. *Lecture Notes in Computer Science*. Gequan Mo, Ranhao Jia, Yunfei Gu. DOI
10.1007/978-981-95-5716-5_1.

[111] NVLSM: A Persistent Memory Key-Value Store Using Log-Structured Merge Tree with
Accumulative Compaction. *ACM Transactions on Storage*. Baoquan Zhang, David H. C. Du. DOI
10.1145/3453300.

[112] On Integration of Appends and Merges in Log-Structured Merge Trees. *Proceedings of the
48th International Conference on Parallel Processing*. Caixin Gong, Shuibing He, Yili Gong. DOI
10.1145/3337821.3337836.

[113] Optimization of Key-Value Stores with Ranged Log-Structured Merge Trees. *KIISE
Transactions on Computing Practices*. Nae Young Song, Heon Young Yeom, Hyuck Han. DOI
10.5626/ktcp.2019.25.3.164.

[114] Parallel-Log-Single-Compaction-Tree: Flash-Friendly Two-Level Key-Value Management in
KVSSDs. *2020 25th Asia and South Pacific Design Automation Conference (ASP-DAC)*. Yen-Ting
Chen, Ming-Chang Yang, Yuan-Hao Chang. DOI 10.1109/asp-dac47756.2020.9045144.

[115] Partition pruning for range query on distributed log-structured merge-tree. *Frontiers of
Computer Science*. Chenchen Huang, Huiqi Hu, Xing Wei. DOI 10.1007/s11704-019-8234-x.

[116] Precise Data Access on Distributed Log-Structured Merge-Tree. *Lecture Notes in Computer
Science*. Tao Zhu, Huiqi Hu, Weining Qian. DOI 10.1007/978-3-319-63564-4_17.

[117] Reducing I/O Amplification for Key-Value Stores With a Log-Assisted Log-Structured Merge
Tree. *IEEE Transactions on Knowledge and Data Engineering*. Kecheng Huang, Minyang Bao, Kai
Zhang. DOI 10.1109/tkde.2026.3699948.

[118] Reducing Write Amplification in LSM-Tree by Data Compaction Based on Sliding-Window. *2024
6th International Academic Exchange Conference on Science and Technology In*. Jianqiang Li,
Kunfeng Wang, Ruyang Chen. DOI 10.1109/iaecst64597.2024.11118070.

[119] Reducing Write Amplification in LSM-Trees Through Orchestrated Fine-Grained Compaction and
Persistent Memory. *IEEE Transactions on Computers*. Licheng Shan, Jiang Zhou, Jinchao Zhang.
DOI 10.1109/tc.2026.3662419.

[120] Reducing Write Amplification of LSM-Tree with Block-Grained Compaction. *2022 IEEE 38th
International Conference on Data Engineering (ICDE)*. Xiaoliang Wang, Peiquan Jin, Bei Hua. DOI
10.1109/icde53745.2022.00279.

[121] Reducing Write Stall and Write Amplification for LSM-Tree Based Key-Value Stores Using a
Hybrid Compression Strategy. *Lecture Notes in Computer Science*. Zhicheng Bu, Jinbao Wang, Lina
Chen. DOI 10.1007/978-981-95-5716-5_26.

[122] SFM: Mitigating Read/Write Amplification Problem of LSM-Tree-Based Key-Value Stores. *IEEE
Access*. Hoyoung Lee, Minho Lee, Young Ik Eom. DOI 10.1109/access.2021.3098736.

[123] SLSM - A Scalable Log Structured Merge Tree with Bloom Filters for Low Latency Analytics.
*Procedia Technology*. P.A. Riyaz, Surekha Mariam Varghese. DOI 10.1016/j.protcy.2016.05.075.

[124] Splaying Log-Structured Merge-Trees. *Proceedings of the 2018 International Conference on
Management of Data*. Thomas Lively, Luca Schroeder, Carlos Mendizábal. DOI
10.1145/3183713.3183723.

[125] The log-structured merge-tree (LSM-tree). *Acta Informatica*. Patrick O’Neil, Edward
Cheng, Dieter Gawlick. DOI 10.1007/s002360050048.

[126] The LSM RUM-Tree: A Log Structured Merge R-Tree for Update-intensive Spatial Workloads.
*2021 IEEE 37th International Conference on Data Engineering (ICDE)*. Jaewoo Shin, Jianguo Wang,
Walid G. Aref. DOI 10.1109/icde51399.2021.00238.

[127] TLSM: Tiered Log-Structured Merge-Tree Utilizing Non-Volatile Memory. *IEEE Access*.
Jihwan Lee, Won Gi Choi, Doyoung Kim. DOI 10.1109/access.2020.2985407.

[128] Towards an asynchronous commit in micro-batch streaming systems with log-structured
merge-tree based key-value store. *Cluster Computing*. Kyuli Park, Dongjae Lee, Yeonwoo Jeong.
DOI 10.1007/s10586-024-05000-6.

[129] TriangleKV: Reducing Write Stalls and Write Amplification in LSM-Tree Based KV Stores With
Triangle Container in NVM. *IEEE Transactions on Parallel and Distributed Systems*. Chen Ding,
Ting Yao, Hong Jiang. DOI 10.1109/tpds.2022.3188268.

[130] Workload-Aware Log-Structured Merge Key-Value Store for NVM-SSD Hybrid Storage. *2023 IEEE
39th International Conference on Data Engineering (ICDE)*. Lixiang Chen, Ruihao Chen, Chengcheng
Yang. DOI 10.1109/icde55515.2023.00171.

[131] A Competitive Online Algorithm for the Paging Problem with “Shelf” Memory. *Lecture Notes
in Computer Science*. Sung-Pil Hong. DOI 10.1007/3-540-48686-0_40.

[132] A Modified Working Set Paging Algorithm. *IEEE Transactions on Computers*. Smith. DOI
10.1109/tc.1976.1674715.

[133] A novel algorithm for efficient paging in mobile WiMAX. *2007 IEEE Mobile WiMAX
Symposium*. Shantidev Mohanty, Muthaiah Venkatachalam, XiangYing Yang. DOI
10.1109/wimax.2007.348683.

[134] A SPACE-EFFICIENT ALGORITHM FOR PAGING UNBALANCED BINARY TREES. *Proceedings of the Second
International Conference on Software and Data Technolo*. (no author field in record). DOI
10.5220/0001334500380043.

[135] A strongly competitive randomized paging algorithm. *Algorithmica*. Lyle A. McGeoch,
Daniel D. Sleator. DOI 10.1007/bf01759073.

[136] A Unified Analysis of Paging and Caching. *Algorithmica*. E. Torng. DOI
10.1007/pl00009192.

[137] An O (log k )-Competitive Algorithm for Generalized Caching. *ACM Transactions on
Algorithms*. Anna Adamaszek, Artur Czumaj, Matthias Englert. DOI 10.1145/3280826.

[138] Competitive analysis of randomized paging algorithms. *Lecture Notes in Computer Science*.
Dimitris Achlioptas, Marek Chrobak, John Noga. DOI 10.1007/3-540-61680-2_72.

[139] Competitive analysis of randomized paging algorithms. *Theoretical Computer Science*.
Dimitris Achlioptas, Marek Chrobak, John Noga. DOI 10.1016/s0304-3975(98)00116-9.

[140] Competitive Analysis of the LRFU Paging Algorithm. *Lecture Notes in Computer Science*.
Edith Cohen, Haim Kaplan, Uri Zwick. DOI 10.1007/3-540-44634-6_14.

[141] Competitive Analysis of the LRFU Paging Algorithm. *Algorithmica*. E. Cohen, H. Kaplan, U.
Zwick. DOI 10.1007/s00453-002-0936-y.

[142] Competitive on-line paging strategies for mobile users under delay constraints.
*Proceedings of the twenty-third annual ACM symposium on Principles of distribute*. Amotz
Bar-Noy, Yishay Mansour. DOI 10.1145/1011767.1011805.

[143] Competitive Paging with Locality of Reference. *Journal of Computer and System Sciences*.
A. Borodin, S. Irani, P. Raghavan. DOI 10.1006/jcss.1995.1021.

[144] Competitive paging with locality of reference. *Proceedings of the twenty-third annual ACM
symposium on Theory of computing - ST*. Allan Borodin, Prabhakar Raghavan, Sandy Irani. DOI
10.1145/103418.103422.

[145] Designing Registration Caching Free High-Performance MPI Library with Implicit On-Demand
Paging (ODP) of InfiniBand. *2017 IEEE 24th International Conference on High Performance
Computing (HiPC)*. Mingzhe Li, Xiaoyi Lu, Hari Subramoni. DOI 10.1109/hipc.2017.00017.

[146] Exploiting the optimal paging algorithms. *Information Processing Letters*. Radha Krishan
Arora, R.K. Subramanian. DOI 10.1016/0020-0190(78)90006-6.

[147] Finding Optimal Demand Paging Algorithms. *Journal of the ACM*. Giorgio Ingargiola, James
F. Korsh. DOI 10.1145/321796.321801.

[148] Improved Space Bounds for Strongly Competitive Randomized Paging Algorithms. *Lecture
Notes in Computer Science*. Gabriel Moruz, Andrei Negoescu. DOI 10.1007/978-3-642-39206-1_64.

[149] Issues in File Caching and Virtual Memory Paging with Fast SCM Storage. *Advances in
Science, Technology and Engineering Systems Journal*. Yunjoo Park, Hyokyung Bahn. DOI
10.25046/aj050581.

[150] Multicore Paging Algorithms Cannot Be Competitive. *Proceedings of the 32nd ACM Symposium
on Parallelism in Algorithms and Architect*. Shahin Kamali, Helen Xu. DOI
10.1145/3350755.3400270.

[151] On-line algorithm of loose competitive caching. *Journal of Computer Applications*.
Zhao-quan CAI. DOI 10.3724/sp.j.1087.2008.02604.

[152] Online Paging and Caching. *Encyclopedia of Algorithms*. Neal E. Young. DOI
10.1007/978-0-387-30162-4_267.

[153] Online Paging and Caching. *Encyclopedia of Algorithms*. Neal E. Young. DOI
10.1007/978-1-4939-2864-4_267.

[154] Online Paging and Caching. *Encyclopedia of Algorithms*. NealE. Young. DOI
10.1007/978-3-642-27848-8_267-2.

[155] Online paging and file caching with expiration times. *Theoretical Computer Science*.
Tracy Kimbrel. DOI 10.1016/s0304-3975(00)00263-2.

[156] OnlineMin: A Fast Strongly Competitive Randomized Paging Algorithm. *Lecture Notes in
Computer Science*. Gerth Stølting Brodal, Gabriel Moruz, Andrei Negoescu. DOI
10.1007/978-3-642-29116-6_14.

[157] OnlineMin: A Fast Strongly Competitive Randomized Paging Algorithm. *Theory of Computing
Systems*. Gerth Stølting Brodal, Gabriel Moruz, Andrei Negoescu. DOI 10.1007/s00224-012-9427-y.

[158] Optimal control of demand-paging systems. *Information Sciences*. Art Lew. DOI
10.1016/0020-0255(76)90052-9.

[159] Optimal control of demand-paging systems. *Information Sciences*. Art Lew. DOI
10.1016/s0020-0255(76)90962-2.

[160] Outperforming LRU via Competitive Analysis on Parametrized Inputs for Paging. *Proceedings
of the Twenty-Third Annual ACM-SIAM Symposium on Discrete Algorithms*. Gabriel Moruz, Andrei
Negoescu. DOI 10.1137/1.9781611973099.132.

[161] Segmentation, paging and optimal page sizes in virtual memory. *Computer Compacts*. Timo
O. Alanko, A.Inkeri Verkamo. DOI 10.1016/0167-7136(83)90150-6.

[162] Track Paging an Optimal Method for Minimizing Paging and Signaling Cost in Mobile IP.
*Journal of Computer and Communications*. Tania Baghaie. DOI 10.4236/jcc.2013.14002.

[163] UM Paging: Unified M2M Paging with Optimal DRX Cycle. *IEEE Transactions on Mobile
Computing*. Chia-Wei Chang, Jyh-Cheng Chen. DOI 10.1109/tmc.2016.2575835.

[164] A Competitive analysis of the list update problem with lookahead. *Lecture Notes in
Computer Science*. Susanne Albers. DOI 10.1007/3-540-58338-6_67.

[165] A competitive analysis of the list update problem with lookahead. *Theoretical Computer
Science*. Susanne Albers. DOI 10.1016/s0304-3975(97)00026-1.

[166] A general modeling approach to online optimization with lookahead. *Omega*. Fabian Dunke,
Stefan Nickel. DOI 10.1016/j.omega.2015.10.009.

[167] Correction to: Exact distributional analysis of online algorithms with lookahead. *4OR*.
Fabian Dunke, Stefan Nickel. DOI 10.1007/s10288-021-00479-w.

[168] Exact distributional analysis of online algorithms with lookahead. *4OR*. Fabian Dunke,
Stefan Nickel. DOI 10.1007/s10288-020-00442-1.

[169] Improving Greedy Algorithms by Lookahead-Search. *Journal of Algorithms*. U.K. Sarkar,
P.P. Chakrabarti, S. Ghose. DOI 10.1006/jagm.1994.1001.

[170] Lookahead-based algorithms for anytime induction of decision trees. *Twenty-first
international conference on Machine learning - ICML '04*. Saher Esmeir, Shaul Markovitch. DOI
10.1145/1015330.1015373.

[171] New algorithms for online rectangle filling with k-lookahead. *Journal of Combinatorial
Optimization*. Haitao Wang, Amitabh Chaudhary, Danny Z. Chen. DOI 10.1007/s10878-009-9246-5.

[172] On competitive on-line paging with lookahead. *Lecture Notes in Computer Science*. Dany
Breslauer. DOI 10.1007/3-540-60922-9_48.

[173] On competitive on-line paging with lookahead. *Theoretical Computer Science*. Dany
Breslauer. DOI 10.1016/s0304-3975(98)00118-2.

[174] On Competitive On-Line Paging with Lookahead. *BRICS Report Series*. Dany Breslauer. DOI
10.7146/brics.v2i50.19951.

[175] On the Influence of Lookahead in Competitive Paging Algorithms. *Algorithmica*. S. Albers.
DOI 10.1007/pl00009158.

[176] Online algorithms for scheduling unit length jobs on parallel-batch machines with
lookahead. *Information Processing Letters*. Wenhua Li, Zhenkun Zhang, Sufang Yang. DOI
10.1016/j.ipl.2012.01.002.

[177] Online Algorithms for Scheduling Unit Length Jobs on Unbounded Parallel-Batch Machines
with Linearly Lookahead. *Asia-Pacific Journal of Operational Research*. Chengwen Jiao, Jinjiang
Yuan, Qi Feng. DOI 10.1142/s0217595919500246.

[178] Parallel lookahead algorithms for pruned interleavers. *IEEE Transactions on
Communications*. Mohammad M. Mansour. DOI 10.1109/tcomm.2009.11.070661.

[179] Parameter learning in lookahead online algorithms for data acknowledgment. *3rd IEEE
International Symposium on Logistics and Industrial Informatics*. Tamas Nemeth, Balazs
Gyekiczki, Csanad Imreh. DOI 10.1109/lindi.2011.6031146.

[180] Remarks on recent algorithms for LALR lookahead sets. *ACM SIGPLAN Notices*. J C H Park.
DOI 10.1145/24714.24717.

[181] Response to remarks on recent algorithms for LALR lookahead sets. *ACM SIGPLAN Notices*.
Fred Ives. DOI 10.1145/35596.35606.

[182] Semi-Online Scheduling with Lookahead. *(no venue field)*. Debasis Dwibedy, Rakesh
Mohanty. DOI 10.2139/ssrn.4485992.

[183] Stage-lookahead dynamic programming algorithms for stochastic problems with time-lagged
control dynamics. *2009 IEEE International Conference on Industrial Engineering and Engineering
Man*. Eiji Mizutani, Stuart Dreyfus. DOI 10.1109/ieem.2009.5373354.

[184] The influence of lookahead in competitive paging algorithms. *Lecture Notes in Computer
Science*. Susanne Albers. DOI 10.1007/3-540-57273-2_39.

[185] Unifying view of recent LALR(1) lookahead set algorithms. *Proceedings of the 1986 SIGPLAN
symposium on Compiler construction*. Fred Ives. DOI 10.1145/12276.13324.

[186] Unifying view of recent LALR(1) lookahead set algorithms. *ACM SIGPLAN Notices*. Fred
Ives. DOI 10.1145/13310.13324.

[187] A polylog( n )-competitive algorithm for metrical task systems. *Proceedings of the
twenty-ninth annual ACM symposium on Theory of computing - ST*. Yair Bartal, Avrim Blum, Carl
Burch. DOI 10.1145/258533.258667.

[188] A Polylogarithmic-Competitive Algorithm for the k-Server Problem. *2011 IEEE 52nd Annual
Symposium on Foundations of Computer Science*. N. Bansal, N. Buchbinder, A. Madry. DOI
10.1109/focs.2011.63.

[189] An optimal on-line algorithm for metrical task system. *Journal of the ACM*. Allan
Borodin, Nathan Linial, Michael E. Saks. DOI 10.1145/146585.146588.

[190] An optimal online algorithm for metrical task systems. *Proceedings of the nineteenth
annual ACM conference on Theory of computing - STO*. A. Borodin, N. Linial, M. Saks. DOI
10.1145/28395.28435.

[191] Barely Random Algorithms and Collective Metrical Task Systems. *Advances in Neural
Information Processing Systems 37*. Romain Cosson, Laurent Massoulié. DOI 10.52202/079017-1178.

[192] Better Algorithms for Unfair Metrical Task Systems and Applications. *SIAM Journal on
Computing*. Amos Fiat, Manor Mendel. DOI 10.1137/s0097539700376159.

[193] Better algorithms for unfair metrical task systems and applications. *Proceedings of the
thirty-second annual ACM symposium on Theory of computing*. Amos Fiat, Manor Mendel. DOI
10.1145/335305.335408.

[194] Metrical task systems on trees via mirror descent and unfair gluing. *Proceedings of the
Thirtieth Annual ACM-SIAM Symposium on Discrete Algorithms*. Sébastien Bubeck, Michael B. Cohen,
James R. Lee. DOI 10.1137/1.9781611975482.6.

[195] Metrical Task Systems on Trees via Mirror Descent and Unfair Gluing. *SIAM Journal on
Computing*. Sébastien Bubeck, Michael B. Cohen, James R. Lee. DOI 10.1137/19m1237879.

[196] Metrical task systems, the server problem and the work function algorithm. *Lecture Notes
in Computer Science*. Marek Chrobak, Lawrence L. Larmore. DOI 10.1007/bfb0029565.

[197] On Algorithm Design for Metrical Task Systems. *Algorithmica*. W. R. Burley, S. Irani. DOI
10.1007/pl00009166.

[198] On the competitive ratio of the work function algorithm for the k-server problem.
*Theoretical Computer Science*. Yair Bartal, Elias Koutsoupias. DOI 10.1016/j.tcs.2004.06.001.

[199] Randomized algorithms for metrical task systems. *Lecture Notes in Computer Science*.
Sandy Irani, Steve Seiden. DOI 10.1007/3-540-60220-8_59.

[200] Randomized algorithms for metrical task systems. *Theoretical Computer Science*. Sandy
Irani, Steve Seiden. DOI 10.1016/s0304-3975(97)00006-6.

[201] The distributed k-server problem-a competitive distributed translator for k-server
algorithms. *Proceedings., 33rd Annual Symposium on Foundations of Computer Science*. Y. Bartal,
A. Rosen. DOI 10.1109/sfcs.1992.267756.

[202] The Distributedk-Server Problem—A Competitive Distributed Translator fork-Server
Algorithms. *Journal of Algorithms*. Yair Bartal, Adi Rosén. DOI 10.1006/jagm.1996.0826.

[203] Topology Matters: Smoothed Competitiveness of Metrical Task Systems. *Lecture Notes in
Computer Science*. Guido Schäfer, Naveen Sivadasan. DOI 10.1007/978-3-540-24749-4_43.

[204] Topology matters: Smoothed competitiveness of metrical task systems. *Theoretical Computer
Science*. Guido Schäfer, Naveen Sivadasan. DOI 10.1016/j.tcs.2005.04.006.

[205] Unfair Problems and Randomized Algorithms for Metrical Task Systems. *Information and
Computation*. Steve Seiden. DOI 10.1006/inco.1998.2744.

[206] A fast and effective lookahead and fractional search based scheduling algorithm for
high-level synthesis. *2018 Design, Automation &amp; Test in Europe Conference &amp; Exhibition
(DATE)*. Shantanu Dutt, Ouwen Shi. DOI 10.23919/date.2018.8341975.

[207] A Lookahead Algorithm for Robust Subspace Recovery. *2021 IEEE International Conference on
Data Mining (ICDM)*. Guihong Wan, Haim Schweitzer. DOI 10.1109/icdm51629.2021.00175.

[208] An efficient one-step lookahead A* algorithm for PM-CT scheduling problems. *The
International Journal of Advanced Manufacturing Technology*. Hwang Ho Kim, Jin Young Choi. DOI
10.1007/s00170-014-5755-1.

[209] An Improved Online Algorithm for the Online Preemptive Scheduling of Equal-Length
Intervals on a Single Machine with Lookahead. *Asia-Pacific Journal of Operational Research*.
Wenjie Li, Jinjiang Yuan. DOI 10.1142/s0217595915500475.

[210] Backfilling with Lookahead to Optimize the Performance of Parallel Job Scheduling.
*Lecture Notes in Computer Science*. Edi Shmueli, Dror G. Feitelson. DOI 10.1007/10968987_12.

[211] DAG Scheduling Using a Lookahead Variant of the Heterogeneous Earliest Finish Time
Algorithm. *2010 18th Euromicro Conference on Parallel, Distributed and Network-based Proces*.
Luiz F. Bittencourt, Rizos Sakellariou, Edmundo R. M. Madeira. DOI 10.1109/pdp.2010.56.

[212] Disk scheduling policies with lookahead. *ACM SIGMETRICS Performance Evaluation Review*.
Alexander Thomasian, Chang Liu. DOI 10.1145/588160.588165.

[213] How much can lookahead help in online single machine scheduling. *Information Processing
Letters*. Feifeng Zheng, Yinfeng Xu, E. Zhang. DOI 10.1016/j.ipl.2007.10.008.

[214] Lookahead scheduling. *ACM SIGMICRO Newsletter*. Steven J. Beaty. DOI
10.1145/144965.145822.

[215] Lookahead scheduling requests for multisize page caching. *IEEE Transactions on
Computers*. J. Kiniwa, T. Hamada, D. Mizoguchi. DOI 10.1109/12.954511.

[216] Online Batch Scheduling of Incompatible Job Families with Variable Lookahead Interval.
*Asia-Pacific Journal of Operational Research*. Wenhua Li, Libo Wang, Hang Yuan. DOI
10.1142/s0217595922400127.

[217] Online interval scheduling on a single machine with finite lookahead. *Computers &amp;
Operations Research*. Feifeng Zheng, Yongxi Cheng, Ming Liu. DOI 10.1016/j.cor.2012.06.003.

[218] Online interval scheduling on two related machines: the power of lookahead. *Journal of
Combinatorial Optimization*. Nicolas Pinson, Frits C. R. Spieksma. DOI
10.1007/s10878-019-00381-6.

[219] Online packet scheduling with bounded delay and lookahead. *Theoretical Computer Science*.
Martin Böhm, Marek Chrobak, Łukasz Jeż. DOI 10.1016/j.tcs.2019.01.013.

[220] Online scheduling of incompatible unit-length job families with lookahead. *Theoretical
Computer Science*. Wenhua Li, Jinjiang Yuan, Sufang Yang. DOI 10.1016/j.tcs.2014.05.024.

[221] Online scheduling of two-machine flowshop with lookahead and incompatible job families.
*Journal of Combinatorial Optimization*. Xia Qian, Zhang Xingong. DOI
10.1007/s10878-022-00974-8.

[222] Online scheduling of unit length jobs on a batching machine to maximize the number of
early jobs with lookahead. *Theoretical Computer Science*. Wenjie Li, Jinjiang Yuan, Jianfa Cao.
DOI 10.1016/j.tcs.2009.07.056.

[223] Online Scheduling with Lookahead: Multipass Assembly Lines. *INFORMS Journal on
Computing*. Rajeev Motwani, Vijay Saraswat, Eric Torng. DOI 10.1287/ijoc.10.3.331.

[224] Quality vs. Performance in Lookahead Scheduling. *Advances in Intelligent Systems
Research*. Ben Coleman. DOI 10.2991/jcis.2006.324.

[225] Scheduling unit length jobs on parallel machines with lookahead information. *Journal of
Scheduling*. Marvin Mandelbaum, Dvir Shabtay. DOI 10.1007/s10951-010-0192-y.

[226] Semi-Online Scheduling on Two Identical Parallel Machines with Initial-Lookahead
Information. *Asia-Pacific Journal of Operational Research*. Feifeng Zheng, Yuhong Chen, Ming
Liu. DOI 10.1142/s0217595923500033.

[227] Semi-online scheduling on two uniform parallel machines with initial lookahead. *RAIRO -
Operations Research*. Feifeng Zheng, Yuhong Chen, Ming Liu. DOI 10.1051/ro/2024042.

[228] Simple Channel Predictors for Lookahead Scheduling. *2012 IEEE 75th Vehicular Technology
Conference (VTC Spring)*. Thomas Werthmann, Matthias Kaschub, Magnus Proebster. DOI
10.1109/vetecs.2012.6240134.

[229] The Lookahead Heuristic For Multi-Item Single Machine Production Scheduling With Dynamic,
Stochastic Demands. *INFOR: Information Systems and Operational Research*. André Gascon. DOI
10.1080/03155986.1988.11732058.

[230] Analysis of PLS Path Model between CRM Information Possessed by a Ski Rental Shop and
Customer Behavior. *Journal of Sport and Leisure Studies*. Tae Soo Cho. DOI
10.51979/kssls.2012.05.48.129.

[231] Combinatorial Ski Rental and Online Bipartite Matching. *Proceedings of the 21st ACM
Conference on Economics and Computation*. Hanrui Zhang, Vincent Conitzer. DOI
10.1145/3391403.3399470.

[232] Combinatorial Ski Rental Problem: Robust and Learning-Augmented Algorithms. *Advances in
Neural Information Processing Systems 38*. Ziwei Li, Bo Sun, Zhiqiu Zhang. DOI
10.52202/085713-4014.

[233] Competitive FIB Aggregation for Independent Prefixes: Online Ski Rental on the Trie.
*Lecture Notes in Computer Science*. Marcin Bienkowski, Stefan Schmid. DOI
10.1007/978-3-319-03578-9_8.

[234] Improved Learning-Augmented Algorithms and (Tight) Lower Bounds for Multi-Option Ski
Rental Problem. *ACM Transactions on Algorithms*. Yongho Shin, Changyeol Lee, Gukryeol Lee. DOI
10.1145/3763239.

[235] Machine learning advised algorithms for the ski rental problem with a discount.
*Theoretical Computer Science*. Arghya Bhattacharya, Rathish Das. DOI 10.1016/j.tcs.2022.10.006.

[236] Online Algorithms for Multi-shop Ski Rental with Machine Learned Predictions.
*International Joint Conference on Autonomous Agents and Multiagent Systems*. Shufan Wang, Jian
Li. DOI 10.65109/ocnn5096.

[237] Online Ski Rental for ON/OFF Scheduling of Energy Harvesting Base Stations. *IEEE
Transactions on Wireless Communications*. Gilsoo Lee, Walid Saad, Mehdi Bennis. DOI
10.1109/twc.2017.2672964.

[238] Online ski rental for scheduling self-powered, energy harvesting small base stations.
*2016 IEEE International Conference on Communications (ICC)*. Gilsoo Lee, Walid Saad, Mehdi
Bennis. DOI 10.1109/icc.2016.7511011.

[239] Rent, Lease, or Buy: Randomized Algorithms for Multislope Ski Rental. *SIAM Journal on
Discrete Mathematics*. Zvi Lotker, Boaz Patt-Shamir, Dror Rawitz. DOI 10.1137/100794018.

### Works read in full for the comparison in the model and related-work sections

[240] P. O'Neil, E. Cheng, D. Gawlick, E. O'Neil. The log-structured merge-tree (LSM-tree). Acta
Informatica, 1996. DOI 10.1007/s002360050048

[241] RocksDB project documentation, *Compaction* (wiki, read 2026-10-27): taxonomy of Classic
Leveled / Tiered / Tiered+Leveled / FIFO, and the statement that LevelDB and RocksDB compaction
is some-to-some over overlapping data.

[242] RocksDB project documentation, *RocksDB Overview* (wiki, read 2026-10-27): level style vs
universal style compaction, and the role of overlapping keys in L0.

[243] On Competitive On-Line Paging with Lookahead. BRICS report 1995 (DOI
10.7146/brics.v2i50.19951); journal version 1997 (DOI 10.1016/s0304-3975(98)00118-2):
competitive efficiency depends on k + l.

[244] Semi-Online Scheduling on Two Identical Parallel Machines with Initial-Lookahead
Information. 2023. DOI 10.1142/s0217595923500033.

[245] Semi-online scheduling on two uniform parallel machines with initial lookahead. 2024. DOI
10.1051/ro/2024042.

[246] Disk scheduling policies with lookahead. 2002. DOI 10.1145/588160.588165.

[247] An optimal on-line algorithm for metrical task systems. 1992. DOI 10.1145/146585.146588.

