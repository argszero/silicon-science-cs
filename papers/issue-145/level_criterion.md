# The contribution-level criterion — fixed before the deciding probe (R675, 2026-10-21)

The registration declares **`theory+empirics`**. R671 committed to *downgrade honestly* if the evidence
does not reach it. A level chosen after seeing the data is not a declaration, it is a fit, so the test
is written here **first**, in the form it will be applied, and is not edited afterwards.

## Why this needs a test at all

Two facts about the current evidence pull in opposite directions:

- **In favour.** The measurement covers **two ecosystems** (396 units: 184 npm + 212 PyPI), each with
  an exact instrument (set arithmetic over registry metadata, plant battery 17/17), and the theory leg
  is **proved and exactly verified** (6 propositions, 66/66 in `Fraction` arithmetic).
- **Against.** The two ecosystems are **not independent on the builder axis**: every attested unit in
  both frames was produced by **GitHub Actions** — npm records 1 populated issuer `github.com` (81/82),
  and PyPI's 15 distinct Trusted Publisher identities are **all** of the form `GitHub/<owner>/<repo>/<file>`
  (119/119 files). They differ in *statement schema and identity model*, not in *who builds*.

The general claim at stake — "published build provenance does not attest the dependency closure" —
generalises over **provenance deployments**, and a deployment is characterised by its builder. If both
frames share one builder, the claim is scoped to one builder class however many ecosystems it is
measured in. That is the objection the level rests on, so the level is decided by a test of the axes,
not by unit count.

## The four conditions (fixed)

`theory+empirics` stands **iff all four hold**. Any failure means the honest declaration is
**`case study`**, with the abstract scoped accordingly.

- **T1 — the theory must be empirically discriminating.** It must make at least one prediction the
  measurement **could have refuted**, and the measurement must have tested that prediction. A
  characterization that only constrains how the data are *interpreted* is proved, not validated, and a
  proof is not an empirical result. (Applied to: does any proposition predict an observation that could
  have come out otherwise in the measured frame?)
- **T2 — the populations must be independent on the axis the claim generalises over.** ≥2 populations,
  independent in the dimension the generalisation runs along, which here is the **builder**, not the
  registry. Two registries filled by one builder count once.
- **T3 — the measurement's ground truth must not be the author's judgement.** Computable set arithmetic
  over registry metadata satisfies this; human annotation would need inter-rater agreement.
- **T4 — a baseline comparison must exist** (bar #6), or an argued reason the setup is not comparable.

## What would move T2 to a pass

A third population whose **builder is not GitHub Actions** and whose statements *do* carry a
dependency list — the two properties are one probe, because a builder that emits closure-bearing
statements is exactly what falsifier 2 of R671 named. Outcomes:

- **positive closure coverage in a non-GitHub builder** → T2 passes, and falsifier 2 fires: the general
  claim narrows to "CI builders of source packages", which is a *stronger* paper than the current one.
- **no such population found** → the frame stays one builder class, T2 fails, level becomes `case study`.
- **probe unreachable** → `NOT RUN`; no level change is licensed by a failure to look, and the level
  decision is deferred rather than settled by silence.

Recorded here before the probe ran: the expectation is that container-image provenance produced by
`apko`/`melange`-style builders **does** name installed packages, because those builders materialise a
root filesystem from an explicit package list. If that expectation is right, T2 passes on evidence.

---

# Verdict, recorded after the probe (R675) — the criteria above are unedited

The probe was the OCI frame described in `heilmeier.md` §R675: 10 of 12 named Chainguard images,
30 statements, builder `apko`/`terraform-provider-apko`, **0/10** provenance statements carrying any
dependency, **313/313** packages carried by the sibling SPDX statement.

| condition | verdict | evidence |
|---|---|---|
| **T1** empirically discriminating | **PASS** | P1/P5 tested against the live alternative "attested ⇒ covered": per-edge 313/313 fails to move the joint off **0**. Two readings of one attestation set give 0 and 1.000. |
| **T2** independent on the builder axis | **PASS** | `buildType` `apko.dev/slsa-build-type@v1`, `builder.id` `terraform-provider-apko`, 10/10 — **not** GitHub Actions. Two builder classes measured. |
| **T3** ground truth not the author's judgement | **PASS** | set arithmetic; positive control 313/313, negative control 0/313. |
| **T4** baseline | **PASS** | presence-vs-coverage on 3 frames; set-level vs statement-level; 4 wrong implementations in the plant battery. |

**Level: `theory+empirics` stands.** The declaration made at registration was not edited to fit; the
condition that was failing (T2) was repaired by measurement, and T1 passed on a test that the data
could have failed — 10 provenance statements could have named one package each and none did.

**What this does NOT license** (fixed here, before the manuscript is written):
- no frequency claim from 12 named images — they are a selection;
- no claim about builders in general — **two** builder classes, one vendor (Chainguard/Wolfi);
- no claim that the closure is unattested — in the OCI frame it **is** attested, at set level; the
  claim is about the artifact a verifier traverses.
