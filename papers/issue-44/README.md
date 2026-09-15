# Issue #44 — What Does a Verification Budget Buy? Location, Dispersion, and the Sample-Size Ceiling of Trustless Re-Execution

Evidence package. Everything a reader needs to re-derive every number in the manuscript is
in this directory.

## Reproduce

```
bash reproduce.sh
```

Expected final line, and the lines that carry the verdict:

```
criteria: a=MET, b=MET, c=MET, d=MET
cross-checks: 85 run, 0 failed
figure checks: 106 run, 0 failed   (106 on the matplotlib build the manifest pins;
                                    100 on another build, where the six PNG byte hashes
                                    are REPORTED rather than required -- the six DATA
                                    digests are required on every build)
manuscript check: 22 run, 0 failed
verdict: OK
REPRODUCE: ALL GREEN
```

Step 4 then prints the sha256 of the five artefacts this package ships, as a block to copy: a
digest quoted in a report is read off that output, never typed.

Exit status carries the verdict: 0 only if every check passes, and any disagreement names the
check that disagrees. Runtime is about 90 s for the numbers and about 30 s for the figures on
one CPU core.

**Dependencies.** The instruments are pure Python standard library — no numpy, no scipy, no
network. Only the figures need matplotlib; on a machine without it, step 1 still reproduces
every number and step 2 reports that it was skipped. `REQUIRE_FIGURES=1` makes a missing
matplotlib fatal.

## Files

| file | what it is |
|---|---|
| `instrument_v0.py` … `instrument_v4.py` | the five stage instruments, in the order the claims require |
| `canonical_runner.py` | runs the stages, then recomputes every criterion and every sensitivity statement from the stage artefacts' primitives and cross-checks each against the flag the stage recorded about itself |
| `reproduce.sh` | the one command above |
| `results_v0.json` … `results_v4.json` | the stage artefacts |
| `canonical_results.json` | the recomputed aggregate: the four registered criteria, the three sensitivity statements, and the evidence for each registered prior |
| `run.log` | the full transcript of a run, with this machine's directory scrubbed out |
| `make_figures.py` | draws the six figures from the artefacts |
| `verify_figures.py` | checks the figures: content, render, canvas |
| `verify_figures_mutations.py` | attacks the figure checker and reports which check fires |
| `figures/` | the six figures and their manifest |
| `assemble.py` | builds `manuscript.md` from its part files, resolving every printed number out of `canonical_results.json` |
| `manuscript_part1.md` … `manuscript_part3.md` | the manuscript sources — edits go here, never into `manuscript.md` |
| `check_manuscript.py` | checks the assembled manuscript against the artefact and the reference list |
| `verify_refs.py`, `verify_refs.sh`, `refs_to_verify.tsv` | re-verify every citation against Crossref / arXiv and rewrite `references.md` |
| `references.md`, `reference-check.md` | the bibliography, and the reference check: authenticity (one
row per key, with the method that resolved it) **and** coverage/ambiguity (the journal's own
`refgate.py` output, the bracket groups that are not citations, and the two counters compared
against each other) — both files generated, never hand-edited |

## The manuscript, and why it cannot drift from the data

`manuscript.md` is **generated**: never edit it. `manuscript_part1.md` … `manuscript_part3.md`
carry the prose, in which every measurement is a placeholder such as
`{{F:crit_c.median_factor|4f}}` or `{{G:counts.0|d}}`, and `assemble.py` substitutes the value out
of `canonical_results.json` (namespaces `F`, `C`, `P`, `X`) or `search_form.json` (`G`). The count is printed by
`assemble.py` on every run -- it is not quoted here, because a run can change it -- and **no
number in the body is typed by hand**, which is the only way the
prose can be guaranteed to be a view of the artefacts rather than a memory of them. An
unresolvable placeholder is a hard error, so a fact that disappears cannot silently blank a
sentence.

`check_manuscript.py` runs 22 checks, in the classes that have actually failed on this package
before:

* **recompute** — a fresh assembly, run from a *foreign* working directory, must be byte-identical
  to the committed `manuscript.md`;
