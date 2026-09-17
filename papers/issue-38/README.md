# Issue #38 - reproduction package

**When Do Agent Markets Beat Planners? A Boundary Law for Decentralised Allocation under
Misestimated Costs and Bounded Central Attention**

Contribution level: **theory + empirics**.

This directory is the committed artefact set for issue #38: the allocation model, the canonical
runner (the single source of every number in `manuscript.md`), the artefact it produces, the
figure generator and the figures, a 97-check validation suite, a self-audit of that suite, and the
citation-authenticity report.

## One-command reproduction

    working directory:  papers/issue-38        (the package root - run it from there)
    command:            bash reproduce.sh

Expected output (tail):

    VALIDATE 97/97
    artefact sha256: 4935c409ecec4fda70f4b5f573a879eded4fd6055623e16ba4439c799fbb4807
    RESULT: PASS

Full artefact digest:

    4935c409ecec4fda70f4b5f573a879eded4fd6055623e16ba4439c799fbb4807

**Tolerance: exact, not statistical.** `validate.py` must print `VALIDATE 97/97`; each of its 97
conditions is attached to a specific headline number of the manuscript (the reductions, the
behavioural anchors, the §4.1 series counts, the §4.2 out-of-sample table, the §4.3 closure table,
the §4.4 attention-model test, the §4.5 mechanism rates, the §4.6 ablation). Every quantity is a
deterministic function of the seed scheme, so there is no tolerance band to choose. A single failed
condition fails the run.

**Files this run rewrites, deliberately:** `canonical_results.json`, `run.log`, `figures/*.png`,
`figures/manifest.json`. Nothing compares any of those against a stored copy, so **the command is
re-entrant** - it prints `RESULT: PASS` on the first run and on every run after it over the same
checkout (verified twice in a row; the digest above was identical on both). Figure digests are
checked against `figures/manifest.json`, which is regenerated in the same run, so figure bytes may
legitimately differ across matplotlib builds without failing.

**Measured wall-clock** (Apple silicon, CPU-only, measured by the script itself): **~180 s**
(canonical runner ~175 s, figures < 1 s, validation < 1 s). Machine-dependent; not part of any claim.

### Environment

The pipeline needs **numpy**, **scipy** and **matplotlib**. `scipy.optimize.linear_sum_assignment`
(`alloc_model.py`) computes the exact oracle that every reduction is measured against, so scipy is a
hard dependency of the recompute path and not an optional extra. The interpreter first on `PATH` need
not be the one that has them, so `reproduce.sh` probes for an interpreter that can actually import
**all three** and reports an explicit `RESULT: FAIL` if none exists, rather than silently substituting
one — the probe imports every dependency precisely so that a machine missing one gets that message
instead of an uncaught `ModuleNotFoundError` raised from inside the runner:

    bash reproduce.sh              # auto-selects; prints the interpreter and matplotlib version it used
    PY=/usr/bin/python3 bash reproduce.sh   # override

Verified here with `/usr/bin/python3` (numpy 2.0.2, scipy 1.13.1, matplotlib 3.9.4); the editor's
independent triage run used CPython 3.14.6 with numpy 2.5.1, scipy 1.18.1, matplotlib 3.11.1 and
reproduced the same artefact digest.

## What is in the package

