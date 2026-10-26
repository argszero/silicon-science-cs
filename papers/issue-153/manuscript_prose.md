# When the Largest Overlap Is the Most Expensive Merge

### An exact characterisation of a local compaction heuristic, and the lookahead it would need

---

## Abstract

Log-structured storage engines decide *which* sorted runs to merge with a local rule: take the
ranges that currently overlap, and merge the one overlapping most. This paper asks a narrow,
answerable question about that rule. On a model with `K` capacity slots and `R` key
ranges, run sizes frozen at creation, we enumerate **every** trace of up to
{{n:model.Tmax}} flushes across {{n:n_cells}} cells ({{n:n_traces_total}} traces, {{n:n_states_total}} reachable visible
states, no sampling) and score the rule against an exact dynamic program that is itself
certified against an independent brute-force traversal on {{n:certificate.instances}}
instances.

Four measured results. **(i)** The rule is not making a trade-off: on all
{{n:decisions.decisions}} merge decisions of the base cell its fan-in equals the widest legal
alternative (gap {{n:decisions.fanin_gap_max}} on every decision), while the bytes it pays are
never below the cheapest legal merge. "Largest overlap" and "most runs collapsed" are the same
choice, and it is the most expensive one. **(ii)** It is wrong often and sometimes badly: the
non-optimal fraction ranges from {{n:range.loss_min_pct}}% to {{n:range.loss_max_pct}}% depending
on capacity and trace length, and the worst excess is **{{n:max_worst}}×**, at R=3 K=5 T=6. **(iii)** Exactness requires a horizon
that grows with the trace — `w* = T − 1 − i_first`, where `i_first` is the first flush at which
more than one legal merge exists — and a lookahead of one is *worse than none*
({{n:lookahead.w1_loss}} losing traces against {{n:lookahead.w0_loss}}). **(iv)** No function of
the visible state is exact whenever that horizon is positive: at R=3 K=3 T=6 the intersection
of optimal choices over all continuations reaching a state is empty at {{n:proposition.refuting}}
of {{n:proposition.states}} states, and we print a two-trace witness that can be checked by hand.

The horizon claim is a **proposition of this model**, with its scope stated: the model is not a
deployment, no production trace is replayed, and the modelled rule is a named member of the
compaction family, not a reimplementation of any engine. Contribution level: **`theory+empirics`**
— a formal model with exhaustively verified results, and no claim about production systems.

## 1. Introduction

A log-structured merge tree defers and batches writes: flushes append sorted runs, and a
*compaction* merges runs so the run count stays bounded. The cost of that choice is write
amplification — the bytes rewritten by merges rather than written once. The choice is made
online, by a local rule, under a capacity bound, and it recurs on every flush. That is
precisely the shape of an online problem with an offline optimum, which is why this paper
positions the question in the vocabulary of competitive analysis rather than of engine tuning.

The question this paper answers is not "can compaction be made cheaper". It is: **how much of
the future would an exact rule at this decision point have to see, and does any rule reading
only what is visible make the right choice?** Those are two different questions, and this paper
gives a measured answer to each, plus the control that says whether the answer is about the
world or about our instrument.

Our contributions:

1. A model of the decision — {{n:model.K}} slots, {{n:model.R}} ranges, runs whose size is
   frozen when created, merges that pay the bytes they cover — and a named local rule inside
   it, with an explicit statement of how it corresponds to deployed leveled compaction and what
   it drops (§2).
2. An exhaustive method with an independent certificate: the dynamic program used as the
   optimum is checked against a separately written brute-force traversal on
   {{n:certificate.instances}} instances, all agreeing (§3).
3. Measured facts about the rule: it is not a trade-off (§4.1), how often and how badly it is
   wrong across {{n:n_cells}} cells (§4.2), the horizon exactness needs and the non-monotonicity
   of lookahead (§4.3), and that no visible-state function is exact when that horizon is
   positive (§4.4), with a positive control in both directions (§4.5).
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

The model is deliberately small. Its virtue is that every trace can be enumerated, which is
what makes the claims exact rather than sampled.

