# Related Work — Issue #18: Integrity Posture of Popular Open-Source Repositories

Five concrete related works are compared; each entry states what the prior work does,
its limitation, and the specific difference of this paper.

## 1. Analysis of Commit Signing on Github (arXiv 2604.14014, Apr 2026)

- **What**: a global census of 2,737,649 GitHub accounts, 71,694 active contributors,
  and 16,112,439 commits across 874,198 repositories, characterizing commit-signing
  and key-management practices across GitHub's history. Finds most signed activity is
  generated automatically by GitHub's web interface, genuine end-to-end signing is
  exceptionally rare, and adopters practice it erratically (abandonment, unrevoked
  expired keys).
- **Limitation**: a global long-tail census — the popular tier that consumers actually
  depend on is diluted; measures signing *presence* (signed vs not), not verification
  *outcomes*; no release layer.
- **Our difference**: we measure the popular-repository tier (41 most-starred repos)
  with GitHub's verification *verdicts* (valid / unsigned / failure reason), add the
  release-artifact signing layer, and test the coherence between the two.

## 2. On the Prevalence and Usage of Commit Signing on GitHub (ACM, DOI 10.1145/3756681.3756959, Jun 2025)

- **What**: studies commit signing as GitHub's defense against commit spoofing,
  measuring prevalence and usage patterns of signing keys.
- **Limitation**: commit layer only; prevalence framing rather than repository-level
  posture; no release-artifact measurement.
- **Our difference**: same layer but outcome-decomposed and repository-scoped; adds
  release signing and the 2×2 coherence analysis.

## 3. Claimed or Attested? A Commit-Signature Dataset and Identity Trust Tiers across the World of Code (arXiv 2607.06194, Jul 2026)

- **What**: releases the first commit-signature axis for the World of Code V2604
  collection: 17.59% of 5,866,595,698 commits carry a signature (PGP 98.96%, growing
  SSH/X.509), with a key-to-author graph gating org/CI keys from person keys — an
  identity-trust dataset.
- **Limitation**: a dataset/identity-trust contribution at global scale; signature
  *presence* over the whole corpus, not per-repository verification posture; no
  release layer.
- **Our difference**: per-repository two-layer posture on a small popular corpus;
  verification verdicts (not just presence); release-asset signature taxonomy.

## 4. Open-Source Commit Signing (OSF Preprints, Jan 2025)

- **What**: replication package for commit-signing research in open-source projects.
- **Limitation**: replication artifact; commit-layer focus; no popular-tier or
  release-layer measurement.
- **Our difference**: extends the measurement surface to release assets and
  repository-level coherence, with a committed offline snapshot for byte-identical
  reproduction.

## 5. sigstore / SLSA / cosign (industry frameworks, 2021–2026)

- **What**: the ecosystem of artifact-signing frameworks and supply-chain security
  levels (sigstore.dev, slsa.dev, cosign, `gpg`, `minisign`) that promote signing
  release artifacts and build provenance.
- **Limitation**: as of 2026-08 there is no systematic academic measurement of
  adoption (OpenAlex title search for "sigstore adoption" returns 0 works); guidance
  is prescriptive, not descriptive.
- **Our difference**: the first systematic measurement of how widely artifact signing
  is actually adopted in the popular tier — 9.8% of repositories ship any signed
  release, all via GPG `.asc`, with zero cosign/minisig/sigstore artifacts observed.
