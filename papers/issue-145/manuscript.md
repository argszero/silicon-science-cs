# Attested Is Not Covered: What Published Build Provenance Names, and the Detection Ceiling a Compromised Input Faces

*Issue #145. Contribution level: **theory+empirics** — a proved non-identification result plus a
measurement over three populations and two builder classes.*

## Abstract

Build provenance is now published at scale: npm and PyPI attach signed attestations to package
releases, and container registries attach them to images. The natural reading is that a verifier who
follows such an attestation can learn what went into the artifact. We measure whether that reading
holds, on three frames and two builder classes, and find it does not: **the artifact a provenance
verifier traverses does not carry the dependency closure**, in three deployments that differ in
mechanism and agree in outcome.

On npm (20 stated seeds, 184 packages at depth 1) **82** releases are attested and **52** declare a
non-empty closure; **52 of 52** name **none** of it — **0 of 249** declared dependencies — because
every statement names exactly **one** input, always a source-repository URI. On PyPI (20 stated
seeds, 212 files) **119** files are attested across **15** trusted-publisher identities; **none**
carries a predicate with any input at all, so the closure is not merely uncovered but unmentioned:
**0 of 564** declared dependencies. On container images (10 of 12 named Chainguard images, builder
`apko`, not GitHub Actions) the same **0/313** appears where the closure **is** attested in the same
signed set — a sibling SPDX statement covers **313/313** — so the failure is not missing data but a
statement that does not carry the data its own attestation set holds.

We then prove what such a measurement can and cannot support. Treating the closure as a path, the
detection ceiling is the **joint** probability `P(A₁ ∩ … ∩ A_k)`, not a per-edge rate. The coverage
vector does **not** identify it: with fixed marginals the ceiling ranges over a Fréchet interval
`[max(0, Σcᵢ − (k−1)), min cᵢ]`, both endpoints attained by joint laws with exactly those marginals,
differing by `2^(k−1)` at `cᵢ = 1/2` — so a non-zero ceiling claim owes a correlation structure that
a coverage measurement cannot see. The converse is what makes the empirical result stand: **one
`cᵢ = 0` forces the ceiling to 0 under every joint law**, so the measured zero does not rest on an
untestable independence assumption.

*Claim boundary.* We make no claim about the security of any package, image or publisher, and none
about a real attack; a covered dependency is not thereby benign. The 12 images are a **selection**,
not a sample of any registry, and no frequency is read from them. Two measured builder classes, one
vendor in the container class.

## 1. The problem

A verifier who wants to know what went into an artifact has, in principle, a signed statement to
read. The claim under test in this paper is narrow and falsifiable: **presence of provenance is not
coverage of the input closure.** An attestation can be present, valid, signed by the right identity,
and still name none of the artifact's dependencies.

The distinction matters because it is invisible to the checks that are actually run. Signature
verification asks whether the statement is authentic; it does not ask what the statement says. A
pipeline that verifies signatures therefore passes over a statement whose substantive field is empty,
and reports success. The measurement in §5–§7 is a measurement of that field.

Two things follow, and they organise the paper. First, the empirical question is not "is provenance
adopted" — it plainly is — but "what does the adopted statement name". Second, the *theory* question
is what a coverage number could possibly license: §8 proves that it does not identify the quantity a
security reader wants (the joint probability that a verifier can walk a path to a compromised input),
and §11 states what the empirical zero is worth given that.

## 2. What each layer actually promises

The three layers must be kept apart, because conflating them turns a specification-vs-deployment gap
into a story about vendors that the sources do not support.

**The definition layer.** The SLSA provenance predicate defines a `resolvedDependencies` field for
the artifacts a build fetched, and hedges it: it captures fetched dependencies *"if known"*
[1]. The hedge is doing real work — it converts a promise into a goal.

**The vendor layer.** npm's documentation describes provenance as a verifiable link between a
published package and the source repository and public build instructions that produced it, and
disclaims security inference [2]. PyPI documents
trusted publishing as the registry trusting an identity asserted by an OIDC provider, and its
provenance page is framed around package origin [3]. Neither layer states
that the dependency closure is named.

**The filling layer.** What deployments emit. This is the layer we measure, and the disagreement the
paper reports is between **layer 1 and layer 3**: a specification that asks builders to record fetched
dependencies when they know them, against builders that know them and do not record them. It is not a
disagreement between vendors and their users, and §5–§7 are written so it cannot be read as one.

Two neighbouring constructs are worth separating here because they share the word *attestation*. In
the hardware tradition, remote attestation has a machine measure its own runtime state and report it
to a challenger [4]. That construct answers "what is running"; build
provenance answers "what went in". A reader who imports expectations from the first to the second
will over-read a provenance statement, and the rest of this paper is about the size of that over-read.

Two further literatures supply the vocabulary the paper leans on and are not its subject. Transparency
logs give append-only public ledgers of signed statements [5] [6],
and the update-framework line gives a survivable, signature-checked update path
[7]; reproducible builds give bit-for-bit agreement between independent rebuilds
[8]. Each is a mechanism for making a statement *checkable*. None of them is a
mechanism for making a statement *complete*, which is the gap this paper measures.

## 3. The construct: the closure as a path, and why a per-edge rate is not a ceiling

Take a release `r` whose resolved dependency closure is a rooted DAG with root `r`. A verifier holds
`r`'s published attestation, and can obtain a dependency `q`'s attestation only if `r`'s statement
**names** `q` among its inputs. Detection of a compromise at depth `k` therefore requires every edge
on the path to be named: with `A_i` the event that the attestation at `v_{i-1}` names `v_i`, the
detection predicate is `A_1 ∧ … ∧ A_k`. The *detection ceiling* at depth `k` is `P(D = 1)`.

Two consequences are worth stating before any number. Unnamed is not the same as undeclared: a
package manifest can declare a dependency the attestation does not name, and the OCI frame in §7
shows a set that is *declared* 313 strong while its provenance statement names none of it. And the
unit of coverage is a set operation on package identifiers and digests, not string similarity — a
construct we take from the provenance literature, where provenance is a record of derivation rather
than a name that matches [9] [10] [11], and where
artifact provenance is understood as a description of the process that produced the artifact, not of
its dependencies [12].

The trap is two-level, and the OCI frame in §7 is its cleanest instance: on one edge of the same
signed attestation set the coverage reads **1.000** and on the other **0**. A measurement that
reports one number, or that lets "the attestation set covers everything" stand in for "the statement
a verifier reads covers it", will read the second as the first. §4 states how the instrument keeps
those two readings apart.

## 4. Instrument and its failure modes

Each frame has one enumerator, one snapshot, and one rule about zero. The enumerator writes a JSON
artifact with a sha256 beside it; every number in this paper is read from those artifacts by a script
rather than retyped, which is the construct-validity discipline the measurement literature asks for
when a measure is a proxy for a construct [13] [14]
[15].

