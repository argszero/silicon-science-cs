# The Queue Count Is Not the Fidelity: An Exact Rank-Inversion Floor for PIFO Emulation, and the Traffic Statistic That Sets It

## Abstract

Programmable packet schedulers emulate a push-in-first-out (PIFO) queue with a small bank of
strict-priority queues, and the size that bank needs is usually answered with the longest
decreasing subsequence (LDS) of the arrival order — the statistic behind Dilworth's
chain-decomposition theorem. This paper shows that statistic answers a different question from the
one a device asks. Under a strict-priority dequeue the exact requirement is `runs(p)`, the number
of maximal ascending runs of the inverse arrival order; we verify `required k = runs(p)`
exhaustively over all {{n:total_distinct_windows}} distinct-rank arrival orders at n = 4…7 with
{{n:threshold_distinct[7].runs_p_violations}} violations, and prove `runs(p) >= LDS`. The
inequality is what makes the error one-directional: LDS cannot overstate what a device needs, so it
is *short* — on {{p:threshold_distinct[7].lds_understates_fraction}} % of n = 7 windows, by at most
{{n:gap_summary.distinct_max_gap}} queues in the measured range. Ties move both numbers at once. The
statistic survives them only when it is minimised over tie-breakings
({{n:threshold_ties_totals.T3}} violations over {{n:threshold_ties_totals.windows}} tie-bearing
windows), while the *frequency* of the discipline gap collapses: once ranks repeat, the two
disciplines require the same queue count on {{n:agree_ties_pct}} % of windows, against
{{n:agree_distinct_n7_pct}} % at n = 7 with distinct ranks.

**Prior-art position, stated first because it bounds the novelty.** The statistic
`runs(p) = 1 + #{descents}` is *classical* permutation-sorting machinery. Even and Itai
{{cite:evenitai1971}} treated queues, stacks and graphs as sorting devices; Tarjan {{cite:tarjan1972}}
gave sorting using networks of queues and stacks; and Pratt {{cite:pratt1973}} computed which
permutations double-ended queues, parallel stacks and parallel queues produce — which is, almost
literally, this paper's question. We verified all three records **by DOI** against Crossref and
**did not read them**: every publisher landing page and bronze-OA PDF for them returned `HTTP 403`
to this environment, and we did not attempt to reach them by another route. This paper therefore
*attributes* the problem and the machinery to those works and asserts nothing about their
statements. If a reader who can open them finds that one already states a result of ours, the result
is theirs, and ours is a re-derivation in a scheduler's setting.

What is left, and what this paper claims, is a **system-level pairing**: the number of queues a
scheduler needs is a function of the traffic *and* of the dequeue discipline. The discipline the
literature treats as default — free merge, i.e. LDS — is the wrong one for a strict-priority device,
the two differ on a measurable set of arrival orders, and the error is directional: always short,
never long. Contribution level: **theory + empirics**, resting on two *models* rather than two
deployments — free merge and strict priority — each with its own exact statistic, both certified
against an independently written exhaustive brute force over {{n:cert_pairs_total}} (window, k) pairs
with {{n:certificate.distinct.mismatches}} and {{n:certificate.ties.mismatches}} mismatches
respectively, and with the deployed rank-band rule plus a per-cell anti-rule control as baselines.

## 1 Prior art and the shape of the claim

The combinatorial fact this paper uses is not new, and the first obligation of the paper is to say so
precisely rather than in a hedge.

Sorting by a network of queues and stacks is a classical problem with a classical literature. Even
and Itai {{cite:evenitai1971}} treated queues, stacks and graphs as sorting devices. Tarjan
{{cite:tarjan1972}} gave sorting using networks of queues and stacks. Pratt {{cite:pratt1973}}
computed which permutations double-ended queues, parallel stacks and parallel queues produce. Of the
three, Pratt's question is the nearest to ours: a bank of `k` strict-priority queues is a set of
parallel queues, and "which arrival orders can this bank emit without a rank inversion" is the
question that title names.

We could not read those statements. Crossref confirms each record by DOI — title, venue, year — and
nothing more, because the pages that carry the theorems returned `HTTP 403` to this environment. The
rule that follows is one we held throughout: **attribute, never claim**. This paper credits those
works with the problem and with the machinery, and makes no assertion about what their theorems say.
Where the two overlap, the overlap is theirs.

