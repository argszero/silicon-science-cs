# A Declaration Does Not Determine an Install

## What a version range leaves open, and why the answer is a property of the range dialect

---

## Abstract

A dependency declaration names a set of versions, not a version. Whether that set collapses to
one install is therefore not a property of the ecosystem or of the package: **it is a property of
the range dialect the ecosystem's conventions favour.** We test this on two registries. In npm,
where the dominant idiom is the caret range with an upper bound, 13.3% of the 2,427 evaluable
declared edges admit more than one version [12.0, 14.7], and 34.5% of those ambiguous edges lead
to alternative installs that constrain *further* dependencies differently [29.5, 39.8] — so the
ambiguity is not local. In PyPI, where the wild requirement is an unbounded `>=`, 94.2% of the 226
evaluable edges admit more than one version [90.4, 96.6]. The two ecosystems differ by a factor of
seven on the same instrument, and the difference tracks the range text rather than the ecosystem:
stratifying npm's declarations by syntax, an exact pin survives twelve months at 1.000 (n=582), a
caret range at 0.781 (n=439), and on the 16 target packages where both forms occur the caret range
loses 10 times and wins 0. The second ecosystem supports only the birth-state half of this claim:
PyPI's decay curve is **not run by construction**, because a declaration that is already
multi-valued when written has no determination left to lose. We also price the alternative: a
minimum certificate that recovers determination costs 25.8% of a lockfile's pins on npm and 92.1%
on PyPI, because the certificate can never be smaller than the number of ambiguous edges — a
closed form we prove and then confirm by exhaustive search on 454 declarations. We claim no
construction: what we offer is a measured mechanism, its price, and the observation that the
widely-held reading of a range as a compatibility promise is contradicted by the decay curve of
the range form that is supposed to make that promise.

---

## 1. Why a declaration is not an install

Reproducibility work has largely treated the *environment* as the unit to be pinned. Tools make
the environment portable and re-creatable [13, 95]; researchers are studied as the actors who fail to share enough
[4]; the field is told the gap is structural rather
than a tooling defect [44]; and reproducibility is cast
as an engineering requirement with acceptance criteria [45, 65]. Environmental failures are known to reproduce differently in
different environments — the exact failure mode an over-wide range admits
[20]. Long-term reproducibility is understood to need
maintenance over time rather than a one-off pin [76]. And the
vulnerability literature has measured, for npm, how long a vulnerable dependency persists by
declaration class [33] — which is the same shape of
question we ask about determination, asked about a different property.

What this body of work takes for granted is the *declaration* itself. A line such as
`"left-pad": "^1.3.0"` is read as a statement about compatibility, and the resolved version is
treated as the declaration's meaning. This paper starts one step earlier: a declaration is a
**set**, and the question is whether that set is a singleton. When it is not, the sentence "this
project depends on left-pad 1.3.0" is not true of the declaration — it is true of one resolution
of it, chosen by a resolver, at a time.

That distinction is old in constraint reasoning and new in registry measurement. Constraint
satisfaction is the natural language for it [64], and the
tractability literature tells us that what matters is the structure of the constraint language
rather than the size of the instance [18, 19, 25, 35]. The last of these recovers structure by variable
elimination rather than assuming it, which is the closest analogue of what a bounded range does
for us: it removes a source of freedom instead of enumerating it. Our
contribution is not a new solver: it is the observation that the *range syntax* is the constraint
language, that registries already publish which language each package speaks, and that the
consequences of speaking one language rather than another are measurable and large.

**Contributions.**

1. A construct — the **admissible set** of one declaration at one instant — and an instrument that
   computes it from registry metadata alone, with its unparsed and absent-package counts printed
   beside every rate (§2, §6).
2. A measured **dialect effect**: the same instrument on two registries gives 13.3% and 94.2%, and
   within one registry the survival of determination is ordered by range syntax, not by package
   (§4, §7).
3. A **negative** result on the construct's own compression: the minimum distinguishing certificate
   has exactly as many entries as there are ambiguous edges, so it cannot be compressed, and its
   price is 25.8% / 92.1% of a lockfile (§3, §7.4). We report this as a closed form and a price,
   not as a system.
4. A **refutation of our own registered expectations** on two of three priors, with the detectable
   effect stated so the refutation cannot be dismissed as underpowered (§7.1).

---

## 2. Setting: what one declaration admits

For a declaration of package `p` at version `v` published at instant `t`, and a dependency `d`
constrained by range `r`, define the **admissible set** `A(e,t) = { x ∈ versions(d) : x published
at or before t, x satisfies r }`. The edge `e` is *determined* when `|A(e,t)| = 1`, *ambiguous*
when `|A(e,t)| > 1`, and **unknown** when `d` is absent from the snapshot — never zero, because an
absence in our data is not an absence of versions. A declaration is determined when every one of
its edges is.

The measurement is deliberately narrower than a resolver. We do not ask what npm's resolver would
pick; we ask how many outcomes the declaration leaves it free to pick. That is why the instrument
is mechanical: `|A|` is a set-cardinality computation over published metadata, so its ground truth
needs no annotator and no inter-rater agreement. Where the set cannot be computed we say so and
count it separately.

Prior work that studies dependencies measures something else. Incompatibilities are studied as
historical events rather than as properties of the declaration that admitted them
[23]; dependency-network topology is measured on one resolved
version per package, which presumes the declaration names one [26];
build errors are found by executing builds, i.e. after resolution
[60]; breaking updates are diagnosed post hoc
[84]; upgrade cost is measured at the interface level
[71]; dependency cost and survival are measured per declared
dependency [41, 89]; remediation presumes a
single resolved state to repair [57]. Each is a real result about
resolved graphs. None of them counts the size of the set the resolver chose from, and that
omission is what lets "the declaration determines the install" pass unexamined.

