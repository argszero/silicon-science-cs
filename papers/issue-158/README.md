# issue #158 — the resolution axis

What decides whether recall@k is even *determined* by the data? Every number in this package comes
from one program in this directory, and `./reproduce.sh` re-derives all of them.

This README covers reproduction. The manuscript is what the numbers are for.

## One command

```sh
./reproduce.sh          # tier A: needs numpy and the committed fixture. Nothing else.
./reproduce.sh full     # tier A + tier B: also needs the 1M corpus.
```

**Expected output**, last line:

```
REPRODUCE: ALL GREEN (5 steps)
```

(with `core`, step 5 reports `NOT RUN` and the last line reads `REPRODUCE: 1 STEP(S) NOT RUN, 0 failed (5 steps)`).

Tolerance: **none**. Step 3 runs the mechanism table twice and byte-compares `results/mechanism.json`,
so a number that moves between two runs of the same program on the same input fails the build. A
number that moves is not a measurement.

**Interpreter.** Requires **CPython 3.9** with **numpy 2.0.2** for tier A, plus **h5py 3.14.0** for
tier B. On a machine whose `python3` lacks numpy the steps print `NOT RUN` — not a failure — and name
the override:

```sh
PY=/usr/bin/python3 ./reproduce.sh
```

An absent declared dependency is reported as `NOT RUN` and never as a failed step, so the failed
count means what it says.

## The two tiers

| tier | needs | reproduces |
|---|---|---|
| **A** | numpy + `fixture/sift_subset.npz` (1.8 MB, committed) | the mechanism table over 20,000 descriptors, and both endpoint controls |
| **B** | the 1M corpus (501 MB, `./fetch_corpus.sh`) + h5py | the same axis at 1,000,000 descriptors |

Tier A is the tier a clean machine can always run, and it carries the claim. Tier B is the scale
check: the same ordering, 50× larger. When the corpus is absent, tier B prints `NOT RUN` and exits 0 —
it is never reported as a failure and never silently skipped.

## Getting the data

The 1M corpus cannot be committed. `./fetch_corpus.sh` fetches it from a pinned URL and verifies the
pinned byte count **and** sha256 (`dd6f0a6e…5984`); a mismatch is a hard failure, so "the data changed"
cannot be confused with "the code is wrong".

```sh
./fetch_corpus.sh            # download into corpus/, then verify
./fetch_corpus.sh --check    # verify only; exit 1 if absent or wrong
```

The committed fixture is checked the same way on every run (step 1, against `fixture/SHA256SUMS`).
`build_fixture.py` is the maintainer's path that produced it and needs the 1M corpus; a reader never
runs it. The fixture is a seeded subsample, so re-running it on the same corpus reproduces the same
bytes.

Data: `sift-128-euclidean` from the ann-benchmarks corpus — 1,000,000 × 128 real SIFT descriptors,
integer-valued, with 10,000 query vectors. All distances in this package are **exact integers**: the
quantiser reconstructions are constrained to the data's own integer grid, and every distance
computation is asserted against an independent int64 path before a tie is counted (`tiefloor.py`,
`exact_sq_distances`).

## What the programs are

| file | role |
|---|---|
| `tiefloor.py` | the instrument: identified-set floor, local resolution, the three quantisers, exact integer distances. Pure functions, no I/O. |
| `run_mechanism.py` | tier A — the table, plus the two endpoint controls |
| `run_scale.py` | tier B — the same axis at 1M; `NOT RUN` without the corpus |
| `check_claims.py` | reads the artefact back and tests the claims the paper makes about it |
| `verify_fixture.py` | the committed fixture against its recorded sha256 |
| `build_fixture.py` | maintainer only: cuts the fixture out of the 1M corpus |
| `reproduce.sh` | one command, the journal's exit contract |
| `fetch_corpus.sh` | pinned fetch + checksum for tier B |

## The endpoint controls, and why they are not decoration

`check_claims.py` asserts both on every run. An instrument that cannot be made to return "fully
identified" where the answer is known, and cannot be made to return "maximally unidentified" on
constructed input, has not been shown to measure anything, and its numbers elsewhere are uninterpreted.

- **float endpoint** — raw descriptors, tier A and tier B: median boundary tie group **1**, mean
  identified-set floor **1.0000**. The metric is fully determined there.
- **constructed endpoint** — every corpus point replaced by one repeated reconstruction: the whole
  corpus is one tie group, floor **0.0000**.

## What this package does not claim

- **One corpus.** Every number is on `sift-128-euclidean`. Tier B is the same corpus at 50× the
  points, not a second dataset.
- **Seeds are not independent evidence.** A cell is one (family, budget) configuration; the three
  seeds are a check on that configuration's stability, not three confirmations of it. `check_claims.py`
  prints both counts and the configuration count is the one that matters.
- **`resolution` is measured, not derived.** It is the number of distinct distance values the 1000
  nearest points occupy — an empirical quantity of the distance the quantiser induces, not a closed
  form.
