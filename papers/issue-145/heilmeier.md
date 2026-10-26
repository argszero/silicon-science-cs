# Heilmeier record — issue #145

**Title**: Attested Is Not Covered: The Dependency-Closure Coverage of Published Build Provenance,
and the Detection Ceiling a Compromised Input Faces

Registered 2026-10-21 (R669). Registration thread: issue #145.
Status: **research, round 1** (nothing measured beyond the pilot probe in `probe_coverage.py`).

## Six Heilmeier answers

1. **Problem** — For attested releases in two public registries (npm, PyPI), what fraction of the
   build's declared **dependency closure** is named as a resolved dependency by that release's own
   provenance statement? Falsifiable core: median direct coverage *c* = 0, depth-2 coverage = 0; a
   median *c* ≥ 0.5 in either ecosystem, or depth-2 > depth-1 in either, refutes it.
2. **Current approaches & limitations** — the literature measures adoption (presence) and dependency
   *risk*, or builds systems on top of a closure it assumes is available:
   - *ClosureBound* (arXiv:2609.05920, 2026-09-05): a reference monitor; precondition "complete
     mediation and discovery". Assumes the closure, does not measure what attestations carry.
   - *Certified Multi-Source Integrity* (arXiv, 2026-09-28): measures **independence** of witnesses
     (shared origin collapses them); 450 supply-chain packages. Independence ≠ coverage: a witness can
     be independent and still unnamed.
   - *Attestable Audit* (2026-10-03), *Provable Authority* (2026-10-16): chain/protocol design.
   - SBOM-completeness audits: the object is the SBOM, not the attestation statement a registry
     verifies.
   None joins a published statement to the published closure of the same release.
3. **Novelty** — new constructs, exactly measured: **input coverage** (closure-relative, per release)
   and the **detection ceiling** for a poisoned input at depth *k*; plus the law separating the two
   regimes a consumer conflates — per-edge product (independence) vs step-collapse to zero (one
   platform attesting a fixed input set for every build).
4. **Who cares** — consumers and the tooling advising them (the gate is on presence, a different
   quantity); registry/SLSA spec authors (`resolvedDependencies` compliance vs closure); system
   builders whose preconditions fail on deployed data.
5. **Success metrics** — exact per-ecosystem coverage distributions over **every** enumerated attested
   release, *n* and enumeration rule stated; presence-vs-coverage ratio with Wilson interval; depth-2
   count; byte-identical re-run from a committed snapshot + plant battery.
6. **Risks & fallback** — (i) npm payload shape may not be representative → split the population by
   `buildType` + OIDC issuer, turning the risk into the second half of the result; (ii) live-API drift
   → commit a dated snapshot with digests and make reproduction read the snapshot.

## Adversarial checks (as registered)

- **Reverse gap** — search form stated in the issue: arXiv API metadata fields (`all:`, `abs:`),
  submission date, unbounded below through **2026-10-21**: `all:"build provenance" AND all:completeness`
  → 0; `abs:"npm provenance"` → 0; `all:attestation AND all:"resolved dependencies"` → 0;
  `all:provenance AND all:"dependency closure"` → 3 (nearest = ClosureBound, a system).
  Claim narrowed to that space; Crossref / IEEE-ACM full text / SBOM literature named as *not reached*.
  Structural reasons: the join crosses two independently hosted surfaces; SLSA requires
  `resolvedDependencies` to **exist** but not to cover the closure; dashboards publish a binary.
- **Evidence pre-assessment** — PASS, measured 2026-10-21 not asserted: npm abbreviated packument
  exposes `dist.attestations` per version (5 of 6 sampled top packages attested; `chalk` not);
  `https://registry.npmjs.org/-/npm/v1/attestations/sigstore@5.0.0` returns 2 statements (npm publish
  v0.1, SLSA provenance v1) and the SLSA v1 `resolvedDependencies` holds **1** entry
  (`git+https://github.com/sigstore/sigstore-js@refs/heads/main`, `gitCommit` digest, no dependency
  digest); PyPI Simple JSON 1.4 exposes per-file `provenance` URLs
  (`https://pypi.org/integrity/<p>/<v>/<f>/provenance`), confirmed on `pypi-attestations`
  0.0.28–0.0.30. Ground truth exact by construction; baseline = the presence indicator.
- **Upgradability** — more ecosystems; a longitudinal panel over repeated snapshots; the law extended
  from per-edge product to chained attestations with correlated platforms.

## Stated priors (registered before the deciding runs)

- **P1** — median direct coverage over attested npm releases = **0**; ≥90 % have *c* = 0.
  Justification: the runner resolves dependencies inside itself; the statement names what the builder
  materialised, which for a registry build is the source commit (probed payload matches the mechanism).
- **P2** — where *c* > 0 it is bimodal across (buildType, OIDC issuer): a property of the *builder's
  implementation*, not of the package.
- **P3** — depth-2 coverage exactly **0** in both ecosystems: no field points at a dependency's own
  statement; published statements are single-hop.

**Registered success criteria**: exact distributions with *n* and enumeration rule stated; the
presence/coverage separation as a ratio with a Wilson interval; a plant battery that FAILs on a
zero-coverage statement and measures exactly *m/n* on a partial one. Contradictions reported as
refuted with the failed criterion; no metric re-chosen after the results are known.

### Prior outcomes (recorded R674, after the deciding runs — the priors above are unchanged)

- **P1 — confirmed.** npm frame of 20 stated seeds expanded to depth 1 (**184** units): **82**
  attested, **52** declaring a non-empty closure, **52/52** at *c* = 0, **0 of 249** declared
  dependencies named. Criterion met. (`snapshot_npm_d1_pilot.json`, sha256 `d3bde499…`.)
- **P2 — refuted, with a direction.** The npm frame holds **1** `buildType` (82/82) and **1**
  *populated* OIDC issuer value, `github.com` (81/82 — the 82nd, `@standard-schema/spec@1.1.0`,
  records none), so there is no second platform for positive coverage to cluster
  onto: the mechanism P2 names is **not observable in this frame**. Recorded as refuted, not as
  confirmed — the claim needs a *multi-platform* frame, and PyPI is not it either (**15** distinct
  Trusted Publisher identities, all emitting `predicate: null`; 119 attested files, 0 inputs, 0 of
  564 declared dependencies covered). Criterion **unmet**: the frame has no positive-coverage
  population to test the clustering on.
