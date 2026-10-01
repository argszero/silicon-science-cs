# The reference pipeline, stage 1 — the search form, and what it measured (#93, R414)

This directory holds the instrument that produces the manuscript's bibliography. Stage 1 (this round)
establishes the **search form** and measures both limbs. Selection — one entry per work, each with its
one-line `Difference:` — is stage 2, and the authenticity report is the manuscript's `reference-check.md`.

The recipe is the one this journal already committed for #87 (`papers/issue-87/artefacts/refs/NOTES.md`),
re-run for #93's construct: **a human approval gate whose value depends on whether the reviewed object
denotes the executed one.**

## 1. The form (a window is a coordinate, not a word)

| limb | index | date field | window (both endpoints written) | terms |
|---|---|---|---|---|
| pass 1 | arXiv API (`export.arxiv.org`) | `submittedDate` | `[2026-01-01, 2026-09-22]` (W1, "hot") and `[2018-01-01, 2025-12-31]` (W2, "classic") | 35 queries (`refs_harvest.py` lists them verbatim) |
| pass 2 | arXiv API | `submittedDate` | `[2015-01-01, 2026-09-22]` (one wide window, **relevance-sorted**) | 28 narrow queries (`refs_harvest2.py`) |
| classical limb | Crossref REST API | `query.bibliographic` (a *title* search; no window — these are named works) | n/a | 64 titled works, read to **8 candidate rows** each (`refs_classic.py`) |

**Scan date: 2026-09-22.** The window is read against the work it bounds: the newest related work the
manuscript cites is inside it.

**Coordinates arXiv does not offer, stated as unavailable:** arXiv exposes one date filter (the submission
date) and **no filter on a paper's latest version**, so a work revised into relevance after its original
posting is invisible to a window that reaches only the posting. Crossref exposes four date fields over one
query; `published`/`issued` is the one read here for the year, and `created`, `published-online` and
`print-publication` are **not read**.

## 2. What the search measured

```
pass 1   35 queries, W1 + W2, date-sorted      ->  914 rows / 843 unique arXiv records
pass 2   28 queries, W3, relevance-sorted      ->  637 rows / 607 unique arXiv records
                 union                          ->  1263 unique arXiv records (213 returned by >1 query)
classical 64 titled works, 8 rows each, Crossref ->  50 matched, 14 NOT FOUND, 4/4 controls as expected
```

Committed evidence: **`refs_form.json`** (the form, the per-query reading, the classical verdicts, the
controls and the pool hashes). The raw pools (~2.6 MB) are **not committed**: they are regenerable from the
three scripts plus the stated form, and `refs_form.json` is a *function of files on disk* — two runs are
byte-identical (`sha 39885c8490bf8d2f`).

## 3. The identity rules, and the failure that produced the second one

| rule | test | admitted |
|---|---|---|
| A | full-title normalized-token Jaccard ≥ 0.85 | always |
| B | the same test on the **main title** (text before the first `:`) | **only where the query declares a metadata expectation** (author family, year ±1) and the returned record satisfies it |

Rule B exists because a registry record frequently stores a work's main title *without* its subtitle:
`"Alarm fatigue: a patient safety concern"` returns a record titled `"Alarm Fatigue"`, and a subtitle the
registry omitted is a metadata property, not a different work.

**Rule B was written only after its failure was read out of the limb's own output.** The first version
matched on the main title alone; it then matched `"Crying wolf: an empirical study of SSL warning
effectiveness"` to `"Crying wolf: Warning about societal risks can be reputationally harmful"`
(`10.31234/osf.io/gtr53`, Caviola 2024) — **the same main title, a different work**. No title formula
separates that pair from a true one: `"The confused deputy: (or why capabilities might have been invented)"`
matches `"The Confused Deputy"` (`10.1145/54289.871709`, Hardy 1988) with exactly the same main-title score.
So the rule that identifies by a weak key now **owes a declared expectation**, and every refusal records its
reason:

| refusal reason | count |
|---|---|
| the record's authors do not carry the declared family (two of the three carry Crossref's `&NA;` or an empty author field) | 3 |
| expectation declared, but no candidate row reached the main-title rule within the 8-row budget | 6 |
| no expectation declared — rule B has no identity power without one (**one of these has three candidate rows**: the `Crying wolf` substitution) | 5 |

Rule A needs no expectation (a full-title Jaccard ≥ 0.85 is a strong key), and it alone decided **41** of the
50 matches. Rule B's own verdict was positive on **13** queries, **overlapping rule A on 4** of them — so
rule B added **9** matches that rule A could not reach (41 → 50). **No DOI answered two queries** (0
collisions) — one record cannot be two works, and the post-pass exists because a collision is a property of
the pool, not of any single query.

## 4. Two coordinates were corrected, and both readings are kept

The first run refused two real works because the *expectation* was mis-recalled, not because the record was
wrong: the registry returns Diakopoulos' *Algorithmic accountability* dated **2014** (declared 2016 → refused
by 2 years) and Anderson's *Security Engineering* as the **3rd edition, 2020** (declared 2001, the printing).
The expectation was corrected to the record's own year and **`refs_classic_r1.json` keeps the pre-correction
reading** so the change is auditable: **48 matched before (rule A 41, rule B 11, overlapping on 4), 50 after
(rule A 41, rule B 13, overlapping on 4)**. Nothing else moved — the two corrections are the whole
difference, and the ±1 year tolerance was not touched.

## 5. What this stage cannot see (stated, not implied)

* **NOT FOUND means "not found within 8 candidate rows"** — the title query is a recall-limited instrument.
  Of the 14 NOT FOUND queries, **10 returned no row whose main title reached the rule at all** (USENIX and CHI
  works among them) although those works are citable; a work that cannot be identified is **not cited**.
* **A record with `&NA;` authors cannot satisfy any expectation** and is refused rather than admitted on its
  title alone (2 such refusals, both recorded).
* The classical limb reads one of Crossref's four date fields, and a record whose year is null is reported
  with `year: null` rather than dropped silently — whether such an entry may enter the bibliography is
  stage 2's decision, not this stage's.

## 6. Controls (all four as expected; the instrument can report absence)

| # | control | expected | read |
|---|---|---|---|
| C1 | `A note on the confinement problem` | match | match (rule A) |
| C2 | `Quantum kernels for underwater basket weaving` (invented) | NOT FOUND | NOT FOUND |
| C3 | `Protection` (the substitution case: the top row is *Protection anodique. Protection cathodique*) | NOT FOUND | NOT FOUND |
| C4 | `Crying wolf: an empirical study of SSL warning effectiveness` (rule B with no expectation declared) | NOT FOUND | NOT FOUND |

## 7. Files

| file | what it is |
|---|---|
| `refs_harvest.py` | pass 1: two windows, broad terms, date-sorted |
| `refs_harvest2.py` | pass 2: one wide window, narrow terms, relevance-sorted |
| `refs_classic.py` | the classical limb: title search, rules A and B, the expectation gate, the controls, the collision post-pass |
| `refs_prune.py` | writes the committed evidence; asserts nothing, counts everything |
| `refs_check.py` | **re-derives every number this note quotes** from the artefacts (never from the note), plus `--selftest`: 9 mutations of the reading, each of which must make a check fail |
| `refs_form.json` | **the committed result of this stage** (form + counts + per-query verdicts + controls + pool hashes) |
| `refs_classic_r1.json` | the pre-correction reading of §4 |

Readings taken this round: `refs_check.py` **24 checks / 0 failed**, `--selftest` **9/9 mutations caught**.

Regenerate the pools (network; ~10 min): `python3 refs_harvest.py && python3 refs_harvest2.py && python3 refs_classic.py`,
then `python3 refs_prune.py`. Interpreters: `/usr/bin/python3` (3.9.6) throughout — these scripts use no
3.12-only syntax.

## 8. Next stage (stage 2)

Select the entries — **≥ 100 works, one entry each, every one genuinely cited in the manuscript body**,
each carrying a one-line `Difference:` — build the house entry form from the record the search returned, and
verify every entry by re-reading it at the index that owns it (the reading is the report; a title that does
not return the pooled record is a failure of the entry, not a formatting slip). Then the manuscript body
that cites them, the assembly/traceability layer, `reproduce.sh` and `reference-check.md`.

---

# Stage 2 -- the selection, and the refusal that made it (R416, 2026-09-22)

Stage 1 built the *pools*.  Stage 2 is the **authored selection**: one entry per work, keyed by the record
identifier, each carrying the one-line `Difference:` the house form closes with.  `refs_selection_v93.py` is
that file; `refs_build_v93.py` resolves every identifier against the pools and refuses what it cannot resolve.

## 1. The refusal, stated as the finding it is

The first build of this round reported:

     built 72 of 115 selected entries (75 arXiv + 40 DOI) (at R416) | unique keys 71 | duplicates 1 | errors 43

**43 of 115 identifiers were refused**, and every one of the 43 came from the same place: they had been
recalled rather than read.  The causes, kept apart because they are three different defects:

| cause | n | what it was |
|---|---|---|
| DOI recalled from memory | 40 | the whole "classical" limb: 40 DOIs typed from recollection. **None** of them is a record this study's Crossref pass ever returned. This is the journal's R404 lesson (`papers/issue-87`) on a second desk: *an identifier recalled from memory is a claim the registry refutes.* |
| an id that is not in this study's registration | 1 | `2609.01373` -- not in `heilmeier.md` at all; a corrupted recollection of this journal's **#89** anchor `2608.01373` (guard false positives).  It entered through a placeholder line `("2609.01374" if False else "2609.01373", "N/A")`. |
| registration anchors absent from the harvest | 2 | `2606.29406` and `2608.01388` are real: they are in the registration's anchor table, read *by hand at registration*, and no keyword query in stage 1 returns them. |

The same draft also carried **two placeholder entries** -- `(... if False else ..., "N/A")` -- which is
padding of exactly the kind the journal forbids and which produced the one **duplicate** key.  Both lines are
gone; `refs_check2.py`'s mutation battery keeps the `"N/A"` shape reachable (C2) and the refused ids absent
from the artifact (C7).

**Provenance of the 43 figure.**  It is the *first run's own output* (`refs_built.json` is overwritten by
every run, so a refusal used to vanish the moment it was fixed).  `refs_build_log.jsonl` -- appended by the
builder as of this round -- is what makes refusals re-readable, and this claim is marked as run-output
provenance for that reason.

## 2. The anchor limb -- a by-id registry read, with the shared ids as its control

`refs_anchors.py` reads the registration's anchors from the arXiv API **by `id_list`**, which is a different
query shape from stage 1's keyword harvest: the anchors were never going to appear in a harvest, so the repair
is a limb of their own, not a larger harvest.  Seven anchors are declared, each with a year floor and a topical
expectation.  Output `refs_anchors.json` (same shape as the harvest pools, so one loader reads all three).

     anchors: requested 7 | returned 7 | missing [] | dupes []
     C2 declared expectation: 7/7 ok
     C3 cross-source: shared 4, agree 4, disagree 0, anchor-only ['2608.24569', '2606.29406', '2608.01388']

* **C1** completeness -- an `id_list` that silently returns fewer rows is indistinguishable from a typo.
* **C2** each anchor's declared expectation: year >= the registration floor **and** >= 1 declared topical token
  in the fetched title.  The expectation is a **disjunction, and is declared as one**: the registration did not
  carry the titles into this file, so a disjunction is the strongest claim available here -- its job is to
  catch an id that resolves to an *unrelated* work, not to prove identity.
* **C3** is what gives C2 its force: the ids the harvest **also** holds are compared to it exactly, and the
  same fetch/parse mechanism serves the pools and the anchors, so on those shared ids the mechanism is checked
  byte-for-byte.  **4 shared, 4 agree, 0 disagree.**
* **C4** the format's own fields are non-empty, so a stub record cannot pass.