---

## 3. Coupling: why ambiguity is not local

An ambiguous edge is not necessarily consequential. If all admissible versions of `d` declare the
same dependencies, the install is undetermined in *version* but determined in *closure*. The
mechanism-sensitive question is therefore: do the alternatives constrain the rest of the graph
differently?

This is where the paper's earlier construction ambition failed, and the failure is informative.
The registered plan was a *minimal distinguishing key*: a small set of packages whose recorded
versions would pin the whole install, argued via a vertex-cover bound. Enumerating solution sets
exactly for 191 npm and 38 PyPI instances gives a median `|K*|/|M|` of **1.0** in both
ecosystems: the certificate is never smaller than the number of ambiguous edges. The vertex-cover
bound is valid but not attained, because the ambiguity graph of an independent product is a clique
— whose cover is `|M| - 1` — and no cover of that size determines an install. The bounds we
registered came from the approximation literature on set cover, whose guarantees are stated for
the general weighted form [31, 47];
our unit-cost instance is the degenerate case of that form, which is why the guarantee there is
true and yet silent about the structure we actually have. Functional
dependence between packages is the only mechanism that could compress the certificate, and in the
data it does not appear; we can exhibit it only in a synthetic plant, which we label as such (§6).
Savings, where they exist at all, are 11.5% of instances on npm and 0% on PyPI.

So the coupling leg is reported at cost, not as a system: the certificate **is** the list of
ambiguous edges, and the honest content of this section is the lemma and its price. The lemma is
`|K*| = |M|`, proved in §3.1 and confirmed by exhaustive search on every declaration small enough
to enumerate (389 npm, 65 PyPI; 604 and 199 skipped as too large, counted rather than dropped).

This is where our work meets the solver literature at a well-defined boundary. Formal models of
resolution define which solution a solver returns [38]; hypergraph
encodings make solving faster and address cross-ecosystem ambiguity
[37]; algebraic decomposition targets zero-conflict resolution
[82]; Max-SMT selects an assignment optimal under stated
costs [78]. Every one of these takes the admissible set as
input. We measure its size. The relationship is not competition but ordering: their optimality
statements are defined over the set whose cardinality we report. Adjacent empirical work has
measured downstream dependency groups [80], dependency clusters in
Maven Central [56], peer-dependency resolution loops
[97], dynamic conflict detection at build time
[75], versioned transitive closure binding
[102], and yanked-release behaviour — the impossibility
argument's own exception, which we count rather than assume away [58].

### 3.1 The certificate cannot be compressed

**Lemma.** For one declaration, let `M` be the set of ambiguous edges and `K*` a minimum set of
(package, version) records that determines the install. Then `|K*| = |M|`.

*Lower bound.* For each `p ∈ M` there exist two solutions that differ only at `p`. Any record that
determines the install must distinguish them, so `p ∈ K`. Hence `|K| ≥ |M|`.

*Upper bound.* Recording the version of every `p ∈ M` leaves every remaining domain a singleton, so
the install is determined. Hence `|K| ≤ |M|`. ∎

The consequence is a price rather than a design. Recording the ambiguous edges costs 153 pins
where a full lockfile costs 594 (25.8%) on the npm instances, and 58 where a lockfile costs 63
(92.1%) on the PyPI instances. On PyPI the certificate is barely cheaper than pinning everything,
which is what an ecosystem whose declarations are already multi-valued should look like.

---

## 4. The dialect

The interesting fact is not that ambiguity exists. It is that its **rate is set by the range
syntax**, and that the syntax is an ecosystem convention rather than a property of the package.

A caret range `^1.3.0` is bounded above by the next major version; a tilde range by the next
minor; an exact pin names one version. A bare `>=1.3.0` in the wild is bounded by nothing, which
is why it is multi-valued at birth — and why the PyPI rate is 94.2% while npm's is 13.3%.

That a range is *read* as a compatibility promise is itself documented: declared constraints are
studied as semantic-versioning promises [28], compliance with those
promises is measured and found imperfect [59, 74], and version ordering is a convention rather than a
property of the artifact [6, 50].

If the promise were kept, a bounded range would stay determined: its upper bound would exclude
every incompatible version, so no later publish could enter the admissible set. §7.3 tests exactly
this and finds the promise false in a specific, ordered way: exact 1.000, tilde 0.980, caret 0.781
at twelve months. The dialect is real; the promise attached to it is not.

---

## 5. What follows for practice

Three consequences, each scoped to what we measured.

**For a project that wants a determined install**, the syntax is a cheap lever and the lockfile is
the expensive one. Changing a caret range to an exact pin moves a declaration from the stratum that
decays to the stratum that does not; the price of that move is the flexibility the caret was
chosen for. The lockfile alternative — recording resolved state rather than bounding a range — is
the strongest form of the other choice, and its state of the art is well developed: Maven-Lockfile
brings high-integrity rebuilds to a manager that lacked native lockfiles
[87]; lockfile design is compared across managers [3, 87, 96], and Maven's
own mediation rule is a third dialect with its own semantics [96].
Monorepo strategies reach the same tension from the build side
[3].

**For the container and model registries**, the same degree of freedom reappears in a different
artifact. An image tag names a set that can move; image rebuilds are not reproducible even from
identical inputs [90], continuous delivery makes the image rather
than the manifest the unit of change [8], automatic updates
change published environments
under the reader [92], images are scanned as artifacts with drift of
their own [9, 30], and vulnerability assessment
is an ongoing obligation [52]. Pinning the image rather than the
declaration is the practitioner's answer [7, 16, 21, 67], with provenance recorded as evidence
[55] and evaluated for what it actually buys
[68, 72]. Model
registries have the same shape with prose declarations: model cards are generated automatically
over a hub whose artifacts move [1], and self-describing
models carry their dependency identity instead of leaving it to be inferred
[29, 39, 79, 81, 99, 101].

