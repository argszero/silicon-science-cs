#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_citations.py -- bind the manuscript's citations to the placed corpus, and emit the list.

Three judgements, each of which has failed before in this journal:

  C1  every key a claim places resolves to a record whose verification status is `verified*`
      (a citation to a record that did not corroborate is a citation to something we never saw);
  C2  every claim the manuscript cites exists, and every claim that exists is cited -- a claim placed
      but never cited is padding counted toward the reference floor;
  C3  the distinct cited records meet the floor.

Plus C4, which is what makes this file worth having: the manuscript cites a claim by ID, never by
key. A citation therefore cannot be added without a claim that owns it, and the reference list cannot
drift from the corpus because it is generated from the corpus.

`--render` writes the manuscript with its `{{c:id}}` markers replaced by numbered clusters and
`{{refs}}` replaced by the generated list. `--list` writes the list alone. Neither invents a number:
the numbering is assigned from the placed corpus in key order, so it is stable across runs.

Usage:
  ./gate_citations.py                 # checks; exit 0 green, 1 failed, 3 nothing to check
  ./gate_citations.py --render out.md # also write the rendered manuscript
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from placements import CLAIMS, PRUNED, FLOOR, placed_keys  # noqa: E402

REFS = os.path.join(HERE, "refs", "references.json")
MS = os.path.join(HERE, "manuscript.src.md")   # authored; manuscript.md is rendered from it

MARK = re.compile(r"\{\{c:([a-z0-9-]+)\}\}")
REFS_MARK = "{{refs}}"
GRID_MARK = "{{grid}}"
FINDINGS = os.path.join(HERE, "nines_findings.json")


def render_grid():
    """The reading table, rendered from the artefact the instrument writes.

    A table typed into a manuscript is a second copy of a derived object, and the copy does not have a
    producer: it agrees with the artefact on the day it is typed and never afterwards. This renders
    from `nines_findings.json` so the manuscript's table cannot disagree with the run that made it.
    """
    if not os.path.exists(FINDINGS):
        return None
    d = json.load(open(FINDINGS, encoding="utf-8"))
    head = ("| per-device p | r | quoted | worst identified | nines quoted | nines at worst | span "
            "(decades) | set reaches total loss |")
    rule = "|---|---|---|---|---|---|---|---|"
    rows = [head, rule]
    for c in d["grid"]:
        rows.append("| %s | %d | %.2e | %.2e | %.1f | %.1f | %.1f | %s |"
                    % (c["p"], c["r"], c["independent"], c["set_hi"], c["quoted_nines"],
                       c["set_hi_nines"], c["span_nines"], "yes" if c["contains_zero"] else "no"))
    return "\n".join(rows)


def load_corpus():
    if not os.path.exists(REFS):
        return None
    return json.load(open(REFS, encoding="utf-8"))