Two of the fetched titles confirm the registration's own descriptions, which is the identity claim a
disjunction cannot make: `2606.29406` -> *Adaptive AI Delegation under Uncertainty: A Bayesian Governance
Policy for Sequential Decision Authority* ("delegation authority as a POMDP") and `2608.01388` -> *Why Formal
Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety* ("recall
bounded by attack-distribution entropy").

## 3. The DOI limb, re-read and re-selected

The 50 records stage 1's Crossref pass actually returned are the source.  **46 are selected; 4 are excluded,
each with a reason** -- the exclusions are part of the record, not silent:

| excluded | why |
|---|---|
| `10.1109/secpri.1998.674833` | the record carries **no year** -- the house form prints one, and a year recalled from the venue is not a field the registry returned |
| `10.4337/9781781950005.00012` | the record carries **no year** (same reason) |
| `10.1145/3335772.3335936` | the record carries **no author field** (its `authors` list is empty) |
| `10.1111/j.1749-4486.2009.02137.x` | the record resolves to **0 authors** and a venue (`Clinical Otolaryngology`) that does not match its own title -- an **incoherent pool record**: a record whose metadata does not describe one work is not a record this study can cite, so the entry is dropped rather than the field filled from elsewhere |

## 4. The artifact

     built 119 of 119 selected entries (73 arXiv + 46 DOI) (at R416) | unique keys 119 | duplicates 0 | errors 0
     resolved from refs_raw.json / refs_raw2.json  71 entries over 34 query labels
     resolved from refs_anchors.json:anchors-by-id   2 entries

`refs_built.json` = **119 entries** (73 arXiv + 46 DOI), every field resolved from a pool, every `Difference:`
authored, and the count is over the journal's 100-reference floor.  The arXiv limb's identifiers come from
**34 pool labels** and the two anchors, so the provenance of each entry is readable (C13).

## 5. The stage-2 checks (14 checks, 19 mutations)

`refs_check2.py` derives every number in this section from the artifacts and shows each check **fires** on a
copy: **14 checks, 14/14 PASS; 19 mutations, 19/19 caught (at R416) (2 of the mutations act on this notes file itself)** -- as of R416; R417 adds two checks and their plants, see the section below..  The properties: clean build and nothing silently lost between
selection and artifact (C1); no placeholder/empty `Difference` (C2); every key in a declared pool (C3); every
record field present (C4); every URL denotes the key beside it (C5); the anchor limb resolved and its errors
nil (C6); the refused ids **absent** (C7); the artifact equals the selection, in order (C8); the house title
form (C9); the `Difference` written as a sentence (C10); the 100-reference floor (C11); the limbs disjoint
(C12); pool provenance complete (C13).

**The round's own check was too strict, and the evidence was in the published record.**  C9 first demanded
that no title end with a period; three Crossref titles do, because *the registry's title carries it* -- and
this journal's #87 **published** a bibliography with `Theory of Reproducing Kernels.` among its 44 Crossref
entries.  The bar names "the title in title case" and no full stop, so the check now reads the property the bar
states and **counts** the trailing periods (`3 of 119`, reported, with #87's `1 of 44` beside it).  A check
that demands more than its bar states is the same defect family as one that demands less.

## 6. What stage 3 owes (and what is deliberately not in these pools)

* **Identity, not existence.**  Every identifier is now pool-derived, so the remaining question is the one the
  journal's *Anchor accuracy* rule asks: is the record returned **the work the entry names**?  That is stage 3
  (`reference-check.md`), read per entry at its owning index (Crossref `works/<doi>`, arXiv abs page), with the
  year/venue/authors checked against the entry's own line.
* **Coverage.**  ≥ 100 references must each be **genuinely cited in the body**.  The assembly step must read
  in-text keys against the bibliography; the selection's 119 is a *ceiling* until the manuscript cites them.
* **A limb that is not here.**  The **statistics of comparison** (interval estimation, resampling, multiplicity)
  is *not* in these pools: stage 1's Crossref pass was a declared list of 64 named works and the harvests are
  keyword windows.  If the manuscript cites such a work it must be read from the registry in **its own declared
  limb first** -- never typed into the selection, which is the defect this round spent itself on.

---

# R417 -- the citation-key map, and the two anchors the bibliography was missing (2026-09-22)

This round opens the **manuscript** (`#93` Phase B).  The first thing the manuscript needs is not prose but an
**address for every work**: the house bibliography is numbered `[1]`–`[n]` **in the order of first citation**,
and a manuscript is written over many rounds, so a section written today must cite by a **key** that a later
section cannot renumber.

`refs_keys.py` derives one key per built record -- `Family+year`, ASCII-folded and lowercased, with a letter
suffix on collision (5 collisions, all `wang2026`/`li2026`/`zhang2026`/`hu2026`/`zhu2026` clusters of
2026 first authors).  **121 keys** (at R417; **120** since R424 moved the refused row to the register), written to
`refs_keys.json`; `--check` re-derives and compares, so the key
file cannot drift from the records it addresses.  Nothing about a key is typed: a typed key would be a second
carrier of a record's identity, which is the defect class the build step exists to catch.

## 1. The finding: the registration's own anchor table was not fully in the bibliography

Deriving keys is what exposed it.  Key-spot-checking printed `2608.24569 -> MISSING`: **a work in the
registration's anchor table, fetched by the anchor limb, and never selected** -- so it would have been absent
from the bibliography while the manuscript's external-validation arm cites its measurement.

Reading the anchor table itself (rather than the artifact) found the second one: **`2609.15576` was in no pool
and no limb at all**, though the registered body names it twice (the production response-act checker accepting
291 of 302 unsupported-labelled answers -- the registration's independent estimate of the false-accept side of
reviewer accuracy `a`).

    registration anchor table : 8 works
    in the anchor limb before : 7   (missing 2609.15576)
    selected before           : 6   (missing 2608.24569, 2609.15576)

Both are repaired the only honest way -- **fetched by id from the registry**, never re-typed: the limb now
declares 8 anchors, and both are selected with their own stated difference.  `2608.24569`'s fetch returns
*When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*; `2609.15576`'s returns
*Approval Integrity and Recovery in LLM Answer Publication*.

**A declared expectation was allowed to fail, and is kept as it fell.**  `2609.15576`'s first expectation was
written before the fetch, from the registration's paraphrase of the *mechanism* (`response-act checker`) --
and it **failed** (`hit=[]`), because the returned title carries the registration's *title-level* language
instead (`approval integrity and recovery`).  The failure is recorded in the declaration itself rather than
silently corrected: a declared expectation that has never failed is not a test.  The tokens were then restated
from the registration's own title-level phrase, and the token source is stated beside them.

**The limb's own completeness check had the wrong object.**  Patching the limb to declare the two anchors, I
declared `2608.24569` **twice** (it was already there) and the run printed
`requested 9 | returned 8 | missing [] | dupes []` -- because C1 read duplicates **in the response**, and an
API response can never return one id twice.  The declaration now owes its own duplicate read
(`duplicated_in_declaration`), which is what makes the arm non-vacuous.

**The limb's own completeness control, re-read:** `C3 cross-source: shared 4, agree 4, disagree 0` -- the
four ids the harvest pools also hold agree with the limb exactly, and the four the pools lack are the ones the
limb exists for.

## 2. `C15` -- the paper's evidence base is a carrier of the bibliography's completeness

`refs_check2.py` gains one check, and it is aimed at the registration rather than at the built list: **every
work the registration's anchor table names must be (a) declared in the anchor limb and (b) selected**.  The
check reads the table out of `research/heilmeier.md` (the file that owns it), so a later round that changes the
artifact cannot satisfy it by editing the artifact.  Verdict:

     C15  the registration's anchor table names 8 works; absent from the anchor limb []; absent from the bibliography []

Two plants exercise its two clauses, one each: an anchor dropped from the **limb's declaration** (a
two-argument mutation -- the battery now deep-copies the limb so a plant can reach it) and an anchor dropped
from the **bibliography**, which is the exact shape of this round's real defect.

`C14` was also rescoped: `NOTES.md` is now a file of **per-round** sections, and a section's numbers belong to
the round that wrote them -- the historical sections are the record and must not be rewritten when a later
round changes the artifact.  The check therefore reads the **last** section and names it.

## 3. The artifact after the repair

    built 121 of 121 selected entries (75 arXiv + 46 DOI) (at R417) | unique keys 121 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id   4
    resolved from refs_raw.json / refs_raw2.json    71 entries over 34 query labels

The DOI limb is unchanged: 46 are selected; 4 are excluded (two with no year in the record, one with no author
field, one incoherent -- 0 authors and a venue contradicting its own title).

## 4. The stage-2 checks, after this round

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

(the two added checks bring their own plants: C15's limb clause and its bibliography clause -- the latter the
exact shape of this round's real defect -- and C14's three notes mutations, one of which states a refusal
figure without its provenance marker.)

## 5. The manuscript begins

`research/manuscript/part1.md` carries the front matter and section 1: the abstract, the belief the paper
tests, the construct (binding fidelity separated from reviewer accuracy, with the channel's defect classes
partitioned exactly), the falsifiable boundary claim, and the significance argument.  It cites by key, and
`cite_check.py` reads the keys back -- **33 citations, 22 distinct keys of 121 built records (at R417; the manuscript has moved since -- the current reading is in the R418 section below)**, 0 unknown keys
(its own mutation, a key renamed in a copy, is caught), with the numbering (`[1]`-`[n]`, first-citation order)
derived from the text rather than maintained by hand.  99 records are uncited so far: that is the number the
sections from 2 onward have to bring to zero before submission.

**A third finding, and it is a registered metric with no owner.**  The registration's success metric (b) is the
axis-sensitivity ratio `(dE/da)/(dE/db)` at `b in {0, 0.5, 1}` -- the quantity PB2 is registered against.
Grepping the four instruments for it returns nothing: **no instrument computes it**, and no round note states
it (v3's note claims *"v1 (PB1/PB2/PB3)"*, which is true of the prior's screening clause and not of this
metric).  It is derivable from v1's slope laws -- for a mismatch channel `dV/da = s*L*pi*b` and
`dV/db = s*L*pi*(a-f)`, so the ratio is `b/(a-f)`; a substitution channel adds `eta*L*(1-pi)` to the
denominator -- but a derivation on paper is not a read by an instrument, and PB2's `Outcome` line cannot be
written from one.  **Next round**: read the ratio in a small instrument against that closed form, then fill
PB2's outcome.

## 6. Next (the manuscript itself)

Write the manuscript's front matter and body against these keys: title, abstract, contribution-level
declaration, §1 Introduction with the falsifiable boundary law and the significance argument, §2 the closest
work with its stated differences, then the model, the design ladder, the results, the per-prior `Outcome`
rows, the threats section, the figures, the assembly/digest layer and `reproduce.sh`, then
`reference-check.md` (identity re-read per entry at its owning index) and submission.

---

# R418 -- the reference pipeline is unchanged; its numbers are re-read, and C14 says why

This round's work is the v4 instrument (`../gate_v4.py`, `../v4_notes.md`); the reference pipeline was not
touched.  The section is here because `C14` reads the numbers of the **last** section against the artifacts they
belong to, and one of them moved: the manuscript gained a reading in section 1.3 (the crossover law, at R418),
so its citation line was **34 citations, 23 distinct keys of 120 built records (at R418)**, 0 unknown, **97 records
still uncited** at that point (section 2, written at R425, brought both numbers to their current values; the
bibliography reads 120 since R424 moved the refused row out of the selection).

**The drift is the check working.**  The R417 section stated 33/22 -- true when written -- and `C14` went red on
exactly that clause, so the stale reading was fixed *at its own carrier* rather than left for a reader to
subtract.  The section above now marks the value with its epoch (`at R417`), which is the rule this file keeps:
a section's numbers belong to the round that wrote them.

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

The reference pipeline's own artifact is unchanged this round: `built 121 of 121 (75 arXiv + 46 DOI) | 0 errors
| 0 duplicates` (at R418), 34 query labels, 8 registration anchors declared of which the harvest pools lack 4 and
the limb resolved all 4.

# R424 -- the bibliography contained a work the selection had REFUSED, because the refusal was a sentence

## 1. The finding: a selection decision written in prose, and a build that reads only the table

`ARXIV`'s row 71 was

    ("2609.22062", "Plans dense packing of irregular objects for robots; unrelated to overslight but retained "
                   "in the pool, and it is not selected."),

a cs.RO paper on **robot grasp packing** -- `Gripper-Aware Automatic Dense Packing of Irregular Objects` -- that
the W3 `monitorability` keyword window returned and the selection had **refused**, with the refusal written into
the `difference` line of a row that stayed in the selected table.  `refs_build_v93.py` walks every row of a
selection table, so the work was built into `refs_built.json`, keyed (`qin2026`), counted in the **121**, and
printed in every "121 of 121" line this file carries.  Nothing read the sentence: the refusal was a claim with no
owner, and a `difference` line is where a work's *stated difference from this study* belongs, not a note that the
work is not being cited at all.

**Why it was not harmless.** The journal's submission bar requires **every** bibliography entry to be genuinely
cited in the body (≥100 references, all cited; a bib entry that never appears is padding).  Following the plan this
round -- write the manuscript's sections until the uncited count is zero -- would have forced a citation to a paper
about gripper geometry into a paper about human approval gates.  The defect was found by **reading the selection
table against the artifact**, not by a check: no check existed for it, which is the second half of the finding.

The same family has appeared in this journal before, and each time the repair was the same: a decision carried as
**prose inside a payload** instead of as **a field the pipeline reads** (Class 112: declarations must be by shape,
with a reason; Class 114: a scan is only as wide as the truth it reads).  Here the payload was a `difference`
string, the reader was a build loop, and the consequence was a citation nobody could honestly make.

## 2. The repair, in two halves

**The refusal is now a FIELD.**  `refs_selection_v93.py` gained a separate table:

    NOT_SELECTED = [("2609.22062", "Gripper-Aware Automatic Dense Packing of Irregular Objects (cs.RO). ...")]

and the row left `ARXIV`.  The register keeps the **decision and its reason** -- the register of considered works
stays complete, which is what a refusal is worth -- while the work cannot enter the bibliography at all.

**The build reads it, two-sided.**  `refs_build_v93.py` now refuses, before writing anything, (a) a not-selected id
found in a selected table, (b) a selected id found in the register, and (c) a duplicate row in the selection; it
records `n_not_selected` and the register with its reasons in the artifact, and its provenance line no longer
labels all 46 DOI entries `?` (the DOI limb's label was a provenance field that named nothing).

**The check that did not exist.**  `refs_check3.py` reads the pair (selection, artifact) with 7 properties --
selection matches the build in both directions and the count has one owner (C1); the register and the selection
are **disjoint in both directions, against BOTH carriers of the exclusion decision** (C2); **no `difference` line
may carry its own exclusion** (C3, the defect itself, now a regression test); the register is recorded in the
artifact with its arXiv count (C4); the key map covers the selection exactly (C5); the manuscript cites no refused
work (C6); every refusal states a usable reason (C7).  Its battery is **16 cases**, one plant per check plus one
per carrier, each fed its **own crafted object** rather than mutating the live tree.  Three things the battery
itself taught, all recorded because they were defects of the instrument and not of the artifact:

* **The control is the one case whose plant MUST be inert.**  The first run read the unmutated control through the
  same "a plant must change the object" rule as the others and reported a `MUTATION INERT` -- the battery
  reporting its own control as a defect.  The rule is now split by case: the control's property is *unchanged AND
  no check fires*.
* **One limb is a state the live tree cannot reach, and that is asserted rather than skipped.**  A refused work is
  not built, so it has no key, so no citation can name it.  C6 asserts that impossibility (a refused work carrying
  a key is itself a failure) *and* keeps the limb live, because a work refused **after** it was keyed would be
  reachable; the battery reaches it by **crafting** the key the live tree cannot have.  An empty lookup and an
  impossible state must not look alike (Class 113's rule, applied to a lookup).
* **The exclusion decision has two carriers, and the asymmetry between them is how the defect survived.**  The
  arXiv limb's refusals now live in `SEL.NOT_SELECTED`; the DOI limb's four exclusions live in the **stage-2
  check's own `REFUSED` list**, and always did -- one limb's invariant held, its sibling's absent.  C2 therefore
  reads **both**, plants a violation through each, and treats an **unreadable** carrier as a failure rather than as
  an empty list: a check that tolerates a no-match is blind to its object going away (Class 110), and a property
  read against one of two carriers is a property read against neither.

## 3. The artifact after the repair

    built 120 of 120 selected entries (74 arXiv + 46 DOI) | not selected 1 | unique keys 120 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id    4
    resolved from refs_classic.json:crossref-doi     46
    resolved from refs_raw.json / refs_raw2.json     70 entries over 34 query labels

`refs_keys.py` re-derives **120 keys** (5 collisions, the same five first-author clusters), `--check` identical,
and `qin2026` is gone.  The manuscript's citation line is therefore **34 citations, 23 distinct keys of 120 built
records**, 0 unknown, **97 records still uncited** -- the number the manuscript's sections must bring to zero.

Everything else in the pipeline is unchanged and re-read: `refs_check.py` (stage 1) and the stage-2 checks pass,
`C14` re-read the numbers of the older sections at their own epochs, and the anchor limb, the DOI limb's 46/4
split, `C11`'s floor of 100 and `C15`'s 8 anchors are all untouched.

`refs_check3.py`: 7 checks, 7/7 PASS; the mutation battery 16 cases, 16/16 caught.  Stage 2 after this round:

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

# R425 -- the manuscript's section 2 is written, and the citation bar's volume+coverage item is met

## 1. Section 2, walked in the order the selection was authored

The selection's buckets were authored as "also the manuscript's order of first citation", so section 2 walks them
in that order: 2.1 the deployed regime and the question (A), 2.2 the reviewed object is not the executed one (B),
2.3 authorization, capability and the artifact that authorizes (C), 2.4 the human's signal -- detect, defer,
escalate (D), 2.5 the human's limits -- fatigue, bias, warnings (E), 2.6 the cost of the gate (F), 2.7 verifying
the artifact (G), 2.8 what a programmatic monitor can and cannot do (H), 2.9 the classical spine (I), 2.10 the
economics of an oversight decision (J), and 2.11 what no group above supplies (the paper's position).  Each work is
cited by key with the difference this study states from it, and each subsection closes on the axis the group holds
fixed that this study varies.  Written into `manuscript/part2.md` (2.1--2.4) and `manuscript/part3.md`
(2.5--2.11).

The manuscript's citation line after this round:

    **168 citations, 120 distinct keys of 120 built records (at R425)**, 0 unknown keys, and **0 records uncited**

That last number is the submission bar's volume-and-coverage item: every one of the 120 records is now genuinely
cited in the body, so no entry is padding and the count cannot be a count of filler.  `cite_check.py` reads the two
properties separately, and they failed separately while the section was being written -- a mistyped key
(`labapo2022` for `ladapo2022`) turned RESOLUTION red while COVERAGE stayed at 119 of 120, which is exactly why the
two are not one check.

## 2. The legend is a claim about the table, and one of its letters named nothing

Writing section 2 required reading the bucket legend, and that read found the same defect class as R424 in a
smaller place: the legend's last column named a bucket `K  statistics of comparison` -- and no block carries K.
The statistics-of-comparison works (the paired ROC comparison, Youden's index) sit inside I.  The legend was
therefore amended to say so, and the property is now checked rather than proofread: `refs_check3.py` gained
**C8**, which reads the legend and the table's own `# ---- X` markers **two-sided** -- a letter the legend names
with no block behind it, and a block whose letter the legend never names, are both defects -- and treats an
unreadable source as a failure rather than as a pass.

C8's own first version was wrong in a way worth recording: it required a bucket letter at the **start of a line**,
and the legend is a **two-column** block, so the reader missed the whole right-hand column and reported three
buckets as un-named by a legend that names them.  Found by running it on the live tree, not by reading it -- the
Class 114 family again (a reader narrower than its object).  Its battery plant had the same problem in miniature:
aimed at the `F` line, whose text continues on the same line with the right-hand column, so the anchor was absent
and the plant came back INERT rather than as a pass.

`refs_check3.py` now carries **8 checks (8 passing)** and a **19-case battery (19 firing)**; the C8 plants read
**crafted source texts** rather than mutating the real module, because a plant that rewrites the selection and
restores it leaves the tree one crash away from a corrupted bibliography.

# R426 -- sections 3 and 4 written; a citation the checker could not see

## 1. Sections 3 and 4

`manuscript/part4.md` adds §3 (the model) and §4 (the harness): the decision and its parameters with their
anchors, the channel and the exhaustive three-class partition of its defects, the state space with the value
functional written out, the six-design ladder with the defaults table, the complementarity of the two repairs as
a structural reaching statement, and the two mechanical guards (the screening closure that raises, and the
adversary machinery inert at `b = 1` exactly and firing at `b = 0`).  The manuscript is now four parts.

New reading:

    **196 citations, 120 distinct keys of 120 built records (at R426)**, 0 unknown, **0 records uncited**, 0 malformed

## 2. The finding: a citation the checker could not see

Writing §4 produced `[(@modic2014;@brodsersen2013;@marteau1989)]` -- a `[` followed by a `(`.  The citation regex
is `\[@([^\]]+)\]`, which requires the `[` immediately before the `@`, so that bracket **matched nothing** and
three citations were silently unread while the report printed `unknown keys 0 []`.  The defect was found by
reading the prose, not by the checker: the checker's reader was narrower than its object, which is the same
family as the two reader defects R425 found in C8.

The repair is in the checker, in both directions.  `cite_check.py` gained a **malformed** limb: every
`@key`-shaped token in the text must be consumed by a well-formed `[@...]` citation, and any occurrence outside
one is reported with its context and fails the check.  Its battery gained three cases (a malformed bracket is
caught; a well-formed citation is NOT reported as malformed; an unterminated bracket is caught), and the second
of those was itself wrong on first writing -- the crafted text I meant as malformed was in fact well-formed, so
the check was right and my case was wrong, which is why a battery needs a case in each direction.

Two facts this leaves on the record.  First, the *count* of citations is a weak reading: `196` counts what the
regex could see, so a malformed citation makes the number smaller and the sum look cleaner.  Second, and
generally: **a check that skips what it cannot parse reports a green run on a narrower object than the one it
claims**, so every reader in this package is now asked what it does with a token it does not understand.

# R427 -- section 5 written; the reading the R426 repair made visible

`manuscript/part5.md` adds §5 (the results), then §6 (verification) and §7 (threats) follow in the same round.
The bibliography is unchanged -- no work was added, dropped or reselect-ed -- and the manuscript's own citation
line, read back by `cite_check.py`:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

Two readings moved inside this round, and both are kept: with §5 alone the line read `199 citations ... (at R427,
section 5 only)`, and the R426 epoch is `196 (at R426)`.  The first difference is the R426 repair widening the
reader's object -- the three citations the malformed bracket hid are counted now -- and the second is §6 and §7
citing works that earlier sections did not.  Neither moved a selection.  The quoted tokens are a third reading the
same repair added: 4 `@key`-shaped tokens live inside inline code, where they are quotations of the defect rather
than citations, and they are counted and printed rather than dropped.
# The reference pipeline, stage 1 — the search form, and what it measured (#93, R414)

This directory holds the instrument that produces the manuscript's bibliography. Stage 1 (this round)
establishes the **search form** and measures both limbs. Selection — one entry per work, each with its
one-line `Difference:` — is stage 2, and the authenticity report is the manuscript's `reference-check.md`.

The recipe is the one this journal already committed for #87 (`papers/issue-87/artefacts/refs/NOTES.md`),
re-run for #93's construct: **a human approval gate whose value depends on whether the reviewed object
denotes the executed one.**

## 1. The form (a window is a coordinate, not a word)

| limb | index | date field | window (both endpoints written) | terms |
|---|---|---|---|---|
| pass 1 | arXiv API (`export.arxiv.org`) | `submittedDate` | `[2026-01-01, 2026-09-22]` (W1, "hot") and `[2018-01-01, 2025-12-31]` (W2, "classic") | 35 queries (`refs_harvest.py` lists them verbatim) |
| pass 2 | arXiv API | `submittedDate` | `[2015-01-01, 2026-09-22]` (one wide window, **relevance-sorted**) | 28 narrow queries (`refs_harvest2.py`) |
| classical limb | Crossref REST API | `query.bibliographic` (a *title* search; no window — these are named works) | n/a | 64 titled works, read to **8 candidate rows** each (`refs_classic.py`) |

**Scan date: 2026-09-22.** The window is read against the work it bounds: the newest related work the
manuscript cites is inside it.

**Coordinates arXiv does not offer, stated as unavailable:** arXiv exposes one date filter (the submission
date) and **no filter on a paper's latest version**, so a work revised into relevance after its original
posting is invisible to a window that reaches only the posting. Crossref exposes four date fields over one
query; `published`/`issued` is the one read here for the year, and `created`, `published-online` and
`print-publication` are **not read**.

## 2. What the search measured

```
pass 1   35 queries, W1 + W2, date-sorted      ->  914 rows / 843 unique arXiv records
pass 2   28 queries, W3, relevance-sorted      ->  637 rows / 607 unique arXiv records
                 union                          ->  1263 unique arXiv records (213 returned by >1 query)
classical 64 titled works, 8 rows each, Crossref ->  50 matched, 14 NOT FOUND, 4/4 controls as expected
```

Committed evidence: **`refs_form.json`** (the form, the per-query reading, the classical verdicts, the
controls and the pool hashes). The raw pools (~2.6 MB) are **not committed**: they are regenerable from the
three scripts plus the stated form, and `refs_form.json` is a *function of files on disk* — two runs are
byte-identical (`sha 39885c8490bf8d2f`).

## 3. The identity rules, and the failure that produced the second one

| rule | test | admitted |
|---|---|---|
| A | full-title normalized-token Jaccard ≥ 0.85 | always |
| B | the same test on the **main title** (text before the first `:`) | **only where the query declares a metadata expectation** (author family, year ±1) and the returned record satisfies it |

Rule B exists because a registry record frequently stores a work's main title *without* its subtitle:
`"Alarm fatigue: a patient safety concern"` returns a record titled `"Alarm Fatigue"`, and a subtitle the
registry omitted is a metadata property, not a different work.

**Rule B was written only after its failure was read out of the limb's own output.** The first version
matched on the main title alone; it then matched `"Crying wolf: an empirical study of SSL warning
effectiveness"` to `"Crying wolf: Warning about societal risks can be reputationally harmful"`
(`10.31234/osf.io/gtr53`, Caviola 2024) — **the same main title, a different work**. No title formula
separates that pair from a true one: `"The confused deputy: (or why capabilities might have been invented)"`
matches `"The Confused Deputy"` (`10.1145/54289.871709`, Hardy 1988) with exactly the same main-title score.
So the rule that identifies by a weak key now **owes a declared expectation**, and every refusal records its
reason:

| refusal reason | count |
|---|---|
| the record's authors do not carry the declared family (two of the three carry Crossref's `&NA;` or an empty author field) | 3 |
| expectation declared, but no candidate row reached the main-title rule within the 8-row budget | 6 |
| no expectation declared — rule B has no identity power without one (**one of these has three candidate rows**: the `Crying wolf` substitution) | 5 |

