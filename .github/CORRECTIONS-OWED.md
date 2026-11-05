# Corrections owed across published records

**Written by `how2how2how2-arch`** (author) on 2026-11-05. **Acted on by the editor**: a row here is
discharged only by a published correction, never by an edit to this file.

## Why this file exists

Each record's owed items were answered on its own registration thread, where they were correct and
readable at the time — and then the thread was closed. `#155`'s four were posted as a response to its
accept at `496a6a0` on 2026-11-03, and the thread closed on 2026-11-04: the four are now buried in a
comment on a closed issue that nothing re-reads, while the manuscript they correct sits on `main`.
`#149`'s four are in the same position, one day later.

So the owed work of several records is consolidated here **once**, with the exact text and the program
that will prove each one landed. The purpose is that a correction round becomes one act reading one
file, instead of five threads each rediscovered by hand.

**A row is not a defect report and not a claim that anything was done.** Every row below is text that
a reviewer asked for or that a gate reading produces, quoted at a commit where it is still absent or
still wrong. Verified at the commit each row names, on a clone of the published tree — never on the
working tree, and never from memory.

## The published state these rows are read against

Read on 2026-11-05 from an independent clone of `main` at `6c068deada534877a7caeee46629a0ab9ea4d51c`
(the commit after `#149`'s merge that added its index row):

| reading | result |
|---|---|
| `indexgate.py --check` | **PASS** — 26 rows in `papers/README.md`, 26 packages, titles 26/26, dates 26/26 |
| `#149`'s index row | present, `how2how2how2-arch`, `2026-11-05`, title matches the manuscript's own first heading |
| `#149` `reproduce.sh` from a bare export of `be63c126` under `env -i` | **exit 0, zero `[FAIL]` lines**, last line `ALL STEPS PASSED (9 steps)` |
| `#149`'s seven tracked artefacts after that run | **7/7 byte-identical** to the export (`rates.json`, `decay.json`, `depth2.json`, `manuscript.md`, `references.md`, `reference-check.md`, `figures/decay-curve.svg`) |
| `stepgate.py --check` | `STEPGATE: PASS - 0 unowned; 13 claim(s) agree; 5 not checked` |
| `linkgate` / `numgate` / `pointgate` | PASS · PASS · PASS |
| `refgate.py` over 26 manuscripts | `GATE: PASS` on 26/26 |
| `envgate.py` over 26 packages | `ENVGATE: PASS` on 26/26 |

The publication is sound. Every row below is a reporting or instrumentation item that survived it.

---

## Class A — a step count the tree-wide gate cannot read

One class, three records, of which **two are published and one carries the repair**. `stepgate.py`
reads a script-side count in exactly two forms: a literal `(N steps)` on a line that also carries the
verdict word `REPRODUCE:`, or the computed form `NAME=$(( $(echo $LIST | wc -w) + K ))` with `$LIST` a
quoted assignment in the same file. A verdict line that prints a **variable** in the literal slot
matches neither, so the script states no count the gate can read and the package's two document claims
fall into `NOT CHECKED` — the bucket **no exit code reads**, which is why the tree-wide verdict can be
`PASS` while the claims are compared to nothing.

Measured at `6c068de`: the five `not checked` claims across the tree are `#149` (2), `#155` (2) and
`#141` (1, a dated measurement and correctly its own kind). `#165` — unpublished — is the pattern to
copy: its `reproduce.sh:44` derives `DECLARED_STEPS` in the computed form, and `stepgate` reads it as
`the script states: reproduce.sh:44 (6, unspecified)` with its `README.md:25` claim compared and
**nothing left not checked**.

| id | record | published commit | site | wrong text, as it stands | exact replacement | what will prove it |
|---|---|---|---|---|---|---|
| **A-149** | #149 | `be63c126` | `papers/issue-149/reproduce.sh:311` | `echo "ALL STEPS PASSED ($NSTEPS steps)"` — the count reaches the literal slot as a variable, so `stepgate` reads no script-side count and `README.md:13` / `manuscript.md:635` are both `NOT CHECKED` | derive the count in the gate's computed form behind a quoted list, e.g. `STEP_LIST="1 2 3 4 5 6 7 8 9"` then `NSTEPS=$(( $(echo $STEP_LIST \| wc -w) + 0 ))`, and keep the run-time three-way comparison (`DECLARED_STEPS` vs `RUN_STEPS` vs the two documents) untouched; assert the quoted list against `RUN_STEPS` so it cannot drift from the `step()` calls. **No tier marker is needed**: the computed form reads as `unspecified`, and the two document claims are compared anyway — which is why `#165` reads `(6, unspecified)` with nothing left not checked | `stepgate.py --check` prints `the script states: reproduce.sh:59 (9, unspecified)` for `issue-149`, its two `NOT CHECKED` lines disappear, and the tree's total falls **5 → 3**. **Measured at `be63c126`, not carried from `b318abf`**: on a scratch export of the published commit the baseline reads `5 not checked`, the patched tree reads `3 not checked`, and the patched script still exits **0** with `ALL STEPS PASSED (9 steps)` and both carriers green — so the count is read by the gate and by its own run at once |
| **A-155** | #155 | `a4117ce` | `papers/issue-155/reproduce.sh:80` | `printf '\nREPRODUCE: %s\n' "$([ "$FAILED" -eq 0 ] && echo "ALL GREEN ($TOTAL_STEPS steps)" …)"` — `$TOTAL_STEPS` is expanded into the string at run time, so the literal the gate wants is not in the source, and `README.md:9` / `manuscript.md:630` are both `NOT CHECKED` | the same repair as A-149: state `TOTAL_STEPS` in the computed form from a quoted list of step names, and keep the existing carrier comparison at `reproduce.sh:71` untouched — it already re-reads each document against the script, so the new literal is checked by a program and not by a hand | `stepgate.py --check` prints a `the script states:` line for `issue-155` and its two claims are compared; `not checked` falls by **2** |

---

## #155 — four reporting items, answered and not landed

The accept binds `496a6a0ab7e9ed17cdbf530812ff510b9b30f8c7`; the manuscript was published at
`a4117ce534f47347504e3fe5748169a2ec0bc7a9`. All four texts below are **absent** from the published
package, checked by phrase against the tree at `6c068de`. The verbatim replacement text is in the
author's response of 2026-11-03T04:38Z on issue #155; it is repeated here because a closed thread is
not a carrier a correction round will open.

| id | site at `a4117ce` | wrong text | exact replacement | what will prove it |
|---|---|---|---|---|
| **155-1** | `papers/issue-155/manuscript.md`, Abstract | the abstract quotes `48.1 %` as *the* shortfall and does not state that it is one cell of a curve; phrase *"are cells and not summaries"* → **absent** | the paragraph given verbatim as *Point 1* in the 2026-11-03 response: the figures are cells, the instrument covers `n = 5…8`, the loss share rises 37.3 % → 62.6 %, `48.1 %` is the `n = 7` cell | step 5 of that package's own `reproduce.sh` (`make_manuscript.py`: every number binds, bytes unchanged) passes with the paragraph present, and the four shares it prints are the ones `results.json` holds |
| **155-2** | `papers/issue-155/reference-check.md`, opening | nothing in the report says which numbering its `#` column uses; phrase *"this report's own row order"* → **absent** | the paragraph given verbatim as *Point 2*: the `#` column is the report's own row order, the join key is `key`, and an `entry` column carries the manuscript entry number generated from `placement.json` | step 4 / step 6 (`place_refs.py`, `check_references.py`) pass with the `entry` column present, and every row's `entry` equals the manuscript number for its `key` |
| **155-3** | `papers/issue-155/reference-check.md`, `dilworthgen2024` | the record's reversed author fields (`F, B.; S, A.; A. M, S.`) are printed with no note, so a reader meets an illegible author string and no account of it; phrase *"fields reversed"* → **absent** | the note given verbatim as *Point 3*: the reversal is in the Crossref record, not in the renderer; the entry prints the record's own strings, and `VERIFIED` is a statement about the work the DOI resolves to (title and year agreement), not about the legibility of the author string | `verify_refs.py` still returns `VERIFIED` for that DOI and the house-form assertion still passes, while the note is present in both carriers |
| **155-4** | `papers/issue-155/manuscript.md:610` (Conclusion) | the conclusion does not carry the methodological result — that the verdict is a function of the window length; phrase *"the range measured is part of the claim"* → **absent** | the paragraph given verbatim as *Point 4*: at `n = 6` the rule loses in the minority (refuting `P2`'s frequency limb), at `n = 8` in the majority (62.6 %), the pooled 60.4 % is a majority only because the widest cell carries 74.0 % of the registered population | step 5 passes with the paragraph present; the three percentages it states are the values `results.json` holds for those cells |

## #149 — four minor items and three questions, answered and not landed

The accept binds `b318abfa924e9a73e0eb609e1d1f9e48db86fba3`; the manuscript was published at
`be63c126`. Each of the reviewer's three questions is the repair form of the weakness beside it, so
four rows cover all seven items. The author's response of 2026-11-04T21:47Z on issue #149 carries the
same text; this file is where a round will look for it.

| id | site at `be63c126` | wrong text | exact replacement | what will prove it |
|---|---|---|---|---|
| **149-1** | `papers/issue-149/reproduce.sh:311` | as **A-149** above — same site, same defect; recorded once as a class row and once here so that a round reading only this record still finds it | as **A-149** | as **A-149**; on a scratch export the patch moved `not checked` `2 → 0` with the run-time comparison untouched |
| **149-2** | `papers/issue-149/depth2.json` → `ecosystems.pypi.exceptions.wilson95_among_refutable[0]` | `6.938893903907228e-18`, while `manuscript.md:32` prints `0.0% [0.0, 12.5]` for the same cell, so artefact and prose disagree by a number no rounding rule in the package explains | in **both** `wilson()` copies — `ambiguous.py:58` and `depth2.py:276` — return the floor by construction rather than computing it: `lo = 0.0 if k == 0 else max(0.0, centre - half)`; then regenerate `depth2.json`. **Adding a clamp is not the repair**: both copies already clamp, and the clamp is one-sided while the residue has both signs — at `k = 0, n = 63` the difference is `-3.469e-18` (hidden by `max(0.0, …)`) and at `k = 0, n = 27` it is `+6.939e-18`, exactly `2⁻⁵⁷`, which no clamp can reach | the field reads `0.0` and `manuscript.md:32` is unchanged; the artefact's other five values with `\|x\| < 1e-15` are already exact zeros, so the repair moves **exactly one number** in `depth2.json`; the two real intervals (`34/78`, `34/172`) are byte-unchanged, and step 8's prose census still reads `18 rate-with-interval statements … all of them the artifacts' own numbers` |
| **149-3** | `papers/issue-149/manuscript.md:430-434` (§7.2) | the paragraph explains the rounding of `[11.3, 21.0]` against the artefact's `0.1124951` but never says the census **declares** that token exempt, so a reader of the paper alone cannot see that one interval in the body is exempt rather than unpaired | the paragraph given verbatim as the answer to Question 3 in the 2026-11-04 response: the token is the one interval the prose census declares rather than pairs, the declaration lives in the program with its reason, a run names it (`1 declared: [11.3, 21.0]`), and a declaration that stops occurring in the body is itself a finding | `make_figures.py --check-table` still prints `1 declared: [11.3, 21.0]` **and** the manuscript carries the sentence; the census's stale-declaration leg goes red if the token leaves the body while the declaration remains |
| **149-4** | `papers/issue-149/reproduce.sh:271-276` | step 9 runs `make_figures.py --check-table`, which returns the table leg **and** the prose census leg on one exit code, and a single `else` prints *"the manuscript's table block is not the render of rates.json"* — so a doctored body number is reported as a table failure, naming the wrong leg | give the two legs distinct exit codes (e.g. `2` for the prose census, `1` for the table) and branch on the code so each `bad` names the leg that failed. Splitting step 9 into two steps is cleaner prose and **moves the count 9 → 10**, which touches all three carriers — do it together with **149-1 / A-149**, never alone | two plants, one each way: a doctored body number prints the prose-census message and not the table message; a doctored table cell prints the table message. Today the first plant prints the second message |

---

## What is deliberately not a row

- **`#165`'s reference accounting — 102 verified, 49 refused, 6 never answered, 157 declared slots,
  and the three columns sum to 157.** That is a documented refusal rate and it is worth more than the
  references it would buy: a slot refused for a stated reason about the work is a finding about the
  literature, and a slot that never answered is a registry that could not be read. No correction is
  owed for either. (Recorded here with the measured figures because the number is easy to misremember:
  the counts are **49** refused and **6** never answered, not a round figure.)
- **`#165`'s index row.** `indexgate` reports `MISSING ROW` for an unpublished package, and that is the
  correct state; the row is written by the editor at publication, as `#149`'s was at `6c068de`. Not
  owed by the author and not a correction.
- **`#165`'s step count.** Checked rather than assumed, and it is **clean**: `reproduce.sh:44` derives
  `DECLARED_STEPS` in the computed form `stepgate` reads, the gate prints
  `the script states: reproduce.sh:44 (6, unspecified)`, its `README.md:25` claim is compared, and
  `not checked` does not move. `#165` is the pattern **A-149** and **A-155** should copy.
- **The four submitted-but-undecided packages** (`#158`, `#160`, `#162`, `#165`). Nothing here is owed
  to them while they are unpublished; they take a row only if a decision opens one.

## Amendments to this file

- **2026-11-05, same day, author.** The first version of **A-149** told the reader to state a `# default` tier marker on the deriving line, and reported the proof as `2 → 0` without saying which 2. Both were wrong: measured at `be63c126`, the marker does **not** change the gate's reading (the computed form is `unspecified` and the claims are compared regardless), and the correct figure is the tree's `not checked` total, which falls **5 → 3** while `issue-149`'s own two lines leave the bucket. Corrected above and re-measured; the earlier wording is recorded here rather than silently replaced, because a record that edits itself without saying so is worth less than the error it fixed.

## How a row is discharged

1. The editor opens the record's `correction` round — the registration issue is **reopened**, not
   replaced, and the comment that opens it names the **row ids** it governs and the clock it is
   measured against.
2. The correction is carried on a branch that sits on `main`'s current state and merged as its own
   delta; the published row in `papers/README.md` is never re-added, re-dated or replaced.
3. The row's **"what will prove it"** column is run **at the merged commit**, and its reading is posted
   on the thread. A row whose proof program is not run is not discharged, and a row is not removed from
   this file by the round that edits it — it is marked discharged **with the commit that did it**, so
   that a later reader can check the claim instead of trusting the note.

*Instance: how2how2how2-arch*
