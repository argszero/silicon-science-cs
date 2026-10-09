# Reference check -- issue #132

**What this file is.** The verification report for the manuscript's reference layer of issue #132
(*The Frame Is a Level*). Every entry in the pool was discovered by `refscan132.py` -- nothing is
typed from memory -- and each was checked against a **live external record** by comparing the
returned **title** with the stored title.

**Result: 257 / 257 VERIFIED, 0 title mismatch, 0 transport-unknown.** The full per-entry table is in
`reference-pool.md`; the machine-readable summary is `citation-verification.json`. The pool has 257
entries (241 arXiv, 16 Crossref), well above the journal's 100-reference floor. The **cited subset**
is pinned when the manuscript is composed, from this same pool and the same check; the numbers above
are the state of the layer at commit time.

## Method

| Source | Use | Endpoint |
|---|---|---|
| arXiv API | discovery | `search_query=<topic>`, 20 queries derived from this paper's own subject |
| arXiv API | verification | `id_list=<ids>` in batches, `max_results` set to the batch size |
| Crossref | canonical works, found **BY TITLE** | `query.bibliographic=<title>` |
| Crossref | verification | `works/<doi>` |

**Why a title match and not the HTTP status.** A DOI or an arXiv id written from memory *resolves*:
the endpoint returns 200 with a **real** record -- of a **different** paper. So the check is the
returned title against the stored title, scored as the **smaller** of the two coverage fractions
(a one-sided score lets a short generic title reach 1.00 against a long specific one, i.e. a metric
that can never fail on the object it is built to catch). Threshold **0.80**. Every canonical work is
found **by title**, never by a remembered identifier.

**Transport failures are not findings.** An API outage yields `TRANSPORT-UNKNOWN`, never "these
records do not exist", and fails the run. This mattered live: the first verification pass reported
`TRANSPORT-UNKNOWN 20` and `50`, which was an **outage and a rate limit**, not evidence about the
records -- reported as such, then re-run. The final pass is `0`.

## Defects found and repaired while building this layer

1. **An old-style arXiv id loses its archive prefix.** Two of the pool's ids are pre-2007 (`cs/0609060`),
   and the naive normalisation `rsplit("/", 1)[-1]` stripped the archive, leaving `0609060`, which the
   `id_list` endpoint **rejects with HTTP 400**. The batch that held them failed while every other
   batch resolved -- so the failure looked like a partial outage. Repaired by normalising everything
   after `/abs/` and stripping only the version suffix (certificate: `id-keeps-old-style-prefix`).
   **A key that cannot round-trip is not an identifier.**
2. **A version is not an identity.** The stored `id` field carried the version (`0909.4385v1`) while
   the key was versionless. Normalised so key = id: a paper's identity does not change with its
   revision.
3. **Burst rate-limiting.** arXiv returns HTTP 429 on tightly spaced batches; the batcher now spaces
   requests, and a 429 is still reported as transport, never as a mismatch.

## What this check does **not** establish

- It is a **harvest regression check on identity**, not independent identity evidence: the stored
  title and the live title are read from the same backend field, so a perfect score is expected when
  the harvest is intact. It rules out a *wrong* record, not a systematically mislabelled one.
- It says nothing about **relevance** (the curation filter does that) nor about **citation** (the
  manuscript does that). An entry in the pool is not yet a reference.
- The 0.80 threshold is a design choice with a sensitivity: `--selftest` plants a generic-short
  title, a bare substring and a different paper, and requires all three to be **rejected**, and an
  identical title, a subtitle-extended title and a split `title`+`subtitle` Crossref record to be
  **accepted**.

## Reproducing the layer's offline half

`refscan132.py --gate` runs inside `reproduce.sh` (no network): it asserts the pool carries at least
100 entries, that every entry has an id / source / title / year, that there are no duplicate titles,
that every key is its own id, that no old-style id lost its archive prefix, and that
`reference-pool.md` lists exactly the pool. The **live** pass is the network step documented above
(`refscan132.py --verify`), which is deliberately **not** in `reproduce.sh`: the one-command
reproduction never touches the network.
