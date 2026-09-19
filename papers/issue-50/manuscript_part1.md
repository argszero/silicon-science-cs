# When Does Speculative Tool Execution Pay? Contention Boundaries, Latency Tails, and the Parallelism the Serial Baseline Already Had

## Abstract

An agent that issues a tool call speculatively - on a guess about what it will need
next - buys hidden latency and pays for it twice: the guessed call occupies shared
capacity, and a guess that is wrong either wastes that capacity or, when the call is
not idempotent, has to be undone. The systems literature of the last six months reports
speedups from doing this, each inside a window its authors chose. This paper asks where
the practice stops paying, and what it is actually buying.

We build a deterministic, closed simulator of an agent loop whose tool calls are served
by a shared pool with measured contention, and locate the **contention-indexed
speculation boundary** `rho*(A, h)`: the utilisation at which speculation's mean benefit
crosses zero, indexed by the pool size `A` and the speculation rate `h`. Ground truth is
by construction (a serial schedule and an oracle are both defined inside the instrument),
so the boundary is a property of the model rather than of a fitted curve.

Four results. (i) **The boundary is real and it is indexed by the pool, not only by the
speculation rate**: at `h = 1.0` it moves from {{rho_star_A16}} at `A = 16` to
{{rho_star_A96}} at `A = 96`, a span {{rho_star_span}} - more than an order of
magnitude larger than the per-seed interval width - and cells with the *same* utilisation
to five decimals straddle the boundary with opposite signs. The registered single-variable
law (`rho*(h)`) is therefore **unresolved**, and we report it as such rather than as a
confirmation; the sharpness statistic the same criterion registered is reported **unmet with
its reason**, because the committed windows bracket the zero crossing rather than the
registered `+/-5%` band. (ii) **The registered claim that the tail, rather than the mean, locates the
boundary is refuted in both halves**: at matched means a heavier tail moves the boundary
*down* and its descent is *shallower*; the quantity that actually indexes the boundary is a
count (the fraction of steps that can be hidden at all), not a magnitude. (iii) A
**matched-parallelism control** - the same speculation width, the same pool, but the
in-flight calls chosen blindly instead of by the engine's own signal - shows that a blind
schedule of the same width already buys {{blind_share_h050}} of the informed
gain at one cell, and that the informed share *falls* as speculation widens: most of what
"prediction" buys at these rates is parallelism the serial baseline never had.
(iv) The side-effect channel is priced rather than assumed: the compensation work a
discarded speculative call triggers lands on the shared pool and is not waited for by the
step that caused it, and a domain admissibility rule that speculates only on
idempotent or side-effect-free edges still admits a non-empty set of states with negative
benefit per step, of which about half the steps at the boundary are losing steps.

We also close the two remaining registered questions honestly: the classical closed-form
mean-field fixed point predicts the boundary's *level* well ({{fix_within_tol_pct}} of
comparable cells within +/-0.05 in the same coordinate) but expresses **no boundary at
all** - it is optimistic on every cell in which the simulator's benefit has already turned
negative - so the registered calibration criterion is reported **unmet, with that reason**;
and an external cell built from two published systems' own reported numbers reproduces
their signs {{ext_sign_match}} of {{ext_cells}}, reaching one inside its reported operating region, reaching a second,
and reporting the third as out of the model's reach rather than as a disagreement.

The instrument, every measurement behind every number, and the reference layer are
committed and reproduce byte-identically with one command. Contribution level:
**theory + empirics**.

## 1. Introduction

### 1.1 The question

An agent loop alternates thinking and tool calls. A tool call's latency is a large part of
the loop's wall clock, and a call can be issued *before* the agent has decided it needs
the result - that is speculation. The system keeps the guess in flight; if the agent then
asks for exactly that call, its latency has been hidden; if not, the in-flight work is
discarded, and if the call was not idempotent the discard has to be compensated.

Both halves are real and they move in opposite directions. The hidden half is bounded by
how much of a call's latency can overlap a think phase that is itself finite, so the
benefit saturates. The cost half grows with shared capacity: every in-flight guess is work
the pool must do, and at high utilisation the queueing delay it causes is unbounded. A
quantity that saturates meets a quantity that does not, so *if* the practice is worth
doing at all there should be a utilisation below which it pays and above which it does
not. This paper's study question is whether that boundary exists, where it is, and what
indexes it.

The answer we can defend is narrower than the question. The boundary exists - a single
positive-to-nonpositive crossing, located in every cell - and it is indexed by the pool's size
as well as by the speculation rate, which means the single-variable statement a reader would
like ("speculate below utilisation `x`") is not available from this instrument. How *sharp*
the crossing is, in the registered sense of a measured `+/-5%` fall, is **not established
here**: the windows that locate the crossing span at most {{win_rho_span_max}} in `rho` and
contain the family's whole benefit range ({{win_benefit_span_max}} percentage points) from its
positive maximum to below zero, which bounds the transition without measuring the registered
statistic (4.2).

