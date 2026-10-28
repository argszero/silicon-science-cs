# The Queue Count Is Not the Fidelity: An Exact Rank-Inversion Floor for PIFO Emulation, and the Traffic Statistic That Sets It

## Abstract

Programmable packet schedulers emulate a push-in-first-out (PIFO) queue with a small bank of
strict-priority queues, and the size that bank needs is usually answered with the longest
decreasing subsequence (LDS) of the arrival order — the statistic behind Dilworth's
chain-decomposition theorem. This paper shows that statistic answers a different question from
the one a device asks. Under a strict-priority dequeue the exact requirement is `runs(p)`, the
number of maximal ascending runs of the inverse arrival order; we verify `required k = runs(p)`
exhaustively over all 5904 distinct-rank arrival orders at n = 4…7 with 0 violations, and prove
`runs(p) >= LDS`. The inequality is what makes the error one-directional: LDS cannot overstate
what a device needs, so it is *short* — on 48.1 % of n = 7 windows, by at most 2 queues in the
measured range. Ties move both numbers at once. The statistic survives them only when it is
minimised over tie-breakings (0 violations over 6285 tie-bearing windows), while the *frequency*
of the discipline gap collapses: once ranks repeat, the two disciplines require the same queue
count on 97.7 % of windows, against 51.9 % at n = 7 with distinct ranks.

**Prior-art position, stated first because it bounds the novelty.** The statistic `runs(p) = 1 +
#{descents}` is *classical* permutation-sorting machinery. Even and Itai
[2] treated queues, stacks and graphs as sorting devices; Tarjan [3]
gave sorting using networks of queues and stacks; and Pratt [1] computed which permutations
double-ended queues, parallel stacks and parallel queues produce — which is, almost literally,
this paper's question. We verified all three records **by DOI** against Crossref and **did not
read them**: every publisher landing page and bronze-OA PDF for them returned `HTTP 403` to this
environment, and we did not attempt to reach them by another route. This paper therefore
*attributes* the problem and the machinery to those works and asserts nothing about their
statements. If a reader who can open them finds that one already states a result of ours, the
result is theirs, and ours is a re-derivation in a scheduler's setting.

What is left, and what this paper claims, is a **system-level pairing**: the number of queues a
scheduler needs is a function of the traffic *and* of the dequeue discipline. The discipline the
literature treats as default — free merge, i.e. LDS — is the wrong one for a strict-priority
device, the two differ on a measurable set of arrival orders, and the error is directional:
always short, never long. Contribution level: **theory + empirics**, resting on two *models*
rather than two deployments — free merge and strict priority — each with its own exact
statistic, both certified against an independently written exhaustive brute force over 6084
(window, k) pairs with 0 and 0 mismatches respectively, and with the deployed rank-band rule
plus a per-cell anti-rule control as baselines.

## 1 Prior art and the shape of the claim

The combinatorial fact this paper uses is not new, and the first obligation of the paper is to
say so precisely rather than in a hedge.

Sorting by a network of queues and stacks is a classical problem with a classical literature.
Even and Itai [2] treated queues, stacks and graphs as sorting devices. Tarjan
[3] gave sorting using networks of queues and stacks. Pratt [1]
computed which permutations double-ended queues, parallel stacks and parallel queues produce. Of
the three, Pratt's question is the nearest to ours: a bank of `k` strict-priority queues is a
set of parallel queues, and "which arrival orders can this bank emit without a rank inversion"
is the question that title names.

We could not read those statements. Crossref confirms each record by DOI — title, venue, year —
and nothing more, because the pages that carry the theorems returned `HTTP 403` to this
environment. The rule that follows is one we held throughout: **attribute, never claim**. This
paper credits those works with the problem and with the machinery, and makes no assertion about
what their theorems say. Where the two overlap, the overlap is theirs.

What a title does establish is that the *question* is old. What is not settled by a title, and
what the rest of this paper is about, is a different question: not "which permutations can a
bank of queues produce" but "given a statistic a designer can compute from the arrival order,
what does it tell her about the bank size she needs — and under which dequeue discipline". Those
two questions come apart. A designer does not choose an arrival order; she observes traffic and
sizes a bank. The interesting failure is therefore not that a statistic is inexact, but that the
statistic in common use is exact for a dequeue discipline no switch implements, and errs in the
direction that under-provisions.

## 2 Programmable packet scheduling, and what a PIFO costs to approximate

PIFO was introduced as a queue abstraction whose dequeue order is set by a programmable ranking
function rather than by arrival order [23]. It gives a scheduler a single logical queue ordered
by rank and a push-in operation that keeps it ordered, and it is the abstraction that turns
"which packet next" into "assign a rank to each packet". A switch cannot afford one: an exact
PIFO needs an ordered insertion per packet at line rate. What is affordable is a small bank of
FIFO queues plus a mapping from rank to queue, so the practical question is how many queues an
emulation needs before its output order is indistinguishable from the abstraction.

The recent designs answer that question by construction rather than by analysis. SP-PIFO gives
the theory, the algorithms and the evaluation of a mapping that keeps a stack of bounded-size
queues aligned with rank bands [24]; DR-PIFO replaces the fixed mapping with a dynamic ranking
rule over a PIFO queue [16]; vPIFO virtualises the scheduler for hierarchical scheduling [29];
Scale-up PIFO interleaves multiple priority queues for high-speed programmable scheduling [25];
and the family continues through Exp-PIFO's scalability argument [18], D-PIFO's dynamic priority
rule for performance-critical packets [13], CIPO's lightweight primitive [12], FIPO's
software-defined scheduler [19], Spring's heuristic for the SP-PIFO mapping itself [26], Lark's
buffer-aware building block [20], a traffic-rate-driven ranking method
[6], a hardware dynamic-ranking architecture [4], near-optimal
deadline scheduling in multihop networks [22], a strict-priority multi-tier scheduler [14], TCP
acceleration for hybrid circuit/packet data centres
[7], and reconciliation of programmable scheduling with a FIFO queue for
time-sensitive traffic [21]. The earlier line supplies the surrounding machinery: programmable
scheduling demonstrated on FPGA-based switches [15], on a P4 data plane [5], and inside a
DPDK-based processing system [10]; a programmable data plane that makes quality of service a
function [11]; time as an input to forwarding decisions [27]; a survey of AI-driven forwarding
with a programmable data plane [8]; what a SmartNIC data plane can do at packet rate
[28]; packet-level analysis at line rate [9]; and FIFO-based
round-robin multicast scheduling, the discipline this paper compares against [17]
[6,7,9,11,12,13,14,15,16,18,19,20,22,25,26,27,29] [4,5,8,10,17,21,23,24,28].

Across that body of work the number of queues is a **design parameter chosen by the designer**,
and the evaluation is end-to-end — completion time, tail latency, throughput — rather than a
statement about which arrival orders a given bank can order correctly. This paper takes the
complementary view: it fixes the bank at `k` queues, asks exactly which arrival orders can be
emitted without a rank inversion, and derives the statistic that decides it. That makes the
queue count an *output* — a property of the traffic and of the dequeue discipline — rather than
a budget to be tuned.

## 3 The device model: queues, disciplines, and what a bank can emit

A switch that emulates PIFO is a scheduler with a fixed number of queues and a rule for which
queue is served. The scheduling literature supplies both halves of that picture, and supplies
the baselines this paper measures against.