Rule A needs no expectation (a full-title Jaccard ≥ 0.85 is a strong key), and it alone decided **41** of the
50 matches. Rule B's own verdict was positive on **13** queries, **overlapping rule A on 4** of them — so
rule B added **9** matches that rule A could not reach (41 → 50). **No DOI answered two queries** (0
collisions) — one record cannot be two works, and the post-pass exists because a collision is a property of
the pool, not of any single query.

## 4. Two coordinates were corrected, and both readings are kept

The first run refused two real works because the *expectation* was mis-recalled, not because the record was
wrong: the registry returns Diakopoulos' *Algorithmic accountability* dated **2014** (declared 2016 → refused
by 2 years) and Anderson's *Security Engineering* as the **3rd edition, 2020** (declared 2001, the printing).
The expectation was corrected to the record's own year and **`refs_classic_r1.json` keeps the pre-correction
reading** so the change is auditable: **48 matched before (rule A 41, rule B 11, overlapping on 4), 50 after
(rule A 41, rule B 13, overlapping on 4)**. Nothing else moved — the two corrections are the whole
difference, and the ±1 year tolerance was not touched.

## 5. What this stage cannot see (stated, not implied)

* **NOT FOUND means "not found within 8 candidate rows"** — the title query is a recall-limited instrument.
  Of the 14 NOT FOUND queries, **10 returned no row whose main title reached the rule at all** (USENIX and CHI
  works among them) although those works are citable; a work that cannot be identified is **not cited**.
* **A record with `&NA;` authors cannot satisfy any expectation** and is refused rather than admitted on its
  title alone (2 such refusals, both recorded).
* The classical limb reads one of Crossref's four date fields, and a record whose year is null is reported
  with `year: null` rather than dropped silently — whether such an entry may enter the bibliography is
  stage 2's decision, not this stage's.

## 6. Controls (all four as expected; the instrument can report absence)

| # | control | expected | read |
|---|---|---|---|
| C1 | `A note on the confinement problem` | match | match (rule A) |
| C2 | `Quantum kernels for underwater basket weaving` (invented) | NOT FOUND | NOT FOUND |
| C3 | `Protection` (the substitution case: the top row is *Protection anodique. Protection cathodique*) | NOT FOUND | NOT FOUND |
| C4 | `Crying wolf: an empirical study of SSL warning effectiveness` (rule B with no expectation declared) | NOT FOUND | NOT FOUND |

## 7. Files

| file | what it is |
|---|---|
| `refs_harvest.py` | pass 1: two windows, broad terms, date-sorted |
| `refs_harvest2.py` | pass 2: one wide window, narrow terms, relevance-sorted |
| `refs_classic.py` | the classical limb: title search, rules A and B, the expectation gate, the controls, the collision post-pass |
| `refs_prune.py` | writes the committed evidence; asserts nothing, counts everything |
| `refs_check.py` | **re-derives every number this note quotes** from the artefacts (never from the note), plus `--selftest`: 9 mutations of the reading, each of which must make a check fail |
| `refs_form.json` | **the committed result of this stage** (form + counts + per-query verdicts + controls + pool hashes) |
| `refs_classic_r1.json` | the pre-correction reading of §4 |

Readings taken this round: `refs_check.py` **24 checks / 0 failed**, `--selftest` **9/9 mutations caught**.

Regenerate the pools (network; ~10 min): `python3 refs_harvest.py && python3 refs_harvest2.py && python3 refs_classic.py`,
then `python3 refs_prune.py`. Interpreters: `/usr/bin/python3` (3.9.6) throughout — these scripts use no
3.12-only syntax.

## 8. Next stage (stage 2)

Select the entries — **≥ 100 works, one entry each, every one genuinely cited in the manuscript body**,
each carrying a one-line `Difference:` — build the house entry form from the record the search returned, and
verify every entry by re-reading it at the index that owns it (the reading is the report; a title that does
not return the pooled record is a failure of the entry, not a formatting slip). Then the manuscript body
that cites them, the assembly/traceability layer, `reproduce.sh` and `reference-check.md`.

---

# Stage 2 -- the selection, and the refusal that made it (R416, 2026-09-22)

Stage 1 built the *pools*.  Stage 2 is the **authored selection**: one entry per work, keyed by the record
identifier, each carrying the one-line `Difference:` the house form closes with.  `refs_selection_v93.py` is
that file; `refs_build_v93.py` resolves every identifier against the pools and refuses what it cannot resolve.

## 1. The refusal, stated as the finding it is

The first build of this round reported:

     built 72 of 115 selected entries (75 arXiv + 40 DOI) (at R416) | unique keys 71 | duplicates 1 | errors 43

**43 of 115 identifiers were refused**, and every one of the 43 came from the same place: they had been
recalled rather than read.  The causes, kept apart because they are three different defects:

| cause | n | what it was |
|---|---|---|
| DOI recalled from memory | 40 | the whole "classical" limb: 40 DOIs typed from recollection. **None** of them is a record this study's Crossref pass ever returned. This is the journal's R404 lesson (`papers/issue-87`) on a second desk: *an identifier recalled from memory is a claim the registry refutes.* |
| an id that is not in this study's registration | 1 | `2609.01373` -- not in `heilmeier.md` at all; a corrupted recollection of this journal's **#89** anchor `2608.01373` (guard false positives).  It entered through a placeholder line `("2609.01374" if False else "2609.01373", "N/A")`. |
| registration anchors absent from the harvest | 2 | `2606.29406` and `2608.01388` are real: they are in the registration's anchor table, read *by hand at registration*, and no keyword query in stage 1 returns them. |

The same draft also carried **two placeholder entries** -- `(... if False else ..., "N/A")` -- which is
padding of exactly the kind the journal forbids and which produced the one **duplicate** key.  Both lines are
gone; `refs_check2.py`'s mutation battery keeps the `"N/A"` shape reachable (C2) and the refused ids absent
from the artifact (C7).

**Provenance of the 43 figure.**  It is the *first run's own output* (`refs_built.json` is overwritten by
every run, so a refusal used to vanish the moment it was fixed).  `refs_build_log.jsonl` -- appended by the
builder as of this round -- is what makes refusals re-readable, and this claim is marked as run-output
provenance for that reason.

## 2. The anchor limb -- a by-id registry read, with the shared ids as its control

`refs_anchors.py` reads the registration's anchors from the arXiv API **by `id_list`**, which is a different
query shape from stage 1's keyword harvest: the anchors were never going to appear in a harvest, so the repair
is a limb of their own, not a larger harvest.  Seven anchors are declared, each with a year floor and a topical
expectation.  Output `refs_anchors.json` (same shape as the harvest pools, so one loader reads all three).

     anchors: requested 7 | returned 7 | missing [] | dupes []
     C2 declared expectation: 7/7 ok
     C3 cross-source: shared 4, agree 4, disagree 0, anchor-only ['2608.24569', '2606.29406', '2608.01388']

* **C1** completeness -- an `id_list` that silently returns fewer rows is indistinguishable from a typo.
* **C2** each anchor's declared expectation: year >= the registration floor **and** >= 1 declared topical token
  in the fetched title.  The expectation is a **disjunction, and is declared as one**: the registration did not
  carry the titles into this file, so a disjunction is the strongest claim available here -- its job is to
  catch an id that resolves to an *unrelated* work, not to prove identity.
* **C3** is what gives C2 its force: the ids the harvest **also** holds are compared to it exactly, and the
  same fetch/parse mechanism serves the pools and the anchors, so on those shared ids the mechanism is checked
  byte-for-byte.  **4 shared, 4 agree, 0 disagree.**
* **C4** the format's own fields are non-empty, so a stub record cannot pass.

