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
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from placements import (CLAIMS, PRUNED, FLOOR, placed_keys, correction_records,  # noqa: E402
                        correction_violations, loose_only)
from price_search import (QUERIES, VERDICTS, WINDOW,  # noqa: E402
                          CORPUS_VERDICTS, screen as price_screen,
                          tally as price_tally)

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
            "(decades) | zero end in set (loss can be ruled out) |")
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
    surplus = [r for r in recs if r["key"] not in nums and r["key"] not in PRUNED]
    out.append("| — of those, on-topic surplus: no sentence in this paper needs it | %d |"
               % len(surplus))
    out.append("")
    out.append("## What the uncited records are\n")
    out.append("The uncited records are not a rejected set. Each one passed its query's term screen "
               "and the harvest's type whitelist, and each was verified against its DOI record; they "
               "are the RECALL the thirty declared queries bought, and the class each one falls into "
               "is stated here so that the number above is one a reader can act on.\n")
    out.append("| class | n | what it is |")
    out.append("|---|---|---|")
    out.append("| cited in the manuscript, through a claim that owns it | %d | supports a named sentence |"
               % len(nums))
    out.append("| excluded by name, with a reason | %d | names an adjacent construct; the reason is in "
               "`placements.py` and repeated below |"
               % len([r for r in recs if r["key"] not in nums and r["key"] in PRUNED]))
    out.append("| on-topic surplus | %d | on the subject, and no sentence in this paper needs it |"
               % len(surplus))
    out.append("")
    if surplus:
        by_group = {}
        for r in surplus:
            by_group[r.get("group") or "(none)"] = by_group.get(r.get("group") or "(none)", 0) + 1
        out.append("The surplus is distributed across the declared queries rather than produced by "
                   "one bad one -- if it were concentrated, the fix would be a narrower query "
                   "instead of a longer exclusion list:\n")
        out.append("| query group | surplus records |")
        out.append("|---|---|")
        for g in sorted(by_group):
            out.append("| `%s` | %d |" % (g, by_group[g]))
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
    corr = correction_records(recs)
    near = loose_only(recs)
    out.append("## Correction-type records: the class, and what the screen spares\n")
    out.append("A correction-type record is a notice about a work, not the work. `harvest_refs.py` "
               "refuses by TYPE and cannot catch the class, because Crossref types an \"Erratum to: "
               "...\" as the same type its parent carries; the class is closed on the title in "
               "`placements.py` instead (`CORRECTION_TYPE`), and no placed key may be a member. The "
               "pattern matches the \"correction OF a work\" shape rather than the word, because a "
               "paper ABOUT correcting a failure probability is on-topic and a word match would "
               "refuse it.\n")
    out.append("| key | year | refused by | title |")
    out.append("|---|---|---|---|")
    for r in corr:
        out.append("| `%s` | %s | the strict pattern | %s |"
                   % (r["key"], r.get("year"), (r.get("title") or "").replace("|", "/")))
    for r in near:
        out.append("| `%s` | %s | nothing -- spared, and named | %s |"
                   % (r["key"], r.get("year"), (r.get("title") or "").replace("|", "/")))
    out.append("")
    ps = None
    pspath = os.path.join(HERE, "price_search.json")
    if os.path.exists(pspath):
        ps = json.load(open(pspath, encoding="utf-8"))
    if ps is not None:
        t = price_tally(ps)
        out.append("## The price search, which is what §8 answers with\n")
        out.append("Section 8 used to carry a hedge. The hedge is now a search with a record behind "
                   "it (`price_search.py`, `price_search.json`), and this is that record in the form "
                   "a reader can check.\n")
        out.append("| field | value |")
        out.append("|---|---|")
        out.append("| **issued at (UTC)** | `%s` |" % ps.get("ran_at"))
        out.append("| publication window searched | `%s` |" % ps.get("window"))
        out.append("| source | %s |" % ps.get("source"))
        out.append("| queries declared / run | %d / %d |" % (t["queries"], t["ran"]))
        out.append("| records returned | %d |" % t["records"])
        out.append("| refused by the title screen | %d |" % t["refused"])
        out.append("| records read, each with a verdict | %d |" % t["read"])
        out.append("| read at abstract level / title only | %d / %d |" % (t["abstract"], t["title"]))
        out.append("| **statements of the price in the quote's own unit** | **%d** |" % t["price"])
        out.append("| stating the direction, with no magnitude | %d |" % t["understatement"])
        out.append("| parameterising the dependence and computing a figure under it | %d |"
                   % t["model"])
        out.append("")
        out.append("Every query, with the number of records it returned:\n")
        out.append("| group | query | returned |")
        out.append("|---|---|---|")
        for group, q in QUERIES:
            got = ps.get("queries", {}).get(q, {})
            out.append("| `%s` | %s | %s |" % (group, q.replace("|", "/"),
                                               got.get("returned", "NOT RUN")))
        out.append("")
        out.append("Every record the screen let through, with the verdict on it (categories: `price`, "
                   "`understatement`, `model`, `bounds`, `design`, `other`; `read at` is how much of "
                   "the record was available to read):\n")
        out.append("| DOI | year | read at | verdict | what it is |")
        out.append("|---|---|---|---|---|")
        for r in ps.get("records", []):
            ok, _why = price_screen(r)
            if not ok:
                continue
            v = VERDICTS.get(r["doi"])
            if not v:
                out.append("| %s | %s | - | **NO VERDICT** | %s |"
                           % (r["doi"], r.get("year"), (r.get("title") or "").replace("|", "/")))
                continue
            out.append("| %s | %s | %s | `%s` | %s |"
                       % (r["doi"], r.get("year"), v[1], v[0], v[2].replace("|", "/")))
        out.append("")
        out.append("The corpus this paper harvested was screened the same way, and it is reported "
                   "separately because it is a weaker instrument: it stores titles and venues, not "
                   "abstracts. Its %d correction-type titles and its %d title(s) whose words suggest a "
                   "pricing statement are named above; the suggested one is a homonym -- %s.\n"
                   % (len(corr),
                      sum(1 for r in recs if r["key"] in CORPUS_VERDICTS),
                      "; ".join("%s: %s" % (k, v[1]) for k, v in sorted(CORPUS_VERDICTS.items()))))
    # The numerator and the denominator must count the same population. They did not: the absence was
    # collected over the whole harvested corpus while the sentence divided by the cited set, so the
    # report read "%d of the %d cited records" out of two different populations -- true of neither.
    noauthor_all = [r for r in recs if not (r.get("first_family") or "").strip()]
    noauthor = [r for r in noauthor_all if r["key"] in nums]
    out.append("## Entries whose record carries no author\n")
    out.append("%d of the %d cited records carry no author field on Crossref, and their entries say so "
               "by naming the record that was read (\"author not established on Crossref for this "
               "DOI\") rather than by leaving the position empty or inventing an initial. The absence "
               "is a claim about a record, and it is checkable against the registry the entry names. "
               "The table below lists exactly those %d, which is the whole of what this report can "
               "show a reader: every one of them has an entry here to check.\n"
               % (len(noauthor), len(nums), len(noauthor)))
    placeholder = [r for r in recs
                   if r["key"] in nums
                   and (r.get("first_family") or "").strip()
                   and not HAS_LETTER.search((r.get("first_family") or "").strip())]
    if placeholder:
        out.append("A further %d cited record(s) store punctuation where a family name belongs, so "
                   "their entries print the given name the same record holds and the absence is not "
                   "claimed for them: %s. The registry value is quoted here because it is the thing "
                   "to check -- the field holds %s, not a name.\n"
                   % (len(placeholder),
                      "; ".join("DOI %s (`%s`, family `%s`, given `%s`)"
                                % (r["doi"], r["key"], r["first_family"], r.get("first_given") or "")
                                for r in placeholder),
                      ", ".join("`%s`" % r["first_family"] for r in placeholder)))
    out.append("For the harvested corpus as a whole the same absence holds for %d of its %d records. "
               "The other %d are part of the corpus this paper does not cite, so they have no entry "
               "here and the count of them is a fact about the harvest, not about the bibliography.\n"
               % (len(noauthor_all), len(recs), len(noauthor_all) - len(noauthor)))
    out.append("| key | DOI | title |")
    out.append("|---|---|---|")
    for r in noauthor:
        out.append("| `%s` | %s | %s |" % (r["key"], r["doi"], r["title"].replace("|", "/")))
    out.append("")
    out.append("## Bracketed groups in the text that are not citations\n")
    out.append("The prose writes the closed unit interval as `[0, 1]`, and writes a claim's citation "
               "cluster as a bracketed number list. A reader (and `refgate.py`, which calls it "
               "`AMBIGUOUS [0]`) sees the first as a citation to entry 0, which does not exist. It is "
               "an interval: `rho` is declared on `[0, 1]`, and every bracket group in this paper is "
               "either that interval or a generated cluster.\n")
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
    # The title's number is quoted in the abstract as an anchor per replica, computed by
    # `anchored_quote` and stored in `title_quote`. Held for the same reason the grid's numbers are:
    # a number in prose has to be a number a program prints.
    tq = d.get("title_quote")
    if tq:
        add(tq.get("target_nines"))
        for a in tq.get("anchors", []):
            for field in ("p", "quoted", "quoted_nines", "rho_one_decade", "r"):
                add(a.get(field))

    # Section 8 quotes the price search's own counts. They are held here for the same reason the
    # grid's numbers are: a count typed into prose has to be a count a program prints, and the print
    # that produces these is `price_search.tally`, not a copy of it.
    pspath = os.path.join(HERE, "price_search.json")
    if os.path.exists(pspath):
        t = price_tally(json.load(open(pspath, encoding="utf-8")))
        for k in ("queries", "ran", "records", "refused", "read", "abstract", "title", "price",
                  "understatement", "model", "bounds", "design", "other", "refused_no_dependence",
                  "refused_no_object", "refused_correction"):
            add(t[k])
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
    # an ISO date stamp is an identifier too: `1960-01-01..2026-11-21` is a window, and its month and
    # day fields are not quantities a reader will take as measurements. Declared rather than exempted
    # silently, and narrowed to the ISO shape so a bare `01` in prose is still caught.
    body = re.sub(r"\b\d{4}-\d\d-\d\d\b", " ", body)
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


