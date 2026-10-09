# The Specificity–Brittleness Frontier of Machine-Checked Specifications

## Abstract

Machine-checked specifications — types, contracts, invariants, pre/post-conditions — are the currency
of program verification, and the standing advice is to make them stronger. This study asks whether
strength has a price. We separate the one informal axis the literature uses into two constructs set
independently on the same specification: **observational specificity `s`**, the share of the observable
behaviour space the specification pins, and **representation exposure `r`**, the share of its
constraints that mention internals a legitimate change may move; both are computed from the
specification's own text rather than asserted. Over a generated reference population and a declared
draw family we measure **detection** (the share of semantics-changing mutations a specification
rejects) and **breakage** (the share of semantics-preserving mutations it wrongly rejects), with the
split decided by an oracle rather than by a human label, and we locate the argmax `s*(lambda, r)` of
the net value `detection - lambda x breakage`. The falsifiable claim is that **exposure, not strength,
is the dominant term of a specification's maintenance cost**: at `r = 0` breakage is **exactly zero**
in every one of the 96 declared draws [C10], while detection saturates in `s`, so a specification that
exposes representation buys its last increments of detection at a cost that rises with the change rate.
Three registered predictions were tested and are reported as results: the mechanism prediction (P3) is
confirmed; the frontier prediction (P2) is confirmed in its movement half and **refuted** in its
interiority half — the optimum sits at a boundary, not interior, in 75% of the cells of the upper half
of the rate grid; and the alignment prediction (P1) is **refuted** — the worst matched-specificity
detection span over twelve behaviour alignments is **1.370x** [C11], against a registered gate of at
least 2x. The contribution level is `theory+empirics`: a derivation of the frontier plus a controlled
instrument that measures it, with ground truth by construction. No pipeline of this journal is reused
(no corpus, no classifier, no prevalence estimate); novelty is claimed under exemption (a) — a new
construct pair and a new measurement instrument — and exemption (b) — a result contradicting a
registered, theory-anchored prior.

## 1. Introduction

A machine-checked specification is a predicate over a program's behaviour, and the field's
practitioners are told to make it as strong as they can [8,10,4]. The advice is
sound for a specification written once and read once. It is not obviously sound for a specification
that is *maintained*: the same predicate that rejects a defect rejects a legitimate change, and the two
rejections are indistinguishable at the point of failure. Anyone who has updated a proof after a
refactor knows the shape of this — a `distinct` lemma dies because a list became a `Finset`, an
invariant dies because a field was renamed — but the field's practitioner literature records the pain
rather than a law: thirty deductive-verification practitioners name proof maintenance as an
underexplored obstacle with no quantification; the 2026 refactoring line states in its own words that
"maintainability" is difficult to reduce to reliable automatic metrics; a proof-maintenance case study
shows the consequence without measuring it; and the specification-generation wave measures whether
generated specifications are *faithful*, not how *durable* they are.

This study asks for the functional form. Given a program space with a declared change distribution and
a family of specifications over it, what are detection and breakage as functions of the
specification's **observational specificity** `s` and its **representation exposure** `r`? Does the net
value `detection - lambda x breakage` have an interior maximum `s*(lambda, r)`, and does `s*` fall as
the change rate `lambda` rises? If it does, then beyond a threshold rate the strongest available
specification is worth *less* than a weaker one, and the naive policy is dominated.

**Why this is not a census re-application.** This journal's census family measures prevalence in a
corpus with a classifier, and the quality bar caps that reuse at Novelty 3. This submission contains no
corpus, no classifier and no prevalence estimate. What it introduces is a construct pair and an
instrument:

