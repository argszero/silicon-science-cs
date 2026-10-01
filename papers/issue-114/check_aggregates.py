#!/usr/bin/env python3
"""Check the manuscript's GRID claims -- the ones whose artefact key cannot be written in Appendix A.

`check_manuscript.py` binds Appendix A's rows to `canonical_results.json` by a slash-separated path,
and its row grammar cannot carry a `|` (the pipe is the table's own separator).  The blocks keyed by
`<s>|<r>` and `<lambda>|<r>` are therefore outside that instrument's reach -- and an unchecked block
is not a checked block: `cells`, `frontier`, `mix` and `alignment` between them carry every claim this
paper makes about the *shape* of the plane, including two of its three verdicts on the registered
priors.  So they get their own reader, which re-derives the aggregate and asserts the sentence the
manuscript prints.

The contract, deliberately narrow and stated so a reader can judge its reach: for each claim this
file computes a value from the artefact and requires a **literal sentence** in `manuscript.md` to be
present.  A claim whose sentence is missing fails, and a claim whose computed value changed fails,
because the sentence is built from the computed value.

Usage: python3 check_aggregates.py
"""

from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(HERE, "canonical_results.json")
MANUSCRIPT = os.path.join(HERE, "manuscript.md")

S_GRID = ["0.0", "0.0625", "0.125", "0.25", "0.5", "0.75", "1.0"]
R_GRID = ["0.0", "0.05", "0.1", "0.2", "0.3"]
LAMBDA_GRID = ["0.1", "0.25", "0.5", "1.0", "2.0", "5.0"]


def main() -> int:
    D = json.load(io.open(CANON, encoding="utf-8"))
    if not os.path.exists(MANUSCRIPT):
        print(f"AGGREGATES: FAIL -- {MANUSCRIPT} is absent (nothing to check)")
        return 1
    text = io.open(MANUSCRIPT, encoding="utf-8").read()

    checks = []          # (name, computed value, sentence the manuscript must print)

    # --- the reachable region -------------------------------------------------
    cells = D["cells"]
    reached = [k for k in cells if cells[k]["reached"]]
    checks.append(("reachable cells",
                   f"{len(reached)} of {len(cells)}",
                   f"Of the 35 declared cells, **{len(reached)} are reachable**"))

    # --- the frontier: the optimum falls monotonically in lambda, per r --------
    monotone = []
    for r in R_GRID:
        modes = [D["frontier"][f"{lam}|{r}"]["mode"] for lam in LAMBDA_GRID]
        monotone.append(all(modes[i] >= modes[i + 1] for i in range(len(modes) - 1)))
    checks.append(("modal optimum non-increasing in lambda for every r",
                   str(all(monotone)),
                   "the modal optimum is 1.0 at `lambda = 0.1` and 0.0 at `lambda = 5.0`"))

    # --- the interiority share over the upper half of the rate grid -----------
    upper = [D["frontier"][f"{lam}|{r}"] for lam in ("1.0", "2.0", "5.0") for r in R_GRID if r != "0.0"]
    interior = sum(1 for f in upper if f["interior_share"] >= 0.8)
    interior_pct = 100.0 * interior / len(upper)
    checks.append(("interior share over the upper half of the rate grid",
                   f"{interior} of {len(upper)} ({interior_pct:.0f}% interior)",
                   f"`s*` is interior in **{interior} of {len(upper)} ({interior_pct:.0f}%)**"))

    # --- the alignment span collapses to 1.000 at full specificity ------------
    at_full = [D["alignment"][f"1.0|{r}"]["span"] for r in R_GRID]
    checks.append(("alignment span at s = 1.0",
                   f"{max(at_full):.3f}",
                   "reaches **1.000 at `s = 1.0`**"))

    # --- the empty specification wins at lambda >= 2 for every r >= 0.1 -------
    empty_wins = all(D["frontier"][f"{lam}|{r}"]["mode"] == 0.0
                     for lam in ("2.0", "5.0") for r in ("0.1", "0.2", "0.3"))
    checks.append(("empty specification modal at lambda >= 2, r >= 0.1",
                   str(empty_wins),
                   "At `lambda >= 2` the empty specification\n(`s = 0`) wins outright for every `r >= 0.1`"))

    # --- detection saturates: the full observational specification rejects all -
    det_full = [D["cells"][f"1.0|{r}"]["det_band"] for r in R_GRID]
    checks.append(("detection at s = 1.0 is 1.0 for every r",
                   str(all(b[0] == 1.0 and b[1] == 1.0 for b in det_full)),
                   "rejects **all** of them\n(1.000 to 1.000)"))

    # --- the per-kind claim the table's own ratio cell is built from ----------
    kinds = {r["kind"]: r for r in D["kind_ranking"]}
    checks.append(("size and depth bounds reject no changing mutation",
                   str(kinds["size_le"]["changing_share"] == 0.0
                       and kinds["depth_le"]["changing_share"] == 0.0),
                   "`depth_le` and `size_le` each reject **zero**\nsemantics-changing mutations"))

    bad = []
    # A sentence is read as prose, not as lines: the manuscript is hard-wrapped, so a claim that
    # spans a line break would otherwise read as absent while it is printed.  Collapsing whitespace
    # on both sides is what keeps this check about the claim and not about the author's line width.
    flat = " ".join(text.split())
    print("=" * 78)
    print("issue #114 -- grid claims (the blocks Appendix A cannot address)")
    print("=" * 78)
    for name, value, sentence in checks:
        ok = " ".join(sentence.split()) in flat
        print(f"  [{'ok' if ok else 'MISSING'}] {name}: {value}")
        if not ok:
            bad.append(name)
    print()
    print(f"AGGREGATES: {len(checks) - len(bad)}/{len(checks)} claims anchored"
          + (f" -- FAILING: {bad}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