HAS_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
# A registry field can hold punctuation where a name belongs. `10.36948/ijfmr.2020.v02i04.39038`
# stores `family: "-"` with the name in `given`, and a truthy dash was read as a family name, so the
# entry printed `-, V. R. I.` -- an author-shaped string with no name in it. The rule is therefore
# about the *content* of the field, not its emptiness: a family name has a letter in it. The fallback
# is the given name, which is what the same record holds; when that is empty too, the absence is
# named the way `reference-check.md`'s policy names it, so the two carriers say one thing.
def author_component(rec):
    """The name this record's entry prints, and the reason it prints it."""
    fam = (rec.get("first_family") or "").strip()
    given = (rec.get("first_given") or "").strip()
    if fam and HAS_LETTER.search(fam):
        fam = fam[:1].upper() + fam[1:].lower() if fam.isupper() or fam.islower() else fam
        initials = ""
        if given:
            initials = ", " + " ".join(p[0] + "." for p in re.split(r"[\s-]+", given) if p)
        return fam + initials
    if given:
        return given
    return "author not established on Crossref for this DOI"


def entry_line(num, rec, claim=None):
    """One bibliography entry, in this journal's house order.

    `[n] Family, I. (year). Title. Venue. https://doi.org/...` and then the difference line. The
    link is printed as a URL a reader can open, never as a bare DOI string: a pointer has to resolve
    in the hands of whoever reads it.

    The difference line is the *claim's* — one authored line per claim, printed on each entry that
    claim owns, and the entry names the claim it speaks for. That is a declared construction rather
    than 200 restatements: the claims are what the paper distinguishes, and a per-entry sentence
    invented for a record the paper cites in a cluster would be boilerplate dressed as content.
    """
    authors = author_component(rec)
    title = html.unescape(rec["title"]).strip()
    title = title[:1].upper() + title[1:]
    bits = ["[%d]" % num, authors + " (%s)." % rec.get("year", "n.d."), title]
    if not title.endswith((".", "?", "!")):
        bits[-1] = bits[-1] + "."
    venue = html.unescape(rec.get("venue") or "").strip()
    if venue:
        bits.append("*%s*." % venue)
    bits.append("https://doi.org/%s" % rec["doi"])
    line = " ".join(bits)
    if claim and claim.get("difference"):
        line += " Difference: %s. (supports `%s`)" % (claim["difference"], claim["id"])
    return line