What a title does establish is that the *question* is old. What is not settled by a title, and what
the rest of this paper is about, is a different question: not "which permutations can a bank of
queues produce" but "given a statistic a designer can compute from the arrival order, what does it
tell her about the bank size she needs — and under which dequeue discipline". Those two questions
come apart. A designer does not choose an arrival order; she observes traffic and sizes a bank. The
interesting failure is therefore not that a statistic is inexact, but that the statistic in common
use is exact for a dequeue discipline no switch implements, and errs in the direction that
under-provisions.

## 2 Programmable packet scheduling, and what a PIFO costs to approximate

PIFO was introduced as a queue abstraction whose dequeue order is set by a programmable ranking
function rather than by arrival order {{cite:pifo2016}}. It gives a scheduler a single logical queue
ordered by rank and a push-in operation that keeps it ordered, and it is the abstraction that turns
"which packet next" into "assign a rank to each packet". A switch cannot afford one: an exact PIFO
needs an ordered insertion per packet at line rate. What is affordable is a small bank of FIFO queues
plus a mapping from rank to queue, so the practical question is how many queues an emulation needs
before its output order is indistinguishable from the abstraction.

The recent designs answer that question by construction rather than by analysis. SP-PIFO gives the
theory, the algorithms and the evaluation of a mapping that keeps a stack of bounded-size queues
aligned with rank bands {{cite:sppifo2022}}; DR-PIFO replaces the fixed mapping with a dynamic
ranking rule over a PIFO queue {{cite:drpifo2024}}; vPIFO virtualises the scheduler for hierarchical
scheduling {{cite:vpifo2024}}; Scale-up PIFO interleaves multiple priority queues for high-speed
programmable scheduling {{cite:scaleuppifo2026}}; and the family continues through Exp-PIFO's
scalability argument {{cite:exppifo2025}}, D-PIFO's dynamic priority rule for performance-critical
packets {{cite:dpifo2024}}, CIPO's lightweight primitive {{cite:cipo2024}}, FIPO's software-defined
scheduler {{cite:fipo2025}}, Spring's heuristic for the SP-PIFO mapping itself {{cite:spring2025}},
Lark's buffer-aware building block {{cite:lark2025}}, a traffic-rate-driven ranking method
{{cite:ratesched2024}}, a hardware dynamic-ranking architecture {{cite:hwrank2023}}, near-optimal
deadline scheduling in multihop networks {{cite:nearsched2024}}, a strict-priority multi-tier
scheduler {{cite:ddspq2025}}, TCP acceleration for hybrid circuit/packet data centres
{{cite:acceltor2025}}, and reconciliation of programmable scheduling with a FIFO queue for
time-sensitive traffic {{cite:tsfifo2023}}. The earlier line supplies the surrounding machinery:
programmable scheduling demonstrated on FPGA-based switches {{cite:schedfpga2025}}, on a P4 data
plane {{cite:p4sched2021}}, and inside a DPDK-based processing system {{cite:dpdk2021}}; a
programmable data plane that makes quality of service a function {{cite:qosdp2024}}; time as an
input to forwarding decisions {{cite:timeaware2025}}; a survey of AI-driven forwarding with a
programmable data plane {{cite:p4survey2023}}; what a SmartNIC data plane can do at packet rate
{{cite:smartnic2023}}; packet-level analysis at line rate {{cite:anomaly2026}}; and FIFO-based
round-robin multicast scheduling, the discipline this paper compares against {{cite:fifo2024}}
{{cites:2 Background:recent}} {{cites:2 Background:earlier}}.

Across that body of work the number of queues is a **design parameter chosen by the designer**, and
the evaluation is end-to-end — completion time, tail latency, throughput — rather than a statement
about which arrival orders a given bank can order correctly. This paper takes the complementary
view: it fixes the bank at `k` queues, asks exactly which arrival orders can be emitted without a
rank inversion, and derives the statistic that decides it. That makes the queue count an *output* —
a property of the traffic and of the dequeue discipline — rather than a budget to be tuned.

## 3 The device model: queues, disciplines, and what a bank can emit

A switch that emulates PIFO is a scheduler with a fixed number of queues and a rule for which queue
is served. The scheduling literature supplies both halves of that picture, and supplies the baselines
this paper measures against.

