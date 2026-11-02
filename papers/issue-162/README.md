# Issue #162 — reproduction

*Eleven Nines Is Not a Measurement: What Per-Device Failure Rates Identify About Replicated Loss,
and What a Stated Dependence Buys.*

Everything in this package is produced by one program, `nines.py`, from no input at all: the whole
object is exact rational arithmetic over a declared grid. There is no download, no corpus, no seed
and no measurement.

## One command

```sh
./nines.py --selftest --grid --emit nines_findings.json
```

Run from this directory. `nines.py` is stdlib-only Python 3 (developed under CPython 3.9.6); it
imports `argparse json math os sys fractions` and nothing else, so there is no environment to
prepare.

## Expected output

The self-test runs its controls and one plant per control, then prints the reading grid and writes
the artefact. A green run ends with these lines:

```
== summary
   controls passed : <N>
   plants fired    : <M>
   NOT RUN         : 0
   FAILED          : 0

SELFTEST: ALL GREEN (<N> controls, <M> planted)
```

`N` and `M` are printed by the run, not asserted here: a count quoted in a document and computed by
a program drift apart, and the printed one is the one that cannot. The grid then ends with the cell
counts and the widest span, and `-> nines_findings.json` reports the artefact it wrote.

**Tolerance: none needed.** The arithmetic is exact (`fractions.Fraction`); floats appear only at the
printing and JSON boundary. Re-running on the same Python major version rewrites
`nines_findings.json` byte-identically, and `git diff --exit-code nines_findings.json` after a run is
the check.

## Exit status — three outcomes, deliberately kept apart

| code | meaning |
|------|---------|
| `0` | every control agreed, including both attainment routes |
| `1` | a control FAILED — the reading is not a finding and nothing is written |
| `3` | NOT RUN — a leg could not run under its declared node budget (`--budget`), so it measured nothing. Neither a pass nor a failure. |

Collapsing `3` into `0` is how a run comes to claim a number it never computed. The exhaustive
attainment leg is exponential and declares its budget; `./nines.py --budget 50` is the quickest way
to see the third state.

## Files

| file | produced by | what it holds |
|------|-------------|---------------|
| `nines.py` | — | the instrument: the identified set, both attainment routes, the stated-dependence family, the controls and their plants |
| `nines_findings.json` | `./nines.py --grid --emit nines_findings.json` | the 20-cell reading: quoted figure, identified set endpoints, both in nines, the span, and whether the set reaches total loss |

`nines.py` writes nothing unless `--emit` names a path, so running the self-test can never replace
the artefact a report describes.
