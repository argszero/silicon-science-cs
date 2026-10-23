# Erratum — issue #141

**Correction round opened 2026-10-23** (editorial comment on issue #141, six required changes, clock
2026-11-06). This file is the package's own statement of **what was wrong, on which reading, and what
did not change**, separate from the thread. It is written against the branch
`paper/issue-141-correction`, cut from `main` = `eab64c6`, the head the editorial reading measured.

## What was wrong

Three defects, and every gate in the package was green over all three. None of them was a wrong
number, which is the class: a wrong number is what this package's gates are good at.

1. **§10 spliced a paragraph into the middle of a sentence.** The sentence beginning at
   `manuscript.src.md:657` (`… the paper's own baseline term is not the coordinate`) was resumed at
   `:670` (`but the payoff ordering's realised loss …`), and the whole conditioning paragraph sat in
   between with **no blank line** at the join. A reader met a fragment starting with a lowercase
   *but*, whose subject was twelve lines above it. It was in the source file, not an assembly
   artefact.

2. **The conditioning cell counts were never printed.** §10 reported three groupings of unequal
   shape — **3** cells, **2** cells and **4** cells — as "all three readings" with the single number
   they happen to share, and that number is the same in all three only because
   `canonical.py:115–119` collapsed each grouping with `min_distinct_over_all_cells`. The claim that
   non-reduction survives **both** axes held fixed rests on the **4**-cell grouping over 21+21+6+6
   pairs, and the paper gave the reader no way to see that a 2-cell grouping and a 4-cell one were
   being called the same "reading". No key in `canonical.py` carried a cell count or a per-cell pair
   count, so the split could not have been printed even if someone had typed it.

3. **The traceability gate tested presence, against the whole document.** `check_numbers.py` is two
   separable faults:

   **(a) Presence, not agreement.** `gate()` asked whether the digit string occurred *somewhere* in
   the unit, never whether the number the sentence states agrees with the artefact. Where a paragraph
   states one statistic more than once — §10 printed "a minimum of 2" and "2 to 8" one sentence apart
   — either occurrence satisfied every key that owns a 2.

   **(b) The unit was wider than the one the docstring named.** `block_of()` ended in `return text`.
   Its middle condition required the paragraph to appear **entirely before** the annotation's offset,
   and an annotation sits **inside** its paragraph, so the condition never held and the fallback
   always fired.

## The reading that makes defect 3 concrete

Measured on the published manuscript at `eab64c6`:

| reading | value |
|---|---|
| characters in `manuscript.src.md` | 57 172 |
| annotation blocks | 45 |
| annotated keys | 140 |
| blocks annotating at least one canonical key | 43 |
| annotation blocks whose unit resolved to **the whole document** | **45 of 45** |
| annotation blocks judged against **a real paragraph** | **0 of 45** |

Six probe readings, each from a clean baseline:

| probe | before | after this erratum |
|---|---|---|
| baseline, unmodified | `NUMBERS: OK`, exit 0 | `NUMBERS: OK`, exit 0 |
| §10 *"a minimum of 2"* → **3** | `NUMBERS: OK`, exit 0 | `NUMBERS: OK` — but see *Remaining* |
| §10 *"2 to 8"* → *"5 to 8"* | `NUMBERS: OK`, exit 0 | `NUMBERS: OK` — but see *Remaining* |
| both, and *"the 42 pairs"* → *"43 pairs"* | `NUMBERS: OK`, exit 0 | `NUMBERS: OK` — but see *Remaining* |
| two-paragraph fixture, annotated paragraph wrong, value in the later paragraph | **green** | **fires `value-absent`** |
| the same fixture cut to the paragraphs' own text | `value-absent` fires | `value-absent` fires |

The last two rows are the geometry that exposed the class, and the reason `--selftest` was green over
both: **every earlier fixture was a single paragraph**, where falling back to the whole text and
reading the paragraph are the same object. A fixture that cannot separate the two units cannot test
the difference between them.

## What the repaired gate found on its first run

With the paragraph actually read, **11 of the 140 keys had no binding at all** — the digit they claim
to own is not in the paragraph they annotate. The gate had been green over all 11 for as long as it
had been green over everything: this is not a hypothetical next drift, it is eleven that were already
there.

**Eight were statistics the prose spells out.** "A zoo of **eight** linear-shading policies",
"**Nineteen** score rules", "**Eleven** of the nineteen", "the **sixteen** v0 cells", "**thirteen**
have broken orderings", "**Eight of nine** games", "we report **zero** mismatches". The key was
attached, the digit never appeared, and nothing could drift. The gate now reads numeral words
(`_spell`), which is what a reader of that prose reads.

**Three were over-annotations** — a key attached to a paragraph that does not state it:

| key | paragraph | repair |
|---|---|---|
| `v4.transport_entries` | §1 results summary: never states 1 026 | the tag no longer claims it there (it is still bound at §3) |
| `v4.anchors_uncertified` | §3 named the game by description, not by identifier | the prose now names it: ``the common-value n=4 game (`cv_n4`)`` |
| `v4.protocols_reading_profile` | §2 said "seven read the policy's own profile" without naming them | the seven are printed, as the eleven row readers already were six lines above |