On the matching side, an input-queued switch must resolve contention every slot, and its algorithms
are matching algorithms: virtual output queueing {{cite:voq2019}}, iterative algorithms such as QPS-r
{{cite:qpsr2021}} and parallel iterative matching {{cite:pim2009}}, round-robin matching
{{cite:hdmrr2019}}, longest-queue-first {{cite:lqf2010}}, approximate max-weight matching under
heavy traffic {{cite:maxweight2020}}, and a diffusion approximation for maximum-weight matching
{{cite:mwm2012}}. The architectural statements behind them — Birkhoff-von Neumann decomposition of a
schedule {{cite:bvn2024}}, output-queued behaviour imitated by an input-queued switch
{{cite:oqsq2009}}, combined input-output queueing {{cite:ciocq2026}}, and scalable Clos fabrics
{{cite:clos2007}} — say what a fabric can realise in principle, which is the question a rank-band
emulation is a special case of. Multicast with variable packet size is the same problem with a
broader output set {{cite:multicast2017}}.

On the dequeue side the disciplines are the classical ones: strict priority {{cite:strprio2016}},
deficit round robin {{cite:drr2025}} {{cite:drr2012}}, weighted fair queueing and its approximations
{{cite:wfq2010}} {{cite:owfq2023}} {{cite:wfq2012}}, class-based low-latency fair queueing
{{cite:cbllfq2020}}, a combined priority and weighted-fair device {{cite:priowfq2020}}, weighted round
robin at line rate {{cite:rr2014}}, crosspoint-queued switches {{cite:cqswitch2013}}, weighted round
robin at a network-on-chip router {{cite:nocqos2012}}, and buffers whose own access order is part of
the scheduling design {{cite:rrbuffer2010}} {{cites:3 The device model:recent}}
{{cites:3 The device model:earlier}}.

Two of those disciplines are the two models this paper compares, and they are worth stating as
programs rather than as names:

- **Free merge.** Dequeuing may take the head of any queue, in any order. This is the discipline
  under which Dilworth's theorem applies, and the one that yields LDS.
- **Strict priority.** Queues are served in priority order: the output is the concatenation of the
  queues, each in arrival order, highest priority first. This is the discipline a rank-band emulation
  actually implements, and the one that yields `runs(p)`.

Both models are batch: every packet arrives, then dequeuing begins. That is a boundary of the model,
and §11 states what it costs.

## 4 The combinatorics: runs, descents, chain decompositions

The two statistics this paper separates both live in the permutation-statistics literature, which is
why the separation is easy to miss.

The free-merge side is the chain-decomposition side. Dilworth's theorem gives the partition of a
permutation into the fewest decreasing subsequences, and its generalisation to partially ordered
multisets {{cite:dilworthgen2024}} is exactly what the tied-rank case needs; the classical
decomposition theorem itself {{cite:dilworth2009}} and optimal balanced chain decomposition
{{cite:chaindecomp2022}} supply the constructive versions. The statistic a designer computes from that
theorem is the longest decreasing subsequence, and the longest-increasing-subsequence literature
around it is where its algorithmic cost and its structure are worked out: revisiting the problem
{{cite:lisrevisited2026}}, its relation to the longest decreasing subsequence {{cite:ehrt2019}},
parallel {{cite:parallellis2023}}, dynamic {{cite:dynamiclis2021}}, sublinear
{{cite:sublinear2021}} and space-bounded {{cite:spacelis2019}} algorithms, a commentary on the
patience-sorting line {{cite:patience2018}}, and the shape of permutations whose increasing
subsequence is unique or pattern-avoiding {{cite:incr2020}}.

The strict-priority side is the descents side. The number of descents of a permutation, its joint
distribution with the inverse statistic, its concentration and its large deviations are all known
{{cite:descents2025}} {{cite:descsharp2025}} {{cite:desclargedev2024}}, including under a Mallows
model {{cite:mallows2022}}; the Robinson-Schensted correspondence is the classical bridge between a
permutation's insertion structure and its statistics {{cite:rsk2019}} and is still being generalised
{{cite:rsk2024}} {{cite:rskpoisson2023}}; and continued-fraction and poset-entropy treatments give the
same statistics a generating-function face {{cite:continfrac2018}} {{cite:widthentropy2015}}
{{cite:posetramsey2024}}. Sorting devices are the applied face of the same objects — networks of
stacks and queues as sorting devices {{cite:sortnetstack2008}}, and stack-sorting under vincular
pattern avoidance {{cite:stacksort2026}} {{cites:4 Combinatorics:recent}}
{{cites:4 Combinatorics:earlier}}.

