#!/usr/bin/env python3
"""Assert that every number printed in manuscript_skeleton.md's claim table is
still what the committed artifacts say.

The table in `manuscript_skeleton.md` is the manuscript's number source. A table
that nothing checks is a note; the #141 experience is that derived text goes stale
while the numbers it quotes are fine, so the check has to compare the *printed*
value against the *artifact* value, in both directions:

  1. read the table's rows out of the markdown,
  2. resolve the named key in the named artifact,
  3. compare.

Rows that do not name a single artifact key (the Wilson, law and plant rows) are
listed in `NOT_CHECKED` and printed as NOT CHECKED — silence is never a pass.

Usage: python3 check_claims.py [skeleton.md] [-v]
Exit: 0 all checked rows agree, 1 otherwise.
"""
import json
import re
import sys

SKEL = "manuscript_skeleton.md"
# The skeleton's table is the PLAN; the manuscript is what ships. Gating only the plan leaves the
# prose free to print a number the artifacts do not hold -- the defect class this package's own
# memory records from issue #128. So every value the table asserts must also appear in the manuscript.
MS = "manuscript_source.md"
MS_FALLBACKS = ("../manuscript_source.md",)   # the package root when this runs from research/
ARTIFACTS = {
    "npm": "snapshot_npm_d1_pilot.json",
    "pypi": "snapshot_pypi.json",
    "oci": "snapshot_oci.json",
}

# rows whose value is not a single artifact key (kept explicit, never implied)
NOT_CHECKED = {26: "values printed by wilson_separation.py, not stored in an artifact",
               27: "printed by ceiling_check.py",
               28: "printed by plant_coverage.py"}


