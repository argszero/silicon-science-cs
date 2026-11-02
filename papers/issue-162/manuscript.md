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
[58, 164, 193, 183, 171, 117]. For an intersection of `r` events the lower extreme is the inclusion–exclusion
bound, and the statistics literature's business there has been to sharpen that bound rather than to
question the framing: improved Bonferroni inequalities, sharp forms, and graph-theoretic
generalisations are all refinements of the same inequality [78, 93, 112, 161, 170, 176, 179, 181, 192, 51, 63, 64, 65, 143, 118, 24, 25, 26, 27, 124].

That literature is not this paper's competitor; it is this paper's premise. What it does not do is
take a *published reliability figure* — a number someone quotes as a promise — and ask which member
of the class it is. The applied literature computes bounds for dependent risks in order to optimise
under them, and it treats the bound as a tool for allocation rather than as a statement about a
quoted number [7, 45, 54, 184, 137, 67, 56, 71, 133, 194, 107, 52, 61, 68, 60, 201, 126].

The further fact this paper adds is that the bounds are **attained**, on a finite space, with every
marginal exactly `p`. A bound that no coupling attains would be a statement about nothing: every
coupling satisfies it, so it separates none of them. Attainment is what converts "the figure is in an
interval" into "the figure is at the *best* end of an interval whose other end is reachable".

## 3. Correlation is measured, not hypothetical

The claim that dependence matters is not a thought experiment. Production data shows correlated
failure across every layer that a replication argument assumes independent: latent sector errors and
data corruption within a disk population, whole-rack and whole-cluster correlated failures,
geographically correlated network failures, and grid outage statistics
[29, 30, 195, 200, 4, 69, 70, 156, 151, 157, 174, 144, 104, 33, 109, 130, 196, 76].

The consequence has been known in the failure-mode literature for decades: under common-cause
failure, adding replicas is not a monotone improvement, and the standard apparatus — common-cause
models, shared-cause parameters, k-out-of-n systems with correlated failures — exists to price
exactly that [106, 12, 72, 73, 74, 146, 147, 83, 84, 85, 40, 15, 11, 13, 8, 9, 14, 163, 198, 199, 90, 96, 16, 129, 108, 113, 10]. Systems work has reached the same conclusion from the design
side. The copyset line accepts a dependence model as an input, constrains which replicas may fail
together, and computes the resulting loss rate [97, 121, 134, 135, 136, 32, 37, 6, 47, 105, 123, 50]. Quorum systems make
the trade in the availability direction, with probabilistic quorum variants introduced because
availability depends on which nodes fail together [152, 5, 185, 188, 189, 191, 190, 114, 115, 122, 66, 35].

**The difference this paper claims is narrow, and it is in the reporting layer.** Those lines assume
a dependence and compute what follows; this paper assumes none and computes what *not assuming* one
leaves undetermined — and then prices the missing input in the quote's own unit. A design that
constrains correlated failure answers "what should we build"; the question here is "what did the
number we published say", and it is answerable without any of the design machinery.

## 4. Where the quoted number comes from

A durability figure is produced by a model whose inputs are per-device rates and whose arithmetic is
the independence product: mean-time-to-data-loss computations for replicated and erasure-coded
stores, RAID analyses, and the reliability sections of storage systems papers all instantiate it
[160, 158, 159, 127, 120, 102, 101, 48, 177, 178, 187, 202, 203, 125, 2, 20]. Erasure coding changes the arithmetic and a great deal of the engineering —
it lowers the redundancy cost of a given tolerance under the same independence assumption — without
changing what the marginals identify [77, 205, 186, 169, 91, 110, 82, 175, 3, 49, 119, 139, 62].

The result is then published as a promise: a durability or availability claim in a service-level
objective, an object-storage redundancy description, or a contract
[21, 41, 154, 150, 23, 173, 182, 180, 1, 19, 59, 148, 149]. The reader of that promise is a customer, not a reviewer, and the promise is read
as a measurement of the store. That gap — between what the number is (a value under one coupling) and
how it is read (a property of the store) — is the whole subject of this paper.

## 5. Why this paper does not estimate the dependence

There is an obvious alternative to bounding: estimate the joint law from data. This paper does not,
and the reason is not convenience.

Estimating a probability at the far tail is a research programme with its own assumptions:
importance sampling and rare-event simulation, extreme-value extrapolation, large-deviation and
Chernoff-type bounds — each of which is a *model of the tail* being extrapolated into
[22, 42, 88, 46, 31, 141, 140, 142, 94, 168, 103, 206, 79, 80, 116, 89, 18, 138, 131, 86]. A nines figure is 10 or more decades beyond anything a deployment observes, so
"estimate `rho` from data" does not replace an assumption with a measurement; it replaces a stated
assumption with an unstated one.

Nor is the assumption-free framing idle. The reliability-reporting literature already recognises that
a quoted failure probability inherits its assumptions and treats the question as sensitivity analysis
[75, 39, 17, 55, 98, 99, 100, 162, 197, 145, 172, 87, 92, 34, 128, 167, 95, 57, 155, 111], and outside engineering the same arithmetic has a name: diversification
computed under one coupling fails under another, and zero correlation is not independence
[43, 44, 166, 204, 165, 53, 153, 36, 132, 38, 28, 81]. What is missing in both places is the specific object this paper
supplies: the *identified set* of the quoted quantity, with the quote located at a named end of it.

**Therefore `rho` is a declared parameter in everything that follows.** No value of `rho` in this
paper is fitted, and any sentence in which `rho` appears is conditional: *if* the dependence were
`rho`, the figure would be `rho p + (1-rho) p^r`. The paper has no data and claims none.

## 6. The span, and the boundary that must be excluded

The identified set and the quote, in the unit a nines figure is made in (`nines = -log10` of a
probability):

