# Provenance of `refs/references.json`

**This file is an input, and it is pinned by its own content hash.** `reproduce.sh` step 6
recomputes the sha256 of `refs/references.json`, compares it to the value recorded here, and
fails when they differ; it also fails, naming this path, when the file is absent. The corpus
is the one producer in this package that reaches the network, so its output ships as a
committed file instead of being fetched at reproduction time — the verifier's tree is an
export of the head and carries only tracked files.

| item | value |
|---|---|
| corpus sha256 | `0478b2879cfee53df1ee3d4d028af52b2813a790a85782f15eeb417abf033bc8` |
| bytes | 382387 |
| records | 270 |
| producer | `build_references.py --harvest` (Crossref REST, `works` endpoint) |
| built_at_utc (recorded inside the corpus) | 2026-10-23T02:07:01Z |
| scan date (`verification.checked_on`) | 2026-10-23 |
| rows per query | 16 |
| queries issued | 81 |
| queries that failed to run | 0 |
| search window | **none imposed** — Crossref's `query.bibliographic` takes no date filter in this call, so records of any year may return. The span is therefore not a claim this corpus can make; the scan date is. |

## What the harvest dropped, and how the survivors were reviewed

Dropping is recorded rather than silent, because a corpus is only as honest as its refusals.

| stage | kept | dropped |
|---|---|---|
| harvest relevance gate | 7 | 45 off-topic by title terms, 10 non-scholarly type, 2 near-duplicate, 0 with no DOI |
| review, pass 1 (salience: another field) + pass 2 (criterion: an adjacent construct) | 166 kept, 2 removed after the review | 102 excluded (37.8 %) |
| DOI verification | 166 verified | 0 stale, 0 not run, 0 no locator |

Queries that returned nothing usable, 13 of 81, listed rather than dropped: `apibreakage`, `condaenv`, `declarative`, `determinism`, `featuremodel`, `monorepo`, `pkgversion`, `presolve`, `rangeapi`, `smtconfig`, `tagmut`, `typosquat`, `versiondrift`.

`166` entries are `kept`, `102` are `excluded` with a reason, `2` are `removed` — a recorded
decision that a rebuild must not overwrite, which is why it lives in this file rather than in a
recomputed field.

## Why this file is the input and not an output

`place_references.py` reads it and writes only the derived report; `gate_citations.py` reads it
and writes only the numbered list. Neither rewrites the corpus, so a reproduction run leaves
these bytes untouched — checked by comparing every artifact after the run (see `README.md`).
Regenerating the corpus means re-harvesting, which needs the network; that is why the hash is
pinned here instead of the harvest being repeated by the one command.

## Venue repair, revision round 1 (2026-10-29)

The harvest truncated every container title to 60 characters (`build_references.py`, the join of
`container-title[0]` with `[:60]`). **92 of the 270 records were cut**, so the printed list showed
venue strings that stopped mid-word — `...48th International Conferen`, `...Computation, Automa` —
while nothing in the package could detect it, because the cut was stored in the corpus and every
later step reproduced it faithfully. The `[:60]` is removed, and the 92 recorded venues were
re-fetched from the registry by their own DOIs (92 requests, **92 restored, 0 unchanged, 0 with no
record, 0 errors**); each repaired entry keeps the harvested cut in `venue_full`-adjacent form
(`venue` now holds the record's own string). The corpus hash above is the repaired corpus; the
byte count moved with it. The superseded hash is stated here rather than deleted:
`fe77f50542d7f75d6faf82d1ba9a861adfa74ea4ed97214c9a3f20e6256a2239` (382387 bytes).
