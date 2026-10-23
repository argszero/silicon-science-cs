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
               28: "printed by plant_coverage.py",
               # `23b`/`23c` print a build-type and a builder URL: an identifier has no quantity and
               # therefore no statement site. Their COUNTS are rows 10/23 (`(len)`), which are bound.
               # Named here so the exception is printed rather than silently passed by a digit.
               "23b": "value is a registry identifier (build-type URL), not a quantity; its count is row 10",
               "23c": "value is a registry identifier (builder URL), not a quantity; its count is row 23"}


# `NOT_CHECKED` keyed as the table writes it: rows may carry a letter suffix (`23b`), and an
# integer-only lookup silently made the printed exception a crash instead of a report.
NOT_CHECKED_BY_ID = {str(k): v for k, v in NOT_CHECKED.items()}


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


# --- statement-site binding: the repair required by issue #145's R2 --------------------------------
#
# The published version of this file built ONE set of every numeric token in the manuscript (88
# distinct tokens over 40 116 characters) and asked only that each table value's tokens appear
# SOMEWHERE in it. The editorial decision measured the consequence: `giving **184** package
# releases` changed to `**999**` at its statement site left `C5 ok` and `VERDICT: PASS`, because
# `184` also stood at two other lines of the same file. A set of tokens is not a binding, and a
# document-wide presence test cannot tell a statement from an echo.
#
# So the manuscript now DECLARES where each quantity is stated:
#
#     ... giving **184** package releases <!-- c: npm.summary.units -->.
#
# and this gate verifies, for every checked table row, that
#   * the row's key has at least one such site (an unstated quantity is a defect, not a pass);
#   * the SITE -- the sentence containing the annotation, with the annotation cut out -- states the
#     artifact's value, read with number words (`Twelve` -> 12) and boundary-anchored, so `2` is not
#     found inside `42` and `9` is not found inside `1961`.
# An annotation is not evidence for itself: the tag's own text is removed before the match, because
# a key written into the tag could otherwise satisfy itself (issue #141's correction round).
SITE = re.compile(r"<!--\s*c:\s*(.+?)-->", re.S)
C_DECL = re.compile(r"^(npm|pypi|oci)\.(.+)$")

_NUMWORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
             "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
             "nineteen": 19, "twenty": 20}
_WORD = re.compile(r"\b(%s)\b" % "|".join(_NUMWORDS), re.I)


def read_numbers(text):
    """The numbers a reader of `text` reads: digits and number words alike."""
    t = _WORD.sub(lambda m: str(_NUMWORDS[m.group(1).lower()]), text)
    t = t.replace("**", "").replace("*", "").replace("`", "")
    return set(re.findall(r"(?<![0-9A-Za-z.])(\d+(?:\.\d+)?)(?![0-9])", t))


def sentence_of(text, offset):
    """The CLAUSE containing a character offset -- the statement site, not the whole document.

    A sentence is not tight enough, and the plant that showed it is the one the editor's own probe
    predicts one step further: "Coverage of that 313 is **0 by the provenance statement** ... and
    **313 by a sibling SPDX**" states 313 twice in one sentence, so drifting one of them to 512 left
    the other standing and the site still read 313. The unit is therefore the clause: a value must be
    stated NEXT TO the annotation that owns it, not merely somewhere in the same sentence. Measured
    cost of this tightening on the repaired manuscript is reported by the gate itself -- the number of
    rows that still bind.
    """
    lo = 0
    for sep in (". ", ".\n", "\n\n", "; ", " — ", " – ", ", "):
        j = text.rfind(sep, 0, offset)
        if j >= 0:
            lo = max(lo, j + len(sep))
    m = re.search(r"[;.,](?=\s|\n|$)|\s—\s", text[offset:])
    hi = offset + (m.start() if m else 0)
    return text[lo:hi]