| per-device p | r | quoted | worst identified | nines quoted | nines at worst | span (decades) | set reaches total loss |
|---|---|---|---|---|---|---|---|
| 1e-2 | 1 | 1.00e-02 | 1.00e-02 | 2.0 | 2.0 | 0.0 | no |
| 1e-2 | 2 | 1.00e-04 | 1.00e-02 | 4.0 | 2.0 | 2.0 | yes |
| 1e-2 | 3 | 1.00e-06 | 1.00e-02 | 6.0 | 2.0 | 4.0 | yes |
| 1e-2 | 4 | 1.00e-08 | 1.00e-02 | 8.0 | 2.0 | 6.0 | yes |
| 1e-2 | 5 | 1.00e-10 | 1.00e-02 | 10.0 | 2.0 | 8.0 | yes |
| 1e-3 | 1 | 1.00e-03 | 1.00e-03 | 3.0 | 3.0 | 0.0 | no |
| 1e-3 | 2 | 1.00e-06 | 1.00e-03 | 6.0 | 3.0 | 3.0 | yes |
| 1e-3 | 3 | 1.00e-09 | 1.00e-03 | 9.0 | 3.0 | 6.0 | yes |
| 1e-3 | 4 | 1.00e-12 | 1.00e-03 | 12.0 | 3.0 | 9.0 | yes |
| 1e-3 | 5 | 1.00e-15 | 1.00e-03 | 15.0 | 3.0 | 12.0 | yes |
| 1e-4 | 1 | 1.00e-04 | 1.00e-04 | 4.0 | 4.0 | 0.0 | no |
| 1e-4 | 2 | 1.00e-08 | 1.00e-04 | 8.0 | 4.0 | 4.0 | yes |
| 1e-4 | 3 | 1.00e-12 | 1.00e-04 | 12.0 | 4.0 | 8.0 | yes |
| 1e-4 | 4 | 1.00e-16 | 1.00e-04 | 16.0 | 4.0 | 12.0 | yes |
| 1e-4 | 5 | 1.00e-20 | 1.00e-04 | 20.0 | 4.0 | 16.0 | yes |
| 1e-5 | 1 | 1.00e-05 | 1.00e-05 | 5.0 | 5.0 | 0.0 | no |
| 1e-5 | 2 | 1.00e-10 | 1.00e-05 | 10.0 | 5.0 | 5.0 | yes |
| 1e-5 | 3 | 1.00e-15 | 1.00e-05 | 15.0 | 5.0 | 10.0 | yes |
| 1e-5 | 4 | 1.00e-20 | 1.00e-05 | 20.0 | 5.0 | 15.0 | yes |
| 1e-5 | 5 | 1.00e-25 | 1.00e-05 | 25.0 | 5.0 | 20.0 | yes |

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

## References

1. Achary R. (2021) Reliability and High Availability Analysis for Cloud Datacenter. *Cloud Reliability Engineering*. doi:10.1201/9781003030973-2

2. Aguilera M.K. (2017) Multi-Data Center Replication Protocols. *Encyclopedia of Database Systems*. doi:10.1007/978-1-4899-7993-3_80641-1

3. Albano M. (2009) Distributed Erasure Coding in Data Centric Storage for wireless sensor networks. *2009 IEEE Symposium on Computers and Communications*. doi:10.1109/iscc.2009.5202250

4. Ali S.M. (2018) Fault Tolerance of Data Center under Multi-Correlated Failures. *2018 International Symposium on Recent Advances in Electrical Engineering (RAEE)*. doi:10.1109/raee.2018.8706892

5. Amir Y. (1998) Optimal availability quorum systems: Theory and practice. *Information Processing Letters*. doi:10.1016/s0020-0190(98)00017-9

6. Amjad T. (2010) An Application of Bayesian Theorem for Optimal Replica Placement in Data Grids. *Informatics*. doi:10.2316/p.2010.724-051

7. Anastassiou G.A. (1997) Optimal Bounds on the Average of a Rounded off Observation in the Presence of a Single Moment Condition. *Distributions with given Marginals and Moment Problems*. doi:10.1007/978-94-011-5532-8_1

8. anon. (1964) How much does redundancy improve reliability?. *Microelectronics Reliability*. doi:10.1016/0026-2714(64)90260-4

9. anon. (1964) Optimum redundancy when components are subject to two kinds of failure. *Microelectronics Reliability*. doi:10.1016/0026-2714(64)90183-0

10. anon. (1979) A common cause-failure availability model. *Microelectronics Reliability*. doi:10.1016/0026-2714(79)90195-1

11. anon. (1983) Linearly correlated intermittent failures. *Microelectronics Reliability*. doi:10.1016/0026-2714(83)91230-1

12. anon. (1988) Correlated failures in fault-tolerant computers. *Microelectronics Reliability*. doi:10.1016/0026-2714(88)90195-3

13. anon. (1988) Reliability of a system for Markov-dependent components. *Microelectronics Reliability*. doi:10.1016/0026-2714(88)90062-5

14. anon. (1990) Redundancy strategy for dependent subsystems. *Microelectronics Reliability*. doi:10.1016/0026-2714(90)90489-a

15. anon. (1992) Redundancy optimization of k--n systems with common-cause failures. *Microelectronics Reliability*. doi:10.1016/0026-2714(92)90164-g

16. anon. (1998) The Betaplus Common Cause Failure Model. *Safety and Reliability*. doi:10.1080/09617353.1998.11690672

17. anon. (2003) Concepts of Probability Theory For Sensitivity And Uncertainty Analysis. *Sensitivity &amp; Uncertainty Analysis, Volume 1*. doi:10.1201/9780203498798.ch2

18. anon. (2006) Estimation of the Probability of a Failure Set. *Springer Series in Operations Research and Financial Engineering*. doi:10.1007/0-387-34471-3_8

