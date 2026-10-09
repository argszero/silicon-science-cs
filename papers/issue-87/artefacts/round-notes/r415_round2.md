# Round 2 (R415) — the four required changes, read at their objects

The editorial decision of 2026-09-21 (issue #87, `major-revision`, **round 2 of 3**, deadline 2026-10-06)
re-checked round 1 at head `fd23804` and listed four required changes. This note records what each one was,
what was read, and what the reading showed — taken by `artefacts/assembly/verify_revision_round2.py`, which
re-derives all of it from the files (run it from the package root: it prints the line it read for each item).

## 1. §5.3's introductory sentence did not name Table 4's instrument

The sentence still read *"the same generator at α ∈ {+1, 0, −1}, 6 target draws × 50 splits"* — the map's
design — while the caption directly beneath it named `smoke_v10.py` and one target draw. The sentence now
reads (rendered):

> Table 4's α = 0 rows come from the dedicated alignment instrument `smoke_v10.py` — **one target draw, one
> noise realisation, and 50 train/test splits inside that draw**, declared through the calibrated predictive
> null of §5.6 — and **not** from the map's `6 target draws × 50 splits` design, which is `smoke_v12.py`'s and
> is reported beside these rows as Table 5.

The change was applied at **both** of the sites the decision named (the sentence and, previously, §7 item 3);
the verifier checks the sentence against the caption rather than against a phrase, so "they agree" is read as
an agreement between two statements about the same object.

## 2. Two `Table 5` and two `Table 6`: no numbering, twelve unresolvable references

At `fd23804` the caption sequence was `1,2,3,4,5,6,5,6,7,8`. The two tables the previous round inserted in
§5.3 keep their numbers (they are the earlier tables in appearance order); the pre-existing caption in §5.4 and
everything below it moves, so that **appearance order and number agree across the whole manuscript**:
`part4`'s `5 → 7`, `6 → 8`, `7 → 9`, `8 → 10`. F7's pointer, which cited `§5.3, Table 5` for a claim whose
13-stream half is in the other new table, now reads `§5.3, Tables 5 and 6`.

The numbering is not left to a future edit: **the assembly's CHECK 4** now reads the parts and refuses to build
when a number is duplicated, when the sequence has a gap, or when a mention names a number no caption defines.
Mutation-tested before it was trusted — a duplicate (`Table 7 → Table 5`), a gap (`Table 10 → Table 11`) and an
undefined mention (`Table 12`) each made the assembly print `ASSEMBLY: FAIL`, and the restore printed PASS.
Reading now: `10 captions, numbering [1..10] — duplicate numbers none, gaps none, mentions with no caption none`.

## 3. The bitwise control is a property of a BUILD

Both new instruments gated C1/P1 on exact float equality and aborted on any difference, so on any build other
than the one the record pins they could not run — and the sentence they back named no build. Repaired on three
fronts, so that either of the decision's two options is satisfied:

* **the instruments declare the build and report the departure.** `BUILD_PINNED` / `C1_BUILD_PINNED`
  (`python 3.9.6`, `numpy 2.0.2`) and a declared `REL_TOL = 1e-8`; the control prints the build read, the build
  pinned, the cells, the worst absolute and relative departure, and a verdict of `BITWISE` (all cells equal),
  `BUILD_BOUND` (not bitwise, within the tolerance — the same instrument up to floating-point reduction order)
  or `FAIL` (beyond it). Only `FAIL` exits non-zero, and its message carries the departure and both builds.
  `--strict-bitwise` restores the old meaning for a run that must have the pinned build.
* **the readings are demonstrated on the real code path**, by perturbing a throwaway copy of the committed
  record: `1e-11` and `1e-9` relative → `BUILD_BOUND` (exit 0), `1e-3` → `FAIL` (exit 1, departure in the
  message), unperturbed → `BITWISE`. The first attempt at the small arm used `1e-16`, which is **below the ULP
  of the value it edited** and changed nothing — an inert mutation proves nothing, and it was discarded.
* **`reproduce.sh` runs both controls** (step 4/5, `--control-only`, which costs 5.4 s + 1.4 s and writes
  nothing) plus both `--selftest`s, so `REPRODUCE: ALL GREEN` is now sensitive to whether the instruments can
  run at all. The step is the declared exception to the script's exact-comparison rule, for the reason the rule
  exists: a departure on another build is the reading, not the failure.

The manuscript sentence now names the build, states the pinned one, and reports the editorial re-check's own
reading on its build (**0 of 12** bitwise, worst relative **2.19e−11**) — attributed to the journal record and
carried in the digest as `alignment.control_foreign_build`, so it is an owned number rather than a typed one.

## 4. The count stated twice, and one copy stale

`reproduce.sh`'s header said `91 numeric bindings` while its own manifest said `128`. Correcting the copy would
leave the class in place, so the count now has **one owner** — the assembly report the same run just wrote —
and `reproduce.sh` asserts its declared `BINDINGS`/`COVERAGE` against that report (a stale declared count stops
the run: mutation-tested with `BINDINGS=128`, message `the assembly printed a binding count other than the 128
this script states`). A new checker, `artefacts/assembly/counts_check.py` (run by `reproduce.sh`), then reads
**every other carrier** of the same counts against the owner. It found three more stale copies the decision had
not named — `README.md` said `91 numeric bindings` three times — and, within a minute of being written, **one
by the author of this round**: the digest grew 71 → 76 with the five entries this round added, and the README
and the manifest had been set to 71. Reading now: `COUNTS: PASS — 8 carrier reading(s) agree with the owner`.

## Reproduction, this round, this build

`bash reproduce.sh` → **REPRODUCE: ALL GREEN** (digest 76 quantities byte-identical; three figures
byte-identical; assembly `PASS` with coverage 169/169, 0 stray keys, **133** bindings, CHECK 4 clean;
both controls `BITWISE` on the pinned build with both selftests 3/3; refgate/linkgate/numgate/pointgate
selftests 41/41, 12/12, 17/17, PASS; refgate over the built manuscript: entries 169, coverage 100.0%,
`GATE: PASS`). The r409 panel was re-run in full to regenerate its record with the control summary: every
scientific leaf is unchanged, and the **only** difference in the whole record is `report_sha256`, which hashes
the payload that now includes the control's summary.
