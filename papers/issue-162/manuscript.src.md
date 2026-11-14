# Eleven Nines Is Not a Measurement

**What per-device failure rates identify about replicated loss, and what a stated dependence buys**

*Issue #162. Contribution level: `theory+empirics` — with the empirical component being exhaustive
verification over enumerated coupling polytopes, not data. There is no real-system measurement in
this paper and none is claimed.*

---

## Abstract

Operators quote durability in nines. For an `r`-replica store with per-device annual loss probability
`p`, the quoted figure is `p^r`, the probability that all `r` replicas fail **under independence**.
Given only the per-device marginals — which is all such a figure is ever computed from — the
probability that all replicas fail is not identified: it lies in an interval whose upper end is `p`
and whose lower end is `max(0, rp - (r-1))`. The quoted figure is the *rare* end of that interval,
and at every realistic quote the interval reaches the other end as well, where loss is certain.

Two consequences are exact and mechanically verified. First, the interval does not narrow as
replication improves the quote: each added replica multiplies the quote by `p` — buying `-log10 p`
more nines — while the worst identified value stays at `p`, so the span between what is quoted and
what is identified grows by exactly `-log10 p` decades per replica. At `p = 1e-4` and `r = 5`, a
quoted 20.0 nines sit above a worst identified value of 4.0 nines: a **span of 16.0 decades**, in a
grid whose widest cell (`p = 1e-5`, `r = 5`) spans 20.0. Second, stating a dependence does not close
the gap symmetrically. The natural family — a fraction `rho` of replication groups failing together —
spans `[p^r, p]` and never reaches the lower end, because reaching it would require negative
dependence, which is not a coupling. So **a stated `rho >= 0` is a statement that the quoted figure
is the best case**, and it costs one decade of the quote to buy `rho = 9e-16` at `p = 1e-4, r = 5`.
Read backwards: "eleven nines" asserts a bound `rho < ~9 p^(r-1)` on a quantity nobody measures.
`rho` is *declared* throughout this paper and never estimated; the paper contains **no data at all**,
and its empirical component is an exhaustive check that both bounds are attained, not a measurement
of any system.

## 1. The question

A durability figure quoted as `p^r` reads as a measurement. It is presented in design reviews, in
service-level objectives and in papers as the probability that a store loses everything. The
arithmetic behind it is one line, and it is the arithmetic of a *specific* joint law: independence.

The question this paper asks is not "what is the loss probability". It is:

> Given the numbers a nines figure is actually computed from, what does the figure identify?

The answer is not a number. Given `r` events each of probability `p` and nothing else, the
probability that all of them occur is bounded below by `max(0, r p - (r-1))` (inclusion–exclusion)
and above by `p` (the intersection is contained in each event). Both bounds are classical, both are
attained, and the pair is the tightest statement the marginals support. The quoted figure `p^r` is
the value of that probability under exactly one coupling: the independent one.

So the figure is a *point inside an interval*, chosen by an assumption the figure does not state, and
at realistic parameters the interval's other end is not a small number. The remainder of the paper
prices that interval in the unit the quote is made in, shows the pricing is exact, and shows what
stating a dependence buys.

## 2. The object, and what it identifies

Given marginals, the object is the set of joint laws with those marginals — the Fréchet class — and
its extreme members are the classical bounds. That set, not a point, is what the marginals determine
{{c:frechet-class}}. For an intersection of `r` events the lower extreme is the inclusion–exclusion
bound, and the statistics literature's business there has been to sharpen that bound rather than to
question the framing: improved Bonferroni inequalities, sharp forms, and graph-theoretic
generalisations are all refinements of the same inequality {{c:bonferroni-lower}}.

That literature is not this paper's competitor; it is this paper's premise. What it does not do is
take a *published reliability figure* — a number someone quotes as a promise — and ask which member
of the class it is. The applied literature computes bounds for dependent risks in order to optimise
under them, and it treats the bound as a tool for allocation rather than as a statement about a
quoted number {{c:bounds-stated-not-attained}}.