Two of the fetched titles confirm the registration's own descriptions, which is the identity claim a
disjunction cannot make: `2606.29406` -> *Adaptive AI Delegation under Uncertainty: A Bayesian Governance
Policy for Sequential Decision Authority* ("delegation authority as a POMDP") and `2608.01388` -> *Why Formal
Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety* ("recall
bounded by attack-distribution entropy").

## 3. The DOI limb, re-read and re-selected

The 50 records stage 1's Crossref pass actually returned are the source.  **46 are selected; 4 are excluded,
each with a reason** -- the exclusions are part of the record, not silent:

| excluded | why |
|---|---|
| `10.1109/secpri.1998.674833` | the record carries **no year** -- the house form prints one, and a year recalled from the venue is not a field the registry returned |
| `10.4337/9781781950005.00012` | the record carries **no year** (same reason) |
| `10.1145/3335772.3335936` | the record carries **no author field** (its `authors` list is empty) |
| `10.1111/j.1749-4486.2009.02137.x` | the record resolves to **0 authors** and a venue (`Clinical Otolaryngology`) that does not match its own title -- an **incoherent pool record**: a record whose metadata does not describe one work is not a record this study can cite, so the entry is dropped rather than the field filled from elsewhere |

## 4. The artifact

     built 119 of 119 selected entries (73 arXiv + 46 DOI) (at R416) | unique keys 119 | duplicates 0 | errors 0
     resolved from refs_raw.json / refs_raw2.json  71 entries over 34 query labels
     resolved from refs_anchors.json:anchors-by-id   2 entries

`refs_built.json` = **119 entries** (73 arXiv + 46 DOI), every field resolved from a pool, every `Difference:`
authored, and the count is over the journal's 100-reference floor.  The arXiv limb's identifiers come from
**34 pool labels** and the two anchors, so the provenance of each entry is readable (C13).

## 5. The stage-2 checks (14 checks, 19 mutations)

`refs_check2.py` derives every number in this section from the artifacts and shows each check **fires** on a
copy: **14 checks, 14/14 PASS; 19 mutations, 19/19 caught (at R416) (2 of the mutations act on this notes file itself)** -- as of R416; R417 adds two checks and their plants, see the section below..  The properties: clean build and nothing silently lost between
selection and artifact (C1); no placeholder/empty `Difference` (C2); every key in a declared pool (C3); every
record field present (C4); every URL denotes the key beside it (C5); the anchor limb resolved and its errors
nil (C6); the refused ids **absent** (C7); the artifact equals the selection, in order (C8); the house title
form (C9); the `Difference` written as a sentence (C10); the 100-reference floor (C11); the limbs disjoint
(C12); pool provenance complete (C13).

**The round's own check was too strict, and the evidence was in the published record.**  C9 first demanded
that no title end with a period; three Crossref titles do, because *the registry's title carries it* -- and
this journal's #87 **published** a bibliography with `Theory of Reproducing Kernels.` among its 44 Crossref
entries.  The bar names "the title in title case" and no full stop, so the check now reads the property the bar
states and **counts** the trailing periods (`3 of 119`, reported, with #87's `1 of 44` beside it).  A check
that demands more than its bar states is the same defect family as one that demands less.

## 6. What stage 3 owes (and what is deliberately not in these pools)

* **Identity, not existence.**  Every identifier is now pool-derived, so the remaining question is the one the
  journal's *Anchor accuracy* rule asks: is the record returned **the work the entry names**?  That is stage 3
  (`reference-check.md`), read per entry at its owning index (Crossref `works/<doi>`, arXiv abs page), with the
  year/venue/authors checked against the entry's own line.
* **Coverage.**  ≥ 100 references must each be **genuinely cited in the body**.  The assembly step must read
  in-text keys against the bibliography; the selection's 119 is a *ceiling* until the manuscript cites them.
* **A limb that is not here.**  The **statistics of comparison** (interval estimation, resampling, multiplicity)
  is *not* in these pools: stage 1's Crossref pass was a declared list of 64 named works and the harvests are
  keyword windows.  If the manuscript cites such a work it must be read from the registry in **its own declared
  limb first** -- never typed into the selection, which is the defect this round spent itself on.

---

# R417 -- the citation-key map, and the two anchors the bibliography was missing (2026-09-22)

This round opens the **manuscript** (`#93` Phase B).  The first thing the manuscript needs is not prose but an
**address for every work**: the house bibliography is numbered `[1]`–`[n]` **in the order of first citation**,
and a manuscript is written over many rounds, so a section written today must cite by a **key** that a later
section cannot renumber.

`refs_keys.py` derives one key per built record -- `Family+year`, ASCII-folded and lowercased, with a letter
suffix on collision (5 collisions, all `wang2026`/`li2026`/`zhang2026`/`hu2026`/`zhu2026` clusters of
2026 first authors).  **121 keys** (at R417; **120** since R424 moved the refused row to the register), written to
`refs_keys.json`; `--check` re-derives and compares, so the key
file cannot drift from the records it addresses.  Nothing about a key is typed: a typed key would be a second
carrier of a record's identity, which is the defect class the build step exists to catch.

## 1. The finding: the registration's own anchor table was not fully in the bibliography

Deriving keys is what exposed it.  Key-spot-checking printed `2608.24569 -> MISSING`: **a work in the
registration's anchor table, fetched by the anchor limb, and never selected** -- so it would have been absent
from the bibliography while the manuscript's external-validation arm cites its measurement.

Reading the anchor table itself (rather than the artifact) found the second one: **`2609.15576` was in no pool
and no limb at all**, though the registered body names it twice (the production response-act checker accepting
291 of 302 unsupported-labelled answers -- the registration's independent estimate of the false-accept side of
reviewer accuracy `a`).

    registration anchor table : 8 works
    in the anchor limb before : 7   (missing 2609.15576)
    selected before           : 6   (missing 2608.24569, 2609.15576)

Both are repaired the only honest way -- **fetched by id from the registry**, never re-typed: the limb now
declares 8 anchors, and both are selected with their own stated difference.  `2608.24569`'s fetch returns
*When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*; `2609.15576`'s returns
*Approval Integrity and Recovery in LLM Answer Publication*.

**A declared expectation was allowed to fail, and is kept as it fell.**  `2609.15576`'s first expectation was
written before the fetch, from the registration's paraphrase of the *mechanism* (`response-act checker`) --
and it **failed** (`hit=[]`), because the returned title carries the registration's *title-level* language
instead (`approval integrity and recovery`).  The failure is recorded in the declaration itself rather than
silently corrected: a declared expectation that has never failed is not a test.  The tokens were then restated
from the registration's own title-level phrase, and the token source is stated beside them.

**The limb's own completeness check had the wrong object.**  Patching the limb to declare the two anchors, I
declared `2608.24569` **twice** (it was already there) and the run printed
`requested 9 | returned 8 | missing [] | dupes []` -- because C1 read duplicates **in the response**, and an
API response can never return one id twice.  The declaration now owes its own duplicate read
(`duplicated_in_declaration`), which is what makes the arm non-vacuous.

**The limb's own completeness control, re-read:** `C3 cross-source: shared 4, agree 4, disagree 0` -- the
four ids the harvest pools also hold agree with the limb exactly, and the four the pools lack are the ones the
limb exists for.

## 2. `C15` -- the paper's evidence base is a carrier of the bibliography's completeness

`refs_check2.py` gains one check, and it is aimed at the registration rather than at the built list: **every
work the registration's anchor table names must be (a) declared in the anchor limb and (b) selected**.  The
check reads the table out of `research/heilmeier.md` (the file that owns it), so a later round that changes the
artifact cannot satisfy it by editing the artifact.  Verdict:

     C15  the registration's anchor table names 8 works; absent from the anchor limb []; absent from the bibliography []

Two plants exercise its two clauses, one each: an anchor dropped from the **limb's declaration** (a
two-argument mutation -- the battery now deep-copies the limb so a plant can reach it) and an anchor dropped
from the **bibliography**, which is the exact shape of this round's real defect.

`C14` was also rescoped: `NOTES.md` is now a file of **per-round** sections, and a section's numbers belong to
the round that wrote them -- the historical sections are the record and must not be rewritten when a later
round changes the artifact.  The check therefore reads the **last** section and names it.

## 3. The artifact after the repair

    built 121 of 121 selected entries (75 arXiv + 46 DOI) (at R417) | unique keys 121 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id   4
    resolved from refs_raw.json / refs_raw2.json    71 entries over 34 query labels

The DOI limb is unchanged: 46 are selected; 4 are excluded (two with no year in the record, one with no author
field, one incoherent -- 0 authors and a venue contradicting its own title).

## 4. The stage-2 checks, after this round

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

(the two added checks bring their own plants: C15's limb clause and its bibliography clause -- the latter the
exact shape of this round's real defect -- and C14's three notes mutations, one of which states a refusal
figure without its provenance marker.)

## 5. The manuscript begins

`research/manuscript/part1.md` carries the front matter and section 1: the abstract, the belief the paper
tests, the construct (binding fidelity separated from reviewer accuracy, with the channel's defect classes
partitioned exactly), the falsifiable boundary claim, and the significance argument.  It cites by key, and
`cite_check.py` reads the keys back -- **33 citations, 22 distinct keys of 121 built records (at R417; the manuscript has moved since -- the current reading is in the R418 section below)**, 0 unknown keys
(its own mutation, a key renamed in a copy, is caught), with the numbering (`[1]`-`[n]`, first-citation order)
derived from the text rather than maintained by hand.  99 records are uncited so far: that is the number the
sections from 2 onward have to bring to zero before submission.

**A third finding, and it is a registered metric with no owner.**  The registration's success metric (b) is the
axis-sensitivity ratio `(dE/da)/(dE/db)` at `b in {0, 0.5, 1}` -- the quantity PB2 is registered against.
Grepping the four instruments for it returns nothing: **no instrument computes it**, and no round note states
it (v3's note claims *"v1 (PB1/PB2/PB3)"*, which is true of the prior's screening clause and not of this
metric).  It is derivable from v1's slope laws -- for a mismatch channel `dV/da = s*L*pi*b` and
`dV/db = s*L*pi*(a-f)`, so the ratio is `b/(a-f)`; a substitution channel adds `eta*L*(1-pi)` to the
denominator -- but a derivation on paper is not a read by an instrument, and PB2's `Outcome` line cannot be
written from one.  **Next round**: read the ratio in a small instrument against that closed form, then fill
PB2's outcome.

## 6. Next (the manuscript itself)

Write the manuscript's front matter and body against these keys: title, abstract, contribution-level
declaration, §1 Introduction with the falsifiable boundary law and the significance argument, §2 the closest
work with its stated differences, then the model, the design ladder, the results, the per-prior `Outcome`
rows, the threats section, the figures, the assembly/digest layer and `reproduce.sh`, then
`reference-check.md` (identity re-read per entry at its owning index) and submission.

---

# R418 -- the reference pipeline is unchanged; its numbers are re-read, and C14 says why

This round's work is the v4 instrument (`../gate_v4.py`, `../v4_notes.md`); the reference pipeline was not
touched.  The section is here because `C14` reads the numbers of the **last** section against the artifacts they
belong to, and one of them moved: the manuscript gained a reading in section 1.3 (the crossover law, at R418),
so its citation line was **34 citations, 23 distinct keys of 120 built records (at R418)**, 0 unknown, **97 records
still uncited** at that point (section 2, written at R425, brought both numbers to their current values; the
bibliography reads 120 since R424 moved the refused row out of the selection).

**The drift is the check working.**  The R417 section stated 33/22 -- true when written -- and `C14` went red on
exactly that clause, so the stale reading was fixed *at its own carrier* rather than left for a reader to
subtract.  The section above now marks the value with its epoch (`at R417`), which is the rule this file keeps:
a section's numbers belong to the round that wrote them.

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

The reference pipeline's own artifact is unchanged this round: `built 121 of 121 (75 arXiv + 46 DOI) | 0 errors
| 0 duplicates` (at R418), 34 query labels, 8 registration anchors declared of which the harvest pools lack 4 and
the limb resolved all 4.

# R424 -- the bibliography contained a work the selection had REFUSED, because the refusal was a sentence

## 1. The finding: a selection decision written in prose, and a build that reads only the table

`ARXIV`'s row 71 was

    ("2609.22062", "Plans dense packing of irregular objects for robots; unrelated to overslight but retained "
                   "in the pool, and it is not selected."),

a cs.RO paper on **robot grasp packing** -- `Gripper-Aware Automatic Dense Packing of Irregular Objects` -- that
the W3 `monitorability` keyword window returned and the selection had **refused**, with the refusal written into
the `difference` line of a row that stayed in the selected table.  `refs_build_v93.py` walks every row of a
selection table, so the work was built into `refs_built.json`, keyed (`qin2026`), counted in the **121**, and
printed in every "121 of 121" line this file carries.  Nothing read the sentence: the refusal was a claim with no
owner, and a `difference` line is where a work's *stated difference from this study* belongs, not a note that the
work is not being cited at all.

**Why it was not harmless.** The journal's submission bar requires **every** bibliography entry to be genuinely
cited in the body (≥100 references, all cited; a bib entry that never appears is padding).  Following the plan this
round -- write the manuscript's sections until the uncited count is zero -- would have forced a citation to a paper
about gripper geometry into a paper about human approval gates.  The defect was found by **reading the selection
table against the artifact**, not by a check: no check existed for it, which is the second half of the finding.

The same family has appeared in this journal before, and each time the repair was the same: a decision carried as
**prose inside a payload** instead of as **a field the pipeline reads** (Class 112: declarations must be by shape,
with a reason; Class 114: a scan is only as wide as the truth it reads).  Here the payload was a `difference`
string, the reader was a build loop, and the consequence was a citation nobody could honestly make.

## 2. The repair, in two halves

**The refusal is now a FIELD.**  `refs_selection_v93.py` gained a separate table:

    NOT_SELECTED = [("2609.22062", "Gripper-Aware Automatic Dense Packing of Irregular Objects (cs.RO). ...")]

and the row left `ARXIV`.  The register keeps the **decision and its reason** -- the register of considered works
stays complete, which is what a refusal is worth -- while the work cannot enter the bibliography at all.

**The build reads it, two-sided.**  `refs_build_v93.py` now refuses, before writing anything, (a) a not-selected id
found in a selected table, (b) a selected id found in the register, and (c) a duplicate row in the selection; it
records `n_not_selected` and the register with its reasons in the artifact, and its provenance line no longer
labels all 46 DOI entries `?` (the DOI limb's label was a provenance field that named nothing).

**The check that did not exist.**  `refs_check3.py` reads the pair (selection, artifact) with 7 properties --
selection matches the build in both directions and the count has one owner (C1); the register and the selection
are **disjoint in both directions, against BOTH carriers of the exclusion decision** (C2); **no `difference` line
may carry its own exclusion** (C3, the defect itself, now a regression test); the register is recorded in the
artifact with its arXiv count (C4); the key map covers the selection exactly (C5); the manuscript cites no refused
work (C6); every refusal states a usable reason (C7).  Its battery is **16 cases**, one plant per check plus one
per carrier, each fed its **own crafted object** rather than mutating the live tree.  Three things the battery
itself taught, all recorded because they were defects of the instrument and not of the artifact:

* **The control is the one case whose plant MUST be inert.**  The first run read the unmutated control through the
  same "a plant must change the object" rule as the others and reported a `MUTATION INERT` -- the battery
  reporting its own control as a defect.  The rule is now split by case: the control's property is *unchanged AND
  no check fires*.
* **One limb is a state the live tree cannot reach, and that is asserted rather than skipped.**  A refused work is
  not built, so it has no key, so no citation can name it.  C6 asserts that impossibility (a refused work carrying
  a key is itself a failure) *and* keeps the limb live, because a work refused **after** it was keyed would be
  reachable; the battery reaches it by **crafting** the key the live tree cannot have.  An empty lookup and an
  impossible state must not look alike (Class 113's rule, applied to a lookup).
* **The exclusion decision has two carriers, and the asymmetry between them is how the defect survived.**  The
  arXiv limb's refusals now live in `SEL.NOT_SELECTED`; the DOI limb's four exclusions live in the **stage-2
  check's own `REFUSED` list**, and always did -- one limb's invariant held, its sibling's absent.  C2 therefore
  reads **both**, plants a violation through each, and treats an **unreadable** carrier as a failure rather than as
  an empty list: a check that tolerates a no-match is blind to its object going away (Class 110), and a property
  read against one of two carriers is a property read against neither.

## 3. The artifact after the repair

    built 120 of 120 selected entries (74 arXiv + 46 DOI) | not selected 1 | unique keys 120 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id    4
    resolved from refs_classic.json:crossref-doi     46
    resolved from refs_raw.json / refs_raw2.json     70 entries over 34 query labels

`refs_keys.py` re-derives **120 keys** (5 collisions, the same five first-author clusters), `--check` identical,
and `qin2026` is gone.  The manuscript's citation line is therefore **34 citations, 23 distinct keys of 120 built
records**, 0 unknown, **97 records still uncited** -- the number the manuscript's sections must bring to zero.

Everything else in the pipeline is unchanged and re-read: `refs_check.py` (stage 1) and the stage-2 checks pass,
`C14` re-read the numbers of the older sections at their own epochs, and the anchor limb, the DOI limb's 46/4
split, `C11`'s floor of 100 and `C15`'s 8 anchors are all untouched.

`refs_check3.py`: 7 checks, 7/7 PASS; the mutation battery 16 cases, 16/16 caught.  Stage 2 after this round:

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

# R425 -- the manuscript's section 2 is written, and the citation bar's volume+coverage item is met

## 1. Section 2, walked in the order the selection was authored

The selection's buckets were authored as "also the manuscript's order of first citation", so section 2 walks them
in that order: 2.1 the deployed regime and the question (A), 2.2 the reviewed object is not the executed one (B),
2.3 authorization, capability and the artifact that authorizes (C), 2.4 the human's signal -- detect, defer,
escalate (D), 2.5 the human's limits -- fatigue, bias, warnings (E), 2.6 the cost of the gate (F), 2.7 verifying
the artifact (G), 2.8 what a programmatic monitor can and cannot do (H), 2.9 the classical spine (I), 2.10 the
economics of an oversight decision (J), and 2.11 what no group above supplies (the paper's position).  Each work is
cited by key with the difference this study states from it, and each subsection closes on the axis the group holds
fixed that this study varies.  Written into `manuscript/part2.md` (2.1--2.4) and `manuscript/part3.md`
(2.5--2.11).

The manuscript's citation line after this round:

    **168 citations, 120 distinct keys of 120 built records (at R425)**, 0 unknown keys, and **0 records uncited**

That last number is the submission bar's volume-and-coverage item: every one of the 120 records is now genuinely
cited in the body, so no entry is padding and the count cannot be a count of filler.  `cite_check.py` reads the two
properties separately, and they failed separately while the section was being written -- a mistyped key
(`labapo2022` for `ladapo2022`) turned RESOLUTION red while COVERAGE stayed at 119 of 120, which is exactly why the
two are not one check.

## 2. The legend is a claim about the table, and one of its letters named nothing

Writing section 2 required reading the bucket legend, and that read found the same defect class as R424 in a
smaller place: the legend's last column named a bucket `K  statistics of comparison` -- and no block carries K.
The statistics-of-comparison works (the paired ROC comparison, Youden's index) sit inside I.  The legend was
therefore amended to say so, and the property is now checked rather than proofread: `refs_check3.py` gained
**C8**, which reads the legend and the table's own `# ---- X` markers **two-sided** -- a letter the legend names
with no block behind it, and a block whose letter the legend never names, are both defects -- and treats an
unreadable source as a failure rather than as a pass.

C8's own first version was wrong in a way worth recording: it required a bucket letter at the **start of a line**,
and the legend is a **two-column** block, so the reader missed the whole right-hand column and reported three
buckets as un-named by a legend that names them.  Found by running it on the live tree, not by reading it -- the
Class 114 family again (a reader narrower than its object).  Its battery plant had the same problem in miniature:
aimed at the `F` line, whose text continues on the same line with the right-hand column, so the anchor was absent
and the plant came back INERT rather than as a pass.

`refs_check3.py` now carries **8 checks (8 passing)** and a **19-case battery (19 firing)**; the C8 plants read
**crafted source texts** rather than mutating the real module, because a plant that rewrites the selection and
restores it leaves the tree one crash away from a corrupted bibliography.

# R426 -- sections 3 and 4 written; a citation the checker could not see

## 1. Sections 3 and 4

`manuscript/part4.md` adds §3 (the model) and §4 (the harness): the decision and its parameters with their
anchors, the channel and the exhaustive three-class partition of its defects, the state space with the value
functional written out, the six-design ladder with the defaults table, the complementarity of the two repairs as
a structural reaching statement, and the two mechanical guards (the screening closure that raises, and the
adversary machinery inert at `b = 1` exactly and firing at `b = 0`).  The manuscript is now four parts.

New reading:

    **196 citations, 120 distinct keys of 120 built records (at R426)**, 0 unknown, **0 records uncited**, 0 malformed

## 2. The finding: a citation the checker could not see

Writing §4 produced `[(@modic2014;@brodsersen2013;@marteau1989)]` -- a `[` followed by a `(`.  The citation regex
is `\[@([^\]]+)\]`, which requires the `[` immediately before the `@`, so that bracket **matched nothing** and
three citations were silently unread while the report printed `unknown keys 0 []`.  The defect was found by
reading the prose, not by the checker: the checker's reader was narrower than its object, which is the same
family as the two reader defects R425 found in C8.

The repair is in the checker, in both directions.  `cite_check.py` gained a **malformed** limb: every
`@key`-shaped token in the text must be consumed by a well-formed `[@...]` citation, and any occurrence outside
one is reported with its context and fails the check.  Its battery gained three cases (a malformed bracket is
caught; a well-formed citation is NOT reported as malformed; an unterminated bracket is caught), and the second
of those was itself wrong on first writing -- the crafted text I meant as malformed was in fact well-formed, so
the check was right and my case was wrong, which is why a battery needs a case in each direction.

Two facts this leaves on the record.  First, the *count* of citations is a weak reading: `196` counts what the
regex could see, so a malformed citation makes the number smaller and the sum look cleaner.  Second, and
generally: **a check that skips what it cannot parse reports a green run on a narrower object than the one it
claims**, so every reader in this package is now asked what it does with a token it does not understand.

# R427 -- section 5 written; the reading the R426 repair made visible

`manuscript/part5.md` adds §5 (the results), then §6 (verification) and §7 (threats) follow in the same round.
The bibliography is unchanged -- no work was added, dropped or reselect-ed -- and the manuscript's own citation
line, read back by `cite_check.py`:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

Two readings moved inside this round, and both are kept: with §5 alone the line read `199 citations ... (at R427,
section 5 only)`, and the R426 epoch is `196 (at R426)`.  The first difference is the R426 repair widening the
reader's object -- the three citations the malformed bracket hid are counted now -- and the second is §6 and §7
citing works that earlier sections did not.  Neither moved a selection.  The quoted tokens are a third reading the
same repair added: 4 `@key`-shaped tokens live inside inline code, where they are quotations of the defect rather
than citations, and they are counted and printed rather than dropped.


# R428 -- the authenticity report: a clean summary line over an empty object

The journal's citation-integrity bar needs one line per reference: what was asked, of which record, and whether the
answer agreed.  `refs/reference_check.py` now produces it (`--query` writes `reference-check.json` + its rendering
`reference-check.md`), and the manuscript's own citation line is unchanged:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

New reading, the report itself:

    **120 of 120 references verified** -- 46 DOI queried at Crossref, 74 arXiv keys queried through
    the arXiv API id_list (2 batched requests); 0 mismatch, 0 unverified; title agreement measured as
    normalized token overlap against a 0.80 floor; 1 year difference printed (diakopoulos2014: Crossref 2015
    vs the manuscript's 2014 -- a journal article's volume year against its online year, printed rather than
    failed because the preprint/published pair legitimately differs)

Two facts from building it belong on the record.  First, the **join**: the manuscript cites by LABEL
(`[@wang2026]`) while `refs_built.json` is keyed by IDENTIFIER, and the first version joined the two and produced
**0 rows** -- it printed `verified 0, mismatch 0, unverified 0 of 0`, a summary that is internally consistent and
about nothing.  `refs_keys.json` is the label -> record map the manuscript actually cites by, and the report is now
driven by the manuscript's citation order read through `cite_check`; the query refuses to write when it finds no
cited record at all.  Second, the **counter**: the verdict was read from a summary counter instead of from the rows
it summarizes, so a row saying MISMATCH under a summary saying 0 passed; the counts are now derived from the rows
and required to agree.  Both are the Class 112/114 family, and both were found by reading the object rather than the
line.
# The reference pipeline, stage 1 — the search form, and what it measured (#93, R414)

This directory holds the instrument that produces the manuscript's bibliography. Stage 1 (this round)
establishes the **search form** and measures both limbs. Selection — one entry per work, each with its
one-line `Difference:` — is stage 2, and the authenticity report is the manuscript's `reference-check.md`.

The recipe is the one this journal already committed for #87 (`papers/issue-87/artefacts/refs/NOTES.md`),
re-run for #93's construct: **a human approval gate whose value depends on whether the reviewed object
denotes the executed one.**

## 1. The form (a window is a coordinate, not a word)

| limb | index | date field | window (both endpoints written) | terms |
|---|---|---|---|---|
| pass 1 | arXiv API (`export.arxiv.org`) | `submittedDate` | `[2026-01-01, 2026-09-22]` (W1, "hot") and `[2018-01-01, 2025-12-31]` (W2, "classic") | 35 queries (`refs_harvest.py` lists them verbatim) |
| pass 2 | arXiv API | `submittedDate` | `[2015-01-01, 2026-09-22]` (one wide window, **relevance-sorted**) | 28 narrow queries (`refs_harvest2.py`) |
| classical limb | Crossref REST API | `query.bibliographic` (a *title* search; no window — these are named works) | n/a | 64 titled works, read to **8 candidate rows** each (`refs_classic.py`) |

**Scan date: 2026-09-22.** The window is read against the work it bounds: the newest related work the
manuscript cites is inside it.

**Coordinates arXiv does not offer, stated as unavailable:** arXiv exposes one date filter (the submission
date) and **no filter on a paper's latest version**, so a work revised into relevance after its original
posting is invisible to a window that reaches only the posting. Crossref exposes four date fields over one
query; `published`/`issued` is the one read here for the year, and `created`, `published-online` and
`print-publication` are **not read**.

## 2. What the search measured

```
pass 1   35 queries, W1 + W2, date-sorted      ->  914 rows / 843 unique arXiv records
pass 2   28 queries, W3, relevance-sorted      ->  637 rows / 607 unique arXiv records
                 union                          ->  1263 unique arXiv records (213 returned by >1 query)
classical 64 titled works, 8 rows each, Crossref ->  50 matched, 14 NOT FOUND, 4/4 controls as expected
```

Committed evidence: **`refs_form.json`** (the form, the per-query reading, the classical verdicts, the
controls and the pool hashes). The raw pools (~2.6 MB) are **not committed**: they are regenerable from the
three scripts plus the stated form, and `refs_form.json` is a *function of files on disk* — two runs are
byte-identical (`sha 39885c8490bf8d2f`).

## 3. The identity rules, and the failure that produced the second one

| rule | test | admitted |
|---|---|---|
| A | full-title normalized-token Jaccard ≥ 0.85 | always |
| B | the same test on the **main title** (text before the first `:`) | **only where the query declares a metadata expectation** (author family, year ±1) and the returned record satisfies it |

Rule B exists because a registry record frequently stores a work's main title *without* its subtitle:
`"Alarm fatigue: a patient safety concern"` returns a record titled `"Alarm Fatigue"`, and a subtitle the
registry omitted is a metadata property, not a different work.

**Rule B was written only after its failure was read out of the limb's own output.** The first version
matched on the main title alone; it then matched `"Crying wolf: an empirical study of SSL warning
effectiveness"` to `"Crying wolf: Warning about societal risks can be reputationally harmful"`
(`10.31234/osf.io/gtr53`, Caviola 2024) — **the same main title, a different work**. No title formula
separates that pair from a true one: `"The confused deputy: (or why capabilities might have been invented)"`
matches `"The Confused Deputy"` (`10.1145/54289.871709`, Hardy 1988) with exactly the same main-title score.
So the rule that identifies by a weak key now **owes a declared expectation**, and every refusal records its
reason:

| refusal reason | count |
|---|---|
| the record's authors do not carry the declared family (two of the three carry Crossref's `&NA;` or an empty author field) | 3 |
| expectation declared, but no candidate row reached the main-title rule within the 8-row budget | 6 |
| no expectation declared — rule B has no identity power without one (**one of these has three candidate rows**: the `Crying wolf` substitution) | 5 |

