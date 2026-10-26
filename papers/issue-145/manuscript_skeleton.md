# Manuscript skeleton — issue #145 (drafted R676, 2026-10-21)

**Status: plan, not prose.** This file fixes the argument's order and binds every number the
manuscript will print to a key in a committed artifact. It is drafted **before** the reference corpus,
because the claim structure decides which literatures must be cited — the reverse order produces a
bibliography shaped around whatever happened to get read.

---

## Title

*Attested Is Not Covered: What Published Build Provenance Names, and the Detection Ceiling a
Compromised Input Faces*

## Abstract (draft — this is where the argument is fixed)

Build provenance is now published at scale: npm and PyPI attach signed attestations to package
releases, and container registries attach them to images. The natural reading is that a verifier who
follows such an attestation can learn what went into the artifact. We measure whether that reading
holds, on three frames and two builder classes, and find it does not: **the artifact a provenance
verifier traverses does not carry the dependency closure**, in three deployments that differ in
mechanism and agree in outcome.

On npm (20 stated seeds, 184 packages at depth 1) **82** releases are attested and **52** declare a
non-empty closure; **52 of 52** name **none** of it — **0 of 249** declared dependencies — because
every statement names exactly **one** input, always a source-repository URI. On PyPI (20 stated seeds,
212 files) **119** files are attested across **15** Trusted Publisher identities; **none** carries a
predicate with any input at all, so the closure is not merely uncovered but unmentioned: **0 of 564**
declared dependencies. On container images (10 of 12 named Chainguard images, builder `apko`, not
GitHub Actions) the same **0/313** appears where the closure **is** attested in the same signed set —
a sibling SPDX statement covers **313/313** — so the failure is not missing data but a statement that
does not carry the data its own attestation set holds.

We then prove what such a measurement can and cannot support. Treating the closure as a path, the
detection ceiling is the **joint** probability `P(A₁ ∩ … ∩ A_k)`, not a per-edge rate. The coverage
vector does **not** identify it: with fixed marginals the ceiling ranges over a Fréchet interval
`[max(0, Σcᵢ − (k−1)), min cᵢ]`, both endpoints attained, differing by `2^(k−1)` at `cᵢ = 1/2` — so a
non-zero ceiling claim owes a correlation structure that a coverage measurement cannot see. The
converse is what makes the empirical result stand: **one `cᵢ = 0` forces the ceiling to 0 under every
joint law**, so the measured zero does not rest on an untestable independence assumption.

*Claim boundary*: we make no claim about the security of any package, image or publisher, and none
about a real attack; a covered dependency is not thereby benign. The 12 images are a **selection**,
not a sample of any registry, and no frequency is read from them. Two measured builder classes, one
vendor in the container class.

## Section plan (with the role each section carries)

### §1 Problem — one sentence, then the reading that fails
The claim under test: *presence of provenance ≠ coverage of the input closure*. Name the addressee
explicitly (§2) and state that the paper measures an artifact, not the world.

### §2 What each layer actually promises (quoted, not paraphrased)
The three-layer read from R672, which is the paper's answer to "whom does this contradict": the
**definition layer** (SLSA v1.0: `resolvedDependencies` captures fetched dependencies "if known"), the
**vendor layer** (npm's docs disclaim security inference and describe provenance as a verifiable link
to source code; PyPI pages provenance under package origin), and the **filling layer** (what deployments
actually emit). The disagreement is between layer 1 and layer 3 — *not* between vendors and their users.
This section is load-bearing for §9's significance and must not degenerate into a claims-versus-reality
story the sources do not support.

### §3 The construct, and why the naive reading is wrong
Closure as a path; coverage `cᵢ` per edge; the ceiling as a **joint**. Introduce the two-level trap
with the OCI frame's own numbers (**1.000** on one edge, **0** on the other) as the motivating example.
Definitional content: what counts as "covered" (set arithmetic on purls/digests, not string similarity).

### §4 Instrument and its failure modes
The enumerators, the snapshot discipline (sha256 per frame, NOT RUN never 0), and the plant battery
(**9 plants, 4 deliberately wrong variants, 17/17**) including the one that was caught only after a
mutation survived. State the rule that makes the zeros readings rather than dead instruments: every
zero is accompanied by a **real** positive control where one exists (OCI: 313/313 on the sibling edge).

### §5 npm — the schema that names the source and not the closure
184 units, 82 attested, 52 with a closure, 52/52 at 0, 0/249 deps. One `buildType`, one populated
issuer (81/82; one release records none — a *missing* value is not a second platform). Input-URI
families `git: 82` with an **empty `other` bucket**, which is what makes the zero structural rather
than a parser gap.