The further fact this paper adds is that the bounds are **attained**, on a finite space, with every
marginal exactly `p`. A bound that no coupling attains would be a statement about nothing: every
coupling satisfies it, so it separates none of them. Attainment is what converts "the figure is in an
interval" into "the figure is at the *best* end of an interval whose other end is reachable".

## 3. Correlation is measured, not hypothetical

The claim that dependence matters is not a thought experiment. Production data shows correlated
failure across every layer that a replication argument assumes independent: latent sector errors and
data corruption within a disk population, whole-rack and whole-cluster correlated failures,
geographically correlated network failures, and grid outage statistics
{{c:correlation-measured}}.

The consequence has been known in the failure-mode literature for decades: under common-cause
failure, adding replicas is not a monotone improvement, and the standard apparatus — common-cause
models, shared-cause parameters, k-out-of-n systems with correlated failures — exists to price
exactly that {{c:redundancy-defeated}}. Systems work has reached the same conclusion from the design
side. The copyset line accepts a dependence model as an input, constrains which replicas may fail
together, and computes the resulting loss rate {{c:placement-under-correlation}}. Quorum systems make
the trade in the availability direction, with probabilistic quorum variants introduced because
availability depends on which nodes fail together {{c:quorum-availability}}.

**The difference this paper claims is narrow, and it is in the reporting layer.** Those lines assume
a dependence and compute what follows; this paper assumes none and computes what *not assuming* one
leaves undetermined — and then prices the missing input in the quote's own unit. A design that
constrains correlated failure answers "what should we build"; the question here is "what did the
number we published say", and it is answerable without any of the design machinery.

## 4. Where the quoted number comes from

A durability figure is produced by a model whose inputs are per-device rates and whose arithmetic is
the independence product: mean-time-to-data-loss computations for replicated and erasure-coded
stores, RAID analyses, and the reliability sections of storage systems papers all instantiate it
{{c:durability-models}}. Erasure coding changes the arithmetic and a great deal of the engineering —
it lowers the redundancy cost of a given tolerance under the same independence assumption — without
changing what the marginals identify {{c:erasure-arithmetic}}.

The result is then published as a promise: a durability or availability claim in a service-level
objective, an object-storage redundancy description, or a contract
{{c:sla-promise}}. The reader of that promise is a customer, not a reviewer, and the promise is read
as a measurement of the store. That gap — between what the number is (a value under one coupling) and
how it is read (a property of the store) — is the whole subject of this paper.

## 5. Why this paper does not estimate the dependence

There is an obvious alternative to bounding: estimate the joint law from data. This paper does not,
and the reason is not convenience.

Estimating a probability at the far tail is a research programme with its own assumptions:
importance sampling and rare-event simulation, extreme-value extrapolation, large-deviation and
Chernoff-type bounds — each of which is a *model of the tail* being extrapolated into
{{c:rare-event-cost}}. A nines figure is 10 or more decades beyond anything a deployment observes, so
"estimate `rho` from data" does not replace an assumption with a measurement; it replaces a stated
assumption with an unstated one.

Nor is the assumption-free framing idle. The reliability-reporting literature already recognises that
a quoted failure probability inherits its assumptions and treats the question as sensitivity analysis
{{c:assumption-sensitivity}}, and outside engineering the same arithmetic has a name: diversification
computed under one coupling fails under another, and zero correlation is not independence
{{c:diversification-fallacy}}. What is missing in both places is the specific object this paper
supplies: the *identified set* of the quoted quantity, with the quote located at a named end of it.

**Therefore `rho` is a declared parameter in everything that follows.** No value of `rho` in this
paper is fitted, and any sentence in which `rho` appears is conditional: *if* the dependence were
`rho`, the figure would be `rho p + (1-rho) p^r`. The paper has no data and claims none.

## 6. The span, and the boundary that must be excluded

The identified set and the quote, in the unit a nines figure is made in (`nines = -log10` of a
probability):