**Snapshot discipline.** A frame is enumerated once and frozen. A unit that could not be read is
recorded `NOT RUN` and counted separately; it is never recorded as a zero, because "the instrument
could not ask" and "the answer was none" are different findings. This rule has teeth in §7, where
two of twelve named images require authentication and are reported as NOT RUN — the paper's headline
is over the ten that were read, and says so.

**The plant battery.** A guard that has never been seen to fail is not a guard. The instrument is
exercised on nine planted defects, four of them deliberately wrong *variants* of a correct check —
a checker that refuses everything scores as well as one that refuses nothing unless the variant must
succeed — for **17 of 17** expected outcomes. One mutation survived the first battery and is the
reason the battery has variant rows at all: a rule keyed on the presence of a field cannot see a
malformed row that carries the field.

**Zero needs a positive control.** Every frame is asked for a measurement that *should* come out
positive if the parser is alive. In §7 the sibling SPDX statement in the same signed set covers
313 of 313 declared packages, so the 0 on the provenance edge is a property of that edge rather than
of a dead parser. Where no positive control exists in the frame, the paper says the zero is
uncontrolled.

**Threats the literature names, and where this instrument stands.** Mining-software-repositories
work has established that tool choice and data-extraction choices move results
[16] [17] [18];
that generalisation from a frame is the hard problem, not the measurement
[19] [20]
[21] [22]
[23]; and that reproduction and replication need to be designed rather than
asserted [24] [25]
[26] [27]. Accordingly: every frame
here is a **stated seed set**, not a census; no number in this paper is a registry-wide frequency; and
the seed sets are published so that a reader can re-draw a different one.

## 5. npm: a schema that names the source and not the closure

The frame is 20 stated seeds expanded to depth 1, giving **184** package releases. **82** are
attested. **52** of those declare a non-empty dependency closure.

Of those 52, **52** name none of their declared dependencies: **0 of 249**. Not one attestation in
the frame names a single dependency it declared.

The shape is not a parser gap, and three counts say so. First, every one of the 82 statements carries
exactly **one** input, and that input's URI family is `git` for all 82 — the `other` bucket is empty,
so the input space is not being under-read, it is being read and found to have one inhabitant.
Second, there is exactly **one** build type in the frame — the GitHub Actions workflow build type —
and it accounts for all 82 statements, so the result is not an average over heterogeneous builders
that a different builder would change. Third, the OIDC issuer is populated for **81** of 82 with a
single value, `github.com`; the eighty-second records none. A missing value is not a second platform,
and this paper does not count it as one.

An earlier draft of this package said "one issuer across 82", which was wrong: 81 records carry a
value and one carries none. The correction is stated here rather than quietly applied, because the
distinction between "one identity" and "one identity plus one absence" is exactly the distinction the
paper is about.

That a statement names its source is a coherent design, and the npm ecosystem literature explains why
it is the design that got built: the empirical work on npm is about dependency structure and churn
[28] [29], same-day releases [30],
dependency downgrades [31], trivial packages
[32], popularity metrics [33],
package-manager behaviour [34], maintainer responsiveness
[35] and ecosystem chatter [36] — and the attacks that
motivate provenance in the first place are supply-chain compromises, including one analysed in
detail in this ecosystem [37] [2].
Provenance that pins a package to its source repository answers the question those attacks raise —
*is this the source I think it is* — and does not answer the question a closure verifier asks.

## 6. PyPI: a different mechanism, the same outcome

The frame is 20 stated seeds giving **212** distribution files. **119** are attested, across **15**
distinct trusted-publisher identities, all of them OIDC-asserted GitHub identities
[3].

Here the finding is stronger than in §5, and the taxonomy is what makes it so. **None** of the 119
attested files carries a predicate with any input at all: `attested_with_predicate` is 0 and
`attested_inputs_total` is 0. **47** of the files declare a non-empty closure, and all 47 are at
zero coverage: **0 of 564** declared dependencies.

So the two ecosystems fail differently, and the difference is the paper's point. npm attests *a
source commit*: the statement has an input, the input is one URI, and the closure is not among the
things it names. PyPI attests *a publisher identity*: the statement has no input field populated at
all. Two mechanisms, one number. A study that reported only the coverage rate would have reported
"0 in both" and lost the fact that these are two different objects; the taxonomy is stronger than the
count, and §11 relies on it, because it is why the result is a classification rather than one
measurement repeated.

The PyPI ecosystem's own literature supplies the same orientation: registry-scale empirical work on
the index [38], malicious-code studies
[39] [40], configuration issues
[41], typosquatting and combosquatting against Python names
[42] and cross-language malicious-package detection
[43] [44]
[45] [46]
[47] [48]
[49] [50]
[51] [52]
[53] [54] [55]
[56] [57]
[58] [59]. All of this work detects a bad
package. None of it asks what the published attestation names, which is the question a verifier who
trusts provenance is relying on.

## 7. Container images: where the closure is attested and the statement still omits it

This frame is the paper's lead example in the abstract and in §1, although it is third in measurement
order, because it is the only one that separates **"the data does not exist"** from **"the statement
does not carry it"**.

Twelve named Chainguard images are enumerated; **10** are read and **2** require authentication and
are recorded NOT RUN, never imputed. The 10 carry **30** attestation statements, of which **10** are
provenance statements. The builder is not GitHub Actions: there is exactly one build type, the
`apko` build type, and one builder identity, the `apko` Terraform provider.

`resolvedDependencies` is **absent** in **10 of 10** provenance statements — absent, not empty, which
the artifact records as a distinct state. The declared closure of the ten images is **313** packages,
and the installed closure is **313**.

Coverage of that 313 is **0 by the provenance statement** and **313 by a sibling SPDX statement in
the same signed attestation set**. Both statements are attested, both are signed by the same builder,
and they are read by different consumers: a verifier that traverses provenance reads the first.

This is the measurement that makes the paper's construct claim concrete rather than rhetorical. If
the closure had been unavailable in the frame, the finding would be about the *frame*. It is present,
attested, signed, and 313 of 313 complete — in an artifact adjacent to the one a provenance verifier
reads. The gap is a gap between two artifacts of one publication, not between a publication and the
world. The SBOM literature supplies the vocabulary for the artifact that does carry it
[60] [61]
[62] [63]
[64] [65]
[66] [67]
[68]
[69] [70]
[71] [72]
[73] [74]
[75].

The frame's own limits are stated with the result. The twelve images are a **selection** — named
images from one vendor — and no frequency is read from them; two of twelve were not read at all; and
the builder class is a single one, so nothing here generalises to "container builders". What the
frame does establish is existential and it needs only one instance: a published provenance statement
can omit a closure that its own attestation set contains.

## 8. The ceiling law

The propositions below are proved in the package (`ceiling_law.md`) and verified computationally in
exact rational arithmetic (`ceiling_check.py`, **66 of 66** checks). Nothing here is measured on a
population; the section's job is to say what the measurement in §5–§7 can and cannot license.