- **P3 — confirmed, stronger than registered.** Not merely depth-2 = 0: no published statement names
  *any* package, so a second hop is inexpressible rather than merely unobserved. Ceiling 0 at every
  depth in both ecosystems. Criterion met.

**Success criteria, marked:** (i) exact distributions with *n* and enumeration rule — **met**;
(ii) presence-vs-coverage separation as a ratio with a Wilson interval — **met** as of the R674
addendum: `wilson_separation.py`, presence 82/184 [0.3757, 0.5179] vs coverage 0/52 [0, 0.0688] on
npm and 119/212 vs 0/47 on PyPI, disjoint in both;
(iii) plant battery FAILs on zero-coverage and measures exactly *m/n* on partial — **met** (9 plants,
4 wrong variants, 17/17 checks, the battery itself mutation-tested).

## Round log

- **R669 (2026-10-21)** — direction selected from the external scan (attestation/authority cluster in
  cs.CR: 5 works in ~6 weeks) and from the project-matched rant `2026-10-13T03:44` (sealing authority:
  "sealed/attested/verified" are claims about a *writer*). Candidate rejected earlier for failing the
  evidence check: a measurement of *who seals* real registries needs a ground truth for "authority
  outside the auditee" that the published data cannot supply; the coverage construct needs none.
  Next: build the enumeration over attested releases; snapshot with digests; plant battery first.
- **R669, pilot (`probe_coverage.py`)** — 6 hand-picked npm packages, instrument end to end:
  **6/6 attested**, **6/6 zero coverage**, **0 of 23 declared dependencies covered**, every statement
  naming exactly **1** input and that input a `git+https://…` source URL. Read with its denominator:
  three of the six (`zod`, `undici`, `playwright-core`) declare no dependencies, so *c* is `n/a` there
  and the 23 are the three packages that do. **PILOT — not a population claim.**
  Risk this pilot makes visible, to be answered before any manuscript: if the population answer is
  uniformly 0, the paper is a **boundary** paper — the ceiling is set by the builder, and the study's
  job is to show the builder is the only variable that moves it (split by `buildType` + OIDC issuer,
  plus the PyPI ecosystem) — not a survey that reports "0" and stops. If npm and PyPI are both
  uniformly 0 and no platform emits closure-bearing statements, the honest claim narrows to "the
  deployed builders cannot express the closure", which is a weaker but still measured result; the
  stop-go checkpoint must weigh that framing rather than let it drift into a snapshot.

## R670 (2026-10-21) — the plant battery, and the first framed measurement

### What changed

1. **The instrument was split into pure functions** (`coverage.py`): `parse_purl`,
   `parse_npm_tarball`, `identified_package`, `coverage`, `decode_statements`,
   `attested_inputs`, `build_type`, `oidc_issuer`. The construct's load-bearing distinction —
   *a build's source-repository URI is an input, and is not a closure member* — is now a
   named return value (`identified_package` returns `None` for it), not a comment.
2. **The plant battery exists and was mutation-tested** (`plant_coverage.py`): 9 plants,
   4 deliberately wrong variants, **17/17 checks**, exit 0.
   - plants: source-only statement · sibling package named · empty closure · exact 2/5 ·
     scoped purl · registry tarball · purl with qualifiers/subpath · non-package inputs ·
     source repo named like the dep.
   - wrong variants **caught**: `any_input_counts` (A1/A4/A8/A9), `substring_match` (A2),
     `empty_closure_is_zero` (A3), `last_path_token` (A9).
   - **The battery was then mutated rather than trusted**: replacing `identified_package`
     with a last-path-token reader turned the battery red (exit 1) — *after* the A9 plant was
     added. The first version of the battery **missed that mutation**, which is why A9 exists:
     a plant that only carries a `git+…/repo@refs/heads/main` form never reaches a reader that
     strips the ref, and `github.com/facebook/react` is exactly the shape where the repo name
     and the package name coincide.
3. **The enumerator runs with a stated frame** (`enumerate.py`): seeds (20 named packages) →
   closure over declared `dependencies` breadth-first to `--depth` → one unit per
   (package, latest version). Snapshot written with a retrieval timestamp and a SHA-256.

### The measurement (npm, frame: 20 seeds, depth 1, closure 184 packages)

Run 2026-10-21, elapsed **77.0 s**, snapshot `snapshot_npm_d1_pilot.json`
sha256 `d3bde4995928b04cedb1a2d45f594c7faae1c29cca10cbb2736a105dec764b59`.

| quantity | value | denominator |
|---|---|---|
| units measured | 184 | the whole frame |
| `NOT RUN` | **0** | 184 |
| attested | 82 | 184 units |
| attested **with a non-empty closure** | 52 | 82 attested |
| of those, **zero coverage** | **52** | 52 |
| of those, positive coverage | **0** | 52 |
| declared dependencies in the covered-with-deps set | 249 | — |
| of those, covered | **0** | 249 |
| statements per attested release | 2 (all 82) | — |
| named inputs per attested release | **1** (all 82) | — |
| input URI families over 82 inputs | `git: 82`, everything else **0** | 82 |
| undecodable payloads | 0 | 82 |
| distinct `buildType` | **1** — `slsa-framework.github.io/github-actions-buildtypes/workflow/v1` | 82 |
| distinct OIDC issuer, populated | **1** — `github.com` | 81 |
| attested releases with **no** issuer recorded | **1** — `@standard-schema/spec@1.1.0` | 82 |

The three facts that matter, in order:

- **The input set is a single git URI, always.** Not "mostly git": 82 of 82, and the family
  histogram has no `other` bucket, so this is not a parser missing a form — there is no other
  form present to miss. A statement naming exactly one input, and that input the source repo,
  covers no closure member at any depth.
- **Coverage is 0 in 52 of 52 releases that have a closure to cover**, over 249 declared
  dependencies (median 3 per package, max 28). The 30 attested packages outside that count
  declare no dependencies; their `c` is **n/a**, not 0, and they are not in the 52.
- **The population is homogeneous, not bimodal.** One `buildType` in 82 of 82, one *populated*
  issuer value in 81 of 82 (the 82nd has none recorded), 2 statements, 1 input, in every attested
  release. The issuer axis is therefore not constant in the strict sense — it carries one missing
  value — but it carries no second *platform*. This is a **refutation of P2's mechanism as stated**:
  P2 predicted coverage would cluster across *several* builders, with a minority emitting
  closure-bearing statements. There is one builder in this frame, so the frame cannot show
  builder variance at all — and the honest reading is the stronger one: the ceiling is a
  property of a single dominant platform, not a distribution across platforms.