**For maintainers and for repair tooling**, the measurement locates where the cost lands.
Automated update tooling and post-hoc repair — including LLM-based repair of breaking updates —
treat the *update* as the unit of work [15, 63, 85]; when the declaration already admits many versions, the
update is not the event that introduces freedom. The same is true of infrastructure-as-code
providers, which are version-constrained artifacts with their own upgrade discipline
[11, 12], and of functional package
management, whose strongest evidence is that it does enable reproducible builds at scale
[17, 40, 46, 53, 61, 62, 83].

### 5.1 The ecosystems themselves

The two registries are not interchangeable substrates, and the literature says so from several
directions. Each has been characterised as an object — size and growth for PyPI
[14], dynamics read from registry metadata for JavaScript
[98], and a third ecosystem, CRAN, with its own conventions
[70]. Managers differ even where they consume the same
declarations: npm against yarn [22], and Debian's
distribution-level graph against both [91].

Three of those findings shape our interpretation rather than merely accompany it. Technical lag —
how far behind a declaration leaves an install [27] — is what our
survival curve complements: lag measures distance to the newest version, we measure whether the
install is determined at all. Downgrades in npm show the resolved version moving independently of
the declaration [24], which is what an undetermined declaration
permits and a determined one does not. And the ecosystem's response to abandonment
[66] is the practical cost of admitting versions that may later
disappear.

Two adjacent literatures measure *other properties of the same edges*, and we name the boundary
explicitly: licensing obligations propagate across dependencies
[49], security-disclosure practice is recorded per package
[93], and ecosystem health is scored at ecosystem level
[100] — none of which is a statement about how many installs a
declaration admits. Dependency structure represented as a graph is shared machinery rather than a
shared question [32]. Finally, the actors are studied: the
maintainer's role [34], and how API changes and deprecations
are announced and versioned [73, 88] — which matters here because a deprecation announced in
prose does not narrow an admissible set.

**On prior work being thin.** We searched for work that measures the admissible set of a
declaration and did not find it. That is a claim about a searched space, not an absence claim: 81
Crossref bibliographic queries, a scholarly-type filter, and a two-pass relevance review left 102
citable records out of 270 harvested, and of those only the six in §8 state a competing object. The
rest of the literature is adjacent: it shares the vocabulary and asks about a different construct.

---

## 6. Method and instrument

**Snapshots.** Two registry snapshots were built once and committed: npm (158 packages, 993
declaring versions) and PyPI (31 packages, 264 declaring versions). Every number in this paper is a
function of those files and nothing else. A content hash pins each snapshot, and those pins changed
once during the work — extending a snapshot for a panel moved published rates without any
declaration changing, which is the signature of absence being read as measurement. The corrected
rates are the ones reported here, and the earlier figures are superseded rather than quietly
replaced.

**Counting the uncomputable.** Every rate is printed beside its unparsed count and its
absent-package count: on npm, 975 of the declared specs could not be parsed by our instrument and
913 named a package outside the snapshot; on PyPI, 53 and 6. A package absent from the snapshot is
`UNKNOWN`, never "no admissible version" — reading absence as zero is the defect that produced the
superseded rates. Because `edges` counts only evaluable edges, the denominators here are
evaluable-edge denominators, and we say so wherever a rate appears rather than implying the full
declared population.

**Whose data this is.** Registries are a mining substrate with documented limits
[54]; registry-derived metrics can fail to measure what their names
claim [69]; SBOM-style dependency records drift in place
[94]. Our response is a pinned snapshot, an explicit
denominator, and a separate count for everything the instrument could not read.

**Intervals.** Where a rate is a proportion we report a Wilson score interval, which behaves at the
small proportions several of our cells sit at [42]. We deliberately
do not use the Wald interval, which is known to misbehave near 0 and 1
[2, 51], nor the conservative
exact interval, whose coverage costs length [43, 86]; the criteria by which such a choice should be judged are
the subject of their own literature [36].

**Plants.** A guard that cannot fail is not a guard, so each instrument ships known-answer plants
that fail if the instrument reverts to a plausible wrong behaviour: identical closures must not
count as a closure difference, a version published later must not be admissible as-of, an unparsed
spec must return `None` rather than an empty set,`wilson(0,52)` must have a positive upper bound,
an absent target must be `UNKNOWN`, an empty denominator must print `NOT RUN` and not `0.0`, and a
caret range must saturate at its major bound. The guards pass 7/7, 3/3 and 7/7; the
functional-dependence positive that the data does not contain is a plant, and is labelled as one
everywhere it appears (§3).

**Decay.** A panel of declarations at least 12 months old is read at k = 0, 3, 6, 9, 12 months. The
**at-risk set** is declared before the curve is read: only an edge that is a singleton at k = 0 can
lose a determination it has, so the denominator at each k is printed. An unobservable deletion
before the snapshot instant is declared in advance, and a k where survival rises is counted and
reported as `NON-MONOTONE` rather than treated as a refutation — none occurred.

---

## 7. Results, against what we expected

### 7.1 The registered priors

We registered three priors before measuring. Two were wrong, and we report the detectable effect
with each so that the refutation is a measurement and not a power failure.

**P1 — "≥30% of real declared edges are under-determined at declaration time."** Refuted for npm,
confirmed for PyPI: npm **13.3%** [12.0, 14.7] (322/2,427 evaluable edges), PyPI **94.2%**
[90.4, 96.6] (213/226). The prior was ecosystem-blind, and the split is the finding: npm's caret
range carries an upper bound, wild PEP 440 requirements are dominated by `>=` without one. The pilot
that motivated P1 read one package in one ecosystem and could not have seen this.