{{grid}}

The table is rendered from the instrument's artefact (`nines_findings.json`), not typed; the numbers
below are its cells.

**The span law.** The quote is `p^r` and the worst identified value is `p`, so the span in nines is
`-log10(p^r) - (-log10 p) = (r-1)(-log10 p)`. Each added replica buys `-log10 p` more nines and
widens the unidentified span by exactly the same amount. The figure improves exactly as fast as its
identification degrades — which is the paper's first registered prior, and it is met in every
non-boundary cell.

**The rare end.** The quote is not in the middle of the set; it is at the end that assumes
independence. At `p = 1e-4, r = 5` the quote is 20.0 nines and the worst identified value is 4.0:
16.0 decades apart. Reading only the quote, a store looks 16 decades safer than the marginals can
establish.

**The catastrophic end.** Total loss is excluded by the marginals exactly when
`p > (r-1)/r`, decided in exact rational arithmetic so that the boundary case
`p = (r-1)/r` (for example `p = 1/2, r = 2`) closes *at* zero rather than above it. Since a
per-device annual loss probability is small and `r >= 2`, that condition never holds at a realistic
quote: the set always contains total loss. In the grid, 16 of the 20 cells reach it; the four that do
not are the four boundary cells.

**The boundary.** At `r = 1` there is no coupling to choose: the set is the single point `p`, the span
is exactly 0, and the quote equals the truth. That row is why the widest-cell selector must exclude
`r = 1` *by name*. A selector that takes a signed difference and maximises it would pick that row —
the one cell where nothing is at stake — instead of the widest real span; the instrument carries a
plant that demonstrates exactly that failure.

**What stating a dependence buys.** `mixture(p, r, rho) = rho p + (1-rho) p^r` is affine in `rho`, so
the inverse is closed: to make the quoted figure come out at `target` one would have to state

    rho = (target - p^r) / (p - p^r),

which lies in `[0, 1]` exactly when `target` lies in `[p^r, p]`. Below `p^r` the required `rho` is
negative — anti-correlated replication, which is not a coupling and therefore not available in this
family — and above `p` it exceeds full correlation. Both are refused rather than clamped, because a
clamp would answer with a `rho` outside `[0,1]` and call it a dependence. Costing `d` decades
therefore costs `rho = (10^d - 1) p^r / (p - p^r) = (10^d - 1) p^(r-1) / (1 - p^(r-1))`, the second
form asserted exactly in the instrument's self-test: at a realistic quote the denominator is 1 to any
precision, so **one decade costs about `9 p^(r-1)`** — `9e-16` at `p = 1e-4, r = 5`, and `9e-20` at
the widest cell in the table.

Two readings of that number, and the second is the paper's point. Forwards: a dependence far too
small to rule out destroys a decade of the figure. Backwards: the quote *asserts* a bound on a
quantity that no one measures.

## 7. Verification: bounds that are attained, not cited

A bound about nothing separates nothing, so the instrument establishes attainment rather than citing
it, by three routes that must agree and cannot share a mistake:

1. **Exhaustive.** Enumerate every integer assignment of `N` atoms to the `2^r` membership types with
   each event holding exactly `a` atoms. The constraint matrix is a 0/1 incidence matrix, hence
   totally unimodular, hence its vertices are integral, hence the integer points *are* the vertices of
   the coupling polytope — so "no coupling attains anything outside this interval" is a statement
   about **all** couplings, not about the ones built here. The leg declares a node budget and reports
   NOT RUN (exit 3) when the budget is short, because a search that silently stops reports the size of
   its own search as a property of the world.
2. **Constructed.** An explicit coupling for arbitrary `(r, N, a)` — `m` atoms in every event, the
   remaining incidences handed out in chunks of `r-1` from a cycle of period `r` — verified against
   the closed form and raising if its own marginals or all-fail count disagree. Covers the `r` the
   enumeration cannot reach.
3. **Unpruned composition.** A brute-force enumerator with no pruning agrees on a further set of
   instances.

