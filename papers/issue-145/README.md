# Issue #145 — Attested Is Not Covered

*What published build provenance names, and the detection ceiling a compromised input faces.*

**Contribution level: `theory+empirics`** — one proved non-identification result plus a measurement
over three frames and two builder classes, with ground truth by set arithmetic over public registries
(no sampling, no annotation, no proxy).

## One command

```
bash reproduce.sh
```

Expected last line:

```
REPRODUCE: ALL GREEN (10 steps)
```

`reproduce.sh` runs, in order: (1) the SHA-256 pins of the three frame artefacts; (2) the ceiling law
in exact rational arithmetic (**66** checks, 5 propositions, 3 wrong variants plus 1 mutation);
(3) the plant battery (**17** checks, 9 plants and 4 deliberately wrong variants — a guard nobody has
seen fail is not a guard); (4) the Wilson intervals and whether presence and coverage are separated;
(5) every number in the claim table re-derived from an artefact **and** required to be **bound to its
declared statement site** — a number that appears somewhere else in the prose is not bound; (6) the
claim gate's own plants, so a gate nobody has seen fail is not a gate: drift at a statement site,
drift while the token still stands elsewhere, a sibling occurrence, a removed site, and the clause
binding left intact; (7) the reference review reproducing the same kept/excluded counts; (8) the
citation pool being a function of the corpus; (9) the citation gates C1–C5; (10) the reference-check
report being a function of the pool.

## Environment

- Python **3.9** (`/usr/bin/python3`). **No third-party module is needed** — `.github/tools/envgate.py`
  reads this package's imports as 0 third-party modules, so the frames are committed and pinned and
  every number is re-derived from them offline with the standard library alone. (The *enumerators*
  need network access, not a library.)
- **No network is needed to reproduce this paper's claims.** Re-*enumerating* the frames from the live
  registries is a different act — it answers "what do the registries say today" — and it needs network
  access plus roughly 8 minutes as measured (npm 77 s, PyPI 240 s, OCI 152 s). The enumerators are in
  this package:

  ```
  python3 enumerate.py          # npm  -> writes snapshot_npm_d1_pilot.json
  python3 pypi_enumerate.py     # PyPI -> writes snapshot_pypi.json
  python3 oci_enumerate.py      # OCI  -> writes snapshot_oci.json
  ```

  A re-enumeration writes **new** snapshots and would require the pins in step (1) to be updated. That
  is a deliberate act, not a side effect of a reproduction run — which is why it is not a step here.
- Exit 0 is `ALL GREEN`, exit 1 is a difference the run measured, exit 2 is a step this build could
  not take. A missing dependency is the third state, never the second.

## What is what

| file | role |
|---|---|
| `manuscript_source.md` | the paper's source, with citation **keys** `[@key]` |
| `manuscript.md` | the paper (built; do not edit by hand) |
| `build_refs.py` | numbers the citations, emits the reference list, and enforces C1–C5 |
| `refs_pool.json` | the reviewed citation pool the keys resolve against; each entry carries the **full** author list |
| `harvest_authors.py`, `authors_by_doi.json` | re-query Crossref by DOI for the full author list, and the **committed cache** that makes the pool regenerate offline |
| `reference-check.md` | per-entry citation verification (built) |
| `references.json` | the corpus the pool was cut from, **including the records refused and why** |
| `review_references.py`, `export_pool.py` | the two review passes and the pool freeze |
| `ceiling_law.md`, `ceiling_check.py` | the theory leg: propositions, proofs, exact verification |
| `plant_coverage.py` | the plant battery for the coverage instrument |
| `wilson_separation.py` | presence vs coverage, with intervals |
| `check_claims.py` | every printed number re-derived from its artefact **and bound to the statement site** that prints it (`--selftest` plants the drift) |
| `snapshot_*.json(.sha256)` | the three frame artefacts, pinned |
| `enumerate.py`, `pypi_enumerate.py`, `oci_enumerate.py`, `coverage.py`, `probe_coverage.py` | the networked enumerators and the coverage helpers |
| `manuscript_skeleton.md` | the argument's plan and the claim → artefact table |

## How a printed number is held to its artifact

The claim table names, per row, the artefact and key that own a quantity. Two gates run over it, and
both must pass:

1. **re-derivation** — the table's value is compared with the artefact's value, in both directions;
2. **statement-site binding** — every checked row's key must be *declared* where the manuscript states
   it, as a source annotation `<!-- c: npm.summary.units -->` sitting beside the number, and the clause
   the annotation closes must contain that artefact value.

The second gate is not a document-wide presence test, and the difference is the point. The published
version asked only whether each value's digits appeared *somewhere* in the manuscript, so changing
`giving **184** package releases` to `**999**` at its statement site left the gate green — `184` stood
at two other lines of the same file. Read the clause, and the same drift is red, naming the row and
the site. Five rows (the identifier rows 23b/23c and the three printed-only rows 26–28) are listed as
**NOT CHECKED** with their reason rather than passed by a stray digit.

`python3 check_claims.py --selftest` runs the plants that make this claim good: the drift above, a
sibling occurrence drifting while its twin stands, and a quantity whose annotation was removed — each
must fire, and the shipped manuscript must stay green.

## What this paper claims, and what it does not

It claims that **the artefact a provenance verifier traverses does not carry the dependency closure**,
in three deployments that differ in mechanism and agree in outcome — and that a coverage measurement
does not identify the detection ceiling, while a single zero forces it to zero under every joint law.

It does **not** claim that any package, image or publisher is insecure, or that any attack succeeds:
no attack was run. The 12 container images are a **selection**, not a sample, and no frequency is read
from them. Two of the twelve required authentication and are recorded **NOT RUN**, never imputed.

## A known and corrected defect, recorded rather than quietly fixed

Step (1) failed the first time it was run: `snapshot_oci.json.sha256` did not match the artefact it
pinned. The artefact had not been modified — its own `retrieved_at_utc` (`2026-10-21T05:16:12Z`)
matches its last write — so the **pin** was the stale side: it had been computed from an intermediate
write rather than from the file that ships. Every number in §7 was re-read from the shipped artefact
before the pin was recomputed. The step exists precisely to catch this, and it did.