### §6 PyPI — a different mechanism, the same outcome
212 files, 119 attested, 0 with a predicate, **0 inputs total**, 15 Trusted Publisher identities,
47 with a closure all at 0, 0/564 deps. The taxonomy point: npm attests *a source commit*, PyPI attests
*publisher identity*. Two mechanisms, one number — so the result is a classification, not a count.

### §7 Container images — where the closure is attested and the statement still omits it
**This is the lead example in the final ordering even though it appears third in measurement order**;
the manuscript should foreground it in §1 and the abstract because it is the only frame separating
"the data does not exist" from "the statement does not carry it". 12 named images, 10 OK / 2 NOT RUN,
builder `apko` via `terraform-provider-apko`, `resolvedDependencies` **absent** in 10/10 (absent, not
empty), 313 declared packages, 0/313 on the provenance edge, 313/313 on the sibling SPDX edge.

### §8 The ceiling law (six propositions)
P1 definition; P2 Fréchet upper bound, attained under comonotonicity; P3 product under independence;
P4 non-identification via the Fréchet interval; P5 the first zero dominates; P6 which object is
actionable. Exact verification (**66/66** checks in `Fraction` arithmetic) and the defect the check
caught in its own author's code (a prefix/suffix builder bug reporting ceiling 1 for an all-zero path).

### §9 Significance — whose belief or decision changes
Three decisions, named: (i) a policy that reads "has provenance" as "attests its inputs" is reading a
different object than it thinks; (ii) a closure-verifier that traverses provenance alone **cannot see**
a compromised input no matter how deep it walks, and should say so or traverse the sibling artifact;
(iii) a specification that says `resolvedDependencies` captures dependencies "if known" states a goal
its own deployed builders do not fill — the deployment gap is the measurable thing.

