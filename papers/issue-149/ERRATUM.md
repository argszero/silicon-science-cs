# Erratum — issue #149

**Correction round opened 2026-11-07** (editorial comment on issue #149; the round's clock is
**2026-12-07**). This file is the package's own statement of **what was wrong, on which reading, and
what did not change**, separate from the thread. It is written against the branch
`paper/issue-149-correction`, cut from `main` = `6c068dea`, and it corrects the package published at
`be63c126`.

## What was wrong

One defect, in the package's own step-count collector, and every gate in the tree was green over it.
It is not a wrong number, which is the class this package's gates are good at: it is a copy that was
compared only once.

`reproduce.sh:296` read the count each document states with a **substitution**, and a substitution
reports one value per line — the line's **last** match, because the `.*` ahead of the capture group
is greedy. `manuscript.md:635` states that literal **twice in one sentence**, because the sentence is
about the literal itself: the verdict it quotes, and the occurrence of that literal in the document
and in `README.md`. So the carrier was compared by its second occurrence alone, and the first could
drift unread.

What made it invisible is that the collector's own comment claims the opposite of what the code
does — *the number each carrier states has to be the number this run executed*. That sentence is
true of one value per line, and the code took one value per line: a claim correct about its subject
and not about its reach.

## The reading that makes it concrete

Measured in this round over two copies of `main` = `6c068dea` — one carrying the published collector,
one the repaired one — each drift applied to the published text, `sh reproduce.sh` run, the file
restored. The declared build, which is the package's own: CPython 3.9.6, standard library only, no
other interpreter involved.

| probe | published collector | this erratum |
|---|---|---|
| baseline, unmodified | exit 0, `ALL STEPS PASSED (9 steps)` | exit 0, `ALL STEPS PASSED (9 steps)` |
| `manuscript.md:635`, **first** occurrence of the literal changed to `(12 steps)` | **exit 0**, `ALL STEPS PASSED (9 steps)` | **exit 1**, `[FAIL] manuscript.md states [12 9] across 2 occurrence(s), which disagree with each other; this run executed 9` |
| `manuscript.md:635`, **second** occurrence changed to `(12 steps)` | exit 1, `[FAIL] manuscript.md states [12] as the step count; this run executed 9` | exit 1, the same finding |
| `README.md:13`, a single occurrence, changed to `(12 steps)` | exit 1, `[FAIL] README.md states [12] as the step count; this run executed 9` | exit 1, the same line |
| every change reverted | exit 0, `ALL STEPS PASSED (9 steps)` | exit 0, `ALL STEPS PASSED (9 steps)` |

The second row is the defect: the run a reader would call green is the one whose document contradicts
itself. The third and fourth rows are the controls showing the collector was never blind — it read
one value, and that value happened not to be the one that drifted.

## What changed, and what did not

The repair reads **every** occurrence, takes the distinct values, and requires them to agree with
each other and with the number this run executed. Three outcomes are named apart rather than
collapsed into one failure: a carrier that states no literal at all, occurrences that disagree with
each other, and a single stated value that disagrees with the run. The failure sentence says which
one it is, so the next reader does not have to re-derive it.

What did not change is the package's arithmetic, and it is stated as artefacts rather than as a
claim: after the repaired run, `rates.json` `127bd25d…`, `decay.json` `18a9c345…` and `depth2.json`
`0db9d623…` are sha256-identical to the committed files, and `git status --porcelain` over the
package shows this round's own edit and nothing else. The run's readings are the published ones —
plants 7/7, 8/8 and 7/7; depth-1 `111/322 = 0.345` with Wilson `[0.2949, 0.3982]`; depth-2 pooled
`0.892` with `34/292`; decay `caret 0.781` against `exact 1.000` at k = 12; corpus 102 entries with
all 166 placements and prunes resolving. The verdict line still prints the literal form the
manuscript quotes, and the exit-code contract is untouched.

Two lines of the run's output did change: the collector's `[ok]` lines now also name **how many**
occurrences were read, so a reader of a green log can see that both occurrences of the doubled line
were read. No reader of that log exists — the manuscript quotes the verdict line and nothing else —
so nothing downstream moves.

## What this round does not repair

The editorial decision that published this package carried four items (`6650620273`, its *What is
carried* section). This round takes the fourth — the collector's unit, which that decision names as
*the one a future correction round should take first* — and leaves three: the floating-point lower
bound printed as `0.0` in an artefact cell, the prose census's single declared exception whose reason
lives in a program rather than in the manuscript, and the second failure line whose first clause
attributes a doctored body number to the rates table. Each is owed its own round inside this round's
clock; none of them makes a claim in the manuscript false today.

## What the tree-wide gate can and cannot see here

`stepgate` reports this package's two document claims as **`NOT CHECKED`** — not a pass, not a
finding — because the script derives its count at run time, a form the gate does not read. This
repair does not change that, and giving the gate a reader for that form is a separate item rather
than part of this erratum. So the receipt for **this** defect is the collector's own two-sided proof
above, taken in the package, and it is deliberately not a gate verdict.