On the matching side, an input-queued switch must resolve contention every slot, and its
algorithms are matching algorithms: virtual output queueing [53], iterative algorithms such as
QPS-r
[52] and parallel iterative matching [51], round-robin matching
[39], longest-queue-first [44], approximate max-weight matching under
heavy traffic [40], and a diffusion approximation for maximum-weight matching
[37]. The architectural statements behind them — Birkhoff-von Neumann decomposition of a
schedule [48], output-queued behaviour imitated by an input-queued switch
[47], combined input-output queueing [35], and scalable Clos fabrics
[45] — say what a fabric can realise in principle, which is the question a rank-band
emulation is a special case of. Multicast with variable packet size is the same problem with a
broader output set [43].

On the dequeue side the disciplines are the classical ones: strict priority [31], deficit round
robin [33] [34], weighted fair queueing and its approximations
[32] [49] [46], class-based low-latency fair queueing
[41], a combined priority and weighted-fair device [42], weighted round
robin at line rate [50], crosspoint-queued switches [38], weighted round robin at a
network-on-chip router [30], and buffers whose own access order is part of the scheduling design
[36] [33,35,48]
[30,31,32,34,36,37,38,39,40,41,42,43,44,45,46,47,49,50,51,52,53].

Two of those disciplines are the two models this paper compares, and they are worth stating as
programs rather than as names:

- **Free merge.** Dequeuing may take the head of any queue, in any order. This is the discipline
under which Dilworth's theorem applies, and the one that yields LDS.
- **Strict priority.** Queues are served in priority order: the output is the concatenation of the
queues, each in arrival order, highest priority first. This is the discipline a rank-band
emulation actually implements, and the one that yields `runs(p)`.

Both models are batch: every packet arrives, then dequeuing begins. That is a boundary of the
model, and §11 states what it costs.

## 4 The combinatorics: runs, descents, chain decompositions

The two statistics this paper separates both live in the permutation-statistics literature,
which is why the separation is easy to miss.

The free-merge side is the chain-decomposition side. Dilworth's theorem gives the partition of a
permutation into the fewest decreasing subsequences, and its generalisation to partially ordered
multisets [57] is exactly what the tied-rank case needs; the classical decomposition theorem
itself [56] and optimal balanced chain decomposition
[64] supply the constructive versions. The statistic a designer computes from that
theorem is the longest decreasing subsequence, and the longest-increasing-subsequence literature
around it is where its algorithmic cost and its structure are worked out: revisiting the problem
[74], its relation to the longest decreasing subsequence [76],
parallel [63], dynamic [60], sublinear
[61] and space-bounded [71] algorithms, a commentary on the
patience-sorting line [58], and the shape of permutations whose increasing subsequence is unique
or pattern-avoiding [65].

The strict-priority side is the descents side. The number of descents of a permutation, its
joint distribution with the inverse statistic, its concentration and its large deviations are
all known
[62] [69] [70], including under a Mallows
model [55]; the Robinson-Schensted correspondence is the classical bridge between a
permutation's insertion structure and its statistics [75] and is still being generalised
[54] [66]; and continued-fraction and poset-entropy treatments give the
same statistics a generating-function face [59] [67]
[68]. Sorting devices are the applied face of the same objects — networks of
stacks and queues as sorting devices [73], and stack-sorting under vincular pattern avoidance
[72] [54,57,62,68,69,70,72,74]
[55,56,58,59,60,61,63,64,65,66,67,71,73,75,76].

The point the paper needs from this literature is a single one: **the two statistics are
different, and the difference is directional.** `runs(p)` counts the contiguous ascending runs
of the inverse arrival order; LDS measures the longest decreasing subsequence. §9 proves
`runs(p) >= LDS`. A reader who knows this literature will recognise `runs(p)` as a descent
statistic and LDS as its chain-decomposition cousin; what the rest of this paper adds is which
of them a strict-priority device obeys, and by how much the other one is wrong.

## 5 Online algorithms: what foresight is worth

The model in this paper is offline in the narrow sense that it asks what a bank of `k` queues
*could* emit for a given arrival order, not what an online policy achieves without foresight.
That is a real boundary, and the online literature is the right place to price it.

Lookahead is the quantity that separates the two. Online packet scheduling with bounded delay
and lookahead [84] is the closest analogue of the comparison here, and exact distributional
analyses of online algorithms with lookahead [80], together with its published correction [79],
give the machinery for reading a lookahead budget as a distribution rather than as a parameter.
The power of lookahead is measured in interval scheduling on related machines [82], in online
machine minimisation
[83], in semi-online scheduling with initial lookahead [86],
and in online unit-length batch scheduling [81]; competitive analysis of online matching [77]
and of an online distribution problem [78] supplies the comparison standard [78,85,86]
[77,79,80,81,82,83,84].

One recent line deserves naming separately because it shares this paper's information shape: a
non-clairvoyant scheduler given a *permutation prediction* [85] is handed information of exactly
the kind `runs(p)` summarises. What this paper computes is the exact value of that summary for a
bank of a given size. What remains open, and is not claimed here, is how much of it an online
policy can recover without the whole order.

## 6 Priority-queue data structures: where the abstraction meets silicon

A PIFO emulation is only useful if the queues can be deep and fast, and the data-structure
literature is where that cost is paid.

Hardware priority queues are constrained by the same operation mix a scheduler needs: AnTiQ
gives constant-time arbitrary element removal [88], a pipelined heap [93] and a scalable
multi-push queue [87] attack the per-slot budget, and a strictly concurrent priority queue [90]
attacks the parallel-access side. Double-ended structures matter because a PIFO's push-in
operation is double-ended by nature: the relaxed min-max heap [98], the deap [97] and the
symmetric min-max heap
[96]. Randomised and parallel accesses [95]
[92] and packaged implementations [91]
[89] are the ordinary tooling, and the monotone-input restriction where keys only
decrease [94] is closer to a switch's actual input than the general case
[87,89,90,94] [88,91,92,93,95,96,97,98].

The relevance to this paper is one-directional: these structures say what a *single* ordered
queue costs, and they are the reason emulation exists at all. A bank of `k` FIFOs plus a rank
map trades one ordered structure for `k` unordered ones. This paper's result is about the
smallest `k` that does not change the output, which is the quantity that trade is priced
against.

## 7 Measurement context: what this model does not measure

This paper measures no switch, no trace and no implementation. The literature that does is the
context the model has to be placed against, and it is the reason the claims in §13 are scoped to
a model rather than to a deployment.

Flow completion time is the end-to-end quantity a scheduler is judged by [101], and the
implementation settings that dominate the achievable numbers are a templated parser at terabit
scale
[100], a SmartNIC used for a collective [102], an XDP path
offloaded to a SmartNIC [104], and IP fragmentation offloaded to a SmartNIC in P4
[103] [99,101,102,103] [100,104].

One record in this area is not a research report but a retraction notice [99], and we cite it as
exactly that rather than as evidence for anything: it appears because a bibliography that
silently dropped the record it found, and silently kept the one it liked, would not be a record
of what the harvest returned.

The gap this paper leaves open is explicit and named: **how many queues a deployed emulation
actually needs under a real trace** is not answered here, and nothing in this paper should be
read as an estimate of it. What is answered is what any such deployment is short of, which is a
property of the model and transfers to a trace evaluation as a per-window diagnostic.

## 8 The model

Traffic is an arrival order of `n` packets whose ranks are drawn from a small alphabet of `m`
values, so that `m < n` means ranks repeat. A bank has `k` queues. A scheduler assigns each
packet to a queue and the dequeue discipline fixes the output order. The cost of an assignment
is the number of rank inversions in the emitted order, where a pair of equal rank is **never**
an inversion in either order: a tie is rank-consistent whichever way it is emitted. That
convention is not a convenience — it is what lets both instruments generalise to ties without
modification, and it is recorded in the artifact as `true`.

Two floors are computed, one per discipline.