def write_report(path, corpus, nums):
    """The citation report, derived from the corpus and the authored placement.

    DERIVED FILE. It reads the stored verification state and the placement, and writes no timestamp
    of its own — the scan date comes from the corpus, where the run that did the scanning recorded it.
    Regenerating it therefore reproduces it byte for byte, and a change in it is always a change of
    input rather than of the day.
    """
    recs = corpus["records"]
    by_group = {}
    for rec in recs:
        by_group.setdefault(rec.get("group", "?"), []).append(rec)
    refusals = corpus.get("refusals") or []
    tally = {}
    for r in refusals:
        tally[r.get("reason", "?")] = tally.get(r.get("reason", "?"), 0) + 1
    out = []
    out.append("# Reference verification report — issue #162\n")
    out.append("**DERIVED FILE — do not edit.** Regenerate with `./gate_citations.py --report "
               "reference-check.md`. It is a pure function of the stored verification state in "
               "`refs/references.json` and the authored placement in `placements.py`; it reads no "
               "network and writes no timestamp of its own, so regenerating it reproduces it byte for "
               "byte.\n")
    out.append("## What was searched, and how\n")
    out.append("| item | value |")
    out.append("|---|---|")
    out.append("| index | Crossref REST API, `works` endpoint (`query.bibliographic` for discovery, "
               "`works/{doi}` for verification) |")
    out.append("| window | **none imposed** — the bibliographic query takes no date filter in this "
               "call, so the scan is a scan and the window is not a claim this report can make; the "
               "scan date is |")
    out.append("| scan date | %s |" % corpus.get("scan_date", "unknown"))
    out.append("| rows per query | %s |" % corpus.get("rows_per_query", "?"))
    out.append("| queries issued | %d |" % len(corpus.get("queries") or []))
    out.append("| verification method | DOI → `works/{doi}`; the stored title must match the returned "
               "title **and** an independent field must corroborate it: the first-author family, or "
               "the year when no author is asserted. Author mismatch is fatal; a year mismatch is "
               "recorded as an edition (`verified-edition`) |")
    out.append("| arXiv | **NOT RUN** — the arXiv API returned HTTP 429 on every probe this round. "
               "That is a rate limit, not an absence of records, so this report does not claim any "
               "work is missing from arXiv |")
    out.append("")
    out.append("## Counts\n")
    c = corpus["counts"]
    out.append("| quantity | value |")
    out.append("|---|---|")
    out.append("| records harvested mechanically | %d |" % c.get("harvested", len(recs)))
    out.append("| candidate records refused at harvest | %d |" % c.get("refused", len(refusals)))
    for reason in sorted(tally):
        out.append("| — refused: %s | %d |" % (reason, tally[reason]))
    out.append("| records verified against their DOI record | %d |" % c.get("verified", 0))
    out.append("| verified in this run / carried from an earlier run | %d / %d |"
               % (c.get("verified", 0) - c.get("carried", 0), c.get("carried", 0)))
    out.append("| records not verified (excluded, never cited) | %d |" % c.get("not_verified", 0))
    out.append("| **distinct records cited in the manuscript** | **%d** (floor %d) |"
               % (len(nums), FLOOR))
    out.append("| records verified but not cited | %d |" % (len(recs) - len(nums)))
    out.append("| — of those, carrying a named reason in `placements.py` | %d |"
               % len([r for r in recs if r["key"] not in nums and r["key"] in PRUNED]))
    out.append("")
    out.append("A verified record is not a citation. The floor is met in records the manuscript "
               "actually cites, each through a claim that owns it (`{{c:<id>}}`), so an entry cannot "
               "be padding: `gate_citations.py` fails if a claim is placed and never cited, and fails "
               "if a citation exists with no claim behind it.\n")
    out.append("## Refusals at harvest, by reason\n")
    out.append("| reason | n | what it means |")
    out.append("|---|---|---|")
    meaning = {
        "type": "not an academic item (figure caption, front matter, component, peer review)",
        "no-year": "the record carries no date, so nothing can corroborate the year",
        "no-identifier": "no DOI or no title, so the record cannot be re-fetched",
        "terms": "the returned title does not mention the group's own terms: the query measured the "
                 "index's recall, not the literature",
        "adjacent-construct": "shares a word with this paper and names a different object",
        "duplicate-title": "the same work under another DOI; the corpus admits one key per work",
        "NOT RUN": "the query could not be issued or answered this run",
    }
    for reason in sorted(tally):
        out.append("| %s | %d | %s |" % (reason, tally[reason], meaning.get(reason, "")))
    out.append("")
    out.append("## What the corpus is placed against\n")
    out.append("| claim id | section | records | the claim it supports |")
    out.append("|---|---|---|---|")
    for cl in CLAIMS:
        out.append("| `%s` | §%s | %d | %s |"
                   % (cl["id"], cl["section"], len(cl["keys"]), cl["claim"].replace("|", "/")))
    out.append("")
    out.append("## Records excluded by name, with the reason\n")
    out.append("These cleared the screen and are real records; they are not cited because they name "
               "an adjacent construct. The exclusion is a decision with a reason, not a silent "
               "drop.\n")
    out.append("| key | reason |")
    out.append("|---|---|")
    for k in sorted(PRUNED):
        out.append("| `%s` | %s |" % (k, PRUNED[k]))
    out.append("")
    out.append("## A prior-art line this report does not cite, and why\n")
    out.append("The copyset placement discipline — constrain which replicas may fail together, then "
               "compute the loss rate — originates in a USENIX ATC paper that carries **no DOI** and "
               "therefore has no Crossref record. The arXiv probe that could have corroborated it "
               "returned HTTP 429 (NOT RUN) on every attempt this round. It is consequently **not "
               "cited**: an unverifiable citation is not admissible here, and a rate limit does not "
               "establish that the record does not exist. What the manuscript does cite is the "
               "copyset placement literature that *is* indexed (see the `placement-under-correlation` "
               "claim), which makes the same design argument on the record.\n")
    return "\n".join(out) + "\n"