The point the paper needs from this literature is a single one: **the two statistics are different,
and the difference is directional.** `runs(p)` counts the contiguous ascending runs of the inverse
arrival order; LDS measures the longest decreasing subsequence. §9 proves `runs(p) >= LDS`. A
reader who knows this literature will recognise `runs(p)` as a descent statistic and LDS as its
chain-decomposition cousin; what the rest of this paper adds is which of them a strict-priority
device obeys, and by how much the other one is wrong.

## 5 Online algorithms: what foresight is worth

The model in this paper is offline in the narrow sense that it asks what a bank of `k` queues *could*
emit for a given arrival order, not what an online policy achieves without foresight. That is a real
boundary, and the online literature is the right place to price it.

Lookahead is the quantity that separates the two. Online packet scheduling with bounded delay and
lookahead {{cite:onpktlookahead2019}} is the closest analogue of the comparison here, and exact
distributional analyses of online algorithms with lookahead {{cite:lookaheadexact2020}}, together
with its published correction {{cite:lookaheadcorr2021}}, give the machinery for reading a lookahead
budget as a distribution rather than as a parameter. The power of lookahead is measured in interval
scheduling on related machines {{cite:onlineinterval2019}}, in online machine minimisation
{{cite:machinemin2020}}, in semi-online scheduling with initial lookahead {{cite:semiuniform2024}},
and in online unit-length batch scheduling {{cite:unitbatch2019}}; competitive analysis of online
matching {{cite:metmatch2021}} and of an online distribution problem {{cite:competcloud2024}}
supplies the comparison standard {{cites:5 Online algorithms:recent}}
{{cites:5 Online algorithms:earlier}}.

One recent line deserves naming separately because it shares this paper's information shape: a
non-clairvoyant scheduler given a *permutation prediction* {{cite:permpred2025}} is handed
information of exactly the kind `runs(p)` summarises. What this paper computes is the exact value of
that summary for a bank of a given size. What remains open, and is not claimed here, is how much of
it an online policy can recover without the whole order.

## 6 Priority-queue data structures: where the abstraction meets silicon

A PIFO emulation is only useful if the queues can be deep and fast, and the data-structure literature
is where that cost is paid.

Hardware priority queues are constrained by the same operation mix a scheduler needs: AnTiQ gives
constant-time arbitrary element removal {{cite:antq2023}}, a pipelined heap {{cite:pipelinedheap2007}}
and a scalable multi-push queue {{cite:fastpq2024}} attack the per-slot budget, and a strictly
concurrent priority queue {{cite:qpidsr2026}} attacks the parallel-access side. Double-ended
structures matter because a PIFO's push-in operation is double-ended by nature: the relaxed min-max
heap {{cite:delaunay1993}}, the deap {{cite:deap1987}} and the symmetric min-max heap
{{cite:minmax1999}}. Randomised and parallel accesses {{cite:randpq1998}}
{{cite:binomialheaps2000}} and packaged implementations {{cite:jheaps2021}}
{{cite:binaryheaps2025}} are the ordinary tooling, and the monotone-input restriction where keys only
decrease {{cite:decreasingkeys2024}} is closer to a switch's actual input than the general case
{{cites:6 Data structures:recent}} {{cites:6 Data structures:earlier}}.

The relevance to this paper is one-directional: these structures say what a *single* ordered queue
costs, and they are the reason emulation exists at all. A bank of `k` FIFOs plus a rank map trades
one ordered structure for `k` unordered ones. This paper's result is about the smallest `k` that does
not change the output, which is the quantity that trade is priced against.

## 7 Measurement context: what this model does not measure

This paper measures no switch, no trace and no implementation. The literature that does is the
context the model has to be placed against, and it is the reason the claims in §13 are scoped
to a model rather than to a deployment.

Flow completion time is the end-to-end quantity a scheduler is judged by {{cite:ctpifo2025}}, and the
implementation settings that dominate the achievable numbers are a templated parser at terabit scale
{{cite:trimmer2022}}, a SmartNIC used for a collective {{cite:smartnicallreduce2024}}, an XDP path
offloaded to a SmartNIC {{cite:xdp2023}}, and IP fragmentation offloaded to a SmartNIC in P4
{{cite:frag2026}} {{cites:7 Measurement:recent}} {{cites:7 Measurement:earlier}}.

One record in this area is not a research report but a retraction notice {{cite:noc2024}}, and we
cite it as exactly that rather than as evidence for anything: it appears because a bibliography that
silently dropped the record it found, and silently kept the one it liked, would not be a record of
what the harvest returned.

