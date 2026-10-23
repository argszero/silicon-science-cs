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
[@ladisa2023sok]. The hedge is doing real work — it converts a promise into a goal.

**The vendor layer.** npm's documentation describes provenance as a verifiable link between a
published package and the source repository and public build instructions that produced it, and
disclaims security inference [@samaana2025opportunitiessecurityrisks]. PyPI documents
trusted publishing as the registry trusting an identity asserted by an OIDC provider, and its
provenance page is framed around package origin [@goncalves2022oidctcioidc]. Neither layer states
that the dependency closure is named.

**The filling layer.** What deployments emit. This is the layer we measure, and the disagreement the
paper reports is between **layer 1 and layer 3**: a specification that asks builders to record fetched
dependencies when they know them, against builders that know them and do not record them. It is not a
disagreement between vendors and their users, and §5–§7 are written so it cannot be read as one.

Two neighbouring constructs are worth separating here because they share the word *attestation*. In
the hardware tradition, remote attestation has a machine measure its own runtime state and report it
to a challenger [@prnster2019fidesunleashingfull]. That construct answers "what is running"; build
provenance answers "what went in". A reader who imports expectations from the first to the second
will over-read a provenance statement, and the rest of this paper is about the size of that over-read.

Two further literatures supply the vocabulary the paper leans on and are not its subject. Transparency
logs give append-only public ledgers of signed statements [@laurie2014certificate] [@ryan2014enhanced],
and the update-framework line gives a survivable, signature-checked update path
[@samuel2010survivable]; reproducible builds give bit-for-bit agreement between independent rebuilds
[@lamb2022reproducible]. Each is a mechanism for making a statement *checkable*. None of them is a
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
than a name that matches [@buneman2001why] [@cheney2009provenance] [@muller2022howwherewhy], and where
artifact provenance is understood as a description of the process that produced the artifact, not of
its dependencies [@godfrey2015understandingsoftwareartifact].

The trap is two-level, and the OCI frame in §7 is its cleanest instance: on one edge of the same
signed attestation set the coverage reads **1.000** and on the other **0**. A measurement that
reports one number, or that lets "the attestation set covers everything" stand in for "the statement
a verifier reads covers it", will read the second as the first. §4 states how the instrument keeps
those two readings apart.

## 4. Instrument and its failure modes

Each frame has one enumerator, one snapshot, and one rule about zero. The enumerator writes a JSON
artifact with a sha256 beside it; every number in this paper is read from those artifacts by a script
rather than retyped, which is the construct-validity discipline the measurement literature asks for
when a measure is a proxy for a construct [@cronbach1955construct] [@berry2000instrumentassessingsoftware]
[@schneidewind2001knowledgerequirementssoftware].

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
[@hoess2025doestoolmatter] [@mockus2014miningsoftwarerepositories] [@voinea2006miningsoftwarerepositories];
that generalisation from a frame is the hard problem, not the measurement
[@baltes2022samplingsoftwareengineering] [@small2017empiricalgeneralizability]
[@demello2014samplingimprovementsoftware] [@nunkesser2026assessinggeneralizabilitymobile]
[@runesonndcasestudysampling]; and that reproduction and replication need to be designed rather than
asserted [@gonzlezbarahona2011reproducibilityempiricalsoftware] [@juristo2013understandingreplicationsoftware]
[@brooks2013partialreplicationsample] [@porter1998comparingdetectionmethods]. Accordingly: every frame
here is a **stated seed set**, not a census; no number in this paper is a registry-wide frequency; and
the seed sets are published so that a reader can re-draw a different one.

## 5. npm: a schema that names the source and not the closure

The frame is 20 stated seeds expanded to depth 1, giving **184** package releases <!-- c: npm.summary.units -->. **82** are
attested <!-- c: npm.summary.attested -->. **52** of those declare a non-empty dependency closure <!-- c: npm.summary.attested_with_deps -->. Every one of the 184 was read: **0** NOT RUN and **0** undecodable payloads <!-- c: npm.summary.not_run --> <!-- c: npm.summary.undecodable_payloads -->.

