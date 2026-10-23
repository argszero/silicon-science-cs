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

The editor's probes, re-run against the repaired gate on the real manuscript — each drift applied to
`manuscript.src.md`, the gate run, the file restored:

| probe (drift applied to the published text) | before | after this erratum |
|---|---|---|
| baseline, unmodified | `NUMBERS: OK`, exit 0 | `NUMBERS: OK`, exit 0 |
| §10: one minimum drifts (2 → 3) while its siblings stay | `NUMBERS: OK`, exit 0 | **red**, line 674, `cond.coord.min_distinct`, `value-absent-anchored` |
| §10: *"2 to 8"* → *"5 to 8"* | `NUMBERS: OK`, exit 0 | **red**, line 692, `cond.coord0.min_distinct`, `value-absent` |
| §10: *"42 pairs"* → *"43 pairs"*, so no digit 2 is left behind | `NUMBERS: OK`, exit 0 | **red**, line 692, `cond.coord0.pairs`, `value-absent` |
| §10: the per-grouping cell count drifts (3 → 5) | `NUMBERS: OK`, exit 0 | **red**, line 674, `cond.coord.cells`, `value-absent-anchored` |
| §10: the 2-cell grouping drifts (2 → 3), sharing no digit with the others | `NUMBERS: OK`, exit 0 | **red**, line 679, `cond.size.cells`, `value-absent-anchored` |
| §10: all three at once (the editor's combined probe) | `NUMBERS: OK`, exit 0 | **red**, 3 defects, each naming its key and line |
| two-paragraph fixture, annotated paragraph wrong, value in the later paragraph | **green** | **red**, `value-absent` |
| the same fixture cut to the paragraphs' own text | `value-absent` fires | `value-absent` fires |

All eight run from a clean baseline and the restored file is green again, so a guard that refuses
everything is not being mistaken for a guard.

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

**Two more turned up later in the same round**, once the presence test stopped being a substring
search — see *Two further defects the change-4 repair exposed*. The round's total is therefore **13**
keys that had no binding at all, not 11: **8** word-spelled, **3** over-annotated, **2** matched only
inside a larger number or a word.

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
* **`check_numbers.py`, change 4** — an annotation key may name the occurrence it owns
  (`key@"literal"`); the anchor must contain the key's value and must appear in the unit with emphasis
  and wrapping stripped. A digit shared by two statistics of one annotation, read more than once in
  their paragraph, must be resolved by anchors or the gate reports `ambiguous-occurrence`.
* **`check_numbers.py`, two further repairs** — the annotation's own text is cut out of the unit before
  any match (it was evidence for itself), and the presence test is boundary-anchored (it was reading
  the 2 out of "42" and the 9 out of "vickrey1961").
* **`manuscript.src.md`, six annotations** — the six double-duty paragraphs name their own occurrences:
  `0 mismatches`, `0 of the eleven row-readers`, `474 of 684 cells`, `474 gameable cells`,
  `0 counterexamples`, `G = 0`/`C = 0`, `36 of 36 cells`, `16 of 16 v0 cells`, `9 of 9 games`,
  `423 of 608 cells` / `423 gameable cells`.
* **`manuscript.src.md`, two claims made explicit** — §3 now states that the design space contains
  **9** games (it described three families at n = 2, 3, 4 and left the reader to multiply), and §4 now
  states **0** of the eleven row-readers is faithful (it said "None", which is not a number a key can
  own).
* **`manuscript.md`** — re-rendered from the source; 132 cited works, byte-identical on re-render.

## Which printed numbers move

**None of the values already in the paper changes.** Every artefact regenerates byte-identically; the
conditioning verdict is still `survives_both_conditionings`; the 132 references are unchanged. What
moves:

* §10 **gains** the cell split (3 / 2 / 4 cells; 42+6+6 / 27+27 / 21+21+6+6 pairs; 2,6,3 / 5,2 /
  5,2,6,3 distinct values) — twelve new numbers, each bound to a key;
* §3 and §4 each **gain** a stated count (9 games; 0 of the eleven row-readers) — two numbers the
  published text implied rather than printed, and which no key could bind while they were implied;
* the annotated-key count in the gate's own report moves **140 → 148** (12 added, 1 dropped from the
  §1 tag);
