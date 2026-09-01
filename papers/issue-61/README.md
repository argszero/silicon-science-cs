# Issue #61 — Post-Quantum in the Wild: source-level PQC migration census

Reproduce the core results (hypotheses report + validation) with one command:

```bash
bash reproduce.sh
```

Expected output (exit 0):
- `OK: hypotheses_report.txt regenerated`
- `PASS: 9/9 checks` (independent re-computation of H1/H2/H3 from committed snapshots)
- `== reproduction complete ==`

No network required — everything reads from committed snapshots
(`snapshots/`, including `tier_ab_corpus.json` with head_sha pins, dep evidence,
content-probe evidence, classifier labels, and the gold-standard annotation).

## Core results (Tier B, n=199 top open-source projects, snapshot 2026-09-01)

| Hypothesis | Point estimate | Wilson 95% CI | Verdict |
|---|---|---|---|
| H1: direct PQC implementation/usage is rare (<10%) | **2.0%** (4/199) | [0.8%, 5.1%] | ✅ CONFIRMED (16 flips to 10%) |
| H2: PQC arrives via dependency upgrades | **91.1%** (41/45) | [79.3%, 96.5%] | ✅ CONFIRMED (10.2×; 37 flips) |
| H3: adoption is ecosystem-stratified | anchors **90.0%** vs Tier B **2.0%** | — (Fisher p≈0) | ✅ CONFIRMED |

**Level distribution**: L0 NONE 154 (77.4%) / L1 CAPABLE 41 (20.6%) / L2 DIRECT 4 (2.0%)
/ L3 ACTIVE 0. The four direct implementers: torvalds/linux (kernel ML-DSA
`crypto/mldsa.c`), Ladybird (LibCrypto/PK), Deno (ext/crypto), Bun (webcrypto).

**Baseline gap**: UK HTTPS endpoints with a PQC group = 44.0% (network, 2026-08) vs
source-level direct implementation = 2.0% → observable-deployment ≠ implementation.

## Committed artifacts

- `manuscript.md` — full paper (theory+empirics)
- `hypotheses.py` — H1/H2/H3 + Wilson CIs + flip sensitivity → `snapshots/hypotheses_report.txt`
- `validate.py` — independent cross-check of report numbers (9 checks)
- `trace_check.py` — manuscript-claim traceability (0 gaps)
- `classifier_v1.py` / `content_probe.py` / `extract_manifests.py` — signal pipeline
- `snapshots/` — corpus (head_sha-pinned), dep evidence, content-probe evidence,
  classifier labels, gold standard `annotation/ground_truth_r114.tsv`

## Data provenance

Corpus built from a GitHub snapshot 2026-09-01: 219 repos (Tier B 200 six-language
top-starred + Tier A 20 crypto anchors), all pinned by `head_sha`. Full corpus
artifacts (trees, 4149 manifest fetches, content probes) live in the git-ignored
`research/` workspace; committed snapshots are the analysis layer. Classifier v1
validated 8/8 on the human-annotated gold standard; L0 negative controls clean.