### §10 Related work (with stated differences)
Required: ≥3 with an actual difference each, plus ≥100 references all cited. Candidate lines named
here so the corpus is built to fit, not fitted afterwards: (a) build provenance & SLSA/in-toto
specifications and their measurement literature; (b) software supply-chain security — reproducible
builds, dependency confusion/typosquatting, SBOM completeness; (c) attestation/transparency-log
studies (Sigstore, Rekor) and their coverage limits; (d) the general problem of **instrument validity**
— a measurement that answers a different question than the one it is read as answering (this is where
the paper's methodological claim joins a real literature instead of standing alone); (e) detection and
audit theory sufficient to support the "ceiling" framing.

### §11 Threats to validity — and why the result still stands
The Fréchet non-identification (P4) against the empirical frame; the 12-image **selection**; one vendor
in the container class; two builder classes, never "all builders"; the `if known` hedge in the
specification, which is the strongest counter-argument and must be met head-on rather than footnoted;
the Wilson upper bounds that make each 0 an "at most" claim (§ see table).

---

## Claim → artifact table

Every number the manuscript prints resolves to one of these. A number with no row here does not go in.

| # | claim as printed | artifact | key | value |
|---|---|---|---|---|
| 1 | npm frame size | `snapshot_npm_d1_pilot.json` (sha256 `d3bde499…`) | `summary.units` | 184 |
| 2 | npm attested | same | `summary.attested` | 82 |
| 3 | npm attested with a non-empty closure | same | `summary.attested_with_deps` | 52 |
| 4 | npm at zero coverage | same | `summary.attested_zero_coverage` | 52 |
| 5 | npm positive coverage | same | `summary.attested_positive_coverage` | 0 |
| 6 | npm declared deps / covered | same | `summary.deps_total` / `summary.deps_covered_total` | 249 / 0 |
| 7 | npm NOT RUN | same | `summary.not_run` | 0 |
| 8 | npm undecodable payloads | same | `summary.undecodable_payloads` | 0 |
| 9 | npm input families | same | `summary.input_families` | `{git: 82}` |
| 10 | npm distinct build types | same | `summary.build_types (len)` | 1 |
| 10b | npm releases per build type | same | `summary.build_types` | {https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1: 82} |
| 11 | npm populated issuers | same | `summary.oidc_issuers` | `{github.com: 81}` |
| 12 | PyPI frame size (files) | `snapshot_pypi.json` (sha256 `9a285cc2…`) | `summary.files` | 212 |
| 13 | PyPI attested files | same | `summary.attested_files` | 119 |
| 14 | PyPI files NOT RUN | same | `summary.files_not_run` | 0 |
| 15 | PyPI with a predicate | same | `summary.attested_with_predicate` | 0 |
| 16 | PyPI statement inputs | same | `summary.attested_inputs_total` | 0 |
| 17 | PyPI Trusted Publisher identities | same | `summary.publishers` (len) | 15 |
| 18 | PyPI attested with closure / at zero | same | `summary.attested_with_deps` / `summary.attested_zero_coverage` | 47 / 47 |
| 19 | PyPI deps / covered | same | `summary.deps_total` / `summary.deps_covered` | 564 / 0 |
| 20 | OCI images named / OK / NOT RUN | `snapshot_oci.json` (sha256 `4796125…`) | `summary.images` / `summary.images_ok` / `summary.images_not_run` | 12 / 10 / 2 |
| 21 | OCI statements / provenance statements | same | `summary.statements` / `summary.provenance_statements` | 30 / 10 |
| 22 | provenance with positive `resolvedDependencies` | same | `summary.provenance_with_positive_resolvedDependencies` | 0 |
| 23 | OCI distinct build type / builder id | same | `summary.build_types (len)` / `summary.builder_ids (len)` | 1 / 1 |
| 23b | OCI build type actually recorded | same | `summary.build_types` | [https://apko.dev/slsa-build-type@v1] |
| 23c | OCI builder actually recorded | same | `summary.builder_ids` | [https://github.com/chainguard-dev/terraform-provider-apko] |
| 24 | declared / installed package closure | same | `rows[].closure.declared_n (sum over OK)` / `rows[].closure.installed_n (sum over OK)` | 313 / 313 |
| 25 | covered by provenance / by sibling SPDX | same | `rows[].closure.declared_covered_by_provenance (sum over OK)` / `rows[].closure.declared_covered_by_spdx (sum over OK)` | 0 / 313 |
| 26 | presence & coverage with Wilson 95 % | `wilson_separation.py` (stdout, exit 0) | printed lines | see §Wilson |
| 27 | law verified | `ceiling_check.py` (exit 0) | printed total | 66/66 |
| 28 | plant battery | `plant_coverage.py` | printed total | 17/17 |

**Values above were re-read from the artifacts this round** (not from notes). Two key names are easy to
get wrong and are recorded here as a guard: npm's dependency count is **`deps_covered_total`** (not
`deps_covered`), and PyPI's publisher count lives in **`summary.publishers` as a list** (bind it as
`len`, not as a scalar key).

### Wilson table (values printed by `wilson_separation.py`, exit 0)

| | npm (n = 184) | PyPI (n = 212) |
|---|---|---|
| presence | 82/184 = 0.4457, [0.3757, 0.5179] | 119/212 = 0.5613, [0.4940, 0.6264] |
| coverage \| closure | 0/52 = 0, [0, **0.0688**] | 0/47 = 0, [0, **0.0756**] |
| coverage \| attested | 0/82 = 0, [0, 0.0448] | 0/119 = 0, [0, 0.0313] |
| dependencies covered | 0/249 = 0, [0, 0.0152] | 0/564 = 0, [0, 0.0068] |

These upper bounds are the study's **minimum detectable effect** and belong beside the claim, not only
in §11: a per-unit rate below 6.9 % (7.6 % PyPI) and a per-dependency rate below 1.5 % (0.7 %) would
very likely go unseen. The measured 0 is therefore "at most about 7 % per unit", which is the honest
form.

---

## What must exist before this can be submitted

1. **Manuscript prose** — §1–§11 above, in `papers/issue-145/manuscript.md`.
2. **≥100 references, all cited**, with `reference-check.md` giving one line per entry: key → method
   (Crossref DOI / Crossref title / arXiv id) → result → the real record found. No entry ships
   unverified; an unverifiable entry is deleted rather than kept.
3. **`reproduce.sh`** reproducing all three frames plus the law, with expected output/tolerance. The
   two OCI NOT RUN images are recorded as NOT RUN in it, never silently skipped.
4. **README** — one command, expected verdict lines, environment, and the wall clock each frame needs
   (npm 77 s, PyPI 240 s, OCI 152 s as measured).
5. **Contribution level: `theory+empirics`**, already decided on a criterion fixed before the deciding
   probe (`level_criterion.md`, T1–T4 all pass).
6. **Prior-belief reporting** — the three registered priors with their outcomes (P1 confirmed, P2
   refuted with a direction, P3 confirmed and stronger), each against what the study could detect.

## Deliberate omissions (and why)

- **No security claim.** Not "malicious packages get through" — we did not run an attack. The claim is
  about what a verifier can *see*.
- **No registry-wide frequency.** Every frame is a stated seed set; none is a census, and the paper
  says so in the abstract rather than only in §11.
- **No third builder class** in this submission. Two builder classes are measured; naming a third as
  future work is honest, and claiming generality over builders would not be.