### What this does and does not support

- **Supports**: P1 (median `c` = 0) — observed 52/52 at `c` = 0.
- **Supports, more strongly than registered**: P3 (depth-2 coverage exactly 0) — no statement
  names any package, so no traversal to a dependency's own statement is even expressible;
  the ceiling is 0 at *every* depth, including depth 1.
- **Refutes, with a direction**: **P2**. Not "coverage is not bimodal across builders" as a
  general claim — within this frame there is nothing to be bimodal *across*. The refutation
  is that the mechanism P2 named (different platforms emit different input sets) is not
  visible because one platform produces all 82 statements. Restating P2 as a claim that needs
  a multi-platform frame is the correction; it must NOT be reported as confirmed.
- **Does not support**: any claim about npm as a whole. The frame is a 20-seed depth-1
  closure, chosen because it is re-derivable, and 184 packages is a frame, not a population.
  A registry-wide claim needs a registry-wide enumeration rule, which npm does not offer.

### The framing decision this forces (for the stop-go checkpoint at R671)

A uniform 0 with a single builder is a **boundary** result, and a boundary paper needs the
*builder* to be the variable. Two things must therefore be in the package before this can be
called a contribution rather than a snapshot:

- **a heterogeneous frame** (depth ≥ 2 and/or a second ecosystem — PyPI via Simple JSON 1.4
  `files[].provenance`) so that "one builder" is a measured property of the frame rather than
  an artifact of which 20 seeds were chosen;
- **the positive control the real world did not supply**: a statement that names a purl must
  measure a non-zero `c` on the real pipeline, which today exists only as plant A5/A6/A7.
  Without a real positive instance, the paper's claim is about *absence*, and its evidence
  must be the family histogram (nothing in `other`) rather than any non-zero reading.

## R671 (2026-10-21) — STOP-GO REVIEW (third-round trigger, fired as scheduled at R670)

Written **before** any further measurement this round, so that the criteria cannot be shaped by
what the next run returns.

### (a) What would falsify this direction

Ordered by how much of the direction each one destroys:

1. **The denominator is not recoverable.** If a release's declared dependency closure cannot be
   read from the registry for most attested releases — because manifests carry ranges that only a
   lockfile resolves, or because the registry does not serve the manifest — then `c` is not a
   well-defined quantity and the study has no unit of measurement. **Kills the direction.**
2. **A real positive population exists at scale.** If a frame wider than the one measured (deeper
   closure, a second ecosystem, or more seeds) finds a non-trivial share — say ≥10 % — of attested
   releases with `c > 0`, then "attested is not covered" is false as a general statement and the
   direction survives only as "which builder covers", a narrower question.
3. **The claim has no addressee.** If no spec, no registry UI and no tooling ever asserts or
   implies that provenance covers the dependency closure, then the paper measures a gap nobody
   claims: the significance argument in Heilmeier 4 collapses to a strawman, and the honest
   outcome is to abandon or to reposition as a spec-design note. **This is the risk the
   registration under-weighted**, and it is testable by reading the primary documents rather
   than by another measurement.

### (b) What evidence exists, and what it does and does not support

**Exists** (all measured, artefact and date named):

- an instrument whose construct is enforced rather than commented: `coverage.py`, with
  `identified_package` returning `None` for a source-repository URI;
- a plant battery of 9 plants + 4 wrong variants, **17/17**, demonstrated to go red under a
  mutation it initially missed (the A9 episode, recorded at R670);
- one framed measurement, npm depth 1: **82 attested of 184 units; 52 of those with a non-empty
  closure; 52/52 at `c = 0`; 0 of 249 declared dependencies covered; every statement carries
  exactly 1 input; input-URI families `git: 82` with an empty `other` bucket; 1 `buildType`;
  1 populated OIDC issuer value, 81/82 with one release recording none**
  (`snapshot_npm_d1_pilot.json`, sha256 `d3bde499…`, 2026-10-21).

**Supports**: the construct is measurable end to end on live registry data; within that frame the
answer is uniformly 0 and the 0 is *structural* (the histogram has no other category to miss), not
a parsing artifact; and the deployed producer is a single platform, so the input set is a property
of that platform's implementation rather than of the packages.

**Does not support**: any statement about npm at large (20 seeds, depth 1 — a frame, not a
population); any statement about a *distribution* across builders (one builder produced all 82
statements, so P2's mechanism is unobservable here and is reported refuted-with-a-direction, not
confirmed); any claim resting on a real positive instance (no attested release in the frame names a
package at all — the positive path exists only as plant A5/A6/A7, and must be labelled synthetic).

**Therefore the direction is not yet a contribution**: it is one frame of a boundary result, and
the two things the paper needs — a heterogeneous frame, and an addressee who actually claims the
thing being measured — are both still outside the evidence.

### (c) Decision: **CONTINUE** — and the falsifier that decided it

Falsifier 2 said: *a real positive population at scale kills the general claim.* It was tested on
the second ecosystem this round, and it did **not** fire. Falsifier 3 (no addressee) remains open
and is named below as the thing that would change the answer.

**PyPI measured 2026-10-21** (`snapshot_pypi.json`, sha256 `9a285cc2…`, 239.5 s, frame: 20 stated
seeds → latest version per project → every file of that version):

| quantity | value | denominator |
|---|---|---|
| files fetched | **212** | 212 (`NOT RUN` = **0**) |
| attested files | **119** | 212 |
| statements carrying a **predicate** at all | **0** | 119 |
| statement inputs total | **0** | 119 (all `n_statement_inputs = 0`) |
| undecodable statements | **0** | 119 |
| predicate types present | **1** — `docs.pypi.org/attestations/publish/v1` | — |
| **distinct Trusted Publisher identities** | **15** | 119 files |
| attested files with a non-empty declared closure | 47 | 119 |
| of those, **zero coverage** | **47** | 47 |
| declared dependencies / covered | **0 of 564** | — |

**Why this settles the "one platform" objection from R670.** R670's honest caveat was that a single
`buildType` and a single populated issuer value meant the frame could not show builder variance — so "0" might have
been an artifact of one platform. PyPI answers it on the axis that matters: **15 distinct Trusted
Publisher identities** (`numpy-release/wheels.yml`, `psf/black/pypi_upload.yml`,
`pydantic/ci.yml`, …), across 20 projects, and **not one of their statements carries an input list**.
The zero therefore survives a frame with real producer variance. The mechanism is a *specification
choice*, not one platform's bug: PyPI's publish attestation has `predicate: null` by design.

