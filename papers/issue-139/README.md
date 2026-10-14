# Issue #139 — Proving Is Not Paying: the Success-vs-Cost Frontier of Interdependent Proof Obligations

**Contribution level: `theory+empirics`.** This package is the evidence layer for the manuscript: four
instruments, each with its own plant battery, the reports every manuscript number is read from, a
generated figure set, and a verified reference layer. Ground truth is **by construction** — the model
*is* the ground truth, and every reported quantity is an exact count or an exact expectation over it,
so there are no timings anywhere in the package.

The model: a dependency DAG whose obligations each cost one unit per attempt and succeed with a
declared probability, where discharging an obligation raises its dependents' success probability by the
coupling `c`. The measured object is the **frontier** `F(B) = E[# discharged after B attempts]`,
computed by backward induction (`2^n` discharged sets), which makes every cell a computed frontier and
not an estimate.

## Reproduction

```
cd papers/issue-139 && bash reproduce.sh
```

* **Expected output**: `REPRODUCE: ALL GREEN`, preceded by one line per check. The four instruments
  print `SELFTEST 7/7` each and then each report is compared **byte-for-byte** (`Tolerance: exact`)
  against the report this package ships (`spike_v0` `5b148eab…`, `v1` `7d0806f1…`, `v2` `52ec9778…`,
  `v3` `8abc814c…`, plus the three text reports). The **claims leg** then re-reads the fresh reports
  and asserts **27** of the manuscript's headline numbers against them (`CLAIMS: 27 checked, 0 wrong`),
  and five **plants** must fire (a perturbed instrument must change its report; a broken uncoupled
  recursion must fail its battery; a broken coupled recursion must change the report; a planted number
  must make the claims leg fail; and a README quoting a stale manuscript size must fail the `readme`
  leg). The figure certificate prints `FIGURE SELFTEST 35/35` and the
  **nine** generated files (six SVGs, `FIGURES.md`, `CAPTIONS.md`, `manifest.json`) are compared
  byte-for-byte. The reference layer prints `refscan selftest SELFTEST: ALL PASS`,
  `refscan gate GATE 8/8` and `reference-check … is what this renders`. Finally the manuscript is
  re-rendered (`MANUSCRIPT: MATCH -- 288 references, 60 numbers, 151130 bytes re-rendered
  byte-identically`), its own plant battery runs (`SELFTEST 4/4`), and the journal's gates are applied
  to the built manuscript: `numgate`, `linkgate`, `pointgate` and
  `refgate … covered=288/288 coverage=100.0%`. The line just quoted is **itself checked**: the
  `readme` leg reads this file back against the line the run printed — three numbers, byte count
  included — and a copy that quotes a stale size fails it, with a plant proving the comparison can
  fail.
* **Exit status**: `0` = `REPRODUCE: ALL GREEN`; `1` = at least one step **FAILED** (the count is
  printed with it); `2` = no step failed, but a journal gate could not read its window and printed its
  own named **`NOT RUN`** — a **coordinate of the run, not a finding about the work**. The three tree
  gates (`numgate`/`linkgate`/`pointgate`) take their carrier set from `git ls-files`, so over a
  `git archive` **export** (which carries no `.git`) they report `NOT RUN: the carrier set is empty`
  and exit 2; `refgate.py` reads its window from its arguments, so it runs and passes in either form.
  An export run therefore ends at **2**, and the exit status says which of the three happened.
* **Environment**: CPython 3, standard library only — **no third-party import appears anywhere in this
  package** (`json`/`math`/`os`/`sys`/`random`/`itertools`/`argparse`), so no library version enters a
  comparison; matplotlib is neither used nor required. Measured byte-identical under **3.9.6** and
  **3.13.9**.
* **Cross-build leg**: an `exact` tolerance is a claim about a *build*, not only about a run, and the
  builtin `sum()` over floats became Neumaier-compensated in CPython 3.12 — so the leg that can see a
  version-scoped defect is the one that re-runs every report under a second interpreter, and the pair
  has to **straddle** that boundary (two builds on the same side of it are one reading taken twice):
  `REPRO_BUILDS="/usr/bin/python3 python3.13" bash reproduce.sh`. Measured here: every shipped report
  byte-identical under **3.9.6 and 3.13.9**, one on each side of the 3.12 change.
* **Inputs**: none, and no network. Every graph, difficulty vector, coupling level and schedule is
  declared in the instruments, and the only randomness is drawn from the committed seeds, so a run
  touches nothing outside its own directory. (The reference layer's *live* verification is a separate,
  documented network pass — see **Reference layer** below; the offline gate re-checks its committed
  receipt without touching the network.)
* **Cost**: about **two minutes** (four instruments, each re-run once, plus the batteries, the figure
  certificate, the offline reference layer and the manuscript re-render); about two more with the
  cross-build leg.
