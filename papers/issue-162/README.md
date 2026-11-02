# Issue #162 — reproduction

*Eleven Nines Is Not a Measurement: What Per-Device Failure Rates Identify About Replicated Loss, and
What a Stated Dependence Buys.*

The paper's object is arithmetic. `nines.py` computes all of it from no input at all — exact rational
arithmetic over a declared grid, no download, no corpus, no seed, no measurement. The reference corpus
is the only part assembled from outside, and it is committed.

## One command

```sh
./reproduce.sh
```

Stdlib-only Python 3 (developed under CPython 3.9.6): `argparse json math os sys fractions hashlib re
time unicodedata urllib`. There is nothing to install and nothing to fetch.

`reproduce.sh` runs, in order: the instrument's self-test; the reading, emitted to
`nines_findings.json`; the citation gate, which renders `manuscript.md` and rewrites
`reference-check.md`; and then a byte comparison of each of those three artefacts against the
committed copy.

## Expected output

```
reproduce.sh -- issue #162
== 1 instrument self-test (controls + one plant each)
   [ok]   instrument self-test (controls + one plant each)
...
STEPS RUN: 6
REPRODUCE: ALL GREEN (6 steps)
```

The step count and the control/plant counts are printed by the programs, not asserted here: a count
quoted in a document and a count computed by a program drift apart, and the printed one cannot.

**Tolerance: none.** The arithmetic is exact (`fractions.Fraction`); floats appear only at the
printing and JSON boundary. The three artefacts must come back byte-identical, and that comparison is
the second half of the run.

## Exit status — three outcomes, deliberately kept apart

| code | meaning |
|------|---------|
| `0` | every step ran and every artefact reproduced |
| `1` | a control failed, a gate failed, or an artefact changed on re-run |
| `3` | NOT RUN — a leg could not run under its declared node budget, so it measured nothing |

Collapsing `3` into `0` is how a run comes to claim a number it never computed. The exhaustive
attainment leg is exponential and declares its budget; `./nines.py --budget 50` is the quickest way to
see the third state.

## Files

| file | authored or derived | what it holds |
|------|--------------------|---------------|
| `nines.py` | authored | the instrument: identified set, both attainment routes, the stated-dependence family and its closed-form inverse, controls with one plant each |
| `nines_findings.json` | derived (`--grid --emit`) | the 20-cell reading: quoted figure, identified-set endpoints in probability and in nines, the span, whether the set reaches total loss, and `rho_one_decade` |
| `harvest_refs.py` | authored | assembles the reference corpus from registry responses and verifies each record by DOI |
| `refs/references.json` | derived (network) | the corpus with its stored verification state; committed so reproduction stays offline |
| `placements.py` | authored | which record supports which claim, and the named exclusions |
| `manuscript.src.md` | authored | the manuscript with `{{c:<claim>}}`, `{{grid}}` and `{{refs}}` markers |
| `manuscript.md` | derived (`gate_citations.py --render`) | the paper with claims rendered as numbered clusters, the reading table rendered from the artefact, and the reference list generated |
| `reference-check.md` | derived (`--report`) | the citation report: what was searched, what was refused and why, and what is cited |
| `gate_citations.py` | authored | binds citations to claims, checks the floor, checks the prose's numbers against the artefact |

`nines.py` writes nothing unless `--emit` names a path, so a self-test can never replace the artefact a
report describes. `manuscript.md` and `reference-check.md` are derived files: do not edit them,
regenerate them.

## Re-harvesting the corpus (maintenance, network)

```sh
./harvest_refs.py --harvest     # issue the declared queries, screen and record refusals
./harvest_refs.py --verify      # re-fetch every record by DOI and corroborate it
```

Two rules make this safe to re-run. Verification state is **carried forward**: a record verified
earlier keeps that verdict, so a rate-limited day cannot thin the corpus and read as a finding. And a
key collision is broken by a DOI-derived suffix rather than by arrival order, so adding a query cannot
silently re-key a record the placement already cites — if it ever does, `gate_citations.py` fails
loudly rather than renumbering underneath a citation.

## What `rho` is, and is not

`rho` is a **declared** parameter here and is never fitted: nothing in this package observes a
dependence. The inverse `rho = (target - p**r)/(p - p**r)` answers a conditional — *if* the loss figure
were to come out at `target`, what would have to be stated — and `rho_one_decade` reads that
conditional in the unit the quote is made in. Calling either of them a measurement of a store would be
the error this paper is about. The decision is written into the artefact (`dependence`) as well.