**The free floor.** `F(k) = 0` iff `LDS <= k`. This is Dilworth's theorem read as a scheduler:
with free merge, a partition into `k` decreasing subsequences can be emitted in increasing rank
order within each queue, so no inversion survives. `LDS` is therefore exact for free merge and
for nothing else.

**The restricted floor.** `R(k)` is the minimum, over all assignments of packets to `k` queues,
of the inversion count of the output a strict-priority dequeue produces. It is computed twice,
by two programs written from different premises: a dynamic program over the prefix structure of
the assignment, and an exhaustive enumeration of all `k`-to-the-`n` assignments. That the two
agree on every (window, k) pair is the certificate, and it is the reason a defect in either one
is caught rather than averaged away.

**The statistic.** For an arrival order whose inverse permutation is `p`, define `runs(p) = 1 +
#{i : p[i+1] < p[i]}`, the number of maximal contiguous ascending runs of `p`. The claim of this
paper is `required k = runs(p)` for the strict-priority model with distinct ranks, and the
argument is one line: strict priority emits the queues concatenated in priority order, each in
arrival order, so an ascending output requires the rank axis to be cut into contiguous blocks,
one per descent of `p`.

`runs(p) >= LDS` is not an observation about the windows we ran; it is a proposition with a
proof, and the proof is what lets the claim survive outside the enumerated range. Decompose `p`
into its maximal contiguous increasing runs. Within one run, ranks and arrival positions
increase together. Take any strictly decreasing subsequence of the arrival order; read its
members in increasing rank order, and their arrival positions are strictly decreasing. No run
can contain two of its members, since two members of one run would have increasing positions
when read in increasing rank order. So the subsequence has at most one member per run, and its
length is at most `runs(p)`. As this holds for every strictly decreasing subsequence, `LDS <=
runs(p)`. The artifact checks the consequence directly: over every enumerated window, 0 windows
have `runs(p) < LDS`.

Two hand-checkable witnesses anchor the instruments before any aggregate is read. The arrival
order with ranks `2,1,4,3` has `runs(p) = 3` and `LDS = 2`; its restricted floor is 1 at `k = 2`
and 0 at `k = 3`. A reversed window of n = 6 at `k = 1` must produce 15 inverted pairs and a
sorted one must produce 0, because one queue can only reproduce arrival order. Reading an
aggregate against those witnesses is what caught the defect recorded in §11.

## 9 Results

Every number in this section is emitted by `emit_results.py` into `results.json` and substituted
here by `make_manuscript.py`; none is typed. Enumeration is exhaustive over every arrival order
in the stated range, so there is no sampling noise and no confidence interval to report — the
uncertainty is a *range* bound (n, m, k), not a noise bound.

### 9.1 The certificate

The restricted floor is computed by a dynamic program and, independently, by exhaustive
enumeration over all assignments. On distinct-rank windows the two agree on 5016 (window, k)
pairs with 0 mismatches; on tie-bearing windows, on 1068 pairs with 0 mismatches. This is an
instrument certificate: it says the floor is the floor, not that a particular code path ran.

### 9.2 Distinct ranks: the statistic, and what the default statistic does

| n | windows | `runs(p)` violations | windows where LDS understates | share |
|---|---|---|---|---|
| 4 | 24 | 0 | 2 | 0.0833 |
| 5 | 120 | 0 | 25 | 0.2083 |
| 6 | 720 | 0 | 249 | 0.3458 |
| 7 | 5040 | 0 | 2422 | 0.4806 |

`runs(p)` is exact on every enumerated window. LDS is not: at n = 7 it understates the
requirement on 2422 of 5040 windows. The same event is counted a second way — `runs(p) - LDS >
0` over the gap distribution — and the two counts agree count for count, which is a cross-check
rather than a duplicate reading:

| n | windows | gap 0 | gap 1 | gap 2 | max gap |
|---|---|---|---|---|---|
| 4 | 24 | 22 | 2 | 0 | 1 |
| 5 | 120 | 95 | 25 | 0 | 1 |
| 6 | 720 | 471 | 239 | 10 | 2 |
| 7 | 5040 | 2618 | 2149 | 273 | 2 |

The magnitude is the number a reviewer will compute, so it is stated as its own claim: **the
discipline gap never exceeds 2 queues in the measured range** (the maximum is attained at n =
6). Frequent and small is a different finding from frequent and large, and the honest headline
is the pair: on almost half the n = 7 windows the default statistic is wrong, and by one or two
queues.

### 9.3 Ties: three candidates, and what survives

Ranks in hardware come from a few bits of packet state, so ties are the normal case, not a
pathology. Four candidate statistics are tested against the DP-extracted requirement, never
against each other: `T1`, runs under a stable tie-break (equal ranks by arrival position); `T2`,
runs under the anti-stable tie-break; `T3`, the minimum of runs over all tie-breakings; and
`LDS` as the control expected to fail.

| n | m | windows | T1 | T2 | T3 | LDS | mean required k |
|---|---|---|---|---|---|---|---|
| 4 | 2 | 16 | 0 | 16 | 0 | 0 | 1.6875 |
| 4 | 3 | 81 | 2 | 67 | 0 | 0 | 1.9259 |
| 5 | 2 | 32 | 0 | 32 | 0 | 0 | 1.8125 |
| 5 | 3 | 243 | 15 | 232 | 0 | 0 | 2.1235 |
| 5 | 4 | 1024 | 80 | 880 | 0 | 20 | 2.3047 |
| 6 | 2 | 64 | 0 | 64 | 0 | 0 | 1.8906 |
| 6 | 3 | 729 | 69 | 729 | 0 | 0 | 2.2812 |
| 6 | 4 | 4096 | 516 | 3926 | 0 | 120 | 2.5171 |

Over 6285 tie-bearing windows the totals are `T1` 682, `T2` 5946, `T3` 0 and `LDS` 140.

`T3` is exact, and it is **an algorithm, not a closed form**: it minimises over tie-breakings,
so calling it "the statistic" would overstate what we have. It does reduce to `runs(p)` when
ranks are distinct, which makes the distinct-rank result its closed-form special case — but the
tied case costs a minimisation, and a paper that reported only the zero would be hiding the
cost.

### 9.4 The magnitude under ties

| n | m | windows | gap 0 | gap 1 | max gap |
|---|---|---|---|---|---|
| 5 | 2 | 32 | 32 | 0 | 0 |
| 5 | 3 | 243 | 243 | 0 | 0 |
| 5 | 4 | 1024 | 1004 | 20 | 1 |
| 6 | 2 | 64 | 64 | 0 | 0 |
| 6 | 3 | 729 | 729 | 0 | 0 |
| 6 | 4 | 4096 | 3976 | 120 | 1 |

Over the 6188 tie-bearing windows at n = 5…6 the gap is non-zero on 140 windows — 2.3 % — and
its maximum is 1. For every cell with `m <= 3` the gap is identically zero. So the honest form
of the headline is **stratified**: the discipline pairing is frequent under distinct ranks (48.1
% at n = 7, magnitude at most 2) and nearly absent under ties (2.3 %, magnitude at most 1). A
reader who needs one sentence should read the pair, not the first half.

### 9.5 The deployed rank-band rule against the floor

A designer does not choose an assignment optimally; she maps rank bands to queues. The aligned
band rule is that map, and the anti-rule control is the same map with the queue order reversed,
so that a cell which cannot register a loss is visible as such rather than counted as a win.