**P2 — ">50% of determined-at-birth edges become ambiguous within 12 months."** **Refuted.** Pooled
edge survival at twelve months is 0.910 (975/1,072, half-width ≈ 3 points, so this is not
underpowered); the worst stratum is 21.9%, and declaration-level survival is 0.767. The registered
>50% would have required a collapse an order of magnitude larger than what occurs.

**P3 — "median |K*| is below 50% of the packages in the solution support."** **Refuted**: median
`|K*|/|M| = 1.0` in both ecosystems (§3). This is the refutation that changed the paper's shape: the
construction leg became a closed form and a price.

### 7.2 Ambiguity is not local (npm)

Of the 322 ambiguous npm edges, **111 (34.5% [29.5, 39.8])** have admissible alternatives that
constrain further dependencies *differently*, and 9.3% [6.6, 13.0] change the closure's *shape* —
a dependency is added or removed. The remaining alternatives differ in version but not in
consequence, which is the distinction that separates an alarming rate from a consequential one. On
PyPI the analogous figures are 33/213 = 15.5% [11.3, 21.0] and 6.6% [4.0, 10.7].

That asymmetry is expected under the dialect reading and is worth stating plainly: PyPI's
declarations are ambiguous far more often and consequential far less often, because an unbounded
range is ambiguous in a way that rarely changes the next layer — the same ranges admit many
versions whose own declarations agree.

### 7.3 The decay is ordered by syntax, not by package

npm edge survival at twelve months, by stratum: `exact` **1.000** (n=582), `tilde` **0.980**
(n=51), `caret` **0.781** (n=439); declaration-level **0.767** (n=150). The ordering follows
boundedness — an unbounded range cannot stay determined, a bounded one decays as versions
accumulate inside its bound, and an exact pin has nothing to accumulate.

The control that makes this a statement about syntax: on the **16 target packages** for which both
an exact and a caret declaration exist, exact outlives caret on **10** targets and caret outlives
exact on **0**. On the 11 targets where caret and tilde coexist the two are tied (1 and 1). The
effect is carried by the range text, not by which package is popular or hard-working.

**PyPI's curve is not run, and that is a result.** No panel declaration there has all edges
singleton at k = 0, so the declaration-level at-risk set is empty at every k and the curve prints
`NOT RUN`. A cohort under-determined at birth has no decay to measure. We report this rather than
substituting a smaller population that would produce a number.

### 7.4 The price of recovering determination

From the depth-2 artifact: a certificate covering the ambiguous edges costs **25.8%** of a
pin-everything baseline on npm (153 of 594 pins) and **92.1%** on PyPI (58 of 63). The two figures
differ for the same reason the rates do. These counts come from an artifact computed over an
earlier snapshot than the one the depth-1 and decay numbers use; we report them with that
provenance rather than implying a single consistent snapshot across all three legs.

---

## 8. Related work, and what separates us from it

Six works state a competing object. Each is cited because the difference is load-bearing, and for
each we record what we actually read while writing this paper.

**A formal model of dependency resolution** [38] states that managers
differ in their resolution *semantics*. We do not model the resolver; we count what it may choose
among. The two results concern different objects and neither subsumes the other. *(Read at abstract
level: the registry carries an abstract, and it confirms the semantic-difference framing.)*

**Hypergraph dependency resolution** [37] is about interoperability
between managers and the encoding of the resolution problem. It is a contribution to the cost of
choosing and is silent on how many admissible choices a declaration leaves; our construction is
the input such an encoding would receive. *(Read at abstract level.)*

**Max-SMT optimal dependency management** [78] selects an
optimal assignment under stated costs. Optimality is defined over the admissible set. The paper
needs our quantity as a precondition and does not measure it. *(Title and venue only: no abstract
in the registry and the arXiv attempt timed out; the difference must be confirmed against the full
text before submission.)*

**LLM-based repair of breaking updates** [85] repairs a build after an
update breaks it. It is post-hoc and per-update; we ask beforehand how much of the update space the
declaration left open. *(Title, venue and journal only; abstract unavailable, full text to be read
before submission.)*

**Maven-Lockfile** [87] brings high-integrity rebuilds to a manager that
lacked native lockfiles. It is the strongest form of the alternative we price. *(Read at abstract
level: it states that Maven lacks native lockfile support and that lockfiles freeze versions and
verify integrity.)*

**Semantic versioning read as a compatibility promise** [28] is the
belief our dialect measure tests. If a bounded range really did promise compatibility, ambiguity
inside the range would carry no risk and the decay curve would be flat in every stratum. It is not
flat, and the departure is ordered by boundedness. *(Title and venue only; abstract unavailable, and
because this work is the belief under test it must be read in full before the claim is made.)*

Beyond these, the remaining 96 placed works are context, method, or adjacent construct, and each is
placed in a section with the sentence it supports in `reference-check.md` — a generated report that
lists every entry's verification record, the section it is placed in, and the claim it supports,
and that marks every record we pruned as supporting no claim here.

---

## 9. Threats to validity

**The populations are small and named.** 158 npm packages and 31 PyPI packages, chosen as a seed set
and a panel, not sampled at random — and there is no random sampling of package ecosystems to be
had [5]; what a frame must state to make a rate interpretable is itself a
methodological literature [10]. Our rates are statements about
these frames. We do not claim that npm is 13.3% ambiguous; we claim that 322 of 2,427 evaluable
declared edges in this frame are.

**The instrument reads syntax, not intent.** 975 npm specs were unparseable by our parser. If those
specs behave differently from the parseable ones, the rate is biased in an unknown direction; the
count is printed for that reason, and the honest reading of a rate whose denominator excludes 40%
of the input population is "a rate over the readable part".

