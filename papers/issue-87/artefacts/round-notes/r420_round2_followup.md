# R420 — the R446 follow-up items (journal revision round 2, follow-up 1)

The editorial re-check at `0d33c51` (2026-09-22T02:41Z) confirmed **defect (D) discharged** — it ran the thing on
two foreign builds and read the `BUILD_BOUND` / `RENDER_BOUND` / `NOT RUN` lines with their declarations — and
left **three items**, all in the text and instruments the fix *added*. This is the record of those three.

## Which clock this round numbers against

The journal's clock counts **editor decisions**, and this thread's open decision is **round 2** (the R444
decision; `verify_revision_round2.py` reads its four items). The re-check's items are a **follow-up** to that
same round — a comment asking for a further change does not open a round — so this turn is *round 2, follow-up
1*. The previous turn's artifacts numbered themselves "round 3" (the author's turn count), which the re-check
filed as a second numbering basis, the same species as the two bases for one step list that the previous round
repaired. Repaired here rather than filed again: the verifier is renamed
**`verify_revision_round2_followup.py`** and its header states which clock its name uses.

## Item 1 — the verifier's interpreter is declared, and a missing dependency is `NOT RUN`

**Defect.** The verifier pinned `PY = "/usr/bin/python3"` for its child processes and printed no build line, so
on a host whose `/usr/bin/python3` carries no numpy, item 3 read the child's traceback as `(1, '?')`, the verdict
line read **`(D) NOT DISCHARGED`**, and the exit code was 1 — a finding about the *interpreter* printed as a
finding about the *manuscript*. That is precisely the rule this round's required change is about (*a reading
names the build it is read against*), not applied to the instrument that reports the discharge.

**Repair, at the object.** Two interpreters are now resolved and BOTH are printed with the versions that enter
the comparison: `$PY` (this file's own, stdlib only) and `$CMP_PY` (the comparator's, so it needs numpy). A
caller-named interpreter (`--cmp-py`, else `$CMP_PY`) is **binding** — falling back silently would answer a
different question than the one asked — while the default path walks the declared candidate list
(`/usr/bin/python3`, the study's second build) and prints its choice. Where no candidate can carry numpy, item 3
is **`NOT RUN`** and the verdict is **`(D) NOT ASSESSED`** with exit **2** — the journal's own code for *not run*
— never `NOT DISCHARGED`.

**The root cause was one level down, and is repaired there too.** `build_bound.py` itself raised
`ModuleNotFoundError` from `build_line()` before printing anything, so a *caller* saw exit 1 — i.e. `FAIL`, i.e.
a departure, the one thing the comparator exists to detect. It now prints `build read: python X / numpy ABSENT`,
the words `NOT RUN`, the interpreters it checked, and exits **2**; `reproduce.sh` step 2/5 distinguishes that code
from a departure and stops with *"the digest comparison could NOT BE TAKEN at this interpreter … nothing was
compared, so this run cannot report ALL GREEN"*.

**Measured.** Comparators verdicts at the declared build: unperturbed `(0, BITWISE)`, 1-ULP plant
`(0, BUILD_BOUND)`, `1e-5` plant `(1, FAIL)`, structural plant `(1, FAIL)`. `NOT RUN` path at
`~/.local/bin/python3.12`: exit **2**, `verdict: NOT RUN`, `NOTHING WAS COMPARED`, no traceback. Verifier with
`CMP_PY` naming that interpreter: **`(D) NOT ASSESSED`, exit 2, and the words `NOT DISCHARGED` appear nowhere.**

## Item 2 — the matplotlib absence is local, not a property of the interpreter

**Defect.** The README (and the response comment) said step 3/5 prints `NOT RUN` because that interpreter has "no
matplotlib", and that no foreign renderer is installed — false on the re-check's host, which measured
**matplotlib 3.11.1** at the same path and step 3/5 printing **`RENDER_BOUND` for all three figures, exit 0**.

**Repair.** The absence is stated as a property of **the environment the package was authored in**, and the
measured reading is recorded with its attribution *(the editorial re-check at `0d33c51`: `RENDER_BOUND`,
renderer 3.11.1 against the pinned 3.9.4, exit 0)* — which is the stronger evidence for the step's own claim,
since the step exists to report rather than stop on a rendering.

## Item 3 — a margin is arithmetic on a named number

**Defect.** "`1e-8` is three orders above the `1.610e-16` a foreign build returns" — `1e-8 / 1.610e-16` is
**7.8** orders, and the phrase fits a *different* number (`2.192e-11` → 2.7 orders) which `reproduce.sh`'s own
copy of the claim named. Two carriers, two numbers, one sentence.

**Repair.** Both carriers now state the same three margins, each computed from the number it names: 1e-8 is
**2.7 orders above** the controls' worst foreign-build departure (`2.192e-11`), **7.8 orders above** the digest's
(`1.610e-16`), and **5.3 orders below** the smallest panel separation the manuscript claims (`2.153e-03`,
`panel.q6_matched_vs_rbf.value.median_abs_sep[8]`). The verifier reads **both** carriers and fails if they
disagree, so the "two numbers for one claim" defect cannot come back silently.

## The verifier, read at its objects

`artefacts/assembly/verify_revision_round2_followup.py` — **13 of 13 items pass**, with battery **13 cases, 13
caught**. Three defects it caught in *itself* this turn, each one a class already written down in this study's
notes:

1. the verdict regex `(\w+)` matched `NOT` where the verdict reads `NOT RUN`, so the new `NOT RUN` item failed on
   its own success (`\w+` is not a phrase — a shape too crude for a two-word verdict);
2. `margins()` sliced the **raw** README at an offset taken in its **flattened** form and read a neighbouring
   number as the value of the phrase (the two strings are different offsets);
3. item 5c checked for a locality marker *anywhere in the paragraph*, so its plant — which removed the locality
   from the absence's own sentence — was **MISSED**. The check now reads the property in the sentence that states
   the absence, and the plant breaks exactly that. (A marker elsewhere left the absence itself generalised, which
   is the sentence the re-check called false.)

Also: the comparator's `numpy_at()` probe and `PINNED` are now **imported** by the verifier rather than copied,
so the two files cannot disagree about the build the records name.
