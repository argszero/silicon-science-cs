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

Stdlib-only Python 3 (developed under CPython 3.9.6): `argparse ast datetime fractions hashlib html io json math os re sys tempfile time unicodedata
urllib`. There is nothing to install and nothing to fetch. That list
is a claim about the build, so it is read on every run by `check_declared_env.py`, which compares it
with the modules the package's own files import and refuses a list that is narrower than the code —
or wider than it. It is there because the list *was* narrower: `gate_citations.py` imports `html` and
the sentence did not name it, and no journal gate could see that, because `envgate` asks only whether
every third-party name is declared and never asserts a standard-library one.

`reproduce.sh` prints one line per step, and that output — not a sentence here — is the list of
what it runs: an enumeration in this file is a second copy of the script's own count, and a copy is
what drifts. Two of the steps are worth naming because they are about this file rather than about the
instrument: one compares the three derived artefacts against the SHA-256 digests sealed in
`artefacts.sha256`, and one reads the module list above against the modules the code imports.

**That digest step deliberately does not use git.** It used to: `git diff --quiet` and `git ls-files`
decide nothing in a `git archive` export, which carries no `.git` — so for every reader following
this file, three steps reported NOT RUN while the author saw `[ok]`. A check only the author can run
is not a check. The manifest travels inside the package and the comparison needs no git and no
network.

## Expected output

```
reproduce.sh -- issue #162
== 1 instrument self-test (controls + one plant each)
   [ok]   instrument self-test (controls + one plant each)
...
== 7 the stated step count matches the steps this script runs
   [ok]   the stated step count matches the steps this script runs
STEPS RUN: 8   NOT RUN: 0
REPRODUCE: ALL GREEN (8 steps)
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
| `check_step_count.py` | authored | the count check: reads the two counts this file states and compares them with the `step` call sites in `reproduce.sh`, and refuses a header that states a count at all (a comment cannot be derived, so it must not compete with the run) |
| `check_declared_env.py` | authored | the declaration check: reads the module list above against the modules the package imports, and refuses a list narrower than the code or wider than it |
| `check_file_table.py` | authored | the inventory check: reads this table against the files the package ships, in both directions, and names every difference |
| `nines_findings.json` | derived (`--grid --emit`) | the 20-cell reading: quoted figure, identified-set endpoints in probability and in nines, the span, whether the set reaches total loss, and `rho_one_decade` |
| `harvest_refs.py` | authored | assembles the reference corpus from registry responses and verifies each record by DOI |
| `refs/references.json` | derived (network) | the corpus with its stored verification state; committed so reproduction stays offline |
| `refs/candidates.json` | derived (network) | every record the harvest returned and the screen's decision on it, with the refusals and why — so a refusal can be checked rather than believed |
| `placements.py` | authored | which record supports which claim, and the named exclusions |
| `price_search.py` | authored | section 8's collector: the declared queries for a statement of what a dependence assumption costs, the title screen, and a refusal for any surviving record with no recorded verdict |
| `price_search.json` | derived (`price_search.py --harvest`, network) | the stored hits, their screen results and the authored verdicts by DOI; committed so the offline run is a verdict and not a fetch |
| `manuscript.src.md` | authored | the manuscript with `{{c:<claim>}}`, `{{grid}}` and `{{refs}}` markers |
| `manuscript.md` | derived (`gate_citations.py --render`) | the paper with claims rendered as numbered clusters, the reading table rendered from the artefact, and the reference list generated |
| `reference-check.md` | derived (`--report`) | the citation report: what was searched, what was refused and why, and what is cited |
| `gate_citations.py` | authored | binds citations to claims, checks the floor, checks the prose's numbers against the artefact |
| `seal_artefacts.py` | authored | `--seal` rewrites the digest manifest (a maintenance act); `--verify` only compares, and is what `reproduce.sh` runs |
| `artefacts.sha256` | derived (`--seal`) | the SHA-256 of the three derived files, so byte identity is decidable without a `.git` |
| `reproduce.sh` | authored | the one command: a verdict per step, with NOT RUN kept distinct from a failure |
| `README.md` | authored | this file: the one command, its expected output, the module list, and this table |

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