Of those 52, **52** name none of their declared dependencies: **0 of 249** <!-- c: npm.summary.attested_zero_coverage --> <!-- c: npm.summary.deps_total --> <!-- c: npm.summary.deps_covered_total -->. Not one attestation in
the frame names a single dependency it declared, so **0** of the 184 packages has positive
coverage <!-- c: npm.summary.attested_positive_coverage -->.

The shape is not a parser gap, and three counts say so. First, every one of the 82 statements carries
exactly **one** input, and that input's URI family is `git` for all 82 <!-- c: npm.summary.input_families --> — the `other` bucket is empty,
so the input space is not being under-read, it is being read and found to have one inhabitant.
Second, there is exactly **one** build type in the frame <!-- c: npm.summary.build_types (len) --> — the GitHub Actions workflow build type —
and it accounts for all 82 statements <!-- c: npm.summary.build_types -->, so the result is not an average over heterogeneous builders
that a different builder would change. Third, the OIDC issuer is populated for **81** of 82 <!-- c: npm.summary.oidc_issuers --> with a
single value, `github.com`; the eighty-second records none. A missing value is not a second platform,
and this paper does not count it as one.

An earlier draft of this package said "one issuer across 82", which was wrong: 81 records carry a
value and one carries none. The correction is stated here rather than quietly applied, because the
distinction between "one identity" and "one identity plus one absence" is exactly the distinction the
paper is about.

That a statement names its source is a coherent design, and the npm ecosystem literature explains why
it is the design that got built: the empirical work on npm is about dependency structure and churn
[@decan2019evolution] [@kikas2020structure], same-day releases [@cogo2021empiricalstudysame],
dependency downgrades [@cogo2021empiricalstudydependency], trivial packages
[@chowdhury2022untrivialitytrivialpackages], popularity metrics [@zerouali2019diversitysoftwarepackage],
package-manager behaviour [@chodorowski2021comparativeanalysisjavascript], maintainer responsiveness
[@saeidi2025whataboutour] and ecosystem chatter [@islam2023empiricalstudynpm] — and the attacks that
motivate provenance in the first place are supply-chain compromises, including one analysed in
detail in this ecosystem [@rayarao2025shaihuludnpm] [@samaana2025opportunitiessecurityrisks].
Provenance that pins a package to its source repository answers the question those attacks raise —
*is this the source I think it is* — and does not answer the question a closure verifier asks.

## 6. PyPI: a different mechanism, the same outcome

The frame is 20 stated seeds giving **212** distribution files <!-- c: pypi.summary.files -->. **119** are attested <!-- c: pypi.summary.attested_files -->, across **15**
distinct trusted-publisher identities <!-- c: pypi.summary.publishers (len) -->, all of them OIDC-asserted GitHub identities
[@goncalves2022oidctcioidc].

Here the finding is stronger than in §5, and the taxonomy is what makes it so. **None** of the 119
attested files carries a predicate with any input at all: `attested_with_predicate` is 0 <!-- c: pypi.summary.attested_with_predicate --> and
`attested_inputs_total` is 0 <!-- c: pypi.summary.attested_inputs_total -->. Every one of the 212 was read: **0** NOT RUN <!-- c: pypi.summary.files_not_run -->. **47** of the files declare a non-empty closure <!-- c: pypi.summary.attested_with_deps -->, and all 47 are at
zero coverage <!-- c: pypi.summary.attested_zero_coverage -->: **0 of 564** <!-- c: pypi.summary.deps_total --> <!-- c: pypi.summary.deps_covered --> declared dependencies.

So the two ecosystems fail differently, and the difference is the paper's point. npm attests *a
source commit*: the statement has an input, the input is one URI, and the closure is not among the
things it names. PyPI attests *a publisher identity*: the statement has no input field populated at
all. Two mechanisms, one number. A study that reported only the coverage rate would have reported
"0 in both" and lost the fact that these are two different objects; the taxonomy is stronger than the
count, and §11 relies on it, because it is why the result is a classification rather than one
measurement repeated.