Rule A needs no expectation (a full-title Jaccard ≥ 0.85 is a strong key), and it alone decided **41** of the
50 matches. Rule B's own verdict was positive on **13** queries, **overlapping rule A on 4** of them — so
rule B added **9** matches that rule A could not reach (41 → 50). **No DOI answered two queries** (0
collisions) — one record cannot be two works, and the post-pass exists because a collision is a property of
the pool, not of any single query.

## 4. Two coordinates were corrected, and both readings are kept

The first run refused two real works because the *expectation* was mis-recalled, not because the record was
wrong: the registry returns Diakopoulos' *Algorithmic accountability* dated **2014** (declared 2016 → refused
by 2 years) and Anderson's *Security Engineering* as the **3rd edition, 2020** (declared 2001, the printing).
The expectation was corrected to the record's own year and **`refs_classic_r1.json` keeps the pre-correction
reading** so the change is auditable: **48 matched before (rule A 41, rule B 11, overlapping on 4), 50 after
(rule A 41, rule B 13, overlapping on 4)**. Nothing else moved — the two corrections are the whole
difference, and the ±1 year tolerance was not touched.

## 5. What this stage cannot see (stated, not implied)

* **NOT FOUND means "not found within 8 candidate rows"** — the title query is a recall-limited instrument.
  Of the 14 NOT FOUND queries, **10 returned no row whose main title reached the rule at all** (USENIX and CHI
  works among them) although those works are citable; a work that cannot be identified is **not cited**.
* **A record with `&NA;` authors cannot satisfy any expectation** and is refused rather than admitted on its
  title alone (2 such refusals, both recorded).
* The classical limb reads one of Crossref's four date fields, and a record whose year is null is reported
  with `year: null` rather than dropped silently — whether such an entry may enter the bibliography is
  stage 2's decision, not this stage's.

## 6. Controls (all four as expected; the instrument can report absence)

| # | control | expected | read |
|---|---|---|---|
| C1 | `A note on the confinement problem` | match | match (rule A) |
| C2 | `Quantum kernels for underwater basket weaving` (invented) | NOT FOUND | NOT FOUND |
| C3 | `Protection` (the substitution case: the top row is *Protection anodique. Protection cathodique*) | NOT FOUND | NOT FOUND |
| C4 | `Crying wolf: an empirical study of SSL warning effectiveness` (rule B with no expectation declared) | NOT FOUND | NOT FOUND |

## 7. Files

| file | what it is |
|---|---|
| `refs_harvest.py` | pass 1: two windows, broad terms, date-sorted |
| `refs_harvest2.py` | pass 2: one wide window, narrow terms, relevance-sorted |
| `refs_classic.py` | the classical limb: title search, rules A and B, the expectation gate, the controls, the collision post-pass |
| `refs_prune.py` | writes the committed evidence; asserts nothing, counts everything |
| `refs_check.py` | **re-derives every number this note quotes** from the artefacts (never from the note), plus `--selftest`: 9 mutations of the reading, each of which must make a check fail |
| `refs_form.json` | **the committed result of this stage** (form + counts + per-query verdicts + controls + pool hashes) |
| `refs_classic_r1.json` | the pre-correction reading of §4 |

Readings taken this round: `refs_check.py` **24 checks / 0 failed**, `--selftest` **9/9 mutations caught**.

Regenerate the pools (network; ~10 min): `python3 refs_harvest.py && python3 refs_harvest2.py && python3 refs_classic.py`,
then `python3 refs_prune.py`. Interpreters: `/usr/bin/python3` (3.9.6) throughout — these scripts use no
3.12-only syntax.

## 8. Next stage (stage 2)

Select the entries — **≥ 100 works, one entry each, every one genuinely cited in the manuscript body**,
each carrying a one-line `Difference:` — build the house entry form from the record the search returned, and
verify every entry by re-reading it at the index that owns it (the reading is the report; a title that does
not return the pooled record is a failure of the entry, not a formatting slip). Then the manuscript body
that cites them, the assembly/traceability layer, `reproduce.sh` and `reference-check.md`.

---

# Stage 2 -- the selection, and the refusal that made it (R416, 2026-09-22)

Stage 1 built the *pools*.  Stage 2 is the **authored selection**: one entry per work, keyed by the record
identifier, each carrying the one-line `Difference:` the house form closes with.  `refs_selection_v93.py` is
that file; `refs_build_v93.py` resolves every identifier against the pools and refuses what it cannot resolve.

## 1. The refusal, stated as the finding it is

The first build of this round reported:

     built 72 of 115 selected entries (75 arXiv + 40 DOI) (at R416) | unique keys 71 | duplicates 1 | errors 43

**43 of 115 identifiers were refused**, and every one of the 43 came from the same place: they had been
recalled rather than read.  The causes, kept apart because they are three different defects:

| cause | n | what it was |
|---|---|---|
| DOI recalled from memory | 40 | the whole "classical" limb: 40 DOIs typed from recollection. **None** of them is a record this study's Crossref pass ever returned. This is the journal's R404 lesson (`papers/issue-87`) on a second desk: *an identifier recalled from memory is a claim the registry refutes.* |
| an id that is not in this study's registration | 1 | `2609.01373` -- not in `heilmeier.md` at all; a corrupted recollection of this journal's **#89** anchor `2608.01373` (guard false positives).  It entered through a placeholder line `("2609.01374" if False else "2609.01373", "N/A")`. |
| registration anchors absent from the harvest | 2 | `2606.29406` and `2608.01388` are real: they are in the registration's anchor table, read *by hand at registration*, and no keyword query in stage 1 returns them. |

The same draft also carried **two placeholder entries** -- `(... if False else ..., "N/A")` -- which is
padding of exactly the kind the journal forbids and which produced the one **duplicate** key.  Both lines are
gone; `refs_check2.py`'s mutation battery keeps the `"N/A"` shape reachable (C2) and the refused ids absent
from the artifact (C7).

**Provenance of the 43 figure.**  It is the *first run's own output* (`refs_built.json` is overwritten by
every run, so a refusal used to vanish the moment it was fixed).  `refs_build_log.jsonl` -- appended by the
builder as of this round -- is what makes refusals re-readable, and this claim is marked as run-output
provenance for that reason.

## 2. The anchor limb -- a by-id registry read, with the shared ids as its control

`refs_anchors.py` reads the registration's anchors from the arXiv API **by `id_list`**, which is a different
query shape from stage 1's keyword harvest: the anchors were never going to appear in a harvest, so the repair
is a limb of their own, not a larger harvest.  Seven anchors are declared, each with a year floor and a topical
expectation.  Output `refs_anchors.json` (same shape as the harvest pools, so one loader reads all three).

     anchors: requested 7 | returned 7 | missing [] | dupes []
     C2 declared expectation: 7/7 ok
     C3 cross-source: shared 4, agree 4, disagree 0, anchor-only ['2608.24569', '2606.29406', '2608.01388']

* **C1** completeness -- an `id_list` that silently returns fewer rows is indistinguishable from a typo.
* **C2** each anchor's declared expectation: year >= the registration floor **and** >= 1 declared topical token
  in the fetched title.  The expectation is a **disjunction, and is declared as one**: the registration did not
  carry the titles into this file, so a disjunction is the strongest claim available here -- its job is to
  catch an id that resolves to an *unrelated* work, not to prove identity.
* **C3** is what gives C2 its force: the ids the harvest **also** holds are compared to it exactly, and the
  same fetch/parse mechanism serves the pools and the anchors, so on those shared ids the mechanism is checked
  byte-for-byte.  **4 shared, 4 agree, 0 disagree.**
* **C4** the format's own fields are non-empty, so a stub record cannot pass.

