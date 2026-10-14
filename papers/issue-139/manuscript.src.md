# Proving Is Not Paying: the Success-vs-Cost Frontier of Interdependent Proof Obligations

## Abstract

A verification project does not pay for a theorem; it pays for a **set** of interdependent proof
obligations under a budget. The field's benchmark culture reports **pass rate** — the fraction of
obligations a prover discharges at whatever sampling or search budget it takes — and that number is
silent about the object a project actually buys: the **success-vs-cost frontier**, the expected number
of obligations discharged as a function of the budget. This paper promotes the frontier to the
measured object and asks what sets its shape. We model obligation discharge as a declared stochastic
search over a **dependency DAG** with ground truth by construction: each obligation costs one unit per
attempt and succeeds with a declared probability, and discharging an obligation **raises** the success
probability of the obligations that depend on it (its assumptions are no longer open). Every reported
quantity is an exact count or an exact expectation over the model, and the run is byte-identical, so no
number is a timing. Three registered claims were put to the instrument, and the study returns a
**refutation, a theorem and a rule**. The registered concavity claim is **refuted as stated** — the
frontier is concave in only {{v1.p1.concave}} of {{v1.p1.cells}} measured cells — and is replaced by a
stronger object: an **exact one-directional theorem** (a non-increasing, easiest-first attempt order
always yields a concave frontier: {{v3.gviol}} violations over {{v3.perm}} exhaustively enumerated
permutations) whose converse is false ({{v3.conv}} exceptions) and which **fails only when the coupling
is on** ({{v3.bnd.viol}} of {{v3.bnd.cells}} genuinely fixed-order cells, with {{v3.expl}} of
{{v3.brk}} breakdowns attributed to the coupling under a fixed attempt order). The registered coupling
claim is **decided in the moderate regime and refuted in its added-value form**: coupling moves the
frontier ({{v1.p2.pos}} of {{v1.p2.cells}} coupled cells, up to +{{v1.p2.maxgain}} obligations against
the same schedule with its edges removed), but a permuted schedule is **not** a valid control — under
zero coupling a permutation already moves the frontier by {{v0.order.eff}} — so the permuted-schedule
"coupling gain" is a confounded quantity. The practical deliverable is a **budget-sizing rule**: a
budget read off a pass-rate table **under-budgets** the frontier in {{v2.sz.under}} of {{v2.plan.cells}}
cells ({{v2.sz.pct}}%), by up to {{v2.sz.worst}}x. The design rule the measurement supports is that a
verification budget must be sized from the frontier and the DAG, never from a pass-rate table.

**Contribution level: `theory+empirics`.** A declared stochastic model with a closed-form anchor, an
exact instrument with ground truth by construction over a declared grid, an exhaustive theorem, and
explicit baselines (four schedules — difficulty-greedy, assumptions-first, a fixed order and a permuted
placebo — a zero-coupling control and a closed-form oracle).

## 1. Introduction

A verification engineer is asked a procurement question: **how much budget does this obligation set
need?** The literature answers a different question — how often does the prover succeed — and the two
are not interchangeable. A pass rate is a point on a curve that has been collapsed to a scalar by
forgetting the budget at which it was taken. Two obligation sets can have the same multiset of
per-obligation difficulties and different dependency structure, reach the same pass rate at one budget
and different success fractions at the next.

The field itself names the gap. *Cost-Efficient Theorem Proving via Agent Orchestration in Program
Verification* {ref:2610.09681} states, verbatim, that "Almost all existing provers, however, pursue
pass rates alone at whatever sampling or search budget it takes, and overlook the success-vs-cost
frontier; yet real software often carries hundreds of interdependent proof obligations, so what matters
at scale is not whether one theorem can be proved, but how many can be proved economically." That is
the gap in one sentence, written by the field — and the paper answers it with a **system** (a
metalevel scheduler) rather than a **law**. It does not characterize the frontier, does not separate
coupling from marginal difficulty, and reports no operating characteristic a planner could size
against.

This paper takes the sentence seriously and asks the measurement question underneath it. We declare a
model in which the mechanism the field's systems exploit — *discharging an obligation makes its
dependents cheaper* — is an explicit parameter, and we measure the frontier exactly rather than
approximately.

**Three registered claims, and what the instrument did with them.** The priors were registered before
the deciding runs, and §4 reports each one against its outcome. In one paragraph: the frontier was
claimed to be **concave** (**refuted as stated**), the budget-to-target relation was claimed to be
**superlinear** (**confirmed**), the frontier's shape was claimed to be set by **coupling rather than
marginal difficulty** (**decided in the moderate regime, refuted in its added-value form**), and a
coupling-aware schedule was claimed to beat a difficulty-greedy one at **every** budget (**refuted as
stated** — the two schedules coincide wherever they select the same obligation, and the coupling-aware
schedule is *worse* on a hard-root family).