* **Writes nothing inside the package**: each instrument runs with `SPIKE_OUT` pointing into a private
  temp directory the script creates and removes.

## Layout

| Path | What it is |
|---|---|
| `spike_v0.py` | v0 — the two declared exact cases: the coupling gain by schedule, the zero-coupling anchor, and the pre-check that reshaped the registered priors |
| `spike_v1.py` | v1 — the `n = 8` grid: 7 DAG families × 5 difficulty distributions × 4 coupling levels × 4 schedules, the `c = 0` certificate against the closed form, and the P1/P2/P3 findings |
| `spike_v2.py` | v2 — the two laws: the exact two-obligation biconditional over a 1600-cell `(p1, p2)` grid (beside the hand-derived rule that disagrees), and the pass-rate budget-sizing rule |
| `spike_v3.py` | v3 — the settled n-form: **every permutation** at `n` = 5, 6, 7, the guarantee against its converse, the coupling attribution, and the `c > 0` boundary |
| `spike_v*_results.json` | The report each instrument emits; every manuscript number is read from one of these |
| `spike_v1_robust.txt`, `spike_v2_reliability.txt`, `spike_v3_report.txt` | The instrument's human-readable report (robustness across sizes and seeds; the laws' reliability; the exhaustive table) |
| `make_figures139.py` | The figure set: six SVG figures, `FIGURES.md`, `CAPTIONS.md` and `manifest.json`, generated from the four reports — standard library only, deterministic, `--selftest` runs the certificate **F0–F3** |
| `figures/` | The generated figure set, its captions (from the same run), and the sha256 manifest |
| `refscan139.py` | The reference layer: discovers candidates from arXiv by topic query, verifies the pool against live Crossref/arXiv records, and gates the pool offline (`--gate`) with its own plant battery (`--selftest`) |
| `refs/pool.json` | The verified pool (288 entries) — every manuscript reference comes from here, never from memory |
| `refs/roles.json` | The role class of each pool entry (the citation list's difference lines are scoped by it) |
| `refs/verify-run.txt` | The committed verification receipt: the verbatim stdout of the network pass, naming the pool it verified by sha256 |
| `reference-pool.md` | The pool in reading order, with the discovery query that found each entry |
| `make_reference_check.py` | Renders the generated blocks of `reference-check.md` (the verification receipt, the journal gate's output, and the per-entry table) — `--check` compares without writing |
| `refgate-journal.txt` | The committed receipt of the journal's own reference gate, re-run and compared by `reproduce.sh` |
| `build_manuscript.py` | Renders `manuscript.md` from `manuscript.src.md`: every `{{number}}` resolved from a committed report, every `{ref:…}` citation resolved against the pool, every `{{figN}}` block from the generated captions — and it **refuses to render** on an unknown or unused number, a citation off the pool, fewer than 100 cited references, a missing figure image or an unresolved placeholder |
| `manuscript.md`, `manuscript.src.md` | The manuscript, and the source it is rendered from (the numbers and citations live in the source as placeholders) |
| `reference-check.md` | The citation authenticity report, with the journal gate's verbatim output and a per-entry verification table |
| `heilmeier.md`, `notes.md` | The six Heilmeier answers, the adversarial checks and the registered priors (research workspace, git-ignored) |

## The manuscript's numbers

Nothing in `manuscript.md` is typed twice. `build_manuscript.py` resolves every number from the
committed report that owns it, every citation from the verified pool, and every figure block from the
captions generated in the same run as the images — and it fails the build when a number it carries is
never used, when a citation key is not in the pool, when fewer than 100 references are cited, or when a
figure's image is absent. The claims leg in `reproduce.sh` is the second reading: it asserts the same
headline numbers against **freshly generated** reports, so a number that moves in the instrument and
not in the prose fails the reproduction rather than the reader.

## Reference layer

`refscan139.py` discovers the related work (45 arXiv topic queries + 14 canonical works found **by
title** on Crossref) and verifies **every** pool entry against a live record by comparing the returned
**title** with the stored one, scored as the smaller of the two coverage fractions (a one-sided score
lets a short generic title reach 1.00 against a long specific one). Result: **288 / 288 VERIFIED, 0
title mismatch, 0 transport-unknown**; all 288 are cited in the manuscript (gate coverage 100.0%). The
verbatim run is the committed receipt `refs/verify-run.txt`, whose first line binds it to the shipped
pool by sha256 — so a receipt that outlived its pool is caught by `--gate` rather than quoted.

## Reference to the registration

The research registration (issue #139) carries the six Heilmeier answers, the adversarial checks, the
**prior beliefs** and the registered success criteria. The manuscript reports every prior against its
outcome (confirmed / refuted / decided) in §4, including the two refutations and the one criterion
that is **unmet** in its registered form — the registered placebo control is invalid by measurement,
and the manuscript says so rather than dropping it.