**The identity lemma is close to definitional.** `|K*| = |M|` follows from the product structure
once the question is posed correctly; its value is that it rules out the compression we hoped for
and turns the certificate into a price. We do not present it as deep theory, and the reader should
not read §3 as a construction.

**The functional-dependence mechanism is witnessed only by a plant.** In principle a functional
dependency between packages can compress the certificate below `|M|`. We can construct such a case
and our instrument finds it; the registries in this study contain none. Any claim that certificates
*can* be compressed rests on synthetic data and is labelled as such.

**One leg is measured on an older snapshot.** The depth-2 counts (and hence the prices in §7.4) come
from an artifact computed before the panel extension. The depth-1 and decay numbers are from the
committed snapshot. The qualitative conclusion — the certificate cannot be compressed — is
structural and does not depend on the snapshot; the prices are quantities and do depend on it.

**Design-dependence of validity.** Worldview, method and validity are coupled
[77], and what "validity" means for a measurement claim has to
be operationalized rather than asserted [48]. Our threats
are stated in that frame: each is a statement about what this instrument, on this frame, can
support.

**Why it is still worth publishing.** The mechanism is small and the populations are small, but the
claim is not a snapshot of a new domain through an existing pipeline: the construct — the admissible
set of a declaration and its survival over time — is new, the measurement is longitudinal over a
panel, and the finding changes a belief that practitioners act on, namely that a bounded range is a
compatibility promise. The refutation of our own registered priors is part of the evidence that the
measurement was not designed to confirm what we expected.

---

## 10. Conclusion

Whether a dependency declaration determines an install is a property of the range dialect, not of
the ecosystem or the package. Two registries, one instrument: 13.3% of evaluable npm edges are
ambiguous against 94.2% on PyPI, and within npm the survival of determination over twelve months is
ordered exact 1.000, tilde 0.980, caret 0.781, with the same-package control showing the syntax
rather than the package carrying the effect. The minimum certificate that recovers determination
cannot be smaller than the number of ambiguous edges, which makes it a price rather than a design:
25.8% of a lockfile on npm, 92.1% on PyPI. What we did not find — a compression mechanism, or a
decay curve on PyPI — we report as not found, with the counts that show the search was made.

---

## Contribution level

We declare **`theory+empirics`**, against that level's own test: two independent systems validated
with one instrument (npm and PyPI), ground truth that is mechanical rather than annotated (set
cardinality over published metadata), a stated theory result used as a bound (`|K*| = |M|`, with the
registered vertex-cover bound shown valid but unattained), and baselines against which the
certificate is priced (pin-everything and pin-direct-only). We do not claim a construction: the
certificate leg reduces to a closed form and a price, and §3 says so. If a reader holds that the
analytic statements are too close to definitional to carry the label, `case study` is the level the
evidence supports, and the abstract already claims no general conclusion beyond the two measured
populations.

---

## Reproduction

```
sh reproduce.sh          # all legs; the depth-2 enumeration takes ~30 min
sh reproduce.sh --fast   # skips the depth-2 enumeration and reports it NOT RUN
```

Expected output: steps 1–3, 5 and 6 pass with the numbers quoted above; step 4 passes on a full run
or prints `NOT RUN` under `--fast`. Exit code is the count of failed steps.

## References

1. Alharbi. 2026. Enhancing AI Transparency on Hugging Face: An Automated Pipeline for Model Card Generation and Reproducibility Scoring From Repository Artifacts. IEEE Access. DOI 10.1109/access.2026.3723027.

2. Almendra-Arao. 2020. USING ADJUSTED WALD CONFIDENCE INTERVAL FOR A BINOMIAL PROPORTION. JP Journal of Biostatistics. DOI 10.17654/bs017020415.

3. Almishev. 2025. Dependency Management Strategies in Scalable Monorepositories: Analysis and Resolution of Version Conflicts. World Journal of Advanced Research and Reviews. DOI 10.30574/wjarr.2025.28.1.3468.

4. Alnoamany. 2018. Towards computational reproducibility: researcher perspectives on the use and sharing of software. DOI 10.7287/peerj.preprints.26727v1.

5. Amir. 2018. There is no random sampling in software engineering research. Proceedings of the 40th International Conference on Software. DOI 10.1145/3183440.3195001.

6. anon. 1976. A numbering scheme for a computer programming library. Software: Practice and Experience. DOI 10.1002/spe.4380060317.

7. Aranguren. 2015. Enhanced reproducibility of SADI web service workflows with Galaxy and Docker. Gigascience. DOI 10.1186/s13742-015-0092-3.

8. Ayres. 2021. Continuous Automotive Software Updates through Container Image Layers. Electronics. DOI 10.3390/electronics10060739.

9. B. 2024. Exploring Large Scale Docker Image Vulnerability and Storage Performance Analysis Using High Performance Container-Based Docker Environment. 2024 International Conference on System, Computation, Automa. DOI 10.1109/icscan62807.2024.10894527.

10. Baltes. 2022. Sampling in software engineering research: a critical review and guidelines. Empirical Software Engineering. DOI 10.1007/s10664-021-10072-8.

11. Begoug. 2024. How Do Infrastructure-as-Code Practitioners Update their Provider Dependencies? An Empirical Study on the AWS Provider. Lecture Notes in Computer Science. DOI 10.1007/978-981-96-0808-9_28.

12. Begoug. 2025. Understanding AWS Provider Dependency Updates in Infrastructure-As-Code: Empirical Study, Taxonomy, and Insights. IEEE Transactions on Services Computing. DOI 10.1109/tsc.2025.3601051.