**What replaces the refuted claims.** The refutation of concavity is not the end of the story, and the
paper's central result is the object that replaces it. We isolate the two directions the earlier
statistic had conflated and test them **exhaustively** over the entire permutation group at n = 5, 6
and 7 ({{v3.perm}} permutations):

> **Law 1' (the guarantee, exact).** If the attempt order is non-increasing in difficulty
> (easiest-first), the frontier is concave. **{{v3.gviol}} violations in {{v3.perm}} permutations.**
> The converse fails {{v3.conv}} times: concavity does not require the order.
>
> **Corollary (the boundary).** The guarantee is a **`c` = 0 theorem**: {{v3.bnd.viol}} of
> {{v3.bnd.cells}} genuinely fixed-order cells violate it once the coupling is on, and
> {{v3.expl}} of {{v3.brk}} breakdowns are attributed to the coupling with the attempt order held
> fixed (defect exactly 0 with the coupling switched off).

> **Law 2 (the sizing rule, the practical deliverable).** The budget a pass-rate table implies — the
> sum of the cheapest independent expected costs — **under-budgets** the frontier in {{v2.sz.under}} of
> {{v2.plan.cells}} cells ({{v2.sz.pct}}%), and its worst cell is off by **{{v2.sz.worst}}x**. The error
> is worst in the low-target regime, where budgets are usually set.

**Who cares.** (a) Teams applying verification to machine-generated code, who must decide how large a
proof/sampling budget to buy and are currently told a pass rate. (b) The 2026 agentic-proving wave,
which needs a target quantity other than a rate to optimize. (c) Benchmark authors, because the
frontier is the comparable quantity across provers while a pass rate at one budget is not. **The
changed decision:** a planner who sizes a budget from "our prover proves 78 % of obligations" is sizing
from a quantity the measurement says is systematically optimistic; the decision changes to sizing from
the frontier of the actual DAG, and to reading the schedule as part of the budget.

## 2. Related work, and the specific difference from each

The reference list carries this paper's field, and every entry states its difference in one line. This
section states the differences that decide the argument, work by work.