def norm(s):
    s = s.replace("`", "").replace("*", "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def resolve(art, keyexpr, artifact_paths):
    """Resolve one key expression against an artifact. Supports:
         summary.a.b            -> scalar / list / dict
         summary.a (len)        -> length of list/dict
         rows[]... (sum over OK) -> per-row sum restricted to status == OK
       Returns (value_string, error_or_None).
    """
    data = json.load(open(artifact_paths[art]))
    m = re.match(r"rows\[\]\.(.*?)\s*\(sum over OK\)", keyexpr)
    if m:
        path = m.group(1).split(".")
        total = 0
        for row in data["rows"]:
            if row.get("status") != "OK":
                continue
            cur = row
            for p in path:
                cur = cur[p]
            total += cur
        return str(total), None
    want_len = "(len)" in keyexpr
    key = keyexpr.replace("(len)", "").replace("`", "").strip()
    cur = data
    for p in key.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return None, "key %r missing in %s" % (p, art)
        cur = cur[p]
    if want_len:
        if not isinstance(cur, (list, dict)):
            return None, "%s is not a list/dict, cannot take len" % key
        return str(len(cur)), None
    if isinstance(cur, dict):
        # render a histogram the way a manuscript prints it: {k: v, ...}
        return "{" + ", ".join("%s: %s" % (k, cur[k]) for k in sorted(cur)) + "}", None
    if isinstance(cur, list):
        return "[" + ", ".join(str(x) for x in cur) + "]", None
    return str(cur), None


def art_of(cell):
    c = cell.lower()
    for name in ARTIFACTS:
        if name in c:
            return name
    return None


def table_region(text):
    """The claim table runs from its header to the next blank line.

    A row inside that region IS a claim row — there is no such thing as a row
    there that is not one — so the region, not a regex, decides what must parse.
    (An earlier version counted rows with the same pattern it parsed with, so the
    two could never disagree and a malformed row vanished silently.)
    """
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("|") and "artifact" in line.lower() and line.lower().count("|") >= 5:
            inside = True
            continue
        if inside and not line.startswith("|"):
            break
        if inside:
            out.append(line)
    return out


def parse_rows(text):
    """Pull the claim table's data rows: | id | claim | artifact | key | value |."""
    rows = []
    carry = None
    region = table_region(text)   # the region decides what must parse; see table_region
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        # ids may carry a letter suffix (10b, 23c); a numeric-only pattern would
        # silently drop those rows, and a row nobody reads is not a row that passed.
        if not re.fullmatch(r"\d+[a-z]?", cells[0]):
            continue
        # "same" means the artifact named by the previous row — a table shorthand
        artcell = cells[2]
        if artcell.strip().lower().startswith("same"):
            artcell = carry or artcell
        else:
            carry = artcell
        rows.append({"id": cells[0], "claim": cells[1], "artifact": artcell,
                     "key": cells[3], "value": cells[4]})
    return rows


NUM = re.compile(r"\d+(?:[.,]\d+)*")


def check_manuscript(rows):
    """Every quantity the claim table asserts must be STATABLE in the manuscript that ships.

    A literal string match is the wrong binding here: the table's value column is written for a
    machine (`0 / 313`, `{git: 82}`) and the prose states the same quantity in sentences. What is
    asserted is that each numeric token of the table's value appears in the manuscript as a
    standalone number, so a manuscript that silently drops or alters a quantity fails, while one
    that states it in prose passes. The strong half of the binding -- that the value re-derives from
    the artifact -- is the row loop above; this half closes the door on prose drift.
    """
    import io as _io
    import os as _os
    text, used = None, None
    for cand in (MS,) + MS_FALLBACKS:
        if _os.path.exists(cand):
            text, used = _io.open(cand, encoding="utf-8").read(), cand
            break
    if text is None:
        # a gate that reads nothing must FAIL: "no manuscript found" is not "no drift"
        print("FAIL cannot read %s (or %s) -- the manuscript binding verified nothing"
              % (MS, ", ".join(MS_FALLBACKS)))
        return 0, 1, None
    body = text.replace("**", "").replace("`", "").replace(",", "")
    have = set(re.findall(r"(?<![0-9.])\d+(?:\.\d+)?(?![0-9])", body))
    ok_rows, missing, nonnumeric = 0, [], 0
    for r in rows:
        if r["id"] in {str(k) for k in NOT_CHECKED}:
            continue
        toks = NUM.findall(norm(r["value"]).replace(",", ""))
        if not toks:
            nonnumeric += 1
            continue
        absent = [t for t in toks if t not in have and t.rstrip(".0") not in have]
        if absent:
            missing.append((r["id"], r["claim"][:44], absent))
        else:
            ok_rows += 1
    for i, c, absent in missing:
        print("FAIL         [%2s] the manuscript never states %s  (%s)" % (i, absent, c))
    checked = len(rows) - len(NOT_CHECKED) - nonnumeric
    print("\nMANUSCRIPT: %d of %d table row(s) statable in %s, %d unstatable, %d non-numeric value(s)"
          % (ok_rows, checked, used, len(missing), nonnumeric))
    return ok_rows, len(missing), used


def main():
    skel = sys.argv[1] if len(sys.argv) > 1 else SKEL
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    text = open(skel).read()
    rows = parse_rows(text)
    if not rows:
        print("FAIL: no claim rows found in %s" % skel)
        return 1

    # every row inside the claim table must parse: a row nobody reads is not a pass
    region = table_region(text)
    data = [l for l in region
            if not re.fullmatch(r"\|\s*:?-{3,}.*", l)]        # drop the |---| separator
    ids = {r["id"] for r in rows}
    dropped = []
    for line in data:
        first = line.strip().strip("|").split("|")[0].strip()
        if first in ("#", ""):
            continue
        if first not in ids:
            dropped.append(first or "(empty id)")
    if dropped:
        print("FAIL: %d claim-table row(s) did not parse: %s" % (len(dropped), dropped))
        return 1
    print("claim table: %d data rows, all parsed" % len(data))

    env = {p: json.load(open(p)) for p in ARTIFACTS.values()}
    ok = fail = notchecked = 0
    for r in rows:
        if r["id"] in {str(k) for k in NOT_CHECKED}:
            notchecked += 1
            print("NOT CHECKED  [%2s] %s" % (r["id"], NOT_CHECKED[int(r["id"])]))
            continue
        art = art_of(r["artifact"])
        if art is None:
            print("FAIL         [%2s] no artifact named in %r" % (r["id"], r["artifact"]))
            fail += 1
            continue
        # a row may name two keys with ' / ' and print two values with ' / '
        keys = [k.replace("`", "").strip() for k in r["key"].split(" / ")]
        keys = [k for k in keys if k]
        printed = [norm(x) for x in r["value"].split(" / ")]
        if len(keys) != len(printed):
            # tolerate a single key whose value legitimately contains ' / '
            keys, printed = [r["key"]], [norm(r["value"])]
        good = True
        for k, pv in zip(keys, printed):
            got, err = resolve(art, k, ARTIFACTS)
            if err:
                print("FAIL         [%2s] %s: %s" % (r["id"], k, err))
                good = False
                continue
            if norm(got) != pv:
                print("FAIL         [%2s] %s: table says %r, artifact says %r"
                      % (r["id"], k, pv, got))
                good = False
            elif verbose:
                print("ok           [%2s] %s = %s" % (r["id"], k, got))
        if good:
            ok += 1
        else:
            fail += 1

    present, ms_missing, used = check_manuscript(rows)
    if ms_missing:
        fail += ms_missing

    print("\nCLAIMS: %d ok, %d FAIL, %d NOT CHECKED (of %d rows)"
          % (ok, fail, notchecked, len(rows)))
    if fail:
        print("VERDICT: FAIL")
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