The gap this paper leaves open is explicit and named: **how many queues a deployed emulation actually
needs under a real trace** is not answered here, and nothing in this paper should be read as an
estimate of it. What is answered is what any such deployment is short of, which is a property of the
model and transfers to a trace evaluation as a per-window diagnostic.

## 8 The model

Traffic is an arrival order of `n` packets whose ranks are drawn from a small alphabet of `m` values,
so that `m < n` means ranks repeat. A bank has `k` queues. A scheduler assigns each packet to a queue
and the dequeue discipline fixes the output order. The cost of an assignment is the number of rank
inversions in the emitted order, where a pair of equal rank is **never** an inversion in either
order: a tie is rank-consistent whichever way it is emitted. That convention is not a convenience —
it is what lets both instruments generalise to ties without modification, and it is recorded in the
artifact as `{{n:certificate.ties_are_not_inversions}}`.

Two floors are computed, one per discipline.

**The free floor.** `F(k) = 0` iff `LDS <= k`. This is Dilworth's theorem read as a scheduler: with
free merge, a partition into `k` decreasing subsequences can be emitted in increasing rank order
within each queue, so no inversion survives. `LDS` is therefore exact for free merge and for nothing
else.

**The restricted floor.** `R(k)` is the minimum, over all assignments of packets to `k` queues, of the
inversion count of the output a strict-priority dequeue produces. It is computed twice, by two
programs written from different premises: a dynamic program over the prefix structure of the
assignment, and an exhaustive enumeration of all `k`-to-the-`n` assignments. That the two agree on
every (window, k) pair is the certificate, and it is the reason a defect in either one is caught
rather than averaged away.

**The statistic.** For an arrival order whose inverse permutation is `p`, define
`runs(p) = 1 + #{i : p[i+1] < p[i]}`, the number of maximal contiguous ascending runs of `p`. The
claim of this paper is `required k = runs(p)` for the strict-priority model with distinct ranks, and
the argument is one line: strict priority emits the queues concatenated in priority order, each in
arrival order, so an ascending output requires the rank axis to be cut into contiguous blocks, one
per descent of `p`.

`runs(p) >= LDS` is not an observation about the windows we ran; it is a proposition with a proof,
and the proof is what lets the claim survive outside the enumerated range. Decompose `p` into its
maximal contiguous increasing runs. Within one run, ranks and arrival positions increase together.
Take any strictly decreasing subsequence of the arrival order; read its members in increasing rank
order, and their arrival positions are strictly decreasing. No run can contain two of its members,
since two members of one run would have increasing positions when read in increasing rank order. So
the subsequence has at most one member per run, and its length is at most `runs(p)`. As this holds
for every strictly decreasing subsequence, `LDS <= runs(p)`. The artifact checks the consequence
directly: over every enumerated window, {{n:inequality_runs_p_ge_lds.violations}} windows have
`runs(p) < LDS`.

Two hand-checkable witnesses anchor the instruments before any aggregate is read. The arrival order
with ranks `2,1,4,3` has `runs(p) = {{n:certificate.witnesses.hand_case_2_1_4_3_runs}}` and
`LDS = {{n:certificate.witnesses.hand_case_2_1_4_3_lds}}`; its restricted floor is
{{n:certificate.witnesses.hand_case_2_1_4_3_floor_k2}} at `k = 2` and
{{n:certificate.witnesses.hand_case_2_1_4_3_floor_k3}} at `k = 3`. A reversed window of n = 6 at
`k = 1` must produce {{n:certificate.witnesses.reverse_window_n6_k1}} inverted pairs and a sorted one
must produce {{n:certificate.witnesses.sorted_window_n6_k1}}, because one queue can only reproduce
arrival order. Reading an aggregate against those witnesses is what caught the defect recorded in
§11.

## 9 Results

Every number in this section is emitted by `emit_results.py` into `results.json` and substituted here
by `make_manuscript.py`; none is typed. Enumeration is exhaustive over every arrival order in the
stated range, so there is no sampling noise and no confidence interval to report — the uncertainty is
a *range* bound (n, m, k), not a noise bound.

### 9.1 The certificate

The restricted floor is computed by a dynamic program and, independently, by exhaustive enumeration
over all assignments. On distinct-rank windows the two agree on {{n:certificate.distinct.pairs}}
(window, k) pairs with {{n:certificate.distinct.mismatches}} mismatches; on tie-bearing windows, on
{{n:certificate.ties.pairs}} pairs with {{n:certificate.ties.mismatches}} mismatches. This is an
instrument certificate: it says the floor is the floor, not that a particular code path ran.