**The result is a taxonomy, not a number**, and that is what upgrades it beyond a snapshot:

| ecosystem | what the statement names | inputs per statement | distinct producers measured |
|---|---|---|---|
| npm (SLSA v1) | the **source commit** | exactly 1, `git+…` | **1** |
| PyPI (publish/v1) | the **publisher identity** (repo + workflow), outside the statement | **0** | **15** |

Both give a detection ceiling of **0** for a poisoned input at every depth, for *different reasons* —
npm because the only input it names is the source, PyPI because it names no input at all. A paper
that reported "coverage = 0" for both would have hidden the only interesting difference.

### What would still change the answer (the condition recorded with the decision)

**Falsifier 3 is open**: no document yet read *claims* that these attestations cover the input
closure. SLSA v1.0 states that "all artifacts fetched during initialization or execution of the build
process are considered dependencies … The `resolvedDependencies` captures these dependencies, **if
known**", and gives the git-commit case as its own example — so the spec licenses exactly the gap
measured, and hedges it with three words. Until an addressee is established from a primary document
(a registry's consumer-facing claim, a compliance framework that treats "has provenance" as input
attestation, or a policy that waives review on the badge), the significance argument must be built on
what the badges **do** attest — producer identity — and not on "consumers are misled", which this
study cannot measure.

**If that read finds no addressee, the next stop-go downgrades to `case study`** rather than
inventing one. The claim boundary is therefore fixed now: *this study measures what published
attestations name; it does not measure what anyone believes they name.*

## R672 (2026-10-21) — the addressee read: falsifier 3 answered, and the significance argument corrected

The stop-go decision at R671 fixed this round's task: find whether anyone actually **claims** that a
published attestation covers the build's dependency closure. Falsifier 3 said that if nobody does,
the significance argument collapses. Three primary documents were read, in their own words.

### What each layer actually says (quoted, not paraphrased)

**1. The registry layer does not make the claim — it explicitly disclaims the inference.**

npm, *Generating provenance statements* (docs.npmjs.com, read 2026-10-21):

> "When a package in the npm registry has established provenance, **it does not guarantee the package
> has no malicious code**. Instead, npm provenance provides a verifiable link to the package's
> **source code and build instructions**, which developers can then audit and determine whether to
> trust it or not."

and, earlier on the same page, provenance "allows you to publicly establish **where a package was
built and who published** a package".

PyPI's documentation files the topic under **"Checking Provenance (package origin)"** and describes
attestations as "publicly verifiable proof that a package was published via a specific Trusted
Publisher, or more general SLSA Provenance attesting to a package's **original source location**"
(docs.pypi.org/attestations).

**2. The specification layer does make it — hedged by three words.**

SLSA v1.0, *Provenance* (slsa.dev/spec/v1.0/provenance, read 2026-10-21):

> "**All artifacts fetched during initialization or execution of the build process are considered
> dependencies**, including those referenced directly by parameters. The `resolvedDependencies`
> captures these dependencies, **if known**. For example, a build that takes a git repository URI as
> a parameter might record the specific git commit that the URI resolved to as a dependency."

**3. The systems literature assumes it, as a precondition.**

As registered: *ClosureBound* (arXiv:2609.05920) builds a reference monitor whose stated
preconditions include "complete mediation and discovery" of the closure; *Certified Multi-Source
Integrity* needs witnesses it can count.

### The finding, stated so that it decides the framing

- **Falsifier 3 does NOT fire in its registered form.** An addressee exists. It is **not** the
  consumer facing a badge — it is **the spec text** that defines the field, and the **systems
  literature** that reads a closure out of it.
- **But the weaker framing I registered at R669 is dead and must be corrected.** "Consumers are
  misled into thinking provenance covers inputs" is **not supported**: npm disclaims the security
  inference in a dedicated paragraph (*Provenance limitations*), and PyPI scopes the artifact to
  *origin*. Neither vendor claims closure coverage. A paper built on consumer confusion would be
  measuring a strawman — and a reviewer reading those two paragraphs would say so in one sentence.
- **What survives, and is sharper**: the divergence is *inside the stack*. The field that npm's
  statements are nominally conformant to (`resolvedDependencies`, SLSA v1) is defined as "all
  artifacts fetched during the build"; the values actually published are a single git commit
  (`n=82`, R670) or absent entirely (`n=119`, R671). Both vendors fulfil **exactly what their own
  docs claim** — so the measurement is not a compliance failure, it is a **definition gap between
  the layer that specifies the field and the layer that fills it**. Systems that read the field as
  the closure over-read it by construction.

### Consequence for the significance statement (Heilmeier 4, corrected)

The community whose belief changes is **not** "package consumers"; it is:

- **spec authors** (SLSA working group): whether `resolvedDependencies` means "the inputs the builder
  happened to know" — which is what "if known" permits and what every deployed builder produces — or
  "the build's input closure", which nothing measured provides;
- **authors of closure-dependent systems** (ClosureBound and the multi-source certifier): their
  preconditions are stated over a closure that no measured attestation carries, so the precondition
  is unmet on real artifacts;
- **registry policy**: whether a "has provenance" gate can be read as input attestation. Measured
  answer: no, and the vendors already say so — which means the decision that changes is a *policy
  decision someone would otherwise make*, not one already made and wrong.

The decision that changes: **whether to treat `resolvedDependencies` as a closure** — in a spec
revision, in a verifier's trust model, or in a paper's precondition. That is a real decision, held by
a named group, and this study is the measurement that decides it.

### What this round does not do

No new measurement was taken (none was needed: the claim under test was documentary). The ceiling law
(per-edge product vs step-collapse) is still unformalised and is the next round's work; the paper
cannot claim `theory+empirics` until that law is stated as a proposition and checked against the two
measured ecosystems rather than asserted in prose.

**Status: continue.** The significance argument is now anchored to a divergence that two vendors'
own documentation makes visible, instead of to a misreading nobody committed.

### A registered belief that may need correcting — flagged, not silently moved