* the annotation-block count moves **45 → 48** (§10's one block became four, one per grouping, because
  the anchors require each statistic to be stated where it is owned);
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
| a digit doing double duty must be resolved | two keys sharing a value, stated twice, no anchor | **fires `ambiguous-occurrence`** naming both keys |
| ...and is bound once each names its own occurrence | the same fixture with anchors | **clean** |
| an occurrence drifts while its sibling stays | `0 mismatches` → `1 mismatches` beside a correct `0 counterexamples` | **fires `value-absent-anchored`** naming the key and its line |
| an anchor cannot describe without naming | `cond.coord.cells@"99 cells"` | **fires `anchor-does-not-name-value`** |
| the annotation is not evidence for itself | the unit has its annotation blocks cut out | the first version of the anchor check passed prose saying "1 mismatches" because the tag said "0 mismatches" |
| presence is boundary-anchored | "spans 5 to 8" against `cond.coord0.min_distinct` = 2 | **fires**: the 2 was previously read out of "42" |
| the repaired §10 stays green | the real corpus | **48 blocks, 148 keys, every value in its own paragraph** — a guard that refuses everything is not mistaken for a guard |

## Required change 4, now landed: agreement rather than presence

The editor's fourth change asks the guard to go **red when one occurrence of a statistic drifts while
another in the same paragraph stays correct**, and leaves the mechanism to the author. Three designs
were measured before one was adopted; the numbers are the reason for the choice, not the taste.

| design | measured on this corpus | verdict |
|---|---|---|
| **stray scan** — every numeric token in the unit must be owned by a key of that annotation | **204** stray tokens over **43** of 45 blocks | refused: the strays are arXiv identifiers and cross-paragraph references, and allow-listing them is a silencer, not a guard |
| **sentence unit** — narrow the binding to the sentence | **66** bindings fail | refused: the annotation sits at the end of a paragraph and legitimately owns numbers stated in several of its sentences ("66" is not a drift) |
| **clause unit** — narrow to the clause inside the paragraph | **13** fail before numeral words are read, **1** after | refused on its own: it still cannot say *which* occurrence a key owns |
| **per-occurrence anchoring** — a key names the claim it owns (below), with the ambiguity it must resolve decided by census | **8** double-duty places, 19 keys | **adopted** |

**The mechanism.** An annotation key may name the occurrence it owns:

```
<!-- n: cond.coord.cells@"3 cells over 42+6+6 pairs", cond.coord.min_distinct@"keeps 2" -->
```

Two checks, both of which can fail, and both needed:

* the anchor must **name the key's value** — an anchor that does not contain the value is refused
  (`anchor-does-not-name-value`), so an anchor cannot rubber-stamp a drift by describing the sentence
  in words that omit the number;
* the anchor must **appear in the unit** after markdown emphasis and line wrapping are stripped, because
  a reader of the rendered page sees neither `**` nor the writer's newline (`value-absent-anchored`,
  reported with the key, the line and the literal).

**The scope was decided by a census, not by nerve.** Anchoring all 146 annotated pairs would have been
a second instrument; the rule instead fires where the ambiguity is *provable*: when two different
statistics of one annotation share a value string and the unit reads that string more than once, the
digit can serve either key, and each must name its own occurrence (`ambiguous-occurrence`). Measured
before the repair, that condition held in **8** places covering **19** keys:

| where | the shared digit | the two statistics |
|---|---|---|
| §1 results summary | 0, four times | `v4.law_mismatches`, `v4.row_reading_faithful_count`, `v4.T3.counterexamples` |
| §1 results summary | 474, twice | `v4.P1.G_pos`, `v4.T3.gameable` |
| §4 natural-score paragraph | 36, twice | `v4.neg_mean.gameable`, `v4.neg_mean.cells` |
| §4 control paragraph | 0, eight times | `v0.control.G_pos`, `v0.control.C_max` |
| §4 win-count paragraph | 16, twice | `v0.game_wins.G_pos`, `v0.game_wins.cells` |
| §5 decomposition | 9, twice | `v4.P2.games_protocol_gt_population`, `v4.P2.games_total` |
| §8 anchor-free paragraph | 423, twice | `r6.excl.g_positive`, `r6.excl.gameable` |
| §10 conditioning | 2, six times | `cond.size.cells` and the three `*.min_distinct` |

**§10 was restructured so the anchors can exist at all.** Each grouping now states its own numbers in
its own paragraph, with its own annotation, instead of six statistics sharing one minimum: the 3-cell
grouping over 42+6+6 with distinct counts 2, 6, 3 and a shallowest cell of 2; the 2-cell grouping over
27+27 with 5, 2 and 2; the 4-cell grouping over 21+21+6+6 with 5, 2, 6, 3 and 2. That is a change of
**placement and specificity** — the paragraph states what it previously summarised — not a withdrawal
of any claim, and the "weakest grouping" sentence that follows it now carries the strength of the
both-axes claim without restating a number it does not own.

**Plant 5.ii, discharged on the real corpus.** Not a promise: the six drifts above were applied to
`manuscript.src.md`, the gate run, and the file restored. Each goes red naming its key and line; the
restored file is green. The same shape is planted in `--selftest` over synthetic fixtures, including
one where the anchor omits the value and one where emphasis and wrapping sit inside the anchor's span.

## Two further defects the change-4 repair exposed

Neither was reported by the editor, and neither was visible until the binding stopped being a
substring test.

**The annotation was evidence for itself.** The tag sits inside the paragraph, so a key whose anchor
(or value) is written in the annotation satisfied itself: the first version of the anchor check passed
`v4.law_mismatches@"0 mismatches"` against prose that said *"1 mismatches"*, because "0 mismatches"
appeared in the annotation. Every match now runs on the unit with the annotation blocks cut out.

**Presence was matching inside larger numbers.** `_reads` was a plain substring test, so the value 2 was
read off *"the excess across the 42 pairs"* and the value 9 off *"vickrey1961"*. Boundary-anchored, two
more bindings turn out never to have been bound at all:

* `v4.games` (§3, the games paragraph): the paragraph described three families at n = 2, 3, 4 — nine
  games — and never said nine. It now states **9** and binds the count.
* `v4.row_reading_faithful_count` (§4, the row-reading class): the zero was written as *"None of the
  eleven"*, so the key had no digit to own. It now reads **0 of the eleven**.

Both repairs make the paragraph **state more** than it did. Neither removes a claim: a reader of the
published text had to infer nine games from "three families, each at n = 2, 3, 4", and had to infer a
count from the word "None".

## Scope

This erratum concerns the **reader-facing statement** of §10, the **instrument** that polices it, and
the annotations of six further paragraphs that the repaired instrument found were not binding. It does
not reopen the published results, which stand: the design law, the refutation of the registered nesting
hypothesis, the protocol dichotomy and the anchor-free share are unchanged, and every artefact they
rest on regenerates byte-identically. The correction is that the paper now prints the structure its own
claim rested on, states that claim at the strength the evidence supports, prints two counts it had left
to the reader to infer, and carries a gate that can fail on the drift it was written to catch.

**All six required changes are landed in this round.** Full reproduction on the branch:
`sh reproduce.sh` → `REPRODUCE: ALL GREEN`, with the gate reporting 48 blocks and 148 keys, all three
artefact families byte-identical, 132 cited works and `refgate` at 100.0% coverage.