The self-test additionally carries one plant per control: a defect of the same shape as the claim,
run through the same predicate, which must be refused. A control that has never been shown to fail on
the defect it names is not a control.

## 8. Threats to validity

**This is arithmetic, not measurement.** Nothing here says what `rho` a real deployment has, and the
paper would be wrong to say so. A reader who wants the loss probability of a particular store gets
nothing from this paper except the statement that the quoted figure does not provide it without an
additional input.

**The bounds are classical.** Fréchet (1935) and the Bonferroni/inclusion–exclusion inequality are
not new, and a reviewer may fairly say the mathematical content is a re-derivation. The paper's claim
is deliberately thinner than novelty in the mathematics: it is that the *published* quantity sits at a
named end of its own identified set, that the set's other end is reachable, and — the part we have not
seen stated — that the price of being wrong is `9 p^(r-1)` in the quote's own unit. If that pricing is
standard somewhere, this paper is a restatement and should be judged as one.

**The dependence family is one family.** `rho` as a fraction of groups failing together is a modelling
choice, not a canonical one. Its two endpoints are canonical (independence, comonotonicity); its
interior is a convention. The results that do not depend on the convention are the identified set,
the span law, the total-loss condition, and the fact that the family's floor is `p^r` — the last of
which is a statement about *any* coupling family parameterised by non-negative dependence.

**No sensitivity figure is reported, because there is no measurement.** The minimum detectable effect
of a study is a property of its data; this paper has none. What replaces it is the resolution the
*quote* implies: a reader can hold a vendor to `rho < ~9 p^(r-1)` without any data at all, and that is
the strongest form of the result.

**Why it is still worth publishing.** The failure mode is not that someone computed `p^r`; it is that
a design review treats `p^r` as a property of a store while the number is a property of an assumption.
Naming the assumption, locating the quote at an end of the identified set, and pricing the missing
input in the unit the promise is made in turns a rhetorical question into an arithmetic one.

## 9. Registered priors, and how they fared

Three priors were registered before the instrument ran.

- **B1 — the quote improves as fast as its identification degrades**: the span grows by exactly
  `-log10 p` decades per replica. *Met*: it is the span law, asserted in every non-boundary cell of the
  table and planted against the wrong law (`r*k` instead of `(r-1)*k`), which the same predicate
  refuses.
- **B2 — the span is zero exactly when there is no coupling to choose**: at `r = 1` the set is a point,
  the span is exactly 0 and the quote equals the truth. *Met*, and the prior was written so that a
  failure would indict the instrument rather than the world; the boundary row is in the table, and its
  exclusion from the widest-cell selector is itself controlled.
- **B3 — the identified set contains total loss at every realistic quote**: `p <= (r-1)/r`. *Met*, and
  sharpened during the work: the condition is now decided in exact rationals for *every* quote rather
  than counted over a grid, with the boundary case shown to close at zero.

Two facts the registration did not anticipate. The stated-dependence family spans only `[p^r, p]`, so
the half-interval below the quote is unreachable without negative dependence — which converts a
sensitivity parameter into a statement about the quote being a *best case*. And the inverse exists in
closed form, which is what makes the dependence priceable in nines rather than only in probability.

## 10. Reproduction

Everything in this paper is produced by `nines.py` from no input: exact rational arithmetic over a
declared grid, no download, no corpus, no seed.

```sh
./nines.py --selftest --grid --emit nines_findings.json
```

The command, the expected verdict line and the three-state exit contract (0 green, 1 a control failed,
3 NOT RUN) are in `README.md`. The reference corpus is assembled by `harvest_refs.py` from registry
responses — every record re-fetched by DOI and corroborated by a field that is not the title — and
`gate_citations.py` binds each citation to a claim that owns it, so a citation cannot be added without
one. The counts those programs print carry their own denominators; this section deliberately quotes
none, because a count typed into a document and a count printed by a program drift apart, and the
printed one is the one that cannot.

{{refs}}