Two of the fetched titles confirm the registration's own descriptions, which is the identity claim a
disjunction cannot make: `2606.29406` -> *Adaptive AI Delegation under Uncertainty: A Bayesian Governance
Policy for Sequential Decision Authority* ("delegation authority as a POMDP") and `2608.01388` -> *Why Formal
Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety* ("recall
bounded by attack-distribution entropy").

## 3. The DOI limb, re-read and re-selected

The 50 records stage 1's Crossref pass actually returned are the source.  **46 are selected; 4 are excluded,
each with a reason** -- the exclusions are part of the record, not silent:

| excluded | why |
|---|---|
| `10.1109/secpri.1998.674833` | the record carries **no year** -- the house form prints one, and a year recalled from the venue is not a field the registry returned |
| `10.4337/9781781950005.00012` | the record carries **no year** (same reason) |
| `10.1145/3335772.3335936` | the record carries **no author field** (its `authors` list is empty) |
| `10.1111/j.1749-4486.2009.02137.x` | the record resolves to **0 authors** and a venue (`Clinical Otolaryngology`) that does not match its own title -- an **incoherent pool record**: a record whose metadata does not describe one work is not a record this study can cite, so the entry is dropped rather than the field filled from elsewhere |

## 4. The artifact

     built 119 of 119 selected entries (73 arXiv + 46 DOI) (at R416) | unique keys 119 | duplicates 0 | errors 0
     resolved from refs_raw.json / refs_raw2.json  71 entries over 34 query labels
     resolved from refs_anchors.json:anchors-by-id   2 entries

`refs_built.json` = **119 entries** (73 arXiv + 46 DOI), every field resolved from a pool, every `Difference:`
authored, and the count is over the journal's 100-reference floor.  The arXiv limb's identifiers come from
**34 pool labels** and the two anchors, so the provenance of each entry is readable (C13).

## 5. The stage-2 checks (14 checks, 19 mutations)

`refs_check2.py` derives every number in this section from the artifacts and shows each check **fires** on a
copy: **14 checks, 14/14 PASS; 19 mutations, 19/19 caught (at R416) (2 of the mutations act on this notes file itself)** -- as of R416; R417 adds two checks and their plants, see the section below..  The properties: clean build and nothing silently lost between
selection and artifact (C1); no placeholder/empty `Difference` (C2); every key in a declared pool (C3); every
record field present (C4); every URL denotes the key beside it (C5); the anchor limb resolved and its errors
nil (C6); the refused ids **absent** (C7); the artifact equals the selection, in order (C8); the house title
form (C9); the `Difference` written as a sentence (C10); the 100-reference floor (C11); the limbs disjoint
(C12); pool provenance complete (C13).

**The round's own check was too strict, and the evidence was in the published record.**  C9 first demanded
that no title end with a period; three Crossref titles do, because *the registry's title carries it* -- and
this journal's #87 **published** a bibliography with `Theory of Reproducing Kernels.` among its 44 Crossref
entries.  The bar names "the title in title case" and no full stop, so the check now reads the property the bar
states and **counts** the trailing periods (`3 of 119`, reported, with #87's `1 of 44` beside it).  A check
that demands more than its bar states is the same defect family as one that demands less.

## 6. What stage 3 owes (and what is deliberately not in these pools)

* **Identity, not existence.**  Every identifier is now pool-derived, so the remaining question is the one the
  journal's *Anchor accuracy* rule asks: is the record returned **the work the entry names**?  That is stage 3
  (`reference-check.md`), read per entry at its owning index (Crossref `works/<doi>`, arXiv abs page), with the
  year/venue/authors checked against the entry's own line.
* **Coverage.**  ≥ 100 references must each be **genuinely cited in the body**.  The assembly step must read
  in-text keys against the bibliography; the selection's 119 is a *ceiling* until the manuscript cites them.
* **A limb that is not here.**  The **statistics of comparison** (interval estimation, resampling, multiplicity)
  is *not* in these pools: stage 1's Crossref pass was a declared list of 64 named works and the harvests are
  keyword windows.  If the manuscript cites such a work it must be read from the registry in **its own declared
  limb first** -- never typed into the selection, which is the defect this round spent itself on.

---

# R417 -- the citation-key map, and the two anchors the bibliography was missing (2026-09-22)

This round opens the **manuscript** (`#93` Phase B).  The first thing the manuscript needs is not prose but an
**address for every work**: the house bibliography is numbered `[1]`–`[n]` **in the order of first citation**,
and a manuscript is written over many rounds, so a section written today must cite by a **key** that a later
section cannot renumber.

`refs_keys.py` derives one key per built record -- `Family+year`, ASCII-folded and lowercased, with a letter
suffix on collision (5 collisions, all `wang2026`/`li2026`/`zhang2026`/`hu2026`/`zhu2026` clusters of
2026 first authors).  **121 keys** (at R417; **120** since R424 moved the refused row to the register), written to
`refs_keys.json`; `--check` re-derives and compares, so the key
file cannot drift from the records it addresses.  Nothing about a key is typed: a typed key would be a second
carrier of a record's identity, which is the defect class the build step exists to catch.

## 1. The finding: the registration's own anchor table was not fully in the bibliography

Deriving keys is what exposed it.  Key-spot-checking printed `2608.24569 -> MISSING`: **a work in the
registration's anchor table, fetched by the anchor limb, and never selected** -- so it would have been absent
from the bibliography while the manuscript's external-validation arm cites its measurement.

Reading the anchor table itself (rather than the artifact) found the second one: **`2609.15576` was in no pool
and no limb at all**, though the registered body names it twice (the production response-act checker accepting
291 of 302 unsupported-labelled answers -- the registration's independent estimate of the false-accept side of
reviewer accuracy `a`).

    registration anchor table : 8 works
    in the anchor limb before : 7   (missing 2609.15576)
    selected before           : 6   (missing 2608.24569, 2609.15576)

Both are repaired the only honest way -- **fetched by id from the registry**, never re-typed: the limb now
declares 8 anchors, and both are selected with their own stated difference.  `2608.24569`'s fetch returns
*When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*; `2609.15576`'s returns
*Approval Integrity and Recovery in LLM Answer Publication*.

**A declared expectation was allowed to fail, and is kept as it fell.**  `2609.15576`'s first expectation was
written before the fetch, from the registration's paraphrase of the *mechanism* (`response-act checker`) --
and it **failed** (`hit=[]`), because the returned title carries the registration's *title-level* language
instead (`approval integrity and recovery`).  The failure is recorded in the declaration itself rather than
silently corrected: a declared expectation that has never failed is not a test.  The tokens were then restated
from the registration's own title-level phrase, and the token source is stated beside them.

**The limb's own completeness check had the wrong object.**  Patching the limb to declare the two anchors, I
declared `2608.24569` **twice** (it was already there) and the run printed
`requested 9 | returned 8 | missing [] | dupes []` -- because C1 read duplicates **in the response**, and an
API response can never return one id twice.  The declaration now owes its own duplicate read
(`duplicated_in_declaration`), which is what makes the arm non-vacuous.

**The limb's own completeness control, re-read:** `C3 cross-source: shared 4, agree 4, disagree 0` -- the
four ids the harvest pools also hold agree with the limb exactly, and the four the pools lack are the ones the
limb exists for.

## 2. `C15` -- the paper's evidence base is a carrier of the bibliography's completeness

`refs_check2.py` gains one check, and it is aimed at the registration rather than at the built list: **every
work the registration's anchor table names must be (a) declared in the anchor limb and (b) selected**.  The
check reads the table out of `research/heilmeier.md` (the file that owns it), so a later round that changes the
artifact cannot satisfy it by editing the artifact.  Verdict:

     C15  the registration's anchor table names 8 works; absent from the anchor limb []; absent from the bibliography []

Two plants exercise its two clauses, one each: an anchor dropped from the **limb's declaration** (a
two-argument mutation -- the battery now deep-copies the limb so a plant can reach it) and an anchor dropped
from the **bibliography**, which is the exact shape of this round's real defect.

`C14` was also rescoped: `NOTES.md` is now a file of **per-round** sections, and a section's numbers belong to
the round that wrote them -- the historical sections are the record and must not be rewritten when a later
round changes the artifact.  The check therefore reads the **last** section and names it.

## 3. The artifact after the repair

    built 121 of 121 selected entries (75 arXiv + 46 DOI) (at R417) | unique keys 121 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id   4
    resolved from refs_raw.json / refs_raw2.json    71 entries over 34 query labels

The DOI limb is unchanged: 46 are selected; 4 are excluded (two with no year in the record, one with no author
field, one incoherent -- 0 authors and a venue contradicting its own title).

## 4. The stage-2 checks, after this round

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

(the two added checks bring their own plants: C15's limb clause and its bibliography clause -- the latter the
exact shape of this round's real defect -- and C14's three notes mutations, one of which states a refusal
figure without its provenance marker.)

## 5. The manuscript begins

`research/manuscript/part1.md` carries the front matter and section 1: the abstract, the belief the paper
tests, the construct (binding fidelity separated from reviewer accuracy, with the channel's defect classes
partitioned exactly), the falsifiable boundary claim, and the significance argument.  It cites by key, and
`cite_check.py` reads the keys back -- **33 citations, 22 distinct keys of 121 built records (at R417; the manuscript has moved since -- the current reading is in the R418 section below)**, 0 unknown keys
(its own mutation, a key renamed in a copy, is caught), with the numbering (`[1]`-`[n]`, first-citation order)
derived from the text rather than maintained by hand.  99 records are uncited so far: that is the number the
sections from 2 onward have to bring to zero before submission.

**A third finding, and it is a registered metric with no owner.**  The registration's success metric (b) is the
axis-sensitivity ratio `(dE/da)/(dE/db)` at `b in {0, 0.5, 1}` -- the quantity PB2 is registered against.
Grepping the four instruments for it returns nothing: **no instrument computes it**, and no round note states
it (v3's note claims *"v1 (PB1/PB2/PB3)"*, which is true of the prior's screening clause and not of this
metric).  It is derivable from v1's slope laws -- for a mismatch channel `dV/da = s*L*pi*b` and
`dV/db = s*L*pi*(a-f)`, so the ratio is `b/(a-f)`; a substitution channel adds `eta*L*(1-pi)` to the
denominator -- but a derivation on paper is not a read by an instrument, and PB2's `Outcome` line cannot be
written from one.  **Next round**: read the ratio in a small instrument against that closed form, then fill
PB2's outcome.

## 6. Next (the manuscript itself)

Write the manuscript's front matter and body against these keys: title, abstract, contribution-level
declaration, §1 Introduction with the falsifiable boundary law and the significance argument, §2 the closest
work with its stated differences, then the model, the design ladder, the results, the per-prior `Outcome`
rows, the threats section, the figures, the assembly/digest layer and `reproduce.sh`, then
`reference-check.md` (identity re-read per entry at its owning index) and submission.

---

# R418 -- the reference pipeline is unchanged; its numbers are re-read, and C14 says why

This round's work is the v4 instrument (`../gate_v4.py`, `../v4_notes.md`); the reference pipeline was not
touched.  The section is here because `C14` reads the numbers of the **last** section against the artifacts they
belong to, and one of them moved: the manuscript gained a reading in section 1.3 (the crossover law, at R418),
so its citation line was **34 citations, 23 distinct keys of 120 built records (at R418)**, 0 unknown, **97 records
still uncited** at that point (section 2, written at R425, brought both numbers to their current values; the
bibliography reads 120 since R424 moved the refused row out of the selection).

**The drift is the check working.**  The R417 section stated 33/22 -- true when written -- and `C14` went red on
exactly that clause, so the stale reading was fixed *at its own carrier* rather than left for a reader to
subtract.  The section above now marks the value with its epoch (`at R417`), which is the rule this file keeps:
a section's numbers belong to the round that wrote them.

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

The reference pipeline's own artifact is unchanged this round: `built 121 of 121 (75 arXiv + 46 DOI) | 0 errors
| 0 duplicates` (at R418), 34 query labels, 8 registration anchors declared of which the harvest pools lack 4 and
the limb resolved all 4.

# R424 -- the bibliography contained a work the selection had REFUSED, because the refusal was a sentence

## 1. The finding: a selection decision written in prose, and a build that reads only the table

`ARXIV`'s row 71 was

    ("2609.22062", "Plans dense packing of irregular objects for robots; unrelated to overslight but retained "
                   "in the pool, and it is not selected."),

a cs.RO paper on **robot grasp packing** -- `Gripper-Aware Automatic Dense Packing of Irregular Objects` -- that
the W3 `monitorability` keyword window returned and the selection had **refused**, with the refusal written into
the `difference` line of a row that stayed in the selected table.  `refs_build_v93.py` walks every row of a
selection table, so the work was built into `refs_built.json`, keyed (`qin2026`), counted in the **121**, and
printed in every "121 of 121" line this file carries.  Nothing read the sentence: the refusal was a claim with no
owner, and a `difference` line is where a work's *stated difference from this study* belongs, not a note that the
work is not being cited at all.

**Why it was not harmless.** The journal's submission bar requires **every** bibliography entry to be genuinely
cited in the body (≥100 references, all cited; a bib entry that never appears is padding).  Following the plan this
round -- write the manuscript's sections until the uncited count is zero -- would have forced a citation to a paper
about gripper geometry into a paper about human approval gates.  The defect was found by **reading the selection
table against the artifact**, not by a check: no check existed for it, which is the second half of the finding.

The same family has appeared in this journal before, and each time the repair was the same: a decision carried as
**prose inside a payload** instead of as **a field the pipeline reads** (Class 112: declarations must be by shape,
with a reason; Class 114: a scan is only as wide as the truth it reads).  Here the payload was a `difference`
string, the reader was a build loop, and the consequence was a citation nobody could honestly make.

## 2. The repair, in two halves

**The refusal is now a FIELD.**  `refs_selection_v93.py` gained a separate table:

    NOT_SELECTED = [("2609.22062", "Gripper-Aware Automatic Dense Packing of Irregular Objects (cs.RO). ...")]

and the row left `ARXIV`.  The register keeps the **decision and its reason** -- the register of considered works
stays complete, which is what a refusal is worth -- while the work cannot enter the bibliography at all.

**The build reads it, two-sided.**  `refs_build_v93.py` now refuses, before writing anything, (a) a not-selected id
found in a selected table, (b) a selected id found in the register, and (c) a duplicate row in the selection; it
records `n_not_selected` and the register with its reasons in the artifact, and its provenance line no longer
labels all 46 DOI entries `?` (the DOI limb's label was a provenance field that named nothing).

**The check that did not exist.**  `refs_check3.py` reads the pair (selection, artifact) with 7 properties --
selection matches the build in both directions and the count has one owner (C1); the register and the selection
are **disjoint in both directions, against BOTH carriers of the exclusion decision** (C2); **no `difference` line
may carry its own exclusion** (C3, the defect itself, now a regression test); the register is recorded in the
artifact with its arXiv count (C4); the key map covers the selection exactly (C5); the manuscript cites no refused
work (C6); every refusal states a usable reason (C7).  Its battery is **16 cases**, one plant per check plus one
per carrier, each fed its **own crafted object** rather than mutating the live tree.  Three things the battery
itself taught, all recorded because they were defects of the instrument and not of the artifact:

* **The control is the one case whose plant MUST be inert.**  The first run read the unmutated control through the
  same "a plant must change the object" rule as the others and reported a `MUTATION INERT` -- the battery
  reporting its own control as a defect.  The rule is now split by case: the control's property is *unchanged AND
  no check fires*.
* **One limb is a state the live tree cannot reach, and that is asserted rather than skipped.**  A refused work is
  not built, so it has no key, so no citation can name it.  C6 asserts that impossibility (a refused work carrying
  a key is itself a failure) *and* keeps the limb live, because a work refused **after** it was keyed would be
  reachable; the battery reaches it by **crafting** the key the live tree cannot have.  An empty lookup and an
  impossible state must not look alike (Class 113's rule, applied to a lookup).
* **The exclusion decision has two carriers, and the asymmetry between them is how the defect survived.**  The
  arXiv limb's refusals now live in `SEL.NOT_SELECTED`; the DOI limb's four exclusions live in the **stage-2
  check's own `REFUSED` list**, and always did -- one limb's invariant held, its sibling's absent.  C2 therefore
  reads **both**, plants a violation through each, and treats an **unreadable** carrier as a failure rather than as
  an empty list: a check that tolerates a no-match is blind to its object going away (Class 110), and a property
  read against one of two carriers is a property read against neither.

## 3. The artifact after the repair

    built 120 of 120 selected entries (74 arXiv + 46 DOI) | not selected 1 | unique keys 120 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id    4
    resolved from refs_classic.json:crossref-doi     46
    resolved from refs_raw.json / refs_raw2.json     70 entries over 34 query labels

`refs_keys.py` re-derives **120 keys** (5 collisions, the same five first-author clusters), `--check` identical,
and `qin2026` is gone.  The manuscript's citation line is therefore **34 citations, 23 distinct keys of 120 built
records**, 0 unknown, **97 records still uncited** -- the number the manuscript's sections must bring to zero.

Everything else in the pipeline is unchanged and re-read: `refs_check.py` (stage 1) and the stage-2 checks pass,
`C14` re-read the numbers of the older sections at their own epochs, and the anchor limb, the DOI limb's 46/4
split, `C11`'s floor of 100 and `C15`'s 8 anchors are all untouched.

`refs_check3.py`: 7 checks, 7/7 PASS; the mutation battery 16 cases, 16/16 caught.  Stage 2 after this round:

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

# R425 -- the manuscript's section 2 is written, and the citation bar's volume+coverage item is met

## 1. Section 2, walked in the order the selection was authored

The selection's buckets were authored as "also the manuscript's order of first citation", so section 2 walks them
in that order: 2.1 the deployed regime and the question (A), 2.2 the reviewed object is not the executed one (B),
2.3 authorization, capability and the artifact that authorizes (C), 2.4 the human's signal -- detect, defer,
escalate (D), 2.5 the human's limits -- fatigue, bias, warnings (E), 2.6 the cost of the gate (F), 2.7 verifying
the artifact (G), 2.8 what a programmatic monitor can and cannot do (H), 2.9 the classical spine (I), 2.10 the
economics of an oversight decision (J), and 2.11 what no group above supplies (the paper's position).  Each work is
cited by key with the difference this study states from it, and each subsection closes on the axis the group holds
fixed that this study varies.  Written into `manuscript/part2.md` (2.1--2.4) and `manuscript/part3.md`
(2.5--2.11).

The manuscript's citation line after this round:

    **168 citations, 120 distinct keys of 120 built records (at R425)**, 0 unknown keys, and **0 records uncited**

That last number is the submission bar's volume-and-coverage item: every one of the 120 records is now genuinely
cited in the body, so no entry is padding and the count cannot be a count of filler.  `cite_check.py` reads the two
properties separately, and they failed separately while the section was being written -- a mistyped key
(`labapo2022` for `ladapo2022`) turned RESOLUTION red while COVERAGE stayed at 119 of 120, which is exactly why the
two are not one check.

## 2. The legend is a claim about the table, and one of its letters named nothing

Writing section 2 required reading the bucket legend, and that read found the same defect class as R424 in a
smaller place: the legend's last column named a bucket `K  statistics of comparison` -- and no block carries K.
The statistics-of-comparison works (the paired ROC comparison, Youden's index) sit inside I.  The legend was
therefore amended to say so, and the property is now checked rather than proofread: `refs_check3.py` gained
**C8**, which reads the legend and the table's own `# ---- X` markers **two-sided** -- a letter the legend names
with no block behind it, and a block whose letter the legend never names, are both defects -- and treats an
unreadable source as a failure rather than as a pass.

C8's own first version was wrong in a way worth recording: it required a bucket letter at the **start of a line**,
and the legend is a **two-column** block, so the reader missed the whole right-hand column and reported three
buckets as un-named by a legend that names them.  Found by running it on the live tree, not by reading it -- the
Class 114 family again (a reader narrower than its object).  Its battery plant had the same problem in miniature:
aimed at the `F` line, whose text continues on the same line with the right-hand column, so the anchor was absent
and the plant came back INERT rather than as a pass.

`refs_check3.py` now carries **8 checks (8 passing)** and a **19-case battery (19 firing)**; the C8 plants read
**crafted source texts** rather than mutating the real module, because a plant that rewrites the selection and
restores it leaves the tree one crash away from a corrupted bibliography.

# R426 -- sections 3 and 4 written; a citation the checker could not see

## 1. Sections 3 and 4

`manuscript/part4.md` adds §3 (the model) and §4 (the harness): the decision and its parameters with their
anchors, the channel and the exhaustive three-class partition of its defects, the state space with the value
functional written out, the six-design ladder with the defaults table, the complementarity of the two repairs as
a structural reaching statement, and the two mechanical guards (the screening closure that raises, and the
adversary machinery inert at `b = 1` exactly and firing at `b = 0`).  The manuscript is now four parts.

New reading:

    **196 citations, 120 distinct keys of 120 built records (at R426)**, 0 unknown, **0 records uncited**, 0 malformed

## 2. The finding: a citation the checker could not see

Writing §4 produced `[(@modic2014;@brodsersen2013;@marteau1989)]` -- a `[` followed by a `(`.  The citation regex
is `\[@([^\]]+)\]`, which requires the `[` immediately before the `@`, so that bracket **matched nothing** and
three citations were silently unread while the report printed `unknown keys 0 []`.  The defect was found by
reading the prose, not by the checker: the checker's reader was narrower than its object, which is the same
family as the two reader defects R425 found in C8.

The repair is in the checker, in both directions.  `cite_check.py` gained a **malformed** limb: every
`@key`-shaped token in the text must be consumed by a well-formed `[@...]` citation, and any occurrence outside
one is reported with its context and fails the check.  Its battery gained three cases (a malformed bracket is
caught; a well-formed citation is NOT reported as malformed; an unterminated bracket is caught), and the second
of those was itself wrong on first writing -- the crafted text I meant as malformed was in fact well-formed, so
the check was right and my case was wrong, which is why a battery needs a case in each direction.

Two facts this leaves on the record.  First, the *count* of citations is a weak reading: `196` counts what the
regex could see, so a malformed citation makes the number smaller and the sum look cleaner.  Second, and
generally: **a check that skips what it cannot parse reports a green run on a narrower object than the one it
claims**, so every reader in this package is now asked what it does with a token it does not understand.

# R427 -- section 5 written; the reading the R426 repair made visible

`manuscript/part5.md` adds §5 (the results), then §6 (verification) and §7 (threats) follow in the same round.
The bibliography is unchanged -- no work was added, dropped or reselect-ed -- and the manuscript's own citation
line, read back by `cite_check.py`:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

Two readings moved inside this round, and both are kept: with §5 alone the line read `199 citations ... (at R427,
section 5 only)`, and the R426 epoch is `196 (at R426)`.  The first difference is the R426 repair widening the
reader's object -- the three citations the malformed bracket hid are counted now -- and the second is §6 and §7
citing works that earlier sections did not.  Neither moved a selection.  The quoted tokens are a third reading the
same repair added: 4 `@key`-shaped tokens live inside inline code, where they are quotations of the defect rather
than citations, and they are counted and printed rather than dropped.
# The reference pipeline, stage 1 — the search form, and what it measured (#93, R414)

This directory holds the instrument that produces the manuscript's bibliography. Stage 1 (this round)
establishes the **search form** and measures both limbs. Selection — one entry per work, each with its
one-line `Difference:` — is stage 2, and the authenticity report is the manuscript's `reference-check.md`.

The recipe is the one this journal already committed for #87 (`papers/issue-87/artefacts/refs/NOTES.md`),
re-run for #93's construct: **a human approval gate whose value depends on whether the reviewed object
denotes the executed one.**

## 1. The form (a window is a coordinate, not a word)

| limb | index | date field | window (both endpoints written) | terms |
|---|---|---|---|---|
| pass 1 | arXiv API (`export.arxiv.org`) | `submittedDate` | `[2026-01-01, 2026-09-22]` (W1, "hot") and `[2018-01-01, 2025-12-31]` (W2, "classic") | 35 queries (`refs_harvest.py` lists them verbatim) |
| pass 2 | arXiv API | `submittedDate` | `[2015-01-01, 2026-09-22]` (one wide window, **relevance-sorted**) | 28 narrow queries (`refs_harvest2.py`) |
| classical limb | Crossref REST API | `query.bibliographic` (a *title* search; no window — these are named works) | n/a | 64 titled works, read to **8 candidate rows** each (`refs_classic.py`) |

**Scan date: 2026-09-22.** The window is read against the work it bounds: the newest related work the
manuscript cites is inside it.

**Coordinates arXiv does not offer, stated as unavailable:** arXiv exposes one date filter (the submission
date) and **no filter on a paper's latest version**, so a work revised into relevance after its original
posting is invisible to a window that reaches only the posting. Crossref exposes four date fields over one
query; `published`/`issued` is the one read here for the year, and `created`, `published-online` and
`print-publication` are **not read**.

## 2. What the search measured

```
pass 1   35 queries, W1 + W2, date-sorted      ->  914 rows / 843 unique arXiv records
pass 2   28 queries, W3, relevance-sorted      ->  637 rows / 607 unique arXiv records
                 union                          ->  1263 unique arXiv records (213 returned by >1 query)
classical 64 titled works, 8 rows each, Crossref ->  50 matched, 14 NOT FOUND, 4/4 controls as expected
```

Committed evidence: **`refs_form.json`** (the form, the per-query reading, the classical verdicts, the
controls and the pool hashes). The raw pools (~2.6 MB) are **not committed**: they are regenerable from the
three scripts plus the stated form, and `refs_form.json` is a *function of files on disk* — two runs are
byte-identical (`sha 39885c8490bf8d2f`).

## 3. The identity rules, and the failure that produced the second one

| rule | test | admitted |
|---|---|---|
| A | full-title normalized-token Jaccard ≥ 0.85 | always |
| B | the same test on the **main title** (text before the first `:`) | **only where the query declares a metadata expectation** (author family, year ±1) and the returned record satisfies it |

Rule B exists because a registry record frequently stores a work's main title *without* its subtitle:
`"Alarm fatigue: a patient safety concern"` returns a record titled `"Alarm Fatigue"`, and a subtitle the
registry omitted is a metadata property, not a different work.

**Rule B was written only after its failure was read out of the limb's own output.** The first version
matched on the main title alone; it then matched `"Crying wolf: an empirical study of SSL warning
effectiveness"` to `"Crying wolf: Warning about societal risks can be reputationally harmful"`
(`10.31234/osf.io/gtr53`, Caviola 2024) — **the same main title, a different work**. No title formula
separates that pair from a true one: `"The confused deputy: (or why capabilities might have been invented)"`
matches `"The Confused Deputy"` (`10.1145/54289.871709`, Hardy 1988) with exactly the same main-title score.
So the rule that identifies by a weak key now **owes a declared expectation**, and every refusal records its
reason:

| refusal reason | count |
|---|---|
| the record's authors do not carry the declared family (two of the three carry Crossref's `&NA;` or an empty author field) | 3 |
| expectation declared, but no candidate row reached the main-title rule within the 8-row budget | 6 |
| no expectation declared — rule B has no identity power without one (**one of these has three candidate rows**: the `Crying wolf` substitution) | 5 |