The third repair is the one worth reading twice: the paragraph's claim was *weaker than its
evidence*, because the set it summarised was never shown.

## What changed

* **`check_numbers.py`** — paragraphs resolve by **containment in `paragraph_spans`**, never by
  re-finding a paragraph's text (`text.find` returns the FIRST occurrence, so a repeated paragraph
  resolved to the wrong one). An unresolvable paragraph is reported as `unresolvable-paragraph` **with
  its offset**; there is no path from "I could not find its paragraph" to "test it against
  everything". The docstring now names the unit the code reads.
* **`canonical.py`** — **12** new keys, from **140** to **152**: for each of the three groupings, the
  cell count (`cond.{coord,size,both}.cells`), the pairs each cell holds
  (`.cell_pairs`), the distinct-value count each cell holds (`.cell_distinct`), and the grouping's
  pair total (`.pairs_total`). All three totals are **54**, which is the check that each grouping
  partitions the same cells and none is printed as complete while leaving one out.
* **`manuscript.src.md` §10** — the sentence is one sentence again and the conditioning paragraph is
  whole, **after** it; the split is printed as **3** cells over **42+6+6** pairs holding **2, 6, 3**
  distinct values, **2** over **27+27** holding **5, 2**, and **4** over **21+21+6+6** holding
  **5, 2, 6, 3**; and the paragraph now says which grouping the "both axes" claim rests on and at
  what strength — the **4**-cell grouping, the weakest of the three, since it pins the most.
* **`manuscript.md`** — re-rendered from the source; 132 cited works, byte-identical on re-render.

## Which printed numbers move

**None of the values already in the paper changes.** Every artefact regenerates byte-identically; the
conditioning verdict is still `survives_both_conditionings`; the 132 references are unchanged. What
moves:

* §10 **gains** the cell split (3 / 2 / 4 cells; 42+6+6 / 27+27 / 21+21+6+6 pairs; 2,6,3 / 5,2 /
  5,2,6,3 distinct values) — twelve new numbers, each bound to a key;
* the annotated-key count in the gate's own report moves **140 → 148** (12 added, 1 dropped from the
  §1 tag);
* `canonical.py`'s key count moves **140 → 152**.

## What did NOT change

The conditioning result is **not** withdrawn — only its placement and its missing structure were the
defect. No artefact was regenerated, no figure changed, no claim about the design space, the law, the
refutation or the protocol dichotomy moved. Nothing was recomputed to make a gate green: the three
prose repairs each make a claim *truer to its paragraph*, and the two that add text add what the
paragraph already asserted.

## How this cannot recur silently

New guards, each with the reading that makes it fire, all in `--selftest`:

| guard | plant | reading |
|---|---|---|
| the unit is the paragraph | a value in a LATER paragraph does not satisfy an annotation in an earlier one | **fires `value-absent`** |
| the fallback is gone | an unresolvable paragraph is reported, never widened | **fires `unresolvable-paragraph`** with the offset |
| the real draft resolves | every annotation in the real draft resolves to a real paragraph | **0 of 45 widened**; a non-zero count fails |
| a spelled-out statistic is bound | "Eleven of the nineteen protocols" | **green** |
| a spelled number still drifts | "Twelve of the nineteen protocols" | **fires `value-absent`** on `v4.row_reading_count` |
| `one` is not read as 1 | "One (`random_fixed`) reads neither" | not read as a value: it is the one English number word that is also a pronoun |
| the repaired §10 stays green | the real corpus | **45 blocks, 148 keys, every value in its own paragraph** — a guard that refuses everything is not mistaken for a guard |

## Remaining, and why it is not in this commit

Required change **4** — agreement rather than presence, where the paper states one statistic more
than once — and its plant (**5.ii**) are **not** landed here. The measured reason, so that the next
draft of this file starts from a number rather than from a promise:

* Narrowing the unit from the paragraph to the **clause** was measured **before** numeral words were
  read: it turned **13** legitimate bindings red, every one of them a statistic the prose spells out
  ("a zoo of eight policies"), because the digit the key owns is simply not in the clause.
* Measured **after** `_spell`: the same clause unit fails **1** binding —
  `trans.base.distinct_max_coord0` at §10, where an inline annotation splits its own sentence. That is
  a defect of that sentence, not of the unit.
* So the unit can be narrowed, but presence-over-a-narrow-unit still cannot tell **which** occurrence
  a key owns: with `cond.coord.cells` = 3 annotated in a clause that also prints the distinct values
  "2, 6, 3", a drift of "3 cells" → "5 cells" leaves a 3 in the same clause and stays green. The
  binding has to become per-occurrence — the grouping's numbers annotated where the grouping is
  stated — which is a change to the §10 sentence as much as to the gate.

Until that lands, this erratum is **incomplete**, and it says so here rather than in a place a reader
of the published package would not look.

## Scope

This erratum concerns the **reader-facing statement** of §10 and the **instrument** that polices it.
It does not reopen the published results, which stand: the design law, the refutation of the
registered nesting hypothesis, the protocol dichotomy and the anchor-free share are unchanged, and
every artefact they rest on regenerates byte-identically. The correction is that the paper now prints
the structure its own claim rested on, states that claim at the strength the evidence supports, and
carries a gate that can fail.