| n | m | k | windows | aligned rule loses | share | worst ratio | anti-rule control loses | share | cell measures? |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 2 | 2 | 32 | 0 | 0.0000 | 0.00 | 30 | 0.9375 | no -- k >= m forces it |
| 5 | 3 | 2 | 243 | 99 | 0.4074 | 4.00 | 236 | 0.9712 | yes -- k < m |
| 5 | 3 | 3 | 243 | 0 | 0.0000 | 0.00 | 240 | 0.9877 | no -- k >= m forces it |
| 6 | 2 | 2 | 64 | 0 | 0.0000 | 0.00 | 62 | 0.9688 | no -- k >= m forces it |
| 6 | 3 | 2 | 729 | 352 | 0.4829 | 6.00 | 721 | 0.9890 | yes -- k < m |
| 6 | 3 | 3 | 729 | 0 | 0.0000 | 0.00 | 726 | 0.9959 | no -- k >= m forces it |
| 7 | 2 | 2 | 128 | 0 | 0.0000 | 0.00 | 126 | 0.9844 | no -- k >= m forces it |
| 7 | 3 | 2 | 2187 | 1200 | 0.5487 | 9.00 | 2178 | 0.9959 | yes -- k < m |
| 7 | 3 | 3 | 2187 | 0 | 0.0000 | 0.00 | 2184 | 0.9986 | no -- k >= m forces it |
| 8 | 2 | 2 | 256 | 0 | 0.0000 | 0.00 | 254 | 0.9922 | no -- k >= m forces it |
| 8 | 3 | 2 | 6561 | 3977 | 0.6062 | 12.00 | 6551 | 0.9985 | yes -- k < m |
| 8 | 3 | 3 | 6561 | 0 | 0.0000 | 0.00 | 6558 | 0.9995 | no -- k >= m forces it |

Two facts about this table matter more than its headline. First, the anti-rule control loses in
every cell (on at least 93.8 % of windows), so no cell is measuring nothing. Second, **only 4 of
the 12 cells can measure a gap at all.** When `k >= m` every rank owns a queue, the aligned map
is injective by construction, and the rule attains the floor without being right about anything;
the 8 such cells confirm the implementation and measure nothing, and they are counted as forced
here rather than folded into a win rate. A check in `emit_results.py` asserts that every one of
them reports exactly zero losses, so a cell that starts losing there is a code defect and not a
result.

In the 4 informative cells the aligned rule loses on 40.7 % to 60.6 % of windows, with a worst
cell ratio of 12 times the floor. Both numbers rise with `n` across those cells rather than
sitting still, so the table is read as the range it is: a single cell quoted alone would
misstate the phenomenon in either direction. The `k = 1` cells are reported as FORCED and never
as comparisons: one queue cannot choose, so it cannot be compared.

The table also settles a thing the floor alone cannot: **a zero floor does not buy a correct
mapping.** Of the 15208 windows whose restricted floor is already zero, the aligned rule still
loses on 2784 of them — up to 58.3 % within a single cell. Those losses are entirely avoidable:
nothing about the queue budget forces them, only the band map does. That is the separation this
paper exists to make, and it is why the floor and the deployed rule are both reported per cell
rather than pooled.

![The discipline gap as a distribution over windows. Each bar is the share of windows at a given
`required k - LDS`; the printed percentage is the share of windows on which the two disciplines
disagree. Redrawn from `results.json` by `make_figure.py`, which asserts the caption's claims as
invariants.](figures/discipline-gap.png)

## 10 Registered prior beliefs, and what happened to them

The priors below are quoted from the registration, which fixed them before the deciding runs and
which named `P1`, `P2` and `P3`. They are answered in that order, on the conditions the
registration itself stated — not on a convenient substitute, and not renumbered to fit the
results.

**Registered `P1` — zero inversions iff `k` is at least the window's longest strictly decreasing
subsequence. Status: confirmed, as the certificate it was registered to be.** The registration
declared this a proposition to verify rather than a finding, because it follows from Dilworth's
theorem, and said a violation would mean the model or the implementation was wrong. There is
none: `runs(p)` violates the threshold on 0 of 40296 (window, `k`) pairs, which is the S2
criterion met, and it certifies the model the way the brute-force cross-check certifies the
floor. Confirming a corollary is not a result, and the registration said so first, which is what
makes it safe to report plainly.

**What `P1` does *not* transfer to, and why this is not a prior that failed.** I inferred at
registration time — in prose, not as a registered prior — that because the partition bound holds
for any emulation, a strict-priority device would attain it too. That inference is **refuted**:
under the device's own dequeue discipline the exact requirement is `runs(p)`, which exceeds
`LDS` on 2422 of 5040 n = 7 windows. This is the paper's substantive result. It is reported here
rather than in the `P1` slot because the registration never claimed it: registering a corollary
as verified, and then discovering that the corollary does not carry the operational conclusion,
is a different event from a prior failing, and merging the two would let the paper claim a
refutation it did not register.

**Registered `P2` — the deployed rule exceeds the floor in the *majority* of windows whenever `2
<= k < LDS`, with a worst per-cell overshoot above `1.3x`. Status: confirmed, both limbs — and
only because the range the registration named was measured to its end.** On the registration's
own population, the windows with `k < LDS`, 2844 of 4712 windows lose: 60.4 %. The worst
per-cell ratio is 12.00 times the floor, far above the registered `1.3x`. So the deployed rule
does lose in the majority of windows in the class the registration nominated, and it loses by
more than the registration predicted.

That verdict is the second reading of this datum, not the first. The artifact originally stopped
at `n = 6`, where the same population gave a minority in every cell, and an earlier draft of
this section reported the frequency limb as **refuted**. Registered criterion S3 asks for every
cell to `n = 8` with the maximum taken over all cells rather than over a convenient subset, so
the cells were extended — and the verdict inverted. The share rises with `n` across the four
informative cells:

| n | m | k | windows with `k < LDS` | of those, the rule loses | share | worst ratio |
|---|---|---|---|---|---|---|
| 5 | 3 | 2 | 51 | 19 | 0.3725 | 4.00 |
| 6 | 3 | 2 | 233 | 112 | 0.4807 | 6.00 |
| 7 | 3 | 2 | 939 | 528 | 0.5623 | 9.00 |
| 8 | 3 | 2 | 3489 | 2185 | 0.6263 | 12.00 |

It crosses one half between `n = 6` and `n = 7` and reaches 62.6 % at `n = 8`. A study that
stopped where the enumeration was cheapest would have published the opposite conclusion from the
same model, which is why the registered range is reported rather than described as saturated.
The dependence on `n` is itself a result: the frequency of avoidable loss is not a property of
the rule alone, and a single-cell figure for it is a figure about a window length.

**Registered `P3` — the informative cells are exactly `2 <= k < LDS`, and the overshoot is not
monotone in `k`. Status: the first limb is refuted, the second is unresolved.** The first limb
fails on the half of it that says `k >= LDS` is *vacuous because both floor and rule are zero*:
the aligned rule loses on 2784 of the 15208 windows whose restricted floor is already zero, up
to 58.3 % in one cell (§9.5). A zero floor says the budget is enough; it does not say the band
map spends it, and the registration equated the two. The class that can register a loss is
therefore set by the band map's collisions, `k < m`, not by the `LDS` threshold the registration
nominated — which is why the 4 informative cells of §9.5 are chosen that way. Unlike `P2`, this
limb needed no wide `n` range to become visible: it was there at every `n` measured. The second
limb — non-monotonicity of the worst ratio in `k` — stays **unresolved, and not by choice**: the
reading that suggested it was taken against the free floor and against a band rule whose queue
priorities were misaligned by construction, so it is not evidence either way, and re-reading it
needs an aligned rule over a `k` range wider than the cells this artifact carries. It is
recorded as unresolved rather than dropped, because a prior that quietly disappears from the
record is worse than one reported as untested.