**P1 (definition).** The detection ceiling at depth `k` is `P(A_1 ∩ … ∩ A_k)` — the joint
probability of the whole edge set. A per-edge coverage rate is a marginal, and the rest of this
section is about the gap between a marginal and the joint it does not determine.

**P2 (assumption-free upper bound, attained).** `P(D) ≤ minᵢ cᵢ`, and the bound is attained when the
edges are comonotone — one mechanism deciding every edge together, which is what a single build
platform is. *Proof:* the intersection is contained in each `A_i`, so its probability is bounded by
each `c_i`; for attainment take `U` uniform on the unit interval and `A_i = {U ≤ c_i}`.

**P3 (independence).** If the `A_i` are mutually independent, `P(D) = ∏ᵢ cᵢ`.

**P2 and P3 are not two candidate laws about one quantity.** An earlier round of this work framed
them as a choice between a "product law" and a "min law". They are the two **endpoints of an
interval**, and which endpoint applies is a fact about correlation, not a fact about coverage. The
Fréchet bounds this rests on are classical [76]
[77] [78]
[79].

**P4 (the coverage vector does not identify the ceiling).** For `k ≥ 2` and `0 < cᵢ < 1` the ceiling
ranges over

    max(0, Σᵢ cᵢ − (k − 1))  ≤  P(D)  ≤  minᵢ cᵢ,

and **both endpoints are attained by joint laws with exactly the marginals `c`**. At `cᵢ = 1/2` the
endpoints differ by a factor of `2` at `k = 2` (`1/4` against `1/2`) and `4` at `k = 3`
(`1/8` against `1/2`).

This is the paper's sharpest statement about its own instrument: **measuring per-edge input coverage
does not determine the detection ceiling.** The result is the standard partial-identification
conclusion in econometrics — a parameter bounded but not point-identified by the available moments
[80] [81]
[82] [83]
[84] [85]
[86] [87], and the same
logic that governs diagnostic accuracy measured against an imperfect reference
[88]. A coverage measurement is therefore *necessary but not
sufficient* for a ceiling claim, and a paper that states a non-zero ceiling owes the correlation
structure that selects a point inside the interval.

**P5 (the first zero dominates).** If `cᵢ = 0` for any `i` on the path, then `P(D) = 0` under
**every** joint law with those marginals. This is the proposition that makes §5–§7 an empirical
result rather than a restatement of P4: the measured zero does not rest on an untestable
independence assumption. The measured zero *is* the assumption-free floor.

**P6 (which object is actionable).** Because P5 is assumption-free and P4 is not, the actionable
object is the per-edge naming decision — a builder either names a dependency or does not — and not
the coverage rate. This is a claim about where an intervention binds, and it is the reason §9's
recommendations are phrased as "name the closure" rather than "raise coverage".

**The check caught its own author.** The first implementation of the comonotone construction built
the blocks as a prefix rather than a suffix and reported a ceiling of 1 for an **all-zero** path —
the one case P5 forbids. The verification was written before the construction was trusted, and it is
the reason the package carries an exact-arithmetic check rather than a float comparison: a float
`1 − 1e−16` is indistinguishable from a correct answer, and `Fraction` is not.

One further discipline applies to §5–§7 and belongs in the theory section because it is a theory of
reading a zero. A zero count has two explanations that the count cannot separate: the world contains
none, or the instrument cannot see one. A base rate is what separates them
[89], and §11 states the base rates that make the measured zeros readings rather
than absences of evidence.

## 9. Significance: whose belief or decision changes

Three decisions, named, each of which this result changes.

**(i) A policy that reads "has provenance" as "attests its inputs" is reading a different object
than it thinks.** Adoption counts are published and rising; the SLSA literature reports deployment
experience and the challenges of implementing levels [90]
[91] [92], and the supply-chain
security literature documents the attack vectors that motivate adoption
[93] [94]
[95] [96]
[97] [98] [1]. A policy that
counts attested releases as covered dependencies would report progress against a quantity nobody
measured. The measurement here is the one that distinguishes them, and it is cheap: one field.

**(ii) A closure verifier that traverses provenance alone cannot see a compromised input, however
deep it walks, and should say so.** Given P5, a single unnamed edge ends the traversal, so depth
buys nothing once an edge is missing. The concrete advice is in §7: the same signed set that omits
the closure from the provenance statement carries it in a sibling SPDX statement, so the fix is to
traverse the sibling artifact or to state the limit. The dependency-resolution and
package-manager-modelling work explains why the closure is knowable at build time — resolution is a
solved, formalised problem [99] [100], and
transitive-closure binding has been specified [101] — which is what
makes its absence a recording decision rather than a technical impossibility. The same holds for the
risk-scoring and propagation literature, which needs the closure to exist before it can score it
[102] [103]
[104] [105]
[106] [107]
[108].

**(iii) A specification that says `resolvedDependencies` captures dependencies "if known" states a
goal its own deployed builders do not fill.** The hedge is honest, and that is precisely what makes
the deployment gap the measurable thing: the specification does not promise what the deployments do
not deliver, but readers and policies treat presence of provenance as delivery. The gap between
"asked for" and "filled in" is a field-level, countable quantity, and §5–§7 count it.

A fourth audience is the signing effort itself. Sigstore and transparency-log deployment made
signed statements routine [109] [5]; the result here is that
making statements routine does not make them complete, and the two are checked at different layers.
Maintainer-facing work is where the cost of filling the field would land, and it is a real cost
[110] [111]
[112] [113].

## 10. Related work, with the difference from each line

**(a) Build provenance and its specifications.** SLSA and in-toto define what a provenance statement
may contain [1]; implementation studies report what deploying it costs
[90] [91]. *Difference:* these
ask whether the statement exists and is correct; this paper asks what it **names**, and shows a
present, valid statement whose substantive field is empty.

**(b) SBOM completeness and consumption.** SBOM work builds, evaluates and consumes the dependency
listing [60] [61]
[62]. *Difference:* an SBOM is the artifact that **does** carry the
closure in §7; this paper's finding is the gap between it and the provenance statement read by the
verifier, which is why the two literatures are adjacent rather than the same.

**(c) Supply-chain attacks and malicious packages.** Detection, taxonomies and reporting-bias studies
establish that bad packages reach registries [1] [42]
[46]. *Difference:* those measure whether an attack succeeds; this
paper measures whether a verifier could have seen the input, and makes no attack claim at all.

**(d) Reproducible builds and transparency logs.** Bit-for-bit rebuild agreement
[8] [114]
[115] [116] and append-only
public logs [5] [6] make a statement *checkable*. *Difference:*
checkability is orthogonal to completeness, and this paper supplies the case where the first holds
and the second fails.

**(e) Partial identification.** The theory leg is an instance of a well-established result
[81] [80].
*Difference:* the econometrics literature supplies the interval; this paper supplies a construct
(build-time naming) whose measured zero lands on the assumption-free endpoint, which is what converts
a bounds result into an actionable finding.