19. anon. (2017) Continuous Availability and Replication. *Data Protection*. doi:10.4324/9781315169620-10

20. anon. (2019) Multi-data Center Replication. *Encyclopedia of Big Data Technologies*. doi:10.1007/978-3-319-77525-8_100219

21. - V.R.I. (2020) Azure Storage Redundancy: Ensuring Availability and Durability in Hybrid Cloud Environments. *International Journal For Multidisciplinary Research*. doi:10.36948/ijfmr.2020.v02i04.39038

22. Asmussen S. (2006) Improved algorithms for rare event simulation with heavy tails. *Advances in Applied Probability*. doi:10.1239/aap/1151337084

23. AUBINEAU B. (2012) Cloud Storage. *Industrie du futur*. doi:10.51257/a-v1-h6010

24. anon. (2016) Bivariate Lower Bounds. *Multivariate Bonferroni-Type Inequalities*. doi:10.1201/b17163-12

25. anon. (2016) Bivariate Upper Bounds. *Multivariate Bonferroni-Type Inequalities*. doi:10.1201/b17163-10

26. anon. (2016) Multivariate and Hybrid Upper Bounds. *Multivariate Bonferroni-Type Inequalities*. doi:10.1201/b17163-11

27. anon. (2016) Multivariate and Hybrid Lower Bounds. *Multivariate Bonferroni-Type Inequalities*. doi:10.1201/b17163-13

28. Badikov S. (2016) No-Arbitrage Bounds for the Forward Smile Given Marginals. *SSRN Electronic Journal*. doi:10.2139/ssrn.2755274

29. Bairavasundaram L.N. (2007) An analysis of latent sector errors in disk drives. *ACM SIGMETRICS Performance Evaluation Review*. doi:10.1145/1269899.1254917

30. Bairavasundaram L.N. (2008) An analysis of data corruption in the storage stack. *ACM Transactions on Storage*. doi:10.1145/1416944.1416947

31. Balesdent M. (2014) Rare Event Probability Estimation in the Presence of Epistemic Uncertainty on Input Probability Distribution Parameters. *Methodology and Computing in Applied Probability*. doi:10.1007/s11009-014-9411-x

32. Bansal S. (2011) A Dynamic Replica Placement Algorithm to Enhance Multiple Failures Capability in Distributed System. *International Journal of Distributed and Parallel systems*. doi:10.5121/ijdps.2011.2607

33. Barrera J. (2023) Communication Network Reliability under geographically correlated failures using Probabilistic Seismic Hazard Analysis. doi:10.36227/techrxiv.20954647.v2

34. Barros A.K. (2000) The Independence Assumption: Dependent Component Analysis. *Perspectives in Neural Computing*. doi:10.1007/978-1-4471-0443-8_4

35. Basmadjian R. (2026) Availability, Load, and Energy Cost of Quorum-based Replication Protocols: A Comprehensive Survey. doi:10.2139/ssrn.6904050

36. Belak C. (2014) Worst-case optimal investment with a random number of crashes. *Statistics &amp; Probability Letters*. doi:10.1016/j.spl.2014.03.021

37. Benoit A. (2012) Optimal Algorithms and Approximation Algorithms for Replica Placement with Distance Constraints in Tree Networks. *2012 IEEE 26th International Parallel and Distributed Processing Symposium*. doi:10.1109/ipdps.2012.95

38. Bernard C. (2013) Bounds on Capital Requirements for Bivariate Risk with Given Marginals and Partial Information on the Dependence. doi:10.2139/ssrn.2335391

39. Berner C. (2016) Strengthening quantitative risk assessments by systematic treatment of uncertain assumptions. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2015.10.009

40. Bhattacharya A. (1991) Redundancy optimization problems for systems with dependent failure rates. *Microelectronics Reliability*. doi:10.1016/0026-2714(91)90296-j

41. Bosse S. (2015) Optimizing IT Service Costs with Respect to the Availability Service Level Objective. *2015 10th International Conference on Availability, Reliability and Security*. doi:10.1109/ares.2015.11

42. Botev Z.I. (2016) An M-estimator for rare-event probability estimation. *2016 Winter Simulation Conference (WSC)*. doi:10.1109/wsc.2016.7822103

43. Bürgi R. (2009) Risk Aggregation, Dependence Structure and Diversification Benefit. doi:10.2139/ssrn.1468526

44. Bush R. (2019) The Fallacy of Currency Diversification: <i>How Zero Correlation Can Still Add Risk</i>. *The Journal of Investing*. doi:10.3905/joi.2019.1.097

45. Butucea C. (2018) Maximum entropy distribution of order statistics with given marginals. *Bernoulli*. doi:10.3150/16-bej868

46. Chan H.P. (2012) Rare-Event Simulation of Heavy-Tailed Random Walks by Sequential Importance Sampling and Resampling. *Advances in Applied Probability*. doi:10.1239/aap/1354716593

47. Chang T.Y. (2012) An Optimal Replica Placement Algorithm for Symphony P2P Networks. *2012 Fifth International Symposium on Parallel Architectures, Algorithms and Programming*. doi:10.1109/paap.2012.29

48. Chan-Ik Park (1995) Efficient placement of parity and data to tolerate two disk failures in disk array systems. *IEEE Transactions on Parallel and Distributed Systems*. doi:10.1109/71.476189

49. Charles D. (2009) Hierarchical Erasure coding for P2P storage. *2009 IEEE Pacific Rim Conference on Communications, Computers and Signal Processing*. doi:10.1109/pacrim.2009.5291245

50. Chaubey M. (2015) Replicated Data Placement for Uncertain Scheduling. *2015 IEEE International Parallel and Distributed Processing Symposium Workshop*. doi:10.1109/ipdpsw.2015.50

