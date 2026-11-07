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
carried* section). The first correction round took the fourth — the collector's unit, which that
decision names as *the one a future correction round should take first*. The list below is current as
of the second item rather than as of that round, because a list of what is owed goes stale the moment
one of its entries is paid:

- the floating-point lower bound carried in an artefact cell — **repaired**, in the section below;
- the prose census's single declared exception, whose reason lives in a program rather than in the
  manuscript — still owed;
- the second failure line, whose first clause attributes a doctored body number to the rates table —
  still owed.

Each of the two still owed is owed its own round inside this round's clock, and neither makes a claim
in the manuscript false today.

## What the tree-wide gate can and cannot see here

`stepgate` reports this package's two document claims as **`NOT CHECKED`** — not a pass, not a
finding — because the script derives its count at run time, a form the gate does not read. This
repair does not change that, and giving the gate a reader for that form is a separate item rather
than part of this erratum. So the receipt for **this** defect is the collector's own two-sided proof
above, taken in the package, and it is deliberately not a gate verdict.


## Item 1 of the three owed — the floating-point lower bound at `k = 0`

Repaired 2026-11-07, on branch `paper/issue-149-correction-2`, cut from `origin/main` = `2703762`
(the merge of the first correction round's PR #170) after confirming the merge base at `f9a1535`.

**What was wrong.** `depth2.json`'s `ecosystems.pypi.exceptions.wilson95_among_refutable[0]` read
`6.938893903907228e-18` where every carrier prints `0.0`. A 95 % Wilson interval at a zero count is an
upper bound whose lower end is **0 exactly**, by construction — no observed event places any mass
below it. The published form **computed** that end instead of stating it, and subtracting below a zero
count leaves a floating-point residue on some denominators and not on others.

**The signature was in the same artefact, and no carrier could see it.** One function, one `k = 0`,
two denominators in the same dictionary:

| cell | denominator `n` | published lower end |
|---|---|---|
| `wilson95` | 63 | `0.0` — clean |
| `wilson95_among_refutable` | 27 | `6.938893903907228e-18` |

That is why a published package with every gate green carried it: the printed end was a property of
the **denominator**, not of the measurement. And the repair a reader would reach for — a clamp — was
already there, on the wrong side: `max(0.0, ·)` hides a negative residue and does nothing to a
positive one.

**Where it was repaired.** In the interval function's `k = 0` leg, not in the carrier that prints the
value: `wilson` now returns the exact `0.0` the interval has, rather than the value the arithmetic
happens to give. Two copies of that function exist in this package — `depth2.py`, which produced this
cell, and `ambiguous.py`, which produced `rates.json` — and **both** are repaired, because fixing only
the copy that happened to show the residue would leave the same defect latent in the other. Measured
consequence in the second copy: none. `rates.json` carries no residue under either form and is
byte-identical after the run.

**The receipt, and it is two-sided.** The repair ships inside the package's own plant list
(`PLANTS: 10/10 ALL PASS`, previously 8):

- `plant the k=0 lower end is exactly 0.0 on every denominator` — sweeps `n` over 1…199 and requires
  the lower end to *be* `0.0`, not to print as one, at every denominator in the sweep;
- `plant the residue the published form leaves at k=0 is refused` — the published form is carried in
  the plant as its negative leg, and the same predicate must refuse it. It does, and it prints the
  refused value at `n = 27`. Without that leg the first plant would pass just as well if the mutant
  and the original were the same object, which is a failure this package has recorded before.

Measured over the wider range: **37 of the 399** denominators in 1…399 reproduce a residue under the
published form, so the negative leg is not a lucky case.

**What changed, and what did not** — stated as artefacts, and one of them did change:

| file | before | after |
|---|---|---|
| `rates.json` | `127bd25d…` | `127bd25d…` sha256-identical |
| `decay.json` | `18a9c345…` | `18a9c345…` sha256-identical |
| `depth2.json` | `0db9d623…` | `751d373a…` **changed** |
| `manuscript.md` | `7d857459…` | `7d857459…` sha256-identical |

`depth2.json` changed in **exactly one line**, and `git diff` over the file is that line and nothing
else: the lower end `6.938893903907228e-18` → `0.0`. The upper end `0.12455903714463581` is untouched.
The prose does not move because it never printed this end at full precision — the manuscript renders
the interval to four decimals, where both values are `0.0000` — so **this correction is invisible in
print and visible only in the artefact**, which is precisely the class of defect no carrier can catch.
No sub-1e-15 non-zero float remains in any of the three artefacts after the run, and
`git status --porcelain` over the package shows this item's two source files and the one artefact.

**Why this item fills no `sites` entry.** `.github/corrections.json` records `sites` as claim sites the
tree-wide gate reads. This defect occupied none: it lived in an artefact cell, and the gate does not
read artefacts. So it is discharged by the artefact and the plant above, and the entry's `sites` list
stays empty — a site that occupies no finding prints a note in place of a receipt.

**One reading to carry forward, recorded rather than fixed.** With no `sites` listed, `stepgate`
prints for this round: *"occupies no finding, so the claims it named now agree — the round may be
discharged and the entry retired"*. An entry that named no claims cannot have claims that agree, and
this round still owes two items, so that sentence is a note about an empty list and not a verdict on
the package. The entry's own `note` already says the opposite in terms; it is repeated here because a
future cycle opener reads the gate's line and not the entry's.
