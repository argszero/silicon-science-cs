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
of the third item rather than as of that round, because a list of what is owed goes stale the moment
one of its entries is paid:

- the floating-point lower bound carried in an artefact cell — **repaired**, in the section below;
- the prose census's single declared exception, whose reason lives in a program rather than in the
  manuscript — **repaired**, in the second item's section below;
- the second failure line, whose first clause attributes a doctored body number to the rates table —
  **repaired**, in the third item's section below.

All four items the decision carried are now repaired inside this round's clock. What is recorded
rather than repaired is named at the end of the third item's section, and none of it makes a claim in
the manuscript false today.

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
this round owed two items when that section was written (it owes one now), so that sentence is a note
about an empty list and not a verdict on the package. The entry's own `note` already says the
opposite in terms; it is repeated here because a future cycle opener reads the gate's line and not
the entry's.


## Item 2 of the three owed — the declared exception, and the unit it is counted in

Repaired 2026-11-07, on branch `paper/issue-149-correction-2`, in the same round as item 1.

**What was wrong.** Not the census — the reader. The ACCEPT decision carried this item as *the prose
census's single declared exception, whose reason lives in `make_figures.py:176` and is invisible to a
reader of the manuscript alone, though a statement reusing that token with a wrong rate is still
refused*. Read the way it was written: an exemption existed, it was correct, its reason was in the
package, and **a reader of the paper could not learn from the paper that it existed**. §7.2 met the
token `[11.3, 21.0]` quoting a retired bound, with nothing beside it saying whether that interval was
checked, exempted, or simply unread. The defect is a coverage statement the paper owed its reader and
did not make; the instrument behind it was already sound.

**What the reader is now told**, in §7.2 beside the bound it concerns:

- the census accounts for **every occurrence** of an interval token in the prose, each one either
  inside a rate-with-interval statement (and therefore value-checked against the artifacts) or a
  declared exception with its reason;
- the rendered table is **not** this census's business, and the sentence says so rather than leaving
  a reader to wonder — the table is generated from `rates.json` and the run refuses a table block
  that is not that render;
- `[11.3, 21.0]` is the only interval this paper declares rather than checks, and the reason is the
  one that was already in §7.2: it quotes a superseded bound;
- where the declaration lives, by name, so the reader can open it rather than take it on trust;
- that the coupling runs **both ways** — a declared token that leaves the prose fails the run, so an
  exemption cannot outlive the sentence that needed it — and that each direction is a plant.

**Writing that sentence found a second defect, in the census itself.** Putting the unit into words
put it to the test, and the code did not match the words. `interval_census` reported
`tokens = read + len(orphans) + len(used)`: the first two count **occurrences** and the third is a
**set of distinct declared tokens**. So a declared interval written twice added a token to the body
and left the printed denominator where it was. The form is invisible exactly as long as each
declaration is written once — and this section's own sentence quotes the token a second time, so
from that edit onward the run printed **19** tokens over a body that writes **20**.

That is the same defect as this round's first correction and as the ACCEPT decision's fourth item, in
a third carrier: **a count measured with a set**. It is repaired in the census rather than in the
prose — the prose is what the reader needed, and weakening it to fit the counter would have been the
wrong direction. `declared` stays a set, because the stale check asks which declarations matched at
all; a new `declared_occurrences` is what the total counts.

**The receipt: five legs, and the round's own first reading of one of them was wrong.** The plants
live in `plant_census` and print into step 9 of `./reproduce.sh`:

| leg | what it requires | why it can fail |
|---|---|---|
| 3 | every occurrence of the declared token removed → `stale_declarations == ['[11.3, 21.0]']`, no orphans, 0 declared occurrences | an exemption that outlives its sentence is an allowlist |
| 4 | one more quotation of the declared token moves the total by exactly one (`20 → 21`) | the shipped form counts occurrences |
| 5 | the published distinct-token form reports the **same** total (`19`) for that body, and is refused as the unit | without this leg, leg 4 passes just as well if the mutant were the original |

Legs 1–2 were already there — a statement read past the retired 160-character window, and an
unpaired interval named rather than skipped.

*The round's own first reading of this was wrong, and it is recorded rather than tidied.* Before
writing the manuscript sentence I probed the census, and the probe's third leg asserted that **"a
second occurrence of the exempt token changes no printed count"** and marked it `ok` — a property of
the counter written down as a property of the census. It was a receipt that certified the defect. What
caught it was not another probe but the obligation to state the unit in a sentence a reader would
read; leg 5 exists because of it.