| file | what it is |
|---|---|
| `manuscript.md` | the paper (abstract, model, registered priors, results, related work, threats) |
| `reference-check.md` | citation-authenticity report: 125/125 entries resolved, one line per entry |
| `references.json` / `refs_selected.json` | the verified bibliography and the curated selection it was built from |
| `refs_tool.py` | the bibliography tool (`harvest` / `verify`); re-runnable |
| `refs_display.json` | per-entry display metadata (authors, year, venue) + the transport each came from; built by `refs_build_display.py` |
| `refs_build_display.py` | builds `refs_display.json` from the harvest, with the five gap entries resolved individually and named |
| `refs_render.py` | renders the manuscript's `## References` section from the two data files; `--check` verifies the committed section against a fresh render **and reads two properties on that section** (no ALL-CAPS author component survives; no escaped character reference survives), each with the count from the records printed beside it; `reproduce.sh` runs that check |
| `refs_verify.log` | the verification run log (including the recorded API outage) |
| `verify_correction_r1.py` | the round-1 correction checker: one check per required change (R1-R4), each two-sided (it must fail on a mutated copy). `python3 verify_correction_r1.py` prints the verdict and writes `correction_r1_verify.log` beside the package; exit status follows the verdict |
| `verify_correction_r2.py` | the round-2 correction checker: one check per required change (items 1-5), each two-sided, with the layout read taken by the journal's own gate (`block form:`) and by **GitHub's own renderer** -- the two instruments the decision names -- plus the local read, each of which must fail on a collapsed copy |
| `verify_correction_r3.py` | the round-3 correction checker: the required change (the author component's case fold) and the second instance of the same test one entry's text carried (a registry escape). Every reading is taken on the artefact and every control is **derived inside the checker** -- the section is re-rendered with the fold removed and with the decode removed by monkeypatching `refs_render` by name, and the shipped `--check` is run on a mutated copy -- so no control is a typed anchor that can go stale. `python3 verify_correction_r3.py` prints the verdict and writes `correction_r3_verify.log` beside the package |
| `alloc_model.py` | the allocation model: instances, oracle, planner, market |
| `canonical_runner.py` | the canonical runner - every number in the manuscript is read out of its artefact |
| `canonical_results.json` | the artefact (reductions, anchors, law grid, out-of-sample race, closure, mechanism, ablation) |
| `run.log` | the runner's own summary of the configuration and the headline results |
| `make_figures.py`, `figures/` | the three figures and their manifest |
| `validate.py` | the 97-check validation suite (`VALIDATE 97/97`) |
| `check_audit.py` | self-audit of `validate.py`: 32 mutations, all of which must be caught |
| `reproduce.sh` | the one command above |

## Reference style — how the bibliography is rendered

The manuscript's `## References` section is **generated**, not typed:

    python3 refs_render.py            # rewrite the section in manuscript.md
    python3 refs_render.py --check    # exit non-zero if the committed section differs

from `references.json` (title, link, and the per-entry *stated difference*) and `refs_display.json`
(authors, year, venue, and the transport each was read from; built by `refs_build_display.py`).
**One style is applied to all 125 entries** — the house style stated at `README.md` (the journal's)
→ *Presentation requirements* → *Formal References section*:

    [N] <Authors> (<Year>). <Title>. <Venue or identifier>. <resolvable URL>
        Difference: <the one-line stated difference that closes the entry>

- Authors are `Family, I.`, joined with `; `; **four or more are abbreviated to the first three and
  `et al.`** (one period). A record that states an author in capitals is **folded the way its title is**
  (`[15]`, `[20]`); a mixed-case author field prints as the record states it.
- The record's **text** prints the record's name: a character reference the registry ships inside its
  metadata (`O&#39;Brien`) is decoded before it reaches the page, so the entry reads `O'Brien` in the
  document's text and not only in the rendered paragraph.
- The year is in **parentheses** after the author block; it is the source's publication year, and for
  an arXiv preprint with no stated publication date the **arXiv submission year**, read from the
  abstract page. The literal placeholders `n.d.` and `None.` are never emitted.
- The title is in **title case**: an all-caps record title is folded (`[10]`, `[15]`), and a title the
  publisher wrote in mixed case is printed as the record states it.
- Venue is the container title from Crossref, or `arXiv preprint arXiv:<id>`.
- The link is the entry's own identifier URL (arXiv abstract page or DOI), never a bare identifier and
  never inside backticks.
- The **stated difference** is printed on its own indented line and closes the entry.
  `references.json` has carried one for all 125 entries since the submission; it was simply never
  rendered before.
- **Entries are separated by a blank line.** Each entry begins on a line of its own *and* a blank line
  follows it, because consecutive entry lines are **one paragraph** to every CommonMark renderer: with
  no blank line between them the entry boundaries vanish on the page and one entry's trailing URL is
  read as part of the next entry's sentence. Measured on the published head (`refgate.py`'s
  `block form:` line, and GitHub's own renderer): **124 of 125 not separated, 2 paragraphs**. Now:
  **0 of 125 not separated, 125 paragraphs**.

**Two deliberate exceptions to the 100-column wrap: image lines are not wrapped** (a markdown image
must stay on one physical line to render at all) **and table rows are not wrapped.**

**One entry, [51], carries no author, and the entry says so by naming the records that were read**
rather than guessing at one: it prints *`Author not established on Crossref/OpenAlex for this DOI`*,
and `reference-check.md` carries the same line with what each registry returned — Crossref's record for
the DOI has **no `author` field at all**, OpenAlex's has an **empty `authorships` list**, and both
return the same work (*Selective Attention*, The Psychology of Attention, 1997; the publisher's landing
page answers HTTP 403 to automated access and Semantic Scholar answers 404 for the DOI). Naming the
registry is the point: the exception is a claim about a record, so a reviewer can check it against the
registry the entry names. The four other entries whose bulk source also carried no author (**7, 9, 14,
38**) were resolved against a named alternative record — OpenAlex, or the DOI landing page's
`citation_author` metadata — and each entry's `via` field records which.

## Headline results (all read out of `canonical_results.json`)

| result | value |
|---|---|
| model reductions exact (attention `m=N` is the optimum; `sigma=0` market is the optimum) | **270/270** |
| registered **P1** (boundary moves toward the planner as the pool grows) | **REFUTED** - `sigma*` endpoint rises in 50/50 series, falls in 0, 173/190 steps non-negative (17 local dips) |
| registered **P2** (a parameter-free constant) | **UNMET** - the constant moves with the cost scale (median rel. error 20.8 %) |
| registered **P3** (the advantage is specialisation) | **REFUTED** - with the channel off (`beta=0`) the boundary still exists (`sigma*` = 0.410/0.570/0.739 at `N` = 16/64/256) |
| boundary law | `sigma* ~= A * p`, `A` median **2.734**, range [1.612, 13.570] |
| fit, in sample | exponent **1.0358**, R^2 **0.9176**, n = 240 (report, do not trust: see below) |
| **out-of-sample race** (240 train / 120 held-out cells) | gamma-aware proportional **18.4 %** median, trivial proportional **27.0 %**, fitted power law **28.5 %**, constant **57.6 %** |
| exponent refit on held-out cells | **0.9773** (drift -0.0585) => the exponent is 1 |
| how much the constant moves with the cost scale | 2.904 / 2.686 / 2.548 / 2.388 at gamma = 0.25 / 0.5 / 1.0 / 2.0 |
| how much it moves with the cost distribution | < 3 % (uniform 2.446, lognormal 2.496, Beta 2.423) |
| the two "physical" scales, scored out of sample | assignment gap **98.4 %** median (2546 % max), cost spread **153.9 %** -> both ruled out |
| attention-model independence | 12 never-fitted fraction-reading cells predicted at **12.4 %** median (budget-cell constant) |
| mechanism | **scrambling** - Hamming fraction 0.138 -> 0.662 over `N` = 16 -> 256; wrong-block rate **exactly 0** for `beta >= 1`, `sigma <= 0.2` |
| ablation | boundary survives with specialisation off; amplification a roughly constant **x4** (3.93/4.12/3.94); at `sigma=0` the market is **exactly** the oracle |

**Read the fit row with the race row, not without it.** An in-sample R^2 of 0.92 with ~30 % residual
scatter is not evidence of a power law; the power law *loses* to a one-parameter proportional law on
cells it has never seen. That comparison is the reason the manuscript claims a proportionality.

## Suite self-audit

    python3 check_audit.py

applies 32 mutations to throwaway copies of the package (artefact fields, the manifest, a deleted
figure, the A-breakdowns, the exponent table, the ablation numbers, the mechanism series, the
block-count block, and - batch 3 - the manuscript's own prose) and requires every one to be caught by
at least one `[FAIL]` with a non-zero exit. Each mutator asserts that it actually changed the file,
and the sandbox manifest digest is refreshed first so that the digest check cannot be the reason a
semantic mutation is caught. Current result: **32/32 caught**, with a clean run at **97/97**.

Batch 3 exists because of the defect this revision fixes. `validate.py` originally asserted
properties of the *artefact* only: it compared the three distribution constants to each other, never
to the numbers the manuscript prints. A value could therefore be correct in the artefact and wrong in
the manuscript, which is what happened - the abstract carried `2.616` where the artefact's uniform
median is `2.446` (2.616 is `exp(oos.gamma_exponent.intercept)`, the gamma-aware prefactor, a
different quantity). The suite now reads `manuscript.md` and binds every number the abstract quotes,
and the block-count and amplification numbers in the body, to the artefact field they come from;
reverting the abstract to `2.616` fails `m1` and `m2`.

## Revision note (round 1)

The revision adds one artefact block (`closure.block_count`) and **changes nothing that was already
there**: of the artefact's 178 pre-existing leaf fields, 0 changed and 0 were removed, against 33
added. All pre-existing checks still pass; the digest changed only because the file gained a block.

## Correction note (round 1)

A post-publication `correction` round, for defects in the manuscript **as a document**; **no number,
claim, conclusion or table value changes**. `canonical_results.json` is untouched, so the artefact
digest printed by `reproduce.sh` is the same as at publication.

- **R1 — the figures are shown in the text.** All three figures are embedded where their claim is
  made, with a number cited from the body: Figure 1 (§4.2), Figure 2 (§4.5), Figure 3 (§4.6).
  Previously the files were committed and their digests recorded, but the manuscript embedded
  nothing (`![` occurred zero times and no numbered figure was ever referred to); §8 now points at
  the figures the body shows instead of introducing them in a bullet list.
- **R2 — every table is captioned and cited.** All nine tables carry a `**Table N — …**` caption
  above them, are numbered in document order, and are referred to from the body where their numbers
  are used. One table already had a caption numbered `Table 2` while standing fourth in the
  document; the captions are now in document order and the in-text reference follows.
- **R3 — the bibliography is a readable list.** All 125 entries now carry authors, a year, the
  title, the venue or identifier, the link, and the entry's stated difference; see *Reference style*
  above for the style and `refs_render.py` for the renderer. The machine-export placeholders
  (`n.d.`, `None.`, the doubled `n.d..`) are gone: measured on the pre-correction file, 107 of 125
  entries stated no year in any form and none named an author.
- **R4 — one multiplication mark.** The lowercase `x` used as a multiplication sign is now `×`
  throughout (10 occurrences in prose, including `~×3.4` and the grid description). The ASCII
  parameter names (`sigma`, `beta`, `gamma`) are unchanged, and unicode `x` inside identifiers
  (DOIs, arXiv ids, ordinary words) is untouched.

Line-wrapping was normalised to 100 columns for the prose; tables and image lines are deliberately
not wrapped, for the reason given under *Reference style*.

## Correction note (round 2)

Required changes **1-5** of the round-2 editorial decision, all of them properties of what the
reference list **prints**. As in round 1, **no number, claim, conclusion or table value changes**, and
`canonical_results.json` is untouched.

- **1 — the list renders as entries.** Each entry now begins on a line of its own *and* is separated
  from the entry above by a blank line, so the section renders as 125 entries and not as two blocks.
  Round 1 put each entry on its own line and stopped there, which is not enough: consecutive entry
  lines are one paragraph to CommonMark. Acceptance read: `refgate.py`'s `block form:` line returns
  **0 of 125 not separated** (was `124`), and GitHub's own renderer returns **125** `<p>` for the 125
  entries against a known-present control returning **1**. Both readings are taken by
  `verify_correction_r2.py`, each with the control that must fail.
- **2 — the heading.** `## 9. References` → **`## References`**: the section number is a fifth form no
  other published list uses. The body's one cross-reference (`Reference numbers follow §9.`) followed
  it and now reads *Reference numbers follow the reference list.*
- **3 — titles in title case.** `[10]` and `[15]` printed the record's capitals; the two titles are now
  folded (`Counterspeculation, Auctions, and Competitive Sealed Tenders`; `College Admissions and the
  Stability of Marriage`), and no all-caps title survives in the list.
- **4 — entry [51].** The entry names the records it read
  (*`Author not established on Crossref/OpenAlex for this DOI`*) instead of *"the record"*, its year
  prints in parentheses (`[1997]` → `(1997)`), and `reference-check.md` carries the same line **with
  what each registry returned** (Crossref: no `author` field; OpenAlex: empty `authorships` list),
  read 2026-09-17. The section note that used to repeat this is gone: the exception rule asks the
  **entry** to carry the statement, and with the note removed the section is exactly 125 entries.
- **5 — one order for the whole list.** Verified entry by entry: authors (`Family, I.`; four or more →
  first three and `et al.`), the year in parentheses, the title in title case, the venue or identifier,
  the link as a resolvable URL, and the entry closing with its `Difference: …`. No backticked
  identifier and no doubled `et al..` survives.

**What this round had to fix in the package, not only in the document.** The renderer's own check
(`refs_render.py --check`) was **run by nothing** — the bibliography is generated, and the command the
package asks a reader to run could not see the generated form at all. It is now a step of
`reproduce.sh`, and the round's five checks are carried by `verify_correction_r2.py`, whose every check
is two-sided.

## Correction note (round 3)

The round-3 decision has **one required change**; the read it asks for found a **second instance of the
same test**, and both are recorded here.

- **The required change — the author component's case.** `refs_render.py` now applies to an author
  component the fold it already applied to the title: a record that states an author in capitals prints
  as `Family, I.` (`[15]` `GALE, D.; SHAPLEY, L.` → `Gale, D.; Shapley, L.`; `[20]` `SMITH, R. G.` →
  `Smith, R. G.`), and a mixed-case author field prints as the record states it. `[15]`'s capitals were
  the round-2 title fold's own leftovers: that fold had one side. The list is **regenerated by the
  renderer**, so nothing is hand-edited. Acceptance read: `refs_render.py --check` prints
  `author case: 0 ALL-CAPS author component(s) over 125 entries`, and re-running the renderer without
  the fold turns exactly those **2** entries red. The fold is the title's fold **minus its small-word
  rule**, because over an author that rule lowercases an initial (`SMITH, A. B.` → `Smith, a. B.`),
  which no author component may lose.
- **The same test's second instance — one entry's text carried an escape for a name.** `[95]` printed
  `O&#39;Brien, L.`, because the arXiv `citation_author` metadata ships `&#39;` where the name has an
  apostrophe. **Measured: GitHub's own renderer returns `<p>X O'Brien</p>` for the escaped and for the
  decoded form alike**, so the rendered page was never wrong — the **text** was, and the text is the
  object the journal's gate, a grep and a diff read. The record files keep what the registry returned;
  the renderer decodes. Acceptance read: `record text: 0 escaped character reference(s) over 125
  entries`, with the page reading taken by GitHub's own renderer so the sentence above is a measurement
  rather than a judgement call.

**What the round had to fix in the package, not only in the document.** The correction lives in the
renderer, so the rule has to be readable where the artefact is: `--check` reads both properties **on the
section** — the object the reader's page and the journal's gate read — and not on the renderer's
behaviour, because a section regenerated by a renderer that lost the fold agrees with that renderer, and
the section-versus-render comparison cannot see it. Two counts are printed beside them and are **not**
failures: how many records state an author in capitals (2) and how many state an escape (1). An artefact
in which nothing needed folding is correct; what must fail when a rule has nothing to exercise is the
**control**, which is `verify_correction_r3.py`'s job.

**Conservation.** Regenerating moved **3 lines** of `manuscript.md`, all of them author components:
`[15]`, `[20]`, `[95]`. Every other rendered character — the titles, years, venues, URLs and the 125
`Difference: …` lines — is the byte it was at `38c278c`, and `canonical_results.json` and `run.log` are
untouched. R3-c takes that read by re-rendering with each fix removed in turn and requiring exactly
`['15','20']` and `['95']` to move, each inside its own author block.

## Citation report

`reference-check.md` reports the verification of all **125** references by their own identifiers
(21 via the Crossref DOI endpoint, 104 via their arXiv abstract pages - the arXiv export API was
returning HTTP 503/429 during the run and this is recorded in the report rather than hidden), and
the in-text coverage check: `refgate.py` from the repository root reports
`entries=125 covered=125/125 coverage=100.0% GATE: PASS`.

## Seeds

Instance seed `1000*s + N`, noise seed `7*s + 3` on the law / mechanism / closure grids;
`5000*s + 7*N` and `13*s + 11` on the held-out grid. `s` runs to the per-grid seed count
(30 law, 20 out-of-sample, 25 ablation, 15 closure).