NUM = re.compile(r"\b\d+(?:\.\d+)?(?:e-?\d+)?\b")


def artefact_numbers():
    """Every number the artefact holds, in the forms the manuscript may quote.

    The gate needs both formats because the artefact and the table print differently: probabilities as
    `%.2e`, nines and spans as `%.1f`. A number quoted in the manuscript has to be one of these; the
    point is not to police style but to make sure that a number typed into prose has a run behind it.
    """
    if not os.path.exists(FINDINGS):
        return None
    d = json.load(open(FINDINGS, encoding="utf-8"))
    held = set()

    def add(v):
        if isinstance(v, float) or isinstance(v, int):
            held.add("%.1f" % v)
            held.add("%.2e" % v)
            held.add("%.3e" % v)
            held.add("%.0e" % v)
            held.add("%.1e" % v)
            held.add("%d" % v if float(v) == int(v) else "%.1f" % v)

    for c in d["grid"]:
        held.add(c["p"])                    # the grid's own p, quoted as written
        for field in ("independent", "set_hi", "quoted_nines", "set_hi_nines", "span_nines",
                      "rho_one_decade"):
            add(c.get(field))
        add(c["r"])
    return held


def check_numbers(text):
    """Numbers in the manuscript that the artefact does not hold.

    Deliberately narrow and declared: section numbers, years and DOIs are not prose quantities, and
    the reference list is generated rather than authored, so the scan runs over the manuscript body
    before `{{refs}}` is expanded. Anything left over is a number a reader will take as a measurement
    and that no run produces — which is the defect this check exists to catch.
    """
    held = artefact_numbers()
    if held is None:
        return None
    body = text.split(REFS_MARK)[0]
    body = re.sub(r"\{\{c:[a-z0-9-]+\}\}", " ", body)
    body = re.sub(r"\{\{grid\}\}", " ", body)
    body = re.sub(r"#\d+", " ", body)          # issue numbers are identifiers, not quantities
    # structural numbers, not quantities: headings, decades-of-year, and the arithmetic of the paper's
    # own indices (r=1..5, section numbers) are declared here rather than silently exempted
    declared = set(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "0"])
    stray = []
    for m in NUM.finditer(body):
        tok = m.group(0)
        if tok in declared or tok in held:
            continue
        if re.match(r"^(19|20)\d\d$", tok):          # a year
            continue
        stray.append(tok)
    return sorted(set(stray))


def numbered(corpus):
    """Key -> number, assigned from the placed corpus in key order (stable, not arrival order)."""
    order = sorted(placed_keys())
    return dict((k, i + 1) for i, k in enumerate(order))


def entry_line(num, rec):
    fam = rec.get("first_family") or ""
    given = rec.get("first_given") or ""
    initials = ""
    if given:
        initials = " " + "".join(p[0] + "." for p in re.split(r"[\s-]+", given) if p)
    authors = (fam + initials).strip() or "anon."
    venue = rec.get("venue") or ""
    bits = []
    if authors:
        bits.append(authors)
    if rec.get("year"):
        bits.append("(%s)" % rec["year"])
    bits.append(rec["title"].rstrip(".") + ".")
    if venue:
        bits.append("*%s*." % venue)
    bits.append("doi:%s" % rec["doi"])
    return "%d. %s" % (num, " ".join(bits))