The PyPI ecosystem's own literature supplies the same orientation: registry-scale empirical work on
the index [@bommarito2019empiricalanalysispython], malicious-code studies
[@guo2023empiricalstudymalicious] [@ruohonen2021largescalesecurity], configuration issues
[@peng2024lessmoreempirical], typosquatting and combosquatting against Python names
[@vu2021typosquatting] and cross-language malicious-package detection
[@ladisa2023feasibilitycrosslanguage] [@gandhi2024automateddetectionmitigation]
[@montaruli2025onedetectorfits] [@raszka2026maliciouspackagespublic]
[@lim2026bridgingregistryfragmentation] [@zhang2025killingtwobirds]
[@liang2026detectingmaliciouspackages] [@liu2026seeingforesttaxonomy]
[@wang2026decodingmaliciousnessscalable] [@yan2026pypimaldetmaliciouspypi]
[@iqbal2025pypiguardnovelmeta] [@iqbal2026clampdnetcross] [@jobu2026pypiguardlightweightexplainable]
[@wyss2025evaluatingllmbased] [@moufid2026metadatacompressibilityevaluation]
[@sun2024integratingdeepcode] [@draz2026versioncontextcontrol]. All of this work detects a bad
package. None of it asks what the published attestation names, which is the question a verifier who
trusts provenance is relying on.

## 7. Container images: where the closure is attested and the statement still omits it

This frame is the paper's lead example in the abstract and in §1, although it is third in measurement
order, because it is the only one that separates **"the data does not exist"** from **"the statement
does not carry it"**.

Twelve named Chainguard images are enumerated <!-- c: oci.summary.images -->; **10** are read <!-- c: oci.summary.images_ok --> and **2** require authentication and
are recorded NOT RUN <!-- c: oci.summary.images_not_run -->, never imputed. The 10 carry **30** attestation statements <!-- c: oci.summary.statements -->, of which **10** are
provenance statements <!-- c: oci.summary.provenance_statements -->. The builder is not GitHub Actions: there is exactly one build type <!-- c: oci.summary.build_types (len) -->, the
`apko` build type, and one builder identity <!-- c: oci.summary.builder_ids (len) -->, the `apko` Terraform provider.

`resolvedDependencies` is **absent** in **10 of 10** provenance statements — absent, not empty, which
the artifact records as a distinct state, and **0** of the 10 carries a positive
`resolvedDependencies` <!-- c: oci.summary.provenance_with_positive_resolvedDependencies -->. The declared closure of the ten images is **313** packages <!-- c: oci.rows[].closure.declared_n (sum over OK) -->,
and the installed closure is **313** <!-- c: oci.rows[].closure.installed_n (sum over OK) -->.

Coverage of that 313 is **0 by the provenance statement** <!-- c: oci.rows[].closure.declared_covered_by_provenance (sum over OK) --> and **313 by a sibling SPDX statement in
the same signed attestation set** <!-- c: oci.rows[].closure.declared_covered_by_spdx (sum over OK) -->. Both statements are attested, both are signed by the same builder,
and they are read by different consumers: a verifier that traverses provenance reads the first.

This is the measurement that makes the paper's construct claim concrete rather than rhetorical. If
the closure had been unavailable in the frame, the finding would be about the *frame*. It is present,
attested, signed, and 313 of 313 complete — in an artifact adjacent to the one a provenance verifier
reads. The gap is a gap between two artifacts of one publication, not between a publication and the
world. The SBOM literature supplies the vocabulary for the artifact that does carry it
[@sehgal2024taxonomysurveysoftware] [@kishimoto2025datasetsoftwarebill]
[@nyambe2025reframingsoftwarebill] [@oberhauser2025sbomvisualizationsoftware]
[@hendrick2022softwarebillmaterials] [@odonoghue2023impactssoftwarebill]
[@lee2025softwarebillmaterials] [@seknametla2025securesupplychain]
[@bamidelesamueladelusi2023blockchainintegratedsoftware]
[@beninger2024ers0enhancingmilitary] [@dalia2025cometogethersbom]
[@jang2026machinelearningbased] [@kawai2026missionawaresbom]
[@mydin2026sbomtoolingecosystem] [@shtoma2025sbombasedvulnerability]
[@radanliev2023softwarevulnerabilitymanagement].

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
Fréchet bounds this rests on are classical [@rschendorf1991frechetboundstheir]
[@rschendorf1996developmentsfrechetbounds] [@scarsini1997frechetclassesnonmonotone]
[@skivnek2014basicboundsfrechet].