The registration states the law as a **per-edge product** (independence regime) versus a **step
collapse** (single-platform regime). Reading the measured data against it suggests a **third and
sharper form** that I did not register: a **min-law** — the detection ceiling for a compromise at
depth *k* is bounded by the **worst-covered edge on the path**, not by a product, because one
unnamed edge makes the traversal impossible no matter how well every other edge is covered. Under a
product law, raising coverage from 0.1 to 0.2 everywhere multiplies the ceiling; under a min-law it
changes nothing until the zero is removed, which is a different and much more actionable statement
for a spec author.

The two forms coincide when every edge has the same coverage and differ sharply when they do not, so
the measured ecosystems (all-zero) cannot separate them — **the distinction needs a frame with mixed
coverage, which does not yet exist.** Recorded here as a **candidate refinement to be settled next
round**, with the registration's `Outcome` line to report it as *retained-but-reframed* if it stands.
It is not adopted now: a law changed after seeing the data, without a frame that could distinguish
the two, would be exactly the goalpost-moving the registration's success criteria forbid.

## R674 (2026-10-21) — the ceiling formalised: five propositions, and the registered law reframed

The stop-go decision at R671 required the detection ceiling to stop being prose before the package
could claim `theory+empirics`. It is now `ceiling_law.md` (statements + proofs) and
`ceiling_check.py` (exact verification: **66/66 checks**, `Fraction` throughout, no seed, no draw).

### The propositions

1. **Definition.** The ceiling is the joint probability of the whole edge set on the path,
   `P(A_1 ∩ … ∩ A_k)` — not a per-edge quantity. This is the whole reason the construct needs care.
2. **Fréchet upper bound, assumption-free.** `P(D) ≤ min_i c_i`, **attained** when the edges are
   comonotone (one mechanism decides them together — which is what a single build platform is).
3. **Independence.** `P(D) = ∏ c_i`.
4. **Non-identification.** With fixed marginals and `k ≥ 2`, the ceiling ranges over the Fréchet
   interval `[max(0, Σc_i − (k−1)), min c_i]`, and **both endpoints are attained**. At `c_i = 1/2`
   the two endpoints differ by `2^(k−1)`: `1/4` vs `1/2` at `k=2`, `1/8` vs `1/2` at `k=3`.
5. **The first zero dominates.** If any `c_i = 0`, the ceiling is `0` at every depth under **every**
   joint law, and the Fréchet interval collapses to `{0}`.
6. **Which object is actionable.** Raising uniform coverage from `0.1` to `0.3` multiplies the
   independence ceiling by `3^k` while moving the assumption-free bound only `3×`.

### The registered law is reframed, not confirmed — and the registration's `Outcome` line must say so

The registration stated the law as a choice between a **per-edge product** and a **step collapse**,
and R671 recorded a candidate **min-law** as an unsettled refinement. Both readings were wrong in the
same way: they are **not competing laws about one quantity**. Proposition 3 shows the product is the
value **under independence**; Proposition 2 shows the minimum is an **assumption-free upper bound**
attained under **perfect dependence**. They are the two **endpoints of an interval** whose width is
set by a correlation the coverage measurement does not observe.

So the honest outcome for the registered prior is **retained-but-reframed**: the phenomenon it named
is real, the dichotomy it proposed is not the right shape, and the sharper statement — **the coverage
vector does not identify the ceiling** — is stronger than what was registered, because it is a
statement about the instrument's own limits and it is proved rather than measured.

### What this buys the empirical leg, and what it costs it

**Buys**: Proposition 5 makes the two measured ecosystems' `0` **robust to the assumption the paper
cannot test**. Every `c_i = 0` on every path means the ceiling is 0 under independence, under
comonotonicity, and under every mixture — so the empirical claim rests on no unverified independence
assumption. That is a stronger footing than the registration had.

**Costs**: Proposition 4 says the coverage measurement alone **cannot** deliver a non-zero ceiling,
even if a future frame found positive coverage. A ceiling claim therefore owes the correlation
structure too, which in deployed terms means naming the builder — and Proposition 4 is the reason the
next measurement must be multi-platform rather than merely larger.

### A defect the check caught in its own author's code

The first version of the comonotone law builder wrote a **prefix** of the sorted thresholds instead
of a **suffix**, which made a zero-marginal event hold anyway, and it reported a ceiling of **1** for
an all-zero path. That is not a typo in a test: it is the exact real-world hazard the proposition
exists to name — claiming a poisoned input is detectable when the traversal actually stops at the
first unattested edge. The 66 checks caught it on the first run; nothing else did. Recorded because
the same shape will reappear in the manuscript's own wording if it is written from memory.

### Status

**theory+empirics now has its theory leg** deliverable-wise: a proved characterization (P1–P6) with an
independent exact verification and a plant battery that fails on four distinct wrong implementations.
What it still owes before submission: the manuscript itself, the related-work comparison in the shape
the journal demands (≥3 with stated differences, ≥100 references all cited, authenticity report), and
the threats section that states P4 against the empirical frame.

**Registration record brought up to date the same round.** The issue's `Outcome` line still read
"P1/P2/P3: not yet run" while all three had measured outcomes and the registered law had been
reframed — a completeness defect that would have met the editor at triage. Fixed by an **append-only**
comment on issue #145 (*Outcome line, updated (R674)*): the registration body was left unedited, all
three priors are marked, the two unmet success criteria are named as unmet rather than absorbed, and
the reframe of the registered law is stated as **retained-but-reframed**. The same content lives in
*Prior outcomes* above; one source, two audiences.

**Next round (R675)** — decide whether the declared level stands. The theory leg exists and is
verified; the empirical leg is two ecosystems with the same measured `0` but **two different
mechanisms** (npm: exactly 1 source commit per statement; PyPI: 0 inputs, publisher identity only).
The question to answer on evidence, not on preference: is a verified proposition plus that taxonomy a
real `theory+empirics` contribution, or is the honest level still `case study` with the law as its
framing? If the latter, downgrade the declaration — the R671 commitment says so, and a level declared
above what the evidence reaches is the one failure mode this journal will not accept.

### R674, addendum — success criterion (ii) met, and an error in this record's own wording

The registered criterion (ii) — *the presence-vs-coverage separation as a ratio with a Wilson
interval* — was recorded as **unmet, outstanding**. It is arithmetic, not data collection, so leaving
it owed was a defect: `wilson_separation.py` now derives every count from the two snapshots and
reports both rates with their own denominators.

