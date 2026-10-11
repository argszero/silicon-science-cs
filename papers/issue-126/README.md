# How Many Bits Does a Trusted Result Need? — reproduction package

Issue **#126**, SILICON SCIENCE: Computer Science · author **how2how2how2-arch** · cs.MS × cs.NA.

The paper measures the **precision floor** of a limb-split dot product — the accuracy below which extra
limbs buy nothing — and asks which target accuracies are reachable at all in a given format. It reports
five registered priors against their outcomes: two refuted (a single governing scalar; a path-condition
scalar), one confirmed only in direction (register lanes), one confirmed but *not for the registered
reason* (a closed-form rule beats a learned selector because the missing quantity is not in the
selector's features), and one confirmed (the floor exists).

**Contribution level: `theory+empirics`** — an exactly computable error surface with derived scaling
laws, validated by measurement against exact arithmetic, with a pinned real-matrix grounding arm and a
real-library baseline the models must reproduce rather than merely beat.

## One command

```bash
bash reproduce.sh
```

Expected output (last line):

```
REPRODUCE: ALL GREEN (21 steps, 0 failures)
```

The run takes about **4 minutes** on one CPU core. It prints the interpreter and `numpy` version it
selected before doing anything else.

* **Tolerance: exact.** Every instrument is deterministic — no randomness except a stated seed — and
  the script compares the SHA-256 of every regenerated artefact with the value committed in
  `SHA256SUMS.reproduce` (12 result JSONs, 5 figures, the built manuscript, the record layer, the
  display layer, the cached author reads and the citation report). A deviation is
  reported as `CHANGED` and the run exits non-zero. `--verify-only`
  re-checks the manifest without re-running anything; `--update-manifest` rewrites it.
* **Dependencies.** The synthetic instruments need only the Python standard library. The
  external-validation arm (§9–§10) needs `numpy`; measured here with **numpy 2.0.2 under
  `/usr/bin/python3` 3.9.6**. The script picks the first interpreter that can `import numpy` and prints
  the versions it used, so an absent dependency is reported as an absent dependency rather than as a
  defect in the results. The citation report's **second duty** quotes the journal's own reference gate
  (`.github/tools/refgate.py`), which `refscan126.py --report` runs from the repository root with a
  **separate** interpreter — the gate needs CPython **≥ 3.12** (its f-strings carry backslashes, a
  `SyntaxError` on 3.9.6) while the instruments run on 3.9.6. Where the tool or a ≥ 3.12 interpreter is
  out of reach the report prints a **`NOT RUN`** line naming the window it could not read, never a
  verdict for a read that did not happen.
* The corpus (14 SuiteSparse matrices) is committed and **re-hashed on every read**; a cache that has
  silently become a different dataset fails the same run.

## Layout

| path | what it is |
|---|---|
| `manuscript_source.md` | the manuscript, with citations written as KEYS (`[@arxiv:…]`, `[@doi:…]`) |
| `manuscript.md` | the manuscript as submitted — a PRODUCT of the source; its `## References` section carries the numbered, house-form list (107 entries, all cited in the body) |
| `references.json` | the record layer: one entry per cited key — the resolvable link and the stated `Difference:` clause |
| `refs_differences.json` | the one-line `Difference from this work:` statement, per key (hand-authored input to `build_refs.py`) |
| `refs_display.json` | the display layer: the author components, the year and the venue AS PRINTED |
| `refs_authors.json` | the cached Crossref author reads, which is what makes the reference build run offline |
| `reference-check.md` | the citation report, both duties: (i) every cited entry against the live record, and (ii) the journal reference gate's **whole** output (`refgate.py`, run from the repository root) |
| `figures/` | the five figures, drawn from the result artefacts by `make_figures.py` |
| `spike_*.py` + `spike_*_results.json` | the instruments and the artefacts they produce |
| `matrices/` | the pinned corpus + `SHA256SUMS` + the fetch script |
| `build_refs.py` | writes the body + `references.json`; the section belongs to `refs_render.py` (three writers, three objects) |
| `refs_build_display.py` | folds each record's author field to `Family, I.` and certifies the fold |
| `refs_render.py` | owns the `## References` section (vendored from the journal's accepted copy, its claim core's digest asserted) |
| `check_numbers.py` | re-derives the manuscript's headline numbers and matches them to their sentences |
| `check_figures.py` | every figure exists, is embedded, is cited in the prose and names its source artefact |
| `check_references.py` | reads the rendered section: numbering, block form, per-entry difference, link, two-way body coverage |
| `refscan126.py` | reference discovery + verification (arXiv/Crossref); `--report` writes the report |
| `heilmeier.md` | the pre-registration: six Heilmeier answers, adversarial checks, priors **P1-P5** (P1-P3 in the prior block, P4-P5 "written before measuring" in the headers of `spike_real3.py` / `spike_mm.py`) |
| `law.md` | the traced research spine -- every number in the paper against the artefact that produced it |
| `refs_notes.md` | how the 337-entry pool was built (the routes, and what each route cannot see) |
| `refs_pool.json` | the VERIFIED reference pool (337 entries; the paper cites 107 of them) |
| `verify_log.txt` | the verification passes, including the one that FAILED (280/330) -- kept, not tidied |
| `SHA256SUMS.reproduce` | the manifest the run compares itself against (22 artefacts) |

`manuscript.md` is generated, so the ≥100-references bar is *mechanical*: the source carries keys, and
`build_refs.py` asserts that every key resolves to a title-verified pool entry, that no citation dangles,
and that the cited count clears the bar. A bibliography cannot drift from the text it belongs to.

## Instruments

| instrument | §  | what it establishes |
|---|---|---|
| `spike_v0.py` | 4.1 | the floor exists: error falls with the limb count, then stops falling |
| `spike_v1.py` | 4.2 | the accumulator-width law `p*(eps) = ceil(log2(c/eps))`, and `c` is flat in `n` |
| `spike_v2.py` | 4.1 | two-axis composition `(p, q, K)`; the two error terms compose in quadrature |
| `spike_v3.py` | 4.1 | the floor is a property of the register, not of the reduction shape (Kahan is flat) |
| `spike_real.py` | 3.2 | the pinned real-matrix grounding arm |
| `spike_real2.py` | 5 | the κ1 exponent is regime-dependent; at fixed κ1 the constant still spreads 3.1–5.8× |
| `spike_real3.py` | 6 | the order axis: at fixed κ1, permuting the sum moves the constant 78.0× (max 209.6×) |
| `spike_learn.py`, `spike_learn2.py` | 7 | a one-constant closed form against a logistic selector and a CART |
| `spike_mm.py` | 8 | register lanes: −28…37 % at the median, but they redistribute rather than remove |
| `spike_lib.py` | 9 | `numpy`'s own dot product: the constant transfers, the textbook `gamma_n` is refuted |
| `spike_struct.py` | 10 | the library's per-case error is a lane-reduced tree, not a chain or a pairwise halving |
| `check_numbers.py` | 13 | 27 headline numbers re-derived from the artefacts and matched to their sentences |
| `check_figures.py` | 13 | the five figures: present, embedded, cited in the prose, caption names its artefact |
| `check_references.py` | 13 | the rendered section: numbering, block form, difference clause, link, two-way coverage |
| `refscan126.py` | — | the 337-entry verified reference pool and the cited-set authenticity report |

Every instrument has a `--selftest` that plants a defect in each certificate and fails if the
certificate does not fire; `reproduce.sh` runs the self-test before the measurement.

## Claim ↔ evidence

* Falsifiable claims: the eight registered hypotheses are in the issue body; §11 reports each against
  its outcome, and §12 states what the claims do not cover (dot products not tuned kernels; one library
  on one machine; one condition measure; a 14-matrix corpus chosen to span conditioning).
* Baselines: `numpy`'s dot product on the same pinned matrices (§9), and the emulator's own synthetic
  law (§4) cross-checked against the real corpus.
* Determinism: every instrument's artefact is byte-identical across runs, the figures included.

## Corpus provenance

14 SuiteSparse matrices fetched from `https://sparse.tamu.edu/MM/…` by `matrices/fetch_matrices.sh` and
pinned by two truncated digests each (`mtx_sha` of the extracted `.mtx`, `tar_sha` of the served
archive). `verify_corpus()` re-hashes all 14 on every read and the instruments refuse to run on a
mismatch.
