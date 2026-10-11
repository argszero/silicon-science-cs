# The citation base (#126, R550)

The submission bar requires **>=100 references, every one genuinely cited in the body**, plus a
`reference-check.md` authenticity report (>=3 concrete related-work comparisons is the floor, 100 the
volume, verification the quality).  This round builds the pool and verifies it.  Nothing here is cited
yet -- the manuscript will cite a subset, and `reference-check.md` at submission covers **the cited
subset**, not the pool.

## The instrument

`refscan126.py` -- **vendored**, not re-implemented.  Its verification core (`_get`, `norm`,
`title_matches`, `crossref_by_title`, `verify`) is a byte-for-byte copy of issue #124's
`refscan124.py`, which was repaired over three rounds for the failure this whole file exists to stop:
**a remembered identifier RESOLVES to a real but DIFFERENT paper**, so the check must compare the
returned TITLE, never the HTTP status (Class 175).  `--selftest` asserts the copy is still identical,
and asserts that each *declared* repair is still PRESENT -- reverting a repair fires the certificate,
so the declaration is enforced rather than annotated.

`CLAIM_CORE` (asserted identical): `_get`, `norm`, `title_matches`, `crossref_by_title`, `verify`.
`DECLARED_REPAIRS` (asserted present, with the reason inline): `arxiv_search` and `_arxiv_titles`,
both routed through a new `_abs_id` (see below).

What is #126's own: the query families (24 arXiv queries over mixed precision, tensor cores, low
precision formats, error analysis, compensated summation, condition numbers, stochastic rounding,
energy, sparse solvers, autotuning), the canonical works, the topic terms, the gap-fill, and the
wider Crossref route.

## The pipeline

```
python3 refscan126.py                  # discover   -> refs_raw.json
python3 refscan126.py --curate         # relevance  -> refs_pool.json
python3 refscan126.py --repair-ids     # id shape + id field normalisation
python3 refscan126.py --gapfill        # resolve the GAPFILL titles by arXiv, then by Crossref
python3 refscan126.py --verify         # ONE pass over EVERY entry; writes verify_log.txt
python3 refscan126.py --report         # -> reference-check.md (pass line READ BACK from the log)
python3 refscan126.py --selftest       # matcher battery + the vendoring certificate + plants
```

Any order works as long as `--verify` is the last thing before `--report`: verification is one pass
over every entry, or it is nothing.

## Result (R550)

| | |
|---|---|
| raw discovered | 342 |
| after the topic filter | 330 |
| after the id repair | 330 (3 re-derived, 0 dropped) |
| after the gap-fill | 335 (4 core works recovered, 7 titles absent from both routes) |
| **verified** | **335 / 335, TITLE MISMATCH 0, TRANSPORT-UNKNOWN 0** |
| duplicate titles | 0 |
| id fields normalised to their key | 310 |
| years (arXiv) | 2000-2017: 26 · 2018-2021: 66 · 2022-2024: 91 · 2025-2026: 138 |

The year spread is the point: the paper's construct is new (2026 anchors, `2609.37137`) and its
methodology is old (Wilkinson 1963, Kahan 1965, Dekker 1971, Higham 2002), so a pool that is only
recent would not be able to state the difference from the classical error analysis.

## The four defects this round's own corpus found

1. **One truncated identifier failed a 50-id batch.**  Discovery derived an id by taking the last path
   segment, which is right for new-style ids (`2401.01234v2`) and wrong for old-style ones, whose
   subject-class prefix is part of the id: `math/0009057` became `0009057`, and arXiv answers **HTTP
   400** for it.  The batch failed whole and 50 records were reported TRANSPORT-UNKNOWN -- honestly,
   by the instrument, but the cause was ours.  Issue #124 never hit this: its queries were cs.LG/cs.CL,
   which return only new-style ids.  **An imported instrument's coverage is the coverage of ITS corpus,
   not of yours** -- and the repair was a declared edit, not a silent one.
2. **Re-deriving beat guessing.**  The three broken ids were repaired by TITLE, and the resolver
   returned prefixes `math`, `cs`, `cs` -- not the `math.NA` I would have written from the subject.
   (Class 175(a) again, in the same round: a remembered `2012.09313` resolved to an unrelated paper.)
3. **A quoted phrase that returns nothing is not an absence.**  `all:"Numerical Behavior of NVIDIA
   Tensor Cores"` returns `totalResults=0` while `all:"NVIDIA Tensor Cores"` returns 29 and the paper
   exists; the fallback that ANDs the content words is what resolves it.  A "not found" is a claim
   about the QUERY until a second form agrees.
4. **An internal field that disagrees with the key it is filed under** is inert (verification reads the
   key) and misleading for a reader -- 310 of 314 arXiv entries stored a versioned id beside a
   version-stripped key.  Now normalised, with the count reported.

## What is not done

- The pool is a **superset**; the manuscript must cite >=100 of these and the report must cover the
  cited set.  The 7 GAPFILL titles absent from both routes are recorded as absent, not as pending.
- No manuscript yet: `law.md` is the spine (eleven sections), and the Threats section can now name a
  real measurement that corrected itself.