### 1.2 Why the question is being asked now

Speculation is not new; hiding latency by executing work early is as old as
out-of-order execution [@uht1995] and as old as thread-level speculation
[@steffan2000][@oancea2007][@oancea2008]. What changed in 2026 is the unit being
speculated on: the tool call of an LLM agent, which is a network round trip with a side
effect, not a memory load [@spork2026][@smc2026][@specbox2026][@speculativecalls2025].
{{n_2026_speculation_works}} of this manuscript's references are 2026 works on
speculative execution for agents, and their reported gains are real measurements.

They are also, without exception, measurements taken inside a window the authors chose.
The discipline a system paper does not have to carry - and this journal's readers are
entitled to ask for - is the one that says where the window ends. A practitioner deciding
whether to enable speculative calls in a deployment needs the boundary, not the peak.

### 1.3 What we do

We build a simulator with three properties that make the boundary measurable rather than
plausible.

*Ground truth by construction.* The model defines both reference schedules - a serial
schedule that issues a call only after the think phase that wants it, and an oracle that
issues exactly the calls that will be needed - so a benefit is a difference between two
schedules of the same sampled work, not a comparison against a fitted baseline.

*Contention measured, not assumed.* Utilisation is a measured output (busy capacity over
capacity-times-makespan), not an input parameter, so a cell's `rho` is a fact about what
the schedule did.

*A matched-parallelism control.* The registered claim we test in (iii) above is really two
claims wearing one name: that issuing calls early buys *hidden latency*, and that the
*choice* of which calls to issue early buys something the width alone does not. They are
separated by holding the width fixed - the same fraction of steps issue a call early - and
varying only the rule that picks which ones.

We then take the model to two published systems' own reported numbers, with the mapping
from their coordinate to ours declared rather than fitted, and report the cells the model
reaches and the one it does not.

### 1.4 Contributions

1. **The construct.** A contention-indexed speculation boundary `rho*(A, h)`, with the
   instrument that makes it measurable, the serial baseline and oracle defined inside the
   instrument, and the per-seed interval attached to every reported location.
2. **The pool effect.** Evidence that the boundary is a function of the state and not only
   of the scheduling rate, with matched-utilisation cells on both sides of it.
3. **A decomposition.** The identity `benefit = w_s + S - overshoot` over observable
   per-step terms, which turns "does speculation pay" into three quantities that can be
   read off a run, and which shows that the near-tie at matched contention is carried by
   two large terms that nearly cancel.
4. **The matched-parallelism result.** A blind scheduler of the same width reproduces a
   large share of the informed gain, and that share grows with width - so "prediction"
   at these rates is mostly parallelism the serial baseline already had.
5. **The cost channel.** Where the compensation for a bad guess lands (on the pool, not on
   the charged step), and what the domain's admissibility prior leaves inside its allowed
   region.
6. **A negative result about the classical model, stated precisely.** The closed form has
   no boundary to locate the registered criterion in, and where the two are compared in the
   same coordinate it is optimistic on every cell the simulator has already turned
   negative.

Every one of the study's registered prior beliefs is reported in Section 7 with its
outcome - including the two that were refuted and the one that could not be resolved.

### 1.5 Roadmap

Section 2 places the work against six literatures and states the specific difference from
each. Section 3 describes the instrument and the design that makes each registered
question answerable. Section 4 reports the results in the order of the registered
criteria. Section 5 lists what the instrument does not model. Section 6 gives the
reproduction specification. Section 7 reports the registered prior beliefs one by one.
Section 8 states the threats to validity and why the result is worth publishing anyway.
Section 9 concludes.

## 2. Related work

Each subsection below ends with the difference that matters for this paper. The reference
list carries the same difference, one line per entry, so that the two readings can be
compared entry by entry.

### 2.1 Speculation in processors, compilers and languages

Speculation below the tool boundary is a solved-looking problem with a sixty-year lineage.
Disjoint eager execution showed that executing work outside program order is *optimal* when
the extra work is free [@uht1995]; thread-level speculation made the bet concrete and
scalable, with the memory-dependence machinery that keeps a speculative thread legal
[@steffan2000][@memdep2005], lightweight models for it [@oancea2007][@oancea2008], and
quantitative assessments of what it buys across benchmark loops [@marcuello2000].
Adjacent lines pay the same way for the same reason: pre-execution prefetching hides
memory and I/O latency [@pajuelo2004][@chen2008][@zhao2012], latency-hiding studies
measure how much of a stall can be covered [@latencyhiding1993][@optimistic2002], and
speculative locking and dynamic speculation schemes generalise the bet to critical
sections and to code with dynamic structure [@martinez2004][@raghavan2003]. The bet was
also taken to cluster schedulers, where re-executing a slow task hides stragglers
[@chen2014][@ibrahim2017][@redkha2017], and modelled for cloud applications
[@nylander2020]. A separate literature studies what speculation costs other than
throughput, since a speculative path can leak: software defences
[@cauligi2021][@oleksenko2023][@oleksenko2019][@bhattacharyya2019] and safe
speculation [@ye2020] all price the *information* channel, and the survey collection
[@specbook2005] collects the architecture-side background.