51. Chen T. (1996) Multivariate Bonferroni-type lower bounds. *Journal of Applied Probability*. doi:10.2307/3215354

52. Cheung K.C. (2010) Characterizing a comonotonic random vector by the distribution of the sum of its components. *Insurance: Mathematics and Economics*. doi:10.1016/j.insmatheco.2010.06.004

53. Chichilnisky G. (2009) Catastrophic Risk. doi:10.2139/ssrn.1375632

54. Cicalese F. (2017) How to find a joint probability distribution of minimum entropy (almost) given the marginals. *2017 IEEE International Symposium on Information Theory (ISIT)*. doi:10.1109/isit.2017.8006914

55. Connors D. (1984) The variability of system failure probability. *Reliability Engineering*. doi:10.1016/0143-8174(84)90045-3

56. Cossette H. (2014) A note on the computation of sharp numerical bounds for the distribution of the sum, product or ratio of dependent risks. *Journal of Multivariate Analysis*. doi:10.1016/j.jmva.2014.04.023

57. Cronvall O. (2012) A study on the effect of flaw detection probability assumptions on risk reduction achieved by non-destructive inspection. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2012.03.012

58. Dall’aglio G. (1991) Frechet Classes: The Beginnings. *Advances in Probability Distributions with Given Marginals*. doi:10.1007/978-94-011-3466-8_1

59. de Guise P. (2020) Continuous Availability, Replication, and CDP. *Data Protection*. doi:10.1201/9780367463496-10

60. De Meyer H. (2007) On the transitivity of the comonotonic and countermonotonic comparison of random variables. *Journal of Multivariate Analysis*. doi:10.1016/j.jmva.2005.05.007

61. Denuit M. (2007) Comonotonic bounds on the survival probabilities in the Lee–Carter model for mortality projection. *Journal of Computational and Applied Mathematics*. doi:10.1016/j.cam.2006.03.015

62. Djouama A. (2026) MobiCloud: Reliability-Aware Coordination and Adaptive Erasure Coding for Minimal Infrastructure Smartphone Storage Clusters. doi:10.2139/ssrn.7429824

63. Dohmen K. (2002) Improved Inclusion-Exclusion Identities and Bonferroni Inequalities with Reliability Applications. *SIAM Journal on Discrete Mathematics*. doi:10.1137/s0895480101392630

64. Dohmen K. (2003) 3 Bonferroni Inequalities via Abstract Tubes. *Lecture Notes in Mathematics*. doi:10.1007/978-3-540-39399-3_3

65. Dohmen K. (2003) Improved Bonferroni Inequalities via Abstract Tubes. *Lecture Notes in Mathematics*. doi:10.1007/b13785

66. Dong H. (2024) Asynchronous Consensus Quorum Read: Pioneering Read Optimization for Asynchronous Consensus Protocols. *Electronics*. doi:10.3390/electronics13030481

67. Durante F. (2008) Bounds for Trivariate Copulas with Given Bivariate Marginals. *Journal of Inequalities and Applications*. doi:10.1155/2008/161537

68. Ekeland I. (2008) Comonotonic Measures of Multivariate Risks. doi:10.2139/ssrn.1115729

69. Ekisheva S. (2015) North American AC circuit outage rates and durations in assessment of transmission system reliability and availability. *2015 IEEE Power &amp; Energy Society General Meeting*. doi:10.1109/pesgm.2015.7285782

70. Ekisheva S. (2017) Outage statistics, reliability and availability of DC circuits in North American Bulk Power System. *2017 IEEE Power &amp; Energy Society General Meeting*. doi:10.1109/pesgm.2017.8274442

71. Embrechts P. (2010) Bounds for the sum of dependent risks having overlapping marginals. *Journal of Multivariate Analysis*. doi:10.1016/j.jmva.2009.07.004

72. Fiondella L. (2010) Estimating system reliability with correlated component failures. *International Journal of Reliability and Safety*. doi:10.1504/ijrs.2010.032445

73. Fiondella L. (2014) Recovery block fault tolerance considering correlated failures. *2014 Reliability and Maintainability Symposium*. doi:10.1109/rams.2014.6798525

74. Fiondella L. (2014) Reliability of two failure mode systems subject to correlated failures. *2014 Reliability and Maintainability Symposium*. doi:10.1109/rams.2014.6798438

75. Flage R. (2020) Assumptions in quantitative risk assessments: When explicit and when tacit?. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2020.106799

76. Franklin P.H. (2017) Predicting disk drive failure using condition based monitoring. *2017 Annual Reliability and Maintainability Symposium (RAMS)*. doi:10.1109/ram.2017.7889647

77. Fu Y. (2015) EC-FRM: An Erasure Coding Framework to Speed Up Reads for Erasure Coded Cloud Storage Systems. *2015 44th International Conference on Parallel Processing*. doi:10.1109/icpp.2015.57

78. Galambos J. (1977) Bonferroni Inequalities. *The Annals of Probability*. doi:10.1214/aop/1176995765

79. Galambos J. (1988) 1. Failure models via extreme value theory. *Advances in Applied Probability*. doi:10.1017/s000186780001764x

80. Galambos J. (1988) 2. Inequalities in extreme value theory. *Advances in Applied Probability*. doi:10.1017/s0001867800017651

81. Galichon A. (2011) A Stochastic Control Approach to No-Arbitrage Bounds Given Marginals, with an Application to Lookback Options. *SSRN Electronic Journal*. doi:10.2139/ssrn.1912477

82. Gan Y. (2024) Erasure Coding Based Optimization in Decentralized Distributed Storage Systems. *2024 International Conference on Networking, Architecture and Storage (NAS)*. doi:10.1109/nas63802.2024.10781352