13. Bhatt. 2020. Reproducible Software Environment: a tool enabling computational reproducibility in geospace sciences and facilitating collaboration. Journal of Space Weather and Space Climate. DOI 10.1051/swsc/2020011.

14. Bommarito. 2019. An Empirical Analysis of the Python Package Index (PyPI). SSRN Electronic Journal. DOI 10.2139/ssrn.3426281.

15. Botto-Tobar. 2026. Is my dependency up-to-date? Exploring challenges with automated dependency updates. DOI 10.21203/rs.3.rs-9390837/v1.

16. Bruccoleri. 2025. Docker Image Builder: A Robust Method for Constructing Docker Images for Reproducible Research. DOI 10.31219/osf.io/8pgd7_v1.

17. Bzeznik. 2017. Nix as HPC package management system. Proceedings of the Fourth International Workshop on HPC User. DOI 10.1145/3152493.3152556.

18. Carbonnel. 2015. Tractability in constraint satisfaction problems: a survey. Constraints. DOI 10.1007/s10601-015-9198-6.

19. Carbonnel. n.d.. Harnessing tractability in constraint satisfaction problems. DOI 10.70675/25f2c2c6zc9f2z4828z8530z8d66a557d24e.

20. Cavezza. 2014. Reproducibility of Environment-Dependent Software Failures: An Experience Report. 2014 IEEE 25th International Symposium on Software Reliabili. DOI 10.1109/issre.2014.19.

21. Cervera. 2026. Reproducibility of Legacy ROS-Based Research Code Through Transparent Docker Integration. IEEE Robotics and Automation Practice. DOI 10.1109/rap.2026.3686662.

22. Chodorowski. 2021. Comparative analysis of JavaScript package managers - yarn and npm. Journal of Computer Sciences Institute. DOI 10.35784/jcsi.2460.

23. Claes. 2015. A Historical Analysis of Debian Package Incompatibilities. 2015 IEEE/ACM 12th Working Conference on Mining Software Rep. DOI 10.1109/msr.2015.27.

24. Cogo. 2021. An Empirical Study of Dependency Downgrades in the npm Ecosystem. IEEE Transactions on Software Engineering. DOI 10.1109/tse.2019.2952130.

25. Cooper. 2010. Generalizing constraint satisfaction on trees: Hybrid tractability and variable elimination. Artificial Intelligence. DOI 10.1016/j.artint.2010.03.002.

26. Decan. 2016. On the topology of package dependency networks. Proccedings of the 10th European Conference on Software Arch. DOI 10.1145/2993412.3003382.

27. Decan. 2018. On the Evolution of Technical Lag in the npm Package Dependency Network. 2018 IEEE International Conference on Software Maintenance a. DOI 10.1109/icsme.2018.00050.

28. Decan. 2021. What Do Package Dependencies Tell Us About Semantic Versioning?. IEEE Transactions on Software Engineering. DOI 10.1109/tse.2019.2918315.

29. Ding. 2024. Towards Scalable and Robust Model Versioning. 2024 IEEE Conference on Secure and Trustworthy Machine Learn. DOI 10.1109/satml59370.2024.00036.

30. Doan. 2022. DAVS: Dockerfile Analysis for Container Image Vulnerability Scanning. Computers, Materials &amp; Continua. DOI 10.32604/cmc.2022.025096.

31. Dutta. n.d.. Survey of Approximation Algorithms for Set Cover Problem. DOI 10.12794/metadc12118.

32. Exman. 2019. Software Modularity Coupling Resolution by the Laplacian of a Bipartite Dependency Graph. Proceedings of the 14th International Conference on Software. DOI 10.5220/0007955802980305.

33. Ferreira. 2026. PERSISTÊNCIA DE VULNERABILIDADES DE DEPENDÊNCIA POR TIPO EM PROJETOS NPM: UMA ANÁLISE DE SOBREVIVÊNCIA SOBRE HISTÓRICOS DE LOCKFILE. Revista Sistemática. DOI 10.56238/rcsv16n8-001.

34. Foote. 2013. Roles and Responsibilities of a Package Maintainer. ROSCon Stutgart 2013. DOI 10.36288/roscon2013-900674.

35. Ganian. 2015. Discovering Archipelagos of Tractability for Constraint Satisfaction and Counting. Proceedings of the Twenty-Seventh Annual ACM-SIAM Symposium. DOI 10.1137/1.9781611974331.ch114.

36. Garthwaite. 2023. Locally correct confidence intervals for a binomial proportion: A new criteria for an interval estimator. Scandinavian Journal of Statistics. DOI 10.1111/sjos.12672.

37. Gibb. 2025. Solving Package Management via Hypergraph Dependency Resolution. DOI 10.59350/nrbbt-e7k85.

38. Gibb. 2026. Package managers à la carte: A Formal Model of Dependency Resolution. DOI 10.59350/rk9s4-43g76.

39. Gonzalez. 2026. sklearn-migrator: Cross-version migration of scikit-learn models for reproducible MLOps. Journal of Open Source Software. DOI 10.21105/joss.10374.

40. Goswami. 2024. Reproducible High Performance Computing without Redundancy with Nix. DOI 10.31219/osf.io/3fp2v.

41. Gu. 2022. <i>pkgndep</i> : a tool for heaviness analysis on R package dependencies. DOI 10.1101/2022.02.11.480073.

42. Guan. 2012. A generalized score confidence interval for a binomial proportion. Journal of Statistical Planning and Inference. DOI 10.1016/j.jspi.2011.09.010.

43. Habtzghi. 2014. Modified Clopper-Pearson Confidence Interval for Binomial Proportion. Journal of Statistical Theory and Applications. DOI 10.2991/jsta.2014.13.4.3.