**The paper that names the gap.** {ref:2610.09681} states the pass-rate-versus-frontier critique in one
sentence and answers it with a metalevel scheduler. **The specific difference:** we do not build a
scheduler; we *characterize the object the scheduler is optimizing*. Where that work reports its
scheduler's rate gains without a frontier, we report the frontier's closed form at two obligations, its
exact one-directional theorem at zero coupling, and the location of that theorem's failure — so its
scheduler's gain is the quantity this paper measures and bounds, and our result reframes it: a schedule
that reorders away from difficulty order buys coupling at the cost of convexity (Law 1').

**Adaptive cost-aware proof search.** {ref:2610.11862} makes the search objective cost-aware over
AND/OR proof graphs, improving proof quality after a correct proof is found. **The specific
difference:** its objective is a *per-proof* quality/cost trade-off on a single goal; ours is the
*aggregate* success-vs-cost frontier of a coupled obligation **set**, where the object of interest is
how many obligations are discharged, not how cheap any one proof is. The coupling in our model is the
residue of exactly the dependency structure an AND/OR graph encodes, so the two are complementary
rather than competing: our frontier is the quantity a portfolio of such searches would be sized
against.

**Cost-aware and budget-aware proving.** A body of work treats proving as a resource-allocation
problem — cost-aware proof search, budgeted premise selection, effort control, and cost models for
neural provers {ref:1809.05959, 10.1007/s10817-020-09580-x, 2305.02521, 2505.12031, 2507.16331,
2508.15878, 2602.10512, 2604.23002, 2605.13616, 2606.04883, 2606.22063, 2607.04631, 2607.26306,
2608.04886, 2608.12375, 2609.39544}. **The specific difference:** this literature models the *price* of
a discharge (a cost distribution, a learned predictor, an allocation rule) and evaluates it by rate or
by total cost; we hold the price structure fixed at the simplest possible form — one unit per attempt,
a declared success probability — and vary only the **dependency structure**, precisely so that the
frontier's shape is attributable to the structure rather than to the price model. Our contribution to
this literature is the object it would need to be evaluated against: the frontier, and the place where
the easy formula for it fails.

**Scheduling, portfolio and search control in deduction.** Scheduling and portfolio selection over
tactics and provers, and the search-control literature around them, are the natural home of a claim
about attempt order {ref:10.1007/s10817-013-9286-5, 1106.1372, 1509.03534, 1607.07797, 1909.09137,
2412.20735, 2502.03438, 2509.06493, 2601.06795, 2605.27485, 2608.28639, 2610.08319, cs/0701184}.
**The specific difference:** that literature asks which tactic or prover to run next and scores the
choice by problems solved; we ask what an *order* does to the *aggregate frontier*, and we find that
the answer is a theorem at zero coupling and a located failure with coupling. Concretely: the
coupling-aware (assumptions-first) schedule a portfolio intuition recommends is **worse** than
difficulty-greedy on a hard-root family by up to {{v0.p3.neg}} obligations, and the two schedules
**coincide** on {{v1.p3.ident}} of {{v1.p3.cells}} cells.

**Verification systems and proof assistants.** The application setting is the large family of
interactive and automated verification systems and their dependency structure — proof assistants, SMT
solvers, deductive verifiers, refinement and separation-logic toolchains, and the automation built on
them {ref:0907.1357, 10.1007/978-3-540-78800-3_24, 10.1007/978-3-642-17511-4_20,
10.1007/978-3-642-37036-6_8, 10.1007/s10817-009-9155-4, 10.1145/1629575.1629596, 1508.03894, 1702.01332,
1704.07935, 1707.02115, 1811.10814, 1811.10818, 1905.09381, 1908.01979, 2002.00423, 2003.07959,
2007.02559, 2008.10061, 2010.07253, 2211.10675, 2309.15806, 2401.02950, 2401.14320, 2406.17762,
2407.00695, 2410.19940, 2410.22419, 2411.15143, 2412.10657, 2501.17766, 2503.03205, 2503.09730,
2504.02246, 2504.06122, 2504.07642, 2504.21230, 2505.10328, 2505.10962, 2505.13454, 2505.15959,
2505.24230, 2506.07047, 2506.11487, 2506.22005, 2507.02726, 2507.15225, 2508.02733, 2509.22819,
2512.15816, 2512.24594, 2601.15737, 2603.19329, 2603.24465, 2604.03789, 2604.18587, 2604.24354,
2605.20120, 2605.21385, 2605.22257, 2605.22763, 2605.29955, 2606.03743, 2606.11430, 2606.19315,
2606.20740, 2606.21867, 2606.26442, 2608.18084, 2609.24252, 2609.25575, 2610.11605}. **The specific
difference:** these works report what a system proves and at what cost in aggregate; none reports the
frontier of a *coupled obligation set* as a function of its dependency structure. The coupled set is
exactly the object a large verification campaign holds — hundreds of obligations that share
assumptions — and it is the object their aggregate statistics average away.

**Benchmarks, evaluation and measurement methodology.** A rate is only as good as the benchmark that
produced it, and the measurement-methodology literature is where the rate currency is defended
{ref:2109.00110, 2403.04017, 2403.12627, 2406.11915, 2502.17840, 2505.04528, 2505.12680, 2508.18798,
2512.18256, 2602.18307, 2604.23698, 2605.10141, 2605.17255}. **The specific difference:** we do not
propose a benchmark, we propose a *different measurement* — the frontier, which is comparable across
provers at every budget simultaneously, where a rate at one budget is comparable only to a rate taken
at the same one. §6 states what the frontier does not capture.

**The theory of dependent search processes.** The frontier's shape is a question about a dependent
search process, and the closest theory is the literature on dependent and adaptive search, on
completion times of sequences of searches, and on the value of information about dependencies
{ref:1210.6857, 1403.2628, 1508.06827, 1804.02503, 1901.05456, 1905.10501, 2010.10296, 2103.02209,
2106.02550, 2207.08775, 2211.10219, 2301.13867, 2309.12711, 2402.08957, 2405.14414, 2406.18964,
2408.14017, 2410.15748, 2410.23493, 2411.10393, 2412.16058, 2501.17493, 2502.04671, 2502.19963,
2507.06804, 2507.20199, 2509.16237, 2603.29088, 2608.13757, 2608.21356}. **The specific difference:**
these give asymptotic or approximation results for adaptive processes; we give an *exact* finite-size
result — a closed form at two obligations and an exhaustively verified one-directional theorem at
n <= 7 — and, more importantly, we locate where the clean result *fails* (the coupling) rather than
assuming it extends.

**The 2026 agentic-proving wave.** The setting this question comes from is the recent wave of learned,
agentic and LLM-driven theorem proving and program verification, where a prover is asked to discharge
many obligations under a compute budget {ref:1410.5467, 1811.00796, 1903.03182, 1904.03241, 1907.07794,
1910.11797, 1911.02065, 2102.06203, 2102.09756, 2109.00542, 2210.03590, 2212.08578, 2306.15626,
2310.04353, 2311.03739, 2311.03755, 2312.14188, 2312.17353, 2401.00963, 2404.00762, 2404.09939,
2404.12534, 2405.02580, 2405.14333, 2405.17216, 2406.06555, 2406.07222, 2407.14521, 2410.10135,
2411.01829, 2411.13627, 2412.08805, 2412.10483, 2501.18310, 2502.05344, 2502.15795, 2502.17925,
2505.02735, 2505.03171, 2505.05758, 2505.15740, 2505.22846, 2505.23311, 2505.23754, 2506.04592,
2506.19923, 2506.22370, 2507.03659, 2507.07399, 2507.14330, 2507.18885, 2508.18914, 2508.20340,
2509.06809, 2509.23061, 2509.25197, 2510.02335, 2510.06857, 2510.08988, 2510.10131, 2510.11225,
2510.12787, 2510.15981, 2510.17919, 2510.24592, 2510.25427, 2511.00125, 2511.10356, 2511.11990,
2511.17330, 2511.18760, 2512.00997, 2512.23511, 2512.24379, 2601.14027, 2601.18944, 2601.19747,
2601.20055, 2602.00715, 2602.08384, 2602.16554, 2602.22631, 2602.24273, 2603.02895, 2603.12744,
2603.14628, 2603.18334, 2603.19828, 2603.21065, 2603.22114, 2604.01483, 2604.07455, 2604.08388,
2604.10761, 2604.15839, 2604.19000, 2604.19558, 2605.01394, 2605.11905, 2605.14061, 2605.15445,
2605.17475, 2605.22885, 2605.23772, 2605.26457, 2605.27531, 2605.30914, 2606.03303, 2606.08728,
2606.13782, 2606.14357, 2606.16886, 2606.20068, 2606.27926, 2606.31134, 2606.32007, 2607.06820,
2607.07779, 2607.09217, 2607.11307, 2607.14082, 2607.16372, 2607.21533, 2607.27259, 2607.28877,
2608.00894, 2608.02295, 2608.05420, 2608.12629, 2608.13077, 2608.21516, 2608.25220, 2608.29270,
2609.19391, 2609.22347, 2609.27162, 2609.37203, 2610.00885, 2610.02792, 10.1145/3611643.3616243,
10.52202/068431-1910}. **The specific difference:** these systems report rates at whatever budget they
chose; we provide the curve they are points on, and a rule for sizing the budget they are evaluated at.
The measurement we report is the one their own tables silently assume.

**Classical foundations of the model.** The model's ingredients — a sequence of independent searches
with success probabilities, and the completion time of the k-th success — are classical
{ref:10.1007/978-1-4612-6315-9_9, 10.1145/357073.357079}, and this paper is stated *against* them rather
than as a new stochastic model. **The specific difference:** the classical results are for *independent*
searches, which in our terms is the `c` = 0 control; the paper's content is entirely in what the
coupling (`c` > 0) does to those results, and in the theorem that does not survive it (exactly:
{{v3.bnd.viol}} of {{v3.bnd.cells}} fixed-order cells fail it).

## 3. The model and the exact instrument

### 3.1 The model

An obligation set is a DAG `(V, E)`. Obligation `j` has a standalone success probability `p_j`. One
attempt costs one budget unit and discharges `j` with probability `p_j` while no parent of `j` is
discharged. **Coupling:** if at least one parent of `j` is discharged, then `p_j -> min(1, p_j + c)`;
`c` is the coupling parameter, and `c` = 0 is the uncoupled control. A **schedule** is any
deterministic map from the discharged set to the obligation attempted next. The **frontier** is
`F(B) = E[number of discharged obligations after B attempts]`.

`F` is computed by **backward induction** over the discharged sets and the budget. Under a fixed order
the state is only *(how many done, attempts used)*, so the whole permutation group is affordable; under
a state-dependent schedule the state is the discharged set itself, so the `2^n` sets are enumerated.
Every reported quantity is therefore an **exact count or an exact expectation**, not a simulation
estimate. Where a state space would not close, the instrument falls back to a seeded exact-expectation
Monte Carlo read ({{v0.trials}} trials at seed {{v0.seed}}) reported beside the exact value; its maximum
absolute error at `N` and at `4N` trials falls as the trial count quadruples, as an independent reading
must.

The schedules are: **difficulty-greedy** (maximum current discharge probability — the obvious rule),
**assumptions-first** (maximum dependent cone, tie-broken on probability — the coupling-aware rule), a
**fixed order** (the same order at every state, which is what makes the exhaustive test possible), and
a **permuted placebo**.

### 3.2 The instrument, and the checks that could have failed it

The zero-coupling anchor is the ground truth the instrument is checked against: an uncoupled set is a
sum of independent geometric searches, whose frontier is exactly `sum_{k>=1} P(sum_{i<=k} G_i <= B)`.
The dynamic program reproduces it to machine precision over {{v1.cert.cells}} anchor cells, maximum
absolute difference **{{v1.cert.err}}**. Four further checks fired clean: the frontier at `c` = 0 equals
the uncoupled closed form; the coupling gain at `c` = 0 is exactly {{v1.p2.c0}}; the permutation's
effect at `c` = 0 is the measured {{v0.order.eff}} and **not** zero; and a re-run is bit-identical.

### 3.3 The grid

The measured grid is {{v0.cases}} fully reported exact cases plus a scaled grid at **n = {{v1.n}}**
obligations: {{v1.graphs}} DAG families (a chain, a tree, a layered graph, Erdős–Rényi graphs at two
densities, a hub-and-spoke family, and an empty graph as the control), {{v1.diffs}} difficulty
distributions (uniform, easy, hard-root, bimodal, Zipf), {{v1.cs}} coupling levels
(`c` in {0, 0.15, 0.35, 0.6}), {{v1.scheds}} schedules and a budget sweep to `B` = {{v1.Bmax}}, at seed
{{v1.seed}}. The empty graph is the control: it carries no edges, so a schedule effect measured on it
is an ordering effect with no coupling under test. **{{v1.ctrl.excl}} control cells are excluded from
every treatment count**, and each count below states its denominator.

**The delivered schedule set, and the registration's baseline list.** The four schedules above are the
three rules of §3.1 — difficulty-greedy, assumptions-first and a fixed order — plus the seeded
**permuted placebo**, and the registration's list named two rules the instrument does not carry: a
**random** schedule and a **breadth-first** order. Each is absent for a reason the model itself gives.
A *random* schedule is a distribution over maps, not the single deterministic map §3.1 defines a
schedule to be, so it has no frontier to enumerate exactly and every cell would become a Monte Carlo
read; the ordering it was meant to control is carried instead by the **seeded permuted placebo**, which
is deterministic and therefore exactly enumerable, and §5.2 shows that placebo is itself the wrong
control for the coupling — a finding about the registered design, not a gap in it. A *breadth-first*
order is one specific topological order applied at every state, i.e. a member of the delivered
**fixed-order** family, not a distinct rule. No result reported for P2 or P3 rests on either dropped
baseline: P2's coupling effect is the **same schedule on the graph with its edges removed** (§5.2), and
P3 compares the two state-dependent rules (difficulty-greedy against assumptions-first) with that same
delivered placebo as its control — every quantity those two priors are decided on comes from one of the
four schedules that were run.

## 4. Registered prior beliefs, and what the study found

The priors below were registered before the deciding runs, and each is reported against its measured
outcome. A prior that follows from a definition is not a prior, so each is stated in the form the
instrument could refute.

| Registered prior | Outcome |
|---|---|
| **P1a — the frontier is strictly concave in the budget**, on every declared family | **REFUTED as stated.** {{v1.p1.concave}} of {{v1.p1.cells}} cells are concave; the worst concavity defect is {{v1.p1.defect}}. Replaced by Law 1' (§5.4–5.5), which is exact. |
| **P1b — the target budget is superlinear in the target fraction** (registered: a factor >= 1.5 from a 0.5 to a 0.9 target) | **CONFIRMED.** The ratio of the budget at a 0.9 target to the budget at a 0.5 target is >= {{v1.p1.rmin}} in **{{v1.p1.rge15}} of {{v1.p1.cells}}** cells, maximum {{v1.p1.rmax}}. |
| **P2 — the frontier is set by coupling, not by marginal difficulty** (registered: a matched-pairs gap > 0.05 in success fraction at a declared mid budget) | **DECIDED in the moderate regime; REFUTED in its added-value form.** The coupling does move the frontier ({{v1.p2.pos}} of {{v1.p2.cells}} coupled cells, up to +{{v1.p2.maxgain}} obligations against the same schedule with its edges removed), but the registered control — a permuted schedule — is **not null**: a permutation alone moves the zero-coupling frontier by {{v0.order.eff}}. The "coupling gain" of a permuted schedule therefore measures an ordering effect and not the coupling (§5.2). |
| **P3 — a coupling-aware schedule beats difficulty-greedy at every budget, and the permutation shows no gain** | **REFUTED as stated, in both directions.** The two schedules coincide on {{v1.p3.ident}} of {{v1.p3.cells}} cells (gain exactly {{v1.p3.control}}); the coupling-aware schedule is *worse* on a hard-root family by up to {{v0.p3.neg}} obligations at `B` = 4; and the permutation control is the confounded quantity P2 already flagged. No cell has the coupling-aware schedule better at every budget ({{v1.p3.pos}} sign-stable-positive cells, {{v1.p3.signchg}} sign-changing). |

**Registered success criteria, reported as met or unmet.** (i) byte-identical reproduction and exact
quantities — **met** (§7). (ii) per-cell concavity and target-budget reported, with a failure reported
as a finding rather than tuned away — **met**, and the failure is the paper's central object. (iii) the
matched-pairs gap reported with its interval over >= 5 seeds and the zero-coupling anchor asserted —
**met**, with the caveat that the registered control was mis-specified and is reported as such.
(iv) the two-sided schedule comparison — **unmet in the registered form**, because the placebo half of
the test is invalid by measurement; the valid control (same schedule, edges removed, or `c` = 0) is
substituted and stated. (v) every rate states its eligible-subset denominator and no `0/0` cell is
written as a rate — **met** (no cell in this paper has an empty denominator; all statistics are
computed over non-empty sets, and the control cells are excluded and counted).

## 5. Results

### 5.1 The coupling's value is a property of the (schedule, DAG) pair

The model's central mechanism — a discharged assumption makes its dependents cheaper — does not
monotonically help, and the counter-example is *derivable* rather than observed. On the hard-root
family (`p` = 0.15 at the root, 0.6 at the three children), difficulty-greedy always attempts the
highest-probability undischarged obligation, so it discharges the three easy children before it would
ever spend an attempt on the root. The root is never discharged, the boost never activates, and the
edges carry **exactly** zero value at every budget. A schedule that does prioritise the dependent cone
(*assumptions-first*) activates the coupling and is **worse** by {{v0.p3.neg}} obligations at `B` = 4:
the budget spent on the hard assumption starves the easy set, and the deficit decays with the budget but
never turns positive on this family. On the uniform chain the same comparison gives the largest
coupling gain in the study, **+{{v0.gain.max}}** at `B` = {{v0.gain.atB}}.

So "coupling helps" is false as a general statement. The sign of the coupling's value is a property of
the **(schedule, DAG) pair**, and the effect lives in the *middle* of the budget range: on the chain the
gain rises to +{{v0.gain.max}} at `B` = {{v0.gain.atB}}, then decays to a few thousandths by the end of
the sweep (which runs to `B` = {{v0.Bmax}}). A single mid-budget cell would have reported the answer; the *maximum over a budget sweep* is
the quantity to register, and a paper that reported one budget would have reported either the whole
effect or none of it.

{{fig1}}

### 5.2 The permuted placebo is not a control

The registration's control was a permuted schedule: if the coupling-aware order's gain were real, a
random permutation should show none. It does not hold. On the exact cases, the permutation's effect on
the **zero-coupling** frontier reaches {{v0.order.eff}} (hard-root family, `B` = 4) with no graph at
all, because the completion time of the k-th obligation depends on the order in which the geometric
searches are concatenated. The permutation therefore confounds the ordering effect with the coupling
effect, and the "coupling gain" a permuted schedule reports — up to {{v0.placebo.eff}} on these cases —
is not the coupling.

**The control that is null by construction** is the same schedule on the graph with its edges removed,
which is the denominator of every coupling gain reported here, or the same schedule at `c` = 0 (where
the gain is exactly {{v1.p2.c0}}). This is a defect of the *registered design*, found by the
instrument, and it is reported as one: criterion (iv) is unmet in its stated form (§4). The general form
of the lesson is that a control must be null **under the null hypothesis it is meant to exclude** — a
randomised schedule is not, because the quantity it randomises (the attempt order) is itself a
first-order effect.

### 5.3 The concavity prior is refuted; the superlinearity prior is exact

Across the `n` = {{v1.n}} grid, the frontier is concave in only {{v1.p1.concave}} of
{{v1.p1.cells}} cells, and the defect grows with the coupling: the count of concave cells falls from
{{v1.c0.conc}} of {{v1.c0.cells}} at `c` = 0 to {{v1.c6.conc}} of {{v1.c0.cells}} at `c` = 0.6, the
median defect rising from {{v1.c0.dmed}} to {{v1.c6.dmed}}, and the worst cell reaching
{{v1.c6.dmax}}.

The registered concavity claim is refuted, and — this is the paper's pivot — the refutation is
*informative*. An earlier pass over the same grid reported the n-obligation law as an **agreement
rate** ("the induced order is non-increasing" agrees with "the frontier is concave" in 99.3 % of
uncoupled cells), and that statistic was averaging **an exact law with a false converse** (§5.5). The
agreement rate was a statistic that hid the structure it was supposed to measure. Separating the two
directions is what turns a refuted prior into a theorem.

The other half of P1 needs no replacement, because it came out exact. The ratio of the budget needed to
reach a 0.9 success fraction to the budget needed for 0.5 is at least {{v1.p1.rmin}} and at most
{{v1.p1.rmax}} in **every** one of the {{v1.p1.rge15}} cells — the budget is superlinear in the target
everywhere, with no exceptions and no counter-example to report.

{{fig2}}

### 5.4 Law 1: at two obligations, the law is exact — and a derivation was wrong

For **two** obligations attempted in a fixed order the frontier has a closed form (a sum of two
geometric searches; the marginal is `delta(B) = A q1^(B-1) + C q2^(B-1)` with `qi = 1 - pi`). Measuring
it over a **{{v2.law.cells}}-cell** grid of `(p1, p2)` — {{v2.law.convex}} of which are convex
somewhere — gives:

> **Law 1 (n = 2).** The frontier is convex somewhere **iff the second-attempted obligation is the
> harder one** (`p2 > p1`). Agreement: **{{v2.law.p2gtp1}} %** (1600/1600 cells).

Equivalently, the easiest-first (difficulty-greedy) rule is exactly the rule that preserves concavity
at n = 2, which is the seed of the n-form in §5.5.

**A hand-derived rule that was wrong, and is recorded as such.** Before measuring, we derived the
condition "the coefficient on the faster-decaying exponential is negative" as the necessary condition.
It agrees with the measured convex region in **{{v2.law.hand}} %** of cells — neither necessary nor
sufficient. The measured law is *simpler* than the derivation. It stays in the record because a
derivation that disagrees with its own measurement is evidence about the derivation (§6).

{{fig3}}

### 5.5 Law 1': the n-form is an exact one-directional theorem, and it is a `c` = 0 theorem

The n-obligation form was stated as a biconditional and measured as an agreement rate. Tested
**exhaustively** — every distinct permutation at `n` = 5, 6 and 7, over six difficulty vectors
(uniform; a wide zigzag; hard-first; bimodal; exact ties; near-ties differing by 2e-7) — the two
directions separate cleanly:

> **GUARANTEE** — a non-increasing (easiest-first) order yields a concave frontier:
> **{{v3.gviol}} violations in {{v3.perm}} permutations**, for every difficulty vector and every size.
>
> **CONVERSE** — a concave frontier requires a non-increasing order: **false**,
> **{{v3.conv}} exceptions** (about 10.5 %), and the exceptions are not small perturbations — the
> largest late rise inside a concave frontier exceeds 0.5.

So non-increasing is **sufficient and not necessary**, and the sufficient direction is **exact**. The
agreement rate of the earlier pass was, arithmetically, the blend of an exact law with a converse that
fails one time in ten.

**Why it breaks when the coupling is on: the coupling, not the order.** First, for every grid cell
whose *empty-set* order is non-increasing yet whose frontier is convex ({{v3.brk}} cells), recompute the
frontier with **the same attempt order and the coupling switched off**: in **{{v3.expl}} of
{{v3.brk}}** the uncoupled defect is **exactly 0**. The order is not what breaks the guarantee. Second,
test a **genuinely fixed** order *with* coupling (still exact: a fixed order's discharged set is a
prefix of the order, so the boost is a function of the step index alone) — the guarantee **fails in
{{v3.bnd.viol}} of {{v3.bnd.cells}}** cells. Hence:

> **Corollary.** The concavity guarantee is a **`c` = 0 theorem**. Coupling — the model's central
> feature, and the mechanism the field's systems exploit — is exactly what destroys it.

This is the paper's sharpest result and its most transferable one: the clean rule a portfolio intuition
would reach for (order by difficulty, and the frontier behaves) is *true* precisely in the regime where
the interesting mechanism is absent.

{{fig4}}

{{fig5}}

### 5.6 Law 2: the pass-rate budget rule under-budgets (the practical deliverable)

A planner is given `(graph, difficulties, c, target)` and asked for a budget. The frontier gives one:
the smallest `B` with `F(B) >= t * n`. The **pass-rate rule** gives another: a table says "our prover
discharges `t` of the obligations", and the implied budget is the sum of the `ceil(t * n)` cheapest
independent expected costs `1/p_i` — the most favourable reading, with the coupling already credited.

> **Law 2.** Over {{v2.plan.cells}} cells the pass-rate rule **under-budgets in {{v2.sz.under}}** of them
> (**{{v2.sz.pct}} %**), and its worst cell is short by **{{v2.sz.worst}}x** (it quotes 4.87 units
> where the frontier needs 24). The median ratio is {{v2.sz.med}}.

The error is worst exactly where budgets are usually set. At a 0.5 target it is short in
{{v2.sz.t50.under}} of {{v2.sz.t50.n}} cells; at a 0.9 target it is still short in
{{v2.sz.t90.under}} of {{v2.sz.t90.n}}. The pass-rate view is *systematically* optimistic, and
optimistic in the direction that costs a project its deadline: it buys less budget than the frontier
needs.

{{fig6}}

## 6. Threats to validity

**The model is not a prover.** `p_j` is a declared constant per obligation and one attempt costs one
unit; a real prover's per-obligation success probability moves with context, and a real attempt costs
varying time. This is deliberate — it makes the frontier an exact expectation rather than an estimate —
but it means the paper's claims are claims about the *model's* frontier, and their transfer to a real
toolchain is an open step (the model's parameters are recoverable from a toolchain's own logs, which is
the natural next study). The registered criterion (ii) is met in the model and not in a prover.

**The grid is declared, not exhaustive.** {{v1.graphs}} families × {{v1.diffs}} distributions ×
{{v1.cs}} coupling levels at `n` = {{v1.n}} is a designed grid, and the counts above are counts over
*that* grid. Robustness was checked by re-running the same laws at `n` in {6, 8, 10} × seeds
{139, 271, 511} (nine combinations): the n = 2 law agrees in 100.00 % of cells at every size and seed,
the sizing gap reproduces at 77.1–100.0 %, and no stated law is violated in any combination. The exact
theorem (§5.5) does not depend on the grid at all, since it is over the permutation group.

**The exactness is exactness about a computation, not about a machine's timing.** Every number is a
count or an expectation, so no number is a timing — but the *instrument* is still a program, and its
correctness rests on the anchor check (§3.2) rather than on a proof. The anchor is a closed form, not a
simulation, so the check is against ground truth; still, the theorem in §5.5 is *verified exhaustively
by computation*, not proved by hand, and the paper says so.

**One prior is refuted and one criterion is unmet.** P1a, P2 (in its added-value form) and P3 are
refuted; criterion (iv) is unmet in its registered form because the registered control is invalid. The
paper's contribution rests on what replaces them (Law 1, Law 1', the boundary, Law 2), not on the
refutations, and the refutations are reported here because the registration is on the record.