def render_list(corpus, nums):
    lines = []
    for key in sorted(nums, key=lambda k: nums[k]):
        rec = corpus["by_key"][key]
        lines.append(entry_line(nums[key], rec))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate issue #162's citations against the placed corpus.")
    ap.add_argument("--render", metavar="PATH", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--report", metavar="PATH", default=None,
                    help="write the derived citation report (reference-check.md)")
    args = ap.parse_args(argv)

    corpus = load_corpus()
    if corpus is None or not os.path.exists(MS):
        print("NOT RUN: corpus or manuscript missing (refs/references.json, manuscript.md)")
        return 3
    corpus["by_key"] = dict((r["key"], r) for r in corpus["records"])

    fails, notes = [], []

    # C0 every key in the corpus is unique
    keys = [r["key"] for r in corpus["records"]]
    if len(keys) != len(set(keys)):
        fails.append("C0 the corpus carries a duplicate key")

    # C1 every placed key resolves to a verified record
    placed = placed_keys()
    for k in placed:
        rec = corpus["by_key"].get(k)
        if rec is None:
            fails.append("C1 placed key %r is not in the corpus" % k)
            continue
        status = (rec.get("verification") or {}).get("status", "")
        if not status.startswith("verified"):
            fails.append("C1 placed key %r has verification status %r" % (k, status))
    unplaced = sorted(set(keys) - set(placed))
    named = sum(1 for k in unplaced if k in PRUNED)
    notes.append("corpus %d records; placed %d; unplaced %d (%d carry a named reason)"
                 % (len(keys), len(placed), len(unplaced), named))
    for k in unplaced:
        if k in PRUNED:
            continue
    stray = [k for k in PRUNED if k not in corpus["by_key"]]
    if stray:
        fails.append("C1 PRUNED names %d key(s) absent from the corpus: %s"
                     % (len(stray), ", ".join(stray[:4])))

    # C2 the manuscript and the placement cover each other
    text = open(MS, encoding="utf-8").read()
    used = [m.group(1) for m in MARK.finditer(text)]
    declared = [cl["id"] for cl in CLAIMS]
    for cid in sorted(set(used)):
        if cid not in declared:
            fails.append("C2 manuscript cites claim %r, which no placement declares" % cid)
    for cid in declared:
        if cid not in used:
            fails.append("C2 claim %r is placed but never cited in the manuscript" % cid)
    if REFS_MARK not in text:
        fails.append("C2 the manuscript has no %s marker, so the list is not generated into it"
                     % REFS_MARK)
    for cl in CLAIMS:
        if not cl["keys"]:
            fails.append("C2 claim %r places no key" % cl["id"])

    # C3b the prose's numbers must be numbers the artefact holds
    stray = check_numbers(text)
    if stray is None:
        fails.append("C3b no artefact to check the prose's numbers against")
    elif stray:
        fails.append("C3b %d number(s) in the manuscript that no run produces: %s"
                     % (len(stray), ", ".join(stray)))
    else:
        notes.append("every decimal in the prose is a number the artefact holds")

    # C3 the floor, counted in DISTINCT records, and every claim's keys must appear in its cluster
    distinct = sorted(set(placed))
    if len(distinct) < FLOOR:
        fails.append("C3 %d distinct cited records, floor is %d" % (len(distinct), FLOOR))
    nums = numbered(corpus)
    rendered = text
    for cl in CLAIMS:
        cluster = ", ".join(str(nums[k]) for k in cl["keys"] if k in nums)
        if not cluster:
            fails.append("C2 claim %r renders an empty cluster" % cl["id"])
        rendered = rendered.replace("{{c:%s}}" % cl["id"], "[%s]" % cluster)
    leftover = MARK.findall(rendered)
    if leftover:
        fails.append("C2 unrendered claim markers remain: %s" % ", ".join(sorted(set(leftover))))
    rendered = rendered.replace(REFS_MARK, "## References\n\n" + render_list(corpus, nums))
    if GRID_MARK in text:
        grid = render_grid()
        if grid is None:
            fails.append("C2 the manuscript has a %s marker but no artefact to render it from"
                         % GRID_MARK)
        else:
            rendered = rendered.replace(GRID_MARK, grid)

    for n in notes:
        print("  " + n)
    print("  distinct cited records: %d (floor %d)" % (len(distinct), FLOOR))
    print("  claims: %d placed, %d cited in the manuscript" % (len(declared), len(set(used))))
    if fails:
        for f in fails:
            print("  [FAIL] " + f)
        print("\nGATE: %d FAILED" % len(fails))
        return 1
    print("  [ok]   every placed key resolves to a verified record")
    print("  [ok]   every claim cited, every citation owned by a claim")
    print("  [ok]   floor met in distinct cited records")
    if args.list:
        sys.stdout.write("\n" + render_list(corpus, nums))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(write_report(args.report, corpus, nums))
        print("  -> report %s" % os.path.basename(args.report))
    if args.render:
        with open(args.render, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        print("  -> rendered %s" % os.path.basename(args.render))
    print("\nGATE: ALL GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