### 9.2 Distinct ranks: the statistic, and what the default statistic does

{{table:threshold_distinct}}

`runs(p)` is exact on every enumerated window. LDS is not: at n = 7 it understates the requirement on
{{n:threshold_distinct[7].lds_understates_windows}} of {{n:threshold_distinct[7].windows}} windows.
The same event is counted a second way — `runs(p) - LDS > 0` over the gap distribution — and the two
counts agree count for count, which is a cross-check rather than a duplicate reading:

{{table:gap_distinct}}

The magnitude is the number a reviewer will compute, so it is stated as its own claim: **the
discipline gap never exceeds {{n:gap_summary.distinct_max_gap}} queues in the measured range** (the
maximum is attained at n = {{n:gap_summary.distinct_max_gap_n}}). Frequent and small is a different
finding from frequent and large, and the honest headline is the pair: on almost half the n = 7
windows the default statistic is wrong, and by one or two queues.

### 9.3 Ties: three candidates, and what survives

Ranks in hardware come from a few bits of packet state, so ties are the normal case, not a pathology.
Four candidate statistics are tested against the DP-extracted requirement, never against each other:
`T1`, runs under a stable tie-break (equal ranks by arrival position); `T2`, runs under the
anti-stable tie-break; `T3`, the minimum of runs over all tie-breakings; and `LDS` as the control
expected to fail.

{{table:threshold_ties}}

Over {{n:threshold_ties_totals.windows}} tie-bearing windows the totals are `T1`
{{n:threshold_ties_totals.T1}}, `T2` {{n:threshold_ties_totals.T2}}, `T3`
{{n:threshold_ties_totals.T3}} and `LDS` {{n:threshold_ties_totals.LDS}}.

`T3` is exact, and it is **an algorithm, not a closed form**: it minimises over tie-breakings, so
calling it "the statistic" would overstate what we have. It does reduce to `runs(p)` when ranks are
distinct, which makes the distinct-rank result its closed-form special case — but the tied case costs
a minimisation, and a paper that reported only the zero would be hiding the cost.

### 9.4 The magnitude under ties

{{table:gap_ties}}

Over the {{n:ties_gap_scope_windows}} tie-bearing windows at n = 5…6 the gap is non-zero on
{{n:gap_summary.ties_nonzero}} windows — {{p:gap_summary.ties_nonzero_fraction}} % — and its maximum
is {{n:gap_summary.ties_max_gap}}. For every cell with `m <= 3` the gap is identically zero. So the
honest form of the headline is **stratified**: the discipline pairing is frequent under distinct
ranks ({{p:threshold_distinct[7].lds_understates_fraction}} % at n = 7, magnitude at most
{{n:gap_summary.distinct_max_gap}}) and nearly absent under ties
({{p:gap_summary.ties_nonzero_fraction}} %, magnitude at most {{n:gap_summary.ties_max_gap}}). A
reader who needs one sentence should read the pair, not the first half.

### 9.5 The deployed rank-band rule against the floor

A designer does not choose an assignment optimally; she maps rank bands to queues. The aligned band
rule is that map, and the anti-rule control is the same map with the queue order reversed, so that a
cell which cannot register a loss is visible as such rather than counted as a win.

{{table:rules}}

Two facts about this table matter more than its headline. First, the anti-rule control loses in every
cell (on at least {{p:rules_summary.control_min_fraction}} % of windows), so no cell is measuring
nothing. Second, **only {{n:rules_informative_cells}} of the {{n:rules_summary.cells}} cells can
measure a gap at all.** When `k >= m` every rank owns a queue, the aligned map is injective by
construction, and the rule attains the floor without being right about anything; the
{{n:rules_forced_cells}} such cells confirm the implementation and measure nothing, and they are
counted as forced here rather than folded into a win rate. A check in `emit_results.py` asserts that
every one of them reports exactly zero losses, so a cell that starts losing there is a code defect
and not a result.

In the {{n:rules_informative_cells}} informative cells the aligned rule loses on
{{n:rules_informative_min_pct}} % and {{n:rules_informative_max_pct}} % of windows, with a worst cell
ratio of {{n:rules_summary.aligned_max_worst_ratio}} times the floor. The `k = 1` cells are reported
as FORCED and never as comparisons: one queue cannot choose, so it cannot be compared.

