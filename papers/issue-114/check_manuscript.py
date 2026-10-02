#!/usr/bin/env python3
"""Check the manuscript's numbers against `canonical_results.json`.

A paper whose every number is produced by a script owes a reader a mechanical link between
the sentence and the artefact.  This package states that link explicitly, in the manuscript's
**Appendix A — claims and their artefacts**, one row per claim:

    | C7 | the worst matched-specificity detection span across the twelve pin sets | 1.370 | findings/p1_worst_alignment_span |

and this checker verifies three separate things about that table:

  1. **the value** -- the artefact value at that path, rendered to the SAME number of decimals
     as the claim, equals the claim string.  (Comparing rounded-to-displayed precision is
     what makes the check bite at the precision the reader sees: a drift of 0.0004 is caught
     where the paper says three decimals and ignored where it says two, which is correct.)
  2. **the citation** -- every claim id is cited in the body text (outside the appendix), and
     every `[C..]` marker in the body exists in the table.  A claim in the appendix that no
     sentence uses, or a marker that resolves to nothing, is a broken link either way.
  3. **the figures** -- every figure in `figures/manifest.json` is embedded in the manuscript
     and every embedded figure exists in the manifest, so the paper cannot cite a picture it
     does not ship or ship one it never shows.

A missing or unreadable manuscript is a FAIL, not a traceback: "I could not read the thing I
was asked to check" and "the thing is wrong" are different sentences and both must be said.

Usage: python3 check_manuscript.py
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPT = os.path.join(HERE, "manuscript.md")
CANON = os.path.join(HERE, "canonical_results.json")
MANIFEST = os.path.join(HERE, "figures", "manifest.json")

APPENDIX_HEADING = re.compile(r"^#+\s*Appendix A\b", re.M)
ROW = re.compile(r"^\|\s*(C\d+)\s*\|\s*(.+?)\s*\|\s*`?([^|`]+?)`?\s*\|\s*`?([^|`]+?)`?\s*\|\s*$",
                 re.M)


def walk(obj, path: str):
    """Resolve a slash-separated path; a numeric segment indexes a list."""
    cur = obj
    for part in path.split("/"):
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            if part not in cur:
                raise KeyError(part)
            cur = cur[part]
    return cur


def render(value, decimals: int) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def decimals_of(s: str) -> int:
    s = s.strip().rstrip("%")
    if "." in s:
        return len(s.split(".")[1])
    return 0


def main() -> int:
    if not os.path.exists(MANUSCRIPT):
        print(f"MANUSCRIPT: FAIL -- {MANUSCRIPT} is absent (nothing to check)")
        return 1
    try:
        text = open(MANUSCRIPT, encoding="utf-8").read()
    except Exception as exc:                      # noqa: BLE001 - an unreadable document is a FAIL
        print(f"MANUSCRIPT: FAIL -- cannot read it: {type(exc).__name__}: {exc}")
        return 1
    D = json.load(open(CANON))

    m = APPENDIX_HEADING.search(text)
    if not m:
        print("MANUSCRIPT: FAIL -- no 'Appendix A' claims table found")
        return 1
    body, appendix = text[:m.start()], text[m.start():]

    rows = ROW.findall(appendix)
    if not rows:
        print("MANUSCRIPT: FAIL -- the claims table has no rows")
        return 1

    bad_value, bad_path, uncited, mismatched = [], [], [], []
    for cid, claim, value, path in rows:
        value = value.strip()
        try:
            actual = walk(D, path.strip())
        except (KeyError, IndexError, ValueError) as exc:
            bad_path.append(f"{cid} -> {path} ({type(exc).__name__}: {exc})")
            continue
        want = render(actual, decimals_of(value))
        if want != value.rstrip("%"):
            bad_value.append(f"{cid}: claims {value}, artefact says {want} ({path})")
        if f"[{cid}]" not in body:
            uncited.append(cid)

    markers = set(re.findall(r"\[(C\d+)\]", body))
    table_ids = {r[0] for r in rows}
    undefined = sorted(markers - table_ids)

    # figures: both directions
    manifest = json.load(open(MANIFEST))
    shipped = {os.path.basename(f["figure"]) for f in manifest["figures"]}
    embedded = set(re.findall(r"!\[[^\]]*\]\((?:\./)?(?:figures/)?([^)\s]+\.png)\)", text))
    missing_file = sorted(f for f in embedded if f not in shipped)
    never_shown = sorted(shipped - embedded)

    print("=" * 78)
    print("issue #114 -- manuscript vs canonical_results.json")
    print("=" * 78)
    print(f"  claims in the table      : {len(rows)}")
    print(f"  values verified          : {len(rows) - len(bad_value) - len(bad_path)}")
    print(f"  uncited claim ids        : {len(uncited)} {uncited if uncited else ''}")
    print(f"  body markers undefined   : {len(undefined)} {undefined if undefined else ''}")
    print(f"  figures shipped/shown    : {len(shipped)} shipped, {len(embedded)} embedded")
    for label, items in (("VALUE MISMATCH", bad_value), ("BAD ARTEFACT PATH", bad_path)):
        for it in items:
            print(f"  {label}: {it}")
    if missing_file:
        print(f"  EMBEDDED BUT NOT SHIPPED: {missing_file}")
    if never_shown:
        print(f"  SHIPPED BUT NEVER SHOWN : {never_shown}")

    ok = not (bad_value or bad_path or uncited or undefined or missing_file or never_shown)
    print()
    print("MANUSCRIPT: " + ("ALL CLAIMS ANCHORED" if ok else "PROBLEMS ABOVE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
