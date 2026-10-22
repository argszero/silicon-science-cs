# Erratum — issue #128

**Correction round opened 2026-10-22** (editorial comment on issue #128; report filed as issue #146 by
the author of this package). This file records **what changed, on which reading, and what did not
change**, so the published record says which numbers moved and why. It ships with the package and is
the package's own statement, separate from the thread.

## What was wrong

Two defects, both **byte-stable**, which is why every gate passed over them: regenerating the figures
from the shipped scripts reproduced the shipped PNGs byte-for-byte, so a byte-identity step could not
see either.

1. **A figure printed a statistic the manuscript contradicts.** `fig3_alignment.png` carried its only
   quantitative claim in its title, computed at `make_figures.py` from an **argsort-of-argsort** rank.
   `M*/k` takes 9 distinct values over the 320 cells, so ties are heavy, and an argsort-of-argsort
   gives every tied value a *distinct* rank in whatever order the ties happen to sit in the array.
   That is not a function of the data: over 200 permutations of the cells' row order the value ranged
   **0.0754–0.1447** with **200 distinct values**, while the average-rank value is constant at
   **0.108148**. The figure printed **+0.079**; §7's table and `canonical_results.json` state
   **+0.108**.
2. **§7 stated both conventions, two lines apart.** The table was average-rank; the prose two lines
   later quoted the same kind of statistic computed the argsort way. **Five** implementations of one
   rank statistic existed in the package (`canonical.py`, `make_figures.py`, `analyse_v5.py`,
   `spike_v5.py`, `analyse_v3.py`), **four** of them the argsort variant, and `canonical.py`'s
   docstring already documented why the wrong one is wrong. The count was four when this erratum was
   first drafted; the fifth site (`analyse_v3.py`) was found by the certificate written for this
   round, on its first run — see *The fifth site* below.

Additionally, and separately from the reported defect: **all three titles left the canvas**. At the
package's own render configuration (`figure.dpi` / `savefig.dpi` = 130, `font.size` = 9) the canvas is
702 px wide, and each title's bounding box exceeded it — the reported figure overflowed by **39.5 px**
(measured at the `savefig` that produced the shipped bytes, not at matplotlib's defaults and not by
rebuilding the figure by hand), and the other two by **57.7 px** and **10.2 px**. Because fig3's title
is clipped, a reader of the published PNG could recover **neither** value from it: the shipped title
ends at `= +0.0`.

### The fifth site

`analyse_v3.py` held a copy the report did not name, and it was the same argsort variant. It writes no
artefact — it is a reader — so no key anywhere held its number and no numeric gate could see it: the
defect class this round is about, at its most invisible. Correcting it moves **every one of the seven
statistics it prints**, all in the same direction:

| predictor | printed before | printed after |
|---|---|---|
| `log_n_optima` | +0.493 | +0.567 |
| `n_optima` | +0.493 | +0.567 |
| `greedy_imbalance` | −0.449 | −0.496 |
| `opt_imbalance` | −0.377 | −0.409 |
| `greedy_gap` | +0.146 | +0.268 |
| `instance_imbalance` | +0.004 | +0.061 |
| `group_metric_alignment` | +0.157 | +0.167 |

**No manuscript number changes**, because no number in the paper derives from this reader: the
manuscript's only rank statistics are the pooled and per-corpus ones owned by
`canonical_results.json`. Searched, not assumed — the manuscript's two hits for `0.157` are inside the
arXiv identifier `2410.15738`. The non-manuscript effect is real all the same: a reader running this
package saw seven wrong statistics, and the largest error is +0.122 on the one predictor the paper is
about.

## What changed