**(f) Measurement validity.** The framing follows construct-validity work
[13] [14]
[15] and the threats-to-validity literature in empirical
software engineering [16] [19].
*Difference:* the instrument-validity literature is usually applied to surveys and human measures;
here the measure is a field in a signed document, and the error mode is that a document's presence is
read as its content.

**How this list was searched.** A related-work claim is only as strong as the search behind it, so
the search states its form rather than its conclusion. *Indices:* the Crossref REST API
(`api.crossref.org/works`), field `query.bibliographic` — no other index contributed a citation
here. *Terms:* 46 recorded topic queries over provenance, attestation, SBOM, dependency closure and
the package ecosystems, of which **28** produced at least one cited entry. *Window:* counted on
Crossref's `issued` field, **no date filter was applied on either endpoint** — the lower endpoint is
unbounded by choice, and the upper endpoint is the instant of the scan, `2026-10-22T06:10:08Z`, which
is the index's state then rather than a date this paper chose. *Scan date:* `2026-10-22`, the third
time and neither endpoint. The window reaches at least as late as the newest cited work (2026), and
the cited entries span 1952–2026; the comparison is at the granularity the records carry, a year. What
bounds this search is therefore **depth, not time**: each query was read relevance-ranked to 16 rows
with no pagination, so a work ranked below that cut is invisible to it whatever its date, and every
absence claim in this section is scoped to what these queries returned. Records were kept or refused
in two review passes, and the refusals stay in the corpus with a reason; `reference-check.md` prints
the form with each count read from the pool rather than retyped here.

## 11. Threats to validity, and why the result still stands

**Each zero is an "at most", and the bound is the study's own sensitivity.** A count of `0/n` is not
a zero; it is an upper bound. With Wilson intervals, per-unit coverage is at most **6.88 %** on npm
(0/52) and **7.56 %** on PyPI (0/47); per-dependency coverage is at most **1.52 %** (0/249) and
**0.68 %** (0/564); coverage among attested units at most **4.48 %** (0/82) and **3.13 %** (0/119).
Those bounds are the **minimum effect this study can detect**, and they belong beside the claim rather
than in a limitations paragraph: a per-unit rate below about 7 % would very likely have gone unseen.
The measured zero is therefore "at most about 7 % per unit", which is the honest form. The interval
method is the small-sample one appropriate to a proportion near zero, and the alternatives would not
change the reading at these counts [117]
[118] [119]
[120] [121]
[122] [123]
[124] [125]. The
power/MDE literature is the frame for reading a null this way
[126] [127]
[128] [129]
[130].

**Presence and coverage are separated, not correlated.** The presence rate is high and its interval
is far from the coverage interval — npm 82/184 = 0.446 [0.376, 0.518] against coverage 0/52
0 to 0.069; PyPI 119/212 = 0.561 with 0.494 to 0.626 against 0/47 with 0 to 0.076. The intervals are disjoint — stated without
square brackets, because this journal's in-text citation key *is* a bracket number, so an interval
whose left endpoint is 0 is read by the citation gate as a reference to entry 0;
so "attested" and "covered" are not two readings of one variable at these counts. That is the
statistical form of the paper's construct claim.

**The frames are seeds, not samples.** Every frame is a stated seed set expanded one step; none is a
census, and no frequency is read from any of them. An exit from this threat is in the package: the
seed sets are published, so a reader who believes the seeds are unrepresentative can re-draw and
re-run, and the enumerator will report a different number rather than argue.

**The 12 images are a selection, and two were not read.** Named images from one vendor; two require
authentication and are NOT RUN. The paper's headline over that frame is an existence claim — one
published statement omits a closure its own attestation set carries — and an existence claim needs
one instance, which the ten provide.

**One vendor in the container class; two builder classes overall.** Nothing here generalises to "all
container builders" or "all builders". Two classes that differ in mechanism — GitHub Actions and
`apko` — and agree in outcome is a stronger statement than one class would be, and a weaker one than
a claim over builders in general.

**The `if known` hedge is the strongest counter-argument, and it is met here rather than footnoted.**
The specification does not promise the closure; it asks for it when known. A reader may therefore say
the finding is expected. Two answers. First, the field is known at build time for every frame here —
resolution is a solved problem and the OCI frame literally has the closure in the same signed set —
so "known" is satisfied and the field is still not filled. Second, the empirical question is not what
the specification promises but what a verifier receives, and §9(i) names the decision that reads the
second as the first.

**What would falsify the empirical claim.** One attested statement, in any frame, that names a
dependency it declares and is not covered — or a positive per-dependency coverage rate outside the
interval bounds above. The enumerators are published so that this can be attempted against a
different seed set, and the package reports the counts that would do it.

## 12. Registered priors and their outcomes

Three priors were registered before the deciding runs, with a mechanism stated for each. They are
reported here whether or not the data agreed, and a refuted prior is reported as refuted rather than
quietly replaced by a metric chosen after the results were known.

**P1 — "median direct input coverage over attested npm releases is exactly 0, and at least 90 % of
attested npm releases have `c = 0`", justified by mechanism: the statement's input list is what the
builder materialised, which for a registry build is the source commit.** **Supported, and stronger
than stated:** 52 of 52 attested releases with a non-empty closure are at zero (100 %, against a 90 %
floor), the median is 0, and the mechanism shows up directly as the input-URI histogram — one input
per statement, family `git` for all 82, empty `other` bucket.

**P2 — "where `c > 0`, it is a minority carried by a *different build platform*, so coverage is
bimodal across `buildType` and OIDC issuer rather than a continuum".** **Refuted, and the direction of
the refutation is the informative part:** the frame contains exactly **one** build type and **one**
populated issuer, so the second mode P2 predicted does not exist in it, and there is no `c > 0`
anywhere for a mode to be carried by. P2 is not a claim the data can support or undermine — it names
a population the frame does not contain. The lesson is about the design, not the hypothesis: testing
a bimodality claim needs a **multi-platform** frame, and enlarging a homogeneous frame cannot supply
one. This is why §6 is the paper's taxonomy result rather than a second point on a curve. No power
statement is owed here: the finding is a census of the frame's platforms (1 of 1), not a null result
about a rate.

**P3 — "depth-2 coverage is exactly 0 in both ecosystems, so the detection ceiling for a transitive
compromise is 0 rather than a small positive product".** **Supported, and by a stronger route than
registered.** The registered justification was empirical — the probed statements are single-hop. The
measured claim is assumption-free: depth-1 coverage is 0 for every declared dependency in both
ecosystems, and by P5 a single zero on the path forces the ceiling to 0 under *every* joint law, with
no independence assumption and no argument about how platforms correlate. The prior's conclusion
survives; the reason it survives does not depend on the probe.