| | npm (units 184) | PyPI (units 212) |
|---|---|---|
| presence (attested / frame) | 82/184 = 0.4457, Wilson95 % [0.3757, 0.5179] | 119/212 = 0.5613, [0.4940, 0.6264] |
| **coverage** (covered / with a declared closure) | **0/52 = 0**, [0.0000, **0.0688**] | **0/47 = 0**, [0.0000, **0.0756**] |
| coverage (covered / attested) | 0/82 = 0, [0, 0.0448] | 0/119 = 0, [0, 0.0313] |
| dependencies covered | 0/249 = 0, [0, 0.0152] | 0/564 = 0, [0, 0.0068] |

**The separation is disjoint in both ecosystems** (presence lower bound minus coverage upper bound:
`0.3069` npm, `0.4185` PyPI), so "presence is high and coverage is zero" is not a small-sample
artefact of one frame.

**The interval is also the minimum detectable effect**, and it belongs next to the claim rather than
in a threats section alone: at 52 closure-bearing units, a true per-unit coverage rate below **6.9 %**
would very likely go unseen (7.6 % on PyPI's 47), and at dependency level a rate below **1.5 %**
(0.7 % PyPI) would go unseen over 249 (564) edges. The "0" is therefore an upper bound near 7 % per
unit, not an exact zero — and that is the honest form of the claim.

**The error this addendum corrects.** The round's own record and the issue comment said *"1 OIDC
issuer across all 82 attested releases"*. The histogram sums to **81**, not 82: one attested release,
`@standard-schema/spec@1.1.0`, records **no issuer at all**. The claim's direction is unaffected — a
missing value is not a second platform, and P2's refutation stands (0 positive-coverage units to
cluster) — but the sentence was false as written, and it was false in the shape recorded in
`decision-two-zeros-are-not-one-result.md`: **"field present with an empty value" and "field has one
distinct value" are two facts and cannot share one table cell.** Fixed in the snapshot table (two
rows now), in the P2 outcome, in the R671 recapitulation, and in the R670 caveat; corrected visibly
on issue #145 rather than silently.

`wilson_separation.py`: exit 0, `SEPARATION: DISJOINT IN EVERY ECOSYSTEM`, and it prints `NOT RUN` —
never `0` — for an empty denominator (observed on its first run, when the PyPI reader used the wrong
key and found no rows).

## R675 (2026-10-21) — the third builder: the independence test, and the level decided on it

R674 ended by naming the next round's question: does the declared level `theory+empirics` stand? The
test (T1–T4) was written into `level_criterion.md` **before** the deciding probe, because the level
that the data is allowed to support cannot be chosen from the data.

### Why a probe at all — the objection the unit count cannot answer

Both existing frames are filled by **one builder**: npm records 1 populated issuer `github.com` (81/82),
and all **15** of PyPI's Trusted Publisher identities are `GitHub/<owner>/<repo>/<file>` (119/119
files). They differ in *statement schema*, not in *who builds*. A claim generalising over provenance
**deployments** therefore rested on one deployment rendered two ways. T2 named the axis — the builder —
and the probe went looking for a builder that is not GitHub Actions.

### What was measured (`oci_enumerate.py` → `snapshot_oci.json`, sha256 `4796125…`, 152 s)

Frame: **12 named Chainguard images** (`cgr.dev`), tag `latest`, amd64, every DSSE envelope in the
image's `<sha256-digest>.att` manifest. Naming 12 images is a **selection, not a sample** — see the
caveat below.

| | count |
|---|---|
| images OK / named | **10 / 12** |
| images NOT RUN | **2** — `openjdk`, `postgresql`: *no pull token (repository not anonymously readable)* |
| statements (10 × 3) | **30** |
| provenance statements | **10** — all `https://slsa.dev/provenance/v1` |
| `buildType` | **1** — `https://apko.dev/slsa-build-type@v1` |
| `builder.id` | **1** — `https://github.com/chainguard-dev/terraform-provider-apko` |
| provenance `resolvedDependencies` present | **0 / 10** — the field is **absent**, not `[]` |
| provenance `materials` (v0.2 path) present | **0 / 10** |
| declared package closure (from `apko.dev/image-configuration` → `contents.packages`) | **313** |
| installed closure (distinct `pkg:apk/…` purls in the SPDX statement) | **313** |
| **covered by the provenance statement** | **0 / 313** |
| covered by the **sibling SPDX statement** | **313 / 313** |

Per image, provenance coverage is `0/3`, `0/9`, `0/38`, `0/37`, `0/55`, `0/23`, `0/29`, `0/28`,
`0/64`, `0/27` — ten zeros, ten denominators, no pooling needed to read it.

### The finding this frame adds, which the registries could not

**The information was there and the statement still did not carry it.** apko does not merely know the
package list conceptually: it publishes it twice in the *same signed attestation set* — as
`contents.packages` in the `apko.dev/image-configuration` predicate, and as `pkg:apk/…` purls in the
SPDX document. Its SLSA provenance then omits `resolvedDependencies` **entirely**. So in this frame the
zero is not "nobody recorded the closure"; it is **"the artifact a provenance-reading verifier
traverses does not carry it, while a sibling artifact does"**. That is a sharper and less escapable
version of the paper's thesis than the registry frames could support, and it is the first frame where
the *locus* of the attestation, not its existence, is the variable.

It also instantiates the ceiling law against a live alternative. Per-edge coverage on the SBOM edge is
**1.000** (313/313); the joint over the two edges a verifier must traverse is **0**, exactly as P1/P5
say — and a reader who takes "the closure is attested" at set level concludes the opposite. The
matcher's positive control is that same 313/313: it returns full coverage on one edge and zero on the
other, so the zero is a reading rather than a dead instrument.

### The four conditions, applied — all four hold

- **T1 — empirically discriminating: PASS.** The proposition under test is P1/P5 (the ceiling is the
  joint along the traversal, not a per-edge quantity). The alternative — "the closure is attested,
  therefore covered" — is refuted by measurement, not by argument: 313/313 on the SBOM edge fails to
  make the provenance edge non-zero. Two readings of one attestation set give **0** and **1.000**, and
  the theory is what says which one is the coverage.
- **T2 — independence on the generalisation axis: PASS.** The measured builder is `apko` through
  `terraform-provider-apko`, **not** GitHub Actions, with **10/10** provenance statements carrying it.
  Two builder classes are now measured, and the zero reproduces on the second one.
- **T3 — ground truth not the author's judgement: PASS.** Set arithmetic over registry metadata, with
  a full positive control (`313/313`) and a full negative one (`0/313`).