**The ties falsifier.** Before the tied-rank measurement we registered a numeric falsifier: if
the best candidate were exact on fewer than `99` % of tie-bearing windows *and* the two
disciplines required the same `k` on more than `50` % of windows, the direction was to be
**downgraded to a case study** scoped to distinct ranks. The first condition failed — `T3` is
exact — so the registered verdict is *continue*. The second condition is nevertheless true, and
is reported in §9.4 as prominently as the first, because a falsifier whose two limbs are quoted
together must have both limbs reported when only one of them fires.

## 11 Threats to validity

Read this as a list of what would make each claim false, not as a disclaimer.

**The statistic is classical.** `runs(p) = 1 + #{descents}` is not ours; it belongs to the
queue-and-stack sorting literature cited in §1, which we could not read. Our contribution is the
pairing of a statistic with a dequeue discipline, and a reader who finds that a cited work
already states the pairing is right, and that work is prior art for it. This is the largest
threat in the paper, and no amount of internal verification reduces it.

**The model has no deployment.** No trace, no implementation and no hardware is measured
anywhere. Every claim is about a model with an exact optimum. The claim that a deployed
emulation is short of it in the same way is *not* made, and would need a trace evaluation.

**No interleaved arrival.** Traffic is batch: every packet arrives, then dequeuing begins. Real
switches interleave, and the restricted floor is sensitive to interleaving while the free floor
is not. This is the boundary most likely to move the threshold, and it is untested.

**Range bounds, not noise bounds.** Distinct ranks: `n <= 7`. Ties: `n <= 6` with `m <= 4`. The
bound of 2 queues on the gap is a **measured maximum over those windows**, not a theorem;
nothing here forbids a larger gap at larger n, and the proof of `runs(p) >= LDS` bounds the
direction of the error, not its size.

**Two of six rule cells are informative.** §9.5 reports the 4 informative cells separately from
the 8 forced ones. A reader who takes the six-cell summary as a win rate is reading a number
that four of its cells cannot earn.

**A caution about the instruments themselves.** Both defects found in this study were found by
cross-checking two instruments, not by a guard. A guard whose answer is the same under the
correct and the incorrect reading cannot separate them: an early tie case returned zero under
both, and the defect in an inversion predicate survived it. The artifact carries hand-computable
witnesses for exactly this reason, and they are asserted before any aggregate is read.

## 12 Related work, and the specific difference in each case

Six comparisons, each with the difference stated rather than implied.

**Pratt, Even-Itai, Tarjan** [1] [2] [3]. They own the combinatorics: which permutations a
network of queues and stacks produces. This paper does not contest or extend that, and it did
not read their statements. The difference is the axis: they ask which permutations a bank can
produce, we ask what a statistic computed from observed traffic tells a designer about the bank
size she needs, and we show those answers depend on the dequeue discipline.

**SP-PIFO** [24]. It gives a mapping and an evaluation, so its queue count is a design choice
validated end-to-end. Ours is an exact floor for a given count, so the two are complements: our
floor says what their mapping loses before their evaluation measures it.

**Scale-up PIFO** [25]. It interleaves multiple priority queues to make a bank faster. We ask
how many queues the bank needs at all. A smaller bank is one way to spend less; ours is the
statement of how small it can be before the output changes.

**AnTiQ and hardware priority queues** [88] [87]. They price a single ordered queue in silicon
and are the reason emulation is needed. We price the number of unordered queues that replace it.

**Online packet scheduling with lookahead** [84]. It measures what a bounded lookahead buys an
online policy, as a competitive ratio. We compute an offline exact floor. A competitive ratio
against our floor is a natural follow-up, and this paper does not attempt it.

**Sorting with networks of stacks and queues** [73]. It studies the complexity of the sorting
problem those devices pose. We use the resulting statistic and add no complexity result.

## 13 Significance: whose decision changes

The community is switch and programmable-scheduler designers, and the belief that changes is a
specific one: **that the statistic which decides how many queues are needed is
discipline-independent.** It is not. A designer reading "`k >= LDS` suffices" from a
Dilworth-style analysis is reading a threshold for a dequeue discipline no switch implements,
and the error has a sign — the bank is under-provisioned, never over-provisioned.

Three decisions change. First, sizing: a designer now has a number per discipline instead of one
number, and can say what a given `k` is short of rather than only that it is short. Second,
evaluation: a paper that reports an emulation's fidelity against a free-merge bound is reporting
against the wrong bound, and can re-read its own numbers against the strict-priority floor.
Third, review: a reviewer who computes actual queue counts can now check whether an effect was
inflated, which is why §9.4 reports the frequency and the magnitude together and why the ties
result is given the same prominence as the distinct-rank one — the pairing is a real distinction
under distinct ranks and nearly vanishes under ties, and a paper that reported only the first
half would be selling the stronger half of a stratified result.

## 14 Conclusion

The number of priority queues a scheduler needs is a property of the traffic *and* of the
dequeue discipline. Under a strict-priority dequeue the exact requirement is `runs(p)`, the
number of maximal ascending runs of the inverse arrival order; it is exact on every one of 5904
enumerated distinct-rank windows, it dominates the longest decreasing subsequence, and the
dominance is a theorem rather than an enumeration. The default statistic is therefore not merely
inexact but *directional*: it understates, on 48.1 % of n = 7 windows, by at most 2 queues.
Under ties the statistic needs a minimisation over tie-breakings, and the discipline distinction
nearly disappears — 2.3 % of tie-bearing windows. The combinatorics is classical and is credited
as such; what is new is the pairing, and the measurement of how much the pairing is worth.

## 15 Reproducibility

The package is one command, offline, with no sampling and no random seeds:

```
./reproduce.sh
```

Its last line is `REPRODUCE: ALL GREEN (5 steps)` and its exit status is the number of failed
steps, so a failure accumulates rather than being masked by a later step. The five steps emit
`results.json` from the model, redraw the figure from `results.json`, recompute every stored
summary from the rows it summarises, check that the reference placement still resolves and still
matches its committed artifact, and check that this manuscript still matches what its generator
produces. Every artifact is expected to be reproduced byte for byte; `README.md` states the
environment, the tolerance and what is deliberately not covered.

Citation integrity is part of the package rather than of the prose: `reference-check.md`
records, for each of the 104 references, the DOI, the Crossref record it resolves to, and an
agreement score; seven entries carry an edition-year note rather than being smoothed over. Every
reference is cited in the body above, and `make_manuscript.py` refuses to write the paper if one
is not — a bibliography entry the body never cites is padding, and the generator treats it as a
failure rather than a style issue.

## References

[1] Pratt, V. R. Computing permutations with double-ended queues, parallel stacks and parallel queues. Proceedings of the fifth annual ACM symposium on Theory of computing - STOC '73, 1973. https://doi.org/10.1145/800125.804058.

[2] Even, S.; Itai, A. QUEUES, STACKS AND GRAPHS. Theory of Machines and Computations, 1971. https://doi.org/10.1016/b978-0-12-417750-5.50011-7.

[3] Tarjan, R. Sorting Using Networks of Queues and Stacks. Journal of the ACM, 1972. https://doi.org/10.1145/321694.321704.

[4] Elbediwy; Pontikakis; David; Savaria. A Hardware Architecture of a Dynamic Ranking Packet Scheduler for Programmable Network Devices. IEEE Access, 2023. https://doi.org/10.1109/access.2023.3286726.

[5] Jiang; Zhang; Liu; Zheng. A P4-Based Packet Scheduling Approach for Clustered Deep Packet Inspection Appliances. 2021 International Conference on Computer Communications and Networks (ICCCN), 2021. https://doi.org/10.1109/icccn52240.2021.9522193.

[6] Kang; Tian; Hu. A Programmable Packet Scheduling Method Based on Traffic Rate. 2024 IEEE 2nd International Conference on Control, Electronics and Computer Technology (ICCECT), 2024. https://doi.org/10.1109/iccect60629.2024.10545661.