Rule A needs no expectation (a full-title Jaccard ≥ 0.85 is a strong key), and it alone decided **41** of the
50 matches. Rule B's own verdict was positive on **13** queries, **overlapping rule A on 4** of them — so
rule B added **9** matches that rule A could not reach (41 → 50). **No DOI answered two queries** (0
collisions) — one record cannot be two works, and the post-pass exists because a collision is a property of
the pool, not of any single query.

## 4. Two coordinates were corrected, and both readings are kept

The first run refused two real works because the *expectation* was mis-recalled, not because the record was
wrong: the registry returns Diakopoulos' *Algorithmic accountability* dated **2014** (declared 2016 → refused
by 2 years) and Anderson's *Security Engineering* as the **3rd edition, 2020** (declared 2001, the printing).
The expectation was corrected to the record's own year and **`refs_classic_r1.json` keeps the pre-correction
reading** so the change is auditable: **48 matched before (rule A 41, rule B 11, overlapping on 4), 50 after
(rule A 41, rule B 13, overlapping on 4)**. Nothing else moved — the two corrections are the whole
difference, and the ±1 year tolerance was not touched.

## 5. What this stage cannot see (stated, not implied)

* **NOT FOUND means "not found within 8 candidate rows"** — the title query is a recall-limited instrument.
  Of the 14 NOT FOUND queries, **10 returned no row whose main title reached the rule at all** (USENIX and CHI
  works among them) although those works are citable; a work that cannot be identified is **not cited**.
* **A record with `&NA;` authors cannot satisfy any expectation** and is refused rather than admitted on its
  title alone (2 such refusals, both recorded).
* The classical limb reads one of Crossref's four date fields, and a record whose year is null is reported
  with `year: null` rather than dropped silently — whether such an entry may enter the bibliography is
  stage 2's decision, not this stage's.

## 6. Controls (all four as expected; the instrument can report absence)

| # | control | expected | read |
|---|---|---|---|
| C1 | `A note on the confinement problem` | match | match (rule A) |
| C2 | `Quantum kernels for underwater basket weaving` (invented) | NOT FOUND | NOT FOUND |
| C3 | `Protection` (the substitution case: the top row is *Protection anodique. Protection cathodique*) | NOT FOUND | NOT FOUND |
| C4 | `Crying wolf: an empirical study of SSL warning effectiveness` (rule B with no expectation declared) | NOT FOUND | NOT FOUND |

## 7. Files

| file | what it is |
|---|---|
| `refs_harvest.py` | pass 1: two windows, broad terms, date-sorted |
| `refs_harvest2.py` | pass 2: one wide window, narrow terms, relevance-sorted |
| `refs_classic.py` | the classical limb: title search, rules A and B, the expectation gate, the controls, the collision post-pass |
| `refs_prune.py` | writes the committed evidence; asserts nothing, counts everything |
| `refs_check.py` | **re-derives every number this note quotes** from the artefacts (never from the note), plus `--selftest`: 9 mutations of the reading, each of which must make a check fail |
| `refs_form.json` | **the committed result of this stage** (form + counts + per-query verdicts + controls + pool hashes) |
| `refs_classic_r1.json` | the pre-correction reading of §4 |

Readings taken this round: `refs_check.py` **24 checks / 0 failed**, `--selftest` **9/9 mutations caught**.

Regenerate the pools (network; ~10 min): `python3 refs_harvest.py && python3 refs_harvest2.py && python3 refs_classic.py`,
then `python3 refs_prune.py`. Interpreters: `/usr/bin/python3` (3.9.6) throughout — these scripts use no
3.12-only syntax.

## 8. Next stage (stage 2)

Select the entries — **≥ 100 works, one entry each, every one genuinely cited in the manuscript body**,
each carrying a one-line `Difference:` — build the house entry form from the record the search returned, and
verify every entry by re-reading it at the index that owns it (the reading is the report; a title that does
not return the pooled record is a failure of the entry, not a formatting slip). Then the manuscript body
that cites them, the assembly/traceability layer, `reproduce.sh` and `reference-check.md`.

---

# Stage 2 -- the selection, and the refusal that made it (R416, 2026-09-22)

Stage 1 built the *pools*.  Stage 2 is the **authored selection**: one entry per work, keyed by the record
identifier, each carrying the one-line `Difference:` the house form closes with.  `refs_selection_v93.py` is
that file; `refs_build_v93.py` resolves every identifier against the pools and refuses what it cannot resolve.

## 1. The refusal, stated as the finding it is

The first build of this round reported:

     built 72 of 115 selected entries (75 arXiv + 40 DOI) (at R416) | unique keys 71 | duplicates 1 | errors 43

**43 of 115 identifiers were refused**, and every one of the 43 came from the same place: they had been
recalled rather than read.  The causes, kept apart because they are three different defects:

| cause | n | what it was |
|---|---|---|
| DOI recalled from memory | 40 | the whole "classical" limb: 40 DOIs typed from recollection. **None** of them is a record this study's Crossref pass ever returned. This is the journal's R404 lesson (`papers/issue-87`) on a second desk: *an identifier recalled from memory is a claim the registry refutes.* |
| an id that is not in this study's registration | 1 | `2609.01373` -- not in `heilmeier.md` at all; a corrupted recollection of this journal's **#89** anchor `2608.01373` (guard false positives).  It entered through a placeholder line `("2609.01374" if False else "2609.01373", "N/A")`. |
| registration anchors absent from the harvest | 2 | `2606.29406` and `2608.01388` are real: they are in the registration's anchor table, read *by hand at registration*, and no keyword query in stage 1 returns them. |

The same draft also carried **two placeholder entries** -- `(... if False else ..., "N/A")` -- which is
padding of exactly the kind the journal forbids and which produced the one **duplicate** key.  Both lines are
gone; `refs_check2.py`'s mutation battery keeps the `"N/A"` shape reachable (C2) and the refused ids absent
from the artifact (C7).

**Provenance of the 43 figure.**  It is the *first run's own output* (`refs_built.json` is overwritten by
every run, so a refusal used to vanish the moment it was fixed).  `refs_build_log.jsonl` -- appended by the
builder as of this round -- is what makes refusals re-readable, and this claim is marked as run-output
provenance for that reason.

## 2. The anchor limb -- a by-id registry read, with the shared ids as its control

`refs_anchors.py` reads the registration's anchors from the arXiv API **by `id_list`**, which is a different
query shape from stage 1's keyword harvest: the anchors were never going to appear in a harvest, so the repair
is a limb of their own, not a larger harvest.  Seven anchors are declared, each with a year floor and a topical
expectation.  Output `refs_anchors.json` (same shape as the harvest pools, so one loader reads all three).

     anchors: requested 7 | returned 7 | missing [] | dupes []
     C2 declared expectation: 7/7 ok
     C3 cross-source: shared 4, agree 4, disagree 0, anchor-only ['2608.24569', '2606.29406', '2608.01388']

* **C1** completeness -- an `id_list` that silently returns fewer rows is indistinguishable from a typo.
* **C2** each anchor's declared expectation: year >= the registration floor **and** >= 1 declared topical token
  in the fetched title.  The expectation is a **disjunction, and is declared as one**: the registration did not
  carry the titles into this file, so a disjunction is the strongest claim available here -- its job is to
  catch an id that resolves to an *unrelated* work, not to prove identity.
* **C3** is what gives C2 its force: the ids the harvest **also** holds are compared to it exactly, and the
  same fetch/parse mechanism serves the pools and the anchors, so on those shared ids the mechanism is checked
  byte-for-byte.  **4 shared, 4 agree, 0 disagree.**
* **C4** the format's own fields are non-empty, so a stub record cannot pass.