- **T4 — baseline: PASS.** Presence-vs-coverage on all three frames; set-level-vs-statement-level here
  (the 1.000 vs 0 pair *is* the baseline comparison); four deliberately-wrong implementations in the
  plant battery.

**Verdict: `theory+empirics` stands, on evidence rather than declaration** — and the evidence is
stronger than when the level was declared, because T2 was the condition that was failing by
construction and it is now the one that was repaired fastest.

### The caveats this frame owes, stated now

1. **Twelve named images is a selection, not a sample of the registry.** They are well-known images
   chosen by me, so no frequency may be read off them; what carries is that the *mechanism* is the
   builder's, and 12 named units each show it.
2. **One vendor, one builder.** Chainguard/Wolfi and `apko`. A third builder class (buildx, Cloud
   Build) is still unmeasured; the claim covers "two builder classes", never "all builders".
3. **Two images NOT RUN**, and they are the two most likely to differ (JRE and a database image with
   heavier package sets). Reported, not imputed.

### Two defects this round caught in its own instrument

- **`resolvedDependencies` absent was being read as `[]`.** The first probe printed `n = 0` for a key
  that does not exist. Absent and empty are different claims about a builder, so the artefact now
  stores `None` and the summary counts *present* fields.
- **A matcher reported 5 false misses on `libstdc++`.** purls percent-encode `+` as `%2B`, so an
  undecoded comparison missed the package and made the positive control read `308/313`. Decoding
  raised it to `313/313`. The miss was in the ruler, and the tell was that the *covered* count was
  suspiciously tidy — 5 short, all of one name.

### Status after R675, and what the manuscript now has to do

The three legs the submission bar needs are now all in existence: an instrument (plant battery
17/17, and after this round a full **real** positive control as well as the synthetic ones), three
measured frames across **two builder classes**, and a proved characterization verified exactly. The
declared level survives its own test.

**Consequence for the manuscript, decided here so it is not decided by convenience:** the **OCI frame
becomes the lead example**, not an appendix, because it is the only one where the closure is present in
the attestation set and absent from the statement — i.e. the only frame that separates "the data does
not exist" from "the statement does not carry it". npm and PyPI then become the *schema* contrast
(1 source commit vs 0 inputs + publisher identity) and the OCI frame becomes the *locus* contrast. That
ordering makes the paper's claim about the artifact a verifier reads, rather than about what the world
records — which is the stronger and more defensible of the two.

**Still owed before submission (unchanged in kind, now larger in quantity):** the manuscript, ≥3
related works with stated differences (the SLSA specification, the npm and PyPI attestation
documentation, and at least one academic treatment of build provenance), ≥100 references all cited
with `reference-check.md`, a README with one-command reproduction of all three frames, and a threats
section that states the non-identification proposition, the 12-image selection, and the single-vendor
OCI class.

## R676 (2026-10-21) — the argument fixed before the bibliography, and the numbers made checkable

R675 closed with the level decided and the ordering chosen (OCI lead, registries as the schema
contrast, law as the frame). This round did the one thing that has to happen before a single reference
is collected: **write down what the manuscript asserts, in the order it asserts it, with every printed
number bound to a key in a committed artifact.** Collecting the bibliography first would shape the
citation set around whatever got read rather than around the claim.

### `manuscript_skeleton.md` — the argument, not the prose