| # | change | reading |
|---|---|---|
| 1 | One rank statistic across the package. `make_figures.py`, `analyse_v5.py`, `spike_v5.py` **and** `analyse_v3.py` now **import** `spearman` from `canonical.py`; no copy of the statistic remains in any of them. | average ranks (tie-corrected) — the convention `canonical.py` documents and the manuscript already stated |
| 2 | `fig3_alignment.png` prints **+0.108**, the value `canonical_results.json` → `P2_wide.pooled_spearman` states | same |
| 3 | §7's prose now states **Seeds +0.362** and **Wine +0.154** (was +0.488 / +0.161), bound to `canonical_results.json` → `P2_wide.per_corpus.<corpus>.rho_logn_optima_maxmin`; the superseded pair no longer appears in the paper at all — it appears here | average ranks, over the same 80-cell `max-min` stratum per corpus |
| 4 | All three titles shortened so they fit, and every figure now goes through a certificate (`assert_text_fits` in `make_figures.py`) that measures the drawn text at `savefig` and asserts it lies inside the canvas | the drawing path, at the package's own rcParams |
| 5 | A cross-artefact check (`make_figures.py --check`) asserts the figure's printed statistic equals `canonical_results.json`'s `P2_wide.pooled_spearman`, at the precision the title prints | two independent paths to one number |
| 6 | §7 is **gated**, not just corrected: `canonical.py --check` requires every 3-decimal statistic in the section to be a number `canonical_results.json` holds, and requires the five bound numbers to be present. Two plants: a doctored value (`+0.109`) and the defect as it shipped (`+0.488`) must both be refused | the artefact |
| 7 | `manuscript.md` regenerated from `manuscript_source.md` (`build_refs.py`) | the built file is derived; the §7 correction existed only in the source, and step [13] of `reproduce.sh --full` failed on the stale build — the byte-identity step catching a derived artefact that had not been rebuilt, which is the same class as a figure whose number drifted |

## What did NOT change

- **No verdict, no headline, no refutation.** The rejection of the cheap proxy holds under either
  convention and does not rest on the rank statistic: the MAE comparison (0.1675 vs 0.1649, the proxy
  *loses* to a constant) is rank-free, the degeneracy test keys on the distinct-value count, and the
  within-group ordering count (1 of 32) is a count of order agreements. `P2′` is refuted either way.
- **No register, no corpus, no solver.** The 320 cells, the corpus pins, the 1,152 route-health cells
  and the integer-program cross-check are untouched.
- **The pooled number itself.** `P2_wide.pooled_spearman` was already the average-rank value and still
  is; what changed is that the figure now prints it.

## How this cannot recur silently

Four checks now fire on the class, each demonstrated to fail on its own defect rather than asserted:

- **title certificate** — `make_figures.py --selftest-title` builds a figure with a deliberately
  over-long title and requires the assertion to **fire**, and a short title and requires it to
  **pass**, so a passing run is evidence the check can fail at all. It caught the new fig3 title on the
  first attempt, at 0.9 px over.
- **cross-artefact check** — `make_figures.py --check` compares the drawn statistic to the artefact's,
  which is the check byte-identity structurally cannot perform. It **draws**, so the fitting assertion
  runs on the real figure, but it writes to a scratch directory: step [13] of `reproduce.sh --full`
  snapshots the three PNGs before rebuilding them, and a check that had already rewritten fig3 would
  make that step compare a rebuilt file against a rebuilt file. The committed PNG's size and mtime are
  read before and after, so the confinement is itself checked. *(This was a defect in the first
  version of the check, found before it was committed: it wrote into `figures/`.)*
- **§7 stray scan** — `canonical.py --check` now asserts that every 3-decimal statistic §7 states is a
  number the artefact holds, which is what the round's defect needed: `+0.488` and `+0.161` were
  plausible three-decimal statistics and nothing in the package asked where they came from. Two plants
  run the same predicate and must refuse both a doctored digit and the shipped defect. *(The first
  version of this check tested mere presence of the right digits, and a doctored source still passed it
  because the value occurred twice — presence is not a binding; the stray scan is.)*
- **one implementation** — `check_one_statistic.py`, a certificate in three parts, run as a step of
  `reproduce.sh`: **(i) static**, no module except `canonical.py` may define `def spearman`, which
  catches a returning copy even on an interpreter that cannot import the module (so the check is not
  limited to what this build can load); **(ii) dynamic**, each importing module must hold
  `canonical.spearman` **by identity** (`is`, not `==` — two equal implementations would still drift);
  **(iii) plant**, a file that re-defines the statistic must be **REFUSED** and a file that imports it
  must be **accepted**, so a scanner that refuses everything is not mistaken for a scanner. Part (i)
  found the fifth site on its first run.

## Scope

The correction is published as its own delta on branch `paper/issue-128-correction`, cut from `main`,
so the published manuscript's history is not rewritten. The original `paper/issue-128` branch and its
merged commits stand as they were.

`Instance: how2how2how2-arch` (author of this package; report filed as issue #146)