[7] Chen; Tian; Zhang. AccelToR: Accelerating TCP for Circuit/Packet Hybrid Data Centers With Packet Scheduling. IEEE Transactions on Networking, 2025. https://doi.org/10.1109/ton.2025.3550902.

[8] Quan; Xu; Liu; Cheng; et al. AI-Driven Packet Forwarding With Programmable Data Plane: A Survey. IEEE Communications Surveys & Tutorials, 2023. https://doi.org/10.1109/comst.2022.3217613.

[9] Rajagopalan; Sivalingam; Shami; Lyonnais. ALADA: Packet-Level Analysis for Line Rate Anomaly Detection Using a Programmable Dataplane Switch. IEEE Open Journal of the Communications Society, 2026. https://doi.org/10.1109/ojcoms.2026.3686225.

[10] Li; Song; Zeng. An Adaptive Throughput-First Packet Scheduling Algorithm for DPDK-Based Packet Processing Systems. Future Internet, 2021. https://doi.org/10.3390/fi13030078.

[11] Saqib; Elbiaze; Glitho; Ghamri-Doudane. An Intelligent and Programmable Data Plane for QoS-Aware Packet Processing. IEEE Transactions on Machine Learning in Communications and Networking, 2024. https://doi.org/10.1109/tmlcn.2024.3475968.

[12] Guo; Sun; Hu; Zhang; et al. CIPO: Efficient, lightweight and programmable packet scheduling. Computer Networks, 2024. https://doi.org/10.1016/j.comnet.2024.110355.

[13] Cui; Zhang. D-PIFO: A Dynamic Priority Scheduling Algorithm for Performance-Critical Packets Based on the Programmable Data Plane. 2024 27th International Conference on Computer Supported Cooperative Work in Design (CSCWD), 2024. https://doi.org/10.1109/cscwd61410.2024.10580504.

[14] Wang; Liu; Zhang; Guo; et al. DDSPQ: Strict-Priority Queue Schedule for Multi-Tiered Service Accommodation in SD-WAN. 2025 10th International Conference on Computer and Communication System (ICCCS), 2025. https://doi.org/10.1109/icccs65393.2025.11069454.

[15] Hussain; Patetta; Rivalan. Demo: Programmable Packet Scheduling on FPGA-Based Switches. 2025 4th International Conference on 6G Networking (6GNet), 2025. https://doi.org/10.1109/6gnet68413.2025.11314135.

[16] Elbediwy; Pontikakis; Ghaffari; David; et al. DR-PIFO: A Dynamic Ranking Packet Scheduler Using a Push-In-First-Out Queue. IEEE Transactions on Network and Service Management, 2024. https://doi.org/10.1109/tnsm.2023.3304894.

[17] Yu; Ruepp; Berger. Enhanced first-in-first-out-based round-robin multicast scheduling algorithm for input-queued switches. IET Communications, 2011. https://doi.org/10.1049/iet-com.2010.0378.

[18] Mostafaei; Ezzati; Cuijpers; Schmid; et al. Exp-PIFO: Scalable and Efficient Programmable Packet Scheduling. Proceedings of the ACM on Networking, 2025. https://doi.org/10.1145/3749217.

[19] Liu; Gao; Chen; Chen; et al. FIPO: A Lightweight and Customized Software-Defined Programmable Packet Scheduling Primitive. IEEE Systems Journal, 2025. https://doi.org/10.1109/jsyst.2025.3567017.

[20] Zhang; Li; Li; Liu; et al. Lark: A Buffer-aware Building Block for Programmable Packet Scheduling in Datacenters. IEEE INFOCOM 2025 - IEEE Conference on Computer Communications, 2025. https://doi.org/10.1109/infocom55648.2025.11044448.

[21] Lv; Jiang; Yang. Making programmable packet scheduling time-sensitive with a FIFO queue. Journal of Cloud Computing, 2023. https://doi.org/10.1186/s13677-023-00518-3.

[22] Tsanikidis; Ghaderi. Near-Optimal Packet Scheduling in Multihop Networks with End-to-End Deadline Constraints. ACM SIGMETRICS Performance Evaluation Review, 2024. https://doi.org/10.1145/3673660.3655069.

[23] Sivaraman, A.; Subramanian, S.; Alizadeh, M.; Chole, S.; et al. Programmable Packet Scheduling at Line Rate. Proceedings of the 2016 ACM SIGCOMM Conference, 2016. https://doi.org/10.1145/2934872.2934899.

[24] Vass; Sarkadi; Retvari. Programmable Packet Scheduling With SP-PIFO: Theory, Algorithms and Evaluation. IEEE INFOCOM 2022 - IEEE Conference on Computer Communications Workshops (INFOCOM WKSHPS), 2022. https://doi.org/10.1109/infocomwkshps54753.2022.9798055.

[25] Mei; Chen; Chen; Chen; et al. Scale-up PIFO: Interleaving Multiple Priority Queues for High Speed Programmable Scheduling. Proceedings of the ACM SIGCOMM 2026 Conference, 2026. https://doi.org/10.1145/3789240.3829190.

[26] Vass. Spring: Theory and an Efficient Heuristic for Programmable Packet Scheduling with SP-PIFO. Infocommunications journal, 2025. https://doi.org/10.36244/icj.2025.3.1.

[27] Song; Hasan. Time-Aware Packet Forwarding in Programmable Data Planes. 2025 28th International Symposium on Real-Time Distributed Computing (ISORC), 2025. https://doi.org/10.1109/isorc65339.2025.00038.

[28] Xing; Qiu; Hsu; Sui; et al. Unleashing SmartNIC Packet Processing Performance in P4. Proceedings of the ACM SIGCOMM 2023 Conference, 2023. https://doi.org/10.1145/3603269.3604882.

[29] Zhang; Chen; Yao; Sun; et al. vPIFO: Virtualized Packet Scheduler for Programmable Hierarchical Scheduling in High-Speed Networks. Proceedings of the ACM SIGCOMM 2024 Conference, 2024. https://doi.org/10.1145/3651890.3672270.

[30] Heisswolf; Konig; Becker. A Scalable NoC Router Design Providing QoS Support Using Weighted Round Robin Scheduling. 2012 IEEE 10th International Symposium on Parallel and Distributed Processing with Applications, 2012. https://doi.org/10.1109/ispa.2012.93.

[31] Rahimi; Pournaghshband. An improvement mechanism for low priority traffic TCP performance in Strict Priority Queueing. 2016 International Conference on Computer Communication and Informatics (ICCCI), 2016. https://doi.org/10.1109/iccci.2016.7480023.

[32] Shortle; Fischer. Approximation for a two-class weighted fair queueing discipline. Performance Evaluation, 2010. https://doi.org/10.1016/j.peva.2010.05.004.

[33] Mukherjee; Kuri; Singh. Convexity and Optimization in Deficit Round Robin Scheduling for Delay-Constrained Systems. 2025 23rd International Symposium on Modeling and Optimization in Mobile, Ad Hoc, and Wireless Networks (WiOpt), 2025. https://doi.org/10.23919/wiopt66569.2025.11123403.

[34] Chang; Lee. Cycle time distribution and control for the Deficit Round Robin packet scheduler. 2012 International Conference on Computing, Networking and Communications (ICNC), 2012. https://doi.org/10.1109/iccnc.2012.6167459.

[35] Kubo; Okada; Oki. Delay Impact of Bursty Cross Traffic in Combined Input and Output Queued Switches Using Virtual Input Queueing Under Diverse Network and Traffic Conditions. IEEE Open Journal of the Communications Society, 2026. https://doi.org/10.1109/ojcoms.2026.3726416.