**What the study could detect, stated with the priors.** A per-unit coverage rate below about
**6.9 %** (npm) and **7.6 %** (PyPI), and a per-dependency rate below **1.5 %** and **0.7 %**, would
very likely have gone unseen. P1's 90 % floor is far outside that blind spot, so its support is not an
artefact of low power. P2's refutation is not a statement about sensitivity at all, because the
quantity it needed — a second platform — is absent from the frame rather than unmeasured within it.

## 13. Baseline, and why this study is not a before/after comparison

The baseline this paper is measured against is the **naive reading**: that presence of provenance
implies coverage of the input closure. That reading is not a straw man — it is what a signature check
reports, and §9(i) names the policy decision that inherits it. The measurement in §5–§7 is a
falsification of that baseline, and the falsification is quantitative: coverage is 0 against a
presence rate of 0.446 (npm) and 0.561 (PyPI), with disjoint intervals.

What is *not* here, and why. There is no before/after comparison of a system against its own prior
state, because this paper builds no system. There is no comparison against a competing
coverage-measuring instrument, because — to the best of our reading of the provenance, SBOM and
registry literature cited in §10 — no published instrument reports this quantity at all: the SBOM
work measures the listing's presence and quality, not the provenance statement's coverage of it; the
SLSA implementation work measures deployment and level compliance, not input naming. The absent
comparison is therefore a statement about the field rather than an omission, and it is the reason
§10's per-line differences are phrased as "these ask a different question" rather than "these do
worse".

**House-pipeline position, stated explicitly.** This is not the journal's census pipeline applied to
a new domain. It introduces a **new construct and a new measurement instrument** — build-time input
naming, measured as set arithmetic between a statement's declared inputs and the artifact's declared
closure — and pairs it with a proved non-identification result. The construct is what makes the
presence/coverage distinction measurable, and §3 defines it before any number is reported.