83. Goel L. (1992) A warm standby redundant system with correlated failures and repairs. *Microelectronics Reliability*. doi:10.1016/0026-2714(92)90044-l

84. Goel L. (1993) A two unit series system with correlated failures and repairs. *Microelectronics Reliability*. doi:10.1016/0026-2714(93)90010-v

85. Goel L. (1994) An inspection policy for unrevealed failures in a two-unit cold standby system subject to correlated failures and repairs. *Microelectronics Reliability*. doi:10.1016/0026-2714(94)90516-9

86. Gomes J. (1996) Extreme value theory for a thermal energy storage model. *Statistics &amp; Probability Letters*. doi:10.1016/0167-7152(95)00197-2

87. Gu R. (2015) CCF structural reliability estimation under statistical uncertainty. *2015 Annual Reliability and Maintainability Symposium (RAMS)*. doi:10.1109/rams.2015.7105172

88. Gudmundsson T. (2014) Markov Chain Monte Carlo for Computing Rare-Event Probabilities for a Heavy-Tailed Random Walk. *Journal of Applied Probability*. doi:10.1239/jap/1402578630

89. HAIMAN G. (2003) EXTREMES OF MARKOV SEQUENCES. *Probability Theory and Extreme Value Theory*. doi:10.1515/9783110917826.666

90. Harada K. (1994) Probability analysis of a 2-out-of-n: F system with common cause failure, multiple failure and dependent failure. *Microelectronics Reliability*. doi:10.1016/0026-2714(94)90111-2

91. Heide J. (2016) Composite extension finite fields for distributed storage erasure coding. *2016 IEEE International Conference on Communications (ICC)*. doi:10.1109/icc.2016.7510828

92. Helton J. (1996) Probability, conditional probability and complementary cumulative distribution functions in performance assessment for radioactive waste disposal. *Reliability Engineering &amp; System Safety*. doi:10.1016/s0951-8320(96)00072-5

93. Hoppe F.M. (1985) Iterating bonferroni bounds. *Statistics &amp; Probability Letters*. doi:10.1016/0167-7152(85)90048-3

94. Huang Z. (2019) On The Impacts of Tail Model Uncertainty in Rare-Event Estimation. *2019 Winter Simulation Conference (WSC)*. doi:10.1109/wsc40007.2019.9004933

95. Huber M. (2015) A Test of the Conditional Independence Assumption in Sample Selection Models. *Journal of Applied Econometrics*. doi:10.1002/jae.2431

96. Hughes R. (1987) A new approach to common cause failure. *Reliability Engineering*. doi:10.1016/0143-8174(87)90044-8

97. Huo Y. (2021) Optimal Copyset in Distributed Object Storage. *2021 IEEE International Conference on Big Data (Big Data)*. doi:10.1109/bigdata52589.2021.9671908

98. Ichikawa M. (1983) New formula for upper bound of probability of failure. *Reliability Engineering*. doi:10.1016/0143-8174(83)90012-4

99. Ichikawa M. (1984) Confidence limit of probability of failure based on stress-strength model. *Reliability Engineering*. doi:10.1016/0143-8174(84)90056-8

100. Ichikawa M. (1984) General formula for upper bound of probability of failure. *Reliability Engineering*. doi:10.1016/0143-8174(84)90035-0

101. Iliadis I. (2008) Reliability Assurance of RAID Storage Systems for a Wide Range of Latent Sector Errors. *2008 International Conference on Networking, Architecture, and Storage*. doi:10.1109/nas.2008.20

102. Iliadis I. (2023) Reliability Evaluation of Erasure-coded Storage Systems with Latent Errors. *ACM Transactions on Storage*. doi:10.1145/3568313

103. Jiang J.R. (2026) Likelihood-Based Quantum Computing Monte Carlo for Rare-Event Probability Estimation. *2026 IEEE International Conference on Consumer Electronics - Taiwan (ICCE-Taiwan)*. doi:10.1109/icce-taiwan71481.2026.11652476

104. Jimenez D. (2023) Resilience of a telecommunications network subjected to correlated geographical failures. doi:10.36227/techrxiv.22213948

105. Jing Sun (2010) A new optimal replica placement strategy in Content Distribution Networks. *2010 International Conference on Intelligent Computing and Integrated Systems*. doi:10.1109/iciss.2010.5656943

106. Jones H.W. (2025) Common Cause Failures Dominate and Defeat Redundancy. *2025 Annual Reliability and Maintainability Symposium (RAMS)*. doi:10.1109/rams48127.2025.10935209

107. Kaas R. (2002) A Simple Geometric Proof that Comonotonic Risks Have the Convex-Largest Sum. *ASTIN Bulletin*. doi:10.2143/ast.32.1.1015

108. Kančev D. (2012) A new method for explicit modelling of single failure event within different common cause failure groups. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2012.03.009

109. Kim K. (2010) Assessing the Impact of Geographically Correlated Failures on Overlay-Based Data Dissemination. *2010 IEEE Global Telecommunications Conference GLOBECOM 2010*. doi:10.1109/glocom.2010.5685229

110. Kim J.J. (2021) Erasure-Coding-Based Storage and Recovery for Distributed Exascale Storage Systems. *Applied Sciences*. doi:10.3390/app11083298

111. Knaeble B. (2026) Sensitivity Analysis of the Consistency Assumption. *Observational Studies*. doi:10.1353/obs.00012

112. Kounias S. (1989) Bonferroni bounds revisited. *Journal of Applied Probability*. doi:10.2307/3214031

113. Kulkarni R. (1994) Modelling common cause failures under data uncertainty of the system unavailability. *Microelectronics Reliability*. doi:10.1016/0026-2714(94)90046-9

114. Kumar V. (2011) Multi-dimensional Grid Quorum Consensus for High Capacity and Availability in a Replica Control Protocol. *Communications in Computer and Information Science*. doi:10.1007/978-3-642-22577-2_10