1. **A construct pair set independently on one object.** The literature's "specification strength" is a
   single informal axis. We split it into `s` (how much observable behaviour is pinned) and `r` (how
   much of the specification's text is about internals), and we compute both from the specification's
   own clauses — so the x-axis and the z-axis of every figure are *derived* quantities, not settings.
2. **A semantics-preservation oracle.** The language is a small straight-line expression language over
   the finite ring `Z_256`, and a program's meaning is its complete 256-point table. Two programs are
   equivalent exactly when their tables are equal. "Legitimate change" and "defect" are therefore
   decided by an independent reference interpreter, with **no human labels and hence no
   annotation-disagreement rate to disclose**.
3. **A frontier, its located optimum, and its mechanism.** We measure the optimum's location, the
   boundary of the reachable region of the `(s, r)` plane, the size of the composition band at matched
   `(s, r)`, and — the paper's central mechanism — the per-kind ranking that says *which*
   representational clauses are worth exposing and which are pure liability.

**Significance.** Three communities have a decision that changes if the result is true. (i)
**Verification practitioners** who write Dafny, Frama-C, JML, Lean or Coq specifications today choose
how much to pin by taste; the frontier replaces "pin everything you can" with "pin what survives the
changes you actually make", and prices the difference. (ii) **Tool builders** in the selection, updating
and refactoring line, which currently optimises proxies — if durability is led by exposure, the proxy is
aimed at the wrong variable. (iii) **Agent pipelines that gate on a generated specification**: if
durability is led by exposure, then generating *stronger* specifications is the wrong lever, and the
audit that matters before merge is an exposure audit. The per-kind ranking converts that advice into a
concrete prescription (§6.6): if a specification must expose representation, expose *which literals
occur* and never *tree shape*.

**Contributions.** (1) The construct pair and its measurement (§3). (2) The instrument: the language,
the mutation algebra, the oracle and the generated reference population (§4). (3) The frontier
measurement: bands, the located optimum, the reachable region and the composition band (§6.1–§6.5). (4)
The mechanism ranking by clause kind (§6.6). (5) Three registered predictions tested and reported as
results, one of them refuted (§6.7). Every number in this manuscript is re-derived from the committed
artefact by the package's own checks; §7 states which claims those checks reach and which they do not.

## 2. Related work

**Specification strength as one axis.** The classical formal-methods literature treats a specification
as a predicate and its strength as a single scalar [8]; TLA+, design-by-contract, JML, Dafny, Why3 and
refinement types each give a language in which "stronger" is the only dial
[20,10,16,32,44,47]. The model-checking and refinement line makes the
same assumption when it refines an abstraction [21,31,36].
*Difference:* none of these separates "pins more observable behaviour" from "mentions more internals",
because in each of them the two move together by construction; we separate them and set them
independently, and our result is that they are governed by different terms.

**Proof and annotation maintenance.** The maintenance cost of formal artefacts is named in the
literature at least as far back as Brooks' distinction between essential and accidental difficulty
[7] and Lehman's laws of software evolution [5], and the survey literature documents
the scale of the engineering effort [60,26]. The closest prior work is a line
that *adapts* proofs rather than modelling their brittleness: proof automation is retargeted so that
proofs survive change [57], translation validation is used to check that a transformation
preserved meaning [17,41], a verified compiler carries the preservation argument
end-to-end [28], and compiler testing finds the failures that validation misses
[37,42]. *Difference:* these systems repair or check after the fact; we ask
what property of the specification predicts whether repair will be needed at all, and we measure it. The
Kepler proof [55], the four-colour formalisation [25] and the Lean mathematical library
[62] are the field's demonstration that large machine-checked developments are possible; their
maintenance cost is exactly the quantity that has no model [81].

**The oracle problem and mutation testing.** Mutation testing supplies the canonical way to measure a
test suite's or a specification's discriminating power [3,35]. Its central difficulty
is the **equivalent mutant** [11,30,40,51,45,59], and the oracle problem more generally [6,50], with metamorphic
testing as one response [52]. *Difference:* mutation testing's equivalent-mutant problem is the
same *object* as our breakage — a mutant that does not change behaviour — but it is treated as a nuisance
to be detected case by case, and the validity threats of mutation-based assessment are debated as a
measurement-validity question [53,45]. Here the split is the treatment, not the
nuisance: semantics preservation is decided *by construction* over a 256-point table, so the two classes
are exact and breakage becomes a first-class dependent variable, while the mutation signal is elsewhere
used to grade generated artefacts [86]. Test generation and invariant inference
supply the specifications this literature mutates [15,23,24,34,33]; regression-testing selection, minimisation and prioritisation are the operational answers
to "which of these should I keep" [13,19,39], and our frontier is the
objective those heuristics approximate.

**Change, not strength, is what a maintained artefact meets.** The mining literature has measured how
code changes [22,43,29], how changes go wrong [39],
how automatically repaired changes are evaluated [38,58], how flaky behaviour distorts
measurements [46,63], and how continuous integration absorbs the volume [54].
*Difference:* this line predicts *when* a change breaks something from properties of the change; we
predict it from a property of the *specification that meets the change*, at matched specificity, and we
show (§6.4) that at matched specificity the breakage is a **band** and not a number — the reason a
code-change-only predictor cannot be complete.

**Machine-checked artefacts outside verification proper.** Formal methods have been industrialised in
cloud infrastructure [48], shipped in static analysers [49], and used to build assurance
cases [70]; runtime verification supplies the monitoring counterpart [61], and the
trust-and-audit line applies similar reasoning to provenance [100]. *Difference:* each of these
fixes the specification once; we take the specification as the object under measurement and ask how its
contents, not its mere existence, determine cost.

**Machine learning systems, where specifications are generated and then rot.** The ML-engineering line
documents the debt and documentation gaps of systems whose behaviour is specified implicitly
[64,56,65,66]; the 2026 wave moves specification *writing*
into agents and then measures whether the result is faithful [97,93,102,101,72,77], including audits of whether agent benchmarks and merged patches
do what they claim [74,73,75,85] and equivalence
techniques for validating generated code [78,89]. *Difference:* those works measure
whether a generated artefact is *correct*; ours measures whether it is *durable*, and the construct
difference is what makes the answer decision-relevant — a faithful specification that exposes internals
is expensive for exactly the reason our mechanism predicts.

**The 2026 verification-language frontier.** The months before this manuscript produced work on
operational semantics for weak-memory C [71], sensitivity type systems for Rust [79],
multi-language program logics [87], dependently typed model composition
[83], the formalisation of computational models in Dafny [76], lifting a
preprocessor's structure [90], coordination semantics [84], session-type state spaces
[98], producer-driven stream protocols by refinement [95], machine-checked
group theory [81], shallow embeddings of ontological arguments [88], certified
sorting [91], formal reasoning about performance models [92], equivalence checking of
hybrid quantum programs [94], tristate multiplication [99], and evaluation of generated
RTL beyond compilation [80] and of manual optimisation as a practice [82], alongside
statistical reporting standards for LLM-based software engineering [96,69]. *Difference:*
every one of them either produces a machine-checked artefact or a rule for producing one; none reports
how much of a specification to pin, and none has a durability measurement.

**Empirical method.** The study follows the field's methodological guidance on running and reporting
software-engineering experiments [14,18,67,68] and on structural
metrics as quality indicators [9,12,27]. *Difference:* those works measure a
proxy for a cost; our dependent variables are defined by an oracle, so the measurement's validity rests
on the semantics being decidable rather than on a metric's correlation with a human judgement. Dijkstra's
and Hoare's treatment of programs as mathematical objects [2,4] and Parnas' information
hiding [1] are the intellectual ancestors of the construct: Parnas' criterion is exactly the
distinction between a decision that is *likely to change* and one that is not, which is what exposure
measures.

**Reverse gap, with its search form.** The claim "no prior work reports a functional form for this
trade-off" is an absence claim, and an absence claim owes the search that produced it. *Index 1
(primary):* the arXiv API (`https://export.arxiv.org/api/query`), date field **`submittedDate`**, sorted
descending, 10–12 results per query, executed **2026-10-01**. Queries and the windows they returned
(submission date, oldest → newest): `all:"proof maintenance"` → 2 results, 2025-10-23 → 2026-06-19;
`all:"proof" AND all:"refactoring"` → 10, 2025-08-17 → 2026-09-24; `cat:cs.SE AND all:"formal
verification" AND all:"LLM"` → 10, 2026-08-18 → 2026-09-30; `all:"formal verification" AND all:"testing"
AND all:"cost"` → 10, 2024-11-05 → 2026-08-21; `cat:cs.PL AND all:"annotation" AND all:"overhead"` → 10,
2025-07-21 → 2026-07-01; `all:"specification" AND (all:"brittle" OR all:"brittleness")` → 10, 2026-09-21 →
2026-09-29; `all:"test" AND all:"brittleness"` → 10, 2026-09-20 → 2026-09-29; `all:"invariant" AND
all:"strength" AND all:"verification"` → 10, 2023-11-07 → 2026-09-30; `all:"verification" AND
all:"debt"` → 10, 2026-05-22 → 2026-09-24; `all:"over-specification" OR all:"overspecification"` → **0
results**. Within those sets — and this is the claim, *narrowed to what the search reaches* — we found no
work that reports a functional form, a threshold, or an interior optimum for the detection-versus-
breakage trade-off of a specification; what the searches return are tools, surveys and case studies.
*Index 2 (Crossref),* `query.bibliographic`, relevance-ranked, no date filter, same date: this index
**cannot support the claim and is not relied on** — its totals are index-wide (950,217 records for one
of the phrases) and its top rows are off-domain (a materials-science "brittleness" cluster), so a reader
could not re-run the search to the same absence. It is named because the first index has no record of
the venues this literature also uses, and stating that is part of the form. *Structural reason the gap
exists*, independent of the search: measuring the trade-off needs a program space whose semantics are
known, a graded specification family, and an oracle for legitimate-versus-defect change — three artefacts
the proof-tooling line has no reason to build, because its questions are about *closing* proofs.

## 3. The construct: specificity and exposure

Let a specification be a set of clauses over a program. Each clause is one of two kinds:

- **Observational** — `("obs", i, v)`: the program's output at input `i` must equal `v`. This constrains
  behaviour a caller can see.
- **Representational** — a constraint on the syntax tree: the root operator must be `op` (`top`), the
  operator `op` must not occur (`no_op`), the node at a given path must be `op` (`node_op`), the node
  count is at most `n` (`size_le`), the depth is at most `n` (`depth_le`), or a literal is present
  (`const_present`) or absent (`const_absent`).

The two constructs are then computed from the specification's own text:

```
s = |{ i : ("obs", i, .) in spec }| / |domain|          (observational specificity)
r = |{representational clauses}| / |{all clauses}|      (representation exposure)
```

Every specification used in this study is *true of a reference program by construction*: the
observational clauses pin that program's outputs on a nested prefix of a fixed input permutation, and
the representational clauses are tight facts about its syntax. A mutation therefore fails a clause only
by differing from the reference — the specification is never wrong about the program it was written for.
This is what makes breakage interpretable: every rejection of a semantics-preserving mutation is a false
alarm by construction, not a judgement call.

**The consequence that is the study's mechanism.** A semantics-preserving change preserves the whole
256-point table, and an observational clause is a statement about that table. Therefore a specification
with `r = 0` has **breakage exactly zero** — not small, not bounded, but zero, at every grade. False
alarms can be produced only by exposure. `smoke_frontier.py` asserts this as a control rather than
assuming it [C10].

**Reachability is bounded, and the bound is a finding.** A specification that spends `s x 256` clauses on
observable behaviour can carry at most as many representational clauses as the reference's syntax offers,
`B`. The requested `r` is therefore a *request* and the measured `r` is the computed one; the reachable
part of the plane is bounded by roughly `r <= B / (B + s x M)` with `M = 256`. In the measured population
`B` ranges from **21 to 47** candidates per reference [C7] [C8], and the bound is what determines which
cells can be measured at all — §6.5 reports it.

## 4. Instrument

**The language.** A tiny straight-line expression language over `Z_256` with the operators `add sub mul
mod max min lt not and or ite`, constants, and one input variable `x`. Its meaning is the complete table
`x -> output(x)` for `x` in `Z_256`; there are no side effects, no variables and no recursion, so the
denotation is a total function of the single input and the table **is** the semantics. Two programs are
semantically equivalent exactly when their tables are equal — exact and decidable, which is what makes
the downstream measurement possible without any annotation.

**The reference population is generated, not chosen.** Sources are enumerated from the language's grammar
with a declared size bound [C1]; each source's semantics is computed [C2]; sources whose table is
constant, or whose mutation set contains no semantics-changing mutation, are dropped with the count
recorded [C4]; duplicates by table and by name are merged. The census is reported in full [C1] [C2] [C3] [C4]
so that the population's construction is auditable rather than asserted.

**The mutation algebra, and the oracle.** A mutation set is generated for each reference: edits that
replace an operator, replace a constant, restructure a subtree, or rewrite an identity (`add x 0`, `mul x
1`). Whether an edit is semantics-preserving is decided by **comparing 256-point tables** through the
reference interpreter — not by a human label, not by a syntactic criterion, and not by a proxy
[C5] [C6]. This is the instrument's core: it is what turns "legitimate change" into a defined set.

**The specification family is graded and non-nested across kinds.** For a target `(s, r)` the family
builds a specification whose observational clauses pin a nested prefix of the fixed input permutation (so
higher grades strictly contain lower ones) and whose representational clauses are chosen from the
reference's menu of `B` true syntactic facts [C7] [C8]. The family's `s` and `r` are **computed from the
specification's text** and compared against the declared grid, so a grading error is a check failure
rather than a silent reading. Because the representational clauses are drawn from a menu, the same
`(s, r)` admits many specifications; that freedom is a *treatment* in this study (§6.4), not noise.

**Controls, and the rule that a control must be able to fail.** Six smoke batteries and five plant audits
are part of the package. Each check is required to fire on a deliberately corrupted copy of its object; a
plant that reaches no check is reported as *inert* rather than counted as a pass. The bitmask evaluator
used inside the decisive run is checked against the reference interpreter's own `satisfies` rather than
assumed equivalent.

## 5. Protocol

The decisive run enumerates, for every reference program, every cell of a declared grid and every draw:

- **Specificity grid** `s` in {0, 0.0625, 0.125, 0.25, 0.5, 0.75, 1.0} (7 grades).
- **Exposure grid** `r` in {0, 0.05, 0.1, 0.2, 0.3} (5 levels).
- **Cost grid** `lambda` in {0.1, 0.25, 0.5, 1.0, 2.0, 5.0} (6 values).
- **Draws**: 12 behaviour alignments (a `None` protocol plus `low`, `high`, `even`, `odd`, `edges` and
  six seeded random pin sets) crossed with 8 clause mixes (a `None` protocol plus seven seeded orderings
  of the clause kinds). **96 draws in total** [C9].

For a draw and a cell, detection and breakage are **pooled over all 262 references** [C3], and
`net(s) = detection(s) - lambda x breakage(s)`; the optimum `s*(lambda, r)` is the argmax over the seven
grades, with ties going to the smaller `s`. The alignment axis moves *which* input positions a
specification pins (detection); the mix axis moves *which kinds* fill the representational budget at a
fixed clause count (breakage). Both are free choices an author makes without noticing, which is why the
study reports **bands over the enumerated draws** rather than single numbers.

**What is sampled and what is not.** Nothing is sampled randomly: the population is generated and
enumerated, the draws are declared and enumerated, and the grid is fully crossed. The report is therefore
a band over an enumerated set, not a confidence interval over a random sample, and the artefact stores
the endpoints. **Determinism replaces the multi-run requirement**: the study's results are not
stochastic, and the package requires two independent runs of the decisive run to be byte-identical (§6.7,
criterion 6). A differing artefact is a failure of the package, not a reading.

## 6. Results

### 6.1 The two bands

At `r = 0` detection rises with specificity and **saturates**: the empty specification detects nothing,
the weakest non-empty grade already rejects about 69% of semantics-changing mutations (band 0.690 to
0.943 over the draws), and the fully observational specification (`s = 1.0`) rejects **all** of them
(1.000 to 1.000). Breakage, by contrast, is **exactly 0.000 at every grade when `r = 0`** [C10], and
rises with exposure once representation is mentioned: at `s = 0.125`, breakage's band runs from 0.163 to
0.557 at `r = 0.05` and reaches 0.994 to 1.000 at `r = 0.3`.

![Detection and breakage against specificity s, each drawn as the full band over the 96 declared draws. Left: detection saturates in s and its band narrows as the specification gets stronger. Right: breakage is exactly 0 at every s when exposure r = 0, and rises with r once representation is exposed.](figures/fig1_bands.png)

The two channels therefore have different *arguments*: detection is governed by `s` and is concave in it,
while breakage is governed by `r` and is, to first order, linear in it. That difference is the paper's
claim in its simplest form.

### 6.2 The frontier and its located optimum

The optimum `s*(lambda, r)` is not degenerate. At `r = 0` it is the boundary `s = 1` for every `lambda` —
the strongest specification wins outright, because there is no breakage to pay for. Once `r > 0` the
optimum moves interior, and it then **falls monotonically in the change rate**: for every `r > 0`, the
modal optimum is 1.0 at `lambda = 0.1` and 0.0 at `lambda = 5.0`. At `lambda >= 2` the empty specification
(`s = 0`) wins outright for every `r >= 0.1` — a specification that pins nothing cannot false-alarm, and at
that price the loss of detection is not worth paying.

![The graded optimum s*(lambda, r): each horizontal bar spans the argmax observed across the 96 draws, with the modal value marked. At r = 0 the optimum is the boundary s = 1 for every lambda. For r > 0 the optimum moves interior and falls with lambda, until the empty specification (s = 0) wins outright at lambda >= 2.](figures/fig2_frontier.png)

**The registered interiority claim is refuted.** We registered that `s*` would be interior in at least 80%
of the cells of the upper half of the rate grid. Measured over the twelve cells with `lambda >= 1` and
`r > 0`, `s*` is interior in **3 of 12 (25%)**: the optimum is pushed to a boundary at both ends — to the
strongest specification where exposure is zero (the frontier degenerates, because the cost term vanishes),
and to the empty specification at the top of the rate range (where the cost term dominates). The interior
optimum exists, and is where the trade-off is live, but it occupies the *middle* of the rate grid rather
than the upper half. §6.7 reports this against the registered criterion.

### 6.3 Matched specificity: the alignment span, and the refutation of P1

We registered that, at **matched observational specificity**, detection would vary across behaviour
alignments by a factor of at least 2, because a specification is falsified only by changes whose effect
leaves the behaviours it constrains. It does not. Holding the clause mix at the protocol of the earlier
steps and varying only the pin set, the worst matched-specificity span over the twelve alignments is
**1.370x**, at `s = 0.125`, `r = 0.0` [C11] [C12] [C13]. The span shrinks as the specification strengthens
and reaches **1.000 at `s = 1.0`**, where every alignment pins the entire behaviour space and the alignment
term disappears.

![Matched specificity, twelve pin-set alignments (prior P1). Detection against s at r = 0.05: the structured pin sets are the extremes (edges best, block-low/high worst) and the seeded random ones sit between them. The span is 1.37x at most and collapses to 1.00 at s = 1 — the registered prediction of at least 2x is refuted.](figures/fig3_alignment.png)

The *ordering* the registered mechanism implies survives even though the magnitude does not: the
structured pin sets are the extremes (`edges` best) and the seeded random sets sit between them. What is
refuted is the size of the term, not its existence. The registered success criterion required at least 2x
[C11]; the measured value is 1.370x, and the criterion is reported **unmet with its reason**.

This refutation also corrects an artefact of the earlier rounds: a pilot on six hand-written programs had
suggested a span of 16x, because those programs' pin sets had *known* difference sets and the coincidence
made the pin set's extremes coincide with the extremes of the difference set. On a generated population —
where the pin sets are not chosen to expose a particular difference — the term is an order of magnitude
smaller. The lesson is recorded as a result: an alignment effect measured on programs chosen by hand is
not a measurement of the alignment effect.

### 6.4 At matched (s, r) the answer is a band, not a number

Composition — *which kinds* fill the representational budget — is free at a fixed clause count and a fixed
exposure. Fixing the alignment and the specification grade and varying only the clause ordering, breakage
moves by up to **0.479** [C14], while detection never moves by more than **0.096** [C15].

![The composition band at matched (s, r): for each exposure r at s = 0.125, the vertical extent of breakage across the eight clause orderings against the same extent for detection. Breakage swings by up to 0.479 while detection never moves by more than 0.096.](figures/fig4_mixband.png)

The consequence is a well-posedness result: a statement of the form "at exposure `r` the false-alarm rate
is `x`" is **not defined** by `(s, r)` alone. Two specifications with the same specificity and the same
exposure can differ in breakage by nearly half the unit interval. This is also, numerically, the model's
reproduction of the qualitative claim in the 2026 refactoring line — that maintainability is difficult to
reduce to a reliable automatic metric: the automatic metric `(s, r)` provably does not determine the cost
of maintenance, and the residual is measured here. (§6.7 criterion 5 reports this mapping, and states what
it is not.)

### 6.5 The reachable region

Not every cell of the declared grid can be built. Because the representational clauses must be *true
facts* about the reference's syntax, a specification that spends `s x 256` clauses on observable
behaviour can carry at most `B` representational ones, with `B` between 21 and 47 for this population
[C7] [C8]. Of the 35 declared cells, **23 are reachable**; the unreachable ones are the high-specificity,
high-exposure corner, exactly where the bound binds.

![The reachable region of the (s, r) plane. A specification that spends s*M clauses on observable behaviour can carry at most r <= B/(B + s*M) representational ones, with B the menu the reference's syntax offers (21-47 here). The curve is the boundary for the smallest, median and largest menu; the points are the measured cells, hollow where the request was out of reach.](figures/fig5_region.png)

The region is itself a result about the construct: `r` is not a dial an author can set freely against `s`,
and the boundary couples them. It also explains part of the frontier's shape — the cells where the
strongest specification is optimal are precisely the cells where exposure cannot be purchased.

### 6.6 The mechanism: which representational clauses are worth exposing

Per clause kind, and pooled over the population, we ask how many semantics-changing mutations a kind
*alone* rejects, and how many semantics-preserving mutations it *alone* rejects. The ranking is decisive
and it is the paper's practical prescription.

| kind | changing rejected | preserving rejected | ratio | claim ids |
|---|---|---|---|---|
| `obs` | 591 | 0 | — (free of false alarms) | [C26] [C27] [C16] [C17] |
| `const_present` | 380 | 1 | 1388.8325 | [C28] [C29] [C18] [C19] [C20] |
| `const_absent` | 379 | 349 | 3.969 | [C37] [C38] [C21] |
| `top` | 42 | 489 | 0.314 | [C39] |
| `child_op` | 63 | 2157 | 0.107 | [C35] |
| `no_op` | 55 | 1826 | 0.110 | [C40] |
| `node_op` | 104 | 2159 | 0.176 | [C36] |
| `op_count_le` | 2 | 1978 | 0.0037 | [C34] |
| `depth_le` | 0 | 2065 | 0.0 | [C30] [C31] [C22] [C24] |
| `size_le` | 0 | 2110 | 0.0 | [C32] [C33] [C23] [C25] |

![The mechanism, by clause kind: the share of semantics-changing mutations a kind alone can reject, against the share of semantics-preserving mutations it alone rejects. The observational family rejects every defect and no legitimate change; among the representational kinds the literal-presence family is the only one with a favourable ratio, while size_le and depth_le reject a thousand legitimate rewrites and no defect at all.](figures/fig6_mechanism.png)

Three readings matter. First, the observational family is the only one free of false alarms — 591
semantics-changing mutations rejected and **zero** legitimate ones [C26] [C27] [C16] [C17]: the mechanism
of P3 at the clause level. Second, among representational kinds the **literal-presence** family is the only
favourable one: `const_present` rejects 380 semantics-changing mutations [C28] and exactly **one**
legitimate change [C29], a ratio of about **1389 to 1** [C20]. Its absence twin already pays:
`const_absent` rejects 379 defects [C37] but 349 legitimate rewrites [C38], a ratio near **4 to 1** [C21].
Third, the **structural** bounds are pure liability: `depth_le` and `size_le` each reject **zero**
semantics-changing mutations [C30] [C32] while rejecting more than two thousand legitimate rewrites each
[C31] [C33], and each rejects about 96% of the preserving set [C24] [C25] while rejecting no defect at all
[C22] [C23]. They are the shape of a specification that has silently become untouchable.

The menu sizes make the same point structurally: of the 262 references [C3], 102 offer a menu of 29
syntactic facts [C41], 77 offer 26 [C42], 72 offer 24 [C43], and only 2 offer the smallest menu, 21
[C44] — the population's syntax is rich enough to expose representation almost everywhere, which is why
the region of §6.5 is bounded by the *specificity* an author chooses and not by the language's poverty.

The prescription that follows — and the reason this ranking is the paper's decision-relevant output — is:
**if a specification must expose representation, expose which literals occur, never tree shape.**

### 6.7 The registered predictions and their criteria

The registration fixed three predictions and six success criteria before the deciding runs. Reported
against them:

| # | registered prediction | outcome |
|---|---|---|
| P1 | at matched specificity, detection spans at least 2x across alignments | **refuted**: 1.370x [C11], criterion 4 **unmet** |
| P2 | interior `s*` in at least 80% of the upper-half cells; `s*` decreasing in `lambda`; the strongest specification dominated at the highest `lambda` | **confirmed in the movement half** — the modal `s*` falls monotonically in `lambda` for every `r > 0`, and at `lambda >= 2` the empty specification wins; **refuted in the interiority half** — 3 of 12 cells interior (25%), criterion 1 **unmet with its reason**; criterion 2 **met** (the highest-rate cell's optimum is 0.0, below the family's median grade) |
| P3 | at matched specificity, the exposure ablation moves breakage by at least 3x | **confirmed**: breakage at `r = 0` is exactly 0 in all 96 draws [C10], so the ratio is unbounded, and the per-kind ranking shows the same separation at clause level (1389 to 1 for `const_present` [C20]); criterion 3 **met** |

Criterion 5, the reproduction arm, is **met in the weak form the model can support and not in the strong
one**: the model reproduces numerically the *mechanism* of one registered anchor — that maintainability
resists a reliable automatic metric — as the measured composition band of §6.4, where the automatic metric
`(s, r)` fails to determine breakage by up to 0.479 [C14]. It is **not** a re-run of that anchor's
experiment, whose claim is qualitative and whose data are not in this package; the mapping is stated here
so that a reader can reject it if they find it too loose. Criterion 6, determinism, is **met**: the package
requires two independent runs of the decisive run to produce a byte-identical artefact, and that
requirement is executed by `bash reproduce.sh`.

**What the two refutations change.** The registered story was that specificity is the wrong axis and
alignment is the term it omits. The measurement says the opposite in both halves: alignment is a real term
but a *small* one (1.370x, vanishing as specificity grows), while the term specificity's story omits is
**exposure**, whose cost is unbounded in `r` and larger than the whole detection range at `r >= 0.2`. The
paper's thesis survives the refutation of its registered form and is sharper for it: it is not that a
strength-only model under-predicts the spread by an order of magnitude, it is that a strength-only model is
looking at the wrong variable.

## 7. Threats to validity

**Construct validity: the change distribution is synthetic.** The mutation algebra is a declared generator,
not a measured refactoring distribution, so the *shape* of the frontier could be a property of the generator.
This is the study's largest threat, and it is bounded in three ways. (i) The mechanism does not depend on
the generator: breakage at `r = 0` is zero **by construction**, because a semantics-preserving change
preserves the table every observational clause speaks about — no generator can violate that (P3 is a theorem
about the instrument, and the measurement confirms it rather than discovering it) [C10]. (ii) The per-kind
ranking is bounded by the same argument: a `size_le` clause can only be falsified by a change that alters
the node count, which is representation-local by definition; that the ranking's *magnitudes* would move under
a different generator is likely, and its *ordering* is what the prescription uses. (iii) The registered
fallback — deriving the mutation distribution from the commit history of a public machine-checked
development — is not executed here and is declared as the first upgrade step, not claimed.

**Construct validity: the language is small.** A straight-line language over `Z_256` with one input has a
semantics that is a 256-entry table, which is what makes the oracle exact; it also means the "programs" are
not programs in the sense a verification engineer means. The constructs transfer — `s` and `r` are defined
over clauses about behaviour and clauses about representation, and every real specification language has
both — but the *numbers* do not. The claim is a shape and a mechanism, not a prediction of a false-alarm
rate for a Dafny development.

**Internal validity: composition is not controlled, it is measured.** §6.4 shows that at matched `(s, r)`
breakage is a band of up to 0.479 wide [C14]. That band is reported as a result, but it also means every
number elsewhere in this paper is a band endpoint over an enumerated draw set rather than a point
prediction. Where a single number is quoted (the frontier's modal optimum, the per-kind counts) it is the
modal or pooled value over the draws, and the band is stated beside it in the artefact.

**Internal validity: the population is generated from a grammar.** `B`, the menu of representational facts,
comes from a grammar enumeration, so the distribution of menu sizes [C41] [C42] [C43] [C44] is a property of
the enumerator. The region boundary of §6.5 is therefore quantitative for this population and qualitative
in general: `r` is bounded by `s` because a specification cannot constrain more syntax than its behavioural
clauses leave room for.

**External validity: no real specification was measured.** The study measures no published proof, no real
Dafny specification, and no library's annotations. It is a controlled instrument, and its claim is the
functional form and the mechanism, which are the *inputs* a field-level measurement would need. The
reproduction arm (§6.7 criterion 5) is the only contact with the literature's claims, and it is explicitly
weak.

**The refuted criteria are reported as unmet, not reframed.** Two of the six registered success criteria
failed (criterion 1, interiority, and criterion 4, the alignment gate). The registration's own rule — that
substituting newly chosen metrics after the results are known voids the exemption-(b) credit — is why they
are reported with the measured values beside them rather than replaced. The refutations are the study's
strongest novelty position, and the honest statement of them is the point.

**Why this is still worth publishing.** The result that survives every threat above is a *definitional*
one: specificity and exposure are separable constructs, they are governed by different terms, exposure's
term is the one that produces false alarms, and within exposure the kinds are ranked by a ratio that spans
three orders of magnitude. A practitioner who changes nothing else can swap a `size_le` clause for a
`const_present` clause and reduce the specification's exposure to legitimate change without losing a single
defect — that is a decision, and it does not depend on the generator being realistic, the language being
large, or the numbers transferring.

**The instrument's reach, stated with its verdict.** `check_manuscript.py` re-derives every value in
Appendix A from `canonical_results.json` at the precision this text prints, verifies that every claim id
here is cited in the body, and checks that the figures shipped and the figures shown are the same set.
`check_aggregates.py` covers the claims that depend on the `(s, r)` and `(lambda, r)` grids, which the
Appendix A path form cannot address because their keys contain a separator. What neither reads: the prose
sentences that are not claims-table rows (for example the qualitative statements about *which* alignment is
best, and the §7 arguments), the correctness of the mutation algebra's design, and the correspondence
between this toy language and a real one. Those are the reviewer's read, and they are named here rather
than left to be discovered.

## 8. Conclusion

A specification's strength and its exposure to representation are different things, and only the second
one produces false alarms on legitimate change. Measured over a generated population, a semantics-
preservation oracle and 96 declared draws: breakage at zero exposure is exactly zero; detection saturates
in specificity; the net-value optimum moves from the strongest specification to the empty one as the change
rate rises; at matched `(s, r)` the breakage is a band nearly half the unit interval wide; and among the
representational clause kinds, only literal-presence pays, at a ratio of about 1389 to 1, while the
structural bounds reject no defects and thousands of legitimate rewrites. Two registered predictions were
refuted or narrowed — the alignment term is real but small, and the optimum is a boundary at both ends of
the rate range — and one was confirmed as a theorem of the instrument. The prescription for a
specification author is short: **expose which literals occur, never tree shape**, and price the change rate
before pinning more behaviour.

## Appendix A — claims and their artefacts

Each row is one claim this manuscript makes about its own content. The path is resolved against
`canonical_results.json`, the committed artefact of `decide.py`; the value is compared at the number of
decimals printed here, so the check bites at the precision a reader sees. `refs/keys.json` maps every
citation key to its reference number and `assemble.py` renders the `@key` tokens in this source file to
that numbering, so a renumbering cannot silently re-point a citation.

| id | claim | value | artefact path |
|---|---|---|---|
| C1 | generated sources enumerated from the language grammar | 6600 | population/census/generated_sources |
| C2 | distinct semantics among the generated sources | 365 | population/census/distinct_semantics |
| C3 | reference programs in the measured population | 262 | population/references |
| C4 | sources dropped for having a constant table | 106 | population/census/dropped_constant_table |
| C5 | semantics-changing mutations in the population | 591 | population/changing_mutations |
| C6 | semantics-preserving mutations in the population | 2160 | population/preserving_mutations |
| C7 | smallest representational menu (B) in the population | 21 | population/menu_B_min |
| C8 | largest representational menu (B) in the population | 47 | population/menu_B_max |
| C9 | declared draws in the decisive run | 96 | protocol/n_draws |
| C10 | maximum breakage over all draws at zero exposure | 0.0 | findings/p3_breakage_at_r0_max |
| C11 | worst matched-specificity detection span across alignments | 1.370 | findings/p1_worst_alignment_span |
| C12 | specificity of the cell carrying the worst alignment span | 0.125 | findings/p1_worst_alignment_cell/0 |
| C13 | exposure of the cell carrying the worst alignment span | 0.0 | findings/p1_worst_alignment_cell/1 |
| C14 | largest breakage spread across clause mixes at matched (s, r) | 0.479 | findings/max_mix_break_spread |
| C15 | largest detection spread across clause mixes at matched (s, r) | 0.096 | findings/max_mix_detect_spread |
| C16 | share of changing mutations rejected by observational clauses | 1.0 | kind_ranking/0/changing_share |
| C17 | share of preserving mutations rejected by observational clauses | 0.0 | kind_ranking/0/preserving_share |
| C18 | share of changing mutations rejected by literal presence | 0.643 | kind_ranking/1/changing_share |
| C19 | share of preserving mutations rejected by literal presence | 0.0005 | kind_ranking/1/preserving_share |
| C20 | changing-to-preserving ratio for literal presence | 1388.8325 | kind_ranking/1/ratio |
| C21 | changing-to-preserving ratio for literal absence | 3.969 | kind_ranking/2/ratio |
| C22 | share of changing mutations rejected by the depth bound | 0.0 | kind_ranking/8/changing_share |
| C23 | share of changing mutations rejected by the size bound | 0.0 | kind_ranking/9/changing_share |
| C24 | share of preserving mutations rejected by the depth bound | 0.956 | kind_ranking/8/preserving_share |
| C25 | share of preserving mutations rejected by the size bound | 0.977 | kind_ranking/9/preserving_share |
| C26 | changing mutations observable clauses alone reject | 591 | mechanism_by_kind/obs/changing |
| C27 | preserving mutations observable clauses alone reject | 0 | mechanism_by_kind/obs/preserving |
| C28 | changing mutations literal presence alone rejects | 380 | mechanism_by_kind/const_present/changing |
| C29 | preserving mutations literal presence alone rejects | 1 | mechanism_by_kind/const_present/preserving |
| C30 | changing mutations the depth bound alone rejects | 0 | mechanism_by_kind/depth_le/changing |
| C31 | preserving mutations the depth bound alone rejects | 2065 | mechanism_by_kind/depth_le/preserving |
| C32 | changing mutations the size bound alone rejects | 0 | mechanism_by_kind/size_le/changing |
| C33 | preserving mutations the size bound alone rejects | 2110 | mechanism_by_kind/size_le/preserving |
| C34 | changing mutations the operator-count bound alone rejects | 2 | mechanism_by_kind/op_count_le/changing |
| C35 | changing mutations the child-operator clause alone rejects | 63 | mechanism_by_kind/child_op/changing |
| C36 | changing mutations the node-operator clause alone rejects | 104 | mechanism_by_kind/node_op/changing |
| C37 | changing mutations literal absence alone rejects | 379 | mechanism_by_kind/const_absent/changing |
| C38 | preserving mutations literal absence alone rejects | 349 | mechanism_by_kind/const_absent/preserving |
| C39 | changing mutations the root-operator clause alone rejects | 42 | mechanism_by_kind/top/changing |
| C40 | changing mutations the operator-absence clause alone rejects | 55 | mechanism_by_kind/no_op/changing |
| C41 | references whose representational menu has 29 candidates | 102 | menu_sizes/29 |
| C42 | references whose representational menu has 26 candidates | 77 | menu_sizes/26 |
| C43 | references whose representational menu has 24 candidates | 72 | menu_sizes/24 |
| C44 | references whose representational menu has 21 candidates | 2 | menu_sizes/21 |

## References

[1] Parnas, D. L. (1971). On the Criteria to Be Used in Decomposing Systems into Modules. https://doi.org/10.21236/ad0773837.
    Difference: gives the criterion for a module boundary -- hide the decision likely to change; we measure the cost of the decisions an artefact states instead of hiding

[2] Dijkstra, E. W. (1978). Guarded Commands, Nondeterminacy, and Formal Derivation of Programs. Programming Methodology. https://doi.org/10.1007/978-1-4612-6315-9_14.
    Difference: derives programs from their specification by construction; we ask what that specification costs after the program changes

[3] DeMillo, R. A.; Lipton, R. J.; Sayward, F. G. (1978). Hints on Test Data Selection: Help for the Practicing Programmer. Computer. https://doi.org/10.1109/c-m.1978.218136.
    Difference: introduced mutation as a test-data criterion; we use a mutation algebra with a semantics-preservation oracle, so the changing/preserving split is exact rather than sampled

[4] Hoare, C. A. R. (1978). An Axiomatic Basis for Computer Programming. Programming Methodology. https://doi.org/10.1007/978-1-4612-6315-9_9.
    Difference: axiomatic semantics as the basis for proving programs; strength is a proof obligation in that frame and a cost in ours

[5] Lehman, M. M. (1980). Programs, life cycles, and laws of software evolution. Proceedings of the IEEE. https://doi.org/10.1109/proc.1980.11805.
    Difference: laws of software evolution over releases -- growth and declining quality; we isolate one cost of change, the specification's exposure to representation

[6] Weyuker, E. J. (1982). On Testing Non-Testable Programs. The Computer Journal. https://doi.org/10.1093/comjnl/25.4.465.
    Difference: introduced the oracle problem for programs with no expected output; we do not need an oracle because our semantics is decidable

[7] Brooks. (1987). No Silver Bullet Essence and Accidents of Software Engineering. Computer. https://doi.org/10.1109/mc.1987.1663532.
    Difference: essential versus accidental difficulty; we give one accidental difficulty -- representation coupling -- a measurable functional form

[8] Wing, J. M. (1990). A specifier's introduction to formal methods. Computer. https://doi.org/10.1109/2.58215.
    Difference: the classical formal-methods primer; it treats specification strength as monotone, which is what we test

[9] Chidamber, S. R.; Kemerer, C. F. (1991). Towards a metrics suite for object oriented design. Conference proceedings on Object-oriented programming systems, languages, and applications. https://doi.org/10.1145/117954.117970.
    Difference: a metrics suite for object-oriented design measured against maintenance outcomes; our dependent variables are decided by an oracle rather than correlated with a proxy

[10] Meyer, B. (1992). Applying 'design by contract'. Computer. https://doi.org/10.1109/2.161279.
    Difference: contracts as predicates; strength is a single dial there, and we separate it into observational specificity and representation exposure

[11] Offutt, A. J.; Craft, W. M. (1994). Using compiler optimization techniques to detect equivalent mutants. Software Testing, Verification and Reliability. https://doi.org/10.1002/stvr.4370040303.
    Difference: detects equivalent mutants by compiler optimisation, case by case; our oracle decides equivalence over the whole input domain by construction

[12] Basili, V. R.; Briand, L. C.; Melo, W. L. (1996). A validation of object-oriented design metrics as quality indicators. IEEE Transactions on Software Engineering. https://doi.org/10.1109/32.544352.
    Difference: validates design metrics as quality indicators statistically; we define the quantity rather than validate a proxy for it

[13] Rothermel, G.; Harrold, M. J. (1996). Analyzing regression test selection techniques. IEEE Transactions on Software Engineering. https://doi.org/10.1109/32.536955.
    Difference: which tests to re-run after a change; our question is which constraints to keep, at matched detection

[14] Tichy, W. F. (1998). Should computer scientists experiment more?. Computer. https://doi.org/10.1109/2.675631.
    Difference: argues for experiment in CS; this paper is an experiment on specifications

[15] Ernst, M. D.; Cockrell, J.; Griswold, W. G.; et al. (1999). Dynamically discovering likely program invariants to support program evolution. Proceedings of the 21st international conference on Software engineering. https://doi.org/10.1145/302405.302467.
    Difference: infers invariants from executions -- a specification PROPOSER; we study what a given specification costs

[16] Leavens, G. T.; Baker, A. L.; Ruby, C. (1999). JML: A Notation for Detailed Design. Behavioral Specifications of Businesses and Systems. https://doi.org/10.1007/978-1-4615-5229-1_12.
    Difference: a notation for detailed design; a specification language, not a measurement of what using it costs

[17] Necula, G. C. (2000). Translation validation for an optimizing compiler. ACM SIGPLAN Notices. https://doi.org/10.1145/358438.349314.
    Difference: proves a compiler transformation equivalent; we ask what a specification can DETECT about one

[18] Kitchenham, B. A.; Pfleeger, S. L.; Pickard, L. M.; et al. (2002). Preliminary guidelines for empirical research in software engineering. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2002.1027796.
    Difference: the standard empirical-methodology guidelines; our controls are built to its spirit

[19] Elbaum, S.; Malishevsky, A. G.; Rothermel, G. (2002). Test case prioritization: a family of empirical studies. IEEE Transactions on Software Engineering. https://doi.org/10.1109/32.988497.
    Difference: orders tests; we order specifications by net value at a given change rate

[20] Lamport, L.; Matthews, J.; Tuttle, M.; et al. (2002). Specifying and verifying systems with TLA+. Proceedings of the 10th workshop on ACM SIGOPS European workshop: beyond the PC - EW10. https://doi.org/10.1145/1133373.1133382.
    Difference: TLA+ and its tooling -- model checking a specification; we price the specification's maintenance instead

[21] Wang, C.; Somenzi, F.; Hachtel, G. D. (2006). Abstraction Refinement for Large Scale Model Checking. Series on Integrated Circuits and Systems. https://doi.org/10.1007/0-387-34600-7.
    Difference: refinement abstracts representation away so a proof survives; we measure what the representation an artefact keeps costs

[22] Fluri, B.; Wursch, M.; PInzger, M.; et al. (2007). Change Distilling:Tree Differencing for Fine-Grained Source Code Change Extraction. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2007.70731.
    Difference: extracts fine-grained source changes; we supply the change distribution's ground-truth split into semantics-changing and semantics-preserving

[23] Ernst, M. D.; Perkins, J. H.; Guo, P. J.; et al. (2007). The Daikon system for dynamic detection of likely invariants. Science of Computer Programming. https://doi.org/10.1016/j.scico.2007.01.015.
    Difference: the Daikon implementation; our specs are constructed from a generator, not inferred

[24] Pacheco, C.; Lahiri, S. K.; Ernst, M. D.; et al. (2007). Feedback-Directed Random Test Generation. 29th International Conference on Software Engineering (ICSE'07). https://doi.org/10.1109/icse.2007.37.
    Difference: generates tests from execution feedback; we generate mutations whose semantic effect is decided rather than tests whose failure is observed

[25] Gonthier, G. (2008). The Four Colour Theorem: Engineering of a Formal Proof. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-540-87827-8_28.
    Difference: an engineering account of a large formal proof; a data point for the field's capability, not for its maintenance cost

[26] D'Silva, V.; Kroening, D.; Weissenbacher, G. (2008). A Survey of Automated Techniques for Formal Software Verification. IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems. https://doi.org/10.1109/tcad.2008.923410.
    Difference: surveys the cost of automated formal verification techniques; that cost is per proof attempt, not per legitimate change

[27] Wadler, P.; Findler, R. B. (2009). Well-Typed Programs Can’t Be Blamed. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-642-00590-9_1.
    Difference: localises type errors by blame; a specification whose failures are attributed rather than priced

[28] Leroy, X. (2009). Formal verification of a realistic compiler. Communications of the ACM. https://doi.org/10.1145/1538788.1538814.
    Difference: a verified compiler carries the preservation argument end to end; the specification is fixed once and the compiler is what changes

[29] Hassan, A. E. (2009). Predicting faults using the complexity of code changes. 2009 IEEE 31st International Conference on Software Engineering. https://doi.org/10.1109/icse.2009.5070510.
    Difference: predicts faults from the complexity of code changes; we predict false alarms from the contents of the specification that meets the change

[30] Grün, B. J. M.; Schuler, D.; Zeller, A. (2009). The Impact of Equivalent Mutants. 2009 International Conference on Software Testing, Verification, and Validation Workshops. https://doi.org/10.1109/icstw.2009.37.
    Difference: measures how many equivalent mutants a suite admits; equivalence is a nuisance to filter there and the dependent variable here

[31] Jhala, R.; Majumdar, R. (2009). Software model checking. ACM Computing Surveys. https://doi.org/10.1145/1592434.1592438.
    Difference: software model checking as a verification method; we measure the durability of what is checked

[32] Leino, K. R. M. (2010). Dafny: An Automatic Program Verifier for Functional Correctness. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-642-17511-4_20.
    Difference: an automatic program verifier; the language in which practitioners write the specifications whose exposure we measure

[33] Thummalapenta, S.; Xie, T.; Marri, M. (2011). Mining API Usage Specifications via Searching Source Code from the Web. Chapman & Hall/CRC Data Mining and Knowledge Discovery Series. https://doi.org/10.1201/b10928-11.
    Difference: mines usage specifications from source; it produces specifications, and we ask which of their clauses survive change

[34] Sen, K. (2011). DART: Directed Automated Random Testing. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-642-19237-1_4.
    Difference: directed automated random testing; it generates inputs, and we generate mutations

[35] Jia, Y.; Harman, M. (2011). An Analysis and Survey of the Development of Mutation Testing. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2010.62.
    Difference: the standard survey of mutation testing; we invert it -- mutants are our instruments, not our object of study

[36] Ball, T.; Levin, V.; Rajamani, S. K. (2011). A decade of software model checking with SLAM. Communications of the ACM. https://doi.org/10.1145/1965724.1965743.
    Difference: a decade of SLAM static driver verification at scale; the specification is a property and its maintenance is out of frame

[37] Yang, X.; Chen, Y.; Eide, E.; et al. (2012). Finding and understanding bugs in C compilers. ACM SIGPLAN Notices. https://doi.org/10.1145/2345156.1993532.
    Difference: differential testing of compilers; a change population of the same kind, without a specification axis

[38] Le Goues, C.; Nguyen, T.; Forrest, S.; et al. (2012). GenProg: A Generic Method for Automatic Software Repair. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2011.104.
    Difference: automatic program repair -- repair after a failure, whereas we price the false alarm that produced it

[39] Yoo, S.; Harman, M. (2012). Regression testing minimization, selection and prioritization: a survey. Software Testing, Verification and Reliability. https://doi.org/10.1002/stv.430.
    Difference: prices test suites by cost and detection; we price a specification by detection AND false alarms

[40] Kintis, M.; Papadakis, M.; Malevris, N. (2012). Isolating First Order Equivalent Mutants via Second Order Mutation. 2012 IEEE Fifth International Conference on Software Testing, Verification and Validation. https://doi.org/10.1109/icst.2012.160.
    Difference: isolates first-order equivalent mutants via second-order mutation; the same nuisance-filtering frame reached by a different mechanism

[41] Tristan, J. B.; Govereau, P.; Morrisett, G. (2012). Evaluating value-graph translation validation for LLVM. ACM SIGPLAN Notices. https://doi.org/10.1145/2345156.1993533.
    Difference: translation validation at scale; same question, compiler-specific instrument, no strength axis

[42] Chen, Y.; Groce, A.; Zhang, C.; et al. (2013). Taming compiler fuzzers. ACM SIGPLAN Notices. https://doi.org/10.1145/2499370.2462173.
    Difference: tests compilers against a reference; we test specifications against a decidable semantics

[43] Herzig, K.; Zeller, A. (2013). The impact of tangled code changes. 2013 10th Working Conference on Mining Software Repositories (MSR). https://doi.org/10.1109/msr.2013.6624018.
    Difference: tangled changes mix concerns and break more; a property of the change rather than of the specification meeting it

[44] Filliâtre, J. C.; Paskevich, A. (2013). Why3 — Where Programs Meet Provers. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-642-37036-6_8.
    Difference: a platform where programs meet provers; a specification language and its tooling, not a model of the specification's cost

[45] Just, R.; Jalali, D.; Inozemtseva, L.; et al. (2014). Are mutants a valid substitute for real faults in software testing?. Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering. https://doi.org/10.1145/2635868.2635929.
    Difference: asks whether mutants substitute for real faults; we ask what a specification's shape implies about which changes it will catch

[46] Luo, Q.; Hariri, F.; Eloussi, L.; et al. (2014). An empirical analysis of flaky tests. Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering. https://doi.org/10.1145/2635868.2635920.
    Difference: flaky tests as a symptom of brittleness; we make the brittleness a designed axis rather than a discovered symptom

[47] Vazou, N.; Seidel, E. L.; Jhala, R.; et al. (2014). Refinement types for Haskell. ACM SIGPLAN Notices. https://doi.org/10.1145/2692915.2628161.
    Difference: refinement types for Haskell; a specification calculus whose strength is one dial

[48] Newcombe, C.; Rath, T.; Zhang, F.; et al. (2015). How Amazon web services uses formal methods. Communications of the ACM. https://doi.org/10.1145/2699417.
    Difference: industrial evidence; we quantify the trade-off it reports anecdotally

[49] Kirchner, F.; Kosmatov, N.; Prevosto, V.; et al. (2015). Frama-C: A software analysis perspective. Formal Aspects of Computing. https://doi.org/10.1007/s00165-014-0326-7.
    Difference: a static analysis and verification platform; a tool for writing the specifications rather than a model of their maintenance

[50] Barr, E. T.; Harman, M.; McMinn, P.; et al. (2015). The Oracle Problem in Software Testing: A Survey. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2014.2372785.
    Difference: catalogues oracle-construction techniques; we ask a different question -- what a specification's own STRENGTH costs

[51] Papadakis, M.; Jia, Y.; Harman, M.; et al. (2015). Trivial Compiler Equivalence: A Large Scale Empirical Study of a Simple, Fast and Effective Equivalent Mutant Detection Technique. 2015 IEEE/ACM 37th IEEE International Conference on Software Engineering. https://doi.org/10.1109/icse.2015.103.
    Difference: a large-scale empirical study of equivalent-mutant detection; our ground truth is exact and needs no detector

[52] Segura, S.; Fraser, G.; Sanchez, A. B.; et al. (2016). A Survey on Metamorphic Testing. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2016.2532875.
    Difference: metamorphic testing sidesteps the oracle problem; we remove the oracle problem by construction instead

[53] Papadakis, M.; Henard, C.; Harman, M.; et al. (2016). Threats to the validity of mutation-based test assessment. Proceedings of the 25th International Symposium on Software Testing and Analysis. https://doi.org/10.1145/2931037.2931040.
    Difference: threats to mutation-based test assessment; our measurement answers one of them by deciding equivalence exactly

[54] Memon, A.; Gao, Z.; Nguyen, B.; et al. (2017). Taming Google-scale continuous testing. 2017 IEEE/ACM 39th International Conference on Software Engineering: Software Engineering in Practice Track (ICSE-SEIP). https://doi.org/10.1109/icse-seip.2017.16.
    Difference: continuous testing at Google scale absorbs the volume of changes; we measure the false alarms that volume produces

[55] Hales, T.; Adams, M.; Bauer, G.; et al. (2017). A Formal Proof Of The Kepler Conjecture. Forum of Mathematics, Pi. https://doi.org/10.1017/fmp.2017.1.
    Difference: a formal proof of the Kepler conjecture; the field's capability rather than the durability of the effort

[56] Breck, E.; Cai, S.; Nielsen, E.; et al. (2017). The ML test score: A rubric for ML production readiness and technical debt reduction. 2017 IEEE International Conference on Big Data (Big Data). https://doi.org/10.1109/bigdata.2017.8258038.
    Difference: a rubric for ML production readiness; a checklist rather than a law with a located optimum

[57] Ringer, T.; Yazdani, N.; Leo, J.; et al. (2018). Adapting proof automation to adapt proofs. Proceedings of the 7th ACM SIGPLAN International Conference on Certified Programs and Proofs. https://doi.org/10.1145/3167094.
    Difference: retargets proof automation so proofs survive change -- the closest prior work to ours; it repairs after the breakage and we predict the breakage from the specification's exposure

[58] Gazzola, L.; Micucci, D.; Mariani, L. (2019). Automatic Software Repair: A Survey. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2017.2755013.
    Difference: surveys automatic program repair; the repaired artefact is code, and the false alarms we price are specification failures

[59] Papadakis, M.; Kintis, M.; Zhang, J.; et al. (2019). Mutation Testing Advances: An Analysis and Survey. Advances in Computers. https://doi.org/10.1016/bs.adcom.2018.03.015.
    Difference: a survey of mutation testing advances; equivalent mutants stay a filter there and are the treatment here

[60] Ringer, T.; Palmskog, K.; Sergey, I.; et al. (2019). QED at Large: A Survey of Engineering of Formally Verified Software. https://doi.org/10.1561/9781680835953.
    Difference: documents proof-engineering cost and maintenance; we make the cost of REPRESENTATION a measurable axis

[61] Sánchez, C.; Schneider, G.; Ahrendt, W.; et al. (2019). A survey of challenges for runtime verification from advanced application domains (beyond software). Formal Methods in System Design. https://doi.org/10.1007/s10703-019-00337-w.
    Difference: runtime verification monitors a running system; a specification at runtime, not one maintained across changes

[62] The mathlib Community. (2020). The lean mathematical library. Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs. https://doi.org/10.1145/3372885.3373824.
    Difference: the Lean mathematical library; a machine-checked library whose maintenance is exactly the cost we model

[63] Gruber, M.; Lukasczyk, S.; Krois, F.; et al. (2021). An Empirical Study of Flaky Tests in Python. 2021 14th IEEE Conference on Software Testing, Verification and Validation (ICST). https://doi.org/10.1109/icst49551.2021.00026.
    Difference: same, in Python; our change population is generated, so the brittleness is not a property of one repository

[64] [Author not established on Crossref or OpenAlex for DOI 10.7551/mitpress/12440.003.0011] (2021). Technical Debt in Machine Learning Systems. Technical Debt in Practice. https://doi.org/10.7551/mitpress/12440.003.0011.
    Difference: names technical debt in ML systems; we make one class of it -- representation coupling -- measurable

[65] Paleyes, A.; Urma, R. G.; Lawrence, N. D. (2022). Challenges in Deploying Machine Learning: A Survey of Case Studies. ACM Computing Surveys. https://doi.org/10.1145/3533378.
    Difference: case studies of machine-learning deployment challenges; representation coupling is not isolated or priced

[66] Zhang, J. M.; Harman, M.; Ma, L.; et al. (2022). Machine Learning Testing: Survey, Landscapes and Horizons. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2019.2962027.
    Difference: documents ML testing practice; a different notion of specification (data, not code)

[67] Baltes, S.; Ralph, P. (2022). Sampling in software engineering research: a critical review and guidelines. Empirical Software Engineering. https://doi.org/10.1007/s10664-021-10072-8.
    Difference: how to sample a population for SE research; we enumerate our population and report bands instead

[68] Wohlin, C.; Runeson, P.; Höst, M.; et al. (2024). Experimentation in Software Engineering. https://doi.org/10.1007/978-3-662-69306-3.
    Difference: the methodology text for software-engineering experiments, which we follow; our design is enumerated rather than sampled

[69] Shi, J.; Chen, Y.; He, J.; et al. (2026). Aletheia: Permission-Minimality Testing for Coding-Agent Rules. arXiv preprint. https://arxiv.org/abs/2609.39678.
    Difference: permission-minimality testing for coding-agent rules

[70] Li, H.; Wang, Z.; Li, G.; et al. (2026). Automatically Building Machine-Checked Assurance Cases from C Codebases to Requirements. arXiv preprint. https://arxiv.org/abs/2609.40119.
    Difference: machine-checked assurance cases generated from a codebase

[71] Kissig, C.; Richards, J.; Batty, M. (2026). Episodic Loops: Finitary Event Structures and Operational Semantics for C11 Programs with Retries. arXiv preprint. https://arxiv.org/abs/2609.34646.
    Difference: operational semantics for C11 programs

[72] Jha, P.; Ghosh, A.; Ganesh, V. (2026). Towards Certificate-Driven Software Porting: A Self-Improving Agentic Harness for Scientific Program Optimization. arXiv preprint. https://arxiv.org/abs/2609.34069.
    Difference: certificate-driven software porting

[73] Song, Y.; Xie, D.; Xie, X.; et al. (2026). COMPASS: Predicting the Relationship of Multiple Patches for Vulnerabilities with LLMs. arXiv preprint. https://arxiv.org/abs/2609.39783.
    Difference: predicting relationships among vulnerability patches

[74] Bellibatlu, R. R.; Wang, Z.; Zhang, W. (2026). Do Agent Benchmarks Do What They Say? An Executable-Contract Audit of Tool-Using Agent Environments. arXiv preprint. https://arxiv.org/abs/2609.37315.
    Difference: executable-contract audit of tool-using agents

[75] Garg, A.; Yang-Smith, C.; Rishav, R.; et al. (2026). From Codebase to Culprit (C2C): Reducing the Search Space for Bugs with Semantic Retrieval and Hierarchical Reinforcement Learning. arXiv preprint. https://arxiv.org/abs/2609.38402.
    Difference: reducing a bug search space with semantic retrieval

[76] Ciobâcă, Ş.; Gratie, D. E.; Rotariu, D. I. (2026). The Formalization of two Computational Models in Dafny. arXiv preprint. https://arxiv.org/abs/2609.34883.
    Difference: two computational models formalized in Dafny

[77] Tan, G.; Chen, P.; Sun, Z.; et al. (2026). Trustworthy Runtime Error Healing in Real-World Repositories: A Benchmark and Guardrail. arXiv preprint. https://arxiv.org/abs/2609.39086.
    Difference: benchmark and guarantees for runtime error healing

[78] Dramko, L.; Le Goues, C.; Schwartz, E. (2026). Faultless: A Program Equivalence Technique for Validating and Evaluating Neural Decompilers. arXiv preprint. https://arxiv.org/abs/2609.34089.
    Difference: a program-equivalence technique for validating decompilation

[79] Abuah, C. (2026). Forte: A sensitivity type system for imperative Rust. arXiv preprint. https://arxiv.org/abs/2609.30254.
    Difference: a sensitivity type system for imperative Rust

[80] Susan, H.; Shivaranjani G. R.; Imran, M.; et al. (2026). GRADE-RTL: Evaluating LLM-Generated RTL Beyond Compilation. arXiv preprint. https://arxiv.org/abs/2609.25335.
    Difference: evaluating generated RTL beyond compilation

[81] Dağlı, V.; Dağlı, Z.; Dağlı, D. (2026). Machine-Checked Computational Group Theory in Lean 4: Operational Schreier-Sims Stabilizer Chains, BSGS Sifting, and Backtrack Ordered Partitions. arXiv preprint. https://arxiv.org/abs/2609.38492.
    Difference: machine-checked computational group theory in Lean 4

[82] Poličar, P. G.; Špendl, M.; Hočevar, T. (2026). Is manual software optimization a thing of the past?. arXiv preprint. https://arxiv.org/abs/2609.37849.
    Difference: whether manual software optimisation is still worthwhile

[83] Kurucz, Á.; Bereczky, P.; Horpácsi, D. (2026). Dependently Typed Model Composition for Matching Logic. arXiv preprint. https://arxiv.org/abs/2609.34892.
    Difference: dependently typed model composition

[84] Reuther, C.; Jacquet, J. M. (2026). Modelling Shared-Space Coordination in mCRL2: a Bach-to-mCRL2 Translation Framework. arXiv preprint. https://arxiv.org/abs/2609.37726.
    Difference: modelling shared-space coordination in mCRL2

[85] Qi, Z.; Li, H.; Chen, J.; et al. (2026). Merged, Not Measured: An Empirical Study of Performance Issues Fixed by Coding Agents. arXiv preprint. https://arxiv.org/abs/2609.37985.
    Difference: empirical study of performance fixes merged without measurement

[86] Yang, J.; Zhang, J. M.; Lou, Y.; et al. (2026). Mubric: Mutation Testing-Guided Rubric Generation for LLM Evaluation. arXiv preprint. https://arxiv.org/abs/2609.37322.
    Difference: mutation testing used to guide rubric generation

[87] Loitzl, A.; Mück, N.; Sammler, M. (2026). Multi-language Program Logics. arXiv preprint. https://arxiv.org/abs/2609.32877.
    Difference: multi-language program logics

[88] Benzmüller, C. (2026). Proofs Without Nominals: Gödel's Ontological Argument, its Shallow Embedding, and the Open Questions of the Monatshefte Notes. arXiv preprint. https://arxiv.org/abs/2609.36279.
    Difference: shallow embeddings and proofs without nominals

[89] Brănici-Faraon, A.; Ciobâcă, Ş.; Gratie, D. E. (2026). Formalizing the Omega Test in Dafny. arXiv preprint. https://arxiv.org/abs/2609.34882.
    Difference: the Omega test formalized in Dafny

[90] De Greef, R.; Engels, T.; Van den Broucke, F.; et al. (2026). Lifting the Preprocessor with Oxidize: Structure-Preserving C-to-Rust Translation (Technical Report). arXiv preprint. https://arxiv.org/abs/2609.30062.
    Difference: structure-preserving C-to-Rust translation

[91] Drǎmnesc, I.; Jebelean, T.; Stratulat, S. (2026). Certification of Bilateral Patience Sort in Theorema and Rocq. arXiv preprint. https://arxiv.org/abs/2609.34889.
    Difference: certification of a sorting algorithm in two provers

[92] Labbadi, M.; Majumdar, R.; Sathiyanarayana, V. R.; et al. (2026). Formal Reasoning about Performance Models. arXiv preprint. https://arxiv.org/abs/2609.37728.
    Difference: formal reasoning about performance models

[93] Kronlund-Drouault, P. (2026). Semantic Prefix Oracles for LLM Decoding: Contracts and Differential Validation. arXiv preprint. https://arxiv.org/abs/2609.35425.
    Difference: semantic prefix oracles and differential validation

[94] Ke, J.; Li, J.; Li, G. (2026). Irene: Equivalence Checking of Hybrid Quantum Programs via Structure-Preserving Symbolic Reduction. arXiv preprint. https://arxiv.org/abs/2609.36065.
    Difference: equivalence checking of hybrid quantum programs

[95] Lavoie, E. (2026). Designing a Producer-driven Stream Protocol by Formal Refinement. arXiv preprint. https://arxiv.org/abs/2609.33813.
    Difference: a stream protocol designed by formal refinement

[96] Ortin, F. (2026). SafeLLM4SE: Statistical Evaluation and Reporting for LLM-based Software Engineering Systems. arXiv preprint. https://arxiv.org/abs/2609.37294.
    Difference: statistical evaluation and reporting for LLM-based SE

[97] Qian, J.; Dong, Y.; Li, Y.; et al. (2026). Self-Spec Verifiable Code Generation. arXiv preprint. https://arxiv.org/abs/2609.39568.
    Difference: self-specifying verifiable code generation

[98] Caldeira, A. Z. (2026). Session Type State Spaces Form Lattices. arXiv preprint. https://arxiv.org/abs/2609.34927.
    Difference: session-type state spaces as lattices

[99] Edamana, N.; Kurur, P. P.; Cheramangalath, U. (2026). Improved Tristate Multiplication With Formalization in Rocq. arXiv preprint. https://arxiv.org/abs/2609.39009.
    Difference: a tristate multiplier formalized in Rocq

[100] Singavarapu, I. K.; Bhatt, M. (2026). A Trust Ledger and an Execution Check for CPG-Based C-to-Lean 4 Autoformalization: Separating Declined from Silently Incorrect Translations. arXiv preprint. https://arxiv.org/abs/2609.38237.
    Difference: execution check for C-to-Lean autoformalization

[101] Zhai, Y.; Chen, X.; Zhang, L.; et al. (2026). From Verification Failures to Reusable Guidance for Coding Agents. arXiv preprint. https://arxiv.org/abs/2609.39022.
    Difference: verification failures turned into reusable guidance

[102] Qin, J.; Du, A.; Zhang, D.; et al. (2026). Vosti: Specifying, Implementing, and Verifying Deterministic LLM Inference. arXiv preprint. https://arxiv.org/abs/2609.38981.
    Difference: specifying, implementing and verifying a deterministic inference pipeline