**Determinism, stated rather than assumed.** Every number here is a deterministic function of a
committed snapshot: no sampling, no random state, no multi-run averaging. The "≥3 independent runs"
requirement for stochastic systems therefore does not apply, and the analogous safeguard is stronger
for this design — the artefacts are pinned by sha256 and re-derived from those pins on every run, so a
number cannot drift without the pin check failing first. The two synthetic components in the package
(the plant battery and the theory's worked cases) demonstrate that the instrument *can* fail and that
the propositions hold. They are held to the rule that synthetic data may prove a pipeline but never a
claim about the world: no empirical claim in this paper rests on them.

## 14. Data and code availability

One command reproduces the three frames and the law (see `README.md`): the enumerators write one
JSON artifact per frame with a sha256 beside it, the law is verified in exact arithmetic, and the
numbers this paper prints are read from those artifacts by script rather than retyped. The
`reference-check.md` in this package lists every citation with the registry record it was verified
against, and the corpus the references were drawn from — including the records refused and why — is
part of the reproducible run.

## References

[1] Ladisa (2023). SoK: Taxonomy of Attacks on Open-Source Software Supply Chains. 2023 IEEE Symposium on Security and Privacy (SP). https://doi.org/10.1109/sp46215.2023.10179304

[2] Samaana (2025). Opportunities and security risks of technical leverage: A replication study on the NPM ecosystem. Empirical Software Engineering. https://doi.org/10.1007/s10664-025-10648-8

[3] Goncalves (2022). OIDC-TCI: OIDC with Trust Context Information. 2022 14th IFIP Wireless and Mobile Networking Conference (WM. https://doi.org/10.23919/wmnc56391.2022.9954295

[4] Prünster (2019). Fides: Unleashing the Full Potential of Remote Attestation. Proceedings of the 16th International Joint Conference on e-. https://doi.org/10.5220/0008121003140321

[5] Laurie (2013). Certificate Transparency. https://doi.org/10.17487/rfc6962

[6] Ryan (2014). Enhanced Certificate Transparency and End-to-End Encrypted Mail. Proceedings 2014 Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2014.23379

[7] Samuel (2010). Survivable key compromise in software update systems. Proceedings of the 17th ACM conference on Computer and communications security. https://doi.org/10.1145/1866307.1866315

[8] Lamb (2022). Reproducible Builds: Increasing the Integrity of Software Supply Chains. IEEE Software. https://doi.org/10.1109/ms.2021.3073045

[9] Buneman (2001). Why and Where: A Characterization of Data Provenance. Lecture Notes in Computer Science. https://doi.org/10.1007/3-540-44503-x_20

[10] Cheney (2007). Provenance in Databases: Why, How, and Where. https://doi.org/10.1561/9781601982339

[11] Muller (2022). How, Where, and Why Data Provenance Improves Query Debugging: A Visual Demonstration of Fine–Grained Provenance Analysis for SQL. 2022 IEEE 38th International Conference on Data Engineering. https://doi.org/10.1109/icde53745.2022.00292

[12] Godfrey (2015). Understanding software artifact provenance. Science of Computer Programming. https://doi.org/10.1016/j.scico.2013.11.021

[13] Cronbach (1955). Construct validity in psychological tests.. Psychological Bulletin. https://doi.org/10.1037/h0040957

[14] Berry (2000). An Instrument for Assessing Software Measurement Programs. Empirical Software Engineering. https://doi.org/10.1023/a:1026534430984

[15] Schneidewind (2001). Knowledge Requirements for Software Quality Measurement. Empirical Software Engineering. https://doi.org/10.1023/a:1011435315749

[16] Hoess (2025). Does the Tool Matter? Exploring Some Causes of Threats to Validity in Mining Software Repositories. 2025 IEEE International Conference on Software Analysis, Evo. https://doi.org/10.1109/saner64311.2025.00067

[17] Mockus (2014). Is mining software repositories data science? (keynote). Proceedings of the 11th Working Conference on Mining Softwar. https://doi.org/10.1145/2597073.2600728

[18] Voinea (2006). Mining software repositories with CVSgrab. Proceedings of the 2006 international workshop on Mining sof. https://doi.org/10.1145/1137983.1138024

[19] Baltes (2022). Sampling in software engineering research: a critical review and guidelines. Empirical Software Engineering. https://doi.org/10.1007/s10664-021-10072-8

[20] Small (2017). Empirical Generalizability. Oxford Scholarship Online. https://doi.org/10.1093/oso/9780190661427.003.0008

[21] de Mello (2014). Sampling improvement in software engineering surveys. Proceedings of the 8th ACM/IEEE International Symposium on E. https://doi.org/10.1145/2652524.2652566

[22] Nunkesser (2026). Assessing the Generalizability of Mobile Software Engineering Research Through Combined Systematic Methods. Software. https://doi.org/10.3390/software5010012

[23] Runeson (n.d.). A case study using sampling to improve software inspection effectiveness. 2003 International Symposium on Empirical Software Engineeri. https://doi.org/10.1109/isese.2003.1237985

[24] González-Barahona (2011). On the reproducibility of empirical software engineering studies based on data retrieved from development repositories. Empirical Software Engineering. https://doi.org/10.1007/s10664-011-9181-9

[25] Juristo (2013). Towards understanding replication of software engineering experiments. 2013 ACM / IEEE International Symposium on Empirical Softwar. https://doi.org/10.1109/esem.2013.64

[26] Brooks (2013). A Partial Replication with a Sample Size of One: A Smoke Test for Empirical Software Engineering. 2013 3rd International Workshop on Replication in Empirical. https://doi.org/10.1109/reser.2013.7

[27] Porter (1998). Comparing Detection Methods For Software Requirements Inspections: A Replication Using Professional Subjects. Empirical Software Engineering. https://doi.org/10.1023/a:1009776104355

[28] Decan (2017). An empirical comparison of dependency issues in OSS packaging ecosystems. 2017 IEEE 24th International Conference on Software Analysis, Evolution and Reengineering (SANER). https://doi.org/10.1109/saner.2017.7884604

[29] Kikas (2017). Structure and Evolution of Package Dependency Networks. 2017 IEEE/ACM 14th International Conference on Mining Software Repositories (MSR). https://doi.org/10.1109/msr.2017.55

[30] Cogo (2021). An empirical study of same-day releases of popular packages in the npm ecosystem. Empirical Software Engineering. https://doi.org/10.1007/s10664-021-09980-6

[31] Cogo (2021). An Empirical Study of Dependency Downgrades in the npm Ecosystem. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2019.2952130

[32] Chowdhury (2022). On the Untriviality of Trivial Packages: An Empirical Study of npm JavaScript Packages. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2021.3068901

[33] Zerouali (2019). On the Diversity of Software Package Popularity Metrics: An Empirical Study of npm. 2019 IEEE 26th International Conference on Software Analysis. https://doi.org/10.1109/saner.2019.8667997

[34] Chodorowski (2021). Comparative analysis of JavaScript package managers - yarn and npm. Journal of Computer Sciences Institute. https://doi.org/10.35784/jcsi.2460

[35] Saeidi (2025). What About Our Bug? A Study on the Responsiveness of NPM Package Maintainers. 2025 ACM/IEEE International Symposium on Empirical Software. https://doi.org/10.1109/esem64174.2025.00071

[36] Islam (2023). An Empirical Study of npm Ecosystem Related Tweets by Core Software Developers: A Case Study. https://doi.org/10.21203/rs.3.rs-2560509/v1

[37] Rayarao (2025). The Shai-Hulud NPM Supply Chain Attack: A Comprehensive Analysis of Self-Replicating Malware in the JavaScript Ecosystem. https://doi.org/10.22541/au.175830854.42750868/v1

[38] Bommarito (2019). An Empirical Analysis of the Python Package Index (PyPI). SSRN Electronic Journal. https://doi.org/10.2139/ssrn.3426281

[39] Guo (2023). An Empirical Study of Malicious Code In PyPI Ecosystem. 2023 38th IEEE/ACM International Conference on Automated Sof. https://doi.org/10.1109/ase56229.2023.00135

[40] Ruohonen (2021). A Large-Scale Security-Oriented Static Analysis of Python Packages in PyPI. 2021 18th International Conference on Privacy, Security and. https://doi.org/10.1109/pst52912.2021.9647791

[41] Peng (2024). Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem. Proceedings of the IEEE/ACM 46th International Conference on. https://doi.org/10.1145/3597503.3639077

[42] Vu (2020). Typosquatting and Combosquatting Attacks on the Python Ecosystem. 2020 IEEE European Symposium on Security and Privacy Workshops (EuroS&amp;PW). https://doi.org/10.1109/eurospw51379.2020.00074

[43] Ladisa (2023). On the Feasibility of Cross-Language Detection of Malicious Packages in npm and PyPI. Annual Computer Security Applications Conference. https://doi.org/10.1145/3627106.3627138

[44] Gandhi (2024). Automated Detection and Mitigation of Malicious Packages in the PyPI Ecosystem and.exe Files: PyGuardEX. 2024 First International Conference for Women in Computing (. https://doi.org/10.1109/incowoco64194.2024.10863220

[45] Montaruli (2025). One Detector Fits All: Robust and Adaptive Detection of Malicious Packages from PyPI to Enterprises. 2025 IEEE Annual Computer Security Applications Conference (. https://doi.org/10.1109/acsac67867.2025.00053

[46] Raszka (2026). Malicious packages in public registries: reporting bias, detection coverage, and the limits of evaluating registry interventions. https://doi.org/10.2139/ssrn.7592667

[47] Lim (2026). Bridging Registry Fragmentation: SBOM-Based Metadata for Generalized Malicious Package Detection. IEEE Access. https://doi.org/10.1109/access.2026.3743923

[48] Zhang (2025). Killing Two Birds with One Stone: Malicious Package Detection in NPM and PyPI using a Single Model of Malicious Behavior Sequence. ACM Transactions on Software Engineering and Methodology. https://doi.org/10.1145/3705304

[49] Liang (2026). Detecting Malicious Packages in PyPI and NPM by Clustering Installation Scripts. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2025.3618952

[50] Liu (2026). Seeing the Forest: A Taxonomy-Guided Analysis and Improvement of Malicious PyPI Package Detectors. Proceedings of the 2nd International Workshop on Software Ge. https://doi.org/10.1145/3844178.3844648

[51] wang (2026). Decoding Maliciousness: A Scalable Framework for Malicious PyPI Package Detection via Multi-source Semantic Fusion. https://doi.org/10.2139/ssrn.6727185

[52] Yan (2026). PyPIMalDet: A malicious PyPI package detection method combining code features and metadata features. Neural Networks. https://doi.org/10.1016/j.neunet.2025.108487

[53] Iqbal (2025). PypiGuard: A novel meta-learning approach for enhanced malicious package detection in PyPI through static-dynamic feature fusion. Journal of Information Security and Applications. https://doi.org/10.1016/j.jisa.2025.104032

[54] Iqbal (2026). CLAMPD-Net: Cross-language malicious package detection across PyPI and NPM with multimodal fusion. Information and Software Technology. https://doi.org/10.1016/j.infsof.2026.108129

[55] Jobu (2026). PyPIGuard: A Lightweight, Explainable Machine Learning Tool for Pre-Install Detection of Malicious PyPI Packages. https://doi.org/10.2139/ssrn.7233262

[56] Wyss (2025). Evaluating LLM-Based Detection of Malicious Package Updates in npm. 2025 28th International Symposium on Research in Attacks, In. https://doi.org/10.1109/raid67961.2025.00047

[57] Moufid (2026). Metadata Compressibility and Evaluation Bias in Malicious Package Detection for NPM and PyPI. Journal of Cybersecurity and Privacy. https://doi.org/10.3390/jcp6050160

[58] Sun (2024). 1+1&gt;2: Integrating Deep Code Behaviors with Metadata Features for Malicious PyPI Package Detection. Proceedings of the 39th IEEE/ACM International Conference on. https://doi.org/10.1145/3691620.3695493

[59] Draz (2026). Version context and control construction in machine learning detection of malicious package updates across npm and PyPI. Scientific Reports. https://doi.org/10.1038/s41598-026-71750-5

[60] Sehgal (2024). A Taxonomy and Survey of Software Bill of Materials (SBOM) Generation Approaches. Communications in Computer and Information Science. https://doi.org/10.1007/978-3-031-50815-8_3

[61] Kishimoto (2025). A Dataset of Software Bill of Materials for Evaluating SBOM Consumption Tools. 2025 IEEE/ACM 22nd International Conference on Mining Softwa. https://doi.org/10.1109/msr66628.2025.00090

[62] Nyambe (2025). Reframing Software Bill of Materials (SBOM) Security Evaluation Using a Model-Based Systems Engineering Approach. 2025 IEEE International Symposium on Systems Engineering (IS. https://doi.org/10.1109/isse65546.2025.11370101

[63] Oberhauser (2025). VR-SBOM: Visualization of Software Bill of Materials and Software Supply Chains in Virtual Reality. Lecture Notes in Business Information Processing. https://doi.org/10.1007/978-3-031-98033-6_4

[64] Hendrick (2022). Software Bill of Materials (SBOM) and Cybersecurity Readiness. https://doi.org/10.70828/rytl5793

[65] O'Donoghue (2023). Impacts of Software Bill of Materials (SBOM) Generation on Vulnerability Detection. Proceedings of the 2024 Workshop on Software Supply Chain Of. https://doi.org/10.1145/3689944.3696164

[66] Lee (2025). Software Bill of Materials(SBOM) Implementation and Evaluation of AI-based Digital Therapeutics. Journal of the Korea Academia-Industrial cooperation Society. https://doi.org/10.5762/kais.2025.26.4.268

[67] Seknametla (2025). Secure Supply Chain Management in DevOps: Addressing Software Bill of Materials (SBOM) Risks. International Journal of Emerging Research in Engineering an. https://doi.org/10.63282/3050-922x.ijeret-v6i2p115

[68] Bamidele Samuel Adelusi (2023). Blockchain-Integrated Software Bill of Materials (SBOM) for Real-Time Vulnerability Detection in Decentralized Package Repositories. International Journal of Scientific Research in Civil Engine. https://doi.org/10.32628/ijsrce237314

[69] Beninger (2024). ERS0: Enhancing Military Cybersecurity with AI-Driven SBOM for Firmware Vulnerability Detection and Asset Management. 2024 16th International Conference on Cyber Conflict: Over t. https://doi.org/10.23919/cycon62501.2024.10685598

[70] Dalia (2025). Come Together: Sbom-Enhanced Vulnerability Assessment in Safety-Critical Systems. https://doi.org/10.2139/ssrn.5362510

[71] Jang (2026). A Machine Learning-Based Vulnerability Prediction System Using SBOM Metadata for Software Supply Chain Security. The Journal of Korean Institute of Communications and Inform. https://doi.org/10.7840/kics.2026.51.4.792

[72] Kawai (2026). Mission-Aware SBOM Vulnerability Triage with KEV/EPSS and LLM-Based VEX Drafting. 2026 23rd International Joint Conference on Computer Science. https://doi.org/10.1109/jcsse68839.2026.11597025

[73] Mydin (2026). SBOM Tooling Ecosystem: A Systematic Literature Review. Applied Research. https://doi.org/10.1002/appl.70209

[74] SHTOMA (2025). SBOM-BASED VULNERABILITY PRIORITIZATION IN SOFTWARE SUPPLY CHAIN USING MACHINE LEARNING. Advanced Information Technology. https://doi.org/10.17721/ait.2025.2.04

[75] Radanliev (2023). ML) in Software Vulnerability Management: automations in the Software Bill of Materials (SBOM) and the Vulnerability-Exploitability eXchange (VEX). https://doi.org/10.36227/techrxiv.23706684.v1

[76] Rüschendorf (1991). FréChet-Bounds and Their Applications. Advances in Probability Distributions with Given Marginals. https://doi.org/10.1007/978-94-011-3466-8_9

[77] Rüschendorf (1996). Developments on Fréchet-bounds. Institute of Mathematical Statistics Lecture Notes - Monogra. https://doi.org/10.1214/lnms/1215452625

[78] Scarsini (1997). Fréchet Classes and Nonmonotone Dependence. Distributions with given Marginals and Moment Problems. https://doi.org/10.1007/978-94-011-5532-8_7

[79] Skřivánek (2014). Basic bounds of Fréchet classes. Kybernetika. https://doi.org/10.14736/kyb-2014-1-0095

[80] (no author in the registry record) (2020). Microeconometrics with partial identification. Handbook of Econometrics. https://doi.org/10.1016/bs.hoe.2020.05.002

[81] Molinari (2019). Econometrics with Partial Identification. https://doi.org/10.1920/wp.cem.2019.2519

[82] Molinari (2008). Partial identification of probability distributions with misclassified data. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2007.12.003

[83] McAdams (2008). Partial identification and testable restrictions in multi-unit auctions. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2008.07.003

[84] Hong (2017). Inference in semiparametric conditional moment models with partial identification. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2016.09.014

[85] Jiang (2017). On limiting distribution of quasi-posteriors under partial identification. Econometrics and Statistics. https://doi.org/10.1016/j.ecosta.2017.03.006

[86] Fan (2018). Partial identification and inference in censored quantile regression. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2018.04.002

[87] Beresteanu (2012). Partial identification using random set theory. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2011.06.003

[88] Obradović (2024). Measuring diagnostic test performance using imperfect reference tests: A partial identification approach. Journal of Econometrics. https://doi.org/10.1016/j.jeconom.2024.105842

[89] Bar-Hillel (1977). The Base-Rate Fallacy in Probability Judgments. https://doi.org/10.21236/ada045772

[90] Ghanshyambhai Patel (2025). Software Supply Chain Security: Implementing SLSA Compliance in CI/CD Pipelines. International Journal for Research Trends and Innovation. https://doi.org/10.56975/ijrti.v10i7.205129

[91] Mohomed (2025). ARGO-SLSA: Software Supply Chain Security in Argo Workflows. 2025 Moratuwa Engineering Research Conference (MERCon). https://doi.org/10.1109/mercon67903.2025.11217128

[92] Tamanna (2025). Unraveling Challenges with Supply-Chain Levels for Software Artifacts (Slsa) for Securing the Software Supply Chain. https://doi.org/10.2139/ssrn.5119626

[93] Cesarano (2023). GoSurf: Identifying Software Supply Chain Attack Vectors in Go. Proceedings of the 2024 Workshop on Software Supply Chain Of. https://doi.org/10.1145/3689944.3696166

[94] Reyes (2025). Maven-Hijack: Software Supply Chain Attack Exploiting Packaging Order. Proceedings of the 2025 Workshop on Software Supply Chain Of. https://doi.org/10.1145/3733827.3765523

[95] Chen (2023). Runtime Verification for Software Supply Chain Security using Confidential Computing. Proceedings of the 2024 Workshop on Software Supply Chain Of. https://doi.org/10.1145/3689944.3696350

[96] Williams (2024). Narrowing the Software Supply Chain Attack Vectors: The SSDF Is Wonderful but not Enough. IEEE Security &amp; Privacy. https://doi.org/10.1109/msec.2024.3359798

[97] Kerman (2025). Software Supply Chain and DevOps Security Practices. https://doi.org/10.6028/nist.sp.1800-44

[98] Soeiro (n.d.). Assessing the Security of Software Supply Chains: Software Bill of Materials, Threat Propagation, and Logical Attack Graphs. https://doi.org/10.70675/6dd72cb7z7135z4d1dza942z3f6c57308033

[99] Gibb (2025). Solving Package Management via Hypergraph Dependency Resolution. https://doi.org/10.59350/nrbbt-e7k85

[100] Gibb (2026). Package managers à la carte: A Formal Model of Dependency Resolution. https://doi.org/10.59350/rk9s4-43g76

[101] Zhu (2026). Versioned Transitive Dependency-Closure Binding and Operation-Time Effect Governance for Agent Skills: ClosureBound. https://doi.org/10.2139/ssrn.7456458

[102] Teng (2026). Supply Chain Software Package Risk Scoring TD3-MPC Model Based on Dependency Metadata Graph. Journal of Applied Automation Technologies. https://doi.org/10.64972/jaat.2026v4.386p31e:413-425

[103] Liu (2022). Demystifying the vulnerability propagation and its evolution via dependency trees in the NPM ecosystem. Proceedings of the 44th International Conference on Software. https://doi.org/10.1145/3510003.3510142

[104] Gao (2026). LLM-Enhanced Evolutionary Dependency Graphs: A System Approach to Precise Vulnerability Propagation Tracking. Mathematics. https://doi.org/10.3390/math14142593

[105] Abdalkareem (2022). A Machine Learning Approach to Determine the Semantic Versioning Type of NPM Packages Releases. https://doi.org/10.2139/ssrn.4082606

[106] Decan (2021). What Do Package Dependencies Tell Us About Semantic Versioning?. IEEE Transactions on Software Engineering. https://doi.org/10.1109/tse.2019.2918315

[107] Panter (2025). PVAC: package version activity categorizer, leveraging semantic versioning in a heterogeneous system. Empirical Software Engineering. https://doi.org/10.1007/s10664-025-10678-2

[108] Tang (2026). Package selection and versioning matter. Nature Methods. https://doi.org/10.1038/s41592-026-03108-8

[109] Newman (2022). Sigstore. Proceedings of the 2022 ACM SIGSAC Conference on Computer an. https://doi.org/10.1145/3548606.3560596

[110] Dias (2021). What Makes a Great Maintainer of Open Source Projects?. 2021 IEEE/ACM 43rd International Conference on Software Engi. https://doi.org/10.1109/icse43902.2021.00093

[111] Hendrick (2023). Maintainer Perspectives on Open Source Software Security: Survey-based Insights from Maintainers Regarding How They Address Best Practices for Secure Software Development. https://doi.org/10.70828/pvsn3075

[112] Linåker (2024). Sustaining Maintenance Labor for Healthy Open Source Software Projects through Human Infrastructure: A Maintainer Perspective. Proceedings of the 18th ACM/IEEE International Symposium on. https://doi.org/10.1145/3674805.3686667

[113] Salmon (2026). How to Recruit a New Maintainer for Your Package. https://doi.org/10.59350/qgdfk-ce602

[114] Randrianaina (n.d.). Incremental, reproducible builds of software variants. https://doi.org/10.70675/e95564c6zca79z417aza37ez10821a9a0a48

[115] Goswami (2024). Reproducible High Performance Computing without Redundancy with Nix. https://doi.org/10.31219/osf.io/3fp2v

[116] (no author in the registry record) (2017). Workflow-ready bioinformatics packages and Debian’s infrastructure for low-friction reproducible research. https://doi.org/10.7490/f1000research.1114468.1

[117] Afshartous (2008). Sample Size Determination for Binomial Proportion Confidence Intervals. The American Statistician. https://doi.org/10.1198/000313008x271474

[118] Balayla (2024). Gaussian Distribution, Confidence Intervals, Binomial (Wald) Proportion, Wilson Score Interval and Delta Theorem. Theorems on the Prevalence Threshold and the Geometry of Scr. https://doi.org/10.1007/978-3-031-71452-8_13

[119] Garthwaite (2023). Locally correct confidence intervals for a binomial proportion: A new criteria for an interval estimator. Scandinavian Journal of Statistics. https://doi.org/10.1111/sjos.12672

[120] Guan (2012). A generalized score confidence interval for a binomial proportion. Journal of Statistical Planning and Inference. https://doi.org/10.1016/j.jspi.2011.09.010

[121] Habtzghi (2014). Modified Clopper-Pearson Confidence Interval for Binomial Proportion. Journal of Statistical Theory and Applications. https://doi.org/10.2991/jsta.2014.13.4.3

[122] Kim (2021). A generalized Agresti–Coull type confidence interval for a binomial proportion. Journal of the Korean Statistical Society. https://doi.org/10.1007/s42952-021-00143-3

[123] Nawa (2022). A weighted score confidence interval for a binomial proportion. Japanese Journal of Statistics and Data Science. https://doi.org/10.1007/s42081-022-00146-2

[124] Sandelius (1952). A Confidence Interval for the Smallest Proportion of a Binomial Population. Journal of the Royal Statistical Society Series B: Statistic. https://doi.org/10.1111/j.2517-6161.1952.tb00105.x

[125] Tang (2005). Confidence interval construction for proportion difference in small‐sample paired studies. Statistics in Medicine. https://doi.org/10.1002/sim.2216

[126] (no author in the registry record) (2015). Power calculation for causal inference in social science: sample size and minimum detectable effect determination. https://doi.org/10.23846/wp0026

[127] Brydges (2019). Effect Size Interpretation, Sample Size Calculation, and Statistical Power in Gerontology. https://doi.org/10.31234/osf.io/u2jbm

[128] Dalgaard (2023). What minimal detectable effect size is in your power – An inverted sample size formular for survival data. European Psychiatry. https://doi.org/10.1192/j.eurpsy.2023.1139

[129] Greenland (1985). Power, sample size and smallest detectable effect determination for multivariate studies. Statistics in Medicine. https://doi.org/10.1002/sim.4780040203

[130] Hunter (2024). PUMP: Estimating Power, Minimum Detectable Effect Size, and Sample Size When Adjusting for Multiple Outcomes in Multi-Level Experiments. Journal of Statistical Software. https://doi.org/10.18637/jss.v108.i06