**Difference.** Every one of these prices speculation with extra work that is free at the
margin - the discarded guess burns a slot that no one is queued for - and with effects
that are internal to the process (registers, memory, or the microarchitectural state).
Our speculation crosses a tool boundary: the discarded guess occupies a *shared* server,
its cost is paid by other requests, and its correctness question is whether the outside
world was changed rather than whether a location was clobbered.

### 2.2 Speculative execution of tool calls in agent systems

The 2026 agent literature is where the practice moved from plausible to measured. SPORK
self-speculates on a forked agent state and reports a per-request break-even cost model
[@spork2026]; Speculative Macro Commit commits macro-actions early and reports gains
against sequential execution [@smc2026]; SpecBox schedules speculation inside a sandbox
[@specbox2026]; B-PASTE treats co-run interference as a scheduling term [@bpaste2026];
the cost-aware line replaces "issue everything" with an expected-value rule and an
admissibility precondition on the edges it will speculate across [@costaware2026]; and
speculative tool calls are made to pay at the inference-serving layer
[@speculativecalls2025]. Speculation also appears one level down, as a decoding-time
device for agents [@agentspec2026][@asymspec2026][@specgen2026][@alossurvey2026], for
multi-hop retrieval [@spechop2026], and inside real-time agent loops
[@specagents2026][@hidelatency2026]. Two papers bound the effects we model: the
agent-tool boundary is where failures accumulate rather than in the calls themselves
[@agentboundary2026], and issue-time privacy constrains when a guess may be issued at all
[@ghosttools2026]. Adjacent serving work supplies the scheduling context
[@grotov2026][@tailaware2026][@fleet2026][@chronos2026].

**Difference.** These works answer "does it help, and by how much, in the regime we
tested"; each reports its gain inside a chosen interval and none locates the utilisation
at which the sign turns. We do not propose a better predictor or a better commit policy;
we show that the boundary moves with a variable those works hold fixed - the pool's size -
and we quantify how much of the reported gain is parallelism rather than prediction, which
none of them separates.

### 2.3 Queueing models of multi-server systems

The queueing literature supplies the shape of the cost side. Exact and approximate results
for `M/M/c` and its relatives are the classical base [@finch2019][@chydzinski2024b], with
service rates that depend on waiting [@dauria2021], correlated service times [@zhu2026],
busy-period and queue-length distributions computed exactly [@zuk2023][@zuk2023b][@zuk2023c],
discrete-time networks approximated by refined mean field [@pan2023], and diffusion
approximations for networks [@koroliouk2021]. Fork-join systems are the closest relative
of our think/tool structure: large fork-join queues with nearly deterministic arrivals
[@schol2019], their maximum waiting time including heavy-tailed cases [@schol2023][@schol2022],
heterogeneous parallel servers [@mohanty2024], redundancy [@gao2026], and multiserver
waiting times in layered systems [@zhou2021layered]. Scheduling under uncertainty and
control objectives appears as uncertain holding costs [@gocmen2025], heavy-traffic limits
for SRPT queues [@ji2024], and heavy-tailed single-server models [@barik2026].

**Difference.** These results characterise waiting times for a service discipline, given a
load. Our quantity is the load at which two *schedules of the same work* produce equal
completion time, which is a crossing between two curves over the same samples; we use the
textbook results as anchors the instrument must reproduce - and one of them does not hold
in the regime our instrument probes - rather than as the prediction itself.

### 2.4 Tail latency in distributed systems

Tail latency is the reason a mean-based answer would be misleading, and the systems
literature has measured both the mechanism and its mitigation: heavy-tailed service times
dominate the waiting time of the multi-server queue [@whitt2000][@sigman1999], tail
latency is managed explicitly in file systems [@misra2019], in replicated systems by
proactive rejection [@lawniczak2024], in warehouse-scale applications by power management
[@kanev2014], in retrieval systems [@mackenzie2020], with approximate optimisations
[@iyer2023], and by treating large jobs separately [@split2026]; straggler mitigation by
cloning and by delayed relaunch is the same bet in a different coordinate
[@aktas2017][@aktas2017b]. Heavy tails also appear as a traffic property rather than a
service property [@chen2009].