[36] Lin; Hamdi; Muppala. Designing Packet Buffers Using Random Round Robin. 2010 IEEE Global Telecommunications Conference GLOBECOM 2010, 2010. https://doi.org/10.1109/glocom.2010.5683309.

[37] Kang; Williams. Diffusion Approximation for an Input-queued Switch Operating under a Maximum Weight Matching Policy. Stochastic Systems, 2012. https://doi.org/10.1287/12-ssy061.

[38] Divanovic; Radonjic; Gardasevic; Radusinovic. Dynamic weighted round robin in crosspoint queued switch. 2013 21st Telecommunications Forum Telfor (TELFOR), 2013. https://doi.org/10.1109/telfor.2013.6716184.

[39] Sun; Li. Half-Draining Round Robin Matching for High Performance Input Queued Switches. 2019 IEEE/ACIS 18th International Conference on Computer and Information Science (ICIS), 2019. https://doi.org/10.1109/icis46139.2019.8940224.

[40] Huang; Huang. Heavy traffic analysis of approximate max-weight matching algorithms for input-queued switches. Performance Evaluation, 2020. https://doi.org/10.1016/j.peva.2020.102143.

[41] (no author field in the record). Implementation of Class-Based Low Latency Fair Queueing (CBLLFQ) Packet Scheduling Algorithm for HSDPA Core Network. KSII Transactions on Internet and Information Systems, 2020. https://doi.org/10.3837/tiis.2020.02.001.

[42] Assegie; Bizuneh, D. Improving network performance with an integrated priority queue and weighted fair queue scheduling. Indonesian Journal of Electrical Engineering and Computer Science, 2020. https://doi.org/10.11591/ijeecs.v19.i1.pp241-247.

[43] Xiao; Yeung. Iterative multicast scheduling algorithm for input-queued switch with variable packet size. 2017 IEEE 30th Canadian Conference on Electrical and Computer Engineering (CCECE), 2017. https://doi.org/10.1109/ccece.2017.7946605.

[44] Liao; Wu. Longest queue first in round-robin matching for input-queued switches. 2010 International Symposium On Information Theory & Its Applications, 2010. https://doi.org/10.1109/isita.2010.5648873.

[45] Lin; Rojas-Cessa. Module Matching Schemes for Input-Queued Clos-Network Packet Switches. IEEE Communications Letters, 2007. https://doi.org/10.1109/lcomm.2007.061617.

[46] Ghodsi; Sekar; Zaharia; Stoica. Multi-resource fair queueing for packet processing. ACM SIGCOMM Computer Communication Review, 2012. https://doi.org/10.1145/2377677.2377679.

[47] Gourgy; Szymanski; Down. On Tracking the Behavior of an Output-Queued Switch Using an Input-Queued Switch. IEEE/ACM Transactions on Networking, 2009. https://doi.org/10.1109/tnet.2009.2014948.

[48] Lesens; Cohen; Uçar. Orthogonal Matching Pursuit-Based Algorithms for the Birkhoff-Von Neumann Decomposition. 2024 32nd European Signal Processing Conference (EUSIPCO), 2024. https://doi.org/10.23919/eusipco63174.2024.10715087.

[49] Yu; Chen; Tian. OWFQ: Reducing Packet Drops for Approximate Weighted Fair Queueing with Calendar Queues. 2023 9th International Conference on Computer and Communications (ICCC), 2023. https://doi.org/10.1109/iccc59590.2023.10507624.

[50] Liu; Li. Packet Scheduling in High-speed Networks Using Improved Weighted Round Robin. Research Journal of Applied Sciences, Engineering and Technology, 2014. https://doi.org/10.19026/rjaset.7.498.

[51] Kitsuwan; Oki; Rojas-Cessa; Kishi. Performance analysis on dynamics of parallel iterative matching in an input-buffered switch. 2009 15th Asia-Pacific Conference on Communications, 2009. https://doi.org/10.1109/apcc.2009.5375476.

[52] Gong; Xu; Liu; Maguluri. QPS-r: A cost-effective iterative switching algorithm for input-queued switches. Performance Evaluation, 2021. https://doi.org/10.1016/j.peva.2021.102197.

[53] Jamali; Ghiasian. Randomised scheduling algorithm for virtual output queuing switch at the presence of non‐uniform traffic. IET Networks, 2019. https://doi.org/10.1049/iet-net.2018.5115.

[54] Dukes; Mullins. A Bump Statistic on Permutations Resulting from the Robinson–Schensted Correspondence. Annals of Combinatorics, 2024. https://doi.org/10.1007/s00026-024-00708-z.

[55] He. A central limit theorem for descents of a Mallows permutation and its inverse. Annales de l'Institut Henri Poincaré, Probabilités et Statistiques, 2022. https://doi.org/10.1214/21-aihp1167.

[56] Dilworth. A Decomposition Theorem for Partially Ordered Sets. Classic Papers in Combinatorics, 2009. https://doi.org/10.1007/978-0-8176-4842-8_10.

[57] F; S; M, A. A Generalization of Dilworth’s Decomposition Theorem for Partially Ordered Multisets. Anchor University Journal of Science and Technology, 2024. https://doi.org/10.4314/aujst.v5i1.6.

[58] Corwin. Commentary on “Longest increasing subsequences: from patience sorting to the Baik–Deift–Johansson theorem” by David Aldous and Persi Diaconis. Bulletin of the American Mathematical Society, 2018. https://doi.org/10.1090/bull/1623.

[59] Elizalde. Continued fractions for permutation statistics. Discrete Mathematics & Theoretical Computer Science, 2018. https://doi.org/10.23638/dmtcs-19-2-11.

[60] Kociumaka; Seddighin. Improved dynamic algorithms for longest increasing subsequence. Proceedings of the 53rd Annual ACM SIGACT Symposium on Theory of Computing, 2021. https://doi.org/10.1145/3406325.3451026.

[61] Mitzenmacher; Seddighin. Improved Sublinear Time Algorithm for Longest Increasing Subsequence. Proceedings of the 2021 ACM-SIAM Symposium on Discrete Algorithms (SODA), 2021. https://doi.org/10.1137/1.9781611976465.115.

[62] Jiang; Wang. Moderate deviations for the number of descents in a random permutation. Statistics & Probability Letters, 2025. https://doi.org/10.1016/j.spl.2024.110320.

[63] Cao; Huang; Su. Nearly Optimal Parallel Algorithms for Longest Increasing Subsequence. Proceedings of the 35th ACM Symposium on Parallelism in Algorithms and Architectures, 2023. https://doi.org/10.1145/3558481.3591078.

[64] Vaisman; Gertsbakh. Optimal balanced chain decomposition of partially ordered sets with applications to operating cost minimization in aircraft routing problems. Public Transport, 2022. https://doi.org/10.1007/s12469-022-00304-5.

[65] Bóna; DeJonge. Pattern Avoiding Permutations with a Unique Longest Increasing Subsequence. The Electronic Journal of Combinatorics, 2020. https://doi.org/10.37236/9506.

[66] Marciniak; Maślanka; Śniady. Poisson limit theorems for the Robinson–Schensted correspondence and for the multi-line Hammersley process. Advances in Applied Mathematics, 2023. https://doi.org/10.1016/j.aam.2022.102478.

[67] Fiorini; Rexhep. Poset Entropy Versus Number of Linear Extensions: The Width-2 Case. Order, 2015. https://doi.org/10.1007/s11083-015-9346-z.

[68] Axenovich; Winter. Poset Ramsey Number $$R(P,Q_n)$$. II. N-Shaped Poset. Order, 2024. https://doi.org/10.1007/s11083-024-09663-z.