def sites(text):
    """Every declared statement site: (art, keyexpr, the text it annotates, decl).

    Consecutive annotations separated only by whitespace form ONE run and share one site -- a run is
    how a sentence states several quantities at a single place ("... **52** ... **0 of 249**
    <!-- c: a --> <!-- c: b --> <!-- c: c -->"). Treating each tag as its own boundary would leave the
    second and third with an EMPTY site, and treating only punctuation as a boundary would let one
    tag's clause swallow the next tag's number, which is how drifting "**313** by a sibling SPDX" to
    512 stayed green. Both shapes are in the manuscript, so the unit is the run: text from the
    previous separator OR the previous run's end, up to this run's first tag.
    """
    marks = [(m.start(), m.end(), m.group(1).strip()) for m in SITE.finditer(text)]
    runs, cur = [], []
    for st, en, decl in marks:
        if cur and not text[cur[-1][1]:st].strip():
            cur.append((st, en, decl))
        else:
            if cur:
                runs.append(cur)
            cur = [(st, en, decl)]
    if cur:
        runs.append(cur)
    out, prev_end = [], 0
    for run in runs:
        run_start = run[0][0]
        lo = prev_end
        for sep in (". ", ".\n", "\n\n", "; ", " — ", " – ", ", "):
            j = text.rfind(sep, 0, run_start)
            if j >= 0:
                lo = max(lo, j + len(sep))
        site = SITE.sub(" ", text[lo:run_start])      # the annotation is not evidence for itself
        for st, en, decl in run:
            dm = C_DECL.match(decl)
            out.append((dm.group(1), dm.group(2).strip(), site, decl) if dm
                       else (None, None, site, decl))
        prev_end = run[-1][1]
    return out


def _resolve_in(env, art, keyexpr):
    """resolve() against an already-loaded artifact, for the plants."""
    m = re.match(r"rows\[\]\.(.*?)\s*\(sum over OK\)", keyexpr)
    data = env[art]
    if m:
        path = m.group(1).split(".")
        total = 0
        for row in data["rows"]:
            if row.get("status") != "OK":
                continue
            cur = row
            for q in path:
                cur = cur[q]
            total += cur
        return str(total), None
    want_len = "(len)" in keyexpr
    key = keyexpr.replace("(len)", "").replace("`", "").strip()
    cur = data
    for q in key.split("."):
        if not isinstance(cur, dict) or q not in cur:
            return None, "key %r missing in %s" % (q, art)
        cur = cur[q]
    if want_len:
        if not isinstance(cur, (list, dict)):
            return None, "%s is not a list/dict, cannot take len" % key
        return str(len(cur)), None
    if isinstance(cur, dict):
        return "{" + ", ".join("%s: %s" % (x, cur[x]) for x in sorted(cur)) + "}", None
    if isinstance(cur, list):
        return "[" + ", ".join(str(x) for x in cur) + "]", None
    return str(cur), None


def check_manuscript(rows, given=None):
    """Bind every table value to the SITE where the manuscript states it."""
    import io as _io
    import os as _os
    text, used = given, (MS if given is not None else None)
    if text is not None:
        return _bind(rows, text, used,
                     {k: json.load(open(v)) for k, v in ARTIFACTS.items()})
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

    return _bind(rows, text, used, {k: json.load(open(v)) for k, v in ARTIFACTS.items()})


def _bind(rows, text, used, env):
    """The site binding itself: pure in (rows, text, artifacts)."""
    declared = sites(text)
    by_decl = {}
    for art, keyexpr, site, decl in declared:
        by_decl.setdefault(decl, []).append(site)

    bad, ok_rows, nonnumeric = [], 0, 0
    for r in rows:
        if r["id"] in {str(k) for k in NOT_CHECKED}:
            continue
        toks = NUM.findall(norm(r["value"]).replace(",", ""))
        if not toks:
            nonnumeric += 1
            continue
        art = art_of(r["artifact"])
        keys = [k.replace("`", "").strip() for k in r["key"].split(" / ")]
        problems = []
        for k in [k for k in keys if k]:
            decl = "%s.%s" % (art, k)
            where = by_decl.get(decl)
            if not where:
                problems.append("%s: no statement site -- the manuscript never says where it states "
                                "this quantity" % decl)
                continue
            got, err = _resolve_in(env, art, k)
            if err:
                problems.append("%s: %s" % (decl, err))
                continue
            need = read_numbers(norm(got))
            if not need:
                continue                       # a non-numeric value has no site to bind (see NOT_CHECKED)
            for site in where:
                have = read_numbers(site)
                if not need <= have:
                    problems.append("%s: the site states %s, the artifact says %s  [%s]"
                                    % (decl, sorted(have) or "no number",
                                       sorted(need), site.strip()[:90]))
        if problems:
            bad.append((r["id"], r["claim"][:44], problems))
        else:
            ok_rows += 1
    for i, c, problems in bad:
        for pr in problems:
            print("FAIL         [%2s] %s  (%s)" % (i, pr, c))
    checked = len(rows) - len(NOT_CHECKED) - nonnumeric
    print("\nMANUSCRIPT: %d of %d table row(s) bound to a statement site in %s, %d unbound, "
          "%d non-numeric value(s), %d declared site(s)"
          % (ok_rows, checked, used, len(bad), nonnumeric, len(declared)))
    return ok_rows, len(bad), used