### 2.2 The rule we study, and its correspondence to deployed engines

The rule, which we call **largest-overlap-first**, is: among the ranges for which a merge is
legal, merge the one whose covering runs hold the most live bytes; break ties toward the lowest
range index. It reads only the visible state — the runs with their sizes, the live bytes per
range, and the incoming flush.

This is a *named local heuristic*, and we state its correspondence to practice precisely rather
than claiming identity. In leveled compaction as deployed, a compaction merges a file from level
`Ln` with the files it *overlaps* in `Ln+1`: RocksDB's own compaction documentation describes
this as "some-to-some" — "some data from `Ln-1` is merged with some (the overlapping) data in
`Ln`" {{cite:rocksdb_compaction}} — where classic leveled compaction from the LSM-tree paper is
all-to-all for adjacent levels {{cite:oneil1996}}. So overlap determines *which* runs are
combined, exactly as in our rule, and the bytes rewritten by that combination are the cost the
engine pays, again as in our rule.

What the model drops, stated plainly: RocksDB chooses *which level* to compact by a compaction
score, not by largest overlap, and applies rate limits and background-job scheduling; real
engines have tombstones and deletions (so a merge can *reduce* live bytes), partial key-range
overlap rather than whole-range overlap, level size targets with a fanout ratio, and both tiered
and tiered+leveled layouts rather than one shape {{cite:rocksdb_overview}}. Our model has none
of them. Section 5 states what follows from that, and §2.3 states what does not.

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

Everything is exhaustive. For a cell `(R, K, T)` we enumerate all `R^T` traces: across the
{{n:n_cells}} cells of §4.2 that is {{n:n_traces_total}} traces, with no sampling and no
random seeds, so the reported fractions are exact counts, not estimates with error bars.

The optimum is computed by dynamic programming over `(flush index, run multiset, live bytes)`.
Because a DP can be wrong in a way that flatters the rule under study, it is **certified**: a
separately written brute-force traversal enumerates the same instances and must agree. It does,
on all {{n:certificate.instances}} instances. The certificate earned its keep immediately: its
first run disagreed on every instance, because the brute force charged a run the bytes live
*later* rather than the bytes it held when created. That defect was in the brute force, but the
same rule governs the DP, which is why the model states frozen-at-creation sizes explicitly
(§2.1).

Three controls run throughout, and we report them wherever a rate is reported:

- **The anti-rule.** A cheapest-overlap rule — merge the legal range paying the fewest bytes —
  runs in every cell. If the deployed rule's failures were an artefact of the model rather than
  of its locality, this rule would fail in the same places.
- **The no-choice control.** At `K = 2` the legal merge set is a singleton: no rule has any
  freedom, so every rule ties. These cells are reported as a control, never as evidence.
- **The positive control.** In the cells where the horizon is zero we exhibit a rule that is
  *exact*, and in a refuting cell we show that no such rule exists (§4.5). A negative result
  without a positive counterpart cannot distinguish "no rule can do it" from "we did not find
  one".

## 4. Results

### 4.1 The rule is not a trade-off

Across the base cell's decisions, the fan-in of the rule's chosen merge equals the maximum
fan-in among legal alternatives on **every** decision: the gap is
{{n:decisions.fanin_gap_max}} over {{n:decisions.decisions}} decisions. And the price it pays is
never below the cheapest legal merge (minimum gap {{n:decisions.paid_gap_min}}). So on this
model the two natural readings of "largest overlap" — merge the most-overlapping range, and
collapse the most runs — denote the same choice, and that choice is also the most expensive one
available. Of those {{n:decisions.decisions}} decisions,
{{n:decisions.suboptimal}} are non-optimal.

This is the paper's title as a measurement rather than a slogan: the largest overlap is the most
expensive merge, and choosing it is not buying anything with the expense.

### 4.2 How often the rule is wrong, and by how much

{{table:cells}}