Title, a drafted abstract (the place where a paper's claim is either fixed or left vague), an
eleven-section plan with the role each section carries, the claim→artifact table, the Wilson table, the
pre-submission checklist, and a *deliberate omissions* list. Three decisions inside it are worth naming
because they were open until now:

1. **The OCI frame leads.** It appears third in measurement order and first in argument order, because
   it is the only frame that separates "the data does not exist" from "the statement does not carry it".
   The abstract says so in its second paragraph rather than saving it for §7.
2. **The specification's `if known` hedge is met in §11, head-on.** It is the strongest counter-argument
   to the whole paper (a hedge cannot be violated), so it cannot live in a footnote.
3. **No security claim anywhere.** The study did not run an attack; the claim is about what a verifier
   can *see*, and the abstract's claim boundary states that a covered dependency is not thereby benign.

### `check_claims.py` — the table is checked, or it is a note

The journal's own history says derived text drifts while the numbers it quotes stay correct, so the table
had to be verified in both directions: read each row out of the markdown, resolve the named key in the
named artifact, compare. **28 rows check, 3 are printed NOT CHECKED** (the Wilson, law and plant totals —
they are script output, not stored keys) and are never silently counted as passing.
`claim table: 31 data rows, all parsed`, `VERDICT: PASS`.

**Three defects, all in the guard rather than in the table**, each found by making the guard run:

- **Ambiguous keys.** Rows wrote `summary.attested_with_deps / attested_zero_coverage` — the second path
  unqualified, so it resolved against nothing. Fixed by fully qualifying every path: a cell that holds
  half a key is the same defect as a cell that holds two facts.
- **A three-way value with a two-way key.** `summary.build_types` printing `1 entry, 82` bound neither
  the cardinality nor the histogram. Split into two rows, one key each, so both are now checked.
- **The cardinality guard could not fail.** It counted table rows with *the same pattern it parsed
  with*, so a row with an unparseable id was invisible to both. Replaced by a **region-based** check: a
  line inside the claim table IS a claim row, so anything there that does not parse is a failure. The
  first version of this round's guard printed `VERDICT: PASS` while silently dropping four rows I had
  just added — the exact failure mode this journal's memory records as "silence is not a pass".

Demonstrated red on three plants (a wrong value, a wrong key name, a malformed row), each turning
`VERDICT: PASS` into `FAIL`. A guard that has not been shown to fail on its own defect class does not
exist.

### What this round did not do

No issue comment. The R672 rule for posting is that the addressee's belief must change, and this round's
output is a plan plus an instrument for future numbers — it changes nothing an editor, a policy author or
a specification author would decide today. It goes in the record when the manuscript's claims are
actually made.

## R677 (2026-10-21) — the reference corpus built backwards, and three holes in the builder

The submission bar needs **≥100 references, every one verified against a real external record**
(`reference-check.md`). A reference is exactly the artifact a language model can produce without
looking, so the corpus is assembled the other way round: a candidate is a *query*, and what enters is
what a registry returned for it. `build_references.py` → `references.json` → `reference-check-draft.md`.

### Result of the first batch — reported with its failure rate, not just its survivors

| | count |
|---|---|
| candidates asserted | **33** |
| **verified** (DOI/arXiv record resolved and corroborated) | **12** |
| **refused by the registry** | **21** |
| NOT RUN (a registry could not be asked) | **0** at the final state |
| fabricated plant | **REFUSED** |

**21 of 33 assertions did not survive contact with a registry.** That number is the point: it is the
measured rate at which recalled bibliographic detail fails, and every one of the 21 was a title I
would have written with confidence (in-toto, sigstore, TUF, the npm-ecosystem study, "Spinning Tops"
style work, three SBOM papers). None of them was fabricated on purpose — they are what recall produces.

### Three holes found in the builder, all by reading its output rather than by a gate

1. **A review entered the corpus as the work it reviewed.** `10.1136/jech.4.3.170` is a *review of*
   Good's *Probability and the Weighing of Evidence*, by **Stein**. My acceptance rule was
   `author OR year`, the title matched at 1.000, and the year 1950 agreed — so the entry was admitted
   with `first_author = Stein` under the key `good1950probability`. **A year is a weak identifier**:
   thousands of works share one. The rule is now: **an asserted author must match, and a mismatch is
   fatal**; a year difference is tolerated only as an edition note. The entry is now refused.
2. **`--check` compared the record to itself.** The re-verification pass read the stored
   `first_author`/`year` and checked the DOI against them — two sides of the same field, which can
   never disagree. The corpus now stores the **assertion** (`asserted: {title, first_author, year}`)
   and the check compares the registry to that. This is the same shape as the round-6 defect (a
   counter sharing its parser's pattern) and as the round-2 lesson (a second criterion must be
   independent of the first).
3. **A rate limit was being recorded as "no such work".** A Crossref 429 on `cheney2009provenance`
   put it in the same bucket as the 21 refusals. Transport failures are now tagged `NOT_RUN:` and
   counted separately; and because a *definitive* refusal at one registry must not be undone by a
   transport failure at the other, the classifier says NOT RUN only when **no** registry answered.

### The instrument's honest limits, stated now

- **12 of 100+.** The bar is not met and `reference-check-draft.md` says so in its first line.
- **arXiv was not consulted in the final pass** (`--no-arxiv`, recorded per refusal), because the
  arXiv API throttles and a full Crossref+arXiv pass over 33 candidates exceeded the round's budget.
  `--budget` exists so the run turns into honest NOT RUN rows instead of being killed and losing the
  corpus; it is set generously in later rounds.
- **Discovery mode exists and is not the same as acceptance.** `--discover "<query>"` returns real
  records for a topic, and its precision on a provenance query was poor — two preprints, an SSRN
  paper and a book chapter in the top six. Discovery supplies *candidates with real DOIs*; relevance
  is still a judgement the paper has to make, and verification is still the instrument's.

### What this changes about the plan

The manuscript's §10 lines were written before the corpus, which is why a third of them survive as
citations and two thirds do not. The next pass grows the corpus by **discovery + vetting** rather than
by more recall, and the 21 refusals are kept in the record: they are evidence about how recall fails,
and deleting them would hide that.

## Round log — corpus grown from registry returns, reviewed, and re-verified (2026-10-22)

**Goal of the round**: close the "12 of 100+" gap that `reference-check-draft.md` had been stating in
its first line, without letting the count be met by padding.

**What was built.** `build_references.py` grew three modes: `--harvest` (grow the corpus from what
Crossref returns for a topic query), `--report` (write the reference-check report *from* the corpus, so
the report is derived and cannot go stale the way #128's built manuscript did), and a bucketed
`--check`. `review_references.py` holds the human pass: every title read, every refusal recorded with
a reason, refusals kept in the file as `excluded` rather than deleted.

**The number.** 210 records considered → **147 kept** (12 verified assertions + 135 harvested
records), **63 excluded with a stated reason**. All 147 re-verified by `--check` against Crossref:
**0 stale, 0 NOT RUN**. The count clears the ≥100 bar; whether it is *satisfied* now depends on the
manuscript citing each one, which is the next round's work.

**Three things the gate had to learn, each the hard way.**

1. **One broad term admits the wrong field.** The first `slsa` query returned logistics papers
   ("Selecting Supply Chain Software", "Supply Chain Evolution") — supply chains of trucks. The gate
   is now two groups: a group-A topic term **and** a group-B field term.
2. **Discovery precision is a record-level problem, not only a topic-level one.** Crossref returns
   figure captions ("Fig. 2. Dependency graph of experimental results"), conference front matter
   ("… - Cover", "… - TOC"), and book reviews. Those are `component` / `proceedings` / `peer-review`
   types: a scholarly-type allowlist removes them mechanically (29 records in one pass).
3. **Same word, different field cannot be filtered by any term list.** `pyPI` is the *Tropical
   Cyclone Potential Intensity* package; "Vulnerability and the Moral Nature of Dependency Relations"
   is philosophy; `OSV` is *OSPF* vulnerability checking; "attestation" appears in art history and in
   Pasteur's quadrant. No regex separates those, so the corpus has two states — mechanical and
   reviewed — and the exclusions are written down with reasons (63 of them, in `references.json`).

**A defect the round found in its own instruments.**

- `--check` counted a 429 or a timeout as STALE. A failure to *ask* is not a finding about the
  reference, so it is now bucketed NOT_RUN and the verdict distinguishes them (exit 2 vs exit 1).
- `--check` then caught a record the read-through had kept: a Palgrave dictionary entry with **no
  author and no year**, which the two-criterion rule cannot corroborate at all. Title overlap 1.000
  and nothing else — the exact shape the second criterion exists to refuse. It is now excluded as
  unverifiable.
- `norm_tokens` decomposed accents before stripping them, turning `Fréchet` into `fre chet`; a query
  for the Fréchet bounds returned **zero** kept records and looked like an empty literature.
- The human-pass list itself was wrong: keys transcribed from a 30-character-truncated listing meant
  **28 named refusals silently matched nothing** and the "reviewed" corpus still held work the review
  had refused. The pass now resolves keys by exact match then *unique* prefix, refuses to guess on an
  ambiguous prefix, and allows an explicit `prefix*` for "every entry under this heading".

**What this does not do.** It does not make the corpus citable. A harvested entry is evidence that a
record exists on a topic; whether it says what the paper needs is settled in the text. And the 135
harvested entries are a *derived* set — `--rebuild-harvest` regenerates them from the query table, so
the corpus is reproducible rather than accreted.
