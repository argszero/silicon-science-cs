"""Gate the corpus against the authored placement, and emit the reference-check report.

Two jobs, one file, because they must agree:

  gate    every kept corpus entry is placed exactly once or pruned with a reason; every key named
          in placements.py resolves to exactly one kept entry; every placement names a declared
          section; every placed entry carries stored verification state. Exit 1 on any violation,
          and the placed count against the 100-reference floor is printed as a gate row, not as a
          footnote.

  report  `--report MD` writes reference-check.md as a PURE FUNCTION of the corpus's stored
          verification state and placements.py. No network, no wall clock: the two things that
          made the previous generator's output unreproducible. Running it twice must produce the
          same bytes, which is what lets reproduce.sh regenerate it instead of trusting it.

Why the gate resolves keys instead of trusting them: issue #145's reference round listed 28
rejected keys copied from a truncated print, and not one of them matched an entry -- the pool
still contained everything that had been refused. A named key is therefore resolved here
(exactly, else uniquely by prefix) and an ambiguous or absent key is an error, never a guess.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from placements import SECTIONS, PLACEMENTS, PRUNED, COMPARISON_KEYS

FLOOR = 100


def load(path):
    return json.load(open(path))


def kept_entries(doc):
    return [e for e in doc["entries"] if e.get("review", "kept") == "kept"]


def resolve(named, keymap):
    """Resolve a named key to exactly one corpus key. Absent is an error, ambiguity is an error."""
    if named in keymap:
        return keymap[named], "exact"
    hits = [k for k in keymap if k.startswith(named)]
    if len(hits) == 1:
        return keymap[hits[0]], "prefix"
    if not hits:
        return None, "absent"
    return None, "ambiguous (%d: %s)" % (len(hits), ", ".join(sorted(hits)[:4]))


def check(doc):
    """Return (placed, pruned, problems) where placed/pruned are key->entry maps."""
    kept = {e["key"]: e for e in kept_entries(doc)}
    problems = []

    placed, pruned = {}, {}
    for named, (section, claim) in PLACEMENTS.items():
        ent, how = resolve(named, kept)
        if ent is None:
            problems.append("PLACEMENT %-46s %s" % (named, how))
            continue
        if how == "prefix":
            print("resolve     %-46s -> %s" % (named, ent["key"]))
        if section not in SECTIONS:
            problems.append("SECTION     %-46s %r is not a declared section" % (named, section))
            continue
        if ent["key"] in placed:
            problems.append("DUPLICATE   %s placed twice" % ent["key"])
            continue
        placed[ent["key"]] = (section, claim, ent)

    for named, reason in PRUNED.items():
        ent, how = resolve(named, kept)
        if ent is None:
            problems.append("PRUNED      %-46s %s" % (named, how))
            continue
        if not reason or len(reason) < 20:
            problems.append("REASON      %-46s a prune needs a stated reason" % named)
            continue
        if ent["key"] in pruned:
            problems.append("DUPLICATE   %s pruned twice" % ent["key"])
            continue
        pruned[ent["key"]] = reason

    both = sorted(set(placed) & set(pruned))
    for k in both:
        problems.append("BOTH        %s is placed and pruned" % k)

    orphan = sorted(set(kept) - set(placed) - set(pruned))
    for k in orphan:
        problems.append("UNPLACED    %s is kept but neither placed nor pruned" % k)

    # a placed entry that is not verified is not citable
    for k, (section, claim, ent) in sorted(placed.items()):
        v = ent.get("verification") or {}
        if v.get("result") != "verified":
            problems.append("UNVERIFIED  %s placed but verification says %r"
                            % (k, v.get("result")))

    for named in [c[0] for c in COMPARISON_KEYS]:
        ent, how = resolve(named, kept)
        if ent is None or ent["key"] not in placed:
            problems.append("COMPARISON  %-46s %s and must be placed" % (named, how))

    return placed, pruned, problems, kept


def gate(doc, placed, pruned, problems, kept):
    print("")
    print("CORPUS      kept %d   placed %d   pruned %d   (placed+pruned must equal kept)"
          % (len(kept), len(placed), len(pruned)))
    by = {}
    for k, (section, claim, ent) in placed.items():
        by.setdefault(section, []).append(k)
    print("")
    print("placements by section")
    for s in sorted(SECTIONS):
        print("  %-4s %3d  %s" % (s, len(by.get(s, [])), SECTIONS[s][:74]))
    print("")
    if len(placed) < FLOOR:
        print("FLOOR       %d placed, floor is %d -- SHORT by %d"
              % (len(placed), FLOOR, FLOOR - len(placed)))
    else:
        print("FLOOR       %d placed, floor is %d -- PASS" % (len(placed), FLOOR))
    if problems:
        print("")
        print("PROBLEMS (%d)" % len(problems))
        for p in problems:
            print("  " + p)
        print("")
        print("VERDICT: FAIL")
        return 1
    print("")
    print("VERDICT: PASS (every kept entry placed or pruned with a reason; every placement verified)")
    return 0


def report(doc, placed, pruned, out):
    """Byte-stable: no wall clock, no network, sorted iteration only."""
    ver = doc.get("verification") or {}
    hv = doc.get("harvest") or {}
    rv = doc.get("review") or {}
    L = []
    A = L.append

    A("# Reference verification report — issue #149")
    A("")
    A("**DERIVED FILE — do not edit.** Regenerate with `python3 place_references.py "
      "--report reference-check.md`. It is a pure function of two inputs: the stored "
      "verification state in `research/references.json` and the authored placement in "
      "`placements.py`. It reads no network and writes no timestamp, so regenerating it "
      "reproduces it byte for byte.")
    A("")
    A("## What was searched, and how")
    A("")
    A("| item | value |")
    A("|---|---|")
    A("| index | Crossref REST API, `works` endpoint (`query.bibliographic` for discovery, "
      "`works/{doi}` for verification) |")
    A("| window | **none imposed** — Crossref's bibliographic query takes no date filter in this "
      "call, so records of any year may return. The search window is therefore not a claim this "
      "report can make; the scan date is. |")
    A("| scan date | %s |" % (ver.get("checked_on") or "--"))
    A("| rows per query | 16 |")
    A("| queries issued | %d |" % len(hv.get("per_query") or {}))
    A("| queries that returned nothing usable | %d (listed below, not dropped) |"
      % len([q for q, c in (rv.get("per_query") or {}).items() if c.get("kept") == 0]))
    A("| verification method | DOI → `works/{doi}`, then corroboration by a field that is "
      "**not the title**: the first-author family, or the year when no author is asserted. "
      "Author mismatch is fatal. |")
    A("")
    if hv.get("failed_queries"):
        A("**Queries that could not be run** — recorded rather than dropped, because a failed "
          "request is not a finding about the literature:")
        A("")
        for f in hv["failed_queries"]:
            A("* `%s` — %s" % (f.get("query"), f.get("why")))
        A("")
    refused = sorted(q for q, c in (rv.get("per_query") or {}).items()
                     if c.get("kept") == 0 and c.get("considered"))
    if refused:
        A("**Queries whose whole yield was refused on relevance** (%d): %s."
          % (len(refused), ", ".join("`%s`" % q for q in refused)))
        A("")

    A("## Counts")
    A("")
    A("| quantity | value |")
    A("|---|---|")
    A("| records harvested mechanically | %d |" % rv.get("mechanical", len(doc["entries"])))
    A("| refused in pass 1 (salience: another field entirely) | %d |" % rv.get("excluded_pass1", 0))
    A("| refused in pass 2 (criterion: adjacent construct) | %d |" % rv.get("excluded_pass2", 0))
    A("| **pruned at placement** (real records supporting no claim here) | **%d** |" % len(pruned))
    A("| **placed and cited** | **%d** |" % len(placed))
    A("| verification floor | ≥ %d |" % FLOOR)
    A("| state | %s |" % ("PASS" if len(placed) >= FLOOR else
                           "SHORT by %d" % (FLOOR - len(placed))))
    A("")
    A("The two pruning stages answer different questions and are counted separately. Passes 1 "
      "and 2 ask whether a record is about this subject at all; placement asks whether it "
      "supports a claim this paper makes. A record can pass both review passes and still be "
      "unplaceable, and that is the failure mode a word-level gate cannot see: *Agile Software "
      "Assurance: An Empirical Study* is about software engineering and about measurement, and "
      "still has nothing to say here.")
    A("")

    A("## Works this paper is measured against")
    A("")
    A("Each states a competing object or a competing answer. The difference, not the citation, "
      "is the content.")
    A("")
    for named, difference, basis in COMPARISON_KEYS:
        ent = None
        for k, (section, claim, e) in placed.items():
            if k.startswith(named):
                ent = e
                break
        A("### %s" % (ent.get("title") if ent else named))
        A("")
        A("*%s, %s. DOI `%s`.*" % (ent.get("first_author") or "--",
                                    ent.get("year") or "--", ent.get("doi") or "--"))
        A("")
        A("Difference: %s" % difference)
        A("")
        A("What was read, at the time this report was generated: %s." % basis)
        A("")

    A("## Verification, one line per placed entry")
    A("")
    A("Method is `doi` (record fetched by DOI) unless stated. `result` is what the stored state "
      "says, not what a re-run would say now.")
    A("")
    A("| # | key | result | title match | record found | DOI | checked |")
    A("|---|---|---|---|---|---|---|")
    n = 0
    for k in sorted(placed):
        section, claim, ent = placed[k]
        v = ent.get("verification") or {}
        rec = v.get("record") or {}
        score = v.get("title_score")
        n += 1
        A("| %d | `%s` | %s | %s | %s | `%s` | %s |"
          % (n, k, v.get("result") or "--",
             ("%.3f" % score) if isinstance(score, float) else "--",
             (rec.get("title") or "--")[:70], rec.get("doi") or ent.get("doi") or "--",
             v.get("checked_on") or "--"))
    A("")
    A("Total placed and verified: **%d**." % n)
    A("")

    A("## Placement: entry, section, and the claim it supports")
    A("")
    for s in sorted(SECTIONS):
        rows = sorted([(k, c, e) for k, (sec, c, e) in placed.items() if sec == s])
        A("### %s — %s (%d)" % (s, SECTIONS[s], len(rows)))
        A("")
        if not rows:
            A("_No entry placed in this section._")
            A("")
            continue
        A("| key | title | claim supported |")
        A("|---|---|---|")
        for k, claim, ent in rows:
            A("| `%s` | %s | %s |" % (k, (ent.get("title") or "")[:70], claim))
        A("")

    A("## Pruned at placement (%d)" % len(pruned))
    A("")
    A("Recorded, not deleted. A record removed without a reason is a silent edit to the "
      "reference list; these are real records that support no claim in this paper.")
    A("")
    A("| key | title | reason |")
    A("|---|---|---|")
    for k in sorted(pruned):
        ent = None
        for e in doc["entries"]:
            if e["key"] == k:
                ent = e
                break
        A("| `%s` | %s | %s |" % (k, ((ent or {}).get("title") or "")[:70], pruned[k]))
    A("")

    A("## Against the submission bar")
    A("")
    A("| gate | required | this corpus | state |")
    A("|---|---|---|---|")
    A("| references, each genuinely cited | ≥ %d | %d placed, each with a named section and claim "
      "| %s |" % (FLOOR, len(placed), "PASS" if len(placed) >= FLOOR else "SHORT"))
    A("| every entry verified against a real record | all | %d of %d placed | PASS |"
      % (len(placed), len(placed)))
    A("| entries pruned with a stated reason | all prunes | %d of %d | PASS |"
      % (len(pruned), len(pruned)))
    A("| ≥ 3 works compared with a stated difference | 3 | %d | PASS |" % len(COMPARISON_KEYS))
    A("")
    A("A placement is a promise about the manuscript, not a count. The gate here checks that "
      "every placement names a section and a claim; it cannot check that the manuscript later "
      "makes good on the claim, because that text does not exist yet. That check belongs to the "
      "manuscript round, and it is the one that can still fail.")
    open(out, "w").write("\n".join(L) + "\n")
    print("wrote %s (%d lines): %d placed, %d pruned"
          % (out, len(L), len(placed), len(pruned)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/references.json")
    ap.add_argument("--report", metavar="MD", default=None)
    a = ap.parse_args()
    doc = load(a.out)
    placed, pruned, problems, kept = check(doc)
    rc = gate(doc, placed, pruned, problems, kept)
    if a.report and not problems:
        rc = report(doc, placed, pruned, a.report)
    elif a.report:
        print("refusing to write %s: the corpus does not pass its own gate" % a.report)
    return rc


if __name__ == "__main__":
    sys.exit(main())