Two readings matter. First, the failure fraction is stable across trace length in a fixed
`(R, K)` family — it does not wash out as traces grow, so this is not a small-trace artefact of
boundary effects. Second, the *magnitude* is worse than the fraction suggests: the worst excess
is {{n:max_worst}}× at R=3 K=5 T=6, and that cell is not the base cell but a cell with more
capacity, where the rule loses {{n:detail.k5t6_loss}} of {{n:detail.k5t6_traces}} traces.

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
of one loses {{n:lookahead.w1_loss}} traces, against {{n:lookahead.w0_loss}} for the
zero-lookahead cheapest-overlap rule and {{n:lookahead.deployed_loss}} for the deployed rule. A
practitioner's instinct — "look one step ahead" — makes it worse. The mechanism is that a
one-step lookahead optimises the immediate merge cost against a single future flush, which is
exactly enough information to be systematically wrong about which range is hot.

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

This is immediate from the definition — a visible-state rule picks one candidate at `S`
whatever the continuation, and that candidate is outside `argmin(S, τ)` for some `τ`. We state
it because it organises the measurement, not because it is deep. What is *not* an identity is
the measurement: at R=3 K=3 T=6, `Opt(S)` is empty at {{n:proposition.refuting}} of
{{n:proposition.states}} reachable states, and across the cells of §4.2 the count of refuting
states is {{n:n_refuting_total}}.

The witness can be checked without running anything. At flush 3, with runs `[(1,1), (1,2),
(2,1), (2,2)]`, live bytes `[2,2,0]` and next flush in range 0, the legal merges are ranges 0
and 1. Suffix `010` makes range 0 the unique optimal merge; suffix `000` makes range 1 the
unique optimal merge. Both suffixes reach that state, so `Opt(S) = ∅`: any rule reading only the
state is wrong on one of them. Note the state includes live bytes and the incoming flush — more
than the deployed rule reads — so the refutation is only strengthened for narrower information
sets.

### 4.5 The controls

{{table:controls}}

In the cell with `w* = 0` — R=3 K=5 T=6, where no choice ever exists early enough to need the
future — the rule `min Opt(S)` (merge toward the smallest choice that is optimal for *every*
continuation) loses {{n:control.exact_loss}} of {{n:control.exact_traces}} traces: an exact
visible-state rule **exists** there. In the refuting cell R=3 K=3 T=6 the same rule loses
{{n:control.refuting_loss}}, as it must, because no visible-state rule can do better. Both
directions are asserted in the committed program, so the pair distinguishes "no rule can" from
"we did not find one".

The anti-rule control is reported per cell in the table of §4.2. Among the cells where a genuine
choice exists, cheapest-overlap loses **fewer** traces than largest-overlap in
{{n:anti.wins}} of {{n:anti.choice_cells}} and **more** in {{n:anti.loses}}, at R=3 K=4 T=6,
R=4 K=4 T=6 and R=3 K=5 T=7. The exception is reported rather than smoothed: the two simple
rules are not ordered by locality alone, and we do not know of a general statement that orders
them.

## 5. Scope and threats

**The model is not a deployment.** No production trace is replayed; flushes are enumerated
sequences over a small range alphabet, not workload-driven. Run sizes are frozen by fiat.
Tombstones, deletions, partial key-range overlap, level size targets, compaction scores, rate
limits and background scheduling are all absent (§2.2). No number here should be read as a
measurement of any engine.

**The claims are exact but bounded.** Every fraction in §4 is an exact count over an enumerated
set, which removes sampling error and replaces it with a different limitation: the cells are
small, and the choice of cells is ours. The horizon formula is verified in cells up to
{{n:model.Rmax}} ranges, {{n:model.Kmax}} slots and {{n:model.Tmax}} flushes; we do not claim it
beyond that, and the one place where a natural generalisation failed — asserting the formula to
`K = 2`, where it is false — is recorded in §8.

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
extra bit of the future {{cite:paging_lookahead}}. Our result fails *in form* rather than in
constant: foresight here is not tradeable against capacity, because `w*` grows with the trace,
so no constant `l` is exact for any `K`, and raising `l` by one can make the rule worse (§4.3).