**Why it is still worth publishing.** The refutation of the registered control is itself a transferable
result: a randomised placebo is the standard reflex for "is the mechanism real?" and here it is the
wrong instrument, for a reason that generalises (the randomised quantity is a first-order effect). The
theorem and its boundary say something a planner can act on — order by difficulty or lose concavity —
and the sizing rule says something a project can act on today, with a measured error and a worst case.

## 7. Reproducibility

Everything in this paper is reproduced by **one command** in the package directory:

```
bash reproduce.sh
```

It re-runs the four instruments, the figure set and the claims leg, and prints
`ALL GREEN` on success with exit status 0 (exit 1 for a failure; exit 2 with a *named*
`NOT RUN` for each step that cannot run in the tree it is given — the exit code is a contract, and a
step that did not run is not a step that passed). The **claims leg** re-reads the freshly generated
reports and asserts 27 of the paper's headline numbers against them, so a number in the prose that
stops agreeing with a report fails the reproduction rather than the reader. The **plants** are five
deliberately broken inputs (a report, a battery, a report, the claims leg, and the README's copy of
the reproduction line) that must each fire, so the checks are tests and not restatements. The README
is read back because it quotes the run — the three numbers of the manuscript leg, its byte count
among them — and a copy that quotes a stale size fails the reproduction instead of a reader
noticing. The **cross-build leg** re-runs every shipped report on a second interpreter and compares
the two, because an `exact` tolerance is a claim about a *build* and a defect scoped to one
interpreter version is invisible to two runs of the same one. The pair has to **straddle** the
CPython 3.12 `sum()` change — the builtin `sum()` over floats became Neumaier-compensated in 3.12,
so a `sum()`-reduced quantity can differ across that boundary and cannot differ within one side of
it — and measured here the pair is **CPython 3.9.6 and 3.13.9**, which do straddle it, with every
shipped report byte-identical on both. Which interpreters exist is a property of the machine rather
than of the package, so the leg reads its list from `REPRO_BUILDS` instead of naming them.

