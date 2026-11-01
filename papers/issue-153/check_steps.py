#!/usr/bin/env python3
"""check_steps.py -- the step count a package *states*, read against the count its script *runs*.

Why this file exists, as the class rather than as an anecdote. A one-command reproduction ends
in a verdict line carrying the number of steps the run takes. That number is a claim about a
program, and the package states it in three carriers: `reproduce.sh` (the labels and the verdict
line), `README.md`, and `manuscript.md`. The program is the authority; the documents are copies.
The same drift has been corrected by hand on `#128`, `#145` and `#149`, and it opened a fourth time
on this package: the manuscript's reproducibility section enumerated **seven** steps while the
script ran **eight**, because the figure step had been added to the program and to the literal
verdict line, and the prose sentence between them was never touched. That history is the reason this
file exists, and it is stated here rather than in a round label no reader of this package can look
up.

The journal's own `stepgate.py` cannot see that shape, and its reach is stated rather than
implied: it reads a literal `(N steps)`, so a sentence that spells the number out -- "It runs
seven steps -- ..." -- is invisible to it. The literal forms in this package were all correct
while the prose was wrong, which is exactly how the defect survived a green run.

So this check reads **both** shapes, against one counter:

  * the counter: the `step "N/M ..."` invocations in `reproduce.sh` -- how many there are, and
    whether the labels number them 1..N with the same denominator;
  * the literal shape: `(N steps)` in `reproduce.sh`, `README.md` and `manuscript.md`;
  * the spelled-out shape: `<number word> steps` plus the enumeration that follows it, in
    `manuscript.md` -- the number word and the number of enumerated items must both equal the
    counter, so a step added to the program without being added to the sentence fails even when
    the digits elsewhere still agree.

A carrier that states nothing is reported as NOT STATED and fails: silence is not agreement, and
a check that passes by reading nothing is the defect it is meant to catch.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}


def read(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def counter(script):
    """The program's own count: the N/M labels on its step invocations."""
    labels = re.findall(r'(?m)^step "(\d+)/(\d+)\b', script)
    if not labels:
        return None, "no `step \"N/M ...\"` invocation found in reproduce.sh"
    nums = [int(a) for a, _ in labels]
    dens = {int(b) for _, b in labels}
    if nums != list(range(1, len(nums) + 1)):
        return None, "the step labels are not numbered 1..%d, they are %s" % (len(nums), nums)
    if len(dens) != 1:
        return None, "the step labels carry more than one denominator: %s" % sorted(dens)
    return len(nums), None


def literal(text):
    """Every literal `(N steps)` in a carrier."""
    return [int(m) for m in re.findall(r"\((\d+) steps\)", text or "")]


def spelled(text):
    """The spelled-out shape: a number word before `steps`, and the enumeration after it.

    Returns (word_value, item_count, items) or None when the carrier states no such sentence.
    """
    m = re.search(r"\b([A-Za-z]+)\s+steps\s+[-\u2013\u2014]+\s*(.+?)\s*[-\u2013\u2014]+\s+accumulating",
                  text or "", re.S)
    if not m:
        return None
    word = m.group(1).lower()
    if word not in WORDS:
        return None
    body = re.sub(r"\s+", " ", m.group(2)).strip()
    items = [p.strip() for p in body.split(",") if p.strip()]
    # the last item is written "and a check that ..." -- the conjunction is not an item
    if items and items[-1].lower().startswith("and "):
        items[-1] = items[-1][4:].strip()
    return WORDS[word], len(items), items


def main():
    script = read("reproduce.sh")
    if script is None:
        print("STEPS: FAIL -- reproduce.sh is not here")
        return 1
    total, why = counter(script)
    if total is None:
        print("STEPS: FAIL -- %s" % why)
        return 1
    print("  counter: reproduce.sh runs %d step(s), labels numbered 1..%d" % (total, total))

    bad = 0

    def ck(ok, msg):
        nonlocal bad
        print(("  [ok]   " if ok else "  [FAIL] ") + msg)
        if not ok:
            bad += 1

    # the literal shape, in the file that prints it and in the two that copy it
    lit = literal(script)
    ck(bool(lit), "reproduce.sh states a literal verdict count (%s)" % (lit or "NOT STATED"))
    for n in lit:
        ck(n == total, "reproduce.sh literal count %d == the %d steps it runs" % (n, total))
    for carrier in ("README.md", "manuscript.md"):
        text = read(carrier)
        if text is None:
            ck(False, "%s is not here" % carrier)
            continue
        vals = literal(text)
        ck(bool(vals), "%s states a literal count (%s)" % (carrier, vals or "NOT STATED"))
        for n in vals:
            ck(n == total, "%s literal count %d == the %d steps the script runs"
               % (carrier, n, total))

    # the spelled-out shape: the number word AND the enumeration, both against the counter
    manuscript = read("manuscript.md") or ""
    sp = spelled(manuscript)
    ck(sp is not None, "manuscript.md spells the count out before an enumeration")
    if sp is not None:
        word_val, n_items, items = sp
        ck(word_val == total, "the number word says %d, the script runs %d" % (word_val, total))
        ck(n_items == total, "the enumeration names %d items, the script runs %d steps"
           % (n_items, total))
        if bad:
            print("         enumerated: %s" % "; ".join(items))

    # a sentence that names a step the program does not have is a copy of a program that changed
    named = re.findall(r"the (\w[\w'-]*(?: [\w'-]+){0,4}) step\b", manuscript)
    if named:
        print("  note: manuscript.md names step(s) %s" % ", ".join(sorted(set(named))))

    if bad:
        print("STEPS: FAIL (%d disagreement(s) between the program and what states its count)" % bad)
        return 1
    print("STEPS: PASS -- %d steps, and every carrier that states the count agrees" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