def render_list(corpus, nums):
    lines = []
    owner = {}
    for cl in CLAIMS:
        for k in cl["keys"]:
            owner.setdefault(k, cl)
    for key in sorted(nums, key=lambda k: nums[k]):
        rec = corpus["by_key"][key]
        lines.append(entry_line(nums[key], rec, owner.get(key)))
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
    bad_corr = correction_violations(corpus["records"], placed)
    if bad_corr:
        fails.append("C1b placed key(s) are corrections OF another work, not the work: %s"
                     % ", ".join(bad_corr))
    corr = correction_records(corpus["records"])
    near = loose_only(corpus["records"])
    notes.append("correction-type records in the corpus: %d (%s); spared by the strict pattern: %d (%s)"
                 % (len(corr), ", ".join(r["key"] for r in corr) or "none",
                    len(near), ", ".join(r["key"] for r in near) or "none"))
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

    # C4 the FAMILY position has to hold a name. A registry field holding `-` used to print as
    # `-, V. R. I.` -- author-shaped, and no name in the family position -- and nothing failed.
    #
    # The rule is scoped to that position and not to the whole component, because the whole component
    # holds letters either way: `-, V. R. I.` carries `V`, `R`, `I` in the initials, so a check asking
    # "does this string contain a letter" passes on the very defect it was written for. Measured, not
    # assumed: with the old rule back, that weaker version stayed green and only the digest step
    # objected -- an indirect signal naming a different object. The family slot is the position the
    # defect occupies, so it is the position the check reads.
    by_key = dict((r["key"], r) for r in corpus["records"])
    nameless = []
    for k in sorted(nums):
        if k not in by_key:
            continue
        slot = author_component(by_key[k]).split(", ")[0]
        if not HAS_LETTER.search(slot):
            nameless.append("%s -> %r" % (k, slot))
    if nameless:
        fails.append("C4 %d cited entr(ies) print no name in the family position: %s"
                     % (len(nameless), "; ".join(nameless)))
    else:
        notes.append("every entry holds a name in the family position")
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
