# R419 — round 3 of 3 on issue #87: the run's own reading

The editorial re-check of 2026-09-22T01:12Z closed R444's four required changes and left **one** defect:

> (D) the run has three build-bound steps but declares one, and the declared one is last, so a reader on
> another build stops at step 1/5 and never sees the `BUILD_BOUND` reading the revision built.

This round discharges it, and the repairs are stated here because two of them were found *by* discharging it.

## 1. The repair, at the object

`reproduce.sh` was rewritten around **one numbering basis** and an ordering that is a property of the reading,
not a layout choice:

| step | what it writes | its reading | on a build other than the pinned one |
|------|----------------|-------------|--------------------------------------|
| 1/5 | — (the two instruments' controls) | REPORTED: build read, build pinned, cells, worst relative departure, verdict, plus both `--selftest`s | `BITWISE` or `BUILD_BOUND`; the run continues |
| 2/5 | `artefacts/results_digest.json` | REPORTED, leaf by leaf, with the worst departure at its leaf's own path | `BUILD_BOUND` within `1e-8`; the committed copy is then restored and the run continues |
| 3/5 | `figures/*.png` | RENDERED: the bytes against the saved copy, with the renderer named | `RENDER_BOUND` — reported, **never** a stop condition; `NOT RUN` (not a pass) when the interpreter has no matplotlib |
| 4/5 | `manuscript.md`, the assembly report | EXACT (`cmp`) | exact — the stop condition |
| 5/5 | — (the journal's gates) | EXACT (`GATE: PASS`) | exact |

The under-count is repaired by *declaring the three* in the preamble and by the ordering: every build-bound
step precedes every stop condition, so a reader on another build sees what is happening before anything can
stop them. `artefacts/assembly/build_bound.py` (new) is the comparator, and its three verdicts are
**measured**, not asserted: unperturbed → `BITWISE` exit 0; a 1-ULP plant → `BUILD_BOUND` exit 0; a 1e-5 plant
and a structural plant → `FAIL` exit 1. A zero test is relative to the value's own scale
(`abs(d) <= REL_TOL * max(|a|,|b|)`), which is what makes an analytically-zero quantity a reading rather than a
defect.

## 2. The defect the repair exposed in its own checker

`counts_check.py` printed `-- not present --` for a declared phrasing that matched nothing, and counted only
hits — so when this round's rewrite of `reproduce.sh` **deleted** the phrase `76 quantities read out` from that
carrier, the checker went on printing `COUNTS: PASS`. **A count can be lost, not only contradicted.** Two
repairs: the rows are now two-sided (`required` — zero matches is a failure of the carrier; `absent-design` —
with the reason written beside it), the report prints each row's expectation and reach, and the verdict is taken
from the rows, not from the number of hits. One row is `absent-design`: the manuscript states no count of its
own apparatus, and a count added to the paper to feed a checker would be a claim in service of the apparatus.

The checker now carries its own battery — `counts_check.py --selftest` → **9 cases, 9 caught**, on scratch
copies: a contradicted count, a count **removed** from a carrier, a re-worded count, a changed header, a changed
owner, an absent carrier, a stale copy in a phrasing the list had missed, and the absent-by-design row starting
to state a wrong count. Two stale copies this round's reading found and corrected: the digest described as 55
quantities (the owner prints 76) and a manuscript line count that had drifted; the phrasing that hid the first
one was added to the list, so the copy no one edits is not the copy no check can see.

## 3. The reading, on a foreign build

Same package, same head, `PY=~/.asdf/installs/python/3.14.6/bin/python3` (Python 3.14.6 / numpy 2.5.1) against
the pinned Python 3.9.6 / numpy 2.0.2:

* 1/5: `build read: python 3.14.6 / numpy 2.5.1`, both controls `BITWISE`;
* 2/5: **`BUILD_BOUND`** — 1 leaf differs, worst absolute `1.110e-16`, worst relative `1.610e-16` at
  `quantities.panel.q8_over_q6_ratio_of_the_mid_band.value.mean` — **and the run continues**;
* 3/5: `NOT RUN` (no matplotlib there; the step says so rather than implying a pass);
* 4/5 and 5/5: `byte-identical`, `GATE: PASS`;
* exit **0**, `REPRODUCE: ALL GREEN`.

This is exactly the reading the previous revision could not deliver: with the digest compared by `cmp` in the
old 1/5, a foreign-build reader stopped before the `BUILD_BOUND` line existed at all.

## 4. The verifier, and what it caught in itself

`artefacts/assembly/verify_revision_round3.py` — **renamed in the follow-up round to `verify_revision_round2_followup.py`**, because the journal's clock counts editor decisions and this turn is the round-2 decision's follow-up, not a round — reads each property of the repair at its object (10 checks, all
green) and is its own battery (9 plants, 9 caught). Its four self-caught defects are worth recording, because
every one is a rule this project has already written down and broken again:

1. Splitting the step bodies on a bare `=== ` put the run's **preamble** in the list, shifting every body by
   one; the check then read step 5's body as step 4's. Split on the numbered header.
2. Classifying a step by keywords in its body misread step 4/5 as build-bound (its body runs the counts
   checker's battery). The classification now reads **two** objects — what the header declares and what the body
   calls — and requires them to agree, which is the under-declaration defect itself.
3. A prose probe read the **source**, and the sentence it looked for wrapped between `Python` and
   `3.9.6 / numpy 2.0.2`; the check went red on a sentence that was present. Prose probes read the flattened
   text (R415's lesson, relearned).
4. A plant used `str.replace(..., 0)` — which replaces **nothing** — so the case was scored against an
   unmutated package and read as "the check missed it". The plant helper now asserts the text changed, and the
   probe was narrowed from "the file names the foreign build somewhere" to "the paragraph that makes the claim
   names both builds, the verdict, the worst departure and the exit code": the whole-text probe was satisfied
   by a quoted instrument line elsewhere, which is how an inert plant stays invisible.

## 5. Baseline held

`REPRODUCE: ALL GREEN` on both builds: digest `BITWISE` (76 quantities, no leaf differs on the pinned build),
three figures byte-identical, assembly `coverage 169/169, 0 stray, 133 bindings`, CHECK 4 numbering clean,
counts checker 10 rows / 9 firing + battery 9/9, gates 41/41 · 12/12 · 17/17 · `POINTGATE SELFTEST: PASS`,
refgate `entries 169, 0 not separated, coverage 100.0%, GATE: PASS`. A run leaves the tree as it found it.