44. Hatton. 2019. Computational Reproducibility: The Elephant in the Room. IEEE Software. DOI 10.1109/ms.2018.2883805.

45. Heroux. 2011. Improving CSE software through reproducibility requirements. Proceedings of the 4th International Workshop on Software En. DOI 10.1145/1985782.1985787.

46. Hinsen. 2012. The Nix package manager in computational science. DOI 10.59350/c4wzx-s6q80.

47. Hochbaum. 2008. The multi‐integer set cover and the facility terminal cover problem. Networks. DOI 10.1002/net.20265.

48. Härtel. 2023. Operationalizing validity of empirical software engineering studies. Empirical Software Engineering. DOI 10.1007/s10664-023-10370-3.

49. Kechagia. 2010. Open Source Licensing Across Package Dependencies. 2010 14th Panhellenic Conference on Informatics. DOI 10.1109/pci.2010.28.

50. Keller. n.d.. A version numbering scheme with a useful lexicographical order. Proceedings of the Eleventh International Conference on Data. DOI 10.1109/icde.1995.380387.

51. Kim. 2021. A generalized Agresti–Coull type confidence interval for a binomial proportion. Journal of the Korean Statistical Society. DOI 10.1007/s42952-021-00143-3.

52. Kim. 2025. A Robust Framework for Comprehensive Container Image Vulnerability Assessment. IEEE Access. DOI 10.1109/access.2025.3545124.

53. Kowalewski. 2021. Sustainable Packaging of Quantum Chemistry Software with the Nix Package Manager. DOI 10.22541/au.163462780.05778677/v1.

54. Kula. 2023. Promises and Perils of Mining Software Package Ecosystem Data. Software Ecosystems. DOI 10.1007/978-3-031-36060-2_3.