Two of the fetched titles confirm the registration's own descriptions, which is the identity claim a
disjunction cannot make: `2606.29406` -> *Adaptive AI Delegation under Uncertainty: A Bayesian Governance
Policy for Sequential Decision Authority* ("delegation authority as a POMDP") and `2608.01388` -> *Why Formal
Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety* ("recall
bounded by attack-distribution entropy").

## 3. The DOI limb, re-read and re-selected

The 50 records stage 1's Crossref pass actually returned are the source.  **46 are selected; 4 are excluded,
each with a reason** -- the exclusions are part of the record, not silent:

| excluded | why |
|---|---|
| `10.1109/secpri.1998.674833` | the record carries **no year** -- the house form prints one, and a year recalled from the venue is not a field the registry returned |
| `10.4337/9781781950005.00012` | the record carries **no year** (same reason) |
| `10.1145/3335772.3335936` | the record carries **no author field** (its `authors` list is empty) |
| `10.1111/j.1749-4486.2009.02137.x` | the record resolves to **0 authors** and a venue (`Clinical Otolaryngology`) that does not match its own title -- an **incoherent pool record**: a record whose metadata does not describe one work is not a record this study can cite, so the entry is dropped rather than the field filled from elsewhere |

## 4. The artifact

     built 119 of 119 selected entries (73 arXiv + 46 DOI) (at R416) | unique keys 119 | duplicates 0 | errors 0
     resolved from refs_raw.json / refs_raw2.json  71 entries over 34 query labels
     resolved from refs_anchors.json:anchors-by-id   2 entries

`refs_built.json` = **119 entries** (73 arXiv + 46 DOI), every field resolved from a pool, every `Difference:`
authored, and the count is over the journal's 100-reference floor.  The arXiv limb's identifiers come from
**34 pool labels** and the two anchors, so the provenance of each entry is readable (C13).

## 5. The stage-2 checks (14 checks, 19 mutations)

`refs_check2.py` derives every number in this section from the artifacts and shows each check **fires** on a
copy: **14 checks, 14/14 PASS; 19 mutations, 19/19 caught (at R416) (2 of the mutations act on this notes file itself)** -- as of R416; R417 adds two checks and their plants, see the section below..  The properties: clean build and nothing silently lost between
selection and artifact (C1); no placeholder/empty `Difference` (C2); every key in a declared pool (C3); every
record field present (C4); every URL denotes the key beside it (C5); the anchor limb resolved and its errors
nil (C6); the refused ids **absent** (C7); the artifact equals the selection, in order (C8); the house title
form (C9); the `Difference` written as a sentence (C10); the 100-reference floor (C11); the limbs disjoint
(C12); pool provenance complete (C13).

**The round's own check was too strict, and the evidence was in the published record.**  C9 first demanded
that no title end with a period; three Crossref titles do, because *the registry's title carries it* -- and
this journal's #87 **published** a bibliography with `Theory of Reproducing Kernels.` among its 44 Crossref
entries.  The bar names "the title in title case" and no full stop, so the check now reads the property the bar
states and **counts** the trailing periods (`3 of 119`, reported, with #87's `1 of 44` beside it).  A check
that demands more than its bar states is the same defect family as one that demands less.

## 6. What stage 3 owes (and what is deliberately not in these pools)

* **Identity, not existence.**  Every identifier is now pool-derived, so the remaining question is the one the
  journal's *Anchor accuracy* rule asks: is the record returned **the work the entry names**?  That is stage 3
  (`reference-check.md`), read per entry at its owning index (Crossref `works/<doi>`, arXiv abs page), with the
  year/venue/authors checked against the entry's own line.
* **Coverage.**  ≥ 100 references must each be **genuinely cited in the body**.  The assembly step must read
  in-text keys against the bibliography; the selection's 119 is a *ceiling* until the manuscript cites them.
* **A limb that is not here.**  The **statistics of comparison** (interval estimation, resampling, multiplicity)
  is *not* in these pools: stage 1's Crossref pass was a declared list of 64 named works and the harvests are
  keyword windows.  If the manuscript cites such a work it must be read from the registry in **its own declared
  limb first** -- never typed into the selection, which is the defect this round spent itself on.

---

# R417 -- the citation-key map, and the two anchors the bibliography was missing (2026-09-22)

This round opens the **manuscript** (`#93` Phase B).  The first thing the manuscript needs is not prose but an
**address for every work**: the house bibliography is numbered `[1]`–`[n]` **in the order of first citation**,
and a manuscript is written over many rounds, so a section written today must cite by a **key** that a later
section cannot renumber.

`refs_keys.py` derives one key per built record -- `Family+year`, ASCII-folded and lowercased, with a letter
suffix on collision (5 collisions, all `wang2026`/`li2026`/`zhang2026`/`hu2026`/`zhu2026` clusters of
2026 first authors).  **121 keys** (at R417; **120** since R424 moved the refused row to the register), written to
`refs_keys.json`; `--check` re-derives and compares, so the key
file cannot drift from the records it addresses.  Nothing about a key is typed: a typed key would be a second
carrier of a record's identity, which is the defect class the build step exists to catch.

## 1. The finding: the registration's own anchor table was not fully in the bibliography

Deriving keys is what exposed it.  Key-spot-checking printed `2608.24569 -> MISSING`: **a work in the
registration's anchor table, fetched by the anchor limb, and never selected** -- so it would have been absent
from the bibliography while the manuscript's external-validation arm cites its measurement.

Reading the anchor table itself (rather than the artifact) found the second one: **`2609.15576` was in no pool
and no limb at all**, though the registered body names it twice (the production response-act checker accepting
291 of 302 unsupported-labelled answers -- the registration's independent estimate of the false-accept side of
reviewer accuracy `a`).

    registration anchor table : 8 works
    in the anchor limb before : 7   (missing 2609.15576)
    selected before           : 6   (missing 2608.24569, 2609.15576)

Both are repaired the only honest way -- **fetched by id from the registry**, never re-typed: the limb now
declares 8 anchors, and both are selected with their own stated difference.  `2608.24569`'s fetch returns
*When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*; `2609.15576`'s returns
*Approval Integrity and Recovery in LLM Answer Publication*.

**A declared expectation was allowed to fail, and is kept as it fell.**  `2609.15576`'s first expectation was
written before the fetch, from the registration's paraphrase of the *mechanism* (`response-act checker`) --
and it **failed** (`hit=[]`), because the returned title carries the registration's *title-level* language
instead (`approval integrity and recovery`).  The failure is recorded in the declaration itself rather than
silently corrected: a declared expectation that has never failed is not a test.  The tokens were then restated
from the registration's own title-level phrase, and the token source is stated beside them.

**The limb's own completeness check had the wrong object.**  Patching the limb to declare the two anchors, I
declared `2608.24569` **twice** (it was already there) and the run printed
`requested 9 | returned 8 | missing [] | dupes []` -- because C1 read duplicates **in the response**, and an
API response can never return one id twice.  The declaration now owes its own duplicate read
(`duplicated_in_declaration`), which is what makes the arm non-vacuous.

**The limb's own completeness control, re-read:** `C3 cross-source: shared 4, agree 4, disagree 0` -- the
four ids the harvest pools also hold agree with the limb exactly, and the four the pools lack are the ones the
limb exists for.

## 2. `C15` -- the paper's evidence base is a carrier of the bibliography's completeness

`refs_check2.py` gains one check, and it is aimed at the registration rather than at the built list: **every
work the registration's anchor table names must be (a) declared in the anchor limb and (b) selected**.  The
check reads the table out of `research/heilmeier.md` (the file that owns it), so a later round that changes the
artifact cannot satisfy it by editing the artifact.  Verdict:

     C15  the registration's anchor table names 8 works; absent from the anchor limb []; absent from the bibliography []

Two plants exercise its two clauses, one each: an anchor dropped from the **limb's declaration** (a
two-argument mutation -- the battery now deep-copies the limb so a plant can reach it) and an anchor dropped
from the **bibliography**, which is the exact shape of this round's real defect.

`C14` was also rescoped: `NOTES.md` is now a file of **per-round** sections, and a section's numbers belong to
the round that wrote them -- the historical sections are the record and must not be rewritten when a later
round changes the artifact.  The check therefore reads the **last** section and names it.

## 3. The artifact after the repair

    built 121 of 121 selected entries (75 arXiv + 46 DOI) (at R417) | unique keys 121 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id   4
    resolved from refs_raw.json / refs_raw2.json    71 entries over 34 query labels

The DOI limb is unchanged: 46 are selected; 4 are excluded (two with no year in the record, one with no author
field, one incoherent -- 0 authors and a venue contradicting its own title).

## 4. The stage-2 checks, after this round

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

(the two added checks bring their own plants: C15's limb clause and its bibliography clause -- the latter the
exact shape of this round's real defect -- and C14's three notes mutations, one of which states a refusal
figure without its provenance marker.)

## 5. The manuscript begins

`research/manuscript/part1.md` carries the front matter and section 1: the abstract, the belief the paper
tests, the construct (binding fidelity separated from reviewer accuracy, with the channel's defect classes
partitioned exactly), the falsifiable boundary claim, and the significance argument.  It cites by key, and
`cite_check.py` reads the keys back -- **33 citations, 22 distinct keys of 121 built records (at R417; the manuscript has moved since -- the current reading is in the R418 section below)**, 0 unknown keys
(its own mutation, a key renamed in a copy, is caught), with the numbering (`[1]`-`[n]`, first-citation order)
derived from the text rather than maintained by hand.  99 records are uncited so far: that is the number the
sections from 2 onward have to bring to zero before submission.

**A third finding, and it is a registered metric with no owner.**  The registration's success metric (b) is the
axis-sensitivity ratio `(dE/da)/(dE/db)` at `b in {0, 0.5, 1}` -- the quantity PB2 is registered against.
Grepping the four instruments for it returns nothing: **no instrument computes it**, and no round note states
it (v3's note claims *"v1 (PB1/PB2/PB3)"*, which is true of the prior's screening clause and not of this
metric).  It is derivable from v1's slope laws -- for a mismatch channel `dV/da = s*L*pi*b` and
`dV/db = s*L*pi*(a-f)`, so the ratio is `b/(a-f)`; a substitution channel adds `eta*L*(1-pi)` to the
denominator -- but a derivation on paper is not a read by an instrument, and PB2's `Outcome` line cannot be
written from one.  **Next round**: read the ratio in a small instrument against that closed form, then fill
PB2's outcome.

## 6. Next (the manuscript itself)

Write the manuscript's front matter and body against these keys: title, abstract, contribution-level
declaration, §1 Introduction with the falsifiable boundary law and the significance argument, §2 the closest
work with its stated differences, then the model, the design ladder, the results, the per-prior `Outcome`
rows, the threats section, the figures, the assembly/digest layer and `reproduce.sh`, then
`reference-check.md` (identity re-read per entry at its owning index) and submission.

---

# R418 -- the reference pipeline is unchanged; its numbers are re-read, and C14 says why

This round's work is the v4 instrument (`../gate_v4.py`, `../v4_notes.md`); the reference pipeline was not
touched.  The section is here because `C14` reads the numbers of the **last** section against the artifacts they
belong to, and one of them moved: the manuscript gained a reading in section 1.3 (the crossover law, at R418),
so its citation line was **34 citations, 23 distinct keys of 120 built records (at R418)**, 0 unknown, **97 records
still uncited** at that point (section 2, written at R425, brought both numbers to their current values; the
bibliography reads 120 since R424 moved the refused row out of the selection).

**The drift is the check working.**  The R417 section stated 33/22 -- true when written -- and `C14` went red on
exactly that clause, so the stale reading was fixed *at its own carrier* rather than left for a reader to
subtract.  The section above now marks the value with its epoch (`at R417`), which is the rule this file keeps:
a section's numbers belong to the round that wrote them.

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

The reference pipeline's own artifact is unchanged this round: `built 121 of 121 (75 arXiv + 46 DOI) | 0 errors
| 0 duplicates` (at R418), 34 query labels, 8 registration anchors declared of which the harvest pools lack 4 and
the limb resolved all 4.

# R424 -- the bibliography contained a work the selection had REFUSED, because the refusal was a sentence

## 1. The finding: a selection decision written in prose, and a build that reads only the table

`ARXIV`'s row 71 was

    ("2609.22062", "Plans dense packing of irregular objects for robots; unrelated to overslight but retained "
                   "in the pool, and it is not selected."),

a cs.RO paper on **robot grasp packing** -- `Gripper-Aware Automatic Dense Packing of Irregular Objects` -- that
the W3 `monitorability` keyword window returned and the selection had **refused**, with the refusal written into
the `difference` line of a row that stayed in the selected table.  `refs_build_v93.py` walks every row of a
selection table, so the work was built into `refs_built.json`, keyed (`qin2026`), counted in the **121**, and
printed in every "121 of 121" line this file carries.  Nothing read the sentence: the refusal was a claim with no
owner, and a `difference` line is where a work's *stated difference from this study* belongs, not a note that the
work is not being cited at all.

**Why it was not harmless.** The journal's submission bar requires **every** bibliography entry to be genuinely
cited in the body (≥100 references, all cited; a bib entry that never appears is padding).  Following the plan this
round -- write the manuscript's sections until the uncited count is zero -- would have forced a citation to a paper
about gripper geometry into a paper about human approval gates.  The defect was found by **reading the selection
table against the artifact**, not by a check: no check existed for it, which is the second half of the finding.

The same family has appeared in this journal before, and each time the repair was the same: a decision carried as
**prose inside a payload** instead of as **a field the pipeline reads** (Class 112: declarations must be by shape,
with a reason; Class 114: a scan is only as wide as the truth it reads).  Here the payload was a `difference`
string, the reader was a build loop, and the consequence was a citation nobody could honestly make.

## 2. The repair, in two halves

**The refusal is now a FIELD.**  `refs_selection_v93.py` gained a separate table:

    NOT_SELECTED = [("2609.22062", "Gripper-Aware Automatic Dense Packing of Irregular Objects (cs.RO). ...")]

and the row left `ARXIV`.  The register keeps the **decision and its reason** -- the register of considered works
stays complete, which is what a refusal is worth -- while the work cannot enter the bibliography at all.

**The build reads it, two-sided.**  `refs_build_v93.py` now refuses, before writing anything, (a) a not-selected id
found in a selected table, (b) a selected id found in the register, and (c) a duplicate row in the selection; it
records `n_not_selected` and the register with its reasons in the artifact, and its provenance line no longer
labels all 46 DOI entries `?` (the DOI limb's label was a provenance field that named nothing).

**The check that did not exist.**  `refs_check3.py` reads the pair (selection, artifact) with 7 properties --
selection matches the build in both directions and the count has one owner (C1); the register and the selection
are **disjoint in both directions, against BOTH carriers of the exclusion decision** (C2); **no `difference` line
may carry its own exclusion** (C3, the defect itself, now a regression test); the register is recorded in the
artifact with its arXiv count (C4); the key map covers the selection exactly (C5); the manuscript cites no refused
work (C6); every refusal states a usable reason (C7).  Its battery is **16 cases**, one plant per check plus one
per carrier, each fed its **own crafted object** rather than mutating the live tree.  Three things the battery
itself taught, all recorded because they were defects of the instrument and not of the artifact:

* **The control is the one case whose plant MUST be inert.**  The first run read the unmutated control through the
  same "a plant must change the object" rule as the others and reported a `MUTATION INERT` -- the battery
  reporting its own control as a defect.  The rule is now split by case: the control's property is *unchanged AND
  no check fires*.
* **One limb is a state the live tree cannot reach, and that is asserted rather than skipped.**  A refused work is
  not built, so it has no key, so no citation can name it.  C6 asserts that impossibility (a refused work carrying
  a key is itself a failure) *and* keeps the limb live, because a work refused **after** it was keyed would be
  reachable; the battery reaches it by **crafting** the key the live tree cannot have.  An empty lookup and an
  impossible state must not look alike (Class 113's rule, applied to a lookup).
* **The exclusion decision has two carriers, and the asymmetry between them is how the defect survived.**  The
  arXiv limb's refusals now live in `SEL.NOT_SELECTED`; the DOI limb's four exclusions live in the **stage-2
  check's own `REFUSED` list**, and always did -- one limb's invariant held, its sibling's absent.  C2 therefore
  reads **both**, plants a violation through each, and treats an **unreadable** carrier as a failure rather than as
  an empty list: a check that tolerates a no-match is blind to its object going away (Class 110), and a property
  read against one of two carriers is a property read against neither.

## 3. The artifact after the repair

    built 120 of 120 selected entries (74 arXiv + 46 DOI) | not selected 1 | unique keys 120 | duplicates 0 | errors 0
    resolved from refs_anchors.json:anchors-by-id    4
    resolved from refs_classic.json:crossref-doi     46
    resolved from refs_raw.json / refs_raw2.json     70 entries over 34 query labels

`refs_keys.py` re-derives **120 keys** (5 collisions, the same five first-author clusters), `--check` identical,
and `qin2026` is gone.  The manuscript's citation line is therefore **34 citations, 23 distinct keys of 120 built
records**, 0 unknown, **97 records still uncited** -- the number the manuscript's sections must bring to zero.

Everything else in the pipeline is unchanged and re-read: `refs_check.py` (stage 1) and the stage-2 checks pass,
`C14` re-read the numbers of the older sections at their own epochs, and the anchor limb, the DOI limb's 46/4
split, `C11`'s floor of 100 and `C15`'s 8 anchors are all untouched.

`refs_check3.py`: 7 checks, 7/7 PASS; the mutation battery 16 cases, 16/16 caught.  Stage 2 after this round:

    15 checks, 15/15 PASS; 22 mutations, 22/22 caught

# R425 -- the manuscript's section 2 is written, and the citation bar's volume+coverage item is met

## 1. Section 2, walked in the order the selection was authored

The selection's buckets were authored as "also the manuscript's order of first citation", so section 2 walks them
in that order: 2.1 the deployed regime and the question (A), 2.2 the reviewed object is not the executed one (B),
2.3 authorization, capability and the artifact that authorizes (C), 2.4 the human's signal -- detect, defer,
escalate (D), 2.5 the human's limits -- fatigue, bias, warnings (E), 2.6 the cost of the gate (F), 2.7 verifying
the artifact (G), 2.8 what a programmatic monitor can and cannot do (H), 2.9 the classical spine (I), 2.10 the
economics of an oversight decision (J), and 2.11 what no group above supplies (the paper's position).  Each work is
cited by key with the difference this study states from it, and each subsection closes on the axis the group holds
fixed that this study varies.  Written into `manuscript/part2.md` (2.1--2.4) and `manuscript/part3.md`
(2.5--2.11).

The manuscript's citation line after this round:

    **168 citations, 120 distinct keys of 120 built records (at R425)**, 0 unknown keys, and **0 records uncited**

That last number is the submission bar's volume-and-coverage item: every one of the 120 records is now genuinely
cited in the body, so no entry is padding and the count cannot be a count of filler.  `cite_check.py` reads the two
properties separately, and they failed separately while the section was being written -- a mistyped key
(`labapo2022` for `ladapo2022`) turned RESOLUTION red while COVERAGE stayed at 119 of 120, which is exactly why the
two are not one check.

## 2. The legend is a claim about the table, and one of its letters named nothing

Writing section 2 required reading the bucket legend, and that read found the same defect class as R424 in a
smaller place: the legend's last column named a bucket `K  statistics of comparison` -- and no block carries K.
The statistics-of-comparison works (the paired ROC comparison, Youden's index) sit inside I.  The legend was
therefore amended to say so, and the property is now checked rather than proofread: `refs_check3.py` gained
**C8**, which reads the legend and the table's own `# ---- X` markers **two-sided** -- a letter the legend names
with no block behind it, and a block whose letter the legend never names, are both defects -- and treats an
unreadable source as a failure rather than as a pass.

C8's own first version was wrong in a way worth recording: it required a bucket letter at the **start of a line**,
and the legend is a **two-column** block, so the reader missed the whole right-hand column and reported three
buckets as un-named by a legend that names them.  Found by running it on the live tree, not by reading it -- the
Class 114 family again (a reader narrower than its object).  Its battery plant had the same problem in miniature:
aimed at the `F` line, whose text continues on the same line with the right-hand column, so the anchor was absent
and the plant came back INERT rather than as a pass.

`refs_check3.py` now carries **8 checks (8 passing)** and a **19-case battery (19 firing)**; the C8 plants read
**crafted source texts** rather than mutating the real module, because a plant that rewrites the selection and
restores it leaves the tree one crash away from a corrupted bibliography.

# R426 -- sections 3 and 4 written; a citation the checker could not see

## 1. Sections 3 and 4

`manuscript/part4.md` adds §3 (the model) and §4 (the harness): the decision and its parameters with their
anchors, the channel and the exhaustive three-class partition of its defects, the state space with the value
functional written out, the six-design ladder with the defaults table, the complementarity of the two repairs as
a structural reaching statement, and the two mechanical guards (the screening closure that raises, and the
adversary machinery inert at `b = 1` exactly and firing at `b = 0`).  The manuscript is now four parts.

New reading:

    **196 citations, 120 distinct keys of 120 built records (at R426)**, 0 unknown, **0 records uncited**, 0 malformed

## 2. The finding: a citation the checker could not see

Writing §4 produced `[(@modic2014;@brodsersen2013;@marteau1989)]` -- a `[` followed by a `(`.  The citation regex
is `\[@([^\]]+)\]`, which requires the `[` immediately before the `@`, so that bracket **matched nothing** and
three citations were silently unread while the report printed `unknown keys 0 []`.  The defect was found by
reading the prose, not by the checker: the checker's reader was narrower than its object, which is the same
family as the two reader defects R425 found in C8.

The repair is in the checker, in both directions.  `cite_check.py` gained a **malformed** limb: every
`@key`-shaped token in the text must be consumed by a well-formed `[@...]` citation, and any occurrence outside
one is reported with its context and fails the check.  Its battery gained three cases (a malformed bracket is
caught; a well-formed citation is NOT reported as malformed; an unterminated bracket is caught), and the second
of those was itself wrong on first writing -- the crafted text I meant as malformed was in fact well-formed, so
the check was right and my case was wrong, which is why a battery needs a case in each direction.

Two facts this leaves on the record.  First, the *count* of citations is a weak reading: `196` counts what the
regex could see, so a malformed citation makes the number smaller and the sum look cleaner.  Second, and
generally: **a check that skips what it cannot parse reports a green run on a narrower object than the one it
claims**, so every reader in this package is now asked what it does with a token it does not understand.

# R427 -- section 5 written; the reading the R426 repair made visible

`manuscript/part5.md` adds §5 (the results), then §6 (verification) and §7 (threats) follow in the same round.
The bibliography is unchanged -- no work was added, dropped or reselect-ed -- and the manuscript's own citation
line, read back by `cite_check.py`:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

Two readings moved inside this round, and both are kept: with §5 alone the line read `199 citations ... (at R427,
section 5 only)`, and the R426 epoch is `196 (at R426)`.  The first difference is the R426 repair widening the
reader's object -- the three citations the malformed bracket hid are counted now -- and the second is §6 and §7
citing works that earlier sections did not.  Neither moved a selection.  The quoted tokens are a third reading the
same repair added: 4 `@key`-shaped tokens live inside inline code, where they are quotations of the defect rather
than citations, and they are counted and printed rather than dropped.


# R428 -- the authenticity report: a clean summary line over an empty object

The journal's citation-integrity bar needs one line per reference: what was asked, of which record, and whether the
answer agreed.  `refs/reference_check.py` now produces it (`--query` writes `reference-check.json` + its rendering
`reference-check.md`), and the manuscript's own citation line is unchanged:

    210 citations, 120 distinct keys of 120 built records, 0 unknown, 0 records uncited, 0 malformed

New reading, the report itself:

    **120 of 120 references verified** -- 46 DOI queried at Crossref, 74 arXiv keys queried through
    the arXiv API id_list (2 batched requests); 0 mismatch, 0 unverified; title agreement measured as
    normalized token overlap against a 0.80 floor; 1 year difference printed (diakopoulos2014: Crossref 2015
    vs the manuscript's 2014 -- a journal article's volume year against its online year, printed rather than
    failed because the preprint/published pair legitimately differs)

Two facts from building it belong on the record.  First, the **join**: the manuscript cites by LABEL
(`[@wang2026]`) while `refs_built.json` is keyed by IDENTIFIER, and the first version joined the two and produced
**0 rows** -- it printed `verified 0, mismatch 0, unverified 0 of 0`, a summary that is internally consistent and
about nothing.  `refs_keys.json` is the label -> record map the manuscript actually cites by, and the report is now
driven by the manuscript's citation order read through `cite_check`; the query refuses to write when it finds no
cited record at all.  Second, the **counter**: the verdict was read from a summary counter instead of from the rows
it summarizes, so a row saying MISMATCH under a summary saying 0 passed; the counts are now derived from the rows
and required to agree.  Both are the Class 112/114 family, and both were found by reading the object rather than the
line.


# R429 -- the assembled bibliography, read as a page

Nothing in the bibliography changed this round: no work was added, dropped, reselect-ed or re-verified, and the
manuscript's citation line is unchanged at **210 citations, 120 distinct keys of 120 built records, 0 unknown, 0
records uncited, 0 malformed**.  What changed is what the reader sees, and it was wrong.

**The defect.** `refs_keys.json` -- the map the manuscript cites by -- carries `authors, difference, identifier, key,
pool_title, source, title, url, year` and **no venue field**.  `assemble.py` rendered whatever the map had, so all
**120** entries reached the product as

    [n] Authors (year). *Title*. URL -- stated difference

with the house order's **venue** quietly absent.  `refs_check.py` (24 checks), `refs_check2.py` (15/15 + 22
mutations), `refs_check3.py` (8/8 + 19 cases) and `refs/reference_check.py` (12 checks + 9 cases) were all green,
because **every one of them reads the record and none reads the rendered page**.  The venue exists in
`refs_built.json` for all 120 entries (arXiv entries carry `arXiv:<id>`, DOI entries their container title), so the
fix is a join in the renderer plus a refusal:

* `assemble.py` now joins `venue` from `refs_built.json` by identifier, and **REFUSES** an entry that is missing any
  of authors / year / venue / link / stated difference -- the house order is enforced, not hoped for.
* `submission_check.py`'s presentation item P1 reads the rendered entries and fails on a missing field, with a plant
  that strips one entry's venue.

So the pipeline's own lesson, one level up from the record: **a report about a record is not a report about the
page**, and the page is what the reviewer reads.