def selftest():
    """The receipt R2 owes: each plant IS the defect, and each must go RED.

    The editorial decision measured the published gate passing on
    `giving **184** package releases` -> `**999**` at its statement site, because 184 stood at two
    other lines of the same file. These fixtures are that defect and its neighbours; the control is
    the repaired manuscript, so a guard that refuses everything is not mistaken for a guard.
    """
    import io as _io
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-64s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    text = _io.open(MS, encoding="utf-8").read()
    rows = parse_rows(_io.open(SKEL, encoding="utf-8").read())
    env = {k: json.load(open(v)) for k, v in ARTIFACTS.items()}

    def unbound(t):
        import contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            _ok, bad, _used = _bind(rows, t, MS, env)
        return bad, buf.getvalue()

    n0, _ = unbound(text)
    holds("CONTROL: the shipped manuscript binds every checked row (0 unbound)", n0 == 0)

    # 1. the editorial probe, exactly
    old = "giving **184** package releases <!-- c: npm.summary.units -->"
    if old in text:
        drift = text.replace(old, "giving **999** package releases <!-- c: npm.summary.units -->")
        n, out = unbound(drift)
        holds("a value drifting AT ITS STATEMENT SITE fires (184 -> 999)",
              n == 1 and "npm.summary.units" in out)
        holds("...while the drifted number still stands elsewhere in the file, as it did when the "
              "published gate passed", "184" in drift.replace(old, ""))
    else:
        holds("a value drifting AT ITS STATEMENT SITE fires (184 -> 999)", False)

    # 2. a second statistic of the same sentence drifting, its twin standing
    old2 = "**313 by a sibling SPDX statement in"
    if old2 in text:
        n, out = unbound(text.replace(old2, "**512 by a sibling SPDX statement in"))
        holds("a sibling occurrence drifting fires (313 -> 512, 313 stands in the same sentence)",
              n == 1 and "declared_covered_by_spdx" in out)
    else:
        holds("a sibling occurrence drifting fires (313 -> 512, 313 stands in the same sentence)", False)

    # 3. an unstated quantity: the annotation removed
    old3 = " <!-- c: npm.summary.not_run -->"
    if old3 in text:
        n, out = unbound(text.replace(old3, "", 1))
        holds("a quantity with no statement site fires (annotation removed)",
              n == 1 and "no statement site" in out)
    else:
        holds("a quantity with no statement site fires (annotation removed)", False)

    # 4. the site unit: a value in the WRONG clause must not satisfy the annotation
    old4 = "giving **184** package releases <!-- c: npm.summary.units -->"
    if old4 in text:
        moved = text.replace(old4, "giving 184 package releases, and 184 more in an appendix "
                                   "<!-- c: npm.summary.units -->")
        n, _out = unbound(moved)
        holds("...and the clause unit keeps this binding valid (184 beside its tag)", n == 0)
    print("CLAIMS-SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
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

    # keyed by the SHORT NAME (`npm`), the same key `art_of()` returns and `_resolve_in` expects:
    # keying by file path made the two resolvers disagree and the row loop raise instead of report
    env = {k: json.load(open(v)) for k, v in ARTIFACTS.items()}
    ok = fail = notchecked = 0
    for r in rows:
        if r["id"] in {str(k) for k in NOT_CHECKED}:
            notchecked += 1
            print("NOT CHECKED  [%2s] %s" % (r["id"], NOT_CHECKED_BY_ID[r["id"]]))
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
            got, err = _resolve_in(env, art, k)
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