**P4 (the coverage vector does not identify the ceiling).** For `k ≥ 2` and `0 < cᵢ < 1` the ceiling
ranges over

    max(0, Σᵢ cᵢ − (k − 1))  ≤  P(D)  ≤  minᵢ cᵢ,

and **both endpoints are attained by joint laws with exactly the marginals `c`**. At `cᵢ = 1/2` the
endpoints differ by a factor of `2` at `k = 2` (`1/4` against `1/2`) and `4` at `k = 3`
(`1/8` against `1/2`).

This is the paper's sharpest statement about its own instrument: **measuring per-edge input coverage
does not determine the detection ceiling.** The result is the standard partial-identification
conclusion in econometrics — a parameter bounded but not point-identified by the available moments
[@anon2020microeconometricspartialidentification] [@molinari2019econometricspartialidentification]
[@molinari2008partialidentificationprobability] [@mcadams2008partialidentificationtestable]
[@hong2017inferencesemiparametricconditional] [@jiang2017limitingdistributionquasi]
[@fan2018partialidentificationinference] [@beresteanu2012partialidentificationrandom], and the same
logic that governs diagnostic accuracy measured against an imperfect reference
[@obradovi2024measuringdiagnostictest]. A coverage measurement is therefore *necessary but not
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
[@base_rate_fallacy], and §11 states the base rates that make the measured zeros readings rather
than absences of evidence.

## 9. Significance: whose belief or decision changes

Three decisions, named, each of which this result changes.

**(i) A policy that reads "has provenance" as "attests its inputs" is reading a different object
than it thinks.** Adoption counts are published and rising; the SLSA literature reports deployment
experience and the challenges of implementing levels [@ghanshyambhaipatel2025softwaresupplychain]
[@mohomed2025argoslsasoftware] [@tamanna2025unravelingchallengessupply], and the supply-chain
security literature documents the attack vectors that motivate adoption
[@cesarano2023gosurfidentifyingsoftware] [@reyes2025mavenhijacksoftware]
[@chen2023runtimeverificationsoftware] [@williams2024narrowingsoftwaresupply]
[@kerman2025softwaresupplychain] [@soeirondassessingsecuritysoftware] [@ladisa2023sok]. A policy that
counts attested releases as covered dependencies would report progress against a quantity nobody
measured. The measurement here is the one that distinguishes them, and it is cheap: one field.

**(ii) A closure verifier that traverses provenance alone cannot see a compromised input, however
deep it walks, and should say so.** Given P5, a single unnamed edge ends the traversal, so depth
buys nothing once an edge is missing. The concrete advice is in §7: the same signed set that omits
the closure from the provenance statement carries it in a sibling SPDX statement, so the fix is to
traverse the sibling artifact or to state the limit. The dependency-resolution and
package-manager-modelling work explains why the closure is knowable at build time — resolution is a
solved, formalised problem [@gibb2025solvingpackagemanagement] [@gibb2026packagemanagerscarte], and
transitive-closure binding has been specified [@zhu2026versionedtransitivedependency] — which is what
makes its absence a recording decision rather than a technical impossibility. The same holds for the
risk-scoring and propagation literature, which needs the closure to exist before it can score it
[@teng2026supplychainsoftware] [@liu2022demystifyingvulnerabilitypropagation]
[@gao2026llmenhancedevolutionary] [@abdalkareem2022machinelearningapproach]
[@decan2021whatpackagedependencies] [@panter2025pvacpackageversion]
[@tang2026packageselectionversioning].