![The discipline gap as a distribution over windows. Each bar is the share of windows at a given
`required k - LDS`; the printed percentage is the share of windows on which the two disciplines
disagree. Redrawn from `results.json` by `make_figure.py`, which asserts the caption's claims as
invariants.](figures/discipline-gap.png)

## 10 Registered prior beliefs, and what happened to them

The study registered its expectations before running, and reports them in that order — not as a
retrospective narrative.

**P1 — the free-merge threshold transfers to the device.** Registered expectation: `R(k) = 0` iff
`k >= LDS`, i.e. the statistic a designer already knows is the one a strict-priority device obeys. The
justification given at registration was Dilworth's theorem: the partition bound holds for any
emulation, so the device was expected to attain it. **Status: refuted.** Under strict priority the
bound is not attained; the exact requirement is `runs(p)`, which exceeds `LDS` on
{{n:threshold_distinct[7].lds_understates_windows}} of {{n:threshold_distinct[7].windows}} n = 7
windows. This is the paper's substantive result, and it is the one the registered prior got wrong.

**P3 — the overshoot of a deployed rule is non-monotone in `k`.** Registered expectation: the worst
ratio of a band rule to the floor peaks at an intermediate `k`. **Status: unresolved, and not by
choice.** The reading that suggested P3 was taken against the free floor and against a band rule whose
queue priorities were misaligned by construction, so it does not count as evidence either way;
re-reading it needs an aligned rule over a `k` range wider than the cells this artifact carries. It is
recorded as unresolved rather than dropped, because a prior that quietly disappears from the record is
worse than one reported as untested.

**The ties falsifier.** Before the tied-rank measurement we registered a numeric falsifier: if the
best candidate were exact on fewer than `99` % of tie-bearing windows *and* the two disciplines
required the same `k` on more than `50` % of windows, the direction was to be **downgraded to a case
study** scoped to distinct ranks. The first condition failed — `T3` is exact — so the registered
verdict is *continue*. The second condition is nevertheless true, and is reported in §9.4 as
prominently as the first, because a falsifier whose two limbs are quoted together must have both limbs
reported when only one of them fires.

## 11 Threats to validity

Read this as a list of what would make each claim false, not as a disclaimer.

**The statistic is classical.** `runs(p) = 1 + #{descents}` is not ours; it belongs to the
queue-and-stack sorting literature cited in §1, which we could not read. Our contribution is
the pairing of a statistic with a dequeue discipline, and a reader who finds that a cited work already
states the pairing is right, and that work is prior art for it. This is the largest threat in the
paper, and no amount of internal verification reduces it.

**The model has no deployment.** No trace, no implementation and no hardware is measured anywhere.
Every claim is about a model with an exact optimum. The claim that a deployed emulation is short of it
in the same way is *not* made, and would need a trace evaluation.

**No interleaved arrival.** Traffic is batch: every packet arrives, then dequeuing begins. Real
switches interleave, and the restricted floor is sensitive to interleaving while the free floor is
not. This is the boundary most likely to move the threshold, and it is untested.

**Range bounds, not noise bounds.** Distinct ranks: `n <= 7`. Ties: `n <= 6` with `m <= 4`. The bound
of {{n:gap_summary.distinct_max_gap}} queues on the gap is a **measured maximum over those windows**,
not a theorem; nothing here forbids a larger gap at larger n, and the proof of `runs(p) >= LDS` bounds
the direction of the error, not its size.

**Two of six rule cells are informative.** §9.5 reports the {{n:rules_informative_cells}}
informative cells separately from the {{n:rules_forced_cells}} forced ones. A reader who takes the
six-cell summary as a win rate is reading a number that four of its cells cannot earn.

**A caution about the instruments themselves.** Both defects found in this study were found by
cross-checking two instruments, not by a guard. A guard whose answer is the same under the correct and
the incorrect reading cannot separate them: an early tie case returned zero under both, and the defect
in an inversion predicate survived it. The artifact carries hand-computable witnesses for exactly this
reason, and they are asserted before any aggregate is read.

## 12 Related work, and the specific difference in each case

Six comparisons, each with the difference stated rather than implied.