The expected output and its tolerance are stated in `README.md`; the figures are regenerated and
compared byte-for-byte against the shipped set; the reference layer is checked offline by `--gate`
against a committed receipt whose first line binds it to the shipped pool by digest. Nothing here is a
timing and nothing depends on a seed's luck: the instruments are deterministic, and a re-run is
byte-identical.

## 8. Conclusion

A verification budget is not a pass rate, and the difference is measurable. We promoted the
success-vs-cost frontier to the measured object and returned three things. A **theorem**: an
easiest-first order always yields a concave frontier — exact, {{v3.gviol}} violations in
{{v3.perm}} permutations — whose converse is false and whose only failure mode is the coupling
({{v3.bnd.viol}} of {{v3.bnd.cells}} fixed-order cells), so what looks like an ordering rule is in fact
a statement about the *absence* of the mechanism the field cares about. A **decided prior**: coupling
moves the frontier, but the registered way of measuring that move — a randomised placebo — does not
separate the mechanism from the act of ordering ({{v0.order.eff}} of spurious effect under zero
coupling), which is a defect of the control and not of the mechanism. And a **rule**: reading a budget
off a pass-rate table under-budgets in {{v2.sz.under}} of {{v2.plan.cells}} cells
({{v2.sz.pct}} %), by up to {{v2.sz.worst}}x, worst where budgets are usually set. The instruction to a
planner is short: size from the frontier and the DAG, order by difficulty, and do not size from a rate.