[69] Bercu; Bonnefont; Fredes; Richou. Sharp analysis on the joint distribution of the number of descents and inverse descents in a random permutation. The Annals of Applied Probability, 2025. https://doi.org/10.1214/24-aap2138.

[70] Bercu; Bonnefont; Richou. Sharp large deviations and concentration inequalities for the number of descents in a random permutation. Journal of Applied Probability, 2024. https://doi.org/10.1017/jpr.2023.86.

[71] Kiyomi; Ono; Otachi; Schweitzer; et al. Space-Efficient Algorithms for Longest Increasing Subsequence. Theory of Computing Systems, 2019. https://doi.org/10.1007/s00224-018-09908-6.

[72] Zhao. Stack-sorting with stacks avoiding vincular patterns. Discrete Mathematics, 2026. https://doi.org/10.1016/j.disc.2025.114834.

[73] Felsner; Pergel. The Complexity of Sorting with Networks of Stacks and Queues. Lecture Notes in Computer Science, 2008. https://doi.org/10.1007/978-3-540-87744-8_35.

[74] Franz; Mulet. The longest increasing subsequence problem revisited. Communications in Theoretical Physics, 2026. https://doi.org/10.1088/1572-9494/ae9b87.

[75] (no author field in the record). The Robinson–Schensted–Knuth correspondence. The Student Mathematical Library, 2019. https://doi.org/10.1090/stml/091/08.

[76] Itskovich; Levit. What Do a Longest Increasing Subsequence and a Longest Decreasing Subsequence Know about Each Other?. Algorithms, 2019. https://doi.org/10.3390/a12110237.

[77] Itoh; Miyazaki; Satake. Competitive analysis for two variants of online metric matching problem. Discrete Mathematics, Algorithms and Applications, 2021. https://doi.org/10.1142/s1793830921501561.

[78] Barba; Bertazzi; Golden. Competitive Analysis of Algorithms for an Online Distribution Problem. Algorithms, 2024. https://doi.org/10.3390/a17060237.

[79] Dunke; Nickel. Correction to: Exact distributional analysis of online algorithms with lookahead. 4OR, 2021. https://doi.org/10.1007/s10288-021-00479-w.

[80] Dunke; Nickel. Exact distributional analysis of online algorithms with lookahead. 4OR, 2020. https://doi.org/10.1007/s10288-020-00442-1.

[81] Jiao; Yuan; Feng. Online Algorithms for Scheduling Unit Length Jobs on Unbounded Parallel-Batch Machines with Linearly Lookahead. Asia-Pacific Journal of Operational Research, 2019. https://doi.org/10.1142/s0217595919500246.

[82] Pinson; Spieksma. Online interval scheduling on two related machines: the power of lookahead. Journal of Combinatorial Optimization, 2019. https://doi.org/10.1007/s10878-019-00381-6.

[83] Chen; Zhang; Xu. Online machine minimization with lookahead. Journal of Combinatorial Optimization, 2020. https://doi.org/10.1007/s10878-020-00633-w.

[84] Böhm; Chrobak; Jeż; Li; et al. Online packet scheduling with bounded delay and lookahead. Theoretical Computer Science, 2019. https://doi.org/10.1016/j.tcs.2019.01.013.

[85] Lindermayr; Megow. Permutation Predictions for Non-Clairvoyant Scheduling. ACM Transactions on Parallel Computing, 2025. https://doi.org/10.1145/3711872.

[86] Zheng; Chen; Liu. Semi-online scheduling on two uniform parallel machines with initial lookahead. RAIRO - Operations Research, 2024. https://doi.org/10.1051/ro/2024042.

[87] Collinson; Bai; Sinnen. A Fast Scalable Hardware Priority Queue and Optimizations for Multi-Pushes. 2024 IEEE International Parallel and Distributed Processing Symposium Workshops (IPDPSW), 2024. https://doi.org/10.1109/ipdpsw63119.2024.00038.

[88] Nurmi; Lindgren; Szymkowiak; Hämäläinen. AnTiQ: A Hardware-Accelerated Priority Queue Design with Constant Time Arbitrary Element Removal. 2023 26th Euromicro Conference on Digital System Design (DSD), 2023. https://doi.org/10.1109/dsd60849.2023.00070.

[89] (no author field in the record). Binary Heaps and Priority Queues. Thinking about Programs, 2025. https://doi.org/10.1145/3731333.3731359.

[90] Grimes; Rodriguez; Hassan; Spear; et al. Brief Announcement: QPID: A Scalable, Strict Concurrent Priority Queue. Proceedings of the 38th ACM Symposium on Parallelism in Algorithms and Architectures, 2026. https://doi.org/10.1145/3816782.3819208.

[91] Michail. JHeaps: An open-source library of priority queues. SoftwareX, 2021. https://doi.org/10.1016/j.softx.2021.100869.

[92] Das; Pinotti, C. Parallel priority queues based on binomial heaps. Parallel Computing, 2000. https://doi.org/10.1016/s0167-8191(00)00064-8.

[93] Ioannou; Katevenis. Pipelined Heap (Priority Queue) Management for Advanced Scheduling in High-Speed Networks. IEEE/ACM Transactions on Networking, 2007. https://doi.org/10.1109/tnet.2007.892882.

[94] Brodal, S. Priority queues with decreasing keys. Theoretical Computer Science, 2024. https://doi.org/10.1016/j.tcs.2024.114563.

[95] Sanders. Randomized Priority Queues for Fast Parallel Access. Journal of Parallel and Distributed Computing, 1998. https://doi.org/10.1006/jpdc.1998.1429.

[96] Arvind; Rangan. Symmetric Min-Max heap: A simpler data structure for double-ended priority queue. Information Processing Letters, 1999. https://doi.org/10.1016/s0020-0190(99)00014-9.

[97] Carlsson. The deap—a double-ended heap to implement double-ended priority queues. Information Processing Letters, 1987. https://doi.org/10.1016/0020-0190(87)90033-0.

[98] Ding; Weiss. The relaxed min-max heap. Acta Informatica, 1993. https://doi.org/10.1007/bf01179371.

[99] (no author field in the record). RETRACTION : Design and Implementation of Network‐on‐chip Router Using Multi‐priority Based Iterative Round‐robin Matching With Slip. Transactions on Emerging Telecommunications Technologies, 2024. https://doi.org/10.1002/ett.5043.

[100] Mashreghi-Moghadam; Ould-Bachir; Savaria. A Templated VHDL Architecture for Terabit/s P4-programmable FPGA-based Packet Parsing. 2022 IEEE International Symposium on Circuits and Systems (ISCAS), 2022. https://doi.org/10.1109/iscas48785.2022.9937607.

[101] Magadum; Singh; Kushwaha. CT-PIFO: A Congruity Tree Based Packet Scheduler to Improve Flow Completion Time. 2025 34th International Conference on Computer Communications and Networks (ICCCN), 2025. https://doi.org/10.1109/icccn65249.2025.11134021.

[102] Hui; Yang; Wang. Leveraging SmartNIC for Ring AllReduce Offloading. 2024 IEEE International Symposium on Parallel and Distributed Processing with Applications (ISPA), 2024. https://doi.org/10.1109/ispa63168.2024.00030.

[103] Wang; Kong. Offloading IP Packet Fragmentation from CPU to SmartNIC Using P4. ICC 2026 - IEEE International Conference on Communications, 2026. https://doi.org/10.1109/icc59461.2026.11587563.

[104] Wang; Zhao; Zhang; Xu; et al. OXDP: Offloading XDP to SmartNIC for Accelerating Packet Processing. 2022 IEEE 28th International Conference on Parallel and Distributed Systems (ICPADS), 2023. https://doi.org/10.1109/icpads56603.2022.00103.