Semi-online scheduling with initial lookahead is the second nearest, and the one a reviewer
should raise against us, because it also reports that lookahead can be worthless: for one
regime of two-machine makespan, any online algorithm has ratio at least 3/2, matching what is
achievable without the information {{cite:semi_online_two}}. The difference is the object
quantified: that line gives competitive ratios per regime for a known prefix of the input,
whereas we give the horizon at which optimality becomes possible at all. "Lookahead is
powerless" and "lookahead must be total" are different statements — one about a ratio, one about
existence — and only the second is claimed here.

Two further works bound the value of finite lookahead positively: semi-online scheduling on
uniform machines where finite initial lookahead "can greatly improve" competitiveness
{{cite:semi_online_uniform}}, and disk-scheduling policies with a lookahead window evaluated
empirically {{cite:disk_sched}}. Our horizon result is the opposite shape for a different
decision, and the disagreement on monotonicity is the substantive difference we would want a
reviewer to press on. The metrical-task-system framework supplies the general setting in which a
rule is scored against an offline optimum {{cite:mts_optimal}}, and it is cited for that
setting, not for the question.

**Not cited as comparison.** We read no abstract for *How much can lookahead help in online
single machine scheduling* (2008), and we therefore state no difference from it; a title-level
difference is not evidence.

## 7. Further related work

The corpus below was assembled from Crossref with a stated search form and is reproduced in
`reference-check.md`, which records for each entry the DOI-verified record returned by the
register. Placement required a record to name a construct its section uses; entries that named
adjacent constructs (wireless caching placement, instruction scheduling) were excluded with
their reason.

*Compaction and write amplification.* {{cites:2:lsm-compaction}} {{cites:2:flash-write-amp}}

*Leveled and tiered layouts, and the engines that carry them.* {{cites:2:levels-tiering}}
{{cites:2:kv-engine}}

*Log-structured file systems, where cleaning is the ancestor of compaction.*
{{cites:2:logstructured-fs}}

*Paging and caching, where the offline optimum is classical.* {{cites:7:competitive-paging}}

*Lookahead in online algorithms.* {{cites:7:lookahead-online}} {{cites:7:sched-lookahead}}

*Metrical task systems and k-server.* {{cites:7:mts-kserver}}

*Ski rental and other minimal online decisions.* {{cites:7:ski-rental}}

## 8. Prior beliefs, and what happened to them

Two priors were registered before the study.

**P1 — optimality at `K = 2` is structural, not empirical.** Predicted: the deployed rule is
optimal on 100% of `K = 2` traces, and this cannot be evidence about the rule, because a legal
merge must cover at least two runs, so at capacity 2 the merge set is forced. **Confirmed**, and
strengthened: in every `K = 2` cell the anti-rule also loses nothing, which is the observation
that makes the row a control rather than a result. The mechanism predicted is the mechanism
measured.

**P2 — the excess is born at `K = 3` and does not vanish.** Predicted: a non-zero non-optimal
fraction at `K = 3` with worst excess strictly above {{n:priors.p2_threshold}}×. **Confirmed in direction, revised in
magnitude.** The fraction is measured (§4.2) and the worst excess is {{n:max_worst}}×, not the
1.667× recorded at registration, which was the maximum within a single cell and not across
cells. The correction is posted visibly on the issue rather than edited into the registration.

**A third claim was registered and is withdrawn.** The registration proposed that the traces
defeating the rule "admit a predicate computable from the trace alone". They do not: a derived
predicate was sound — it never fired on an optimal instance — but it covered only a minority of
the failures on one half of the instances and about half on the other, so it described the
failures it caught rather than characterising them. We withdrew it in favour of the
non-existence result of §4.4. The counts are recorded on the issue thread, not quoted here,
because the draft that produced them was discarded and we cannot re-derive them from a committed
program: a figure this paper cannot regenerate does not belong in it. We also corrected the horizon formula from `T − K − 1` to `T − 1 − i_first` after the
adversarial cells of §4.3 falsified the former at `K = 2`.

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

{{refs}}