* **read** — a mutation control rewrites one fact in a throwaway copy of the artefact and requires
  the rendered prose to change; without it, a placeholder whose value was typed to match the
  artefact would pass every other check here. A second control deletes a fact and requires a
  non-zero exit rather than a silent blank;
* **citations** — every cited key has an entry, every entry is cited, the count clears the
  journal's bar of 100, and every entry has a row in `reference-check.md`;
* **punctuation** — one period per separator in the compiled reference list, over **every** entry:
  a renderer that appends the separator period to a name that already ends in one prints `Wald, A..`
  and `et al..`. The list length is asserted against the cited-key count, so the denominator is the
  bibliography and not "lines that begin with a citation marker" — five body paragraphs do that too;
* **layout** — tables and figures are numbered in document order, embedded, captioned, cited in the
  running text, and every embedded file exists;
* **audit** — numbers outside a placeholder are listed for review, so a hand-typed measurement has
  to be looked at rather than trusted;
* **counts** — counts written in words are checked against sizes derived from the artefact
  (`registered priors`, `registered criteria`) and from the document's own enumerations (the
  numbered consequences of Section 1, the contributions, the captions). The audit class above
  lists only code spans carrying a decimal, so a count in words was invisible to it: this class
  was added after a review found `the four registered priors` in a study that registers three.
  Every occurrence is listed, a subset claim ("three of the four X") is listed rather than
  judged, and the scanner carries a six-case self-test so that a pattern which silently stopped
  matching is caught by the same run that depends on it.

### The bibliography is verified, not asserted

`refs_to_verify.tsv` lists one candidate per line (key, method, value); `verify_refs.sh` resolves a
DOI through `api.crossref.org/works/<doi>`, an arXiv id through the paper's own abstract page, and
a title through Crossref bibliographic search with a normalised-title acceptance test. It rewrites
`references.md` from the records that came back and `reference-check.md` with one row per key
recording the method and the record found. A key that cannot be verified is **dropped from
`references.md`**, which makes the manuscript check fail rather than let an unverifiable citation
through: of 104 candidates, 102 verified and 2 were dropped for this reason. The rendering itself is
checked too: `reference-check.md` carries the whole-list doubled-period measurement in a section
generated by the same run, so a bibliography that re-acquires `A..` is reported rather than shipped. Every one of the 102
appears in the body text — a bib entry that is never cited does not count toward the bar, and the
checker enforces that too.

### The support test: existence is not support

"Is there a real record at this locator?" and "is that record the work the sentence needs?" are
different questions, and until this revision only the first one was asked -- which is how a
102/102 coverage PASS and a full authenticity table coexisted with anchors pointing at the wrong
paper. The candidate list now carries a **declared intent** per line, and `verify_refs.py` requires
the resolved record to *be* that work:

* a `title`-method resolution must match the declared title **exactly** under order-preserving
  tokenisation (the earlier test compared token *sets* at 0.85 similarity, which is what let a
  same-words substitution through);
* a resolution whose venue or type marks it as a **secondary source** -- an encyclopedia or
  dictionary entry, a reference work, a component or dataset record -- is rejected as support
  however well its title matches; and
* the outcome is printed per key as `support OK` / `support FAIL` and counted in
  `reference-check.md`, so a key whose record is real but wrong is reported rather than accepted.

The defect the test exists for: a title search for Student's *The Probable Error of a Mean*
resolved to a 2010 SAGE encyclopedia entry bearing the same normalised words, and was accepted --
so the bibliography cited an encyclopedia article for Student's paper. That class of defect is
structural, and no reviewer should be the check that catches it.

## The construct, and what was registered

For a mean test at level `alpha`, the detection power of `k` re-executions against a node
whose divergence shifts the mean by `delta_D` with dispersion `sigma_D` is

    power = Phi(u),    u = ( sqrt(k) * delta_D - c_alpha ) / sigma_D,    c_alpha = 1.6449

so exactly two numbers — the node's own mean and sd — fix its detectability. The registered
success criteria and their recomputed outcomes from the committed primitives:

| | registered criterion | outcome |
|---|---|---|
| (a) | held-out median absolute prediction error at most 10 pp | **MET** — 31 cells, median 0.00092 |
| (b) | insensitivity region non-empty, boundary within ±20 % of the predicted band width | **MET** — worst refined width error 0.0086, edge 0.0628, slope 1.02e-4 against a 0.01 cut |
| (c) | derived rule better than the best constant threshold matched to zero honest rejections | **MET** — 41 of 42 informative cells, sign test p 9.8e-12, median factor 1.0897; the stricter per-cell reading is reported UNMET with its 17 cells |
| (d) | at least 3 disjoint streams per cell, mean ± sd, intervals on the key contrasts | **MET** — 41 streams per cell in the two deciding stages, per-stream arrays committed |

Registered priors P1, P2 and P3 are each **CONFIRMED**, and `canonical_results.json` carries
the recomputed evidence for each rather than the verdict alone.

## Sensitivity

* **S1 — the construct's limit is a lattice, not a rate of convergence.** For a two-point node
  the sample mean lives on a lattice of spacing `big/k`, so the controlling quantity is
  `big/(sigma*sqrt(k))`. Every measured cell with that ratio at most 0.25 is within 1
  percentage point (worst 0.0017); the error is **not monotone in k** (sign changes 4/2/5/1).
  A Gaussian control is exact at every budget (worst 0.0013, 241× tighter).
* **S2 — the ceiling bounds the prize, not the detection.** The difference never exceeds its
  `1 - p_c` bound; the maximum achievable gain is **0.00098** in the saturated cells against
  **0.9148** outside them. The intervals in those cells still exclude zero, so the ceiling's
  cost is that the prize becomes a fraction of a percentage point.
* **S3 — where the comparison is decidable at all.** Inverting each cell's interval: 25 of 42
  informative cells are decidable at the 41 streams the study ran, 17 are not and 1 never;
  `N_min` has median 30 and range 11–1854, and is set by the effect size, not the budget.

## Determinism

`canonical_results.json` and `run.log` are byte-identical across runs and across working
directories, and contain no wall-clock, no host name and no absolute path. The five stage
artefacts are byte-identical too, and their digests are recorded in the aggregate:

    v0  9cc6160f3d452a4179a30f57a2384f701e3b267399c1620689df37c8b45eeb5b
    v1  eec995d92db43f75476dddbc2501980ad7b21644a8afdcb8e4f2586cc3110a40
    v2  db7b0834d7a238c06a106ef150f59707b1a10486d3680fa21b60efa81fe98157
    v3  edccf0f49c320128a3ee2322373d03a8a4b341f2a8323967b5f8504fc16cca42
    v4  0671ebedc46e277bf1552adc3c2519afce15b669a97b1b64988384c0d91fb842

The **PNGs are a different matter**: their bytes depend on the matplotlib build. Each
figure's manifest entry therefore records the build that produced it and pins the **data** —
a digest over both the declared arrays and the numbers read back off the drawn artists — and
over every artefact the figure read. Reproduce on another build and the data digests must
still match exactly; the pixel hashes are then reported rather than required.

## What the figure checks cover, and one stated blind spot

`verify_figures.py` checks, per figure: that a fresh run produces the same manifest (data and
source digests), that the committed PNG matches its entry, that ink is present and on both
halves, that every label a caption promises is actually drawn, and that every positioned
element falls inside the rendered canvas.

**Blind spot, stated rather than left implicit.** matplotlib renders any string containing
mathtext as glyph outlines, so those labels — and the plain text sharing their string — are
invisible to a text search. `MATHTEXT_LABELS` in `verify_figures.py` lists them, and for those
the canvas check is what covers them, because they are drawn as positioned groups.

`verify_figures_mutations.py` is the control on that checker: one defect at a time, and it
reports which check fires. M1–M6 and M8 fire; M7 is a clean control (a different matplotlib
build must be reported, not failed); P1–P5 call the checker's own functions on inputs that
violate exactly one property.

## Data

No external data. The study is a controlled synthetic family with ground truth by
construction, plus one calibration cell pinned to the rates reported by the antecedent
(arXiv 2609.10601) and reported as a residual at the false-positive floor. The research
workspace with the round-by-round notes is git-ignored by design; this directory is the
committed evidence.