55. Kunstmann. 2024. Scientific Workflow Deployment: Container Provenance in High-Performance Computing. Anais do XXXIX Simpósio Brasileiro de Banco de Dados (SBBD 2. DOI 10.5753/sbbd.2024.240194.

56. Lake. 2025. Analyzing Dependency Clusters and Security Risks in the Maven Central Repository. 2025 IEEE/ACM 22nd International Conference on Mining Softwa. DOI 10.1109/msr66628.2025.00046.

57. Laval. n.d.. Package Dependencies Analysis and Remediation in Object-Oriented Systems. DOI 10.70675/950f31fczd7a0z427dza2a9zf55aa8caf63f.

58. Li. 2023. An Empirical Study of Yanked Releases in the Rust Package Registry. IEEE Transactions on Software Engineering. DOI 10.1109/tse.2022.3152148.

59. Li. 2023. A Large-Scale Empirical Study on Semantic Versioning in Golang Ecosystem. 2023 38th IEEE/ACM International Conference on Automated Sof. DOI 10.1109/ase56229.2023.00140.

60. Lyu. 2025. Detecting Build Dependency Errors by Dynamic Analysis of Build Execution Against Declaration. IEEE Transactions on Software Engineering. DOI 10.1109/tse.2025.3566225.

61. Malka. 2024. Increasing trust in the open source supply chain with reproducible builds and functional package management. Proceedings of the 2024 IEEE/ACM 46th International Conferen. DOI 10.1145/3639478.3639806.

62. Malka. 2025. Does Functional Package Management Enable Reproducible Builds at Scale? Yes. 2025 IEEE/ACM 22nd International Conference on Mining Softwa. DOI 10.1109/msr66628.2025.00115.

63. Mecheo. 2026. DependaFix: A GitHub App for Fixing Breaking Dependency Updates in CI Build for Java Projects. Proceedings of the 34th ACM International Conference on the. DOI 10.1145/3803437.3806404.

64. Miguel. 2004. The Constraint Satisfaction Problem. Dynamic Flexible Constraint Satisfaction and its Application. DOI 10.1007/978-0-85729-378-7_2.

65. Milewicz. 2023. Towards Evidence-Based Software Quality Practices for Reproducibility: Preliminary Results and Research Directions. Proceedings of the 2023 ACM Conference on Reproducibility an. DOI 10.1145/3589806.3600040.

66. Miller. 2025. Understanding the Response to Open-Source Dependency Abandonment in the npm Ecosystem. 2025 IEEE/ACM 47th International Conference on Software Engi. DOI 10.1109/icse55347.2025.00004.

67. Mitra-Behura. 2022. Singularity Containers Improve Reproducibility and Ease of Use in Computational Image Analysis Workflows. Frontiers in Bioinformatics. DOI 10.3389/fbinf.2021.757291.

68. Mittal. 2025. Evaluating Container Security and Reproducibility in Research Software Engineering. DOI 10.36227/techrxiv.175459769.96908041/v1.

69. Montaruli. 2026. SourceBroken: A large-scale analysis on the (un)reliability of SourceRank in the PyPI ecosystem. Proceedings of the 41st ACM/SIGAPP Symposium on Applied Comp. DOI 10.1145/3748522.3779992.

70. Mora‐Cantallops. 2020. Evolution and prospects of the Comprehensive R Archive Network (CRAN) package ecosystem. Journal of Software: Evolution and Process. DOI 10.1002/smr.2270.

71. Nakanishi. n.d.. A metric for evaluating class library interfaces and its application to library upgrades. Proceedings of International Conference on Software Maintena. DOI 10.1109/icsm.1995.526523.

72. Nakata. 2021. Evaluation of Vulnerability Reproducibility in Container-based Cyber Range. Proceedings of the 7th International Conference on Informati. DOI 10.5220/0010324606350642.

73. Nascimento. 2022. Exploring API Deprecation Evolution in JavaScript. 2022 IEEE International Conference on Software Analysis, Evo. DOI 10.1109/saner53432.2022.00031.

74. Opdebeeck. 2021. On the practice of semantic versioning for Ansible galaxy roles: An empirical study and a change classification model. Journal of Systems and Software. DOI 10.1016/j.jss.2021.111059.

75. Pan. 2020. Research on Dynamic Detection of Java Dependency Conflict. 2020 IEEE International Conference on Advances in Electrical. DOI 10.1109/aeeca49918.2020.9213605.

76. Peer. 2020. Active Maintenance: A Proposal for the Long-term Computational Reproducibility of Scientific Results. DOI 10.31235/osf.io/8jwhk.

77. Petersen. 2013. Worldviews, Research Methods, and their Relationship to Validity in Empirical Software Engineering Research. 2013 Joint Conference of the 23rd International Workshop on. DOI 10.1109/iwsm-mensura.2013.22.

78. Pinckney. 2023. Flexible and Optimal Dependency Management via Max-SMT. 2023 IEEE/ACM 45th International Conference on Software Engi. DOI 10.1109/icse48619.2023.00124.

79. Pulicharla. 2024. Data Versioning and Its Impact on Machine Learning Models. Journal of Science &amp; Technology. DOI 10.55662/jst.2024.5101.

80. Qi. 2024. An Empirical Study on Downstream Dependency Package Groups in Software Packaging Ecosystems. IET Software. DOI 10.1049/2024/4488412.

81. Raatikainen. 2025. Machine Learning Lineage for Trustworthy Machine Learning Systems: Information Framework for MLOps Pipelines. IEEE Software. DOI 10.1109/ms.2024.3414317.

82. Rajendran. 2025. PRIMITIVA: Algebraic Decomposition for Zero-Conflict Package Management A Foundational Approach to Eliminating Dependency Hell Through Primitive Operations. DOI 10.2139/ssrn.5753502.

83. Randrianaina. n.d.. Incremental, reproducible builds of software variants. DOI 10.70675/e95564c6zca79z417aza37ez10821a9a0a48.

84. Reyes. 2024. Breaking-Good: Explaining Breaking Dependency Updates with Build Analysis. 2024 IEEE International Conference on Source Code Analysis a. DOI 10.1109/scam63643.2024.00014.

85. Reyes. 2026. Byam: Fixing Breaking Dependency Updates with Large Language Models. Empirical Software Engineering. DOI 10.1007/s10664-026-10835-1.

86. Sandelius. 1952. A Confidence Interval for the Smallest Proportion of a Binomial Population. Journal of the Royal Statistical Society Series B: Statistic. DOI 10.1111/j.2517-6161.1952.tb00105.x.

87. Schmid. 2026. Maven-Lockfile: High Integrity Rebuild of Past Java Releases. Proceedings of the 2026 IEEE/ACM 48th International Conferen. DOI 10.1145/3774748.3787615.

88. Serbout. 2023. Interactively Exploring API Changes and Versioning Consistency. 2023 IEEE Working Conference on Software Visualization (VISS. DOI 10.1109/vissoft60811.2023.00013.

89. Shaffer. 2021. An Empirical Study of Package Dependencies and Lifetimes in Binder Python Containers. 2021 IEEE 17th International Conference on eScience (eScienc. DOI 10.1109/escience51609.2021.00032.

90. Solarin. 2026. It’s Not Just Timestamps: A Study on Docker Reproducibility. Proceedings of the 34th ACM International Conference on the. DOI 10.1145/3803437.3804434.

91. Sousa. 2009. Analysis of the package dependency on Debian GNU/Linux. Journal of Computational Interdisciplinary Sciences. DOI 10.6062/jcis.2009.01.02.0015.

92. Tekin. 2026. Death Is Not the End: a Longitudinal Study on the Impact of Automatic Updates on Container Vulnerability Lifespans. 2026 IEEE Symposium on Security and Privacy (SP). DOI 10.1109/sp63933.2026.00227.

93. Termphaiboon. 2025. Exploring the SECURITY.md in the Dependency Chain: Preliminary Analysis of the PyPI Ecosystem. 2025 40th IEEE/ACM International Conference on Automated Sof. DOI 10.1109/asew67777.2025.00055.

94. Thirumalaisamy. 2025. AI-Assisted Verification of SBOM Accuracy and Drift in Software Supply Chains. International Journal of Computer Trends and Technology. DOI 10.14445/22312803/ijctt-v73i12p103.

95. Turner. 2025. Make your development environment portable and reproducible. DOI 10.59350/gavxb-3e465.

96. Varanasi. 2019. Maven Dependency Management. Introducing Maven. DOI 10.1007/978-1-4842-5410-3_3.

97. Wang. 2025. Understanding and Detecting Peer Dependency Resolving Loop in npm Ecosystem. 2025 IEEE/ACM 47th International Conference on Software Engi. DOI 10.1109/icse55347.2025.00054.

98. Wittern. 2016. A look at the dynamics of the JavaScript package ecosystem. Proceedings of the 13th International Conference on Mining S. DOI 10.1145/2901739.2901743.

99. Wonsil. 2023. Integrated Reproducibility with Self-describing Machine Learning Models. Proceedings of the 2023 ACM Conference on Reproducibility an. DOI 10.1145/3589806.3600039.

100. Wynn Jr.. 2007. Assessing the Health of an Open Source Ecosystem. Emerging Free and Open Source Software Practices. DOI 10.4018/978-1-59904-210-7.ch011.

101. Yang. 2026. Reproducible LLM-Based Measurement Depends on the Serving Stack. DOI 10.2139/ssrn.7083993.

102. Zhu. 2026. Versioned Transitive Dependency-Closure Binding and Operation-Time Effect Governance for Agent Skills: ClosureBound. DOI 10.2139/ssrn.7456458.