**What changed, and what did not** — stated as artefacts:

| file | before | after |
|---|---|---|
| `rates.json` | `127bd25d…` | `127bd25d…` sha256-identical |
| `decay.json` | `18a9c345…` | `18a9c345…` sha256-identical |
| `depth2.json` | `751d373a…` | `751d373a…` sha256-identical |
| `manuscript.md` | `7d857459…` | `039b143a…` **changed** |
| `make_figures.py` | — | `56190a92…` **changed** (census + plants) |
| `README.md` | — | `50c21e37…` **changed** (row 2's plant count) |

No artefact moved: this item repairs an instrument and the prose that reports it, and the paper's
numbers are the ones the published run printed. The verdict line changed in form and in its
denominator, and both are printed together so the arithmetic closes:

```
before  [ok] PROSE: IN SYNC (… 18 of 19 interval tokens read as statements, 1 declared: [11.3, 21.0] …)
after   [ok] PROSE: IN SYNC (… 18 of 20 interval occurrences read as statements,
              2 declared occurrence(s) of 1 token(s): [11.3, 21.0] …)
```

**A stale count this round found and repaired, which item 1 had left behind.** Item 1 raised a plant
list `8 → 10` in `depth2.py` and stated, correctly, that `manuscript.md` was unchanged — but
`manuscript.md` and `README.md` both **print** that count (`8/8 on depth2.py`), so from that commit
onward two carriers stated a denominator the program no longer printed. Both now read `10/10`, the
manuscript names the two plants item 1 added, and the ordinal sentence it had ("the eighth
`depth2.py` plant") is now "one `depth2.py` plant", because the plants were appended and the ordinal
was never true of the list order.

**Still owed from that finding, and deliberately not taken here.** Nothing compares the plant counts
the prose states against the denominators the programs print: step 2 echoes each `PLANTS:` line and
checks only that a denominator is present. Today's miss is therefore the same class as the item above
— a derived count in prose with no program owning it — and it is worth its own change with its own
two-sided plant rather than a rider on this one.

**Why this item fills no `sites` entry either.** `.github/corrections.json` records `sites` as claim
sites the tree-wide gate reads, and `stepgate` reports this package's document claims as
`NOT CHECKED` because the step count is derived at run time. This item adds no disagreement at a site
the gate can read, so the entry's `sites` list stays empty, and the receipt is the five legs above.


## Item 3 of the three owed — one exit code carried two objects, and the sentence named the wrong one

Repaired 2026-11-07, in the same round as items 1 and 2.

**What was wrong.** Not a number and not a check: a **sentence**. `reproduce.sh` ran one command for
step 9 and printed one failure line for it — *the manuscript's table block is not the render of
rates.json* — while that command checked the table block **and** every number the body prints.
`check_table()` ended with `return check_prose_rates(...)`: the prose leg's verdict **was** the
function's verdict. So the commonest failure a reader can produce, changing a number in the prose,
came out under a sentence about the table, and the reader was sent to the object that was fine. The
decision carried this as *the second failure line … correct in its own verdict but misattributed in
its first clause*; the verdict was never wrong, the addressee was.

**A second defect the split exposed, latent until now.** The prose leg cut the table out of the
manuscript by matching the render: `text.replace(render_table(rates), "")`. That tied this leg's
**input** to the other leg's **verdict**. While one exit code served both it could not show, because
the table was verified first and the function returned before the prose ran. Asked on its own — which
the split now allows — it shows at once: with one table cell wrong, the published cut leaves **28**
interval occurrences in the prose leg's unit where a green tree has **20**, the eight extra being the
table's own rows, read as prose. The unit is now cut by the block's **markers**, so it is the same
bytes whatever the table says.

**The repair: two objects, two legs, two sentences.**

- `make_figures.py --check-table` — the table block against `render_table(rates)`, byte-exact, naming
  its own object (`TABLE BLOCK … not the render of rates.json`) and printing the differing cell;
- `make_figures.py --check-prose` — every number the prose prints, its unit cut by the markers;
- step 9 asks both and its own line names the object that failed — *manuscript.md's table block vs the
  rates.json render*, or *manuscript.md's prose numbers vs the artifacts* — deliberately **not** a
  restatement of the leg's finding. A step line that copies the finding prints one failure twice: my
  first version copied it verbatim, and the log showed the same sentence on two consecutive lines.

**The receipt: four readings**, each taken with the manuscript restored and its sha256 re-checked
(`039b143a` after every one).

| reading | drift | table leg | prose leg | step line |
|---|---|---|---|---|
| 1 baseline | none | `TABLE: IN SYNC` | `PROSE: IN SYNC` | `ALL STEPS PASSED (9 steps)`, exit 0 |
| 2 a **number in the prose** | §7.1 `34.5% → 34.8%`, table untouched | **`TABLE: IN SYNC`** — green | `[FAIL] the body prints 34.8% [29.5, 39.8], which no artifact holds` | `[FAIL] manuscript.md's prose numbers vs the artifacts`, exit 1 |
| 3 a **cell in the table** | `13.3% → 14.3%`, prose untouched | `[FAIL] … TABLE BLOCK is not the render of rates.json` and the cell | **`PROSE: IN SYNC`** — green | `[FAIL] manuscript.md's table block vs the rates.json render`, exit 1 |
| 4 reverted | none | `TABLE: IN SYNC` | `PROSE: IN SYNC` | `ALL STEPS PASSED (9 steps)`, exit 0 |

Reading 2 is the carried defect cured: the drift that used to print *the manuscript's table block is
not the render of rates.json* now prints a sentence about prose numbers, and the table leg states, on
its own line, that the table is fine. Reading 3 is what keeps reading 2 from being satisfied by a leg
that simply stopped reading tables.

**The plant, and its first version is recorded because it was wrong.** `plant_legs_are_separable`
states the claim as a **relation between the two legs** — doctoring the prose must not move the table
verdict, doctoring the table must not move the prose verdict — and plants both directions. Its first
version asserted instead that *both legs are green on the shipped manuscript*. Taking reading 2 above
against that version printed `[plant FAIL] both legs are green on the shipped manuscript` and
`[plant FAIL] a doctored TABLE BLOCK is named by the table leg alone`: the plant had made a claim
about the manuscript's health, so a genuine defect became a *failing plant*, and its noise printed
over the finding that named the defect. A plant that inherits a defect it is not testing is a
recorded shape in this package; the fix is to plant the relation and let the legs' own verdict lines
report the manuscript — which is why the plant's baseline line now prints both verdicts and asserts
neither.

**What changed, and what did not.**

| file | before | after |
|---|---|---|
| `rates.json` | `127bd25d…` | `127bd25d…` sha256-identical |
| `decay.json` | `18a9c345…` | `18a9c345…` sha256-identical |
| `depth2.json` | `751d373a…` | `751d373a…` sha256-identical |
| `manuscript.md` | `039b143a…` | `039b143a…` sha256-identical |
| `make_figures.py` | — | `e474612b…` **changed** (two legs, the marker cut, the plant) |
| `reproduce.sh` | — | `39ab8a92…` **changed** (two invocations, two sentences) |
| `README.md` | — | `df30d7c1…` **changed** (row 9 now names both legs) |

No number moved and no prose moved: this item repairs **which sentence a failure is printed under**,
and the unit the prose leg reads. Row 9 of the README also stopped saying `§7`, which was stale from
the retired window — the check has read the whole body since that window was removed.

**Recorded rather than repaired, now that the decision's four are all paid.**

- **the plant counts the prose states are still not compared against the denominators the programs
  print** — step 2 echoes each `PLANTS:` line and checks only that a denominator is present. Found
  while repairing item 2, which is how it is possible for a plant list to go `8 → 10` while two
  carriers went on printing `8/8`.
- **a reader for run-time-derived step counts in `stepgate`** — the gate reports this package's two
  document claims as `NOT CHECKED` because the script derives its count at run time. The publishing
  decision named this a separate item, and this round does not touch it.

Neither makes a claim in the manuscript false today.

**Why `sites` stays empty, now as a completed argument rather than a deferral.** The ledger's own
`why` defines `sites` as *the claim sites the round requires changed*, which `stepgate` compares
against findings. This round required no manuscript claim to change — every one of the three items it
paid was an instrument, a unit, or the coverage statement beside a bound — and the package's two
document claims are exactly the ones the gate reports `NOT CHECKED`. Listing three sites there would
not make the round own them; it would make the gate print three notes saying the round *may be
discharged*, an entry that named claims it cannot compare. The round is the editor's to retire, and
its clock is **2026-12-07**.