**Difference.** This literature establishes that tails matter and shows how to hide them.
We test the registered hypothesis that the *tail* indexes the boundary of a speculation
decision and refute it: with means matched, the heavier tail moves the boundary down and
its descent is flatter, because the binding quantity is the fraction of steps that can be
hidden, which is a count.

### 2.5 Side effects, idempotency and retries

The cost of a wrong guess is not only wasted work. Retry amplification shows how a retry
policy can multiply load [@mehan2026], and idempotency is the standard defence:
mechanisms in payment systems [@dusad2025][@idempotency2025], stage-aware retries in
event-driven processing [@desai2026], duplicate detection with an idempotency framework
[@konasani2026], algebraic treatments of idempotency [@intro1998][@fagin2024], and retry
inside transactional memory [@tmretry2008][@bush2022] or as software error recovery
[@progressive1993].

**Difference.** This literature makes a repeated call safe; it does not price the
repetition. We take idempotency as a declared assumption of the model and ask what happens
to the boundary when it is relaxed, and we show that the domain's usual admissibility
prior - speculate only across side-effect-free or idempotent edges - still admits a
non-empty set of states in which a single step's benefit is negative.

### 2.6 Online algorithms with predictions

The learning-augmented line is the closest theory to a tool-call decision: a call is issued
on a prediction, and the quantity at stake is bounded by how good the prediction is.
Competitive paging [@irani1998paging][@antoniadis2022], metric tasks with untrusted
predictions [@antoniadis2023metric], calibrating predictions [@calibrated2025], designing
for the prediction rather than the algorithm [@predictionspecific2025], and the ski-rental
family with discounts [@advised2022][@discount2022], multiple shops [@multishop2014],
distributional advice [@kim2026][@cui2026][@discrete2026], statistical advice
[@canonne2025], tail risk [@twoslope2025], multiple agents [@multiagent2025], waiting
[@waiting2025], combinatorial variants [@combinatorial2025], the parking permit problem
[@parking2026], and improved bounds
[@improved2025] define the state of the art, with graph problems and smoothness
[@onlinegraph2022][@smoothness2023] generalising beyond paging. Adjacent LLM-systems work
predicts the quantities a scheduler would need - output lengths [@lengthpred2026],
tail-aware scheduling [@tailawarellm2026], cost models [@cnncost2026] - and routing with
calibration [@calibrateroute2026]; a new metric for ski rental [@newmetric2026] is the
same instinct as our registered criterion (iii).

**Difference.** Learning-augmented results bound *worst-case* ratios for one decision
against an adversary that knows the prediction error; the cost is a ratio of offline
optima and capacity is not modelled. Our benefit is a measured difference between two
schedules of the same sampled work on a contended server, and our control asks what the
*width* of the signal buys: at the rates we measure, most of the informed gain is available
to a blind schedule of equal width, which is a statement no competitive-ratio result makes
because those models have no parallelism to buy.

### 2.7 Speedup measurement and workload characterisation

Finally, the methodology the result must satisfy. Speedup itself is a contested
measurement: geometric-mean speedup is the wrong aggregate and equal-work or equal-time
harmonic means should be used instead [@eeckhout2025][@eeckhout2025b], superlinear speedup
is possible and sometimes inherent [@superlinear1987][@unconv2019], Amdahl's law bounds
parallel benefit and has been extended, revisited and pushed against repeatedly
[@amdahl2013][@amdahl2021][@amdahl2017][@amdahl2017b][@amdahl2007][@divisible2021] and
re-examined under AI scaling [@amdahl2026][@amdahl2026b]; fixed-size speedup has its own
definition [@fixedsize2011], alternative normalisations exist [@anotherview1990], and
speedup has been measured for virtual cores [@dlt2025], predicted from sequential runtime
distributions [@speedupdist2024], modelled for parallel programs [@model1997], scheduled
under common speedup models [@linearspeedup2005][@moldable2023], and accompanied by
theoretical constructions with exponential parallel speedup [@exp2024] or blockwise
variance reduction [@variance2023]. Workload characterisation supplies the profiles any
simulation is judged against: interactive cloud services [@workload2017], graph processing
[@workload2015], cloud efficiency at scale [@workload2024], LLM serving
[@servegen2025][@hydra2026], plus higher-level measures such as the roofline
[@roofline2026], vector-processing benchmarks [@vectorproc2023], utilisation-oriented
distribution [@util2024], fork-join decompositions [@forkjoin2026], and statistical
practice for evaluation itself [@stats2026].

**Difference.** This literature fixes how a speedup may be reported and what a workload
must look like; it does not supply the decision quantity, because a speedup is defined
against a schedule that never speculates, and the practice we study changes the schedule
*and* the load at once. We adopt the equal-work pairing for every reported benefit
(the same sampled work, two schedules, per-seed intervals) and we report the serial
baseline explicitly as the reference the model's own definition of the benefit names.