**Pratt, Even-Itai, Tarjan** {{cite:pratt1973}} {{cite:evenitai1971}} {{cite:tarjan1972}}. They own the
combinatorics: which permutations a network of queues and stacks produces. This paper does not contest
or extend that, and it did not read their statements. The difference is the axis: they ask which
permutations a bank can produce, we ask what a statistic computed from observed traffic tells a
designer about the bank size she needs, and we show those answers depend on the dequeue discipline.

**SP-PIFO** {{cite:sppifo2022}}. It gives a mapping and an evaluation, so its queue count is a design
choice validated end-to-end. Ours is an exact floor for a given count, so the two are complements: our
floor says what their mapping loses before their evaluation measures it.

**Scale-up PIFO** {{cite:scaleuppifo2026}}. It interleaves multiple priority queues to make a bank
faster. We ask how many queues the bank needs at all. A smaller bank is one way to spend less; ours is
the statement of how small it can be before the output changes.

**AnTiQ and hardware priority queues** {{cite:antq2023}} {{cite:fastpq2024}}. They price a single
ordered queue in silicon and are the reason emulation is needed. We price the number of unordered
queues that replace it.

**Online packet scheduling with lookahead** {{cite:onpktlookahead2019}}. It measures what a bounded
lookahead buys an online policy, as a competitive ratio. We compute an offline exact floor. A
competitive ratio against our floor is a natural follow-up, and this paper does not attempt it.

**Sorting with networks of stacks and queues** {{cite:sortnetstack2008}}. It studies the complexity of
the sorting problem those devices pose. We use the resulting statistic and add no complexity result.

## 13 Significance: whose decision changes

The community is switch and programmable-scheduler designers, and the belief that changes is a specific
one: **that the statistic which decides how many queues are needed is discipline-independent.** It is
not. A designer reading "`k >= LDS` suffices" from a Dilworth-style analysis is reading a threshold for
a dequeue discipline no switch implements, and the error has a sign — the bank is under-provisioned,
never over-provisioned.

Three decisions change. First, sizing: a designer now has a number per discipline instead of one number,
and can say what a given `k` is short of rather than only that it is short. Second, evaluation: a
paper that reports an emulation's fidelity against a free-merge bound is reporting against the wrong
bound, and can re-read its own numbers against the strict-priority floor. Third, review: a reviewer who
computes actual queue counts can now check whether an effect was inflated, which is why §9.4
reports the frequency and the magnitude together and why the ties result is given the same prominence
as the distinct-rank one — the pairing is a real distinction under distinct ranks and nearly vanishes
under ties, and a paper that reported only the first half would be selling the stronger half of a
stratified result.

## 14 Conclusion

The number of priority queues a scheduler needs is a property of the traffic *and* of the dequeue
discipline. Under a strict-priority dequeue the exact requirement is `runs(p)`, the number of maximal
ascending runs of the inverse arrival order; it is exact on every one of
{{n:total_distinct_windows}} enumerated distinct-rank windows, it dominates the longest decreasing
subsequence, and the dominance is a theorem rather than an enumeration. The default statistic is
therefore not merely inexact but *directional*: it understates, on
{{p:threshold_distinct[7].lds_understates_fraction}} % of n = 7 windows, by at most
{{n:gap_summary.distinct_max_gap}} queues. Under ties the statistic needs a minimisation over
tie-breakings, and the discipline distinction nearly disappears — {{p:gap_summary.ties_nonzero_fraction}} %
of tie-bearing windows. The combinatorics is classical and is credited as such; what is new is the
pairing, and the measurement of how much the pairing is worth.

## 15 Reproducibility

The package is one command, offline, with no sampling and no random seeds:

```
./reproduce.sh
```

Its last line is `REPRODUCE: ALL GREEN (5 steps)` and its exit status is the number of failed steps, so
a failure accumulates rather than being masked by a later step. The five steps emit `results.json` from
the model, redraw the figure from `results.json`, recompute every stored summary from the rows it
summarises, check that the reference placement still resolves and still matches its committed artifact,
and check that this manuscript still matches what its generator produces. Every artifact is expected to
be reproduced byte for byte; `README.md` states the environment, the tolerance and what is deliberately
not covered.

Citation integrity is part of the package rather than of the prose: `reference-check.md` records, for
each of the {{nplaced}} references, the DOI, the Crossref record it resolves to, and an agreement score;
seven entries carry an edition-year note rather than being smoothed over. Every reference is cited in
the body above, and `make_manuscript.py` refuses to write the paper if one is not — a bibliography entry
the body never cites is padding, and the generator treats it as a failure rather than a style issue.

{{refs}}