115. Kumar V. (2015) Circular Quorum Systems for Write Dominant Data Replication Protocols under Serial Isolation Using Quorum Consensus Approach. *Procedia Computer Science*. doi:10.1016/j.procs.2015.02.156

116. Leadbetter M.R. (1979) On dependent extreme value theory. *Advances in Applied Probability*. doi:10.1017/s0001867800031992

117. Leblanc H. (1984) Probability Functions and Their Assumption Sets — The Binary Case. *Foundations: Logic, Language, and Mathematics*. doi:10.1007/978-94-017-1592-8_6

118. Lee M.Y. (1997) Improved bivariate Bonferroni-type inequalities. *Statistics &amp; Probability Letters*. doi:10.1016/s0167-7152(96)00050-8

119. Li J. (2006) Adaptive Erasure Resilient Coding in Distributed Storage. *2006 IEEE International Conference on Multimedia and Expo*. doi:10.1109/icme.2006.262470

120. Li X. (2011) Reliability analysis of deduplicated and erasure-coded storage. *ACM SIGMETRICS Performance Evaluation Review*. doi:10.1145/1925019.1925021

121. Li J. (2022) Random Versus Copyset Placement: Data-Loss Models for Proactive-Tolerance Replica-Based Data Storage. *IEEE Transactions on Reliability*. doi:10.1109/tr.2021.3105675

122. Lin X. (2003) Delay Optimization in Quorum Consensus. *Algorithmica*. doi:10.1007/s00453-003-1066-x

123. Lin Y.F. (2008) A List-Based Strategy for Optimal Replica Placement in Data Grid Systems. *2008 37th International Conference on Parallel Processing*. doi:10.1109/icpp.2008.31

124. Liu W. (1994) A strong limit theorem under no assumption of independence, stationarity or various dependences. *Statistics &amp; Probability Letters*. doi:10.1016/0167-7152(94)90224-0

125. Liu J. (2016) A popularity-aware cost-effective replication scheme for high data durability in cloud storage. *2016 IEEE International Conference on Big Data (Big Data)*. doi:10.1109/bigdata.2016.7840627

126. Loper J. (2026) Worst-case Chernoff bounds for sums of random variables with known means and unequal ranges. *Statistics &amp; Probability Letters*. doi:10.1016/j.spl.2026.110742

127. Luo X. (2009) On the impact of erasure coding parameters to the reliability of distributed brick storage systems. *2009 International Conference on Cyber-Enabled Distributed Computing and Knowledge Discovery*. doi:10.1109/cyberc.2009.5342197

128. Manne A.S. (1952) The Strong Independence Assumption--Gasoline Blends and Probability Mixtures. *Econometrica*. doi:10.2307/1907648

129. Martin B. (1987) A practical method of common cause failure modelling. *Reliability Engineering*. doi:10.1016/0143-8174(87)90003-5

130. Medina M.G. (2020) Impact of Large-Scale Correlated Failures on Multilevel Virtualized Networks. *2020 IEEE 21st International Conference on High Performance Switching and Routing (HPSR)*. doi:10.1109/hpsr48589.2020.9098972

131. Melchers R. (2011) Application of extreme value theory to discriminate between failure modes. *Applications of Statistics and Probability in Civil Engineering*. doi:10.1201/b11332-350

132. Menkens O. (2014) Worst-Case Scenario Portfolio Optimization Given the Probability of a Crash. *SSRN Electronic Journal*. doi:10.2139/ssrn.2397263

133. Mesfioui M. (2005) Bounds on the value-at-risk for the sum of possibly dependent risks. *Insurance: Mathematics and Economics*. doi:10.1016/j.insmatheco.2005.03.002

134. Mills K.A. (2015) On Replica Placement in High-Availability Storage Under Correlated Failure. *Lecture Notes in Computer Science*. doi:10.1007/978-3-319-26626-8_26

135. Mills K.A. (2016) Erratum to: On Replica Placement in High-Availability Storage Under Correlated Failure. *Lecture Notes in Computer Science*. doi:10.1007/978-3-319-26626-8_60

136. Mills K.A. (2020) Algorithms for optimal replica placement under correlated failure in hierarchical failure domains. *Theoretical Computer Science*. doi:10.1016/j.tcs.2020.01.004

137. Müller A. (2001) Bounds for optimal stopping values of dependent random variables with given marginals. *Statistics &amp; Probability Letters*. doi:10.1016/s0167-7152(00)00220-0

138. Müller U.K. (2019) Refining the central limit theorem approximation via extreme value theory. *Statistics &amp; Probability Letters*. doi:10.1016/j.spl.2019.108564

139. Moghadamfarid A. (2025) Secure Decentralized Cloud Storage Assisted by Trusted Hardware and Erasure Coding. doi:10.2139/ssrn.5437322

140. Morio J. (2016) The formalism of rare event probability estimation in complex systems. *Estimation of Rare Event Probabilities in Complex Aerospace and Other Systems*. doi:10.1016/b978-0-08-100091-5.00003-4

141. Morio J. (2016) Introduction to rare event probability estimation. *Estimation of Rare Event Probabilities in Complex Aerospace and Other Systems*. doi:10.1016/b978-0-08-100091-5.00001-0

142. Morio J. (2016) Synthesis of rare event probability estimation methods for input–output systems. *Estimation of Rare Event Probabilities in Complex Aerospace and Other Systems*. doi:10.1016/b978-0-08-100091-5.00014-9

143. Naiman D.Q. (1992) Inclusion-Exclusion-Bonferroni Identities and Inequalities for Discrete Tube-Like Problems via Euler Characteristics. *The Annals of Statistics*. doi:10.1214/aos/1176348512