**(iii) A specification that says `resolvedDependencies` captures dependencies "if known" states a
goal its own deployed builders do not fill.** The hedge is honest, and that is precisely what makes
the deployment gap the measurable thing: the specification does not promise what the deployments do
not deliver, but readers and policies treat presence of provenance as delivery. The gap between
"asked for" and "filled in" is a field-level, countable quantity, and §5–§7 count it.

A fourth audience is the signing effort itself. Sigstore and transparency-log deployment made
signed statements routine [@newman2022sigstore] [@laurie2014certificate]; the result here is that
making statements routine does not make them complete, and the two are checked at different layers.
Maintainer-facing work is where the cost of filling the field would land, and it is a real cost
[@dias2021whatmakesgreat] [@hendrick2023maintainerperspectivesopen]
[@linker2024sustainingmaintenancelabor] [@salmon2026howrecruitnew].

## 10. Related work, with the difference from each line

**(a) Build provenance and its specifications.** SLSA and in-toto define what a provenance statement
may contain [@ladisa2023sok]; implementation studies report what deploying it costs
[@ghanshyambhaipatel2025softwaresupplychain] [@mohomed2025argoslsasoftware]. *Difference:* these
ask whether the statement exists and is correct; this paper asks what it **names**, and shows a
present, valid statement whose substantive field is empty.

**(b) SBOM completeness and consumption.** SBOM work builds, evaluates and consumes the dependency
listing [@sehgal2024taxonomysurveysoftware] [@kishimoto2025datasetsoftwarebill]
[@nyambe2025reframingsoftwarebill]. *Difference:* an SBOM is the artifact that **does** carry the
closure in §7; this paper's finding is the gap between it and the provenance statement read by the
verifier, which is why the two literatures are adjacent rather than the same.

**(c) Supply-chain attacks and malicious packages.** Detection, taxonomies and reporting-bias studies
establish that bad packages reach registries [@ladisa2023sok] [@vu2021typosquatting]
[@raszka2026maliciouspackagespublic]. *Difference:* those measure whether an attack succeeds; this
paper measures whether a verifier could have seen the input, and makes no attack claim at all.

**(d) Reproducible builds and transparency logs.** Bit-for-bit rebuild agreement
[@lamb2022reproducible] [@randrianainandincrementalreproduciblebuilds]
[@goswami2024reproduciblehighperformance] [@anon2017workflowreadybioinformatics] and append-only
public logs [@laurie2014certificate] [@ryan2014enhanced] make a statement *checkable*. *Difference:*
checkability is orthogonal to completeness, and this paper supplies the case where the first holds
and the second fails.

**(e) Partial identification.** The theory leg is an instance of a well-established result
[@molinari2019econometricspartialidentification] [@anon2020microeconometricspartialidentification].
*Difference:* the econometrics literature supplies the interval; this paper supplies a construct
(build-time naming) whose measured zero lands on the assumption-free endpoint, which is what converts
a bounds result into an actionable finding.

**(f) Measurement validity.** The framing follows construct-validity work
[@cronbach1955construct] [@berry2000instrumentassessingsoftware]
[@schneidewind2001knowledgerequirementssoftware] and the threats-to-validity literature in empirical
software engineering [@hoess2025doestoolmatter] [@baltes2022samplingsoftwareengineering].
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
change the reading at these counts [@afshartous2008samplesizedetermination]
[@balayla2024gaussiandistributionconfidence] [@garthwaite2023locallycorrectconfidence]
[@guan2012generalizedscoreconfidence] [@habtzghi2014modifiedclopperpearson]
[@kim2021generalizedagresticoull] [@nawa2022weightedscoreconfidence]
[@sandelius1952confidenceintervalsmallest] [@tang2005confidenceintervalconstruction]. The
power/MDE literature is the frame for reading a null this way
[@anon2015powercalculationcausal] [@brydges2019effectsizeinterpretation]
[@dalgaard2023whatminimaldetectable] [@greenland1985powersamplesize]
[@hunter2024pumpestimatingpower].

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

<!--REFERENCE-LIST-->