144. Neumayer S. (2010) Network Reliability With Geographically Correlated Failures. *2010 Proceedings IEEE INFOCOM*. doi:10.1109/infcom.2010.5461984

145. Nieuwhof G. (1985) Matching a failure probability distribution to test data. *Reliability Engineering*. doi:10.1016/0143-8174(85)90069-1

146. Nikolov A.V. (1986) K-out-of-N:G system with multiple correlated failures. *Microelectronics Reliability*. doi:10.1016/0026-2714(86)90811-5

147. Nikolov A.V. (1986) N-unit parallel redundant system with multiple correlated failures. *Microelectronics Reliability*. doi:10.1016/0026-2714(86)90767-5

148. Osrael J. (2006) A Replication Model for Trading Data Integrity against Availability. *2006 12th Pacific Rim International Symposium on Dependable Computing (PRDC'06)*. doi:10.1109/prdc.2006.12

149. Osrael J. (2007) Availability/Consistency Balancing Replication Model. *2007 IEEE International Parallel and Distributed Processing Symposium*. doi:10.1109/ipdps.2007.370610

150. anon. (2003) Appendix 3: Template for a typical service level agreement. *Telecommunications Quality of Service Management*. doi:10.1049/pbte048e_appendix3

151. Pei Dong X. (2018) Cascading Failure Risk Assessment in Power Grid Considering the Line Outage Rate. *The Journal of Engineering*. doi:10.1049/joe.2018.8356

152. Peleg D. (1995) The Availability of Quorum Systems. *Information and Computation*. doi:10.1006/inco.1995.1169

153. Peng F. (2013) Decentralized estimation with correlated additive noise: Does dependency always imply redundancy?. *2013 Asilomar Conference on Signals, Systems and Computers*. doi:10.1109/acssc.2013.6810368

154. Perez G. (2023) Service Level Agreement (SLA). *Elgar Encyclopedia of Services*. doi:10.4337/9781802202595.service.level.agreement

155. Phelps R.P. (2010) On the Reporting of Measurement Uncertainty and Reliability for U.S. Educational and Licensure Tests: Report to Ofqual. *SSRN Electronic Journal*. doi:10.2139/ssrn.2687370

156. Pijarski P. (2025) Outage Rates and Failure Removal Times for Power Lines and Transformers. *Applied Sciences*. doi:10.3390/app15148030

157. Qi J. (2021) Utility Outage Data Driven Interaction Networks for Cascading Failure Analysis and Mitigation. *IEEE Transactions on Power Systems*. doi:10.1109/tpwrs.2020.3015380

158. Rahman P.A. (2017) Analysis of the mean time to data loss of nested disk arrays RAID-01 on basis of a specialized mathematical model. *IOP Conference Series: Materials Science and Engineering*. doi:10.1088/1757-899x/177/1/012088

159. Rahman P.A. (2018) Analysis of mean time to data loss of fault-tolerant disk arrays RAID-6 based on specialized Markov chain. *IOP Conference Series: Materials Science and Engineering*. doi:10.1088/1757-899x/327/2/022086

160. Ramabhadran S. (2008) Durability of replicated distributed storage systems. *Proceedings of the 2008 ACM SIGMETRICS international conference on Measurement and modeling of computer systems*. doi:10.1145/1375457.1375514

161. Recsei E. (1987) Bonferroni-type inequalities. *Advances in Applied Probability*. doi:10.2307/1427431

162. Reiser B. (1985) A remark on Ichikawa's upper bound of probability of failure. *Reliability Engineering*. doi:10.1016/0143-8174(85)90095-2

163. Rosenhaus M.B. (2004) Calculation of some Reliability Measures for Redundancy Systems with Different Types of Failures. *Quality and Reliability Engineering International*. doi:10.1002/qre.597

164. Rüschendorf L. (1991) FréChet-Bounds and Their Applications. *Advances in Probability Distributions with Given Marginals*. doi:10.1007/978-94-011-3466-8_9

165. Rüschendorf L. (2012) Optimal Portfolio Diversification w.r.t. Extreme Risks. *Springer Series in Operations Research and Financial Engineering*. doi:10.1007/978-3-642-33590-7_13

166. Russell J.W. (1998) The International Diversification Fallacy of Exchange-Listed Securities. *Financial Services Review*. doi:10.1016/s1057-0810(99)80005-5

167. Saigo H. (2021) The independence assumption in the mixed randomized response model. *Statistics &amp; Probability Letters*. doi:10.1016/j.spl.2020.108986

168. Sakalauskas L. (2013) Multidimensional rare event probability estimation algorithm. *Computational Science and Techniques*. doi:10.15181/csat.v1i2.93

169. Sakif M.S.I. (2024) Towards Benchmarking Erasure Coding Schemes in Object Storage System. doi:10.2139/ssrn.4713329

170. Samuels S.M. (1989) Bonferroni-Type Probability Bounds as an Application of the Theory of Tchebycheff Systems. *Probability, Statistics, and Mathematics*. doi:10.1016/b978-0-12-058470-3.50026-4

171. Schay G. (1979) Optimal Joint Distributions of Several Random Variables with Given Marginals. *Studies in Applied Mathematics*. doi:10.1002/sapm1979612179

172. Scheu M.N. (2017) Influence of statistical uncertainty of component reliability estimations on offshore wind farm availability. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2017.05.021

173. Sharaf S. (2014) Enabling service-level agreement renegotiation through extending WS-Agreement specification. *Service Oriented Computing and Applications*. doi:10.1007/s11761-014-0159-5

174. She B. (2025) Descriptor: United States Event-Correlated Power Outage Dataset (USECPO). *IEEE Data Descriptions*. doi:10.1109/ieeedata.2025.3598229

175. Shi H. (2020) INEC: Fast and Coherent In-Network Erasure Coding. *SC20: International Conference for High Performance Computing, Networking, Storage and Analysis*. doi:10.1109/sc41405.2020.00070

176. Sibuya M. (1992) Sharp Bonferroni-Type Inequalities in Explicit Forms. *Probability Theory and Applications*. doi:10.1007/978-94-011-2817-9_11

177. Smith H. (2016) Reliability and Continuous Data Protection, Synchronous Replication. *Data Center Storage*. doi:10.1201/b10798-20

178. Smith H. (2016) Reliability and Near-Continuous Data Protection, Asynchronous Replication. *Data Center Storage*. doi:10.1201/b10798-21

179. Spencer T.H. (1994) Generalized Bonferroni inequalities. *Journal of Applied Probability*. doi:10.2307/3215034

180. Talapko D. (2012) Telecom datacenter power infrastructure availability comparison of DC and AC UPS. *Intelec 2012*. doi:10.1109/intlec.2012.6374509

181. Tan X. (1989) Some inequalities of Bonferroni—Galambos type. *Statistics &amp; Probability Letters*. doi:10.1016/0167-7152(89)90075-8

182. Tang Z. (2017) Quantitative Availability Analysis of Hierarchical Datacenter under Power Oversubscription. *2017 IEEE International Conference on Smart Computing (SMARTCOMP)*. doi:10.1109/smartcomp.2017.7947039

183. Tiit E.M. (2002) Existence of Multivariate Distributions with Given Marginals. *Distributions With Given Marginals and Statistical Modelling*. doi:10.1007/978-94-017-0061-0_24

184. Tonon F. (2009) Bounds on Previsions and Conditional Probabilities on Joint Finite Spaces Under the Assumption of Independence in Imprecise Probability. *Volume 10: Mechanical Systems and Control, Parts A and B*. doi:10.1115/imece2009-12206

185. Tsuchiya T. (2002) Byzantine quorum systems with maximum availability. *Information Processing Letters*. doi:10.1016/s0020-0190(01)00311-8

186. Uezato Y. (2021) Accelerating XOR-based erasure coding using program optimization techniques. *Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis*. doi:10.1145/3458817.3476204

187. van Renesse R. (2010) Replication Techniques for Availability. *Lecture Notes in Computer Science*. doi:10.1007/978-3-642-11294-2_2

188. Vukolić M. (2012) Byzantine Quorum Systems. *Synthesis Lectures on Distributed Computing Theory*. doi:10.1007/978-3-031-02007-0_5

189. Vukolić M. (2012) Classical Quorum-Based Emulations. *Synthesis Lectures on Distributed Computing Theory*. doi:10.1007/978-3-031-02007-0_4

190. Vukolić M. (2012) Latency-efficient Quorum Systems. *Synthesis Lectures on Distributed Computing Theory*. doi:10.1007/978-3-031-02007-0_6

191. Vukolić M. (2012) Probabilistic Quorum Systems. *Synthesis Lectures on Distributed Computing Theory*. doi:10.1007/978-3-031-02007-0_7

192. Walker A.M. (1981) On the classical Bonferroni inequalities and the corresponding Galambos inequalities. *Journal of Applied Probability*. doi:10.2307/3213333

193. Walter W. (1988) Marginal-frechet-bounds for multidimensional distribution functions. *Statistics*. doi:10.1080/02331888808802100

194. Wang R. (2013) Bounds for the sum of dependent risks and worst Value-at-Risk with monotone marginal densities. *Finance and Stochastics*. doi:10.1007/s00780-012-0200-5

195. Xian G. (2024) Examining SSD-correlated Failures within Racks in Production Data Centers. *2024 IEEE International Conference on High Performance Computing and Communications (HPCC)*. doi:10.1109/hpcc64274.2024.00065

196. Xu Y. (2010) Characterizing the Spread of Correlated Failures in Large Wireless Networks. *2010 Proceedings IEEE INFOCOM*. doi:10.1109/infcom.2010.5462009

197. Yarimer E. (1983) Statistical Parameter Uncertainty, Information Level And Reliability Assessment. *Reliability Theory and Its Application in Structural and Soil Mechanics*. doi:10.1007/978-94-009-6896-7_28

198. Yeh C.T. (2017) Cost-oriented component redundancy allocation for a communication system subject to correlated failures and a transmission reliability threshold. *Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability*. doi:10.1177/1748006x17742778

199. Yeh C.T. (2017) Optimal redundancy allocation to maximize multi-state computer network reliability subject to correlated failures. *Reliability Engineering &amp; System Safety*. doi:10.1016/j.ress.2016.08.026

200. Yigitbasi N. (2010) Analysis and modeling of time-correlated failures in large-scale distributed systems. *2010 11th IEEE/ACM International Conference on Grid Computing*. doi:10.1109/grid.2010.5697961

201. Yin C. (2016) Sharp Convex Bounds on the Aggregate Sums–An Alternative Proof. *Risks*. doi:10.3390/risks4040034

202. Zhong M. (2007) Object replication degree customization for high availability. *Proceedings of the twenty-sixth annual ACM symposium on Principles of distributed computing*. doi:10.1145/1281100.1281164

203. Zhong M. (2008) Replication degree customization for high availability. *Proceedings of the 3rd ACM SIGOPS/EuroSys European Conference on Computer Systems 2008*. doi:10.1145/1352592.1352599

204. Zhou C. (2009) Dependence Structure of Risk Factors and Diversification Effects. doi:10.2139/ssrn.1456848

205. Zhou T. (2020) Fast Erasure Coding for Data Storage. *ACM Transactions on Storage*. doi:10.1145/3375554

206. Zuk J. (2014) Rare-event simulation for radar threshold estimation in heavy-tailed sea clutter. *2014 IEEE Workshop on Statistical Signal Processing (SSP)*. doi:10.1109/ssp.2014.6884669

